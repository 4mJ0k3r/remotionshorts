"""Deterministic 2x-supersampled comic face expression & viseme generator for Mascot.

Generates 12 story expressions in `assets/mascot/expressions/<name>.png` and
6 speech visemes in `assets/mascot/expressions/visemes/<name>.png`.

All artwork is authored in physical 3D head-front meters `(x_m, z_m)` mapped
onto the conformed face decal domain `x in [-0.19, +0.19]`, `z in [-0.19, +0.07]`,
rendered in premultiplied float32 at 2048x2048, downsampled via LANCZOS to
1024x1024 RGBA, and unpremultiplied-RGB edge-dilated across transparent texels
so zero white or dark alpha halos appear under hardware bilinear filtering.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------------------------------------------------------------------------
# Public UV / Layout & Naming Contract (shared with build_mascot_asset / API)
# ---------------------------------------------------------------------------

EXPRESSIONS: tuple[str, ...] = (
    "idle_cute",
    "curious_o",
    "chill_laugh",
    "hype_letsgo",
    "cringe_teeth",
    "whatever_eyeroll",
    "phone_zombie",
    "sulk_pout",
    "mortified_blush",
    "smug_wink",
    "crush_hearts",
    "ugh_groan",
)

VISEMES: tuple[str, ...] = (
    "vis_closed",
    "vis_AA",
    "vis_EE",
    "vis_OH",
    "vis_OO",
    "vis_FV",
)

# Physical head & conformed face decal bounds (meters, head-local, -Y forward)
HEAD_RADII: tuple[float, float, float] = (0.220, 0.200, 0.224)
DECAL_X_RANGE: tuple[float, float] = (-0.19, 0.19)
DECAL_Z_RANGE: tuple[float, float] = (-0.19, 0.07)
DECAL_HALF: tuple[float, float] = (
    0.5 * (DECAL_X_RANGE[1] - DECAL_X_RANGE[0]),
    0.5 * (DECAL_Z_RANGE[1] - DECAL_Z_RANGE[0]),
)
DECAL_CENTER_Z: float = 0.5 * (DECAL_Z_RANGE[0] + DECAL_Z_RANGE[1])

SUPERSAMPLE_RES: int = 2048
FINAL_RES: int = 1024

# Core comic palette
INK = "#141016"
WHITE = "#FFFDFB"
MOUTH_DARK = "#4A121B"
MOUTH_DEEP = "#2D0910"
TONGUE_PINK = "#FF7B89"
SWEAT_CYAN = "#5CE1FF"
SWEAT_SHINE = "#D6F8FF"
DROOL_CYAN = "#BCEEFF"
HEART_PINK = "#FF4785"
HEART_SHINE = "#FFC4D8"
BLUSH_PINK = "#FF85A2"
FLUSH_RED = "#FF5468"


def _hex_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


# ---------------------------------------------------------------------------
# Premultiplied 2x-Supersampled Physical-Meter Canvas
# ---------------------------------------------------------------------------


class FaceCanvas:
    """2048x2048 premultiplied RGBA compositor parameterized in head meters."""

    def __init__(self, size: int = SUPERSAMPLE_RES) -> None:
        self.size = size
        self.premul = np.zeros((size, size, 4), dtype=np.float32)

    def m_to_px(self, x_m: float, z_m: float) -> tuple[float, float]:
        u = (x_m - DECAL_X_RANGE[0]) / (DECAL_X_RANGE[1] - DECAL_X_RANGE[0])
        v = (z_m - DECAL_Z_RANGE[0]) / (DECAL_Z_RANGE[1] - DECAL_Z_RANGE[0])
        return (u * self.size, (1.0 - v) * self.size)

    def pts_to_px(self, pts_m: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
        return [self.m_to_px(x, z) for x, z in pts_m]

    def _over_mask(self, mask_img: Image.Image, color: str, opacity: float = 1.0) -> None:
        alpha = (np.asarray(mask_img, dtype=np.float32) / 255.0) * float(opacity)
        if alpha.max() <= 0.0:
            return
        r, g, b = _hex_rgb(color)
        rgb = np.array([r / 255.0, g / 255.0, b / 255.0], dtype=np.float32)
        inv = 1.0 - alpha[..., None]
        self.premul[..., :3] = alpha[..., None] * rgb + self.premul[..., :3] * inv
        self.premul[..., 3] = alpha + self.premul[..., 3] * inv[..., 0]

    def _over_rgba_arrays(self, rgb01: np.ndarray, alpha01: np.ndarray) -> None:
        a = np.clip(alpha01, 0.0, 1.0).astype(np.float32)
        if a.max() <= 0.0:
            return
        inv = 1.0 - a[..., None]
        self.premul[..., :3] = (
            a[..., None] * np.clip(rgb01, 0.0, 1.0).astype(np.float32)
            + self.premul[..., :3] * inv
        )
        self.premul[..., 3] = a + self.premul[..., 3] * inv[..., 0]

    def new_mask(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        img = Image.new("L", (self.size, self.size), 0)
        return img, ImageDraw.Draw(img)

    def fill_poly(
        self,
        pts_m: Sequence[tuple[float, float]],
        color: str,
        opacity: float = 1.0,
        clip_mask: Image.Image | None = None,
    ) -> Image.Image:
        mask, draw = self.new_mask()
        if len(pts_m) >= 3:
            draw.polygon(self.pts_to_px(pts_m), fill=255)
        if clip_mask is not None:
            mask = Image.fromarray(
                np.minimum(np.asarray(mask), np.asarray(clip_mask)), mode="L"
            )
        self._over_mask(mask, color, opacity=opacity)
        return mask

    @staticmethod
    def ellipse_poly(
        cx: float,
        cz: float,
        rx: float,
        rz: float,
        deg: float = 0.0,
        n: int = 96,
    ) -> list[tuple[float, float]]:
        rad = math.radians(deg)
        ca, sa = math.cos(rad), math.sin(rad)
        pts: list[tuple[float, float]] = []
        for i in range(n):
            t = math.tau * i / n
            ux, uz = rx * math.cos(t), rz * math.sin(t)
            pts.append((cx + ux * ca - uz * sa, cz + ux * sa + uz * ca))
        return pts

    def fill_ellipse(
        self,
        cx: float,
        cz: float,
        rx: float,
        rz: float,
        color: str,
        deg: float = 0.0,
        opacity: float = 1.0,
        clip_mask: Image.Image | None = None,
    ) -> Image.Image:
        return self.fill_poly(
            self.ellipse_poly(cx, cz, rx, rz, deg=deg),
            color,
            opacity=opacity,
            clip_mask=clip_mask,
        )

    @staticmethod
    def bezier_pts(
        ctrl: Sequence[tuple[float, float]], steps: int = 64
    ) -> list[tuple[float, float]]:
        n = len(ctrl) - 1
        out: list[tuple[float, float]] = []
        for i in range(steps + 1):
            t = i / steps
            u = 1.0 - t
            x = 0.0
            z = 0.0
            for k, (px, pz) in enumerate(ctrl):
                w = math.comb(n, k) * (u ** (n - k)) * (t**k)
                x += w * px
                z += w * pz
            out.append((x, z))
        return out

    def stroke_pts(
        self,
        pts_m: Sequence[tuple[float, float]],
        width_m: float,
        color: str = INK,
        *,
        closed: bool = False,
        taper: float = 0.0,
        opacity: float = 1.0,
        clip_mask: Image.Image | None = None,
    ) -> None:
        """Draw a uniform physical-width stroke in 3D face meters with round caps."""
        pts: list[tuple[float, float]] = [pts_m[0]]
        for p in pts_m[1:]:
            if math.hypot(p[0] - pts[-1][0], p[1] - pts[-1][1]) > 1e-6:
                pts.append(p)
        if len(pts) < 2:
            if pts:
                self.fill_ellipse(
                    pts[0][0], pts[0][1], 0.5 * width_m, 0.5 * width_m, color,
                    opacity=opacity, clip_mask=clip_mask,
                )
            return

        if closed and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) > 1e-6:
            pts.append(pts[0])

        m = len(pts)
        half = 0.5 * width_m
        mask, draw = self.new_mask()

        left_rib: list[tuple[float, float]] = []
        right_rib: list[tuple[float, float]] = []
        radii: list[float] = []

        for i in range(m):
            if closed:
                p_prev = pts[(i - 1) % (m - 1)]
                p_next = pts[(i + 1) % (m - 1)]
            else:
                p_prev = pts[max(0, i - 1)]
                p_next = pts[min(m - 1, i + 1)]
            tx, tz = p_next[0] - p_prev[0], p_next[1] - p_prev[1]
            length = math.hypot(tx, tz) or 1.0
            nx, nz = -tz / length, tx / length

            if not closed and taper > 0.0:
                s = i / max(1, m - 1)
                arch = math.sin(math.pi * s)
                r = half * ((1.0 - taper) + taper * (arch**0.65))
            else:
                r = half
            radii.append(r)
            left_rib.append((pts[i][0] + nx * r, pts[i][1] + nz * r))
            right_rib.append((pts[i][0] - nx * r, pts[i][1] - nz * r))

        for i in range(m - 1):
            quad = [left_rib[i], left_rib[i + 1], right_rib[i + 1], right_rib[i]]
            draw.polygon(self.pts_to_px(quad), fill=255)

        cap_steps = 24
        for i, (px, pz) in enumerate(pts):
            r = radii[i]
            if r > 1e-5:
                if closed and i == m - 1:
                    continue
                if i in (0, m - 1) or i % 2 == 0:
                    draw.polygon(
                        self.pts_to_px(self.ellipse_poly(px, pz, r, r, n=cap_steps)),
                        fill=255,
                    )

        if clip_mask is not None:
            mask = Image.fromarray(
                np.minimum(np.asarray(mask), np.asarray(clip_mask)), mode="L"
            )
        self._over_mask(mask, color, opacity=opacity)

    def stroke_bezier(
        self,
        ctrl: Sequence[tuple[float, float]],
        width_m: float,
        color: str = INK,
        *,
        taper: float = 0.0,
        steps: int = 64,
        clip_mask: Image.Image | None = None,
    ) -> None:
        self.stroke_pts(
            self.bezier_pts(ctrl, steps=steps),
            width_m,
            color=color,
            taper=taper,
            clip_mask=clip_mask,
        )

    def soft_ellipse(
        self,
        cx: float,
        cz: float,
        rx: float,
        rz: float,
        color: str,
        *,
        opacity: float = 0.55,
        deg: float = 0.0,
        blur_px: float = 42.0,
    ) -> None:
        """Feathered blush / glow guaranteed to drop to 0 inside decal borders."""
        mask, draw = self.new_mask()
        draw.polygon(self.pts_to_px(self.ellipse_poly(cx, cz, rx, rz, deg=deg)), fill=255)
        if blur_px > 0:
            mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_px))
        arr = (np.asarray(mask, dtype=np.float32) / 255.0) * self._decal_safe_envelope()
        r, g, b = _hex_rgb(color)
        rgb = np.broadcast_to(
            np.array([r / 255.0, g / 255.0, b / 255.0], dtype=np.float32),
            (self.size, self.size, 3),
        )
        self._over_rgba_arrays(rgb, arr * opacity)

    def _decal_safe_envelope(self) -> np.ndarray:
        """Smooth cosine^2 window fading to 0 well inside UV [0..1] boundaries."""
        u = np.linspace(0.0, 1.0, self.size, dtype=np.float32)
        v = np.linspace(1.0, 0.0, self.size, dtype=np.float32)
        x = DECAL_X_RANGE[0] + u[None, :] * (DECAL_X_RANGE[1] - DECAL_X_RANGE[0])
        z = DECAL_Z_RANGE[0] + v[:, None] * (DECAL_Z_RANGE[1] - DECAL_Z_RANGE[0])
        rad = np.sqrt((x / 0.176) ** 2 + ((z + 0.056) / 0.118) ** 2)
        t = np.clip((1.0 - rad) / 0.28, 0.0, 1.0)
        return (t * t * (3.0 - 2.0 * t)).astype(np.float32)

    def finalize_1024(self) -> Image.Image:
        """Downsample premultiplied 2048->1024 with LANCZOS and edge-dilate RGB."""
        chans_1024 = [
            np.clip(
                np.asarray(
                    Image.fromarray(self.premul[..., c], mode="F").resize(
                        (FINAL_RES, FINAL_RES), Image.Resampling.LANCZOS
                    ),
                    dtype=np.float32,
                ),
                0.0,
                1.0,
            )
            for c in range(4)
        ]
        pm = np.stack(chans_1024, axis=-1)
        alpha = pm[..., 3]
        valid = alpha >= (0.75 / 255.0)
        alpha = np.where(valid, alpha, 0.0)

        ink_rgb = np.array([c / 255.0 for c in _hex_rgb(INK)], dtype=np.float32)
        rgb = np.broadcast_to(ink_rgb, (FINAL_RES, FINAL_RES, 3)).copy()

        solid_seed = alpha >= (12.0 / 255.0)
        nz = alpha > 0.0
        rgb[nz] = np.clip(pm[nz, :3] / alpha[nz, None], 0.0, 1.0)

        dil_rgb = rgb.copy()
        known = solid_seed.copy()
        if not known.any() and nz.any():
            known = nz.copy()

        if known.any():
            for _ in range(18):
                if known.all():
                    break
                pad_k = np.pad(known, 1, mode="edge")
                pad_c = np.pad(dil_rgb, ((1, 1), (1, 1), (0, 0)), mode="edge")
                acc_c = np.zeros_like(dil_rgb)
                acc_w = np.zeros((FINAL_RES, FINAL_RES), dtype=np.float32)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        w = 1.0 if (dx == 0 or dy == 0) else 0.7071
                        nk = pad_k[1 + dy : 1 + dy + FINAL_RES, 1 + dx : 1 + dx + FINAL_RES]
                        nc = pad_c[1 + dy : 1 + dy + FINAL_RES, 1 + dx : 1 + dx + FINAL_RES]
                        mask_w = nk.astype(np.float32) * w
                        acc_c += nc * mask_w[..., None]
                        acc_w += mask_w
                newly = (~known) & (acc_w > 0.0)
                if not newly.any():
                    break
                dil_rgb[newly] = acc_c[newly] / acc_w[newly, None]
                known |= newly

            fringe = nz & (~solid_seed)
            rgb[fringe] = dil_rgb[fringe]
            rgb[~nz] = dil_rgb[~nz]

        out = np.empty((FINAL_RES, FINAL_RES, 4), dtype=np.uint8)
        out[..., :3] = np.clip(np.round(rgb * 255.0), 0, 255).astype(np.uint8)
        out[..., 3] = np.clip(np.round(alpha * 255.0), 0, 255).astype(np.uint8)
        return Image.fromarray(out, mode="RGBA")


# ---------------------------------------------------------------------------
# Reusable Mascot Facial Feature Primitives (in physical head meters)
# ---------------------------------------------------------------------------


def _draw_base_eyes(
    c: FaceCanvas,
    *,
    rx: float = 0.056,
    rz: float = 0.063,
    cx_abs: float = 0.086,
    cz: float = -0.022,
    tilt_deg: float = 6.0,
) -> None:
    """Two large solid glossy-black ovals tilted ~6 deg inward toward nose bridge."""
    c.fill_ellipse(-cx_abs, cz, rx, rz, INK, deg=-tilt_deg)
    c.fill_ellipse(+cx_abs, cz, rx, rz, INK, deg=+tilt_deg)


def _draw_cheek_ticks(
    c: FaceCanvas,
    *,
    cx_abs: float = 0.141,
    cz: float = -0.092,
    count: int = 2,
    color: str = INK,
    sides: tuple[int, ...] = (-1, 1),
) -> None:
    """Cute diagonal '//' ink hash-ticks tucked right below outer corners of eyes."""
    spacing = 0.0112
    dx, dz = 0.0056, 0.0138
    for side in sides:
        base_x = side * cx_abs - 0.5 * (count - 1) * spacing
        for k in range(count):
            x0 = base_x + k * spacing - 0.5 * dx
            z0 = cz - 0.5 * dz
            c.stroke_pts([(x0, z0), (x0 + dx, z0 + dz)], 0.0048, color=color, taper=0.18)


def _sample_closed_spline(
    anchors: Sequence[tuple[float, float]], subdiv: int = 18
) -> list[tuple[float, float]]:
    """Smooth Catmull-Rom closed loop through control anchors."""
    n = len(anchors)
    pts: list[tuple[float, float]] = []
    for i in range(n):
        p0 = anchors[(i - 1) % n]
        p1 = anchors[i]
        p2 = anchors[(i + 1) % n]
        p3 = anchors[(i + 2) % n]
        for s in range(subdiv):
            t = s / subdiv
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (
                (2.0 * p1[0])
                + (-p0[0] + p2[0]) * t
                + (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2
                + (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
            )
            z = 0.5 * (
                (2.0 * p1[1])
                + (-p0[1] + p2[1]) * t
                + (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2
                + (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
            )
            pts.append((x, z))
    return pts


def _draw_sweat_drop(
    c: FaceCanvas, cx: float, cz: float, scale: float = 1.0, tilt_deg: float = 0.0
) -> None:
    """Crisp #141016-outlined cyan comic teardrop safely below tilted beanie cuff."""
    rad = math.radians(tilt_deg)
    ca, sa = math.cos(rad), math.sin(rad)

    def xf(lx: float, lz: float) -> tuple[float, float]:
        sx, sz = lx * scale, lz * scale
        return (cx + sx * ca - sz * sa, cz + sx * sa + sz * ca)

    pts: list[tuple[float, float]] = []
    steps = 48
    for i in range(steps):
        a = math.tau * i / steps
        s = math.sin(a)
        w = 0.0124 * (0.62 - 0.38 * s) * math.cos(a)
        h = 0.0185 * s + (0.0038 if s > 0 else 0.0)
        pts.append(xf(w, h))

    c.fill_poly(pts, SWEAT_CYAN)
    c.fill_ellipse(
        *xf(-0.0034, -0.0038), 0.0028 * scale, 0.0048 * scale, SWEAT_SHINE, deg=tilt_deg
    )
    c.stroke_pts(pts, 0.0040 * max(0.85, scale), INK, closed=True)


