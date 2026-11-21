"""Stable hand-inked cel artwork and composited ASCII screen graphics."""
from pathlib import Path
import json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');ART=OUT/'assets'
W,H=1024,1536
INK='#161219'
FONT=r'C:\Windows\Fonts\arialbd.ttf'

def stroke(d,points,width=17,fill=INK):
    d.line(points,fill=fill,width=width,joint='curve')
    for x,y in (points[0],points[-1]):d.ellipse((x-width/2,y-width/2,x+width/2,y+width/2),fill=fill)

def shaded(mask,color):
    rgb=np.array(tuple(bytes.fromhex(color)),dtype=float)
    yy,xx=np.mgrid[:H,:W];grad=np.clip(1.02-.12*(1-xx/W)-.07*yy/H,.76,1.02)
    data=np.zeros((H,W,4),dtype=np.uint8);data[:,:,:3]=(rgb[None,None,:]*grad[:,:,None]).clip(0,255).astype(np.uint8);data[:,:,3]=np.array(mask)
    im=Image.fromarray(data)
    shifted=Image.new('L',(W,H));shifted.paste(mask,(22,-18))
    crescent=ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(9));crescent=ImageChops.multiply(crescent,mask)
    blue=Image.new('RGBA',(W,H),(66,88,118,0));blue.putalpha(crescent.point(lambda p:int(p*.15)))
    return Image.alpha_composite(im,blue)

def body(who,pose):
    im=Image.new('RGBA',(W,H),(22,18,25,0));d=ImageDraw.Draw(im)
    left,right=(376,850),(648,850)
    hands={'inspect':((290,1050),(847,650)),'pluck':((290,1050),(850,770)),'spray':((245,920),(815,1035)),'launch':((260,1060),(865,740)),'shocked':((270,730),(765,730)),'celebrate':((200,560),(825,560)),'wave':((250,630),(805,1110)),'carry':((260,1020),(820,940)),'back':((285,1060),(810,1060))}
    lh,rh=hands[pose]
    if who=='victim' and pose=='carry':
        stroke(d,[(440,1170),(340,1290),(210,1250)],25);stroke(d,[(570,1170),(620,1290),(760,1290)],25)
    else:
        stroke(d,[(444,1170),(405,1310),(380,1440)],25);stroke(d,[(578,1170),(615,1310),(650,1440)],25)
        stroke(d,[(350,1440),(400,1440)],26);stroke(d,[(625,1440),(680,1440)],26)
    stroke(d,[left,(285,930) if lh[1]>800 else (240,780),lh],25)
    stroke(d,[right,(760,990) if rh[1]>850 else (810,790),rh],25)
    for h in (lh,rh):d.ellipse((h[0]-24,h[1]-24,h[0]+24,h[1]+24),fill=INK)
    mask=Image.new('L',(W,H));md=ImageDraw.Draw(mask)
    md.rounded_rectangle((370,770,654,1202),radius=115,fill=255)
    md.rounded_rectangle((467,650,558,835),radius=26,fill=255)
    color={'scientist':'f2f6fa','victim':'6e4e32','firefighter':'29323c'}[who]
    outer=Image.new('RGBA',(W,H),INK);outer.putalpha(mask);im=Image.alpha_composite(im,outer)
    inside=mask.filter(ImageFilter.MinFilter(25));im=Image.alpha_composite(im,shaded(inside,color));d=ImageDraw.Draw(im)
    if who=='scientist':
        d.polygon([(450,785),(512,850),(574,785)],fill='#0d9488');stroke(d,[(512,860),(512,1170)],6,fill='#8dabb9')
        d.line([(430,825),(475,930),(512,870),(548,930),(595,825)],fill='#758b99',width=7)
        d.rounded_rectangle((555,970,622,1040),radius=10,outline='#9eb0bc',width=6)
        for y in (1000,1095):d.ellipse((492,y,502,y+10),fill=INK)
    if who=='victim':d.polygon([(440,793),(510,920),(585,792),(543,860),(510,970),(475,860)],fill='#b99b76')
    if who=='firefighter':
        for y in (965,1080):d.rectangle((385,y,638,y+30),fill='#eaff00')
        d.rectangle((501,790,523,1180),fill='#f4b83d')
    im.save(ART/f'{who}_body_{pose}.png')
    return {'left':lh,'right':rh}

