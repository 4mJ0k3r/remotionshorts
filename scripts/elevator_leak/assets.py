"""Supersampled cream-head cast, story HUDs and real Hindi audio data."""
from pathlib import Path
import importlib.util
import json
import math
import subprocess
import wave

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/elevator_leak'
ART=OUT/'assets'
INK='#331c12'
SOURCE=Path('C:/Users/lavis/Downloads/ElevenLabs_2026-11-13T17_15_16_Viraj - Rich, Confident and Expressive_pvc_s30_sim75_v4.mp3')
spec=importlib.util.spec_from_file_location('presenter_art',ROOT/'scripts/inside_brain_dog/assets.py')
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

CAST={'employee':('#3d2210','#343a40','#3976c7'),'boss':('#ced4da','#eae4dc','#ae9677'),'baby':('#67401d','#facc15','#f6ce40'),'commuter1':('#492b25','#8e304e','#b87882'),'commuter2':('#1e1820','#26436d','#6082ac'),'commuter3':('#7c4a26','#dcbb82','#fff2d1')}
HUD=[
 'CROWDED ELEVATOR: SYSTEM FAILURE','NOT JUST A FART: CODE BROWN!',
 'DESTINATION: 90 FLOORS TO GO','SURVIVAL PROTOCOL: WHAT DO YOU DO?',
 'STEP 1: ACT 100% NORMAL','REALITY CHECK: THE SMELL IS LETHAL',
 'STEP 2: BLAME THE INNOCENT BABY','PLOT TWIST: BABY EQUIPS GAS MASK!',
 'STEP 3: CLAMP REAR & HUG THE WALL','GRAVITY WINS: PAYLOAD ESCAPED!',
 "CRITICAL HIT: RIGHT BY BOSS'S SHOE!","STEP 4: CLAIM IT'S JUST CHOCOLATE",
 "BOSS'S ORDER: EAT IT TO PROVE IT!",'STEP 5: SLAM THE EMERGENCY BUTTON!',
 'ELEVATOR STALLED: EVERYONE TRAPPED','FINAL BOSS INSPECTION...',
 'PLOT TWIST: BOSS DROPS ONE TOO!','DOUBLE SYSTEM LEAK CONFIRMED!']


def head(who,hair):
    base.ART=ART
    base.head()
    image=Image.open(ART/'head.png').convert('RGBA')
    pixels=np.array(image)
    dark=(pixels[:,:,0]==69)&(pixels[:,:,1]==35)&(pixels[:,:,2]==14)
    pixels[dark,:3]=tuple(bytes.fromhex(hair[1:]))
    image=Image.fromarray(pixels)
    draw=ImageDraw.Draw(image)
    if who=='boss':
        pixels=np.array(image)
        for original,replacement in [((156,88,34),(146,159,168)),((112,64,29),(159,169,179))]:
            selected=np.all(pixels[:,:,:3]==original,axis=2)
            pixels[selected,:3]=replacement
        image=Image.fromarray(pixels)
        draw=ImageDraw.Draw(image)
        draw.line([(198,389),(313,283),(467,229),(621,246),(768,346)],fill='#f0ece4',width=14,joint='curve')
        draw.line([(216,412),(331,319),(487,272),(644,290)],fill='#929fa8',width=10,joint='curve')
    if who=='baby':
        image=Image.new('RGBA',(1024,1024),base.CLEAR)
        draw=ImageDraw.Draw(image)
        outer,inner=[],[]
        for index in range(300):
            angle=index*math.tau/300
            radius=366*(1+.022*math.sin(2*angle+.6)-.015*math.cos(3*angle-.8)+.008*math.sin(5*angle+1.9))
            for points,offset in [(outer,10),(inner,-10)]:
                points.append((512+(radius+offset)*math.cos(angle),535+(radius+offset)*math.sin(angle)))
        draw.polygon(outer,fill=INK)
        draw.polygon(inner,fill='#fdfaf2')
        mask=Image.new('L',image.size)
        ImageDraw.Draw(mask).polygon(inner,fill=255)
        image=base.crescent(image,mask,(58,-40))
        ImageDraw.Draw(image).polygon([(460,201),(481,137),(521,164),(551,126),(577,200)],fill=hair,outline=INK,width=14)
    pixels=np.array(image)
    cream=(pixels[:,:,0]>190)&(pixels[:,:,1]>190)&(pixels[:,:,2]>180)&(pixels[:,:,3]>0)
    pixels[cream,:3]=np.minimum(255,pixels[cream,:3].astype('uint16')+np.array([2,1,2])).astype('uint8')
    image=Image.fromarray(pixels)
    image.save(ART/f'{who}_head.png')
    if who=='baby':
        image.save(ART/'baby_head_masked.png')
    rear=image.copy()
    rear_draw=ImageDraw.Draw(rear)
    rear_draw.ellipse((155,180,865,892),fill=INK)
    rear_draw.ellipse((173,198,847,874),fill=hair)
    rear_draw.arc((231,234,790,792),185,310,fill='#929fa8' if who=='boss' else '#9c5822',width=12)
    rear.save(ART/f'{who}_back.png')


