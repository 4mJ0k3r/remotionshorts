"""User-authorized two-still contact recheck, preserving the other eighteen tiles."""
import bpy,json,time,sys
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');data=json.loads((OUT/'shots.json').read_text());times=[];version='v5' if '--v5' in sys.argv else 'v4'
for f in [1315,1435]:
 row=next(x for x in data['shots'] if x['start_frame']<=f<=x['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.resolution_percentage=50;s.render.filepath=str(OUT/('calibration_'+version)/f'f{f:04}.png');t=time.monotonic();bpy.ops.render.render(write_still=True,scene=s.name);assert Path(s.render.filepath).is_file();times.append({'frame':f,'seconds':time.monotonic()-t});print('CONTACT RECHECK',f,flush=True)
(OUT/f'calibration_times_{version}.json').write_text(json.dumps(times,indent=2))
