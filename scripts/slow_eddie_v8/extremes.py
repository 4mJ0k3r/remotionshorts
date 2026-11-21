import bpy
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v8');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v8_runtime.py'].as_string(),'runtime','exec'));s.render.resolution_percentage=50
for f in [30,34,35,36,37,84,85,105,106,110,140,155,160,204,205,215,221,223,245,246,255,268,292]:
 s.frame_set(f);update(s);s.render.filepath=str(P/f'extreme_{f:03d}.png');bpy.ops.render.render(write_still=True)
