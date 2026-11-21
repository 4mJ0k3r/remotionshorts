"""Shared cel painting helpers (PIL + numpy + scipy).

Implements the cel studio contract: one stable organic contour, distance-field
ink inset with directional pressure (never a radial inset from image center),
paint clipped inside the ink, a 15% cool crescent, and RGB edge-dilation so
transparent pixels never carry a white halo.

The briefing's volumetric read is painted, not geometric: a directional gradient
from lit top-left to 28% darker bottom-right plus a crisp warm rim on the lit
contour. Cards stay flat planes in Blender.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import distance_transform_edt

SS = 2  # supersample factor
OUT_SCALE = 1.5  # V4: design space stays 1024-based, PNGs ship at 1536-class resolution


def rough_ellipse(cx, cy, rx, ry, count=360, seed=0.0, amp=1.0):
    """Static organic contour. No frame-dependent phase."""
    pts = []
    for i in range(count):
        a = 2 * np.pi * i / count
        r = 1 + amp * (0.022 * np.sin(2 * a + 0.6 + seed)
                       - 0.015 * np.cos(3 * a - 0.8 + seed)
                       + 0.008 * np.sin(5 * a + 1.9 + seed))
        pts.append((cx + rx * r * np.cos(a), cy + ry * r * np.sin(a)))
    return pts


def mask_from(draw_fn, size):
    m = Image.new("L", (size[0] * SS, size[1] * SS), 0)
    d = ImageDraw.Draw(m)
    draw_fn(d, SS)
    return m


def pts_scaled(pts, ss=SS):
    return [(x * ss, y * ss) for x, y in pts]


def edge_dilate(arr):
    """Fill transparent RGB from the nearest opaque pixel (kills white fringes)."""
    a = arr[..., 3]
    if a.min() > 0:
        return arr
    _, inds = distance_transform_edt(a == 0, return_indices=True)
    out = arr.copy()
    zero = a == 0
    out[zero] = arr[inds[0][zero], inds[1][zero]]
    out[..., 3] = a
    return out


def paint_cel(mask, base, lit, shade, ink, ink_w=9.333, rim_w=14.0,
              rim_color=(255, 240, 225), rim_strength=0.5,
              crescent=0.25, volume=0.28, spec=None, pressure=0.0, tint=None):
    """Composite one flat cel from a silhouette mask.

    base/lit/shade/ink are RGB tuples. ink_w and rim_w are in design pixels.
    spec is an optional (cx, cy, rx, ry, strength) soft highlight in design px.
    tint is an optional environment bounce multiply (RGB 0-255).
    """
    w, h = mask.size
    m = np.asarray(mask, dtype=np.float64) / 255.0
    solid = m > 0.5
    if not solid.any():
        return Image.new("RGBA", (w // SS, h // SS), (0, 0, 0, 0))
    dist = distance_transform_edt(solid)

    ys, xs = np.mgrid[0:h, 0:w]
    cx, cy = xs[solid].mean(), ys[solid].mean()
    rx = max((xs[solid].max() - xs[solid].min()) / 2, 1)
    ry = max((ys[solid].max() - ys[solid].min()) / 2, 1)
    nx = (xs - cx) / rx
    ny = (ys - cy) / ry

    # directional pressure: heavier ink on the lower/shaded edge
    t = np.clip(0.62 * nx + 0.78 * ny, -1, 1)
    wmap = (ink_w * SS) * (1.0 - pressure * 0.5 + pressure * (t * 0.5 + 0.5))
    inner = (dist > wmap) & solid
    band = solid & ~inner

    # painted volume: lit top-left -> darker bottom-right, plus radial roundness
    lin = np.clip(((-nx - ny) * 0.5 + 1) * 0.5, 0, 1)
    rad = np.clip(1 - np.sqrt(nx ** 2 + ny ** 2), 0, 1)
    g = (1 - volume) + volume * (0.62 * lin + 0.38 * rad)
    lit_a, base_a, shade_a = np.array(lit), np.array(base), np.array(shade)
    rgb = np.where(g[..., None] > 0.5,
                   base_a + (lit_a - base_a) * ((g[..., None] - 0.5) * 2),
                   base_a + (shade_a - base_a) * ((0.5 - g[..., None]) * 2))
    rgb = np.clip(rgb, 0, 255)
    if tint is not None:
        rgb = np.clip(rgb * (np.array(tint, dtype=np.float64) / 255.0), 0, 255)

    # 25% burgundy crescent clipped to the inner paint mask, soft bottom-left edge
    if crescent > 0:
        im = Image.fromarray((inner * 255).astype(np.uint8))
        sh = Image.new("L", im.size, 0)
        off = (int(0.030 * w), int(-0.024 * h))
        sh.paste(im, off)
        cr = np.asarray(Image.fromarray(np.asarray(im, dtype=np.int16).__sub__(
            np.asarray(sh, dtype=np.int16)).clip(0, 255).astype(np.uint8))
            .filter(ImageFilter.GaussianBlur(3 * SS)), dtype=np.float64) / 255.0
        cr = cr * inner
        cool = np.array([92, 29, 36], dtype=np.float64)
        k = (crescent * cr)[..., None]
        rgb = rgb * (1 - k) + cool * k

    if spec is not None:
        sx, sy, srx, sry, sst = spec
        d2 = ((xs - sx * SS) / (srx * SS)) ** 2 + ((ys - sy * SS) / (sry * SS)) ** 2
        sp = np.clip(1 - d2, 0, 1) ** 1.6 * sst * inner
        rgb = rgb * (1 - sp[..., None]) + 255 * sp[..., None]

    rgb = np.clip(rgb, 0, 255)
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = rgb.astype(np.uint8)
    out[..., 3] = (inner * 255).astype(np.uint8)

    ink_rgba = np.zeros((h, w, 4), dtype=np.uint8)
    ink_rgba[..., :3] = np.array(ink, dtype=np.uint8)
    ink_rgba[..., 3] = (band * 255).astype(np.uint8)
    base_img = Image.fromarray(out)
    base_img = Image.alpha_composite(base_img, Image.fromarray(ink_rgba))

    # soft interior gradient highlight hugging the inside of the ink contour:
    # rim light reads as a gentle falloff, never a second coloured outline
    if rim_w > 0 and rim_strength > 0:
        fall = np.clip(1 - (dist - ink_w * SS) / (rim_w * SS), 0, 1) ** 2
        rim_zone = (dist > ink_w * SS) & solid
        lit_side = np.clip((-nx - ny) * 0.5 + 0.5, 0, 1)
        ra = rim_zone * fall * (0.35 + 0.65 * lit_side) * rim_strength * 255
        rim_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rim_rgba[..., :3] = np.array(rim_color, dtype=np.uint8)
        rim_rgba[..., 3] = np.clip(ra, 0, 255).astype(np.uint8)
        base_img = Image.alpha_composite(base_img, Image.fromarray(rim_rgba))

    arr = edge_dilate(np.asarray(base_img))
    return Image.fromarray(arr).resize((int(w // SS * OUT_SCALE),
                                        int(h // SS * OUT_SCALE)), Image.LANCZOS)


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path