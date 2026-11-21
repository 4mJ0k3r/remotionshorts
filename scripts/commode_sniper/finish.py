"""Contact sheet review labels stay outside frames; delivered video has no text."""
import json
import subprocess
import sys
import time
import struct
from PIL import Image,ImageDraw,ImageFont
from timeline import OUT,ROOT,FRAMES,BOUNDS,STILLS,EXTRA_STILLS

def make_sheet(frames,filename,columns=4):
    tw,th=270,480;rows=(len(frames)+columns-1)//columns
    canvas=Image.new('RGB',(tw*columns,(th+24)*rows),'#17191d');d=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14)
    for i,f in enumerate(frames):
        directory=next(folder for folder in ('frames_preview','stills_v3','stills_v2','stills_v1') if (OUT/folder/f'f{f:04}.png').exists())
        path=OUT/directory/f'f{f:04}.png'
        with Image.open(path) as im:frame=im.resize((tw,th),Image.Resampling.LANCZOS)
        x=i%columns*tw;y=i//columns*(th+24);canvas.paste(frame,(x,y))
        d.text((x+8,y+th+4),f'f{f:04}  |  {(f-1)/30:05.2f}s',font=font,fill='#efe6d2')
    canvas.save(OUT/filename,quality=94)

def sheet():
    make_sheet(STILLS,'sheet_v1.jpg')
    make_sheet(tuple(sorted(set(STILLS+EXTRA_STILLS))),'sheet_contacts_v1.jpg')
    if (OUT/'stills_v2').exists():make_sheet(STILLS,'sheet_v2.jpg')
    print(OUT/'sheet_v1.jpg')

def video():
    destination=OUT/'commode_sniper_preview.mp4'
    temporary=OUT/'preview_encoding.mp4'
    process=subprocess.Popen(['ffmpeg','-v','error','-y','-f','image2pipe','-c:v','png','-r','30','-i','-',
        '-i',str(OUT/'audio_master.wav'),'-frames:v',str(FRAMES),'-t','54.50','-map','0:v','-map','1:a',
        '-c:v','libx264','-threads','2','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(temporary)],stdin=subprocess.PIPE)
    try:
        for f in range(1,FRAMES+1):
            path=OUT/'frames_preview'/f'f{f:04}.png';deadline=time.monotonic()+180
            while True:
                try:
                    data=path.read_bytes();break
                except OSError:
                    if time.monotonic()>deadline:raise RuntimeError(f'Render stopped before frame {f}')
                    time.sleep(.2)
            if struct.unpack('>II',data[16:24])!=(540,960):raise ValueError(f'Wrong frame resolution {f}')
            process.stdin.write(data)
        process.stdin.close()
        if process.wait():raise RuntimeError('Preview encoding failed')
    except BaseException:
        if process.poll() is None:process.terminate()
        process.wait();raise
    temporary.replace(destination)
    subshots=(1,43,84,141,186,236,306,346,417,618,723,804,849,905,1083,1171,1248,1362,1457,1539,1636)
    mapping={'shots':[{'id':i+1,'a':a-1,'b':b-1} for i,(a,b) in enumerate(zip(subshots,subshots[1:]))]}
    (OUT/'shots.json').write_text(json.dumps(mapping,indent=2))
    subprocess.run([sys.executable,str(ROOT/'scripts'/'short_qa.py'),str(destination),str(OUT/'qa_preview'),str(OUT/'shots.json')],check=True)
    print(destination)

if __name__=='__main__':sheet() if sys.argv[1]=='sheet' else video()
