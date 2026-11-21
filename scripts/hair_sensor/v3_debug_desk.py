import bpy
from mathutils import Vector as V
for name,f in [('1E',270),('3E',1069)]:
 s=bpy.data.scenes['V3_'+name];bpy.context.window.scene=s;s.frame_set(f-1);s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();dg.update()
 for o in s.objects:
  if o.name.startswith(('scientist curved leg','scientist torso pivot','scientist shaded pinstriped wardrobe','scientist supported foot')):
   e=o.evaluated_get(dg); print(name,o.name,'loc',list(o.location),'world',list(e.matrix_world.translation),'bbox',min((e.matrix_world@V(p)).y for p in e.bound_box),flush=True)
   if o.type=='CURVE':
    print('coords',[list(p.co) for p in o.data.splines[0].bezier_points],flush=True)
    print('FC',[(fc.data_path,fc.array_index,fc.evaluate(f)) for fc in o.data.animation_data.action.fcurves if fc.array_index==1],flush=True)
    me=e.to_mesh();print('MESH_Y',min((e.matrix_world@v.co).y for v in me.vertices),flush=True);e.to_mesh_clear()
