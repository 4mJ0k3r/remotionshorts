"""Local Blender job mailbox; files contain only this project's authored bpy code."""
import bpy,traceback
from pathlib import Path
ROOT=Path('D:/remotionshorts/scripts/circle_challenge');OUT=Path('D:/remotionshorts/renders/circle_challenge')
def poll_job():
    q=ROOT/'pending_job.py'
    if q.exists():
        code=q.read_text(encoding='utf-8');q.replace(ROOT/'last_job.py')
        try:
            exec(compile(code,str(q),'exec'),{})
            (OUT/'job_status.txt').write_text('COMPLETE')
        except Exception:(OUT/'job_status.txt').write_text(traceback.format_exc())
    return 1.0
bpy.app.timers.register(poll_job,first_interval=1)
