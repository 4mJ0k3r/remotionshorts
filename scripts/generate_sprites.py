import os
import math
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = "D:/remotionshorts/output/sprites"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Color Constants
INK_COLOR = (22, 18, 25, 255)          # #161219 bold ink
CLEAR_CANVAS = (22, 18, 25, 0)         # Dark ink RGB with 0 alpha (prevents white halo!)
CREAM_HEAD = (253, 250, 242, 255)      # #fdfaf2
SHADOW_CRESCENT = (216, 226, 236, 255) # #d8e2ec 15% cool grey-blue
PEACH_HEAD = (255, 210, 204, 255)      # #ffd2cc
PANIC_HEAD = (208, 232, 255, 255)      # #d0e8ff
NAVY_SHORTS = (29, 45, 68, 255)        # #1d2d44
PLAID_BASE = (58, 157, 93, 255)        # #3a9d5d
PLAID_DARK = (36, 106, 60, 255)        # #246a3c
PLAID_LIGHT = (234, 244, 236, 255)     # #eaf4ec
SWEAT_BLUE = (77, 166, 255, 255)
CHESTNUT_HAIR = (92, 51, 23, 255)      # #5c3317
PINK_BAND = (255, 107, 157, 255)
CORAL_BLAZER = (240, 113, 103, 255)

def get_head_polygons(cx=512, cy=360, R=210, steps=120):
    inner_pts = []
    outer_pts = []
    for i in range(steps):
        a = 2.0 * math.pi * i / steps
        r_mid = R * (1.0 + 0.013 * math.sin(2.0 * a + 0.6)
                         - 0.009 * math.cos(3.0 * a - 0.8)
                         + 0.005 * math.sin(5.0 * a + 1.9))
        w = 16.0 * (1.0 + 0.24 * math.cos(a - 2.3)
                        + 0.11 * math.sin(3.0 * a + 1.1)
                        + 0.07 * math.cos(5.0 * a - 0.6))
        r_in = r_mid - w / 2.0
        r_out = r_mid + w / 2.0
        inner_pts.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a)))
        outer_pts.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
    return inner_pts, outer_pts

