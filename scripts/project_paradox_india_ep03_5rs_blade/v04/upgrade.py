"""V4 look and rig changes on top of the V3 master."""
import bpy
import math
from mathutils import Vector
import geometry as G
import ricks_lookdev as look

O = bpy.data.objects
M = bpy.data.materials

def assign(obj, material):
    obj.data.materials[0] = material

def surface_noise(material, a, b, scale, bump_distance):
    tree=material.node_tree
    nodes,links=tree.nodes,tree.links
    noise=nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=scale
    noise.inputs['Detail'].default_value=2
    tex=nodes.new('ShaderNodeTexCoord')
    links.new(tex.outputs['Object'],noise.inputs['Vector'])
    colors=nodes.new('ShaderNodeValToRGB')
    colors.color_ramp.elements[0].color=look.rgba(a)
    colors.color_ramp.elements[1].color=look.rgba(b)
    links.new(noise.outputs['Fac'],colors.inputs[0])
    bump=nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.19
    bump.inputs['Distance'].default_value=bump_distance
    links.new(noise.outputs['Fac'],bump.inputs['Height'])
    surface=nodes.get('Principled BSDF')
    links.new(bump.outputs[0],surface.inputs['Normal'])
    return colors.outputs[0],tex.outputs['Object']

def workshop_floor():
    floor=look.metal('V4 soot-dark stone pavers','#39343B',0,.70)
    color,coords=surface_noise(floor,'#22232B','#54454A',21,.009)
    nodes,links=floor.node_tree.nodes,floor.node_tree.links
    brick=nodes.new('ShaderNodeTexBrick')
    brick.inputs['Scale'].default_value=1
    brick.inputs['Brick Width'].default_value=.55
    brick.inputs['Row Height'].default_value=.43
    brick.inputs['Mortar Size'].default_value=.013
    brick.inputs['Mortar Smooth'].default_value=.009
    brick.inputs['Color2'].default_value=look.rgba('#35343E')
    brick.inputs['Mortar'].default_value=look.rgba('#25242A')
    links.new(color,brick.inputs['Color1'])
    links.new(coords,brick.inputs['Vector'])
    surface=nodes.get('Principled BSDF')
    links.new(brick.outputs['Color'],surface.inputs['Base Color'])
    old=surface.inputs['Normal'].links[0].from_socket
    bevel=nodes.new('ShaderNodeBump')
    bevel.inputs['Strength'].default_value=.31
    bevel.inputs['Distance'].default_value=.018
    bevel.invert=True
    links.new(old,bevel.inputs['Normal'])
    links.new(brick.outputs['Fac'],bevel.inputs['Height'])
    links.new(bevel.outputs[0],surface.inputs['Normal'])
    assign(O['WORKSHOP support floor'],floor)

