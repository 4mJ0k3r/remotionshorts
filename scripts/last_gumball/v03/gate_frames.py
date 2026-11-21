"""Per-frame readout of ricks_metrics_gate's own camera-flow measure (diagnostic).

  python scripts/last_gumball/v03/gate_frames.py VIDEO CUTS.json [first_blender_frame] [lo hi]

Uses the gate's functions unchanged, and prints the measured speed or
UNMEASURED for each destination frame. Blender frame = clip index + first.
"""
import json
from pathlib import Path
import sys

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import ricks_metrics_gate as g

video, cuts_path = Path(sys.argv[1]), Path(sys.argv[2])
first = int(sys.argv[3]) if len(sys.argv) > 3 else 1
lo, hi = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 10 ** 9)
cuts = g.read_cuts(cuts_path)
info = g.run_json(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                   "-of", "json", str(video)])["streams"][0]
width, height = g.dimensions(info["width"], info["height"], 480)
half, search = 24, 29
margin = half + search
tiles = [(int(x), int(y)) for y in np.linspace(margin, height - margin, 3) for x in np.linspace(margin, width - margin, 3)]
corners = [(0, 0), *[(x * width / 2, y * height / 2) for x in (-1, 1) for y in (-1, 1)]]
reference = g.similarity_design(np.asarray(corners))
prev = None
for i, gray in enumerate(g.video_frames(video, width, height)):
    frame = gray.astype(np.float32) / 255
    cur = frame - ndimage.gaussian_filter(frame, sigma=2.)
    if prev is not None and i not in cuts and lo <= i + first <= hi:
        found = sum(g.patch_shift(prev, cur, x, y, half, search) is not None for x, y in tiles)
        flow = g.estimate_flow(prev, cur, tiles, half, search, reference)
        speed = None if flow is None else float(np.linalg.norm(flow, axis=1).max())
        print(i + first, "UNMEASURED" if speed is None else f"{speed:6.1f}", f"tiles {found}/9")
    prev = cur
