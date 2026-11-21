"""Double-click launcher for future Blender bridge sessions."""
import os
import queue
import re
import secrets
import subprocess
import threading
import time
import uuid
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import urllib.request
import json

from core import (
    HERE, PROJECT, PORT, active_processes, atomic_json, console_python,
    external_conflict, find_blender, find_cloudflared, launch_process,
    load_secret, read_json, save_secret, validate_url, health_request,
)

PROMPT = '''Connect to my local Blender using the server-side environment secrets
BLENDER_BRIDGE_URL and BLENDER_BRIDGE_TOKEN. The current URL is {url}.
Keep credentials on the server and out of frontend code, Git and logs.

Every request requires Authorization: Bearer followed by BLENDER_BRIDGE_TOKEN.
Endpoints are GET /health, POST /jobs with {{"code": "Python code"}},
GET /jobs/{{id}}, and GET /files/{{relative_export_filename}}.
Submit a job, retain its ID and poll it until complete or failed. Do not submit
duplicate jobs when Blender is busy. A long render can keep a job running.
The Python namespace includes bpy and EXPORT_DIR, a pathlib.Path to the
downloadable exports folder. Save files for retrieval into EXPORT_DIR.

Use D:\\remotionshorts as the local working repository. Before making changes,
read AGENTS.md, ANIMATION_STYLE_HANDOFF.md, BLENDER_SKILL.md,
animated-3d-story-video/SKILL.md and its references/cel-studio-contract.md.
Inspect relevant existing assets and scripts. Follow the current user's brief
and authorized stage. Save a checkpoint before changing the open scene.
Render calibration frames, retrieve and inspect them, correct defects, and
benchmark representative frames before an authorized full render. Verify the
final video dimensions, frame count, duration and audio.

Confirm /health and execute a small read-only scene inspection first. Then
wait for my animation brief. Keep all production work in its own project
folders. The bridge starts a fresh job queue each time the launcher starts.
'''