def _draw_heart(
    c: FaceCanvas, cx: float, cz: float, size: float, color: str, deg: float = 0.0
) -> None:
    rad = math.radians(deg)
    ca, sa = math.cos(rad), math.sin(rad)
    pts: list[tuple[float, float]] = []
    for i in range(72):
        t = math.tau * i / 72
        hx = 16.0 * (math.sin(t) ** 3) / 17.0
        hz = (
            13.0 * math.cos(t)
            - 5.0 * math.cos(2.0 * t)
            - 2.0 * math.cos(3.0 * t)
            - math.cos(4.0 * t)
        ) / 17.0
        lx, lz = hx * size, (hz + 0.12) * size
        pts.append((cx + lx * ca - lz * sa, cz + lx * sa + lz * ca))
    c.fill_poly(pts, color)


# ---------------------------------------------------------------------------
# 12 Story Expressions + 6 Lip-Sync Visemes
# ---------------------------------------------------------------------------


def _expr_idle_cute(c: FaceCanvas) -> None:
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)
    c.stroke_bezier(
        [(-0.028, -0.102), (-0.011, -0.114), (0.011, -0.114), (0.028, -0.102)],
        0.0064,
        INK,
        taper=0.20,
    )


def _expr_curious_o(c: FaceCanvas) -> None:
    """Exact Reference Images 5 & 6: big black oval eyes + // ticks + open 'o' mouth."""
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)

    # Bold cute rounded-bean 'o' mouth matching Images 5 & 6
    mouth_loop = _sample_closed_spline(
        [
            (-0.034, -0.126),
            (-0.036, -0.103),
            (-0.015, -0.082),
            (0.019, -0.081),
            (0.038, -0.102),
            (0.035, -0.126),
            (0.004, -0.136),
        ],
        subdiv=20,
    )
    clip = c.fill_poly(mouth_loop, MOUTH_DARK)

    # Coral-pink curved tongue filling lower ~56% of cavity
    tongue_top = c.bezier_pts(
        [(-0.042, -0.123), (-0.014, -0.100), (0.018, -0.103), (0.042, -0.127)],
        steps=40,
    )
    tongue_poly = tongue_top + [(0.046, -0.152), (-0.046, -0.152)]
    c.fill_poly(tongue_poly, TONGUE_PINK, clip_mask=clip)
    c.stroke_pts(tongue_top, 0.0040, INK, clip_mask=clip)

    c.stroke_pts(mouth_loop, 0.0068, INK, closed=True)


