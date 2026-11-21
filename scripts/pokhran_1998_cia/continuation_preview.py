"""Render a saved native scene at 50 percent without resaving it."""
import json
from pathlib import Path
import sys
import time

import bpy

scene = bpy.context.scene
settings = scene.render
if (settings.resolution_x, settings.resolution_y, settings.fps, settings.fps_base) != (1080, 1920, 30, 1):
    raise RuntimeError("Unexpected scene dimensions or frame rate.")
output = Path(bpy.data.filepath).parent
settings.resolution_percentage = 50
phase = sys.argv[-1]
if phase == "proof":
    frames = json.loads((output / "shot_map.json").read_text())["proof_frames"]
    folder = output / "preview_stills"
    folder.mkdir(exist_ok=True)
    checks = []
    for frame in frames:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        triangles = 0
        for obj in depsgraph.objects:
            if obj.hide_render or obj.type not in {"MESH", "CURVE", "FONT", "SURFACE"}:
                continue
            mesh = obj.to_mesh()
            if mesh:
                triangles += sum(len(poly.vertices)-2 for poly in mesh.polygons)
                obj.to_mesh_clear()
        if triangles >= 150_000:
            raise RuntimeError(f"Frame {frame} has {triangles} triangles")
        settings.filepath = str(folder / f"frame_{frame:04d}.png")
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        checks.append({"frame": frame, "visible_triangles": triangles, "seconds": time.perf_counter()-started})
    (output / "preview_checks.json").write_text(json.dumps(checks, indent=2))
elif phase == "render":
    folder = output / "preview_540p_frames"
    folder.mkdir(exist_ok=True)
    settings.filepath = str(folder / "frame_")
    settings.use_overwrite = False
    settings.use_placeholder = False
    bpy.ops.render.render(animation=True)
else:
    raise SystemExit("Use proof or render.")
