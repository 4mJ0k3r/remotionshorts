"""Original-speed narration, no overlays, V2 frame verification and technical QA."""
from pathlib import Path
import subprocess,sys,json
ROOT=Path(r'D:\remotionshorts');OUT=ROOT/'renders/bamboo_ambush';frames=OUT/'frames_v2_360';video=OUT/'bamboo_ambush_v2_360p.mp4'
missing=[f for f in range(1,936) if not (frames/f'{f:04d}.png').is_file()]
if missing:raise RuntimeError('V2 frames missing: '+str(missing[:8]))
subprocess.run(['ffmpeg','-y','-v','warning','-framerate','30','-start_number','1','-i',str(frames/'%04d.png'),'-i',str(OUT/'audio_master.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-frames:v','935','-t','31.166667','-movflags','+faststart',str(video)],check=True)
subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(video),str(OUT/'qa_v2'),str(OUT/'shots.json')],check=True)
p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));v=next(x for x in p['streams'] if x['codec_type']=='video');assert (v['width'],v['height'],int(v['nb_frames']),v['r_frame_rate'])==(360,640,935,'30/1');assert abs(float(p['format']['duration'])-935/30)<.05;(OUT/'qa_v2/probe.json').write_text(json.dumps(p,indent=2));print('V2 MUX AND TECHNICAL QA COMPLETE',video,flush=True)
