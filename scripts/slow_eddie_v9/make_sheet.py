from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,sys
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v9';final='final' in sys.argv
frames=[15,26,35,60,90,135,181,222,256,286];labels=['Opening stare','Launch dissolve','Bullet chase','Tracked projectile','Holster arrival','Continuous pullback','Sideways standoff','Small tumbleweed','Hands dissolve','Late reveal']
fontdir=Path('C:/Windows/Fonts')
def ft(size,bold=False):return ImageFont.truetype(str(fontdir/('arialbd.ttf' if bold else 'arial.ttf')),size)
W=3784;H=1656;im=Image.new('RGB',(W,H),'#101721');d=ImageDraw.Draw(im);d.text((36,22),'SLOW EDDIE  |  V9 vs RicksClips',font=ft(42,True),fill='white');d.text((36,80),'10 matched timestamps  /  LEFT: RicksClips reference  /  RIGHT: Blender V9  /  Full frames; no crop or comparison grading',font=ft(23),fill='#B8C5D6')
for i,(f,title) in enumerate(zip(frames,labels)):
 x=36+i%5*746;y=136+i//5*746;d.rounded_rectangle((x-1,y-1,x+728,y+728),radius=8,fill='#1C2837',outline='#33465B',width=2);d.text((x+12,y+9),f'{i+1:02d}  {title}',font=ft(24,True),fill='white');d.text((x+12,y+39),f'{(f-1)/30:.3f}s  |  frame {f:03d} (1-based)',font=ft(20),fill='#B8C5D6')
 for j,tag in enumerate(['RICKSCLIPS','BLENDER V9']):
  xx=x+j*368;d.text((xx+8,y+66),tag,font=ft(18,True),fill='#6CE5C5' if j==0 else '#C0A7FF');path=P/f'reference/{f:03d}.png' if j==0 else (P/f'captioned/frame_{f:04d}.png' if final else P/f'cal_{f:03d}.png');im.paste(Image.open(path).convert('RGB').resize((360,640),Image.Resampling.LANCZOS),(xx,y+88))
d.text((36,H-32),'Reference: LC8hYwUZ-kU saved 360x640 clip. V9 displayed at equal size. '+('FINAL 1080x1920 ENCODED FRAMES / SUPPLIED CAPTIONS' if final else 'CALIBRATION / 50% RENDER'),font=ft(20),fill='#A8B7C8')
name='comparison_final' if final else 'comparison_calibration';im.save(P/(name+'.jpg'),quality=96,subsampling=0);im.save(P/(name+'.png'));print(P/(name+'.jpg'))
