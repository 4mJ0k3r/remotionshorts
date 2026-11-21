"""Level narration while copying the approved picture stream unchanged."""
import json
import shutil
import subprocess
import sys
from timeline import OUT,ROOT

source=OUT/'audio_master_unleveled.wav'
if not source.exists():shutil.copy2(OUT/'audio_master.wav',source)
temp_audio=OUT/'audio_master_leveled.wav'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-af','loudnorm=I=-16:TP=-1.5:LRA=7',
                '-ar','48000','-ac','1','-t','54.50','-c:a','pcm_s16le',str(temp_audio)],check=True)
temp_audio.replace(OUT/'audio_master.wav')
destination=OUT/'commode_sniper_preview.mp4';temp_movie=OUT/'preview_audio_level.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(destination),'-i',str(OUT/'audio_master.wav'),
                '-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','192k','-t','54.50','-movflags','+faststart',str(temp_movie)],check=True)
temp_movie.replace(destination)
provenance=json.loads((OUT/'render_provenance.json').read_text());provenance['audio_normalization']='-16 LUFS target, -1.5 dBTP ceiling'
(OUT/'render_provenance.json').write_text(json.dumps(provenance,indent=2))
subprocess.run([sys.executable,str(ROOT/'scripts'/'short_qa.py'),str(destination),str(OUT/'qa_final'),str(OUT/'shots.json')],check=True)
