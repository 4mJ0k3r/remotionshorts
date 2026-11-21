"""Build a deterministic, new Bigg Boss courtyard reel using the Rick's v2 kit."""
import json
import math
from functools import lru_cache
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/bb_shark_slipper_reel/v01c"
ART=HERE/"art"
sys.path[:0]=[str(HERE),str(ROOT/"scripts")]
import ricks_v2_kit as k
from courtyard import stage, slipper
import graphic_materials as graphic

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
TURF_Z=0.
LOVE_ANKLE_Y=-.410
TORSO_SUPPORT=()
OBLIQUE=math.radians(17.5)


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
    # Open the throat and tuck the side panels back into the shoulders.
    shell=bmesh.new()
    shell.from_mesh(hood.data)
    hem=[]
    for face in shell.faces:
        pt=face.calc_center_median()
        if pt.z<-.155 and (abs(pt.x)<.15 or pt.y<-.15):
            hem.append(face)
    bmesh.ops.delete(shell,geom=hem,context="FACES_ONLY")
    for vertex in shell.verts:
        p=vertex.co
        tuck=k.look.ease5((-.135-p.z)/.12)
        p.x*=1-.32*tuck
        p.y=mix(p.y,.025,.86*tuck)
        p.z-=.070*tuck
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


@lru_cache(maxsize=None)
def pose_love(f):
    tucked=mix(.70,1.,ease(f,HOOD_SHOT+7,HOOD_SHOT+22))
    reaches=pop(f,HOOD_UP-9)*(1-ease(f,HOOD_UP+1,HOOD_UP+8))
    hurt=pop(f,HIT,4)
    tremble=.014*math.sin(f*1.63)*tucked*(1-hurt) if SECOND<=f<THIRD or THOUGHT<=f<HIT else 0.
    if f<HOOD_SHOT:
        intent=math.sin(f*.061)*.4+.63
    else:
        intent=0.
    # The pelvis and feet stay fixed. The chest carries the tremble.
    yaw=.05
    tilt=.13+.23*tucked+.095*hurt+tremble
    squash=.90- (.065 if HIT<=f<HIT+2 else 0)
    # Evaluate the lowest vertex of the tilted pill, with the same transform
    # RicksCharacter.pose uses. Place it on the turf on every baked frame.
    sy=math.sin(tilt)
    cz=math.cos(tilt)*squash
    bottom=min(sy*y+cz*z for y,z in TORSO_SUPPORT)
    bounce=TURF_Z-.59-bottom
    head_tilt=-.24+.20*tucked-.22*hurt+.09*math.sin(f*.105)*intent
    head_yaw=-.14*intent+.25*ease(f,THOUGHT+9,THOUGHT+24)-.33*hurt
    arms,legs=[],[]
    for side in (-1,1):
        # Root-local coordinates keep calves and soles in front of the pelvis.
        knee=(side*(.136-.012*tucked),-.326,.284+.023*tucked)
        ankle=(side*.116,LOVE_ANKLE_Y,.027)
        hand_contact=(side*.066,knee[1]-.058,knee[2]-.057)
        elbow_contact=(side*.178,knee[1]+.027,knee[2]-.064)
        fold_tip=body_local_point(hand_contact,tilt,bounce,squash)
        fold_elbow=body_local_point(elbow_contact,tilt,bounce,squash)
        gesturing=intent*(.79 if side==1 else .25)
        open_hand=(side*.268,-.23,.31+.080*math.sin(f*.13+side))
        tips=vlerp(fold_tip,open_hand,gesturing)
        tips=tips.lerp(Vector((side*.251,-.121,.637)),reaches)
        tips=tips.lerp(Vector((side*.212,-.176,.511)),hurt)
        elbows=vlerp(fold_elbow,(side*.218,-.096,.246),gesturing)
        elbows=elbows.lerp(Vector((side*.29,-.02,.37)),reaches)
        elbows=elbows.lerp(Vector((side*.283,-.033,.266)),hurt)
        arms.append((tips,elbows));legs.append((ankle,knee))
    return (LOVE,yaw,tilt,arms,legs),dict(bounce=bounce,head_tilt=head_tilt,
                                         head_yaw=head_yaw,squash=squash)


def body_local_point(point,tilt,bounce,squash):
    local=Euler((tilt,0,0)).to_quaternion().inverted()@(Vector(point)-Vector((0,0,.59+bounce)))
    local.z/=squash
    return local


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
    tilt=.72*bend-.36*wind+.28*fling
    bounce=-.34*bend-.016*wind
    position=Vector(scout_route(f))
    elbow=vlerp((.20,.011,.215),(.28,.20,.43),wind)
    elbow=elbow.lerp(Vector((.262,-.09,.37)),fling)
    hand=vlerp((.17,-.1,.13),(.30,.37,.589),wind)
    hand=hand.lerp(Vector((.187,-.54,.43)),fling)
    grab=pop(f,SILENT+9,7)*(1-ease(f,SILENT+18,SILENT+26))
    held=local_hand(GRAB+GROUND_ROTATION@AIR_GRIP,position,yaw,tilt,bounce,SCOUT_SCALE)
    hand=hand.lerp(held,min(1,grab))
    aim_amount=min(1.,wind)
    aiming=vlerp((-.14,-.108,.162),(-.385,-.390,.344),aim_amount)
    aim_elbow=vlerp((-.20,-.072,.238),(-.239,-.209,.365),aim_amount)
    arms=[(aiming,aim_elbow),(hand,elbow)]
    legs=[((s*.118,-.062+s*.039,.028),(s*.10,-.065-.09*bend,.318-.066*bend)) for s in (-1,1)]
    return (position,yaw,tilt,arms,legs),dict(bounce=bounce,head_tilt=.23*wind,
                                             head_yaw=-.20*ease(f,SILENT,SILENT+10))


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


