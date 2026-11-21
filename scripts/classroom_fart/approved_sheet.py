"""Map unchanged calibration ranges explicitly onto the final V6 source."""
import json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');proof={}
for rev in [4,5,6]:
    for p in (OUT/f'calibration_v{rev}').glob('*.png'):
        f=int(p.stem)
        if rev<6 and (971<=f<=1298 or 1410<=f<=1483):continue
        proof[f]=p
rows=json.loads((OUT/'shots.json').read_text())['shots'];font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',18)
main=[60,160,232,300,385,455,520,620,702,855,1007,1145,1360,1446,1580]
def sheet(frames,name):
    tw,th=270,480;cols=5;im=Image.new('RGB',(1422,44+516*((len(frames)+4)//5)),'#142a38');d=ImageDraw.Draw(im)
    d.text((12,10),'CLASSROOM FART / FINAL CALIBRATION / V6',font=font,fill='#f1db9f')
    for i,f in enumerate(frames):
        row=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);x=12+i%5*282;y=44+i//5*516
        d.text((x,y),f'{row["shot"]} / f{f}',font=font,fill='white');frame=Image.open(proof[f]);frame.thumbnail((tw,th));im.paste(frame,(x,y+26))
    im.save(OUT/name,quality=93)
sheet(main,'sheet_final.jpg');sheet(sorted(proof),'sheet_final_contacts.jpg')
(OUT/'calibration_frame_map.json').write_text(json.dumps({'final_source':'classroom_fart_v6.blend','source_sha256':hashlib.sha256((OUT/'classroom_fart_v6.blend').read_bytes()).hexdigest(),'frames':{str(k):str(v) for k,v in proof.items()},'basis':'V5 camera-only 971..1034, V6 head-only971..1298 and friend visibility1410..1483; unchanged ranges retained. No source mutation in this script.'},indent=2))