def face_and_room_lighting():
    for o in list(O):
        if o.get('ricks_light') and not o.data.use_shadow:
            o.data.energy *= .64
        if o.name.startswith(('V3 barber reflection strip','V3 market reflection strip','V3 mint reflection strip')):
            o.data.energy *= .66
        if o.name.startswith('V3 forge reflection strip'):
            o.data.energy *= .65
    O['Workshop slate fill'].data.energy*=.60
    # The sun and new cap key already cast shadows on the market set.
    O['V3 market warm pool'].data.use_shadow=False
    # Give the shallow, graphic heads a warm frontal key with a single cool side.
    for label, name, origin, target, watts in [
        ('barber','BARBER',(-2.25,-1.2,3.18),(-.25,.52,1.45),110),
        ('market','MARKET',(-1.9,-1.0,3.16),(.13,.9,1.48),108),
        ('mint','MINT',(-2.1,-1.0,3.12),(-.59,.47,1.43),102),
        ('forge','WORKSHOP',(-1.55,-.9,2.89),(-.31,.65,1.42),75)]:
        key=G.light('V4 '+label+' warm face key','SPOT',origin,target,watts,'#FFE7C9',.22)
        key.parent=O[name+' stage']
        key.data.spot_size=math.radians(58)
        key.data.spot_blend=.64
        key.data.use_shadow=True
        key.data.specular_factor=.14
    skin=M['V2 warm graphic skin']
    remap=skin.node_tree.nodes['Received light calibration']
    remap.inputs['From Min'].default_value=.115
    remap.inputs['From Max'].default_value=.82
    ramp=next(n for n in skin.node_tree.nodes if n.type=='VALTORGB')
    for el,color in zip(ramp.color_ramp.elements,('#C4C8EA','#DDD7EC','#F6E9E7','#FFF5EF')):
        el.color=look.rgba(color)
    # Reinforce soft wrap in the local head plane without changing the 2D contour.
    tree=skin.node_tree
    n,l=tree.nodes,tree.links
    tex=n.new('ShaderNodeTexCoord');split=n.new('ShaderNodeSeparateXYZ')
    l.new(tex.outputs['Generated'],split.inputs[0])
    falloff=n.new('ShaderNodeMapRange')
    falloff.interpolation_type='SMOOTHERSTEP'
    falloff.inputs['From Min'].default_value=.47
    falloff.inputs['From Max'].default_value=.94
    falloff.inputs['To Max'].default_value=.39
    l.new(split.outputs['X'],falloff.inputs['Value'])
    wrap=n.new('ShaderNodeMixRGB')
    wrap.inputs[2].default_value=look.rgba('#C4C8EA')
    l.new(falloff.outputs[0],wrap.inputs[0])
    l.new(ramp.outputs['Color'],wrap.inputs[1])
    l.new(wrap.outputs[0],next(x for x in n if x.type=='EMISSION').inputs['Color'])
    cap_skin=skin.copy()
    cap_skin.name='V4 shadow beneath cap brim'
    cap_tree=cap_skin.node_tree
    cn,cl=cap_tree.nodes,cap_tree.links
    emitter=next(node for node in cn if node.type=='EMISSION')
    wrap_out=emitter.inputs['Color'].links[0].from_socket
    z=next(node for node in cn if node.type=='SEPXYZ').outputs['Z']
    band=cn.new('ShaderNodeValToRGB')
    for index,(loc,gain) in enumerate(((.60,0),(.67,.10),(.72,.75),(.81,.82))):
        el=band.color_ramp.elements[index] if index<2 else band.color_ramp.elements.new(loc)
        el.position=loc
        el.color=(gain,gain,gain,1)
    band.color_ramp.interpolation='EASE'
    cl.new(z,band.inputs[0])
    shade=cn.new('ShaderNodeMixRGB')
    shade.inputs[2].default_value=look.rgba('#C4C8EA')
    cl.new(band.outputs[0],shade.inputs[0])
    cl.new(wrap_out,shade.inputs[1])
    cl.new(shade.outputs[0],emitter.inputs['Color'])
    for actor in ('Smuggler','Trader'):
        assign(O[actor+' cream rough head'],cap_skin)
        head=O[actor+' head']
        G.loft('V4 fitted cap band',[(.158,.276,.090),(.196,.286,.103),(.213,.277,.101)],
               M['Dark leather'],head,n=28,outline=.002)
        for part in O[actor+' head'].children:
            if part.name.startswith('Cap projecting brim'):
                part.scale.y*=1.22
                part.location.y-=.022

