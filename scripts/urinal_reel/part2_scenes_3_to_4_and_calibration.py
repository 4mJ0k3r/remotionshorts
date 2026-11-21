#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
# part2_scenes_3_to_4_and_calibration.py
# RicksClips 2.5D Blender 4.2 Studio Architect (Part 2 of 2)
# Target: Blender 4.2 LTS (BLENDER_EEVEE_NEXT) | 1080x1920 @ 30fps | AgX
# Workflow:
#   1. Opens D:/remotionshorts/urinal_dilemma_part1.blend
#   2. Verifies Part 1 rigs/materials/HUD and generates all specialized Scene 3 & 4
#      2.5D parallax, finger-gun, pale-dread terror scream, rear walk, and synchronized
#      urinal dance sprites + updated Scene 3 & 4 HUD badges via PIL.
#   3. Adds PartyLight_Cyan (#00e5ff) and PartyLight_Gold (#ffab00) for Cut 4C.
#   4. Animates Scenes 3 & 4 (Frames 429 to 855: Cuts 3A, 3B, 3C, 4A, 4B, 4C).
#   5. Renders the 12 Calibration Contact Sheet frames at 540x960 (16 EEVEE samples)
#      and stitches them into D:/remotionshorts/renders/urinal_dilemma/sheet_v1.jpg
#   6. Resets resolution to 1080x1920 and saves D:/remotionshorts/urinal_dilemma_full.blend
# ==============================================================================

import os
import sys
import site
user_site = site.getusersitepackages()
if user_site not in sys.path:
    sys.path.append(user_site)
import math
import bpy
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

# ==============================================================================
# 0. PATHS & DIRECTORIES
# ==============================================================================
BASE_DIR = "D:/remotionshorts"
RENDER_DIR = os.path.join(BASE_DIR, "renders/urinal_dilemma")
SPRITE_DIR = os.path.join(RENDER_DIR, "sprites")
HUD_DIR = os.path.join(RENDER_DIR, "hud")
CALIB_DIR = os.path.join(RENDER_DIR, "calib_tiles")

BLEND_PART1_PATH = os.path.join(BASE_DIR, "urinal_dilemma_part1.blend")
BLEND_FULL_PATH = os.path.join(BASE_DIR, "urinal_dilemma_full.blend")
CONTACT_SHEET_PATH = os.path.join(RENDER_DIR, "sheet_v4.jpg")
PREVIEW_MP4_PATH = os.path.join(RENDER_DIR, "urinal_dilemma_preview_v2_540p.mp4")

for _d in (BASE_DIR, RENDER_DIR, SPRITE_DIR, HUD_DIR, CALIB_DIR):
    os.makedirs(_d, exist_ok=True)


# ==============================================================================
# 1. PIL DRAWING & BEZIER HELPERS FOR SCENES 3 & 4 SPRITES
# ==============================================================================
W_CANVAS, H_CANVAS = 1024, 1536
INK = (22, 18, 25, 255)
TRANSPARENT_INK = (22, 18, 25, 0)
CREAM = (253, 250, 242, 255)
DREAD_PALE = (216, 236, 255, 255)  # Pale dread-tinted cream face (#d8ecff) for Cut 3C
SHADOW_COOL = (184, 200, 220, 255)

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


