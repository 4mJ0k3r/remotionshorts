"""Mux the corrected opening with untouched later source frames and narration."""
import json
import struct
import subprocess
import sys
import time
from PIL import Image,ImageDraw,ImageFont
from timeline import OUT,ROOT,FRAMES,STILLS

def frame_path(f):
    return OUT/('frames_revision2' if f<=416 else 'frames_preview')/f'f{f:04}.png'

def sheet():
    canvas=Image.new('RGB',(1080,2016),'#17191d');d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14)
    for i,f in enumerate(STILLS):
        with Image.open(frame_path(f)) as im:thumb=im.resize((270,480),Image.Resampling.LANCZOS)
        x=i%4*270;y=i//4*504;canvas.paste(thumb,(x,y))
        d.text((x+8,y+484),f'f{f:04}  |  {(f-1)/30:.2f}s',font=font,fill='#eee3cd')
    canvas.save(OUT/'sheet_revision2.jpg',quality=94)

def video():
    temp=OUT/'v2_encoding.mp4';dest=OUT/'commode_sniper_v2_preview.mp4'
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','image2pipe','-c:v','png','-r','30','-i','-',
        '-i',str(OUT/'audio_master.wav'),'-frames:v',str(FRAMES),'-t','54.50','-map','0:v','-map','1:a',
        '-c:v','libx264','-threads','2','-preset','fast','-crf','19','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','192k','-movflags','+faststart',str(temp)],stdin=subprocess.PIPE)
    try:
        for f in range(1,FRAMES+1):
            deadline=time.monotonic()+180
            while True:
                try:data=frame_path(f).read_bytes();break
                except OSError:
                    if time.monotonic()>deadline:raise RuntimeError(f'Missing revised frame {f}')
                    time.sleep(.2)
            if struct.unpack('>II',data[16:24])!=(540,960):raise ValueError(f'Bad resolution at {f}')
            p.stdin.write(data)
        p.stdin.close()
        if p.wait():raise RuntimeError('Revised encode failed')
    except BaseException:
        if p.poll() is None:p.terminate()
        p.wait();raise
    temp.replace(dest);sheet()
    provenance={'movie':dest.name,'scene':'commode_sniper_v2.blend','frames':1635,'fps':30,'duration':54.5,
        'ranges':[{'a':1,'b':416,'source':'frames_revision2','change':'Natural side/back stance; higher waist source; pressure struggle and alternate grip slips'},
                  {'a':417,'b':1635,'source':'frames_preview','change':'Original approved later cuts retained'}],
        'text_overlays':False,'audio':'Same normalized Hindi audio_master.wav'}
    (OUT/'revision2_provenance.json').write_text(json.dumps(provenance,indent=2))
    subprocess.run([sys.executable,str(ROOT/'scripts'/'short_qa.py'),str(dest),str(OUT/'qa_revision2'),str(OUT/'shots.json')],check=True)
    print(dest)

if __name__=='__main__':video()
