import subprocess,sys
from pathlib import Path
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v6'
subprocess.run([sys.executable,str(R/'scripts/slow_eddie_v6/launch.py'),'patch'],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(P/'frames/frame_%04d.png'),'-frames:v','300','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',str(P/'slow_eddie_v6_1080p.mp4')],check=True)
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(P/'slow_eddie_v6_1080p.mp4'),'-f','null','-'],check=True)
subprocess.run([sys.executable,str(R/'scripts/short_qa.py'),str(P/'slow_eddie_v6_1080p.mp4'),str(P/'qa'),str(P/'shots.json')],check=True)
subprocess.run([sys.executable,str(R/'scripts/slow_eddie_v6/post_qa.py')],check=True)
print('FINAL DELIVERY VERIFIED')
