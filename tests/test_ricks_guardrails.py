"""Pure-Python unit test suite for `scripts/ricks_guardrails.py`.

Runs cleanly on host Python with zero Blender (`bpy`) dependency:
    python -m unittest tests.test_ricks_guardrails -v
"""
from __future__ import annotations

import contextlib
import io
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ricks_guardrails as gr


def _make_mock_scene(
    *,
    engine: str = "BLENDER_EEVEE_NEXT",
    use_raytracing: bool = False,
    resolution_x: int = 1080,
    resolution_y: int = 1920,
    resolution_percentage: int = 100,
    fps: int = 30,
    fps_base: float = 1.0,
    use_dof: bool = False,
    has_camera: bool = True,
    visible_tris: int = 42000,
    objects: list | None = None,
    collection: Any | None = None,
):
    cam = None
    if has_camera:
        cam = SimpleNamespace(
            name="MainCamera",
            data=SimpleNamespace(dof=SimpleNamespace(use_dof=use_dof)),
        )
    col = collection or SimpleNamespace(
        name="Scene Collection",
        hide_viewport=False,
        hide_render=False,
        children=[],
    )
    scene = SimpleNamespace(
        name="TestScene",
        frame_current=1,
        frame_start=1,
        frame_end=60,
        render=SimpleNamespace(
            engine=engine,
            resolution_x=resolution_x,
            resolution_y=resolution_y,
            resolution_percentage=resolution_percentage,
            fps=fps,
            fps_base=fps_base,
        ),
        eevee=SimpleNamespace(use_raytracing=use_raytracing),
        camera=cam,
        collection=col,
        objects=list(objects or ()),
        _mock_visible_triangles=visible_tris,
    )
    scene.frame_set = lambda f: setattr(scene, "frame_current", int(f))
    return scene


class TestCheckHeadRatio(unittest.TestCase):
    def test_round_and_upright_heads_pass(self):
        # 1:1 round head
        res_round = gr.check_head_ratio(0.470, 0.470, obj_name="HeroHead")
        self.assertTrue(res_round["pass"])
        self.assertAlmostEqual(res_round["ratio"], 1.0)
        self.assertEqual(res_round["fix_hint"], "")

        # Official Mascot head (ratio ~1.018)
        res_mascot = gr.check_head_ratio(0.440, 0.448, obj_name="MascotHead")
        self.assertTrue(res_mascot["pass"])
        self.assertAlmostEqual(res_mascot["ratio"], 0.448 / 0.440)

        # Exact boundary values
        self.assertTrue(gr.check_head_ratio(1.0, 0.98)["pass"])
        self.assertTrue(gr.check_head_ratio(1.0, 1.12)["pass"])

    def test_squashed_horizontal_oval_fails_with_fix_hint(self):
        # Legacy squashed head: H/W = 0.876 or 0.94
        res = gr.check_head_ratio(0.480, 0.420, obj_name="SquashedHead")
        self.assertFalse(res["pass"])
        self.assertEqual(res["check"], "head_ratio")
        self.assertEqual(res["severity"], "error")
        self.assertIn("Squashed", res["detail"])
        self.assertIn("ROUND_HEAD", res["fix_hint"])

        res_legacy = gr.check_head_ratio(0.24, 0.2256, obj_name="LegacyHead")
        self.assertFalse(res_legacy["pass"])

    def test_over_elongated_head_fails_with_fix_hint(self):
        res = gr.check_head_ratio(0.400, 0.480, obj_name="TallHead")
        self.assertFalse(res["pass"])
        self.assertIn("Over-elongated", res["detail"])
        self.assertTrue(len(res["fix_hint"]) > 10)

    def test_non_positive_dimensions_fail_cleanly(self):
        res = gr.check_head_ratio(0.0, 0.44)
        self.assertFalse(res["pass"])
        self.assertTrue(res["fix_hint"])
        res_neg = gr.check_head_ratio(0.44, -0.1)
        self.assertFalse(res_neg["pass"])


