import bpy,time,json
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v12');s=bpy.context.scene;exec(compile(bpy.data.texts['slow_eddie_v12_runtime.py'].as_string(),'runtime','exec'));s.render.resolution_percentage=100;s.frame_set(24);update(s)
start=time.perf_counter();bpy.ops.render.render(write_still=False);warm=time.perf_counter()-start;s.render.filepath=str(P/'frames/frame_0024.png');start=time.perf_counter();bpy.ops.render.render(write_still=True);(P/'patch24_timing.json').write_text(json.dumps({'warmup':warm,'render':time.perf_counter()-start},indent=2))
