from pathlib import Path
import json, subprocess
import numpy as np
from faster_whisper import WhisperModel
root = Path(__file__).resolve().parents[2]
out = root/'renders/gta6_13yr_wait_papa_chappal_v1'
audio = Path(r'C:\Users\lavis\Downloads\gta6-viraj-v4.mp3')
raw = subprocess.run(['ffmpeg','-v','error','-i',str(audio),'-ar','16000','-ac','1','-f','f32le','-'],capture_output=True,check=True).stdout
signal = np.frombuffer(raw,np.float32)
model = WhisperModel('medium',device='cpu',compute_type='int8',cpu_threads=6,local_files_only=True)
segments,_ = model.transcribe(signal,language='hi',word_timestamps=True)
rows=[]
for seg in segments:
    row={'start':seg.start,'end':seg.end,'text':seg.text,'words':[dict(start=w.start,end=w.end,text=w.word) for w in seg.words]}
    rows.append(row)
    print(seg.start, seg.end, seg.text,flush=True)
(out/'alignment.json').write_text(json.dumps({'seconds':len(signal)/16000,'segments':rows},indent=2,ensure_ascii=False),encoding='utf-8')
