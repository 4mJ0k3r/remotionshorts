"""Generate 1024x1024 RGBA character head/torso cards, gridded clenched teeth, 20 top HUD pills, translucent steam & vignette."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'renders' / 'farmer_owns_train'
ART = OUT / 'assets'

INK = '#23140d'
INK_RGBA = (35, 20, 13, 0)
CREAM = '#fffdf7'
EYE_INK = '#1c1417'

HUD_TEXTS = [
    "2017 PUNJAB: THE IMPOSSIBLE OWNER",
    "OWNER OF FULL SHATABDI EXPRESS!",
    "TOTAL COST SPENT: ZERO RUPEES",
    "HOW DID HE GET A WHOLE TRAIN?",
    "NORMAL LOAN DEFAULT: BANK TAKES CAR",
    "COMMON MAN LOSES EVERYTHING!",
    "PLOT TWIST: UNO REVERSE ON RAILWAYS!",
    "UNPAID LAND COMPENSATION: 1.05 CRORE",
    "IGNORED FOR YEARS BY OFFICIALS",
    "LUDHIANA COURT: FINAL WARNING",
    "COURT ORDER: SEIZE THE TRAIN!",
    "DESTINATION: LUDHIANA STATION",
    "TRAIN 12029: 2-MINUTE HALT",
    "COURT BAILIFF STEPS ONTO PLATFORM",
    "OFFICIAL ATTACHMENT ORDER SERVED!",
    "LOCO PILOT IN TOTAL SHOCK!",
    "LEGAL OWNER: SAMPURAN SINGH!",
    "FOR THE PASSENGERS: 1-DAY LOAN",
    "FARMER FLAGS OFF HIS OWN TRAIN!",
    "THE FARMER WHO OWNED A TRAIN",
]


def organic_head_polygons(cx=512, cy=540, rx=356, ry=348, stroke=15):
    outer, inner = [], []
    for i in range(300):
        a = i * math.tau / 300
        wobble = 1.0 + 0.016 * math.sin(2 * a + 0.5) - 0.011 * math.cos(3 * a - 0.7) + 0.006 * math.sin(5 * a + 1.4)
        ox = cx + (rx * wobble + stroke * 0.5) * math.cos(a)
        oy = cy + (ry * wobble + stroke * 0.5) * math.sin(a)
        ix = cx + (rx * wobble - stroke * 0.5) * math.cos(a)
        iy = cy + (ry * wobble - stroke * 0.5) * math.sin(a)
        outer.append((ox, oy))
        inner.append((ix, iy))
    return outer, inner


def apply_crescent(image, mask, shift=(54, -38), blur=9):
    shifted = ImageChops.offset(mask, shift[0], shift[1])
    crescent = ImageChops.subtract(mask, shifted).filter(ImageFilter.GaussianBlur(blur))
    shadow = Image.new('RGBA', image.size, (46, 62, 92, 38))
    shadow.putalpha(ImageChops.multiply(crescent, shadow.getchannel('A')))
    return Image.alpha_composite(image, shadow)


def draw_hair_and_hat(kind, d, im, inner_poly):
    if kind == 'farmer':
        d.ellipse((128, 120, 896, 545), fill=INK)
        d.ellipse((144, 136, 880, 528), fill='#ff7b00')
        for arc_box, col in [
            ((152, 150, 868, 490), '#e06600'),
            ((168, 185, 852, 510), '#ffa200'),
            ((185, 220, 835, 530), '#ff8800'),
        ]:
            d.arc(arc_box, start=188, end=352, fill=INK, width=14)
            d.arc((arc_box[0] + 6, arc_box[1] + 6, arc_box[2] - 6, arc_box[3] - 6), start=190, end=350, fill=col, width=22)
        d.polygon([(512, 345), (390, 210), (634, 210)], fill='#ff9500', outline=INK, width=14)
        d.polygon([(462, 348), (512, 275), (562, 348)], fill='#fffdf7', outline=INK, width=12)
        beard_layer = Image.new('RGBA', im.size, INK_RGBA)
        bd = ImageDraw.Draw(beard_layer)
        bd.chord((162, 465, 862, 915), start=8, end=172, fill='#e2e8f0', outline=INK, width=15)
        bd.arc((235, 585, 789, 865), start=20, end=160, fill='#94a3b8', width=10)
        head_mask = Image.new('L', im.size, 0)
        ImageDraw.Draw(head_mask).polygon(inner_poly, fill=255)
        im = Image.alpha_composite(im, beard_layer)
        d = ImageDraw.Draw(im)
        d.chord((285, 608, 520, 710), start=180, end=360, fill='#cbd5e1', outline=INK, width=13)
        d.chord((504, 608, 739, 710), start=180, end=360, fill='#cbd5e1', outline=INK, width=13)
    elif kind == 'judge':
        for side_box in [(130, 285, 275, 520), (749, 285, 894, 520)]:
            d.ellipse(side_box, fill='#e5e7eb', outline=INK, width=14)
        d.chord((158, 175, 866, 460), start=180, end=360, fill='#f3f4f6', outline=INK, width=14)
    elif kind == 'bailiff':
        d.chord((150, 175, 874, 430), start=180, end=360, fill='#8c7355', outline=INK, width=15)
        d.rounded_rectangle((132, 310, 892, 372), radius=22, fill='#5c4730', outline=INK, width=14)
        d.ellipse((468, 225, 556, 315), fill='#facc15', outline=INK, width=11)
        d.chord((335, 622, 515, 692), start=180, end=360, fill='#2b1d14', outline=INK, width=11)
        d.chord((509, 622, 689, 692), start=180, end=360, fill='#2b1d14', outline=INK, width=11)
    elif kind == 'loco_pilot':
        d.chord((148, 165, 876, 425), start=180, end=360, fill='#1e3a8a', outline=INK, width=15)
        d.rounded_rectangle((128, 308, 896, 368), radius=22, fill='#0f172a', outline=INK, width=14)
        d.line((150, 312, 874, 312), fill='#facc15', width=12)
        d.ellipse((465, 215, 559, 302), fill='#ef4444', outline='#facc15', width=10)
    elif kind == 'bank_officer':
        d.chord((152, 170, 872, 470), start=178, end=362, fill='#1e293b', outline=INK, width=15)
        d.polygon([(265, 310), (355, 235), (410, 325)], fill=CREAM)
        d.line((355, 235, 410, 325), fill=INK, width=12)
    else:
        d.chord((156, 178, 868, 465), start=180, end=360, fill='#3b2314', outline=INK, width=15)
        d.polygon([(465, 195), (505, 125), (548, 190)], fill='#3b2314', outline=INK, width=13)
    return im


def head(kind, expression):
    im = Image.new('RGBA', (1024, 1024), INK_RGBA)
    d = ImageDraw.Draw(im)
    outer, inner = organic_head_polygons()
    for ex_l, ex_r in [(82, 232), (792, 942)]:
        d.ellipse((ex_l, 468, ex_r, 642), fill=INK)
        d.ellipse((ex_l + 15, 483, ex_r - 15, 627), fill=CREAM)
    d.polygon(outer, fill=INK)
    d.polygon(inner, fill=CREAM)
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).polygon(inner, fill=255)
    im = apply_crescent(im, mask)
    d = ImageDraw.Draw(im)
    im = draw_hair_and_hat(kind, d, im, inner)
    d = ImageDraw.Draw(im)

    eye_y_base = 505 if kind == 'farmer' else 495
    for s, x in enumerate([352, 672]):
        if expression == 'blink' or (expression == 'wink' and s == 1):
            d.arc((x - 50, eye_y_base + 24, x + 50, eye_y_base + 84), start=190, end=350, fill=INK, width=16)
        elif expression == 'shock':
            d.ellipse((x - 46, eye_y_base - 50, x + 46, eye_y_base + 112), fill=EYE_INK)
        elif expression == 'panic':
            d.ellipse((x - 42, eye_y_base - 32, x + 42, eye_y_base + 104), fill=EYE_INK)
        else:
            ew = 34
            d.ellipse((x - ew, eye_y_base - 6, x + ew, eye_y_base + 106), fill=EYE_INK)
            if expression in ('smirk', 'wink'):
                d.rectangle((x - 46, eye_y_base - 14, x + 46, eye_y_base + 22), fill=CREAM)
                d.line((x - 48, eye_y_base + 22, x + 48, eye_y_base + 26), fill=INK, width=14)

        if kind == 'judge':
            d.ellipse((x - 95, eye_y_base - 52, x + 95, eye_y_base + 142), outline='#343747', width=12)
        elif kind == 'bank_officer':
            d.rounded_rectangle((x - 96, eye_y_base - 40, x + 96, eye_y_base + 128), radius=24, outline='#1e293b', width=12)

        brow_y = eye_y_base - 95
        if expression == 'angry':
            y_left = brow_y - 18 if s == 0 else brow_y + 38
            y_right = brow_y + 38 if s == 0 else brow_y - 18
            d.line((x - 64, y_left, x + 64, y_right), fill=INK, width=20)
        elif expression == 'panic':
            d.line((x - 60, brow_y + (42 if s else 0), x + 60, brow_y + (0 if s else 42)), fill=INK, width=18)
        elif expression == 'shock':
            d.arc((x - 66, brow_y - 58, x + 66, brow_y + 24), 185, 355, fill=INK, width=18)
        elif expression == 'worry':
            d.arc((x - 62, brow_y - 25, x + 62, brow_y + 55), 195, 345, fill=INK, width=15)
        elif expression in ('smirk', 'wink'):
            d.line((x - 56, brow_y + (s * 22), x + 56, brow_y + 24 - (s * 22)), fill=INK, width=16)
        else:
            d.arc((x - 56, brow_y - 12, x + 56, brow_y + 48), 195, 345, fill=INK, width=15)

    if kind == 'judge':
        d.line((447, eye_y_base + 38, 577, eye_y_base + 38), fill='#343747', width=11)
    elif kind == 'bank_officer':
        d.line((448, eye_y_base + 38, 576, eye_y_base + 38), fill='#1e293b', width=12)

    im.save(ART / f'{kind}_{expression}.png')


def body(kind):
    im = Image.new('RGBA', (640, 1024), INK_RGBA)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((255, 0, 385, 240), radius=55, fill=INK)
    d.rounded_rectangle((271, 0, 369, 250), radius=40, fill=CREAM)
    d.rounded_rectangle((105, 155, 535, 1008), radius=190, fill=INK)
    colors = {
        'farmer': '#fffdf7',
        'judge': '#181a1f',
        'bailiff': '#9c8468',
        'loco_pilot': '#74c0fc',
        'common_man': '#e9c46a',
        'bank_officer': '#262a30',
    }
    d.rounded_rectangle((122, 174, 518, 990), radius=178, fill=colors[kind])
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((122, 174, 518, 990), 178, fill=255)
    im = apply_crescent(im, mask, shift=(40, -30), blur=8)
    d = ImageDraw.Draw(im)
    if kind == 'farmer':
        d.line((320, 174, 320, 560), fill='#cbd5e1', width=14)
        d.line((320, 174, 320, 560), fill='#64748b', width=4)
        for by in [255, 345, 435]:
            d.ellipse((310, by - 10, 330, by + 10), fill='#475569')
        d.polygon([(265, 174), (320, 232), (375, 174)], fill='#e2e8f0', outline=INK)
    elif kind == 'judge':
        d.polygon([(252, 178), (320, 365), (388, 178)], fill='#e2e8f0')
        d.polygon([(276, 260), (314, 260), (310, 445), (272, 445)], fill='#ffffff', outline='#94a3b8')
        d.polygon([(326, 260), (364, 260), (368, 445), (330, 445)], fill='#ffffff', outline='#94a3b8')
    elif kind == 'bailiff':
        d.line((320, 180, 320, 820), fill='#6e5a42', width=8)
        for px in [175, 375]:
            d.rounded_rectangle((px, 325, px + 90, 435), radius=12, outline='#5c4a35', width=7)
            d.line((px, 355, px + 90, 355), fill='#5c4a35', width=6)
        d.rectangle((122, 815, 518, 885), fill='#3b2c20', outline=INK, width=8)
        d.rounded_rectangle((285, 808, 355, 892), radius=10, fill='#eab308', outline=INK, width=7)
    elif kind == 'loco_pilot':
        d.polygon([(275, 178), (320, 255), (365, 178)], fill='#e0f2fe', outline=INK)
        d.polygon([(304, 235), (336, 235), (344, 520), (320, 565), (296, 520)], fill='#1e3a8a', outline=INK)
        d.rounded_rectangle((375, 340, 462, 448), radius=12, outline='#1e40af', width=7)
    elif kind == 'bank_officer':
        d.polygon([(248, 178), (320, 440), (392, 178)], fill='#f8fafc', outline=INK)
        d.polygon([(300, 218), (340, 218), (348, 435), (320, 480), (292, 435)], fill='#dc2626', outline=INK)
        d.line((320, 480, 320, 960), fill='#0f172a', width=10)
    elif kind == 'common_man':
        d.rounded_rectangle((368, 345, 458, 455), radius=14, outline='#b08930', width=7)
    im.save(ART / f'body_{kind}.png')


def passengers():
    for idx, (hair_c, accent_c) in enumerate([('#3b2314', '#e07a5f'), ('#1e293b', '#3b82f6'), ('#5c3a21', '#10b981')]):
        for mode in ['worry', 'smile']:
            im = Image.new('RGBA', (512, 512), INK_RGBA)
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((110, 350, 402, 520), radius=90, fill=accent_c, outline=INK, width=12)
            d.ellipse((116, 70, 396, 355), fill=CREAM, outline=INK, width=13)
            d.chord((116, 68, 396, 240), start=180, end=360, fill=hair_c, outline=INK, width=12)
            for s, ex in enumerate([205, 307]):
                d.ellipse((ex - 16, 182, ex + 16, 232), fill=EYE_INK)
                if mode == 'worry':
                    d.line((ex - 26, 168 if s == 0 else 150, ex + 26, 150 if s == 0 else 168), fill=INK, width=9)
                else:
                    d.arc((ex - 26, 150, ex + 26, 182), 195, 345, fill=INK, width=8)
            if mode == 'worry':
                d.rounded_rectangle((192, 246, 320, 302), radius=16, fill=INK)
                d.rounded_rectangle((200, 254, 312, 294), radius=10, fill='#fdfaf2')
                for tx in range(224, 300, 24):
                    d.line((tx, 255, tx, 293), fill=INK, width=5)
                d.line((200, 274, 312, 274), fill=INK, width=5)
            else:
                d.arc((192, 236, 320, 306), 12, 168, fill=INK, width=12)
            im.save(ART / f'passenger_{idx}_{mode}.png')
            if mode == 'smile':
                im.save(ART / f'passenger_{idx}.png')


def mouths_huds_steam_and_vignette():
    for state in ['smile', 'o', 'flat', 'panic', 'open', 'smirk', 'clenched']:
        for talk in range(6):
            im = Image.new('RGBA', (256, 160), INK_RGBA)
            d = ImageDraw.Draw(im)
            h = (22 + talk * 16) if state != 'o' else (90 + talk * 7)
            if state == 'clenched' or (state == 'panic' and talk <= 2):
                # elevator_leak_v3 gridded clenched teeth
                d.rounded_rectangle((18, 22, 238, 138), radius=34, fill=INK)
                d.rounded_rectangle((32, 36, 224, 124), radius=18, fill='#fdfaf2')
                for tx in range(68, 204, 34):
                    d.line((tx, 38, tx, 122), fill=INK, width=8)
                d.line((32, 80, 224, 80), fill=INK, width=7)
            elif state in ['panic', 'open']:
                bounds = (46, 8, 210, 152) if state == 'panic' else (22, 8, 234, 152)
                d.ellipse(bounds, fill=INK)
                d.rectangle((58, 20, 198, 44), fill='#fff9e7')
                d.ellipse((78, 108, 178, 145), fill='#dd6486')
            elif state == 'smirk' and talk == 0:
                d.arc((35, 35, 225, 120), 10, 155, fill=INK, width=14)
            elif state == 'flat' and talk == 0:
                d.line((35, 78, 220, 82), fill=INK, width=13)
            else:
                d.ellipse((25, 80 - h / 2, 231, 80 + h / 2), fill=INK)
                if h > 46:
                    d.rectangle((52, 80 - h / 2 + 8, 204, 80 - h / 2 + 24), fill='#fff9e7')
                    d.ellipse((80, 80 + h / 2 - 34, 190, 80 + h / 2 - 5), fill='#e97988')
            im.save(ART / f'mouth_{state}_{talk}.png')

    for i, text in enumerate(HUD_TEXTS):
        hud_im = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(hud_im)
        font_size = 32
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', font_size)
        while draw.textlength(text, font=font) > 940 and font_size > 20:
            font_size -= 1
            font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', font_size)
        width = int(draw.textlength(text, font=font)) + 58
        left = (1080 - width) // 2
        draw.rounded_rectangle((left, 134, left + width, 224), radius=29, fill='#0d1826', outline='#d4a359', width=4)
        draw.text((540, 179), text, font=font, fill='white', anchor='mm')
        hud_im.save(ART / f'hud_{i}.png')

    yy, xx = np.mgrid[-1:1:256j, -1:1:320j]
    r2 = xx * xx * 0.85 + yy * yy * 1.15
    alpha = (np.clip(np.exp(-r2 * 2.8) * (1.0 - np.clip(r2, 0.0, 1.0)), 0.0, 1.0) * 64).astype('uint8')
    steam_rgba = np.zeros((256, 320, 4), dtype='uint8')
    steam_rgba[:, :, 0] = 236
    steam_rgba[:, :, 1] = 242
    steam_rgba[:, :, 2] = 250
    steam_rgba[:, :, 3] = alpha
    Image.fromarray(steam_rgba, 'RGBA').save(ART / 'steam_puff.png')

    yy_v, xx_v = np.mgrid[-1:1:960j, -1:1:540j]
    val = (255 * (1 - 0.18 * np.clip((xx_v * xx_v + yy_v * yy_v - 0.55) / 1.45, 0, 1))).astype('uint8')
    Image.fromarray(val).convert('RGB').save(ART / 'vignette.png')


def main():
    ART.mkdir(parents=True, exist_ok=True)
    for kind in ['farmer', 'judge', 'bailiff', 'loco_pilot', 'common_man', 'bank_officer']:
        body(kind)
        for expr in ['neutral', 'smile', 'smirk', 'wink', 'worry', 'panic', 'shock', 'angry', 'blink']:
            head(kind, expr)
    passengers()
    mouths_huds_steam_and_vignette()
    print('ASSETS_GENERATED_OK', len(list(ART.glob('*.png'))))


if __name__ == '__main__':
    main()
