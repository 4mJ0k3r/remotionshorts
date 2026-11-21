import bpy,time,json,hashlib
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v13');s=bpy.context.scene;sha=hashlib.sha256((P/'slow_eddie_v13.blend').read_bytes()).hexdigest();assert sha==json.loads((P/'source_hash.json').read_text())['sha256'];exec(compile(bpy.data.texts['slow_eddie_v13_runtime.py'].as_string(),'runtime','exec'));s.render.resolution_percentage=100;s.frame_set(272);update(s);start=time.perf_counter();bpy.ops.render.render(write_still=False);warm=time.perf_counter()-start;r=[]
for f in [272,274,275,276,292]:
 start=time.perf_counter();s.frame_set(f);update(s);s.render.filepath=str(P/f'frames/frame_{f:04d}.png');bpy.ops.render.render(write_still=True);r.append({'frame':f,'seconds':time.perf_counter()-start,'source_sha256':sha})
(P/'warm_rechecks.json').write_text(json.dumps({'warmup_seconds':warm,'samples':s.eevee.taa_render_samples,'replacement_frames':r},indent=2));print(r)
