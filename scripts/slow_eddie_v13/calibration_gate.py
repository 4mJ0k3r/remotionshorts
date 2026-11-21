import bpy
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v13');s=bpy.context.scene;exec(compile(bpy.data.texts['slow_eddie_v13_runtime.py'].as_string(),'runtime','exec'));s.render.resolution_percentage=50
for f in [15,26,60,90,222,286]:
 s.frame_set(f);update(s);s.render.filepath=str(P/f'cal_{f:03d}.png');bpy.ops.render.render(write_still=True)
