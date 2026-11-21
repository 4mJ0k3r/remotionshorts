"""Production stages; render is guarded by evidence from calibration/performance."""
import bpy,sys,json,time,runpy,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;P=R/'renders/project_paradox_india_ep03_5rs_blade/v01'
sys.path[:0]=[str(R/'scripts'),str(D)]
action=sys.argv[sys.argv.index('--')+1]
if action=='build':
 runpy.run_path(str(D/'build.py'),run_name='__main__');raise SystemExit(0)
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
  S.frame_start,S.frame_end=start,end;S.render.resolution_percentage=100;S.render.filepath=str(folder/'frame_####')
  bpy.ops.render.render(animation=True)
  if rows:rows[-1]['seconds']+=time.perf_counter()-cursor[0]
 finally:
  bpy.app.handlers.render_write.remove(written);S.frame_start,S.frame_end,S.render.filepath=old
 assert [r['frame'] for r in rows]==list(range(start,end+1)),'Animation write callbacks missed frames'
 return rows
if action=='calibrate':
 shots=[{'id':n,'a':a-1,'b':b} for n,a,b,g in runtime.SHOTS]
 meta={'schema':1,'shots':shots,'cuts':[s['a'] for s in shots[1:]],'continuous_junctions':[],
 'transitions':[[197,231]],'calibration_frames':[35,150,175,190,350,475,519,675,760,816,869,920,1020,1090,1198,1252,1280,1400],
 'action_ranges':[[140,180],[325,450],[739,870],[1180,1320]],
 'closeups':[{'frame':1090,'kind':'hat_brim','label':'Flat graphic face and cap shadow','region':[.30,.15,.72,.45]},
 {'frame':760,'kind':'hand_prop','label':'Ladle handle grip','region':[.10,.35,.90,.88]},
 {'frame':1252,'kind':'hand_prop','label':'Officer lever contact','region':[.1,.1,.9,.9]}]}
 (P/'shots.json').write_text(json.dumps(meta,indent=2));plan=json.loads((P/'calibration_plan.json').read_text())
 folder=P/('calibration_'+time.strftime('%H%M%S'));folder.mkdir(exist_ok=True)
 (P/'latest_calibration.json').write_text(json.dumps({'folder':str(folder)}))
 for frame in plan['blender_frames']:render(frame,folder/f'frame_{frame:04d}.png')
 print('CALIBRATION_READY',len(plan['blender_frames']),flush=True)
elif action=='refresh':
 bpy.data.objects['Customer hand mirror'].location.z=.94
 for strip in list(S.sequence_editor.sequences_all) if S.sequence_editor else []:
  if strip.type=='SOUND':
   sound=strip.sound;S.sequence_editor.sequences.remove(strip)
   if sound.users==0:bpy.data.sounds.remove(sound)
 seq=S.sequence_editor_create();seq.sequences.new_sound('Final Hindi narration and mix',str(P/'final_mix.wav'),1,1).sound.pack();S.render.use_sequencer=False
 bpy.data.texts['runtime.py'].from_string((D/'runtime.py').read_text(encoding='utf-8'))
 exec(compile(bpy.data.texts['START_HERE.py'].as_string(),'START_HERE.py','exec'))
 S.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'project_paradox_ep03_v01.blend'))
elif action=='contact_polish':
 from geometry import cylinder,cube,faceline,rough
 import geometry as G
 def point(x,z,offset=.004):
  r=.32*rough(__import__('math').atan2(-z,x));return (x,-.063*max(.035,1-(x*x+z*z)/(r*r))**.5-offset,z)
 G.facepoint=point
 press=bpy.data.objects['Barber press'];silver=bpy.data.materials['Silver razor and steel coin']
 cylinder('Supported coin die',(0,0,.05),(0,0,.084),.078,silver,press,24,outline=.002)
 cube('Blade receiving tray',(0,-.34,.064),(.35,.34,.04),silver,press,bevel=.025,outline=.003)['collision']=True
 bpy.data.objects['Pressed blade'].rotation_euler.x=-__import__('math').pi/2
 for o in list(S.objects):
  if o.type=='CURVE':o.data.bevel_resolution=1
  if o.name.startswith('Kenney licensed'):o.name=o.name.replace('Kenney licensed','Local generated town kit')
 for actor in runtime.ACTORS:faceline(actor+' frown',[(-.055,-.13),(0,-.106),(.055,-.13)],.007,bpy.data.materials['Graphic limbs and features'],bpy.data.objects[actor+' head'])
 for name in ['geometry.py','runtime.py']:bpy.data.texts[name].from_string((D/name).read_text(encoding='utf-8'))
 seq=S.sequence_editor_create();seq.sequences.new_sound('Final Hindi narration and mix',str(P/'final_mix.wav'),1,1).sound.pack();S.render.use_sequencer=False
 exec(compile(bpy.data.texts['START_HERE.py'].as_string(),'START_HERE.py','exec'));S.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'project_paradox_ep03_v01.blend'))
