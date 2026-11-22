"""Pure-Python unit tests for V7 kit upgrades, drawn-look head ratios, beat_drift, and templates.

Runs in ordinary system Python with zero Blender dependency:
  python -m unittest tests.test_ricks_kit_upgrades -v
"""
from __future__ import annotations

import importlib.util
import inspect
import math
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ricks_camera as rc  # noqa: E402
import ricks_drawn_look as drawn  # noqa: E402
import ricks_v2_kit as kit  # noqa: E402


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mock_ellipsoid_obj(rx: float, ry: float, rz: float, scale=(1.0, 1.0, 1.0)):
    verts = []
    for sx in (-1.0, 1.0):
        verts.append(SimpleNamespace(co=(sx * rx, 0.0, 0.0)))
    for sy in (-1.0, 1.0):
        verts.append(SimpleNamespace(co=(0.0, sy * ry, 0.0)))
    for sz in (-1.0, 1.0):
        verts.append(SimpleNamespace(co=(0.0, 0.0, sz * rz)))
    return SimpleNamespace(
        name="Mock | ellipsoid head",
        type="MESH",
        scale=scale,
        parent=None,
        data=SimpleNamespace(vertices=verts),
    )


class TestKitConstantsAndExports(unittest.TestCase):
    def test_head_and_paper_white_constants(self):
        self.assertEqual(kit.ROUND_HEAD, (0.235, 0.205, 0.235))
        self.assertAlmostEqual(kit.ROUND_HEAD[2] / kit.ROUND_HEAD[0], 1.0, places=6)
        self.assertEqual(kit.UPRIGHT_HEAD, (0.230, 0.205, 0.238))
        upright_ratio = kit.UPRIGHT_HEAD[2] / kit.UPRIGHT_HEAD[0]
        self.assertGreaterEqual(upright_ratio, 1.03)
        self.assertLessEqual(upright_ratio, 1.04)
        self.assertEqual(kit.PAPER_WHITE_FACE, "#FAF9F6")
        self.assertEqual(kit.PAPER_WHITE_SHADOW, "#EAE8E1")

    def test_v7_api_exports_and_backward_compat_signatures(self):
        expected_callables = (
            "make_bright_paper_face_material",
            "normalize_head_proportions",
            "measure_head_ratio",
            "render_pixel_locked_expression_pair",
            "verify_upper_face_lock",
            "setup_chiaroscuro_lighting",
            "make_subtle_light_cone",
            "make_plank_wood_material",
            "build_beveled_plank_floor",
            "make_brushed_metal_material",
            "make_editorial_brick_material",
            "make_tile_material",
            "make_glossy_fluid_material",
            "build_lofted_tube",
            "build_lathe_prop",
            "setup_diorama_camera_and_compositor",
        )
        for attr in expected_callables:
            self.assertTrue(callable(getattr(kit, attr, None)), f"Missing callable kit.{attr}")

        for fn in (kit.build_ricks_character, kit.RicksCharacter.__init__):
            sig = inspect.signature(fn)
            self.assertIn("head_radii", sig.parameters)
            self.assertIsNone(sig.parameters["head_radii"].default)

    def test_measure_head_ratio_pure_python_mocks(self):
        r_round = kit.measure_head_ratio(_mock_ellipsoid_obj(*kit.ROUND_HEAD))
        self.assertAlmostEqual(r_round["ratio"], 1.0, places=6)
        self.assertFalse(r_round["is_squashed"])

        r_up = kit.measure_head_ratio(_mock_ellipsoid_obj(*kit.UPRIGHT_HEAD))
        self.assertAlmostEqual(r_up["ratio"], kit.UPRIGHT_HEAD[2] / kit.UPRIGHT_HEAD[0], places=5)
        self.assertFalse(r_up["is_squashed"])

        r_squash = kit.measure_head_ratio(_mock_ellipsoid_obj(*kit.HEAD))
        self.assertLess(r_squash["ratio"], 0.98)
        self.assertTrue(r_squash["is_squashed"])

        # MascotRig delegate compatibility
        fake_mascot = SimpleNamespace(head_bbox_ratio=lambda: {"ratio": 1.02, "width_m": 0.46, "height_m": 0.4692})
        r_mascot = kit.measure_head_ratio(fake_mascot)
        self.assertAlmostEqual(r_mascot["ratio"], 1.02)
        self.assertFalse(r_mascot["is_squashed"])


