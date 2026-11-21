"""v03 interior chute camera plan (pure Python; Blender bakes it in build.py).

Shot 3 frames 109-186 only. Frame 109 reproduces v02 exactly (brass-ring
match). The aim follows the red ball through the drop and bend, then hands
off to the outlet while the ball is still rolling; the position track carries
through the lower bend past the foreground rods and lands on the outlet.
"""
import importlib.util
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "scripts/ricks_v2_kit.py").is_file())
sys.path[:0] = [str(ROOT / "scripts")]
import ricks_camera as rc

_spec = importlib.util.spec_from_file_location("gumball_v01", ROOT / "scripts/last_gumball/v01/build.py")
v01 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v01)

S3, S4 = v01.S3, v01.S4                     # 109, 187
F0, F1 = S3, S4 - 1
GX, GY, GZ = v01.GATE
OX, OY, OZ = v01.O
POINTS = v01.track_points()
LENGTHS = v01.path_tables(POINTS)
LIP = POINTS[-1]
OUTLET = (LIP[0] + .01, LIP[1], LIP[2] + .02)          # aim point just above the outlet lip
START = (GX, GY - v01.GATE_START_D, GZ)                 # v02 frame 109: ring match
HANDOFF = (150, 179)                                   # aim ball -> outlet (frames)
FOCUS_HANDOFF = (160, 177)


def ball(f):
    f = max(F0, min(F1, f))
    return v01.interior_ball(f, POINTS, LENGTHS)


def program():
    # Position: pull back and drop with the ball, sweep wide of the bend, carry
    # through the lower bend behind the foreground rods, land on the outlet.
    pos = rc.Track([
        (F0, START),
        (126, (GX + .06, GY - .62, GZ - .04)),
        (145, (GX + .38, GY - .80, GZ - .11)),
        (161, (GX + .31, GY - .91, GZ - .18)),
        (177, (GX + .17, GY - .90, GZ - .25)),
        (F1, (GX + .16, GY - .89, GZ - .255)),
    ], "carry")
    bend = (OX + .24, OY - .22, OZ + .79)
    loose = lambda f: rc.lerp(ball(f), bend, .35)          # ball travels across the frame in the bend
    track_ball = rc.Track([(F0, (GX, GY, GZ)), (111, (GX, GY, GZ)), (136, ball), (144, loose),
                           (154, loose)], "ease")
    smooth_ball = rc.damped(track_ball, F0, F1, settle_frames=11.0)
    aim = rc.Track([(F0, smooth_ball), (HANDOFF[0], smooth_ball), (HANDOFF[1], OUTLET)], "ease")
    focus = rc.Track([(F0, ball), (FOCUS_HANDOFF[0], ball), (FOCUS_HANDOFF[1], OUTLET)], "ease")
    shot3 = rc.Shot(F0, F1, pos=pos, aim=aim, focus=focus, lens=28.0, fstop=4.0, name="interior chute")
    return rc.CameraProgram([shot3])


# Static interior points at several depths, for a background-motion estimate.
STATIC = ([(OX + x, OY + .45, OZ + z) for x in (-.6, -.3, 0, .3, .6) for z in (.45, .8, 1.15)]
          + [(OX + x, OY + y, OZ + .33) for x in (-.5, -.2, .1, .4) for y in (-.1, .2)])
RODS = [(OX - .12, OY - .55), (OX + .42, OY - .50)]
GEAR = (OX - .27, OY - .56, OZ + .86)


def report(prog=None, width=1080, height=1920):
    prog = prog or program()
    rows, prev = [], None
    for f in prog.frames:
        s = prog.evaluate(f)
        b = rc.project(s, ball(f))
        motion = None
        if prev is not None:
            steps = []
            for p in STATIC:
                a, c = rc.project(prev, p), rc.project(s, p)
                if a and c and 0 <= c[0] <= 1 and 0 <= c[1] <= 1:
                    steps.append(math.hypot((c[0] - a[0]) * width, (c[1] - a[1]) * height))
            steps.sort()
            motion = steps[len(steps) // 2] if steps else None
        clear = min(math.hypot(s.pos[0] - x, s.pos[1] - y) for x, y in RODS)
        rows.append({"f": f, "ball": b, "motion": motion, "rod_clear": clear,
                     "gear_clear": rc.length(rc.sub(s.pos, GEAR))})
        prev = s
    return rows


if __name__ == "__main__":
    rows = report()
    peak = max((r for r in rows if r["motion"] is not None), key=lambda r: r["motion"])
    print("peak static motion px/f (1920 scale):", round(peak["motion"], 1), "at", peak["f"])
    for r in rows:
        if r["f"] % 3 == 0 or r["f"] in (109, 110, 113, 115, 117, 158, 172, 176, 182, 186):
            b = r["ball"]
            print(r["f"], "ball", None if b is None else (round(b[0], 3), round(b[1], 3), round(b[2], 3)),
                  "motion", None if r["motion"] is None else round(r["motion"], 1),
                  "rod", round(r["rod_clear"], 3), "gear", round(r["gear_clear"], 3))
