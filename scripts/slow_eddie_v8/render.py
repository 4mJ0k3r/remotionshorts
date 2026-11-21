import bpy,time,json,sys,traceback,os
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v8');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v8_runtime.py'].as_string(),'runtime','exec'))
original=update
def checked(scene):
 try:original(scene)
 except BaseException:traceback.print_exc();sys.stdout.flush();os._exit(3)
bpy.app.handlers.frame_change_post.clear();bpy.app.handlers.frame_change_post.append(checked)
s.render.resolution_percentage=100;s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.fps=30;s.frame_start=1;s.frame_end=300;s.render.filepath=str(P/'frames/frame_');(P/'frames').mkdir(exist_ok=True)
start=time.perf_counter();bpy.ops.render.render(animation=True);(P/'full_timing.json').write_text(json.dumps({'seconds':time.perf_counter()-start,'frames':300},indent=2))
