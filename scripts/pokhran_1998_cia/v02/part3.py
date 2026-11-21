"""Part 3: command-tent realization and a complete cricket delivery."""
from staging import *

s,cam,frame=opening(3)
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
label(c,"OBSERVATION / BLINDSPOTS",(.61,2.012,2.20),.093,m["paper"])
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
kalam=actor(c,"Kalam in command tent","kalam",small=True)
engineer=actor(c,"58th Engineer in command tent","engineer",small=True)
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
batter=actor(d,"Field 58th Engineer batter","engineer",small=True)
watcher=actor(d,"Kalam fielding on the edge","kalam",small=True)
second=actor(c,"Second 58th Engineer in tent","engineer",small=True)
bowler=actor(d,"Running field bowler","engineer",small=True)
for x in (-1.16,1.27):
    for j in range(4):
        k.ball("Worn canvas sandbag",c,(x+.075*(j%2),1.47,.092+.149*j),(.23,.16,.102),canvas,
               segments=14,rings=8)
for i in range(7):
    trace(d,"Camouflage net strand",[(-1.83+.19*i,1.82,.05),(-1.70+.20*i,1.83,.71),
          (-1.70+.22*i,1.84,1.14)],.012,m["wood"])
for i in range(6):
    trace(d,"Camouflage net cross mesh",[(-1.79,1.83,.13+.17*i),(-.58,1.83,.11+.17*i)],.011,m["wood"])
chalk=k.cylinder("Chalk stub held in thumb mitten",c,(.80,1.94,1.75),.020,.11,m["paper"],length_segments=12)
chalk_arc=trace(c,"Drawn green chalk path",[(.53+.32*i/34,1.974,1.73+.19*sin(i*pi/43)) for i in range(35)],
                .016,m["green"])
label(c,"RED SCAN",(.67,1.976,1.53),.064,m["red"])
label(c,"GREEN BLINDSPOT",(.73,1.976,1.38),.047,m["green"])
light_scan=scan_pyramid(d,"Stylized passing scan above the cricket pitch",.17)
impact_fx=pathspark(d,m,"Comic cricket hit",.29)
photo=k.empty("Just cricket photo title card",d,parent=cam)
box(d,"Warm white shutter print", (0,0,0),(1.23,.04,.79),m["paper"],True,parent=photo)
box(d,"Ink blue inset print",(0,-.026,.061),(1.12,.008,.58),m["navy"],parent=photo)
title=label(d,"JUST CRICKET",(0,-.052,-.30),.097,m["ink"])
title.parent=photo
for j in range(8):
    trace(d,"Desert contour in surveillance print",[(-.52+.115*i,-.034,-.14+j*.052+.025*sin(i*.81+j))
              for i in range(10)],.005,m["cyan"],photo)
for x in (-.25,.2):
    trace(d,"Stick player silhouette in print",[(x,-.045,.19),(x,-.045,.047),(x-.052,-.045,-.075)],.013,m["paper"],photo)
    trace(d,"Bat in silhouette",[(x,-.052,.08),(x+.135,-.053,.22)],.014,m["paper"],photo)
    oval(d,"Round character head in print",x,-.048,.212,.048,.049,m["paper"],.010).parent=photo

wide2=frame(31.12)
macro=frame(33.62)
back=frame(34.36)
cut=frame(35.60)
bat_cut=frame(38.32)
hit=frame(39.73)
shutter=frame(40.30)
release=frame(38.08)

def bowler_path(f):
    run=ease(f,cut+2,release)
    clear=ease(f,release+4,hit-5)
    return Vector((-1.09+1.15*run-1.34*clear,.84-run+1.16*clear,0))

