"""CPU-only narration analysis; outputs stay inside this project."""
import json, math, subprocess
from pathlib import Path
import av
import numpy as np
from faster_whisper import WhisperModel

OUT = Path(r'D:\remotionshorts\renders\hair_sensor')
SOURCE = Path(r'C:\Users\lavis\Downloads\ElevenLabs_2026-11-12T13_25_32_Viraj - Rich, Confident and Expressive_pvc_s30_sim75_v4.mp3')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(SOURCE), '-ar', '48000', '-ac', '1', str(OUT/'audio_master.wav')], check=True)
c = av.open(str(OUT/'audio_master.wav'))
samples = np.concatenate([f.to_ndarray().reshape(-1) for f in c.decode(audio=0)]).astype(float)/32768
duration = len(samples)/48000
env = [float(np.sqrt(np.mean(samples[i:i+1600]**2))) for i in range(0,len(samples),1600)]
(OUT/'audio_analysis.json').write_text(json.dumps({'source':str(SOURCE),'duration':duration,'fps':30,'frame_count':math.ceil(duration*30),'rms':env},indent=2))
print('Audio duration:', duration, 'frames:', math.ceil(duration*30), flush=True)
model = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=4, local_files_only=True)
segments, info = model.transcribe(samples[::3].astype(np.float32), language='hi', word_timestamps=True, beam_size=5, vad_filter=True)
data=[]
for s in segments:
    row={'start':s.start,'end':s.end,'text':s.text,'words':[{'start':w.start,'end':w.end,'text':w.word,'probability':w.probability} for w in s.words]}
    data.append(row)
    print(json.dumps(row,ensure_ascii=True),flush=True)
(OUT/'transcript.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
