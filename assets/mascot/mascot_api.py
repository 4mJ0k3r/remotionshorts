"""Shared Public Python & Blender 4.2 API for the Official Mascot (`assets/mascot/`).

Exposes:
  - Constants: `EXPRESSIONS` (12), `VISEMES` (6), `HAND_POSES` (7)
  - `load_mascot(collection, name="Mascot", bottom_style="pajamas", arm_style="hoodie") -> MascotRig`
  - `MascotRig` methods:
      * `pose(...)`
      * `set_expression(expr_name, frame=None)`
      * `auto_lipsync(audio_path, start_frame, end_frame, base_expr="idle_cute", fps=30)`
      * `attach_prop(prop_obj, side="R", f_start=1, f_end=100, offset=(0,0,0), rot_euler=(0,0,0))`
      * `update_ink(camera, frame=None, pixels=4.2)`
      * `head_bbox_ratio() -> dict`
      * `finish_bake()`
"""
from __future__ import annotations

import math
from pathlib import Path
import subprocess
import sys
import wave

try:
    import bpy
    from mathutils import Euler, Matrix, Quaternion, Vector
except ModuleNotFoundError as _exc:
    if _exc.name not in {"bpy", "mathutils"}:
        raise
    bpy = None
    Euler = Matrix = Quaternion = Vector = None

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "scripts/ricks_v2_kit.py").is_file())
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

EXPRESSIONS = (
    "idle_cute",
    "curious_o",
    "chill_laugh",
    "hype_letsgo",
    "cringe_teeth",
    "whatever_eyeroll",
    "phone_zombie",
    "sulk_pout",
    "mortified_blush",
    "smug_wink",
    "crush_hearts",
    "ugh_groan",
)

VISEMES = (
    "vis_closed",
    "vis_AA",
    "vis_EE",
    "vis_OH",
    "vis_OO",
    "vis_FV",
)

ALL_EXPRESSIONS = EXPRESSIONS + VISEMES

HAND_POSES = (
    "relaxed_curl",
    "open_stop",
    "power_claw",
    "fist",
    "point",
    "thumbs_up_ok",
    "behind_head",
)

MASTER_BLEND_PATH = ROOT / "assets" / "mascot" / "mascot_master.blend"
MASTER_COLLECTION_NAME = "MascotHero"

BODY_REST_Z = 0.560
HEAD_REL_Z = 0.400
SHOULDER_L = (-0.155, 0.0, 0.180)
SHOULDER_R = (+0.155, 0.0, 0.180)
DEFAULT_ARM_L = (-0.220, -0.060, -0.060)
DEFAULT_ARM_R = (+0.220, -0.060, -0.060)
DEFAULT_LEG_L = (-0.105, 0.0, 0.0)
DEFAULT_LEG_R = (+0.105, 0.0, 0.0)
HIP_X = 0.102
HIP_REL_Z = -0.180


def _ink_thickness_m(depth: float | None, lens_mm: float | None, pixels: float, default: float = 0.0062) -> float:
    if depth is None or lens_mm is None or depth <= 0.0 or lens_mm <= 0.0 or pixels <= 0.0:
        return default
    return depth * 36.0 * pixels / (lens_mm * 640.0)


def _is_pair_of_vec3(val) -> bool:
    if not isinstance(val, (tuple, list)) or len(val) != 2:
        return False
    a, b = val
    return hasattr(a, "__len__") and hasattr(b, "__len__") and len(a) == 3 and len(b) == 3


def _auto_elbow(shoulder: Vector, hand: Vector, side: int) -> Vector:
    """Compute a natural chibi outward/downward elbow in `body`-local space."""
    span = hand - shoulder
    dist = span.length
    mid = shoulder.lerp(hand, 0.50)
    arm_len = 0.295
    sag = math.sqrt(max(0.0, max(0.0, 0.5 * arm_len) ** 2 - (0.5 * dist) ** 2))
    sag = max(0.028, min(0.095, sag))

    # High hands (e.g. behind_head / celebrate) flare elbows wide; forward/low hands drop elbows outward & down
    if hand.z > shoulder.z + 0.08:
        pole = Vector((side * 0.90, -0.22, 0.18))
    elif hand.y < -0.18:
        pole = Vector((side * 0.68, 0.16, -0.68))
    else:
        pole = Vector((side * 0.72, 0.24, -0.60))

    if dist > 1e-5:
        axis = span / dist
        pole = pole - axis * pole.dot(axis)
    if pole.length_squared < 1e-6:
        pole = Vector((float(side), 0.0, -0.2))
    pole.normalize()
    return mid + pole * sag


