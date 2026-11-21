from pathlib import Path
import subprocess,json,hashlib,sys,shutil
from PIL import Image
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v9';K=R/'tools/V9_Parity_Packet/V9_Parity_Packet'
assert json.loads((P/'performance_gate.json').read_text())['passed'];assert json.loads((P/'vram.json').read_text())['passed']
if '--encode-only' not in sys.argv:
 (P/'source_hash.json').write_text(json.dumps({'sha256':hashlib.sha256((P/'slow_eddie_v9.blend').read_bytes()).hexdigest()},indent=2))
 for stage in ['render','editorial']:subprocess.run([sys.executable,str(R/'scripts/slow_eddie_v9/launch.py'),stage],check=True)
 for f in range(24,34):
  dst=P/f'frames/frame_{f:04d}.png';alt=P/f'launch/frame_{f:04d}.png'
  if f<=26:
   alpha=(f-24)/2;im=Image.blend(Image.open(dst).convert('RGB'),Image.open(alt).convert('RGB'),alpha);im.save(dst)
  else:shutil.copyfile(alt,dst)
 background=Image.open(P/'frames/frame_0254.png').convert('RGB')
 for f,alpha in zip(range(255,259),[0,1/3,2/3,1]):
  dst=P/f'frames/frame_{f:04d}.png';Image.blend(background,Image.open(dst).convert('RGB'),alpha).save(dst)
else:
 assert hashlib.sha256((P/'slow_eddie_v9.blend').read_bytes()).hexdigest()==json.loads((P/'source_hash.json').read_text())['sha256']
shutil.copyfile(K/'captions_reference.ass',P/'captions_reference.ass');(P/'fonts').mkdir(exist_ok=True);shutil.copyfile('C:/Windows/Fonts/arialbd.ttf',P/'fonts/arialbd.ttf')
# Measure actual source mix before the two-pass loudness conversion.
args=['ffmpeg','-hide_banner','-nostats','-i',str(P/'reference_mix_10s.wav'),'-af','loudnorm=I=-14.3:TP=-2.9:LRA=7:print_format=json','-f','null','-'];out=subprocess.run(args,capture_output=True,text=True,check=True).stderr;data=json.JSONDecoder().raw_decode(out[out.rfind('{'):])[0];(P/'audio_input_measurements.json').write_text(json.dumps(data,indent=2))
filt=f"loudnorm=I=-14.3:TP=-2.9:LRA=7:measured_I={data['input_i']}:measured_TP={data['input_tp']}:measured_LRA={data['input_lra']}:measured_thresh={data['input_thresh']}:offset={data['target_offset']}:linear=true"
subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i','frames/frame_%04d.png','-i','reference_mix_10s.wav','-vf','ass=captions_reference.ass:fontsdir=fonts','-af',filt,'-frames:v','300','-t','10','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','slow_eddie_v9_1080p.mp4'],cwd=P,check=True)
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(P/'slow_eddie_v9_1080p.mp4'),'-f','null','-'],check=True)
(P/'shots.json').write_text(json.dumps({'shots':[{'id':i,'a':a,'b':b} for i,a,b in [('aim',0,23),('launch',23,33),('chase',33,60),('approach',60,90),('hold',90,121),('retreat',121,170),('stare',170,210),('push',210,254),('hands',254,270),('reveal',270,300)]],'flash':[20,33],'xfade':[[23,26],[254,258]]}))
subprocess.run([sys.executable,str(R/'scripts/short_qa.py'),str(P/'slow_eddie_v9_1080p.mp4'),str(P/'qa'),str(P/'shots.json')],check=True)
print('V9 CANDIDATE RENDERED; PARITY SCORE REQUIRES REVIEW',flush=True)

C=P/'captioned';C.mkdir(exist_ok=True)
for f in [15,26,35,60,90,135,181,222,256,286]:subprocess.run(['ffmpeg','-v','error','-y','-ss',str((f-1)/30),'-i',str(P/'slow_eddie_v9_1080p.mp4'),'-frames:v','1',str(C/f'frame_{f:04d}.png')],check=True)
subprocess.run([sys.executable,str(R/'scripts/slow_eddie_v9/make_sheet.py'),'final'],check=True)
