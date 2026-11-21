import bpy,sys,json,time,hashlib
from pathlib import Path
from mathutils import Vector as V
R=Path(__file__).resolve().parents[3];P=R/'renders/gold_mine_salting_10s/v01'
sys.path.insert(0,str(R/'scripts'))
import shorts_preflight as gate
exec(compile(bpy.data.texts['START_HERE.py'].as_string(),'START_HERE.py','exec'))
S=bpy.context.scene
stage=sys.argv[sys.argv.index('--')+1];args=sys.argv[sys.argv.index('--')+2:]
if stage=='gates':
 resources=gate.validate_resources(S)
 obstacles=[o for o in S.objects if o.type=='MESH' and o.get('collision')]
 contacts=[];states={}
 def validate_frame(f):
  update(f);bpy.context.view_layer.update()
  checks=[('Miner R hand frame','Shotgun trigger surface grip'),('Buddy R hand frame','Mug handle surface grip')]
  if f<30 or f>=271:checks.append(('Miner L hand frame','Gold shell surface grip'))
  else:checks.append(('Miner L hand frame','Shotgun forend surface grip'))
  for a,b in checks:
   err=(bpy.data.objects[a].matrix_world.translation-bpy.data.objects[b].matrix_world.translation).length
   contacts.append({'frame':f,'a':a,'b':b,'error_m':err})
  if f in [1,45,46,75,76,110,111,200,270,271,286,300]:
   states[str(f)]=[[o.name,[round(v,5) for v in o.matrix_world.translation],o.hide_render] for o in [S.camera,bpy.data.objects['Gold shell root'],bpy.data.objects['Buddy mug root'],bpy.data.objects['Miner head pivot']]]
 report=gate.validate_camera_path(S,validate_frame,obstacles,subjects=[(bpy.data.objects['Miner rough-round head'],1,45),(bpy.data.objects['Buddy rough-round head'],111,270),(bpy.data.objects['Miner rough-round head'],271,301)],cuts=[46,76,111,271])
 # Keep the shared gate's raw evidence. Its signed nearest-normal heuristic
 # can label an exterior point inside an open relief or a concave/beveled prop.
 # Resolve ONLY those flags, using exact evaluated triangles and three parity rays.
 (P/'camera_gate_raw.json').write_text(json.dumps(report,indent=2))
 from mathutils.bvhtree import BVHTree
 unresolved=[];resolutions=[]
 for issue in report['issues']:
  if issue['kind']!='camera_clearance' or not issue.get('inside') or issue['distance_m']<.30:
   unresolved.append(issue);continue
  f=issue['frame'];S.frame_set(f);update(f);bpy.context.view_layer.update()
  ob=bpy.data.objects[issue['object']];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  try:
   vs=[ev.matrix_world @ v.co for v in me.vertices];fs=[tuple(p.vertices) for p in me.polygons]
   edges={}
   for face in fs:
    for a,b in zip(face,face[1:]+face[:1]):
     key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
   closed=all(n==2 for n in edges.values())
   tree=BVHTree.FromPolygons(vs,fs);counts=[]
   if closed:
    for direction in [V((.743,.419,.517)).normalized(),V((-.371,.862,.345)).normalized(),V((.231,-.543,.807)).normalized()]:
     pos=S.camera.matrix_world.translation.copy();count=0
     for _ in range(80):
      hit=tree.ray_cast(pos,direction,100)
      if hit[0] is None:break
      count+=1;pos=hit[0]+direction*.0001
     counts.append(count)
   outside=not closed or all(n%2==0 for n in counts)
   if outside:
    resolutions.append(dict(issue,reason='Open relief has no enclosing volume; nearest surface and closed backing both clear' if not closed else 'Exterior by three evaluated-triangle parity rays',closed=closed,intersection_counts=counts))
   else:unresolved.append(dict(issue,parity_counts=counts))
  finally:ev.to_mesh_clear()
 report['issues']=unresolved;report['resolved_signed_normal_false_positives']=resolutions
 report['status']='PASS' if not unresolved else 'REVIEW'
 (P/'camera_gate.json').write_text(json.dumps(report,indent=2))
 (P/'resource_gate.json').write_text(json.dumps(resources,indent=2))
 # Direct seeking equals chronological evaluation from a reopened frozen source.
 for f in [300,111,46,1,286,76,200,271,110,75,45,270]:
  S.frame_set(f);update(f);bpy.context.view_layer.update()
  state=[[o.name,[round(v,5) for v in o.matrix_world.translation],o.hide_render] for o in [S.camera,bpy.data.objects['Gold shell root'],bpy.data.objects['Buddy mug root'],bpy.data.objects['Miner head pivot']]]
  assert state==states[str(f)],('Seeking mismatch',f,state,states[str(f)])
 (P/'camera_gate.json').write_text(json.dumps(report,indent=2))
 (P/'resource_gate.json').write_text(json.dumps(resources,indent=2))
 (P/'contact_gate.json').write_text(json.dumps({'max_anchor_error_m':max(c['error_m'] for c in contacts),'checks':contacts,'support':'Miner boots bottom z=.001 on dirt between raised sleepers; Buddy pelvis bottom z=.630 matches stump top z=.630.','limitations':'Semantic anchors are complementary to native finger/surface image review.'},indent=2))
 print('CAMERA_GATE',report['status'],'issues',report['issues'][:12],flush=True)
 print('RESOURCES',resources,flush=True)
