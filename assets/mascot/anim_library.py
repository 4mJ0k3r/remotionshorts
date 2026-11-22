"""Parameterized 18-animation library for the Official Mascot (`assets/mascot/`).

All 18 animations follow Rick's Clips v6 animation laws:
  - Smooth quintic S-curves (`ease5`) and 6-stage acting envelopes
    (Notice -> Wind-up -> Strike -> Hit -> Settle -> STILL, zero robotic wobble).
  - Exact world-space planted feet during stance (`0.000 m` foot skating), even
    while the root shifts weight or twists `yaw`.
  - Chibi squash/stretch, vertical stride bob, and damped secondary motion on
    the hoodie drawstrings (`string_sway`).
  - Safe to import in pure CPU Python (Blender `bpy` is only required when
    constructing 3D helper props/aura or querying scene cameras/matrices).
"""
from __future__ import annotations

import inspect
import math
from typing import Any

try:
    import bpy
    from mathutils import Euler, Matrix, Vector
except ModuleNotFoundError as exc:
    if exc.name not in {"bpy", "mathutils"}:
        raise
    bpy = None
    Euler = Matrix = Vector = None


ANIMATION_NAMES: tuple[str, ...] = (
    "idle_breathe",
    "walk_to",
    "run_panic_to",
    "sneak_to",
    "stop_hold_up",
    "power_aura_stance",
    "chill_chair_lean",
    "talk_explain",
    "point_at_camera_wink",
    "shrug_idk",
    "jump_parabolic",
    "celebrate_hype",
    "facepalm_groan",
    "take_hit_recoil",
    "phone_scroll_zombie",
    "pickup_and_present",
    "throw_prop_at",
    "dramatic_double_take",
)

# Default standing geometry constants matching `mascot_api.py`
STANCE_X = 0.105
BODY_PIVOT_Z = 0.56
HEAD_OFFSET_Z = 0.40
HEAD_CENTER_Z = BODY_PIVOT_Z + HEAD_OFFSET_Z  # 0.96 m
SHOULDER_X = 0.155
SHOULDER_Z = 0.18
REST_ARM_L = ((-0.22, -0.06, -0.06), (-0.21, 0.02, 0.07))
REST_ARM_R = ((+0.22, -0.06, -0.06), (+0.21, 0.02, 0.07))


# ---------------------------------------------------------------------------
# Pure-Python easing, vector, and foot-pinning math
# ---------------------------------------------------------------------------
def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if x < lo else (hi if x > hi else x)


