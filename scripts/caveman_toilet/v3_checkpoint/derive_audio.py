"""Derive a per-frame narration envelope + speech segments for caveman_toilet.

CPU only (ffmpeg decode + numpy). Writes renders/caveman_toilet/audio_env.json
with {fps, total_frames, duration, env:[...], segments:[{a,b,sa,sb}]}.
Frame indices are 1-based to match Blender.
"""
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "caveman_toilet"
SRC = OUT / "narration.mp3"
FPS = 30
SR = 44100


def main():
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(SRC), "-ac", "1", "-ar", str(SR),
         "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    dur = len(x) / SR
    total = int(round(dur * FPS))
    spf = SR / FPS
    env = np.zeros(total, np.float32)
    for f in range(total):
        a = int(f * spf)
        b = int((f + 1) * spf)
        seg = x[a:b]
        env[f] = float(np.sqrt(np.mean(seg * seg))) if len(seg) else 0.0
    peak = float(env.max()) or 1.0
    envn = env / peak
    # speech segments: envelope above noise floor, bridging short gaps
    thr = 0.04
    active = envn > thr
    segments = []
    f = 0
    while f < total:
        if active[f]:
            a = f
            while f < total and (active[f] or (f + 1 < total and active[f + 1])):
                f += 1
            b = f
            if (b - a) >= 4:
                segments.append({"a": a + 1, "b": b, "sa": round(a / FPS, 3),
                                 "sb": round(b / FPS, 3)})
        else:
            f += 1
    data = {"fps": FPS, "total_frames": total, "duration": round(dur, 6),
            "peak_rms": peak, "env": [round(float(v), 4) for v in envn],
            "segments": segments}
    (OUT / "audio_env.json").write_text(json.dumps(data), encoding="utf-8")
    print(f"duration={dur:.6f}s total_frames={total} peak_rms={peak:.4f}")
    print(f"speech segments ({len(segments)}):")
    for s in segments:
        print(f"  f{s['a']:>4}-{s['b']:<4} {s['sa']:>6.2f}-{s['sb']:<6.2f}s")


if __name__ == "__main__":
    main()