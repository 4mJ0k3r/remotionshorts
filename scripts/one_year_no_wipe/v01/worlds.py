"""Disco stage, transit, florist, and the final bedroom props."""
import math
from random import Random

from mathutils import Vector
import ricks_v2_kit as k
from sets import box, line, rim, text


def light(c,warm="#ffcb8e",cool="#91c6f4"):
    k.make_ricks_light("Warm window key",c,(-2.6,-2.8,3.25),(0,.11,1),warm,431,1.6)
    fill=k.make_ricks_light("Cool reflected bounce",c,(2.3,-1.3,2.5),(0,.34,1.12),cool,173,1.6)
    rim=k.make_ricks_light("Warm edge on practical surfaces",c,(1.9,1.47,2.69),(0,.31,1.2),"#ffe1a7",211,.8)
    fill.data.use_shadow=rim.data.use_shadow=False


def micro(c,m,disco=True):
    terrain=k.texture("Combed abstract velvet skin terrain",("#41283e","#955975","#c17b84"),"plaster",(.76,.93))
    back=k.emission("Deep plum microscope backdrop","#312048",.71)
    box(c,"Soft deep gradient backdrop",(0,4.2,2.24),(18,.22,4.48),back)
    box(c,"Abstract skin floor",(0,.40,-.11),(14,11,.219),terrain)
    colors=[k.surface("Microscope terrain texture "+color,color,.84) for color in (
        "#a46980","#744961","#bc7483","#553754","#eba7a0")]
    rng=Random(1108)
    for j in range(172):
        x,y=rng.uniform(-6,6),rng.uniform(-2.5,3.9)
        if y<.8 and abs(x)<2 and j%3==0:
            continue
        r=rng.uniform(.042,.24)
        k.ball("Raised softly rounded microscope texture",c,(x,y,-.017), (r,r*.9,r*.42),colors[j%5],segments=10,rings=6)
    for j in range(27):
        x,y=rng.uniform(-5,5),rng.uniform(1.65,4)
        line(c,"Thin abstract texture stroke",[(x,y,.005),(x+.12,y+.07,.078),(x+.19,y+.19,.11)],.012,colors[j%5])
    contour=[k.emission("Clean dried mauve ridges "+tone,tone,.93) for tone in ("#8c4a7f","#eba0ab","#a75f91")]
    for j in range(42):
        y=-3.2+j*.105
        stroke=line(c,"Paired abstract skin crease",[(x,y+.062*math.sin(x*2.3+j*.27),.010+.002*math.sin(i))
                     for i,x in enumerate(-4.8+.29*n for n in range(34))],.017,contour[j%3])
        stroke.visible_shadow=False
    backlit=[k.emission("Colored patterned microscope wall line",tone,1.3) for tone in (
        "#9776c9","#cb73a3","#6898d4")]
    for j in range(28):
        x=(j-13.5)*.318
        for i,z in enumerate((.47,.88,1.29,1.7,2.11,2.52,2.93,3.34)):
            y=3.30
            ripple=.127+.033*math.sin(j*1.7+i)
            if disco:
                line(c,"Depth-of-field neon venue scale motif",[(x-ripple,y,z-.063),(x,y,z+.06),
                     (x+ripple,y,z-.062)],.022,backlit[(j+i)%3])
            else:
                line(c,"Microscope environment hex-indicator",[(x-.115,y,z),(x-.057,y,z+.08),
                     (x+.055,y,z+.08),(x+.112,y,z)],.024,backlit[(j+i)%3])
    for j in range(8):
        z=.32+j*.41
        line(c,"Far microscope illuminated stage ledge",[(-5.8,3.34,z),(5.8,3.34,z)],.018,backlit[j%3])
    for j in range(53):
        x,y,z=rng.uniform(-6,6),rng.uniform(2.30,3.8),rng.uniform(.14,3.60)
        r=rng.uniform(.013,.042)
        k.ball("Lavender microcosm bokeh bead",c,(x,y,z),(r,r,r),
               m["blue"] if j%3 else m["gold"],segments=9,rings=6)
    light(c,"#f1b5a4","#aa97ff")
    if disco:
        for x,z,color in ((-1.76,2.79,"#ff79cc"),(1.79,2.80,"#74f5ff"),(.35,3.17,"#ffca59")):
            k.make_ricks_light("Rotating disco spot",c,(x,1.67,z),(x*.3,-.53,.14),color,185,.14,"SPOT")
            k.make_light_cone("Disco split prism cone",c,(x,1.66,z),(x*.19,-.29,.29),.045,.39,color)


