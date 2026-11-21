"""Part 4: twilight work, a symbolic seismic impact, and the war-room payoff."""
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hook_continuation import *
from sets import war_room

s,cam,start,stop=begin(4)
frame=lambda seconds: ftime(seconds)-start
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
    k.make_ricks_light("Warm work light pool",c,(x,.31,1.58),(x-.18,0,.4),"#ffb880",84,.45)
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
box(c,"Sealed symbolic bunker access",(0,.786,.53),(1.42,.105,.91),m["navy"])
for j in range(5):
    trace(c,"Recessed light rail",[(-.62+j*.31,.709,.12),(-.62+j*.31,.709,.85)],.014,amber)
for index in range(10):
    z=.20+index*.066
    trace(c,"Industrial gate rib",[(-.70,.706,z),(.70,.706,z)],.009,m["steel"])
box(c,"Warm amber landing strip",(0,.32,.051),(1.30,.55,.10),m["wood"],True)
crate=k.empty("Equipment silhouette",c)
box(c,"Hanging equipment case",(0,0,-.16),(.25,.22,.31),m["steel"],True,parent=crate)
box(c,"Painted band",(0,-.116,-.158),(.233,.014,.072),amber,parent=crate)
worker=styled(c,"Moonlight gear engineer","engineer")
wind=group(s,"Wind and straw at desert blue hour",18)
d=wind[0]
desert_floor(d,m,True)
sweeper=styled(d,"Sweeping 58th engineer","engineer")
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
final=group(s,"CIA alarm finale",70)
e=final[0]
boss=styled(e,"Finale CIA boss","analyst")
cup=war_room(e,boss)
for prop in e.objects:
    if prop.type=="CURVE" and prop.parent is None and prop.data.splines:
        spline=prop.data.splines[0]
        if spline.bezier_points and spline.bezier_points[0].co.y>2:
            prop.data.resolution_u=1
            prop.data.bevel_resolution=0
analyst=styled(e,"Alarm desk analyst","analyst")
box(e,"Alarm panel dark matte backing",(.07,2.11,2.48),(1.93,.07,.25),m["navy"],True)
label(e,"SEISMIC EVENT: INDIA",(.07,2.064,2.451),.102,m["red"])
for x in (-1.06,1.18):
    k.cylinder("Crimson alert beacon",e,(x,1.59,1.69),.085,.16,m["red"],length_segments=18)
redlight=k.make_ricks_light("Crimson alarm face rim",e,(-.96,-.6,2.43),(.1,.63,1.23),"#ff6676",95,.97)
c1=frame(45.16)
c2=frame(50.78)
c3=frame(51.56)
c4=c3+8
shock=frame(53.13)
drop=shock+4
cup_loc=cup.location.copy()
for f in range(1,s.frame_end+1):
    if f<c1:
        sweep_edge.location.x=-.72+4.8*ease(f,1,frame(42.07))
        key(sweep_edge,f,"location")
        descend=ease(f,frame(42.84),frame(44.96))
        crate.location=(.42,.388,1.24-.78*descend)
        key(crate,f,"location")
        trace_height=.12*ease(f,frame(42.12),frame(43.04))
        pose(worker,f,(-.48,.06,.001),.49,.11+.11*descend,
             [((-.18,-.18,.22),(-.20,-.089,.30)),
              ((.27+.12*descend,-.065,.30+trace_height-.24*descend),(.24,-.11,.28))],"rest",(-.06,-.11))
        camera_move(cam,f,night,1,c1-1,(-.86,-2.09,1.71),(.21,-1.66,1.54),
                    (-.04,.29,1.10),(.02,.29,.94))
    elif f<c2:
        shift=push(f,c1,c1+6,c1+12,frame(46.8),frame(47.3))
        sw=max(0,f-frame(47.28))
        sweep=math.sin(sw*.104)*ease(f,frame(47.28),frame(47.52))*(1-ease(f,frame(49.37),frame(49.9)))
        root=Vector((.11,.225,0))
        broom_top=Vector((.40+.27*sweep,-.18,.80+.12*shift))
        broom_base=Vector((.56+.48*sweep,-.53,.22))
        aim_object(broom,f,broom_base,broom_top)
        el=(.25,-.072,.268)
        target=broom_base+(broom_top-broom_base).normalized()*.53
        pose(sweeper,f,root,-.21+.16*sweep,.10+.08*abs(sweep),
             [((-.24,-.1-.09*shift,.24+.24*shift),(-.21,-.08,.28)),
              (grip_target(target,root,-.21+.16*sweep,.10+.08*abs(sweep),el),el)],"rest",(.03,.08))
        dust.location=(.04*sw%1.81-.91,0,0)
        key(dust,f,"location")
        marks.hide_render=marks.hide_viewport=f>=frame(49.03)
        key(marks,f,"hide_render","hide_viewport")
        camera_move(cam,f,wind,c1,c1+12,(-.60,-2.13,1.55),(-.10,-1.72,1.34),
                    (.075,.13,1.10),(.12,.12,.87))
    elif f<c3:
        grow=.10+1.48*ease(f,frame(50.99),c3-2)
        burst.location=(0,3.13,0)
        burst.scale=(grow,grow,grow)
        key(burst,f,"location","scale")
        shake=.03*math.sin((f-(c3-5))*2.2) if c3-5<=f<c3-1 else 0
        camera_at(cam,f,blast,(shake,-2.30,1.25+shake),(0,2.7,1.28))
    elif f<c4:
        camera_at(cam,f,comic,(0,-1.18,1.12),(0,1.01,1.07))
    else:
        root=Vector((.06,.48,.065))
        alarm=ease(f,shock-2,shock+5)
        yaw=.09-.05*alarm
        tilt=.045-.105*alarm
        pose(boss,f,root,yaw,tilt,[((-.20,-.09-.10*alarm,.25+.26*alarm),(-.21,-.025,.265)),
             ((.24,-.14-.10*alarm,.41+.12*alarm),(.23,-.045,.29))],
             "rest" if f<shock else "AA",(.03-.10*alarm,.01),desk_legs())
        pose(analyst,f,(.77,1.26,.01),-.22,.025-.06*alarm,
             [((-.22,-.09,.24+.17*alarm),(-.23,-.04,.265)),REST[1]],
             "rest" if f<shock else "OH",(.06,-.11))
        if f<=drop:
            mug_grip(cup,boss,f,root,yaw,tilt,.02)
            cup_loc=cup.location.copy()
        else:
            u=min(1,(f-drop)/12)
            cup.location=cup_loc+Vector((.11*u,-.15*u,-.35*u*u))
            cup.rotation_euler=(.41*u,.48*u,math.pi-.75*u)
            key(cup,f,"location","rotation_euler")
        redlight.data.energy=65+40*(.5+.5*math.sin(f*.31))
        key(redlight.data,f,"energy")
        camera_move(cam,f,final,c4,c4+12,(1.0,-2.49,1.63),(.51,-1.91,1.55),
                    (.24,.56,1.34),(.26,.51,1.36))
close(s,4,[worker,sweeper,boss,analyst],
      [(night,1,c1-1),(wind,c1,c2-1),(blast,c2,c3-1),(comic,c3,c4-1),(final,c4,s.frame_end)],
      [1,c1,c2,c3,c4],[1,frame(43.28),c1+12,frame(47.91),frame(50.27),c3-2,c3+2,c4+12,shock+7,s.frame_end])