def _expr_chill_laugh(c: FaceCanvas) -> None:
    """Exact Reference Image 7: big black ovals + // ticks + wide happy D/U laugh mouth."""
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)

    # Tall joyful U/D laugh shield sitting high between the cheeks (exact Image 7!)
    top_arc = c.bezier_pts(
        [(-0.052, -0.068), (-0.018, -0.073), (0.018, -0.073), (0.052, -0.068)],
        steps=28,
    )
    right_down = c.bezier_pts(
        [(0.052, -0.068), (0.055, -0.112), (0.035, -0.156), (0.0, -0.160)],
        steps=28,
    )
    left_up = c.bezier_pts(
        [(0.0, -0.160), (-0.035, -0.156), (-0.055, -0.112), (-0.052, -0.068)],
        steps=28,
    )
    mouth_pts = top_arc + right_down[1:] + left_up[1:]
    clip = c.fill_poly(mouth_pts, MOUTH_DARK)

    # Crisp snow-white top teeth bar (#FFFDFB)
    teeth_bot = c.bezier_pts(
        [(-0.058, -0.087), (-0.018, -0.092), (0.018, -0.092), (0.058, -0.087)],
        steps=32,
    )
    teeth_poly = [(-0.062, -0.058), (0.062, -0.058)] + list(reversed(teeth_bot))
    c.fill_poly(teeth_poly, WHITE, clip_mask=clip)
    c.stroke_pts(teeth_bot, 0.0044, INK, clip_mask=clip)

    # Joyful coral-pink tongue curving across lower ~54%
    tongue_top = c.bezier_pts(
        [(-0.056, -0.128), (-0.022, -0.104), (0.020, -0.105), (0.056, -0.132)],
        steps=36,
    )
    tongue_poly = tongue_top + [(0.060, -0.172), (-0.060, -0.172)]
    c.fill_poly(tongue_poly, TONGUE_PINK, clip_mask=clip)
    c.stroke_pts(tongue_top, 0.0042, INK, clip_mask=clip)

    c.stroke_pts(mouth_pts, 0.0070, INK, closed=True)


