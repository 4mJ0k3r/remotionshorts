from pathlib import Path
import json,sys
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\bamboo_ambush');version='v2_confirm' if '--confirm' in sys.argv else 'v2';cal=OUT/('calibration_'+version);frames=[45,140,240,345,430,495,560,660,735,800,860,910];cuts=['1A','1B','2A','2B','3A','3B','3C','4A','4B','5A','5B','5C'];sheet=Image.new('RGB',(2220,3030),'#141b22');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',21)
for j,(f,cut) in enumerate(zip(frames,cuts)):
 x=15+j%4*550;y=15+j//4*1000;im=Image.open(cal/f'{f:04d}.png').convert('RGB');assert im.size==(540,960);sheet.paste(im,(x,y+32));d.text((x,y),f'Cut {cut} | f{f} | {(f-1)/30:.2f}s',font=font,fill='white')
sheet.save(OUT/('sheet_v2_confirmation.jpg' if '--confirm' in sys.argv else 'sheet_v2.jpg'),quality=95,subsampling=0)
