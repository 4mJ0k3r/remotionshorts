import bpy,json
from pathlib import Path
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view
P=Path('D:/remotionshorts/renders/slow_eddie_v5');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v5_runtime.py'].as_string(),'runtime','exec'))
rows=[];endpoint=None
for f in [15,60,88,89,90,91,92,93,96,165,195,220,253,282]:
 s.frame_set(f);update(s);bpy.context.view_layer.update();q=s.camera.matrix_world.to_quaternion();r=q@V((1,0,0));b=bpy.data.objects['Copper_bullet'];verts=[b.matrix_world@v.co for v in b.data.vertices];coords=[world_to_camera_view(s,s.camera,p) for p in verts]
 row={'frame':f,'bullet_width_fraction':max(v.x for v in coords)-min(v.x for v in coords),'focus_empty':s.camera.data.dof.focus_object.name,'fstop':s.camera.data.dof.aperture_fstop}
 if 88<=f<=93:
  gun=bpy.data.objects['Eddie_pearl_revolver'];h=bpy.data.objects['Eddie left black holster'];p=bpy.data.objects['Eddie pearl handle'];edge=min((o.matrix_world@V(c)).dot(r) for o in [gun,h,p] for c in o.bound_box);row['gun_gap_m']=edge-max(v.dot(r) for v in verts);assert row['gun_gap_m']>.08
 if f==96:
  c=s.camera;endpoint={'position':list(c.location),'target':list(c.location+(q@V((0,0,-1)))*c.data.dof.focus_distance),'lens':c.data.lens}
 rows.append(row)
s.frame_set(165);update(s);dg=bpy.context.evaluated_depsgraph_get();tri=0
for inst in dg.object_instances:
 o=inst.object
 if o.type in ['MESH','CURVE','FONT']:
  if o.hide_render and not inst.is_instance:continue
  me=o.to_mesh();tri+=sum(len(p.vertices)-2 for p in me.polygons);o.to_mesh_clear()
assert tri<150000,tri
images={im.name:list(im.size) for im in bpy.data.images if im.type=='IMAGE' and im.size[0]};assert max(max(x) for x in images.values())<=1024
(P/'audit.json').write_text(json.dumps({'evaluated_triangles_including_instances':tri,'images':images,'head_diameter_m':.777,'shoulder_width_m':286/1024*2.3,'head_to_shoulder':.777/(286/1024*2.3),'height_including_hat_m':2.3,'head_height_fraction':.777/2.3,'frames':rows,'endpoint96':endpoint,'geometry_nodes':'Western curb scatter','source_assets':['PolyPizza/Google Saloon CC BY','Quaternius Barrel CC0','Quaternius Cube Crate CC0']},indent=2))