def render_head(
    canvas: Image.Image,
    char_type: str,
    view: str,
    turn_x: float = 0.0,
    expr: str = "neutral",
    head_cx: int = 512,
    head_cy: int = 390,
    head_r: int = 195,
):
    head_fill_img = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
    head_mask = Image.new("L", (W_CANVAS, H_CANVAS), 0)
    d_fill = ImageDraw.Draw(head_fill_img)
    d_mask = ImageDraw.Draw(head_mask)

    base_face_color = DREAD_PALE if expr == "terror_scream" else CREAM
    poly = organic_head_polygon(head_cx, head_cy, head_r, head_r, num_pts=160)
    d_fill.polygon(poly, fill=base_face_color)
    d_mask.polygon(poly, fill=255)

    crescent_mask = Image.new("L", (W_CANVAS, H_CANVAS), 0)
    d_cm = ImageDraw.Draw(crescent_mask)
    d_cm.polygon(poly, fill=255)
    cut_poly = organic_head_polygon(head_cx + 38, head_cy - 34, int(head_r * 0.98), int(head_r * 0.96))
    d_cm.polygon(cut_poly, fill=0)
    crescent_alpha = crescent_mask.point(lambda p: int(p * 0.18))
    head_fill_img.paste((165, 185, 210, 255), (0, 0), crescent_alpha)

    canvas.alpha_composite(head_fill_img)
    draw = ImageDraw.Draw(canvas)

    # Subtle ear contour on 3/4 turns for char_you
    if char_type == "you" and view != "back" and abs(turn_x) > 0.08:
        ear_side = -1 if turn_x > 0 else 1
        ear_x = head_cx + ear_side * int(head_r * 0.96)
        ear_y = head_cy + 18
        ear_box = [ear_x - 26, ear_y - 38, ear_x + 26, ear_y + 38]
        draw.ellipse(ear_box, fill=base_face_color, outline=INK, width=14)
        draw.arc([ear_x - 12, ear_y - 18, ear_x + 12, ear_y + 18], 30, 260, fill=INK, width=6)

    draw_variable_outline(draw, poly, base_w=17, color=INK)

    if view != "back":
        fx = head_cx + int(turn_x * head_r)
        fy = head_cy + 8
        eye_sep = 54 if abs(turn_x) < 0.15 else 48
        lx = fx - eye_sep
        rx = fx + eye_sep
        eye_y = fy - 18

        if char_type == "stranger":
            strap_pts = quad_bezier(
                (head_cx - int(head_r * 0.78), head_cy - 10),
                (fx, head_cy + int(head_r * 0.92)),
                (head_cx + int(head_r * 0.78), head_cy - 10),
                steps=32,
            )
            draw_thick_round_curve(draw, strap_pts, width=10, color=STRAP_BROWN)
            draw_thick_round_curve(draw, strap_pts, width=3, color=INK)

        # Solid #161219 Vertical Oval Eyes (Zero white sclera)
        eye_layer = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
        d_eye = ImageDraw.Draw(eye_layer)

        ew, eh = 19, 32
        if expr in ("terror_scream", "terror_scream_2", "shock_1"):
            ew, eh = 25, 44
        elif expr in ("creepy_unhinged", "creepy_eyebrow_raise", "finger_gun_wink"):
            ew, eh = 22, 38
        elif expr in ("calm_down", "uncomfortable_1", "uncomfortable_2"):
            ew, eh = 18, 28

        d_eye.ellipse([lx - ew, eye_y - eh, lx + ew, eye_y + eh], fill=INK)
        d_eye.ellipse([rx - ew, eye_y - eh, rx + ew, eye_y + eh], fill=INK)

        lid_mask = Image.new("L", (W_CANVAS, H_CANVAS), 255)
        d_lid = ImageDraw.Draw(lid_mask)
        if expr == "blink":
            d_lid.rectangle([0, 0, W_CANVAS, H_CANVAS], fill=0)
            draw.line([(lx - 24, eye_y), (lx + 24, eye_y)], fill=INK, width=12)
            draw.line([(rx - 24, eye_y), (rx + 24, eye_y)], fill=INK, width=12)
        elif expr == "finger_gun_wink":
            d_lid.rectangle([0, 0, fx, H_CANVAS], fill=0)
            draw.arc([lx - 24, eye_y - 12, lx + 24, eye_y + 14], 190, 350, fill=INK, width=12)
        elif expr == "calm_down":
            d_lid.rectangle([0, 0, W_CANVAS, eye_y - 4], fill=0)
            draw.line([(lx - 26, eye_y - 4), (lx + 26, eye_y - 4)], fill=INK, width=11)
            draw.line([(rx - 26, eye_y - 4), (rx + 26, eye_y - 4)], fill=INK, width=11)
        elif expr in ("creepy_smirk", "side_eye"):
            d_lid.rectangle([0, 0, W_CANVAS, eye_y - 10], fill=0)
            d_lid.rectangle([0, eye_y + 18, W_CANVAS, H_CANVAS], fill=0)
            draw.line([(lx - 26, eye_y - 10), (lx + 26, eye_y - 6)], fill=INK, width=10)
            draw.line([(rx - 26, eye_y - 6), (rx + 26, eye_y - 10)], fill=INK, width=10)
        elif expr in ("uncomfortable_1", "uncomfortable_2"):
            d_lid.rectangle([0, 0, W_CANVAS, eye_y - 8], fill=0)
            draw.line([(lx - 26, eye_y - 8), (lx + 26, eye_y - 8)], fill=INK, width=10)
            draw.line([(rx - 26, eye_y - 8), (rx + 26, eye_y - 8)], fill=INK, width=10)

        eye_clipped = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
        eye_clipped.paste(eye_layer, (0, 0), lid_mask)
        canvas.alpha_composite(eye_clipped)

        # Eyebrows
        brow_y = eye_y - eh - 20
        if expr == "creepy_eyebrow_raise":
            draw_thick_round_curve(draw, [(lx - 30, brow_y - 4), (lx, brow_y - 18), (lx + 26, brow_y - 2)], 14, INK)
            draw_thick_round_curve(draw, [(rx - 26, brow_y - 20), (rx, brow_y - 42), (rx + 30, brow_y - 18)], 15, INK)
        elif expr in ("creepy_unhinged", "finger_gun_wink"):
            draw_thick_round_curve(draw, [(lx - 30, brow_y - 8), (lx, brow_y - 26), (lx + 26, brow_y - 6)], 14, INK)
            draw_thick_round_curve(draw, [(rx - 26, brow_y - 6), (rx, brow_y - 28), (rx + 30, brow_y - 8)], 14, INK)
        elif expr in ("terror_scream", "terror_scream_2", "shock_1"):
            draw_thick_round_curve(draw, [(lx - 32, brow_y - 8), (lx + 24, brow_y - 30)], 15, INK)
            draw_thick_round_curve(draw, [(rx - 24, brow_y - 30), (rx + 32, brow_y - 8)], 15, INK)
        elif expr in ("uncomfortable_1", "uncomfortable_2"):
            draw_thick_round_curve(draw, [(lx - 28, brow_y + 8), (lx + 22, brow_y - 10)], 13, INK)
            draw_thick_round_curve(draw, [(rx - 22, brow_y - 10), (rx + 28, brow_y + 8)], 13, INK)
        else:
            draw_thick_round_curve(draw, [(lx - 26, brow_y), (lx + 24, brow_y - 4)], 13, INK)
            draw_thick_round_curve(draw, [(rx - 24, brow_y - 4), (rx + 26, brow_y)], 13, INK)

        # Mouths & Sweat Drops
        mouth_y = fy + 62
        if expr in ("creepy_unhinged", "creepy_smirk", "creepy_eyebrow_raise"):
            widen = 8 if expr == "creepy_eyebrow_raise" else 0
            pts = cubic_bezier(
                (fx - 58 - widen, mouth_y - 14),
                (fx - 16, mouth_y + 38 + widen),
                (fx + 30, mouth_y + 34 + widen),
                (fx + 68 + widen, mouth_y - 26),
                36,
            )
            draw_thick_round_curve(draw, pts, 15, INK)
            draw_thick_round_curve(draw, [(fx + 60 + widen, mouth_y - 36), (fx + 76 + widen, mouth_y - 16)], 10, INK)
        elif expr == "finger_gun_wink":
            draw.chord([fx - 46, mouth_y - 20, fx + 54, mouth_y + 36], 0, 180, fill=(45, 18, 25, 255), outline=INK, width=12)
            draw.chord([fx - 38, mouth_y - 14, fx + 46, mouth_y + 12], 0, 180, fill=WHITE_INK, outline=INK, width=5)
        elif expr == "shock_1":
            draw.ellipse([fx - 26, mouth_y - 10, fx + 26, mouth_y + 32], fill=(45, 15, 22, 255), outline=INK, width=13)
        elif expr in ("terror_scream", "terror_scream_2"):
            jit = 6 if expr == "terror_scream_2" else 0
            m_box = [fx - 46 - jit, mouth_y - 26, fx + 46 + jit, mouth_y + 72 + jit]
            draw.ellipse(m_box, fill=(45, 15, 22, 255), outline=INK, width=15)
            draw.chord([fx - 40, mouth_y - 22, fx + 40, mouth_y + 18], 180, 360, fill=WHITE_INK, outline=INK, width=6)
            draw.chord([fx - 30, mouth_y + 26, fx + 30, mouth_y + 68], 0, 180, fill=(215, 82, 95, 255), outline=INK, width=6)
            sw_shift = 12 if expr == "terror_scream_2" else 0
            for sw_x, sw_y in ((head_cx - int(head_r * 0.62), head_cy - 36 + sw_shift), (head_cx + int(head_r * 0.62), head_cy - 22 + sw_shift)):
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
        elif expr in ("uncomfortable_1", "uncomfortable_2"):
            pts = quad_bezier((fx - 38, mouth_y + 14), (fx, mouth_y - 10), (fx + 38, mouth_y + 16), 24)
            draw_thick_round_curve(draw, pts, 12, INK)
            if expr == "uncomfortable_2":
                sw_x, sw_y = head_cx + int(head_r * 0.56), head_cy - 26
                drop_pts = [(sw_x, sw_y - 28), (sw_x + 16, sw_y + 4), (sw_x, sw_y + 22), (sw_x - 16, sw_y + 4)]
                draw.polygon(drop_pts, fill=SWEAT_CYAN)
                draw_thick_round_curve(draw, drop_pts + [drop_pts[0]], 6, INK)
        else:
            pts = quad_bezier((fx - 28, mouth_y + 4), (fx, mouth_y + 14), (fx + 28, mouth_y + 2), 24)
            draw_thick_round_curve(draw, pts, 12, INK)

    # Soldier Helmet (#5c6346) raised slightly on front views (rim_y = 310) so eyes & brows are 100% clear
    if char_type == "stranger":
        helmet_img = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
        helmet_mask = Image.new("L", (W_CANVAS, H_CANVAS), 0)
        dh = ImageDraw.Draw(helmet_img)
        dm = ImageDraw.Draw(helmet_mask)

        dome_pts = []
        num_dome = 90
        rim_y = 310 if view != "back" else head_cy + 16
        dome_cy = (head_cy - 52) if view != "back" else (head_cy + 4)
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