def ease5(u: float) -> float:
    """Quintic smoothstep: zero 1st and 2nd derivatives at u=0 and u=1."""
    u = clamp(u, 0.0, 1.0)
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def vlerp(a: tuple[float, ...], b: tuple[float, ...], t: float) -> tuple[float, ...]:
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def arm_lerp(
    arm_a: tuple[tuple[float, float, float], tuple[float, float, float]],
    arm_b: tuple[tuple[float, float, float], tuple[float, float, float]],
    t: float,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    return (vlerp(arm_a[0], arm_b[0], t), vlerp(arm_a[1], arm_b[1], t))


def bell(u: float) -> float:
    """Smooth zero-slope bell pulse on [0, 1], peaking at 1.0 at u=0.5."""
    u = clamp(u, 0.0, 1.0)
    s = math.sin(math.pi * u)
    return s * s


def six_stage_envelope(
    frame: int,
    f0: int,
    f1: int,
    *,
    windup_dip: float = -0.14,
    max_act_frames: float = 20.0,
) -> float:
    """Notice -> Wind-up -> Strike -> Hit -> Settle -> STILL without overshoot.

    For very short ranges (`f1 - f0 < 6`), immediately returns `1.0` so single-frame
    pose renders capture the settled hero silhouette. For longer holds, completes
    the strike/settle within `max_act_frames` so both `(f0 + f1) // 2` and `f1`
    sit cleanly in the settled hero pose.
    """
    span = f1 - f0
    if span < 6:
        return 1.0
    act = min(float(span), max_act_frames)
    s = (frame - f0) / act
    if s <= 0.10:
        return 0.0
    if s <= 0.28:
        return windup_dip * ease5((s - 0.10) / 0.18)
    if s <= 0.68:
        return lerp(windup_dip, 1.0, ease5((s - 0.28) / 0.40))
    return 1.0


def _validate_range(f0: int, f1: int) -> tuple[int, int]:
    f0, f1 = int(f0), int(f1)
    if f1 < f0:
        raise ValueError(f"Animation end frame f1 ({f1}) must be >= f0 ({f0}).")
    return f0, f1


def _heading_from_delta(dx: float, dy: float, fallback: float = 0.0) -> float:
    """Rig faces -Y at yaw=0; R_z(yaw) @ (0, -1) = (+sin(yaw), -cos(yaw))."""
    if math.hypot(dx, dy) < 1e-6:
        return float(fallback)
    return math.atan2(dx, -dy)


def _wrap_angle(rad: float) -> float:
    return (rad + math.pi) % math.tau - math.pi


def local_to_world_point(
    origin_xyz: tuple[float, float, float],
    yaw: float,
    local_xyz: tuple[float, float, float],
) -> tuple[float, float, float]:
    c, s = math.cos(yaw), math.sin(yaw)
    lx, ly, lz = local_xyz
    return (
        origin_xyz[0] + c * lx - s * ly,
        origin_xyz[1] + s * lx + c * ly,
        origin_xyz[2] + lz,
    )


def world_to_root_local(
    world_xyz: tuple[float, float, float],
    root_xyz: tuple[float, float, float],
    root_yaw: float,
) -> tuple[float, float, float]:
    """Exact inverse of R_z(root_yaw) + root_xyz so world feet stay 0.000 m pinned."""
    dx = world_xyz[0] - root_xyz[0]
    dy = world_xyz[1] - root_xyz[1]
    dz = world_xyz[2] - root_xyz[2]
    c, s = math.cos(root_yaw), math.sin(root_yaw)
    return (c * dx + s * dy, -s * dx + c * dy, dz)


def pinned_leg_pair(
    foot_L_world: tuple[float, float, float],
    foot_R_world: tuple[float, float, float],
    cur_loc: tuple[float, float, float],
    cur_yaw: float,
    *,
    knee_fwd: float = -0.075,
    knee_out: float = 0.015,
    knee_z: float = 0.19,
) -> tuple[
    tuple[tuple[float, float, float], tuple[float, float, float]],
    tuple[tuple[float, float, float], tuple[float, float, float]],
]:
    """Compute root-local `(foot, knee)` pairs for world-pinned feet."""
    fl = world_to_root_local(foot_L_world, cur_loc, cur_yaw)
    fr = world_to_root_local(foot_R_world, cur_loc, cur_yaw)
    kl = (0.55 * (-STANCE_X) + 0.45 * fl[0] - knee_out, min(-0.04, 0.45 * fl[1] + knee_fwd), knee_z + 0.45 * max(0.0, fl[2]))
    kr = (0.55 * (+STANCE_X) + 0.45 * fr[0] + knee_out, min(-0.04, 0.45 * fr[1] + knee_fwd), knee_z + 0.45 * max(0.0, fr[2]))
    return (fl, kl), (fr, kr)


def _aim_angles_toward(
    origin_loc: tuple[float, float, float],
    origin_yaw: float,
    target_xyz: tuple[float, float, float],
    eye_height: float = HEAD_CENTER_Z,
) -> tuple[float, float]:
    """Return `(rel_yaw, rel_pitch)` from head center toward `target_xyz`.

    With local -Y forward:
      - `rel_yaw > 0` turns toward local +X (viewer-right).
      - `rel_pitch < 0` tilts face UP (+Z); `rel_pitch > 0` tilts face DOWN (-Z).
    """
    local_t = world_to_root_local(
        target_xyz,
        (origin_loc[0], origin_loc[1], origin_loc[2] + eye_height),
        origin_yaw,
    )
    rel_yaw = _wrap_angle(math.atan2(local_t[0], -local_t[1]))
    horiz = max(0.18, math.hypot(local_t[0], local_t[1]))
    rel_pitch = -math.atan2(local_t[2], horiz)
    return (
        clamp(rel_yaw, -1.10, 1.10),
        clamp(rel_pitch, -0.62, 0.62),
    )


def compute_string_sway_series(
    frames: list[int],
    locs: list[tuple[float, float, float]],
    bounces: list[float],
    body_tilts: list[float],
    body_rolls: list[float],
    yaws: list[float],
) -> list[tuple[float, float]]:
    """Critically damped 2D pendulum secondary motion `(sway_x, sway_y)` in radians."""
    n = len(frames)
    if n == 0:
        return []
    sx, sy = 0.0, 0.0
    vx, vy = 0.0, 0.0
    omega = 0.62
    damping = 0.58
    out: list[tuple[float, float]] = []
    for i in range(n):
        if 0 < i < n - 1:
            ax = locs[i + 1][0] - 2.0 * locs[i][0] + locs[i - 1][0]
            ay = locs[i + 1][1] - 2.0 * locs[i][1] + locs[i - 1][1]
            az = (locs[i + 1][2] + bounces[i + 1]) - 2.0 * (locs[i][2] + bounces[i]) + (locs[i - 1][2] + bounces[i - 1])
            dyaw = _wrap_angle(yaws[i + 1] - yaws[i - 1]) * 0.5
            droll = (body_rolls[i + 1] - body_rolls[i - 1]) * 0.5
            dtilt = (body_tilts[i + 1] - body_tilts[i - 1]) * 0.5
        else:
            ax = ay = az = dyaw = droll = dtilt = 0.0

        c, s = math.cos(yaws[i]), math.sin(yaws[i])
        lat_acc = c * ax + s * ay
        fwd_acc = -s * ax + c * ay

        target_x = clamp(-3.2 * lat_acc - 0.55 * dyaw + 0.45 * body_rolls[i] + 0.30 * droll, -0.45, 0.45)
        target_y = clamp(2.6 * fwd_acc - 1.8 * az + 0.55 * max(0.0, body_tilts[i]) + 0.35 * dtilt, -0.38, 0.45)

        for _ in range(3):
            fx = omega * omega * (target_x - sx) - 2.0 * damping * omega * vx
            fy = omega * omega * (target_y - sy) - 2.0 * damping * omega * vy
            vx += fx / 3.0
            vy += fy / 3.0
            sx += vx / 3.0
            sy += vy / 3.0
        out.append((round(clamp(sx, -0.48, 0.48), 5), round(clamp(sy, -0.48, 0.48), 5)))
    return out


# ---------------------------------------------------------------------------
# Rig pose adapter (keeps every animation channel clean across sequential beats)
# ---------------------------------------------------------------------------
_POSE_SWAY_STYLE_CACHE: dict[type, str] = {}


def _detect_sway_style(hero: Any) -> str:
    cls = type(hero)
    if cls in _POSE_SWAY_STYLE_CACHE:
        return _POSE_SWAY_STYLE_CACHE[cls]
    style = "tuple2"
    try:
        src = inspect.getsource(hero.pose)
        if "float(string_sway)" in src and "isinstance(string_sway" not in src:
            style = "float"
    except (OSError, TypeError):
        pass
    _POSE_SWAY_STYLE_CACHE[cls] = style
    return style


def _format_sway(hero: Any, sway_xy: tuple[float, float]) -> Any:
    if _detect_sway_style(hero) == "float":
        return float(sway_xy[0])
    return sway_xy


def _apply_pose_series(hero: Any, records: list[dict[str, Any]]) -> None:
    """Bake a list of per-frame pose dicts with automatic secondary `string_sway`."""
    if not records:
        return
    frames = [r["frame"] for r in records]
    locs = [tuple(float(c) for c in r.get("loc", (0.0, 0.0, 0.0))) for r in records]
    bounces = [float(r.get("bounce", 0.0)) for r in records]
    tilts = [float(r.get("body_tilt", 0.0)) for r in records]
    rolls = [float(r.get("body_roll", 0.0)) for r in records]
    yaws = [float(r.get("yaw", 0.0)) for r in records]
    auto_sways = compute_string_sway_series(frames, locs, bounces, tilts, rolls, yaws)

    for rec, auto_sway in zip(records, auto_sways):
        sway = rec.get("string_sway")
        if sway is None:
            sway = _format_sway(hero, auto_sway)
        elif isinstance(sway, tuple) and _detect_sway_style(hero) == "float":
            sway = float(sway[0])

        hero.pose(
            rec["frame"],
            loc=tuple(float(c) for c in rec.get("loc", (0.0, 0.0, 0.0))),
            yaw=float(rec.get("yaw", 0.0)),
            body_tilt=float(rec.get("body_tilt", 0.0)),
            body_roll=float(rec.get("body_roll", 0.0)),
            bounce=float(rec.get("bounce", 0.0)),
            squash=float(rec.get("squash", 1.0)),
            head_yaw=float(rec.get("head_yaw", 0.0)),
            head_pitch=float(rec.get("head_pitch", 0.0)),
            head_roll=float(rec.get("head_roll", 0.0)),
            arm_L=rec.get("arm_L", REST_ARM_L),
            arm_R=rec.get("arm_R", REST_ARM_R),
            leg_L=rec.get("leg_L"),
            leg_R=rec.get("leg_R"),
            hand_L=rec.get("hand_L", "relaxed_curl"),
            hand_R=rec.get("hand_R", "relaxed_curl"),
            hand_rot_L=rec.get("hand_rot_L", (0.0, 0.0, 0.0)),
            hand_rot_R=rec.get("hand_rot_R", (0.0, 0.0, 0.0)),
            foot_rot_L=rec.get("foot_rot_L", (0.0, 0.0, 0.0)),
            foot_rot_R=rec.get("foot_rot_R", (0.0, 0.0, 0.0)),
            string_sway=sway,
            expr=rec.get("expr"),
        )


# ---------------------------------------------------------------------------
# Discrete world-pinned biped stride planner (0.000 m skating!)
# ---------------------------------------------------------------------------
def plan_biped_locomotion(
    f0: int,
    f1: int,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
    *,
    ground_z: float = 0.0,
    target_step_frames: int = 9,
    max_stride_m: float = 0.34,
    stance_x: float = STANCE_X,
    lift_height: float = 0.11,
) -> dict[str, Any]:
    """Plan alternating L/R footsteps with exact world-space stance pinning.

    Returns per-frame dictionaries containing:
      - `root_xyz`, `yaw`
      - `foot_L_world`, `foot_R_world`
      - `planted_L`, `planted_R` (booleans)
      - `swing_phase` (-1..+1 signed arm/stride phase)
      - `step_bob` (0..1 vertical stride bounce factor)
      - `stance_windows_L`, `stance_windows_R` (lists of `(a, b)` inclusive frame spans)
    """
    f0, f1 = _validate_range(f0, f1)
    x0, y0 = float(start_xy[0]), float(start_xy[1])
    x1, y1 = float(end_xy[0]), float(end_xy[1])
    gz = float(ground_z)
    dx, dy = x1 - x0, y1 - y0
    dist = math.hypot(dx, dy)
    yaw = _heading_from_delta(dx, dy, fallback=0.0)

    start_L = local_to_world_point((x0, y0, gz), yaw, (-stance_x, 0.0, 0.0))
    start_R = local_to_world_point((x0, y0, gz), yaw, (+stance_x, 0.0, 0.0))
    end_L = local_to_world_point((x1, y1, gz), yaw, (-stance_x, 0.0, 0.0))
    end_R = local_to_world_point((x1, y1, gz), yaw, (+stance_x, 0.0, 0.0))

    total = f1 - f0
    if total < 4 or dist < 1e-4:
        frames_out = []
        for f in range(f0, f1 + 1):
            frames_out.append({
                "frame": f,
                "root_xyz": (x1, y1, gz),
                "yaw": yaw,
                "foot_L_world": end_L,
                "foot_R_world": end_R,
                "planted_L": True,
                "planted_R": True,
                "swing_u_L": 0.0,
                "swing_u_R": 0.0,
                "swing_phase": 0.0,
                "step_bob": 0.0,
            })
        return {
            "yaw": yaw,
            "frames": frames_out,
            "stance_windows_L": [(f0, f1)],
            "stance_windows_R": [(f0, f1)],
        }

    start_hold = min(2, max(1, total // 12))
    end_hold = min(4, max(2, total // 8))
    sa = f0 + start_hold
    sb = f1 - end_hold
    if sb - sa < 4:
        sa, sb = f0 + 1, max(f0 + 3, f1 - 1)
    move_frames = max(2, sb - sa)

    by_time = max(2, round(move_frames / max(3, target_step_frames)))
    by_dist = max(2, int(math.ceil(dist / max(0.12, max_stride_m))) + 1)
    max_allowed_steps = max(2, move_frames // 3)
    n_steps = min(max_allowed_steps, max(by_time, by_dist))

    # Integer frame boundaries for each single-foot swing step
    boundaries = [sa + round(k * move_frames / n_steps) for k in range(n_steps + 1)]
    cur_L = start_L
    cur_R = start_R
    steps = []
    denom = max(1, n_steps - 1)
    for k in range(n_steps):
        a_f, b_f = boundaries[k], boundaries[k + 1]
        side = "L" if (k % 2 == 0) else "R"
        p_land = 1.0 if k >= n_steps - 2 else ease5((k + 1) / denom)
        cx = lerp(x0, x1, p_land)
        cy = lerp(y0, y1, p_land)
        land_world = local_to_world_point(
            (cx, cy, gz),
            yaw,
            (-stance_x if side == "L" else +stance_x, 0.0, 0.0),
        )
        from_world = cur_L if side == "L" else cur_R
        steps.append({
            "side": side,
            "a": a_f,
            "b": b_f,
            "from": from_world,
            "to": land_world,
        })
        if side == "L":
            cur_L = land_world
        else:
            cur_R = land_world

    frames_out = []
    for f in range(f0, f1 + 1):
        if f <= sa:
            fl, fr = start_L, start_R
            pl, pr = True, True
            ul, ur = 0.0, 0.0
            phase = 0.0
            bob = 0.0
        elif f >= sb:
            fl, fr = end_L, end_R
            pl, pr = True, True
            ul, ur = 0.0, 0.0
            phase = 0.0
            bob = 0.0
        else:
            # Locate active step interval
            idx = 0
            for k, st in enumerate(steps):
                if st["a"] <= f <= st["b"]:
                    idx = k
                    if f < st["b"]:
                        break
            st = steps[idx]
            # Reconstruct exact stance foot from completed prior steps
            stance_L = start_L
            stance_R = start_R
            for prev in steps[:idx]:
                if prev["side"] == "L":
                    stance_L = prev["to"]
                else:
                    stance_R = prev["to"]

            span = max(1, st["b"] - st["a"])
            raw_u = clamp((f - st["a"]) / span, 0.0, 1.0)
            if raw_u <= 0.0 or raw_u >= 1.0 or st["from"] == st["to"]:
                pos = st["from"] if raw_u <= 0.0 else st["to"]
                fl = pos if st["side"] == "L" else stance_L
                fr = pos if st["side"] == "R" else stance_R
                pl, pr = True, True
                ul = ur = 0.0
                bob = 0.0
                phase = 0.0
            else:
                xy_t = ease5(raw_u)
                z_arc = lift_height * (math.sin(math.pi * raw_u) ** 1.25)
                swing_xyz = (
                    lerp(st["from"][0], st["to"][0], xy_t),
                    lerp(st["from"][1], st["to"][1], xy_t),
                    gz + z_arc,
                )
                if st["side"] == "L":
                    fl, fr = swing_xyz, stance_R
                    pl, pr = False, True
                    ul, ur = raw_u, 0.0
                    phase = +math.sin(math.pi * raw_u)
                else:
                    fl, fr = stance_L, swing_xyz
                    pl, pr = True, False
                    ul, ur = 0.0, raw_u
                    phase = -math.sin(math.pi * raw_u)
                bob = math.sin(math.pi * raw_u) ** 1.15

        # Root stays smoothly centered between feet with slight lateral transfer over planted foot
        mid_x = 0.5 * (fl[0] + fr[0])
        mid_y = 0.5 * (fl[1] + fr[1])
        lat_shift = 0.0
        if pl and not pr:
            lat_shift = -0.016
        elif pr and not pl:
            lat_shift = +0.016
        rx, ry, _ = local_to_world_point((mid_x, mid_y, gz), yaw, (lat_shift, 0.0, 0.0))
        frames_out.append({
            "frame": f,
            "root_xyz": (rx, ry, gz),
            "yaw": yaw,
            "foot_L_world": fl,
            "foot_R_world": fr,
            "planted_L": pl,
            "planted_R": pr,
            "swing_u_L": ul,
            "swing_u_R": ur,
            "swing_phase": phase,
            "step_bob": bob,
        })

    def _collect_windows(key: str) -> list[tuple[int, int]]:
        wins: list[tuple[int, int]] = []
        run_start: int | None = None
        prev_f: int | None = None
        for item in frames_out:
            if item[key]:
                if run_start is None:
                    run_start = item["frame"]
                prev_f = item["frame"]
            elif run_start is not None and prev_f is not None:
                if prev_f > run_start:
                    wins.append((run_start, prev_f))
                run_start = None
        if run_start is not None and prev_f is not None and prev_f >= run_start:
            wins.append((run_start, prev_f))
        return wins

    return {
        "yaw": yaw,
        "frames": frames_out,
        "stance_windows_L": _collect_windows("planted_L"),
        "stance_windows_R": _collect_windows("planted_R"),
    }


# ---------------------------------------------------------------------------
# Blender 3D helper builders (Aura, Studio Chair, Smartphone)
# ---------------------------------------------------------------------------
def _srgb_to_linear_rgba(hex_color: str) -> tuple[float, float, float, float]:
    h = hex_color.lstrip("#")
    vals = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in vals)
    return (*lin, 1.0)


def _resolve_collection(hero: Any, collection: Any = None) -> Any:
    if bpy is None:
        return None
    if collection is not None:
        return collection
    root = getattr(hero, "root", None)
    if root is not None and getattr(root, "users_collection", None):
        return root.users_collection[0]
    return bpy.context.scene.collection


def _key_visibility_window(objs: list[Any], f0: int, f1: int) -> None:
    """Make `objs` visible ONLY on `[f0, f1]` inclusive with `CONSTANT` F-curves."""
    if bpy is None:
        return
    cur_frame = bpy.context.scene.frame_current
    in_window = f0 <= cur_frame <= f1
    for obj in objs:
        for f_key, hidden in ((f0 - 1, True), (f0, False), (f1 + 1, True)):
            obj.hide_render = hidden
            obj.hide_viewport = hidden
            obj.keyframe_insert("hide_render", frame=f_key)
            obj.keyframe_insert("hide_viewport", frame=f_key)
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                if fc.data_path in {"hide_render", "hide_viewport"}:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"
        obj.hide_render = not in_window
        obj.hide_viewport = not in_window


def _get_or_make_emission(name: str, hex_color: str, strength: float = 1.0) -> Any:
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = _srgb_to_linear_rgba(hex_color)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    em = nodes.new("ShaderNodeEmission")
    out = nodes.new("ShaderNodeOutputMaterial")
    em.inputs["Color"].default_value = _srgb_to_linear_rgba(hex_color)
    em.inputs["Strength"].default_value = strength
    links.new(em.outputs[0], out.inputs[0])
    return mat


def _get_or_make_matte_cel(name: str, lit_hex: str, shade_hex: str, cutoff: float = 0.26) -> Any:
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = _srgb_to_linear_rgba(lit_hex)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    diff = nodes.new("ShaderNodeBsdfDiffuse")
    diff.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    s2r = nodes.new("ShaderNodeShaderToRGB")
    bw = nodes.new("ShaderNodeRGBToBW")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    ramp.color_ramp.elements[0].position = cutoff
    ramp.color_ramp.elements[0].color = _srgb_to_linear_rgba(shade_hex)
    ramp.color_ramp.elements[1].position = min(0.98, cutoff + 0.04)
    ramp.color_ramp.elements[1].color = _srgb_to_linear_rgba(lit_hex)
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.15
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(diff.outputs[0], s2r.inputs[0])
    links.new(s2r.outputs[0], bw.inputs[0])
    links.new(bw.outputs[0], ramp.inputs[0])
    links.new(ramp.outputs[0], em.inputs["Color"])
    links.new(em.outputs[0], out.inputs[0])
    return mat


def _add_prop_ink_hull(obj: Any, col: Any, thickness: float = 0.0055) -> Any:
    ink_mat = _get_or_make_emission("MascotAnim | #141016 prop ink", "#141016", 1.0)
    ink_mat.use_backface_culling = True
    verts = [tuple(v.co) for v in obj.data.vertices]
    faces = [tuple(reversed(p.vertices)) for p in obj.data.polygons]
    data = bpy.data.meshes.new(obj.name + " • ink")
    data.from_pydata(verts, [], faces)
    data.update()
    for poly, src in zip(data.polygons, obj.data.polygons):
        poly.use_smooth = src.use_smooth
    hull = bpy.data.objects.new(obj.name + " • ink", data)
    col.objects.link(hull)
    hull.parent = obj
    hull.data.materials.append(ink_mat)
    hull.visible_shadow = False
    hull["ricks_role"] = "ink"
    disp = hull.modifiers.new("Prop comic hull", "DISPLACE")
    disp.mid_level = 0.0
    disp.strength = -thickness
    return hull


def _build_cyan_power_aura(
    hero: Any,
    f0: int,
    f1: int,
    loc: tuple[float, float, float],
    yaw: float,
    collection: Any = None,
) -> list[Any]:
    """Build & animate glowing `#3BE8FF` 3D lightning/aura curves on `[f0, f1]`."""
    if bpy is None:
        return []
    col = _resolve_collection(hero, collection)
    cyan_mat = _get_or_make_emission("MascotAnim | #3BE8FF power aura", "#3BE8FF", 4.6)
    core_mat = _get_or_make_emission("MascotAnim | #E2FCFF lightning core", "#E2FCFF", 6.2)

    prefix = f"{getattr(hero, 'name', 'Mascot')} | Aura_{f0}_{f1}"
    root_empty = bpy.data.objects.new(prefix + " | root", None)
    col.objects.link(root_empty)
    root_empty.location = loc
    root_empty.rotation_euler = (0.0, 0.0, yaw)
    created: list[Any] = [root_empty]

    # Outer enveloping silhouette halo + jagged comic lightning arcs (kept clear of the face!)
    arc_specs = [
        # Continuous smooth outer cyan energy aura dome hugging ankles -> wide elbows -> crimson beanie crown
        (
            "outer_halo_dome",
            [
                (-0.23, 0.03, 0.06),
                (-0.30, 0.02, 0.34),
                (-0.43, -0.02, 0.64),
                (-0.36, 0.03, 0.96),
                (-0.24, 0.05, 1.21),
                (0.0, 0.06, 1.31),
                (0.24, 0.05, 1.21),
                (0.36, 0.03, 0.96),
                (0.43, -0.02, 0.64),
                (0.30, 0.02, 0.34),
                (0.23, 0.03, 0.06),
            ],
            0.0105,
            cyan_mat,
        ),
        # Secondary inner electric rim arcs around shoulders & knees
        (
            "inner_arc_L",
            [(-0.20, 0.02, 0.14), (-0.27, -0.02, 0.42), (-0.39, -0.06, 0.70), (-0.31, 0.02, 1.02)],
            0.0065,
            cyan_mat,
        ),
        (
            "inner_arc_R",
            [(0.20, 0.02, 0.14), (0.27, -0.02, 0.42), (0.39, -0.06, 0.70), (0.31, 0.02, 1.02)],
            0.0065,
            cyan_mat,
        ),
        # Jagged hot-core lightning bolts off left/right arms, legs, and crown
        (
            "bolt_arm_L",
            [(-0.26, -0.16, 0.56), (-0.39, -0.14, 0.66), (-0.33, -0.19, 0.77), (-0.42, -0.12, 0.89), (-0.35, -0.15, 0.99)],
            0.0065,
            core_mat,
        ),
        (
            "bolt_arm_R",
            [(0.26, -0.16, 0.56), (0.39, -0.14, 0.66), (0.33, -0.19, 0.77), (0.42, -0.12, 0.89), (0.35, -0.15, 0.99)],
            0.0065,
            core_mat,
        ),
        (
            "bolt_leg_L",
            [(-0.18, -0.08, 0.10), (-0.27, -0.11, 0.22), (-0.21, -0.14, 0.34), (-0.30, -0.09, 0.46)],
            0.0058,
            cyan_mat,
        ),
        (
            "bolt_leg_R",
            [(0.18, -0.08, 0.10), (0.27, -0.11, 0.22), (0.21, -0.14, 0.34), (0.30, -0.09, 0.46)],
            0.0058,
            cyan_mat,
        ),
        (
            "bolt_crown_L",
            [(-0.29, 0.04, 1.05), (-0.34, 0.02, 1.16), (-0.23, 0.05, 1.26), (-0.11, 0.06, 1.34)],
            0.0058,
            core_mat,
        ),
        (
            "bolt_crown_R",
            [(0.29, 0.04, 1.05), (0.34, 0.02, 1.16), (0.23, 0.05, 1.26), (0.11, 0.06, 1.34)],
            0.0058,
            core_mat,
        ),
        # Ground shockwave ring at Z = 0.015 m
        (
            "ground_ring",
            [
                (0.40 * math.cos(i * math.tau / 24), 0.32 * math.sin(i * math.tau / 24), 0.016 + 0.010 * ((i % 2) * 2 - 1))
                for i in range(25)
            ],
            0.0055,
            cyan_mat,
        ),
    ]

    bolt_curves = []
    for arc_name, pts, rad, mat in arc_specs:
        cdata = bpy.data.curves.new(f"{prefix} | {arc_name}", "CURVE")
        cdata.dimensions = "3D"
        cdata.resolution_u = 16 if "bolt" not in arc_name else 4
        cdata.bevel_resolution = 2
        cdata.bevel_depth = rad
        cdata.use_fill_caps = True
        spline = cdata.splines.new("POLY" if "bolt" in arc_name else "BEZIER")
        if spline.type == "POLY":
            spline.points.add(len(pts) - 1)
            for idx, p in enumerate(pts):
                spline.points[idx].co = (p[0], p[1], p[2], 1.0)
                t = idx / max(1, len(pts) - 1)
                spline.points[idx].radius = 0.35 + 0.85 * math.sin(math.pi * t)
        else:
            spline.bezier_points.add(len(pts) - 1)
            for idx, p in enumerate(pts):
                bp = spline.bezier_points[idx]
                bp.co = p
                bp.handle_left_type = bp.handle_right_type = "AUTO"
                t = idx / max(1, len(pts) - 1)
                bp.radius = 0.40 + 0.80 * math.sin(math.pi * t)
        cobj = bpy.data.objects.new(f"{prefix} | {arc_name}", cdata)
        col.objects.link(cobj)
        cobj.parent = root_empty
        cobj.data.materials.append(mat)
        cobj.visible_shadow = False
        cobj["ricks_role"] = "wisp"
        created.append(cobj)
        bolt_curves.append((arc_name, cobj))

    # Animate energetic crackling pulse & rising surge over [f0, f1]
    for f in range(f0, f1 + 1):
        env = max(0.25, six_stage_envelope(f, f0, f1, windup_dip=0.25, max_act_frames=14.0))
        pulse = 1.0 + 0.055 * math.sin((f - f0) * 1.35)
        root_empty.scale = (env * pulse, env * pulse, lerp(0.65, 1.0, env) * (1.0 + 0.04 * math.cos((f - f0) * 1.7)))
        root_empty.keyframe_insert("scale", frame=f)
        for idx, (arc_name, cobj) in enumerate(bolt_curves):
            if "bolt" in arc_name:
                phase = (f - f0) * 1.9 + idx * 1.3
                cobj.location = (
                    0.012 * math.sin(phase),
                    0.008 * math.cos(phase * 1.3),
                    0.022 * ((f - f0) % 5) / 4.0,
                )
                cobj.keyframe_insert("location", frame=f)

    _key_visibility_window(created, f0, f1)
    return created


def _make_rounded_box_mesh(
    name: str,
    col: Any,
    size_xyz: tuple[float, float, float],
    loc: tuple[float, float, float],
    rot_euler: tuple[float, float, float],
    mat: Any,
    parent: Any,
    *,
    bevel_width: float = 0.025,
    ink_thickness: float = 0.0055,
) -> list[Any]:
    sx, sy, sz = size_xyz[0] * 0.5, size_xyz[1] * 0.5, size_xyz[2] * 0.5
    verts = [
        (-sx, -sy, -sz), (+sx, -sy, -sz), (+sx, +sy, -sz), (-sx, +sy, -sz),
        (-sx, -sy, +sz), (+sx, -sy, +sz), (+sx, +sy, +sz), (-sx, +sy, +sz),
    ]
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7),
        (0, 1, 5, 4), (2, 3, 7, 6),
        (1, 2, 6, 5), (3, 0, 4, 7),
    ]
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    obj.parent = parent
    obj.location = loc
    obj.rotation_euler = rot_euler
    obj.data.materials.append(mat)
    if bevel_width > 0.0:
        bev = obj.modifiers.new("Smooth bevel", "BEVEL")
        bev.width = bevel_width
        bev.segments = 2
        bev.limit_method = "NONE"
    for p in obj.data.polygons:
        p.use_smooth = True
    hull = _add_prop_ink_hull(obj, col, thickness=ink_thickness) if ink_thickness > 0 else None
    return [obj, hull] if hull is not None else [obj]


def _build_studio_lounge_chair(
    hero: Any,
    f0: int,
    f1: int,
    seat_z: float,
    loc: tuple[float, float, float],
    yaw: float,
    collection: Any = None,
) -> list[Any]:
    """Build sleek maroon & walnut 3D studio chair matching Reference Image 7."""
    if bpy is None:
        return []
    col = _resolve_collection(hero, collection)
    maroon = _get_or_make_matte_cel("MascotAnim | Maroon leather", "#6A2632", "#3B131B", cutoff=0.28)
    walnut = _get_or_make_matte_cel("MascotAnim | Walnut trim", "#7D492F", "#472617", cutoff=0.28)

    prefix = f"{getattr(hero, 'name', 'Mascot')} | StudioChair_{f0}_{f1}"
    chair_root = bpy.data.objects.new(prefix + " | root", None)
    col.objects.link(chair_root)
    chair_root.location = loc
    chair_root.rotation_euler = (0.0, 0.0, yaw)
    objs: list[Any] = [chair_root]

    cushion_thick = 0.11
    seat_center_z = max(0.14, seat_z - cushion_thick * 0.5)
    # Plush seat cushion (top at exact `seat_z`)
    objs.extend(
        _make_rounded_box_mesh(
            prefix + " | seat cushion",
            col,
            (0.62, 0.56, cushion_thick),
            (0.0, 0.03, seat_center_z),
            (-0.06, 0.0, 0.0),
            maroon,
            chair_root,
            bevel_width=0.032,
        )
    )
    # Reclined high-shoulder studio backrest framing the yellow hoodie & elbows (Image 7)
    objs.extend(
        _make_rounded_box_mesh(
            prefix + " | backrest",
            col,
            (0.64, 0.12, 0.54),
            (0.0, 0.27, seat_z + 0.23),
            (-0.34, 0.0, 0.0),
            maroon,
            chair_root,
            bevel_width=0.038,
        )
    )
    # Walnut outer back shell & low side armrests
    objs.extend(
        _make_rounded_box_mesh(
            prefix + " | walnut shell",
            col,
            (0.67, 0.06, 0.50),
            (0.0, 0.33, seat_z + 0.22),
            (-0.34, 0.0, 0.0),
            walnut,
            chair_root,
            bevel_width=0.022,
        )
    )
    for side in (-1.0, 1.0):
        objs.extend(
            _make_rounded_box_mesh(
                f"{prefix} | armrest {'L' if side < 0 else 'R'}",
                col,
                (0.085, 0.48, 0.17),
                (side * 0.31, 0.06, seat_z + 0.06),
                (-0.10, 0.0, 0.0),
                maroon,
                chair_root,
                bevel_width=0.024,
            )
        )
    # 4 tapered walnut legs down to Z = 0.000 m
    leg_h = max(0.08, seat_center_z - cushion_thick * 0.35)
    for sx in (-0.23, +0.23):
        for sy, tilt_x in ((-0.16, 0.10), (+0.22, -0.12)):
            objs.extend(
                _make_rounded_box_mesh(
                    f"{prefix} | leg_{sx:+.2f}_{sy:+.2f}",
                    col,
                    (0.048, 0.048, leg_h),
                    (sx, sy, leg_h * 0.5),
                    (tilt_x, -0.08 * (1.0 if sx > 0 else -1.0), 0.0),
                    walnut,
                    chair_root,
                    bevel_width=0.010,
                    ink_thickness=0.004,
                )
            )

    _key_visibility_window(objs, f0, f1)
    return objs


def _build_smartphone_prop(hero: Any, f0: int, f1: int, collection: Any = None) -> tuple[Any, list[Any]]:
    """Build sleek glowing 3D smartphone prop visible ONLY on `[f0, f1]`."""
    if bpy is None:
        return None, []
    col = _resolve_collection(hero, collection)
    chassis_mat = _get_or_make_matte_cel("MascotAnim | Phone slate", "#242A3A", "#141822", cutoff=0.30)
    screen_mat = _get_or_make_emission("MascotAnim | Phone screen glow", "#6CE2FF", 2.8)

    prefix = f"{getattr(hero, 'name', 'Mascot')} | Phone_{f0}_{f1}"
    body_objs = _make_rounded_box_mesh(
        prefix + " | chassis",
        col,
        (0.082, 0.154, 0.012),
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0),
        chassis_mat,
        None,
        bevel_width=0.004,
        ink_thickness=0.0035,
    )
    phone_obj = body_objs[0]

    # Glowing screen face on +Z of phone local coordinates
    sx, sy = 0.035, 0.068
    s_verts = [(-sx, -sy, 0.0068), (+sx, -sy, 0.0068), (+sx, +sy, 0.0068), (-sx, +sy, 0.0068)]
    s_data = bpy.data.meshes.new(prefix + " | screen")
    s_data.from_pydata(s_verts, [], [(0, 1, 2, 3)])
    s_data.update()
    screen_obj = bpy.data.objects.new(prefix + " | screen", s_data)
    col.objects.link(screen_obj)
    screen_obj.parent = phone_obj
    screen_obj.data.materials.append(screen_mat)
    screen_obj.visible_shadow = False
    screen_obj["ricks_role"] = "wisp"

    all_objs = [*body_objs, screen_obj]
    _key_visibility_window(all_objs, f0, f1)
    return phone_obj, all_objs


# ===========================================================================
# THE 18 STUDIO-POLISHED PARAMETERIZED ANIMATIONS
# ===========================================================================

# 1. idle_breathe
def idle_breathe(hero, f0, f1, *, loc=(0, 0, 0), yaw=0.0, expr="idle_cute"):
    """Gentle chibi breathing cycle with planted feet, subtle curiosity tilt, and string sway."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    foot_L_w = local_to_world_point(loc, yaw, (-STANCE_X, 0.0, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+STANCE_X, 0.0, 0.0))

    span = max(1, f1 - f0)
    cycles = max(1, round(span / 45.0))
    records = []
    for f in range(f0, f1 + 1):
        phase = math.tau * cycles * (f - f0) / span if f1 > f0 else 0.0
        breath = 0.5 - 0.5 * math.cos(phase)  # 0 at ends, 1 at mid-inhale
        curiosity = math.sin(phase) * bell((f - f0) / span) if f1 > f0 else 0.0

        cur_loc = local_to_world_point(loc, yaw, (0.006 * curiosity, 0.0, 0.0))
        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, cur_loc, yaw)
        arm_L = (
            (-0.22 - 0.010 * breath, -0.06 - 0.008 * breath, -0.05 + 0.014 * breath),
            (-0.21 - 0.008 * breath, 0.02, 0.07 + 0.008 * breath),
        )
        arm_R = (
            (+0.22 + 0.010 * breath, -0.06 - 0.008 * breath, -0.05 + 0.014 * breath),
            (+0.21 + 0.008 * breath, 0.02, 0.07 + 0.008 * breath),
        )
        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": yaw,
            "body_tilt": -0.018 * breath,
            "body_roll": 0.014 * curiosity,
            "bounce": 0.012 * breath,
            "squash": 1.0 + 0.010 * breath,
            "head_yaw": 0.045 * curiosity,
            "head_pitch": -0.022 * breath,
            "head_roll": -0.035 * curiosity,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "relaxed_curl",
            "hand_R": "relaxed_curl",
            "expr": expr if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    return {"animation": "idle_breathe", "f0": f0, "f1": f1, "stance_windows_L": [(f0, f1)], "stance_windows_R": [(f0, f1)]}


# 2. walk_to
def walk_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="idle_cute"):
    """Bouncy chibi walk with world-pinned stance feet (`0.000 m` skating) and opposite-phase arms."""
    plan = plan_biped_locomotion(
        f0, f1, start_xy, end_xy,
        ground_z=ground_z, target_step_frames=9, max_stride_m=0.33, lift_height=0.105,
    )
    span = max(1, f1 - f0)
    records = []
    for item in plan["frames"]:
        f = item["frame"]
        u = (f - f0) / span
        act_fade = clamp(min((f - f0) / 4.0, (f1 - f) / 4.0), 0.0, 1.0) if span >= 8 else 1.0
        cur_loc = item["root_xyz"]
        yaw = item["yaw"]
        leg_L, leg_R = pinned_leg_pair(item["foot_L_world"], item["foot_R_world"], cur_loc, yaw, knee_fwd=-0.095)

        sw = item["swing_phase"] * act_fade  # + when L leg swings forward -> R arm swings forward!
        bob = item["step_bob"] * act_fade
        arm_L = (
            (-0.21, -0.07 + 0.16 * sw, -0.03 + 0.06 * max(0.0, -sw)),
            (-0.22, 0.03 + 0.09 * sw, 0.09 + 0.03 * sw),
        )
        arm_R = (
            (+0.21, -0.07 - 0.16 * sw, -0.03 + 0.06 * max(0.0, +sw)),
            (+0.22, 0.03 - 0.09 * sw, 0.09 - 0.03 * sw),
        )
        foot_rot_L = (-0.28 * math.sin(math.pi * item["swing_u_L"]), 0.0, 0.0) if not item["planted_L"] else (0.0, 0.0, 0.0)
        foot_rot_R = (-0.28 * math.sin(math.pi * item["swing_u_R"]), 0.0, 0.0) if not item["planted_R"] else (0.0, 0.0, 0.0)

        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": yaw,
            "body_tilt": 0.16 * act_fade,
            "body_roll": 0.045 * sw,
            "bounce": 0.036 * bob - 0.010 * (1.0 - bob) * act_fade,
            "squash": 1.0 + 0.018 * bob - 0.012 * (1.0 - bob) * act_fade,
            "head_yaw": -0.04 * sw,
            "head_pitch": -0.06 * act_fade,
            "head_roll": 0.04 * sw,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "relaxed_curl",
            "hand_R": "relaxed_curl",
            "foot_rot_L": foot_rot_L,
            "foot_rot_R": foot_rot_R,
            "expr": expr if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    return {
        "animation": "walk_to",
        "f0": f0,
        "f1": f1,
        "stance_windows_L": plan["stance_windows_L"],
        "stance_windows_R": plan["stance_windows_R"],
    }


# 3. run_panic_to
def run_panic_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="mortified_blush"):
    """Frantic forward-leaning panic run with flailing raised open hands and zero stance skating."""
    plan = plan_biped_locomotion(
        f0, f1, start_xy, end_xy,
        ground_z=ground_z, target_step_frames=6, max_stride_m=0.38, lift_height=0.155,
    )
    span = max(1, f1 - f0)
    records = []
    for item in plan["frames"]:
        f = item["frame"]
        act_fade = clamp(min((f - f0) / 3.0, (f1 - f) / 4.0), 0.0, 1.0) if span >= 8 else 1.0
        cur_loc = item["root_xyz"]
        yaw = item["yaw"]
        leg_L, leg_R = pinned_leg_pair(item["foot_L_world"], item["foot_R_world"], cur_loc, yaw, knee_fwd=-0.13)

        sw = item["swing_phase"] * act_fade
        bob = item["step_bob"] * act_fade
        flail = math.sin((f - f0) * 1.15) * act_fade

        arm_L_panic = (
            (-0.27 - 0.04 * flail, -0.14 + 0.12 * sw, 0.34 + 0.09 * max(-1.0, flail)),
            (-0.29, -0.05 + 0.05 * sw, 0.21),
        )
        arm_R_panic = (
            (+0.27 - 0.04 * flail, -0.14 - 0.12 * sw, 0.34 - 0.09 * min(1.0, flail)),
            (+0.29, -0.05 - 0.05 * sw, 0.21),
        )
        arm_L = arm_lerp(REST_ARM_L, arm_L_panic, act_fade)
        arm_R = arm_lerp(REST_ARM_R, arm_R_panic, act_fade)
        foot_rot_L = (-0.42 * math.sin(math.pi * item["swing_u_L"]), 0.0, 0.0) if not item["planted_L"] else (0.0, 0.0, 0.0)
        foot_rot_R = (-0.42 * math.sin(math.pi * item["swing_u_R"]), 0.0, 0.0) if not item["planted_R"] else (0.0, 0.0, 0.0)

        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": yaw,
            "body_tilt": 0.32 * act_fade,
            "body_roll": 0.075 * sw,
            "bounce": 0.058 * bob - 0.022 * (1.0 - bob) * act_fade,
            "squash": 1.0 + 0.035 * bob - 0.020 * (1.0 - bob) * act_fade,
            "head_yaw": 0.11 * flail,
            "head_pitch": -0.14 * act_fade,
            "head_roll": -0.07 * flail,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "open_stop" if act_fade > 0.2 else "relaxed_curl",
            "hand_R": "open_stop" if act_fade > 0.2 else "relaxed_curl",
            "foot_rot_L": foot_rot_L,
            "foot_rot_R": foot_rot_R,
            "expr": expr if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    return {
        "animation": "run_panic_to",
        "f0": f0,
        "f1": f1,
        "stance_windows_L": plan["stance_windows_L"],
        "stance_windows_R": plan["stance_windows_R"],
    }


# 4. sneak_to
def sneak_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="curious_o"):
    """Hunched high-knee tiptoe sneak with furtive side-to-side head peeks and zero skating."""
    plan = plan_biped_locomotion(
        f0, f1, start_xy, end_xy,
        ground_z=ground_z, target_step_frames=12, max_stride_m=0.28, lift_height=0.14,
    )
    span = max(1, f1 - f0)
    records = []
    for item in plan["frames"]:
        f = item["frame"]
        u = (f - f0) / span
        act_fade = clamp(min((f - f0) / 5.0, (f1 - f) / 5.0), 0.0, 1.0) if span >= 10 else 1.0
        cur_loc = item["root_xyz"]
        yaw = item["yaw"]
        leg_L, leg_R = pinned_leg_pair(item["foot_L_world"], item["foot_R_world"], cur_loc, yaw, knee_fwd=-0.14, knee_z=0.22)

        sw = item["swing_phase"] * act_fade
        bob = item["step_bob"] * act_fade
        peek = math.sin(math.tau * 1.5 * u) * act_fade

        sneak_L = ((-0.17, -0.22 + 0.04 * sw, 0.14 + 0.03 * bob), (-0.25, -0.05, 0.08))
        sneak_R = ((+0.17, -0.22 - 0.04 * sw, 0.14 + 0.03 * bob), (+0.25, -0.05, 0.08))
        arm_L = arm_lerp(REST_ARM_L, sneak_L, act_fade)
        arm_R = arm_lerp(REST_ARM_R, sneak_R, act_fade)
        foot_rot_L = (0.38 * math.sin(math.pi * item["swing_u_L"]), 0.0, 0.0) if not item["planted_L"] else (0.0, 0.0, 0.0)
        foot_rot_R = (0.38 * math.sin(math.pi * item["swing_u_R"]), 0.0, 0.0) if not item["planted_R"] else (0.0, 0.0, 0.0)

        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": yaw,
            "body_tilt": 0.28 * act_fade,
            "body_roll": 0.04 * sw,
            "bounce": -0.065 * act_fade + 0.028 * bob,
            "squash": 1.0 - 0.035 * act_fade + 0.015 * bob,
            "head_yaw": 0.34 * peek,
            "head_pitch": -0.18 * act_fade,
            "head_roll": -0.08 * peek,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "power_claw" if act_fade > 0.3 else "relaxed_curl",
            "hand_R": "power_claw" if act_fade > 0.3 else "relaxed_curl",
            "foot_rot_L": foot_rot_L,
            "foot_rot_R": foot_rot_R,
            "expr": expr if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    return {
        "animation": "sneak_to",
        "f0": f0,
        "f1": f1,
        "stance_windows_L": plan["stance_windows_L"],
        "stance_windows_R": plan["stance_windows_R"],
    }


# 5. stop_hold_up — Exact Reference Image 5
def stop_hold_up(hero, f0, f1, *, loc=(0, 0, 0), yaw=0.0):
    """Reference Image 5: slight lean back + viewer-left `arm_L` thrust forward with `open_stop` palm."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    # Sturdy planted wide chibi stance
    foot_L_w = local_to_world_point(loc, yaw, (-0.132, -0.025, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+0.132, +0.040, 0.0))

    # Heroic Reference Image 5 target arm silhouettes:
    # Viewer-left (-X) arm thrust straight forward toward -Y camera from shoulder with big `open_stop` palm!
    target_arm_L = ((-0.175, -0.420, 0.175), (-0.205, -0.195, 0.105))
    target_arm_R = ((+0.280, +0.075, -0.020), (+0.230, +0.035, 0.095))
    wind_arm_L = ((-0.175, -0.135, 0.115), (-0.235, 0.035, 0.055))

    records = []
    for f in range(f0, f1 + 1):
        env = six_stage_envelope(f, f0, f1, windup_dip=-0.18, max_act_frames=18.0)
        if env < 0.0:
            w = -env / 0.18
            arm_L = arm_lerp(REST_ARM_L, wind_arm_L, w)
            arm_R = REST_ARM_R
            t = 0.0
            crouch = -0.032 * w
            sq = 1.0 - 0.035 * w
        else:
            t = clamp(env, 0.0, 1.0)
            arm_L = arm_lerp(REST_ARM_L, target_arm_L, t)
            arm_R = arm_lerp(REST_ARM_R, target_arm_R, t)
            crouch = -0.012 * t
            sq = 1.0 + 0.012 * t

        cur_loc = local_to_world_point(loc, yaw, (0.018 * t, 0.028 * t, 0.0))
        cur_yaw = yaw - 0.11 * t  # Rotates viewer-left shoulder (-X) slightly forward toward -Y camera!
        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, cur_loc, cur_yaw)

        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": cur_yaw,
            "body_tilt": -0.145 * t,
            "body_roll": 0.055 * t,
            "bounce": crouch,
            "squash": sq,
            "head_yaw": 0.095 * t,
            "head_pitch": -0.075 * t,
            "head_roll": -0.085 * t,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "open_stop" if t >= 0.22 else "relaxed_curl",
            "hand_R": "relaxed_curl",
            "hand_rot_L": (0.06 * t, 0.0, 0.18 * t),
            "hand_rot_R": (0.0, 0.0, 0.0),
            "expr": "curious_o" if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    return {"animation": "stop_hold_up", "f0": f0, "f1": f1, "stance_windows_L": [(f0, f1)], "stance_windows_R": [(f0, f1)]}


# 6. power_aura_stance — Exact Reference Image 6
def power_aura_stance(hero, f0, f1, aura=True, *, loc=(0, 0, 0), yaw=0.0, collection=None):
    """Reference Image 6: wide heroic stance + dual `power_claw` hands + `#3BE8FF` cyan lightning aura."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    # Wide planted heroic stance (Image 6)
    foot_L_w = local_to_world_point(loc, yaw, (-0.158, -0.015, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+0.158, -0.015, 0.0))

    # Wide bowed yellow hoodie elbows + upturned white `power_claw` hands angled ~40 deg toward camera/sky!
    hero_arm_L = ((-0.255, -0.235, 0.205), (-0.335, -0.055, 0.055))
    hero_arm_R = ((+0.255, -0.235, 0.205), (+0.335, -0.055, 0.055))
    coil_arm_L = ((-0.165, -0.155, 0.045), (-0.225, 0.025, 0.015))
    coil_arm_R = ((+0.165, -0.155, 0.045), (+0.225, 0.025, 0.015))

    records = []
    for f in range(f0, f1 + 1):
        env = six_stage_envelope(f, f0, f1, windup_dip=-0.22, max_act_frames=18.0)
        if env < 0.0:
            w = -env / 0.22
            arm_L = arm_lerp(REST_ARM_L, coil_arm_L, w)
            arm_R = arm_lerp(REST_ARM_R, coil_arm_R, w)
            t = 0.0
            bounce = -0.055 * w
            sq = 1.0 - 0.05 * w
        else:
            t = clamp(env, 0.0, 1.0)
            arm_L = arm_lerp(REST_ARM_L, hero_arm_L, t)
            arm_R = arm_lerp(REST_ARM_R, hero_arm_R, t)
            bounce = -0.022 * t
            sq = 1.0 + 0.018 * t

        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, loc, yaw, knee_fwd=-0.085, knee_out=0.025)
        records.append({
            "frame": f,
            "loc": loc,
            "yaw": yaw,
            "body_tilt": -0.105 * t,
            "body_roll": 0.0,
            "bounce": bounce,
            "squash": sq,
            "head_yaw": -0.045 * t,
            "head_pitch": -0.095 * t,
            "head_roll": 0.035 * t,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "power_claw" if t >= 0.20 else "fist",
            "hand_R": "power_claw" if t >= 0.20 else "fist",
            "hand_rot_L": (-0.62 * t, +0.25 * t, +0.22 * t),
            "hand_rot_R": (-0.62 * t, -0.25 * t, -0.22 * t),
            "expr": "curious_o" if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    aura_objs = _build_cyan_power_aura(hero, f0, f1, loc, yaw, collection=collection) if aura else []
    return {
        "animation": "power_aura_stance",
        "f0": f0,
        "f1": f1,
        "aura_objects": aura_objs,
        "stance_windows_L": [(f0, f1)],
        "stance_windows_R": [(f0, f1)],
    }


# 7. chill_chair_lean — Exact Reference Image 7
def chill_chair_lean(hero, f0, f1, seat_z=0.42, *, loc=(0, 0, 0), yaw=0.0, build_chair=True, collection=None):
    """Reference Image 7: reclined in maroon/walnut studio chair, arms behind beanie, sneaker sole visible."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    seat_z = float(seat_z)

    chair_objs = _build_studio_lounge_chair(hero, f0, f1, seat_z, loc, yaw, collection=collection) if build_chair else []

    # Hoodie hem sits ~0.20 m below `body`; settle torso cleanly onto `seat_z`
    sit_bounce = (seat_z + 0.17) - BODY_PIVOT_Z
    # Both yellow-sleeved elbows raised high & wide framing the red beanie, hands tucked cleanly behind head!
    chill_arm_L = ((-0.150, +0.215, 0.430), (-0.355, +0.025, 0.415))
    chill_arm_R = ((+0.150, +0.215, 0.430), (+0.355, +0.025, 0.415))
    # Crossed/propped lounge legs with viewer-right chunky sneaker sole angled directly toward -Y camera!
    chill_leg_L = ((-0.075, -0.315, 0.015), (-0.115, -0.225, seat_z * 0.68))
    chill_leg_R = ((+0.085, -0.385, seat_z * 0.48), (+0.035, -0.245, seat_z * 0.92))
    stand_leg_L = ((-STANCE_X, 0.0, 0.0), (-STANCE_X, -0.07, 0.19))
    stand_leg_R = ((+STANCE_X, 0.0, 0.0), (+STANCE_X, -0.07, 0.19))

    span = max(1, f1 - f0)
    records = []
    for f in range(f0, f1 + 1):
        settle = 1.0 if span < 8 else ease5(min(1.0, (f - f0) / min(16.0, span * 0.42)))
        laugh_bob = 0.008 * math.sin((f - f0) * 0.45) * settle if span >= 12 else 0.0

        cur_loc = local_to_world_point(loc, yaw, (0.0, 0.035 * settle, 0.0))
        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": yaw,
            "body_tilt": -0.36 * settle,
            "body_roll": 0.055 * settle,
            "bounce": sit_bounce * settle + laugh_bob,
            "squash": 1.0 - 0.015 * settle + 0.5 * laugh_bob,
            "head_yaw": 0.045 * settle,
            "head_pitch": 0.22 * settle,  # Compensates backward torso recline so face beams at camera!
            "head_roll": -0.115 * settle,
            "arm_L": arm_lerp(REST_ARM_L, chill_arm_L, settle),
            "arm_R": arm_lerp(REST_ARM_R, chill_arm_R, settle),
            "leg_L": (vlerp(stand_leg_L[0], chill_leg_L[0], settle), vlerp(stand_leg_L[1], chill_leg_L[1], settle)),
            "leg_R": (vlerp(stand_leg_R[0], chill_leg_R[0], settle), vlerp(stand_leg_R[1], chill_leg_R[1], settle)),
            "hand_L": "behind_head" if settle >= 0.35 else "relaxed_curl",
            "hand_R": "behind_head" if settle >= 0.35 else "relaxed_curl",
            # Pitch right sneaker toe UP (+X rotation < 0 lifts -Y toe toward +Z!) so flat rubber sole faces camera!
            "foot_rot_L": (-0.18 * settle, 0.0, 0.08 * settle),
            "foot_rot_R": (-1.12 * settle, -0.18 * settle, -0.16 * settle),
            "expr": "chill_laugh" if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    return {"animation": "chill_chair_lean", "f0": f0, "f1": f1, "chair_objects": chair_objs}


# 8. talk_explain
def talk_explain(hero, f0, f1, audio_path=None, *, loc=(0, 0, 0), yaw=0.0, base_expr="idle_cute"):
    """Expressive two-hand conversational beat gestures + `auto_lipsync` (or rhythmic visemes)."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    foot_L_w = local_to_world_point(loc, yaw, (-STANCE_X, 0.0, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+STANCE_X, 0.0, 0.0))

    beat_poses = [
        # Beat A: left open hand presenting idea
        (
            ((-0.24, -0.24, 0.13), (-0.25, -0.06, 0.05)),
            ((+0.21, -0.12, 0.02), (+0.22, -0.01, 0.06)),
            "open_stop", "relaxed_curl", -0.06, -0.05,
        ),
        # Beat B: both hands open framing point
        (
            ((-0.25, -0.25, 0.16), (-0.27, -0.07, 0.06)),
            ((+0.25, -0.25, 0.16), (+0.27, -0.07, 0.06)),
            "open_stop", "open_stop", +0.05, +0.04,
        ),
        # Beat C: right point emphasis
        (
            ((-0.21, -0.11, 0.01), (-0.22, -0.01, 0.06)),
            ((+0.23, -0.27, 0.18), (+0.25, -0.08, 0.07)),
            "relaxed_curl", "point", +0.07, -0.04,
        ),
    ]
    viseme_cycle = ("vis_AA", "vis_EE", "vis_OH", "vis_FV", "vis_AA", "vis_OO", "vis_closed")

    span = max(1, f1 - f0)
    settle_tail = min(7, max(0, span // 6))
    active_end = f1 - settle_tail
    records = []

    for f in range(f0, f1 + 1):
        if f >= active_end or span < 4:
            fade = 0.0 if settle_tail == 0 else 1.0 - ease5((f - active_end) / max(1, settle_tail))
        else:
            fade = ease5(min(1.0, (f - f0) / 5.0))

        seg_len = 14.0
        seg = int((f - f0) // seg_len)
        local_u = ease5(((f - f0) % seg_len) / seg_len)
        pa = beat_poses[seg % len(beat_poses)]
        pb = beat_poses[(seg + 1) % len(beat_poses)]

        gest_L = arm_lerp(pa[0], pb[0], local_u)
        gest_R = arm_lerp(pa[1], pb[1], local_u)
        arm_L = arm_lerp(REST_ARM_L, gest_L, fade)
        arm_R = arm_lerp(REST_ARM_R, gest_R, fade)
        hyaw = lerp(pa[4], pb[4], local_u) * fade
        hroll = lerp(pa[5], pb[5], local_u) * fade
        nod = math.sin((f - f0) * 0.55) * fade

        cur_loc = local_to_world_point(loc, yaw, (0.012 * math.sin((f - f0) * 0.22) * fade, 0.0, 0.0))
        cur_yaw = yaw + 0.04 * hyaw
        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, cur_loc, cur_yaw)

        frame_expr = None
        if audio_path is None:
            if f == f0:
                frame_expr = base_expr
            elif f >= active_end:
                if f == active_end:
                    frame_expr = base_expr
            elif (f - f0) % 3 == 0:
                slot = ((f - f0) // 3)
                frame_expr = base_expr if (slot % 9 == 8) else viseme_cycle[slot % len(viseme_cycle)]

        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": cur_yaw,
            "body_tilt": 0.045 * fade + 0.025 * max(0.0, nod),
            "body_roll": 0.025 * hroll,
            "bounce": 0.012 * max(0.0, nod),
            "squash": 1.0 + 0.008 * nod,
            "head_yaw": hyaw,
            "head_pitch": 0.045 * nod - 0.02 * fade,
            "head_roll": hroll,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": pa[2] if fade > 0.35 else "relaxed_curl",
            "hand_R": pa[3] if fade > 0.35 else "relaxed_curl",
            "expr": frame_expr,
        })

    _apply_pose_series(hero, records)
    if audio_path is not None:
        hero.auto_lipsync(audio_path, f0, f1, base_expr=base_expr)
    return {"animation": "talk_explain", "f0": f0, "f1": f1, "stance_windows_L": [(f0, f1)], "stance_windows_R": [(f0, f1)]}


# 9. point_at_camera_wink
def point_at_camera_wink(hero, f0, f1, *, loc=(0, 0, 0), yaw=0.0, camera=None):
    """Anticipation wind-up -> snappy `point` hand toward camera lens + `smug_wink`."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    foot_L_w = local_to_world_point(loc, yaw, (-0.118, -0.01, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+0.118, +0.02, 0.0))

    default_cam_w = local_to_world_point(loc, yaw, (0.0, -2.6, 1.08))
    wind_R = ((+0.16, -0.10, 0.14), (+0.25, +0.06, 0.06))
    hip_L = ((-0.20, -0.04, 0.02), (-0.27, 0.03, 0.09))

    records = []
    for f in range(f0, f1 + 1):
        cam_w = default_cam_w
        if camera is not None and bpy is not None:
            bpy.context.scene.frame_set(f)
            bpy.context.view_layer.update()
            cam_w = tuple(camera.matrix_world.translation)

        aim_yaw, aim_pitch = _aim_angles_toward(loc, yaw, cam_w)
        cam_local = world_to_root_local(cam_w, (loc[0], loc[1], loc[2] + BODY_PIVOT_Z), yaw)
        dx_s = cam_local[0] - SHOULDER_X
        dy_s = cam_local[1]
        dz_s = cam_local[2] - SHOULDER_Z
        norm_s = max(1e-4, math.sqrt(dx_s * dx_s + dy_s * dy_s + dz_s * dz_s))
        # Keep pointing hand slightly to viewer-right (+X >= +0.15) so it never blocks the winking face!
        px = max(0.155, SHOULDER_X + 0.34 * (dx_s / norm_s))
        py = clamp(0.35 * (dy_s / norm_s), -0.38, -0.22)
        pz = clamp(SHOULDER_Z + 0.32 * (dz_s / norm_s), 0.12, 0.30)
        point_R = ((px, py, pz), (+0.23, py * 0.45, pz - 0.09))

        env = six_stage_envelope(f, f0, f1, windup_dip=-0.22, max_act_frames=16.0)
        if env < 0.0:
            w = -env / 0.22
            arm_R = arm_lerp(REST_ARM_R, wind_R, w)
            arm_L = arm_lerp(REST_ARM_L, hip_L, 0.5 * w)
            t = 0.0
            bounce = -0.030 * w
            sq = 1.0 - 0.03 * w
        else:
            t = clamp(env, 0.0, 1.0)
            arm_R = arm_lerp(REST_ARM_R, point_R, t)
            arm_L = arm_lerp(REST_ARM_L, hip_L, t)
            bounce = 0.012 * t
            sq = 1.0 + 0.010 * t

        cur_yaw = yaw + 0.22 * aim_yaw * t
        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, loc, cur_yaw)
        wink_active = t >= 0.35 or (f1 - f0 < 6)
        expr = ("smug_wink" if wink_active else "idle_cute") if f == f0 else ("smug_wink" if wink_active else None)

        records.append({
            "frame": f,
            "loc": loc,
            "yaw": cur_yaw,
            "body_tilt": -0.06 * t,
            "body_roll": -0.05 * t,
            "bounce": bounce,
            "squash": sq,
            "head_yaw": 0.78 * aim_yaw * t,
            "head_pitch": aim_pitch * t,
            "head_roll": 0.11 * t,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "fist" if t > 0.3 else "relaxed_curl",
            "hand_R": "point" if t >= 0.22 else "relaxed_curl",
            "expr": expr,
        })
    _apply_pose_series(hero, records)
    return {"animation": "point_at_camera_wink", "f0": f0, "f1": f1, "stance_windows_L": [(f0, f1)], "stance_windows_R": [(f0, f1)]}


