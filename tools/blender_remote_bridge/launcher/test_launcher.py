"""Offline and isolated checks. Never uses the production port or Blender."""
import json
import os
from pathlib import Path
import queue
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

import core
import app


class SafetyChecks(unittest.TestCase):
    def test_external_sessions_block_launch_before_secrets_or_children(self):
        snapshots = [
            {'listeners': [{'OwningProcess': 4242}], 'apps': []},
            {'listeners': [], 'apps': [{'Name': 'blender.exe', 'ProcessId': 4242}]},
            {'listeners': [], 'apps': [{'Name': 'cloudflared.exe', 'ProcessId': 4242}]},
        ]
        for snapshot in snapshots:
            launcher = types.SimpleNamespace(events=queue.Queue(), config={})
            with patch.object(app, 'active_processes', return_value=snapshot), \
                    patch.object(app, 'launch_process') as spawn, \
                    patch.object(app, 'load_secret') as read_secret:
                app.Launcher.start_session(launcher)
            self.assertEqual(launcher.events.get()[0], 'blocked')
            spawn.assert_not_called()
            read_secret.assert_not_called()

    def test_credential_encryption(self):
        original = b'test-only-credential-roundtrip'
        encrypted = core.protect(original)
        self.assertNotEqual(encrypted, original)
        self.assertEqual(core.protect(encrypted, decrypt=True), original)

    def test_permanent_url_validation(self):
        self.assertEqual(core.validate_url('https://blender.example.com/'), 'https://blender.example.com')
        for invalid in ('http://blender.example.com', 'https://secret@example.com',
                        'https://example.com/jobs', 'https://example.com?token=abc'):
            with self.assertRaises(ValueError):
                core.validate_url(invalid)

    def test_worker_uses_isolated_session_and_returns_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / 'bridge/launcher/sessions/test'
            (session / 'jobs').mkdir(parents=True)
            register = unittest.mock.Mock()
            fake_bpy = types.SimpleNamespace(
                app=types.SimpleNamespace(timers=types.SimpleNamespace(register=register)),
                context=types.SimpleNamespace(preferences=types.SimpleNamespace(view=types.SimpleNamespace(show_splash=True))))
            source = (core.HERE / 'worker_entry.py').read_text()
            with patch.dict(os.environ, {'BLENDER_BRIDGE_SESSION': str(session)}), \
                    patch.dict(sys.modules, {'bpy': fake_bpy}):
                shutil.copy2(core.HERE / 'worker_runtime.py', session.parent.parent / 'worker_runtime.py')
                namespace = {'__file__': 'C:/worker_entry.py', '__name__': '__main__'}
                exec(compile(source, 'worker_entry.py', 'exec'), namespace)
                namespace.clear()
                tick = register.call_args.args[0]
                self.assertEqual(tick.__module__, '_launcher_blender_worker')
                self.assertTrue(register.call_args.kwargs['persistent'])
                jobs = session / 'jobs'
                job_id = '1' * 32
                core.atomic_json(jobs / (job_id + '.request.json'), {'code': "print('isolated worker executed')"})
                self.assertEqual(tick(), 0.5)
                result = core.read_json(jobs / (job_id + '.result.json'))
                self.assertEqual(result['status'], 'complete')
                self.assertIn('isolated worker executed', result['output'])
                job_id = '2' * 32
                core.atomic_json(jobs / (job_id + '.request.json'), {'code': "raise ValueError('test failure')"})
                tick()
                result = core.read_json(jobs / (job_id + '.result.json'))
                self.assertEqual(result['status'], 'failed')
                self.assertIn('test failure', result['error'])
                (session / 'stop_worker').touch()
                self.assertIsNone(tick())
                self.assertEqual(core.read_json(session / 'worker.json')['status'], 'stopped')


class IsolatedApiChecks(unittest.TestCase):
    def test_http_jobs_authentication_and_exports_in_temporary_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'bridge'
            launcher = root / 'launcher'
            launcher.mkdir(parents=True)
            shutil.copy2(core.BRIDGE / 'server.py', root / 'server.py')
            shutil.copy2(core.HERE / 'server_entry.py', launcher / 'server_entry.py')
            session = launcher / 'sessions/test'
            (session / 'jobs').mkdir(parents=True)
            with socket.socket() as reservation:
                reservation.bind(('127.0.0.1', 0))
                port = reservation.getsockname()[1]
            self.assertNotEqual(port, 8765)
            token = secrets.token_urlsafe(32)
            environment = dict(os.environ, BLENDER_BRIDGE_TOKEN=token,
                               BLENDER_BRIDGE_SESSION=str(session), BLENDER_BRIDGE_PORT=str(port))
            process = subprocess.Popen([sys.executable, str(launcher / 'server_entry.py')],
                                       env=environment, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, creationflags=core.HIDDEN)

            def request(path, payload=None, auth=True):
                headers = {'Authorization': 'Bearer ' + token} if auth else {}
                if payload is not None:
                    headers['Content-Type'] = 'application/json'
                req = urllib.request.Request(f'http://127.0.0.1:{port}' + path,
                                             data=None if payload is None else json.dumps(payload).encode(),
                                             headers=headers)
                return urllib.request.urlopen(req, timeout=2)

            try:
                for _ in range(50):
                    try:
                        with request('/health') as response:
                            health = json.load(response)
                        break
                    except OSError:
                        time.sleep(0.1)
                else:
                    self.fail('Isolated test server did not start')
                self.assertEqual(health['blender'], 'waiting')
                with self.assertRaises(urllib.error.HTTPError) as error:
                    request('/health', auth=False)
                self.assertEqual(error.exception.code, 401)
                error.exception.close()
                with request('/jobs', {'code': "print('safe test')"}) as response:
                    self.assertEqual(response.status, 202)
                    job = json.load(response)
                self.assertTrue((session / 'jobs' / (job['id'] + '.request.json')).exists())
                with request('/jobs/' + job['id']) as response:
                    self.assertEqual(json.load(response)['status'], 'queued')
                core.atomic_json(session / 'jobs' / (job['id'] + '.result.json'),
                                 {'id': job['id'], 'status': 'complete', 'output': 'test'})
                with request('/jobs/' + job['id']) as response:
                    self.assertEqual(json.load(response)['output'], 'test')
                (root / 'exports' / 'test.txt').write_text('export test')
                with request('/files/test.txt') as response:
                    self.assertEqual(response.read(), b'export test')
                with self.assertRaises(urllib.error.HTTPError) as error:
                    request('/files/../server.py')
                self.assertEqual(error.exception.code, 404)
                error.exception.close()
            finally:
                process.terminate()
                process.wait(timeout=5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
