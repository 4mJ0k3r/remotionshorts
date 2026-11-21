import bpy,json,time,hashlib
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v6');R=Path('D:/remotionshorts');s=bpy.context.scene
old=(P/'source_hash.json').read_text();(P/'source_hash_transition.json').write_text(old)
bpy.data.texts['slow_eddie_v6_runtime.py'].from_string((R/'scripts/slow_eddie_v6/runtime.py').read_text());exec(compile(bpy.data.texts['slow_eddie_v6_runtime.py'].as_string(),'runtime','exec'))
s.frame_set(1);s.render.resolution_percentage=100;bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v6.blend'))
(P/'source_hash.json').write_text(json.dumps({'source':str(P/'slow_eddie_v6.blend'),'sha256':hashlib.sha256((P/'slow_eddie_v6.blend').read_bytes()).hexdigest()}))
start=time.perf_counter()
for f in range(35,88):
 s.frame_set(f);update(s);s.render.filepath=str(P/f'frames/frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
(P/'chase_entry_patch.json').write_text(json.dumps({'frames':[35,87],'reason':'Begin chase ahead of Challenger so his body cannot occlude hero bullet; same endpoint, easing and holster arrival','seconds':time.perf_counter()-start},indent=2))
