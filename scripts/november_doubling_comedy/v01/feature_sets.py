"""Practical scale-comedy sets for the café, city and orbit."""
import math
from random import Random

import bpy
import ricks_v2_kit as k
from sets import box, cylinder, stroke, text


def area(col, warm="#ffd298", cool="#a6c8ff"):
    k.make_ricks_light("Angled warm window",col,(-2.4,-1.18,4.2),(0,.3,1),warm,510,1.4)
    l=k.make_ricks_light("Blue set reflection",col,(2.1,1.48,3.5),(0,-.2,1.05),cool,280,1.16)
    l.data.use_shadow=False


def inlay(c,kind):
    """A continuous inlaid herringbone floor designed to survive portrait blur."""
    tones = ("#754e52","#ba826b","#dbac7c") if kind!="office" else ("#394966","#6c8098","#b7a9ae")
    vertices=[[],[],[]]
    faces=[[],[],[]]
    for y in range(-27,30):
        for x in range(-21,22):
            px=x*.239+(y%2)*.12
            py=y*.155
            i=(x+2*y)%3
            slope=(-1 if x%2 else 1)*.045
            index=len(vertices[i])
            vertices[i].extend(((px,py,.007),(px+.181,py+slope,.007),
                                (px+.181,py+slope+.021,.007),(px,py+.021,.007)))
            faces[i].append(tuple(range(index,index+4)))
    for i,color in enumerate(tones):
        k.mesh("Fine herringbone floor inlay",c,vertices[i],faces[i],
               k.emission("Waxed inlay "+color,color,1.05)).visible_shadow=False


def room(c,m,kind):
    wall=m["paint"] if kind=="safe" else m["night"] if kind=="office" else m["plum"]
    wall_height=7.0 if kind=="door" else 4.2
    box(c,"Deep painterly set wall",(0,3.0,wall_height*.5),(13,.18,wall_height),wall)
    box(c,"Solid set floor",(0,0,-.098),(16,12,.194),m["wood"] if kind!="office" else m["rubber"])
    edge=k.emission("Dim floor trim","#6d7890" if kind=="office" else "#917079",.82)
    for j in range(25):
        x=(j-12)*.365
        stroke(c,"Thin flooring channel",[(x,-4,.003),(x,4.4,.003)],.006,edge)
        for i in range(6):
            y=(i-2)*.91+.24*(j%2)
            stroke(c,"Offset flooring end joint",[(x,y,.004),(x+.36,y,.004)],.004,edge)
    for j in range(32):
        x=(j-15.5)*.33
        box(c,"Recessed architectural wall slat",(x,2.877,1.53),(.032,.05,2.92),m["roof"] if j%3 else m["gold"])
    for z in (.12,.69,2.93):
        box(c,"Wall continuous rail",(0,2.864,z),(12,.06,.052),m["ink"])
    inlay(c,kind)
    area(c)
    for j,x in enumerate((-1.9,1.85)):
        box(c,"Deep warm window sash",(x,2.81,1.97),(1.35,.22,1.58),m["wood"],bevel=.043)
        box(c,"Daylight through tall glass",(x,2.674,1.97),(1.21,.038,1.44),m["window"])
        for z in (1.33,1.68,2.02,2.37,2.64):
            box(c,"Window horizontal mullion",(x,2.642,z),(1.27,.056,.038),m["roof"])
        for dx in (-.57,0,.57):
            box(c,"Tall window vertical mullion",(x+dx,2.638,1.96),(.035,.052,1.40),m["roof"])
    for x in (-2.4,2.6):
        cylinder(c,"Ceramic plant pot",(x,1.75,.155),.152,.31,m["cork"],top=.198)
        for j in range(8):
            leaf=k.ball("Oval painted plant leaves",c,(x+.25*math.sin(j*2.4),1.75+.14*math.cos(j*2.4),.58+.17*(j%4)),
                        (.18,.08,.26),m["turf"],segments=12,rings=8)
            leaf.rotation_euler.y=.44*math.sin(j*2.4)


