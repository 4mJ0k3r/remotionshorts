# ==============================================================================
# FILE: part2_scenes_5_to_7_and_calibration.py
# PROJECT: Lifetime Fart — 2.5D Story Video (Part 2: Scenes 5 to 7, f1426..2715)
# ENGINE: Blender 4.2 LTS (BLENDER_EEVEE_NEXT) | 1080x1920 @ 30fps | Z-UP
# CONTRACT: Blender v3 Visual Contract & Shared Cel-Studio Contract (§1–§7)
# ==============================================================================

import os
import sys
import site

_user_site = site.getusersitepackages()
if _user_site not in sys.path and os.path.exists(_user_site):
    sys.path.append(_user_site)
import math
from math import sin, cos, pi, radians
import bpy
import mathutils
from mathutils import Vector, Euler, Matrix

from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

# ------------------------------------------------------------------------------
# 0. GLOBAL PATHS & CONFIGURATION
# ------------------------------------------------------------------------------
PART1_BLEND_PATH = "D:/remotionshorts/output/blender/lifetime_fart_part1.blend"
FULL_BLEND_PATH = "D:/remotionshorts/output/blender/lifetime_fart_full.blend"
ASSET_DIR = "D:/remotionshorts/output/blender/cel_assets_part2"
CAL_DIR = "D:/remotionshorts/out/lifetime_fart/cal_v3"
SHEET_PATH = "D:/remotionshorts/out/lifetime_fart/sheet_v3.jpg"

if not os.path.exists("D:/"):
    BASE_OUT = os.path.abspath("./output/blender")
    BASE_QA = os.path.abspath("./out/lifetime_fart")
    PART1_BLEND_PATH = os.path.join(BASE_OUT, "lifetime_fart_part1.blend")
    FULL_BLEND_PATH = os.path.join(BASE_OUT, "lifetime_fart_full.blend")
    ASSET_DIR = os.path.join(BASE_OUT, "cel_assets_part2")
    CAL_DIR = os.path.join(BASE_QA, "cal_v3")
    SHEET_PATH = os.path.join(BASE_QA, "sheet_v3.jpg")

os.makedirs(os.path.dirname(FULL_BLEND_PATH), exist_ok=True)
os.makedirs(ASSET_DIR, exist_ok=True)
os.makedirs(CAL_DIR, exist_ok=True)
os.makedirs(os.path.dirname(SHEET_PATH), exist_ok=True)

FPS = 30
FRAME_START = 1
FRAME_END = 2715
PART2_FIRST_FRAME = 1426

# Studio Palette Constants (§1 & §7.3 Laws)
INK_RGBA = (22, 18, 25, 255)          # #161219 Bold RicksClips Ink
INK_CLEAR = (22, 18, 25, 0)           # Dark RGB zero-alpha (Zero white halo!)
CREAM_RGBA = (253, 250, 242, 255)     # #fdfaf2 Organic Cream Head
WARM_RIM_CREAM = (255, 238, 218, 255) # Meteor-lit warm cream skin
CRESCENT_RGB = (95, 118, 152)         # 15% Cool grey-blue crescent tint
SUIT_DARK = (238, 124, 42, 255)       # Hero casual orange tee
SUIT_PANTS = (38, 54, 82, 255)        # Hero dark-blue shorts
SHIRT_WHITE = (245, 246, 250, 255)
TIE_RED = (210, 45, 55, 255)
HOODIE_TEAL = (38, 118, 138, 255)
HOODIE_DARK = (24, 78, 96, 255)
JEANS_BLUE = (42, 58, 88, 255)
NEON_GREEN = (78, 255, 86, 255)
FLAME_ORANGE = (255, 115, 25, 255)
FLAME_YELLOW = (255, 225, 65, 255)


