"""Project-owned hand-inked character art; latest user references override the volumetric cast."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageChops
import numpy as np,math
ART=Path(r'D:\remotionshorts\renders\ancient_condom\assets');S=3;N=512
def canvas():return Image.new('RGBA',(N*S,N*S),(52,32,30,0))
def poly(d,pts,fill):d.polygon([(round(x*S),round(y*S)) for x,y in pts],fill=fill)
def line(d,pts,fill,width):d.line([(round(x*S),round(y*S)) for x,y in pts],fill=fill,width=round(width*S),joint='curve')
def ellipse(d,box,fill):d.ellipse(tuple(round(x*S) for x in box),fill=fill)
def crescent(im,mask):
 shifted=Image.new('L',mask.size,0);shifted.paste(mask,(18*S,-15*S));c=ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(2*S));a=np.array(im).astype(float);m=np.array(c)/255;a[:,:,:3]*=1-.15*m[:,:,None]*np.array([1,.70,.35]);return Image.fromarray(np.uint8(a))
ink='#422c29'
for who in ['male','female']:
 for pose in ['smile','shy','panic','horror','blink']:
  im=canvas();d=ImageDraw.Draw(im);outer=[];inner=[]
  for j in range(256):
   a=j*math.tau/256;r=1+.018*math.sin(2*a+.7)+.010*math.sin(5*a-1);pressure=8.3+2.1*math.sin(a-2.1)
   outer.append((256+(222*r+pressure)*math.cos(a),282+(207*r+pressure)*math.sin(a)));inner.append((256+(222*r-pressure)*math.cos(a),282+(207*r-pressure)*math.sin(a)))
  poly(d,outer,ink);poly(d,inner,'#fff2d4');mask=Image.new('L',im.size,0);poly(ImageDraw.Draw(mask),inner,255);im=crescent(im,mask);d=ImageDraw.Draw(im)
  # One flat fitted hair silhouette with irregular fringe and a painted topknot.
  ellipse(d,(214,12,301,93),ink);ellipse(d,(223,20,292,80),'#67432f');line(d,[(183,53),(322,55)],'#b8944f',7)
  hair=[(36,259),(28,213),(49,156),(84,113),(145,84),(216,70),(278,79),(341,74),(401,105),(451,153),(474,209),(466,252),(437,216),(402,175),(379,194),(351,164),(326,184),(295,157),(257,174),(218,159),(178,182),(135,175),(98,211),(64,227)]
  poly(d,hair,ink);poly(d,[(x+(3 if x<256 else -3),y+5) for x,y in hair],'#664630')
  line(d,[(56,191),(99,141),(152,114),(207,105)],'#876347',10);line(d,[(246,101),(298,111),(338,108),(390,135)],'#79553a',8)
  look=7 if who=='male' and pose=='smile' else -7 if pose=='shy' else 0
  for x in [187,324]:
   if pose=='blink':line(d,[(x-17,280),(x+17,280)],ink,6)
   else:
    ellipse(d,(x-13+look,255,x+13+look,292),'#66442d');ellipse(d,(x-7+look,259,x-2+look,266),'#fff2d4')
   if pose in ['panic','horror']:line(d,[(x-23,242+(10 if x<256 else 0)),(x+23,242-(10 if x>256 else 0))],ink,6)
  if pose=='horror':ellipse(d,(224,331,285,406),ink);ellipse(d,(233,380,278,402),'#be7982')
  elif pose=='panic':
   d.rounded_rectangle(tuple(v*S for v in (204,342,310,383)),radius=12*S,fill='#f4ebd1',outline=ink,width=5*S)
   line(d,[(208,361),(306,361)],ink,2)
   for x in [226,246,266,286]:line(d,[(x,346),(x,379)],ink,2)
  else:
   points=[(209+j*3.8,349+17*math.sin(j/24*math.pi)) for j in range(25)];line(d,points,ink,6)
  if pose=='shy':
   ellipse(d,(131,312,177,330),(226,155,140,150));ellipse(d,(337,312,383,330),(226,155,140,150))
  im.resize((1024,1024),Image.Resampling.LANCZOS).save(ART/f'cel_{who}_{pose}.png')
 # Single torso silhouette: flat wrap-front Hanfu, patterned hem, clipped cool crescent.
 im=canvas();d=ImageDraw.Draw(im);shape=[(153,40),(349,40),(409,150),(440,394),(403,464),(130,469),(75,398),(98,156)];poly(d,shape,ink)
 inside=[(158,49),(343,49),(399,155),(429,391),(397,452),(136,457),(87,395),(108,160)];colour='#278f87' if who=='female' else '#5167a1';poly(d,inside,colour);mask=Image.new('L',im.size,0);poly(ImageDraw.Draw(mask),inside,255);im=crescent(im,mask);d=ImageDraw.Draw(im)
 poly(d,[(191,45),(320,45),(258,117)],'#f9e7c4');poly(d,[(143,57),(165,51),(285,184),(272,205)],'#d6b878');poly(d,[(341,56),(361,63),(211,228),(196,211)],'#d6b878')
 poly(d,[(117,253),(405,253),(409,279),(113,279)],'#cfb174');line(d,[(123,258),(402,258)],'#7d633f',3)
 for x in [146,208,270,332,394]:
  line(d,[(x-9,408),(x,398),(x+9,409),(x,420),(x-9,408)],'#a6c6aa' if who=='female' else '#aab8d5',3)
 line(d,[(121,438),(399,436)],'#d2ba83',4)
 im.resize((1024,1024),Image.Resampling.LANCZOS).save(ART/f'cel_{who}_body.png')
print('Flat outlined Hanfu cast painted: two wardrobes, five expressions each.')