# 10. shrug_idk
def shrug_idk(hero, f0, f1, *, loc=(0, 0, 0), yaw=0.0):
    """Classic 'I dunno!' palms-up wide W-shrug + head tilt + `whatever_eyeroll`."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    foot_L_w = local_to_world_point(loc, yaw, (-STANCE_X, 0.0, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+STANCE_X, 0.0, 0.0))

    shrug_L = ((-0.32, -0.17, 0.20), (-0.21, -0.03, 0.04))
    shrug_R = ((+0.32, -0.17, 0.20), (+0.21, -0.03, 0.04))
    span = max(1, f1 - f0)
    records = []

    for f in range(f0, f1 + 1):
        env = max(0.0, six_stage_envelope(f, f0, f1, windup_dip=-0.10, max_act_frames=16.0))
        # Slight relaxed exhale on the last 20% while keeping the expressive shrug readable
        exhale = 0.15 * ease5(((f - f0) / span - 0.80) / 0.20) if span >= 20 and (f - f0) / span > 0.80 else 0.0
        t = clamp(env * (1.0 - exhale), 0.0, 1.0)

        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, loc, yaw)
        records.append({
            "frame": f,
            "loc": loc,
            "yaw": yaw,
            "body_tilt": -0.05 * t,
            "body_roll": 0.04 * t,
            "bounce": 0.024 * t,
            "squash": 1.0 - 0.028 * t,
            "head_yaw": -0.06 * t,
            "head_pitch": -0.05 * t,
            "head_roll": 0.20 * t,
            "arm_L": arm_lerp(REST_ARM_L, shrug_L, t),
            "arm_R": arm_lerp(REST_ARM_R, shrug_R, t),
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "open_stop" if t >= 0.25 else "relaxed_curl",
            "hand_R": "open_stop" if t >= 0.25 else "relaxed_curl",
            "hand_rot_L": (-0.65 * t, -0.25 * t, 0.0),
            "hand_rot_R": (-0.65 * t, +0.25 * t, 0.0),
            "expr": "whatever_eyeroll" if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    return {"animation": "shrug_idk", "f0": f0, "f1": f1, "stance_windows_L": [(f0, f1)], "stance_windows_R": [(f0, f1)]}


# 11. jump_parabolic
def jump_parabolic(hero, f0, f1, start_xyz, end_xyz, jump_height=0.55):
    """Anticipation crouch -> ballistic parabolic air arc -> cushioned knee-bend squash landing."""
    f0, f1 = _validate_range(f0, f1)
    s_xyz = tuple(float(c) for c in start_xyz)
    e_xyz = tuple(float(c) for c in end_xyz)
    jump_h = max(0.08, float(jump_height))
    yaw = _heading_from_delta(e_xyz[0] - s_xyz[0], e_xyz[1] - s_xyz[1], fallback=0.0)

    start_L = local_to_world_point(s_xyz, yaw, (-STANCE_X, 0.0, 0.0))
    start_R = local_to_world_point(s_xyz, yaw, (+STANCE_X, 0.0, 0.0))
    end_L = local_to_world_point(e_xyz, yaw, (-STANCE_X, 0.0, 0.0))
    end_R = local_to_world_point(e_xyz, yaw, (+STANCE_X, 0.0, 0.0))

    span = f1 - f0
    if span < 6:
        mid = ((s_xyz[0] + e_xyz[0]) * 0.5, (s_xyz[1] + e_xyz[1]) * 0.5, max(s_xyz[2], e_xyz[2]) + jump_h)
        records = []
        for f in range(f0, f1 + 1):
            cur = e_xyz if f == f1 and span > 0 else mid
            leg_L, leg_R = pinned_leg_pair(end_L, end_R, e_xyz, yaw)
            records.append({
                "frame": f, "loc": cur, "yaw": yaw,
                "arm_L": ((-0.26, -0.14, 0.34), (-0.28, -0.04, 0.18)),
                "arm_R": ((+0.26, -0.14, 0.34), (+0.28, -0.04, 0.18)),
                "leg_L": leg_L, "leg_R": leg_R,
                "hand_L": "fist", "hand_R": "fist",
                "expr": "hype_letsgo" if f == f0 else None,
            })
        _apply_pose_series(hero, records)
        return {"animation": "jump_parabolic", "f0": f0, "f1": f1, "stance_windows_L": [], "stance_windows_R": []}

    f_takeoff = f0 + max(2, round(span * 0.22))
    f_land = f0 + min(span - 2, max(f_takeoff - f0 + 2, round(span * 0.76)))

    crouch_arm_L = ((-0.23, +0.14, -0.06), (-0.24, +0.09, 0.08))
    crouch_arm_R = ((+0.23, +0.14, -0.06), (+0.24, +0.09, 0.08))
    air_arm_L = ((-0.27, -0.14, 0.38), (-0.29, -0.04, 0.21))
    air_arm_R = ((+0.27, -0.14, 0.38), (+0.29, -0.04, 0.21))

    records = []
    for f in range(f0, f1 + 1):
        if f <= f_takeoff:
            u = ease5((f - f0) / max(1, f_takeoff - f0))
            crouch = math.sin(math.pi * 0.85 * u)
            cur_loc = s_xyz
            leg_L, leg_R = pinned_leg_pair(start_L, start_R, cur_loc, yaw, knee_fwd=-0.12)
            arm_L = arm_lerp(REST_ARM_L, crouch_arm_L, crouch)
            arm_R = arm_lerp(REST_ARM_R, crouch_arm_R, crouch)
            bounce = -0.085 * crouch
            sq = 1.0 - 0.085 * crouch
            tilt = 0.22 * crouch
            hpitch = -0.14 * crouch
            f_rot = (0.0, 0.0, 0.0)
            expr = "curious_o" if f == f0 else None
            hand = "fist" if u > 0.5 else "relaxed_curl"
        elif f < f_land:
            u = (f - f_takeoff) / max(1, f_land - f_takeoff)
            z_peak = max(s_xyz[2], e_xyz[2]) + jump_h
            rt0 = math.sqrt(max(1e-6, z_peak - s_xyz[2]))
            rt1 = math.sqrt(max(1e-6, z_peak - e_xyz[2]))
            u_apex = rt0 / (rt0 + rt1)
            z_ballistic = z_peak - ((rt0 + rt1) * (u - u_apex)) ** 2
            arc = clamp((z_ballistic - lerp(s_xyz[2], e_xyz[2], u)) / max(1e-6, jump_h), 0.0, 1.2)
            cur_loc = (
                lerp(s_xyz[0], e_xyz[0], u),
                lerp(s_xyz[1], e_xyz[1], u),
                z_ballistic,
            )
            tuck = math.sin(math.pi * u)
            leg_L = ((-STANCE_X, -0.06 * tuck, 0.09 * tuck), (-STANCE_X - 0.02, -0.16, 0.24 + 0.06 * tuck))
            leg_R = ((+STANCE_X, +0.04 * tuck, 0.12 * tuck), (+STANCE_X + 0.02, -0.14, 0.25 + 0.06 * tuck))
            arm_L = arm_lerp(crouch_arm_L, air_arm_L, math.sin(math.pi * min(1.0, u * 1.15)))
            arm_R = arm_lerp(crouch_arm_R, air_arm_R, math.sin(math.pi * min(1.0, u * 1.15)))
            bounce = 0.0
            sq = 1.0 + 0.075 * (1.0 - arc * 0.5)
            tilt = lerp(0.18, -0.08, u)
            hpitch = lerp(-0.16, 0.08, u)
            f_rot = (0.28 * tuck, 0.0, 0.0)
            expr = "hype_letsgo" if f == f_takeoff + 1 else None
            hand = "fist"
        else:
            u = (f - f_land) / max(1, f1 - f_land)
            impact = math.sin(math.pi * min(1.0, u * 1.35)) * (1.0 - ease5(u))
            cur_loc = e_xyz
            leg_L, leg_R = pinned_leg_pair(end_L, end_R, cur_loc, yaw, knee_fwd=-0.12)
            arm_L = arm_lerp(air_arm_L, REST_ARM_L, ease5(u))
            arm_R = arm_lerp(air_arm_R, REST_ARM_R, ease5(u))
            bounce = -0.080 * impact
            sq = 1.0 - 0.080 * impact
            tilt = 0.18 * impact
            hpitch = 0.06 * impact
            f_rot = (0.0, 0.0, 0.0)
            expr = "idle_cute" if f == f_land + max(1, (f1 - f_land) // 2) else None
            hand = "relaxed_curl" if u > 0.5 else "open_stop"

        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": yaw,
            "body_tilt": tilt,
            "body_roll": 0.0,
            "bounce": bounce,
            "squash": sq,
            "head_yaw": 0.0,
            "head_pitch": hpitch,
            "head_roll": 0.0,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": hand,
            "hand_R": hand,
            "foot_rot_L": f_rot,
            "foot_rot_R": f_rot,
            "expr": expr,
        })
    _apply_pose_series(hero, records)
    return {
        "animation": "jump_parabolic",
        "f0": f0,
        "f1": f1,
        "stance_windows_L": [(f0, f_takeoff), (f_land, f1)],
        "stance_windows_R": [(f0, f_takeoff), (f_land, f1)],
    }


# 12. celebrate_hype
def celebrate_hype(hero, f0, f1, *, loc=(0, 0, 0), yaw=0.0):
    """Joyful double-`fist` hype hops + `hype_letsgo`, finishing in a planted victory hold."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    foot_L_w = local_to_world_point(loc, yaw, (-0.125, 0.0, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+0.125, 0.0, 0.0))

    span = f1 - f0
    settle_len = min(8, max(2, span // 5)) if span >= 12 else 0
    hop_end = f1 - settle_len
    hop_span = max(1, hop_end - f0)
    n_hops = max(1, min(3, round(hop_span / 16.0)))

    pump_hi_L = ((-0.25, -0.13, 0.44), (-0.29, -0.03, 0.24))
    pump_hi_R = ((+0.25, -0.13, 0.44), (+0.29, -0.03, 0.24))
    pump_lo_L = ((-0.22, -0.15, 0.24), (-0.26, -0.02, 0.11))
    pump_lo_R = ((+0.22, -0.15, 0.24), (+0.26, -0.02, 0.11))

    records = []
    stance_wins: list[tuple[int, int]] = []
    run_start: int | None = None

    for f in range(f0, f1 + 1):
        if span < 6 or f >= hop_end:
            air = 0.0
            crouch = 0.0
            t_settle = 1.0 if settle_len == 0 else ease5((f - hop_end) / max(1, settle_len))
            arm_L = arm_lerp(pump_hi_L, ((-0.26, -0.14, 0.39), (-0.29, -0.04, 0.22)), t_settle)
            arm_R = arm_lerp(pump_hi_R, ((+0.26, -0.14, 0.39), (+0.29, -0.04, 0.22)), t_settle)
            grounded = True
        else:
            cyc = ((f - f0) / hop_span) * n_hops
            local_u = cyc - math.floor(cyc)
            if 0.22 < local_u < 0.78:
                air_u = (local_u - 0.22) / 0.56
                air = 0.16 * 4.0 * air_u * (1.0 - air_u)
                crouch = 0.0
                grounded = False
            else:
                g_u = local_u / 0.22 if local_u <= 0.22 else (local_u - 0.78) / 0.22
                air = 0.0
                crouch = -0.048 * math.sin(math.pi * g_u)
                grounded = True
            pump = 0.5 - 0.5 * math.cos(math.tau * local_u)
            arm_L = arm_lerp(pump_lo_L, pump_hi_L, pump)
            arm_R = arm_lerp(pump_lo_R, pump_hi_R, pump)

        if grounded:
            if run_start is None:
                run_start = f
            cur_loc = loc
            leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, cur_loc, yaw)
            f_rot = (0.0, 0.0, 0.0)
        else:
            if run_start is not None:
                if f - 1 > run_start:
                    stance_wins.append((run_start, f - 1))
                run_start = None
            cur_loc = (loc[0], loc[1], loc[2] + air)
            leg_L = ((-0.125, -0.04, 0.04), (-0.14, -0.14, 0.22))
            leg_R = ((+0.125, -0.04, 0.04), (+0.14, -0.14, 0.22))
            f_rot = (0.22, 0.0, 0.0)

        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": yaw,
            "body_tilt": -0.08 if air > 0 else 0.06 * (-crouch / 0.05),
            "body_roll": 0.04 * math.sin((f - f0) * 0.5),
            "bounce": crouch,
            "squash": 1.0 + (0.045 if air > 0 else crouch * 0.9),
            "head_yaw": 0.05 * math.sin((f - f0) * 0.5),
            "head_pitch": -0.11,
            "head_roll": -0.05 * math.sin((f - f0) * 0.5),
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "fist",
            "hand_R": "fist",
            "foot_rot_L": f_rot,
            "foot_rot_R": f_rot,
            "expr": "hype_letsgo" if f == f0 else None,
        })

    if run_start is not None and f1 >= run_start:
        stance_wins.append((run_start, f1))
    _apply_pose_series(hero, records)
    return {"animation": "celebrate_hype", "f0": f0, "f1": f1, "stance_windows_L": stance_wins, "stance_windows_R": stance_wins}


