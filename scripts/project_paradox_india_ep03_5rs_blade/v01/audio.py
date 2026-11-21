"""Original synthesized foley/underscore, preserving narration speed and words."""
import json,subprocess,math,wave
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[3];P=R/'renders/project_paradox_india_ep03_5rs_blade/v01'
sr=48000;count=1401*1600;duration=count/sr;rng=np.random.default_rng(509)
raw=subprocess.run(['ffmpeg','-v','error','-i',str(P/'narration_preserved.wav'),'-ac','1','-ar',str(sr),'-f','f32le','-'],capture_output=True,check=True).stdout
source=np.frombuffer(raw,np.float32);vo=np.zeros(count);vo[:len(source)]=source
music=np.zeros(count);foley=np.zeros(count)
def place(dst,time,signal,gain=1,wrap=False):
 start=round(time*sr);n=min(len(signal),len(dst)-start)
 if n>0:dst[start:start+n]+=signal[:n]*gain
 if wrap and len(signal)>n:dst[:len(signal)-n]+=signal[n:]*gain
def bell(hz,length=.30,decay=13):
 t=np.arange(round(sr*length))/sr
 return sum(np.sin(2*math.pi*hz*k*t)*np.exp(-t*decay*k*.65)/k**1.7 for k in [1,2.71,4.13])*(1-np.exp(-t*1200))
for i in range(64):
 hz=[110,146.83,164.81,130.81][i%4];t=np.arange(round(sr*1.3))/sr
 pluck=np.sin(2*math.pi*hz*t)*np.exp(-t*7)+.25*np.sin(2*math.pi*hz*2*t)*np.exp(-t*10)
 place(music,i*duration/64,pluck,1,True)
env=np.array(json.loads((P/'audio_envelope.json').read_text()))
duck=np.interp(np.arange(count)/1600,np.arange(len(env)),env)
music*=1-.65*np.clip(duck,0,1)
vrms=np.sqrt(np.mean(vo*vo));music*=vrms*10**(-23/20)/max(1e-8,np.sqrt(np.mean(music*music)))
events=[]
for sec,hz,gain,kind in [(0.25,1400,.045,'coin clink'),(5.0,210,.055,'press thud'),(5.2,3400,.025,'blade shing'),(11.7,1800,.025,'jar coin clink'),(12.3,1500,.025,'jar coin clink'),(13.1,2100,.025,'jar coin clink'),(17.4,480,.05,'heavy coin scale thud'),(25.3,1500,.03,'coin into ladle'),(31.0,2000,.025,'blade price'),(34.2,950,.045,'scale payment clatter'),(39.9,130,.06,'cancelled stamp thud'),(41.7,350,.04,'mint lever click')]:
 place(foley,sec,bell(hz),gain);events.append({'seconds':sec,'kind':kind})
for i in range(6):
 sec=(822-1+i*5)/30;place(foley,sec,bell(2100+i*180,.16,20),.025);events.append({'seconds':sec,'kind':'blade '+str(i+1)+' click'})
for i in range(8):place(foley,42.1+i*.24,bell(2300+i*120,.2,18),.025)
t=np.arange(round(sr*1.3))/sr;noise=rng.normal(size=len(t));sizzle=(noise-np.convolve(noise,np.ones(35)/35,mode='same'))*np.sin(math.pi*np.minimum(1,t/1.3))**2
place(foley,26.8,sizzle,.008);events.append({'seconds':26.8,'kind':'molten sizzling pour'})
t=np.arange(round(sr*.7))/sr;riser=rng.normal(size=len(t))*np.linspace(0,.009,len(t))
place(foley,duration-.7,riser);mix=vo+music+foley
def wav(path,data):
 with wave.open(str(path),'wb') as w:
  w.setnchannels(2);w.setsampwidth(3);w.setframerate(sr)
  v=np.round(np.clip(np.repeat(data[:,None],2,axis=1),-.999999,.999999)*8388607).astype(np.int32).reshape(-1)
  w.writeframes(np.column_stack([v&255,(v>>8)&255,(v>>16)&255]).astype(np.uint8).tobytes())
assert np.max(abs(mix))<1,'Premix clipping'
wav(P/'premix.wav',mix)
probe=subprocess.run(['ffmpeg','-hide_banner','-i',str(P/'premix.wav'),'-af','loudnorm=I=-14.3:TP=-3.3:LRA=5:print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
stats=json.loads(probe[probe.rfind('{'):probe.rfind('}')+1]);(P/'mix_loudness_pass1.json').write_text(json.dumps(stats,indent=2))
filters=f"loudnorm=I=-14.3:TP=-3.3:LRA=5:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}:linear=true:print_format=json"
subprocess.run(['ffmpeg','-y','-v','error','-i',str(P/'premix.wav'),'-af',filters,'-ar','48000','-c:a','pcm_s24le',str(P/'final_mix.wav')],check=True)
(P/'audio_events.json').write_text(json.dumps({'narration_speed_unchanged':True,'mix_samples':count,'music_target_below_vo_db':23,'events':events},indent=2))
print('AUDIO_MIX_READY',duration,'seconds')
