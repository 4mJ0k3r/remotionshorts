"""Calibration-only controller; deliberately has no movie-render command."""
import os,sys,json,subprocess,time,uuid
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=ROOT/'renders/crorepati_poop_love';LOCK=ROOT/'.blender_gpu.lock'
BLENDER=Path(os.environ.get('BLENDER_EXE','D:/tools/Blender/4.2.23/blender.exe'))
AUDIO=Path(os.environ.get('NARRATION_AUDIO','C:/Users/lavis/Downloads/ElevenLabs_2026-11-15T19_21_51_Viraj - Energetic & Clear Hindi Narrator_pvc_s30_sim75_v4.mp3'))
sys.path.insert(0,str(HERE));from story import SHOTS

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,str(HERE/'assets.py')],check=True)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(AUDIO),'-f','f32le','-ac','1','-ar','24000','pipe:1']);audio=np.frombuffer(raw,dtype=np.float32)
    values=[]
    for f in range(2124):
        span=audio[f*800:(f+1)*800];values.append(float(np.sqrt(np.mean(span*span))) if len(span) else 0)
    env=np.asarray(values);env=np.clip((env-.01)/max(.01,np.percentile(env,94)-.01),0,1)
    for f in range(1,len(env)):env[f]=.65*env[f]+.35*env[f-1]
    (OUT/'audio_env.json').write_text(json.dumps([round(float(v),4) for v in env]))
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(AUDIO),'-af','apad','-t','70.8','-ar','48000','-ac','2',str(OUT/'narration.wav')],check=True)
    (OUT/'shot_plan.json').write_text(json.dumps({'fps':30,'frames':2124,'duration':70.8,'authorized_stage':'calibration_only','shots':[{'id':n,'a':a,'b':b-1,'peak':p} for n,a,b,p in SHOTS]},indent=2))

def others():
    result=subprocess.run(['powershell','-NoProfile','-Command','Get-CimInstance Win32_Process -Filter "Name=\'blender.exe\'" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress'],capture_output=True,text=True,check=True)
    rows=json.loads(result.stdout) if result.stdout.strip() else []
    if isinstance(rows,dict):rows=[rows]
    return [r for r in rows if any(arg in (r.get('CommandLine') or '').split() for arg in ['-b','--background'])]

def launch(phase):
    OUT.mkdir(parents=True,exist_ok=True);owner=str(uuid.uuid4())
    while True:
        if LOCK.exists() or others():print('Waiting for current GPU owner.',flush=True);time.sleep(15);continue
        try:fd=os.open(LOCK,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:continue
        with os.fdopen(fd,'w') as file:json.dump({'project':'crorepati_poop_love','owner':owner,'pid':os.getpid(),'phase':phase},file)
        break
    process=None
    try:
        if others():raise RuntimeError('Another Blender started; retry after it finishes.')
        command=[str(BLENDER),'-b','--factory-startup','--python-exit-code','1']
        if phase=='build':command+=['--python',str(HERE/'build_crorepati.py')]
        else:command+=[str(ROOT/'crorepati_poop_love_v2.blend'),'--python',str(HERE/'calibrate.py'),'--',phase]
        env=os.environ.copy();env['TEMP']=env['TMP']=str(OUT/'tmp');env['BLENDER_USER_RESOURCES']=str(OUT/'.blender_user');(OUT/'tmp').mkdir(exist_ok=True)
        with (OUT/(phase+'.log')).open('w',encoding='utf-8') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env);print(phase,'BLENDER_PID',process.pid,flush=True);process.wait()
        if process.returncode:raise RuntimeError((OUT/(phase+'.log')).read_text(errors='replace')[-6000:])
    except KeyboardInterrupt:
        if process and process.poll() is None:process.terminate();process.wait()
        raise
    finally:
        if LOCK.exists() and json.loads(LOCK.read_text()).get('owner')==owner:LOCK.unlink()

def sheet():
    output=Image.new('RGB',(6*552+12,3*1004+12),'#152330');draw=ImageDraw.Draw(output);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',22)
    for i,(cut,a,b,f) in enumerate(SHOTS):
        x=12+(i%6)*552;y=12+(i//6)*1004;draw.text((x+6,y+5),f'CUT {cut:02} | f{f}',font=font,fill='white')
        im=Image.open(OUT/'calibration_v2'/f'{f:04}.png').convert('RGB');assert im.size==(540,960);output.paste(im,(x,y+35))
    output.save(OUT/'sheet_v2.jpg',quality=94);print('CALIBRATION_SHEET',OUT/'sheet_v2.jpg')

if __name__=='__main__':
    phase=sys.argv[1]
    if phase=='build':prepare();launch('build')
    elif phase=='sheet':launch('sheet');sheet()
    elif phase=='verify':launch('verify')
    else:raise SystemExit('Allowed commands: build, sheet, verify. Full video requires visual audit approval.')