def cafe(c,m):
    room(c,m,"cafe")
    box(c,"Ivory café counter",(0,.35,.455),(1.48,.46,.91),m["wood"],bevel=.045)
    for x in (-.65,-.53,-.41,-.29,-.17,-.05,.07,.19,.31,.43,.55,.67):
        box(c,"Oak counter front fluting",(x,.101,.446),(.047,.035,.78),m["gold"])
    box(c,"Stone counter lip",(0,.31,.932),(1.61,.62,.061),m["cream"],bevel=.023)
    box(c,"Slate menu sign",(0,2.758,2.20),(1.91,.052,.79),m["rubber"],bevel=.052)
    text(c,"COFFEE",(0,2.716,2.30),.222,m["shade"])
    for i in range(4):
        box(c,"Small cream menu stroke",(0,2.717,2.23-i*.105),(1.23-.13*(i%2),.012,.019),m["cream"])
    box(c,"Professional coffee machine",(-.87,1.42,.956),(.67,.38,.58),m["metal"],bevel=.023)
    for i in range(3):
        cylinder(c,"Knurled espresso machine dial",(-1.04+i*.17,1.193,1.044),.043,.03,m["gold"],axis="Y")
    for x in (-1.24,1.24):
        stroke(c,"Cable to low pendant",[(x,1.73,2.79),(x,1.73,2.273)],.014,m["ink"])
        cylinder(c,"Gold pendant", (x,1.73,2.21),.172,.119,m["shade"],top=.069)
        k.make_light_cone("Pendant glow on the espresso counter",c,(x,1.73,2.16),(x,1.73,.55),
                          .085,.51,"#ffd0a5")


def mug(c,m):
    parent=k.empty("Token #47 white paper cup",c)
    cylinder(c,"Matte white café cup",(0,0,.043),.105,.246,m["cream"],parent,top=.125,segments=32)
    cylinder(c,"White takeaway cup lid",(0,0,.174),.127,.032,m["cream"],parent,segments=30)
    for i in range(4):
        cylinder(c,"Subtle embossed cup rim",(0,0,.120+i*.012),.123,.004,m["gold"],parent,segments=30)
    accent=k.emission("Café red printing ink","#b42f38",.92)
    text(c,"#47",(0,-.127,.013),.095,accent,parent)
    for z in (-.051,-.040,-.031,.097,.105):
        cylinder(c,"Small crimson café cup stripe",(0,0,z),.106+(z+.080)*.02/.246,.0035,accent,
                 parent,segments=35)
    for j in range(14):
        t=j*math.tau/14
        radius=.123
        x,y=radius*math.cos(t),radius*math.sin(t)
        stroke(c,"Printed café cup sleeve chevron",[(x+.012*math.sin(t),y-.012*math.cos(t),.116),
               (x,y,.125),(x-.012*math.sin(t),y+.012*math.cos(t),.116)],.0023,accent,parent)
    return parent


def office(c,m):
    room(c,m,"office")
    for i,x in enumerate((-2.3,-1.28,.86,2.18)):
        box(c,"Fabric-wrapped glass office cubicle",(x,1.64,.624),(.91,.165,1.25),m["blue"] if i%2 else m["turf"],bevel=.019)
        box(c,"Pale horizontal desk accent",(x,1.52,.969),(.85,.046,.041),m["cream"])
        box(c,"Office monitor stand",(x,1.32,1.078),(.35,.23,.26),m["ink"],bevel=.025)
        box(c,"Teal monitor screen",(x,1.197,1.12),(.285,.02,.171),m["window"])
        for j in range(3):
            box(c,"Thin monitor UI stroke",(x,1.179,1.081+j*.035),(.173,.012,.010),m["lightblue"])
    for z in (1.50,1.83,2.16,2.49):
        stroke(c,"Frosted glass wrap line",[(-3.6,1.69,z),(3.6,1.69,z)],.014,m["lightblue"])


def door(c,m):
    room(c,m,"door")
    for x in (-1.49,1.49):
        box(c,"Warm textured plaster around doorway",(x,.67,1.42),(1.04,.27,2.83),m["plum"],bevel=.031)
        for j in range(6):
            box(c,"Brass-plaster relief on apartment jamb",(x-.47+j*.18,.515,1.43),(.023,.044,2.8),m["cork"])
    for x in (-.939,.939):
        box(c,"Warm wood doorway upright",(x,.46,1.43),(.112,.252,2.853),m["wood"],bevel=.022)
    box(c,"Warm doorway head lintel",(0,.46,2.84),(1.991,.252,.122),m["wood"],bevel=.027)
    for x in (-1.38,1.37):
        cylinder(c,"Gold hallway sconce",(x,.33,2.16),.113,.255,m["shade"],top=.146)
    for x in (-2.17,0,2.17):
        box(c,"Upper framed hall light", (x,2.73,4.14),(1.91,.24,1.88),m["wood"],bevel=.036)
        box(c,"Soft cobalt clerestory glass",(x,2.571,4.14),(1.72,.065,1.72),m["window"])
        for dx in (-.72,-.50,-.26,0,.26,.50,.72):
            box(c,"Vertical ribbed clerestory mullion",(x+dx,2.532,4.14),(.038,.082,1.72),m["gold"])
        for z in (3.34,3.68,4.02,4.36,4.70,4.96):
            box(c,"Horizontal clerestory astragal",(x,2.504,z),(1.72,.092,.046),m["roof"])
    for z in (3.09,3.19,5.15,5.23,5.32,5.42):
        box(c,"Apartment decorative panel belts",(0,2.60,z),(13,.13,.052),m["gold"] if z in (3.19,5.23) else m["wood"])


