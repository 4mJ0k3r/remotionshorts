"""Text-free master and review sheets with captions outside the video frames."""
import sys
import struct
import subprocess
import time
from PIL import Image,ImageDraw,ImageFont
from timeline import OUT,ROOT,STILLS,EXTRA_STILLS,FRAMES

def make_sheet(frames,name,columns=4):
    canvas=Image.new('RGB',(270*columns,((len(frames)+columns-1)//columns)*504),'#15191d');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14)
    for i,f in enumerate(frames):
        directory='frames_anatomy_v2' if (OUT/'frames_anatomy_v2'/f'f{f:04}.png').exists() else 'stills_anatomy_v2'
        with Image.open(OUT/directory/f'f{f:04}.png') as im:thumb=im.resize((270,480),Image.Resampling.LANCZOS)
        x=i%columns*270;y=i//columns*504;canvas.paste(thumb,(x,y));draw.text((x+8,y+484),f'f{f:04} | {(f-1)/30:.2f}s',font=font,fill='#e9dfca')
    canvas.save(OUT/name,quality=94)

def sheet():
    make_sheet(STILLS,'sheet_v2.jpg')
    make_sheet(tuple(sorted(set(STILLS+EXTRA_STILLS+(1,42,82,184,234,344,348,400,615,1239,1539,1635)))),'sheet_anatomy_checks.jpg')

def video():
    temp=OUT/'anatomy_encoding.mp4';dest=OUT/'commode_sniper_v2_master.mp4'
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','image2pipe','-c:v','png','-r','30','-i','-',
        '-i',str(OUT/'audio_master.wav'),'-map','0:v','-map','1:a','-frames:v',str(FRAMES),'-t','54.50',
        '-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(temp)],stdin=subprocess.PIPE)
    try:
        for f in range(1,FRAMES+1):
            path=OUT/'frames_anatomy_v2'/f'f{f:04}.png';deadline=time.monotonic()+180
            while True:
                try:data=path.read_bytes();break
                except OSError:
                    if time.monotonic()>deadline:raise RuntimeError(f'Missing master frame {f}')
                    time.sleep(.2)
            if struct.unpack('>II',data[16:24])!=(540,960):raise ValueError(f'Incorrect frame size {f}')
            p.stdin.write(data)
        p.stdin.close()
        if p.wait():raise RuntimeError('Master encoding failed')
    except BaseException:
        if p.poll() is None:p.terminate()
        p.wait();raise
    temp.replace(dest);sheet()
    subprocess.run([sys.executable,str(ROOT/'scripts'/'short_qa.py'),str(dest),str(OUT/'qa_anatomy_master'),str(OUT/'shots.json')],check=True)
    print(dest)

if __name__=='__main__':sheet() if sys.argv[1]=='sheet' else video()
