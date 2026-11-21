import bpy,json,time
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v3');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v3_runtime.py'].as_string(),'runtime','exec'))
s.render.resolution_percentage=50
for f in [15,60,93,165,195,222,253,282]:
 s.frame_set(f);update(s);s.render.filepath=str(P/f'cal_{f:03d}.png');bpy.ops.render.render(write_still=True)
