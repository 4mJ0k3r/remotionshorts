from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import sys
OUT=Path('D:/remotionshorts/renders/circle_challenge')
version = sys.argv[1] if len(sys.argv) > 1 else 'v1'
source = OUT if version == 'v1' else OUT/f'{version}_frames'
frames=[70,205,330,420,515,655,830,1030,1200,1380,1495,1600,1795,1950,2140]
titles=['1A · THE PRIZE','1B · STOMACH WARNING','1C · THE ACCIDENT','2A · THE BOUNDARY','2B · CANNOT SIT','2C · SUPERPOWER','3A · GAS SCIENCE','3B · BRAIN ALARM','4A · MASS EXODUS','4B · HOST RETREATS','5A · FINAL TWO','5B · SOUL LEAVES','6A · CALLING MOM','6B · MOM TO RESCUE','6C · LOVE WINS']
columns=5
if version=='v4':
    frames=[1005 if f==1030 else f for f in frames]
    extras=[(947,'3B · CONTESTANT REACTS'),(1895,'6B · CAR SKID'),(2050,'6C · THE HUG')]
    labeled=sorted(list(zip(frames,titles))+extras)
    frames,titles=zip(*labeled)
    columns=6
rows=(len(frames)+columns-1)//columns
im=Image.new('RGB',(540*columns,1010*rows),'#111827');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/seguisb.ttf',25)
for i,(f,t) in enumerate(zip(frames,titles)):
    x=(i%columns)*540;y=(i//columns)*1010
    with Image.open(source/f'frame_{f:04d}.png') as tile:im.paste(tile.convert('RGB'),(x,y+50))
    d.text((x+15,y+10),f'{t}  /  F{f}',font=font,fill='#fff2cb')
im.save(OUT/f'sheet_{version}.jpg',quality=94)
print(OUT/f'sheet_{version}.jpg')


