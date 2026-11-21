"""Fire drill, bus confession, Friday crossing, and the hard cut to black."""
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]

import bpy
from mathutils import Vector
from feature_scene import (LEGS, REST, act, clock, ease, fade_to_black, figure, finish,
                           block, glide, k, key, line, make_scene, move_hands, prop_pose, route,
                           show_title, stage, street, sunrise, title, view, walk)
from sets import bus, crosswalk, fire_bell, school

F = clock(3)


def cards(prefix):
    return {path.stem:path for path in HERE.glob(prefix+"_*.png")}


def speech(f, default, prefix, timings, end):
    if f<F(timings[0][0]) or f>=F(end):
        return default
    return prefix+"_"+next(shape for start,shape in reversed(timings) if f>=F(start))


SLEEP = ((62.76,"E"),(62.93,"I"),(63.09,"M"),(63.42,"I"),(63.63,"M"),(63.77,"E"),
         (63.98,"A"),(64.10,"O"),(64.37,"L"),(64.53,"U"),(64.73,"I"),(64.84,"A"),
         (65.14,"U"),(65.36,"S"),(65.50,"M"),(65.68,"A"),(65.82,"O"),(66.09,"E"))
LOVE = ((71.56,"I"),(71.68,"E"),(71.80,"L"),(71.93,"F"),(72.02,"U"),(72.20,"U"),(72.43,"M"))
SHOUT = ((82.40,"W"),(82.56,"I"),(82.72,"L"),(82.81,"O"),(82.94,"U"),(83.18,"E"))


def attach_headphones(c, rig):
    headset = k.empty("Headphones lifted as one continuous prop",c,parent=rig.head)
    for obj in tuple(rig.head.children):
        if obj.name.startswith(("Round matte headphone earcup","Arched matte headphone","Soft graphite band")):
            obj.parent = headset
    return headset


def bake_crowd(collection, rig):
    """Same classmate rig and costume in a fixed background pose."""
    bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get()
    original=tuple(rig.root.children_recursive)
    saved=[]
    for obj in original:
        if obj.type not in {"MESH","CURVE"} or obj.hide_render:
            continue
        evaluated=obj.evaluated_get(graph)
        mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=graph)
        saved.append((obj.name,mesh,evaluated.matrix_world.copy(),obj.visible_shadow))
    for obj in reversed(original):
        bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.objects.remove(rig.root,do_unlink=True)
    for name,mesh,matrix,shadow in saved:
        obj=k.put(bpy.data.objects.new(name,mesh),collection)
        obj.matrix_world=matrix
        obj.visible_shadow=shadow
        if len(mesh.polygons)>28:
            decimate=obj.modifiers.new("Background cast silhouette budget","DECIMATE")
            decimate.ratio=.13


def sleeve_cuff(collection,rig):
    root=k.empty("Thin grey knitted cuff at Shoko's wrist",collection,parent=rig.body)
    base=k.make_cel_character_material("Grey wool cardigan cuff","#8f849f")
    pale=k.emission("Grey rib-stitch highlights","#c5bcca",.78)
    block(collection,"Close-up grey cuff cloth",(-.052,-.013,0),(.106,.022,.058),base,root)
    for index in range(8):
        x=-.097+index*.012
        line(collection,"Raised knit cuff seam",[(x,-.026,-.024),(x,-.026,.024)],.0018,pale,root)
    return root


