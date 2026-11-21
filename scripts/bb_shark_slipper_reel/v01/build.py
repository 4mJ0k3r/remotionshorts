"""Build a deterministic, new Bigg Boss courtyard reel using the Rick's v2 kit."""
import json
import math
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Euler, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/bb_shark_slipper_reel/v01"
ART=HERE/"art"
sys.path[:0]=[str(HERE),str(ROOT/"scripts")]
import ricks_v2_kit as k
from courtyard import stage, slipper

SOUND=json.loads((OUT/"timeline.json").read_text())
TOTAL=SOUND["frames"]
fsec=lambda seconds: 1+round(seconds*30)
SECOND=fsec(SOUND["samples"][0]/SOUND["rate"])
THIRD=fsec(sum(SOUND["samples"][:2])/SOUND["rate"])
SILENT=fsec(sum(SOUND["samples"])/SOUND["rate"])
HOOD_SHOT=fsec(8.05)
HOOD_UP=fsec(9.63)
MASK_SLIP=SECOND+112
THOUGHT=THIRD+60
FLIGHT=SILENT+42
HIT=SILENT+72
LOVE=Vector((-1.86,-.20,0))
GRAB=Vector((1.29,-.63,.032))
AIR_GRIP=Vector((.047,-.009,.040))
GROUND_ROTATION=Quaternion((0,0,1),.42)
SCOUT_SCALE=1.06
BROWN="#41302d"


def mix(a,b,t):
    return a+(b-a)*t


def ease(f,a,b):
    return k.look.ease5((f-a)/(b-a))


def pop(f,a,n=5):
    return 1.08*ease(f,a,a+n-1)-.08*ease(f,a+n-1,a+n+3)


def vlerp(a,b,t):
    return Vector(a).lerp(Vector(b),t)


def range_visibility(object_, start, final, show_before):
    for f, hide in ((1,not show_before),(start,show_before),(final,show_before)):
        object_.hide_render=object_.hide_viewport=hide
        for prop in ("hide_render","hide_viewport"):
            object_.keyframe_insert(prop,frame=f)
            for key in object_.animation_data.action.fcurves.find(prop).keyframe_points:
                key.interpolation="CONSTANT"


def off_camera(root, condition):
    """Cull a rig only in shots that frame the other side of the courtyard."""
    for obj in root.children_recursive:
        for channel in ("hide_render","hide_viewport"):
            animation=obj.animation_data
            action=animation.action if animation else None
            existing=action.fcurves.find(channel) if action else None
            if existing:
                prop="pose_"+channel
                obj[prop]=getattr(obj,channel)
                path=f'["{prop}"]'
                existing.data_path=path
            driver=obj.driver_add(channel).driver
            driver.expression=condition
            if existing:
                local=driver.variables.new()
                local.name="pose_hide"
                local.type="SINGLE_PROP"
                local.targets[0].id=obj
                local.targets[0].data_path=path
                driver.expression=condition+" or pose_hide > 0.5"


def camo_material():
    mat=k.surface("Love • four-color cloth shell","#626947",.92,glow=.07)
    n,l=mat.node_tree.nodes,mat.node_tree.links
    tex=n.new("ShaderNodeTexCoord")
    noise=n.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=7.3
    noise.inputs["Detail"].default_value=1.6
    l.new(tex.outputs["Generated"],noise.inputs[0])
    ramp=n.new("ShaderNodeValToRGB")
    k.look._ramp(ramp,[(.0,"#343831"),(.35,"#504438"),(.47,"#687455"),(.61,"#99815a"),(.72,"#443a35")],"CONSTANT")
    p=next(o for o in n if o.type=="BSDF_PRINCIPLED")
    l.new(noise.outputs["Fac"],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs["Base Color"])
    return mat


