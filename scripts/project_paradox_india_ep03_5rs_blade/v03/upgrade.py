"""V3 room materials, practicals, and reflected specular lighting."""
import bpy
import math
import random
from mathutils import Vector
import geometry as G
import ricks_lookdev as look

O = bpy.data.objects
M = bpy.data.materials
S = bpy.context.scene

def ramp(nodes, stops, interpolation='EASE'):
    node = nodes.new('ShaderNodeValToRGB')
    node.color_ramp.interpolation = interpolation
    elements = node.color_ramp.elements
    for index, (position, color) in enumerate(stops):
        element = elements[index] if index < 2 else elements.new(position)
        element.position = position
        element.color = look.rgba(color) if isinstance(color, str) else (color,color,color,1)
    return node

def textured(name, colors, scale, roughness, *, pattern=None, metallic=0, bump=.06):
    material = look.metal(name, colors[0], metallic, roughness)
    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    bsdf = nodes.get('Principled BSDF')
    coords = nodes.new('ShaderNodeTexCoord')
    stretch = nodes.new('ShaderNodeVectorMath')
    stretch.operation = 'MULTIPLY'
    stretch.inputs[1].default_value = scale
    links.new(coords.outputs['Object'], stretch.inputs[0])
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 1
    noise.inputs['Detail'].default_value = 2
    links.new(stretch.outputs[0],noise.inputs['Vector'])
    color = ramp(nodes,[(.19,colors[0]),(.81,colors[1])])
    rough = ramp(nodes,[(.1,max(.055,roughness-(.035 if metallic else .085))),(.9,min(.94,roughness+(.035 if metallic else .085)))])
    for node in (color,rough):
        links.new(noise.outputs['Fac'],node.inputs[0])
    links.new(rough.outputs[0],bsdf.inputs['Roughness'])
    albedo = color.outputs[0]
    height = noise.outputs['Fac']
    if pattern:
        kind, axes, size, grout, alt = pattern
        coord = coords.outputs['Object']
        if axes == 'XZ':
            split,join = nodes.new('ShaderNodeSeparateXYZ'),nodes.new('ShaderNodeCombineXYZ')
            links.new(coord,split.inputs[0])
            links.new(split.outputs['X'],join.inputs['X'])
            links.new(split.outputs['Z'],join.inputs['Y'])
            coord = join.outputs[0]
        if kind == 'CHECKER':
            blocks = nodes.new('ShaderNodeTexChecker')
            blocks.inputs['Color1'].default_value = look.rgba(colors[1])
            blocks.inputs['Color2'].default_value = look.rgba(alt)
            blocks.inputs['Scale'].default_value = 1/size[0]
        else:
            blocks = nodes.new('ShaderNodeTexBrick')
            blocks.offset = .5
            blocks.inputs['Scale'].default_value = 1
            blocks.inputs['Brick Width'].default_value = size[0]
            blocks.inputs['Row Height'].default_value = size[1]
            blocks.inputs['Mortar Size'].default_value = size[2]
            blocks.inputs['Mortar Smooth'].default_value = .012
            blocks.inputs['Color1'].default_value = look.rgba(colors[1])
            blocks.inputs['Color2'].default_value = look.rgba(alt)
            blocks.inputs['Mortar'].default_value = look.rgba(grout)
            mortar = nodes.new('ShaderNodeMath')
            mortar.operation = 'MULTIPLY_ADD'
            mortar.inputs[1].default_value = -2.0
            links.new(blocks.outputs['Fac'],mortar.inputs[0])
            links.new(height,mortar.inputs[2])
            height = mortar.outputs[0]
        links.new(coord,blocks.inputs['Vector'])
        weather = nodes.new('ShaderNodeMixRGB')
        weather.blend_type = 'MULTIPLY'
        weather.inputs[0].default_value = .29
        links.new(blocks.outputs['Color'],weather.inputs[1])
        links.new(color.outputs[0],weather.inputs[2])
        albedo = weather.outputs[0]
    links.new(albedo,bsdf.inputs['Base Color'])
    relief = nodes.new('ShaderNodeBump')
    relief.inputs['Strength'].default_value = bump
    relief.inputs['Distance'].default_value = .008 if not metallic else .00045
    links.new(height,relief.inputs['Height'])
    links.new(relief.outputs[0],bsdf.inputs['Normal'])
    return material

