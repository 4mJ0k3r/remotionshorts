"""Paint a soft cloud backdrop and export the clean 20-second review."""
import json
import subprocess
import sys
from PIL import Image,ImageFilter
import numpy as np
from timeline import OUT, ROOT

def sky():
    w,h=2048,1536;rng=np.random.default_rng(185)
    field=np.zeros((h,w),np.float32)
    for nx,ny,weight in [(12,10,.58),(30,20,.28),(70,45,.14)]:
        noise=Image.fromarray((rng.random((ny,nx))*255).astype(np.uint8))
        field+=np.asarray(noise.resize((w,h),Image.Resampling.BICUBIC),dtype=np.float32)/255*weight
    vertical=np.linspace(1,0,h)[:,None,None]
    horizon=np.array([178,209,224],np.float32);upper=np.array([55,121,177],np.float32)
    gradient=horizon+(upper-horizon)*vertical**.65
    bands=.7+.3*np.sin(np.linspace(0,5*np.pi,h))[:,None]
    alpha=np.clip((field-.49)/.15,0,1)*bands*.90
    alpha=np.asarray(Image.fromarray((alpha*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)),dtype=np.float32)/255
    cloud=np.array([243,239,226],np.float32)
    rgb=gradient*(1-alpha[:,:,None])+cloud*alpha[:,:,None]
    Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).save(OUT/'sprites'/'sky_v2.png')

def encode():
    dest=OUT/'puri_flag_physics_sky_v2_20s_360p.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-start_number','1','-i',str(OUT/'frames_sky_v2_360p'/'f%04d.png'),
        '-i',str(OUT/'audio_master.wav'),'-frames:v','600','-t','20','-map','0:v','-map','1:a',
        '-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k',
        '-movflags','+faststart',str(dest)],check=True)
    shots=[{'id':i+1,'a':a,'b':b} for i,(a,b) in enumerate(((0,182),(182,355),(355,554),(554,600)))]
    mapping=OUT/'shots_sky_v2_20s.json';mapping.write_text(json.dumps({'shots':shots},indent=2))
    subprocess.run([sys.executable,str(ROOT/'scripts'/'short_qa.py'),str(dest),str(OUT/'qa_sky_v2_20s'),str(mapping)],check=True)
    print(dest)

if __name__=='__main__':sky() if sys.argv[1]=='sky' else encode()
