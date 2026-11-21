import bpy,time,json,sys
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_runtime.py'].as_string(),'runtime','exec'))
s.render.resolution_percentage=100
start=time.perf_counter();s.frame_set(1);s.render.filepath=str(P/'warmup.png');bpy.ops.render.render(write_still=True);(P/'warmup.json').write_text(json.dumps({'cold_setup_seconds':time.perf_counter()-start}));results=[]
for f in [15,60,95,170,270]:
 start=time.perf_counter();s.frame_set(f);s.render.filepath=str(P/f'benchmark_{f:03d}.png');bpy.ops.render.render(write_still=True);results.append({'frame':f,'seconds':time.perf_counter()-start})
(P/'benchmark.json').write_text(json.dumps(results,indent=2));print('BENCHMARK',results,flush=True)
