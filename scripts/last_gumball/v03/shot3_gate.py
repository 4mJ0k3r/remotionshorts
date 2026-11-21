"""Encode a scratch shot-3 render and run the repo motion gate on it.

  python scripts/last_gumball/v03/shot3_gate.py renders/last_gumball/v03/_iter/NAME

Frames 106-190 are rendered; the clip keeps the real cuts at 109 and 187
(zero-based 3 and 81 in the clip) so the gate excludes them.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
folder = Path(sys.argv[1]).resolve()
clip = folder.with_suffix(".mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "30", "-start_number", "106", "-i",
                str(folder / "frame_%04d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p",
                "-vf", "setsar=1", "-an", str(clip)], check=True)
cuts = folder.with_name(folder.name + "_cuts.json")
cuts.write_text(json.dumps({"cuts": [109 - 106, 187 - 106]}), encoding="utf-8")
out = subprocess.run([sys.executable, str(ROOT / "scripts/ricks_metrics_gate.py"), "--cam-velocity", str(clip),
                      str(cuts)], capture_output=True, text=True)
r = json.loads(out.stdout)
steps = r.get("steps") or r.get("pairs") or []
print("status", r["status"], "max", round(r["max_smooth_px_per_frame"], 1), "at clip", r["max_velocity_destination_frame"],
      "-> blender", r["max_velocity_destination_frame"] + 106 if r["max_velocity_destination_frame"] is not None else None)
print("hops (blender)", [f + 106 for f in r["hop_destination_frames"]])
print("unmeasured (blender)", [f + 106 for f in r["unmeasured_destination_frames"]])
print("keys", sorted(r.keys()))
