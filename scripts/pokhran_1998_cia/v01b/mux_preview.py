"""Mux and decode-check the portrait hook preview with the original voice."""
import hashlib
import json
from pathlib import Path
import subprocess


here = Path(__file__).resolve().parent
output = here.parents[2] / "renders/pokhran_1998_cia/v01b"
plan = json.loads((here / "master_plan.json").read_text(encoding="utf-8"))
source = Path.home() / "Downloads" / plan["source_audio"]["file"]
frames = output / "preview_540p_frames"
movie = output / "pokhran_part1_v01b_540p.mp4"
pending = movie.with_stem(movie.stem + "_pending")

if hashlib.sha256(source.read_bytes()).hexdigest() != plan["source_audio"]["sha256"]:
    raise RuntimeError("The preview audio does not match the locked master.")
if not all((frames / f"frame_{frame:04d}.png").is_file() for frame in range(1, 451)):
    raise RuntimeError("The 450 preview frames are incomplete.")

subprocess.run([
    "ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", "30", "-start_number", "1",
    "-i", str(frames / "frame_%04d.png"), "-i", str(source), "-map", "0:v:0", "-map", "1:a:0",
    "-af", "atrim=duration=15", "-c:v", "libx264", "-preset", "fast", "-crf", "17",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movie_timescale", "44100",
    "-movflags", "+faststart", str(pending),
], check=True)

probe = json.loads(subprocess.check_output([
    "ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", str(pending),
]))
video, audio = probe["streams"]
if (video["width"], video["height"], video["r_frame_rate"], video["nb_read_frames"]) != (
    540, 960, "30/1", "450"
):
    raise RuntimeError("The preview frame count, dimensions, or frame rate are incorrect.")
if audio["codec_type"] != "audio" or any(
    abs(float(stream["duration"]) - 15.) > .001 or abs(float(stream["start_time"])) > .0001
    for stream in (video, audio)
):
    raise RuntimeError("The preview streams do not span exactly 0–15 seconds.")

subprocess.run([
    "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(pending),
    "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-",
], check=True)
pending.replace(movie)
(output / "preview_decode_check.json").write_text(json.dumps(probe, indent=2), encoding="utf-8")
