"""The Last Gumball v01: silent 10 s Rick's Clips style test (540x960, 30 fps).

Launcher (system Python, owns .blender_gpu.lock):
  python scripts/last_gumball/v01/build.py proof           # build, save, reopen, benchmark
  python scripts/last_gumball/v01/build.py stills 1 66 ... # render chosen frames from saved blend
  python scripts/last_gumball/v01/build.py render          # render all frames from saved blend
Frames are one-based in Blender. Cuts (zero-based destination): 66, 108, 186.
"""
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
from uuid import uuid4

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "scripts/ricks_v2_kit.py").is_file())
OUT = ROOT / "renders/last_gumball/v01"
BLEND = OUT / "last_gumball_v01.blend"
BLENDER = r"D:\tools\Blender\4.2.23\blender.exe"
FPS, END = 30, 300
SIZE = (540, 960)
S2, S3, S4 = 67, 109, 187          # first Blender frame of shots 2-4
CUTS0 = [S2 - 1, S3 - 1, S4 - 1]   # zero-based destination frames
BENCH = (1, 30, 66, 67, 78, 108, 109, 150, 187, 212, 260, 300)

# World layout (metres). Machine front faces -Y at y=0.
HERO = (-0.45, -0.10)
ROOT_YAW = math.radians(85)        # body forward heading ~ -5 deg (toward machine side)
SLOT = (-0.17, 0.0, 0.98)
WINDOW = (0.02, 0.0, 1.22)
MOUTH = (-0.17, -0.15, 0.70)
CUP_HOME = (-0.17, -0.15, 0.465)   # cup bottom centre in shot 4
CUP_H, CUP_RB, CUP_RT = 0.10, 0.052, 0.072
BALL_R = 0.028
COIN_R = 0.018
O = (6.0, 0.0, 0.0)                # machine interior set origin
GATE = (O[0], O[1], O[2] + 1.0)
SLOT_END_D, GATE_START_D = 0.32, 0.2405


# ----------------------------------------------------------------------------------------------
# Small math helpers (usable before bpy import)
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(f, a, b):
    from ricks_v2_kit import look
    return look.ease5((f - a) / (b - a)) if b != a else float(f >= b)


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def catmull(points, u):
    """Uniform Catmull-Rom through points for u in [0, 1]."""
    n = len(points) - 1
    x = clamp(u) * n
    i = min(int(x), n - 1)
    t = x - i
    p0 = points[max(i - 1, 0)]
    p1, p2 = points[i], points[i + 1]
    p3 = points[min(i + 2, n)]
    return tuple(.5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                       + (-a + 3 * b - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3))


# ----------------------------------------------------------------------------------------------
# Interior track path and red-ball timing (shot 3)
def track_points():
    pts = []
    ox, oy, oz = O
    for i in range(13):                                 # leg 1, +X, gentle fall
        t = i / 12
        pts.append((ox + .24 * t, oy - .10, oz + .85 - .05 * t))
    for i in range(1, 25):                              # bend toward camera
        a = math.pi / 2 - math.pi * i / 24
        pts.append((ox + .24 + .12 * math.cos(a), oy - .22 + .12 * math.sin(a), oz + .80 - .04 * i / 24))
    for i in range(1, 21):                              # leg 2, -X, flattening into the lip rise
        t = i / 20
        z = oz + .76 - .085 * smooth(t / .8) + .009 * smooth((t - .82) / .18)
        pts.append((ox + .24 - .38 * t, oy - .34, z))
    return pts


def path_tables(points):
    lengths = [0.0]
    for a, b in zip(points, points[1:]):
        lengths.append(lengths[-1] + math.dist(a, b))
    return lengths


def path_at(points, lengths, s):
    s = clamp(s, 0, lengths[-1])
    for i in range(1, len(lengths)):
        if lengths[i] >= s:
            t = (s - lengths[i - 1]) / max(1e-9, lengths[i] - lengths[i - 1])
            return lerp(points[i - 1], points[i], t), i
    return points[-1], len(points) - 1


ROLL_A, STALL, TIP, DROP_END = 117, 176, 182, 186


def interior_ball(f, points, lengths):
    """Red ball centre in the interior for Blender frame f (109-186)."""
    gx, gy, gz = GATE
    total = lengths[-1]
    if f <= 112:
        u = (f - 109) / 3
        return (gx, gy - .005 - .035 * smooth(u), gz - .01 * u)
    if f < ROLL_A:
        t = (f - 112) / FPS
        land = points[0]
        T = (ROLL_A - 112) / FPS
        k = t / T
        z0 = gz - .01
        return (gx + (land[0] - gx) * k, gy - .04 + (land[1] - gy + .04) * k,
                z0 - (z0 - land[2]) * k * k)
    if f <= TIP:
        # Speed peaks around the bend and decays to a near-stall at the lip.
        def speed(u):
            return max(.03, math.sin(math.pi * (.15 + .85 * u)))
        steps = 400
        cum = [0.0]
        for i in range(steps):
            cum.append(cum[-1] + speed((i + .5) / steps))
        main_end = total - .018
        if f <= STALL:
            u = (f - ROLL_A) / (STALL - ROLL_A)
            s = main_end * cum[int(u * steps)] / cum[-1]
        else:
            u = (f - STALL) / (TIP - STALL)
            s = main_end + .018 * u ** 1.6
        return path_at(points, lengths, s)[0]
    t = (f - TIP) / FPS
    end = points[-1]
    return (end[0] - .32 * t, end[1] - .03 * t, end[2] - 4.9 * t * t - .05 * t)


# ----------------------------------------------------------------------------------------------
# Shot-4 spill simulation (pure Python, deterministic)
def cup_pose(f):
    """Cup bottom centre (world) for shot 4 frame f (fractional allowed)."""
    rec = smooth((f - 208) / 5) - .55 * smooth((f - 216) / 16)
    return (CUP_HOME[0] - .018 * rec, CUP_HOME[1] - .004 * rec, CUP_HOME[2] - .016 * rec)


