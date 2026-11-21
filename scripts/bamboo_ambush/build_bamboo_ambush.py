"""Stage 2B: Build 'Japanese Bamboo Ambush Twist (GOP GOP)' in Blender 4.2 (935 frames @ 30fps)."""
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Matrix, Quaternion, Vector

V = Vector
ROOT = Path(r"D:\remotionshorts")
OUT = ROOT / "renders" / "bamboo_ambush"
ART = OUT / "assets"

IMAGES = {}
MATS = {}

CUTS = [
    ("1A", 1, 90, 45),
    ("1B", 91, 189, 140),
    ("2A", 190, 285, 240),
    ("2B", 286, 404, 345),
    ("3A", 405, 459, 430),
    ("3B", 460, 528, 495),
    ("3C", 529, 590, 560),
    ("4A", 591, 696, 660),
    ("4B", 697, 768, 735),
    ("5A", 769, 834, 800),
    ("5B", 835, 888, 860),
    ("5C", 889, 935, 910),
]


def rgb(hex_str):
    v = [int(hex_str.lstrip("#")[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c < 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in v)


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def ease_out(u):
    u = max(0.0, min(1.0, u))
    return 1.0 - (1.0 - u) ** 3


def lerp(a, b, t):
    return V(a).lerp(V(b), t)


def key(o, path, f):
    o.keyframe_insert(data_path=path, frame=f)


def set_vis(o, on, f):
    o.hide_render = o.hide_viewport = not on
    key(o, "hide_render", f)
    key(o, "hide_viewport", f)


def packed_image(path):
    p = str(path)
    if p not in IMAGES:
        im = bpy.data.images.load(p, check_existing=False)
        im.pack()
        IMAGES[p] = im
    return IMAGES[p]


def mat(hex_col, metal=0.0, rough=0.55, em=0.0, name=None):
    k = (hex_col, metal, rough, em, name)
    if k in MATS:
        return MATS[k]
    m = bpy.data.materials.new(name or f"Mat_{hex_col}")
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    col = (*rgb(hex_col), 1.0)
    p.inputs["Base Color"].default_value = col
    p.inputs["Metallic"].default_value = metal
    p.inputs["Roughness"].default_value = rough
    p.inputs["Emission Color"].default_value = col
    p.inputs["Emission Strength"].default_value = em
    MATS[k] = m
    return m


def alpha_mat(name, hex_col, alpha=0.55, em=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.surface_render_method = "BLENDED"
    n = m.node_tree.nodes
    n.clear()
    l = m.node_tree.links
    tr = n.new("ShaderNodeBsdfTransparent")
    e = n.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*rgb(hex_col), 1.0)
    e.inputs[1].default_value = em
    mix = n.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = alpha
    l.new(tr.outputs[0], mix.inputs[1])
    l.new(e.outputs[0], mix.inputs[2])
    out = n.new("ShaderNodeOutputMaterial")
    l.new(mix.outputs[0], out.inputs[0])
    return m


def cel_mat(path, lit=True, ink_fours=True):
    """Scene-responsive cel shader: 82% Principled BSDF + 18% Emission with 4-frame stepped ink."""
    k = ("cel", str(path), lit)
    if k in MATS:
        return MATS[k]
    m = bpy.data.materials.new(f"Cel_{Path(path).stem}")
    m.use_nodes = True
    m.surface_render_method = "DITHERED" if lit else "BLENDED"
    n = m.node_tree.nodes
    n.clear()
    l = m.node_tree.links

    tex = n.new("ShaderNodeTexImage")
    tex.image = packed_image(path)
    tex.interpolation = "Linear"

    col_sock = tex.outputs["Color"]
    if lit and ink_fours:
        bw = n.new("ShaderNodeRGBToBW")
        l.new(tex.outputs["Color"], bw.inputs[0])
        is_ink = n.new("ShaderNodeMath")
        is_ink.operation = "LESS_THAN"
        is_ink.inputs[1].default_value = 0.035
        l.new(bw.outputs[0], is_ink.inputs[0])
        v = n.new("ShaderNodeValue")
        v.name = "Stepped_Ink_4f"
        for f in range(1, 936, 4):
            v.outputs[0].default_value = 1.0 + 0.010 * math.sin((f // 4) * 1.73)
            v.outputs[0].keyframe_insert("default_value", frame=f)
        if m.node_tree.animation_data and m.node_tree.animation_data.action:
            for fc in m.node_tree.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"
        tint = n.new("ShaderNodeMixRGB")
        tint.blend_type = "MULTIPLY"
        tint.inputs[0].default_value = 1.0
        l.new(tex.outputs["Color"], tint.inputs[1])
        l.new(v.outputs[0], tint.inputs[2])
        mix_ink = n.new("ShaderNodeMixRGB")
        l.new(is_ink.outputs[0], mix_ink.inputs[0])
        l.new(tex.outputs["Color"], mix_ink.inputs[1])
        l.new(tint.outputs[0], mix_ink.inputs[2])
        col_sock = mix_ink.outputs[0]

    if lit:
        bsdf = n.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = 0.58
        l.new(col_sock, bsdf.inputs["Base Color"])
        em = n.new("ShaderNodeEmission")
        em.inputs[1].default_value = 1.0
        l.new(col_sock, em.inputs[0])
        mix = n.new("ShaderNodeMixShader")
        mix.inputs[0].default_value = 0.18  # 82% Principled BSDF + 18% Emission
        l.new(bsdf.outputs[0], mix.inputs[1])
        l.new(em.outputs[0], mix.inputs[2])
        surf = mix.outputs[0]
    else:
        em = n.new("ShaderNodeEmission")
        em.inputs[1].default_value = 1.05
        l.new(col_sock, em.inputs[0])
        surf = em.outputs[0]

    tr = n.new("ShaderNodeBsdfTransparent")
    a_mix = n.new("ShaderNodeMixShader")
    l.new(tex.outputs["Alpha"], a_mix.inputs[0])
    l.new(tr.outputs[0], a_mix.inputs[1])
    l.new(surf, a_mix.inputs[2])
    out = n.new("ShaderNodeOutputMaterial")
    l.new(a_mix.outputs[0], out.inputs[0])
    MATS[k] = m
    return m


def sand_material(name, hex_dark, hex_lit, scale=6.0, bump=0.14):
    """Procedural Voronoi + Noise cracked beach sand material (no 4K PBR)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    l = m.node_tree.links
    bsdf = n.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.88

    tc = n.new("ShaderNodeTexCoord")
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 4.0
    l.new(tc.outputs["Object"], noise.inputs[0])

    vor = n.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = scale * 1.4
    l.new(tc.outputs["Object"], vor.inputs[0])

    cracks = n.new("ShaderNodeMapRange")
    cracks.inputs["From Min"].default_value = 0.0
    cracks.inputs["From Max"].default_value = 0.09
    cracks.inputs["To Min"].default_value = 0.0
    cracks.inputs["To Max"].default_value = 1.0
    l.new(vor.outputs["Distance"], cracks.inputs[0])

    blend = n.new("ShaderNodeMath")
    blend.operation = "MULTIPLY"
    l.new(noise.outputs["Fac"], blend.inputs[0])
    l.new(cracks.outputs[0], blend.inputs[1])

    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*rgb(hex_dark), 1.0)
    ramp.color_ramp.elements[1].color = (*rgb(hex_lit), 1.0)
    l.new(blend.outputs[0], ramp.inputs[0])
    l.new(ramp.outputs[0], bsdf.inputs["Base Color"])

    bmp = n.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = bump
    bmp.inputs["Distance"].default_value = 0.03
    l.new(blend.outputs[0], bmp.inputs["Height"])
    l.new(bmp.outputs[0], bsdf.inputs["Normal"])
    return m


class Stage:
    def __init__(self, scene):
        self.s = scene

    def obj(self, name, data=None, xyz=(0, 0, 0), parent=None):
        o = bpy.data.objects.new(name, data)
        self.s.collection.objects.link(o)
        o.location = xyz
        o.parent = parent
        return o

    def mesh(self, name, bm, m, xyz=(0, 0, 0), parent=None):
        d = bpy.data.meshes.new(name)
        bm.to_mesh(d)
        bm.free()
        d.update()
        if m:
            d.materials.append(m)
        return self.obj(name, d, xyz, parent)

    def box(self, name, xyz, dim, m, parent=None, bevel=0.02):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, verts=list(bm.verts), vec=dim)
        o = self.mesh(name, bm, m, xyz, parent)
        if bevel > 0:
            mod = o.modifiers.new("Bevel", "BEVEL")
            mod.width = bevel
            mod.segments = 2
        return o

    def ball(self, name, xyz, scale, m, parent=None):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
        o = self.mesh(name, bm, m, xyz, parent)
        o.scale = scale
        for p in o.data.polygons:
            p.use_smooth = True
        return o

    def rod(self, name, a, b, r1, r2, m, parent=None, segs=16):
        a, b = V(a), V(b)
        delta = b - a
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r1, radius2=r2, depth=max(0.002, delta.length))
        o = self.mesh(name, bm, m, (a + b) / 2.0, parent)
        o.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
        for p in o.data.polygons:
            p.use_smooth = True
        return o

    def curve(self, name, pts, r, m, parent=None, closed=False):
        d = bpy.data.curves.new(name, "CURVE")
        d.dimensions = "3D"
        d.bevel_depth = r
        d.bevel_resolution = 2
        d.resolution_u = 10
        sp = d.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for v, p in zip(sp.bezier_points, pts):
            v.co = p
            v.handle_left_type = v.handle_right_type = "AUTO"
        sp.use_cyclic_u = closed
        d.materials.append(m)
        return self.obj(name, d, parent=parent)

    def plane(self, name, w, h, m, xyz=(0, 0, 0), parent=None):
        d = bpy.data.meshes.new(name)
        d.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 1, 2, 3)])
        uv = d.uv_layers.new()
        for a, b in zip(uv.data, [(0, 0), (1, 0), (1, 1), (0, 1)]):
            a.uv = b
        d.materials.append(m)
        return self.obj(name, d, xyz, parent)

    def light(self, name, kind, xyz, target, energy, hex_col, angle_deg=10):
        d = bpy.data.lights.new(name, kind)
        d.energy = energy
        d.color = rgb(hex_col)
        o = self.obj(name, d, xyz)
        if kind != "POINT":
            o.rotation_euler = (V(target) - o.location).to_track_quat("-Z", "Y").to_euler()
        if kind == "SUN":
            d.angle = math.radians(angle_deg)
            d.use_shadow = True
        elif kind == "AREA":
            d.size = 4.5
            d.use_shadow = False
        elif kind == "POINT":
            d.shadow_soft_size = 0.25
            d.use_shadow = False
        return o


def solve_ik_2bone(a, b, l1, l2, pole):
    a, b = V(a), V(b)
    d = b - a
    dist = max(0.005, min(l1 + l2 - 0.002, d.length))
    axis = d.normalized() if d.length > 1e-5 else V((0, 0, -1))
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2.0 * dist)
    y = math.sqrt(max(0.0, l1 * l1 - x * x))
    p = V(pole) - axis * axis.dot(V(pole))
    if p.length < 1e-5:
        p = axis.cross(V((0, 1, 0)))
        if p.length < 1e-5:
            p = axis.cross(V((1, 0, 0)))
    return a + axis * x + p.normalized() * y


def set_bezier_3(curve_obj, pts, f):
    pts = [V(p) for p in pts]
    bps = curve_obj.data.splines[0].bezier_points
    for i, (bp, pos) in enumerate(zip(bps, pts)):
        tan = (pts[min(2, i + 1)] - pts[max(0, i - 1)]) * (0.28 if i == 1 else 0.30)
        bp.handle_left_type = bp.handle_right_type = "FREE"
        bp.co = pos
        bp.handle_left = pos - tan
        bp.handle_right = pos + tan
        for prop in ("co", "handle_left", "handle_right"):
            bp.keyframe_insert(prop, frame=f)


def build_world(s):
    """Bright 3-stop blue sky gradient (#0d47a1 -> #29b6f6 -> #e1f5fe)."""
    w = bpy.data.worlds.new("Sunny_Beach_Sky")
    w.use_nodes = True
    s.world = w
    n = w.node_tree.nodes
    l = w.node_tree.links
    bg = n.get("Background")
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Generated"], sep.inputs[0])

    mr = n.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.05
    mr.inputs["From Max"].default_value = 0.65
    l.new(sep.outputs["Z"], mr.inputs[0])

    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*rgb("e1f5fe"), 1.0)
    mid = ramp.color_ramp.elements.new(0.42)
    mid.color = (*rgb("29b6f6"), 1.0)
    ramp.color_ramp.elements[-1].position = 1.0
    ramp.color_ramp.elements[-1].color = (*rgb("0d47a1"), 1.0)
    l.new(mr.outputs[0], ramp.inputs[0])
    l.new(ramp.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.72


def build_beach_set(g):
    """Build 3D beach sand ground with recessed 0.85m x 1.95m x 0.65m coffin pit, cutaway front, tent, tree, ocean, clouds."""
    sand_top = sand_material("Sand_Top", "a88148", "cfa261", scale=5.5, bump=0.15)
    sand_wall = sand_material("Sand_Wall", "73542d", "966f3d", scale=7.0, bump=0.16)
    sand_floor = sand_material("Sand_Floor", "5c4221", "785930", scale=8.0, bump=0.15)
    cut_rim = mat("523a1c", rough=0.88)

    # Pit bounds: X in [-0.425, +0.425], Y in [-0.975, +0.975], Z_floor = -0.65
    # Left, Right, Back beach terrain slabs (extending deep below Z=0)
    g.box("Beach_Sand_Left", (-10.425, 0.0, -0.45), (20.0, 22.0, 0.90), sand_top, bevel=0.02)
    g.box("Beach_Sand_Right", (10.425, 0.0, -0.45), (20.0, 22.0, 0.90), sand_top, bevel=0.02)
    g.box("Beach_Sand_Back", (0.0, 5.975, -0.45), (0.85, 10.0, 0.90), sand_top, bevel=0.02)

    # Pit inner floor & walls (pit interior)
    g.box("Pit_Floor", (0.0, 0.0, -0.68), (0.87, 1.97, 0.06), sand_floor, bevel=0.01)
    g.box("Pit_Wall_Left", (-0.435, 0.0, -0.325), (0.02, 1.97, 0.65), sand_wall, bevel=0.008)
    g.box("Pit_Wall_Right", (0.435, 0.0, -0.325), (0.02, 1.97, 0.65), sand_wall, bevel=0.008)
    g.box("Pit_Wall_Back", (0.0, 0.985, -0.325), (0.87, 0.02, 0.65), sand_wall, bevel=0.008)

    # Front wall & front sand bank: Solid version (f=1..834) vs Cutaway X-ray version (f=835..935)
    front_solid = g.obj("Front_Sand_Solid")
    g.box("Beach_Sand_Front_Solid", (0.0, -5.975, -0.45), (0.85, 10.0, 0.90), sand_top, front_solid, bevel=0.02)
    g.box("Pit_Wall_Front_Solid", (0.0, -0.985, -0.325), (0.87, 0.02, 0.65), sand_wall, front_solid, bevel=0.008)

    front_cutaway = g.obj("Front_Sand_Cutaway")
    # In Cut 5B & 5C, front sand slab is completely cut away below Z=-0.03 so the camera sees cleanly above & below Z=0!
    g.box("Cutaway_Soil_Border_Left", (-0.44, -0.975, -0.34), (0.03, 0.03, 0.68), cut_rim, front_cutaway, bevel=0.005)
    g.box("Cutaway_Soil_Border_Right", (0.44, -0.975, -0.34), (0.03, 0.03, 0.68), cut_rim, front_cutaway, bevel=0.005)
    g.box("Cutaway_Soil_Border_Bottom", (0.0, -0.975, -0.67), (0.91, 0.03, 0.04), cut_rim, front_cutaway, bevel=0.005)
    g.box("Cutaway_Earth_Backing", (0.0, 4.0, -1.68), (40.0, 10.0, 2.0), sand_floor, front_cutaway, bevel=0)

    # Cracked-earth beveled sand berms around coffin pit perimeter (left/right/back stay always)
    berm_specs = [
        ((-0.49, -0.45, 0.03), (0.14, 0.85, 0.07)),
        ((-0.48, 0.48, 0.035), (0.13, 0.95, 0.08)),
        ((0.49, -0.40, 0.032), (0.14, 0.92, 0.075)),
        ((0.48, 0.52, 0.03), (0.13, 0.88, 0.07)),
        ((0.0, 1.05, 0.035), (0.96, 0.16, 0.08)),
    ]
    for idx, (pos, dim) in enumerate(berm_specs):
        g.box(f"Pit_Berm_{idx}", pos, dim, sand_top, bevel=0.03)
    front_berm = g.box("Pit_Berm_Front", (0.0, -1.05, 0.032), (0.96, 0.15, 0.07), sand_top, front_solid, bevel=0.03)

    # Camouflage sand cover slabs:
    # 1) Cut 2B cover_2b: slides over soldier's body (Y in [-0.18, +0.98]) + front chin apron (Y in [-0.98, -0.60]) so no dark chasm shows
    cover_2b = g.box("Sand_Cover_2B_Body", (0.0, 0.40, -0.014), (0.86, 1.16, 0.032), sand_top, bevel=0.012)
    cover_2b_apron = g.box("Sand_Cover_2B_Apron", (0.0, -0.79, -0.014), (0.86, 0.40, 0.032), sand_top, bevel=0.012)
    # 2) Full camouflage cover (Cuts 3A, 4A, 4B, 5A, 5B, 5C): flush with ground Z=0, 0.085m collar gap around bamboo at (0, -0.40)
    cover_full = g.obj("Sand_Cover_Full")
    g.box("Cover_Back", (0.0, 0.31, -0.015), (0.86, 1.33, 0.030), sand_top, cover_full, bevel=0.008)
    g.box("Cover_Front", (0.0, -0.71, -0.015), (0.86, 0.53, 0.030), sand_top, cover_full, bevel=0.008)
    g.box("Cover_Left", (-0.235, -0.40, -0.015), (0.39, 0.085, 0.030), sand_top, cover_full, bevel=0.006)
    g.box("Cover_Right", (0.235, -0.40, -0.015), (0.39, 0.085, 0.030), sand_top, cover_full, bevel=0.006)

    # Sand burst debris chunks for Cut 3B eruption
    sand_chunks = []
    for i in range(20):
        c = g.box(f"Sand_Burst_Chunk_{i}", (0, 0, -2), (0.09 + 0.03 * (i % 3), 0.08, 0.05), sand_wall, bevel=0.015)
        sand_chunks.append(c)

    # 3D Olive-Tan Military Beach Tent / Hut at X=-2.2, Y=+4.5
    tent = g.obj("Military_Beach_Tent", xyz=(-2.2, 4.5, 0.0))
    tent_wall = mat("7a7853", rough=0.85)
    tent_roof = mat("5c5a3b", rough=0.82)
    wood_pole = mat("6b4c30", rough=0.78)
    bag_mat = mat("9c8c68", rough=0.88)
    g.box("Tent_Base_Left", (-0.85, 0.0, 0.55), (0.12, 2.2, 1.1), tent_wall, tent, bevel=0.02)
    g.box("Tent_Base_Right", (0.85, 0.0, 0.55), (0.12, 2.2, 1.1), tent_wall, tent, bevel=0.02)
    g.box("Tent_Back_Wall", (0.0, 1.05, 0.72), (1.7, 0.12, 1.44), tent_wall, tent, bevel=0.02)
    g.box("Tent_Interior_Shadow", (0.0, 0.0, 0.55), (1.5, 1.9, 1.0), mat("232118", rough=0.95), tent, bevel=0)
    # Sloped tent roof panels
    for sx in (-1, 1):
        rp = g.box(f"Tent_Roof_{sx}", (sx * 0.48, 0.0, 1.32), (1.12, 2.4, 0.09), tent_roof, tent, bevel=0.02)
        rp.rotation_euler.y = sx * math.radians(32)
    g.rod("Tent_Ridge_Pole", (0, -1.25, 1.62), (0, 1.25, 1.62), 0.04, 0.04, wood_pole, tent)
    for sx in (-0.85, 0.85):
        for sy in (-1.08, 1.08):
            g.rod(f"Tent_Corner_Pole_{sx}_{sy}", (sx, sy, 0.0), (sx, sy, 1.08), 0.035, 0.035, wood_pole, tent)
    for k in range(5):
        g.ball(f"Tent_Sandbag_{k}", (-0.7 + k * 0.35, -1.12, 0.08), (0.20, 0.12, 0.09), bag_mat, tent)

    # Stylized Bare Branching Tree at X=+1.8, Y=+3.5
    tree = g.obj("Bare_Coastal_Tree", xyz=(1.8, 3.5, 0.0))
    bark = mat("5c432d", rough=0.88)
    g.rod("Tree_Trunk", (0, 0, 0), (-0.08, 0.05, 1.35), 0.11, 0.065, bark, tree)
    branches = [
        ((-0.07, 0.04, 1.25), (-0.65, -0.15, 2.05), 0.05, 0.018),
        ((-0.05, 0.03, 1.15), (0.58, -0.10, 1.92), 0.048, 0.016),
        ((-0.08, 0.05, 1.32), (0.10, 0.35, 2.25), 0.045, 0.015),
        ((-0.42, -0.06, 1.72), (-0.85, 0.10, 2.22), 0.025, 0.010),
        ((0.32, -0.05, 1.60), (0.78, 0.18, 2.10), 0.024, 0.010),
    ]
    for idx, (a, b, r1, r2) in enumerate(branches):
        g.rod(f"Tree_Branch_{idx}", a, b, r1, r2, bark, tree)

    # Turquoise Ocean Strip & Shoreline Foam (horizon Y=+10..28m)
    ocean_mat = mat("19a8bd", rough=0.22, em=0.14)
    foam_mat = mat("dbfaff", rough=0.35, em=0.25)
    g.box("Turquoise_Ocean", (0.0, 20.0, -0.14), (60.0, 20.0, 0.12), ocean_mat, bevel=0)
    g.box("Shoreline_Foam", (0.0, 10.1, -0.06), (55.0, 0.75, 0.06), foam_mat, bevel=0.02)

    # Fluffy White Clouds in the upper sky
    cloud_top = mat("ffffff", rough=0.8, em=0.55)
    cloud_pos = [
        (-4.5, 19.0, 5.2, 1.2),
        (-1.2, 21.0, 6.0, 1.4),
        (2.8, 18.5, 5.5, 1.1),
        (5.8, 22.0, 6.2, 1.3),
        (0.4, 23.0, 4.4, 0.9),
    ]
    for ci, (cx, cy, cz, sc) in enumerate(cloud_pos):
        cl = g.obj(f"Cloud_{ci}", xyz=(cx, cy, cz))
        for lx, ly, lz, lr in [(0, 0, 0, 0.65), (-0.55, 0.1, -0.1, 0.48), (0.55, 0.1, -0.08, 0.50), (0.15, -0.05, 0.25, 0.45)]:
            g.ball(f"Cloud_Lobe_{ci}_{lx}", (lx * sc, ly * sc, lz * sc), (lr * sc * 1.3, lr * sc * 0.7, lr * sc * 0.85), cloud_top, cl)

    return front_solid, front_cutaway, cover_2b, cover_2b_apron, cover_full, sand_chunks


def build_props(g):
    """Build 3D Green Bamboo Tube, 3D Assault Rifle with Bayonet, and 3D Frag Grenade."""
    # 1. 3D Green Bamboo Breathing Tube (origin at bottom tip, extends +0.82m along +Z)
    bamboo = g.obj("Bamboo_Breathing_Tube")
    bam_body = mat("6db33f", rough=0.52, em=0.10)
    bam_node = mat("3e6b22", rough=0.58, em=0.06)
    bam_bore = mat("14240b", rough=0.95, em=0.0)
    g.rod("Bamboo_Shaft", (0, 0, 0.0), (0, 0, 0.82), 0.038, 0.038, bam_body, bamboo, segs=20)
    for nz in (0.14, 0.28, 0.42, 0.56, 0.70, 0.80):
        g.ball(f"Bamboo_Node_{nz:.2f}", (0, 0, nz), (0.043, 0.043, 0.012), bam_node, bamboo)
    g.rod("Bamboo_Top_Bore", (0, 0, 0.795), (0, 0, 0.822), 0.025, 0.025, bam_bore, bamboo, segs=16)

    # 2. 3D Black Assault Rifle with Bayonet (origin near receiver grip)
    rifle = g.obj("Assault_Rifle_Bayonet")
    gunmetal = mat("232629", metal=0.45, rough=0.38)
    wood_stk = mat("6e4726", rough=0.65)
    bayonet_steel = mat("d8dee9", metal=0.85, rough=0.22)
    g.box("Rifle_Receiver", (0.0, 0.0, 0.0), (0.32, 0.045, 0.09), gunmetal, rifle, bevel=0.008)
    g.box("Rifle_Stock", (-0.28, 0.0, -0.02), (0.28, 0.04, 0.085), wood_stk, rifle, bevel=0.01)
    g.box("Rifle_Magazine", (0.06, 0.0, -0.10), (0.055, 0.032, 0.14), gunmetal, rifle, bevel=0.005)
    g.rod("Rifle_Barrel", (0.15, 0.0, 0.02), (0.56, 0.0, 0.02), 0.016, 0.014, gunmetal, rifle)
    g.box("Rifle_Handguard", (0.26, 0.0, 0.01), (0.20, 0.042, 0.055), wood_stk, rifle, bevel=0.008)
    g.box("Rifle_Bayonet_Blade", (0.64, 0.0, -0.015), (0.22, 0.008, 0.028), bayonet_steel, rifle, bevel=0.002)

    # 3. 3D Pineapple Frag Grenade (Cut 3C)
    grenade = g.obj("Pineapple_Frag_Grenade")
    olive_metal = mat("3f4a2c", metal=0.35, rough=0.45)
    dark_groove = mat("1e2415", metal=0.25, rough=0.6)
    silver_pin = mat("d8dee9", metal=0.85, rough=0.22)
    g.ball("Grenade_Body", (0, 0, 0), (0.052, 0.052, 0.068), olive_metal, grenade)
    for gz in (-0.032, 0.0, 0.032):
        g.ball(f"Grenade_Ring_{gz}", (0, 0, gz), (0.054, 0.054, 0.007), dark_groove, grenade)
    g.rod("Grenade_Fuse_Neck", (0, 0, 0.058), (0, 0, 0.088), 0.018, 0.018, olive_metal, grenade)
    g.box("Grenade_Spoon", (0.038, 0.0, 0.035), (0.012, 0.020, 0.09), olive_metal, grenade, bevel=0.003)
    g.curve(
        "Grenade_Pin_Ring",
        [(0.02 + 0.024 * math.cos(k * math.tau / 24), 0.0, 0.082 + 0.024 * math.sin(k * math.tau / 24)) for k in range(24)],
        0.004,
        silver_pin,
        grenade,
        closed=True,
    )

    return bamboo, rifle, grenade


class Actor:
    """2.5D Cel Character with independent camera-facing head pivot and curved 2-bone IK limbs."""

    def __init__(self, g, who, size=0.85):
        self.g = g
        self.who = who
        self.size = size
        self.root = g.obj(f"char_{who}_root")

        # Torso pivot
        self.body_pivot = g.obj(f"{who}_body_pivot", parent=self.root)
        self.torso = g.plane(
            f"{who}_torso_card",
            0.78 * size,
            0.94 * size,
            cel_mat(ART / f"{who}_torso.png"),
            parent=self.body_pivot,
        )

        # Independent camera-facing head pivot + grouped face parallax
        self.head = g.obj(f"{who}_head_pivot", parent=self.root)
        self.head.rotation_mode = "QUATERNION"
        self.head_card = g.plane(
            f"{who}_head_card",
            1.16 * size,
            1.16 * size,
            cel_mat(ART / f"{who}_head.png"),
            parent=self.head,
        )
        self.face_group = g.obj(f"{who}_face_parallax", xyz=(0, 0, 0.006 * size), parent=self.head)

        if who == "soldier":
            face_states = [
                "neutral_open",
                "neutral_blink",
                "pipe_o_open",
                "pipe_o_blink",
                "pipe_o_left",
                "pipe_o_right",
                "war_cry",
                "gag_in",
                "gag_out",
            ]
            sleeve_mat = mat("9c8468", rough=0.65, em=0.14)
            pant_mat = mat("6b533b", rough=0.72, em=0.10)
            pelvis_col = "6b533b"
            boot_col = "1c191b"
        else:
            face_states = [
                "patrol_open",
                "patrol_blink",
                "patrol_down",
                "terror_open",
                "grenade_mouth",
                "creepy_grin_1",
                "creepy_grin_2",
                "wild_squint_grin",
            ]
            sleeve_mat = mat("fdfaf2", rough=0.62, em=0.16)
            pant_mat = mat("283b54", rough=0.68, em=0.12)
            pelvis_col = "283b54"
            boot_col = "1a1719"

        self.faces = {}
        for st in face_states:
            self.faces[st] = g.plane(
                f"{who}_face_{st}",
                1.16 * size,
                1.16 * size,
                cel_mat(ART / f"{who}_face_{st}.png"),
                parent=self.face_group,
            )

        ink_m = mat("1a1214", rough=0.75, em=0.05)
        self.pelvis_ink = g.ball(f"{who}_pelvis_ink", (0, 0, 0), (0.23 * size, 0.10 * size, 0.13 * size), ink_m, self.root)
        self.pelvis_fill = g.ball(
            f"{who}_pelvis_fill", (0, 0, 0), (0.205 * size, 0.095 * size, 0.11 * size), mat(pelvis_col, rough=0.7, em=0.12), self.root
        )

        self.arms_ink = []
        self.arms_fill = []
        self.hands = []
        self.legs_ink = []
        self.legs_fill = []
        self.feet = []
        self.shadows = []

        for side in (-1, 1):
            self.arms_ink.append(g.curve(f"{who}_arm_ink_{side}", [(0, 0, 0)] * 3, 0.032 * size, ink_m, self.root))
            self.arms_fill.append(g.curve(f"{who}_arm_fill_{side}", [(0, 0, 0)] * 3, 0.022 * size, sleeve_mat, self.root))
            self.hands.append(g.ball(f"{who}_hand_{side}", (0, 0, 0), (0.052 * size, 0.042 * size, 0.052 * size), ink_m, self.root))

            self.legs_ink.append(g.curve(f"{who}_leg_ink_{side}", [(0, 0, 0)] * 3, 0.038 * size, ink_m, self.root))
            self.legs_fill.append(g.curve(f"{who}_leg_fill_{side}", [(0, 0, 0)] * 3, 0.026 * size, pant_mat, self.root))
            self.feet.append(g.ball(f"{who}_boot_{side}", (0, 0, 0), (0.068 * size, 0.115 * size, 0.046 * size), mat(boot_col, rough=0.55, em=0.06), self.root))
            self.shadows.append(g.ball(f"{who}_foot_shadow_{side}", (0, 0, 0), (0.11 * size, 0.14 * size, 0.004), alpha_mat(f"{who}_cshadow_{side}", "120e08", 0.34, em=0.0), self.root))

        # Temple sweat droplets attached to head billboard
        self.drops = [
            g.plane(
                f"{who}_sweat_{i}",
                0.11 * size,
                0.16 * size,
                cel_mat(ART / "sweat_drop.png", lit=False),
                parent=self.head,
            )
            for i in range(4)
        ]
        self.active_face = None

    def set_face(self, state, f):
        if self.active_face == state:
            return
        old = self.active_face
        self.active_face = state
        for st, ob in self.faces.items():
            if old is None or st in (old, state):
                ob.scale = (1.0, 1.0, 1.0) if st == state else (0.0001, 0.0001, 0.0001)
                key(ob, "scale", f)

    def set_visible(self, on, f):
        self.root.scale = (1.0, 1.0, 1.0) if on else (0.0001, 0.0001, 0.0001)
        key(self.root, "scale", f)

    def pose(self, hip, spine_dir, cam_rot, face_state, turn_x, feet_pos, hands_pos, leg_pole, arm_pole, f, sweat_mode=0, drop_shadow=True):
        sz = self.size
        hip = V(hip)
        axis = V(spine_dir).normalized()

        # Derive camera-facing torso basis aligned to spine axis
        cam_fwd = cam_rot @ V((0, 0, -1))
        to_cam = (-cam_fwd).normalized()
        right = axis.cross(to_cam)
        if right.length < 1e-4:
            right = cam_rot @ V((1, 0, 0))
        right.normalize()
        normal = right.cross(axis).normalized()
        torso_q = Matrix((right, axis, normal)).transposed().to_quaternion()

        self.body_pivot.location = hip + axis * (0.28 * sz)
        self.body_pivot.rotation_mode = "QUATERNION"
        self.body_pivot.rotation_quaternion = torso_q
        key(self.body_pivot, "location", f)
        key(self.body_pivot, "rotation_quaternion", f)

        # Head billboard strictly faces active camera
        head_pos = hip + axis * (0.88 * sz)
        self.head.location = head_pos
        self.head.rotation_quaternion = cam_rot
        key(self.head, "location", f)
        key(self.head, "rotation_quaternion", f)

        # Grouped face turn parallax inside 22% head radius
        self.face_group.location = (0.11 * sz * max(-1.0, min(1.0, turn_x)), 0.0, 0.008 * sz)
        key(self.face_group, "location", f)
        self.set_face(face_state, f)

        self.pelvis_ink.location = hip
        self.pelvis_ink.rotation_mode = "QUATERNION"
        self.pelvis_ink.rotation_quaternion = torso_q
        self.pelvis_fill.location = hip + normal * 0.006
        self.pelvis_fill.rotation_mode = "QUATERNION"
        self.pelvis_fill.rotation_quaternion = torso_q
        for ob in (self.pelvis_ink, self.pelvis_fill):
            key(ob, "location", f)
            key(ob, "rotation_quaternion", f)

        for i, s in enumerate((-1, 1)):
            shoulder = self.body_pivot.location + axis * (0.09 * sz) + right * (s * 0.19 * sz) - normal * (0.022 * sz)
            hand = V(hands_pos[i])
            elbow = solve_ik_2bone(shoulder, hand, 0.29 * sz, 0.29 * sz, right * s + V(arm_pole))
            set_bezier_3(self.arms_ink[i], [shoulder, elbow, hand], f)
            set_bezier_3(self.arms_fill[i], [shoulder + normal * 0.005, elbow + normal * 0.005, hand + normal * 0.005], f)
            self.hands[i].location = hand
            key(self.hands[i], "location", f)

            hip_j = hip + right * (s * 0.13 * sz) - axis * (0.04 * sz)
            foot = V(feet_pos[i])
            knee = solve_ik_2bone(hip_j, foot, 0.36 * sz, 0.36 * sz, V(leg_pole) + right * (s * 0.2))
            set_bezier_3(self.legs_ink[i], [hip_j, knee, foot], f)
            set_bezier_3(self.legs_fill[i], [hip_j + normal * 0.005, knee + normal * 0.005, foot + normal * 0.005], f)
            self.feet[i].location = foot
            key(self.feet[i], "location", f)

            sh_z = foot.z - 0.032 * sz
            self.shadows[i].location = (foot.x, foot.y, max(0.004, sh_z) if drop_shadow else -5.0)
            self.shadows[i].scale = (0.11 * sz, 0.14 * sz, 0.004) if drop_shadow else (0.0001, 0.0001, 0.0001)
            key(self.shadows[i], "location", f)
            key(self.shadows[i], "scale", f)

        for i, drop in enumerate(self.drops):
            if sweat_mode == 0:
                drop.scale = (0.0001, 0.0001, 0.0001)
                key(drop, "scale", f)
            else:
                sx = -1 if i % 2 == 0 else 1
                phase = ((f + i * 4) % 14) / 14.0
                dx = sx * (0.38 + 0.18 * phase) * sz
                dy = (0.12 - 0.24 * phase) * sz
                drop.location = (dx, dy, 0.015 * sz)
                sc = (0.7 + 0.4 * math.sin(phase * math.pi))
                drop.scale = (sc, sc, sc)
                key(drop, "location", f)
                key(drop, "scale", f)


def shot_camera(cut_id, u, f):
    """Return (cam_pos, target, lens, stop, focus_target) for each of the 12 cuts with 8-14% linear push."""
    if cut_id == "1A":
        p = lerp((-0.90, -1.80, 1.45), (-0.79, -1.60, 1.32), u)
        t = lerp((0.05, -0.05, -0.15), (0.0, -0.10, -0.35), u)
        return p, t, 32.0, 4.8, t
    if cut_id == "1B":
        # Direct overhead bird's-eye top-down shot looking straight down into coffin pit
        p = lerp((0.0, 0.0, 2.65), (0.0, 0.0, 3.00), u)
        t = V((0.0, 0.01, -0.42))
        return p, t, 32.0, 4.8, t
    if cut_id == "2A":
        p = lerp((0.10, -0.92, 0.56), (0.08, -0.82, 0.49), u)
        t = V((0.0, -0.46, -0.35))
        return p, t, 36.0, 4.8, V((0.0, -0.46, -0.36))
    if cut_id == "2B":
        p = lerp((0.0, -0.40, 2.25), (0.0, -0.40, 1.92), u)
        t = V((0.0, -0.15, -0.05))
        return p, t, 34.0, 4.8, V((0.0, -0.40, -0.15))
    if cut_id == "3A":
        p = lerp((-0.60, -1.90, 0.35), (-0.52, -1.70, 0.36), u)
        t = lerp((0.18, 0.40, 0.38), (0.12, 0.15, 0.40), u)
        return p, t, 32.0, 4.8, lerp((0.26, 0.45, 0.35), (0.15, 0.10, 0.35), u)
    if cut_id == "3B":
        p = lerp((-0.05, -2.75, 0.80), (-0.03, -2.45, 0.80), u)
        t = V((0.0, -0.06, 0.72))
        return p, t, 30.0, 6.0, V((0.0, -0.06, 0.75))
    if cut_id == "3C":
        p = lerp((0.15, -1.18, 1.36), (0.15, -1.06, 1.36), u)
        if 535 <= f <= 541:
            amp = 1.0 - (f - 535) / 6.0
            p += V((0.032 * amp * ((-1) ** f), 0.025 * amp, 0.028 * amp * ((-1) ** (f + 1))))
        t = V((0.20, 0.05, 1.24))
        return p, t, 46.0, 4.8, V((0.20, 0.05, 1.24))
    if cut_id == "4A":
        p = lerp((0.10, -2.02, 0.94), (0.10, -1.80, 0.98), u)
        t = V((0.06, -0.05, 0.98))
        return p, t, 32.0, 4.8, V((0.08, 0.0, 1.15))
    if cut_id == "4B":
        p = lerp((-0.35, -1.32, 0.85), (-0.31, -1.18, 0.79), u)
        t = V((0.0, -0.40, 0.28))
        return p, t, 35.0, 4.8, V((0.0, -0.40, 0.28))
    if cut_id == "5A":
        p = lerp((-1.05, -2.02, 0.86), (-0.93, -1.80, 0.84), u)
        t = V((0.0, -0.35, 0.74))
        return p, t, 34.0, 4.8, V((0.0, -0.40, 0.74))
    if cut_id == "5B":
        p = lerp((0.18, -1.90, -0.12), (0.16, -1.70, -0.14), u)
        t = V((0.0, -0.36, -0.36))
        return p, t, 34.0, 4.8, V((0.0, -0.38, -0.36))
    # Cut 5C: Vertical 9:16 X-Ray Cross-Section Split Shot (shows enemy on top + thin sand crust + soldier gagging below!)
    p = lerp((0.0, -3.25, 0.22), (0.0, -2.92, 0.20), u)
    t = V((0.0, -0.36, 0.26))
    return p, t, 26.0, 6.0, V((0.0, -0.36, 0.25))


def compose(s):
    s.use_nodes = True
    n = s.node_tree.nodes
    n.clear()
    l = s.node_tree.links

    rl = n.new("CompositorNodeRLayers")
    rl.scene = s

    gl = n.new("CompositorNodeGlare")
    gl.glare_type = "FOG_GLOW"
    gl.threshold = 0.94
    gl.mix = -0.84  # ~0.08 glow blend in Blender 4.2 [-1, 1] convention
    gl.size = 7
    gl.quality = "MEDIUM"
    l.new(rl.outputs["Image"], gl.inputs[0])

    sharp = n.new("CompositorNodeFilter")
    sharp.filter_type = "SHARPEN"
    sharp.inputs["Fac"].default_value = 0.15
    l.new(gl.outputs[0], sharp.inputs[1])

    # 0.59 corner vignette
    mask = n.new("CompositorNodeEllipseMask")
    mask.width = 0.85
    mask.height = 0.90
    blur = n.new("CompositorNodeBlur")
    blur.filter_type = "GAUSS"
    blur.size_x = 180
    blur.size_y = 280
    l.new(mask.outputs[0], blur.inputs[0])
    mp = n.new("CompositorNodeMapRange")
    mp.inputs["To Min"].default_value = 0.59
    mp.inputs["To Max"].default_value = 1.0
    l.new(blur.outputs[0], mp.inputs["Value"])
    vig = n.new("CompositorNodeMixRGB")
    vig.blend_type = "MULTIPLY"
    vig.inputs[0].default_value = 1.0
    l.new(sharp.outputs[0], vig.inputs[1])
    l.new(mp.outputs[0], vig.inputs[2])

    out = n.new("CompositorNodeComposite")
    l.new(vig.outputs[0], out.inputs[0])


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.name = "Bamboo_Ambush_Master"
    g = Stage(s)
    build_world(s)

    s.render.engine = "BLENDER_EEVEE_NEXT"
    s.eevee.use_raytracing = False
    s.eevee.taa_render_samples = 16
    if hasattr(s.eevee, "fast_gi_method"):
        s.eevee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
        s.eevee.fast_gi_distance = 0.45
    s.render.use_simplify = True
    s.render.simplify_subdivision = 2
    s.render.simplify_subdivision_render = 2
    s.render.resolution_x = 1080
    s.render.resolution_y = 1920
    s.render.resolution_percentage = 50
    s.render.fps = 30
    s.frame_start = 1
    s.frame_end = 935
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast"
    s.view_settings.exposure = -0.35

    compose(s)

    # Audio strip
    seq = s.sequence_editor_create()
    au = seq.sequences.new_sound("Master_Audio", str(OUT / "audio_master.wav"), channel=1, frame_start=1)
    au.sound.pack()

    # Lighting: Sunny warm key + sky/sand fill calibrated to ~100-115 target luma
    sun = g.light("Sunny_Key_Light", "SUN", (-3.5, -2.8, 7.2), (0, 0, 0), 3.8, "fff4d8", angle_deg=10)
    g.light("Sky_Cool_Fill", "AREA", (2.5, -3.5, 5.0), (0, 0, 0.5), 110.0, "d4eeff")
    g.light("Sand_Bounce_Fill", "AREA", (-1.5, -4.0, 2.2), (0, 0, 0.8), 70.0, "ffe5b4")
    pit_fill = g.light("Pit_Interior_Fill", "POINT", (0.0, -0.20, -0.22), (0, 0, -0.5), 38.0, "ffe8c2")

    # Set & props
    front_solid, front_cutaway, cover_2b, cover_2b_apron, cover_full, sand_chunks = build_beach_set(g)
    bamboo, rifle, grenade = build_props(g)

    # Vapor wisps above bamboo tube (Cut 2A)
    vapor_wisps = [
        g.plane(f"Bamboo_Vapor_{i}", 0.18, 0.18, cel_mat(ART / "vapor_wisp.png", lit=False)) for i in range(4)
    ]

    # Characters
    soldier = Actor(g, "soldier", size=0.82)
    enemy = Actor(g, "enemy", size=0.88)

    # Camera
    cam_data = bpy.data.cameras.new("Delivery_Camera")
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_height = 36.0
    cam_data.clip_start = 0.02
    cam_data.clip_end = 100.0
    cam_data.dof.use_dof = True
    cam = g.obj("Delivery_Camera", cam_data)
    s.camera = cam

    for cut_id, a, b, _ in CUTS:
        s.timeline_markers.new(f"Cut_{cut_id}", frame=a)

    # Bake animation across frames 1..935
    for cut_id, a, b, _ in CUTS:
        for f in range(a, b + 1):
            u = (f - a) / max(1, b - a)
            cam_pos, target, lens, fstop, focus_pt = shot_camera(cut_id, u, f)
            cam_rot = (target - cam_pos).to_track_quat("-Z", "Y")
            cam.location = cam_pos
            cam.rotation_mode = "QUATERNION"
            cam.rotation_quaternion = cam_rot
            cam_data.lens = lens
            cam_data.dof.aperture_fstop = fstop
            cam_fwd = cam_rot @ V((0, 0, -1))
            cam_data.dof.focus_distance = max(0.25, (focus_pt - cam_pos).dot(cam_fwd))
            key(cam, "location", f)
            key(cam, "rotation_quaternion", f)
            cam_data.keyframe_insert("lens", frame=f)
            cam_data.dof.keyframe_insert("aperture_fstop", frame=f)
            cam_data.dof.keyframe_insert("focus_distance", frame=f)

            # Set visibility toggles on cut boundaries
            if f == a:
                is_cutaway = cut_id in ("5B", "5C")
                for ob in [front_solid] + front_solid.children_recursive:
                    set_vis(ob, not is_cutaway, f)
                for ob in [front_cutaway] + front_cutaway.children_recursive:
                    set_vis(ob, is_cutaway, f)

                set_vis(cover_2b, cut_id == "2B", f)
                set_vis(cover_2b_apron, cut_id == "2B", f)
                full_on = cut_id in ("3A", "4A", "4B", "5A", "5B", "5C")
                for ob in [cover_full] + cover_full.children_recursive:
                    set_vis(ob, full_on, f)

                pit_fill.data.energy = 38.0 if cut_id in ("1A", "1B", "2A", "5B", "5C") else (22.0 if cut_id == "2B" else 0.0)
                pit_fill.data.keyframe_insert("energy", frame=f)

            # Slide Cut 2B cover over soldier's body across f=286..325 (home origin Y=0.40, Z=-0.014)
            if cut_id == "2B":
                slide_t = ease((f - 286) / 39.0)
                cover_2b.location = (0.0, 0.40 + 1.45 * (1.0 - slide_t), -0.014)
                key(cover_2b, "location", f)

            # Burst sand chunks in Cut 3B (f=460..528)
            if cut_id == "3B" or f in (1, 529):
                for ci, ch in enumerate(sand_chunks):
                    if cut_id != "3B":
                        ch.scale = (0.0001, 0.0001, 0.0001)
                        key(ch, "scale", f)
                    else:
                        t_b = max(0.0, (f - 461) / 32.0)
                        ang = ci * math.tau / 20.0
                        rad = 0.25 + 1.15 * ease_out(t_b)
                        z_arc = 0.05 + 1.25 * math.sin(min(1.0, t_b) * math.pi) - 0.35 * t_b
                        ch.location = (rad * math.cos(ang), -0.15 + rad * 0.7 * math.sin(ang), max(-0.5, z_arc))
                        sc = 1.0 if 461 <= f <= 496 else 0.0001
                        ch.scale = (sc, sc, sc)
                        ch.rotation_euler = (f * 0.15 + ci, f * 0.12, ci)
                        key(ch, "location", f)
                        key(ch, "scale", f)
                        key(ch, "rotation_euler", f)

            # --- Bamboo tube transform ---
            bam_on = cut_id in ("2A", "2B", "3A", "4A", "4B", "5A", "5B", "5C")
            if f == a or cut_id in ("5A", "5B", "5C"):
                for ob in [bamboo] + bamboo.children_recursive:
                    set_vis(ob, bam_on, f)
            if bam_on:
                if cut_id == "2A":
                    # Held directly in soldier's O mouth at (0, -0.55, -0.39)
                    bamboo.location = (0.0, -0.55, -0.39)
                    bamboo.rotation_euler = (math.radians(-16), 0.0, 0.0)
                elif cut_id in ("2B", "3A", "4A", "4B"):
                    # Sticks 0.38m out of sand at (0, -0.40) matching cover collar gap
                    bamboo.location = (0.0, -0.40, -0.44)
                    bamboo.rotation_euler = (0.0, 0.0, 0.0)
                else:
                    # Cuts 5A, 5B, 5C: pistons every 5 frames right into soldier's underground O-mouth!
                    phase = ((f - 769) % 5) / 5.0
                    pump = 0.5 - 0.5 * math.cos(phase * math.tau)
                    bamboo.location = (0.0, -0.40, -0.43 - 0.10 * pump)
                    bamboo.rotation_euler = (0.05 * pump, 0.0, 0.0)
                key(bamboo, "location", f)
                key(bamboo, "rotation_euler", f)

            # Vapor wisps in Cut 2A
            for vi, vw in enumerate(vapor_wisps):
                if cut_id == "2A":
                    vt = ((f - 190 + vi * 11) % 44) / 44.0
                    vw.location = (0.04 * math.sin(vt * 6 + vi), -0.62, 0.32 + 0.26 * vt)
                    vw.rotation_mode = "QUATERNION"
                    vw.rotation_quaternion = cam_rot
                    sc = 0.9 * math.sin(vt * math.pi)
                    vw.scale = (sc, sc, sc)
                    key(vw, "location", f)
                    key(vw, "rotation_quaternion", f)
                    key(vw, "scale", f)
                elif f == a:
                    vw.scale = (0.0001, 0.0001, 0.0001)
                    key(vw, "scale", f)

            # --- Soldier acting & visibility ---
            sol_on = cut_id in ("1A", "1B", "2A", "2B", "3B", "3C", "5B", "5C")
            if f == a:
                soldier.set_visible(sol_on, f)
            if sol_on:
                blink = (f % 75) in (36, 37, 38)
                if cut_id == "1A":
                    # f=1..20 crouch/step on pit edge -> f=20..44 lie back into coffin pit -> f=45..90 settle
                    if f < 22:
                        t_step = ease((f - 1) / 21.0)
                        hip = lerp((0.15, -0.20, 0.25), (0.0, 0.14, -0.40), t_step)
                        spine = lerp((0.0, 0.25, 0.96), (0.0, 0.72, 0.69), t_step)
                        f_pos = [(-0.18, 0.15, 0.02) if t_step < 0.4 else (-0.15, 0.72, -0.56), (0.18, 0.20, 0.02) if t_step < 0.4 else (0.15, 0.72, -0.56)]
                        h_pos = [hip + V((-0.24, -0.10, 0.18)), hip + V((0.24, -0.10, 0.18))]
                    else:
                        t_lie = ease((f - 22) / 22.0)
                        hip = lerp((0.0, 0.14, -0.40), (0.0, 0.30, -0.52), t_lie)
                        spine = lerp((0.0, 0.72, 0.69), (0.0, -0.96, 0.26), t_lie)
                        f_pos = [(-0.15, 0.82, -0.56), (0.15, 0.82, -0.56)]
                        h_pos = [(hip.x - 0.18, hip.y - 0.18, -0.34), (hip.x + 0.18, hip.y - 0.24, -0.34)]
                    st = "neutral_blink" if blink else "neutral_open"
                    soldier.pose(hip, spine, cam_rot, st, 0.0, f_pos, h_pos, (0, -0.3, 0.8), (0, 0, 0.4), f, drop_shadow=False)

                elif cut_id == "1B":
                    # Lying on back inside coffin pit, slight grip shift
                    grip_bob = 0.018 * math.sin((f - 91) * math.tau / 40.0)
                    hip = V((0.0, 0.30, -0.52))
                    spine = V((0.0, -0.98, 0.18))
                    f_pos = [(-0.15, 0.82, -0.56), (0.15, 0.82, -0.56)]
                    h_pos = [(-0.18, 0.12 + grip_bob, -0.34), (0.18, 0.05 + grip_bob, -0.34)]
                    st = "neutral_blink" if blink else "neutral_open"
                    soldier.pose(hip, spine, cam_rot, st, 0.0, f_pos, h_pos, (0, -0.2, 1.0), (0, 0, 0.5), f, drop_shadow=False)

                elif cut_id == "2A":
                    # Macro close-up inside pit, holding bamboo tube in O-mouth + subtle chest breath
                    breath = 0.010 * math.sin((f - 190) * math.tau / 36.0)
                    hip = V((0.0, 0.30, -0.52 + breath * 0.5))
                    spine = V((0.0, -0.97, 0.24))
                    f_pos = [(-0.15, 0.82, -0.56), (0.15, 0.82, -0.56)]
                    h_pos = [(-0.09, -0.51, -0.22), (0.09, -0.50, -0.14)]
                    st = "pipe_o_blink" if blink else "pipe_o_open"
                    soldier.pose(hip, spine, cam_rot, st, 0.0, f_pos, h_pos, (0, -0.2, 1.0), (0, -0.2, 0.6), f, drop_shadow=False)

                elif cut_id == "2B":
                    # Buried under sand cover, mouth aligned at Y=-0.40 under bamboo while eyes dart left/right
                    hip = V((0.0, 0.42, -0.52))
                    spine = V((0.0, -0.95, 0.30))
                    f_pos = [(-0.15, 0.90, -0.56), (0.15, 0.90, -0.56)]
                    h_pos = [(-0.22, 0.15, -0.45), (0.22, 0.15, -0.45)]
                    cycle = ((f - 286) // 24) % 3
                    st = "pipe_o_left" if cycle == 1 else ("pipe_o_right" if cycle == 2 else "pipe_o_open")
                    turn = -0.35 if cycle == 1 else (0.35 if cycle == 2 else 0.0)
                    soldier.pose(hip, spine, cam_rot, st, turn, f_pos, h_pos, (0, -0.2, 1.0), (0, 0, 0.5), f, drop_shadow=False)

                elif cut_id == "3B":
                    # Erupts onto left sand rim (f=460..476), feet solidly grounded, bayonet aimed between characters
                    pop_t = ease_out((f - 460) / 16.0)
                    hip = lerp((-0.44, -0.12, -0.25), (-0.52, -0.12, 0.58), pop_t)
                    spine = V((0.04, 0.05, 1.0))
                    f_pos = [(-0.64, -0.12, 0.04), (-0.42, -0.12, 0.04)]
                    h_pos = [hip + V((-0.04, -0.12, 0.30)), hip + V((0.24, -0.16, 0.28))]
                    soldier.pose(hip, spine, cam_rot, "war_cry", 0.22, f_pos, h_pos, (0, -1, 0), (0, -0.4, -0.3), f, drop_shadow=(pop_t > 0.75))

                elif cut_id == "3C":
                    # Soldier positioned off-screen left-front, thrusting right arm to shove grenade into enemy's mouth
                    thrust = ease_out((f - 529) / 6.0)
                    hip = V((-0.38, -0.30, 0.62))
                    spine = V((0.1, 0.1, 1.0))
                    f_pos = [(-0.52, -0.30, 0.04), (-0.24, -0.30, 0.04)]
                    g_hand = lerp((-0.18, -0.25, 1.08), (0.19, -0.04, 1.16), thrust)
                    h_pos = [hip + V((-0.25, 0.0, 0.10)), g_hand]
                    soldier.pose(hip, spine, cam_rot, "war_cry", 0.3, f_pos, h_pos, (0, -1, 0), (0, -0.5, -0.2), f, drop_shadow=False)

                elif cut_id in ("5B", "5C"):
                    # Underground cutaway pit: lowered nicely inside cutaway floor with clear headroom below sand roof!
                    phase = ((f - 769) % 5) / 5.0
                    pump = 0.5 - 0.5 * math.cos(phase * math.tau)
                    hip = V((0.0, 0.26, -0.58))
                    spine = V((0.0, -0.90, 0.43))
                    flail = 0.08 * math.sin(f * 0.9)
                    f_pos = [(-0.18, 0.78, -0.56 + 0.04 * pump), (0.18, 0.78, -0.56 + 0.04 * (1 - pump))]
                    h_pos = [(-0.32, -0.16 + flail, -0.34 + 0.09 * pump), (0.32, -0.16 - flail, -0.34 + 0.09 * (1 - pump))]
                    st = "gag_out" if pump > 0.45 else "gag_in"
                    soldier.pose(hip, spine, cam_rot, st, 0.0, f_pos, h_pos, (0, -0.3, 1.0), (0, -0.2, 0.5), f, sweat_mode=1, drop_shadow=False)

            # --- Rifle prop attachment (Cuts 1A, 1B, 3B) ---
            rifle_on = (cut_id == "1A" and f >= 34) or cut_id in ("1B", "3B")
            if f == a or cut_id == "1A":
                for ob in [rifle] + rifle.children_recursive:
                    set_vis(ob, rifle_on, f)
            if rifle_on:
                if cut_id in ("1A", "1B"):
                    # Rests horizontally across soldier's chest (clear of head/face)
                    rifle.location = (0.0, 0.05, -0.36)
                    rifle.rotation_euler = (0.0, 0.0, math.radians(-10))
                else:
                    # Cut 3B: aimed toward enemy cleanly in gap
                    pop_t = ease_out((f - 460) / 16.0)
                    rifle.location = lerp((-0.34, -0.24, 0.05), (-0.34, -0.24, 0.85), pop_t)
                    rifle.rotation_euler = (0.0, math.radians(-6), math.radians(12))
                key(rifle, "location", f)
                key(rifle, "rotation_euler", f)

            # --- Grenade prop attachment (Cut 3C) ---
            gren_on = cut_id == "3C"
            if f == a:
                for ob in [grenade] + grenade.children_recursive:
                    set_vis(ob, gren_on, f)
            if gren_on:
                thrust = ease_out((f - 529) / 6.0)
                grenade.location = lerp((-0.14, -0.22, 1.08), (0.20, -0.03, 1.19), thrust)
                grenade.rotation_euler = (math.radians(15), math.radians(-20), math.radians(10))
                key(grenade, "location", f)
                key(grenade, "rotation_euler", f)

            # --- Enemy #17 acting & visibility ---
            en_on = cut_id in ("3A", "3B", "3C", "4A", "4B", "5A", "5C")
            if f == a:
                enemy.set_visible(en_on, f)
            if en_on:
                blink = (f % 83) in (40, 41, 42)
                if cut_id == "3A":
                    # 4-frame-phase brisk walk across sand toward buried trench
                    wt = (f - 405) / max(1, 459 - 405)
                    ex = lerp((0.40, 1.15, 0.62), (0.12, -0.10, 0.62), wt).x
                    ey = lerp((0.40, 1.15, 0.62), (0.12, -0.10, 0.62), wt).y
                    stride_phase = ((f - 405) % 16) / 16.0
                    bob = 0.035 * abs(math.sin(stride_phase * math.tau))
                    hip = V((ex, ey, 0.62 + bob))
                    l_lift = max(0.0, math.sin(stride_phase * math.tau)) * 0.14
                    r_lift = max(0.0, -math.sin(stride_phase * math.tau)) * 0.14
                    l_dy = 0.24 * math.cos(stride_phase * math.tau)
                    r_dy = -0.24 * math.cos(stride_phase * math.tau)
                    f_pos = [(ex - 0.14, ey + l_dy, 0.04 + l_lift), (ex + 0.14, ey + r_dy, 0.04 + r_lift)]
                    h_pos = [(ex - 0.28, ey - l_dy * 0.8, 0.65), (ex + 0.28, ey - r_dy * 0.8, 0.65)]
                    st = "patrol_blink" if blink else "patrol_open"
                    enemy.pose(hip, (0, 0, 1), cam_rot, st, -0.1, f_pos, h_pos, (0, -1, 0), (0, 0.3, -0.4), f)

                elif cut_id == "3B":
                    # Freezes in terror with both hands raised beside bald head!
                    jolt = ease_out((f - 462) / 10.0)
                    ex, ey = 0.46, -0.02
                    hip = V((ex, ey, 0.62 + 0.04 * math.sin(jolt * math.pi)))
                    f_pos = [(ex - 0.12, ey, 0.04), (ex + 0.12, ey, 0.04)]
                    h_pos = [(ex - 0.32, ey - 0.06, 1.38), (ex + 0.32, ey - 0.06, 1.38)]
                    enemy.pose(hip, (0.04, 0, 1), cam_rot, "terror_open", -0.22, f_pos, h_pos, (0, -1, 0), (0, -0.2, -0.4), f, sweat_mode=1)

                elif cut_id == "3C":
                    # Extreme front close-up: grenade shoved into wide open mouth!
                    hip = V((0.20, 0.05, 0.62))
                    f_pos = [(0.04, 0.05, 0.04), (0.36, 0.05, 0.04)]
                    h_pos = [(-0.14, 0.0, 1.10), (0.54, 0.0, 1.10)]
                    enemy.pose(hip, (0, 0, 1), cam_rot, "grenade_mouth", 0.0, f_pos, h_pos, (0, -1, 0), (0, -0.2, -0.5), f, sweat_mode=1)

                elif cut_id == "4A":
                    # Stops, looks down at bamboo pipe (591..635), then transitions into creepy grin (636..696)
                    hip = V((0.08, 0.02, 0.62))
                    f_pos = [(-0.08, 0.02, 0.04), (0.24, 0.02, 0.04)]
                    h_pos = [(-0.24, -0.04, 0.56), (0.40, -0.04, 0.56)]
                    if f < 636:
                        st = "patrol_down"
                        turn = -0.20
                    elif f < 660:
                        st = "creepy_grin_1"
                        turn = -0.10
                    else:
                        st = "creepy_grin_2"
                        turn = 0.0
                    enemy.pose(hip, (0, 0, 1), cam_rot, st, turn, f_pos, h_pos, (0, -1, 0), (0, 0.2, -0.5), f)

                elif cut_id == "4B":
                    # Steps up straddling bamboo pipe at (0, -0.40) and bends knees in anticipation
                    step_t = ease((f - 697) / 28.0)
                    crouch_t = ease((f - 730) / 30.0)
                    hip = lerp((0.06, 0.02, 0.62), (0.0, -0.34, 0.62 - 0.14 * crouch_t), step_t)
                    f_pos = [(-0.20, -0.40, 0.04), (0.20, -0.40, 0.04)]
                    h_pos = [(hip.x - 0.26, hip.y, hip.z + 0.06), (hip.x + 0.26, hip.y, hip.z + 0.06)]
                    enemy.pose(hip, (0, -0.15 * crouch_t, 1), cam_rot, "creepy_grin_2", 0.0, f_pos, h_pos, (0, -1, 0), (0, 0.3, -0.3), f)

                else:
                    # Cuts 5A & 5C: Rhythmically belly-humps the vertical bamboo pipe every 5 frames!
                    phase = ((f - 769) % 5) / 5.0
                    pump = 0.5 - 0.5 * math.cos(phase * math.tau)
                    hip = V((0.0, -0.28 - 0.12 * pump, 0.48 - 0.10 * pump))
                    spine = V((0.0, -0.18 - 0.14 * pump, 1.0))
                    f_pos = [(-0.22, -0.40, 0.04), (0.22, -0.40, 0.04)]
                    # Hands on hips
                    h_pos = [(hip.x - 0.22, hip.y, hip.z + 0.06), (hip.x + 0.22, hip.y, hip.z + 0.06)]
                    enemy.pose(hip, spine, cam_rot, "wild_squint_grin", 0.0, f_pos, h_pos, (0, -1, 0), (0, 0.4, -0.2), f)

    # Set CONSTANT interpolation at cut ends & discrete swaps, LINEAR inside pushes
    cut_ends = {b for _, _, b, _ in CUTS}
    for ob in list(s.objects) + [cam_data, pit_fill.data]:
        ad = ob.animation_data
        if not ad or not ad.action:
            continue
        is_swap = "_face_" in ob.name or ob in (soldier.root, enemy.root)
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kf = round(kp.co.x)
                if is_swap or fc.data_path.startswith("hide_") or (kf in cut_ends and kf < 935):
                    kp.interpolation = "CONSTANT"
                else:
                    kp.interpolation = "LINEAR"

    s.frame_set(45)
    blend_path = globals().get('BLEND_PATH', OUT / "bamboo_ambush.blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"Saved Blender scene: {blend_path}", flush=True)


if __name__ == "__main__":
    main()
