"""Dappled grave, carved stone and the roadside lily memorial."""
import math
from random import Random

from mathutils import Vector
import bpy
from feature_scene import block, daylights, k, line, outdoor_sky


def spray(c,m,name,root,size=1.,incline=0.):
    bouquet=k.empty(name,c,root)
    bouquet.scale=(size,)*3
    bouquet.rotation_euler.y=incline
    moss=k.surface("Florist stems","#3b614c",.82)
    leaf=k.surface("Waxy lily leaves","#628363",.66)
    white=k.surface("Pearl lily petals","#f5ead6",.77,glow=.16)
    white_shadow=k.surface("Pale gray-blue lily petals","#d6dce1",.81,glow=.13)
    ribbon=k.surface("Pale blue woven memorial ribbon","#a3c9e2",.88,glow=.05)
    for j,(x,y,z) in enumerate(((-.107,.06,.29),(.024,-.043,.34),(.112,.043,.303),(.006,.095,.383),(-.135,-.07,.246))):
        line(c,"Fresh-cut long lily stem",[(0,0,.015),(x*.46,y*.65,.171),(x,y,z)],.0058,moss,bouquet)
        for side in (-1,1):
            blade=k.ball("Pointed lily leaf",c,(x*.58+side*.027,y,.115+.026*j),(.012,.010,.067),leaf,bouquet,
                         segments=9,rings=6)
            blade.rotation_euler.y=side*.67
        for p in range(6):
            a=p*math.tau/6+j*.47
            petal=k.ball("Ivory trumpet lily petal",c,(x+.030*math.cos(a),y+.030*math.sin(a),z+.016),
                         (.049,.020,.011),white if p%3 else white_shadow,bouquet,segments=12,rings=7)
            petal.rotation_euler=(0,.16*math.sin(a),a)
            line(c,"Slim ochre lily stamen",[(x,y,z+.009),(x+.011*math.cos(a),y+.011*math.sin(a),z+.035)],
                 .0035,m["gold"],bouquet)
        k.ball("Green star in lily throat",c,(x,y,z+.011),(.015,.014,.008),leaf,bouquet,segments=10,rings=6)
    for side in (-1,1):
        line(c,"Knotted sky-blue lily bow",[(0,-.012,.108),(side*.046,-.015,.140),(side*.071,-.018,.121),
             (side*.035,-.026,.089),(0,-.012,.108),(side*.065,-.019,.033)],.014,ribbon,bouquet)
    return bouquet