def build_cast(c):
    love_art={p.stem:p for p in ART.glob("*.png") if p.stem[:-1] in ("scheme","cheeky","sad","evil","hurt")}
    scout_art={p.stem:p for p in ART.glob("*.png") if p.stem[:-1] in ("scout","glare")}
    # The kit subdivides the hair and its outline twice. Reduce the base
    # rings for this stage while retaining the smooth 48-segment face mesh.
    original_ring=k.RING
    try:
        k.RING=24
        love=k.build_ricks_character("Love",c,costume_image=ART/"camo.png",expression_images=love_art,
                                     initial_expression="scheme0")
        scout=k.build_ricks_character("Scout",c,costume_image=ART/"tee.png",expression_images=scout_art,
                                      initial_expression="scout0")
    finally:
        k.RING=original_ring
    # Sculptural hair extensions augment the kit's offset subdivided scalp.
    hair=k.surface("Love • dark chestnut locks",BROWN,.59,glow=.064)
    plain_hair=[o for o in love.head.children if "hair cap" in o.name or "chestnut highlight" in o.name]
    for side in (-1,1):
        curls=k.ball("Love • long sweeping hair lock",c,(side*.176,.011,-.145),
                     (.091,.151,.258),hair,love.head,segments=24,rings=15)
        curls.rotation_euler.y=side*.16
        plain_hair.append(curls)
        love.ink_modifiers.append(k.apply_character_ink(curls,c))
    for obj in plain_hair:
        for part in [obj,*obj.children]:
            range_visibility(part,HOOD_UP,TOTAL,True)
    camo=camo_material()
    hood=k.hood("Love",c,love.head,camo,k.surface("Love • hood shadow lining","#0b0d18",.97,glow=.10))
    # Open the lower lip into hanging side panels instead of wrapping the chin.
    shell=bmesh.new()
    shell.from_mesh(hood.data)
    hem=[face for face in shell.faces if len(face.verts)==4
         and face.calc_center_median().z<-.16 and face.calc_center_median().y<-.115]
    bmesh.ops.delete(shell,geom=hem,context="FACES_ONLY")
    shell.to_mesh(hood.data)
    shell.free()
    hood_ink=k.apply_character_ink(hood,c)
    love.ink_modifiers.append(hood_ink)
    hood_parts=[hood,hood_ink.id_data]
    for side in (-1,1):
        hood_parts.append(k.tube("Love • hood cheek wisps",c,[(side*.144,-.159,.127),(side*.177,-.169,.071),
                              (side*.174,-.154,.015),(side*.196,-.145,-.063)],.015,hair,love.head))
    for part in hood_parts:
        range_visibility(part,HOOD_UP,TOTAL,False)
    for frame,angle,lift in ((HOOD_UP,.24,.046),(HOOD_UP+4,-.035,-.007),(HOOD_UP+8,0.,0.)):
        hood.rotation_euler.x=angle
        hood.location.z=lift
        hood.keyframe_insert("location",frame=frame)
        hood.keyframe_insert("rotation_euler",frame=frame)
    for actor,color,leg_color in ((love,camo,"#262431"),(scout,k.surface("Scout • tee cloth","#e9e5db",.85),"#686879")):
        torso=next(o for o in actor.body.children if "pill torso" in o.name)
        torso.data.materials[0]=color
        joggers=k.surface(actor.name+" • slim lower ink",leg_color,.85)
        for leg in actor.legs:
            leg.data.materials[0]=joggers
        for limb in (*actor.arms,*actor.legs):
            limb.data.resolution_u=7
            limb.data.bevel_resolution=2
            limb.data.splines[0].use_smooth=True
        if actor==scout:
            shoe=k.surface("Scout • bright vermilion sneakers","#d23647",.74,glow=.11)
            white=k.surface("Scout • rubber midsoles","#d1c4bd",.82)
            for foot in actor.feet:
                foot.data.materials[0]=shoe
                k.ball("Scout • sneaker midsoles",c,(0,-.007,-.010),(.027,.040,.007),white,foot,
                       segments=12,rings=8)
                k.ball("Scout • sneaker uppers",c,(0,-.008,.007),(.028,.042,.018),shoe,foot,
                       segments=12,rings=8)
    scout.root.scale=(SCOUT_SCALE,)*3
    return love,scout


