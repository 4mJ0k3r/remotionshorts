"""Packed raster cels, badge overlays, and dialogue envelope for the washroom short."""
from pathlib import Path
import math,json,wave,array
from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageFilter
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/washroom_experiment'
ART=OUT/'assets'
INK='#2c1d22'
CLEAR=(22,18,25,0)
N=1024
def canvas():return Image.new('RGBA',(N,N),CLEAR)
def head(name,hair,color,profile=False):
 im=canvas();d=ImageDraw.Draw(im);outer=[];inner=[]
 for i in range(240):
  a=i*math.tau/240
  r=360*(1+.023*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9))
  if profile:r+=48*math.exp(-((math.atan2(math.sin(a),math.cos(a))-.12)/.095)**2)
  w=24*(1+.41*math.cos(a-2.2)+.19*math.sin(3*a+1.1))
  for pts,x in [(outer,r+w/2),(inner,r-w/2)]:
   pts.append((512+x*math.cos(a),533+x*.92*math.sin(a)))
 d.polygon(outer,fill=INK);d.polygon(inner,fill=color)
 mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(inner,fill=255)
 sh=Image.new('L',im.size);sh.paste(mask,(65,-42))
 shade=ImageChops.subtract(mask,sh).filter(ImageFilter.GaussianBlur(11))
 shade=ImageChops.multiply(shade,mask).point(lambda x:int(x*.16))
 im=Image.composite(Image.new('RGBA',im.size,'#708db7'),im,shade)
 d=ImageDraw.Draw(im)
 if name=='beti':
  points=[]
  for j in range(42):
   a=math.pi+(j/41)*math.pi
   r=1.18 if j%2 else .94
   points.append((512+395*r*math.cos(a),492+337*r*math.sin(a)))
  points.extend([(793,410),(668,336),(611,405),(536,334),(462,390),(388,354),(254,451)])
  d.polygon(points,fill=hair,outline=INK,width=20)
  for i in range(7):d.arc((277+i*36,153-i%2*24,661+i*26,432),209,302,fill='#b365ff',width=11)
 else:
  pts=[(159,496),(174,390),(218,294),(301,226),(415,190),(531,188),(645,211),(753,270),(824,365),(860,464),(800,400),(742,411),(680,361),(600,381),(536,329),(474,360),(399,329),(327,396),(259,414),(207,483)]
  d.polygon(pts,fill=hair,outline=INK,width=20)
  if name=='hero':
   d.line([(225,338),(300,284),(400,246),(490,240),(561,249)],fill='#886757',width=12,joint='curve')
   d.line([(239,360),(300,315),(389,283)],fill='#755347',width=9,joint='curve')
  else:
   d.line([(216,342),(316,257),(468,225),(651,250),(783,337)],fill='#ff9a54',width=13,joint='curve')
 im.save(ART/f'{name}_{"profile" if profile else color[1:]}.png')
def face(style,amount):
 im=canvas();d=ImageDraw.Draw(im)
 for s in [-1,1]:
  if style=='profile' and s==-1:continue
  x=512+s*124;y=515
  if style=='profile':x=702
  if style=='dizzy':
   pts=[(x+i*.85*math.cos(i*.27),y+i*.85*math.sin(i*.27)) for i in range(45)]
   d.line(pts,fill=INK,width=12)
  else:
   r=51 if style in ('shock','scream') else 40
   h=59 if style in ('shock','scream') else 52
   if style=='confused' and s==1:h=15
   if style=='crossed':x-=s*56;r=30;h=43
   if style=='smug':
    m=Image.new('L',im.size);ImageDraw.Draw(m).ellipse((x-r,y-h,x+r,y+h),fill=255)
    clip=Image.new('L',im.size);ImageDraw.Draw(clip).rectangle((x-r,y-12,x+r,y+h),fill=255)
    im.paste(INK,(0,0,N,N),ImageChops.multiply(m,clip))
   else:d.ellipse((x-r,y-h,x+r,y+h),fill=INK)
  b=-s*(20 if style in ['panic','shock','dizzy','scream'] else -11)
  y=370 if style=='confused' and s==-1 else 416
  d.line((x-48,y-b,x+48,y-5+b),fill=INK,width=23)
 if style=='smug' and not amount:
  d.arc((455,574,592,664),15,164,fill=INK,width=22)
 elif style=='confused':
  d.line([(433,645),(466,622),(499,621),(536,645),(577,619)],fill=INK,width=20,joint='curve')
 elif (style=='panic' and not amount) or style=='crossed':
  wide=38 if style=='crossed' else 0
  d.rounded_rectangle((437-wide,600,587+wide,679),radius=26,fill=INK)
  d.rounded_rectangle((453-wide,614,572+wide,665),radius=12,fill='#fffaf0')
  for x in range(465-wide,565+wide,26):d.line((x,616,x,664),fill=INK,width=7)
  d.line((453-wide,638,572+wide,638),fill=INK,width=6)
 elif style=='profile':
  d.ellipse((708,581,808,673+amount*8),fill=INK)
  d.arc((717,610,796,654+amount*8),0,173,fill='#dc7581',width=13)
 elif style in ('shock','scream','dizzy','open') or amount:
  h={'shock':126,'scream':166,'dizzy':113,'open':154}.get(style,38)+amount*12
  w={'shock':64,'scream':123,'open':105}.get(style,70)
  d.ellipse((512-w,626-h/2,512+w,626+h/2),fill=INK)
  if style=='scream' or amount>=3:
   d.ellipse((478,632,550,626+h*.43),fill='#da6370')
 else:d.line((474,627,550,628),fill=INK,width=17)
 im.save(ART/f'face_{style}_{amount}.png')
