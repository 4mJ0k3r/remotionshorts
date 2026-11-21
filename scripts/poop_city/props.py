"""Prop textures for the poop_city set: HUD pill, mini-sperm, wisps, sweat.

Runs on system Python (Blender's bundled interpreter has no PIL).
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import cel

OUT = Path(__file__).resolve().parents[2] / "renders" / "poop_city" / "sprites"
SS = cel.SS
INK = (23, 7, 9)


def font(size, bold=True):
    for name in ("arialbd.ttf" if bold else "arial.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except OSError:
            continue
    return ImageFont.load_default()


def hud_pill():
    W, H = 1024, 224
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8 * SS, 8 * SS, (W - 8) * SS, (H - 8) * SS],
                        radius=(H // 2 - 8) * SS, fill=(250, 250, 248, 255))
    f = font(int(78 * SS))
    text = "Sperm took one wrong turn"
    box = d.textbbox((0, 0), text, font=f)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text(((W * SS - tw) / 2 - box[0], (H * SS - th) / 2 - box[1]), text,
           font=f, fill=(38, 30, 32, 255))
    return cel.save(Image.fromarray(cel.edge_dilate(np.asarray(img)))
                    .resize((W, H), Image.LANCZOS), OUT / "hud_pill.png")


def mini_sperm():
    """Knocked-out mini sperm: cel-shaded head, XX eyes, wavy tail."""
    W, H = 320, 220
    cx, cy = W * 0.38, H * 0.5
    rx, ry = W * 0.26, H * 0.32
    mask = cel.mask_from(lambda d, s: d.ellipse(
        [(cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s], fill=255), (W, H))
    img = cel.paint_cel(mask, (226, 223, 215), (246, 245, 241), (182, 178, 170),
                        INK, ink_w=6, rim_w=8, rim_strength=0.4)
    big = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    pts = []
    for i in range(41):
        t = i / 40
        x = cx + rx * 0.8 + t * (W * 0.92 - cx - rx * 0.8)
        y = cy + math.sin(t * 5 * math.pi) * (H * 0.05 + H * 0.10 * t)
        pts.append((x * SS, y * SS))
    d.line(pts, fill=INK + (255,), width=int(7 * SS), joint="curve")
    d.line(pts, fill=(226, 223, 215, 255), width=int(3 * SS), joint="curve")
    for sgn in (-1, 1):
        ex = cx + sgn * rx * 0.42
        ey = cy - ry * 0.10
        r = rx * 0.17
        d.line([(ex - r) * SS, (ey - r) * SS, (ex + r) * SS, (ey + r) * SS],
               fill=INK + (255,), width=int(6 * SS))
        d.line([(ex - r) * SS, (ey + r) * SS, (ex + r) * SS, (ey - r) * SS],
               fill=INK + (255,), width=int(6 * SS))
    img = Image.alpha_composite(img, big.resize(img.size, Image.LANCZOS))
    return cel.save(img, OUT / "mini_sperm.png")


def sign():
    """Gag sign plate: EGG DEPT with up-arrow over MISSED EXIT."""
    W, H = 512, 288
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([6 * SS, 6 * SS, (W - 6) * SS, (H - 6) * SS],
                        radius=26 * SS, fill=(242, 226, 220, 255),
                        outline=INK + (255,), width=int(8 * SS))
    f1, f2 = font(int(64 * SS)), font(int(56 * SS))
    t1 = "EGG DEPT"
    box = d.textbbox((0, 0), t1, font=f1)
    tw = box[2] - box[0]
    d.text(((W * SS - tw) / 2 - box[0] - 30 * SS, 40 * SS), t1,
           font=f1, fill=INK + (255,))
    axc, ay = W * SS - 70 * SS, 90 * SS
    d.polygon([(axc, ay - 40 * SS), (axc - 26 * SS, ay), (axc - 10 * SS, ay),
               (axc - 10 * SS, ay + 40 * SS), (axc + 10 * SS, ay + 40 * SS),
               (axc + 10 * SS, ay), (axc + 26 * SS, ay)], fill=INK + (255,))
    t2 = "MISSED EXIT"
    box = d.textbbox((0, 0), t2, font=f2)
    tw = box[2] - box[0]
    d.text(((W * SS - tw) / 2 - box[0], 170 * SS), t2,
           font=f2, fill=(178, 58, 48, 255))
    return cel.save(Image.fromarray(cel.edge_dilate(np.asarray(img)))
                    .resize((W, H), Image.LANCZOS), OUT / "sign.png")


def wisps():
    """Four distinct S-curve steam wisps, soft radial alpha peaking at 0.45."""
    paths = []
    W, H = 200, 420
    for i, tag in enumerate("abcd"):
        ys, xs = np.mgrid[0:H * SS, 0:W * SS]
        t = ys / (H * SS - 1)
        phase, amp, freq = i * 1.9, 0.26 + 0.05 * i, 5.2 + 0.9 * i
        center = W * SS * 0.5 + np.sin(t * freq + phase) * W * SS * amp * (0.25 + 0.75 * t)
        half = W * SS * (0.22 + 0.05 * i) * np.sin(np.pi * np.clip(t, 0, 1)) ** 0.6 + 3
        a = np.clip(1 - np.abs(xs - center) / np.maximum(half, 1), 0, 1) ** 1.5
        a *= np.sin(np.pi * np.clip(t, 0, 1)) ** 0.6
        rgb = np.zeros((H * SS, W * SS, 4), dtype=np.uint8)
        rgb[..., 0], rgb[..., 1], rgb[..., 2] = 255, 236, 232
        rgb[..., 3] = (a * 95).astype(np.uint8)
        paths.append(cel.save(Image.fromarray(rgb).resize((W, H), Image.LANCZOS),
                              OUT / f"wisp_{tag}.png"))
    return paths


def _coil_mask(W, H, cx, cy, rx, ry, tiers):
    def shape(d, s):
        for ty, trx, try_ in tiers:
            oy = cy + ry * ty
            d.ellipse([(cx - rx * trx) * s, (oy - ry * try_) * s,
                       (cx + rx * trx) * s, (oy + ry * try_) * s], fill=255)
    return cel.mask_from(shape, (W, H))


def mounds():
    """Toon-inked coiled poop mounds in the speaking cast's cel palette."""
    paths = []
    specs = [
        ("a", 512, 512, (256, 330), 200, 170,
         [(0.45, 0.90, 0.40), (-0.10, 0.68, 0.34), (-0.55, 0.44, 0.26)]),
        ("b", 512, 448, (256, 290), 210, 150,
         [(0.40, 0.92, 0.42), (-0.20, 0.62, 0.34)]),
        ("c", 448, 512, (224, 330), 170, 180,
         [(0.45, 0.88, 0.38), (-0.05, 0.66, 0.32), (-0.50, 0.46, 0.26), (-0.85, 0.26, 0.18)]),
    ]
    for tag, W, H, c, rx, ry, tiers in specs:
        mask = _coil_mask(W, H, c[0], c[1], rx, ry, tiers)
        img = cel.paint_cel(mask, (135, 85, 42), (166, 108, 56), (107, 65, 30),
                            INK, spec=(c[0] - rx * 0.3, c[1] - ry * 0.4,
                                       rx * 0.3, ry * 0.2, 0.30))
        paths.append(cel.save(img, OUT / f"mound_{tag}.png"))
    return paths