def layered_shape(c,name,profile,front,back,material):
    points=[(x,front,z) for x,z in profile]+[(x,back,z) for x,z in profile]
    n=len(profile)
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    faces += [(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    return k.mesh(name,c,points,faces,material)


def marker(c,m,x,y,s=1.,hero=False):
    stone=k.surface("Honed pale blue-gray memorial stone" if hero else "Weathered background slate",
                    "#a1afbb" if hero else "#85909a",.84)
    profile=[(-.42,0),(.42,0),(.42,.81)]
    profile += [(.42*math.cos(a),.81+.31*math.sin(a)) for a in (.16,.42,.73,1.03,1.31,1.57,1.83,2.12,2.4,2.72,2.98,math.pi)]
    stone_object=layered_shape(c,"Arch-top blue gray gravestone",[(x+a*s,b*s) for a,b in profile],y-.09*s,y+.13*s,stone)
    bevel=stone_object.modifiers.new("Hand-dressed softly chipped stone edges","BEVEL")
    bevel.width=.038*s
    bevel.segments=3
    block(c,"Broad sanctuary stone base",(x,y-.015*s,.081*s),(.96*s,.43*s,.162*s),stone)
    if not hero:
        return
    tree=stone.node_tree
    bsdf=next(node for node in tree.nodes if node.type=="BSDF_PRINCIPLED")
    coords=tree.nodes.new("ShaderNodeTexCoord")
    flecks=tree.nodes.new("ShaderNodeTexVoronoi")
    flecks.inputs["Scale"].default_value=127
    stones=tree.nodes.new("ShaderNodeValToRGB")
    k.look._ramp(stones,[(.14,"#567185"),(.30,"#8497a7"),(.42,"#a4b5bb"),(.54,"#c9c5b7")])
    tree.links.new(coords.outputs["Object"],flecks.inputs["Vector"])
    tree.links.new(flecks.outputs["Distance"],stones.inputs[0])
    tree.links.new(stones.outputs["Color"],bsdf.inputs["Base Color"])
    for dx in (-.36,.36):
        line(c,"Weathered chamfer shading on the stone edge",[(x+dx,y-.092,.23),(x+dx,y-.092,.71),
             (x+.92*dx,y-.092,.87),(x+.78*dx,y-.092,.968)],.006,m["blue"])
    for z in (.285,.322,.37):
        line(c,"Short engraved water ripple",[(x-.196,y-.094,z),(x-.096,y-.094,z+.014),
             (x+.01,y-.095,z-.005),(x+.12,y-.094,z+.010),(x+.201,y-.094,z)],.005,m["blue"])
    shade=k.surface("Engraving inside the whale recess","#3d596b",.88)
    inner=k.surface("Stone rim catching sunlight inside carving","#6f8999",.86)
    whale=[(-.257,.641),(-.204,.627),(-.170,.544),(-.143,.566),(-.096,.602),
           (-.016,.627),(.059,.630),(.122,.612),(.171,.575),(.174,.531),(.15,.488),
           (.108,.461),(.047,.452),(-.036,.463),(-.113,.492),(-.153,.516),(-.187,.489),
           (-.236,.475),(-.213,.523),(-.197,.558),(-.24,.593)]
    cutter=layered_shape(c,"Whale engraving cutter",[(x+u,v) for u,v in reversed(whale)],y-.17,y-.062,shade)
    cut=stone_object.modifiers.new("Recess the whale into the granite","BOOLEAN")
    cut.object=cutter
    cut.operation="DIFFERENCE"
    bpy.context.view_layer.objects.active=stone_object
    bpy.ops.object.modifier_apply(modifier=cut.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    layer=layered_shape(c,"Blue-grey shadow at the back of the whale recess",[(x+u,v) for u,v in whale],y-.066,y-.061,shade)
    line(c,"Soft stone edge inside the whale carving",[(x+u,y-.095,v) for u,v in whale[8:15]],.005,inner)
    k.ball("Single recessed friendly whale eye",c,(x+.104,y-.096,.566),(.011,.003,.010),m["ink"],
           segments=12,rings=7)
    line(c,"Shallow whale smile groove",[(x+.102,y-.097,.514),(x+.130,y-.097,.510),(x+.154,y-.097,.521)],.005,m["ink"])
    for dx,toz in ((-.044,.686),(.016,.735),(.071,.697)):
        line(c,"Whale water spout cut into the stone",[(x+.017,y-.094,.653),(x+dx*.75,y-.095,toz-.019),
             (x+dx,y-.096,toz)],.006,shade)
    for dx in (-.30,.27):
        line(c,"Small stone wear lines",[(x+dx,y-.092,.305),(x+dx+.03,y-.093,.321),(x+dx+.042,y-.093,.345)],.004,inner)


def cemetery(c,m):
    outdoor_sky(c,m)
    for obj in tuple(c.objects):
        if obj.name.startswith(("Forked street tree trunk","Organic overlapping leafy lobe")):
            bpy.data.objects.remove(obj,do_unlink=True)
    daylights(c)
    block(c,"Broad soft-green cemetery lawn",(0,2.9,-.099),(18,19,.199),m["grass"])
    block(c,"Cemetery winding gravel path",(-1.72,2.4,-.007),(1.09,10.6,.020),m["ground"])
    for x,y,s in ((0,.41,1),(-1.42,1.68,.63),(1.54,2.04,.64),(-.85,3.39,.72),(1.99,4.2,.58),(-2.42,4.15,.49),
                 (.83,4.27,.63),(3.07,4.12,.59),(-3.57,4.21,.70)):
        marker(c,m,x,y,s,hero=(x==0))
    for x,y,angle,s in ((-.31,.083,-.49,.74),(.30,.081,.57,.63),(.07,-.02,-.83,.62)):
        bouquet=spray(c,m,"White lilies around the grave",(x,y,0),s,angle)
        bouquet.rotation_euler.x=.55
    cream=k.surface("White-lime houses beyond the cemetery","#c0bfce",.82)
    roof=k.surface("Church blue-gray slate roof","#536071",.79)
    for j,x in enumerate((-6.8,-4.7,-2.49,1.1,3.22,5.1,7.2)):
        y=7.0+.28*(j%3)
        z=1.+.32*(j%2)
        block(c,"Distant white stucco house",(x,y,z/2),(1.94,.82,z),cream)
        layer=layered_shape(c,"Triangular distant slate roof",[(x-1.02,z),(x+1.02,z),(x,z+.59)],y-.49,y+.48,roof)
        for u in (-.67,-.04,.64):
            block(c,"Distant leaded glass house window",(x+u,y-.423,z*.63),(.32,.012,.28),m["dark"])
            block(c,"Limestone window lip",(x+u,y-.437,z*.63-.15),(.40,.044,.046),m["cream"])
            block(c,"Window frame mullion",(x+u,y-.435,z*.63),(.022,.014,.28),m["cream"])
    block(c,"Church with old white stone exterior",(2.87,8.41,1.72),(1.17,1.11,3.44),cream)
    steeple=k.cylinder("Old church steeple",c,(2.87,8.41,4.08),.72,1.54,roof,r2=.032,length_segments=4)
    steeple.rotation_euler.z=math.pi/4
    line(c,"Church spire cross",[(2.63,8.41,4.97),(3.11,8.41,4.97)],.034,m["dark"])
    line(c,"Church spire cross post",[(2.87,8.41,4.75),(2.87,8.41,5.28)],.034,m["dark"])
    for x in (2.58,3.16):
        block(c,"Tall dark lancet window",(x,7.84,2.69),(.22,.025,.83),m["dark"])
    for j in range(26):
        x=(j-12.5)*.61
        block(c,"Distant low cemetery stone boundary",(x,5.75,.31),(.60,.18,.65),cream)
        block(c,"Cemetery boundary cap",(x,5.73,.646),(.56,.205,.075),m["ground"])
    for x,y,z in ((-1.88,1.94,2.86),(2.42,3.65,3.05)):
        for j in range(4):
            tip=(x+.95*math.sin(j*2.4),y+.68*math.cos(j*2.4),z+.34*(j%3))
            line(c,"Forked mature cemetery oak limb",[(x,y,0),(x+.031,y,1.94+j*.132),tip],
                 .088 if j else .178,m["wood"])
        greens=[k.surface("Oak canopy greens "+color,color,.86) for color in ("#345947","#527b53","#789752","#a4ab6f")]
        rng=Random(round(400+100*x))
        for j in range(41):
            a=j*2.4
            radius=rng.uniform(.39,1.55)
            leaf=k.ball("Dappled mature oak leaf cluster",c,(x+math.cos(a)*radius,y+math.sin(a)*radius,
                 z+rng.uniform(-.53,.52)),(.59,.53,.31),greens[j%4],segments=12,rings=8)
    verts=[]
    rng=Random(98)
    for _ in range(1460):
        x,y=rng.uniform(-4,4),rng.uniform(-1.5,5.6)
        if -2.24<x<-1.20 or abs(x)<.51 and abs(y-.42)<.34:
            continue
        z=rng.uniform(.021,.085)
        verts.extend(((x-.019,y,.003),(x+.011,y+.001,.003),(x+.043,y-.019,z)))
    tuft=k.surface("Individual dappled grass blades","#b5bf7b",.81)
    tuft_obj=k.mesh("Low triangle grass blade highlights",c,verts,[tuple(range(i,i+3)) for i in range(0,len(verts),3)],tuft)
    tuft_obj.data.materials.append(k.surface("Dark blue-green grass in the shade","#465944",.84))
    for index,polygon in enumerate(tuft_obj.data.polygons):
        polygon.material_index=index%2