class TestCheckFrustumPoints(unittest.TestCase):
    def test_points_inside_safe_margin_pass(self):
        pts = [(0.10, 0.10, 2.0), (0.90, 0.90, 2.5), (0.50, 0.50, 2.2)]
        res = gr.check_frustum_points(pts, margin=0.04, obj_name="Hero", frame=15)
        self.assertTrue(res["pass"])
        self.assertEqual(res["violations"], [])
        self.assertEqual(res["frame"], 15)

        # Exact margin boundary passes
        res_edge = gr.check_frustum_points([(0.04, 0.04, 1.0), (0.96, 0.96, 1.0)], margin=0.04)
        self.assertTrue(res_edge["pass"])

    def test_2d_points_supported(self):
        res = gr.check_frustum_points([(0.2, 0.2), (0.8, 0.8)], margin=0.04)
        self.assertTrue(res["pass"])

    def test_clipped_outside_frustum_fails(self):
        pts = [(-0.05, 0.50, 2.0), (0.50, 1.03, 2.0)]
        res = gr.check_frustum_points(pts, margin=0.04, obj_name="Actor", frame=24)
        self.assertFalse(res["pass"])
        self.assertIn("clipped_left", res["violations"])
        self.assertIn("clipped_top", res["violations"])
        self.assertIn("26-28 mm", res["fix_hint"])

    def test_edge_margin_bleed_fails(self):
        pts = [(0.02, 0.50, 2.0), (0.98, 0.01, 2.0)]
        res = gr.check_frustum_points(pts, margin=0.04, obj_name="Prop", frame=5)
        self.assertFalse(res["pass"])
        self.assertIn("margin_bleed_left", res["violations"])
        self.assertIn("margin_bleed_right", res["violations"])
        self.assertIn("margin_bleed_bottom", res["violations"])
        self.assertTrue(res["fix_hint"])

    def test_behind_camera_fails(self):
        pts = [(0.50, 0.50, -0.2), (0.50, 0.60, 1.0)]
        res = gr.check_frustum_points(pts, margin=0.04, obj_name="BehindHero", frame=9)
        self.assertFalse(res["pass"])
        self.assertIn("behind_camera", res["violations"])

    def test_empty_points_fail_cleanly(self):
        res = gr.check_frustum_points([], obj_name="EmptyMesh", frame=1)
        self.assertFalse(res["pass"])
        self.assertIn("empty_points", res["violations"])


class TestCheckLimbStretch(unittest.TestCase):
    def test_normal_and_bent_limbs_pass(self):
        # Bent limb (shorter than rest) MUST pass
        self.assertTrue(gr.check_limb_stretch(0.24, 0.36, max_ratio=1.25)["pass"])
        # Exact rest length passes
        self.assertTrue(gr.check_limb_stretch(0.36, 0.36, max_ratio=1.25)["pass"])
        # Exact boundary 1.25x passes
        self.assertTrue(gr.check_limb_stretch(0.45, 0.36, max_ratio=1.25)["pass"])

    def test_stretched_noodle_limb_fails_with_fix_hint(self):
        res = gr.check_limb_stretch(0.55, 0.36, max_ratio=1.25, obj_name="Arm_R", frame=42)
        self.assertFalse(res["pass"])
        self.assertEqual(res["check"], "limb_stretch")
        self.assertAlmostEqual(res["ratio"], 0.55 / 0.36)
        self.assertIn("Over-stretched", res["detail"])
        self.assertIn("0.450m", res["fix_hint"])

    def test_collapsed_and_invalid_lengths_fail(self):
        self.assertFalse(gr.check_limb_stretch(0.0, 0.36, obj_name="Arm_L")["pass"])
        self.assertFalse(gr.check_limb_stretch(0.30, 0.0, obj_name="Leg_L")["pass"])
        self.assertFalse(gr.check_limb_stretch(-0.10, 0.36, obj_name="Leg_R")["pass"])


