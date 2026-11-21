"""Pre-render image, screen-motion and annotated word-sync gates. Outputs JSON."""

import argparse
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from itertools import combinations
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image
from scipy import ndimage, signal

EDGE_THRESHOLD = .10
MOTION_THRESHOLD = 2.
VELOCITY_LIMIT = 55.
HOP_RATE_LIMIT = .4
SYNC_WINDOW_CS = 10
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def dimensions(width, height, long_edge):
    scale = long_edge / max(width, height)
    return max(1, round(width * scale)), max(1, round(height * scale))


def edge_density(path):
    if path.is_dir():
        paths = sorted(item for item in path.iterdir() if item.is_file()
                       and item.suffix.lower() in IMAGE_EXTENSIONS)
    else:
        paths = [path]
    if not paths:
        raise ValueError("The folder has no supported images.")
    frames = []
    for item in paths:
        with Image.open(item) as image:
            size = dimensions(*image.size, 640)
            gray = np.asarray(image.convert("L").resize(size, Image.Resampling.BILINEAR),
                              dtype=np.float32) / 255
        dx = ndimage.sobel(gray, axis=1) / 4
        dy = ndimage.sobel(gray, axis=0) / 4
        density = float(np.mean(np.hypot(dx, dy) >= EDGE_THRESHOLD))
        frames.append({"file": item.name, "density": density})
    values = [frame["density"] for frame in frames]
    average, minimum = float(np.mean(values)), min(values)
    return {
        "mean": average, "min": minimum, "frames": frames, "frame_count": len(frames),
        "below_minimum_frames": [frame["file"] for frame in frames if frame["density"] < .088],
        "gradient_threshold": EDGE_THRESHOLD, "analysis_long_edge_px": 640,
        "checks": {"mean_at_least_0_14": average >= .14, "min_at_least_0_088": minimum >= .088},
    }


def run_json(command):
    return json.loads(subprocess.check_output(command, text=True, encoding="utf-8"))


def load_json(path):
    with path.open(encoding="utf-8-sig") as file:
        return json.load(file, parse_float=Decimal)


def read_cuts(path):
    data = load_json(path)
    cuts = data.get("cuts") if isinstance(data, dict) else data
    if not isinstance(cuts, list) or any(type(frame) is not int or frame < 1 for frame in cuts):
        raise ValueError("cuts must list positive zero-based destination frame indices.")
    if len(set(cuts)) != len(cuts):
        raise ValueError("cuts contains duplicate indices.")
    return set(cuts)


def box_sums(image, side):
    """Sum every side-by-side square at its possible top-left position."""
    integral = np.pad(image.cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)))
    return integral[side:, side:] - integral[:-side, side:] - integral[side:, :-side] + integral[:-side, :-side]


def patch_shift(before, after, x, y, half, search):
    """Find a textured tile in its next-frame neighborhood using normalized correlation."""
    template = before[y-half:y+half, x-half:x+half].copy()
    template -= template.mean()
    magnitude = np.linalg.norm(template)
    if magnitude / (2 * half) < .008:
        return None
    region = after[y-half-search:y+half+search, x-half-search:x+half+search]
    side = 2 * half
    sums = box_sums(region, side)
    energy = box_sums(region**2, side) - sums**2 / (side * side)
    numerator = signal.correlate(region, template, mode="valid", method="fft")
    scores = numerator / (magnitude * np.sqrt(np.maximum(energy, 1e-8)))
    row, col = np.unravel_index(np.argmax(scores), scores.shape)
    score = float(scores[row, col])
    if score < .58 or not (0 < row < 2*search and 0 < col < 2*search):
        return None
    # Reject repeated slats or grid lines whose alternative match is almost as good.
    scores_without_peak = scores.copy()
    scores_without_peak[max(0, row-3):row+4, max(0, col-3):col+4] = -np.inf
    if score - float(scores_without_peak.max()) < .025:
        return None

    def subpixel(a, b, c):
        curvature = 2 * (a - 2*b + c)
        return float(np.clip((a-c)/curvature, -.5, .5)) if curvature < -1e-6 else 0.

    dx = col-search + subpixel(scores[row, col-1], score, scores[row, col+1])
    dy = row-search + subpixel(scores[row-1, col], score, scores[row+1, col])
    return (dx, dy)


def similarity_design(points):
    """Represent a screen displacement as translation, uniform zoom and roll."""
    x, y = points.T
    zeros, ones = np.zeros_like(x), np.ones_like(x)
    return np.column_stack((ones, zeros, x, -y, zeros, ones, y, x)).reshape(-1, 2, 4)