def body(who,color,tie):
    image=Image.new('RGBA',(1024,1024),base.CLEAR)
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((197,45,827,978),radius=171,fill=INK)
    draw.rounded_rectangle((214,62,810,961),radius=155,fill=color)
    mask=Image.new('L',image.size)
    ImageDraw.Draw(mask).rounded_rectangle((214,62,810,961),radius=155,fill=255)
    image=base.crescent(image,mask,(45,-30))
    draw=ImageDraw.Draw(image)
    if who!='baby':
        draw.polygon([(370,74),(654,74),(516,472)],fill='#fdfaf2')
        draw.polygon([(360,80),(489,421),(347,290),(386,256),(315,190)],fill='#6a7075' if who=='employee' else '#c7bdaf')
        draw.polygon([(664,80),(540,421),(679,290),(639,256),(708,190)],fill='#565d64' if who=='employee' else '#d2c7b9')
        draw.polygon([(512,152),(551,199),(529,244),(554,492),(512,550),(472,492),(496,244),(476,199)],fill=tie,outline=INK,width=8)
        if who=='employee':
            for y in range(275,465,39):
                draw.line((492,y,539,y+18),fill='#a1c8ed',width=8)
        draw.line((606,490,731,490),fill=INK,width=9)
        draw.ellipse((506,619,521,634),fill=INK)
        draw.ellipse((506,728,521,743),fill=INK)
    if who=='commuter3':
        stripes=Image.new('RGBA',image.size,(0,0,0,0))
        stripe_draw=ImageDraw.Draw(stripes)
        for y in range(350,920,70):
            stripe_draw.line((230,y,794,y),fill='#775842',width=17)
        stripes.putalpha(ImageChops.multiply(stripes.getchannel('A'),mask))
        image=Image.alpha_composite(image,stripes)
    image.save(ART/f'{who}_body.png')
    back=Image.new('RGBA',(1024,1024),base.CLEAR)
    back_draw=ImageDraw.Draw(back)
    back_draw.rounded_rectangle((197,45,827,978),radius=171,fill=INK)
    back_draw.rounded_rectangle((214,62,810,961),radius=155,fill=color)
    back_draw.line((512,190,512,913),fill='#242c33' if who=='employee' else '#c5b9a9',width=8)
    back.save(ART/f'{who}_body_back.png')


def faces():
    for style in ['panic','angry','innocent','laugh','horror','baby','blink','whistle_up']:
        for amount in range(5):
            image=Image.new('RGBA',(1024,1024),base.CLEAR)
            draw=ImageDraw.Draw(image)
            for sign in [-1,1]:
                x,y=512+sign*124,535
                if style=='blink':
                    draw.line((x-36,y,x+36,y),fill='#1c1417',width=12)
                else:
                    draw.ellipse((x-34,y-46,x+34,y+46),fill='#1c1417')
                tilt=-sign*(24 if style=='angry' else -20 if style in ['panic','horror'] else 0)
                draw.line((x-49,419-tilt,x+49,419+tilt),fill=INK,width=20)
            if style=='horror':
                draw.ellipse((434,592,590,765),fill=INK)
            elif amount:
                h=17+amount*15
                draw.ellipse((443,666-h,581,666+h),fill='#28151b')
                if amount>2:draw.ellipse((477,677,551,666+h-5),fill='#d8667b')
            elif style=='panic':
                draw.rounded_rectangle((431,610,593,697),radius=25,fill=INK)
                draw.rounded_rectangle((444,623,580,684),radius=12,fill='#fdfaf2')
                for x in range(461,580,27):draw.line((x,625,x,682),fill=INK,width=7)
                draw.line((444,653,580,653),fill=INK,width=6)
            elif style in ['innocent','whistle_up']:
                draw.ellipse((491,643,532,678),fill=INK)
            elif style in ['laugh','baby']:
                draw.arc((438,611,588,706),0,170,fill=INK,width=17)
            else:
                draw.line((463,670,560,667),fill=INK,width=15)
            if style=='whistle_up':
                shifted=Image.new('RGBA',image.size,base.CLEAR)
                shifted.paste(image,(0,-65))
                image=shifted
            image.save(ART/f'face_{style}_{amount}.png')


