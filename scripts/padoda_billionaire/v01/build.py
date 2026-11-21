import json, math, sys
from pathlib import Path
from random import Random
import bpy
from mathutils import Vector,Euler,Quaternion
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/padoda_billionaire/v01"
sys.path[:0]=[str(HERE),str(ROOT/"scripts"),str(ROOT/"scripts/bb_shark_slipper_reel/v01d")]
import ricks_v2_kit as k
import graphic_materials as g
from sets import workshop,vault,disk,box

CAL=(14,61,77,89,145,188,223,261)
BENCH=(1,14,41,61,77,81,89,112,145,188,223,261)
FLASH=((1,0),(76,0),(77,.002),(78,.24),(79,.94),(80,1),(81,1),(82,1),(83,.34),(84,.07),(85,0),(260,0),(261,.002),(262,0))
AUDIO=json.loads((OUT/"audio_check.json").read_text())["audio_rms"]
SWITCH=81
OFFSET=25

def step(f,a,b):return k.look.ease5((f-a)/(b-a))
def blend(a,b,t):return Vector(a).lerp(Vector(b),t)
def pop(f,a,b):return 1.075*step(f,a,b)-.075*step(f,b,b+4)
def channel(obj,path,f):obj.keyframe_insert(path,frame=f)
def col(scene,name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c

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
    scene=bpy.context.scene;k.configure_ricks_scene(scene,frame_end=261,samples=8)
    scene.render.image_settings.file_format="PNG";scene.render.image_settings.compression=0
    scene.world=bpy.data.worlds.new("Indigo studio world");scene.world.use_nodes=True
    bg=next(n for n in scene.world.node_tree.nodes if n.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#19243b");bg.inputs[1].default_value=.31
    ca,cb=col(scene,"Workshop / behind the dial"),col(scene,"Vault / bullion throne")
    pointer,rim=workshop(ca)
    bills,brass,gold,glow=vault(cb)
    act,king=hero(ca,"Hero workshop",False),hero(cb,"Hero vault",True)
    crown,glasses=ornaments(cb,king,gold[2],glow)
    coin=k.empty("Flicked bullion coin",cb)
    o=disk("Coin bevelled grip edge",cb,(0,0,0),.057,.016,brass,coin);k.apply_prop_ink(o,cb,thickness=.002)
    disk("Coin stamped face",cb,(0,-.011,0),.046,.009,gold[2],coin)
    disk("Coin star seal",cb,(0,-.017,0),.021,.005,glow,coin)
    gas_col=[k.surface("Neon lime vapor","#6bfd40",.87,glow=2.25),
             k.surface("Lime vapor cool rim","#269239",.89,glow=1.15)]
    rng=Random(55)
    puffs=[k.ball("Rounded cartoon shock cloud",ca,(0,0,0),(.23,.25,.26),gas_col[i%2],segments=18,rings=12)
           for i in range(8)]
    for puff in puffs:
        for polygon in puff.data.polygons:
            polygon.use_smooth=True
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
    for f in range(1,262):
        tension=step(f,8,62)
        needle=-1.87+3.97*step(f,4,63)+.047*math.sin(f*1.43)*tension
        pointer.rotation_euler.y=needle;channel(pointer,"rotation_euler",f)
        rim.data.energy=8+117*tension**2;channel(rim.data,"energy",f)
        expand=.03+step(f,63,80)
        for i,puff in enumerate(puffs):
            a=i*math.tau/len(puffs)
            plume=step(f,76,81)
            drift=.33*step(f,68,78)
            puff.location=(-.25+drift+.48*math.cos(a)*expand,.50-2.13*plume,.71+.52*math.sin(a)*expand+.26*plume)
            puff.scale=(expand*(.67+.073*i)+1.30*plume,)*3
            puff.hide_render=puff.hide_viewport=f<63
            for prop in ("location","scale","hide_render","hide_viewport"):channel(puff,prop,f)
        if f<=SWITCH:
            release=pop(f,64,68)
            sway=.017*math.sin(f*1.82)*tension
            elbows=[((s*(.225+.041*release),-.157,.145+.25*release),(s*.284,-.035,.20+.08*release)) for s in (-1,1)]
            legs=[((s*.166,-.039,.027),(s*.164,-.163,.29)) for s in (-1,1)]
            face="pop" if 64<=f<=69 else "strain"
            act.pose(f,(-.24,.16,0),-.11,.26+.18*tension-.32*release,elbows,legs,
                None if face==prevA else face,bounce=-.047-.136*tension+.063*release+sway,
                squash=1-.088*tension+.137*release,head_tilt=-.18+.044*math.sin(f*.28),
                sweat=min(1.,step(f,20,66)) if 20<=f<=72 else None)
            prevA=face
        if f>=SWITCH:
            cheer=pop(f,87,91)*(1-step(f,146,161))
            nudge=pop(f,164,168)*(1-step(f,187,196))
            flick=pop(f,178,182)*(1-step(f,186,198))
            story=step(f,198,226)
            syllable=min(.95,AUDIO[f-1]*6)*story
            bounce=-.222+.031*cheer+.020*flick+.020*syllable
            tilt=.061-.12*cheer+.21*story
            yaw=.045-.136*step(f,156,193)+.105*story
            root=Vector((0,.813,1.035))
            head_yaw=.08+.19*step(f,162,194)-.19*story
            head_tilt=.08-.14*cheer-.13*story+.017*math.sin(f*.35)
            glass_loc=Vector((0,-.200,.027+.100*(1-step(f,89,95))-.076*step(f,164,171)))
            rim_touch=(Euler((head_tilt,0,head_yaw)).to_quaternion()@
                       (glass_loc+Vector((-.165,-.002,-.006)))+Vector((0,0,k.FACE_CENTER-.59)))
            arms=[]
            for s in (-1,1):
                neutral=(s*.203,-.113,.183)
                hand=blend(neutral,(s*.393,-.032,.357),cheer)
                hand=hand.lerp(Vector((s*.311,-.281,.426+.065*math.sin(f*.18))),story*.8)
                if s==-1:hand=hand.lerp(rim_touch,min(1,nudge))
                else:hand=hand.lerp(Vector((.295,-.248,.490)),flick)
                arms.append((hand,(s*(.225+.066*cheer),-.102,.262+.084*cheer+.065*nudge*(s==-1))))
            feet=[((s*.169,-.665,-.129),(s*.182,-.424,.295)) for s in (-1,1)]
            face="wink" if f>=251 else "story" if f>=194 and AUDIO[f-1]>.027 else "smug"
            king.pose(f,root,yaw,tilt,arms,feet,None if face==prevB else face,bounce=bounce,
                      head_yaw=head_yaw,head_tilt=head_tilt)
            prevB=face
            crown.location=(.014,.026,.252+.248*(1-step(f,83,87))-.026*math.sin(math.pi*step(f,87,94)))
            crown.rotation_euler=(.11,.21-.16*step(f,85,91),-.165)
            glasses.location=glass_loc
            for p in ("location","rotation_euler"):channel(crown,p,f)
            channel(glasses,"location",f)
            tip=Vector(arms[1][0]); tip.z*=1
            tip=Euler((0,0,yaw)).to_quaternion()@(Euler((tilt,0,0)).to_quaternion()@tip+Vector((0,0,.59+bounce)))+root
            spin=step(f,181,202)
            coin.rotation_euler=(.28+spin*math.tau*2,spin*math.tau*3,-.24+spin*math.tau)
            coin.location=(tip-coin.rotation_euler.to_quaternion()@Vector((-.037,0,-.043))
                           +Vector((.14,-.21,.45))*math.sin(math.pi*spin))
            coin.hide_render=coin.hide_viewport=False
            for p in ("location","rotation_euler"):channel(coin,p,f)
            for i,(bill,data) in enumerate(zip(bills,locations)):
                x,y,z,a=data; age=(f-81)/30
                bill.location=(x+.23*math.sin(age*.86+a),y+.18*math.cos(age+a),z+.28*math.sin(age*.78+a)+.059*age)
                bill.rotation_euler=(1.04+.38*math.sin(age*2+a),.54*math.sin(age*1.4+a),a+.63*age)
                for p in ("location","rotation_euler"):channel(bill,p,f)
            for i,sp in enumerate(sparks):
                a=i*math.tau/len(sparks)+f*.074;v=step(f,83,116)
                sp.location=((.30+1.04*v)*math.cos(a),.84+.12*math.sin(4*a),2.05+(.29+.72*v)*math.sin(a))
                sp.scale=(max(.02,(1-v)*(.35+.60*abs(math.sin(a+f*.17)))),)*3
                for p in ("location","scale"):channel(sp,p,f)
        if f<SWITCH:
            t=step(f,1,80);shake=.012*t*math.sin(f*1.39)
            p=Vector((-.13+.22*t+shake,-3.04+.29*t,1.14-.15*t))
            aim=Vector((.205,.02,1.0-.12*t)); focus=Vector((-.25,.005,.99-.15*t));lens=35
        elif f<160:
            t=step(f,81,159)
            p=blend((-.20,-1.82,1.69),(-.15,-5.08,1.87),t)
            aim=blend((-.015,.74,1.99),(.04,.98,1.48),t)
            focus=Vector((0,.59,2.04));lens=34
        elif f<=198:
            u=step(f,160,168);v=step(f,168,198)
            p=blend((-.15,-5.08,1.87),(-.39,-2.20,1.94),u)+Vector((.36*v,.16*v,.06*v))
            aim=blend((.04,.98,1.48),(.006,.74,2.00),u)
            focus=Vector((0,.60,2.04));lens=34
        else:
            t=step(f,199,261)
            p=blend((-.03,-2.04,2.00),(.243,-1.66,2.00),t)
            aim=blend((.006,.74,2.00),(.025,.66,2.04),t)
            focus=Vector((.00,.47,2.02));lens=39
        forward=(aim-p).normalized()
        camera.location=p+(Vector((OFFSET,0,0)) if f>=SWITCH else Vector((0,0,0)))
        camera.rotation_mode="QUATERNION";camera.rotation_quaternion=forward.to_track_quat("-Z","Y")
        camera.data.lens=lens;camera.data.dof.focus_distance=(focus-p).dot(forward)
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
    for f,name in ((1,"Strain and pressure dial"),(64,"Gas release"),(81,"Gold shockwave stage switch"),
                   (89,"Clear vault reveal"),(160,"Vault whip-in"),(183,"Coin flick"),(198,"Storyteller"),(251,"Wink")):
        scene.timeline_markers.new(name,frame=f)
    scene.frame_set(1);scene.render.filepath="//frame_"
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"padoda_hook_v01.blend"))

if __name__=="__main__":build()


