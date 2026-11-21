import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view as project
P=Path('D:/remotionshorts/renders/slow_eddie_v6');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v6_runtime.py'].as_string(),'runtime','exec'))
result={'resolution':[s.render.resolution_x,s.render.resolution_y],'fps':s.render.fps,'samples':s.eevee.taa_render_samples,'view':s.view_settings.view_transform,'grip_max_error_m':0,'arrival_clearance_m':{},'poses':{}}
for f in range(1,301):
 s.frame_set(f);update(s)
 if f<=35:
  g=O['Challenger_revolver'];error=((g.matrix_world@V((-.20,0,.10)))-O['Challenger grip surface'].location).length;result['grip_max_error_m']=max(error,result['grip_max_error_m'])
 if 88<=f<=95:
  right=cam.matrix_world.to_quaternion()@V((1,0,0));pts=[o.matrix_world@V(c) for o in [O['Eddie_pearl_revolver'],O['Eddie left black holster'],O['Eddie pearl handle']] for c in o.bound_box];b=O['Copper_bullet'];clearance=min(p.dot(right) for p in pts)-max((b.matrix_world@v.co).dot(right) for v in b.data.vertices);result['arrival_clearance_m'][f]=clearance;assert clearance>=.119,clearance
 if f in [15,31,60,90,165,195,253,268,280,288,300]:
  b=O['Copper_bullet'];bounds=[project(s,cam,b.matrix_world@v.co).x for v in b.data.vertices]
  result['poses'][f]={'camera':list(cam.location),'lens_mm':cam.data.lens,'fstop':cam.data.dof.aperture_fstop,'dof':cam.data.dof.use_dof,'head_pitch_deg':math.degrees(O['eddie_head'].rotation_euler.x),'gun_position':list(O['Challenger_revolver'].location),'bullet_screen_width':max(bounds)-min(bounds)}
assert result['grip_max_error_m']<1e-5
assert abs(result['poses'][280]['head_pitch_deg']+10)<.001
assert result['poses'][165]['camera']!=result['poses'][195]['camera']
assert result['poses'][165]['gun_position']!=result['poses'][195]['gun_position']
result['triangles']=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in s.objects if o.type=='MESH' and not o.hide_render)
assert result['triangles']<150000
assert 'Eddie thigh holster strap' not in O
(P/'anchor_motion_audit.json').write_text(json.dumps(result,indent=2));print('AUDIT PASSED',result['triangles'],flush=True)
