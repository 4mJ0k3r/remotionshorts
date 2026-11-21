"""Serial native HD export queue: each Blender launch owns its project mutex."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/commode_sniper'
STATUS=OUT/'three_1080p_queue.json'
jobs=[
 ('commode_sniper',[
  [sys.executable,'-u',str(ROOT/'scripts/commode_sniper/run_headless.py'),'master','--script','render_1080p.py','--timeout','21600'],
  [sys.executable,'-u',str(ROOT/'scripts/commode_sniper/finish_1080p.py')]]),
 ('puri_flag_physics',[
  [sys.executable,'-u',str(ROOT/'scripts/puri_flag_physics/run_headless.py'),'master','--script','render_1080p.py','--timeout','21600'],
  [sys.executable,'-u',str(ROOT/'scripts/puri_flag_physics/finish_1080p.py')]]),
 ('elevator_leak',[
  [sys.executable,'-u',str(ROOT/'scripts/elevator_leak/produce_v2.py'),'--version','3','--resolution','1080']])
]
state={'state':'running','pid':os.getpid(),'started':time.time(),'completed':[]}
def write():
    temporary=STATUS.with_suffix('.tmp')
    temporary.write_text(json.dumps(state,indent=2))
    temporary.replace(STATUS)
try:
    for project,commands in jobs:
        state['active_project']=project
        for index,command in enumerate(commands):
            state['step']=index
            write()
            print('QUEUE_START',project,index,time.strftime('%H:%M:%S'),flush=True)
            subprocess.run(command,cwd=str(ROOT),check=True)
        state['completed'].append(project)
        print('QUEUE_COMPLETE',project,time.strftime('%H:%M:%S'),flush=True)
        write()
    state.update(state='complete',active_project=None,finished=time.time())
    write()
except BaseException as error:
    state.update(state='stopped',error=str(error),finished=time.time())
    write()
    raise
