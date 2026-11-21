import bpy
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v8');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v8_runtime.py'].as_string(),'runtime','exec'))
s.render.resolution_percentage=50
for f in [15,31,60,90,96,135,165,195,222,280]:
 s.frame_set(f);update(s);s.render.filepath=str(P/f'cal_{f:03d}.png');bpy.ops.render.render(write_still=True)
