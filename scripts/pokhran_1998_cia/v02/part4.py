"""Part 4: moonlit work, an abstract seismic graphic, and the red alarm payoff."""
from staging import *

s,cam,frame=opening(4)
s.eevee.taa_render_samples=5
m=palette()
night=group(s,"Moonlit Thar work site",0)
c=night[0]
desert_floor(c,m,True)
amber=k.emission("Warm lantern reflection","#ffa45d",2.2)
scan=translucent("Illustrative last sliver of red scan","#ff5874",.32,1.45)
sweep_edge=k.empty("Scan fading out of the frame",c)
k.mesh("Symbolic receding scan beam",c,[(-.13,1.52,.001),(.21,1.52,.001),(.06,1.52,3.62)],
       [(0,1,2)],scan,parent=sweep_edge)
for x in (-1.27,1.23):
    trace(c,"Industrial work-lamp stand",[(x,.36,0),(x,.36,1.63)],.024,m["steel"])
    box(c,"Caged amber work lamp",(x,.36,1.65),(.19,.16,.13),m["wood"],True)
    box(c,"Frosted amber lamp face",(x,.267,1.65),(.13,.025,.095),amber)
    k.make_light_cone("Glowing amber work light",c,(x,.27,1.59),(x,.27,.01),.055,.46,"#ffa66c")
    lamp=k.make_ricks_light("Warm work light pool",c,(x,.31,1.58),(x-.18,0,.4),"#ffb880",84,.45)
    lamp.data.use_shadow=False
    for index in range(8):
        z=.16+index*.166
        trace(c,"Side rails on light gantry",[(x-.165,.452,z),(x+.16,.452,z)],.016,m["steel"])
for i in range(5):
    x=-1.25+i*.63
    box(c,"Sandbag wall", (x,.93,.125),(.49,.25,.25),m["wood"],True)
    box(c,"Survey gear storage case",(x+.07,1.31,.24),(.39,.31,.48),m["steel"],True)
for x in (-.78,.75):
    box(c,"Graphite portal frame upright",(x,.70,.51),(.18,.23,1.02),m["steel"],True)
box(c,"Graphite portal frame top",(0,.70,1.01),(1.68,.23,.18),m["steel"],True)
hatch=box(c,"Sliding scenic access plate",(0,.786,.53),(1.42,.105,.91),m["navy"],True)
for j in range(5):
    trace(c,"Recessed light rail",[(-.62+j*.31,.709,.12),(-.62+j*.31,.709,.85)],.014,amber)
for index in range(10):
    z=.20+index*.066
    trace(c,"Industrial gate rib",[(-.70,.706,z),(.70,.706,z)],.009,m["steel"])
box(c,"Warm amber landing strip",(0,.32,.051),(1.30,.55,.10),m["wood"],True)
crate=k.empty("Equipment silhouette",c)
box(c,"Hanging equipment case",(0,0,-.16),(.25,.22,.31),m["steel"],True,parent=crate)
box(c,"Painted band",(0,-.116,-.158),(.233,.014,.072),amber,parent=crate)
worker=actor(c,"Moonlight gear engineer","engineer",small=True)
wind=group(s,"Wind and straw at desert blue hour",18)
d=wind[0]
desert_floor(d,m,True)
sweeper=actor(d,"Sweeping 58th engineer","engineer",small=True)
broom=k.empty("Flat straw broom",d)
k.cylinder("Wood broom handle",d,(0,0,.33),.019,.66,m["wood"],parent=broom,length_segments=12)
straw=k.surface("Cut golden straw","#c29158",.78)
for i in range(19):
    a=i/18-.5
    trace(d,"Tapered broom straw",[(0,0,.065),(a*.14,.023,-.125),(a*.24,.034,-.25)],.009,straw,broom)
whisk=translucent("Ink wash suspended windblown sand","#e7ae7f",.51,1.13)
dust=k.empty("Low ribbons of blowing sand",d)
for j in range(9):
    trace(d,"Abstract dry wind marks",[(i*.113-1.1,-.09+.032*math.sin(i*.58+j),.09+j*.032+.029*math.sin(i*.51+j))
              for i in range(13)],.007,whisk,dust)
fine_dust=k.empty("Fine flecks close to the raised hand",d)
flick_rng=Random(919)
for i in range(107):
    x,z=flick_rng.uniform(-.37,.42),flick_rng.uniform(-.26,.27)
    w=flick_rng.uniform(.014,.079)
    trace(d,"Sunlit fleck of airborne grit",[(x,0,z),(x+w,0,z+.017)],.004,
          m["paper"] if i%3 else m["steel"],fine_dust)
