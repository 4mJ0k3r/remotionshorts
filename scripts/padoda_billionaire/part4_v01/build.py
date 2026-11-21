"""Twilight power plant, slapstick dinner and a stylized national power map."""
import json
from pathlib import Path
from random import Random
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from sequence_tools import *

OUT=ROOT/"renders/padoda_billionaire/part4_v01"
END=384
CAL=(14,135,171,212,269,304,330,377)
BENCH=(*CAL,1,156,286,384)

def exterior(c):
    concrete=k.texture("Painterly cooling tower concrete",("#414c62","#6a6d78","#888486"),"plaster",(.70,.85))
    iron=k.surface("Transmission pylon gunmetal","#3c5270",.76)
    navy=k.surface("Dark twilight factory road","#172542",.78)
    amb=k.emission("Golden windows and factory sign","#ffd476",2.15)
    lime=k.emission("Lime tower rim glow","#a6f364",1.48)
    box("Wide twilight ground",c,(0,0,-.16),(38,43,.31),navy)
    for j in range(9):
        box("Painted approach lane mark",c,(0,-9.4+j*.94,.002),(.085,.51,.012),iron,.013)
    for x in (-2.62,2.62):
        for y in (-4.8,-2.9,-1.0):
            k.cylinder("Approach bollard",c,(x,y,.26),.071,.52,iron,length_segments=14)
            k.cylinder("Approach amber marker",c,(x,y,.51),.054,.065,amb,length_segments=12)
    box("Single illuminated factory hall",c,(0,1.84,1.17),(4.45,3.38,2.36),concrete,.073,True)
    box("Factory fascia",c,(0,.105,1.90),(4.23,.12,.54),navy,.046,True)
    text(c,"PADODA POWER PLANT",(0,.017,1.81),.283,amb)
    for i in range(8):
        x=-1.89+.54*i
        box("Luminous control hall window",c,(x,.12,1.13),(.38,.13,.74),amb,.021,True)
        box("Window steel mullion",c,(x,.035,1.13),(.033,.025,.74),iron,.006)
    for x in (-1.83,1.83):
        verts=[]
        for j in range(13):
            z=j*.265
            r=.66+.29*((z-1.95)/1.95)**2
            for n in range(32):
                a=math.tau*n/32
                verts.append((x+r*math.cos(a),3.2+r*math.sin(a),1.3+z))
        faces=[(j*32+n,j*32+(n+1)%32,(j+1)*32+(n+1)%32,(j+1)*32+n)
               for j in range(12) for n in range(32)]
        tower=k.mesh("Hyperbolic cooling tower shell",c,verts,faces,concrete,smoothing=True)
        k.apply_prop_ink(tower,c)
        for z,material in ((4.49,lime),(4.40,iron),(2.07,iron)):
            r=.66+.29*((z-3.25)/1.95)**2
            k.tube("Cooling tower rim band",c,[(x+r*math.cos(j*math.tau/48),3.2+r*math.sin(j*math.tau/48),z)
                  for j in range(49)],.043,material)
    for i,(x,y) in enumerate(((-3.8,2.3),(3.7,3.1),(4.4,8.5),(-5.2,10))):
        h=3.98-i*.23
        for sign in (-1,1):
            rod("Steel transmission tower leg",c,(x+sign*.51,y,0),(x+sign*.13,y,h),.044,.029,iron,8)
        for j in range(6):
            z=.55+j*.54
            rod("Pylon lattice brace",c,(x-.39+j*.042,y,z),(x+.37-j*.042,y,z+.48),.023,.023,iron,8)
        for j in range(3):
            z=h-.18-j*.40
            rod("Pylon conductor crossarm",c,(x-.65,y,z),(x+.65,y,z),.032,.03,iron,8)
            k.tube("Electrical transmission line",c,[(x,y,z),(x+.51,y+3,z-.36),(x+.89,y+7,z-.18)],.013,iron)
    rng=Random(88)
    for i in range(25):
        x=-13+i*1.12;y=13+rng.random()*3;h=.45+rng.random()*2.55
        box("Distant indigo city silhouette",c,(x,y,h*.5),(rng.uniform(.62,.93),1.0,h),iron,.023)
        for z in (.26,.61,.95):
            if z<h:box("Distant office window",c,(x,y-.513,z),(.32,.016,.046),amb,.005)
    k.make_ricks_light("Twilight sky",c,(-5,-6,8),(0,1,2),"#97afff",2100,8)
    k.make_ricks_light("Factory warm facade fill",c,(4,-3,6),(0,1,1.2),"#ffc287",820,4)