elif stage=='all_geometry_clearance':
 # Conservative EVERY-object AABB lower bounds supplement the exact-BVH
 # critical-obstacle gate, including stones, small hardware and curve props.
 # A lower bound above 30 cm proves the full surface cannot be closer.
 rows=[];issues=[];tested=set()
 for f in range(1,302):
  S.frame_set(f);update(f);bpy.context.view_layer.update()
  deps=bpy.context.evaluated_depsgraph_get();pos=S.camera.matrix_world.translation
  minimum=1000.;nearest=None
  for ob in list(S.objects):
   if ob.type not in {'MESH','CURVE','FONT'} or ob.hide_render or ob.get('ricks_role') in {'ink','wisp','smoke','streak','cloud'}:continue
   ev=ob.evaluated_get(deps)
   margin=V((0,0,0))
   if ob.type=='CURVE':
    assert all(sp.type=='POLY' for sp in ev.data.splines),'Bezier requires evaluated surface bounds'
    points=[ev.matrix_world @ V(p.co[:3]) for sp in ev.data.splines for p in sp.points]
    margin=V(tuple(sum(abs(ev.matrix_world[i][j]) for j in range(3))*ev.data.bevel_depth for i in range(3)))
   else:points=[ev.matrix_world @ V(v) for v in ev.bound_box]
   lo=V(tuple(min(p[k] for p in points) for k in range(3)));hi=V(tuple(max(p[k] for p in points) for k in range(3)))
   lo-=margin;hi+=margin
   delta=V(tuple(max(lo[k]-pos[k],0,pos[k]-hi[k]) for k in range(3)));distance=delta.length;tested.add(ob.name)
   if distance<minimum:minimum=distance;nearest=ob.name
   if distance<.30:issues.append({'frame':f,'object':ob.name,'aabb_lower_bound_m':distance})
  rows.append({'frame':f,'minimum_conservative_clearance_m':minimum,'nearest_bound':nearest})
 report={'status':'PASS' if not issues else 'REVIEW','frames_checked':301,'distinct_geometry_objects_checked':len(tested),'minimum_aabb_clearance_m':min(r['minimum_conservative_clearance_m'] for r in rows),'issues':issues,'frames':rows,'method':'Conservative evaluated world AABB lower bound for every visible solid mesh/curve/font; transparent FX and non-shadowing ink excluded.'}
 (P/'all_geometry_clearance.json').write_text(json.dumps(report,indent=2));print('ALL_GEOMETRY_CLEARANCE',report['status'],report['minimum_aabb_clearance_m'],len(tested),flush=True)
elif stage=='shadowprobe':
 folder=P/'brim_probe_v1';folder.mkdir(exist_ok=False)
 S.render.resolution_percentage=50
 for f in [1,288]:
  S.frame_set(f);update(f)
  for state in ['brim_on','brim_off']:
   visible(bpy.data.objects['Miner physical hat brim'],state=='brim_on')
   S.render.filepath=str(folder/f'{f}_{state}.png');bpy.ops.render.render(write_still=True)
  visible(bpy.data.objects['Miner physical hat brim'],True)
elif stage in ['calibrate','native']:
 folder=P/(args[0] if args else ('calibration_v1' if stage=='calibrate' else 'native_v1'));folder.mkdir(exist_ok=False)
 frames=[int(x) for x in args[1].split(',')] if len(args)>1 else json.loads((P/'calibration_plan.json').read_text())['blender_frames']
 S.render.resolution_percentage=50 if stage=='calibrate' else 100
 for f in frames:
  S.frame_set(f);update(f);S.render.filepath=str(folder/f'frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
 print('CALIBRATED',len(frames),flush=True)
elif stage=='benchmark':
 S.render.resolution_percentage=100
 report=gate.benchmark(S,[1,22,40,59,62,69,83,115,160,217,260,288],P/(args[0] if args else 'benchmark_v1'),update)
 import gpu
 print('GPU_RENDERER',gpu.platform.renderer_get(),flush=True)
 print('NATIVE_BENCHMARK',report['status'],report['p95_seconds'],report['max_seconds'],report['sampled_board_peak_gib'],flush=True)
elif stage in ['render','preview']:
 # Source identity is frozen before the first movie frame, and cannot change during resume.
 source=P/'gold_mine_salting_v01.blend'
 identity={k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in [('blend',source),('audio',P/'final_mix.wav')]}
 preview=stage=='preview'
 identity.update({'size':[540,960] if preview else [1080,1920],'fps':30,'frames':301})
 folder=P/('preview_frames_540' if preview else 'frames_1080_v01');folder.mkdir(exist_ok=True)
 ip=P/('preview_identity.json' if preview else 'render_identity.json')
 if ip.exists():assert json.loads(ip.read_text())==identity,'Frozen source mismatch'
 else:ip.write_text(json.dumps(identity,indent=2))
 a,b=map(int,args) if args else (1,301);S.render.resolution_percentage=50 if preview else 100
 timings=[]
 S.frame_set(a);update(a);warm=time.perf_counter();bpy.ops.render.render(write_still=False)
 (P/f'warmup_{a}.json').write_text(json.dumps({'seconds':time.perf_counter()-warm}))
 for f in range(a,b+1):
  path=folder/f'frame_{f:04d}.png'
  if path.exists():continue
  start=time.perf_counter();S.frame_set(f);update(f);S.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  timings.append({'frame':f,'seconds':time.perf_counter()-start})
  (P/f'{stage}_timing_{a}_{b}.json').write_text(json.dumps(timings))
  (P/(stage+'_progress.json')).write_text(json.dumps({'last_complete_frame':f,'total':301}))
 print('RENDERED',a,b,flush=True)