def pads(c,m,diameter,center,*,spacing=.80):
    root=k.empty("Twin fully clothed fabric forms",c,center)
    cloth=k.texture("Heather-grey woven sweatpant fabric",("#454c60","#6b7488","#a3aab6"),"plaster",(.87,.96))
    for side in (-1,1):
        x=side*diameter*spacing*.5
        ball=k.ball("Matte heather-grey fabric sphere",c,(x,0,0),(diameter*.5,diameter*.5,diameter*.5),cloth,root,
                    29,18)
        k.apply_prop_ink(ball,c,thickness=min(.04,diameter*.018))
        r=diameter*.501
        stroke(c,"Curved double stitched seam",[(x+r*.23*math.cos(t),-r*.973*math.cos(t),r*math.sin(t))
               for t in (-.96,-.64,-.32,0,.32,.64,.96)],diameter*.0045,m["lightblue"],root)
    return root


def street(c,m):
    area(c,"#ffbf80","#9bbaff")
    k.make_ricks_light("Late sun above the roof",c,(-5,-7,16),(1,-.4,7.4),"#ffd097",4150,4.8)
    rim=k.make_ricks_light("Roof-height blue skylight",c,(8,3,12),(4,0,8.6),"#9ebfff",2450,4.9)
    rim.data.use_shadow=False
    sky=k.emission("Late blue sunset beyond apartment skyline","#7597c9",.88)
    box(c,"Continuous twilight sky",(0,18,18),(126,.20,65),sky)
    blush=k.emission("Peach late-afternoon cloud edges","#daa58d",.96)
    cloud=k.emission("Dusty lilac cloud underlights","#9a8da7",.88)
    rng=Random(91)
    for bank in range(9):
        xx=-26+bank*6.68
        zz=9.2+1.37*(bank%4)+rng.random()
        for stripe in range(4):
            x=xx+rng.uniform(-1.7,1.7)
            z=zz+stripe*.151
            width=rng.uniform(1.1,3.2)
            stroke(c,"Wind-streaked sunset cloud",[(x-width,16.2,z),(x-.19*width,16.2,z+.18),
                   (x+width,16.2,z+.14)],.08 if stripe%2 else .13,blush if stripe>1 else cloud)
    box(c,"Dim indigo asphalt",(0,-9,-.117),(89,85,.23),k.texture("Subtle painted street asphalt",
        ("#2a3448","#4c5367","#808296"),"plaster",(.84,.95)))
    for x in range(-14,15):
        box(c,"Warm broken road centerline",(x*1.47,-1.75,.011),(.61,.061,.016),m["gold"])
    for y in (-19.8,-13.6,-7.4,3.7):
        stroke(c,"Long painted curb edge",[(-34,y,.017),(34,y,.017)],.051,m["cream"])
        for j in range(25):
            x=(j-12)*1.95
            box(c,"Long street paving seam",(x,y+.63,.013),(.052,1.19,.022),m["metal"])
    for center,y,width in ((-12.77,-12.8,3.7),(3.7,-13.0,3.9),(18.4,-6.0,5.35),(8.2,7.9,4.4)):
        tower(c,m,center,y,width,7.1 if y<0 else 12.0)
    colors=(
        k.emission("Distant sun-washed building paint","#758baa",.88),
        k.emission("Dusty violet distant glazing","#34365b",.93),
        k.emission("Warm skylight across cornices","#c79d91",.89),
    )
    for n,x in enumerate((-20,-13,-7,-1,5,11,17,23,29)):
        skyline(c,colors,x,14.8,4.0+n%3*.43,10.2+1.54*(n%4))
    paving(c)
    curb=k.emission("Recessed sandy sidewalk seams","#9c8a94",.92)
    for y in (-25.5,-23.9,-22.4,-20.9,-19.4,-17.9,-14.3,-9.1,-6.3):
        for ix in range(-45,46):
            x=ix*.64
            if abs(x+1.7) < 3.1 and y>-23:
                continue
            box(c,"Staggered granite paving mark",(x+(round(y*10)%2)*.29,y,.009),(.44,.085,.021),curb)
    for j,x in enumerate((-14,-9,-4,4.5,9,14)):
        front=5.7+.77*(j%2)
        h=6.7+.94*(j%3)
        box(c,"Tall painted apartment volume",(x,front+1.02,h*.5),(4.41,2.1,h),m["wood2"] if "wood2" in m else m["cork"])
        box(c,"Flat roof parapet",(x,front+1.02,h+.14),(4.58,2.31,.25),m["roof"])
        for level in range(3):
            z=1.30+2.10*level
            for i in range(3):
                xx=x+(i-1)*1.37
                box(c,"Deep limestone jamb",(xx,front-.062,z),(.97,.106,1.26),m["cream"])
                box(c,"Blue apartment glazing",(xx,front-.129,z),(.83,.058,1.09),m["window"])
                box(c,"Window shadow mullion",(xx,front-.162,z),(.069,.046,1.09),m["ink"])
            box(c,"Long bright masonry floor band",(x,front-.13,z+.99),(4.42,.15,.10),m["gold"])
        for inset in (-1.77,1.77):
            for n in range(9):
                z=.32+n*.714
                stroke(c,"Masonry edge course",[(x+inset-.21,front-.14,z),
                       (x+inset+.21,front-.14,z)],.018,m["wood"])
    join_cuboids(c)


