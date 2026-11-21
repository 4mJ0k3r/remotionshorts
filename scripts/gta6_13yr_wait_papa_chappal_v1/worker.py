"""Blender-side work. The host launcher owns the live GPU lock."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "renders" / HERE.name
SOURCE = OUT / (HERE.name + ".blend")
sys.path[:0] = [str(HERE), str(ROOT / "scripts")]

action, payload = sys.argv[sys.argv.index("--") + 1:]
parameters = json.loads(payload)
sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
if parameters["source_sha256"] != sha:
    raise RuntimeError("The saved Blender source changed before the worker opened it")
bootstrap = bpy.data.texts["START_HERE.py"].as_string()
exec(compile(bootstrap, "START_HERE.py", "exec"))
runtime = sys.modules["runtime"]
scene = bpy.context.scene
size = scene.render.resolution_x, scene.render.resolution_y, scene.render.fps, scene.render.fps_base
if size != (1080, 1920, 30, 1.0):
    raise RuntimeError(f"Unexpected master output geometry and fps: {size}")

def dump(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)

def verify_audio():
    sounds = [strip.sound for strip in scene.sequence_editor.sequences_all if strip.type == "SOUND"]
    if len(sounds) != 1 or sounds[0].packed_file is None:
        raise RuntimeError("The master does not contain exactly one packed narration mix")
    mix = OUT / "final_mix.wav"
    packed_sha = hashlib.sha256(sounds[0].packed_file.data).hexdigest()
    if hashlib.sha256(mix.read_bytes()).hexdigest() != packed_sha:
        raise RuntimeError("The external mix differs from the audio packed in the master")
    dump(OUT / "build_source.json", {
        "source_sha256": sha,
        "mix_sha256": packed_sha,
        "narration_sha256": runtime.T["audio_sha256"],
        "frames": scene.frame_end,
    })

def configure(scale):
    scene.render.resolution_percentage = scale
    scene.render.image_settings.file_format = "PNG"
    scene.render.use_sequencer = False
    scene.render.use_file_extension = True
    scene.render.use_stamp = False
    scene.render.use_overwrite = True
    scene.render.use_placeholder = False

def render_stills(frames, folder):
    configure(50)
    folder.mkdir(parents=True, exist_ok=True)
    for frame in frames:
        scene.frame_set(frame)
        runtime.update(frame)
        scene.render.filepath = str(folder / f"frame_{frame:04d}.png")
        bpy.ops.render.render(write_still=True)

if action == "calibrate":
    render_stills(parameters["frames"], Path(parameters["folder"]))
elif action == "benchmark":
    from shorts_preflight import benchmark
    configure(100)
    now = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    folder = OUT / "benchmarks" / f"{sha[:12]}-{now}"
    frames = parameters["frames"]
    report = benchmark(scene, frames, folder, runtime.update)
    report.update(source_sha256=sha, directory=str(folder), samples=scene.eevee.taa_render_samples)
    dump(OUT / "benchmark_gate.json", report)
    print("Benchmark", report["status"], report["p95_seconds"], report["max_seconds"], report["sampled_board_peak_gib"], flush=True)
    if report["status"] != "PASS":
        raise RuntimeError("The native benchmark did not meet its envelope")
elif action == "audit":
    import audit
    result = audit.run(runtime, OUT, SOURCE)
    if not result["pass"]:
        raise RuntimeError("The camera and contact audit reported issues")
elif action == "render":
    verify_audio()
    configure(100)
    folder = Path(parameters["folder"])
    folder.mkdir(parents=True, exist_ok=True)
    start, end = parameters["start"], scene.frame_end
    scene.frame_start = start
    scene.render.filepath = str(folder / "frame_####")
    progress = OUT / "render_progress.json"
    initial = time.perf_counter()
    previous = [initial]
    timings = folder / "time_samples.ndjson"

    def written(active_scene, *_):
        frame = active_scene.frame_current
        now = time.perf_counter()
        with timings.open("a", encoding="utf-8") as output:
            output.write(json.dumps({"frame": frame, "seconds": now - previous[0]}) + "\n")
        previous[0] = now
        if frame == start or frame % 15 == 0 or frame == end:
            dump(progress, {"completed": frame, "total": end, "source_sha256": sha, "folder": str(folder)})
    bpy.app.handlers.render_write.append(written)
    dump(progress, {"completed": start - 1, "total": end, "source_sha256": sha, "folder": str(folder)})
    try:
        bpy.ops.render.render(animation=True)
    finally:
        bpy.app.handlers.render_write.remove(written)
    if json.loads(progress.read_text())["completed"] != end:
        raise RuntimeError("Animation ended without writing the last native frame")
    dump(OUT / "render_wall_time.json", {"seconds": time.perf_counter() - initial,
                                        "first_frame_this_run": start, "last_frame": end, "source_sha256": sha})
else:
    raise RuntimeError(f"Unknown action: {action}")
