"""Second calibration pass for the existing Circle Challenge master."""
import bpy, math, random
from pathlib import Path
from mathutils import Vector, Quaternion

OUT = Path('D:/remotionshorts/renders/circle_challenge')
s = bpy.context.scene
objects = bpy.data.objects
cam = s.camera
rng = random.Random(42)


def key(obj, prop, frame, value, interpolation='CONSTANT'):
    setattr(obj, prop, value)
    obj.keyframe_insert(prop, frame=frame)
    for curve in obj.animation_data.action.fcurves:
        if curve.data_path == prop:
            for point in curve.keyframe_points:
                if abs(point.co.x-frame) < .01:
                    point.interpolation = interpolation


def material(name, color, emission=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color,1)
    shader.inputs['Emission Color'].default_value = (*color,1)
    shader.inputs['Emission Strength'].default_value = emission
    return mat


def mesh_prop(name, loc, scale, mat, parent=None, kind='cube'):
    if kind == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12)
    elif kind == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(vertices=48)
    else:
        bpy.ops.mesh.primitive_cube_add(size=2)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = loc
    obj.scale = scale
    obj.data.materials.append(mat)
    return obj


def label(name, words, location, size, mat):
    data = bpy.data.curves.new(name,'FONT')
    data.body = words
    data.font = bpy.data.fonts.load('C:/Windows/Fonts/seguisb.ttf',check_existing=True)
    data.size = size
    data.align_x = 'CENTER'
    data.materials.append(mat)
    obj = bpy.data.objects.new(name,data)
    s.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler.x = math.pi/2
    return obj

