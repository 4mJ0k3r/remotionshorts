"""One consolidated V2 calibration batch: twelve tiles plus contact extremes."""
import bpy,json,time,sys
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\bamboo_ambush');version='v2_confirm' if '--confirm' in sys.argv else 'v2';CAL=OUT/('calibration_'+version);CAL.mkdir(exist_ok=True);s=bpy.context.scene;s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=50;s.eevee.taa_render_samples=12
if hasattr(s.render,'compositor_device'):s.render.compositor_device='GPU'
frames=[45,140,240,345,430,495,560,660,735,800,860,910,22,44,285,325,769,771,773,834,835,889,891,893,935];times=[]
for f in frames:
 s.frame_set(f);s.render.filepath=str(CAL/f'{f:04d}.png');t=time.monotonic();bpy.ops.render.render(write_still=True);times.append({'frame':f,'seconds':time.monotonic()-t});print('V2 CAL',f,times[-1]['seconds'],flush=True)
(OUT/(version+'_calibration_times.json')).write_text(json.dumps(times,indent=2))
