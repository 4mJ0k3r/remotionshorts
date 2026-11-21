"""Opt-in camera program for Rick's Clips Blender shots: independent position,
aim, focus and lens tracks with in-shot handoffs, hard cuts between shots.

Pure Python core, so plans can be checked with system Python. Blender baking
uses bpy/mathutils only inside key_camera() and bake().

Model
-----
A CameraProgram is a list of Shots. A Shot owns its frame range and four
independent tracks (pos, aim, focus, lens) plus roll and f-stop. A shot
boundary is always a HARD cut: nothing is interpolated across it, so match
cuts and cut-on-action stay exactly where they are authored.

A Track is a list of keys (frame, value). A value is a number, a 3-tuple, or
a callable(frame) -> value for a moving subject. Between keys a track uses:

  "carry"  Catmull-Rom in value AND time. Velocity is continuous through inner
           keys, so a camera passing a waypoint keeps its momentum.
           The ends ease in and out. Default for position.
  "ease"   quintic ease per segment. The track settles on every key (a
           deliberate rest or punchline hold). Default for aim/focus/lens.
  "linear" constant speed per segment.

Helpers
-------
  handoff(a, b, start, end)      aim/focus moves from target a to b while the
                                 position track keeps travelling.
  lead(subject, frames, max_m)   aim slightly ahead of a moving subject.
  damped(fn, f0, f1, settle)     critically damped follow (frame trails, catches up).
  parallax_reveal(...)           truck distance that clears a foreground occluder.
  matched_distance(...)          distance that keeps a circle the same screen size
                                 across a match cut.
  screen_speed(program, ...)     per-frame estimate in px/frame at 1080x1920
                                 (the repo's 55 px/frame gate scale is 1920 long edge).

Coordinates: metres, Z up, Blender camera looks down -Z with +Y up.
Sensor: the kit's vertical 36 mm fit, so a 9:16 frame is 20.25 mm wide.
"""
from dataclasses import dataclass, field
import math

SENSOR_H = 36.0
ASPECT = 9 / 16


# ------------------------------------------------------------------ vector maths
def _v(x):
    return tuple(float(c) for c in x)


def add(a, b): return tuple(x + y for x, y in zip(a, b))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def length(a): return math.sqrt(dot(a, a))
def lerp(a, b, t): return tuple(x + (y - x) * t for x, y in zip(a, b))


def norm(a):
    n = length(a)
    return mul(a, 1 / n) if n > 1e-12 else (0.0, 1.0, 0.0)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def ease5(u):
    u = max(0.0, min(1.0, u))
    return u * u * u * (u * (u * 6 - 15) + 10)


def _mix(a, b, t):
    if isinstance(a, (int, float)):
        return a + (b - a) * t
    return lerp(a, b, t)


def _scale(a, k):
    return a * k if isinstance(a, (int, float)) else mul(a, k)


def _plus(a, b):
    return a + b if isinstance(a, (int, float)) else add(a, b)


def _minus(a, b):
    return a - b if isinstance(a, (int, float)) else sub(a, b)


def _value(v, f):
    v = v(f) if callable(v) else v
    return float(v) if isinstance(v, (int, float)) else _v(v)


