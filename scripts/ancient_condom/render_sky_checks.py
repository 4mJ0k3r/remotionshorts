"""Full-resolution source checks and representative renderer timing."""
import bpy,json,time,sys
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');rows=json.loads((OUT/'shots.json').read_text())['shots'];records=[]
for f in ([1315,1830] if '--confirm' in sys.argv else [40,1315,1760,1830]):
 row=next(x for x in rows if x['start_frame']<=f<=x['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.resolution_percentage=100
 mode='CPU'
 if hasattr(s.render,'compositor_device'):
  try:s.render.compositor_device='GPU';mode=s.render.compositor_device
  except TypeError:pass
 s.render.filepath=str(OUT/'qa'/f'sky_f{f:04}.png');t=time.monotonic();bpy.ops.render.render(write_still=True,scene=s.name);records.append({'frame':f,'seconds':time.monotonic()-t,'compositor':mode});print('FULL HD CHECK',records[-1],flush=True)
(OUT/'qa/sky_benchmark.json').write_text(json.dumps(records,indent=2))
