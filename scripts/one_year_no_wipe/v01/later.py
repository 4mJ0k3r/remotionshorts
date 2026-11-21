"""Baked motion for the seven scenes after the classroom."""
import json
import math
from random import Random

import bpy
from mathutils import Euler, Vector

from build import camera_action, graphic, overlay, palette, switch
from cast import CHAIR, REST, STAND, contact_arm, figure, key, pose
from finale_sets import DOGS, avalanche, bedroom, dog, tp_roll, underwear
from native import ENDS, NAMES
from sets import bathroom, box, line, text
from worlds import bus, disco_ball, flower, germ, micro, mushroom, street, vapor
import ricks_v2_kit as k


def move(obj,f,xyz,rotation=None,scale=None):
    obj.location=xyz
    key(obj,f,"location")
    if rotation is not None:
        obj.rotation_euler=rotation
        key(obj,f,"rotation_euler")
    if scale is not None:
        obj.scale=(scale,)*3 if isinstance(scale,(int,float)) else scale
        key(obj,f,"scale")


def ease(t,a,b):
    return k.look.ease5((t-a)/(b-a))


def curve(t,p,q,a,b):
    return Vector(p).lerp(Vector(q),ease(t,a,b))


def label(c,cam,m,title,width=.95,font=.111,fill="purple",height=.151):
    return overlay(c,cam,m,title,width,height,font,fill)


def show(obj,f,cam,t,a,b,x=0,y=.66,angle=0,plane=.70):
    depth=max(.54,min(2.6,cam.data.dof.focus_distance*plane))
    factor=depth/1.62
    size=max(.0001,factor*ease(t,a,a+.135)*(1-ease(t,b-.16,b)))
    move(obj,f,(x*factor,y*factor,-depth),(0,0,angle*(1-ease(t,a,a+.3))),size)


def camera(cam,f,offset,start_frame,shot):
    a,b,p,q,at,bt,lens,*stops=shot
    a-=start_frame/30
    b-=start_frame/30
    camera_action(cam,f,offset,a,b,p,q,at,bt,lens,stop_number=stops[0] if stops else 2.8)


def stride(rig,f,t,path,*,mode="calm",yaw=math.pi/2,phase=0.):
    pos=Vector(path(t))
    cycle=.81
    legs=[]
    arms=[]
    lean=.020
    basis=Euler((0,0,-yaw)).to_matrix()
    side=Euler((0,0,yaw)).to_matrix()@Vector((1,0,0))
    for i,s in enumerate((-1,1)):
        clock=t-phase-i*cycle*.5
        strike=clock-clock%cycle+phase+i*cycle*.5
        swing=max(0.,min(1.,((t-strike)/cycle-.59)/.41))
        plant=Vector(path(strike+.23)).lerp(Vector(path(strike+cycle+.23)),k.look.ease5(swing))
        raise_foot=.084*math.sin(math.pi*swing)**1.2
        local=basis@(plant+side*(.104*s)-pos)
        legs.append(((local.x,local.y+.021,.028+raise_foot),
                     (.112*s,min(-.059,local.y*.40)-.45*raise_foot,.270+raise_foot*.43)))
        swing_arm=.095*math.cos(clock*math.tau/cycle)
        arms.append(((s*.181,-.14+swing_arm,.16), (s*.205,-.034+swing_arm*.50,.26)))
    rig.pose(f,pos,yaw,lean,arms,legs,mode,bounce=-.09+.018*math.sin(math.pi*(t-phase)/cycle)**2,
             head_tilt=.02,head_yaw=-.14)
    k.studio_pose_hands(rig,f)


