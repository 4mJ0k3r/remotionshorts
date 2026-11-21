"""Extract representative delivered movie frames, including both sides of cuts."""
import subprocess
from PIL import Image,ImageDraw,ImageFont
from timeline import OUT

frames=(1,80,182,183,260,355,356,450,554,555,760,785,786,980,1043,1044,1235,1236,1487,1488,1673,1674,1740,1815,1816,1920,1991,1992,2110,2211)
folder=OUT/'qa_export';folder.mkdir(exist_ok=True)
selection='+'.join(f'eq(n\\,{f-1})' for f in frames)
subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'puri_flag_physics_preview.mp4'),
                '-vf','select='+selection,'-fps_mode','vfr',str(folder/'f%02d.png')],check=True)
sheet=Image.new('RGB',(1080,1700),'#131922');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',12)
for i,f in enumerate(frames):
    im=Image.open(folder/f'f{i+1:02}.png').resize((180,320),Image.Resampling.LANCZOS)
    x=i%6*180;y=i//6*340;sheet.paste(im,(x,y))
    draw.text((x+5,y+322),f'f{f:04}  |  {(f-1)/30:.2f}s',font=font,fill='#f4ddaf')
sheet.save(folder/'delivered_review.jpg',quality=94)
print(folder/'delivered_review.jpg')