def face_state(f):
    rms=SOUND["rms"][f-1]
    mouth=int(rms>.018)+int(rms>.072)
    if f<HOOD_UP:
        mode="cheeky" if f>=fsec(8.63) else "scheme"
    elif f<SECOND:
        mode="sad"
    elif f<MASK_SLIP:
        mode="sad"
    elif f<THIRD-7:
        mode="evil"
    elif f<THIRD:
        mode="sad"
    elif f<THOUGHT:
        mode="sad"; mouth=0
    elif f<HIT:
        mode="evil"; mouth=0
    else:
        return "hurt0"
    return f"{mode}{mouth}"


def pose_love(f):
    tucked=ease(f,HOOD_SHOT+7,HOOD_SHOT+22)
    reaches=pop(f,HOOD_UP-9)*(1-ease(f,HOOD_UP+1,HOOD_UP+8))
    hurt=pop(f,HIT,4)
    tremble=.014*math.sin(f*1.63)*tucked*(1-hurt) if SECOND<=f<THIRD or THOUGHT<=f<HIT else 0.
    if f<HOOD_SHOT:
        intent=math.sin(f*.061)*.4+.63
    else:
        intent=0.
    yaw=.05-.15*ease(f,THOUGHT+11,THOUGHT+28)+.12*hurt
    tilt=.10+.10*tucked+.089*hurt
    # Keep the lower pill against the turf as the knees fold up around it.
    bounce=-.573+tremble-.011*hurt
    squash=.90- (.065 if HIT<=f<HIT+2 else 0)
    head_tilt=-.065+.18*tucked-.22*hurt+.09*math.sin(f*.105)*intent
    head_yaw=-.14*intent+.25*ease(f,THOUGHT+9,THOUGHT+24)-.33*hurt
    arms,legs=[],[]
    for side in (-1,1):
        open_hand=(side*(.237+.074*intent),-.17,.236+.09*math.sin(f*.13+side)*intent)
        folded=(side*.089,-.289,.484)
        tips=vlerp(open_hand,folded,tucked)
        tips=tips.lerp(Vector((side*.244,-.103,.623)),reaches)
        tips=tips.lerp(Vector((side*.212,-.176,.511)),hurt)
        elbows=vlerp((side*.218,-.051,.228),(side*.202,-.157,.272),tucked)
        elbows=elbows.lerp(Vector((side*.29,-.02,.37)),reaches)
        elbows=elbows.lerp(Vector((side*.283,-.033,.266)),hurt)
        bend=(side*(.174-.026*tucked),-.288-.024*tucked,.204+.203*tucked)
        ankle=(side*(.194-.062*tucked),-.473+.060*tucked,.028)
        arms.append((tips,elbows));legs.append((ankle,bend))
    return (LOVE,yaw,tilt,arms,legs),dict(bounce=bounce,head_tilt=head_tilt,
                                         head_yaw=head_yaw,squash=squash)


def scout_route(f):
    u=min(1,max(0,(f-THIRD)/(SILENT-THIRD-6)))
    # Central grass corridor left of the statue's large boots.
    return (mix(1.60,1.50,k.look.ease5(u)),mix(3.96,-.37,u),0.)


