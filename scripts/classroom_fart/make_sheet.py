from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
import sys
OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
ROWS=json.loads((OUT/'shots.json').read_text())['shots']
MAIN=[60,160,232,300,385,455,520,620,702,855,1007,1145,1360,1446,1580]
REV=next((a[2:] for a in sys.argv if a.startswith('--v')),'v1');CAL=OUT/('calibration' if REV=='v1' else f'calibration_{REV}')
ALL=[int(p.stem) for p in CAL.glob('*.png')]
FONT=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',18)
def sheet(frames,name):
    cols=5;tw,th=270,480;rows=(len(frames)+cols-1)//cols
    canvas=Image.new('RGB',(cols*(tw+12)+12,rows*(th+36)+44),'#142a38');d=ImageDraw.Draw(canvas)
    d.text((12,10),'CLASSROOM FART / CALIBRATION / NOT FINAL VIDEO',font=FONT,fill='#f4d99c')
    for i,f in enumerate(frames):
        row=next(r for r in ROWS if r['start_frame']<=f<=r['end_frame']);x=12+(i%cols)*(tw+12);y=44+(i//cols)*(th+36)
        d.text((x,y),f'{row["shot"]} / f{f}',font=FONT,fill='white')
        im=Image.open(CAL/f'{f:04}.png');im.thumbnail((tw,th));canvas.paste(im,(x,y+26))
    canvas.save(OUT/name,quality=93)
sheet(MAIN,f'sheet_{REV}.jpg');sheet(sorted(ALL),f'sheet_{REV}_contacts.jpg')
print('15-tile sheet plus all-cut/contact evidence saved.')
