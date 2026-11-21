import json
import subprocess
import wave
from pathlib import Path
import numpy as np
from timeline import OUT, FRAMES

SOURCE = Path('C:/Users/lavis/Downloads/ElevenLabs_2026-11-14T13_58_38_Lavish_ivc_s30_sim75_v4.mp3')
OUT.mkdir(parents=True, exist_ok=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(SOURCE), '-t', '73.70',
                '-af', 'afade=t=out:st=73.67:d=0.03', '-ar', '48000', '-ac', '1',
                '-c:a', 'pcm_s16le', str(OUT/'audio_master.wav')], check=True)
with wave.open(str(OUT/'audio_master.wav')) as wav:
    samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(float)/32768
env = np.array([np.sqrt(np.mean(samples[i*1600:(i+1)*1600]**2)) for i in range(FRAMES)])
env = np.clip((env-.012)/max(.01, np.percentile(env, 85)-.012), 0, 1)
(OUT/'audio_envelope.json').write_text(json.dumps(np.round(env, 3).tolist()))
(OUT/'audio_source.json').write_text(json.dumps({'source':str(SOURCE),'trim_end':73.7,'frames':FRAMES,'fps':30},indent=2))
print('Audio ready: 73.70 seconds, 2211 frames')