# 13. facepalm_groan
def facepalm_groan(hero, f0, f1, *, loc=(0, 0, 0), yaw=0.0):
    """Hand slap to brow + defeated forward slump + `ugh_groan` with planted feet."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    foot_L_w = local_to_world_point(loc, yaw, (-STANCE_X, 0.0, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+STANCE_X, 0.0, 0.0))

    # Right palm slaps upper brow/beanie brim while leaving the groaned open mouth visible below!
    brow_R = ((+0.045, -0.235, 0.415), (+0.275, -0.145, 0.255))
    wind_R = ((+0.285, -0.185, 0.285), (+0.305, -0.045, 0.145))
    limp_L = ((-0.205, -0.095, -0.085), (-0.215, -0.015, 0.055))

    span = max(1, f1 - f0)
    records = []
    for f in range(f0, f1 + 1):
        env = six_stage_envelope(f, f0, f1, windup_dip=-0.20, max_act_frames=18.0)
        shake = math.sin((f - f0) * 0.65) * ease5(clamp((f - f0 - 12.0) / 10.0)) * (1.0 - ease5(clamp(((f - f0) / span - 0.78) / 0.22))) if span >= 16 else 0.0

        if env < 0.0:
            w = -env / 0.20
            arm_R = arm_lerp(REST_ARM_R, wind_R, w)
            arm_L = REST_ARM_L
            t = 0.0
            tilt = -0.08 * w
            expr = "cringe_teeth" if f == f0 else None
        else:
            t = clamp(env, 0.0, 1.0)
            arm_R = arm_lerp(wind_R, brow_R, t)
            arm_L = arm_lerp(REST_ARM_L, limp_L, t)
            tilt = 0.22 * t
            slap_hit = t >= 0.55 or (span < 6)
            expr = ("ugh_groan" if slap_hit else "cringe_teeth") if f == f0 else ("ugh_groan" if slap_hit else None)

        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, loc, yaw)
        records.append({
            "frame": f,
            "loc": loc,
            "yaw": yaw,
            "body_tilt": tilt,
            "body_roll": -0.04 * t,
            "bounce": -0.032 * t,
            "squash": 1.0 - 0.025 * t,
            "head_yaw": 0.085 * shake,
            "head_pitch": 0.18 * t,
            "head_roll": 0.06 * t,
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "relaxed_curl",
            "hand_R": "open_stop" if t >= 0.15 or env < -0.05 else "relaxed_curl",
            "hand_rot_R": (0.45 * t, -0.35 * t, 0.20 * t),
            "expr": expr,
        })
    _apply_pose_series(hero, records)
    return {"animation": "facepalm_groan", "f0": f0, "f1": f1, "stance_windows_L": [(f0, f1)], "stance_windows_R": [(f0, f1)]}


# 14. take_hit_recoil
def take_hit_recoil(hero, f0, f1, from_side="L", *, loc=(0, 0, 0), yaw=0.0):
    """Sharp comic impact recoil away from `from_side` + `cringe_teeth` with braced planted feet."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    push = +1.0 if str(from_side).upper() == "L" else -1.0  # Hit from L (-X) knocks torso toward +X!

    foot_L_w = local_to_world_point(loc, yaw, (-0.135, -0.01, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+0.135, +0.02, 0.0))

    guard_L = ((-0.16 + 0.06 * push, -0.22, 0.24), (-0.26 + 0.04 * push, -0.06, 0.11))
    guard_R = ((+0.16 + 0.06 * push, -0.22, 0.24), (+0.26 + 0.04 * push, -0.06, 0.11))

    span = f1 - f0
    records = []
    for f in range(f0, f1 + 1):
        if span < 6:
            shock = 1.0
        else:
            s = (f - f0) / span
            if s <= 0.08:
                shock = 0.0
            elif s <= 0.22:
                shock = ease5((s - 0.08) / 0.14)
            elif s <= 0.55:
                shock = lerp(1.0, 0.52, ease5((s - 0.22) / 0.33))
            else:
                shock = lerp(0.52, 0.0, ease5((s - 0.55) / 0.45))

        cur_loc = local_to_world_point(loc, yaw, (0.065 * push * shock, +0.045 * shock, 0.0))
        cur_yaw = yaw + 0.18 * push * shock
        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, cur_loc, cur_yaw)

        hit_on = shock >= 0.15 or span < 6
        expr = ("cringe_teeth" if hit_on else "idle_cute") if f == f0 else ("cringe_teeth" if hit_on else None)
        records.append({
            "frame": f,
            "loc": cur_loc,
            "yaw": cur_yaw,
            "body_tilt": -0.18 * shock,
            "body_roll": 0.24 * push * shock,
            "bounce": -0.045 * shock,
            "squash": 1.0 - 0.065 * shock,
            "head_yaw": 0.32 * push * shock,
            "head_pitch": -0.12 * shock,
            "head_roll": 0.22 * push * shock,
            "arm_L": arm_lerp(REST_ARM_L, guard_L, shock),
            "arm_R": arm_lerp(REST_ARM_R, guard_R, shock),
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "open_stop" if shock > 0.25 else "relaxed_curl",
            "hand_R": "fist" if shock > 0.25 else "relaxed_curl",
            "expr": expr,
        })
    _apply_pose_series(hero, records)
    return {"animation": "take_hit_recoil", "f0": f0, "f1": f1, "stance_windows_L": [(f0, f1)], "stance_windows_R": [(f0, f1)]}


