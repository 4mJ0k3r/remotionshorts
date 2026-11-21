"""Part 2 acting and props, using the approved v03 cast and locations."""
import json
import math
from pathlib import Path
from random import Random
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import BENCH, BONK, CUTS, HERE, LENGTH, OUT, PHONE, PHONE_END, SHARED, TAP, frame

sys.path.insert(0,str(SHARED))
import bpy
from mathutils import Euler, Vector
from build import (activate, act, block, cam_view, drive_car, ease, figure, hallway, key, k,
                   lettering, line, palette, prop_pose, route, slide, sparks, stage, street, walk)
from cast import LEGS, LOWER, REST


def header(c,m,cam,text):
    badge=k.empty(text+" day graphic",c,parent=cam)
    back=lettering(c,text,(0,.015,0),.135,m["ink"],badge)
    back.data.offset=.009
    back.data.extrude=.002
    lettering(c,text,(0,-.007,0),.135,m["gold"],badge)
    return badge


def show_day(badge,f,start,stop):
    pop=ease(f,start,start+8)*(1-ease(f,stop-8,stop))
    prop_pose(badge,f,(0,.698,-1.58),pop,(-math.pi/2,0,.045))


def music_note(c,material,parent):
    k.ball("Music note head",c,(0,0,0),(.035,.016,.028),material,parent,segments=13,rings=7)
    line(c,"Music note stem and flag",[(.028,0,0),(.028,0,.122),(.058,0,.097),(.082,0,.086)],.009,
         material,parent)


def phone(c,m,parent=None,scale=1.0):
    root=k.empty("Shoko's glowing phone",c,parent=parent)
    block(c,"Rounded plum phone body",(0,.003,0),(.50,.058,.79),m["ink"],root)
    frosted=k.emission("Brilliant indigo phone screen","#1d294f",1.2)
    block(c,"Lit phone screen",(0,-.032,0),(.446,.007,.717),frosted,root)
    block(c,"Small camera bezel",(0,-.039,.355),(.11,.009,.021),m["dark"],root)
    lavender=k.emission("Lilac phone graphics","#cbafe9",1.22)
    for phrase,z,size in (("DHINCHAK",.165,.060),("POOJA",.058,.074),("— 40 SONGS",-.062,.053)):
        lettering(c,phrase,(0,-.041,z),size,m["white"],root)
    for j in range(5):
        x=(j-2)*.045
        line(c,"Sound meter below playlist name",[(x,-.041,-.259),(x,-.041,-.198+.021*math.sin(j*1.7))],.007,
             lavender,root)
    for x,z in ((-.143,.269),(.131,-.135)):
        note=k.empty("Small music note on screen poster",c,(x,-.043,z),root)
        note.scale=(.43,)*3
        music_note(c,lavender,note)
    root.scale=(scale,)*3
    return root


