"""Fast V2 preview:360x640,12 samples,30fps; never reuses the V1 frames."""
import bpy,json,time,hashlib,os
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\bamboo_ambush');frames=OUT/'frames_v2_360';frames.mkdir(exist_ok=True);s=bpy.context.scene;s.render.resolution_x=360;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.fps=30;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=10;s.eevee.taa_render_samples=12
if hasattr(s.render,'compositor_device'):s.render.compositor_device='GPU'
digest=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();cfg=OUT/'v2_preview_config.json';profile={'source_sha256':digest,'source':bpy.data.filepath,'resolution':[360,640],'samples':12,'fps':30,'frames':935}
if cfg.exists() and json.loads(cfg.read_text())!=profile:raise RuntimeError('V2 frame profile/source differs; refusing to mix cached frames.')
cfg.write_text(json.dumps(profile,indent=2));start=time.monotonic();count=0
for f in range(1,936):
 out=frames/f'{f:04d}.png'
 if out.exists() and out.stat().st_size>1024:continue
 s.frame_set(f);tmp=frames/f'{f:04d}.part.png';s.render.filepath=str(tmp);bpy.ops.render.render(write_still=True);os.replace(tmp,out);count+=1;elapsed=time.monotonic()-start;sec=elapsed/count;progress={'stage':'rendering','last_frame':f,'total_frames':935,'percent':round(f/935*100,1),'mean_seconds':round(sec,3),'estimated_seconds_left':round((935-f)*sec),'resolution':[360,640],'samples':12};p=OUT/'v2_progress.tmp.json';p.write_text(json.dumps(progress,indent=2));os.replace(p,OUT/'v2_progress.json')
 if count==1 or count%25==0:print('V2 PREVIEW',json.dumps(progress),flush=True)
print('V2 ALL935 PREVIEW FRAMES COMPLETE',flush=True)