def simulate_spill():
    rng = random.Random(7)
    balls = []
    # Red hero gumball keeps the downward momentum from the cut.
    balls.append({"p": [MOUTH[0], MOUTH[1], MOUTH[2] - .012], "v": [0, 0, -1.05], "t": S4, "r": BALL_R})
    n = 34
    for i in range(n):
        t = 207 + (i * 0.55 if i < 12 else 6.6 + (i - 12) * .72)
        balls.append({"p": [MOUTH[0] + rng.uniform(-.018, .018), MOUTH[1] + rng.uniform(-.02, .015),
                            MOUTH[2] + .012],
                      "v": [rng.uniform(-.22, .22), rng.uniform(-.32, -.05), rng.uniform(-.9, -.5)],
                      "t": t, "r": BALL_R * rng.uniform(.93, 1.04)})
    sub = 10
    dt = 1 / (FPS * sub)
    g = -9.81
    hx, hy = HERO
    box = ((-.30, .30), (0.0, .42), (0.0, 1.62))
    frames = {}

    def push(b, n_, depth, e=.3, mu=.08):
        p, v = b["p"], b["v"]
        for k in range(3):
            p[k] += n_[k] * depth
        vn = sum(v[k] * n_[k] for k in range(3))
        if vn < 0:
            for k in range(3):
                v[k] -= (1 + e) * vn * n_[k]
            vt = [v[k] - sum(v[j] * n_[j] for j in range(3)) * n_[k] for k in range(3)]
            for k in range(3):
                v[k] -= mu * vt[k]

    for f in range(S4, END + 1):
        for s in range(sub):
            ft = f + s / sub
            cb = cup_pose(ft)
            active = [b for b in balls if b["t"] <= ft]
            for b in active:
                b["v"][2] += g * dt
                for k in range(3):
                    b["p"][k] += b["v"][k] * dt
            for b in active:
                p, r = b["p"], b["r"]
                # Floor with rolling resistance.
                if p[2] < r + .001:
                    if p[2] < r:
                        push(b, (0, 0, 1), r - p[2], e=.26, mu=.05)
                    b["v"][0] *= .965
                    b["v"][1] *= .965
                # Machine cabinet.
                c = [clamp(p[k], *box[k]) for k in range(3)]
                d = math.dist(p, c)
                if d < r:
                    if d > 1e-6:
                        push(b, tuple((p[k] - c[k]) / d for k in range(3)), r - d)
                    else:
                        push(b, (0, -1, 0), r + p[1])
                # Commuter legs / torso (soft cylinders).
                dx, dy = p[0] - hx, p[1] - hy
                rho = math.hypot(dx, dy)
                lim = .15 if p[2] < .56 else .14
                if p[2] < 1.05 and rho < lim + r and rho > 1e-6:
                    push(b, (dx / rho, dy / rho, 0), lim + r - rho, e=.2)
                # Paper cup: wall, bottom and rolled rim.
                rel = [p[k] - cb[k] for k in range(3)]
                rho = math.hypot(rel[0], rel[1])
                radial = (rel[0] / rho, rel[1] / rho, 0) if rho > 1e-6 else (1, 0, 0)
                zr = rel[2]
                if -r < zr < CUP_H:
                    R = CUP_RB + (CUP_RT - CUP_RB) * clamp(zr / CUP_H)
                    if rho < R:
                        if zr > 0 and rho > R - r:
                            push(b, tuple(-x for x in radial), rho - (R - r), e=.15)
                        if zr < r:
                            push(b, (0, 0, 1), r - zr, e=.22, mu=.25)
                            b["v"][0] *= .97
                            b["v"][1] *= .97
                    elif rho < R + r and zr > 0:
                        push(b, radial, R + r - rho, e=.25)
                q = (cb[0] + radial[0] * CUP_RT, cb[1] + radial[1] * CUP_RT, cb[2] + CUP_H)
                d = math.dist(p, q)
                if 1e-6 < d < r + .004:
                    push(b, tuple((p[k] - q[k]) / d for k in range(3)), r + .004 - d, e=.3)
            # Ball-ball contacts.
            for i in range(len(active)):
                a = active[i]
                for j in range(i + 1, len(active)):
                    b = active[j]
                    dvec = [b["p"][k] - a["p"][k] for k in range(3)]
                    d = math.sqrt(sum(x * x for x in dvec))
                    rr = a["r"] + b["r"]
                    if 1e-7 < d < rr:
                        n_ = [x / d for x in dvec]
                        corr = (rr - d) * .5
                        for k in range(3):
                            a["p"][k] -= n_[k] * corr
                            b["p"][k] += n_[k] * corr
                        rv = sum((b["v"][k] - a["v"][k]) * n_[k] for k in range(3))
                        if rv < 0:
                            imp = -(1 + .2) * rv * .5
                            for k in range(3):
                                a["v"][k] -= imp * n_[k]
                                b["v"][k] += imp * n_[k]
            for b in active:
                speed = math.sqrt(sum(x * x for x in b["v"]))
                if speed < .025 and b["p"][2] < b["r"] + .002:
                    b["v"] = [0, 0, 0]
        frames[f] = [(tuple(b["p"]), b["t"] <= f) for b in balls]
    return balls, frames


