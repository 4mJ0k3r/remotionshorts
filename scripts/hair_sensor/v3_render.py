"""Calibration or preview frames from the same immutable V3 scene file."""
import bpy,sys,json,time
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
data=json.loads((OUT/'shots_v3.json').read_text());mode='preview' if '--preview' in sys.argv else 'calibration'
suffix='_confirm' if '--confirm' in sys.argv else ''
dest=OUT/('v3_frames' if mode=='preview' else 'v3_stills'+suffix);dest.mkdir(exist_ok=True)
progress=[]
for row in data['shots']:
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[row['camera']];s.render.resolution_percentage=50;s.eevee.taa_render_samples=16
    frames=range(row['start_frame'],row['end_frame']+1) if mode=='preview' else [row['sample']]
    for f in frames:
        path=dest/f'{f:04d}.png'
        if mode=='preview' and path.exists():continue
        s.frame_set(f);s.camera=bpy.data.objects[row['camera']];s.render.filepath=str(path);t=time.time();bpy.ops.render.render(write_still=True,scene=s.name)
        progress.append({'shot':row['shot'],'frame':f,'seconds':round(time.time()-t,3)})
        if mode=='calibration' or f%30==0:
            (OUT/('v3_'+mode+suffix+'_progress.json')).write_text(json.dumps(progress[-100:],indent=2));print('V3_PROGRESS',row['shot'],f,round(time.time()-t,2),flush=True)
    if mode=='preview':print('V3_CUT_COMPLETE',row['shot'],flush=True)
print('V3_'+mode.upper()+'_COMPLETE',flush=True)
