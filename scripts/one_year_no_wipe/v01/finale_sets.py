"""Dogs, bedroom and loaded vanity used in the last two parts."""
import math
from random import Random

from mathutils import Vector
import ricks_v2_kit as k
from sets import box, line, rim, text
from worlds import light


DOGS=("Dachshund","Big Fluffy Dog","Dalmatian","Chihuahua","Poodle")


def dog(c,m,j):
    root=k.empty(DOGS[j]+" follow rig",c)
    tone=("#a66a49","#fff4de","#f6f0df","#cf9c68","#b28c9e")[j]
    accent=("#643942","#e3ccb5","#252339","#95623f","#806582")[j]
    base=k.surface(DOGS[j]+" body pigment",tone,.81)
    ear=k.surface(DOGS[j]+" ear pigment",accent,.82)
    height,length,width=((.187,.32,.125),(.304,.29,.180),(.273,.26,.138),(.132,.15,.101),(.247,.22,.121))[j]
    body=k.ball("Distinct dog breed trunk",c,(0,.038,height), (width,length,.76*width),base,root,20,12)
    k.apply_prop_ink(body,c,thickness=.004)
    head=k.empty("Dog snout sniff pivot",c,(0,-length*.76,height+.086+.028*(j%3)),root)
    head_size=(.88,1.23,.95,.80,1.0)[j]
    k.ball("Round forehead cartoon dog",c,(0,-.030,.03),(.130*head_size,.108*head_size,.126*head_size),base,head,19,12)
    k.ball("Friendly dog muzzle",c,(0,-.129,-.010),(.077*head_size,.082*head_size,.051*head_size),base,head,17,10)
    k.ball("Lustrous black nose",c,(0,-.203,.013),(.051*head_size,.027,.028*head_size),m["purple"],head,16,10)
    for side in (-1,1):
        x=side*.057*head_size
        k.ball("Dog cream eye sclera",c,(x,-.113,.077),(.033,.022,.036),m["paper"],head,11,7)
        k.ball("Curious dog pupil",c,(x+.008,-.131,.081),(.017,.012,.023),m["purple"],head,11,7)
        if j==3:
            pointed=k.cylinder("Tall Chihuahua ear",c,(side*.098,0,.147),.055,.112,ear,head,r2=.009,length_segments=12)
            pointed.rotation_euler.y=side*.32
        else:
            e=k.ball("Drooping spaniel-like canine ear",c,(side*.107,-.006,.041),
                   (.058,.05,.106 if j in (0,4) else .081),ear,head,15,10)
            e.rotation_euler.y=-side*.28
    if j in (1,4):
        for i in range(12):
            a=i*2.39996
            o=(.15*math.cos(a),.14*math.sin(a),.09+.032*(i%3))
            k.ball("Layered fluffy coat or poodle pom",c,o,(.065,.058,.066),base,head,12,7)
    if j==2:
        rng=Random(101)
        for i in range(20):
            theta=i*2.39996
            phi=rng.uniform(-.95,.95)
            pos=(width*math.cos(theta)*math.cos(phi),.038+length*math.sin(phi),
                 height+.76*width*math.sin(theta)*math.cos(phi))
            k.ball("Dalmatian chocolate round spots",c,pos,(.019,.032,.012),ear,root,10,6)
    legs=[]
    for y in (-length*.56,length*.69):
        for s in (-1,1):
            x=s*width*.64
            leg=k.empty("Four-foot gait pivot",c,(x,y,height-.033),root)
            line(c,"Dark outlined slim dog leg",[(0,0,0),(0,.005,-height*.54),(0,-.026,-height+.052)],
                 .023 if j!=3 else .016,ear,leg)
            k.ball("Small flat dark dog paw",c,(0,-.043,-height+.049),(.034,.046,.015),base,leg,11,7)
            if j==4:
                k.ball("Poodle foot pom",c,(0,-.020,-height+.090),(.044,.041,.042),base,leg,11,7)
            legs.append(leg)
    tail=k.empty("Wagging dog tail pivot",c,(0,length+.01,height+.025),root)
    line(c,"Curving dog tail",[(0,0,0),(0,.14,.035),(0,.219,.137)],.024 if j!=1 else .041,base,tail)
    return root,head,legs,tail