class TestCheckFacingDot(unittest.TestCase):
    def test_facing_camera_and_three_quarter_pass(self):
        # Directly facing camera
        res_front = gr.check_facing_dot((0.0, -1.0), (0.0, -3.0), min_dot=0.15, obj_name="Hero", frame=1)
        self.assertTrue(res_front["pass"])
        self.assertAlmostEqual(res_front["dot"], 1.0)
        self.assertAlmostEqual(res_front["angle_deg"], 0.0, places=3)

        # 3/4 view (~45 deg -> dot ~0.707)
        res_34 = gr.check_facing_dot((0.707, -0.707), (0.0, -1.0), min_dot=0.15)
        self.assertTrue(res_34["pass"])

        # Exact min_dot boundary passes
        res_edge = gr.check_facing_dot((math.sqrt(1.0 - 0.15**2), -0.15), (0.0, -1.0), min_dot=0.15)
        self.assertTrue(res_edge["pass"])

    def test_turned_away_back_of_head_fails(self):
        # Back turned completely to camera (dot = -1.0)
        res = gr.check_facing_dot((0.0, 1.0), (0.0, -2.5), min_dot=0.15, obj_name="Guest", frame=18)
        self.assertFalse(res["pass"])
        self.assertAlmostEqual(res["dot"], -1.0)
        self.assertIn("turned away", res["detail"])
        self.assertIn("allow_back_view", res["fix_hint"])

        # Pure 90-degree side profile (dot = 0.0 < 0.15) fails
        res_profile = gr.check_facing_dot((1.0, 0.0), (0.0, -1.0), min_dot=0.15)
        self.assertFalse(res_profile["pass"])

    def test_zero_vector_fails_cleanly(self):
        res = gr.check_facing_dot((0.0, 0.0), (0.0, -1.0))
        self.assertFalse(res["pass"])
        self.assertTrue(res["fix_hint"])


class TestCheckUpperFacePixelLock(unittest.TestCase):
    def _make_grid(self, w: int, h: int, fill=(250, 249, 246, 255)):
        return [[fill for _ in range(w)] for _ in range(h)]

    def test_identical_upper_face_with_open_mouth_lower_face_passes(self):
        closed = self._make_grid(20, 20)
        open_mouth = self._make_grid(20, 20)
        # Modify ONLY lower face (y >= 11, since 20 * 0.55 = 11 -> upper rows 0..10)
        for y in range(12, 18):
            for x in range(6, 14):
                open_mouth[y][x] = (60, 15, 25, 255)

        res = gr.check_upper_face_pixel_lock(closed, open_mouth, split_y_frac=0.55, max_abs_diff=0)
        self.assertTrue(res["pass"])
        self.assertEqual(res["max_diff"], 0)
        self.assertEqual(res["changed_pixels"], 0)
        self.assertEqual(res["upper_rows"], 11)

    def test_upper_face_eye_flutter_fails_with_fix_hint(self):
        closed = self._make_grid(20, 20)
        open_mouth = self._make_grid(20, 20)
        # Shift 1 eye pixel in upper face (row 5 < 11)
        open_mouth[5][8] = (20, 16, 22, 255)

        res = gr.check_upper_face_pixel_lock(closed, open_mouth, split_y_frac=0.55, max_abs_diff=0)
        self.assertFalse(res["pass"])
        self.assertEqual(res["changed_pixels"], 1)
        self.assertGreater(res["max_diff"], 0)
        self.assertIn("eye-flutter", res["detail"])
        self.assertIn("render_pixel_locked_expression_pair", res["fix_hint"])

    def test_tolerance_and_pil_png_paths(self):
        try:
            from PIL import Image
        except ModuleNotFoundError:
            self.skipTest("Pillow not installed")

        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "closed.png"
            p2 = Path(tmp) / "open.png"
            im1 = Image.new("RGBA", (32, 32), (250, 249, 246, 255))
            im2 = Image.new("RGBA", (32, 32), (250, 249, 246, 255))
            # Change mouth pixel in lower half
            im2.putpixel((16, 24), (80, 20, 20, 255))
            # Slight 2-level noise in upper half
            im2.putpixel((10, 4), (248, 249, 246, 255))
            im1.save(p1)
            im2.save(p2)

            # Strict max_abs_diff=0 fails
            strict = gr.check_upper_face_pixel_lock(p1, p2, split_y_frac=0.55, max_abs_diff=0)
            self.assertFalse(strict["pass"])
            self.assertEqual(strict["max_diff"], 2)

            # Relaxed max_abs_diff=2 passes
            relaxed = gr.check_upper_face_pixel_lock(p1, p2, split_y_frac=0.55, max_abs_diff=2)
            self.assertTrue(relaxed["pass"])

            # CLI check returns exit code 0 when passing, 1 when failing
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gr.main(["--check-expr-pair", str(p1), str(p2)]), 1)
                self.assertEqual(
                    gr.main(["--check-expr-pair", str(p1), str(p2), "--max-abs-diff", "2"]),
                    0,
                )

    def test_size_mismatch_fails_cleanly(self):
        res = gr.check_upper_face_pixel_lock(self._make_grid(16, 16), self._make_grid(16, 20))
        self.assertFalse(res["pass"])
        self.assertIn("mismatch", res["detail"])


