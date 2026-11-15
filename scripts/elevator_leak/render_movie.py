"""Render a deterministic, restartable span of the frozen V2 source."""
import bpy
import json
import os
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/elevator_leak'
arguments=sys.argv[sys.argv.index('--')+1:]
start,end=map(int,arguments[:2])
version=int(arguments[2]) if len(arguments)>2 else 2
resolution=int(arguments[3]) if len(arguments)>3 else 540
assert resolution in [540,1080]
tag=f'v{version}' if resolution==540 else f'v{version}_{resolution}p'
DIRECTORY=OUT/f'{tag}_frames'
DIRECTORY.mkdir(exist_ok=True)
scene=bpy.context.scene
scene.render.resolution_x=1080
scene.render.resolution_y=1920
scene.render.resolution_percentage=100 if resolution==1080 else 50
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.compression=15
scene.render.use_lock_interface=True
scene.eevee.taa_render_samples=16
scene['set_ink_enabled']=True
namespace={'__name__':'elevator_runtime'}
exec(bpy.data.texts['elevator_runtime.py'].as_string(),namespace)
started=time.time()
times=[]
last_frame_finished=started


def frame_written(current_scene,*args):
    global last_frame_finished
    frame=current_scene.frame_current
    path=DIRECTORY/f'frame_{frame:04}.png'
    if not path.is_file():
        raise RuntimeError('Missing rendered frame '+str(frame))
    now=time.time()
    times.append(now-last_frame_finished)
    last_frame_finished=now
    status={'state':'rendering','frame':frame,'total':2145,'chunk_start':start,'chunk_end':end,'chunk_elapsed':round(now-started,2),'mean_frame_seconds':round(sum(times[-20:])/len(times[-20:]),3),'renderer_mode':'animation'}
    temporary=OUT/f'movie_{tag}_progress.tmp'
    temporary.write_text(json.dumps(status))
    for attempt in range(3):
        try:
            os.replace(temporary,OUT/f'movie_{tag}_progress.json')
            break
        except PermissionError:
            time.sleep(.03)
    if frame==start:
        try:
            import gpu
            print('ACTIVE_GPU',gpu.platform.vendor_get(),gpu.platform.renderer_get(),flush=True)
        except Exception as error:
            print('GPU platform metadata unavailable',str(error),flush=True)
    if frame%30==0:
        print(f'V{version}_PROGRESS',json.dumps(status),flush=True)


scene.frame_start=start
scene.frame_end=end
scene.render.filepath=str(DIRECTORY/'frame_')
bpy.app.handlers.render_write.append(frame_written)
try:
    bpy.ops.render.render(animation=True)
finally:
    bpy.app.handlers.render_write.remove(frame_written)
print(f'V{version}_CHUNK_COMPLETE',start,end,round(time.time()-started,2),flush=True)
