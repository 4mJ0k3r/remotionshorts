import os,json,uuid,subprocess,sys,time
from pathlib import Path
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v11';stage=sys.argv[1];lock=R/'.blender_gpu.lock';owner=uuid.uuid4().hex
fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
with os.fdopen(fd,'w') as f:json.dump({'project':'slow_eddie_v11','pid':os.getpid(),'owner':owner},f)
source=R/'renders/slow_eddie_v10/slow_eddie_v10.blend' if stage in ['inspect_scene','build'] else P/'slow_eddie_v11.blend';samples=[]
try:
 with (P/(stage+'.log')).open('w') as log:
  proc=subprocess.Popen(['D:/tools/Blender/4.2.23/blender.exe','-b','--factory-startup','--python-exit-code','1',str(source),'--python',str(R/f'scripts/slow_eddie_v11/{stage}.py')],stdout=log,stderr=subprocess.STDOUT,creationflags=0x08000000)
  while proc.poll() is None:
   if stage in ['benchmark','render','editorial']:
    result=subprocess.run(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,creationflags=0x08000000)
    if result.returncode==0:
     try:samples.append(float(result.stdout.strip().splitlines()[0]))
     except ValueError:pass
   time.sleep(.5)
  if proc.returncode:raise RuntimeError('Blender stage failed: '+str(proc.returncode))
 if samples:
  peak=max(samples);(P/('vram_'+stage+'.json')).write_text(json.dumps({'whole_board_peak_mib':peak,'limit_mib':3.3*1024,'passed':peak<=3.3*1024,'samples':len(samples)},indent=2))
 if stage=='benchmark' and (P/'vram_benchmark.json').exists():
  (P/'vram.json').write_text((P/'vram_benchmark.json').read_text())
finally:
 if lock.exists() and json.loads(lock.read_text()).get('owner')==owner:lock.unlink()
