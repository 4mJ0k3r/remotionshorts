"""Stage 1: Clean and merge Hindi narration + GOP GOP SFX into master audio (935 frames @ 30fps)."""
import json
import shutil
import subprocess
import wave
from pathlib import Path
import numpy as np

ROOT = Path(r"D:\remotionshorts")
OUT = ROOT / "renders" / "bamboo_ambush"
OUT.mkdir(parents=True, exist_ok=True)

SRC_GOP = Path(
    r"C:\Users\lavis\.gemini\antigravity\brain\ebe125a5-8873-4d02-a5d3-828dfb0546b3\.user_uploaded\uploaded_media_0_1794559187295.mp3"
)
SRC_HINDI = Path(
    r"C:\Users\lavis\.gemini\antigravity\brain\ebe125a5-8873-4d02-a5d3-828dfb0546b3\.user_uploaded\uploaded_media_1_1794559187295.mp3"
)

RAW_GOP = OUT / "raw_gop_gop_sfx.mp3"
RAW_HINDI = OUT / "raw_hindi_narration.mp3"
MASTER_WAV = OUT / "audio_master.wav"

FPS = 30
TOTAL_FRAMES = 935
TARGET_DUR = TOTAL_FRAMES / FPS  # 31.166667s

CUTS = [
    {"id": 1, "shot": "1A", "start_frame": 1, "end_frame": 90, "peak": 45, "cue": "Japanese soldier enters coffin pit"},
    {"id": 2, "shot": "1B", "start_frame": 91, "end_frame": 189, "peak": 140, "cue": "Top-down coffin pit"},
    {"id": 3, "shot": "2A", "start_frame": 190, "end_frame": 285, "peak": 240, "cue": "Bamboo breathing tube close-up"},
    {"id": 4, "shot": "2B", "start_frame": 286, "end_frame": 404, "peak": 345, "cue": "Sand covers soldier"},
    {"id": 5, "shot": "3A", "start_frame": 405, "end_frame": 459, "peak": 430, "cue": "Enemy #17 boots approach"},
    {"id": 6, "shot": "3B", "start_frame": 460, "end_frame": 528, "peak": 495, "cue": "Soldier erupts with bayonet rifle"},
    {"id": 7, "shot": "3C", "start_frame": 529, "end_frame": 590, "peak": 560, "cue": "Grenade stuffed in enemy mouth"},
    {"id": 8, "shot": "4A", "start_frame": 591, "end_frame": 696, "peak": 660, "cue": "Enemy spots bamboo & creepy grin"},
    {"id": 9, "shot": "4B", "start_frame": 697, "end_frame": 768, "peak": 735, "cue": "Enemy straddles bamboo pipe"},
    {"id": 10, "shot": "5A", "start_frame": 769, "end_frame": 834, "peak": 800, "cue": "GOP GOP above ground"},
    {"id": 11, "shot": "5B", "start_frame": 835, "end_frame": 888, "peak": 860, "cue": "GOP GOP underground gagging"},
    {"id": 12, "shot": "5C", "start_frame": 889, "end_frame": 935, "peak": 910, "cue": "X-ray cross-section finale"},
]


def main():
    if not SRC_GOP.exists() or not SRC_HINDI.exists():
        raise FileNotFoundError("Missing uploaded audio inputs")

    shutil.copy2(SRC_GOP, RAW_GOP)
    shutil.copy2(SRC_HINDI, RAW_HINDI)

    # Part A: 0.00 - 13.45s (13.45s)
    # Skip 13.45 - 15.85s ("Seven to thirteen seconds")
    # Part B: 15.85 - 28.00s padded to exact 12.15s => 13.45 + 12.15 = 25.60s (768 frames)
    # Part C: gop_gop 0.00 - 5.00s + 3.75 - 4.316667s => 5.566667s => Total 31.166667s (935 frames)
    filter_complex = (
        "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "atrim=start=0:end=13.45,asetpts=PTS-STARTPTS,afade=t=out:st=13.40:d=0.05[a1];"
        "[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "atrim=start=15.85:end=28.00,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.05,apad=whole_dur=12.15,atrim=0:12.15[a2];"
        "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "atrim=start=0:end=5.00,asetpts=PTS-STARTPTS[g1];"
        "[1:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
        "atrim=start=3.75:end=4.316667,asetpts=PTS-STARTPTS,afade=t=out:st=0.45:d=0.11[g2];"
        "[a1][a2][g1][g2]concat=n=4:v=0:a=1[outa]"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "warning",
            "-i",
            str(RAW_HINDI),
            "-i",
            str(RAW_GOP),
            "-filter_complex",
            filter_complex,
            "-map",
            "[outa]",
            "-ar",
            "48000",
            "-ac",
            "2",
            "-c:a",
            "pcm_s16le",
            str(MASTER_WAV),
        ],
        check=True,
    )

    probe = json.loads(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=sample_rate,channels,duration:format=duration",
                "-of",
                "json",
                str(MASTER_WAV),
            ],
            text=True,
        )
    )
    dur = float(probe["format"]["duration"])
    print(f"audio_master.wav duration: {dur:.6f}s (target {TARGET_DUR:.6f}s)")

    # Compute per-frame RMS audio envelope (935 frames)
    with wave.open(str(MASTER_WAV), "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        if ch > 1:
            pcm = pcm.reshape(-1, ch).mean(axis=1)

    env = []
    for f in range(TOTAL_FRAMES):
        i0 = int(round(f * sr / FPS))
        i1 = int(round((f + 1) * sr / FPS))
        seg = pcm[i0:i1]
        rms = float(np.sqrt(np.mean(seg * seg))) if len(seg) else 0.0
        env.append(rms)
    norm_scale = max(float(np.percentile(env, 92)), 1e-4)
    env_norm = [round(min(1.0, v / norm_scale), 3) for v in env]
    (OUT / "audio_envelope.json").write_text(json.dumps(env_norm), encoding="utf-8")

    # Save shots.json for short_qa.py (0-based inclusive/exclusive slices a, b)
    shots_meta = {
        "fps": FPS,
        "frames": TOTAL_FRAMES,
        "duration": round(dur, 4),
        "shots": [
            {
                "id": c["id"],
                "shot": c["shot"],
                "a": c["start_frame"] - 1,
                "b": c["end_frame"],
                "start_frame": c["start_frame"],
                "end_frame": c["end_frame"],
                "peak": c["peak"],
                "cue": c["cue"],
            }
            for c in CUTS
        ],
        "planned": [[c["start_frame"] - 2, c["start_frame"] + 1] for c in CUTS if c["start_frame"] > 1]
        + [[534, 542], [461, 478]],
    }
    (OUT / "shots.json").write_text(json.dumps(shots_meta, indent=2), encoding="utf-8")
    print("Wrote audio_master.wav, audio_envelope.json, and shots.json")


if __name__ == "__main__":
    main()
