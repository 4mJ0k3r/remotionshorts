from PIL import Image,ImageDraw,ImageFilter,ImageChops
from pathlib import Path
import math
P=Path('renders/slow_eddie/art');P.mkdir(exist_ok=True)
INK='#352329'
def curve(d,pts,width=20):
 a,b,c=pts;path=[]
 for i in range(41):
  t=i/40;path.append(((1-t)**2*a[0]+2*(1-t)*t*b[0]+t*t*c[0],(1-t)**2*a[1]+2*(1-t)*t*b[1]+t*t*c[1]))
 d.line(path,fill=INK,width=width,joint='curve')

for who in ['challenger','eddie']:
 e=who=='eddie'; im=Image.new('RGBA',(1024,1024),(53,35,41,0));d=ImageDraw.Draw(im)
 pts=[];ins=[]
 for i in range(256):
  a=i*math.tau/256;r=1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9);w=12*(1+.4*math.cos(a-2.35))
  pts.append((512+(350*r+w)*math.cos(a),540+(350*r+w)*math.sin(a)));ins.append((512+(350*r-w)*math.cos(a),540+(350*r-w)*math.sin(a)))
 d.polygon(pts,fill=INK);d.polygon(ins,fill='#fdfaf2')
 mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(ins,fill=255);shift=Image.new('L',im.size);shift.paste(mask,(50,-30));cres=ImageChops.subtract(mask,shift).filter(ImageFilter.GaussianBlur(8));shade=Image.new('RGBA',im.size,'#8796ac');shade.putalpha(cres.point(lambda x:int(x*.15)));im=Image.alpha_composite(im,shade);d=ImageDraw.Draw(im)
 for x in [390,625]:
  d.ellipse((x-29,470,x+29,542),fill=INK)
  if e:d.rectangle((x-40,465,x+40,509),fill='#fdfaf2');d.line((x-45,506,x+45,506),fill=INK,width=12)
  d.line((x-65,422+(0 if e else -15),x+53,422+(0 if e else 17)),fill=INK,width=18)
 if e:
  d.ellipse((440,633,534,680),fill=INK);d.polygon([(510,604),(460,600),(413,635),(385,671),(452,669),(510,637),(565,669),(634,673),(594,628),(552,603)],fill='#513b31')
 else:
  d.rounded_rectangle((411,620,603,705),30,fill=INK);d.rounded_rectangle((426,635,588,687),14,fill='#fdfaf2');d.line((426,662,588,662),fill=INK,width=5)
  for x in [460,502,544]:d.line((x,636,x,686),fill=INK,width=5)
 hat='#bc9665' if e else '#24232a';d.rounded_rectangle((318,130,711,356),35,fill=INK);d.rounded_rectangle((335,145,694,340),25,fill=hat);d.rectangle((335,302,694,342),fill='#765637' if e else '#39333a');d.polygon([(143,336),(346,348),(710,335),(866,316),(875,354),(703,381),(315,389),(140,368)],fill=INK);d.line((160,349,350,369,707,357,855,336),fill=hat,width=16)
 im.save(P/f'{who}_head.png')
 # Body plus curved anatomical limbs; pixel anchors head(512,265), grip(795,560), soles y980.
 im=Image.new('RGBA',(1024,1024),(53,35,41,0));d=ImageDraw.Draw(im)
 # feet / legs smooth and curved
 for pts in [[(455,672),(444,800),(402,970)],[(555,672),(590,825),(598,970)]]:
  curve(d,pts);d.ellipse((pts[-1][0]-27,958,pts[-1][0]+25,981),fill=INK)
 d.rounded_rectangle((490,320,544,405),12,fill='#fdfaf2',outline=INK,width=9)
 d.rounded_rectangle((391,379,628,689),68,fill=INK);d.rounded_rectangle((405,390,614,674),59,fill='#24a99e' if e else '#b32c3f')
 if not e:
  for x in range(423,607,26):d.line((x,401,x,650),fill='#e17a79',width=8)
 else:
  d.polygon([(410,390),(467,396),(478,656),(411,671)],fill='#92643d');d.polygon([(555,395),(607,390),(607,670),(548,655)],fill='#92643d')
 # cool crescent shirt
 d.arc((405,390,614,674),80,265,fill='#4e7278' if e else '#893449',width=15)
 d.rounded_rectangle((396,652,622,699),12,fill='#54372a',outline=INK,width=8);d.ellipse((489,656,535,694),fill='#d9b75a',outline=INK,width=6)
 # limbs painted outside torso; challenger arm aiming right
 if e:
  for pts in [[(411,420),(355,525),(367,650)],[(607,420),(672,535),(649,653)]]:curve(d,pts,19);d.ellipse((pts[-1][0]-16,pts[-1][1]-18,pts[-1][0]+16,pts[-1][1]+18),fill='#fdfaf2',outline=INK,width=6)
 else:
  curve(d,[(413,424),(310,538),(417,620)]);d.ellipse((401,604,437,638),fill='#fdfaf2',outline=INK,width=6)
  curve(d,[(608,430),(682,520),(795,470)],21);d.ellipse((777,450,817,492),fill='#fdfaf2',outline=INK,width=7)
 d.polygon([(613,660),(664,656),(657,779),(625,796),(603,768)],fill='#302830',outline=INK)
 im.save(P/f'{who}_body.png')
