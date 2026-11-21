"""Mesh, curve, material, and lighting construction for the benchmark."""
import math
from pathlib import Path

import bpy
from mathutils import Vector

import ricks_lookdev as look

ART = Path(__file__).with_name("art")
INK = None


def surface(name, color, rough=.78, metal=0., glow=0.):
    m = bpy.data.materials.new(name)
    m.diffuse_color = look.rgba(color)
    m.use_nodes = True
    b = next(node for node in m.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = m.diffuse_color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = .32
    if glow:
        b.inputs["Emission Color"].default_value = m.diffuse_color
        b.inputs["Emission Strength"].default_value = glow
    return m


def emission(name, color, strength=1):
    m = bpy.data.materials.new(name)
    m.diffuse_color = look.rgba(color)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    light, out = n.new("ShaderNodeEmission"), n.new("ShaderNodeOutputMaterial")
    light.inputs[0].default_value, light.inputs[1].default_value = m.diffuse_color, strength
    l.new(light.outputs[0], out.inputs[0])
    return m


def skin(name, tone, stops):
    m = surface(name, tone, .85)
    n, l = m.node_tree.nodes, m.node_tree.links
    b = next(node for node in n if node.type == "BSDF_PRINCIPLED")
    b.inputs["Specular IOR Level"].default_value = .05
    out = next(node for node in n if node.type == "OUTPUT_MATERIAL")
    lit = n.new("ShaderNodeShaderToRGB")
    ramp = n.new("ShaderNodeValToRGB")
    look._ramp(ramp, stops)
    mix = n.new("ShaderNodeMixRGB")
    mix.inputs[0].default_value = .65
    out_light = n.new("ShaderNodeEmission")
    l.new(b.outputs[0], lit.inputs[0])
    l.new(lit.outputs[0], ramp.inputs[0])
    l.new(ramp.outputs[0], mix.inputs[1])
    l.new(lit.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out_light.inputs[0])
    l.new(out_light.outputs[0], out.inputs[0])
    return m


def texture(name, colors, kind, roughness=(.58, .84)):
    m = surface(name, colors[0], roughness[0])
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(node for node in n if node.type == "BSDF_PRINCIPLED")
    coord = n.new("ShaderNodeTexCoord")
    mapping = n.new("ShaderNodeVectorMath")
    mapping.operation = "MULTIPLY"
    mapping.inputs[1].default_value = {"wood": (.72, 7.4, 5.9), "asphalt": (1.5, 1.5, 1.5),
                                      "plaster": (3, 3, 3)}[kind]
    l.new(coord.outputs["Object"], mapping.inputs[0])
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 7 if kind == "wood" else 3
    noise.inputs["Detail"].default_value = 2.3
    l.new(mapping.outputs[0], noise.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    look._ramp(ramp, [(0.16, colors[0]), (.48, colors[1]), (.79, colors[2])])
    l.new(noise.outputs["Fac"], ramp.inputs[0])
    l.new(ramp.outputs[0], p.inputs["Base Color"])
    rough = n.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = roughness
    l.new(noise.outputs["Fac"], rough.inputs["Value"])
    l.new(rough.outputs[0], p.inputs["Roughness"])
    fine = n.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 68 if kind == "asphalt" else 15
    l.new(mapping.outputs[0], fine.inputs["Vector"])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .22 if kind == "asphalt" else .13
    bump.inputs["Distance"].default_value = .019 if kind == "asphalt" else .025
    l.new(fine.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs[0], p.inputs["Normal"])
    return m


def artwork(name, lit=True, glow=.15):
    m = surface(name, "#FFFFFF", .83)
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(node for node in n if node.type == "BSDF_PRINCIPLED")
    out = next(node for node in n if node.type == "OUTPUT_MATERIAL")
    img = n.new("ShaderNodeTexImage")
    if (ART / (name + ".png")).exists():
        img.image = bpy.data.images.load(str(ART / (name + ".png")), check_existing=True)
        img.image.pack()
    if lit:
        l.new(img.outputs["Color"], p.inputs["Base Color"])
        l.new(img.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = glow
        transparent = n.new("ShaderNodeBsdfTransparent")
        mix = n.new("ShaderNodeMixShader")
        l.new(img.outputs["Alpha"], mix.inputs[0])
        l.new(transparent.outputs[0], mix.inputs[1])
        l.new(p.outputs[0], mix.inputs[2])
        l.new(mix.outputs[0], out.inputs[0])
        m.surface_render_method = "BLENDED"
    else:
        em = n.new("ShaderNodeEmission")
        em.inputs[1].default_value = glow
        l.new(img.outputs["Color"], em.inputs[0])
        l.new(em.outputs[0], out.inputs[0])
    return m, img


def put(obj, col, parent=None, mat=None):
    for existing in tuple(obj.users_collection):
        existing.objects.unlink(obj)
    col.objects.link(obj)
    obj.parent = parent
    if mat and obj.data:
        obj.data.materials.append(mat)
    return obj


def empty(name, col, loc=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    put(obj, col, parent)
    obj.location = loc
    return obj


def mesh(name, col, vertices, faces, mat, parent=None, smoothing=False, uv=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = put(bpy.data.objects.new(name, data), col, parent, mat)
    if smoothing:
        for polygon in data.polygons:
            polygon.use_smooth = True
    if uv:
        layer = data.uv_layers.new(name="Surface artwork")
        for loop in data.loops:
            layer.data[loop.index].uv = uv[loop.vertex_index]
    return obj


def outline(obj, col, thickness=.006, mat=None):
    global INK
    if INK is None:
        INK = emission("Ink | near-black", "#0B0A10", .55)
        INK.use_backface_culling = True
    vertices = [tuple(v.co) for v in obj.data.vertices]
    faces = [tuple(reversed(p.vertices)) for p in obj.data.polygons]
    ink = mesh(obj.name + " • ink", col, vertices, faces, mat or INK, obj)
    for polygon, source in zip(ink.data.polygons, obj.data.polygons):
        polygon.use_smooth = source.use_smooth
    d = ink.modifiers.new("Screen-compensated hull", "DISPLACE")
    d.mid_level, d.strength = 0, -thickness
    look.mark_role(ink, "ink")
    return d


def box(name, col, loc, dim, mat, bevel=.018, parent=None, ink=0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name = name
    for vert in obj.data.vertices:
        for i, size in enumerate(dim):
            vert.co[i] *= size
    put(obj, col, parent, mat)
    obj.location = loc
    if ink:
        outline(obj, col, ink)
    if bevel:
        b = obj.modifiers.new("Soft caught edge", "BEVEL")
        b.width, b.segments = bevel, 2
    return obj


def ball(name, col, loc, radii, mat, parent=None, segments=24, rings=16, stretch=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings)
    obj = bpy.context.object
    obj.name = name
    for vert in obj.data.vertices:
        z = vert.co.z
        for axis, radius in enumerate(radii):
            vert.co[axis] *= radius
        if stretch:
            vert.co.z += stretch * (1 if z > .00001 else -1 if z < -.00001 else 0)
    put(obj, col, parent, mat)
    obj.location = loc
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def cylinder(name, col, loc, radius, depth, mat, parent=None, r2=None, length_segments=24):
    bpy.ops.mesh.primitive_cone_add(vertices=length_segments, radius1=radius,
                                   radius2=radius if r2 is None else r2, depth=depth)
    obj = bpy.context.object
    obj.name = name
    put(obj, col, parent, mat)
    obj.location = loc
    for p in obj.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return obj


def tube(name, col, coords, radius, mat, parent=None):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u, data.bevel_resolution = 9, 3
    data.bevel_depth, data.use_fill_caps = radius, True
    b = data.splines.new("BEZIER")
    b.bezier_points.add(len(coords) - 1)
    for p, co in zip(b.bezier_points, coords):
        p.co = co
        p.handle_left_type = p.handle_right_type = "AUTO"
    return put(bpy.data.objects.new(name, data), col, parent, mat)


def tube_pose(obj, coords, frame):
    for i, (point, co) in enumerate(zip(obj.data.splines[0].bezier_points, coords)):
        point.co = co
        obj.data.keyframe_insert(f"splines[0].bezier_points[{i}].co", frame=frame)


def aim(obj, target):
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = (Vector(target) - obj.location).to_track_quat("-Z", "Y")


def light(name, col, loc, target, color, watts, size=.3, kind="AREA", angle=55):
    data = bpy.data.lights.new(name, kind)
    data.color, data.energy = look.rgba(color)[:3], watts
    data.use_shadow = True
    data.use_shadow_jitter = False
    if kind == "AREA":
        data.size = size
    else:
        data.shadow_soft_size = size
        data.spot_size = math.radians(angle)
        data.spot_blend = .65
    obj = put(bpy.data.objects.new(name, data), col)
    obj.location = loc
    aim(obj, target)
    return obj


def beam(name, col, top, bottom, narrow, wide, color):
    """Low-opacity cone with volume-free feathering for the RT-off profile."""
    m = emission(name, color, .8)
    m.surface_render_method = "BLENDED"
    n, l = m.node_tree.nodes, m.node_tree.links
    em = next(node for node in n if node.type == "EMISSION")
    out = next(node for node in n if node.type == "OUTPUT_MATERIAL")
    geom, clear, mix = n.new("ShaderNodeLayerWeight"), n.new("ShaderNodeBsdfTransparent"), n.new("ShaderNodeMixShader")
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (.0, .0, .0, 1)
    ramp.color_ramp.elements[1].color = (.034, .034, .034, 1)
    l.new(geom.outputs["Facing"], ramp.inputs[0])
    l.new(ramp.outputs[0], mix.inputs[0])
    l.new(clear.outputs[0], mix.inputs[1])
    l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs[0])
    top, bottom = Vector(top), Vector(bottom)
    obj = cylinder(name, col, (top+bottom)/2, wide, (top-bottom).length, m, r2=narrow)
    obj.rotation_euler = (top-bottom).to_track_quat("Z", "Y").to_euler()
    look.mark_role(obj, "wisp")
    return obj
