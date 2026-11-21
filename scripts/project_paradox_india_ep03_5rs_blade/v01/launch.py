"""Exclusive owner-checked launcher; never terminates unrelated processes."""
import os,json,sys,uuid,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;P=R/'renders/project_paradox_india_ep03_5rs_blade/v01'
action=sys.argv[1];lock=R/'.blender_gpu.lock';owner=uuid.uuid4().hex
if action=='calibrate':
 import ast
 sys.path.insert(0,str(R/'scripts'))
 from calibration_sheet import build_plan
 tree=ast.parse((D/'runtime.py').read_text())
 shots=next(ast.literal_eval(x.value) for x in tree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SHOTS' for t in x.targets))
 meta={'shots':[{'id':n,'a':a-1,'b':b} for n,a,b,g in shots],'cuts':[a-1 for n,a,b,g in shots[1:]],
 'transitions':[[197,231]],'calibration_frames':[35,150,175,190,350,475,519,675,760,816,869,920,1020,1090,1198,1252,1280,1400],
 'closeups':[{'frame':1090,'kind':'hat_brim','region':[.3,.15,.72,.45]},{'frame':760,'kind':'hand_prop','region':[.1,.35,.9,.88]}]}
 (P/'calibration_plan.json').write_text(json.dumps(build_plan(meta,1401),indent=2))
try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
except FileExistsError:raise SystemExit('GPU lock owned by another job; wait for its owner to finish')
with os.fdopen(fd,'w') as f:json.dump({'project':'paradox_india_ep03','pid':os.getpid(),'owner':owner,'action':action},f)
try:
 P.mkdir(parents=True,exist_ok=True)
 args=['D:/tools/Blender/4.2.23/blender.exe','-b','--factory-startup','--python-exit-code','1']
 if action!='build':args+=[str(P/'project_paradox_ep03_v01.blend')]
 args+=['--python',str(D/'worker.py'),'--',action]
 path=P/(action+'_'+time.strftime('%Y%m%d_%H%M%S')+'.log');print(path,flush=True)
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
 (P/('board_vram_'+action+'.json')).write_text(json.dumps({'peak_gib':max(samples) if samples else None,'sample_count':len(samples)},indent=2))
 if code:raise SystemExit(code)
finally:
 if lock.exists() and json.loads(lock.read_text()).get('owner')==owner:lock.unlink()