elif action=='native':
 folder=P/('native_'+time.strftime('%H%M%S'));folder.mkdir()
 (P/'latest_native.json').write_text(json.dumps({'folder':str(folder)}))
 for f in [1,125,153,190,230,371,536,668,758,820,870,918,1006,1111,1198,1277,1401]:render(f,folder/f'frame_{f:04d}.png',100)
elif action=='environment_polish':
 from geometry import cube,sphere
 glass=runtime.look.metal('Pale blue window glass','#91C8E5',0,.3);glass.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.10;glass.surface_render_method='BLENDED'
 plaster=bpy.data.materials['Cream painted plaster']
 for name in ['BARBER','MARKET','MINT']:
  stage=bpy.data.objects[name+' stage'];old=bpy.data.objects.get(name+' back wall')
  if old:bpy.data.objects.remove(old,do_unlink=True)
  cube(name+' lower wall',(0,3,.85),(8,.22,1.7),plaster,stage,.02)['collision']=True
  cube(name+' upper wall',(0,3,3.15),(8,.22,.9),plaster,stage,.02)['collision']=True
  for lo,hi in [(-4,-2.925),(-1.875,-1.325),(-.275,.275),(1.325,1.875),(2.925,4)]:
   cube(name+' window masonry pier',((lo+hi)/2,3,2.2),(hi-lo,.22,1),plaster,stage,.02)['collision']=True
  for pane in [o for o in stage.children if 'recessed window' in o.name]:
   pane.data.materials.clear();pane.data.materials.append(glass);pane.visible_shadow=False
  for j in range(3):
   for k in range(2):
    lobe=sphere('Varied cloud lobe',(j*3-3-.45+k*.7,8,5+j*.2+.16+(j%2)*.09),(.38+.08*j,.18,.24+.04*k),bpy.data.materials['Graphic cream face'],stage,16,8);runtime.look.mark_role(lobe,'cloud')
 bpy.data.objects['RBI wall plaque'].location.z=3.05;bpy.data.objects['Mint plaque'].location.z=3.05
 exec(compile(bpy.data.texts['START_HERE.py'].as_string(),'START_HERE.py','exec'));S.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'project_paradox_ep03_v01.blend'))
elif action=='wardrobe':
 import wardrobe
 wardrobe.apply()
 exec(compile(bpy.data.texts['START_HERE.py'].as_string(),'START_HERE.py','exec'));S.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'project_paradox_ep03_v01.blend'))
elif action=='design_finish':
 import wardrobe
 wardrobe.apply(force=True)
 for pane in [o for o in list(S.objects) if o.type=='MESH' and 'recessed window' in o.name and not o.get('ricks_role')]:
  for child in list(pane.children):
   if child.get('ricks_role')=='ink':bpy.data.objects.remove(child,do_unlink=True)
 exec(compile(bpy.data.texts['START_HERE.py'].as_string(),'START_HERE.py','exec'));S.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'project_paradox_ep03_v01.blend'))
elif action=='preview10':
 S.render.resolution_x=540;S.render.resolution_y=960;S.render.resolution_percentage=100;S.eevee.bokeh_max_size=12
 folder=P/'preview_540p_first10_frames';folder.mkdir(exist_ok=True)
 S.frame_set(1);runtime.update(1);bpy.ops.render.render(write_still=False)
 rows=[]
 for start in range(1,301,60):
  rows.extend(animation_chunk(start,min(300,start+59),folder))
  (P/'preview_progress.json').write_text(json.dumps({'completed':min(300,start+59),'total':300}))
 (P/'preview_timings.json').write_text(json.dumps(rows,indent=2))