def _expr_hype_letsgo(c: FaceCanvas) -> None:
    """Wide excited eyes + bold brows + huge open hype mouth + action ticks."""
    for side in (-1, 1):
        c.stroke_bezier(
            [
                (side * 0.038, 0.024),
                (side * 0.068, 0.039),
                (side * 0.102, 0.036),
                (side * 0.124, 0.019),
            ],
            0.0078,
            INK,
            taper=0.26,
        )
        cx, cz = side * 0.082, -0.025
        eye_pts = c.ellipse_poly(cx, cz, 0.048, 0.051, deg=side * 4.0)
        c.fill_poly(eye_pts, WHITE)
        c.fill_ellipse(cx - side * 0.004, cz - 0.002, 0.017, 0.020, INK)
        c.stroke_pts(eye_pts, 0.0070, INK, closed=True)

    # Huge open hype trapezoid-U mouth ("LET'S GOOO!")
    top_edge = c.bezier_pts(
        [(-0.074, -0.078), (-0.026, -0.074), (0.026, -0.074), (0.074, -0.078)],
        steps=30,
    )
    r_edge = c.bezier_pts(
        [(0.074, -0.078), (0.080, -0.128), (0.050, -0.172), (0.0, -0.176)],
        steps=30,
    )
    l_edge = c.bezier_pts(
        [(0.0, -0.176), (-0.050, -0.172), (-0.080, -0.128), (-0.074, -0.078)],
        steps=30,
    )
    mouth_pts = top_edge + r_edge[1:] + l_edge[1:]
    clip = c.fill_poly(mouth_pts, MOUTH_DEEP)

    c.fill_ellipse(0.0, -0.126, 0.013, 0.022, "#5C2230", clip_mask=clip)
    tongue_top = c.bezier_pts(
        [(-0.060, -0.168), (-0.022, -0.142), (0.022, -0.142), (0.060, -0.168)],
        steps=36,
    )
    c.fill_poly(tongue_top + [(0.068, -0.185), (-0.068, -0.185)], TONGUE_PINK, clip_mask=clip)
    c.stroke_pts(tongue_top, 0.0040, INK, clip_mask=clip)

    teeth_bot = c.bezier_pts(
        [(-0.080, -0.098), (-0.026, -0.094), (0.026, -0.094), (0.080, -0.098)],
        steps=32,
    )
    c.fill_poly(
        [(-0.084, -0.068), (0.084, -0.068)] + list(reversed(teeth_bot)),
        WHITE,
        clip_mask=clip,
    )
    for tx in (-0.048, -0.024, 0.0, 0.024, 0.048):
        c.stroke_pts([(tx, -0.072), (tx, -0.097)], 0.0028, INK, clip_mask=clip)
    c.stroke_pts(teeth_bot, 0.0046, INK, clip_mask=clip)
    c.stroke_pts(mouth_pts, 0.0072, INK, closed=True)

    for side in (-1, 1):
        c.stroke_pts(
            [(side * 0.144, 0.002), (side * 0.166, 0.014)], 0.0050, INK, taper=0.25
        )
        c.stroke_pts(
            [(side * 0.149, -0.020), (side * 0.172, -0.016)], 0.0048, INK, taper=0.25
        )
        c.stroke_bezier(
            [
                (side * 0.148, -0.092),
                (side * 0.158, -0.118),
                (side * 0.148, -0.144),
            ],
            0.0044,
            INK,
            taper=0.30,
        )


def _expr_cringe_teeth(c: FaceCanvas) -> None:
    """Left eye squeezed '>' + right wide eye + wide clenched teeth grid + cyan sweat drops."""
    # Left squeezed '>' chevron eye + wince brow
    c.stroke_bezier(
        [(-0.122, 0.022), (-0.088, 0.016), (-0.052, 0.002)], 0.0074, INK, taper=0.25
    )
    c.stroke_pts(
        [(-0.124, -0.006), (-0.048, -0.028), (-0.124, -0.050)], 0.0090, INK, taper=0.12
    )

    # Right wide startled eye + tense flat brow
    rx_c, rz_c = 0.084, -0.028
    eye_pts = c.ellipse_poly(rx_c, rz_c, 0.046, 0.048)
    c.fill_poly(eye_pts, WHITE)
    c.fill_ellipse(rx_c - 0.003, rz_c + 0.002, 0.014, 0.015, INK)
    c.stroke_pts(eye_pts, 0.0068, INK, closed=True)
    c.stroke_bezier(
        [(0.040, 0.020), (0.084, 0.028), (0.128, 0.018)], 0.0076, INK, taper=0.22
    )

    # Wide clenched curved teeth grimace
    top_lip = c.bezier_pts(
        [(-0.096, -0.098), (-0.036, -0.089), (0.036, -0.089), (0.096, -0.098)],
        steps=36,
    )
    r_corner = c.bezier_pts(
        [(0.096, -0.098), (0.102, -0.118), (0.075, -0.146), (0.0, -0.150)],
        steps=24,
    )
    l_corner = c.bezier_pts(
        [(0.0, -0.150), (-0.075, -0.146), (-0.102, -0.118), (-0.096, -0.098)],
        steps=24,
    )
    grimace_pts = top_lip + r_corner[1:] + l_corner[1:]
    clip = c.fill_poly(grimace_pts, WHITE)

    mid_bite = c.bezier_pts(
        [(-0.100, -0.116), (-0.034, -0.121), (0.034, -0.121), (0.100, -0.116)],
        steps=36,
    )
    c.stroke_pts(mid_bite, 0.0040, INK, clip_mask=clip)
    for tx in (-0.070, -0.046, -0.023, 0.0, 0.023, 0.046, 0.070):
        c.stroke_pts([(tx, -0.084), (tx, -0.154)], 0.0034, INK, clip_mask=clip)

    c.stroke_pts(grimace_pts, 0.0066, INK, closed=True)
    for side in (-1, 1):
        c.stroke_bezier(
            [(side * 0.104, -0.090), (side * 0.112, -0.104), (side * 0.106, -0.118)],
            0.0040,
            INK,
            taper=0.30,
        )
    for cx_t in (-0.017, 0.0, 0.017):
        c.stroke_pts([(cx_t, -0.160), (cx_t - 0.002, -0.171)], 0.0032, INK, taper=0.25)

    # Cyan temple sweat drops safely below tilted beanie cuff
    _draw_sweat_drop(c, -0.152, -0.008, scale=1.02, tilt_deg=12.0)
    _draw_sweat_drop(c, +0.152, -0.016, scale=1.06, tilt_deg=-12.0)