def props_circles(c,cam,m):
    objects=[]
    for j,(heading,glyph,col) in enumerate((("WARM","I","red"),("WET","DROP","blue"),("DARK","☾","gold"))):
        unit=k.empty(heading+" pop-up circle",c,parent=cam)
        body=k.cylinder(heading+" enamel icon disk",c,(0,0,0),.163,.025,m[col],unit,length_segments=39)
        title=text(c,heading,(0,-.088,.018),.063,m["purple"] if col=="gold" else m["paper"],unit)
        title.rotation_euler.x=0
        if j==0:
            line(c,"Cream thermometer stem",[(-.016,-.004,.021),(-.016,.089,.021)],.014,m["paper"],unit)
            k.ball("Cream thermometer bulb",c,(-.016,-.011,.018),(.027,.027,.009),m["paper"],unit,15,8)
            for y in (.029,.055,.08):
                line(c,"Thermometer gradation",[(.012,y,.022),(.053,y,.022)],.004,m["paper"],unit)
        elif j==1:
            points=[(0,.112,.019),(-.066,.042,.019),(-.055,.008,.019),(0,-.015,.019),(.053,.008,.019),(.065,.04,.019)]
            k.mesh("Large white water droplet",c,points,[tuple(range(len(points)))],m["paper"],unit)
        else:
            points=[(.069*math.cos(a),.042+.069*math.sin(a),.019) for a in [math.pi*.22+i*math.pi*1.62/19 for i in range(20)]]
            points+= [(.036+.055*math.cos(a),.063+.057*math.sin(a),.019) for a in [math.pi*1.52-i*math.pi*1.1/16 for i in range(17)]]
            k.mesh("Golden moon crescent silhouette",c,points,[tuple(range(len(points)))],m["purple"],unit)
        objects.append(unit)
    return objects


def microscope_overlay(c,cam,m):
    root=k.empty("Circular microscope eyepiece reticle",c,parent=cam)
    # Circle, inset crosshair ticks and a readable magnification plate.
    line(c,"Round eyepiece outside border",[(.493*math.cos(i*math.tau/64),.068+.493*math.sin(i*math.tau/64),0) for i in range(65)],
         .011,m["purple"],root)
    line(c,"Round eyepiece cream inner border",[(.474*math.cos(i*math.tau/64),.068+.474*math.sin(i*math.tau/64),.011) for i in range(65)],
         .004,m["paper"],root)
    for i in range(12):
        a=i*math.tau/12
        line(c,"Microscope aperture scale tick",[(.439*math.cos(a),.068+.439*math.sin(a),.013),
             (.469*math.cos(a),.068+.469*math.sin(a),.013)],.007,m["paper"],root)
    plate=label(c,cam,m,"x 1000",.371,.110)
    return root,plate


