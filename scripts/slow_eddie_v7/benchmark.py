import bpy,time,json,sys,traceback,os
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v7');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v7_runtime.py'].as_string(),'runtime','exec'))
original=update
def checked(scene):
 try:original(scene)
 except BaseException:traceback.print_exc();sys.stdout.flush();os._exit(3)
bpy.app.handlers.frame_change_post.clear();bpy.app.handlers.frame_change_post.append(checked);s.render.resolution_percentage=100
start=time.perf_counter();s.frame_set(1);s.render.filepath=str(P/'warmup.png');bpy.ops.render.render(write_still=True);(P/'warmup.json').write_text(json.dumps({'seconds':time.perf_counter()-start}));results=[]
for f in [15,31,60,90,135,280]:
 start=time.perf_counter();s.frame_set(f);s.render.filepath=str(P/f'benchmark_{f:03d}.png');bpy.ops.render.render(write_still=True);results.append({'frame':f,'seconds':time.perf_counter()-start})
(P/'benchmark.json').write_text(json.dumps(results,indent=2));assert max(x['seconds'] for x in results)<=2,results
print('BENCHMARK PASSED',results,flush=True)
