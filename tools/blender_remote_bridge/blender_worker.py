"""Open in Blender's Text Editor and press Run Script to accept queued jobs."""
import contextlib
import io
import json
import traceback
from pathlib import Path

import bpy

ROOT = Path(r'D:\remotionshorts\tools\blender_remote_bridge')
JOBS = ROOT / '.state' / 'jobs'
EXPORT_DIR = ROOT / 'exports'
JOBS.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)


def write_result(job_id, value):
    target = JOBS / (job_id + '.result.json')
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    temporary.replace(target)


def poll_jobs():
    queued = sorted(JOBS.glob('*.request.json'), key=lambda path: path.stat().st_mtime_ns)
    if not queued:
        return 0.5
    request = queued[0]
    job_id = request.name.split('.')[0]
    running = JOBS / (job_id + '.running.json')
    request.replace(running)
    output = io.StringIO()
    result = {'id': job_id, 'status': 'complete'}
    try:
        job = json.loads(running.read_text(encoding='utf-8'))
        namespace = {'bpy': bpy, 'EXPORT_DIR': EXPORT_DIR, '__name__': '__remote_blender_job__'}
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            exec(compile(job['code'], '<remote Blender job>', 'exec'), namespace)
    except BaseException:
        result['status'] = 'failed'
        result['error'] = traceback.format_exc()
    result['output'] = output.getvalue()[-100000:]
    write_result(job_id, result)
    # Result files take priority over the running marker. Retain the submitted
    # script as a local audit record, without retrying it automatically.
    return 0.5


previous = bpy.app.driver_namespace.get('remote_blender_queue_worker')
if previous and bpy.app.timers.is_registered(previous):
    bpy.app.timers.unregister(previous)
bpy.app.driver_namespace['remote_blender_queue_worker'] = poll_jobs
bpy.app.timers.register(poll_jobs, first_interval=0.5)
print('Remote Blender job worker started. Exports:', EXPORT_DIR)
