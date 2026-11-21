import bpy,sys,json
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view as p
s=bpy.context.scene;exec(compile(bpy.data.texts['slow_eddie_v8_runtime.py'].as_string(),'runtime','exec'))
for f in [135,280]:
 s.frame_set(f);update(s);print('CAM',f,list(cam.location),cam.data.lens,cam.data.sensor_fit,cam.data.sensor_width,cam.data.sensor_height,'clipend',cam.data.clip_end)
 for name in ['V7 eddie rough skull','V7 eddie pinched crown','V7 eddie curved brim']:
  o=O[name];pts=[p(s,cam,o.matrix_world@v.co) for v in o.data.vertices];print(name,'worldz',min((o.matrix_world@v.co).z for v in o.data.vertices),max((o.matrix_world@v.co).z for v in o.data.vertices),'screen',min(v.x for v in pts),max(v.x for v in pts),min(v.y for v in pts),max(v.y for v in pts))
