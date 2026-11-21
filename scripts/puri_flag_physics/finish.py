"""Composite screen graphics after the world grade and mux the trimmed narration."""
import json
import subprocess
import sys
import time
from PIL import Image,ImageDraw,ImageFont
from timeline import OUT, ROOT, FRAMES, STILLS, BOUNDS, TITLES, beat

def font(size,bold=True):
    return ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf',max(8,round(size)))

def graphics(size,f):
    w,h=size;b=beat(f);im=Image.new('RGBA',size);d=ImageDraw.Draw(im)
    gold='#ffd46c';cyan='#8ce5fa';red='#ff8552'
    if b==9:
        # The requested foreground narrator is a cel overlay, independent of
        # the physical pilgrims at the base several storeys below this view.
        ink='#351f22';lw=max(2,round(w*.007))
        d.line([(w*.102,h*.942),(w*.087,h*.992)],fill=ink,width=lw)
        d.line([(w*.172,h*.942),(w*.185,h*.992)],fill=ink,width=lw)
        d.line([(w*.078,h*.872),(w*.043,h*.904),(w*.054,h*.933)],fill=ink,width=lw,joint='curve')
        d.line([(w*.190,h*.872),(w*.230,h*.886),(w*.250,h*.853)],fill=ink,width=lw,joint='curve')
        costume=Image.open(OUT/'sprites'/'host_body.png').resize((round(w*.20),round(h*.15)),Image.Resampling.LANCZOS)
        portrait=Image.open(OUT/'sprites'/'host_1_0.png').resize((round(w*.30),round(w*.30)),Image.Resampling.LANCZOS)
        im.alpha_composite(costume,(round(w*.035),round(h*.827)))
        im.alpha_composite(portrait,(round(w*.000),round(h*.710)))
        d=ImageDraw.Draw(im)
    box=(w*.045,h*.022,w*.955,h*.066)
    d.rounded_rectangle(box,radius=h*.014,fill='#0d1826',outline=gold,width=max(1,round(w/400)))
    fs=w*.035
    while d.textlength(TITLES[b],font=font(fs))>w*.85:fs-=1
    d.text((w*.5,h*.044),TITLES[b],anchor='mm',font=font(fs),fill='#fff5db')
    def label(x,y,text,tint=gold):
        ft=font(w*.027);bounds=d.textbbox((x*w,y*h),text,font=ft,anchor='mm')
        d.rounded_rectangle((bounds[0]-6,bounds[1]-5,bounds[2]+6,bounds[3]+5),radius=5,fill=(7,14,24,218))
        d.text((x*w,y*h),text,anchor='mm',font=ft,fill=tint)
    if b in (0,1,5,6,7,9):
        label(.23,.13,'SEA WIND  >>>',cyan)
        label(.75,.18,'<<<  RETURN FLOW' if b>=6 else '<<<  TEMPLE FLAG',red)
    if b==2:label(.68,.80,'NORMAL FLAG  >>>',cyan)
    if b==3:
        d.line([(w*.89,h*.20),(w*.89,h*.84)],fill=gold,width=max(1,round(w/270)))
        for yy in (.20,.84):d.line([(w*.87,h*yy),(w*.91,h*yy)],fill=gold,width=2)
        label(.76,.52,'214 FT')
    if b==4:
        label(.5,.81,'FLUTED AMALAKA CROWN' if f<911 else 'NEELACHAKRA | 8 SPOKES')
    if b in (6,7):label(.72,.40,'LOW-PRESSURE WAKE')
    if b==8:
        label(.5,.81,'GROUND: SCARF FOLLOWS WIND  >>>' if f<1816 else 'CROWN: PROPOSED RETURN FLOW  <<<',cyan if f<1816 else red)
    if b==9:
        for x,y in ((.74,.34),(.83,.40),(.69,.46)):
            d.text((w*x,h*y),'?',anchor='mm',font=font(w*.085),fill=gold,stroke_width=1,stroke_fill='#7d5c1d')
    note='ILLUSTRATIVE AIRFLOW MODEL - NOT SITE-VALIDATED CFD'
    d.text((w*.5,h*.963),note,anchor='mm',font=font(w*.020,False),fill='#b7b8b9',stroke_width=1,stroke_fill='#090c12')
    return im

def compose(image,overlay):
    image=image.convert('RGB');image.paste(overlay,(0,0),overlay);return image

def sheet():
    tw,th=540,960;result=Image.new('RGB',(tw*4,(th+34)*3),'#10151d');d=ImageDraw.Draw(result)
    for i,f in enumerate(STILLS):
        directory='frames_preview' if all((OUT/'frames_preview'/f'f{k:04}.png').exists() for k in STILLS) else 'stills_v1'
        image=Image.open(OUT/directory/f'f{f:04}.png')
        image=compose(image,graphics(image.size,f));x=i%4*tw;y=i//4*(th+34)
        result.paste(image,(x,y));d.text((x+12,y+th+6),f'{(f-1)/30:05.2f}s  |  f{f:04}  |  Beat {beat(f)+1}',font=font(19),fill='#f7deae')
    result.save(OUT/'sheet_v1.jpg',quality=93)
    result.resize((1080,1491),Image.Resampling.LANCZOS).save(OUT/'sheet_v1_small.jpg',quality=93)
    print(OUT/'sheet_v1.jpg')

def video():
    temp=OUT/'preview_encoding.mp4';dest=OUT/'puri_flag_physics_preview.mp4'
    process=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','540x960','-r','30','-i','-',
        '-i',str(OUT/'audio_master.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','19',
        '-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','192k','-movflags','+faststart',str(temp)],stdin=subprocess.PIPE)
    cache={}
    try:
        for f in range(1,FRAMES+1):
            key=(beat(f),f>=911,f>=1816)
            if key not in cache:cache[key]=graphics((540,960),f)
            target=OUT/'frames_preview'/f'f{f:04}.png'
            deadline=time.monotonic()+180
            while True:
                try:
                    with Image.open(target) as im:
                        im.load()
                        if im.size!=(540,960):raise ValueError(f'Wrong resolution at frame {f}: {im.size}')
                        pixels=compose(im,cache[key]).tobytes()
                    break
                except (FileNotFoundError,OSError,SyntaxError):
                    if time.monotonic()>deadline:raise RuntimeError(f'Render stopped before frame {f}')
                    time.sleep(.25)
            process.stdin.write(pixels)
        process.stdin.close()
        if process.wait():raise RuntimeError('Encoding failed')
    except BaseException:
        if process.poll() is None:process.terminate()
        process.wait();raise
    temp.replace(dest)
    (OUT/'shots.json').write_text(json.dumps({'shots':[{'id':i+1,'a':a-1,'b':c-1} for i,(a,c) in enumerate(zip(BOUNDS,BOUNDS[1:]))]},indent=2))
    subprocess.run([sys.executable,str(ROOT/'scripts'/'short_qa.py'),str(dest),str(OUT/'qa_preview'),str(OUT/'shots.json')],check=True)
    print(dest)

if __name__=='__main__':sheet() if sys.argv[1]=='sheet' else video()
