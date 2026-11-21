"""Mux the unchanged narration and audit the final V4 movie."""
import json,subprocess,hashlib
from pathlib import Path
import numpy as np
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');QA=OUT/'qa_v4';VIDEO=OUT/'hair_sensor_v4_master.mp4'
complete=json.loads((OUT/'v4_render_complete.json').read_text());source=OUT/'hair_sensor_v4_master.blend'
assert complete['completed'] and complete['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
frames=sorted((OUT/'v4_frames').glob('*.png'));assert [int(x.stem) for x in frames]==list(range(1,1414))
changed=set()
for row in json.loads((OUT/'shots_v4.json').read_text())['shots']:
    if row['shot'] in ('1A','1C','1D','3A','3B','4B','4C'):changed.update(range(row['start_frame'],row['end_frame']+1))
untouched=[f for f in range(1,1414) if f not in changed]
bad=[f for f in untouched if hashlib.sha256((OUT/'v3_frames'/f'{f:04d}.png').read_bytes()).digest()!=hashlib.sha256((OUT/'v4_frames'/f'{f:04d}.png').read_bytes()).digest()]
(QA/'unchanged_frames.json').write_text(json.dumps({'checked':len(untouched),'different':bad},indent=2));assert not bad,'An unaffected frame changed'
subprocess.run(['ffmpeg','-y','-v','warning','-framerate','30','-start_number','1','-i',str(OUT/'v4_frames/%04d.png'),'-i',str(OUT/'audio_master.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-threads','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t','47.1','-movflags','+faststart',str(VIDEO)],check=True)
subprocess.run(['python',r'D:\remotionshorts\scripts\short_qa.py',str(VIDEO),str(QA),str(OUT/'shots_v4.json')],check=True)
md5=subprocess.run(['ffmpeg','-v','error','-i',str(VIDEO),'-map','0:v:0','-f','framemd5','-'],capture_output=True,text=True,check=True).stdout;(QA/'decoded_framemd5.txt').write_text(md5)
hashes=[l.split(',')[-1].strip() for l in md5.splitlines() if l and not l.startswith('#')];duplicates=[i+1 for i in range(1,len(hashes)) if hashes[i]==hashes[i-1]];stats=np.load(QA/'perframe.npz')
report={'frames':len(hashes),'exact_duplicates':duplicates,'frozen_threshold_frames':int((stats['diff']<.02).sum()),'held_threshold_frames':int((stats['diff']<.3).sum()),'minimum_difference':float(stats['diff'].min()),'source_sha256':complete['source_sha256'],'video_sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest()}
(QA/'summary.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