def bedroom(c,m):
    pale=k.surface("Light-blue painted bedroom walls","#91b8d4",.84)
    coral=k.surface("Duvet coral stitched cloth","#ce7775",.849)
    box(c,"Early-morning blue bedroom plaster",(0,1.38,1.55),(11,.13,3.1),pale)
    ribbon=k.surface("Faded pale-blue vertical wallpaper print","#d5e1e8",.91)
    for j in range(40):
        x=(j-19.5)*.222
        box(c,"Thin printed vertical bedroom wallpaper band",(x,1.304,2.181),(.048,.013,1.93),ribbon)
        box(c,"Narrow low contrast second wallpaper band",(x+.057,1.301,2.181),(.014,.009,1.93),m["blue"])
    box(c,"Dark navy painted bedroom baseboard",(0,1.282,.096),(11,.07,.183),m["blue"])
    for z in (.365,.766,1.176):
        box(c,"Slim cream bedroom wainscot molding",(0,1.274,z),(10.95,.048,.034),m["cream"])
    for i in range(22):
        x=(i-10)*.48
        box(c,"Slim blue inset wainscot upright",(x,1.275,.762),(.043,.054,.79),m["blue"])
    box(c,"Oiled bedroom parquet floor",(0,-.20,-.09),(10,8,.18),m["wood"])
    for j in range(34):
        x=(j-16)*.270
        box(c,"Alternating thin parquet strip",(x,-.15,-.010),(.259,5.70,.021),m["wood"] if j%3 else m["wood2"])
        for i in range(5):
            y=(i-2)*.79+.232*(j%2)
            box(c,"Fine warm parquet plank joint",(x,y,.002),(.255,.014,.005),m["purple"])
    for j,color in enumerate(("#cf575a","#ed8849","#f2c24e","#8dae65","#6997c4","#957bad")):
        mat=k.surface("Woven rainbow ring "+color,color,.91)
        r=.99-.126*j
        rim(c,"Braided rainbow rug color",(0,-.761,.0045),r,r,.126,.006,mat)
    box(c,"Warm natural wood bed side frame",(-.69,.50,.221),(1.25,1.27,.303),m["wood"],bevel=.025)
    box(c,"Ivory mattress",(-.69,.50,.408),(1.24,1.27,.137),m["cream"],bevel=.051)
    box(c,"Coral quilted blanket",(-.85,.55,.467),(.91,1.15,.090),coral,bevel=.077)
    k.ball("Ivory puffed sleeping pillow",c,(-.77,.907,.527),(.41,.206,.110),m["paper"],segments=21,rings=12)
    for i in range(9):
        x=-1.23+i*.096
        line(c,"Fine quilting seams",[(x,.019,.493),(x,.34,.525),(x,.91,.525)],.0037,m["red"])
    box(c,"Routed wood study table",(1.26,.761,.706),(.76,.77,.11),m["wood"],bevel=.024)
    for dx in (-.316,.311):
        for y in (.424,1.07):
            box(c,"Tapered writing-desk leg",(1.26+dx,y,.33),(.060,.058,.69),m["wood"])
    box(c,"Scuffed school chair beside desk",(1.30,.19,.37),(.35,.34,.066),m["blue"],bevel=.024)
    for dx in (-.142,.142):
        for y in (.061,.29):
            box(c,"Bedroom desk chair leg",(1.30+dx,y,.154),(.035,.035,.33),m["blue"])
    for j in range(6):
        block=box(c,"Book on room study desk",(.992+.077*j,.719,.86),(.068,.169,.211),
                  m[("blue","red","gold","plaster")[j%4]],bevel=.008)
        block.rotation_euler.y=.07*(-1)**j
    box(c,"Deep blue rocket-poster outer mount",(-.52,1.289,1.78),(.83,.065,.963),m["blue"],bevel=.027)
    box(c,"Colorful rocket poster printing",(-.52,1.246,1.78),(.74,.025,.868),m["purple"])
    rocket=k.cylinder("Space rocket art white fuselage",c,(-.55,1.22,1.78),.088,.381,m["paper"],r2=.052,length_segments=18)
    rocket.rotation_euler.y=.29
    tip=k.cylinder("Rocket poster burnt-orange nose cone",c,(-.485,1.22,1.99),.063,.144,m["orange"],r2=.005,length_segments=16)
    tip.rotation_euler.y=.29
    for j in range(14):
        a=math.sin(j*12.87)
        k.ball("Printed poster star",c,(-.53+.31*a,1.221,1.389+j*.059),(.012,.009,.012),m["gold"],segments=8,rings=5)
    for z in (1.46,1.84,2.20):
        box(c,"Mounted pale wood shadow-box shelf",(.69,1.16,z),(.65,.286,.052),m["wood"],bevel=.013)
        for j in range(5):
            color=("blue","orange","cream","red")[j%4]
            book=box(c,"Painted little bedroom book jacket",(.45+j*.103,1.137,z+.108),(.081,.133,.167+.019*(j%3)),
                     m[color],bevel=.006)
            box(c,"Small contrasting book spine label",(.45+j*.103,1.061,z+.101),(.053,.019,.026),m["paper"])
    box(c,"Framed bright bedroom window",(-1.52,1.272,2.06),(.85,.10,.62),m["cream"],bevel=.021)
    box(c,"Blue sky through bedroom window",(-1.52,1.209,2.06),(.77,.031,.54),m["window"])
    for j in range(6):
        z=1.84+j*.082
        box(c,"Alternating horizontal bedroom blind",(-1.52,1.171,z),(.81,.046,.029),m["wood2"])
    door_color=k.surface("Sunny pale bedroom door","#dcccab",.86)
    box(c,"Bedroom door angle and jamb",(1.99,1.25,1.14),(.83,.12,2.26),m["wood2"],bevel=.024)
    box(c,"Tall pale interior door",(1.99,1.168,1.14),(.73,.06,2.13),door_color,bevel=.012)
    for x in (1.773,2.214):
        box(c,"Vertical door shaker panel edging",(x,1.126,1.22),(.032,.028,1.76),m["wood2"])
    for z in (.35,.84,1.31,2.09):
        box(c,"Horizontal door inset trim shelf",(1.99,1.126,z),(.442,.032,.037),m["wood2"])
    box(c,"Dark visible threshold crack",(1.99,1.129,.024),(.76,.037,.035),m["purple"])
    k.ball("Warm brass bedroom doorknob",c,(1.73,1.101,.94),(.045,.041,.039),m["gold"],segments=16,rings=8)
    basket=k.empty("Timber laundry hamper",c,(.77,.02,0))
    k.cylinder("Wicker hamper bottom",c,(0,0,.041),.244,.078,m["wood"],basket,length_segments=25)
    for i in range(27):
        a=i*math.tau/27
        line(c,"Wicker upright stave",[(.218*math.cos(a),.218*math.sin(a),.071),
             (.255*math.cos(a),.255*math.sin(a),.502)],.023,m["wood2"] if i%3 else m["cream"],basket)
    for i in range(7):
        r=.228+.0049*i
        rim(c,"Horizontal basket braid",(0,0,.094+i*.061),r,r,.020,.034,m["wood"] if i%2 else m["wood2"],basket)
        if i>0:
            for j in range(25):
                a=j*math.tau/25+.07*(i%2)
                line(c,"Over-under darker braided wicker strand",
                     [((r+.016)*math.cos(q),(r+.016)*math.sin(q),.095+i*.061+h)
                      for q,h in ((a-.07,-.012),(a,.009),(a+.07,-.007))],
                     .009,m["wood"] if i%2==0 else m["cream"],basket)
    light(c)