# ------------------------------------------------------------------ tracks
@dataclass
class Track:
    """Keys (frame, value) with one interpolation mode; see module doc."""
    keys: list
    mode: str = "ease"

    def __post_init__(self):
        if not self.keys:
            raise ValueError("A track needs at least one key.")
        self.keys = sorted(((float(f), v) for f, v in self.keys), key=lambda k: k[0])
        if any(a[0] == b[0] for a, b in zip(self.keys, self.keys[1:])):
            raise ValueError("Track keys need distinct frames.")
        if self.mode not in {"carry", "ease", "linear"}:
            raise ValueError(f"Unknown track mode {self.mode!r}")

    @classmethod
    def of(cls, value, mode=None):
        """Coerce a constant, callable or Track into a Track."""
        if isinstance(value, Track):
            return value
        return cls([(0, value)], mode or "ease")

    def __call__(self, f):
        keys = self.keys
        if len(keys) == 1 or f <= keys[0][0]:
            return _value(keys[0][1], f)
        if f >= keys[-1][0]:
            return _value(keys[-1][1], f)
        i = max(j for j in range(len(keys) - 1) if keys[j][0] <= f)
        (f0, v0), (f1, v1) = keys[i], keys[i + 1]
        u = (f - f0) / (f1 - f0)
        a, b = _value(v0, f), _value(v1, f)
        if self.mode == "linear":
            return _mix(a, b, u)
        if self.mode == "ease":
            return _mix(a, b, ease5(u))
        # carry: cubic Hermite with Catmull-Rom tangents in value per frame.
        def tangent(j):
            if j == 0 or j == len(keys) - 1:
                return None                      # eased endpoint, zero velocity
            fp, vp = keys[j - 1]
            fn, vn = keys[j + 1]
            return _scale(_minus(_value(vn, f), _value(vp, f)), 1 / (fn - fp))
        d = f1 - f0
        m0, m1 = tangent(i), tangent(i + 1)
        zero = _scale(a, 0)
        m0 = zero if m0 is None else _scale(m0, d)
        m1 = zero if m1 is None else _scale(m1, d)
        h00 = 2 * u ** 3 - 3 * u ** 2 + 1
        h10 = u ** 3 - 2 * u ** 2 + u
        h01 = -2 * u ** 3 + 3 * u ** 2
        h11 = u ** 3 - u ** 2
        if m0 == zero and m1 == zero:
            s = ease5(u)                         # a single eased segment: no overshoot
            return _mix(a, b, s)
        return _plus(_plus(_scale(a, h00), _scale(m0, h10)), _plus(_scale(b, h01), _scale(m1, h11)))


def handoff(a, b, start, end, mode="ease"):
    """Attention moves from a to b between start and end; a/b may be callables."""
    return Track([(start, a), (end, b)], mode)


def lead(subject, frames=6.0, max_m=None):
    """Aim ahead of a moving subject by `frames` of its current velocity."""
    def at(f):
        p, q, r = _value(subject, f - 1), _value(subject, f), _value(subject, f + 1)
        v = mul(sub(r, p), .5 * frames)
        if max_m is not None and length(v) > max_m:
            v = mul(norm(v), max_m)
        return add(q, v)
    return at


def damped(fn, f0, f1, settle_frames=8.0):
    """Critically damped follow of fn over [f0, f1]; deterministic and cached."""
    w = 2 * math.pi / max(1e-6, settle_frames * 1.1)
    cache, steps = {}, 4
    pos, vel = _value(fn, f0), None
    vel = _scale(pos, 0)
    cache[int(f0)] = pos
    for f in range(int(f0) + 1, int(f1) + 1):
        target = _value(fn, f)
        for _ in range(steps):
            acc = _minus(_scale(_minus(target, pos), w * w), _scale(vel, 2 * w))
            vel = _plus(vel, _scale(acc, 1 / steps))
            pos = _plus(pos, _scale(vel, 1 / steps))
        cache[f] = pos

    def at(f):
        fi = int(math.floor(f))
        fi = max(int(f0), min(int(f1), fi))
        if fi + 1 in cache and f > fi:
            return _mix(cache[fi], cache[fi + 1], f - fi)
        return cache[fi]
    return at


def creep(pos, aim, f0, rate=.0015):
    """A slow push toward aim from frame f0 (V1.1 rests at about 0.15 % per frame)."""
    def at(f):
        p, a = _value(pos, f), _value(aim, f)
        return add(a, mul(sub(p, a), (1 - rate) ** max(0.0, f - f0)))
    return at


# ------------------------------------------------------------------ shots
@dataclass
class CameraState:
    frame: float
    pos: tuple
    aim: tuple
    focus: tuple
    lens: float
    roll: float
    fstop: float
    shot: int
    cut: bool
    up: tuple = (0.0, 0.0, 1.0)

    def basis(self):
        fwd = norm(sub(self.aim, self.pos))
        right = cross(fwd, self.up)
        if length(right) < 1e-6:
            right = cross(fwd, (0.0, 1.0, 0.0))
        right = norm(right)
        up = cross(right, fwd)
        if self.roll:
            c, s = math.cos(self.roll), math.sin(self.roll)
            right, up = add(mul(right, c), mul(up, s)), add(mul(up, c), mul(right, -s))
        return right, up, fwd

    def focus_distance(self):
        return max(.05, dot(sub(self.focus, self.pos), self.basis()[2]))