def plaque(name,text,color,size=(1024,360)):
    image=Image.new('RGBA',size,'#f6f1df')
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((5,5,size[0]-6,size[1]-6),radius=15,outline=color,width=16)
    rows=text.split('\n')
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',58)
    for i,row in enumerate(rows):
        draw.text((size[0]/2,(i+.5)*size[1]/len(rows)),row,font=font,fill=color,anchor='mm')
    image.save(ART/name)


def make():
    ART.mkdir(parents=True,exist_ok=True)
    for who,(hair,color,tie) in CAST.items():
        head(who,hair)
        body(who,color,tie)
    faces()
    notes=Image.new('RGBA',(256,384),base.CLEAR)
    note_font=ImageFont.truetype('C:/Windows/Fonts/seguisym.ttf',270)
    ImageDraw.Draw(notes).text((128,192),'♪',font=note_font,fill='#e7bc58',stroke_width=3,stroke_fill=INK,anchor='mm')
    notes.save(ART/'whistle_note.png')
    for i,text in enumerate(HUD):
        image=Image.new('RGBA',(1080,1920),(0,0,0,0))
        draw=ImageDraw.Draw(image)
        font_size=32
        font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',font_size)
        while draw.textlength(text,font=font)>960:
            font_size-=1
            font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',font_size)
        width=int(draw.textlength(text,font=font))+58
        left=(1080-width)//2
        draw.rounded_rectangle((left,134,left+width,224),radius=29,fill='#0d1826',outline='#d4a359',width=4)
        draw.text((540,179),text,font=font,fill='white',anchor='mm')
        image.save(ART/f'hud_{i}.png')
    plaque('safety.png','SAFETY FIRST\nDAYS WITHOUT ACCIDENT: 0','#1b6542')
    plaque('capacity.png','CAPACITY: MAX 8 PERSONS\n0 FARTS','#ae2626')
    plaque('advert.png','YOUR AD HERE\nDM ME','#8c5618')
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(SOURCE),'-af','apad','-t','71.5','-ar','48000','-ac','1',str(OUT/'narration.wav')],check=True)
    with wave.open(str(OUT/'narration.wav')) as sound:
        samples=np.frombuffer(sound.readframes(sound.getnframes()),dtype='<i2').astype(float)/32768
    rms=np.sqrt(np.mean(samples[:2145*1600].reshape(2145,1600)**2,axis=1))
    normalized=np.clip((rms-.007)/max(.01,np.percentile(rms,92)-.007),0,1)
    envelope=[]
    prior=0
    for value in normalized:
        prior=.25*prior+.75*float(value)
        envelope.append(round(prior*4))
    (ART/'envelope.json').write_text(json.dumps(envelope))
    gas=Image.new('RGBA',(512,768),(44,70,22,0))
    yy,xx=np.mgrid[:768,:512]
    center=256+58*np.sin(yy/95)
    alpha=np.exp(-((xx-center)/(75+yy*.10))**2)*np.sin(np.pi*yy/768)**2*65
    pixels=np.array(gas)
    pixels[:,:,:3]=[137,181,64]
    pixels[:,:,3]=alpha.astype('uint8')
    Image.fromarray(pixels).save(ART/'gas.png')
    pixels[:,:,:3]=[198,193,173]
    pixels[:,:,3]=(alpha*.55).astype('uint8')
    Image.fromarray(pixels).save(ART/'heat.png')
    # Shared fixed vignette asset, scaled by the compositor at review size.
    base.ART=ART
    base.overlays()
    # base.overlays writes three presenter HUDs, restore the elevator captions.
    for i in range(3):
        text=HUD[i]
        image=Image.new('RGBA',(1080,1920),(0,0,0,0))
        draw=ImageDraw.Draw(image)
        font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',31)
        width=int(draw.textlength(text,font=font))+58
        left=(1080-width)//2
        draw.rounded_rectangle((left,134,left+width,224),radius=29,fill='#0d1826',outline='#d4a359',width=4)
        draw.text((540,179),text,font=font,fill='white',anchor='mm')
        image.save(ART/f'hud_{i}.png')
    print('Elevator cast, 18 HUDs, wall plaques and 2145 audio samples ready.')


if __name__=='__main__':
    make()
