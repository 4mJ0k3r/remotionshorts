import bpy,json
from pathlib import Path
from mathutils import Vector as V
P=Path('D:/remotionshorts/renders/slow_eddie_v2');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v2_runtime.py'].as_string(),'runtime','exec'))
rows=[]
for f in range(90,97):
 s.frame_set(f);update(s);bpy.context.view_layer.update();r=s.camera.matrix_world.to_quaternion()@V((1,0,0));b=bpy.data.objects['Copper_bullet'];points=[]
 for name in ['Eddie_pearl_revolver','Eddie pearl handle']:
  o=bpy.data.objects[name];points.extend(o.matrix_world@V(c) for c in o.bound_box)
 left=min(p.dot(r) for p in points);right=max((b.matrix_world@v.co).dot(r) for v in b.data.vertices);rows.append({'frame':f,'projected_gap_m':left-right})
# Evaluated triangle count includes curves, text, bevels and ink.
s.frame_set(15);dg=bpy.context.evaluated_depsgraph_get();tri=0
for o in s.objects:
 if o.type in ['MESH','CURVE','FONT']:
  ev=o.evaluated_get(dg);m=ev.to_mesh();tri+=sum(len(p.vertices)-2 for p in m.polygons);ev.to_mesh_clear()
(P/'audit.json').write_text(json.dumps({'arrival_clearances':rows,'evaluated_triangles':tri},indent=2));assert tri<150000
