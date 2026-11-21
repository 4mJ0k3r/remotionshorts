"""One GPU renderer, all full-resolution frames; resumable lossless output."""
import bpy,json,time,os,hashlib
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');FRAMES=OUT/'frames_1080_sky_v1';FRAMES.mkdir(exist_ok=True);table=json.loads((OUT/'shots.json').read_text());started=time.monotonic();rendered=0;times=[]
SAMPLES=32  # User-selected balanced1080p profile; retain completed48-sample frames.
source_hash=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();config=OUT/'master_render_config.json'
runtime={'source_sha256':source_hash,'source':bpy.data.filepath,'dimensions':[1080,1920],'fps':30,'frames':1875,'samples':SAMPLES,'engine':'BLENDER_EEVEE_NEXT','compositor':'GPU','raytracing':False,'motion_blur':.65,'frames_dir':str(FRAMES)}
previous=json.loads(config.read_text()) if config.exists() else None
if previous and previous['source_sha256']!=source_hash:raise RuntimeError('Existing frame sequence belongs to a different saved source; refusing mixed-version resume.')
resume=next((f for f in range(1,1876) if not (FRAMES/f'f{f:04}.png').is_file()),1876)
segments=previous.get('sampling_segments',[{'start_frame':1,'samples':previous['samples']}]) if previous else [{'start_frame':1,'samples':SAMPLES}]
if segments[-1]['samples']!=SAMPLES:segments.append({'start_frame':resume,'samples':SAMPLES})
runtime['sampling_segments']=segments;runtime['resume_frame']=resume
config.write_text(json.dumps(runtime,indent=2));stop=OUT/'logs/stop_preview.request'
if stop.exists():stop.unlink()
def progress(f,seconds,stage='rendering'):
 elapsed=time.monotonic()-started;remaining=1875-f;avg=sum(times[-60:])/max(1,len(times[-60:]));p={'stage':stage,'last_complete_frame':f,'total_frames':1875,'percent':round(f/1875*100,2),'current_frame_seconds':round(seconds,3),'recent_mean_seconds':round(avg,3),'elapsed_seconds_this_run':round(elapsed,1),'estimated_remaining_seconds':round(remaining*avg,1),'rendered_this_run':rendered,'samples':SAMPLES,'resume_frame':resume,'source_sha256':source_hash};tmp=OUT/'render_progress.tmp.json';tmp.write_text(json.dumps(p,indent=2));os.replace(tmp,OUT/'render_progress.json');print('MASTER_PROGRESS',json.dumps(p),flush=True)
for row in table['shots']:
 s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=10;s.eevee.taa_render_samples=SAMPLES
 if hasattr(s.render,'compositor_device'):s.render.compositor_device='GPU'
 old=next((n for n in s.node_tree.nodes if n.type=='R_LAYERS' and n.scene and n.scene.name=='AC_13'),None) if row['id']==14 else None
 for f in range(row['start_frame'],row['end_frame']+1):
  if stop.exists():progress(f-1,0,'stopped');raise SystemExit('Own project stop requested; complete frames preserved.')
  target=FRAMES/f'f{f:04}.png'
  if target.exists() and target.stat().st_size>10000:continue
  if old:old.mute=f>1183
  s.frame_set(f);tmp=FRAMES/f'f{f:04}.part.png';s.render.filepath=str(tmp);t=time.monotonic();bpy.ops.render.render(write_still=True,scene=s.name)
  if not tmp.exists():raise RuntimeError('Render produced no frame: '+str(f))
  os.replace(tmp,target);seconds=time.monotonic()-t;times.append(seconds);rendered+=1;progress(f,seconds)
progress(1875,0,'frames_complete')