def food(c,place,kind,material,herb,butter,parent=None):
    x,y,z=place
    obj=k.ball("Layered round mooli paratha" if kind==0 else "Puffed bhatura bread",c,place,
              (.127,.137,.027 if kind==0 else .069),material,parent,segments=14,rings=8)
    for j in range(5):
        a=j*2.4
        k.ball("Toasty blister and herb fleck",c,(x+.075*math.cos(a),y+.062*math.sin(a),z+.025+.019*kind),
               (.016,.012,.005),herb,parent,segments=8,rings=5)
    if kind==0:box("Melting cube of butter",c,(x,y,z+.032),(.046,.040,.023),butter,.008,parent=parent)
    return obj

def console(c):
    steel,green,gold=(k.surface("Steel console and thalis","#667c92",.70,.35),
        k.emission("Control indicator green","#9eef62",1.95),k.emission("Cream gauge ink","#ffe2a9",1.23))
    dark=k.surface("Dark industrial blue console","#24374e",.75)
    teal=k.emission("Industrial cyan monitors","#488fb2",1.15)
    black=k.emission("Printed control ink","#182133")
    toast=k.surface("Golden toasted flatbread","#ca7e29",.82,glow=.06)
    bread=k.surface("Puffy golden fried dough","#dda64b",.81,glow=.045)
    char=k.surface("Brown blisters and green spice","#6f3821",.82)
    butter=k.surface("Warm melting butter","#ffd87b",.67)
    box("Gauge and console enamel steel",c,(.68,.74,.63),(1.70,.65,1.21),dark,.065,True)
    box("Dining shelf at console top",c,(.86,.44,.84),(1.82,.55,.075),steel,.035,True)
    for i,x in enumerate((.13,.65,1.18)):
        box("Control monitor frame",c,(x,.61,1.36),(.47,.14,.32),steel,.038,True)
        box("Dim green and cyan monitor",c,(x,.523,1.36),(.39,.035,.24),teal,.017)
        k.tube("Equipment signal trace",c,[(x-.16+j*.036,.5,1.33+.029*math.sin(j*1.6+i)) for j in range(10)],.006,green)
    center=vec((.77,.165,1.06))
    disk("Max power gauge bevel",c,center,.286,.135,steel)
    disk("Pale power gauge face",c,center+vec((0,-.084,0)),.251,.043,gold)
    for j in range(15):
        a=math.radians(-134+j*19)
        tick=box("Power meter tick",c,center+vec((.215*math.sin(a),-.115,.215*math.cos(a))),
                 (.012,.010,.031),black,.002)
        tick.rotation_euler.y=a
    text(c,"100%",center+vec((0,-.115,-.124)),.076,black)
    text(c,"MAX POWER",center+vec((0,-.112,-.174)),.044,black)
    needle=k.empty("Power meter slamming needle",c,center+vec((0,-.123,0)))
    red=k.emission("Red needle enamel","#e74146",1.04)
    k.mesh("Long arrow needle",c,[(-.014,0,-.021),(.014,0,-.022),(.007,0,.154),(0,0,.204)],[(0,1,2,3)],red,needle)
    disk("Needle rivet",c,(0,-.011,0),.024,.018,black,needle)
    for i,x in enumerate((-.04,.42,1.20,1.55)):
        disk("Round steel dinner thali",c,(x,.257,.89),.168,.017,steel).rotation_euler.x=0
        pile=(4,3,4,3)[i]
        for j in range(pile):
            food(c,(x+.024*math.sin(j),.248+.022*math.cos(j),.913+j*.045),i%2,
                 bread if i%2 else toast,char,butter)
    held=[]
    for i in range(2):
        obj=k.empty("Food gripped by Hero",c)
        food(c,(0,0,0),i,bread if i else toast,char,butter,obj)
        held.append(obj)
    steam=[k.ball("Translucent curled steam",c,(0,0,0),(.036,.024,.082),
            transparent("Steam over hot thali","#eac79d",.22,1.02),segments=10,rings=7) for _ in range(5)]
    return needle,held,steam

