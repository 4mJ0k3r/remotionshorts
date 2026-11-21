import bpy,json,math
from pathlib import Path
from mathutils import Vector
P=Path('D:/remotionshorts/renders/slow_eddie_v11');s=bpy.context.scene;t=bpy.data.texts['slow_eddie_v11_runtime.py'];t.from_string(Path('D:/remotionshorts/scripts/slow_eddie_v11/runtime.py').read_text());exec(compile(t.as_string(),t.name,'exec'))
a=[];positions={};axes={}
for f in range(25,92):
 s.frame_set(f);update(s);b=bpy.data.objects['Copper_bullet'];positions[f]=b.location.copy();axes[f]=b.rotation_quaternion@Vector((0,1,0))
for f in range(25,91):
 v=positions[f+1]-positions[f];angle=math.degrees(axes[f].angle(v));a.append({'frame':f,'angle_deg':angle,'speed':v.length});assert angle<.1
(P/'velocity_audit.json').write_text(json.dumps(a,indent=2));s.frame_set(1);update(s);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v11.blend'))
