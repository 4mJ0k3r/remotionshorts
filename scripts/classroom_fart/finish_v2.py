"""Assemble only a complete, consistently reviewed frame set, then audit."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');ROOT=OUT.parents[1]
QA=OUT/'qa_v2_full';QA.mkdir(exist_ok=True);VIDEO=OUT/'classroom_fart_v2_full.mp4'
approval=json.loads((OUT/'calibration_v2_approved.json').read_text());source=Path(approval['source'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==approval['source_sha256'],'Source changed after review'
frames=sorted((OUT/'v2_full_frames').glob('*.png'));assert [int(x.stem) for x in frames]==list(range(1,1636)),'Incomplete frame set'
for f,h in approval.get('retained_frame_sha256',{}).items():assert hashlib.sha256((OUT/'v2_full_frames'/f'{int(f):04}.png').read_bytes()).hexdigest()==h
for a in range(1,1636,300):
    b=min(1635,a+299);record=json.loads((OUT/'logs'/f'v2_chunk_{a:04}_{b:04}.json').read_text());assert record['source_sha256']==approval['source_sha256']
subprocess.run(['ffmpeg','-v','warning','-y','-framerate','30','-start_number','1','-i',str(OUT/'v2_full_frames/%04d.png'),'-i',str(OUT/'audio_master.wav'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','medium','-crf','18','-threads','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-af','apad','-t','54.5','-movflags','+faststart',str(VIDEO)],check=True)
subprocess.run(['python',str(ROOT/'scripts/short_qa.py'),str(VIDEO),str(QA),str(OUT/'shots_v2.json')],check=True)
probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(VIDEO)],capture_output=True,text=True,check=True).stdout)
v=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==1635 and (v['width'],v['height'])==(540,960)
md5=subprocess.run(['ffmpeg','-v','error','-i',str(VIDEO),'-map','0:v:0','-f','framemd5','-'],capture_output=True,text=True,check=True).stdout
(QA/'decoded_framemd5.txt').write_text(md5);hs=[s.split(',')[-1].strip() for s in md5.splitlines() if s and not s.startswith('#')]
stats=np.load(QA/'perframe.npz')
summary={'source_sha256':approval['source_sha256'],'video_sha256':hashlib.sha256(VIDEO.read_bytes()).hexdigest(),'frames':len(hs),'duplicates':[i+1 for i in range(1,len(hs)) if hs[i]==hs[i-1]],'frozen_threshold_frames':int((stats['diff']<.02).sum()),'intentional_internal_cuts':[768,1034]}
summary['retained_baseline_frames']=[int(f) for f in approval.get('retained_frame_sha256',{})]
summary['retained_baseline_source_sha256']=approval.get('retained_baseline_source_sha256')
def audio(path):
    raw=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-vn','-ac','1','-ar','8000','-f','f32le','-'],capture_output=True,check=True).stdout
    return np.frombuffer(raw,dtype=np.float32)
x=audio(OUT/'audio_master.wav');y=audio(VIDEO);n=min(len(x),len(y));x=x[:n].astype(float);y=y[:n].astype(float)
size=1<<(2*n-1).bit_length();c=np.fft.irfft(np.fft.rfft(y,size)*np.conj(np.fft.rfft(x,size)),size)
lags=np.arange(-1600,1601);lag=int(lags[np.argmax(c[lags%size])]);summary['audio_lag_ms']=lag/8
xx=x[max(0,-lag):min(n,n-lag)];yy=y[max(0,lag):min(n,n+lag)];summary['audio_similarity']=float(xx@yy/np.sqrt((xx@xx)*(yy@yy)))
assert abs(lag)<=8,'Narration alignment shifted more than 1 ms'
(QA/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