def eyes(c,p,m,scale=1.,dark=False):
    for side in (-1,1):
        x=side*.081*scale
        k.ball("Dark espresso outer eye",c,(x,-.147*scale,.048*scale),
               (.063*scale,.034*scale,.067*scale),m["purple"],p,13,8)
        k.ball("White sclera",c,(x,-.171*scale,.050*scale),
               (.050*scale,.025*scale,.053*scale),m["paper"],p,13,8)
        k.ball("Big dark pupil",c,(x+.011*scale,-.192*scale,.048*scale),
               (.023*scale,.010*scale,.026*scale),m["purple"],p,10,7)
        if dark:
            box(c,"Violet party sunglasses", (x,-.209*scale,.060*scale),(.125*scale,.018,.092*scale),
                m["purple"],p,bevel=.013)
    line(c,"Inked cheerful creature smile",[(-.046*scale,-.160*scale,-.04*scale),
         (0,-.183*scale,-.064*scale),(.046*scale,-.160*scale,-.035*scale)],.008*scale,m["purple"],p)


def germ(c,m,j):
    root=k.empty("Dancing green cartoon germ",c)
    shade=("#85da5c","#a5e45d","#57c781","#6bdb99")[j%4]
    skin=k.surface("Pearlescent green bacterium "+shade,shade,.83,glow=.12)
    body=k.ball("Rounded lime microbe",c,(0,0,0),(.180,.164,.198),skin,root,23,14)
    k.apply_prop_ink(body,c,thickness=.005)
    for i in range(7):
        a=i*math.tau/7
        r=.039+.007*(i%2)
        k.ball("Cute soft membrane knob",c,(.154*math.cos(a),.036,.180*math.sin(a)),(r,r,r),skin,root,11,7)
    eyes(c,root,m,1.,dark=j%4==1)
    for s in (-1,1):
        line(c,"Stick creature party arm",[(s*.136,0,-.02),(s*.235,0,.029),(s*.265,-.008,.094)],.013,m["purple"],root)
        line(c,"Stick creature party foot",[(s*.072,0,-.165),(s*.113,-.018,-.229),(s*.156,-.058,-.235)],.013,m["purple"],root)
    if j%3==0:
        party=k.cylinder("Tiny coral party hat",c,(.037,.014,.238),.084,.127,m["orange"],root,
                         r2=.012,length_segments=14)
        party.rotation_euler.y=.19
        k.ball("Party hat pom pom",c,(.051,.014,.312),(.029,.028,.027),m["gold"],root,12,7)
    return root


def disco_ball(c,m):
    root=k.empty("Mirror-ball pivot",c)
    body=k.ball("Mirrored disco sphere",c,(0,0,0),(.31,.31,.31),m["metal"],root,24,15)
    line(c,"Ceiling suspension cable",[(0,0,.28),(0,0,2)],.012,m["purple"],root)
    for j in range(6):
        elev=(j-2.5)*.34
        for i in range(14):
            angle=(i+.26*(j%2))*math.tau/14
            point=Vector((math.cos(elev)*math.cos(angle),math.cos(elev)*math.sin(angle),math.sin(elev)))
            material=k.emission("Mosaic disco facet",("#a9cdf7","#ffe7b3","#dcd3e7","#e8b6d9")[(i+j)%4],.8+.27*((i*3+j)%5))
            shard=box(c,"Colored beveled mirror facet",point*.306,(.095,.095,.017),material,root,bevel=.006)
            shard.rotation_mode="QUATERNION"
            shard.rotation_quaternion=point.to_track_quat("Z","Y")
    return root


