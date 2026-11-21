"""Production stages; render is guarded by evidence from calibration/performance."""
import bpy,sys,json,time,runpy,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;P=R/'renders/project_paradox_india_ep03_5rs_blade/v03'
sys.path[:0]=[str(R/'scripts'),str(D)]
action=sys.argv[sys.argv.index('--')+1]
if action=='build':
 import upgrade
 upgrade.apply()
 for name in ('geometry.py','runtime.py'):
  bpy.data.texts[name].from_string((D/name).read_text(encoding='utf8'))
 bpy.context.scene.eevee.taa_render_samples=12
 bpy.context.scene.eevee.gi_cubemap_resolution='256'
 bpy.context.scene.eevee.bokeh_max_size=12
 bpy.context.scene.render.resolution_percentage=50
 exec(compile(bpy.data.texts['START_HERE.py'].as_string(),'START_HERE.py','exec'))
 bpy.context.scene.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'project_paradox_ep03_v03.blend'))
 print('V3 source ready',flush=True)
exec(compile(bpy.data.texts['START_HERE.py'].as_string(),'START_HERE.py','exec'))
runtime=sys.modules['runtime'];S=bpy.context.scene
import shorts_preflight as gate
def render(frame,path,scale=50):
 S.render.resolution_percentage=scale;S.frame_set(frame);runtime.update(frame)
 S.render.filepath=str(path);bpy.ops.render.render(write_still=True)
def animation_chunk(start,end,folder):
 rows=[];cursor=[time.perf_counter()];old=(S.frame_start,S.frame_end,S.render.filepath)
 def written(scene,*args):
  now=time.perf_counter();rows.append({'frame':scene.frame_current,'seconds':now-cursor[0]});cursor[0]=now
  if action=='render' and scene.frame_current%15==0:(P/'render_progress.json').write_text(json.dumps({'completed':scene.frame_current,'total':1401}))
 bpy.app.handlers.render_write.append(written)
 try:
  S.frame_start,S.frame_end=start,end;S.render.resolution_percentage=50;S.render.filepath=str(folder/'frame_####')
  bpy.ops.render.render(animation=True)
  if rows:rows[-1]['seconds']+=time.perf_counter()-cursor[0]
 finally:
  bpy.app.handlers.render_write.remove(written);S.frame_start,S.frame_end,S.render.filepath=old
 assert [r['frame'] for r in rows]==list(range(start,end+1)),'Animation write callbacks missed frames'
 return rows
if action=='build':
 pass
elif action=='calibrate':
 folder=P/'calibration';folder.mkdir(exist_ok=True)
 plan=json.loads((P/'calibration_plan.json').read_text())
 for frame in plan['blender_frames']:
  render(frame,folder/f'frame_{frame:04d}.png')
 print('CALIBRATION_READY',len(plan['blender_frames']),flush=True)
elif action=='benchmark':
 S.render.resolution_percentage=50
 for frame in (1,350,758,1191):
  S.frame_set(frame);bpy.ops.render.render(write_still=False)
 report=gate.benchmark(S,[1,77,191,260,350,520,758,870,918,1021,1191,1281],
                       P/('benchmark_'+time.strftime('%H%M%S')),runtime.update,
                       resolution=(1080,1920,50),p95_limit=1.0,max_limit=1.0)
 image_dimensions={image.name:list(image.size) for image in bpy.data.images
                   if image.source in {'FILE','GENERATED','TILED'} and image.users and max(image.size)>0}
 report['texture_dimensions']=image_dimensions
 report['texture_cap_pass']=all(max(size)<=512 for size in image_dimensions.values())
 if not report['texture_cap_pass']:report['status']='FAIL'
 report['source_sha256']=hashlib.sha256((P/'project_paradox_ep03_v03.blend').read_bytes()).hexdigest()
 (P/'benchmark_gate.json').write_text(json.dumps(report,indent=2))
 print('BENCHMARK',report['status'],report['p95_seconds'],report['max_seconds'],report['sampled_board_peak_gib'])
