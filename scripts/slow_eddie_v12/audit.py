import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view as uv
P=Path('D:/remotionshorts/renders/slow_eddie_v12');s=bpy.context.scene;exec(compile(bpy.data.texts['slow_eddie_v12_runtime.py'].as_string(),'runtime','exec'))
vs=[];faces=[];names=[]
for o in s.objects:
 if o.type!='MESH' or o.get('v7_outline') or not any(k in o.name.lower() for k in ['porch','barrel','downloaded western','quaternius','crate','facade']):continue
 names.append(o.name);i=len(vs);vs.extend([o.matrix_world@v.co for v in o.data.vertices]);faces.extend([tuple(i+n for n in p.vertices) for p in o.data.polygons])
bvh=BVHTree.FromPolygons(vs,faces);rows=[];states={};s.frame_set(91);update(s)
for f in range(31,301):
 s.frame_current=f;plan(s);bpy.context.view_layer.update();p=s.camera.location.copy();near=bvh.find_nearest(p);dist=near[3] if near else 999
 row={'frame':f,'camera':list(p),'lens':s.camera.data.lens,'shift':[s.camera.data.shift_x,s.camera.data.shift_y],'clearance':dist,'focus':list(bpy.data.objects['V7 hero focus'].location)}
 if 61<=f<=90:
  row['bullet_uv']=list(uv(s,s.camera,flight(f)));row['eddie_hip_uv']=list(uv(s,s.camera,V((0,19,.85))))
 if 91<=f<=121:
  bullet=bpy.data.objects['Copper_bullet'];grip=bpy.data.objects['V7 pearl revolver butt'];tip=max(uv(s,s.camera,bullet.matrix_world@v.co).x for v in bullet.data.vertices);edge=min(uv(s,s.camera,grip.matrix_world@V(c)).x for c in grip.bound_box);row['gap_360px']=(edge-tip)*360;row['bullet_min_x']=min(uv(s,s.camera,bullet.matrix_world@v.co).x for v in bullet.data.vertices)
 if f in [121,122,210,211]:states[f]=row
 rows.append(row)
report={'set_objects':names,'frames':rows,'min_camera_clearance_158_181':min(r['clearance'] for r in rows if 158<=r['frame']<=181),'junction_121_122_exact':all(states[121][k]==states[122][k] for k in ['camera','lens','shift','focus']),'delta_210_211_m':(V(states[210]['camera'])-V(states[211]['camera'])).length}
(P/'junction_audit.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k not in ['set_objects','frames']});print('hold gaps',min(r['gap_360px'] for r in rows if 'gap_360px' in r),max(r['gap_360px'] for r in rows if 'gap_360px' in r));print('min bullet x',min(r['bullet_min_x'] for r in rows if 'bullet_min_x' in r))