def bedroom(c,m):
    wall=k.texture("Deep blue painted bedroom","#20223f #34365c #5b5575".split(),"plaster",(.76,.89))
    quilt=k.texture("Heather violet knit blanket","#574762 #8d799f #a294bb".split(),"plaster",(.82,.91))
    block(c,"Indigo bedroom wall",(0,1.43,1.37),(7,.16,2.75),wall)
    block(c,"Dark blue timber floor",(0,0,-.087),(8,7,.175),m["wood"])
    block(c,"Painted wooden bed frame",(.16,.42,.239),(1.53,1.99,.44),m["dark"])
    block(c,"Firm overnight mattress",(.16,.39,.464),(1.49,1.93,.18),m["cream"])
    block(c,"Indigo spindle headboard",(.16,1.06,.79),(1.55,.14,.88),m["blue"])
    for j in range(10):
        x=-.49+j*.147
        line(c,"Bed headboard wood grooves",[(x,.968,.57),(x,.968,1.20)],.008,m["dark"])
    pillow=k.ball("Soft cream bed pillow",c,(.13,.49,.935),(.49,.22,.263),m["cream"],segments=22,rings=13)
    pillow.rotation_euler.x=-.24
    points=[]
    faces=[]
    for row in range(10):
        for col in range(14):
            x=-.58+col*.112
            y=-.58+row*.118
            z=.574+.086*math.sin(row*.26)+.036*math.sin(col*.73)+.08*math.exp(-((row-7)/1.35)**2)*(1-abs(x-.16)*.62)
            points.append((x,y,z))
            i=len(points)-1
            if row and col:
                faces.append((i-15,i-14,i,i-1))
    blanket=k.mesh("Draped knitted blanket",c,points,faces,quilt,smoothing=True)
    blanket.modifiers.new("Fabric hem thickness","SOLIDIFY").thickness=.026
    for j in range(11):
        x=-.53+j*.136
        coords=[(x,-.57+q*.09,.593+.082*math.sin(q*.19)+.026*math.sin(j*.85)) for q in range(13)]
        line(c,"Braided knit blanket rib",coords,.007,m["blue"] if j%3 else m["cream"])
    block(c,"Right bedside cabinet", (1.15,.63,.267),(.42,.44,.52),m["wood"])
    for z in (.21,.393):
        block(c,"Bedside drawer pull",(1.15,.391,z),(.15,.021,.029),m["cream"])
    frame_mat=k.emission("Night sky through curtains","#23325e",1.1)
    block(c,"Blue bedroom window",(-.89,1.327,1.73),(1.17,.045,.86),frame_mat)
    for x in (-1.44,-.91,-.35):
        line(c,"Moonlit white window frame",[(x,1.293,1.31),(x,1.293,2.14)],.022,m["cream"])
    for z in (1.34,1.73,2.12):
        line(c,"Moonlit window frame cross bar",[(-1.44,1.292,z),(-.35,1.292,z)],.021,m["cream"])
    paper=k.emission("Moon in Shoko's window","#a8cbfa",1.2)
    orb=k.cylinder("Tiny moon outside window",c,(-1.10,1.306,1.93),.138,.010,paper,length_segments=23)
    orb.rotation_euler.x=math.pi/2
    k.make_ricks_light("Cold moonlight from window",c,(-.99,.71,2.37),(-.01,.19,1.13),"#889de7",127,1.14)
    k.make_ricks_light("Phone light on Shoko's determined expression",c,(.035,-.51,.73),(.11,.16,1.22),"#c1c5ff",71,.56)


def target_arm(world,root,yaw,tilt,elbow):
    facing=Euler((0,0,yaw)).to_matrix()
    body=Euler((tilt,0,0)).to_matrix()
    result=(facing@body).transposed()@(Vector(world)-Vector(root)-Vector((0,0,.59-LOWER)))
    return result-(result-Vector(elbow)).normalized()*.016


def rain(c):
    root=k.empty("Diagonal rain field",c)
    mat=k.emission("Pale rain streaks", "#b3cae1",1.17)
    rng=Random(1506)
    for _ in range(169):
        x,y,z=rng.uniform(-3.6,3.8),rng.uniform(-1.5,3.1),rng.uniform(-.18,3.62)
        height=rng.uniform(.10,.31)
        drop=line(c,"Slanted rain glint",[(x,y,z),(x-.33*height,y,z+height)],rng.uniform(.0019,.0038),mat,root)
        drop.visible_shadow=False
    return root