def headset_pose(rig, headset, f):
    lift=ease(f,F(70.11),F(70.52))
    lower=ease(f,F(70.52),F(71.37))
    clear=ease(f,F(70.30),F(70.60))
    prop_pose(headset,f,(.21*lower,-.185*clear-.089*lower,.32*lift-.82*lower),
              rotation=(.20*clear+.27*lower,-.31*lower,.20*lower))
    wrist_pose = rig.root.matrix_basis @ rig.body.matrix_basis @ rig.head.matrix_basis @ headset.matrix_basis
    reach = ease(f,F(69.76),F(70.13))
    let_go = ease(f,F(70.92),F(71.29))
    for i,side in enumerate((-1,1)):
        if i==0 or let_go<1:
            rest=Vector(REST[i][0])
            grip = wrist_pose @ Vector((side*.307,-.008,-.030))
            local = (rig.root.matrix_basis @ rig.body.matrix_basis) @ rest
            weight=reach*(1-let_go if i==1 else 1)
            goals=[None,None]
            goals[i]=local.lerp(grip,weight)
            elbows=((- .269,-.129,.428),(.269,-.129,.428))
            move_hands(rig,f,goals,elbows)


def main():
    s,cam,m,length=make_scene(3,"Shoko Part 3")
    yard=stage(s,"Fire drill schoolyard",0)
    yard_extras=stage(s,"Fire drill classmates",0)
    coach=stage(s,"Thursday amber bus interior",32)
    fri=stage(s,"Friday sunrise school crossing",64)
    fri_extras=stage(s,"Classmates at the crossing",64)
    y,b,c=[g[0] for g in (yard,coach,fri)]
    school(y,m,yard=True)
    bell=fire_bell(y,m,-2.16,2.99,1.75)
    yboy=figure(y,"Boy in the fire drill line","boy",compact=True,expressions=("deadpan_blush","warm_smile"))
    ygirl=figure(y,"Shoko gently taking his hand","shoko",compact=True,expressions=("shy_glance","whisper_M"))
    cuff=sleeve_cuff(y,ygirl)
    for j,(x,d) in enumerate(((-2.36,.89),(-1.60,1.08),(-.89,1.22),(.71,1.31),(1.51,1.34),(2.37,1.28))):
        pupil=figure(yard_extras[0],f"Fire drill classmate {j+1}","classmate",background=True,expressions=("smile",))
        act(pupil,1,(x,d,0),-.24+.15*(j%4),expression="smile",head=(0,.13*(-1)**j))
        bake_crowd(yard_extras[0],pupil)
    bus_backdrop=bus(b,m)
    bboy=figure(b,"Boy stiff on the bus bench","boy",compact=True,expressions=("deadpan_blush","year7_shock","warm_smile"))
    bgirl=figure(b,"Shoko asleep against his shoulder","shoko",compact=True,
                 expressions=("shy_glance","peaceful_sleep"),extra_expressions=cards("sleep"))
    thu=title(b,m,cam,"THURSDAY")
    passing=street(c,m)
    passing[0].hide_render=passing[0].hide_viewport=True
    for obj in passing[0].children_recursive:
        obj.hide_render=obj.hide_viewport=True
    school(c,m,offset=-1.93,depth=3.02)
    crosswalk(c,m)
    sunrise(c)
    cboy=figure(c,"Boy in the Friday sunrise","boy",compact=True,
                expressions=("deadpan_blush","warm_smile","joyful_grin"),extra_expressions=cards("tender"))
    headphones=attach_headphones(c,cboy)
    cgirl=figure(c,"Shoko at the sunrise crossing","shoko",compact=True,
                 expressions=("shy_glance","whisper_A","whisper_E","whisper_O","whisper_M","stunned_freeze",
                              "deep_crimson_blush","radiant_joy","happy_chatter"),
                 extra_expressions=cards("radiant")|cards("blush"))
    for j,(x,d) in enumerate(((-1.23,2.62),(.80,2.63),(1.62,2.70))):
        pupil=figure(fri_extras[0],f"Classmate watching from the far curb {j+1}","classmate",background=True,expressions=("smile",))
        act(pupil,1,(x,d,0),-.1+.14*j,expression="smile",head=(0,-.19))
        bake_crowd(fri_extras[0],pupil)
    friday=title(c,m,cam,"FRIDAY")

    alarm, lineup, holding, nod, thursday, bus_wide, shoulder, bus_close, daylight, lift, reply, freeze, blush, sleeves, skip, spin, proclaim, grin, payoff, crash = map(
        F,(57.20,57.80,58.62,59.47,59.97,60.73,61.47,62.72,66.50,69.60,71.40,72.93,
           74.10,75.39,78.23,80.17,82.35,84.10,85.48,86.167))
    cuts=((1,"Fire drill begins"),(alarm,"Ringing red bell"),(lineup,"Schoolyard lineup"),
          (holding,"Knitted cuff and handhold"),(nod,"The nod"),(thursday,"Thursday"),
          (bus_wide,"Bus aisle and school windows"),(shoulder,"Shoulder rest"),(bus_close,"Quiet promise"),
          (daylight,"Friday sunrise"),(lift,"Both hands on the earcups"),(reply,"I love you too"),
          (freeze,"Shoko freezes"),(blush,"Crimson blush"),(sleeves,"Hide and laugh"),
          (skip,"Dash to the crossing"),(spin,"Open-armed turn"),(proclaim,"I LOVE YOU"),
          (grin,"Boy grins"),(payoff,"Shoko in the crossing"),(crash,"Hard cut to black"))
    yr=(-.331,.01,0)
    yg=(.333,.015,0)
    walk_b=route((-1.43,.61,0),daylight,lift, (.65,.03,0))
    walk_s=route((-1.44,-.056,0),daylight,lift,(.65,.03,0))
    boy_base=walk_b(lift)
    girl_base=walk_s(lift)
    cross_out=route(tuple(girl_base),skip,spin, (.52,1.90,0))
    crossing=cross_out(spin)
    seated=tuple(((side*.124,-.418,.027),(side*.115,-.348,.369)) for side in (-1,1))
    for f in range(1,length+1):
        if f<thursday:
            vibration=.028*math.sin(f*2.76) if alarm<=f<lineup else 0
            bell.rotation_euler.y=vibration
            key(bell,f,"rotation_euler")
            contact=ease(f,F(58.52),F(59.1))
            lift_hand=(.004,-.183,.737+.026*contact)
            act(yboy,f,yr,.047,0,expression="warm_smile" if f>=nod else "deadpan_blush",
                head=(.105*(ease(f,nod,nod+5)-ease(f,nod+5,nod+12)),.13*contact))
            act(ygirl,f,yg,-.14,.025,expression="whisper_M" if f>=holding else "shy_glance",head=(.047,-.14*contact))
            if f>=F(58.52):
                goal=Vector((.115,-.15,.696)).lerp(Vector(lift_hand),contact)
                move_hands(yboy,f,(None,(-.028,-.191,lift_hand[2]-.006)),((0,0,0),(.182,-.052,.298)))
                move_hands(ygirl,f,(goal,None),((-.169,-.047,.333),(0,0,0)))
            hand=ygirl.studio_hands[0]
            prop_pose(cuff,f,tuple(hand.location),1. if holding<=f<nod else .0001,
                      (0,hand.rotation_euler.y,0))
            if f<alarm:
                view(cam,f,yard,(.11,-2.11,1.55),(0,.13,1.15),26)
            elif f<lineup:
                glide(cam,f,yard,alarm,lineup-1,(-2.03,1.04,1.82),(-2.09,1.14,1.81),
                      (-2.16,2.97,1.67),(-2.16,2.97,1.67),47,stop=4.2)
            elif f<holding:
                glide(cam,f,yard,lineup,holding-1,(2.12,-3.57,1.87),(1.37,-3.22,1.83),
                      (0,.81,1.22),(0,.72,1.21),25)
            elif f<nod:
                glide(cam,f,yard,holding,nod-1,(.053,-1.31,.76),(.136,-1.21,.78),
                      (.005,-.14,.766),(.005,-.175,.77),47,stop=5.0)
            else:
                glide(cam,f,yard,nod,thursday-1,(.35,-1.67,1.43),(.29,-1.53,1.42),
                      (0,.0,1.23),(0,.0,1.24),27)
        elif f<daylight:
            drift=.025*(f-thursday)
            prop_pose(bus_backdrop,f,(0,-drift,0))
            settle=ease(f,shoulder,F(62.29))
            boyloc=(-.325,.09,0)
            girlloc=(.276-.076*settle,-.008-.114*settle,-.094*settle)
            say=speech(f,"peaceful_sleep" if f>=F(61.96) else "shy_glance","sleep",SLEEP,66.36)
            act(bboy,f,boyloc,.035,.06,((( -.158,-.236,.052),(-.177,-.049,.224)),
                ((.156,-.228,.045),(.183,-.026,.213))),seated,
                expression="year7_shock" if F(61.72)<=f<F(63.60) else "warm_smile" if f>=F(64.88) else "deadpan_blush",
                head=(.012,-.114*settle))
            girllegs=tuple(((x,yy,z+.082*settle),(xx,yyy,zz+.053*settle)) for (x,yy,z),(xx,yyy,zz) in seated)
            act(bgirl,f,girlloc,-.037,.092,((( -.133,-.198,.081),(-.154,-.034,.220)),
                ((.133,-.198,.073),(.156,-.042,.220))),girllegs,say,head=(.045*settle,.084*settle),sway=-.315*settle)
            if f<bus_wide:
                show_title(thu,f,thursday,bus_wide+7)
                glide(cam,f,coach,thursday,bus_wide-1,(-.66,-1.81,1.60),(-.56,-1.77,1.53),
                      (-.04,.32,1.32),(-.04,.29,1.28),26)
            elif f<shoulder:
                show_title(thu,f,thursday,bus_wide+7)
                glide(cam,f,coach,bus_wide,shoulder-1,(-1.03,-1.91,1.70),(-.83,-1.68,1.59),
                      (.03,.22,1.17),(.02,.18,1.19),25)
            elif f<bus_close:
                glide(cam,f,coach,shoulder,bus_close-1,(-.84,-1.67,1.48),(-.62,-1.52,1.37),
                      (-.019,.13,1.20),(-.05,.08,1.16),27)
            else:
                glide(cam,f,coach,bus_close,daylight-1,(.20,-1.51,1.42),(.16,-1.40,1.38),
                      (-.087,.001,1.18),(-.10,-.01,1.15),28)
        else:
            show_title(friday,f,daylight,F(67.53))
            if f<lift:
                shoko=speech(f,"shy_glance","whisper",((68.40,"A"),(68.56,"E"),(68.68,"O"),(68.90,"M")),69.20)
                walk(cboy,f,walk_b,math.pi/2,daylight,lift,"deadpan_blush")
                walk(cgirl,f,walk_s,math.pi/2,daylight,lift,shoko,phase=6,face=(0,.20*ease(f,F(67.68),F(68.42))))
            else:
                warmth=ease(f,F(70.76),reply+10)
                head_turn=-.38*warmth
                boy_mode=speech(f,"joyful_grin" if f>=proclaim else "warm_smile","tender",LOVE,72.48)
                turn_road=ease(f,skip,skip+8)*(1-ease(f,grin-10,grin))
                act(cboy,f,boy_base,.86-.27*warmth+2.34*turn_road,-.018,
                    expression=boy_mode,head=(-.045,head_turn))
                headset_pose(cboy,headphones,f)
                if f<freeze:
                    act(cgirl,f,girl_base,1.19,0,expression="shy_glance",head=(0,.30))
                elif f<skip:
                    hidden=ease(f,sleeves,F(76.28))-ease(f,F(76.88),F(77.59))
                    shy="stunned_freeze" if f<F(74.69) else "blush_crimson" if f<F(77.16) else "radiant_joy"
                    hands=tuple(((side*(.211-.09*hidden),-.15-.072*hidden,.17+.445*hidden),
                                 (side*(.223+.03*hidden),-.065-.076*hidden,.26+.161*hidden)) for side in (-1,1))
                    laugh=(.017*math.sin(f*.61) if F(77.19)<=f<skip else 0)
                    act(cgirl,f,girl_base,.39,.11*hidden,hands,expression=shy,head=(.081*hidden,.11),bounce=laugh)
                elif f<spin:
                    walk(cgirl,f,cross_out,0,skip,spin,"radiant_joy",face=(-.036,.14))
                else:
                    turn=ease(f,spin,F(81.08))
                    pose=ease(f,spin,F(81.28))
                    yaw=math.pi-.267+(math.pi+.267)*turn
                    arms=tuple(((side*(.22+.23*pose),-.13+.087*pose,.18+.25*pose),
                               (side*(.22+.12*pose),-.061,.26+.142*pose)) for side in (-1,1))
                    joyful=speech(f,"radiant_joy","radiant",SHOUT,83.42)
                    root=tuple(crossing)
                    act(cgirl,f,root,yaw,-.059,arms,expression=joyful,head=(-.071,0),bounce=.039*math.sin(math.pi*turn))
            if f<lift:
                t=ease(f,daylight,lift-1)
                x=walk_b(f).x
                view(cam,f,fri,(x+1.76-.12*t,-.125+.10*t,1.53),(x-.025,.269,1.42),26)
            elif f<reply:
                glide(cam,f,fri,lift,reply-1,(.79,-.63,1.49),(.67,-.59,1.50),(-.78,.63,1.40),(-.78,.63,1.47),29)
            elif f<freeze:
                glide(cam,f,fri,reply,freeze-1,(-.02,-.73,1.47),(-.15,-.64,1.46),(-.79,.58,1.25),(-.79,.58,1.28),31)
            elif f<blush:
                glide(cam,f,fri,freeze,blush-1,(.03,-1.25,1.48),(-.10,-1.11,1.43),(-.79,-.033,1.22),(-.79,-.033,1.23),31)
            elif f<sleeves:
                glide(cam,f,fri,blush,sleeves-1,(-.34,-1.11,1.40),(-.46,-.99,1.38),(-.79,-.04,1.20),(-.79,-.05,1.22),33)
            elif f<skip:
                glide(cam,f,fri,sleeves,skip-1,(.05,-1.40,1.45),(-.24,-1.41,1.44),(-.70,.12,1.23),(-.70,.18,1.22),28)
            elif f<spin:
                glide(cam,f,fri,skip,spin-1,(1.19,-2.17,1.96),(.79,-1.78,1.84),(-.42,1.05,1.15),(-.38,1.32,1.15),26)
            elif f<proclaim:
                glide(cam,f,fri,spin,proclaim-1,(.24,-.86,1.57),(.12,-.42,1.54),(-.29,1.51,1.04),(-.27,1.55,1.11),26)
            elif f<grin:
                glide(cam,f,fri,proclaim,grin-1,(.24,-.11,1.47),(.17,.02,1.45),(-.27,1.85,1.28),(-.27,1.85,1.32),27)
            elif f<payoff:
                glide(cam,f,fri,grin,payoff-1,(.24,-.94,1.50),(.08,-.82,1.49),(-.78,.59,1.24),(-.78,.59,1.27),28)
            else:
                view(cam,f,fri,(.36,-.94,1.79),(-.34,1.64,1.12),25,focus=crossing+Vector((0,0,1.19)))
    fade_to_black(s,((1,0),(crash-1,0),(crash,1),(length,1)),hard=True)
    proofs=list(map(F,(57.40,58.10,59.10,60.84,62.21,64.42,67.64,70.49,72.21,75.17,79.31,82.79)))
    finish(s,3,(yboy,ygirl,bboy,bgirl,cboy,cgirl),
           ((yard,((1,thursday-1),)),(yard_extras,((1,alarm-1),(lineup,holding-1))),
            (coach,((thursday,daylight-1),)),(fri,((daylight,length),)),(fri_extras,((skip,length),))),
           cuts,proofs,((crash-1,length-1),))


if __name__=="__main__":
    main()