# 15. phone_scroll_zombie
def phone_scroll_zombie(hero, f0, f1, *, loc=(0, 0, 0), yaw=0.0, collection=None):
    """Hunched holding glowing 3D smartphone in `L` hand + `R` thumb scroll + `phone_zombie`."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    foot_L_w = local_to_world_point(loc, yaw, (-STANCE_X, 0.0, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+STANCE_X, 0.0, 0.0))

    phone_obj, phone_objs = _build_smartphone_prop(hero, f0, f1, collection=collection)

    # Hold phone at chest height (-Y = -0.25, Z = +0.14) so droopy `phone_zombie` eyes stay 100% visible!
    hold_L = ((-0.065, -0.255, 0.135), (-0.215, -0.095, 0.035))
    records = []
    for f in range(f0, f1 + 1):
        cyc = ((f - f0) % 18) / 18.0
        swipe = ease5(cyc / 0.55) if cyc <= 0.55 else 1.0 - ease5((cyc - 0.55) / 0.45)
        tap_z = 0.125 + 0.048 * swipe
        tap_y = -0.245 + 0.016 * math.sin(math.pi * swipe)
        scroll_R = ((+0.035, tap_y, tap_z), (+0.225, -0.095, 0.045))

        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, loc, yaw)
        records.append({
            "frame": f,
            "loc": loc,
            "yaw": yaw,
            "body_tilt": 0.19,
            "body_roll": -0.025,
            "bounce": -0.025 + 0.004 * math.sin((f - f0) * 0.25),
            "squash": 0.98,
            "head_yaw": -0.03,
            "head_pitch": 0.24,  # Gazing down at glowing screen while keeping eyes visible to camera
            "head_roll": 0.04,
            "arm_L": hold_L,
            "arm_R": scroll_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": "relaxed_curl",
            "hand_R": "point",
            "hand_rot_L": (-0.55, 0.25, 0.15),
            "expr": "phone_zombie" if f == f0 else None,
        })
    _apply_pose_series(hero, records)
    if phone_obj is not None:
        hero.attach_prop(phone_obj, side="L", f_start=f0, f_end=f1, offset=(0.0, 0.0, 0.0), rot_euler=(-0.65, 0.0, 0.0))
    return {
        "animation": "phone_scroll_zombie",
        "f0": f0,
        "f1": f1,
        "phone_object": phone_obj,
        "phone_objects": phone_objs,
        "stance_windows_L": [(f0, f1)],
        "stance_windows_R": [(f0, f1)],
    }


# 16. pickup_and_present
def pickup_and_present(hero, f0, f1, prop_obj, *, loc=(0, 0, 0), yaw=0.0, side="R"):
    """Crouch/reach to `prop_obj` initial location -> `0.000 m` grab -> stand & present proudly."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    side_u = "L" if str(side).upper() == "L" else "R"
    sgn = -1.0 if side_u == "L" else +1.0

    foot_L_w = local_to_world_point(loc, yaw, (-0.125, -0.01, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+0.125, -0.01, 0.0))

    init_loc = tuple(float(c) for c in getattr(prop_obj, "location", (loc[0] + 0.20 * sgn, loc[1] - 0.30, loc[2] + 0.12)))
    init_rot = tuple(float(c) for c in getattr(prop_obj, "rotation_euler", (0.0, 0.0, 0.0)))

    span = f1 - f0
    f_grab = f0 if span < 6 else f0 + max(2, round(span * 0.40))

    # Compute crouch and exact body-local reach target for `init_loc`
    rel_prop = world_to_root_local(init_loc, loc, yaw)
    crouch_bounce = clamp(rel_prop[2] - 0.48, -0.18, 0.0)
    crouch_tilt = clamp(0.32 * (1.0 - clamp(rel_prop[2] / 0.65, 0.0, 1.0)), 0.06, 0.34)

    # Approximate body-local target (refined with exact matrix_world when bpy is active!)
    ct, st = math.cos(crouch_tilt), math.sin(crouch_tilt)
    dy_b = rel_prop[1]
    dz_b = rel_prop[2] - (BODY_PIVOT_Z + crouch_bounce)
    bx = rel_prop[0]
    by = ct * dy_b + st * dz_b
    bz = -st * dy_b + ct * dz_b

    if bpy is not None and hasattr(hero, "body") and getattr(hero.body, "matrix_world", None) is not None:
        leg_Lg, leg_Rg = pinned_leg_pair(foot_L_w, foot_R_w, loc, yaw)
        hero.pose(
            None, loc=loc, yaw=yaw, body_tilt=crouch_tilt, bounce=crouch_bounce, squash=0.95,
            arm_L=REST_ARM_L, arm_R=REST_ARM_R, leg_L=leg_Lg, leg_R=leg_Rg,
        )
        bpy.context.view_layer.update()
        inv_b = hero.body.matrix_world.inverted()
        b_vec = inv_b @ Vector(init_loc)
        bx, by, bz = float(b_vec.x), float(b_vec.y), float(b_vec.z)

    # Clamp within natural chibi arm reach from shoulder so sleeve never hyper-extends
    dx_s, dy_s, dz_s = bx - sgn * SHOULDER_X, by, bz - SHOULDER_Z
    reach_len = math.sqrt(dx_s * dx_s + dy_s * dy_s + dz_s * dz_s)
    max_reach = 0.44
    if reach_len > max_reach and reach_len > 1e-6:
        scale = max_reach / reach_len
        bx = sgn * SHOULDER_X + dx_s * scale
        by = dy_s * scale
        bz = SHOULDER_Z + dz_s * scale

    grab_arm = ((bx, by, bz), (sgn * 0.24, min(-0.04, by * 0.48), max(0.04, (SHOULDER_Z + bz) * 0.52)))
    present_arm = ((sgn * 0.225, -0.325, 0.235), (sgn * 0.275, -0.115, 0.085))
    support_off_arm = ((-sgn * 0.215, -0.215, 0.125), (-sgn * 0.255, -0.055, 0.055))
    rest_main = REST_ARM_L if side_u == "L" else REST_ARM_R
    rest_off = REST_ARM_R if side_u == "L" else REST_ARM_L

    records = []
    for f in range(f0, f1 + 1):
        if span < 6 or f >= f_grab:
            u = 1.0 if (span < 6 or f1 == f_grab) else ease5(min(1.0, (f - f_grab) / min(16.0, max(1.0, (f1 - f_grab) * 0.65))))
            main_arm = arm_lerp(grab_arm, present_arm, u)
            off_arm = arm_lerp(rest_off, support_off_arm, u)
            tilt = lerp(crouch_tilt, -0.08, u)
            bounce = lerp(crouch_bounce, 0.015, u)
            sq = lerp(0.95, 1.02, u)
            hyaw, hpitch = _aim_angles_toward(loc, yaw, local_to_world_point(loc, yaw, (sgn * 0.12, -1.8, 1.05)))
            hyaw *= u
            hpitch *= u
            expr = "hype_letsgo" if (f == f_grab or (span < 6 and f == f0)) else None
            off_hand = "open_stop" if u > 0.45 else "relaxed_curl"
        else:
            u = ease5((f - f0) / max(1, f_grab - f0))
            main_arm = arm_lerp(rest_main, grab_arm, u)
            off_arm = rest_off
            tilt = crouch_tilt * u
            bounce = crouch_bounce * u
            sq = lerp(1.0, 0.95, u)
            hyaw, hpitch = _aim_angles_toward(loc, yaw, init_loc)
            hyaw *= u
            hpitch *= u
            expr = "curious_o" if f == f0 else None
            off_hand = "relaxed_curl"

        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, loc, yaw)
        records.append({
            "frame": f,
            "loc": loc,
            "yaw": yaw,
            "body_tilt": tilt,
            "body_roll": -0.04 * sgn * (1.0 if f >= f_grab else 0.0),
            "bounce": bounce,
            "squash": sq,
            "head_yaw": hyaw,
            "head_pitch": hpitch,
            "head_roll": -0.05 * sgn,
            "arm_L": main_arm if side_u == "L" else off_arm,
            "arm_R": main_arm if side_u == "R" else off_arm,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": ("relaxed_curl" if side_u == "L" else off_hand),
            "hand_R": ("relaxed_curl" if side_u == "R" else off_hand),
            "expr": expr,
        })

    _apply_pose_series(hero, records)

    # Keep `prop_obj` resting cleanly at `init_loc` prior to `f_grab`, then 0.000 m locked on `[f_grab, f1]`
    if prop_obj is not None and hasattr(prop_obj, "keyframe_insert"):
        for pre_f in range(f0, f_grab):
            prop_obj.location = init_loc
            prop_obj.rotation_euler = init_rot
            prop_obj.keyframe_insert("location", frame=pre_f)
            prop_obj.keyframe_insert("rotation_euler", frame=pre_f)
    if prop_obj is not None:
        hero.attach_prop(prop_obj, side=side_u, f_start=f_grab, f_end=f1, offset=(0.0, 0.0, 0.0), rot_euler=(0.0, 0.0, 0.0))

    return {
        "animation": "pickup_and_present",
        "f0": f0,
        "f1": f1,
        "grab_frame": f_grab,
        "stance_windows_L": [(f0, f1)],
        "stance_windows_R": [(f0, f1)],
    }