marks=k.empty("Foreground impression shapes",d)
for i in range(9):
    trace(d,"Broken sand indentation",[(.29+i*.056,-.68+i*.028,.012),(.34+i*.056,-.655+i*.028,.012),
          (.41+i*.056,-.668+i*.028,.012)],.019,m["wood"],marks)
for x in (-.94,1.00):
    box(d,"Dust-streaked camp rail",(x,1.22,.43),(.12,1.01,.083),m["wood"],True)
    for j in range(5):
        y=.75+j*.21
        trace(d,"Camp rail upright post",[(x,y,.012),(x,y,.57)],.026,m["wood"])
        trace(d,"Canvas seam under rail",[(x+.018,y,.28),(x-.018,y,.51)],.013,m["paper"])
blast=group(s,"Stylized seismic horizon",36)
b=blast[0]
desert_floor(b,m,True)
core=k.emission("Gold seismic graphic","#ffca83",2.2)
cool=k.emission("Coral outer shock edge","#ff9f77",1.22)
pale=k.emission("Ivory seismic splash","#ffe7b5",2.4)
burst=k.empty("Symbolic seismic dome expanding",b)
k.ball("Billowing seismic light mass",b,(0,0,.30),(.55,.24,.45),core,burst,segments=32,rings=20)
for j in range(20):
    x=(j-9.5)*.070
    z=.19+.29*max(0,1-abs(x)*1.4)
    w=.16+.06*math.sin(j*1.2)
    k.ball("Graphic dust lobe",b,(x,.012*math.sin(j),z),(w,.27,w*1.10),
           core if j%3 else pale,burst,segments=16,rings=10)
for j in range(4):
    points=[((.48+j*.17)*math.cos(i*math.tau/46),
             (.16+j*.08)*math.sin(i*math.tau/46),.026+j*.013) for i in range(47)]
    trace(b,"Expanding elliptical seismic ring",points,.014,cool,burst)
comic=group(s,"Two-tone eight-frame seismic impact artwork",54)
q=comic[0]
ink=k.emission("Impact near-black ink","#171322",.9)
cream=k.emission("Impact pale ochre paper","#f8d39a",1.27)
box(q,"Impact ink background",(0,1.26,1.38),(8,.09,6),ink)
verts=[(0,1.014,.96)]
for i in range(80):
    a=i*math.tau/80
    r=(.82+.095*math.sin(i*.53))*(1 if i%2 else 1.16)
    verts.append((r*math.cos(a),1.014,.96+r*math.sin(a)))
k.mesh("Printed two-tone impact cloud",q,verts,[(0,i+1,(i+1)%80+1) for i in range(80)],cream)
for i in range(24):
    a=i*math.tau/24
    r=1.05+.085*math.sin(i*1.7)
    length=.32+.34*(.5+.5*math.sin(i*2.3))
    trace(q,"Radial printed impact streak",[(r*math.cos(a),.990,.96+r*math.sin(a)),
          ((r+length)*math.cos(a),.990,.96+(r+length)*math.sin(a))],.012,cream)

label(c,"BLINDSPOT ACTIVE",(.11,.53,1.24),.083,m["green"])
box(c,"Recessed lighting window behind the scenic gate",(0,.845,.51),(1.36,.035,.89),m["ink"])
for j in range(6):
    z=.20+j*.105
    trace(c,"Amber interior light strips",[(-.46,.812,z),(.55,.812,z)],.010,amber)
winch=k.empty("Theatrical winch crank",c,(-.34,.17,.81))
oval(c,"Industrial crank wheel",0,0,0,.19,.19,amber,.024).parent=winch
for j in range(5):
    ang=j*tau/5
    trace(c,"Steel edges on winch handwheel",[(0,0,0),(.17*cos(ang),0,.17*sin(ang))],.016,m["steel"],winch)
trace(c,"Wooden crank grip",[(.176,-.045,0),(.176,-.114,0)],.022,m["wood"],winch)
stage_fx=pathspark(c,m,"Graphic prop wheel sparks",.17)
bat=k.empty("Bat dropped at transition",c)
box(c,"Ash cricket bat wing",(0,0,.31),(.10,.038,.33),m["wood"],True,parent=bat)
trace(c,"Wrapped cricket bat handle",[(0,0,0),(0,0,.18)],.019,m["ink"],bat)
mate=actor(c,"Moonlight assistant engineer","engineer",small=True)
second=actor(d,"Second sweeping engineer","engineer",small=True)
broom2=k.empty("Second straw broom",d)
for obj in list(broom.children):
    duplicate=obj.copy()
    d.objects.link(duplicate)
    duplicate.parent=broom2
