"""CPU-only timing evidence; never competes for CUDA memory."""
import json,subprocess,numpy as np
from pathlib import Path
from faster_whisper import WhisperModel
OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
model=WhisperModel('small',device='cpu',compute_type='int8',cpu_threads=6)
raw=subprocess.run(['ffmpeg','-v','error','-i',str(OUT/'audio_master.wav'),'-f','f32le','-ar','16000','-ac','1','-'],capture_output=True,check=True).stdout
segments,info=model.transcribe(np.frombuffer(raw,dtype=np.float32),language='hi',word_timestamps=True)
rows=[]
for s in segments:
    row={'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'word':w.word} for w in s.words or []]}
    rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
(OUT/'transcript.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