def map_stage(c):
    land=k.surface("Deep blue raised India silhouette","#233753",.80)
    ocean=k.texture("Indigo night map base",("#121938","#16274e","#2b3659"),"plaster")
    west=k.emission("Golden electrical grid","#ffd263",2.45)
    green=k.emission("Lime power line tracer","#a7ff69",1.9)
    box("Dark blue map ocean",c,(0,0,-.11),(11,10,.21),ocean)
    outline=[(-.75,1.59),(-.49,1.99),(-.25,2.03),(-.09,2.16),(.16,2.01),(.53,1.76),(.46,1.53),
        (.75,1.27),(1.04,1.12),(1.30,1.30),(1.54,1.63),(1.83,1.48),(1.72,1.22),(1.61,.94),(1.45,1.03),
        (1.28,.80),(1.05,.65),(.83,.30),(.65,-.04),(.34,-.24),(.22,-.55),(.10,-.99),(-.13,-1.51),
        (-.37,-1.86),(-.54,-1.51),(-.77,-1.18),(-.85,-.83),(-.99,-.48),(-1.14,-.28),(-1.09,-.09),
        (-1.41,.05),(-1.56,.27),(-1.35,.48),(-1.16,.62),(-1.14,.98),(-.89,1.12)]
    count=len(outline)
    p=[(x,y,z) for z in (.03,.15) for x,y in outline]
    faces=[tuple(reversed(range(count))),tuple(range(count,count*2))]
    faces.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    obj=k.mesh("Stylized raised India landmass",c,p,faces,land)
    mod=obj.modifiers.new("Soft map shore edges","BEVEL");mod.width=.034;mod.segments=2
    obj.modifiers.new("Weighted map normals","WEIGHTED_NORMAL")
    cities=[(-.44,1.02),(-.72,.56),(-1.15,.33),(-.85,-.26),(-.45,-.68),(-.34,-1.16),
        (-.43,-1.52),(.29,.03),(.77,.59),(.26,.83),(-.05,.49),(-.15,-.28),(.62,.92),(1.36,1.18)]
    hub=vec((-.49,.54,.183))
    paths=[];clusters=[]
    rng=Random(109)
    for j,(x,y) in enumerate(cities):
        dest=vec((x,y,.165))
        mid=hub.lerp(dest,.53)+vec((.04*math.sin(j),.096*math.cos(j),.07))
        paths.append(k.tube("Lit export path",c,[hub,mid,dest],.012,green if j%3==0 else west))
        points=[]
        for i in range(6):
            pt=dest+vec((rng.uniform(-.07,.07),rng.uniform(-.07,.07),rng.uniform(0,.015)))
            radius=rng.uniform(.008,.028)
            points.append(k.ball("City cluster point",c,pt,(radius,radius,radius*.66),west,segments=8,rings=5))
        clusters.append(points)
    k.cylinder("Power plant location light",c,hub,.077,.049,green,length_segments=18)
    k.make_ricks_light("Indigo coast fill",c,(-3,-2,6),(0,0,0),"#7598ff",560,4)
    return paths,clusters