def render_torso_and_limbs(
    canvas: Image.Image,
    char_type: str,
    view: str,
    pose: str = "stand",
    torso_cx: int = 512,
    torso_top: int = 575,
    torso_bot: int = 930,
    torso_w: int = 165,
):
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
    elif pose == "urinal_stand":
        l_arm_pts = [l_sh, (l_sh[0] - 42, sh_y + 120), (l_sh[0] + 10, sh_y + 225)]
        r_arm_pts = [r_sh, (r_sh[0] + 42, sh_y + 120), (r_sh[0] - 10, sh_y + 225)]
    elif pose == "finger_gun_raise":
        l_arm_pts = [l_sh, (l_sh[0] - 55, sh_y + 115), (l_sh[0] - 20, sh_y + 225)]
        r_arm_pts = [r_sh, (r_sh[0] + 95, sh_y + 65), (r_sh[0] + 195, sh_y + 15)]
    elif pose in ("finger_gun_left", "finger_gun_right", "finger_gun_shoot_1"):
        l_arm_pts = [l_sh, (l_sh[0] - 55, sh_y + 115), (l_sh[0] - 20, sh_y + 225)]
        r_arm_pts = [r_sh, (r_sh[0] + 115, sh_y + 30), (r_sh[0] + 245, sh_y - 25)]
    elif pose == "finger_gun_shoot_2":
        l_arm_pts = [l_sh, (l_sh[0] - 60, sh_y + 110), (l_sh[0] - 25, sh_y + 220)]
        r_arm_pts = [r_sh, (r_sh[0] + 120, sh_y + 10), (r_sh[0] + 255, sh_y - 55)]
    elif pose == "terror_hands":
        l_arm_pts = [l_sh, (l_sh[0] - 120, sh_y - 15), (torso_cx - 180, 425)]
        r_arm_pts = [r_sh, (r_sh[0] + 120, sh_y - 15), (torso_cx + 180, 425)]
        l_leg_pts = [l_hip, (l_hip[0] - 48, hip_y + 175), (l_hip[0] - 32, 1370)]
        r_leg_pts = [r_hip, (r_hip[0] + 48, hip_y + 175), (r_hip[0] + 32, 1370)]
    elif pose == "terror_hands_2":
        l_arm_pts = [l_sh, (l_sh[0] - 145, sh_y - 45), (torso_cx - 215, 375)]
        r_arm_pts = [r_sh, (r_sh[0] + 145, sh_y - 45), (torso_cx + 215, 375)]
        l_leg_pts = [l_hip, (l_hip[0] - 65, hip_y + 165), (l_hip[0] - 48, 1355)]
        r_leg_pts = [r_hip, (r_hip[0] + 65, hip_y + 165), (r_hip[0] + 48, 1355)]
    elif pose == "back_bump":
        l_arm_pts = [l_sh, (l_sh[0] - 65, sh_y + 95), (l_sh[0] - 25, sh_y + 215)]
        r_arm_pts = [r_sh, (r_sh[0] + 105, sh_y + 75), (r_sh[0] + 145, sh_y + 165)]
        l_leg_pts = [l_hip, (l_hip[0] - 35, hip_y + 180), (l_hip[0] - 45, 1375)]
        r_leg_pts = [r_hip, (r_hip[0] + 55, hip_y + 170), (r_hip[0] + 65, 1365)]
    elif pose in ("dance_left", "back_dance_1"):
        l_arm_pts = [l_sh, (l_sh[0] - 135, sh_y - 55), (l_sh[0] - 195, sh_y - 175)]
        r_arm_pts = [r_sh, (r_sh[0] + 100, sh_y + 55), (r_sh[0] + 175, sh_y - 10)]
        l_leg_pts = [l_hip, (l_hip[0] - 95, hip_y + 140), (l_hip[0] - 45, 1340)]
        r_leg_pts = [r_hip, (r_hip[0] + 50, hip_y + 180), (r_hip[0] + 75, 1380)]
    elif pose == "back_dance_2":
        l_arm_pts = [l_sh, (l_sh[0] - 120, sh_y - 85), (l_sh[0] - 165, sh_y - 210)]
        r_arm_pts = [r_sh, (r_sh[0] + 120, sh_y - 85), (r_sh[0] + 165, sh_y - 210)]
        l_leg_pts = [l_hip, (l_hip[0] - 65, hip_y + 150), (l_hip[0] - 25, 1355)]
        r_leg_pts = [r_hip, (r_hip[0] + 65, hip_y + 150), (r_hip[0] + 25, 1355)]
    elif pose in ("dance_right", "back_dance_3"):
        l_arm_pts = [l_sh, (l_sh[0] - 100, sh_y + 55), (l_sh[0] - 175, sh_y - 10)]
        r_arm_pts = [r_sh, (r_sh[0] + 135, sh_y - 55), (r_sh[0] + 195, sh_y - 175)]
        l_leg_pts = [l_hip, (l_hip[0] - 50, hip_y + 180), (l_hip[0] - 75, 1380)]
        r_leg_pts = [r_hip, (r_hip[0] + 95, hip_y + 140), (r_hip[0] + 45, 1340)]
    elif pose == "back_dance_4":
        l_arm_pts = [l_sh, (l_sh[0] - 140, sh_y + 20), (l_sh[0] - 210, sh_y - 65)]
        r_arm_pts = [r_sh, (r_sh[0] + 140, sh_y + 20), (r_sh[0] + 210, sh_y - 65)]
        l_leg_pts = [l_hip, (l_hip[0] - 80, hip_y + 145), (l_hip[0] - 55, 1350)]
        r_leg_pts = [r_hip, (r_hip[0] + 80, hip_y + 145), (r_hip[0] + 55, 1350)]

    for leg in (l_leg_pts, r_leg_pts):
        curve = quad_bezier(leg[0], leg[1], leg[2], steps=36)
        draw_thick_round_curve(draw_main, curve, width=17, color=INK)
        fx_foot, fy_foot = leg[2]
        draw_main.ellipse([fx_foot - 24, fy_foot - 12, fx_foot + 24, fy_foot + 14], fill=INK)

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
            db.line([(torso_cx - 52, torso_top + 10), (torso_cx + 48, 895)], fill=SUSPENDER_BEIGE, width=22)
            db.line([(torso_cx + 52, torso_top + 10), (torso_cx - 48, 895)], fill=SUSPENDER_BEIGE, width=22)
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

    for arm in (l_arm_pts, r_arm_pts):
        curve = quad_bezier(arm[0], arm[1], arm[2], steps=36)
        draw_thick_round_curve(draw_main, curve, width=17, color=INK)
        hx, hy = arm[2]
        draw_main.ellipse([hx - 14, hy - 14, hx + 14, hy + 14], fill=INK)

    if pose in ("finger_gun_left", "finger_gun_right", "finger_gun_raise", "finger_gun_shoot_1", "finger_gun_shoot_2"):
        gx, gy = r_arm_pts[2]
        draw_thick_round_curve(draw_main, [(gx, gy), (gx + 44, gy - 4)], width=12, color=INK)
        draw_thick_round_curve(draw_main, [(gx - 4, gy), (gx + 10, gy - 30)], width=11, color=INK)


def generate_sprite(filename: str, char_type: str, view: str, turn_x: float, expr: str, pose: str, head_cy: int = 390) -> str:
    out_path = os.path.join(SPRITE_DIR, filename)
    canvas = Image.new("RGBA", (W_CANVAS, H_CANVAS), TRANSPARENT_INK)
    render_torso_and_limbs(canvas, char_type=char_type, view=view, pose=pose)
    render_head(canvas, char_type=char_type, view=view, turn_x=turn_x, expr=expr, head_cy=head_cy)
    canvas.save(out_path, "PNG")
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


