"""Stable supersampled cel artwork. No captions, labels or font rendering."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/sendha_namak_science'
ART=OUT/'assets'
INK='#2b1810'

def head(kind,expression):
    im=Image.new('RGBA',(1024,1024),(28,18,14,0)); d=ImageDraw.Draw(im)
    outer=[]; inner=[]
    for i in range(384):
        a=i*math.tau/384
        r=1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9)
        w=15*max(.25,1+.52*math.cos(a-2.35)+.22*math.sin(3*a+1.1)+.14*math.cos(5*a-.7))
        outer.append((512+(416*r+w/2)*math.cos(a),510+(416*r+w/2)*math.sin(a)))
        inner.append((512+(416*r-w/2)*math.cos(a),510+(416*r-w/2)*math.sin(a)))
    if kind=='partner':
        d.ellipse((745,190,1000,660),fill=INK);d.ellipse((760,205,982,645),fill='#45230e')
    d.polygon(outer,fill=INK);d.polygon(inner,fill='#fdfaf2')
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(inner,fill=255)
    shifted=Image.new('L',im.size);shifted.paste(mask,(65,-45))
    cres=ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(15))
    arr=np.array(im); strength=np.asarray(cres)/255*.15
    arr[:,:,:3]=(arr[:,:,:3]*(1-strength[:,:,None])).astype('uint8'); im=Image.fromarray(arr);d=ImageDraw.Draw(im)
    if kind!='doctor':
        hair=[(108,435),(105,344),(153,229),(251,145),(391,100),(549,87),(697,120),(818,201),(893,331),(901,465),(861,469),(824,324),(762,329),(722,290),(622,329),(557,289),(446,331),(374,300),(282,359),(232,330),(167,453)]
        d.polygon(hair,fill=INK)
        d.polygon([(x, y-3 if y>320 else y+13) for x,y in hair[:-3]],fill='#45230e')
        for j in range(3):d.arc((175+j*38,130+j*15,775,540),190,279,fill='#9c5822',width=9-j*2)
    else:
        d.pieslice((102,240,260,650),90,270,fill='#b6becb');d.pieslice((768,240,926,650),270,450,fill='#b6becb')
        d.line((145,314,875,314),fill=INK,width=16)
    face_base=im.copy()
    for s,x in enumerate([350,665]):
        if expression=='spiral':
            pts=[(x+(.6+a*8)*math.cos(a),540+(.6+a*8)*math.sin(a)) for a in np.linspace(0,math.pi*3,100)]
            d.line(pts,fill=INK,width=13)
        elif expression=='hypno':
            for r in [73,47,20]:d.ellipse((x-r,540-r,x+r,540+r),outline=INK,width=9)
        elif expression=='blink':d.line((x-47,544,x+43,544),fill=INK,width=15)
        else:
            top=485 if expression not in ['panic','worry'] else 461
            ew=40 if expression=='panic' else 32
            d.ellipse((x-ew,top,x+ew-4,top+112),fill='#1c1417')
            if expression=='smirk':d.line((x-55,top+10,x+46,top+32),fill=INK,width=22)
        if kind=='doctor':d.ellipse((x-103,423,x+100,639),outline='#343747',width=12)
        if kind=='partner':d.line((x-40,490,x-70,467),fill=INK,width=10)
        if expression=='panic':d.line((x-61,412+(40 if s else 0),x+61,412+(0 if s else 40)),fill=INK,width=17)
        elif expression=='worry':d.arc((x-64,374,x+62,460),190,340,fill=INK,width=14)
        elif expression=='smirk':d.line((x-58,420+(s*22),x+54,444-(s*22)),fill=INK,width=16)
        else:d.arc((x-57,396,x+60,462),195,340,fill=INK,width=13)
    if kind=='doctor':d.line((450,517,563,517),fill='#343747',width=10)
    if expression=='worry':
        d.ellipse((208,611,295,639),fill='#f3b4b7');d.ellipse((742,611,825,639),fill='#f3b4b7')
    im.save(ART/f'{kind}_{expression}.png')
    if kind=='boy' and expression=='neutral':
        # Shift the face group only; skull, hair and alpha remain unchanged.
        # Redraw a deliberately authored three-quarter face variant.
        base=face_base.copy();dd=ImageDraw.Draw(base)
        for x in [460,745]:
            dd.ellipse((x-29,484,x+29,596),fill='#1c1417');dd.arc((x-55,395,x+55,460),190,345,fill=INK,width=14)
        base.save(ART/'boy_profile.png')

def body(kind):
    im=Image.new('RGBA',(640,1024),(28,18,14,0));d=ImageDraw.Draw(im)
    d.rounded_rectangle((255,0,385,240),radius=55,fill=INK)
    d.rounded_rectangle((270,0,370,250),radius=40,fill='#fdfaf2')
    d.rounded_rectangle((105,155,535,1008),radius=190,fill=INK)
    color={'boy':'#4895ef','partner':'#f26a8d','doctor':'#f8f9fa'}[kind]
    d.rounded_rectangle((122,174,518,990),radius=178,fill=color)
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).rounded_rectangle((122,174,518,990),178,fill=255)
    shift=Image.new('L',im.size);shift.paste(mask,(40,-30))
    cres=ImageChops.subtract(mask,shift).filter(ImageFilter.GaussianBlur(8))
    arr=np.array(im);arr[:,:,:3]=(arr[:,:,:3]*(1-np.asarray(cres)[:,:,None]/255*.15)).astype('uint8');im=Image.fromarray(arr);d=ImageDraw.Draw(im)
    if kind=='boy':
        d.line((335,240,335,925),fill='#eaf5ff',width=13)
        d.rounded_rectangle((368,360,458,475),radius=14,outline='#235c95',width=8)
    elif kind=='doctor':
        d.polygon([(260,188),(320,400),(380,188),(350,560),(300,560)],fill='#8dd6d0')
        d.line((257,245,234,425,278,525),fill='#546471',width=10);d.line((380,245,408,425,365,525),fill='#546471',width=10)
        d.arc((190,360,435,645),0,180,fill='#283849',width=15);d.ellipse((295,596,347,650),fill='#546471')
        d.rounded_rectangle((365,660,466,782),radius=10,outline='#97b3bd',width=8)
    im.save(ART/f'body_{kind}.png')

def icons():
    # Icons are drawn shapes, with no text/font objects anywhere in the scene.
    for name in ['question','mouth','diagram','soul']:
        im=Image.new('RGBA',(512,512),(28,18,14,0));d=ImageDraw.Draw(im)
        if name=='question':
            d.arc((135,45,380,280),180,470,fill='#ff453d',width=48);d.line((258,273,258,350),fill='#ff453d',width=48);d.ellipse((234,402,282,450),fill='#ff453d')
        elif name=='mouth':d.ellipse((75,35,440,480),fill=INK);d.ellipse((96,60,420,456),fill='#61122e')
        elif name=='diagram':
            d.rounded_rectangle((20,20,492,492),radius=28,fill='#132f43',outline='#72ece8',width=9)
            d.ellipse((150,55,360,265),fill='#f6e7d0',outline=INK,width=8)
            d.ellipse((190,170,325,244),fill='#932d49');d.rounded_rectangle((168,272,342,455),radius=75,fill='#e7d6cb')
            for x in [210,295]:d.ellipse((x-22,293,x+22,390),fill='#f67486')
            d.line((255,242,255,370),fill='#65e7e0',width=15)
        else:
            d.ellipse((90,40,425,410),fill=(118,221,255,155),outline=(197,250,255,200),width=12)
            d.polygon([(140,350),(103,460),(230,396),(310,465),(365,350)],fill=(118,221,255,145))
            for x in [210,315]:d.ellipse((x-12,180,x+12,223),fill='#355d85')
            d.arc((225,230,304,300),0,180,fill='#355d85',width=9)
        im.save(ART/f'{name}.png')
    for state in ['smile','o','flat','panic','open']:
        for talk in range(6):
            im=Image.new('RGBA',(256,160),(28,18,14,0));d=ImageDraw.Draw(im)
            h=(20+talk*16) if state!='o' else (95+talk*7)
            if state in ['panic','open']:
                bounds=(55,8,201,152) if state=='panic' else (20,8,236,152)
                d.ellipse(bounds,fill=INK)
                if state=='open':d.ellipse((85,115,191,147),fill='#dd6486')
            elif state=='flat' and talk==0:d.line((35,75,220,85),fill=INK,width=13)
            else:
                d.ellipse((25,80-h/2,231,80+h/2),fill=INK)
                if h>48:
                    d.rectangle((51,80-h/2+8,204,80-h/2+23),fill='#fff9e7')
                    d.ellipse((82,80+h/2-32,192,80+h/2-5),fill='#e97988')
            im.save(ART/f'mouth_{state}_{talk}.png')
    yy,xx=np.mgrid[-1:1:960j,-1:1:540j]
    val=(255*(1-.18*np.clip((xx*xx+yy*yy-.55)/1.45,0,1))).astype('uint8')
    Image.fromarray(val).convert('RGB').save(ART/'vignette.png')

def main():
    ART.mkdir(parents=True,exist_ok=True)
    for kind in ['boy','partner','doctor']:
        body(kind)
        for expr in ['neutral','smirk','panic','hypno','worry','spiral','smile','blink']:head(kind,expr)
    icons()

if __name__=='__main__':main()
