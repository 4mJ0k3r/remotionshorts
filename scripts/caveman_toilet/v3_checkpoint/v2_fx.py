"""caveman_toilet v2 story FX: per-cut cards + baked animated events."""
import math

import bpy
from mathutils import Vector

from v2_common import (SPR, cel_mat, mat_world, add_card, sphere, empty,
                       noise_mod, bake, hide_keys, log)
from v2_story import (CUTS, CORNER, SQUAT_SPOT, DIG_POS, EUREKA_POS, ARCH,
                      dig_blade, ev15, lerp3, clamp01)

ALL_CUTS = [c[0] for c in CUTS]


def build_fx(cam):
    """Returns {name: dict(ob, cuts)}; cuts = cut ids where visible."""
    fx = {}

    def reg(name, ob, cuts):
        fx[name] = dict(ob=ob, cuts=cuts)
        return ob

    # cut1: question mark above the confused caveman
    q = add_card("fx_question", SPR / "fx_question.png", 0.30, 0.30,
                 (0.30, 0, 1.85), mat=cel_mat("q_mat", SPR / "fx_question.png", emit=0.8))
    reg("question", q, [1])
    # cut9: lion head-and-mane silhouette inside the arch + glowing eyes
    lion = add_card("fx_lion", SPR / "v2_lion.png", 1.3, 1.3,
                    (ARCH[0], 4.35, 1.1), mat=cel_mat("lion_mat", SPR / "v2_lion.png", emit=1.1))
    yaw = math.atan2(0.2 - ARCH[0], -(-1.6 - 4.35))  # face the cut9 camera
    lion.rotation_euler = (math.radians(90), 0, yaw)
    eyem = mat_world("lion_eye", (1.0, 0.6, 0.1), 0.5, emit=6.0, emit_color=(1.0, 0.5, 0.05))
    for sx in (-1, 1):
        sphere(f"lion_eye_{sx}", (sx * 0.16, 0.18, 0.06), 0.045, eyem, parent=lion)
    reg("lion", lion, [9])
    # cuts 10-14: poop mounds in the toxic corner
    poopmat = cel_mat("poop_mat", SPR / "fx_poop.png", emit=0.6)
    for i, (dx, dy) in enumerate([(-0.5, -0.3), (0.4, -0.5), (-0.2, 0.5), (0.6, 0.4)]):
        ob = add_card(f"poop_{i}", SPR / "fx_poop.png", 0.5, 0.5,
                      (CORNER[0] + dx, CORNER[1] + dy, 0.26), mat=poopmat)
        reg(f"poop_{i}", ob, [10, 11, 12, 13, 14])
    # cuts 11-14: 35 buzzing flies + 6 toxic haze cards
    flymat = cel_mat("fly_mat", SPR / "fx_fly.png", emit=0.6)
    import random
    random.seed(41)
    for i in range(35):
        a = random.uniform(0, 2 * math.pi)
        r = random.uniform(0.2, 1.3)
        ob = add_card(f"fly_{i}", SPR / "fx_fly.png", 0.08, 0.08,
                      (CORNER[0] + r * math.cos(a), CORNER[1] + r * math.sin(a),
                       random.uniform(0.3, 1.3)), mat=flymat)
        noise_mod(ob, "location", 0, scale=6, strength=0.12, phase=i * 1.7)
        noise_mod(ob, "location", 1, scale=6, strength=0.12, phase=i * 2.9)
        noise_mod(ob, "location", 2, scale=7, strength=0.08, phase=i * 0.9)
        reg(f"fly_{i}", ob, [11, 12, 13, 14])
    hazemat = cel_mat("haze_mat", SPR / "v2_haze.png", emit=0.5)
    for i in range(6):
        a = 2 * math.pi * i / 6
        ob = add_card(f"haze_{i}", SPR / "v2_haze.png", 1.4, 0.7,
                      (CORNER[0] + 0.8 * math.cos(a), CORNER[1] + 0.8 * math.sin(a),
                       0.5 + 0.15 * (i % 3)), mat=hazemat)
        noise_mod(ob, "location", 0, scale=10, strength=0.10, phase=i * 2.2)
        reg(f"haze_{i}", ob, [11, 12, 13, 14])
    # cut5: relief gas plume behind the hide-rock (3 wisps, animated)
    wispmat = cel_mat("wisp_mat", SPR / "fx_wisp.png", emit=0.8)
    for i in range(3):
        ob = add_card(f"plume_{i}", SPR / "fx_wisp.png", 0.34, 0.75,
                      (SQUAT_SPOT[0] + 0.15 * (i - 1), SQUAT_SPOT[1] + 0.25, 0.4),
                      mat=wispmat)
        reg(f"plume_{i}", ob, [5])
    # cut14: soul bubbles rising from the collapsed heads (3 per char)
    soulmat = cel_mat("soul_mat", SPR / "fx_soul.png", emit=1.6, glow=True)
    anchors = {"caveman": (-0.40, 1.75, 0.30), "buddy": (0.40, 1.75, 0.30)}
    for cn, anc in anchors.items():
        for i in range(3):
            ob = add_card(f"soul_{cn}_{i}", SPR / "fx_soul.png", 0.28, 0.28, anc, mat=soulmat)
            reg(f"soul_{cn}_{i}", ob, [14])
    # cut15: 3D Eureka bulb (emissive sphere + screw base + point light)
    bulb = empty("fx_bulb")
    bulb.location = (EUREKA_POS[0] + 0.15, EUREKA_POS[1], 1.95)
    glow = mat_world("bulb_glow", (1.0, 0.88, 0.45), 0.4, emit=3.0, emit_color=(1.0, 0.85, 0.4))
    sphere("bulb_glass", (0, 0, 0.08), 0.11, glow, parent=bulb)
    base = mat_world("bulb_base", (0.55, 0.55, 0.58), 0.6)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=0.08, location=(0, 0, -0.06))
    bs = bpy.context.active_object
    bs.name = "bulb_screw"
    bs.data.materials.append(base)
    bs.parent = bulb
    bl = bpy.data.lights.new("BulbLight", "POINT")
    bl.energy = 0
    bl.color = (1.0, 0.85, 0.4)
    bl.shadow_soft_size = 0.2
    bl.use_shadow = False  # light sits inside the emissive glass sphere
    blo = bpy.data.objects.new("BulbLight", bl)
    bpy.context.collection.objects.link(blo)
    blo.parent = bulb
    fx["bulb"] = dict(ob=bulb, cuts=[15], light=bl)
    # cut17: 3D stone shovel (handle + flat blade), placed per frame
    shovel = empty("fx_shovel")
    wood = mat_world("shovel_wood", (0.45, 0.32, 0.18), 0.8)
    stone = mat_world("shovel_stone", (0.50, 0.48, 0.45), 0.85)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=1.15, location=(0, 0, 0.575))
    h = bpy.context.active_object
    h.name = "shovel_handle"
    h.data.materials.append(wood)
    h.parent = shovel
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -0.02))
    b = bpy.context.active_object
    b.name = "shovel_blade"
    b.scale = (0.18, 0.03, 0.22)
    b.data.materials.append(stone)
    b.parent = shovel
    reg("shovel", shovel, [17])
    # cut17: 4 flying dirt clods per dig cycle
    dirtmat = cel_mat("dirt_mat", SPR / "fx_dirt.png", emit=0.6)
    for i in range(5):
        ob = add_card(f"clod_{i}", SPR / "fx_dirt.png", 0.16, 0.16, (0, 0, -1), mat=dirtmat)
        reg(f"clod_{i}", ob, [17])
    return fx


