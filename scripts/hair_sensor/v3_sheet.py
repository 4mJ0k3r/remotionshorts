import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');rows=json.loads((OUT/'shots_v3.json').read_text())['shots'];confirm='--confirm' in sys.argv;final='--final' in sys.argv
source=OUT/('v3_stills_final' if final else 'v3_stills_confirm' if confirm else 'v3_stills')
def sheet(rows,name,columns=4):
    cw,ch=288,550;nr=(len(rows)+columns-1)//columns;im=Image.new('RGB',(columns*cw+24,nr*ch+64),'#192331');d=ImageDraw.Draw(im);f=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',17)
    d.text((16,13),'HAIR SENSOR V3 / 21-CUT STUDIO REBUILD',font=f,fill='#f3dfb9')
    for i,r in enumerate(rows):
        x=16+(i%columns)*cw;y=53+(i//columns)*ch;p=Image.open(source/f"{r['sample']:04d}.png").convert('RGB');p.thumbnail((272,484));im.paste(p,(x,y+25));d.text((x,y),f"{r['shot']} / f{r['sample']} / {(r['sample']-1)/30:.2f}s",font=f,fill='#e6c48f');d.text((x,y+515),r['title'][:31],font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',14),fill='#b8c9d5')
    im.save(OUT/name,quality=94)
sheet([r for r in rows if r['calibration']], 'sheet_v3_final.jpg' if final else 'sheet_v3_confirm.jpg' if confirm else 'sheet_v3.jpg')
sheet(rows,'sheet_v3_all_final.jpg' if final else 'sheet_v3_all_confirm.jpg' if confirm else 'sheet_v3_all.jpg',7)
print('V3 12-tile and 21-cut sheets created.')
