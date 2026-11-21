"""CPU-only preview mux and additional unmodified-frame diagnostics."""
import subprocess,json,hashlib
from pathlib import Path
import numpy as np
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');VIDEO=OUT/'hair_sensor_v3_preview.mp4';QA=OUT/'qa_v3';QA.mkdir(exist_ok=True)
complete=json.loads((OUT/'v3_desk_render_complete.json').read_text())
source=OUT/'hair_sensor_v3_desk_fixed.blend'
assert complete['completed'] and complete['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest(), 'Final corrected ranges have not completed for this source'
frames=sorted((OUT/'v3_frames').glob('*.png'))
assert len(frames)==1413, f'Expected 1413 rendered frames, found {len(frames)}'
assert [int(p.stem) for p in frames]==list(range(1,1414)), 'Frame sequence has a gap'
subprocess.run(['ffmpeg','-y','-v','warning','-framerate','30','-start_number','1','-i',str(OUT/'v3_frames/%04d.png'),'-i',str(OUT/'audio_master.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-threads','4','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t','47.1','-movflags','+faststart',str(VIDEO)],check=True)
subprocess.run(['python',r'D:\remotionshorts\scripts\short_qa.py',str(VIDEO),str(QA),str(OUT/'shots_v3.json')],check=True)
md5=subprocess.run(['ffmpeg','-v','error','-i',str(VIDEO),'-map','0:v:0','-f','framemd5','-'],capture_output=True,text=True,check=True).stdout
(QA/'decoded_framemd5.txt').write_text(md5)
hashes=[line.split(',')[-1].strip() for line in md5.splitlines() if line and not line.startswith('#')]
duplicates=[i+1 for i in range(1,len(hashes)) if hashes[i]==hashes[i-1]]
stats=np.load(QA/'perframe.npz')
report={'scene_source':str(source),'source_sha256':complete['source_sha256'],'frames':len(hashes),'consecutive_exact_duplicate_frames':duplicates,'consecutive_exact_duplicate_percent':100*len(duplicates)/max(1,len(hashes)-1),'below_frozen_threshold_frames':int((stats['diff']<.02).sum()),'below_held_threshold_frames':int((stats['diff']<.3).sum()),'minimum_frame_difference':float(stats['diff'].min()),'mean_frame_difference':float(stats['diff'].mean()),'output_sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest()}
(QA/'duplicate_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