def fit_camera_flow(points, shifts):
    """Fit to tile consensus, discarding independently moving foreground tiles."""
    design = similarity_design(points)
    best_score = (0, -math.inf)
    best = None
    for i, j in combinations(range(len(points)), 2):
        params = np.linalg.solve(design[[i, j]].reshape(4, 4), shifts[[i, j]].ravel())
        errors = np.linalg.norm(design @ params - shifts, axis=1)
        inliers = errors <= 1.6
        score = (int(inliers.sum()), -float(errors[inliers].sum()))
        if score > best_score:
            best_score, best = score, inliers
    if best_score[0] < max(4, math.ceil(len(points)*.60)):
        return None
    return np.linalg.lstsq(design[best].reshape(-1, 4), shifts[best].ravel(), rcond=None)[0]


def estimate_flow(previous, current, tiles, half, search, reference):
    if np.array_equal(previous, current):
        return np.zeros((len(reference), 2))
    points, shifts = [], []
    height, width = previous.shape
    for x, y in tiles:
        shift = patch_shift(previous, current, x, y, half, search)
        if shift is not None:
            points.append((x-width/2, y-height/2))
            shifts.append(shift)
    if len(points) < 4:
        return None
    params = fit_camera_flow(np.asarray(points), np.asarray(shifts))
    if params is None:
        return None
    return (reference @ params) * (1920 / max(width, height))


def video_frames(path, width, height):
    command = ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(path), "-map", "0:v:0",
               "-an", "-vf", f"scale={width}:{height}:flags=area", "-fps_mode", "passthrough",
               "-pix_fmt", "gray", "-f", "rawvideo", "-"]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as decoder:
        try:
            size = width * height
            while raw := decoder.stdout.read(size):
                if len(raw) != size:
                    raise ValueError("FFmpeg emitted an incomplete video frame.")
                yield np.frombuffer(raw, np.uint8).reshape(height, width)
            error = decoder.stderr.read().decode(errors="replace")
            if decoder.wait():
                raise ValueError(f"FFmpeg could not decode the video: {error.strip()}")
        finally:
            if decoder.poll() is None:
                decoder.terminate()


def camera_velocity(path, cut_plan):
    cuts = read_cuts(cut_plan)
    streams = run_json(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height,avg_frame_rate",
                        "-of", "json", str(path)])
    if not streams["streams"]:
        raise ValueError("No video stream found.")
    stream = streams["streams"][0]
    fps = float(Fraction(stream["avg_frame_rate"]))
    if fps <= 0:
        raise ValueError("Could not determine a positive video frame rate.")
    width, height = dimensions(stream["width"], stream["height"], 480)
    half, search = 24, 29
    margin = half + search
    if min(width, height) < 2*margin+4:
        raise ValueError("The video aspect ratio is too narrow for camera registration.")
    tiles = [(int(x), int(y)) for y in np.linspace(margin, height-margin, 3)
             for x in np.linspace(margin, width-margin, 3)]
    corners = [(0, 0), *[(x*width/2, y*height/2) for x in (-1, 1) for y in (-1, 1)]]
    reference = similarity_design(np.asarray(corners))
    previous = last_flow = None
    speeds, hops, unknown = {}, [], []
    last_jump = -2
    frame_count = 0
    for index, gray in enumerate(video_frames(path, width, height)):
        frame = gray.astype(np.float32) / 255
        current = frame - ndimage.gaussian_filter(frame, sigma=2.)
        frame_count += 1
        if previous is not None and index not in cuts:
            flow = estimate_flow(previous, current, tiles, half, search, reference)
            if flow is None:
                unknown.append(index)
            else:
                speed = float(np.linalg.norm(flow, axis=1).max())
                speeds[index] = speed
                change = float(np.linalg.norm(flow-last_flow, axis=1).max()) if last_flow is not None else 0.
                if speed > VELOCITY_LIMIT or (speed >= 35. and change >= 30.):
                    if index != last_jump + 1:
                        hops.append(index)
                    last_jump = index
            last_flow = flow
        else:
            last_flow = None
        previous = current
    if frame_count < 2 or (cuts and max(cuts) >= frame_count):
        raise ValueError("The video must contain two frames and every declared cut must be in range.")
    duration = frame_count / fps
    measured = len(speeds)
    moving = sum(speed > MOTION_THRESHOLD for speed in speeds.values())
    moving_fraction = moving/measured if measured else None
    still_fraction = (measured-moving)/measured if measured else None
    rate = len(hops) * 10 / duration
    maximum = max(speeds.values(), default=None)
    return {
        "frames": frame_count, "fps": fps, "duration_s": duration,
        "declared_cut_destination_frames": sorted(cuts),
        "measured_pairs": measured, "eligible_pairs": frame_count-1-len(cuts),
        "unmeasured_destination_frames": unknown,
        "max_smooth_px_per_frame": maximum,
        "max_velocity_destination_frame": max(speeds, key=speeds.get) if speeds else None,
        "moving_fraction": moving_fraction, "settled_still_fraction": still_fraction,
        "moving_threshold_px_per_frame": MOTION_THRESHOLD,
        "hop_destination_frames": hops, "hops_per_10_seconds": rate,
        "measurement": "Dominant image motion, including zoom and roll, at a 1920px long edge",
        "checks": {
            "all_non_cut_pairs_measured": measured > 0 and not unknown,
            "max_at_most_55_px": maximum is not None and maximum <= VELOCITY_LIMIT,
            "hops_at_most_0_4_per_10_seconds": rate <= HOP_RATE_LIMIT,
        },
    }


