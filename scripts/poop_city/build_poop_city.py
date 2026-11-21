"""Headless build of the poop_city short (Blender 4.2, EEVEE Next).

Phases:
  build  - construct set, cast, lights, cameras, animation; save poop_city.blend
  sheet  - open the saved blend and render the 12-tile calibration sheet

Runs only through run_headless.py (GPU lock + isolated profile). All assets and
outputs stay inside renders/poop_city. No live MCP, no texture swaps at render
time: expressions are child pose planes with CONSTANT scale swaps.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "poop_city"
SPR = OUT / "sprites"
FPS = 30
END = 1825

TIM = json.loads((OUT / "segments_timeline.json").read_text(encoding="utf-8"))
SEGS = {s["id"]: s for s in TIM["segments"]}
ENV = json.loads((OUT / "audio_env.json").read_text(encoding="utf-8"))
MOUTH = ENV["mouth"]
MAN = json.loads((SPR / "manifest.json").read_text(encoding="utf-8"))["characters"]


def log(m):
    print(f"[build] {m}", flush=True)


def ease_out(u):
    return 1 - (1 - u) ** 3


def event_progress(f, start, anticipate, extreme, settled):
    if f <= start:
        return 0.0
    if f < anticipate:
        return -0.06 * ease_out((f - start) / (anticipate - start))
    if f < extreme:
        return -0.06 + 1.14 * ease_out((f - anticipate) / (extreme - anticipate))
    if f < settled:
        return 1.08 - 0.08 * ease_out((f - extreme) / (settled - extreme))
    return 1.0


def anim(obj, attr, f, val, interp="CONSTANT"):
    setattr(obj, attr, val)
    obj.keyframe_insert(attr, frame=f)
    ad = getattr(obj, "animation_data", None)
    if ad is None:
        ad = getattr(obj.id_data, "animation_data", None)
    if ad and ad.action:
        for fc in ad.action.fcurves:
            if fc.data_path == attr or fc.data_path.endswith("." + attr):
                for kc in fc.keyframe_points:
                    if kc.co.x == f:
                        kc.interpolation = interp


def event(obj, attr, f0, f1, f2, f3, hold, v0, v1, step=2):
    for f in range(f0, f3 + 1, step):
        p = event_progress(f, f0, f1, f2, f3)
        v = tuple(a + (b - a) * p for a, b in zip(v0, v1)) if isinstance(v0, tuple) \
            else v0 + (v1 - v0) * p
        anim(obj, attr, f, v, "LINEAR")
    anim(obj, attr, hold, v1, "CONSTANT")


def look_rot(loc, target):
    d = (Vector(target) - Vector(loc)).normalized()
    q = d.to_track_quat("-Z", "Y")
    return q.to_euler()


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.use_raytracing = False
    sc.render.use_simplify = True
    sc.render.simplify_subdivision = 2
    sc.eevee.taa_render_samples = 64
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.fps = FPS
    sc.frame_start = 1
    sc.frame_end = END
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.look = "Medium High Contrast"
    return sc


def mat_world(name, color, rough=0.6, spec=0.2):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    return m


def organic_mat(name, color, rough, bump_scale, vein=0.0):
    m = mat_world(name, color, rough)
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 3.4
    n.inputs["Detail"].default_value = 6.0
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.inputs["Scale"].default_value = 2.2
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "ADD"
    mix.inputs["Fac"].default_value = 0.5
    nt.links.new(n.outputs["Fac"], mix.inputs["Color1"])
    nt.links.new(v.outputs["Distance"], mix.inputs["Color2"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_scale
    nt.links.new(mix.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    if vein > 0:
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.62
        dark = nt.nodes.new("ShaderNodeMixRGB")
        dark.blend_type = "MULTIPLY"
        dark.inputs["Fac"].default_value = vein
        dark.inputs["Color2"].default_value = (0.35, 0.16, 0.14, 1)
        nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], dark.inputs["Fac"])
        base = nt.nodes.new("ShaderNodeRGB")
        base.outputs[0].default_value = (*color, 1)
        nt.links.new(base.outputs[0], dark.inputs["Color1"])
        nt.links.new(dark.outputs["Color"], b.inputs["Base Color"])
    # high-contrast toon mucosal crease lines along ring folds / floor ripples
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 2.2
    wave.inputs["Distortion"].default_value = 6.0
    cramp = nt.nodes.new("ShaderNodeValToRGB")
    cramp.color_ramp.elements[0].position = 0.42
    cramp.color_ramp.elements[1].position = 0.58
    crease = nt.nodes.new("ShaderNodeMixRGB")
    crease.blend_type = "MULTIPLY"
    crease.inputs["Fac"].default_value = 0.35
    crease.inputs["Color2"].default_value = (0.290, 0.094, 0.082, 1)  # #4a1815
    src = None
    for l in list(nt.links):
        if l.to_node == b and l.to_socket.name == "Base Color":
            src = l.from_socket
            nt.links.remove(l)
            break
    if src is None:
        rgbn = nt.nodes.new("ShaderNodeRGB")
        rgbn.outputs[0].default_value = (*color, 1)
        src = rgbn.outputs[0]
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], cramp.inputs["Fac"])
    nt.links.new(cramp.outputs["Color"], crease.inputs["Fac"])
    nt.links.new(src, crease.inputs["Color1"])
    nt.links.new(crease.outputs["Color"], b.inputs["Base Color"])
    return m


def floor_mat(name):
    """V4 smooth glossy mucosa: low-freq 2-tone coral, zero white stripes."""
    m = mat_world(name, (0.482, 0.084, 0.061), 0.18, 0.08)  # #b85246 lit
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "Y"
    wave.inputs["Scale"].default_value = 1.8
    wave.inputs["Distortion"].default_value = 1.5
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (0.262, 0.038, 0.026, 1)  # #8c372e trough
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[1].color = (0.482, 0.084, 0.061, 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(wave.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def cel_mat(name, path):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.surface_render_method = "BLENDED"
    m.use_transparent_shadow = True
    m.use_backface_culling = False
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(path))
    tex.interpolation = "Cubic"
    prin = nt.nodes.new("ShaderNodeBsdfPrincipled")
    prin.inputs["Roughness"].default_value = 0.60
    prin.inputs["Specular IOR Level"].default_value = 0.20
    emi = nt.nodes.new("ShaderNodeEmission")
    emi.inputs["Strength"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.15
    trans = nt.nodes.new("ShaderNodeBsdfTransparent")
    outer = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Color"], prin.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], emi.inputs["Color"])
    nt.links.new(prin.outputs[0], mix.inputs[1])
    nt.links.new(emi.outputs[0], mix.inputs[2])
    nt.links.new(trans.outputs[0], outer.inputs[1])
    nt.links.new(mix.outputs[0], outer.inputs[2])
    nt.links.new(tex.outputs["Alpha"], outer.inputs["Fac"])
    nt.links.new(outer.outputs[0], out.inputs["Surface"])
    return m


def fx_mat(name, path, strength=2.2):
    m = cel_mat(name, path)
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == "EMISSION":
            n.inputs["Strength"].default_value = strength
    return m


def plane(name, w, h, mat, parent=None, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    verts = [(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)]
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    me.uv_layers.new()
    for i, uv in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        me.uv_layers[0].data[i].uv = uv
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.append(mat)
    if parent:
        ob.parent = parent
    ob.location = loc
    bpy.context.collection.objects.link(ob)
    return ob


def empty(name, parent=None, loc=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    if parent:
        ob.parent = parent
    ob.location = loc
    bpy.context.collection.objects.link(ob)
    return ob


def add_depth_haze(m, near=3.5, far=11.0):
    """Blend the surface toward crimson-black with camera distance (View Z)."""
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    cam = nt.nodes.new("ShaderNodeCameraData")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = near
    mr.inputs["From Max"].default_value = far
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs["Color2"].default_value = (0.431, 0.169, 0.149, 1)  # #6e2b26 deep haze
    src = None
    for l in list(nt.links):
        if l.to_node == b and l.to_socket.name == "Base Color":
            src = l.from_socket
            nt.links.remove(l)
            break
    if src is not None:
        nt.links.new(src, mix.inputs["Color1"])
    else:
        mix.inputs["Color1"].default_value = b.inputs["Base Color"].default_value
    nt.links.new(cam.outputs["View Z Depth"], mr.inputs["Value"])
    nt.links.new(mr.outputs[0], mix.inputs["Fac"])
    nt.links.new(mix.outputs[0], b.inputs["Base Color"])


def vein_tube(name, pts, mat, r=0.05):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = r
    cu.bevel_resolution = 3
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu)
    ob.data.materials.append(mat)
    bpy.context.collection.objects.link(ob)
    return ob


def build_set(sc):
    wall = organic_mat("mucosa_wall", (0.80, 0.42, 0.36), 0.22, 0.35, vein=0.5)
    add_depth_haze(wall)
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=4.2, depth=24,
                                        end_fill_type="NOTHING",
                                        location=(0, 8.0, 2.4), rotation=(math.pi / 2, 0, 0))
    tun = bpy.context.object
    tun.name = "colon_tunnel"
    tun.data.materials.append(wall)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    sub = tun.modifiers.new("sub", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    tex = bpy.data.textures.new("haustra", "CLOUDS")
    tex.noise_scale = 0.9
    disp = tun.modifiers.new("disp", "DISPLACE")
    disp.texture = tex
    disp.strength = 0.22
    for i in range(14):
        y = -3.2 + i * 1.6
        bpy.ops.mesh.primitive_torus_add(major_radius=4.05, minor_radius=0.24,
                                         location=(0, y, 2.4),
                                         rotation=(math.pi / 2, 0, 0),
                                         major_segments=48, minor_segments=10)
        rib = bpy.context.object
        rib.name = f"haustral_rib_{i}"
        rib.data.materials.append(wall)
    floor_m = floor_mat("mucosa_floor")
    add_depth_haze(floor_m)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=48, y_subdivisions=48, size=11,
                                    location=(0, 2.0, 0))
    fl = bpy.context.object
    fl.name = "floor"
    fl.data.materials.append(floor_m)
    fd = fl.modifiers.new("disp", "DISPLACE")
    fd.texture = tex
    fd.strength = 0.06
    # recessed 6 m sphincter chamber (Y +8..+14) with toroidal folds + dark interior
    sph = organic_mat("sphincter", (0.45, 0.16, 0.14), 0.35, 0.5)
    add_depth_haze(sph, near=6.0, far=14.0)
    nt = sph.node_tree
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mathn = nt.nodes.new("ShaderNodeMath")
    mathn.operation = "MULTIPLY"
    mathn.inputs[1].default_value = 26.0
    sin = nt.nodes.new("ShaderNodeMath")
    sin.operation = "SINE"
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], mathn.inputs[0])
    nt.links.new(mathn.outputs[0], sin.inputs[0])
    nt.links.new(sin.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], nt.nodes["Principled BSDF"].inputs["Normal"])
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.7, depth=6,
                                        end_fill_type="NOTHING",
                                        location=(0, 11.0, 2.4),
                                        rotation=(math.pi / 2, 0, 0))
    ch = bpy.context.object
    ch.name = "sphincter_chamber"
    ch.data.materials.append(sph)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.flip_normals()
    bpy.ops.object.mode_set(mode="OBJECT")
    for i, y in enumerate((8.0, 9.5, 11.0, 12.5, 14.0)):
        bpy.ops.mesh.primitive_torus_add(major_radius=1.7 - i * 0.12, minor_radius=0.22,
                                         location=(0, y, 2.4),
                                         rotation=(math.pi / 2, 0, 0),
                                         major_segments=40, minor_segments=10)
        fold = bpy.context.object
        fold.name = f"sphincter_fold_{i}"
        fold.data.materials.append(sph)
    for k in range(8):
        a = 2 * math.pi * k / 8
        x, z = 1.7 * math.cos(a), 2.4 + 1.7 * math.sin(a)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.10,
                                             location=(x, 8.0, z))
        cr = bpy.context.object
        cr.name = f"sphincter_crease_{k}"
        cr.scale = (1, 6, 1)
        cr.data.materials.append(sph)
    chamber_light = bpy.data.lights.new("chamber_red", "POINT")
    chamber_light.color = (0.60, 0.05, 0.05)
    chamber_light.energy = 40
    chamber_light.shadow_soft_size = 0.6
    clo = bpy.data.objects.new("chamber_red", chamber_light)
    clo.location = (0, 12.5, 2.4)
    bpy.context.collection.objects.link(clo)
    cap = mat_world("far_cap", (0.431, 0.169, 0.149), 0.8)
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=4.2, fill_type="NGON",
                                      location=(0, 20.0, 2.4),
                                      rotation=(math.pi / 2, 0, 0))
    bpy.context.object.name = "tunnel_far_cap"
    bpy.context.object.data.materials.append(cap)
    # branching sub-mucosal vein tubes along the walls
    vein_m = mat_world("vein", (0.29, 0.09, 0.08), 0.30, 0.4)
    add_depth_haze(vein_m)
    vein_tube("vein_l0", [(-3.6, -2, 1.2), (-3.8, 0, 1.8), (-3.6, 2, 2.6),
                          (-3.7, 4, 3.2), (-3.5, 6, 3.6)], vein_m, 0.07)
    vein_tube("vein_l1", [(-3.7, 1, 2.2), (-3.3, 2, 1.4), (-3.5, 3.4, 0.9)], vein_m, 0.045)
    vein_tube("vein_r0", [(3.6, -1, 1.4), (3.8, 1, 2.2), (3.6, 3, 3.0),
                          (3.7, 5, 3.5)], vein_m, 0.07)
    vein_tube("vein_r1", [(3.7, 2, 2.6), (3.3, 3, 1.6), (3.5, 4.4, 1.0)], vein_m, 0.045)
    # wet specular mucus droplets
    mucus = mat_world("mucus", (0.95, 0.75, 0.72), 0.08, 0.6)
    for i, (x, y, z, r) in enumerate([(-2.6, -1.0, 0.05, 0.09), (2.7, -0.6, 0.05, 0.11),
                                      (-3.2, 1.4, 0.9, 0.07), (3.2, 1.8, 1.1, 0.08),
                                      (0.4, -2.2, 0.04, 0.08), (-1.6, -2.4, 0.04, 0.06)]):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=r,
                                             location=(x, y, z))
        dr = bpy.context.object
        dr.name = f"mucus_{i}"
        dr.scale = (1, 1, 0.6)
        dr.data.materials.append(mucus)
    # toon-inked foreground / midground poop mounds + corn / peanut props
    for i, (tag, x, y, z, w) in enumerate([
            ("a", -2.3, -2.6, 0.42, 0.95), ("b", 2.4, -2.9, 0.50, 1.10),
            ("c", -1.7, -0.8, 0.30, 0.60), ("a", 1.7, -1.0, 0.35, 0.70),
            ("b", 2.2, 0.6, 0.30, 0.60)]):
        mw = w
        mh = w * (512 / 512 if tag != "b" else 448 / 512)
        p = plane(f"toon_mound_{i}", mw, mh, cel_mat(f"toon_mound_{i}_m",
                                                    SPR / f"mound_{tag}.png"),
                  loc=(x, y, z))
        p.rotation_euler = (math.pi / 2, 0, 0)
    for i, (tag, x, y, r) in enumerate([("corn", -1.9, -2.2, 0.5), ("peanut", 1.6, -2.5, 1.2),
                                        ("corn", 2.8, -1.6, 2.0)]):
        p = plane(f"prop_{tag}_{i}", 0.24, 0.24, cel_mat(f"prop_{tag}_{i}_m",
                                                        SPR / f"{tag}.png"),
                  loc=(x, y, 0.10))
        p.rotation_euler = (math.pi / 2, 0, r)
    mini = cel_mat("mini_sperm", SPR / "mini_sperm.png")
    for i, (x, y, r) in enumerate([(-1.4, -0.5, 0.4), (0.6, -0.7, 1.2), (1.5, -0.4, 2.1),
                                   (-1.9, -0.6, 0.9), (1.2, -2.6, 1.7), (2.6, -2.0, 0.2)]):
        p = plane(f"mini_sperm_{i}", 0.30, 0.21, mini, loc=(x, y, 0.06))
        p.rotation_euler = (0, 0, r)
    # wrong-neighborhood gag: tilted toon road sign, deep center-right background
    sign = plane("gag_sign", 0.75, 0.405, cel_mat("gag_sign_m", SPR / "sign.png"),
                 loc=(0.55, 2.4, 1.15))
    sign.rotation_euler = (math.pi / 2, 0, math.radians(-8))


def grade(obj, attr, keys, ramp=8):
    """Hold each value, then linearly ramp into the next beat over `ramp` frames."""
    prev = None
    for f, val in keys:
        if prev is not None:
            anim(obj, attr, f - ramp, prev, "LINEAR")
        anim(obj, attr, f, val, "CONSTANT")
        prev = val


def build_lights(sc):
    key = bpy.data.lights.new("key_sun", "SUN")
    key.energy = 5.5
    key.angle = math.radians(6)
    key.use_shadow = True
    key.color = (1.0, 0.953, 0.922)  # #fff3eb warm peach-white
    ko = bpy.data.objects.new("key_sun", key)
    ko.rotation_euler = (math.radians(32), 0, math.radians(-32))  # 58 deg elevation
    bpy.context.collection.objects.link(ko)
    rim = bpy.data.lights.new("rim_warm", "SUN")
    rim.energy = 1.5
    rim.angle = math.radians(8)
    rim.use_shadow = False
    rim.color = (1.0, 0.62, 0.52)
    ro = bpy.data.objects.new("rim_warm", rim)
    ro.rotation_euler = (math.radians(115), 0, math.radians(18))
    bpy.context.collection.objects.link(ro)
    fill = bpy.data.lights.new("fill_soft", "AREA")
    fill.energy = 450
    fill.size = 8.0
    fill.color = (1.0, 0.851, 0.831)  # #ffd9d4
    fo = bpy.data.objects.new("fill_soft", fill)
    fo.location = (0, -3.0, 5.0)
    fo.rotation_euler = (math.radians(35), 0, 0)
    bpy.context.collection.objects.link(fo)
    char_key = bpy.data.lights.new("char_key", "AREA")
    char_key.energy = 150
    char_key.size = 4.0
    char_key.color = (1.0, 0.97, 0.92)
    ck = bpy.data.objects.new("char_key", char_key)
    ck.location = (-0.5, -2.0, 2.6)
    ck.rotation_euler = (math.radians(50), 0, 0)
    bpy.context.collection.objects.link(ck)
    w = bpy.data.worlds.new("cavern_world")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.72, 0.35, 0.30, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.5
    sc.world = w
    # 4-beat motivated grade arc (tamed reds, bright throughout)
    grade(key, "color", [(1, (1.0, 0.953, 0.922)), (221, (1.0, 0.88, 0.80)),
                         (762, (1.0, 0.70, 0.62)), (975, (1.0, 0.93, 0.85))])
    grade(key, "energy", [(1, 5.5), (221, 6.0), (762, 5.5), (975, 5.5)])
    grade(rim, "color", [(1, (1.0, 0.62, 0.52)), (221, (0.60, 0.20, 0.20)),
                         (762, (1.0, 0.50, 0.45)), (975, (0.80, 0.50, 0.70))])
    grade(fill, "color", [(1, (1.0, 0.851, 0.831)), (975, (0.85, 0.85, 1.0))])
    sir = bpy.data.lights.new("siren_red", "POINT")
    sir.color = (1.0, 0.09, 0.266)  # #ff1744
    sir.energy = 0
    sir.shadow_soft_size = 0.4
    so = bpy.data.objects.new("siren_red", sir)
    so.location = (-1.2, -1.1, 1.7)
    bpy.context.collection.objects.link(so)
    for f, e in [(891, 0), (905, 180), (915, 40), (930, 200), (940, 40), (955, 0),
                 (962, 260), (966, 40), (969, 260), (973, 30), (976, 0)]:
        anim(sir, "energy", f, e, "LINEAR")
    return so


def contact_patch(name, x, y, base_w, alpha=0.80, feather=0.08, z=0.06):
    """Tight base-width contact shadow: #26070a, alpha `alpha` feathering to 0
    over `feather` metres. Real cast shadows come from the key sun."""
    m = bpy.data.materials.new(name + "_mat")
    m.use_nodes = True
    m.surface_render_method = "BLENDED"
    m.use_transparent_shadow = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sub = nt.nodes.new("ShaderNodeVectorMath")
    sub.operation = "SUBTRACT"
    sub.inputs[1].default_value = (0.5, 0.5, 0.0)
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.clamp = True
    mr.inputs["From Min"].default_value = max(0.0, 0.5 - feather / base_w)
    mr.inputs["From Max"].default_value = 0.5
    mr.inputs["To Min"].default_value = alpha
    mr.inputs["To Max"].default_value = 0.0
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
    pr.inputs["Base Color"].default_value = (0.149, 0.027, 0.039, 1)  # #26070a
    pr.inputs["Roughness"].default_value = 0.9
    nt.links.new(tc.outputs["UV"], sub.inputs[0])
    nt.links.new(sub.outputs["Vector"], ln.inputs[0])
    nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
    nt.links.new(mr.outputs[0], pr.inputs["Alpha"])
    nt.links.new(pr.outputs[0], out.inputs["Surface"])
    ob = plane(name, base_w, base_w * 0.45, m, loc=(x, y, z))
    ob.visible_shadow = False
    return ob


def key_floor_hit(x, y, z):
    """Project a point to the floor along the key sun vector (58 deg, -32 deg)."""
    d = Vector((0.281, 0.450, -0.848))
    t = z / 0.848
    return (x + d.x * t, y + d.y * t)


CAST_POS = {
    "sperm": (-0.38, 0.0, 0.48),
    "buff": (0.16, 0.28, 0.0),
    "potato": (0.42, 0.52, 0.0),
    "swirl": (0.34, -0.08, 0.0),
}
CARD_W = {"sperm": 0.62, "buff": 0.60, "potato": 0.62, "swirl": 0.66}
BODY_W = 0.90
# design-px gap between each body art's bottom ink edge and its plane bottom
GROUND_PX = {"buff": 80, "potato": 180, "swirl": 219}


def build_character(name, cam):
    cfg = MAN[name]
    cw, ch = cfg["card_size"]
    s = CARD_W[name] / cw
    root = empty(f"root_{name}", loc=CAST_POS[name])
    bb = empty(f"billboard_{name}", parent=root)
    cr = bb.constraints.new("COPY_ROTATION")
    cr.target = cam
    cr.owner_space = "WORLD"
    cr.target_space = "WORLD"
    idle = empty(f"idle_{name}", parent=bb)
    bounce = empty(f"bounce_{name}", parent=idle)
    card_h = ch * s
    zc = card_h / 2 if name != "sperm" else 0.0
    body_poses, arm_poses, card_hat = {}, {}, None
    if name == "buff":
        bs = BODY_W / 1536
        bh = 1920 * bs
        for pose, info in cfg["body_poses"].items():
            bp = plane(f"buff_body_{pose}", BODY_W, bh,
                       cel_mat(f"buff_body_{pose}_m", SPR / info["file"]),
                       parent=bounce, loc=(0, bh / 2, 0))
            bp.scale = (0, 0, 0)
            body_poses[pose] = bp
        zc = bh + CARD_W[name] / 2 - 0.26
    if name != "sperm":
        margin = GROUND_PX[name] * (bs if name == "buff" else s)
        root.location.z = 0.01 - margin
    card = plane(f"card_{name}", CARD_W[name], card_h,
                 cel_mat(f"card_{name}_m", SPR / cfg["card"]), parent=bounce,
                 loc=(0, zc, 0.01 if name == "buff" else 0))
    if name == "sperm":
        card_hat = plane("sperm_card_hat", CARD_W[name], card_h,
                         cel_mat("sperm_card_hat_m", SPR / cfg["card_hat"]),
                         parent=bounce, loc=(0, zc, 0.002))
        card_hat.scale = (0, 0, 0)
    if name in ("potato", "swirl"):
        for pose, info in cfg["arm_poses"].items():
            ap = plane(f"{name}_arms_{pose}", CARD_W[name], card_h,
                       cel_mat(f"{name}_arms_{pose}_m", SPR / info["file"]),
                       parent=bounce, loc=(0, zc, 0.006))
            ap.scale = (0, 0, 0)
            arm_poses[pose] = ap
    face = empty(f"face_{name}", parent=bounce, loc=(0, zc, 0))
    parts = {}
    for slot, variants in (("eyes", ["open", "half", "squint", "closed", "wide", "sad"]),
                           ("brows", ["neutral", "angry", "raised", "sad"]),
                           ("mouth", ["closed", "smile", "small", "mid", "wide", "laugh", "frown"])):
        for v in variants:
            info = cfg["parts"][f"{slot}_{v}"]
            pw, ph = info["size"]
            ax, ay = info["anchor"]
            cx, cy = cfg["center"]
            z = {"eyes": 0.012, "brows": 0.016, "mouth": 0.020}[slot]
            p = plane(f"{name}_{slot}_{v}", pw * s, ph * s,
                      cel_mat(f"{name}_{slot}_{v}_m", SPR / info["file"]),
                      parent=face, loc=((ax - cx) * s, (cy - ay) * s, z))
            p.scale = (0, 0, 0)
            parts[(slot, v)] = p
    hat = None
    if name == "sperm":
        hi = cfg["parts"]["hardhat"]
        hw, hh = hi["size"]
        ax, ay = hi["anchor"]
        cx, cy = cfg["center"]
        hat = plane("sperm_hardhat", hw * s, hh * s,
                    cel_mat("hardhat_m", SPR / hi["file"]), parent=face,
                    loc=((ax - cx) * s, (cy - ay) * s, 0.026))
        hat.scale = (0, 0, 0)
    if name == "sperm":
        sx, sy = key_floor_hit(CAST_POS[name][0], CAST_POS[name][1], CAST_POS[name][2])
        disc = contact_patch(f"contact_{name}", sx, sy, 0.45, alpha=0.45, feather=0.18, z=0.02)
    else:
        disc = contact_patch(f"contact_{name}", CAST_POS[name][0], CAST_POS[name][1],
                             CARD_W[name] * 1.05 if name != "buff" else BODY_W * 1.05,
                             z=0.02)
    return dict(root=root, bb=bb, idle=idle, bounce=bounce, card=card,
                card_hat=card_hat, face=face, parts=parts, body_poses=body_poses,
                arm_poses=arm_poses, hat=hat, s=s, zc=zc, cfg=cfg)


def pose_timeline(poses, changes):
    changes = sorted(changes)
    for f, active in [(1, changes[0][1])] + changes:
        for pname, ob in poses.items():
            anim(ob, "scale", f, (1, 1, 1) if pname == active else (0, 0, 0), "CONSTANT")


def swap_timeline(ch, slot, changes):
    changes = sorted(changes)
    variants = [v for (sl, v) in ch["parts"] if sl == slot]
    for f, v in [(1, changes[0][1])] + changes:
        for vv in variants:
            anim(ch["parts"][(slot, vv)], "scale", f,
                 (1, 1, 1) if vv == v else (0, 0, 0), "CONSTANT")


def mouth_map(q):
    if q <= 0.0:
        return "closed"
    if q <= 0.2:
        return "small"
    if q <= 0.6:
        return "mid"
    return "wide"


def build_acting(chars):
    spans = {
        "sperm": [
            (1, 76, "open", "neutral", None), (77, 105, "squint", "neutral", None),
            (106, 195, "open", "raised", None), (196, 220, "wide", "raised", "wide"),
            (221, 295, "open", "raised", "smile"), (296, 347, "open", "sad", None),
            (348, 457, "open", "neutral", None), (458, 490, "wide", "raised", None),
            (491, 546, "open", "sad", None), (547, 761, "open", "neutral", None),
            (762, 890, "open", "neutral", None), (891, 929, "wide", "raised", None),
            (930, 974, "wide", "raised", "wide"), (975, 1071, "wide", "neutral", None),
            (1072, 1119, "open", "angry", None), (1120, 1209, "sad", "sad", "frown"),
            (1210, 1390, "half", "sad", "frown"), (1391, 1437, "sad", "sad", None),
            (1438, 1594, "half", "sad", "frown"), (1595, 1692, "sad", "sad", None),
            (1693, 1825, "half", "neutral", "closed"),
        ],
        "buff": [
            (1, 195, "open", "neutral", "closed"), (196, 220, "wide", "raised", "wide"),
            (221, 295, "open", "angry", None), (296, 554, "open", "neutral", "smile"),
            (555, 623, "open", "raised", None), (624, 820, "open", "neutral", "smile"),
            (821, 890, "open", "raised", None), (891, 974, "open", "neutral", "smile"),
            (975, 1071, "open", "neutral", None), (1072, 1297, "open", "neutral", "smile"),
            (1298, 1390, "open", "raised", None), (1391, 1437, "open", "neutral", "smile"),
            (1438, 1490, "open", "neutral", None), (1491, 1594, "closed", "raised", "laugh"),
            (1595, 1692, "open", "neutral", "smile"), (1693, 1739, "open", "raised", None),
            (1740, 1825, "closed", "raised", "laugh"),
        ],
        "potato": [
            (1, 105, "open", "neutral", "closed"), (106, 174, "squint", "angry", None),
            (175, 220, "wide", "raised", "wide"), (221, 347, "open", "neutral", "closed"),
            (348, 371, "wide", "raised", None), (372, 457, "open", "neutral", "closed"),
            (458, 481, "open", "neutral", "closed"), (482, 490, "closed", "raised", "laugh"),
            (491, 623, "open", "neutral", "closed"), (624, 682, "open", "angry", None),
            (683, 761, "open", "neutral", "smile"), (762, 929, "open", "neutral", "closed"),
            (930, 974, "half", "neutral", None), (975, 1119, "open", "neutral", "closed"),
            (1120, 1209, "wide", "raised", "smile"), (1210, 1490, "open", "neutral", "closed"),
            (1491, 1594, "closed", "raised", "laugh"), (1595, 1692, "open", "neutral", "closed"),
            (1693, 1825, "closed", "raised", "laugh"),
        ],
        "swirl": [
            (1, 174, "open", "neutral", "closed"), (175, 212, "open", "neutral", None),
            (213, 220, "wide", "raised", "wide"),
            (221, 371, "open", "neutral", "closed"), (372, 457, "half", "neutral", None),
            (458, 481, "open", "neutral", "closed"), (482, 490, "closed", "raised", "laugh"),
            (491, 682, "open", "neutral", "closed"), (683, 761, "half", "raised", None),
            (762, 929, "open", "neutral", "closed"), (930, 974, "half", "neutral", None),
            (975, 1119, "open", "neutral", "closed"), (1120, 1209, "wide", "raised", None),
            (1210, 1490, "open", "neutral", "closed"), (1491, 1594, "closed", "raised", "laugh"),
            (1595, 1692, "open", "neutral", "smile"), (1693, 1825, "closed", "raised", "laugh"),
        ],
    }
    talk = {1: "sperm", 2: "sperm", 3: "potato", 4: "potato", 5: "swirl", 6: "buff",
            7: "sperm", 8: "potato", 9: "swirl", 10: "sperm", 11: "sperm", 12: "buff",
            13: "potato", 14: "swirl", 15: "sperm", 16: "buff", 17: "sperm", 18: "swirl",
            19: "buff", 20: "sperm", 21: "swirl", 22: "sperm", 23: "buff", 24: "sperm",
            25: "buff", 26: "swirl", 27: "sperm", 28: "buff", 29: "buff"}
    for name, ch in chars.items():
        sp = spans[name]
        eyes_ch, brow_ch = [], []
        for (a, b, ev, bv, mv) in sp:
            eyes_ch.append((a, ev))
            brow_ch.append((a, bv))
        blink_at = {"sperm": 41, "buff": 67, "potato": 23, "swirl": 88}[name]
        intervals = [52, 61, 47, 66, 58]
        f, i = blink_at, 0
        while f < END - 6:
            cur = next((e for (a, b, e, bb_, m) in sp if a <= f <= b), "open")
            if cur in ("open", "half", "sad"):
                eyes_ch.append((f, "closed"))
                eyes_ch.append((f + 4, cur))
            f += intervals[i % len(intervals)]
            i += 1
        swap_timeline(ch, "eyes", eyes_ch)
        swap_timeline(ch, "brows", brow_ch)
        mouth_ch = []
        for (a, b, ev, bv, mv) in sp:
            if mv:
                mouth_ch.append((a, mv))
        for sid, speaker in talk.items():
            if speaker != name:
                continue
            seg = SEGS[sid]
            last, hold = None, 0
            for f in range(seg["start_frame"], seg["end_frame"] + 1):
                override = next((m for (a, b, e, bb_, m) in sp if a <= f <= b and m), None)
                q = MOUTH[f]
                if q > 0:
                    v = mouth_map(q)
                    if v == last:
                        hold += 1
                        if hold >= 2:
                            v = {"small": "mid", "mid": "small",
                                 "wide": "mid", "laugh": "wide"}[v]
                            hold = 0
                    else:
                        hold = 0
                else:
                    v = override or "closed"
                    hold = 0
                if v != last:
                    mouth_ch.append((f, v))
                    last = v
            mouth_ch.append((seg["end_frame"] + 1,
                             next((m for (a, b, e, bb_, m) in sp
                                   if a <= seg["end_frame"] + 1 <= b and m), "closed")))
        swap_timeline(ch, "mouth", mouth_ch)
        # per-syllable squash-stretch (2-4%) on the bounce rig, from the envelope
        env = ENV["env"]
        for sid, speaker in talk.items():
            if speaker != name:
                continue
            seg = SEGS[sid]
            a, b = seg["start_frame"], seg["end_frame"]
            anim(ch["bounce"], "scale", max(1, a - 1), (1, 1, 1), "CONSTANT")
            f = a
            while f <= b:
                q = env[min(f, len(env) - 1)]
                anim(ch["bounce"], "scale", f,
                     (1 - 0.02 * q, 1 + 0.035 * q, 1.0), "LINEAR")
                f += 3
            anim(ch["bounce"], "scale", b + 1, (1, 1, 1), "LINEAR")
    sp_c, bf_c, po_c, sw_c = (chars[n] for n in ("sperm", "buff", "potato", "swirl"))
    # V3: roots never move; all travel is camera-only. Face-local acting below.
    event(sp_c["face"], "location", 1201, 1204, 1210, 1216, 1297,
          (0, sp_c["zc"], 0), (0, sp_c["zc"] - 0.03, 0))
    for f0, f1, f2, f3, hold, t0, t1 in [
            (30, 34, 44, 50, 76, 0.0, 0.6), (52, 56, 62, 68, 76, 0.6, -0.4),
            (77, 80, 86, 92, 105, -0.4, 0.7)]:
        event(sp_c["face"], "location", f0, f1, f2, f3, hold,
              (t0 * 0.066, sp_c["zc"], 0), (t1 * 0.066, sp_c["zc"], 0))
    for f0, f1, f2, f3, hold, t0, t1 in [
            (624, 628, 636, 642, 660, 0.0, -0.5), (644, 648, 654, 660, 673, -0.5, 0.4),
            (662, 666, 670, 673, 700, 0.4, 0.0)]:
        event(po_c["face"], "location", f0, f1, f2, f3, hold,
              (t0 * 0.066, po_c["zc"], 0), (t1 * 0.066, po_c["zc"], 0))
    event(bf_c["card"], "scale", 224, 227, 232, 236, 260, (1, 1, 1), (1.05, 1.0, 1.05))
    event(bf_c["card"], "scale", 262, 265, 270, 274, 295, (1.05, 1.0, 1.05), (1, 1, 1))
    hat = sp_c["hat"]
    anim(hat, "scale", 1, (0, 0, 0), "CONSTANT")
    anim(hat, "scale", 1005, (1, 1, 1), "CONSTANT")
    s = sp_c["s"]
    start_local = (1.5, 0.55, 0.05)
    end_local = (0.0, (512 - 144) * s, 0.026)
    for f in range(1005, 1026, 2):
        p = event_progress(f, 1005, 1009, 1019, 1025)
        loc = tuple(a + (b - a) * p for a, b in zip(start_local, end_local))
        loc = (loc[0], loc[1] + 0.18 * math.sin(math.pi * min(max(p, 0), 1)), loc[2])
        anim(hat, "location", f, loc, "LINEAR")
    anim(hat, "location", 1025, end_local, "CONSTANT")
    # hat lands: hide the flying prop, swap to the baked hard-hat head card (fix 8)
    anim(hat, "scale", 1025, (0, 0, 0), "CONSTANT")
    anim(sp_c["card"], "scale", 1, (1, 1, 1), "CONSTANT")
    anim(sp_c["card"], "scale", 1025, (0, 0, 0), "CONSTANT")
    anim(sp_c["card_hat"], "scale", 1, (0, 0, 0), "CONSTANT")
    anim(sp_c["card_hat"], "scale", 1024, (0, 0, 0), "CONSTANT")
    event(sp_c["card_hat"], "scale", 1025, 1027, 1029, 1031, 1063,
          (1, 0.90, 1), (1, 1, 1))
    # body / arm pose schedules (fix 10)
    pose_timeline(bf_c["body_poses"], [
        (1, "crossed"), (196, "flex"), (221, "point"), (296, "crossed"),
        (624, "point"), (762, "crossed"), (930, "flex"), (975, "extend"),
        (1064, "crossed"), (1491, "laugh"), (1595, "crossed"), (1693, "laugh")])
    pose_timeline(po_c["arm_poses"], [
        (1, "hips"), (106, "point"), (221, "hips"), (482, "laugh"), (491, "hips"),
        (821, "welcome"), (891, "hips"), (1072, "facepalm"), (1210, "hips"),
        (1491, "laugh"), (1595, "hips"), (1693, "laugh")])
    pose_timeline(sw_c["arm_poses"], [
        (1, "hips"), (175, "point"), (221, "hips"), (482, "laugh"), (491, "hips"),
        (821, "welcome"), (891, "hips"), (1072, "facepalm"), (1210, "hips"),
        (1491, "laugh"), (1595, "hips"), (1693, "laugh")])
    # continuous idle motion in camera-aligned space (fix 10)
    idle_drivers = [
        (sp_c["idle"], "location", 0, "0.05*sin(0.10*frame)"),
        (sp_c["idle"], "location", 1, "0.03*sin(0.16*frame+1.0)"),
        (bf_c["idle"], "scale", 0, "1+0.020*sin(0.10*frame)"),
        (bf_c["idle"], "scale", 1, "1+0.012*sin(0.10*frame+3.14)"),
        (po_c["idle"], "scale", 0, "1+0.012*sin(0.11*frame+1.0)"),
        (po_c["idle"], "scale", 1, "1-0.010*sin(0.11*frame+1.0)"),
        (po_c["idle"], "rotation_euler", 0, "0.04*sin(0.07*frame+2.0)"),
        (sw_c["idle"], "scale", 0, "1+0.020*sin(0.13*frame)"),
        (sw_c["idle"], "scale", 1, "1-0.015*sin(0.13*frame)"),
        (sw_c["idle"], "rotation_euler", 0, "0.05*sin(0.06*frame)"),
    ]
    for ob, attr, idx, expr in idle_drivers:
        dr = ob.driver_add(attr, idx).driver
        dr.type = "SCRIPTED"
        dr.expression = expr
    for name, ch in chars.items():
        if name == "sperm":
            continue
        for (a, b) in [(482, 490), (1491, 1594), (1693, 1825)]:
            if b - a < 20:
                event(ch["card"], "scale", a, a + 2, a + 4, a + 6, b,
                      (1, 1, 1), (1.05, 1, 1.08))
                continue
            f = a
            while f < b - 10:
                event(ch["card"], "scale", f, f + 2, f + 5, f + 8, f + 10,
                      (1, 1, 1), (1.04, 1, 1.07))
                event(ch["card"], "scale", f + 10, f + 12, f + 14, f + 16, f + 18,
                      (1.04, 1, 1.07), (1, 1, 1))
                f += 20
    for (a, b) in [(196, 220)]:
        for name in ("potato", "swirl"):
            event(chars[name]["card"], "scale", a, a + 2, a + 5, a + 8, b,
                  (1, 1, 1), (1.06, 1, 1.06))
            event(chars[name]["card"], "scale", 221, 224, 228, 232, 295,
                  (1.06, 1, 1.06), (1, 1, 1))
    sweat_m = fx_mat("sweat_m", SPR / "sweat.png", 1.4)
    for i, (f0, f1) in enumerate([(962, 975), (1210, 1240)]):
        sw = plane(f"sweat_{i}", 0.09, 0.13, sweat_m, parent=sp_c["face"],
                   loc=(0.30, 0.22, 0.03))
        sw.scale = (0, 0, 0)
        anim(sw, "scale", 1, (0, 0, 0), "CONSTANT")
        anim(sw, "scale", f0, (1, 1, 1), "CONSTANT")
        event(sw, "location", f0, f0 + 2, f0 + 8, f1 - 2, f1,
              (0.30, 0.22, 0.03), (0.36, -0.05, 0.03))
        anim(sw, "scale", f1, (0, 0, 0), "CONSTANT")


def build_tail(ch):
    bb = ch["bounce"]
    me = bpy.data.meshes.new("tail_mesh")
    n = 24
    verts, faces, uvs = [], [], []
    for i in range(n + 1):
        t = i / n
        x = -0.16 - 0.14 * t
        yc = 0.10 * math.sin(math.pi * t)
        w = 0.10 * (1 - t) ** 1.3 + 0.010
        verts += [(x, yc, -w), (x, yc, w)]
        uvs += [(t, 0), (t, 1)]
    for i in range(n):
        a = 2 * i
        faces.append((a, a + 1, a + 3, a + 2))
    me.from_pydata(verts, [], faces)
    me.uv_layers.new()
    uvd = me.uv_layers[0].data
    for i in range(n):
        a = 2 * i
        for loop, vi in zip(range(4 * i, 4 * i + 4), (a, a + 1, a + 3, a + 2)):
            uvd[loop].uv = uvs[vi]
    ob = bpy.data.objects.new("sperm_tail", me)
    ob.parent = bb
    ob.location = (0, 0, -0.015)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(cel_mat("tail_m", SPR / "sperm_tail.png"))
    ob["swim_amp"] = 0.3
    k_sin = ob.shape_key_add(name="swim_sin")
    k_cos = ob.shape_key_add(name="swim_cos")
    lam = 0.22
    for i in range(n + 1):
        t = i / n
        x = -0.16 - 0.14 * t
        env = 0.05 * (1 - t) ** 1.2 + 0.006
        ph = 2 * math.pi * (x + 0.16) / lam
        for key, fn in ((k_sin, math.sin), (k_cos, math.cos)):
            dz = env * fn(ph)
            for k in (2 * i, 2 * i + 1):
                co = key.data[k].co
                key.data[k].co = (co.x, co.y + dz, co.z)
    for key, expr in ((k_sin, "amp*cos(0.30*frame)"),
                      (k_cos, "-amp*sin(0.30*frame)")):
        dr = key.driver_add("value").driver
        dr.type = "SCRIPTED"
        var = dr.variables.new()
        var.name = "amp"
        var.targets[0].id = ob
        var.targets[0].data_path = '["swim_amp"]'
        dr.expression = expr
    for f, amp in [(1, 0.3), (3, 1.0), (40, 1.0), (60, 0.35), (196, 0.6),
                   (220, 0.35), (962, 0.5), (976, 0.25), (1210, 0.2), (1825, 0.2)]:
        ob["swim_amp"] = amp
        ob.keyframe_insert('["swim_amp"]', frame=f)
    for fc in ob.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    return ob


def _shot(a, b, loc, tgt, lens, fs, push):
    l0, t0 = Vector(loc), Vector(tgt)
    l1 = l0 + (t0 - l0) * push
    t1 = t0 + Vector((0, 0, 0.02))
    return (a, b, tuple(l0), tuple(t0), tuple(l1), tuple(t1), lens, fs)


# V4 rhythm: same hard-cut boundaries, narrow 9:16-safe stage, deep-focus cels.
CAM_SETUPS = [
    _shot(1, 70, (-0.375, -1.35, 0.62), (-0.375, 0.00, 0.55), 45, 4.8, 0.10),
    _shot(71, 130, (-0.36, -1.15, 0.60), (-0.36, 0.00, 0.52), 45, 4.8, 0.12),
    _shot(131, 195, (1.90, -0.90, 0.70), (0.40, 0.25, 0.60), 34, 6.4, 0.10),
    _shot(196, 255, (-0.04, -2.65, 0.75), (-0.04, 0.30, 0.85), 34, 6.4, 0.09),
    _shot(256, 320, (-0.10, -2.65, 0.80), (-0.10, 0.15, 0.75), 34, 6.4, 0.10),
    _shot(321, 385, (1.35, -0.35, 0.65), (0.42, 0.52, 0.55), 50, 4.8, 0.12),
    _shot(386, 450, (1.30, -0.75, 0.60), (0.34, -0.08, 0.55), 42, 4.8, 0.11),
    _shot(451, 515, (-0.04, -2.90, 0.70), (-0.04, 0.30, 0.85), 32, 6.4, 0.09),
    _shot(516, 580, (-0.40, -1.20, 0.60), (-0.38, 0.00, 0.52), 42, 4.8, 0.12),
    _shot(581, 645, (0.16, -1.50, 0.85), (0.16, 0.28, 0.80), 45, 4.8, 0.11),
    _shot(646, 710, (1.40, -0.30, 0.68), (0.42, 0.52, 0.58), 50, 4.8, 0.12),
    _shot(711, 775, (-0.12, -2.80, 0.85), (-0.12, 0.15, 0.80), 34, 6.4, 0.10),
    _shot(776, 840, (1.25, -0.80, 0.62), (0.34, -0.08, 0.55), 42, 4.8, 0.11),
    _shot(841, 905, (-0.04, -2.65, 0.75), (-0.04, 0.30, 0.85), 34, 6.4, 0.09),
    _shot(906, 970, (-0.42, -1.15, 0.62), (-0.38, 0.00, 0.55), 45, 4.8, 0.12),
    _shot(971, 1035, (-0.36, -1.30, 0.66), (-0.36, 0.00, 0.60), 45, 4.8, 0.10),
    _shot(1036, 1100, (0.20, -1.55, 0.90), (0.16, 0.28, 0.85), 45, 4.8, 0.11),
    _shot(1101, 1165, (-0.38, -1.20, 0.60), (-0.38, 0.00, 0.52), 45, 4.8, 0.12),
    _shot(1166, 1230, (-0.40, -1.15, 0.58), (-0.38, 0.00, 0.50), 42, 4.8, 0.12),
    _shot(1231, 1295, (1.35, -0.35, 0.65), (0.42, 0.52, 0.55), 50, 4.8, 0.12),
    _shot(1296, 1360, (-0.04, -2.90, 0.72), (-0.04, 0.30, 0.85), 32, 6.4, 0.09),
    _shot(1361, 1425, (1.30, -0.75, 0.60), (0.34, -0.08, 0.55), 42, 4.8, 0.11),
    _shot(1426, 1490, (0.16, -1.50, 0.88), (0.16, 0.28, 0.82), 45, 4.8, 0.11),
    _shot(1491, 1555, (-0.04, -2.65, 0.70), (-0.04, 0.30, 0.85), 34, 6.4, 0.09),
    _shot(1556, 1620, (-0.10, -2.70, 0.80), (-0.10, 0.15, 0.75), 34, 6.4, 0.10),
    _shot(1621, 1692, (0.18, -1.55, 0.90), (0.16, 0.28, 0.85), 45, 4.8, 0.11),
    _shot(1693, 1757, (-0.04, -2.85, 0.75), (-0.04, 0.30, 0.85), 32, 6.4, 0.09),
    _shot(1758, 1825, (-0.12, -2.65, 0.82), (-0.12, 0.15, 0.78), 34, 6.4, 0.10),
]
SUBJECTS = [
    {"sperm"}, {"sperm"}, {"potato", "swirl"}, {"sperm", "buff", "potato", "swirl"},
    {"sperm", "buff"}, {"potato"}, {"swirl"}, {"sperm", "buff", "potato", "swirl"},
    {"sperm"}, {"buff"}, {"potato"}, {"sperm", "buff"}, {"swirl"},
    {"sperm", "buff", "potato", "swirl"}, {"sperm"}, {"sperm"}, {"buff"},
    {"sperm"}, {"sperm"}, {"potato"}, {"sperm", "buff", "potato", "swirl"},
    {"swirl"}, {"buff"}, {"sperm", "buff", "potato", "swirl"}, {"sperm", "buff"},
    {"buff"}, {"sperm", "buff", "potato", "swirl"}, {"sperm", "buff"},
]
SIGN_HIDE_SHOTS = [9, 16, 22, 25]  # buff solos: sign would sit behind his head


def build_camera(sc):
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36
    cd.dof.use_dof = True
    cam = bpy.data.objects.new("camera", cd)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    prev_end_key = None
    for (a, b, l0, t0, l1, t1, lens, fs) in CAM_SETUPS:
        cd.lens = lens
        cd.dof.aperture_fstop = fs
        for f, loc, tgt in ((a, l0, t0), (b, l1, t1)):
            cam.location = loc
            cam.rotation_euler = look_rot(loc, tgt)
            cam.keyframe_insert("location", frame=f)
            cam.keyframe_insert("rotation_euler", frame=f)
            cd.dof.focus_distance = (Vector(tgt) - Vector(loc)).length
            cd.keyframe_insert("dof.focus_distance", frame=f)
        ad = cam.animation_data.action
        for fc in ad.fcurves:
            if fc.data_path in ("location", "rotation_euler"):
                for kc in fc.keyframe_points:
                    if kc.co.x == a:
                        kc.interpolation = "LINEAR"
        cda = cd.animation_data.action
        for fc in cda.fcurves:
            for kc in fc.keyframe_points:
                if kc.co.x == a:
                    kc.interpolation = "LINEAR"
        if prev_end_key is not None:
            pa, pb = prev_end_key
            for fc in ad.fcurves:
                for kc in fc.keyframe_points:
                    if kc.co.x == pa:
                        kc.interpolation = "CONSTANT"
            for fc in cda.fcurves:
                for kc in fc.keyframe_points:
                    if kc.co.x == pa:
                        kc.interpolation = "CONSTANT"
        prev_end_key = (b, b)
        anim(cd, "lens", a, lens, "CONSTANT")
    for f, dx, dz in [(213, 0.05, 0.03), (215, -0.05, -0.04), (217, 0.04, 0.02),
                      (219, 0.0, 0.0)]:
        base = Vector(CAM_SETUPS[3][2])
        cam.location = base + Vector((dx, 0, dz))
        cam.keyframe_insert("location", frame=f)
    cam.location = CAM_SETUPS[0][2]
    cam.rotation_euler = look_rot(CAM_SETUPS[0][2], CAM_SETUPS[0][3])
    cam.keyframe_insert("location", frame=1)
    cam.keyframe_insert("rotation_euler", frame=1)
    return cam


def hide_timeline(chars):
    """Solo/pair shots hide off-subject cast so no elbow photobombs the frame."""
    sign = bpy.data.objects.get("gag_sign")
    for i, (a, b, *_rest) in enumerate(CAM_SETUPS):
        for name, ch in chars.items():
            hidden = name not in SUBJECTS[i]
            # hide_render does not propagate from an empty to its children
            targets = [ch["root"]] + list(ch["root"].children_recursive)
            disc = bpy.data.objects.get(f"contact_{name}")
            if disc:
                targets.append(disc)
            for ob in targets:
                anim(ob, "hide_render", a, hidden, "CONSTANT")
        if sign:
            anim(sign, "hide_render", a, i in SIGN_HIDE_SHOTS, "CONSTANT")


def verify_framing(sc, cam, chars):
    """Project every visible character bbox; 9:16 safe zone is 8%-92% width."""
    from bpy_extras.object_utils import world_to_camera_view
    bad = 0
    for i, (a, b, *_rest) in enumerate(CAM_SETUPS):
        for f in (a, b):
            sc.frame_set(f)
            bpy.context.view_layer.update()
            for name, ch in chars.items():
                if name not in SUBJECTS[i]:
                    continue
                objs = [ch["card"]] + list(ch["body_poses"].values()) \
                    + list(ch["arm_poses"].values())
                if name == "sperm":
                    objs.append(bpy.data.objects["sperm_tail"])
                xs, ys = [], []
                for ob in objs:
                    for c in ob.bound_box:
                        co = world_to_camera_view(sc, cam, ob.matrix_world @ Vector(c))
                        xs.append(co.x)
                        ys.append(co.y)
                lo, hi, ylo, yhi = min(xs), max(xs), min(ys), max(ys)
                ok = 0.08 <= lo and hi <= 0.92 and 0.0 <= ylo and yhi <= 1.0
                bad += 0 if ok else 1
                log(f"FRAME {'OK' if ok else 'VIOLATION'} shot{i+1:02d} f{f} "
                    f"{name} x[{lo:.2f},{hi:.2f}] y[{ylo:.2f},{yhi:.2f}]")
    log(f"framing violations={bad}")


def build_wisps(chars):
    spots = [(-1.5, 0.9, 0.35), (-0.6, 1.3, 0.30), (0.9, 1.1, 0.35), (1.7, 0.8, 0.30)]
    tags = ["a", "b", "c", "d"]
    for i, (x, y, z) in enumerate(spots):
        m = fx_mat(f"wisp_m_{i}", SPR / f"wisp_{tags[i]}.png", 3.2)
        w = plane(f"wisp_{i}", 0.26, 0.50, m, loc=(x, y, z + 0.30))
        w.rotation_euler = (math.pi / 2, 0, 0)
        w.visible_shadow = False
        em = next(n for n in m.node_tree.nodes if n.type == "EMISSION")
        anim(em.inputs["Strength"], "default_value", 1, 0.0, "CONSTANT")
        curl = 0.35 * (1 if i % 2 else -1)
        f = 1 + i * 11
        while f < END:
            a, b = f, min(f + 45, END)
            anim(em.inputs["Strength"], "default_value", a, 0.0, "LINEAR")
            anim(em.inputs["Strength"], "default_value", a + 12, 3.2, "LINEAR")
            anim(em.inputs["Strength"], "default_value", b - 10, 3.2, "LINEAR")
            anim(em.inputs["Strength"], "default_value", b, 0.0, "LINEAR")
            anim(w, "location", a, (x, y, z + 0.15), "LINEAR")
            anim(w, "location", b, (x, y, z + 0.40), "LINEAR")
            anim(w, "rotation_euler", a, (math.pi / 2, 0, 0.0), "LINEAR")
            anim(w, "rotation_euler", b, (math.pi / 2, 0, curl), "LINEAR")
            anim(w, "scale", a, (1.0, 1.0, 1.0), "LINEAR")
            anim(w, "scale", b, (0.72, 1.12, 1.0), "LINEAR")
            f = b + 1
    return


def compositor(sc):
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.threshold = 0.94
    glare.mix = -0.92  # mix 0 = full glare add; -0.92 keeps ~8% glow
    glare.size = 7
    em = nt.nodes.new("CompositorNodeEllipseMask")
    em.name = "vignette_mask"
    em.width = sc.render.resolution_x
    em.height = sc.render.resolution_y
    blur = nt.nodes.new("CompositorNodeBlur")
    blur.size_x = 160
    blur.size_y = 160
    blur.use_relative = False
    mr = nt.nodes.new("CompositorNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 0.59
    mr.inputs["To Max"].default_value = 1.0
    mul = nt.nodes.new("CompositorNodeMixRGB")
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1.0
    hs = nt.nodes.new("CompositorNodeHueSat")
    hs.name = "grade_sat"
    sat = hs.inputs["Sat"] if "Sat" in hs.inputs else hs.inputs[2]
    sat.default_value = 1.0
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
    nt.links.new(em.outputs["Mask"], blur.inputs["Image"])
    nt.links.new(blur.outputs["Image"], mr.inputs["Value"])
    nt.links.new(glare.outputs["Image"], mul.inputs[1])
    nt.links.new(mr.outputs[0], mul.inputs[2])
    nt.links.new(mul.outputs["Image"], hs.inputs["Image"])
    anim(sat, "default_value", 1, 0.94, "CONSTANT")
    anim(sat, "default_value", 969, 0.94, "LINEAR")
    anim(sat, "default_value", 975, 0.86, "LINEAR")
    anim(sat, "default_value", 1031, 0.94, "CONSTANT")
    expo = nt.nodes.new("CompositorNodeExposure")
    expo.inputs["Exposure"].default_value = 0.30
    nt.links.new(hs.outputs["Image"], expo.inputs["Image"])
    # V3: zero subtitles; ONLY the top-center hook badge, frames 1-105
    prev = expo.outputs["Image"]

    def overlay(path, keys):
        nonlocal prev
        img = nt.nodes.new("CompositorNodeImage")
        img.image = bpy.data.images.load(str(path))
        ao = nt.nodes.new("CompositorNodeAlphaOver")
        nt.links.new(prev, ao.inputs[1])
        nt.links.new(img.outputs["Image"], ao.inputs[2])
        for f, v in keys:
            anim(ao.inputs[0], "default_value", f, v, "CONSTANT")
        prev = ao.outputs[0]

    overlay(SPR / "hud_full.png", [(1, 1.0), (106, 0.0)])
    filt = nt.nodes.new("CompositorNodeFilter")
    filt.filter_type = "SHARPEN_DIAMOND"
    filt.inputs["Fac"].default_value = 0.16
    nt.links.new(prev, filt.inputs["Image"])
    nt.links.new(filt.outputs["Image"], comp.inputs["Image"])


def fit_vignette(sc):
    for n in sc.node_tree.nodes:
        if n.type == "ELLIPSEMASK":
            n.width = sc.render.resolution_x
            n.height = sc.render.resolution_y


SHEET_FRAMES = [40, 120, 160, 216, 290, 350, 610, 940, 1015, 1250, 1520, 1780]


def do_build():
    sc = clear_scene()
    build_set(sc)
    build_lights(sc)
    cam = build_camera(sc)
    chars = {n: build_character(n, cam) for n in ("sperm", "buff", "potato", "swirl")}
    build_tail(chars["sperm"])
    build_acting(chars)
    build_wisps(chars)
    hide_timeline(chars)
    compositor(sc)
    verify_framing(sc, cam, chars)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "poop_city_v4.blend"))
    log(f"saved {OUT / 'poop_city_v4.blend'}; objects={len(bpy.data.objects)}")


def do_sheet():
    bpy.ops.wm.open_mainfile(filepath=str(OUT / "poop_city_v4.blend"))
    sc = bpy.context.scene
    sc.render.resolution_x = 540
    sc.render.resolution_y = 960
    sc.eevee.taa_render_samples = 16
    fit_vignette(sc)
    cal = OUT / "calibration_v4"
    cal.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(SHEET_FRAMES):
        sc.frame_set(f)
        sc.render.filepath = str(cal / f"tile_{i:02d}_f{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        log(f"tile {i:02d} frame {f} done")
    log("sheet tiles complete")


def do_video(start, end, w=540, h=960):
    bpy.ops.wm.open_mainfile(filepath=str(OUT / "poop_city_v4.blend"))
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.render.fps = 30
    sc.eevee.taa_render_samples = 16 if w <= 540 else 24
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    fit_vignette(sc)
    fr = OUT / ("frames_v4" if w <= 540 else "frames_v4_1080")
    fr.mkdir(parents=True, exist_ok=True)
    for f in range(start, end + 1):
        sc.frame_set(f)
        sc.render.filepath = str(fr / f"f{f:04d}.png")
        bpy.ops.render.render(write_still=True)
    log(f"video frames {start}..{end} complete")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    phase = args[0] if args else "build"
    rest = args[1:]
    if phase == "sheet":
        do_sheet()
    elif phase == "master":
        do_video(int(rest[0]), int(rest[1]),
                 int(rest[2]) if len(rest) > 2 else 540,
                 int(rest[3]) if len(rest) > 3 else 960)
    else:
        do_build()