"""Fast pre-render scene guardrail module for the Rick's Clips Blender 4.2 pipeline.

Usable in two modes:
  1. Pure-Python (NO `bpy` required at import time) — host unit tests, CI checks,
     and expression-pair pixel-lock verification:
       - `check_head_ratio(width_m, height_m, ...)`
       - `check_frustum_points(ndc_points, ...)`
       - `check_limb_stretch(actual_len, rest_len, ...)`
       - `check_facing_dot(forward_xy, to_cam_xy, ...)`
       - `check_upper_face_pixel_lock(img_closed, img_open, ...)`
       - `audit_scene(scene, ...)` (works on real Blender scenes AND mocks)
       - `format_report(report)`
  2. Inside Blender 4.2 LTS (`bpy` available) — fast pre-render gate called right
     before GPU rendering or via CLI:
       blender -b --factory-startup --python scripts/ricks_guardrails.py -- \\
           --blend renders/my_short/v01/scene.blend --frames 1,30,60

Every failed check emits a structured issue dict with a concrete `fix_hint` so
any agent can fix the exact defect on the first try without burning GPU minutes.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any, Iterable, Sequence
import zlib

try:
    import bpy  # type: ignore
    from mathutils import Vector  # type: ignore
    from bpy_extras.object_utils import world_to_camera_view  # type: ignore
except ModuleNotFoundError as _exc:
    if _exc.name not in {"bpy", "mathutils", "bpy_extras"}:
        raise
    bpy = None
    Vector = None
    world_to_camera_view = None


DEFAULT_MIN_HEAD_RATIO = 0.98
DEFAULT_MAX_HEAD_RATIO = 1.12
DEFAULT_MAX_ARM_STRETCH = 1.25
DEFAULT_MAX_LEG_STRETCH = 1.25
DEFAULT_MIN_FACING_DOT = 0.15
DEFAULT_FRUSTUM_MARGIN = 0.04
DEFAULT_MAX_TRIS = 150000
DEFAULT_SPLIT_Y_FRAC = 0.55
# Official Mascot shoulder-to-hand_socket reference reach (palm socket sits ~0.045m past wrist;
# with max_arm_stretch=1.25 this permits up to 0.525m for foreshortened poses like stop_hold_up
# at 0.465m & pickup_and_present at ~0.485m while still catching detached sockets > 0.525m).
MASCOT_HAND_SOCKET_REST_LEN = 0.42


# ---------------------------------------------------------------------------
# Pure-Python guardrail primitives
# ---------------------------------------------------------------------------

def check_head_ratio(
    width_m: float,
    height_m: float,
    *,
    min_ratio: float = DEFAULT_MIN_HEAD_RATIO,
    max_ratio: float = DEFAULT_MAX_HEAD_RATIO,
    obj_name: str = "Head",
) -> dict[str, Any]:
    """Validate character head height/width ratio (bans squashed horizontal ovals).

    Healthy upright / 1:1 heads satisfy `0.98 <= height_m / width_m <= 1.12`
    (Official Mascot tight invariant is `1.00 <= H/W <= 1.05`).
    """
    w = float(width_m)
    h = float(height_m)
    if w <= 0.0 or h <= 0.0 or not (math.isfinite(w) and math.isfinite(h)):
        return {
            "pass": False,
            "check": "head_ratio",
            "severity": "error",
            "frame": None,
            "object": obj_name,
            "width_m": w,
            "height_m": h,
            "ratio": 0.0,
            "min_ratio": float(min_ratio),
            "max_ratio": float(max_ratio),
            "detail": f"Invalid non-positive head dimensions: width_m={w:.4f}, height_m={h:.4f}.",
            "fix_hint": (
                f"Ensure '{obj_name}' has positive non-zero scale and use kit.ROUND_HEAD "
                "(0.235, 0.205, 0.235) or kit.UPRIGHT_HEAD (0.230, 0.205, 0.238)."
            ),
        }

    ratio = h / w
    if ratio < min_ratio:
        return {
            "pass": False,
            "check": "head_ratio",
            "severity": "error",
            "frame": None,
            "object": obj_name,
            "width_m": w,
            "height_m": h,
            "ratio": ratio,
            "min_ratio": float(min_ratio),
            "max_ratio": float(max_ratio),
            "detail": (
                f"Squashed horizontal oval head detected on '{obj_name}': "
                f"H/W={ratio:.3f} (width={w:.3f}m, height={h:.3f}m) < min {min_ratio:.2f}."
            ),
            "fix_hint": (
                f"Pass head_radii=kit.ROUND_HEAD (or kit.UPRIGHT_HEAD) to build_ricks_character(), "
                f"call kit.normalize_head_proportions(rig, radii=kit.ROUND_HEAD), or remove "
                f"horizontal squash scaling on '{obj_name}'. For Official Mascot keep H/W in [1.00, 1.05]."
            ),
        }
    if ratio > max_ratio:
        return {
            "pass": False,
            "check": "head_ratio",
            "severity": "error",
            "frame": None,
            "object": obj_name,
            "width_m": w,
            "height_m": h,
            "ratio": ratio,
            "min_ratio": float(min_ratio),
            "max_ratio": float(max_ratio),
            "detail": (
                f"Over-elongated vertical head on '{obj_name}': "
                f"H/W={ratio:.3f} (width={w:.3f}m, height={h:.3f}m) > max {max_ratio:.2f}."
            ),
            "fix_hint": (
                f"Clamp Z-stretch on '{obj_name}' or call kit.normalize_head_proportions(rig, "
                "radii=kit.UPRIGHT_HEAD) so height_m / width_m stays within "
                f"[{min_ratio:.2f}, {max_ratio:.2f}]."
            ),
        }

    return {
        "pass": True,
        "check": "head_ratio",
        "severity": "ok",
        "frame": None,
        "object": obj_name,
        "width_m": w,
        "height_m": h,
        "ratio": ratio,
        "min_ratio": float(min_ratio),
        "max_ratio": float(max_ratio),
        "detail": f"Head ratio H/W={ratio:.3f} within [{min_ratio:.2f}, {max_ratio:.2f}].",
        "fix_hint": "",
    }


def check_frustum_points(
    ndc_points: Iterable[Sequence[float]],
    *,
    margin: float = DEFAULT_FRUSTUM_MARGIN,
    obj_name: str = "Subject",
    frame: int = 1,
) -> dict[str, Any]:
    """Validate 9:16 normalized camera-view coordinates against frustum clipping & edge bleed.

    Expects points in Blender's `world_to_camera_view` convention:
      - `0.0 <= x <= 1.0` (left to right)
      - `0.0 <= y <= 1.0` (bottom to top)
      - `z > 0.0` (in front of camera; omitted 3rd coord defaults to `1.0`)
    All points must stay inside `[margin, 1.0 - margin]` on X and Y with `z > 0`.
    """
    pts: list[tuple[float, float, float]] = []
    for raw in ndc_points:
        if len(raw) == 2:
            pts.append((float(raw[0]), float(raw[1]), 1.0))
        elif len(raw) >= 3:
            pts.append((float(raw[0]), float(raw[1]), float(raw[2])))
        else:
            raise ValueError(f"Expected 2D or 3D NDC point, got {raw!r}")

    if not pts:
        return {
            "pass": False,
            "check": "frustum_clipping",
            "severity": "error",
            "frame": int(frame),
            "object": obj_name,
            "bounds": None,
            "violations": ["empty_points"],
            "detail": f"No frustum sample points provided for '{obj_name}' at frame {frame}.",
            "fix_hint": f"Ensure '{obj_name}' has evaluated geometry or pass valid bounding points.",
        }

    m = float(margin)
    if m < 0.0 or m >= 0.5:
        raise ValueError(f"margin must be in [0.0, 0.5), got {margin!r}")

    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    zs = [p[2] for p in pts]
    bounds = {
        "min_x": min(xs),
        "max_x": max(xs),
        "min_y": min(ys),
        "max_y": max(ys),
        "min_z": min(zs),
        "max_z": max(zs),
    }

    violations: list[str] = []
    directions: list[str] = []
    if bounds["min_z"] <= 0.0:
        violations.append("behind_camera")
        directions.append("move camera back or reposition subject in front of lens")
    if bounds["min_x"] < 0.0:
        violations.append("clipped_left")
        directions.append("pan left / shift subject +X")
    elif bounds["min_x"] < m:
        violations.append("margin_bleed_left")
        directions.append("add left safe margin")
    if bounds["max_x"] > 1.0:
        violations.append("clipped_right")
        directions.append("pan right / shift subject -X")
    elif bounds["max_x"] > 1.0 - m:
        violations.append("margin_bleed_right")
        directions.append("add right safe margin")
    if bounds["min_y"] < 0.0:
        violations.append("clipped_bottom")
        directions.append("tilt down / pull back")
    elif bounds["min_y"] < m:
        violations.append("margin_bleed_bottom")
        directions.append("add bottom safe margin")
    if bounds["max_y"] > 1.0:
        violations.append("clipped_top")
        directions.append("tilt up / pull back")
    elif bounds["max_y"] > 1.0 - m:
        violations.append("margin_bleed_top")
        directions.append("add top safe margin")

    if violations:
        return {
            "pass": False,
            "check": "frustum_clipping",
            "severity": "error",
            "frame": int(frame),
            "object": obj_name,
            "bounds": bounds,
            "violations": violations,
            "detail": (
                f"'{obj_name}' fails 9:16 frustum safe zone (margin={m:.2f}) at frame {frame}: "
                f"{', '.join(violations)} "
                f"(x=[{bounds['min_x']:.3f}, {bounds['max_x']:.3f}], "
                f"y=[{bounds['min_y']:.3f}, {bounds['max_y']:.3f}], "
                f"min_z={bounds['min_z']:.3f})."
            ),
            "fix_hint": (
                f"Reframe camera at frame {frame} ({'; '.join(directions)}), pull camera back "
                "or widen focal length into the 26-28 mm diorama range so the full subject stays "
                f"within [{m:.2f}, {1.0 - m:.2f}] NDC."
            ),
        }

    return {
        "pass": True,
        "check": "frustum_clipping",
        "severity": "ok",
        "frame": int(frame),
        "object": obj_name,
        "bounds": bounds,
        "violations": [],
        "detail": (
            f"'{obj_name}' safely inside 9:16 frustum at frame {frame} "
            f"(x=[{bounds['min_x']:.3f}, {bounds['max_x']:.3f}], "
            f"y=[{bounds['min_y']:.3f}, {bounds['max_y']:.3f}])."
        ),
        "fix_hint": "",
    }


def check_limb_stretch(
    actual_len: float,
    rest_len: float,
    *,
    max_ratio: float = DEFAULT_MAX_ARM_STRETCH,
    obj_name: str = "Limb",
    frame: int = 1,
) -> dict[str, Any]:
    """Detect stretched noodle limbs or detached shoulder/hip joints."""
    actual = float(actual_len)
    rest = float(rest_len)
    limit = float(max_ratio)

    if rest <= 0.0 or actual < 0.0 or not (math.isfinite(actual) and math.isfinite(rest)):
        return {
            "pass": False,
            "check": "limb_stretch",
            "severity": "error",
            "frame": int(frame),
            "object": obj_name,
            "actual_len": actual,
            "rest_len": rest,
            "ratio": 0.0,
            "max_ratio": limit,
            "detail": (
                f"Invalid limb lengths on '{obj_name}' at frame {frame}: "
                f"actual_len={actual:.4f}m, rest_len={rest:.4f}m."
            ),
            "fix_hint": (
                f"Measure standing reference lengths with rig.measure_leg_lengths() / rest pose "
                f"before posing '{obj_name}'."
            ),
        }

    if actual <= 1e-6:
        return {
            "pass": False,
            "check": "limb_stretch",
            "severity": "error",
            "frame": int(frame),
            "object": obj_name,
            "actual_len": actual,
            "rest_len": rest,
            "ratio": 0.0,
            "max_ratio": limit,
            "detail": (
                f"Collapsed zero-length limb on '{obj_name}' at frame {frame} "
                f"(actual={actual:.4f}m, rest={rest:.4f}m)."
            ),
            "fix_hint": (
                f"Separate shoulder/elbow/hand or hip/knee/foot control points on '{obj_name}' "
                f"at frame {frame} so the limb curve does not collapse to a point."
            ),
        }

    ratio = actual / rest
    if ratio > limit:
        max_allowed_m = rest * limit
        return {
            "pass": False,
            "check": "limb_stretch",
            "severity": "error",
            "frame": int(frame),
            "object": obj_name,
            "actual_len": actual,
            "rest_len": rest,
            "ratio": ratio,
            "max_ratio": limit,
            "detail": (
                f"Over-stretched/detached limb on '{obj_name}' at frame {frame}: "
                f"actual={actual:.3f}m vs rest={rest:.3f}m (ratio={ratio:.2f}x > max {limit:.2f}x)."
            ),
            "fix_hint": (
                f"Bring '{obj_name}' end target within <= {max_allowed_m:.3f}m of its joint at "
                f"frame {frame}, move rig.root/body closer to the prop, or pass measured "
                "`leg_lengths=rig.measure_leg_lengths()` to rig.pose()."
            ),
        }

    return {
        "pass": True,
        "check": "limb_stretch",
        "severity": "ok",
        "frame": int(frame),
        "object": obj_name,
        "actual_len": actual,
        "rest_len": rest,
        "ratio": ratio,
        "max_ratio": limit,
        "detail": (
            f"'{obj_name}' length ratio={ratio:.2f}x <= {limit:.2f}x "
            f"(actual={actual:.3f}m, rest={rest:.3f}m)."
        ),
        "fix_hint": "",
    }


def check_facing_dot(
    forward_xy: Sequence[float],
    to_cam_xy: Sequence[float],
    *,
    min_dot: float = DEFAULT_MIN_FACING_DOT,
    obj_name: str = "Actor",
    frame: int = 1,
) -> dict[str, Any]:
    """Detect actors accidentally turned away from camera (blank back-of-head)."""
    fx, fy = float(forward_xy[0]), float(forward_xy[1])
    cx, cy = float(to_cam_xy[0]), float(to_cam_xy[1])
    f_len = math.hypot(fx, fy)
    c_len = math.hypot(cx, cy)

    if f_len <= 1e-8 or c_len <= 1e-8 or not (math.isfinite(f_len) and math.isfinite(c_len)):
        return {
            "pass": False,
            "check": "facing_camera",
            "severity": "error",
            "frame": int(frame),
            "object": obj_name,
            "dot": 0.0,
            "min_dot": float(min_dot),
            "angle_deg": 90.0,
            "detail": (
                f"Degenerate XY facing/camera vector for '{obj_name}' at frame {frame} "
                f"(|forward|={f_len:.4f}, |to_cam|={c_len:.4f})."
            ),
            "fix_hint": (
                f"Ensure '{obj_name}' and the active camera are not directly stacked vertically "
                "on the exact same XY coordinate."
            ),
        }

    dot = max(-1.0, min(1.0, (fx * cx + fy * cy) / (f_len * c_len)))
    angle_deg = math.degrees(math.acos(dot))

    if dot < min_dot:
        return {
            "pass": False,
            "check": "facing_camera",
            "severity": "error",
            "frame": int(frame),
            "object": obj_name,
            "dot": dot,
            "min_dot": float(min_dot),
            "angle_deg": angle_deg,
            "detail": (
                f"'{obj_name}' is turned away from the camera at frame {frame} "
                f"(dot={dot:.3f} < min {min_dot:.2f}, off-axis={angle_deg:.1f} deg)."
            ),
            "fix_hint": (
                f"Rotate '{obj_name}' `yaw` or `head_yaw` so local -Y faces toward the camera "
                f"(dot >= {min_dot:.2f}), or pass `allow_back_view=('{obj_name}',)` if an "
                "over-the-shoulder / back-view shot is intentional."
            ),
        }

    return {
        "pass": True,
        "check": "facing_camera",
        "severity": "ok",
        "frame": int(frame),
        "object": obj_name,
        "dot": dot,
        "min_dot": float(min_dot),
        "angle_deg": angle_deg,
        "detail": (
            f"'{obj_name}' faces camera at frame {frame} "
            f"(dot={dot:.3f} >= {min_dot:.2f}, angle={angle_deg:.1f} deg)."
        ),
        "fix_hint": "",
    }


def _read_png_rgba_stdlib(path: Path) -> tuple[int, int, Any, bool]:
    """Decode an 8-bit non-interlaced PNG to RGBA without Pillow (stock Blender 4.2 safe)."""
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Unsupported image format without Pillow (expected PNG): {path}")

    pos = 8
    width = height = bit_depth = color_type = interlace = 0
    idat_parts: list[bytes] = []
    while pos + 8 <= len(raw):
        length = struct.unpack(">I", raw[pos:pos + 4])[0]
        ctype = raw[pos + 4:pos + 8]
        chunk = raw[pos + 8:pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filt, interlace = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"IDAT":
            idat_parts.append(chunk)
        elif ctype == b"IEND":
            break

    if bit_depth != 8 or interlace != 0 or color_type not in (0, 2, 4, 6):
        raise ValueError(
            f"Unsupported PNG variant without Pillow (bit_depth={bit_depth}, "
            f"color_type={color_type}, interlace={interlace}): {path}"
        )

    bpp_map = {0: 1, 2: 3, 4: 2, 6: 4}
    bpp = bpp_map[color_type]
    stride = width * bpp
    decomp = zlib.decompress(b"".join(idat_parts))

    prev = bytearray(stride)
    out = bytearray(width * height * 4)
    src = 0
    for y in range(height):
        ftype = decomp[src]
        src += 1
        row = bytearray(decomp[src:src + stride])
        src += stride
        if ftype == 1:  # Sub
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif ftype == 2:  # Up
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif ftype == 3:  # Average
            for i in range(stride):
                left = row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:  # Paeth
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF
        elif ftype != 0:
            raise ValueError(f"Unknown PNG filter type {ftype} in {path}")

        dst = y * width * 4
        if color_type == 6:
            out[dst:dst + width * 4] = row
        elif color_type == 2:
            for x in range(width):
                si, di = x * 3, dst + x * 4
                out[di] = row[si]
                out[di + 1] = row[si + 1]
                out[di + 2] = row[si + 2]
                out[di + 3] = 255
        elif color_type == 4:
            for x in range(width):
                si, di = x * 2, dst + x * 4
                g = row[si]
                out[di] = out[di + 1] = out[di + 2] = g
                out[di + 3] = row[si + 1]
        else:  # color_type == 0
            for x in range(width):
                di = dst + x * 4
                g = row[x]
                out[di] = out[di + 1] = out[di + 2] = g
                out[di + 3] = 255
        prev = row

    try:
        import numpy as np
        arr = np.frombuffer(out, dtype=np.uint8).reshape((height, width, 4)).astype(np.int16)
        return width, height, arr, True
    except ModuleNotFoundError:
        rows = [
            [tuple(out[(y * width + x) * 4:(y * width + x) * 4 + 4]) for x in range(width)]
            for y in range(height)
        ]
        return width, height, rows, False


def _load_image_rgba_rows(img: Any) -> tuple[int, int, Any, bool]:
    """Return `(width, height, data, is_numpy)` from path, PIL Image, ndarray, or nested list."""
    # Path or string -> PIL Image (with pure-Python stdlib PNG fallback for stock Blender 4.2)
    if isinstance(img, (str, Path)):
        try:
            from PIL import Image
        except ModuleNotFoundError:
            return _read_png_rgba_stdlib(Path(img))
        with Image.open(img) as im:
            rgba = im.convert("RGBA")
            w, h = rgba.size
            try:
                import numpy as np
                return w, h, np.asarray(rgba, dtype=np.int16), True
            except ModuleNotFoundError:
                raw = list(rgba.getdata())
                rows = [raw[r * w:(r + 1) * w] for r in range(h)]
                return w, h, rows, False

    # PIL Image duck-typing
    if hasattr(img, "convert") and hasattr(img, "size"):
        rgba = img.convert("RGBA")
        w, h = rgba.size
        try:
            import numpy as np
            return w, h, np.asarray(rgba, dtype=np.int16), True
        except ModuleNotFoundError:
            raw = list(rgba.getdata())
            rows = [raw[r * w:(r + 1) * w] for r in range(h)]
            return w, h, rows, False

    # NumPy array duck-typing
    if hasattr(img, "shape") and hasattr(img, "dtype"):
        import numpy as np
        arr = np.asarray(img, dtype=np.int16)
        if arr.ndim == 2:
            h, w = arr.shape
            arr = arr[:, :, None]
        elif arr.ndim == 3:
            h, w = arr.shape[0], arr.shape[1]
        else:
            raise ValueError(f"Expected 2D or 3D image array, got shape {arr.shape}")
        return int(w), int(h), arr, True

    # Pure-Python nested sequences: rows[y][x] -> pixel int or tuple
    rows = list(img)
    h = len(rows)
    w = len(rows[0]) if h > 0 else 0
    return w, h, rows, False


def check_upper_face_pixel_lock(
    img_closed: Any,
    img_open: Any,
    *,
    split_y_frac: float = DEFAULT_SPLIT_Y_FRAC,
    max_abs_diff: int = 0,
) -> dict[str, Any]:
    """Verify closed/talk expression plates are pixel-locked above `split_y_frac`.

    Eliminates syllable eye-flutter by guaranteeing zero pixel drift in the upper
    face (`y < split_y_frac * height`, eyes & brows region) between mouth swaps.
    Accepts file paths, PIL Images, NumPy arrays, or nested Python pixel lists.
    """
    frac = float(split_y_frac)
    if not (0.0 < frac <= 1.0):
        raise ValueError(f"split_y_frac must be in (0.0, 1.0], got {split_y_frac!r}")
    tol = int(max_abs_diff)
    if tol < 0:
        raise ValueError(f"max_abs_diff must be >= 0, got {max_abs_diff!r}")

    w1, h1, data1, np1 = _load_image_rgba_rows(img_closed)
    w2, h2, data2, np2 = _load_image_rgba_rows(img_open)

    if (w1, h1) != (w2, h2) or w1 <= 0 or h1 <= 0:
        return {
            "pass": False,
            "check": "upper_face_pixel_lock",
            "severity": "error",
            "frame": None,
            "object": "ExpressionPair",
            "split_y_frac": frac,
            "upper_rows": 0,
            "max_diff": -1,
            "max_abs_diff": tol,
            "changed_pixels": -1,
            "detail": (
                f"Expression plate size mismatch or empty image: "
                f"closed=({w1}x{h1}) vs open=({w2}x{h2})."
            ),
            "fix_hint": (
                "Render both closed and open mouth expressions at identical resolution "
                "(e.g. 1024x1024 RGBA) using kit.render_pixel_locked_expression_pair()."
            ),
        }

    upper_rows = max(1, int(h1 * frac))
    if np1 and np2:
        import numpy as np
        if data1.shape != data2.shape:
            return {
                "pass": False,
                "check": "upper_face_pixel_lock",
                "severity": "error",
                "frame": None,
                "object": "ExpressionPair",
                "split_y_frac": frac,
                "upper_rows": upper_rows,
                "max_diff": -1,
                "max_abs_diff": tol,
                "changed_pixels": -1,
                "detail": (
                    f"Channel count mismatch: closed={data1.shape} vs open={data2.shape}."
                ),
                "fix_hint": "Convert both expression decals to RGBA before comparing.",
            }
        diff = np.abs(data1[:upper_rows] - data2[:upper_rows])
        max_diff = int(diff.max()) if diff.size else 0
        per_pixel_max = diff.max(axis=-1)
        changed_pixels = int(np.count_nonzero(per_pixel_max > tol))
    else:
        max_diff = 0
        changed_pixels = 0
        for y in range(upper_rows):
            r1, r2 = data1[y], data2[y]
            for x in range(w1):
                p1, p2 = r1[x], r2[x]
                if isinstance(p1, (tuple, list)):
                    d = max(abs(int(a) - int(b)) for a, b in zip(p1, p2))
                else:
                    d = abs(int(p1) - int(p2))
                if d > max_diff:
                    max_diff = d
                if d > tol:
                    changed_pixels += 1

    passed = max_diff <= tol
    if not passed:
        return {
            "pass": False,
            "check": "upper_face_pixel_lock",
            "severity": "error",
            "frame": None,
            "object": "ExpressionPair",
            "split_y_frac": frac,
            "upper_rows": upper_rows,
            "max_diff": max_diff,
            "max_abs_diff": tol,
            "changed_pixels": changed_pixels,
            "detail": (
                f"Syllable eye-flutter detected: upper {int(frac * 100)}% of face "
                f"(rows 0..{upper_rows - 1}) has {changed_pixels} changed pixels "
                f"(max channel abs diff={max_diff} > allowed {tol})."
            ),
            "fix_hint": (
                "Generate talking expression pairs with kit.render_pixel_locked_expression_pair() "
                f"or copy/composite rows 0..{upper_rows - 1} identically from the closed base "
                "expression so eyes and brows never shift during lip-sync."
            ),
        }

    return {
        "pass": True,
        "check": "upper_face_pixel_lock",
        "severity": "ok",
        "frame": None,
        "object": "ExpressionPair",
        "split_y_frac": frac,
        "upper_rows": upper_rows,
        "max_diff": max_diff,
        "max_abs_diff": tol,
        "changed_pixels": changed_pixels,
        "detail": (
            f"Upper {int(frac * 100)}% face pixel-locked (rows 0..{upper_rows - 1}, "
            f"max_diff={max_diff} <= {tol})."
        ),
        "fix_hint": "",
    }


# ---------------------------------------------------------------------------
# Internal scene/rig inspection helpers (Blender + mock-compatible)
# ---------------------------------------------------------------------------

def _record_if_failed(issues: list[dict[str, Any]], res: dict[str, Any]) -> None:
    if not res.get("pass", True):
        issues.append({
            "check": res["check"],
            "severity": res.get("severity", "error"),
            "frame": res.get("frame"),
            "object": res.get("object", "Scene"),
            "detail": res["detail"],
            "fix_hint": res.get("fix_hint", ""),
        })


def _make_issue(
    check: str,
    obj: str,
    detail: str,
    fix_hint: str,
    *,
    severity: str = "error",
    frame: int | None = None,
) -> dict[str, Any]:
    return {
        "check": check,
        "severity": severity,
        "frame": frame,
        "object": obj,
        "detail": detail,
        "fix_hint": fix_hint,
    }


def _check_eevee_contract(
    scene: Any,
    *,
    expect_deep_focus: bool,
    max_tris: int,
) -> tuple[list[dict[str, Any]], int | None]:
    issues: list[dict[str, Any]] = []
    render = getattr(scene, "render", None)
    eevee = getattr(scene, "eevee", None)
    cam = getattr(scene, "camera", None)
    scene_name = getattr(scene, "name", "Scene")

    if render is not None:
        engine = getattr(render, "engine", None)
        if engine != "BLENDER_EEVEE_NEXT":
            issues.append(_make_issue(
                "eevee_contract",
                scene_name,
                f"Render engine is {engine!r}, expected 'BLENDER_EEVEE_NEXT'.",
                "Set `scene.render.engine = 'BLENDER_EEVEE_NEXT'` (never Cycles or legacy EEVEE).",
            ))
        rx = getattr(render, "resolution_x", None)
        ry = getattr(render, "resolution_y", None)
        rp = getattr(render, "resolution_percentage", 100)
        if (rx, ry, rp) != (1080, 1920, 100):
            issues.append(_make_issue(
                "eevee_contract",
                scene_name,
                f"Delivery resolution is {rx}x{ry} @ {rp}%, expected native 1080x1920 @ 100%.",
                (
                    "Set `scene.render.resolution_x = 1080; scene.render.resolution_y = 1920; "
                    "scene.render.resolution_percentage = 100`."
                ),
            ))
        fps = getattr(render, "fps", None)
        fps_base = getattr(render, "fps_base", 1.0)
        if fps != 30 or abs(float(fps_base) - 1.0) > 1e-6:
            issues.append(_make_issue(
                "eevee_contract",
                scene_name,
                f"Frame rate is {fps}/{fps_base}, expected 30 fps (fps=30, fps_base=1.0).",
                "Set `scene.render.fps = 30; scene.render.fps_base = 1.0`.",
            ))

    if eevee is not None:
        if getattr(eevee, "use_raytracing", False):
            issues.append(_make_issue(
                "eevee_contract",
                scene_name,
                "EEVEE Next raytracing is enabled (`use_raytracing=True`), violating RTX 3050 budget.",
                "Set `scene.eevee.use_raytracing = False` and use `fast_gi_method = 'AMBIENT_OCCLUSION_ONLY'`.",
            ))

    if cam is None:
        issues.append(_make_issue(
            "eevee_contract",
            scene_name,
            "Scene has no active `scene.camera`.",
            "Assign a 9:16 camera via `scene.camera = camera` or `kit.setup_diorama_camera_and_compositor(scene)`.",
        ))
    else:
        cam_data = getattr(cam, "data", None)
        dof = getattr(cam_data, "dof", None) if cam_data is not None else None
        if expect_deep_focus and dof is not None and getattr(dof, "use_dof", False):
            issues.append(_make_issue(
                "eevee_contract",
                getattr(cam, "name", "Camera"),
                "Camera DOF is enabled (`use_dof=True`) while deep focus is expected.",
                (
                    "Call `kit.setup_diorama_camera_and_compositor(scene, camera)` or set "
                    "`camera.data.dof.use_dof = False` AFTER `kit.setup_ricks_compositor()`."
                ),
            ))

    visible_tris = _measure_visible_triangles(scene)
    if visible_tris is not None and visible_tris >= max_tris:
        issues.append(_make_issue(
            "triangle_budget",
            scene_name,
            f"Evaluated visible triangles ({visible_tris:,}) >= budget ({max_tris:,}).",
            (
                f"Reduce subdivision levels, merge/decimate heavy set props, or run "
                f"`shorts_preflight.sanitize_assets(scene, ..., target_tris={max_tris})` so "
                f"visible triangles stay strictly below {max_tris:,}."
            ),
        ))

    return issues, visible_tris


def _measure_visible_triangles(scene: Any) -> int | None:
    mock_tris = getattr(scene, "_mock_visible_triangles", None)
    if mock_tris is not None:
        return int(mock_tris)
    if bpy is not None and getattr(bpy.context, "scene", None) == scene:
        try:
            deps = bpy.context.evaluated_depsgraph_get()
            total = 0
            for inst in deps.object_instances:
                obj = inst.object
                if obj.type != "MESH" or obj.hide_render or not inst.show_self:
                    continue
                mesh = obj.to_mesh()
                try:
                    mesh.calc_loop_triangles()
                    total += len(mesh.loop_triangles)
                finally:
                    obj.to_mesh_clear()
            return total
        except Exception:
            return None
    return None


def _check_viewport_render_parity(scene: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    def walk_collection(col: Any) -> None:
        if col is None:
            return
        hv = bool(getattr(col, "hide_viewport", False))
        hr = bool(getattr(col, "hide_render", False))
        if hv != hr:
            name = getattr(col, "name", "<Collection>")
            issues.append(_make_issue(
                "viewport_render_parity",
                name,
                f"Collection '{name}' visibility mismatch: hide_viewport={hv} != hide_render={hr}.",
                f"Align collection visibility: `col.hide_viewport = col.hide_render` on '{name}'.",
            ))
        for child in getattr(col, "children", ()):
            walk_collection(child)

    walk_collection(getattr(scene, "collection", None))

    for obj in getattr(scene, "objects", ()):
        name = getattr(obj, "name", "<Object>")
        hv = bool(getattr(obj, "hide_viewport", False))
        hr = bool(getattr(obj, "hide_render", False))
        if hv != hr:
            issues.append(_make_issue(
                "viewport_render_parity",
                name,
                f"Object '{name}' visibility mismatch: hide_viewport={hv} != hide_render={hr}.",
                (
                    f"Set `obj.hide_viewport = obj.hide_render` on '{name}' and keyframe both "
                    "channels together with CONSTANT interpolation."
                ),
            ))
        for mod in getattr(obj, "modifiers", ()):
            mname = getattr(mod, "name", "<Modifier>")
            sv = bool(getattr(mod, "show_viewport", True))
            sr = bool(getattr(mod, "show_render", True))
            if sv != sr:
                issues.append(_make_issue(
                    "viewport_render_parity",
                    f"{name}/{mname}",
                    f"Modifier '{mname}' on '{name}' mismatch: show_viewport={sv} != show_render={sr}.",
                    f"Set `mod.show_viewport = mod.show_render` on '{name}'.modifiers['{mname}'].",
                ))
            if getattr(mod, "type", None) == "SUBSURF":
                lv = int(getattr(mod, "levels", 0))
                rlv = int(getattr(mod, "render_levels", 0))
                if rlv != lv:
                    issues.append(_make_issue(
                        "viewport_render_parity",
                        f"{name}/{mname}",
                        (
                            f"Subsurf '{mname}' on '{name}' level mismatch: "
                            f"viewport levels={lv} != render_levels={rlv}."
                        ),
                        f"Set `mod.render_levels = mod.levels` on '{name}'.modifiers['{mname}'] so pre-render tri counts match GPU render.",
                    ))
    return issues


def _extract_rig_head_dims(rig: Any) -> tuple[str, float, float] | None:
    """Return `(head_obj_name, width_m, height_m)` for MascotRig, RicksCharacter, or mock."""
    rig_name = getattr(rig, "name", "Rig")

    # 1. Explicit mock or MascotRig helper (`head_bbox_ratio()`)
    if callable(getattr(rig, "head_bbox_ratio", None)):
        try:
            info = rig.head_bbox_ratio()
            if isinstance(info, dict) and "width_m" in info and "height_m" in info:
                return f"{rig_name} | Head", float(info["width_m"]), float(info["height_m"])
        except Exception:
            pass

    # 2. Pure-Python mock tuple attribute `head_dims = (w, h)`
    head_dims = getattr(rig, "head_dims", None)
    if head_dims is not None and len(head_dims) >= 2:
        return f"{rig_name} | Head", float(head_dims[0]), float(head_dims[1])

    # 3. Blender RicksCharacter / generic rig with `rig.head`
    head_ctrl = getattr(rig, "head", None)
    if head_ctrl is None:
        return None

    head_mesh = None
    if getattr(head_ctrl, "type", None) == "MESH":
        head_mesh = head_ctrl
    else:
        for child in getattr(head_ctrl, "children", ()):
            if getattr(child, "type", None) != "MESH":
                continue
            cname = getattr(child, "name", "").lower()
            if "ellipsoid head" in cname or child.get("mascot_tag") == "head_mesh":
                head_mesh = child
                break
        if head_mesh is None:
            for child in getattr(head_ctrl, "children", ()):
                if getattr(child, "type", None) == "MESH":
                    cname = getattr(child, "name", "").lower()
                    if not any(k in cname for k in ("ink", "hair", "hood", "ear", "sweat", "decal", "beanie")):
                        head_mesh = child
                        break

    if head_mesh is None or not hasattr(head_mesh, "bound_box"):
        return None

    bb = [tuple(c) for c in head_mesh.bound_box]
    if not bb:
        return None
    sx = abs(float(getattr(head_mesh.scale, "x", 1.0))) * abs(float(getattr(head_ctrl.scale, "x", 1.0))) if head_mesh is not head_ctrl else abs(float(getattr(head_mesh.scale, "x", 1.0)))
    sz = abs(float(getattr(head_mesh.scale, "z", 1.0))) * abs(float(getattr(head_ctrl.scale, "z", 1.0))) if head_mesh is not head_ctrl else abs(float(getattr(head_mesh.scale, "z", 1.0)))
    width_m = (max(c[0] for c in bb) - min(c[0] for c in bb)) * sx
    height_m = (max(c[2] for c in bb) - min(c[2] for c in bb)) * sz
    return getattr(head_mesh, "name", f"{rig_name} | Head"), width_m, height_m


def _measure_curve_length(curve_obj: Any) -> float | None:
    data = getattr(curve_obj, "data", None)
    splines = getattr(data, "splines", None) if data is not None else None
    if not splines:
        return None
    sp = splines[0]
    if callable(getattr(sp, "calc_length", None)):
        try:
            return float(sp.calc_length())
        except Exception:
            pass
    pts = getattr(sp, "bezier_points", None)
    if pts and len(pts) >= 2:
        total = 0.0
        for a, b in zip(pts[:-1], pts[1:]):
            ax, ay, az = a.co[0], a.co[1], a.co[2]
            bx, by, bz = b.co[0], b.co[1], b.co[2]
            total += math.sqrt((bx - ax) ** 2 + (by - ay) ** 2 + (bz - az) ** 2)
        return total
    return None


def _extract_rig_limb_samples(rig: Any, rest_cache: dict[str, float]) -> list[tuple[str, str, float, float]]:
    """Return list of `(kind, name, actual_len, rest_len)` where `kind` is `'arm'` or `'leg'`."""
    samples: list[tuple[str, str, float, float]] = []
    rig_name = getattr(rig, "name", "Rig")

    # Mock rig attributes: `arm_lengths=[(name, actual, rest), ...]` / `leg_lengths=[...]`
    for kind, attr in (("arm", "mock_arms"), ("leg", "mock_legs")):
        entries = getattr(rig, attr, None)
        if entries:
            for item in entries:
                lname, actual, rest = item
                samples.append((kind, str(lname), float(actual), float(rest)))

    # RicksCharacter curve limbs (`rig.arms`, `rig.legs`)
    for kind, attr, default_rest in (("arm", "arms", 0.38), ("leg", "legs", 0.66)):
        limbs = getattr(rig, attr, None) or ()
        explicit_rests = getattr(rig, f"{kind}_rest_lengths", None)
        for idx, limb in enumerate(limbs):
            actual = _measure_curve_length(limb)
            if actual is None:
                continue
            lname = getattr(limb, "name", f"{rig_name} | {kind}_{idx}")
            if explicit_rests and idx < len(explicit_rests):
                rest = float(explicit_rests[idx])
            else:
                rest = rest_cache.setdefault(lname, max(actual, default_rest))
            samples.append((kind, lname, actual, rest))

    # MascotRig sockets (`hand_socket_L/R`, `foot_L/R`, `body`, `root`)
    if getattr(rig, "hand_socket_L", None) is not None and getattr(rig, "body", None) is not None:
        body_mat = getattr(rig.body, "matrix_world", None)
        if body_mat is not None:
            for side, sh_local, sock_attr in (
                ("L", (-0.155, 0.0, 0.180), "hand_socket_L"),
                ("R", (0.155, 0.0, 0.180), "hand_socket_R"),
            ):
                sock = getattr(rig, sock_attr, None)
                if sock is not None and hasattr(sock, "matrix_world"):
                    hand_w = sock.matrix_world.translation
                    if Vector is not None:
                        sh_w = body_mat @ Vector(sh_local)
                        dist = float((hand_w - sh_w).length)
                    else:
                        bt = getattr(body_mat, "translation", (0.0, 0.0, 0.0))
                        sh_w = (bt[0] + sh_local[0], bt[1] + sh_local[1], bt[2] + sh_local[2])
                        dist = math.sqrt(
                            (hand_w[0] - sh_w[0]) ** 2
                            + (hand_w[1] - sh_w[1]) ** 2
                            + (hand_w[2] - sh_w[2]) ** 2
                        )
                    samples.append(("arm", f"{rig_name} | arm_{side}", dist, MASCOT_HAND_SOCKET_REST_LEN))

    return samples


def _extract_rig_facing(rig: Any, camera: Any) -> tuple[str, tuple[float, float], tuple[float, float]] | None:
    rig_name = getattr(rig, "name", "Rig")

    # Mock facing vectors directly attached
    if hasattr(rig, "mock_forward_xy") and hasattr(rig, "mock_to_cam_xy"):
        return rig_name, tuple(rig.mock_forward_xy), tuple(rig.mock_to_cam_xy)

    if camera is None or not hasattr(camera, "matrix_world"):
        return None

    anchor = getattr(rig, "head", None) or getattr(rig, "root", None)
    if anchor is None or not hasattr(anchor, "matrix_world"):
        return None

    mat = anchor.matrix_world
    cam_pos = camera.matrix_world.translation
    anc_pos = mat.translation

    if Vector is not None:
        fwd = mat.to_3x3() @ Vector((0.0, -1.0, 0.0))
        to_cam = cam_pos - anc_pos
        return rig_name, (float(fwd.x), float(fwd.y)), (float(to_cam.x), float(to_cam.y))

    return None


def _extract_subject_ndc_points(scene: Any, camera: Any, subject: Any) -> tuple[str, list[tuple[float, float, float]]] | None:
    name = getattr(subject, "name", "Subject")

    # Mock subject with direct `ndc_points`
    if hasattr(subject, "ndc_points"):
        pts = subject.ndc_points
        if callable(pts):
            pts = pts(getattr(scene, "frame_current", 1))
        return name, [tuple(p) for p in pts]

    if camera is None or world_to_camera_view is None or Vector is None:
        return None

    # Allow passing a rig directly in `subjects`
    targets = []
    if hasattr(subject, "bound_box") and hasattr(subject, "matrix_world"):
        targets.append(subject)
    elif hasattr(subject, "head") or hasattr(subject, "body"):
        for part_attr in ("head", "body", "root"):
            part = getattr(subject, part_attr, None)
            if part is None:
                continue
            if getattr(part, "type", None) == "MESH":
                targets.append(part)
            for child in getattr(part, "children", ()):
                if getattr(child, "type", None) == "MESH" and not getattr(child, "hide_render", False):
                    targets.append(child)

    if not targets:
        return None

    ndc_pts: list[tuple[float, float, float]] = []
    for obj in targets:
        mat = obj.matrix_world
        for corner in obj.bound_box:
            co_ndc = world_to_camera_view(scene, camera, mat @ Vector(corner))
            ndc_pts.append((float(co_ndc.x), float(co_ndc.y), float(co_ndc.z)))
    return name, ndc_pts


# ---------------------------------------------------------------------------
# Main scene audit entrypoint (LOCKED API)
# ---------------------------------------------------------------------------

def audit_scene(
    scene: Any,
    *,
    rigs: Iterable[Any] = (),
    subjects: Iterable[Any] = (),
    frames: Iterable[int] | None = None,
    expect_deep_focus: bool = True,
    min_head_ratio: float = DEFAULT_MIN_HEAD_RATIO,
    max_head_ratio: float = DEFAULT_MAX_HEAD_RATIO,
    max_arm_stretch: float = DEFAULT_MAX_ARM_STRETCH,
    max_leg_stretch: float = DEFAULT_MAX_LEG_STRETCH,
    min_facing_dot: float = DEFAULT_MIN_FACING_DOT,
    allow_back_view: Iterable[str] = (),
    margin: float = DEFAULT_FRUSTUM_MARGIN,
    max_tris: int = DEFAULT_MAX_TRIS,
) -> dict[str, Any]:
    """Run all fast pre-render guardrails on `scene` and return a structured report.

    Returns:
        {
            "pass": bool,
            "issues": [{"check", "severity", "frame", "object", "detail", "fix_hint"}, ...],
            "summary": {...},
        }
    """
    rigs_list = list(rigs)
    subjects_list = list(subjects)
    allow_back_set = {str(n) for n in allow_back_view}
    issues: list[dict[str, Any]] = []
    checks_run = ["eevee_contract", "viewport_render_parity"]

    # Determine sampled frames without mutating caller's current frame permanently
    orig_frame = getattr(scene, "frame_current", 1)
    if frames is None:
        frame_list = [int(orig_frame)]
    else:
        frame_list = [int(f) for f in frames]
        if not frame_list:
            frame_list = [int(orig_frame)]

    # 1. Static EEVEE / delivery contract & triangle budget
    eevee_issues, visible_tris = _check_eevee_contract(
        scene,
        expect_deep_focus=expect_deep_focus,
        max_tris=max_tris,
    )
    issues.extend(eevee_issues)

    # 2. Viewport vs. render parity (collections, objects, modifiers)
    issues.extend(_check_viewport_render_parity(scene))

    # 3. Rig head ratio (geometry invariant — check once per rig)
    if rigs_list:
        checks_run.extend(["head_ratio", "limb_stretch", "facing_camera"])
        for rig in rigs_list:
            head_info = _extract_rig_head_dims(rig)
            if head_info is not None:
                h_name, w_m, h_m = head_info
                res = check_head_ratio(
                    w_m,
                    h_m,
                    min_ratio=min_head_ratio,
                    max_ratio=max_head_ratio,
                    obj_name=h_name,
                )
                _record_if_failed(issues, res)

    if subjects_list:
        checks_run.append("frustum_clipping")

    # 4. Per-frame dynamic checks (limbs, facing, 9:16 frustum)
    rest_cache: dict[str, float] = {}
    camera = getattr(scene, "camera", None)
    try:
        for f in frame_list:
            if callable(getattr(scene, "frame_set", None)):
                scene.frame_set(f)
                if bpy is not None and getattr(bpy.context, "view_layer", None) is not None:
                    bpy.context.view_layer.update()

            for rig in rigs_list:
                rig_name = getattr(rig, "name", "Rig")
                for kind, lname, actual_len, rest_len in _extract_rig_limb_samples(rig, rest_cache):
                    limit = max_arm_stretch if kind == "arm" else max_leg_stretch
                    res = check_limb_stretch(
                        actual_len,
                        rest_len,
                        max_ratio=limit,
                        obj_name=lname,
                        frame=f,
                    )
                    _record_if_failed(issues, res)

                if rig_name not in allow_back_set:
                    facing = _extract_rig_facing(rig, camera)
                    if facing is not None:
                        fname, fwd_xy, to_cam_xy = facing
                        if fname not in allow_back_set:
                            res = check_facing_dot(
                                fwd_xy,
                                to_cam_xy,
                                min_dot=min_facing_dot,
                                obj_name=fname,
                                frame=f,
                            )
                            _record_if_failed(issues, res)

            for subj in subjects_list:
                extracted = _extract_subject_ndc_points(scene, camera, subj)
                if extracted is not None:
                    sname, ndc_pts = extracted
                    res = check_frustum_points(
                        ndc_pts,
                        margin=margin,
                        obj_name=sname,
                        frame=f,
                    )
                    _record_if_failed(issues, res)
    finally:
        if callable(getattr(scene, "frame_set", None)):
            scene.frame_set(orig_frame)

    error_count = sum(1 for item in issues if item.get("severity", "error") == "error")
    warning_count = sum(1 for item in issues if item.get("severity") == "warning")
    return {
        "pass": error_count == 0,
        "issues": issues,
        "summary": {
            "scene_name": getattr(scene, "name", "Scene"),
            "frames_checked": frame_list,
            "rigs_checked": len(rigs_list),
            "subjects_checked": len(subjects_list),
            "error_count": error_count,
            "warning_count": warning_count,
            "checks_run": checks_run,
            "visible_triangles": visible_tris,
        },
    }


def format_report(report: dict[str, Any]) -> str:
    """Format an `audit_scene(...)` result into a crisp human-readable terminal report."""
    summary = report.get("summary", {})
    status = "PASS" if report.get("pass") else "FAIL"
    lines = [
        f"=== Ricks Guardrails Audit: {status} ===",
        (
            f"Scene: {summary.get('scene_name', 'Scene')} | "
            f"Frames: {summary.get('frames_checked', [])} | "
            f"Errors: {summary.get('error_count', 0)} | "
            f"Warnings: {summary.get('warning_count', 0)}"
        ),
    ]
    tris = summary.get("visible_triangles")
    if tris is not None:
        lines.append(f"Visible Evaluated Triangles: {tris:,}")

    issues = report.get("issues", [])
    if not issues:
        lines.append("All pre-render guardrail checks passed with 0 issues.")
    else:
        for idx, issue in enumerate(issues, 1):
            f_tag = f"f={issue['frame']}" if issue.get("frame") is not None else "static"
            lines.append(
                f"[{idx}] ({issue.get('severity', 'error').upper()} | {issue['check']} | "
                f"{f_tag}) {issue['object']}: {issue['detail']}"
            )
            if issue.get("fix_hint"):
                lines.append(f"    FIX: {issue['fix_hint']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entrypoint (both pure-Python expression check & Blender `--blend` audit)
# ---------------------------------------------------------------------------

def _parse_cli_args(argv: Sequence[str]) -> argparse.Namespace:
    if "--" in argv:
        argv = list(argv)[list(argv).index("--") + 1:]
    parser = argparse.ArgumentParser(
        description="Pre-render scene guardrails for Rick's Clips Blender 4.2 Shorts."
    )
    parser.add_argument("--blend", type=str, default=None, help="Path to .blend file to audit (requires Blender).")
    parser.add_argument(
        "--frames",
        type=str,
        default=None,
        help="Comma-separated 1-based frames to inspect (default: start, mid, end).",
    )
    parser.add_argument("--allow-dof", action="store_true", help="Allow camera DOF (portrait shallow-DOF mode).")
    parser.add_argument("--max-tris", type=int, default=DEFAULT_MAX_TRIS, help="Maximum visible triangles budget.")
    parser.add_argument("--margin", type=float, default=DEFAULT_FRUSTUM_MARGIN, help="9:16 NDC safe margin.")
    parser.add_argument(
        "--check-expr-pair",
        nargs=2,
        metavar=("CLOSED_IMG", "OPEN_IMG"),
        default=None,
        help="Pure-Python upper-face pixel-lock check on two expression PNGs.",
    )
    parser.add_argument("--split-y-frac", type=float, default=DEFAULT_SPLIT_Y_FRAC)
    parser.add_argument("--max-abs-diff", type=int, default=0)
    parser.add_argument("--json", dest="json_out", type=str, default=None, help="Optional JSON report output path.")
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_cli_args(sys.argv[1:] if argv is None else argv)

    if args.check_expr_pair:
        closed_path, open_path = args.check_expr_pair
        res = check_upper_face_pixel_lock(
            closed_path,
            open_path,
            split_y_frac=args.split_y_frac,
            max_abs_diff=args.max_abs_diff,
        )
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(json.dumps(res, indent=2))
        return 0 if res["pass"] else 1

    if args.blend:
        if bpy is None:
            print(
                "ERROR: `--blend` requires running inside Blender: "
                "blender -b --factory-startup --python scripts/ricks_guardrails.py -- --blend <file.blend>",
                file=sys.stderr,
            )
            return 2
        blend_path = Path(args.blend).expanduser().resolve()
        if not blend_path.is_file():
            print(f"ERROR: Blend file not found: {blend_path}", file=sys.stderr)
            return 2
        bpy.ops.wm.open_mainfile(filepath=str(blend_path))
        scene = bpy.context.scene
        if args.frames:
            frames = [int(x.strip()) for x in args.frames.split(",") if x.strip()]
        else:
            f0, f1 = int(scene.frame_start), int(scene.frame_end)
            frames = sorted({f0, (f0 + f1) // 2, f1})
        report = audit_scene(
            scene,
            frames=frames,
            expect_deep_focus=not args.allow_dof,
            margin=args.margin,
            max_tris=args.max_tris,
        )
        print(format_report(report))
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 0 if report["pass"] else 1

    print("Specify `--blend <scene.blend>` (inside Blender) or `--check-expr-pair <closed.png> <open.png>`.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