def ease_out(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 1.0 - (1.0 - u) ** 3


def event_progress(f: float, start: int, anticipate: int, extreme: int, settled: int) -> float:
    assert start < anticipate < extreme < settled
    if f <= start:
        return 0.0
    if f < anticipate:
        return -0.06 * ease_out((f - start) / (anticipate - start))
    if f < extreme:
        return -0.06 + 1.14 * ease_out((f - anticipate) / (extreme - anticipate))
    if f < settled:
        return 1.08 - 0.08 * ease_out((f - extreme) / (settled - extreme))
    return 1.0


def set_fcurve_constant_after(obj, data_path: str, settled_frame: int):
    if not obj.animation_data or not obj.animation_data.action:
        return
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == data_path:
            for kp in fc.keyframe_points:
                if kp.co.x >= settled_frame:
                    kp.interpolation = 'CONSTANT'


def enforce_constant_visibility(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path in ("hide_viewport", "hide_render"):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


def bake_event_transform(obj, start: int, anticipate: int, extreme: int, settled: int, hold_end: int,
                         loc_a=None, loc_b=None, rot_a=None, rot_b=None, scale_a=None, scale_b=None):
    for f in range(start, settled + 1):
        p = event_progress(f, start, anticipate, extreme, settled)
        if loc_a is not None and loc_b is not None:
            obj.location = Vector(loc_a).lerp(Vector(loc_b), p)
            obj.keyframe_insert(data_path="location", frame=f)
        if rot_a is not None and rot_b is not None:
            obj.rotation_euler = Euler((
                rot_a[0] + (rot_b[0] - rot_a[0]) * p,
                rot_a[1] + (rot_b[1] - rot_a[1]) * p,
                rot_a[2] + (rot_b[2] - rot_a[2]) * p,
            ), 'XYZ')
            obj.keyframe_insert(data_path="rotation_euler", frame=f)
        if scale_a is not None and scale_b is not None:
            obj.scale = Vector(scale_a).lerp(Vector(scale_b), p)
            obj.keyframe_insert(data_path="scale", frame=f)

    if loc_b is not None:
        obj.location = Vector(loc_b)
        obj.keyframe_insert(data_path="location", frame=hold_end)
        set_fcurve_constant_after(obj, "location", settled)
    if rot_b is not None:
        obj.rotation_euler = Euler(rot_b, 'XYZ')
        obj.keyframe_insert(data_path="rotation_euler", frame=hold_end)
        set_fcurve_constant_after(obj, "rotation_euler", settled)
    if scale_b is not None:
        obj.scale = Vector(scale_b)
        obj.keyframe_insert(data_path="scale", frame=hold_end)
        set_fcurve_constant_after(obj, "scale", settled)


def set_root_visibility(root_obj, col, visible_ranges):
    """Keyframes CONSTANT visibility on root, its recursive children, or collection objects."""
    if root_obj is not None and len(root_obj.children_recursive) > 0:
        all_objs = [root_obj] + list(root_obj.children_recursive)
    elif col is not None:
        all_objs = [root_obj] + list(col.objects)
    else:
        all_objs = [root_obj]

    critical_frames = {1, PART2_FIRST_FRAME - 1, PART2_FIRST_FRAME, FRAME_END}
    for s, e in visible_ranges:
        critical_frames.add(max(1, s - 1))
        critical_frames.add(s)
        critical_frames.add(e)
        critical_frames.add(min(FRAME_END, e + 1))

    for f in sorted(critical_frames):
        is_vis = any(s <= f <= e for (s, e) in visible_ranges)
        hide = not is_vis
        for o in all_objs:
            o.hide_viewport = hide
            o.hide_render = hide
            o.keyframe_insert(data_path="hide_viewport", frame=f)
            o.keyframe_insert(data_path="hide_render", frame=f)

    for o in all_objs:
        enforce_constant_visibility(o)


# ------------------------------------------------------------------------------
# 2. PIL v3 CEL-STUDIO SPRITE & GRAPHICS GENERATORS (§1, §7.1, §7.3, §7.6)
# ------------------------------------------------------------------------------
def load_font(size: int):
    candidates = [
        "C:/Windows/Fonts/NirmalaB.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/mangal.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def head_contours(cx: float, cy: float, rx: float, ry: float, count: int = 256, w0: float = 16.5):
    """Exact §1 Shared Contract rough-circle contour recipe with pressure-varying outer/inner ink."""
    outer, inner = [], []
    for i in range(count):
        a = 2.0 * pi * i / count
        r = 1.0 + 0.022 * sin(2.0 * a + 0.6) - 0.015 * cos(3.0 * a - 0.8) + 0.008 * sin(5.0 * a + 1.9)
        w = w0 * max(0.25, 1.0 + 0.52 * cos(a - 2.35) + 0.22 * sin(3.0 * a + 1.1) + 0.14 * sin(5.0 * a - 0.7))
        outer.append((cx + (rx * r + w / 2.0) * cos(a), cy + (ry * r + w / 2.0) * sin(a)))
        inner.append((cx + (rx * r - w / 2.0) * cos(a), cy + (ry * r - w / 2.0) * sin(a)))
    return outer, inner


def apply_15pct_crescent(base_rgba: Image.Image, inner_mask: Image.Image, shift_xy=(22, -18)) -> Image.Image:
    """Exact §1 / §7.3 15% cool grey-blue multiply crescent along bottom-left inner contour."""
    shifted = Image.new('L', inner_mask.size, 0)
    shifted.paste(inner_mask, shift_xy)
    crescent = ImageChops.subtract(inner_mask, shifted)
    crescent = crescent.filter(ImageFilter.GaussianBlur(5))
    crescent = ImageChops.multiply(crescent, head_inner_mask := inner_mask)

    crescent_15 = crescent.point(lambda p: int(p * 0.15))
    cool_layer = Image.new('RGBA', base_rgba.size, (CRESCENT_RGB[0], CRESCENT_RGB[1], CRESCENT_RGB[2], 255))
    darkened = ImageChops.multiply(base_rgba, cool_layer)
    return Image.composite(darkened, base_rgba, crescent_15)


def draw_clipped_eye(canvas: Image.Image, cx: int, cy: int, rx: int, ry: int,
                     lid_top_ratio: float, lid_bot_ratio: float,
                     pupil_dx: int = 0, pupil_dy: int = 0):
    """§7.3 Solid dark oval pupils clipped by horizontal eyelid aperture (top <= y <= bottom)."""
    w, h = canvas.size
    if lid_bot_ratio <= lid_top_ratio + 0.02:
        # Closed blink stroke at the closed aperture (§7.3)
        cdraw = ImageDraw.Draw(canvas)
        closed_y = int(cy - ry + (2 * ry) * 0.55)
        cdraw.line([(cx - rx - 6, closed_y), (cx + rx + 6, closed_y)], fill=INK_RGBA, width=12)
        cdraw.line([(cx - rx + 8, closed_y + 10), (cx - rx - 10, closed_y + 18)], fill=INK_RGBA, width=8)
        cdraw.line([(cx + rx - 8, closed_y + 10), (cx + rx + 10, closed_y + 18)], fill=INK_RGBA, width=8)
        return

    eye_mask = Image.new('L', (w, h), 0)
    mdraw = ImageDraw.Draw(eye_mask)
    pts = [(cx + rx * cos(2.0 * pi * i / 64.0), cy + ry * sin(2.0 * pi * i / 64.0)) for i in range(64)]
    mdraw.polygon(pts, fill=255)

    y_min, y_max = cy - ry, cy + ry
    span = max(1, y_max - y_min)
    top_y = int(y_min + span * lid_top_ratio)
    bot_y = int(y_min + span * lid_bot_ratio)

    lid_clip = Image.new('L', (w, h), 0)
    ImageDraw.Draw(lid_clip).rectangle([0, top_y, w, bot_y], fill=255)
    final_eye_mask = ImageChops.multiply(eye_mask, lid_clip)

    eye_layer = Image.new('RGBA', (w, h), INK_CLEAR)
    edraw = ImageDraw.Draw(eye_layer)
    edraw.rectangle([cx - rx - 10, y_min - 10, cx + rx + 10, y_max + 10], fill=(255, 255, 255, 255))

    prx, pry = int(rx * 0.48), int(ry * 0.56)
    px0, py0 = cx + pupil_dx - prx, cy + pupil_dy - pry
    edraw.ellipse([px0, py0, px0 + 2 * prx, py0 + 2 * pry], fill=INK_RGBA)

    eye_layer.putalpha(final_eye_mask)
    canvas.alpha_composite(eye_layer)

    cdraw = ImageDraw.Draw(canvas)
    cdraw.polygon(pts, outline=INK_RGBA, width=8)
    if lid_top_ratio > 0.04:
        cdraw.line([(cx - rx - 4, top_y), (cx + rx + 4, top_y)], fill=INK_RGBA, width=9)
    if lid_bot_ratio < 0.96:
        cdraw.line([(cx - rx - 4, bot_y), (cx + rx + 4, bot_y)], fill=INK_RGBA, width=8)


def generate_part2_head_sprite(filename: str, mode: str) -> str:
    """
    RicksClips Stickman Heads for Part 2 (1024x1024 RGBA):
    - Rough circle cream head (#fdfaf2), 15% cool grey-blue crescent shadow
    - Bold #161219 outline + 3 curved black hair strands on top
    - Solid #161219 vertical oval eyes directly on cream face (ZERO white sclera!)
    """
    W, H = 1024, 1024
    canvas = Image.new('RGBA', (W, H), INK_CLEAR)
    cx, cy = 512, 520
    rx, ry = 285, 270
    ink_col = (22, 18, 25, 255)

    if mode == 'hero_meteor_fire':
        flame_bg = Image.new('RGBA', (W, H), INK_CLEAR)
        fdraw = ImageDraw.Draw(flame_bg)
        outer_flames = [
            (512, 25), (675, 165), (815, 95), (795, 310), (935, 260),
            (855, 530), (945, 690), (775, 805), (512, 875), (249, 805),
            (79, 690), (169, 530), (89, 260), (229, 310), (209, 95), (349, 165)
        ]
        inner_flames = [
            (512, 90), (635, 210), (745, 165), (745, 345), (855, 320),
            (795, 540), (865, 660), (725, 750), (512, 815), (299, 750),
            (159, 660), (229, 540), (169, 320), (279, 345), (279, 165), (389, 210)
        ]
        fdraw.polygon(outer_flames, fill=(255, 80, 15, 235), outline=ink_col, width=10)
        fdraw.polygon(inner_flames, fill=(255, 205, 45, 240))
        canvas = Image.alpha_composite(canvas, flame_bg)

    outer, inner = head_contours(cx, cy, rx, ry, count=256, w0=17.0)
    head_outer_mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(head_outer_mask).polygon(outer, fill=255)
    head_inner_mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(head_inner_mask).polygon(inner, fill=255)

    skin_col = WARM_RIM_CREAM if mode.startswith("neighbor_") else CREAM_RGBA
    fill_layer = Image.new('RGBA', (W, H), skin_col)
    fill_layer = apply_15pct_crescent(fill_layer, head_inner_mask, shift_xy=(28, -22))
    fill_layer.putalpha(head_inner_mask)
    canvas = Image.alpha_composite(canvas, fill_layer)

    ink_band = ImageChops.subtract(head_outer_mask, head_inner_mask)
    ink_layer = Image.new('RGBA', (W, H), ink_col)
    ink_layer.putalpha(ink_band)
    canvas = Image.alpha_composite(canvas, ink_layer)

    draw = ImageDraw.Draw(canvas)

    # 3 small curved black hair strands on top
    for hx_off, hy_off, dx in [(-45, -268, -28), (5, -275, 10), (55, -265, 42)]:
        x0, y0 = cx + hx_off, cy + hy_off
        pts = [(x0, y0 + 18), (x0 + dx // 2, y0 - 28), (x0 + dx, y0 - 52)]
        draw.line(pts, fill=ink_col, width=14, joint="curve")

    tx = 18 if mode.startswith("neighbor_") else 0
    ex_L, ex_R = cx - 82 + tx, cx + 82 + tx
    ey = cy - 25
    eye_rx, eye_ry = 22, 34

    if mode == 'hero_stratosphere':
        draw.ellipse([ex_L - eye_rx, ey - eye_ry, ex_L + eye_rx, ey + eye_ry], fill=ink_col)
        draw.ellipse([ex_R - eye_rx, ey - eye_ry, ex_R + eye_rx, ey + eye_ry], fill=ink_col)
        # Frosted icy eyebrows
        draw.rounded_rectangle([ex_L - 48, ey - 85, ex_L + 42, ey - 52], radius=8,
                               fill=(205, 245, 255, 255), outline=ink_col, width=8)
        draw.rounded_rectangle([ex_R - 42, ey - 85, ex_R + 48, ey - 52], radius=8,
                               fill=(205, 245, 255, 255), outline=ink_col, width=8)
        draw.line([(cx - 48, cy + 82), (cx + 48, cy + 82)], fill=ink_col, width=13)

    elif mode in ('hero_meteor_fire', 'hero_meteor_face'):
        draw.ellipse([ex_L - eye_rx, ey - eye_ry, ex_L + eye_rx, ey + eye_ry], fill=ink_col)
        draw.ellipse([ex_R - eye_rx, ey - eye_ry, ex_R + eye_rx, ey + eye_ry], fill=ink_col)
        draw.line([(ex_L - 46, ey - 76), (ex_L + 32, ey - 48)], fill=ink_col, width=15)
        draw.line([(ex_R - 32, ey - 48), (ex_R + 46, ey - 76)], fill=ink_col, width=15)
        draw.ellipse([cx - 65, cy + 62, cx + 65, cy + 152], fill=(140, 25, 35, 255), outline=ink_col, width=12)

    elif mode == 'hero_space':
        draw.ellipse([ex_L - eye_rx, ey - eye_ry, ex_L + eye_rx, ey + eye_ry], fill=ink_col)
        draw.ellipse([ex_R - eye_rx, ey - eye_ry, ex_R + eye_rx, ey + eye_ry], fill=ink_col)
        draw.line([(ex_L - 40, ey - 66), (ex_L + 35, ey - 68)], fill=ink_col, width=13)
        draw.line([(ex_R - 35, ey - 68), (ex_R + 40, ey - 66)], fill=ink_col, width=13)
        draw.line([(cx - 48, cy + 84), (cx + 48, cy + 84)], fill=ink_col, width=12)

    elif mode in ('neighbor_pray_closed', 'neighbor_pray_talk', 'neighbor_one_eye_wish'):
        # Left eye squeezed shut (curved chevron line)
        draw.line([(ex_L - 34, ey - 10), (ex_L, ey + 8), (ex_L - 34, ey + 24)], fill=ink_col, width=13)
        # Right eye: squeezed shut in pray_closed/pray_talk, solid oval open in neighbor_one_eye_wish!
        if mode == 'neighbor_one_eye_wish':
            draw.ellipse([ex_R - eye_rx, ey - eye_ry, ex_R + eye_rx, ey + eye_ry], fill=ink_col)
        else:
            draw.line([(ex_R + 34, ey - 10), (ex_R, ey + 8), (ex_R + 34, ey + 24)], fill=ink_col, width=13)

        draw.line([(ex_L - 42, ey - 48), (ex_L + 28, ey - 74)], fill=ink_col, width=13)
        draw.line([(ex_R - 28, ey - 74), (ex_R + 42, ey - 48)], fill=ink_col, width=13)

        if mode == 'neighbor_pray_closed':
            draw.arc([cx - 48 + tx, cy + 65, cx + 48 + tx, cy + 110], start=190, end=350, fill=ink_col, width=12)
        elif mode == 'neighbor_pray_talk':
            draw.ellipse([cx - 45 + tx, cy + 68, cx + 45 + tx, cy + 128], fill=ink_col)
        elif mode == 'neighbor_one_eye_wish':
            draw.arc([cx - 58 + tx, cy + 55, cx + 58 + tx, cy + 120], start=10, end=170, fill=ink_col, width=13)

    out_path = os.path.join(ASSET_DIR, filename)
    canvas.save(out_path, "PNG")
    return out_path


def generate_part2_body_sprite(filename: str, mode: str) -> str:
    """
    RicksClips Stickman Bodies for Part 2 (1024x1536 RGBA):
    - Narrow vertical rounded pill/capsule torso (x: 432..592, width=160px; y: 435..865)
    - Thin curved #161219 stick arms and stick legs (width = 20px) with small black oval hands/shoes
    """
    W, H = 1024, 1536
    canvas = Image.new('RGBA', (W, H), INK_CLEAR)
    draw = ImageDraw.Draw(canvas)
    ink_col = (22, 18, 25, 255)
    leg_w = 20

    if mode == 'neighbor_back_point_full':
        # 3/4 Back-shoulder RicksClips Stickman pointing up at night sky
        # Stick legs
        draw.line([(472, 910), (455, 1425)], fill=ink_col, width=leg_w)
        draw.line([(552, 910), (569, 1425)], fill=ink_col, width=leg_w)
        # Left arm resting down, right stick arm raised high pointing at meteor!
        draw.line([(435, 520), (355, 760)], fill=ink_col, width=leg_w)
        draw.ellipse([330, 745, 380, 795], fill=ink_col)
        draw.line([(585, 520), (745, 355), (815, 165)], fill=ink_col, width=leg_w, joint="curve")
        draw.ellipse([790, 130, 845, 185], fill=ink_col)

        # Pill torso (teal hoodie)
        t_mask = Image.new('L', (W, H), 0)
        ImageDraw.Draw(t_mask).rounded_rectangle([422, 460, 602, 920], radius=85, fill=255)
        t_inner = t_mask.filter(ImageFilter.MinFilter(23))
        t_paint = apply_15pct_crescent(Image.new('RGBA', (W, H), HOODIE_TEAL), t_inner, shift_xy=(22, -16))
        t_PaintClip = t_paint.copy()
        t_PaintClip.putalpha(t_inner)
        canvas = Image.alpha_composite(canvas, t_PaintClip)
        t_ink = Image.new('RGBA', (W, H), ink_col)
        t_ink.putalpha(ImageChops.subtract(t_mask, t_inner))
        canvas = Image.alpha_composite(canvas, t_ink)

        # Rough-circle cream head from 3/4 back view with 3 hair strands
        outer, inner = head_contours(512, 285, 215, 205, count=256, w0=16.5)
        h_out = Image.new('L', (W, H), 0)
        ImageDraw.Draw(h_out).polygon(outer, fill=255)
        h_in = Image.new('L', (W, H), 0)
        ImageDraw.Draw(h_in).polygon(inner, fill=255)
        h_fill = apply_15pct_crescent(Image.new('RGBA', (W, H), WARM_RIM_CREAM), h_in, shift_xy=(22, -18))
        h_fill.putalpha(h_in)
        canvas = Image.alpha_composite(canvas, h_fill)
        h_ink = Image.new('RGBA', (W, H), ink_col)
        h_ink.putalpha(ImageChops.subtract(h_out, h_in))
        canvas = Image.alpha_composite(canvas, h_ink)

        cdraw = ImageDraw.Draw(canvas)
        for hx_off, hy_off, dx in [(-35, -202, -22), (5, -208, 10), (45, -200, 32)]:
            x0, y0 = 512 + hx_off, 285 + hy_off
            cdraw.line([(x0, y0 + 14), (x0 + dx, y0 - 42)], fill=ink_col, width=13)

        out_path = os.path.join(ASSET_DIR, filename)
        canvas.save(out_path, "PNG")
        return out_path

    if mode == 'hero_meteor_fire':
        f_layer = Image.new('RGBA', (W, H), INK_CLEAR)
        fdraw = ImageDraw.Draw(f_layer)
        outer_f = [
            (512, 160), (695, 320), (815, 260), (765, 580), (855, 760),
            (745, 1120), (790, 1440), (512, 1500), (234, 1440), (279, 1120),
            (169, 760), (259, 580), (209, 260), (329, 320)
        ]
        mid_f = [
            (512, 230), (645, 370), (735, 330), (705, 600), (775, 760),
            (685, 1090), (710, 1390), (512, 1450), (314, 1390), (339, 1090),
            (249, 760), (319, 600), (289, 330), (379, 370)
        ]
        fdraw.polygon(outer_f, fill=FLAME_ORANGE, outline=ink_col, width=10)
        fdraw.polygon(mid_f, fill=FLAME_YELLOW)
        canvas = Image.alpha_composite(canvas, f_layer)
        draw = ImageDraw.Draw(canvas)

    elif mode == 'hero_space_seated':
        w_layer = Image.new('RGBA', (W, H), INK_CLEAR)
        wdraw = ImageDraw.Draw(w_layer)
        wdraw.polygon([(512, 930), (565, 1120), (512, 1320), (459, 1120)], fill=(78, 255, 86, 175))
        w_layer = w_layer.filter(ImageFilter.GaussianBlur(6))
        canvas = Image.alpha_composite(canvas, w_layer)
        draw = ImageDraw.Draw(canvas)

    # Stick legs
    draw.line([(472, 910), (442, 1180), (452, 1425)], fill=ink_col, width=leg_w, joint="curve")
    draw.line([(552, 910), (582, 1180), (572, 1425)], fill=ink_col, width=leg_w, joint="curve")
    draw.ellipse([392, 1405, 488, 1465], fill=ink_col)
    draw.ellipse([536, 1405, 632, 1465], fill=ink_col)

    # Stick arms (unless neighbor_pray_body which joins hands in front of chest)
    if mode != 'neighbor_pray_body':
        draw.line([(435, 510), (345, 675), (385, 835)], fill=ink_col, width=leg_w, joint="curve")
        draw.line([(589, 510), (679, 675), (639, 835)], fill=ink_col, width=leg_w, joint="curve")
        draw.ellipse([358, 812, 414, 862], fill=ink_col)
        draw.ellipse([610, 812, 666, 862], fill=ink_col)

    # Narrow Vertical Rounded Pill Torso & Shorts
    neck_mask = Image.new('L', (W, H), 0)
    shirt_mask = Image.new('L', (W, H), 0)
    shorts_mask = Image.new('L', (W, H), 0)

    ImageDraw.Draw(neck_mask).rounded_rectangle([482, 395, 542, 465], radius=18, fill=255)
    ImageDraw.Draw(shirt_mask).rounded_rectangle([432, 435, 592, 865], radius=80, fill=255)
    ImageDraw.Draw(shorts_mask).rounded_rectangle([432, 815, 592, 935], radius=38, fill=255)

    body_mask = ImageChops.lighter(neck_mask, ImageChops.lighter(shirt_mask, shorts_mask))
    body_inner = body_mask.filter(ImageFilter.MinFilter(23))

    neck_paint = Image.new('RGBA', (W, H), WARM_RIM_CREAM if mode == 'neighbor_pray_body' else CREAM_RGBA)
    shirt_col = HOODIE_TEAL if mode == 'neighbor_pray_body' else SUIT_DARK
    shirt_paint = apply_15pct_crescent(Image.new('RGBA', (W, H), shirt_col), body_inner, shift_xy=(22, -16))
    shorts_paint = Image.new('RGBA', (W, H), JEANS_BLUE if mode == 'neighbor_pray_body' else SUIT_PANTS)

    torso_cel = Image.new('RGBA', (W, H), INK_CLEAR)
    for paint, reg in [(neck_paint, neck_mask), (shirt_paint, shirt_mask), (shorts_paint, shorts_mask)]:
        clipped = paint.copy()
        clipped.putalpha(ImageChops.multiply(paint.getchannel('A'), ImageChops.multiply(reg, body_inner)))
        torso_cel = Image.alpha_composite(torso_cel, clipped)

    ink_band = ImageChops.subtract(body_mask, body_inner)
    ink_layer = Image.new('RGBA', (W, H), ink_col)
    ink_layer.putalpha(ink_band)
    torso_cel = Image.alpha_composite(torso_cel, ink_layer)
    canvas = Image.alpha_composite(canvas, torso_cel)

    if mode == 'neighbor_pray_body':
        cdraw = ImageDraw.Draw(canvas)
        # Thin curved stick arms meeting at Namaste prayer hands in front of chest
        cdraw.line([(435, 515), (345, 645), (492, 605)], fill=ink_col, width=leg_w, joint="curve")
        cdraw.line([(589, 515), (679, 645), (532, 605)], fill=ink_col, width=leg_w, joint="curve")
        cdraw.polygon([(512, 515), (475, 585), (485, 645), (512, 650)], fill=WARM_RIM_CREAM, outline=ink_col, width=10)
        cdraw.polygon([(512, 515), (549, 585), (539, 645), (512, 650)], fill=WARM_RIM_CREAM, outline=ink_col, width=10)

    out_path = os.path.join(ASSET_DIR, filename)
    canvas.save(out_path, "PNG")
    return out_path


def generate_thought_bubble_card(filename: str, zapped: bool = False) -> str:
    W, H = 1024, 768
    img = Image.new('RGBA', (W, H), INK_CLEAR)
    draw = ImageDraw.Draw(img)

    circles = [(260, 340, 180), (440, 260, 210), (650, 280, 195), (760, 380, 165), (520, 440, 190), (330, 450, 160)]
    for cx, cy, r in circles:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(252, 250, 245, 252), outline=INK_RGBA, width=12)
    draw.ellipse([285, 160, 775, 540], fill=(252, 250, 245, 255))
    draw.ellipse([440, 595, 510, 665], fill=(252, 250, 245, 255), outline=INK_RGBA, width=10)
    draw.ellipse([465, 685, 515, 735], fill=(252, 250, 245, 255), outline=INK_RGBA, width=10)

    f_title = load_font(52)
    f_sub = load_font(40)

    if not zapped:
        draw.rounded_rectangle([245, 195, 795, 510], radius=22, fill=(255, 228, 228, 255), outline=(215, 30, 40, 255), width=9)
        draw.text((275, 235), "SEMESTER BACK", font=f_title, fill=(205, 20, 30, 255))
        draw.text((275, 320), "SUPPLY EXAM: FAIL [X]", font=f_sub, fill=INK_RGBA)
    else:
        draw.rounded_rectangle([245, 195, 795, 510], radius=22, fill=(32, 42, 58, 255), outline=(255, 210, 35, 255), width=10)
        for sx, sy, sr in [(300, 255, 42), (735, 255, 45), (315, 450, 40), (720, 445, 44)]:
            star_pts = [
                (sx, sy - sr), (sx + int(sr * 0.3), sy - int(sr * 0.3)),
                (sx + sr, sy), (sx + int(sr * 0.3), sy + int(sr * 0.3)),
                (sx, sy + sr), (sx - int(sr * 0.3), sy + int(sr * 0.3)),
                (sx - sr, sy), (sx - int(sr * 0.3), sy - int(sr * 0.3)),
            ]
            draw.polygon(star_pts, fill=(255, 215, 35, 255), outline=(255, 255, 255, 255), width=4)
        draw.text((310, 285), "WISH GRANTED!", font=f_title, fill=(255, 225, 55, 255))
        draw.text((310, 370), "ALL EXAMS PASSED!", font=f_sub, fill=(95, 255, 135, 255))

    out_path = os.path.join(ASSET_DIR, filename)
    img.save(out_path, "PNG")
    return out_path


def generate_coroner_newspaper_card(filename: str) -> str:
    W, H = 1024, 1536
    img = Image.new('RGBA', (W, H), INK_CLEAR)
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([36, 36, W - 36, H - 36], radius=18, fill=(244, 238, 224, 255), outline=INK_RGBA, width=12)
    draw.rectangle([68, 72, W - 68, 220], fill=(28, 24, 30, 255))

    f_mast = load_font(66)
    f_head = load_font(46)
    f_sub = load_font(36)
    f_body = load_font(32)

    draw.text((195, 105), "DAILY EXPRESS", font=f_mast, fill=(252, 248, 240, 255))
    draw.text((82, 252), "MAN BECOMES DESI ROCKET!", font=f_head, fill=(195, 25, 32, 255))
    draw.text((82, 325), "LAUNCHED INTO ORBIT AT MACH 8", font=f_sub, fill=INK_RGBA)
    draw.line([(68, 390), (W - 68, 390)], fill=INK_RGBA, width=6)

    draw.rectangle([78, 425, 485, 755], fill=(222, 214, 198, 255), outline=INK_RGBA, width=6)
    draw.line([(280, 735), (280, 515)], fill=(45, 185, 85, 255), width=26)
    draw.ellipse([235, 455, 325, 545], fill=INK_RGBA)
    for ly in range(435, 745, 44):
        draw.rectangle([515, ly, W - 82, ly + 18], fill=(150, 142, 130, 255))

    draw.rounded_rectangle([72, 795, W - 72, 1445], radius=16, fill=(253, 252, 248, 255), outline=INK_RGBA, width=10)
    draw.rectangle([72, 795, W - 72, 895], fill=(42, 54, 72, 255))
    draw.text((145, 822), "OFFICIAL CORONER'S REPORT", font=f_sub, fill=(255, 255, 255, 255))

    fields = [
        ("Name:", "You (Age 25)"),
        ("Last Seen:", "Mach 8 (Seated)"),
        ("Remains:", "1 Sofa (Shredded)"),
        ("Cause:", "100% Natural Fart"),
    ]
    y_cursor = 930
    for label, val in fields:
        draw.text((104, y_cursor), label, font=f_body, fill=(95, 85, 85, 255))
        draw.text((345, y_cursor), val, font=f_body, fill=INK_RGBA)
        draw.line([(104, y_cursor + 50), (W - 104, y_cursor + 50)], fill=(210, 205, 195, 255), width=4)
        y_cursor += 76

    out_path = os.path.join(ASSET_DIR, filename)
    img.save(out_path, "PNG")
    return out_path


def generate_stamp_overlay_card(filename: str) -> str:
    W, H = 1024, 320
    img = Image.new('RGBA', (W, H), INK_CLEAR)
    draw = ImageDraw.Draw(img)

    stamp_col = (215, 28, 36, 245)
    draw.rounded_rectangle([42, 36, W - 42, H - 36], radius=18, fill=(255, 235, 235, 65), outline=stamp_col, width=16)
    draw.rounded_rectangle([64, 58, W - 64, H - 58], radius=10, outline=stamp_col, width=6)

    f_stamp = load_font(52)
    draw.text((92, 118), "[100% TECHNICALLY NATURAL]", font=f_stamp, fill=stamp_col)

    out_path = os.path.join(ASSET_DIR, filename)
    img.save(out_path, "PNG")
    return out_path


def generate_mooli_paratha_prop(filename: str) -> str:
    W, H = 512, 512
    img = Image.new('RGBA', (W, H), INK_CLEAR)

    steam_layer = Image.new('RGBA', (W, H), INK_CLEAR)
    sdraw = ImageDraw.Draw(steam_layer)
    for sx in (185, 256, 325):
        sdraw.arc([sx - 35, 45, sx + 35, 165], start=110, end=260, fill=(255, 255, 255, 195), width=14)
        sdraw.arc([sx - 35, 125, sx + 35, 235], start=280, end=80, fill=(255, 255, 255, 195), width=14)
    steam_layer = steam_layer.filter(ImageFilter.GaussianBlur(4))
    img = Image.alpha_composite(img, steam_layer)

    draw = ImageDraw.Draw(img)
    paratha_pts = [
        (256, 175), (385, 235), (435, 355), (375, 445),
        (256, 465), (137, 445), (77, 355), (127, 235)
    ]
    draw.polygon(paratha_pts, fill=(218, 162, 78, 255), outline=INK_RGBA, width=10)
    spots = [(220, 280, 26), (310, 320, 30), (245, 385, 28), (175, 360, 22), (335, 395, 20)]
    for x, y, r in spots:
        draw.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=(138, 78, 28, 235))
        draw.ellipse([x + 12, y - 10, x + 22, y - 2], fill=(65, 145, 55, 235))

    out_path = os.path.join(ASSET_DIR, filename)
    img.save(out_path, "PNG")
    return out_path


def generate_hud_banner(filename: str, title: str, subtitle: str = "",
                        bg_col=(14, 20, 28, 244), border_col=(78, 255, 86, 255),
                        title_col=(255, 255, 255, 255), sub_col=(78, 255, 86, 255)) -> str:
    """Generates high-contrast 100% English screen-space HUD cards (zero □□□□ boxes!)."""
    W, H = 1024, 384
    img = Image.new('RGBA', (W, H), INK_CLEAR)
    draw = ImageDraw.Draw(img)

    safe_bg = (14, 20, 28, 245) if sum(bg_col[:3]) > 380 else bg_col
    safe_title = (255, 255, 255, 255) if sum(bg_col[:3]) > 380 else title_col
    safe_sub = (255, 215, 65, 255) if sum(bg_col[:3]) > 380 else sub_col

    draw.rounded_rectangle([24, 24, W - 24, H - 24], radius=32, fill=safe_bg, outline=border_col, width=8)
    f_big = load_font(56)
    f_med = load_font(42)

    clean_title = title.encode("ascii", "ignore").decode("ascii").strip()
    clean_sub = subtitle.encode("ascii", "ignore").decode("ascii").strip()

    draw.text((58, 72), clean_title, font=f_big, fill=safe_title)
    if clean_sub:
        draw.text((58, 188), clean_sub, font=f_med, fill=safe_sub)
    out_path = os.path.join(ASSET_DIR, filename)
    img.save(out_path, "PNG")
    return out_path


# ------------------------------------------------------------------------------
# 3. SHADER & GEOMETRY BUILDERS (Z-UP, EEVEE 4.2 COMPLIANT)
# ------------------------------------------------------------------------------
def make_opaque_mat(name: str, rgba=(0.8, 0.8, 0.8, 1.0), roughness=0.65, metallic=0.0,
                    emission_rgba=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.surface_render_method = 'DITHERED'
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission_rgba is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_rgba
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def make_translucent_mat(name: str, rgba=(1.0, 1.0, 1.0, 0.38), emission_strength=2.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.surface_render_method = 'BLENDED'
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transp = nodes.new("ShaderNodeBsdfTransparent")
    emis = nodes.new("ShaderNodeEmission")

    emis.inputs["Color"].default_value = (rgba[0], rgba[1], rgba[2], 1.0)
    emis.inputs["Strength"].default_value = emission_strength
    mix.inputs["Fac"].default_value = rgba[3]

    links.new(transp.outputs["BSDF"], mix.inputs[1])
    links.new(emis.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def make_cel_sprite_mat(name: str, image_path: str, blended: bool = True, emission_boost: float = 0.35):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.surface_render_method = 'BLENDED' if blended else 'DITHERED'
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")
    transp = nodes.new("ShaderNodeBsdfTransparent")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    tex = nodes.new("ShaderNodeTexImage")

    img = bpy.data.images.load(image_path, check_existing=True)
    img.alpha_mode = 'STRAIGHT'
    tex.image = img
    tex.extension = 'CLIP'

    bsdf.inputs["Roughness"].default_value = 0.92
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emission_boost

    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if "Emission Color" in bsdf.inputs:
        links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
    links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix.inputs[1])
    links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def link_to_collection(obj, col):
    if obj.name not in col.objects:
        col.objects.link(obj)
    for other_col in list(obj.users_collection):
        if other_col != col:
            other_col.objects.unlink(obj)


def create_box(name: str, size_xyz, loc_xyz, mat, col, parent=None, rot_xyz=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc_xyz, rotation=rot_xyz)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    obj.scale = size_xyz
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_cylinder(name: str, radius: float, depth: float, loc_xyz, mat, col, parent=None,
                    rot_xyz=(0.0, 0.0, 0.0), vertices: int = 28):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=loc_xyz, rotation=rot_xyz)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_cone(name: str, radius1: float, radius2: float, depth: float, loc_xyz, mat, col,
                parent=None, rot_xyz=(0.0, 0.0, 0.0), vertices: int = 32):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth,
                                    location=loc_xyz, rotation=rot_xyz)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_sphere(name: str, radius: float, loc_xyz, mat, col, parent=None, segments: int = 32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=20, radius=radius, location=loc_xyz)
    obj = bpy.context.view_layer.objects.active
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_vertical_cel_plane(name: str, width: float, height: float, loc_xyz, mat, col, parent=None):
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.location = loc_xyz
    if parent:
        obj.parent = parent

    hw, hh = width * 0.5, height * 0.5
    verts = [(-hw, -hh, 0.0), (hw, -hh, 0.0), (hw, hh, 0.0), (-hw, hh, 0.0)]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    mesh.update()

    uv_layer = mesh.uv_layers.new(name="UVMap")
    for idx, uv in enumerate([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
        uv_layer.data[idx].uv = uv

    obj.rotation_euler = Euler((radians(90.0), 0.0, 0.0), 'XYZ')
    if mat:
        obj.data.materials.append(mat)
    return obj


# ------------------------------------------------------------------------------
# 4. BUILD PART 2 3D SETS (SCENES 5, 6, AND 7)
# ------------------------------------------------------------------------------
def build_set_stratosphere(scene):
    """
    SET_STRATOSPHERE (Frames 1426 – 1974):
    - Sub-group 1 (f1426..1444): 3D House Roof shatter with flying terracotta tiles.
    - Sub-group 2 (f1445..1974): 2 KM UP curved Earth horizon, clouds, narrow (r=0.14m)
      semi-transparent (alpha=0.65) lime-green (#4eff56) beam strictly BELOW seated hips,
      3 translucent white Mach shockwave cones, and roaring orange/green meteor fire cones.
    """
    col = bpy.data.collections.new("SET_STRATOSPHERE")
    scene.collection.children.link(col)
    root = bpy.data.objects.new("ROOT_STRATOSPHERE", None)
    col.objects.link(root)

    mat_roof = make_opaque_mat("ST_RoofTile", (0.62, 0.22, 0.14, 1.0), roughness=0.75)
    mat_earth = make_opaque_mat("ST_EarthCurved", (0.10, 0.36, 0.68, 1.0), roughness=0.80,
                                emission_rgba=(0.12, 0.42, 0.78, 1.0), emission_strength=0.45)
    mat_cloud = make_translucent_mat("ST_CloudLayer", (0.94, 0.97, 1.0, 0.58), emission_strength=0.6)
    # Narrow translucent lime-green (#4eff56) beam (alpha=0.65, emission=1.45 -> NEVER white!)
    mat_beam = make_translucent_mat("ST_GreenBeam", (0.306, 1.0, 0.337, 0.65), emission_strength=1.45)
    mat_mach_cone = make_translucent_mat("ST_MachShockCone", (0.92, 0.98, 1.0, 0.42), emission_strength=1.15)
    mat_fire_outer = make_translucent_mat("ST_MeteorFireOuter", (1.0, 0.38, 0.06, 0.68), emission_strength=1.8)
    mat_fire_inner = make_translucent_mat("ST_MeteorFireInner", (1.0, 0.82, 0.18, 0.75), emission_strength=2.2)

    # 1. Roof Shatter Sub-Assembly (f1426..1444 ONLY)
    roof_grp = bpy.data.objects.new("ST_RoofShatter_Grp", None)
    col.objects.link(roof_grp)
    roof_grp.parent = root

    create_box("ST_RoofSlope_L", (1.6, 2.2, 0.18), (-1.15, 0.35, 0.45), mat_roof, col, roof_grp,
               rot_xyz=(0.0, radians(-24.0), 0.0))
    create_box("ST_RoofSlope_R", (1.6, 2.2, 0.18), (1.15, 0.35, 0.45), mat_roof, col, roof_grp,
               rot_xyz=(0.0, radians(24.0), 0.0))
    create_cylinder("ST_RoofCraterGlow", 0.38, 0.06, (0.0, 0.35, 0.52), mat_beam, col, roof_grp)

    roof_shred_tiles = []
    tile_specs = [
        ((-0.25, 0.25, 0.55), (-1.15, -0.85, 1.85), (2.5, -1.8, 1.2)),
        ((0.25, 0.25, 0.55), (1.20, -0.75, 1.95), (-2.2, 2.1, -1.5)),
        ((0.0, 0.15, 0.60), (0.10, -1.15, 2.10), (3.1, 1.4, -2.0)),
        ((-0.40, 0.40, 0.50), (-1.45, -0.55, 1.55), (-1.9, -2.6, 1.8)),
        ((0.40, 0.40, 0.50), (1.45, -0.60, 1.60), (2.4, 2.5, 1.9)),
    ]
    for idx, (p0, p1, r1) in enumerate(tile_specs):
        t_obj = create_box(f"ST_RoofTileDebris_{idx}", (0.34, 0.28, 0.08), p0, mat_roof, col, roof_grp)
        roof_shred_tiles.append((t_obj, p0, p1, r1))

    # 2. Curved Earth Horizon & Cloud Layer (f1445..1974)
    strat_grp = bpy.data.objects.new("ST_Stratosphere_Grp", None)
    col.objects.link(strat_grp)
    strat_grp.parent = root

    create_sphere("ST_CurvedEarth", 18.0, (0.0, 9.5, -19.8), mat_earth, col, strat_grp, segments=48)
    for idx, (cx, cy, cz, sx) in enumerate([
        (-2.2, 4.2, -1.4, 1.8), (2.4, 4.5, -1.2, 2.1), (0.0, 5.2, -1.6, 2.6),
        (-3.5, 5.5, -1.8, 2.0), (3.2, 5.2, -1.7, 1.9)
    ]):
        c_obj = create_sphere(f"ST_StratCloud_{idx}", 0.55, (cx, cy, cz), mat_cloud, col, strat_grp)
        c_obj.scale = (sx, 1.0, 0.35)

    # Narrow (r=0.13m) lime-green tapered beam strictly BELOW Hero's seated hips!
    # Hero is at Z = 0.55m (hips at Z ~ 1.15m); beam depth = 5.0m centered at Z = -1.45m -> top of beam is at Z = +1.05m!
    green_beam = create_cone("ST_LaserBeam", 0.16, 0.10, 5.0, (0.0, 0.42, -1.45), mat_beam, col, strat_grp)

    # 3 Translucent White Conical Mach 8 Shockwave Rings trailing below Hero (Cut 5B: f1546..1686)
    mach_cones = []
    for idx, (r_bot, h_cone, z_off) in enumerate([
        (0.75, 0.95, 0.25),
        (1.12, 1.25, -0.55),
        (1.48, 1.55, -1.45),
    ]):
        mc = create_cone(f"ST_MachCone_{idx}", r_bot, 0.08, h_cone, (0.0, 0.42, z_off), mat_mach_cone, col, strat_grp)
        mach_cones.append((mc, z_off))

    # Roaring 3D Orange & Green Meteor Fire Cones + Stars (Cut 5C: f1687..1974) positioned behind Hero (Y = 0.55m)
    meteor_fx = bpy.data.objects.new("ST_MeteorFire_Grp", None)
    col.objects.link(meteor_fx)
    meteor_fx.parent = root

    create_cone("ST_MeteorCone_Outer", 0.72, 0.10, 2.6, (0.0, 0.55, -0.35), mat_fire_outer, col, meteor_fx)
    create_cone("ST_MeteorCone_Inner", 0.46, 0.06, 2.0, (0.0, 0.52, -0.15), mat_fire_inner, col, meteor_fx)

    for idx, (ex, ey, ez) in enumerate([
        (-0.55, 0.48, -0.4), (0.58, 0.48, -0.6), (-0.38, 0.45, -1.1),
        (0.42, 0.45, -1.3), (0.0, 0.45, -1.6)
    ]):
        create_sphere(f"ST_MeteorEmber_{idx}", 0.075, (ex, ey, ez), mat_fire_inner, col, meteor_fx)

    st_sun_data = bpy.data.lights.new(name="ST_KeySun", type='SUN')
    st_sun_data.energy = 3.5
    st_sun_data.color = (1.0, 0.94, 0.85)
    st_sun = bpy.data.objects.new("ST_KeySun", st_sun_data)
    col.objects.link(st_sun)
    st_sun.parent = root
    st_sun.rotation_euler = Euler((radians(52.0), radians(-18.0), radians(20.0)), 'XYZ')

    return {
        "col": col,
        "root": root,
        "roof_grp": roof_grp,
        "roof_tiles": roof_shred_tiles,
        "strat_grp": strat_grp,
        "green_beam": green_beam,
        "mach_cones": mach_cones,
        "meteor_fx": meteor_fx,
    }


def build_set_neighbor_rooftop(scene):
    """
    SET_NEIGHBOR_ROOFTOP (Frames 1975 – 2274):
    Crisp, sharp nighttime Indian neighborhood rooftop terrace (छत) with concrete parapet wall,
    black ribbed overhead water tank, detailed city skyline windows, starry sky spheres,
    and the bright green-and-orange human shooting star streaking across the night sky.
    """
    col = bpy.data.collections.new("SET_NEIGHBOR_ROOFTOP")
    scene.collection.children.link(col)
    root = bpy.data.objects.new("ROOT_NEIGHBOR_ROOFTOP", None)
    col.objects.link(root)

    mat_concrete = make_opaque_mat("NR_TerraceConcrete", (0.28, 0.30, 0.36, 1.0), roughness=0.82)
    mat_parapet = make_opaque_mat("NR_ParapetWall", (0.36, 0.39, 0.46, 1.0), roughness=0.76)
    mat_tank = make_opaque_mat("NR_BlackWaterTank", (0.08, 0.10, 0.14, 1.0), roughness=0.40)
    mat_house = make_opaque_mat("NR_DistantHouse", (0.14, 0.16, 0.24, 1.0), roughness=0.78)
    mat_win_warm = make_opaque_mat("NR_WarmWindow", (1.0, 0.82, 0.38, 1.0), roughness=0.25,
                                   emission_rgba=(1.0, 0.78, 0.32, 1.0), emission_strength=2.6)
    mat_star = make_opaque_mat("NR_NightStar", (1.0, 1.0, 1.0, 1.0),
                               emission_rgba=(0.90, 0.95, 1.0, 1.0), emission_strength=3.0)
    mat_meteor_core = make_translucent_mat("NR_MeteorCore", (0.35, 1.0, 0.55, 0.90), emission_strength=2.8)
    mat_meteor_tail = make_translucent_mat("NR_MeteorTail", (1.0, 0.52, 0.14, 0.78), emission_strength=2.4)

    create_box("NR_TerraceFloor", (9.0, 9.0, 0.12), (0.0, 0.0, -0.06), mat_concrete, col, root)
    create_box("NR_ParapetBack", (9.0, 0.22, 0.88), (0.0, 2.25, 0.44), mat_parapet, col, root)
    create_box("NR_ParapetCap", (9.1, 0.28, 0.08), (0.0, 2.25, 0.90), mat_concrete, col, root)
    create_box("NR_ParapetLeft", (0.22, 5.0, 0.88), (-2.65, 0.0, 0.44), mat_parapet, col, root)

    # Black Ribbed Overhead Water Tank on brick pedestal
    create_box("NR_TankPedestal", (1.05, 1.05, 0.52), (-1.35, 1.65, 0.26), mat_parapet, col, root)
    create_cylinder("NR_WaterTankBody", 0.44, 1.15, (-1.35, 1.65, 1.08), mat_tank, col, root)
    create_cylinder("NR_WaterTankLid", 0.20, 0.10, (-1.35, 1.65, 1.70), mat_tank, col, root)
    for rz in (0.72, 0.95, 1.18, 1.41):
        create_cylinder(f"NR_TankRib_{rz}", 0.465, 0.035, (-1.35, 1.65, rz), mat_tank, col, root)

    # Crisp Distant Neighborhood Houses & Warm Windows
    house_specs = [
        (-1.8, 5.2, 1.0, (1.4, 1.0, 2.2)),
        (-0.2, 5.6, 1.2, (1.5, 1.0, 2.6)),
        (1.4, 5.3, 0.95, (1.4, 1.0, 2.1)),
        (2.8, 5.8, 1.3, (1.4, 1.0, 2.7)),
    ]
    for idx, (hx, hy, hz, hsz) in enumerate(house_specs):
        create_box(f"NR_House_{idx}", hsz, (hx, hy, hz), mat_house, col, root)
        for wz_off in (-0.25, 0.28):
            create_box(f"NR_HouseWinA_{idx}_{wz_off}", (0.22, 0.05, 0.28), (hx - 0.28, hy - 0.51, hz + wz_off), mat_win_warm, col, root)
            create_box(f"NR_HouseWinB_{idx}_{wz_off}", (0.22, 0.05, 0.28), (hx + 0.28, hy - 0.51, hz + wz_off), mat_win_warm, col, root)

    # Crisp Night Sky Stars
    for idx, sc in enumerate([
        (-1.5, 6.2, 3.2), (-0.6, 6.4, 3.6), (0.4, 6.3, 3.5), (1.3, 6.1, 3.3),
        (-1.1, 6.3, 2.7), (0.9, 6.2, 2.8), (-0.1, 6.5, 3.9), (1.7, 6.2, 3.8)
    ]):
        create_sphere(f"NR_Star_{idx}", 0.035, sc, mat_star, col, root, segments=12)

    # Streaking Human Shooting Star (Green & Orange Meteor)
    meteor_streak = bpy.data.objects.new("NR_MeteorStreak", None)
    col.objects.link(meteor_streak)
    meteor_streak.parent = root
    create_sphere("NR_MeteorHead", 0.20, (0.0, 0.0, 0.0), mat_meteor_core, col, meteor_streak)
    create_cone("NR_MeteorFlameTail", 0.18, 0.02, 2.1, (-0.95, 0.0, 0.38), mat_meteor_tail, col, meteor_streak,
                rot_xyz=(0.0, radians(-68.0), 0.0))

    m_light_data = bpy.data.lights.new(name="NR_MeteorRimLight", type='AREA')
    m_light_data.energy = 95.0
    m_light_data.color = (1.0, 0.72, 0.35)
    m_light_data.size = 2.2
    m_light = bpy.data.objects.new("NR_MeteorRimLight", m_light_data)
    col.objects.link(m_light)
    m_light.parent = root
    m_light.location = (1.65, -0.85, 2.15)
    m_light.rotation_euler = Euler((radians(55.0), 0.0, radians(135.0)), 'XYZ')

    n_fill_data = bpy.data.lights.new(name="NR_NightMoonFill", type='SUN')
    n_fill_data.energy = 2.2
    n_fill_data.color = (0.48, 0.62, 0.95)
    n_fill = bpy.data.objects.new("NR_NightMoonFill", n_fill_data)
    col.objects.link(n_fill)
    n_fill.parent = root
    n_fill.rotation_euler = Euler((radians(42.0), radians(15.0), radians(-25.0)), 'XYZ')

    return {
        "col": col,
        "root": root,
        "meteor_streak": meteor_streak,
    }


def build_set_coroner_desk(scene):
    """
    SET_CORONER_DESK (Frames 2275 – 2526):
    Coroner's Report card width scaled down by 35% (0.62m x 0.93m) so 100% of text
    fits inside the 9:16 vertical frame with clean left/right wooden desk margins!
    """
    col = bpy.data.collections.new("SET_CORONER_DESK")
    scene.collection.children.link(col)
    root = bpy.data.objects.new("ROOT_CORONER_DESK", None)
    col.objects.link(root)

    mat_desk = make_opaque_mat("CD_WoodDesk", (0.28, 0.15, 0.08, 1.0), roughness=0.48)
    mat_plank = make_opaque_mat("CD_DeskGroove", (0.14, 0.07, 0.03, 1.0), roughness=0.70)
    mat_pen_body = make_opaque_mat("CD_PenBlack", (0.08, 0.08, 0.10, 1.0), roughness=0.25, metallic=0.3)
    mat_gold = make_opaque_mat("CD_BrassGold", (0.88, 0.68, 0.22, 1.0), roughness=0.28, metallic=0.88)
    mat_stamp_wood = make_opaque_mat("CD_StampHandleRedWood", (0.52, 0.10, 0.08, 1.0), roughness=0.40)

    create_box("CD_DeskTop", (3.6, 3.6, 0.12), (0.0, 0.0, -0.06), mat_desk, col, root)
    for gx in (-0.45, -0.15, 0.15, 0.45):
        create_box(f"CD_DeskGrain_{gx}", (0.008, 2.4, 0.004), (gx, 0.0, 0.002), mat_plank, col, root)

    # Coroner Newspaper Card scaled down by 35% (0.62m x 0.93m) for clean 9:16 margins!
    news_png = generate_coroner_newspaper_card("coroner_newspaper_card.png")
    mat_news = make_cel_sprite_mat("Mat_CoronerNewspaper", news_png, blended=True, emission_boost=0.25)
    news_card = create_vertical_cel_plane("CD_NewspaperCard", 0.62, 0.93, (0.0, 0.0, 0.005), mat_news, col, root)
    news_card.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')

    # Distressed Red Rubber-Stamp Overlay Card (`[100% TECHNICALLY NATURAL]`) scaled proportionally
    stamp_png = generate_stamp_overlay_card("stamp_overlay_card.png")
    mat_stamp_ov = make_cel_sprite_mat("Mat_StampOverlay", stamp_png, blended=True, emission_boost=0.45)
    stamp_overlay = create_vertical_cel_plane("CD_StampOverlayCard", 0.50, 0.16, (0.0, -0.30, 0.012), mat_stamp_ov, col, root)
    stamp_overlay.rotation_euler = Euler((0.0, 0.0, radians(-4.5)), 'XYZ')

    # 3D Fountain Pen Prop resting beside report inside frame
    pen_grp = bpy.data.objects.new("CD_FountainPen", None)
    col.objects.link(pen_grp)
    pen_grp.parent = root
    pen_grp.location = (0.36, 0.08, 0.030)
    pen_grp.rotation_euler = Euler((radians(90.0), 0.0, radians(18.0)), 'XYZ')
    create_cylinder("CD_PenBarrel", 0.016, 0.38, (0.0, 0.0, 0.0), mat_pen_body, col, pen_grp)
    create_cylinder("CD_PenGoldRing", 0.018, 0.025, (0.0, 0.0, -0.10), mat_gold, col, pen_grp)
    create_cone("CD_PenNib", 0.015, 0.002, 0.07, (0.0, 0.0, -0.22), mat_gold, col, pen_grp,
                rot_xyz=(radians(180.0), 0.0, 0.0))

    # Heavy 3D Rubber Stamp Tool (Slams down at f2455 in Cut 7B!)
    stamp_tool = bpy.data.objects.new("CD_RubberStamp3D", None)
    col.objects.link(stamp_tool)
    stamp_tool.parent = root
    stamp_tool.location = (0.0, -1.50, 2.50)  # Default off-screen outside Cut 7A view
    create_box("CD_StampBaseBlock", (0.50, 0.16, 0.05), (0.0, 0.0, 0.025), mat_gold, col, stamp_tool)
    create_cylinder("CD_StampStem", 0.035, 0.18, (0.0, 0.0, 0.13), mat_stamp_wood, col, stamp_tool)
    create_sphere("CD_StampKnob", 0.075, (0.0, 0.0, 0.23), mat_stamp_wood, col, stamp_tool)

    d_light_data = bpy.data.lights.new(name="CD_WarmDeskLamp", type='AREA')
    d_light_data.energy = 75.0
    d_light_data.color = (1.0, 0.88, 0.72)
    d_light_data.size = 1.8
    d_light = bpy.data.objects.new("CD_WarmDeskLamp", d_light_data)
    col.objects.link(d_light)
    d_light.parent = root
    d_light.location = (0.35, -0.25, 1.85)
    d_light.rotation_euler = Euler((radians(12.0), radians(10.0), 0.0), 'XYZ')

    return {
        "col": col,
        "root": root,
        "news_card": news_card,
        "stamp_overlay": stamp_overlay,
        "stamp_tool": stamp_tool,
    }


def build_set_outer_space(scene):
    """
    SET_OUTER_SPACE (Frames 2527 – 2715):
    Deep black starry space with a large, slowly rotating 3D Earth sphere below
    with a glowing blue atmospheric rim and floating Mooli Paratha prop cards.
    """
    col = bpy.data.collections.new("SET_OUTER_SPACE")
    scene.collection.children.link(col)
    root = bpy.data.objects.new("ROOT_OUTER_SPACE", None)
    col.objects.link(root)

    mat_earth_ocean = make_opaque_mat("OS_EarthOcean", (0.06, 0.28, 0.68, 1.0), roughness=0.65,
                                      emission_rgba=(0.08, 0.35, 0.82, 1.0), emission_strength=0.55)
    mat_earth_land = make_opaque_mat("OS_EarthContinent", (0.16, 0.52, 0.24, 1.0), roughness=0.78)
    mat_atmo_rim = make_translucent_mat("OS_AtmosphereRim", (0.28, 0.72, 1.0, 0.32), emission_strength=2.4)
    mat_star = make_opaque_mat("OS_StarWhite", (1.0, 1.0, 1.0, 1.0),
                               emission_rgba=(0.92, 0.96, 1.0, 1.0), emission_strength=4.0)

    # Slowly Rotating 3D Earth Sphere below Hero
    earth_sphere = create_sphere("OS_EarthSphere", 2.65, (0.0, 1.45, -2.85), mat_earth_ocean, col, root, segments=48)
    create_sphere("OS_EarthAtmosphere", 2.76, (0.0, 1.45, -2.85), mat_atmo_rim, col, root, segments=48)

    # Continent patches parented to Earth so rotation is clearly visible
    for idx, (lx, ly, lz, rad) in enumerate([
        (0.45, -2.15, 1.35, 0.65), (-0.85, -2.05, 1.20, 0.55), (1.10, -1.85, 1.45, 0.48)
    ]):
        create_sphere(f"OS_Continent_{idx}", rad, (lx, ly, lz), mat_earth_land, col, earth_sphere)

    # Distant Starfield Spheres
    star_coords = [
        (-1.4, 4.5, 2.2), (1.5, 4.8, 2.4), (-0.8, 4.6, 1.5), (0.9, 4.4, 1.8),
        (-1.6, 4.2, 0.6), (1.4, 4.5, 0.8), (0.0, 4.9, 2.6), (-0.4, 4.3, 0.2)
    ]
    for idx, sc in enumerate(star_coords):
        create_sphere(f"OS_Star_{idx}", 0.032, sc, mat_star, col, root, segments=12)

    # Two Steaming Mooli Paratha Prop Cards floating beside Hero's head!
    paratha_png = generate_mooli_paratha_prop("mooli_paratha_prop.png")
    mat_paratha = make_cel_sprite_mat("Mat_MooliParatha", paratha_png, blended=True, emission_boost=0.45)
    paratha_L = create_vertical_cel_plane("OS_MooliParatha_L", 0.42, 0.42, (-0.56, 0.25, 1.25), mat_paratha, col, root)
    paratha_R = create_vertical_cel_plane("OS_MooliParatha_R", 0.38, 0.38, (0.58, 0.25, 1.12), mat_paratha, col, root)

    # Space Sunlight
    sp_sun_data = bpy.data.lights.new(name="OS_SpaceSun", type='SUN')
    sp_sun_data.energy = 4.2
    sp_sun_data.color = (1.0, 0.98, 0.95)
    sp_sun = bpy.data.objects.new("OS_SpaceSun", sp_sun_data)
    col.objects.link(sp_sun)
    sp_sun.parent = root
    sp_sun.rotation_euler = Euler((radians(58.0), radians(-24.0), radians(15.0)), 'XYZ')

    return {
        "col": col,
        "root": root,
        "earth": earth_sphere,
        "paratha_L": paratha_L,
        "paratha_R": paratha_R,
    }


# ------------------------------------------------------------------------------
# 5. EXTEND HERO RIG, BUILD NEIGHBOR RIG & ADD PART 2 HUD CARDS
# ------------------------------------------------------------------------------
def extend_cast_and_hud_for_part2(scene):
    cam_col = bpy.data.collections.get("CAMERA_AND_HUD")
    cam_obj = bpy.data.objects.get("MainCamera")
    aim_helper = bpy.data.objects.get("Cam_HeadBillboard_Target")
    hero_col = bpy.data.collections.get("CAST_HERO_2D")
    hero_root = bpy.data.objects.get("Hero_Root")
    head_pivot = bpy.data.objects.get("Hero_Head_BillboardPivot")

    # 1. Generate & attach new Hero heads and bodies for Scenes 5 & 7
    p_head_strat = generate_part2_head_sprite("head_stratosphere_sit.png", "hero_stratosphere")
    p_head_meteor = generate_part2_head_sprite("head_meteor_fire.png", "hero_meteor_fire")
    p_head_space = generate_part2_head_sprite("head_space_seated.png", "hero_space")

    p_body_strat = generate_part2_body_sprite("body_stratosphere_sit.png", "hero_stratosphere_sit")
    p_body_meteor = generate_part2_body_sprite("body_meteor_fire.png", "hero_meteor_fire")
    p_body_space = generate_part2_body_sprite("body_space_seated.png", "hero_space_seated")

    new_hero_heads = {}
    for key, path, boost in [
        ("stratosphere", p_head_strat, 0.45),
        ("meteor_fire", p_head_meteor, 1.35),
        ("space_seated", p_head_space, 0.45),
    ]:
        h_obj = create_vertical_cel_plane(
            f"Hero_Head_{key}", 0.56, 0.56, (0.0, 0.0, 0.0),
            make_cel_sprite_mat(f"Mat_Head_{key}", path, emission_boost=boost),
            hero_col, head_pivot
        )
        h_obj.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
        new_hero_heads[key] = h_obj

    new_hero_bodies = {}
    for key, path, boost in [
        ("stratosphere", p_body_strat, 0.45),
        ("meteor_fire", p_body_meteor, 1.35),
        ("space_seated", p_body_space, 0.45),
    ]:
        b_obj = create_vertical_cel_plane(
            f"Hero_Body_{key}", 0.96, 1.44, (0.0, 0.0, 0.72),
            make_cel_sprite_mat(f"Mat_Body_{key}", path, emission_boost=boost),
            hero_col, hero_root
        )
        new_hero_bodies[key] = b_obj

    # Schedule visibility for new Hero states across 1..2715
    set_root_visibility(new_hero_heads["stratosphere"], None, [(1426, 1686)])
    set_root_visibility(new_hero_bodies["stratosphere"], None, [(1426, 1686)])
    set_root_visibility(new_hero_heads["meteor_fire"], None, [(1687, 1974)])
    set_root_visibility(new_hero_bodies["meteor_fire"], None, [(1687, 1974)])
    set_root_visibility(new_hero_heads["space_seated"], None, [(2527, 2715)])
    set_root_visibility(new_hero_bodies["space_seated"], None, [(2527, 2715)])

    # 2. Build Neighbor 2D Cel Cast Rig (Scene 6: f1975..2274) with §7.1 DAMPED_TRACK Head Pivot
    nb_col = bpy.data.collections.new("CAST_NEIGHBOR_2D")
    scene.collection.children.link(nb_col)
    nb_root = bpy.data.objects.new("Neighbor_Root", None)
    nb_col.objects.link(nb_root)
    nb_root.location = (0.0, 0.35, 0.0)

    nb_head_pivot = bpy.data.objects.new("Neighbor_Head_BillboardPivot", None)
    nb_col.objects.link(nb_head_pivot)
    nb_head_pivot.parent = nb_root
    nb_head_pivot.location = (0.0, -0.02, 1.18)

    dt = nb_head_pivot.constraints.new(type='DAMPED_TRACK')
    dt.target = aim_helper
    dt.track_axis = 'TRACK_Z'

    p_nb_back = generate_part2_body_sprite("neighbor_back_point.png", "neighbor_back_point_full")
    p_nb_pray_body = generate_part2_body_sprite("neighbor_pray_body.png", "neighbor_pray_body")
    p_nb_h_closed = generate_part2_head_sprite("neighbor_pray_closed.png", "neighbor_pray_closed")
    p_nb_h_talk = generate_part2_head_sprite("neighbor_pray_talk.png", "neighbor_pray_talk")
    p_nb_h_wish = generate_part2_head_sprite("neighbor_one_eye_wish.png", "neighbor_one_eye_wish")
    p_thought_back = generate_thought_bubble_card("thought_back_supply.png", zapped=False)
    p_thought_zap = generate_thought_bubble_card("thought_star_sparkles.png", zapped=True)

    nb_back_card = create_vertical_cel_plane(
        "Neighbor_BackPoint_Card", 1.05, 1.55, (-0.38, -0.15, 0.78),
        make_cel_sprite_mat("Mat_NB_BackPoint", p_nb_back, emission_boost=0.45),
        nb_col, nb_root
    )
    nb_pray_body = create_vertical_cel_plane(
        "Neighbor_Pray_Body", 0.96, 1.44, (0.0, 0.0, 0.72),
        make_cel_sprite_mat("Mat_NB_PrayBody", p_nb_pray_body, emission_boost=0.45),
        nb_col, nb_root
    )

    nb_heads = {}
    for key, path in [
        ("pray_closed", p_nb_h_closed),
        ("pray_talk", p_nb_h_talk),
        ("one_eye_wish", p_nb_h_wish),
    ]:
        nh = create_vertical_cel_plane(
            f"Neighbor_Head_{key}", 0.56, 0.56, (0.0, 0.0, 0.0),
            make_cel_sprite_mat(f"Mat_NB_Head_{key}", path, emission_boost=0.50),
            nb_col, nb_head_pivot
        )
        nh.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
        nb_heads[key] = nh

    # Thought bubble cards floating above Neighbor's head in Cut 6C (f2161..2274)
    thought_fail = create_vertical_cel_plane(
        "Neighbor_Thought_Fail", 0.68, 0.51, (0.05, -0.04, 1.72),
        make_cel_sprite_mat("Mat_Thought_Fail", p_thought_back, emission_boost=0.65),
        nb_col, nb_root
    )
    thought_zap = create_vertical_cel_plane(
        "Neighbor_Thought_Zap", 0.68, 0.51, (0.05, -0.04, 1.72),
        make_cel_sprite_mat("Mat_Thought_Zap", p_thought_zap, emission_boost=0.75),
        nb_col, nb_root
    )

    # 3. Generate & parent 100% English Part 2 Screen-Space HUD Cards to MainCamera (§7.6)
    p2_hud_specs = {
        "mach8_top": (
            generate_hud_banner(
                "hud_mach8_top.png", "MACH 8 - 2 KM UP", "STRATOSPHERE ASCENT",
                bg_col=(14, 20, 28, 244), border_col=(255, 205, 35, 255),
                title_col=(255, 215, 45, 255), sub_col=(255, 255, 255, 255)
            ),
            (0.62, 0.23), (0.0, 0.48, -1.65)
        ),
        "still_sitting": (
            generate_hud_banner(
                "hud_still_sitting.png", "<- STILL SITTING!", "RIGID SEATED POSTURE",
                bg_col=(14, 20, 28, 244), border_col=(78, 255, 86, 255)
            ),
            (0.38, 0.14), (0.21, 0.02, -1.65)
        ),
        "sound_behind": (
            generate_hud_banner(
                "hud_sound_behind.png", "THE SOUND IS BACK THERE v", "OUTRUNNING OWN SONIC BOOM!",
                bg_col=(14, 20, 28, 244), border_col=(120, 235, 255, 255),
                sub_col=(135, 240, 255, 255)
            ),
            (0.62, 0.23), (0.0, -0.44, -1.65)
        ),
        "meteor_mode": (
            generate_hud_banner(
                "hud_meteor_mode.png", "METHANE + AIR FRICTION", "HUMAN METEOR IGNITION!",
                bg_col=(36, 12, 10, 244), border_col=(255, 145, 35, 255),
                sub_col=(255, 205, 65, 255)
            ),
            (0.62, 0.23), (0.0, 0.48, -1.65)
        ),
        "rooftop_hdr": (
            generate_hud_banner(
                "hud_rooftop_hdr.png", "NEIGHBOR'S ROOFTOP", "2:00 AM - NIGHT TERRACE",
                bg_col=(18, 16, 32, 244), border_col=(255, 185, 75, 255),
                sub_col=(255, 210, 115, 255)
            ),
            (0.62, 0.23), (0.0, 0.48, -1.65)
        ),
        "cta_paratha": (
            generate_hud_banner(
                "hud_cta_paratha.png", "SEND TO MOOLI PARATHA", "FRIEND! (FREE SPACE TICKET!)",
                bg_col=(14, 20, 28, 245), border_col=(255, 205, 35, 255),
                title_col=(255, 215, 45, 255), sub_col=(95, 255, 135, 255)
            ),
            (0.64, 0.24), (0.0, 0.48, -1.65)
        ),
    }

    p2_hud_cards = {}
    for key, (png_path, (w, h), loc) in p2_hud_specs.items():
        mat = make_cel_sprite_mat(f"Mat_HUD_{key}", png_path, blended=True, emission_boost=0.85)
        card = create_vertical_cel_plane(f"HUD_Card_{key}", w, h, loc, mat, cam_col, parent=cam_obj)
        card.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
        p2_hud_cards[key] = card

    return {
        "hero_root": hero_root,
        "nb_col": nb_col,
        "nb_root": nb_root,
        "nb_back_card": nb_back_card,
        "nb_pray_body": nb_pray_body,
        "nb_heads": nb_heads,
        "thought_fail": thought_fail,
        "thought_zap": thought_zap,
        "p2_hud_cards": p2_hud_cards,
    }


# ------------------------------------------------------------------------------
# 6. ANIMATE SCENES 5 TO 7 (FRAMES 1426 – 2715 | 47.5s – 90.5s)
# ------------------------------------------------------------------------------
def set_part2_hud_schedule(p2_hud_cards: dict, schedule: list):
    crit_frames = {1, PART2_FIRST_FRAME - 1, PART2_FIRST_FRAME, FRAME_END}
    for s, e, _ in schedule:
        crit_frames.update([max(1, s - 1), s, e, min(FRAME_END, e + 1)])

    for f in sorted(crit_frames):
        active_keys = {k for (s, e, k) in schedule if s <= f <= e}
        for k, obj in p2_hud_cards.items():
            hide = (k not in active_keys)
            obj.hide_viewport = hide
            obj.hide_render = hide
            obj.keyframe_insert(data_path="hide_viewport", frame=f)
            obj.keyframe_insert(data_path="hide_render", frame=f)

    for obj in p2_hud_cards.values():
        enforce_constant_visibility(obj)


def animate_part2_scenes(scene, st_set, nr_set, cd_set, os_set, cast_p2):
    cam = bpy.data.objects.get("MainCamera")
    hero_root = cast_p2["hero_root"]
    nb_root = cast_p2["nb_root"]
    p2_hud = cast_p2["p2_hud_cards"]

    # --------------------------------------------------------------------------
    # A. ISOLATED SET VISIBILITY SCHEDULE (Recursive Child Hiding Fixed!)
    # --------------------------------------------------------------------------
    set_root_visibility(st_set["root"], st_set["col"], [(1426, 1974)])
    # Explicitly override recursive sub-groups AFTER parent col so roof planks hide at f1445!
    set_root_visibility(st_set["roof_grp"], None, [(1426, 1444)])
    set_root_visibility(st_set["strat_grp"], None, [(1445, 1974)])
    for mc, _ in st_set["mach_cones"]:
        set_root_visibility(mc, None, [(1546, 1686)])
    set_root_visibility(st_set["meteor_fx"], None, [(1687, 1974)])

    set_root_visibility(nr_set["root"], nr_set["col"], [(1975, 2274)])
    set_root_visibility(cd_set["root"], cd_set["col"], [(2275, 2526)])
    # Keep 3D rubber stamp completely hidden before f2451 so f2360 (Cut 7A) is clean!
    set_root_visibility(cd_set["stamp_tool"], None, [(2451, 2526)])
    # Override stamp_overlay AFTER cd_set["col"] so f2360 is unstamped and f2485 is stamped!
    set_root_visibility(cd_set["stamp_overlay"], None, [(2455, 2526)])
    set_root_visibility(os_set["root"], os_set["col"], [(2527, 2715)])

    # Neighbor Cast Visibility Schedule (Scene 6: f1975..2274)
    set_root_visibility(cast_p2["nb_back_card"], None, [(1975, 2070)])
    set_root_visibility(cast_p2["nb_pray_body"], None, [(2071, 2274)])
    set_root_visibility(cast_p2["thought_fail"], None, [(2161, 2209)])
    set_root_visibility(cast_p2["thought_zap"], None, [(2210, 2274)])

    talk_spans_6b = [
        (2075, 2083), (2088, 2096), (2102, 2112), (2118, 2128), (2134, 2145), (2150, 2158)
    ]
    talk_spans_6c = [
        (2166, 2174), (2180, 2190), (2196, 2206), (2214, 2224), (2230, 2242), (2248, 2258)
    ]
    nb_heads = cast_p2["nb_heads"]
    crit_nb_frames = {1, 1974, 1975, 2070, 2071, 2160, 2161, 2274, 2275, FRAME_END}
    for s, e in talk_spans_6b + talk_spans_6c:
        crit_nb_frames.update([s - 1, s, e, e + 1])

    for f in sorted(crit_nb_frames):
        active_nh = None
        if 2071 <= f <= 2160:
            is_talking = any(s <= f <= e for (s, e) in talk_spans_6b)
            active_nh = "pray_talk" if is_talking else "pray_closed"
        elif 2161 <= f <= 2274:
            is_talking_c = any(s <= f <= e for (s, e) in talk_spans_6c)
            active_nh = "pray_talk" if (is_talking_c and f < 2208) else "one_eye_wish"

        for hk, hobj in nb_heads.items():
            hide = (hk != active_nh)
            hobj.hide_viewport = hide
            hobj.hide_render = hide
            hobj.keyframe_insert(data_path="hide_viewport", frame=f)
            hobj.keyframe_insert(data_path="hide_render", frame=f)

    for hobj in nb_heads.values():
        enforce_constant_visibility(hobj)

    # --------------------------------------------------------------------------
    # B. PART 2 SCREEN-SPACE HUD SCHEDULE (§7.6)
    # --------------------------------------------------------------------------
    set_part2_hud_schedule(p2_hud, [
        (1445, 1545, "mach8_top"),
        (1445, 1545, "still_sitting"),
        (1546, 1686, "sound_behind"),
        (1687, 1974, "meteor_mode"),
        (1975, 2070, "rooftop_hdr"),
        (2527, 2715, "cta_paratha"),
    ])

    # --------------------------------------------------------------------------
    # C. WORLD MOOD BEAT TABLE FOR SCENES 5–7 (§7.5)
    # --------------------------------------------------------------------------
    bg_node = scene.world.node_tree.nodes.get("Background")
    p2_world_beats = [
        (1426, (0.14, 0.38, 0.78, 1.0)),
        (1445, (0.05, 0.18, 0.44, 1.0)),
        (1687, (0.02, 0.04, 0.12, 1.0)),
        (1975, (0.02, 0.03, 0.08, 1.0)),
        (2275, (0.08, 0.05, 0.03, 1.0)),
        (2527, (0.003, 0.004, 0.010, 1.0)),
    ]
    if bg_node:
        for f_beat, col_val in p2_world_beats:
            bg_node.inputs[0].default_value = col_val
            bg_node.inputs[0].keyframe_insert(data_path="default_value", frame=f_beat)
        for fc in scene.world.node_tree.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'

    # --------------------------------------------------------------------------
    # SCENE 5 (Frames 1426 – 1974 | 47.5s – 65.8s): Roof Smash, Mach 8 & Meteor
    # --------------------------------------------------------------------------
    bake_event_transform(
        hero_root, start=1426, anticipate=1428, extreme=1439, settled=1444, hold_end=1444,
        loc_a=(0.0, 0.35, -0.35), loc_b=(0.0, 0.35, 1.45),
        rot_a=(0.0, 0.0, 0.0), rot_b=(0.0, 0.0, 0.0),
        scale_a=(1.0, 1.0, 1.0), scale_b=(1.0, 1.0, 1.0)
    )
    for t_obj, p0, p1, r1 in st_set["roof_tiles"]:
        bake_event_transform(
            t_obj, start=1427, anticipate=1429, extreme=1440, settled=1444, hold_end=1444,
            loc_a=p0, loc_b=p1, rot_a=(0.0, 0.0, 0.0), rot_b=r1
        )
    bake_event_transform(
        cam, start=1426, anticipate=1429, extreme=1439, settled=1444, hold_end=1444,
        loc_a=(0.0, -2.65, 1.05), loc_b=(0.0, -2.45, 1.35),
        rot_a=(radians(86.0), 0.0, 0.0), rot_b=(radians(92.0), 0.0, 0.0)
    )

    # Cut 5A Part 2 (f1445..1545): 2 KM UP in Stratosphere atop narrow translucent lime-green beam
    hero_root.location = (0.0, 0.35, 0.55)
    hero_root.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
    hero_root.keyframe_insert(data_path="location", frame=1445)
    hero_root.keyframe_insert(data_path="rotation_euler", frame=1445)
    set_fcurve_constant_after(hero_root, "location", 1445)
    set_fcurve_constant_after(hero_root, "rotation_euler", 1445)

    bake_event_transform(
        cam, start=1445, anticipate=1452, extreme=1510, settled=1525, hold_end=1545,
        loc_a=(0.22, -2.25, 1.18), loc_b=(0.0, -2.05, 1.15),
        rot_a=(radians(86.5), 0.0, radians(5.5)), rot_b=(radians(87.5), 0.0, 0.0)
    )

    # Cut 5B (f1546..1686): High-angle dolly-out revealing 3 conical Mach shockwave rings trailing below
    bake_event_transform(
        cam, start=1546, anticipate=1554, extreme=1625, settled=1645, hold_end=1686,
        loc_a=(0.0, -2.05, 1.15), loc_b=(0.0, -4.35, 0.45),
        rot_a=(radians(87.5), 0.0, 0.0), rot_b=(radians(84.5), 0.0, 0.0)
    )
    for idx, (mc, z_off) in enumerate(st_set["mach_cones"]):
        f0 = 1548 + idx * 10
        bake_event_transform(
            mc, start=f0, anticipate=f0 + 4, extreme=f0 + 28, settled=f0 + 38, hold_end=1686,
            loc_a=(0.0, 0.42, z_off + 0.35), loc_b=(0.0, 0.42, z_off),
            scale_a=(0.35, 0.35, 0.35), scale_b=(1.0, 1.0, 1.0)
        )

    # Cut 5C (f1687..1974): Air friction + methane ignition! Stickman centered in frame wrapped in fire!
    bake_event_transform(
        hero_root, start=1687, anticipate=1695, extreme=1920, settled=1950, hold_end=1974,
        loc_a=(-0.28, 0.35, 0.35), loc_b=(0.28, 0.35, 0.75),
        rot_a=(0.0, radians(16.0), 0.0), rot_b=(0.0, radians(16.0), 0.0)
    )
    bake_event_transform(
        st_set["meteor_fx"], start=1687, anticipate=1695, extreme=1920, settled=1950, hold_end=1974,
        loc_a=(-0.28, 0.52, 0.35), loc_b=(0.28, 0.52, 0.75),
        rot_a=(0.0, radians(16.0), 0.0), rot_b=(0.0, radians(16.0), 0.0),
        scale_a=(0.65, 0.65, 0.65), scale_b=(1.05, 1.05, 1.05)
    )
    bake_event_transform(
        cam, start=1687, anticipate=1695, extreme=1920, settled=1950, hold_end=1974,
        loc_a=(-0.18, -2.75, 0.95), loc_b=(0.18, -2.65, 1.25),
        rot_a=(radians(87.0), 0.0, radians(-3.0)), rot_b=(radians(88.0), 0.0, radians(3.0))
    )

    # --------------------------------------------------------------------------
    # SCENE 6 (Frames 1975 – 2274 | 65.8s – 75.8s): Neighbor's Rooftop & Wish
    # --------------------------------------------------------------------------
    # Keep 3D backgrounds & character cards 100% razor-sharp (disable heavy DOF blur!)
    cam.data.dof.use_dof = False
    cam.data.dof.keyframe_insert(data_path="use_dof", frame=1975)

    nb_root.location = (0.0, 0.35, 0.0)
    nb_root.keyframe_insert(data_path="location", frame=1975)
    set_fcurve_constant_after(nb_root, "location", 1975)

    bake_event_transform(
        nr_set["meteor_streak"], start=1975, anticipate=1982, extreme=2055, settled=2066, hold_end=2070,
        loc_a=(-1.35, 4.45, 2.05), loc_b=(0.85, 4.45, 2.45)
    )
    bake_event_transform(
        cam, start=1975, anticipate=1980, extreme=2045, settled=2060, hold_end=2070,
        loc_a=(-0.12, -2.15, 0.98), loc_b=(0.04, -2.02, 1.04),
        rot_a=(radians(93.5), 0.0, radians(-3.0)), rot_b=(radians(95.0), 0.0, radians(3.0))
    )

    # Cut 6B (f2071..2160): Crisp medium close-up on Neighbor's front praying face & city skyline
    bake_event_transform(
        cam, start=2071, anticipate=2075, extreme=2084, settled=2090, hold_end=2160,
        loc_a=(0.0, -1.78, 1.12), loc_b=(0.0, -1.58, 1.14),
        rot_a=(radians(88.0), 0.0, 0.0), rot_b=(radians(88.5), 0.0, 0.0)
    )

    # Cut 6C (f2161..2274): Snappy 8-frame framing onto neighbor_one_eye_wish + thought bubble zap at f2210!
    bake_event_transform(
        cam, start=2161, anticipate=2163, extreme=2167, settled=2169, hold_end=2274,
        loc_a=(0.0, -1.58, 1.14), loc_b=(0.0, -1.68, 1.26),
        rot_a=(radians(88.5), 0.0, 0.0), rot_b=(radians(89.5), 0.0, 0.0)
    )
    bake_event_transform(
        cast_p2["thought_zap"], start=2210, anticipate=2212, extreme=2216, settled=2221, hold_end=2274,
        scale_a=(0.65, 0.65, 0.65), scale_b=(1.0, 1.0, 1.0)
    )

    # --------------------------------------------------------------------------
    # SCENE 7 (Frames 2275 – 2715 | 75.8s – 90.5s): Newspaper, Stamp & Space CTA
    # --------------------------------------------------------------------------
    # Cut 7A (f2275..2445): Smooth top-down macro camera glide across 35%-narrower Coroner's Report
    bake_event_transform(
        cam, start=2275, anticipate=2285, extreme=2415, settled=2435, hold_end=2445,
        loc_a=(0.0, 0.14, 1.48), loc_b=(0.0, -0.14, 1.42),
        rot_a=(0.0, 0.0, 0.0), rot_b=(0.0, 0.0, 0.0)
    )

    # Cut 7B (f2446..2526): Heavy 3D rubber stamp slams down at f2455 + 7-frame decaying camera shake!
    st_tool = cd_set["stamp_tool"]
    st_tool.location = (0.0, -1.50, 2.50)
    st_tool.keyframe_insert(data_path="location", frame=2275)
    st_tool.location = (0.0, -1.50, 2.50)
    st_tool.keyframe_insert(data_path="location", frame=2450)
    st_tool.location = (0.0, -0.30, 0.85)
    st_tool.keyframe_insert(data_path="location", frame=2451)
    st_tool.location = (0.0, -0.30, 0.02)
    st_tool.keyframe_insert(data_path="location", frame=2455)
    st_tool.location = (0.0, -0.30, 0.02)
    st_tool.keyframe_insert(data_path="location", frame=2468)
    st_tool.location = (0.42, -0.45, 0.78)
    st_tool.keyframe_insert(data_path="location", frame=2478)
    set_fcurve_constant_after(st_tool, "location", 2478)

    desk_shakes = [
        (2446, (0.0, -0.14, 1.42), (0.0, 0.0, 0.0)),
        (2454, (0.0, -0.14, 1.42), (0.0, 0.0, 0.0)),
        (2455, (0.035, -0.11, 1.38), (radians(1.1), radians(-0.9), radians(0.7))),
        (2456, (-0.028, -0.17, 1.45), (radians(-0.9), radians(0.8), radians(-0.6))),
        (2457, (0.020, -0.12, 1.40), (radians(0.6), radians(-0.5), radians(0.4))),
        (2458, (-0.014, -0.15, 1.43), (radians(-0.4), radians(0.3), radians(-0.2))),
        (2459, (0.008, -0.13, 1.41), (radians(0.2), radians(-0.1), 0.0)),
        (2460, (-0.004, -0.14, 1.42), (0.0, 0.0, 0.0)),
        (2462, (0.0, -0.14, 1.42), (0.0, 0.0, 0.0)),
        (2526, (0.0, -0.14, 1.42), (0.0, 0.0, 0.0)),
    ]
    for f_s, loc_s, rot_s in desk_shakes:
        cam.location = Vector(loc_s)
        cam.rotation_euler = Euler(rot_s, 'XYZ')
        cam.keyframe_insert(data_path="location", frame=f_s)
        cam.keyframe_insert(data_path="rotation_euler", frame=f_s)
    set_fcurve_constant_after(cam, "location", 2462)
    set_fcurve_constant_after(cam, "rotation_euler", 2462)

    # Cut 7C (f2527..2715): SET_OUTER_SPACE — Stickman floats weightlessly above rotating Earth
    hero_root.location = (0.0, 0.35, 0.35)
    hero_root.rotation_euler = Euler((0.0, radians(-8.0), 0.0), 'XYZ')
    hero_root.keyframe_insert(data_path="location", frame=2527)
    hero_root.keyframe_insert(data_path="rotation_euler", frame=2527)
    set_fcurve_constant_after(hero_root, "location", 2527)
    set_fcurve_constant_after(hero_root, "rotation_euler", 2527)

    earth_obj = os_set["earth"]
    earth_obj.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
    earth_obj.keyframe_insert(data_path="rotation_euler", frame=2527)
    earth_obj.rotation_euler = Euler((0.0, 0.0, radians(28.0)), 'XYZ')
    earth_obj.keyframe_insert(data_path="rotation_euler", frame=2715)

    bake_event_transform(
        cam, start=2527, anticipate=2536, extreme=2665, settled=2690, hold_end=2715,
        loc_a=(0.0, -2.25, 1.15), loc_b=(0.0, -2.85, 1.28),
        rot_a=(radians(86.0), 0.0, 0.0), rot_b=(radians(84.5), 0.0, 0.0)
    )


# ------------------------------------------------------------------------------
# 7. CALIBRATION STILL RENDERER & 7x3 CONTACT SHEET BUILDER (`sheet_v1.jpg`)
# ------------------------------------------------------------------------------
CALIBRATION_SHOTS = [
    (70,   "Cut 1A: Living Room Hook"),
    (200,  "Cut 1B: X-Ray 38,269 Counter"),
    (320,  "Cut 1C: 1,30,000 Farts Orbit"),
    (425,  "Cut 2A: 9,000L Gas Sphere"),
    (550,  "Cut 2B: Bus & Tanker Fill"),
    (750,  "Cut 2C: 1-Sec Pelvic Nozzle"),
    (850,  "Cut 3A: 20 KM/S Plasma Beam"),
    (950,  "Cut 3B: Sniper vs Fart Chart"),
    (1045, "Cut 3C: 3D Sofa Shred"),
    (1145, "Cut 4A: 290 G Rocket Thrust"),
    (1250, "Cut 4B: 290 G Face Warp"),
    (1360, "Cut 4C: Blood Balloon Legs"),
    (1495, "Cut 5A: Mach 8 — 2 KM Up"),
    (1615, "Cut 5B: Mach Shockwave Cones"),
    (1830, "Cut 5C: Human Meteor Fire"),
    (2020, "Cut 6A: Rooftop OTS Meteor"),
    (2115, "Cut 6B: Neighbor Prayer Glow"),
    (2220, "Cut 6C: One-Eye Wish Granted"),
    (2360, "Cut 7A: Newspaper & Coroner"),
    (2485, "Cut 7B: 100% Natural Stamp"),
    (2620, "Cut 7C: Space Mooli Paratha"),
]


def render_calibration_sheet(scene):
    """
    Renders the 21 representative calibration stills at 540x960 (50% scale)
    and tiles them into a 7 columns x 3 rows contact sheet (`sheet_v1.jpg`).
    """
    print("[Calibration] Configuring 540x960 (50% scale) PNG output...")
    orig_x = scene.render.resolution_x
    orig_y = scene.render.resolution_y
    orig_pct = scene.render.resolution_percentage

    scene.render.resolution_x = 540
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    rendered_tiles = []
    for frame_num, label in CALIBRATION_SHOTS:
        out_png = os.path.join(CAL_DIR, f"f_{frame_num:04d}.png")
        scene.frame_set(frame_num)
        scene.render.filepath = out_png
        print(f"[Calibration] Rendering f_{frame_num:04d}.png ({label})...")
        bpy.ops.render.render(write_still=True)
        rendered_tiles.append((frame_num, label, out_png))

    # Restore full 1080x1920 delivery settings
    scene.render.resolution_x = orig_x
    scene.render.resolution_y = orig_y
    scene.render.resolution_percentage = orig_pct

    # Assemble 7 columns x 3 rows contact sheet using PIL
    cols, rows = 7, 3
    tile_w, tile_h = 540, 960
    pad = 8
    sheet_w = cols * tile_w + (cols + 1) * pad
    sheet_h = rows * tile_h + (rows + 1) * pad

    sheet = Image.new('RGB', (sheet_w, sheet_h), (18, 20, 26))
    f_label = load_font(28)

    for idx, (frame_num, label, png_path) in enumerate(rendered_tiles):
        r = idx // cols
        c = idx % cols
        x0 = pad + c * (tile_w + pad)
        y0 = pad + r * (tile_h + pad)

        if os.path.exists(png_path):
            tile_img = Image.open(png_path).convert('RGB')
            if tile_img.size != (tile_w, tile_h):
                tile_img = tile_img.resize((tile_w, tile_h), Image.Resampling.LANCZOS)
        else:
            tile_img = Image.new('RGB', (tile_w, tile_h), (40, 20, 25))

        tdraw = ImageDraw.Draw(tile_img)
        # Burn frame number & cut label banner into top-left corner of each tile
        tdraw.rounded_rectangle([12, 12, tile_w - 12, 68], radius=10, fill=(12, 16, 22), outline=(80, 255, 140), width=3)
        tdraw.text((24, 22), f"f{frame_num:04d} | {label}", font=f_label, fill=(255, 255, 255))

        sheet.paste(tile_img, (x0, y0))

    sheet.save(SHEET_PATH, "JPEG", quality=94)
    print(f"[Calibration v3] SUCCESS — 21-tile Contact Sheet v3 saved to: {SHEET_PATH}")


# ------------------------------------------------------------------------------
# 8. MAIN EXECUTION PIPELINE
# ------------------------------------------------------------------------------
def main(part1_blend_path=PART1_BLEND_PATH, full_blend_path=FULL_BLEND_PATH):
    # Ensure Part 1 .blend exists (or build it on the fly if running standalone)
    if not os.path.exists(part1_blend_path):
        print(f"[Part 2 Builder] {PART1_BLEND_PATH} not found on disk; running Part 1 builder first...")
        script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        import part1_sets_and_scenes_1_to_4 as part1
        part1.main(part1_blend_path)

    print(f"[Part 2 Builder] Opening Part 1 scene: {PART1_BLEND_PATH}")
    bpy.ops.wm.open_mainfile(filepath=part1_blend_path)
    # Force reload all images from disk to guarantee no stale cached textures
    for img in list(bpy.data.images):
        if img.filepath and os.path.exists(bpy.path.abspath(img.filepath)):
            try:
                img.reload()
            except Exception as e:
                print(f"[Part 2 Builder] Warning reloading {img.name}: {e}")
    scene = bpy.context.scene
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END

    print("[Part 2 Builder] Building Scenes 5–7 3D Sets (Stratosphere, Rooftop, Coroner Desk, Outer Space)...")
    st_set = build_set_stratosphere(scene)
    nr_set = build_set_neighbor_rooftop(scene)
    cd_set = build_set_coroner_desk(scene)
    os_set = build_set_outer_space(scene)

    print("[Part 2 Builder] Generating Part 2 PIL 2D Cel Sprites, Neighbor Rig & HUD Cards...")
    cast_p2 = extend_cast_and_hud_for_part2(scene)

    print("[Part 2 Builder] Animating Scenes 5, 6, and 7 (Frames 1426..2715)...")
    animate_part2_scenes(scene, st_set, nr_set, cd_set, os_set, cast_p2)

    from studio_overhaul import finish
    finish(scene)

    try:
        bpy.ops.file.pack_all()
    except Exception as exc:
        print(f"[Part 2 Builder] Warning during pack_all: {exc}")

    print(f"[Part 2 Builder] Saving complete 2,715-frame Blender 4.2 file to: {FULL_BLEND_PATH}")
    bpy.ops.wm.save_as_mainfile(filepath=full_blend_path)


if __name__ == "__main__":
    main()
