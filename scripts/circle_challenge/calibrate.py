"""Render ONLY the fifteen authorized still frames, restartable per frame."""
import bpy,json,time
from pathlib import Path
OUT=Path('D:/remotionshorts/renders/circle_challenge');s=bpy.context.scene
frames=[70,205,330,420,515,655,830,1030,1200,1380,1495,1600,1795,1950,2140]
s.render.resolution_percentage=50;s.eevee.taa_render_samples=16
log=[]
for f in frames:
    path=OUT/f'frame_{f:04d}.png'
    s.frame_set(f);s.render.filepath=str(path);t=time.time()
    bpy.ops.render.render(write_still=True)
    log.append({'frame':f,'seconds':round(time.time()-t,2),'path':str(path)})
    (OUT/'render_progress.json').write_text(json.dumps(log,indent=2));print('CALIBRATION_FRAME',f,flush=True)
print('CALIBRATION_COMPLETE',flush=True)
