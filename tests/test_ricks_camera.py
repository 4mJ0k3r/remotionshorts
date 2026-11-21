"""Pure-Python checks for the opt-in camera program (no Blender needed)."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ricks_camera as rc


def vel(fn, f, h=.01):
    a, b = fn(f - h), fn(f + h)
    return tuple((y - x) / (2 * h) for x, y in zip(a, b))


class Tracks(unittest.TestCase):
    def test_carry_keeps_momentum_through_inner_keys(self):
        t = rc.Track([(1, (0, 0, 0)), (20, (1, 0, 0)), (40, (2, .5, 0)), (60, (2.5, .5, 0))], "carry")
        left, right = vel(t, 39.99), vel(t, 40.01)
        self.assertGreater(rc.length(vel(t, 40)), .01)            # still moving at the waypoint
        self.assertLess(rc.length(rc.sub(left, right)), 1e-3)     # no kink
        self.assertLess(rc.length(vel(t, 1.0)), 1e-3)             # eased start
        self.assertLess(rc.length(vel(t, 60.0)), 1e-3)            # eased landing

    def test_ease_settles_on_every_key(self):
        t = rc.Track([(1, (0, 0, 0)), (20, (1, 0, 0)), (40, (2, 0, 0))], "ease")
        self.assertLess(rc.length(vel(t, 20)), 1e-6)

    def test_callable_keys_track_a_moving_subject(self):
        subject = lambda f: (f * .01, 0, 1)
        t = rc.handoff((0, 0, 0), subject, 10, 20)
        self.assertEqual(t(5), (0, 0, 0))
        self.assertEqual(t(30), subject(30))
        mid = t(15)
        self.assertAlmostEqual(mid[0], subject(15)[0] * .5)

    def test_lead_and_damped(self):
        subject = lambda f: (f * .02, 0, 0)
        self.assertAlmostEqual(rc.lead(subject, 5)(10)[0], .3)
        self.assertAlmostEqual(rc.lead(subject, 5, max_m=.05)(10)[0], .25)
        step = lambda f: (0, 0, 0) if f < 10 else (1, 0, 0)
        d = rc.damped(step, 1, 60, settle_frames=8)
        self.assertLess(d(12)[0], .9)                             # trails the jump
        self.assertGreater(d(60)[0], .999)                        # and catches up without overshoot
        self.assertLessEqual(max(d(f)[0] for f in range(1, 61)), 1.0 + 1e-6)


class Program(unittest.TestCase):
    def build(self):
        # Shot A: travel while attention hands off from a prop to a face, then settle.
        prop, face = (.9, .2, .8), (0, 0, 1.24)
        a = rc.Shot(1, 24, pos=rc.Track([(1, (.6, -3.4, 1.2)), (12, (.3, -3.1, 1.2)), (22, (0, -2.95, 1.2))], "carry"),
                    aim=rc.handoff(prop, face, 6, 16), focus=rc.handoff(prop, face, 9, 18), lens=26)
        b = rc.Shot(25, 48, pos=rc.Track([(25, (1.25, -2.68, 1.2)), (48, (1.35, -2.9, 1.2))], "carry"),
                    aim=face, lens=26)
        return rc.CameraProgram([a, b]), prop, face

    def test_shots_must_tile_and_cuts_are_hard(self):
        prog, _, face = self.build()
        self.assertEqual(prog.cuts, [25])
        self.assertTrue(prog.evaluate(25).cut)
        self.assertFalse(prog.evaluate(24).cut)
        jump = rc.length(rc.sub(prog.evaluate(25).pos, prog.evaluate(24).pos))
        self.assertGreater(jump, 1.0)                             # authored cut is not smoothed away
        with self.assertRaises(ValueError):
            rc.CameraProgram([rc.Shot(1, 10, (0, 0, 0), face), rc.Shot(12, 20, (0, 0, 0), face)])

    def test_attention_shifts_while_camera_still_travels(self):
        prog, prop, face = self.build()
        mid = 11
        moving = rc.length(rc.sub(prog.evaluate(mid + 1).pos, prog.evaluate(mid).pos))
        self.assertGreater(moving, .01)
        aim = prog.evaluate(mid).aim
        self.assertTrue(0 < rc.length(rc.sub(aim, prop)) < rc.length(rc.sub(face, prop)))
        # Focus is independent: it lags the aim at this frame.
        s = prog.evaluate(mid)
        self.assertGreater(rc.length(rc.sub(s.focus, face)), rc.length(rc.sub(s.aim, face)))

    def test_settles_before_the_cut(self):
        prog, _, _ = self.build()
        settled = rc.settle_frame(prog, 0, threshold_px=2.0)
        self.assertIsNotNone(settled)
        self.assertLessEqual(settled, 24)
        speeds = dict(rc.screen_speed(prog))
        self.assertNotIn(25, speeds)                              # cut frames are excluded

    def test_projection_centres_the_aim(self):
        prog, _, face = self.build()
        x, y, z = rc.project(prog.evaluate(30), face)
        self.assertAlmostEqual(x, .5, places=6)
        self.assertAlmostEqual(y, .5, places=6)


class Planning(unittest.TestCase):
    def test_parallax_reveal_clears_the_pillar(self):
        # Last Gumball v01 geometry: pillar between the camera and the window.
        start, window, pillar = (.85, -1.60, 1.25), (.02, 0, 1.22), (.665, -1.10, 1.22)
        self.assertTrue(rc.occluded(start, window, pillar, .11))
        end, metres = rc.parallax_reveal(start, window, pillar, .11, (-1, -.2, 0), lens=26)
        self.assertGreater(metres, 0)
        state = rc.CameraState(0, end, window, window, 26, 0, 2.8, 0, False)
        x = rc.project(state, pillar)[0]
        self.assertTrue(x > 1 or x < 0)
        self.assertFalse(rc.occluded(end, window, pillar, .11))

    def test_match_cut_distance(self):
        # Brass slot rim r .045 at .32 m, 50 mm -> interior gate r .06 at 28 mm.
        d = rc.matched_distance(.045, .32, 50, .06, 28)
        self.assertAlmostEqual(d, .06 * .32 * 28 / (.045 * 50))
        a = rc.CameraState(0, (0, -.32, 1), (0, 0, 1), (0, 0, 1), 50, 0, 4, 0, False)
        b = rc.CameraState(1, (6, -d, 1), (6, 0, 1), (6, 0, 1), 28, 0, 2.8, 1, True)
        err = rc.match_error(a, (0, 0, 1), .045, b, (6, 0, 1), .06)
        self.assertLess(err["centre_offset"], 1e-9)
        self.assertAlmostEqual(err["size_ratio"], 1.0)


if __name__ == "__main__":
    unittest.main()
