"""Unit and headless-Blender integration suite for `assets/mascot/`.

Invocation modes:
  1. CPU Python (when `BLENDER_EXE` is unset):
       python -m unittest tests.test_mascot -v
     Runs pure-Python contract/math/18-animation tests and cleanly skips `bpy`
     tests without touching local Blender or `.blender_gpu.lock`.
  2. Modal Python (`BLENDER_EXE=/opt/blender42/blender` set in container):
       python3 -m unittest tests.test_mascot -v
     Runs pure-Python tests AND spawns headless Blender `--python-exit-code 1`
     executing the full `bpy` verification suite.
  3. Direct Modal Blender runner:
       modal run scripts/modal_blender.py --mode run --project assets/mascot \
           --script tests/test_mascot.py --runner blender
"""
from __future__ import annotations

import inspect
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

try:
    import bpy
    from mathutils import Vector
except ModuleNotFoundError as exc:
    if exc.name not in {"bpy", "mathutils"}:
        raise
    bpy = None
    Vector = None

from assets.mascot import anim_library, mascot_api


EXPECTED_EXPRESSIONS = (
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
EXPECTED_VISEMES = (
    "vis_closed",
    "vis_AA",
    "vis_EE",
    "vis_OH",
    "vis_OO",
    "vis_FV",
)
EXPECTED_HAND_POSES = (
    "relaxed_curl",
    "open_stop",
    "power_claw",
    "fist",
    "point",
    "thumbs_up_ok",
    "behind_head",
)


def _write_test_speech_wav(path: Path, duration_s: float = 1.6, sample_rate: int = 16000) -> Path:
    """Synthesize a clean mono 16-bit PCM WAV with speech bursts and silence gaps."""
    n_samples = int(duration_s * sample_rate)
    frames = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        # Silence [0.0..0.25], vowel burst [0.25..0.65], fricative/high ZCR [0.70..1.05], silence [1.05..1.60]
        if 0.25 <= t <= 0.65:
            env = math.sin(math.pi * (t - 0.25) / 0.40)
            val = 0.72 * env * (0.7 * math.sin(math.tau * 210.0 * t) + 0.3 * math.sin(math.tau * 630.0 * t))
        elif 0.70 <= t <= 1.05:
            env = math.sin(math.pi * (t - 0.70) / 0.35)
            val = 0.55 * env * math.sin(math.tau * 2400.0 * t) * math.cos(math.tau * 370.0 * t)
        else:
            val = 0.0
        pcm = max(-32767, min(32767, int(val * 32767)))
        frames.extend(struct.pack("<h", pcm))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))
    return path


class _MockProp:
    def __init__(self, loc=(0.22, -0.30, 0.12), rot=(0.0, 0.0, 0.0)):
        self.location = tuple(loc)
        self.rotation_euler = tuple(rot)
        self.keys: dict[tuple[str, int], tuple[float, ...]] = {}
        self.animation_data = None

    def keyframe_insert(self, data_path: str, frame: int) -> None:
        val = self.location if data_path == "location" else self.rotation_euler
        self.keys[(data_path, int(frame))] = tuple(val)


