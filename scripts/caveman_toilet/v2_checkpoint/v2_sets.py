"""caveman_toilet v2 sets: A savanna, B cave, C valley + lights + sky."""
import math
import random

import bpy
from mathutils import Vector

from v2_common import (ROOT, OUT, SPR, mat_world, mat_ground, cel_mat,
                       add_card, sphere, smooth_rock, empty, noise_mod, log)
from v2_story import FIRE, CORNER, SQUAT_SPOT, ARCH


def _plane(name, loc, sx, sy, mat, parent, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    p = bpy.context.active_object
    p.name = name
    p.rotation_euler = rot
    p.scale = (sx, sy, 1)
    p.data.materials.append(mat)
    p.parent = parent
    return p


def _cone(name, loc, r, h, mat, parent, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0.0, depth=h, location=loc)
    c = bpy.context.active_object
    c.name = name
    c.rotation_euler = rot
    c.data.materials.append(mat)
    c.parent = parent
    return c


def build_set_A():
    random.seed(11)
    A = empty("set_A")
    grassm = mat_ground("savanna_grass", (0.42, 0.42, 0.16), (0.55, 0.50, 0.22), scale=5)
    _plane("savanna_ground", (0, 4, 0), 40, 40, grassm, A)
    # rolling multi-tier midground hills
    hillm = mat_ground("hill", (0.30, 0.38, 0.16), (0.42, 0.46, 0.22), scale=3)
    for i, (y, r, h) in enumerate([(8, 7, 1.4), (12, 9, 2.2), (16, 12, 3.0)]):
        for j, x in enumerate((-6, 2, 9)):
            sphere(f"hill_{i}_{j}", (x + j * 2, y, h * 0.3), r, hillm,
                   scale=(1, 0.6, h / r), parent=A)
    # clustered irregular rock outcrops (varied scale + rotation)
    rockm = mat_ground("sandstone", (0.42, 0.30, 0.19), (0.55, 0.41, 0.26), scale=9, rough=0.8)
    clusters = [(-3.2, 2.5), (3.4, 3.2), (-2.0, 5.5), (2.2, 6.5), (0.5, 3.8)]
    for ci, (cx, cy) in enumerate(clusters):
        n = random.randint(2, 4)
        for k in range(n):
            x = cx + random.uniform(-0.8, 0.8)
            y = cy + random.uniform(-0.6, 0.6)
            r = random.uniform(0.25, 0.6)
            smooth_rock(f"outcrop_{ci}_{k}", (x, y, r * 0.4), r, rockm,
                        scale=(random.uniform(0.8, 1.4), random.uniform(0.8, 1.2), 0.7),
                        parent=A, rot=(0, 0, random.uniform(0, 3.14)))
    # tall swaying grass clusters (NOISE on cluster empty)
    blademat = mat_world("grass_blade", (0.36, 0.48, 0.16), 0.7)
    for ci in range(8):
        cx = random.uniform(-4, 4)
        cy = random.uniform(0.5, 7)
        piv = empty(f"grassclust_{ci}", parent=A)
        piv.location = (cx, cy, 0)
        for k in range(random.randint(3, 5)):
            h = random.uniform(0.3, 0.6)
            _cone(f"grass_{ci}_{k}", (random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), h / 2),
                  0.035, h, blademat, piv,
                  rot=(random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), 0))
        noise_mod(piv, "rotation_euler", 2, scale=7, strength=0.05, phase=ci * 3.1)
    # hide-rock cluster + tall grass at the squat spot
    smooth_rock("hide_rock_main", (0.15, 1.05, 0.22), 0.45, rockm, scale=(1.2, 1.0, 0.8), parent=A)
    smooth_rock("hide_rock_2", (0.85, 1.5, 0.15), 0.30, rockm, scale=(1.0, 0.9, 0.75), parent=A)
    for i, (gx, gy) in enumerate([(0.35, 0.95), (0.8, 1.2), (0.05, 1.5)]):
        piv = empty(f"hidegrass_{i}", parent=A)
        piv.location = (gx, gy, 0)
        for k in range(4):
            _cone(f"hidegrass_{i}_{k}", (random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), 0.25),
                  0.03, 0.5, blademat, piv)
        noise_mod(piv, "rotation_euler", 2, scale=6, strength=0.06, phase=i * 2.0)
    # curved-trunk layered-canopy acacias
    trunkm = mat_world("acacia_trunk", (0.35, 0.25, 0.15), 0.8)
    canopym = mat_world("acacia_canopy", (0.30, 0.42, 0.18), 0.8)
    for i, (x, y) in enumerate([(-3, 5), (3.2, 6), (0.5, 7)]):
        cu = bpy.data.curves.new(f"trunk_{i}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.07
        cu.bevel_resolution = 4
        cu.use_fill_caps = True
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        for j, p in enumerate([(x, y, 0), (x + 0.18, y, 0.8), (x - 0.06, y, 1.5)]):
            bp = sp.bezier_points[j]
            bp.co = Vector(p)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        t = bpy.data.objects.new(f"trunk_{i}", cu)
        bpy.context.collection.objects.link(t)
        t.data.materials.append(trunkm)
        t.parent = A
        for k, (dz, sx) in enumerate([(1.65, 1.6), (1.85, 1.1)]):
            sphere(f"canopy_{i}_{k}", (x - 0.06, y, dz), 0.6, canopym, scale=(sx, sx, 0.35), parent=A)
    # clouds high (z 7-9) so they never sit behind a head
    cloudmat = cel_mat("cloud_matA", SPR / "fx_cloud.png", emit=1.0)
    for i, (x, y, z, s) in enumerate([(-4, 15, 7.5, 3.0), (3, 17, 8.5, 3.6),
                                      (0, 19, 7.0, 2.6), (6, 15, 8.0, 2.8)]):
        add_card(f"cloudA_{i}", SPR / "fx_cloud.png", s, s * 0.5, (x, y, z),
                 parent=A, mat=cloudmat)
    return A


def build_fg_silhouettes(cam):
    """Dark out-of-focus foreground rocks/grass at bottom screen edges,
    parented to the camera (savanna cuts only)."""
    fg = empty("fg_savanna", parent=cam)
    dark = mat_world("fg_dark", (0.03, 0.05, 0.02), 0.95)
    for side in (-1, 1):
        smooth_rock(f"fg_rock_{side}", (side * 1.05, -0.78, -1.15), 0.42, dark,
                    scale=(1.1, 0.8, 0.9), parent=fg)
        for k in range(3):
            _cone(f"fg_grass_{side}_{k}", (side * (0.85 + 0.12 * k), -0.85, -1.05),
                  0.05, 0.55, dark, fg, rot=(0.1 * side, 0, 0.2 * k))
    return fg


def build_set_B():
    random.seed(23)
    B = empty("set_B")
    rockm = mat_ground("cave_rock", (0.17, 0.15, 0.14), (0.26, 0.22, 0.19), scale=7, rough=0.85)
    darkm = mat_ground("cave_dark", (0.10, 0.09, 0.09), (0.16, 0.14, 0.13), scale=6, rough=0.9)
    _plane("cave_floor", (0, 1.5, 0), 9, 8, rockm, B)
    # back wall with a REAL rectangular arch opening (x -2.9..-1.5, z 0..2.2)
    _plane("cave_back_L", (-3.7, 4.5, 2), 1.6, 4, rockm, B, rot=(math.radians(90), 0, 0))
    _plane("cave_back_R", (1.5, 4.5, 2), 6.0, 4, rockm, B, rot=(math.radians(90), 0, 0))
    _plane("cave_back_top", (-2.2, 4.5, 3.1), 1.4, 1.8, rockm, B, rot=(math.radians(90), 0, 0))
    _plane("cave_left", (-4.5, 1.5, 2), 8, 6, darkm, B, rot=(0, math.radians(90), 0))
    _plane("cave_right", (4.5, 1.5, 2), 8, 6, darkm, B, rot=(0, math.radians(90), 0))
    _plane("cave_ceil", (0, 1.5, 4), 9, 8, darkm, B)
    # stone arch rim: semicircle curve + jambs
    arcm = mat_world("arch_stone", (0.30, 0.26, 0.22), 0.85)
    cu = bpy.data.curves.new("arch_rim", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.12
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    pts = [(ARCH[0] + 0.7 * math.cos(math.pi * i / 12), 4.42,
            1.5 + 0.7 * math.sin(math.pi * i / 12)) for i in range(13)]
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1)
    sp.order_u = 3
    sp.use_endpoint_u = True
    arc = bpy.data.objects.new("arch_rim", cu)
    bpy.context.collection.objects.link(arc)
    arc.data.materials.append(arcm)
    arc.parent = B
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.12, depth=1.5,
                                            location=(ARCH[0] + sx * 0.7, 4.42, 0.75))
        j = bpy.context.active_object
        j.name = f"arch_jamb_{sx}"
        j.data.materials.append(arcm)
        j.parent = B
    # night canyon backdrop seen through the arch
    nightm = mat_world("night_canyon", (0.02, 0.03, 0.06), 0.95, emit=0.25,
                       emit_color=(0.03, 0.05, 0.10))
    _plane("canyon_back", (-2.2, 12, 3), 16, 8, nightm, B, rot=(math.radians(90), 0, 0))
    spirem = mat_world("spire", (0.015, 0.02, 0.04), 0.95)
    for i, (x, h) in enumerate([(-4.5, 3.5), (-2.8, 5.0), (-1.0, 4.2), (0.8, 3.0)]):
        _cone(f"spire_{i}", (x, 10.5, h / 2), 0.8, h, spirem, B)
    # dark foreground rock pillars framing left/right
    for sx in (-1, 1):
        smooth_rock(f"fg_pillar_{sx}", (sx * 1.5, -0.6, 1.4), 0.5, darkm,
                    scale=(1, 1, 3.0), parent=B, rot=(0, 0, sx * 0.3))
    # varied stalagmites along the walls
    for i in range(8):
        x = random.choice([-3.8, 3.8]) + random.uniform(-0.4, 0.4)
        y = random.uniform(0.5, 4.0)
        h = random.uniform(0.4, 1.3)
        _cone(f"stalag_{i}", (x, y, h / 2), random.uniform(0.12, 0.3), h, rockm, B,
              rot=(random.uniform(-0.08, 0.08), random.uniform(-0.08, 0.08), 0))
    # campfire ring at FIRE
    stone = mat_ground("firestone", (0.13, 0.11, 0.10), (0.20, 0.17, 0.14), scale=8)
    for i in range(8):
        a = 2 * math.pi * i / 8
        smooth_rock(f"firestone_{i}", (FIRE[0] + 0.42 * math.cos(a), FIRE[1] + 0.42 * math.sin(a), 0.06),
                    0.09, stone, scale=(1, 1, 0.8), parent=B)
    logm = mat_world("log", (0.22, 0.12, 0.07), 0.85, emit=0.25, emit_color=(0.9, 0.25, 0.05))
    for i in range(3):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.055, depth=0.62,
                                            location=(FIRE[0], FIRE[1], 0.10),
                                            rotation=(math.radians(75), 0, i * 2.094))
        l = bpy.context.active_object
        l.name = f"log_{i}"
        l.data.materials.append(logm)
        l.parent = B
    flamem = mat_world("flame", (0.0, 0.0, 0.0), 0.5, emit=0.7, emit_color=(1.0, 0.28, 0.03))
    flames = []
    for i, (dx, dy, h, r) in enumerate([(-0.12, 0.04, 0.38, 0.10), (0.0, -0.03, 0.55, 0.13),
                                        (0.12, 0.05, 0.42, 0.10)]):
        f = _cone(f"flame_{i}", (FIRE[0] + dx, FIRE[1] + dy, 0.16 + h / 2), r, h, flamem, B)
        noise_mod(f, "scale", 2, scale=9, strength=0.18, phase=i * 2.3)
        flames.append(f)
    # toxic poop corner dirt patch
    soilm = mat_ground("corner_soil", (0.22, 0.18, 0.10), (0.30, 0.24, 0.14), scale=9)
    _plane("corner_patch", (CORNER[0], CORNER[1], 0.005), 2.2, 2.0, soilm, B)
    return B, flames


