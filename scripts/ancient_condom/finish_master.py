"""Mux the exact 1875-frame sequence with original-speed Hindi narration, then run QA."""
import subprocess,json,sys,os,time
from pathlib import Path
ROOT=Path(r'D:\remotionshorts');OUT=ROOT/'renders/ancient_condom';FRAMES=OUT/'frames_1080_sky_v1';target=OUT/'ancient_condom_1080p_master.mp4'
missing=[f for f in range(1,1876) if not (FRAMES/f'f{f:04}.png').is_file()]
if missing:raise SystemExit('Cannot encode: missing frames '+str(missing[:10]))
cmd=['ffmpeg','-y','-v','warning','-framerate','30','-start_number','1','-i',str(FRAMES/'f%04d.png'),'-i',str(OUT/'audio_master.wav'),'-map','0:v:0','-map','1:a:0','-frames:v','1875','-t','62.5','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p','-threads','0','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(target)]
print('Encoding full-HD master with Hindi narration.',flush=True)
with (OUT/'logs/encode_master.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
meta=json.loads((OUT/'shots.json').read_text());meta['xfade']=[[1175,1183]];meta['planned']=[[e-6,e+1] for e in meta['whip_ends']];qmeta=OUT/'qa/master_shots.json';qmeta.write_text(json.dumps(meta,indent=2));subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(target),str(OUT/'qa/master'),str(qmeta)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)]));v=next(s for s in probe['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1080,1920,'30/1',1875);assert abs(float(probe['format']['duration'])-62.5)<.04;assert any(s['codec_type']=='audio' for s in probe['streams']);(OUT/'qa/master_probe.json').write_text(json.dumps(probe,indent=2));print('MASTER ENCODED AND TECHNICALLY VERIFIED',target,flush=True)
cal=OUT/'calibration_master';cal.mkdir(exist_ok=True);select='+'.join('eq(n,%d)'%(f-1) for f in meta['samples']);subprocess.run(['ffmpeg','-y','-v','error','-i',str(target),'-vf',"select='"+select+"',scale=540:960",'-fps_mode','vfr','-frames:v','20',str(cal/'tile_%02d.png')],check=True)
for j,f in enumerate(meta['samples'],1):os.replace(cal/f'tile_{j:02}.png',cal/f'f{f:04}.png')
subprocess.run([sys.executable,str(ROOT/'scripts/ancient_condom/assemble_sheet.py'),'--master'],check=True)