elif action=='gates':
 from mathutils import Vector as V
 from bpy_extras.object_utils import world_to_camera_view
 import numpy as np
 cuts={a for n,a,b,g in runtime.SHOTS[1:]};issues=[];previous=None;minimum=1e9;triangles=0;contacts=[];blade_bound_checks=0
 # Conservative transformed AABBs: passing this bound guarantees >=.30m
 # distance to the enclosed mesh. A failed bound needs a triangle-level check.
 obstacles=[o for o in S.objects if o.type in ['MESH','CURVE','FONT']]
 cache={};triangle_cache={};resource_checks=[];min_chest_gap=10.0
 shadow_rois={}
 for f in range(1,1402):
  S.frame_set(f);runtime.update(f);bpy.context.view_layer.update();cam=S.camera;p=cam.matrix_world.translation.copy()
  state=(p,cam.rotation_quaternion.copy(),cam.data.lens,(bpy.data.objects['Story focus'].location-p).length)
  if previous and f not in cuts:
   if (p-previous[0]).length>.50 or state[1].rotation_difference(previous[1]).angle>.15 or abs(state[2]-previous[2])>.01:
    issues.append({'frame':f,'kind':'undocumented_camera_jump'})
  previous=state
  if 822<=f<=879:
   for i in range(6):
    blade=bpy.data.objects['Six output blade '+str(i)]
    if blade.hide_render:continue
    for child in blade.children:
     if child.type!='MESH' or child.hide_render:continue
     for corner in child.bound_box:
      projected=world_to_camera_view(S,cam,child.matrix_world@V(corner))
      if projected.z<=0 or not (.02<=projected.x<=.98 and .03<=projected.y<=.97):
       issues.append({'frame':f,'kind':'blade_out_of_frame','blade':i+1});break
    blade_bound_checks+=1
  active=[o for o in obstacles if not o.hide_render];bounds=[]
  deps=bpy.context.evaluated_depsgraph_get()
  if f in [15,153,260,370,520,668,758,870,918,1021,1111,1199,1281,1401]:
   resource_checks.append(dict(frame=f,**gate.validate_resources(S)))
  for actor,table in {0:[('Barber','Barber counter')],1:[('Shopkeeper','Kirana counter'),('Trader','Kirana counter')],2:[('Smuggler','Workshop bench')],3:[('Officer','Mint blueprint desk')]}[S['active_stage']]:
   torso=bpy.data.objects[actor+' connected torso'];top=bpy.data.objects[table+' top']
   body_front=min((torso.matrix_world@V(c)).y for c in torso.bound_box)
   desk_rear=max((top.matrix_world@V(c)).y for c in top.bound_box)
   gap=body_front-desk_rear
   # Officer and blueprint desk may instead be separated horizontally.
   if actor=='Officer':
    body_left=min((torso.matrix_world@V(c)).x for c in torso.bound_box)
    desk_right=max((top.matrix_world@V(c)).x for c in top.bound_box)
    gap=max(gap,body_left-desk_right)
   min_chest_gap=min(min_chest_gap,gap)
   if gap<.12:issues.append({'frame':f,'kind':'chest_gap','actor':actor,'gap_m':gap})
  for o in active:
   dynamic=o.type=='CURVE' and any(word in o.name for word in [' arm ',' leg ','molten stream','molten white core','Pan suspension'])
   if dynamic or o.name not in cache:
    if o.type=='CURVE' and all(spline.type=='POLY' for spline in o.data.splines):
     centers=np.array([point.co[:3] for spline in o.data.splines for point in spline.points])
     radius=o.data.bevel_depth+o.data.extrude
     lo,hi=centers.min(0)-radius,centers.max(0)+radius
     points=np.array([(x,y,z) for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    elif o.get('ink_base_width'):
     # Enclose the source plus maximum camera compensation in object space.
     source=np.array(o.parent.bound_box,dtype=np.float64)
     lo,hi=source.min(0)-.10,source.max(0)+.10
     points=np.array([(x,y,z) for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    else:
     evaluated=o.evaluated_get(deps)
     mesh=evaluated.to_mesh()
     try:
      if not mesh or not mesh.vertices:
       issues.append({'frame':f,'kind':'missing_geometry_bounds','object':o.name})
       points=np.zeros((8,3))
      else:
       co=np.array([v.co[:] for v in mesh.vertices]);lo,hi=co.min(0),co.max(0)
       points=np.array([(x,y,z) for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
     finally:
      evaluated.to_mesh_clear()
    if not dynamic:cache[o.name]=points
   else:points=cache[o.name]
   bounds.append(points)
  matrices=np.array([o.matrix_world for o in active],dtype=np.float64)
  world=np.einsum('nij,nkj->nki',matrices[:,:3,:3],np.array(bounds))+matrices[:,:3,3][:,None,:]
  low,high=world.min(1),world.max(1);position=np.array(p)
  distance=np.sqrt((np.maximum(np.maximum(low-position,position-high),0)**2).sum(1))
  minimum=min(minimum,float(distance.min()))
  for idx in np.where(distance<.30)[0]:issues.append({'frame':f,'kind':'camera_AABB_clearance','object':active[idx].name,'distance':float(distance[idx])})
  if 76<=f<=100:
   corners=[world_to_camera_view(S,cam,V((x,2.875,z))) for x in [-.1,.1] for z in [1.45,1.55]]
   roi=[min(v.x for v in corners),1-max(v.y for v in corners),max(v.x for v in corners),1-min(v.y for v in corners)]
   if all(0<=x<=1 for x in roi):shadow_rois[str(f-1)]=[roi]
  # Every-frame semantic contact follows the current grip target exactly.
  expected=[]
  if S['active_stage']==0:expected=[('Customer',1,'Mirror actual handle grip'),('Barber',1,'Barber press moving ram')]
  elif S['active_stage']==1:expected=[('Shopkeeper',1,'Jar neck grip')]
  elif S['active_stage']==2:expected=[('Smuggler',1,'Ladle handle surface grip')]
  else:expected=[('Officer',-1,'Stamp hand surface grip'),('Officer',1,'Lever hand anchor')]
  for name,side,target in expected:
   point=bpy.data.objects[target].matrix_world.translation
   if target=='Barber press moving ram':point=bpy.data.objects[target].matrix_world@V((-.13,-.24,.05))
   error=(bpy.data.objects[name+f' hand {side}'].matrix_world.translation-point).length
   if error>.002:issues.append({'frame':f,'kind':'grip_anchor','actor':name,'error_m':error})
  deps=bpy.context.evaluated_depsgraph_get()
  for o in active:
   if o.name not in triangle_cache:
    evaluated=o.evaluated_get(deps);mesh=evaluated.to_mesh()
    if mesh:
     mesh.calc_loop_triangles();triangle_cache[o.name]=len(mesh.loop_triangles);evaluated.to_mesh_clear()
    else:triangle_cache[o.name]=0
  # Topology is fixed: all deformation is positions/transforms/visibility.
  triangles=max(triangles,sum(triangle_cache[o.name] for o in active))
  if f%100==0:print('GATES_FRAME',f,flush=True)
 meta=json.loads((P/'shots.json').read_text())
 meta['shadow_checks']=[{'name':'Opening world shadow receiver tracked on plaster','start':75,'end':100,'registration':'tracked','regions_by_frame':shadow_rois,'max_adjacent_luma':1}]
 (P/'shots.json').write_text(json.dumps(meta,indent=2))
 report={'pass':not issues and triangles<200000 and all(r['pass'] for r in resource_checks),'minimum_chest_gap_m':min_chest_gap,'resource_checks':resource_checks,'source_sha256':hashlib.sha256((P/'project_paradox_ep03_v03.blend').read_bytes()).hexdigest(),'minimum_conservative_camera_clearance_m':minimum,'frames_checked':1401,'all_visible_mesh_curve_font_objects_checked':True,'visible_triangles_including_curves_and_text':triangles,'projected_blade_checks':blade_bound_checks,'issues':issues}
 (P/'camera_contact_gate.json').write_text(json.dumps(report,indent=2));print('GATES',report['pass'],minimum,triangles,len(issues),flush=True)
elif action=='render':
 assert json.loads((P/'scope.json').read_text()).get('full_render_authorized') is True,'Full render is stopped by current user scope'
 acceptance=json.loads((P/'visual_acceptance.json').read_text());bench=json.loads((P/'benchmark_gate.json').read_text())
 assert acceptance['pass'] and bench['status']=='PASS','Calibration/performance gates block full rendering'
 assert acceptance['source_sha256']==hashlib.sha256((P/'project_paradox_ep03_v03.blend').read_bytes()).hexdigest(),'Source changed since visual acceptance'
 camera_gate=json.loads((P/'camera_contact_gate.json').read_text());assert camera_gate['pass'] and camera_gate['source_sha256']==acceptance['source_sha256']
 assert bench['source_sha256']==acceptance['source_sha256'],'Benchmark source differs'
 S.render.resolution_percentage=50;folder=P/'frames_540';folder.mkdir(exist_ok=True);rows=[]
 warm=[]
 for f in [1,360,665,1200]:
  t=time.perf_counter();S.frame_set(f);runtime.update(f);bpy.ops.render.render(write_still=False);warm.append({'frame':f,'seconds':time.perf_counter()-t})
 (P/'render_warmup.json').write_text(json.dumps(warm,indent=2))
 total_start=time.perf_counter()
 for start in range(1,1402,120):
  rows.extend(animation_chunk(start,min(1401,start+119),folder))
  (P/'render_timings.json').write_text(json.dumps(rows,indent=2))
 (P/'render_wall_time.json').write_text(json.dumps({'seconds':time.perf_counter()-total_start,'timing_method':'intervals between frame-write callbacks; chunk cleanup assigned to last frame'}))
 (P/'render_timings.json').write_text(json.dumps(rows,indent=2))