def build_set_C():
    """Valley: recessed trench (real opening), dirt mound, latrine reveal."""
    C = empty("set_C")
    vm = mat_ground("valley_grass", (0.34, 0.47, 0.19), (0.47, 0.56, 0.25), scale=5)
    soil = mat_ground("soil", (0.29, 0.20, 0.12), (0.40, 0.28, 0.17), scale=10, rough=0.9)
    ox0, ox1, oy0, oy1 = -0.55, 0.55, 0.1, 1.5
    for name, cx, cy, sx, sy in [("vg_back", 0, (oy1 + 9) / 2, 14, 9 - oy1),
                                 ("vg_front", 0, (-5 + oy0) / 2, 14, oy0 + 5),
                                 ("vg_left", (-7 + ox0) / 2, (oy0 + oy1) / 2, ox0 + 7, oy1 - oy0),
                                 ("vg_right", (7 + ox1) / 2, (oy0 + oy1) / 2, 7 - ox1, oy1 - oy0)]:
        _plane(name, (cx, cy, 0), sx, sy, vm, C)
    pitd = 0.5
    wallh = pitd + 0.08
    wz = -pitd / 2 + 0.04
    pitm = mat_world("trench_dark", (0.10, 0.07, 0.05), 0.9)
    for name, cx, cy, sx, sy, rot in [("pit_back", 0, oy1, ox1 - ox0, wallh, (math.radians(90), 0, 0)),
                                      ("pit_front", 0, oy0, ox1 - ox0, wallh, (math.radians(90), 0, 0)),
                                      ("pit_left", ox0, (oy0 + oy1) / 2, wallh, oy1 - oy0, (0, math.radians(90), 0)),
                                      ("pit_right", ox1, (oy0 + oy1) / 2, wallh, oy1 - oy0, (0, math.radians(90), 0))]:
        _plane(name, (cx, cy, wz), sx, sy, pitm, C, rot=rot)
    _plane("pit_floor", (0, (oy0 + oy1) / 2, -pitd), ox1 - ox0, oy1 - oy0, pitm, C)
    smooth_rock("soil_mound", (0.95, 0.8, 0.12), 0.5, soil, scale=(1, 1.3, 0.45), parent=C)
    # latrine reveal group (cut18 only): planks over the trench + stake fence
    lat = empty("latrine_group", parent=C)
    wood = mat_world("plank_wood", (0.45, 0.32, 0.18), 0.8)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(sx * 0.35, (oy0 + oy1) / 2, 0.03))
        p = bpy.context.active_object
        p.name = f"latrine_plank_{sx}"
        p.scale = (0.28, 1.5, 0.05)
        p.data.materials.append(wood)
        p.parent = lat
    stakem = mat_world("stake_wood", (0.40, 0.28, 0.16), 0.8)
    for i in range(6):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=1.0,
                                            location=(-1.2 + i * 0.4, 1.8, 0.5))
        st = bpy.context.active_object
        st.name = f"stake_{i}"
        st.data.materials.append(stakem)
        st.parent = lat
    # golden-hour sunset disc + hills + clouds
    sunm = mat_world("sunset_disc", (1.0, 0.75, 0.35), 0.5, emit=6.0, emit_color=(1.0, 0.65, 0.25))
    sphere("sunset_disc", (-6, 18, 2.5), 1.2, sunm, parent=C)
    hillm = mat_ground("valley_hill", (0.25, 0.32, 0.16), (0.35, 0.40, 0.22), scale=3)
    for i, (x, y, r) in enumerate([(-7, 12, 6), (4, 14, 8), (10, 11, 5)]):
        sphere(f"vhill_{i}", (x, y, 1.0), r, hillm, scale=(1, 0.6, 0.4), parent=C)
    cloudmat = cel_mat("cloud_matC", SPR / "fx_cloud.png", emit=1.0)
    for i, (x, y, z, s) in enumerate([(-3, 16, 7.5, 3.0), (3, 18, 8.5, 3.4), (0, 20, 7.0, 2.6)]):
        add_card(f"cloudC_{i}", SPR / "fx_cloud.png", s, s * 0.5, (x, y, z), parent=C, mat=cloudmat)
    return C, lat


