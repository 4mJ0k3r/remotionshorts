"""Extract a 30 Hz speech envelope and an acoustic mouth-width proxy."""
import array
import json
import math
import subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parents[2]/'renders'/'billionaire_handkerchief'
RATE=24000
STEP=RATE//30
raw=subprocess.run(['ffmpeg','-v','error','-i',str(OUT/'narration.mp3'),'-ac','1','-ar',str(RATE),'-f','s16le','-'],check=True,capture_output=True).stdout
samples=array.array('h',raw)
levels=[];rounding=[]
for start in range(0,len(samples),STEP):
    chunk=samples[start:start+STEP]
    rms=math.sqrt(sum(s*s for s in chunk)/len(chunk))/32768
    levels.append(max(0,min(1,(rms-.012)/.105)))
    # Lower spectral brightness generally suggests a more rounded vowel shape.
    # This drives width alongside the amplitude-driven aperture, not phoneme labels.
    bright=sum((a-b)**2 for a,b in zip(chunk,chunk[1:]))/max(1,sum(a*a for a in chunk))
    rounding.append(max(0,min(1,1.04-bright*3.5))*levels[-1])
envelope=[[round(max(level,levels[i-1]*.49 if i else 0),3),round(rounding[i],3)] for i,level in enumerate(levels)]
(OUT/'narration_envelope.json').write_text(json.dumps(envelope),encoding='utf-8')
