from pathlib import Path
import json,subprocess,hashlib,re,numpy as np
from PIL import Image
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v12';v=P/'slow_eddie_v12_1080p.mp4';old=R/'renders/slow_eddie_v11/slow_eddie_v11_1080p.mp4'
def run(args):return subprocess.run(args,capture_output=True,text=True,check=True).stdout
probe=json.loads(run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(v)]));video=next(x for x in probe['streams'] if x['codec_type']=='video');assert(video['width'],video['height'],video['r_frame_rate'],int(video['nb_read_frames']))==(1080,1920,'30/1',300)
def audio(p):return json.loads(run(['ffprobe','-v','error','-select_streams','a','-show_packets','-show_data_hash','sha256','-show_entries','packet=pts_time,duration_time,data_hash','-of','json',str(p)]))['packets']
a,b=audio(old),audio(v);assert a==b,'Audio packet content or timestamps changed'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();original_sha=json.loads((P/'source_hash.json').read_text())['sha256']
patch=json.loads((P/'launch_patch_manifest.json').read_text()) if (P/'launch_patch_manifest.json').exists() else None
if patch:
 assert patch['original_source_sha256']==original_sha
 assert sha(P/'slow_eddie_v12.blend')==patch['patched_source_sha256']
 old_runtime=(R/'scripts/slow_eddie_v12/runtime_before_launch_patch.py').read_text();new_runtime=(R/'scripts/slow_eddie_v12/runtime.py').read_text()
 assert old_runtime.replace('b.hide_render=not 24<=f<=126','b.hide_render=not 31<=f<=126')==new_runtime
else:assert sha(P/'slow_eddie_v12.blend')==original_sha
assert sha(P/'captions_reference.ass')==sha(P/'captions_v12.ass')
assert len(list((P/'frames').glob('frame_*.png')))==300;assert all(Image.open(p).size==(1080,1920) for p in (P/'frames').glob('frame_*.png'))
run(['ffmpeg','-v','error','-xerror','-i',str(v),'-f','null','-'])
def seconds(x):return sum(float(v)*60**i for i,v in enumerate(reversed(x.split(':'))))
times=[seconds(x) for x in re.findall(r'^Time: ([\d:.]+) \(Saving:',(P/'render.log').read_text(),re.M)][-300:];assert len(times)==300
j=json.loads((P/'junction_audit.json').read_text());gate=json.loads((P/'performance_gate.json').read_text());vr={p.stem:json.loads(p.read_text()) for p in P.glob('vram_*.json')}
assert j['junction_121_122_exact'];assert j['min_camera_clearance_158_181']>=.3;assert j['delta_210_211_m']<.01
holds=[r['gap_360px'] for r in j['frames'] if 'gap_360px' in r];assert min(holds)>=18 and max(holds)<=22
assert gate['passed'];assert all(x['passed'] for x in vr.values())
report={'video':{'resolution':[1080,1920],'fps':30,'frames':300,'seconds':float(probe['format']['duration'])},'audio_packet_content_and_timestamps_identical_to_v11':True,'audio_packets':len(a),'benchmark':gate,'full_render':{**json.loads((P/'full_timing.json').read_text()),'p95':float(np.percentile(times,95)),'max':max(times),'mean':float(np.mean(times)),'max_2_second_gate':max(times)<=2},'vram':vr,'camera_clearance_158_181':j['min_camera_clearance_158_181'],'junction_121_122_exact':True,'camera_delta210211_m':j['delta_210_211_m'],'hold_clearance360px':[min(holds),max(holds)],'sha256':{'blend':sha(P/'slow_eddie_v12.blend'),'video':sha(v),'captions':sha(P/'captions_reference.ass')},'review_scope':'Numerical gates plus matched stills/junction strips; no subjective parity percentage certified.'}
report['launch_patch']=patch
(P/'delivery_validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
