"""Warm night bedroom and cool gym dressed for close vertical cameras."""
import math
from pathlib import Path
from random import Random

import bpy
from mathutils import Vector
import ricks_v2_kit as k

ART=Path(__file__).with_name("art")


def box(col,name,pos,size,material,parent=None,bevel=0):
    x,y,z=(v*.5 for v in size)
    vertices=[(a*x,b*y,c*z) for a,b,c in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
              (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    obj=k.mesh(name,col,vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,parent)
    obj.location=pos
    if bevel:
        mod=obj.modifiers.new("Rounded hard-surface edge","BEVEL")
        mod.width=bevel
        mod.segments=2
    return obj


def stroke(col,name,coords,radius,mat,parent=None):
    obj=k.tube(name,col,coords,radius,mat,parent)
    obj.data.resolution_u=2
    obj.data.bevel_resolution=1
    return obj


def text(col,label,pos,size,mat,parent=None):
    font=bpy.data.curves.new(label,"FONT")
    font.body=label
    font.align_x="CENTER"
    font.size=size
    font.resolution_u=5
    obj=k.put(bpy.data.objects.new(label,font),col,parent,mat)
    obj.location=pos
    obj.rotation_euler.x=math.pi/2
    return obj


def print_on_plane(col,name,art,pos,size,parent=None,emission=1):
    mat=k.artwork(name,ART/art,glow=emission,cel=False)
    w,h=(v/2 for v in size)
    obj=k.mesh(name,col,[(-w,0,-h),(w,0,-h),(w,0,h),(-w,0,h)],[(0,1,2,3)],mat,parent,
               uv=[(0,0),(1,0),(1,1),(0,1)])
    obj.location=pos
    obj.visible_shadow=False
    return obj


def palette():
    colors={"ink":"#161020","blue":"#3c527a","lightblue":"#818fac","cream":"#efe0ca","gold":"#f4b35f",
            "red":"#bb4649","night":"#262c47","plum":"#443b56","grey":"#777e8d","metal":"#626e79",
            "turf":"#2e5552","rubber":"#323c4d","cork":"#a56c53","roof":"#4b5475"}
    m={name:k.surface(name,color,.78) for name,color in colors.items()}
    m["wood"]=k.texture("Fine amber oak",("#332b43","#8a5445","#bf865e"),"wood",(.74,.91))
    m["paint"]=k.texture("Painterly deep-indigo wall",("#182137","#293851","#475777"),"plaster",(.82,.92))
    m["shade"]=k.emission("Amber paper lampshade","#ffc277",2.6)
    m["window"]=k.emission("Midnight skyline atmosphere","#3c507d",1.08)
    m["moon"]=k.emission("Cool soft November moon","#d5e6ff",2.1)
    m["spark"]=k.emission("Little comic highlight","#ffcf66",1.5)
    m["marquee"]=k.emission("Red LED alarm","#ff505a",2.05)
    return m


def wood_floor(col,m):
    box(col,"Stained wooden floor",(0,1,-.092),(12,11,.181),m["wood"])
    for j in range(30):
        x=(j-14.5)*.302
        stroke(col,"Long floorboard seam",[(x,-4,.002),(x,4.7,.002)],.005,m["plum"])
        for i in range(4):
            y=-3.2+i*1.84+.91*(j%2)
            stroke(col,"Offset end-grain seam",[(x+.008,y,.003),(x+.296,y,.003)],.0035,m["plum"])
        for i in range(6):
            y=-2.72+i*1.08+.16*math.sin(j*2.01)
            x0=x+.048+.041*(i%3)
            stroke(col,"Hand-painted slender woodgrain",( (x0,y,.004),(x0+.013,y+.14,.004),
                   (x0+.021,y+.33,.004),(x0+.012,y+.46,.004)),.0036,m["gold"] if i%3==0 else m["plum"])


def cylinder(col,name,pos,r,h,mat,parent=None,*,axis="Z",top=None,segments=22):
    obj=k.cylinder(name,col,pos,r,h,mat,parent,r2=top,length_segments=segments)
    if axis=="Y":
        obj.rotation_euler.x=math.pi/2
    elif axis=="X":
        obj.rotation_euler.y=math.pi/2
    return obj


def quilt(col,m):
    wool=k.texture("Indigo brushed woven blanket",("#26354d","#465d89","#788cb0"),"plaster",(.88,.95))
    coords=[]
    for r in range(13):
        for s in range(11):
            x=.37+(s-5)*.138
            y=-.42+r*.108
            center=.603+.08*math.sin(math.pi*r/12)+.017*math.sin(s*.96+r*.19)
            edge=max(0,abs(s-5)-4)*(-.068)
            coords.append((x,y,center+edge))
    faces=[(r*11+s,r*11+s+1,(r+1)*11+s+1,(r+1)*11+s) for r in range(12) for s in range(10)]
    q=k.mesh("Pleated duvet with soft folded edges",col,coords,faces,wool,smoothing=True)
    q.modifiers.new("Cloth thickness","SOLIDIFY").thickness=.016
    for j in range(7):
        stroke(col,"Fine sewn quilt stripe",[Vector(coords[(j+2)*11+s])+Vector((0,-.003,.009)) for s in range(11)],
               .008,m["lightblue"] if j%3==0 else m["blue"])
    for j in (1,4,7,9):
        stroke(col,"Long sewn blanket accent",[Vector(coords[r*11+j])+Vector((0,0,.009)) for r in range(13)],
               .006,m["lightblue"])
    for j in range(5):
        for ri in (.012,.031):
            idx=j*2+2
            stroke(col,"Double stitched piping on duvet",
                   [Vector(coords[idx*11+p])+Vector((0,-ri,.013)) for p in range(11)],
                   .0045,m["cream"] if j%2 else m["lightblue"])


def bedroom(col,m):
    wood_floor(col,m)
    border=k.emission("Oat thread on the navy bedside runner","#977f83",.92)
    deep=k.surface("Midnight mauve runner backing","#342c48",.92)
    box(col,"Slim handmade wool bedside runner",(-.95,-.04,.008),(1.05,2.31,.016),deep,bevel=.007)
    for j in range(30):
        y=-1.15+j*.076
        stroke(col,"Broken herringbone weave in the bedside runner",[(-1.449,y,.022),(-1.25,y+.023,.022),
               (-.949,y-.011,.022),(-.689,y+.023,.022),(-.447,y,.022)],.006,
               border if j%3 else m["lightblue"])
    for x in (-1.451,-1.414,-.485,-.449):
        stroke(col,"Pale side stripe on bedside runner",[(x,-1.17,.023),(x,1.06,.023)],.008,border)
    back=2.97
    box(col,"Deep purple bedroom back wall",(0,back,1.71),(10,.19,3.43),m["paint"])
    box(col,"Night indigo side wall",(-3.19,.1,1.70),(.13,7.7,3.4),m["paint"])
    for z in (.092,.21,2.93):
        box(col,"Dark oak architectural wall trim",(0,back-.116,z),(9.8,.075,.061),m["wood"])
    framed=k.surface("Quiet lavender print mount","#5e5574",.85,glow=.13)
    motif=k.emission("Soft gold frame pinstripe","#e0ae7b",.85)
    for i,(x,z,w,h) in enumerate(((-2.64,1.69,.38,.58),(-2.62,2.38,.35,.45),(.99,1.12,.77,.28),(1.85,2.13,.48,.72),
                                   (2.43,2.28,.40,.45),(2.81,1.73,.32,.53))):
        box(col,"Slim honey edge wall-art frame",(x,back-.133,z),(w,.091,h),m["wood"],bevel=.015)
        box(col,"Deep mauve wall artwork surface",(x,back-.187,z),(w-.053,.024,h-.056),framed)
        for j in range(4):
            d=(j-1.5)*.072
            stroke(col,"Rose and brass geometric print",[(x-w*.34,back-.205,z+d-.04),
                 (x-w*.09,back-.205,z+d+.067),(x+w*.29,back-.205,z+d-.036)],.009,motif)
    for j in range(8):
        xx=(j-3.5)*.58
        stroke(col,"Gold inlay along bedroom wainscot",[(xx,back-.150,.24),(xx,back-.150,.67),
               (xx+.52,back-.150,.67),(xx+.52,back-.150,.24)],.009,m["gold"])
    # Large moon window, little city silhouettes and soft curtains.
    box(col,"Distant oak sash frame",(-.83,back-.16,1.98),(2.45,.25,1.57),m["wood"],bevel=.042)
    box(col,"Moonlit night behind the sash",(-.83,back-.303,1.99),(2.20,.028,1.34),m["window"])
    cylinder(col,"Distant cream blue moon",(-1.24,back-.331,2.403),.202,.016,m["moon"],axis="Y",segments=42)
    rng=Random(48)
    for j in range(15):
        x=-1.89+j*.154
        height=rng.uniform(.19,.76)
        box(col,"Distant silhouetted city roof",(x,back-.346,1.32+height*.5),(.163,.034,height),m["night"])
        for i in range(int(height/.135)):
            for s in (-1,1):
                if (i+j+s)%4:
                    box(col,"Warm little skyline window",(x+s*.036,back-.373,1.403+i*.113),
                        (.029,.007,.034),m["shade"] if (j+i)%3==0 else m["moon"])
    for i in range(21):
        x=rng.uniform(-1.91,.19);z=rng.uniform(1.97,2.57)
        k.ball("Distant pinprick star",col,(x,back-.333,z),(.012,.005,.012),m["moon"],segments=8,rings=5)
    for x in (-2.03,-.83,.365):
        box(col,"Narrow night-window sash",(x,back-.392,1.99),(.060,.080,1.49),m["plum"])
    box(col,"Window sill with amber reflections",(-.83,back-.385,1.272),(2.57,.267,.085),m["wood"],bevel=.020)
    for side in (-1,1):
        for j in range(6):
            x=-.83+side*(1.11+j*.083)
            box(col,"Indigo velvet drape fold",(x,back-.420+.024*math.cos(j),1.82),
                (.12,.104,1.90+.046*(j%3)),m["plum"] if j%2 else m["blue"],bevel=.044)
    box(col,"Headboard chamfered timber",(.37,.91,.685),(1.57,.23,1.23),m["wood"],bevel=.071)
    box(col,"Low bed platform",(.37,.32,.247),(1.55,1.65,.361),m["wood"],bevel=.048)
    box(col,"Cream tucked mattress",(.37,.266,.461),(1.48,1.53,.173),m["cream"],bevel=.072)
    for j in range(7):
        x=-.25+j*.204
        stroke(col,"Padded headboard vertical seam",[(x,.786,.73),(x,.785,1.20)],.010,m["ink"])
    pillow=k.ball("Soft blue head pillow",col,(.39,.736,.598),(.50,.245,.114),m["lightblue"],segments=23,rings=11)
    pillow.rotation_euler.x=.28
    quilt(col,m)
    box(col,"Deep walnut bedside table",(1.41,.54,.32),(.55,.54,.625),m["wood"],bevel=.030)
    for z in (.234,.45):
        box(col,"Bedside maple drawer",(1.41,.249,z),(.481,.058,.145),m["wood"],bevel=.018)
        box(col,"Brass bedside handle",(1.41,.204,z),(.157,.045,.028),m["gold"],bevel=.008)
    cylinder(col,"Round brass lamp base",(1.53,.53,.662),.123,.063,m["metal"])
    cylinder(col,"Slim bedside lamp stem",(1.53,.53,.827),.030,.294,m["gold"])
    cylinder(col,"Lit ochre lampshade",(1.53,.53,1.099),.190,.273,m["shade"],top=.124,segments=32)
    for z,r in ((.964,.191),(1.234,.125)):
        cylinder(col,"Dark shade silhouette band",(1.53,.53,z),r+.003,.014,m["gold"],segments=30)
    k.make_light_cone("Bedside cone across drawer and book",(col),(1.53,.523,1.071),(1.33,.38,.49),.106,.36,"#ffb65f")
    box(col,"Graphite bedside digital alarm",(1.196,.302,.699),(.294,.163,.148),m["ink"],bevel=.023)
    clocks=[]
    for label in ("12:00","2:00"):
        clocks.append(text(col,label,(1.196,.214,.672),.079,m["marquee"]))
    for j in range(4):
        z=.661+j*.033
        book=box(col,"Stack of dog-eared bedside books",(-.681,.684,z),(.264,.184,.031),
                 (m["blue"],m["cream"],m["cork"])[j%3],bevel=.006)
        book.rotation_euler.z=.13*(-1)**j
    box(col,"Calendar wall mount",(1.22,2.767,1.889),(.78,.082,.701),m["wood"],bevel=.020)
    print_on_plane(col,"November wall calendar with day one circled","wall_calendar.png",
                   (1.22,2.719,1.889),(.684,.633))
    for j in range(17):
        x=.878+j*.042
        stroke(col,"Calendar wire binding loops",[(x,2.725,2.201),(x,2.701,2.218),(x,2.726,2.241)],
               .008,m["gold"])
    for x in (.833,1.605):
        stroke(col,"Thin highlight on calendar oak trim",[(x,2.723,1.55),(x,2.722,2.225)],.010,m["gold"])
    for x in (1.91,2.40):
        box(col,"Deep narrow display shelves",(x,2.79,1.32),(.43,.27,.056),m["wood"],bevel=.011)
        for j in range(4):
            box(col,"Lean blue and sienna shelf books",(x-.155+j*.095,2.754,1.47),
                (.075,.104,.239+.019*(j%3)),(m["plum"],m["blue"],m["cork"])[j%3],bevel=.004)
    for i in range(7):
        x=.23+i*.047
        stroke(col,"Warm oak bedfront joinery",[(x,-.519,.12),(x,-.519,.346)],.006,m["gold"])
    key=k.make_ricks_light("Warm lamp-driven left room pool",col,(1.34,-.08,1.86),(.15,.33,.85),"#ffb56d",153,.62)
    k.make_ricks_light("Cool window-motivated blue rim",col,(-1.15,1.21,2.40),(.25,-.14,1),"#839fff",223,.76)
    k.make_ricks_light("Quiet warm ceiling bounce",col,(-.55,-2.1,2.65),(0,.23,.84),"#ffd5ae",62,1.37)
    return clocks


def dumbbell(col,m,name,parent=None,blue=True):
    handle=k.empty(name,col,parent=parent)
    finish=m["blue"] if blue else m["rubber"]
    cylinder(col,"Brushed grip pin",(0,0,0),.018,.210,m["metal"],handle,axis="X",segments=14)
    for j in range(5):
        x=-.041+j*.020
        cylinder(col,"Raised knurled grip stripe",(x,0,0),.021,.008,m["ink"],handle,axis="X",segments=10)
    for s in (-1,1):
        cap=cylinder(col,"Rubber hex-head gym weight",(s*.085,0,0),.059,.069,finish,handle,axis="X",segments=6)
        k.apply_prop_ink(cap,col,thickness=.002)
        cylinder(col,"Silver dumbbell bolt cap",(s*.122,0,0),.017,.013,m["metal"],handle,axis="X",segments=12)
    return handle


def gym(col,m):
    box(col,"Layered matte gym flooring",(0,.5,-.099),(13,11,.195),m["rubber"])
    for j in range(15):
        y=(j-7)*.444
        for i in range(19):
            x=(i-9)*.46+.23*(j%2)
            box(col,"Shallow rubber tile insets",(x,y,-.011),(.449,.434,.022),(m["rubber"],m["night"],m["blue"])[(j+i)%3])
    for y in (-1.12,.85):
        box(col,"Faded yellow runner's floor stripe",(0,y,.004),(10,.032,.009),m["gold"])
    floor_ink=k.emission("Cool blueprint mat tape","#6f88a9",.86)
    warm_ink=k.emission("Warm old court guide","#ddb370",.86)
    for y in (-1.25,-1.18,-1.051,-.23,-.174,.68,.77,.91):
        box(col,"Narrow graphic floor guide stripe",(0,y,.004),(10,.014,.008),floor_ink)
    for j in range(29):
        x=(j-14)*.27
        for y in (-1.115,-.19,.85):
            box(col,"White exercise-lane position tick",(x,y,.009),(.018,.092 if j%4 else .164,.007),
                floor_ink if j%4 else warm_ink)
    for row in range(29):
        x=(row-14)*.320
        for i in range(6):
            y=-.95+i*.309
            box(col,"Yard marks breaking long empty mat runs",(x+.09*(i%2),y,.004),(.148,.016,.007),
                floor_ink if (i+row)%4 else warm_ink)
            box(col,"Short adjacent rubber floor channel",(x+.09*(i%2)+.079,y+.066,.004),(.017,.082,.007),
                floor_ink)
    box(col,"Layered deep navy painted gym wall",(0,3.05,1.72),(11,.18,3.45),m["paint"])
    box(col,"Gym accent wall dark lower trim",(0,2.94,.16),(10,.125,.31),m["turf"])
    for j in range(16):
        x=(j-7.5)*.49
        box(col,"Wide charcoal gym wall rib",(x,2.928,1.49),(.047,.104,2.69),m["rubber"])
    for x in (-1.70,.05,1.80):
        box(col,"Blackened gym mirror or tall window frame",(x,2.828,1.79),(1.53,.15,1.47),m["metal"],bevel=.030)
        box(col,"Blue reflected shapes in gym glass",(x,2.732,1.79),(1.42,.023,1.36),m["window"])
        for z in (1.58,2.23):
            box(col,"Milk-blue reflected ceiling geometry",(x,2.703,z),(1.33,.022,.075),m["lightblue"])
        box(col,"Black gym mirror mullion",(x,2.702,1.79),(.041,.024,1.36),m["rubber"])
        for i in range(8):
            v=x-.62+i*.175
            stroke(col,"Soft vertical window glare stripe",[(v,2.698,1.23),(v+.12,2.699,2.42)],
                   .009,m["blue"] if i%3 else m["lightblue"])
    box(col,"Three-tier steel dumbbell rack",(.38,2.21,.522),(3.47,.38,.997),m["rubber"],bevel=.033)
    for row in range(3):
        z=.29+row*.290
        box(col,"Blue-black weight-rack shelf",(.38,1.99,z-.062),(3.57,.334,.061),m["metal"],bevel=.014)
        for j in range(10):
            d=dumbbell(col,m,"Small racked hex weight",blue=row==1)
            d.location=(-1.15+j*.335,1.99,z)
            d.scale=(.88,.88,.88)
    for i, x in enumerate((-2.63,-2.18,2.53)):
        k.ball("Bunched exercise stability ball",col,(x,1.67,.23),(.24,.24,.24),
               (m["turf"],m["red"],m["blue"])[i],segments=20,rings=12)
    for x in (-2.96,2.51,3.05):
        box(col,"Old wire-look gym bench plank",(x,1.04,.417),(.91,.35,.079),m["blue"],bevel=.019)
        for s in (-1,1):
            stroke(col,"Oblique exercise bench structure",[(x+s*.31,.96,.038),(x+s*.32,1.04,.417),
                 (x+s*.37,1.14,.038)],.025,m["metal"])
    box(col,"Flush textile floor drop mat",(.52,-.49,-.014),(.73,.46,.030),m["grey"],bevel=.005)
    for j in range(22):
        yy=-.708+j*.021
        stroke(col,"Diagonal safety-map thread on weight drop pad",[(.161,yy,.004),(.86,yy+.025,.004)],
              .0034,m["rubber"] if j%3 else warm_ink)
    for x in (-2.05,-.24,1.92):
        box(col,"Warm overhead gym lamp black edge",(x,.83,2.54),(1.0,.34,.08),m["ink"],bevel=.026)
        box(col,"Warm glowing recessed gym light",(x,.83,2.493),(.89,.26,.029),m["shade"],bevel=.017)
    for y in (-.795,.465):
        box(col,"Open doorway side jamb",(-2.02,y,1.071),(.223,.149,2.14),m["blue"],bevel=.021)
    box(col,"Cross beam over open gym exit",(-2.02,-.164,2.143),(.223,1.41,.144),m["blue"],bevel=.021)
    box(col,"Indigo hall beyond the open door",(-2.93,-.165,1.061),(.07,1.46,2.11),m["night"])
    box(col,"Glowing amber exit plate",(-1.955,-.161,2.27),(.075,.63,.125),m["cork"],bevel=.017)
    badge=text(col,"EXIT",(-1.912,-.16,2.232),.101,m["shade"])
    badge.rotation_euler.z=math.pi/2
    k.make_ricks_light("Warm overhead gym light",col,(-.92,-1.63,2.57),(0,-.34,.94),"#ffcf9d",275,.79)
    k.make_ricks_light("Cool reflection off the gym windows",col,(1.69,1.72,2.37),(0,-.40,1.05),"#8baeff",190,.88)
    k.make_ricks_light("Soft cool mat bounce",col,(.22,-2.3,1.86),(.27,-.27,.74),"#b0bbec",98,1.38)


def phone(col,m,parent=None):
    root=k.empty("Graphite phone",col,parent=parent)
    rect=box(col,"Rounded graphite handset shell",(0,0,0),(.152,.030,.270),m["ink"],root,bevel=.017)
    k.apply_prop_ink(rect,col,thickness=.002)
    screens=[print_on_plane(col,"Incoming message screen",f"phone_{i}.png",(0,-.016,0),(.135,.251),root) for i in range(2)]
    box(col,"Recessed upper phone earpiece", (0,-.017,.120),(.057,.008,.008),m["grey"],root,bevel=.003)
    return root,screens