# 17. throw_prop_at
def throw_prop_at(hero, f0, f1, prop_obj, target_xyz, *, loc=(0, 0, 0), yaw=0.0, side="R"):
    """Held in hand -> pitcher wind-up -> release -> clean ballistic arc landing on `target_xyz`."""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    target = tuple(float(c) for c in target_xyz)
    side_u = "L" if str(side).upper() == "L" else "R"
    sgn = -1.0 if side_u == "L" else +1.0

    foot_L_w = local_to_world_point(loc, yaw, (-0.135, -0.03 * sgn, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+0.135, +0.03 * sgn, 0.0))

    span = f1 - f0
    f_rel = f0 if span < 4 else f0 + max(2, round(span * 0.36))
    f_land = f1 if f1 - f_rel <= 3 else f_rel + max(2, round((f1 - f_rel) * 0.76))

    hold_arm = ((sgn * 0.21, -0.22, 0.16), (sgn * 0.24, -0.06, 0.06))
    wind_arm = ((sgn * 0.28, +0.16, 0.28), (sgn * 0.32, +0.08, 0.14))
    rel_arm = ((sgn * 0.19, -0.37, 0.27), (sgn * 0.24, -0.15, 0.14))
    follow_arm = ((-sgn * 0.06, -0.28, 0.05), (sgn * 0.18, -0.14, 0.08))
    aim_off_arm = ((-sgn * 0.18, -0.28, 0.18), (-sgn * 0.24, -0.10, 0.08))
    rest_off = REST_ARM_R if side_u == "L" else REST_ARM_L

    aim_yaw, aim_pitch = _aim_angles_toward(loc, yaw, target)

    records = []
    for f in range(f0, f1 + 1):
        if span < 4:
            main_arm = rel_arm
            off_arm = aim_off_arm
            cur_yaw = yaw + 0.15 * aim_yaw
            tilt = 0.12
            bounce = 0.0
            sq = 1.0
            main_hand = "open_stop"
            expr = "hype_letsgo" if f == f0 else None
        elif f <= f_rel:
            u = (f - f0) / max(1, f_rel - f0)
            if u <= 0.62:
                w = ease5(u / 0.62)
                main_arm = arm_lerp(hold_arm, wind_arm, w)
                off_arm = arm_lerp(rest_off, aim_off_arm, w)
                cur_yaw = yaw - 0.26 * sgn * w
                tilt = -0.14 * w
                bounce = -0.035 * w
                sq = 1.0 - 0.03 * w
            else:
                s = ease5((u - 0.62) / 0.38)
                main_arm = arm_lerp(wind_arm, rel_arm, s)
                off_arm = arm_lerp(aim_off_arm, rest_off, 0.5 * s)
                cur_yaw = yaw + lerp(-0.26 * sgn, 0.22 * sgn, s)
                tilt = lerp(-0.14, 0.20, s)
                bounce = lerp(-0.035, 0.025, s)
                sq = lerp(0.97, 1.04, s)
            main_hand = "open_stop" if f == f_rel else "relaxed_curl"
            expr = "curious_o" if f == f0 else ("hype_letsgo" if f == f_rel else None)
        else:
            u = (f - f_rel) / max(1, f1 - f_rel)
            ft = ease5(min(1.0, u / 0.45))
            recover = ease5(clamp((u - 0.50) / 0.50))
            mid_arm = arm_lerp(rel_arm, follow_arm, ft)
            main_arm = arm_lerp(mid_arm, REST_ARM_L if side_u == "L" else REST_ARM_R, recover * 0.65)
            off_arm = rest_off
            cur_yaw = yaw + lerp(0.22 * sgn, 0.12 * aim_yaw, recover)
            tilt = lerp(0.20, 0.04, recover)
            bounce = lerp(0.025, 0.0, ft)
            sq = 1.0
            main_hand = "open_stop" if u < 0.35 else "relaxed_curl"
            expr = "smug_wink" if f == f_land else None

        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, loc, cur_yaw)
        records.append({
            "frame": f,
            "loc": loc,
            "yaw": cur_yaw,
            "body_tilt": tilt,
            "body_roll": -0.05 * sgn,
            "bounce": bounce,
            "squash": sq,
            "head_yaw": clamp(aim_yaw - (cur_yaw - yaw), -0.95, 0.95),
            "head_pitch": aim_pitch,
            "head_roll": 0.0,
            "arm_L": main_arm if side_u == "L" else off_arm,
            "arm_R": main_arm if side_u == "R" else off_arm,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": main_hand if side_u == "L" else "relaxed_curl",
            "hand_R": main_hand if side_u == "R" else "relaxed_curl",
            "expr": expr,
        })

    _apply_pose_series(hero, records)

    # Pin prop in hand during `[f0, f_rel]`, then launch clean parabolic arc to `target_xyz`!
    if prop_obj is not None:
        hero.attach_prop(prop_obj, side=side_u, f_start=f0, f_end=f_rel, offset=(0.0, 0.0, 0.0), rot_euler=(0.0, 0.0, 0.0))
        rel_pos = local_to_world_point(loc, yaw, (sgn * 0.19, -0.37, BODY_PIVOT_Z + 0.27))
        rel_rot = (0.0, 0.0, 0.0)
        if bpy is not None:
            bpy.context.scene.frame_set(f_rel)
            bpy.context.view_layer.update()
            sock = getattr(hero, "hand_socket_L" if side_u == "L" else "hand_socket_R", None)
            if sock is not None:
                rel_pos = tuple(float(c) for c in sock.matrix_world.translation)
            elif hasattr(prop_obj, "matrix_world"):
                rel_pos = tuple(float(c) for c in prop_obj.matrix_world.translation)
            rel_rot = tuple(float(c) for c in prop_obj.rotation_euler)

        horiz_d = math.hypot(target[0] - rel_pos[0], target[1] - rel_pos[1])
        arc_h = max(0.28, 0.30 * horiz_d + 0.18)

        if hasattr(prop_obj, "keyframe_insert"):
            for f in range(f_rel + 1, f1 + 1):
                if f < f_land:
                    u = (f - f_rel) / max(1, f_land - f_rel)
                    px = lerp(rel_pos[0], target[0], u)
                    py = lerp(rel_pos[1], target[1], u)
                    pz = lerp(rel_pos[2], target[2], u) + 4.0 * arc_h * u * (1.0 - u)
                    rx = lerp(rel_rot[0], math.tau, u)
                    ry = lerp(rel_rot[1], 0.0, u)
                    rz = lerp(rel_rot[2], 0.0, u)
                else:
                    px, py, pz = target
                    rx, ry, rz = 0.0, 0.0, 0.0
                prop_obj.location = (px, py, pz)
                prop_obj.rotation_euler = (rx, ry, rz)
                prop_obj.keyframe_insert("location", frame=f)
                prop_obj.keyframe_insert("rotation_euler", frame=f)
            if getattr(prop_obj, "animation_data", None) and prop_obj.animation_data.action:
                for fc in prop_obj.animation_data.action.fcurves:
                    if fc.data_path in {"location", "rotation_euler"}:
                        for kp in fc.keyframe_points:
                            kp.interpolation = "LINEAR"

    return {
        "animation": "throw_prop_at",
        "f0": f0,
        "f1": f1,
        "release_frame": f_rel,
        "land_frame": f_land,
        "stance_windows_L": [(f0, f1)],
        "stance_windows_R": [(f0, f1)],
    }


