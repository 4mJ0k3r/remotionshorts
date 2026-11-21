from pathlib import Path
import json,sys
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
rows=json.loads((OUT/'segments_timeline.json').read_text())['shots']
version='v2' if '--v2' in sys.argv else 'v1';suffix='_v2' if version=='v2' else ''
sheet=Image.new('RGB',(4*366+18,3*718+100),'#13232c');d=ImageDraw.Draw(sheet)
font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',18)
d.text((18,15),'HAIR SENSOR / NARRATION-ALIGNED CALIBRATION / '+version,font=font,fill='#e5f8ed')
for i,r in enumerate(rows):
    im=Image.open(OUT/('frame_'+r['shot']+suffix+'.png')).convert('RGB');im.thumbnail((348,619))
    x=18+(i%4)*366;y=60+(i//4)*718
    d.text((x,y),f"{r['shot']}  /  f{r['representative_frame']}  /  {(r['representative_frame']-1)/30:.2f}s",font=font,fill='#f8d58b')
    sheet.paste(im,(x,y+30))
    text=r['narration_cue'];d.text((x,y+657),text[:37],font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',16),fill='#bdd3dc')
sheet.save(OUT/('sheet_'+version+'.jpg'),quality=94)
print(OUT/('sheet_'+version+'.jpg'))
