"""Blender CLI entry point. The launcher acquires the GPU lock first."""
import json
import runpy
import sys
import traceback
from pathlib import Path

import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from shots import MASTER_CALIBRATION

OUT=HERE.parents[1]/'renders'/HERE.name
MASTER=OUT/'billionaire_handkerchief.blend'


def run(phase):
    status=OUT/f'headless_{phase}_status.json'
    try:
        status.write_text(json.dumps({'state':'started','phase':phase}))
        if phase=='calibration':
            from build import build
            queue=runpy.run_path(str(HERE/'calibrate.py'))['queue']
            scene=build()
            assert len(scene.timeline_markers)==43 and scene.frame_end==3270
            assert scene.render.use_motion_blur and scene.eevee.taa_render_samples==32
            status.write_text(json.dumps({'state':'saved','objects':len(scene.objects),'motion_blur':scene.render.motion_blur_shutter}))
            queue(scene,MASTER_CALIBRATION,directory=OUT/'calibration_v3_polished',samples=32,background=True)
        elif phase=='review':
            queue=runpy.run_path(str(HERE/'calibrate.py'))['queue']
            bpy.ops.wm.open_mainfile(filepath=str(MASTER))
            queue(bpy.context.scene,MASTER_CALIBRATION,directory=OUT/'calibration_v3_final',samples=32,background=True)
        elif phase=='master':
            queue=runpy.run_path(str(HERE/'preview.py'))['queue']
            bpy.ops.wm.open_mainfile(filepath=str(MASTER))
            queue(bpy.context.scene,master=True,background=True)
        else:
            raise ValueError(f'Unknown Blender phase {phase}')
        status.write_text(json.dumps({'state':'complete','phase':phase}))
    except Exception:
        status.write_text(json.dumps({'state':'failed','error':traceback.format_exc()}))
        raise


if __name__=='__main__':
    run(sys.argv[sys.argv.index('--')+1])
