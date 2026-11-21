"""CPU artifact: both sides of all changed-range boundaries in the final frame sequence."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');QA=OUT/'qa_v3';source=QA/'decoded_frames' if '--encoded' in sys.argv else OUT/'v3_frames'
frames=[85,86,168,169,249,250,291,292,365,366,420,421,465,466,725,726,843,844,885,886,921,922,1029,1030,1109,1110]
cw,ch=182,347;cols=6;im=Image.new('RGB',(cols*cw,((len(frames)+cols-1)//cols)*ch+42),'#17212b');d=ImageDraw.Draw(im);font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',15)
d.text((10,10),'FINAL V3 / PATCH BOUNDARIES / BOTH SIDES',font=font,fill='#efd6a6')
for i,f in enumerate(frames):
    p=Image.open(source/f'{f:04d}.png').convert('RGB');p.thumbnail((174,309));x=i%cols*cw+4;y=i//cols*ch+42;im.paste(p,(x,y+20));d.text((x,y),f'f{f}',font=font,fill='white')
im.save(QA/'patch_boundaries.jpg',quality=94)
