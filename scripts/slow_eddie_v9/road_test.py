import bpy
from pathlib import Path
s=bpy.context.scene;exec(compile(bpy.data.texts['slow_eddie_v9_runtime.py'].as_string(),'runtime','exec'))
for o in O:
 if o.name.startswith(('Downloaded Western','Porch timber','Porch railing')):
  o.visible_shadow=False
  for m in o.data.materials:
   if hasattr(m,'shadow_method'):m.shadow_method='NONE'
s.frame_set(181);update(s);s.render.resolution_percentage=50;s.render.filepath='D:/remotionshorts/renders/slow_eddie_v9/road_shadow_test.png';bpy.ops.render.render(write_still=True)
