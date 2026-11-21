"""Authenticated HTTP job queue for a trusted remote Blender coding agent."""
import hmac
import json
import os
import re
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
JOBS = ROOT / '.state' / 'jobs'
EXPORTS = ROOT / 'exports'
TOKEN = os.environ.get('BLENDER_BRIDGE_TOKEN', '')
if len(TOKEN) < 32:
    raise SystemExit('Set BLENDER_BRIDGE_TOKEN to a random value of at least 32 characters.')
JOBS.mkdir(parents=True, exist_ok=True)
EXPORTS.mkdir(exist_ok=True)


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    temporary.replace(path)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        # Request paths and credentials stay out of console logs.
        pass

    def reply(self, status, value):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        supplied = self.headers.get('Authorization', '')
        if not hmac.compare_digest(supplied.encode(), ('Bearer ' + TOKEN).encode()):
            self.reply(401, {'error': 'Valid Bearer token required'})
            return False
        return True

    def do_GET(self):
        if not self.authorized():
            return
        path = unquote(urlparse(self.path).path)
        if path == '/health':
            self.reply(200, {'bridge': 'online', 'blender': 'Submit a test job to verify Blender'})
        elif re.fullmatch(r'/jobs/[a-f0-9]{32}', path):
            job_id = path.rsplit('/', 1)[1]
            result = JOBS / (job_id + '.result.json')
            request = JOBS / (job_id + '.request.json')
            running = JOBS / (job_id + '.running.json')
            if result.exists():
                self.reply(200, json.loads(result.read_text(encoding='utf-8')))
            elif running.exists():
                self.reply(200, {'id': job_id, 'status': 'running'})
            elif request.exists():
                self.reply(200, {'id': job_id, 'status': 'queued'})
            else:
                self.reply(404, {'error': 'Unknown job'})
        elif path.startswith('/files/'):
            target = (EXPORTS / path.removeprefix('/files/')).resolve()
            if not target.is_relative_to(EXPORTS.resolve()) or not target.is_file():
                self.reply(404, {'error': 'Export file not found'})
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(target.stat().st_size))
            self.end_headers()
            with target.open('rb') as file:
                while chunk := file.read(256 * 1024):
                    self.wfile.write(chunk)
        else:
            self.reply(404, {'error': 'Unknown endpoint'})

    def do_POST(self):
        if not self.authorized():
            return
        if urlparse(self.path).path != '/jobs':
            self.reply(404, {'error': 'Unknown endpoint'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 512 * 1024:
                raise ValueError('Request must be between 1 byte and 512 KB')
            body = json.loads(self.rfile.read(length))
            code = body.get('code')
            if not isinstance(code, str) or not code.strip():
                raise ValueError('Provide a nonempty code string')
            compile(code, '<remote job>', 'exec')
        except (ValueError, SyntaxError, AttributeError) as error:
            self.reply(400, {'error': str(error)})
            return
        job_id = uuid.uuid4().hex
        write_json(JOBS / (job_id + '.request.json'), {'id': job_id, 'code': code})
        self.reply(202, {'id': job_id, 'status': 'queued'})


if __name__ == '__main__':
    print('Bridge listening on http://127.0.0.1:8765')
    print('Blender worker must also be running. Stop this server with Ctrl+C.')
    HTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
