import bpy
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v11');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v11_runtime.py'].as_string(),'runtime','exec'));s.render.resolution_percentage=50
for f in range(1,31):
 s.frame_set(f);update(s);s.render.filepath=str(P/f'opening/frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
