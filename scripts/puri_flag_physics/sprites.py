"""Paint stable flat cels and the sacred flag texture; no generated bitmap service."""
from math import sin, cos, pi
from PIL import Image, ImageDraw, ImageChops, ImageFilter
from timeline import OUT

DEST = OUT/'sprites'
INK = '#351f22'

def crescent(im, mask):
    shifted=Image.new('L',mask.size); shifted.paste(mask,(20,-16))
    edge=ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(7))
    shade=Image.new('RGBA',mask.size,(46,83,118,0))
    shade.putalpha(edge.point(lambda x:round(x*.15)))
    im.alpha_composite(shade)

def head(role, mouth, blink):
    im=Image.new('RGBA',(768,768)); d=ImageDraw.Draw(im)
    points=[]
    for j in range(256):
        a=2*pi*j/256; r=1+.022*sin(2*a+.6)-.015*cos(3*a-.8)+.008*sin(5*a+1.9)
        points.append((384+309*r*cos(a),393+303*r*sin(a)))
    mask=Image.new('L',im.size); ImageDraw.Draw(mask).polygon(points,fill=255)
    d.polygon(points,fill=INK)
    inner=mask.filter(ImageFilter.MinFilter(21))
    cream=Image.new('RGBA',im.size,'#fdfaf2');cream.putalpha(inner);im.alpha_composite(cream)
    crescent(im,inner);d=ImageDraw.Draw(im)
    hair=[(82,374),(64,289),(110,177),(207,104),(329,65),(470,78),(608,145),(687,270),
          (680,350),(636,307),(607,237),(537,213),(494,169),(446,219),(384,171),
          (314,218),(255,199),(197,259),(156,267),(128,342)]
    d.polygon(hair,fill='#46302b',outline=INK,width=16)
    d.line([(112,249),(196,161),(300,118),(400,126)],fill='#86603d',width=13,joint='curve')
    d.line([(438,123),(536,163),(600,224)],fill='#73513a',width=10,joint='curve')
    for x in (275,491):
        if blink==2:d.line([(x-24,397),(x+24,397)],fill='#1c1417',width=10)
        else:
            pupil=Image.new('L',im.size);p=ImageDraw.Draw(pupil)
            p.ellipse((x-20,365,x+20,426),fill=255)
            if blink==1:p.rectangle((0,0,768,391),fill=0)
            layer=Image.new('RGBA',im.size,'#1c1417');layer.putalpha(pupil);im.alpha_composite(layer)
    d=ImageDraw.Draw(im)
    for x in (275,491):d.arc((x-38,326,x+40,357),190,335,fill=INK,width=9)
    if role=='host':
        for x in (275,491):d.ellipse((x-78,341,x+78,463),outline=INK,width=9)
        d.line([(352,389),(413,389)],fill=INK,width=9)
    else:
        d.line([(384,278),(384,319)],fill='#c56a32',width=13)
        d.ellipse((372,324,396,347),fill='#b44f2e')
    if mouth==0:d.arc((331,465,435,534),12,168,fill=INK,width=10)
    else:
        h=(24,42,65)[mouth-1]
        d.ellipse((351,492-h/2,417,492+h/2),fill=INK)
        if mouth>1:d.ellipse((367,495,406,510+h/2),fill='#aa5364')
    return im

def body(role):
    im=Image.new('RGBA',(512,640));d=ImageDraw.Draw(im)
    contour=[(222,36),(290,36),(296,78),(377,103),(403,216),(390,474),
             (352,528),(158,528),(120,474),(109,216),(136,103),(216,78)]
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(contour,fill=255)
    d.polygon(contour,fill=INK)
    inner=mask.filter(ImageFilter.MinFilter(15))
    base=Image.new('RGBA',im.size,'#244a71' if role=='host' else '#df9e36');base.putalpha(inner)
    im.alpha_composite(base);crescent(im,inner);d=ImageDraw.Draw(im)
    if role=='host':
        d.polygon([(202,86),(256,309),(307,86)],fill='#eee9d9')
        d.polygon([(252,134),(268,149),(265,264),(253,284),(244,260),(243,152)],fill='#ba5d37')
        d.line([(193,98),(170,201),(214,210),(197,247),(256,366)],fill='#6683a0',width=7)
        d.line([(315,98),(339,201),(296,210),(315,247),(256,366)],fill='#6683a0',width=7)
        d.line([(280,390),(357,390)],fill='#dbb874',width=6)
    else:
        d.polygon([(173,94),(215,81),(334,483),(289,495)],fill='#f5df9d')
        for y in range(140,481,60):d.line([(220,y),(280,y+33)],fill='#b87931',width=4)
    d.rounded_rectangle((139,474,372,541),radius=20,fill='#233346',outline=INK,width=8)
    return im

def flag():
    im=Image.new('RGBA',(1024,512),'#e63946');d=ImageDraw.Draw(im)
    d.rectangle((10,10,1013,501),outline='#ffd700',width=27)
    # The UV maps a rectangular painting onto a geometrically triangular cloth.
    d.ellipse((694,193,814,313),fill='#ffd85c')
    for j in range(12):
        a=j*pi/6;d.line([(754+68*cos(a),253+68*sin(a)),(754+91*cos(a),253+91*sin(a))],fill='#ffd85c',width=8)
    d.ellipse((420,184,564,328),fill='#ffe592')
    d.ellipse((456,164,590,299),fill='#e63946')
    return im

if __name__=='__main__':
    DEST.mkdir(parents=True,exist_ok=True)
    for role in ('host','pilgrim'):
        body(role).save(DEST/f'{role}_body.png')
        for mouth in range(4):
            for blink in range(3):head(role,mouth,blink).save(DEST/f'{role}_{mouth}_{blink}.png')
    flag().save(DEST/'temple_flag.png')
    for name,rgb,opacity in [('wake',(164,115,222),60),('mist',(160,176,182),42)]:
        soft=Image.new('RGBA',(768,384));mask=Image.new('L',soft.size)
        ImageDraw.Draw(mask).ellipse((80,95,690,290),fill=opacity)
        mask=mask.filter(ImageFilter.GaussianBlur(47))
        soft.paste((*rgb,255),(0,0,768,384));soft.putalpha(mask);soft.save(DEST/f'{name}.png')
    print('Cel art and flag painting ready')
