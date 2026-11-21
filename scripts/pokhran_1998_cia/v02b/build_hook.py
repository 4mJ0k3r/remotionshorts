"""Save the seven-beat v02 hook using the approved v01b environment builders."""
import json
import math
from pathlib import Path
from random import Random
import sys

import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE.parent/"v01b"), str(HERE.parent), str(ROOT/"scripts")]
import build as original
import ricks_v2_kit as k
from build import activate, aim_scan, bake_paper, camera_at, ease, group, key, stage_look
from hook_continuation import LEGS, REST, pose, scan_panel, palette
from sets import box, cutaway, label, orbit, oval, trace, war_room

OUT = ROOT/"renders/pokhran_1998_cia/v02b"
END = 444
CUTS = (67,91,175,295,338,370,397)
BENCH = (1,32,68,75,110,159,215,290,315,359,383,420)
CONTACT = (25,30,32,37,194,215,254,278,315,337,412,420,429,444)
LOCKS = (242,254,266,278,290)


def cast(collection,name,portrait):
    # Let the approved rig constructor load the v02 expression decals.
    before = original.HERE
    original.HERE = HERE.parent/"v02"
    try:
        return original.cast(collection,name,portrait)
    finally:
        original.HERE = before


def move(cam,f,stage,a,b,p,q,u,v,lens=26):
    t=ease(f,a,b)
    camera_at(cam,f,stage,Vector(p).lerp(Vector(q),t),Vector(u).lerp(Vector(v),t),lens)


def make_iris(collection,satellite,m):
    blades=[]
    for j in range(9):
        pivot=k.empty("Aperture leaf axis",collection,(0,-.669,-.06),satellite)
        leaf=k.mesh("Iris fan leaf",collection,[(0,0,0),(.136,0,-.034),(.161,0,.030),(.087,0,.068),(.019,0,.045)],
                    [(0,1,2,3,4)],m["steel"],parent=pivot)
        leaf.location.y=-.001*j
        trace(collection,"Slim metallic edge on iris leaf",[(.031,-.012,.005),(.135,-.012,.027)],
              .0029,m["paper"],pivot)
        blades.append(pivot)
    for j in range(3):
        oval(collection,"Optical ring bevel glint",0,-.674,-.06,.177+j*.025,.177+j*.025,
             m["cyan"] if j%2 else m["paper"],.0034).parent=satellite
    rng=Random(632)
    for j in range(186):
        x,z=rng.uniform(-.30,.30),rng.uniform(-.36,.29)
        if math.hypot(x,z+.06)<.245:
            continue
        w=rng.uniform(.007,.025)
        trace(collection,"Fine wear marks on camera surround",[(x,-.36,z),(x+w,-.36,z+.006)],
              .0028,m["ink"] if j%3 else m["paper"],satellite)
    return blades


def desk_acting(f,boss,chair,mug,button,glow,cam,stage):
    opening=f<67
    press=ease(f,25,31)-ease(f,34,39)
    reach=ease(f,19,27)-ease(f,35,43)
    point=ease(f,42,53)
    sip=ease(f,404,416)-ease(f,421,429)
    yaw=(.18+.06*press) if opening else -.19
    tilt=(.019+.125*reach) if opening else -.12*sip
    head_angle=-.13*sip
    root=Vector((-.32,1.16 if opening else 1.14,.283))
    swivel=chair.rotation_euler
    swivel.z=yaw
    key(chair,f,"rotation_euler")
    z_button=.872-.016*press
    button.location.z=z_button
    glow.default_value=1.9+4.6*press
    key(button,f,"location")
    key(glow,f,"default_value")
    facing=Euler((0,0,yaw)).to_matrix()
    torso=Euler((tilt,0,0)).to_matrix()
    body_origin=root+Vector((0,0,.59))
    world_to_body=(facing@torso).transposed()
    right_elbow=Vector((-.20,-.13-.075*reach,.25+.035*reach))
    other_elbow=Vector((.19,-.12,.296))
    rest=Vector((-.22,-.14,.20))
    mug_base=Vector((-.425,.782,.914))
    mug_rotation=Euler((-.39*sip,0,math.pi+yaw))
    lip=facing@torso@(Vector((0,0,k.FACE_CENTER-.59))+
        Euler((head_angle,0,0)).to_matrix()@Vector((0,-.201*boss.head.scale.y,-.066*boss.head.scale.z)))+body_origin
    rim=mug_rotation.to_matrix()@Vector((0,-.072,.076))
    mug.location=mug_base.lerp(lip-rim,sip)
    mug.rotation_euler=mug_rotation
    key(mug,f,"location","rotation_euler")
    rim_delta=(mug.location+rim-lip).length
    handle=mug.location+mug_rotation.to_matrix()@Vector((.113,0,0))
    button_top=Vector((button.location.x,button.location.y,z_button+.021))
    if opening:
        end=rest.lerp(world_to_body@(button_top+Vector((0,0,.016))-body_origin),reach)
        end=end.lerp(Vector((-.29,-.085,.64)),point)
    else:
        grasp=ease(f,397,404)-ease(f,429,430)
        end=rest.lerp(world_to_body@(handle-body_origin),grasp)
    right=(end,right_elbow)
    left=(Vector((.22,-.18,.27)),other_elbow)
    legs=[((side*.125,-.045,-.245),(side*.149,-.27,.327)) for side in (-1,1)]
    expression="rest" if opening else "sip" if 411<=f<=429 else "rest"
    pose(boss,f,root,yaw,tilt,[right,left],expression,(head_angle,.10*point if opening else 0),legs)
    if opening:
        move(cam,f,stage,1,66,(-1.12,-2.60,2.28),(-.98,-2.48,2.22),
             (-.10,.42,1.088),(-.10,.52,1.14))
    else:
        move(cam,f,stage,397,429,(1.24,-2.72,2.16),(1.05,-2.55,2.15),
             (-.06,.48,1.11),(-.08,.53,1.16))
    hand_world=body_origin+facing@torso@end
    return {"button_palm_to_top_m":(hand_world-button_top).length if opening else None,
            "handle_to_mitten_m":(hand_world-handle).length if not opening else None,
            "rim_to_lips_m":rim_delta if not opening else None}