class TestAuditSceneMocked(unittest.TestCase):
    def test_clean_scene_passes_all_checks(self):
        rig = SimpleNamespace(
            name="Mascot",
            head_dims=(0.440, 0.448),
            mock_arms=[("Mascot | arm_L", 0.28, 0.34), ("Mascot | arm_R", 0.30, 0.34)],
            mock_legs=[("Mascot | leg_L", 0.40, 0.40)],
            mock_forward_xy=(0.0, -1.0),
            mock_to_cam_xy=(0.1, -2.5),
        )
        subj = SimpleNamespace(
            name="Mascot",
            ndc_points=[(0.25, 0.15, 2.4), (0.75, 0.85, 2.4)],
        )
        obj = SimpleNamespace(
            name="Floor",
            hide_viewport=False,
            hide_render=False,
            modifiers=[
                SimpleNamespace(name="Bevel", type="BEVEL", show_viewport=True, show_render=True),
                SimpleNamespace(name="Sub", type="SUBSURF", show_viewport=True, show_render=True, levels=2, render_levels=2),
            ],
        )
        scene = _make_mock_scene(objects=[obj])
        report = gr.audit_scene(scene, rigs=[rig], subjects=[subj], frames=[1, 30])

        self.assertTrue(report["pass"])
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["summary"]["error_count"], 0)
        self.assertEqual(report["summary"]["frames_checked"], [1, 30])
        self.assertEqual(report["summary"]["visible_triangles"], 42000)
        self.assertEqual(scene.frame_current, 1)  # Restores original frame

        text = gr.format_report(report)
        self.assertIn("PASS", text)

    def test_eevee_contract_and_dof_violations_caught(self):
        scene = _make_mock_scene(
            engine="CYCLES",
            use_raytracing=True,
            resolution_x=1920,
            resolution_y=1080,
            fps=24,
            use_dof=True,
            visible_tris=185000,
        )
        report = gr.audit_scene(scene, expect_deep_focus=True, max_tris=150000)
        self.assertFalse(report["pass"])
        checks = {i["check"] for i in report["issues"]}
        self.assertIn("eevee_contract", checks)
        self.assertIn("triangle_budget", checks)
        # Expect 6 distinct failures: engine, res, fps, raytracing, dof, tris
        self.assertEqual(report["summary"]["error_count"], 6)
        for issue in report["issues"]:
            self.assertTrue(issue["fix_hint"], f"Missing fix_hint on {issue}")

        # Portrait mode opt-in suppresses DOF failure
        report_dof_ok = gr.audit_scene(scene, expect_deep_focus=False, max_tris=150000)
        self.assertEqual(report_dof_ok["summary"]["error_count"], 5)

    def test_viewport_render_parity_mismatches_caught(self):
        bad_col = SimpleNamespace(
            name="HiddenSet",
            hide_viewport=True,
            hide_render=False,
            children=[],
        )
        bad_obj = SimpleNamespace(
            name="HeroProp",
            hide_viewport=False,
            hide_render=True,
            modifiers=[
                SimpleNamespace(name="Outline", type="SOLIDIFY", show_viewport=False, show_render=True),
                SimpleNamespace(name="Smooth", type="SUBSURF", show_viewport=True, show_render=True, levels=1, render_levels=3),
            ],
        )
        root_col = SimpleNamespace(
            name="Scene Collection",
            hide_viewport=False,
            hide_render=False,
            children=[bad_col],
        )
        scene = _make_mock_scene(objects=[bad_obj], collection=root_col)
        report = gr.audit_scene(scene)
        self.assertFalse(report["pass"])
        parity_issues = [i for i in report["issues"] if i["check"] == "viewport_render_parity"]
        self.assertEqual(len(parity_issues), 4)

    def test_rig_and_frustum_failures_and_allow_back_view(self):
        bad_rig = SimpleNamespace(
            name="Rival",
            head_dims=(0.48, 0.41),  # H/W = 0.854 -> squashed!
            mock_arms=[("Rival | arm_R", 0.60, 0.36)],  # 1.67x stretch!
            mock_forward_xy=(0.0, 1.0),  # facing away from camera
            mock_to_cam_xy=(0.0, -2.0),
        )
        clipped_subj = SimpleNamespace(
            name="Rival",
            ndc_points=[(-0.02, 0.50, 2.0), (0.50, 0.50, 2.0)],
        )
        scene = _make_mock_scene()
        report = gr.audit_scene(scene, rigs=[bad_rig], subjects=[clipped_subj], frames=[10])
        self.assertFalse(report["pass"])
        found_checks = {i["check"] for i in report["issues"]}
        self.assertEqual(
            found_checks,
            {"head_ratio", "limb_stretch", "facing_camera", "frustum_clipping"},
        )
        formatted = gr.format_report(report)
        self.assertIn("FAIL", formatted)
        self.assertIn("FIX:", formatted)

        # Explicitly allowing back view suppresses only facing_camera
        report_ots = gr.audit_scene(
            scene,
            rigs=[bad_rig],
            subjects=[clipped_subj],
            frames=[10],
            allow_back_view=("Rival",),
        )
        found_ots = {i["check"] for i in report_ots["issues"]}
        self.assertNotIn("facing_camera", found_ots)
        self.assertEqual(found_ots, {"head_ratio", "limb_stretch", "frustum_clipping"})

    def test_mascot_socket_reach_passes_and_detached_fails(self):
        # stop_hold_up palm socket reach (~0.465m) and pickup_and_present (~0.485m) MUST pass
        # against MascotRig reference length (0.42m * 1.25 = 0.525m), while detached 0.60m MUST fail.
        mascot_ok = SimpleNamespace(
            name="Mascot",
            head_dims=(0.440, 0.448),
            body=SimpleNamespace(matrix_world=SimpleNamespace(translation=(0.0, 0.0, 0.56))),
            # L shoulder is (-0.155, 0.0, 0.74); place hand_socket_L at exact 0.465m along -Y
            hand_socket_L=SimpleNamespace(matrix_world=SimpleNamespace(translation=(-0.155, -0.465, 0.74))),
            # R shoulder is (+0.155, 0.0, 0.74); place hand_socket_R at 0.485m along -Y
            hand_socket_R=SimpleNamespace(matrix_world=SimpleNamespace(translation=(0.155, -0.485, 0.74))),
            mock_forward_xy=(0.0, -1.0),
            mock_to_cam_xy=(0.0, -2.5),
        )
        scene = _make_mock_scene()
        report_ok = gr.audit_scene(scene, rigs=[mascot_ok], frames=[78])
        self.assertTrue(report_ok["pass"], f"Expected Mascot stop_hold_up reach to pass, got {report_ok['issues']}")

        # Detached / broken Mascot socket at 0.60m (> 0.525m) MUST fail with limb_stretch
        mascot_detached = SimpleNamespace(
            name="Mascot",
            head_dims=(0.440, 0.448),
            body=SimpleNamespace(matrix_world=SimpleNamespace(translation=(0.0, 0.0, 0.56))),
            hand_socket_L=SimpleNamespace(matrix_world=SimpleNamespace(translation=(-0.155, -0.600, 0.74))),
            hand_socket_R=SimpleNamespace(matrix_world=SimpleNamespace(translation=(0.155, -0.250, 0.74))),
            mock_forward_xy=(0.0, -1.0),
            mock_to_cam_xy=(0.0, -2.5),
        )
        report_bad = gr.audit_scene(scene, rigs=[mascot_detached], frames=[78])
        self.assertFalse(report_bad["pass"])
        limb_issues = [i for i in report_bad["issues"] if i["check"] == "limb_stretch"]
        self.assertEqual(len(limb_issues), 1)
        self.assertEqual(limb_issues[0]["object"], "Mascot | arm_L")
        self.assertIn("0.600m", limb_issues[0]["detail"])

    def test_stdlib_png_fallback_without_pil(self):
        try:
            from PIL import Image
        except ModuleNotFoundError:
            self.skipTest("Pillow needed to synthesize PNG fixtures")

        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "closed.png"
            p2 = Path(tmp) / "open.png"
            p3 = Path(tmp) / "flutter.png"
            im1 = Image.new("RGBA", (24, 24), (250, 249, 246, 255))
            im2 = Image.new("RGBA", (24, 24), (250, 249, 246, 255))
            im3 = Image.new("RGBA", (24, 24), (250, 249, 246, 255))
            # Lower mouth change only
            im2.putpixel((12, 18), (60, 15, 20, 255))
            # Upper eye flutter
            im3.putpixel((8, 4), (20, 20, 20, 255))
            im1.save(p1)
            im2.save(p2)
            im3.save(p3)

            # Directly exercise stdlib PNG decoder (used inside stock Blender 4.2 without PIL)
            w, h, _arr, _is_np = gr._read_png_rgba_stdlib(p1)
            self.assertEqual((w, h), (24, 24))

            # Block PIL import to verify end-to-end check_upper_face_pixel_lock without PIL
            saved_pil = sys.modules.get("PIL")
            saved_pil_img = sys.modules.get("PIL.Image")
            sys.modules["PIL"] = None  # type: ignore[assignment]
            sys.modules["PIL.Image"] = None  # type: ignore[assignment]
            try:
                ok = gr.check_upper_face_pixel_lock(p1, p2, split_y_frac=0.55, max_abs_diff=0)
                self.assertTrue(ok["pass"])
                self.assertEqual(ok["max_diff"], 0)

                bad = gr.check_upper_face_pixel_lock(p1, p3, split_y_frac=0.55, max_abs_diff=0)
                self.assertFalse(bad["pass"])
                self.assertEqual(bad["changed_pixels"], 1)
            finally:
                if saved_pil is not None:
                    sys.modules["PIL"] = saved_pil
                else:
                    sys.modules.pop("PIL", None)
                if saved_pil_img is not None:
                    sys.modules["PIL.Image"] = saved_pil_img
                else:
                    sys.modules.pop("PIL.Image", None)


if __name__ == "__main__":
    unittest.main()
