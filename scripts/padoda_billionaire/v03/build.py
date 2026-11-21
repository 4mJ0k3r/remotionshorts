import json, math, sys
from pathlib import Path
from random import Random
import bpy
from mathutils import Vector,Euler
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/padoda_billionaire/v03"
sys.path[:0]=[str(HERE),str(ROOT/"scripts"),str(ROOT/"scripts/bb_shark_slipper_reel/v01d")]
import ricks_v2_kit as k
import graphic_materials as g
from sets import workshop,vault,disk,box

BENCH=(1,44,70,75,80,84,151,178,191,225,250,261)
FLASH=((1,0),(78,0),(79,.20),(80,.49),(81,.002),(82,0),(262,0))
AUDIO=json.loads((OUT/"audio_check.json").read_text())["audio_rms"]
SWITCH=81
OFFSET=25

def step(f,a,b):return k.look.ease5((f-a)/(b-a))
def blend(a,b,t):return Vector(a).lerp(Vector(b),t)
def pop(f,a,b):return 1.075*step(f,a,b)-.075*step(f,b,b+4)
def channel(obj,path,f):obj.keyframe_insert(path,frame=f)
def col(scene,name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c

def vapor_material(color):
    material=k.emission("Soft translucent lime vapor",color,1.65)
    material.surface_render_method="BLENDED"
    material.use_transparency_overlap=False
    nodes=material.node_tree.nodes
    links=material.node_tree.links
    output=next(node for node in nodes if node.type=="OUTPUT_MATERIAL")
    emission=next(node for node in nodes if node.type=="EMISSION")
    facing=nodes.new("ShaderNodeLayerWeight")
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation="EASE"
    ramp.color_ramp.elements[0].position=.12
    ramp.color_ramp.elements[0].color=(.51,.51,.51,1)
    ramp.color_ramp.elements[1].position=.94
    ramp.color_ramp.elements[1].color=(0,0,0,1)
    mix=nodes.new("ShaderNodeMixShader")
    links.new(facing.outputs["Facing"],ramp.inputs[0])
    links.new(ramp.outputs[0],mix.inputs[0])
    links.new(nodes.new("ShaderNodeBsdfTransparent").outputs[0],mix.inputs[1])
    links.new(emission.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs[0])
    return material

def seated_knee(leg,hip,ankle,target_length):
    low,high=.23,.73
    for _ in range(12):
        reach=(low+high)/2
        knee=Vector((ankle.x,-reach,.305))
        k.tube_pose(leg,(hip,knee,ankle),None)
        if leg.data.splines[0].calc_length()<target_length:
            low=reach
        else:
            high=reach
    return knee

def hand_world(root,yaw,body_basis,bounce,hand):
    return root+Euler((0,0,yaw)).to_matrix() @ (
        body_basis @ hand+Vector((0,0,.59+bounce)))

def coin_contact_tip(arms):
    hand,elbow=map(Vector,arms[1])
    return hand+(hand-elbow).normalized()*.016

def lime_bounce(material):
    nodes=material.node_tree.nodes
    links=material.node_tree.links
    emission=next(node for node in nodes if node.type=="EMISSION" and node.outputs[0].is_linked)
    color=emission.inputs["Color"]
    original=color.links[0].from_socket
    layer=nodes.new("ShaderNodeMixRGB")
    layer.blend_type="MULTIPLY"
    layer.inputs[2].default_value=k.look.rgba("#95ff6a")
    links.new(original,layer.inputs[1])
    links.new(layer.outputs[0],color)
    for frame,strength in ((1,0),(65,0),(72,.37),(77,.44),(81,0)):
        layer.inputs[0].default_value=strength
        layer.inputs[0].keyframe_insert("default_value",frame=frame)

def stage_visibility(c,vault_stage):
    for obj in c.objects:
        for prop in ("hide_render","hide_viewport"):
            track=obj.animation_data.action.fcurves.find(prop) if obj.animation_data and obj.animation_data.action else None
            driver=obj.driver_add(prop).driver
            cond=f"frame < {SWITCH}" if vault_stage else f"frame >= {SWITCH}"
            driver.expression=cond
            if track:
                key="pose_"+prop
                obj[key]=bool(getattr(obj,prop));track.data_path=f'["{key}"]'
                v=driver.variables.new();v.name="hidden";v.type="SINGLE_PROP"
                v.targets[0].id=obj;v.targets[0].data_path=track.data_path
                driver.expression=cond+" or hidden > 0.5"

def hero(c,name,warm):
    art=HERE/"art"
    n=k.RING
    try:
        k.RING=28
        a=k.build_ricks_character(name,c,costume_image=art/"outfit.png",
            expression_images={s:art/(s+".png") for s in ("strain","pop","smug","story","wink")})
    finally:
        k.RING=n
    ink=k.emission(name+" • jet black silhouette","#040407",1)
    ink.use_backface_culling=True
    limbs=k.emission(name+" • matte graphic sticks","#050508",1)
    for mod in a.ink_modifiers:mod.id_data.data.materials[0]=ink
    for limb in (*a.arms,*a.legs,*a.feet):limb.data.materials[0]=limbs
    handled=set()
    for o in a.root.children_recursive:
        if o.type not in ("MESH","CURVE") or not o.data.materials:
            continue
        m=o.data.materials[0]
        if m in handled or not any(n.type=="BSDF_PRINCIPLED" for n in m.node_tree.nodes):continue
        if "ellipsoid head" in o.name:g.face(m,"#D9B67A" if warm else "#9EB2D6",.32 if warm else .28,None)
        else:
            if "pill torso" in o.name:
                p=next(n for n in m.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
                p.inputs["Base Color"].default_value=k.look.rgba("#238b98")
            g.graphics(m,texture=o not in a.expressions.values(),two_tone=True)
        if not warm and ("ellipsoid head" in o.name or "pill torso" in o.name or "outfit" in o.name):
            lime_bounce(m)
        handled.add(m)
    return a

def ornaments(c,a,gold,glow):
    crown=k.empty("Animated tilted crown",c,parent=a.head)
    pts=[]
    for z in range(3):
        for i in range(40):
            t=i*math.tau/40;h=(.16 if i%8==0 else .088 if i%8 in (1,7) else .055)
            r=(.155,.156,.172)[z]
            pts.append((r*math.cos(t),r*.88*math.sin(t),(-.025,.015,h)[z]))
    faces=[(j*40+i,j*40+(i+1)%40,(j+1)*40+(i+1)%40,(j+1)*40+i) for j in range(2) for i in range(40)]
    ring=k.mesh("Scalloped jewel-crown gold",c,pts,faces,gold,crown)
    s=ring.modifiers.new("Cast gold thickness","SOLIDIFY");s.thickness=.010
    for i in range(5):
        t=i*math.tau/5
        k.ball("Crown pearl points",c,(.171*math.cos(t),.15*math.sin(t),.153),(.026,.026,.026),glow,crown,segments=12,rings=8)
    glasses=k.empty("Billionaire tapered dark glasses",c,parent=a.head)
    black=k.surface("Polished smoked sunglasses","#161b2c",.20,.49)
    shine=k.emission("Sunglass diagonal ink glint","#b6e2f3",1.1)
    for side in (-1,1):
        x=.091*side
        box("Dark sunglasses lens",c,(x,0,-.006),(.159,.03,.056),black,.019,parent=glasses)
        k.tube("Lens angled highlight",c,[(x-.049,-.016,-.024),(x-.023,-.017,.001),(x+.001,-.016,.018)],.004,shine,glasses)
    box("Sunglass nose bridge",c,(0,-.005,.014),(.05,.033,.018),black,.005,parent=glasses)
    chain=k.tube("Diamanté heavy gold chain",c,[(-.094,-.072,.422),(-.086,-.083,.325),(0,-.106,.27),
                       (.085,-.084,.325),(.095,-.072,.417)],.011,gold,a.body)
    k.ball("Chain medallion",c,(0,-.115,.265),(.033,.013,.034),gold,a.body,segments=20,rings=12)
    return crown,glasses

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene;k.configure_ricks_scene(scene,frame_end=261,samples=6)
    scene.render.image_settings.file_format="PNG";scene.render.image_settings.compression=0
    scene.world=bpy.data.worlds.new("Indigo studio world");scene.world.use_nodes=True
    bg=next(n for n in scene.world.node_tree.nodes if n.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#19243b");bg.inputs[1].default_value=.31
    ca,cb=col(scene,"Workshop / behind the dial"),col(scene,"Vault / bullion throne")
    pointer,gauge,rim,spill=workshop(ca)
    bills,brass,gold,glow=vault(cb)
    act,king=hero(ca,"Hero workshop",False),hero(cb,"Hero vault",True)
    crown,glasses=ornaments(cb,king,gold[2],glow)
    coin=k.empty("Flicked bullion coin",cb)
    o=disk("Coin bevelled grip edge",cb,(0,0,0),.057,.016,brass,coin);k.apply_prop_ink(o,cb,thickness=.002)
    disk("Coin stamped face",cb,(0,-.011,0),.046,.009,gold[2],coin)
    disk("Coin star seal",cb,(0,-.017,0),.021,.005,glow,coin)
    gas_material=vapor_material("#83f943")
    rng=Random(55)
    puffs=[k.ball("Airy comic vapor wisp",ca,(0,0,0),(.33,.19,.19),gas_material,segments=16,rings=10)
           for _ in range(6)]
    for puff in puffs:
        for polygon in puff.data.polygons:
            polygon.use_smooth=True
    wave_center=Vector((.63,-.23,.90))
    wave_material=k.emission("Lime circular pressure wave","#a7ff43",1.85)
    wave_glow=next(n for n in wave_material.node_tree.nodes if n.type=="EMISSION").inputs["Color"]
    for f,color in ((1,"#a7ff43"),(76,"#a7ff43"),(78,"#ffcf54"),(80,"#ffb747")):
        wave_glow.default_value=k.look.rgba(color)
        channel(wave_glow,"default_value",f)
    wave=k.tube("Circular gauge shockwave",ca,[(.259*math.cos(i*math.tau/48),0,.259*math.sin(i*math.tau/48))
                                               for i in range(49)],.007,wave_material)
    wave.location=wave_center
    sparks=[k.ball("Gold transformation spark",cb,(0,0,0),(.021,.022,.045),glow,segments=8,rings=5)
            for i in range(19)]
    locations=[]
    for bill in bills:
        x,y,z,a=rng.uniform(-2.65,2.65),rng.uniform(-2.15,3.35),rng.uniform(.48,3.48),rng.uniform(0,6.28)
        if y<.95 and 1.33<z<2.77 and abs(x)<.67:x=math.copysign(.76,x)
        locations.append((x,y,z,a))
    camera=bpy.data.objects.new("Baked 36mm delivery camera",bpy.data.cameras.new("Vertical Cine Camera"))
    scene.collection.objects.link(camera);scene.camera=camera
    k.setup_ricks_camera(camera,lens=38,fstop=2.85)
    k.setup_ricks_compositor(scene,camera=camera,portal_flash_keys=FLASH)
    camera.data.dof.aperture_fstop=2.85
    for node in scene.node_tree.nodes:
        if node.type=="GLARE":node.threshold=.85
        if node.type=="MIX_RGB" and node.blend_type=="ADD" and node.inputs[2].is_linked:
            node.inputs[0].default_value=.36
    prevA=prevB=None
    standing_lengths=None
    checked_contacts={}
    launch_center=None
    for f in range(1,262):
        tension=step(f,8,62)
        gauge_shake=step(f,28,44)*(1-step(f,52,61))
        needle=-1.87+4.10*step(f,4,44)+.095*math.sin(f*1.95)*gauge_shake
        pointer.rotation_euler.y=needle;channel(pointer,"rotation_euler",f)
        gauge.rotation_euler.y=.030*math.sin(f*2.27)*gauge_shake
        channel(gauge,"rotation_euler",f)
        rim.data.energy=8+117*tension**2;channel(rim.data,"energy",f)
        spill.data.energy=14*gauge_shake+109*step(f,65,75)
        channel(spill.data,"energy",f)
        expand=.44*step(f,66,71)+.56*step(f,71,79)
        sweep=.41*step(f,67,72)+.59*step(f,72,80)
        wash=step(f,75,80)
        for i,puff in enumerate(puffs):
            a=i*math.tau/len(puffs)
            plume=step(f,69+(i%4),80)
            puff.location=(-.14+(.91+.27*math.cos(a))*sweep+.74*wash,.52-(.85+.32*(i%3))*plume,
                           .65+(.24+.35*math.sin(a))*expand+.13*plume+.25*wash)
            size=.10+expand*(.73+.07*(i%4))
            puff.scale=((1.23+.80*wash)*size,size,.73*size)
            puff.rotation_euler.y=.67*math.sin(a)+.26*sweep-.64*wash
            puff.hide_render=puff.hide_viewport=f<67
            for prop in ("location","rotation_euler","scale","hide_render","hide_viewport"):channel(puff,prop,f)
        wave.scale=(1+2.7*wash,1,1+1.9*wash)
        wave.location=wave_center+Vector((.45*wash,-.15*wash,.17*wash))
        wave.hide_render=wave.hide_viewport=f<76
        for prop in ("location","scale","hide_render","hide_viewport"):channel(wave,prop,f)
        if f<=SWITCH:
            release=step(f,66,70)
            jolt=pop(f,66,70)*(1-step(f,70,74))
            sway=.017*math.sin(f*1.82)*tension
            root_a=Vector((-.24+(.18 if f>=53 else 0)-.038*release,.16,0))
            yaw_a=-.11
            tilt_a=.26+.18*tension-.31*release+math.radians(10)*jolt
            bounce_a=-.047-.136*tension+.072*release+.065*jolt+sway
            squash_a=1-.088*tension-.056*(step(f,64,66)-release)+.095*release+.138*jolt
            body_basis=Euler((0,0,yaw_a)).to_matrix() @ Euler((tilt_a,0,0)).to_matrix()
            body_origin=root_a+Vector((0,0,.59+bounce_a))
            brace=Vector((.165,.026,.567))
            elbow_world=Vector((-.034,-.015,.661-.056*tension))
            elbow_a=body_basis.transposed()@(elbow_world-body_origin)
            hand_a=body_basis.transposed()@(brace-body_origin)
            hand_a-=(hand_a-elbow_a).normalized()*.016
            hand_a.z/=squash_a
            elbow_a.z/=squash_a
            recoil=step(f,65,70)
            arms_a=[
                ((-.225-.094*release,-.157,.145+.26*release+.065*jolt),
                 (-.270-.034*release,-.035,.20+.115*release+.052*jolt)),
                (hand_a.lerp(Vector((.32,-.20,.49)),recoil),elbow_a.lerp(Vector((.29,-.045,.33)),recoil)),
            ]
            legs=[((s*.166,-.039,.027),(s*.164,-.163,.29)) for s in (-1,1)]
            face="pop" if f>=67 else "strain"
            act.pose(f,root_a,yaw_a,tilt_a,arms_a,legs,None if face==prevA else face,
                bounce=bounce_a,squash=squash_a,head_tilt=-.18+.044*math.sin(f*.28)+.21*release-.11*jolt,
                sweat=step(f,20,66) if 20<=f<=67 else None)
            if f==14:
                standing_lengths=[leg.data.splines[0].calc_length() for leg in act.legs]
            if f in (1,14,34,64):
                wrist=act.arms[1].data.splines[0].bezier_points[-1].co.copy()
                wrist.z*=squash_a
                checked_contacts[f"workbench_f{f:03}_tip_error_m"]=(body_origin+body_basis@wrist-brace).length
            prevA=face
        if f>=SWITCH:
            cheer=pop(f,87,91)*(1-step(f,146,161))
            nudge=pop(f,164,168)*(1-step(f,187,196))
            pinch=step(f,172,180)*(1-step(f,184,190))
            throw=step(f,180,183)*(1-step(f,185,193))
            catch=step(f,193,200)*(1-step(f,204,213))
            story=step(f,208,224)
            wink_hold=step(f,238,242)
            syllable=min(.95,AUDIO[f-1]*6)*story
            bounce=-.270
            tilt=.055-.11*cheer+math.radians(14)*story
            roll=.112*story
            yaw=.045-.136*step(f,156,193)+.18*story
            body_basis=Euler((tilt,roll,0)).to_matrix()
            pelvis=Vector((0,.817,1.425))
            root=pelvis-Euler((0,0,yaw)).to_matrix() @ (
                body_basis @ Vector((0,0,.070))+Vector((0,0,.59+bounce)))
            head_yaw=.08+.09*step(f,152,167)-.16*story
            head_tilt=.08-.14*cheer-.18*story+(.023*math.sin(f*.35)-.060*syllable)*(1-wink_hold)
            glass_drop=step(f,86,100)
            glass_loc=Vector((0,-.229-.029*math.sin(math.pi*glass_drop),
                              .036+.159*(1-glass_drop)-.077*step(f,164,171)-.026*wink_hold))
            rim_touch=(Euler((head_tilt,0,head_yaw)).to_quaternion()@
                       (glass_loc+Vector((-.165,-.002,-.006)))+Vector((0,0,k.FACE_CENTER-.59)))
            arms=[]
            for s in (-1,1):
                neutral=(s*.203,-.113,.183)
                hand=blend(neutral,(s*.393,-.032,.357),cheer)
                hand=hand.lerp(Vector((s*(.31+.035*math.sin(f*.25)*(1-wink_hold)),
                                       -.255-.059*(s==-1),
                                       .378+.087*(s==-1)+(.086*math.sin(f*.22)+.067*syllable)*(1-wink_hold))),
                               story*.93)
                if s==-1:hand=hand.lerp(rim_touch,min(1,nudge))
                else:
                    hand=hand.lerp(Vector((.222,-.239,.401)),pinch)
                    hand=hand.lerp(Vector((.385,-.216,.477)),throw)
                    hand=hand.lerp(Vector((.305,-.191,.331)),catch)
                arms.append((hand,(s*(.225+.066*cheer),-.102,.262+.084*cheer+.065*nudge*(s==-1))))
            root_basis=Euler((0,0,yaw)).to_matrix()
            feet=[]
            for i,s in enumerate((-1,1)):
                ankle=root_basis.transposed()@(Vector((s*.129,.563,1.313))-root)
                hip=Vector((0,0,.59+bounce))+body_basis@Vector((s*.060,0,.070))
                knee=seated_knee(king.legs[i],hip,ankle,standing_lengths[i])
                feet.append((ankle,knee))
            face="wink" if f>=243 else "story" if f>=203 and AUDIO[f-1]>.027 else "smug"
            king.body.rotation_euler.y=roll
            king.pose(f,root,yaw,tilt,arms,feet,None if face==prevB else face,bounce=bounce,
                      head_yaw=head_yaw,head_tilt=head_tilt)
            for i,(ankle,knee) in enumerate(feet):
                hip=Vector((0,0,.59+bounce))+body_basis@Vector((((-1,1)[i])*.060,0,.070))
                k.tube_pose(king.legs[i],(hip,knee,ankle),f)
            prevB=face
            if f in (89,145,188,223,261):
                checked_contacts[f"seated_f{f:03}_leg_length_delta_m"]=[
                    leg.data.splines[0].calc_length()-reference for leg,reference in zip(king.legs,standing_lengths)]
            crown.location=(.014,.026,.252+.248*(1-step(f,83,87))-.026*math.sin(math.pi*step(f,87,94)))
            crown.rotation_euler=(.11,.21-.16*step(f,85,91),-.165)
            glasses.location=glass_loc
            for p in ("location","rotation_euler"):channel(crown,p,f)
            channel(glasses,"location",f)
            tip=hand_world(root,yaw,body_basis,bounce,coin_contact_tip(arms))
            spin=max(0.,min(1.,(f-182)/18))
            coin.rotation_euler=(.24+.90*math.sin(spin*math.tau),spin*math.tau*2,
                                 -.16+.57*math.sin(spin*math.tau))
            gripped=tip-coin.rotation_euler.to_matrix()@Vector((-.026,0,-.047))
            if f==182:
                launch_center=gripped.copy()
            if 183<=f<200:
                coin.location=launch_center.lerp(gripped,step(f,187,200))+Vector(
                    (.165*math.sin(math.pi*spin)*step(f,183,187),.075*math.sin(math.pi*spin),
                     .76*4*spin*(1-spin)))
            else:
                coin.location=gripped
            coin.hide_render=coin.hide_viewport=f<172
            for p in ("location","rotation_euler","hide_render","hide_viewport"):channel(coin,p,f)
            for i,sp in enumerate(sparks):
                a=i*math.tau/len(sparks)+f*.074;v=step(f,83,116)
                sp.location=((.30+1.04*v)*math.cos(a),.84+.12*math.sin(4*a),2.05+(.29+.72*v)*math.sin(a))
                sp.scale=(max(.02,(1-v)*(.35+.60*abs(math.sin(a+f*.17)))),)*3
                for p in ("location","scale"):channel(sp,p,f)
        if f<35:
            t=step(f,1,34)
            p=blend((-.10,-3.01,1.05),(.05,-2.80,1.015),t)
            aim=Vector((.185,.04,.77));focus=Vector((-.05,.03,.94));lens=38
        elif f<=52:
            t=step(f,35,52)
            jitter=.019*gauge_shake*math.sin(f*2.31)
            p=Vector((.63+jitter,-1.81+.22*t,.91+.012*math.sin(f*1.89)))
            aim=Vector((.63,-.193,.90));focus=aim.copy();lens=55
        elif f<SWITCH:
            t=step(f,53,77);match=step(f,77,80)
            jitter=.035*jolt*math.sin(f*1.67)
            p=Vector((-.065+jitter,-2.83+.13*t,.99+.07*jolt)).lerp(Vector((.36,-2.17,.99)),match)
            aim=Vector((.163,.03,.81+.08*jolt)).lerp(Vector((.72,-.12,.94)),match)
            focus=Vector((-.08,.03,.96)).lerp(wave_center,match);lens=35+4*match
        elif f<152:
            t=step(f,81,143)
            p=blend((-.09,-1.96,1.67),(-.12,-4.65,1.80),t)
            aim=blend((0,.70,1.97),(.04,.98,1.69),t)
            focus=Vector((0,.57,2.01));lens=34
        elif f<=202:
            t=step(f,152,202)
            p=blend((1.48,-2.38,1.94),(1.37,-2.16,1.93),t)
            aim=blend((.105,.72,2.10),(.113,.66,2.08),t)
            focus=Vector((.035,.59,2.03));lens=36
        else:
            t=step(f,203,242)
            p=blend((-.23,-2.15,1.65),(-.13,-1.79,1.69),t)
            aim=blend((.012,.68,1.95),(.015,.52,1.99),t)
            focus=Vector((.00,.48,2.01));lens=37+2*t
        forward=(aim-p).normalized()
        facing=forward.to_track_quat("-Z","Y")
        camera.location=p+(Vector((OFFSET,0,0)) if f>=SWITCH else Vector((0,0,0)))
        camera.rotation_mode="QUATERNION";camera.rotation_quaternion=facing
        camera.data.lens=lens;camera.data.dof.focus_distance=(focus-p).dot(forward)
        if f>=SWITCH:
            view_right=facing@Vector((1,0,0))
            view_up=facing@Vector((0,1,0))
            coin_shot=152<=f<=202
            keep_clear=1. if coin_shot else step(f,221,235)
            face_center=Vector((.17,.62,2.28) if coin_shot else (.02,.38,2.01))
            clear_width,clear_height=(.50,.61) if coin_shot else (.38,.48)
            face_depth=(face_center-p).dot(forward)
            for i,(bill,data) in enumerate(zip(bills,locations)):
                x,y,z,a=data;age=(f-81)/30
                pos=Vector((x+.23*math.sin(age*.86+a),y+.18*math.cos(age+a),
                            z+.28*math.sin(age*.78+a)+.059*age))
                depth=(pos-p).dot(forward)
                if depth>.09 and keep_clear>0:
                    eye_target=p+(face_center-p)*(depth/face_depth)
                    horizontal=(pos-eye_target).dot(view_right)
                    vertical=(pos-eye_target).dot(view_up)
                    half_width=clear_width*depth/face_depth+.15
                    half_height=clear_height*depth/face_depth+.15
                    side=-1 if x<0 else 1
                    band=1-step(abs(vertical),half_height,half_height+.13)
                    pos+=view_right*side*max(0,half_width-side*horizontal)*keep_clear*band
                bill.location=pos
                bill.rotation_euler=(1.04+.38*math.sin(age*2+a),.54*math.sin(age*1.4+a),a+.63*age)
                for prop in ("location","rotation_euler"):channel(bill,prop,f)
        for pth in ("location","rotation_quaternion"):channel(camera,pth,f)
        for pth in ("lens","dof.focus_distance"):channel(camera.data,pth,f)
        active=act if f<SWITCH else king
        depth=(focus-p).length if "p" in locals() else 2.
        for mod in active.ink_modifiers:
            mod.strength=-min(.012,k.look.ink_width(depth,lens,3.))
            mod.keyframe_insert("strength",frame=f)
    act.finish_bake();king.finish_bake()
    parent=k.empty("Vault stage positioning",cb,(OFFSET,0,0))
    for obj in tuple(cb.objects):
        if obj.parent is None and obj!=parent:obj.parent=parent
    stage_visibility(ca,False);stage_visibility(cb,True)
    for a in bpy.data.actions:
        for fc in a.fcurves:
            for key in fc.keyframe_points:
                key.interpolation="CONSTANT" if "hide_" in fc.data_path or fc.data_path=="lens" else "LINEAR"
    for f,name in ((1,"Hands braced"),(35,"Redline insert"),(53,"Recoil framing"),(67,"Gas release"),
                   (79,"Two-frame flash"),(81,"Centered vault reveal"),(152,"Three-quarter coin shot"),
                   (172,"Coin pinch"),(183,"Coin released"),(200,"Coin catch"),(203,"Storyteller"),(243,"Held wink")):
        scene.timeline_markers.new(name,frame=f)
    scene.frame_set(1);scene.render.filepath="//frame_"
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"padoda_hook_v03.blend"))
    (OUT/"contact_check.json").write_text(json.dumps({"standing_leg_length_m":standing_lengths,**checked_contacts},indent=2))

if __name__=="__main__":build()


