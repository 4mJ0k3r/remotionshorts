"""Padoda Energy invention sequence."""
import json
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from sequence_tools import *

OUT=ROOT/"renders/padoda_billionaire/part3_v01"
END=303
CAL=(42,75,127,208,221,233,264,294)
BENCH=(*CAL,1,78,186,303)

def bulb(c,loc,size,gold,glass):
    globe=k.empty("Glass lamp rig",c,loc)
    globe.scale=(size,)*3
    k.ball("Glass lightbulb globe",c,(0,0,.15),(.265,.218,.268),glass,globe,segments=24,rings=18)
    k.cylinder("Threaded copper base",c,(0,0,-.15),.132,.205,gold,globe,length_segments=24)
    for j in range(5):
        k.cylinder("Lamp socket screw rim",c,(0,0,-.214+j*.034),.142,.012,gold,globe,length_segments=24)
    lit=k.emission("Lightbulb filament","#ffd36d",1)
    k.tube("Bent golden tungsten filament",c,[(-.073,-.073,-.067),(-.078,-.071,.14),(-.038,-.07,.220),
             (.02,-.07,.154),(.074,-.07,.22),(.087,-.07,-.056)],.016,lit,globe)
    return globe,next(n for n in lit.node_tree.nodes if n.type=="EMISSION").inputs["Strength"]

def goggles(c,hero,metal):
    root=k.empty("Liftable smoked glass inventor goggles",c,parent=hero.head)
    shade=k.emission("Dark shaded teal lenses","#1a2c3c",1)
    glint=k.emission("Diagonal lens accent","#79bacb",1.15)
    for s in (-1,1):
        x=s*.094
        disk("Brass goggle housing",c,(x,0,0),.081,.038,metal,root)
        disk("Smoked circular lens",c,(x,-.026,0),.060,.015,shade,root)
        k.tube("Lens glint",c,[(x-.030,-.037,-.024),(x+.020,-.037,.032)],.006,glint,root)
    box("Goggles bridge",c,(0,.001,.014),(.075,.021,.026),metal,.008,parent=root)
    return root

