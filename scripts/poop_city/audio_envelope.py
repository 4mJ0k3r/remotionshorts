"""Per-frame audio envelope for speaker-gated mouth drive at 30 fps.

Normalized RMS with a noise floor and asymmetric attack/release, plus a 0.2
quantized channel for pose caching as the cel contract requires.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[2] / "renders" / "poop_city"
FPS = 30
NOISE_FLOOR = 0.06
ATTACK = 0.55
RELEASE = 0.22
QUANT = 0.2


def main():
    with wave.open(str(OUT / "audio_master.wav"), "rb") as w:
        rate = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    x = x.astype(np.float64) / 32768.0
    n_frames = int(round(len(x) / rate * FPS))
    hop = len(x) / n_frames
    rms = np.array([
        np.sqrt(np.mean(x[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-12)
        for i in range(n_frames)])
    scale = float(np.percentile(rms, 98)) or 1.0
    e = np.clip(rms / scale, 0.0, 1.0)
    e[e < NOISE_FLOOR] = 0.0

    sm = np.zeros(n_frames)
    prev = 0.0
    for i, v in enumerate(e):
        k = ATTACK if v > prev else RELEASE
        prev = prev + k * (v - prev)
        sm[i] = prev
    sm = np.clip(sm, 0.0, 1.0)
    mouth = np.round(sm / QUANT) * QUANT

    tl = json.loads((OUT / "segments_timeline.json").read_text(encoding="utf-8"))
    voiced = np.zeros(n_frames, dtype=bool)
    for s in tl["segments"]:
        voiced[s["start_frame"]:s["end_frame"] + 1] = True

    payload = dict(
        fps=FPS, total_frames=n_frames, duration_s=round(len(x) / rate, 4),
        source="audio_master.wav", rms_scale=round(scale, 6),
        noise_floor=NOISE_FLOOR, attack=ATTACK, release=RELEASE, quant=QUANT,
        env=[round(float(v), 4) for v in sm],
        mouth=[round(float(v), 3) for v in mouth],
        voiced_frames=int(voiced.sum()),
        peak=round(float(sm.max()), 4),
        mean_voiced=round(float(sm[voiced].mean()), 4) if voiced.any() else 0.0,
    )
    (OUT / "audio_env.json").write_text(json.dumps(payload), encoding="utf-8")
    print(f"frames {n_frames}  duration {len(x) / rate:.3f}s  rms p98 {scale:.4f}")
    print(f"env peak {sm.max():.3f}  mean over voiced {sm[voiced].mean():.3f}  "
          f"voiced frames {int(voiced.sum())}/{n_frames} "
          f"({100 * voiced.sum() / n_frames:.1f}%)")
    print(f"silent frames inside segments: "
          f"{int((~(sm > 0) & voiced).sum())}")
    print(f"wrote {OUT / 'audio_env.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())