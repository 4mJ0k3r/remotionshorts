import bpy,json
from mathutils import Vector as V
s=bpy.data.scenes['V3_1E'];bpy.context.window.scene=s
h=next(o for o in s.objects if o.name.startswith('Tapered keratin hero filament'));t=bpy.data.objects[h['filament_target']];p=h.data.splines[0].bezier_points[-1].co
for fc in h.animation_data.action.fcurves:
 if fc.array_index in (0,2) or fc.data_path=='rotation_euler': print('FC',fc.data_path,fc.array_index,[(p.co.x,p.co.y) for p in fc.keyframe_points if p.co.x in (250,251,274)],flush=True)
for f in [250,250,250,260,270,274,291]:
 s.frame_set(f+1);s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();dg.update();he=h.evaluated_get(dg);te=t.evaluated_get(dg)
 print('DEBUG_CONTACT',f,'loc',tuple(h.location),'rot',tuple(h.rotation_euler),'scale',tuple(h.scale),'parent',tuple(h.parent.location),'tip',tuple(p),'actual',tuple(he.matrix_world@p),'tool',tuple(te.matrix_world.translation),flush=True)
