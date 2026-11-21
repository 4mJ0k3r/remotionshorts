"""Exclusive Blender launcher. Never removes another owner's lock."""
import argparse, json, os, re, subprocess, sys, time, uuid
from pathlib import Path

ROOT=Path(r'D:\remotionshorts')
OUT=ROOT/'renders/ancient_condom'
LOCK=ROOT/'.blender_gpu.lock'
BLENDER=ROOT/'renders/billionaire_handkerchief/.blender_cli/blender.exe'

def headless():
    # Process metadata only: no access to the other project's files.
    cmd="Get-CimInstance Win32_Process -Filter \"Name = 'blender.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    r=subprocess.run(['powershell','-NoProfile','-Command',cmd],capture_output=True,text=True,check=True)
    if not r.stdout.strip(): return []
    rows=json.loads(r.stdout)
    if isinstance(rows,dict): rows=[rows]
    return [x for x in rows if re.search(r'(?:^|\s)(?:-b|--background)(?:\s|$)',x.get('CommandLine') or '')]

def sustained_gpu_load():
    busy=[]
    for i in range(3):
        try:
            p=subprocess.run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=8)
            vals=[int(x.strip()) for x in p.stdout.strip().splitlines()[0].split(',')]
            busy.append(vals[0]>=3300 or vals[1]>=85)
        except (OSError,ValueError,IndexError,subprocess.TimeoutExpired): return False
        if not busy[-1]: return False
        if i<2: time.sleep(1)
    return all(busy)

def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',required=True);p.add_argument('--threads',type=int,default=0,help='0 uses all available CPU threads');p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args()
    if not BLENDER.is_file(): raise SystemExit('Isolated Blender executable unavailable: '+str(BLENDER))
    owner=str(uuid.uuid4());claimed=False
    payload={'project':'ancient_condom','pid':os.getpid(),'owner':owner,'phase':a.phase}
    registry=OUT/'logs'/f'active_run_{os.getpid()}.json';stopfile=OUT/'logs'/f'stop_{owner}.request'
    state={**payload,'child_pid':None,'stop_file':str(stopfile),'threads':a.threads}
    registry.write_text(json.dumps(state,indent=2))
    try:
        while not claimed:
            if stopfile.exists():print('Stopped our queued job by request.',flush=True);return
            if LOCK.exists():
                if time.time()-LOCK.stat().st_mtime>1800 and not headless():
                    raise SystemExit('STOP: possible stale GPU lock. Ask user; do not remove it.')
                print('GPU queue: lock held; waiting 15 seconds.',flush=True);time.sleep(15);continue
            if headless() or sustained_gpu_load():
                print('GPU queue: headless Blender or sustained GPU load; waiting 15 seconds.',flush=True);time.sleep(15);continue
            try:
                fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
            except FileExistsError: continue
            with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(payload,f)
            claimed=True
            if headless():
                if json.loads(LOCK.read_text())['owner']==owner:LOCK.unlink()
                claimed=False;time.sleep(15)
        env=os.environ.copy()
        profile=OUT/'.blender_user';profile.mkdir(exist_ok=True)
        env.update({'BLENDER_USER_RESOURCES':str(profile),'BLENDER_USER_CONFIG':str(profile/'config'),'BLENDER_USER_SCRIPTS':str(profile/'scripts'),'BLENDER_USER_DATAFILES':str(profile/'datafiles'),'TEMP':str(OUT/'tmp'),'TMP':str(OUT/'tmp')})
        (OUT/'tmp').mkdir(exist_ok=True)
        args=a.args[1:] if a.args and a.args[0]=='--' else a.args
        cmd=[str(BLENDER),'-b','--factory-startup','--threads',str(a.threads),'--python-exit-code','1']+args
        print('Acquired GPU lock:',json.dumps(payload),flush=True)
        with (OUT/'logs'/('blender_'+a.phase+'.log')).open('a',encoding='utf-8') as log:
            proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,cwd=str(ROOT/'scripts/ancient_condom'))
            state['child_pid']=proc.pid;registry.write_text(json.dumps(state,indent=2))
            print('Started our Blender PID',proc.pid,flush=True)
            try:
                while proc.poll() is None:
                    if stopfile.exists():
                        print('Stopping only our Blender child PID '+str(proc.pid),flush=True);proc.terminate();proc.wait();break
                    time.sleep(.5)
                code=proc.returncode
            except KeyboardInterrupt:
                # Stop only this exact child, never another process by image name.
                proc.terminate();proc.wait();raise
        if code:raise SystemExit(code)
    finally:
        if claimed:
            try:
                if json.loads(LOCK.read_text(encoding='utf-8')).get('owner')==owner:
                    LOCK.unlink();print('Released our GPU lock.',flush=True)
            except (FileNotFoundError,json.JSONDecodeError):pass
        registry.unlink(missing_ok=True);stopfile.unlink(missing_ok=True)

if __name__=='__main__': main()
