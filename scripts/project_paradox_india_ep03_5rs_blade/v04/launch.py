"""Exclusive owner-checked launcher; never terminates unrelated processes."""
import os,json,sys,uuid,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;P=R/'renders/project_paradox_india_ep03_5rs_blade/v04'
action=sys.argv[1]
output=P/'native_1080' if action.startswith('native_') else P
lock=R/'.blender_gpu.lock';owner=uuid.uuid4().hex
try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
except FileExistsError:raise SystemExit('GPU lock owned by another job; wait for its owner to finish')
with os.fdopen(fd,'w') as f:json.dump({'project':'paradox_india_ep03','pid':os.getpid(),'owner':owner,'action':action},f)
try:
 output.mkdir(parents=True,exist_ok=True)
 args=['D:/tools/Blender/4.2.23/blender.exe','-b','--factory-startup','--python-exit-code','1']
 args += [str(P.parent/'v03/project_paradox_ep03_v03.blend' if action == 'build' else P/'project_paradox_ep03_v04.blend')]
 args+=['--python',str(D/'worker.py'),'--',action]
 path=output/(action+'_'+time.strftime('%Y%m%d_%H%M%S')+'.log');print(path,flush=True)
 samples=[]
 with path.open('w',encoding='utf-8') as log:
  child=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT)
  while child.poll() is None:
   try:
    v=subprocess.run(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),check=True)
    samples.append(max(float(x) for x in v.stdout.splitlines())/1024)
   except (OSError,ValueError,subprocess.SubprocessError):pass
   time.sleep(.4)
  code=child.wait()
 (output/('board_vram_'+action+'.json')).write_text(json.dumps({'peak_gib':max(samples) if samples else None,'sample_count':len(samples)},indent=2))
 if code:raise SystemExit(code)
finally:
 if lock.exists() and json.loads(lock.read_text()).get('owner')==owner:lock.unlink()
