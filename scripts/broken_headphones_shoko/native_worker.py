"""Reopen, benchmark or render a saved Shoko part."""
import json
import sys
from pathlib import Path
from uuid import uuid4

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shorts_preflight as gate

phase, output, length, *frame_args = sys.argv[sys.argv.index("--") + 1:]
output = Path(output)
scene = bpy.context.scene
render = scene.render
assert (render.resolution_x, render.resolution_y, render.resolution_percentage,
        render.fps, render.fps_base, scene.frame_end) == (1080, 1920, 100, 30, 1, int(length))
assert all(image.packed_file for image in bpy.data.images if image.source == "FILE")
render.image_settings.file_format = "PNG"
render.image_settings.compression = 12

if phase == "proof":
    frames = list(map(int, frame_args))
    native_stills = output / f"native_stills_{uuid4().hex[:8]}"
    native_stills.mkdir()
    resources = []
    for frame in frames:
        scene.frame_set(frame)
        resources.append(gate.validate_resources(scene))
    report = gate.benchmark(scene, frames, native_stills, p95_limit=1.8, max_limit=2.0)
    report["max_evaluated_triangles"] = max(item["visible_triangles"] for item in resources)
    report["native_stills_dir"] = native_stills.name
    if any(not item["pass"] or item["target_exceeded"] for item in resources):
        report["status"] = "FAIL"
    (output / "benchmark.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if report["status"] != "PASS":
        raise RuntimeError("Native benchmark failed")
else:
    frames_dir = output / "native_frames"
    frames_dir.mkdir(exist_ok=True)
    render.image_settings.compression = 0
    render.filepath = str(frames_dir / "frame_")
    if frame_args:
        first,last=map(int,frame_args[0].split(":"))
        if not 1<=first<=last<=scene.frame_end:
            raise ValueError("Partial render is outside the saved scene range")
        scene.frame_start,scene.frame_end=first,last
    render.use_overwrite = bool(frame_args)
    bpy.ops.render.render(animation=True)
