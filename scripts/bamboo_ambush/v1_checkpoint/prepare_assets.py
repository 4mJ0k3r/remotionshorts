"""Stage 2A: Generate 1536x1536 shaded cel character cards, FX textures, and top hook HUD."""
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(r"D:\remotionshorts")
OUT = ROOT / "renders" / "bamboo_ambush"
ART = OUT / "assets"
ART.mkdir(parents=True, exist_ok=True)

N = 1536
INK = "#1a1214"
INK_RGBA = (26, 18, 20, 0)
CREAM = "#fdfaf2"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"


def canvas(size=N):
    return Image.new("RGBA", (size, size), INK_RGBA)


def ink_line(draw, pts, width=9, fill=INK):
    draw.line(pts, fill=fill, width=width, joint="curve")
    r = width / 2.0
    for x, y in (pts[0], pts[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def apply_cel_shading(im, fill_mask, base_hex, crescent_strength=0.25, rim_strength=0.18, sand_bounce=False):
    """Apply bright lit top-right side, 25% cool shaded crescent bottom-left, and warm golden rim highlight."""
    arr = np.array(im, dtype=np.float32)
    mask_arr = np.array(fill_mask, dtype=np.float32) / 255.0
    yy, xx = np.mgrid[:N, :N]
    # Directional top-right brightness lift + warm sand bounce near chin
    lit_grad = np.clip(0.95 + 0.08 * (xx / N) - 0.05 * (yy / N), 0.90, 1.05)
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] * (1.0 + (lit_grad - 1.0) * mask_arr), 0, 255)
    if sand_bounce:
        bounce = np.clip((yy - N * 0.45) / (N * 0.45), 0.0, 1.0) * mask_arr * 0.14
        arr[:, :, 0] = np.clip(arr[:, :, 0] * (1 - bounce) + 245 * bounce, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] * (1 - bounce) + 216 * bounce, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * (1 - bounce) + 165 * bounce, 0, 255)
    shaded = Image.fromarray(arr.astype(np.uint8))

    # 25% darker shaded crescent on lower-left (shifted +92, -68 inside N=1536)
    shifted_bl = Image.new("L", (N, N), 0)
    shifted_bl.paste(fill_mask, (96, -70))
    crescent = ImageChops.subtract(fill_mask, shifted_bl).filter(ImageFilter.GaussianBlur(18))
    crescent = ImageChops.multiply(crescent, fill_mask).point(lambda v: int(v * crescent_strength))
    cool_layer = Image.new("RGBA", (N, N), (74, 86, 102, 0))
    cool_layer.putalpha(crescent)
    shaded = Image.alpha_composite(shaded, cool_layer)

    # Warm golden rim highlight along upper-right inner edge
    shifted_tr = Image.new("L", (N, N), 0)
    shifted_tr.paste(fill_mask, (-48, 38))
    rim = ImageChops.subtract(fill_mask, shifted_tr).filter(ImageFilter.GaussianBlur(9))
    rim = ImageChops.multiply(rim, fill_mask).point(lambda v: int(v * rim_strength))
    gold_layer = Image.new("RGBA", (N, N), (255, 233, 166, 0))
    gold_layer.putalpha(rim)
    shaded = Image.alpha_composite(shaded, gold_layer)
    return shaded


def rough_head_contours(cx=768, cy=810, rx=510, ry=495, count=256, w0=14.0):
    outer, inner = [], []
    for i in range(count):
        a = math.tau * i / count
        r = 1.0 + 0.020 * math.sin(2 * a + 0.6) - 0.014 * math.cos(3 * a - 0.8) + 0.007 * math.sin(5 * a + 1.9)
        w = w0 * max(0.55, 1.0 + 0.42 * math.cos(a - 2.35) + 0.16 * math.sin(3 * a + 1.1))
        outer.append((cx + (rx * r + w / 2) * math.cos(a), cy + (ry * r + w / 2) * math.sin(a)))
        inner.append((cx + (rx * r - w / 2) * math.cos(a), cy + (ry * r - w / 2) * math.sin(a)))
    return outer, inner


