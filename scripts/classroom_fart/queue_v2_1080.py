"""Separate owned Blender runs give the shared GPU regular release points."""
import subprocess,sys,time,json
import hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
approval=json.loads((OUT/'calibration_v2_approved.json').read_text())
stop=OUT/'logs/stop_preview.request';stop.unlink(missing_ok=True)
for a in range(1,1636,300):
    if stop.exists():print('Stopped our chunk queue by request.',flush=True);break
    b=min(1635,a+299)
    if all((OUT/'v2_1080_frames'/f'{f:04}.png').exists() and str(f) in approval.get('retained_frame_sha256',{}) for f in range(a,b+1)):
        records=[]
        for f in range(a,b+1):
            h=hashlib.sha256((OUT/'v2_1080_frames'/f'{f:04}.png').read_bytes()).hexdigest();assert h==approval['retained_frame_sha256'][str(f)]
            records.append({'f':f,'retained_source_sha256':approval['retained_baseline_source_sha256'],'png_sha256':h})
        (OUT/'logs'/f'v2_1080_chunk_{a:04}_{b:04}.json').write_text(json.dumps({'source_sha256':approval['source_sha256'],'frames':records},indent=2))
        continue
    subprocess.run([sys.executable,str(HERE/'run_blender.py'),'--phase',f'v2-1080-{a:04}-{b:04}','--',approval['source'],'-P',str(HERE/'render_v2_1080.py'),'--',str(a),str(b)],check=True)
    # Both queues check occupied locks every 15s; leave an actual handoff window.
    time.sleep(15)
else:subprocess.run([sys.executable,str(HERE/'finish_v2_1080.py')],check=True)
