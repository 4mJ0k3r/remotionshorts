"""Sample-contiguous narration slices and one scored master audio bed."""
import json
from pathlib import Path
import subprocess
import wave

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"renders/padoda_billionaire"
SOURCE=next((Path.home()/"Downloads").glob("ElevenLabs_2026-11-19T12_48_43*.mp3"))
RATE=44100
FPS=30
BOUNDS=(0,261,543,846,1230,1849)
raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(SOURCE),"-ac","1","-ar",str(RATE),"-f","s16le","-"])
original=np.frombuffer(raw,"<i2")
sample_frame=RATE//FPS
count=BOUNDS[-1]*sample_frame
voice=np.zeros(count)
voice[:len(original)]=original/32768
fx=np.zeros(count)
rng=np.random.default_rng(822)

def wav(path,values):
    pcm=np.clip(np.round(values*32768),-32768,32767).astype("<i2")
    with wave.open(str(path),"wb") as file:
        file.setparams((1,2,RATE,0,"NONE","not compressed"))
        file.writeframes(pcm.tobytes())

def read(path):
    with wave.open(str(path),"rb") as file:
        return np.frombuffer(file.readframes(file.getnframes()),"<i2").astype(float)/32768

def sine(t,hz):
    return np.sin(2*np.pi*hz*t)

def effect(at,duration,amp,kind):
    sample=round(at*RATE)
    n=min(round(duration*RATE),count-sample)
    t=np.arange(n)/RATE
    edge=np.minimum(1,t/.009)*np.minimum(1,(duration-t)/.052)
    noise=rng.normal(size=n)
    if kind=="bell":
        signal=np.exp(-4*t)*(sine(t,1024)+.34*sine(t,1612)+.19*sine(t,2056))
    elif kind=="metal":
        signal=np.exp(-15*t)*(.3*noise+sine(t,171+50*t)+.4*sine(t,873))
    elif kind=="spark":
        signal=np.exp(-7*t)*(.31*noise+sine(t,540+180*sine(t,13))*.66)
    elif kind=="power":
        signal=.66*sine(t,60+13*t)+.26*sine(t,175+34*t)+.17*sine(t,330+18*t)
    elif kind=="whoosh":
        signal=.40*noise+.69*sine(t,156-56*t)
    else:
        signal=np.exp(-22*t)*(.46*noise+.71*sine(t,128))
    fx[sample:sample+n]+=amp*signal*edge

for i,folder,narr,mix in ((0,"v01","hook_narration.wav","hook_master_audio.wav"),
                          (1,"part2_v01","part2_narration.wav","part2_master_audio.wav")):
    a,b=(BOUNDS[j]*sample_frame for j in (i,i+1))
    assert np.array_equal(voice[a:b],read(OUT/folder/narr))
    fx[a:b]=read(OUT/folder/mix)-voice[a:b]

effect(19.24,.56,.042,"bell")
effect(20.53,.35,.030,"whoosh")
for at in (21.66,22.13,22.60,23.07,23.54,24.01):
    effect(at,.23,.032,"metal");effect(at+.11,.18,.017,"spark")
effect(25.05,.37,.069,"metal")
effect(25.30,2.90,.032,"power"); effect(26.03,.65,.036,"bell")
effect(28.20,3.15,.017,"power");effect(33.27,.39,.022,"whoosh")
for at in (34.1,34.9,35.7,36.5,37.28):
    effect(at,.23,.029,"plop")
effect(38.00,.52,.051,"metal");effect(38.46,2.45,.026,"power")
for at in (38.76,39.09,39.44,39.88,40.37):effect(at,.40,.018,"bell")
for at in np.arange(42.1,45.9,.36):effect(float(at),.14,.020,"plop")
effect(45.8,.39,.024,"whoosh");effect(48.76,1.2,.038,"power")
effect(49.12,1.81,.045,"whoosh");effect(51.12,.46,.035,"bell")
effect(52.45,.29,.024,"plop");effect(54.19,.48,.023,"whoosh")
for at in (54.5,55.18,55.65,56.14,57.00,60.8):effect(at,.46,.023,"bell")

for i in range(2,5):
    a,b=(BOUNDS[j]*sample_frame for j in (i,i+1))
    dst=OUT/f"part{i+1}_v01"
    wav(dst/f"part{i+1}_narration.wav",voice[a:b])
    wav(dst/f"part{i+1}_master_audio.wav",voice[a:b]+fx[a:b])
    (dst/"audio_cut.json").write_text(json.dumps({"start":BOUNDS[i]/30,"end":BOUNDS[i+1]/30,
        "frames":BOUNDS[i+1]-BOUNDS[i]},indent=2))
time=np.arange(count)/RATE
bed=0*time
for i,at in enumerate(np.arange(0,61.2,.5)):
    a=round(at*RATE);b=min(a+round(.85*RATE),count)
    t=time[a:b]-at
    pitch=(110,130.81,146.83,164.81,130.81,98)[(i//4)%6]
    bed[a:b]+=np.sin(np.pi*t/.85)**2*(.68*sine(t,pitch)+.22*sine(t,pitch*2.01))*.0095
fade=np.clip((61.62-time)/.42,0,1)*np.clip(time/.32,0,1)
wav(OUT/"final/master_mix_before_loudness.wav",voice+fx+bed*fade)
for cut in BOUNDS[1:-1]:
    p=cut*sample_frame
    score=np.std(voice[p-441:p+441])
    assert score<.002,(cut,score)
(OUT/"final/timeline.json").write_text(json.dumps({"fps":30,"frame_boundaries":BOUNDS,
    "boundaries_seconds":[cut/30 for cut in BOUNDS],"decoded_narration_seconds":len(original)/RATE,
    "tail_pad_seconds":(count-len(original))/RATE},indent=2))
