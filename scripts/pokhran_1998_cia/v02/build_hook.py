"""Save the seven-beat v02 hook using the approved v01b environment builders."""
import math
from pathlib import Path
from random import Random
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE.parent/"v01b"), str(HERE.parent), str(ROOT/"scripts")]
import build as original
import ricks_v2_kit as k
from build import activate, aim_scan, bake_paper, camera_at, ease, group, key, mug_grip, stage_look
from hook_continuation import desk_legs, grip_target, LEGS, REST, pose, scan_panel, palette
from sets import box, cutaway, label, orbit, oval, trace, war_room

OUT = ROOT/"renders/pokhran_1998_cia/v02"
END = 444
CUTS = (67,91,175,229,370,397)
BENCH = (1,32,68,75,110,159,218,229,311,359,383,431)
CONTACT = (28,32,37,194,264,303,311,322,333,344,353,412,422,444)
LOCKS = (311,321,332,341,349)


def cast(collection,name,portrait):
    # Let the approved rig constructor load the v02 expression decals.
    before = original.HERE
    original.HERE = HERE
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
        for ridge in range(6):
            x=.024+ridge*.016
            trace(collection,"Milled iris leaf grooves",[(x,-.012,.005),(x+.018,-.012,.033)],
                  .0026,m["cyan"] if ridge%4==0 else m["ink"],pivot)
        blades.append(pivot)
    for j in range(3):
        oval(collection,"Optical ring bevel glint",0,-.674,-.06,.177+j*.025,.177+j*.025,
             m["cyan"] if j%2 else m["paper"],.0034).parent=satellite
    for j in range(54):
        angle=j*math.tau/54
        x,z=math.cos(angle),math.sin(angle)
        outer=.242 if j%3 else .252
        trace(collection,"Optical witness ticks",[(.221*x,-.681,-.06+.221*z),(outer*x,-.681,-.06+outer*z)],
              .0034,m["paper"] if j%3 else m["cyan"],satellite)
    rng=Random(632)
    for j in range(150):
        x,z=rng.uniform(-.30,.30),rng.uniform(-.36,.29)
        if math.hypot(x,z+.06)<.245:
            continue
        w=rng.uniform(.007,.025)
        trace(collection,"Fine wear marks on camera surround",[(x,-.36,z),(x+w,-.36,z+.006)],
              .0028,m["ink"] if j%3 else m["paper"],satellite)
    return blades


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
    button=k.cylinder("Glowing SCAN button",room[0],(-.60,-.007,.869),.071,.042,m["red"],length_segments=24)
    label(room[0],"SCAN",(-.60,-.087,.793),.069,m["paper"])
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
    for j,prop in enumerate(props):
        spark=k.empty(f"Graphic lock glint {j+1}",ground[0],(prop.location.x,.31,.61))
        points=[(.12*math.cos(i*math.tau/12),0,.12*math.sin(i*math.tau/12)) for i in range(12)]
        for x,y,z in points:
            trace(ground[0],"Two-frame amber cyan lock spark",[(x,y,z),(x*1.47,y,z*1.47)],.007,
                  m["cyan"] if x>0 else m["paper"],spark)
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
    for i in range(11):
        x=(i-5)*.34
        box(bunker[0],"Gallery frame rib",(x,.98,1.21),(.09,.088,2.42),m["steel"],True)
        box(bunker[0],"Storage panel and latch",(x,1.04,.53),(.306,.065,.72),m["navy"])
        box(bunker[0],"Gallery light bar",(x,.93,1.99),(.16,.04,.061),m["paper"])
    box(bunker[0],"Indigo gallery rear wall",(0,1.17,1.28),(5,.17,3),m["navy"])
    box(bunker[0],"Amber sandstone floor",(0,.12,-.075),(5,7,.15),m["sand"])
    from sets import lights
    lights(bunker[0],"#ffd29a","#6c95ff")
    kalam=cast(bunker[0],"Dr. Kalam","kalam")
    engineer=cast(bunker[0],"58th Regiment Engineer","engineer")
    pk=cast(kp[0],"Kalam portrait","kalam")
    pe=cast(ep[0],"Engineer portrait","engineer")
    stage_look(kp[0])
    stage_look(ep[0])
    cam=bpy.data.objects.new("Vertical 26 mm delivery camera",bpy.data.cameras.new("Hook lens"))
    s.collection.objects.link(cam)
    s.camera=cam
    k.setup_ricks_compositor(s,camera=cam)
    bake_paper(s)
    for f in range(1,END+1):
        if f<67 or f>=397:
            opening=f<67
            slam=.19*ease(f,15,26)+.81*ease(f,27,32)-ease(f,34,45)
            point=ease(f,39,52)
            sip=ease(f,400,419)-ease(f,421,427)
            root=Vector((-.31+.044*slam,.49,.035))
            yaw=.28 if opening else -.30
            tilt=.09+.135*slam-.16*sip
            elbow=(-.214,-.12,.285)
            planted=grip_target((-.60,-.010,.889-.012*slam),root,yaw,tilt,elbow)
            hand=Vector((-.223,-.123,.31)).lerp(planted,slam)
            left=hand.lerp(Vector((-.33,-.078,.62)),point) if opening else Vector((-.231,-.15,.34))
            right=Vector((.284,-.254,.388)).lerp(Vector((-.075,-.253,.55)),sip)
            mode="rest" if opening or f<408 else "sip"
            pose(boss,f,root,yaw,tilt,[(left,elbow),(right,(.263,-.142,.331+.13*sip))],
                 mode,(-.27*sip,.12*point if opening else -.07),desk_legs())
            mug_grip(mug,boss,f,root,yaw,tilt,sip)
            button.location.z=.871-.009*slam
            key(button,f,"location")
            if opening:
                move(cam,f,room,1,66,(-.90,-1.96,1.48),(-.57,-1.80,1.56),
                     (-.29,.28,1.13),(-.29,.29,1.20))
            else:
                move(cam,f,room,397,426,(.54,-2.11,1.42),(.48,-1.77,1.44),
                     (-.24,.31,1.18),(-.25,.30,1.23))
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
                spark.hide_render=spark.hide_viewport=not(hit<=f<hit+4)
                spark.scale=((1+.31*ease(f,hit,hit+4)) if hit<=f<hit+4 else .001,)*3
                key(spark,f,"hide_render","hide_viewport","scale")
            if f<229:
                move(cam,f,ground,175,228,(.16,-3.72,3.24),(-.22,-3.47,1.37),
                     (.02,.54,2.51),(-.44,.47,1.00))
            elif f<292 or f>=309:
                if f<292:
                    move(cam,f,ground,229,291,(-.22,-3.47,1.37),(-.77,-3.67,1.27),
                         (-.44,.47,1.00),(-.39,.44,1.00))
                else:
                    t=ease(f,309,369)
                    thud=.020 if f==LOCKS[-1] else -.008 if f==LOCKS[-1]+1 else 0
                    camera_at(cam,f,ground,(-.58+1.17*t,-4.52,1.37+thud),(-.17+.34*t,.45,.95))
            else:
                for rig,x,sign in ((kalam,-.39,1),(engineer,.41,-1)):
                    raise_hand=ease(f,292,303)
                    arms=[((-.22,-.124,.23+.31*raise_hand),(-.23,-.12,.26)),REST[1]]
                    pose(rig,f,(x,.13,0),sign*.21,.045,arms,"rest",(.02,sign*.03))
                move(cam,f,bunker,292,308,(-.34,-2.10,1.51),(-.22,-1.90,1.44),
                     (0,.17,1.19),(0,.16,1.23))
        else:
            move(cam,f,screen,370,389,(.06,-1.76,1.51),(.055,-1.67,1.50),
                 (0,1.30,1.46),(0,1.30,1.46),50)
    for f,stage,rig,expression in ((501,kp,pk,"rest"),(502,ep,pe,"rest"),(503,room,boss,"sip"),(504,room,boss,"shock")):
        is_boss=rig==boss
        root=Vector((-.31,.49,.035)) if is_boss else Vector((0,0,0))
        arms=[((-.23,-.14,.49),(-.25,-.11,.27)),((.25,-.25,.40),(.22,-.15,.3))]
        pose(rig,f,root,-.20,.055,arms,expression,(.06,-.09),desk_legs() if is_boss else LEGS)
        if is_boss:
            mug_grip(mug,boss,f,root,-.20,.055,0)
        camera_at(cam,f,stage,root+Vector((-.27,-1.51,1.30)),root+Vector((0,-.02,1.15)),26)
    for stage,expression in (
        (room,"(67 <= frame < 397) or (frame > 444 and frame != 503 and frame != 504)"),
        (space,"not (67 <= frame < 175)"),
        (ground,"not (175 <= frame < 292 or 309 <= frame < 370)"),
        (screen,"not (370 <= frame < 397)"),
        (bunker,"not (292 <= frame < 309)"),
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
                   (229,"Track across exhibit"),(292,"Gallery heroes"),(309,"Five lock-ins"),
                   (370,"Clear CRT macro"),(397,"Coffee payoff")):
        s.timeline_markers.new(name,frame=f)
    s.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"pokhran_part1_v02.blend"))


if __name__=="__main__":
    main()
