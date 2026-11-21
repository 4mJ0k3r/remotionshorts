"""Practical lighting, textured architecture, and hero props for seven stages."""
import math
import random
from pathlib import Path

import bpy

from importlib.util import module_from_spec, spec_from_file_location

spec = spec_from_file_location('washroom_primitives', Path(__file__).resolve().parents[1] / 'washroom_experiment' / 'sets.py')
primitives = module_from_spec(spec)
spec.loader.exec_module(primitives)
Stage, rgb = primitives.Stage, primitives.rgb


def textured(g, name, dark, light, scale=5, brick=False, ground=False, cobble=False):
    cache=('surface',name,dark,light)
    if cache in g.materials:return g.materials[cache]
    mat = g.mat(light).copy()
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    p = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nodes.new('ShaderNodeTexBrick' if brick else 'ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = scale
    coord = nodes.new('ShaderNodeTexCoord')
    if brick:
        separate = nodes.new('ShaderNodeSeparateXYZ'); combine = nodes.new('ShaderNodeCombineXYZ')
        links.new(coord.outputs['Object'], separate.inputs[0])
        for source, target in [('X','X'),('Y','Z'),('Z','Y')]:
            links.new(separate.outputs[source], combine.inputs[target])
        links.new(combine.outputs[0], tex.inputs['Vector'])
        tex.inputs['Color1'].default_value = (*rgb(dark), 1)
        tex.inputs['Color2'].default_value = (*rgb(light), 1)
        tex.inputs['Mortar'].default_value = (*rgb('4b3947'), 1)
        tex.inputs['Mortar Size'].default_value = .014
        links.new(tex.outputs['Color'], p.inputs['Base Color'])
    else:
        links.new(coord.outputs['Object'], tex.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        for e, c in zip(ramp.color_ramp.elements, (dark, light)):
            e.color = (*rgb(c), 1)
        links.new(tex.outputs['Fac'], ramp.inputs[0]); links.new(ramp.outputs[0], p.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .25 if ground else .19
    bump.inputs['Distance'].default_value = .032 if ground else .04
    height=tex.outputs['Fac']
    if name in ('Sidewalk stone','Damp asphalt'):
        micro=nodes.new('ShaderNodeTexNoise');micro.inputs['Scale'].default_value=87
        links.new(coord.outputs['Object'],micro.inputs['Vector'])
        aggregate=nodes.new('ShaderNodeMath');aggregate.operation='MULTIPLY_ADD';aggregate.inputs[1].default_value=.33
        links.new(micro.outputs['Fac'],aggregate.inputs[0]);links.new(height,aggregate.inputs[2]);height=aggregate.outputs[0]
    if cobble:
        cells=nodes.new('ShaderNodeTexVoronoi');cells.voronoi_dimensions='2D';cells.feature='DISTANCE_TO_EDGE';cells.inputs['Scale'].default_value=5.5
        links.new(coord.outputs['Object'],cells.inputs['Vector'])
        joints=nodes.new('ShaderNodeMapRange');joints.interpolation_type='SMOOTHERSTEP';joints.inputs['From Max'].default_value=.11
        links.new(cells.outputs['Distance'],joints.inputs['Value'])
        grit=nodes.new('ShaderNodeMath');grit.operation='MULTIPLY_ADD';grit.inputs[1].default_value=.24
        links.new(height,grit.inputs[0]);links.new(joints.outputs[0],grit.inputs[2]);height=grit.outputs[0]
        color=nodes.new('ShaderNodeMixRGB');color.blend_type='MIX';color.inputs[1].default_value=(*rgb('7b6658'),1)
        links.new(joints.outputs[0],color.inputs[0]);links.new(ramp.outputs[0],color.inputs[2]);links.new(color.outputs[0],p.inputs['Base Color'])
    links.new(height, bump.inputs['Height']); links.new(bump.outputs[0], p.inputs['Normal'])
    roughness = nodes.new('ShaderNodeMapRange')
    roughness.inputs['To Min'].default_value = .18 if ground else .34; roughness.inputs['To Max'].default_value = .55 if ground else .72
    links.new(tex.outputs['Fac'], roughness.inputs['Value']); links.new(roughness.outputs[0], p.inputs['Roughness'])
    if ground:
        p.inputs['Specular IOR Level'].default_value=.34
        p.inputs['Coat Weight'].default_value=.12 if 'asphalt' in name or 'Sidewalk' in name else .045
        p.inputs['Coat Roughness'].default_value=.32
    mat.name = name
    g.materials[cache]=mat
    return mat


def leaves(g, root, x, y, z=.43, spread=1, seed=4, count=245, core=None):
    from mathutils import Vector
    rng=random.Random(seed);vertices=[];faces=[];tones=[]
    m=[textured(g,'Foliage interior','132a17','214b2b',18),textured(g,'Foliage midtones','2d6a35','448848',23),textured(g,'Foliage tips','438d48','65c466',27)]
    lobes=[(rng.uniform(-.79,.79),rng.uniform(-.28,.27),rng.uniform(-.19,.21),rng.uniform(.23,.43)) for _ in range(15)]
    for i in range(count):
        lx,ly,lz,rad=lobes[i%len(lobes)]
        a=rng.uniform(0,math.tau);e=rng.uniform(-1,1);s=math.sqrt(1-e*e);extent=rng.uniform(.21,1)*rad
        p=Vector(((lx+extent*math.cos(a)*s)*spread,(ly+extent*math.sin(a)*s)*spread,(lz+extent*e*.78)*spread))
        if core and i%2==0:
            center,radii=core
            theta=rng.uniform(-2.86,-.20);height=rng.uniform(-.40,.94);ring=math.sqrt(1-height*height)
            p=Vector(center)+Vector((radii[0]*ring*math.cos(theta),radii[1]*ring*math.sin(theta),radii[2]*height))*rng.uniform(1.02,1.14)
        u=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.64,.8))).normalized()
        v=u.cross(Vector((rng.uniform(-.65,.65),rng.uniform(-.65,.65),1))).normalized();n=u.cross(v)
        length=rng.uniform(.091,.25)*spread;width=length*rng.uniform(.24,.48);bend=width*rng.uniform(.14,.45)
        index=len(vertices)
        profile=[(-.70,0),(-.47,-.51),(-.22,-.83),(.04,-.95),(.32,-.62),(.64,0),(.32,.58),(.03,.92),(-.22,.82),(-.49,.47)]
        vertices.extend(p+u*(t*length)+v*(w*width)+n*(bend*abs(t)) for t,w in profile)
        vertices.append(p-n*bend)
        for j in range(10):
            faces.append((index+10,index+j,index+(j+1)%10))
            tones.append(0 if extent<rad*.55 and e<.35 else 2 if e>.34 and rng.random()>.29 else 1)
    mesh=bpy.data.meshes.new('Folded and serrated leaf mesh');mesh.from_pydata(vertices,[],faces);mesh.update()
    for material in m:mesh.materials.append(material)
    for polygon,index in zip(mesh.polygons,tones):polygon.material_index=index
    return g.link('Layered shrub foliage',mesh,root,(x,y,z))


