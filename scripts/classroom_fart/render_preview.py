"""Render an explicitly reviewed source, in resumable bounded GPU windows."""
import bpy,json,sys,hashlib,time
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
a,b=map(int,args[:2]);approval=json.loads((OUT/'calibration_approved.json').read_text())
source=Path(bpy.data.filepath);digest=hashlib.sha256(source.read_bytes()).hexdigest()
if digest!=approval['source_sha256']:raise RuntimeError('Reviewed source changed; calibration must be reviewed again.')
rows=json.loads((OUT/'shots.json').read_text())['shots'];records=[]
for f in range(a,b+1):
    target=OUT/'frames'/f'{f:04}.png'
    if target.exists():
        expected=approval.get('retained_frame_sha256',{}).get(str(f))
        if expected:
            assert hashlib.sha256(target.read_bytes()).hexdigest()==expected,'Retained frame changed'
            records.append({'f':f,'retained_source_sha256':approval['retained_baseline_source_sha256'],'png_sha256':expected})
        continue
    row=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f)
    s.render.resolution_percentage=50;s.eevee.taa_render_samples=16;s.render.filepath=str(target)
    t=time.monotonic();bpy.ops.render.render(write_still=True);records.append({'f':f,'seconds':round(time.monotonic()-t,3)})
(OUT/'logs'/f'chunk_{a:04}_{b:04}.json').write_text(json.dumps({'source_sha256':digest,'frames':records},indent=2))
