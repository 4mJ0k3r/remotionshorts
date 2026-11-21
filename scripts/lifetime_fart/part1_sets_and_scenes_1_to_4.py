# ==============================================================================
# FILE: part1_sets_and_scenes_1_to_4.py
# PROJECT: Lifetime Fart — 2.5D Story Video (Part 1: Scenes 1 to 4, f1..1425)
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
# 0. GLOBAL CONFIGURATION & OUTPUT PATHS
# ------------------------------------------------------------------------------
OUTPUT_BLEND_PATH = "D:/remotionshorts/output/blender/lifetime_fart_part1.blend"
ASSET_DIR = "D:/remotionshorts/output/blender/cel_assets_part1"

# Fallback to local temp directory if D:/ drive does not exist on audit machine
if not os.path.exists("D:/"):
    BASE_FALLBACK = os.path.abspath("./output/blender")
    OUTPUT_BLEND_PATH = os.path.join(BASE_FALLBACK, "lifetime_fart_part1.blend")
    ASSET_DIR = os.path.join(BASE_FALLBACK, "cel_assets_part1")

os.makedirs(os.path.dirname(OUTPUT_BLEND_PATH), exist_ok=True)
os.makedirs(ASSET_DIR, exist_ok=True)

FPS = 30
FRAME_START = 1
FRAME_END = 2715
PART1_LAST_FRAME = 1425

# Palette Constants
INK_RGBA = (53, 31, 34, 255)          # #351f22 Dark Marker Ink
INK_CLEAR = (22, 18, 25, 0)           # Dark RGB zero-alpha (Zero white halo!)
CREAM_RGBA = (253, 250, 242, 255)     # #fdfaf2 Organic Cream Head
FLUSH_CREAM_RGBA = (242, 224, 218, 255)
PALE_CREAM_RGBA = (232, 240, 248, 255)
CRESCENT_RGB = (95, 118, 152)         # Cool grey-blue crescent tint
SUIT_DARK = (36, 40, 52, 255)
SUIT_PANTS = (28, 31, 42, 255)
SHIRT_WHITE = (245, 246, 250, 255)
TIE_RED = (210, 45, 55, 255)
NEON_GREEN = (50, 255, 110, 255)
CYAN_XRAY = (30, 210, 245, 115)       # alpha ~ 0.45
BLOOD_RED = (225, 28, 38, 255)


