"""Render frames 1–450 of the approved packed scene at preview resolution."""
import os
from pathlib import Path

import bpy


scene = bpy.context.scene
settings = scene.render
if (scene.frame_start, scene.frame_end, settings.resolution_x, settings.resolution_y,
        settings.fps, settings.fps_base) != (1, 455, 1080, 1920, 30, 1):
    raise RuntimeError("The preview requires the approved 455-frame v01b scene.")

frames = Path(bpy.data.filepath).parent / "preview_540p_frames"
complete_part = os.environ.get("POKHRAN_PREVIEW_TAIL") == "1"
frames.mkdir(exist_ok=complete_part)
settings.resolution_percentage = 50
settings.image_settings.file_format = "PNG"
settings.filepath = str(frames / "frame_")
if complete_part:
    scene.frame_start = 451 if all((frames / f"frame_{f:04d}.png").is_file()
                                    for f in range(1, 451)) else 1
else:
    scene.frame_end = 450
bpy.ops.render.render(animation=True)
