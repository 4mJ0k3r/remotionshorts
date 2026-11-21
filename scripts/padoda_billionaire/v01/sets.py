import math
import ricks_v2_kit as k
from courtyard import box,tapered_between as rod
from mathutils import Vector
import bpy

def disk(name,c,p,r,h,m,parent=None):
    obj=k.cylinder(name,c,p,r,h,m,parent,length_segments=48)
    obj.rotation_euler.x=math.pi/2
    return obj

def text(c,txt,p,size,material):
    data=bpy.data.curves.new(txt,"FONT");data.body=txt;data.align_x="CENTER";data.size=size
    o=k.put(bpy.data.objects.new(txt,data),c,mat=material);o.location=p;o.rotation_euler.x=math.pi/2

def workshop(c):
    wood=k.texture("Workshop walnut",("#211925","#69402d","#9b643d"),"wood")
    navy=k.texture("Workshop indigo",("#121c3a","#192947","#354267"),"plaster")
    brass=k.surface("Gauge brass","#d1954c",.27,.66)
    black=k.emission("Gauge ink","#261e2b",.8)
    red=k.emission("Hot redline","#ff2940",2.8)
    sky=k.emission("Midnight blue window","#4078c1",1)
    shade=k.surface("Banker's lamp green","#178578",.4)
    amber=k.emission("Lamp diffuser","#ffc16e",5)
    cream=k.surface("Gauge enamel","#ffe1a1",.82,glow=.3)
    box("Midnight plaster wall",c,(0,1.66,2.1),(7,.18,4.6),navy)
    box("Long plank flooring",c,(0,-.5,-.09),(8,7,.18),wood)
    for i in range(13):box("Floorboard seam",c,(-3.2+i*.53,-.5,.002),(.013,6,.004),navy,0)
    box("Dark baseboard",c,(0,1.54,.09),(6,.09,.18),wood,.018,True)
    box("Recessed window frame",c,(-.52,1.53,1.57),(1.53,.17,1.64),wood,.022,True)
    box("Blue window opening",c,(-.52,1.43,1.57),(1.39,.029,1.49),sky,.008)
    for i in range(17):
        o=box("Heavy venetian slat",c,(-.52,1.39,.88+i*.084),(1.39,.11,.045),navy,.007)
        o.rotation_euler.x=.24
    for x in (-.98,-.11):box("Blind pull cord",c,(x,1.31,1.54),(.018,.024,1.47),brass,.002)
    box("Workbench thick slab",c,(.84,.15,.49),(1.38,.70,.125),wood,.03,True)
    for x in (.25,1.42):
        for y in (-.14,.41):box("Bench leg",c,(x,y,.235),(.09,.09,.47),wood,.016,True)
    for i in range(5):
        p=box("Scattered drafting sheets",c,(1.01+i*.04,.13-i*.019,.554+i*.003),(.27,.19,.004),cream,.001);p.rotation_euler.z=i*.17
        rod("Metal hand tool",c,(.33+i*.17,-.17,.563),(.48+i*.17,-.08,.563),.013,.013,brass)
    books=[k.surface("Colored book cloth",col) for col in ("#ad5046","#356e73","#68558b","#c08a51")]
    for i,z in enumerate((.87,1.38,1.84)):
        box("Tool shelf",c,(1.19,1.37,z),(1.60,.34,.07),wood,.019,True)
        for j in range(8):
            m=books[(j+i)%4];x=.50+j*.17;h=.13+.033*(j%3)
            if j%3:box("Clothbound workshop manual",c,(x,1.28,z+.037+h/2),(.11,.20,h),m,.012)
            else:
                k.cylinder("Jar",c,(x,1.26,z+.106),.056,.14,m,length_segments=12)
                k.cylinder("Brass jar lid",c,(x,1.26,z+.184),.056,.029,brass,length_segments=12)
    for j in range(3):box("Rough cedar storage crate",c,(-1.52+.34*j,1.1,.18),(.30,.35,.36),wood,.022,True)
    k.cylinder("Lamp foot",c,(-.72,.33,.076),.12,.097,brass)
    k.tube("Curved banker's lamp stem",c,[(-.72,.33,.10),(-.72,.33,.70),(-.66,.34,.98),(-.57,.34,.98)],.024,brass)
    box("Viridian glass lamp shade",c,(-.59,.34,.95),(.33,.22,.13),shade,.041,True)
    box("Under-shade amber filament",c,(-.59,.34,.883),(.27,.16,.024),amber,.013)
    k.make_light_cone("Amber banker's lamp cone",c,(-.59,.34,.871),(-.51,.29,.21),.072,.28,"#ffae64")
    base=disk("Oversized pressure gauge",c,(.63,-.11,.90),.260,.116,brass)
    k.apply_prop_ink(base,c,thickness=.007)
    disk("Pressure meter glass and dial",c,(.63,-.179,.90),.233,.016,cream)
    text(c,"PRESSURE",(.63,-.195,.96),.045,black)
    text(c,"GAS",(.63,-.195,.78),.039,black)
    for j in range(19):
        a=math.radians(-125+250*j/18)
        o=box("Gauge scale mark",c,(.63+.197*math.sin(a),-.195,.90+.197*math.cos(a)),(.011,.009,.028),red if j>=14 else black,.002)
        o.rotation_euler.y=a
    pointer=k.empty("Animated pressure needle pivot",c,(.63,-.212,.90))
    k.mesh("Pressure red needle",c,[(-.014,0,-.045),(.015,0,-.034),(.008,0,.123),(0,0,.176)],[(0,1,2,3)],red,pointer)
    disk("Pressure needle rivet",c,(.63,-.224,.90),.022,.012,black)
    k.make_ricks_light("Cold window shaft",c,(-.53,1.00,2.14),(-.13,-.46,.74),"#6d98ff",120,.72)
    k.make_ricks_light("Banker warm key",c,(-.96,-.55,1.64),(-.03,.12,.95),"#ffbf77",105,.61)
    k.make_ricks_light("Workshop face fill",c,(.17,-1.94,1.53),(-.10,.15,1.04),"#a9bdff",90,1.16)
    lime=k.make_ricks_light("Lime cartoon backlight",c,(-.02,.67,.62),(0,-.13,.90),"#6bff4e",8,.57)
    return pointer,lime

