"""Owner-checked render launcher and audio/QA preparation for this short."""
import sys, os, json, subprocess, time, uuid, hashlib, shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];SCRIPT=Path(__file__).resolve().parent
OUT=ROOT/'renders/sendha_namak_science';LOCK=ROOT/'.blender_gpu.lock'
BLENDER=Path(os.environ.get('BLENDER_EXE') or shutil.which('blender') or 'D:/tools/Blender/4.2.23/blender.exe')
AUDIO=Path(os.environ.get('NARRATION_AUDIO',str(ROOT/'public/sendha_namak_science/audio.mp3')))
FRAMES=[60,120,240,360,560,800,960,1210,1298,1415,1585,1710]
LABELS=['1A / Salted strawberry','1A / Pictorial chart','1B / Phone warning','1C / Panic & meters','2A / Mouth bacteria','2B / Tissue micro-cuts','2C / Pitchfork invasion','2D / Virus conquest','3A / Questioning shrug','3B / Raita & cucumber','3C / Tongue blocked','3D / Clinic faint']

def others():
    p=subprocess.run(['powershell','-NoProfile','-Command','Get-CimInstance Win32_Process -Filter "Name=\'blender.exe\'" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress'],capture_output=True,text=True,check=True)
    rows=json.loads(p.stdout) if p.stdout.strip() else []
    if isinstance(rows,dict):rows=[rows]
    return [r for r in rows if any(t in (r.get('CommandLine') or '').split() for t in ['-b','--background'])]

def launch(mode,a=None,b=None):
    if not BLENDER.is_file():raise FileNotFoundError('Set BLENDER_EXE to your installed Blender 4.2 executable.')
    OUT.mkdir(parents=True,exist_ok=True);owner=str(uuid.uuid4())
    while True:
        if LOCK.exists() or others():
            print('Waiting for the active GPU owner.',flush=True);time.sleep(15);continue
        try:fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:continue
        with os.fdopen(fd,'w') as file:json.dump({'project':'sendha_namak_science','owner':owner,'pid':os.getpid(),'phase':mode},file)
        break
    process=None
    try:
        if others():raise RuntimeError('Another Blender appeared; retry after it finishes.')
        command=[str(BLENDER),'-b','--factory-startup','--python-exit-code','1']
        if mode=='build':command+=['--python',str(SCRIPT/'build_sendha_namak.py')]
        else:command+=[str(OUT/'sendha_namak_v2_render_source.blend' if mode=='movie' else ROOT/'sendha_namak_science.blend'),'--python',str(SCRIPT/'render.py'),'--',mode]+([] if a is None else [str(a),str(b)])
        env=os.environ.copy();env['TEMP']=env['TMP']=str(OUT/'tmp');env['BLENDER_USER_RESOURCES']=str(OUT/'.blender_user');(OUT/'tmp').mkdir(exist_ok=True)
        logpath=OUT/('v2_'+mode+('' if a is None else f'_{a:04}_{b:04}')+'.log')
        with logpath.open('w',encoding='utf-8') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
            print(mode,'BLENDER_PID',process.pid,flush=True)
            while process.poll() is None:
                try:process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    if mode=='movie' and (OUT/'v2_progress.json').exists():print((OUT/'v2_progress.json').read_text(),flush=True)
            if process.returncode:raise RuntimeError(logpath.read_text(errors='replace')[-5500:])
    except KeyboardInterrupt:
        if process and process.poll() is None:process.terminate();process.wait()
        raise
    finally:
        if LOCK.exists() and json.loads(LOCK.read_text()).get('owner')==owner:LOCK.unlink()

