"""Serialized full-HD rendering, followed automatically by audio mux and technical QA."""
import subprocess,sys,json,datetime,os
from pathlib import Path
ROOT=Path(r'D:\remotionshorts');SRC=ROOT/'scripts/bamboo_ambush';OUT=ROOT/'renders/bamboo_ambush'
def state(stage,**kw):(OUT/'v2_1080_pipeline.json').write_text(json.dumps({'stage':stage,'pid':os.getpid(),'updated_local':datetime.datetime.now().isoformat(timespec='seconds'),**kw},indent=2))
try:
 state('rendering_or_waiting_for_gpu')
 subprocess.run([sys.executable,str(SRC/'run_blender.py'),'--phase','v2_1080_master','--',str(OUT/'bamboo_ambush_v2.blend'),'-P',str(SRC/'render_1080p_v2.py')],cwd=ROOT,check=True)
 state('encoding_and_qa')
 subprocess.run([sys.executable,str(SRC/'finish_1080p_v2.py')],cwd=ROOT,check=True)
 state('encoded_needs_visual_review',output=str(OUT/'bamboo_ambush_v2_1080p.mp4'))
except Exception as e:state('stopped_or_failed',error=str(e));raise
