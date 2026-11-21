import bpy,json,time
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v2');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v2_runtime.py'].as_string(),'runtime','exec'))
for f in [1,17,30,32,34,60,90,93,96,97,150,180,215,216,270,300]:
 s.frame_set(f);update(s);s.render.filepath=str(P/f'cal_{f:03d}.png');bpy.ops.render.render(write_still=True)