def _auto_knee(hip: Vector, ankle: Vector, side: int) -> Vector:
    """Compute a natural forward-bending chibi knee in `root`-local space."""
    span = ankle - hip
    dist = span.length
    mid = hip.lerp(ankle, 0.52)
    leg_len = 0.316
    bend_amt = math.sqrt(max(0.0, (0.5 * leg_len) ** 2 - (0.5 * dist) ** 2))
    bend_amt = max(0.012, min(0.125, bend_amt))

    # Knees bend forward (-Y) with slight chibi outward stance
    pole = Vector((side * 0.16, -0.98, 0.08))
    if dist > 1e-5:
        axis = span / dist
        pole = pole - axis * pole.dot(axis)
    if pole.length_squared < 1e-6:
        pole = Vector((0.0, -1.0, 0.0))
    pole.normalize()
    return mid + pole * bend_amt


def _wrist_basis_quat(forearm_dir: Vector, side: int) -> Quaternion:
    """Build smooth orthonormal wrist quaternion (`-Y` along `forearm_dir`, `+Z` up)."""
    d = forearm_dir.normalized() if forearm_dir.length > 1e-5 else Vector((0.0, -0.2, -0.98)).normalized()
    y_axis = -d
    ref_up = Vector((0.0, -0.26, 1.0)).normalized()
    if abs(y_axis.dot(ref_up)) > 0.94:
        ref_up = Vector((float(side) * 0.65, -0.76, 0.0)).normalized()
    x_axis = y_axis.cross(ref_up)
    if x_axis.length_squared < 1e-6:
        x_axis = Vector((1.0, 0.0, 0.0))
    x_axis.normalize()
    z_axis = x_axis.cross(y_axis).normalized()
    mat3 = Matrix((
        (x_axis.x, y_axis.x, z_axis.x),
        (x_axis.y, y_axis.y, z_axis.y),
        (x_axis.z, y_axis.z, z_axis.z),
    ))
    return mat3.to_quaternion()


def _pose_bezier_spline(curve_obj, knots: list[Vector], frame: int | None):
    """Set smooth `FREE` Bezier knots + tangents and optionally keyframe them."""
    pts = curve_obj.data.splines[0].bezier_points
    n = len(knots)
    if len(pts) != n:
        raise RuntimeError(f"Expected {n} Bezier points on {curve_obj.name}, got {len(pts)}")
    tangents = []
    for i in range(n):
        if i == 0:
            d = knots[1] - knots[0]
        elif i == n - 1:
            d = knots[-1] - knots[-2]
        else:
            d = knots[i + 1] - knots[i - 1]
        tangents.append(d.normalized() if d.length > 1e-6 else Vector((0.0, 0.0, -1.0)))

    for i, (pt, knot, tan) in enumerate(zip(pts, knots, tangents)):
        left_len = (knot - knots[i - 1]).length * 0.32 if i > 0 else 0.0
        right_len = (knots[i + 1] - knot).length * 0.32 if i < n - 1 else 0.0
        pt.co = knot
        pt.handle_left_type = "FREE"
        pt.handle_right_type = "FREE"
        pt.handle_left = knot - tan * left_len
        pt.handle_right = knot + tan * right_len
        if frame is not None:
            for ch in ("co", "handle_left", "handle_right"):
                curve_obj.data.keyframe_insert(f"splines[0].bezier_points[{i}].{ch}", frame=frame)


def _key_constant_visibility(obj, visible: bool, frame: int | None):
    hide = not visible
    obj.hide_render = hide
    obj.hide_viewport = hide
    if frame is not None:
        for prop in ("hide_render", "hide_viewport"):
            obj.keyframe_insert(prop, frame=frame)
            if obj.animation_data and obj.animation_data.action:
                fc = obj.animation_data.action.fcurves.find(prop)
                if fc is not None:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "CONSTANT"


def _decode_audio_mono_16k(audio_path: Path):
    """Decode WAV or compressed audio (MP3/M4A/AAC) into float32 mono samples at 16 kHz."""
    import numpy as np

    audio_path = Path(audio_path).expanduser().resolve()
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Fast native pure-Python path for standard 16-bit PCM WAV files
    if audio_path.suffix.lower() == ".wav":
        try:
            with wave.open(str(audio_path), "rb") as wf:
                if wf.getsampwidth() == 2 and wf.getcomptype() == "NONE":
                    sr = wf.getframerate()
                    n_ch = wf.getnchannels()
                    raw = wf.readframes(wf.getnframes())
                    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                    if n_ch > 1:
                        pcm = pcm.reshape(-1, n_ch).mean(axis=1)
                    return pcm, float(sr)
        except wave.Error:
            pass

    proc = subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-i",
            str(audio_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "s16le",
            "-",
        ],
        capture_output=True,
        check=True,
    )
    pcm = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return pcm, 16000.0


