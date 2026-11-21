import subprocess,sys,json,hashlib
from pathlib import Path
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v8'
b=json.loads((P/'benchmark.json').read_text());assert len(b)==6 and max(x['seconds'] for x in b)<=2.0
assert json.loads((P/'town_preservation.json').read_text())['unchanged'];assert (P/'comparison_calibration.jpg').exists()
source=P/'slow_eddie_v8.blend';(P/'source_hash.json').write_text(json.dumps({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'runtime_sha256':hashlib.sha256((R/'scripts/slow_eddie_v8/runtime.py').read_bytes()).hexdigest()},indent=2))
subprocess.run([sys.executable,str(R/'scripts/slow_eddie_v8/launch.py'),'render'],check=True)
assert len(list((P/'frames').glob('frame_*.png')))==300
subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(P/'frames/frame_%04d.png'),'-frames:v','300','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(P/'slow_eddie_v8_1080p.mp4')],check=True)
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(P/'slow_eddie_v8_1080p.mp4'),'-f','null','-'],check=True)
(P/'shots.json').write_text(json.dumps({'shots':[{'id':n,'a':a,'b':b} for n,a,b in [('aim',0,36),('chase',36,84),('hip',84,105),('reverse',105,160),('standoff',160,204),('push',204,245),('hero',245,300)]],'flash':[29,36]}))
subprocess.run([sys.executable,str(R/'scripts/short_qa.py'),str(P/'slow_eddie_v8_1080p.mp4'),str(P/'qa'),str(P/'shots.json')],check=True)
subprocess.run([sys.executable,str(R/'scripts/slow_eddie_v8/make_sheet.py'),'final'],check=True)
subprocess.run([sys.executable,str(R/'scripts/slow_eddie_v8/post_qa.py')],check=True)
print('V8 DELIVERY VERIFIED',flush=True)