def build_soldier_head():
    im = canvas()
    d = ImageDraw.Draw(im)
    outer, inner = rough_head_contours(cx=768, cy=825, rx=500, ry=480, w0=14.0)

    # Side ears behind head contour
    for s in (-1, 1):
        ex = 768 + s * 498
        d.ellipse((ex - 58, 795, ex + 58, 945), fill=CREAM, outline=INK, width=14)

    d.polygon(outer, fill=INK)
    d.polygon(inner, fill=CREAM)
    head_mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(head_mask).polygon(inner, fill=255)
    im = apply_cel_shading(im, head_mask, CREAM, crescent_strength=0.25, rim_strength=0.18, sand_bounce=True)

    # 2.5D Olive-Drab Netted Military Helmet (#5c6346)
    hel = canvas()
    hd = ImageDraw.Draw(hel)
    # Helmet dome arc
    dome_pts = []
    cx, cy = 768, 745
    for i in range(129):
        a = math.pi + (i / 128) * math.pi  # pi -> 2pi (top half)
        rx_h = 568
        ry_h = 515
        dome_pts.append((cx + rx_h * math.cos(a), cy + ry_h * math.sin(a)))
    # Helmet brim curve across forehead
    brim_pts = [
        (1340, 745),
        (1270, 682),
        (1100, 622),
        (920, 592),
        (768, 584),
        (616, 592),
        (436, 622),
        (266, 682),
        (196, 745),
    ]
    helmet_poly = dome_pts + brim_pts
    hd.polygon(helmet_poly, fill="#5c6346")
    hel_mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(hel_mask).polygon(helmet_poly, fill=255)
    hel = apply_cel_shading(hel, hel_mask, "#5c6346", crescent_strength=0.28, rim_strength=0.20)

    # Dark olive diamond net grid clipped inside helmet
    net = canvas()
    nd = ImageDraw.Draw(net)
    for k in range(-10, 14):
        x0 = 768 + k * 115
        nd.line([(x0 - 480, 180), (x0 + 480, 820)], fill="#333924", width=9)
        nd.line([(x0 + 480, 180), (x0 - 480, 820)], fill="#333924", width=9)
    net.putalpha(ImageChops.multiply(net.getchannel("A"), hel_mask))
    hel = Image.alpha_composite(hel, net)

    # Helmet outer ink border (14px) around dome + curved brim (no horizontal chord across forehead)
    hd = ImageDraw.Draw(hel)
    hd.line(helmet_poly + [helmet_poly[0]], fill=INK, width=14, joint="curve")
    # Helmet band strap
    band_pts = [(220, 665), (430, 595), (768, 565), (1106, 595), (1316, 665)]
    hd.line(band_pts, fill="#3d422d", width=18, joint="curve")
    hd.line(band_pts, fill=INK, width=7, joint="curve")

    # Forehead cast shadow under brim on cream face
    brim_sh = canvas()
    bsd = ImageDraw.Draw(brim_sh)
    bsd.polygon(brim_pts + [(200, 775), (440, 665), (768, 632), (1096, 665), (1336, 775)], fill=(45, 38, 35, 68))
    brim_sh.putalpha(ImageChops.multiply(brim_sh.getchannel("A"), head_mask))
    im = Image.alpha_composite(im, brim_sh)
    im = Image.alpha_composite(im, hel)

    # Brown chin strap (#5c3d24) wrapping around jaw
    d = ImageDraw.Draw(im)
    strap_pts = [(280, 760), (312, 990), (470, 1210), (768, 1285), (1066, 1210), (1224, 990), (1256, 760)]
    d.line(strap_pts, fill=INK, width=42, joint="curve")
    d.line(strap_pts, fill="#5c3d24", width=22, joint="curve")
    # Chin strap brass buckle
    d.rounded_rectangle((425, 1145, 485, 1210), radius=10, fill="#c9a558", outline=INK, width=9)

    im.save(ART / "soldier_head.png")


def build_enemy_head():
    im = canvas()
    d = ImageDraw.Draw(im)
    outer, inner = rough_head_contours(cx=768, cy=810, rx=510, ry=495, w0=14.0)
    for s in (-1, 1):
        ex = 768 + s * 508
        d.ellipse((ex - 58, 770, ex + 58, 920), fill=CREAM, outline=INK, width=14)
    d.polygon(outer, fill=INK)
    d.polygon(inner, fill=CREAM)
    head_mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(head_mask).polygon(inner, fill=255)
    im = apply_cel_shading(im, head_mask, CREAM, crescent_strength=0.25, rim_strength=0.18, sand_bounce=True)
    # Subtle bald shine / brow line hint at top-right (non-white-dot, soft warm crescent)
    d = ImageDraw.Draw(im)
    d.arc((640, 385, 1080, 560), 235, 315, fill="#f5e6c8", width=11)
    im.save(ART / "enemy_head.png")


