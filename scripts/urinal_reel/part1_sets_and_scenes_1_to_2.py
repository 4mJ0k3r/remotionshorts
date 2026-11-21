#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
# part1_sets_and_scenes_1_to_2.py
# RicksClips 2.5D Blender 4.2 Studio Architect (Part 1 of 2)
# Target: Blender 4.2 LTS (BLENDER_EEVEE_NEXT) | 1080x1920 @ 30fps | AgX
# Builds:
#   1. Complete Procedural 2D RicksClips Sprite & Articulated Pose Library (PIL)
#      for Part 1 & Part 2 saved to D:/remotionshorts/renders/urinal_dilemma/sprites/
#   2. Complete 3D Open-Air Tiled Men's Restroom Set, 4 Beveled Porcelain Urinals,
#      Wall Typography, Exterior Grass & 3D Branching Winter Tree, 3-Stop Vertical
#      Sky World Gradient + Clouds, Directional Sun + Contact Shadows, Optical DOF
#      + Compositor FOG_GLOW & Vignette, 3 Floating '?' Pop-up Cards, and Top-9%
#      Screen-Space HUD Badge Plane.
#   3. Animates Scenes 1 & 2 (Frames 1 to 429, Cuts 1A, 1B, 1C, 2A, 2B, 2C-1, 2C-2).
#   4. Saves D:/remotionshorts/urinal_dilemma_part1.blend
# ==============================================================================

import os
import sys
import site
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)
import math
import bpy
import mathutils
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

# ==============================================================================
# 0. PATHS & DIRECTORIES
# ==============================================================================
BASE_DIR = "D:/remotionshorts"
RENDER_DIR = os.path.join(BASE_DIR, "renders/urinal_dilemma")
SPRITE_DIR = os.path.join(RENDER_DIR, "sprites")
HUD_DIR = os.path.join(RENDER_DIR, "hud")
BLEND_PART1_PATH = os.path.join(BASE_DIR, "urinal_dilemma_part1.blend")

for _d in (BASE_DIR, RENDER_DIR, SPRITE_DIR, HUD_DIR):
    os.makedirs(_d, exist_ok=True)


# ==============================================================================
# 1. FONT LOADER & PIL BEZIER / DRAWING HELPERS
# ==============================================================================
def load_font(size: int, bold: bool = True):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/seguisb.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def quad_bezier(p0, p1, p2, steps=40):
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        x = u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0]
        y = u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]
        pts.append((x, y))
    return pts


def cubic_bezier(p0, p1, p2, p3, steps=48):
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        x = (
            (u ** 3) * p0[0]
            + 3 * (u ** 2) * t * p1[0]
            + 3 * u * (t ** 2) * p2[0]
            + (t ** 3) * p3[0]
        )
        y = (
            (u ** 3) * p0[1]
            + 3 * (u ** 2) * t * p1[1]
            + 3 * u * (t ** 2) * p2[1]
            + (t ** 3) * p3[1]
        )
        pts.append((x, y))
    return pts


def draw_thick_round_curve(draw: ImageDraw.ImageDraw, pts, width: int, color=(22, 18, 25, 255)):
    if len(pts) < 2:
        return
    draw.line(pts, fill=color, width=width, joint="curve")
    r = width / 2.0
    for px, py in (pts[0], pts[-1]):
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)


def organic_head_polygon(cx, cy, rx, ry, num_pts=160):
    pts = []
    for i in range(num_pts):
        a = (2.0 * math.pi * i) / num_pts
        r_mod = (
            1.0
            + 0.020 * math.sin(2.0 * a + 0.6)
            - 0.014 * math.cos(3.0 * a - 0.8)
            + 0.007 * math.sin(5.0 * a + 1.9)
        )
        x = cx + rx * r_mod * math.cos(a)
        y = cy + ry * r_mod * math.sin(a)
        pts.append((x, y))
    return pts


def draw_variable_outline(draw: ImageDraw.ImageDraw, poly_pts, base_w=17, color=(22, 18, 25, 255)):
    n = len(poly_pts)
    for i in range(n):
        p0 = poly_pts[i]
        p1 = poly_pts[(i + 1) % n]
        a = (2.0 * math.pi * i) / n
        w = int(round(base_w + 2.0 * math.sin(2.0 * a + 1.1)))
        draw.line([p0, p1], fill=color, width=w)
        r = w * 0.48
        draw.ellipse([p0[0] - r, p0[1] - r, p0[0] + r, p0[1] + r], fill=color)


# ==============================================================================
# 2. RICKSCLIPS 2D STICKMAN SPRITE GENERATOR (PART 1 & PART 2 COMPLETE LIBRARY)
# ==============================================================================
W_CANVAS, H_CANVAS = 1024, 1536
INK = (22, 18, 25, 255)
TRANSPARENT_INK = (22, 18, 25, 0)  # Zero white fringe
CREAM = (253, 250, 242, 255)
SHADOW_COOL = (184, 200, 220, 255)

# Character Colors
JERSEY_GREEN = (0, 135, 81, 255)
JERSEY_DARK = (0, 102, 60, 255)
WHITE_INK = (250, 252, 255, 255)
JEANS_NAVY = (28, 43, 68, 255)

SOLDIER_KHAKI = (156, 132, 104, 255)
SOLDIER_PANTS = (112, 95, 74, 255)
SUSPENDER_BEIGE = (200, 185, 158, 255)
POUCH_BROWN = (88, 70, 50, 255)
HELMET_OLIVE = (92, 99, 70, 255)
HELMET_DARK = (58, 64, 43, 255)
STRAP_BROWN = (76, 54, 38, 255)
SWEAT_CYAN = (115, 208, 255, 245)


