"""Extract actual delivered movie frames for story/contact review."""
import subprocess
import sys
from PIL import Image,ImageDraw,ImageFont
from timeline import OUT

frames=(1,25,65,110,160,210,260,325,380,520,630,700,760,820,875,990,1120,1205,1300,1380,1410,1444,1452,1480,1500,1520,1542,1590,1625,1635)
revision2=len(sys.argv)>1 and sys.argv[1]=='v2'
anatomy=len(sys.argv)>1 and sys.argv[1]=='master'
if revision2:frames=(25,236,247,255,269,282,300,416,417)
if anatomy:frames=(1,25,65,184,348,380,400,520,615,1205,1239,1500,1542,1590,1635)
folder=OUT/('qa_export_anatomy' if anatomy else 'qa_export_v2' if revision2 else 'qa_export');folder.mkdir(exist_ok=True)
selection='+'.join(f'eq(n\\,{f-1})' for f in frames)
subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/('commode_sniper_v2_master.mp4' if anatomy else 'commode_sniper_v2_preview.mp4' if revision2 else 'commode_sniper_preview.mp4')),'-vf','select='+selection,
                '-fps_mode','vfr',str(folder/'f%02d.png')],check=True)
columns,tw,th=(3,270,480) if revision2 or anatomy else (5,216,384)
sheet=Image.new('RGB',(columns*tw,((len(frames)+columns-1)//columns)*(th+24)),'#14181d');d=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14)
for i,f in enumerate(frames):
    with Image.open(folder/f'f{i+1:02d}.png') as im:frame=im.resize((tw,th),Image.Resampling.LANCZOS)
    x=i%columns*tw;y=i//columns*(th+24);sheet.paste(frame,(x,y))
    d.text((x+7,y+th+4),f'f{f:04d}  |  {(f-1)/30:.2f}s',font=font,fill='#eadfc9')
sheet.save(folder/'delivered_review.jpg',quality=94)
print(folder/'delivered_review.jpg')