def build():
    s,cam=scene_setup(END,((1,0),(72,0),(73,.072),(74,.14),(75,.001),(77,0),(END,0)))
    entry=collection(s,"Warm study corner")
    shop=collection(s,"Inventor workshop",25)
    a=entry[0]; c=shop[0]
    room(a,workshop=False)
    wood,gold,dark=room(c)
    cream=k.emission("Cream device lettering","#fff0c6",1.18)
    red=k.surface("Painted red breaker","#ab343c",.69,.0,glow=.12)
    copper=k.surface("Satin copper windings","#b46f46",.68,.52)
    aura=transparent("Golden glass and soft halo","#ffc951",.50,1.65)
    cold=transparent("Teal side bulb glass","#79e7ec",.27,1.28)
    green=transparent("Transparent swirling lime gas","#7bf657",.61,1.45)
    cyan=k.emission("Cyan capacitor discharge","#65ecff",3.1)
    yellow=k.emission("Golden capacitor discharge","#ffc443",2.35)
    hero1=actor(a,"Hero in study"); hero=actor(c,"Inventor Hero")
    glasses=goggles(c,hero,gold)
    idea,idea_light=bulb(a,(-.18,.02,1.92),.87,gold,aura)
    rays=sparks(a,13)
    goldring=ring("Circular gold entrance edge",a,(-.18,-.16,2.05),.24,yellow,.010)
    center=vec((.52,-.094,1.26))
    box("Converter cabinet",c,(.59,.275,.693),(.91,.65,1.34),dark,.091,True)
    for x in (.27,.91):
        box("Machine steel foot",c,(x,.21,.064),(.29,.60,.135),dark,.035,True)
    box("Console brass instrument panel",c,(.60,-.095,.63),(.85,.075,.42),gold,.042,True)
    box("Ink name plate",c,(.59,-.142,.77),(.78,.018,.143),dark,.024,True)
    text(c,"PADODA ENERGY",(.59,-.163,.738),.081,cream)
    for x in (.214,.949):
        for z in (.48,1.51):
            disk("Cabinet assembly bolts",c,(x,-.097,z),.039,.026,copper)
    disk("Brass inspection ring back plate",c,center+vec((0,.031,0)),.326,.102,gold)
    disk("Dark chamber backing",c,center+vec((0,-.024,0)),.286,.060,dark)
    chamber=k.ball("Transparent glass chamber",c,center+vec((0,-.085,0)),(.28,.105,.28),
                  cold,segments=28,rings=20)
    rim=ring("Circular brass glass chamber rim",c,center+vec((0,-.109,0)),.302,copper,.025)
    flare=ring("Gold rim carried from bulb",c,center+vec((0,-.143,0)),.300,yellow,.009)
    for x in (.105,.998):
        k.cylinder("Iron winding core",c,(x,.11,1.26),.086,.52,dark,length_segments=16)
        k.tube("Copper conductor coil",c,[(x+.091*math.cos(j*.47),.11+.091*math.sin(j*.47),1.03+j*.0036)
               for j in range(121)],.021,copper)
    dial=vec((.80,-.163,.53))
    disk("Analog voltage dial housing",c,dial,.112,.038,dark)
    disk("Warm analog enamel face",c,dial+vec((0,-.027,0)),.091,.021,cream)
    needle=box("Moving voltage needle",c,dial+vec((0,-.043,.022)),(.013,.02,.079),red,.003)
    for j in range(7):
        angle=math.radians(-109+j*36)
        tick=box("Small volt dial tick",c,dial+vec((.071*math.sin(angle),-.044,.070*math.cos(angle))),
                 (.009,.009,.016),dark,.002)
        tick.rotation_euler.y=angle
    pivot=vec((.177,-.178,.58))
    box("Breaker safety panel",c,(.185,-.119,.609),(.25,.136,.45),dark,.037,True)
    text(c,"ON",(.177,-.197,.425),.071,cream)
    lever=k.empty("Heavy red breaker control",c,pivot)
    k.tube("Breaker black handle stem",c,[(0,0,0),(-.044,-.061,.062),(-.059,-.085,.164)],.027,dark,lever)
    box("Red breaker grip",c,(-.059,-.09,.165),(.149,.113,.083),red,.027,True,lever)
    lamp,filament=bulb(c,(1.27,.14,1.20),1.17,copper,cold)
    cableink=k.surface("Heavy graphite power cable","#111620",.79)
    k.tube("Black generator-to-lamp power cable",c,[(.86,-.10,.24),(1.16,-.26,.10),(1.59,-.06,.10),
             (1.63,.12,.57),(1.27,.13,.94)],.035,cableink)
    k.cylinder("Tall power lamp pedestal",c,(1.27,.14,.33),.164,.66,dark,length_segments=20)
    k.cylinder("Brass pedestal base",c,(1.27,.14,.059),.222,.116,copper,length_segments=24)
    vapor=[k.ball("Lime chamber swirl packet",c,center,(.115,.038,.063),green,segments=14,rings=10) for _ in range(5)]
    bolts=[]
    for j in range(5):
        points=[center+vec((-.21+.07*i,-.186,.102*math.sin(j*1.36+i*2.8))) for i in range(7)]
        arc=k.tube("Jagged cyan-gold electricity",c,points,.009,cyan if j%2 else yellow)
        for point in arc.data.splines[0].bezier_points:
            point.handle_left_type=point.handle_right_type="VECTOR"
        bolts.append(arc)
    spill=k.make_ricks_light("Cyan electrical spill",c,(.91,-.46,1.56),(-.3,-.03,1.19),"#65EFFF",0,.45)
    tool=k.empty("Socket wrench turn around actual bolt",c,(.214,-.146,1.51))
    disk("Wrench socket",c,(0,-.007,0),.055,.04,copper,tool)
    k.tube("Silver wrench handle",c,[(0,-.021,0),(-.105,-.023,-.069),(-.234,-.022,-.117)],.020,
           k.surface("Brushed steel wrench","#9faabe",.69,.55),tool)
    weld=sparks(c,10)
    contacts={}
    for f in range(1,END+1):
        if f<=75:
            look=step(f,11,31)
            pop=step(f,27,35)
            root=(-.18+.058*look,0,0)
            arms=idle()
            arms[1]=(arms[1][0].lerp(vec((.112,-.262,.483)),step(f,1,11)*(1-step(f,19,29))),arms[1][1])
            hero1.pose(f,root,.10,.09+.085*look,arms,floor_legs(),"smug" if f==1 else "shock" if f==28 else None,
                       head_yaw=.18*(1-look),head_tilt=.18*(1-look)-.20*look,bounce=.018*pop)
            idea.scale=(max(.02,pop*(.87+.08*math.sin(math.pi*step(f,31,41)))),)*3
            idea.location.z=1.67+.21*pop
            idea_light.default_value=3.5*pop
            key(idea_light,f,"default_value"); key(idea,f,"location","scale")
            scatter(rays,f,(-.18,-.05,2.03),step(f,29,48))
            visible(goldring,71<=f<=75,f)
            t=step(f,62,75)
            p=vec((-.20,-3.46,1.50)).lerp(vec((-.18,-1.05,1.92)),t)
            aim=vec((-.07,.06,1.38)).lerp(vec((-.18,-.07,2.05)),t)
            camera_pose(cam,entry,f,p,aim,37+3*t)
            continue
        phase=(f-108)%14
        stroke=.18+.68*step(phase,1,5)-.68*step(phase,7,13)
        wrench_active=93<=f<=181
        tool.rotation_euler.y=stroke
        key(tool,f,"rotation_euler")
        for item in tool.children:visible(item,wrench_active,f)
        pressing=step(f,198,210)
        lever.rotation_euler.y=-1.83*pressing
        key(lever,f,"rotation_euler")
        rotation=lever.rotation_euler.to_matrix()
        grip=pivot+rotation@vec((-.114,-.133,.167))
        power=step(f,209,251)
        needle.rotation_euler.y=-1.12+2.18*power+.12*power*math.sin(f*.83)
        key(needle,f,"rotation_euler")
        filament.default_value=.10+5.9*power
        key(filament,f,"default_value")
        spill.data.energy=4+175*power
        key(spill.data,f,"energy")
        visible(flare,f<=78,f)
        for j,packet in enumerate(vapor):
            angle=.13*f+j*math.tau/5
            packet.location=center+vec((.145*math.cos(angle),-.166-.008*j,.148*math.sin(angle)))
            packet.rotation_euler.y=-angle
            packet.scale=(1.2,.83,.9-.42*power)
            key(packet,f,"location","rotation_euler","scale")
        for j,bolt in enumerate(bolts):
            bolt.rotation_euler.y=.0
            visible(bolt,f>=213 and ((f+j*3)%11)<5,f)
        scatter(weld,f,tool.location,step(phase,4,10) if wrench_active else 0,.71)
        root=vec((-.54+.12*step(f,178,196)-.10*step(f,226,250),-.106,0))
        yaw=.20-.14*step(f,245,272)
        tilt=.10+.08*step(f,176,199)-.13*step(f,241,268)
        arms=idle()
        elbows=(vec((-.24,-.10,.254)),vec((.26,-.13,.31)))
        grip_weight=step(f,189,197)*(1-step(f,216,228))
        if wrench_active:
            wrench_point=vec(tool.location)+tool.rotation_euler.to_matrix()@vec((-.234,-.055,-.117))
            arms[1]=(contact(wrench_point,root,yaw,tilt,0,elbows[1]),elbows[1])
            if f in (111,127,157):contacts[f"wrench_f{f}"]=measure_contact(arms[1],root,yaw,tilt,0,wrench_point)
        else:
            arms[1]=(arms[1][0].lerp(contact(grip,root,yaw,tilt,0,elbows[1]),grip_weight),elbows[1])
        if f in (199,208,213):contacts[f"lever_f{f}"]=measure_contact(arms[1],root,yaw,tilt,0,grip)
        wipe=step(f,172,180)*(1-step(f,184,190))
        lift=step(f,252,258)*(1-step(f,261,267))
        arms[0]=(arms[0][0].lerp(vec((-.147,-.20,.73)),max(wipe,lift)),elbows[0])
        hips=step(f,269,280)
        arms=[(h.lerp(vec((side*.113,-.022,.188)),hips),e) for (h,e),side in zip(arms,(-1,1))]
        hero.pose(f,root,yaw,tilt,arms,floor_legs(),
                  "smug" if f==76 or f==182 else "strain" if f==106 else "wink" if f==END-16 else None,
                  head_tilt=.11*(1-hips),head_yaw=.14*(1-hips))
        glasses.location=(0,-.222,.025+.126*step(f,255,263))
        key(glasses,f,"location")
        if f<=79:
            camera_pose(cam,shop,f,(.58,-1.05,1.22),center,39)
        elif f<191:
            t=step(f,80,103)
            p=vec((.72,-2.46,1.49)).lerp(vec((1.71,-3.22,1.38)),t)
            camera_pose(cam,shop,f,p,(.21,.062,1.22),35,(-.26,-.11,1.19))
        elif f<=212:
            t=step(f,191,210)
            camera_pose(cam,shop,f,(.21,-1.46,.81-.13*t),(.084,-.17,.641-.087*t),54)
        elif f<=234:
            camera_pose(cam,shop,f,(.68,-1.61,1.28),center,55)
        else:
            t=step(f,235,END-18)
            p=vec((1.62,-3.04,1.12)).lerp(vec((1.85,-3.89,1.18)),t)
            camera_pose(cam,shop,f,p,(.31,.08,1.11),32,(.31,-.09,1.18))
    stage(entry,1,75); stage(shop,76,END)
    assert max(contacts.values())<.001
    (OUT/"contact_check.json").write_text(json.dumps(contacts,indent=2))
    finish(s,OUT/"padoda_part3_v01.blend",(hero1,hero))

if __name__=="__main__":
    build()