# ----------------------------------------------------------------------------------------------
# Blender scene
def build():
    import bpy
    from mathutils import Matrix, Quaternion, Vector, Euler
    import ricks_v2_kit as kit

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    kit.configure_ricks_scene(scene, width=SIZE[0], height=SIZE[1], fps=FPS, frame_end=END, samples=8)
    scene.world = bpy.data.worlds.new("Station cool air")
    scene.world.use_nodes = True
    bg = next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = kit.look.rgba("#18213a")
    bg.inputs[1].default_value = .55
    col = bpy.data.collections.new("Last Gumball v01")
    scene.collection.children.link(col)

    bpy.ops.object.camera_add()
    camera = scene.camera = bpy.context.object
    camera.name = "Camera | delivery"
    kit.put(camera, col)
    camera.data.lens = 26
    flash = ((1, 0), (S3 - 2, 0), (S3 - 1, .007), (S3, .007), (S3 + 1, 0))
    kit.setup_ricks_compositor(scene, camera=camera, portal_flash_keys=flash)
    camera.data.clip_start = .015
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = None
    camera.data.dof.aperture_blades = 6

    def open_tube(obj):
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if len(f.verts) > 4], context="FACES")
        bm.to_mesh(obj.data)
        bm.free()
        return obj

    prop_inks = []

    def ink(obj, px=1.25):
        mod = kit.apply_prop_ink(obj, col)
        prop_inks.append((obj, mod, px))
        return obj

    def block(name, loc, size, mat, inked=False, parent=None, rot=None):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
        obj = kit.put(bpy.context.object, col, parent, mat)
        obj.name = name
        obj.scale = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.location = loc
        if rot:
            obj.rotation_euler = rot
        if inked:
            ink(obj)
        return obj

    def torus(name, loc, major, minor, mat, rot=(math.pi / 2, 0, 0), parent=None, segs=48, inked=False):
        bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=segs,
                                         minor_segments=10)
        obj = kit.put(bpy.context.object, col, parent, mat)
        obj.name = name
        obj.location, obj.rotation_euler = loc, rot
        for p in obj.data.polygons:
            p.use_smooth = True
        if inked:
            ink(obj)
        return obj

    def disc_y(name, loc, radius, depth, mat, parent=None, inked=False, segs=40):
        obj = kit.cylinder(name, col, loc, radius, depth, mat, parent, length_segments=segs)
        obj.rotation_euler = (math.pi / 2, 0, 0)
        if inked:
            ink(obj)
        return obj

    def tiles(name, base, alt, mortar, plane, scale=6.0, rough=.55):
        m = kit.surface(name, base, rough)
        nt, ln = m.node_tree.nodes, m.node_tree.links
        p = next(n for n in nt if n.type == "BSDF_PRINCIPLED")
        tc, sep, comb = nt.new("ShaderNodeTexCoord"), nt.new("ShaderNodeSeparateXYZ"), nt.new("ShaderNodeCombineXYZ")
        ln.new(tc.outputs["Object"], sep.inputs[0])
        a, b = {"xz": ("X", "Z"), "yz": ("Y", "Z"), "xy": ("X", "Y")}[plane]
        ln.new(sep.outputs[a], comb.inputs[0])
        ln.new(sep.outputs[b], comb.inputs[1])
        brick = nt.new("ShaderNodeTexBrick")
        brick.inputs["Color1"].default_value = kit.look.rgba(base)
        brick.inputs["Color2"].default_value = kit.look.rgba(alt)
        brick.inputs["Mortar"].default_value = kit.look.rgba(mortar)
        brick.inputs["Scale"].default_value = scale
        brick.inputs["Mortar Size"].default_value = .018
        brick.inputs["Brick Width"].default_value = .5
        brick.inputs["Row Height"].default_value = .25
        ln.new(comb.outputs[0], brick.inputs["Vector"])
        noise = nt.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 3.0
        mix = nt.new("ShaderNodeMixRGB")
        mix.blend_type, mix.inputs[0].default_value = "MULTIPLY", .25
        ln.new(brick.outputs["Color"], mix.inputs[1])
        ln.new(noise.outputs["Color"], mix.inputs[2])
        ln.new(comb.outputs[0], noise.inputs["Vector"])
        ln.new(mix.outputs[0], p.inputs["Base Color"])
        bump = nt.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .25
        ln.new(brick.outputs["Fac"], bump.inputs["Height"])
        ln.new(bump.outputs[0], p.inputs["Normal"])
        return m

    # ---------------- Station alcove (cool) ----------------
    floor = tiles("Station floor tiles", "#4a5266", "#3f475a", "#262b3a", "xy", 3.0, .5)
    wall = tiles("Subway wall tiles", "#9fb2c8", "#8ea2bb", "#3d4a60", "xz", 7.0, .45)
    side = tiles("Side wall tiles", "#8ea3bd", "#7f95b0", "#36435a", "yz", 7.0, .45)
    trim = kit.surface("Tile trim navy", "#1f2f52", .6)
    block("Floor", (0, -1.0, -.05), (4.0, 4.5, .1), floor)
    block("Back wall", (0, .56, 1.25), (4.0, .1, 2.5), wall)
    block("Left wall", (-1.35, -1.0, 1.25), (.1, 4.5, 2.5), side)
    block("Right wall", (1.35, -1.0, 1.25), (.1, 4.5, 2.5), side)
    block("Ceiling", (0, -1.0, 2.45), (4.0, 4.5, .1), kit.surface("Ceiling", "#1a2236", .8))
    block("Wall trim band", (0, .50, .95), (4.0, .03, .07), trim)
    block("Left trim band", (-1.29, -1.0, .95), (.03, 4.5, .07), trim)
    block("Floor skirting", (0, .50, .06), (4.0, .04, .12), trim)
    cool = kit.emission("Fluorescent cool tube", "#d9e6ff", 2.2)
    block("Ceiling tube", (-.2, -.2, 2.37), (1.3, .05, .03), cool)
    block("Ceiling tube 2", (-.2, -1.6, 2.37), (1.3, .05, .03), cool)
    steel = kit.surface("Pillar painted steel", "#33486e", .72)
    pillar = kit.cylinder("Foreground pillar", col, (.665, -1.10, 1.2), .11, 2.4, steel, length_segments=32)
    ink(pillar, 1.4)
    for z in (.35, 1.9):
        kit.cylinder("Pillar band", col, (.665, -1.10, z), .118, .06, trim, length_segments=32)
    wood = kit.texture("Bench slats", ("#3a2a2c", "#6b4a3c", "#8a6248"), "wood")
    block("Bench seat", (-.95, .30, .44), (.70, .32, .05), wood, True)
    block("Bench back", (-.95, .45, .70), (.70, .04, .30), wood, True)
    for x in (-1.22, -.68):
        block("Bench leg", (x, .30, .21), (.05, .26, .42), trim, True)
    binmat = kit.surface("Bin steel", "#4a5d74", .6, .3)
    bin_ = kit.cylinder("Trash bin", col, (.62, .26, .28), .14, .56, binmat, length_segments=28)
    ink(bin_)
    kit.cylinder("Bin lid", col, (.62, .26, .57), .15, .03, trim, length_segments=28)
    # Abstract route map, coloured lines only (no lettering).
    block("Map frame", (-.92, .50, 1.45), (.72, .02, .50), trim, True)
    block("Map paper", (-.92, .488, 1.45), (.66, .01, .44), kit.surface("Map cream", "#e8dfc8", .8))
    for i, (c, z0, z1) in enumerate((("#d8463c", 1.30, 1.58), ("#2f78c4", 1.52, 1.36), ("#e3a930", 1.40, 1.42))):
        line = kit.tube("Map line", col, [(-1.20, .48, z0), (-.92, .48, (z0 + z1) / 2 + .03 * (i - 1)), (-.64, .48, z1)],
                        .008, kit.surface("Map ink " + c, c, .7))
    # Shadowy far floor beyond the pillar for depth.
    block("Platform edge strip", (0, -2.6, .005), (4.0, .12, .01), kit.surface("Edge strip", "#c99a2e", .6))

    # ---------------- Gumball machine (warm practical) ----------------
    mroot = kit.empty("Machine | root", col)
    teal = kit.surface("Machine teal enamel", "#2a6b70", .68)
    teal_dark = kit.surface("Machine dark panel", "#1b3f47", .74)
    brass = kit.surface("Brass", "#c99a45", .36, .8)
    chrome = kit.surface("Chrome trim", "#a3abba", .32, .75)
    warm = kit.emission("Header warm glow", "#ffbf6a", 1.25)
    glow_back = kit.emission("Window back glow", "#ffdca0", .95)
    dark = kit.emission("Mouth darkness", "#08070a", 1.0)
    block("Machine cabinet", (0, .21, .81), (.60, .42, 1.62), teal, True, mroot)
    block("Machine kick panel", (0, -.004, .16), (.56, .01, .26), teal_dark, False, mroot)
    block("Machine header box", (0, -.01, 1.52), (.56, .04, .14), teal_dark, True, mroot)
    block("Header warm panel", (0, -.032, 1.52), (.50, .006, .09), warm, False, mroot)
    for x in (-.29, .29):
        block("Machine chrome edge", (x, -.004, .81), (.025, .02, 1.60), chrome, False, mroot)
    for i in range(7):
        kit.ball("Header bulb", col, (-.21 + i * .07, -.04, 1.52), (.012, .006, .012), warm, mroot, 10, 6)
    # Window: brass porthole, glowing recess, lone red gumball on a shelf.
    torus("Window brass rim", (WINDOW[0], -.014, WINDOW[2]), .145, .016, brass, parent=mroot, inked=True)
    rec = kit.cylinder("Window recess", col, (WINDOW[0], .10, WINDOW[2]), .135, .22, teal_dark, mroot, length_segments=40)
    rec.rotation_euler = (math.pi / 2, 0, 0)
    open_tube(rec)
    disc_y("Window glow back", (WINDOW[0], .205, WINDOW[2]), .133, .01, glow_back, mroot)
    block("Window shelf", (WINDOW[0], .10, WINDOW[2] - .105), (.26, .20, .02), chrome, False, mroot)
    red = kit.surface("Red gumball", "#e3262d", .26)
    window_ball = kit.ball("Window | last red gumball", col, (WINDOW[0] + .035, .11, WINDOW[2] - .095 + BALL_R),
                           (BALL_R,) * 3, red, mroot, 24, 16)
    ink(window_ball, 1.6)
    glass = kit.emission("Glass glint", "#f4fbff", 1.6)
    for k, (a0, a1, rr) in enumerate(((2.25, 2.75, .10), (2.35, 2.55, .075))):
        pts = [(WINDOW[0] + rr * math.cos(a0 + (a1 - a0) * i / 6), -.03, WINDOW[2] + rr * math.sin(a0 + (a1 - a0) * i / 6))
               for i in range(7)]
        kit.tube("Window glass glint", col, pts, .0035 - .001 * k, glass, mroot)
    # Coin slot: round brass rim plate with a dark vertical slit.
    disc_y("Coin plate", (SLOT[0], -.007, SLOT[2]), .045, .014, brass, mroot, True)
    torus("Coin plate raised rim", (SLOT[0], -.0145, SLOT[2]), .041, .0055, brass, parent=mroot)
    block("Coin slit", (SLOT[0], -.0145, SLOT[2]), (.0085, .003, .040), dark, False, mroot)
    kit.ball("Coin return button", col, (SLOT[0] + .10, -.01, SLOT[2]), (.022, .012, .022), chrome, mroot, 16, 10)
    # Delivery spout: chrome box chute with a dark mouth underneath and a hinged flap.
    spout = block("Spout chute", (MOUTH[0], -.095, .765), (.115, .19, .085), chrome, True, mroot)
    block("Spout back plate", (MOUTH[0], -.006, .74), (.17, .012, .17), teal_dark, True, mroot)
    mouth = kit.ball("Spout mouth dark", col, (MOUTH[0], MOUTH[1], .7215), (.040, .040, .002), dark, mroot, 20, 6)
    flap_pivot = kit.empty("Spout flap pivot", col, (MOUTH[0], -.19, .808), mroot)
    block("Spout flap", (0, -.004, -.04), (.10, .006, .08), brass, True, flap_pivot)
    machine_lamp = kit.make_ricks_light("Machine warm spill", col, (-.05, -.30, 1.50), (-.30, -.15, .70),
                                        "#ffb15a", 32, .45, kind="SPOT", angle=75)
    window_lamp = bpy.data.lights.new("Window warm bulb", "POINT")
    window_lamp.energy, window_lamp.color, window_lamp.shadow_soft_size = 3.0, kit.look.rgba("#ffcf8a")[:3], .05
    wl = kit.put(bpy.data.objects.new("Window warm bulb", window_lamp), col, mroot)
    wl.location = (WINDOW[0] - .05, .08, WINDOW[2] + .07)
    kit.make_ricks_light("Ceiling cool area", col, (-.3, -.7, 2.3), (-.3, -.3, .8), "#a8bfff", 70, 1.4)
    kit.make_ricks_light("Cool fill from platform", col, (.6, -2.6, 1.6), (-.3, 0, 1.0), "#7d95e0", 40, 1.2)

    # ---------------- Machine interior set (shot 3) ----------------
    ox, oy, oz = O
    bronze = kit.surface("Interior dark bronze", "#4e3426", .62, .35)
    bronze_lit = kit.surface("Interior bronze plate", "#8a5c3a", .5, .45)
    rail_mat = kit.surface("Track chrome rail", "#c6c9d2", .28, .85)
    # Gate plate: square plate with a round hole for the ball.
    verts, faces = [], []
    seg = 48
    for i in range(seg):
        a = math.tau * i / seg
        c, s = math.cos(a), math.sin(a)
        k = .42 / max(abs(c), abs(s))
        verts.append((ox + .06 * c, oy, GATE[2] + .06 * s))
        verts.append((ox + k * c, oy, GATE[2] + k * s))
    for i in range(seg):
        j = (i + 1) % seg
        faces.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    plate = kit.mesh("Interior gate plate", col, verts, faces, bronze_lit)
    torus("Interior brass gate ring", GATE, .06, .009, brass, inked=True)
    for i in range(10):
        a = math.tau * i / 10
        kit.ball("Gate rivet", col, (ox + .11 * math.cos(a), oy - .006, GATE[2] + .11 * math.sin(a)),
                 (.008, .006, .008), brass, None, 10, 6)
    hopper = kit.cylinder("Hopper chute behind gate", col, (ox, oy + .12, GATE[2]), .062, .24, bronze, length_segments=32)
    hopper.rotation_euler = (math.pi / 2, 0, 0)
    open_tube(hopper)
    disc_y("Hopper warm glow", (ox, oy + .235, GATE[2]), .06, .005, kit.emission("Hopper glow", "#ff9a48", .55), None)
    block("Interior back wall", (ox, oy + .48, oz + .8), (1.8, .05, 1.6), bronze)
    slits = kit.emission("Grille warm slits", "#ffae5c", 1.4)
    for i in range(7):
        block("Grille slit", (ox - .45 + i * .15, oy + .45, oz + .55), (.035, .01, .30), slits)
    for i in range(5):
        g = kit.cylinder("Background gear", col, (ox + .45 - i * .26, oy + .40, oz + 1.15 - .1 * (i % 2)),
                         .09 + .02 * (i % 3), .03, bronze_lit, length_segments=18)
        g.rotation_euler = (math.pi / 2, 0, 0)
        ink(g)
    block("Interior floor", (ox, oy - .2, oz + .30), (1.8, 1.6, .05), bronze)
    block("Interior side wall", (ox - .70, oy - .2, oz + .8), (.05, 1.6, 1.4), bronze)
    block("Interior side wall R", (ox + .75, oy - .2, oz + .8), (.05, 1.6, 1.4), bronze)
    points = track_points()
    lengths = path_tables(points)
    rails_l, rails_r = [], []
    for i, p in enumerate(points):
        a, b = points[max(i - 1, 0)], points[min(i + 1, len(points) - 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty)
        nx, ny = -ty / tl, tx / tl
        rails_l.append((p[0] + nx * .021, p[1] + ny * .021, p[2] - .0245))
        rails_r.append((p[0] - nx * .021, p[1] - ny * .021, p[2] - .0245))
    for name, pts in (("Track rail L", rails_l), ("Track rail R", rails_r)):
        kit.tube(name, col, pts, .0043, rail_mat)
    for i in range(0, len(points), 8):
        p = points[i]
        kit.tube("Track support", col, [(p[0], p[1], p[2] - .03), (p[0], p[1], oz + .32)], .005, bronze_lit)
    lip = points[-1]
    kit.tube("Track lip bar", col, [(lip[0] - .006, lip[1] - .03, lip[2] - .014), (lip[0] - .006, lip[1] + .03, lip[2] - .014)],
             .005, brass)
    for x, y in ((-.12, -.55), (.42, -.50)):
        kit.cylinder("Foreground brass rod", col, (ox + x, oy + y, oz + .9), .012, 1.2, brass, length_segments=16)
    fg = kit.cylinder("Foreground gear", col, (ox - .27, oy - .56, oz + .86), .085, .025, bronze_lit, length_segments=20)
    fg.rotation_euler = (math.pi / 2, 0, 0)
    ink(fg)
    for i in range(12):
        a = math.tau * i / 12
        t_ = block("Gear tooth", (ox - .27 + .095 * math.cos(a), oy - .56, oz + .86 + .095 * math.sin(a)),
                   (.025, .022, .02), bronze_lit, False, None, (0, -a, 0))
    interior_ball_obj = kit.ball("Interior | last red gumball", col, GATE, (BALL_R,) * 3, red, None, 24, 16)
    ink(interior_ball_obj, 1.6)
    kit.make_ricks_light("Interior warm key", col, (ox + .30, oy - .55, oz + 1.25), (ox + .1, oy - .2, oz + .8),
                         "#ffb26a", 40, .5, kind="SPOT", angle=95)
    kit.make_ricks_light("Interior cool fill", col, (ox - .5, oy - .9, oz + .7), (ox, oy - .2, oz + .8),
                         "#7f9cff", 22, .8)
    kit.make_ricks_light("Interior track wash", col, (ox + .05, oy - .35, oz + 1.20), (ox + .05, oy - .25, oz + .55),
                         "#ffc890", 14, .9)
    for i in range(6):
        block("Floor glow slit", (ox - .40 + i * .16, oy - .05, oz + .33), (.05, .40, .01), slits)
    pl = bpy.data.lights.new("Interior gate glow", "POINT")
    pl.energy, pl.color, pl.shadow_soft_size = 2.4, kit.look.rgba("#ffb06a")[:3], .05
    kit.put(bpy.data.objects.new("Interior gate glow", pl), col).location = (ox + .05, oy - .12, GATE[2] + .08)

    # ---------------- Commuter ----------------
    art = HERE / "art"
    names = ("bored", "notice", "eager", "hopeful", "shock", "shock_track", "deadpan_down", "deadpan")
    hero = kit.build_ricks_character("Commuter", col, costume_image=art / "commuter_coat.png",
                                     expression_images={n: art / f"{n}.png" for n in names},
                                     initial_expression="bored")
    torso = bpy.data.objects["Commuter | graphic pill torso"]
    torso.data.materials[0] = kit.make_cel_character_material("Commuter navy coat", "#2e3757")
    cap = bpy.data.objects["Commuter | shaped hair cap"]
    cap.data.materials[0] = kit.make_cel_character_material("Commuter charcoal hair", "#2a2230")
    for obj in hero.head.children:
        if obj.type == "CURVE" and "highlight" in obj.name:
            obj.data.materials[0] = kit.make_cel_character_material("Commuter hair sheen", "#5a4c66")
    face_mat = bpy.data.objects["Commuter | ellipsoid head"].data.materials[0]

    # Uneven, asymmetric head: one smooth static field applied to the head, hair,
    # their ink hulls and the conformed face decals, so the art follows the surface.
    def warp(co):
        x, y, z = co
        ax, az = x / kit.HEAD[0], z / kit.HEAD[2]
        s = 1 + .045 * ax * (-az) + .022 * math.sin(1.7 * ax + .9 * az + .6) + .03 * max(0, -az) * max(0, ax)
        return Vector((x * s + .013 * az * az * (1 if az > 0 else -.6), y * s * (1 + .02 * az),
                       z * s * (1 + .035 * ax)))

    head_meshes = [o for o in hero.head.children_recursive if o.type == "MESH" and o != hero.sweat]
    for obj in head_meshes:
        for v in obj.data.vertices:
            v.co = warp(v.co)
    for obj in hero.head.children:
        if obj.type == "CURVE":
            for p in obj.data.splines[0].bezier_points:
                p.co, p.handle_left, p.handle_right = warp(p.co), warp(p.handle_left), warp(p.handle_right)

    # Varied, hand-drawn line weight on the character hulls (static per vertex).
    for mod in hero.ink_modifiers:
        obj = mod.id_data
        vg = obj.vertex_groups.new(name="Ink weight")
        for v in obj.data.vertices:
            x, y, z = v.co
            n = .5 + .5 * math.sin(23 * x + 9 * z + 1.3) * math.cos(17 * z - 11 * y + .4)
            w = clamp(.42 + .48 * n + .55 * max(0, -z / .25) * .5 + .12 * max(0, x / .25), .38, 1.0)
            vg.add([v.index], w, "REPLACE")
        mod.vertex_group = vg.name

    # Flat cream thumb mittens with bold ink edges (two-sided).
    contour = [(0.000, -0.016), (0.020, -0.024), (0.045, -0.025), (0.066, -0.021), (0.077, -0.011),
               (0.079, 0.000), (0.075, 0.010), (0.062, 0.016), (0.050, 0.017), (0.046, 0.024),
               (0.040, 0.034), (0.031, 0.039), (0.024, 0.036), (0.022, 0.026), (0.015, 0.019), (0.002, 0.014)]
    hand_ink = kit.emission("Commuter mitten ink", kit.CHARACTER_INK)
    hands = []
    for side in (-1, 1):
        root = kit.empty(f"Commuter | mitten {side}", col)
        root.rotation_mode = "QUATERNION"
        pts = [(x * 1.12, 0, z * 1.12) for x, z in contour]
        o = kit.mesh("Commuter | mitten ink", col, pts, [tuple(range(len(pts)))], hand_ink, root)
        o.visible_shadow = False
        cx = .042
        for dy in (-.0013, .0013):
            inner = [(cx + (x * 1.12 - cx) * .80, dy, z * 1.12 * .78) for x, z in contour]
            o = kit.mesh("Commuter | mitten cream", col, inner, [tuple(range(len(inner)))], face_mat, root)
            o.visible_shadow = False
        hands.append(root)
    coin_mat = kit.surface("Brass coin", "#e4b44c", .3, .85)
    coin = kit.cylinder("Coin", col, (0, 0, 0), COIN_R, .0035, coin_mat, length_segments=32)
    coin.rotation_mode = "QUATERNION"
    coin_ring = torus("Coin milled rim", (0, 0, 0), COIN_R - .002, .0012, kit.surface("Coin rim", "#b88a2e", .4, .8),
                      rot=(0, 0, 0), parent=coin, segs=32)
    pads = []
    for dy in (-.0042, .0042):
        pad = kit.empty("Pinch pad", col, (.088, dy, .006), hands[0])
        a = kit.ball("Pinch pad ink", col, (0, 0, 0), (.0095, .0008, .0075), hand_ink, pad, 14, 6)
        b = kit.ball("Pinch pad cream", col, (0, dy * .2, 0), (.0068, .0009, .0050), face_mat, pad, 14, 6)
        a.visible_shadow = b.visible_shadow = False
        pads.append(pad)
    COIN_LOCAL = Vector((.092, 0, .016))

    # Paper cup (origin at bottom centre), open top, painted stripe and rolled rim.
    paper = kit.surface("Paper cup white", "#f1ece2", .85)
    stripe = kit.surface("Paper cup blue stripe", "#2f66c8", .8)
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=CUP_RB, radius2=CUP_RT, depth=CUP_H, end_fill_type="NOTHING")
    cup = kit.put(bpy.context.object, col, None, paper)
    cup.name = "Paper cup"
    for v in cup.data.vertices:
        v.co.z += CUP_H / 2
    for p in cup.data.polygons:
        p.use_smooth = True
    cup.rotation_mode = "QUATERNION"
    ink(cup, 1.6)
    bpy.ops.mesh.primitive_circle_add(vertices=40, radius=CUP_RB, fill_type="NGON")
    bottom = kit.put(bpy.context.object, col, cup, paper)
    bottom.location.z = .002
    bpy.ops.mesh.primitive_cone_add(vertices=40, radius1=CUP_RB + (CUP_RT - CUP_RB) * .55 + .0015,
                                    radius2=CUP_RB + (CUP_RT - CUP_RB) * .78 + .0015, depth=.023,
                                    end_fill_type="NOTHING")
    band = kit.put(bpy.context.object, col, cup, stripe)
    band.location.z = .0665
    for p in band.data.polygons:
        p.use_smooth = True
    torus("Cup rolled rim", (0, 0, CUP_H), CUP_RT, .0035, paper, rot=(0, 0, 0), parent=cup, segs=40)

    # Spilled / delivered gumballs for shot 4.
    palette = ["#f2c230", "#3a9be0", "#5cc98a", "#f3eee2", "#8a5cd0", "#f08a2a"]
    balls_sim, frames_sim = simulate_spill()
    spill = []
    for i, b in enumerate(balls_sim):
        mat = red if i == 0 else kit.surface(f"Gumball {palette[i % len(palette)]}", palette[i % len(palette)], .3)
        obj = kit.ball("Spill | red gumball" if i == 0 else "Spill | gumball", col, MOUTH, (b["r"],) * 3, mat, None,
                       20 if i == 0 else 14, 12 if i == 0 else 9)
        ink(obj, 1.5 if i == 0 else 1.1)
        spill.append(obj)

    # Portrait lighting after environment lights.
    kit.setup_hero_portrait_lighting(hero.head, bg_dim=.68)

    # --------------------------------------------------------------------------------------
    lengths_ref = hero.measure_leg_lengths()
    stand_legs = [((side * .10, -.02, .027), (side * .095, -.06, .32)) for side in (-1, 1)]
    root_loc = Vector((HERO[0], HERO[1], 0))
    shoulder = {s: Vector((s * .106, -.003, .342)) for s in (-1, 1)}

    def body_matrix(bx, by, bz, tilt, lean, twist, squash=1.0):
        mr = Matrix.Translation(root_loc) @ Matrix.Rotation(ROOT_YAW, 4, "Z")
        mb = Matrix.Translation((bx, by, bz)) @ Euler((tilt, lean, twist)).to_matrix().to_4x4()
        mb = mb @ Matrix.Diagonal((1, 1, squash, 1))
        return mr @ mb

    def basis(d, up=(0, 0, 1)):
        X = Vector(d).normalized()
        Z = Vector(up) - X * X.dot(Vector(up))
        Z.normalize()
        Y = Z.cross(X)
        m = Matrix((X, Y, Z)).transposed()
        return m

    def elbow_for(side, hand_local, L=.37):
        s = shoulder[side]
        h = Vector(hand_local)
        mid = (s + h) / 2
        d = (h - s).length
        L = max(L, d + .035)
        off = math.sqrt(max(0.0, (L / 2) ** 2 - (d / 2) ** 2)) + .012
        out = Vector((side * .55, .25, -1.0))
        axis = (h - s).normalized()
        out = (out - axis * out.dot(axis)).normalized()
        return mid + out * off

    # Camera helpers.
    prev_q = [None]
    aim_state = [None]

    def place_camera(f, loc, target, lens, fstop, focus, roll=0.0):
        camera.location = loc
        kit.aim(camera, target)
        if roll:
            camera.rotation_quaternion = camera.rotation_quaternion @ Quaternion((0, 0, 1), roll)
        q = camera.rotation_quaternion
        if prev_q[0] is not None and q.dot(prev_q[0]) < 0:
            camera.rotation_quaternion = -q
        prev_q[0] = camera.rotation_quaternion.copy()
        camera.data.lens = lens
        camera.data.dof.aperture_fstop = fstop
        depth = -(camera.matrix_world.inverted() @ Vector(focus)).z
        bpy.context.view_layer.update()
        depth = -(camera.matrix_world.inverted() @ Vector(focus)).z
        camera.data.dof.focus_distance = max(.05, depth)
        camera.keyframe_insert("location", frame=f)
        camera.keyframe_insert("rotation_quaternion", frame=f)
        camera.data.keyframe_insert("lens", frame=f)
        camera.data.keyframe_insert("dof.aperture_fstop", frame=f)
        camera.data.keyframe_insert("dof.focus_distance", frame=f)

    def key_obj(obj, f, loc=None, quat=None, hidden=None):
        if loc is not None:
            obj.location = loc
            obj.keyframe_insert("location", frame=f)
        if quat is not None:
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = quat
            obj.keyframe_insert("rotation_quaternion", frame=f)
        if hidden is not None:
            obj.hide_render = obj.hide_viewport = hidden
            obj.keyframe_insert("hide_render", frame=f)
            obj.keyframe_insert("hide_viewport", frame=f)

    def hide_tree(obj, f, hidden):
        for o in (obj, *obj.children_recursive):
            key_obj(o, f, hidden=hidden)

    gx, gy, gz = GATE
    report = {"coin_grip_mm": [], "rail_contact_mm": [], "cup_catch": [], "cuts_zero_based": CUTS0}
    expression_now = [None]
    shoulder_world_cache = {}

    for f in range(1, END + 1):
        shot = 1 if f < S2 else 2 if f < S3 else 3 if f < S4 else 4
        # ------------------ character pose state (body-local hand targets) ------------------
        bx = by = 0.0
        bounce, tilt, lean, twist, squash = 0.0, 0.0, 0.0, 0.0, 1.0
        head_tilt, head_yaw = 0.0, 0.0
        expr = None
        coin_attached, coin_world = True, None
        cup_world = None          # (bottom centre, quaternion) in world when not body-held
        hand_world = {}           # side -> (wrist pos world, basis matrix world)
        hand_local = {}           # side -> (wrist pos body-local, basis body-local)

        if f < S4:
            # Shots 1-3: standing beside the machine, coin in near hand, cup in far hand.
            shift = ease(f, 4, 14) - .45 * ease(f, 14, 26)
            by = -.012 * ease(f, 4, 12)
            bx = .035 * shift - .015
            bounce = -.022 * math.sin(math.pi * clamp((f - 4) / 14))
            tilt = .02 + .10 * ease(f, 6, 16) + .05 * ease(f, 50, 64) + .04 * ease(f, 66, 80)
            twist = -.16 + .20 * ease(f, 6, 18) + .06 * ease(f, 48, 62)
            lean = -.03 * shift
            head_yaw = -.30 + .44 * ease(f, 7, 18) - .08 * ease(f, 26, 40) + .06 * ease(f, 50, 62)
            head_tilt = -.04 * ease(f, 7, 14) + .16 * ease(f, 24, 36) + .02 * ease(f, 50, 62)
            for frame_, e in ((1, "bored"), (9, "notice"), (25, "eager")):
                if f >= frame_:
                    expr = e
            # Cup held by the far mitten at the hip.
            cup_local = Vector((.17, -.15, -.10))
            hand_local[1] = (cup_local + Vector((.072, .045, .055)), basis((-.35, -1, 0)))
            mb = body_matrix(bx, by, .59 + bounce, tilt, lean, twist)
            mb_inv = mb.inverted()
            # Coin hand: rest -> raise -> start toward slot -> insert -> retract.
            rest = Vector((-.19, -.08, .05))
            show = Vector((-.07, -.27, .36))
            rest_b = basis((.25, -1, -.6))
            show_b = basis((.35, -1, .35))
            if f <= 58:
                u = ease(f, 20, 44)
                pos = rest.lerp(show, u) + Vector((0, 0, .015 * math.sin(math.pi * clamp((f - 44) / 14))))
                bas = rest_b.to_quaternion().slerp(show_b.to_quaternion(), u).to_matrix()
                hand_local[-1] = (pos, bas)
            else:
                # World-space approach to the slot (continues across the shot 1/2 cut).
                show_w = mb @ show
                pre = Vector(SLOT) + Vector((0, -.032 - COIN_LOCAL.x, -COIN_LOCAL.z))
                start_dir = (mb.to_3x3() @ show_b.col[0]).normalized()
                ins_dir = Vector((0, 1, 0))
                if f <= 77:
                    u = (f - 58) / (77 - 58)
                    k = 1 - (1 - u) ** 2.2                      # decelerate onto contact
                    arc = Vector((0, -.05 * math.sin(math.pi * k), .03 * math.sin(math.pi * k)))
                    wrist = show_w.lerp(pre, k) + arc
                    d = start_dir.lerp(ins_dir, smooth(k * 1.15)).normalized()
                elif f <= 79:
                    wrist, d = pre.copy(), ins_dir
                elif f <= 86:
                    u = ease(f, 79, 86)
                    wrist, d = pre + Vector((0, .026 * u, 0)), ins_dir
                else:
                    seat = pre + Vector((0, .026, 0))
                    u = ease(f, 87, 98)
                    away = seat + Vector((-.16, -.12, -.05))
                    wrist = seat.lerp(away, u) + Vector((0, -.01 * math.sin(math.pi * clamp((f - 86) / 3)), 0))
                    d = ins_dir.lerp(Vector((-.2, -1, -.3)), u).normalized()
                    coin_attached = False
                hand_world[-1] = (wrist, basis(d))
        else:
            # Shot 4: both mittens brace the cup under the spout.
            g = f
            cb = Vector(cup_pose(g))
            cup_world = (cb, Quaternion())
            # Recoil and reaction choreography.
            recoil = ease(g, 208, 213) - .75 * ease(g, 216, 236)
            lean_in = ease(g, 193, 203) * (1 - ease(g, 207, 211))
            tilt = .14 + .06 * lean_in - .24 * recoil + .05 * ease(g, 240, 256) - .05 * ease(g, 258, 280)
            bounce = -.018 * lean_in - .02 * recoil
            bx = -.02 * recoil
            twist = .02 - .03 * recoil - .06 * ease(g, 256, 282)
            head_tilt = (.34 + .06 * lean_in - .46 * ease(g, 208, 212) + .30 * ease(g, 214, 224)
                         + .28 * ease(g, 222, 244) - .58 * ease(g, 256, 282))
            head_yaw = -.05 - .05 * ease(g, 214, 230) - .58 * ease(g, 256, 282)
            squash = 1 + .05 * math.sin(math.pi * clamp((g - 208) / 5)) - .03 * math.sin(math.pi * clamp((g - 213) / 6))
            for frame_, e in ((S4, "hopeful"), (209, "shock"), (217, "shock_track"), (244, "deadpan_down"),
                              (266, "deadpan")):
                if g >= frame_:
                    expr = e
            mid = cb + Vector((0, 0, .055))
            hand_world[1] = (mid + Vector((-.055, .069, 0)), basis((1, -.10, 0)))
            hand_world[-1] = (mid + Vector((-.055, -.069, 0)), basis((1, .10, 0)))
            coin_attached = False

        mb = body_matrix(bx, by, .59 + bounce, tilt, lean, twist, squash)
        mb_inv = mb.inverted()
        mb3, mb3_inv = mb.to_3x3(), mb.inverted().to_3x3()
        for side, (pos, bas) in hand_local.items():
            hand_world[side] = (mb @ pos, mb3 @ bas)
        arms = []
        for side in (-1, 1):
            wpos, wbas = hand_world[side]
            local = mb_inv @ wpos
            arms.append((tuple(local), tuple(elbow_for(side, local))))
            q = wbas.to_quaternion()
            hand = hands[0 if side < 0 else 1]
            if hand.rotation_quaternion.dot(q) < 0:
                q = -q
            key_obj(hand, f, loc=wpos, quat=q)
        hero.body.location.x, hero.body.location.y = bx, by
        hero.body.rotation_euler.y, hero.body.rotation_euler.z = lean, twist
        e_arg = expr if expr != expression_now[0] else None
        expression_now[0] = expr
        hero.pose(f, tuple(root_loc), ROOT_YAW, tilt, arms, stand_legs, e_arg, bounce=bounce,
                  head_tilt=head_tilt, head_yaw=head_yaw, squash=squash, sweat=None, leg_lengths=lengths_ref)

        # Coin.
        wpos, wbas = hand_world[-1]
        if coin_attached:
            cpos = wpos + wbas @ COIN_LOCAL
            cq = wbas.to_quaternion() @ Quaternion((1, 0, 0), math.pi / 2)  # disc normal = hand Y
            key_obj(coin, f, loc=cpos, quat=cq)
            report["coin_grip_mm"].append(round((cpos - (wpos + wbas @ COIN_LOCAL)).length * 1000, 3))
        elif f < S4:
            seat_c = Vector(SLOT) + Vector((0, -.006, 0))
            u = ease(f, 87, 90)
            key_obj(coin, f, loc=seat_c + Vector((0, .05 * u, 0)), quat=basis((0, 1, 0)).to_quaternion()
                    @ Quaternion((1, 0, 0), math.pi / 2))
        coin_hidden = f >= 91
        hide_tree(coin, f, coin_hidden)
        for pad in pads:
            hide_tree(pad, f, not coin_attached)

        # Cup.
        if cup_world is None:
            cup_local = Vector((.17, -.15, -.10))
            cpos = mb @ (cup_local + Vector((0, 0, -CUP_H / 2)))
            key_obj(cup, f, loc=cpos, quat=mb3.to_quaternion())
        else:
            key_obj(cup, f, loc=cup_world[0], quat=cup_world[1])

        # Window ball, interior ball and spill balls.
        hide_tree(window_ball, f, f >= S3)
        if S3 <= f < S4:
            bp = interior_ball(f, points, lengths)
            key_obj(interior_ball_obj, f, loc=bp, hidden=False)
            if ROLL_A <= f <= TIP:
                d = min(min(math.dist(bp, q) for q in rails_l), min(math.dist(bp, q) for q in rails_r))
                report["rail_contact_mm"].append(round((d - BALL_R - .0043) * 1000, 2))
        else:
            key_obj(interior_ball_obj, f, loc=GATE if f < S3 else interior_ball(S4 - 1, points, lengths), hidden=True)
        for i, obj in enumerate(spill):
            if f >= S4:
                p, alive = frames_sim[f][i]
                key_obj(obj, f, loc=p, hidden=not alive)
            else:
                key_obj(obj, f, loc=MOUTH, hidden=True)
        if S4 <= f <= 206:
            p = Vector(frames_sim[f][0][0])
            cb = Vector(cup_pose(f))
            rel = p - cb
            report["cup_catch"].append({"frame": f, "radial_mm": round(math.hypot(rel.x, rel.y) * 1000, 1),
                                        "height_mm": round(rel.z * 1000, 1)})

        # Machine rumble + flap opening before the dump.
        shake = math.sin(f * 2.7) * .004 * clamp(1 - abs(f - 205) / 3) if 202 <= f <= 208 else 0.0
        key_obj(mroot, f, loc=(shake, 0, abs(shake) * .5))
        flap_pivot.rotation_euler.x = -1.1 * ease(f, 205, 208) if f >= S4 else 0
        flap_pivot.keyframe_insert("rotation_euler", frame=f)

        # ------------------ camera ------------------
        bpy.context.view_layer.update()
        head_w = hero.head.matrix_world.translation.copy()
        eyes = hero.head.matrix_world @ Vector((0, -.17, .03))
        if shot == 1:
            u = ease(f, 1, 70)
            loc = Vector((.85, -1.60, 1.25)).lerp(Vector((.15, -1.75, 1.19)), u)
            tgt = Vector((-.33, -.08, 1.10)).lerp(Vector((-.16, 0.0, 1.08)), u)
            place_camera(f, loc, tgt, 26, 2.0, eyes)
        elif shot == 2:
            slot = Vector(SLOT)
            cpos = coin.location.copy() if f < 91 else slot
            a = Vector((.20, -.235, .07)).lerp(Vector((.17, -.215, .05)), ease(f, S2, 86))
            front = Vector((0, -SLOT_END_D, 0))
            u = ease(f, 88, 105)
            off = a.lerp(front, u)
            off = off.normalized() * (a.length + (front.length - a.length) * u)
            focus = cpos.lerp(slot, ease(f, 74, 80))
            tgt = (cpos.lerp(slot, .45 + .55 * ease(f, 70, 80))).lerp(slot, u)
            place_camera(f, slot + off, tgt, 50, 4.0, focus.lerp(slot, u))
        elif shot == 3:
            bp = Vector(interior_ball(f, points, lengths))
            way = [(gx, gy - GATE_START_D, gz), (gx + .02, gy - .30, gz - .02), (gx + .20, gy - .60, gz - .08),
                   (gx + .30, gy - .76, gz - .16), (gx + .04, gy - .76, gz - .26), (gx - .04, gy - .72, gz - .30)]
            u = clamp((f - S3) / (S4 - 1 - S3))
            u = .35 * u + .65 * smooth(u)           # near-constant descending glide
            loc = Vector(catmull(way, u))
            gate = Vector(GATE)
            aim_at = Vector(interior_ball(min(f, STALL), points, lengths))
            if f == S3:
                aim_state[0] = gate.copy()
            aim_state[0] = aim_state[0].lerp(aim_at, .16 if f < ROLL_A + 6 else .22)
            tgt = gate.lerp(aim_state[0], ease(f, S3, 113))
            place_camera(f, loc, tgt, 28, 2.8, bp)
        else:
            cb = Vector(cup_pose(f))
            near = (Vector((.08, -.50, .68)), Vector((-.17, -.15, .61)))
            mid_ = (Vector((.05, -.56, .70)), Vector((-.18, -.15, .60)))
            far = (Vector((.36, -1.20, .86)), Vector((-.30, -.16, .72)))
            rest = (Vector((.33, -1.16, .84)), Vector((-.31, -.15, .73)))
            u1 = ease(f, S4, 206)
            loc, tgt = near[0].lerp(mid_[0], u1), near[1].lerp(mid_[1], u1)
            u2 = ease(f, 209, 252)
            loc, tgt = loc.lerp(far[0], u2), tgt.lerp(far[1], u2)
            u3 = ease(f, 250, 279)
            loc, tgt = loc.lerp(rest[0], u3), tgt.lerp(rest[1], u3)
            jolt = Vector((.006 * math.sin(f * 3.1), 0, .005 * math.cos(f * 2.3))) if 208 <= f <= 210 else Vector()
            focus = (cb + Vector((0, 0, .06))).lerp(eyes, ease(f, 212, 232))
            fstop = 2.2 + 2.3 * ease(f, 209, 252)
            place_camera(f, loc + jolt, tgt, 28 - 2 * ease(f, 209, 252), fstop, focus)

        bpy.context.view_layer.update()
        hero.update_ink(camera, pixels=4.2, frame=f)
        inv = camera.matrix_world.inverted()
        for obj, mod, px in prop_inks:
            center = obj.matrix_world @ (sum((Vector(c) for c in obj.bound_box), Vector()) / 8)
            depth = -(inv @ center).z
            if depth <= .02:
                depth = 1.0
            mod.strength = -clamp(depth * 36 * px / (camera.data.lens * 640), .0003, .008)
            mod.keyframe_insert("strength", frame=f)

    hero.finish_bake()

    def constant_visibility(obj):
        ad = obj.animation_data
        if ad and ad.action:
            for c in ad.action.fcurves:
                if c.data_path in {"hide_render", "hide_viewport"}:
                    for k in c.keyframe_points:
                        k.interpolation = "CONSTANT"
    for obj in scene.objects:
        constant_visibility(obj)
    # Cameras keyed every frame: linear between integer frames.
    for idblock in (camera, camera.data):
        for c in idblock.animation_data.action.fcurves:
            for k in c.keyframe_points:
                k.interpolation = "LINEAR"
    kit.look.install_shadow_policy(scene)
    scene.frame_set(1)
    report["cup_catch_last"] = report["cup_catch"][-1] if report["cup_catch"] else None
    late = [frames_sim[f] for f in range(285, END + 1)]
    jitter = 0.0
    for a, b in zip(late, late[1:]):
        for (pa, _), (pb, _) in zip(a, b):
            jitter = max(jitter, math.dist(pa, pb))
    report["spill_max_step_last_15_frames_mm"] = round(jitter * 1000, 2)
    report["spill_count"] = len(spill)
    floor_balls = sum(1 for p, alive in frames_sim[END] if alive and p[2] < BALL_R + .005)
    report["spill_on_floor_at_end"] = floor_balls
    report["spill_in_cup_at_end"] = sum(
        1 for p, alive in frames_sim[END] if alive and math.hypot(p[0] - cup_pose(END)[0], p[1] - cup_pose(END)[1]) < CUP_RT
        and cup_pose(END)[2] < p[2] < cup_pose(END)[2] + CUP_H + .03)
    return scene, report


