"""Owner-checked Blender lock and calibration image assembly."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=Path(__file__).resolve().parent
OUT=ROOT/'renders/elevator_leak'
BLENDER=Path(os.environ.get('BLENDER_EXE','D:/tools/Blender/4.2.23/blender.exe'))
LOCK=ROOT/'.blender_gpu.lock'
LABELS=[('1A  Panic close-up',50),('1B  Bloated suit',130),('1B  Door-peek cabin',190),('1C  Floors 45-90',260),('1D  Three-quarter panic',320),('2A  Upward whistle',400),('2B  Commuter reaction',510),('3A  Blame / baby response',570),('3B  Raised gas mask',690),('4A  Rear clamp',885),('4B  Trouser-cuff exit',970),('4C  Boss shoe contact',1090),('5A  Chocolate excuse',1210),('5B  Boss order',1340),('6A  Emergency press',1460),('6B  High-corner CCTV',1560),('6C  Boss inspection',1710),('6D  Second cuff exit',1840),('6D  Macro payoff',1910),('6E  Double leak',2050)]


def other_blenders():
    result=subprocess.run(['powershell','-NoProfile','-Command',"Get-CimInstance Win32_Process -Filter \"Name = 'blender.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],capture_output=True,text=True,check=True)
    if not result.stdout.strip():
        return False
    records=json.loads(result.stdout)
    if isinstance(records,dict):
        records=[records]
    return any(any(argument in ('-b','--background') for argument in (record.get('CommandLine') or '').split()) for record in records)


def launch(phase,start=None,end=None,version=2,resolution=540):
    tag=f'v{version}' if resolution==540 else f'v{version}_{resolution}p'
    owner=str(uuid.uuid4())
    claimed=False
    while not claimed:
        if LOCK.exists() and time.time()-LOCK.stat().st_mtime>25*60 and not other_blenders():
            raise RuntimeError('The GPU lock appears stale. Ask its owner to release it; this runner will not delete it.')
        if LOCK.exists() or other_blenders():
            print('Waiting for the current Blender owner to finish.',flush=True)
            time.sleep(15)
            continue
        try:
            descriptor=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:
            continue
        with os.fdopen(descriptor,'w') as file:
            json.dump({'project':'elevator_leak','phase':phase,'pid':os.getpid(),'owner':owner},file)
        claimed=True
    try:
        if other_blenders():
            raise RuntimeError('A Blender process appeared during lock acquisition. Retry safely.')
        command=[str(BLENDER),'-b','--factory-startup','--python-exit-code','1']
        if phase=='build':
            command+=['--python',str(SCRIPT/'build_elevator_leak.py')]
        elif phase=='verify':
            command+=[str(ROOT/'elevator_leak.blend'),'--python',str(SCRIPT/'verify_scene.py')]
        elif phase=='prepare_1080p':
            command+=[str(ROOT/'elevator_leak.blend'),'--python',str(SCRIPT/'prepare_1080p.py')]
        elif phase=='movie':
            command+=[str(OUT/f'elevator_leak_{tag}_render_source.blend'),'--python',str(SCRIPT/'render_movie.py'),'--',str(start),str(end),str(version),str(resolution)]
        else:
            command+=[str(ROOT/'elevator_leak.blend'),'--python',str(SCRIPT/'render_calibration.py'),'--',phase]
        environment=os.environ.copy()
        environment['BLENDER_USER_RESOURCES']=str(OUT/'.blender_user')
        temporary=OUT/'tmp'
        temporary.mkdir(exist_ok=True)
        environment['TEMP']=str(temporary)
        environment['TMP']=str(temporary)
        log_name=f'movie_{tag}_{start:04}_{end:04}.log' if phase=='movie' else phase+'.log'
        with (OUT/log_name).open('w',encoding='utf-8') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=environment)
            print(f'{phase}: Blender PID {process.pid}',flush=True)
            try:
                last_reported=None
                while process.poll() is None:
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        progress_path=OUT/f'movie_{tag}_progress.json'
                        if phase=='movie' and progress_path.exists():
                            try:
                                progress=json.loads(progress_path.read_text())
                            except (OSError,json.JSONDecodeError):
                                continue
                            frame=progress.get('frame')
                            if frame!=last_reported:
                                print(f'Rendered {frame}/2145 frames ({100*frame/2145:.1f}%).',flush=True)
                                last_reported=frame
                code=process.returncode
            except KeyboardInterrupt:
                process.terminate()
                process.wait()
                raise
        if code:
            raise RuntimeError((OUT/log_name).read_text(encoding='utf-8',errors='replace')[-5000:])
        print(phase+' complete',flush=True)
    finally:
        if LOCK.exists() and json.loads(LOCK.read_text()).get('owner')==owner:
            LOCK.unlink()


def ink_sheet():
    result=Image.new('RGB',(1100,2000),'#121b27')
    draw=ImageDraw.Draw(result)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',22)
    for row,shot in enumerate(['medium','close']):
        for column,state in enumerate(['off','on']):
            x=column*550
            y=row*1000
            draw.text((x+12,y+8),f'{shot.upper()} / SET INK {state.upper()}',font=font,fill='white')
            result.paste(Image.open(OUT/'ink_tests'/f'{shot}_{state}.png').convert('RGB'),(x+5,y+35))
    result.save(OUT/'set_ink_ab_v1.jpg',quality=95)


def sheet(version=2):
    result=Image.new('RGB',(4*552+12,5*1004+12),'#121b27')
    draw=ImageDraw.Draw(result)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',22)
    labels=[('6C  Turning step',1640) if version==3 and frame==1710 else (name,frame) for name,frame in LABELS]
    directory=OUT/('calibration_v3' if version==3 else 'calibration')
    for index,(name,frame) in enumerate(labels):
        x=12+(index%4)*552
        y=12+(index//4)*1004
        draw.text((x+6,y+6),f'{name} | f{frame}',font=font,fill='white')
        if frame==570:
            for offset,subframe in enumerate([570,620]):
                img=Image.open(directory/f'{subframe:04}.png').convert('RGB')
                # Two complete views share one tile, retaining their full framing.
                img.thumbnail((540,478),Image.Resampling.LANCZOS)
                result.paste(img,(x+(540-img.width)//2,y+36+offset*480))
        else:
            result.paste(Image.open(directory/f'{frame:04}.png').convert('RGB'),(x,y+36))
    target=OUT/f'sheet_v{version}.jpg'
    result.save(target,quality=94)
    print(target)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['build','ink_tests','calibration','patch','motion_checks','cctv_patch','calibration_v3','rig_checks_v3','ink_sheet','sheet','sheet_v3','verify','prepare_1080p'])
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.phase in ['sheet','sheet_v3']:
        sheet(3 if args.phase=='sheet_v3' else 2)
    elif args.phase=='ink_sheet':
        ink_sheet()
    else:
        launch(args.phase)