# Replace checker blocks with layered turf color and fine surface texture.
for name, colors in [('grass',((.045,.13,.028,1),(.25,.46,.085,1))),('road',((.24,.10,.046,1),(.56,.32,.14,1)))]:
    tree = bpy.data.materials[name].node_tree
    nodes = tree.nodes
    shader = nodes.get('Principled BSDF')
    coord = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 2.7
    noise.inputs['Detail'].default_value = 4
    tree.links.new(coord.outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    for stop, position, color in zip(ramp.color_ramp.elements,(.18,.85),colors):
        stop.position = position
        stop.color = color
    tree.links.new(noise.outputs['Fac'],ramp.inputs[0])
    tree.links.new(ramp.outputs[0],shader.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .26
    bump.inputs['Distance'].default_value = .07
    tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
    tree.links.new(bump.outputs[0],shader.inputs['Normal'])

# Sky uses three colors and true view direction. A separate dark studio world
# is unnecessary because the brain room has an opaque back wall.
tree = s.world.node_tree
nodes = tree.nodes
xyz = nodes.new('ShaderNodeSeparateXYZ')
# World Normal is the incoming ray direction with Blender's world convention.
coord = nodes.new('ShaderNodeTexCoord')
tree.links.new(coord.outputs['Normal'],xyz.inputs[0])
ramps = []
for index, palette in enumerate([
    ((.67,.86,1),(.10,.57,.95),(.013,.23,.64)),
    ((1,.78,.38),(1,.34,.10),(.68,.15,.023)),
    ((1,.34,.17),(.34,.084,.46),(.042,.023,.24)),
    ((1,.81,.22),(1,.30,.08),(.55,.065,.018)),
]):
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements.new(.11)
    for element, height, color in zip(ramp.color_ramp.elements,(.0,.11,.34),palette):
        element.position = height
        element.color = (*color,1)
    absolute = nodes.new('ShaderNodeMath')
    absolute.operation = 'ABSOLUTE'
    tree.links.new(xyz.outputs['Z'],absolute.inputs[0])
    tree.links.new(absolute.outputs[0],ramp.inputs[0])
    ramps.append(ramp)
color = ramps[0].outputs[0]
for index in range(1,4):
    mix = nodes.new('ShaderNodeMixRGB')
    tree.links.new(color,mix.inputs[1])
    tree.links.new(ramps[index].outputs[0],mix.inputs[2])
    for frame, mode in [(1,0),(576,1),(1446,2),(1668,0),(1854,3)]:
        mix.inputs[0].default_value = float(mode==index)
        mix.inputs[0].keyframe_insert('default_value',frame=frame)
    color = mix.outputs[0]
for curve in tree.animation_data.action.fcurves:
    for point in curve.keyframe_points:
        point.interpolation = 'CONSTANT'
tree.links.new(color,nodes.get('Background').inputs['Color'])

white = material('V2 warm porcelain white',(.94,.95,1),.38)
ink = material('V2 navy hardware',(.019,.029,.043))
cloud = material('V2 cloud cream',(.92,.92,1),.18)
for old_cloud in [obj for obj in s.objects if obj.name.startswith("Layered cloud puff")]:
    bpy.data.objects.remove(old_cloud,do_unlink=True)
for i in range(7):
    x = -20+i*6.6
    z = rng.uniform(4.2,7.7)
    for j in range(4):
        mesh_prop('Layered cloud puff',(x+j*.85,25+i%2*3,z+rng.uniform(-.23,.32)),(1.2,.65,rng.uniform(.32,.68)),cloud,kind='sphere')

# Actor-safe perspective coverage. The HUD sits on the optical focus plane.
cam.data.type = 'PERSP'
cam.data.sensor_fit = 'VERTICAL'
cam.data.sensor_height = 24
cam.data.dof.use_dof = True
cam.data.animation_data_clear()
cam.animation_data_clear()
hud = objects['hud_rig']
hud.animation_data_clear()
shots = [
 (1,(0,-23,15),(0,2,2),27,8,0),(70,(0,-20,12),(0,2,2),26,8,0),
 (144,(-.72,-3.3,2.1),(0,0,1.94),42,2.4,0),
 (264,(-.62,-2.95,1.75),(.14,0,1.86),38,2.4,-.09),
 (378,(-1.0,-7.53,.55),(0,-5.6,.8),31,2.4,.025),
 (459,(2.25,-3.7,1.72),(.12,0,1.53),30,2.4,.025),
 (576,(-1.8,-4.65,.8),(.04,0,1.62),31,2.4,-.035),
 (732,(1.15,-6.7,2.5),(0,0,1.98),30,3.5,0),
 (930,(-2,-2.4,2.25),(-2,2,1.9),43,2.4,0),
 (965,(49.34,-4.6,2.5),(50.3,-.45,1.65),29,4,0),
 (1104,(0,-13.6,4.3),(0,-3.5,1.35),26,5.6,.035),
 (1299,(-.68,-6.2,2.27),(-.76,.15,1.5),33,3.2,0),
 (1446,(-.82,-5.3,2.2),(-.84,0,1.58),29,2.4,0),
 (1539,(-1.95,-3.35,2.65),(-1.38,0,2.37),43,2.4,.04),
 (1615,(-3.5,-10,4),(-3.5,0,1.4),26,5.6,0),
 (1668,(-.95,-11,4.15),(-.85,1.6,2.5),28,5.6,0),
 (1740,(.25,-2.85,2.12),(.02,0,2.08),42,2.4,-.025),
 (1854,(0,-17,4),(0,-8,1.2),24,5.6,0),
 (1910,(.35,-10.3,1.8),(-.53,-5,1.5),29,4,0),
 (2013,(-.35,-5.6,2.2),(-.45,0,1.58),30,3.2,0),
 (2095,(2.7,-7.2,4.0),(2.8,1.2,2),25,5.6,0),
]
for frame, eye, target, lens, aperture, tilt in shots:
    distance = (Vector(target)-Vector(eye)).length
    rotation = (Vector(target)-Vector(eye)).to_track_quat('-Z','Y') @ Quaternion((0,0,1),tilt)
    key(cam,'location',frame,eye)
    key(cam,'rotation_euler',frame,rotation.to_euler())
    key(cam.data,'lens',frame,lens)
    for prop, value in [('focus_distance',distance),('aperture_fstop',aperture)]:
        setattr(cam.data.dof,prop,value)
        cam.data.dof.keyframe_insert(prop,frame=frame)
    size = distance*24/lens/10
    key(hud,'scale',frame,(size,)*3)
    key(hud,'location',frame,(0,0,-distance+size))
for curve in cam.data.animation_data.action.fcurves:
    for point in curve.keyframe_points:
        point.interpolation = 'CONSTANT'
# Restore short accident shake within the new perspective setup.
for frame, x in [(312,.035),(313,-.04),(314,.031),(315,-.022),(316,.013),(317,0)]:
    key(cam,'delta_location',frame,(x,0,0))
key(cam,'delta_location',1,(0,0,0))

# Wide opening retains the full cast. The inserts use a staggered deeper group.
for index in range(38):
    actor = objects[f'Contestant_{index:02d}']
    s.frame_set(70)
    initial = actor.location.copy()
    key(actor,'location',1,initial)
    offset = ((index%7-3)*.94+rng.uniform(-.25,.25),2.2+index%5*.92,0)
    key(actor,'location',144,offset)
    scale = .92+rng.random()*.13
    key(actor,'scale',144,(scale,)*3 if index<21 else (0,0,0))
    if index<18:
        old_frames = {int(point.co.x) for curve in actor.animation_data.action.fcurves
                      if curve.data_path == 'location' for point in curve.keyframe_points
                      if 1104 <= point.co.x < 1299}
        for old_frame in old_frames:
            actor.keyframe_delete('location',frame=old_frame)
        x = (index%8-3.5)*.46 if index<8 else (index%2*2-1)*(2.0+index%4*.44)
        start = 1110+index*2
        crossing = 1180+index*5
        key(actor,'scale',1104,(.69,)*3)
        key(actor,'location',1104,(x,-.1+index%3*.6,0))
        key(actor,'location',start,(x,-.1+index%3*.6,0),'LINEAR')
        key(actor,'location',crossing,(x*1.08,-math.sqrt(max(10,6.5**2-x*x)),.18),'LINEAR')
        key(actor,'location',1298,(x*1.3,-11,0))
        key(actor,'scale',1299,(0,0,0))

# Brain console. Mount the dome under the press pose and remove duplicate signage.
objects['Vomit center wall sign'].hide_render = True
s.frame_set(1030)
bpy.context.view_layer.update()
operator_body = objects['char_brain_op_body_billboard']
hand = operator_body.matrix_world @ Vector(((845-512)*3/1474,(1474-930)*3/1474,0))
button = objects['Fixed VOMIT CENTER button']
button.animation_data_clear()
button.hide_render = True
red = material('V2 red control cap',(.7,.016,.037),.36)
mount = mesh_prop('Console button pedestal',(hand.x,hand.y+.09,hand.z-.30),(.43,.43,.22),ink,kind='cylinder')
dome = mesh_prop('Mounted alarm dome',(hand.x,hand.y+.09,hand.z-.115),(.34,.34,.14),red,kind='sphere')
for frame,z in [(1000,.11),(1015,.09),(1030,0),(1040,0),(1055,.11)]:
    key(dome,'delta_location',frame,(0,0,z),'LINEAR')
mesh_prop('Control console forward extension',(hand.x,hand.y+.53,hand.z-.64),(.60,.75,.37),bpy.data.materials['console'])
label('Console VOMIT label','VOMIT',(hand.x,hand.y-.235,hand.z-.71),.17,white)

# Car, raised paper roll, and the ignored cheque.
car = objects['Mom family car']
key(car,'scale',1910,(1,1,1))
key(car,'scale',2013,(0,0,0))
key(car,'location',1910,(-1.8,-3.25,.18))
key(car,'rotation_euler',1910,(0,0,-.26))
for y in (-.5,.5):
    mesh_prop('Hatchback headlight',(1.86,y,.54),(.12,.22,.10),white,car,'sphere')
for obj in car.children:
    if obj.name.startswith('Car side window'):
        obj.data.materials[0] = ink
roll = objects['Bright white toilet roll']
roll.rotation_euler = (0,.24,0)
roll.data.materials[0] = white
core = objects['Roll cardboard core']
core.location = (.048,0,.199)
core.rotation_euler = roll.rotation_euler
core.data.materials[0] = ink
paper = objects['Paper hanging end']
paper.location = (.13,-.29,.05)
paper.rotation_euler = (math.pi/2,.2,-.14)
paper.data.materials[0] = white
for obj in s.objects:
    if obj.name.startswith('Mom sunburst ray'):
        obj.hide_render = True
check = objects['Ignored cheque on grass']
key(check,'location',2095,(.35,-.55,.11))
check.rotation_euler.z = -.16

# Move the soul's origin to the rival's mouth in the newly framed insert.
s.frame_set(1600)
bpy.context.view_layer.update()
head = objects['char_rival_head_independent_pivot'].matrix_world
mouth = head @ Vector((0,-.176,.03))
ghost = objects['Rival ghost soul']
key(ghost,'location',1539,mouth,'LINEAR')
key(ghost,'location',1600,mouth+Vector((.38,-.14,.14)),'LINEAR')
key(ghost,'location',1614,mouth+Vector((.67,-.2,.65)))

script_dir = Path('D:/remotionshorts/scripts/circle_challenge')
for module, function, args in [
    ('cinematic_finish.py','finish',(s,key)),
    ('cinematic_polish.py','polish',(s,key,material,label)),
]:
    namespace = {}
    path = script_dir/module
    exec(compile(path.read_text(encoding='utf-8-sig'),str(path),'exec'),namespace)
    namespace[function](*args)
s.frame_set(70)
s['calibration_revision'] = 2
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'circle_challenge.blend'))