def mushroom(c,m,j):
    root=k.empty("Purple mushroom tourist",c)
    cap=k.surface("Mulberry cap pigment",("#a058bb","#8456a5","#af69cd")[j%3],.76)
    stem=k.ball("Cream oval face and stem",c,(0,0,.09),(.139,.138,.204),m["cream"],root,19,13)
    hat=k.ball("Flared violet mushroom cap",c,(0,.01,.258),(.243,.215,.149),cap,root,25,15)
    k.apply_prop_ink(hat,c,thickness=.005)
    for x,y,z,r in ((-.112,-.10,.34,.038),(.102,-.109,.344,.048),(.019,-.153,.340,.027),(.02,.029,.409,.046)):
        k.ball("Pale mauve cap marking",c,(x,y,z),(r,r*.66,r*.32),m["paper"],root,12,8)
    face=k.empty("Mushroom tourist face",c,(0,0,.115),root)
    eyes(c,face,m,.76)
    arms=[]
    for sign in (-1,1):
        arm=k.empty("Tourist swinging foot",c,(sign*.062,0,-.05),root)
        line(c,"Tourist boot stick",[(0,0,0),(sign*.023,-.01,-.08),(sign*.049,-.046,-.105)],.012,m["purple"],arm)
        arms.append(arm)
    line(c,"Suitcase-carrying arm",[(.111,0,.103),(.198,-.024,.071),(.254,-.04,.034)],.015,m["purple"],root)
    box(c,"Toffee-brown travel suitcase",(.252,-.034,-.018),(.143,.089,.136),m["wood"],root,bevel=.020)
    line(c,"Rounded suitcase carrying handle",[(.217,-.057,.043),(.226,-.057,.075),(.278,-.057,.075),(.292,-.057,.043)],.008,m["gold"],root)
    return root,arms


def bus(c,m):
    rail=k.surface("Bus brushed bronze rails","#b0a17d",.63,.16)
    box(c,"Blue stippled bus floor",(0,0,-.102),(4.3,10,.201),m["blue"])
    box(c,"Warm transit floor safety aisle",(0,-.15,.001),(1.16,8,.012),m["wood2"])
    box(c,"Bus ceiling",(0,.0,2.55),(4.3,9,.15),m["cream"])
    box(c,"Blue front bus bulkhead",(0,3.80,1.36),(4.18,.22,2.76),m["blue"])
    fabric=k.surface("Powder-coated blue bus panels","#4e84a6",.79,glow=.08)
    aisle=k.surface("Speckled cream bus aisle","#dcc7a3",.83,glow=.06)
    for i in range(36):
        y=(i-17.5)*.220
        box(c,"Rounded aisle anti-slip insertion",(0,y,.014),(1.11,.207,.025),aisle if i%2 else m["wood2"])
        for side in (-1,1):
            box(c,"Yellow dotted edge of transit aisle",(side*.539,y,.031),(.031,.092,.009),m["gold"])
    for side in (-1,1):
        for y in [-3.4,-2.02,-.64,.74,2.12,3.50]:
            box(c,"Sturdy window mullion",(side*1.94,y,1.63),(.172,.146,1.78),m["blue"],bevel=.013)
        for z,height in ((.395,.81),(2.368,.39)):
            box(c,"Transit window sill rail",(side*1.95,.01,z),(.17,8.5,height),fabric)
        for z in (.726,.797,2.18,2.265):
            line(c,"Reflecting brushed aluminum window track",[(1.84*side,-3.7,z),(1.84*side,3.64,z)],.019,m["paper"])
        for y in (-2.8,-.40,1.37,2.83):
            x=side*1.36
            k.ball("Royal blue upholstered bus cushion",c,(x,y,.46),(.42,.36,.117),m["blue"],segments=17,rings=9)
            k.ball("Royal blue rounded bus backrest",c,(x,y+.296,.82),(.426,.133,.409),m["blue"],segments=19,rings=11)
            for j in range(3):
                line(c,"Cream-lit bus fabric stitch",[(x-.22+j*.215,y+.17,.69),(x-.22+j*.215,y+.17,1.068)],.010,m["paper"])
        line(c,"Continuous cream grab rail",[(side*.77,-3.5,2.18),(side*.77,3.5,2.18)],.03,rail)
        for j in range(6):
            y=-2.57+j*.89
            anchor=1.49 if side==1 and j==3 else 1.84
            line(c,"Yellow transit overhead triangular strap",[(side*.77,y,2.17),(side*.67,y,anchor),
                 (side*.86,y,anchor),(side*.77,y,2.17)],.020,m["gold"])
    for y in (-2.2,-.52,1.16,2.84):
        box(c,"Warm cream overhead light panel",(0,y,2.459),(.59,.41,.032),m["window"])
    box(c,"Next stop LED sign base",(0,3.642,2.02),(.983,.12,.24),m["purple"],bevel=.035)
    text(c,"NEXT STOP",(0,3.567,1.979),.127,m["gold"])
    buildings=k.empty("Looping buildings outside bus windows",c)
    sky=k.emission("Blue day outside bus windows","#96c6ea",.91)
    for side in (-1,1):
        box(c,"Clear blue city sky beyond bus",(side*4.14,0,1.76),(.15,29,4.36),sky)
        for j in range(17):
            y=(j-8)*1.54
            box(c,"Brick blocks passing beyond windows",(side*3.20,y,1.32),(.47,1.41,2.65),
                m["wood2"] if j%2 else m["plaster"],buildings)
            for dy in (-.39,.34):
                for z in (.94,1.61,2.22):
                    box(c,"Clean window casing",(side*2.960,y+dy,z),(.020,.40,.47),m["cream"],buildings)
                    box(c,"Blue city window",(side*2.941,y+dy,z),(.026,.32,.35),m["blue"],buildings)
    light(c)
    lamp=k.make_ricks_light("Interior bus front softbox",c,(.68,-2.14,2.13),(.58,.34,1.1),"#ffd9a4",251,1.14)
    lamp.data.use_shadow=False
    return buildings


