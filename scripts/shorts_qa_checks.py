"""Pure image diagnostics. Metadata frame indices are ZERO-based throughout.

MAD is a review signal, not proof of a camera collision. Shadow tests require
declared static receiver crops; moving cameras need tracked crops per frame.
"""
import numpy as np


def planned_frames(meta):
    planned = set()
    for a, b in meta.get('xfade', []) + meta.get('planned', []) + ([meta['flash']] if 'flash' in meta else []):
        planned.update(range(a-1, b+2))  # Inclusive event plus its exit pair.
    # Legacy metadata has no explicit cuts. New metadata MUST declare cuts,
    # including [] for a fully continuous sequence; shot labels are not cuts.
    cuts = meta.get('cuts', [s['a'] for s in meta.get('shots', [])])
    for frame in cuts:
        planned.add(frame)
    planned.difference_update(meta.get('continuous_junctions', []))
    return planned


def region_pixels(region, width, height):
    if len(region) != 4 or not all(0 <= x <= 1 for x in region) or region[0] >= region[2] or region[1] >= region[3]:
        raise ValueError('ROI must be normalized [left, top, right, bottom]')
    x0, y0, x1, y1 = region
    pixels = int(x0*width), int(y0*height), min(width, int(x1*width)), min(height, int(y1*height))
    if pixels[0] >= pixels[2] or pixels[1] >= pixels[3]:
        raise ValueError('ROI is smaller than one pixel at the analysis resolution')
    return pixels


def frame_differences(frames, excludes=()):
    _, h, w, _ = frames.shape
    mask = np.ones((h, w), dtype=bool)
    for region in excludes:
        x0, y0, x1, y1 = region_pixels(region, w, h)
        mask[y0:y1, x0:x1] = False
    if not mask.any():
        raise ValueError('MAD exclusions cover the entire frame')
    result = np.empty(max(0, len(frames)-1), dtype=np.float64)
    for start in range(0, len(result), 60):
        block = frames[start:min(len(frames), start+61)].astype(np.int16)
        d = np.abs(np.diff(block, axis=0))[:, mask].mean(axis=(1, 2))
        result[start:start+len(d)] = d
    return result


def mad_spikes(diff, meta):
    excluded = planned_frames(meta)
    relative, absolute = [], []
    for i, value in enumerate(diff):
        if i+1 in excluded:
            continue
        local = np.median(diff[max(0, i-8):i+9])
        if value > meta.get('mad_ratio', 3)*local+meta.get('mad_floor', 1.):
            relative.append(i+1)
        if value > meta.get('mad_absolute', 12.):
            absolute.append(i+1)
    return {'relative': relative, 'absolute': absolute, 'review': sorted(set(relative+absolute))}


def frozen_spans(diff, minimum=12):
    spans, start = [], None
    for i in range(len(diff)+1):
        held = i < len(diff) and diff[i] < .02
        if held and start is None:
            start = i
        if not held and start is not None:
            if i-start >= minimum:
                spans.append((start, i))  # Inclusive frame endpoints.
            start = None
    return spans


def shadow_stability(frames, meta):
    checks = meta.get('shadow_checks', [])
    if not checks:
        return [{'name': 'opening shadows', 'status': 'UNVERIFIED', 'reason': 'No static/registered shadow receiver ROI declared'}]
    results, excluded = [], planned_frames(meta)
    for spec in checks:
        name = spec.get('name', 'shadow receiver')
        start, end = spec['start'], spec['end']
        static = spec.get('registration') == 'locked-camera'
        tracked = spec.get('regions_by_frame', {})
        if not (0 <= start < end <= len(frames)) or (not static and not tracked):
            results.append({'name': name, 'status': 'UNVERIFIED', 'reason': 'Invalid interval or missing camera/ROI registration'})
            continue
        images, bad, missing = {}, [], False
        for f in range(start, end):
            regions = spec.get('regions', []) if static else tracked.get(str(f), [])
            if not regions:
                missing = True; break
            crops = []
            for region in regions:
                x0, y0, x1, y1 = region_pixels(region, frames.shape[2], frames.shape[1])
                # Resize registered crops to a common grid, then compare pixels,
                # not median luminance (which can hide shifting shadow patterns).
                from PIL import Image
                rgb = np.asarray(Image.fromarray(frames[f, y0:y1, x0:x1]).resize((32, 32)), dtype=np.float32)
                crops.append(rgb @ np.array([.2126, .7152, .0722]))
            images[f] = np.stack(crops)
        deltas = []
        if not missing:
            for f in range(start+1, end):
                if f in excluded:
                    continue
                value = float(np.abs(images[f]-images[f-1]).mean())
                deltas.append(value)
                if value > spec.get('max_adjacent_luma', 1.):
                    bad.append(f)
        status = 'UNVERIFIED' if missing or not deltas else ('REVIEW' if bad else 'PASS')
        results.append({'name': name, 'status': status, 'frames': bad, 'pairs_checked': len(deltas),
                        'max_adjacent_luma': max(deltas) if deltas else None})
    return results
