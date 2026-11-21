"""Serial, restartable native 1080p deliveries with exclusive GPU ownership."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BLENDER = Path(os.environ.get('BLENDER_EXE', 'D:/tools/Blender/4.2.23/blender.exe'))
LOCK = ROOT / '.blender_gpu.lock'
STATE = ROOT / 'renders/native_1080_batch.json'
PROJECTS = [
    dict(id='farmer_owns_train', source=ROOT/'renders/farmer_owns_train/farmer_owns_train_v2_overhaul_source.blend',
         runtime='farmer_runtime.py', frames=1668, samples=[55, 840, 1600], output='farmer_owns_train_v3_master_1080p.mp4'),
    dict(id='crorepati_poop_love', source=ROOT/'crorepati_poop_love_v2.blend',
         runtime='crorepati_runtime.py', frames=2124, samples=[35, 980, 1980], output='crorepati_poop_love_v2_master_1080p.mp4'),
    dict(id='sendha_namak_science', source=ROOT/'renders/sendha_namak_science/sendha_namak_v2_render_source.blend',
         runtime='sendha_runtime.py', frames=1728, samples=[60, 800, 1585], output='sendha_namak_v2_master_1080p.mp4'),
]


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


def gpu_available():
    command = "@(Get-CimInstance Win32_Process -Filter \"Name='blender.exe'\").Count"
    count = subprocess.check_output(['powershell', '-NoProfile', '-Command', command], text=True)
    browsers = subprocess.check_output(['powershell', '-NoProfile', '-Command',
        "@(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe' OR Name='msedge.exe' OR Name='chromium.exe'\" | Where-Object {$_.CommandLine -match '--headless'}).Count"], text=True)
    return int(count.strip()) == 0 and int(browsers.strip()) == 0


def freeze(project):
    base = ROOT / 'renders' / project['id']
    folder = base / 'native_1080_v2'
    folder.mkdir(exist_ok=True)
    inputs = {'source': Path(project['source']), 'audio': base/'narration.wav',
              'envelope': base/'audio_env.json', 'worker': HERE/'worker.py'}
    identity = {'hashes': {key: digest(path) for key, path in inputs.items()},
                'size': [1080, 1920], 'fps': 30, 'samples': 16, 'frames': project['frames']}
    manifest = folder / 'manifest.json'
    if manifest.exists() and json.loads(manifest.read_text()) != identity:
        raise RuntimeError(f'{project["id"]}: source identity changed; retain this cache and use a new version.')
    if not manifest.exists():
        for key, path in inputs.items():
            shutil.copy2(path, folder / {'source': 'render_source.blend', 'audio': 'narration.wav',
                                       'envelope': 'audio_env.json', 'worker': 'worker.py'}[key])
        save(manifest, identity)
    config = {key: value for key, value in project.items() if key != 'source'}
    config['directory'] = str(folder)
    save(folder/'config.json', config)
    return folder, inputs, identity


def valid_frame(folder, frame):
    path = folder/'frames'/f'frame_{frame:04d}.png'
    if not path.exists():
        return False
    try:
        with Image.open(path) as image:
            if image.size != (1080, 1920):
                return False
            image.verify()
        return True
    except OSError:
        return False


def worker(folder, mode, a=0, b=0):
    arguments = [str(BLENDER), '-b', '--factory-startup', '--python-exit-code', '1',
                 str(folder/'render_source.blend'), '--python', str(folder/'worker.py'),
                 '--', str(folder/'config.json'), mode, str(a), str(b)]
    with (folder/f'{mode}_{a:04d}_{b:04d}.log').open('w') as log:
        child = subprocess.Popen(arguments, stdout=log, stderr=subprocess.STDOUT)
        try:
            code = child.wait()
        except BaseException:
            child.terminate()
            child.wait()
            raise
    if code:
        raise RuntimeError(f'Blender failed ({code}). See {folder}/{mode}_{a:04d}_{b:04d}.log')


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))


def deliver(project, folder):
    final = folder.parent/project['output']
    temporary = folder/'encoding.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', '30', '-start_number', '1',
                    '-i', str(folder/'frames/frame_%04d.png'), '-i', str(folder/'narration.wav'),
                    '-frames:v', str(project['frames']), '-t', str(project['frames']/30),
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-metadata:s:a:0', 'language=hin',
                    '-movflags', '+faststart', str(temporary)], check=True)
    data = probe(temporary)
    video = next(stream for stream in data['streams'] if stream['codec_type'] == 'video')
    assert (video['width'], video['height'], int(video['nb_frames']), video['r_frame_rate']) == (1080,1920,project['frames'],'30/1')
    assert abs(float(data['format']['duration']) - project['frames']/30) < .04
    assert any(stream['codec_type'] == 'audio' for stream in data['streams'])
    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(temporary), '-f', 'null', '-'], check=True)
    temporary.replace(final)
    save(folder/'delivery_probe.json', data)
    with (folder/'qa.log').open('w') as log:
        command = [sys.executable, str(ROOT/'scripts/short_qa.py'), str(final), str(folder/'qa')]
        shots = folder.parent/'shots.json'
        if shots.exists():
            command.append(str(shots))
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
    return final


def run():
    if not BLENDER.is_file():
        raise FileNotFoundError(BLENDER)
    completed = []
    for project in PROJECTS:
        folder, inputs, identity = freeze(project)
        owner = uuid.uuid4().hex
        while True:
            save(STATE, {'project': project['id'], 'status': 'waiting_for_gpu', 'completed': completed})
            if not LOCK.exists() and gpu_available():
                try:
                    descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    with os.fdopen(descriptor, 'w') as file:
                        json.dump({'project': project['id'], 'pid': os.getpid(), 'owner': owner, 'phase': '1080p'}, file)
                    break
                except FileExistsError:
                    pass
            time.sleep(10)
        try:
            if not gpu_available():
                raise RuntimeError('Another renderer appeared before launch. Retry when it exits.')
            if not (folder/'benchmark.json').exists():
                save(STATE, {'project': project['id'], 'status': 'benchmark', 'completed': completed})
                worker(folder, 'benchmark')
            times = json.loads((folder/'benchmark.json').read_text())
            mean = sum(item['seconds'] for item in times)/len(times)
            print('BENCHMARK',project['id'],round(mean,2),'seconds/frame',flush=True)
            state = {'project': project['id'], 'status': 'rendering', 'completed': completed,
                     'estimate_minutes': [round(mean*project['frames']/60*.8), round(mean*project['frames']/60*1.4)]}
            save(STATE, state)
            missing = [f for f in range(1,project['frames']+1) if not valid_frame(folder,f)]
            for first in range(min(missing) if missing else project['frames']+1, project['frames']+1,144):
                last = min(first+143,project['frames'])
                if all(valid_frame(folder,f) for f in range(first,last+1)):
                    continue
                if any(digest(path) != identity['hashes'][key] for key,path in inputs.items()):
                    raise RuntimeError('Production inputs changed during rendering.')
                worker(folder,'movie',first,last)
                if not all(valid_frame(folder,f) for f in range(first,last+1)):
                    raise RuntimeError(f'Incomplete frames in {first}–{last}')
            if not all(valid_frame(folder,f) for f in range(1,project['frames']+1)):
                raise RuntimeError('Frame cache has a gap')
        finally:
            if LOCK.exists() and json.loads(LOCK.read_text()).get('owner') == owner:
                LOCK.unlink()
        save(STATE, {'project': project['id'], 'status': 'encoding_and_qa', 'completed': completed})
        final = deliver(project,folder)
        completed.append(str(final))
        print('DELIVERED',final,flush=True)
    save(STATE, {'status': 'complete', 'completed': completed})


if __name__ == '__main__':
    try:
        run()
    except BaseException as error:
        data = json.loads(STATE.read_text()) if STATE.exists() else {}
        data.update(status='failed', error=str(error))
        save(STATE,data)
        raise
