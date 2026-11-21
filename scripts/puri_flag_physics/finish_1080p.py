"""Mux and inspect native HD frames without adding screen graphics."""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

PROJECT=Path(__file__).resolve().parent.name
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders'/PROJECT
total,tag={'commode_sniper':(1635,'commode_sniper_v2_1080p'),'puri_flag_physics':(2211,'puri_flag_physics_sky_v2_1080p')}[PROJECT]
folder=OUT/(tag+'_frames')
for frame in range(1,total+1):
    with Image.open(folder/f'f{frame:04}.png') as image:
        assert image.size==(1080,1920)
        image.verify()
duration=total/30
final=OUT/(tag+'_master.mp4')
temp=OUT/(tag+'_encoding.mp4')
subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-start_number','1','-i',str(folder/'f%04d.png'),'-i',str(OUT/'audio_master.wav'),'-map','0:v:0','-map','1:a:0','-frames:v',str(total),'-t',str(duration),'-c:v','libx264','-threads','4','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(temp)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(temp)],text=True))
video=next(stream for stream in probe['streams'] if stream['codec_type']=='video')
audio=next(stream for stream in probe['streams'] if stream['codec_type']=='audio')
assert (video['width'],video['height'],int(video['nb_frames']),video['r_frame_rate'])==(1080,1920,total,'30/1')
assert abs(float(video['duration'])-duration)<.001
assert abs(float(audio['duration'])-duration)<.05
temp.replace(final)
(OUT/(tag+'_specs.json')).write_text(json.dumps(probe,indent=2))
frames=[1+round(i*(total-1)/19) for i in range(20)]
canvas=Image.new('RGB',(1080,2520),'#141a20')
draw=ImageDraw.Draw(canvas)
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',14)
for i,frame in enumerate(frames):
    x=i%4*270;y=i//4*504
    with Image.open(folder/f'f{frame:04}.png') as image:
        canvas.paste(image.resize((270,480),Image.Resampling.LANCZOS),(x,y))
    draw.text((x+8,y+484),f'{(frame-1)/30:.2f}s | f{frame:04}',font=font,fill='#efe9dc')
canvas.save(OUT/(tag+'_sheet.jpg'),quality=94)
qa=OUT/('qa_'+tag)
subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(final),str(qa),str(OUT/'shots.json')],check=True)
(OUT/(tag+'_delivery.json')).write_text(json.dumps({'state':'complete','movie':str(final),'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'finished':time.time(),'width':1080,'height':1920,'fps':30,'frames':total,'duration':duration,'samples':16},indent=2))
print('HD_MASTER_READY',final,flush=True)

