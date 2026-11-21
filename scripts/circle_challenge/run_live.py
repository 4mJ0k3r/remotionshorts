import bpy,traceback
from pathlib import Path
ROOT=Path('D:/remotionshorts/scripts/circle_challenge')
OUT=Path('D:/remotionshorts/renders/circle_challenge')
def build_job():
    try:
        exec(compile((ROOT/'build.py').read_text(encoding='utf-8'),str(ROOT/'build.py'),'exec'),{})
        (OUT/'build_status.txt').write_text('COMPLETE')
    except Exception:(OUT/'build_status.txt').write_text(traceback.format_exc())
    return None
bpy.app.timers.register(build_job,first_interval=.5)
