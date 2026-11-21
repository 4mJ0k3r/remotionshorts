"""Render the twenty approved calibration frames, resuming missing stills."""
import json
import time
import traceback
from pathlib import Path
import sys

import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from shots import AB_TEST_FRAMES, CALIBRATION

OUT=HERE.parents[1]/'renders'/HERE.name


def queue(scene, frames=CALIBRATION, directory=None, samples=None, background=False):
    directory=directory or OUT/'calibration';directory.mkdir(parents=True,exist_ok=True)
    pending=iter(frames);done=[];timings={}
    original_samples=scene.eevee.taa_render_samples
    if samples is not None:scene.eevee.taa_render_samples=samples
    def tick():
        try:
            frame=next(pending,None)
            if frame is None:
                scene.render.resolution_percentage=100
                scene.eevee.taa_render_samples=original_samples
                (directory/'progress.json').write_text(json.dumps({'state':'complete','frames':done,'seconds':timings}))
                return None
            path=directory/f'{frame:04d}.png'
            if samples is not None or not path.exists():
                scene.frame_set(frame);scene.render.resolution_percentage=50;scene.render.filepath=str(path)
                started=time.perf_counter();bpy.ops.render.render(write_still=True,scene=scene.name)
                timings[frame]=round(time.perf_counter()-started,2)
            done.append(frame)
            (directory/'progress.json').write_text(json.dumps({'state':'rendering','frames':done,'seconds':timings}))
            return .15
        except Exception:
            scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=original_samples
            (directory/'progress.json').write_text(json.dumps({'state':'failed','frames':done,'error':traceback.format_exc()}))
            if background:raise
            return None
    if background:
        while tick() is not None:pass
    else:bpy.app.timers.register(tick,first_interval=.3)


def queue_ab_test(scene):
    queue(scene, AB_TEST_FRAMES, OUT/'ab_test_after', samples=32)


if __name__=='__main__':
    queue(bpy.context.scene)
