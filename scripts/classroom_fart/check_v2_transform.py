import bpy,sys,json
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');sys.path.insert(0,str(OUT.parents[1]/'scripts/classroom_fart'))
s=bpy.data.scenes['CF_1A'];bpy.context.window.scene=s;s.frame_set(1)
from optimize_static import optimize
result=optimize(s)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'classroom_fart_surgical_v2_checked.blend'))
folder=OUT/'v2_transform_check';folder.mkdir(exist_ok=True)
rows=json.loads((OUT/'shots_v2.json').read_text())['shots']
for f in [300,855,1007,1145,1360,1446]:
    row=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.filepath=str(folder/f'{f:04}.png');bpy.ops.render.render(write_still=True)
