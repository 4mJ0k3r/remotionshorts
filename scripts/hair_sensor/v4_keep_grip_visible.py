"""Roll the free filament into the fixed camera crop; preserve the full .45m root lift."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector as V,Euler
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
for name in ('V3_1C','V3_1D'):
    s=bpy.data.scenes[name];h=next(o for o in s.objects if 'v4_grip_index' in o);tool=bpy.data.objects[h['v4_tweezer']];point=V(h.data.splines[0].bezier_points[h['v4_grip_index']].co)
    for f in range(s.frame_start,s.frame_end+1):
        if f<185:u=max(0,min(1,(f-169)/16));e=u*u*(3-2*u);dz=0;stretch=1+.45*e;angle=0
        else:u=max(0,min(1,(f-185)/25));e=u*u*(3-2*u);dz=.025+.425*e;stretch=1.45-.45*e;angle=math.radians(50)*e
        rotation=Euler((angle,0,0));local=rotation.to_matrix()@V((point.x,point.y,point.z*stretch));h.location=(0,point.y-local.y,.05+dz);h.scale=(1,1,stretch);h.rotation_euler=rotation
        for prop in ('location','scale','rotation_euler'):h.keyframe_insert(prop,frame=f)
        tool.location=h.location+local;tool.keyframe_insert('location',frame=f)
    for ob in (h,tool):
        for fc in ob.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_v4_master.blend'))
print('FREE HAIR ROLLED INTO ORIGINAL CAMERA; ROOT LIFT REMAINS .45m.',flush=True)
