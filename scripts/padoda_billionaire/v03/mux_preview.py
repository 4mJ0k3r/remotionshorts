"""Mux the complete motion preview and verify the delivered streams."""
import json
from pathlib import Path
import subprocess


output = Path(__file__).resolve().parents[3] / "renders/padoda_billionaire/v03"
frames = output / "motion_frames"
audio = output / "hook_master_audio.wav"
preview = output / "padoda_hook_v03_540p.mp4"
pending = preview.with_stem(preview.stem + "_pending")
expected_frames = 261
if not all((frames / f"frame_{frame:04}.png").is_file() for frame in range(1, expected_frames + 1)):
    raise SystemExit("The preview frame sequence is incomplete.")

subprocess.run([
    "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
    "-framerate", "30", "-start_number", "1", "-i", str(frames / "frame_%04d.png"),
    "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
    "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-pix_fmt", "yuv420p",
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
    != (540, 960, "30/1", expected_frames)
    or sound["codec_type"] != "audio"
    or float(sound["start_time"]) != 0
    or abs(float(sound["duration"]) - 8.7) > .001
    or abs(float(video["duration"]) - 8.7) > .001
):
    raise SystemExit("The preview failed its stream check.")

subprocess.run([
    "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(pending),
    "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-",
], check=True)
pending.replace(preview)
probe["format"]["filename"] = str(preview)
(output / "preview_check.json").write_text(json.dumps(probe, indent=2))
