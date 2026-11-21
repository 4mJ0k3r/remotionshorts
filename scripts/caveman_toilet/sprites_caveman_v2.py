"""v2 cel sprites for caveman_toilet: redesigned heads (16px #23140d ink weighted
to the shaded lower-left, forehead hair cap y=140..330 with zero bald halo,
large #1c1417 solid eyes clipped by horizontal lid apertures), the full v2
expression map, torso crescent, lion head card and toxic haze card.
FX/props reuse sprites_caveman.py.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sprites_caveman as S  # noqa: E402

OUT = S.OUT
SS = 2
INK = (35, 20, 13)          # #23140d
EYE = (28, 20, 23)          # #1c1417
CREAM = (253, 250, 242)
SICK = (216, 235, 208)      # #d8ebd0
COOL = (120, 140, 165)
CYAN = (110, 215, 240)
TONGUE = (226, 118, 132)
MDARK = (40, 18, 20)
TEETH = (247, 243, 232)
GREEN = (92, 168, 64)
S.INK = INK

CX, CY, RX, RY = 512, 548, 318, 338
EX, EY, ERX, ERY = 126, CY - 22, 44, 60
MY = CY + 160
BROW_Y = EY - ERY - 30

HAIR = {
    "caveman": ((61, 32, 13), (156, 88, 34)),     # #3d200d / #9c5822
    "buddy": ((44, 25, 12), (126, 74, 32)),
    "elder": ((226, 230, 238), (184, 190, 204)),
}
EXPRS = ["neutral", "confused", "clenched", "strain", "relieved", "panic",
         "sneaky", "sick", "knockout", "inspired", "stern", "determined",
         "triumphant"]
ALWAYS_SICK = {"sick", "knockout"}


def P(x, y):
    return (x * SS, y * SS)


def contour(width_sign):
    pts = []
    n = 288
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1 + .022 * math.sin(2 * a + .6) - .015 * math.cos(3 * a - .8) + .008 * math.sin(5 * a + 1.9)
        w = 16 * max(.5, 1 + .35 * math.cos(a - 2.35) + .12 * math.sin(3 * a + 1.1))
        pts.append((CX + (RX * r + width_sign * w / 2) * math.cos(a),
                    CY + (RY * r + width_sign * w / 2) * math.sin(a)))
    return pts


def crescent_layer(mask, dx, dy, blur, strength=0.15):
    shifted = Image.new("L", mask.size, 0)
    shifted.paste(mask, (dx, dy))
    cres = ImageChops.subtract(mask, shifted).filter(ImageFilter.GaussianBlur(blur))
    cres = ImageChops.multiply(cres, mask)
    lay = Image.new("RGBA", mask.size, COOL + (0,))
    lay.putalpha(cres.point(lambda v: int(v * strength)))
    return lay


def hair_poly():
    random.seed(7)
    pts = []
    a0, a1 = math.pi + 0.36, 2 * math.pi - 0.36
    n = 30
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        top = max(0.0, -math.sin(a))
        spike = (16 + 30 * abs(math.sin(i * 2.3 + 0.7)) + (14 if i % 2 else 0)) * (0.45 + 0.55 * top)
        pts.append((CX + (RX + 24 + spike) * math.cos(a), CY + (RY + 24 + spike) * math.sin(a)))
    m = 22
    for j in range(m + 1):
        u = 1 - 2 * j / m
        x = CX + (RX - 6) * u
        y = 330 + 92 * u ** 4 + (20 if j % 2 else -4)
        pts.append((x, y))
    return pts


def draw_hair(img, char):
    hair, streak = HAIR[char]
    pts = hair_poly()
    d = ImageDraw.Draw(img)
    d.line([P(*p) for p in pts + [pts[0]]], fill=INK + (255,), width=24 * SS, joint="curve")
    d.polygon([P(*p) for p in pts], fill=hair + (255,))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([P(*p) for p in pts], fill=255)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    random.seed(hash(char) % 9973)
    for _ in range(9):
        x0 = CX + random.uniform(-250, 250)
        y0 = random.uniform(200, 260)
        bend = random.uniform(-40, 40)
        ld.line([P(x0, y0), P(x0 + bend * 0.5, y0 + 40), P(x0 + bend, y0 + 85)],
                fill=streak + (235,), width=9 * SS, joint="curve")
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), mask.filter(ImageFilter.MinFilter(9))))
    img.alpha_composite(lay)
    if char == "elder":
        beard = []
        for i in range(15):
            a = math.pi * 0.12 + math.pi * 0.76 * i / 14
            rr = RX + 20 + 24 * abs(math.sin(i * 1.7))
            beard.append((CX + rr * math.cos(a), CY + (RY + 34) * math.sin(a)))
        beard += [(CX - 160, CY + 210), (CX - 60, CY + 236), (CX + 60, CY + 236), (CX + 160, CY + 210)]
        d = ImageDraw.Draw(img)
        d.line([P(*p) for p in beard + [beard[0]]], fill=INK + (255,), width=20 * SS, joint="curve")
        d.polygon([P(*p) for p in beard], fill=hair + (255,))


def eye(img, cx, cy, rx, ry, top, bot, dx=0):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse([P(cx + dx - rx, cy - ry), P(cx + dx + rx, cy + ry)], fill=255)
    clip = Image.new("L", img.size, 0)
    ImageDraw.Draw(clip).rectangle([P(cx - rx * 2, top), P(cx + rx * 2, bot)], fill=255)
    lay = Image.new("RGBA", img.size, EYE + (0,))
    lay.putalpha(ImageChops.multiply(mask, clip))
    img.alpha_composite(lay)


def thick(d, pts, w, col=INK):
    d.line([P(*p) for p in pts], fill=col + (255,), width=w * SS, joint="curve")
    for p in (pts[0], pts[-1]):
        r = w / 2
        d.ellipse([P(p[0] - r, p[1] - r), P(p[0] + r, p[1] + r)], fill=col + (255,))


def brows(d, inner_dy, outer_dy, w=15, sides=(-1, 1), per=None):
    for sx in sides:
        idy, ody = per[sx] if per else (inner_dy, outer_dy)
        cx = CX + sx * EX
        thick(d, [(cx - sx * (ERX + 4), BROW_Y + idy), (cx + sx * (ERX + 14), BROW_Y + ody)], w)


def lid(d, cx, y, rx, slope=0, w=10):
    thick(d, [(cx - rx - 6, y - slope), (cx + rx + 6, y + slope)], w)


def open_eyes(img, scale=1.0, top_frac=1.0, bot_frac=1.0, dx=0, lids=False):
    d = ImageDraw.Draw(img)
    rx, ry = ERX * scale, ERY * scale
    for sx in (-1, 1):
        cx = CX + sx * EX
        top = EY - ry * top_frac
        bot = EY + ry * bot_frac
        eye(img, cx, EY, rx, ry, top, bot, dx)
        if lids:
            lid(d, cx + dx, top, rx)
            if bot_frac < 0.9:
                lid(d, cx + dx, bot, rx, w=7)


def arcs_closed(d, w=14):
    for sx in (-1, 1):
        cx = CX + sx * EX
        d.arc([P(cx - ERX - 4, EY - 30), P(cx + ERX + 4, EY + 50)], 200, 340, fill=INK + (255,), width=w * SS)


def capsule_teeth(d, w, h, cy=MY, cols=6):
    d.rounded_rectangle([P(CX - w, cy - h), P(CX + w, cy + h)], radius=h * SS,
                        fill=TEETH + (255,), outline=INK + (255,), width=9 * SS)
    d.line([P(CX - w + 8, cy), P(CX + w - 8, cy)], fill=INK + (255,), width=5 * SS)
    for i in range(1, cols):
        x = CX - w + 2 * w * i / cols
        d.line([P(x, cy - h + 6), P(x, cy + h - 6)], fill=INK + (255,), width=4 * SS)


def drop(d, x, y, s=1.0):
    pts = [(x, y - 26 * s), (x + 15 * s, y + 4 * s), (x + 10 * s, y + 18 * s), (x, y + 23 * s),
           (x - 10 * s, y + 18 * s), (x - 15 * s, y + 4 * s)]
    d.polygon([P(*p) for p in pts], fill=CYAN + (245,), outline=INK + (255,), width=4 * SS)


def sweat4(d):
    for sx in (-1, 1):
        drop(d, CX + sx * 258, 412)
        drop(d, CX + sx * 282, 486, 0.8)


def features(img, expr):
    d = ImageDraw.Draw(img)
    if expr == "neutral":
        open_eyes(img)
        brows(d, 0, -6)
        d.arc([P(CX - 64, MY - 40), P(CX + 64, MY + 30)], 25, 155, fill=INK + (255,), width=12 * SS)
    elif expr == "confused":
        open_eyes(img)
        brows(d, 0, 0, per={-1: (-34, -46), 1: (14, 2)})
        mouth = [(CX - 52, MY + 14), (CX - 10, MY - 14), (CX + 58, MY - 30), (CX + 76, MY + 4),
                 (CX + 46, MY + 40), (CX - 8, MY + 34)]
        d.polygon([P(*p) for p in mouth], fill=MDARK + (255,), outline=INK + (255,), width=9 * SS)
    elif expr == "clenched":
        open_eyes(img, top_frac=0.45, bot_frac=0.7, lids=True)
        brows(d, 30, -24, w=17)
        capsule_teeth(d, 150, 46)
        sweat4(d)
    elif expr == "strain":
        for sx in (-1, 1):
            cx = CX + sx * EX
            tip = cx - sx * 0.0
            thick(d, [(cx + sx * ERX, EY - 36), (tip - sx * ERX * 0.7, EY), (cx + sx * ERX, EY + 36)], 15)
        brows(d, 34, -28, w=17)
        capsule_teeth(d, 120, 38, cols=5)
        for sx in (-1, 1):
            drop(d, CX + sx * 262, 430, 0.9)
    elif expr == "relieved":
        arcs_closed(d)
        brows(d, -12, -20)
        d.ellipse([P(CX - 36, MY - 30), P(CX + 36, MY + 44)], fill=MDARK + (255,), outline=INK + (255,), width=9 * SS)
    elif expr == "panic":
        open_eyes(img, scale=1.22)
        for sx in (-1, 1):
            cx = CX + sx * EX
            d.arc([P(cx - ERX - 18, BROW_Y - 70), P(cx + ERX + 18, BROW_Y - 6)], 195, 345,
                  fill=INK + (255,), width=15 * SS)
        d.ellipse([P(CX - 96, MY - 70), P(CX + 96, MY + 150)], fill=MDARK + (255,), outline=INK + (255,), width=10 * SS)
        d.ellipse([P(CX - 58, MY + 70), P(CX + 58, MY + 140)], fill=TONGUE + (255,))
    elif expr == "sneaky":
        open_eyes(img, top_frac=0.05, dx=20, lids=False)
        for sx in (-1, 1):
            lid(d, CX + sx * EX + 10, EY - ERY * 0.05, ERX + 6, slope=4 * sx, w=13)
        brows(d, 0, 0, per={-1: (8, 6), 1: (-8, -24)})
        thick(d, [(CX - 74, MY + 4), (CX - 20, MY + 18), (CX + 40, MY + 10), (CX + 82, MY - 22)], 12)
    elif expr == "sick":
        open_eyes(img, top_frac=0.12, bot_frac=0.38, lids=True)
        brows(d, -24, 8, w=14)
        wave = [(CX - 96 + 8 * i, MY + 14 * math.sin(i * 0.95)) for i in range(25)]
        d.line([P(*p) for p in wave], fill=INK + (255,), width=20 * SS, joint="curve")
        d.line([P(*p) for p in wave], fill=GREEN + (255,), width=9 * SS, joint="curve")
    elif expr == "knockout":
        for sx in (-1, 1):
            cx = CX + sx * EX
            pts = [P(cx + (5 + t * 0.78) * math.cos(t * 0.40 * sx), EY + (5 + t * 0.78) * math.sin(t * 0.40 * sx))
                   for t in range(64)]
            d.line(pts, fill=EYE + (255,), width=10 * SS, joint="curve")
        brows(d, -18, 6, w=12)
        d.ellipse([P(CX - 58, MY - 30), P(CX + 58, MY + 70)], fill=MDARK + (255,), outline=INK + (255,), width=9 * SS)
        d.ellipse([P(CX - 34, MY + 30), P(CX + 34, MY + 66)], fill=TONGUE + (255,))
        drop(d, CX + 62, MY + 78, 1.1)
    elif expr == "inspired":
        open_eyes(img, scale=1.16)
        brows(d, -36, -30, w=15)
        d.pieslice([P(CX - 74, MY - 52), P(CX + 74, MY + 82)], 0, 180, fill=MDARK + (255,), outline=INK + (255,), width=9 * SS)
        d.ellipse([P(CX - 34, MY + 40), P(CX + 34, MY + 76)], fill=TONGUE + (255,))
    elif expr == "stern":
        open_eyes(img, top_frac=0.5, lids=True)
        brows(d, 28, -10, w=21)
        d.rounded_rectangle([P(CX - 72, MY - 22), P(CX + 72, MY + 30)], radius=20 * SS,
                            fill=MDARK + (255,), outline=INK + (255,), width=9 * SS)
    elif expr == "determined":
        open_eyes(img, top_frac=0.4, lids=True)
        brows(d, 22, -16, w=17)
        capsule_teeth(d, 132, 34, cols=6)
    elif expr == "triumphant":
        arcs_closed(d)
        brows(d, -26, -34)
        d.chord([P(CX - 130, MY - 90), P(CX + 130, MY + 110)], 0, 180, fill=MDARK + (255,), outline=INK + (255,), width=10 * SS)
        d.rectangle([P(CX - 112, MY + 10), P(CX + 112, MY + 34)], fill=TEETH + (255,))
        d.ellipse([P(CX - 50, MY + 62), P(CX + 50, MY + 104)], fill=TONGUE + (255,))


def draw_head(char, expr):
    sick = expr in ALWAYS_SICK
    img = Image.new("RGBA", (1024 * SS, 1024 * SS), INK + (0,))
    d = ImageDraw.Draw(img)
    d.polygon([P(*p) for p in contour(+1)], fill=INK + (255,))
    inner = contour(-1)
    d.polygon([P(*p) for p in inner], fill=(SICK if sick else CREAM) + (255,))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([P(*p) for p in inner], fill=255)
    img.alpha_composite(crescent_layer(mask, 16 * SS, -14 * SS, 5 * SS))
    draw_hair(img, char)
    features(img, expr)
    return img.resize((1536, 1536), Image.LANCZOS)


def torso_v2(char):
    img = S.draw_torso(char)
    a = img.getchannel("A")
    inner = a.point(lambda v: 255 if v > 250 else 0).filter(ImageFilter.MinFilter(15))
    img.alpha_composite(crescent_layer(inner, 14, -12, 4))
    return img


def lion_card():
    W = 512
    img = Image.new("RGBA", (W * SS, W * SS), (30, 18, 10, 0))
    d = ImageDraw.Draw(img)
    mane = []
    for i in range(40):
        a = 2 * math.pi * i / 40
        r = 225 if i % 2 else 186
        mane.append((256 + r * math.cos(a), 250 + r * 0.95 * math.sin(a)))
    d.polygon([P(*p) for p in mane], fill=(46, 26, 12, 255), outline=(14, 8, 5, 255), width=8 * SS)
    d.ellipse([P(136, 120), P(376, 400)], fill=(82, 52, 26, 255), outline=(14, 8, 5, 255), width=7 * SS)
    for sx in (-1, 1):
        d.ellipse([P(256 + sx * 62 - 30, 200), P(256 + sx * 62 + 30, 236)], fill=(20, 10, 6, 255))
    d.polygon([P(232, 270), P(280, 270), P(256, 296)], fill=(20, 10, 6, 255))
    d.ellipse([P(186, 300), P(326, 392)], fill=(70, 12, 14, 255), outline=(14, 8, 5, 255), width=6 * SS)
    for fx, up in ((214, True), (298, True), (232, False), (280, False)):
        if up:
            d.polygon([P(fx - 12, 306), P(fx + 12, 306), P(fx, 346)], fill=(250, 248, 240, 255))
        else:
            d.polygon([P(fx - 10, 388), P(fx + 10, 388), P(fx, 356)], fill=(250, 248, 240, 255))
    return img.resize((W, W), Image.LANCZOS)


def haze_card():
    W, H = 512, 256
    img = Image.new("RGBA", (W, H), (120, 210, 80, 0))
    d = ImageDraw.Draw(img)
    random.seed(21)
    for _ in range(14):
        cx, cy = random.uniform(90, 420), random.uniform(90, 170)
        r = random.uniform(50, 95)
        d.ellipse([cx - r, cy - r * 0.6, cx + r, cy + r * 0.6], fill=(130, 215, 85, 70))
    return img.filter(ImageFilter.GaussianBlur(18))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    n = 0
    for char in HAIR:
        for expr in EXPRS:
            draw_head(char, expr).save(OUT / f"v2head_{char}_{expr}.png")
            n += 1
        torso_v2(char).save(OUT / f"v2torso_{char}.png")
        n += 1
    lion_card().save(OUT / "v2_lion.png")
    haze_card().save(OUT / "v2_haze.png")
    print(f"v2 sprites: {n + 2} files -> {OUT}")


if __name__ == "__main__":
    main()
