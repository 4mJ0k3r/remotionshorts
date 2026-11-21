"""Full-resolution production frames; warmed timings across every cut."""
import bpy,json,time,hashlib,gpu
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');frames=OUT/'v2_1080_frames';frames.mkdir(exist_ok=True)
pending=OUT/'v2_1080_pending';pending.mkdir(exist_ok=True)
approval=json.loads((OUT/'calibration_v2_approved.json').read_text());digest=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();assert digest==approval['source_sha256']
rows=json.loads((OUT/'shots_v2.json').read_text())['shots'];results=[]
for row in rows:
    mid=(row['start_frame']+row['end_frame'])//2
    for f in [mid,mid+1,mid+2]:
        if (OUT/'logs/stop_preview.request').exists():raise SystemExit('Stopped by user')
        s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.resolution_percentage=100;s.eevee.taa_render_samples=16;s.render.filepath=str(pending/f'{f:04}.png')
        t=time.monotonic();bpy.ops.render.render(write_still=True);elapsed=time.monotonic()-t;(pending/f'{f:04}.png').replace(frames/f'{f:04}.png')
        results.append({'shot':row['shot'],'frame':f,'seconds':elapsed,'warm':f!=mid})
        (OUT/'1080_timing_progress.json').write_text(json.dumps({'source_sha256':digest,'measurements':results,'gpu':gpu.platform.renderer_get()},indent=2))
        print('1080 TIMING',row['shot'],f,round(elapsed,3),flush=True)