def scout_state(f):
    yaw=-.13-.70*ease(f,SILENT-10,SILENT+8)
    walking=SILENT-6
    if f<=walking:
        w=k.eval_stick_walk_cycle(f,scout_route,yaw,start_frame=THIRD-3,
               stop_frame=walking,plant_yaw=-.11,strength=1-ease(f,walking-11,walking))
        # Pocket-adjacent hands, with subdued forearm counter-swing.
        arms=[(Vector((s*.129,-.09,.117)).lerp(Vector(a[0]),.22),vlerp((s*.184,.009,.23),a[1],.34))
              for a,s in zip(w.arms,(-1,1))]
        foot_offset=Vector((0,-.021,-.010))
        # Re-express the kit's fixed world anchors in the taller rig's coordinates.
        legs=[((Vector(ankle)+foot_offset)/SCOUT_SCALE-foot_offset,knee) for ankle,knee in w.legs]
        return (w.location,w.yaw,w.tilt,arms,legs),dict(bounce=w.bounce)
    bend=pop(f,SILENT+8,7)*(1-ease(f,SILENT+18,SILENT+27))
    wind=pop(f,SILENT+30,4)*(1-ease(f,FLIGHT-5,FLIGHT+1))
    fling=pop(f,FLIGHT-4,5)*(1-ease(f,FLIGHT+9,FLIGHT+18))
    tilt=.72*bend-.21*wind+.28*fling
    bounce=-.34*bend-.016*wind
    position=Vector(scout_route(f))
    elbow=vlerp((.20,.011,.215),(.28,.20,.43),wind)
    elbow=elbow.lerp(Vector((.262,-.09,.37)),fling)
    hand=vlerp((.17,-.1,.13),(.30,.37,.589),wind)
    hand=hand.lerp(Vector((.187,-.54,.43)),fling)
    grab=pop(f,SILENT+9,7)*(1-ease(f,SILENT+18,SILENT+26))
    held=local_hand(GRAB+GROUND_ROTATION@AIR_GRIP,position,yaw,tilt,bounce,SCOUT_SCALE)
    hand=hand.lerp(held,min(1,grab))
    arms=[((-.14,-.108,.162),(-.20,-.072,.238)),(hand,elbow)]
    legs=[((s*.118,-.062+s*.039,.028),(s*.10,-.065-.09*bend,.318-.066*bend)) for s in (-1,1)]
    return (position,yaw,tilt,arms,legs),dict(bounce=bounce,head_yaw=-.20*ease(f,SILENT,SILENT+10))


def local_hand(point,root,yaw,tilt,bounce,scale):
    q=Euler((0,0,yaw)).to_quaternion()
    tip=q.inverted()@(Vector(point)-Vector(root))/scale-Vector((0,0,.59+bounce))
    return Euler((tilt,0,0)).to_quaternion().inverted()@tip


def world_hand(pose,style,side,scale=1.0):
    root,yaw,tilt,arms,_=pose
    body=Vector(arms[side][0])
    body.z*=style.get("squash",1.)
    p=Euler((tilt,0,0)).to_quaternion()@body + Vector((0,0,.59+style.get("bounce",0.)))
    return Vector(root)+Euler((0,0,yaw)).to_quaternion()@(p*scale)


def face_point(f,local):
    args,params=pose_love(f)
    root,yaw,tilt,_,_=args
    p=Euler((params["head_tilt"],0,params["head_yaw"])).to_quaternion()@Vector(local)
    p.z+=k.FACE_CENTER-.59
    p.z*=params["squash"]
    p=Euler((tilt,0,0)).to_quaternion()@p + Vector((0,0,.59+params["bounce"]))
    return Vector(root)+Euler((0,0,yaw)).to_quaternion()@p


def trajectory(face_mesh):
    start_args,start_style=scout_state(FLIGHT)
    start=world_hand(start_args,start_style,1,SCOUT_SCALE)
    spin0=Euler((.6,.75,-.28)).to_quaternion()
    start-=spin0@AIR_GRIP
    # The back of the sole meets the evaluated hooded face at this surface socket.
    surface=BVHTree.FromPolygons([v.co for v in face_mesh.vertices],
                                [tuple(p.vertices) for p in face_mesh.polygons])
    socket,*_=surface.ray_cast(Vector((.034,-.5,-.009)),Vector((0,1,0)))
    assert socket is not None
    point=face_point(HIT,socket)
    normal=(point-face_point(HIT,(socket.x,0,socket.z))).normalized()
    rotation=normal.to_track_quat("Z","Y")@Quaternion((0,0,1),.32)
    end=point-rotation@Vector((0,0,-.027))
    bounce=Vector((LOVE.x+.46,LOVE.y-.71,.037))
    return start,spin0,end,rotation,bounce,point


