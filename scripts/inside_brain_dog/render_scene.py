"""Run in Blender after loading the saved presenter scene."""
import bpy
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/inside_brain_dog'
scene=bpy.context.scene
mode=sys.argv[sys.argv.index('--')+1]
started=time.time()
status=OUT/f'{mode}_progress.json'


def write(frame,state):
    status.write_text(json.dumps({'state':state,'frame':frame,'elapsed':round(time.time()-started,2)}))


def progress(scene,*args):
    write(scene.frame_current,'rendering')


scene.render.resolution_percentage=50
scene.render.image_settings.file_format='PNG'
bpy.app.handlers.render_post.append(progress)
if mode=='calibration':
    (OUT/'calibration').mkdir(exist_ok=True)
    for frame in [20,50,85,110,135,155]:
        scene.frame_set(frame)
        scene.render.filepath=str(OUT/'calibration'/f'{frame:04}.png')
        bpy.ops.render.render(write_still=True)
else:
    (OUT/'frames').mkdir(exist_ok=True)
    scene.render.filepath=str(OUT/'frames'/'frame_')
    bpy.ops.render.render(animation=True)
write(scene.frame_current if mode=='calibration' else scene.frame_end,'complete')