def daylight_backdrop(g,root):
    # A distance-controlled sky plate keeps the horizon low behind the architecture.
    mat=bpy.data.materials.new('Day sky with three atmospheric stops');mat.use_nodes=True
    n,l=mat.node_tree.nodes,mat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial')
    tex=n.new('ShaderNodeTexCoord');axis=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Generated'],axis.inputs[0])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE';l.new(axis.outputs['Z'],ramp.inputs[0])
    for element,position,color in zip((ramp.color_ramp.elements[0],ramp.color_ramp.elements.new(.30),ramp.color_ramp.elements[-1]),(.035,.30,.68),('e8e5d4','5eb5e4','2362a9')):
        element.position=position;element.color=(*rgb(color),1)
    em=n.new('ShaderNodeEmission');l.new(ramp.outputs[0],em.inputs[0]);em.inputs[1].default_value=1.08;l.new(em.outputs[0],out.inputs[0])
    sky=g.box('Azure gradient sky beyond horizon',(0,17,11.7),(46,.08,25),mat,root,0)
    haze=bpy.data.materials.new('Faint low-altitude atmospheric haze');haze.use_nodes=True;haze.surface_render_method='BLENDED'
    n,l=haze.node_tree.nodes,haze.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial')
    tex=n.new('ShaderNodeTexCoord');axis=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Generated'],axis.inputs[0]);fade=n.new('ShaderNodeValToRGB');l.new(axis.outputs['Z'],fade.inputs[0])
    for element,value in zip(fade.color_ramp.elements,(.32,0)):element.color=(value,value,value,1)
    blend=n.new('ShaderNodeMixShader');l.new(fade.outputs[0],blend.inputs[0]);transparent=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(*rgb('c0dce1'),1)
    l.new(transparent.outputs[0],blend.inputs[1]);l.new(em.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs[0])
    g.box('Mist band behind architecture',(0,12.5,1.36),(31,.016,3),haze,root,0)
    return sky