def ensure_scenes_3_and_4_sprites() -> dict:
    paths = {}

    specs = [
        # Cut 3A: Stranger calm + blink + uncomfortable side-eye; You stepping into Urinal #3
        ("stranger_front_calm.png", "stranger", "front", -0.06, "calm_down", "urinal_stand", 390),
        ("stranger_front_calm_blink.png", "stranger", "front", -0.06, "blink", "urinal_stand", 390),
        ("stranger_front_uncomfortable_1.png", "stranger", "front", -0.18, "uncomfortable_1", "urinal_stand", 390),
        ("stranger_front_uncomfortable_2.png", "stranger", "front", -0.22, "uncomfortable_2", "urinal_stand", 390),
        ("you_front_neutral.png", "you", "front", 0.04, "neutral", "urinal_stand", 390),
        ("you_front_blink.png", "you", "front", 0.04, "blink", "urinal_stand", 390),
        ("you_front_side_eye.png", "you", "front", 0.14, "side_eye", "urinal_stand", 390),
        # Cut 3B: 4-Stage Progressive Creepy Head Turn
        ("you_turn_1.png", "you", "front", 0.08, "neutral", "urinal_stand", 390),
        ("you_turn_2.png", "you", "front", 0.15, "creepy_smirk", "urinal_stand", 390),
        ("you_creepy_smirk_1.png", "you", "three_quarter_r", 0.22, "creepy_unhinged", "urinal_stand", 390),
        ("you_creepy_smirk_eyebrow_raise.png", "you", "three_quarter_r", 0.24, "creepy_eyebrow_raise", "urinal_stand", 388),
        # Cut 3C: Multi-stage Finger-Gun & Terror Scream
        ("you_finger_gun_raise.png", "you", "three_quarter_r", 0.20, "creepy_smirk", "finger_gun_raise", 390),
        ("you_finger_gun_shoot_1.png", "you", "three_quarter_r", 0.22, "finger_gun_wink", "finger_gun_shoot_1", 386),
        ("you_finger_gun_shoot_2.png", "you", "three_quarter_r", 0.22, "creepy_unhinged", "finger_gun_shoot_2", 390),
        ("stranger_shock_1.png", "stranger", "front", -0.16, "shock_1", "urinal_stand", 390),
        ("stranger_scream_1.png", "stranger", "front", -0.16, "terror_scream", "terror_hands", 390),
        ("stranger_scream_2.png", "stranger", "front", -0.18, "terror_scream_2", "terror_hands_2", 384),
        # Cut 4A: 4-Pose Rear Walk Cycle (facing away from camera!)
        ("you_back_walk_1.png", "you", "back", 0.0, "neutral", "walk_a", 390),
        ("you_back_walk_2.png", "you", "back", 0.0, "neutral", "walk_b", 382),
        ("you_back_walk_3.png", "you", "back", 0.0, "neutral", "walk_c", 390),
        ("you_back_walk_4.png", "you", "back", 0.0, "neutral", "walk_b", 384),
        # Cut 4B: Rear Bump & Startled Rear Urinal Poses
        ("you_back_bump.png", "you", "back", 0.0, "neutral", "back_bump", 386),
        ("stranger_back_startled.png", "stranger", "back", 0.0, "neutral", "back_bump", 382),
        # Cut 4C: 4-Pose Synchronized Rear Urinal Dance Finale (facing into Urinal #4!)
        ("you_back_dance_1.png", "you", "back", 0.0, "dance_joy", "back_dance_1", 396),
        ("you_back_dance_2.png", "you", "back", 0.0, "dance_joy", "back_dance_2", 380),
        ("you_back_dance_3.png", "you", "back", 0.0, "dance_joy", "back_dance_3", 396),
        ("you_back_dance_4.png", "you", "back", 0.0, "dance_joy", "back_dance_4", 382),
        ("stranger_back_dance_1.png", "stranger", "back", 0.0, "dance_joy", "back_dance_1", 396),
        ("stranger_back_dance_2.png", "stranger", "back", 0.0, "dance_joy", "back_dance_2", 380),
        ("stranger_back_dance_3.png", "stranger", "back", 0.0, "dance_joy", "back_dance_3", 396),
        ("stranger_back_dance_4.png", "stranger", "back", 0.0, "dance_joy", "back_dance_4", 382),
    ]
    for fname, ctype, view, tx, expr, pose, hcy in specs:
        paths[fname] = generate_sprite(fname, ctype, view, tx, expr, pose, head_cy=hcy)

    # Exact Top-10% English HUD Badges for Scenes 3 & 4
    paths["hud_scene3.png"] = generate_hud_badge(
        "hud_scene3.png",
        "OPTION 2: RIGHT NEXT TO HIM = 100% CREEP",
        accent_color=(248, 113, 113, 255),
    )
    paths["hud_scene4.png"] = generate_hud_badge(
        "hud_scene4.png",
        "THE PRO MOVE: JOIN HIM & START DANCING!",
        accent_color=(74, 222, 128, 255),
    )

    # Also register all existing Part 1 sprites in the dictionary
    for fname in os.listdir(SPRITE_DIR):
        if fname.endswith(".png"):
            paths[fname] = os.path.join(SPRITE_DIR, fname)
    for fname in os.listdir(HUD_DIR):
        if fname.endswith(".png"):
            paths[fname] = os.path.join(HUD_DIR, fname)

    return paths


