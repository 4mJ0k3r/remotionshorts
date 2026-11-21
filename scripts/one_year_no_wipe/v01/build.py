"""Bake the Stage 1 bathroom, empty roll and classroom beats."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Euler, Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT/"scripts")]
import ricks_v2_kit as k
from cast import CHAIR, REST, SEATED, contact_arm, figure, key, pose
from sets import bathroom, box, classroom, line, text

OUT=ROOT/"renders/one_year_no_wipe/v01"
LENGTH=837


def frame(t):
    return round(t*30)+1


def progress(f,a,b):
    return k.look.ease5((f-frame(a))/max(1,frame(b)-frame(a)))


def switch(c,first,last,x):
    root=k.empty(c.name+" root",c)
    for obj in tuple(c.objects):
        if obj!=root and obj.parent is None:
            obj.parent=root
    for obj in c.objects:
        if obj==root:
            continue
        for prop in ("hide_render","hide_viewport"):
            existing=obj.animation_data.action if obj.animation_data else None
            curve=existing.fcurves.find(prop) if existing else None
            d=obj.driver_add(prop).driver
            d.expression=f"frame < {first} or frame > {last}"
            if curve:
                ch="prior_"+prop
                obj[ch]=bool(getattr(obj,prop))
                curve.data_path=f'["{ch}"]'
                v=d.variables.new()
                v.name="hidden"
                v.type="SINGLE_PROP"
                v.targets[0].id=obj
                v.targets[0].data_path=curve.data_path
                d.expression+=" or hidden > .5"
    root.location.x=x


def palette():
    surfaces={"cream":"#f5ebd8","ink":"#161020","grout":"#4c786e","blue":"#325591","gold":"#eac04b",
              "orange":"#e96e38","metal":"#6e665d","cardboard":"#b88551","plaster":"#d8b98d",
              "mirror":"#80b6be","wood2":"#b78c60"}
    m={name:k.surface(name,color,.77) for name,color in surfaces.items()}
    m["wood"]=k.texture("Layered painted timber",("#624249","#9e6e48","#c89564"),"wood",(.72,.83))
    m["window"]=k.emission("Frosted golden panes","#fff1c6",1.93)
    m["paper"]=k.emission("Ivory calendar paper","#fff2d8",1.05)
    m["red"]=k.emission("Stamp red field","#b7323d",.95)
    m["purple"]=k.emission("Deep aubergine overlay ink","#291c3a",.94)
    return m


def overlay(c,cam,m,label,width,height,font,fill):
    root=k.empty(label+" graphic",c,parent=cam)
    box(c,label+" drop shadow",(.012,-.013,-.014),(width+.020,height+.020,.018),m["purple"],root,bevel=.02)
    box(c,label+" graphic paper",(0,0,0),(width,height,.019),m[fill],root,bevel=.018)
    item=text(c,label,(0,-font*.33,.016),font,m["purple" if fill=="paper" else "paper"],root)
    item.rotation_euler.x=0
    return root


def graphic(root,cam,f,at,stop,*,stamp=False):
    t=progress(f,at,at+(0.12 if stamp else .24))
    on=1-progress(f,stop-.28,stop)
    size=max(.0001,t*on)
    dist=min(2.8,max(.64,cam.data.dof.focus_distance*.94))
    factor=dist/1.62
    root.location=((0 if stamp else -.342)*factor,(.28 if stamp else .923)*factor,-dist)
    root.scale=(size*factor,)*3
    root.rotation_euler=(.17*(1-t),0,-.112 if stamp else .098*(1-t))
    key(root,f,"location","scale","rotation_euler")


CUT_TIMES=(0,2.67,4.66,6.27,7.67,8.39,10.17,13.07,15.85,18.17,20.39,22.60,25.44,26.57)
CUTS=tuple(frame(t) for t in CUT_TIMES)
PROOFS=tuple(frame(t) for t in (0.14,2.93,6.77,7.94,9.18,10.85,13.57,16.68,19.28,23.76,25.76,27.27))
PANELS=tuple(frame(t) for t in (10.85,25.76,.14,13.57))


def camera_action(cam,f,part,start,stop,p,q,a,b,lens=26,focus=None,stop_number=2.8):
    t=progress(f,start,stop)
    eye=Vector(p).lerp(Vector(q),t)+Vector((part,0,0))
    aim=Vector(a).lerp(Vector(b),t)+Vector((part,0,0))
    cam.location=eye
    k.aim(cam,aim)
    cam.data.lens=lens
    cam.data.dof.aperture_fstop=stop_number
    target=(Vector(focus)+Vector((part,0,0))) if focus is not None else aim
    cam.data.dof.focus_distance=(target-eye).dot((aim-eye).normalized())
    key(cam,f,"location","rotation_quaternion")
    key(cam.data,f,"lens","dof.focus_distance","dof.aperture_fstop")


def build(output=OUT, polish=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    k.configure_ricks_scene(s,frame_end=LENGTH,samples=5)
    s.world=bpy.data.worlds.new("Warm slate room bounce")
    s.world.use_nodes=True
    bg=s.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value=k.look.rgba("#789d9f")
    bg.inputs[1].default_value=.35
    cam=bpy.data.objects.new("Vertical storytelling camera",bpy.data.cameras.new("25–28 mm portrait"))
    s.collection.objects.link(cam)
    s.camera=cam
    k.setup_ricks_compositor(s,camera=cam)
    m=palette()
    c=bpy.data.collections.new("01 Mint bathroom")
    school=bpy.data.collections.new("02 Water cycle classroom")
    for col in (c,school):
        s.collection.children.link(col)
    tp=bathroom(c,m)
    classroom(school,m)
    boy=figure(c,"Red Cap at the toilet","boy")
    pupil=figure(school,"Red Cap at his desk","boy")
    friend=figure(school,"Curly-haired classmate","student")
    teacher=figure(school,"Stern teacher","teacher")
    cuts=tuple(frame(8.27) if polish and i==5 else value for i,value in enumerate(CUTS))
    finger=None
    if polish:
        hand=teacher.studio_hands[1]
        finger=k.empty("Teacher pointing index fingertip",school,parent=hand)
        line(school,"Extended index in espresso ink",[(.010,-.002,.008),(.081,-.003,.011)],.013,m["purple"],finger)
        line(school,"Flat cream interior of the pointing finger",[(.016,-.015,.008),(.079,-.015,.011)],.007,m["paper"],finger)
    day1=overlay(c,cam,m,"DAY 1",.39,.182,.116,"paper")
    day2=overlay(school,cam,m,"DAY 2",.39,.182,.116,"paper")
    stamp=overlay(school,cam,m,"PRURITUS ANI",.894,.176,.116,"red")
    wiggles=[]
    for sign in (-1,1):
        ar=k.empty("Three curling comic fidget marks",school,(sign*.31,-.081,.86))
        for z in (-.079,-.008,.063):
            line(school,"Cream jitter accent",[(sign*.024,-.010,z),(sign*.048,-.010,z+.029),
                 (sign*.040,-.010,z+.052)],.007,m["window"],ar)
        wiggles.append(ar)
    cams=[
        (0,2.67,(.67,-2.16,1.52),(.60,-2.02,1.49),(.12,.07,1.07),(.12,.08,1.09),26),
        (2.67,4.66,(-.87,-1.67,1.43),(-.74,-1.55,1.40),(.033,.01,1.03),(.04,.015,1.05),26),
        (4.66,6.27,(.55,-1.39,1.37),(.50,-1.30,1.33),(.014,.052,1.10),(.014,.052,1.10),28),
        (6.27,7.67,(-.26,-1.76,1.42),(-.16,-1.62,1.39),(.22,.04,1.05),(.24,.05,1.04),26),
        (7.67,8.39,(1.104,-.855,1.18),(1.064,-.795,1.163),(.57,.11,.906),(.57,.11,.912),51),
        (8.39,10.17,(.64,-1.67,1.35),(.57,-1.56,1.35),(.13,.043,1.01),(.10,.04,1.03),26),
        (10.17,13.07,(-.38,-1.31,1.40),(-.31,-1.25,1.38),(.034,.07,1.11),(.031,.07,1.11),27),
        (13.07,15.85,(1.44,-2.48,1.75),(1.30,-2.29,1.70),(.21,.34,1.14),(.25,.34,1.19),25),
        (15.85,18.17,(-.78,-1.62,1.39),(-.64,-1.54,1.38),(.19,.03,1.06),(.18,.03,1.08),27),
        (18.17,20.39,(.94,-1.58,1.41),(.88,-1.48,1.43),(.32,.01,1.14),(.33,.04,1.14),26),
        (20.39,22.60,(-.28,-1.73,1.49),(-.19,-1.49,1.47),(.38,.05,1.09),(.36,.03,1.10),26),
        (22.60,25.44,(.77,-1.93,1.55),(.69,-1.81,1.51),(.13,.05,1.07),(.13,.05,1.07),26),
        (25.44,26.57,(.50,-.45,1.56),(.50,-.33,1.55),(-.32,1.42,1.21),(-.34,1.42,1.23),26),
        (26.57,27.9,(.29,.07,1.49),(.29,.07,1.49),(-.43,1.41,1.245),(-.43,1.41,1.245),27),
    ]
    if polish:
        cams[4]=(7.67,8.27,(1.104,-.855,1.18),(1.064,-.795,1.163),(.57,.11,.906),(.57,.11,.912),51)
        cams[5]=(8.27,*cams[5][1:])
    teacher_mouth=((26.62,"W"),(26.74,"O"),(26.84,"E"),(26.94,"M"),(27.06,"I"),
                   (27.16,"L"),(27.24,"A"),(27.36,"W"),(27.42,"M"),(27.46,"A"),
                   (27.58,"O"),(27.7,"S"),(27.78,"M"))
    for f in range(1,LENGTH+1):
        index=max(i for i,cut in enumerate(cuts) if cut<=f)
        camera_action(cam,f,0 if index<7 else 32,*cams[index],stop_number=3.7 if index==4 else 2.8)
        if index<7:
            t=progress(f,0,.65)-progress(f,1.02,1.62)
            reach=progress(f,7.19,7.74)-progress(f,8.62,9.3)
            up=progress(f,10.08,10.61)-progress(f,11.34,11.81)
            turn=progress(f,6.93,7.36)-progress(f,8.51,9.3)
            twist=.31*turn
            tilt=.067*t-.091*up
            rest=Vector(REST[1][0])
            hand=contact_arm((.546,.052,.917),(0,.045,0),twist,tilt,(.294,-.03,.39))
            arm=(rest.lerp(Vector(hand[0]),reach)+Vector((.066*up,-.041*up,.164*up)),hand[1] if reach>.22 else REST[1][1])
            left=(Vector(REST[0][0])+Vector((-.077*up,-.041*up,.166*up)),REST[0][1])
            mode="smirk" if f>=frame(10.3) else "look" if f>=frame(6.3) else "calm"
            foot_lock=SEATED
            if polish:
                inv=Euler((0,0,-twist)).to_matrix()
                foot_lock=tuple((inv@Vector(ankle),knee) for ankle,knee in SEATED)
            pose(boy,f,(0,.045,0),yaw=twist,tilt=tilt,arms=(left,arm),legs=foot_lock,seat=True,mode=mode,
                 head=(.05*t-.076*up,.35*turn-.14*up))
            tp.rotation_euler.x=11.8*progress(f,7.75,8.46)+2.9*progress(f,8.46,8.97)
            key(tp,f,"rotation_euler")
            graphic(day1,cam,f,6.23,7.67 if index<4 else 6.75)
        else:
            pulse=math.sin(f*.31)*(.027+.017*math.sin(f*.037)**2)
            squirm=progress(f,15.14,16.25)*(1-progress(f,25.26,25.73))
            settle=progress(f,25.42,25.83)
            y=.03
            # Feet remain planted while the shoulders and elbows fidget in front of the chair back.
            tilt=.104*pulse*squirm-.05*settle
            root=(pulse*squirm,y,0)
            elbows=tuple(((s*(.21+.014*squirm),-.18+.038*pulse,.137+(s*pulse+.06)*squirm),
                          (s*(.22+.012*squirm),-.052,.257+.024*squirm)) for s in (-1,1))
            legs=tuple(((x-root[0],yy-y,z),(xx-root[0]*.44,yyy,zz)) for (x,yy,z),(xx,yyy,zz) in CHAIR)
            mode="sweat" if settle>=.60 else "wince" if squirm>.58 and math.sin(f*.23)<-.36 else "squirm" if squirm>.25 else "calm"
            pose(pupil,f,root,yaw=-.53*settle,tilt=tilt,arms=elbows,legs=legs,seat=True,mode=mode,
                 head=(.084*squirm*math.sin(f*.23)-.078*settle,-.31*settle),sweat=.28 if settle>=.60 else None)
            look=progress(f,16.22,16.69)
            pose(friend,f,(.86,.18,0),yaw=-.151-.13*look,tilt=.016,legs=CHAIR,seat=True,
                 mode="frown" if f>=frame(19.0) else "side_eye",head=(.055,-.223*look))
            lash=progress(f,25.86,26.67)-.13*progress(f,27.27,27.68)
            right=((.198+.193*lash,-.130-.25*lash,.21+.122*lash),(.207+.081*lash,-.06-.084*lash,.267+.082*lash))
            mode="stern"
            if frame(26.62)<=f<frame(27.90):
                mode=next(code for a,code in reversed(teacher_mouth) if f>=frame(a))
            teacher_x=-.49-.94*(1-progress(f,19.0,22.55)) if polish else -.49
            if polish:
                right=contact_arm((teacher_x+.61*lash,1.43-.61*lash,.70+.36*lash),
                    (teacher_x,1.43,0),.34+.17*lash,.11*lash,(.221,-.143,.31),seat=False)
                right=(Vector(REST[1][0]).lerp(Vector(right[0]),lash),right[1])
            pose(teacher,f,(teacher_x,1.43,0),yaw=.34+.17*lash,tilt=.11*lash,arms=(REST[0],right),mode=mode,head=(.055*lash,.11))
            if finger is not None:
                finger.scale=(max(.0001,lash),)*3
                key(finger,f,"scale")
            for sign,obj in zip((-1,1),wiggles):
                size=max(.0001,squirm*.86*(.65+.35*math.sin(f*.29+sign)**2))
                obj.scale=(size,)*3
                key(obj,f,"scale")
            graphic(day2,cam,f,13.00,15.38)
            graphic(stamp,cam,f,23.55,25.05,stamp=True)
    switch(c,1,CUTS[7]-1,0)
    switch(school,CUTS[7],LENGTH,32)
    for rig in (boy,pupil,friend,teacher):
        rig.finish_bake()
    for action in bpy.data.actions:
        for curve in action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation="CONSTANT" if "hide_" in curve.data_path or curve.data_path=="lens" else "LINEAR"
    for f,tag in zip(cuts,("Hook","Toilet reverse","Question","DAY 1","Cardboard core","Empty roll payoff",
                     "Shrug","DAY 2","Restless","Classmate side-eye","Fidget build","Stamp","Teacher OTS","Teacher scold")):
        s.timeline_markers.new(tag,frame=f)
    s.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(output/("part1_v02.blend" if polish else "part1_v01.blend")))
    (output/"shots.json").write_text(json.dumps({
        "cuts":[f-1 for f in cuts[1:]],"proof_frames":PROOFS,"panels":PANELS,
        "shots":[{"id":i,"a":a-1,"b":b-1} for i,(a,b) in enumerate(zip(cuts,(*cuts[1:],LENGTH+1)),1)],
    },indent=2))


if __name__=="__main__":
    build()