def _expr_whatever_eyeroll(c: FaceCanvas) -> None:
    """Half-lidded upward eye-roll + side air-puff mouth."""
    c.stroke_bezier(
        [(-0.122, 0.022), (-0.082, 0.031), (-0.044, 0.028)], 0.0072, INK, taper=0.25
    )
    c.stroke_bezier(
        [(0.044, 0.030), (0.084, 0.036), (0.124, 0.024)], 0.0072, INK, taper=0.25
    )

    for side in (-1, 1):
        cx, cz = side * 0.082, -0.027
        eye_pts = c.ellipse_poly(cx, cz, 0.048, 0.048)
        clip = c.fill_poly(eye_pts, WHITE)
        c.fill_ellipse(cx + 0.005, cz + 0.020, 0.025, 0.022, INK, clip_mask=clip)
        lid_line = c.bezier_pts(
            [(cx - 0.052, cz + 0.007), (cx, cz + 0.011), (cx + 0.052, cz + 0.005)],
            steps=28,
        )
        lid_poly = [(cx - 0.055, cz + 0.055), (cx + 0.055, cz + 0.055)] + list(
            reversed(lid_line)
        )
        c.fill_poly(lid_poly, "#E8EEF7", clip_mask=clip)
        c.stroke_pts(lid_line, 0.0062, INK, clip_mask=clip)
        c.stroke_pts(eye_pts, 0.0066, INK, closed=True)
        c.stroke_bezier(
            [(cx - 0.028, cz - 0.056), (cx, cz - 0.060), (cx + 0.028, cz - 0.056)],
            0.0032,
            INK,
            taper=0.35,
        )

    _draw_cheek_ticks(c, sides=(-1,))

    c.stroke_bezier(
        [(-0.022, -0.116), (0.018, -0.108), (0.060, -0.098)], 0.0068, INK, taper=0.20
    )
    c.stroke_bezier(
        [(0.060, -0.086), (0.071, -0.098), (0.060, -0.112)], 0.0046, INK, taper=0.30
    )
    c.stroke_pts([(0.078, -0.090), (0.102, -0.080)], 0.0040, INK, taper=0.25)
    c.stroke_pts([(0.080, -0.100), (0.108, -0.100)], 0.0040, INK, taper=0.25)
    c.stroke_pts([(0.078, -0.110), (0.102, -0.120)], 0.0040, INK, taper=0.25)
    for bx, bz, br in ((0.122, -0.088, 0.0115), (0.143, -0.106, 0.0145)):
        bpts = c.ellipse_poly(bx, bz, br, br)
        c.fill_poly(bpts, WHITE)
        c.stroke_pts(bpts, 0.0040, INK, closed=True)


def _expr_phone_zombie(c: FaceCanvas) -> None:
    """Droopy tired lids + under-eye bags + open 'o' mouth + drool drop + blue screen glow."""
    # Cool-blue screen glow tint calibrated for AgX snow-white head
    c.soft_ellipse(0.0, -0.024, 0.158, 0.104, "#2B4885", opacity=0.38, blur_px=54.0)
    c.soft_ellipse(0.0, -0.112, 0.140, 0.076, "#58C8FF", opacity=0.46, blur_px=46.0)

    for side in (-1, 1):
        c.stroke_bezier(
            [(side * 0.040, 0.020), (side * 0.080, 0.024), (side * 0.122, 0.016)],
            0.0068,
            INK,
            taper=0.25,
        )
        cx, cz = side * 0.080, -0.028
        eye_pts = c.ellipse_poly(cx, cz, 0.047, 0.042)
        clip = c.fill_poly(eye_pts, "#EDF5FF")
        c.fill_ellipse(cx, cz - 0.008, 0.019, 0.019, INK, clip_mask=clip)

        lid_line = c.bezier_pts(
            [(cx - 0.052, cz + 0.002), (cx, cz - 0.005), (cx + 0.052, cz + 0.000)],
            steps=28,
        )
        c.fill_poly(
            [(cx - 0.055, cz + 0.048), (cx + 0.055, cz + 0.048)] + list(reversed(lid_line)),
            "#7892BE",
            clip_mask=clip,
        )
        c.stroke_pts(lid_line, 0.0062, INK, clip_mask=clip)
        c.stroke_pts(eye_pts, 0.0064, INK, closed=True)

        c.stroke_bezier(
            [(cx - 0.038, cz - 0.049), (cx, cz - 0.058), (cx + 0.038, cz - 0.049)],
            0.0042,
            INK,
            taper=0.35,
        )
        c.stroke_bezier(
            [(cx - 0.026, cz - 0.059), (cx, cz - 0.066), (cx + 0.026, cz - 0.059)],
            0.0030,
            "#314263",
            taper=0.35,
        )

    mouth_pts = c.ellipse_poly(0.0, -0.114, 0.022, 0.027)
    mclip = c.fill_poly(mouth_pts, MOUTH_DARK)
    c.fill_ellipse(0.0, -0.129, 0.018, 0.013, TONGUE_PINK, clip_mask=mclip)
    c.stroke_pts(mouth_pts, 0.0060, INK, closed=True)

    drool_pts = _sample_closed_spline(
        [
            (0.002, -0.136),
            (0.009, -0.138),
            (0.012, -0.160),
            (0.005, -0.174),
            (-0.002, -0.160),
        ],
        subdiv=14,
    )
    c.fill_poly(drool_pts, DROOL_CYAN)
    c.stroke_pts(drool_pts, 0.0036, INK, closed=True)


