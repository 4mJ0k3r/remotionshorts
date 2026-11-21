import bpy,json
from pathlib import Path
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view
P=Path('D:/remotionshorts/renders/slow_eddie_v4');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v4_runtime.py'].as_string(),'runtime','exec'))
rows=[];framing=[]
for f in [88,89,90,91,92,93,94,95,96,165,195,220,253,282]:
 s.frame_set(f);update(s);bpy.context.view_layer.update();q=s.camera.matrix_world.to_quaternion();r=q@V((1,0,0))
 if f<=96:
  b=bpy.data.objects['Copper_bullet'];gun=bpy.data.objects['Eddie_pearl_revolver'];pearl=bpy.data.objects['Eddie pearl handle'];edge=min((o.matrix_world@V(c)).dot(r) for o in [gun,pearl] for c in o.bound_box);bv=max((b.matrix_world@v.co).dot(r) for v in b.data.vertices);leg=bpy.data.objects['eddie_body'].location.dot(r)-.31;rows.append({'frame':f,'gun_gap':edge-bv,'leg_separating_gap':leg-bv});assert min(edge-bv,leg-bv)>.119
 if f==96:
  c=s.camera;target=c.location+(q@V((0,0,-1)))*c.data.dof.focus_distance;endpoint={'position':list(c.location),'target':list(target),'lens':c.data.lens}
 if f in [165,195]:
  parts=[bpy.data.objects[n] for n in ['challenger_head','challenger_body','Challenger_revolver']];pts=[world_to_camera_view(s,s.camera,o.matrix_world@V(c)) for o in parts for c in o.bound_box];e=world_to_camera_view(s,s.camera,bpy.data.objects['eddie_head_pivot'].location);framing.append({'frame':f,'challenger_bounds':[min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts)],'eddie_x':e.x})
dg=bpy.context.evaluated_depsgraph_get();tris=0
for o in s.objects:
 if o.type in ['MESH','CURVE','FONT']:
  ev=o.evaluated_get(dg);me=ev.to_mesh();tris+=sum(len(p.vertices)-2 for p in me.polygons);ev.to_mesh_clear()
assert tris<150000,tris
(P/'audit.json').write_text(json.dumps({'arrival':rows,'framing':framing,'endpoint96':endpoint,'evaluated_triangles':tris},indent=2))
