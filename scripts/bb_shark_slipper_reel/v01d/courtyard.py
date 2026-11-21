"""Original carnival courtyard geometry, constructed around the supplied reference."""
import math
from random import Random

import bpy
from mathutils import Vector

import ricks_v2_kit as k
from graphic_materials import matte

TAU = math.tau


def box(name,c,p,extent,m,edge=.025,ink=False,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=bpy.context.object
    o.name=name
    for v in o.data.vertices:
        for i, size in enumerate(extent):
            v.co[i]*=size
    k.put(o,c,parent,m)
    o.location=p
    if ink:
        k.apply_prop_ink(o,c,thickness=.011)
    if edge:
        bev=o.modifiers.new("Rounded edge","BEVEL")
        bev.width,bev.segments=edge,2
    return o


def ring_mesh(name,c,rows,m,n=40,parent=None):
    points=[(cx+rx*math.cos(j*TAU/n), y, cz+rz*math.sin(j*TAU/n))
            for cx,y,cz,rx,rz in rows for j in range(n)]
    faces=[(r*n+j,(r+1)*n+j,(r+1)*n+(j+1)%n,r*n+(j+1)%n)
           for r in range(len(rows)-1) for j in range(n)]
    faces.extend([tuple(range(n)),tuple(reversed(range(len(points)-n,len(points))))])
    return k.mesh(name,c,points,faces,m,parent,True)


def tapered_between(name,c,a,b,r0,r1,m,segments=10,parent=None):
    a,b=Vector(a),Vector(b)
    o=k.cylinder(name,c,(a+b)/2,r0,(b-a).length,m,parent,r2=r1,length_segments=segments)
    o.rotation_euler=(b-a).to_track_quat("Z","Y").to_euler()
    return o


def stage(c):
    rng=Random(417)
    turf=k.texture("Turf • velvety olive pile",("#172d25","#39633a","#63805a"),"plaster",(.72,.9))
    patio=k.texture("Paving • violet slate",("#202036","#373448","#51414f"),"plaster")
    pool=k.surface("Pool water • cobalt glints","#305a9c",.19,.64,glow=.08)
    nt=pool.node_tree; noise=nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=8
    bump=nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.21
    bump.inputs["Distance"].default_value=.043
    bs=next(n for n in nt.nodes if n.type=="BSDF_PRINCIPLED")
    nt.links.new(noise.outputs["Fac"],bump.inputs["Height"]); nt.links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    gold=k.surface("Gilded brass","#b08043",.38,.52,glow=.10)
    red=k.texture("Red carpet • woven garnet",("#38213a","#76263e","#a74754"),"plaster")
    maroon=k.texture("Ribbed pavilion masonry",("#2b243b","#503449","#79534f"),"plaster")
    trim=k.surface("Indigo-stained trim","#2b2b50",.54,.10)
    lamp=k.emission("Carnival marquee • amber glass","#ffb956",5.25)
    cyan=k.emission("Pool rim • lilac cyan","#689afb",1.8)
    ivory=k.surface("Carved ivory and wicker","#d9b990",.67,glow=.10)
    pink=k.surface("Ottoman • rose tufted velvet","#c55e8b",.82,glow=.13)
    black=k.surface("Black leather","#161728",.32,.08)
    steel=k.surface("Brushed chrome rail","#a2b5da",.27,.69)
    box("Courtyard foundation",c,(0,1,-.20),(14,16,.35),patio,.02)
    box("Artificial lawn",c,(.25,-.85,-.05),(10.3,8.5,.10),turf,.018)
    box("Carpet runner",c,(3.30,1,.012),(1.46,10.3,.015),red)
    box("Carpet across courtyard",c,(.25,4.47,.014),(9.4,1.08,.019),red)
    for x in (2.61,3.98):
        box("Runner • woven border",c,(x,1,.022),(.05,10.3,.013),gold,.004)
    # Pool water and lit ceramic edging sit just behind the lawn.
    box("Pool",c,(-2.65,2.21,-.014),(4.7,3.92,.09),pool)
    for x in (-5.02,-.28):
        box("Pool coping",c,(x,2.20,.061),(.22,4.0,.17),patio,.045,True)
        box("Blue pool rail light",c,(x,2.20,.11),(.045,3.87,.075),cyan,.011)
    for y in (.22,4.22):
        box("Pool coping",c,(-2.65,y,.061),(4.95,.21,.17),patio,.045,True)
        box("Blue pool rim light",c,(-2.66,y,.11),(4.63,.036,.073),cyan,.010)
    for i in range(20):
        x=-4.91+i*.235
        box("Pool • alternating mosaic",c,(x,.115,.070),(.212,.035,.095),trim if i%3 else gold,.008)
    for x in (-3.82,-3.50):
        k.tube("Silver candy-cane ladder rail",c,[(x,-.03,.03),(x,-.03,.56),(x,.06,.75),
                (x,.30,.77),(x,.53,.57),(x,.53,-.01)],.037,steel)
    for z in (.15,.34,.50):
        tapered_between("Ladder rung",c,(-3.82,.52,z),(-3.50,.52,z),.021,.021,steel)

    shark(c)
    for x,y in ((-2.47,-1.89),(-.73,-1.69)):
        body=k.cylinder("Ottoman • fluted shell",c,(x,y,.20),.36,.38,ivory,length_segments=32)
        k.apply_prop_ink(body,c)
        for j in range(14):
            a=j*TAU/14
            k.cylinder("Ottoman • piping",c,(x+.351*math.cos(a),y+.351*math.sin(a),.185),.015,.33,gold,length_segments=6)
        k.ball("Ottoman • pink cushion",c,(x,y,.399),(.371,.371,.09),pink,segments=24,rings=12)
        for a in range(5):
            t=a*TAU/5
            k.ball("Ottoman • fabric button",c,(x+.19*math.cos(t),y+.19*math.sin(t),.476),(.027,.027,.012),red,segments=8,rings=6)
    # Pavilion with an open central arch, real recess, raised filigree and marquee.
    for x in (-3.2, .64, 4.35):
        box("Pavilion • ribbed wall",c,(x,5.46,1.80),(3.5 if x<0 else 1.55,.35,3.6),maroon,.035,True)
    box("Pavilion • tall dark entry recess",c,(2.36,5.63,1.51),(2.58,.30,3.03),trim,.04)
    box("Pavilion • upper frieze",c,(1.90,5.28,3.70),(6.6,.52,.46),maroon,.04,True)
    for z in (.24,3.94):
        box("Pavilion • brass stringcourse",c,(.10,5.20,z),(11,.22,.15),gold,.02,True)
    for x in (-4.35,-2.42,-.48,4.95):
        box("Pavilion pilaster",c,(x,5.21,1.83),(.23,.43,3.61),trim,.04,True)
        for z in (.18,3.28):
            box("Pilaster capital",c,(x,5.12,z),(.40,.55,.18),gold,.035)
    arch=[(1.22,4.96,.07),(1.22,4.96,1.81)]
    arch += [(2.38+1.16*math.cos(math.pi-i*math.pi/24),4.96,
              1.81+1.21*math.sin(math.pi-i*math.pi/24)) for i in range(1,25)]
    arch += [(3.54,4.96,.07)]
    k.tube("Golden arch • thick carved surround",c,arch,.136,gold)
    k.tube("Golden arch • inner strip",c,[(2.38+(x-2.38)*.91,4.82,z*.965) for x,_,z in arch],.032,lamp)
    for i,(x,y,z) in enumerate(arch[::2]):
        k.ball("Arch • amber cabochon",c,(x,y-.104,z),(.048,.04,.048),lamp,segments=12,rings=8)
    for x in (1.05,3.71):
        for z in (.23,.40,1.43,1.53):
            box("Arch • ornamental collar",c,(x,4.93,z),(.45,.39,.075),gold,.028)
    for x in (1.46,3.30):
        box("Entry • recessed warm jamb",c,(x,5.35,1.14),(.054,.04,2.08),lamp,.016)
    box("Entry • brass glowing threshold",c,(2.38,5.05,.033),(1.85,.63,.060),gold,.022)
    for x in (.42,4.30):
        peacock(c,x,5.09,1.28)
    for x in (-4.35,-1.05,4.21,4.80):
        for j in range(4):
            flower(c,(x+.19*j,4.79+rng.uniform(-.24,.06),.18+rng.uniform(.0,.17)),.14+rng.random()*.045,j)
    for x,y in ((-4.03,2.9),(-.54,3.65)):
        chair(c,x,y,ivory)
    cone(c,-.90,3.97,rng)
    statue(c,2.63,2.01,black,ivory,gold)
    for x,y,z in ((-4.17,4.8,2.87),(-.82,4.8,2.91),(4.27,4.8,2.83)):
        k.ball("Pavilion • round warm lantern",c,(x,y,z),(.20,.13,.20),lamp,segments=16,rings=12)
        k.tube("Lantern hanger",c,[(x,y,z+.18),(x,y,z+.42),(x,y,z+.58)],.017,gold)
    k.make_ricks_light("Pool • low cyan bounce",c,(-3.20,.79,.51),(-2.02,-.35,.50),"#69c4e6",49,1.43)
    k.make_ricks_light("Shark • indigo-violet contour wash",c,(-.18,1.60,3.02),(-2.02,.52,1.05),"#6659c8",108,2.3)
    k.make_ricks_light("Love • focused cream key",c,(-2.46,-2.31,1.51),(-1.82,-.53,.50),
                       "#fff0d5",126,.24,kind="SPOT",angle=42)
    k.make_ricks_light("Golden arch • warm bounce",c,(2.38,4.52,2.39),(2.1,1.93,.74),"#ffb957",278,2.10)
    key=k.make_ricks_light("Scout entrance • warm face bounce",c,(.63,1.41,2.95),(1.63,3.45,.87),"#ffd5a6",123,1.94)
    key.data.use_shadow=False
    k.make_ricks_light("Scout • directional honey key",c,(2.96,-2.09,2.37),(1.38,.12,1.1),"#ffc075",184,.85)
    fill=k.make_ricks_light("Broad cool ambient",c,(.30,-1.23,5.25),(0,1,0),"#6f89d6",116,5.3)
    fill.data.use_shadow=False
    k.make_light_cone("Arch warm atmosphere",c,(2.36,4.77,2.94),(2.57,4.13,.09),.10,.92,"#ffc46e")
    k.make_light_cone("Carpet • warm lantern shaft",c,(4.27,4.77,2.73),
                      (3.52,3.27,.02),.10,.69,"#ffba65")


def shark(c):
    skin=k.texture("Shark • painterly midnight blues",("#27345c","#475d86","#65779d"),"plaster",(.68,.79))
    under=k.surface("Shark • matte cool belly","#8b9bb9",.76)
    matte(skin,.74,.10)
    matte(under,.76,.10)
    gum=k.surface("Shark • rose-red gumline","#9b426c",.65,glow=.08)
    dark=k.surface("Shark • deep purple mouth","#221329",.9,glow=.043)
    tooth=k.surface("Shark • ivory sharp teeth","#fff1d7",.49,glow=.18)
    iris=k.surface("Shark • black glass eyes","#101827",.21,.23)
    shine=k.emission("Shark eye • pin glint","#c3e5ff",.88)
    socket=k.surface("Shark • deep slate eye recess","#354368",.75,glow=.04)
    ridge=k.surface("Shark • brow crest","#516892",.74,.04)
    matte(socket,.75,.10)
    matte(ridge,.74,.10)
    cx=-1.99
    rows=[(cx,.78,1.13,1.60,.398),(cx,.92,1.31,1.73,.52),
          (cx,1.27,1.54,1.63,.66),(cx-.14,1.78,1.50,1.38,.63),
          (cx-.32,2.66,1.15,1.03,.52),(cx-.47,3.56,.64,.63,.40),
          (cx-.55,3.91,.55,.27,.18)]
    top=ring_mesh("Shark • sculpted upper head and back",c,rows,skin)
    k.apply_prop_ink(top,c,thickness=.017)
    lower=ring_mesh("Shark • swept lower jaw",c,
                    [(cx,.68,.293,1.61,.197),(cx,.86,.30,1.72,.23),
                     (cx,1.20,.36,1.61,.27),(cx-.11,1.92,.49,1.40,.30),
                     (cx-.33,2.50,.60,1.05,.33)],under)
    k.apply_prop_ink(lower,c,thickness=.013)
    k.ball("Shark • recessed mouth throat",c,(cx,1.30,.64),(1.59,.36,.56),dark,segments=32,rings=16)
    upper,lower=[],[]
    for j in range(33):
        q=-1+j/16
        v=math.sqrt(max(0,1-q*q))
        y=.78+.24*abs(q)**1.9
        upper.append((cx+1.58*q,y,.50+.25*v))
        lower.append((cx+1.59*q,y-.076,.50-.115*v))
    k.tube("Shark • upper scalloped gum",c,upper,.067,gum)
    k.tube("Shark • lower scalloped gum",c,lower,.068,gum)
    for j in range(23):
        q=-.94+j*.085
        v=math.sqrt(max(0,1-q*q))
        x=cx+1.56*q
        y=.75+.24*abs(q)**1.9
        top_z=.50+.25*v
        low_z=.50-.115*v
        t=.14+.081*v
        tapered_between("Shark • upper pointed tooth",c,(x,y,top_z+.023),
                        (x+.02*math.sin(j),y-.023,top_z-t),.048,.001,tooth,8)
        x+=.035
        tapered_between("Shark • lower pointed tooth",c,(x,y-.095,low_z-.021),
                        (x+.015,y-.111,low_z+.109*v+.039),.043,.001,tooth,8)
    for s in (-1,1):
        x=cx+s*1.171
        z=1.155
        inset=k.ball("Shark • inset side socket",c,(x,.785,z),(.113,.032,.061),
                     socket,segments=20,rings=12)
        inset.rotation_euler.y=-s*.32
        e=k.ball("Shark • recessed narrow iris",c,(x,.782,z-.006),(.074,.031,.037),
                 iris,segments=20,rings=12)
        e.rotation_euler.y=-s*.32
        k.ball("Shark • small eye catchlight",c,(x-.024,.751,z+.002),(.012,.007,.009),
               shine,segments=10,rings=8)
        brow=k.mesh("Shark • sculpted fierce brow ridge",c,
                    [(x-s*.133,.738,z+.008),(x+s*.133,.762,z+.087),
                     (x+s*.184,.805,z+.161),(x-s*.077,.805,z+.103),
                     (x-s*.121,.784,z+.014),(x+s*.137,.799,z+.087)],
                    [(0,1,2,3),(4,5,1,0),(0,3,4),(1,5,2),(4,3,2,5)],ridge,smoothing=True)
        bevel=brow.modifiers.new("Sculpted edge softness","BEVEL")
        bevel.width=.012; bevel.segments=2
        for i in range(3):
            xx=cx+s*(1.40+i*.095)
            k.tube("Shark • dark gill grooves",c,[(xx,1.38+i*.08,1.27),(xx+.04*s,1.22+i*.12,1.13),
                   (xx,1.26+i*.12,1.03)],.021,dark)
    dorsal=k.mesh("Shark • towering dorsal fin",c,
                [(cx-.28,1.45,1.74),(cx-.51,2.39,2.89),(cx-.17,3.26,1.23),
                 (cx-.55,1.64,1.72),(cx-.59,2.41,2.83),(cx-.64,3.18,1.25)],
                [(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],skin, smoothing=True)
    b=dorsal.modifiers.new("Rounded fin edges","BEVEL");b.width=.041;b.segments=3
    k.apply_prop_ink(dorsal,c,thickness=.013)


def flower(c,p,r,style):
    colors=[("#ec73a5","#f6bc65"),("#9b60cf","#efbd6a"),("#d75659","#ffd775"),("#52a8a0","#ffe09d")]
    name="Flower"
    petal,core=colors[style%4]
    if not bpy.data.materials.get(petal): k.surface(petal,petal,glow=.10)
    if not bpy.data.materials.get(core): k.surface(core,core,glow=.13)
    m=bpy.data.materials[petal]; q=bpy.data.materials[core]
    x,y,z=p
    for j in range(5):
        a=j*TAU/5
        o=k.ball(name+" • petals",c,(x+r*.82*math.cos(a),y,z+r*.82*math.sin(a)),
                 (r*.73,.038,r*.42),m,segments=7,rings=4)
        o.rotation_euler.y=-a
    k.ball(name+" • pollen",c,(x,y-.025,z),(r*.51,.041,r*.51),q,segments=8,rings=6)


def peacock(c,x,y,z):
    palette=[k.surface("Relief • oxidized turquoise","#3f8d87",.48,.32,glow=.12),
             k.surface("Relief • petrol feathers","#3b436c",.55,.40),
             k.surface("Relief • gilded filigree","#bb8561",.56,.43,glow=.10)]
    for j in range(11):
        a=-.94+1.88*j/10
        ex=x+.71*math.sin(a)
        ez=z+.97*math.cos(a)
        k.tube("Peacock relief • gilded rill",c,[(x,y,z-.18),(x+(ex-x)*.52,y-.026,z+.30),(ex,y-.031,ez)],.031,palette[2])
        o=k.ball("Peacock relief • enamel eyespot",c,(ex,y-.056,ez),(.071,.043,.112),
                 palette[0] if j%2==0 else palette[1],segments=12,rings=8)
        o.rotation_euler.y=a
    k.tube("Peacock relief • curved neck",c,[(x-.12,y-.10,z-.20),(x+.08,y-.105,z+.19),
           (x+.05,y-.10,z+.42),(x+.19,y-.11,z+.51)],.09,palette[0])
    k.ball("Peacock relief • head",c,(x+.21,y-.115,z+.52),(.115,.072,.091),palette[2],segments=12,rings=10)


def chair(c,x,y,m):
    box("Wicker seat",c,(x,y,.40),(.58,.50,.057),m,.031,True)
    for dx in (-.26,.26):
        k.tube("Wicker • bent frame",c,[(x+dx,y-.25,.01),(x+dx,y-.23,.39),
               (x+dx,y+.22,.43),(x+dx,y+.25,.92)],.031,m)
        tapered_between("Wicker • rear foot",c,(x+dx,y+.26,.01),(x+dx,y+.22,.44),.024,.028,m)
    for i in range(8):
        yy=y-.23+i*.064
        tapered_between("Wicker web • seat",c,(x-.267,yy,.433),(x+.267,yy,.433),.007,.007,m,6)
    for i in range(12):
        xx=x-.254+i*.046
        tapered_between("Wicker web • back",c,(xx,y+.225,.44),(xx,y+.252,.91),.010,.010,m,6)
    for i in range(6):
        z=.48+i*.081
        tapered_between("Wicker web • back weave",c,(x-.257,y+.236,z),(x+.257,y+.236,z),.012,.012,m,6)


def cone(c,x,y,rng):
    foliage=k.surface("Flower tower • dark emerald","#2c5c45",glow=.12)
    k.cylinder("Floral cone • topiary",c,(x,y,1.03),.56,2.05,foliage,r2=.055)
    for j in range(30):
        z=.14+(j/30)*1.80
        a=(j*2.399)%(math.tau)
        r=.54*(1-z/2.10)
        flower(c,(x+r*math.cos(a),y+r*math.sin(a),z),rng.uniform(.076,.126),j)


def stripe_leg(c,x,y,spread,black,white):
    n=32
    rows=[(x+spread*.13,y,.31,.22,.21),(x+spread*.13,y+.012,.65,.225,.233),
          (x+spread*.11,y+.082,1.05,.263,.258),(x+spread*.06,y+.145,1.52,.304,.29),
          (x,y+.18,1.89,.330,.312)]
    vv=[(xc+rx*math.cos(a*TAU/n),yc+ry*math.sin(a*TAU/n),z)
        for xc,yc,z,rx,ry in rows for a in range(n)]
    ff=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i)
        for j in range(len(rows)-1) for i in range(n)]
    obj=k.mesh("Ringmaster • black and ivory striped trousers",c,vv,ff,black,smoothing=True)
    obj.data.materials.append(white)
    for p in obj.data.polygons: p.material_index=(p.index%n)//2%2
    k.apply_prop_ink(obj,c,thickness=.017)


