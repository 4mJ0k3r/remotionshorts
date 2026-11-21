"""Regression cases for the failure modes that motivated the shared pipeline."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from shorts_qa_checks import frame_differences, mad_spikes, frozen_spans, shadow_stability
from calibration_sheet import build_plan
from ricks_lookdev import ease5, distance_for_height, interpolate_distance, ink_width


class ImageGates(unittest.TestCase):
    def test_continuous_shot_label_does_not_hide_transform_reset(self):
        diff = np.array([.2]*30); diff[14] = 50
        meta = {'shots': [{'a': 0}, {'a': 15}], 'cuts': []}
        self.assertIn(15, mad_spikes(diff, meta)['review'])
        self.assertNotIn(15, mad_spikes(diff, dict(meta, cuts=[15]))['review'])
        self.assertIn(15, mad_spikes(diff, dict(meta, cuts=[15], continuous_junctions=[15]))['review'])

    def test_legacy_manifest_still_exempts_actual_shot_cut(self):
        diff = np.zeros(30); diff[14] = 50
        self.assertNotIn(15, mad_spikes(diff, {'shots': [{'a': 15}]})['review'])

    def test_caption_exclusion_does_not_erase_raw_differences(self):
        frames = np.zeros((2, 20, 10, 3), np.uint8); frames[1, 16:] = 255
        self.assertGreater(frame_differences(frames)[0], 0)
        self.assertEqual(frame_differences(frames, [[0, .8, 1, 1]])[0], 0)
        with self.assertRaises(ValueError): frame_differences(frames, [[0, 0, 1, 1]])

    def test_shadow_shift_with_unchanged_median_is_caught(self):
        frames = np.full((20, 32, 32, 3), 180, np.uint8)
        frames[:, :16, :16] = 80
        spec = {'start': 0, 'end': 20, 'registration': 'locked-camera', 'regions': [[0, 0, 1, 1]]}
        self.assertEqual(shadow_stability(frames, {'shadow_checks': [spec]})[0]['status'], 'PASS')
        frames[10] = np.roll(frames[10], 16, axis=1)
        self.assertEqual(shadow_stability(frames, {'shadow_checks': [spec]})[0]['status'], 'REVIEW')
        self.assertEqual(shadow_stability(frames, {})[0]['status'], 'UNVERIFIED')

    def test_unregistered_moving_shadows_are_unverified(self):
        frames = np.zeros((4, 10, 10, 3), np.uint8)
        spec = {'start': 0, 'end': 4, 'regions': [[0, 0, 1, 1]]}
        self.assertEqual(shadow_stability(frames, {'shadow_checks': [spec]})[0]['status'], 'UNVERIFIED')

    def test_frozen_run_reaching_eof_is_reported(self):
        self.assertEqual(frozen_spans(np.zeros(12)), [(0, 12)])

    def test_planned_flash_exit_is_not_a_spurious_pop(self):
        diff = np.zeros(30); diff[9] = 80; diff[12] = 80
        self.assertEqual(mad_spikes(diff, {'cuts': [], 'flash': [10, 12]})['review'], [])


class CalibrationGates(unittest.TestCase):
    def test_transition_interiors_and_both_junction_sides_are_included(self):
        plan = build_plan({'shots': [{'id': 1, 'a': 0, 'b': 40}, {'id': 2, 'a': 40, 'b': 100}],
                           'transitions': [[60, 80]]}, 100)
        self.assertTrue(set([38, 39, 40, 41, 42, 65, 70, 75]).issubset(plan['frame_indices']))
        self.assertEqual(plan['blender_frames'], [f+1 for f in plan['frame_indices']])
        self.assertEqual(plan['closeup_status'], 'UNVERIFIED')

    def test_closeup_not_already_a_keyframe_is_added(self):
        crops = [{'frame': 13, 'kind': 'hat_brim', 'region': [0, 0, .5, .5]},
                 {'frame': 16, 'kind': 'hand_prop', 'region': [.5, .5, 1, 1]}]
        plan = build_plan({'closeups': crops}, 100)
        self.assertEqual(plan['closeup_status'], 'DECLARED')
        self.assertIn(13, plan['frame_indices']); self.assertIn(16, plan['frame_indices'])


class FramingMath(unittest.TestCase):
    def test_optical_size_easing_and_ink_clamp(self):
        self.assertEqual(ease5(0), 0); self.assertEqual(ease5(1), 1)
        self.assertAlmostEqual(ease5(.5), .5)
        self.assertAlmostEqual(distance_for_height(1.8, .8, 50), 3.125)
        self.assertAlmostEqual(interpolate_distance(2, 4, .5), 8/3)
        self.assertAlmostEqual(ink_width(4, 50, 999), ink_width(4, 50, 3))


if __name__ == '__main__': unittest.main()