@dataclass
class Shot:
    """Frames [f0, f1] inclusive. Tracks may be Tracks, callables or constants."""
    f0: int
    f1: int
    pos: object
    aim: object
    focus: object = None
    lens: object = 26.0
    roll: object = 0.0
    fstop: object = 2.8
    name: str = ""
    up: tuple = (0.0, 0.0, 1.0)

    def __post_init__(self):
        if self.f1 < self.f0:
            raise ValueError("A shot needs f1 >= f0.")
        self.pos = self.pos if isinstance(self.pos, Track) else Track.of(self.pos, "carry")
        self.aim = Track.of(self.aim)
        self.focus = self.aim if self.focus is None else Track.of(self.focus)
        self.lens = Track.of(self.lens)
        self.roll = Track.of(self.roll)
        self.fstop = Track.of(self.fstop)


@dataclass
class CameraProgram:
    shots: list = field(default_factory=list)

    def __post_init__(self):
        self.shots = sorted(self.shots, key=lambda s: s.f0)
        for a, b in zip(self.shots, self.shots[1:]):
            if b.f0 != a.f1 + 1:
                raise ValueError(f"Shots must tile the timeline: {a.name or a.f0} ends {a.f1}, next starts {b.f0}.")

    @property
    def frames(self):
        return range(self.shots[0].f0, self.shots[-1].f1 + 1)

    @property
    def cuts(self):
        """Blender (one-based) destination frames of the hard cuts."""
        return [s.f0 for s in self.shots[1:]]

    def shot_at(self, f):
        for i, s in enumerate(self.shots):
            if s.f0 <= f <= s.f1:
                return i, s
        raise ValueError(f"Frame {f} is outside the program.")

    def evaluate(self, f):
        i, s = self.shot_at(f)
        lens = s.lens(f)
        if lens <= 0:
            raise ValueError("Lens must stay positive.")
        return CameraState(f, s.pos(f), s.aim(f), s.focus(f), lens, s.roll(f), s.fstop(f), i,
                           f == s.f0 and i > 0, s.up)


# ------------------------------------------------------------------ projection and planning
def project(state, point, aspect=ASPECT, sensor_h=SENSOR_H):
    """World point -> (x, y) in frame fractions (0,0 top-left) and depth; None behind the lens."""
    right, up, fwd = state.basis()
    d = sub(point, state.pos)
    z = dot(d, fwd)
    if z <= 1e-6:
        return None
    half_h = sensor_h / 2 / state.lens
    half_w = half_h * aspect
    return (.5 + dot(d, right) / z / half_w * .5, .5 - dot(d, up) / z / half_h * .5, z)


def matched_distance(radius_a, dist_a, lens_a, radius_b, lens_b):
    """Distance for shot B so a circle of radius_b matches radius_a's screen size."""
    if min(radius_a, dist_a, lens_a, radius_b, lens_b) <= 0:
        raise ValueError("Match inputs must be positive.")
    return radius_b * dist_a * lens_b / (radius_a * lens_a)


def match_error(state_a, center_a, radius_a, state_b, center_b, radius_b):
    """Screen-centre offset and size ratio of two circles facing their cameras."""
    pa, pb = project(state_a, center_a), project(state_b, center_b)
    if pa is None or pb is None:
        return None
    ha = SENSOR_H / 2 / state_a.lens
    hb = SENSOR_H / 2 / state_b.lens
    size_a = radius_a / pa[2] / ha
    size_b = radius_b / pb[2] / hb
    return {"centre_offset": math.hypot(pa[0] - pb[0], pa[1] - pb[1]), "size_ratio": size_b / size_a}


def occluded(cam_pos, target, occluder, radius, lens=26.0, margin=0.0):
    """True when a vertical cylinder (centre, radius) blocks the line to target."""
    d = sub(target, cam_pos)
    o = sub(occluder, cam_pos)
    dh, oh = (d[0], d[1]), (o[0], o[1])
    lt = math.hypot(*dh)
    t = (oh[0] * dh[0] + oh[1] * dh[1]) / max(1e-9, lt * lt)
    if not 0 < t < 1:
        return False
    perp = abs(oh[0] * dh[1] - oh[1] * dh[0]) / max(1e-9, lt)
    return perp < radius + margin


