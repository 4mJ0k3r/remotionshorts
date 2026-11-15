"""Authorized stills only. No movie-render path is provided."""
import bpy
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/elevator_leak'
scene=bpy.context.scene
namespace={'__name__':'elevator_runtime'}
exec(bpy.data.texts['elevator_runtime.py'].as_string(),namespace)
mode=sys.argv[sys.argv.index('--')+1]
started=time.time()
scene.render.resolution_percentage=50
scene.render.image_settings.file_format='PNG'
scene.eevee.taa_render_samples=16
if mode=='ink_tests':
    samples=[(190,False,'medium_off'),(190,True,'medium_on'),(1340,False,'close_off'),(1340,True,'close_on')]
elif mode=='patch':
    samples=[(frame,True,f'{frame:04}') for frame in [885,970,1090,1210,2050]]
elif mode=='motion_checks':
    samples=[(frame,True,f'{frame:04}') for frame in [820,940,1520,1598,1847,1853]]
elif mode=='cctv_patch':
    samples=[(frame,True,f'{frame:04}') for frame in [1520,1560,1598]]
elif mode=='calibration_v3':
    samples=[(frame,True,f'{frame:04}') for frame in [50,130,190,260,320,400,510,570,620,690,885,970,1090,1210,1340,1460,1560,1640,1840,1910,2050]]
elif mode=='rig_checks_v3':
    samples=[(frame,True,f'{frame:04}') for frame in [133,790,793,1418,1422,1624,1628,1710]]
else:
    samples=[(frame,True,f'{frame:04}') for frame in [50,130,190,260,320,400,510,570,620,690,885,970,1090,1210,1340,1460,1560,1710,1840,1910,2050]]
directory=OUT/('calibration' if mode in ['patch','cctv_patch'] else mode)
directory.mkdir(parents=True,exist_ok=True)
for frame,ink,name in samples:
    scene['set_ink_enabled']=ink
    scene.frame_set(frame)
    namespace['update'](scene)
    scene.render.filepath=str(directory/f'{name}.png')
    bpy.ops.render.render(write_still=True)
    (OUT/f'{mode}_progress.json').write_text(json.dumps({'state':'rendering','last':name,'frame':frame,'elapsed':round(time.time()-started,2)}))
scene['set_ink_enabled']=True
scene.frame_set(190)
namespace['update'](scene)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'elevator_leak.blend'))
(OUT/f'{mode}_progress.json').write_text(json.dumps({'state':'complete','renders':len(samples),'elapsed':round(time.time()-started,2)}))
