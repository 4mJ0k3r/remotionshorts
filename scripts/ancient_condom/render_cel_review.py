"""Only the four changed character tiles; all existing process tiles are preserved."""
import bpy,json,time,sys
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');data=json.loads((OUT/'shots.json').read_text());times=[];version='cel_v2' if '--v2' in sys.argv else 'cel_v1'
for f in [40,115,1760,1830]:
 row=next(x for x in data['shots'] if x['start_frame']<=f<=x['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.resolution_percentage=50;s.render.filepath=str(OUT/('calibration_'+version)/f'f{f:04}.png');t=time.monotonic();bpy.ops.render.render(write_still=True,scene=s.name);assert Path(s.render.filepath).is_file();times.append({'frame':f,'seconds':time.monotonic()-t});print('ILLUSTRATED CAST CHECK',f,flush=True)
(OUT/f'calibration_times_{version}.json').write_text(json.dumps(times,indent=2))