def bush_core(g, root, xyz, size, seed):
    import bmesh
    rng=random.Random(seed);mesh=bmesh.new()
    for x,y,z,s in ((0,0,0,1),(-.62,.07,-.15,.54),(.59,-.05,-.12,.58),(-.26,.03,.45,.54),(.35,-.10,.37,.53)):
        verts=bmesh.ops.create_uvsphere(mesh,u_segments=32,v_segments=18,radius=1)['verts']
        for v in verts:
            a,b,c=v.co
            bump=1+.068*math.sin(11*a+4*c)*math.cos(9*b-3*a)+rng.uniform(-.047,.047)
            v.co=((x+a*s*bump)*size[0],(y+b*s*bump)*size[1],(z+c*s*bump)*size[2])
    data=bpy.data.meshes.new('Closed overlapping rough shrub cores');mesh.to_mesh(data);mesh.free();data.update()
    mat=textured(g,'Forest green shrub core','0d2512','15351a',25)
    p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    for link in tuple(p.inputs['Roughness'].links):mat.node_tree.links.remove(link)
    p.inputs['Roughness'].default_value=.9
    data.materials.append(mat)
    for face in data.polygons:face.use_smooth=True
    return g.link('Opaque forest-green shrub core',data,root,xyz)


def windows(g, root, x, y, z, w=.65, h=.95, daylight=False):
    g.box('Window recessed surround',(x,y,z),(w+.14,.14,h+.13),g.mat('222637'),root,.02)
    glass=g.mat('7094ab',metal=.12,rough=.29) if daylight else g.mat('ffc56d',em=1.35)
    g.box('Daytime unlit window' if daylight else 'Warm window glass',(x,y-.09,z),(w,.035,h),glass,root,.008)
    g.batch('Window mullions',[((x,y-.125,z),(.039,.032,h)),((x,y-.125,z),(w,.032,.037)),((x,y-.14,z-h/2-.04),(w+.18,.26,.06))],g.mat('513c45'),root,.006)


def lamp(g, root, x, y, z=2.9):
    dark=g.mat('202c39',metal=.6); glow=g.mat('ffd192',em=4)
    g.rod('Iron streetlamp',(x,y,0),(x,y,z),.055,dark,root)
    g.ball('Warm practical bulb',(x,y,z),(.14,.14,.2),glow,root)
    for dz in (-.20,.19): g.ball('Lantern iron cap',(x,y,z+dz),(.19,.19,.056),dark,root)
    g.light('Streetlamp pool','POINT',(x,y-.14,z-.03),(x,y,0),78,'ffc174',root)


def cloth(g, root, p, stains=False):
    x,y,z=p; mesh=bpy.data.meshes.new('Pleated silk grid'); verts=[]; faces=[]
    for j in range(17):
        for i in range(17):
            u=(i-8)/16; v=(j-8)/16
            verts.append((u*.48, .028*math.cos(u*23+v*2)*math.cos(v*3), v*.43))
    for j in range(16):
        for i in range(16):
            a=j*17+i;faces.append((a,a+1,a+18,a+17))
    mesh.from_pydata(verts,[],faces); mesh.update()
    mesh.materials.append(g.mat('ac2146',metal=.19,rough=.31));mesh.materials.append(g.mat('e7ac50',metal=.46,rough=.29))
    for face in mesh.polygons:
        j,i=divmod(face.index,16); face.material_index=int(min(i,j,15-i,15-j)==0); face.use_smooth=True
    obj=g.link('Crimson silk with gold selvage',mesh,root,p)
    if stains:
        for dx,dz,s in [(-.08,.01,.06),(.02,-.056,.087),(.096,.047,.045),(-.068,-.105,.025)]:
            surface=.028*math.cos(dx/.48*23+dz/.43*2)*math.cos(dz/.43*3)
            g.ball('Old brown stain',(dx,surface-.016,dz),(s,.031,s*.62),g.mat('52332e',rough=.9),obj)
    return obj