def trajectory(face_mesh,sole_mesh):
    start_args,start_style=scout_state(FLIGHT)
    start=world_hand(start_args,start_style,1,SCOUT_SCALE)
    spin0=Euler((.6,.75,-.28)).to_quaternion()
    start-=spin0@AIR_GRIP
    # The back of the sole meets the evaluated hooded face at this surface socket.
    surface=BVHTree.FromPolygons([v.co for v in face_mesh.vertices],
                                [tuple(p.vertices) for p in face_mesh.polygons])
    socket,face_normal,*_=surface.ray_cast(Vector((.041,-.5,-.030)),Vector((0,1,0)))
    assert socket is not None
    point=face_point(HIT,socket)
    origin=face_point(HIT,(0,0,0))
    directions=tuple(face_point(HIT,axis)-origin for axis in ((1,0,0),(0,1,0),(0,0,1)))
    normal=(Matrix(directions).transposed().inverted().transposed()@face_normal).normalized()
    rotation=(normal.to_track_quat("Z","Y")@Quaternion((0,0,1),.40)
              @Quaternion((0,1,0),OBLIQUE))
    # Use the sole's actual support vertex against the tangent plane, so
    # tilting the sandal cannot push the lower edge through her face.
    local_normal=rotation.inverted()@normal
    sole_socket=min((v.co for v in sole_mesh.vertices),key=lambda p:p.dot(local_normal)).copy()
    end=point-rotation@sole_socket
    bounce=Vector((LOVE.x+.46,LOVE.y-.71,.037))
    return (start,spin0,end,rotation,bounce,point),sole_socket


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
        p=move((-1.98,-2.70,.62),(-1.82,-2.42,.585),1,HOOD_SHOT)
        t=move((-1.93,-.14,.491),(-1.91,-.14,.505),1,HOOD_SHOT);l=41
        focus=love_face
    elif f<SECOND:
        p=move((-1.82,-2.42,.585),(-1.78,-2.81,.62),HOOD_SHOT,SECOND)
        t=move((-1.91,-.14,.505),(-1.94,-.21,.495),HOOD_SHOT,SECOND);l=41
        focus=love_face
    elif f<MASK_SLIP:
        p=move((-1.73,-1.84,.593),(-1.69,-1.47,.559),SECOND,MASK_SLIP); l=44
        t=love_face+Vector((-.047,0,-.066));focus=love_face
    elif f<THIRD:
        u=ease(f,MASK_SLIP,MASK_SLIP+4)
        drift=ease(f,MASK_SLIP,THIRD)
        p=Vector((-1.69,-1.47+.166*u+.066*drift,.559-.015*u))
        t=love_face+Vector((-.020,0,-.023));l=44;focus=love_face
    elif f<THOUGHT:
        p=move((.74,-1.71,1.94),(.31,-1.42,1.48),THIRD,THOUGHT)
        t=move((1.97,2.46,1.53),(1.81,1.95,1.30),THIRD,THOUGHT)
        focus=Vector(scout_route(f))+Vector((0,-.10,1.10));l=44
    elif f<SILENT:
        p=move((-1.65,-1.87,.608),(-1.55,-1.55,.557),THOUGHT,SILENT)
        t=love_face+Vector((-.030,0,-.019));l=48;focus=love_face
    elif f<FLIGHT:
        u=ease(f,SILENT,SILENT+5)
        drift=ease(f,SILENT,FLIGHT)
        p=Vector((.10+.18*u,-2.84+.18*u+.16*drift,.79+.13*drift))
        t=Vector((1.66,-.13,.84-.16*ease(f,SILENT+10,SILENT+16)+.24*ease(f,SILENT+18,SILENT+38)))
        l=34;focus=Vector((1.50,-.32,.91))
    elif f<HIT:
        pos,_=sandal_pose(f,arc)
        drift=ease(f,FLIGHT,HIT)
        p=pos+Vector((.93-.16*drift,-.83+.07*drift,.51-.14*drift))
        t=pos+Vector((-.119,.034,-.034))
        l=38;focus=pos
    else:
        h=ease(f,HIT+8,TOTAL)
        shake=math.sin((f-HIT)*2.42)*.034*max(0,1-(f-HIT)/4)
        p=vlerp((-1.62,-2.12,.559),(-1.25,-5.22,1.93),h)+Vector((shake,0,-shake*.6))
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


