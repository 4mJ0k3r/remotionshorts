"""Authored cel assets: unified body masks, scene-lit cream heads, no subtitles."""
from pathlib import Path
import math, numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/crorepati_poop_love';ART=OUT/'assets'
N=1536;INK='#1a1214';CREAM='#fdfaf2';CLEAR=(26,18,20,0)

def canvas():return Image.new('RGBA',(N,N),CLEAR)
def shade(im,mask):
    shifted=Image.new('L',mask.size);shifted.paste(mask,(-90,-75))
    shadow=ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(24))
    a=np.asarray(im).copy();weight=np.asarray(shadow)/255*.22
    a[:,:,:3]=(a[:,:,:3]*(1-weight[:,:,None])).astype('uint8');im=Image.fromarray(a)
    lit=Image.new('L',mask.size);lit.paste(mask,(22,15))
    rim=ImageChops.subtract(mask,lit).filter(ImageFilter.GaussianBlur(7))
    layer=Image.new('RGBA',im.size,(255,222,172,0));layer.putalpha(rim.point(lambda x:int(x*.35)))
    return Image.alpha_composite(im,layer)

def head(kind):
    im=canvas();d=ImageDraw.Draw(im);outer=[];inner=[]
    for i in range(384):
        a=i*math.tau/384;r=1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9)
        w=14*max(.4,1+.42*math.cos(a-.7)+.18*math.sin(3*a+1.1)+.1*math.cos(5*a-.7))
        outer.append((768+(597*r+w/2)*math.cos(a),768+(594*r+w/2)*math.sin(a)))
        inner.append((768+(597*r-w/2)*math.cos(a),768+(594*r-w/2)*math.sin(a)))
    d.polygon(outer,fill=INK);d.polygon(inner,fill=CREAM)
    mask=Image.new('L',(N,N));ImageDraw.Draw(mask).polygon(inner,fill=255);im=shade(im,mask);d=ImageDraw.Draw(im)
    messy=kind=='broke';hair='#191619' if messy else '#302029'
    points=[(178,690),(188,490),(298,323),(451,221),(642,171),(832,175),(1033,248),(1198,373),(1314,551),(1344,680),(1286,645),(1220,494),(1100,530),(975,463),(861,525),(705,467),(549,546),(431,507),(311,610),(236,701)]
    if messy:
        points=[(178,690),(180,500),(248,460),(220,370),(340,385),(330,285),(455,330),(510,190),(610,260),(720,145),(820,215),(940,182),(1060,268),(1198,373),(1314,551),(1344,680),(1286,645),(1220,494),(1100,530),(975,463),(861,525),(705,467),(549,546),(431,507),(311,610),(236,701)]
    hm=Image.new('L',(N,N));ImageDraw.Draw(hm).polygon(points,fill=255)
    if messy:
        # Fill the skull beneath the spikes; otherwise cream triangles leak
        # between the jagged crown and the organic outer head boundary.
        cap=Image.new('L',(N,N));ImageDraw.Draw(cap).polygon(inner[192:]+[(1344,680),(1286,645),(1220,494),(1100,530),(975,463),(861,525),(705,467),(549,546),(431,507),(311,610),(236,701),(178,690)],fill=255)
        hm=ImageChops.lighter(hm,cap)
    hairink=Image.new('RGBA',(N,N),INK);hairink.putalpha(hm);im=Image.alpha_composite(im,hairink)
    hp=Image.new('RGBA',(N,N),hair);hp.putalpha(hm.filter(ImageFilter.MinFilter(15)));im=Image.alpha_composite(im,hp);d=ImageDraw.Draw(im)
    for j in range(3):d.arc((290+j*42,260+j*22,1210,760),197,280,fill='#65505a' if not messy else '#3d3032',width=10-j*2)
    if messy:
        for i in range(65):
            a=.24+math.pi*.85*i/64;x=768+531*math.cos(a);y=768+530*math.sin(a)
            d.line((x,y,x+7,y+14),fill='#685a55',width=5)
    im.save(ART/f'head_{kind}.png')
    if kind in ['broke','butler']:
        arr=np.array(im);skin=(arr[:,:,0]>140)&(arr[:,:,1]>120)&(arr[:,:,2]>100)&(arr[:,:,3]>0)
        for c,factor in enumerate([255/253,210/250,204/242]):arr[:,:,c]=np.where(skin,np.clip(arr[:,:,c]*factor,0,255),arr[:,:,c]).astype('uint8')
        Image.fromarray(arr).save(ART/f'head_{kind}_flush.png')

