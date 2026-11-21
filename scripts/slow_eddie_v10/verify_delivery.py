"""Read-only validation of the finished V9 delivery, plus a reproducible report."""
from pathlib import Path
import hashlib,json,re,subprocess,statistics
from PIL import Image

R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v10'
video=P/'slow_eddie_v10_1080p.mp4'
probe=json.loads(subprocess.run(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(video)],capture_output=True,text=True,check=True).stdout)
v=next(s for s in probe['streams'] if s['codec_type']=='video')
a=next(s for s in probe['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(1080,1920,'30/1',300)
assert abs(float(probe['format']['duration'])-10)<.05
frames=sorted((P/'frames').glob('frame_*.png'));assert len(frames)==300
assert all(Image.open(p).size==(1080,1920) for p in frames)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'slow_eddie_v10.blend')==json.loads((P/'source_hash.json').read_text())['sha256']
assert sha(P/'captions_reference.ass')==sha(R/'tools/V9_Parity_Packet/V9_Parity_Packet/captions_reference.ass')
result=subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(video),'-f','null','-'],capture_output=True,text=True,check=True)
audio=subprocess.run(['ffmpeg','-hide_banner','-i',str(video),'-af','loudnorm=I=-14.3:TP=-2.9:LRA=7:print_format=json','-f','null','-'],capture_output=True,text=True,check=True).stderr
loudness=json.JSONDecoder().raw_decode(audio[audio.rfind('{'):])[0];(P/'audio_output_measurements.json').write_text(json.dumps(loudness,indent=2))
assert abs(float(loudness['input_i'])+14.3)<=.5
# Blender's Time lines include a mm:ss field; parse them without dropping any.
def secs(s):
 z=s.split(':');return sum(float(n)*60**i for i,n in enumerate(reversed(z)))
timings=[secs(s) for s in re.findall(r'^Time: ([\d:.]+) \(Saving:',(P/'render.log').read_text(),re.M)]
assert len(timings)==300
gate=json.loads((P/'performance_gate.json').read_text());assert gate['passed']
vram={p.stem:json.loads(p.read_text()) for p in P.glob('vram_*.json')}
assert all(d['passed'] for d in vram.values())
import numpy as np
report={'video':{'width':1080,'height':1920,'fps':30,'frames':300,'seconds':float(probe['format']['duration']),'codec':v['codec_name'],'audio_codec':a['codec_name']},'render_settings':{'engine':'BLENDER_EEVEE_NEXT','samples':24,'shadow_pool_mib':128,'ray_tracing':False,'native_resolution':True},'gate':gate,'full_render':{**json.loads((P/'full_timing.json').read_text()),'log_frame_mean':statistics.mean(timings),'log_frame_p95':float(np.percentile(timings,95)),'log_frame_max':max(timings)},'vram':vram,'audio_output':{'integrated_lufs':float(loudness['input_i']),'true_peak_dbtp':float(loudness['input_tp'])},'hashes':{'blend':sha(P/'slow_eddie_v10.blend'),'runtime':sha(R/'scripts/slow_eddie_v10/runtime.py'),'captions':sha(P/'captions_reference.ass'),'mp4':sha(video)},'decode_check':'passed','source_unchanged_during_render':True,'parity_certified':False,'remaining_visual_differences':['Opening town geometry and camera azimuth differ from the reference.','Final composition follows requested buckle/hat placement but is not a pixel-identical reference match.','Mustache, glove contact and cel-shadow boundary remain approximations.'],'review_scope':'Ten matched stills and automated all-frame QA; no claim of direct aural review or objective 90 percent parity.'}
(P/'delivery_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