def tower(c,m,x,y,width,height):
    box(c,"Foreground warm masonry", (x,y+.67,height*.5),(width,1.40,height),m["wood"])
    box(c,"Cut limestone rooftop coping",(x,y+.66,height+.10),(width+.07,1.47,.18),m["gold"])
    for column in (-.42,.42):
        box(c,"Tall limestone pilaster",(x+column*width,y-.070,height*.49),(.17,.146,height*.97),m["cream"])
    for level in range(1,int(height/.75)):
        z=level*.75
        box(c,"Cream building string course",(x,y-.055,z),(width,.119,.037),m["gold"])
        for sign in (-1,1):
            face_x=x+sign*width*.228
            box(c,"Dark inset window reveal",(face_x,y-.094,z+.319),(width*.32,.12,.528),m["ink"])
            box(c,"Sun toned blue window reflecting town",(face_x,y-.163,z+.319),(width*.286,.027,.45),m["window"])
            for dx in (-.085,.085):
                box(c,"Reflective steel door-or-window mullion",(face_x+width*dx,y-.19,z+.319),
                    (.047,.052,.467),m["lightblue"])
            box(c,"Painted metallic windowsill",(face_x,y-.200,z+.065),(width*.345,.11,.051),m["cream"])


def skyline(c,materials,x,y,width,height):
    material,glazing,trim=materials
    box(c,"Layered distant town silhouette",(x,y,height*.5),(width,1.0,height),material)
    box(c,"Sunlit city cornice",(x,y-.53,height-.17),(width+.06,.09,.15),trim)
    for row in range(1,int(height/.92)):
        z=row*.92
        for dx in (-.34,-.11,.11,.34):
            box(c,"Dim reflective skyline window",(x+dx*width,y-.526,z),(.31,.036,.42),glazing)
        box(c,"Dusty warm skyline course",(x,y-.551,z-.26),(width,.037,.064),trim)


def join_cuboids(c):
    """Batch the static city meshes by material to reduce per-frame draw overhead."""
    groups={}
    for obj in tuple(c.objects):
        if (obj.type=="MESH" and len(obj.data.vertices)==8 and not len(obj.modifiers)
                and len(obj.data.materials)==1 and obj.parent is None):
            groups.setdefault(obj.data.materials[0],[]).append(obj)
    for material,objects in groups.items():
        if len(objects)<3:
            continue
        points,faces=[],[]
        for obj in objects:
            i=len(points)
            points.extend(tuple(v.co+obj.location) for v in obj.data.vertices)
            faces.extend(tuple(j+i for j in face.vertices) for face in obj.data.polygons)
            bpy.data.objects.remove(obj,do_unlink=True)
        k.mesh("Static city geometry | "+material.name,c,points,faces,material)