def body(name,color,trim):
 im=canvas();d=ImageDraw.Draw(im)
 d.rounded_rectangle((139,32,885,965),radius=219,fill=INK)
 d.rounded_rectangle((172,64,852,934),radius=187,fill=color)
 d.rounded_rectangle((206,110,817,880),radius=163,outline=trim,width=15)
 if name in ('hero','licker'):
  d.polygon([(299,100),(727,100),(515,472)],fill='#fff6e3')
  d.polygon([(511,176),(558,229),(540,281),(565,528),(512,600),(464,529),(490,281),(471,230)],fill='#b3283f',outline=INK,width=14)
  d.line((285,658,392,657),fill=trim,width=19)
 else:
  d.arc((230,65,798,378),9,171,fill='#74a5ff',width=24)
 im.save(ART/f'{name}_torso.png')
def back(name,hair):
 im=canvas();d=ImageDraw.Draw(im)
 d.ellipse((141,194,883,871),fill=INK)
 d.ellipse((165,218,859,847),fill='#fffdf9')
 d.polygon([(165,516),(176,394),(218,306),(309,237),(423,216),(586,217),(734,250),(827,342),(858,475),(848,674),(784,739),(694,751),(658,798),(423,810),(381,756),(267,750),(193,662)],fill=hair)
 im.save(ART/f'{name}_back.png')
def badges():
 font='C:/Windows/Fonts/arialbd.ttf'
 labels=[('DUAL URGE: 99% CRITICAL','#ffca52'),('WASHROOM STALL #3: STRANGE SOUNDS','#61d7ff'),('INSIDE STALL #3: SHUDDH HINDI DUB','#df99ff'),('SYSTEM OVERLOAD: PRESSURE RELEASE!','#ff9d85'),('SHUDDH HINDI OVERLOAD','#ff7669')]
 for i,(txt,col) in enumerate(labels):
  im=Image.new('RGBA',(1080,1920),CLEAR);d=ImageDraw.Draw(im)
  w=657;x=(im.width-w)//2;y=91
  d.rounded_rectangle((x,y,x+w,y+122),radius=43,fill='#172337',outline=col,width=5)
  size=39
  f=ImageFont.truetype(font,size)
  while d.textlength(txt,font=f)>w-56:
   size-=1
   f=ImageFont.truetype(font,size)
  d.text((im.width//2,y+61),txt,font=f,anchor='mm',fill='#fff7e8')
  im.save(ART/f'hud_{i}.png')
 im=Image.new('RGBA',(1080,1920),CLEAR);d=ImageDraw.Draw(im)
 for x,txt,col in [(140,'PEE: 100%','#ffe671'),(940,'POOP: 100%','#ff9979')]:
  y=1120
  d.rounded_rectangle((x-121,y-43,x+121,y+43),radius=26,fill='#202541',outline=col,width=7)
  d.text((x,y),txt,font=ImageFont.truetype(font,31),anchor='mm',fill=col)
 im.save(ART/'warnings.png')
def envelope():
 with wave.open(str(OUT/'narration.wav'),'rb') as s:
  c=s.getnchannels();rate=s.getframerate();a=array.array('h',s.readframes(s.getnframes()))
 data=[]
 for f in range(1404):
  x=a[int(f*rate/30)*c:int((f+1)*rate/30)*c]
  rms=math.sqrt(sum((y/32768)**2 for y in x)/max(1,len(x)))
  data.append(round(max(0,min(4,(rms-.017)*25))))
 (ART/'envelope.json').write_text(json.dumps(data))
def effects():
 im=canvas();d=ImageDraw.Draw(im)
 d.polygon([(232,589),(234,405),(282,269),(384,184),(536,159),(669,181),(768,256),(808,383),(792,520),(734,655),(651,719),(510,739),(415,786),(398,850),(446,902),(324,884),(285,811),(304,724),(238,669)],fill=(236,251,255,202),outline=(131,207,242,240),width=23)
 for x in (394,619):
  d.line([(x+i*1.20*math.cos(i*.23),392+i*1.20*math.sin(i*.23)) for i in range(56)],fill='#2c1d22',width=15)
 d.ellipse((443,474,561,591),fill='#2c1d22')
 im.save(ART/'ghost.png')
 im=canvas();d=ImageDraw.Draw(im)
 f=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',800)
 d.text((N//2,N//2),'?',font=f,anchor='mm',fill='#ffe243',stroke_width=21,stroke_fill='#382e30')
 im.save(ART/'question.png')
 im=canvas();d=ImageDraw.Draw(im)
 for i in range(27):
  a=i*math.tau/27
  r=350+(i%5)*13
  d.line((512+r*math.cos(a),512+r*math.sin(a),512+600*math.cos(a),512+600*math.sin(a)),fill=(244,253,255,195),width=5+i%4*3)
 im.save(ART/'scream_lines.png')
if __name__=='__main__':
 ART.mkdir(parents=True,exist_ok=True)
 for who,hair,top,trim in [('hero','#443029','#60a5fa','#a4d1ff'),('beti','#9333ea','#2563eb','#73a1ff'),('licker','#ea580c','#9ca3af','#c9d2dc')]:
  for c in ('#fffdf9','#d8ecff','#ffd2cc') if who=='hero' else ('#fffdf9',):head(who,hair,c)
  body(who,top,trim)
 for s in ('panic','shock','smug','talk','scream','dizzy','confused','crossed','open','profile'):
  for a in range(5):face(s,a)
 head('hero','#443029','#fffdf9',profile=True)
 back('hero','#443029')
 back('licker','#ea580c')
 badges();effects();envelope()