def silk_frame(g,root,p):
    x,y,z=p; gold=g.mat('d29848',metal=.67,rough=.28)
    g.box('Velvet frame lining',p,(.8,.09,.94),g.mat('252130'),root)
    for w,h in [(.9,1.04),(.83,.96),(.74,.87)]:
        g.batch('Bevelled gilded frame rails', [((x,y-.066,z+sign*h/2),(w+.036,.095,.046)) for sign in (-1,1)]+[((x+sign*w/2,y-.066,z),(.046,.095,h)) for sign in (-1,1)],gold,root,.018)
    return cloth(g,root,(x,y-.12,z),True)


def shopping_cart(g,r):
    cart=g.link('Rusty shopping trolley',p=r,xyz=(-2.63,.45,0));iron=g.mat('a08175',metal=.62,rough=.39)
    rubber=g.mat('332d42',rough=.7);steel=g.mat('b6a5a3',metal=.72,rough=.32)
    for x in (-.29,.29):
        g.rod('Lower cart frame',(x,-.27,.247),(x,.27,.247),.024,iron,cart)
        for y in (-.25,.25):
            g.box('Caster mounting plate',(x,y,.227),(.13,.105,.024),steel,cart)
            g.rod('Caster swivel pin',(x,y,.133),(x,y,.224),.022,steel,cart)
            for sign in (-1,1):
                g.rod('Steel caster fork',(x,y+sign*.039,.077),(x,y+sign*.029,.159),.015,steel,cart)
            g.rod('Rubber caster tread',(x,y-.032,.075),(x,y+.032,.075),.073,rubber,cart)
            g.rod('Steel wheel axle',(x,y-.05,.075),(x,y+.05,.075),.023,steel,cart)
            g.rod('Cart uprights to basket',(x,y,.25),(x*1.1,y,.37),.021,iron,cart)
    for y in (-.258,.258):g.rod('Cart lower frame crossbar',(-.3,y,.247),(.3,y,.247),.023,iron,cart)
    for i in range(5):
        z=.36+i*.088
        g.curve('Wire basket horizontal',[(x,y,z) for x,y in [(-.32,-.26),(.32,-.26),(.32,.26),(-.32,.26)]],.011,iron,cart,True)
    for i in range(11):
        x=(i-5)*.060
        for y in (-.26,.26):g.rod('Wire basket upright',(x,y,.35),(x,y,.72),.01,iron,cart)
        g.rod('Wire basket base',(x,-.26,.36),(x,.26,.36),.01,iron,cart)
    for i in range(7):
        y=(i-3)*.078
        for x in (-.32,.32):g.rod('Wire basket end upright',(x,y,.35),(x,y,.72),.01,iron,cart)
    for y in (-.22,.22):g.rod('Push handle support',(-.32,y,.67),(-.46,y,.82),.018,iron,cart)
    g.rod('Oxide red push grip',(-.46,-.24,.82),(-.46,.24,.82),.026,g.mat('933e3b'),cart)
    board=textured(g,'Corrugated cardboard','815938','bd9262',13)
    for x in (-.30,-.015):g.box('Carton side wall',(x,-.015,.54),(.017,.29,.30),board,cart)
    for y in (-.161,.131):g.box('Carton end wall',(-.16,y,.54),(.286,.018,.30),board,cart)
    g.box('Carton floor',(-.16,-.015,.39),(.29,.29,.024),board,cart)
    for sign in (-1,1):
        lid=g.box('Angled carton flap',(-.158,-.015+sign*.213,.728),(.29,.15,.014),board,cart);lid.rotation_euler.x=sign*.43
        lid=g.box('Short carton flap',(-.16+sign*.189,-.015,.717),(.11,.28,.014),board,cart);lid.rotation_euler.y=-sign*.53
    g.box('Carton packing tape',(-.159,-.174,.52),(.034,.008,.21),g.mat('d5a866'),cart,.003)
    melon=g.mat('32692e',rough=.38).copy();melon.name='Procedural striped watermelon rind'
    n,l=melon.node_tree.nodes,melon.node_tree.links;bsdf=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    coords=n.new('ShaderNodeTexCoord');wave=n.new('ShaderNodeTexWave');wave.bands_direction='X';wave.inputs['Scale'].default_value=3.2;wave.inputs['Distortion'].default_value=3.0
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*rgb('193d24'),1);ramp.color_ramp.elements[1].color=(*rgb('88a94d'),1)
    l.new(coords.outputs['Generated'],wave.inputs['Vector']);l.new(wave.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bsdf.inputs['Base Color'])
    g.ball('Striped watermelon',(.155,-.069,.545),(.147,.15,.141),melon,cart)
    g.rod('Rolled blanket cloth',(-.02,.146,.507),(.284,.146,.507),.091,textured(g,'Blanket yarn','644c69','a5849b',29),cart)
    for x in (.282,.286,.290):g.rod('Blanket rolled spiral',(x,.146,.507),(x+.004,.146,.507),.077-(x-.282)*5,g.mat('b59aa6' if x!=.286 else '755b78'),cart)
    a=(.198,.13,.46);b=(.366,.23,.987)
    g.rod('Umbrella center shaft',a,b,.019,steel,cart)
    from mathutils import Vector
    axis=(Vector(b)-Vector(a)).normalized();base=Vector(a)+axis*.09;end=Vector(b)-axis*.03
    u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u)
    for i in range(8):
        angle=i*math.tau/8; radial=math.cos(angle)*u+math.sin(angle)*v
        g.curve('Folded umbrella rib',[base,base.lerp(end,.55)+radial*.063,end],.013,g.mat('944963' if i%2 else 'bb657d'),cart)
    g.curve('Curved umbrella grip',[b,(.392,.239,1.055),(.446,.247,1.065),(.471,.247,1.018)],.021,g.mat('51333e'),cart)