def build_soldier_torso():
    im = canvas()
    mask = Image.new("L", (N, N), 0)
    md = ImageDraw.Draw(mask)
    # Unified rounded torso + neck stub + waist overlap
    md.rounded_rectangle((635, 90, 901, 340), radius=60, fill=255)
    md.rounded_rectangle((280, 220, 1256, 1370), radius=260, fill=255)

    ink_layer = Image.new("RGBA", (N, N), INK)
    ink_layer.putalpha(mask)
    inner_mask = mask.filter(ImageFilter.MinFilter(29))  # ~14px outline inset

    fill = Image.new("RGBA", (N, N), "#9c8468")
    fill_clip = Image.new("RGBA", (N, N), INK_RGBA)
    fill_clip.paste(fill, (0, 0), inner_mask)
    fill_clip = apply_cel_shading(fill_clip, inner_mask, "#9c8468", crescent_strength=0.25, rim_strength=0.18)

    im = Image.alpha_composite(ink_layer, fill_clip)
    d = ImageDraw.Draw(im)

    # Khaki shirt details clipped inside inner_mask
    detail = canvas()
    dd = ImageDraw.Draw(detail)
    # Collar
    dd.polygon([(540, 235), (768, 405), (996, 235), (930, 195), (768, 305), (606, 195)], fill="#8a7256", outline=INK, width=9)
    # Center placket + buttons
    dd.line([(768, 405), (768, 1060)], fill=INK, width=9)
    for by in (520, 685, 850):
        dd.ellipse((748, by - 20, 788, by + 20), fill="#524332", outline=INK, width=6)

    # Beige X-suspenders (#c8b99e)
    for x0, x1 in [(440, 1096), (1096, 440)]:
        dd.line([(x0, 235), (x1, 1075)], fill=INK, width=82)
        dd.line([(x0, 235), (x1, 1075)], fill="#c8b99e", width=62)

    # Waist belt & ammo pouches (#6b4f35)
    dd.rectangle((270, 1045, 1266, 1145), fill="#4a3726", outline=INK, width=9)
    dd.rounded_rectangle((708, 1030, 828, 1160), radius=14, fill="#b89854", outline=INK, width=9)
    for px in (385, 550, 985, 1150):
        dd.rounded_rectangle((px - 72, 1025, px + 72, 1215), radius=24, fill="#6b4f35", outline=INK, width=9)
        dd.polygon([(px - 70, 1035), (px + 70, 1035), (px + 55, 1110), (px - 55, 1110)], fill="#7d5e41", outline=INK, width=7)
        dd.ellipse((px - 12, 1085, px + 12, 1109), fill="#c9a558", outline=INK, width=5)

    detail.putalpha(ImageChops.multiply(detail.getchannel("A"), inner_mask))
    im = Image.alpha_composite(im, detail)
    im.save(ART / "soldier_torso.png")


