"""Artwork and syllable envelope for the alternate washroom ending."""
from assets import ART, OUT, N, INK, CLEAR, canvas
from PIL import Image, ImageDraw, ImageFont
import array,json,math,wave

LABELS=[
 ('SHUDDH HINDI SHOCK: SYSTEM TREMOR','#80daff'),
 ('PRESSURE REVERSED: SUPERPOWER AWAKENED!','#ffcd67'),
 ('SIGMA WASHROOM GRINDSET: ACTIVATED','#6bf5ee'),
 ('WORK HARD IN SILENCE. HOLD IT HARDER.','#fff5b7'),
 ('ASCENDED TO ANOTHER DIMENSION','#fdd583'),
]
FONT='C:/Windows/Fonts/arialbd.ttf'
def badge(text,accent,path):
 im=Image.new('RGBA',(1080,1920),CLEAR)
 d=ImageDraw.Draw(im);center=540;half=394;y=91;h=122
 d.rounded_rectangle((center-half,y,center+half,y+h),radius=43,fill='#172337',outline=accent,width=5)
 for size in range(40,14,-1):
  font=ImageFont.truetype(FONT,size)
  if d.textlength(text,font=font)<=2*half-58:break
 d.text((center,y+h/2),text,font=font,anchor='mm',fill='#fff7e8')
 im.save(path)
def expression(style,level,path):
 im=canvas();d=ImageDraw.Draw(im)
 for side in (-1,1):
  x=512+side*125
  rx=37;ry=45 if style=='proud' else 34
  d.ellipse((x-rx,515-ry,x+rx,515+ry),fill=INK)
  if style=='power':
   d.ellipse((x-23,498,x+23,534),fill='#60f8ff')
   d.ellipse((x-10,505,x+10,525),fill='#edfff8')
  if style=='proud':d.line((x-43,422+side*9,x+43,421-side*9),fill=INK,width=20)
  else:d.line((x-64,423+side*24,x+61,423-side*25),fill=INK,width=27)
 if style=='speak':
  half=36+level*12
  d.ellipse((410,626-half,614,626+half),fill=INK)
  if level>=2:
   d.rounded_rectangle((433,637,591,626+half-11),radius=24,fill='#d65d69')
 elif style=='focus':
  d.line((453,641,567,641),fill=INK,width=18)
 else:d.arc((427,580,602,677),8,164,fill=INK,width=23)
 im.save(path)
def pop_art(path):
 im=canvas();d=ImageDraw.Draw(im)
 d.text((512,505),'POP!',font=ImageFont.truetype(FONT,345),anchor='mm',fill='#fff9d9',stroke_width=15,stroke_fill='#9b5528')
 im.save(path)
def envelope():
 with wave.open(str(OUT/'alt_narration.wav'),'rb') as sound:
  c,rate=sound.getnchannels(),sound.getframerate()
  samples=array.array('h',sound.readframes(sound.getnframes()))
 data=[]
 for f in range(675):
  block=samples[int(f*rate/30)*c:int((f+1)*rate/30)*c]
  rms=math.sqrt(sum((x/32768)**2 for x in block)/max(1,len(block)))
  data.append(round(max(0,min(4,(rms-.018)*22))))
 (ART/'alt_envelope.json').write_text(json.dumps(data))
if __name__=='__main__':
 for i,(title,accent) in enumerate(LABELS):badge(title,accent,ART/f'alt_hud_{i}.png')
 for style in ('focus','power','proud','speak'):
  for level in range(5 if style=='speak' else 1):expression(style,level,ART/f'alt_face_{style}_{level}.png')
 pop_art(ART/'alt_pop.png')
 envelope()