def vault(c):
    navy=k.texture("Vault naval plaster",("#111428","#25243b","#39304c"),"plaster")
    steel=k.surface("Bank steel blue","#484f62",.40,.67)
    brass=k.surface("Machined brass","#bb843e",.34,.7)
    golds=[k.surface("Gold ingot",p,.245+i*.03,.69,glow=.15) for i,p in enumerate(("#d88d26","#f3b033","#f8c548"))]
    velvet=k.surface("Throne raspberry velvet","#a9264c",.87,glow=.045)
    glow=k.emission("Honey lantern","#ffd05a",4.2)
    floor=k.texture("Dark polished purple marble",("#121426","#292438","#634459"),"wood",(.08,.18))
    box("Dark marble vault floor",c,(0,0,-.128),(14,16,.25),floor)
    for x in (-3.5,-2.29,2.29,3.5):box("Brass floor inlay",c,(x,.08,.001),(.022,12,.009),brass,.002)
    box("Vault hammer-painted back wall",c,(0,4.94,3.52),(13,.32,7.4),navy)
    for x in (-4.3,-3.01,3.01,4.3):
        box("Vault pillar",c,(x,4.40,2.42),(.51,.69,4.84),navy,.049,True)
        for z in (.20,4.45):box("Carved pillar collar",c,(x,4.27,z),(.72,.80,.19),brass,.029,True)
        for dx in (-.15,.15):box("Gold pillar rib",c,(x+dx,4.04,2.33),(.032,.042,4.06),brass,.006)
    ring=disk("Circular vault frame",c,(-.28,4.72,2.39),2.24,.25,brass)
    k.apply_prop_ink(ring,c,thickness=.018)
    disk("Open vault recess",c,(-.28,4.57,2.39),2.05,.115,navy)
    door=k.empty("Open circular steel bank door",c,(1.69,4.03,2.44));door.rotation_euler.z=-.43
    plate=disk("Steel door plate",c,(0,0,0),1.81,.21,steel,door);k.apply_prop_ink(plate,c,thickness=.018)
    disk("Vault gold locking wheel",c,(0,-.14,0),.49,.07,brass,door)
    disk("Wheel steel recess",c,(0,-.19,0),.393,.055,steel,door)
    disk("Lock wheel lit hub",c,(0,-.23,0),.135,.057,glow,door)
    for i in range(12):
        a=i*math.tau/12;x,z=math.sin(a),math.cos(a)
        o=disk("Door inset brass bolt",c,(1.65*x,-.131,1.65*z),.052,.029,brass,door)
        if i%2==0:
            o=box("Golden radial lock spoke",c,(.97*x,-.123,.97*z),(.117,.094,1.01),brass,.021,parent=door)
            o.rotation_euler.y=a
    for tier in range(6):
        n=7-tier
        for j in range(n):
            for row in range(3 if tier<3 else 2):
                x=(j-(n-1)/2)*.48+.03*((tier+row)%2);y=.44+.33*row+.091*tier;z=.114+.213*tier
                b=box("Stacked beveled bullion",c,(x,y,z),(.448,.307,.199),golds[(tier+j+row)%3],.031,tier>=3 or (row==0 and j%2==0))
                b.rotation_euler.z=.036*math.sin(tier+j+row)
                if row==0 and j%2==0:box("Assay-stamped ingot groove",c,(x,y-.155,z),(.184,.005,.024),brass,.002)
    box("Crimson velvet throne cushion",c,(0,1.0,1.34),(.64,.61,.125),velvet,.045,True)
    box("Tufted throne back",c,(0,1.285,1.809),(.63,.172,.98),velvet,.070,True)
    k.tube("Throne gilt surround",c,[(-.34,1.18,1.38),(-.34,1.18,2.09),(-.27,1.18,2.24),(0,1.18,2.38),
           (.27,1.18,2.24),(.34,1.18,2.08),(.34,1.18,1.38)],.035,brass)
    for s in (-1,1):box("Gilt throne arm",c,(s*.345,1.00,1.51),(.091,.52,.091),brass,.022,True)
    for i in range(8):
        box("Scattered gold reserve",c,((-1)**i*(1.7+.068*i),1.90+.157*i,.131+.08*(i%2)),(.43,.31,.204),golds[i%3],.03,True)
    for x,y,z in ((-2.55,2.63,4.27),(2.73,2.51,4.27),(-.27,4.03,4.63)):
        k.cylinder("Hanging brass spotlight",c,(x,y,z),.206,.164,brass,r2=.139)
        k.ball("Glow spotlight lens",c,(x,y,z-.088),(.161,.161,.056),glow,segments=18,rings=10)
        k.make_light_cone("Warm translucent gold beam",c,(x,y,z-.100),(x*.57,y-.43,.12),.11,.85,"#ffc85b")
    k.make_ricks_light("Warm heroic face key",c,(-1.85,-2.55,3.58),(0,.71,2.16),"#ffdc93",228,1.35)
    k.make_ricks_light("Amber door light",c,(3.47,1.82,4.08),(1,3.67,2.1),"#ffc365",285,2.6)
    k.make_ricks_light("Low bullion rim",c,(1.54,-1.72,1.91),(.22,.64,1.27),"#ffd05a",126,1.15)
    k.make_ricks_light("Navy side fill",c,(-3.59,1.32,3.20),(-1.5,2.8,2.2),"#7c92d2",92,2.25)
    bills=[]
    green=k.surface("Emerald cash cardstock","#39815d",.86,glow=.26)
    light=k.surface("Bank note fine print","#add592",.85,glow=.22)
    dark=k.surface("Engraved money portrait","#185745",.85,glow=.13)
    for i in range(31):
        note=k.empty("Fluttering cash bill",c)
        box("Emerald bank note",c,(0,0,0),(.226,.111,.009),green,.005,parent=note)
        for y in (-.038,.038):box("Banknote printed edge",c,(0,y,.006),(.195,.004,.003),light,.001,parent=note)
        k.cylinder("Note centre rosette",c,(0,0,.006),.027,.003,dark,note,length_segments=10)
        bills.append(note)
    return bills,brass,golds,glow
