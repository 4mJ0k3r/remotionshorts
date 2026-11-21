from pathlib import Path
import subprocess,json,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v6/comparison';P.mkdir(exist_ok=True)
frames=[15,31,60,90,96,135,165,195,222,280]
labels=['Aim / blink','Recoil / launch','Bullet chase','Holster arrival','Pullback entrance','Reverse pullback','Wide standoff','Drift / tumbleweed','Silhouette push-in','Eddie / nod']
files={'ricksclips':R/'renders/slow_eddie_reference.mp4','v6':R/'renders/slow_eddie_v6/slow_eddie_v6_1080p.mp4'}
for tag,source in files.items():
 out=P/tag;out.mkdir(exist_ok=True)
 expression='+'.join(f'eq(n,{f-1})' for f in frames)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-vf',f'select={expression.replace(chr(44),chr(92)+chr(44))},scale=360:640:flags=lanczos','-vsync','0',str(out/'%02d.png')],check=True)
 assert len(list(out.glob('*.png')))==10
fontpath=Path('C:/Windows/Fonts')
def font(size,bold=False):return ImageFont.truetype(str(fontpath/('arialbd.ttf' if bold else 'arial.ttf')),size)
# 10 comparison moments, 20 source frames; same display size, full-frame uncropped.
margin=36;gap=18;inside=8;pairw=728;pairh=728;header=136
W=2*margin+5*pairw+4*gap;H=header+2*pairh+gap+46
sheet=Image.new('RGB',(W,H),'#101721');d=ImageDraw.Draw(sheet)
d.text((margin,22),'SLOW EDDIE  |  V6 vs RicksClips',font=font(42,True),fill='#F5F7FA')
d.text((margin,80),'10 matched timestamps  /  LEFT: RicksClips reference  /  RIGHT: Blender V6  /  Full frames; no crop or color adjustment',font=font(23),fill='#B8C5D6')
manifest=[]
for i,(f,label) in enumerate(zip(frames,labels)):
 x=margin+(i%5)*(pairw+gap);y=header+(i//5)*(pairh+gap);t=(f-1)/30
 d.rounded_rectangle((x-1,y-1,x+pairw,y+pairh),radius=8,fill='#1C2837',outline='#33465B',width=2)
 d.text((x+12,y+9),f'{i+1:02d}  {label}',font=font(24,True),fill='#FFFFFF')
 d.text((x+12,y+39),f'{t:05.3f}s  |  frame {f:03d} (1-based)',font=font(20),fill='#B8C5D6')
 for j,(tag,title,color) in enumerate([('ricksclips','RICKSCLIPS','#6CE5C5'),('v6','BLENDER V6','#C0A7FF')]):
  xx=x+j*(360+inside);d.text((xx+8,y+66),title,font=font(18,True),fill=color)
  im=Image.open(P/tag/f'{i+1:02d}.png').convert('RGB');assert im.size==(360,640);sheet.paste(im,(xx,y+88))
 manifest.append({'pair':i+1,'label':label,'source_frame_1based':f,'source_frame_0based':f-1,'time_seconds':t})
d.text((margin,H-32),'Reference: LC8hYwUZ-kU (saved 360x640 clip).  V6: native 1080x1920, downsampled to 360x640 for equal-size comparison. Reference subtitles retained.',font=font(20),fill='#A8B7C8')
sheet.save(P/'slow_eddie_v6_vs_ricksclips_10_pairs.png');sheet.save(P/'slow_eddie_v6_vs_ricksclips_10_pairs.jpg',quality=96,subsampling=0)
(P/'manifest.json').write_text(json.dumps({'reference_url':'https://www.youtube.com/shorts/LC8hYwUZ-kU','sources':{k:{'path':str(v),'sha256':hashlib.sha256(v.read_bytes()).hexdigest()} for k,v in files.items()},'pairs':manifest,'framing':'uncropped; 360x640 each; no grading or overlays on source images'},indent=2))
print('Created',W,H,P/'slow_eddie_v6_vs_ricksclips_10_pairs.jpg')
