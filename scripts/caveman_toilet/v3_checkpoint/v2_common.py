"""Shared helpers for the caveman_toilet v2 build (Blender 4.2 EEVEE Next)."""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "caveman_toilet"
SPR = OUT / "sprites"
FPS = 30
END = 1620
sys.path.insert(0, str(Path(__file__).resolve().parent))


def log(m):
    print("BUILD " + str(m), flush=True)


def bake(ob, path, frames, values, index=-1):
    """Bulk keyframe bake: values is a list of scalars or N-vectors.
    Writes EVERY component fcurve (index=-1 creates them all)."""
    ad = ob.animation_data or ob.animation_data_create()
    act = ad.action or bpy.data.actions.new(ob.name + "_act")
    ad.action = act
    n = len(frames)
    scalar = not hasattr(values[0], "__len__")
    dim = 1 if scalar else max(len(v) for v in values)
    if scalar or index >= 0:
        fcs = [act.fcurves.new(data_path=path, index=index)]
    else:
        fcs = [act.fcurves.new(data_path=path, index=i) for i in range(dim)]
    for i, fc in enumerate(fcs):
        flat = []
        for f, v in zip(frames, values):
            comp = v if scalar else v[i]
            flat.extend((f, comp))
        fc.keyframe_points.add(n)
        fc.keyframe_points.foreach_set("co", flat)
        fc.keyframe_points.foreach_set("interpolation", [1] * n)  # LINEAR
        fc.update()
    return fcs[0]


def hide_keys(ob, frames, hidden):
    ad = ob.animation_data or ob.animation_data_create()
    act = ad.action or bpy.data.actions.new(ob.name + "_act")
    ad.action = act
    fc = act.fcurves.find("hide_render")
    if fc is None:
        fc = act.fcurves.new(data_path="hide_render")
    else:
        fc.keyframe_points.clear()
    n = len(frames)
    flat = []
    for f, h in zip(frames, hidden):
        flat.extend((f, float(h)))
    fc.keyframe_points.add(n)
    fc.keyframe_points.foreach_set("co", flat)
    fc.keyframe_points.foreach_set("interpolation", [0] * n)  # CONSTANT
    fc.update()


def ease_out(u):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def ev(f, start, anticipate, extreme, settled):
    if f <= start:
        return 0.0
    if f < anticipate:
        return -0.06 * ease_out((f - start) / (anticipate - start))
    if f < extreme:
        return -0.06 + 1.14 * ease_out((f - anticipate) / (extreme - anticipate))
    if f < settled:
        return 1.08 - 0.08 * ease_out((f - extreme) / (settled - extreme))
    return 1.0


def ramp01(f, a, b):
    return ease_out((f - a) / max(1, b - a))