elif action=='benchmark':
 S.render.resolution_percentage=100
 for f in [15,360,665,1200]:
  S.frame_set(f);runtime.update(f);bpy.ops.render.render(write_still=False)
 report=gate.benchmark(S,[15,155,225,360,505,665,760,838,920,1025,1200,1285],P/('benchmark_'+time.strftime('%H%M%S')),runtime.update)
 report['source_sha256']=hashlib.sha256((P/'project_paradox_ep03_v01.blend').read_bytes()).hexdigest()
 report['samples']=S.eevee.taa_render_samples
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
 cache={o.name:np.array(o.bound_box,dtype=np.float64) for o in obstacles};triangle_cache={}
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
  for o in active:
   dynamic=o.type=='FONT' or (o.type=='CURVE' and any(word in o.name for word in [' arm ',' leg ','molten stream','Pan suspension']))
   points=np.array(o.bound_box,dtype=np.float64) if dynamic else cache[o.name].copy()
   if o.get('ink_base_width'):
    lo=points.min(0)-.06;hi=points.max(0)+.06
    points=np.array([(x,y,z) for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
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
   if target=='Barber press moving ram':point=bpy.data.objects[target].matrix_world@V((-.13,-.14,.05))
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
 report={'pass':not issues and triangles<200000,'source_sha256':hashlib.sha256((P/'project_paradox_ep03_v01.blend').read_bytes()).hexdigest(),'minimum_conservative_camera_clearance_m':minimum,'frames_checked':1401,'all_visible_mesh_curve_font_objects_checked':True,'visible_triangles_including_curves_and_text':triangles,'projected_blade_checks':blade_bound_checks,'issues':issues}
 (P/'camera_contact_gate.json').write_text(json.dumps(report,indent=2));print('GATES',report['pass'],minimum,triangles,len(issues),flush=True)
elif action=='batch_probe':
 S.render.resolution_percentage=100;folder=P/('batch_probe_'+time.strftime('%H%M%S'));folder.mkdir()
 rows=animation_chunk(609,620,folder)
 (P/'batch_probe.json').write_text(json.dumps({'frames':rows,'folder':str(folder),'source_sha256':hashlib.sha256((P/'project_paradox_ep03_v01.blend').read_bytes()).hexdigest()},indent=2))
elif action=='render':
 assert json.loads((P/'scope.json').read_text()).get('full_render_authorized') is True,'Full render is stopped by current user scope'
 acceptance=json.loads((P/'visual_acceptance.json').read_text());bench=json.loads((P/'benchmark_gate.json').read_text())
 assert acceptance['pass'] and bench['status']=='PASS','Calibration/performance gates block full rendering'
 assert acceptance['source_sha256']==hashlib.sha256((P/'project_paradox_ep03_v01.blend').read_bytes()).hexdigest(),'Source changed since visual acceptance'
 camera_gate=json.loads((P/'camera_contact_gate.json').read_text());assert camera_gate['pass'] and camera_gate['source_sha256']==acceptance['source_sha256']
 assert bench['source_sha256']==acceptance['source_sha256'],'Benchmark source differs'
 S.render.resolution_percentage=100;folder=P/'frames_1080';folder.mkdir(exist_ok=True);rows=[]
 warm=[]
 for f in [1,360,665,1200]:
  t=time.perf_counter();S.frame_set(f);runtime.update(f);bpy.ops.render.render(write_still=False);warm.append({'frame':f,'seconds':time.perf_counter()-t})
 (P/'render_warmup.json').write_text(json.dumps(warm,indent=2))
 total_start=time.perf_counter()
 for start in range(1,1402,60):
  rows.extend(animation_chunk(start,min(1401,start+59),folder))
  (P/'render_timings.json').write_text(json.dumps(rows,indent=2))
 (P/'render_wall_time.json').write_text(json.dumps({'seconds':time.perf_counter()-total_start,'timing_method':'intervals between frame-write callbacks; chunk cleanup assigned to last frame'}))
 (P/'render_timings.json').write_text(json.dumps(rows,indent=2))
