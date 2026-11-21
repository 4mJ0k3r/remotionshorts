from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
frames=[('1A clamp',35),('1A hold',65),('1C stretch',184),('1C snap',185),('1C pull',205),('1C free',217),('1D continuation',234),('3A desk support',864),('3B support',886),('3B liftoff',911),('4B translucent vapor',1224),('4C supported carry',1308)]
source=OUT/'v4_stills';encoded='--encoded' in sys.argv
if encoded:
    import av
    source=OUT/'qa_v4/decoded_contacts';source.mkdir(exist_ok=True);needed={f for _,f in frames}
    with av.open(str(OUT/'hair_sensor_v4_master.mp4')) as movie:
        for f,frame in enumerate(movie.decode(video=0),1):
            if f in needed:frame.to_image().save(source/f'{f:04d}.png')
sheet=Image.new('RGB',(4*286+20,3*548+64),'#182330');d=ImageDraw.Draw(sheet);font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',16)
d.text((14,14),'V4 / FOUR CONTACT FIXES / ORIGINAL V3 ART & LIGHTING',font=font,fill='#e7d5ac')
for i,(label,f) in enumerate(frames):
    im=Image.open(source/f'{f:04d}.png').convert('RGB');im.thumbnail((270,480));x=14+i%4*286;y=50+i//4*548;d.text((x,y),f'{label} / f{f}',font=font,fill='#eee0bd');sheet.paste(im,(x,y+25))
target=OUT/'qa_v4/encoded_contacts.jpg' if encoded else OUT/'sheet_v4_contacts.jpg';sheet.save(target,quality=94);print(target)