def _expr_sulk_pout(c: FaceCanvas) -> None:
    """Angled pouty brows + soft pink rosy cheeks + hmph pout mouth."""
    for side in (-1, 1):
        c.soft_ellipse(
            side * 0.130, -0.088, 0.042, 0.026, BLUSH_PINK, opacity=0.68, blur_px=22.0
        )

    for side in (-1, 1):
        cx, cz = side * 0.084, -0.030
        c.stroke_bezier(
            [
                (side * 0.130, 0.028),
                (side * 0.084, 0.016),
                (side * 0.038, -0.001),
            ],
            0.0086,
            INK,
            taper=0.18,
        )
        eye_mask, edraw = c.new_mask()
        edraw.polygon(
            c.pts_to_px(c.ellipse_poly(cx, cz, 0.050, 0.045, deg=side * 5.0)), fill=255
        )
        lid_cut = [
            (cx - side * 0.060, cz - 0.005),
            (cx + side * 0.060, cz + 0.020),
            (cx + side * 0.060, cz + 0.060),
            (cx - side * 0.060, cz + 0.060),
        ]
        cut_mask, cdraw = c.new_mask()
        cdraw.polygon(c.pts_to_px(lid_cut), fill=255)
        kept = Image.fromarray(
            np.minimum(np.asarray(eye_mask), 255 - np.asarray(cut_mask)), mode="L"
        )
        c._over_mask(kept, INK)
        c.stroke_pts(
            [(cx - side * 0.052, cz - 0.002), (cx + side * 0.052, cz + 0.018)],
            0.0074,
            INK,
            taper=0.15,
        )

    _draw_cheek_ticks(c, cx_abs=0.136, cz=-0.090)

    pout_loop = _sample_closed_spline(
        [
            (-0.036, -0.108),
            (-0.014, -0.098),
            (0.018, -0.100),
            (0.035, -0.114),
            (0.016, -0.129),
            (-0.020, -0.126),
        ],
        subdiv=16,
    )
    pclip = c.fill_poly(pout_loop, TONGUE_PINK)
    c.fill_poly(
        [(-0.040, -0.094), (0.040, -0.094), (0.040, -0.107), (-0.040, -0.107)],
        WHITE,
        clip_mask=pclip,
    )
    c.stroke_pts([(-0.038, -0.107), (0.038, -0.108)], 0.0036, INK, clip_mask=pclip)
    c.stroke_pts(pout_loop, 0.0062, INK, closed=True)
    c.stroke_bezier(
        [(-0.016, -0.139), (0.0, -0.135), (0.016, -0.139)], 0.0038, INK, taper=0.35
    )


def _expr_mortified_blush(c: FaceCanvas) -> None:
    """Warm rosy-red embarrassed flush + wide shock eyes + wavy '~' mouth + sweat drops."""
    c.soft_ellipse(0.0, -0.060, 0.158, 0.098, FLUSH_RED, opacity=0.56, blur_px=50.0)
    for side in (-1, 1):
        c.soft_ellipse(
            side * 0.120, -0.084, 0.050, 0.032, "#FF3E55", opacity=0.44, blur_px=26.0
        )

    for side in (-1, 1):
        c.stroke_bezier(
            [
                (side * 0.120, 0.028),
                (side * 0.080, 0.018),
                (side * 0.036, 0.004),
            ],
            0.0074,
            INK,
            taper=0.22,
        )
        cx, cz = side * 0.078, -0.029
        eye_pts = c.ellipse_poly(cx, cz, 0.045, 0.050)
        c.fill_poly(eye_pts, WHITE)
        c.fill_ellipse(cx - side * 0.004, cz, 0.011, 0.012, INK)
        c.stroke_pts(eye_pts, 0.0068, INK, closed=True)
        c.stroke_bezier(
            [
                (side * 0.130, -0.016),
                (side * 0.136, -0.030),
                (side * 0.130, -0.044),
            ],
            0.0036,
            INK,
            taper=0.35,
        )

    _draw_cheek_ticks(c, cx_abs=0.128, cz=-0.090, count=3)

    wavy = (
        c.bezier_pts(
            [(-0.058, -0.120), (-0.040, -0.104), (-0.022, -0.104), (-0.008, -0.119)],
            steps=24,
        )
        + c.bezier_pts(
            [(-0.008, -0.119), (0.008, -0.134), (0.026, -0.104), (0.042, -0.118)],
            steps=24,
        )[1:]
        + c.bezier_pts(
            [(0.042, -0.118), (0.050, -0.127), (0.056, -0.120), (0.060, -0.112)],
            steps=16,
        )[1:]
    )
    c.stroke_pts(wavy, 0.0068, INK, taper=0.18)

    _draw_sweat_drop(c, -0.152, -0.008, scale=1.00, tilt_deg=12.0)
    _draw_sweat_drop(c, +0.152, -0.014, scale=1.00, tilt_deg=-12.0)


def _expr_smug_wink(c: FaceCanvas) -> None:
    """Smooth '—' wink on left eye, confident Mascot oval eye on right + smirk."""
    c.stroke_bezier(
        [(-0.124, 0.020), (-0.086, 0.026), (-0.048, 0.018)], 0.0068, INK, taper=0.28
    )
    c.stroke_bezier(
        [(-0.134, -0.026), (-0.086, -0.018), (-0.038, -0.028)], 0.0096, INK, taper=0.20
    )

    c.fill_ellipse(0.086, -0.024, 0.055, 0.061, INK, deg=6.0)
    c.stroke_bezier(
        [(0.042, 0.028), (0.086, 0.042), (0.128, 0.024)], 0.0076, INK, taper=0.28
    )

    _draw_cheek_ticks(c)

    c.stroke_bezier(
        [(-0.044, -0.112), (-0.004, -0.116), (0.032, -0.106), (0.060, -0.090)],
        0.0068,
        INK,
        taper=0.20,
    )
    c.stroke_bezier(
        [(0.058, -0.081), (0.068, -0.089), (0.064, -0.101)],
        0.0046,
        INK,
        taper=0.30,
    )


def _expr_crush_hearts(c: FaceCanvas) -> None:
    """Glowing pink heart highlights inside big black oval eyes + rosy /// cheeks + :3 mouth."""
    for side in (-1, 1):
        c.soft_ellipse(
            side * 0.130, -0.090, 0.045, 0.026, "#FF759B", opacity=0.72, blur_px=18.0
        )

    for side in (-1, 1):
        c.stroke_bezier(
            [(side * 0.044, 0.030), (side * 0.086, 0.040), (side * 0.124, 0.024)],
            0.0068,
            INK,
            taper=0.28,
        )

    _draw_base_eyes(c, rx=0.056, rz=0.061, cx_abs=0.086, cz=-0.025, tilt_deg=6.0)
    for side in (-1, 1):
        hx, hz = side * 0.084, -0.024
        _draw_heart(c, hx, hz, size=0.035, color=HEART_PINK, deg=-side * 8.0)
        _draw_heart(
            c,
            hx - side * 0.005,
            hz + 0.005,
            size=0.014,
            color=HEART_SHINE,
            deg=-side * 8.0,
        )

    _draw_cheek_ticks(c, cx_abs=0.130, cz=-0.090, count=3, color="#5E152E")

    left_w = c.bezier_pts(
        [(-0.046, -0.100), (-0.034, -0.120), (-0.010, -0.118), (0.0, -0.102)], steps=28
    )
    right_w = c.bezier_pts(
        [(0.0, -0.102), (0.010, -0.118), (0.034, -0.120), (0.046, -0.100)], steps=28
    )
    c.stroke_pts(left_w, 0.0062, INK, taper=0.15)
    c.stroke_pts(right_w, 0.0062, INK, taper=0.15)


