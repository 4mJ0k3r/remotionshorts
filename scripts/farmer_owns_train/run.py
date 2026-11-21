"""Single-GPU owner-checked runner for farmer_owns_train V2 20-cut overhaul."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).resolve().parent
OUT = ROOT / 'renders' / 'farmer_owns_train'
AUDIO = Path(os.environ.get('FARMER_TRAIN_AUDIO', str(OUT / 'source_audio.mp3')))
BLENDER = Path(os.environ.get('BLENDER_EXE', 'D:/tools/Blender/4.2.23/blender.exe'))
SYS_PY = os.environ.get('SYS_PYTHON', 'C:/Program Files/Python314/python.EXE')
LOCK = ROOT / '.blender_gpu.lock'

FRAMES_16 = [55, 165, 248, 305, 375, 465, 538, 625, 735, 840, 900, 1035, 1135, 1248, 1302, 1455]
LABELS_16 = [
    '1A-1 | Hero Farmer & Shatabdi',
    '1A-2 | Farmer Tight CU (58mm)',
    '1B-1 | Coin & Ban Slam Macro',
    '1B-2 | Farmer Wink & Shrug CU',
    '2A-1 | Officer Yanks Car Tow',
    '2A-2 | Citizen Clenched Teeth CU',
    '2B | Uno Reverse Arrows CU',
    '2C-1 | Farmland Grass & Sack',
    '2C-2 | Official & Calendar CU',
    '3A-1 | Judge Glare & Gavel CU',
    '3A-2 | Gavel Slam & Seal Macro',
    '3B | 12cm Stride & Arm Swing',
    '3C-1 | Shatabdi Brakes & Steam',
    '4A-1 | Bailiff Serves Warrant CU',
    '4A-2 | Pilot Inside Cab Window CU',
    '4C-1 | Coach Passengers Worry CU',
]
SHOT_DEFS = [
    ('1A-1', 1, 110), ('1A-2', 110, 222), ('1B-1', 222, 275), ('1B-2', 275, 333),
    ('2A-1', 333, 420), ('2A-2', 420, 507), ('2B', 507, 570), ('2C-1', 570, 680),
    ('2C-2', 680, 792), ('3A-1', 792, 885), ('3A-2', 885, 981), ('3B', 981, 1095),
    ('3C-1', 1095, 1165), ('3C-2', 1165, 1221), ('4A-1', 1221, 1275), ('4A-2', 1275, 1329),
    ('4B', 1329, 1422), ('4C-1', 1422, 1505), ('4C-2', 1505, 1585), ('4C-3', 1585, 1669),
]


def others():
    p = subprocess.run(
        [
            'powershell', '-NoProfile', '-Command',
            'Get-CimInstance Win32_Process -Filter "Name=\'blender.exe\'" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress',
        ],
        capture_output=True, text=True, check=True,
    )
    rows = json.loads(p.stdout) if p.stdout.strip() else []
    if isinstance(rows, dict):
        rows = [rows]
    return [r for r in rows if any(t in (r.get('CommandLine') or '').split() for t in ['-b', '--background'])]


def launch(mode, a=None, b=None, res_w=360, res_h=640):
    if not BLENDER.is_file():
        raise FileNotFoundError(f'Blender executable not found: {BLENDER}')
    OUT.mkdir(parents=True, exist_ok=True)
    owner = str(uuid.uuid4())
    while True:
        if LOCK.exists() or others():
            print('Waiting for the active GPU owner.', flush=True)
            time.sleep(15)
            continue
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            continue
        with os.fdopen(fd, 'w') as file:
            json.dump({'project': 'farmer_owns_train', 'owner': owner, 'pid': os.getpid(), 'phase': mode}, file)
        break
    process = None
    try:
        if others():
            raise RuntimeError('Another background Blender appeared; retry after it finishes.')
        command = [str(BLENDER), '-b', '--factory-startup', '--python-exit-code', '1']
        if mode == 'build':
            command += ['--python', str(SCRIPT / 'build_farmer_train.py')]
        else:
            blend = OUT / 'farmer_owns_train_v2_overhaul_source.blend' if mode == 'movie' else ROOT / 'farmer_owns_train.blend'
            extra = [] if a is None else [str(a), str(b), str(res_w), str(res_h)]
            command += [str(blend), '--python', str(SCRIPT / 'render.py'), '--', mode] + extra
        env = os.environ.copy()
        env['TEMP'] = env['TMP'] = str(OUT / 'tmp')
        env['BLENDER_USER_RESOURCES'] = str(OUT / '.blender_user')
        (OUT / 'tmp').mkdir(exist_ok=True)
        logpath = OUT / ('v2_overhaul_' + mode + ('' if a is None else f'_{a:04}_{b:04}') + '.log')
        with logpath.open('w', encoding='utf-8') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
            print(mode, 'BLENDER_PID', process.pid, flush=True)
            while process.poll() is None:
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    if mode == 'movie' and (OUT / 'v2_overhaul_progress.json').exists():
                        print((OUT / 'v2_overhaul_progress.json').read_text(), flush=True)
            if process.returncode:
                raise RuntimeError(logpath.read_text(errors='replace')[-5500:])
    except KeyboardInterrupt:
        if process and process.poll() is None:
            process.terminate()
            process.wait()
        raise
    finally:
        if LOCK.exists():
            try:
                if json.loads(LOCK.read_text()).get('owner') == owner:
                    LOCK.unlink()
            except Exception:
                pass


def prepare():
    if not AUDIO.is_file():
        raise FileNotFoundError(f'Provide narration audio at {AUDIO}')
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run([SYS_PY, str(SCRIPT / 'assets.py')], check=True)
    if not (OUT / 'narration.wav').is_file() or not (OUT / 'audio_env.json').is_file():
        raw = subprocess.run(
            ['ffmpeg', '-v', 'error', '-i', str(AUDIO), '-f', 'f32le', '-ac', '1', '-ar', '24000', 'pipe:1'],
            stdout=subprocess.PIPE, check=True,
        ).stdout
        audio = np.frombuffer(raw, dtype=np.float32)
        env = []
        for f in range(1668):
            span = audio[f * 800:(f + 1) * 800]
            env.append(float(np.sqrt(np.mean(span * span))) if len(span) else 0.0)
        env = np.asarray(env)
        env = np.clip((env - 0.012) / max(0.01, np.percentile(env, 94) - 0.012), 0.0, 1.0)
        for i in range(1, len(env)):
            env[i] = 0.64 * env[i] + 0.36 * env[i - 1]
        (OUT / 'audio_env.json').write_text(json.dumps([round(float(v), 4) for v in env]))
        subprocess.run(
            ['ffmpeg', '-y', '-v', 'error', '-i', str(AUDIO), '-af', 'apad', '-t', '55.60', '-ar', '48000', '-ac', '2', str(OUT / 'narration.wav')],
            check=True,
        )
    (OUT / 'shots.json').write_text(
        json.dumps({'shots': [{'id': n, 'a': a - 1, 'b': b - 1} for n, a, b in SHOT_DEFS]}, indent=2)
    )


def sheet():
    # 16-tile (4x4) Calibration Contact Sheet -> sheet_v2.jpg
    result = Image.new('RGB', (4 * 552 + 12, 4 * 1004 + 12), '#121b27')
    d = ImageDraw.Draw(result)
    font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 20)
    for i, (f, label) in enumerate(zip(FRAMES_16, LABELS_16)):
        x = 12 + (i % 4) * 552
        y = 12 + (i // 4) * 1004
        d.text((x, y + 4), f'{label} | f{f}', font=font, fill='white')
        im = Image.open(OUT / 'calibration_v2_16' / f'{f:04}.png').convert('RGB')
        assert im.size == (540, 960)
        result.paste(im, (x, y + 35))
    out_sheet = OUT / 'sheet_v2.jpg'
    result.save(out_sheet, quality=94)
    shutil.copy2(out_sheet, OUT / 'sheet_v5.jpg')
    print('SHEET_SAVED', out_sheet, flush=True)


def movie(res_w=360, res_h=640):
    source = ROOT / 'farmer_owns_train.blend'
    frozen = OUT / 'farmer_owns_train_v2_overhaul_source.blend'
    shutil.copy2(source, frozen)
    folder = OUT / f'v2_overhaul_{res_w}p_frames'
    folder.mkdir(exist_ok=True)
    for attempt in range(4):
        missing = []
        for f in range(1, 1669):
            p = folder / f'frame_{f:04}.png'
            try:
                with Image.open(p) as im:
                    assert im.size == (res_w, res_h)
                    im.verify()
            except (OSError, AssertionError):
                missing.append(f)
        if not missing:
            break
        launch('movie', min(missing), 1668, res_w, res_h)

    target_master = OUT / 'farmer_owns_train_v2_master.mp4'
    target_360p = OUT / 'farmer_owns_train_v2_360p.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-v', 'error', '-framerate', '30', '-start_number', '1',
        '-i', str(folder / 'frame_%04d.png'), '-i', str(OUT / 'narration.wav'),
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-t', '55.60', '-movflags', '+faststart', str(target_master),
    ], check=True)
    shutil.copy2(target_master, target_360p)
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(target_master)]))
    video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    assert (video['width'], video['height'], int(video['nb_frames'])) == (res_w, res_h, 1668)
    (OUT / 'v2_delivery_probe.json').write_text(json.dumps(probe, indent=2))
    print('DELIVERED', target_master, target_360p, flush=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'build':
        prepare()
        launch('build')
    elif mode == 'verify':
        launch('verify')
    elif mode == 'sheet':
        launch('sheet')
        sheet()
    elif mode == 'movie':
        movie()