def head(who,expression):
    im=Image.new('RGBA',(W,H),(22,18,25,0));d=ImageDraw.Draw(im)
    outer=[];inner=[]
    for i in range(256):
        a=2*math.pi*i/256;r=195*(1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9));w=17*(1+.25*math.cos(a-2.35))
        outer.append((512+(r+w/2)*math.cos(a),465+(r+w/2)*math.sin(a)))
        inner.append((512+(r-w/2)*math.cos(a),465+(r-w/2)*math.sin(a)))
    d.polygon(outer,fill=INK);mask=Image.new('L',(W,H));ImageDraw.Draw(mask).polygon(inner,fill=255)
    im=Image.alpha_composite(im,shaded(mask,'fdfaf2'));d=ImageDraw.Draw(im)
    if expression!='back':
        eye_y=443
        if expression=='blink':
            for x in (450,575):stroke(d,[(x-16,eye_y),(x+16,eye_y)],10)
        else:
            for x in (450,575):
                top=eye_y-31 if expression not in ('smirk','happy') else eye_y-18
                d.ellipse((x-17,eye_y-31,x+17,eye_y+31),fill=INK)
                # horizontal eyelid mask clips ONLY pupils.
                if top>eye_y-31:
                    crop=shaded(mask,'fdfaf2');im.paste(crop.crop((x-20,eye_y-34,x+20,top)),(x-20,eye_y-34));d=ImageDraw.Draw(im)
        brow=-16 if expression=='surprise' else 0
        stroke(d,[(423,391+brow),(474,397+brow)],12);stroke(d,[(550,397+brow),(600,389+brow)],12)
        if expression=='surprise':d.ellipse((483,518,540,590),fill=INK)
        elif expression=='worried':stroke(d,[(480,557),(512,542),(548,557)],12)
        else:
            d.arc((467,493,561,579),0,165,fill=INK,width=13)
        if who in ('scientist','victim'):
            for x in (450,575):
                if who=='scientist':d.ellipse((x-49,eye_y-52,x+49,eye_y+52),outline=INK,width=7)
                else:d.rounded_rectangle((x-49,eye_y-48,x+49,eye_y+48),radius=10,outline=INK,width=7)
            stroke(d,[(500,eye_y-4),(524,eye_y-4)],6)
            stroke(d,[(350,eye_y-20),(398,eye_y-10)],7);stroke(d,[(626,eye_y-10),(675,eye_y-20)],7)
    if who=='scientist':
        for x in (455,500,543):d.arc((x,239,x+65,330),180,310,fill=INK,width=13)
    elif who=='victim':
        for x,sgn in ((319,-1),(704,1)):
            d.polygon([(x,425),(x+sgn*45,382),(x+sgn*36,449),(x+sgn*50,474),(x,482)],fill='#e5e6de',outline=INK,width=7)
    else:
        d.pieslice((310,246,712,479),180,360,fill='#242b32',outline=INK,width=13)
        d.rounded_rectangle((290,346,735,387),radius=15,fill='#edca31',outline=INK,width=10)
        d.polygon([(481,270),(543,270),(559,349),(464,349)],fill='#eaff00')
        d.rounded_rectangle((489,291,534,335),radius=8,fill='#cf4629')
    im.save(ART/f'{who}_head_{expression}.png')

def pill(d,box,text,small=False,accent='#6ee7d2'):
    font_size=25 if small else 30
    f=ImageFont.truetype(FONT,font_size)
    while d.textbbox((0,0),text,font=f)[2]>box[2]-box[0]-50:
        font_size-=1;f=ImageFont.truetype(FONT,font_size)
    d.rounded_rectangle(box,radius=24,fill='#102431',outline=accent,width=2)
    d.text(((box[0]+box[2])/2,(box[1]+box[3])/2),text,font=f,fill='#f3faf6',anchor='mm')