class TestPixelLockedSpeechPairs(unittest.TestCase):
    def test_render_and_verify_zero_upper_diff_across_moods(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for mood in ("neutral", "happy", "smug", "skeptical", "surprised", "worried"):
                with self.subTest(mood=mood):
                    pair = kit.render_pixel_locked_expression_pair(tmp_dir, f"hero_{mood}", mood=mood, size=256)
                    self.assertTrue(pair["closed"].is_file())
                    self.assertTrue(pair["talk"].is_file())
                    lock = kit.verify_upper_face_lock(pair["closed"], pair["talk"], split_y_frac=0.55)
                    self.assertTrue(lock["pass"], lock)
                    self.assertTrue(lock["locked"], lock)
                    self.assertEqual(lock["max_diff"], 0)
                    self.assertEqual(lock["nonzero_pixels"], 0)
                    self.assertGreater(lock["lower_changed_pixels"], 20)

    def test_verify_upper_face_lock_catches_single_pixel_eye_flutter(self):
        pair = kit.render_pixel_locked_expression_pair(None, "mem_neutral", mood="neutral", size=128)
        closed_arr = np.asarray(pair["closed_image"], dtype=np.uint8)
        tampered = np.asarray(pair["talk_image"], dtype=np.uint8).copy()
        tampered[20, 40, 0] = (int(tampered[20, 40, 0]) + 15) % 255  # 1 pixel flutter in upper face

        res = kit.verify_upper_face_lock(closed_arr, tampered, split_y_frac=0.55, max_abs_diff=0)
        self.assertFalse(res["pass"])
        self.assertGreater(res["max_diff"], 0)
        self.assertEqual(res["nonzero_pixels"], 1)

    def test_no_pil_numpy_fallback_writes_and_verifies_real_pngs(self):
        """Stock Blender 4.2 Python has numpy without PIL; fallback must produce valid 0-diff PNGs."""
        blocked = {k: None for k in list(sys.modules) if k == "PIL" or k.startswith("PIL.")}
        blocked["PIL"] = None
        blocked["PIL.Image"] = None
        blocked["PIL.ImageDraw"] = None
        blocked["PIL.ImageChops"] = None

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            with mock.patch.dict(sys.modules, blocked):
                for mood in ("neutral", "happy", "smug", "skeptical", "surprised", "worried"):
                    with self.subTest(mood=mood):
                        pair = kit.render_pixel_locked_expression_pair(
                            tmp_dir, f"nopil_{mood}", mood=mood, size=128
                        )
                        self.assertTrue(pair["closed"].is_file())
                        self.assertTrue(pair["talk"].is_file())
                        self.assertIsInstance(pair["closed_image"], np.ndarray)
                        self.assertEqual(pair["closed_image"].shape, (128, 128, 4))
                        # Verify PNG round-trip via pure-Python PNG reader (still with PIL blocked)
                        lock = kit.verify_upper_face_lock(pair["closed"], pair["talk"], split_y_frac=0.55)
                        self.assertTrue(lock["pass"], lock)
                        self.assertEqual(lock["max_diff"], 0)
                        self.assertEqual(lock["nonzero_pixels"], 0)
                        self.assertGreater(lock["lower_changed_pixels"], 10)
            # Confirm PNG written without PIL is 100% spec-compliant and readable by PIL too
            from PIL import Image
            with Image.open(tmp_dir / "nopil_neutral_closed.png") as im:
                self.assertEqual(im.size, (128, 128))
                self.assertEqual(im.mode, "RGBA")


class TestDrawnLookHeadWarpAndPresets(unittest.TestCase):
    def test_round_and_upright_ban_horizontal_oval_squash(self):
        rx, ry, rz = kit.ROUND_HEAD
        round_warp = drawn.head_warp("round")
        left = round_warp((-rx, 0.0, 0.0))
        right = round_warp((rx, 0.0, 0.0))
        top = round_warp((0.0, 0.0, rz))
        bot = round_warp((0.0, 0.0, -rz))
        hw_round = (top[2] - bot[2]) / (right[0] - left[0])
        self.assertAlmostEqual(hw_round, 1.0, places=6)

        upright_warp = drawn.head_warp("upright")
        u_left = upright_warp((-rx, 0.0, 0.0))
        u_right = upright_warp((rx, 0.0, 0.0))
        u_top = upright_warp((0.0, 0.0, rz))
        u_bot = upright_warp((0.0, 0.0, -rz))
        hw_upright = (u_top[2] - u_bot[2]) / (u_right[0] - u_left[0])
        self.assertAlmostEqual(hw_upright, 1.035, places=6)

    def test_legacy_lopsided_remains_unchanged_for_optin_smoke(self):
        rx, _, rz = kit.HEAD
        lop = drawn.head_warp("lopsided")
        left = lop((-rx, 0.0, 0.0))
        right = lop((rx, 0.0, 0.0))
        top = lop((0.0, 0.0, rz))
        bot = lop((0.0, 0.0, -rz))
        self.assertNotAlmostEqual(abs(left[0]), abs(right[0]), places=3)
        self.assertNotAlmostEqual(abs(top[2]), abs(bot[2]), places=3)

    def test_paper_white_preset_contract(self):
        self.assertIn("paper_white", drawn.DRAWN_PRESETS)
        pw = drawn.DRAWN_PRESETS["paper_white"]
        self.assertEqual(pw["face"], "#FAF9F6")
        self.assertEqual(pw["face_shadow"], "#EAE8E1")
        self.assertAlmostEqual(pw["face_shadow_amount"], 0.05)
        self.assertAlmostEqual(pw["brightness"], 1.26)
        sig = inspect.signature(drawn.apply_drawn_look)
        self.assertIn("preset", sig.parameters)
        self.assertIsNone(sig.parameters["preset"].default)


class TestCameraBeatDrift(unittest.TestCase):
    def test_beat_drift_produces_alive_2_to_6_px_per_frame_with_zero_freeze(self):
        span = rc.drift_span_for_px_speed(distance_m=2.7, frames=45, px_per_frame=3.5, lens=27.0)
        p0 = (-span * 0.5, -2.7, 1.10)
        p1 = (span * 0.5, -2.7, 1.10)
        a0 = (-span * 0.5, 0.0, 1.10)
        a1 = (span * 0.5, 0.0, 1.10)
        drift_pos = rc.beat_drift(p0, p1, 1, 46)
        drift_aim = rc.beat_drift(a0, a1, 1, 46)
        self.assertEqual(drift_pos(1), p0)
        self.assertEqual(drift_pos(46), p1)

        prog = rc.CameraProgram([rc.Shot(1, 46, pos=drift_pos, aim=drift_aim, lens=27.0)])
        speeds = [v for _, v in rc.screen_speed(prog)]
        self.assertEqual(len(speeds), 45)
        self.assertGreaterEqual(min(speeds), 2.0)
        self.assertLessEqual(max(speeds), 6.0)
        self.assertAlmostEqual(sum(speeds) / len(speeds), 3.5, delta=0.15)

    def test_beat_drift_edge_ease_never_stalls(self):
        drift_pos = rc.beat_drift((0.0, -2.5, 1.0), (0.36, -2.5, 1.0), 1, 61, min_speed_frac=0.7)
        drift_aim = rc.beat_drift((0.0, 0.0, 1.0), (0.36, 0.0, 1.0), 1, 61, min_speed_frac=0.7)
        prog = rc.CameraProgram([rc.Shot(1, 61, pos=drift_pos, aim=drift_aim, lens=27.0)])
        speeds = [v for _, v in rc.screen_speed(prog)]
        self.assertGreater(min(speeds), 1.5)
        self.assertLess(max(speeds), 8.0)

    def test_beat_drift_validation(self):
        with self.assertRaises(ValueError):
            rc.beat_drift((0, 0, 0), (1, 0, 0), 10, 10)
        with self.assertRaises(ValueError):
            rc.beat_drift((0, 0, 0), (1, 0, 0), 1, 20, min_speed_frac=0.0)


class TestTemplatesSyntaxAndCLI(unittest.TestCase):
    TEMPLATE_PATHS = (
        ROOT / "scripts/templates/ricks_short_template.py",
        ROOT / "scripts/templates/diorama_short_template.py",
        ROOT / "assets/mascot/starter_scene_template.py",
    )

    def test_all_upgraded_modules_compile_cleanly(self):
        targets = (
            ROOT / "scripts/ricks_v2_kit.py",
            ROOT / "scripts/ricks_drawn_look.py",
            ROOT / "scripts/ricks_camera.py",
            *self.TEMPLATE_PATHS,
        )
        for path in targets:
            with self.subTest(path=str(path)):
                py_compile.compile(str(path), doraise=True)

    def test_templates_cli_help_and_resolver_fallback(self):
        for path in self.TEMPLATE_PATHS:
            with self.subTest(template=path.name):
                proc = subprocess.run(
                    [sys.executable, str(path), "--help"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                self.assertEqual(proc.returncode, 0, f"--help failed for {path}: {proc.stderr}")

                mod = _load_module(f"tpl_{path.stem}", path)
                self.assertTrue(callable(mod.resolve_blender_exe))
                with mock.patch.dict(os.environ, {"BLENDER_EXE": "/custom/blender"}, clear=False):
                    self.assertEqual(mod.resolve_blender_exe(), "/custom/blender")
                with mock.patch.dict(os.environ, {"BLENDER_EXE": ""}, clear=False):
                    with mock.patch.object(Path, "is_file", return_value=False):
                        with mock.patch("shutil.which", side_effect=lambda n: f"/usr/bin/{n}" if n == "blender" else None):
                            self.assertEqual(mod.resolve_blender_exe(), "/usr/bin/blender")
                        with mock.patch("shutil.which", side_effect=lambda n: f"/win/{n}" if n == "blender-launcher" else None):
                            self.assertEqual(mod.resolve_blender_exe(), "/win/blender-launcher")

    def test_template_contract_signatures_and_diorama_drift(self):
        ricks_tpl = _load_module("tpl_ricks_contract", ROOT / "scripts/templates/ricks_short_template.py")
        sig = inspect.signature(ricks_tpl.build)
        self.assertEqual(list(sig.parameters), ["bpy", "kit", "look", "camera_mode"])
        self.assertEqual(sig.parameters["look"].default, "cel")
        self.assertEqual(sig.parameters["camera_mode"].default, "keyed")

        mascot_tpl = _load_module("tpl_mascot_contract", ROOT / "assets/mascot/starter_scene_template.py")
        self.assertEqual(len(inspect.signature(mascot_tpl.build_scene).parameters), 0)
        self.assertEqual(mascot_tpl.SIZE, (1080, 1920))
        self.assertEqual(mascot_tpl.FPS, 30)
        self.assertEqual(mascot_tpl.SAMPLES, 32)
        self.assertEqual(mascot_tpl.LENS_MM, 26.0)

        diorama_tpl = _load_module("tpl_diorama_contract", ROOT / "scripts/templates/diorama_short_template.py")
        self.assertEqual(diorama_tpl.SIZE, (1080, 1920))
        self.assertEqual(diorama_tpl.FPS, 30)
        self.assertEqual(diorama_tpl.LENS_MM, 27.0)
        prog = diorama_tpl.build_camera_program()
        speeds = [v for _, v in rc.screen_speed(prog)]
        self.assertGreaterEqual(min(speeds), 2.0)
        self.assertLessEqual(max(speeds), 6.5)


if __name__ == "__main__":
    unittest.main()
