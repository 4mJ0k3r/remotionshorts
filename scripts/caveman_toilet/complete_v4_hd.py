"""Wait for this HD render, then run CPU encode and QA exactly once."""
import json
import os
import sys
import time
import uuid
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

SCRIPT=Path(__file__).resolve().parent
ROOT=SCRIPT.parents[1]
OUT=ROOT/'renders'/'caveman_toilet'
STATUS=OUT/'v4_hd_completion.json'
GUARD=OUT/'.hd_finish.lock'
owner=uuid.uuid4().hex
fd=os.open(str(GUARD),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
with os.fdopen(fd,'w') as stream:json.dump(dict(owner=owner,pid=os.getpid()),stream)


def status(phase,**extra):
    state=dict(phase=phase,updated_local=datetime.now().isoformat(timespec='seconds'),**extra)
    STATUS.write_text(json.dumps(state,indent=2))
    print('HD FINISH '+phase,flush=True)


try:
    status('waiting_for_frames',width=1080,height=1920,samples=64)
    deadline=time.time()+6*3600
    while time.time()<deadline:
        try:
            progress=json.loads((OUT/'v4_hd_progress.json').read_text())
        except (FileNotFoundError,json.JSONDecodeError):progress={}
        if progress.get('frame')==1620 and (OUT/'frames_v4_1080p'/'f1620.png').exists():break
        time.sleep(15)
    else:raise TimeoutError('HD frame wait exceeded six hours')
    status('encoding')
    subprocess.run([sys.executable,str(SCRIPT/'finish_v4_hd.py')],check=True,cwd=ROOT)
    status('checking_video')
    video=OUT/'caveman_toilet_v4_1080p_master.mp4'
    subprocess.run([sys.executable,str(ROOT/'scripts'/'short_qa.py'),str(video),
                    str(OUT/'qa_v4_1080p'),str(OUT/'qa_v4_shots.json')],check=True,cwd=ROOT)
    result=subprocess.run(['ffprobe','-v','error','-show_entries',
        'stream=codec_type,width,height,r_frame_rate,nb_frames:format=duration','-of','json',str(video)],
        capture_output=True,text=True,check=True)
    specs=json.loads(result.stdout)
    stream=next(s for s in specs['streams'] if s['codec_type']=='video')
    if (stream['width'],stream['height'])!=(1080,1920) or stream['r_frame_rate']!='30/1' or int(stream['nb_frames'])!=1620:
        raise RuntimeError('HD export specification mismatch')
    if abs(float(specs['format']['duration'])-54)>.02:raise RuntimeError('Incorrect HD duration')
    report=(OUT/'qa_v4_1080p'/'report.md').read_text()
    clean=all(phrase in report for phrase in ('black [];','unplanned white [];','frozen spans >=12f []','median): []'))
    profile=json.loads((OUT/'frames_v4_1080p'/'profile.json').read_text())
    manifest=dict(project='caveman_toilet',version=4,profile=profile,frames=1620,duration=54,
        output=str(video),output_sha256=hashlib.sha256(video.read_bytes()).hexdigest(),
        checked_local=datetime.now().isoformat(timespec='seconds'),qa_clean=clean,
        qa_report=str(OUT/'qa_v4_1080p'/'report.md'))
    (OUT/'v4_1080p_manifest.json').write_text(json.dumps(manifest,indent=2))
    status('complete' if clean else 'needs_review',output=str(video),qa_clean=clean)
except BaseException as error:
    status('failed',error=str(error))
    raise
finally:
    if GUARD.exists() and json.loads(GUARD.read_text()).get('owner')==owner:GUARD.unlink()