def assign(obj,mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

def match(mat,*prefixes):
    for obj in O:
        if obj.type in {'MESH','CURVE'} and obj.name.startswith(prefixes) and not obj.name.endswith(' / ink'):
            assign(obj,mat)

def box(name, parent, pos, size, mat, bevel=.015):
    return G.cube('V3 '+name,pos,size,mat,parent,bevel)

def set_materials():
    stucco = textured('V3 sunworn cream and terracotta stucco',('#C28D6A','#E6BD94'),(8,10,12),.72,bump=.085)
    tile = textured('V3 glazed mint and ivory subway ceramic',('#9DAC9D','#D2E1C9'),(11,13,15),.22,
                    pattern=('BRICK','XZ',(.30,.145,.007),'#7B8E83','#C5D3BC'),bump=.20)
    checker = textured('V3 worn cream and blue slate checker',('#7D7467','#D7C2A4'),(16,16,11),.35,
                       pattern=('CHECKER','XY',(.35,0,0),'#45405A','#607C87'),bump=.15)
    walnut = textured('V3 dark walnut satin grain',('#422821','#86543B'),(3,82,28),.35,bump=.15)
    teak = textured('V3 warm teak with sapwood grain',('#79472E','#C18A55'),(4,68,26),.41,bump=.14)
    brick = textured('V3 ochre limewashed bazaar brick',('#876342','#DCAC76'),(13,15,18),.68,
                     pattern=('BRICK','XZ',(.39,.19,.014),'#826B51','#B58050'),bump=.24)
    burlap = textured('V3 warm woven burlap',('#68563D','#AE9567'),(125,135,110),.84,bump=.27)
    planks = textured('V3 workshop scarred and sooted planks',('#37241F','#895534'),(3,25,75),.67,
                      pattern=('BRICK','XZ',(2.0,.26,.010),'#372824','#5F3A28'),bump=.23)
    forge = textured('V3 charcoal forge masonry',('#342726','#674638'),(11,16,19),.86,
                     pattern=('BRICK','XZ',(.29,.155,.013),'#312626','#51433E'),bump=.24)
    bench = textured('V3 scarred oiled workshop bench',('#4A2C22','#AA7146'),(5,80,47),.41,bump=.24)
    stone = textured('V3 restrained limestone architecture',('#737165','#B6AC95'),(11,13,15),.53,
                     pattern=('BRICK','XZ',(.74,.38,.008),'#7F796C','#A49F8F'),bump=.15)
    concrete = textured('V3 polished warm grey concrete',('#908576','#A69F92'),(13,14,17),.34,bump=.06)
    iron = textured('V3 #2C3944 cast iron hammertone',('#232D38','#42515B'),(107,118,109),.35,metallic=.85,bump=.16)
    nickel = textured('V3 brushed cupro nickel alloy',('#A39885','#BDB29F'),(18,138,125),.25,metallic=.72,bump=.09)
    silver = textured('V3 brushed silver and steel',('#889BAC','#D7DBD6'),(39,157,104),.23,metallic=.78,bump=.08)
    brass = textured('V3 satin brass',('#A46B32','#E5B66C'),(47,71,91),.24,metallic=.74,bump=.08)
    mirror = look.metal('V3 silver backed mirror', '#CCD4DF',.92,.15,emission_strength=.10)
    brass.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.22
    for mat,amount in [(nickel,.11),(silver,.085),(iron,.11),(brass,.10)]:
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Emission Color'].default_value=look.rgba('#8795AA' if mat==iron else '#FFE0AA')
        bsdf.inputs['Emission Strength'].default_value=amount
    for mat, tint, energy in [(stucco,'#C68655',.16),(brick,'#BD742C',.15),(stone,'#B0A489',.08)]:
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Emission Color'].default_value=look.rgba(tint)
        bsdf.inputs['Emission Strength'].default_value=energy
    match(stucco,'BARBER lower wall','BARBER upper wall','BARBER window masonry')
    match(tile,'Barber terracotta wainscot')
    match(checker,'BARBER support floor')
    match(walnut,'Barber counter','Wainscot cap rail','Mounted mirror frame','Mirror grooming shelf','Hand mirror walnut surround')
    match(mirror,'Mirror face','Hand mirror silver')
    match(brick,'MARKET lower wall','MARKET upper wall','MARKET window masonry')
    match(teak,'Kirana counter','Kirana stocked shelf','Blade display plinth')
    match(burlap,'Burlap open sack')
    match(planks,'WORKSHOP back wall','Workshop side masonry','Workshop closed ceiling')
    match(forge,'Furnace brick body')
    match(bench,'Workshop bench')
    match(stone,'MINT lower wall','MINT upper wall','MINT window masonry','MINT side jamb')
    match(concrete,'MINT support floor')
    match(iron,'Mint machine column','Mint head crossbar','Mint base','Mint piston head','Mint lever bolted','Press guide','Press base','Barber press moving ram')
    match(brass,'Mint lever mounting pin','RBI wall plaque','Scale foot','Scale central axle','Balance brass beam','Brass scale pan','Supported coin die','Burnished nickel rim')
    match(nickel,'Loop hero coin milled body','Heavy coin macro milled body','Raised minted circular field','Jar vanishing coin')
    match(silver,'Coin chute','Coin receiving tray','Mint piston','Thin steel output')
    for obj in O:
        if obj.type=='MESH' and 'open bevel steel' in obj.name and 'reflected' not in obj.name and not obj.name.endswith(' / ink'):
            assign(obj,silver)
    return walnut,teak,stone,iron,brass,forge

def room_dressing(mats):
    walnut,teak,stone,iron,brass,forge=mats
    bar,market,work,mint=stages()
    cream=M['White cotton']; ink=M['Graphic limbs and features']
    # Graphic hair-style board and folded towels sit against the rear set.
    box('hair board frame',bar,(.14,2.81,2.27),(.58,.08,.70),walnut)
    box('hair board ivory card',bar,(.14,2.762,2.27),(.52,.01,.64),cream)
    for i in range(2):
        x=.01+i*.24
        for j in range(2):
            z=2.12+j*.30
            G.sphere('V3 poster head',(x,2.747,z),(.068,.008,.087),M['Graphic cream face'],bar,16,8)
            G.sphere('V3 poster hair',(x,2.741,z+.047),(.075,.010,.048),ink,bar,16,8)
            G.line('V3 poster lettering',[(x-.062,2.745,z-.098),(x+.064,2.745,z-.098)],.006,walnut,bar)
    for i in range(4):
        box('folded grooming towel',bar,(-1.16,2.39,1.047+i*.052),(.29,.26,.048),
            cream if i%2 else M['Petrol turquoise'],.022)
    # Shelves are behind all action and add bokeh depth to both inserts.
    spice = [M['Brick crimson'],brass,M['Petrol turquoise'],cream]
    for j in range(2):
        z=1.38+j*.42
        box('tea shelf',market,(.61,2.63,z),(2.32,.35,.07),teak)
        for i in range(7):
            x=-.36+i*.31
            h=.15+((2*i+j)%3)*.052
            G.cylinder('V3 tea tin',(x,2.58,z+.034),(x,2.58,z+h),.095,spice[(i+j)%4],market,16)
            G.cylinder('V3 tea tin lid',(x,2.58,z+h),(x,2.58,z+h+.018),.100,brass,market,16)
            box('tea tin paper band',market,(x,2.483,z+h*.64),(.13,.01,.057),cream,.003)
    # Real arch stones, an ember grate, and a flared iron extractor.
    furnace=O['Furnace']
    hood=G.loft('V3 iron chimney hood',[(1.02,.70,.42),(1.15,.64,.37),(1.55,.22,.19),(2.05,.205,.177)],
                iron,furnace,n=16,outline=.006)
    for i in range(11):
        angle=math.pi*i/10
        loc=(.45*math.cos(angle),-.398,.48+.40*math.sin(angle))
        stone_block=box('forge arch voussoir',furnace,loc,(.165,.14,.17),forge,.025)
        stone_block.rotation_euler.y=-angle
    for side in (-1,1):
        for j in range(3):
            box('forge lower pilaster',furnace,(side*.45,-.395,.145+j*.123),(.155,.14,.118),forge)
    ember_materials=[G.emission('V3 red ember','#FF4212',2.3),G.emission('V3 orange ember','#FF931F',3.8),
                     G.emission('V3 pale ember','#FFCF61',5.0)]
    rng=random.Random(34)
    for i in range(26):
        x=rng.uniform(-.31,.31)
        G.sphere('V3 forge ember',(x,-.445+rng.uniform(-.044,.012),.355+rng.uniform(-.04,.05)),
                 (.051,.042,.031),ember_materials[i%3],furnace,12,6)
    for obj in list(furnace.children):
        if obj.name.startswith(('Lobed living furnace flame','Furnace orange opening')):
            obj.scale.z*=.55
            obj.location.z-=.065
    for i in range(3):
        x=-.16+i*.34
        G.line('V3 hanging tong legs',[(x-.04,2.66,1.53),(x,2.66,1.82),(x+.045,2.66,1.54)],.014,iron,work)
        box('hanging hammer head',work,(1.22+i*.28,2.66,1.70),(.15,.07,.055),iron)
    # Subtle dado cap and riveted press fittings.
    box('mint stone wainscot cap',mint,(0,2.84,.98),(7.9,.11,.10),stone)
    for x in [-.52,.52]:
        for z in [.77,2.20]:
            G.cylinder('V3 mint brass fixing',(x,-.235,z),(x,-.197,z),.064,brass,O['Mint press assembly'],16)
    for i in range(8):
        coin=O[f'Jar vanishing coin {i}']
        for child in coin.children:
            if 'milled body' in child.name and child.type=='MESH':
                assign(child,M['V3 brushed cupro nickel alloy'])

def stages():
    return [O[name+' stage'] for name in ('BARBER','MARKET','WORKSHOP','MINT')]

def dust_card(parent, name, start, end, radius):
    mat=bpy.data.materials.new('V3 '+name+' feathered dust')
    mat.use_nodes=True
    mat.surface_render_method='BLENDED'
    tree=mat.node_tree
    nodes,links=tree.nodes,tree.links
    nodes.clear()
    uv=nodes.new('ShaderNodeTexCoord')
    separate=nodes.new('ShaderNodeSeparateXYZ')
    links.new(uv.outputs['UV'],separate.inputs[0])
    across=ramp(nodes,[(0,0),(.24,.54),(.50,1),(.76,.54),(1,0)])
    length=ramp(nodes,[(0,0),(.20,.028),(.47,.079),(.78,.050),(1,0)])
    links.new(separate.outputs['X'],across.inputs[0])
    links.new(separate.outputs['Y'],length.inputs[0])
    opacity=nodes.new('ShaderNodeMath');opacity.operation='MULTIPLY'
    links.new(across.outputs[0],opacity.inputs[0]);links.new(length.outputs[0],opacity.inputs[1])
    clear=nodes.new('ShaderNodeBsdfTransparent')
    haze=nodes.new('ShaderNodeEmission');haze.inputs[0].default_value=look.rgba('#FFE5B7')
    mix=nodes.new('ShaderNodeMixShader')
    for a,b in [(opacity.outputs[0],mix.inputs[0]),(clear.outputs[0],mix.inputs[1]),(haze.outputs[0],mix.inputs[2])]:
        links.new(a,b)
    out=nodes.new('ShaderNodeOutputMaterial');links.new(mix.outputs[0],out.inputs[0])
    # Feathered plane is camera-visible dust only, with no volume, probe, or shadow pass.
    a,b=Vector(start),Vector(end)
    verts=[a+Vector((x*.07,0,0)) for x in (-1,1)]+[b+Vector((x*radius,0,0)) for x in (1,-1)]
    obj=G.mesh('V3 '+name+' dust cone',verts,[(0,1,2,3)],mat,parent,smooth=False)
    layer=obj.data.uv_layers.new()
    for loop in obj.data.loops:
        layer.data[loop.index].uv=((0,1),(1,1),(1,0),(0,0))[loop.vertex_index]
    look.mark_role(obj,'wisp')
    obj.hide_probe_sphere=True

def lighting():
    for obj in S.objects:
        if obj.get('ricks_light') and obj.type=='LIGHT':
            if obj.data.use_shadow:
                obj.data.energy=2.7
                obj.data.color=look.rgba('#FFE1AC')[:3]
                obj.rotation_euler=Vector((.62,-.52,-.65)).to_track_quat('-Z','Y').to_euler()
            else:
                obj.data.energy=.38
                obj.data.color=look.rgba('#8193C4')[:3]
    for stage, label, origin, target in zip(stages(),('barber','market','forge','mint'),
            [(-.64,.15,3.04),(.38,.24,2.98),(-.23,-.55,2.83),(-1.26,-.16,3.02)],
            [(-.64,.55,.92),(.30,.33,1.10),(.02,.11,1.11),(-1.29,.04,1.01)]):
        # EEVEE 4.2 captures sphere probes during rendering.
        probe_data=bpy.data.lightprobes.new('V3 '+label+' reflection capture','SPHERE')
        probe_data.influence_distance=6
        probe_data.clip_start=.10
        probe_data.clip_end=10
        probe=G.obj('V3 '+label+' EEVEE sphere probe',probe_data,stage)
        probe.location=(.10,.26,2.05)
        lamp=G.light('V3 '+label+' warm pool','SPOT',origin,target,105 if label=='forge' else 142,'#FFD59D',.22)
        lamp.parent=stage
        lamp.data.use_shadow=label!='forge'
        lamp.data.spot_size=math.radians(51)
        lamp.data.spot_blend=.71
        strip=G.light('V3 '+label+' reflection strip','AREA',(-1.3,-2,2.45),(.05,.35,1.2),
                      56 if label=='forge' else 85,'#FFEAD0',1)
        strip.parent=stage
        strip.data.shape='RECTANGLE'
        strip.data.size=1.75
        strip.data.size_y=.34
        strip.data.use_shadow=False
        if label!='forge':
            dust_card(stage,label,origin,target,.66)
    # Asset set stages are toggled by the original runtime, along with local lights and probes.
    for name in ('Barber','Customer','Shopkeeper','Trader','Smuggler','Officer'):
        O[name].hide_probe_sphere=True
    for obj in O:
        if obj.get('ricks_role') in {'ink','wisp','streak','cloud'}:
            obj.hide_probe_sphere=True
    molten=G.light('V3 molten interactive spill','POINT',(-.45,-.16,1.26),(0,0,0),26,'#FF8B3E',.26)
    molten.parent=stages()[2]
    molten.data.use_shadow=False
    stream=O['Animated molten stream']
    assign(stream,G.emission('V3 orange liquid metal','#FF7A18',6.7))
    core=stream.copy()
    core.data=stream.data.copy()
    S.collection.objects.link(core)
    core.name='V3 molten white core'
    core.data.bevel_depth=.010
    assign(core,G.emission('V3 white hot metal core','#FFF3A8',7.4))
    core.location.y=-.014
    core.visible_shadow=False
    core.hide_probe_sphere=True
    for obj in O:
        if obj.name.startswith('Liquid metal surface'):
            assign(obj,G.emission('V3 ladle molten surface','#FFB740',6.5))

def foam():
    head=O['Customer head']
    for obj in list(head.children):
        if obj.name.startswith('Scalloped shaving foam'):
            bpy.data.objects.remove(obj,do_unlink=True)
    bright=G.emission('V3 crisp shaving foam','#FFFFFF',1)
    line_mat=G.emission('V3 subtle lather boundary','#D9D1CC',1)
    def face(x,z,y=.011):
        r=.32*G.rough(math.atan2(-z,x))
        return (x,-.063*math.sqrt(max(.04,1-(x*x+z*z)/(r*r)))-y,z)
    for side in (-1,1):
        for k,(x,z,rx,rz) in enumerate([(.207,-.100,.070,.062),(.166,-.162,.047,.044),(.113,-.203,.041,.028)]):
            points=[]
            for i in range(48):
                a=math.tau*i/48
                t=1+.085*math.cos(7*a+k)+.048*math.sin(4*a)
                points.append((side*(x+t*rx*math.cos(a)),z+t*rz*math.sin(a)))
            obj=G.mesh('V3 scalloped foam',( [face(side*x,z)] + [face(a,b) for a,b in points]),
                       [(0,i+1,(i+1)%48+1) for i in range(48)],bright,head,smooth=False)
            look.mark_role(obj,'wisp')
            edge=G.line('V3 lather edge',[face(a,b,.0114) for a,b in points+[points[0]]],.0014,line_mat,head)
            look.mark_role(edge,'ink')

def post():
    tree=S.node_tree
    nodes,links=tree.nodes,tree.links
    glow=next(node for node in nodes if node.type=='GLARE')
    glow.threshold=1.2
    glow.size=6
    addition=next(node for node in nodes if node.type=='MIX_RGB' and node.blend_type=='ADD')
    addition.inputs[0].default_value=.12
    output=next(node for node in nodes if node.type=='COMPOSITE')
    # Build a small packed linear falloff texture so corners are reproducible at both sizes.
    size=128
    image=bpy.data.images.new('V3 packed optical falloff',width=size,height=size,alpha=False,float_buffer=True)
    image.colorspace_settings.name='Non-Color'
    values=[]
    for y in range(size):
        for x in range(size):
            d=math.sqrt(((x/(size-1)-.5)*1.41)**2+((y/(size-1)-.5)*1.41)**2)
            gain=1-.08*look.ease5((d-.36)/.64)
            values.extend((gain,gain,gain,1))
    image.pixels.foreach_set(values)
    image.pack()
    read=nodes.new('CompositorNodeImage')
    read.image=image
    scale=nodes.new('CompositorNodeScale')
    scale.space='RENDER_SIZE'
    overscan=nodes.new('CompositorNodeTransform')
    overscan.inputs['Scale'].default_value=1.035
    multiply=nodes.new('CompositorNodeMixRGB')
    multiply.blend_type='MULTIPLY'
    multiply.inputs[0].default_value=1
    links.new(read.outputs['Image'],scale.inputs[0])
    links.new(addition.outputs[0],multiply.inputs[1])
    links.new(scale.outputs[0],overscan.inputs['Image'])
    links.new(overscan.outputs['Image'],multiply.inputs[2])
    links.new(multiply.outputs[0],output.inputs[0])

def apply():
    mats=set_materials()
    room_dressing(mats)
    lighting()
    foam()
    post()
    look.enforce_shadow_policy(S)