# ----------------------------------------------------------------------------------------------
def worker(mode, args):
    import bpy
    sys.path[:0] = [str(ROOT / "scripts")]
    import shorts_preflight as gate

    if mode == "proof":
        scene, report = build()
        OUT.mkdir(parents=True, exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = "//frames/frame_"
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
        rc = report
        rc["coin_grip_mm_max"] = max(report.pop("coin_grip_mm")) if report.get("coin_grip_mm") else None
        rails = report.pop("rail_contact_mm")
        rc["rail_contact_gap_mm"] = {"min": min(rails), "max": max(rails), "samples": len(rails)}
        (OUT / "build_report.json").write_text(json.dumps(rc, indent=2), encoding="utf-8")
        # Reopen check and benchmark from the saved file.
        bpy.ops.wm.open_mainfile(filepath=str(BLEND))
        scene = bpy.context.scene
        assets = gate.validate_resources(scene)
        print("ASSETS", json.dumps(assets))
        bench = OUT / args[0] if args else OUT / "benchmark"
        result = gate.benchmark(scene, BENCH, bench, resolution=(*SIZE, 100))
        print("BENCH", result["status"], result["p95_seconds"], result["max_seconds"], result["sampled_board_peak_gib"])
    elif mode == "stills":
        scene = bpy.context.scene
        folder = OUT / args[0]
        folder.mkdir(parents=True, exist_ok=True)
        for fr in map(int, args[1:]):
            scene.frame_set(fr)
            scene.render.filepath = str(folder / f"frame_{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
    elif mode == "render":
        scene = bpy.context.scene
        (OUT / "frames").mkdir(exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(OUT / "frames/frame_")
        bpy.ops.render.render(animation=True)


def main():
    mode, rest = sys.argv[1], sys.argv[2:]
    lock, owner = ROOT / ".blender_gpu.lock", uuid4().hex
    try:
        with lock.open("x", encoding="utf-8") as fh:
            json.dump({"project": "last_gumball/v01", "pid": os.getpid(), "owner": owner}, fh)
    except FileExistsError:
        raise SystemExit(f"GPU busy. Wait for the owner of {lock}.")
    try:
        cmd = [os.environ.get("BLENDER_EXE", BLENDER), "-b", "--factory-startup"]
        if mode != "proof":
            cmd.append(str(BLEND))
        subprocess.run([*cmd, "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
                        "--", mode, *rest], check=True, cwd=ROOT)
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("owner") == owner:
            lock.unlink()


if __name__ == "__main__":
    if "--" in sys.argv:
        sys.path[:0] = [str(ROOT / "scripts")]
        i = sys.argv.index("--")
        worker(sys.argv[i + 1], sys.argv[i + 2:])
    else:
        main()
