from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import subprocess,sys
P=Path('D:/remotionshorts/renders/slow_eddie_v12');final='final' in sys.argv
frames=[24,31,61,74,76,78,91,121,122,167,169,171,210,211,280,286,300]
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',20)
out=Image.new('RGB',(7*222,3*440+60),'#111822');d=ImageDraw.Draw(out);d.text((20,15),'V12 TRANSITION JUNCTIONS / '+('ENCODED DELIVERY' if final else 'CALIBRATION'),font=font,fill='white')
for i,f in enumerate(frames):
 if final:
  path=P/f'junction/frame_{f:04d}.png';path.parent.mkdir(exist_ok=True);subprocess.run(['ffmpeg','-v','error','-y','-ss',str((f-1)/30),'-i',str(P/'slow_eddie_v12_1080p.mp4'),'-frames:v','1',str(path)],check=True);im=Image.open(path).convert('RGB')
 else:
  im=Image.open(P/f'cal_{f:03d}.png').convert('RGB')
  if 24<=f<=30 and (P/f'launch/frame_{f:04d}.png').exists():
   alt=Image.open(P/f'launch/frame_{f:04d}.png').convert('RGB').resize(im.size)
   alpha=(f-24)/2 if f<=26 else (1 if f<=30 else 1-(f-30)/3);im=Image.blend(im,alt,alpha)
 x=i%7*222;y=60+i//7*440;d.text((x+8,y),f'f{f:03d} / {(f-1)/30:.3f}s',font=font,fill='white');out.paste(im.resize((216,384),Image.Resampling.LANCZOS),(x+3,y+30))
out.save(P/('transition_junctions_final.png' if final else 'transition_junctions_calibration.png'));print('Junction sheet saved')