def _expr_ugh_groan(c: FaceCanvas) -> None:
    """Squeezed '> <' eyes + dramatic tall open groan mouth + long sticking-out pink tongue."""
    for side in (-1, 1):
        c.stroke_bezier(
            [(side * 0.124, 0.026), (side * 0.084, 0.018), (side * 0.046, 0.008)],
            0.0070,
            INK,
            taper=0.25,
        )
        c.stroke_pts(
            [
                (side * 0.126, -0.005),
                (side * 0.048, -0.028),
                (side * 0.126, -0.051),
            ],
            0.0092,
            INK,
            taper=0.12,
        )

    _draw_cheek_ticks(c)

    cave_pts = _sample_closed_spline(
        [
            (-0.048, -0.080),
            (0.0, -0.073),
            (0.048, -0.080),
            (0.054, -0.120),
            (0.035, -0.148),
            (-0.035, -0.148),
            (-0.054, -0.120),
        ],
        subdiv=18,
    )
    c.fill_poly(cave_pts, MOUTH_DEEP)
    c.stroke_pts(cave_pts, 0.0068, INK, closed=True)

    tongue_arch = c.bezier_pts(
        [(-0.028, -0.116), (-0.011, -0.106), (0.012, -0.106), (0.028, -0.118)],
        steps=20,
    )
    tongue_r = c.bezier_pts(
        [(0.028, -0.118), (0.031, -0.152), (0.018, -0.180), (-0.004, -0.181)],
        steps=24,
    )
    tongue_l = c.bezier_pts(
        [(-0.004, -0.181), (-0.024, -0.178), (-0.031, -0.150), (-0.028, -0.116)],
        steps=24,
    )
    tongue_pts = tongue_arch + tongue_r[1:] + tongue_l[1:]
    c.fill_poly(tongue_pts, TONGUE_PINK)
    c.stroke_pts(tongue_pts, 0.0060, INK, closed=True)
    c.stroke_bezier(
        [(0.001, -0.112), (-0.001, -0.140), (-0.003, -0.164)],
        0.0036,
        INK,
        taper=0.25,
    )


# ---------------------------------------------------------------------------
# 6 Lip-Sync Visemes (100% pixel-steady Base Eyes + // cheek ticks)
# ---------------------------------------------------------------------------


def _vis_closed(c: FaceCanvas) -> None:
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)
    c.stroke_bezier(
        [(-0.036, -0.108), (-0.013, -0.112), (0.013, -0.112), (0.036, -0.108)],
        0.0062,
        INK,
        taper=0.18,
    )


def _vis_AA(c: FaceCanvas) -> None:
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)
    mouth_pts = _sample_closed_spline(
        [
            (-0.046, -0.084),
            (0.0, -0.079),
            (0.046, -0.084),
            (0.049, -0.118),
            (0.026, -0.148),
            (-0.026, -0.148),
            (-0.049, -0.118),
        ],
        subdiv=18,
    )
    clip = c.fill_poly(mouth_pts, MOUTH_DARK)
    teeth_bot = c.bezier_pts([(-0.054, -0.097), (0.0, -0.100), (0.054, -0.097)], steps=24)
    c.fill_poly(
        [(-0.056, -0.072), (0.056, -0.072)] + list(reversed(teeth_bot)),
        WHITE,
        clip_mask=clip,
    )
    c.stroke_pts(teeth_bot, 0.0038, INK, clip_mask=clip)
    tongue_top = c.bezier_pts(
        [(-0.048, -0.134), (-0.016, -0.116), (0.016, -0.116), (0.048, -0.134)],
        steps=28,
    )
    c.fill_poly(tongue_top + [(0.052, -0.160), (-0.052, -0.160)], TONGUE_PINK, clip_mask=clip)
    c.stroke_pts(tongue_top, 0.0036, INK, clip_mask=clip)
    c.stroke_pts(mouth_pts, 0.0064, INK, closed=True)


def _vis_EE(c: FaceCanvas) -> None:
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)
    mouth_pts = _sample_closed_spline(
        [
            (-0.058, -0.094),
            (0.0, -0.090),
            (0.058, -0.094),
            (0.054, -0.120),
            (0.0, -0.129),
            (-0.054, -0.120),
        ],
        subdiv=18,
    )
    clip = c.fill_poly(mouth_pts, MOUTH_DARK)
    teeth_bot = c.bezier_pts([(-0.064, -0.107), (0.0, -0.110), (0.064, -0.107)], steps=24)
    c.fill_poly(
        [(-0.066, -0.082), (0.066, -0.082)] + list(reversed(teeth_bot)),
        WHITE,
        clip_mask=clip,
    )
    c.stroke_pts(teeth_bot, 0.0038, INK, clip_mask=clip)
    c.fill_ellipse(0.0, -0.127, 0.036, 0.011, TONGUE_PINK, clip_mask=clip)
    c.stroke_pts(mouth_pts, 0.0062, INK, closed=True)


def _vis_OH(c: FaceCanvas) -> None:
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)
    mouth_pts = c.ellipse_poly(0.0, -0.112, 0.031, 0.035)
    clip = c.fill_poly(mouth_pts, MOUTH_DARK)
    tongue_top = c.bezier_pts([(-0.036, -0.129), (0.0, -0.117), (0.036, -0.129)], steps=24)
    c.fill_poly(tongue_top + [(0.038, -0.155), (-0.038, -0.155)], TONGUE_PINK, clip_mask=clip)
    c.stroke_pts(tongue_top, 0.0036, INK, clip_mask=clip)
    c.stroke_pts(mouth_pts, 0.0064, INK, closed=True)


def _vis_OO(c: FaceCanvas) -> None:
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)
    mouth_pts = c.ellipse_poly(0.0, -0.110, 0.018, 0.020)
    clip = c.fill_poly(mouth_pts, MOUTH_DARK)
    c.fill_ellipse(0.0, -0.121, 0.014, 0.010, TONGUE_PINK, clip_mask=clip)
    c.stroke_pts(mouth_pts, 0.0060, INK, closed=True)


def _vis_FV(c: FaceCanvas) -> None:
    _draw_base_eyes(c)
    _draw_cheek_ticks(c)
    mouth_pts = _sample_closed_spline(
        [
            (-0.046, -0.098),
            (0.0, -0.093),
            (0.046, -0.098),
            (0.038, -0.118),
            (0.0, -0.121),
            (-0.038, -0.118),
        ],
        subdiv=16,
    )
    clip = c.fill_poly(mouth_pts, MOUTH_DARK)
    teeth_poly = [
        (-0.033, -0.088),
        (0.033, -0.088),
        (0.030, -0.111),
        (-0.030, -0.111),
    ]
    c.fill_poly(teeth_poly, WHITE, clip_mask=clip)
    for tx in (-0.011, 0.011):
        c.stroke_pts([(tx, -0.091), (tx, -0.111)], 0.0028, INK, clip_mask=clip)
    c.stroke_pts([(-0.031, -0.111), (0.031, -0.111)], 0.0036, INK, clip_mask=clip)
    c.stroke_pts(mouth_pts, 0.0062, INK, closed=True)