def molten_pool():
    ladle=O['Molten ladle']
    hot=M['V3 ladle molten surface']
    # Blend the pale centre into a darker orange meniscus using the existing pool mesh.
    tree=hot.node_tree
    nodes,links=tree.nodes,tree.links
    uv=nodes.new('ShaderNodeTexCoord')
    split=nodes.new('ShaderNodeSeparateXYZ')
    xy=nodes.new('ShaderNodeCombineXYZ')
    links.new(uv.outputs['Generated'],split.inputs[0])
    links.new(split.outputs['X'],xy.inputs['X'])
    links.new(split.outputs['Y'],xy.inputs['Y'])
    rad=nodes.new('ShaderNodeVectorMath');rad.operation='DISTANCE'
    rad.inputs[1].default_value=(.44,.52,0)
    links.new(xy.outputs[0],rad.inputs[0])
    color=nodes.new('ShaderNodeValToRGB')
    color.color_ramp.elements[0].position=.08
    color.color_ramp.elements[0].color=look.rgba('#FFF3A8')
    color.color_ramp.elements[1].position=.51
    color.color_ramp.elements[1].color=look.rgba('#FF7A18')
    links.new(rad.outputs['Value'],color.inputs[0])
    em=next(x for x in nodes if x.type=='EMISSION')
    links.new(color.outputs['Color'],em.inputs[0])
    strength=nodes.new('ShaderNodeMapRange')
    strength.interpolation_type='SMOOTHSTEP'
    strength.inputs['From Min'].default_value=.12
    strength.inputs['From Max'].default_value=.51
    strength.inputs['To Min'].default_value=6.5
    strength.inputs['To Max'].default_value=1.50
    links.new(rad.outputs['Value'],strength.inputs['Value'])
    links.new(strength.outputs[0],em.inputs[1])

def mint():
    stage=O['MINT stage']
    glass=look.metal('V4 frosted daylight industrial glass','#A8BFCE',.15,.45,emission_strength=.58)
    color,_=surface_noise(glass,'#8EAABF','#DBE9E7',35,.003)
    surface=glass.node_tree.nodes.get('Principled BSDF')
    glass.node_tree.links.new(color,surface.inputs['Base Color'])
    glass.node_tree.links.new(color,surface.inputs['Emission Color'])
    window_tree=glass.node_tree
    diffusion=window_tree.nodes.new('ShaderNodeBsdfTranslucent')
    window_tree.links.new(color,diffusion.inputs['Color'])
    mix=window_tree.nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value=.16
    window_tree.links.new(surface.outputs[0],mix.inputs[1])
    window_tree.links.new(diffusion.outputs[0],mix.inputs[2])
    window_tree.links.new(mix.outputs[0],next(node for node in window_tree.nodes if node.type=='OUTPUT_MATERIAL').inputs['Surface'])
    rail=look.metal('V4 mint graphite window mullion','#4F646C',.26,.37)
    for pane in list(stage.children):
        if 'recessed window' not in pane.name:
            continue
        assign(pane,glass)
        x=pane.location.x
        for dx in (-.51,-.26,0,.26,.51):
            G.cube('V4 mint vertical glass mullion',(x+dx,2.771,2.20),(.035,.045,1.035),rail,stage,.006)
        for z in (1.70,1.95,2.20,2.45,2.70):
            G.cube('V4 mint horizontal glass mullion',(x,2.765,z),(1.055,.052,.034),rail,stage,.006)
    for obj in list(stage.children):
        if obj.name.startswith(('Cloud soft silhouette','Varied cloud lobe','MINT window cream frame')):
            bpy.data.objects.remove(obj,do_unlink=True)
    machine=O['Mint press assembly']
    machine.location.x+=.27
    pivot=O['Mint lever pivot']
    pivot.location=(-.83,-.59,.94)
    pivot.rotation_euler=(0,0,0)
    G.set_line(O['Mint lever bar'],[(0,0,0),(-.43,-.04,.13)])
    O['Lever dark grip'].location=(-.43,-.04,.13)
    O['Lever hand anchor'].location=(-.43,-.04,.13)
    O['Lever dark grip'].rotation_euler.y=math.pi/2
    O['Mint lever bolted mounting bracket'].location=(-.68,-.34,.94)
    O['Mint lever mounting pin'].location+=Vector((-.13,.11,-.21))

def apply():
    workshop_floor()
    face_and_room_lighting()
    molten_pool()
    mint()
