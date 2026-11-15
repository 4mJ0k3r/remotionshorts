"""Render and verify the alternate ending and its five-shot calibration strip."""
import json
import subprocess
import sys
from pathlib import Path

OUT=Path(__file__).resolve().parents[2]/'renders/washroom_experiment'
WORK=OUT/'alt_calibration'
STATUS=WORK/'progress.json'
RAW=OUT/'washroom_alt_raw.mp4'
FINAL=OUT/'washroom_alt_ending_540p.mp4'
FRAMES=[1160,1350,1460,1575,1675]
LABELS=['4A  Tremor','4B  Power awakening','4C  Sigma stare','4D  Power pose','4E  Teleport']
def movie_paths(full):
 if full:
  return OUT/'washroom_alt_raw_1080p.mp4',OUT/'washroom_alt_ending_1080p.mp4',WORK/'progress_1080p.json'
 return RAW,FINAL,STATUS
def queue(scene,movie=False,full=False):
 import bpy,traceback,time
 WORK.mkdir(exist_ok=True)
 raw,_,status=movie_paths(full)
 job={'state':'queued','frames':[],'frame':1061,'started':time.time()}
 def write():
  tmp=status.with_suffix('.tmp');tmp.write_text(json.dumps(job));tmp.replace(status)
 def track(s,*_):
  if s==scene and (s.frame_current%30==0 or s.frame_current==s.frame_end):
   job['frame']=s.frame_current;job['elapsed']=round(time.time()-job['started'],2)
   try:write()
   except PermissionError:pass
 def tick():
  try:
   window=bpy.context.window;previous=window.scene
   try:
    window.scene=scene
    if movie:
     r=scene.render;r.image_settings.file_format='FFMPEG';r.ffmpeg.format='MPEG4';r.ffmpeg.codec='H264'
     r.resolution_percentage=100 if full else 50
     r.ffmpeg.constant_rate_factor='HIGH';r.ffmpeg.audio_codec='NONE';r.filepath=str(raw)
     job['state']='rendering';write()
     bpy.app.handlers.render_post.append(track)
     bpy.ops.render.render(animation=True,scene=scene.name)
    else:
     i=len(job['frames'])
     if i<len(FRAMES):
      f=FRAMES[i];scene.frame_set(f);scene.render.image_settings.file_format='PNG'
      scene.render.filepath=str(WORK/f'{f}.png')
      bpy.ops.render.render(write_still=True,scene=scene.name)
      job['frames'].append(f);job['state']='rendering';write()
      return .12
   finally:
    window.scene=previous
   if movie and track in bpy.app.handlers.render_post:bpy.app.handlers.render_post.remove(track)
   job['state']='complete';write();return None
  except Exception:
   if track in bpy.app.handlers.render_post:bpy.app.handlers.render_post.remove(track)
   job['state']='failed';job['error']=traceback.format_exc();write();return None
 write();bpy.app.timers.register(tick,first_interval=.4)
def sheet():
 from PIL import Image,ImageDraw,ImageFont
 w,h,g=270,480,8
 image=Image.new('RGB',(5*w+6*g,h+44),'#131a2a');d=ImageDraw.Draw(image)
 font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',16)
 for i,(f,name) in enumerate(zip(FRAMES,LABELS)):
  x=g+i*(w+g);img=Image.open(WORK/f'{f}.png').convert('RGB')
  assert img.size==(540,960),img.size
  image.paste(img.resize((w,h),Image.Resampling.LANCZOS),(x,34))
  d.text((x,10),f'{name} · f{f}',font=font,fill='#f3f7ff')
 image.save(OUT/'sheet_alt_v1.jpg',quality=95)
def mux(full=False):
 from preview import probe
 source,final,_=movie_paths(full)
 if not source.exists():
  matches=[p for p in OUT.glob(f'{source.stem}*.mp4') if full or '_1080p' not in p.stem]
  if len(matches)!=1:raise RuntimeError(matches)
  matches[0].replace(source)
 video,=probe(source)
 width,height=(1080,1920) if full else (540,960)
 assert (video['width'],video['height'],int(video['nb_frames']),video['r_frame_rate'])==(width,height,675,'30/1'),video
 tmp=WORK/f'{final.stem}_staging.mp4'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-i',str(OUT/'alt_narration.wav'),
  '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-movflags','+faststart',str(tmp)],check=True)
 v,a=probe(tmp)
 assert int(v['nb_frames'])==675 and abs(float(v['duration'])-22.5)<.001 and abs(float(a['duration'])-22.5)<.03,(v,a)
 tmp.replace(final)
 print(final);print(json.dumps([v,a]))
if __name__=='__main__':
 if sys.argv[1]=='sheet':sheet()
 else:mux(full='--1080p' in sys.argv[1:])