def part2(s,cam,m,start,last):
    mc=stage(s,"Disco microscope",0)
    bc=stage(s,"City bus interior",32)
    fc=stage(s,"Sunlit florist",64)
    a,b,c=(i[0] for i in (mc,bc,fc))
    micro(a,m)
    germs=[germ(a,m,j) for j in range(9)]
    mirror=disco_ball(a,m)
    view,depth=microscope_overlay(a,cam,m)
    cards=[label(a,cam,m,n,.87,.113) for n in ("136,396","2,851,042","49,107,220","832,750,620",
           "9,860,500,714","90 BILLION!")]
    rolling=bus(b,m)
    passenger=figure(b,"Indignant bus passenger","student")
    traveler=figure(b,"Another retreating passenger","student")
    bus_boy=figure(b,"Red-Cap Boy hanging onto the strap","boy")
    day3=label(b,cam,m,"DAY 3",.39,.116,"paper",.182)
    stink=vapor(b,m)
    skatole=label(b,cam,m,"SKATOLE",.88,.151,"red",.275)
    next(obj for obj in skatole.children if obj.type=="FONT").location.y=-.024
    greek=text(b,"Greek: skato- = poop",(0,-.108,.018),.064,m["paper"],skatole)
    greek.rotation_euler.x=0
    street(c,m,florist=True)
    girl=figure(c,"Florist with red and white apron","florist")
    boy=figure(c,"Red-Cap walking past the flowers","boy")
    pots=[]
    for j in range(11):
        x=-1.56+j*.286
        y=(1.06 if j%3 else .66)
        z=(.54 if j%3 else .13)
        k.cylinder("Glazed sunny florist flower pot",c,(x,y,z-.077),.117,.146,
                   m[("orange","blue","wood2","gold")[j%4]],r2=.142,length_segments=16)
        pots.append(((x,y,z),flower(c,m,j)))
    sprig,_=flower(c,m,0)
    shop_scent=vapor(c,m,8)
    pink=k.emission("Tiny rosy flower aroma sparkle","#ff9bc6",1.65)
    sparkles=[k.ball("Floating pink perfume sparkle",c,(0,0,0),(.021,.020,.021),pink,segments=9,rings=6)
              for i in range(11)]
    shots=(
        (27.9,30.58,(.19,-3.13,1.59),(.17,-2.55,1.37),(0,.10,.64),(0,.16,.69),26),
        (30.58,33.62,(-1.30,-3.12,1.47),(-1.01,-2.79,1.40),(-.10,.20,.69),(.02,.26,.76),26),
        (33.62,37.30,(1.22,-3.34,1.53),(.88,-2.91,1.52),(.06,.24,.73),(.10,.34,.69),25),
        (37.30,39.20,(.71,-2.73,1.68),(.63,-2.54,1.66),(.33,.22,1.40),(.31,.25,1.46),25),
        (39.20,41.37,(-.77,-2.61,1.56),(-.82,-2.42,1.51),(.26,.22,1.21),(.22,.27,1.26),26),
        (41.37,44.68,(.55,-2.26,1.54),(.53,-2.11,1.55),(.43,.34,1.25),(.42,.39,1.26),26),
        (44.68,46.49,(-.93,-3.32,1.66),(-.59,-2.91,1.69),(.0,.68,1.41),(-.08,.69,1.44),25),
        (46.49,49.93,(-.85,-1.68,1.45),(-.69,-1.57,1.44),(-.51,.69,1.22),(-.43,.67,1.24),26),
        (49.93,52.02,(1.17,-2.48,1.56),(.90,-2.44,1.51),(.01,.48,1.16),(.20,.55,1.14),25),
        (52.02,last,(-.16,-2.55,1.57),(.21,-2.32,1.55),(.64,.42,1.21),(.79,.36,1.19),26),
    )
    def path(t):
        return (min(1.75,max(-2.28,-2.28+(t-48.8)*.86)),.071,0)
    for f in range(1,round((last-start/30)*30)+1):
        t=(start+f-1)/30
        i=shot_index(t,shots)
        camera(cam,f,(0,32,64)[0 if i<3 else 1 if i<6 else 2],start,shots[i])
        if i<3:
            descend=ease(t,30.85,31.77)
            move(mirror,f,(.06,.88,3.02-1.24*descend),(0,.092,.91*(t-29)))
            for j,g in enumerate(germs):
                row=j//5
                x=(j%5-2)*.53+.22*row
                wave=4.34*t+.69*j
                hop=.16*abs(math.sin(wave))**2*ease(t,30.45,31.33)
                move(g,f,(x+.070*math.sin(wave),.16+row*.55+.05*math.sin(wave*.5),.239+hop),
                     (0,.19*math.sin(wave),.29*math.sin(wave*.55)),(1+.04*math.sin(wave),1,1+.11*hop))
            show(view,f,cam,t,27.87,30.36,y=.022)
            show(depth,f,cam,t,27.89,32.12,y=-.62,plane=.43)
            spans=(30.66,31.25,31.67,32.08,32.51,32.82,36.77)
            for j,card in enumerate(cards):
                show(card,f,cam,t,spans[j],spans[j+1],y=.65,angle=.055)
        elif i<6:
            move(rolling,f,(0,-.67*(t-37.30),0))
            x=.72+.012*math.sin(t*5.2)
            face="sweat" if t>41.83 else "deadpan" if t>39.24 else "calm"
            grip=contact_arm((.773,.097,1.48),(x,.111,0),-.15,.12,(.228,-.083,.523),seat=False)
            pose(bus_boy,f,(x,.111,0),yaw=-.15,tilt=.12,arms=(REST[0],grip),mode=face,
                 sweat=.4 if face=="sweat" else None)
            squeeze=ease(t,38.87,39.27)
            far=ease(t,40.04,41.14)
            for j,rig in enumerate((passenger,traveler)):
                root=(-.69-.68*far,.25+j*.66+.60*far,0)
                raised=((.015,-.234,.627),(.171,-.164,.413))
                hand=(Vector(REST[1][0]).lerp(Vector(raised[0]),squeeze),raised[1])
                pose(rig,f,root,yaw=.31-.34*far,tilt=-.11*squeeze,arms=(REST[0],hand),mode="frown" if squeeze>.4 else "side_eye")
            move(stink,f,(.84,.29,.11+.14*math.sin((t-37.3)*4)),(0,.18*math.sin(t*3.1),0),
                 max(.0001,ease(t,38.55,39.27)))
            show(day3,f,cam,t,37.27,39.68,x=-.342,y=.887,plane=.43)
            show(skatole,f,cam,t,41.36,44.46,y=.50,angle=-.083,plane=.43)
        else:
            loc=(-.51,.66,0)
            gag=ease(t,49.54,50.17)
            flower_pos=curve(t,(-.45,.507,.812),(-.39,.480,.705),49.2,50.17)
            hand=contact_arm(flower_pos,loc,-.31,.06,(.19,-.14,.38),seat=False)
            pinch=contact_arm((-.556,.465,1.146),loc,-.31,.06,(-.19,-.13,.43),seat=False)
            arm=(Vector(REST[0][0]).lerp(Vector(pinch[0]),gag),pinch[1])
            pose(girl,f,loc,yaw=-.31,tilt=.06,arms=(arm,hand),mode="sweat" if gag>.4 else "happy",head=(.093,-.14))
            move(sprig,f,flower_pos,(0,-.19-.62*gag,.012),.69)
            stride(boy,f,t,path,mode="deadpan")
            for j,(pos,(obj,sad)) in enumerate(pots):
                wilt=ease(t,49.97+j*.17,50.57+j*.17)
                move(obj,f,pos,(.38*wilt,(-1)**j*.86*wilt,-.04),(1,1,1-.33*wilt))
                sad.scale=(max(.0001,wilt),)*3
                key(sad,f,"scale")
            for j,obj in enumerate(sparkles):
                z=(.22*(t-46.5)+j*.067)% .55
                move(obj,f,(-.40+.115*math.sin(j*2+t),.36,.93+z),scale=max(.0001,(1-gag)*ease(t,45.0,46.5)))
            move(shop_scent,f,(path(t)[0]-.32,.18,.18),scale=max(.0001,gag*.71))
    return shots,(mc,bc,fc),(bus_boy,passenger,traveler,girl,boy),(
        28.4,29.7,31.36,32.92,35.86,37.66,39.30,41.85,44.91,47.04,50.79,52.98)


