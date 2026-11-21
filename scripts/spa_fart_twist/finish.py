"""Add the seven HUD titles, export the contact sheet and mux the final cut."""
import json
from pathlib import Path
import subprocess
import sys
from PIL import Image,ImageDraw,ImageFont
from timeline import FRAMES, BOUNDS, STILLS

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders'/'spa_fart_twist'
TITLES=(
    'LUXURY ZEN SPA: DEEP RELAXATION',
    'WAIT... WHAT WAS THAT SOUND?!',
    "MASSEUR: 'RELAX, IT’S NATURAL'",
    "CLIENT: 'BRO, THAT WAS YOU!'",
    'PLOT TWIST: CHECK HIS PANT LEG!',
    '100% NATURAL SPA EXPERIENCE',
)

def hud(size,cut):
    w,h=size
    layer=Image.new('RGBA',size);draw=ImageDraw.Draw(layer)
    box=(round(w*.061),round(h*.022),round(w*.939),round(h*.066))
    draw.rounded_rectangle(box,radius=round(h*.016),fill='#0d1826',outline='#cda964',width=max(1,round(w/380)))
    font_size=round(w*.035)
    while True:
        font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',font_size)
        if draw.textlength(TITLES[cut],font=font)<w*.81:break
        font_size-=1
    draw.text((w*.5,(box[1]+box[3])*.5),TITLES[cut],font=font,anchor='mm',fill='#fffbf1')
    return layer

def compose(image,overlay):
    image=image.convert('RGB')
    image.paste(overlay,(0,0),overlay)
    return image

def sheet():
    w,h=270,480
    result=Image.new('RGB',(w*3,(h+22)*2),'#171615')
    draw=ImageDraw.Draw(result)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14)
    for cut,frame in enumerate(STILLS):
        image=Image.open(OUT/'stills_v2'/f'f{frame:04}.png')
        frame_image=compose(image,hud(image.size,cut)).resize((w,h),Image.Resampling.LANCZOS)
        x=cut%3*w;y=cut//3*(h+22)
        result.paste(frame_image,(x,y));draw.text((x+7,y+h+3),f'Cut {cut+1}  |  Frame {frame}',font=font,fill='#fff5e6')
    result.save(OUT/'sheet_v2.jpg',quality=94)

def video():
    destination=OUT/'spa_fart_twist_v2_master.mp4'
    temp=OUT/'spa_fart_twist_v2_encoding.mp4'
    size=(1080,1920)
    overlays=[hud(size,i) for i in range(len(TITLES))]
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-',
             '-i',str(OUT/'audio_master.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','17',
             '-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(temp)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE)
    try:
        for f in range(1,FRAMES+1):
            cut=next(i for i in range(len(TITLES)) if BOUNDS[i]<=f<BOUNDS[i+1])
            with Image.open(OUT/'frames_v2'/f'f{f:04}.png') as frame:
                if frame.size!=size:raise ValueError(f'Frame {f} has size {frame.size}')
                process.stdin.write(compose(frame,overlays[cut]).tobytes())
        process.stdin.close()
        if process.wait():raise RuntimeError('FFmpeg encode failed')
    except BaseException:
        if process.poll() is None:process.terminate()
        process.wait()
        raise
    temp.replace(destination)
    shot_ranges=[dict(id=i+1,a=a-1,b=b-1) for i,(a,b) in enumerate(zip(BOUNDS,BOUNDS[1:]))]
    (OUT/'shots_v2.json').write_text(json.dumps(dict(shots=shot_ranges),indent=2))
    subprocess.run([sys.executable,str(ROOT/'scripts'/'short_qa.py'),str(destination),str(OUT/'qa_v2'),str(OUT/'shots_v2.json')],check=True)

if __name__=='__main__':
    sheet() if sys.argv[1]=='sheet' else video()
