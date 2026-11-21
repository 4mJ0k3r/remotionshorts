"""Validate exact native frame sequence, package narration, and run shared strict QA."""
from pathlib import Path
import json,subprocess,sys,hashlib
from PIL import Image
import numpy as np
from scipy.signal import correlate,correlation_lags
R=Path(__file__).resolve().parents[3];P=R/'renders/gold_mine_salting_v4'
identity=json.loads((P/'render_identity.json').read_text())
for k,p in [('blend',P/'gold_mine_salting_v4.blend'),('audio',P/'final_mix.wav')]:assert hashlib.sha256(p.read_bytes()).hexdigest()==identity[k]
for i in range(1,301):
 with Image.open(P/'frames_1080_v4'/f'frame_{i:04d}.png') as im:
  assert im.size==(1080,1920),(i,im.size)
  im.verify()
movie=P/'gold_mine_salting_v4_1080x1920.mp4'
if movie.exists():raise FileExistsError('Preserve the earlier delivered encoding')
subprocess.run(['ffmpeg','-v','warning','-framerate','30','-i',str(P/'frames_1080_v4/frame_%04d.png'),'-i',str(P/'final_mix.wav'),'-map','0:v:0','-map','1:a:0','-frames:v','300','-t',str(300/30),'-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','192k','-movflags','+faststart',str(movie)],check=True)
probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)],capture_output=True,text=True,check=True).stdout)
v=next(x for x in probe['streams'] if x['codec_type']=='video')
assert (v['width'],v['height'],v['nb_frames'],v['r_frame_rate'])==(1080,1920,'300','30/1')
subprocess.run(['ffmpeg','-v','error','-i',str(movie),'-f','null','-'],check=True)
def audio(path):
 raw=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout
 return np.frombuffer(raw,np.float32).astype(np.float64)
a=audio(movie);b=audio(P/'narration_preserved.wav');n=min(len(a),len(b));a=a[:n];b=b[:n]
cc=correlate(a,b,method='fft');lags=correlation_lags(len(a),len(b));mask=np.abs(lags)<=800
lag=int(lags[mask][np.argmax(cc[mask])]);assert abs(lag)<=16,('Narration timing offset >1ms',lag)
match=float(np.corrcoef(a,b)[0,1])
res={'specs':v,'duration_seconds':float(probe['format']['duration']),'decode':'PASS','contiguous_native_frames':300,'narration_lag_samples_at_16khz':lag,'narration_lag_ms':lag/16,'delivered_narration_correlation_with_preserved_recording':match,'movie_sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'source_identity':identity,'subtitles':False}
(P/'delivery_validation.json').write_text(json.dumps(res,indent=2))
qa=subprocess.run([sys.executable,str(R/'scripts/short_qa.py'),str(movie),str(P/'qa_final'),str(P/'shots.json'),'--strict'],capture_output=True,text=True)
(P/'qa_command.log').write_text(qa.stdout+'\n'+qa.stderr)
print(json.dumps(res,indent=2));print('STRICT_QA_EXIT',qa.returncode)
if qa.returncode:raise SystemExit(qa.returncode)