def underwear(c,m):
    root=k.empty("Striped underwear runner",c)
    shape=[(-.262,.181),(.255,.181),(.234,-.032),(.201,-.111),(.098,-.101),(.035,-.046),
           (-.005,-.047),(-.090,-.113),(-.201,-.112),(-.233,-.037)]
    cloth=k.surface("Primary sky-blue garment","#5e95b9",.93)
    mesh=k.mesh("Underwear soft flat striped body",c,[(x,0,z) for x,z in shape],[tuple(range(len(shape)))],cloth,root)
    mod=mesh.modifiers.new("Small soft cloth thickness","SOLIDIFY")
    mod.thickness=.047
    mod=mesh.modifiers.new("Soft hems","BEVEL")
    mod.width=.016
    mod.segments=3
    for j in range(6):
        z=.131-j*.041
        reach=.227-.013*j
        line(c,"Cream woven striping",[(-reach,-.055,z),(0,-.055,z-.007),(reach,-.055,z)],.009,m["paper"],root)
    line(c,"Yellow waistband elastic",[(-.24,-.056,.164),(0,-.058,.153),(.24,-.055,.165)],.015,m["gold"],root)
    return root


def tp_roll(c,m,j):
    pivot=k.empty(f"White toilet roll {j:02d}",c)
    rim(c,"Pristine paper roll with visible open core",(0,0,0),.093,.093,.052,.133,m["paper"],pivot)
    rim(c,"Recessed brown cardboard roll core",(0,0,0),.042,.042,.006,.13,m["cardboard"],pivot)
    for z in (-.067,.067):
        rim(c,"Thin embossed concentric paper layer",(0,0,z),.083,.083,.003,.0015,m["cream"],pivot)
    for surface in pivot.children:
        surface.modifiers.clear()
    return pivot