def sandal_pose(f,arc):
    start,spin0,end,hit_rotation,bounce,point=arc
    if f<SILENT+16:
        return GRAB,GROUND_ROTATION
    if f<FLIGHT:
        args,params=scout_state(f)
        spin=GROUND_ROTATION.slerp(spin0,ease(f,SILENT+20,SILENT+33))
        return world_hand(args,params,1,SCOUT_SCALE)-spin@AIR_GRIP,spin
    if f<HIT:
        t=(f-FLIGHT)/(HIT-FLIGHT)
        pos=start.lerp(end,t)
        pos.z+=.66*math.sin(math.pi*t)
        tangent=end-start+Vector((0,0,.66*math.pi*math.cos(math.pi*t)))
        facing=tangent.to_track_quat("-Y","Z")
        rolled=facing@Quaternion((0,1,0),math.tau*2.75*t+.40)
        rolled=spin0.slerp(rolled,ease(f,FLIGHT,FLIGHT+3))
        rolled=rolled.slerp(hit_rotation,ease(f,HIT-5,HIT))
        return pos,rolled
    if f<=HIT+1:
        return end,hit_rotation
    t=min(1,(f-HIT-1)/19)
    pos=end.lerp(bounce,k.look.ease5(t))
    pos.z+=.21*math.sin(math.pi*t)
    return pos,hit_rotation.slerp(Euler((0,0,.78)).to_quaternion(),k.look.ease5(t))


def make_effects(c):
    gold=k.emission("Comic stars • honey gold","#ffc461",2.1)
    ink=k.emission("Comic stars • warm black","#251b23",.72)
    stars=[]
    for j in range(3):
        verts=[((.061 if i%2==0 else .026)*math.sin(i*math.pi/5),0,
                (.061 if i%2==0 else .026)*math.cos(i*math.pi/5)) for i in range(10)]
        obj=k.mesh("Dizzy • revolving cartoon star",c,verts,[tuple(range(10))],gold)
        obj.visible_shadow=False
        stars.append(obj)
    burst=[]
    for j in range(10):
        a=j*math.tau/10
        cv,sn=math.cos(a),math.sin(a)
        poly=[(.18*cv,-.31,.18*sn),(.32*cv-.019*sn,-.32,.32*sn+.019*cv),
              (.44*cv,-.32,.44*sn),(.32*cv+.019*sn,-.32,.32*sn-.019*cv)]
        obj=k.mesh("Impact • radial flash spike",c,poly,[(0,1,2,3)],gold)
        obj.visible_shadow=False
        burst.append(obj)
    return stars,burst


def camera_state(f,arc):
    def move(a,b,start,end):
        return vlerp(a,b,ease(f,start,end))
    love_face=face_point(f,(0,-.11,.025))
    if f<HOOD_SHOT:
        p=move((-2.74,-2.63,1.03),(-2.52,-2.18,1.03),1,HOOD_SHOT)
        t=move((-1.96,-.14,.54),(-1.96,-.14,.55),1,HOOD_SHOT);l=38
        focus=love_face
    elif f<SECOND:
        p=move((-2.51,-2.18,1.03),(-2.72,-2.72,1.29),HOOD_SHOT,SECOND)
        t=move((-1.96,-.15,.55),(-2.04,-.23,.57),HOOD_SHOT,SECOND);l=38
        focus=love_face
    elif f<MASK_SLIP:
        p=move((-2.41,-2.14,1.01),(-2.36,-1.71,.91),SECOND,MASK_SLIP); l=49
        t=love_face+Vector((-.047,0,-.066));focus=love_face
    elif f<THIRD:
        u=ease(f,MASK_SLIP,MASK_SLIP+4)
        drift=ease(f,MASK_SLIP,THIRD)
        p=Vector((-2.36,-1.71+.21*u+.06*drift,.91-.029*u))
        t=love_face+Vector((-.020,0,-.023));l=49;focus=love_face
    elif f<THOUGHT:
        p=move((.74,-1.71,1.94),(.31,-1.42,1.48),THIRD,THOUGHT)
        t=move((1.97,2.46,1.53),(1.81,1.95,1.30),THIRD,THOUGHT)
        focus=Vector(scout_route(f))+Vector((0,-.10,1.10));l=44
    elif f<SILENT:
        p=move((-2.65,-2.03,1.00),(-2.34,-1.62,.85),THOUGHT,SILENT)
        t=love_face+Vector((-.030,0,-.019));l=48;focus=love_face
    elif f<FLIGHT:
        u=ease(f,SILENT,SILENT+5)
        drift=ease(f,SILENT,FLIGHT)
        p=Vector((.14+.34*u,-2.61+.28*u+.21*drift,.68+.20*drift))
        t=Vector((1.51,-.11,.81-.16*ease(f,SILENT+10,SILENT+16)+.23*ease(f,SILENT+18,SILENT+38)))
        l=38;focus=Vector((1.50,-.32,.91))
    elif f<HIT:
        pos,_=sandal_pose(f,arc)
        drift=ease(f,FLIGHT,HIT)
        p=pos+Vector((.93-.16*drift,-.83+.07*drift,.40-.16*drift))
        t=pos+Vector((-.119,.034,-.034))
        l=38;focus=pos
    else:
        h=ease(f,HIT+8,TOTAL)
        shake=math.sin((f-HIT)*2.42)*.034*max(0,1-(f-HIT)/4)
        p=vlerp((-1.53,-2.06,.97),(-1.25,-5.22,1.93),h)+Vector((shake,0,-shake*.6))
        t=vlerp(love_face+Vector((0,0,-.021)),(-1.61,.15,.83),h)
        l=38;focus=love_face
    roll=math.radians(6)*ease(f,MASK_SLIP,MASK_SLIP+4) if MASK_SLIP<=f<THIRD else 0.
    return p,t,focus,l,roll


