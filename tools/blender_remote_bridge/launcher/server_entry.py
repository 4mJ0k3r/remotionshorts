"""Future launcher server. Existing server.py remains unmodified."""
import importlib.util
import os
from pathlib import Path
from http.server import ThreadingHTTPServer
import json
import time

HERE = Path(__file__).resolve().parent
SESSION = Path(os.environ['BLENDER_BRIDGE_SESSION'])
spec = importlib.util.spec_from_file_location('bridge_api', HERE.parent / 'server.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
api.JOBS = SESSION / 'jobs'
api.JOBS.mkdir(parents=True, exist_ok=True)


class Handler(api.Handler):
    def do_GET(self):
        if self.path == '/health':
            if not self.authorized():
                return
            try:
                worker = json.loads((SESSION / 'worker.json').read_text(encoding='utf-8'))
            except (OSError, ValueError):
                worker = {}
            busy = any(not item.with_name(item.name.replace('.running.json', '.result.json')).exists()
                       for item in api.JOBS.glob('*.running.json'))
            age = time.time() - worker.get('updated', 0)
            state = 'busy' if busy else 'ready' if age < 10 else 'waiting'
            self.reply(200, {'bridge': 'online', 'blender': state, 'worker_age_seconds': round(age, 1),
                             'session': SESSION.name})
            return
        super().do_GET()


if __name__ == '__main__':
    # One worker executes jobs serially. HTTP polling and downloads remain
    # responsive while that worker renders. Credentials are never logged.
    port = int(os.environ.get('BLENDER_BRIDGE_PORT', '8765'))
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
