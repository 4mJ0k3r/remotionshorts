"""Package the authorized first ten seconds only. Full master stays unrendered."""
from pathlib import Path
import subprocess,json,sys,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[3];P=R/'renders/project_paradox_india_ep03_5rs_blade/v01'
frames=P/'preview_540p_first10_frames';output=P/'Project_Paradox_EP03_first10s_540p.mp4'
for i in range(1,301):
 with Image.open(frames/f'frame_{i:04d}.png') as image:
  assert image.size==(540,960);image.verify()
subprocess.run(['ffmpeg','-y','-v','error','-framerate','30','-start_number','1','-i',str(frames/'frame_%04d.png'),
 '-i',str(P/'final_mix.wav'),'-map','0:v:0','-map','1:a:0','-t','10','-frames:v','300',
 '-vf','scale=in_range=pc:out_range=tv:out_color_matrix=bt709','-c:v','libx264','-crf','18','-preset','medium',
 '-pix_fmt','yuv420p','-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
 '-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(output)],check=True)
probe=json.loads(subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(output)],capture_output=True,text=True,check=True).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],int(v['nb_read_frames']),v['r_frame_rate'])==(540,960,300,'30/1')
assert abs(float(probe['format']['duration'])-10)<.034
subprocess.run(['ffmpeg','-v','error','-i',str(output),'-f','null','-'],check=True)
meta=json.loads((P/'shots.json').read_text());meta['shots']=[dict(s,b=min(s['b'],300)) for s in meta['shots'] if s['a']<300]
for key in ['cuts','continuous_junctions','calibration_frames']:meta[key]=[f for f in meta.get(key,[]) if f<300]
meta['action_ranges']=[[x,min(y,300)] for x,y in meta.get('action_ranges',[]) if x<300]
meta['closeups']=[]
for key in ['transitions','xfade','planned']:meta[key]=[[x,min(y,299)] for x,y in meta.get(key,[]) if x<300]
(P/'preview_shots.json').write_text(json.dumps(meta,indent=2))
qa=subprocess.run([sys.executable,str(R/'scripts/short_qa.py'),str(output),str(P/'qa_preview'),str(P/'preview_shots.json')],capture_output=True,text=True,check=True)
(P/'preview_qa_command.log').write_text(qa.stdout+qa.stderr,encoding='utf-8')
decoded=subprocess.run(['ffmpeg','-v','error','-i',str(output),'-vn','-ac','1','-ar','48000','-f','f32le','-'],capture_output=True,check=True).stdout
reference=subprocess.run(['ffmpeg','-v','error','-i',str(P/'final_mix.wav'),'-t','10','-ac','1','-ar','48000','-f','f32le','-'],capture_output=True,check=True).stdout
x=np.frombuffer(decoded,np.float32);y=np.frombuffer(reference,np.float32);n=min(len(x),len(y));correlation=float(np.corrcoef(x[:n],y[:n])[0,1])
report={'movie':str(output),'seconds':float(probe['format']['duration']),'resolution':[540,960],'fps':30,'frames':300,
 'video_codec':v['codec_name'],'audio_codec':a['codec_name'],'decode_pass':True,'audio_sample_correlation_to_exact_mix_prefix':correlation,
 'subtitles':False,'full_1080_render_started':False,'source_sha256':hashlib.sha256((P/'project_paradox_ep03_v01.blend').read_bytes()).hexdigest(),
 'qa_report':str(P/'qa_preview/report.json')}
(P/'preview_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print(qa.stdout)
