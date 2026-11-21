"""Authorized full-render pipeline; lock-owning Blender first, audio mux and QA afterward."""
import subprocess,sys,json,os,datetime
from pathlib import Path
ROOT=Path(r'D:\remotionshorts');SRC=ROOT/'scripts/ancient_condom';OUT=ROOT/'renders/ancient_condom'
def state(stage,**kw):(OUT/'pipeline_state.json').write_text(json.dumps({'stage':stage,'pipeline_pid':os.getpid(),'updated_local':datetime.datetime.now().isoformat(timespec='seconds'),**kw},indent=2))
try:
 state('rendering_1080p')
 subprocess.run([sys.executable,str(SRC/'run_blender.py'),'--phase','master_1080_sky','--',str(OUT/'ancient_condom.blend'),'-P',str(SRC/'render_master.py')],cwd=ROOT,check=True)
 state('encoding_and_technical_qa')
 subprocess.run([sys.executable,str(SRC/'finish_master.py')],cwd=ROOT,check=True)
 state('encoded_needs_visual_review',output=str(OUT/'ancient_condom_1080p_master.mp4'))
except Exception as e:state('stopped_or_failed',error=str(e));raise
