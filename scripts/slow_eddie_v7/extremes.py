import bpy
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v7');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v7_runtime.py'].as_string(),'runtime','exec'));s.render.resolution_percentage=50
for f in [105,106,140,148,155,160,161,215,216,230,245,246,250,268,292]:
 s.frame_set(f);update(s);s.render.filepath=str(P/f'extreme_{f:03d}.png');bpy.ops.render.render(write_still=True)