def vapor(c,m,count=12):
    mist=k.emission("Translucent sea-green comic scent strokes","#a6d994",.80)
    mist.surface_render_method="BLENDED"
    tree=mist.node_tree
    em=next(node for node in tree.nodes if node.type=="EMISSION")
    out=next(node for node in tree.nodes if node.type=="OUTPUT_MATERIAL")
    trans=tree.nodes.new("ShaderNodeBsdfTransparent")
    mix=tree.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value=.22
    for a,b in ((trans.outputs[0],mix.inputs[1]),(em.outputs[0],mix.inputs[2]),(mix.outputs[0],out.inputs[0])):
        tree.links.new(a,b)
    root=k.empty("Airy stink lines mover",c)
    for j in range(count):
        x=((j*37)%13-6)*.09
        z=((j*13)%17)*.056
        stroke=line(c,"Translucent rising scent curl",[(x+.042*math.sin(i*.81+j),-.06*(j%4),z+i*.038)
                    for i in range(10)],.011+.002*(j%3),mist,root)
        stroke.visible_shadow=False
    return root


def street(c,m,florist=False):
    brick=k.surface("Terracotta bonded street walls","#b57256",.83)
    tree=brick.node_tree
    coords=tree.nodes.new("ShaderNodeTexCoord")
    axes=tree.nodes.new("ShaderNodeSeparateXYZ")
    plane=tree.nodes.new("ShaderNodeCombineXYZ")
    mortar=tree.nodes.new("ShaderNodeTexBrick")
    mortar.inputs["Color1"].default_value=k.look.rgba("#9b5545")
    mortar.inputs["Color2"].default_value=k.look.rgba("#be8163")
    mortar.inputs["Mortar"].default_value=k.look.rgba("#ead1a5")
    mortar.inputs["Scale"].default_value=2.7
    mortar.inputs["Brick Width"].default_value=.29
    mortar.inputs["Row Height"].default_value=.108
    mortar.inputs["Mortar Size"].default_value=.008
    tree.links.new(coords.outputs["Generated"],axes.inputs[0])
    tree.links.new(axes.outputs["X"],plane.inputs["X"])
    tree.links.new(axes.outputs["Z"],plane.inputs["Y"])
    tree.links.new(plane.outputs[0],mortar.inputs["Vector"])
    tree.links.new(mortar.outputs["Color"],next(n for n in tree.nodes if n.type=="BSDF_PRINCIPLED").inputs["Base Color"])
    sky=k.emission("Soft clear sky behind the street","#92c6df",1)
    box(c,"Continuous blue outdoor sky",(0,11.5,4),(32,.27,9.5),sky)
    box(c,"Paved walking area",(0,-.7,-.092),(18,12,.18),m["plaster"])
    for i in range(29):
        x=(i-14)*.49
        for j in range(9):
            box(c,"Broad clean limestone pavers",(x,(j-5)*.56,-.019),(.474,.544,.036),m[("plaster","cream","plaster")[(i+2*j)%3]])
    for j in range(6):
        x=(j-2.5)*2.66
        height=3.03+.67*(j%2)
        box(c,"Three-dimensional brick terrace",(x,2.5,height/2),(2.62,.36,height),brick)
        for z in (1.82,2.55):
            for dx in (-.73,.10,.82):
                box(c,"Cream framed windows",(x+dx,2.29,z),(.57,.081,.57),m["cream"],bevel=.011)
                box(c,"Blue window inset",(x+dx,2.242,z),(.49,.036,.47),m["blue"])
                box(c,"Narrow centre window muntin",(x+dx,2.217,z),(.028,.028,.47),m["cream"])
        box(c,"Dark roof ridge trim",(x,2.43,height+.03),(2.64,.52,.116),m["wood"])
    foliage=k.surface("Layered moss-green topiary leaves","#5f9b5b",.89)
    for j in range(5):
        x=-4.6+j*2.29
        line(c,"Thin knotted tree trunk",[(x,2.12,0),(x+.05,2.11,1.05),(x+.10,2.09,1.54)],.059,m["wood"])
        for i in range(5):
            k.ball("Organic topiary canopy lobe",c,(x+.34*math.sin(i*2.13),2.08+.17*math.cos(i*2.13),1.69+.13*(i%3)),
                   (.37,.33,.32),foliage,segments=12,rings=7)
    if florist:
        box(c,"Florist pale cream signboard",(0,1.56,2.30),(3.16,.24,.42),m["blue"],bevel=.044)
        text(c,"FLOWER SHOP",(0,1.42,2.21),.189,m["paper"])
        for j in range(15):
            x=(j-7)*.205
            strip=box(c,"Alternating cloth awning stripe",(x,1.27,2.02),(.209,.682,.046),
                      m["red"] if j%2==0 else m["paper"],bevel=.014)
            strip.rotation_euler.x=.24
            box(c,"Florist awning scalloped trim",(x,.931,1.926),(.205,.062,.132),
                m["red"] if j%2==0 else m["paper"],bevel=.03)
        box(c,"Florist cream door framing",(-.73,1.80,1.02),(.76,.14,1.84),m["cream"],bevel=.032)
        box(c,"Blue storefront door glass",(-.73,1.716,1.02),(.62,.039,1.68),m["blue"])
        box(c,"Wood display ledge",(0,1.17,.47),(3.10,.52,.11),m["wood"],bevel=.018)
    light(c)