def render_head_with_helmet_and_face(
    canvas: Image.Image,
    char_type: str,
    view: str,
    turn_x: float = 0.0,
    expr: str = "neutral",
    head_cx: int = 512,
    head_cy: int = 390,
    head_r: int = 195,
):
    # Draws the RicksClips organic cream head with 15% cool grey-blue crescent shadow,
    # variable-width marker outline, optional ear contour on 3/4 turns, optional soldier
    # olive-drab netted helmet, and solid #161219 oval eyes (ZERO white sclera).
    head_fill_img = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
    head_mask = Image.new("L", (W_CANVAS, H_CANVAS), 0)
    d_fill = ImageDraw.Draw(head_fill_img)
    d_mask = ImageDraw.Draw(head_mask)

    poly = organic_head_polygon(head_cx, head_cy, head_r, head_r, num_pts=160)
    d_fill.polygon(poly, fill=CREAM)
    d_mask.polygon(poly, fill=255)

    # 18% bottom-left cool grey-blue inner crescent shadow while keeping 100% solid alpha=255 cream fill
    crescent_mask = Image.new("L", (W_CANVAS, H_CANVAS), 0)
    d_cm = ImageDraw.Draw(crescent_mask)
    d_cm.polygon(poly, fill=255)
    cut_poly = organic_head_polygon(head_cx + 38, head_cy - 34, int(head_r * 0.98), int(head_r * 0.96))
    d_cm.polygon(cut_poly, fill=0)
    crescent_alpha = crescent_mask.point(lambda p: int(p * 0.18))
    head_fill_img.paste((165, 185, 210, 255), (0, 0), crescent_alpha)

    # Composite 100% opaque head onto canvas
    canvas.alpha_composite(head_fill_img)
    draw = ImageDraw.Draw(canvas)

    # Subtle ear bump on 3/4 turns for char_you
    if char_type == "you" and view != "back" and abs(turn_x) > 0.08:
        ear_side = -1 if turn_x > 0 else 1
        ear_x = head_cx + ear_side * int(head_r * 0.96)
        ear_y = head_cy + 18
        ear_box = [ear_x - 26, ear_y - 38, ear_x + 26, ear_y + 38]
        draw.ellipse(ear_box, fill=CREAM, outline=INK, width=14)
        draw.arc([ear_x - 12, ear_y - 18, ear_x + 12, ear_y + 18], 30, 260, fill=INK, width=6)

    # Bold variable-width #161219 marker outline around head (15px-19px)
    draw_variable_outline(draw, poly, base_w=17, color=INK)

    # Facial features (if not back view)
    if view != "back":
        fx = head_cx + int(turn_x * head_r)
        fy = head_cy + 8
        eye_sep = 54 if abs(turn_x) < 0.15 else 48
        lx = fx - eye_sep
        rx = fx + eye_sep
        eye_y = fy - 18

        # Chin strap for soldier (under helmet, around jaw)
        if char_type == "stranger":
            strap_pts = quad_bezier(
                (head_cx - int(head_r * 0.78), head_cy - 10),
                (fx, head_cy + int(head_r * 0.92)),
                (head_cx + int(head_r * 0.78), head_cy - 10),
                steps=32,
            )
            draw_thick_round_curve(draw, strap_pts, width=10, color=STRAP_BROWN)
            draw_thick_round_curve(draw, strap_pts, width=3, color=INK)

        # Solid #161219 Vertical Oval Eyes (NO white sclera rings)
        eye_layer = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
        d_eye = ImageDraw.Draw(eye_layer)

        ew, eh = 19, 32
        if expr in ("terror_scream", "shock"):
            ew, eh = 24, 42
        elif expr in ("suspicious", "creepy_smirk", "awkward_side", "awkward_talk"):
            ew, eh = 19, 30

        d_eye.ellipse([lx - ew, eye_y - eh, lx + ew, eye_y + eh], fill=INK)
        d_eye.ellipse([rx - ew, eye_y - eh, rx + ew, eye_y + eh], fill=INK)

        # Horizontal Eyelid Masking (top <= y <= bottom)
        lid_mask = Image.new("L", (W_CANVAS, H_CANVAS), 255)
        d_lid = ImageDraw.Draw(lid_mask)
        if expr in ("blink", "awkward_blink", "whistle_blink", "nervous_blink"):
            d_lid.rectangle([0, 0, W_CANVAS, H_CANVAS], fill=0)
            draw.line([(lx - 24, eye_y), (lx + 24, eye_y)], fill=INK, width=12)
            draw.line([(rx - 24, eye_y), (rx + 24, eye_y)], fill=INK, width=12)
        elif expr in ("suspicious", "awkward_side", "awkward_talk"):
            d_lid.rectangle([0, 0, W_CANVAS, eye_y - 8], fill=0)
            draw.line([(lx - 26, eye_y - 8), (lx + 26, eye_y - 8)], fill=INK, width=10)
            draw.line([(rx - 26, eye_y - 8), (rx + 26, eye_y - 8)], fill=INK, width=10)
        elif expr == "creepy_smirk":
            d_lid.rectangle([0, 0, W_CANVAS, eye_y - 10], fill=0)
            d_lid.rectangle([0, eye_y + 18, W_CANVAS, H_CANVAS], fill=0)
            draw.line([(lx - 26, eye_y - 10), (lx + 26, eye_y - 6)], fill=INK, width=10)
            draw.line([(rx - 26, eye_y - 6), (rx + 26, eye_y - 10)], fill=INK, width=10)
        elif expr in ("paranoid_sweat", "nervous_1", "nervous_talk"):
            d_lid.rectangle([0, eye_y + 26, W_CANVAS, H_CANVAS], fill=0)
            draw.arc([lx - 24, eye_y + 16, lx + 24, eye_y + 34], 190, 350, fill=INK, width=7)
            draw.arc([rx - 24, eye_y + 16, rx + 24, eye_y + 34], 190, 350, fill=INK, width=7)

        eye_clipped = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
        eye_clipped.paste(eye_layer, (0, 0), lid_mask)
        canvas.alpha_composite(eye_clipped)

        # Expressive Floating Black Eyebrows
        brow_y = eye_y - eh - 20
        if expr in ("whistle_walk", "whistle_talk", "whistle_blink"):
            draw_thick_round_curve(draw, [(lx - 26, brow_y + 4), (lx, brow_y - 8), (lx + 24, brow_y + 2)], 13, INK)
            draw_thick_round_curve(draw, [(rx - 24, brow_y + 2), (rx, brow_y - 10), (rx + 26, brow_y + 4)], 13, INK)
        elif expr in ("awkward_side", "awkward_talk", "awkward_blink"):
            draw_thick_round_curve(draw, [(lx - 26, brow_y - 6), (lx + 24, brow_y + 8)], 13, INK)
            draw_thick_round_curve(draw, [(rx - 24, brow_y + 8), (rx + 26, brow_y - 8)], 13, INK)
        elif expr in ("paranoid_sweat", "nervous_1", "nervous_talk", "nervous_blink"):
            draw_thick_round_curve(draw, [(lx - 28, brow_y + 8), (lx + 22, brow_y - 12)], 14, INK)
            draw_thick_round_curve(draw, [(rx - 22, brow_y - 12), (rx + 28, brow_y + 8)], 14, INK)
        elif expr == "creepy_smirk":
            draw_thick_round_curve(draw, [(lx - 28, brow_y - 12), (lx, brow_y - 24), (lx + 24, brow_y - 6)], 14, INK)
            draw_thick_round_curve(draw, [(rx - 24, brow_y + 8), (rx + 26, brow_y - 4)], 14, INK)
        elif expr == "terror_scream":
            draw_thick_round_curve(draw, [(lx - 30, brow_y - 12), (lx + 22, brow_y - 28)], 15, INK)
            draw_thick_round_curve(draw, [(rx - 22, brow_y - 28), (rx + 30, brow_y - 12)], 15, INK)
        else:
            draw_thick_round_curve(draw, [(lx - 26, brow_y), (lx + 24, brow_y - 4)], 13, INK)
            draw_thick_round_curve(draw, [(rx - 24, brow_y - 4), (rx + 26, brow_y)], 13, INK)

        # Mouth Expressions
        mouth_y = fy + 62
        if expr in ("whistle_walk", "whistle_blink"):
            draw.ellipse([fx + 8, mouth_y - 12, fx + 30, mouth_y + 12], fill=INK)
            draw_thick_round_curve(draw, [(fx - 18, mouth_y - 4), (fx + 8, mouth_y + 2)], 10, INK)
        elif expr == "whistle_talk":
            draw.ellipse([fx - 22, mouth_y - 16, fx + 26, mouth_y + 18], fill=(45, 18, 25, 255), outline=INK, width=11)
        elif expr == "awkward_side":
            pts = quad_bezier((fx - 38, mouth_y + 6), (fx, mouth_y - 8), (fx + 36, mouth_y + 10), 24)
            draw_thick_round_curve(draw, pts, 12, INK)
        elif expr in ("awkward_talk", "awkward_blink"):
            pts = cubic_bezier((fx - 42, mouth_y + 8), (fx - 12, mouth_y - 14), (fx + 14, mouth_y + 18), (fx + 42, mouth_y - 4), 32)
            draw_thick_round_curve(draw, pts, 13, INK)
        elif expr in ("paranoid_sweat", "nervous_1", "nervous_talk", "nervous_blink"):
            if expr == "nervous_talk":
                draw.ellipse([fx - 32, mouth_y - 12, fx + 32, mouth_y + 24], fill=(45, 18, 25, 255), outline=INK, width=12)
                draw.chord([fx - 26, mouth_y - 10, fx + 26, mouth_y + 8], 180, 360, fill=WHITE_INK, outline=INK, width=5)
            else:
                pts = quad_bezier((fx - 44, mouth_y + 16), (fx, mouth_y - 14), (fx + 44, mouth_y + 18), 28)
                draw_thick_round_curve(draw, pts, 13, INK)
            # 2D Teardrop Sweat Droplet on temple socket (slides lower on nervous_talk)
            sw_x = head_cx + int(head_r * 0.56)
            sw_y = (head_cy - 18) if expr == "nervous_talk" else (head_cy - 38)
            drop_pts = [
                (sw_x, sw_y - 34),
                (sw_x + 20, sw_y + 6),
                (sw_x + 14, sw_y + 24),
                (sw_x, sw_y + 30),
                (sw_x - 14, sw_y + 24),
                (sw_x - 20, sw_y + 6),
            ]
            draw.polygon(drop_pts, fill=SWEAT_CYAN)
            draw_thick_round_curve(draw, drop_pts + [drop_pts[0]], 7, INK)
            draw.ellipse([sw_x - 6, sw_y + 2, sw_x + 2, sw_y + 14], fill=WHITE_INK)
        elif expr == "creepy_smirk":
            pts = cubic_bezier(
                (fx - 54, mouth_y - 12),
                (fx - 15, mouth_y + 32),
                (fx + 28, mouth_y + 28),
                (fx + 62, mouth_y - 22),
                36,
            )
            draw_thick_round_curve(draw, pts, 14, INK)
            draw_thick_round_curve(draw, [(fx + 56, mouth_y - 32), (fx + 70, mouth_y - 14)], 10, INK)
        elif expr == "terror_scream":
            m_box = [fx - 44, mouth_y - 24, fx + 44, mouth_y + 68]
            draw.ellipse(m_box, fill=(45, 15, 22, 255), outline=INK, width=14)
            draw.chord([fx - 38, mouth_y - 20, fx + 38, mouth_y + 18], 180, 360, fill=WHITE_INK, outline=INK, width=6)
            draw.chord([fx - 28, mouth_y + 25, fx + 28, mouth_y + 64], 0, 180, fill=(215, 82, 95, 255), outline=INK, width=6)
            draw_thick_round_curve(draw, [(lx - 42, mouth_y - 10), (lx - 52, mouth_y + 22)], 8, INK)
            draw_thick_round_curve(draw, [(rx + 42, mouth_y - 10), (rx + 52, mouth_y + 22)], 8, INK)
        elif expr == "dance_joy":
            pts = quad_bezier((fx - 42, mouth_y - 8), (fx, mouth_y + 32), (fx + 42, mouth_y - 8), 28)
            draw_thick_round_curve(draw, pts, 13, INK)
        else:
            pts = quad_bezier((fx - 30, mouth_y + 4), (fx, mouth_y + 14), (fx + 30, mouth_y + 2), 24)
            draw_thick_round_curve(draw, pts, 12, INK)

    # Soldier 2.5D Olive-Drab Netted Military Helmet (#5c6346) seated firmly on skull
    if char_type == "stranger":
        helmet_img = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
        helmet_mask = Image.new("L", (W_CANVAS, H_CANVAS), 0)
        dh = ImageDraw.Draw(helmet_img)
        dm = ImageDraw.Draw(helmet_mask)

        dome_pts = []
        num_dome = 90
        # Raise helmet rim to y=310 on front/3q views so eyes, worried brows, and mouth are 100% visible!
        rim_y = 310 if view != "back" else head_cy + 16
        dome_cy = (head_cy - 52) if view != "back" else (head_cy + 2)
        for i in range(num_dome + 1):
            t = i / float(num_dome)
            a = math.pi + t * math.pi
            rx_d = int(head_r * 1.10)
            ry_d = int(head_r * 0.96)
            px = head_cx + rx_d * math.cos(a)
            py = dome_cy + ry_d * math.sin(a)
            dome_pts.append((px, py))

        for i in range(30, -1, -1):
            t = i / 30.0
            px = (head_cx - int(head_r * 1.10)) + t * (2 * int(head_r * 1.10))
            arch = -12 * math.sin(t * math.pi) if view != "back" else 20 * math.sin(t * math.pi)
            py = rim_y + arch
            dome_pts.append((px, py))

        dh.polygon(dome_pts, fill=HELMET_OLIVE)
        dm.polygon(dome_pts, fill=255)

        net_layer = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
        dn = ImageDraw.Draw(net_layer)
        dn.ellipse(
            [head_cx - int(head_r * 1.15), head_cy - int(head_r * 1.10), head_cx - 20, head_cy + 48],
            fill=(74, 80, 55, 255),
        )
        for offset in range(-280, 280, 34):
            dn.line(
                [(head_cx + offset - 140, head_cy - 230), (head_cx + offset + 140, head_cy + 70)],
                fill=HELMET_DARK,
                width=5,
            )
            dn.line(
                [(head_cx + offset + 140, head_cy - 230), (head_cx + offset - 140, head_cy + 70)],
                fill=HELMET_DARK,
                width=5,
            )
        band_y = rim_y - 24
        dn.line(
            [(head_cx - 240, band_y), (head_cx + 240, band_y)],
            fill=(48, 52, 35, 255),
            width=16,
        )

        helmet_over = Image.alpha_composite(helmet_img, net_layer)
        helmet_clipped = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
        helmet_clipped.paste(helmet_over, (0, 0), helmet_mask)
        canvas.alpha_composite(helmet_clipped)
        draw_thick_round_curve(draw, dome_pts + [dome_pts[0]], width=16, color=INK)


