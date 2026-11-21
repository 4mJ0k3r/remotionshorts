"""Mux the preview or native final and verify the delivered streams."""
import json
from pathlib import Path
import subprocess
import sys


output = Path(__file__).resolve().parents[3] / "renders/padoda_billionaire/v04"
native = sys.argv[1:] == ["--native"]
if sys.argv[1:] and not native:
    raise SystemExit("Use --native for the full-resolution final.")
frames = output / ("native_frames" if native else "motion_frames")
audio = output / "hook_master_audio.wav"
delivery = output / ("padoda_part1_1080p.mp4" if native else "padoda_hook_v04_540p.mp4")
pending = delivery.with_stem(delivery.stem + "_pending")
expected_frames = 261
width, height = (1080, 1920) if native else (540, 960)
if not all((frames / f"frame_{frame:04}.png").is_file() for frame in range(1, expected_frames + 1)):
    raise SystemExit("The frame sequence is incomplete.")
if native:
    render = json.loads((output / "native_render_report.json").read_text())
    if (
        render["frames_completed"] != expected_frames
        or render["resolution"] != [width, height]
        or render["telemetry_errors"]
        or not 0 < (render["max_seconds"] or 0) <= 2.0
        or not 0 < (render["sampled_board_peak_gib"] or 0) <= 3.3
    ):
        raise SystemExit("The native render did not pass the frame count, resolution or GPU gates.")

subprocess.run([
    "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
    "-framerate", "30", "-start_number", "1", "-i", str(frames / "frame_%04d.png"),
    "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "libx264", "-preset", "fast", "-crf", "16" if native else "17", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
    str(pending),
], check=True)

probe = json.loads(subprocess.check_output([
    "ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format",
    "-of", "json", str(pending),
]))
video, sound = probe["streams"]
if (
    (video["width"], video["height"], video["r_frame_rate"], int(video["nb_read_frames"]))
    != (width, height, "30/1", expected_frames)
    or sound["codec_type"] != "audio"
    or float(sound["start_time"]) != 0
    or abs(float(sound["duration"]) - 8.7) > .001
    or abs(float(video["duration"]) - 8.7) > .001
):
    raise SystemExit("The MP4 failed its stream check.")

subprocess.run([
    "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(pending),
    "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-",
], check=True)
pending.replace(delivery)
probe["format"]["filename"] = str(delivery)
check = "native_delivery_check.json" if native else "preview_check.json"
(output / check).write_text(json.dumps(probe, indent=2))
