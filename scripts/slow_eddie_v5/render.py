import bpy,time,json,sys,traceback
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v5');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v5_runtime.py'].as_string(),'runtime','exec'))
original=bpy.app.handlers.frame_change_post[0]
def checked(s):
 try:original(s)
 except BaseException:traceback.print_exc();sys.stdout.flush();__import__('os')._exit(3)
bpy.app.handlers.frame_change_post.clear();bpy.app.handlers.frame_change_post.append(checked)
s.render.resolution_percentage=100;s.render.filepath=str(P/'frames/frame_');s.frame_start=1;s.frame_end=300
(P/'frames').mkdir(exist_ok=True);start=time.perf_counter();bpy.ops.render.render(animation=True)
(P/'full_timing.json').write_text(json.dumps({'seconds':time.perf_counter()-start,'frames':300},indent=2))
