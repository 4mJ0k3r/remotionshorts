# Frame-by-frame QA of a rendered vertical short (every frame at 30 fps): specs, loudness, per-frame luma / saturation /
# motion, black-white-frozen-pop detection (ignoring planned flashes and crossfades), per-shot colour stats and 2 s
# contact sheets (60 frames each, frame numbers burned in for the reviewer only).
# Usage: python scripts/short_qa.py <video.mp4> <outdir> [shots.json]
# Metadata: zero-based indices; shots [a,b), explicit cuts (destination indices),
# continuous_junctions override exemptions; see shorts_qa.example.json.
# Legacy shots.json: [{"id":1,"a":0,"b":130}, ...] plus optional {"flash":[130,134], "xfade":[[1131,1137], ...]}
import argparse, json, os, subprocess, sys
from pathlib import Path
try:
    from .shorts_qa_checks import planned_frames, frame_differences, mad_spikes, frozen_spans, shadow_stability
except ImportError:
    from shorts_qa_checks import planned_frames, frame_differences, mad_spikes, frozen_spans, shadow_stability
import numpy as np
from PIL import Image, ImageDraw

def main():
    parser = argparse.ArgumentParser(description='Every-frame QA; manifest indices are zero-based')
    parser.add_argument('video'); parser.add_argument('outdir'); parser.add_argument('metadata', nargs='?')
    parser.add_argument('--strict', action='store_true')
    args = parser.parse_args()
    vid, out = args.video, args.outdir
    meta = json.loads(Path(args.metadata).read_text(encoding='utf-8')) if args.metadata else {}
    if isinstance(meta, list): meta = {'shots': meta}
    shots = meta.get('shots', [])
    planned = planned_frames(meta)
    os.makedirs(out, exist_ok=True)
    run = lambda *a: subprocess.run(a, capture_output=True, text=True, check=True)
    R = []

    pr = json.loads(run("ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,sample_rate,channels:format=duration", "-of", "json", vid).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    au = [s for s in pr["streams"] if s["codec_type"] == "audio"]
    R.append(f"SPECS {v['width']}x{v['height']} {v['r_frame_rate']} fps, {v.get('nb_frames')} frames, {float(pr['format']['duration']):.3f} s; audio: "
             + (", ".join(f"{s['codec_name']} {s['sample_rate']} Hz {s['channels']}ch" for s in au) if au else "NONE"))
    if au:
        e = run("ffmpeg", "-i", vid, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-").stderr
        tail = e[e.rfind("Summary:"):]
        I = [l.strip() for l in tail.splitlines() if l.strip().startswith(("I:", "LRA:", "Peak:"))]
        R.append("LOUDNESS " + " | ".join(I))
        e = run("ffmpeg", "-i", vid, "-map", "0:a:0", "-af", "silencedetect=n=-45dB:d=0.3", "-f", "null", "-").stderr
        R.append("SILENCES " + ("; ".join(l.split("] ")[-1] for l in e.splitlines() if "silence_" in l) or "none"))

    W, H = 180, 320
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", vid, "-vf", f"scale={W}:{H}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    F = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    n = len(F)
    if not n: raise ValueError('No video frames decoded')
    # Keep statistics bounded to 60-frame chunks. Full-reel RGB/luma/saturation
    # float planes otherwise exceed laptop RAM; detection formulas are unchanged.
    parts = {k: [] for k in ("mean", "std", "p2", "p98", "sat")}
    for start in range(0, n, 60):
        block = F[start:start + 60].astype(np.float32) / 255
        luma = block @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        mx, mn = block.max(-1), block.min(-1)
        sat = np.where(mx > 0.06, (mx - mn) / np.maximum(mx, 1e-6), 0)
        L = luma.reshape(len(block), -1)
        for key, value in {"mean": L.mean(1), "std": L.std(1), "p2": np.percentile(L, 2, 1), "p98": np.percentile(L, 98, 1), "sat": sat.reshape(len(block), -1).mean(1)}.items():
            parts[key].append(value)
        del block, luma, mx, mn, sat, L
    stats = {k: np.concatenate(v) for k, v in parts.items()}
    raw_diff = frame_differences(F)
    diff = frame_differences(F, meta.get('mad_exclude_regions', []))
    spikes = mad_spikes(diff, meta)
    pops = spikes['relative']
    shadows = shadow_stability(F, meta)
    black = [i for i in range(n) if stats["mean"][i] < 0.04 and i not in planned]
    white = [i for i in range(n) if stats["mean"][i] > 0.93 and i not in planned]
    frozen = frozen_spans(raw_diff)
    R.append(f"FRAMES {n}; black {black[:20]}; unplanned white {white[:20]}; frozen spans >=12f {frozen[:20]}")
    R.append(f"POPS (unplanned frame-diff spikes > 3x local median): {pops[:40]}")
    R.append("INDEXING zero-based; spike index is the destination frame")
    R.append("MAD absolute spikes: " + str(spikes["absolute"][:40]))
    for shadow in shadows: R.append("SHADOW " + json.dumps(shadow))
    R.append(f"MOTION mean diff {(diff.mean() if len(diff) else 0):.2f}; frames with diff<0.3 (held): {int((diff < 0.3).sum())} ({((diff < 0.3).mean() * 100 if len(diff) else 0):.0f}%)")

    R.append("\nPER SHOT  (luma mean / std / p2 / p98 / saturation mean, medians over the shot)")
    for s in shots or [{"id": 0, "a": 0, "b": n}]:
        a, b = s["a"], min(s["b"], n)
        if a >= b: continue
        R.append(f"  shot {s['id']:>2} f{a}-{b - 1}: " + " / ".join(f"{np.median(stats[k][a:b]):.3f}" for k in ("mean", "std", "p2", "p98", "sat")))
    np.savez(os.path.join(out, "perframe.npz"), diff=diff, raw_diff=raw_diff, **stats)

    # 2 s contact sheets, 10 x 6 frames of 108x192 each
    cw, ch = 108, 192
    for k in range(0, n, 60):
        S = Image.new("RGB", (cw * 10, ch * 6), "black"); d = ImageDraw.Draw(S)
        for j in range(min(60, n - k)):
            x, y = (j % 10) * cw, (j // 10) * ch
            S.paste(Image.fromarray(F[k + j]).resize((cw, ch)), (x, y))
            d.rectangle([x, y, x + 106, y + 12], fill="black"); d.text((x + 2, y + 1), f"i{k+j}/f{k+j+1}", fill="yellow")
        S.save(os.path.join(out, f"sheet_{k:04d}.jpg"), quality=85)
    action_freezes = [(a,b) for a,b in frozen if any(a < y and b >= x for x,y in meta.get('action_ranges', []))]
    status = 'REVIEW' if spikes['review'] or black or white or action_freezes or any(x['status']=='REVIEW' for x in shadows) else 'PASS'
    if status == 'PASS' and any(x['status']=='UNVERIFIED' for x in shadows): status = 'UNVERIFIED'
    if args.strict and 'cuts' not in meta:
        R.append('CUTS UNVERIFIED: strict new-build manifests must explicitly declare cuts, including []')
        if status == 'PASS': status = 'UNVERIFIED'
    result = {'status': status, 'frames': n, 'specs': v, 'mad': spikes, 'shadow_checks': shadows,
              'frozen': frozen, 'action_freezes': action_freezes, 'black': black, 'white': white}
    Path(out, 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    R.append('DIAGNOSTIC STATUS '+status+'; visual/audio/caption acceptance still requires inspection')
    Path(out, 'report.md').write_text('\n'.join(R)+'\n', encoding='utf-8')
    print('\n'.join(R))
    if args.strict and status != 'PASS': raise SystemExit(2)

if __name__ == "__main__":
    main()
