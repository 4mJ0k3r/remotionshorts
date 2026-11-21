"""Current-story audio and evidence manifest. Does not change supplied recordings."""
import json, subprocess, hashlib, wave
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[3]
P=R/'renders/gold_mine_salting_10s/v01'
SRC=Path('C:/Users/lavis/Downloads/How Mine Salting Worked_0_10.mp3')
P.mkdir(parents=True,exist_ok=True)
raw=subprocess.run(['ffmpeg','-v','error','-i',str(SRC),'-f','f32le','-ac','2','-ar','48000','pipe:1'],capture_output=True,check=True).stdout
audio=np.frombuffer(raw,np.float32).reshape(-1,2)
assert len(audio)<=481600, 'Preserve complete recording; extend frame count if necessary'
vo=np.zeros((481600,2),np.float64);vo[:len(audio)]=audio
mono=vo.mean(1)
env=np.array([np.sqrt(np.mean(mono[i*1600:(i+1)*1600]**2)) for i in range(301)])
env=np.clip((env-.008)/max(.02,np.percentile(env,92)-.008),0,1)
for i in range(1,len(env)):env[i]=.75*env[i]+.25*env[i-1]
(P/'audio_envelope.json').write_text(json.dumps(env.round(5).tolist()))
rng=np.random.default_rng(1899);sr=48000
music=np.zeros(481600);fx=np.zeros(481600)
def place(target,start,signal,gain=1):
 a=round(start*sr);n=min(len(signal),len(target)-a)
 if n>0:target[a:a+n]+=gain*signal[:n]
def pluck(hz,d=1.1):
 t=np.arange(int(sr*d))/sr
 return sum(np.sin(2*np.pi*hz*k*t+.04*k)*np.exp(-t*(3.5+k)) / k**1.6 for k in range(1,6))*(1-np.exp(-t*200))
for t,hz in [(0,110),(.85,164.81),(2.9,146.83),(4.2,110),(5.6,164.81),(7,146.83),(8.3,110)]:place(music,t,pluck(hz),.30)
vrms=np.sqrt(np.mean(mono**2));music*=vrms*10**(-21/20)/max(1e-6,np.sqrt(np.mean(music**2)))
# Original foley: mechanical clicks, resonant cave blast, rock scatter, wink harmonic.
for t in [.37,.92,1.40]:
 x=np.arange(int(.085*sr))/sr
 place(fx,t,rng.normal(size=len(x))*np.exp(-x*65)+.4*np.sin(x*2*np.pi*1700)*np.exp(-x*90),.025)
t=np.arange(int(1.25*sr))/sr
noise=rng.normal(size=len(t));low=np.convolve(noise,np.ones(100)/100,mode='same')
blast=(2.5*low*np.exp(-t*5)+.45*np.sin(2*np.pi*(70*t-18*t*t))*np.exp(-t*7))*(1-np.exp(-t*700))
place(fx,1.96,blast,.17);place(fx,2.13,blast,.055)
for start in [2.20,2.29,2.37,2.48,2.66,2.83]:
 t=np.arange(int(.10*sr))/sr
 place(fx,start,rng.normal(size=len(t))*np.exp(-t*45),.016)
for hz in [329.63,415.30,554.37]:place(fx,9.42,pluck(hz,.5),.010)
air=rng.normal(size=481600);air=np.convolve(air,np.ones(240)/240,mode='same')
air*=vrms*10**(-38/20)/max(1e-6,np.sqrt(np.mean(air**2)))
mix=vo+(music+fx+air)[:,None]
assert np.max(np.abs(mix))<.99, 'Mix clips: lower added sounds, retain VO'
for name,data in [('narration_preserved.wav',vo),('premix_unlimited.wav',mix)]:
 with wave.open(str(P/name),'wb') as w:
  w.setnchannels(2);w.setsampwidth(3);w.setframerate(sr)
  v=np.clip(np.round(data*8388607),-8388608,8388607).astype(np.int32).reshape(-1)
  w.writeframes(np.column_stack([v&255,(v>>8)&255,(v>>16)&255]).astype(np.uint8).tobytes())
subprocess.run(['ffmpeg','-y','-v','error','-i',str(P/'premix_unlimited.wav'),'-af','aresample=192000,alimiter=limit=0.69:level=false:latency=true,aresample=48000','-c:a','pcm_s24le',str(P/'final_mix.wav')],check=True)
meta={'schema':1,'shots':[{'id':n,'a':a,'b':b} for n,a,b in [('load',0,45),('blast',45,75),('impact',75,110),('buddy',110,270),('wink',270,301)]],
 'cuts':[45,75,110,270],'continuous_junctions':[], 'transitions':[], 'xfade':[],
 'calibration_frames':[0,10,20,30,40,45,54,58,60,66,74,75,82,94,109,110,140,175,195,201,215,235,255,269,270,280,286,292,299],
 'action_ranges':[[0,44],[55,73],[75,106],[175,268],[270,299]],
 'mad_exclude_regions':[],
 'shadow_checks':[{'name':'Opening locked-camera forehead','start':0,'end':8,'registration':'locked-camera','regions':[[.43,.410,.57,.423]],'max_adjacent_luma':1}],
 'closeups':[{'frame':10,'kind':'hat_brim','label':'Miner real brim receiver','region':[.25,.20,.75,.43]},
             {'frame':40,'kind':'hand_prop','label':'Shotgun forend and trigger grip','region':[.16,.37,.85,.72]},
             {'frame':235,'kind':'hand_prop','label':'Buddy mug handle finger wrap','region':[.30,.45,.72,.79]},
             {'frame':286,'kind':'hand_prop','label':'Gold shell visible front/back grip','region':[.40,.40,.90,.77]}]}
(P/'shots.json').write_text(json.dumps(meta,indent=2))
(P/'input_identity.json').write_text(json.dumps({'audio_path':str(SRC),'audio_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'decoded_audio_samples':len(audio),'fps':30,'frames':301,'audio_policy':'Exact supplied audio; no retiming; user authorized visual wink without missing final word.','music':'Original synthesized dry plucks at -21dB RMS relative to supplied VO','reference_video':'C:/Users/lavis/Downloads/How Mine Salting Worked_0_10.mp4'},indent=2))
print('PREPARED',len(audio)/sr,'seconds of untouched narration; 301-frame padded timeline; mix peak',np.max(np.abs(mix)))