def paving(c):
    colors=("#a6918d","#75768c","#c1a59c")
    for material,color in enumerate(colors):
        points, faces = [], []
        for r in range(45):
            y=-31.7+r*.55
            for j in range(-51,53):
                x=j*.50+.25*(r%2)
                if (r+j)%3!=material or -3.5 < x < .8:
                    continue
                if -7.5 < y < -5.8:
                    continue
                index=len(points)
                points.extend(((x,y,.006),(x+.476,y,.006),(x+.476,y+.039,.006),(x,y+.039,.006)))
                faces.append(tuple(range(index,index+4)))
        k.mesh("Painted granite sidewalk grout courses",c,points,faces,
               k.emission("Dusk pavement stitching "+color,color,.96)).visible_shadow=False


def truck(c,m):
    root=k.empty("Fire engine",c)
    box(c,"Bright fire engine chassis",(0,0,.53),(3.67,1.04,.68),m["red"],root,bevel=.082)
    box(c,"Fire engine crew cab",(-1.16,0,1.06),(1.17,1.06,.97),m["red"],root,bevel=.08)
    box(c,"Pale cab windscreens",(-1.23,-.545,1.17),(.87,.047,.42),m["window"],root,bevel=.028)
    box(c,"Cream fire truck trim",(0,-.526,.67),(3.47,.036,.098),m["cream"],root)
    for x in (-1.22,1.11):
        for y in (-.485,.485):
            cylinder(c,"Outlined engine tire",(x,y,.325),.315,.17,m["ink"],root,axis="Y")
            cylinder(c,"Brushed wheel rim",(x,y*1.15,.325),.168,.051,m["metal"],root,axis="Y")
    for j in range(2):
        box(c,"Folded steel tool cupboard",(.48+j*.49,-.544,.78),(.447,.06,.44),m["metal"],root)
    beacon=k.emission("Poppy-red emergency beacon","#ff4f47",2.9)
    for y in (-.34,.34):
        cylinder(c,"Glowing fire engine beacon",(-1.16,y,1.62),.095,.132,beacon,root)
    ladder=k.empty("Extended ladder swivel",c,(.77,0,.924),root)
    for side in (-1,1):
        box(c,"Long silver ladder stringer",(0,side*.25,3.47),(.080,.085,7.0),m["metal"],ladder)
    for i in range(20):
        box(c,"Ribbed ladder rung",(0,0,.17+i*.344),(.073,.58,.059),m["gold"],ladder)
    return root,ladder


def safe(c,m):
    root=k.empty("Transparent timed lock box",c)
    light=k.emission("Cyan transparent box edge","#a4d9f4",1.12)
    box(c,"Deep timed safe base",(0,0,.045),(.537,.327,.088),m["rubber"],root,bevel=.024)
    for x in (-.253,.253):
        for y in (-.154,.154):
            stroke(c,"Glass lockbox beveled edge",[(x,y,.07),(x,y,.335)],.012,light,root)
    for z in (.083,.331):
        stroke(c,"Glass lockbox transparent perimeter",[(-.253,-.154,z),(.253,-.154,z),(.253,.154,z),
               (-.253,.154,z),(-.253,-.154,z)],.009,light,root)
    timer=k.emission("Warm digital clock digits","#ffe0a2",1.28)
    display=box(c,"Dark timed safe LED display",(0,-.168,.065),(.387,.023,.075),m["ink"],root,bevel=.011)
    text(c,"DEC 1 — 12:00",(0,-.183,.048),.044,timer,root)
    dial=cylinder(c,"Knurled timer safe dial",(.222,-.177,.080),.049,.037,m["gold"],root,axis="Y")
    stroke(c,"Brown inset timer dial needle",[(.218,-.201,.081),(.223,-.201,.115)],.004,m["cork"],root)
    lid=k.empty("Clear timed safe lid pivot",c,(0,.154,.33),root)
    glass=k.emission("Barely tinted safety glass","#a7d3e4",.88)
    glass.surface_render_method="BLENDED"
    nodes,links=glass.node_tree.nodes,glass.node_tree.links
    em=next(node for node in nodes if node.type=="EMISSION")
    clear=nodes.new("ShaderNodeBsdfTransparent")
    mix=nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value=.065
    links.new(clear.outputs[0],mix.inputs[1])
    links.new(em.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],next(node for node in nodes if node.type=="OUTPUT_MATERIAL").inputs[0])
    for y in (-.155,.155):
        pane=k.mesh("Clear acrylic far or near wall",c,[(-.249,y,.07),(.249,y,.07),(.249,y,.33),(-.249,y,.33)],
                    [(0,1,2,3)],glass,root)
        pane.visible_shadow=False
    for x in (-.252,.252):
        pane=k.mesh("Clear acrylic end wall",c,[(x,-.155,.07),(x,.155,.07),(x,.155,.33),(x,-.155,.33)],
                    [(0,1,2,3)],glass,root)
        pane.visible_shadow=False
    k.mesh("Clear acrylic lid",c,[(-.25,0,0),(.25,0,0),(.25,-.32,0),(-.25,-.32,0)],[(0,1,2,3)],glass,lid)
    for x in (-.260,.260):
        stroke(c,"Cyan clear lid side rail",[(x,0,0),(x,-.323,0)],.013,light,lid)
    for y in (0,-.323):
        stroke(c,"Cyan clear lid cross rail",[(-.260,y,0),(.260,y,0)],.013,light,lid)
    return root,lid,dial


