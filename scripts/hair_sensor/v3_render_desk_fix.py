import bpy,json
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
for row in json.loads((OUT/'shots_v3.json').read_text())['shots']:
    if row['shot'] not in ('1B','1E','2C','2G','3B','3E'):continue
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[row['camera']]
    for f in range(row['start_frame'],row['end_frame']+1):
        s.frame_set(f);s.render.filepath=str(OUT/'v3_frames'/f'{f:04d}.png');bpy.ops.render.render(write_still=True,scene=s.name)
    print('DESK_RANGE_COMPLETE',row['shot'],flush=True)