class _MockMascotRig:
    """Pure-Python recorder verifying `anim_library` poses and world-space foot pinning."""

    def __init__(self):
        self.name = "MockMascot"
        self.poses: dict[int, dict] = {}
        self.lipsync_calls: list[tuple] = []
        self.attach_calls: list[tuple] = []

    def pose(
        self,
        frame,
        loc=(0, 0, 0),
        yaw=0.0,
        body_tilt=0.0,
        body_roll=0.0,
        bounce=0.0,
        squash=1.0,
        head_yaw=0.0,
        head_pitch=0.0,
        head_roll=0.0,
        arm_L=None,
        arm_R=None,
        leg_L=None,
        leg_R=None,
        hand_L="relaxed_curl",
        hand_R="relaxed_curl",
        hand_rot_L=None,
        hand_rot_R=None,
        foot_rot_L=None,
        foot_rot_R=None,
        string_sway=None,
        expr=None,
    ):
        assert hand_L in EXPECTED_HAND_POSES, f"Invalid hand_L: {hand_L}"
        assert hand_R in EXPECTED_HAND_POSES, f"Invalid hand_R: {hand_R}"
        if expr is not None:
            assert expr in (*EXPECTED_EXPRESSIONS, *EXPECTED_VISEMES), f"Invalid expr: {expr}"
        rec = dict(
            loc=tuple(loc),
            yaw=float(yaw),
            body_tilt=float(body_tilt),
            body_roll=float(body_roll),
            bounce=float(bounce),
            squash=float(squash),
            head_yaw=float(head_yaw),
            head_pitch=float(head_pitch),
            head_roll=float(head_roll),
            arm_L=arm_L,
            arm_R=arm_R,
            leg_L=leg_L,
            leg_R=leg_R,
            hand_L=hand_L,
            hand_R=hand_R,
            string_sway=string_sway,
            expr=expr,
        )
        if frame is not None:
            self.poses[int(frame)] = rec

    def set_expression(self, expr_name, frame=None):
        assert expr_name in (*EXPECTED_EXPRESSIONS, *EXPECTED_VISEMES)

    def auto_lipsync(self, audio_path, start_frame, end_frame, base_expr="idle_cute", fps=30):
        self.lipsync_calls.append((str(audio_path), int(start_frame), int(end_frame), base_expr, fps))

    def attach_prop(self, prop_obj, side="R", f_start=1, f_end=100, offset=(0, 0, 0), rot_euler=(0, 0, 0)):
        self.attach_calls.append((prop_obj, side, int(f_start), int(f_end), tuple(offset), tuple(rot_euler)))