def space(c,m):
    bg=k.emission("Indigo deep-space plateau","#1d2846",.84)
    box(c,"Deep-space blue gradient wash",(0,14,4),(67,.2,59),bg)
    rng=Random(703)
    for material,count in ((m["moon"],3190),(m["shade"],590)):
        points,faces=[],[]
        for j in range(count):
            x=rng.uniform(-17,17)
            y=rng.uniform(9,13.8)
            z=rng.uniform(-25,24)
            r=rng.uniform(.027,.090)
            index=len(points)
            points.extend(((x-r,y,z),(x,y,z+r*1.13),(x+r,y,z),(x,y,z-r*1.13)))
            faces.append(tuple(range(index,index+4)))
        k.mesh("Continuous cool or warm constellation field",c,points,faces,material).visible_shadow=False
    k.make_ricks_light("Bright warm space rim",c,(-9,-5,11),(0,0,1),"#ffcca7",3450,4.8)
    k.make_ricks_light("Cool other side space key",c,(8,4,6),(0,0,1),"#8bc8ff",4120,3.7)


def earth(c,m,xyz):
    earth=k.ball("Blue-green Earth",c,xyz,(.885,)*3,k.texture("Ocean and abstract cloud-swept continents",
                 ("#234aa5","#45a692","#c0d9b6"),"plaster",(.64,.86)),segments=38,rings=23)
    k.make_ricks_light("Cyan Earth limb bounce",c,(xyz[0]-1.6,-1.2,xyz[2]+.50),xyz,"#9fe1ff",120,1.1)
    rim=k.emission("Luminous cyan atmosphere","#78c8f3",1.15)
    stroke(c,"Thin brush arc on Earth's atmosphere",
           [(xyz[0]+.902*math.cos(a),xyz[1],xyz[2]+.902*math.sin(a))
            for a in (i*.061 for i in range(12,73))],.017,rim)
    return earth


def satellite(c,m):
    rig=k.empty("Satellite swerving around the fabric spheres",c)
    cylinder(c,"Gold thermal foil satellite tube",(0,0,0),.296,.62,m["gold"],rig,axis="Y")
    cylinder(c,"Telescope black ring",(0,-.329,0),.226,.091,m["ink"],rig,axis="Y",segments=32)
    cylinder(c,"Cyan satellite objective lens",(0,-.386,0),.159,.052,m["window"],rig,axis="Y",segments=32)
    for side in (-1,1):
        x=side*.817
        box(c,"Solar array aluminum frame",(x,0,0),(1.02,.082,.534),m["metal"],rig,bevel=.014)
        box(c,"Indigo-charged solar cells",(x,-.051,0),(.963,.02,.475),m["blue"],rig)
        for j in range(8):
            xx=x+(j-3.5)*.123
            stroke(c,"Thin solar cell bond wires",[(xx,-.065,-.239),(xx,-.065,.239)],.0045,m["lightblue"],rig)
        for z in (-.12,0,.12):
            stroke(c,"Solar cell bond wire",[(x-.478,-.065,z),(x+.478,-.065,z)],.0045,m["lightblue"],rig)
    return rig
