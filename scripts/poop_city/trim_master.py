"""Drop the duplicate ending take from the master, keeping the original.

Reads the measured trim point from segments_timeline.json, preserves the full
decode as audio_master_full.wav, and rewrites audio_master.wav plus the 16 kHz
correlation reference. Re-run prepare_audio.py afterwards to re-measure.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / "renders" / "poop_city"
FULL = OUT / "audio_master_full.wav"
MASTER = OUT / "audio_master.wav"
REF = OUT / "_tight_ref.wav"


def run(args):
    subprocess.run(args, check=True, capture_output=True)


def main():
    tl = json.loads((OUT / "segments_timeline.json").read_text(encoding="utf-8"))
    trim = tl.get("suggested_trim_s")
    if not trim:
        print("no duplicate take detected; nothing to trim")
        return 0
    if not FULL.exists():
        shutil.move(str(MASTER), str(FULL))
        print(f"preserved original as {FULL.name}")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(FULL),
         "-t", f"{trim:.4f}", "-ac", "1", "-ar", "44100",
         "-c:a", "pcm_s16le", str(MASTER)])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(MASTER),
         "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(REF)])
    for p in (FULL, MASTER):
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", str(p)],
                           check=True, capture_output=True, text=True).stdout.strip()
        print(f"{p.name}: {d}s")
    print(f"trimmed at {trim}s -> {int(round(trim * 30))} frames @30fps")
    return 0


if __name__ == "__main__":
    sys.exit(main())