"""Authorized full-HD V2; separate lossless frames and source-checked resume."""
import bpy,json,time,hashlib,os
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\bamboo_ambush');frames=OUT/'frames_v2_1080';frames.mkdir(exist_ok=True);s=bpy.context.scene
s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=30;s.render.frame_map_old=s.render.frame_map_new=100;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=10;s.eevee.taa_render_samples=32;s.eevee.use_raytracing=False;s.render.use_simplify=True;s.render.simplify_subdivision=2
if hasattr(s.render,'compositor_device'):s.render.compositor_device='GPU'
digest=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();cfg=OUT/'v2_1080_config.json';profile={'source_sha256':digest,'source':bpy.data.filepath,'resolution':[1080,1920],'samples':32,'fps':30,'frames':935,'compositor':'GPU'}
if cfg.exists() and json.loads(cfg.read_text())!=profile:raise RuntimeError('Source/profile differs; refusing mixed full-HD frames.')
cfg.write_text(json.dumps(profile,indent=2));start=time.monotonic();count=0;times=[]
for f in range(1,936):
 out=frames/f'{f:04d}.png'
 if out.exists() and out.stat().st_size>10000:continue
 s.frame_set(f);tmp=frames/f'{f:04d}.part.png';s.render.filepath=str(tmp);t=time.monotonic();bpy.ops.render.render(write_still=True);os.replace(tmp,out);count+=1;seconds=time.monotonic()-t;times.append(seconds);recent=times[-60:];sec=sum(recent)/len(recent)
 progress={'stage':'rendering','last_frame':f,'total_frames':935,'percent':round(f/935*100,1),'current_seconds':round(seconds,3),'mean_seconds':round(sec,3),'estimated_seconds_left':round((935-f)*sec),'resolution':[1080,1920],'samples':32,'elapsed_this_run':round(time.monotonic()-start,1)};p=OUT/'v2_1080_progress.tmp.json';p.write_text(json.dumps(progress,indent=2));os.replace(p,OUT/'v2_1080_progress.json')
 if count<=3 or count%25==0:print('V2 FULL HD',json.dumps(progress),flush=True)
progress['stage']='frames_complete';(OUT/'v2_1080_progress.json').write_text(json.dumps(progress,indent=2));print('V2 ALL935 FULL-HD FRAMES COMPLETE',flush=True)
