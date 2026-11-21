"""caveman_toilet v2: 18-cut table + pure-math per-frame pose/camera solvers.

No bpy imports: this module is unit-testable with system Python.
All positions are world-space metres; the builder bakes them per frame.
"""
import math

FPS = 30
END = 1620

# ---- 18 cuts (v1 cut7 split into wide establish + medium huddle) ----
# id, start, end, act, set, chars, hud_id
CUTS = [
    (1,    1,   75, 1, "A", ("caveman",), 1),
    (2,   75,  159, 1, "A", ("caveman",), 2),
    (3,  159,  306, 1, "A", ("caveman",), 3),
    (4,  306,  365, 1, "A", ("caveman",), 4),
    (5,  365,  429, 1, "A", ("caveman",), 5),
    (6,  429,  540, 1, "A", ("caveman", "buddy", "elder"), 6),
    (7,  540,  590, 2, "B", ("caveman", "buddy"), 7),
    (8,  590,  656, 2, "B", ("caveman", "buddy"), 7),
    (9,  656,  735, 2, "B", ("caveman", "buddy"), 8),
    (10, 735,  828, 2, "B", ("caveman",), 9),
    (11, 828,  873, 3, "B", ("elder",), 10),
    (12, 873, 1038, 3, "B", (), 11),
    (13, 1038, 1125, 3, "B", ("caveman", "buddy"), 12),
    (14, 1125, 1206, 3, "B", ("caveman", "buddy"), 13),
    (15, 1206, 1293, 4, "B", ("elder",), 14),
    (16, 1293, 1370, 4, "B", ("elder", "caveman"), 15),
    (17, 1370, 1494, 4, "C", ("caveman",), 16),
    (18, 1494, END + 1, 4, "C", ("caveman", "elder"), 17),
]

HUD_TEXTS = [
    "HISTORY MYSTERY: BEFORE TOILETS EXISTED",
    "ZERO TOILETS. ZERO DOORS. ZERO PRIVACY.",
    "10,000 BC: THE OPEN-AIR ERA",
    "EMERGENCY ALERT: STOMACH CRAMP!",
    "ANYWHERE. ANYTIME. INSTANT RELIEF.",
    "NOMAD LIFE: POOP & MOVE ON",
    "THE CAVE ERA: TRAPPED INDOORS",
    "OUTSIDE AT NIGHT = LION DINNER",
    "BAD IDEA: DROPPING BOMBS INDOORS!",
    "THE RESULT: TOTAL BIO-HAZARD",
    "TOXIC FUMES + FLIES + DEADLY BACTERIA",
    "BREATHING THEIR OWN FILTH",
    "TRIBE WIPEOUT: SELF-POISONED!",
    "EUREKA MOMENT: HYGIENE UNLOCKED!",
    "RULE #1: NEVER POOP WHERE YOU SLEEP",
    "INVENTION: THE OUTDOOR LATRINE PIT",
    "THE WORLD'S FIRST TOILET (JUGAAD EDITION)",
]

SHEET_FRAMES = [40, 230, 330, 382, 415, 480, 620, 700,
                800, 850, 950, 1180, 1250, 1330, 1452, 1560]

# ---- key world anchors ----
WALK3_START = (0.0, 6.2)
WALK3_END = (0.0, 0.0)
WALK6_START = (0.0, 5.6)
WALK6_END = (0.0, 1.6)
SQUAT_SPOT = (0.0, 0.25)          # dedicated boulder at (0,-.35)
FIRE = (0.0, 0.9)
HUDDLE = {"caveman": (-0.45, 0.30), "buddy": (0.45, 0.30)}
LION_REACT = {"caveman": (0.35, 0.55), "buddy": (0.85, 0.60)}
CORNER = (2.3, 3.3)                # poop corner (set B)
SNEAK_END = (2.2, 3.15)
ELDER_SICK = (-1.2, 2.0)
PINCH_POS = {"caveman": (-0.40, 0.75), "buddy": (0.40, 0.75)}
EUREKA_POS = (0.0, 1.4)
POINT_POS = {"elder": (-0.45, 1.2), "caveman": (0.35, 1.0)}
DIG_POS = (0.0, -0.15)
SUNSET_POS = {"caveman": (-0.85, 0.3), "elder": (0.95, -0.25)}
ARCH = (-2.2, 4.35)                # cave entrance arch (lion)

