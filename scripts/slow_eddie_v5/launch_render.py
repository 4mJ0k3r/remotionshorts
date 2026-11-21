import os,json,uuid,subprocess,time,hashlib
from pathlib import Path
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v5';lock=R/'.blender_gpu.lock';owner=uuid.uuid4().hex
b=json.loads((P/'benchmark.json').read_text());assert len(b)==5 and max(x['seconds'] for x in b)<=2.0,b
fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
with os.fdopen(fd,'w') as f:json.dump({'project':'slow_eddie_v5','pid':os.getpid(),'owner':owner},f)
source=P/'slow_eddie_v5.blend';(P/'source_hash.json').write_text(json.dumps({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}))
try:
 with open(P/'render.log','w') as log:subprocess.run(['D:/tools/Blender/4.2.23/blender.exe','-b','--factory-startup','--python-exit-code','1',str(source),'--python',str(R/'scripts/slow_eddie_v5/render.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
finally:
 if lock.exists() and json.loads(lock.read_text()).get('owner')==owner:lock.unlink()
subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(P/'frames/frame_%04d.png'),'-frames:v','300','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(P/'slow_eddie_v5_1080p.mp4')],check=True)
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(P/'slow_eddie_v5_1080p.mp4'),'-f','null','-'],check=True)
(P/'shots.json').write_text(json.dumps({'shots':[{'id':n,'a':a,'b':b} for n,a,b in [('aim',0,32),('bullet',33,95),('pullback',96,214),('eddie',215,299)]]}))
subprocess.run(['python',str(R/'scripts/short_qa.py'),str(P/'slow_eddie_v5_1080p.mp4'),str(P/'qa'),str(P/'shots.json')],check=True)
print('DONE',flush=True)