_BUILDERS = {
    "idle_cute": _expr_idle_cute,
    "curious_o": _expr_curious_o,
    "chill_laugh": _expr_chill_laugh,
    "hype_letsgo": _expr_hype_letsgo,
    "cringe_teeth": _expr_cringe_teeth,
    "whatever_eyeroll": _expr_whatever_eyeroll,
    "phone_zombie": _expr_phone_zombie,
    "sulk_pout": _expr_sulk_pout,
    "mortified_blush": _expr_mortified_blush,
    "smug_wink": _expr_smug_wink,
    "crush_hearts": _expr_crush_hearts,
    "ugh_groan": _expr_ugh_groan,
    "vis_closed": _vis_closed,
    "vis_AA": _vis_AA,
    "vis_EE": _vis_EE,
    "vis_OH": _vis_OH,
    "vis_OO": _vis_OO,
    "vis_FV": _vis_FV,
}


# ---------------------------------------------------------------------------
# Public Generator API & Optional Contact-Sheet Renderer
# ---------------------------------------------------------------------------


def render_expression_image(name: str) -> Image.Image:
    """Render a single named expression or viseme to a 1024x1024 RGBA Image."""
    if name not in _BUILDERS:
        raise ValueError(f"Unknown mascot expression/viseme: {name!r}")
    canvas = FaceCanvas(SUPERSAMPLE_RES)
    _BUILDERS[name](canvas)
    return canvas.finalize_1024()


def generate_all(out_dir: str | Path | None = None) -> dict[str, Path]:
    """Generate all 12 story expressions + 6 visemes and return `{name: Path}`."""
    base_dir = (
        Path(out_dir).expanduser().resolve()
        if out_dir is not None
        else Path(__file__).resolve().parent / "expressions"
    )
    vis_dir = base_dir / "visemes"
    base_dir.mkdir(parents=True, exist_ok=True)
    vis_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for name in EXPRESSIONS:
        dest = base_dir / f"{name}.png"
        render_expression_image(name).save(dest, format="PNG", compress_level=6)
        paths[name] = dest

    for name in VISEMES:
        dest = vis_dir / f"{name}.png"
        render_expression_image(name).save(dest, format="PNG", compress_level=6)
        paths[name] = dest

    return paths


def render_contact_sheet(paths: dict[str, Path], dest_path: str | Path) -> Path:
    """Render an external QA contact sheet previewing decals on the Mascot head."""
    dest = Path(dest_path).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    cols, rows = 6, 3
    cell_w, cell_h = 360, 410
    sheet = Image.new("RGB", (cols * cell_w + 40, rows * cell_h + 70), (242, 238, 229))
    sdraw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    sdraw.text(
        (28, 22),
        "MASCOT EXPRESSION & VISEME PACK (12 Story + 6 Speech Visemes | Exact 3D Head + Beanie Rim Match)",
        fill=(24, 20, 28),
        font=font,
    )

    names = list(EXPRESSIONS) + list(VISEMES)
    px_per_m = 640.0

    for idx, name in enumerate(names):
        r_idx, c_idx = divmod(idx, cols)
        ox = 20 + c_idx * cell_w
        oy = 56 + r_idx * cell_h

        card = Image.new("RGBA", (cell_w - 16, cell_h - 16), (252, 250, 245, 255))
        cdraw = ImageDraw.Draw(card)
        cx_px, cz_px = (cell_w - 16) // 2, 202

        def hm(xm: float, zm: float) -> tuple[float, float]:
            return (cx_px + xm * px_per_m, cz_px - zm * px_per_m)

        rx_h, rz_h = HEAD_RADII[0] * px_per_m, HEAD_RADII[2] * px_per_m
        cdraw.ellipse(
            (cx_px - rx_h - 5, cz_px - rz_h - 5, cx_px + rx_h + 5, cz_px + rz_h + 5),
            fill=_hex_rgb(INK) + (255,),
        )
        cdraw.ellipse(
            (cx_px - rx_h, cz_px - rz_h, cx_px + rx_h, cz_px + rz_h),
            fill=(255, 253, 251, 255),
        )

        decal_im = Image.open(paths[name]).convert("RGBA")
        dw = round((DECAL_X_RANGE[1] - DECAL_X_RANGE[0]) * px_per_m)
        dh = round((DECAL_Z_RANGE[1] - DECAL_Z_RANGE[0]) * px_per_m)
        decal_scaled = decal_im.resize((dw, dh), Image.Resampling.LANCZOS)
        dx0 = round(cx_px + DECAL_X_RANGE[0] * px_per_m)
        dy0 = round(cz_px - DECAL_Z_RANGE[1] * px_per_m)
        card.alpha_composite(decal_scaled, dest=(dx0, dy0))

        # Exact _beanie_rim_z curve + 4 deg tilt matching build_mascot_asset.py!
        beanie_pts: list[tuple[float, float]] = []
        for i in range(41):
            a = math.pi * i / 40.0
            xm = -0.242 * math.cos(a)
            zm = 0.040 + 0.220 * math.sin(a) - 0.070 * xm
            beanie_pts.append(hm(xm, zm))
        for i in range(41):
            t = 1.0 - i / 40.0
            xm = -0.242 + 0.484 * t
            front = math.sqrt(max(0.0, 1.0 - min(1.0, abs(xm) / 0.242) ** 2))
            z_rim = -0.022 + 0.090 * (front**0.85) - 0.008 - 0.070 * xm
            beanie_pts.append(hm(xm, z_rim))

        cdraw = ImageDraw.Draw(card)
        cdraw.polygon(beanie_pts, fill=(230, 36, 41, 255), outline=_hex_rgb(INK) + (255,))
        for rx_rib in (-0.155, -0.092, -0.030, 0.030, 0.092, 0.155):
            front = math.sqrt(max(0.0, 1.0 - (abs(rx_rib) / 0.242) ** 2))
            z_bot = -0.022 + 0.090 * (front**0.85) - 0.008 - 0.070 * rx_rib
            z_top = 0.040 + 0.218 * math.sqrt(max(0.05, 1.0 - (rx_rib / 0.245) ** 2)) - 0.055 * rx_rib
            cdraw.line([hm(rx_rib, z_bot), hm(rx_rib * 0.80, z_top)], fill=_hex_rgb(INK) + (255,), width=3)
        cdraw.line(beanie_pts + [beanie_pts[0]], fill=_hex_rgb(INK) + (255,), width=5)

        tag = f"[VISEME] {name}" if name in VISEMES else f"{idx + 1:02d}. {name}"
        cdraw.rectangle((0, cell_h - 52, cell_w - 16, cell_h - 16), fill=(26, 22, 30, 255))
        cdraw.text((14, cell_h - 40), tag, fill=(255, 253, 251, 255), font=font)

        sheet.paste(card.convert("RGB"), (ox + 8, oy + 8))

    sheet.save(dest, format="PNG")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Mascot expression & viseme PNGs.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Output directory for PNGs.")
    parser.add_argument(
        "--contact-sheet",
        type=Path,
        default=None,
        help="Optional external path for a visual QA contact sheet PNG.",
    )
    args = parser.parse_args()

    generated = generate_all(args.out_dir)
    print(f"Generated {len(generated)} mascot decals in {next(iter(generated.values())).parent}")
    if args.contact_sheet is not None:
        sheet = render_contact_sheet(generated, args.contact_sheet)
        print(f"Rendered contact sheet: {sheet}")


if __name__ == "__main__":
    main()
