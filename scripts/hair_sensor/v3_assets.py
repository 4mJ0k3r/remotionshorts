"""V3 illustrated actors, soft FX and ONE top screen badge."""
from pathlib import Path
import math,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageChops
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');ART=OUT/'assets_v3';ART.mkdir(exist_ok=True)
INK='#211b21';FONT=r'C:\Windows\Fonts\arialbd.ttf'

def line(d,pts,w=9,fill=INK):
    d.line(pts,fill=fill,width=w,joint='curve')
    for x,y in (pts[0],pts[-1]):d.ellipse((x-w/2,y-w/2,x+w/2,y+w/2),fill=fill)

def paint(mask,h):
    yy,xx=np.mgrid[:512,:512];base=np.array(tuple(bytes.fromhex(h)))
    # Directional warm light from upper right, cool crescent on lower left.
    shade=np.clip(.83+.19*xx/512-.075*yy/512,.73,1.02)
    color=np.clip(base[None,None,:]*shade[:,:,None]+np.array([5,2,-3])[None,None,:]*(xx/512)[:,:,None],0,255)
    a=np.zeros((512,512,4),dtype=np.uint8);a[:,:,:3]=color.astype(np.uint8);a[:,:,3]=np.array(mask)
    im=Image.fromarray(a);shift=Image.new('L',mask.size);shift.paste(mask,(17,-12));cres=ImageChops.multiply(ImageChops.subtract(mask,shift).filter(ImageFilter.GaussianBlur(5)),mask)
    cool=Image.new('RGBA',mask.size,(61,84,112,0));cool.putalpha(cres.point(lambda x:int(x*.15)));return Image.alpha_composite(im,cool)

def head(who):
    im=Image.new('RGBA',(512,512),(33,27,33,0));d=ImageDraw.Draw(im);outer=[];inner=[]
    for i in range(256):
        a=math.tau*i/256;r=205*(1+.018*math.sin(2*a+.6)-.012*math.cos(3*a-.8)+.007*math.sin(5*a))
        outer.append((256+(r+5.5)*math.cos(a),276+(r+5.5)*math.sin(a)))
        inner.append((256+(r-5.5)*math.cos(a),276+(r-5.5)*math.sin(a)))
    d.polygon(outer,fill=INK);m=Image.new('L',im.size);ImageDraw.Draw(m).polygon(inner,fill=255);im=Image.alpha_composite(im,paint(m,'fdfaf2'));d=ImageDraw.Draw(im)
    if who=='scientist':
        pts=[(52,220),(53,160),(76,110),(119,72),(159,57),(213,39),(256,55),(303,43),(355,73),(406,110),(445,156),(461,223),(427,193),(398,140),(361,164),(326,115),(287,141),(247,109),(208,137),(169,115),(125,154),(98,151),(79,211)]
        d.polygon(pts,fill='#4c3029',outline=INK,width=11)
        for pts in [[(87,152),(137,101),(195,78),(226,91)],[(239,71),(288,78),(337,98),(370,124)],[(113,160),(157,131),(179,139)]]:line(d,pts,7,'#98704c')
        for x in (185,326):d.ellipse((x-51,219,x+51,321),outline=INK,width=5)
        line(d,[(237,265),(274,265)],5)
    elif who=='victim':
        for side in (-1,1):
            x=256+side*198;d.polygon([(x,222),(x+side*38,193),(x+side*29,253),(x+side*43,278),(x,301)],fill='#e6e2d3',outline=INK,width=7)
        for x in (185,326):d.rounded_rectangle((x-48,224,x+48,316),radius=11,outline=INK,width=5)
        line(d,[(234,265),(276,265)],5)
    else:
        d.pieslice((54,32,458,283),180,360,fill='#2a2d32',outline=INK,width=11)
        d.rounded_rectangle((31,168,480,214),radius=19,fill='#e7c440',outline=INK,width=10)
        d.polygon([(230,57),(284,57),(306,170),(211,170)],fill='#e9f83d')
        d.rounded_rectangle((234,90,284,146),radius=8,fill='#b9422b',outline=INK,width=5)
    im.save(ART/f'{who}_head.png')

def face(exp,mouth,blink=False):
    im=Image.new('RGBA',(512,512),(33,27,33,0));d=ImageDraw.Draw(im)
    ey=270
    for x in (185,326):
        mask=Image.new('L',im.size);md=ImageDraw.Draw(mask);md.ellipse((x-20,ey-36,x+20,ey+36),fill=255)
        top=ey-36;bottom=ey+36
        if exp=='focus':top=ey-6;bottom=ey+28
        if blink:top=bottom=ey
        clip=Image.new('L',im.size);ImageDraw.Draw(clip).rectangle((0,top,512,bottom),fill=255)
        eye=Image.new('RGBA',im.size,INK);eye.putalpha(ImageChops.multiply(mask,clip));im=Image.alpha_composite(im,eye);d=ImageDraw.Draw(im)
        if blink:line(d,[(x-22,ey),(x+22,ey)],8)
    if exp in ('shock','panic'):brows=[[(145,207),(214,198)],[(294,198),(365,207)]]
    elif exp=='focus':brows=[[(143,214),(213,232)],[(296,232),(367,214)]]
    else:brows=[[(148,216),(213,221)],[(296,218),(363,208)]]
    for pts in brows:line(d,pts,13)
    # Capsule mouths support the audio envelope without moving the skull.
    if mouth=='teeth':
        d.rounded_rectangle((201,345,310,407),radius=22,fill='#f3e9da',outline=INK,width=8)
        for x in (225,249,273,289):d.line((x,350,x,402),fill=INK,width=4)
        d.line((205,376,306,376),fill=INK,width=4)
    elif mouth=='wide':
        d.ellipse((217,337,298,426),fill=INK);d.ellipse((233,393,286,421),fill='#b34d5e')
    elif mouth=='half':d.rounded_rectangle((216,357,300,400),radius=20,fill=INK);d.arc((236,375,292,410),180,350,fill='#d67682',width=7)
    elif exp=='panic':line(d,[(214,389),(255,373),(300,390)],10)
    else:d.arc((207,326,312,404),0,165,fill=INK,width=11)
    im.save(ART/f'face_{exp}_{mouth}_{int(blink)}.png')