COLLAPSE_T0 = {"caveman": 1120, "buddy": 1130}


def cut_at(f):
    for c in CUTS:
        if c[1] <= f < c[2]:
            return c
    return CUTS[-1]


def hud_for_frame(f):
    return HUD_TEXTS[cut_at(f)[6] - 1]


def act_for_frame(f):
    return cut_at(f)[3]


def set_for_frame(f):
    return cut_at(f)[4]


# ---- tiny pure-python vector helpers (2D xy / 3D xyz tuples) ----
def add2(a, b): return (a[0] + b[0], a[1] + b[1])
def sub2(a, b): return (a[0] - b[0], a[1] - b[1])
def mul2(a, s): return (a[0] * s, a[1] * s)
def len2(a): return math.hypot(a[0], a[1])
def norm2(a):
    l = len2(a) or 1.0
    return (a[0] / l, a[1] / l)
def perp2(a): return (-a[1], a[0])
def rot2(a, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (a[0] * c - a[1] * s, a[0] * s + a[1] * c)
def lerp2(a, b, u): return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
def add3(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub3(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul3(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def lerp3(a, b, u):
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u,
            a[2] + (b[2] - a[2]) * u)
def clamp01(u): return max(0.0, min(1.0, u))
def ease(u):
    u = clamp01(u)
    return 1 - (1 - u) ** 3
def ramp(f, a, b): return ease((f - a) / max(1, b - a))


def standing_pelvis(xy, z=0.50):
    return (xy[0], xy[1], z)


def default_feet(xy, facing, spread=0.11):
    p = perp2(facing)
    return [(xy[0] - p[0] * spread, xy[1] - p[1] * spread, 0.02, 0.0),
            (xy[0] + p[0] * spread, xy[1] + p[1] * spread, 0.02, 0.0)]


def default_hands(pelvis, facing):
    p = perp2(facing)
    sh = 0.57
    return [(pelvis[0] + p[0] * -0.26, pelvis[1] + p[1] * -0.26, pelvis[2] + sh - 0.50),
            (pelvis[0] + p[0] * 0.26, pelvis[1] + p[1] * 0.26, pelvis[2] + sh - 0.50)]


# ================= walk cycle (period 16, stance .6 / swing .4) =================
def walk_state(f, f0, f1, start, end, phase_off=0.0, period=16, lift=0.14):
    """Real gait: pinned stance foot, swinging foot with heel/toe pitch,
    pelvis bob at 2x stride, opposite arm swing +/-28 deg."""
    dirv = norm2(sub2(end, start))
    dist = len2(sub2(end, start))
    dur = max(1, f1 - f0)
    speed = dist / dur
    t = max(0.0, min(float(dur), f - f0))
    base = add2(start, mul2(dirv, speed * t))
    phase = ((f - f0) / period + phase_off) % 1.0
    pz = 0.50 - 0.035 * math.cos(4 * math.pi * phase)
    pelvis = (base[0], base[1], pz)
    sidev = perp2(dirv)
    feet = []
    for side, off in ((-1, 0.0), (1, 0.5)):
        p = (phase + off) % 1.0
        n = math.floor((f - f0) / period + off)
        fs = f0 + (n - off) * period
        fs = max(f0, min(f1, fs))
        plant_c = add2(start, mul2(dirv, speed * max(0.0, min(float(dur), fs - f0))))
        plant = add2(plant_c, add2(mul2(dirv, 0.22), mul2(sidev, side * 0.10)))
        if p < 0.6:
            u = p / 0.6
            pitch = 0.0
            if u < 0.2:
                pitch = math.radians(10) * (1 - u / 0.2)
            elif u > 0.8:
                pitch = -math.radians(15) * ((u - 0.8) / 0.2)
            feet.append((plant[0], plant[1], 0.02, pitch))
        else:
            u = (p - 0.6) / 0.4
            fs2 = max(f0, min(f1, fs + period))
            next_c = add2(start, mul2(dirv, speed * max(0.0, min(float(dur), fs2 - f0))))
            nxt = add2(next_c, add2(mul2(dirv, 0.22), mul2(sidev, side * 0.10)))
            pos = lerp2(plant, nxt, ease(u))
            z = 0.02 + lift * math.sin(math.pi * u)
            pitch = math.radians(18) * (1 - u) - math.radians(22) * u
            feet.append((pos[0], pos[1], z, pitch))
    # arms: opposite swing, hand targets relative to shoulders
    hands = []
    for side, off in ((-1, 0.0), (1, 0.5)):
        th = math.radians(28) * math.sin(2 * math.pi * (phase + off + 0.5))
        hands.append((dirv[0] * math.sin(th) * 0.42 + sidev[0] * side * 0.24,
                      dirv[1] * math.sin(th) * 0.42 + sidev[1] * side * 0.24,
                      -math.cos(th) * 0.42))
    return dict(pelvis=pelvis, facing=dirv, feet=feet, hand_offsets=hands,
                phase=phase, speed=speed)


def walk_hand_targets(pelvis, facing, hand_offsets):
    """Convert walk hand offsets (relative to shoulder) to world targets."""
    out = []
    for side, off in zip((-1, 1), hand_offsets):
        sh = (pelvis[0], pelvis[1], pelvis[2] + 0.57)
        out.append((sh[0] + off[0], sh[1] + off[1], sh[2] + off[2]))
    return out


# ================= squat 4-beat helpers =================
def squat_pose(xy, facing, s, lean_max=math.radians(22)):
    """s in 0..1 descent. Hips back+down, knees forward, torso lean."""
    back = mul2(facing, -0.12 * s)
    pelvis = (xy[0] + back[0], xy[1] + back[1], 0.50 - 0.26 * s)
    lean = lean_max * s
    p = perp2(facing)
    feet = [(xy[0] - p[0] * 0.16, xy[1] - p[1] * 0.16, 0.02, 0.0),
            (xy[0] + p[0] * 0.16, xy[1] + p[1] * 0.16, 0.02, 0.0)]
    hands = [(pelvis[0] + facing[0] * 0.20 - p[0] * 0.10,
              pelvis[1] + facing[1] * 0.20 - p[1] * 0.10, pelvis[2] + 0.18),
             (pelvis[0] + facing[0] * 0.20 + p[0] * 0.10,
              pelvis[1] + facing[1] * 0.20 + p[1] * 0.10, pelvis[2] + 0.18)]
    return pelvis, lean, feet, hands


def dash_path(f):
    """f345-368 polyline dash behind the hide-rock; returns (xy, dir)."""
    pts = [(0.0, 0.0), (0.3, 1.0), SQUAT_SPOT]
    u = clamp01((f - 345) / 23.0)
    seg = u * 2
    i = min(1, int(seg))
    t = seg - i
    a, b = pts[i], pts[i + 1]
    return lerp2(a, b, t), norm2(sub2(b, a))


# ================= collapse (staggered, 3 phases + bounce) =================
def collapse_state(char, f, base, facing):
    t0 = COLLAPSE_T0[char]
    p = perp2(facing)
    if f < t0:
        return None  # caller uses pinch pose
    if f < t0 + 12:                      # phase 1: stagger sway
        u = (f - t0) / 12.0
        sway = 0.08 * math.sin(2 * math.pi * u)
        pelvis = (base[0] + p[0] * sway, base[1] + p[1] * sway, 0.50)
        lean = 0.06 * math.sin(2 * math.pi * u)
        flail = 0.30 + 0.12 * math.sin(4 * math.pi * u)
        hands = [(pelvis[0] - p[0] * flail, pelvis[1] - p[1] * flail, 1.05),
                 (pelvis[0] + p[0] * flail, pelvis[1] + p[1] * flail, 1.05)]
        feet = default_feet(base, facing)
        return dict(pelvis=pelvis, lean=lean, feet=feet, hands=hands,
                    expr="knockout", phase="stagger")
    if f < t0 + 22:                      # phase 2: knees buckle
        u = ramp(f, t0 + 12, t0 + 22)
        pelvis = (base[0], base[1], 0.50 - 0.22 * u)
        lean = 0.15 * u
        feet = default_feet(base, facing)
        hands = [(pelvis[0] - p[0] * 0.28, pelvis[1] - p[1] * 0.28, 0.75),
                 (pelvis[0] + p[0] * 0.28, pelvis[1] + p[1] * 0.28, 0.75)]
        return dict(pelvis=pelvis, lean=lean, feet=feet, hands=hands,
                    expr="knockout", phase="buckle", knee_in=u)
    if f < t0 + 32:                      # phase 3: fall backward 78 deg
        u = ramp(f, t0 + 22, t0 + 32)
        back = mul2(facing, -0.30 * u)
        pelvis = (base[0] + back[0], base[1] + back[1], 0.28 - 0.18 * u)
        lean = -math.radians(78) * u
        feet = [(base[0] + facing[0] * 0.15 * u - p[0] * 0.11,
                 base[1] + facing[1] * 0.15 * u - p[1] * 0.11, 0.02, 0.0),
                (base[0] + facing[0] * 0.15 * u + p[0] * 0.11,
                 base[1] + facing[1] * 0.15 * u + p[1] * 0.11, 0.02, 0.0)]
        hands = [(pelvis[0] - p[0] * 0.25, pelvis[1] - p[1] * 0.25, pelvis[2] + 0.05),
                 (pelvis[0] + p[0] * 0.25, pelvis[1] + p[1] * 0.25, pelvis[2] + 0.05)]
        return dict(pelvis=pelvis, lean=lean, feet=feet, hands=hands,
                    expr="knockout", phase="fall")
    # settled: CONSTANT hold (bounce overshoot 4 f)
    b = f - (t0 + 32)
    extra = -math.radians(4) * math.sin(math.pi * clamp01(b / 4.0)) if b < 4 else 0.0
    back = mul2(facing, -0.30)
    pelvis = (base[0] + back[0], base[1] + back[1], 0.10)
    lean = -math.radians(78) + extra
    feet = [(base[0] + facing[0] * 0.15 - p[0] * 0.11,
             base[1] + facing[1] * 0.15 - p[1] * 0.11, 0.02, 0.0),
            (base[0] + facing[0] * 0.15 + p[0] * 0.11,
             base[1] + facing[1] * 0.15 + p[1] * 0.11, 0.02, 0.0)]
    hands = [(pelvis[0] - p[0] * 0.25, pelvis[1] - p[1] * 0.25, 0.12),
             (pelvis[0] + p[0] * 0.25, pelvis[1] + p[1] * 0.25, 0.12)]
    return dict(pelvis=pelvis, lean=lean, feet=feet, hands=hands,
                expr="knockout", phase="settled")


# ================= dig cycle (cut17, period 30) =================
def dig_blade(f):
    """Local (facing=+Y) blade target + thrust amount for the stone shovel."""
    u = ((f - 1370) % 30) / 30.0
    if u < 0.30:
        t = ease(u / 0.30)
        return lerp3((0, 0.35, 0.05), (0, 0.55, -0.35), t), t
    if u < 0.55:
        t = ease((u - 0.30) / 0.25)
        return lerp3((0, 0.55, -0.35), (0, 0.45, -0.10), t), 1.0 - t
    if u < 0.80:
        t = ease((u - 0.55) / 0.25)
        return lerp3((0, 0.45, -0.10), (0, 0.30, 0.55), t), 0.0
    t = ease((u - 0.80) / 0.20)
    return lerp3((0, 0.30, 0.55), (0, 0.35, 0.05), t), 0.0


# ================= main per-frame pose solver =================
def pose_state(char, f):
    """Return full rig state for char at frame f, or None if not in shot.
    Keys: pelvis, facing(2D), lean, feet[(x,y,z,pitch)], hands[(x,y,z)],
    expr, tilt, shoulder_drop, knee_in, visible."""
    c = cut_at(f)
    cid, a, b, act, st, chars, hud = c
    if char not in chars:
        return None
    cam_pos, cam_look, lens = camera_at(f)
    base = dict(pelvis=(0, 0, 0.50), facing=(0, -1), lean=0.0,
                feet=None, hands=None, expr="neutral", tilt=0.0,
                shoulder_drop=0.0, knee_in=0.0, visible=True)

    def face_cam(xy):
        return norm2(sub2((cam_pos[0], cam_pos[1]), xy))

    if cid == 1:
        xy = (0.0, 0.0)
        base.update(pelvis=standing_pelvis(xy), facing=face_cam(xy),
                    expr="confused", tilt=math.radians(6) * math.sin(f * 0.15))
    elif cid == 2:
        xy = (0.0, 0.0)
        fc = face_cam(xy)
        pel = standing_pelvis(xy)
        pel = (pel[0], pel[1], pel[2] + 0.012 * math.sin(f * 0.35))
        base.update(pelvis=pel, facing=fc, expr="neutral",
                    tilt=math.radians(2) * math.sin(f * 0.11))
        p = perp2(fc)
        base["hands"] = [(xy[0] - p[0] * 0.34, xy[1] - p[1] * 0.34, 0.95),
                         (xy[0] + p[0] * 0.34, xy[1] + p[1] * 0.34, 0.95)]
    elif cid == 3:
        w = walk_state(f, a, b, WALK3_START, WALK3_END)
        base.update(pelvis=w["pelvis"], facing=w["facing"], feet=w["feet"],
                    hands=walk_hand_targets(w["pelvis"], w["facing"], w["hand_offsets"]),
                    expr="confused")
    elif cid in (4, 5):
        if f < 345:                                   # discomfort clutch
            xy = (0.0, 0.0)
            fc = face_cam(xy)
            sway = 0.02 * math.sin(f * 0.4)
            pel = (xy[0] + sway, xy[1], 0.50)
            p = perp2(fc)
            hands = [(pel[0] + fc[0] * 0.18 - p[0] * 0.07,
                      pel[1] + fc[1] * 0.18 - p[1] * 0.07, 0.74),
                     (pel[0] + fc[0] * 0.18 + p[0] * 0.07,
                      pel[1] + fc[1] * 0.18 + p[1] * 0.07, 0.74)]
            feet = [(xy[0] - p[0] * 0.05, xy[1] - p[1] * 0.05, 0.02, 0.0),
                    (xy[0] + p[0] * 0.05, xy[1] + p[1] * 0.05, 0.02, 0.0)]
            base.update(pelvis=pel, facing=fc, feet=feet, hands=hands,
                        expr="clenched", knee_in=0.7, lean=0.10)
        elif f < 368:                                 # dash behind rock
            xy, dv = dash_path(f)
            w = walk_state(f, 345, 368, (0, 0), SQUAT_SPOT, period=10, lift=0.10)
            pel = (xy[0], xy[1], w["pelvis"][2])
            base.update(pelvis=pel, facing=dv, feet=w["feet"],
                        hands=walk_hand_targets(pel, dv, w["hand_offsets"]),
                        expr="determined")
        else:                                         # descent + relief
            cam5 = (-1.15, -0.75)
            fc = norm2(sub2(SQUAT_SPOT, cam5))
            facing = rot2(fc, math.radians(-55))
            s = ramp(f, 368, 395)
            pel, lean, feet, hands = squat_pose(SQUAT_SPOT, facing, s)
            expr = "strain" if f < 395 else "relieved"
            drop = 0.03 * ramp(f, 395, 403) if f >= 395 else 0.0
            base.update(pelvis=pel, facing=facing, lean=lean, feet=feet,
                        hands=hands, expr=expr, shoulder_drop=drop)
    elif cid == 6:
        off = {"caveman": (0.0, 0.0), "buddy": (-0.75, 0.55), "elder": (0.75, 0.55)}[char]
        po = {"caveman": 0.0, "buddy": 0.33, "elder": 0.66}[char]
        dirv = norm2(sub2(WALK6_END, WALK6_START))
        lat = perp2(dirv)
        start = add2(WALK6_START, mul2(lat, off[0]))
        end = add2(WALK6_END, mul2(lat, off[0]))
        w = walk_state(f, a, b, start, end, phase_off=po)
        base.update(pelvis=w["pelvis"], facing=w["facing"], feet=w["feet"],
                    hands=walk_hand_targets(w["pelvis"], w["facing"], w["hand_offsets"]),
                    expr="neutral")
    elif cid in (7, 8):
        xy = HUDDLE[char]
        fc = face_cam(xy)
        base.update(pelvis=standing_pelvis(xy), facing=fc, expr="neutral")
        tofire = norm2(sub2(FIRE, xy))
        base["hands"] = [(xy[0] + tofire[0] * 0.28 - perp2(fc)[0] * 0.10,
                          xy[1] + tofire[1] * 0.28 - perp2(fc)[1] * 0.10, 0.78),
                         (xy[0] + tofire[0] * 0.28 + perp2(fc)[0] * 0.10,
                          xy[1] + tofire[1] * 0.28 + perp2(fc)[1] * 0.10, 0.78)]
    elif cid == 9:
        xy = LION_REACT[char]
        fc = norm2(sub2(ARCH, xy))
        base.update(pelvis=standing_pelvis(xy), facing=fc, expr="panic",
                    tilt=math.radians(3) * math.sin(f * 0.5))
        p = perp2(fc)
        base["hands"] = [(xy[0] - p[0] * 0.30, xy[1] - p[1] * 0.30, 1.15),
                         (xy[0] + p[0] * 0.30, xy[1] + p[1] * 0.30, 1.15)]
    elif cid == 10:
        if f < 772:                                   # sneaky tiptoe glide
            u = clamp01((f - 735) / 37.0)
            xy = lerp2(HUDDLE["caveman"], SNEAK_END, ease(u))
            dv = norm2(sub2(SNEAK_END, HUDDLE["caveman"]))
            bob = 0.02 * math.sin(f * 0.6)
            pel = (xy[0], xy[1], 0.52 + bob)
            p = perp2(dv)
            step = 0.06 * math.sin(f * 0.6)
            feet = [(xy[0] - p[0] * 0.06 + dv[0] * step,
                     xy[1] - p[1] * 0.06 + dv[1] * step, 0.02 + max(0, 0.05 * math.sin(f * 0.6)), 0.0),
                    (xy[0] + p[0] * 0.06 - dv[0] * step,
                     xy[1] + p[1] * 0.06 - dv[1] * step, 0.02 + max(0, -0.05 * math.sin(f * 0.6)), 0.0)]
            base.update(pelvis=pel, facing=dv, feet=feet, expr="sneaky", lean=0.12)
        else:                                         # compressed squat + hold
            cam10 = (1.35, 1.55)
            fc = norm2(sub2(SNEAK_END, cam10))
            facing = rot2(fc, math.radians(-25))
            s = ramp(f, 772, 798)
            pel, lean, feet, hands = squat_pose(SNEAK_END, facing, s)
            base.update(pelvis=pel, facing=facing, lean=lean, feet=feet,
                        hands=hands, expr="sneaky")
    elif cid == 11:
        xy = ELDER_SICK
        fc = face_cam(xy)
        pel = standing_pelvis(xy)
        p = perp2(fc)
        hands = [(pel[0] + fc[0] * 0.18 - p[0] * 0.07,
                  pel[1] + fc[1] * 0.18 - p[1] * 0.07, 0.74),
                 (pel[0] + fc[0] * 0.18 + p[0] * 0.07,
                  pel[1] + fc[1] * 0.18 + p[1] * 0.07, 0.74)]
        base.update(pelvis=pel, facing=fc, hands=hands, expr="sick",
                    lean=0.12 + 0.04 * math.sin(f * 0.3))
    elif cid in (13, 14):
        xy = PINCH_POS[char]
        fc = face_cam(xy)
        cs = collapse_state(char, f, xy, fc) if cid == 14 or f >= 1120 else None
        if cs is not None:
            base.update(pelvis=cs["pelvis"], facing=fc, lean=cs["lean"],
                        feet=cs["feet"], hands=cs["hands"], expr=cs["expr"],
                        knee_in=cs.get("knee_in", 0.0))
        else:                                         # upright nose pinch
            pel = standing_pelvis(xy)
            p = perp2(fc)
            head = add3(pel, (0, 0, 0.80))
            nose = add3(head, (fc[0] * 0.10, fc[1] * 0.10, -0.06))
            hands = [nose,
                     (pel[0] + p[0] * 0.26, pel[1] + p[1] * 0.26, pel[2] + 0.07)]
            base.update(pelvis=pel, facing=fc, hands=hands, expr="sick",
                        lean=0.05 * math.sin(f * 0.25))
    elif cid == 15:
        xy = EUREKA_POS
        fc = face_cam(xy)
        pel = standing_pelvis(xy)
        p = perp2(fc)
        e = ev15(f)
        base.update(pelvis=pel, facing=fc, expr="inspired",
                    hands=[(pel[0] - p[0] * 0.26, pel[1] - p[1] * 0.26, 0.57),
                           (pel[0] + p[0] * 0.24, pel[1] + p[1] * 0.24, 0.90 + 0.35 * e)])
    elif cid == 16:
        xy = POINT_POS[char]
        fc = face_cam(xy)
        pel = standing_pelvis(xy)
        base.update(pelvis=pel, facing=fc,
                    expr="stern" if char == "elder" else "neutral")
        if char == "elder":
            toarch = norm2(sub2(ARCH, xy))
            toarch = norm2((toarch[0], toarch[1] * 0.35))  # sideways so arm clears torso
            base["hands"] = [(pel[0] - perp2(fc)[0] * 0.26,
                              pel[1] - perp2(fc)[1] * 0.26, 0.57),
                             (pel[0] + toarch[0] * 0.52, pel[1] + toarch[1] * 0.52, 1.12)]
        else:
            base["facing"] = norm2(sub2(POINT_POS["elder"], xy))
    elif cid == 17:
        xy = DIG_POS
        facing = (0.0, 1.0)
        blade, thrust = dig_blade(f)
        pel = (xy[0], xy[1], 0.50)
        lean = math.radians(15) * thrust
        feet = [(xy[0] - 0.13, xy[1], 0.02, 0.0), (xy[0] + 0.13, xy[1], 0.02, 0.0)]
        # hands grip shovel handle (builder places shovel from blade target)
        bw = add3((xy[0], xy[1], 0), blade)
        grip_lo = lerp3(bw, (xy[0], xy[1] + 0.10, 0.95), 0.45)
        grip_hi = lerp3(bw, (xy[0], xy[1] + 0.10, 0.95), 0.75)
        base.update(pelvis=pel, facing=facing, lean=lean, feet=feet,
                    hands=[grip_lo, grip_hi], expr="determined")
        base["blade"] = bw
        base["thrust"] = thrust
    elif cid == 18:
        xy = SUNSET_POS[char]
        fc = face_cam(xy)
        pel = standing_pelvis(xy)
        p = perp2(fc)
        base.update(pelvis=pel, facing=fc, expr="triumphant")
        if char == "caveman":
            base["hands"] = [(pel[0] - p[0] * 0.26, pel[1] - p[1] * 0.26, 0.57),
                             (pel[0] + p[0] * 0.28, pel[1] + p[1] * 0.28, 1.15)]
        else:
            clap = 0.06 * abs(math.sin(f * 0.35))
            base["hands"] = [(pel[0] + fc[0] * 0.18 - p[0] * clap,
                              pel[1] + fc[1] * 0.18 - p[1] * clap, 0.95),
                             (pel[0] + fc[0] * 0.18 + p[0] * clap,
                              pel[1] + fc[1] * 0.18 + p[1] * clap, 0.95)]
    if base["feet"] is None:
        base["feet"] = default_feet(base["pelvis"][:2], base["facing"])
    if base["hands"] is None:
        base["hands"] = default_hands(base["pelvis"], base["facing"])
    return base


def ev15(f):
    """Eureka bulb/hand pop envelope (finite event)."""
    if f <= 1215:
        return 0.0
    if f < 1218:
        return -0.06 * ease((f - 1215) / 3)
    if f < 1222:
        return -0.06 + 1.14 * ease((f - 1218) / 4)
    if f < 1226:
        return 1.08 - 0.08 * ease((f - 1222) / 4)
    return 1.0


# ================= cameras (per-cut, baked per frame) =================
def camera_at(f):
    c = cut_at(f)
    cid, a, b = c[0], c[1], c[2]
    u = clamp01((f - a) / max(1, b - a))
    if cid == 1:
        pos = lerp3((-0.9, -3.4, 1.35), (-0.5, -2.3, 1.25), ease(u))
        return pos, (0, 0, 1.05), 40
    if cid == 2:
        pos = lerp3((0.35, -2.0, 1.25), (0.30, -1.84, 1.22), ease(u))
        return pos, (0, 0, 1.1), 45
    if cid == 3:
        w = walk_state(f, a, b, WALK3_START, WALK3_END)
        p = w["pelvis"]
        return (p[0] - 1.9, p[1] - 2.3, 1.35), (p[0], p[1], 1.0), 40
    if cid == 4:
        look = lerp3((0, 0, 0.95), (SQUAT_SPOT[0], SQUAT_SPOT[1], 0.8),
                     clamp01((f - 345) / 20))
        return (-0.4, -2.2, 1.2), look, 40
    if cid == 5:
        return (-1.15, -0.75, 1.05), (SQUAT_SPOT[0], SQUAT_SPOT[1], 0.75), 42
    if cid == 6:
        dirv = norm2(sub2(WALK6_END, WALK6_START))
        dist = len2(sub2(WALK6_END, WALK6_START))
        lead = add2(WALK6_START, mul2(dirv, dist * clamp01((f - a) / (b - a))))
        return (lead[0] - 2.6, lead[1] - 3.2, 1.5), (lead[0], lead[1], 1.0), 36
    if cid == 7:
        return (0, -4.6, 1.7), (0, 0.8, 1.0), 30
    if cid == 8:
        return (0, -2.15, 1.25), (0, 0.8, 0.95), 45
    if cid == 9:
        return (0.55, -1.7, 1.25), (-0.35, 2.0, 1.2), 32
    if cid == 10:
        if f < 772:
            xy = lerp2(HUDDLE["caveman"], SNEAK_END, ease(clamp01((f - 735) / 37)))
        else:
            xy = SNEAK_END
        return (1.35, 1.55, 1.15), (xy[0], xy[1], 0.75), 50
    if cid == 11:
        return (-1.08, 0.82, 1.4), (ELDER_SICK[0], ELDER_SICK[1], 1.32), 55
    if cid == 12:
        pos = lerp3((0.9, 1.2, 0.7), (1.3, 1.8, 0.6), ease(u))
        return pos, (CORNER[0], CORNER[1], 0.4), 35
    if cid == 13:
        pos = lerp3((0, -1.55, 1.3), (0, -1.4, 1.3), ease(u))
        return pos, (0, 0.75, 1.2), 55
    if cid == 14:
        return (0, -2.0, 2.0), (0, 0.9, 0.35), 40
    if cid == 15:
        pos = lerp3((0.5, -0.5, 1.4), (0.35, -0.2, 1.35), ease(u))
        return pos, (EUREKA_POS[0], EUREKA_POS[1], 1.35), 45
    if cid == 16:
        return (0.1, -1.7, 1.3), (-0.55, 1.3, 1.15), 36
    if cid == 17:
        return (1.9, -0.9, 1.05), (0.0, 0.55, 0.55), 40
    return (0, -3.0, 1.2), (0, 0.6, 0.8), 38
