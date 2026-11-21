"""Blender --python bootstrap for future launcher-owned sessions."""
import contextlib
import io
import json
import os
import time
import traceback
from pathlib import Path

import bpy

SESSION = Path(os.environ['BLENDER_BRIDGE_SESSION'])
JOBS = SESSION / 'jobs'
EXPORT_DIR = SESSION.parent.parent.parent / 'exports'
JOBS.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def atomic_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    temporary.replace(path)


def heartbeat(status='ready', job_id=None):
    atomic_json(SESSION / 'worker.json', {'pid': os.getpid(), 'updated': time.time(),
                                        'status': status, 'job_id': job_id})


def poll_jobs():
    if (SESSION / 'stop_worker').exists():
        heartbeat('stopped')
        return None
    heartbeat()
    pending = sorted(JOBS.glob('*.request.json'), key=lambda path: path.stat().st_mtime_ns)
    if not pending:
        return 0.5
    request = pending[0]
    job_id = request.name.split('.')[0]
    running = JOBS / (job_id + '.running.json')
    request.replace(running)
    heartbeat('busy', job_id)
    captured = io.StringIO()
    result = {'id': job_id, 'status': 'complete'}
    try:
        payload = json.loads(running.read_text(encoding='utf-8'))
        namespace = {'bpy': bpy, 'EXPORT_DIR': EXPORT_DIR, '__name__': '__remote_blender_job__'}
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            exec(compile(payload['code'], '<remote Blender job>', 'exec'), namespace)
    except BaseException:
        result['status'] = 'failed'
        result['error'] = traceback.format_exc()
    result['output'] = captured.getvalue()[-100000:]
    atomic_json(JOBS / (job_id + '.result.json'), result)
    heartbeat()
    return 0.5


def tick():
    try:
        return poll_jobs()
    except Exception:
        try:
            (SESSION / 'worker_error.txt').write_text(traceback.format_exc(), encoding='utf-8')
        except OSError:
            pass
        return 1.0


def start():
    bpy.app.timers.register(tick, first_interval=1.0, persistent=True)
    heartbeat()
