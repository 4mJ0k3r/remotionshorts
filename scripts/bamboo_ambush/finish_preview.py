"""Verify all 935 frames exist, mux preview MP4 with audio_master.wav, and run short_qa.py."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(r"D:\remotionshorts\renders\bamboo_ambush")
FRAMES_DIR = ROOT / "frames"
AUDIO_PATH = ROOT / "audio_master.wav"
SHOTS_PATH = ROOT / "shots.json"
OUT_MP4 = ROOT / "bamboo_ambush_preview_540p.mp4"
QA_DIR = ROOT / "qa"
SHORT_QA = Path(r"D:\remotionshorts\scripts\short_qa.py")
TOTAL_FRAMES = 935


def main():
    missing = [f for f in range(1, TOTAL_FRAMES + 1) if not (FRAMES_DIR / f"{f:04d}.png").exists()]
    if missing:
        raise RuntimeError(f"Missing {len(missing)} frames, first 10: {missing[:10]}")
    if not AUDIO_PATH.exists():
        raise FileNotFoundError(f"Missing master audio: {AUDIO_PATH}")

    cmd_ffmpeg = [
        "ffmpeg",
        "-y",
        "-framerate", "30",
        "-start_number", "1",
        "-i", str(FRAMES_DIR / "%04d.png"),
        "-i", str(AUDIO_PATH),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", "31.166667",
        "-movflags", "+faststart",
        str(OUT_MP4),
    ]
    print("Running:", " ".join(cmd_ffmpeg), flush=True)
    subprocess.run(cmd_ffmpeg, check=True)

    QA_DIR.mkdir(parents=True, exist_ok=True)
    cmd_qa = [sys.executable, str(SHORT_QA), str(OUT_MP4), str(QA_DIR), str(SHOTS_PATH)]
    print("Running:", " ".join(cmd_qa), flush=True)
    subprocess.run(cmd_qa, check=True)
    print(f"Preview MP4 + QA complete: {OUT_MP4} & {QA_DIR}")


if __name__ == "__main__":
    main()