def part3(s,cam,m,start,last):
    fc=stage(s,"Mushroom settlement",0)
    dc=stage(s,"Sunny storefront dog parade",32)
    a,b=fc[0],dc[0]
    micro(a,m,False)
    fungal=[mushroom(a,m,j) for j in range(5)]
    bugs=[germ(a,m,j+1) for j in range(3)]
    mag,level=microscope_overlay(a,cam,m)
    month=label(a,cam,m,"MONTH 1",.51,.109,"paper",.18)
    icons=props_circles(a,cam,m)
    sign=k.empty("Wooden home sign plant",a,(.73,.54,0))
    box(a,"Raised wooden home sign post",(0,0,.45),(.084,.072,.91),m["wood"],sign,bevel=.008)
    box(a,"Wooden sweet-home sign panel",(0,-.024,.81),(.89,.083,.31),m["wood2"],sign,bevel=.021)
    text(a,"HOME SWEET HOME",(0,-.074,.752),.071,m["purple"],sign)
    rng=Random(136)
    confetti=[]
    for j in range(48):
        obj=box(a,"Falling rectangular party confetti",(0,0,0),(.042,.018,.107),
                m[("orange","blue","gold","paper","red")[j%5]])
        confetti.append((obj,rng.uniform(-1.66,1.65),rng.uniform(-.18,1.32),rng.uniform(0,.90)))
    street(b,m,True)
    hero=figure(b,"Red-Cap Boy leading the dog parade","boy")
    pets=[dog(b,m,j) for j in range(5)]
    tag=label(b,cam,m,"MONTH 6",.51,.109,"paper",.18)
    banners=[]
    for name in DOGS:
        badge=label(b,cam,m,"",1.04,.081,"paper",.20)
        line1=text(b,name,(0,.024,.021),.089,m["purple"],badge)
        line2=text(b,"started following you",(0,-.061,.021),.063,m["purple"],badge)
        line1.rotation_euler.x=line2.rotation_euler.x=0
        banners.append(badge)
    shots=(
        (start/30,56.39,(.10,-2.90,1.38),(-.29,-2.49,1.25),(-.07,.41,.58),(-.06,.42,.61),26),
        (56.39,59.80,(-1.00,-2.64,1.33),(-.70,-2.46,1.23),(-.46,.25,.52),(-.16,.27,.58),26),
        (59.8,62.57,(.49,-2.74,1.40),(.43,-2.62,1.35),(-.02,.43,.57),(.0,.44,.58),26),
        (62.57,65,(.94,-2.68,1.43),(.80,-2.48,1.36),(.26,.42,.67),(.27,.43,.69),26),
        (65,67.14,(-.79,-3.27,1.61),(.04,-3.08,1.58),(-1.65,.61,.91),(-.83,.61,.92),25),
        (67.14,69.00,(.20,-2.83,1.49),(.86,-2.79,1.49),(-.81,.42,.87),(-.12,.42,.88),26),
        (69.00,71.19,(.91,-2.77,1.55),(1.77,-2.79,1.53),(-.09,.48,.90),(.77,.50,.91),25),
        (71.19,last,(1.84,-3.11,1.54),(2.84,-3.17,1.57),(.79,.56,.85),(1.79,.59,.88),25),
    )
    def path(t):
        return (-.39+.39*(t-66.10),.042,0)
    for f in range(1,round((last-start/30)*30)+1):
        t=(start+f-1)/30
        i=shot_index(t,shots)
        camera(cam,f,0 if i<4 else 32,start,shots[i])
        if i<4:
            for j,(fun,feet) in enumerate(fungal):
                drift=ease(t,55.39+j*.16,58.53+j*.18)
                step=math.sin(t*8.42+j*.76)
                move(fun,f,(-2.39+3.14*drift-j*.34,.17+j*.25,.154+.058*abs(step)*(1-drift)),
                     (0,.13*step*(1-drift),.39*(1-drift)-.12*drift))
                for q,foot in enumerate(feet):
                    foot.rotation_euler.x=.32*step*(-1)**q*(1-drift)
                    key(foot,f,"rotation_euler")
            for j,bug in enumerate(bugs):
                move(bug,f,((j-1)*.86,.78+j*.24,.235+.043*math.sin(t*8+j)**2),(0,.13*math.sin(t*5+j),0),.73)
            plant=ease(t,62.60,62.95)
            move(sign,f,(.73,.54,-1.22+1.22*plant),(0,.28*(1-plant),0))
            for obj,x,y,z in confetti:
                u=t-62.78-z*.27
                move(obj,f,(x+.16*math.sin(u*4+x),y,max(.022,2.1+z-1.47*max(0,u))),
                     (u*4+x,u*5+y,u*3+z),.99 if u>0 else .0001)
            show(mag,f,cam,t,53.59,55.37,y=.0)
            show(level,f,cam,t,53.6,55.99,y=-.62,plane=.43)
            show(month,f,cam,t,53.57,55.94,x=-.32,y=.913)
            for j,obj in enumerate(icons):
                show(obj,f,cam,t,(60.36,61.05,61.85)[j],64.86,x=(j-1)*.386,y=.65,angle=.075*(-1)**j)
        else:
            stride(hero,f,t,path,mode="calm")
            x=path(t)[0]
            for j,(root,head,legs,tail) in enumerate(pets):
                step=math.tau*(t*1.42-j*.126)
                yaw=math.pi*.37+.05*math.sin(step)
                move(root,f,(x-.47-j*.377,.29+(j%2)*.59+.035*j,0),(0,0,yaw))
                head.rotation_euler.x=-.12+.17*math.sin(step*.47)
                tail.rotation_euler.z=.49*math.sin(step*1.49)
                key(head,f,"rotation_euler")
                key(tail,f,"rotation_euler")
                for z,leg in enumerate(legs):
                    cycle=(t*1.42-j*.126+.5*(z%2^z//2))%1
                    lift=max(0,(cycle-.57)/.43)
                    along=.39/1.42*(.272-cycle+k.look.ease5(lift))
                    travel=Euler((0,0,-yaw)).to_matrix()@Vector((along,0,0))
                    rise=.052*math.sin(math.pi*lift)
                    ankle=travel+Vector((0,-.029,-leg.location.z+.016+rise))
                    stem=next(obj for obj in leg.children if obj.type=="CURVE")
                    k.tube_pose(stem,[(0,0,0),(.50*ankle.x,.43*ankle.y-.041,.54*ankle.z),ankle],f)
                    for paw in leg.children:
                        if paw.type=="MESH":
                            pom="pom" in paw.name
                            paw.location=ankle+Vector((0,.012 if pom else -.017,.033 if pom else 0))
                            key(paw,f,"location")
            show(tag,f,cam,t,64.96,67.24,x=-.323,y=.91)
            for j,badge in enumerate(banners):
                show(badge,f,cam,t,68.98+j*.68,69.65+j*.68,y=.786,angle=.044*(-1)**j)
    return shots,(fc,dc),(hero,),(
        54.16,55.95,57.12,58.62,60.63,62.18,63.42,64.49,65.55,67.40,70.14,73.35)


def part4(s,cam,m,start,last):
    rc=stage(s,"Bedroom and escaping laundry",0)
    bc=stage(s,"Bathroom avalanche",32)
    c,b=rc[0],bc[0]
    bedroom(c,m)
    sitter=figure(c,"Dejected Red-Cap on the bed","boy")
    garment=underwear(c,m)
    mist=vapor(c,m,8)
    day=label(c,cam,m,"DAY 365",.53,.107,"paper",.181)
    bathroom(b,m)
    doors=avalanche(b,m)
    hero=figure(b,"Red-Cap Boy facing the cupboard","boy")
    last_day=label(b,cam,m,"DAY 365",.53,.107,"paper",.18)
    rolls=[tp_roll(b,m,j) for j in range(28)]
    rng=Random(244)
    landing=[]
    for j in range(len(rolls)):
        x=.713+(j%3)*.209+.011*math.sin(j)
        y=.392+((j//3)%3)*.169
        z=.349+(.336 if j>=14 else 0)+.11*(j%2)
        landing.append(((x,y,z),(.37+.98*(j%7)/6,-.49-.62*(j//7)/3,.093),
                        rng.uniform(.08,.46),rng.uniform(-.9,.9)))
    shots=(
        (start/30,76.32,(.49,-2.83,1.51),(.37,-2.44,1.48),(.04,.51,1.09),(.056,.46,1.07),26),
        (76.32,78.16,(-1.33,-1.72,1.31),(-1.27,-1.64,1.30),(-.46,.20,1.09),(-.42,.18,1.09),27),
        (78.16,79.61,(1.17,-1.32,.931),(1.13,-1.22,.90),(.79,.017,.445),(.78,.02,.470),48,3.8),
        (79.61,81.03,(1.41,-2.67,1.23),(1.80,-2.58,1.14),(.93,-.02,.58),(1.40,.32,.56),26),
        (81.03,81.68,(.15,-1.47,1.27),(.072,-1.37,1.22),(.83,.28,.73),(.87,.29,.73),25),
        (81.68,82.20,(-.295,-2.43,1.44),(-.24,-2.33,1.46),(.63,.14,1.01),(.62,.13,.94),25),
        (82.20,last,(-.24,-2.33,1.46),(-.24,-2.33,1.46),(.62,.13,.94),(.62,.13,.94),25),
    )
    sit_loc=(-.446,-.149,0)
    sit_legs=tuple(((s*.122,-.173,.027),(s*.13,-.21,.413)) for s in (-1,1))
    for f in range(1,round((last-start/30)*30)+1):
        t=(start+f-1)/30
        i=shot_index(t,shots)
        camera(cam,f,0 if i<4 else 32,start,shots[i])
        if i<4:
            glance=ease(t,77.20,77.68)-ease(t,80.18,80.82)
            pose(sitter,f,sit_loc,yaw=.134,tilt=.15,legs=sit_legs,seat=True,
                 mode="wince" if glance>.39 else "deadpan",head=(.22-.12*glance,.238*glance))
            move(mist,f,(.80,.044,.40+.048*math.sin(t*6)),scale=.83)
            wind=ease(t,79.28,79.53)
            fly=max(0.,min(1.,(t-79.59)/.42))
            dash=ease(t,79.99,81.02)
            x=.79+.20*fly+.99*dash
            z=(.42+.19*wind)*(1-fly)+.127*fly+.40*math.sin(math.pi*fly)+.061*abs(math.sin(66*t))*dash
            move(garment,f,(x,.02-.52*fly+1.52*dash,z),
                 (-.24+.28*math.sin(math.pi*fly),.20*math.sin(40*t)*dash, -.62*dash),.83)
            show(day,f,cam,t,74.15,76.28,x=-.318,y=.92)
        else:
            pull=ease(t,81.04,81.42)
            release=ease(t,81.42,81.75)
            yaw=1.73*(1-release)-.19*release
            loc=(.33-.196*release,-.22-.061*release,0)
            arms=list(REST)
            for j,door in enumerate(doors):
                sign=(-1,1)[j]
                door.rotation_euler.z=sign*1.66*pull
                key(door,f,"rotation_euler")
                handle=door.location+Euler((0,0,door.rotation_euler.z)).to_matrix()@Vector((-sign*.286,-.078,.037))
                aim=contact_arm(handle,loc,yaw,.055,(sign*.216,-.133,.32),seat=False)
                arms[j]=(Vector(REST[j][0]).lerp(Vector(aim[0]),1-release),aim[1])
            pose(hero,f,loc,yaw=yaw,tilt=.055*(1-release),arms=arms,mode="deadpan",
                 head=(.06*(1-release),-.16*(1-release)))
            for j,(obj,(p,q,delay,spin)) in enumerate(zip(rolls,landing)):
                u=max(0.,min(1.,(t-81.19-delay)/(.61+.16*(j%3)/2)))
                fly=Vector(p).lerp(Vector(q),k.look.ease5(u))
                fly.z+=.29*math.sin(math.pi*u)*(1 if j%3==0 else .71)
                fly.z+=.023*abs(math.sin(u*math.tau*2))*math.sin(math.pi*u)
                move(obj,f,fly,(math.pi*.50+5.1*u,spin*5*u,(.1*j+2.4*u)))
            show(last_day,f,cam,t,81.01,82.80,x=-.318,y=.92)
    return shots,(rc,bc),(sitter,hero),(
        74.27,74.80,75.82,76.84,77.70,78.48,79.20,79.84,80.56,81.24,81.91,82.49)


def shot_index(t,shots):
    return max(i for i,shot in enumerate(shots) if round(t*30)>=round(shot[0]*30))


def stage(scene,name,offset):
    layer=bpy.data.collections.new(name)
    scene.collection.children.link(layer)
    return layer,offset


def build(number,output):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    start,stop=ENDS[number-1:number+1]
    length=stop-start
    k.configure_ricks_scene(scene,frame_end=length,samples=5)
    scene.world=bpy.data.worlds.new("Warm cool painterly room bounce")
    scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value=k.look.rgba("#9f9cbe")
    bg.inputs[1].default_value=.44
    cam=bpy.data.objects.new("Story camera",bpy.data.cameras.new("Vertical delivery lens"))
    scene.collection.objects.link(cam)
    scene.camera=cam
    k.setup_ricks_compositor(scene,camera=cam)
    m=palette()
    shots,groups,actors,samples=(part2,part3,part4)[number-2](scene,cam,m,start,stop/30)
    subdivisions={2:(0,3,6),3:(0,4),4:(0,4)}[number]
    boundaries=[round(shots[i][0]*30)-start for i in subdivisions]+[length]
    for (col,x),a,b in zip(groups,boundaries,boundaries[1:]):
        switch(col,a+1,b,x)
    for actor in actors:
        actor.finish_bake()
    for action in bpy.data.actions:
        for fcurve in action.fcurves:
            mode="CONSTANT" if fcurve.data_path=="lens" or "hide_" in fcurve.data_path else "LINEAR"
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation=mode
    cuts=[round(shot[0]*30)-start for shot in shots[1:] if not (number==4 and shot[0]==82.20)]
    for i,cut in enumerate(cuts):
        scene.timeline_markers.new(f"Shot {i+2}",frame=cut+1)
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output/(NAMES[number-1]+".blend")))
    edges=[0,*cuts,length]
    (output/"shots.json").write_text(json.dumps({"cuts":cuts,
        "shots":[{"id":i,"a":a,"b":b} for i,(a,b) in enumerate(zip(edges,edges[1:]),1)],
        "proof_frames":[round(sample*30)-start+1 for sample in samples]},indent=2))