def avalanche(c,m):
    # Retrofit the approved wood vanity into a cupboard with hinge pivots.
    import bpy
    for obj in tuple(c.objects):
        if obj.name.startswith(("Oiled wooden vanity","Painted routed vanity drawer","Bronze pull handle")):
            bpy.data.objects.remove(obj,do_unlink=True)
        elif obj.name.startswith(("Low blue wooden footstool","Grippy birch stool-top slat")):
            obj.location.x-=.61
    a=1.02
    box(c,"Open-front bathroom vanity plinth",(a,.581,.12),(.79,.596,.118),m["wood"])
    box(c,"Finished maple cabinet rear",(a,.849,.50),(.79,.038,.80),m["wood"])
    for s in (-1,1):
        box(c,"Maple bathroom cupboard side",(a+s*.367,.567,.501),(.057,.59,.78),m["wood"],bevel=.012)
    box(c,"Lower shelf full of toilet paper",(a,.537,.232),(.742,.57,.041),m["wood2"])
    box(c,"Upper shelf full of toilet paper",(a,.555,.566),(.741,.56,.040),m["wood2"])
    doors=[]
    for s in (-1,1):
        pivot=k.empty("Cupboard door swing hinge",c,(a+s*.37,.239,.522))
        box(c,"Wide wooden cupboard door",(-s*.182,0,0),(.352,.045,.710),m["wood"],pivot,bevel=.023)
        box(c,"Raised shaker panel wood moulding",(-s*.184,-.030,0),(.270,.021,.596),m["wood2"],pivot,bevel=.020)
        box(c,"Round-edged brass action handle",(-s*.286,-.062,.037),(.032,.04,.144),m["metal"],pivot,bevel=.016)
        doors.append(pivot)
    return doors
