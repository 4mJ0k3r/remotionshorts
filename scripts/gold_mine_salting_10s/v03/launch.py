"""Owner-checked exclusive launcher. Never touches another project's jobs."""
import os,sys,json,uuid,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;P=R/'renders/gold_mine_salting_v3'
stage=sys.argv[1];lock=R/'.blender_gpu.lock';owner=uuid.uuid4().hex
while True:
 try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:print('Waiting for current GPU owner',flush=True);time.sleep(10);continue
 with os.fdopen(fd,'w') as h:json.dump({'project':'gold_mine_salting_v3','owner':owner,'pid':os.getpid(),'phase':stage},h)
 break
process=None;samples=[]
try:
 # Lock-free legacy background processes are also respected.
 p=subprocess.run(['powershell','-NoProfile','-Command',"Get-CimInstance Win32_Process -Filter \"Name='blender.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],capture_output=True,text=True,creationflags=0x08000000)
 rows=json.loads(p.stdout) if p.stdout.strip() else []
 if isinstance(rows,dict):rows=[rows]
 if any(any(t in (r.get('CommandLine') or '').split() for t in ['-b','--background']) for r in rows):raise RuntimeError('Another background Blender is active; wait without interrupting it')
 command=['D:/tools/Blender/4.2.23/blender.exe','-b','--factory-startup','--python-exit-code','1']
 if stage=='build':command+=['--python',str(D/'build.py')]
 else:command+=[str(P/'gold_mine_salting_v3.blend'),'--python',str(D/'worker.py'),'--',stage]+sys.argv[2:]
 env=os.environ.copy();env['GOLD_MINE_WORKER']='1'
 logpath=P/(stage+'_'+time.strftime('%Y%m%d_%H%M%S')+'.log')
 with logpath.open('w',encoding='utf8') as log:
  process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env,creationflags=0x08000000)
  print('START',stage,'PID',process.pid,'LOG',logpath,flush=True)
  while process.poll() is None:
   mem=subprocess.run(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,creationflags=0x08000000)
   if mem.returncode==0:
    try:samples.append(float(mem.stdout.splitlines()[0]))
    except ValueError:pass
   time.sleep(.2)
 if samples:(P/('board_vram_'+stage+'.json')).write_text(json.dumps({'peak_mib':max(samples),'samples':len(samples),'sampling_seconds':.2},indent=2))
 if process.returncode:raise RuntimeError(logpath.read_text(errors='replace')[-6500:])
 print('FINISHED',stage,'peak board MiB',max(samples) if samples else 'UNVERIFIED',flush=True)
finally:
 if process and process.poll() is None:process.terminate();process.wait()
 if lock.exists() and json.loads(lock.read_text()).get('owner')==owner:lock.unlink()
