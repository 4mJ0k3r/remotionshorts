"""Dog-in-skull hump loop: layered affine warp animation of the reference art.

Native art 308x352. Parts are RGBA sprites cut with anti-aliased polygons;
base plate is the art with all parts inpainted out. Each frame applies
per-part affine transforms (pivot rotation/scale + translation) driven by an
asymmetric thrust phase, then composites back over the base plate.

Usage: python animate_dog_skull.py preview|render
"""
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "dog_skull"
REF = OUT / "reference.png"
NW, NH = 308, 352
SCALE = 1080 / NH            # fit height on the 1080x1080 square canvas
AW, AH = round(NW * SCALE), round(NH * SCALE)   # 945 x 1080 artwork layer
FPS, NFRAMES = 30, 165
STEADY_PERIOD, TURBO_PERIOD = 7.5, 4.5

# ---------------- part polygons (native pixels) ----------------
POLYS = {
    "brain": [(138, 96), (148, 88), (164, 83), (182, 82), (200, 86), (212, 90),
              (220, 86), (236, 84), (250, 90), (258, 100), (262, 114), (258, 130),
              (248, 142), (232, 150), (212, 154), (190, 157), (168, 155), (150, 149),
              (140, 139), (135, 124), (135, 108)],
    "torso": [(130, 24), (150, 20), (172, 24), (196, 32), (216, 44), (230, 56),
              (240, 68), (244, 80), (240, 92), (230, 98), (218, 94), (208, 86),
              (196, 80), (180, 74), (162, 68), (146, 62), (134, 54), (130, 44), (132, 34)],
    "head": [(80, 30), (84, 22), (96, 18), (110, 20), (122, 24), (128, 32),
             (128, 44), (122, 52), (112, 58), (104, 64), (96, 70), (88, 70),
             (82, 64), (80, 56), (84, 50), (80, 42)],
    "ear": [(122, 24), (132, 22), (140, 26), (143, 36), (140, 48), (134, 56),
            (128, 54), (126, 44), (124, 34)],
    "frontleg": [(134, 50), (148, 54), (162, 62), (174, 72), (182, 82), (184, 90),
                 (176, 94), (166, 88), (156, 78), (144, 68), (136, 62)],
    "hindleg": [(222, 66), (236, 70), (246, 78), (252, 88), (254, 100), (250, 112),
                (248, 126), (252, 142), (254, 154), (248, 164), (240, 166), (236, 156),
                (238, 140), (240, 124), (238, 108), (232, 96), (224, 88), (218, 78)],
    "tail": [(248, 82), (260, 84), (268, 94), (272, 110), (270, 128), (266, 146),
             (260, 158), (254, 158), (254, 142), (256, 124), (254, 106), (248, 94)],
}
ORDER = ["tail", "hindleg", "brain", "torso", "frontleg", "head", "ear"]
PIVOTS = {  # native pixels
    "brain": (198, 120), "torso": (170, 55), "head": (128, 40), "ear": (128, 26),
    "frontleg": (176, 86), "hindleg": (248, 158), "tail": (252, 86),
}


def build_parts():
    art = np.array(Image.open(REF).convert("RGB"))
    parts, union = {}, np.zeros((NH, NW), np.uint8)
    for name, poly in POLYS.items():
        m = np.zeros((NH * 4, NW * 4), np.uint8)
        cv2.fillPoly(m, [(np.array(poly) * 4).astype(np.int32)], 255)
        m = cv2.resize(m, (NW, NH), interpolation=cv2.INTER_AREA)
        if name == "brain":
            m = cv2.dilate(m, np.ones((5, 5), np.uint8))
        parts[name] = m.astype(np.float32) / 255.0
        union = np.maximum(union, (m > 40).astype(np.uint8) * 255)
    union = cv2.dilate(union, np.ones((7, 7), np.uint8))
    base = cv2.inpaint(art, union, 5, cv2.INPAINT_TELEA)
    # pink blurred backing under the brain so squash edges never reveal dark cavity
    ghost = cv2.GaussianBlur(art, (9, 9), 0).astype(np.float32)
    bm = parts["brain"][..., None]
    base = (base.astype(np.float32) * (1 - bm) + ghost * bm).astype(np.uint8)
    return art, base, parts, union


