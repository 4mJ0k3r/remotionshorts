import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view as project
P=Path('D:/remotionshorts/renders/slow_eddie_v8');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v8_runtime.py'].as_string(),'runtime','exec'))
r={'frames':300,'resolution':[s.render.resolution_x,s.render.resolution_y],'fps':s.render.fps,'engine':s.render.engine,'samples':s.eevee.taa_render_samples,'ray_tracing':s.eevee.use_raytracing,'grip_max_error_m':0,'arrival_clearance_m':{},'poses':{},'design':'V6 rough harmonic contour and pressure border; V6 feature coordinates/colors/proportions transferred to lit closed 3D volumes'}
for f in sorted(set(list(range(1,37))+list(range(85,106))+[60,135,165,195,216,222,235,245,246,250,254,268,280,292,300])):
 s.frame_set(f);update(s)
 if f<=36:
  gun=O['Challenger_revolver'];r['grip_max_error_m']=max(r['grip_max_error_m'],((gun.matrix_world@V((-.2,0,.1)))-O['V7 aiming grip'].location).length)
 if 85<=f<=105:
  right=cam.matrix_world.to_quaternion()@V((1,0,0));b=O['Copper_bullet'];edge=min((o.matrix_world@V(c)).dot(right) for o in [O['V7 eddie contoured sheath'],O['Eddie_pearl_revolver'],O['V7 pearl revolver butt']] for c in o.bound_box);clearance=edge-max((b.matrix_world@v.co).dot(right) for v in b.data.vertices);r['arrival_clearance_m'][f]=clearance;assert clearance>=.0199
 if f in [15,31,60,90,96,135,165,195,222,280]:
  r['poses'][f]={'camera':list(cam.location),'lens':cam.data.lens,'head_pitch_deg':math.degrees(O['V7 eddie head pivot'].rotation_euler.x),'challenger_head_uv':list(project(s,cam,O['V7 challenger head pivot'].matrix_world.translation)),'eddie_head_uv':list(project(s,cam,O['V7 eddie head pivot'].matrix_world.translation))}
# Required framing/pose checks complement the comparison images.
s.frame_set(135);update(s);hat=O['V7 eddie pinched crown'];hat_uv=[project(s,cam,hat.matrix_world@v.co) for v in hat.data.vertices];r['panel06_hat_max_y']=max(v.y for v in hat_uv);assert r['panel06_hat_max_y']<.98
s.frame_set(222);update(s);r['panel09_challenger_camera_depth']=project(s,cam,O['V7 challenger head pivot'].matrix_world.translation).z;assert r['panel09_challenger_camera_depth']<0
for f in [60,90]:
 s.frame_set(f);update(s);axis=O['Copper_bullet'].rotation_quaternion@V((0,1,0));r['bullet_axis_pitch_'+str(f)]=math.degrees(math.asin(axis.z))
assert -15<r['bullet_axis_pitch_60']<-11
assert abs(r['bullet_axis_pitch_90'])<.001
r['grip_angle_degrees']=math.degrees(O['V7 pearl revolver butt'].rotation_euler.y)
assert r['grip_max_error_m']<1e-5
assert 'Foreground shoulder silhouette' not in O
assert bpy.data.materials['V7 thin warm ink'].use_backface_culling_shadow
s.frame_set(15);update(s);dep=bpy.context.evaluated_depsgraph_get();tris=0
for ins in dep.object_instances:
 o=ins.object
 if o.type not in ['MESH','CURVE'] or o.hide_render:continue
 me=o.to_mesh();tris+=sum(len(p.vertices)-2 for p in me.polygons);o.to_mesh_clear()
r['evaluated_triangles_including_instances']=tris
r['packed_image_max']=max(max(im.size) for im in bpy.data.images if im.type=='IMAGE' and im.size[0])
# The contour is intentionally stable and non-circular, matching V6 artwork rather than adding noise over time.
for who in ['challenger','eddie']:
 o=O['V7 '+who+' rough skull'];r[who+'_head_mesh_vertices']=len(o.data.vertices);r[who+'_head_bounds']=[list(x) for x in o.bound_box]
(P/'audit.json').write_text(json.dumps(r,indent=2));print('AUDIT PASSED',tris,flush=True)
