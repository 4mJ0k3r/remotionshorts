"""Exclusive local Blender launcher, sheet assembly, and final audio packaging."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=Path(__file__).resolve().parent
OUT=ROOT/'renders/inside_brain_dog'
BLENDER=ROOT/'renders/caveman_toilet/.blender_cli/blender.exe'
LOCK=ROOT/'.blender_gpu.lock'


def render(phase):
    owner=str(uuid.uuid4())
    payload={'project':'inside_brain_dog','pid':os.getpid(),'owner':owner,'phase':phase}
    try:
        descriptor=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError:
        raise SystemExit('Blender GPU lock is occupied. Retry after the current owner finishes.')
    with os.fdopen(descriptor,'w') as file:
        json.dump(payload,file)
    try:
        processes=subprocess.run(['powershell','-NoProfile','-Command',"Get-CimInstance Win32_Process -Filter \"Name = 'blender.exe'\" | Select-Object -ExpandProperty CommandLine"],capture_output=True,text=True,check=True)
        if any(' -b ' in line or ' --background ' in line for line in processes.stdout.splitlines()):
            raise RuntimeError('Another background Blender process is active.')
        command=[str(BLENDER),'-b','--factory-startup','--python-exit-code','1']
        if phase=='build':
            command+=['--python',str(SCRIPTS/'build_inside_brain_dog.py')]
        elif phase=='verify':
            command+=[str(ROOT/'inside_brain_dog.blend'),'--python',str(SCRIPTS/'verify_scene.py')]
        else:
            command+=[str(ROOT/'inside_brain_dog.blend'),'--python',str(SCRIPTS/'render_scene.py'),'--',phase]
        environment=os.environ.copy()
        environment['BLENDER_USER_RESOURCES']=str(OUT/'.blender_user')
        with (OUT/f'{phase}.log').open('w',encoding='utf-8') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=environment)
            print(f'{phase} started, Blender PID {process.pid}',flush=True)
            try:
                code=process.wait()
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                raise
        if code:
            raise RuntimeError((OUT/f'{phase}.log').read_text(encoding='utf-8',errors='replace')[-6000:])
        print(f'{phase} complete',flush=True)
    finally:
        if LOCK.exists() and json.loads(LOCK.read_text()).get('owner')==owner:
            LOCK.unlink()


def sheet():
    from PIL import Image,ImageDraw,ImageFont
    image=Image.new('RGB',(3*540+32,2*996+24),'#101d29')
    draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',22)
    for index,frame in enumerate([20,50,85,110,135,155]):
        x=8+(index%3)*548
        y=8+(index//3)*1004
        draw.text((x+8,y+5),f'Cut {1 if frame<66 else 2 if frame<124 else 3}  |  f{frame}',fill='white',font=font)
        tile=Image.open(OUT/'calibration'/f'{frame:04}.png').convert('RGB')
        assert tile.size==(540,960)
        image.paste(tile,(x,y+36))
    destination=OUT/('sheet_v2.jpg' if (OUT/'sheet_v1.jpg').exists() else 'sheet_v1.jpg')
    image.save(destination,quality=94)


def mux():
    frames=list((OUT/'frames').glob('frame_*.png'))
    assert len(frames)==165,len(frames)
    final=OUT/'inside_brain_dog_master.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-start_number','1','-i',str(OUT/'frames'/'frame_%04d.png'),'-i',str(OUT/'narration.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','5.5','-movflags','+faststart',str(final)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(final)],text=True))
    video=next(item for item in probe['streams'] if item['codec_type']=='video')
    assert (video['width'],video['height'],int(video['nb_frames']),video['r_frame_rate'])==(540,960,165,'30/1')
    assert abs(float(probe['format']['duration'])-5.5)<.03
    (OUT/'delivery_specs.json').write_text(json.dumps(probe,indent=2))
    (OUT/'shots.json').write_text(json.dumps({'shots':[{'id':1,'a':0,'b':65},{'id':2,'a':65,'b':123},{'id':3,'a':123,'b':165}]}))
    subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(final),str(OUT/'qa'),str(OUT/'shots.json')],check=True)
    print(final)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['build','calibration','movie','sheet','mux','verify'])
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.phase=='sheet':
        sheet()
    elif args.phase=='mux':
        mux()
    else:
        render(args.phase)
