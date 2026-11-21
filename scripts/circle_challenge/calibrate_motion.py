"""Render representative frames from the motion revision and restore output settings."""
from pathlib import Path
import bpy
import json

out=Path('D:/remotionshorts/renders/circle_challenge/v4_frames')
out.mkdir(exist_ok=True)
scene=bpy.context.scene
frames=[70,205,330,420,515,655,830,947,1005,1200,1380,1495,1600,1795,1895,1950,2050,2140]
original=(scene.render.filepath,scene.render.image_settings.file_format,scene.render.use_file_extension)
log=[]
try:
    scene.render.image_settings.file_format='PNG'
    scene.render.use_file_extension=True
    for frame in frames:
        scene.frame_set(frame)
        path=out/f'frame_{frame:04d}.png'
        scene.render.filepath=str(path)
        result=bpy.ops.render.render(write_still=True,scene=scene.name)
        if 'FINISHED' not in result or not path.is_file():
            raise RuntimeError(f'Calibration frame {frame} failed')
        log.append(frame)
        (out/'motion_stills.json').write_text(json.dumps(log))
finally:
    scene.render.filepath,scene.render.image_settings.file_format,scene.render.use_file_extension=original
    scene.frame_set(70)

