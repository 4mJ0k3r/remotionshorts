"""Bake the isolated first act and four out-of-range look-development panels."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT/"scripts")]
import ricks_v2_kit as k
from cast import ART, LEGS, REST, act, figure, key, walk
from scenery import block, daylights, hallway, lettering, line, living_room, palette, street, sunny_puppy

OUT=ROOT/"renders/broken_headphones_shoko/v02"
END=790
CUTS=(1,75,124,256,319,370,423,528,578,633,663,715,741,760)
BENCH=(1,88,155,228,284,331,376,449,551,612,751,777)
PROOFS=(47,449,901,902,903,904)


def stage(s,name,offset):
    c=bpy.data.collections.new(name)
    s.collection.children.link(c)
    return c,offset


def activate(group,ranges):
    c,x=group
    anchor=k.empty(c.name+" root anchor",c)
    for obj in tuple(c.objects):
        if obj!=anchor and obj.parent is None:
            obj.parent=anchor
    anchor.location.x=x
    condition="not ("+" or ".join(f"{a} <= frame <= {b}" for a,b in ranges)+")"
    for obj in c.objects:
        if obj==anchor:
            continue
        for prop in ("hide_render","hide_viewport"):
            action=obj.animation_data.action if obj.animation_data else None
            curve=action.fcurves.find(prop) if action else None
            driver=obj.driver_add(prop).driver
            driver.expression=condition
            if curve:
                name="original_"+prop
                obj[name]=bool(getattr(obj,prop))
                curve.data_path=f'["{name}"]'
                variable=driver.variables.new()
                variable.name="pose_hidden"
                variable.type="SINGLE_PROP"
                variable.targets[0].id=obj
                variable.targets[0].data_path=curve.data_path
                driver.expression+=" or pose_hidden > .5"


def ease(f,a,b):
    return k.look.ease5((f-a)/(b-a))


def cam_view(cam,f,group,p,target,lens=26,focus=None):
    p=Vector(p)
    target=Vector(target)
    view=(target-p).normalized()
    cam.location=p+Vector((group[1],0,0))
    cam.rotation_mode="QUATERNION"
    cam.rotation_quaternion=view.to_track_quat("-Z","Y")
    cam.data.lens=lens
    outdoor=group[1] in (0,32,64)
    cam.data.dof.aperture_fstop=11 if lens>=45 else 2.8 if outdoor else 6.7 if lens>=32 else 4.6
    cam.data.dof.focus_distance=max(.11,(Vector(focus or target)-p).dot(view))
    key(cam,f,"location","rotation_quaternion")
    key(cam.data,f,"lens","dof.focus_distance","dof.aperture_fstop")


def slide(cam,f,group,a,b,p,q,target,aim,lens=26):
    t=ease(f,a,b)
    cam_view(cam,f,group,Vector(p).lerp(Vector(q),t),Vector(target).lerp(Vector(aim),t),lens)


def route(offset,first,last,delta):
    base=Vector(offset)
    delta=Vector(delta)
    def where(frame):
        return base+delta*max(0,min(1,(frame-first)/(last-first)))
    return where


def tape_heart(c,m,x,z,parent):
    points=[]
    for i in range(34):
        phase=i*math.tau/33
        a=math.sin(phase)
        b=math.cos(phase)
        points.append((x+.067*a**3,0,z+.0047*(13*b-5*math.cos(2*phase)-2*math.cos(3*phase)-math.cos(4*phase))))
    line(c,"Pink pencil-drawn floating heart",points,.006,m,parent)


def sparks(c,m,name):
    ctrl=k.empty(name,c)
    for j in range(10):
        a=j*math.tau/10
        x,z=math.cos(a),math.sin(a)
        line(c,"Little drawn lightning rays",[(x*.060,0,z*.060),(x*.136,0,z*.136)],.007,m["gold"],ctrl)
    return ctrl


def prop_pose(obj,f,location,scale=None,rotation=None):
    obj.location=location
    props=["location"]
    if scale is not None:
        obj.scale=(max(.0001,scale),)*3
        props.append("scale")
    if rotation is not None:
        obj.rotation_euler=rotation
        props.append("rotation_euler")
    key(obj,f,*props)


def drive_car(assembly,f,x,y,start):
    car,wheels=assembly
    prop_pose(car,f,(x,y,0))
    for wheel in wheels:
        wheel.rotation_euler.y=(x-start)/.151
        key(wheel,f,"rotation_euler")


def mute_icon(c,m,cam):
    parent=k.empty("Minimal crossed-out speaker icon",c,parent=cam)
    circle=k.cylinder("Matte ink circular icon field",c,(0,0,0),.072,.008,m["ink"],parent,length_segments=32)
    circle.rotation_euler.x=math.pi/2
    white=m["white"]
    k.mesh("Two-dimensional speaker wedge",c,[(-.037,-.008,-.017),(-.016,-.008,-.017),(.006,-.008,-.033),
           (.006,-.008,.033),(-.016,-.008,.017),(-.037,-.008,.017)],[(0,1,2,3,4,5)],white,parent)
    line(c,"Short speaker sound curve",[(.017,-.008,-.016),(.024,-.008,0),(.017,-.008,.016)],.004,white,parent)
    line(c,"Minimal slash across sound icon",[(-.043,-.013,.041),(.043,-.013,-.041)],.005,
         k.emission("Warm pink mute slash","#f29aaf",1.16),parent)
    return parent


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    k.configure_ricks_scene(s,frame_end=END,samples=6)
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.compression=0
    s.world=bpy.data.worlds.new("Soft studio ambient")
    s.world.use_nodes=True
    bg=next(n for n in s.world.node_tree.nodes if n.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#385275")
    bg.inputs[1].default_value=.44
    cam=bpy.data.objects.new("Native vertical camera",bpy.data.cameras.new("26mm Story Camera"))
    s.collection.objects.link(cam)
    s.camera=cam
    k.setup_ricks_compositor(s,camera=cam)
    cam.data.dof.aperture_fstop=3.38
    m=palette()
    sun=stage(s,"Brick terrace morning walk",0)
    home=stage(s,"The puppy's year-seven living room",16)
    wave=stage(s,"The classmate on the morning sidewalk",32)
    school=stage(s,"Blue tiled corridor and red lockers",48)
    chat=stage(s,"Brick rail courtyard chatter",64)
    drawing=stage(s,"Lined notebook confession insert",80)
    portrait=stage(s,"Shoko expression proof",96)
    boy_panel=stage(s,"Boy expressions and headphones proof",112)
    a,h,w,g,c,n,p,b=(item[0] for item in (sun,home,wave,school,chat,drawing,portrait,boy_panel))
    car=street(a,m)
    boy=figure(a,"Boy morning headphones","boy",expressions=("deadpan_blush","panic_sweat"))
    crush=figure(a,"Shoko morning walk","shoko",expressions=("shy_glance","chat_A","chat_E","chat_O","chat_M"))
    mute=mute_icon(a,m,cam)
    living_room(h,m)
    junior=figure(h,"Boy in year seven","boy",headphones=False,expressions=("year7_shock","panic_sweat"))
    puppy,pup_head,jaw,tail=sunny_puppy(h,m)
    year=k.empty("Gold Year 7 flashback insert",h)
    shadow=lettering(h,"YEAR 7",(0,.006,-.022),.156,m["ink"],year)
    shadow.data.offset=.012
    shadow.data.extrude=.003
    gold_year=lettering(h,"YEAR 7",(0,-.014,-.022),.156,m["gold"],year)
    gold_year.data.extrude=.004
    toy=k.empty("Year seven headphones on the rug",h,(.042,-.44,.105))
    line(h,"Headphones arched band on the rug",[(.203*math.cos(a),.143*math.sin(a),0)
         for a in (math.pi*i/22 for i in range(23))],.024,m["dark"],toy)
    for x in (-.203,.203):
        k.ball("Old headphones ear-pad",h,(x,0,-.027),(.057,.072,.065),m["dark"],toy,segments=20,rings=12)
    wire_route=[(-.18,-.449,.077),(-.31,-.542,.054),(-.45,-.573,.049),(-.56,-.518,.134),(-.640,-.447,.250)]
    line(h,"Headphone wire from rug to puppy mouth",wire_route,.016,m["ink"])
    line(h,"Silvery cable rim",[(x,y-.016,z+.008) for x,y,z in wire_route],.005,m["blue"])
    recoil=k.empty("Free chipped wire end",h)
    line(h,"Separate free cable end after chew",[(0,0,0),(.045,-.055,-.036),(.085,-.07,-.064)],
         .013,m["ink"],recoil)
    bite=sparks(h,m,"Graphic chew spark")
    wave_car=street(w,m)
    passing=figure(w,"Boy passing classmate","boy",expressions=("deadpan_blush",))
    friend=figure(w,"Friendly blazer classmate","classmate",expressions=("greet","smile"))
    hallway(g,m)
    schoolgirl=figure(g,"Shoko carrying books","shoko",compact=True,expressions=("shy_glance","worried_brows"))
    lockerboy=figure(g,"Boy against locker 207","boy",expressions=("deadpan_blush",),compact=True)
    student=figure(g,"School corridor student","classmate",expressions=("smile",),compact=True)
    books=k.empty("Schoolbook stack carried in both hands",g,(0,-.192,.222),schoolgirl.body)
    for j,cover in enumerate((m["red"],m["blue"],m["wood"])):
        block(g,"Schoolbook cover",(0,0,j*.057),(.27,.133,.043),cover,books)
        block(g,"Visible cream page block",(0,-.065,j*.057),(.232,.014,.028),m["cream"],books)
    street(c,m,courtyard=True)
    talking=figure(c,"Shoko expressive chatter","shoko",expressions=("happy_chatter","chat_A","chat_E","chat_O","chat_M","shy_glance"))
    listener=figure(c,"Boy walking under the cloud","boy",expressions=("deadpan_blush",))
    cloud=k.empty("Cartoon thundercloud",c)
    purple=k.make_cel_character_material("Soft blue-grey raincloud","#77768d")
    for j,(x,z,r) in enumerate(((-.17,0,.13),(-.06,.047,.156),(.069,.063,.153),(.181,-.013,.109),(.02,-.066,.131))):
        obj=k.ball("Soft joined cloud puff",c,(x,0,z),(r,.089,r*.78),purple,cloud,segments=18,rings=10)
        mod=k.apply_character_ink(obj,c,pixels=2.3)
        mod.id_data.data.materials[0]=m["ink"]
    bolt=k.mesh("Cartoon gold thunderbolt",c,[(.049,-.045,-.04),(-.071,-.045,-.241),(.025,-.045,-.228),
                 (-.024,-.045,-.39),(.171,-.045,-.195),(.070,-.045,-.215),(.146,-.045,-.056)],
                [(0,1,2,3,4,5,6)],m["gold"],cloud)
    fx=sparks(c,m,"Cloud zap graphic")
    # Close prop card is an original pencil illustration laid in a three-dimensional desk.
    block(n,"Amber notebook desk studio",(0,1.81,1.33),(6,.18,5),m["wood"])
    daylights(n,interior=True,warm=True)
    notebook=k.empty("Outlined lined sketchbook",n)
    block(n,"Book binding spine",(0,0,0),(.76,.047,.959),m["dark"],notebook)
    page=k.artwork("Original headphones notebook sketch",ART/"notebook.png",glow=.88)
    k.mesh("Pencil drawing on a lined page",n,[(-.355,-.028,-.452),(.355,-.028,-.452),
          (.355,-.028,.452),(-.355,-.028,.452)],[(0,1,2,3)],page,notebook,
          uv=[(0,0),(1,0),(1,1),(0,1)])
    pastel=k.emission("Rose pencil hearts","#f18eb5",1.25)
    hearts=[]
    for x,z in ((-.38,.15),(.41,.19),(-.39,-.11),(.33,-.20),(.26,.40),(-.21,.41)):
        heart=k.empty("Floating pink doodle",n)
        tape_heart(n,pastel,0,0,heart)
        hearts.append((heart,x,z))
    for j in range(13):
        z=.62+j*.106
        line(n,"Warm and plum tabletop inlay",[(-1.2,.37,z),(1.2,.37,z+.004)],.009,
             m["cream"] if j%3==0 else m["dark"])
    for x in (-.44,.43):
        line(n,"Side-by-side colored pencil",[(x,-.055,.82),(x+.024,-.055,1.53)],.028,
             m["red"] if x<0 else m["blue"])
    daylights(p,interior=True,warm=True)
    daylights(b,interior=True)
    block(p,"Lilac cast proof wall",(0,1.03,1.28),(6,.122,3.6),m["brick"])
    block(b,"Blue cast proof wall",(0,1.03,1.28),(6,.122,3.6),m["blue"])
    shy=figure(p,"Shoko cast expression pair","shoko",expressions=("shy_glance","deep_crimson_blush"))
    blush=figure(p,"Shoko crimson expression pair","shoko",expressions=("shy_glance","deep_crimson_blush"))
    neutral=figure(b,"Boy cast expression pair","boy",expressions=("deadpan_blush","panic_sweat"))
    panic=figure(b,"Boy wide-eyed cast expression pair","boy",expressions=("deadpan_blush","panic_sweat"))

    first=route((-.42,.02,0),1,255,(1.02,-1.48,0))
    beside=route((.23,.12,0),1,255,(1.02,-1.48,0))
    pass_route=route((-1.01,-.056,0),423,526,(1.64,-.38,0))
    school_route=route((-.79,.18,0),578,632,(1.12,-.38,0))
    chat_shoko=route((.25,.14,0),663,765,(1.27,-.83,0))
    chat_boy=route((-.34,-.014,0),663,765,(1.27,-.83,0))
    student_root=Vector((1.43,.67,0))
    hallway_gaps=[]
    for f in range(1,END+1):
        if f<256:
            first_act=walk(boy,f,first,.53,1,255,"deadpan_blush",face=(.02,0))
            mode="shy_glance"
            if 87<=f<=106:
                mode=("chat_A","chat_E","chat_O","chat_M")[min(3,(f-87)//5)]
            walk(crush,f,beside,.49,1,255,mode,face=(-.08,-.12-.17*ease(f,66,94)))
            current=(first(f)+beside(f))*.5
            drive_car(car,f,-2.91+.047*f,1.96,-2.91)
            prop_pose(mute,f,(.136,.205,-1.17),ease(f,220,227)*(1-ease(f,251,256)),(-math.pi/2,0,-.08))
            foot=first(f)
            if f<75:
                t=ease(f,1,74)
                cam_view(cam,f,sun,current+Vector((-.17+.37*t,-2.23+.19*t,1.53)),
                         current+Vector((-.02,.02,1.20)),26)
            elif f<124:
                cam_view(cam,f,sun,current+Vector((.85,-1.52,1.53)),
                         current+Vector((.02,.06,1.26)),26)
            elif f<204:
                cam_view(cam,f,sun,foot+Vector((.12-.07*ease(f,124,203),-1.49,1.39)),
                         foot+Vector((-.019,-.19,1.263+first_act.bounce*.62)),51)
            else:
                push=ease(f,203,216)
                target=foot+Vector((-.019-.046*push,-.19,1.263+first_act.bounce*.62))
                cam_view(cam,f,sun,foot+Vector((.05-.20*push,-1.49+.125*push,1.39-.035*push)),target,51)
        elif f<423:
            action=ease(f,262,326)
            jolt=ease(f,365,373)-.23*ease(f,382,398)
            arms=[((i*(.25+.078*jolt),-.15,.22+.32*action+.16*jolt),
                   (i*.25,-.073,.24+.14*jolt)) for i in (-1,1)]
            act(junior,f,(.51,.08,0),-.32,.10-.08*jolt,arms,expression="year7_shock",
                head=(.041+.05*jolt,-.13),bounce=.038*jolt)
            chew=(.5+.5*math.sin((f-372)*.68))*ease(f,352,370)
            prop_pose(puppy,f,(-.42,-.22,.005))
            pup_head.rotation_euler=(.11*chew,0,-.055+.043*chew)
            jaw.scale.z=.35+.86*chew
            tail.rotation_euler.z=.22*math.sin(f*.39)
            prop_pose(year,f,(.065,.295,1.733),ease(f,256,268)*(1-ease(f,364,370)),(0,-.08,0))
            snapped=ease(f,393,401)
            prop_pose(recoil,f,(-.636-.062*snapped,-.465-.017*snapped,.245-.084*snapped),
                      1,(0,.3-.80*snapped,0))
            prop_pose(bite,f,(-.648,-.58,.265),1.0 if 394<=f<=398 else .0001)
            key(pup_head,f,"rotation_euler")
            key(jaw,f,"scale");key(tail,f,"rotation_euler")
            if f<319:
                slide(cam,f,home,256,318,(-.61,-2.21,1.43),(-.37,-2.01,1.36),(.03,.04,.91),(-.02,.09,.91))
            elif f<370:
                slide(cam,f,home,319,369,(.63,-1.82,1.30),(.41,-1.70,1.21),(.03,.08,.96),(-.03,-.03,.88))
            else:
                slide(cam,f,home,370,422,(-.76,-1.68,.85),(-.68,-1.56,.72),(-.44,-.12,.35),(-.45,-.14,.32),31)
        elif f<528:
            root=pass_route(f)
            drive_car(wave_car,f,1.38-.036*(f-423),1.96,1.38)
            walk(passing,f,pass_route,1.29,423,527,"deadpan_blush",face=(0,0))
            greeting=ease(f,426,438)-ease(f,480,501)
            wave_hand=.075*math.sin((f-437)*.38)*greeting
            act(friend,f,(.65,.31,0),-.35,.06,[(REST[0]),((.24+wave_hand,-.12,.19+.48*greeting),(.23,-.087,.29))],
                expression="greet" if 435<f<468 else "smile",head=(.045,-.13))
            q=ease(f,423,527)
            cam_view(cam,f,wave,root+Vector((-1.06+.23*q,-1.35,1.47)),
                     Vector((.43,.16,1.22)).lerp(root+Vector((.47,.09,1.16)),q),26)
        elif f<663:
            hall_wave=ease(f,588,620)
            act(student,f,student_root,-.41,.035,expression="smile",head=(.032,.24*hall_wave))
            act(lockerboy,f,(2.38 if f<633 else -.01,.62,0),.21,.08,
                expression="deadpan_blush",head=(.016,-.05))
            if f<578:
                act(schoolgirl,f,(-.34,.16,0),.10,.057,arms=REST,expression="shy_glance",
                    head=(-.023,.26*ease(f,541,563)))
                prop_pose(books,f,(0,-.192,.222),.0001)
                slide(cam,f,school,528,577,(-.60,-1.34,1.59),(-.49,-1.19,1.54),
                      (-.32,.11,1.25),(-.35,.09,1.25),35)
            elif f<633:
                root=school_route(f)
                hands={i:((sign*.135,-.192,.279),(sign*.195,-.062,.245)) for i,sign in enumerate((-1,1))}
                walk(schoolgirl,f,school_route,1.02,578,632,"shy_glance",face=(.048,.075),override=hands)
                prop_pose(books,f,(0,-.192,.222),1)
                hallway_gaps.append((abs(root.x-student_root.x),f))
                cam_view(cam,f,school,root+Vector((.21,-1.97,1.46)),root+Vector((-.025,.08,1.13)),26)
            else:
                # Keep the adjacent student still and let the camera land on the expression.
                slide(cam,f,school,633,662,(.83,-1.31,1.53),(.70,-1.19,1.44),
                      (.01,.35,1.25),(.02,.47,1.28),32)
        elif f<760:
            root=chat_shoko(f)
            person=chat_boy(f)
            talk=("chat_A","chat_O","chat_E","chat_M","happy_chatter")[(f//4)%5]
            gest=.08*math.sin(f*.27)+.09
            walk(talking,f,chat_shoko,.92,663,765,talk if f>=706 else "shy_glance",
                 face=(-.041,-.20),override={0:((-.25,-.16,.24+gest),(-.225,-.06,.26))})
            walk(listener,f,chat_boy,.92,663,765,"deadpan_blush",face=(0,0))
            pop=ease(f,740,746)
            prop_pose(cloud,f,root+Vector((-.06,.10,1.93+.028*math.sin(f*.19))),pop,
                      (.03,0,.05*math.sin(f*.17)))
            prop_pose(fx,f,root+Vector((.02,-.10,1.64)),1 if 747<=f<=750 else .0001)
            guess=(root+person)*.5
            if f<715:
                cam_view(cam,f,chat,guess+Vector((.18,-2.04,1.46)),guess+Vector((.01,.05,1.17)),26)
            elif f<741:
                cam_view(cam,f,chat,root+Vector((.72,-1.42,1.47)),root+Vector((-.021,-.07,1.30)),26)
            else:
                cam_view(cam,f,chat,root+Vector((.58,-1.74,1.68)),root+Vector((-.09,-.05,1.49)),26)
        else:
            t=ease(f,760,772)
            prop_pose(notebook,f,(0,.0,1.25),1,(-.06,0,.095-.18*t))
            for j,(heart,x,z) in enumerate(hearts):
                duration=ease(f,761+j,771+j)
                prop_pose(heart,f,(x*(.84+.24*duration),-.10,1.25+z+.12*duration),duration)
            slide(cam,f,drawing,760,790,(.055,-1.80,1.54),(.020,-1.67,1.43),
                  (0,0,1.25),(0,0,1.26),36)

    for f,rig,x,expression in ((901,neutral,-.33,"deadpan_blush"),(901,panic,.32,"panic_sweat"),
                                (902,shy,-.36,"shy_glance"),(902,blush,.34,"deep_crimson_blush")):
        arms=REST if rig!=blush else [((-.12,-.235,.49),(-.24,-.14,.26)),((.122,-.237,.49),(.235,-.14,.28))]
        act(rig,f,(x,0,0),-.15 if x<0 else .13,.03,arms,expression=expression,head=(.02,-.06),
            sweat=.36 if rig==panic else None)
    cam_view(cam,901,boy_panel,(.03,-1.89,1.36),(0,0,1.09),30)
    cam_view(cam,902,portrait,(.02,-1.87,1.42),(0,0,1.19),30)
    prop_pose(year,903,(.065,.295,1.733),1,(0,-.04,0))
    cam_view(cam,903,home,(-.68,-2.58,1.26),(-.31,-.04,.86),26)
    cam_view(cam,904,school,(.68,-2.14,1.55),(.08,.30,1.23),26)
    for f,name in zip(CUTS,("Morning walk","Shy whisper","Deadpan headphones and mute icon","Year 7",
        "Boy's shock","Puppy chews","Ignored wave","Shoko introduction","Locker walk","Boy at locker",
        "Courtyard stroll","Chatter burst","Thundercloud","Notebook doodle")):
        s.timeline_markers.new(name,frame=f)
    for group,ranges in ((sun,((1,255),)),(home,((256,422),(903,903))),(wave,((423,527),)),
         (school,((528,662),(904,904))),(chat,((663,759),)),(drawing,((760,790),)),
         (portrait,((902,902),)),(boy_panel,((901,901),))):
        activate(group,ranges)
    for rig in (boy,crush,junior,passing,friend,schoolgirl,lockerboy,student,talking,listener,shy,blush,neutral,panic):
        rig.finish_bake()
    for action in bpy.data.actions:
        for curve in action.fcurves:
            mode="CONSTANT" if "hide_" in curve.data_path or curve.data_path=="lens" else "LINEAR"
            for point in curve.keyframe_points:
                point.interpolation=mode
    s.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"part1_v02.blend"))
    (OUT/"shot_map.json").write_text(json.dumps({"cuts":[f-1 for f in CUTS[1:]],"proof_frames":BENCH},indent=2))
    distance,frame=min(hallway_gaps)
    (OUT/"hallway_clearance.json").write_text(json.dumps({"min_lateral_root_clearance_m":distance,
        "frame":frame,"grips":"Both mittens share the book stack's body-local coordinate system"},indent=2))


if __name__=="__main__":
    main()