# 18. dramatic_double_take
def dramatic_double_take(hero, f0, f1, look_target, *, loc=(0, 0, 0), yaw=0.0):
    """Calm glance -> casual look away -> 4-frame supersonic snap whip toward `look_target` + `mortified_blush`!"""
    f0, f1 = _validate_range(f0, f1)
    loc = tuple(float(c) for c in loc)
    yaw = float(yaw)
    target = tuple(float(c) for c in look_target)
    foot_L_w = local_to_world_point(loc, yaw, (-0.12, 0.0, 0.0))
    foot_R_w = local_to_world_point(loc, yaw, (+0.12, 0.0, 0.0))

    t_yaw, t_pitch = _aim_angles_toward(loc, yaw, target)
    away_yaw = -0.35 * (1.0 if t_yaw >= 0.0 else -1.0)

    shock_L = ((-0.23, -0.20, 0.28), (-0.28, -0.05, 0.12))
    shock_R = ((+0.23, -0.20, 0.28), (+0.28, -0.05, 0.12))

    span = f1 - f0
    records = []
    for f in range(f0, f1 + 1):
        if span < 8:
            hyaw, hpitch = t_yaw * 0.78, t_pitch
            cur_yaw = yaw + t_yaw * 0.22
            arm_L, arm_R = shock_L, shock_R
            bounce, sq = 0.015, 1.03
            hand = "open_stop"
            expr = "mortified_blush" if f == f0 else None
        else:
            s = (f - f0) / span
            if s <= 0.22:
                # Beat 1: casual passing glance toward target
                u = ease5(s / 0.22)
                hyaw = 0.55 * t_yaw * u
                hpitch = 0.45 * t_pitch * u
                cur_yaw = yaw
                arm_L, arm_R = REST_ARM_L, REST_ARM_R
                bounce, sq = 0.0, 1.0
                hand = "relaxed_curl"
                expr = "idle_cute" if f == f0 else None
            elif s <= 0.46:
                # Beat 2: casual look away + delayed realization freeze!
                u = ease5(min(1.0, (s - 0.22) / 0.16))
                hyaw = lerp(0.55 * t_yaw, away_yaw, u)
                hpitch = lerp(0.45 * t_pitch, 0.04, u)
                cur_yaw = yaw
                arm_L, arm_R = REST_ARM_L, REST_ARM_R
                bounce, sq = -0.015 * u, 1.0 - 0.015 * u
                hand = "relaxed_curl"
                expr = "whatever_eyeroll" if abs(s - 0.30) < (1.0 / span) else None
            elif s <= 0.60:
                # Beat 3: rapid snap whip onto `look_target`!
                u = ease5((s - 0.46) / 0.14)
                cur_yaw = yaw + 0.24 * t_yaw * u
                hyaw = lerp(away_yaw, 0.76 * t_yaw, u)
                hpitch = lerp(0.04, t_pitch, u)
                arm_L = arm_lerp(REST_ARM_L, shock_L, u)
                arm_R = arm_lerp(REST_ARM_R, shock_R, u)
                pop = math.sin(math.pi * u)
                bounce = 0.045 * pop
                sq = 1.0 + 0.065 * pop
                hand = "open_stop" if u > 0.35 else "relaxed_curl"
                expr = "mortified_blush" if u >= 0.45 else None
            else:
                # Beat 4: settled locked-on shock hold!
                u = ease5(min(1.0, (s - 0.60) / 0.20))
                cur_yaw = yaw + 0.24 * t_yaw
                hyaw = 0.76 * t_yaw
                hpitch = t_pitch
                arm_L = arm_lerp(shock_L, ((-0.22, -0.19, 0.25), (-0.27, -0.05, 0.11)), u)
                arm_R = arm_lerp(shock_R, ((+0.22, -0.19, 0.25), (+0.27, -0.05, 0.11)), u)
                bounce = lerp(0.01, -0.012, u)
                sq = lerp(1.02, 0.99, u)
                hand = "open_stop"
                expr = "mortified_blush" if abs(s - 0.61) < (1.2 / span) else None

        leg_L, leg_R = pinned_leg_pair(foot_L_w, foot_R_w, loc, cur_yaw)
        records.append({
            "frame": f,
            "loc": loc,
            "yaw": cur_yaw,
            "body_tilt": -0.08 if bounce > 0.01 else 0.02,
            "body_roll": -0.04 * (1.0 if t_yaw >= 0 else -1.0) * (1.0 if hand == "open_stop" else 0.0),
            "bounce": bounce,
            "squash": sq,
            "head_yaw": hyaw,
            "head_pitch": hpitch,
            "head_roll": -0.06 * (1.0 if hand == "open_stop" else 0.0),
            "arm_L": arm_L,
            "arm_R": arm_R,
            "leg_L": leg_L,
            "leg_R": leg_R,
            "hand_L": hand,
            "hand_R": hand,
            "expr": expr,
        })
    _apply_pose_series(hero, records)
    return {"animation": "dramatic_double_take", "f0": f0, "f1": f1, "stance_windows_L": [(f0, f1)], "stance_windows_R": [(f0, f1)]}