tracks=[]
for index in range(20):
    x=-.70+.073*index
    track=k.empty("Removable surface marks",d,(x,-.87,0))
    for j in range(2):
        yy=j*.23+.055*sin(index*.71)
        trace(d,"Tire and boot impression",[(-.022,yy,.007),(.031,yy+.063,.009),
              (.074,yy+.022,.008)],.012,m["wood"],track)
    tracks.append(track)

dust_gold=k.surface("Cel shaded gold dust","#c78b58",.85,.03,.16)
dust_amber=k.surface("Cel shaded earth plume","#a86952",.81,.01,.13)
eddies=[]
for j in range(16):
    x=(j-7.5)*.20
    z=.16+.22*(1-abs(x)/1.7)+.21*sin(j*2)**2
    puff=k.ball("Dimensional dust eddy",b,(x,.02,z),(.26,.30,.16+.12*sin(j)**2),
                dust_gold if j%3 else dust_amber,segments=16,rings=10,parent=burst)
    eddies.append((puff,puff.location.copy()))
rock_rng=Random(984)
rocks=[]
for j in range(30):
    start=Vector((rock_rng.uniform(-1.8,1.8),rock_rng.uniform(2.35,3.20),rock_rng.uniform(.04,.22)))
    trajectory=Vector((rock_rng.uniform(-1.8,1.8),rock_rng.uniform(-1.,.3),rock_rng.uniform(.53,2.10)))
    chunk=k.ball("Silhouette of flying earth chunk",b,start,(.045,.039,.041),dust_amber,segments=8,rings=5)
    rocks.append((chunk,start,trajectory))
cracks=[]
for j in range(8):
    series=[(.14*j-.54+i*(j-3.5)*.054,3.2-i*.29,.0015+.0001*j) for i in range(10)]
    cracks.append(trace(b,"Jagged foreground seismic fissure",
                        [(x+.14*sin(i*1.82+j),y,z) for i,(x,y,z) in enumerate(series)],.025,m["ink"]))

final=group(s,"Pure crimson CIA alarm payoff",78)
e=final[0]
screen_glow=console(e,m,alarm=True)
crew=[actor(e,name,"analyst",small=True) for name in ("CIA Boss Alarm","CIA Analyst One Alarm","CIA Analyst Two Alarm")]
roots=[desk(e,m,x,y,rig.name) for (x,y),rig in zip(((0,.05),(-.86,.63),(.86,.63)),crew)]
glasses(e,crew[0],m["ink"])
label(e,"SEISMIC EVENT DETECTED: INDIA",(0,2.142,3.014),.097,m["paper"])
for x in (-1.20,1.20):
    k.cylinder("Rotating red beacon",e,(x,1.70,1.73),.086,.16,m["red"],length_segments=18)
alarms=[k.make_ricks_light("Alarm red fill",e,(x,-.35,2.34),(x*.25,.65,1.32),"#fa1745",140,.94) for x in (-1.20,1.20)]
for lamp in alarms:
    lamp.data.use_shadow=False
cup=k.empty("Stunt porcelain mug",e)
k.cylinder("Dark plum mug wall",e,(0,0,0),.070,.14,m["paper"],cup,length_segments=24)
k.cylinder("Dark coffee surface",e,(0,0,.070),.058,.009,m["wood"],cup,length_segments=24)
oval(e,"Coffee mug handle",.075,0,.003,.050,.047,m["paper"],.014).parent=cup
coffee=pathspark(e,m,"Graphic amber splash",.26)
for j in range(11):
    a=j*tau/11
    x,z=.19*cos(a),.14*sin(a)
    k.ball("Coffee droplet",e,(x,0,z),(.017,.014,.021),m["wood"],coffee,segments=8,rings=5)

c1=frame(43.21)
c2=frame(45.20)
c3=frame(46.00)
c4=frame(50.60)
c5=frame(52.05)
c6=c5+8
for collection in (c,d,b):
    for obj in collection.objects:
        if obj.type=="CURVE" and obj.name.startswith(("Rippled sand edge","Low ribbons","Dusty folded scrub")):
            obj.data.resolution_u=2
            obj.data.bevel_resolution=0