def corn_peanut():
    paths = []
    W, H = 256, 256
    mask = cel.mask_from(lambda d, s: d.ellipse(
        [(W * 0.28) * s, (H * 0.18) * s, (W * 0.72) * s, (H * 0.82) * s], fill=255), (W, H))
    img = cel.paint_cel(mask, (240, 200, 90), (255, 226, 130), (190, 150, 50),
                        INK, spec=(W * 0.42, H * 0.34, 26, 30, 0.5))
    d = ImageDraw.Draw(img)
    k = cel.OUT_SCALE
    for gy in range(3):
        for gx in range(3):
            x = (W * 0.36 + gx * W * 0.14) * k
            y = (H * 0.30 + gy * H * 0.18) * k
            d.arc([x - 12 * k, y - 12 * k, x + 12 * k, y + 12 * k],
                  200, 340, fill=INK + (160,), width=int(3 * k))
    paths.append(cel.save(img, OUT / "corn.png"))
    mask = cel.mask_from(lambda d, s: (
        d.ellipse([(W * 0.30) * s, (H * 0.14) * s, (W * 0.70) * s, (H * 0.52) * s], fill=255),
        d.ellipse([(W * 0.30) * s, (H * 0.48) * s, (W * 0.70) * s, (H * 0.86) * s], fill=255)),
        (W, H))
    img = cel.paint_cel(mask, (214, 178, 120), (236, 204, 150), (168, 132, 80),
                        INK, spec=(W * 0.42, H * 0.28, 22, 26, 0.4))
    paths.append(cel.save(img, OUT / "peanut.png"))
    return paths


def sweat():
    W, H = 96, 140
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon(cel.pts_scaled([(48, 6), (78, 78), (48, 128), (18, 78)]), fill=(150, 210, 240, 235))
    d.ellipse([18 * SS, 62 * SS, 78 * SS, 128 * SS], fill=(150, 210, 240, 235))
    d.ellipse([30 * SS, 74 * SS, 46 * SS, 96 * SS], fill=(240, 252, 255, 220))
    return cel.save(Image.fromarray(cel.edge_dilate(np.asarray(img)))
                    .resize((W, H), Image.LANCZOS), OUT / "sweat.png")


def tail():
    W, H = 512, 128
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts_top, pts_bot = [], []
    for i in range(65):
        t = i / 64
        x = 8 + t * (W - 16)
        half = (H * 0.40) * (1 - t) ** 1.3 + 3
        pts_top.append((x, H / 2 - half))
        pts_bot.append((x, H / 2 + half))
    d.polygon(cel.pts_scaled(pts_top + pts_bot[::-1]), fill=INK + (255,))
    inner_top = [(x, y + 7) for x, y in pts_top]
    inner_bot = [(x, y - 7) for x, y in pts_bot]
    d.polygon(cel.pts_scaled(inner_top + inner_bot[::-1]), fill=(226, 223, 215, 255))
    return cel.save(Image.fromarray(cel.edge_dilate(np.asarray(img)))
                    .resize((W, H), Image.LANCZOS), OUT / "sperm_tail.png")


def overlays():
    """Full-frame 540x960 transparent plate for the compositor hook badge.
    Compositor overlays sit above all geometry and are immune to DOF blur."""
    FW, FH = 540, 960
    hud = Image.open(OUT / "hud_pill.png").convert("RGBA")
    hw = 340
    hh = round(hw * hud.height / hud.width)
    hud = hud.resize((hw, hh), Image.LANCZOS)
    plate = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    plate.alpha_composite(hud, ((FW - hw) // 2, 40))
    return [cel.save(plate, OUT / "hud_full.png")]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in (hud_pill, mini_sperm, sign, sweat, tail):
        print("wrote", fn())
    for group in (wisps(), mounds(), corn_peanut()):
        for p in group:
            print("wrote", p)
    for p in overlays():
        print("wrote", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())