def build_lights():
    lights = {}
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 4.5
    sun.angle = math.radians(15)
    sun.use_shadow = True
    so = bpy.data.objects.new("Sun", sun)
    bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(50), 0, math.radians(20))
    lights["sun"] = so
    # warm flickering campfire: 260 W, #ff7b1a, soft 0.5 m shadows
    camp = bpy.data.lights.new("Campfire", "POINT")
    camp.energy = 260
    camp.color = (1.0, 0.48, 0.10)
    camp.shadow_soft_size = 0.50
    camp.use_shadow = True
    co = bpy.data.objects.new("Campfire", camp)
    bpy.context.collection.objects.link(co)
    co.location = (FIRE[0], FIRE[1], 0.85)  # above flame cones so shadows don't cage the light
    noise_mod(camp, "energy", -1, scale=8, strength=31)  # +/-12% flicker
    lights["camp"] = co
    # cool-slate fill opposite the fire (warm/cool two-sided faces)
    fill = bpy.data.lights.new("CaveFill", "AREA")
    fill.energy = 45
    fill.color = (0.024, 0.047, 0.100)  # #2b3d59 cool slate
    fill.size = 2.0
    fill.use_shadow = False
    fo = bpy.data.objects.new("CaveFill", fill)
    bpy.context.collection.objects.link(fo)
    fo.location = (2.2, -1.0, 2.2)
    fo.rotation_euler = (Vector((0, 0.6, 1.0)) - Vector(fo.location)).to_track_quat("-Z", "Y").to_euler()
    lights["cavefill"] = fo
    tox = bpy.data.lights.new("Toxic", "POINT")
    tox.energy = 150
    tox.color = (0.4, 1.0, 0.13)
    tox.shadow_soft_size = 0.4
    tox.use_shadow = True
    to = bpy.data.objects.new("Toxic", tox)
    bpy.context.collection.objects.link(to)
    to.location = (CORNER[0], CORNER[1], 0.8)
    lights["tox"] = to
    sunset = bpy.data.lights.new("Sunset", "SUN")
    sunset.energy = 5.0
    sunset.color = (1.0, 0.62, 0.27)
    sunset.angle = math.radians(8)
    sunset.use_shadow = True
    su = bpy.data.objects.new("Sunset", sunset)
    bpy.context.collection.objects.link(su)
    su.rotation_euler = (math.radians(72), 0, math.radians(-15))
    lights["sunset"] = su
    return lights