class Launcher:
    def __init__(self, window):
        self.window = window
        self.events = queue.Queue()
        self.processes = {}
        self.session = None
        self.url = ''
        self.token = ''
        self.starting = False
        self.stopping = False
        self.active = False
        self.external = False
        self.ready = False
        self.next_check = 0
        self.config = read_json(HERE / 'config.json', {})
        window.title('Blender Bridge Launcher')
        window.geometry('800x610')
        window.minsize(740, 590)
        window.configure(bg='#f3f5f7')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f3f5f7')
        style.configure('TLabel', background='#f3f5f7', foreground='#182536')
        style.configure('Title.TLabel', font=('Segoe UI', 20, 'bold'))
        style.configure('Status.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('TButton', padding=(12, 9), font=('Segoe UI', 10))
        main = ttk.Frame(window, padding=24)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text='Blender Bridge', style='Title.TLabel').pack(anchor='w')
        ttk.Label(main, text='Connect your web agent to Blender and your local animation project.').pack(anchor='w', pady=(4, 20))
        self.status = tk.StringVar(value='Checking for an existing session…')
        ttk.Label(main, textvariable=self.status, style='Status.TLabel', wraplength=710).pack(anchor='w')
        self.detail = tk.StringVar(value='')
        ttk.Label(main, textvariable=self.detail, wraplength=710).pack(anchor='w', pady=(6, 16))
        controls = ttk.Frame(main)
        controls.pack(fill='x')
        self.start_button = ttk.Button(controls, text='Start bridge', command=self.start)
        self.start_button.pack(side='left')
        self.stop_button = ttk.Button(controls, text='Stop bridge', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=8)
        self.settings_button = ttk.Button(controls, text='Settings', command=self.settings)
        self.settings_button.pack(side='right')
        ttk.Label(main, text='Connection address').pack(anchor='w', pady=(22, 5))
        self.url_text = tk.StringVar(value='Available after the launcher starts its own session')
        ttk.Entry(main, textvariable=self.url_text, state='readonly').pack(fill='x')
        copy_buttons = ttk.Frame(main)
        copy_buttons.pack(fill='x', pady=12)
        self.prompt_button = ttk.Button(copy_buttons, text='Copy agent prompt', command=self.copy_prompt, state='disabled')
        self.prompt_button.pack(side='left')
        self.token_button = ttk.Button(copy_buttons, text='Copy access token', command=self.copy_token, state='disabled')
        self.token_button.pack(side='left', padx=8)
        ttk.Button(copy_buttons, text='Open exports', command=lambda: os.startfile(HERE.parent / 'exports')).pack(side='right')
        ttk.Label(main, text='First use: paste the access token into the web agent’s server-side secrets.\n'
                  'The same saved token is reused on later launches.', wraplength=710).pack(anchor='w', pady=(0, 14))
        self.log = tk.Text(main, height=8, wrap='word', font=('Segoe UI', 10), bg='white', fg='#263545', relief='flat', padx=12, pady=10)
        self.log.pack(fill='both', expand=True)
        self.log.configure(state='disabled')
        ttk.Label(main, text='Full Blender Python access is granted to the trusted agent holding your token.', wraplength=710).pack(anchor='w', pady=(12, 0))
        window.protocol('WM_DELETE_WINDOW', self.close)
        window.after(100, self.check_external)
        window.after(500, self.tick)

    def note(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def check_external(self):
        def inspect():
            try:
                conflict = external_conflict(active_processes())
                self.events.put(('external', conflict))
            except Exception:
                self.events.put(('external', 'Could not check running applications. Check again before starting.'))
        threading.Thread(target=inspect, daemon=True).start()

    def settings(self):
        if self.active or self.starting:
            messagebox.showinfo('Session running', 'Stop this launcher session before changing its settings.')
            return
        dialog = tk.Toplevel(self.window)
        dialog.title('Bridge settings')
        dialog.transient(self.window)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill='both', expand=True)
        fields = {}
        for name, title, default in [
            ('blender', 'Blender executable', self.config.get('blender') or find_blender()),
            ('cloudflared', 'Cloudflare executable', self.config.get('cloudflared') or find_cloudflared()),
        ]:
            ttk.Label(frame, text=title).pack(anchor='w', pady=(8, 3))
            row = ttk.Frame(frame)
            row.pack(fill='x')
            value = tk.StringVar(value=default)
            fields[name] = value
            ttk.Entry(row, textvariable=value, width=70).pack(side='left', fill='x', expand=True)
            def browse(destination=value):
                path = filedialog.askopenfilename(filetypes=[('Executable', '*.exe')])
                if path:
                    destination.set(path)
            ttk.Button(row, text='Browse', command=browse).pack(side='left', padx=(8, 0))
        mode = tk.StringVar(value=self.config.get('mode', 'temporary'))
        ttk.Label(frame, text='Tunnel address').pack(anchor='w', pady=(20, 4))
        ttk.Radiobutton(frame, text='Temporary address — copy the updated prompt each session', variable=mode, value='temporary').pack(anchor='w')
        ttk.Radiobutton(frame, text='Permanent Cloudflare hostname — requires a configured named tunnel', variable=mode, value='permanent').pack(anchor='w')
        ttk.Label(frame, text='Permanent HTTPS address').pack(anchor='w', pady=(12, 3))
        permanent = tk.StringVar(value=self.config.get('url', ''))
        ttk.Entry(frame, textvariable=permanent, width=70).pack(fill='x')
        ttk.Label(frame, text='Cloudflare tunnel token (leave blank to keep the stored token)').pack(anchor='w', pady=(12, 3))
        tunnel_token = tk.StringVar()
        ttk.Entry(frame, textvariable=tunnel_token, show='•').pack(fill='x')
        ttk.Label(frame, text='Set the named tunnel’s public route to http://127.0.0.1:8765.\n'
                  'The tunnel token and the agent’s bridge access token are separate credentials.', wraplength=620).pack(anchor='w', pady=(10, 15))
        def save():
            try:
                config = {name: value.get().strip() for name, value in fields.items()}
                for path in config.values():
                    if not Path(path).is_file():
                        raise ValueError('Choose existing Blender and Cloudflare executables.')
                config['mode'] = mode.get()
                config['url'] = validate_url(permanent.get().strip()) if mode.get() == 'permanent' else ''
                credential = tunnel_token.get().strip()
                if mode.get() == 'permanent' and not (credential or load_secret('tunnel')):
                    raise ValueError('Paste the named tunnel token from Cloudflare.')
                if credential:
                    save_secret('tunnel', credential)
                atomic_json(HERE / 'config.json', config)
                self.config = config
                dialog.destroy()
                self.note('Settings saved for the next launcher session.')
            except Exception as error:
                messagebox.showerror('Settings', str(error), parent=dialog)
        ttk.Button(frame, text='Save settings', command=save).pack(anchor='e')

    def start(self):
        if self.starting or self.active:
            return
        self.starting = True
        self.start_button.configure(state='disabled')
        self.settings_button.configure(state='disabled')
        self.status.set('Checking that the current session is finished…')
        threading.Thread(target=self.start_session, daemon=True).start()

    def start_session(self):
        try:
            conflict = external_conflict(active_processes())
            if conflict:
                self.events.put(('blocked', conflict))
                return
            blender = self.config.get('blender') or find_blender()
            tunnel = self.config.get('cloudflared') or find_cloudflared()
            if not blender or not Path(blender).is_file() or not tunnel or not Path(tunnel).is_file():
                raise RuntimeError('Select the Blender and Cloudflare executables in Settings.')
            self.token = load_secret('access')
            if not self.token:
                self.token = secrets.token_urlsafe(32)
                save_secret('access', self.token)
            mode = self.config.get('mode', 'temporary')
            tunnel_credential = load_secret('tunnel') if mode == 'permanent' else ''
            if mode == 'permanent':
                self.url = validate_url(self.config.get('url', ''))
                if not tunnel_credential:
                    raise RuntimeError('Save the Cloudflare tunnel token in Settings.')
            self.session = HERE / 'sessions' / (time.strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8])
            (self.session / 'jobs').mkdir(parents=True)
            environment = os.environ.copy()
            environment['BLENDER_BRIDGE_TOKEN'] = self.token
            environment['BLENDER_BRIDGE_SESSION'] = str(self.session)
            environment['BLENDER_BRIDGE_PORT'] = str(PORT)
            # Prevent inherited credentials for unrelated tunnels from changing
            # temporary mode. Tokens never enter process command-line arguments.
            environment.pop('TUNNEL_TOKEN', None)
            self.processes['server'] = launch_process(
                [console_python(), str(HERE / 'server_entry.py')], self.session / 'server.log', environment)
            for _ in range(30):
                time.sleep(0.2)
                if self.processes['server'].poll() is not None:
                    raise RuntimeError('The bridge could not start. Another session may have claimed its port.')
                try:
                    self.health()
                    break
                except Exception:
                    continue
            else:
                raise RuntimeError('The new local server did not respond.')
            # Do not pass the access token to Blender. Its file queue needs no
            # network credential. A separate process owns this launch only.
            blender_environment = environment.copy()
            blender_environment.pop('BLENDER_BRIDGE_TOKEN', None)
            # Prevent stale Python environment customizations from a shell from
            # redirecting Blender's bundled Python imports.
            blender_environment.pop('PYTHONHOME', None)
            blender_environment.pop('PYTHONPATH', None)
            self.processes['blender'] = launch_process(
                [blender, '--python', str(HERE / 'worker_entry.py')], self.session / 'blender.log', blender_environment)
            self.events.put(('note', 'Opening Blender and loading the worker automatically…'))
            for _ in range(120):
                if read_json(self.session / 'worker.json'):
                    break
                time.sleep(0.5)
            else:
                raise RuntimeError('Blender did not load the worker. Choose its executable in Settings. The opened Blender is left available for inspection.')
            if mode == 'permanent':
                environment['TUNNEL_TOKEN'] = tunnel_credential
                arguments = [tunnel, 'tunnel', '--no-autoupdate', 'run']
            else:
                arguments = [tunnel, 'tunnel', '--no-autoupdate', '--url', f'http://127.0.0.1:{PORT}']
            self.processes['tunnel'] = launch_process(arguments, self.session / 'tunnel.log', environment)
            for _ in range(150):
                time.sleep(0.4)
                if self.processes['tunnel'].poll() is not None:
                    raise RuntimeError('Cloudflare exited. Check the tunnel settings and network connection.')
                log = (self.session / 'tunnel.log').read_text(encoding='utf-8', errors='replace')
                if mode == 'temporary':
                    match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', log)
                    if match:
                        self.url = match.group()
                        break
                elif 'Registered tunnel connection' in log:
                    break
            else:
                raise RuntimeError('Cloudflare did not establish a tunnel within one minute.')
            self.events.put(('started', mode))
        except Exception as error:
            self.cleanup()
            self.events.put(('error', str(error)))

    def health(self, remote=False):
        base = self.url if remote else f'http://127.0.0.1:{PORT}'
        return health_request(base, self.token)

    def busy(self):
        if not self.session:
            return False
        return any(not path.with_name(path.name.replace('.running.json', '.result.json')).exists()
                   for path in (self.session / 'jobs').glob('*.running.json'))

    def cleanup(self):
        # Never kill Blender or an external process. Stop accepting new jobs and
        # ask this session's worker to retire on its next idle timer callback.
        if self.session:
            (self.session / 'stop_worker').touch()
        for name in ('tunnel', 'server'):
            child = self.processes.get(name)
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)

    def stop(self):
        if not self.active or self.stopping:
            return
        if self.busy():
            messagebox.showinfo('Blender is working', 'A Blender job is running. Let the job finish before stopping this connection.')
            return
        pending = list((self.session / 'jobs').glob('*.request.json'))
        if pending and not messagebox.askyesno('Queued jobs', 'Jobs are waiting. Stop the bridge and leave those jobs unexecuted in this session folder?'):
            return
        self.stopping = True
        self.stop_button.configure(state='disabled')
        def stop_owned():
            self.cleanup()
            self.events.put(('stopped', 'Bridge stopped. Save and close Blender before the next fresh launch.'))
        threading.Thread(target=stop_owned, daemon=True).start()

    def copy_prompt(self):
        if not self.ready:
            return
        self.copy(PROMPT.format(url=self.url))
        self.note('Agent prompt copied. It includes the address and never includes your token.')

    def copy_token(self):
        if self.token:
            self.copy(self.token)
            self.note('Access token copied. Paste it only into the web agent’s server-side secret field.')

    def copy(self, text):
        self.window.clipboard_clear()
        self.window.clipboard_append(text)

    def monitor(self):
        try:
            failed = next((name for name in ('server', 'tunnel') if self.processes[name].poll() is not None), None)
            if failed:
                self.events.put(('offline', failed + ' process stopped. Existing Blender work remains open.'))
                return
            local = self.health()
            remote = self.health(remote=True)
            if remote.get('session') != self.session.name:
                raise RuntimeError('The public address is reaching a different session.')
            self.events.put(('health', local.get('blender', 'waiting')))
        except Exception:
            self.events.put(('unreachable', 'Waiting for the public tunnel to reach this session. Check its route if this persists.'))

    def tick(self):
        try:
            while True:
                kind, text = self.events.get_nowait()
                if kind == 'note':
                    self.note(text)
                elif kind in ('external', 'blocked'):
                    self.external = bool(text)
                    self.starting = False
                    self.start_button.configure(state='normal')
                    self.settings_button.configure(state='normal')
                    self.status.set('Existing session detected' if text else 'Ready to start a new session')
                    self.detail.set(text or 'Start opens Blender and connects the local bridge.')
                    if text:
                        self.note(text + ' Its processes have been left alone.')
                elif kind == 'started':
                    self.starting = False
                    self.active = True
                    self.ready = False
                    self.url_text.set(self.url)
                    self.stop_button.configure(state='normal')
                    self.token_button.configure(state='normal')
                    self.status.set('Tunnel started — checking its public connection…')
                    self.detail.set('The public address may take a short time to become reachable.')
                    self.note('Blender worker and local server are running in this launcher session.')
                    if text == 'temporary':
                        self.note('Temporary mode uses a new URL each session. Settings also supports a permanent named tunnel.')
                elif kind == 'health':
                    self.ready = True
                    self.prompt_button.configure(state='normal')
                    self.status.set('Connected — Blender is ' + text)
                    self.detail.set('Copy the agent prompt, then send your animation brief. Keep this launcher and Blender open.')
                elif kind in ('unreachable', 'offline'):
                    self.ready = False
                    self.prompt_button.configure(state='disabled')
                    self.status.set('Connection needs attention')
                    self.detail.set(text)
                elif kind in ('error', 'stopped'):
                    self.starting = False
                    self.stopping = False
                    self.active = False
                    self.ready = False
                    self.start_button.configure(state='normal')
                    self.settings_button.configure(state='normal')
                    self.stop_button.configure(state='disabled')
                    self.prompt_button.configure(state='disabled')
                    self.token_button.configure(state='disabled')
                    self.status.set('Stopped' if kind == 'stopped' else 'Could not start')
                    self.detail.set(text)
                    self.note(text)
                    if kind == 'error':
                        messagebox.showerror('Bridge launcher', text)
        except queue.Empty:
            pass
        if self.active and not self.stopping and time.monotonic() > self.next_check:
            self.next_check = time.monotonic() + 12
            threading.Thread(target=self.monitor, daemon=True).start()
        self.window.after(500, self.tick)

    def close(self):
        if self.starting or self.active or self.stopping:
            self.window.iconify()
            return
        self.window.destroy()


if __name__ == '__main__':
    # Hold a local lock for this launcher only. Existing hand-started services
    # are discovered separately and are never adopted or stopped.
    import msvcrt
    (HERE / '.private').mkdir(exist_ok=True)
    guard = (HERE / '.private' / 'launcher.lock').open('a+b')
    guard.seek(0)
    if not guard.read(1):
        guard.write(b'1')
        guard.flush()
    guard.seek(0)
    window = tk.Tk()
    try:
        msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        window.withdraw()
        messagebox.showinfo('Blender Bridge', 'A launcher window is already open. Check your taskbar.')
        window.destroy()
    else:
        Launcher(window)
        window.mainloop()
    guard.close()