def render_pill_torso_and_limbs(
    canvas: Image.Image,
    char_type: str,
    view: str,
    pose: str = "stand",
    torso_cx: int = 512,
    torso_top: int = 575,
    torso_bot: int = 930,
    torso_w: int = 165,
):
    # Draws the RicksClips narrow rounded vertical pill torso (165px wide, 575..930) +
    # shorts (900..990), with 100% alpha-masked jersey stripes/text or soldier suspenders
    # inside the union body mask, wrapped once by a 14px #161219 outer border, plus
    # curved 17px Bezier stick limbs.
    draw_main = ImageDraw.Draw(canvas)

    sh_y = torso_top + 48
    l_sh = (torso_cx - torso_w // 2 + 10, sh_y)
    r_sh = (torso_cx + torso_w // 2 - 10, sh_y)
    hip_y = 975
    l_hip = (torso_cx - 38, hip_y)
    r_hip = (torso_cx + 38, hip_y)

    l_arm_pts = [l_sh, (l_sh[0] - 55, sh_y + 130), (l_sh[0] - 32, sh_y + 265)]
    r_arm_pts = [r_sh, (r_sh[0] + 55, sh_y + 130), (r_sh[0] + 32, sh_y + 265)]
    l_leg_pts = [l_hip, (l_hip[0] - 12, hip_y + 190), (l_hip[0] - 18, 1380)]
    r_leg_pts = [r_hip, (r_hip[0] + 12, hip_y + 190), (r_hip[0] + 18, 1380)]

    if pose == "walk_a":
        l_arm_pts = [l_sh, (l_sh[0] - 85, sh_y + 110), (l_sh[0] - 115, sh_y + 225)]
        r_arm_pts = [r_sh, (r_sh[0] + 85, sh_y + 105), (r_sh[0] + 120, sh_y + 210)]
        l_leg_pts = [l_hip, (l_hip[0] - 60, hip_y + 180), (l_hip[0] - 110, 1365)]
        r_leg_pts = [r_hip, (r_hip[0] + 65, hip_y + 170), (r_hip[0] + 115, 1360)]
    elif pose == "walk_b":
        l_arm_pts = [l_sh, (l_sh[0] - 30, sh_y + 135), (l_sh[0] - 15, sh_y + 265)]
        r_arm_pts = [r_sh, (r_sh[0] + 30, sh_y + 135), (r_sh[0] + 15, sh_y + 265)]
        l_leg_pts = [l_hip, (l_hip[0] - 10, hip_y + 190), (l_hip[0] - 8, 1385)]
        r_leg_pts = [r_hip, (r_hip[0] + 35, hip_y + 155), (r_hip[0] + 15, 1335)]
    elif pose == "walk_c":
        l_arm_pts = [l_sh, (l_sh[0] - 48, sh_y + 125), (l_sh[0] - 75, sh_y + 235)]
        r_arm_pts = [r_sh, (r_sh[0] + 52, sh_y + 120), (r_sh[0] + 82, sh_y + 230)]
        l_leg_pts = [l_hip, (l_hip[0] - 35, hip_y + 175), (l_hip[0] - 65, 1360)]
        r_leg_pts = [r_hip, (r_hip[0] + 38, hip_y + 180), (r_hip[0] + 70, 1365)]
    elif pose == "back_hip_rest":
        # Left arm forward at urinal, right curved stick arm resting on hip
        l_arm_pts = [l_sh, (l_sh[0] - 38, sh_y + 115), (l_sh[0] + 12, sh_y + 215)]
        r_arm_pts = [r_sh, (r_sh[0] + 95, sh_y + 110), (r_sh[0] + 14, sh_y + 225)]
    elif pose == "urinal_stand":
        l_arm_pts = [l_sh, (l_sh[0] - 42, sh_y + 120), (l_sh[0] + 10, sh_y + 225)]
        r_arm_pts = [r_sh, (r_sh[0] + 42, sh_y + 120), (r_sh[0] - 10, sh_y + 225)]
    elif pose == "finger_gun":
        l_arm_pts = [l_sh, (l_sh[0] - 65, sh_y + 125), (l_sh[0] - 35, sh_y + 245)]
        r_arm_pts = [r_sh, (r_sh[0] + 110, sh_y + 45), (r_sh[0] + 235, sh_y - 15)]
    elif pose == "terror_hands":
        l_arm_pts = [l_sh, (l_sh[0] - 115, sh_y - 10), (torso_cx - 175, 430)]
        r_arm_pts = [r_sh, (r_sh[0] + 115, sh_y - 10), (torso_cx + 175, 430)]
        l_leg_pts = [l_hip, (l_hip[0] - 45, hip_y + 180), (l_hip[0] - 30, 1375)]
        r_leg_pts = [r_hip, (r_hip[0] + 45, hip_y + 180), (r_hip[0] + 30, 1375)]
    elif pose == "dance_left":
        l_arm_pts = [l_sh, (l_sh[0] - 125, sh_y - 45), (l_sh[0] - 185, sh_y - 155)]
        r_arm_pts = [r_sh, (r_sh[0] + 95, sh_y + 65), (r_sh[0] + 165, sh_y + 15)]
        l_leg_pts = [l_hip, (l_hip[0] - 85, hip_y + 150), (l_hip[0] - 45, 1350)]
        r_leg_pts = [r_hip, (r_hip[0] + 35, hip_y + 185), (r_hip[0] + 65, 1380)]
    elif pose == "dance_right":
        l_arm_pts = [l_sh, (l_sh[0] - 95, sh_y + 65), (l_sh[0] - 165, sh_y + 15)]
        r_arm_pts = [r_sh, (r_sh[0] + 125, sh_y - 45), (r_sh[0] + 185, sh_y - 155)]
        l_leg_pts = [l_hip, (l_hip[0] - 35, hip_y + 185), (l_hip[0] - 65, 1380)]
        r_leg_pts = [r_hip, (r_hip[0] + 85, hip_y + 150), (r_hip[0] + 45, 1350)]

    # Draw Legs first (behind torso)
    for leg in (l_leg_pts, r_leg_pts):
        curve = quad_bezier(leg[0], leg[1], leg[2], steps=36)
        draw_thick_round_curve(draw_main, curve, width=17, color=INK)
        fx_foot, fy_foot = leg[2]
        draw_main.ellipse([fx_foot - 24, fy_foot - 12, fx_foot + 24, fy_foot + 14], fill=INK)

    # Union Mask for Pill Torso (575..930) + Shorts (900..990)
    torso_mask = Image.new("L", (W_CANVAS, H_CANVAS), 0)
    shorts_mask = Image.new("L", (W_CANVAS, H_CANVAS), 0)
    dt_m = ImageDraw.Draw(torso_mask)
    ds_m = ImageDraw.Draw(shorts_mask)

    t_box = [torso_cx - torso_w // 2, torso_top, torso_cx + torso_w // 2, torso_bot]
    s_box = [torso_cx - torso_w // 2 + 4, 895, torso_cx + torso_w // 2 - 4, 992]
    dt_m.rounded_rectangle(t_box, radius=torso_w // 2, fill=255)
    ds_m.rounded_rectangle(s_box, radius=36, fill=255)

    union_mask = ImageChops.lighter(torso_mask, shorts_mask)

    body_layer = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
    db = ImageDraw.Draw(body_layer)

    if char_type == "you":
        db.rectangle([0, torso_top, W_CANVAS, 915], fill=JERSEY_GREEN)
        db.rectangle([torso_cx - torso_w // 2, torso_top, torso_cx - 32, 915], fill=JERSEY_DARK)
        db.line([(torso_cx - 90, torso_top + 42), (torso_cx + 90, torso_top + 42)], fill=WHITE_INK, width=14)
        db.line([(torso_cx - 90, torso_top + 62), (torso_cx + 90, torso_top + 62)], fill=WHITE_INK, width=8)

        font_sm = load_font(15, bold=True)
        font_ny = load_font(22, bold=True)
        font_num = load_font(86, bold=True)

        tx_shift = 0
        if view == "three_quarter_r":
            tx_shift = 16
        elif view == "three_quarter_l":
            tx_shift = -16

        if view != "back":
            db.text((torso_cx + tx_shift, torso_top + 22), "OUT HERE", fill=WHITE_INK, font=font_sm, anchor="mm")
        db.text((torso_cx + tx_shift, torso_top + 108), "NEW YORK", fill=WHITE_INK, font=font_ny, anchor="mm")
        db.text((torso_cx + tx_shift, torso_top + 178), "17", fill=WHITE_INK, font=font_num, anchor="mm")

        db.rectangle([0, 900, W_CANVAS, 995], fill=JEANS_NAVY)
        db.line([(torso_cx - 90, 900), (torso_cx + 90, 900)], fill=INK, width=8)
    else:
        db.rectangle([0, torso_top, W_CANVAS, 910], fill=SOLDIER_KHAKI)
        db.rectangle([torso_cx - torso_w // 2, torso_top, torso_cx - 32, 910], fill=(136, 114, 88, 255))

        if view == "back":
            db.line(
                [(torso_cx - 52, torso_top + 10), (torso_cx + 48, 895)],
                fill=SUSPENDER_BEIGE,
                width=22,
            )
            db.line(
                [(torso_cx + 52, torso_top + 10), (torso_cx - 48, 895)],
                fill=SUSPENDER_BEIGE,
                width=22,
            )
            db.line([(torso_cx - 52, torso_top + 10), (torso_cx + 48, 895)], fill=INK, width=4)
            db.line([(torso_cx + 52, torso_top + 10), (torso_cx - 48, 895)], fill=INK, width=4)
        else:
            for sx in (torso_cx - 42, torso_cx + 42):
                db.line([(sx, torso_top + 10), (sx, 895)], fill=SUSPENDER_BEIGE, width=22)
                db.rectangle([sx - 13, 735, sx + 13, 760], fill=POUCH_BROWN, outline=INK, width=4)

        db.rectangle([0, 895, W_CANVAS, 995], fill=SOLDIER_PANTS)
        db.rectangle([0, 882, W_CANVAS, 914], fill=POUCH_BROWN)
        db.line([(torso_cx - 90, 882), (torso_cx + 90, 882)], fill=INK, width=6)
        db.line([(torso_cx - 90, 914), (torso_cx + 90, 914)], fill=INK, width=6)
        for px in (torso_cx - 46, torso_cx, torso_cx + 46):
            db.rounded_rectangle([px - 18, 874, px + 18, 926], radius=6, fill=POUCH_BROWN, outline=INK, width=5)

    clipped_body = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
    clipped_body.paste(body_layer, (0, 0), union_mask)

    dilated_mask = union_mask.filter(ImageFilter.MaxFilter(29))
    border_layer = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
    border_layer.paste(INK, (0, 0), dilated_mask)
    canvas.alpha_composite(border_layer)
    canvas.alpha_composite(clipped_body)

    draw_main.line([(torso_cx, 945), (torso_cx, 990)], fill=INK, width=10)

    # Curved Stick Arms (width = 17px, #161219)
    for arm in (l_arm_pts, r_arm_pts):
        curve = quad_bezier(arm[0], arm[1], arm[2], steps=36)
        draw_thick_round_curve(draw_main, curve, width=17, color=INK)
        hx, hy = arm[2]
        draw_main.ellipse([hx - 14, hy - 14, hx + 14, hy + 14], fill=INK)

    if pose == "finger_gun":
        gx, gy = r_arm_pts[2]
        draw_thick_round_curve(draw_main, [(gx, gy), (gx + 38, gy - 4)], width=12, color=INK)
        draw_thick_round_curve(draw_main, [(gx - 4, gy), (gx + 10, gy - 28)], width=11, color=INK)


def generate_character_sprite(
    filename: str,
    char_type: str,
    view: str,
    turn_x: float,
    expr: str,
    pose: str,
) -> str:
    out_path = os.path.join(SPRITE_DIR, filename)
    canvas = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
    render_pill_torso_and_limbs(canvas, char_type=char_type, view=view, pose=pose)
    render_head_with_helmet_and_face(
        canvas,
        char_type=char_type,
        view=view,
        turn_x=turn_x,
        expr=expr,
    )
    canvas.save(out_path, "PNG")
    return out_path


def generate_question_mark_sprite() -> str:
    out_path = os.path.join(SPRITE_DIR, "question_badge.png")
    img = Image.new("RGBA", (512, 512), TRANSPARENT_INK)
    draw = ImageDraw.Draw(img)
    draw.ellipse([56, 56, 456, 456], fill=(255, 218, 36, 255), outline=INK, width=20)
    draw.arc([84, 84, 428, 428], 200, 330, fill=(255, 248, 175, 255), width=14)
    font_q = load_font(290, bold=True)
    draw.text((262, 272), "?", fill=INK, font=font_q, anchor="mm")
    img.save(out_path, "PNG")
    return out_path


def generate_hud_badge(filename: str, text: str, accent_color=(255, 214, 10, 255)) -> str:
    out_path = os.path.join(HUD_DIR, filename)
    w, h = 1080, 180
    img = Image.new("RGBA", (w, h), TRANSPARENT_INK)
    draw = ImageDraw.Draw(img)

    pill_box = [44, 24, w - 44, h - 24]
    draw.rounded_rectangle(pill_box, radius=36, fill=(18, 22, 30, 238), outline=accent_color, width=6)
    draw.rounded_rectangle([64, 46, 82, h - 46], radius=8, fill=accent_color)

    font_hud = load_font(34, bold=True)
    draw.text((w // 2 + 10, h // 2), text, fill=(252, 252, 255, 255), font=font_hud, anchor="mm")
    img.save(out_path, "PNG")
    return out_path


def build_all_sprites() -> dict:
    # Generates all sprites needed for Part 1 (Scenes 1-2) with lively expressions & rear urinal poses
    paths = {}

    you_specs = [
        ("you_walk_1.png", "three_quarter_r", 0.16, "whistle_walk", "walk_a"),
        ("you_walk_2.png", "three_quarter_r", 0.16, "whistle_talk", "walk_b"),
        ("you_walk_3.png", "three_quarter_r", 0.16, "whistle_walk", "walk_c"),
        ("you_walk_4.png", "three_quarter_r", 0.16, "whistle_blink", "walk_b"),
        ("you_stand_3q.png", "three_quarter_r", 0.14, "neutral", "stand"),
        ("you_stand_blink.png", "three_quarter_r", 0.14, "blink", "stand"),
        ("you_back_idle.png", "back", 0.0, "neutral", "urinal_stand"),
        ("you_back_hip_rest.png", "back", 0.0, "neutral", "back_hip_rest"),
        ("you_awkward_1.png", "three_quarter_r", 0.20, "awkward_side", "urinal_stand"),
        ("you_awkward_2.png", "three_quarter_r", 0.22, "awkward_talk", "urinal_stand"),
        ("you_awkward_blink.png", "three_quarter_r", 0.20, "awkward_blink", "urinal_stand"),
        ("you_paranoid_sweat.png", "front", -0.18, "paranoid_sweat", "urinal_stand"),
    ]
    for fname, view, tx, expr, pose in you_specs:
        paths[fname] = generate_character_sprite(fname, "you", view, tx, expr, pose)

    stranger_specs = [
        ("stranger_back_idle_1.png", "back", 0.0, "neutral", "urinal_stand"),
        ("stranger_back_idle_2.png", "back", 0.0, "neutral", "back_hip_rest"),
        ("stranger_front_nervous_1.png", "front", -0.16, "nervous_1", "urinal_stand"),
        ("stranger_front_sweat_2.png", "front", -0.20, "paranoid_sweat", "urinal_stand"),
        ("stranger_front_talk_3.png", "front", -0.18, "nervous_talk", "urinal_stand"),
        ("stranger_front_blink.png", "front", -0.18, "nervous_blink", "urinal_stand"),
    ]
    for fname, view, tx, expr, pose in stranger_specs:
        paths[fname] = generate_character_sprite(fname, "stranger", view, tx, expr, pose)

    paths["question_badge.png"] = generate_question_mark_sprite()

    paths["hud_scene1.png"] = generate_hud_badge(
        "hud_scene1.png",
        "THE URINAL DILEMMA: WHICH ONE DO YOU PICK?",
        accent_color=(255, 214, 10, 255),
    )
    paths["hud_scene2.png"] = generate_hud_badge(
        "hud_scene2.png",
        "OPTION 1: FARTHEST URINAL = MAXIMUM PARANOIA",
        accent_color=(56, 189, 248, 255),
    )
    paths["hud_scene3.png"] = generate_hud_badge(
        "hud_scene3.png",
        "OPTION 2: ADJACENT URINAL = SOCIOPATH DANGER",
        accent_color=(248, 113, 113, 255),
    )
    paths["hud_scene4.png"] = generate_hud_badge(
        "hud_scene4.png",
        "SECRET ENDING: SYNCHRONIZED BROTHERHOOD",
        accent_color=(74, 222, 128, 255),
    )

    return paths


# ==============================================================================
# 3. BLENDER 4.2 SCENE & MATERIAL HELPERS
# ==============================================================================
def clear_scene():
    for coll in list(bpy.context.scene.collection.children):
        bpy.context.scene.collection.children.unlink(coll)
    for coll in list(bpy.data.collections):
        bpy.data.collections.remove(coll)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    for img in list(bpy.data.images):
        bpy.data.images.remove(img)
    for curve in list(bpy.data.curves):
        bpy.data.curves.remove(curve)


def set_principled_specular(bsdf_node, value: float):
    for socket_name in ("Specular IOR Level", "Specular"):
        if socket_name in bsdf_node.inputs:
            bsdf_node.inputs[socket_name].default_value = value
            break


def configure_alpha_material(mat: bpy.types.Material):
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"


def configure_render_and_compositor():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    if hasattr(scene, "eevee") and hasattr(scene.eevee, "use_raytracing"):
        scene.eevee.use_raytracing = False

    scene.render.use_simplify = True
    scene.render.simplify_subdivision = 2
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 855

    # AgX Color Management
    try:
        scene.view_settings.view_transform = "AgX"
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        try:
            scene.view_settings.look = "Medium High Contrast"
        except Exception:
            pass

    # Compositor: Clean FOG_GLOW Glare + HueSat (+22% Saturation, +6% Value)
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    n_rl = tree.nodes.new("CompositorNodeRLayers")
    n_rl.location = (-420, 0)

    n_glare = tree.nodes.new("CompositorNodeGlare")
    n_glare.location = (-140, 0)
    n_glare.glare_type = "FOG_GLOW"
    n_glare.quality = "MEDIUM"
    n_glare.mix = 0.08
    n_glare.threshold = 0.90

    n_huesat = tree.nodes.new("CompositorNodeHueSat")
    n_huesat.location = (120, 0)
    n_huesat.inputs["Hue"].default_value = 0.5
    n_huesat.inputs["Saturation"].default_value = 1.22
    n_huesat.inputs["Value"].default_value = 1.06

    n_comp = tree.nodes.new("CompositorNodeComposite")
    n_comp.location = (380, 0)

    tree.links.new(n_rl.outputs["Image"], n_glare.inputs["Image"])
    tree.links.new(n_glare.outputs["Image"], n_huesat.inputs["Image"])
    tree.links.new(n_huesat.outputs["Image"], n_comp.inputs["Image"])


# ==============================================================================
# 4. PROCEDURAL 3D MATERIALS & RICKSCLIPS EMISSION-ASSISTED SPRITE SHADER
# ==============================================================================
def create_azure_floor_tile_material() -> bpy.types.Material:
    # Glossy azure-blue square tile grid (#1488d8 base + #d8f0ff white grout, Roughness = 0.15)
    mat = bpy.data.materials.new(name="Mat_Floor_Azure_Tile")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    n_out = nodes.new("ShaderNodeOutputMaterial")
    n_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    n_bsdf.inputs["Roughness"].default_value = 0.15
    set_principled_specular(n_bsdf, 0.65)

    n_texcoord = nodes.new("ShaderNodeTexCoord")
    n_brick = nodes.new("ShaderNodeTexBrick")
    n_brick.offset_frequency = 1
    n_brick.squash_frequency = 1
    n_brick.inputs["Color1"].default_value = (0.015, 0.240, 0.680, 1.0)
    n_brick.inputs["Color2"].default_value = (0.018, 0.265, 0.720, 1.0)
    n_brick.inputs["Mortar"].default_value = (0.690, 0.870, 1.000, 1.0)
    n_brick.inputs["Scale"].default_value = 4.2
    n_brick.inputs["Mortar Size"].default_value = 0.025
    n_brick.inputs["Mortar Smooth"].default_value = 0.05
    n_brick.inputs["Brick Width"].default_value = 0.5
    n_brick.inputs["Row Height"].default_value = 0.5

    n_bump = nodes.new("ShaderNodeBump")
    n_bump.inputs["Strength"].default_value = 0.08
    n_bump.inputs["Distance"].default_value = 0.01

    links.new(n_texcoord.outputs["Object"], n_brick.inputs["Vector"])
    links.new(n_brick.outputs["Color"], n_bsdf.inputs["Base Color"])
    links.new(n_brick.outputs["Fac"], n_bump.inputs["Height"])
    links.new(n_bump.outputs["Normal"], n_bsdf.inputs["Normal"])
    links.new(n_bsdf.outputs["BSDF"], n_out.inputs["Surface"])
    return mat


def create_charcoal_wall_tile_material() -> bpy.types.Material:
    # Matte dark charcoal-black tiled partition walls (#22262e + #15181e grout, Roughness = 0.55)
    mat = bpy.data.materials.new(name="Mat_Wall_Charcoal_Tile")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    n_out = nodes.new("ShaderNodeOutputMaterial")
    n_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    n_bsdf.inputs["Roughness"].default_value = 0.55
    set_principled_specular(n_bsdf, 0.28)

    n_texcoord = nodes.new("ShaderNodeTexCoord")
    n_brick = nodes.new("ShaderNodeTexBrick")
    n_brick.offset_frequency = 2
    n_brick.inputs["Color1"].default_value = (0.028, 0.036, 0.052, 1.0)
    n_brick.inputs["Color2"].default_value = (0.034, 0.044, 0.062, 1.0)
    n_brick.inputs["Mortar"].default_value = (0.012, 0.015, 0.022, 1.0)
    n_brick.inputs["Scale"].default_value = 5.0
    n_brick.inputs["Mortar Size"].default_value = 0.02
    n_brick.inputs["Brick Width"].default_value = 0.5
    n_brick.inputs["Row Height"].default_value = 0.5

    n_bump = nodes.new("ShaderNodeBump")
    n_bump.inputs["Strength"].default_value = 0.06

    links.new(n_texcoord.outputs["Object"], n_brick.inputs["Vector"])
    links.new(n_brick.outputs["Color"], n_bsdf.inputs["Base Color"])
    links.new(n_brick.outputs["Fac"], n_bump.inputs["Height"])
    links.new(n_bump.outputs["Normal"], n_bsdf.inputs["Normal"])
    links.new(n_bsdf.outputs["BSDF"], n_out.inputs["Surface"])
    return mat


def create_solid_material(name: str, rgba, roughness=0.3, metallic=0.0, emission_strength=0.0) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    n_out = nodes.new("ShaderNodeOutputMaterial")
    n_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    n_bsdf.inputs["Base Color"].default_value = rgba
    n_bsdf.inputs["Roughness"].default_value = roughness
    n_bsdf.inputs["Metallic"].default_value = metallic
    set_principled_specular(n_bsdf, 0.5)
    if emission_strength > 0.0 and "Emission Color" in n_bsdf.inputs:
        n_bsdf.inputs["Emission Color"].default_value = rgba
        n_bsdf.inputs["Emission Strength"].default_value = emission_strength
    links.new(n_bsdf.outputs["BSDF"], n_out.inputs["Surface"])
    return mat


def create_contact_shadow_material(name="Mat_Contact_Shadow") -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    configure_alpha_material(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    n_out = nodes.new("ShaderNodeOutputMaterial")
    n_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    n_bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.02, 1.0)
    n_bsdf.inputs["Roughness"].default_value = 1.0
    set_principled_specular(n_bsdf, 0.0)

    n_uv = nodes.new("ShaderNodeTexCoord")
    n_grad = nodes.new("ShaderNodeTexGradient")
    n_grad.gradient_type = "QUADRATIC_SPHERE"
    n_map = nodes.new("ShaderNodeMapping")
    n_map.inputs["Location"].default_value = (-0.5, -0.5, 0.0)
    n_map.inputs["Scale"].default_value = (2.0, 2.0, 1.0)

    n_math = nodes.new("ShaderNodeMath")
    n_math.operation = "MULTIPLY"
    n_math.inputs[1].default_value = 0.55

    links.new(n_uv.outputs["UV"], n_map.inputs["Vector"])
    links.new(n_map.outputs["Vector"], n_grad.inputs["Vector"])
    links.new(n_grad.outputs["Fac"], n_math.inputs[0])
    links.new(n_math.outputs["Value"], n_bsdf.inputs["Alpha"])
    links.new(n_bsdf.outputs["BSDF"], n_out.inputs["Surface"])
    return mat


def create_ricksclips_sprite_material(name: str, initial_img_path: str):
    # RicksClips Law #1: Emission-Assisted Cel Shader (92% Emission + 8% Principled Diffuse)
    # driven by PNG alpha so AgX tone-mapping keeps #fdfaf2 bright cream and never turns it muddy grey.
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    configure_alpha_material(mat)
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    n_out = nodes.new("ShaderNodeOutputMaterial")
    n_mix_alpha = nodes.new("ShaderNodeMixShader")
    n_transp = nodes.new("ShaderNodeBsdfTransparent")

    n_mix_cel = nodes.new("ShaderNodeMixShader")
    n_mix_cel.inputs["Fac"].default_value = 0.05  # 95% Emission + 5% Principled

    n_emis = nodes.new("ShaderNodeEmission")
    n_emis.inputs["Strength"].default_value = 1.10

    n_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    n_bsdf.inputs["Roughness"].default_value = 0.85
    set_principled_specular(n_bsdf, 0.05)

    n_tex = nodes.new("ShaderNodeTexImage")
    n_tex.extension = "CLIP"
    n_tex.interpolation = "Linear"
    if os.path.exists(initial_img_path):
        img = bpy.data.images.load(initial_img_path, check_existing=True)
        img.alpha_mode = "STRAIGHT"
        n_tex.image = img

    links.new(n_tex.outputs["Color"], n_emis.inputs["Color"])
    links.new(n_tex.outputs["Color"], n_bsdf.inputs["Base Color"])
    links.new(n_emis.outputs["Emission"], n_mix_cel.inputs[1])
    links.new(n_bsdf.outputs["BSDF"], n_mix_cel.inputs[2])

    links.new(n_tex.outputs["Alpha"], n_mix_alpha.inputs["Fac"])
    links.new(n_transp.outputs["BSDF"], n_mix_alpha.inputs[1])
    links.new(n_mix_cel.outputs["Shader"], n_mix_alpha.inputs[2])
    links.new(n_mix_alpha.outputs["Shader"], n_out.inputs["Surface"])

    return mat, n_tex


def setup_world_sky_gradient_and_lighting():
    # 3-Stop Vertical Sky World Gradient (#0d47a1 deep zenith -> #29b6f6 midday blue -> #b3e5fc horizon)
    # with procedural fluffy white clouds + Directional SUN key light (energy=3.8, #fff7e6, angle=12 deg).
    world = bpy.data.worlds.new("World_RicksClips_Sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()

    n_out = nodes.new("ShaderNodeOutputWorld")
    n_bg = nodes.new("ShaderNodeBackground")
    n_bg.inputs["Strength"].default_value = 1.05

    n_texcoord = nodes.new("ShaderNodeTexCoord")
    n_sep = nodes.new("ShaderNodeSeparateXYZ")

    n_map_z = nodes.new("ShaderNodeMapRange")
    n_map_z.inputs["From Min"].default_value = -0.05
    n_map_z.inputs["From Max"].default_value = 0.65

    n_ramp = nodes.new("ShaderNodeValToRGB")
    cr = n_ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.445, 0.785, 0.975, 1.0)
    cr.elements[1].position = 0.48
    cr.elements[1].color = (0.025, 0.455, 0.915, 1.0)
    e_top = cr.elements.new(1.0)
    e_top.color = (0.005, 0.065, 0.355, 1.0)

    n_noise = nodes.new("ShaderNodeTexNoise")
    n_noise.inputs["Scale"].default_value = 3.8
    n_noise.inputs["Detail"].default_value = 5.0
    n_noise.inputs["Roughness"].default_value = 0.58

    n_cloud_ramp = nodes.new("ShaderNodeValToRGB")
    n_cloud_ramp.color_ramp.elements[0].position = 0.56
    n_cloud_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    n_cloud_ramp.color_ramp.elements[1].position = 0.76
    n_cloud_ramp.color_ramp.elements[1].color = (0.38, 0.38, 0.38, 1.0)

    n_mix_cloud = nodes.new("ShaderNodeMixRGB")
    n_mix_cloud.blend_type = "MIX"
    n_mix_cloud.inputs[2].default_value = (0.96, 0.98, 1.0, 1.0)

    links.new(n_texcoord.outputs["Generated"], n_sep.inputs["Vector"])
    links.new(n_sep.outputs["Z"], n_map_z.inputs["Value"])
    links.new(n_map_z.outputs["Result"], n_ramp.inputs["Fac"])
    links.new(n_texcoord.outputs["Generated"], n_noise.inputs["Vector"])
    links.new(n_noise.outputs["Fac"], n_cloud_ramp.inputs["Fac"])
    links.new(n_cloud_ramp.outputs["Color"], n_mix_cloud.inputs["Fac"])
    links.new(n_ramp.outputs["Color"], n_mix_cloud.inputs[1])
    links.new(n_mix_cloud.outputs["Color"], n_bg.inputs["Color"])
    links.new(n_bg.outputs["Background"], n_out.inputs["Surface"])

    # Bright Directional SUN key light (energy = 5.2, warm sunlight #fff9eb)
    sun_data = bpy.data.lights.new(name="Sun_KeyLight", type="SUN")
    sun_data.energy = 5.2
    sun_data.color = (1.0, 0.976, 0.922)
    sun_data.angle = math.radians(12.0)
    if hasattr(sun_data, "use_shadow"):
        sun_data.use_shadow = True
    sun_obj = bpy.data.objects.new(name="Sun_KeyLight", object_data=sun_data)
    bpy.context.scene.collection.objects.link(sun_obj)
    sun_obj.location = (-4.0, -5.0, 8.0)
    sun_obj.rotation_euler = (math.radians(48.0), math.radians(-24.0), math.radians(-32.0))

    # Bright Overhead Daylight Fill AREA Light (location=(0.0, 0.2, 3.8), size=6.0, energy=400.0, #e8f4ff)
    fill_data = bpy.data.lights.new(name="Area_FillLight", type="AREA")
    fill_data.energy = 400.0
    fill_data.size = 6.0
    fill_data.color = (0.910, 0.957, 1.0)
    if hasattr(fill_data, "use_shadow"):
        fill_data.use_shadow = False
    fill_obj = bpy.data.objects.new(name="Area_FillLight", object_data=fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.location = (0.0, 0.2, 3.8)
    fill_obj.rotation_euler = (math.radians(18.0), 0.0, 0.0)


# ==============================================================================
# 5. 3D OPEN-AIR RESTROOM SET, 4 BEVELED URINALS, TYPOGRAPHY & WINTER TREE
# ==============================================================================
def add_beveled_box(name: str, loc, scale, mat, bevel_width=0.02, segments=3):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bev = obj.modifiers.new(name="Bevel", type="BEVEL")
    bev.width = bevel_width
    bev.segments = segments
    obj.data.materials.append(mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def build_detailed_urinal(index: int, x_pos: float, wall_y: float, mats: dict):
    # Builds a multi-part beveled 3D white ceramic urinal assembly on the front face of the North Wall
    # Parent sits at (x_pos, 1.58, 0.0); all child parts use local offsets so world Y = 1.58 (in front of Y=1.80 wall)
    parent = bpy.data.objects.new(f"Urinal_{index}_Root", None)
    bpy.context.scene.collection.objects.link(parent)
    parent.location = (x_pos, 1.58, 0.0)

    bpy.ops.mesh.primitive_plane_add(
        size=1.0,
        location=(0.0, 0.20, 0.92),
        rotation=(math.radians(90), 0, 0),
    )
    sh_wall = bpy.context.active_object
    sh_wall.name = f"Urinal_{index}_WallShadow"
    sh_wall.scale = (0.64, 1.05, 1.0)
    sh_wall.data.materials.append(mats["shadow"])
    sh_wall.parent = parent

    body = add_beveled_box(
        f"Urinal_{index}_Body",
        loc=(0.0, 0.06, 0.92),
        scale=(0.52, 0.26, 0.78),
        mat=mats["porcelain"],
        bevel_width=0.04,
        segments=4,
    )
    body.parent = parent

    basin = add_beveled_box(
        f"Urinal_{index}_Basin",
        loc=(0.0, -0.02, 0.90),
        scale=(0.36, 0.16, 0.62),
        mat=mats["basin_dark"],
        bevel_width=0.025,
        segments=3,
    )
    basin.parent = parent

    for side, s_label in ((-1, "L"), (1, "R")):
        wing = add_beveled_box(
            f"Urinal_{index}_Wing_{s_label}",
            loc=(side * 0.23, -0.02, 0.92),
            scale=(0.08, 0.30, 0.76),
            mat=mats["porcelain"],
            bevel_width=0.025,
            segments=3,
        )
        wing.parent = parent

    bowl_lip = add_beveled_box(
        f"Urinal_{index}_BowlLip",
        loc=(0.0, -0.06, 0.56),
        scale=(0.50, 0.34, 0.16),
        mat=mats["porcelain"],
        bevel_width=0.035,
        segments=4,
    )
    bowl_lip.parent = parent

    top_hood = add_beveled_box(
        f"Urinal_{index}_TopHood",
        loc=(0.0, 0.02, 1.30),
        scale=(0.50, 0.28, 0.10),
        mat=mats["porcelain"],
        bevel_width=0.03,
        segments=3,
    )
    top_hood.parent = parent

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.024, depth=0.22, location=(0.0, 0.04, 1.42)
    )
    pipe_v = bpy.context.active_object
    pipe_v.name = f"Urinal_{index}_FlushPipe"
    pipe_v.data.materials.append(mats["chrome"])
    pipe_v.parent = parent

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=0.026,
        depth=0.18,
        location=(0.0, 0.12, 1.50),
        rotation=(math.radians(90), 0, 0),
    )
    pipe_h = bpy.context.active_object
    pipe_h.name = f"Urinal_{index}_WallStub"
    pipe_h.data.materials.append(mats["chrome"])
    pipe_h.parent = parent

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.045, depth=0.07, location=(0.0, 0.04, 1.50)
    )
    valve = bpy.context.active_object
    valve.name = f"Urinal_{index}_Valve"
    valve.data.materials.append(mats["chrome"])
    valve.parent = parent

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.014,
        depth=0.12,
        location=(-0.06, 0.04, 1.50),
        rotation=(0, math.radians(90), 0),
    )
    handle = bpy.context.active_object
    handle.name = f"Urinal_{index}_Handle"
    handle.data.materials.append(mats["chrome"])
    handle.parent = parent

    return parent


def create_3d_wall_text(name: str, text_body: str, loc, rot_euler, size: float, extrude: float, mat):
    bpy.ops.object.text_add(location=loc, rotation=rot_euler)
    txt_obj = bpy.context.active_object
    txt_obj.name = name
    txt_obj.data.body = text_body
    txt_obj.data.size = size
    txt_obj.data.extrude = extrude
    txt_obj.data.bevel_depth = 0.004
    txt_obj.data.space_character = 1.18
    txt_obj.data.align_x = "CENTER"
    txt_obj.data.align_y = "CENTER"
    txt_obj.data.materials.append(mat)
    return txt_obj


def build_exterior_winter_tree(loc_x=-5.2, loc_y=1.2, mat_bark=None):
    branches = [
        ((loc_x, loc_y, 0.0), (loc_x + 0.1, loc_y - 0.05, 1.8), 0.18, 0.12),
        ((loc_x + 0.1, loc_y - 0.05, 1.8), (loc_x - 0.55, loc_y + 0.25, 3.1), 0.11, 0.05),
        ((loc_x + 0.1, loc_y - 0.05, 1.8), (loc_x + 0.65, loc_y - 0.20, 3.25), 0.10, 0.05),
        ((loc_x - 0.55, loc_y + 0.25, 3.1), (loc_x - 1.05, loc_y + 0.45, 4.0), 0.05, 0.02),
        ((loc_x - 0.55, loc_y + 0.25, 3.1), (loc_x - 0.20, loc_y + 0.55, 4.1), 0.045, 0.02),
        ((loc_x + 0.65, loc_y - 0.20, 3.25), (loc_x + 1.15, loc_y + 0.10, 4.15), 0.05, 0.02),
        ((loc_x + 0.65, loc_y - 0.20, 3.25), (loc_x + 0.35, loc_y - 0.50, 4.05), 0.045, 0.018),
    ]
    for idx, (p0, p1, r0, r1) in enumerate(branches):
        v0 = mathutils.Vector(p0)
        v1 = mathutils.Vector(p1)
        mid = (v0 + v1) * 0.5
        diff = v1 - v0
        length = diff.length
        bpy.ops.mesh.primitive_cone_add(
            vertices=12, radius1=r0, radius2=r1, depth=length, location=mid
        )
        cone = bpy.context.active_object
        cone.name = f"WinterTree_Branch_{idx}"
        rot_quat = diff.to_track_quat("Z", "Y")
        cone.rotation_euler = rot_quat.to_euler()
        if mat_bark:
            cone.data.materials.append(mat_bark)


def build_restroom_set_and_props(sprite_paths: dict):
    mats = {
        "floor": create_azure_floor_tile_material(),
        "wall": create_charcoal_wall_tile_material(),
        "porcelain": create_solid_material("Mat_Porcelain_White", (0.97, 0.985, 1.0, 1.0), roughness=0.12, emission_strength=0.25),
        "basin_dark": create_solid_material("Mat_Basin_Dark", (0.024, 0.032, 0.044, 1.0), roughness=0.35),
        "chrome": create_solid_material("Mat_Flush_Chrome", (0.85, 0.88, 0.92, 1.0), roughness=0.15, metallic=0.90),
        "text_white": create_solid_material(
            "Mat_Text_White", (0.96, 0.98, 1.0, 1.0), roughness=0.25, emission_strength=0.25
        ),
        "grass": create_solid_material("Mat_Exterior_Grass", (0.065, 0.285, 0.085, 1.0), roughness=0.85),
        "bark": create_solid_material("Mat_Tree_Bark", (0.12, 0.09, 0.07, 1.0), roughness=0.85),
        "shadow": create_contact_shadow_material(),
    }

    add_beveled_box(
        "Restroom_Floor",
        loc=(0.0, -0.8, -0.05),
        scale=(8.4, 6.4, 0.10),
        mat=mats["floor"],
        bevel_width=0.01,
        segments=2,
    )

    add_beveled_box(
        "Exterior_Grass_Strip",
        loc=(-6.8, -0.5, -0.06),
        scale=(5.6, 9.0, 0.10),
        mat=mats["grass"],
        bevel_width=0.01,
        segments=2,
    )
    build_exterior_winter_tree(loc_x=-5.4, loc_y=1.35, mat_bark=mats["bark"])

    add_beveled_box(
        "Wall_North_Urinals",
        loc=(0.0, 1.92, 1.32),
        scale=(7.0, 0.24, 2.65),
        mat=mats["wall"],
        bevel_width=0.018,
        segments=2,
    )

    add_beveled_box(
        "Wall_East_Side",
        loc=(3.4, -0.15, 1.32),
        scale=(0.24, 4.3, 2.65),
        mat=mats["wall"],
        bevel_width=0.018,
        segments=2,
    )

    add_beveled_box(
        "Wall_West_EntryPartition",
        loc=(-3.4, -1.25, 1.32),
        scale=(0.24, 3.7, 2.65),
        mat=mats["wall"],
        bevel_width=0.018,
        segments=2,
    )

    # 3D wall text removed per Director instructions (clean tiled restroom walls)

    urinal_xs = [-2.1, -0.7, 0.7, 2.1]
    for idx, ux in enumerate(urinal_xs, start=1):
        build_detailed_urinal(idx, ux, wall_y=1.58, mats=mats)

    q_cards = []
    for idx, ux in enumerate([-2.1, -0.7, 0.7], start=1):
        bpy.ops.mesh.primitive_plane_add(
            size=1.0,
            location=(ux, 1.42, 1.72),
            rotation=(math.radians(90), 0.0, 0.0),
        )
        q_obj = bpy.context.active_object
        q_obj.name = f"Question_Card_{idx}"
        q_mat, _ = create_ricksclips_sprite_material(f"Mat_Question_{idx}", sprite_paths["question_badge.png"])
        q_obj.data.materials.append(q_mat)
        q_obj.scale = (0.0, 0.0, 0.0)
        q_cards.append(q_obj)

    return mats, q_cards


# ==============================================================================
# 6. MULTI-PLANE POSE RIGS (`create_pose_rig` + `key_active_pose`) & HUD RIG
# ==============================================================================
def create_pose_rig(name: str, pose_keys: list, sprite_paths: dict, shadow_mat: bpy.types.Material):
    root = bpy.data.objects.new(f"{name}_Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.empty_display_size = 0.4

    bpy.ops.mesh.primitive_plane_add(size=0.82, location=(0.0, 0.0, 0.008))
    sh_disc = bpy.context.active_object
    sh_disc.name = f"{name}_ShadowDisc"
    sh_disc.scale = (1.0, 0.75, 1.0)
    sh_disc.data.materials.append(shadow_mat)
    sh_disc.parent = root

    pose_planes = {}
    for idx, pkey in enumerate(pose_keys):
        if pkey not in sprite_paths:
            continue
        bpy.ops.mesh.primitive_plane_add(
            size=1.0,
            location=(0.0, 0.0, 0.87),
            rotation=(math.radians(90), 0.0, 0.0),
        )
        plane = bpy.context.active_object
        plane.name = f"{name}_Pose_{pkey}"
        plane.scale = (1.16, 1.74, 1.0) if idx == 0 else (0.0, 0.0, 0.0)
        mat, _ = create_ricksclips_sprite_material(f"Mat_{name}_{pkey}", sprite_paths[pkey])
        plane.data.materials.append(mat)
        plane.parent = root
        pose_planes[pkey] = plane

    return root, pose_planes


def key_active_pose(
    pose_planes: dict,
    active_key: str,
    f_start: int,
    f_end: int,
    active_scale=(1.16, 1.74, 1.0),
):
    zero_scale = (0.0, 0.0, 0.0)
    for pkey, plane_obj in pose_planes.items():
        sc = active_scale if pkey == active_key else zero_scale
        for fr in (f_start, f_end):
            plane_obj.scale = sc
            plane_obj.keyframe_insert(data_path="scale", frame=fr)
        if plane_obj.animation_data and plane_obj.animation_data.action:
            for fc in plane_obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def create_camera_and_hud(sprite_paths: dict):
    cam_data = bpy.data.cameras.new(name="Main_Camera")
    cam_data.lens = 38.0
    cam_data.sensor_width = 36.0
    cam_data.dof.use_dof = False
    cam_data.dof.aperture_fstop = 16.0
    cam_data.dof.focus_distance = 3.5

    cam_obj = bpy.data.objects.new(name="Main_Camera", object_data=cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    hud_root = bpy.data.objects.new("Camera_Top_HUD", None)
    bpy.context.scene.collection.objects.link(hud_root)
    hud_root.parent = cam_obj
    hud_root.location = (0.0, 0.365, -0.95)
    hud_root.rotation_euler = (0.0, 0.0, 0.0)
    hud_root.scale = (0.48, 0.080, 1.0)

    hud_keys = ["hud_scene1.png", "hud_scene2.png", "hud_scene3.png", "hud_scene4.png"]
    hud_planes = {}
    for idx, hkey in enumerate(hud_keys):
        if hkey not in sprite_paths:
            continue
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
        hplane = bpy.context.active_object
        hplane.name = f"HUD_Pose_{hkey}"
        hplane.scale = (1.0, 1.0, 1.0) if idx == 0 else (0.0, 0.0, 0.0)
        hmat, _ = create_ricksclips_sprite_material(f"Mat_HUD_{hkey}", sprite_paths[hkey])
        hplane.data.materials.append(hmat)
        hplane.parent = hud_root
        hud_planes[hkey] = hplane

    return cam_obj, hud_root, hud_planes


# ==============================================================================
# 7. ANIMATION HELPERS (CONSTANT CAMERA CUTS, SPRITE SWAPS & YAW ALIGNMENT)
# ==============================================================================
def set_all_keyframes_constant(obj: bpy.types.Object):
    if obj.animation_data and obj.animation_data.action:
        for fcurve in obj.animation_data.action.fcurves:
            for kp in fcurve.keyframe_points:
                kp.interpolation = "CONSTANT"


def key_camera_cut(
    cam_obj: bpy.types.Object,
    f_start: int,
    f_end: int,
    loc_start,
    rot_deg_start,
    loc_end=None,
    rot_deg_end=None,
    lens: float = 38.0,
    focus_dist: float = 3.2,
    interp: str = "BEZIER",
):
    if loc_end is None:
        loc_end = loc_start
    if rot_deg_end is None:
        rot_deg_end = rot_deg_start

    r_start = tuple(math.radians(a) for a in rot_deg_start)
    r_end = tuple(math.radians(a) for a in rot_deg_end)

    for frame, loc, rot in ((f_start, loc_start, r_start), (f_end, loc_end, r_end)):
        cam_obj.location = loc
        cam_obj.rotation_euler = rot
        cam_obj.keyframe_insert(data_path="location", frame=frame)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

        cam_obj.data.lens = lens
        cam_obj.data.dof.focus_distance = focus_dist
        cam_obj.data.keyframe_insert(data_path="lens", frame=frame)
        cam_obj.data.dof.keyframe_insert(data_path="focus_distance", frame=frame)

    for anim_carrier in (cam_obj, cam_obj.data):
        if anim_carrier.animation_data and anim_carrier.animation_data.action:
            for fc in anim_carrier.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    if int(round(kp.co.x)) == f_start:
                        kp.interpolation = interp
                    elif int(round(kp.co.x)) == f_end:
                        kp.interpolation = "CONSTANT"


def apply_sprite_for_frame(scene):
    f = scene.frame_current
    if f < 78:
        y_name = ["you_walk_a.png", "you_walk_b.png", "you_walk_c.png"][((f - 1) // 6) % 3]
    elif f < 225:
        y_name = "you_stand_3q.png"
    elif f < 288:
        y_name = "you_back_hip_rest.png"
    elif f < 345:
        y_name = "you_side_awkward.png"
    else:
        y_name = "you_paranoid_sweat.png"

    if f < 345:
        s_name = "stranger_back_urinal.png"
    elif f < 383:
        s_name = "stranger_side_glance.png"
    else:
        s_name = "stranger_closeup_sweat.png"

    if f < 225:
        h_name = "hud_scene1.png"
    elif f <= 429:
        h_name = "hud_scene2.png"
    elif f <= 660:
        h_name = "hud_scene3.png"
    else:
        h_name = "hud_scene4.png"

    for mat_name, img_name in (
        ("Mat_char_you_Sprite", y_name),
        ("Mat_char_stranger_Sprite", s_name),
        ("Mat_Top_HUD", h_name),
    ):
        mat = bpy.data.materials.get(mat_name)
        img = bpy.data.images.get(img_name)
        if mat and img and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == "TEX_IMAGE":
                    node.image = img


def build_sprite_swap_handler(sprite_paths: dict):
    # Preload all sprite and HUD images into bpy.data.images with STRAIGHT alpha
    for key, path in sprite_paths.items():
        if os.path.exists(path):
            img = bpy.data.images.load(path, check_existing=True)
            img.alpha_mode = "STRAIGHT"
            img.name = key

    bpy.app.handlers.frame_change_pre.clear()
    bpy.app.handlers.frame_change_pre.append(apply_sprite_for_frame)
    apply_sprite_for_frame(bpy.context.scene)

    # Store an auto-registered startup text datablock without multi-line triple quotes
    driver_lines = [
        "import bpy",
        "",
        "def _rc_frame_change(scene):",
        "    f = scene.frame_current",
        "    if f < 78:",
        "        y_name = ['you_walk_a.png', 'you_walk_b.png', 'you_walk_c.png'][((f - 1) // 6) % 3]",
        "    elif f < 225:",
        "        y_name = 'you_stand_3q.png'",
        "    elif f < 288:",
        "        y_name = 'you_back_hip_rest.png'",
        "    elif f < 345:",
        "        y_name = 'you_side_awkward.png'",
        "    else:",
        "        y_name = 'you_paranoid_sweat.png'",
        "    if f < 345:",
        "        s_name = 'stranger_back_urinal.png'",
        "    elif f < 383:",
        "        s_name = 'stranger_side_glance.png'",
        "    else:",
        "        s_name = 'stranger_closeup_sweat.png'",
        "    if f < 225:",
        "        h_name = 'hud_scene1.png'",
        "    elif f <= 429:",
        "        h_name = 'hud_scene2.png'",
        "    elif f <= 660:",
        "        h_name = 'hud_scene3.png'",
        "    else:",
        "        h_name = 'hud_scene4.png'",
        "    for mat_name, img_name in (",
        "        ('Mat_char_you_Sprite', y_name),",
        "        ('Mat_char_stranger_Sprite', s_name),",
        "        ('Mat_Top_HUD', h_name),",
        "    ):",
        "        mat = bpy.data.materials.get(mat_name)",
        "        img = bpy.data.images.get(img_name)",
        "        if mat and img and mat.use_nodes:",
        "            for n in mat.node_tree.nodes:",
        "                if n.type == 'TEX_IMAGE':",
        "                    n.image = img",
        "",
        "bpy.app.handlers.frame_change_pre.clear()",
        "bpy.app.handlers.frame_change_pre.append(_rc_frame_change)",
    ]
    txt = bpy.data.texts.get("rc_sprite_swap_register.py") or bpy.data.texts.new("rc_sprite_swap_register.py")
    txt.clear()
    txt.write("\n".join(driver_lines) + "\n")
    if hasattr(txt, "use_module"):
        txt.use_module = True


# ==============================================================================
# 8. ANIMATE SCENES 1 & 2 (FRAMES 1 TO 429 @ 30 FPS)
# ==============================================================================
def animate_scenes_1_and_2(
    cam_obj: bpy.types.Object,
    hud_plane: bpy.types.Object,
    you_root: bpy.types.Object,
    stranger_root: bpy.types.Object,
    q_cards: list,
):
    # Cut 1A (Frames 1-84 | 0.00s-2.80s): Tracking shot clearly framing char_you walking around partition wall
    key_camera_cut(
        cam_obj,
        f_start=1,
        f_end=83,
        loc_start=(-2.40, -5.20, 1.38),
        rot_deg_start=(84.0, 0.0, -4.0),
        loc_end=(-1.90, -5.20, 1.38),
        rot_deg_end=(84.0, 0.0, 0.0),
        lens=35.0,
        focus_dist=3.35,
        interp="BEZIER",
    )

    # Cut 1B (Frames 84-165 | 2.80s-5.50s): Wide-to-medium push-in revealing 4 urinals & char_stranger at Urinal #4
    key_camera_cut(
        cam_obj,
        f_start=84,
        f_end=164,
        loc_start=(0.35, -2.55, 1.42),
        rot_deg_start=(85.5, 0.0, -14.0),
        loc_end=(1.35, -1.45, 1.38),
        rot_deg_end=(86.0, 0.0, -14.0),
        lens=36.0,
        focus_dist=3.0,
        interp="BEZIER",
    )

    # Cut 1C (Frames 165-225 | 5.50s-7.50s): Pull back (Y=-2.60, lens=26mm) so Urinals #1, #2, #3 & all 3 '?' badges fit cleanly
    key_camera_cut(
        cam_obj,
        f_start=165,
        f_end=224,
        loc_start=(0.35, -2.60, 1.38),
        rot_deg_start=(86.0, 0.0, -4.0),
        loc_end=(-0.70, -2.60, 1.38),
        rot_deg_end=(86.0, 0.0, 0.0),
        lens=26.0,
        focus_dist=3.75,
        interp="BEZIER",
    )

    # Cut 2A (Frames 225-288 | 7.50s-9.60s): Medium rear shot behind char_you stepping to Urinal #1 (X=-2.1)
    key_camera_cut(
        cam_obj,
        f_start=225,
        f_end=287,
        loc_start=(-1.65, -0.95, 1.38),
        rot_deg_start=(85.0, 0.0, 8.0),
        loc_end=(-1.60, -0.75, 1.38),
        rot_deg_end=(85.0, 0.0, 9.0),
        lens=40.0,
        focus_dist=2.25,
        interp="BEZIER",
    )

    # Cut 2B (Frames 288-345 | 9.60s-11.50s): Side-angle depth shot from left of Urinal #1 looking down line to Urinal #4
    key_camera_cut(
        cam_obj,
        f_start=288,
        f_end=344,
        loc_start=(-3.10, 0.65, 1.36),
        rot_deg_start=(86.0, 0.0, -72.0),
        loc_end=(-3.05, 0.68, 1.36),
        rot_deg_end=(86.0, 0.0, -73.0),
        lens=42.0,
        focus_dist=1.25,
        interp="BEZIER",
    )

    # Cut 2C-1 (Frames 345-382 | 11.50s-12.73s): Side-profile medium shot on char_stranger at Urinal #4 glancing left
    key_camera_cut(
        cam_obj,
        f_start=345,
        f_end=382,
        loc_start=(0.90, 0.65, 1.38),
        rot_deg_start=(86.0, 0.0, -60.0),
        loc_end=(0.98, 0.70, 1.38),
        rot_deg_end=(86.0, 0.0, -62.0),
        lens=45.0,
        focus_dist=1.40,
        interp="BEZIER",
    )

    # Cut 2C-2 (Frames 383-429 | 12.77s-14.30s): Clean front close-up on char_stranger's face (52mm lens)
    key_camera_cut(
        cam_obj,
        f_start=383,
        f_end=429,
        loc_start=(2.10, -0.10, 1.42),
        rot_deg_start=(87.5, 0.0, 0.0),
        loc_end=(2.10, -0.02, 1.42),
        rot_deg_end=(87.5, 0.0, 0.0),
        lens=52.0,
        focus_dist=1.40,
        interp="BEZIER",
    )

    # Compensate HUD local position/scale on lens jumps so the top-9% badge stays locked in screen space
    hud_lens_keys = [
        (1, 35.0),
        (83, 35.0),
        (84, 36.0),
        (164, 36.0),
        (165, 26.0),
        (224, 26.0),
        (225, 40.0),
        (287, 40.0),
        (288, 42.0),
        (344, 42.0),
        (345, 45.0),
        (382, 45.0),
        (383, 52.0),
        (429, 52.0),
    ]
    for f, lens_val in hud_lens_keys:
        ratio = 38.0 / lens_val
        hud_plane.location = (0.0, 0.365 * ratio, -0.95)
        hud_plane.scale = (0.48 * ratio, 0.080 * ratio, 1.0)
        hud_plane.keyframe_insert(data_path="location", frame=f)
        hud_plane.keyframe_insert(data_path="scale", frame=f)
    set_all_keyframes_constant(hud_plane)

    # 1. char_you (Protagonist in green #17 jersey — visible walking around partition wall at Frame 40)
    you_keyframes = [
        (1, (-3.10, -2.45, 0.0), (0.0, 0.0, math.radians(-6.0)), "BEZIER"),
        (40, (-1.90, -1.85, 0.0), (0.0, 0.0, math.radians(-6.0)), "BEZIER"),
        (78, (-1.80, -1.15, 0.0), (0.0, 0.0, math.radians(8.0)), "CONSTANT"),
        (224, (-1.80, -1.15, 0.0), (0.0, 0.0, math.radians(8.0)), "CONSTANT"),
        (225, (-2.12, 1.05, 0.0), (0.0, 0.0, math.radians(8.0)), "BEZIER"),
        (238, (-2.10, 1.15, 0.0), (0.0, 0.0, math.radians(9.0)), "CONSTANT"),
        (287, (-2.10, 1.15, 0.0), (0.0, 0.0, math.radians(9.0)), "CONSTANT"),
        (288, (-2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-68.0)), "CONSTANT"),
        (344, (-2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-68.0)), "CONSTANT"),
        (345, (-2.10, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (429, (-2.10, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
    ]
    for f, loc, rot, interp in you_keyframes:
        you_root.location = loc
        you_root.rotation_euler = rot
        you_root.keyframe_insert(data_path="location", frame=f)
        you_root.keyframe_insert(data_path="rotation_euler", frame=f)

    if you_root.animation_data and you_root.animation_data.action:
        key_interp_map = {f: interp for f, _, _, interp in you_keyframes}
        for fc in you_root.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                fr = int(round(kp.co.x))
                if fr in key_interp_map:
                    kp.interpolation = key_interp_map[fr]

    # 2. char_stranger (Soldier at Urinal #4: X = +2.1, Y = 1.15)
    stranger_keyframes = [
        (1, (2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-14.0)), "CONSTANT"),
        (287, (2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-14.0)), "CONSTANT"),
        (288, (2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-70.0)), "CONSTANT"),
        (344, (2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-70.0)), "CONSTANT"),
        (345, (2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-58.0)), "CONSTANT"),
        (382, (2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-58.0)), "CONSTANT"),
        (383, (2.10, 1.15, 0.0), (0.0, 0.0, 0.0), "BEZIER"),
        (390, (2.10, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (429, (2.10, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
    ]
    for f, loc, rot, interp in stranger_keyframes:
        stranger_root.location = loc
        stranger_root.rotation_euler = rot
        stranger_root.keyframe_insert(data_path="location", frame=f)
        stranger_root.keyframe_insert(data_path="rotation_euler", frame=f)

    if stranger_root.animation_data and stranger_root.animation_data.action:
        s_map = {f: interp for f, _, _, interp in stranger_keyframes}
        for fc in stranger_root.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                fr = int(round(kp.co.x))
                if fr in s_map:
                    kp.interpolation = s_map[fr]

    # Question Mark ('?') Pop-up Cards on Cut 1C (Frames 165-225)
    pop_schedule = [
        (q_cards[2], 175),  # Urinal #3 (+0.7)
        (q_cards[1], 190),  # Urinal #2 (-0.7)
        (q_cards[0], 205),  # Urinal #1 (-2.1)
    ]
    for q_obj, f_pop in pop_schedule:
        keys = [
            (1, (0.0, 0.0, 0.0)),
            (f_pop - 1, (0.0, 0.0, 0.0)),
            (f_pop + 5, (0.52, 0.52, 0.52)),
            (f_pop + 9, (0.45, 0.45, 0.45)),
            (224, (0.45, 0.45, 0.45)),
            (225, (0.0, 0.0, 0.0)),
        ]
        for f, sc in keys:
            q_obj.scale = sc
            q_obj.keyframe_insert(data_path="scale", frame=f)


# ==============================================================================
# 9. MAIN BUILD EXECUTION
# ==============================================================================
def main():
    print("[Part 1] Generating RicksClips 2D Stickman Sprites & HUD Badges via PIL...")
    sprite_paths = build_all_sprites()

    print("[Part 1] Initializing Blender 4.2 EEVEE Next Scene & Compositor...")
    clear_scene()
    configure_render_and_compositor()
    setup_world_sky_gradient_and_lighting()

    print("[Part 1] Building 3D Restroom Set, 4 Porcelain Urinals, Wall Signage & Winter Tree...")
    mats, q_cards = build_restroom_set_and_props(sprite_paths)

    print("[Part 1] Creating Multi-Plane Character Pose Rigs & Camera Top-9% HUD...")
    you_pose_keys = [k for k in sprite_paths.keys() if k.startswith("you_")]
    stranger_pose_keys = [k for k in sprite_paths.keys() if k.startswith("stranger_")]
    you_root, you_planes = create_pose_rig("char_you", you_pose_keys, sprite_paths, mats["shadow"])
    stranger_root, stranger_planes = create_pose_rig("char_stranger", stranger_pose_keys, sprite_paths, mats["shadow"])
    cam_obj, hud_plane, hud_planes = create_camera_and_hud(sprite_paths)

    print("[Part 1] Animating Scenes 1 & 2 (Frames 1 to 429) + Multi-Plane Scale Keyframing...")
    animate_scenes_1_and_2(cam_obj, hud_plane, you_root, stranger_root, q_cards)

    # Keyframe Scenes 1 & 2 active poses via Multi-Plane Scale Keyframing
    walk_cycle = ["you_walk_1.png", "you_walk_2.png", "you_walk_3.png", "you_walk_4.png"]
    for f in range(1, 77, 4):
        p = walk_cycle[((f - 1) // 4) % 4]
        key_active_pose(you_planes, p, f, min(f + 3, 76))
    key_active_pose(you_planes, "you_stand_3q.png", 77, 140)
    key_active_pose(you_planes, "you_stand_blink.png", 141, 146)
    key_active_pose(you_planes, "you_stand_3q.png", 147, 224)
    # Cut 2A (225-287): Rear view at Urinal #1 (facing urinal, back to camera!)
    key_active_pose(you_planes, "you_back_idle.png", 225, 246)
    key_active_pose(you_planes, "you_back_hip_rest.png", 247, 287)
    # Cut 2B (288-344): Lively awkward side expressions
    key_active_pose(you_planes, "you_awkward_1.png", 288, 305)
    key_active_pose(you_planes, "you_awkward_2.png", 306, 322)
    key_active_pose(you_planes, "you_awkward_blink.png", 323, 328)
    key_active_pose(you_planes, "you_awkward_1.png", 329, 344)
    key_active_pose(you_planes, "you_paranoid_sweat.png", 345, 429)

    # Soldier Scenes 1 & 2 active poses
    for f in range(1, 345, 24):
        s_p = "stranger_back_idle_1.png" if ((f // 24) % 2 == 0) else "stranger_back_idle_2.png"
        key_active_pose(stranger_planes, s_p, f, min(f + 23, 344))
    # Cut 2C (345-429): Front face close-up with raised helmet (eyes, brows, mouth & sweat 100% visible!)
    key_active_pose(stranger_planes, "stranger_front_nervous_1.png", 345, 382)
    key_active_pose(stranger_planes, "stranger_front_sweat_2.png", 383, 398)
    key_active_pose(stranger_planes, "stranger_front_talk_3.png", 399, 415)
    key_active_pose(stranger_planes, "stranger_front_blink.png", 416, 420)
    key_active_pose(stranger_planes, "stranger_front_sweat_2.png", 421, 429)

    # HUD Badges for Scenes 1 & 2
    key_active_pose(hud_planes, "hud_scene1.png", 1, 224, active_scale=(1.0, 1.0, 1.0))
    key_active_pose(hud_planes, "hud_scene2.png", 225, 429, active_scale=(1.0, 1.0, 1.0))

    bpy.context.scene.frame_set(1)
    try:
        bpy.ops.file.pack_all()
    except Exception:
        pass

    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PART1_PATH)
    print(f"[Part 1] Saved Blender 4.2 project successfully to: {BLEND_PART1_PATH}")


if __name__ == "__main__":
    main()
