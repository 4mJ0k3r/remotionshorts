"""Painterly theatrical bathroom and schoolroom."""
import math

from mathutils import Vector
import ricks_v2_kit as k


def box(c,name,loc,size,mat,parent=None,bevel=0):
    x,y,z=(axis/2 for axis in size)
    corners=[(i*x,j*y,l*z) for i,j,l in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
             (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    obj=k.mesh(name,c,corners,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],mat,parent)
    obj.location=loc
    if bevel:
        mod=obj.modifiers.new("Soft manufactured edges","BEVEL")
        mod.width=bevel
        mod.segments=2
    return obj


def line(c,name,points,radius,mat,parent=None):
    obj=k.tube(name,c,points,radius,mat,parent)
    obj.data.resolution_u=2
    obj.data.bevel_resolution=1
    return obj


def text(c,label,loc,size,mat,parent=None):
    font=k.bpy.data.curves.new(label,"FONT")
    font.body=label
    font.size=size
    font.align_x="CENTER"
    font.resolution_u=5
    obj=k.put(k.bpy.data.objects.new(label,font),c,parent,mat)
    obj.location=loc
    obj.rotation_euler.x=math.pi/2
    return obj


def rim(c,name,center,rx,ry,width,thick,mat,parent=None):
    x,y,z=center
    vertices=[]
    for offset in (-thick/2,thick/2):
        for r in (0,width):
            vertices.extend((x+(rx-r)*math.cos(j*math.tau/48),y+(ry-r)*math.sin(j*math.tau/48),z+offset) for j in range(48))
    faces=[]
    for j in range(48):
        i=(j+1)%48
        faces.extend(((j,j+96,i+96,i),(48+j,48+i,144+i,144+j),(j,i,48+i,48+j),(96+j,144+j,144+i,96+i)))
    result=k.mesh(name,c,vertices,faces,mat,parent,True)
    bevel=result.modifiers.new("Porcelain edge radius","BEVEL")
    bevel.width=.012
    bevel.segments=2
    return result


def walls(c,mat,colors,*,back=1.3,width=8,height=3.2):
    box(c,"Plastered background wall",(0,back+.07,height/2),(width,.16,height),mat)
    for j in range(8):
        for i in range(30):
            if (i+j*3)%7==0:
                tile=colors[2]
            else:
                tile=colors[(i+j)%2]
            x=(i-14.5)*.266
            box(c,"Ceramic glazed wall tile",(x,back-.024,.14+j*.239),(.254,.047,.227),tile)


def bathroom(c,m):
    mint=[k.surface("Mint glazed tile "+color,color,.67) for color in ("#93c9b0","#82bdad","#a3d1b0")]
    floor=[k.surface("Mint terrazzo floor "+color,color,.77) for color in ("#aac0a9","#ccd3ad","#92aca3")]
    walls(c,m["grout"],mint,back=.94)
    box(c,"Foundation beneath bathroom floor",(0,0,-.11),(12,9,.18),m["ink"])
    for j in range(16):
        for i in range(21):
            box(c,"Offset bathroom floor porcelain",((i-10)*.39,(j-10)*.39,-.021),(.377,.377,.038),floor[(i+j*2)%3])
    box(c,"Frosted window recess",(-.71,.863,2.32),(1.01,.12,.55),m["ink"],bevel=.025)
    box(c,"Warm frosted window panes",(-.71,.790,2.32),(.92,.022,.46),m["window"])
    for x in (-1.153,-.71,-.267):
        box(c,"White frost-window mullion",(x,.75,2.32),(.038,.044,.48),m["cream"])
    for z in (2.083,2.32,2.56):
        box(c,"Wide cream sill",(-.71,.75,z),(.96,.078,.038),m["cream"])
    paper_spout=k.cylinder("Wall-mounted dark towel rail",c,(-.98,.724,1.44),.023,.64,m["metal"],length_segments=16)
    paper_spout.rotation_euler.y=math.pi/2
    for j in range(8):
        x=-1.19+j*.053
        box(c,"Soft orange hand-towel pleat",(x,.72,.999),(.064,.044+.015*(j%2),.62-.011*(j%3)),m["orange"],bevel=.014)
        box(c,"Embroidered lower cream towel welt",(x,.694,.747),(.064,.014,.023),m["cream"])
    for x in (-1.255,-.69):
        box(c,"Towel rail mounting bracket",(x,.79,1.44),(.067,.152,.067),m["metal"],bevel=.008)
    for name,pos,size in (("Ceramic toilet cistern",(0,.47,.706),(.58,.32,.59)),
                          ("Rounded ceramic tank lid",(0,.445,1.002),(.625,.348,.066)),
                          ("Ceramic glossy pedestal",(0,.065,.187),(.301,.469,.373))):
        obj=box(c,name,pos,size,m["cream"],bevel=.055)
        k.apply_prop_ink(obj,c,thickness=.003)
    k.ball("White toilet bowl",c,(0,.015,.284),(.272,.303,.171),m["cream"],segments=32,rings=19)
    k.ball("Indigo shadow inside the toilet",c,(0,.010,.421),(.195,.224,.024),m["blue"],segments=28,rings=15)
    rim(c,"Grounded porcelain toilet seat",(0,.010,.450),.285,.309,.072,.047,m["cream"])
    box(c,"Rear seat hinge under the seated pelvis",(0,.118,.447),(.284,.183,.049),m["cream"],bevel=.023)
    box(c,"Low blue wooden footstool",(0,-.412,.079),(.632,.294,.159),m["blue"],bevel=.018)
    for i in range(5):
        box(c,"Grippy birch stool-top slat",(0,-.514+i*.051,.161),(.596,.040,.012),m["wood"],bevel=.006)
    box(c,"Brushed metal cistern control",(.271,.277,.896),(.088,.054,.052),m["metal"],bevel=.009)
    vanity_x=1.02
    box(c,"Oiled wooden vanity", (vanity_x,.57,.462),(.81,.62,.91),m["wood"],bevel=.026)
    for i in range(3):
        z=.245+i*.22
        box(c,"Painted routed vanity drawer",(vanity_x,.24,z),(.67,.055,.184),m["wood"],bevel=.012)
        box(c,"Bronze pull handle",(vanity_x,.198,z),(.206,.039,.030),m["metal"],bevel=.008)
    box(c,"Cream ceramic sink counter",(vanity_x,.54,.927),(.89,.69,.091),m["cream"],bevel=.055)
    basin=k.ball("Recessed inset wash basin",c,(vanity_x,.48,.976),(.274,.201,.023),m["blue"],segments=29,rings=15)
    rim(c,"Curved ceramic basin lip",(vanity_x,.48,.981),.287,.211,.043,.031,m["cream"])
    line(c,"Arched chrome faucet",[(1.035,.745,.981),(1.035,.734,1.12),(1.035,.634,1.16),
         (1.035,.55,1.11)],.022,m["metal"])
    for radius,depth,y,mat in ((.354,.055,.84,m["wood"]),(.321,.032,.801,m["mirror"])):
        disc=k.cylinder("Round vanity mirror",c,(1.03,y,1.57),radius,depth,mat,length_segments=48)
        disc.rotation_euler.x=math.pi/2
    for j in range(3):
        box(c,"Sage glass toiletries",(1.34,.58+j*.061,1.055+j*.02),(.075,.055,.141+j*.031),mint[j],bevel=.015)
    for j in range(29):
        x=(j-14)*.262
        z=1.929
        box(c,"Celadon tile cap trim",(x,.886,z),(.25,.061,.064),m["grout"],bevel=.009)
        box(c,"Cream highlight on the tiled dado",(x,.852,z+.013),(.249,.013,.018),m["cream"])
        for i in range(2):
            box(c,"Hand-set glazed mosaic accent",(x+.075*(2*i-1),.904,1.805),
                (.055,.014,.053),mint[(i+j)%3] if j%2 else m["cream"])
    # Roll with open inner cylinder, rotating with its seam around a fixed bracket.
    pivot=k.empty("Wall roll spin pivot",c,(.57,.11,.916))
    tube=rim(c,"Empty corrugated cardboard core",(0,0,0),.061,.061,.010,.196,m["cardboard"],pivot)
    tube.rotation_euler.y=math.pi/2
    for j in range(9):
        angle=j*math.tau/9
        y,z=.061*math.cos(angle),.061*math.sin(angle)
        line(c,"Visible longitudinal cardboard fiber", [(-.095,y,z),(.095,y,z)],.00175,m["wood"],pivot)
    for x in (.444,.697):
        line(c,"Brass roll-spindle bracket",[(x,.211,.915),(x,.120,.915),(x,.110,.915)],.014,m["metal"])
    k.make_ricks_light("Warm sunlight outside frosted bathroom glass",c,(-.62,.12,2.58),(.27,-.33,1.13),"#ffd196",282,.62)
    k.make_ricks_light("Soft bathroom cream practical",c,(-1.21,-1.32,2.47),(0,.09,.93),"#fff1d3",231,1.05)
    k.make_ricks_light("Cool porcelain window bounce",c,(2,-1.2,1.95),(0,.18,1.12),"#afddf4",94,1.55)
    k.make_light_cone("Soft tilted warm shaft from high window",c,(-.72,.73,2.33),(.10,-.81,.46),.18,.62,"#ffcc9b")
    return pivot


def desk(c,m,center):
    x,y=center
    box(c,"Warm timber desk top",(x,y-.51,.725),(.72,.439,.060),m["wood"],bevel=.017)
    box(c,"Wooden front desk apron",(x,y-.722,.627),(.685,.070,.16),m["wood"],bevel=.012)
    for side in (-1,1):
        xx=x+side*.306
        for yy in (y-.72,y-.31):
            box(c,"Steel desk tubular frame",(xx,yy,.335),(.036,.035,.67),m["blue"],bevel=.013)
        line(c,"Chair rear welded frame",[(x+side*.166,y+.15,.02),(x+side*.166,y+.15,.47),
             (x+side*.166,y+.188,.80)],.017,m["metal"])
    box(c,"Stamped plywood seat",(x,y+.036,.443),(.424,.337,.058),m["blue"],bevel=.026)
    box(c,"School chair powder-blue back",(x,y+.210,.683),(.384,.06,.29),m["blue"],bevel=.025)
    for i in range(3):
        box(c,"Ruled exercise pages", (x-.15,y-.51,.759+i*.007),(.176,.179,.006),m["cream"])
    book=box(c,"Colorful notebook wrap",(x-.15,y-.515,.782),(.189,.185,.015),m["orange"],bevel=.004)
    line(c,"Sharpened yellow school pencil",[(x+.043,y-.50,.769),(x+.224,y-.548,.769)],.008,m["gold"])


def classroom(c,m):
    box(c,"Warm ochre classroom plaster",(0,2.45,1.67),(10,.20,3.35),m["plaster"])
    box(c,"Classroom parquet floor",(0,.2,-.13),(12,11,.24),m["wood"])
    for i in range(31):
        x=(i-15)*.285
        for j in range(5):
            box(c,"School parquet inset plank",(x,(j-2)*1.59+(i%2)*.38,-.009),(.276,1.58,.022),
                m[("wood","wood2","wood")[i%3]])
    box(c,"Dark lower school skirting",(0,2.29,.11),(9,.105,.206),m["blue"])
    bx=-.83
    box(c,"Wide maple whiteboard frame",(bx,2.23,1.54),(2.89,.15,1.66),m["wood"],bevel=.036)
    box(c,"Warm cream whiteboard writing surface",(bx,2.14,1.55),(2.72,.06,1.49),m["cream"])
    text(c,"THE WATER CYCLE",(bx,2.096,2.07),.181,m["blue"])
    for name,x,z,color in (("EVAPORATION",bx-.83,1.32,"orange"),("CONDENSATION",bx,1.75,"blue"),("RAIN",bx+.83,1.34,"blue")):
        text(c,name,(x,2.09,z),.083,m[color])
    for j in range(3):
        x=bx+(j-1)*.14
        k.ball("Condensation cloud drawn in 3D chalk",c,(x,2.09,1.56),(.125,.008,.067),m["blue"],segments=14,rings=8)
    for j in range(8):
        x=bx+.24+.082*j
        z=1.47-.037*(j%3)
        line(c,"Blue rain slash in whiteboard drawing",[(x,2.089,z),(x-.041,2.089,z-.073)],.012,m["blue"])
    for j in range(3):
        x=bx-.86+j*.11
        line(c,"Curved orange evaporation arrow",[(x-.035,2.086,1.46),(x-.043,2.086,1.57),
             (x+.008,2.086,1.67),(x+.019,2.085,1.74)],.009,m["orange"])
    for j in range(4):
        z=1.10-j*.033
        line(c,"Chalk blue water ripple",[(bx-.78+i*.17,2.087,z+.027*math.sin(i*.8+j*.3)) for i in range(10)],.009,m["blue"])
    for j in range(4):
        x=1.03+j*.331
        for z in (.39,1.16):
            block=box(c,"Alternating cobalt and golden lockers",(x,2.091,z),(.306,.309,.742),
                      m["blue"] if j%2==0 else m["gold"],bevel=.014)
            for i in range(4):
                box(c,"Pressed school locker louvres",(x,1.928,z+.185+i*.031),(.197,.017,.010),m["ink"])
            box(c,"Recessed locker pull",(x+.095,1.923,z-.093),(.04,.023,.10),m["metal"],bevel=.005)
    clock=k.cylinder("Classroom analog clock",c,(1.24,2.16,2.326),.247,.081,m["cream"],length_segments=38)
    clock.rotation_euler.x=math.pi/2
    for i in range(12):
        a=i*math.tau/12
        line(c,"Analog clock hour mark",[(1.24+.192*math.sin(a),2.11,2.326+.192*math.cos(a)),
             (1.24+.215*math.sin(a),2.11,2.326+.215*math.cos(a))],.009,m["ink"])
    line(c,"Clock hands",[(1.13,2.103,2.39),(1.24,2.102,2.326),(1.29,2.103,2.46)],.014,m["ink"])
    box(c,"Cork noticeboard",(-2.78,2.201,1.81),(.863,.15,1.03),m["wood"],bevel=.027)
    for i in range(8):
        x=-3.06+(i%3)*.257
        z=2.14-(i//3)*.287
        box(c,"Pinned paper study graphic",(x,2.111,z),(.198,.025,.22),m[("cream","gold","orange")[i%3]])
        for j in range(3):
            box(c,"Short ink line on study card",(x,2.094,z+.043-j*.037),(.126,.012,.009),m["blue"])
    for center in ((0,0),(.86,.15),(-1.43,.52),(1.75,.53),(-2.,1.12)):
        desk(c,m,center)
    k.make_ricks_light("Sunny classroom key",c,(-1.72,-.72,2.84),(.35,.50,.89),"#ffd198",330,1.13)
    k.make_ricks_light("Honey rim on teacher and blue lockers",c,(2.28,1.51,2.63),(-.53,.63,1.23),"#ffe3b4",264,.73)
    k.make_ricks_light("Cool open door fill",c,(1.5,-1.4,2.44),(.3,.22,1.1),"#b6d5ff",125,1.68)
    sun=k.bpy.data.lights.new("Crisp morning sun from school windows","SUN")
    sun.color=k.look.rgba("#ffe1b2")[:3]
    sun.energy=1.28
    sun.angle=.022
    k.aim(k.put(k.bpy.data.objects.new(sun.name,sun),c),Vector((4.2,5,-2.5)))