def statue(c,x,y,black,white,gold):
    coat=k.surface("Ringmaster • plum-black wool","#241c2c",.70,glow=.085)
    red=k.surface("Ringmaster • ring-red lapels","#a83742",.62,glow=.12)
    paint=k.surface("Ringmaster • matte carved face","#c49b8e",.77)
    matte(paint,.77,.11)
    for s in [-1,1]:
        xx=x+s*.34
        boot=k.ball("Ringmaster • colossal leather boot",c,(xx,y-.24,.181),(.30,.54,.185),black,segments=28,rings=16)
        k.apply_prop_ink(boot,c,thickness=.017)
        box("Ringmaster • layered boot sole",c,(xx,y-.27,.085),(.57,.94,.117),black,.045,True)
        k.cylinder("Ringmaster • boot cuff",c,(xx,y,.318),.255,.29,black)
        stripe_leg(c,xx,y,s,black,white)
    torso=k.ball("Ringmaster • bent tailcoat torso",c,(x,y-.10,2.14),(.64,.445,.75),coat,segments=32,rings=20)
    torso.rotation_euler.x=.59
    k.apply_prop_ink(torso,c,thickness=.016)
    for s in [-1,1]:
        ob=k.ball("Ringmaster • velvet lapel",c,(x+s*.20,y-.51,2.17),(.15,.081,.37),red,segments=18,rings=12)
        ob.rotation_euler.y=s*.33
        k.tube("Ringmaster • long bent coat sleeves",c,[(x+s*.51,y-.23,2.34),
               (x+s*.68,y-.43,2.01),(x+s*.55,y-.67,1.57)],.137,coat)
        k.ball("Ringmaster • sculpted gloved hands",c,(x+s*.55,y-.69,1.56),(.14,.20,.128),white,segments=16,rings=10)
    head=k.ball("Ringmaster • carved face",c,(x,y-.54,2.82),(.34,.327,.37),paint,segments=24,rings=18)
    k.apply_prop_ink(head,c,thickness=.012)
    for s in [-1,1]:
        k.ball("Ringmaster • carved eye",c,(x+s*.108,y-.833,2.85),(.038,.022,.051),black,segments=12,rings=8)
    k.tube("Ringmaster • curled mustache",c,[(x-.14,y-.856,2.73),(x-.067,y-.888,2.705),
           (x,y-.901,2.742),(x+.073,y-.888,2.705),(x+.14,y-.856,2.73)],.022,black)
    k.cylinder("Ringmaster • stovepipe hat brim",c,(x,y-.53,3.105),.431,.085,black)
    k.cylinder("Ringmaster • top hat",c,(x,y-.53,3.355),.278,.468,coat,r2=.314)
    k.cylinder("Ringmaster • red hat ribbon",c,(x,y-.53,3.186),.295,.081,red)
    k.ball("Ringmaster • brass button",c,(x,y-.55,1.99),(.063,.044,.061),gold,segments=12,rings=8)


def slipper(c,name,p,rose=False):
    sole=k.surface(name+" • moulded sole","#efb0c9" if rose else "#362e3e",.66)
    top=k.surface(name+" • foot bed","#d86495" if rose else "#9e6541",.76,glow=.09)
    upper=k.surface(name+" • strap","#fff0da" if rose else "#724735",.54,glow=.08)
    if rose:
        for pigment in (sole,top,upper):
            matte(pigment,.77,.08)
    group=k.empty(name,c,p)
    bed=k.ball(name+" • flattened sole",c,(0,0,0),(.083,.164,.027),sole,group,segments=32,rings=14)
    k.apply_prop_ink(bed,c,thickness=.005)
    k.ball(name+" • tread face",c,(0,-.004,.019),(.073,.151,.016),top,group,segments=24,rings=12)
    k.tube(name+" • raised V strap",c,[(-.071,.037,.021),(-.044,-.004,.062),
           (0,-.076,.049),(.044,-.004,.062),(.071,.037,.021)],.014,upper,group)
    if rose:
        for j in range(3):
            y=.012+j*.029
            k.ball(name+" • printed spot",c,(.011*(-1)**j,y,.035),(.015,.012,.004),upper,group,segments=10,rings=6)
    return group