for f in range(1,s.frame_end+1):
    if f<cut:
        point=ease(f,frame(31.31),frame(32.55))-ease(f,frame(32.62),macro)
        writing=ease(f,macro-3,back-1)
        switch=ease(f,macro-19,macro)* (1-ease(f,back,back+12))
        thumbs=ease(f,back+2,back+14)
        root=Vector((-.43+.45*switch,.18+1.16*switch,0))
        yaw=.30+.65*switch
        tilt=.09+.075*point
        mark=Vector((.53+.32*writing,1.92,1.73+.19*sin(writing*pi*.79)))
        chalk.location=mark
        chalk.rotation_euler.x=1.24
        key(chalk,f,"location")
        chalk_arc.data.bevel_factor_end=max(.002,writing)
        key(chalk_arc.data,f,"bevel_factor_end")
        right=Vector((.24+.08*point,-.18,.30+.25*point+.20*thumbs))
        if writing<1 and switch>.45:
            right=grip_target(mark,root,yaw,tilt,(.25,-.13,.29))
        pose(kalam,f,root,yaw,tilt,[(REST[0]),(right,(.24,-.13,.29))],"rest",(-.11*thumbs,.12*point))
        for j,(rig,x,y) in enumerate(((engineer,.66,.42),(second,-1.04,.55))):
            nod=.032*sin(f*.23+j)
            hand=.10*(point+.40*thumbs)*(1 if j else -1)
            pose(rig,f,(x,y,0),(-.22,.40)[j],.08+nod,
                 [((-.26,-.16,.22+hand),(-.24,-.07,.29)),REST[1]],"rest",(.03+nod,-.20))
        if f<wide2:
            camera_move(cam,f,t,1,wide2-1,(-1.12,-2.80,1.98),(-.98,-2.69,1.83),
                        (-.16,.42,1.35),(-.15,.45,1.39))
        elif f<macro:
            camera_move(cam,f,t,wide2,macro-1,(1.30,-2.06,1.70),(.84,-1.94,1.71),
                        (.14,.42,1.34),(.19,.55,1.39))
        elif f<back:
            camera_move(cam,f,t,macro,back-1,(.75,.58,1.86),(.88,.65,1.82),
                        (.71,1.99,1.68),(.72,1.96,1.69),52)
        else:
            camera_move(cam,f,t,back,cut-1,(-.72,-1.79,1.60),(-.57,-1.57,1.57),
                        (-.31,.10,1.26),(-.35,.12,1.33))
    else:
        transit=ease(f,cut,frame(38.12))
        passby.location=(-2.0+4.7*transit,3.88,2.56+.19*sin(transit*pi))
        key(passby,f,"location")
        aim_scan(light_scan,f,(-1.64+3.95*transit,3.79,3.30),(-1.1+3.9*transit,2.02,.02),1.03,.60)
        run=ease(f,cut+2,release)
        position=bowler_path(f)
        run_pose=(f-cut)/16
        run_weight=sin(pi*run)*.63+.20
        facing=Euler((0,0,.45)).to_matrix()
        blegs=[]
        for index,sgn in enumerate((-1,1)):
            stride=(run_pose+index*.5)
            stance=stride%1
            contact=cut+(math.floor(stride)-index*.5)*16
            offset=facing@Vector((sgn*.123,-.065,.029))
            foot=bowler_path(contact+5)+offset
            if stance>=.58:
                progress=(stance-.58)/.42
                foot=foot.lerp(bowler_path(contact+21)+offset,ease(progress,0,1))
                foot.z+=.13*sin(pi*progress)*run_weight
            if f>=hit:
                foot=position+offset
            blegs.append((facing.transposed()@(foot-position),(sgn*.12,-.15,.29)))
        wind=ease(f,release-15,release-7)
        bowl=ease(f,release-7,release)
        settle=ease(f,release,release+12)
        angle=-.59+2.85*wind-3.03*bowl+.79*settle
        tip=(.23,-.14-.24*sin(angle),.32+.30*cos(angle))
        pose(bowler,f,position,.45,.08+.18*bowl-.14*settle,
             [((-.19,-.18,.20+.12*sin(f*.42)),(-.24,-.09,.22)),(tip,(.23,-.10,.27))],
             "rest",(-.08,.06),blegs,bounce=.045*abs(sin(run_pose*tau))*sin(run*pi))
        load=ease(f,hit-24,hit-8)
        swing=ease(f,hit-8,hit+6)
        recover=ease(f,hit+6,hit+20)
        yaw=-.24-.58*load+1.20*swing-.23*recover
        root=Vector((.47+.16*swing,.11,.006))
        pivot=Vector((.50-.22*load+.19*swing,-.29,.81+.11*load+.16*swing))
        angle=.52-1.91*load+3.14*swing-.49*recover
        direction=Vector((sin(angle),.25*load,cos(angle))).normalized()
        aim_object(bat,f,pivot-direction*.15,pivot+direction*.41)
        elbows=[(-.211,-.13,.29),(.248,-.10,.26)]
        tilt=.08+.09*load-.12*swing
        hands=[(grip_target(pivot+direction*offset,root,yaw,tilt,elbow),elbow)
               for elbow,offset in zip(elbows,(-.023,.035))]
        pose(batter,f,root,yaw,tilt,hands,"rest",(-.09,.15-.27*swing))
        cheer=ease(f,hit,hit+6)-.35*ease(f,hit+9,hit+23)
        clap=.5+.5*cos((f-hit)*.68)
        pose(watcher,f,(-.76,1.11,0),.25,.055,
             [((-.21+.15*clap*cheer,-.20,.20+.29*cheer),(-.23,-.08,.32)),
              ((.21-.15*clap*cheer,-.22,.20+.29*cheer),(.22,-.075,.32))],
             "rest" if f<hit else "EE",(-.07*cheer,.18))
        contact_swing=ease(hit,hit-8,hit+6)
        contact_angle=.52-1.91+3.14*contact_swing
        contact_axis=Vector((sin(contact_angle),.25,cos(contact_angle))).normalized()
        strike=Vector((.28+.19*contact_swing,-.29,.92+.16*contact_swing))+contact_axis*.21
        u=max(0,min(1,(f-release)/(hit-release)))
        if f<hit:
            ball.location=Vector((.12,-.61,1.10)).lerp(strike,u)+Vector((0,0,-.51*sin(pi*u)))
        else:
            u=min(1,(f-hit)/32)
            ball.location=strike+Vector((1.04*u,.17*u,1.46*u-.34*u*u))
        ball.rotation_euler.y=.48*(f-release)
        ball.hide_render=ball.hide_viewport=f<release
        key(ball,f,"location","rotation_euler","hide_render","hide_viewport")
        spark_at(impact_fx,f,strike+Vector((0,-.065,0)),float(hit<=f<hit+5)*(1+.06*max(0,f-hit)))
        pop=ease(f,shutter,shutter+6)-ease(f,shutter+15,shutter+20)
        photo.location=(0,-.04,-1.55)
        photo.rotation_euler=(-pi/2,0,-.13+.055*pop)
        photo.scale=(.0001+.68*pop,)*3
        key(photo,f,"location","rotation_euler","scale")
        if f<bat_cut:
            camera_move(cam,f,field,cut,bat_cut-1,(-1.29,-2.60,1.61),(-1.06,-2.33,1.58),
                        (-.31,.61,1.10),(-.16,.36,1.13))
        else:
            camera_move(cam,f,field,bat_cut,shutter-1,(1.16,-2.25,1.66),(.98,-2.12,1.53),
                        (.19,.31,1.22),(.25,.28,1.29))

finish(s,3,[kalam,engineer,second,bowler,batter,watcher],[(t,1,cut-1),(field,cut,s.frame_end)],
       [1,wide2,macro,back,cut,bat_cut],
       [1,wide2+7,macro,macro+12,back+9,cut+5,release,bat_cut+10,hit,hit+5,shutter+9,s.frame_end])