# ------------------------------------------------------------------------------
# 1. FINITE BEAT-DRIVEN MOTION HELPERS (§2 Law — Ban Continuous Wobble)
# ------------------------------------------------------------------------------
def ease_out(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 1.0 - (1.0 - u) ** 3


def ease_in_out(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return 3.0 * u * u - 2.0 * u * u * u


def event_progress(f: float, start: int, anticipate: int, extreme: int, settled: int) -> float:
    """Mandatory §2 finite beat progression: anticipation -> extreme -> settle -> exact hold."""
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
                else:
                    kp.interpolation = 'LINEAR'


def enforce_constant_visibility(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path in ("hide_viewport", "hide_render"):
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


def bake_event_transform(obj, start: int, anticipate: int, extreme: int, settled: int, hold_end: int,
                         loc_a=None, loc_b=None, rot_a=None, rot_b=None, scale_a=None, scale_b=None):
    """Bakes a finite beat transition across frames and locks CONSTANT interpolation on settle."""
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

    # Key exact hold endpoint
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


# ------------------------------------------------------------------------------
# 2. PROCEDURAL 2D CEL & HUD SPRITE FACTORY (§1, §7.1, §7.3, §7.6 Laws)
# ------------------------------------------------------------------------------
def load_font(size: int):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/NirmalaB.ttf",
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


def warped_head_contours(cx: float, cy: float, rx: float, ry: float, count: int = 256, w0: float = 16.5):
    """290G extreme downward facial deformation contour (jowls/cheeks stretched downward)."""
    outer, inner = [], []
    for i in range(count):
        a = 2.0 * pi * i / count
        r = 1.0 + 0.022 * sin(2.0 * a + 0.6) - 0.015 * cos(3.0 * a - 0.8) + 0.008 * sin(5.0 * a + 1.9)
        w = w0 * max(0.25, 1.0 + 0.52 * cos(a - 2.35) + 0.22 * sin(3.0 * a + 1.1) + 0.14 * sin(5.0 * a - 0.7))
        ox = cx + (rx * r + w / 2.0) * cos(a)
        oy = cy + (ry * r + w / 2.0) * sin(a)
        ix = cx + (rx * r - w / 2.0) * cos(a)
        iy = cy + (ry * r - w / 2.0) * sin(a)
        # In PIL, +Y is downward: stretch lower hemisphere (sin(a) > 0) into heavy drooping jowls
        if sin(a) > -0.1:
            droop = (max(0.0, sin(a) + 0.1) ** 1.4) * 95.0
            jowl_lobe = max(0.0, sin(2.0 * a - 0.3)) * 38.0 if sin(a) > 0.2 else 0.0
            oy += droop + jowl_lobe
            iy += droop + jowl_lobe
            ox += cos(a) * 26.0 * max(0.0, sin(a))
            ix += cos(a) * 26.0 * max(0.0, sin(a))
        outer.append((ox, oy))
        inner.append((ix, iy))
    return outer, inner


def apply_15pct_crescent(base_rgba: Image.Image, inner_mask: Image.Image, shift_xy=(22, -18)) -> Image.Image:
    """Exact §1 / §7.3 15% cool grey-blue multiply crescent along bottom-left inner contour."""
    shifted = Image.new('L', inner_mask.size, 0)
    shifted.paste(inner_mask, shift_xy)
    crescent = ImageChops.subtract(inner_mask, shifted)
    crescent = crescent.filter(ImageFilter.GaussianBlur(5))
    crescent = ImageChops.multiply(crescent, inner_mask)

    # Scale alpha to 15% strength (0.15 * crescent)
    crescent_15 = crescent.point(lambda p: int(p * 0.15))
    cool_layer = Image.new('RGBA', base_rgba.size, (CRESCENT_RGB[0], CRESCENT_RGB[1], CRESCENT_RGB[2], 255))
    darkened = ImageChops.multiply(base_rgba, cool_layer)
    return Image.composite(darkened, base_rgba, crescent_15)


def draw_clipped_eye(canvas: Image.Image, cx: int, cy: int, rx: int, ry: int,
                     lid_top_ratio: float, lid_bot_ratio: float,
                     pupil_dx: int = 0, pupil_dy: int = 0,
                     droop_px: int = 0, bloodshot: bool = False):
    """§7.3 Solid dark oval pupils clipped by horizontal eyelid aperture (top <= y <= bottom)."""
    w, h = canvas.size
    eye_mask = Image.new('L', (w, h), 0)
    mdraw = ImageDraw.Draw(eye_mask)

    pts = []
    for i in range(64):
        a = 2.0 * pi * i / 64.0
        px = cx + rx * cos(a)
        py = cy + ry * sin(a) + (droop_px * max(0.0, sin(a)))
        pts.append((px, py))
    mdraw.polygon(pts, fill=255)

    y_min = cy - ry
    y_max = cy + ry + droop_px
    span = max(1, y_max - y_min)
    top_y = int(y_min + span * lid_top_ratio)
    bot_y = int(y_min + span * lid_bot_ratio)

    lid_clip = Image.new('L', (w, h), 0)
    ldraw = ImageDraw.Draw(lid_clip)
    ldraw.rectangle([0, top_y, w, bot_y], fill=255)

    final_eye_mask = ImageChops.multiply(eye_mask, lid_clip)

    eye_layer = Image.new('RGBA', (w, h), INK_CLEAR)
    edraw = ImageDraw.Draw(eye_layer)
    sclera_col = (255, 235, 235, 255) if bloodshot else (255, 255, 255, 255)
    edraw.rectangle([cx - rx - 10, y_min - 10, cx + rx + 10, y_max + 10], fill=sclera_col)

    # Solid dark oval pupil (NO white shine dots!)
    prx = int(rx * 0.48)
    pry = int(ry * 0.56)
    px0 = cx + pupil_dx - prx
    py0 = cy + pupil_dy - pry + int(droop_px * 0.35)
    edraw.ellipse([px0, py0, px0 + 2 * prx, py0 + 2 * pry], fill=INK_RGBA)

    eye_layer.putalpha(final_eye_mask)
    canvas.alpha_composite(eye_layer)

    # Draw crisp eyelid horizontal lines & outer ink boundary
    cdraw = ImageDraw.Draw(canvas)
    cdraw.polygon(pts, outline=INK_RGBA, width=8)
    if lid_top_ratio > 0.04:
        cdraw.line([(cx - rx - 4, top_y), (cx + rx + 4, top_y + int(droop_px * 0.2))], fill=INK_RGBA, width=9)
    if lid_bot_ratio < 0.96:
        cdraw.line([(cx - rx - 4, bot_y), (cx + rx + 4, bot_y)], fill=INK_RGBA, width=8)


def draw_teardrop_sweat(draw: ImageDraw.ImageDraw, sx: int, sy: int, scale: float = 1.0):
    """§7.4 Attached temple sweat droplet with pointed top and rounded bottom."""
    pts = [
        (sx, sy - int(26 * scale)),
        (sx + int(14 * scale), sy + int(4 * scale)),
        (sx + int(10 * scale), sy + int(18 * scale)),
        (sx, sy + int(24 * scale)),
        (sx - int(10 * scale), sy + int(18 * scale)),
        (sx - int(14 * scale), sy + int(4 * scale)),
    ]
    draw.polygon(pts, fill=(135, 225, 255, 235), outline=INK_RGBA, width=5)


def generate_head_sprite(filename: str, mode: str) -> str:
    """
    RicksClips House Style 2D Stickman Head (1024x1024 RGBA):
    - Rough circle cream head (#fdfaf2), 15% cool grey-blue bottom-left crescent shadow
    - Bold variable-width #161219 dark ink outline (14px-19px) + 3 curved hair strands on top
    - Solid #161219 vertical oval eyes directly on cream face (ZERO white sclera eyeballs/rings!)
    - Expressive floating black eyebrows (chevrons or horizontal half-lid clipping)
    """
    W, H = 1024, 1024
    canvas = Image.new('RGBA', (W, H), INK_CLEAR)
    cx, cy = 512, 520
    rx, ry = 285, 270
    ink_col = (22, 18, 25, 255)  # #161219

    if mode == '290g_warp':
        outer, inner = warped_head_contours(cx, cy, rx, ry, count=256, w0=17.5)
        skin_color = FLUSH_CREAM_RGBA
    elif mode == 'vascular':
        outer, inner = head_contours(cx, cy, rx, ry, count=256, w0=17.0)
        skin_color = PALE_CREAM_RGBA
    else:
        outer, inner = head_contours(cx, cy, rx, ry, count=256, w0=17.0)
        skin_color = CREAM_RGBA

    head_outer_mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(head_outer_mask).polygon(outer, fill=255)
    head_inner_mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(head_inner_mask).polygon(inner, fill=255)

    fill_layer = Image.new('RGBA', (W, H), skin_color)
    fill_layer = apply_15pct_crescent(fill_layer, head_inner_mask, shift_xy=(28, -22))
    fill_layer.putalpha(head_inner_mask)
    canvas = Image.alpha_composite(canvas, fill_layer)

    ink_band = ImageChops.subtract(head_outer_mask, head_inner_mask)
    ink_layer = Image.new('RGBA', (W, H), ink_col)
    ink_layer.putalpha(ink_band)
    canvas = Image.alpha_composite(canvas, ink_layer)

    draw = ImageDraw.Draw(canvas)

    # 3 small curved black hair strands on top of head (RicksClips signature)
    for hx_off, hy_off, dx in [(-45, -268, -28), (5, -275, 10), (55, -265, 42)]:
        x0, y0 = cx + hx_off, cy + hy_off
        pts = [(x0, y0 + 18), (x0 + dx // 2, y0 - 28), (x0 + dx, y0 - 52)]
        draw.line(pts, fill=ink_col, width=14, joint="curve")

    # Solid #161219 vertical oval eyes directly on cream face (NO white sclera!)
    eye_rx, eye_ry = 22, 34
    ex_L, ex_R = cx - 82, cx + 82
    ey = cy - 25

    if mode == 'bloated':
        # Tense wide solid oval eyes + worried chevron brows + puffed cheeks + temple sweat drops
        draw.ellipse([ex_L - eye_rx, ey - eye_ry, ex_L + eye_rx, ey + eye_ry], fill=ink_col)
        draw.ellipse([ex_R - eye_rx, ey - eye_ry, ex_R + eye_rx, ey + eye_ry], fill=ink_col)
        draw.line([(ex_L - 42, ey - 52), (ex_L + 28, ey - 76)], fill=ink_col, width=15)
        draw.line([(ex_R - 28, ey - 76), (ex_R + 42, ey - 52)], fill=ink_col, width=15)
        # Clenched wavy line mouth with puffed cheek arcs
        draw.line([(cx - 65, cy + 78), (cx - 20, cy + 68), (cx + 20, cy + 84), (cx + 65, cy + 74)], fill=ink_col, width=13)
        draw.arc([cx - 125, cy + 42, cx - 55, cy + 112], start=110, end=250, fill=ink_col, width=11)
        draw.arc([cx + 55, cy + 42, cx + 125, cy + 112], start=290, end=70, fill=ink_col, width=11)
        draw_teardrop_sweat(draw, cx - 210, cy - 75, scale=1.15)
        draw_teardrop_sweat(draw, cx + 215, cy - 45, scale=0.95)

    elif mode == 'xray':
        # Same RicksClips stickman head with focused "> <" chevron brows (NO skull, NO bones!)
        draw.ellipse([ex_L - eye_rx, ey - eye_ry, ex_L + eye_rx, ey + eye_ry], fill=ink_col)
        draw.ellipse([ex_R - eye_rx, ey - eye_ry, ex_R + eye_rx, ey + eye_ry], fill=ink_col)
        draw.line([(ex_L - 44, ey - 74), (ex_L + 30, ey - 52)], fill=ink_col, width=15)
        draw.line([(ex_R - 30, ey - 52), (ex_R + 44, ey - 74)], fill=ink_col, width=15)
        draw.arc([cx - 52, cy + 62, cx + 52, cy + 115], start=190, end=350, fill=ink_col, width=13)

    elif mode == '290g_warp':
        # 290G downward stretched solid oval eyes + heavy half-lid clipping + downward-stretched wavy mouth
        draw.chord([ex_L - 25, ey - 10, ex_L + 25, ey + 68], start=0, end=180, fill=ink_col)
        draw.chord([ex_R - 25, ey - 10, ex_R + 25, ey + 68], start=0, end=180, fill=ink_col)
        draw.line([(ex_L - 36, ey + 28), (ex_L + 36, ey + 34)], fill=ink_col, width=14)
        draw.line([(ex_R - 36, ey + 34), (ex_R + 36, ey + 28)], fill=ink_col, width=14)
        draw.line([(ex_L - 48, ey - 32), (ex_L + 28, ey - 65)], fill=ink_col, width=15)
        draw.line([(ex_R - 28, ey - 65), (ex_R + 48, ey - 32)], fill=ink_col, width=15)
        # Stretched jowl creases & downward-pulled wavy grimace
        draw.arc([cx - 195, cy + 45, cx - 45, cy + 235], start=20, end=160, fill=ink_col, width=10)
        draw.arc([cx + 45, cy + 45, cx + 195, cy + 235], start=20, end=160, fill=ink_col, width=10)
        mouth_pts = [
            (cx - 115, cy + 135), (cx - 55, cy + 102), (cx + 55, cy + 102),
            (cx + 115, cy + 135), (cx + 130, cy + 225), (cx, cy + 188), (cx - 130, cy + 225)
        ]
        draw.polygon(mouth_pts, fill=(135, 28, 38, 255), outline=ink_col, width=13)

    elif mode == 'vascular':
        # Half-lidded dizzy solid oval eyes on pale cream head
        draw.chord([ex_L - eye_rx, ey - eye_ry, ex_L + eye_rx, ey + eye_ry], start=0, end=180, fill=ink_col)
        draw.chord([ex_R - eye_rx, ey - eye_ry, ex_R + eye_rx, ey + eye_ry], start=0, end=180, fill=ink_col)
        draw.line([(ex_L - 34, ey), (ex_L + 34, ey)], fill=ink_col, width=14)
        draw.line([(ex_R - 34, ey), (ex_R + 34, ey)], fill=ink_col, width=14)
        draw.line([(ex_L - 40, ey - 62), (ex_L + 28, ey - 50)], fill=ink_col, width=13)
        draw.line([(ex_R - 28, ey - 50), (ex_R + 40, ey - 62)], fill=ink_col, width=13)
        draw.ellipse([cx - 38, cy + 72, cx + 38, cy + 118], fill=ink_col)

    out_path = os.path.join(ASSET_DIR, filename)
    canvas.save(out_path, "PNG")
    return out_path


def generate_body_sprite(filename: str, mode: str) -> str:
    """
    RicksClips House Style Stickman Body (1024x1536 RGBA):
    - Narrow vertical rounded pill/capsule torso (x: 432..592, width=160px; y: 435..865)
    - Bloated mode: slightly rounded belly (width=230px, x: 397..627)
    - Bright casual orange tee + dark-blue shorts (y: 815..935)
    - Thin curved #161219 stick arms and stick legs (width = 20px) with small black oval hands/shoes
    """
    W, H = 1024, 1536
    canvas = Image.new('RGBA', (W, H), INK_CLEAR)
    draw = ImageDraw.Draw(canvas)
    ink_col = (22, 18, 25, 255)  # #161219
    tee_orange = (238, 124, 42, 255)
    tee_stripe = (212, 92, 24, 255)
    shorts_navy = (38, 54, 82, 255)

    # 1. Draw thin curved stick legs & arms first (underneath pill torso)
    leg_w = 20
    if mode in ('vascular_blood', 'vascular'):
        # Upper thin stick legs + swollen bright-red teardrop bulbs at calves/ankles!
        draw.line([(472, 910), (445, 1140)], fill=ink_col, width=leg_w)
        draw.line([(552, 910), (579, 1140)], fill=ink_col, width=leg_w)
        # Red teardrop blood bulbs on lower legs
        draw.ellipse([365, 1085, 505, 1425], fill=BLOOD_RED, outline=ink_col, width=14)
        draw.ellipse([519, 1085, 659, 1425], fill=BLOOD_RED, outline=ink_col, width=14)
        # Highlight arcs inside blood bulbs
        draw.arc([388, 1130, 482, 1380], start=125, end=235, fill=(255, 165, 170, 230), width=10)
        draw.arc([542, 1130, 636, 1380], start=305, end=55, fill=(255, 165, 170, 230), width=10)
        # Flat black oval shoes
        draw.ellipse([345, 1395, 495, 1470], fill=ink_col)
        draw.ellipse([529, 1395, 679, 1470], fill=ink_col)
    else:
        # Thin stick legs (slightly bent at knee for seated/hovering posture)
        draw.line([(472, 910), (442, 1180), (452, 1425)], fill=ink_col, width=leg_w, joint="curve")
        draw.line([(552, 910), (582, 1180), (572, 1425)], fill=ink_col, width=leg_w, joint="curve")
        draw.ellipse([392, 1405, 488, 1465], fill=ink_col)
        draw.ellipse([536, 1405, 632, 1465], fill=ink_col)

    # Thin curved stick arms & small black oval hands
    if mode == 'bloated':
        # Arms curved outward gripping bloated belly / sofa edge
        draw.line([(415, 515), (305, 665), (365, 815)], fill=ink_col, width=leg_w, joint="curve")
        draw.line([(609, 515), (719, 665), (659, 815)], fill=ink_col, width=leg_w, joint="curve")
        draw.ellipse([338, 792, 396, 845], fill=ink_col)
        draw.ellipse([628, 792, 686, 845], fill=ink_col)
    else:
        draw.line([(435, 510), (345, 675), (385, 835)], fill=ink_col, width=leg_w, joint="curve")
        draw.line([(589, 510), (679, 675), (639, 835)], fill=ink_col, width=leg_w, joint="curve")
        draw.ellipse([358, 812, 414, 862], fill=ink_col)
        draw.ellipse([610, 812, 666, 862], fill=ink_col)

    # 2. Unified Masked Pill Torso & Shorts (§1 Union Mask Recipe)
    neck_mask = Image.new('L', (W, H), 0)
    shirt_mask = Image.new('L', (W, H), 0)
    shorts_mask = Image.new('L', (W, H), 0)

    ImageDraw.Draw(neck_mask).rounded_rectangle([482, 395, 542, 465], radius=18, fill=255)
    # Bloated belly width = 230px (x: 397..627) centered on 512; normal width = 160px (x: 432..592)
    t_left, t_right = (397, 627) if mode == 'bloated' else (432, 592)
    ImageDraw.Draw(shirt_mask).rounded_rectangle([t_left, 435, t_right, 865], radius=(t_right - t_left) // 2, fill=255)
    ImageDraw.Draw(shorts_mask).rounded_rectangle([432, 815, 592, 935], radius=38, fill=255)

    body_mask = ImageChops.lighter(neck_mask, ImageChops.lighter(shirt_mask, shorts_mask))
    body_inner_mask = body_mask.filter(ImageFilter.MinFilter(23))

    neck_paint = Image.new('RGBA', (W, H), CREAM_RGBA)
    shirt_paint = Image.new('RGBA', (W, H), tee_orange)
    sp_draw = ImageDraw.Draw(shirt_paint)
    # Subtle vertical casual tee stripes clipped inside inner mask
    for sx in range(t_left + 32, t_right - 16, 36):
        sp_draw.line([(sx, 435), (sx, 865)], fill=tee_stripe, width=8)

    # Glowing lime-green tummy aura inside belly on bloated & xray modes
    if mode in ('bloated', 'xray'):
        glow = Image.new('RGBA', (W, H), INK_CLEAR)
        gdraw = ImageDraw.Draw(glow)
        r_glow = 100 if mode == 'xray' else 85
        gdraw.ellipse([512 - r_glow, 685 - r_glow, 512 + r_glow, 685 + r_glow], fill=(78, 255, 86, 220))
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        shirt_paint = Image.alpha_composite(shirt_paint, glow)

    shirt_paint = apply_15pct_crescent(shirt_paint, body_inner_mask, shift_xy=(22, -16))
    shorts_paint = Image.new('RGBA', (W, H), shorts_navy)

    torso_cel = Image.new('RGBA', (W, H), INK_CLEAR)
    for paint, region in [(neck_paint, neck_mask), (shirt_paint, shirt_mask), (shorts_paint, shorts_mask)]:
        clipped = paint.copy()
        clipped.putalpha(ImageChops.multiply(paint.getchannel('A'), ImageChops.multiply(region, body_inner_mask)))
        torso_cel = Image.alpha_composite(torso_cel, clipped)

    ink_band = ImageChops.subtract(body_mask, body_inner_mask)
    ink_layer = Image.new('RGBA', (W, H), ink_col)
    ink_layer.putalpha(ink_band)
    torso_cel = Image.alpha_composite(torso_cel, ink_layer)

    canvas = Image.alpha_composite(canvas, torso_cel)
    out_path = os.path.join(ASSET_DIR, filename)
    canvas.save(out_path, "PNG")
    return out_path


def generate_hud_banner(filename: str, title: str, subtitle: str = "",
                        bg_col=(14, 20, 28, 244), border_col=(78, 255, 86, 255),
                        title_col=(255, 255, 255, 255), sub_col=(78, 255, 86, 255),
                        bar_compare: bool = False, bar_mode: str = "") -> str:
    """Generates high-contrast 100% English screen-space HUD cards (zero □□□□ boxes!)."""
    W, H = 1024, 384
    img = Image.new('RGBA', (W, H), INK_CLEAR)
    draw = ImageDraw.Draw(img)

    # Always force dark high-contrast slate background so white/green text is 100% legible
    safe_bg = (14, 20, 28, 245) if sum(bg_col[:3]) > 380 else bg_col
    safe_title = (255, 255, 255, 255) if sum(bg_col[:3]) > 380 else title_col
    safe_sub = (255, 215, 65, 255) if sum(bg_col[:3]) > 380 else sub_col

    draw.rounded_rectangle([24, 24, W - 24, H - 24], radius=32, fill=safe_bg, outline=border_col, width=8)
    f_big = load_font(60)
    f_med = load_font(42)
    f_sm = load_font(34)

    # Strip any non-ASCII characters to prevent □□□□ tofu boxes in Arial
    clean_title = title.encode("ascii", "ignore").decode("ascii").strip()
    clean_sub = subtitle.encode("ascii", "ignore").decode("ascii").strip()
    if filename == "hud_you_tag.png":
        clean_title = "<- YOU (AGE 25)"

    if not bar_compare:
        draw.text((64, 72), clean_title, font=f_big, fill=safe_title)
        if clean_sub:
            draw.text((64, 188), clean_sub, font=f_med, fill=safe_sub)
    else:
        draw.text((58, 42), clean_title, font=f_med, fill=(255, 255, 255, 255))
        if bar_mode == "sniper":
            draw.text((58, 118), "SNIPER BULLET (1 KM/S)", font=f_sm, fill=(210, 225, 235, 255))
            draw.rounded_rectangle([58, 162, 125, 202], radius=8, fill=(255, 255, 255, 255))
            draw.text((58, 222), "YOUR FART (20 KM/S - 20X FASTER!)", font=f_sm, fill=(78, 255, 86, 255))
            draw.rounded_rectangle([58, 268, W - 58, 326], radius=12, fill=(78, 255, 86, 255), outline=(255, 255, 255, 255), width=4)
        elif bar_mode == "thrust":
            draw.text((58, 118), "FIGHTER PILOT LIMIT (9 G)", font=f_sm, fill=(255, 215, 90, 255))
            draw.rounded_rectangle([58, 162, 145, 202], radius=8, fill=(255, 215, 90, 255))
            draw.text((58, 222), "YOUR BODY: 290 G-FORCE!", font=f_sm, fill=(255, 85, 95, 255))
            draw.rounded_rectangle([58, 268, W - 58, 326], radius=12, fill=(255, 45, 55, 255), outline=(255, 255, 255, 255), width=4)

    out_path = os.path.join(ASSET_DIR, filename)
    img.save(out_path, "PNG")
    return out_path


def generate_tapered_ribbon_png(filename: str) -> str:
    """§7.4 Tapered alpha-faded gas ribbon texture with pointed tips."""
    W, H = 256, 768
    img = Image.new('RGBA', (W, H), INK_CLEAR)
    px = img.load()
    for y in range(H):
        t = y / float(H - 1)
        center_x = 128.0 + 28.0 * sin(2.5 * pi * t)
        half_w = max(1.0, 72.0 * sin(pi * t))
        top_fade = min(1.0, (1.0 - t) * 1.6) * min(1.0, t * 3.5)
        for x in range(W):
            dist = abs(x - center_x)
            if dist <= half_w:
                radial = 1.0 - (dist / half_w) ** 1.6
                alpha = int(255 * 0.60 * radial * top_fade)
                px[x, y] = (65, 255, 120, alpha)
    out_path = os.path.join(ASSET_DIR, filename)
    img.save(out_path, "PNG")
    return out_path


# ------------------------------------------------------------------------------
# 3. BLENDER 4.2 SCENE INITIALIZATION & HARDWARE CONTRACT (§2 Law)
# ------------------------------------------------------------------------------
def init_blender_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    scene = bpy.context.scene
    scene.name = "LifetimeFart_Part1"

    # Render Engine: BLENDER_EEVEE_NEXT
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.eevee.use_raytracing = False
    scene.render.use_simplify = True
    scene.render.simplify_subdivision = 2
    scene.render.simplify_subdivision_render = 2

    # Resolution & Timing
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.frame_current = 1

    # Color Management: AgX
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    # World Setup with animated beat color capability
    world = bpy.data.worlds.new("StoryWorld")
    scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs[0].default_value = (0.08, 0.05, 0.07, 1.0)
        bg_node.inputs[1].default_value = 1.0

    return scene


# ------------------------------------------------------------------------------
# 4. SHADER & GEOMETRY BUILDER UTILITIES (Z-UP, EEVEE 4.2 COMPLIANT)
# ------------------------------------------------------------------------------
def make_opaque_mat(name: str, rgba=(0.8, 0.8, 0.8, 1.0), roughness=0.65, metallic=0.0,
                    emission_rgba=None, emission_strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.surface_render_method = 'DITHERED'
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission_rgba is not None and "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = emission_rgba
            bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def make_translucent_mat(name: str, rgba=(0.2, 1.0, 0.4, 0.45), emission_strength=2.2):
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
    """Creates an alpha-clipped or alpha-blended 2D cel material with zero white halo."""
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

    img_name = os.path.basename(image_path)
    existing_img = bpy.data.images.get(img_name)
    if existing_img:
        bpy.data.images.remove(existing_img)
    img = bpy.data.images.load(image_path, check_existing=False)
    img.reload()
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
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size_xyz[0], size_xyz[1], size_xyz[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_cylinder(name: str, radius: float, depth: float, loc_xyz, mat, col, parent=None,
                    rot_xyz=(0.0, 0.0, 0.0), vertices: int = 24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                        location=loc_xyz, rotation=rot_xyz)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_sphere(name: str, radius: float, loc_xyz, mat, col, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=16, radius=radius, location=loc_xyz)
    obj = bpy.context.active_object
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    link_to_collection(obj, col)
    if parent:
        obj.parent = parent
    return obj


def create_vertical_cel_plane(name: str, width: float, height: float, loc_xyz, mat, col, parent=None):
    """Creates a flat 2D cel card standing upright in Blender Z-UP (X=width, Z=height, facing -Y)."""
    mesh = bpy.data.meshes.new(name + "_Mesh")
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    obj.location = loc_xyz
    if parent:
        obj.parent = parent

    hw = width * 0.5
    hh = height * 0.5
    # Local XY plane with +Z facing out and +Y up so DAMPED_TRACK (TRACK_Z) works natively (§7.1 Law)
    verts = [
        (-hw, -hh, 0.0),
        (hw, -hh, 0.0),
        (hw, hh, 0.0),
        (-hw, hh, 0.0),
    ]
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    uv_layer = mesh.uv_layers.new(name="UVMap")
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for loop_idx, uv in enumerate(uvs):
        uv_layer.data[loop_idx].uv = uv

    # Default upright orientation facing camera at -Y (local +Z points along world -Y, local +Y along world +Z)
    obj.rotation_euler = Euler((radians(90.0), 0.0, 0.0), 'XYZ')
    if mat:
        obj.data.materials.append(mat)
    return obj


# ------------------------------------------------------------------------------
# 5. BUILD REUSABLE 3D SETS (ISOLATED COLLECTIONS & ROOT EMPTIES)
# ------------------------------------------------------------------------------
def set_root_visibility(root_obj, col, visible_ranges):
    """Keyframes CONSTANT visibility on root, its recursive children, or collection objects."""
    if root_obj is not None and len(root_obj.children_recursive) > 0:
        all_objs = [root_obj] + list(root_obj.children_recursive)
    elif col is not None:
        all_objs = [root_obj] + list(col.objects)
    else:
        all_objs = [root_obj]

    critical_frames = {1, PART1_LAST_FRAME + 1, FRAME_END}
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


def build_set_living_room(scene):
    """
    SET_LIVING_ROOM: Detailed painterly 3D living room with wood-plank floor grooves,
    baseboards, framed wall painting, standing floor lamp, sunset window mullions casting
    diagonal light bars, plush sofa, and explosive sofa debris for Cut 3C.
    """
    col = bpy.data.collections.new("SET_LIVING_ROOM")
    scene.collection.children.link(col)
    root = bpy.data.objects.new("ROOT_LIVING_ROOM", None)
    col.objects.link(root)

    mat_floor = make_opaque_mat("LR_FloorWood", (0.34, 0.19, 0.10, 1.0), roughness=0.50)
    mat_plank_seam = make_opaque_mat("LR_PlankSeam", (0.16, 0.08, 0.04, 1.0), roughness=0.70)
    mat_wall = make_opaque_mat("LR_WallWarm", (0.82, 0.64, 0.48, 1.0), roughness=0.75)
    mat_trim = make_opaque_mat("LR_TrimWood", (0.20, 0.11, 0.06, 1.0), roughness=0.45)
    mat_rug = make_opaque_mat("LR_RugTeal", (0.16, 0.38, 0.42, 1.0), roughness=0.85)
    mat_curtain = make_opaque_mat("LR_CurtainRed", (0.72, 0.14, 0.16, 1.0), roughness=0.70)
    mat_sofa = make_opaque_mat("LR_SofaPlush", (0.64, 0.25, 0.18, 1.0), roughness=0.72)
    mat_sofa_wood = make_opaque_mat("LR_SofaWood", (0.22, 0.12, 0.06, 1.0), roughness=0.48)
    mat_art_canvas = make_opaque_mat("LR_ArtCanvas", (0.92, 0.78, 0.52, 1.0), roughness=0.60)
    mat_lamp_shade = make_opaque_mat("LR_LampShade", (1.0, 0.88, 0.58, 1.0), roughness=0.40,
                                     emission_rgba=(1.0, 0.82, 0.45, 1.0), emission_strength=2.2)
    mat_shadow_disc = make_translucent_mat("LR_ContactShadow", (0.02, 0.01, 0.02, 0.55), emission_strength=0.0)
    mat_spring = make_opaque_mat("LR_MetalSpring", (0.72, 0.75, 0.80, 1.0), roughness=0.25, metallic=0.88)

    # Wood-Plank Floor + Plank Groove Lines
    create_box("LR_Floor", (8.0, 8.0, 0.1), (0.0, 0.0, -0.05), mat_floor, col, root)
    for px in [i * 0.35 for i in range(-8, 9)]:
        create_box(f"LR_PlankGroove_{px:.2f}", (0.012, 6.0, 0.004), (px, 0.2, 0.003), mat_plank_seam, col, root)

    create_box("LR_Rug", (2.8, 1.7, 0.016), (0.0, 0.15, 0.008), mat_rug, col, root)
    create_box("LR_BackWall", (8.0, 0.2, 5.0), (0.0, 2.2, 2.5), mat_wall, col, root)
    create_box("LR_Baseboard", (8.0, 0.24, 0.20), (0.0, 2.12, 0.10), mat_trim, col, root)
    create_box("LR_WainscotRail", (8.0, 0.23, 0.06), (0.0, 2.13, 0.95), mat_trim, col, root)

    # Framed Wall Painting & Standing Floor Lamp for rich 3D background depth
    create_box("LR_PaintingFrame", (1.15, 0.06, 0.78), (-0.75, 2.08, 1.72), mat_trim, col, root)
    create_box("LR_PaintingCanvas", (1.02, 0.07, 0.65), (-0.75, 2.07, 1.72), mat_art_canvas, col, root)
    create_cylinder("LR_LampBase", 0.20, 0.05, (-1.35, 1.25, 0.025), mat_trim, col, root)
    create_cylinder("LR_LampPole", 0.028, 1.55, (-1.35, 1.25, 0.80), mat_trim, col, root)
    create_cylinder("LR_LampShade", 0.24, 0.34, (-1.35, 1.25, 1.62), mat_lamp_shade, col, root)

    # Window Wall on Right (+X) with Mullions casting sharp diagonal golden bars
    create_box("LR_WinWall_Bot", (0.2, 6.0, 0.85), (2.4, 0.0, 0.42), mat_wall, col, root)
    create_box("LR_WinWall_Top", (0.2, 6.0, 1.4), (2.4, 0.0, 4.2), mat_wall, col, root)
    for wy in (-1.2, -0.6, 0.0, 0.6, 1.2):
        create_box(f"LR_Mullion_V_{wy}", (0.12, 0.09, 2.8), (2.35, wy, 2.2), mat_trim, col, root)
    for wz in (1.3, 1.85, 2.4, 2.95):
        create_box(f"LR_Mullion_H_{wz}", (0.12, 3.2, 0.08), (2.35, 0.0, wz), mat_trim, col, root)

    for cx in (-1.65, 1.65):
        create_box(f"LR_Curtain_{cx}", (0.48, 0.16, 3.4), (cx, 1.98, 1.8), mat_curtain, col, root)

    create_box("LR_SofaContactShadow", (2.25, 1.10, 0.005), (0.0, 0.45, 0.020), mat_shadow_disc, col, root)
    create_cylinder("LR_FootShadow_L", 0.16, 0.006, (-0.15, -0.02, 0.022), mat_shadow_disc, col, root)
    create_cylinder("LR_FootShadow_R", 0.16, 0.006, (0.15, -0.02, 0.022), mat_shadow_disc, col, root)

    # Intact Plush Sofa Assembly
    sofa_grp = bpy.data.objects.new("LR_Sofa_Intact", None)
    col.objects.link(sofa_grp)
    sofa_grp.parent = root
    create_box("Sofa_Base", (2.05, 0.92, 0.24), (0.0, 0.45, 0.20), mat_sofa_wood, col, sofa_grp)
    create_box("Sofa_SeatCushion_L", (0.88, 0.86, 0.18), (-0.45, 0.42, 0.40), mat_sofa, col, sofa_grp)
    create_box("Sofa_SeatCushion_R", (0.88, 0.86, 0.18), (0.45, 0.42, 0.40), mat_sofa, col, sofa_grp)
    create_box("Sofa_Backrest", (1.88, 0.26, 0.72), (0.0, 0.80, 0.82), mat_sofa, col, sofa_grp)
    create_box("Sofa_Arm_L", (0.24, 0.95, 0.52), (-0.95, 0.45, 0.55), mat_sofa, col, sofa_grp)
    create_box("Sofa_Arm_R", (0.24, 0.95, 0.52), (0.95, 0.45, 0.55), mat_sofa, col, sofa_grp)
    for lx, ly in [(-0.88, 0.06), (0.88, 0.06), (-0.88, 0.84), (0.88, 0.84)]:
        create_cylinder(f"Sofa_Leg_{lx}_{ly}", 0.045, 0.10, (lx, ly, 0.05), mat_sofa_wood, col, sofa_grp)

    # Explosive Sofa Shred Debris for Cut 3C (f1006..1086)
    debris_pieces = []
    debris_specs = [
        ("Shred_Cushion_L", "box", (0.68, 0.58, 0.20), (-0.30, 0.35, 0.42), (-0.75, -0.85, 1.25), (2.4, -1.8, 1.5), mat_sofa),
        ("Shred_Cushion_R", "box", (0.68, 0.58, 0.20), (0.30, 0.35, 0.42), (0.78, -0.80, 1.18), (-2.1, 2.2, -1.4), mat_sofa),
        ("Shred_Arm_L", "box", (0.24, 0.75, 0.42), (-0.82, 0.38, 0.52), (-0.95, -0.60, 0.85), (1.5, 2.8, -1.9), mat_sofa),
        ("Shred_Arm_R", "box", (0.24, 0.75, 0.42), (0.82, 0.38, 0.52), (0.95, -0.65, 0.90), (-1.8, -2.5, 2.1), mat_sofa),
        ("Shred_Plank_1", "box", (0.85, 0.14, 0.05), (-0.18, 0.30, 0.28), (-0.55, -1.10, 1.48), (3.6, 1.9, -2.8), mat_sofa_wood),
        ("Shred_Plank_2", "box", (0.85, 0.14, 0.05), (0.20, 0.30, 0.28), (0.58, -1.15, 1.42), (-3.2, -2.4, 2.5), mat_sofa_wood),
        ("Shred_Plank_3", "box", (0.78, 0.12, 0.05), (0.0, 0.40, 0.32), (0.08, -1.25, 0.55), (4.1, -1.2, 1.8), mat_sofa_wood),
        ("Shred_Spring_1", "cyl", (0.08, 0.28, 0.08), (-0.25, 0.32, 0.40), (-0.42, -1.15, 1.28), (4.5, 3.1, -2.0), mat_spring),
        ("Shred_Spring_2", "cyl", (0.08, 0.28, 0.08), (0.25, 0.32, 0.40), (0.46, -1.20, 1.22), (-4.2, 2.9, 3.1), mat_spring),
        ("Shred_Spring_3", "cyl", (0.08, 0.28, 0.08), (0.0, 0.30, 0.38), (0.04, -1.30, 1.55), (3.8, -3.5, 1.4), mat_spring),
    ]
    for name, kind, sz, p0, p1, rot1, mat in debris_specs:
        if kind == "box":
            obj = create_box(name, sz, p0, mat, col, root)
        else:
            obj = create_cylinder(name, sz[0], sz[1], p0, mat, col, root)
        debris_pieces.append((obj, p0, p1, rot1))

    # Sharp Sunset Directional Sun casting diagonal window bars (§7.5)
    sun_data = bpy.data.lights.new(name="LR_SunsetKey", type='SUN')
    sun_data.energy = 3.8
    sun_data.color = (1.0, 0.78, 0.50)
    sun_data.angle = radians(6.0)
    sun_data.use_shadow = True
    sun_obj = bpy.data.objects.new(name="LR_SunsetKey", object_data=sun_data)
    col.objects.link(sun_obj)
    sun_obj.parent = root
    sun_obj.location = (3.2, -1.2, 3.0)
    direction = Vector((-1.0, 0.35, -0.52)).normalized()
    sun_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    fill_data = bpy.data.lights.new(name="LR_WarmFill", type='AREA')
    fill_data.energy = 35.0
    fill_data.color = (1.0, 0.88, 0.76)
    fill_data.size = 2.5
    fill_obj = bpy.data.objects.new(name="LR_WarmFill", object_data=fill_data)
    col.objects.link(fill_obj)
    fill_obj.parent = root
    fill_obj.location = (-2.0, -2.2, 2.0)
    fill_obj.rotation_euler = Euler((radians(60.0), 0.0, radians(-35.0)), 'XYZ')

    leak_data = bpy.data.lights.new(name="LR_GreenLeakLight", type='POINT')
    leak_data.energy = 0.0
    leak_data.color = (0.30, 1.0, 0.34)
    leak_obj = bpy.data.objects.new(name="LR_GreenLeakLight", object_data=leak_data)
    col.objects.link(leak_obj)
    leak_obj.parent = root
    leak_obj.location = (0.0, 0.25, 0.42)

    return {
        "col": col,
        "root": root,
        "sofa_intact": sofa_grp,
        "debris": debris_pieces,
        "leak_light": leak_obj,
    }


def build_set_xray_grid(scene):
    """
    SET_XRAY_GRID: Crisp dark cyan (#072227) 3D wireframe grid room with zero bloom washout
    and a narrow (r=0.14m), semi-transparent (alpha=0.65) lime-green (#4eff56) tapered beam
    positioned strictly BELOW the stickman's seated hips!
    """
    col = bpy.data.collections.new("SET_XRAY_GRID")
    scene.collection.children.link(col)
    root = bpy.data.objects.new("ROOT_XRAY_GRID", None)
    col.objects.link(root)

    mat_bg = make_opaque_mat("XR_DarkCyanFloor", (0.027, 0.133, 0.153, 1.0), roughness=0.90)
    mat_grid = make_opaque_mat("XR_CyanGlowLine", (0.12, 0.88, 0.98, 1.0), roughness=0.4,
                               emission_rgba=(0.12, 0.88, 0.98, 1.0), emission_strength=1.15)
    mat_wire_sofa = make_translucent_mat("XR_WireSofaMat", (0.12, 0.82, 0.96, 0.24), emission_strength=0.9)
    mat_gas_orb = make_translucent_mat("XR_NeonGasMat", (0.306, 1.0, 0.337, 0.42), emission_strength=1.35)
    # Narrow translucent lime-green (#4eff56) beam (alpha=0.65, emission=1.45 -> NEVER blows out to white!)
    mat_plasma = make_translucent_mat("XR_PlasmaBeamMat", (0.306, 1.0, 0.337, 0.65), emission_strength=1.45)
    mat_nozzle = make_opaque_mat("XR_NozzleWhite", (0.85, 1.0, 0.88, 1.0), roughness=0.3,
                                 emission_rgba=(0.45, 1.0, 0.55, 1.0), emission_strength=1.5)

    create_box("XR_Floor", (12.0, 12.0, 0.08), (0.0, 0.0, -0.04), mat_bg, col, root)
    create_box("XR_BackWall", (12.0, 0.1, 8.0), (0.0, 3.8, 4.0), mat_bg, col, root)

    for i in range(-5, 6):
        gx = i * 0.75
        create_box(f"XR_GridFloor_X_{i}", (0.018, 8.0, 0.008), (gx, 0.5, 0.005), mat_grid, col, root)
        create_box(f"XR_GridFloor_Y_{i}", (8.0, 0.018, 0.008), (0.0, gx + 0.5, 0.005), mat_grid, col, root)
        create_box(f"XR_GridWall_V_{i}", (0.018, 0.018, 6.5), (gx, 3.72, 3.25), mat_grid, col, root)
    for j in range(1, 8):
        gz = j * 0.75
        create_box(f"XR_GridWall_H_{j}", (8.0, 0.018, 0.018), (0.0, 3.72, gz), mat_grid, col, root)

    wire_sofa = bpy.data.objects.new("XR_WireframeSofa", None)
    col.objects.link(wire_sofa)
    wire_sofa.parent = root
    create_box("XR_SofaSeat", (1.90, 0.88, 0.24), (0.0, 0.42, 0.36), mat_wire_sofa, col, wire_sofa)
    create_box("XR_SofaBack", (1.90, 0.24, 0.70), (0.0, 0.78, 0.82), mat_wire_sofa, col, wire_sofa)
    create_box("XR_SofaArmL", (0.24, 0.92, 0.50), (-0.96, 0.42, 0.54), mat_wire_sofa, col, wire_sofa)
    create_box("XR_SofaArmR", (0.24, 0.92, 0.50), (0.96, 0.42, 0.54), mat_wire_sofa, col, wire_sofa)

    ribbon_png = generate_tapered_ribbon_png("gas_ribbon_tapered.png")
    mat_ribbon = make_cel_sprite_mat("XR_GasRibbonMat", ribbon_png, blended=True, emission_boost=0.9)
    ribbons = []
    for idx, rx in enumerate((-0.26, 0.0, 0.26)):
        rib = create_vertical_cel_plane(f"XR_GasRibbon_{idx}", 0.26, 0.78, (rx, 0.55, 0.72), mat_ribbon, col, root)
        ribbons.append(rib)

    orbs = []
    orb_coords = [(-0.38, 0.48, 0.55), (0.40, 0.48, 0.62), (-0.26, 0.55, 0.72), (0.28, 0.55, 0.68), (0.0, 0.58, 0.80)]
    for idx, oc in enumerate(orb_coords):
        orb = create_sphere(f"XR_GasOrb_{idx}", 0.09, oc, mat_gas_orb, col, root)
        orbs.append((orb, oc))

    # 9,000L Gas Sphere positioned BEHIND Hero (Y = 0.85m) so Hero remains 100% crisp in front
    gas_sphere_9000 = create_sphere("XR_GasSphere_9000L", 0.95, (0.0, 0.85, 0.88), mat_gas_orb, col, root)

    # Coin-sized Nozzle Ring & Narrow Lime-Green Laser Cone strictly BELOW seated hips (Z <= 0.52m)
    nozzle_ring = create_cylinder("XR_NozzleRing", 0.075, 0.02, (0.0, 0.36, 0.52), mat_nozzle, col, root)
    laser_cone = create_cylinder("XR_LaserCone", 0.12, 0.52, (0.0, 0.38, 0.25), mat_plasma, col, root)

    # Narrow (r=0.14m), semi-transparent lime-green beam strictly BELOW seated hips (Z = 0.26, depth = 0.52 -> top at Z = 0.52!)
    plasma_beam = create_cylinder("XR_PlasmaBeam", 0.14, 0.52, (0.0, 0.38, 0.26), mat_plasma, col, root)
    shock_ring_1 = create_cylinder("XR_ShockRing_1", 0.45, 0.015, (0.0, 0.38, 0.02), mat_plasma, col, root)
    shock_ring_2 = create_cylinder("XR_ShockRing_2", 0.82, 0.015, (0.0, 0.38, 0.02), mat_grid, col, root)

    rim_data = bpy.data.lights.new(name="XR_NeonRimLight", type='AREA')
    rim_data.energy = 18.0
    rim_data.color = (0.15, 0.90, 1.0)
    rim_data.size = 3.0
    rim_obj = bpy.data.objects.new(name="XR_NeonRimLight", object_data=rim_data)
    col.objects.link(rim_obj)
    rim_obj.parent = root
    rim_obj.location = (0.0, 1.8, 2.4)
    rim_obj.rotation_euler = Euler((radians(-45.0), 0.0, 0.0), 'XYZ')

    return {
        "col": col,
        "root": root,
        "wire_sofa": wire_sofa,
        "ribbons": ribbons,
        "orbs": orbs,
        "gas_sphere_9000": gas_sphere_9000,
        "nozzle_ring": nozzle_ring,
        "laser_cone": laser_cone,
        "plasma_beam": plasma_beam,
        "shock_ring_1": shock_ring_1,
        "shock_ring_2": shock_ring_2,
    }


def build_set_vehicles(scene):
    """
    SET_VEHICLES (Cut 2B: f466..630): Both Yellow School Bus (left) and Blue Water Tanker (right)
    positioned compactly inside X = -1.4m..+1.4m so 100% of both vehicles fit in frame!
    """
    col = bpy.data.collections.new("SET_VEHICLES")
    scene.collection.children.link(col)
    root = bpy.data.objects.new("ROOT_VEHICLES", None)
    col.objects.link(root)

    mat_asphalt = make_opaque_mat("VH_Asphalt", (0.16, 0.18, 0.22, 1.0), roughness=0.80)
    mat_sky_wall = make_opaque_mat("VH_SkyBackdrop", (0.52, 0.76, 0.96, 1.0), roughness=0.90,
                                   emission_rgba=(0.52, 0.76, 0.96, 1.0), emission_strength=0.65)
    mat_bus_yellow = make_opaque_mat("VH_BusYellow", (0.96, 0.70, 0.06, 1.0), roughness=0.42)
    mat_bus_glass = make_translucent_mat("VH_BusGlass", (0.72, 0.92, 1.0, 0.28), emission_strength=0.3)
    mat_tire = make_opaque_mat("VH_TireBlack", (0.06, 0.06, 0.07, 1.0), roughness=0.85)
    mat_tanker_blue = make_opaque_mat("VH_TankerBlue", (0.18, 0.48, 0.82, 1.0), roughness=0.48)
    mat_tanker_glass = make_translucent_mat("VH_TankerCutaway", (0.28, 0.70, 0.96, 0.30), emission_strength=0.3)
    mat_gas_fill = make_translucent_mat("VH_GreenGasFill", (0.306, 1.0, 0.337, 0.68), emission_strength=1.55)

    create_box("VH_RoadFloor", (12.0, 10.0, 0.1), (0.0, 0.0, -0.05), mat_asphalt, col, root)
    create_box("VH_SkyWall", (12.0, 0.1, 9.0), (0.0, 3.5, 4.0), mat_sky_wall, col, root)

    # LEFT: Yellow School Bus centered at X = -0.68m
    bus_grp = bpy.data.objects.new("VH_SchoolBus", None)
    col.objects.link(bus_grp)
    bus_grp.parent = root
    bus_grp.location = (-0.68, 0.40, 0.0)
    bus_grp.scale = (0.78, 0.78, 0.78)

    create_box("Bus_LowerBody", (1.24, 0.74, 0.48), (0.0, 0.0, 0.42), mat_bus_yellow, col, bus_grp)
    create_box("Bus_Roof", (1.24, 0.74, 0.10), (0.0, 0.0, 1.08), mat_bus_yellow, col, bus_grp)
    create_box("Bus_Nose", (0.24, 0.68, 0.42), (-0.72, 0.0, 0.39), mat_bus_yellow, col, bus_grp)
    create_box("Bus_GlassCab", (1.18, 0.70, 0.42), (0.0, 0.0, 0.84), mat_bus_glass, col, bus_grp)

    bus_windows = []
    for wx in (-0.40, 0.0, 0.40):
        win = create_box(f"Bus_Window_{wx}", (0.30, 0.76, 0.34), (wx, 0.0, 0.84), mat_bus_glass, col, bus_grp)
        bus_windows.append(win)

    for wx in (-0.44, 0.40):
        for wy in (-0.36, 0.36):
            create_cylinder(f"Bus_Wheel_{wx}_{wy}", 0.18, 0.12, (wx, wy, 0.18), mat_tire, col, bus_grp,
                            rot_xyz=(radians(90.0), 0.0, 0.0))

    bus_gas = create_box("Bus_RisingGas", (1.14, 0.66, 0.82), (0.0, 0.0, 0.62), mat_gas_fill, col, bus_grp)

    # RIGHT: Blue Indian Water Tanker centered at X = +0.68m
    tanker_grp = bpy.data.objects.new("VH_WaterTanker", None)
    col.objects.link(tanker_grp)
    tanker_grp.parent = root
    tanker_grp.location = (0.68, 0.40, 0.0)
    tanker_grp.scale = (0.78, 0.78, 0.78)

    create_box("Tanker_Chassis", (1.22, 0.68, 0.16), (0.0, 0.0, 0.26), mat_tire, col, tanker_grp)
    create_box("Tanker_Cab", (0.34, 0.68, 0.64), (-0.52, 0.0, 0.62), mat_tanker_blue, col, tanker_grp)
    create_cylinder("Tanker_DrumShell", 0.36, 0.92, (0.14, 0.0, 0.70), mat_tanker_glass, col, tanker_grp,
                    rot_xyz=(0.0, radians(90.0), 0.0))
    for wx in (-0.42, 0.40):
        for wy in (-0.34, 0.34):
            create_cylinder(f"Tanker_Wheel_{wx}_{wy}", 0.18, 0.12, (wx, wy, 0.18), mat_tire, col, tanker_grp,
                            rot_xyz=(radians(90.0), 0.0, 0.0))

    tanker_gas = create_box("Tanker_RisingGas", (0.86, 0.60, 0.64), (0.14, 0.0, 0.68), mat_gas_fill, col, tanker_grp)

    v_sun_data = bpy.data.lights.new(name="VH_SunKey", type='SUN')
    v_sun_data.energy = 3.6
    v_sun_data.color = (1.0, 0.95, 0.86)
    v_sun_data.angle = radians(10.0)
    v_sun_obj = bpy.data.objects.new(name="VH_SunKey", object_data=v_sun_data)
    col.objects.link(v_sun_obj)
    v_sun_obj.parent = root
    v_sun_obj.rotation_euler = Euler((radians(48.0), radians(-22.0), radians(25.0)), 'XYZ')

    return {
        "col": col,
        "root": root,
        "bus_gas": bus_gas,
        "tanker_gas": tanker_gas,
        "bus_windows": bus_windows,
    }


def build_set_sky_ascent(scene):
    """
    SET_SKY_ASCENT (Cut 4B & 4C: f1207..1425): Bright blue sky with 3D puffy clouds
    rushing rapidly downward past the ascending Hero.
    """
    col = bpy.data.collections.new("SET_SKY_ASCENT")
    scene.collection.children.link(col)
    root = bpy.data.objects.new("ROOT_SKY_ASCENT", None)
    col.objects.link(root)

    mat_sky = make_opaque_mat("SKY_BackdropBlue", (0.16, 0.52, 0.92, 1.0), roughness=0.9,
                              emission_rgba=(0.18, 0.56, 0.95, 1.0), emission_strength=1.2)
    mat_cloud = make_opaque_mat("SKY_CloudWhite", (0.96, 0.98, 1.0, 1.0), roughness=0.85,
                                emission_rgba=(0.92, 0.95, 1.0, 1.0), emission_strength=0.45)

    create_box("SKY_Backdrop", (12.0, 0.1, 16.0), (0.0, 3.6, 2.0), mat_sky, col, root)

    clouds_master = bpy.data.objects.new("SKY_CloudsMaster", None)
    col.objects.link(clouds_master)
    clouds_master.parent = root

    cloud_offsets = [
        (-1.1, 1.2, 1.5, 0.45), (1.15, 1.4, 2.8, 0.52), (-0.95, 1.0, 4.2, 0.42),
        (1.05, 1.3, 5.6, 0.48), (-1.2, 1.5, 7.2, 0.55), (0.95, 1.1, 8.8, 0.46),
        (-0.85, 1.2, 10.4, 0.50), (1.1, 1.4, 12.0, 0.52),
    ]
    for idx, (cx, cy, cz, rad) in enumerate(cloud_offsets):
        c1 = create_sphere(f"Cloud_{idx}_A", rad, (cx, cy, cz), mat_cloud, col, clouds_master)
        c2 = create_sphere(f"Cloud_{idx}_B", rad * 0.78, (cx + rad * 0.65, cy - 0.05, cz - 0.1), mat_cloud, col, clouds_master)
        c3 = create_sphere(f"Cloud_{idx}_C", rad * 0.72, (cx - rad * 0.60, cy + 0.05, cz - 0.12), mat_cloud, col, clouds_master)

    sky_sun_data = bpy.data.lights.new(name="SKY_SunKey", type='SUN')
    sky_sun_data.energy = 4.0
    sky_sun_data.color = (1.0, 0.98, 0.94)
    sky_sun_obj = bpy.data.objects.new(name="SKY_SunKey", object_data=sky_sun_data)
    col.objects.link(sky_sun_obj)
    sky_sun_obj.parent = root
    sky_sun_obj.rotation_euler = Euler((radians(55.0), 0.0, radians(-20.0)), 'XYZ')

    return {
        "col": col,
        "root": root,
        "clouds_master": clouds_master,
    }


# ------------------------------------------------------------------------------
# 6. BUILD FLAT 2D CEL HERO CAST & SCREEN-SPACE HUD CARDS (§1, §7.1, §7.6)
# ------------------------------------------------------------------------------
def build_hero_cel_rig(scene, cam_aim_helper):
    """
    Builds the Hero 2D Cel Cast Assembly with an independent camera-facing DAMPED_TRACK head pivot (§7.1)
    and state-swappable body/head sprites (`hero_bloated`, `hero_xray_skeleton`, `hero_290g_warp`, `hero_vascular_blood`).
    """
    col = bpy.data.collections.new("CAST_HERO_2D")
    scene.collection.children.link(col)

    hero_root = bpy.data.objects.new("Hero_Root", None)
    col.objects.link(hero_root)
    # Default seated anchor on sofa cushion
    hero_root.location = (0.0, 0.35, 0.0)

    # Independent Camera-Facing Head Pivot at Neck Attachment (§7.1 Mandatory Law)
    head_pivot = bpy.data.objects.new("Hero_Head_BillboardPivot", None)
    col.objects.link(head_pivot)
    head_pivot.parent = hero_root
    head_pivot.location = (0.0, -0.02, 1.18)

    # Add DAMPED_TRACK constraint with TRACK_Z aiming at camera-relative helper
    dt = head_pivot.constraints.new(type='DAMPED_TRACK')
    dt.target = cam_aim_helper
    dt.track_axis = 'TRACK_Z'

    # Generate all required PIL sprites on disk
    p_head_bloated = generate_head_sprite("head_bloated.png", "bloated")
    p_head_xray = generate_head_sprite("head_xray.png", "xray")
    p_head_290g = generate_head_sprite("head_290g_warp.png", "290g_warp")
    p_head_vascular = generate_head_sprite("head_vascular.png", "vascular")

    p_body_bloated = generate_body_sprite("body_bloated.png", "bloated")
    p_body_xray = generate_body_sprite("body_xray.png", "xray")
    p_body_normal = generate_body_sprite("body_normal_suit.png", "normal_suit")
    p_body_vascular = generate_body_sprite("body_vascular_blood.png", "vascular_blood")

    # Create Body Planes under Hero_Root
    body_bloated = create_vertical_cel_plane("Hero_Body_Bloated", 0.96, 1.44, (0.0, 0.0, 0.72),
                                             make_cel_sprite_mat("Mat_Body_Bloated", p_body_bloated), col, hero_root)
    body_xray = create_vertical_cel_plane("Hero_Body_Xray", 0.96, 1.44, (0.0, 0.0, 0.72),
                                          make_cel_sprite_mat("Mat_Body_Xray", p_body_xray, emission_boost=1.4), col, hero_root)
    body_normal = create_vertical_cel_plane("Hero_Body_Normal", 0.96, 1.44, (0.0, 0.0, 0.72),
                                            make_cel_sprite_mat("Mat_Body_Normal", p_body_normal), col, hero_root)
    body_vascular = create_vertical_cel_plane("Hero_Body_Vascular", 0.96, 1.44, (0.0, 0.0, 0.72),
                                              make_cel_sprite_mat("Mat_Body_Vascular", p_body_vascular), col, hero_root)

    # Remove any stray skeleton/bone meshes from previous sessions
    for stray in list(bpy.data.objects):
        if any(w in stray.name.lower() for w in ["skull", "skel", "ribcage", "spine", "pelvis"]):
            bpy.data.objects.remove(stray, do_unlink=True)

    # Create Head Planes parented to Head_BillboardPivot (local XY art with +Z facing out!)
    head_cards = {}
    for key, path, e_boost in [
        ("bloated", p_head_bloated, 0.35),
        ("xray", p_head_xray, 1.45),
        ("290g_warp", p_head_290g, 0.35),
        ("vascular", p_head_vascular, 0.35),
    ]:
        h_obj = create_vertical_cel_plane(f"Hero_Head_{key}", 0.56, 0.56, (0.0, 0.0, 0.0),
                                          make_cel_sprite_mat(f"Mat_Head_{key}", path, emission_boost=e_boost),
                                          col, head_pivot)
        # Reset local rotation to zero so it inherits head_pivot's TRACK_Z billboard orientation directly
        h_obj.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
        head_cards[key] = h_obj

    return {
        "col": col,
        "root": hero_root,
        "head_pivot": head_pivot,
        "bodies": {
            "bloated": body_bloated,
            "xray": body_xray,
            "normal": body_normal,
            "vascular": body_vascular,
        },
        "heads": head_cards,
    }


def set_hero_state_schedule(hero_rig, state_schedule):
    """
    Keyframes CONSTANT visibility for Hero pose states across Part 1:
    state_schedule = [(f_start, f_end, head_key, body_key), ...]
    """
    all_heads = hero_rig["heads"]
    all_bodies = hero_rig["bodies"]
    crit_frames = {1, PART1_LAST_FRAME + 1, FRAME_END}
    for s, e, _, _ in state_schedule:
        crit_frames.update([max(1, s - 1), s, e, min(FRAME_END, e + 1)])

    for f in sorted(crit_frames):
        active_h, active_b = None, None
        for s, e, hk, bk in state_schedule:
            if s <= f <= e:
                active_h, active_b = hk, bk
                break
        for hk, hobj in all_heads.items():
            hide = (hk != active_h)
            hobj.hide_viewport = hide
            hobj.hide_render = hide
            hobj.keyframe_insert(data_path="hide_viewport", frame=f)
            hobj.keyframe_insert(data_path="hide_render", frame=f)
        for bk, bobj in all_bodies.items():
            hide = (bk != active_b)
            bobj.hide_viewport = hide
            bobj.hide_render = hide
            bobj.keyframe_insert(data_path="hide_viewport", frame=f)
            bobj.keyframe_insert(data_path="hide_render", frame=f)

    for hobj in all_heads.values():
        enforce_constant_visibility(hobj)
    for bobj in all_bodies.values():
        enforce_constant_visibility(bobj)


# ------------------------------------------------------------------------------
# 7. CAMERA RIG & SCREEN-SPACE HUD OVERLAYS (§5, §7.1, §7.6 Laws)
# ------------------------------------------------------------------------------
def build_camera_and_hud_rig(scene):
    """
    Creates the main camera, the §7.1 camera-relative aim helper for the Hero's
    DAMPED_TRACK head pivot, and camera-parented screen-space HUD cards (§7.6).
    """
    col = bpy.data.collections.new("CAMERA_AND_HUD")
    scene.collection.children.link(col)

    cam_data = bpy.data.cameras.new(name="MainCamera")
    cam_data.lens = 42.0  # Equivalent to ~44 deg vertical FOV (Contract §3: 38-50 deg)
    cam_data.clip_start = 0.05
    cam_data.clip_end = 150.0
    cam_data.dof.use_dof = False

    cam_obj = bpy.data.objects.new("MainCamera", cam_data)
    col.objects.link(cam_obj)
    scene.camera = cam_obj

    # §7.1 Camera-relative helper in front of camera so DAMPED_TRACK (TRACK_Z) keeps head parallel
    cam_aim_helper = bpy.data.objects.new("Cam_HeadBillboard_Target", None)
    col.objects.link(cam_aim_helper)
    cam_aim_helper.parent = cam_obj
    # In camera local space, +Z points behind the camera (toward the viewer), keeping card +Z parallel
    cam_aim_helper.location = (0.0, 0.0, 12.0)

    # Generate all required §7.6 Screen-Space HUD PNG cards
    hud_specs = {
        "you_tag": generate_hud_banner(
            "hud_you_tag.png", "<- तुम (YOU)", "HOLDING IT IN...",
            bg_col=(250, 205, 25, 245), border_col=(35, 20, 22, 255),
            title_col=(25, 18, 20, 255), sub_col=(65, 35, 15, 255)
        ),
        "cnt_14": generate_hud_banner(
            "hud_cnt_14.png", "14 FARTS / DAY", "DAILY HUMAN AVERAGE"
        ),
        "cnt_38k": generate_hud_banner(
            "hud_cnt_38k.png", "38,269 FARTS", "ACCUMULATED BY AGE 8"
        ),
        "cnt_130k": generate_hud_banner(
            "hud_cnt_130k.png", "1,30,000 FARTS", "BY AGE 25 (LIFETIME LOAD!)"
        ),
        "vol_9000": generate_hud_banner(
            "hud_vol_9000.png", "9,000 L OF GAS", "TOTAL COMPRESSED VOLUME"
        ),
        "nozzle_1s": generate_hud_banner(
            "hud_nozzle_1s.png", "1 SECOND", "NOZZLE BLAST DURATION",
            border_col=(255, 255, 255, 255), sub_col=(140, 255, 185, 255)
        ),
        "vel_20kms": generate_hud_banner(
            "hud_vel_20kms.png", "20 KM / SECOND", "EXHAUST EXIT VELOCITY"
        ),
        "chart_sniper": generate_hud_banner(
            "hud_chart_sniper.png", "SPEED COMPARISON", "",
            bar_compare=True, bar_mode="sniper"
        ),
        "chart_thrust": generate_hud_banner(
            "hud_chart_thrust.png", "THRUST: JET vs YOU (290 G)", "",
            bg_col=(32, 12, 16, 238), border_col=(255, 55, 65, 255),
            bar_compare=True, bar_mode="thrust"
        ),
        "warn_290g": generate_hud_banner(
            "hud_warn_290g.png", "WARNING: 290 G!", "PILOTS BLACK OUT AT 9 G",
            bg_col=(48, 10, 14, 242), border_col=(255, 45, 55, 255),
            title_col=(255, 75, 85, 255), sub_col=(255, 230, 110, 255)
        ),
        "blood_pool": generate_hud_banner(
            "hud_blood_pool.png", "HYDROSTATIC SHOCK", "100% BLOOD POOLED IN LEGS!",
            bg_col=(42, 10, 14, 238), border_col=(235, 35, 45, 255),
            title_col=(255, 255, 255, 255), sub_col=(255, 95, 105, 255)
        ),
    }

    hud_cards = {}
    for key, png_path in hud_specs.items():
        mat = make_cel_sprite_mat(f"Mat_HUD_{key}", png_path, blended=True, emission_boost=0.85)
        # Create card parented directly to camera in top 10-18% safe zone (local Z = -1.65m in front of lens)
        if key == "you_tag":
            w, h, loc = 0.34, 0.13, (0.20, 0.08, -1.65)
        elif key == "nozzle_1s":
            w, h, loc = 0.42, 0.16, (0.0, -0.34, -1.65)
        else:
            w, h, loc = 0.62, 0.23, (0.0, 0.48, -1.65)

        card = create_vertical_cel_plane(f"HUD_Card_{key}", w, h, loc, mat, col, parent=cam_obj)
        # In camera local space, X is right, Y is up, -Z is forward
        card.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
        hud_cards[key] = card

    return {
        "col": col,
        "cam": cam_obj,
        "aim_helper": cam_aim_helper,
        "hud_cards": hud_cards,
    }


def set_hud_schedule(hud_cards: dict, schedule: list):
    """
    schedule = [(f_start, f_end, hud_key), ...]
    Keyframes CONSTANT visibility for all screen-space HUD cards.
    """
    crit_frames = {1, PART1_LAST_FRAME + 1, FRAME_END}
    for s, e, _ in schedule:
        crit_frames.update([max(1, s - 1), s, e, min(FRAME_END, e + 1)])

    for f in sorted(crit_frames):
        active_keys = {k for (s, e, k) in schedule if s <= f <= e}
        for k, obj in hud_cards.items():
            hide = (k not in active_keys)
            obj.hide_viewport = hide
            obj.hide_render = hide
            obj.keyframe_insert(data_path="hide_viewport", frame=f)
            obj.keyframe_insert(data_path="hide_render", frame=f)

    for obj in hud_cards.values():
        enforce_constant_visibility(obj)


# ------------------------------------------------------------------------------
# 8. ANIMATE SCENES 1 TO 4 (FRAMES 1 – 1425 | 0.0s – 47.5s)
# ------------------------------------------------------------------------------
def animate_part1_scenes(scene, lr_set, xr_set, vh_set, sky_set, hero_rig, cam_rig):
    cam = cam_rig["cam"]
    hud_cards = cam_rig["hud_cards"]
    hero_root = hero_rig["root"]

    # --------------------------------------------------------------------------
    # A. ISOLATED SET VISIBILITY SCHEDULE (CONSTANT INTERPOLATION)
    # --------------------------------------------------------------------------
    set_root_visibility(lr_set["root"], lr_set["col"], [
        (1, 144),      # Cut 1A: Living Room Hook
        (631, 710),    # Cut 2C (Part 1): Living Room Sofa Grip + Green Leak
        (1006, 1086),  # Cut 3C: Living Room Sofa Shred Explosion
    ])
    set_root_visibility(xr_set["root"], xr_set["col"], [
        (145, 465),    # Cut 1B, 1C, Cut 2A: X-Ray Grid Counter & 9,000L Sphere
        (711, 804),    # Cut 2C (Part 2): X-Ray Pelvic Macro 1-Second Nozzle
        (805, 1005),   # Cut 3A, 3B: 20 KM/S Plasma Beam & Sniper Comparison
        (1087, 1206),  # Cut 4A: 290 G-Force Rocket Thrust Column
    ])
    set_root_visibility(vh_set["root"], vh_set["col"], [
        (466, 630),    # Cut 2B: School Bus & Indian Water Tanker Diorama
    ])
    set_root_visibility(sky_set["root"], sky_set["col"], [
        (1207, 1425),  # Cut 4B, 4C: Sky Ascent 290G Face Warp & Blood Pooling
    ])

    # Hide Hero during Cut 2B (Vehicles Diorama f466..630)
    set_hero_state_schedule(hero_rig, [
        (1, 144, "bloated", "bloated"),
        (145, 465, "xray", "xray"),
        (466, 630, None, None),
        (631, 710, "bloated", "bloated"),
        (711, 1005, "xray", "xray"),
        (1006, 1086, "bloated", "bloated"),
        (1087, 1206, "290g_warp", "bloated"),
        (1207, 1296, "290g_warp", "bloated"),
        (1297, 1425, "vascular", "vascular"),
    ])

    # --------------------------------------------------------------------------
    # B. SCREEN-SPACE HUD SCHEDULE (§7.6)
    # --------------------------------------------------------------------------
    set_hud_schedule(hud_cards, [
        (12, 144, "you_tag"),
        (148, 204, "cnt_14"),
        (205, 264, "cnt_38k"),
        (265, 384, "cnt_130k"),
        (385, 465, "vol_9000"),
        (715, 804, "nozzle_1s"),
        (805, 900, "vel_20kms"),
        (901, 1005, "chart_sniper"),
        (1087, 1206, "chart_thrust"),
        (1207, 1296, "warn_290g"),
        (1297, 1425, "blood_pool"),
    ])

    # --------------------------------------------------------------------------
    # C. WORLD MOOD BEAT TABLE (§7.5)
    # --------------------------------------------------------------------------
    bg_node = scene.world.node_tree.nodes.get("Background")
    world_beats = [
        (1, (0.14, 0.08, 0.06, 1.0)),     # Warm sunset interior
        (145, (0.015, 0.08, 0.10, 1.0)),  # Dark cyan X-ray grid
        (466, (0.12, 0.18, 0.26, 1.0)),   # Crisp diorama daylight
        (631, (0.14, 0.08, 0.06, 1.0)),   # Living room tense warm
        (711, (0.01, 0.09, 0.08, 1.0)),   # X-ray macro green-cyan
        (1006, (0.16, 0.12, 0.08, 1.0)),  # Living room blast flash
        (1087, (0.04, 0.08, 0.10, 1.0)),  # Thrust column dark cyan
        (1207, (0.15, 0.45, 0.85, 1.0)),  # High altitude sky blue
    ]
    if bg_node:
        for f_beat, col_val in world_beats:
            bg_node.inputs[0].default_value = col_val
            bg_node.inputs[0].keyframe_insert(data_path="default_value", frame=f_beat)
        for fc in scene.world.node_tree.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'

    # --------------------------------------------------------------------------
    # SCENE 1 (Frames 1 – 384 | 0.0s – 12.8s): Hook & X-Ray Counter
    # --------------------------------------------------------------------------
    # Cut 1A (f1..144): Medium 3/4 dolly-in on hero_bloated sitting stiffly on sofa
    hero_root.location = (0.0, 0.35, 0.0)
    hero_root.scale = (1.0, 1.0, 1.0)
    hero_root.keyframe_insert(data_path="location", frame=1)
    hero_root.keyframe_insert(data_path="scale", frame=1)

    # Finite strained torso bloat anticipation pulse at f35..48, then exact hold
    bake_event_transform(
        hero_root, start=35, anticipate=38, extreme=43, settled=48, hold_end=144,
        scale_a=(1.0, 1.0, 1.0), scale_b=(1.06, 1.0, 1.04)
    )

    # Camera Cut 1A: Eased dolly-in from medium-wide to medium 3/4
    bake_event_transform(
        cam, start=1, anticipate=15, extreme=110, settled=128, hold_end=144,
        loc_a=(0.42, -2.55, 1.18), loc_b=(0.24, -1.92, 1.14),
        rot_a=(radians(86.0), 0.0, radians(9.5)), rot_b=(radians(86.5), 0.0, radians(6.8))
    )

    # Cut 1B (f145..264): Snap to SET_XRAY_GRID, small tapered green gas ribbons puff out
    hero_root.scale = (1.0, 1.0, 1.0)
    hero_root.keyframe_insert(data_path="scale", frame=145)
    set_fcurve_constant_after(hero_root, "scale", 145)

    bake_event_transform(
        cam, start=145, anticipate=150, extreme=162, settled=170, hold_end=264,
        loc_a=(0.0, -2.35, 1.15), loc_b=(0.0, -2.10, 1.12),
        rot_a=(radians(86.0), 0.0, 0.0), rot_b=(radians(86.5), 0.0, 0.0)
    )

    # Animate tapered gas ribbons puffing upward in finite beats during Cut 1B & 1C
    for idx, rib in enumerate(xr_set["ribbons"]):
        f0 = 152 + idx * 18
        bake_event_transform(
            rib, start=f0, anticipate=f0 + 3, extreme=f0 + 12, settled=f0 + 18, hold_end=384,
            loc_a=((-0.26 + idx * 0.26), 0.52, 0.58),
            loc_b=((-0.30 + idx * 0.30), 0.52, 1.05),
            scale_a=(0.4, 0.4, 0.4), scale_b=(1.0, 1.0, 1.15)
        )

    # Cut 1C (f265..384): 35-degree 3D camera orbit around X-ray skeleton + rising gas orbs
    bake_event_transform(
        cam, start=265, anticipate=272, extreme=355, settled=370, hold_end=384,
        loc_a=(0.0, -2.10, 1.12), loc_b=(1.22, -1.72, 1.20),
        rot_a=(radians(86.5), 0.0, 0.0), rot_b=(radians(84.5), 0.0, radians(35.0))
    )

    for idx, (orb, base_loc) in enumerate(xr_set["orbs"]):
        # Hide orbs outside Cut 1C
        set_root_visibility(orb, xr_set["col"], [(265, 384)])
        f_orb = 268 + idx * 10
        bake_event_transform(
            orb, start=f_orb, anticipate=f_orb + 4, extreme=f_orb + 38, settled=f_orb + 48, hold_end=384,
            loc_a=base_loc, loc_b=(base_loc[0] * 1.35, base_loc[1], base_loc[2] + 0.78),
            scale_a=(0.2, 0.2, 0.2), scale_b=(1.15, 1.15, 1.15)
        )

    # --------------------------------------------------------------------------
    # SCENE 2 (Frames 385 – 804 | 12.8s – 26.8s): 9,000L, Vehicles & 1s Nozzle
    # --------------------------------------------------------------------------
    # Cut 2A (f385..465): Wide pull-back in SET_XRAY_GRID as massive 9,000L gas sphere expands
    gs9000 = xr_set["gas_sphere_9000"]
    set_root_visibility(gs9000, xr_set["col"], [(385, 465)])
    bake_event_transform(
        gs9000, start=386, anticipate=392, extreme=428, settled=440, hold_end=465,
        scale_a=(0.08, 0.08, 0.08), scale_b=(1.65, 1.65, 1.65)
    )
    bake_event_transform(
        cam, start=385, anticipate=390, extreme=425, settled=438, hold_end=465,
        loc_a=(0.65, -2.15, 1.15), loc_b=(0.0, -4.45, 1.55),
        rot_a=(radians(85.0), 0.0, radians(15.0)), rot_b=(radians(82.0), 0.0, 0.0)
    )

    # Cut 2B (f466..630): SET_VEHICLES — Pull camera back so 100% of Bus & Tanker fit in frame!
    bake_event_transform(
        cam, start=466, anticipate=472, extreme=510, settled=525, hold_end=630,
        loc_a=(0.0, -5.85, 1.15), loc_b=(0.0, -5.35, 1.08),
        rot_a=(radians(85.5), 0.0, 0.0), rot_b=(radians(86.0), 0.0, 0.0)
    )
    bake_event_transform(
        vh_set["bus_gas"], start=472, anticipate=478, extreme=574, settled=586, hold_end=630,
        loc_a=(0.0, 0.0, 0.25), loc_b=(0.0, 0.0, 0.64),
        scale_a=(1.0, 1.0, 0.05), scale_b=(1.02, 1.06, 1.0)
    )
    bake_event_transform(
        vh_set["tanker_gas"], start=476, anticipate=482, extreme=576, settled=588, hold_end=630,
        loc_a=(0.14, 0.0, 0.38), loc_b=(0.14, 0.0, 0.68),
        scale_a=(1.0, 1.0, 0.05), scale_b=(1.02, 1.05, 1.0)
    )
    for win in vh_set["bus_windows"]:
        bake_event_transform(
            win, start=574, anticipate=576, extreme=580, settled=586, hold_end=630,
            scale_a=(1.0, 1.0, 1.0), scale_b=(1.14, 1.38, 1.18)
        )

    # Cut 2C (f631..804): Living Room sofa grip + green leak, then pelvic macro 1-Second nozzle cone
    leak_lt = lr_set["leak_light"]
    leak_lt.data.energy = 0.0
    leak_lt.data.keyframe_insert(data_path="energy", frame=631)
    leak_lt.data.energy = 140.0
    leak_lt.data.keyframe_insert(data_path="energy", frame=705)
    leak_lt.data.energy = 0.0
    leak_lt.data.keyframe_insert(data_path="energy", frame=711)

    bake_event_transform(
        cam, start=631, anticipate=636, extreme=685, settled=700, hold_end=710,
        loc_a=(0.0, -2.15, 1.05), loc_b=(0.0, -1.78, 0.96),
        rot_a=(radians(86.0), 0.0, 0.0), rot_b=(radians(87.0), 0.0, 0.0)
    )

    set_root_visibility(xr_set["nozzle_ring"], None, [(711, 804)])
    set_root_visibility(xr_set["laser_cone"], None, [(711, 804)])

    bake_event_transform(
        cam, start=711, anticipate=714, extreme=721, settled=727, hold_end=804,
        loc_a=(0.0, -2.23, 1.14), loc_b=(0.0, -1.70, 0.86),
        rot_a=(radians(87.0), 0.0, 0.0), rot_b=(radians(88.0), 0.0, 0.0)
    )
    bake_event_transform(
        xr_set["laser_cone"], start=716, anticipate=719, extreme=726, settled=732, hold_end=804,
        scale_a=(0.15, 0.15, 0.05), scale_b=(1.0, 1.0, 1.0)
    )

    # --------------------------------------------------------------------------
    # SCENE 3 (Frames 805 – 1086 | 26.8s – 36.2s): 20 KM/S Sniper & Sofa Shred
    # --------------------------------------------------------------------------
    # Cut 3A & 3B (f805..1005): Narrow lime-green beam strictly BELOW seated hips (Z = 0.26m)
    set_root_visibility(xr_set["plasma_beam"], None, [(805, 1005), (1087, 1206)])
    set_root_visibility(xr_set["shock_ring_1"], None, [(805, 1005)])
    set_root_visibility(xr_set["shock_ring_2"], None, [(805, 1005)])

    bake_event_transform(
        xr_set["plasma_beam"], start=805, anticipate=808, extreme=814, settled=820, hold_end=1005,
        loc_a=(0.0, 0.38, 0.26), loc_b=(0.0, 0.38, 0.26),
        scale_a=(0.25, 0.25, 0.1), scale_b=(1.0, 1.0, 1.0)
    )
    bake_event_transform(
        xr_set["shock_ring_1"], start=808, anticipate=812, extreme=855, settled=870, hold_end=1005,
        scale_a=(0.15, 0.15, 1.0), scale_b=(1.5, 1.5, 1.0)
    )
    bake_event_transform(
        xr_set["shock_ring_2"], start=816, anticipate=820, extreme=875, settled=890, hold_end=1005,
        scale_a=(0.15, 0.15, 1.0), scale_b=(2.1, 2.1, 1.0)
    )
    bake_event_transform(
        cam, start=805, anticipate=812, extreme=875, settled=890, hold_end=900,
        loc_a=(-0.65, -2.35, 0.78), loc_b=(0.72, -2.25, 0.85),
        rot_a=(radians(91.0), 0.0, radians(-15.0)), rot_b=(radians(90.0), 0.0, radians(18.0))
    )

    # Cut 3B (f901..1005): Side-profile X-ray view with Sniper vs Fart bar chart
    bake_event_transform(
        cam, start=901, anticipate=905, extreme=914, settled=920, hold_end=1005,
        loc_a=(0.72, -2.25, 0.85), loc_b=(1.15, -2.15, 1.02),
        rot_a=(radians(90.0), 0.0, radians(18.0)), rot_b=(radians(87.5), 0.0, radians(28.0))
    )

    # Cut 3C (f1006..1086): Intact sofa visible ONLY in Living Room cuts 1A & 2C, hidden during 3C shred!
    set_root_visibility(lr_set["sofa_intact"], None, [(1, 144), (631, 710)])
    for deb_obj, p0, p1, rot1 in lr_set["debris"]:
        set_root_visibility(deb_obj, None, [(1006, 1086)])
        bake_event_transform(
            deb_obj, start=1006, anticipate=1008, extreme=1068, settled=1080, hold_end=1086,
            loc_a=p0, loc_b=p1, rot_a=(0.0, 0.0, 0.0), rot_b=rot1
        )

    bake_event_transform(
        hero_root, start=1006, anticipate=1008, extreme=1025, settled=1035, hold_end=1086,
        loc_a=(0.0, 0.35, 0.0), loc_b=(0.0, 0.35, 0.28)
    )

    shake_offsets = [
        (1006, (0.0, -2.35, 1.05), (radians(86.0), 0.0, 0.0)),
        (1007, (0.09, -2.32, 1.12), (radians(87.5), radians(1.2), radians(1.5))),
        (1008, (-0.08, -2.38, 0.99), (radians(84.8), radians(-1.1), radians(-1.4))),
        (1009, (0.06, -2.34, 1.09), (radians(86.9), radians(0.8), radians(0.9))),
        (1010, (-0.05, -2.36, 1.02), (radians(85.3), radians(-0.6), radians(-0.7))),
        (1011, (0.03, -2.35, 1.07), (radians(86.4), radians(0.3), radians(0.4))),
        (1012, (-0.01, -2.35, 1.04), (radians(85.8), 0.0, 0.0)),
        (1013, (0.0, -2.35, 1.05), (radians(86.0), 0.0, 0.0)),
        (1086, (0.0, -2.35, 1.05), (radians(86.0), 0.0, 0.0)),
    ]
    for f_shk, s_loc, s_rot in shake_offsets:
        cam.location = Vector(s_loc)
        cam.rotation_euler = Euler(s_rot, 'XYZ')
        cam.keyframe_insert(data_path="location", frame=f_shk)
        cam.keyframe_insert(data_path="rotation_euler", frame=f_shk)
    set_fcurve_constant_after(cam, "location", 1013)
    set_fcurve_constant_after(cam, "rotation_euler", 1013)

    # --------------------------------------------------------------------------
    # SCENE 4 (Frames 1087 – 1425 | 36.2s – 47.5s): 290 G Warp & Blood Pooling
    # --------------------------------------------------------------------------
    # Cut 4A (f1087..1206): Wireframe sofa visible ONLY in X-Ray cuts 1B..2A & 2C..3B, hidden during 4A launch!
    set_root_visibility(xr_set["wire_sofa"], None, [(145, 465), (711, 1005)])
    bake_event_transform(
        hero_root, start=1087, anticipate=1093, extreme=1175, settled=1192, hold_end=1206,
        loc_a=(0.0, 0.35, -0.20), loc_b=(0.0, 0.35, 1.50)
    )
    bake_event_transform(
        xr_set["plasma_beam"], start=1087, anticipate=1093, extreme=1175, settled=1192, hold_end=1206,
        loc_a=(0.0, 0.38, -0.80), loc_b=(0.0, 0.38, 0.70),
        scale_a=(0.95, 0.95, 2.2), scale_b=(0.95, 0.95, 2.6)
    )
    bake_event_transform(
        cam, start=1087, anticipate=1094, extreme=1178, settled=1195, hold_end=1206,
        loc_a=(0.0, -2.55, 0.85), loc_b=(0.0, -2.45, 1.95),
        rot_a=(radians(89.0), 0.0, 0.0), rot_b=(radians(92.0), 0.0, 0.0)
    )

    # Cut 4B (f1207..1296): SET_SKY_ASCENT Tight close-up on Hero (hero_290g_warp)
    # with clouds rushing rapidly downward past the camera
    hero_root.location = (0.0, 0.35, 0.65)
    hero_root.keyframe_insert(data_path="location", frame=1207)
    set_fcurve_constant_after(hero_root, "location", 1207)

    # Clouds rush downward during active sky ascent span (f1207..1425)
    clouds_m = sky_set["clouds_master"]
    clouds_m.location = (0.0, 0.0, 1.5)
    clouds_m.keyframe_insert(data_path="location", frame=1207)
    clouds_m.location = (0.0, 0.0, -9.5)
    clouds_m.keyframe_insert(data_path="location", frame=1425)

    # Tight close-up camera on warped 290G face (f1207..1296)
    bake_event_transform(
        cam, start=1207, anticipate=1211, extreme=1222, settled=1228, hold_end=1296,
        loc_a=(0.0, -1.45, 1.78), loc_b=(0.0, -1.12, 1.82),
        rot_a=(radians(89.0), 0.0, 0.0), rot_b=(radians(90.0), 0.0, 0.0)
    )

    # Cut 4C (f1297..1425): Medium full-body view in SET_SKY_ASCENT swapping to hero_vascular_blood
    # showing bright red blood pooled into swollen water-balloon lower pant legs and shoes!
    bake_event_transform(
        cam, start=1297, anticipate=1302, extreme=1316, settled=1324, hold_end=1425,
        loc_a=(0.0, -1.12, 1.82), loc_b=(0.0, -2.45, 1.32),
        rot_a=(radians(90.0), 0.0, 0.0), rot_b=(radians(88.5), 0.0, 0.0)
    )
    # Finite balloon-leg swell overshoot on Hero body at f1305..1322
    bake_event_transform(
        hero_rig["bodies"]["vascular"], start=1302, anticipate=1306, extreme=1315, settled=1322, hold_end=1425,
        scale_a=(0.94, 1.0, 0.96), scale_b=(1.08, 1.0, 1.04)
    )


# ------------------------------------------------------------------------------
# 9. MAIN EXECUTION & .BLEND CHECKPOINT SAVE
# ------------------------------------------------------------------------------
def main(output_blend_path=OUTPUT_BLEND_PATH):
    print("[Part 1 Builder] Initializing Blender 4.2 scene & EEVEE Next settings...")
    scene = init_blender_scene()

    print("[Part 1 Builder] Building Camera & Screen-Space HUD Rig...")
    cam_rig = build_camera_and_hud_rig(scene)

    print("[Part 1 Builder] Building Reusable 3D Sets (Living Room, X-Ray Grid, Vehicles, Sky Ascent)...")
    lr_set = build_set_living_room(scene)
    xr_set = build_set_xray_grid(scene)
    vh_set = build_set_vehicles(scene)
    sky_set = build_set_sky_ascent(scene)

    print("[Part 1 Builder] Generating PIL 2D Cel Sprites & Hero DAMPED_TRACK Rig...")
    hero_rig = build_hero_cel_rig(scene, cam_rig["aim_helper"])

    print("[Part 1 Builder] Keyframing Scenes 1 to 4 (Frames 1..1425)...")
    animate_part1_scenes(scene, lr_set, xr_set, vh_set, sky_set, hero_rig, cam_rig)

    # Ensure external textures are packed into the .blend file for portability
    for img in bpy.data.images:
        if img.filepath and os.path.exists(bpy.path.abspath(img.filepath)):
            try:
                img.reload()
            except Exception:
                pass
    try:
        bpy.ops.file.pack_all()
    except Exception as exc:
        print(f"[Part 1 Builder] Warning during pack_all: {exc}")

    print(f"[Part 1 Builder] Saving Blender 4.2 file to: {OUTPUT_BLEND_PATH}")
    bpy.ops.wm.save_as_mainfile(filepath=output_blend_path)
    print("[Part 1 Builder] SUCCESS — Part 1 (Frames 1–1425) build complete!")


if __name__ == "__main__":
    main()
