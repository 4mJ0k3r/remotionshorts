import os,json,uuid,subprocess,sys
from pathlib import Path
R=Path('D:/remotionshorts');lock=R/'.blender_gpu.lock';owner=uuid.uuid4().hex
fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
with os.fdopen(fd,'w') as f:json.dump({'project':'slow_eddie','pid':os.getpid(),'owner':owner},f)
try:
 with open(R/'renders/slow_eddie/extract.log','w') as log:subprocess.run(['D:/tools/Blender/4.2.23/blender.exe','-b','--factory-startup','--python-exit-code','1',str(R/'renders/slow_eddie/slow_eddie_v1.blend'),'--python',str(R/'scripts/slow_eddie/extract.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
finally:
 if lock.exists() and json.loads(lock.read_text()).get('owner')==owner:lock.unlink()