def hud(index,title,tag):
    im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
    pill(d,(56,70,1024,160),title)
    d.text((62,186),f'FIELD NOTES   /   {index}   /   BIO-SENSOR',font=ImageFont.truetype(FONT,22),fill='#d6f5f2')
    if tag:pill(d,(95,1570,985,1650),tag,True)
    if index=='4C':
        pill(d,(75,267,1005,388),'CAREER UNLOCKED: LIFESAVER',accent='#f8c855')
    im.save(ART/f'hud_{index}.png')

def monitor(mode):
    im=Image.new('RGBA',(1024,640),'#0a202a');d=ImageDraw.Draw(im)
    for x in range(0,1024,40):d.line((x,65,x,640),fill='#173e46',width=2)
    for y in range(65,640,40):d.line((0,y,1024,y),fill='#173e46',width=2)
    f=ImageFont.truetype(FONT,30);d.text((40,22),'OLFACTORY NAVIGATION  /  LIVE',font=f,fill='#72f6cf')
    if mode=='wave':
        pts=[]
        for x in range(45,985,3):
            pulse=sum(150*math.exp(-((x-p)/16)**2)-65*math.exp(-((x-p-25)/19)**2) for p in (230,510,800))
            pts.append((x,340-pulse-12*math.sin(x*.07)))
        stroke(d,pts,5,'#63ffc0');d.text((50,550),'HAIR: MATCH     LATENCY: 0.01 s',font=f,fill='#f5cc65')
    else:
        for x,y,r in [(510,340,90),(510,340,170),(510,340,250)]:d.ellipse((x-r,y-r,x+r,y+r),outline='#2a7d71',width=3)
        stroke(d,[(130,490),(300,490),(300,350),(510,350),(680,210),(845,210)],9,'#f1c45f')
        d.polygon([(815,177),(880,210),(815,243)],fill='#6ef2bb')
        d.ellipse((820,185,870,235),outline='#d2ffe7',width=4);d.text((50,550),'SCENT VECTOR: LOCKED     AUTO ROUTE',font=f,fill='#6dffcf')
    im.save(ART/f'monitor_{mode}.png')

if __name__=='__main__':
    ART.mkdir(exist_ok=True)
    sockets={}
    for who,poses in [('scientist',['inspect','pluck','spray','launch','shocked','celebrate','back']),('victim',['wave','carry']),('firefighter',['carry'])]:
        for pose in poses:sockets[f'{who}_{pose}']=body(who,pose)
        for exp in ('smirk','surprise','happy','worried','blink','back'):head(who,exp)
    captions=[('1A','CAN ONE CURLY HAIR SMELL?','TARGET LOCKED: CURL LEVEL 11/10'),('1B','THE MOST UNLIKELY EXPERIMENT','ONE HAIR. ONE BIG OPPORTUNITY.'),('1C','FROM HAIR TO HARDWARE','BIO-SENSOR PROTOTYPE / ONLINE'),('2A','A LITTLE PERFUME. A BIG REACTION.','SCENT INPUT / ACTIVE'),('2B','BIOLOGICAL SENSOR / INSTANT SIGNAL','HAIR: MATCH     MACHINES: WAITING'),('2C','TURNING SCENT INTO DIRECTIONS','LIVE SIGNAL > SCENT MAP'),('3A','NEXT STOP: AUTONOMOUS FLIGHT','MINI DRONE / SENSOR MOUNTED'),('3B','NO REMOTE. JUST FOLLOW THE SCENT.','AUTONOMOUS HOMING / ACTIVE'),('3C','IT FOUND THE OTHER CURLY HAIRS','TARGET LOCKED: 100% MATCH'),('4A','FROM LAB EXPERIMENT TO RESCUE','DISASTER ZONE / SCANNING'),('4B','A SIGNAL FROM UNDER THE RUBBLE','SURVIVOR DETECTED / ALIVE'),('4C','FROM ZERO TO HERO','LIFESAVER CERTIFIED')]
    for args in captions:hud(*args)
    for mode in ('wave','map'):monitor(mode)
    (ART/'sockets.json').write_text(json.dumps(sockets,indent=2))
    print('Created cel layers, stable expression variants, HUDs and monitor artwork.')
