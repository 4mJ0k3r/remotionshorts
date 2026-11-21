import bpy
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v12');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v12_runtime.py'].as_string(),'runtime','exec'))
s.render.resolution_percentage=50
for f in sorted(set([15,26,35,60,90,135,181,222,256,286,24,31,61,74,76,78,91,121,122,167,169,171,210,211,280,300])):
 s.frame_set(f);update(s);s.render.filepath=str(P/f'cal_{f:03d}.png');bpy.ops.render.render(write_still=True)