def body(kind):
    neck=Image.new('L',(N,N));shirt=neck.copy();pants=neck.copy()
    ImageDraw.Draw(neck).rounded_rectangle((671,40,865,430),radius=65,fill=255)
    ImageDraw.Draw(shirt).rounded_rectangle((352,300,1184,1460),radius=255,fill=255)
    ImageDraw.Draw(pants).rectangle((352,1130,1184,1460),fill=255)
    union=ImageChops.lighter(neck,shirt);inside=union.filter(ImageFilter.MinFilter(29))
    im=Image.new('RGBA',(N,N),INK);im.putalpha(union)
    colors={'ragged':('#7a5230','#30303e'),'booted':('#7a5230','#30303e'),'blue':('#2b7bba','#172b46'),'purple':('#4a1c6d','#242033'),'butler':('#171b29','#151723'),'tux':('#f2eee4','#171b25'),'rich_tux':('#39233c','#151725'),'kid1':('#6c367c','#203049'),'kid2':('#276b79','#263149'),'bath':('#7a5230','#e6bba3')}
    top,bottom=colors[kind]
    for mask,color in [(neck,CREAM),(shirt,top),(pants,bottom)]:
        layer=Image.new('RGBA',(N,N),color);layer.putalpha(ImageChops.multiply(mask,inside));im=Image.alpha_composite(im,layer)
    im=shade(im,inside);deco=canvas();d=ImageDraw.Draw(deco)
    if kind in ['ragged','bath','booted']:
        for x,y,col in [(455,805,'#b28b5f'),(937,588,'#5b4030'),(854,1300,'#6c5f5a')]:
            d.rectangle((x,y,x+160,y+145),fill=col,outline=INK,width=8)
            for k in range(5):d.line((x-8+k*40,y-10,x+9+k*40,y+12),fill='#d0b38b',width=5)
        d.line((754,398,754,1140),fill='#493321',width=8)
        if kind=='booted':
            d.ellipse((660,750,840,1000),fill='#352828')
            for i in range(4):d.ellipse((620+i*64,659-abs(i-1)*12,680+i*64,728),fill='#352828')
    elif kind=='blue':
        d.polygon([(600,318),(768,494),(935,318),(865,575),(768,516),(673,575)],fill='#9cc9e0')
        d.line((768,500,768,1180),fill='#17436c',width=9)
        for y in range(560,1160,120):d.ellipse((756,y,780,y+24),fill='#e9dece')
    else:
        d.polygon([(585,335),(768,965),(952,335)],fill='#f5f1e7')
        d.polygon([(441,428),(607,332),(768,953),(598,775)],fill=top,outline='#d4ae63' if kind in ['purple','rich_tux'] else INK,width=12)
        d.polygon([(1093,428),(928,332),(768,953),(938,775)],fill=top,outline='#d4ae63' if kind in ['purple','rich_tux'] else INK,width=12)
        if kind=='purple':d.polygon([(723,400),(813,400),(838,643),(768,716),(700,643)],fill='#daa64b',outline=INK,width=8)
        else:
            color='#f4f0e7' if kind=='butler' else '#1a1520'
            d.polygon([(664,380),(768,425),(871,380),(871,493),(768,451),(664,493)],fill=color,outline=INK,width=8)
        for y in [1010,1110]:d.ellipse((750,y,786,y+36),fill='#cfa84f')
    deco.putalpha(ImageChops.multiply(deco.getchannel('A'),inside));Image.alpha_composite(im,deco).save(ART/f'body_{kind}.png')

def heart(d,cx,cy,r,color):
    pts=[]
    for i in range(80):
        a=i*math.tau/80;x=16*math.sin(a)**3;y=13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a)
        pts.append((cx+x*r/16,cy-y*r/16))
    d.polygon(pts,fill=color)