def build():
    s,cam=scene_setup(END,((1,0),(END,0)))
    ext=collection(s,"Plant exterior")
    ctrl=collection(s,"Dining control booth",25)
    india=collection(s,"Night grid of India",50)
    exterior(ext[0])
    c=ctrl[0]
    wood,brass,dark=room(c)
    needle,meal,steam=console(c)
    bench=box("Inventor's grounded stool",c,(-.65,.12,.305),(.38,.42,.6),wood,.055,True)
    rig=actor(c)
    bib=k.surface("Cream chef bib","#f2ede2",.82)
    k.mesh("Painted chef bib",c,[(-.087,-.087,.37),(.086,-.087,.37),(.095,-.103,.19),(-.087,-.103,.19)],
           [(0,1,2,3)],bib,rig.body)
    paths,clusters=map_stage(india[0])
    sparks4=sparks(c,10)
    distances={}
    last=None
    for f in range(1,END+1):
        if f<=156:
            t=step(f,1,156)
            p=vec((-4.94,-10.4,1.37)).lerp(vec((-.13,-5.84,3.32)),t)
            aim=vec((.20,2.76,2.60)).lerp(vec((.12,1.08,2.39)),t)
            camera_pose(cam,ext,f,p,aim,38-4*t)
        elif f<=308:
            root=vec((-.68,.024,.155))
            yaw=.27
            tilt=.18+.08*math.sin(f*.27)
            bounce=-.19
            arms=idle()
            beat=(f-158)%24
            sign=1 if ((f-158)//24)%2 else -1
            bring=step(beat,4,12)*(1-step(beat,15,20))
            tray=vec((-.07,.204,.985+.062*(sign==1)))
            mouth=vec((-.622,-.283,1.124))
            pos=tray.lerp(mouth,bring)
            elbow=vec((sign*.28,-.08,.312))
            arms[(sign+1)//2]=(contact(pos-vec((0,.014,.041)),root,yaw,tilt,bounce,elbow),elbow)
            if f in (169,217,266):
                distances[str(f)]=measure_contact(arms[(sign+1)//2],root,yaw,tilt,bounce,pos-vec((0,.014,.041)))
            for i,obj in enumerate(meal):
                obj.location=pos;obj.rotation_euler=(.27*bring,.2*bring,sign*.14)
                key(obj,f,"location","rotation_euler")
                for child in obj.children:visible(child,(i==0)==(sign==-1) and 5<=beat<=13 and f<287,f)
            face="shock" if 9<=beat<=13 else "strain" if 14<=beat<=18 else "smug"
            legs=[((d*.152,-.205,-.125),(d*.17,-.43,.17)) for d in (-1,1)]
            rig.pose(f,root,yaw,tilt,arms,legs,face if last!=face else None,bounce=bounce,
                     head_tilt=-.17*bring,head_yaw=.22*bring,leg_lengths=standing)
            last=face
            spin=step(f,290,301)
            needle.rotation_euler.y=-1.77+3.78*spin+.12*spin*math.sin(f*1.66)
            key(needle,f,"rotation_euler")
            scatter(sparks4,f,(.78,.012,1.14),step(f,297,308),1.15)
            for i,obj in enumerate(steam):
                age=((f+11*i)%45)/45
                obj.location=(.07+.23*i+.026*math.sin(f*.25+i),.28,1.06+.42*age)
                obj.scale=(.46+.38*age,.7,.6+.25*age)
                key(obj,f,"location","scale")
            if f<=287:
                t=step(f,157,225)
                p=vec((1.35,-3.51,1.40)).lerp(vec((1.19,-3.32,1.24)),t)
                camera_pose(cam,ctrl,f,p,(-.24,.27,1.04),34,(-.43,.08,1.19))
            else:
                shake=.021*spin*math.sin(f*2.7)
                camera_pose(cam,ctrl,f,(.77+shake,-1.67,1.10),(.77,.047,1.06),57)
        else:
            t=step(f,309,END-8)
            p=vec((-.47,-3.32,4.53)).lerp(vec((1.39,-2.95,5.31)),t)
            camera_pose(cam,india,f,p,(.07,.24,.09),32,(0,.26,.12))
            for j,(route,city) in enumerate(zip(paths,clusters)):
                age=step(f,310+j*4,319+j*4)
                route.data.bevel_factor_end=max(.0001,age)
                key(route.data,f,"bevel_factor_end")
                for point in city:
                    point.scale=(max(.0001,age),)*3
                    key(point,f,"scale")
        if f==1:
            standing=rig.measure_leg_lengths()
    stage(ext,1,156);stage(ctrl,157,308);stage(india,309,END)
    assert max(distances.values())<.001
    (OUT/"contact_check.json").write_text(json.dumps(distances,indent=2))
    finish(s,OUT/"padoda_part4_v01.blend",(rig,))

if __name__=="__main__":
    build()