LIGHT_ACTS = {
    "sun": (1, 4), "camp": (2, 3), "cavefill": (2, 3),
    "tox": (3,), "sunset": (4,),
}

SKY_KEYS = [
    (1,    [(0.80, 0.93, 1.00), (0.10, 0.60, 0.98), (0.05, 0.35, 0.85)], 1.0),
    (540,  [(0.045, 0.060, 0.110)] * 3, 0.8),
    (828,  [(0.055, 0.090, 0.050)] * 3, 0.8),
    (1206, [(0.060, 0.075, 0.115)] * 3, 0.8),
    (1370, [(1.00, 0.72, 0.35), (0.95, 0.45, 0.25), (0.35, 0.25, 0.45)], 1.0),
]


def build_world(sc):
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.05
    mr.inputs["From Max"].default_value = 0.42
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].position = 0.3
    ramp.color_ramp.elements.new(1.0)
    bg = nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.new("ShaderNodeOutputWorld")
    neg = nt.nodes.new("ShaderNodeMath")
    neg.operation = "MULTIPLY"
    neg.inputs[1].default_value = -1.0
    nt.links.new(geo.outputs["Incoming"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], neg.inputs[0])
    nt.links.new(neg.outputs["Value"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    return nt, ramp, bg


def key_sky(wnt, ramp, bg):
    for f, cols, strength in SKY_KEYS:
        for el, col in zip(ramp.color_ramp.elements, cols):
            el.color = (*col, 1)
            el.keyframe_insert(data_path="color", frame=f)
        bg.inputs["Strength"].default_value = strength
        bg.inputs["Strength"].keyframe_insert(data_path="default_value", frame=f)
    for fc in wnt.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"


def build_compositor(sc):
    sc.use_nodes = True
    nt = sc.node_tree
    nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.threshold = 0.80
    glare.mix = 0.20
    hs = nt.nodes.new("CompositorNodeHueSat")
    hs.inputs["Saturation"].default_value = 1.30
    ell = nt.nodes.new("CompositorNodeEllipseMask")
    ell.width = 0.9
    ell.height = 0.9
    blur = nt.nodes.new("CompositorNodeBlur")
    if hasattr(blur, "size_x"):
        blur.size_x = 80
        blur.size_y = 80
    mixv = nt.nodes.new("CompositorNodeMixRGB")
    mixv.blend_type = "MULTIPLY"
    mixv.inputs["Fac"].default_value = 0.35
    comp = nt.nodes.new("CompositorNodeComposite")
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
    nt.links.new(glare.outputs["Image"], hs.inputs["Image"])
    nt.links.new(ell.outputs["Mask"], blur.inputs["Image"])
    nt.links.new(hs.outputs["Image"], mixv.inputs[1])
    nt.links.new(blur.outputs["Image"], mixv.inputs[2])
    nt.links.new(mixv.outputs["Image"], comp.inputs["Image"])