def street(g,r):
    g.box('Slate roadway',(0,-2.1,-.18),(34,7,.29),textured(g,'Damp asphalt','1f273d','414258',12,ground=True),r)
    concrete=textured(g,'Sidewalk stone','676271','a59a96',8,ground=True)
    g.box('Stone pavement',(0,1.9,-.08),(34,4,.16),textured(g,'Sidewalk stone','676271','a59a96',8,ground=True),r)
    g.box('Concrete curb apron under stiletto insert',(1.14,-.91,-.042),(1.8,.62,.078),concrete,r,.008)
    for x in range(-13,15):
        g.box('Cut curb',(x,-.12,.014),(.98,.21,.13),g.mat('a59c9d'),r)
    for i,x in enumerate((-10,-5.8,-1.5,2.8,7.1,11.4)):
        h=5.2+(i%3)*.6
        g.box('Brick apartments',(x,5.9,h/2),(4.0,1.05,h),textured(g,'Apartment masonry',('643d51' if i%2 else '303858'),('9e5c55' if i%2 else '465679'),3,True),r)
        for j in range(3):
            for dx in (-1.2,0,1.2): windows(g,r,x+dx,5.3,1.38+j*1.36)
        for zz in (.47,h-.12):g.box('Stone facade ledge',(x,5.28,zz),(4.05,.23,.14),g.mat('816777'),r)
        for n in range(12):
            awning=g.box('Striped bistro awning',(x+(n-5.5)*.26,5.02,.99),(.261,.68,.055),g.mat(('8e3145','d2a38a')[n%2]),r,.008);awning.rotation_euler.x=.23
    for x in (-4.5,1.2,6.2):lamp(g,r,x,2.8)
    g.box('Stone planter',(-1.22,.81,.15),(1.92,.82,.30),g.mat('685868'),r,.065)
    bush_core(g,r,(-1.22,.69,.51),(.91,.39,.29),9)
    leaves(g,r,-1.22,.68,.46,1.10,count=456,core=((0,.01,.05),(.91,.39,.29))); leaves(g,r,-1.33,1.25,.62,.82,12)
    shopping_cart(g,r)
    car=g.link('Black luxury limousine',p=r,xyz=(1.32,.06,.0)); black=g.mat('141626',metal=.72,rough=.2); gold=g.mat('d29a37',metal=.72,rough=.24); red=g.mat('7a173d')
    g.box('Rounded lower coachwork',(0,0,.64),(3.57,1.08,.52),black,car,.21)
    g.box('Coach roof',(-.11,.03,1.27),(2.23,.99,.14),black,car,.066)
    g.box('Tinted windows',(-.11,.035,1.04),(2.11,.95,.38),g.mat('28304d',metal=.37,rough=.18),car,.072)
    g.box('Crimson leather interior',(-.28,-.34,.85),(1.48,.27,.28),red,car,.077)
    g.box('Gold sill',(0,-.53,.67),(3.15,.035,.035),gold,car)
    door=g.link('Passenger door mechanical hinge',p=car,xyz=(.58,-.55,.61))
    g.box('Passenger exterior door',(-.44,0,.19),(.91,.09,.43),black,door,.057)
    g.box('Red door leather',(-.44,.053,.19),(.83,.033,.31),red,door,.044)
    g.box('Gold door handle',(-.68,-.057,.32),(.19,.03,.029),gold,door,.009)
    g.box('Polished tall grille',(1.8,0,.70),(.055,.56,.41),gold,car,.031)
    for i in range(13):g.box('Grille flute',(1.838,(i-6)*.041,.70),(.012,.016,.35),black,car,.002)
    for y in (-.35,.35):g.box('Headlamp',(1.77,y,.80),(.07,.20,.09),g.mat('fff2bf',em=4),car,.03)
    rims=[]
    for x in (-1.13,1.10):
        for y in (-.53,.53):
            g.ball('Rubber tire',(x,y,.37),(.36,.17,.36),g.mat('171623',rough=.84),car)
            rim=g.link('Spinning solid gold rim',p=car,xyz=(x,y+math.copysign(.15,y),.37));rims.append(rim)
            g.ball('Forged rim',(0,0,0),(.266,.05,.266),gold,rim)
            g.ball('Dark inset',(0,math.copysign(.041,y),0),(.215,.02,.215),black,rim)
            for i in range(10):
                a=i*math.tau/10;dy=math.copysign(.062,y)
                g.rod('Brushed gold spoke',(.045*math.cos(a),dy,.045*math.sin(a)),(.235*math.cos(a),dy,.235*math.sin(a)),.016,gold,rim)
            g.ball('Gold center cap',(0,math.copysign(.069,y),0),(.064,.021,.064),gold,rim)
    return car,door,rims


