import bpy,sys,time,json
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_runtime.py'].as_string(),'slow_eddie_runtime.py','exec'))
frames=[1,15,30,31,60,94,95,96,150,180,215,216,258,280,300]
for f in frames:
 s.frame_set(f);s.render.filepath=str(P/f'cal_{f:03d}.png');bpy.ops.render.render(write_still=True)
