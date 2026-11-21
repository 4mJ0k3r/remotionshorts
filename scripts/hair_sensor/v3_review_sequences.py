"""CPU-only review sheets from actual rendered preview frames, never scene substitutes."""
from pathlib import Path
import json,sys
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');QA=OUT/'qa_v3';QA.mkdir(exist_ok=True)
SPANS=[('pluck',169,249),('grip',250,291),('perfume_press',292,365),('shock',421,465),('palm_launch',844,921),('scent_flight',922,1029),('survivor_wave',1176,1272),('rescue_lift',1273,1344)]
source=OUT/'v3_frames'
if '--encoded' in sys.argv:
    import av
    source=QA/'decoded_frames';source.mkdir(exist_ok=True)
    needed=set()
    for _,a,b in SPANS:needed.update(range(a,b+1,7));needed.add(b)
    needed.update([85,86,168,169,249,250,291,292,365,366,420,421,465,466,725,726,843,844,885,886,921,922,1029,1030,1109,1110])
    with av.open(str(OUT/'hair_sensor_v3_preview.mp4')) as container:
        for index,frame in enumerate(container.decode(video=0),1):
            if index in needed:frame.to_image().save(source/f'{index:04d}.png')
for name,a,b in SPANS:
    if not (source/f'{b:04d}.png').exists():continue
    # Approximately 4 fps for overview; all integer contact transforms are checked separately.
    frames=list(range(a,b+1,7))
    if frames[-1]!=b:frames.append(b)
    cols=6;cw,ch=182,347;nr=(len(frames)+cols-1)//cols
    sheet=Image.new('RGB',(cols*cw,nr*ch+40),'#17212b');d=ImageDraw.Draw(sheet);font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',15)
    d.text((10,10),f'{name.upper()} / ACTUAL V3 PREVIEW FRAMES {a}-{b}',font=font,fill='#f0d4a0')
    for i,f in enumerate(frames):
        p=Image.open(source/f'{f:04d}.png').convert('RGB');p.thumbnail((174,309));x=(i%cols)*cw+4;y=(i//cols)*ch+40;sheet.paste(p,(x,y+20));d.text((x,y),str(f),font=font,fill='white')
    sheet.save(QA/f'action_{name}.jpg',quality=93)
print('Actual-render action review sheets created.')