class MascotRig:
    """High-level animation & look controller for the Official Mascot."""

    def __init__(
        self,
        objects: list,
        *,
        name: str = "Mascot",
        bottom_style: str = "pajamas",
        arm_style: str = "hoodie",
    ):
        self.name = name
        self._objects = list(objects)
        self._by_tag: dict[str, object] = {}
        self.expressions: dict[str, object] = {}
        self._hands_L: dict[str, list] = {p: [] for p in HAND_POSES}
        self._hands_R: dict[str, list] = {p: [] for p in HAND_POSES}
        self._mesh_ink_mods: list = []
        self._curve_ink_mods: list = []
        self._cel_materials: set = set()
        self._prop_attachments: list[dict] = []
        self._prev_wrist_quat = {"L": None, "R": None}

        for obj in self._objects:
            tag = obj.get("mascot_tag")
            if isinstance(tag, str):
                if tag.startswith("expr:"):
                    self.expressions[tag.split(":", 1)[1]] = obj
                elif tag.startswith("hand_L:") or tag.startswith("hand_ink_L:"):
                    pose_k = tag.split(":", 1)[1]
                    if pose_k in self._hands_L:
                        self._hands_L[pose_k].append(obj)
                elif tag.startswith("hand_R:") or tag.startswith("hand_ink_R:"):
                    pose_k = tag.split(":", 1)[1]
                    if pose_k in self._hands_R:
                        self._hands_R[pose_k].append(obj)
                else:
                    self._by_tag[tag] = obj

            if obj.get("ricks_role") == "ink":
                for mod in obj.modifiers:
                    if mod.type == "DISPLACE":
                        self._mesh_ink_mods.append((obj, mod, float(obj.get("mascot_ink_scale", 1.0))))

            for mod in obj.modifiers:
                if mod.type == "NODES" and mod.node_group and "curve comic ink" in mod.node_group.name.lower():
                    sock_id = next(
                        (
                            it.identifier
                            for it in mod.node_group.interface.items_tree
                            if it.item_type == "SOCKET" and it.in_out == "INPUT" and it.name == "Ink Width"
                        ),
                        None,
                    )
                    if sock_id:
                        self._curve_ink_mods.append((obj, mod, sock_id, float(obj.get("mascot_ink_scale", 0.92))))

            if getattr(obj, "data", None) is not None and hasattr(obj.data, "materials"):
                for mat in obj.data.materials:
                    if mat is not None and mat.get("mascot_cel"):
                        self._cel_materials.add(mat)

        self.root = self._by_tag["root"]
        self.body = self._by_tag["body"]
        self.head = self._by_tag["head"]
        self._head_mesh = self._by_tag["head_mesh"]
        self.hand_socket_L = self._by_tag["hand_socket_L"]
        self.hand_socket_R = self._by_tag["hand_socket_R"]
        self.light_empty = self._by_tag["light_empty"]
        self.drawn_light = self.light_empty
        self._wrist_L = self._by_tag["wrist_L"]
        self._wrist_R = self._by_tag["wrist_R"]
        self._wrist_L.rotation_mode = "QUATERNION"
        self._wrist_R.rotation_mode = "QUATERNION"
        self._foot_L = self._by_tag["foot_L"]
        self._foot_R = self._by_tag["foot_R"]
        self.foot_L = self._foot_L
        self.foot_R = self._foot_R
        self._string_L = self._by_tag["string_L"]
        self._string_R = self._by_tag["string_R"]

        self.bottom_style = bottom_style
        self.arm_style = arm_style
        self.set_styles(bottom_style=bottom_style, arm_style=arm_style)

    @classmethod
    def from_collection(
        cls,
        collection,
        *,
        prefix: str = "Mascot",
        bottom_style: str = "pajamas",
        arm_style: str = "hoodie",
    ) -> "MascotRig":
        return cls(list(collection.all_objects), name=prefix, bottom_style=bottom_style, arm_style=arm_style)

    def set_styles(self, *, bottom_style: str | None = None, arm_style: str | None = None):
        """Toggle `bottom_style` ('pajamas'|'shorts') and `arm_style` ('hoodie'|'stick')."""
        if bottom_style is not None:
            if bottom_style not in {"pajamas", "shorts"}:
                raise ValueError(f"bottom_style must be 'pajamas' or 'shorts', got {bottom_style!r}")
            self.bottom_style = bottom_style
            for obj in self._objects:
                bs = obj.get("mascot_bottom_style")
                if bs in {"pajamas", "shorts"}:
                    hide = bs != bottom_style
                    obj.hide_render = hide
                    obj.hide_viewport = hide

        if arm_style is not None:
            if arm_style not in {"hoodie", "stick"}:
                raise ValueError(f"arm_style must be 'hoodie' or 'stick', got {arm_style!r}")
            self.arm_style = arm_style
            for obj in self._objects:
                as_ = obj.get("mascot_arm_style")
                if as_ in {"hoodie", "stick"}:
                    hide = as_ != arm_style
                    obj.hide_render = hide
                    obj.hide_viewport = hide

    def set_expression(self, expr_name: str | None, frame: int | None = None):
        """Switch conformed face decal artwork with a 1-frame `CONSTANT` snap."""
        if expr_name is None:
            return
        if expr_name not in self.expressions:
            raise ValueError(
                f"Unknown expression {expr_name!r}. Valid options: {ALL_EXPRESSIONS}"
            )
        for name, obj in self.expressions.items():
            _key_constant_visibility(obj, name == expr_name, frame)

    def _set_hand_pose(self, side: str, pose_name: str, frame: int | None):
        if pose_name not in HAND_POSES:
            raise ValueError(f"Unknown hand pose {pose_name!r}. Valid options: {HAND_POSES}")
        bank = self._hands_L if side == "L" else self._hands_R
        for name, items in bank.items():
            vis = name == pose_name
            for obj in items:
                _key_constant_visibility(obj, vis, frame)

    def pose(
        self,
        frame: int | None = None,
        loc=(0.0, 0.0, 0.0),
        yaw: float = 0.0,
        body_tilt: float = 0.0,
        body_roll: float = 0.0,
        bounce: float = 0.0,
        squash: float = 1.0,
        head_yaw: float = 0.0,
        head_pitch: float = 0.0,
        head_roll: float = 0.0,
        arm_L=None,
        arm_R=None,
        leg_L=None,
        leg_R=None,
        hand_L: str = "relaxed_curl",
        hand_R: str = "relaxed_curl",
        hand_rot_L=None,
        hand_rot_R=None,
        foot_rot_L=None,
        foot_rot_R=None,
        string_sway=None,
        expr: str | None = None,
    ):
        """Apply or keyframe a full chibi pose (`frame=None` applies immediately)."""
        f = int(frame) if frame is not None else None

        # 1. Root, Body (with volume-preserving squash), and Head (preserving 1:1 marshmallow ratio!)
        self.root.location = Vector(loc)
        self.root.rotation_euler = Euler((0.0, 0.0, float(yaw)), "XYZ")

        sq = max(0.45, min(1.65, float(squash)))
        inv_xy = 1.0 / math.sqrt(sq)
        self.body.location = Vector((0.0, 0.0, BODY_REST_Z + float(bounce)))
        self.body.rotation_euler = Euler((float(body_tilt), float(body_roll), 0.0), "XYZ")
        self.body.scale = Vector((inv_xy, inv_xy, sq))

        # Counter-scale head so body squash bounces head height without squashing the 1:1 marshmallow head!
        self.head.location = Vector((0.0, 0.0, HEAD_REL_Z))
        self.head.rotation_euler = Euler((float(head_pitch), float(head_roll), float(head_yaw)), "XYZ")
        self.head.scale = Vector((1.0 / inv_xy, 1.0 / inv_xy, 1.0 / sq))

        if f is not None:
            for obj, channels in (
                (self.root, ("location", "rotation_euler")),
                (self.body, ("location", "rotation_euler", "scale")),
                (self.head, ("location", "rotation_euler", "scale")),
            ):
                for ch in channels:
                    obj.keyframe_insert(ch, frame=f)

        # 2. Secondary Hoodie Drawstrings (`string_sway` scalar, 2-tuple, or automatic follow-through)
        if string_sway is None:
            sway_roll = -0.55 * float(body_roll)
            sway_pitch = -0.35 * max(-0.4, float(body_tilt)) - 0.65 * max(0.0, float(bounce))
        elif isinstance(string_sway, (int, float)):
            sway_roll = float(string_sway)
            sway_pitch = -0.25 * abs(float(string_sway))
        else:
            sway_roll = float(string_sway[0])
            sway_pitch = float(string_sway[1]) if len(string_sway) > 1 else 0.0

        for s_idx, (s_piv, side_sign) in enumerate(((self._string_L, -1.0), (self._string_R, 1.0))):
            s_piv.rotation_euler = Euler(
                (sway_pitch, sway_roll + side_sign * 0.03 * abs(sway_pitch), sway_roll * 0.25),
                "XYZ",
            )
            if f is not None:
                s_piv.keyframe_insert("rotation_euler", frame=f)

        # 3. Sleeved / Stick IK Arms + 7 Swappable Puffy Hands
        arm_specs = (
            ("L", -1, Vector(SHOULDER_L), arm_L, DEFAULT_ARM_L, hand_L, hand_rot_L, self._wrist_L),
            ("R", +1, Vector(SHOULDER_R), arm_R, DEFAULT_ARM_R, hand_R, hand_rot_R, self._wrist_R),
        )
        for s_lbl, side, shoulder, arm_in, def_hand, h_pose, h_rot, wrist in arm_specs:
            if arm_in is None:
                hand_co = Vector(def_hand)
                elbow_co = _auto_elbow(shoulder, hand_co, side)
            elif _is_pair_of_vec3(arm_in):
                hand_co = Vector(arm_in[0])
                elbow_co = Vector(arm_in[1])
            else:
                hand_co = Vector(arm_in)
                elbow_co = _auto_elbow(shoulder, hand_co, side)

            # Sleeve terminates right at wrist cuff; hand emerges seamlessly from wrist
            arm_knots = [
                shoulder,
                shoulder.lerp(elbow_co, 0.52),
                elbow_co,
                elbow_co.lerp(hand_co, 0.66),
                hand_co,
            ]
            _pose_bezier_spline(self._by_tag[f"sleeve_{s_lbl}"], arm_knots, f)
            _pose_bezier_spline(self._by_tag[f"stick_arm_{s_lbl}"], arm_knots, f)

            forearm_dir = hand_co - elbow_co
            q = _wrist_basis_quat(forearm_dir, side)
            if h_rot is not None:
                q = q @ Euler(tuple(h_rot), "XYZ").to_quaternion()
            prev_q = self._prev_wrist_quat[s_lbl]
            if prev_q is not None and prev_q.dot(q) < 0.0:
                q.negate()
            self._prev_wrist_quat[s_lbl] = q.copy()

            wrist.location = hand_co
            wrist.rotation_quaternion = q
            if f is not None:
                wrist.keyframe_insert("location", frame=f)
                wrist.keyframe_insert("rotation_quaternion", frame=f)

            self._set_hand_pose(s_lbl, h_pose, f)

        # 4. Pajama / Shorts IK Legs + Chunky Sneakers (`fz = 0.0` plants sole flat at `root.z`!)
        body_mat = self.body.rotation_euler.to_matrix()
        leg_specs = (
            ("L", -1, leg_L, DEFAULT_LEG_L, foot_rot_L, self._foot_L),
            ("R", +1, leg_R, DEFAULT_LEG_R, foot_rot_R, self._foot_R),
        )
        for s_lbl, side, leg_in, def_foot, f_rot, foot_piv in leg_specs:
            hip_body = Vector((side * HIP_X * inv_xy, 0.0, HIP_REL_Z * sq))
            hip_root = self.body.location + (body_mat @ hip_body)

            foot_eul = Euler(tuple(f_rot), "XYZ") if f_rot is not None else Euler((0.0, 0.0, 0.0), "XYZ")
            foot_mat = foot_eul.to_matrix()

            if leg_in is None:
                foot_co = Vector(def_foot)
                ankle_co = foot_co + (foot_mat @ Vector((0.0, 0.012, 0.068)))
                knee_co = _auto_knee(hip_root, ankle_co, side)
            elif _is_pair_of_vec3(leg_in):
                foot_co = Vector(leg_in[0])
                knee_co = Vector(leg_in[1])
                ankle_co = foot_co + (foot_mat @ Vector((0.0, 0.012, 0.068)))
            else:
                foot_co = Vector(leg_in)
                ankle_co = foot_co + (foot_mat @ Vector((0.0, 0.012, 0.068)))
                knee_co = _auto_knee(hip_root, ankle_co, side)

            foot_piv.location = foot_co
            foot_piv.rotation_euler = foot_eul
            if f is not None:
                foot_piv.keyframe_insert("location", frame=f)
                foot_piv.keyframe_insert("rotation_euler", frame=f)

            leg_knots = [
                hip_root,
                hip_root.lerp(knee_co, 0.55),
                knee_co,
                ankle_co,
            ]
            _pose_bezier_spline(self._by_tag[f"pajama_{s_lbl}"], leg_knots, f)

            stripe_knots = [
                knot + Vector((side * rad * 0.96, -0.004, 0.0))
                for knot, rad in zip(leg_knots, (0.070, 0.075, 0.080, 0.072))
            ]
            _pose_bezier_spline(self._by_tag[f"stripe_{s_lbl}"], stripe_knots, f)

            short_knots = [hip_root, hip_root.lerp(knee_co, 0.50), knee_co]
            _pose_bezier_spline(self._by_tag[f"short_{s_lbl}"], short_knots, f)

            calf_knots = [knee_co, knee_co.lerp(ankle_co, 0.50), ankle_co]
            _pose_bezier_spline(self._by_tag[f"calf_{s_lbl}"], calf_knots, f)

        # 5. Optional Expression Switch
        if expr is not None:
            self.set_expression(expr, frame=f)

    def auto_lipsync(
        self,
        audio_path: str | Path,
        start_frame: int,
        end_frame: int,
        base_expr: str = "idle_cute",
        fps: int = 30,
    ) -> list[tuple[int, str]]:
        """Decode WAV/MP3 audio and bake `CONSTANT` 1-frame viseme keys over `[start_frame, end_frame]`."""
        import numpy as np

        f0, f1 = int(start_frame), int(end_frame)
        if f1 < f0:
            raise ValueError(f"end_frame ({f1}) must be >= start_frame ({f0})")
        if base_expr not in self.expressions:
            raise ValueError(f"Unknown base_expr {base_expr!r}")

        samples, sr = _decode_audio_mono_16k(Path(audio_path))
        total_frames = f1 - f0 + 1
        win = max(1, int(round(sr / float(fps))))

        rms_vals, zcr_vals = [], []
        for i in range(total_frames):
            s0 = i * win
            s1 = min(len(samples), s0 + win)
            chunk = samples[s0:s1]
            if len(chunk) < 4:
                rms_vals.append(0.0)
                zcr_vals.append(0.0)
                continue
            rms = float(np.sqrt(np.mean(chunk * chunk)))
            signs = chunk >= 0.0
            zcr = float(np.mean(signs[1:] != signs[:-1]))
            rms_vals.append(rms)
            zcr_vals.append(zcr)

        peak_rms = max(max(rms_vals, default=0.0), 1e-4)
        norm_rms = [r / peak_rms for r in rms_vals]

        # Classify per-frame target viseme with 2-frame hold to prevent single-frame chatter
        raw_vis = []
        silent_streak = 10
        for e_val, z_val in zip(norm_rms, zcr_vals):
            if e_val < 0.085:
                silent_streak += 1
                raw_vis.append(base_expr if silent_streak >= 4 else "vis_closed")
            else:
                silent_streak = 0
                if z_val > 0.23 and e_val < 0.46:
                    raw_vis.append("vis_FV")
                elif z_val > 0.145 and e_val >= 0.20:
                    raw_vis.append("vis_EE")
                elif e_val >= 0.62:
                    raw_vis.append("vis_AA")
                elif e_val >= 0.38:
                    raw_vis.append("vis_OH")
                elif e_val >= 0.18:
                    raw_vis.append("vis_OO")
                else:
                    raw_vis.append("vis_closed")

        # Smooth 2-frame hold on active speech visemes
        smoothed = list(raw_vis)
        for i in range(1, len(smoothed) - 1):
            if smoothed[i] != smoothed[i - 1] and smoothed[i - 1] == smoothed[i + 1]:
                smoothed[i] = smoothed[i - 1]
        if smoothed:
            smoothed[-1] = base_expr

        keyed: list[tuple[int, str]] = []
        last_set = None
        for idx, vis_name in enumerate(smoothed):
            frame_num = f0 + idx
            if vis_name != last_set or idx == 0 or idx == len(smoothed) - 1:
                self.set_expression(vis_name, frame=frame_num)
                keyed.append((frame_num, vis_name))
                last_set = vis_name
        return keyed

    def _bake_single_attachment(self, rec: dict):
        scene = bpy.context.scene
        prop_obj = rec["prop_obj"]
        socket = self.hand_socket_L if rec["side"] == "L" else self.hand_socket_R
        local_mat = Matrix.Translation(Vector(rec["offset"])) @ Euler(rec["rot_euler"], "XYZ").to_matrix().to_4x4()
        orig_scale = prop_obj.scale.copy()
        saved_frame = scene.frame_current

        try:
            for f in range(rec["f_start"], rec["f_end"] + 1):
                scene.frame_set(f)
                bpy.context.view_layer.update()
                target_world = socket.matrix_world @ local_mat
                loc, rot_q, _ = target_world.decompose()
                if prop_obj.parent is not None:
                    p_inv = prop_obj.parent.matrix_world.inverted()
                    local_target = p_inv @ Matrix.LocRotScale(loc, rot_q, orig_scale)
                    loc, rot_q, _ = local_target.decompose()

                prop_obj.location = loc
                prop_obj.keyframe_insert("location", frame=f)
                if prop_obj.rotation_mode == "QUATERNION":
                    prop_obj.rotation_quaternion = rot_q
                    prop_obj.keyframe_insert("rotation_quaternion", frame=f)
                else:
                    prop_obj.rotation_euler = rot_q.to_euler(prop_obj.rotation_mode)
                    prop_obj.keyframe_insert("rotation_euler", frame=f)
        finally:
            scene.frame_set(saved_frame)
            bpy.context.view_layer.update()

    def attach_prop(
        self,
        prop_obj,
        side: str = "R",
        f_start: int = 1,
        f_end: int = 100,
        offset=(0.0, 0.0, 0.0),
        rot_euler=(0.0, 0.0, 0.0),
    ):
        """World-pin `prop_obj` to `hand_socket_R` or `hand_socket_L` over `[f_start, f_end]` (`0.000 m` error)."""
        side_u = side.upper()
        if side_u not in {"L", "R"}:
            raise ValueError(f"side must be 'L' or 'R', got {side!r}")
        f0, f1 = int(f_start), int(f_end)
        if f1 < f0:
            raise ValueError(f"f_end ({f1}) must be >= f_start ({f0})")

        rec = {
            "prop_obj": prop_obj,
            "side": side_u,
            "f_start": f0,
            "f_end": f1,
            "offset": tuple(float(x) for x in offset),
            "rot_euler": tuple(float(x) for x in rot_euler),
        }
        # Replace any overlapping record on the same prop/range and bake immediately
        self._prop_attachments = [
            r
            for r in self._prop_attachments
            if not (r["prop_obj"] == prop_obj and r["f_start"] == f0 and r["f_end"] == f1)
        ]
        self._prop_attachments.append(rec)
        self._bake_single_attachment(rec)
        return self.hand_socket_L if side_u == "L" else self.hand_socket_R

    def update_ink(self, camera, frame: int | None = None, pixels: float = 4.2):
        """Update screen-space `#141016` outline widths and sync directional comic light vector."""
        if camera is None or camera.type != "CAMERA":
            raise ValueError("Provide a valid Blender CAMERA object to update_ink().")
        f = int(frame) if frame is not None else None

        # Sync MascotLightVec on cel materials from `self.light_empty`
        ldir = (self.light_empty.matrix_world.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
        for mat in self._cel_materials:
            if not mat.use_nodes:
                continue
            lnode = mat.node_tree.nodes.get("MascotLightVec")
            if lnode is not None:
                lnode.inputs["X"].default_value = ldir.x
                lnode.inputs["Y"].default_value = ldir.y
                lnode.inputs["Z"].default_value = ldir.z

        cam_inv = camera.matrix_world.inverted()
        lens_mm = float(camera.data.lens)

        for ink_obj, disp_mod, k_scale in self._mesh_ink_mods:
            if ink_obj.hide_render:
                continue
            depth = -(cam_inv @ ink_obj.matrix_world.translation).z
            if depth <= 0.02:
                continue
            raw_w = _ink_thickness_m(depth, lens_mm, pixels, 0.0062) * k_scale
            max_w = 0.0065 if k_scale < 0.75 else 0.0155
            disp_mod.strength = -min(max_w, raw_w)
            if f is not None:
                disp_mod.keyframe_insert("strength", frame=f)

        for curve_obj, node_mod, sock_id, k_scale in self._curve_ink_mods:
            if curve_obj.hide_render:
                continue
            pts = curve_obj.data.splines[0].bezier_points
            mid_world = curve_obj.matrix_world @ pts[len(pts) // 2].co
            depth = -(cam_inv @ mid_world).z
            if depth <= 0.02:
                continue
            raw_w = _ink_thickness_m(depth, lens_mm, pixels, 0.0058) * k_scale
            node_mod[sock_id] = min(0.0135, raw_w)
            if f is not None:
                node_mod.keyframe_insert(f'["{sock_id}"]', frame=f)

    def head_bbox_ratio(self) -> dict[str, float]:
        """Measure world-scaled marshmallow head mesh bounds (excluding beanie) and assert `1.00 <= ratio <= 1.05`."""
        verts = self._head_mesh.data.vertices
        # Include net world scale of head control so squashed-head bugs are caught immediately!
        _, _, net_scale = self._head_mesh.matrix_world.decompose()
        xs = [v.co.x * abs(net_scale.x) for v in verts]
        ys = [v.co.y * abs(net_scale.y) for v in verts]
        zs = [v.co.z * abs(net_scale.z) for v in verts]
        width_m = max(xs) - min(xs)
        depth_m = max(ys) - min(ys)
        height_m = max(zs) - min(zs)
        ratio = height_m / width_m
        assert 1.00 <= ratio <= 1.05, (
            f"Mascot head height/width ratio {ratio:.4f} outside [1.00, 1.05] "
            f"(w={width_m:.4f}, d={depth_m:.4f}, h={height_m:.4f})"
        )
        return {
            "width_m": round(width_m, 6),
            "depth_m": round(depth_m, 6),
            "height_m": round(height_m, 6),
            "ratio": round(ratio, 6),
        }

    def finish_bake(self):
        """Re-verify attached props, set `CONSTANT` on visibility swaps, and `LINEAR` on baked motion."""
        for rec in self._prop_attachments:
            self._bake_single_attachment(rec)

        datablocks = set()
        for obj in self._objects:
            datablocks.add(obj)
            if getattr(obj, "data", None) is not None:
                datablocks.add(obj.data)
        for rec in self._prop_attachments:
            datablocks.add(rec["prop_obj"])

        for db in datablocks:
            anim = getattr(db, "animation_data", None)
            if not anim or not anim.action:
                continue
            for fc in anim.action.fcurves:
                is_vis = fc.data_path in {"hide_render", "hide_viewport"}
                interp = "CONSTANT" if is_vis else "LINEAR"
                for kp in fc.keyframe_points:
                    kp.interpolation = interp


def _unique_rig_name(requested: str) -> str:
    if bpy.data.objects.get(requested) is None:
        return requested
    idx = 2
    while bpy.data.objects.get(f"{requested}_{idx}") is not None:
        idx += 1
    return f"{requested}_{idx}"


def load_mascot(
    collection,
    name: str = "Mascot",
    bottom_style: str = "pajamas",
    arm_style: str = "hoodie",
) -> MascotRig:
    """Append `"MascotHero"` from `mascot_master.blend` (or build on the fly) into `collection`."""
    if bpy is None:
        raise RuntimeError("load_mascot() requires Blender 4.2 Python (`bpy`).")
    if bottom_style not in {"pajamas", "shorts"}:
        raise ValueError(f"bottom_style must be 'pajamas' or 'shorts', got {bottom_style!r}")
    if arm_style not in {"hoodie", "stick"}:
        raise ValueError(f"arm_style must be 'hoodie' or 'stick', got {arm_style!r}")

    rig_name = _unique_rig_name(name)

    if MASTER_BLEND_PATH.is_file():
        with bpy.data.libraries.load(str(MASTER_BLEND_PATH), link=False) as (data_from, data_to):
            if MASTER_COLLECTION_NAME not in data_from.collections:
                raise RuntimeError(
                    f"Collection {MASTER_COLLECTION_NAME!r} not found in {MASTER_BLEND_PATH}"
                )
            data_to.collections = [MASTER_COLLECTION_NAME]

        appended_col = data_to.collections[0]
        rig_objs = list(appended_col.all_objects)
        for obj in rig_objs:
            if obj.name not in collection.objects:
                collection.objects.link(obj)
            if obj.name in appended_col.objects:
                appended_col.objects.unlink(obj)
            # Rename with instance prefix for clean multi-character support
            if obj.get("mascot_tag") == "root":
                obj.name = rig_name
            elif " | " in obj.name:
                suffix = obj.name.split(" | ", 1)[1]
                # Strip any Blender `.001` suffix only if clean
                obj.name = f"{rig_name} | {suffix}"
            if getattr(obj, "data", None) is not None and hasattr(obj.data, "materials"):
                for mat in obj.data.materials:
                    if mat is not None and mat.use_nodes:
                        for nd in mat.node_tree.nodes:
                            if nd.type == "TEX_IMAGE" and nd.image and nd.image.source == "FILE" and not nd.image.packed_file:
                                nd.image.pack()
        bpy.data.collections.remove(appended_col)
    else:
        from assets.mascot import build_mascot_asset

        before = set(collection.objects)
        build_mascot_asset.build_mascot_in_collection(collection, name=rig_name)
        rig_objs = [o for o in collection.objects if o not in before]

    rig = MascotRig(rig_objs, name=rig_name, bottom_style=bottom_style, arm_style=arm_style)
    rig.pose(None, loc=(0.0, 0.0, 0.0), expr="idle_cute")
    bpy.context.view_layer.update()
    return rig
