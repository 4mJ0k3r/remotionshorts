"""Approved V4 HD export: 1080x1920, 30fps, 64 EEVEE samples, resumable PNGs."""
import sys
import json
import time
import hashlib
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).parent))
from v2_common import OUT,log

args=sys.argv[sys.argv.index('--')+1:]
phase=args[0]
bpy.ops.wm.open_mainfile(filepath=str(OUT/'caveman_toilet_v4.blend'))
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT';sc.eevee.use_raytracing=False
sc.render.use_simplify=True;sc.render.simplify_subdivision=2
sc.render.resolution_x=1080;sc.render.resolution_y=1920;sc.render.resolution_percentage=100
sc.render.fps=30;sc.eevee.taa_render_samples=64
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB'
sc.render.image_settings.compression=0
folder=OUT/('hd_v4_benchmark' if phase=='sheet' else 'frames_v4_1080p')
folder.mkdir(exist_ok=True)
if phase!='sheet':
    profile=dict(width=1080,height=1920,fps=30,samples=64,
                 scene_sha256=hashlib.sha256((OUT/'caveman_toilet_v4.blend').read_bytes()).hexdigest())
    marker=folder/'profile.json'
    if marker.exists() and json.loads(marker.read_text())!=profile:
        raise RuntimeError('Existing HD frames belong to a different scene/profile')
    if not marker.exists() and any(folder.glob('f*.png')):
        raise RuntimeError('Unverified existing HD frames; refusing to mix renders')
    marker.write_text(json.dumps(profile,indent=2))
frames=[40,950,1250,1427] if phase=='sheet' else list(range(1,1621))
times=[];t0=time.time();rendered=0
for f in frames:
    target=folder/f'f{f:04d}.png'
    if phase!='sheet' and target.exists() and target.stat().st_size>10000:
        continue
    sc.frame_set(f);sc.render.filepath=str(target)
    start=time.time();bpy.ops.render.render(write_still=True)
    elapsed=time.time()-start;times.append(elapsed);rendered+=1
    if phase=='sheet' or rendered%15==0 or f==frames[-1]:
        avg=sum(times)/len(times)
        remaining=0 if phase=='sheet' else 1620-f
        progress=dict(frame=f,frames=1620,seconds_per_frame=avg,elapsed=time.time()-t0,
                      eta_seconds=avg*remaining,width=1080,height=1920,samples=64)
        (OUT/('v4_hd_benchmark.json' if phase=='sheet' else 'v4_hd_progress.json')).write_text(json.dumps(progress,indent=2))
        log(f'HD frame {f}: {elapsed:.2f}s; average {avg:.2f}s/frame; ETA {avg*remaining/60:.1f}min')
if phase=='sheet':
    (OUT/'v4_hd_benchmark.json').write_text(json.dumps(dict(frames=frames,times=times,
        average_seconds=sum(times)/len(times),samples=64,width=1080,height=1920),indent=2))
log(f'HD {phase} complete; {rendered} frames rendered')