def main(output=OUT, *, polish=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    k.configure_ricks_scene(s,frame_end=LENGTH,samples=5)
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.compression=0
    s.world=bpy.data.worlds.new("School blue-grey bounce")
    s.world.use_nodes=True
    bg=next(n for n in s.world.node_tree.nodes if n.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#385275")
    bg.inputs[1].default_value=.40
    cam=bpy.data.objects.new("Part 2 story camera",bpy.data.cameras.new("Portrait 26 mm"))
    s.collection.objects.link(cam)
    s.camera=cam
    k.setup_ricks_compositor(s,camera=cam)
    m=palette()
    mon=stage(s,"Monday approved block and curb lamppost",0)
    tue=stage(s,"Tuesday rainy approved brick street",32)
    hall=stage(s,"Tuesday headphone tap at the lockers",48)
    night=stage(s,"Wednesday moonlit blanket and playlist",64)
    insert=stage(s,"Wednesday phone screen insert",80)
    c,r,h,b,p=[item[0] for item in (mon,tue,hall,night,insert)]
    car=street(c,m)
    shout_art={"shout_wide":output/"shout_wide.png"} if polish else None
    mon_boy=figure(c,"Boy on Monday","boy",compact=True,expressions=("deadpan_blush","year7_shock","shout_what"),
                   extra_expressions=shout_art)
    mon_shoko=figure(c,"Shoko on Monday","shoko",compact=True,
                    expressions=("shy_glance","whisper_A","whisper_E","whisper_O","whisper_M",
                                 "worried_brows","chat_A","chat_O"))
    day_mon=header(c,m,cam,"MONDAY")
    stars=sparks(c,m,"Golden BONK stars")
    for j in range(3):
        offset=.11*j-.16
        points=[(offset+(.057 if i%2==0 else .026)*math.cos(i*math.pi/5),-.014,
                 .035+.076*j+(.057 if i%2==0 else .026)*math.sin(i*math.pi/5)) for i in range(10)]
        k.mesh("Tiny comic star",c,points,[tuple(range(10))],m["gold"],stars)
    wet=palette()
    rain_car=street(r,wet)
    for obj in r.objects:
        if obj.type=="LIGHT":
            obj.data.color=k.look.rgba("#c8d7f4")[:3]
            obj.data.energy*=.62
            obj.data.use_shadow=False
    rain_sky=bpy.data.materials.get("Continuous morning dome.001")
    if rain_sky:
        ramp=next(node.color_ramp for node in rain_sky.node_tree.nodes if node.type=="VALTORGB")
        for swatch,color in zip(ramp.elements,("#a6aebd","#9aaccb","#6781ac","#526b96")):
            swatch.color=k.look.rgba(color)
    rain_group=rain(r)
    rain_boy=figure(r,"Boy on the rainy sidewalk","boy",compact=True,expressions=("deadpan_blush",))
    rain_shoko=figure(r,"Shoko on the rainy sidewalk","shoko",compact=True,expressions=("shy_glance",))
    day_tue=header(r,m,cam,"TUESDAY")
    hallway(h,m)
    hall_boy=figure(h,"Boy at Tuesday lockers","boy",compact=True,expressions=("deadpan_blush","year7_shock","shout_what","panic_sweat"),
                    extra_expressions={"panic_wobble":HERE/"panic_wobble.png"})
    hall_shoko=figure(h,"Shoko reaching toward headphones","shoko",compact=True,
                     expressions=("shy_glance","chat_A","chat_O","chat_E","chat_M"))
    tap_fx=sparks(h,m,"Small two-frame tap rays")
    bedroom(b,m)
    night_shoko=figure(b,"Shoko studying forty songs in bed","shoko",compact=True,
                      expressions=("worried_brows","chat_A","chat_E","chat_M","shy_glance"))
    small_phone=phone(b,m,scale=.34)
    day_wed=header(b,m,cam,"WEDNESDAY")
    floating=[]
    for j,tone in enumerate(("#d7a6eb","#7ed4f4","#f2ceb0","#b695f0")):
        root=k.empty("Floating Wednesday music note",b)
        music_note(b,k.emission("Pleasant pastel music glyph",tone,1.35),root)
        floating.append(root)
    bedroom(p,m)
    macro_phone=phone(p,m)
    if polish:
        for z in (-.282,-.311):
            line(p,"Fine playlist transport divider",[(-.185,-.043,z),(.185,-.043,z)],.003,m["white"],macro_phone)
        for j in range(7):
            x=(j-3)*.053
            line(p,"Playlist timeline tick",[(x,-.044,-.311),(x,-.044,-.292)],.0035,m["white"],macro_phone)
        for j in range(3):
            z=.309-j*.030
            line(p,"Playlist hamburger menu glyph",[(.113,-.041,z),(.169,-.041,z)],.0035,m["white"],macro_phone)
    light=k.make_ricks_light("Soft phone casing edge light",p,(-.41,-1.4,1.49),(0,0,1.1),"#b8caff",95,.76)
    light.data.use_shadow=False
    one,eye,impact,reverse,shout,stone,tuesday,locker,panic,wednesday,*_=CUTS
    if polish:
        lamp_parts=("Cast iron curb lamp plinth","Straight cast iron lamp standard","Turned pole collar",
                    "Curved lamp bracket","Lantern top housing","Frosted lantern glass")
        for lamp in c.objects:
            x=lamp.data.splines[0].bezier_points[0].co.x if lamp.name.startswith("Curved lamp bracket") else lamp.location.x
            if lamp.name.startswith(lamp_parts) and abs(x-2.76)<.19:
                original=lamp.location.copy()
                # Clear the reverse-camera ray paths only after the bonk.
                for at,shift in ((1,0),(reverse-1,0),(reverse,-.48),(shout-1,-.48),(shout,0)):
                    lamp.location=original+Vector((0,shift,0))
                    key(lamp,at,"location")
    approach=route((-.43,1.28,0),1,BONK,(2.866,0,0))
    companion=route((-.46,.665,0),1,BONK,(2.866,0,0))
    rainy_b=route((-.24,-.09,0),tuesday,locker-1,(.33,-.19,0))
    rainy_s=route((.42,.102,0),tuesday,locker-1,(.33,-.19,0))
    for f in range(1,LENGTH+1):
        if f<tuesday:
            drive_car(car,f,-4.21+.042*f,2.02,-4.21)
            show_day(day_mon,f,1,frame(27.74))
            pron=frame(29.44)
            whisper=frame(29.44)<=f<frame(30.32)
            mouth=("whisper_A" if f<frame(29.62) else "whisper_E" if f<frame(29.86)
                   else "whisper_O" if f<frame(30.17) else "whisper_M")
            lean=ease(f,pron-14,pron+4)-ease(f,pron+20,pron+34)
            if f<BONK:
                bend=.043 if f<impact else .03*(1-ease(f,impact,BONK))
                walk(mon_boy,f,approach,math.pi/2,1,BONK,"deadpan_blush",face=(bend,0))
                walk(mon_shoko,f,companion,math.pi/2,1,BONK,mouth if whisper else "shy_glance",
                     face=(-.025-.09*lean,.29*lean),sway=.145*lean,phase=6)
                if f>=eye:
                    mon_boy.sweat.hide_viewport=mon_boy.sweat.hide_render=False
                    progress=ease(f,eye+5,impact-1)
                    mon_boy.sweat.location=(-.138-.021*progress,-.137,.086-.052*progress)
                    key(mon_boy.sweat,f,"location","hide_viewport","hide_render")
            else:
                recoil=ease(f,BONK,BONK+4)
                relax=ease(f,BONK+4,BONK+10)
                duck=ease(f,frame(35.55),frame(36.56))-ease(f,frame(37.12),frame(37.51))
                ear=ease(f,frame(37.50),frame(38.8))-ease(f,frame(40.34),frame(40.58))
                q=frame(39.84)<=f<=frame(40.33)
                expression=("shout_wide" if polish else "shout_what") if q else (
                    "year7_shock" if f<=BONK+10 else "deadpan_blush")
                boy_root=(2.436-.204*recoil+.045*relax,1.28,.017*recoil*(1-relax))
                left=((-.22,-.12,.18+.17*recoil*(1-relax)),(-.22,-.068,.25))
                right=((.214+.057*ear,-.156+.111*ear,.18+.411*ear),(.228+.071*ear,-.023,.254+.115*ear))
                act(mon_boy,f,boy_root,math.pi/2-.47*ease(f,BONK+5,BONK+25),
                    -.19*recoil+.157*relax-.089*ear,[left,right],expression=expression,
                    head=(.09*recoil-.04*relax-.10*ear,-.106*duck),sweat=.74 if f<BONK+14 else None)
                worried="chat_O" if frame(36.54)<=f<=frame(37.02) else "worried_brows"
                act(mon_shoko,f,(2.215-.071*duck,.635+.056*duck,0),1.17,.123*duck,
                    expression=worried,head=(-.043,.24+.11*duck),sway=.14*duck)
            star_pop=(1-ease(f,BONK+3,BONK+12)) if f>=BONK else .0001
            prop_pose(stars,f,(2.61,1.16,1.24),star_pop,(0,-.077*max(0,min(10,f-BONK)),0))
            x=approach(f).x
            if f<eye:
                side=ease(f,1,eye-1)
                cam_view(cam,f,mon,(x+1.34-.05*side,.46+.07*side,1.47),
                          (x-.045,.956,1.43),26,(x,.89,1.25))
            elif f<impact:
                z=ease(f,eye,eye+13)
                cam_view(cam,f,mon,(x+.91-.161*z,.31+.15*z,1.37),
                         (x+.03,1.268,1.23),34)
            elif f<reverse:
                hit_jitter=(.028,-.019,.013,-.006)[f-BONK] if BONK<=f<BONK+4 else 0.
                pos=Vector((3.27+hit_jitter,-.60,1.43+hit_jitter))
                cam_view(cam,f,mon,pos,(2.38,1.11,1.20),26)
            elif f<shout:
                slide(cam,f,mon,reverse,shout-1,(3.55,1.91,1.41),(3.50,1.84,1.42),
                      (2.28,.934,1.31),(2.29,.934,1.32),27)
            elif f<stone:
                slide(cam,f,mon,shout,stone-1,(3.04,.05,1.44),(3.11,.22,1.43),
                      (2.29,1.07,1.217),(2.31,1.10,1.23),28)
            else:
                slide(cam,f,mon,stone,tuesday-1,(3.21,.462,1.32),(3.10,.55,1.31),
                      (2.37,1.245,1.172),(2.39,1.245,1.172),46)
        elif f<locker:
            wind=(f-tuesday)*.103
            prop_pose(rain_group,f,(.16*wind,.01,-wind))
            show_day(day_tue,f,tuesday,locker)
            drive_car(rain_car,f,1.28-.047*(f-tuesday),2.038,1.28)
            walk(rain_boy,f,rainy_b,.64,tuesday,locker-1,"deadpan_blush",face=(.07,0))
            walk(rain_shoko,f,rainy_s,.64,tuesday,locker-1,"shy_glance",phase=6,face=(.044,-.19))
            runner=rainy_b(f)
            cam_view(cam,f,tue,runner+Vector((.53,-1.53,1.41)),runner+Vector((.28,.105,1.31)),26)
        elif f<wednesday:
            bp=Vector((-.32,.16,.0)); sp=Vector((.335,.24,.0))
            byaw=.16; btilt=.017; syaw=-.32; stilt=.055
            y_basis=Euler((0,0,byaw)).to_matrix()
            b_basis=Euler((btilt,0,0)).to_matrix()
            ear_loc=Vector((.291*hall_boy.head.scale.x,-.035*hall_boy.head.scale.y,-.022*hall_boy.head.scale.z))
            cup=bp+y_basis@(Vector((0,0,.59-LOWER))+b_basis@(Vector((0,0,k.FACE_CENTER-.59))+ear_loc))
            reach=ease(f,TAP-12,TAP)-ease(f,TAP+3,TAP+14)
            elbow=(-.224,-.168,.280)
            touch=target_arm(cup,sp,syaw,stilt,elbow)
            target=Vector((-.19,-.12,.23)).lerp(touch,reach)
            question=frame(47.54)<=f<frame(49.24)
            shoko_line=("chat_A","chat_E","chat_O","chat_M")[(f//4)%4] if question else "shy_glance"
            act(hall_shoko,f,sp,syaw,stilt,[(target,elbow),REST[1]],expression=shoko_line,head=(-.027,-.11))
            prop_pose(tap_fx,f,cup+Vector((.052,-.08,.043)),.34 if TAP<=f<TAP+3 else .0001)
            if f<panic:
                act(hall_boy,f,bp,byaw,btilt,expression="deadpan_blush",head=(0,0))
                pan=ease(f,locker,panic-1)
                cam_view(cam,f,hall,(.34-.165*pan,-1.14-.019*pan,1.38),
                         (.007,.13,1.18),26,cup if TAP-6<=f<TAP+8 else None)
            else:
                snap=ease(f,frame(49.66),frame(49.79))
                say=frame(50.86)<=f<=frame(51.92)
                expression="panic_sweat" if say and f%13<7 else "panic_wobble" if f>=frame(49.68) else "deadpan_blush"
                left=((-.217,-.155,.161+.27*snap),(-.227,-.064,.242))
                right=((.217,-.144,.179+.29*snap),(.218,-.067,.249))
                act(hall_boy,f,bp,byaw,.019-.093*snap,[left,right],expression=expression,
                    head=(-.062*snap,.015),sweat=.08+.70*ease(f,frame(49.68),wednesday-1) if snap>.01 else None)
                pull=ease(f,panic,panic+12)
                cam_view(cam,f,hall,(-.04,-1.205+.09*pull,1.31-.021*pull),(-.326,.03,1.19),51)
        elif PHONE<=f<PHONE_END:
            step=ease(f,PHONE,PHONE_END-1)
            prop_pose(macro_phone,f,(.0,.03,1.23),1,(.022,-.11+.09*step,-.050))
            slide(cam,f,insert,PHONE,PHONE_END-1,(.101,-1.79,1.38),(.039,-1.69,1.34),
                  (.0,.02,1.238),(.0,.025,1.225),51)
        else:
            bed_root=Vector((.135,.235,.0))
            rock=.03*math.sin(f*.143)
            rehearsal="worried_brows" if f<PHONE else ("chat_A","chat_E","chat_M","shy_glance")[(f//4)%4]
            act(night_shoko,f,bed_root,.145,.050,[((-.14,-.256,.255),(-.226,-.094,.199)),
                ((.155,-.254,.25),(.228,-.094,.203))],expression=rehearsal,head=(.19+.023*rock,-.095))
            prop_pose(small_phone,f,(.145,-.046,.772+.017*math.sin(f*.123)),.34,(-.18,0,.205))
            show_day(day_wed,f,wednesday,frame(53.34))
            for j,note in enumerate(floating):
                phase=(f-wednesday+j*14)%56/56
                amount=.53*math.sin(math.pi*phase)**.75
                prop_pose(note,f,(.255+.115*j+.042*math.sin(f*.16+j),-.137,1.14+.67*phase),amount,(.04,-.15+.264*phase,0))
            if f<PHONE:
                slide(cam,f,night,wednesday,PHONE-1,(.718,-1.78,1.40),(.585,-1.66,1.38),
                      (.184,.139,1.096),(.145,.136,1.14),26)
            else:
                slide(cam,f,night,PHONE_END,LENGTH,(.621,-1.45,1.37),(.44,-1.42,1.36),
                      (.177,.111,1.143),(.146,.158,1.175),26)
    actors=(mon_boy,mon_shoko,rain_boy,rain_shoko,hall_boy,hall_shoko,night_shoko)
    for rig in actors:
        rig.finish_bake()
    for group,ranges in ((mon,((1,tuesday-1),)),(tue,((tuesday,locker-1),)),
         (hall,((locker,wednesday-1),)),(night,((wednesday,PHONE-1),(PHONE_END,LENGTH))),
         (insert,((PHONE,PHONE_END-1),))):
        activate(group,ranges)
    for action in bpy.data.actions:
        for track in action.fcurves:
            mode="CONSTANT" if "hide_" in track.data_path or track.data_path=="lens" else "LINEAR"
            for point in track.keyframe_points:
                point.interpolation=mode
    for f,label in zip(CUTS,("Monday walk","Boy keeps a straight face","Lamppost bonk","Theek ho",
         "KYA","Stone-cold eyes","Tuesday rain","Headphone tap","Dhinchak Pooja","Wednesday",
         "Forty-song playlist insert","All-nighter payoff")):
        s.timeline_markers.new(label,frame=f)
    s.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(output/((output.name if polish else "part2_v01")+".blend")))
    proofs=tuple(sorted((*BENCH,1,eye+19,reverse+31,frame(39.98),wednesday+23,LENGTH))) if polish else BENCH
    (output/"shot_map.json").write_text(json.dumps({"cuts":[f-1 for f in CUTS[1:]],"proof_frames":proofs},indent=2))


if __name__=="__main__":
    main()
