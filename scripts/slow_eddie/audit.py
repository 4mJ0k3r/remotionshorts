import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
P=Path('D:/remotionshorts/renders/slow_eddie');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_runtime.py'].as_string(),'runtime','exec'))
values=[]
for f in range(1,301):
 s.frame_set(f);o=bpy.data.objects['Rolling_tumbleweed']
 if not o.hide_render:values.append((f,min((o.matrix_world@V(c)).z for c in o.bound_box)))
(P/'contact_audit.json').write_text(json.dumps({'tumbleweed_floor_min':min(values,key=lambda x:x[1]),'tumbleweed_floor_max':max(values,key=lambda x:x[1]),'all_300_frames_evaluated':True},indent=2))