# ==============================================================================
# 2. PARTY LIGHTS & CAMERA / ANIMATION HELPERS
# ==============================================================================
def create_party_lights():
    # Two interactive colored party point lights for Cut 4C (Frames 780-855):
    # PartyLight_Cyan (#00e5ff) and PartyLight_Gold (#ffab00), 0W before 780, 180W during 780-855
    lights_cfg = [
        ("PartyLight_Cyan", (0.0, 0.898, 1.0), (1.55, 0.85, 1.85)),
        ("PartyLight_Gold", (1.0, 0.671, 0.0), (2.55, 0.85, 1.85)),
    ]
    created = []
    for name, color_rgb, loc in lights_cfg:
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        ldata = bpy.data.lights.new(name=name, type="POINT")
        ldata.color = color_rgb
        ldata.shadow_soft_size = 0.35
        lobj = bpy.data.objects.new(name=name, object_data=ldata)
        bpy.context.scene.collection.objects.link(lobj)
        lobj.location = loc

        # Keyframe energy: 0W before frame 780, pulsing 180W <-> 240W on 6-frame dance beats in 780..855
        ldata.energy = 0.0
        ldata.keyframe_insert(data_path="energy", frame=1)
        ldata.keyframe_insert(data_path="energy", frame=779)

        for f in range(780, 856, 6):
            beat_idx = ((f - 780) // 6) % 2
            if name == "PartyLight_Cyan":
                ldata.energy = 180.0 if beat_idx == 0 else 110.0
            else:
                ldata.energy = 110.0 if beat_idx == 0 else 180.0
            ldata.keyframe_insert(data_path="energy", frame=f)

        created.append(lobj)
    return created


def key_camera_cut(
    cam_obj: bpy.types.Object,
    f_start: int,
    f_end: int,
    loc_start,
    rot_deg_start,
    loc_end=None,
    rot_deg_end=None,
    lens_start: float = 38.0,
    lens_end: float = None,
    focus_dist: float = 3.2,
    interp: str = "BEZIER",
):
    if loc_end is None:
        loc_end = loc_start
    if rot_deg_end is None:
        rot_deg_end = rot_deg_start
    if lens_end is None:
        lens_end = lens_start

    r_start = tuple(math.radians(a) for a in rot_deg_start)
    r_end = tuple(math.radians(a) for a in rot_deg_end)

    for frame, loc, rot, l_val in (
        (f_start, loc_start, r_start, lens_start),
        (f_end, loc_end, r_end, lens_end),
    ):
        cam_obj.location = loc
        cam_obj.rotation_euler = rot
        cam_obj.keyframe_insert(data_path="location", frame=frame)
        cam_obj.keyframe_insert(data_path="rotation_euler", frame=frame)

        cam_obj.data.lens = l_val
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


# ==============================================================================
# 3. ANIMATE SCENES 3 & 4 (FRAMES 429 TO 855 @ 30 FPS)
# ==============================================================================
def animate_scenes_3_and_4(
    cam_obj: bpy.types.Object,
    hud_plane: bpy.types.Object,
    you_root: bpy.types.Object,
    stranger_root: bpy.types.Object,
):
    # Ensure Cut 2C-2 ends at frame 428 so Cut 3A starts cleanly on frame 429
    key_camera_cut(
        cam_obj,
        f_start=383,
        f_end=428,
        loc_start=(1.75, 0.35, 1.48),
        rot_deg_start=(88.0, 0.0, -19.0),
        loc_end=(1.78, 0.42, 1.48),
        rot_deg_end=(88.0, 0.0, -19.0),
        lens_start=65.0,
        focus_dist=1.05,
        interp="BEZIER",
    )

    cam_obj.data.dof.use_dof = False
    cam_obj.data.dof.aperture_fstop = 16.0

    # --------------------------------------------------------------------------
    # CUT 3A (Frames 429-507 | 14.30s-16.90s):
    #   Sub-beat 3A-1 (429-462): Medium-close shot on char_stranger at Urinal #4
    #   Sub-beat 3A-2 (463-506): Whip-pan left to (1.52, -2.10, 1.32), lens=28mm so BOTH
    #   char_you at Urinal #3 (+1.05) and char_stranger at Urinal #4 (+2.00) are side-by-side!
    # --------------------------------------------------------------------------
    key_camera_cut(
        cam_obj,
        f_start=429,
        f_end=462,
        loc_start=(2.00, -0.45, 1.38),
        rot_deg_start=(86.5, 0.0, 0.0),
        loc_end=(1.95, -0.45, 1.38),
        rot_deg_end=(86.5, 0.0, 0.0),
        lens_start=42.0,
        focus_dist=1.60,
        interp="BEZIER",
    )
    # Whip-pan 463 -> 474 to two-shot centered at X=+1.52, Y=-2.10, then CONSTANT hold 474 -> 506
    key_camera_cut(
        cam_obj,
        f_start=463,
        f_end=474,
        loc_start=(1.95, -0.45, 1.38),
        rot_deg_start=(86.5, 0.0, 0.0),
        loc_end=(1.52, -2.10, 1.32),
        rot_deg_end=(88.0, 0.0, 0.0),
        lens_start=38.0,
        lens_end=28.0,
        focus_dist=3.25,
        interp="BEZIER",
    )
    key_camera_cut(
        cam_obj,
        f_start=474,
        f_end=506,
        loc_start=(1.52, -2.10, 1.32),
        rot_deg_start=(88.0, 0.0, 0.0),
        loc_end=(1.52, -2.10, 1.32),
        rot_deg_end=(88.0, 0.0, 0.0),
        lens_start=28.0,
        focus_dist=3.25,
        interp="CONSTANT",
    )

    # --------------------------------------------------------------------------
    # CUT 3B (Frames 507-552 | 16.90s-18.40s):
    #   Tight close-up on char_you at Urinal #3 (lens=68mm)
    # --------------------------------------------------------------------------
    key_camera_cut(
        cam_obj,
        f_start=507,
        f_end=551,
        loc_start=(1.05, 0.15, 1.46),
        rot_deg_start=(88.0, 0.0, 0.0),
        loc_end=(1.05, 0.18, 1.46),
        rot_deg_end=(88.0, 0.0, 0.0),
        lens_start=68.0,
        focus_dist=1.00,
        interp="BEZIER",
    )

    # --------------------------------------------------------------------------
    # CUT 3C (Frames 552-609 | 18.40s-20.30s):
    #   Two-shot at (1.52, -2.10, 1.32), lens=28mm framing BOTH char_you at X=+1.05
    #   (pointing finger-gun right) and char_stranger at X=+2.00 (terror scream).
    # --------------------------------------------------------------------------
    key_camera_cut(
        cam_obj,
        f_start=552,
        f_end=608,
        loc_start=(1.52, -2.10, 1.32),
        rot_deg_start=(88.0, 0.0, 0.0),
        loc_end=(1.52, -2.10, 1.32),
        rot_deg_end=(88.0, 0.0, 0.0),
        lens_start=28.0,
        focus_dist=3.25,
        interp="CONSTANT",
    )

    # --------------------------------------------------------------------------
    # CUT 4A (Frames 609-708 | 20.30s-23.60s):
    #   Wide high-rear tracking shot following behind char_you marching diagonally
    #   past empty Urinals #1, #2, #3 straight toward char_stranger at Urinal #4.
    # --------------------------------------------------------------------------
    key_camera_cut(
        cam_obj,
        f_start=609,
        f_end=707,
        loc_start=(-1.65, -2.55, 1.72),
        rot_deg_start=(79.5, 0.0, -26.0),
        loc_end=(0.65, -1.65, 1.62),
        rot_deg_end=(81.5, 0.0, -22.0),
        lens_start=34.0,
        focus_dist=2.85,
        interp="BEZIER",
    )

    # --------------------------------------------------------------------------
    # CUT 4B (Frames 708-780 | 23.60s-26.00s):
    #   Medium rear two-shot centered on Urinal #4 (X=+2.1) as char_you squeezes in.
    # --------------------------------------------------------------------------
    key_camera_cut(
        cam_obj,
        f_start=708,
        f_end=779,
        loc_start=(2.05, -0.85, 1.40),
        rot_deg_start=(85.0, 0.0, 0.0),
        loc_end=(2.05, -0.78, 1.40),
        rot_deg_end=(85.0, 0.0, 0.0),
        lens_start=42.0,
        focus_dist=2.15,
        interp="BEZIER",
    )

    # --------------------------------------------------------------------------
    # CUT 4C (Frames 780-855 | 26.00s-28.50s):
    #   Energetic medium-rear two-shot at Urinal #4 pushing in slightly (lens 42->48mm)
    # --------------------------------------------------------------------------
    key_camera_cut(
        cam_obj,
        f_start=780,
        f_end=855,
        loc_start=(2.05, -0.78, 1.40),
        rot_deg_start=(85.0, 0.0, 0.0),
        loc_end=(2.05, -0.62, 1.40),
        rot_deg_end=(85.0, 0.0, 0.0),
        lens_start=42.0,
        lens_end=48.0,
        focus_dist=2.00,
        interp="BEZIER",
    )

    # Update HUD plane lens compensation across the entire 1..855 timeline
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
        (383, 65.0),
        (428, 65.0),
        (429, 42.0),
        (462, 42.0),
        (463, 28.0),
        (506, 28.0),
        (507, 68.0),
        (551, 68.0),
        (552, 28.0),
        (608, 28.0),
        (609, 34.0),
        (707, 34.0),
        (708, 42.0),
        (779, 42.0),
        (780, 42.0),
        (855, 48.0),
    ]
    for f, lens_val in hud_lens_keys:
        ratio = 38.0 / lens_val
        hud_plane.location = (0.0, 0.365 * ratio, -0.95)
        hud_plane.scale = (0.48 * ratio, 0.080 * ratio, 1.0)
        hud_plane.keyframe_insert(data_path="location", frame=f)
        hud_plane.keyframe_insert(data_path="scale", frame=f)

    if hud_plane.animation_data and hud_plane.animation_data.action:
        for fc in hud_plane.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"

    # --------------------------------------------------------------------------
    # CHARACTER TRAJECTORIES & BILLBOARD ROTATIONS FOR SCENES 3 & 4 (429..855)
    # --------------------------------------------------------------------------
    # 1. char_you
    you_s3_s4_keys = [
        # Hold end of Scene 2 up to 428
        (428, (-2.10, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        # Cut 3A: Steps into Urinal #3 (X=+1.05, Y=1.15) right beside char_stranger (X=+2.00)
        (429, (0.85, 1.10, 0.0), (0.0, 0.0, 0.0), "BEZIER"),
        (463, (0.98, 1.15, 0.0), (0.0, 0.0, 0.0), "BEZIER"),
        (474, (1.05, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (506, (1.05, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        # Cut 3B: Close-up at Urinal #3 facing camera squarely
        (507, (1.05, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (551, (1.05, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        # Cut 3C: Framed cleanly on left (X=+1.05, Y=1.15) pointing finger-gun right at char_stranger (X=+2.00)
        (552, (1.05, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (608, (1.05, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        # Cut 4A: Marches diagonally from (-1.8, -0.5) past empty Urinals #1-#3 straight toward Urinal #4
        (609, (-1.80, -0.50, 0.0), (0.0, 0.0, math.radians(-24.0)), "BEZIER"),
        (658, (0.05, 0.42, 0.0), (0.0, 0.0, math.radians(-23.0)), "BEZIER"),
        (702, (1.75, 1.15, 0.0), (0.0, 0.0, math.radians(-22.0)), "CONSTANT"),
        (707, (1.75, 1.15, 0.0), (0.0, 0.0, math.radians(-22.0)), "CONSTANT"),
        # Cut 4B: Steps into Urinal #4 (X=+1.88) & gives playful shoulder/hip bump (725-742 overshoot to +1.96)
        (708, (1.72, 1.15, 0.0), (0.0, 0.0, 0.0), "BEZIER"),
        (724, (1.84, 1.15, 0.0), (0.0, 0.0, 0.0), "BEZIER"),
        (731, (1.96, 1.15, 0.0), (0.0, 0.0, math.radians(-4.0)), "BEZIER"),
        (742, (1.88, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (779, (1.88, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
    ]

    # Cut 4C (780-855): Synchronized 6-frame lateral hip sway (±0.07m) + vertical bounce (+0.05m) at Urinal #4
    for f in range(780, 856, 3):
        step = (f - 780) // 3
        sway_x = -0.07 if (step % 4 in (0, 1)) else 0.07
        bounce_z = 0.05 if (step % 2 == 1) else 0.0
        tilt_z = math.radians(4.0) if sway_x < 0 else math.radians(-4.0)
        you_s3_s4_keys.append((f, (1.86 + sway_x, 1.15, bounce_z), (0.0, 0.0, tilt_z), "BEZIER"))

    for f, loc, rot, _interp in you_s3_s4_keys:
        you_root.location = loc
        you_root.rotation_euler = rot
        you_root.keyframe_insert(data_path="location", frame=f)
        you_root.keyframe_insert(data_path="rotation_euler", frame=f)

    if you_root.animation_data and you_root.animation_data.action:
        y_map = {f: interp for f, _, _, interp in you_s3_s4_keys}
        for fc in you_root.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                fr = int(round(kp.co.x))
                if fr in y_map:
                    kp.interpolation = y_map[fr]

    # 2. char_stranger
    stranger_s3_s4_keys = [
        (428, (2.12, 1.15, 0.0), (0.0, 0.0, math.radians(-19.0)), "CONSTANT"),
        # Cut 3A: Standing at Urinal #4 (+2.00, 1.15) facing camera alongside char_you
        (429, (2.00, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (551, (2.00, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        # Cut 3C: Recoils in jaw-drop horror at Urinal #4 (X=+2.00, Y=1.15) facing camera
        (552, (2.00, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (564, (2.00, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (608, (2.00, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        # Cut 4A: Standing at Urinal #4
        (609, (2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-22.0)), "CONSTANT"),
        (707, (2.10, 1.15, 0.0), (0.0, 0.0, math.radians(-22.0)), "CONSTANT"),
        # Cut 4B: Nudged from X=+2.10 to +2.26 at frames 725-742, settling at +2.24
        (708, (2.10, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (725, (2.10, 1.15, 0.0), (0.0, 0.0, 0.0), "BEZIER"),
        (733, (2.28, 1.15, 0.0), (0.0, 0.0, math.radians(5.0)), "BEZIER"),
        (742, (2.24, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
        (779, (2.24, 1.15, 0.0), (0.0, 0.0, 0.0), "CONSTANT"),
    ]

    # Cut 4C (780-855): Synchronized 6-frame lateral hip sway (±0.07m) + vertical bounce (+0.05m) with char_you
    for f in range(780, 856, 3):
        step = (f - 780) // 3
        sway_x = -0.07 if (step % 4 in (0, 1)) else 0.07
        bounce_z = 0.05 if (step % 2 == 1) else 0.0
        tilt_z = math.radians(4.0) if sway_x < 0 else math.radians(-4.0)
        stranger_s3_s4_keys.append((f, (2.26 + sway_x, 1.15, bounce_z), (0.0, 0.0, tilt_z), "BEZIER"))

    for f, loc, rot, _interp in stranger_s3_s4_keys:
        stranger_root.location = loc
        stranger_root.rotation_euler = rot
        stranger_root.keyframe_insert(data_path="location", frame=f)
        stranger_root.keyframe_insert(data_path="rotation_euler", frame=f)

    if stranger_root.animation_data and stranger_root.animation_data.action:
        s_map = {f: interp for f, _, _, interp in stranger_s3_s4_keys}
        for fc in stranger_root.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                fr = int(round(kp.co.x))
                if fr in s_map:
                    kp.interpolation = s_map[fr]


# ==============================================================================
# 4. MULTI-PLANE SCALE KEYFRAMING ENGINE (100% VIDEO-SAFE ACROSS FRAMES 1..855)
# ==============================================================================
def build_sprite_mat(mat_name: str, img_path: str):
    mat = bpy.data.materials.get(mat_name) or bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    elif hasattr(mat, "blend_method"):
        mat.blend_method = "BLEND"

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    n_out = nodes.new("ShaderNodeOutputMaterial")
    n_mix_alpha = nodes.new("ShaderNodeMixShader")
    n_transp = nodes.new("ShaderNodeBsdfTransparent")

    n_mix_cel = nodes.new("ShaderNodeMixShader")
    n_mix_cel.inputs["Fac"].default_value = 0.05

    n_emis = nodes.new("ShaderNodeEmission")
    n_emis.inputs["Strength"].default_value = 1.10

    n_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    n_bsdf.inputs["Roughness"].default_value = 0.85

    n_tex = nodes.new("ShaderNodeTexImage")
    n_tex.extension = "CLIP"
    n_tex.interpolation = "Linear"
    if os.path.exists(img_path):
        img = bpy.data.images.load(img_path, check_existing=True)
        img.reload()
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
    return mat


def ensure_multi_plane_rig(root_obj: bpy.types.Object, prefix: str, sprite_paths: dict, is_hud: bool = False) -> dict:
    # Remove any legacy single-sprite mesh child or old pose planes so we have a clean multi-plane rig
    for child in list(root_obj.children):
        if "ShadowDisc" in child.name:
            continue
        bpy.data.objects.remove(child, do_unlink=True)

    # If root_obj itself was a mesh plane (e.g. legacy Camera_Top_HUD), clear its materials so only child planes render
    if root_obj.type == "MESH":
        root_obj.data.materials.clear()

    planes = {}
    keys = [k for k in sorted(sprite_paths.keys()) if k.startswith(prefix)]
    for pkey in keys:
        path = sprite_paths[pkey]
        if not os.path.exists(path):
            continue
        if is_hud:
            bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
        else:
            bpy.ops.mesh.primitive_plane_add(
                size=1.0,
                location=(0.0, 0.0, 0.87),
                rotation=(math.radians(90), 0.0, 0.0),
            )
        p_obj = bpy.context.view_layer.objects.active
        p_obj.name = f"{root_obj.name}_Pose_{pkey}"
        p_obj.scale = (0.0, 0.0, 0.0)
        mat = build_sprite_mat(f"Mat_{root_obj.name}_{pkey}", path)
        p_obj.data.materials.append(mat)
        p_obj.parent = root_obj
        planes[pkey] = p_obj

    return planes


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


def finalize_constant_pose_fcurves(pose_planes: dict):
    for plane_obj in pose_planes.values():
        if plane_obj.animation_data and plane_obj.animation_data.action:
            for fc in plane_obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def apply_full_sprite_for_frame(scene):
    # No-op compatibility shim: Multi-Plane Scale Keyframing is natively evaluated by Blender's depsgraph
    pass


def keyframe_all_multi_plane_poses(
    you_root: bpy.types.Object,
    stranger_root: bpy.types.Object,
    hud_plane: bpy.types.Object,
    sprite_paths: dict,
):
    # Remove any leftover 3D wall text objects from Part 1 if present
    for legacy_txt in ("Sign_Public_Ext", "Sign_KCraft3D_Int"):
        obj = bpy.data.objects.get(legacy_txt)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)

    you_planes = ensure_multi_plane_rig(you_root, "you_", sprite_paths, is_hud=False)
    stranger_planes = ensure_multi_plane_rig(stranger_root, "stranger_", sprite_paths, is_hud=False)
    hud_planes = ensure_multi_plane_rig(hud_plane, "hud_", sprite_paths, is_hud=True)

    # --------------------------------------------------------------------------
    # 1. PROTAGONIST (`char_you`) MULTI-PLANE SCALE KEYFRAMES (FRAMES 1..855)
    # --------------------------------------------------------------------------
    # Cut 1A (1-76): 4-pose front-3/4 walk-in with whistling/talking/blinking
    walk_in = ["you_walk_1.png", "you_walk_2.png", "you_walk_3.png", "you_walk_4.png"]
    for f in range(1, 77, 4):
        p = walk_in[((f - 1) // 4) % 4]
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
    key_active_pose(you_planes, "you_paranoid_sweat.png", 345, 428)

    # Cut 3A (429-506): Walks into Urinal #3 (460-474) and stands right beside soldier
    key_active_pose(you_planes, "you_front_neutral.png", 429, 459)
    for f in range(460, 474, 4):
        p = walk_in[((f - 460) // 4) % 4]
        key_active_pose(you_planes, p, f, min(f + 3, 473))
    key_active_pose(you_planes, "you_front_neutral.png", 474, 488)
    key_active_pose(you_planes, "you_front_blink.png", 489, 493)
    key_active_pose(you_planes, "you_front_side_eye.png", 494, 506)

    # Cut 3B (507-551): 4-Stage Progressive Creepy Head Turn
    key_active_pose(you_planes, "you_turn_1.png", 507, 517)
    key_active_pose(you_planes, "you_turn_2.png", 518, 527)
    key_active_pose(you_planes, "you_creepy_smirk_1.png", 528, 539)
    key_active_pose(you_planes, "you_creepy_smirk_eyebrow_raise.png", 540, 551)

    # Cut 3C (552-608): Finger-Gun Raise & Double Shoot
    key_active_pose(you_planes, "you_finger_gun_raise.png", 552, 561)
    key_active_pose(you_planes, "you_finger_gun_shoot_1.png", 562, 574)
    key_active_pose(you_planes, "you_finger_gun_shoot_2.png", 575, 589)
    key_active_pose(you_planes, "you_finger_gun_shoot_1.png", 590, 608)

    # Cut 4A (609-707): 4-Pose REAR WALK CYCLE toward Urinal #4 (swapping every 4 frames!)
    rear_walk = ["you_back_walk_1.png", "you_back_walk_2.png", "you_back_walk_3.png", "you_back_walk_4.png"]
    for f in range(609, 703, 4):
        p = rear_walk[((f - 609) // 4) % 4]
        key_active_pose(you_planes, p, f, min(f + 3, 702))
    key_active_pose(you_planes, "you_back_idle.png", 703, 707)

    # Cut 4B (708-779): Rear View Squeezing into Urinal #4 & Hip/Shoulder Bump
    key_active_pose(you_planes, "you_back_idle.png", 708, 724)
    key_active_pose(you_planes, "you_back_bump.png", 725, 742)
    key_active_pose(you_planes, "you_back_hip_rest.png", 743, 779)

    # Cut 4C (780-855): 4-Pose Synchronized REAR URINAL DANCE Finale (swapping every 4 frames!)
    you_dance = ["you_back_dance_1.png", "you_back_dance_2.png", "you_back_dance_3.png", "you_back_dance_4.png"]
    for f in range(780, 856, 4):
        p = you_dance[((f - 780) // 4) % 4]
        key_active_pose(you_planes, p, f, min(f + 3, 855))

    # --------------------------------------------------------------------------
    # 2. SOLDIER (`char_stranger`) MULTI-PLANE SCALE KEYFRAMES (FRAMES 1..855)
    # --------------------------------------------------------------------------
    # Cuts 1A-2B (1-344): Rear view at Urinal #4 with subtle idle shifts
    for f in range(1, 345, 24):
        s_p = "stranger_back_idle_1.png" if ((f // 24) % 2 == 0) else "stranger_back_idle_2.png"
        key_active_pose(stranger_planes, s_p, f, min(f + 23, 344))

    # Cut 2C (345-428): Front face close-up with raised helmet (eyes, brows, mouth & sweat 100% visible!)
    key_active_pose(stranger_planes, "stranger_front_nervous_1.png", 345, 382)
    key_active_pose(stranger_planes, "stranger_front_sweat_2.png", 383, 398)
    key_active_pose(stranger_planes, "stranger_front_talk_3.png", 399, 415)
    key_active_pose(stranger_planes, "stranger_front_blink.png", 416, 420)
    key_active_pose(stranger_planes, "stranger_front_sweat_2.png", 421, 428)

    # Cut 3A & 3B (429-551): Calm -> Blink -> Uncomfortable side-eye as char_you invades Urinal #3
    key_active_pose(stranger_planes, "stranger_front_calm.png", 429, 452)
    key_active_pose(stranger_planes, "stranger_front_calm_blink.png", 453, 458)
    key_active_pose(stranger_planes, "stranger_front_calm.png", 459, 473)
    key_active_pose(stranger_planes, "stranger_front_uncomfortable_1.png", 474, 492)
    key_active_pose(stranger_planes, "stranger_front_uncomfortable_2.png", 493, 551)

    # Cut 3C (552-608): Shock -> Wide-open Terror Scream 1 & 2 (trembling scream + waving arms!)
    key_active_pose(stranger_planes, "stranger_shock_1.png", 552, 563)
    key_active_pose(stranger_planes, "stranger_scream_1.png", 564, 575)
    key_active_pose(stranger_planes, "stranger_scream_2.png", 576, 591)
    key_active_pose(stranger_planes, "stranger_scream_1.png", 592, 608)

    # Cut 4A (609-707): Rear view at Urinal #4
    for f in range(609, 708, 24):
        s_p = "stranger_back_idle_1.png" if ((f // 24) % 2 == 0) else "stranger_back_idle_2.png"
        key_active_pose(stranger_planes, s_p, f, min(f + 23, 707))

    # Cut 4B (708-779): Rear view nudged at Urinal #4
    key_active_pose(stranger_planes, "stranger_back_idle_1.png", 708, 724)
    key_active_pose(stranger_planes, "stranger_back_startled.png", 725, 744)
    key_active_pose(stranger_planes, "stranger_back_idle_2.png", 745, 779)

    # Cut 4C (780-855): 4-Pose Synchronized REAR URINAL DANCE Finale (swapping every 4 frames!)
    stranger_dance = [
        "stranger_back_dance_1.png",
        "stranger_back_dance_2.png",
        "stranger_back_dance_3.png",
        "stranger_back_dance_4.png",
    ]
    for f in range(780, 856, 4):
        p = stranger_dance[((f - 780) // 4) % 4]
        key_active_pose(stranger_planes, p, f, min(f + 3, 855))

    # --------------------------------------------------------------------------
    # 3. TOP HUD (`Camera_Top_HUD`) MULTI-PLANE SCALE KEYFRAMES (FRAMES 1..855)
    # --------------------------------------------------------------------------
    key_active_pose(hud_planes, "hud_scene1.png", 1, 224, active_scale=(1.0, 1.0, 1.0))
    key_active_pose(hud_planes, "hud_scene2.png", 225, 428, active_scale=(1.0, 1.0, 1.0))
    key_active_pose(hud_planes, "hud_scene3.png", 429, 608, active_scale=(1.0, 1.0, 1.0))
    key_active_pose(hud_planes, "hud_scene4.png", 609, 855, active_scale=(1.0, 1.0, 1.0))

    finalize_constant_pose_fcurves(you_planes)
    finalize_constant_pose_fcurves(stranger_planes)
    finalize_constant_pose_fcurves(hud_planes)


# ==============================================================================
# 5. RENDER 12-TILE CALIBRATION CONTACT SHEET (sheet_v1.jpg @ 2160x2880)
# ==============================================================================
def render_calibration_contact_sheet():
    scene = bpy.context.scene
    scene.render.resolution_x = 540
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    if hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = 16

    calibration_shots = [
        (40, "CUT 1A | Frame 40 (1.3s)"),
        (125, "CUT 1B | Frame 125 (4.2s)"),
        (205, "CUT 1C | Frame 205 (6.8s)"),
        (255, "CUT 2A | Frame 255 (8.5s)"),
        (315, "CUT 2B | Frame 315 (10.5s)"),
        (405, "CUT 2C | Frame 405 (13.5s)"),
        (485, "CUT 3A | Frame 485 (16.2s)"),
        (535, "CUT 3B | Frame 535 (17.8s)"),
        (580, "CUT 3C | Frame 580 (19.3s)"),
        (660, "CUT 4A | Frame 660 (22.0s)"),
        (745, "CUT 4B | Frame 745 (24.8s)"),
        (820, "CUT 4C | Frame 820 (27.3s)"),
    ]

    tile_w, tile_h = 540, 960
    cols, rows = 4, 3
    sheet_img = Image.new("RGB", (cols * tile_w, rows * tile_h), (14, 16, 22))
    font_label = load_font(22, bold=True)

    for idx, (frame_num, label_text) in enumerate(calibration_shots):
        scene.frame_set(frame_num)
        apply_full_sprite_for_frame(scene)

        tile_path = os.path.join(CALIB_DIR, f"tile_{idx + 1:02d}_f{frame_num:03d}.png")
        scene.render.filepath = tile_path
        print(f"[Part 2] Rendering calibration tile {idx + 1}/12: {label_text} -> {tile_path}")
        bpy.ops.render.render(write_still=True)

        if os.path.exists(tile_path):
            tile_im = Image.open(tile_path).convert("RGBA")
            if tile_im.size != (tile_w, tile_h):
                tile_im = tile_im.resize((tile_w, tile_h), Image.Resampling.LANCZOS)

            # Draw dark top label bar on each tile
            overlay = Image.new("RGBA", (tile_w, tile_h), (0, 0, 0, 0))
            d_ov = ImageDraw.Draw(overlay)
            d_ov.rectangle([0, 0, tile_w, 42], fill=(12, 15, 22, 215))
            d_ov.line([(0, 42), (tile_w, 42)], fill=(255, 214, 10, 255), width=2)
            d_ov.text((tile_w // 2, 21), label_text, fill=(255, 255, 255, 255), font=font_label, anchor="mm")

            tile_merged = Image.alpha_composite(tile_im, overlay).convert("RGB")
            col = idx % cols
            row = idx // cols
            sheet_img.paste(tile_merged, (col * tile_w, row * tile_h))

    sheet_img.save(CONTACT_SHEET_PATH, "JPEG", quality=94)
    print(f"[Part 2] Saved 4x3 Calibration Contact Sheet (2160x2880) to: {CONTACT_SHEET_PATH}")

    # Reset render resolution to full 1080x1920
    scene.render.resolution_x = 1080
    scene.render.resolution_y = 1920
    scene.render.resolution_percentage = 100


# ==============================================================================
# 6. MAIN EXECUTION
# ==============================================================================
def main():
    print(f"[Part 2] Opening Part 1 Blend file: {BLEND_PART1_PATH}")
    if not os.path.exists(BLEND_PART1_PATH):
        raise FileNotFoundError(f"Part 1 blend file not found at {BLEND_PART1_PATH}. Run Part 1 first.")
    bpy.ops.wm.open_mainfile(filepath=BLEND_PART1_PATH)

    print("[Part 2] Generating & verifying Scenes 3 & 4 sprites and HUD badges...")
    sprite_paths = ensure_scenes_3_and_4_sprites()

    # Verify required objects from Part 1
    cam_obj = bpy.data.objects.get("Main_Camera")
    hud_plane = bpy.data.objects.get("Camera_Top_HUD")
    you_root = bpy.data.objects.get("char_you_Root")
    stranger_root = bpy.data.objects.get("char_stranger_Root")

    if not all([cam_obj, hud_plane, you_root, stranger_root]):
        raise RuntimeError("Missing required Part 1 rig objects (Main_Camera, Camera_Top_HUD, char_you_Root, char_stranger_Root).")

    print("[Part 2] Creating Cut 4C interactive party point lights (PartyLight_Cyan & PartyLight_Gold)...")
    create_party_lights()

    print("[Part 2] Animating Scenes 3 & 4 (Frames 429 to 855) & Multi-Plane Scale Keyframing...")
    animate_scenes_3_and_4(cam_obj, hud_plane, you_root, stranger_root)
    keyframe_all_multi_plane_poses(you_root, stranger_root, hud_plane, sprite_paths)

    # Ensure Compositor has +22% Saturation boost
    scene = bpy.context.scene
    if scene.use_nodes and scene.node_tree:
        tree = scene.node_tree
        has_huesat = any(n.type == "HUE_SAT" for n in tree.nodes)
        if not has_huesat:
            n_glare = next((n for n in tree.nodes if n.type == "GLARE"), None)
            n_comp = next((n for n in tree.nodes if n.type == "COMPOSITE"), None)
            if n_glare and n_comp:
                n_huesat = tree.nodes.new("CompositorNodeHueSat")
                n_huesat.location = (120, 0)
                n_huesat.inputs["Hue"].default_value = 0.5
                n_huesat.inputs["Saturation"].default_value = 1.22
                n_huesat.inputs["Value"].default_value = 1.06
                tree.links.new(n_glare.outputs["Image"], n_huesat.inputs["Image"])
                tree.links.new(n_huesat.outputs["Image"], n_comp.inputs["Image"])

    # Save full blend before rendering contact sheet
    try:
        bpy.ops.file.pack_all()
    except Exception:
        pass
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_FULL_PATH)

    print("[Part 2] Rendering 12-tile Calibration Contact Sheet (sheet_v4.jpg at 540x960 per tile)...")
    render_calibration_contact_sheet()

    # Reset frame to 1, full 1080x1920 resolution, and save final urinal_dilemma_full.blend
    bpy.context.scene.frame_set(1)
    apply_full_sprite_for_frame(bpy.context.scene)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_FULL_PATH)
    print(f"[Part 2] Saved complete 855-frame Blender 4.2 project to: {BLEND_FULL_PATH}")


if __name__ == "__main__":
    main()