def scale_up(img, is_mask=False):
    interp = cv2.INTER_LINEAR if is_mask else cv2.INTER_LANCZOS4
    return cv2.resize(img, (AW, AH), interpolation=interp)


def affine(pivot, angle_deg, sx, sy, dx, dy):
    """Affine matrix: scale+rotate about pivot (native), then translate (output px)."""
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    px, py = pivot[0] * SCALE, pivot[1] * SCALE
    m = np.array([[ca * sx, -sa * sy, 0], [sa * sx, ca * sy, 0]], dtype=np.float64)
    m[0, 2] = px - (m[0, 0] * px + m[0, 1] * py) + dx
    m[1, 2] = py - (m[1, 0] * px + m[1, 1] * py) + dy
    return m.astype(np.float32)


def warp(sprite, m):
    return cv2.warpAffine(sprite, m, (AW, AH), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def composite(canvas, rgb, alpha):
    a = alpha[..., None]
    return canvas * (1 - a) + rgb.astype(np.float32) * a


def phase_at(f):
    """Continuous thrust phase; steady 7.5f period, turbo 4.5f from f121."""
    if f <= 120:
        total = (f - 1) / STEADY_PERIOD
    else:
        total = 120 / STEADY_PERIOD + (f - 120) / TURBO_PERIOD
    return total


def thrust_of(f):
    u = phase_at(f) % 1.0
    return math.sin(math.pi * (u ** 0.65)), u


class Animator:
    def __init__(self):
        art, base, parts, union = build_parts()
        self.art = art
        self.base = scale_up(base).astype(np.float32)
        self.parts = {k: (scale_up(art), scale_up(v, True)) for k, v in parts.items()}
        # pre-scale part RGB once (same source for all parts)
        self.art_up = scale_up(art).astype(np.float32)
        self.alpha_up = {k: scale_up(v, True) for k, v in parts.items()}
        self.bg = tuple(int(c) for c in np.median(
            art[:40, :40].reshape(-1, 3), axis=0))

    def frame(self, f):
        t, u = thrust_of(f)
        # 2-frame-lagged thrust for the ears, 1-frame lag for the tail
        lag = 2.0 / (STEADY_PERIOD if f <= 120 else TURBO_PERIOD)
        t_lag = math.sin(math.pi * (((phase_at(f) - lag) % 1.0) ** 0.65))
        t_tail = math.sin(math.pi * (((phase_at(f) - lag / 2) % 1.0) ** 0.65))
        jelly = math.sin(4 * math.pi * u) * math.exp(-3 * u)
        contact = 1.0 if 0.25 <= u <= 0.55 else 0.0
        sq = t * (0.6 + 0.4 * contact)
        canvas = self.base.copy()
        M = {
            "tail": affine(PIVOTS["tail"], 8.0 * (t_tail - 0.5) * 2, 1, 1, 0, 0),
            "hindleg": affine(PIVOTS["hindleg"], -6.0 * t, 1, 1, 0, 0),
            "brain": affine(PIVOTS["brain"], 2.0 * jelly,
                            1 - 0.06 * sq + 0.02 * jelly, 1 + 0.05 * sq,
                            -5 * sq - 18 * t * 0.15, 3 * sq),
            "torso": affine(PIVOTS["torso"], 6.0 * t, 1, 1 + 0.05 * t, -18 * t, 14 * t),
            "frontleg": affine(PIVOTS["frontleg"], -3.0 * t, 1 - 0.04 * sq, 1 + 0.03 * sq,
                               -5 * sq - 6 * t, 3 * sq - 3 * t),
            "head": affine(PIVOTS["head"], -3.0 * t, 1, 1, -6 * t, -6 * t),
            "ear": affine(PIVOTS["ear"], 14.0 * (t_lag - 0.4), 1, 1 + 0.08 * t_lag,
                          -6 * t, -6 * t),
        }
        for name in ORDER:
            m = M[name]
            a = warp(self.alpha_up[name], m)
            rgb = warp(self.art_up, m)
            canvas = composite(canvas, rgb, a)
        img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        # panting tongue at the muzzle (native 86,63), follows the head bob
        if t > 0.15:
            hx, hy = 83 * SCALE - 6 * t, 66 * SCALE - 6 * t
            ln = (2.0 + 2.5 * t) * SCALE
            w = 2.0 * SCALE
            d.polygon([(hx, hy), (hx + w, hy - 1), (hx + w * 0.4, hy + ln),
                       (hx - w * 0.4, hy + ln * 0.9)], fill=(198, 91, 78))
        # vintage impact ticks at hip-brain contact during peak window
        if 0.30 <= u <= 0.45:
            cx = 212 * SCALE - 18 * t
            cy = 100 * SCALE + 14 * t
            fade = 1.0 - abs(u - 0.375) / 0.075
            col = tuple(int(c + (255 - c) * 0.3) for c in (232, 200, 75))
            for ang in (-75, -35, 5):
                r = math.radians(ang)
                r0, r1 = 10 * SCALE, 22 * SCALE
                d.line([(cx + r0 * math.cos(r), cy + r0 * math.sin(r)),
                        (cx + r1 * math.cos(r), cy + r1 * math.sin(r))],
                       fill=col, width=max(2, round(1.2 * SCALE * fade)))
        return img

    def canvas(self, f, vertical=False):
        img = self.frame(f)
        w, h = (1080, 1920) if vertical else (1080, 1080)
        c = Image.new("RGB", (w, h), self.bg)
        c.paste(img, ((w - AW) // 2, (h - AH) // 2))
        return c


def preview():
    an = Animator()
    Image.fromarray(an.base.astype(np.uint8)).save(OUT / "preview_base.png")
    tint = np.array(Image.open(REF).convert("L").convert("RGB"), dtype=np.float32) * 0.5
    colors = {"brain": (255, 60, 60), "torso": (60, 255, 60), "head": (60, 120, 255),
              "ear": (255, 0, 255), "frontleg": (0, 255, 255), "hindleg": (255, 160, 0),
              "tail": (255, 255, 0)}
    for name, poly in POLYS.items():
        m = np.zeros((NH, NW), np.uint8)
        cv2.fillPoly(m, [np.array(poly, np.int32)], 255).astype(bool)
        for c in range(3):
            tint[..., c] = np.where(m > 0, tint[..., c] * 0.4 + colors[name][c] * 0.6, tint[..., c])
    Image.fromarray(tint.astype(np.uint8)).resize((AW, AH)).save(OUT / "preview_parts.png")
    strip = Image.new("RGB", (AW * 2, AH), (0, 0, 0))
    strip.paste(an.frame(1), (0, 0))
    strip.paste(an.frame(4), (AW, 0))
    strip.save(OUT / "preview_motion.png")
    print("previews written")


def render():
    an = Animator()
    fs = OUT / "frames"
    fv = OUT / "frames_vertical"
    fs.mkdir(exist_ok=True)
    fv.mkdir(exist_ok=True)
    for f in range(1, NFRAMES + 1):
        an.canvas(f).save(fs / f"f{f:04d}.png")
        an.canvas(f, vertical=True).save(fv / f"f{f:04d}.png")
        if f % 30 == 0:
            print(f"frame {f}/{NFRAMES}", flush=True)
    # 6-frame calibration strip
    picks = [(1, "1 wind-up"), (3, "2 mid-thrust"), (4, "3 peak+squash"),
             (5, "4 rebound"), (7, "5 recoil"), (140, "6 turbo f140")]
    tw, th = 540, 540
    strip = Image.new("RGB", (tw * 6, th + 46), (16, 24, 32))
    d = ImageDraw.Draw(strip)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    except Exception:
        font = ImageFont.load_default()
    for i, (f, label) in enumerate(picks):
        strip.paste(an.canvas(f).resize((tw, th), Image.LANCZOS), (i * tw, 46))
        d.text((i * tw + 14, 10), label, fill=(232, 200, 75), font=font)
    strip.save(OUT / "dog_hump_calibration_strip.jpg", quality=92)
    print("strip + frames done")


if __name__ == "__main__":
    (preview if len(sys.argv) > 1 and sys.argv[1] == "preview" else render)()
