import bpy,json
from pathlib import Path
from mathutils import Quaternion,Vector
P=Path('D:/remotionshorts/renders/slow_eddie_v13');s=bpy.context.scene;exec(compile(bpy.data.texts['slow_eddie_v13_runtime.py'].as_string(),'runtime','exec'));s.render.resolution_percentage=100
states=json.loads(bpy.data.texts['V13 locked editorial.json'].as_string())
for f in range(24,34):
 s.frame_set(f);update(s);st=states[str(f)];cam.location=st['position'];cam.rotation_mode='QUATERNION';cam.rotation_quaternion=Quaternion(st['rotation']);cam.data.lens=st['lens'];cam.data.shift_x=cam.data.shift_y=0;cam.data.dof.focus_object=None;cam.data.dof.focus_distance=st['focus_distance'];cam.data.dof.aperture_fstop=2;s.render.filepath=str(P/f'launch/frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
