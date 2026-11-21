"""Turn measured narration timings into camera cuts and an original stereo mix."""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import wave
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders'/Path(__file__).resolve().parent.name
SOURCE=Path(r'C:\Users\lavis\Downloads\gta6-viraj-v4.mp3')
SR=48000
def run(args,**kwargs):
    return subprocess.run(args,check=True,capture_output=True,**kwargs)

raw=run(['ffmpeg','-v','error','-i',str(SOURCE),'-ac','1','-ar',str(SR),'-f','f32le','-']).stdout
narration=np.frombuffer(raw,np.float32)
frames=math.ceil(len(narration)*30/SR)
N=frames*SR//30
mix=np.zeros((N,2),np.float32)
dry=np.pad(narration,(0,N-len(narration)))
mix+=dry[:,None]*.88
rng=np.random.default_rng(1907)
def place(at,signal,gain=1,pan=0):
    i=round(at*SR)
    n=min(len(signal),N-i)
    if n>0:mix[i:i+n]+=signal[:n,None]*gain*np.asarray([1-.35*pan,1+.35*pan])
def tone(at,seconds,hz,gain,decay=6,bend=0,pan=0):
    t=np.arange(round(seconds*SR))/SR
    envelope=np.minimum(1,t*180)*np.exp(-t*decay)*np.minimum(1,(seconds-t)*140)
    phi=math.tau*(hz*t+.5*bend*t*t)
    place(at,(np.sin(phi)+.22*np.sin(phi*2.01))*envelope,gain,pan)
def noise(at, seconds, gain, decay=18, high=True, pan=0):
    t=np.arange(round(seconds*SR))/SR
    w=rng.normal(0,1,len(t))
    w=np.r_[0,np.diff(w)] if high else np.convolve(w,np.ones(28)/28,mode='same')*4
    window=np.minimum(1,t*340)*np.exp(-t*decay)*np.minimum(1,(seconds-t)*140)
    place(at,w*window,gain,pan)
for i in range(14):
    at=.45+i*.278
    noise(at,.12,.018,38,pan=.35*(-1)**i)
    tone(at,.074,1140,.020,38)
for i,at in enumerate((7.38,8.43,9.73)):
    tone(at,.21,138+i*36,.07,24,-94)
    noise(at,.14,.034,42,False)
for at in (6.78,7.47):
    tone(at,.16,700,.028,4)
tone(10.70,.25,982,.051);tone(10.78,.34,1493,.04)
for hz in (43,86,174):tone(11.37,.95,hz,.046,3.6,-15)
tone(14.13,.65,780,.044,5);tone(14.29,.50,1169,.034)
tone(16.10,.16,235,.062,26,-460);noise(16.10,.13,.045,28)
for at in (17.99,18.13,18.22,18.37):
    noise(at,.17,.039,26,pan=.18)
tone(18.05,.18,177,.040,22)
for i,hz in enumerate((110,220,261.63,329.63,164.81,246.94,329.63,415.3)*4):
    at=19.94+i*.304
    if at<33.93:tone(at,.49,hz,.013 if i<4 else .020,6,0,.26*(-1)**i)
tone(23.21,.53,190,.057,6,400)
tone(34.54,.48,66,.14,13,-42);noise(34.54,.43,.085,20,False);noise(34.60,.27,.037,14)
for i in range(15):
    noise(40.73+i*.086,.050,.032,58,pan=.3*(-1)**i)
tone(42.25,.34,418,.037,7);tone(42.42,.35,291,.028,8)
for at,hz in [(44.63,173),(45.10,110),(50.33,147)]:
    noise(at,.23,.032,18,False)
    tone(at,.42,hz,.032,6,-105)
for start in (46.4,47.7,49.05,51.0,52.35,53.55):
    for hz in (73.42,110.0,146.83,174.61):
        tone(start,1.31,hz,.012,1.5)
for i in range(5):
    at=56.40+i*.243
    tone(at,.33,680+i*99,.035,8,pan=.25*(-1)**i)
    noise(at,.11,.011,13)
t=np.arange(round(2.03*SR))/SR
freq=575+205*np.sin(math.tau*.89*t)
siren=np.sin(math.tau*np.cumsum(freq)/SR)*np.minimum(1,t*16)*np.minimum(1,(2.03-t)*19)
place(56.45,siren,.034)
tone(58.49,.47,80,.121,7,-64);noise(58.49,.32,.062,17,False)
def write(path, signal):
    with wave.open(str(path),'wb') as f:
        data=np.atleast_2d(signal)
        f.setnchannels(data.shape[1])
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(np.rint(np.clip(data,-1,1)*32767).astype('<i2').tobytes())

write(OUT/'premix.wav',mix)
probe=run(['ffmpeg','-hide_banner','-i',str(OUT/'premix.wav'),'-af','loudnorm=I=-14.3:TP=-3.25:LRA=4.5:print_format=json','-f','null','-'],text=True).stderr
values=json.loads(probe[probe.rfind('{'):probe.rfind('}')+1])
opts='loudnorm=I=-14.3:TP=-3.25:LRA=4.5:linear=true:'+':'.join(
    f'{target}={values[key]}' for target,key in
    [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
run(['ffmpeg','-v','error','-y','-i',str(OUT/'premix.wav'),'-af',opts+',aresample=48000,apad', '-t',str(N/SR),'-c:a','pcm_s16le',str(OUT/'final_mix.wav')])
# Times matched to the aligned narration. Zero-based cuts; frame numbers in Blender are one-based.
marks=[
 (0,'wait'),(2.65,'launch_year'),(5.12,'pawn'),(7.12,'pawn_props'),(10.71,'pc_reveal'),
 (13.06,'midnight'),(14.87,'latch'),(17.16,'chips'),(19.70,'start'),
 (21.08,'neon_display'),(22.78,'awe'),(26.06,'beach'),(31.78,'entry'),
 (36.94,'beach_freeze'),(40.36,'keys'),(41.96,'freeze_popup'),(42.94,'panic'),(43.70,'shoe'),(46.24,'boss'),
 (50.75,'cower'),(53.34,'orbit'),(58.48,'freeze')]
shots=[{'id':name,'a':round(a*30),'b':round(marks[i+1][0]*30) if i+1<len(marks) else frames}
       for i,(a,name) in enumerate(marks)]
manifest={'shots':shots,'cuts':[s['a'] for s in shots[1:]],
          'action_ranges':[[round(a*30),round(b*30)] for a,b in ((.35,2.60),(7.12,10.71),(15.02,18.6),(34.43,36.83),(40.45,42.68),(43.70,50.0),(53.34,58.48))],
          'calibration_frames':[round(t*30) for t in (1.8,4.65,7.38,8.47,9.82,11.95,14.18,16.1,18.11,20.25,23.6,30.8,34.5,35.35,41.2,42.32,44.45,45.72,46.85,52.18,54.65,56.40,57.65,58.57)],
          'closeups':[{'frame':round(18.11*30),'kind':'hand_prop','label':'Hands on the chip bag seams','region':[.14,.34,.86,.89]},
                      {'frame':round(48.38*30),'kind':'hat_brim','label':'Papa brow and spectacles shadow','region':[.13,.20,.87,.61]},
                      {'frame':round(47.35*30),'kind':'hand_prop','label':'Chappal strap grip','region':[.1,.08,.9,.60]}]}
(OUT/'timing.json').write_text(json.dumps({'frames':frames,'audio_seconds':len(narration)/SR,'audio_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),**manifest},indent=2))
(OUT/'shots.json').write_text(json.dumps(manifest,indent=2))
print(frames,len(narration)/SR)