def prepare():
    if not AUDIO.is_file():raise FileNotFoundError('Provide narration via NARRATION_AUDIO or public/sendha_namak_science/audio.mp3.')
    OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,str(SCRIPT/'assets.py')],check=True)
    raw=subprocess.run(['ffmpeg','-v','error','-i',str(AUDIO),'-f','f32le','-ac','1','-ar','24000','pipe:1'],stdout=subprocess.PIPE,check=True).stdout
    audio=np.frombuffer(raw,dtype=np.float32);env=[]
    for f in range(1728):
        span=audio[f*800:(f+1)*800];env.append(float(np.sqrt(np.mean(span*span))) if len(span) else 0)
    env=np.asarray(env);env=np.clip((env-.012)/max(.01,np.percentile(env,94)-.012),0,1)
    for i in range(1,len(env)):env[i]=.64*env[i]+.36*env[i-1]
    (OUT/'audio_env.json').write_text(json.dumps([round(float(v),4) for v in env]))
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(AUDIO),'-af','apad','-t','57.6','-ar','48000','-ac','2',str(OUT/'narration.wav')],check=True)
    (OUT/'shots.json').write_text(json.dumps({'shots':[{'id':n,'a':a-1,'b':b-1} for n,a,b in [('1A',1,156),('1B',156,266),('1C',266,447),('2A_zoom',447,491),('2A',491,633),('2B',633,855),('2C',855,1023),('2D',1023,1263),('3A',1263,1326),('3B',1326,1481),('3C',1481,1634),('3D',1634,1729)]]},indent=2))

def sheet():
    result=Image.new('RGB',(4*552+12,3*1004+12),'#172331');d=ImageDraw.Draw(result);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',21)
    for i,(f,label) in enumerate(zip(FRAMES,LABELS)):
        x=12+(i%4)*552;y=12+(i//4)*1004;d.text((x,y+3),f'{label} | {f}',font=font,fill='white')
        im=Image.open(OUT/'calibration_v2'/f'{f:04}.png').convert('RGB');assert im.size==(540,960);result.paste(im,(x,y+35))
    result.save(OUT/'sheet_v2.jpg',quality=94)

def movie():
    # Freeze build/audio identity before rendering; never mix cached source revisions.
    source=ROOT/'sendha_namak_science.blend';identity={'blend':hashlib.sha256(source.read_bytes()).hexdigest(),'audio':hashlib.sha256((OUT/'narration.wav').read_bytes()).hexdigest(),'frames':1728,'size':[540,960],'fps':30}
    manifest=OUT/'v2_manifest.json'
    if manifest.exists() and json.loads(manifest.read_text())!=identity:raise RuntimeError('Source changed: use a fresh frame directory before resuming.')
    manifest.write_text(json.dumps(identity,indent=2))
    frozen=OUT/'sendha_namak_v2_render_source.blend'
    if not frozen.exists():shutil.copy2(source,frozen)
    assert hashlib.sha256(frozen.read_bytes()).hexdigest()==identity['blend']
    folder=OUT/'v2_frames';folder.mkdir(exist_ok=True)
    for start in range(1,1729,144):
        end=min(1728,start+143);missing=[]
        for f in range(start,end+1):
            p=folder/f'frame_{f:04}.png'
            try:
                with Image.open(p) as im:
                    assert im.size==(540,960);im.verify()
            except (OSError,AssertionError):missing.append(f)
        if missing:launch('movie',min(missing),end)
    target=OUT/'sendha_namak_v2_master.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-framerate','30','-start_number','1','-i',str(folder/'frame_%04d.png'),'-i',str(OUT/'narration.wav'),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','57.6','-movflags','+faststart',str(target)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video');assert (video['width'],video['height'],int(video['nb_frames']))==(540,960,1728)
    (OUT/'v2_delivery_probe.json').write_text(json.dumps(probe,indent=2))
    subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(target),str(OUT/'qa_v2'),str(OUT/'shots.json')],check=True)
    print('DELIVERED',target,flush=True)

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='build':prepare();launch('build')
    elif mode=='verify':launch('verify')
    elif mode=='sheet':launch('sheet');sheet()
    elif mode=='movie':movie()
