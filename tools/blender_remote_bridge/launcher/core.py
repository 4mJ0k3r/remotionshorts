"""Local process discovery, Windows-protected credentials and launch helpers."""
import ctypes
from ctypes import wintypes
import http.client
import ipaddress
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import sys
from urllib.parse import urlparse
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
BRIDGE = HERE.parent
PROJECT = BRIDGE.parent.parent
PORT = 8765
HIDDEN = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)


def read_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def powershell_json(script):
    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script],
        capture_output=True, text=True, creationflags=HIDDEN, timeout=15,
    )
    if result.returncode:
        raise RuntimeError('Windows process detection failed. Close and reopen the launcher.')
    return json.loads(result.stdout.strip() or 'null')


def active_processes():
    """Read OS metadata only. Never connect to an already-running bridge."""
    return powershell_json("""
        $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8765 -ErrorAction SilentlyContinue)
        $apps = @(Get-CimInstance Win32_Process -Filter "Name = 'blender.exe' OR Name = 'cloudflared.exe'" |
            Select-Object Name,ProcessId,ExecutablePath)
        @{listeners=@($listeners | Select-Object OwningProcess); apps=$apps} | ConvertTo-Json -Depth 4 -Compress
    """)


def external_conflict(snapshot, owned_pids=()):
    owned = set(owned_pids)
    if any(item['OwningProcess'] not in owned for item in snapshot.get('listeners', [])):
        return 'A bridge is already using port 8765. Keep using that session until its work finishes.'
    if any(app['Name'].lower() == 'blender.exe' and app['ProcessId'] not in owned
           for app in snapshot.get('apps', [])):
        return 'Blender is already open. Finish and save that session, then close it before starting a new launcher session.'
    if any(app['Name'].lower() == 'cloudflared.exe' and app['ProcessId'] not in owned
           for app in snapshot.get('apps', [])):
        return 'A tunnel is already running outside this launcher. Finish that session before starting a new one.'
    return ''


def find_blender():
    # The Windows Store alias forwards arguments without starting the protected
    # package executable directly. Conventional installations use blender.exe.
    alias = shutil.which('blender-launcher.exe')
    if alias:
        return alias
    found = shutil.which('blender.exe')
    if found:
        return found
    folder = Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Blender Foundation'
    matches = sorted(folder.glob('Blender*/blender.exe'), reverse=True)
    return str(matches[0]) if matches else ''


def find_cloudflared():
    found = shutil.which('cloudflared.exe')
    if found:
        return found
    for folder in ('PROGRAMFILES(X86)', 'PROGRAMFILES'):
        path = Path(os.environ.get(folder, 'C:/Program Files')) / 'cloudflared/cloudflared.exe'
        if path.is_file():
            return str(path)
    return ''


def console_python():
    current = Path(sys.executable)
    candidate = current.with_name('python.exe')
    return str(candidate if candidate.exists() else current)


class Blob(ctypes.Structure):
    _fields_ = [('length', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def protect(data, decrypt=False):
    """DPAPI encryption bound to the current Windows user's profile."""
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        function = crypt.CryptUnprotectData
        result = function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output))
    else:
        function = crypt.CryptProtectData
        result = function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output))
    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(output.data, output.length)
    finally:
        kernel.LocalFree(output.data)


def save_secret(name, text):
    path = HERE / '.private' / (name + '.bin')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_bytes(protect(text.encode('utf-8')))
    temporary.replace(path)


def load_secret(name):
    path = HERE / '.private' / (name + '.bin')
    return protect(path.read_bytes(), decrypt=True).decode('utf-8') if path.exists() else ''


def validate_url(value):
    parsed = urlparse(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
        raise ValueError('Enter an HTTPS hostname, for example https://blender.example.com')
    return value.rstrip('/')


def launch_process(arguments, log_path, environment):
    with log_path.open('ab', buffering=0) as log:
        return subprocess.Popen(
            arguments, cwd=PROJECT, env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, creationflags=HIDDEN,
        )


def health_request(base, token):
    """Use normal HTTPS first, then public DNS only when local lookup fails.

    The fallback keeps the original TLS server name and certificate checks.
    It never changes Windows DNS settings or substitutes an HTTP connection.
    """
    url = base.rstrip('/') + '/health'
    headers = {'Authorization': 'Bearer ' + token}
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)
    except urllib.error.URLError as error:
        if not isinstance(error.reason, socket.gaierror) or not url.startswith('https://'):
            raise
    parsed = urlparse(url)
    dns_url = 'https://cloudflare-dns.com/dns-query?name=' + parsed.hostname + '&type=A'
    request = urllib.request.Request(dns_url, headers={'Accept': 'application/dns-json'})
    with urllib.request.urlopen(request, timeout=5) as response:
        answers = json.load(response).get('Answer', [])
    addresses = [str(ipaddress.IPv4Address(answer['data'])) for answer in answers if answer.get('type') == 1]
    if not addresses:
        raise RuntimeError('The tunnel hostname has not been published in public DNS yet.')
    last_error = None
    for address in addresses:
        connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                timeout=5, context=ssl.create_default_context())
        # HTTPConnection uses this hook to open the transport. The hostname
        # remains unchanged for Host, SNI and TLS certificate verification.
        connection._create_connection = lambda endpoint, timeout, source_address=None, ip=address: socket.create_connection(
            (ip, endpoint[1]), timeout, source_address)
        try:
            connection.request('GET', '/health', headers=headers)
            response = connection.getresponse()
            if response.status != 200:
                raise RuntimeError(f'Tunnel health returned HTTP {response.status}.')
            return json.loads(response.read())
        except (OSError, http.client.HTTPException) as error:
            last_error = error
        finally:
            connection.close()
    raise last_error