def centiseconds(value):
    try:
        decimal = Decimal(str(value)) * 100
    except InvalidOperation as error:
        raise ValueError(f"Invalid timestamp {value!r}.") from error
    if not decimal.is_finite() or decimal < 0 or decimal != decimal.to_integral_value():
        raise ValueError(f"Timestamp {value!r} must lie on the nonnegative 0.01s grid.")
    return int(decimal)


def require_objects(data, key):
    items = data.get(key)
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError(f"{key} must be a list of objects.")
    return items


def word_sync(path):
    plan = load_json(path)
    if not isinstance(plan, dict):
        raise ValueError("The master plan must be a JSON object.")
    hook = centiseconds(plan.get("hook_end", 2))
    if hook <= 0:
        raise ValueError("hook_end must be positive.")
    required, ids = {}, set()
    previous_start = -1
    for word in require_objects(plan, "words"):
        identifier, kind, label = word.get("id"), word.get("kind"), word.get("text")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError("Each transcript word needs a unique string id.")
        if kind not in ("noun", "action", "other") or not isinstance(label, str) or not label.strip():
            raise ValueError(f"Word {identifier!r} needs text and kind noun, action or other.")
        start, end = centiseconds(word.get("start")), centiseconds(word.get("end"))
        if start < previous_start or end < start:
            raise ValueError(f"Invalid word interval for {identifier!r}; sort words by start time.")
        previous_start = start
        ids.add(identifier)
        if kind != "other":
            required[identifier] = (label, start)
    if not required:
        raise ValueError("Annotate at least one spoken noun or action before checking coverage.")

    events, first_face = {}, None
    for item in require_objects(plan, "visual_events"):
        kind, visible = item.get("kind"), item.get("visible", True)
        if kind not in ("prop", "character", "action", "face") or type(visible) is not bool:
            raise ValueError("Each visual event needs kind prop, character, action or face and optional boolean visible.")
        begin = centiseconds(item.get("start"))
        end = centiseconds(item["end"]) if "end" in item else begin
        if end < begin:
            raise ValueError("A visual interval cannot end before it starts.")
        word_id = item.get("word_id")
        if word_id is not None and (not isinstance(word_id, str) or word_id not in ids):
            raise ValueError(f"Unknown visual event word_id {word_id!r}.")
        if not visible:
            continue
        if kind == "face":
            first_face = begin if first_face is None else min(first_face, begin)
        if word_id is not None:
            events.setdefault(word_id, []).append((begin, end))

    measurements, matched = [], 0
    for identifier, (label, spoken) in required.items():
        distance = min((max(begin-spoken, spoken-end, 0) for begin, end in events.get(identifier, [])),
                       default=None)
        in_sync = distance is not None and distance <= SYNC_WINDOW_CS
        matched += in_sync
        measurements.append({"word_id": identifier, "word": label, "spoken_s": spoken/100,
                             "closest_visible_s_offset": distance/100 if distance is not None else None,
                             "in_sync": in_sync})
    coverage = matched / len(required)
    return {
        "annotated_nouns_and_actions": len(required), "matched": matched, "coverage": coverage,
        "first_character_face_s": first_face/100 if first_face is not None else None,
        "opening_hook_end_s": hook/100, "time_tolerance_s": SYNC_WINDOW_CS/100,
        "bindings": measurements,
        "checks": {"coverage_at_least_96_percent": coverage >= .96,
                   "character_face_in_opening_hook": first_face is not None and first_face <= hook},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--edge-density", metavar="IMAGE_OR_FOLDER", type=Path)
    mode.add_argument("--cam-velocity", nargs=2, metavar=("PREVIEW_MP4", "CUTS_JSON"), type=Path)
    mode.add_argument("--word-sync", metavar="MASTER_PLAN_JSON", type=Path)
    args = parser.parse_args()
    name, function, inputs = ("edge_density", edge_density, [args.edge_density])
    if args.cam_velocity is not None:
        name, function, inputs = ("cam_velocity", camera_velocity, args.cam_velocity)
    elif args.word_sync is not None:
        name, function, inputs = ("word_sync", word_sync, [args.word_sync])
    try:
        report = function(*inputs)
    except (ValueError, OSError, subprocess.SubprocessError, KeyError, ZeroDivisionError) as error:
        print(json.dumps({"gate": name, "status": "ERROR", "pass": False, "error": str(error)}, indent=2))
        return 2
    passed = all(report["checks"].values())
    print(json.dumps({"gate": name, "status": "PASS" if passed else "FAIL", "pass": passed, **report},
                     ensure_ascii=True, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