def bake_fx(fx, frames):
    """Per-frame animation for event FX (souls, plume, bulb, shovel, clods)."""
    fr = list(frames)
    # ---- question bob (cut1) ----
    q = fx["question"]["ob"]
    bake(q, "location", fr, [(0.30, 0, 1.85 + 0.03 * math.sin(f * 0.2)) for f in fr])
    # ---- relief plume: rise + fade from f398, staggered 6 f ----
    for i in range(3):
        ob = fx[f"plume_{i}"]["ob"]
        t0 = 398 + i * 6
        locs, scales = [], []
        for f in fr:
            u = clamp01((f - t0) / 30.0)
            z = 0.4 + 1.0 * u
            s = 0.34 * (1 + 0.4 * u) if f >= t0 else 0.0001
            locs.append((SQUAT_SPOT[0] + 0.15 * (i - 1), SQUAT_SPOT[1] + 0.25, z))
            scales.append((s, s * 2.2, 1))
        bake(ob, "location", fr, locs)
        bake(ob, "scale", fr, scales)
    # ---- soul bubbles: rise 0.9 m over 30 f, shrink at top, staggered ----
    starts = {"caveman": [1160, 1168, 1176], "buddy": [1170, 1178, 1186]}
    anchors = {"caveman": (-0.40, 1.75, 0.30), "buddy": (0.40, 1.75, 0.30)}
    for cn in ("caveman", "buddy"):
        for i in range(3):
            ob = fx[f"soul_{cn}_{i}"]["ob"]
            t0 = starts[cn][i]
            anc = anchors[cn]
            locs, scales = [], []
            for f in fr:
                u = clamp01((f - t0) / 30.0)
                active = t0 <= f <= t0 + 30
                x = anc[0] + 0.06 * math.sin(u * 6 + i)
                z = anc[2] + 0.9 * u
                s = 0.28 * (1 - 0.8 * u) if active else 0.0001
                locs.append((x, anc[1], z))
                scales.append((s, s, 1))
            bake(ob, "location", fr, locs)
            bake(ob, "scale", fr, scales)
    # ---- Eureka bulb pop + light ----
    bulb = fx["bulb"]["ob"]
    bl = fx["bulb"]["light"]
    scales = [(max(0.0001, ev15(f)),) * 3 for f in fr]
    bake(bulb, "scale", fr, scales)
    bake(bl, "energy", fr, [12.0 * max(0.0, ev15(f)) for f in fr])
    # ---- shovel follows the dig blade; hands grip the handle ----
    shovel = fx["shovel"]["ob"]
    locs, quats = [], []
    for f in fr:
        blade, thrust = dig_blade(f)
        bw = Vector((DIG_POS[0] + blade[0], DIG_POS[1] + blade[1], blade[2]))
        grip_hi = Vector(lerp3(tuple(bw), (DIG_POS[0], DIG_POS[1] + 0.10, 0.95), 0.75))
        d = (grip_hi - bw)
        if d.length < 1e-5:
            d = Vector((0, 0, 1))
        locs.append(tuple(bw))
        quats.append(tuple(d.normalized().to_track_quat("Z", "Y")))
    bake(shovel, "location", fr, locs)
    bake(shovel, "rotation_quaternion", fr, quats)
    # ---- dirt clods: parabolic toss each 30 f cycle ----
    mound = Vector((0.95, 0.8, 0.30))
    for i in range(5):
        ob = fx[f"clod_{i}"]["ob"]
        locs, vis = [], []
        for f in fr:
            cyc = (f - 1370) // 30
            launch = 1370 + cyc * 30 + 19 + i * 1.5
            u = (f - launch) / 12.0
            if 0 <= u <= 1 and f >= 1370:
                start = Vector((DIG_POS[0], DIG_POS[1] + 0.30, 0.55))
                target = mound + Vector((0.12 * (i - 1.5), 0.1 * (i % 2), 0))
                p = start.lerp(target, u)
                p.z += 0.55 * math.sin(math.pi * u)
                locs.append(tuple(p))
                vis.append(False)
            else:
                locs.append((0, 0, -1))
                vis.append(True)
        bake(ob, "location", fr, locs)
        hide_keys(ob, fr, vis)
        fx[f"clod_{i}"]["skip_vis"] = True
    log(f"fx baked: {len(fx)} objects")


def fx_visibility(fx):
    """hide_render CONSTANT keys at every cut boundary (incl. children)."""
    bounds = sorted({c[1] for c in CUTS} | {CUTS[-1][2]})
    for name, rec in fx.items():
        if rec.get("skip_vis"):
            continue
        ob = rec["ob"]
        cuts = rec["cuts"]
        frames, hidden = [], []
        for f in bounds:
            cid = next((c[0] for c in CUTS if c[1] <= f < c[2]), CUTS[-1][0])
            frames.append(f)
            hidden.append(cid not in cuts)
        for target in [ob] + list(ob.children_recursive):
            hide_keys(target, frames, hidden)
