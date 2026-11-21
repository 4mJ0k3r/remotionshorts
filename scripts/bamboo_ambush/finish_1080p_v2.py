"""Mux full-HD V2 with preserved narration and run all-frame technical QA."""
from pathlib import Path
import subprocess,sys,json
ROOT=Path(r'D:\remotionshorts');OUT=ROOT/'renders/bamboo_ambush';frames=OUT/'frames_v2_1080';video=OUT/'bamboo_ambush_v2_1080p.mp4';qa=OUT/'qa_v2_1080';qa.mkdir(exist_ok=True)
missing=[f for f in range(1,936) if not (frames/f'{f:04d}.png').is_file()]
if missing:raise RuntimeError('Full-HD frames missing: '+str(missing[:8]))
print('Encoding1080p with original Hindi master audio.',flush=True)
with (OUT/'logs/encode_v2_1080.log').open('w') as log:subprocess.run(['ffmpeg','-y','-v','warning','-framerate','30','-start_number','1','-i',str(frames/'%04d.png'),'-i',str(OUT/'audio_master.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-frames:v','935','-t','31.166667','-movflags','+faststart',str(video)],stdout=log,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(video),str(qa),str(OUT/'shots.json')],check=True)
p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));v=next(x for x in p['streams'] if x['codec_type']=='video');assert (v['width'],v['height'],int(v['nb_frames']),v['r_frame_rate'])==(1080,1920,935,'30/1');assert abs(float(p['format']['duration'])-935/30)<.05;assert any(x['codec_type']=='audio' for x in p['streams']);(qa/'probe.json').write_text(json.dumps(p,indent=2));progress=json.loads((OUT/'v2_1080_progress.json').read_text());progress.update(stage='encoded_needs_visual_review',output=str(video));(OUT/'v2_1080_progress.json').write_text(json.dumps(progress,indent=2));print('V2 FULL-HD MUX AND TECHNICAL QA COMPLETE',video,flush=True)