def restaurant(g,r):
    wood=g.mat('97513b',rough=.49); brass=g.mat('d9a45f',metal=.66); red=g.mat('751f3f'); ivory=g.mat('fff0da')
    g.box('Parquet underlay',(0,0,-.09),(16,17,.17),textured(g,'Walnut grain','5b302b','aa6244',11),r)
    for i in range(-12,13):
        for j in range(-8,10):
            o=g.box('Herringbone parquet',(i*.49,j*.57+(i%2)*.22,-.002),(.66,.19,.022),g.mat(('7e4836','a36245','895039')[(i+j)%3]),r,.004);o.rotation_euler.z=(-1 if i%2 else 1)*.73
    g.box('Damask wallpaper',(0,5.2,2.6),(16,.18,5.2),textured(g,'Gold damask','754145','9f6753',8),r)
    for x in (-4,0,4):
        windows(g,r,x,5.02,2.65,2.0,3.0)
        for side in (-1,1):
            for j in range(5):g.ball('Velvet curtain fold',(x+side*(.86+j*.105),4.82,2.75),(.14,.15,1.56),red,r)
        g.box('Brass curtain pelmet',(x,4.66,4.32),(2.85,.24,.24),brass,r,.055)
    for x,y in ((0,0),(-3,2.25),(3,2.5)):
        g.rod('Table pedestal',(x,y,.02),(x,y,.79),.115,wood,r)
        g.ball('Round white linen tabletop',(x,y,.82),(.95,.71,.078),ivory,r)
        for dx in (-1.04,1.04):
            g.box('Red dining chair seat',(x+dx,y+.28,.45),(.48,.54,.11),red,r,.055)
            g.box('Red velvet chair back',(x+dx*1.20,y+.36,.79),(.11,.54,.69),red,r,.06)
            for yy in (.07,.49):g.rod('Chair brass leg',(x+dx,y+yy,.03),(x+dx,y+yy,.43),.032,brass,r)
            g.ball('Porcelain plate',(x+dx*.49,y-.06,.91),(.255,.17,.020),ivory,r)
        g.rod('Wax candle',(x,y+.2,.89),(x,y+.2,1.15),.034,ivory,r)
        g.ball('Candle flame',(x,y+.2,1.19),(.032,.032,.061),g.mat('ffd192',em=4),r)
        g.light('Amber candle pool','POINT',(x,y+.14,1.22),(0,0,0),36,'ffb478',r)