def mat_world(name, color, rough=0.6, emit=0.0, emit_color=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.0
    if emit > 0:
        b.inputs["Emission Color"].default_value = (*(emit_color or color), 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def mat_ink(name="limb_ink"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.0075, 0.0056, 0.0097, 1)  # #161219
    b.inputs["Roughness"].default_value = 0.96
    b.inputs["Specular IOR Level"].default_value = 0.0
    return m


def mat_ground(name, c1, c2, scale=6.0, rough=0.85, bump=0.15):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Specular IOR Level"].default_value = 0.0
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    nt.links.new(noise.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def _alpha_setup(m):
    if hasattr(m, "surface_render_method"):
        try:
            m.surface_render_method = "BLENDED"
        except TypeError:
            pass
    if hasattr(m, "blend_method"):
        try:
            m.blend_method = "BLEND"
        except TypeError:
            m.blend_method = "HASHED"
    if hasattr(m, "show_transparent_back"):
        m.show_transparent_back = False


def cel_mat(name, img, emit=1.8, normals=False, fade=False, glow=False):
    """82% Principled + 18% Emission, alpha-correct; optional fake sphere normals
    (warm/cool two-sided shading on flat cards) and keyable Fade multiply."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    _alpha_setup(m)
    nt = m.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(img), check_existing=True)
    tex.image.colorspace_settings.name = "sRGB"
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.9
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if normals:
        uv = nt.nodes.new("ShaderNodeUVMap")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(uv.outputs["UV"], sep.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY_ADD"
        mx.inputs[1].default_value = 1.6; mx.inputs[2].default_value = -0.8
        my = nt.nodes.new("ShaderNodeMath"); my.operation = "MULTIPLY_ADD"
        my.inputs[1].default_value = 1.6; my.inputs[2].default_value = -0.8
        nt.links.new(sep.outputs["X"], mx.inputs[0])
        nt.links.new(sep.outputs["Y"], my.inputs[0])
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        comb.inputs["Z"].default_value = 1.0
        nt.links.new(mx.outputs["Value"], comb.inputs["X"])
        nt.links.new(my.outputs["Value"], comb.inputs["Y"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = 0.55
        nt.links.new(comb.outputs["Vector"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = emit
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    mix_cel = nt.nodes.new("ShaderNodeMixShader")
    mix_cel.inputs["Fac"].default_value = 0.75 if glow else 0.18
    nt.links.new(bsdf.outputs["BSDF"], mix_cel.inputs[1])
    nt.links.new(em.outputs["Emission"], mix_cel.inputs[2])
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix_a = nt.nodes.new("ShaderNodeMixShader")
    alpha_out = tex.outputs["Alpha"]
    if fade:
        val = nt.nodes.new("ShaderNodeValue")
        val.name = "Fade"
        val.outputs[0].default_value = 1.0
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(alpha_out, mul.inputs[0])
        nt.links.new(val.outputs[0], mul.inputs[1])
        alpha_out = mul.outputs["Value"]
    nt.links.new(alpha_out, mix_a.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix_a.inputs[1])
    nt.links.new(mix_cel.outputs["Shader"], mix_a.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_a.outputs["Shader"], out.inputs["Surface"])
    return m


def shadow_mat(name, img):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    _alpha_setup(m)
    nt = m.node_tree
    nt.nodes.clear()
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(img), check_existing=True)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.0
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(trans.outputs["BSDF"], mix.inputs[1])
    nt.links.new(b.outputs["BSDF"], mix.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m


def empty(name, parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def add_card(name, img, w, h, loc=(0, 0, 0), parent=None, mat=None, flat=True):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (w, h, 1)
    if flat:
        ob.rotation_euler = (math.radians(90), 0, 0)
    ob.data.materials.append(mat or cel_mat(name + "_mat", img))
    if parent:
        ob.parent = parent
        ob.location = loc
    return ob


def sphere(name, loc, r, mat, scale=(1, 1, 1), parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=20, ring_count=12)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


def smooth_rock(name, loc, r, mat, scale=(1, 1, 0.7), parent=None, rot=None):
    ob = sphere(name, loc, r, mat, scale=scale, parent=parent)
    if rot:
        ob.rotation_euler = rot
    sub = ob.modifiers.new("sub", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 1
    d = ob.modifiers.new("disp", "DISPLACE")
    d.texture = bpy.data.textures.get("rock_noise")
    d.strength = 0.12
    return ob


def limb_curve(name, parent=None, depth=0.026):
    """3-point endpoint NURBS stroke; points driven by hook empties (bakeable)."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = depth
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    cu.resolution_u = 8
    sp = cu.splines.new("NURBS")
    sp.points.add(2)
    sp.order_u = 3
    sp.use_endpoint_u = True
    for p in sp.points:
        p.co = (0, 0, 0, 1)
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat_ink())
    if parent:
        ob.parent = parent
    hooks = []
    for i in range(3):
        h = empty(f"{name}_p{i}", parent=ob)
        mod = ob.modifiers.new(f"hook{i}", "HOOK")
        mod.object = h
        mod.vertex_indices_set([i])
        hooks.append(h)
    return ob, hooks


def ik2(a, b, l1, l2, pole):
    """Two-bone solve, returns mid joint. pole = Vector bend direction."""
    a, b = Vector(a), Vector(b)
    d = b - a
    dist = d.length
    dist = max(1e-5, min(dist, l1 + l2 - 0.004))
    dirv = d.normalized()
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(l1 * l1 - x * x, 0.0))
    p = Vector(pole) - Vector(pole).dot(dirv) * dirv
    if p.length < 1e-6:
        p = Vector((0, -1, 0))
    p.normalize()
    return a + dirv * x + p * h


def cam_quat(pos, look):
    return (Vector(look) - Vector(pos)).to_track_quat("-Z", "Y")


def noise_mod(ob, path, index, scale, strength, phase=0.0):
    ad = ob.animation_data or ob.animation_data_create()
    act = ad.action or bpy.data.actions.new(ob.name + "_act")
    ad.action = act
    fc = act.fcurves.find(path, index=index)
    if fc is None:
        fc = act.fcurves.new(path, index=index)
        base = ob.path_resolve(path)
        if index >= 0:
            base = base[index]
        fc.keyframe_points.add(1)
        fc.keyframe_points[0].co = (1, base)
    mod = fc.modifiers.new("NOISE")
    mod.scale = scale
    mod.strength = strength
    mod.phase = phase
    mod.offset = 0.0
    return fc