def face(expr,butler=False):
    im=canvas();d=ImageDraw.Draw(im)
    for j,x in enumerate([540,990]):
        if expr in ['sleep','relief','kiss']:d.arc((x-85,738,x+85,859),190,350,fill=INK,width=17)
        elif expr=='hearts':heart(d,x,790,88,'#ef6a9c')
        elif expr=='blink':d.line((x-65,792,x+65,792),fill=INK,width=15)
        else:
            h=133 if expr in ['panic','shock','plead','surprisedBlush'] else 110
            d.ellipse((x-39,742,x+39,742+h),fill=INK)
        if expr=='angry':d.line((x-90,650+(45 if j else 0),x+90,650+(0 if j else 45)),fill=INK,width=20)
        elif expr in ['sad','plead','cry']:d.arc((x-94,595,x+94,724),193,343,fill=INK,width=19)
        elif expr=='panic':d.line((x-90,651+(40 if j else 0),x+90,651+(0 if j else 40)),fill=INK,width=20)
        else:d.arc((x-88,640,x+88,731),195,345,fill=INK,width=16)
    if expr in ['hearts','warm','surprisedBlush']:
        for x in [390,1130]:d.ellipse((x-65,917,x+65,958),fill='#ffb3c1')
    if butler:
        d.ellipse((887,664,1093,915),outline='#e1b658',width=16)
        d.line((1093,820,1168,930,1145,1135),fill='#d7b05b',width=6)
        d.polygon([(620,990),(703,946),(768,979),(831,946),(922,990),(845,1028),(768,1004),(693,1028)],fill=INK)
    im.save(ART/(f'face_{expr}'+('_butler.png' if butler else '.png')))

def mouths():
    for mode in ['smile','sad','o','teeth','kiss','dream']:
        for t in range(6):
            im=Image.new('RGBA',(384,256),CLEAR);d=ImageDraw.Draw(im)
            if mode=='dream' and t==0:d.arc((60,48,324,186),0,180,fill=INK,width=15)
            elif mode=='sad' and t==0:d.arc((60,110,324,236),195,345,fill=INK,width=15)
            elif mode=='kiss':
                d.ellipse((132,83,232,133),fill='#e26c83');d.ellipse((132,128,232,178),fill='#df5d7a');d.line((140,129,234,129),fill=INK,width=8)
            elif mode=='teeth':
                d.rounded_rectangle((42,59,342,203),radius=38,fill='#fff3dd',outline=INK,width=15)
                for x in [115,190,265]:d.line((x,66,x,195),fill=INK,width=7)
                d.line((48,129,336,129),fill=INK,width=6)
            else:
                h=65+t*20 if mode!='o' else 185
                box=(48,128-h/2,336,128+h/2) if mode!='o' else (112,24,272,232)
                d.ellipse(box,fill=INK)
                if h>88 and mode!='o':d.ellipse((145,128+h/2-41,286,128+h/2-6),fill='#dd718b')
            im.save(ART/f'mouth_{mode}_{t}.png')

def main():
    ART.mkdir(parents=True,exist_ok=True)
    for k in ['broke','neat','millionaire','butler','kid1','kid2']:head(k)
    for k in ['ragged','booted','blue','purple','butler','tux','rich_tux','kid1','kid2','bath']:body(k)
    for e in ['neutral','sad','panic','warm','hearts','sleep','relief','angry','cry','shock','plead','blink','kiss','surprisedBlush']:
        face(e);face(e,True)
    mouths()
    yy,xx=np.mgrid[-1:1:960j,-1:1:540j];v=(255*(1-.14*np.clip((xx*xx+yy*yy-.65)/1.35,0,1))).astype('uint8')
    Image.fromarray(v).convert('RGB').save(ART/'vignette.png')
    for title in ['DAY 30','DAY 60','DAY 100','DAY 200: PARIS','5 YEARS LATER']:
        im=Image.new('RGBA',(900,110),CLEAR);d=ImageDraw.Draw(im)
        font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',67)
        d.text((450,53),title,font=font,anchor='mm',fill='#fff0ce',stroke_width=3,stroke_fill=INK)
        full=Image.new('RGBA',(1080,1920),CLEAR);full.alpha_composite(im,(90,58))
        full.save(ART/('stamp_'+title.replace(':','').replace(' ','_')+'.png'))

if __name__=='__main__':main()