def draw_head_base(img, head_color, cx=512, cy=360, R=210):
    inner_pts, outer_pts = get_head_polygons(cx, cy, R)

    # 1. Inner head layer with shadow crescent
    head_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(head_layer)
    h_draw.polygon(inner_pts, fill=SHADOW_CRESCENT)

    mask = Image.new("L", img.size, 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.polygon(inner_pts, fill=255)

    offset_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(offset_layer)
    offset_pts = [(x + 28, y - 20) for x, y in inner_pts]
    o_draw.polygon(offset_pts, fill=head_color)
    o_draw.ellipse([cx - R + 28, cy - R - 20, cx + R + 28, cy + R - 20], fill=head_color)

    head_layer.paste(offset_layer, (0, 0), mask)
    img.alpha_composite(head_layer)

    # 2. Bold outer ink ring
    ring_poly = outer_pts + inner_pts[::-1]
    r_draw = ImageDraw.Draw(img)
    r_draw.polygon(ring_poly, fill=INK_COLOR)

    return inner_pts

def draw_torso_and_legs(img, is_hero=True, blazer_color=None):
    draw = ImageDraw.Draw(img)

    # Legs & Shoes
    leg_width = 20
    draw.line([(440, 960), (410, 1220), (400, 1430)], fill=INK_COLOR, width=leg_width, joint="curve")
    draw.line([(584, 960), (614, 1220), (624, 1430)], fill=INK_COLOR, width=leg_width, joint="curve")

    draw.rounded_rectangle([340, 1410, 440, 1460], radius=22, fill=INK_COLOR)
    draw.rounded_rectangle([580, 1410, 680, 1460], radius=22, fill=INK_COLOR)

    torso_box = [390, 555, 634, 920]
    radius = 75

    if is_hero:
        pill_mask = Image.new("L", img.size, 0)
        pm_draw = ImageDraw.Draw(pill_mask)
        pm_draw.rounded_rectangle(torso_box, radius=radius, fill=255)

        plaid_layer = Image.new("RGBA", img.size, PLAID_BASE)
        p_draw = ImageDraw.Draw(plaid_layer)

        step = 36
        for x in range(350, 680, step):
            p_draw.line([(x, 500), (x, 950)], fill=PLAID_DARK, width=8)
        for y in range(520, 950, step):
            p_draw.line([(350, y), (680, y)], fill=PLAID_DARK, width=8)

        for x in range(350 + step // 2, 680, step):
            p_draw.line([(x, 500), (x, 950)], fill=PLAID_LIGHT, width=3)
        for y in range(520 + step // 2, 950, step):
            p_draw.line([(350, y), (680, y)], fill=PLAID_LIGHT, width=3)

        torso_masked = Image.new("RGBA", img.size, CLEAR_CANVAS)
        torso_masked.paste(plaid_layer, (0, 0), pill_mask)
        img.alpha_composite(torso_masked)

        draw.rounded_rectangle(torso_box, radius=radius, outline=INK_COLOR, width=14)

        # Shorts (y: 890..1040)
        draw.rounded_rectangle([380, 890, 500, 1040], radius=25, fill=NAVY_SHORTS, outline=INK_COLOR, width=14)
        draw.rounded_rectangle([524, 890, 644, 1040], radius=25, fill=NAVY_SHORTS, outline=INK_COLOR, width=14)
        draw.rectangle([440, 890, 584, 980], fill=NAVY_SHORTS)
        draw.line([(380, 890), (644, 890)], fill=INK_COLOR, width=14)
        draw.line([(500, 1040), (512, 975), (524, 1040)], fill=INK_COLOR, width=14)
    else:
        blazer_col = blazer_color or CORAL_BLAZER
        draw.rounded_rectangle(torso_box, radius=radius, fill=blazer_col, outline=INK_COLOR, width=14)
        # White blouse collar
        draw.polygon([(465, 560), (512, 680), (559, 560)], fill=(252, 252, 255, 255), outline=INK_COLOR, width=8)
        # Lapel lines
        draw.line([(450, 560), (490, 700), (512, 920)], fill=INK_COLOR, width=10)
        draw.line([(574, 560), (534, 700), (512, 920)], fill=INK_COLOR, width=10)
        # Skirt
        draw.rounded_rectangle([380, 890, 644, 1040], radius=25, fill=(45, 40, 65, 255), outline=INK_COLOR, width=14)

def draw_sweat_drop(draw, cx, cy, size=24):
    pts = [
        (cx, cy - size * 1.3),
        (cx + size * 0.7, cy),
        (cx + size * 0.5, cy + size * 0.7),
        (cx, cy + size * 0.9),
        (cx - size * 0.5, cy + size * 0.7),
        (cx - size * 0.7, cy),
    ]
    draw.polygon(pts, fill=SWEAT_BLUE, outline=INK_COLOR)
    draw.ellipse([cx - size * 0.3, cy - size * 0.1, cx - size * 0.1, cy + size * 0.3], fill=(255, 255, 255, 220))

def generate_hero_calm():
    img = Image.new("RGBA", (1024, 1536), CLEAR_CANVAS)
    draw_torso_and_legs(img, is_hero=True)
    draw_head_base(img, CREAM_HEAD)

    draw = ImageDraw.Draw(img)
    # Calm oval pupils with white highlight
    draw.ellipse([436, 330, 464, 370], fill=INK_COLOR)
    draw.ellipse([442, 338, 450, 348], fill=(255, 255, 255, 255))

    draw.ellipse([560, 330, 588, 370], fill=INK_COLOR)
    draw.ellipse([566, 338, 574, 348], fill=(255, 255, 255, 255))

    draw.arc([430, 290, 474, 316], start=190, end=350, fill=INK_COLOR, width=10)
    draw.arc([550, 290, 594, 316], start=190, end=350, fill=INK_COLOR, width=10)

    # Small focused mouth
    draw.arc([492, 420, 532, 450], start=20, end=160, fill=INK_COLOR, width=9)

    # Left arm resting on desk
    draw.line([(395, 620), (330, 750), (400, 830)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([380, 810, 425, 855], fill=CREAM_HEAD, outline=INK_COLOR, width=10)

    # Right arm writing
    draw.line([(629, 620), (690, 740), (590, 820)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([570, 800, 615, 845], fill=CREAM_HEAD, outline=INK_COLOR, width=10)

    # Yellow pencil
    draw.line([(560, 860), (640, 770)], fill=(245, 180, 40, 255), width=12)
    draw.line([(550, 872), (562, 858)], fill=INK_COLOR, width=10)
    draw.line([(635, 776), (648, 762)], fill=(240, 120, 140, 255), width=12)

    path = os.path.join(OUTPUT_DIR, "hero_calm.png")
    img.save(path)
    print("Saved:", path)

def generate_hero_oops():
    img = Image.new("RGBA", (1024, 1536), CLEAR_CANVAS)
    draw_torso_and_legs(img, is_hero=True)
    draw_head_base(img, PEACH_HEAD)

    draw = ImageDraw.Draw(img)
    # Wide shocked oval pupils
    draw.ellipse([424, 314, 468, 376], fill=INK_COLOR)
    draw.ellipse([432, 324, 444, 338], fill=(255, 255, 255, 255))

    draw.ellipse([556, 314, 600, 376], fill=INK_COLOR)
    draw.ellipse([564, 324, 576, 338], fill=(255, 255, 255, 255))

    draw.arc([420, 260, 474, 292], start=190, end=350, fill=INK_COLOR, width=12)
    draw.arc([550, 260, 604, 292], start=190, end=350, fill=INK_COLOR, width=12)

    # Small O mouth
    draw.ellipse([496, 420, 528, 462], fill=(120, 30, 40, 255), outline=INK_COLOR, width=10)

    # Shock blush marks
    draw.line([(390, 385), (415, 395)], fill=(240, 100, 100, 200), width=6)
    draw.line([(400, 395), (425, 405)], fill=(240, 100, 100, 200), width=6)
    draw.line([(610, 395), (635, 385)], fill=(240, 100, 100, 200), width=6)
    draw.line([(600, 405), (625, 395)], fill=(240, 100, 100, 200), width=6)

    # Arms jolting up slightly
    draw.line([(395, 620), (320, 710), (360, 780)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([345, 765, 390, 810], fill=PEACH_HEAD, outline=INK_COLOR, width=10)

    draw.line([(629, 620), (704, 710), (664, 780)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([634, 765, 679, 810], fill=PEACH_HEAD, outline=INK_COLOR, width=10)

    path = os.path.join(OUTPUT_DIR, "hero_oops.png")
    img.save(path)
    print("Saved:", path)

def generate_hero_panic():
    img = Image.new("RGBA", (1024, 1536), CLEAR_CANVAS)
    draw_torso_and_legs(img, is_hero=True)
    draw_head_base(img, PANIC_HEAD)

    draw = ImageDraw.Draw(img)
    # Tiny pinprick pupils
    draw.ellipse([442, 335, 458, 351], fill=INK_COLOR)
    draw.ellipse([566, 335, 582, 351], fill=INK_COLOR)
    draw.arc([430, 320, 470, 365], start=0, end=360, fill=INK_COLOR, width=4)
    draw.arc([554, 320, 594, 365], start=0, end=360, fill=INK_COLOR, width=4)

    # Slanted desperate worry eyebrows
    draw.line([(426, 290), (476, 268)], fill=INK_COLOR, width=12)
    draw.line([(598, 290), (548, 268)], fill=INK_COLOR, width=12)

    # Gridded clenched-teeth grimace:
    # white rounded rect x: 432..592, y: 430..486 with #161219 border, horizontal center line, and 4 vertical tooth lines
    draw.rounded_rectangle([432, 430, 592, 486], radius=14, fill=(255, 255, 255, 255), outline=INK_COLOR, width=10)
    draw.line([(436, 458), (588, 458)], fill=INK_COLOR, width=6)
    step = (592 - 432) / 5.0
    for i in range(1, 5):
        tx = int(432 + i * step)
        draw.line([(tx, 434), (tx, 482)], fill=INK_COLOR, width=6)

    # 3 blue sweat drops near temples
    draw_sweat_drop(draw, 340, 270, size=26)
    draw_sweat_drop(draw, 320, 340, size=22)
    draw_sweat_drop(draw, 680, 280, size=24)

    # Forehead dread lines
    for lx in range(480, 545, 12):
        draw.line([(lx, 220), (lx, 260)], fill=(70, 110, 170, 220), width=5)

    # Rigid trembling stick arms clutching head
    draw.line([(395, 620), (310, 550), (350, 430)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([335, 410, 380, 455], fill=PANIC_HEAD, outline=INK_COLOR, width=10)

    draw.line([(629, 620), (714, 550), (674, 430)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([644, 410, 689, 455], fill=PANIC_HEAD, outline=INK_COLOR, width=10)

    path = os.path.join(OUTPUT_DIR, "hero_panic.png")
    img.save(path)
    print("Saved:", path)

def draw_crush_back_hair(draw, cx=512, cy=360, R=210):
    # Drawn BEHIND head
    # Voluminous chestnut hair mass
    draw.rounded_rectangle([cx - R - 35, cy - R - 30, cx + R + 35, cy + R + 90], radius=120, fill=CHESTNUT_HAIR, outline=INK_COLOR, width=14)

def draw_crush_front_hair_and_band(draw, cx=512, cy=360, R=210):
    # Drawn ON TOP of head, framing face cleanly
    # Pink headband across hair top (y: 155..215)
    draw.arc([cx - R + 10, cy - R - 25, cx + R - 10, cy - 80], start=190, end=350, fill=PINK_BAND, width=26)

    # Bangs / Fringe along forehead (above eyebrows y=290): y: 190..260
    draw.polygon([
        (cx - 150, 210),
        (cx - 90, 265),
        (cx - 40, 240),
        (cx + 20, 270),
        (cx + 90, 235),
        (cx + 150, 255),
        (cx + 160, 200),
        (cx - 150, 200)
    ], fill=CHESTNUT_HAIR, outline=INK_COLOR)

    # Side hair locks framing face (outside eyes, leaving face 100% open!)
    # Left lock
    draw.polygon([
        (cx - R + 10, 220),
        (cx - R - 25, 360),
        (cx - R + 15, 520),
        (cx - R + 45, 500),
        (cx - R + 15, 360),
        (cx - R + 40, 240)
    ], fill=CHESTNUT_HAIR, outline=INK_COLOR)

    # Right lock
    draw.polygon([
        (cx + R - 10, 220),
        (cx + R + 25, 360),
        (cx + R - 15, 520),
        (cx + R - 45, 500),
        (cx + R - 15, 360),
        (cx + R - 40, 240)
    ], fill=CHESTNUT_HAIR, outline=INK_COLOR)

def generate_crush_write():
    img = Image.new("RGBA", (1024, 1536), CLEAR_CANVAS)
    draw_torso_and_legs(img, is_hero=False)

    draw_crush_back_hair(ImageDraw.Draw(img))
    draw_head_base(img, CREAM_HEAD)

    draw = ImageDraw.Draw(img)
    draw_crush_front_hair_and_band(draw)

    # Calm writing face
    # Half closed downward eyes
    draw.arc([430, 335, 474, 365], start=20, end=160, fill=INK_COLOR, width=10)
    draw.ellipse([444, 345, 460, 362], fill=INK_COLOR)

    draw.arc([550, 335, 594, 365], start=20, end=160, fill=INK_COLOR, width=10)
    draw.ellipse([564, 345, 580, 362], fill=INK_COLOR)

    # Gentle focused eyebrows
    draw.arc([426, 295, 474, 320], start=190, end=350, fill=INK_COLOR, width=9)
    draw.arc([550, 295, 598, 320], start=190, end=350, fill=INK_COLOR, width=9)

    # Small calm smile
    draw.arc([495, 425, 530, 450], start=10, end=170, fill=INK_COLOR, width=8)

    # Arms writing
    draw.line([(395, 620), (340, 750), (420, 830)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([405, 810, 445, 850], fill=CREAM_HEAD, outline=INK_COLOR, width=10)

    draw.line([(629, 620), (680, 750), (580, 825)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([565, 805, 605, 845], fill=CREAM_HEAD, outline=INK_COLOR, width=10)
    draw.line([(550, 860), (620, 780)], fill=(50, 50, 150, 255), width=10)

    path = os.path.join(OUTPUT_DIR, "crush_write.png")
    img.save(path)
    print("Saved:", path)

def generate_crush_glare():
    img = Image.new("RGBA", (1024, 1536), CLEAR_CANVAS)
    draw_torso_and_legs(img, is_hero=False)

    draw_crush_back_hair(ImageDraw.Draw(img))
    draw_head_base(img, CREAM_HEAD)

    draw = ImageDraw.Draw(img)
    draw_crush_front_hair_and_band(draw)

    # Half-lidded disgusted glare:
    # Angled angry eyebrows pointing down inwards towards center
    draw.line([(410, 280), (480, 320)], fill=INK_COLOR, width=14)
    draw.line([(614, 280), (544, 320)], fill=INK_COLOR, width=14)

    # Eye sockets (white sclera)
    draw.ellipse([424, 325, 476, 375], fill=(255, 255, 255, 255), outline=INK_COLOR, width=8)
    draw.ellipse([548, 325, 600, 375], fill=(255, 255, 255, 255), outline=INK_COLOR, width=8)

    # Pupils glaring HARD to the left (towards hero)
    draw.ellipse([426, 335, 448, 365], fill=INK_COLOR)
    draw.ellipse([550, 335, 572, 365], fill=INK_COLOR)

    # Half-lidded eyelids cutting top half of eyes
    draw.chord([420, 318, 480, 355], start=180, end=360, fill=CREAM_HEAD, outline=INK_COLOR, width=9)
    draw.chord([544, 318, 604, 355], start=180, end=360, fill=CREAM_HEAD, outline=INK_COLOR, width=9)

    # Disgusted wavy sneer mouth
    draw.arc([475, 435, 545, 475], start=190, end=350, fill=INK_COLOR, width=12)
    # Nose scrunched disgust wrinkle
    draw.line([(495, 360), (505, 375)], fill=INK_COLOR, width=6)
    draw.line([(525, 360), (515, 375)], fill=INK_COLOR, width=6)

    # Hand pinching nose / pulling collar away in disgust!
    draw.line([(395, 620), (330, 710), (450, 680)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([430, 660, 475, 705], fill=CREAM_HEAD, outline=INK_COLOR, width=10)

    draw.line([(629, 620), (690, 750), (620, 830)], fill=INK_COLOR, width=20, joint="curve")
    draw.ellipse([605, 810, 645, 850], fill=CREAM_HEAD, outline=INK_COLOR, width=10)

    path = os.path.join(OUTPUT_DIR, "crush_glare.png")
    img.save(path)
    print("Saved:", path)

def generate_stink_ribbon():
    # 512 x 1024 wavy lime-green ribbon
    img = Image.new("RGBA", (512, 1024), CLEAR_CANVAS)
    draw = ImageDraw.Draw(img)

    STINK_GREEN = (122, 229, 72, 255) # #7ae548

    pts_left = []
    pts_right = []
    for y in range(50, 980, 10):
        offset = 70.0 * math.sin(y * 0.016) + 30.0 * math.cos(y * 0.038)
        w = 60.0 * (y / 980.0) + 20.0
        cx = 256 + offset
        pts_left.append((cx - w/2.0, y))
        pts_right.append((cx + w/2.0, y))

    polygon = pts_left + pts_right[::-1]
    draw.polygon(polygon, fill=STINK_GREEN, outline=INK_COLOR)

    pts_center = [((pl[0] + pr[0])/2.0, pl[1]) for pl, pr in zip(pts_left, pts_right)]
    for i in range(len(pts_center) - 1):
        if i % 3 != 0:
            draw.line([pts_center[i], pts_center[i+1]], fill=(200, 255, 140, 240), width=6)

    # Add a few noxious fume bubbles along ribbon
    draw.ellipse([210, 250, 270, 310], fill=STINK_GREEN, outline=INK_COLOR, width=6)
    draw.ellipse([290, 520, 360, 590], fill=STINK_GREEN, outline=INK_COLOR, width=6)
    draw.ellipse([170, 780, 250, 860], fill=STINK_GREEN, outline=INK_COLOR, width=7)

    path = os.path.join(OUTPUT_DIR, "stink_ribbon.png")
    img.save(path)
    print("Saved:", path)

def generate_sweat_card():
    img = Image.new("RGBA", (256, 256), CLEAR_CANVAS)
    draw = ImageDraw.Draw(img)
    draw_sweat_drop(draw, 128, 128, size=75)
    path = os.path.join(OUTPUT_DIR, "sweat_drop.png")
    img.save(path)
    print("Saved:", path)

if __name__ == "__main__":
    generate_hero_calm()
    generate_hero_oops()
    generate_hero_panic()
    generate_crush_write()
    generate_crush_glare()
    generate_stink_ribbon()
    generate_sweat_card()
    print("All sprites updated successfully!")
