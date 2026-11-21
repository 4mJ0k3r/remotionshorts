"""Generate the poop_city cel cast as PIL sprites plus a placement manifest.

Every expression is a separate image so Blender can keyframe child pose planes
with CONSTANT scale swaps. Runtime texture assignment is never used (it freezes
during video renders). Face parts are anchored in head-art pixels; the Blender
build converts them through the card's world size.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import cel

OUT = Path(__file__).resolve().parents[2] / "renders" / "poop_city" / "sprites"
SS = cel.SS
K = cel.OUT_SCALE
INK = (23, 7, 9)  # #170709 deep espresso unified marker ink

CAST = {
    "sperm": dict(
        card=(1024, 1024), kind="head", center=(512, 512), rx=340, ry=298,
        lit=(246, 245, 241), base=(226, 223, 215), shade=(182, 178, 170),
        tint=None, seed=0.4,
        eye_dx=138, eye_y=468, eye_rx=96, eye_ry=112, pupil=42,
        brow_y=340, brow_len=150, brow_th=34,
        mouth=(512, 668), mouth_w=158, mouth_h=116,
        spec=(392, 372, 108, 76, 0.55),
    ),
    "buff": dict(
        card=(1024, 1024), kind="head", center=(512, 548), rx=298, ry=322,
        lit=(166, 108, 56), base=(135, 85, 42), shade=(107, 65, 30),
        tint=None, seed=1.7,
        eye_dx=126, eye_y=506, eye_rx=82, eye_ry=94, pupil=37,
        brow_y=386, brow_len=156, brow_th=44,
        mouth=(512, 700), mouth_w=168, mouth_h=108,
        spec=(404, 416, 92, 62, 0.30),
    ),
    "potato": dict(
        card=(1024, 1280), kind="body", center=(512, 620), rx=300, ry=470,
        lit=(176, 120, 60), base=(142, 94, 47), shade=(107, 65, 30),
        tint=None, seed=2.9,
        eye_dx=118, eye_y=478, eye_rx=78, eye_ry=94, pupil=35,
        brow_y=366, brow_len=128, brow_th=30,
        mouth=(512, 646), mouth_w=138, mouth_h=96,
        spec=(400, 380, 86, 120, 0.26),
    ),
    "swirl": dict(
        card=(1024, 1280), kind="body", center=(512, 700), rx=330, ry=430,
        lit=(166, 108, 56), base=(135, 85, 42), shade=(107, 65, 30),
        tint=None, seed=4.3,
        eye_dx=112, eye_y=690, eye_rx=76, eye_ry=92, pupil=34,
        brow_y=596, brow_len=122, brow_th=28,
        mouth=(512, 800), mouth_w=136, mouth_h=94,
        spec=(420, 470, 70, 50, 0.34),
    ),
}

EYE_VARIANTS = ["open", "half", "squint", "closed", "wide", "sad"]
BROW_VARIANTS = ["neutral", "angry", "raised", "sad"]
MOUTH_VARIANTS = ["closed", "smile", "small", "mid", "wide", "laugh", "frown"]
BUFF_POSES = ["crossed", "flex", "point", "extend", "laugh"]
ARM_POSES = ["hips", "point", "facepalm", "welcome", "laugh"]


def egg_points(cx, cy, rx, ry, taper=0.16, tilt=0.0, seed=0.0, count=360):
    """Organic egg: one end narrower, optional tilt, static irregularity."""
    pts = []
    for i in range(count):
        a = 2 * np.pi * i / count
        r = 1 + (0.020 * np.sin(2 * a + 0.6 + seed)
                 - 0.014 * np.cos(3 * a - 0.8 + seed)
                 + 0.007 * np.sin(5 * a + 1.9 + seed))
        k = 1 - taper * np.cos(a)
        x = rx * r * k * np.cos(a)
        y = ry * r * (1 - 0.06 * np.cos(a)) * np.sin(a)
        if tilt:
            x, y = x * np.cos(tilt) - y * np.sin(tilt), x * np.sin(tilt) + y * np.cos(tilt)
        pts.append((cx + x, cy + y))
    return pts


def potato_points(cx, cy, rx, ry, seed=0.0, count=420):
    """Bumpy peanut capsule with a slight waist and static craters."""
    pts = []
    for i in range(count):
        a = 2 * np.pi * i / count
        waist = 1 - 0.10 * np.exp(-((np.sin(a)) ** 2) * 6)
        bump = 1 + 0.012 * np.sin(7 * a + seed) + 0.008 * np.sin(11 * a + 2.1)
        rr = (1 + 0.008 * np.sin(3 * a + seed) - 0.006 * np.cos(5 * a))
        pts.append((cx + rx * waist * bump * rr * np.cos(a),
                    cy + ry * bump * rr * np.sin(a)))
    return pts


def outer_contour(mask):
    """Moore-neighbor trace of a connected mask: one closed polygon, design px."""
    m = np.asarray(mask) > 127
    h, w = m.shape
    ys, xs = np.nonzero(m)
    y0 = int(ys.min())
    x0 = int(xs[ys == y0].min())
    dirs = [(0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1)]
    start = (y0, x0)
    cur, b = start, (y0, x0 - 1)
    loop = [start]
    for _ in range(4 * int(m.sum()) + 100):
        bi = next(i for i in range(8)
                  if (cur[0] + dirs[i][0], cur[1] + dirs[i][1]) == b)
        nxt = None
        for k in range(1, 9):
            i = (bi + k) % 8
            p = (cur[0] + dirs[i][0], cur[1] + dirs[i][1])
            if 0 <= p[0] < h and 0 <= p[1] < w and m[p]:
                nxt = p
                j = (i - 1) % 8
                b = (cur[0] + dirs[j][0], cur[1] + dirs[j][1])
                break
        if nxt is None:
            break
        cur = nxt
        if cur == start:
            break
        loop.append(cur)
    pts = [(x / SS, y / SS) for y, x in loop]
    if len(pts) > 560:
        step = len(pts) / 560
        pts = [pts[int(i * step)] for i in range(560)]
    return pts


def swirl_shape(d, s, cx, cy, rx, ry):
    """Three stacked coil ellipses plus a curled peak, drawn as one union."""
    tiers = [(0.50, 0.88, 0.34), (-0.02, 0.70, 0.32), (-0.46, 0.52, 0.26)]
    for ty, trx, try_ in tiers:
        oy = cy + ry * ty
        d.ellipse([(cx - rx * trx) * s, (oy - ry * try_) * s,
                   (cx + rx * trx) * s, (oy + ry * try_) * s], fill=255)
    top_y = cy - ry * 0.46
    tip = [(cx - rx * 0.30, top_y - ry * 0.10),
           (cx - rx * 0.26, top_y - ry * 0.34),
           (cx - rx * 0.02, top_y - ry * 0.50),
           (cx + rx * 0.24, top_y - ry * 0.44),
           (cx + rx * 0.30, top_y - ry * 0.26),
           (cx + rx * 0.14, top_y - ry * 0.16),
           (cx + rx * 0.26, top_y - ry * 0.02)]
    d.polygon(cel.pts_scaled(tip, s), fill=255)


def buff_body_points(cx, cy, w, h):
    """Bodybuilder: thick neck, rounded deltoids, broad chest, tapered waist."""
    return [
        (cx - w * 0.14, cy - h * 0.62), (cx + w * 0.14, cy - h * 0.62),
        (cx + w * 0.30, cy - h * 0.50), (cx + w * 0.50, cy - h * 0.36),
        (cx + w * 0.52, cy - h * 0.16), (cx + w * 0.42, cy + h * 0.04),
        (cx + w * 0.30, cy + h * 0.30), (cx + w * 0.18, cy + h * 0.50),
        (cx - w * 0.18, cy + h * 0.50), (cx - w * 0.30, cy + h * 0.30),
        (cx - w * 0.42, cy + h * 0.04), (cx - w * 0.52, cy - h * 0.16),
        (cx - w * 0.50, cy - h * 0.36), (cx - w * 0.30, cy - h * 0.50),
    ]


def hose(d, joints, width, color=INK, ball=0, fill=None):
    """Rubber-hose limb: rounded polyline with optional ball hand at the end.
    fill paints the interior, leaving a 14px(@1536) ink outline."""
    pts = [(x * SS, y * SS) for x, y in joints]
    d.line(pts, fill=color, width=int(width * SS), joint="curve")
    r = width * SS / 2
    for (x, y) in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)
    if ball:
        x, y = pts[-1]
        br = ball * SS / 2
        d.ellipse([x - br, y - br, x + br, y + br], fill=color)
    if fill:
        iw = max(width - 18.7, 6)
        d.line(pts, fill=fill, width=int(iw * SS), joint="curve")
        ir = iw * SS / 2
        for (x, y) in pts:
            d.ellipse([x - ir, y - ir, x + ir, y + ir], fill=fill)
        if ball:
            x, y = pts[-1]
            br = max(ball - 18.7, 6) * SS / 2
            d.ellipse([x - br, y - br, x + br, y + br], fill=fill)


def muscle_hose(d, joints, peak, wrist, fill, ball=0):
    """Curved bulging limb: bicep peak tapering to wrist, stamped circles."""
    path = []
    for i in range(len(joints) - 1):
        p, q = joints[i], joints[i + 1]
        for j in range(64):
            u = j / 64
            path.append((p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u, i, u))
    path.append((joints[-1][0], joints[-1][1], len(joints) - 2, 1.0))

    def radius(seg, u):
        if seg == 0:
            return (wrist + (peak - wrist) * (0.45 + 0.55 * math.sin(math.pi * u) ** 0.9)) / 2
        return (peak * 0.80 + (wrist - peak * 0.80) * u) / 2

    for pass_r, col in ((0, INK), (9.333, fill)):
        for (x, y, seg, u) in path:
            r = max(radius(seg, u) - pass_r, 2) * SS
            d.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=col)
        if ball:
            x, y = joints[-1]
            br = max(ball / 2 - pass_r, 2) * SS
            d.ellipse([x * SS - br, y * SS - br, x * SS + br, y * SS + br], fill=col)


def shade_crescent(img, mask, color, alpha, dx, dy):
    """Soft directional shading band clipped inside the cel paint."""
    inner = np.asarray(mask) > 127
    im = Image.fromarray((inner * 255).astype(np.uint8))
    sh = Image.new("L", im.size, 0)
    sh.paste(im, (int(dx * im.size[0] * SS), int(dy * im.size[1] * SS)))
    band = np.asarray(im, dtype=np.int16) - np.asarray(sh, dtype=np.int16)
    cr = np.asarray(Image.fromarray(band.clip(0, 255).astype(np.uint8))
                    .filter(ImageFilter.GaussianBlur(2 * SS)), dtype=np.float64) / 255.0
    cr = cr * inner
    lay = np.zeros((*cr.shape, 4), dtype=np.uint8)
    lay[..., :3] = color
    lay[..., 3] = (cr * alpha * 255).astype(np.uint8)
    return Image.alpha_composite(img, Image.fromarray(lay).resize(img.size, Image.LANCZOS))


def buff_arms(d, pose, cx, cy):
    """Five curved muscular arm poses: 130px(@1536) bicep peak tapering to wrist."""
    sh_l, sh_r = (cx - 400, cy - 330), (cx + 400, cy - 330)
    fill = (135, 85, 42)
    peak, wrist, ball = 86.7, 33, 70
    if pose == "crossed":
        muscle_hose(d, [sh_l, (cx - 460, cy - 100), (cx + 140, cy + 30)], peak, wrist, fill, ball)
        muscle_hose(d, [sh_r, (cx + 460, cy - 100), (cx - 140, cy + 60)], peak, wrist, fill, ball)
    elif pose == "flex":
        for sgn, sh in ((-1, sh_l), (1, sh_r)):
            elbow = (cx + sgn * 450, cy - 430)
            muscle_hose(d, [sh, elbow, (cx + sgn * 330, cy - 560)], peak, wrist, fill, ball)
    elif pose == "point":
        muscle_hose(d, [sh_l, (cx - 430, cy - 80), (cx - 160, cy + 40)], peak, wrist, fill, ball)
        hose(d, [(cx - 160, cy + 40), (cx - 260, cy + 80)], 40, ball=30, fill=fill)
        muscle_hose(d, [sh_r, (cx + 460, cy - 100), (cx + 200, cy + 120)], peak, wrist, fill, ball)
    elif pose == "extend":
        muscle_hose(d, [sh_l, (cx - 460, cy - 160), (cx - 470, cy - 40)], peak, wrist, fill, ball)
        muscle_hose(d, [sh_r, (cx - 100, cy - 260), (cx - 400, cy - 60)], peak, wrist, fill, ball)
    elif pose == "laugh":
        muscle_hose(d, [sh_l, (cx - 440, cy - 40), (cx - 160, cy + 120)], peak, wrist, fill, ball)
        muscle_hose(d, [sh_r, (cx + 440, cy - 40), (cx + 160, cy + 120)], peak, wrist, fill, ball)


def draw_card(name, cfg):
    W, H = cfg["card"]
    cx, cy = cfg["center"]
    rx, ry = cfg["rx"], cfg["ry"]

    def shape(d, s):
        if name == "sperm":
            pts = egg_points(cx, cy, rx, ry, taper=0.15, tilt=-0.14, seed=cfg["seed"])
            d.polygon(cel.pts_scaled(pts), fill=255)
        elif name == "buff":
            pts = egg_points(cx, cy, rx, ry, taper=-0.20, tilt=0.0, seed=cfg["seed"])
            d.polygon(cel.pts_scaled(pts), fill=255)
            d.polygon(cel.pts_scaled([(cx - 62, cy - ry * 0.80), (cx - 8, cy - ry * 1.14),
                                      (cx + 40, cy - ry * 0.92), (cx + 6, cy - ry * 0.70)]), fill=255)
        elif name == "potato":
            pts = potato_points(cx, cy, rx, ry, seed=cfg["seed"])
            d.polygon(cel.pts_scaled(pts), fill=255)
        else:
            m = cel.mask_from(lambda dd, s: swirl_shape(dd, s, cx, cy, rx, ry), (W, H))
            d.polygon(cel.pts_scaled(outer_contour(m)), fill=255)

    mask = cel.mask_from(shape, (W, H))
    img = cel.paint_cel(mask, cfg["base"], cfg["lit"], cfg["shade"], INK,
                        spec=cfg["spec"], tint=cfg["tint"])
    if name == "sperm":
        img = shade_crescent(img, mask, (201, 181, 184), 0.22, -0.05, -0.05)
    else:
        img = shade_crescent(img, mask, (84, 48, 22), 0.35, -0.07, 0.0)

    if name == "potato":
        inner = np.asarray(mask) > 127
        inner[:int(18 * SS), :] = False
        inner[-int(18 * SS):, :] = False
        inner[:, :int(18 * SS)] = False
        inner[:, -int(18 * SS):] = False
        details = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        dd = ImageDraw.Draw(details)
        for (sx, sy, sr) in [(400, 828, 30), (610, 900, 34), (460, 1040, 26),
                             (640, 764, 22), (356, 952, 20)]:
            dd.ellipse([(sx - sr) * SS, (sy - sr * 0.8) * SS,
                        (sx + sr) * SS, (sy + sr * 0.8) * SS], fill=(140, 114, 44, 150))
        da = np.asarray(details).copy()
        da[..., 3] = (da[..., 3].astype(np.float64) * inner).astype(np.uint8)
        img = Image.alpha_composite(img, Image.fromarray(da).resize(img.size, Image.LANCZOS))
    if name == "swirl":
        seams = Image.new("RGBA", mask.size, (0, 0, 0, 0))
        ds = ImageDraw.Draw(seams)
        for ty, trx, try_ in [(-0.02, 0.70, 0.32), (-0.46, 0.52, 0.26)]:
            oy = cy + ry * ty
            bx, by = rx * trx * 0.94, ry * try_ * 0.94
            ds.arc([(cx - bx) * SS, (oy - by) * SS, (cx + bx) * SS, (oy + by) * SS],
                   20, 160, fill=(46, 28, 12, 210), width=int(5 * SS))
            ds.arc([(cx - bx * 0.96) * SS, (oy - by + 12) * SS,
                    (cx + bx * 0.96) * SS, (oy + by + 12) * SS],
                   25, 155, fill=(255, 226, 178, 80), width=int(3 * SS))
        img = Image.alpha_composite(img, seams.resize(img.size, Image.LANCZOS))
    return img


def smooth_closed(pts, samples=24, wobble=0.010):
    """Catmull-Rom through control points, plus static low-amplitude wobble."""
    n = len(pts)
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[(i - 1) % n], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for j in range(samples):
            t = j / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            a = np.arctan2(y - cy, x - cx)
            k = 1 + wobble * np.sin(3 * a + 1.3) + wobble * 0.6 * np.sin(7 * a + 0.4)
            out.append((cx + (x - cx) * k, cy + (y - cy) * k))
    return out


def draw_buff_body(cfg, pose):
    W, H = 1024, 1280
    cx, cy = 512, 660
    pts = smooth_closed(buff_body_points(cx, cy, 880, 1080))
    mask = cel.mask_from(
        lambda d, s: d.polygon(cel.pts_scaled(pts), fill=255), (W, H))
    img = cel.paint_cel(mask, (135, 85, 42), (166, 108, 56), (107, 65, 30),
                        INK, spec=(380, 380, 120, 90, 0.22), tint=cfg["tint"])
    img = shade_crescent(img, mask, (84, 48, 22), 0.35, -0.07, 0.0)
    creases = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    dc = ImageDraw.Draw(creases)
    arcs = [([cx - 250, cy - 300, cx - 20, cy - 60], 200, 350),
            ([cx + 20, cy - 300, cx + 250, cy - 60], 190, 340)]
    for i in range(3):
        y = cy - 60 + i * 118
        arcs.append(([cx - 150, y - 46, cx - 12, y + 52], 210, 330))
        arcs.append(([cx + 12, y - 46, cx + 150, y + 52], 210, 330))
    for box, a0, a1 in arcs:
        sb = [box[0] * SS, (box[1] + 6) * SS, box[2] * SS, (box[3] + 6) * SS]
        dc.arc(sb, a0, a1, fill=(84, 48, 22, 200), width=int(8 * SS))
        dc.arc([v * SS for v in box], a0, a1, fill=INK, width=int(6 * SS))
    dc.line([(cx * SS, (cy - 250) * SS), (cx * SS, (cy + 250) * SS)],
            fill=INK, width=int(6 * SS))
    img = Image.alpha_composite(img, creases.resize(img.size, Image.LANCZOS))
    overlay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    buff_arms(ImageDraw.Draw(overlay), pose, cx, cy)
    img = Image.alpha_composite(img, overlay.resize(img.size, Image.LANCZOS))
    return img


def draw_arms(name, cfg, pose):
    """Transparent rubber-hose arm overlay aligned to the body card canvas."""
    W, H = cfg["card"]
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = cfg["center"]
    rx, ry = cfg["rx"], cfg["ry"]
    sh_l = (cx - rx * 0.72, cy - ry * 0.12)
    sh_r = (cx + rx * 0.72, cy - ry * 0.12)

    def h(joints, w, ball=0):
        hose(d, joints, w, ball=ball, fill=cfg["base"])

    if pose == "hips":
        h([sh_l, (cx - rx * 1.05, cy + ry * 0.12), (cx - rx * 0.70, cy + ry * 0.30)], 40, ball=44)
        h([sh_r, (cx + rx * 1.05, cy + ry * 0.12), (cx + rx * 0.70, cy + ry * 0.30)], 40, ball=44)
    elif pose == "point":
        h([sh_l, (cx - rx * 1.10, cy - ry * 0.02), (cx - rx * 1.40, cy + ry * 0.06)], 40, ball=44)
        h([(cx - rx * 1.40, cy + ry * 0.06), (cx - 500, cy + ry * 0.10)], 22, ball=18)
        h([sh_r, (cx + rx * 1.00, cy + ry * 0.14), (cx + rx * 0.68, cy + ry * 0.30)], 40, ball=44)
    elif pose == "facepalm":
        h([sh_r, (cx + rx * 1.00, cy - ry * 0.45), (cx + rx * 0.30, cy - ry * 0.52)], 40, ball=46)
        h([sh_l, (cx - rx * 0.95, cy + ry * 0.15), (cx - rx * 0.70, cy + ry * 0.34)], 40, ball=44)
    elif pose == "welcome":
        h([sh_l, (cx - rx * 1.15, cy - ry * 0.32), (cx - rx * 1.42, cy - ry * 0.52)], 40, ball=44)
        h([sh_r, (cx + rx * 1.15, cy - ry * 0.32), (cx + rx * 1.42, cy - ry * 0.52)], 40, ball=44)
    elif pose == "laugh":
        h([sh_l, (cx - rx * 1.00, cy + ry * 0.08), (cx - rx * 0.40, cy + ry * 0.26)], 40, ball=44)
        h([sh_r, (cx + rx * 1.00, cy + ry * 0.08), (cx + rx * 0.40, cy + ry * 0.26)], 40, ball=44)
    arr = cel.edge_dilate(np.asarray(img))
    return Image.fromarray(arr).resize((int(W * K), int(H * K)), Image.LANCZOS)


def draw_hardhat():
    W, H = 760, 420
    cx, cy = 380, 300

    def shape(d, s):
        d.polygon(cel.pts_scaled([(cx - 300, cy + 40), (cx - 250, cy - 90),
                                  (cx - 120, cy - 170), (cx + 120, cy - 170),
                                  (cx + 250, cy - 90), (cx + 300, cy + 40)]), fill=255)
        d.rounded_rectangle([ (cx - 350) * s, (cy + 20) * s, (cx + 350) * s, (cy + 96) * s],
                            radius=34 * s, fill=255)
        d.rounded_rectangle([(cx - 46) * s, (cy - 208) * s, (cx + 46) * s, (cy - 150) * s],
                            radius=20 * s, fill=255)

    mask = cel.mask_from(shape, (W, H))
    return cel.paint_cel(mask, (245, 184, 46), (255, 214, 110), (176, 124, 22),
                         INK, spec=(268, 168, 96, 44, 0.55))


def draw_sperm_hat_card(cfg):
    """Head card with the hard-hat baked in: shared ink + forehead cast shadow."""
    card = draw_card("sperm", cfg)
    cx, cy = cfg["center"]
    rx, ry = cfg["rx"], cfg["ry"]
    mask = cel.mask_from(
        lambda d, s: d.polygon(cel.pts_scaled(
            egg_points(cx, cy, rx, ry, taper=0.15, tilt=-0.14, seed=cfg["seed"])), fill=255),
        cfg["card"])
    inner = np.asarray(mask) > 127
    band = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    db = ImageDraw.Draw(band)
    db.ellipse([(512 - 300) * SS, 320 * SS, (512 + 300) * SS, 410 * SS],
               fill=(74, 53, 64, 107))
    ba = np.asarray(band).copy()
    ba[..., 3] = (ba[..., 3].astype(np.float64) * inner).astype(np.uint8)
    card = Image.alpha_composite(card, Image.fromarray(ba).resize(card.size, Image.LANCZOS))
    hat = draw_hardhat()
    card.alpha_composite(hat, (int(512 * K) - hat.width // 2, int(144 * K) - hat.height // 2))
    return card


def part_canvas(w, h):
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def finish(img, w, h):
    arr = cel.edge_dilate(np.asarray(img))
    return Image.fromarray(arr).resize((int(w * K), int(h * K)), Image.LANCZOS)


def draw_eyes(cfg, variant):
    """High-contrast eyes: warm-ivory sclera, bold pupil, colored eyelids."""
    W, H = 640, 360
    img, d = part_canvas(W, H)
    ex, ey = W // 2, H // 2
    dx = cfg["eye_dx"] * 0.78
    rx, ry = cfg["eye_rx"] * 0.78, cfg["eye_ry"] * 0.78
    sclera = (255, 248, 240)
    pupil_c = (28, 13, 14)
    lid = cfg["shade"]
    for sgn in (-1, 1):
        cx = ex + sgn * dx
        if variant == "closed":
            d.arc([(cx - rx) * SS, (ey - ry * 0.5) * SS, (cx + rx) * SS, (ey + ry * 0.7) * SS],
                  200, 340, fill=INK, width=int(11 * SS))
            continue
        if variant in ("half", "squint"):
            k = 0.5 if variant == "half" else 0.32
            rx_s, ry_s = rx * 0.95, ry * k
            d.ellipse([(cx - rx_s) * SS, (ey - ry_s) * SS, (cx + rx_s) * SS, (ey + ry_s) * SS],
                      fill=sclera, outline=INK, width=int(6 * SS))
            pr = cfg["pupil"] * 0.78 * 0.8
            d.ellipse([(cx - pr) * SS, (ey - pr * 0.8) * SS, (cx + pr) * SS, (ey + pr * 0.8) * SS],
                      fill=pupil_c)
            d.line([(cx - rx_s) * SS, (ey - ry_s) * SS, (cx + rx_s) * SS, (ey - ry_s) * SS],
                   fill=lid, width=int(10 * SS))
            continue
        k = {"open": 1.0, "wide": 1.22, "sad": 0.82}[variant]
        rx_s, ry_s = rx * 0.95 * k, ry * 0.95 * k
        py = ey + (ry * 0.10 if variant == "sad" else 0)
        d.ellipse([(cx - rx_s) * SS, (py - ry_s) * SS, (cx + rx_s) * SS, (py + ry_s) * SS],
                  fill=sclera, outline=INK, width=int(6 * SS))
        pr = cfg["pupil"] * 0.78 * k
        ppy = py + (ry_s * 0.18 if variant == "sad" else 0)
        d.ellipse([(cx - pr) * SS, (ppy - pr) * SS, (cx + pr) * SS, (ppy + pr) * SS],
                  fill=pupil_c)
        d.ellipse([(cx - pr * 0.35 - pr * 0.3) * SS, (ppy - pr * 0.55) * SS,
                   (cx - pr * 0.35 + pr * 0.1) * SS, (ppy - pr * 0.15) * SS],
                  fill=(255, 255, 255))
        d.arc([(cx - rx_s) * SS, (py - ry_s) * SS, (cx + rx_s) * SS, (py + ry_s) * SS],
              200, 340, fill=lid, width=int(9 * SS))
        d.arc([(cx - rx_s) * SS, (py - ry_s) * SS, (cx + rx_s) * SS, (py + ry_s) * SS],
              20, 160, fill=lid, width=int(5 * SS))
        if variant == "sad":
            d.line([(cx - sgn * rx * 0.9) * SS, (ey - ry * 0.72) * SS,
                    (cx + sgn * rx * 0.9) * SS, (ey - ry * 0.30) * SS],
                   fill=INK, width=int(10 * SS))
    return finish(img, W, H)


def draw_brows(cfg, variant):
    W, H = 640, 220
    img, d = part_canvas(W, H)
    ex, ey = W // 2, H // 2 + 20
    dx = cfg["eye_dx"] * 0.78
    ln = cfg["brow_len"] * 0.78
    th = cfg["brow_th"] * 0.6
    for sgn in (-1, 1):
        cx = ex + sgn * dx
        if variant == "angry":
            pts = [(cx - sgn * ln * 0.5, ey - th * 1.5), (cx + sgn * ln * 0.5, ey + th * 0.5)]
        elif variant == "raised":
            pts = [(cx - sgn * ln * 0.5, ey + th * 0.2), (cx, ey - th * 1.5),
                   (cx + sgn * ln * 0.5, ey + th * 0.2)]
        elif variant == "sad":
            pts = [(cx - sgn * ln * 0.5, ey + th * 0.9), (cx + sgn * ln * 0.5, ey - th * 0.9)]
        else:
            pts = [(cx - sgn * ln * 0.5, ey), (cx, ey - th * 0.7),
                   (cx + sgn * ln * 0.5, ey)]
        d.line([(x * SS, y * SS) for x, y in pts], fill=INK,
               width=int(th * SS), joint="curve")
    return finish(img, W, H)


def draw_mouth(cfg, variant):
    W, H = 520, 380
    img, d = part_canvas(W, H)
    cx, cy = W // 2, H // 2
    w = cfg["mouth_w"] * 0.62
    h = cfg["mouth_h"] * 0.62
    if variant == "closed":
        d.arc([(cx - w * 0.5) * SS, (cy - h * 0.34) * SS, (cx + w * 0.5) * SS, (cy + h * 0.30) * SS],
              20, 160, fill=INK, width=int(12 * SS))
    elif variant == "smile":
        d.arc([(cx - w * 0.62) * SS, (cy - h * 0.62) * SS, (cx + w * 0.62) * SS, (cy + h * 0.42) * SS],
              15, 165, fill=INK, width=int(14 * SS))
    elif variant == "frown":
        d.arc([(cx - w * 0.58) * SS, (cy - h * 0.10) * SS, (cx + w * 0.58) * SS, (cy + h * 0.78) * SS],
              200, 340, fill=INK, width=int(13 * SS))
    else:
        k = {"small": 0.34, "mid": 0.62, "wide": 0.85, "laugh": 1.06}[variant]
        ow, oh = w * 0.5 * k, h * 0.5 * k
        box = [(cx - ow) * SS, (cy - oh) * SS, (cx + ow) * SS, (cy + oh) * SS]
        d.ellipse(box, fill=(38, 8, 11, 255), outline=INK, width=int(8 * SS))
        inner = Image.new("RGBA", img.size, (0, 0, 0, 0))
        di = ImageDraw.Draw(inner)
        tw, th = ow * 0.86, oh * 0.30
        di.rounded_rectangle([(cx - tw) * SS, (cy - oh * 0.98) * SS,
                              (cx + tw) * SS, (cy - oh + th * 2) * SS],
                             radius=int(th * 0.5 * SS), fill=(255, 255, 255, 255))
        for fx in (-0.45, 0.0, 0.45):
            x = cx + tw * fx
            di.line([(x * SS, (cy - oh * 0.90) * SS), (x * SS, (cy - oh + th * 1.7) * SS)],
                    fill=(38, 8, 11, 110), width=int(3 * SS))
        di.ellipse([(cx - ow * 0.52) * SS, (cy + oh * 0.16) * SS,
                    (cx + ow * 0.52) * SS, (cy + oh * 1.04) * SS],
                   fill=(232, 74, 67, 255))
        opening = Image.new("L", img.size, 0)
        ImageDraw.Draw(opening).ellipse(box, fill=255)
        ia = np.asarray(inner).copy()
        ia[..., 3] = (ia[..., 3].astype(np.float64)
                      * (np.asarray(opening) / 255.0)).astype(np.uint8)
        img = Image.alpha_composite(img, Image.fromarray(ia))
    return finish(img, W, H)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"units": "head-art pixels, y down; anchor is the part center",
                "characters": {}}
    for name, cfg in CAST.items():
        entry = {"card_size": [int(v * K) for v in cfg["card"]], "parts": {}}
        card = draw_card(name, cfg)
        p = cel.save(card, OUT / f"{name}_card.png")
        entry["card"] = p.name
        entry["center"] = [int(v * K) for v in cfg["center"]]
        if name == "buff":
            entry["body_poses"] = {}
            for pose in BUFF_POSES:
                b = draw_buff_body(cfg, pose)
                p = cel.save(b, OUT / f"buff_body_{pose}.png")
                entry["body_poses"][pose] = dict(file=p.name, size=[int(1024 * K), int(1280 * K)])
        if name in ("potato", "swirl"):
            entry["arm_poses"] = {}
            for pose in ARM_POSES:
                a = draw_arms(name, cfg, pose)
                p = cel.save(a, OUT / f"{name}_arms_{pose}.png")
                entry["arm_poses"][pose] = dict(file=p.name,
                                                size=[int(v * K) for v in cfg["card"]],
                                                anchor=[int(v * K) for v in cfg["center"]])
        for v in EYE_VARIANTS:
            p = cel.save(draw_eyes(cfg, v), OUT / f"{name}_eyes_{v}.png")
            entry["parts"][f"eyes_{v}"] = dict(file=p.name, size=[int(640 * K), int(360 * K)],
                                               anchor=[int(cfg["center"][0] * K), int(cfg["eye_y"] * K)])
        for v in BROW_VARIANTS:
            p = cel.save(draw_brows(cfg, v), OUT / f"{name}_brows_{v}.png")
            entry["parts"][f"brows_{v}"] = dict(file=p.name, size=[int(640 * K), int(220 * K)],
                                                anchor=[int(cfg["center"][0] * K), int(cfg["brow_y"] * K)])
        for v in MOUTH_VARIANTS:
            p = cel.save(draw_mouth(cfg, v), OUT / f"{name}_mouth_{v}.png")
            entry["parts"][f"mouth_{v}"] = dict(file=p.name, size=[int(520 * K), int(380 * K)],
                                                anchor=[int(v2 * K) for v2 in cfg["mouth"]])
        if name == "sperm":
            p = cel.save(draw_hardhat(), OUT / "sperm_hardhat.png")
            entry["parts"]["hardhat"] = dict(file=p.name, size=[int(760 * K), int(420 * K)],
                                             anchor=[int(512 * K), int(144 * K)])
            hc = draw_sperm_hat_card(cfg)
            p = cel.save(hc, OUT / "sperm_card_hat.png")
            entry["card_hat"] = p.name
        manifest["characters"][name] = entry
        print(f"{name}: card + {len(entry['parts'])} parts")

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {OUT / 'manifest.json'}")

    def face(name, eyes, brows, mouth):
        cfg = CAST[name]
        img = Image.open(OUT / f"{name}_card.png").convert("RGBA")
        for part, anchor in ((f"eyes_{eyes}", (cfg["center"][0], cfg["eye_y"])),
                             (f"brows_{brows}", (cfg["center"][0], cfg["brow_y"])),
                             (f"mouth_{mouth}", cfg["mouth"])):
            p = Image.open(OUT / f"{name}_{part}.png").convert("RGBA")
            img.alpha_composite(p, (int(anchor[0] * K) - p.width // 2,
                                    int(anchor[1] * K) - p.height // 2))
        return img

    combos = [("open", "neutral", "mid"), ("closed", "neutral", "smile"),
              ("wide", "raised", "laugh"), ("half", "angry", "wide"),
              ("open", "sad", "frown")]
    cw, ch = 300, 340
    sheet = Image.new("RGB", (cw * 5, ch * 4 + 30), (24, 20, 22))
    sd = ImageDraw.Draw(sheet)
    for r, name in enumerate(CAST):
        sd.text((10, r * ch + 6), name, fill=(240, 230, 210))
        for c, (eyes, brows, mouth) in enumerate(combos):
            im = face(name, eyes, brows, mouth)
            im.thumbnail((cw - 16, ch - 26), Image.LANCZOS)
            sheet.paste(im, (c * cw + (cw - im.width) // 2,
                             r * ch + 26 + (ch - 26 - im.height) // 2), im)
            sd.text((c * cw + 8, r * ch + ch - 16), f"{eyes}/{brows}/{mouth}",
                    fill=(190, 180, 160))
    cel.save(sheet, OUT.parent / "sprite_preview.jpg")
    print(f"wrote {OUT.parent / 'sprite_preview.jpg'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())