# ===========================================================================
# 1. Pure-Python Contract & 18-Animation Math Suite
# ===========================================================================
class TestAnimLibraryPurePython(unittest.TestCase):
    def test_all_18_animation_signatures_exist(self):
        self.assertEqual(len(anim_library.ANIMATION_NAMES), 18)
        for name in anim_library.ANIMATION_NAMES:
            fn = getattr(anim_library, name, None)
            self.assertTrue(callable(fn), f"Missing animation function: {name}")
            params = list(inspect.signature(fn).parameters)
            self.assertGreaterEqual(len(params), 3)
            self.assertEqual(params[:3], ["hero", "f0", "f1"])

    def test_ease5_and_world_foot_pinning_identity(self):
        self.assertEqual(anim_library.ease5(0.0), 0.0)
        self.assertEqual(anim_library.ease5(1.0), 1.0)
        self.assertAlmostEqual(anim_library.ease5(0.5), 0.5, places=9)

        world_foot = (-0.35, 1.15, 0.0)
        for yaw in (-1.2, 0.0, 0.47, math.pi):
            root_xyz = (-0.20, 1.25, 0.0)
            local = anim_library.world_to_root_local(world_foot, root_xyz, yaw)
            reconstructed = anim_library.local_to_world_point(root_xyz, yaw, local)
            for a, b in zip(world_foot, reconstructed):
                self.assertAlmostEqual(a, b, places=9)

    def test_all_18_animations_execute_with_zero_stance_skating_in_pure_python(self):
        prop_a = _MockProp((0.22, -0.32, 0.12))
        prop_b = _MockProp((0.20, -0.26, 0.72))
        with tempfile.TemporaryDirectory() as tmp:
            wav = _write_test_speech_wav(Path(tmp) / "speech.wav", duration_s=1.0)
            cases = [
                ("idle_breathe", lambda h: anim_library.idle_breathe(h, 1, 45, loc=(0.2, -0.3, 0.0), yaw=0.25)),
                ("walk_to", lambda h: anim_library.walk_to(h, 1, 48, (0.0, 1.1), (0.3, -0.2), ground_z=0.0)),
                ("run_panic_to", lambda h: anim_library.run_panic_to(h, 1, 40, (-0.5, 0.8), (0.4, -0.4), ground_z=0.0)),
                ("sneak_to", lambda h: anim_library.sneak_to(h, 1, 52, (0.0, 0.9), (0.0, 0.0), ground_z=0.0)),
                ("stop_hold_up", lambda h: anim_library.stop_hold_up(h, 1, 45, loc=(0.0, 0.0, 0.0), yaw=0.1)),
                ("power_aura_stance", lambda h: anim_library.power_aura_stance(h, 1, 45, aura=True, loc=(0.0, 0.0, 0.0))),
                ("chill_chair_lean", lambda h: anim_library.chill_chair_lean(h, 1, 45, seat_z=0.42)),
                ("talk_explain_visemes", lambda h: anim_library.talk_explain(h, 1, 45, audio_path=None)),
                ("talk_explain_audio", lambda h: anim_library.talk_explain(h, 1, 30, audio_path=wav)),
                ("point_at_camera_wink", lambda h: anim_library.point_at_camera_wink(h, 1, 40)),
                ("shrug_idk", lambda h: anim_library.shrug_idk(h, 1, 40)),
                ("jump_parabolic", lambda h: anim_library.jump_parabolic(h, 1, 42, (0.0, 0.6, 0.0), (0.0, -0.2, 0.0), 0.55)),
                ("celebrate_hype", lambda h: anim_library.celebrate_hype(h, 1, 48)),
                ("facepalm_groan", lambda h: anim_library.facepalm_groan(h, 1, 42)),
                ("take_hit_recoil", lambda h: anim_library.take_hit_recoil(h, 1, 36, from_side="L")),
                ("phone_scroll_zombie", lambda h: anim_library.phone_scroll_zombie(h, 1, 40)),
                ("pickup_and_present", lambda h: anim_library.pickup_and_present(h, 1, 45, prop_a, side="R")),
                ("throw_prop_at", lambda h: anim_library.throw_prop_at(h, 1, 45, prop_b, (0.4, -1.8, 0.0), side="R")),
                ("dramatic_double_take", lambda h: anim_library.dramatic_double_take(h, 1, 45, (0.8, -1.6, 1.1))),
            ]

            for label, call in cases:
                with self.subTest(animation=label):
                    mock = _MockMascotRig()
                    info = call(mock)
                    self.assertIsInstance(info, dict)
                    f0, f1 = info["f0"], info["f1"]
                    self.assertEqual(sorted(mock.poses.keys()), list(range(f0, f1 + 1)))

                    # Verify 0.000 m world-space foot skating across all declared stance windows!
                    for leg_key, win_key in (("leg_L", "stance_windows_L"), ("leg_R", "stance_windows_R")):
                        for w0, w1 in info.get(win_key, []):
                            p0 = mock.poses[w0]
                            anchor_w = anim_library.local_to_world_point(p0["loc"], p0["yaw"], p0[leg_key][0])
                            for f in range(w0, w1 + 1):
                                pf = mock.poses[f]
                                cur_w = anim_library.local_to_world_point(pf["loc"], pf["yaw"], pf[leg_key][0])
                                drift = math.sqrt(sum((a - b) ** 2 for a, b in zip(anchor_w, cur_w)))
                                self.assertLess(drift, 1e-6, f"{label} {leg_key} skated {drift:.6f} m on [{w0}, {w1}] at f={f}")

            # Check single-frame edge case (`f0 == f1`) works cleanly for still pose sheets
            still_mock = _MockMascotRig()
            anim_library.stop_hold_up(still_mock, 10, 10)
            self.assertEqual(still_mock.poses[10]["hand_L"], "open_stop")
            self.assertEqual(still_mock.poses[10]["expr"], "curious_o")


# ===========================================================================
# 2. Headless Blender (`bpy`) Integration Suite
# ===========================================================================
def _count_hero_triangles(scene, hero) -> int:
    deps = bpy.context.evaluated_depsgraph_get()
    root = hero.root
    owned = {root, *root.children_recursive}
    total = 0
    for obj in owned:
        if obj.hide_render or obj.type not in {"MESH", "CURVE", "SURFACE", "FONT"}:
            continue
        eval_obj = obj.evaluated_get(deps)
        mesh = eval_obj.to_mesh()
        if mesh is not None:
            try:
                mesh.calc_loop_triangles()
                total += len(mesh.loop_triangles)
            finally:
                eval_obj.to_mesh_clear()
    return total


