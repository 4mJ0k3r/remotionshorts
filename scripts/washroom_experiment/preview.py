"""Queue and assemble the approved 540 × 960 preview."""
from pathlib import Path
import json
import subprocess
import sys
OUT=Path(__file__).resolve().parents[2]/'renders/washroom_experiment'
WORK=OUT/'director_preview_chunks'
PROGRESS=WORK/'progress.json'
FINAL=OUT/'washroom_experiment_preview_v2_540p.mp4'
def queue(scene,replacement=None,master=False):
 import bpy,time,traceback
 work,progress,_=output_paths(master)
 work.mkdir(exist_ok=True)
 if replacement is None:
  job={'state':'queued','frame':0,'part':0,'files':[],'started':time.time()}
 else:
  job=json.loads(progress.read_text())
  if job['state']!='complete':raise RuntimeError('Complete the preview before replacing a chunk')
  job.update(state='queued',part=replacement,started=time.time())
 def write():
  path=progress.with_suffix('.tmp');path.write_text(json.dumps(job));path.replace(progress)
 def track(s,*_):
  if s==scene and (s.frame_current%30==0 or s.frame_current==s.frame_end):
   job['frame']=s.frame_current;job['elapsed']=round(time.time()-job['started'],2)
   try:write()
   except PermissionError:pass
 def tick():
  try:
   i=job['part'];a=1+i*300;b=min(1404,a+299)
   if a>1404:
    bpy.app.handlers.render_post.remove(track)
    scene.frame_start=1;scene.frame_end=1404;scene.render.resolution_percentage=100;scene.frame_set(100)
    job['state']='complete';write();return None
   stem=f'preview_{i:02d}' if replacement is None else f'revised_{i:02d}'
   path=work/f'{stem}.mp4'
   scene.frame_start=a;scene.frame_end=b;scene.render.resolution_percentage=100 if master else 50;scene.render.fps=30
   scene.eevee.taa_render_samples=16
   scene.render.image_settings.file_format='FFMPEG'
   scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264'
   scene.render.ffmpeg.constant_rate_factor='HIGH' if master else 'MEDIUM';scene.render.ffmpeg.audio_codec='NONE'
   scene.render.filepath=str(path)
   job['state']='rendering';write()
   window=bpy.context.window;previous=window.scene
   try:
    window.scene=scene
    bpy.ops.render.render(animation=True,scene=scene.name)
   finally:window.scene=previous
   files=list(work.glob(f'{stem}*.mp4'))
   if len(files)!=1:raise RuntimeError(f'Expected one chunk, found {files}')
   if replacement is not None:
    job['files'][i]=str(files[0])
    job['part']=5
   else:
    job['files'].append(str(files[0]));job['part']+=1
   write()
   return .12
  except Exception:
   if track in bpy.app.handlers.render_post:bpy.app.handlers.render_post.remove(track)
   job['state']='failed';job['error']=traceback.format_exc();write();return None
 bpy.app.handlers.render_post.append(track);write();bpy.app.timers.register(tick,first_interval=.45)
def probe(path):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height,r_frame_rate,nb_frames,duration','-of','json',str(path)]))['streams']
def output_paths(master):
 if master:
  work=OUT/'master_1080p_chunks'
  return work,work/'progress.json',OUT/'washroom_experiment_1080p.mp4'
 return WORK,PROGRESS,FINAL
def assemble(master=False):
 work,progress,final=output_paths(master)
 job=json.loads(progress.read_text())
 if job['state']!='complete':raise RuntimeError(job)
 files=[Path(f) for f in job['files']]
 if sum(int(probe(p)[0]['nb_frames']) for p in files)!=1404:raise ValueError('Preview chunks must contain exactly 1404 frames')
 manifest=work/'concat.txt';manifest.write_text(''.join(f"file '{p.as_posix()}'\n" for p in files))
 tmp=work/'mux_staging.mp4'
 subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(manifest),'-i',str(OUT/'narration.wav'),
                 '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(tmp)],check=True)
 v,a=probe(tmp)
 width,height=(1080,1920) if master else (540,960)
 assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(width,height,'30/1',1404),v
 assert abs(float(v['duration'])-46.8)<.001 and abs(float(a['duration'])-46.8)<.030,(v,a)
 tmp.replace(final)
 print(final)
 print(json.dumps([v,a]))
if __name__=='__main__':assemble(master='--master' in sys.argv[1:])