def paris(g,r):
    g.box('Park lawn',(0,3.1,-.19),(30,25,.34),textured(g,'Paris lawn','557249','90a86a',10,ground=True),r)
    g.box('Park cobbled path',(0,2.65,-.12),(8.5,19,.24),textured(g,'Cobble path','b99c83','dfc8ad',7,ground=True,cobble=True),r)
    daylight_backdrop(g,r)
    park(g,r,foreground=True)
    iron=g.mat('815944',metal=.24)
    for i,(z,w) in enumerate([(0,2.15),(1.8,1.44),(3.3,.84),(4.95,.40),(6.3,.22),(7.12,.1)]):
        if i==0:continue
        pz,pw=[(0,2.15),(1.8,1.44),(3.3,.84),(4.95,.40),(6.3,.22)][i-1]
        for j in range(4):
            sx=(-1,1,1,-1)[j]; sy=(-1,-1,1,1)[j]; nx=(-1,1,1,-1)[(j+1)%4];ny=(-1,-1,1,1)[(j+1)%4]
            a=(sx*pw,7+sy*pw,pz);b=(sx*w,7+sy*w,z);c=(nx*w,7+ny*w,z)
            g.rod('Eiffel tower leg',a,b,.078 if i<3 else .048,iron,r)
            g.rod('Eiffel cross brace',a,c,.042,iron,r);g.rod('Eiffel gallery',b,c,.067,iron,r)
        if i in (1,2,4):g.box('Eiffel observation deck',(0,7,z),(w*2.2,w*2.2,.15),iron,r)
    g.rod('Eiffel antenna',(0,7,7.1),(0,7,7.75),.025,iron,r)
    for side in (-1,1):
        for i in range(3):
            x=side*(4.2+i*3.2);g.box('Parisian cream limestone townhouse',(x,9,2.2),(3.05,.82,4.4),g.mat('d1b99d'),r,.032)
            g.box('Blue mansard roof',(x,8.91,4.57),(3.2,1.09,.62),g.mat('64667d'),r,.16)
            for z in (1.02,2.17,3.30):
                for dx in (-.96,0,.96):windows(g,r,x+dx,8.54,z,.45,.66,daylight=True)
    bush_core(g,r,(-.70,.53,.385),(1.00,.51,.37),14)
    leaves(g,r,-.7,.56,.46,1.16,count=470,core=((0,-.03,-.075),(1.00,.51,.37)))


def park(g,r,foreground=False):
    trees=[(-7,3.8),(-4.3,4.9),(4.6,3.8),(7.3,4.9)]
    if foreground:
        trees.append((-3.45,-2.45))
    for i,(x,y) in enumerate(trees):
        g.rod('Park tree trunk',(x,y,0),(x,y,3),.15,g.mat('72523d'),r)
        for j in range(7):
            a=j*2.4;radius=.70 if j else .12
            cx=x+radius*math.sin(a);cy=y+radius*.72*math.cos(a);cz=2.86+(j%3)*.50
            g.rod('Park tree crown branch',(x,y,2.28),(cx,cy,cz),.047,g.mat('72523d'),r)
            foliage=leaves(g,r,cx,cy,cz,.79,310+i*9+j,count=190)
            foliage.name='Park crown leaf cards';foliage.scale.z=1.80


def rose_bud(g,r,center,radius,pink):
    """Three overlapping whorls with cupped, curled petal tips."""
    vertices=[];faces=[];rings=[]
    for ring in range(3):
        count=5+ring*2;length=radius*(.51+ring*.25)
        for petal in range(count):
            angle=math.tau*petal/count+ring*.72;root=len(vertices)
            for i in range(6):
                t=i/5;rho=length*(.17+.88*t);width=.45*length*math.sin(math.pi*t*.89)
                for j in range(5):
                    u=(j-2)/2;cross=width*u
                    cup=length*(.30*math.sin(math.pi*t)+.38*t*t+.20*u*u*t)
                    vertices.append((rho*math.cos(angle)-cross*math.sin(angle),-cup-ring*.005,rho*math.sin(angle)+cross*math.cos(angle)))
            for i in range(5):
                for j in range(4):
                    a=root+i*5+j;faces.append((a,a+1,a+6,a+5));rings.append(ring)
    mesh=bpy.data.meshes.new('Cupped rosebud petals');mesh.from_pydata(vertices,[],faces);mesh.update()
    for color in (('ba496c','e684a1','ffc7ce') if pink else ('c29f9e','e6ccd0','fff2dc')):mesh.materials.append(g.mat(color,rough=.62))
    for face,ring in zip(mesh.polygons,rings):face.material_index=ring;face.use_smooth=True
    g.link('Sculpted rose bud',mesh,r,center)


