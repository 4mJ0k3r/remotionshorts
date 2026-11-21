"""Paint expressive cel art and prepare exact-duration narration."""
from math import sin,cos,pi
import json
import subprocess
from PIL import Image,ImageDraw,ImageChops,ImageFilter
from timeline import OUT

SPR=OUT/'sprites';INK='#141215';CREAM='#f5f2e8'
STATES=('relaxed','target','smirk','fury','vein','shock','momos','cry','no')

def head(state,blink=0,variant=0,turn=0):
    im=Image.new('RGBA',(1024,1024),(22,18,25,0));d=ImageDraw.Draw(im)
    contour=[];inner=[]
    for j in range(256):
        a=j*2*pi/256;r=1+.015*sin(2*a+.4)-.009*cos(3*a-.7)
        width=9*(1+.35*cos(a-2.4))
        contour.append((512+(365*r+width)*cos(a),513+(379*r+width)*sin(a)))
        inner.append((512+(365*r-width)*cos(a),513+(379*r-width)*sin(a)))
    d.polygon(contour,fill=INK);d.polygon(inner,fill=CREAM)
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(inner,fill=255)
    shifted=Image.new('L',im.size);shifted.paste(mask,(29,-22))
    cres=ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(7))
    shade=Image.new('RGBA',im.size,(59,91,122,0));shade.putalpha(cres.point(lambda v:round(v*.15)));im.alpha_composite(shade)
    d=ImageDraw.Draw(im)
    # Small side ear, cropped by hair at its upper join, and stable brown fringe.
    d.ellipse((840,485,933,644),fill=CREAM,outline=INK,width=16)
    d.arc((864,518,910,607),95,278,fill=INK,width=11)
    hair=[(160,427),(147,327),(207,219),(325,135),(479,107),(643,131),(786,230),(859,340),
          (855,407),(799,348),(752,291),(698,309),(633,251),(583,292),(502,246),
          (433,291),(359,272),(303,332),(254,345),(220,412)]
    d.polygon(hair,fill='#46302b',outline=INK,width=16)
    d.line([(206,291),(316,203),(450,164),(580,177)],fill='#856142',width=13,joint='curve')
    original=im;im=Image.new('RGBA',im.size);d=ImageDraw.Draw(im)
    angry=state in ('fury','vein');wide=state in ('target','shock','cry')
    # Contiguous large white cartoon eyes are explicitly requested for this cast.
    for i,x in enumerate((429,588)):
        bbox=(x-91,391 if not wide else 373,x+91,588 if not wide else 600)
        d.ellipse(bbox,fill='#fffdf6',outline=INK,width=13)
        pupil=Image.new('L',im.size);pd=ImageDraw.Draw(pupil)
        px=x+(12 if state=='target' else -2 if state=='smirk' else 0)
        py=512+(33 if state=='target' else 0)
        rad=12 if state=='shock' else 23
        pd.ellipse((px-rad,py-39,px+rad,py+39),fill=255)
        top=470 if state in ('relaxed','smirk','no') else 392
        if angry:top=451
        if blink:top=500 if blink==1 else 589
        pd.rectangle((0,0,1024,top),fill=0)
        layer=Image.new('RGBA',im.size,INK);layer.putalpha(pupil);im.alpha_composite(layer)
        d=ImageDraw.Draw(im)
        if top>392:
            lid=Image.new('RGBA',im.size,CREAM);lm=Image.new('L',im.size)
            ld=ImageDraw.Draw(lm);ld.ellipse(bbox,fill=255);ld.rectangle((0,top,1024,1024),fill=0)
            lid.putalpha(lm);im.alpha_composite(lid);d=ImageDraw.Draw(im)
            d.line([(x-78,top),(x+78,top)],fill=INK,width=11)
    d=ImageDraw.Draw(im)
    if angry:
        d.line([(328,374),(477,427)],fill=INK,width=23)
        d.line([(548,428),(689,373)],fill=INK,width=23)
    elif state in ('target','shock'):
        d.arc((344,326,469,386),190,341,fill=INK,width=14)
        d.arc((553,326,678,386),196,344,fill=INK,width=14)
    else:
        d.line([(349,377),(476,383)],fill=INK,width=12)
        d.line([(548,383),(675,374)],fill=INK,width=12)
    d.ellipse((464,504,565,619),fill='#f2dfc9',outline=INK,width=13)
    if angry:
        d.rounded_rectangle((331,651,708,801),radius=48,fill='#fff9dc',outline=INK,width=17)
        d.line([(344,725),(696,725)],fill=INK,width=9)
        for x in range(385,690,55):d.line([(x,663),(x,787)],fill=INK,width=8)
    elif state=='shock':d.ellipse((438,663,577,827),fill='#34202a',outline=INK,width=15)
    elif state=='target':d.ellipse((473,684,545,755),fill='#34202a')
    elif state=='smirk':
        d.polygon([(344,678),(691,642),(649,743),(485,776),(385,743)],fill='#2e2022',outline=INK)
        d.polygon([(365,680),(666,658),(635,697),(404,720)],fill='#fff8e5')
        d.arc((344,637,699,778),12,169,fill=INK,width=12)
    elif state=='cry':
        d.arc((380,699,647,832),195,348,fill=INK,width=18)
        d.ellipse((413,737,626,804),fill='#483141')
        d.line([(429,750),(607,750)],fill='#fff2d7',width=17)
    elif state=='momos':
        d.ellipse((286,645,379,721),fill='#ecb8a2');d.ellipse((654,644,747,721),fill='#ecb8a2')
        if variant:d.ellipse((449,689,582,771),fill='#38202a')
        else:d.arc((389,654,645,775),5,176,fill=INK,width=14)
        d.polygon([(610,741),(649,730),(675,755),(651,773),(624,766)],fill='#b43b28')
    else:d.arc((385,637,650,767),5,171,fill=INK,width=14)
    if state=='vein':
        col='#c84c55' if variant else '#bd3d38'
        for x,y in ((323,328),(709,325)):
            d.line([(x-24,y-29),(x-12,y-8),(x-34,y+13)],fill=col,width=15,joint='curve')
            d.line([(x+25,y-30),(x+11,y-8),(x+33,y+14)],fill=col,width=15,joint='curve')
    original.alpha_composite(im,(round(turn*365),0))
    return original

