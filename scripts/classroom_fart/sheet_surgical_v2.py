from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');CAL=OUT/'v2_surgical_calibration_final'
data=json.loads((OUT/'v2_calibration_manifest.json').read_text());frames=data['main_frames'];rows=json.loads((OUT/'shots_v2.json').read_text())['shots']
font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',18)
def sheet(fs,path):
    canvas=Image.new('RGB',(1160,60+524*((len(fs)+3)//4)),'#142a38');d=ImageDraw.Draw(canvas);d.text((16,12),'CLASSROOM FART V2 / SURGICAL CONTACT & GAS FIXES',font=font,fill='#f1d99c')
    for i,f in enumerate(fs):
        r=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);t=(f-1)/30;x=16+(i%4)*286;y=60+(i//4)*524
        d.text((x,y),f'{r["shot"]}  {t:05.2f}s  f{f}',font=font,fill='white');im=Image.open(CAL/f'{f:04}.png');im.thumbnail((270,480));canvas.paste(im,(x,y+28))
    canvas.save(OUT/path,quality=94)
sheet(frames,'sheet_v2.jpg');sheet(frames+data['extra_frames'],'sheet_v2_contacts.jpg')
