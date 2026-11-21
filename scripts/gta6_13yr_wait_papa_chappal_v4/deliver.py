"""Package and verify the delivered Blender frame sequence and frozen audio mix."""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

from pipeline import HERE, OUT, ROOT, RESOLUTION, read_json, write_json


def call(args):
    return subprocess.run(args, capture_output=True, check=True).stdout


def samples(path):
    return np.frombuffer(call([
        "ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ac", "2",
        "-ar", "48000", "-f", "f32le", "-"
    ]), dtype="<f4").reshape(-1, 2)


def prefix_manifest(path, frames):
    manifest = read_json(OUT / "shots.json")
    manifest["shots"] = [
        dict(shot, b=min(shot["b"], frames))
        for shot in manifest["shots"] if shot["a"] < frames
    ]
    for key in ("cuts", "continuous_junctions"):
        if key in manifest:
            manifest[key] = [index for index in manifest[key] if index < frames]
    for key in ("transitions", "action_ranges", "xfade"):
        if key in manifest:
            manifest[key] = [
                [start, min(end, frames)] for start, end in manifest[key] if start < frames
            ]
    manifest["shadow_checks"] = [
        check for check in manifest.get("shadow_checks", []) if check["end"] < frames
    ]
    write_json(path, manifest)


def package(folder, frame_count, total, source_sha, narration_sha):
    if frame_count < 1:
        raise SystemExit("No complete native frames to package")
    prefix = frame_count != total
    audio = OUT / "final_mix.wav"
    mix_sha = hashlib.sha256(audio.read_bytes()).hexdigest()
    receipt = read_json(OUT / "build_source.json")
    if (receipt["source_sha256"], receipt["mix_sha256"], receipt["narration_sha256"]) != (
        source_sha, mix_sha, narration_sha
    ):
        raise RuntimeError("The delivered audio and scene must match the frozen build inputs")

    seconds = frame_count / 30
    destination = OUT / f"partial_f{frame_count:04d}" if prefix else OUT
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / f"{HERE.name}_1080p{'_partial' if prefix else ''}.mp4"
    temporary = output.with_name(f".{output.stem}.{os.getpid()}.encoding.mp4")
    try:
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-framerate", "30", "-start_number", "1",
            "-i", str(folder / "frame_%04d.png"), "-i", str(audio),
            "-map", "0:v:0", "-map", "1:a:0", "-t", f"{seconds:.9f}",
            "-vf", "scale=out_color_matrix=bt709", "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(temporary),
        ], check=True)
        info = json.loads(call([
            "ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format",
            "-of", "json", str(temporary)
        ]))
        streams = {entry["codec_type"]: entry for entry in info["streams"]}
        if sorted(streams) != ["audio", "video"] or len(info["streams"]) != 2:
            raise RuntimeError("Unexpected stream or subtitle in the mux")
        video, voice = streams["video"], streams["audio"]
        if (video["width"], video["height"]) != RESOLUTION or int(video["nb_read_frames"]) != frame_count:
            raise RuntimeError("Decoded video size or frame count differs from the native sequence")
        if video["avg_frame_rate"] != "30/1" or abs(float(info["format"]["duration"]) - seconds) > .035:
            raise RuntimeError("Mux rate or runtime does not match the scene")
        if (voice["channels"], voice["sample_rate"]) != (2, "48000"):
            raise RuntimeError("Mux does not contain the stereo 48 kHz mix")
        if any(abs(float(stream["start_time"])) > .001 for stream in (video, voice)):
            raise RuntimeError("A stream does not start at the narration zero point")
        call(["ffmpeg", "-v", "error", "-xerror", "-i", str(temporary), "-f", "null", "-"])
        encoded, reference = samples(temporary), samples(audio)[: frame_count * 1600]
        count = min(len(encoded), len(reference))
        correlation = [
            float(np.corrcoef(encoded[:count, i], reference[:count, i])[0, 1]) for i in range(2)
        ]
        if abs(len(encoded) - len(reference)) > 1024 or not all(r > .998 for r in correlation):
            raise RuntimeError("Encoded audio does not match the frozen mix at zero offset")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)

    manifest = OUT / "shots.json"
    if prefix:
        manifest = destination / "shots_prefix.json"
        prefix_manifest(manifest, frame_count)
    qa_dir = destination / "qa_final"
    qa = subprocess.run([sys.executable, str(ROOT / "scripts/short_qa.py"),
                         str(output), str(qa_dir), str(manifest), "--strict"],
                        capture_output=True, encoding="utf-8", errors="replace")
    (destination / "qa_command.log").write_text(qa.stdout + qa.stderr, encoding="utf-8")
    if qa.returncode not in (0, 2) or not (qa_dir / "report.json").exists():
        raise RuntimeError("QA did not produce a report. See qa_command.log")
    diagnostic = read_json(qa_dir / "report.json")
    if diagnostic["frames"] != frame_count:
        raise RuntimeError("QA frame count differs from the validated mux")
    elapsed = {}
    timing_file = folder / "time_samples.ndjson"
    if timing_file.exists():
        for line in timing_file.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                elapsed[row["frame"]] = row["seconds"]
            except json.JSONDecodeError:
                # An interrupted worker can leave the last timing row incomplete.
                continue
    measured = [wall for frame, wall in elapsed.items() if frame <= frame_count]
    sampled = []
    for path in (OUT / "logs").glob("*-render.gpu.json"):
        info = read_json(path)
        if info.get("source_sha256") == source_sha:
            sampled.append(info)
    peak = max((info["peak_gib"] for info in sampled if info["peak_gib"] is not None), default=None)
    report = {
        "movie": str(output), "frames": frame_count, "total_scene_frames": total,
        "resolution": list(RESOLUTION), "fps": 30, "seconds": seconds, "partial": prefix,
        "decode_pass": True, "subtitle_streams": 0, "audio_zero_offset_correlation": correlation,
        "audio_sample_count": len(encoded), "source_sha256": source_sha,
        "original_narration_sha256": narration_sha, "muxed_mix_sha256": mix_sha,
        "strict_qa_status": diagnostic["status"], "qa_report": str(qa_dir / "report.md"),
        "timing_samples": len(measured), "timing_p95_seconds": float(np.percentile(measured, 95)) if measured else None,
        "timing_max_seconds": max(measured, default=None), "sampled_board_peak_gib": peak,
    }
    write_json(destination / "delivery_validation.json", report)
    print(json.dumps(report, indent=2), flush=True)