def build_enemy_torso():
    im = canvas()
    mask = Image.new("L", (N, N), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((635, 90, 901, 340), radius=60, fill=255)
    md.rounded_rectangle((270, 220, 1266, 1370), radius=265, fill=255)

    ink_layer = Image.new("RGBA", (N, N), INK)
    ink_layer.putalpha(mask)
    inner_mask = mask.filter(ImageFilter.MinFilter(29))

    fill = Image.new("RGBA", (N, N), "#008751")
    fill_clip = Image.new("RGBA", (N, N), INK_RGBA)
    fill_clip.paste(fill, (0, 0), inner_mask)
    fill_clip = apply_cel_shading(fill_clip, inner_mask, "#008751", crescent_strength=0.25, rim_strength=0.18)

    im = Image.alpha_composite(ink_layer, fill_clip)

    detail = canvas()
    dd = ImageDraw.Draw(detail)
    # Crisp white shoulder stripes + collar V-neck
    dd.polygon([(310, 345), (560, 210), (610, 240), (340, 410)], fill="#ffffff", outline=INK, width=9)
    dd.polygon([(1226, 345), (976, 210), (926, 240), (1196, 410)], fill="#ffffff", outline=INK, width=9)
    dd.arc((595, 130, 941, 375), 5, 175, fill="#ffffff", width=36)
    dd.arc((595, 130, 941, 375), 5, 175, fill=INK, width=10)

    # Bold white "NEW YORK" and "17"
    f_ny = ImageFont.truetype(FONT_BOLD, 108)
    f_17 = ImageFont.truetype(FONT_BOLD, 410)
    dd.text((768, 520), "NEW YORK", font=f_ny, anchor="mm", fill="#ffffff", stroke_width=10, stroke_fill=INK)
    dd.text((768, 860), "17", font=f_17, anchor="mm", fill="#ffffff", stroke_width=14, stroke_fill=INK)

    detail.putalpha(ImageChops.multiply(detail.getchannel("A"), inner_mask))
    im = Image.alpha_composite(im, detail)
    im.save(ART / "enemy_torso.png")


def draw_clipped_eye(im, cx, cy, rx, ry, top_ratio, bot_ratio, pupil_dx=0, pupil_dy=0, pupil_scale=1.0, veins=False):
    """Draw warm-ivory sclera + solid #161219 pupil clipped by horizontal eyelid aperture."""
    d = ImageDraw.Draw(im)
    if top_ratio >= bot_ratio:
        # Closed blink stroke
        ink_line(d, [(cx - rx * 1.15, cy), (cx + rx * 1.15, cy)], width=12)
        return im

    sclera_mask = Image.new("L", (N, N), 0)
    ImageDraw.Draw(sclera_mask).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    top_y = cy - ry + (2 * ry) * top_ratio
    bot_y = cy - ry + (2 * ry) * bot_ratio
    lid_clip = Image.new("L", (N, N), 0)
    ImageDraw.Draw(lid_clip).rectangle((cx - rx - 20, top_y, cx + rx + 20, bot_y), fill=255)
    eye_alpha = ImageChops.multiply(sclera_mask, lid_clip)

    eye_fill = Image.new("RGBA", (N, N), "#fffdf7")
    if veins:
        vd = ImageDraw.Draw(eye_fill)
        for ang in (0.3, 0.9, 2.2, 2.8, 3.6, 5.2):
            p0 = (cx + rx * 0.95 * math.cos(ang), cy + ry * 0.95 * math.sin(ang))
            p1 = (cx + rx * 0.55 * math.cos(ang + 0.14), cy + ry * 0.55 * math.sin(ang - 0.1))
            p2 = (cx + rx * 0.34 * math.cos(ang - 0.1), cy + ry * 0.34 * math.sin(ang + 0.08))
            vd.line([p0, p1, p2], fill="#d93829", width=7, joint="curve")

    # Pupil clipped inside eye_alpha
    pd = ImageDraw.Draw(eye_fill)
    prx = max(14, int(rx * 0.48 * pupil_scale))
    pry = max(18, int(ry * 0.54 * pupil_scale))
    pdx = cx + pupil_dx
    pdy = cy + pupil_dy
    pd.ellipse((pdx - prx, pdy - pry, pdx + prx, pdy + pry), fill="#161219")
    # Crisp tiny specular catchlight only when pupil is normal size
    if pupil_scale >= 0.7:
        pd.ellipse((pdx - prx * 0.45, pdy - pry * 0.45, pdx - prx * 0.1, pdy - pry * 0.1), fill="#fffdf7")

    eye_fill.putalpha(eye_alpha)
    im = Image.alpha_composite(im, eye_fill)

    # Eye outline arc along visible aperture (flush with sclera rim, zero protruding whiskers)
    sclera_outer = Image.new("L", (N, N), 0)
    ImageDraw.Draw(sclera_outer).ellipse((cx - rx - 6, cy - ry - 6, cx + rx + 6, cy + ry + 6), fill=255)
    outline_mask = Image.new("L", (N, N), 0)
    od = ImageDraw.Draw(outline_mask)
    od.ellipse((cx - rx - 5, cy - ry - 5, cx + rx + 5, cy + ry + 5), outline=255, width=11)
    if top_ratio > 0.02:
        od.line([(cx - rx - 6, top_y), (cx + rx + 6, top_y)], fill=255, width=11)
    if bot_ratio < 0.98:
        od.line([(cx - rx - 6, bot_y), (cx + rx + 6, bot_y)], fill=255, width=11)
    outline_alpha = ImageChops.multiply(ImageChops.multiply(outline_mask, lid_clip), sclera_outer)
    outline_rgba = Image.new("RGBA", (N, N), INK)
    outline_rgba.putalpha(outline_alpha)
    return Image.alpha_composite(im, outline_rgba)


def build_soldier_faces():
    states = [
        "neutral_open",
        "neutral_blink",
        "pipe_o_open",
        "pipe_o_blink",
        "pipe_o_left",
        "pipe_o_right",
        "war_cry",
        "gag_in",
        "gag_out",
    ]
    eye_y = 890
    for st in states:
        im = canvas()
        is_blink = "blink" in st
        is_gag = st.startswith("gag")
        rx = 100 if is_gag else 78
        ry = 112 if is_gag else 88
        pdx = -26 if st == "pipe_o_left" else (26 if st == "pipe_o_right" else 0)
        pdy = 8 if st == "war_cry" else 0
        pscale = 0.34 if is_gag else 0.95
        top_r, bot_r = (0.5, 0.5) if is_blink else (0.0, 1.0)

        for sx in (-1, 1):
            ex = 768 + sx * 172
            im = draw_clipped_eye(im, ex, eye_y, rx, ry, top_r, bot_r, pdx, pdy, pscale, veins=is_gag)

        d = ImageDraw.Draw(im)
        # Brows
        for sx in (-1, 1):
            bx = 768 + sx * 172
            if st == "war_cry":
                ink_line(d, [(bx - sx * 68, 742), (bx + sx * 68, 782)], width=16)
            elif is_gag:
                ink_line(d, [(bx - sx * 70, 735), (bx + sx * 66, 710)], width=15)
            elif "pipe_o" in st:
                ink_line(d, [(bx - 64, 775), (bx + 64, 768)], width=14)
            else:
                ink_line(d, [(bx - 60, 782), (bx + 60, 780)], width=14)

        # Mouth & cheeks
        my = 1085
        if st.startswith("neutral"):
            ink_line(d, [(700, my), (768, my + 8), (836, my)], width=14)
        elif st.startswith("pipe_o"):
            d.ellipse((712, my - 44, 824, my + 48), fill="#26171a", outline=INK, width=11)
        elif st == "war_cry":
            d.rounded_rectangle((635, my - 68, 901, my + 86), radius=52, fill="#26171a", outline=INK, width=12)
            d.rounded_rectangle((658, my - 56, 878, my - 18), radius=12, fill="#fffdf7")
            d.ellipse((688, my + 12, 848, my + 78), fill="#d9596b")
        elif is_gag:
            # Puffed traumatized cheeks expanding between gag_in and gag_out
            cheek_r = 95 if st == "gag_out" else 68
            for sx in (-1, 1):
                cx_c = 768 + sx * 225
                d.ellipse((cx_c - cheek_r, my - cheek_r * 0.72, cx_c + cheek_r, my + cheek_r * 0.72), fill="#f7c8b8", outline=INK, width=11)
            d.ellipse((694, my - 56, 842, my + 64), fill="#26171a", outline=INK, width=12)
            d.ellipse((728, my + 10, 808, my + 56), fill="#d9596b")

        im.save(ART / f"soldier_face_{st}.png")


def build_enemy_faces():
    states = [
        "patrol_open",
        "patrol_blink",
        "patrol_down",
        "terror_open",
        "grenade_mouth",
        "creepy_grin_1",
        "creepy_grin_2",
        "wild_squint_grin",
    ]
    eye_y = 770
    for st in states:
        im = canvas()
        is_blink = "blink" in st
        is_terror = st in ("terror_open", "grenade_mouth")
        rx = 104 if is_terror else 84
        ry = 114 if is_terror else 94
        top_r, bot_r = (0.5, 0.5) if is_blink else (0.0, 1.0)
        pdy = 28 if st == "patrol_down" else 0
        pscale = 0.42 if is_terror else 0.92
        if st == "creepy_grin_1":
            top_r, bot_r = 0.25, 0.92
        elif st == "creepy_grin_2":
            top_r, bot_r = 0.35, 0.88

        for sx in (-1, 1):
            ex = 768 + sx * 175
            if st == "wild_squint_grin":
                d = ImageDraw.Draw(im)
                # Gleeful squinted V/crescent eyes
                ink_line(d, [(ex - sx * 72, eye_y - 16), (ex + sx * 52, eye_y + 12), (ex - sx * 68, eye_y + 38)], width=16)
            else:
                im = draw_clipped_eye(im, ex, eye_y, rx, ry, top_r, bot_r, 0, pdy, pscale, veins=(st == "grenade_mouth"))

        d = ImageDraw.Draw(im)
        # Brows
        for sx in (-1, 1):
            bx = 768 + sx * 175
            if is_terror:
                ink_line(d, [(bx - sx * 66, 610), (bx + sx * 66, 575)], width=16)
            elif st.startswith("creepy") or st == "wild_squint_grin":
                ink_line(d, [(bx - sx * 74, 622), (bx + sx * 70, 668)], width=18)
            elif st == "patrol_down":
                ink_line(d, [(bx - 64, 650), (bx + 64, 664)], width=15)
            else:
                ink_line(d, [(bx - 64, 642), (bx + 64, 636)], width=15)

        # Mouth
        my = 1020
        if st in ("patrol_open", "patrol_blink", "patrol_down"):
            ink_line(d, [(695, my), (768, my + 12), (842, my)], width=14)
        elif st == "terror_open":
            d.ellipse((662, my - 72, 874, my + 98), fill="#26171a", outline=INK, width=12)
            d.rounded_rectangle((692, my - 60, 844, my - 26), radius=10, fill="#fffdf7")
            d.ellipse((712, my + 24, 824, my + 86), fill="#d9596b")
        elif st == "grenade_mouth":
            # Cavernous mouth ready for 3D grenade insertion
            d.ellipse((596, my - 115, 940, my + 150), fill="#201114", outline=INK, width=14)
            d.ellipse((650, my + 55, 886, my + 138), fill="#ba3c4f")
        elif st == "creepy_grin_1":
            d.arc((590, my - 90, 946, my + 70), 12, 168, fill=INK, width=18)
        elif st in ("creepy_grin_2", "wild_squint_grin"):
            # Clip teeth grid strictly inside the chord mouth shape
            m_mask = Image.new("L", (N, N), 0)
            ImageDraw.Draw(m_mask).chord((568, my - 96, 968, my + 130), 0, 180, fill=255)
            teeth_layer = canvas()
            td = ImageDraw.Draw(teeth_layer)
            td.chord((568, my - 96, 968, my + 130), 0, 180, fill="#fffdf7")
            for tx in range(620, 920, 60):
                td.line([(tx, my - 4), (tx, my + 135)], fill=INK, width=7)
            td.line([(568, my + 52), (968, my + 52)], fill=INK, width=7)
            teeth_layer.putalpha(m_mask)
            im = Image.alpha_composite(im, teeth_layer)
            d = ImageDraw.Draw(im)
            d.chord((568, my - 96, 968, my + 130), 0, 180, outline=INK, width=14)

        im.save(ART / f"enemy_face_{st}.png")


def build_fx_and_hud():
    # Sweat droplet (256x384)
    sw = Image.new("RGBA", (256, 384), INK_RGBA)
    sd = ImageDraw.Draw(sw)
    sd.polygon(
        [(128, 16), (206, 190), (204, 268), (168, 336), (112, 344), (62, 296), (54, 212)],
        fill="#5bc8ff",
        outline=INK,
        width=9,
    )
    sd.ellipse((84, 195, 118, 258), fill="#e0f8ff")
    sw.save(ART / "sweat_drop.png")

    # Vapor wisp (256x256) & sand puff (256x256)
    yy, xx = np.mgrid[:256, :256]
    r = np.sqrt(((xx - 127.5) / 127.5) ** 2 + ((yy - 127.5) / 127.5) ** 2)
    for fname, col, peak in [("vapor_wisp.png", (236, 250, 255), 170), ("sand_puff.png", (223, 190, 138), 215)]:
        arr = np.zeros((256, 256, 4), dtype=np.uint8)
        arr[:, :, :3] = col
        arr[:, :, 3] = (np.clip(1.0 - r, 0.0, 1.0) ** 2.2 * peak).astype(np.uint8)
        Image.fromarray(arr).save(ART / fname)

    # Top-8% screen-space hook badge (1080x1920), visible ONLY Frames 1-105
    hud = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hud)
    pill_box = (115, 74, 965, 164)
    hd.rounded_rectangle(pill_box, radius=34, fill=(20, 28, 43, 236), outline="#f5c542", width=4)
    f = ImageFont.truetype(FONT_BOLD, 38)
    hd.text((540, 119), "WW2 BAMBOO AMBUSH TACTIC", font=f, anchor="mm", fill="#fff9eb")
    hud.save(ART / "hud_hook.png")


def main():
    build_soldier_head()
    build_enemy_head()
    build_soldier_torso()
    build_enemy_torso()
    build_soldier_faces()
    build_enemy_faces()
    build_fx_and_hud()
    print(f"Generated 1536x1536 shaded cel assets and HUD in {ART}")


if __name__ == "__main__":
    main()
