"""Render the approved packed scene at its authored native settings."""
import json
from pathlib import Path
import statistics
import subprocess
from threading import Event, Thread
from time import perf_counter

import bpy


scene = bpy.context.scene
render = scene.render
assert (render.engine, render.resolution_x, render.resolution_y, render.resolution_percentage) == (
    "BLENDER_EEVEE_NEXT", 1080, 1920, 100)
assert (scene.frame_start, scene.frame_end, render.fps, render.fps_base) == (1, 261, 30, 1)
assert not scene.eevee.use_raytracing
output = Path(bpy.data.filepath).parent
frames = output / "native_frames"
frames.mkdir(exist_ok=True)
peak = []
errors = []
stop = Event()


def monitor_gpu():
    while not stop.is_set():
        try:
            memory = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                text=True, timeout=3, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            peak.append(max(float(line) for line in memory.splitlines()) / 1024)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            errors.append(str(error))
            return
        stop.wait(.3)


sampler = Thread(target=monitor_gpu, daemon=True)
sampler.start()
timings = []
try:
    scene.frame_set(scene.frame_start)
    bpy.ops.render.render(write_still=False)
    for frame in range(scene.frame_start, scene.frame_end + 1):
        path = frames / f"frame_{frame:04d}.png"
        pending = path.with_stem(path.stem + "_pending")
        start = perf_counter()
        scene.frame_set(frame)
        render.filepath = str(pending)
        bpy.ops.render.render(write_still=True)
        pending.replace(path)
        timings.append({"frame": frame, "seconds": perf_counter() - start})
finally:
    stop.set()
    sampler.join(timeout=4)
    durations = [row["seconds"] for row in timings]
    report = {
        "resolution": [render.resolution_x, render.resolution_y],
        "frames_completed": len(timings),
        "median_seconds": statistics.median(durations) if durations else None,
        "max_seconds": max(durations, default=None),
        "sampled_board_peak_gib": max(peak, default=None),
        "telemetry_samples": len(peak),
        "telemetry_errors": errors,
        "timings": timings,
    }
    (output / "native_render_report.json").write_text(json.dumps(report, indent=2))
