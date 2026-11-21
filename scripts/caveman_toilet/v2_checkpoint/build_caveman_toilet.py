"""caveman_toilet v2 orchestrator: 18 cuts, baked per-frame rig solver,
3 sets, 4-act grade, single top HUD pill (PIL post-overlay).

Blender 4.2 EEVEE Next, raytracing off, simplify subdiv 2 (4 GB VRAM).
Phases (after --): build | sheet <w> <h> <samples> [tag] | master <s> <e> <w> <h> [tag].
Saves renders/caveman_toilet/caveman_toilet.blend + repo-root copy.
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector, Quaternion

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v2_common import (ROOT, OUT, SPR, FPS, END, log, bake, hide_keys,
                       mat_world, mat_ink, cel_mat, shadow_mat, empty,
                       add_card, sphere, limb_curve, ik2, cam_quat)
from v2_story import (CUTS, SHEET_FRAMES, HUD_TEXTS, pose_state, camera_at,
                      cut_at, act_for_frame, set_for_frame)
import v2_sets
import v2_fx

EXPRS = ["neutral", "confused", "clenched", "strain", "relieved", "panic",
         "sneaky", "sick", "knockout", "inspired", "stern", "determined",
         "triumphant"]
CHARS = ("caveman", "buddy", "elder")
BOUNDS = sorted({c[1] for c in CUTS} | {END})


# ================= character rig =================
def build_char(char):
    root = empty(f"root_{char}")
    torso = add_card(f"torso_{char}", SPR / f"v2torso_{char}.png", 0.56, 0.86,
                     (0, 0, 0.8), parent=root,
                     mat=cel_mat(f"torso_{char}_mat", SPR / f"v2torso_{char}.png",
                                 emit=1.8, normals=True), flat=False)
    headpivot = empty(f"headpivot_{char}", parent=root)
    heads = {}
    for expr in EXPRS:
        img = SPR / f"v2head_{char}_{expr}.png"
        h = add_card(f"head_{char}_{expr}", img, 0.66, 0.66, (0, 0, 0),
                     parent=headpivot,
                     mat=cel_mat(f"head_{char}_{expr}_mat", img, emit=1.8, normals=True),
                     flat=False)
        h.hide_render = True
        heads[expr] = h
    limbs = {}
    ink = mat_ink()
    for side in (-1, 1):
        arm, ah = limb_curve(f"arm_{char}_{side}", parent=root, depth=0.026)
        leg, lh = limb_curve(f"leg_{char}_{side}", parent=root, depth=0.030)
        hand = sphere(f"hand_{char}_{side}", (0, 0, 0), 0.0325, ink, parent=root)
        foot = sphere(f"foot_{char}_{side}", (0, 0, 0), 0.0325, ink,
                      scale=(1.2, 1.4, 0.7), parent=root)
        limbs[side] = dict(arm=arm, ah=ah, leg=leg, lh=lh, hand=hand, foot=foot)
    shmat = shadow_mat(f"shadow_{char}", SPR / "tex_shadow.png")
    footsh = []
    for side in (-1, 1):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.012))
        d = bpy.context.active_object
        d.name = f"footshadow_{char}_{side}"
        d.scale = (0.30, 0.30, 1)
        d.data.materials.append(shmat)
        d.visible_shadow = False
        d.parent = root
        footsh.append(d)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.011))
    bs = bpy.context.active_object
    bs.name = f"bodyshadow_{char}"
    bs.scale = (0.60, 0.34, 1)
    bs.data.materials.append(shmat)
    bs.visible_shadow = False
    bs.parent = root
    objs = [torso, headpivot] + list(heads.values()) + [bs] + footsh
    for side in (-1, 1):
        L = limbs[side]
        objs += [L["arm"], L["leg"], L["hand"], L["foot"]] + L["ah"] + L["lh"]
    return dict(root=root, torso=torso, headpivot=headpivot, heads=heads,
                limbs=limbs, footsh=footsh, bodyshadow=bs, objs=objs)


def rig_solve(st, cam_pos):
    """World-space rig points from a story pose state."""
    P = Vector(st["pelvis"])
    fc = st["facing"]
    facing = Vector((fc[0], fc[1], 0.0))
    axis = Vector((-fc[1], fc[0], 0.0))
    R = Quaternion(axis, st["lean"]) if axis.length > 1e-6 else Quaternion()

    def L(off):
        return P + R @ Vector(off)

    torso_c = L((0, 0, 0.30))
    head_c = L((0, 0, 0.80))
    cd = Vector(cam_pos) - P
    cd.z = 0
    if cd.length > 1e-6:
        cd.normalize()
        head_c += cd * 0.06
    head_c.z -= st["shoulder_drop"]
    yaw = math.atan2(cam_pos[0] - P.x, -(cam_pos[1] - P.y))
    torso_q = Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), math.pi / 2 + st["lean"])
    head_q = R @ (Vector(cam_pos) - head_c).to_track_quat("Z", "Y") @ \
        Quaternion((0, 0, 1), st["tilt"])
    shoulders = [L((-0.21, 0, 0.57)), L((0.21, 0, 0.57))]
    hips = [L((-0.09, 0, 0.02)), L((0.09, 0, 0.02))]
    perp = Vector((-fc[1], fc[0], 0.0))
    knee_in = st.get("knee_in", 0.0)
    arms, legs = [], []
    for idx, side in enumerate((-1, 1)):
        sh, hip = shoulders[idx], hips[idx]
        hand = Vector(st["hands"][idx])
        foot = Vector(st["feet"][idx][:3])
        elbow_pole = sh + perp * (side * 0.6) - facing * 0.4
        elbow = ik2(sh, hand, 0.26, 0.26, elbow_pole)
        knee_pole = hip + facing * (0.5 - 0.3 * knee_in) - perp * (side * 0.3 * knee_in) + Vector((0, 0, 0.3))
        knee = ik2(hip, foot, 0.29, 0.29, knee_pole)
        arms.append((sh, elbow, hand))
        legs.append((hip, knee, foot))
    foot_q = []
    for idx, side in enumerate((-1, 1)):
        pitch = st["feet"][idx][3]
        foot_q.append(Quaternion(axis, pitch))
    return dict(torso_c=torso_c, torso_q=torso_q, head_c=head_c, head_q=head_q,
                arms=arms, legs=legs, foot_q=foot_q, P=P)


def bake_char(ch, char, frames):
    """Bake every rig fcurve for one character across the timeline."""
    n = len(frames)
    acc = {k: [] for k in ("torso_c", "torso_q", "head_c", "head_q",
                           "hand0", "hand1", "foot0", "foot1", "footq0", "footq1",
                           "sh0", "sh1", "bs")}
    for side in (-1, 1):
        for j in range(3):
            acc[f"a{side}_{j}"] = []
            acc[f"l{side}_{j}"] = []
    active_expr = []
    for f in frames:
        st = pose_state(char, f)
        if st is None:
            active_expr.append(None)
            qkeys = {"torso_q", "head_q", "footq0", "footq1"}
            for k in acc:
                default = (0, 0, 0, 1) if k in qkeys else (0, 0, 0)
                acc[k].append(acc[k][-1] if acc[k] else default)
            continue
        cam_pos, _, _ = camera_at(f)
        r = rig_solve(st, cam_pos)
        active_expr.append(st["expr"])
        acc["torso_c"].append(tuple(r["torso_c"]))
        acc["torso_q"].append(tuple(r["torso_q"]))
        acc["head_c"].append(tuple(r["head_c"]))
        acc["head_q"].append(tuple(r["head_q"]))
        for idx, side in enumerate((-1, 1)):
            for j in range(3):
                acc[f"a{side}_{j}"].append(tuple(r["arms"][idx][j]))
                acc[f"l{side}_{j}"].append(tuple(r["legs"][idx][j]))
            acc[f"hand{idx}"].append(tuple(r["arms"][idx][2]))
            acc[f"foot{idx}"].append(tuple(r["legs"][idx][2]))
            acc[f"footq{idx}"].append(tuple(r["foot_q"][idx]))
            acc[f"sh{idx}"].append((r["legs"][idx][2].x, r["legs"][idx][2].y, 0.012))
        acc["bs"].append((r["P"].x, r["P"].y, 0.011))
    bake(ch["torso"], "location", frames, acc["torso_c"])
    bake(ch["torso"], "rotation_quaternion", frames, acc["torso_q"])
    bake(ch["headpivot"], "location", frames, acc["head_c"])
    bake(ch["headpivot"], "rotation_quaternion", frames, acc["head_q"])
    for idx, side in enumerate((-1, 1)):
        L = ch["limbs"][side]
        for j in range(3):
            bake(L["ah"][j], "location", frames, acc[f"a{side}_{j}"])
            bake(L["lh"][j], "location", frames, acc[f"l{side}_{j}"])
        bake(L["hand"], "location", frames, acc[f"hand{idx}"])
        bake(L["foot"], "location", frames, acc[f"foot{idx}"])
        bake(L["foot"], "rotation_quaternion", frames, acc[f"footq{idx}"])
        bake(ch["footsh"][idx], "location", frames, acc[f"sh{idx}"])
    bake(ch["bodyshadow"], "location", frames, acc["bs"])
    return active_expr


def bake_camera(cam, frames):
    locs, quats, lens, focus = [], [], [], []
    for f in frames:
        pos, look, ln = camera_at(f)
        locs.append(pos)
        quats.append(tuple(cam_quat(pos, look)))
        lens.append(ln)
        focus.append((Vector(look) - Vector(pos)).length)
    bake(cam, "location", frames, locs)
    bake(cam, "rotation_quaternion", frames, quats)
    fc = bake(cam.data, "lens", frames, lens)
    for kp in fc.keyframe_points:
        kp.interpolation = "CONSTANT"
    bake(cam.data, "dof.focus_distance", frames, focus)# ================= scene assembly =================
def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.use_raytracing = False
    try:
        sc.eevee.use_fast_gi = True
    except Exception:
        pass
    sc.render.use_simplify = True
    sc.render.simplify_subdivision = 2
    sc.render.resolution_x = 540
    sc.render.resolution_y = 960
    sc.render.fps = FPS
    sc.frame_start = 1
    sc.frame_end = END
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    bpy.data.textures.new("rock_noise", "CLOUDS").noise_scale = 0.6
    wnt, ramp, bg = v2_sets.build_world(sc)
    v2_sets.key_sky(wnt, ramp, bg)
    camdata = bpy.data.cameras.new("Camera")
    camdata.sensor_fit = "HORIZONTAL"
    camdata.sensor_width = 36
    camdata.dof.use_dof = True
    camdata.dof.aperture_fstop = 2.5
    cam = bpy.data.objects.new("Camera", camdata)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    cam.rotation_mode = "QUATERNION"
    A = v2_sets.build_set_A()
    B, flames = v2_sets.build_set_B()
    C, lat = v2_sets.build_set_C()
    fg = v2_sets.build_fg_silhouettes(cam)
    lights = v2_sets.build_lights()
    chars = {c: build_char(c) for c in CHARS}
    for c in CHARS:
        chars[c]["torso"].rotation_mode = "QUATERNION"
        chars[c]["headpivot"].rotation_mode = "QUATERNION"
        for side in (-1, 1):
            chars[c]["limbs"][side]["foot"].rotation_mode = "QUATERNION"
    fx = v2_fx.build_fx(cam)
    frames = list(range(1, END + 1))
    idx_of = {f: i for i, f in enumerate(frames)}
    log("baking characters...")
    active = {}
    for c in CHARS:
        active[c] = bake_char(chars[c], c, frames)
    log("baking camera...")
    bake_camera(cam, frames)
    log("baking fx...")
    v2_fx.bake_fx(fx, frames)
    v2_fx.fx_visibility(fx)
    # ---- visibility at cut boundaries ----
    sets = {"A": A, "B": B, "C": C}
    for sn, root in sets.items():
        hid = [set_for_frame(f) != sn for f in BOUNDS]
        for t in [root] + list(root.children_recursive):
            hide_keys(t, BOUNDS, hid)
    hid = [set_for_frame(f) != "A" for f in BOUNDS]
    for t in [fg] + list(fg.children_recursive):
        hide_keys(t, BOUNDS, hid)
    hid = [cut_at(f)[0] != 18 for f in BOUNDS]
    for t in [lat] + list(lat.children_recursive):
        hide_keys(t, BOUNDS, hid)
    for name, ob in lights.items():
        if name in ("camp", "cavefill"):
            hid = [set_for_frame(f) != "B" for f in BOUNDS]
        else:
            acts = v2_sets.LIGHT_ACTS[name]
            hid = [act_for_frame(f) not in acts for f in BOUNDS]
        hide_keys(ob, BOUNDS, hid)
    # ---- characters: presence + combined head expression keys ----
    for c in CHARS:
        ch = chars[c]
        ae = active[c]
        sig = [(c in cut_at(f)[5], ae[i]) for i, f in enumerate(frames)]
        changes = [frames[0]] + [frames[i] for i in range(1, len(frames))
                                 if sig[i] != sig[i - 1]]
        headset = set(ch["heads"].values())
        for expr, hob in ch["heads"].items():
            hid = [not (sig[idx_of[f]][0] and sig[idx_of[f]][1] == expr)
                   for f in changes]
            hide_keys(hob, changes, hid)
        hid = [c not in cut_at(f)[5] for f in BOUNDS]
        for t in ch["objs"]:
            if t in headset:
                continue
            hide_keys(t, BOUNDS, hid)
    v2_sets.build_compositor(sc)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "caveman_toilet.blend"))
    import shutil
    shutil.copyfile(str(OUT / "caveman_toilet.blend"), str(ROOT / "caveman_toilet.blend"))
    log(f"scene built: {len(bpy.data.objects)} objects, END={END}")


def do_sheet(w, h, samples, tag="v2"):
    import time
    bpy.ops.wm.open_mainfile(filepath=str(OUT / "caveman_toilet.blend"))
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.eevee.taa_render_samples = samples
    fr = OUT / f"calibration_{tag}"
    fr.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    for i, f in enumerate(SHEET_FRAMES):
        sc.frame_set(f)
        sc.render.filepath = str(fr / f"tile_{i:02d}_f{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        log(f"tile {i + 1}/16 f{f} elapsed {time.time() - t0:.1f}s")
    log(f"sheet {len(SHEET_FRAMES)} tiles at {w}x{h} samples={samples} tag={tag}")


def do_video(start, end, w, h, tag="v2"):
    import time
    bpy.ops.wm.open_mainfile(filepath=str(OUT / "caveman_toilet.blend"))
    sc = bpy.context.scene
    sc.render.resolution_x = w
    sc.render.resolution_y = h
    sc.eevee.taa_render_samples = 16 if w <= 540 else 24
    fr = OUT / f"frames_{tag}"
    fr.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    total = end - start + 1
    for i, f in enumerate(range(start, end + 1)):
        sc.frame_set(f)
        sc.render.filepath = str(fr / f"f{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        if (i + 1) % 30 == 0 or i + 1 == total:
            el = time.time() - t0
            eta = el / (i + 1) * (total - i - 1)
            log(f"frame {f} ({i + 1}/{total}) elapsed {el:.0f}s ETA {eta:.0f}s")
    log(f"video frames {start}..{end} complete tag={tag}")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    phase = args[0] if args else "build"
    rest = args[1:]
    if phase == "sheet":
        do_sheet(int(rest[0]), int(rest[1]), int(rest[2]),
                 rest[3] if len(rest) > 3 else "v2")
    elif phase == "master":
        do_video(int(rest[0]), int(rest[1]),
                 int(rest[2]) if len(rest) > 2 else 540,
                 int(rest[3]) if len(rest) > 3 else 960,
                 rest[4] if len(rest) > 4 else "v2")
    else:
        build_scene()