quake=frame(50.94)
shock=frame(52.61)
drop=frame(52.83)
crash=frame(53.23)
hold=s.frame_end-15
for f in range(1,s.frame_end+1):
    if f<c2:
        sweep_edge.location.x=-.76+5.0*ease(f,1,frame(41.84))
        key(sweep_edge,f,"location")
        pull=ease(f,frame(41.75),frame(42.86))
        hatch.location.x=1.49*pull
        key(hatch,f,"location")
        turn=ease(f,c1-6,c2-4)
        phase=1.91*tau*turn
        winch.rotation_euler.y=phase
        key(winch,f,"rotation_euler")
        crate.location=(.36,.466,1.21-.82*turn)
        crate.rotation_euler.z=.12*sin(phase)
        key(crate,f,"location","rotation_euler")
        bat_drop=ease(f,1,frame(41.76))
        bat.location=(-.50-.22*bat_drop,-.57,.76-.69*bat_drop)
        bat.rotation_euler.y=.35+1.18*bat_drop
        key(bat,f,"location","rotation_euler")
        position=Vector((-.64,.24,0))
        yaw=.27
        tilt=.105+.065*sin(phase)
        hand=Vector((-.34+.176*cos(phase),.069,.81-.176*sin(phase)))
        elbow=(.22,-.11,.24)
        pose(worker,f,position,yaw,tilt,[REST[0],(grip_target(hand,position,yaw,tilt,elbow),elbow)],
             "rest",(-.07-.07*sin(phase),.12))
        guide=ease(f,frame(42.24),c1+4)
        pose(mate,f,(.61,.38,0),-.42,.12+.06*pull,
             [((-.24,-.17,.30+.18*guide),(-.20,-.08,.26)),REST[1]],"rest",(-.08,.04))
        flick=1 if turn>.02 and (f-c1)%17 in (0,1,2) else .0001
        spark_at(stage_fx,f,(-.18,.044,.72),flick)
        if f<c1:
            camera_move(cam,f,night,1,c1-1,(-1.55,-2.58,1.82),(-1.19,-2.28,1.69),
                        (.03,.29,1.16),(.05,.35,1.15))
        else:
            camera_move(cam,f,night,c1,c2-1,(1.15,-2.19,1.47),(.79,-2.02,1.41),
                        (.04,.35,.96),(.09,.42,.92))
    elif f<c4:
        motion=ease(f,c3,frame(46.47))*(1-ease(f,frame(49.52),frame(50.07)))
        for j,(rig,tool,x,y) in enumerate(((sweeper,broom,-.49,.05),(second,broom2,.57,.68))):
            sway=sin((f-c3)*.17-1.2*j)*motion
            tilt=.19+.13*motion
            root=Vector((x,y,0))
            yaw=.26 if j==0 else -.26
            foot=Vector((x+.35+.45*sway,y-.56,.234))
            high=Vector((x+.23+.30*sway,y-.31,.83))
            aim_object(tool,f,foot,high)
            target=foot+(high-foot).normalized()*.53
            other=Vector((-.23,-.14,.19+.33*(1-ease(f,c3,c3+12)))) if j==0 else Vector((-.22,-.15,.27))
            el=(.24,-.08,.26)
            pose(rig,f,root,yaw,tilt,[(other,(-.21,-.09,.25)),(grip_target(target,root,yaw,tilt,el),el)],
                 "rest",(.07,-.14 if j else .08))
        for j,track in enumerate(tracks):
            value=1-ease(f,frame(47.33)+3*j,frame(47.53)+3*j)
            track.scale=(max(.0001,value),)*3
            key(track,f,"scale")
        marks.scale=(.0001,)*3
        if f<c3:
            dust.location=(-.51+.48*((f-c2)%24)/24,-.30,1.04)
            dust.scale=(.41,.41,.49)
            fine_dust.location=(-.63+.48*((f-c2)%24)/24,-.29,1.12)
            fine_dust.scale=(1,)*3
            camera_move(cam,f,wind,c2,c3-1,(-.82,-1.63,1.43),(-.69,-1.61,1.40),
                        (-.60,.04,1.20),(-.60,.04,1.19),51)
        else:
            dust.location=(.028*(f-c3)%1.4-.62,-.07,0)
            dust.scale=(.79,.75,.46)
            fine_dust.scale=(.0001,)*3
            camera_move(cam,f,wind,c3,frame(50.10),(1.46,-2.38,1.57),(1.02,-2.31,1.52),
                        (.03,.12,.94),(.07,.13,.91))
        key(dust,f,"location","scale")
        key(fine_dust,f,"location","scale")
    elif f<c5:
        v=ease(f,quake,c5-2)
        blast_scale=.04+1.74*v
        burst.location=(0,3.13,0)
        burst.scale=(blast_scale,blast_scale,blast_scale)
        key(burst,f,"location","scale")
        for j,(puff,where) in enumerate(eddies):
            puff.location=where+Vector((.24*v*sin(j),0,v*(.15+.48*sin(j*.58)**2)))
            puff.rotation_euler.y=.55*sin(j+v*3)
            key(puff,f,"location","rotation_euler")
        for index,(chunk,base,trajectory) in enumerate(rocks):
            u=ease(f,quake+index%6,c5)
            chunk.location=base+trajectory*u-Vector((0,0,.72*u*u))
            chunk.scale=(.001+.96*u,)*3
            chunk.rotation_euler=(4*u,2.77*u,index*.30)
            key(chunk,f,"location","scale","rotation_euler")
        for j,crack in enumerate(cracks):
            crack.data.bevel_factor_end=max(.001,ease(f,c4+j%4,quake+7))
            key(crack.data,f,"bevel_factor_end")
        jitter=((.045,-.032,.038,-.019)[f-quake]) if quake<=f<quake+4 else 0
        camera_at(cam,f,blast,(.29-.17*v+jitter,-2.79-.30*v,1.44+2*jitter),(0,3.1,1.28+.28*v))
    elif f<c6:
        camera_at(cam,f,comic,(0,-1.18,1.12),(0,1.01,1.07))
    else:
        flash=.5+.5*cos((min(hold,f)-c6)*.48)
        next(n for n in screen_glow.node_tree.nodes if n.type=="EMISSION").inputs[1].default_value=.82+flash*1.14
        key(next(n for n in screen_glow.node_tree.nodes if n.type=="EMISSION").inputs[1],f,"default_value")
        for lamp in alarms:
            lamp.data.energy=115+flash*200
            key(lamp.data,f,"energy")
        if f<=drop:
            mug_center=Vector((-.25,-.014,1.07+.12*ease(f,c6,drop)))
            cup.location=mug_center
            cup.rotation_euler=(.13,0,pi)
        elif f<=crash:
            u=(f-drop)/(crash-drop)
            cup.location=(-.25+.35*u,-.014-.15*u,1.19-.27*u*u)
            cup.rotation_euler=(.13+.88*u,.43*u,pi-1.19*u)
        else:
            u=ease(f,crash,crash+14)
            cup.location=(.1+.20*u,-.164-.118*u,.92+.11*sin(pi*u))
            cup.rotation_euler=(1.01+.52*u,.43-.27*u,pi-1.19-1.07*u)
        key(cup,f,"location","rotation_euler")
        spark_at(coffee,f,(.125,-.19,.945),(1-ease(f,crash,crash+10)) if f>=crash else .0001)
        for index,(rig,root) in enumerate(zip(crew,roots)):
            t=ease(f,shock+index*2,shock+index*2+7)
            sway=.035*sin((min(f,hold)-c6)*.25+index)*t
            yaw=(-.03,.19,-.26)[index]
            tilt=.03-.135*t
            left=Vector((-.22-.06*t,-.18,.29+.31*t))
            right=Vector((.22+.06*t,-.16,.25+.36*t))
            if index==0 and f<=drop:
                left=grip(cup.location+cup.rotation_euler.to_matrix()@Vector((.124,0,0)),root,yaw,tilt)
            seated(rig,f,root,yaw,tilt,[(left,(-.245,-.11,.34)),(right,(.24,-.083,.32))],
                   "shock" if f>=shock+index*2 else "rest",(-.13*t,sway))
        camera_move(cam,f,final,c6,c6+12,(1.39,-3.00,1.79),(.98,-2.91,1.79),
                    (.04,.65,1.38),(.03,.64,1.42))

finish(s,4,[worker,mate,sweeper,second,*crew],[(night,1,c2-1),(wind,c2,c4-1),(blast,c4,c5-1),
       (comic,c5,c6-1),(final,c6,s.frame_end)],[1,c1,c2,c3,c4,c5,c6],
       [1,frame(42.50),c1+6,c2+12,c3+20,frame(49.80),c4,c5-2,c5+3,c6,crash+2,s.frame_end],
       flashes=(tuple(range(c5,c6))))
