import os,json,uuid,subprocess,sys
from pathlib import Path
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v8';stage=sys.argv[1];lock=R/'.blender_gpu.lock';owner=uuid.uuid4().hex
fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
with os.fdopen(fd,'w') as f:json.dump({'project':'slow_eddie_v8','pid':os.getpid(),'owner':owner},f)
source=R/'renders/slow_eddie_v7/slow_eddie_v7.blend' if stage in ['inspect_scene','build'] else P/'slow_eddie_v8.blend'
try:
 with (P/(stage+'.log')).open('w') as log:subprocess.run(['D:/tools/Blender/4.2.23/blender.exe','-b','--factory-startup','--python-exit-code','1',str(source),'--python',str(R/f'scripts/slow_eddie_v8/{stage}.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
finally:
 if lock.exists() and json.loads(lock.read_text()).get('owner')==owner:lock.unlink()
