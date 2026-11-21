"""Package only a complete validated native frame sequence; no subtitles."""
from pathlib import Path
import json,subprocess,hashlib,sys
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[3];P=R/'renders/project_paradox_india_ep03_5rs_blade/v01'
folder=P/'frames_1080';frames=[folder/f'frame_{f:04d}.png' for f in range(1,1402)]
for frame in frames:
 with Image.open(frame) as im:
  assert im.size==(1080,1920),(frame,im.size);im.verify()
gate=json.loads((P/'camera_contact_gate.json').read_text());assert gate['pass']
output=P/'Project_Paradox_India_EP03_5RsBladeLoophole_1080p.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-framerate','30','-start_number','1','-i',str(folder/'frame_%04d.png'),
 '-i',str(P/'final_mix.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18',
 '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-t','46.7','-movflags','+faststart',str(output)],check=True)
probe=json.loads(subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(output)],capture_output=True,text=True,check=True).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],int(v['nb_read_frames']))==(1080,1920,1401)
assert v['r_frame_rate']=='30/1' and abs(float(probe['format']['duration'])-46.7)<.04
subprocess.run(['ffmpeg','-v','error','-i',str(output),'-f','null','-'],check=True)
qa=P/'qa_final';res=subprocess.run([sys.executable,str(R/'scripts/short_qa.py'),str(output),str(qa),str(P/'shots.json'),'--strict'],capture_output=True,text=True)
(P/'qa_command.log').write_text(res.stdout+res.stderr,encoding='utf-8')
read=lambda path:np.asarray(Image.open(path),dtype=np.int16)
first,last=read(frames[0]),read(frames[-1]);loop={'mean_absolute_difference_8bit':float(np.abs(first-last).mean()),'max_difference_8bit':int(np.abs(first-last).max())}
timings=json.loads((P/'render_timings.json').read_text());seconds=np.array([row['seconds'] for row in timings])
memory=json.loads((P/'board_vram_render.json').read_text())
report={'movie':str(output),'frames':1401,'resolution':[1080,1920],'fps':30,'seconds':46.7,'decode_pass':True,
 'loop':loop,'timing_p95_seconds':float(np.percentile(seconds,95)),'timing_max_seconds':float(max(seconds)),
 'board_vram':memory,'strict_qa_exit':res.returncode,'source_sha256':hashlib.sha256((P/'project_paradox_ep03_v01.blend').read_bytes()).hexdigest()}
(P/'delivery_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
