import bpy, traceback
from pathlib import Path
root=Path('D:/remotionshorts/scripts/circle_challenge')
out=root.parent.parent/'renders/circle_challenge'
def rebuild():
    try:
        path=root/'motion_revision.py'
        exec(compile(path.read_text(),str(path),'exec'),{})
        code=(root/'calibrate.py').read_text().replace(";s=bpy.context.scene","/'v4_frames';OUT.mkdir(exist_ok=True);s=bpy.context.scene")
        code=code.replace('s.render.resolution_percentage=50','s.render.resolution_x=540;s.render.resolution_y=960;s.render.resolution_percentage=100')
        exec(compile(code,'calibrate.py','exec'),{})
        (out/'motion_build_status.txt').write_text('COMPLETE')
    except Exception:
        (out/'motion_build_status.txt').write_text(traceback.format_exc())
    return None
bpy.app.timers.register(rebuild,first_interval=3,persistent=True)
bpy.ops.wm.open_mainfile(filepath=str(out/'circle_challenge_before_motion.blend'))
exec((root/'live_jobs.py').read_text(),{})