def poop_face(state):
    im=Image.new('RGBA',(512,512),(22,18,25,0));d=ImageDraw.Draw(im)
    for x in (167,337):
        d.ellipse((x-68,89,x+68,256),fill='#fff5d8',outline='#331d0a',width=13)
        if state=='cling':d.ellipse((x-15,113,x+23,195),fill=INK)
        else:d.ellipse((x-17,151,x+17,222),fill=INK)
    if state=='cool':
        for x in (167,337):d.rounded_rectangle((x-86,114,x+86,237),radius=29,fill='#171719',outline='#331d0a',width=11)
        d.line([(245,150),(258,150)],fill=INK,width=18)
        d.line([(119,137),(164,137)],fill='#697886',width=9)
    if state=='gulp':pass # Animated 3D cavity, tongue and jaw replace the painted mouth.
    elif state=='cling':d.ellipse((208,312,300,414),fill='#28171b')
    else:d.arc((130,273,378,401),5,172,fill='#331d0a',width=17)
    return im

def speedlines():
    im=Image.new('RGBA',(1024,1024));d=ImageDraw.Draw(im)
    for j in range(25):
        a=j*2*pi/25+.045*sin(j*13);r1=375+18*sin(j*5);r2=490+12*cos(j*4)
        d.line([(512+r1*cos(a),512+r1*sin(a)),(512+r2*cos(a),512+r2*sin(a))],fill=INK,width=8+j%3*3)
    return im

def main():
    SPR.mkdir(parents=True,exist_ok=True)
    source='C:/Users/lavis/Downloads/ElevenLabs_2026-11-14T16_45_23_Viraj - Rich, Confident and Expressive_pvc_s30_sim75_v4.mp3'
    import sys
    if 'assets-only' not in sys.argv:
        subprocess.run(['ffmpeg','-v','error','-y','-i',source,'-t','54.50','-af','afade=t=out:st=54.47:d=0.03,loudnorm=I=-16:TP=-1.5:LRA=7',
            '-ar','48000','-ac','1','-c:a','pcm_s16le',str(OUT/'audio_master.wav')],check=True)
    for state in STATES:
        for blink in range(3):
            for variant in (range(2) if state in ('vein','momos') else (0,)):
                head(state,blink,variant).save(SPR/f'boy_{state}_{blink}_{variant}.png')
    for state in ('idle','cling','gulp','cool'):poop_face(state).save(SPR/f'poop_{state}.png')
    for blink in range(3):head('relaxed',blink,0,turn=-.18).save(SPR/f'boy_relaxedturn_{blink}_0.png')
    for side,turn in [('noleft',-.12),('noright',.12)]:head('no',0,0,turn=turn).save(SPR/f'boy_{side}_0_0.png')
    # One flat, outlined shirt with a clipped cool crescent and no sidewalls.
    shirt=Image.new('RGBA',(512,640));sd=ImageDraw.Draw(shirt)
    mask=Image.new('L',shirt.size);md=ImageDraw.Draw(mask)
    md.rounded_rectangle((38,29,474,616),radius=178,fill=255)
    sd.rounded_rectangle((38,29,474,616),radius=178,fill=INK)
    inner=mask.filter(ImageFilter.MinFilter(21));paint=Image.new('RGBA',shirt.size,'#2a7f62');paint.putalpha(inner);shirt.alpha_composite(paint)
    shifted=Image.new('L',shirt.size);shifted.paste(inner,(22,-18))
    cres=ImageChops.subtract(inner,shifted).filter(ImageFilter.GaussianBlur(5))
    tint=Image.new('RGBA',shirt.size,(27,60,78,0));tint.putalpha(cres.point(lambda v:round(v*.15)));shirt.alpha_composite(tint)
    ImageDraw.Draw(shirt).arc((195,31,317,110),0,180,fill='#183c35',width=11)
    shirt.save(SPR/'boy_shirt.png')
    speedlines().save(SPR/'speedlines.png')
    (OUT/'audio_source.json').write_text(json.dumps({'source':source,'duration':54.5,'fps':30,'frames':1635,'type':'narration; character reactions are non-speaking acting'},indent=2))
    print('Assets ready: expressive cels and 54.50s narration')

if __name__=='__main__':main()
