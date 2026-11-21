from PIL import Image,ImageDraw,ImageFilter,ImageChops
from pathlib import Path
import math
P=Path('renders/slow_eddie_v5/art');INK='#352329';CREAM='#fdfaf2'
def bez(d,a,b,c,width=24,fill=INK):
 pts=[((1-t)**2*a[0]+2*(1-t)*t*b[0]+t*t*c[0],(1-t)**2*a[1]+2*(1-t)*t*b[1]+t*t*c[1]) for t in [i/60 for i in range(61)]];d.line(pts,fill=fill,width=width,joint='curve')
for who in ['challenger','eddie']:
 e=who=='eddie';im=Image.new('RGBA',(1024,1024),(53,35,41,0));d=ImageDraw.Draw(im)
 # Flat tapered limbs, supported sole endpoints and curved outward elbows.
 for a,b,c in [((450,678),(421,815),(402,972)),((565,678),(579,835),(598,972))]:bez(d,a,b,c,29);d.ellipse((c[0]-26,960,c[0]+28,983),fill=INK)
 d.rounded_rectangle((489,319,545,406),13,fill=CREAM,outline=INK,width=10)
 body=[(369,417),(390,381),(453,364),(509,378),(571,364),(636,385),(655,418),(631,625),(615,691),(409,691),(390,625)]
 d.polygon(body,fill='#259f98' if e else '#a72c39');d.line(body+[body[0]],fill=INK,width=14,joint='curve')
 if e:
  d.polygon([(390,387),(460,371),(489,395),(467,530),(459,655),(392,669),(405,536)],fill='#97633a',outline=INK,width=9)
  d.polygon([(566,372),(630,391),(614,529),(637,668),(568,652),(545,531),(538,398)],fill='#97633a',outline=INK,width=9)
  d.line([(458,383),(441,462),(465,480)],fill='#dbad70',width=9);d.line([(562,385),(583,465),(558,481)],fill='#dbad70',width=9)
 else:
  for x in range(403,626,25):d.line([(x,405),(x+2,631)],fill='#dd7373',width=9)
 d.rounded_rectangle((397,648,625,699),14,fill='#533325',outline=INK,width=9)
 d.rounded_rectangle((483,652,542,696),13,fill='#c79b3f',outline=INK,width=6);d.ellipse((492,659,534,690),outline='#ffe3a0',width=4);d.line((513,660,513,690),fill='#ffe3a0',width=4)
 if e:
  for a,b,c in [((376,418),(318,523),(352,654)),((647,418),(692,526),(663,654))]:bez(d,a,b,c,27);d.ellipse((c[0]-18,c[1]-20,c[0]+18,c[1]+20),fill=CREAM,outline=INK,width=7)
 else:
  bez(d,(376,418),(315,534),(369,641),27);d.ellipse((351,620,388,661),fill=CREAM,outline=INK,width=7)
  bez(d,(647,418),(710,526),(795,470),28);d.ellipse((775,448,819,494),fill=CREAM,outline=INK,width=7)
 im.save(P/f'{who}_body.png')
 head=Image.open('renders/slow_eddie_v3/art/eddie_head.png' if e else 'renders/slow_eddie/art/challenger_head.png').convert('RGBA');hd=ImageDraw.Draw(head)
 if e:
  for x in [390,625]:
   hd.rectangle((x-75,395,x+70,560),fill=CREAM);hd.arc((x-67,400,x+64,453),195,335,fill=INK,width=15);hd.ellipse((x-23,494,x+23,553),fill=INK);hd.rectangle((x-30,490,x+30,521),fill=CREAM);hd.arc((x-43,501,x+44,531),185,355,fill=INK,width=8);hd.ellipse((x-9,530,x-1,538),fill=CREAM)
 head.save(P/f'{who}_head.png');hd=ImageDraw.Draw(head)
 for x in [390,625]:hd.rectangle((x-48,477,x+48,560),fill=CREAM);hd.arc((x-40,510,x+40,535),0,180,fill=INK,width=10)
 head.save(P/f'{who}_blink.png')