def wedding(g,r):
    g.box('Garden grass',(0,0,-.10),(25,25,.20),textured(g,'Garden grass','547552','82a166',11,ground=True),r)
    g.box('Ivory aisle carpet',(0,-.7,.019),(1.48,9,.035),g.mat('f6e2c9'),r)
    park(g,r)
    daylight_backdrop(g,r)
    wood=g.mat('72513f');flower=g.mat('fff1df')
    points=[(-1.40,1.28,0),(-1.40,1.28,1.71)]+[(1.4*math.cos(a),1.28,1.71+1.13*math.sin(a)) for a in [math.pi-i*math.pi/36 for i in range(37)]]+[(1.4,1.28,0)]
    g.curve('Bentwood wedding arch',points,.071,wood,r)
    vines=[(x,y,z) for x,y,z in points[2:-1]]+[(x,1.28,z) for x in (-1.4,1.4) for z in (.28,.60,.93,1.25,1.58)]
    for i,(x,y,z) in enumerate(vines):
        if i%2==0:
            foliage=leaves(g,r,x,y-.022,z,.26,41+i,count=88);foliage.name='Wedding arch leaf cards';foliage.scale.z=1.2
        if i%4==1:
            rose_bud(g,r,(x,y-.125,z),.071 if i%8==1 else .058,i%3==0)
    for y in (-1.55,-.45,.66):
        for x in (-2.5,-1.69,1.69,2.5):
            g.box('White guest chair seat',(x,y,.43),(.45,.43,.055),flower,r)
            g.box('White guest chair back',(x,y+.21,.70),(.46,.058,.45),flower,r)
            for dx in (-.18,.18):
                for dy in (-.18,.18):g.rod('Guest chair leg',(x+dx,y+dy,.02),(x+dx,y+dy,.42),.025,flower,r)


def porch(g,r):
    lawn=textured(g,'Sunset lawn','546750','827e54',7,ground=True); boards=textured(g,'Clapboard paint','547372','7c9590',9);white=g.mat('f1d9bc');timber=textured(g,'Porch warm timber','76473b','a96753',13,ground=True); roof=g.mat('4e3d51')
    g.box('Country garden',(0,0,-.13),(30,22,.23),lawn,r)
    g.box('Two-storey country house',(0,3.4,2.52),(6.4,4.55,5.05),boards,r)
    for i in range(29):
        g.box('Overlapping clapboard',(0,1.09,.10+i*.17),(6.36,.11,.15),boards,r,.014)
    for side in (-1,1):
        o=g.box('Gable roof', (side*1.68,3.39,5.24),(3.82,4.94,.22),roof,r,.05);o.rotation_euler.y=side*.31
        g.box('Porch support column',(side*2.75,-.68,1.42),(.16,.16,2.7),white,r,.025)
        for z in (1.54,3.85):windows(g,r,side*1.91,.99,z,1.07,1.30)
    g.box('Front red door',(0,1.01,1.26),(1.09,.13,2.35),g.mat('943d43'),r,.039)
    g.box('Porch canopy',(0,.06,2.8),(6.23,1.86,.18),roof,r,.055)
    g.box('Porch timber decking',(0,.28,.055),(6.16,2.08,.12),timber,r)
    g.box('Red cushioned porch bench', (0,.05,.55),(2.42,.62,.16),g.mat('9a424f'),r,.055)
    g.box('Porch bench seat back', (0,.34,.84),(2.46,.12,.55),timber,r,.055)
    for x in (-1.08,1.08):g.box('Bench support',(x,.04,.31),(.12,.47,.40),timber,r)
    for side in (-1,1):
        for j in range(13):
            x=side*(2.1+.29*j);g.box('Picket',(x,-2.36,.37),(.15,.061,.77),white,r,.014)
        for z in (.22,.50):g.box('Fence rail',(side*3.82,-2.32,z),(3.8,.07,.09),white,r)
    for x in (-3.7,3.8):leaves(g,r,x,-.32,.38,.75,10)
    silk_frame(g,r,(1.70,.82,1.70))