def body(who):
    im=Image.new('RGBA',(512,512),(33,27,33,0));mask=Image.new('L',im.size);d=ImageDraw.Draw(mask)
    d.rounded_rectangle((108,92,404,454),radius=118,fill=255);d.rounded_rectangle((212,15,301,150),radius=30,fill=255)
    ink=Image.new('RGBA',im.size,INK);ink.putalpha(mask);im=Image.alpha_composite(im,ink);inner=mask.filter(ImageFilter.MinFilter(19))
    color={'scientist':'7ba7d1','victim':'94704b','firefighter':'28333f'}[who];im=Image.alpha_composite(im,paint(inner,color));d=ImageDraw.Draw(im)
    if who=='scientist':
        d.line([(151,157),(151,385),(180,416),(336,416),(364,385),(364,157)],fill='#dcecf4',width=5,joint='curve')
        d.polygon([(190,98),(253,160),(320,98),(285,200),(254,173),(224,200)],fill='#f8f2e7',outline=INK,width=5)
        d.polygon([(249,169),(266,169),(279,207),(265,351),(247,365),(235,341),(247,209)],fill='#cf4232',outline='#7b2b28',width=4)
        d.rounded_rectangle((305,253,357,303),radius=6,outline='#dcecf4',width=5)
    elif who=='firefighter':
        for y in (250,349):d.rectangle((123,y,388,y+32),fill='#e4f638');d.rectangle((123,y+11,388,y+19),fill='#e1e2bf')
        d.rectangle((248,106,263,434),fill='#e7bd4c')
    else:d.polygon([(182,103),(252,210),(326,104),(294,218),(254,257),(215,219)],fill='#d5c9ac',outline=INK,width=5)
    im.save(ART/f'{who}_body.png')

def fx():
    yy,xx=np.mgrid[:256,:256];r=np.sqrt(((xx-127.5)/127.5)**2+((yy-127.5)/127.5)**2)
    for name,col in [('pink',(250,148,192)),('gold',(255,208,107)),('dust',(198,173,128))]:
        a=np.zeros((256,256,4),dtype=np.uint8);a[:,:,:3]=col;a[:,:,3]=(np.clip(1-r,0,1)**2.6*180).astype(np.uint8);Image.fromarray(a).save(ART/f'puff_{name}.png')
    im=Image.new('RGBA',(256,256),(33,27,33,0));d=ImageDraw.Draw(im);d.polygon([(128,22),(190,152),(187,194),(161,225),(111,232),(70,205),(57,163)],fill='#79cbe3',outline=INK,width=6);im.save(ART/'sweat.png')

def hud(shot,title):
    im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im);sz=35
    while True:
        f=ImageFont.truetype(FONT,sz)
        if d.textbbox((0,0),title,font=f)[2]<900:break
        sz-=1
    d.rounded_rectangle((65,80,1015,172),radius=28,fill='#0f172a',outline='#e5d3a1',width=2)
    d.text((540,126),title,font=f,fill='#fff9ef',anchor='mm');im.save(ART/f'hud_{shot}.png')

def main():
    for who in ('scientist','victim','firefighter'):head(who);body(who)
    for exp in ('focus','smug','shock','panic','proud'):
        for mouth in ('closed','half','wide','teeth'):
            for blink in (False,True):face(exp,mouth,blink)
    fx()
    titles={'1A':'ONE CURLY HAIR. ZERO RESPECT.','1B':'THE SCIENTIST HAS OTHER PLANS','1C':'TINY HAIR. BIG EXPERIMENT.','1D':'PLUCK! A NEW CAREER BEGINS','1E':'FROM HAIR TO HARDWARE','2A':'PERFUME IN. SCIENCE OUT.','2B':'BIO-SENSOR: INSTANT SIGNAL','2C':'WAIT... IT ACTUALLY WORKS?!','2D':'HAIR: MATCH  /  MACHINES: WAITING','2E':'PLUG IT IN. FOLLOW THE SIGNAL.','2F':'A NEW WAY TO READ THE AIR','2G':'SMELL BECOMES A DIRECTION','3A':'ONE SENSOR. FOUR ROTORS.','3B':'CLEARED FOR TAKEOFF','3C':'NO REMOTE. JUST SMELL.','3D':'FOLLOWING THE INVISIBLE TRAIL','3E':'TARGET FOUND: MORE CURLY HAIRS','4A':'EMERGENCY MODE: SEARCH & RESCUE','4B':'A SURVIVOR UNDER THE RUBBLE','4C':'FROM ZERO TO RESCUE HERO','4D':'CAREER UNLOCKED: LIFESAVER'}
    for k,v in titles.items():hud(k,v)
    print('V3 actors / expression bank / single-pill HUD / soft FX ready.',flush=True)

if __name__=='__main__':main()