def _find_foot_objects(hero) -> tuple[object, object]:
    """Locate left and right sneaker/foot pivot objects on `MascotRig`."""
    for attr_l, attr_r in (("_foot_L", "_foot_R"), ("foot_L", "foot_R"), ("sneaker_L", "sneaker_R"), ("ankle_L", "ankle_R")):
        if hasattr(hero, attr_l) and hasattr(hero, attr_r):
            return getattr(hero, attr_l), getattr(hero, attr_r)
    for seq_attr in ("feet", "sneakers"):
        seq = getattr(hero, seq_attr, None)
        if seq and len(seq) == 2:
            return seq[0], seq[1]

    by_tag = {o.get("mascot_tag"): o for o in hero.root.children_recursive if o.get("mascot_tag")}
    if "foot_L" in by_tag and "foot_R" in by_tag:
        return by_tag["foot_L"], by_tag["foot_R"]

    cands_l, cands_r = [], []
    for obj in hero.root.children_recursive:
        low = obj.name.lower()
        if "ink" in low or "outline" in low or "hull" in low:
            continue
        if any(tok in low for tok in ("sneaker", "shoe", "foot")):
            if low.endswith("_l") or low.endswith(" l") or "| l" in low or ".l" in low or "_l_" in low or "left" in low:
                cands_l.append(obj)
            elif low.endswith("_r") or low.endswith(" r") or "| r" in low or ".r" in low or "_r_" in low or "right" in low:
                cands_r.append(obj)
    if cands_l and cands_r:
        return cands_l[0], cands_r[0]
    raise AssertionError(f"Could not locate L/R foot or sneaker objects under {hero.root.name}")


def _min_sneaker_world_z(scene, hero) -> float:
    """World-space minimum Z of the mascot's visible non-ink sneaker/foot meshes."""
    deps = bpy.context.evaluated_depsgraph_get()
    min_z = float("inf")
    for obj in hero.root.children_recursive:
        low = obj.name.lower()
        if obj.hide_render or obj.type != "MESH":
            continue
        if "ink" in low or "outline" in low or "hull" in low or obj.get("ricks_role") == "ink":
            continue
        if any(tok in low for tok in ("sneaker", "shoe", "foot", "sole")):
            eval_obj = obj.evaluated_get(deps)
            mesh = eval_obj.to_mesh()
            try:
                mw = eval_obj.matrix_world
                for v in mesh.vertices:
                    wz = (mw @ v.co).z
                    if wz < min_z:
                        min_z = wz
            finally:
                eval_obj.to_mesh_clear()
    return min_z


def _active_expression_names(hero) -> list[str]:
    """Return currently visible expression/viseme names on `hero`."""
    mapping = getattr(hero, "expressions", None) or getattr(hero, "expression_objects", None) or getattr(hero, "decals", None)
    if isinstance(mapping, dict):
        return [name for name, obj in mapping.items() if not obj.hide_render]
    cur = getattr(hero, "current_expression", None)
    if isinstance(cur, str):
        return [cur]
    found = []
    for obj in hero.head.children_recursive:
        if not obj.hide_render:
            for name in (*EXPECTED_EXPRESSIONS, *EXPECTED_VISEMES):
                if name in obj.name:
                    found.append(name)
    return found