def parallax_reveal(start_pos, target, occluder, radius, direction, lens=26.0, margin_frac=.08,
                    max_m=3.0):
    """Shortest truck along `direction` that moves a foreground cylinder out of
    the frame while aiming at target. Returns (end_pos, metres)."""
    direction = norm(direction)
    half_w = math.atan(SENSOR_H * ASPECT / 2 / lens)

    def clear(s):
        p = add(start_pos, mul(direction, s))
        state = CameraState(0, p, target, target, lens, 0.0, 2.8, 0, False)
        q = project(state, occluder)
        if q is None:
            return True
        ang = math.atan(radius / max(1e-6, q[2]))
        x = (q[0] - .5) * 2 * math.tan(half_w)            # tangent units
        edge = abs(math.atan(x)) - ang
        return edge > half_w * (1 + margin_frac)

    if clear(0):
        return _v(start_pos), 0.0
    # Scan forward: clearance is not monotonic (a long truck can bring it back).
    step, lo = .005, 0.0
    while lo < max_m and not clear(lo + step):
        lo += step
    if lo >= max_m:
        raise ValueError("The occluder does not clear the frame within max_m.")
    hi = lo + step
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if clear(mid) else (mid, hi)
    return add(start_pos, mul(direction, hi)), hi


def screen_speed(program, width=1080, height=1920):
    """Per-frame screen motion (px at width x height) of the previous aim point.

    Combines rotation and translation at the subject's depth. Cut frames are
    excluded. A pre-render diagnostic only; measure the render with
    ricks_metrics_gate.py --cam-velocity for the gate result.
    """
    out, prev = [], None
    for f in program.frames:
        s = program.evaluate(f)
        if prev is not None and not s.cut:
            a = project(prev, prev.aim)
            b = project(s, prev.aim)
            if a and b:
                out.append((f, math.hypot((b[0] - a[0]) * width, (b[1] - a[1]) * height)))
        prev = s
    return out


def settle_frame(program, shot_index, threshold_px=2.0, width=1080, height=1920):
    """First frame after which the shot stays below threshold_px per frame."""
    shot = program.shots[shot_index]
    speeds = [(f, v) for f, v in screen_speed(program, width, height) if shot.f0 < f <= shot.f1]
    settled = None
    for f, v in speeds:
        if v >= threshold_px:
            settled = None
        elif settled is None:
            settled = f
    return settled


# ------------------------------------------------------------------ Blender
def key_camera(camera, state, frame, focus_object=None, previous=None):
    """Set and key one frame. Returns the quaternion for sign continuity.

    With focus_object (e.g. the kit's portrait focus empty) the empty is moved
    to state.focus and keyed; otherwise dof.focus_distance is keyed.
    """
    from mathutils import Matrix, Vector
    right, up, fwd = (Vector(v) for v in state.basis())
    q = Matrix((right, up, -fwd)).transposed().to_quaternion()
    if previous is not None and previous.dot(q) < 0:
        q.negate()
    camera.rotation_mode = "QUATERNION"
    camera.location = state.pos
    camera.rotation_quaternion = q
    camera.data.lens = state.lens
    camera.data.dof.aperture_fstop = state.fstop
    camera.keyframe_insert("location", frame=frame)
    camera.keyframe_insert("rotation_quaternion", frame=frame)
    camera.data.keyframe_insert("lens", frame=frame)
    camera.data.keyframe_insert("dof.aperture_fstop", frame=frame)
    if focus_object is not None:
        camera.data.dof.focus_object = focus_object
        focus_object.location = state.focus
        focus_object.keyframe_insert("location", frame=frame)
    else:
        camera.data.dof.focus_object = None
        camera.data.dof.focus_distance = state.focus_distance()
        camera.data.keyframe_insert("dof.focus_distance", frame=frame)
    return q


def bake(camera, program, focus_object=None):
    """Key every program frame, then set linear interpolation on the keys."""
    q = None
    for f in program.frames:
        q = key_camera(camera, program.evaluate(f), f, focus_object, q)
    blocks = [camera, camera.data] + ([focus_object] if focus_object is not None else [])
    for block in blocks:
        ad = block.animation_data
        if ad and ad.action:
            for curve in ad.action.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = "LINEAR"
    return program.cuts
