"""PIL cel sprites for caveman_toilet (200% visual overhaul).

Heads: complete cream #fdfaf2 face on a generous 1536x1536 canvas (chin/hair never
clip), rough-circle contour, 14px-class #1a1214 outer marker ink, solid #161219
oval pupils (NO sclera), 15% cool bottom-left crescent, messy full-width hair cap.
Torso: ONE continuous neck + leopard tunic (#d96b1f / #24140e spots masked inside)
+ matte dark-brown fur shorts, single outer ink outline, no detached pelvis/gloss.
FX/props: cloud, coiled toon poop, tapered stink wisp, digging stick, soft radial
foot-shadow texture. Supersampled x2 then downscaled for crisp ink.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "caveman_toilet" / "sprites"
SS = 2
INK = (26, 18, 20)          # #1a1214 outer marker ink
EYE = (22, 18, 25)          # #161219 solid pupils
CREAM = (253, 250, 242)     # #fdfaf2
SICK = (216, 235, 208)      # #d8ebd0 subtle pale-green face tint
COOL = (120, 140, 165)      # cool grey-blue crescent
CYAN = (120, 220, 235)
TONGUE = (224, 120, 130)
MOUTH_DARK = (38, 23, 26)   # #26171a
TUNIC = (217, 107, 31)      # #d96b1f
SPOT = (36, 20, 14)         # #24140e
SHORTS = (74, 48, 30)       # matte dark-brown fur shorts

CHARS = {
    "caveman": dict(skin=CREAM, hair=(61, 32, 13), streak=(156, 88, 34), beard=False),
    "elder":   dict(skin=CREAM, hair=(226, 232, 240), streak=(198, 203, 214), beard=True),
    "buddy":   dict(skin=CREAM, hair=(45, 26, 12), streak=(122, 72, 32), beard=False),
}
POSES = ["neutral", "shock_question", "clenched_cramp", "relieved_sigh",
         "terror_scream", "sick_nausea", "soul_knockout", "proud_grin",
         "talk_a", "talk_b", "talk_c"]

CX, CY, RX, RY = 512, 548, 318, 338
EX, EY, ERX, ERY = 122, CY - 18, 34, 46
MY = CY + 158


def _new(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (32, 20, 16, 0))


def _down(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def P(x, y):
    return (x * SS, y * SS)


def head_contour(rx, ry, count=240):
    pts = []
    for i in range(count):
        a = 2 * math.pi * i / count
        r = 1 + .022 * math.sin(2 * a + .6) - .015 * math.cos(3 * a - .8) + .008 * math.sin(5 * a + 1.9)
        pts.append((CX + rx * r * math.cos(a), CY + ry * r * math.sin(a)))
    return pts


def draw_head(char, pose, sickly=False):
    c = CHARS[char]
    skin = SICK if sickly else c["skin"]
    img = _new(1024, 1024)
    d = ImageDraw.Draw(img)
    outer = head_contour(RX + 7, RY + 7)
    inner = head_contour(RX - 7, RY - 7)
    # ink then cream
    d.polygon([P(*p) for p in outer], fill=INK + (255,))
    d.polygon([P(*p) for p in inner], fill=skin + (255,))
    # cool bottom-left crescent (15%)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([P(*p) for p in inner], fill=255)
    shifted = Image.new("L", img.size, 0)
    shifted.paste(mask, (14 * SS, -12 * SS))
    cres = ImageChops.subtract(mask, shifted).filter(ImageFilter.GaussianBlur(4 * SS))
    cres = ImageChops.multiply(cres, mask)
    cool_layer = Image.new("RGBA", img.size, COOL + (0,))
    cool_layer.putalpha(cres.point(lambda v: int(v * 0.15)))
    img = Image.alpha_composite(img, cool_layer)
    d = ImageDraw.Draw(img)
    # ---- hair cap: messy polygon across the ENTIRE top width ----
    hair = c["hair"]
    spikes = []
    n = 26
    for i in range(n + 1):
        a = math.pi + math.pi * i / n          # upper arc (y-down)
        base_r = RX + 6
        spike = 30 + 46 * abs(math.sin(i * 2.3 + 0.7)) + (18 if i % 2 else 0)
        rr = base_r + spike
        spikes.append((CX + rr * math.cos(a), CY + (RY + spike * 0.7) * math.sin(a)))
    inner_hair = []
    for i in range(n, -1, -1):
        a = math.pi + math.pi * i / n
        inner_hair.append((CX + (RX - 26) * math.cos(a), CY + (RY - 30) * math.sin(a)))
    d.polygon([P(*p) for p in spikes + inner_hair], fill=hair + (255,))
    # caramel highlight streaks
    random.seed(hash(char) % 9999)
    for _ in range(7):
        a = math.pi + math.pi * random.uniform(0.12, 0.88)
        r0 = RX - 10
        r1 = RX + 40 + random.uniform(0, 30)
        x0, y0 = CX + r0 * math.cos(a), CY + RY * math.sin(a)
        x1, y1 = CX + r1 * math.cos(a), CY + (RY + 30) * math.sin(a)
        d.line([P(x0, y0), P(x1, y1)], fill=c["streak"] + (235,), width=7 * SS)
    # elder beard
    if c["beard"]:
        beard = []
        for i in range(13):
            a = math.pi * 0.15 + math.pi * 0.7 * i / 12   # lower arc
            rr = RX + 26 + 22 * abs(math.sin(i * 1.7))
            beard.append((CX + rr * math.cos(a), CY + (RY + 30) * math.sin(a)))
        chin = [(CX - 150, CY + 200), (CX + 150, CY + 200)]
        d.polygon([P(*p) for p in beard + chin], fill=hair + (255,))
    # ---- features ----
    draw_eyes(d, pose, char)
    draw_mouth(d, pose)
    draw_extras(d, pose, img)
    # generous 1536 canvas: head fills proportionally, chin/hair never clip card edge
    return _down(img, 1536, 1536)


def _oval(d, cx, cy, rx, ry, fill):
    d.ellipse([P(cx - rx, cy - ry), P(cx + rx, cy + ry)], fill=fill)


def draw_eyes(d, pose, char):
    if pose == "soul_knockout":
        for sx in (-1, 1):
            cx = CX + sx * EX
            pts = []
            for t in range(60):
                ang = t * 0.42
                rr = 4 + t * 0.62
                pts.append(P(cx + rr * math.cos(ang), EY + rr * math.sin(ang)))
            d.line(pts, fill=EYE + (255,), width=6 * SS, joint="curve")
        return
    if pose in ("relieved_sigh",):
        for sx in (-1, 1):
            cx = CX + sx * EX
            d.arc([P(cx - ERX, EY - ERY), P(cx + ERX, EY + ERY)], 200, 340,
                  fill=EYE + (255,), width=8 * SS)
        return
    if pose == "sick_nausea":
        for sx in (-1, 1):
            cx = CX + sx * EX
            _oval(d, cx, EY + 8, ERX, ERY * 0.55, EYE + (255,))
            d.line([P(cx - ERX - 6, EY - ERY * 0.5), P(cx + ERX + 6, EY - ERY * 0.5)],
                   fill=INK + (255,), width=7 * SS)
        return
    # default solid vertical ovals (NO sclera)
    brow_lift = -18 if pose == "shock_question" else 0
    for sx in (-1, 1):
        cx = CX + sx * EX
        _oval(d, cx, EY, ERX, ERY, EYE + (255,))
        # brow
        d.line([P(cx - ERX - 4, EY - ERY - 16 + brow_lift),
                P(cx + ERX + 4, EY - ERY - 22 + brow_lift)],
               fill=INK + (255,), width=9 * SS)


def draw_mouth(d, pose):
    if pose == "clenched_cramp":
        # rounded capsule mouth with 2x6 gridded teeth
        w, h = 150, 64
        d.rounded_rectangle([P(CX - w, MY - h), P(CX + w, MY + h)], radius=30 * SS,
                            fill=(245, 240, 230, 255), outline=INK + (255,), width=6 * SS)
        d.line([P(CX - w, MY), P(CX + w, MY)], fill=INK + (255,), width=4 * SS)
        for i in range(1, 6):
            x = CX - w + (2 * w) * i / 6
            d.line([P(x, MY - h), P(x, MY + h)], fill=INK + (255,), width=3 * SS)
        return
    if pose == "terror_scream":
        _oval(d, CX, MY + 10, 78, 96, MOUTH_DARK + (255,))
        _oval(d, CX, MY + 52, 46, 34, TONGUE + (255,))
        d.ellipse([P(CX - 78, MY - 86), P(CX + 78, MY + 106)], outline=INK + (255,), width=6 * SS)
        return
    if pose == "sick_nausea":
        pts = [P(CX - 90 + i * 18, MY + (10 if i % 2 else -10)) for i in range(11)]
        d.line(pts, fill=INK + (255,), width=8 * SS, joint="curve")
        return
    if pose == "soul_knockout":
        _oval(d, CX, MY + 6, 40, 30, MOUTH_DARK + (255,))
        return
    if pose == "proud_grin":
        d.pieslice([P(CX - 110, MY - 70), P(CX + 110, MY + 70)], 10, 170,
                   fill=(245, 240, 230, 255), outline=INK + (255,), width=6 * SS)
        d.line([P(CX - 96, MY + 6), P(CX + 96, MY + 6)], fill=INK + (255,), width=4 * SS)
        return
    if pose == "relieved_sigh":
        d.arc([P(CX - 80, MY - 50), P(CX + 80, MY + 50)], 20, 160, fill=INK + (255,), width=8 * SS)
        return
    if pose == "shock_question":
        _oval(d, CX, MY + 4, 34, 40, MOUTH_DARK + (255,))
        return
    if pose == "talk_a":
        _oval(d, CX, MY + 4, 30, 22, MOUTH_DARK + (255,))
        return
    if pose == "talk_b":
        _oval(d, CX, MY + 6, 46, 40, MOUTH_DARK + (255,))
        return
    if pose == "talk_c":
        _oval(d, CX, MY + 4, 38, 30, MOUTH_DARK + (255,))
        return
    # neutral
    d.arc([P(CX - 60, MY - 34), P(CX + 60, MY + 34)], 20, 160, fill=INK + (255,), width=7 * SS)


def draw_extras(d, pose, img):
    if pose == "clenched_cramp":
        for (sx, sy) in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            cx = CX + sx * (RX - 30)
            cy = EY - 40 + sy * 26
            drop = [(cx, cy - 22), (cx + 13, cy + 6), (cx, cy + 20), (cx - 13, cy + 6)]
            d.polygon([P(*p) for p in drop], fill=CYAN + (235,))
    if pose == "soul_knockout":
        # translucent cyan soul bubble popping out of the top of the head
        bub = Image.new("RGBA", img.size, (0, 0, 0, 0))
        bd = ImageDraw.Draw(bub)
        bcx, bcy, br = CX + 150, CY - RY - 70, 78
        bd.ellipse([P(bcx - br, bcy - br), P(bcx + br, bcy + br)], fill=CYAN + (110,))
        bd.ellipse([P(bcx - br, bcy - br), P(bcx + br, bcy + br)], outline=(180, 240, 250, 200), width=4 * SS)
        bd.ellipse([P(bcx - 26, bcy - 18), P(bcx - 6, bcy + 2)], fill=EYE + (200,))
        bd.ellipse([P(bcx + 8, bcy - 18), P(bcx + 28, bcy + 2)], fill=EYE + (200,))
        bd.arc([P(bcx - 22, bcy + 6), P(bcx + 22, bcy + 34)], 200, 340, fill=EYE + (200,), width=4 * SS)
        img.alpha_composite(bub)


def draw_torso(char):
    """ONE continuous cel: cream neck stub + leopard tunic + matte fur shorts,
    wrapped by a single outer INK outline. No detached pelvis, no gloss."""
    W, H = 768, 1024
    img = _new(W, H)
    cx = W // 2
    neck_top, shoulder_y = 92, 196
    hip_y, hem_y = 600, 632          # tunic fur hem (internal boundary)
    shorts_bot = 862
    # ---- single outer union silhouette (neck -> shoulders -> tunic -> shorts) ----
    outer = [(cx - 80, neck_top), (cx - 98, shoulder_y - 34), (cx - 252, shoulder_y),
             (cx - 288, shoulder_y + 74), (cx - 250, hip_y)]
    outer += [(cx - 214, hem_y), (cx - 206, shorts_bot - 30)]
    # jagged shorts bottom hem, left->right (continues down the left side)
    sb = []
    for i in range(13):
        x = cx - 206 + 412 * i / 12
        sb.append((x, shorts_bot + (26 if i % 2 else 0) + 10 * math.sin(i)))
    outer += sb
    outer += [(cx + 206, shorts_bot - 30), (cx + 214, hem_y), (cx + 250, hip_y),
              (cx + 288, shoulder_y + 74), (cx + 252, shoulder_y),
              (cx + 98, shoulder_y - 34), (cx + 80, neck_top)]
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([P(*p) for p in outer], fill=255)
    inner = mask.filter(ImageFilter.MinFilter(2 * 7 * SS + 1))   # uniform 7px ink inset
    # ink base = full union
    base = Image.new("RGBA", img.size, INK + (255,))
    base.putalpha(mask)
    img = Image.alpha_composite(img, base)
    # ---- colour regions clipped to the inset (seamless, single outline) ----
    fill = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fill)
    # shorts (matte dark-brown fur) lower block
    fd.polygon([P(cx - 230, hem_y - 10), P(cx + 230, hem_y - 10),
                P(cx + 230, shorts_bot + 40), P(cx - 230, shorts_bot + 40)],
               fill=SHORTS + (255,))
    # leopard tunic upper block
    fd.polygon([P(cx - 300, shoulder_y - 40), P(cx + 300, shoulder_y - 40),
                P(cx + 300, hem_y + 6), P(cx - 300, hem_y + 6)], fill=TUNIC + (255,))
    # cream neck stub (mostly hidden behind head card; no white popsicle cylinder)
    fd.polygon([P(cx - 92, neck_top - 6), P(cx + 92, neck_top - 6),
                P(cx + 110, shoulder_y + 6), P(cx - 110, shoulder_y + 6)],
               fill=CREAM + (255,))
    # leopard spots, restricted to tunic band, masked 100% inside union
    random.seed(hash(char) % 7777 + 3)
    for _ in range(30):
        sx = random.uniform(cx - 230, cx + 230)
        sy = random.uniform(shoulder_y + 24, hem_y - 26)
        rr = random.uniform(15, 30)
        blob = [(sx + rr * math.cos(a) * random.uniform(0.7, 1.2),
                 sy + rr * math.sin(a) * random.uniform(0.7, 1.2)) for a in
                [2 * math.pi * k / 10 for k in range(10)]]
        fd.polygon([P(*p) for p in blob], fill=SPOT + (255,))
    fill.putalpha(ImageChops.multiply(fill.getchannel("A"), inner))
    img = Image.alpha_composite(img, fill)
    # jagged fur hem ink line separating tunic / shorts (clipped inside union)
    hemlayer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hemlayer)
    hem = [(cx - 250 + 500 * i / 14, hem_y + (30 if i % 2 else 0) + 12 * math.sin(i))
           for i in range(15)]
    hd.line([P(*p) for p in hem], fill=INK + (255,), width=5 * SS, joint="curve")
    hemlayer.putalpha(ImageChops.multiply(hemlayer.getchannel("A"), mask))
    img = Image.alpha_composite(img, hemlayer)
    return _down(img, W, H)


# ---------------- FX / prop cards ----------------
def fx_question():
    img = _new(256, 256)
    d = ImageDraw.Draw(img)
    d.ellipse([P(20, 20), P(236, 236)], fill=(244, 196, 48, 255), outline=INK + (255,), width=8 * SS)
    d.text(P(78, 40), "?", fill=INK + (255,))
    # draw a bold ? manually
    d.arc([P(86, 60), P(170, 150)], 180, 360, fill=INK + (255,), width=16 * SS)
    d.line([P(128, 130), P(128, 160)], fill=INK + (255,), width=16 * SS)
    d.ellipse([P(118, 176), P(138, 196)], fill=INK + (255,))
    return _down(img, 256, 256)


def fx_fly():
    img = _new(128, 128)
    d = ImageDraw.Draw(img)
    d.ellipse([P(40, 50), P(88, 86)], fill=(20, 18, 20, 255))
    d.ellipse([P(20, 30), P(58, 60)], fill=(180, 200, 220, 150))
    d.ellipse([P(70, 30), P(108, 60)], fill=(180, 200, 220, 150))
    return _down(img, 128, 128)


def fx_bacteria():
    img = _new(256, 256)
    d = ImageDraw.Draw(img)
    cx, cy, r = 128, 128, 70
    pts = []
    for i in range(24):
        a = 2 * math.pi * i / 24
        rr = r + (26 if i % 2 else 0)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon([P(*p) for p in pts], fill=(90, 200, 60, 235), outline=(30, 90, 20, 255), width=5 * SS)
    _oval(d, cx - 18, cy - 10, 10, 12, (20, 60, 15, 255))
    _oval(d, cx + 20, cy + 8, 9, 11, (20, 60, 15, 255))
    return _down(img, 256, 256)


def fx_wisp():
    """Soft alpha-tapered toxic-green stink wisp (tapers at both ends, blurred)."""
    img = _new(256, 512)
    d = ImageDraw.Draw(img)
    for i in range(48):
        t = i / 47
        y = 490 - t * 460
        x = 128 + 46 * math.sin(t * 5.5)
        hw = 46 * math.sin(math.pi * t) ** 0.7 + 4
        alpha = int(140 * math.sin(math.pi * t) ** 1.3)
        d.ellipse([P(x - hw, y - 14), P(x + hw, y + 14)], fill=(150, 225, 120, alpha))
    img = img.filter(ImageFilter.GaussianBlur(3 * SS))
    return _down(img, 256, 512)


def fx_soul():
    img = _new(256, 256)
    d = ImageDraw.Draw(img)
    d.ellipse([P(28, 28), P(228, 228)], fill=CYAN + (120,))
    d.ellipse([P(28, 28), P(228, 228)], outline=(180, 240, 250, 220), width=5 * SS)
    _oval(d, 96, 110, 14, 18, EYE + (220,))
    _oval(d, 160, 110, 14, 18, EYE + (220,))
    d.arc([P(96, 140), P(160, 184)], 200, 340, fill=EYE + (220,), width=5 * SS)
    return _down(img, 256, 256)


def fx_lightbulb():
    img = _new(256, 320)
    d = ImageDraw.Draw(img)
    d.ellipse([P(48, 24), P(208, 184)], fill=(255, 224, 110, 255), outline=(180, 130, 30, 255), width=6 * SS)
    d.rectangle([P(96, 180), P(160, 230)], fill=(150, 150, 160, 255), outline=INK + (255,), width=4 * SS)
    d.line([P(100, 196), P(156, 196)], fill=INK + (255,), width=3 * SS)
    d.line([P(100, 212), P(156, 212)], fill=INK + (255,), width=3 * SS)
    d.line([P(112, 90), P(128, 130), P(144, 90)], fill=(180, 130, 30, 255), width=5 * SS)
    return _down(img, 256, 320)


def fx_shovel():
    img = _new(256, 512)
    d = ImageDraw.Draw(img)
    d.line([P(128, 40), P(128, 330)], fill=(120, 80, 40, 255), width=20 * SS)
    d.line([P(128, 40), P(128, 330)], fill=INK + (255,), width=24 * SS)
    d.line([P(128, 44), P(128, 326)], fill=(140, 95, 50, 255), width=16 * SS)
    blade = [(70, 330), (186, 330), (170, 470), (128, 492), (86, 470)]
    d.polygon([P(*p) for p in blade], fill=(150, 150, 158, 255), outline=INK + (255,), width=6 * SS)
    d.rectangle([P(100, 24), P(156, 48)], fill=(120, 80, 40, 255), outline=INK + (255,), width=4 * SS)
    return _down(img, 256, 512)


def fx_spear():
    img = _new(128, 512)
    d = ImageDraw.Draw(img)
    d.line([P(64, 90), P(64, 490)], fill=(120, 80, 40, 255), width=12 * SS)
    tip = [(64, 16), (92, 92), (64, 78), (36, 92)]
    d.polygon([P(*p) for p in tip], fill=(160, 160, 168, 255), outline=INK + (255,), width=4 * SS)
    return _down(img, 128, 512)


def fx_dirt():
    img = _new(128, 128)
    d = ImageDraw.Draw(img)
    pts = [(64 + 44 * math.cos(a) * random.uniform(0.7, 1.1),
            64 + 44 * math.sin(a) * random.uniform(0.7, 1.1)) for a in
           [2 * math.pi * k / 9 for k in range(9)]]
    random.seed(5)
    d.polygon([P(*p) for p in pts], fill=(74, 50, 31, 255), outline=(40, 26, 16, 255), width=4 * SS)
    return _down(img, 128, 128)


def fx_dust():
    img = _new(256, 256)
    d = ImageDraw.Draw(img)
    for (cx, cy, r, a) in [(90, 150, 60, 120), (160, 130, 70, 110), (128, 180, 55, 100)]:
        d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], fill=(200, 180, 150, a))
    return _down(img, 256, 256)


def fx_cloud():
    """Fluffy stylized cumulus cloud for the sunny sky (soft, no hard ink)."""
    img = _new(512, 256)
    d = ImageDraw.Draw(img)
    for (cx, cy, r) in [(140, 168, 66), (226, 132, 92), (322, 150, 82),
                        (408, 176, 58), (268, 186, 78)]:
        d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], fill=(255, 255, 255, 240))
    # faint cool underside
    for (cx, cy, r) in [(200, 206, 60), (320, 210, 66)]:
        d.ellipse([P(cx - r, cy - r * 0.5), P(cx + r, cy + r * 0.5)], fill=(214, 232, 246, 150))
    img = img.filter(ImageFilter.GaussianBlur(2 * SS))
    return _down(img, 512, 256)


def fx_poop():
    """Toon-inked coiled brown poop mound (#6e4219 + #1a1214 ink), soft-serve swirl."""
    img = _new(256, 256)
    d = ImageDraw.Draw(img)
    POOP = (110, 66, 25)      # #6e4219
    HI = (150, 98, 46)
    cx = 128
    coils = [(198, 66, 34), (152, 50, 30), (112, 34, 26)]   # (cy, rx, ry) bottom->top
    for (cy, rx, ry) in coils:
        d.ellipse([P(cx - rx - 6, cy - ry - 6), P(cx + rx + 6, cy + ry + 6)], fill=INK + (255,))
    for (cy, rx, ry) in coils:
        d.ellipse([P(cx - rx, cy - ry), P(cx + rx, cy + ry)], fill=POOP + (255,))
    # swirl peak
    d.ellipse([P(cx - 18, 66), P(cx + 18, 100)], fill=INK + (255,))
    d.ellipse([P(cx - 13, 71), P(cx + 13, 95)], fill=POOP + (255,))
    d.ellipse([P(cx - 6, 60), P(cx + 8, 78)], fill=POOP + (255,))
    # matte highlights (no gloss)
    for (cy, rx, ry) in coils:
        d.arc([P(cx - rx + 6, cy - ry + 4), P(cx + rx - 6, cy + ry - 4)], 200, 320,
              fill=HI + (255,), width=4 * SS)
    return _down(img, 256, 256)


def fx_stick():
    """Rough wooden digging stick (held prop): tapered shaft + flattened spade end."""
    img = _new(128, 512)
    d = ImageDraw.Draw(img)
    WOOD = (140, 95, 50)
    d.line([P(66, 36), P(60, 360)], fill=INK + (255,), width=22 * SS)
    d.line([P(66, 40), P(60, 356)], fill=WOOD + (255,), width=14 * SS)
    blade = [(40, 352), (84, 352), (76, 468), (62, 494), (48, 468)]
    d.polygon([P(*p) for p in blade], fill=INK + (255,))
    inner = [(x + (4 if x < 62 else -4), y + 4) for (x, y) in blade]
    d.polygon([P(*p) for p in inner], fill=(120, 80, 42, 255))
    d.line([P(56, 120), P(74, 118)], fill=INK + (255,), width=3 * SS)   # grip notch
    d.line([P(58, 200), P(72, 198)], fill=(110, 72, 36, 255), width=3 * SS)
    return _down(img, 128, 512)


def tex_shadow():
    """Soft feathered contact-shadow disc: radial alpha 0.45 center -> 0 edge."""
    S = 256
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    c = (S - 1) / 2
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - c, y - c) / c
            a = 0.45 * (1 - r) ** 1.6 if r < 1 else 0.0
            px[x, y] = (10, 8, 6, int(a * 255))
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for char in CHARS:
        for pose in POSES:
            draw_head(char, pose).save(OUT / f"head_{char}_{pose}.png")
            count += 1
        for pose in ("sick_nausea", "soul_knockout", "shock_question"):
            draw_head(char, pose, sickly=True).save(OUT / f"head_{char}_{pose}_sick.png")
            count += 1
        draw_torso(char).save(OUT / f"torso_{char}.png")
        count += 1
    fx = {"question": fx_question, "fly": fx_fly, "bacteria": fx_bacteria,
          "wisp": fx_wisp, "soul": fx_soul, "lightbulb": fx_lightbulb,
          "shovel": fx_shovel, "spear": fx_spear, "dirt": fx_dirt, "dust": fx_dust,
          "cloud": fx_cloud, "poop": fx_poop, "stick": fx_stick}
    for name, fn in fx.items():
        fn().save(OUT / f"fx_{name}.png")
        count += 1
    tex_shadow().save(OUT / "tex_shadow.png")
    count += 1
    print(f"SHEET sprites generated: {count} files -> {OUT}")


if __name__ == "__main__":
    main()