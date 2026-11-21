"""Soft daylight panorama for the visible world background; no changes to key lighting."""
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,random
from pathlib import Path
W,H=2048,1024;y=np.linspace(0,1,H)[:,None,None];top=np.array([55,126,186]);horizon=np.array([199,227,240]);t=np.minimum(y*2,1)**.8;rgb=top*(1-t)+horizon*t;arr=np.broadcast_to(rgb,(H,W,3)).copy().astype('uint8');im=Image.fromarray(arr).convert('RGBA');cloud=Image.new('RGBA',(W,H));d=ImageDraw.Draw(cloud);random.seed(827)
for cx,cy,wide in [(150,350,180),(620,440,270),(1030,310,220),(1430,405,240),(1900,465,190)]:
 for j in range(12):
  x=cx+random.uniform(-wide*.45,wide*.45);yy=cy+random.uniform(-15,15);rx=random.uniform(25,65);ry=random.uniform(8,23);d.ellipse((x-rx,yy-ry,x+rx,yy+ry),fill=(250,253,255,random.randrange(65,110)))
cloud=cloud.filter(ImageFilter.GaussianBlur(12));im=Image.alpha_composite(im,cloud);im.convert('RGB').save(Path(r'D:\remotionshorts\renders\ancient_condom\assets\daylight_sky.jpg'),quality=96)