def apply_camera(camera,data):
    p,t,focus,l,roll=data
    camera.location=p
    direction=(t-p).normalized()
    camera.rotation_mode="QUATERNION"
    camera.rotation_quaternion=direction.to_track_quat("-Z","Y")@Quaternion((0,0,1),roll)
    camera.data.lens=l
    camera.data.dof.focus_distance=max(.07,(focus-p).dot(direction))


def marker(scene,name,frame):
    scene.timeline_markers.new(name,frame=frame)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    k.configure_ricks_scene(scene,frame_end=TOTAL,samples=8)
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.compression=0
    scene.render.image_settings.color_mode="RGB"
    scene.world=bpy.data.worlds.new("Courtyard • dusky indigo sky")
    scene.world.use_nodes=True
    bg=next(o for o in scene.world.node_tree.nodes if o.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#384264")
    bg.inputs[1].default_value=.32
    col=bpy.data.collections.new("Courtyard • one connected physical set")
    scene.collection.children.link(col)
    cast=bpy.data.collections.new("Cast and choreography")
    scene.collection.children.link(cast)
    stage(col)
    for obj in col.objects:
        if obj.type=="CURVE":
            obj.data.resolution_u=4 if len(obj.data.splines[0].bezier_points)>6 else 6
            obj.data.bevel_resolution=2 if "gum" in obj.name or "Golden arch" in obj.name else 1
            for spline in obj.data.splines:
                spline.use_smooth=True
    love,scout=build_cast(cast)
    for s in (-1,1):
        pair=slipper(col,"Love • pink patterned flip-flop",(LOVE.x+.12+s*.129,-1.025,.030),True)
        pair.rotation_euler.z=.14*s
    chappal=slipper(cast,"Flying slipper • tan leather",GRAB)
    chappal.rotation_mode="QUATERNION"
    stars,burst=make_effects(cast)
    camera=bpy.data.objects.new("Delivery camera",bpy.data.cameras.new("Portrait • 36 mm vertical"))
    scene.collection.objects.link(camera)
    scene.camera=camera
    k.setup_ricks_camera(camera)
    k.setup_ricks_compositor(scene,camera=camera)
    arc=trajectory(bpy.data.objects["Love | ellipsoid head"].data)
    camera_samples={}
    prev_love,prev_scout=None,None
    for f in range(1,TOTAL+1):
        pose,style=pose_love(f)
        face=face_state(f)
        love.pose(f,*pose,expression=None if face==prev_love else face,**style)
        prev_love=face
        # Before his entrance the runner is parked deep inside the entrance recess.
        sg,ss=scout_state(max(f,THIRD-1))
        face="glare0" if f>=SILENT+5 else "scout0"
        scout.pose(f,*sg,expression=None if face==prev_scout else face,**ss)
        prev_scout=face
        chappal.location,chappal.rotation_quaternion=sandal_pose(f,arc)
        for prop in ("location","rotation_quaternion"):
            chappal.keyframe_insert(prop,frame=f)
        cam=camera_state(f,arc)
        apply_camera(camera,cam)
        camera_samples[str(f)]=list(camera.location)
        for prop in ("location","rotation_quaternion"):
            camera.keyframe_insert(prop,frame=f)
        for prop in ("lens","dof.focus_distance"):
            camera.data.keyframe_insert(prop,frame=f)
        for a,p in ((love,face_point(f,(0,0,0))),(scout,Vector(sg[0])+Vector((0,0,1.18)))):
            dist=(p-camera.location).length
            for mod in a.ink_modifiers:
                mod.strength=-min(.013,k.look.ink_width(dist,camera.data.lens,2.85))
                mod.keyframe_insert("strength",frame=f)
        if f in (1,HIT,HIT+4):
            for obj in burst:
                obj.location=(LOVE.x,LOVE.y,.59)
                obj.hide_render=obj.hide_viewport=f!=HIT
                for prop in ("hide_render","hide_viewport"):
                    obj.keyframe_insert(prop,frame=f)
        for j,obj in enumerate(stars):
            a=.081*f+j*math.tau/3
            if f in (1,HIT+4):
                obj.hide_render=obj.hide_viewport=f<HIT+4
                for prop in ("hide_render","hide_viewport"):
                    obj.keyframe_insert(prop,frame=f)
            if f>=HIT+4:
                obj.location=(LOVE.x+.315*math.cos(a),LOVE.y-.093+.18*math.sin(a),.842+.073*math.sin(a))
                obj.rotation_euler.y=a
                for prop in ("location","rotation_euler"):
                    obj.keyframe_insert(prop,frame=f)
    love.finish_bake()
    scout.finish_bake()
    for action in bpy.data.actions:
        for curve in action.fcurves:
            disc=curve.data_path in ("hide_render","hide_viewport","lens")
            for key in curve.keyframe_points:
                key.interpolation="CONSTANT" if disc else "LINEAR"
    off_camera(love.root,f"({THIRD} <= frame < {THOUGHT}) or ({SILENT} <= frame < {FLIGHT})")
    off_camera(scout.root,f"(frame < {THIRD}) or ({THOUGHT} <= frame < {SILENT}) or (frame >= {HIT})")
    for label,f in (("1 • Love schemes",1),("2 • Acting start",HOOD_SHOT),("Hood up",HOOD_UP),
                   ("3A • Shivering",SECOND),("3B • Mask slip",MASK_SLIP),("4 • Scout enters",THIRD),
                   ("5 • Internal voice",THOUGHT),("6A • Silent wind-up",SILENT),
                   ("6B • Flight",FLIGHT),("6C • Impact",HIT)):
        marker(scene,label,f)
    cuts=[SECOND,MASK_SLIP,THIRD,THOUGHT,SILENT,FLIGHT,HIT]
    scene.frame_set(HIT)
    bpy.context.view_layer.update()
    hit_point=chappal.matrix_world@Vector((0,0,-.027))
    contact_error=(hit_point-arc[-1]).length
    print("SLIPPER_CONTACT_POINT_ERROR_M",contact_error,flush=True)
    assert contact_error<.001
    (OUT/"choreography.json").write_text(json.dumps({
        "frame_count":TOTAL,"audio_starts_1_based":[1,SECOND,THIRD],
        "silent_start":SILENT,"flight_start":FLIGHT,"contact_frame":HIT,
        "impact_contact_error_m":contact_error,"cut_frames_1_based":cuts,
        "calibration_frames":[55,HOOD_UP+1,SECOND+52,MASK_SLIP+24,THIRD+17,
                              THOUGHT+50,FLIGHT-9,FLIGHT+13,HIT,TOTAL-9],
        "camera_positions":camera_samples},indent=2))
    scene.frame_set(1)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=="VIEW_3D":
                area.spaces.active.region_3d.view_perspective="CAMERA"
    scene.render.filepath="//frame_"
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"bb_shark_slipper_v01.blend"))

if __name__=="__main__":
    main()
