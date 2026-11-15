"""Tile the fourteen 540 × 960 stills with cut and frame labels."""
from pathlib import Path
import ast
import sys
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'renders/washroom_experiment'
tree=ast.parse((HERE/'build.py').read_text(encoding='utf8'))
cuts=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CUTS' for t in n.targets))
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',16)
w,h=270,480;g=8;title=28
sheet=Image.new('RGB',(5*w+6*g,3*(h+title)+4*g),'#131a2a')
draw=ImageDraw.Draw(sheet)
for i,(_,_,f,label) in enumerate(cuts):
 im=Image.open(OUT/f'calibration/{f:04d}.png')
 if im.size!=(540,960):raise ValueError((f,im.size))
 x=g+(i%5)*(w+g);y=g+(i//5)*(h+title+g)
 sheet.paste(im.convert('RGB').resize((w,h),Image.Resampling.LANCZOS),(x,y+title))
 draw.text((x+5,y+5),f'{label}  ·  f{f}',font=font,fill='#f2f5ff')
version=int(sys.argv[1]) if len(sys.argv)>1 else 1
sheet.save(OUT/f'sheet_v{version}.jpg',quality=95)