class TestMascotBlenderIntegration(unittest.TestCase):
    def test_mascot_blender_suite(self):
        if bpy is None:
            blender_exe = os.environ.get("BLENDER_EXE", "").strip()
            if not blender_exe or not Path(blender_exe).is_file():
                self.skipTest("BLENDER_EXE not set or unavailable; skipping headless Blender bpy suite.")
            proc = subprocess.run(
                [
                    blender_exe,
                    "-b",
                    "--factory-startup",
                    "--python-exit-code",
                    "1",
                    "--python",
                    str(Path(__file__).resolve()),
                    "--",
                    "--bpy-only",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=360,
            )
            if proc.returncode != 0 or "MASCOT_TESTS_OK" not in proc.stdout:
                self.fail(
                    f"Headless Blender suite failed (exit {proc.returncode}):\n"
                    f"STDOUT:\n{proc.stdout[-4000:]}\nSTDERR:\n{proc.stderr[-2000:]}"
                )
            return

        self._run_in_process_bpy_checks()

    def _run_in_process_bpy_checks(self):
        from assets.mascot import mascot_api

        # 1. Verify exported API constants
        self.assertEqual(tuple(mascot_api.EXPRESSIONS), EXPECTED_EXPRESSIONS)
        self.assertEqual(tuple(mascot_api.VISEMES), EXPECTED_VISEMES)
        self.assertEqual(tuple(mascot_api.HAND_POSES), EXPECTED_HAND_POSES)

        # 2. Verify `load_mascot()` default ("pajamas" + "hoodie") AND ("shorts" + "stick") + multi-instance
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        col = scene.collection

        hero = mascot_api.load_mascot(col, name="MascotDefault", bottom_style="pajamas", arm_style="hoodie")
        alt = mascot_api.load_mascot(col, name="MascotAlt", bottom_style="shorts", arm_style="stick")
        self.assertIsNotNone(hero.root)
        self.assertIsNotNone(hero.body)
        self.assertIsNotNone(hero.head)
        self.assertIsNotNone(hero.hand_socket_L)
        self.assertIsNotNone(hero.hand_socket_R)
        self.assertNotEqual(hero.root.name, alt.root.name)

        # 3. Head marshmallow aspect ratio (`1.00 <= head_h/head_w <= 1.05`)
        bbox = hero.head_bbox_ratio()
        self.assertIn("ratio", bbox)
        self.assertGreaterEqual(bbox["ratio"], 1.00, f"Head too squashed: {bbox}")
        self.assertLessEqual(bbox["ratio"], 1.05, f"Head too tall/narrow: {bbox}")

        # 4. Triangle budget `< 40,000` per hero
        hero.pose(1, loc=(0.0, 0.0, 0.0), yaw=0.0, expr="idle_cute")
        alt.pose(1, loc=(1.2, 0.0, 0.0), yaw=0.0, expr="curious_o")
        scene.frame_set(1)
        bpy.context.view_layer.update()

        tris_default = _count_hero_triangles(scene, hero)
        tris_alt = _count_hero_triangles(scene, alt)
        self.assertGreater(tris_default, 500)
        self.assertLess(tris_default, 40000, f"Default mascot exceeds 40k triangle budget: {tris_default}")
        self.assertLess(tris_alt, 40000, f"Shorts/stick mascot exceeds 40k triangle budget: {tris_alt}")

        # 5. Sneaker sole contact at `Z = 0.000 m`
        min_z = _min_sneaker_world_z(scene, hero)
        self.assertTrue(math.isfinite(min_z), "Failed to sample sneaker mesh vertices")
        self.assertAlmostEqual(min_z, 0.0, delta=0.006, msg=f"Sneaker sole min Z={min_z:.5f} m != 0.000 m")

        # 6. `auto_lipsync` on a generated temporary WAV
        with tempfile.TemporaryDirectory() as tmp:
            wav_path = _write_test_speech_wav(Path(tmp) / "test_vo.wav", duration_s=1.5)
            hero.auto_lipsync(wav_path, 1, 45, base_expr="idle_cute", fps=30)
            seen_exprs = set()
            for f in range(1, 46):
                scene.frame_set(f)
                bpy.context.view_layer.update()
                seen_exprs.update(_active_expression_names(hero))
            self.assertTrue(
                any(v in seen_exprs for v in EXPECTED_VISEMES if v != "vis_closed"),
                f"Expected active speech visemes during audio burst, saw: {seen_exprs}",
            )
            # Silence tail should return to `idle_cute` (or `vis_closed`/`idle_cute`)
            scene.frame_set(45)
            bpy.context.view_layer.update()
            tail_exprs = _active_expression_names(hero)
            self.assertIn("idle_cute", tail_exprs, f"Expected base_expr at silent tail f=45, got {tail_exprs}")

        # 7. `attach_prop` `0.000 m` grip error (`< 1e-4 m`) across dynamic arm sweep
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(0.0, 0.0, 0.0))
        test_prop = bpy.context.object
        test_prop.name = "TestGripOrb"
        for f in range(1, 21):
            u = anim_library.ease5((f - 1) / 19.0)
            hero.pose(
                f,
                loc=(0.1 * u, -0.05 * u, 0.0),
                yaw=0.25 * u,
                arm_R=((0.22 + 0.06 * u, -0.18 - 0.14 * u, 0.10 + 0.22 * u), (0.26, -0.04, 0.08)),
                hand_R="relaxed_curl",
            )
        hero.attach_prop(test_prop, side="R", f_start=1, f_end=20, offset=(0.0, 0.0, 0.0), rot_euler=(0.0, 0.0, 0.0))
        max_grip_err = 0.0
        for f in range(1, 21):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            err = (test_prop.matrix_world.translation - hero.hand_socket_R.matrix_world.translation).length
            max_grip_err = max(max_grip_err, err)
        self.assertLess(max_grip_err, 1e-4, f"attach_prop grip error {max_grip_err:.6f} m >= 1e-4 m")

        # 8. Execute ALL 18 `anim_library` functions in Blender verifying zero errors & planted stance feet!
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        col = scene.collection
        bpy.ops.object.camera_add(location=(0.0, -2.8, 1.12))
        cam = scene.camera = bpy.context.object
        cam.data.lens = 26.0

        hero = mascot_api.load_mascot(col, name="AnimHero", bottom_style="pajamas", arm_style="hoodie")
        foot_obj_L, foot_obj_R = _find_foot_objects(hero)

        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.06, location=(0.22, -0.32, 0.12))
        pickup_prop = bpy.context.object
        pickup_prop.name = "PickupGem"

        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.055, location=(0.20, -0.22, 0.72))
        throw_prop = bpy.context.object
        throw_prop.name = "ThrowBall"
        throw_target = (0.35, -1.65, 0.055)

        suite_calls = [
            ("idle_breathe", lambda f0, f1: anim_library.idle_breathe(hero, f0, f1)),
            ("walk_to", lambda f0, f1: anim_library.walk_to(hero, f0, f1, (0.0, 0.8), (0.0, 0.0))),
            ("run_panic_to", lambda f0, f1: anim_library.run_panic_to(hero, f0, f1, (0.0, 0.0), (0.3, -0.7))),
            ("sneak_to", lambda f0, f1: anim_library.sneak_to(hero, f0, f1, (0.3, -0.7), (0.0, 0.0))),
            ("stop_hold_up", lambda f0, f1: anim_library.stop_hold_up(hero, f0, f1)),
            ("power_aura_stance", lambda f0, f1: anim_library.power_aura_stance(hero, f0, f1, aura=True, collection=col)),
            ("chill_chair_lean", lambda f0, f1: anim_library.chill_chair_lean(hero, f0, f1, seat_z=0.42, build_chair=True, collection=col)),
            ("talk_explain", lambda f0, f1: anim_library.talk_explain(hero, f0, f1, audio_path=None)),
            ("point_at_camera_wink", lambda f0, f1: anim_library.point_at_camera_wink(hero, f0, f1, camera=cam)),
            ("shrug_idk", lambda f0, f1: anim_library.shrug_idk(hero, f0, f1)),
            ("jump_parabolic", lambda f0, f1: anim_library.jump_parabolic(hero, f0, f1, (0.0, 0.0, 0.0), (0.0, -0.5, 0.0), 0.50)),
            ("celebrate_hype", lambda f0, f1: anim_library.celebrate_hype(hero, f0, f1)),
            ("facepalm_groan", lambda f0, f1: anim_library.facepalm_groan(hero, f0, f1)),
            ("take_hit_recoil", lambda f0, f1: anim_library.take_hit_recoil(hero, f0, f1, from_side="L")),
            ("phone_scroll_zombie", lambda f0, f1: anim_library.phone_scroll_zombie(hero, f0, f1, collection=col)),
            ("pickup_and_present", lambda f0, f1: anim_library.pickup_and_present(hero, f0, f1, pickup_prop, side="R")),
            ("throw_prop_at", lambda f0, f1: anim_library.throw_prop_at(hero, f0, f1, throw_prop, throw_target, side="R")),
            ("dramatic_double_take", lambda f0, f1: anim_library.dramatic_double_take(hero, f0, f1, (0.75, -1.6, 1.05))),
        ]
        self.assertEqual(len(suite_calls), 18)

        max_stance_drift = 0.0
        cur_f = 1
        span_each = 24
        infos = {}
        for anim_name, fn in suite_calls:
            f0, f1 = cur_f, cur_f + span_each - 1
            cur_f = f1 + 2
            info = fn(f0, f1)
            infos[anim_name] = info
            for f in range(f0, f1 + 1):
                scene.frame_set(f)
                bpy.context.view_layer.update()
                hero.update_ink(cam, frame=f)

            # Check world-space planted feet during every stance window!
            for foot_obj, win_key in ((foot_obj_L, "stance_windows_L"), (foot_obj_R, "stance_windows_R")):
                for w0, w1 in info.get(win_key, []):
                    scene.frame_set(w0)
                    bpy.context.view_layer.update()
                    p0 = foot_obj.matrix_world.translation.copy()
                    for f in range(w0, w1 + 1):
                        scene.frame_set(f)
                        bpy.context.view_layer.update()
                        pf = foot_obj.matrix_world.translation
                        drift = (pf - p0).length
                        max_stance_drift = max(max_stance_drift, drift)
                        self.assertLess(
                            drift,
                            1e-3,
                            f"{anim_name} foot {foot_obj.name} skated {drift:.5f} m in stance [{w0}, {w1}] at f={f}",
                        )

        hero.finish_bake()

        # Verify visibility windowing on aura, studio chair, and phone props
        for key, obj_list_key in (
            ("power_aura_stance", "aura_objects"),
            ("chill_chair_lean", "chair_objects"),
            ("phone_scroll_zombie", "phone_objects"),
        ):
            inf = infos[key]
            objs = inf[obj_list_key]
            self.assertTrue(len(objs) > 0, f"{key} did not build expected 3D helper objects")
            scene.frame_set(inf["f0"] - 1)
            bpy.context.view_layer.update()
            self.assertTrue(all(o.hide_render for o in objs), f"{key} leaked before f0")
            scene.frame_set((inf["f0"] + inf["f1"]) // 2)
            bpy.context.view_layer.update()
            self.assertTrue(all(not o.hide_render for o in objs), f"{key} hidden inside [f0, f1]")
            scene.frame_set(inf["f1"] + 1)
            bpy.context.view_layer.update()
            self.assertTrue(all(o.hide_render for o in objs), f"{key} leaked after f1")

        # Verify `pickup_and_present` grip at end of beat and `throw_prop_at` landing on `throw_target`
        p_inf = infos["pickup_and_present"]
        scene.frame_set(p_inf["f1"])
        bpy.context.view_layer.update()
        self.assertLess(
            (pickup_prop.matrix_world.translation - hero.hand_socket_R.matrix_world.translation).length,
            1e-4,
        )

        t_inf = infos["throw_prop_at"]
        scene.frame_set(t_inf["f1"])
        bpy.context.view_layer.update()
        self.assertLess(
            (throw_prop.matrix_world.translation - Vector(throw_target)).length,
            1e-3,
        )

        # 9. Optional `starter_scene_template.py` smoke check when present
        starter_path = ROOT / "assets/mascot/starter_scene_template.py"
        starter_checked = False
        if starter_path.is_file():
            import importlib.util

            spec = importlib.util.spec_from_file_location("mascot_starter_scene_template", starter_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            build_fn = getattr(mod, "build_scene", None) or getattr(mod, "build", None)
            if callable(build_fn):
                sig = inspect.signature(build_fn)
                if len(sig.parameters) == 0:
                    built_res = build_fn()
                else:
                    built_res = build_fn(bpy.context.scene)
                sc = built_res[0] if isinstance(built_res, tuple) else (built_res if built_res is not None else bpy.context.scene)
                self.assertEqual((sc.render.resolution_x, sc.render.resolution_y), (1080, 1920))
                self.assertEqual(sc.render.fps, 30)
                self.assertEqual(sc.render.engine, "BLENDER_EEVEE_NEXT")
                starter_checked = True

        report = {
            "head_bbox": bbox,
            "triangles_default": tris_default,
            "triangles_shorts_stick": tris_alt,
            "sneaker_min_z_m": round(min_z, 6),
            "max_grip_error_m": round(max_grip_err, 7),
            "max_stance_drift_m": round(max_stance_drift, 7),
            "animations_verified": len(suite_calls),
            "starter_template_checked": starter_checked,
        }
        print("MASCOT_TEST_REPORT " + json.dumps(report))
        print("MASCOT_TESTS_OK")


def _main():
    tail = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    if "--bpy-only" in tail:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestMascotBlenderIntegration)
    else:
        suite = unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromTestCase(TestAnimLibraryPurePython),
            unittest.defaultTestLoader.loadTestsFromTestCase(TestMascotBlenderIntegration),
        ])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    _main()
