"""Painted suburban, home, and school sets in the shared Blender vocabulary."""
import math
from random import Random

import bpy
from mathutils import Vector
import ricks_v2_kit as k


def block(c,name,loc,size,mat,parent=None):
    x,y,z=(value/2 for value in size)
    vertices=[(i*x,j*y,l*z) for i,j,l in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
              (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    obj=k.mesh(name,c,vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,parent)
    obj.location=loc
    return obj


def line(c,name,coords,radius,mat,parent=None):
    obj=k.tube(name,c,coords,radius,mat,parent)
    obj.data.resolution_u=2 if len(coords)>2 else 1
    obj.data.bevel_resolution=1
    return obj


def lettering(c,name,loc,size,mat,parent=None):
    data=bpy.data.curves.new(name,"FONT")
    data.body=name
    data.size=size
    data.align_x="CENTER"
    obj=k.put(bpy.data.objects.new(name,data),c,parent,mat)
    obj.location=loc
    obj.rotation_euler.x=math.pi/2
    return obj


def mesh_tiles(name,colors,width,height,gap,plane="wall"):
    material=k.surface(name,colors[0],.80)
    nd,lk=material.node_tree.nodes,material.node_tree.links
    shader=next(n for n in nd if n.type=="BSDF_PRINCIPLED")
    coordinates=nd.new("ShaderNodeTexCoord")
    xyz=nd.new("ShaderNodeSeparateXYZ")
    combine=nd.new("ShaderNodeCombineXYZ")
    pat=nd.new("ShaderNodeTexBrick")
    lk.new(coordinates.outputs["Object"],xyz.inputs[0])
    lk.new(xyz.outputs["X"],combine.inputs["X"])
    lk.new(xyz.outputs["Z" if plane=="wall" else "Y"],combine.inputs["Y"])
    lk.new(combine.outputs[0],pat.inputs["Vector"])
    for key,value in zip(("Color1","Color2","Mortar"),colors):
        pat.inputs[key].default_value=k.look.rgba(value)
    pat.inputs["Scale"].default_value=1
    pat.inputs["Brick Width"].default_value=width
    pat.inputs["Row Height"].default_value=height
    pat.inputs["Mortar Size"].default_value=gap
    pat.inputs["Mortar Smooth"].default_value=.003
    if plane!="wall":
        pat.offset=0
    lk.new(pat.outputs["Color"],shader.inputs["Base Color"])
    return material


def palette():
    outline=k.emission("Espresso outline","#161020")
    outline.use_backface_culling=True
    return {
        "ink":outline,
        "cream":k.surface("Porcelain warm tinted","#ddd4c9",.76),
        "brick":mesh_tiles("Reclaimed brick with cream joints",("#a76c5e","#5c3d46","#bf978b"),.29,.12,.010),
        "ground":mesh_tiles("Warm limestone sidewalk flagstones",("#c7b5a3","#9092a4","#5d5865"),.70,.58,.013,"floor"),
        "blue":k.surface("Oil painted school blue","#406486",.70),
        "red":k.surface("Burgundy enamel lockers","#a64049",.65),
        "dark":k.surface("Painted blue graphite","#293749",.78),
        "glass":k.emission("Blue reflections in glass","#689cbb",.86),
        "white":k.emission("Ivory sign ink","#fff2d9",1.06),
        "wood":k.texture("Warm timber grain",("#52334c","#7f4a45","#b78b65"),"wood",(.65,.85)),
        "grass":k.texture("Painted hedge foliage",("#243d48","#48734c","#88a765"),"plaster",(.74,.88)),
        "gold":k.emission("Buttery gold visual punctuation","#ffd870",1.45),
    }


def daylights(c,interior=False,warm=False):
    if interior:
        k.make_ricks_light("Large soft window key",c,(-1.08,-2.46,3.42),(0,0,1.18),
                           "#ffd19a" if warm else "#e9e6ff",275,1.15)
        k.make_ricks_light("Broad blue bounce",c,(2,-1.0,2.4),(0,0,1.08),"#a4bfff",105,1.15)
        return
    key=bpy.data.lights.new("Long diagonal morning sun","SUN")
    key.energy=2.92
    key.color=k.look.rgba("#FFE0AD")[:3]
    key.angle=.011
    key.use_shadow_jitter=False
    sun=k.put(bpy.data.objects.new(key.name,key),c)
    sun.location=(-7.9,-5.4,4.0)
    k.aim(sun,(0,0,0))
    fill=k.make_ricks_light("Blue open sky fill",c,(2.5,-.85,3.09),(0,0,1.44),"#c6d9ee",86,1.88)
    rim=k.make_ricks_light("Gold rim on hair and shoulders",c,(.9,2.26,3.5),(0,0,1.20),"#ffcf9c",268,1.01)
    fill.data.use_shadow=rim.data.use_shadow=False


def outdoor_sky(c,m):
    sky=k.emission("Continuous morning dome","#8cc7ee",1.0)
    nodes,links=sky.node_tree.nodes,sky.node_tree.links
    coordinates=nodes.new("ShaderNodeTexCoord")
    xyz=nodes.new("ShaderNodeSeparateXYZ")
    ramp=nodes.new("ShaderNodeValToRGB")
    k.look._ramp(ramp,[(.40,"#e5ead8"),(.50,"#c3e5f3"),(.62,"#61a6d7"),(1,"#3b80c1")])
    links.new(coordinates.outputs["Generated"],xyz.inputs[0])
    links.new(xyz.outputs["Z"],ramp.inputs[0])
    emission=next(node for node in nodes if node.type=="EMISSION")
    links.new(ramp.outputs["Color"],emission.inputs["Color"])
    dome=k.ball("Continuous surrounding blue sky",c,(0,0,0),(42,42,31),sky,segments=32,rings=16)
    dome.visible_shadow=False
    cloud=k.emission("Diffuse cream-white clouds","#eef3ec",.92)
    shade=k.emission("Cool pale cloud lower layer","#cee0eb",.92)
    for x,y,z,scale in ((-8,12,5.8,1.2),(-2,13,6.4,1.),(5,13,5.4,1.35),
                          (10,10,5.3,1.05),(14,6,5.5,1.1),(13,-.6,4.8,1.4)):
        for j in range(4):
            puff=k.ball("Layered oval of a soft distant cloud",c,(x+(j-1.5)*.66*scale,y,z+.23*math.sin(j)),
                         ((.73+.15*math.sin(j))*scale,.42,(.33+.10*math.sin(j*1.3))*scale),
                         cloud if j%3 else shade,segments=13,rings=7)
            puff.visible_shadow=False
    rng=Random(2417)
    leaf=[k.surface("Tree leaves in shaded and sunlit layers",tone,.86,glow=.08)
          for tone in ("#325837","#487443","#6f8b4a","#9aaf62","#728e54")]
    for j,(x,y,z) in enumerate(((-6.8,4.21,3.64),(-4.2,5.1,3.58),(-2.55,4.1,3.89),(-.65,4.57,3.49),
                                (1.86,5.3,3.61),(3.0,4.35,3.97),(4.87,5.14,3.36),(6.34,4.28,3.68))):
        top=Vector((x+.17*(j%3-1),y,z))
        line(c,"Forked street tree trunk",[(x,y,1.53),(x,y,2.95),tuple(top)],.056,m["wood"])
        for i in range(10):
            angle=i*2.39996
            tier=rng.uniform(-.24,.49)
            spread=rng.uniform(.24,.62)*(1-.50*max(0,tier))
            offset=Vector((spread*math.cos(angle),.77*spread*math.sin(angle),tier))
            width=rng.uniform(.24,.53)
            crown=k.ball("Organic overlapping leafy lobe",c,top+offset,
                (width,width*rng.uniform(.70,1.03),width*rng.uniform(.58,.84)),
                leaf[min(4,max(0,round((tier+.31)*6)))],segments=11,rings=6)
            for idx,vertex in enumerate(crown.data.vertices):
                vertex.co*=1+.068*math.sin(idx*1.79+j+i*.9)


def car_mesh(c,name,rings,mat,root,outline=False):
    vertices=[pos for section in rings for pos in section]
    n=len(rings[0])
    faces=[(i*n+j,(i+1)*n+j,(i+1)*n+(j+1)%n,i*n+(j+1)%n)
           for i in range(len(rings)-1) for j in range(n)]
    span=(len(rings)-1)*n
    faces.extend((tuple(range(n)),tuple(reversed(range(span,span+n)))))
    obj=k.mesh(name,c,vertices,faces,mat,root,True)
    if outline:
        k.apply_prop_ink(obj,c,depth=5.4,lens_mm=26,pixels=1.05)


def hatchback(c,m,name,loc,color):
    root=k.empty(name,c,loc)
    paint=k.surface(name+" enamel",color,.37,.25)
    soot=k.surface("Smoke-tinted car windows","#25384b",.41,.12)
    tire=k.surface("Matte road rubber","#232329",.87)
    metal=k.surface("Brushed alloy rims","#afb7c4",.44,.39)
    lens=k.emission("Small warm headlights","#fff0ba",2.1)
    tail=k.emission("Small red rear lamps","#f0655a",1.7)
    skins=[]
    for x,half,high in ((-.84,.20,.25),(-.74,.256,.333),(-.44,.288,.386),(.33,.288,.376),
                         (.66,.262,.318),(.80,.209,.249)):
        skins.append([(x,y,z) for y,z in ((-half,.14),(-half,.22),(-half*.82,high),
                      (half*.82,high),(half,.22),(half,.14))])
    car_mesh(c,"Rounded hatchback painted body",skins,paint,root,True)
    cabin=[[(x,y,z) for y,z in ((-w,b),(-v,t),(v,t),(w,b))]
           for x,w,v,b,t in ((-.53,.197,.186,.356,.369),(-.26,.221,.162,.365,.587),
                              (.207,.227,.152,.356,.575),(.52,.195,.188,.330,.339))]
    car_mesh(c,"Dark windscreen and sloping window canopy",cabin,soot,root,True)
    line(c,"Painted hatchback roof edge",[(-.27,-.166,.588),(-.04,-.171,.606),(.212,-.157,.576)],
         .025,paint,root)
    for side in (-1,1):
        y=side*.216
        line(c,"Slim color-matched cabin pillar",[(.024,y,.365),(-.014,side*.16,.589)],.014,paint,root)
        line(c,"Silver line underneath side windows",[(-.51,y,.36),(.48,y,.345)],.009,metal,root)
        for x,mat in ((.715,lens),(-.76,tail)):
            k.ball("Glowing automotive lens",c,(x,side*.192,.269),(.076,.082,.041),mat,root,segments=12,rings=7)
    wheels=[]
    for x in (-.52,.53):
        for side in (-1,1):
            pivot=k.empty("Rolling alloy and tire wheel",c,(x,side*.240,.151),root)
            wheel=k.cylinder("Continuous molded rubber tire",c,(0,0,0),.151,.083,tire,pivot,length_segments=26)
            wheel.rotation_euler.x=math.pi/2
            rim=k.cylinder("Rounded brushed metal rim",c,(0,side*.047,0),.099,.014,metal,pivot,length_segments=22)
            rim.rotation_euler.x=math.pi/2
            for j in range(5):
                a=math.tau*j/5
                line(c,"Dark narrow inset rim spokes",[(.025*math.cos(a),side*.055,.025*math.sin(a)),
                     (.080*math.cos(a),side*.055,.080*math.sin(a))],.012,tire,pivot)
            wheels.append(pivot)
    return root,wheels


def street(c,m,courtyard=False):
    outdoor_sky(c,m)
    block(c,"Flagstone pedestrian lane",(0,-.25,-.091),(18,11,.181),m["ground"])
    block(c,"Grey side street",(0,2.15,-.082),(18,1.64,.15),m["dark"])
    for i in range(24):
        x=(i-11.5)*.73
        block(c,"Cream road divider",(x,2.21,-.002),(.41,.033,.008),m["cream"])
        block(c,"Segmented stone kerb",(x,1.26,-.010),(.70,.136,.070),m["cream"])
    for j in range(7):
        x=(j-3)*1.94
        depth=3.60+.09*(j%3)
        level=2.87+.30*(j%2)
        block(c,"Main brick terrace", (x,depth,level/2),(1.91,.42,level),m["brick"])
        roof=block(c,"Dark roof line",(x,depth-.09,level+.085),(1.99,.63,.135),m["dark"])
        roof.rotation_euler.y=.035*(-1)**j
        block(c,"Stone dividing pier",(x-.94,depth-.252,level/2),(.068,.129,level+.01),m["cream"])
        for z in (.71,1.62,2.43):
            for xx in (x-.44,x+.42):
                block(c,"Masonry window reveal",(xx,depth-.231,z),(.558,.052,.555),m["cream"])
                block(c,"Blue raised window glass",(xx,depth-.263,z),(.484,.021,.487),m["glass"])
                block(c,"Stone window lintel",(xx,depth-.289,z+.268),(.603,.061,.073),m["cream"])
                block(c,"Single narrow wooden window bar",(xx,depth-.286,z),(.029,.025,.49),m["cream"])
                block(c,"Lower blue-black window shadow",(xx,depth-.284,z-.139),(.468,.022,.104),m["blue"])
        for i in range(3):
            xx=x-.63+i*.60
            k.ball("Round clipped hedge",c,(xx,depth-.70,.21),(.35,.29,.285),m["grass"],segments=12,rings=8)
        for i in range(6):
            xx=x-.76+i*.28
            line(c,"Garden iron rail post",[(xx,depth-.97,.065),(xx,depth-.97,.63)],.014,m["dark"])
        for z in (.18,.48):
            line(c,"Garden iron crossrail",[(x-.92,depth-.98,z),(x+.91,depth-.98,z)],.013,m["dark"])
    for x in (-3.1,2.68,5.22):
        y=1.28
        k.cylinder("Cast iron curb lamp plinth",c,(x,y,.045),.111,.106,m["dark"],length_segments=18)
        k.cylinder("Straight cast iron lamp standard",c,(x,y,1.215),.040,2.35,m["dark"],r2=.027,length_segments=16)
        for z,r in ((.117,.074),(.26,.050),(2.22,.042)):
            k.cylinder("Turned pole collar",c,(x,y,z),r,.042,m["dark"],length_segments=16)
        line(c,"Curved lamp bracket",[(x,y,2.32),(x+.034,y,2.45),(x+.16,y,2.49)],.028,m["dark"])
        block(c,"Lantern top housing",(x+.16,y,2.45),(.25,.22,.077),m["dark"])
        block(c,"Frosted lantern glass",(x+.16,y,2.378),(.169,.14,.099),m["cream"])
    if courtyard:
        block(c,"Closer brick courtyard boundary",(0,1.52,.71),(13,.13,1.39),m["brick"])
        block(c,"Wall cap",(0,1.48,1.43),(13,.19,.047),m["cream"])
        for j in range(13):
            x=(j-6)*.91
            line(c,"Courtyard rail post",[(x,1.46,1.43),(x,1.46,2.05)],.019,m["dark"])
        for z in (1.54,1.94):
            line(c,"Courtyard rail horizontal",[(-6,1.46,z),(6,1.46,z)],.018,m["dark"])
    daylights(c)
    if not courtyard:
        hatchback(c,m,"Parked dusty-blue car",(2.9,2.72,0),"#587c9d")
        return hatchback(c,m,"Passing moss green car",(-3.11,1.96,0),"#668e76")


def living_room(c,m):
    wallpaper=k.texture("Warm apricot painted plaster",("#74535b","#a0776e","#be916f"),"plaster",(.79,.90))
    block(c,"Warm plaster living-room wall",(0,1.56,1.68),(11,.15,3.5),wallpaper)
    block(c,"Painted wooden baseboard",(0,1.459,.072),(11,.073,.144),m["cream"])
    block(c,"Warm plaster interior panel rail",(0,1.456,1.10),(11,.061,.049),m["cream"])
    for x in (-2.15,2.19):
        block(c,"Warm outline of a wood door casing",(x,1.46,1.18),(.072,.093,2.36),m["wood"])
    block(c,"Hickory floorboards",(0,0,-.092),(11,10,.18),
          mesh_tiles("Amber floorboards with seams",("#995b49","#b57f5a","#65404d"),.57,.151,.005,"floor"))
    block(c,"Warm grey rug",(0,-.25,.004),(3.35,2.19,.015),
          k.texture("Warm grey woven cotton",("#8b7e91","#968b9e","#a498aa"),"plaster",(.79,.89)))
    for y in (-1.29,.77):
        line(c,"Rug braided border",[(-1.69,y,.018),(1.69,y,.018)],.029,m["cream"])
    for j in range(11):
        y=-1.11+j*.16
        line(c,"Pale embroidered lines on the grey rug",[(-1.56,y,.015),(1.56,y,.015)],
             .004,m["cream"] if j%3==0 else m["blue"])
    for j in range(21):
        x=(j-10)*.159
        line(c,"Rug fringed hem",[(x,-1.25,.012),(x+.012,-1.36,.014)],.009,m["cream"])
    sofa=k.surface("Mulberry sofa fabric","#824c62",.82)
    cushion=k.surface("Faded warm rose cushions","#a66d76",.80)
    block(c,"Sofa base",(.36,.84,.25),(2.16,.62,.37),sofa)
    block(c,"Sofa padded back",(.36,1.08,.57),(2.16,.21,.61),sofa)
    for j in range(3):
        x=-.33+j*.66
        block(c,"Seat cushion",(x,.75,.43),(.632,.58,.16),cushion)
        block(c,"Sofa back pillow",(x,1.0,.65),(.603,.23,.40),cushion)
        line(c,"Cushion stitching",[(x-.27,.873,.51),(x-.25,.874,.76),(x+.26,.872,.80)],.008,m["wood"])
    for x in (-.76,1.48):
        block(c,"Sofa round arm block",(x,.77,.443),(.26,.72,.41),sofa)
    for x in (-1.47,.20,1.41):
        block(c,"Wood framed print",(x,1.461,1.57),(.63,.05,.56),m["wood"])
        block(c,"Soft painted print",(x,1.430,1.57),(.538,.01,.467),m["cream"])
        for j in range(4):
            line(c,"Graphic motif in wall print",[(x-.20+i*.047,1.421,1.48+j*.065+.048*math.sin(x+i*.87+j))
                 for i in range(9)],.012,m["blue"] if j%3 else m["red"])
    x=-1.19
    k.cylinder("Floor lamp metal pole",c,(x,.99,.78),.029,1.55,m["dark"])
    shade=k.cylinder("Glowing gold fabric cone",c,(x,.99,1.57),.285,.30,m["gold"],r2=.149)
    k.make_light_cone("Soft warm lamp cone",c,(x,.99,1.44),(x,.94,.069),.225,.63,"#ffc587")
    practical=k.make_ricks_light("Warm pool below the floor lamp",c,(x,.96,1.45),(-.91,.05,.22),
                                 "#ffbe83",128,.46,"SPOT",58)
    practical.data.use_shadow=False
    daylights(c,interior=True,warm=True)


def hallway(c,m):
    wall=mesh_tiles("School white and blue wall tiles",("#8fafcb","#cad9e5","#577c9f"),.30,.242,.012)
    floor=mesh_tiles("Terrazzo blue and white school floor",("#d2d4df","#a7b2c6","#7d8ca9"),.43,.43,.020,"floor")
    bsdf=next(node for node in floor.node_tree.nodes if node.type=="BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value=.265
    bsdf.inputs["Specular IOR Level"].default_value=.33
    bsdf.inputs["Coat Weight"].default_value=.27
    block(c,"Polished school corridor floor",(-.6,0,-.087),(12.6,3.47,.174),floor)
    for side in (-1,1):
        face=m["red"] if side==1 else m["blue"]
        block(c,"Long blue porcelain tiled school wall",(-.6,side*1.665,1.31),(12.6,.15,2.64),wall)
        block(c,"Long cream picture rail",(-.6,side*1.570,2.09),(12.6,.047,.05),m["cream"])
        for j in range(23):
            x=(j-10)*.412
            block(c,"Recessed enamel locker",(x,side*1.504,.852),(.398,.27,1.686),face)
            block(c,"Inset locker door",(x,side*1.355,.85),(.359,.026,1.589),face)
            block(c,"Locker door recess stripe",(x-.187,side*1.335,.85),(.019,.012,1.59),m["dark"])
            for z in (1.442,1.365,1.295,.39,.31):
                block(c,"Stamped locker ventilation slot",(x,side*1.328,z),(.155,.012,.014),m["dark"])
            block(c,"Satin silver locker handle",(x+.109,side*1.317,.84),(.037,.039,.123),m["cream"])
            if side==1 and -4<=j-10<=6:
                lettering(c,str(207+j-10),(x,1.329,1.122),.055,m["white"])
    block(c,"Recessed light-grey school ceiling",(-.87,0,2.65),(12.4,3.40,.12),m["cream"])
    panel=k.emission("Warm school ceiling bulb panel","#fff2d2",1.45)
    for j in range(9):
        x=-5.10+j*1.11
        block(c,"Recessed ceiling light trim",(x,.01,2.578),(.62,.77,.032),m["dark"])
        block(c,"Glowing roof light panel",(x,.01,2.558),(.54,.65,.018),panel)
        line(c,"Narrow acoustic ceiling seam",[(x-.55,-1.62,2.588),(x-.55,1.62,2.588)],.006,m["blue"])
    window=k.emission("Sunlit back corridor window","#e1edff",1.95)
    block(c,"Hallway end wall",(-4.81,0,1.29),(.10,3.41,2.60),wall)
    block(c,"Far end light from school window",(-4.742,0,1.47),(.023,2.93,1.89),window)
    for y in (-1.36,-.95,-.47,0,.47,.95,1.36):
        block(c,"Far window tall mullion",(-4.715,y,1.47),(.022,.055,1.91),m["cream"])
    for z in (.55,1.24,1.89,2.39):
        block(c,"Far window horizontal mullion",(-4.715,0,z),(.022,2.93,.058),m["cream"])
    light=k.make_ricks_light("Warm luminous window on hallway tiles",c,(-4.52,-.13,1.66),(-.15,.0,.81),
                            "#fff0d2",308,1.4)
    light.data.use_shadow=False
    daylights(c,interior=True)


def sunny_puppy(c,m):
    cream=k.make_cel_character_material("Cream puppy fur","#f4d2a3")
    ear=k.make_cel_character_material("Toast-tipped floppy ears","#b37960")
    muzzle=k.make_cel_character_material("Puppy cream muzzle","#ffead4")
    pink=k.make_cel_character_material("Puppy tongue","#d67f8c")
    root=k.empty("Puppy grounded spool-chewer",c)
    def fur(name,point,radii,mat,parent):
        obj=k.ball(name,c,point,radii,mat,parent,segments=24,rings=14)
        hull=k.apply_character_ink(obj,c,pixels=2.5)
        hull.id_data.data.materials[0]=m["ink"]
        return obj
    fur("Puppy body on the rug",(.027,.098,.223),(.365,.238,.199),cream,root)
    fur("Tucked chubby hindquarter",(.219,.042,.144),(.167,.171,.119),cream,root)
    head=k.empty("Puppy nibbles with small nods",c,(-.223,-.062,.303),root)
    fur("Puppy soft round head",(0,0,0),(.176,.148,.159),cream,head)
    for side in (-1,1):
        floppy=fur("Floppy ear",(side*.147,.009,-.039),(.061,.075,.107),ear,head)
        floppy.rotation_euler.y=side*.39
        fur("Two front paws",(side*.11-.16,-.120,.069),(.083,.123,.051),muzzle,root)
        fur("Bright button eye",(side*.060,-.132,.029),(.024,.016,.029),m["ink"],head)
        k.ball("Tiny catchlight",c,(side*.06-.007,-.146,.041),(.006,.006,.008),m["white"],head,segments=10,rings=6)
    fur("Round pale muzzle",(0,-.128,-.051),(.104,.059,.064),muzzle,head)
    fur("Small puppy shiny nose",(0,-.176,-.033),(.041,.023,.022),m["ink"],head)
    jaw=fur("Small cartoon puppy tongue",(0,-.170,-.086),(.039,.026,.013),pink,head)
    tail=k.empty("Puppy tail hinge",c,(.245,.174,.183),root)
    line(c,"Soft puppy tail silhouette",[(0,0,0),(.135,.04,.042),(.205,.08,.132)],.038,ear,tail)
    return root,head,jaw,tail