def flower(c,m,j,parent=None):
    stalk=k.empty("Wiltable potted flower stem",c,parent=parent)
    y=.0
    green=k.surface("Fresh leaf green","#61904b",.78)
    color=k.surface("Showy painted blossom",("#d96296","#ed7853","#bb86dc","#e5c34a")[j%4],.81,glow=.075)
    line(c,"Curved flower stalk",[(0,0,0),(.016,0,.17),(.035,0,.34)],.019,green,stalk)
    for s in (-1,1):
        leaf=k.ball("Satin leaf",(c),(.05*s,0,.17),(.084,.016,.028),green,stalk,14,8)
        leaf.rotation_euler.y=.39*s
    for i in range(6):
        a=i*math.tau/6
        k.ball("Glossy warm flower petal",c,(.030+.077*math.cos(a),y,.343+.08*math.sin(a)),(.055,.027,.054),color,stalk,13,8)
    k.ball("Golden flower stigma",c,(.030,-.041,.343),(.060,.024,.058),m["gold"],stalk,16,9)
    sad=k.empty("Tiny frown on wilted bloom",c,(.030,-.067,.342),stalk)
    for x in (-.022,.022):
        k.ball("Tiny sad petal eye",c,(x,0,.012),(.006,.005,.009),m["purple"],sad,9,6)
    line(c,"Small frowning petal mouth",[(-.025,0,-.028),(0,-.003,-.017),(.025,0,-.027)],.005,m["purple"],sad)
    return stalk,sad
