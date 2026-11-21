"""Live Blender calibration and recoverable EEVEE batch jobs."""
import bpy
import json
import time
import traceback
from pathlib import Path

BASE=Path('D:/remotionshorts')
OUT=BASE/'out/lifetime_fart'
PROJECT=BASE/'output/blender/lifetime_fart_full.blend'
FRAMES=[100,258,335,440,555,685,765,857,954,1030,1145,1252,1360,1504,1603,1660,1870,2040,2143,2245,2360,2455,2485,2620]
def save_state(path,job):
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(job));tmp.replace(path)
def calibration(scene,version):
 out=OUT/f'cal_v{version}';out.mkdir(exist_ok=True)
 status=out/'progress.json';job={'status':'queued','done':[],'total':len(FRAMES)}
 def tick():
  try:
   i=len(job['done'])
   if i==len(FRAMES):
    scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=24
    job['status']='complete';save_state(status,job);return None
   f=FRAMES[i];scene.frame_set(f)
   scene.render.resolution_percentage=34;scene.eevee.taa_render_samples=12
   scene.render.image_settings.file_format='PNG';scene.render.filepath=str(out/f'{f:04d}.png')
   bpy.ops.render.render(write_still=True,scene=scene.name)
   job['done'].append(f);job['status']='rendering';save_state(status,job);return .08
  except Exception:
   job['status']='failed';job['error']=traceback.format_exc();save_state(status,job);return None
 save_state(status,job);bpy.app.timers.register(tick,first_interval=.3)
def video(scene,preview=False):
 folder=OUT/('preview_v4_chunks' if preview else 'master_chunks');folder.mkdir(exist_ok=True)
 status=folder/'progress.json';step=2 if preview else 1
 job={'status':'queued','frame':0,'total':2715,'started':time.time(),'files':[],'part':0}
 def track(s,*_):
  if s==scene and (s.frame_current%30==1 or s.frame_current==s.frame_end):
   job['frame']=s.frame_current;job['seconds']=round(time.time()-job['started'],2)
   try:save_state(status,job)
   except PermissionError:pass
 def settings(a,b,name):
  scene.frame_start=a;scene.frame_end=b;scene.frame_step=step
  scene.render.fps=15 if preview else 30;scene.render.fps_base=1
  scene.render.resolution_percentage=25 if preview else 100
  scene.eevee.taa_render_samples=6 if preview else 24
  scene.render.image_settings.file_format='FFMPEG';scene.render.ffmpeg.format='MPEG4'
  scene.render.ffmpeg.codec='H264';scene.render.ffmpeg.constant_rate_factor='MEDIUM' if preview else 'HIGH'
  scene.render.ffmpeg.ffmpeg_preset='GOOD';scene.render.ffmpeg.audio_codec='NONE'
  scene.render.filepath=str(name)
 def tick():
  try:
   part=job['part'];a=1+part*300;b=min(a+299,2715)
   if a>2715:
    scene.frame_step=1;scene.frame_start=1;scene.frame_end=2715;scene.render.fps=30
    scene.render.resolution_percentage=100;scene.eevee.taa_render_samples=24;scene.frame_set(100)
    bpy.app.handlers.render_post.remove(track)
    job['status']='complete';save_state(status,job);return None
   name=folder/f'part_{part:02d}.mp4';settings(a,b,name)
   job['status']='rendering';save_state(status,job)
   bpy.ops.render.render(animation=True,scene=scene.name)
   files=list(folder.glob(f'part_{part:02d}*.mp4'))
   if len(files)!=1:raise RuntimeError(str(files))
   job['files'].append(str(files[0]));job['part']+=1;job['frame']=b;save_state(status,job);return .2
  except Exception:
   job['status']='failed';job['error']=traceback.format_exc();save_state(status,job)
   if track in bpy.app.handlers.render_post:bpy.app.handlers.render_post.remove(track)
   return None
 if not preview:
  settings(1,2715,OUT/'master_silent.mp4');scene.frame_set(100)
  bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT))
 bpy.app.handlers.render_post.append(track);save_state(status,job);bpy.app.timers.register(tick,first_interval=.6)