def make_seat_shadows(col,root):
    shadow=k.emission("Love • soft turf contact","#0c1410",.4)
    n,l=shadow.node_tree.nodes,shadow.node_tree.links
    tex=n.new("ShaderNodeTexCoord")
    distance=n.new("ShaderNodeVectorMath")
    distance.operation="DISTANCE"
    distance.inputs[1].default_value=(.5,.5,0.)
    l.new(tex.outputs["UV"],distance.inputs[0])
    fade=n.new("ShaderNodeMapRange")
    fade.interpolation_type="SMOOTHERSTEP"
    fade.inputs["From Min"].default_value=.05
    fade.inputs["From Max"].default_value=.50
    fade.inputs["To Min"].default_value=.63
    fade.inputs["To Max"].default_value=0.
    l.new(distance.outputs["Value"],fade.inputs["Value"])
    ink=next(node for node in n if node.type=="EMISSION")
    out=next(node for node in n if node.type=="OUTPUT_MATERIAL")
    transparent=n.new("ShaderNodeBsdfTransparent")
    blend=n.new("ShaderNodeMixShader")
    l.new(fade.outputs[0],blend.inputs[0])
    l.new(transparent.outputs[0],blend.inputs[1])
    l.new(ink.outputs[0],blend.inputs[2])
    l.new(blend.outputs[0],out.inputs[0])
    shadow.surface_render_method="BLENDED"
    for name,x,y,rx,ry in (("Seat",0.,-.038,.215,.171),
                           ("Left sole",-.116,LOVE_ANKLE_Y-.021,.063,.082),
                           ("Right sole",.116,LOVE_ANKLE_Y-.021,.063,.082)):
        z=TURF_Z+.0018
        obj=k.mesh("Love • turf shadow • "+name,col,[(x-rx,y-ry,z),(x+rx,y-ry,z),
                  (x+rx,y+ry,z),(x-rx,y+ry,z)],[(0,1,2,3)],shadow,root,
                  uv=[(0,0),(1,0),(1,1),(0,1)])
        obj.visible_shadow=False


def main():
    global TORSO_SUPPORT
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    k.configure_ricks_scene(scene,frame_end=TOTAL,samples=8)
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.compression=0
    scene.render.image_settings.color_mode="RGB"
    scene.world=bpy.data.worlds.new("Courtyard • dusky indigo sky")
    scene.world.use_nodes=True
    bg=next(o for o in scene.world.node_tree.nodes if o.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#141F45")
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
    jet_ink=graphic.apply_cast(love,scout,HOOD_UP)
    for sneaker in [o for o in scout.root.children_recursive if "sneaker uppers" in o.name]:
        contour=k.apply_prop_ink(sneaker,cast,thickness=.0044)
        contour.id_data.data.materials[0]=jet_ink
    torso=bpy.data.objects["Love | graphic pill torso"]
    TORSO_SUPPORT=tuple((v.co.y+torso.location.y,v.co.z+torso.location.z)
                        for v in torso.data.vertices if v.co.z<0.)
    make_seat_shadows(cast,love.root)
    for s in (-1,1):
        pair=slipper(col,"Love • pink patterned flip-flop",(LOVE.x+.12+s*.129,-1.025,.030),True)
        pair.rotation_euler.z=.14*s
    chappal=slipper(cast,"Flying slipper • tan leather",GRAB)
    for part in chappal.children_recursive:
        if " • ink" in part.name:
            part.data.materials[0]=jet_ink
            part.modifiers[0].strength*=1.4
    chappal.rotation_mode="QUATERNION"
    stars,burst=make_effects(cast)
    camera=bpy.data.objects.new("Delivery camera",bpy.data.cameras.new("Portrait • 36 mm vertical"))
    scene.collection.objects.link(camera)
    scene.camera=camera
    k.setup_ricks_camera(camera)
    k.setup_ricks_compositor(scene,camera=camera)
    for node in scene.node_tree.nodes:
        if (node.type=="MIX_RGB" and node.blend_type=="ADD" and node.inputs[2].is_linked
            and node.inputs[2].links[0].from_node.type=="GLARE"):
            node.inputs[0].default_value=.44
    sole=bpy.data.objects["Flying slipper • tan leather • flattened sole"]
    arc,sole_socket=trajectory(bpy.data.objects["Love | ellipsoid head"].data,sole.data)
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
                mod.strength=-min(.0182,1.4*k.look.ink_width(dist,camera.data.lens,2.85))
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
    hit_point=chappal.matrix_world@sole_socket
    contact_error=(hit_point-arc[-1]).length
    print("SLIPPER_CONTACT_POINT_ERROR_M",contact_error,flush=True)
    assert contact_error<.001
    (OUT/"choreography.json").write_text(json.dumps({
        "frame_count":TOTAL,"audio_starts_1_based":[1,SECOND,THIRD],
        "silent_start":SILENT,"flight_start":FLIGHT,"contact_frame":HIT,
        "impact_sole_socket_local":list(sole_socket),"impact_obliquity_degrees":math.degrees(OBLIQUE),
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"bb_shark_slipper_v01c.blend"))

if __name__=="__main__":
    main()
