"""Part 3: portrait-led planning under canvas and a late-afternoon cricket cut."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hook_continuation import *

s, cam, start, stop = begin(3)
frame = lambda second: ftime(second)-start
m = palette()
t = group(s,"Amber canvas command tent",0)
c = t[0]
canvas=k.texture("Woven amber canvas",("#362c31","#786047","#a48859"),"plaster",(.79,.86))
board=k.surface("Swabbed midnight green chalkboard","#293e3d",.85)
brass=k.surface("Aged brass orbit display","#ae815b",.72,.25)
box(c,"Pine plank flooring",(0,0,-.1),(10,10,.19),m["wood"])
box(c,"Amber canvas wall",(0,2.35,2.20),(8,.10,4.42),canvas)
for i in range(21):
    x=(i-10)*.35
    trace(c,"Vertical stitch and support",[(x,2.294,.03),(x*.99,2.290,2.08),(x,2.294,3.5)],.013,m["wood"])
    box(c,"Pine plank joint",(x,-.3,.001),(.014,7,.006),m["navy"])
for x in (-1.75,1.75):
    trace(c,"Tent load-bearing pole",[(x,1.3,0),(x,1.3,3.3)],.048,m["wood"])
    k.make_light_cone("Lantern wash in canvas space",c,(x-.16,1.04,2.93),(x-.16,1.04,.06),.125,.70,"#ffd39c")
    k.cylinder("Brass lantern",c,(x-.16,1.04,2.92),.13,.18,brass,r2=.095)
box(c,"Chalkboard timber bezel",(.50,2.11,1.73),(2.60,.13,1.51),m["wood"],True)
box(c,"Orbit story chalkboard",(.50,2.036,1.73),(2.48,.032,1.39),board)
label(c,"OBSERVATION",(.61,2.012,2.20),.121,m["paper"])
for j in range(7):
    trace(c,"Chalk diagram ruling",[(-.64,2.015,1.19+j*.105),(1.66,2.015,1.19+j*.105)],.0035,m["paper"])
for i in range(10):
    x=-.62+i*.249
    trace(c,"Vertical chalk ruling",[(x,2.016,1.12),(x,2.016,2.13)],.0035,m["paper"])
oval(c,"Wide stylized satellite orbit chalk mark",.61,1.99,1.63,.88,.312,m["green"],.011)
oval(c,"Secondary stylized orbit chalk mark",.61,1.984,1.64,.41,.35,m["red"],.008)
oval(c,"Chalk globe",.6,1.978,1.665,.25,.267,m["cyan"],.009)
k.ball("Brass table globe",c,(.51,.61,1.18),(.20,.20,.20),brass,segments=32)
for j in range(6):
    zz=1.18+(j-2.5)*.052
    rx=(.2**2-(zz-1.18)**2)**.5
    trace(c,"Globe latitude brass inlay",[(.51+rx*math.cos(i*math.tau/32),.61+rx*math.sin(i*math.tau/32),zz)
               for i in range(33)],.004,m["cyan"])
box(c,"Timber globe workbench",(.49,.78,.88),(1.42,.65,.13),m["wood"],True)
for x in (-.06,1.06):
    box(c,"Workbench leg",(x,.82,.43),(.093,.093,.83),m["wood"],True)
lights(c,"#ffbf82","#a7a8e6")
kalam=styled(c,"Kalam in command tent","kalam")
engineer=styled(c,"58th Engineer in command tent","engineer")
field=group(s,"Sunlit Thar cricket ground",18)
d=field[0]
desert_floor(d,m)
passby=k.empty("Distant illustrated satellite pass",d)
satellite_shade=k.emission("Dark cobalt satellite silhouette","#303c63")
box(d,"Transit silhouette center",(0,0,0),(.087,.045,.078),satellite_shade,parent=passby)
for x in (-.106,.106):
    box(d,"Transit silhouette panel",(x,0,0),(.107,.031,.045),satellite_shade,parent=passby)
    box(d,"Sun on distant solar edge",(x,-.016,.022),(.105,.011,.008),m["paper"],parent=passby)
board_sand=k.surface("Foot-worn cricket crease","#c68a54",.82)
box(d,"Cricket pitch packed clay",(.04,-.05,-.003),(1.22,4.35,.019),board_sand)
for y in (.39,.79,-1.86):
    trace(d,"Pale chalk cricket crease",[(-.58,y,.01),(.65,y,.01)],.011,m["paper"])
for x in (-.092,0,.092):
    k.cylinder("Wooden cricket stump",d,(.36+x,.65,.226),.016,.45,m["wood"],length_segments=12)
trace(d,"Cricket bail",[(.253,.65,.462),(.47,.65,.462)],.013,m["paper"])
for x in (-1.32,1.46):
    for y in (.89,1.53):
        box(d,"Wrapped kit box",(x,y,.16),(.42,.34,.32),m["wood"],True)
bat=k.empty("Edge-out cricket bat",d)
box(d,"Cricket bat ash blade",(0,0,.35),(.113,.037,.325),m["wood"],True,parent=bat)
box(d,"Cream cricket bat strike face",(0,-.022,.35),(.086,.008,.285),m["paper"],parent=bat)
k.cylinder("Cricket bat wrapped grip",d,(0,0,.136),.022,.188,m["ink"],parent=bat,length_segments=12)
ball=k.ball("Seamed red cricket ball",d,(-1,0,1),(.037,.037,.037),m["red"],segments=16,rings=10)
trace(d,"Ivory cricket-ball seam",[(-.039*math.cos(i*math.tau/16),0,.039*math.sin(i*math.tau/16)) for i in range(17)],.003,m["paper"],ball)
batter=styled(d,"Field 58th Engineer batter","engineer")
watcher=styled(d,"Kalam fielding on the edge","kalam")
cut=frame(35.66)
hit=frame(39.73)
for f in range(1,s.frame_end+1):
    if f<cut:
        track=push(f,frame(31.82),frame(32.95),frame(34.04),frame(34.95),cut-1)
        pose(kalam,f,(-.39,.20,0),.20,.06+.08*track,[
            ((-.22,-.15,.22),(-.249,-.064,.277)),
            ((.25+.24*track,-.145+.20*track,.23+.44*track),(.31,-.07,.29+.15*track))],
            "rest",(-.08,-.13*track))
        pose(engineer,f,(.95,.73,.018),-.26,.03,REST,"rest",(.03,.14))
        camera_move(cam,f,t,1,frame(34.30),(-.82,-2.2,1.79),(-.34,-1.61,1.63),
                    (.02,.43,1.32),(.015,.45,1.38))
    else:
        transit=ease(f,cut,frame(38.12))
        passby.location=(-2.0+4.7*transit,3.88,2.56+.19*math.sin(transit*math.pi))
        passby.rotation_euler.y=-.18+.42*transit
        key(passby,f,"location","rotation_euler")
        load=ease(f,hit-20,hit-7)
        swing=ease(f,hit-7,hit+5)
        recover=ease(f,hit+5,hit+19)
        yaw=-.17-.43*load+1.03*swing-.24*recover
        root=Vector((.30+.06*swing,.11,.003))
        pivot=Vector((.44-.15*load+.13*swing,-.235,.80+.09*load+.125*swing))
        angle=.52-1.67*load+2.82*swing-.39*recover
        direction=Vector((math.sin(angle),.21*load,math.cos(angle))).normalized()
        aim_object(bat,f,pivot-direction*.15,pivot+direction*.41)
        elbows=[(-.211,-.13,.29),(.248,-.10,.26)]
        arms=[(grip_target(pivot+direction*offset,root,yaw,.09,elbow),elbow)
              for elbow, offset in zip(elbows,(-.023,.03))]
        pose(batter,f,root,yaw,.09,arms,"rest",(-.09,.15- .22*swing))
        pose(watcher,f,(-.69,.85,0),.37,.065,REST,"rest",(.04,-.09))
        contact_swing=ease(hit,hit-7,hit+5)
        contact_angle=.52-1.67+2.82*contact_swing
        contact_axis=Vector((math.sin(contact_angle),.21,math.cos(contact_angle))).normalized()
        impact=Vector((.29+.13*contact_swing,-.235,.89+.125*contact_swing))+contact_axis*.21
        if f<hit:
            u=ease(f,hit-19,hit)
            ball.location=Vector((-.81,-.62,1.22)).lerp(impact,u)
        else:
            u=min(1,(f-hit)/22)
            ball.location=impact+Vector((.98*u,.12*u,1.09*u-.44*u*u))
        ball.hide_viewport=ball.hide_render=f<hit-19
        key(ball,f,"location","hide_viewport","hide_render")
        camera_move(cam,f,field,cut,hit-3,(-.55,-2.35,1.57),(.17,-2.12,1.50),
                    (.02,.26,1.18),(.27,.25,1.24))
close(s,3,[kalam,engineer,batter,watcher],[(t,1,cut-1),(field,cut,s.frame_end)],
      [1,cut],[1,frame(29.22),frame(31.36),frame(34.04),cut,hit-7,hit,hit+8,s.frame_end])