def thumbs_up(rig,index):
    outline=((-0.030,-.029),(.028,-.029),(.038,-.016),(.038,.007),(.029,.015),
             (.005,.015),(.003,.051),(-.012,.057),(-.024,.048),(-.024,.017))
    mitten=rig.studio_hands[index]
    mirror=1 if index==1 else -1
    for child in mitten.children:
        skin=child.data.vertices[0].co.y<0
        scale=.80 if skin else 1.0
        for vertex,(x,z) in zip(child.data.vertices,outline):
            vertex.co.x=x*scale*mirror
            vertex.co.z=z*scale


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    k.configure_ricks_scene(s,frame_end=END,samples=7)
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.compression=0
    s.world=bpy.data.worlds.new("Indigo night")
    s.world.use_nodes=True
    bg=next(node for node in s.world.node_tree.nodes if node.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#141e3b")
    bg.inputs[1].default_value=.34
    room=group(s,"CIA surveillance room",0)
    space=group(s,"Keyhole stylized orbit",25)
    ground=group(s,"Twilight Thar cross-section",50)
    screen=group(s,"CRT insert",75)
    bunker=group(s,"Side gallery with cast",100)
    kp=group(s,"Kalam portrait",125)
    ep=group(s,"Engineer portrait",150)
    boss=cast(room[0],"CIA Boss","analyst")
    mug=war_room(room[0],boss)
    m=palette()
    plaque=bpy.data.objects["1998 / INTELLIGENCE"]
    plaque.location.x=.045
    plaque.data.size=.071
    leather=k.surface("Midnight plum executive chair leather","#222032",.68)
    trim=k.surface("Chair edge piping","#565466",.69)
    chair=k.empty("Executive swivel chair",room[0],(-.32,1.14,0))
    box(room[0],"Low upholstered swivel seat",(0,-.032,.876),(.54,.47,.075),leather,True,parent=chair)
    box(room[0],"High upholstered backrest",(0,.199,1.234),(.61,.102,.74),leather,True,parent=chair)
    for x in (-.269,.269):
        trace(room[0],"Contrasting seat piping",[(x,.148,.92),(x,.148,1.53),(x*.85,.148,1.581)],.010,trim,chair)
    k.cylinder("Swivel chair pedestal",room[0],(0,.02,.432),.051,.84,trim,chair,length_segments=16)
    for j in range(5):
        a=j*math.tau/5
        trace(room[0],"Swivel chair foot",[(0,.02,.085),(.265*math.cos(a),.02+.265*math.sin(a),.052)],
              .024,leather,chair)
    switch=k.emission("Red SCAN actuator","#ff3a51",1.84)
    button=k.cylinder("Glowing SCAN button",room[0],(-.566,.690,.872),.066,.042,switch,length_segments=24)
    glow=next(n for n in switch.node_tree.nodes if n.type=="EMISSION").inputs["Strength"]
    box(room[0],"Graphite button deck",(-.566,.690,.843),(.18,.19,.029),m["navy"],True)
    label(room[0],"SCAN",(-.566,.593,.842),.052,m["paper"])
    # A lighter rectangular glasses contour frames the larger eye cards.
    for obj in room[0].objects:
        if obj.name.startswith("Single clean rectangular lens rim"):
            obj.scale.x=1.05
            obj.scale.z=1.57
            obj.location.z=-.057
            obj.data.bevel_depth=.003
    satellite,sweep,orbital_scan=orbit(space[0])
    iris=make_iris(space[0],satellite,m)
    reticle=oval(space[0],"Two-frame lens glow",0,-.680,-.06,.157,.157,m["red"],.010)
    reticle.parent=satellite
    label(space[0],"RAJASTHAN",(.36,1.17,.14),.112,m["paper"])
    photos=[]
    for j in range(4):
        col=space[0] if j<3 else ground[0]
        x=-.40+.43*j
        photo=k.empty("Flying photogram",col,(x,.42,0))
        box(col,"Ivory contact-print frame",(0,0,0),(.24,.026,.21),m["paper"],True,parent=photo)
        box(col,"Bronze miniature aerial exposure",(0,-.018,.013),(.204,.011,.165),m["wood"],parent=photo)
        for i in range(6):
            trace(col,"Micro dune ridges",[(-.094+q*.024,-.027,-.060+i*.027+.009*math.sin(q*.92+i))
                 for q in range(9)],.0028,m["cyan"],photo)
        photos.append(photo)
    _,desert_scan=cutaway(ground[0])
    label(ground[0],"POKHRAN / RAJASTHAN",(-.52,.47,2.17),.118,m["paper"])
    props=sorted([o for o in ground[0].objects if o.name.startswith("Sealed symbolic test canister")],key=lambda o:o.location.x)
    rims=[o for o in ground[0].objects if o.name.startswith("Amber canister rim")]
    rim_heights={r.name:r.location.z for r in rims}
    sparks=[]
    arc_blue=k.emission("Hot cyan lock highlight","#64e9fd",3.6)
    arc_gold=k.emission("Hot amber lock highlight","#ffd385",3.6)
    for j,prop in enumerate(props):
        spark=k.empty(f"Graphic lock glint {j+1}",ground[0],(prop.location.x,.282,.61))
        for index in range(16):
            a=index*math.tau/16
            x,z=.13*math.cos(a),.16*math.sin(a)
            length=1.4+.28*math.sin(4.1*index)**2
            trace(ground[0],"Cut steel impact spark",[(x,0,z),(x*length,0,z*length)],.011,
                  arc_blue if index%2 else arc_gold,spark)
        sparks.append(spark)
    y=scan_panel(screen[0],m,(0,1.42,1.44),1.64,1.32)
    box(screen[0],"Graphic clear-result banner",(0,y-.023,1.41),(1.22,.022,.65),m["navy"],True)
    label(screen[0],"POKHRAN SECTOR",(0,y-.043,1.60),.109,m["paper"])
    label(screen[0],"100% CLEAR",(0,y-.043,1.26),.125,m["green"])
    trace(screen[0],"Graphic green check",[(-.11,y-.046,1.458),(-.027,y-.046,1.384),(.129,y-.046,1.518)],.027,m["green"])
    for i in range(17):
        box(screen[0],"Horizontal vent on CRT housing",(-.8+i*.10,1.322,.705),(.051,.02,.021),m["green"])
    rng=Random(96)
    for i in range(120):
        x,z=rng.uniform(-.79,.79),rng.uniform(.82,2.05)
        if abs(x)<.62 and 1.08<z<1.74:
            continue
        half=rng.uniform(.012,.042)
        trace(screen[0],"Scattered luminous scope readouts",[(x-half,y-.020,z),(x+half,y-.020,z)],
              .004,m["green"] if i%3 else m["paper"])
    # The cutaway remains a nontechnical exhibit. The two crew members get their own lit gallery insert.
    concrete=k.texture("Painted grooved concrete",("#333745","#59606c","#8d8789"),"plaster",(.72,.85))
    for i in range(11):
        x=(i-5)*.34
        box(bunker[0],"Gallery frame rib",(x,.98,1.21),(.049,.088,2.42),concrete,True)
        box(bunker[0],"Low inset concrete panel",(x,1.04,.53),(.306,.065,.72),m["steel"])
    for index in range(1,7):
        z=index*.29
        trace(bunker[0],"Incised concrete block seam",[(-2.5,1.071,z),(2.5,1.071,z)],.009,m["navy"])
    box(bunker[0],"Concrete gallery rear wall",(0,1.17,1.28),(5,.17,3),concrete)
    box(bunker[0],"Heavy concrete lintel",(0,.77,1.99),(3.42,.46,.16),concrete,True)
    box(bunker[0],"Concrete side return",(-1.66,.47,.98),(.16,1.09,2.0),concrete,True)
    for j in range(5):
        x=.22+j*.14
        box(bunker[0],"Five status lights in the gallery",(x,.949,1.65),(.072,.045,.044),arc_gold)
    from sets import scan_pyramid
    overhead=scan_pyramid(bunker[0],"Crimson scan well above the crew",.16)
    for x in (-.97,.86):
        box(bunker[0],"Inset amber wall sconce",(x,.93,1.81),(.21,.05,.058),m["paper"])
    box(bunker[0],"Amber sandstone floor",(0,.12,-.075),(5,7,.15),m["sand"])
    from sets import lights
    lights(bunker[0],"#ffd29a","#6c95ff")
    kalam=cast(bunker[0],"Dr. Kalam","kalam")
    engineer=cast(bunker[0],"58th Regiment Engineer","engineer")
    thumbs_up(kalam,1)
    thumbs_up(engineer,0)
    pk=cast(kp[0],"Kalam portrait","kalam")
    pe=cast(ep[0],"Engineer portrait","engineer")
    stage_look(kp[0])
    stage_look(ep[0])
    cam=bpy.data.objects.new("Vertical 26 mm delivery camera",bpy.data.cameras.new("Hook lens"))
    s.collection.objects.link(cam)
    s.camera=cam
    k.setup_ricks_compositor(s,camera=cam)
    bake_paper(s)
    contacts={}
    for f in range(1,END+1):
        if f<67 or f>=397:
            contact=desk_acting(f,boss,chair,mug,button,glow,cam,room)
            if f in (25,31,32,34,404,416,420,429,444):
                contacts[str(f)]=contact
        elif f<175:
            t=ease(f,91,173)
            satellite.rotation_euler=(.030-.12*t,.065+.18*t,-.08+.48*t)
            key(satellite,f,"rotation_euler")
            for j,blade in enumerate(iris):
                angle=j*math.tau/9
                aperture=ease(f,70,77)
                blade.location.x=.112*aperture*math.cos(angle)
                blade.location.z=-.06+.112*aperture*math.sin(angle)
                blade.rotation_euler.y=-angle-.54*aperture
                key(blade,f,"location","rotation_euler")
            lit=f in (75,76)
            reticle.hide_viewport=reticle.hide_render=not lit
            key(reticle,f,"hide_viewport","hide_render")
            sweep.location.y=.17+2.51*t
            key(sweep,f,"location")
            lens=satellite.location+satellite.rotation_euler.to_matrix()@Vector((0,-.671,-.06))
            aim_scan(orbital_scan,f,lens,(0,sweep.location.y,-.209),2.29,.42)
            for j,photo in enumerate(photos[:3]):
                shutter=(112,139,164)[j]
                progress=ease(f,shutter,shutter+12)
                photo.hide_render=photo.hide_viewport=not(shutter<=f<175)
                photo.location.z=-.18+.88*progress
                photo.location.y=.42+.11*j-.16*progress
                photo.rotation_euler.y=(j-1)*.33
                pulse=1.20*math.exp(-((f-shutter-2)/2.6)**2)
                photo.scale=(.02+.98*progress+pulse,)*3
                key(photo,f,"hide_render","hide_viewport","location","rotation_euler","scale")
            orbital_scan.active_material.node_tree.nodes.get("Emission").inputs["Strength"].default_value=(
                2.8+5.5*sum(math.exp(-((f-shot)/1.0)**2) for shot in (112,139,164)))
            key(orbital_scan.active_material.node_tree.nodes.get("Emission").inputs["Strength"],f,"default_value")
            if f<91:
                move(cam,f,space,67,90,(-.083,-1.77,1.39),(.022,-1.53,1.37),
                     (0,-.61,1.30),(0,-.65,1.30),52)
            else:
                move(cam,f,space,91,174,(-.84,-3.02,1.76),(1.13,-2.48,1.25),
                     (-.10,.38,.99),(.18,.44,.61))
        elif f<370:
            slip=ease(f,175,202)
            photos[3].location=(.77+1.15*slip,-.69,2.48-.16*slip)
            photos[3].rotation_euler.y=.22+.39*slip
            photos[3].scale=(.9 if f<201 else .001,)*3
            key(photos[3],f,"location","rotation_euler","scale")
            scan_x=-1.45+2.95*ease(f,175,370)
            aim_scan(desert_scan,f,(scan_x-.22,1.39,4.63),(scan_x,.57,1.98),.67,.47)
            for j,(p,hit) in enumerate(zip(props,LOCKS)):
                rest=.62
                z=rest+.48*(1-ease(f,hit-14,hit))+.021*(ease(f,hit,hit+2)-ease(f,hit+2,hit+6))
                p.location.z=z
                key(p,f,"location")
                for rim in (r for r in rims if abs(r.location.x-p.location.x)<.01):
                    base=rim_heights[rim.name]
                    rim.location.z=base+z-rest
                    key(rim,f,"location")
                spark=sparks[j]
                spark.hide_render=spark.hide_viewport=not(hit<=f<hit+6)
                spark.scale=((1.11+.39*ease(f,hit,hit+6)) if hit<=f<hit+6 else .001,)*3
                key(spark,f,"hide_render","hide_viewport","scale")
            if f<229:
                move(cam,f,ground,175,228,(.24,-4.64,3.32),(-.39,-4.57,1.42),
                     (.01,.54,2.41),(-.03,.47,1.04))
            elif f<295 or f>=338:
                if f<295:
                    t=ease(f,228,294)
                    thud=.020 if f==LOCKS[-1] else -.008 if f==LOCKS[-1]+1 else 0
                    camera_at(cam,f,ground,(-.39+.77*t,-4.57,1.42+thud),(-.03+.09*t,.47,1.04))
                else:
                    move(cam,f,ground,338,369,(.44,-4.64,1.59),(.64,-4.78,1.68),
                         (.06,.45,1.07),(.14,.48,1.14))
            else:
                scan=(f-295)/42
                aim_scan(overhead,f,(-1.25+2.8*scan,1.02,3.66),(-1.05+2.8*scan,.78,2.10),.70,.46)
                for index,(rig,x,sign) in enumerate(((kalam,-.39,1),(engineer,.43,-1))):
                    begin=302+4*index
                    salute=ease(f,begin,begin+5)-.12*ease(f,begin+6,begin+12)
                    glance=ease(f,295,301)-ease(f,322,336)
                    arms=list(REST)
                    hand=1 if sign==1 else 0
                    arms[hand]=((sign*.22,-.157,.24+.33*salute),(sign*.235,-.11,.27))
                    pose(rig,f,(x,.11+.07*index,0),sign*(.18+.19*glance),.045,arms,"rest",
                         (.02-.11*salute,sign*.11*glance))
                    mitten=rig.studio_hands[hand]
                    mitten.rotation_euler.y=(1 if hand==0 else -1)*.34
                    key(mitten,f,"rotation_euler")
                move(cam,f,bunker,295,337,(-.99,-2.04,1.61),(-.86,-1.91,1.56),
                     (0,.11,1.18),(0,.12,1.21))
        else:
            move(cam,f,screen,370,389,(.06,-1.76,1.51),(.055,-1.67,1.50),
                 (0,1.30,1.46),(0,1.30,1.46),50)
    for f,stage,rig,expression in ((501,kp,pk,"rest"),(502,ep,pe,"rest")):
        root=Vector((0,0,0))
        arms=[((-.23,-.14,.49),(-.25,-.11,.27)),((.25,-.25,.40),(.22,-.15,.3))]
        pose(rig,f,root,-.20,.055,arms,expression,(.06,-.09),LEGS)
        camera_at(cam,f,stage,root+Vector((-.27,-1.51,1.30)),root+Vector((0,-.02,1.15)),26)
    for stage,expression in (
        (room,"(67 <= frame < 397) or frame > 444"),
        (space,"not (67 <= frame < 175)"),
        (ground,"not (175 <= frame < 295 or 338 <= frame < 370)"),
        (screen,"not (370 <= frame < 397)"),
        (bunker,"not (295 <= frame < 338)"),
        (kp,"frame != 501"),(ep,"frame != 502"),
    ):
        activate(stage,expression)
    for rig in (boss,kalam,engineer,pk,pe):
        rig.finish_bake()
    for action in bpy.data.actions:
        for curve in action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation="CONSTANT" if "hide_" in curve.data_path or curve.data_path=="lens" else "LINEAR"
    for f,name in ((1,"Console slam"),(67,"Iris macro"),(91,"Orbital crane"),(175,"Desert dive"),
                   (229,"Five graphic lock-ins"),(295,"Bunker reaction"),(338,"Five locked markers"),
                   (370,"Clear CRT macro"),(397,"Coffee payoff")):
        s.timeline_markers.new(name,frame=f)
    s.frame_set(1)
    (OUT/"contact_targets.json").write_text(json.dumps(contacts,indent=2))
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"pokhran_part1_v02b.blend"))


if __name__=="__main__":
    main()
