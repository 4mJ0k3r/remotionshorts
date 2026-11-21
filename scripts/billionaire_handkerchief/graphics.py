"""Assemble labeled calibration sheets from rendered stills."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'renders'/HERE.name
CUTS=json.loads((HERE/'cuts.json').read_text(encoding='utf-8'))
from shots import AB_TEST_FRAMES, CALIBRATION, MASTER_CALIBRATION


def font(size, condensed=True):
    return ImageFont.truetype('C:/Windows/Fonts/'+('impact.ttf' if condensed else 'bahnschrift.ttf'),size)


def ab_test():
    width,height=540,960
    margin,gutter,label_height=24,12,49
    image=Image.new('RGB',(2*width+2*margin+gutter,2*(height+label_height)+gutter+2*margin),'#18171d')
    draw=ImageDraw.Draw(image)
    for row,(name,frame) in enumerate(zip(('NIGHT','DAY'),AB_TEST_FRAMES)):
        y=margin+row*(height+label_height+gutter)
        for column,(label,source) in enumerate((('BEFORE','calibration'),('AFTER','ab_test_after'))):
            x=margin+column*(width+gutter)
            path=OUT/source/f'{frame:04d}.png'
            with Image.open(path) as still:
                if still.size!=(width,height):raise ValueError(f'{path} has size {still.size}')
                image.paste(still.convert('RGB'),(x,y+label_height))
            draw.text((x,y+6),f'{label}   /   {name}   /   FRAME {frame}',font=font(25),fill='#f5eadc')
    image.save(OUT/'ab_test_night_day.jpg',quality=94,subsampling=0)


def sheet(version=1):
    w,h=270,480;gap=14;margin=26;header=83;footer=30 if version>=2 else 48
    frames=MASTER_CALIBRATION if version==3 else CALIBRATION
    columns=7 if version==3 else 5;rows=(len(frames)+columns-1)//columns
    image=Image.new('RGB',(margin*2+w*columns+gap*(columns-1),header+rows*(h+footer)+(rows-1)*gap+margin),'#181522');d=ImageDraw.Draw(image)
    d.text((margin,18),'THE BILLIONAIRE’S SILK HANDKERCHIEF',font=font(34),fill='#ffe8c6')
    d.text((margin,58),f'BLENDER CALIBRATION    /    {len(frames)} SELECTED FRAMES',font=font(15,False),fill='#c7a4bd')
    for i,f in enumerate(frames):
        folder={1:'calibration',2:'calibration_v2',3:'calibration_v3_final'}[version]
        p=OUT/folder/f'{f:04d}.png';cut=next(c for c in CUTS if c['start']<=f<(c['end'] if c['id']!=len(CUTS) else c['end']+1))
        x=margin+(w+gap)*(i%columns);y=header+(h+footer+gap)*(i//columns)
        with Image.open(p) as tile:
            assert tile.size==(540,960),(p,tile.size)
            image.paste(tile.resize((w,h),Image.Resampling.LANCZOS),(x,y))
        d.rectangle((x,y+h,x+w,y+h+footer),fill='#261e32')
        label=cut.get('label',f'{cut["id"]:02d}')
        d.text((x+10,y+h+5),f'{i+1:02d}   FRAME {f:04d}   /   CUT {label}',font=font(13,False),fill='#e6af82')
        if version==1:d.text((x+10,y+h+24),cut['caption'],font=font(17,False),fill='#fff0de')
    image.save(OUT/f'sheet_v{version}.jpg',quality=94,subsampling=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('ab-test','sheet','sheet-v2','sheet-v3'))
    {'ab-test':ab_test,'sheet':sheet,'sheet-v2':lambda:sheet(2),'sheet-v3':lambda:sheet(3)}[parser.parse_args().mode]()
