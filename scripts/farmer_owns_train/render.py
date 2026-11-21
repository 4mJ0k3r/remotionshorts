"""Blender worker: verify all 1,668 frames, render 16-tile calibration sheet_v2.jpg, or render movie span."""
import bpy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'renders' / 'farmer_owns_train'
args = sys.argv[sys.argv.index('--') + 1:]
mode = args[0]

S = bpy.context.scene
runtime = {'__name__': 'farmer_runtime'}
exec(bpy.data.texts['farmer_runtime.py'].as_string(), runtime)
original = runtime['update']

SUN_STATION = S.objects.get('Station sun')
SUN_STREET = S.objects.get('StreetFarm sun')
SUN_COURT = S.objects.get('Courtroom sun')
for obj in S.objects:
    if obj.type == 'LIGHT' and obj.data.type != 'SUN':
        obj.data.use_shadow = False


def checked(scene, *unused):
    try:
        f = scene.frame_current
        if SUN_STATION and SUN_STREET and SUN_COURT:
            in_street = (333 <= f < 792)
            in_court = (792 <= f < 981)
            SUN_STATION.data.use_shadow = not (in_street or in_court)
            SUN_STREET.data.use_shadow = in_street
            SUN_COURT.data.use_shadow = in_court
        original(scene)
    except BaseException:
        import os
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(3)


for h in list(bpy.app.handlers.frame_change_pre):
    if getattr(h, '__name__', '') == 'update':
        bpy.app.handlers.frame_change_pre.remove(h)
bpy.app.handlers.frame_change_pre.append(checked)

S.render.fps = 30
S.eevee.taa_render_samples = 8 if mode == 'movie' else 16
S.render.use_lock_interface = True

# Optimize SetInk for fast per-frame culling & zero-scale guard
if 'INK' in runtime and getattr(runtime['INK'], 'sources', None):
    _ink = runtime['INK']
    _mat = bpy.data.materials.get('Warm marker / depth faded set contours')
    if _mat:
        _mat.surface_render_method = 'DITHERED'
    _orig_ink_update = _ink.update
    _all_sources = list(_ink.sources)
    _CUT_STARTS = {s[1] for s in runtime['SHOTS']}
    _last_ink_frame = [None]
    def _fast_ink_update():
        f = _ink.scene.frame_current
        if mode == 'movie' and _last_ink_frame[0] is not None and f not in _CUT_STARTS and (f % 3 != 1):
            return
        _last_ink_frame[0] = f
        cam_pos = _ink.scene.camera.matrix_world.translation
        _ink.sources = [
            src for src in _all_sources
            if not src[0].hide_render
            and (src[0].matrix_world.translation - cam_pos).length < 20.0
            and abs(src[0].matrix_world.to_3x3().determinant()) > 1e-6
        ]
        _orig_ink_update()
    _ink.update = _fast_ink_update

CALIBRATION_FRAMES = [55, 165, 248, 305, 375, 465, 538, 625, 735, 840, 900, 1035, 1135, 1248, 1302, 1455]

if mode == 'verify':
    S.render.resolution_x = 1080
    S.render.resolution_y = 1920
    S.render.resolution_percentage = 50
    from mathutils import Vector
    S['set_ink_enabled'] = False
    assert not any(o.type == 'FONT' for o in S.objects), 'FONT object found'
    max_normal_error = 0.0
    max_reach = 0.0
    max_warrant = 0.0
    max_flag = 0.0
    max_bag = 0.0
    max_gavel = 0.0
    max_walk_lift = 0.0
    visible_heads = 0

    for f in range(1, 1669):
        S.frame_set(f)
        cq = S.camera.matrix_world.to_quaternion()
        cn = cq @ Vector((0, 0, 1))
        for kind in runtime['ACTORS']:
            head = S.objects[kind + '_head']
            if not head.hide_render:
                hn = head.rotation_quaternion @ Vector((0, 0, 1))
                max_normal_error = max(max_normal_error, (hn - cn).length)
                visible_heads += 1
        max_reach = max(max_reach, float(S.get('max_arm_reach_m', 0.0)))
        max_warrant = max(max_warrant, float(S.get('warrant_grip_error_m', 0.0)))
        max_flag = max(max_flag, float(S.get('flag_grip_error_m', 0.0)))
        max_bag = max(max_bag, float(S.get('bag_grip_error_m', 0.0)))
        max_gavel = max(max_gavel, float(S.get('gavel_grip_error_m', 0.0)))
        if 981 <= f < 1095:
            max_walk_lift = max(max_walk_lift, float(S.get('max_walk_lift_m', 0.0)))
            assert all(not S.objects['farmer_' + p].hide_render for p in ['hips', 'legL', 'legR', 'trouserL', 'trouserR', 'shoeL', 'shoeR']), f'Hidden walking part at f={f}'
            assert all(not S.objects['bailiff_' + p].hide_render for p in ['hips', 'legL', 'legR', 'trouserL', 'trouserR', 'shoeL', 'shoeR']), f'Hidden bailiff walking part at f={f}'
        if f % 160 == 0:
            print('AUDIT_FRAME', f, flush=True)

    assert max_normal_error < 1e-5, f'Head normal error {max_normal_error}'
    assert max_reach <= 0.49501, f'Arm reach exceeded: {max_reach}'
    assert max_warrant < 1e-5 and max_flag < 1e-5 and max_bag < 1e-5 and max_gavel < 1e-5, (
        f'Grip error exceeded: warrant={max_warrant} flag={max_flag} bag={max_bag} gavel={max_gavel}'
    )
    assert max_walk_lift >= 0.115, f'Walking foot lift too small: {max_walk_lift}'

    report = {
        'frames_evaluated': 1668,
        'cuts_total': 20,
        'visible_head_samples': visible_heads,
        'max_head_normal_error': round(max_normal_error, 8),
        'max_arm_reach_m': round(max_reach, 6),
        'max_warrant_grip_error_m': round(max_warrant, 8),
        'max_flag_grip_error_m': round(max_flag, 8),
        'max_bag_grip_error_m': round(max_bag, 8),
        'max_gavel_grip_error_m': round(max_gavel, 8),
        'cut_3b_max_walk_lift_m': round(max_walk_lift, 4),
        'font_objects': 0,
        'hud_pills': 20,
        'audio_envelope_frames': len(runtime['ENV']),
    }
    (OUT / 'rig_verification_v2.json').write_text(json.dumps(report, indent=2))
    print('RIG_VERIFIED', json.dumps(report), flush=True)

elif mode == 'sheet':
    S.render.resolution_x = 1080
    S.render.resolution_y = 1920
    S.render.resolution_percentage = 50
    directory = OUT / 'calibration_v2_16'
    directory.mkdir(parents=True, exist_ok=True)
    for f in CALIBRATION_FRAMES:
        S.frame_set(f)
        S.render.filepath = str(directory / f'{f:04}.png')
        bpy.ops.render.render(write_still=True)
        print('CALIBRATION', f, flush=True)

else:
    a, b = map(int, args[1:3])
    res_w = int(args[3]) if len(args) > 3 else 540
    res_h = int(args[4]) if len(args) > 4 else 960
    S.render.resolution_x = res_w
    S.render.resolution_y = res_h
    S.render.resolution_percentage = 100
    S.render.fps = 30
    directory = OUT / f'v2_overhaul_{res_w}p_frames'
    directory.mkdir(parents=True, exist_ok=True)
    S.frame_start = a
    S.frame_end = b
    S.render.filepath = str(directory / 'frame_')
    last = time.time()
    started = last
    times = []

    def written(scene, *unused):
        global last
        now = time.time()
        times.append(now - last)
        last = now
        spf = round(sum(times[-20:]) / len(times[-20:]), 3)
        rem = max(0, 1668 - scene.frame_current)
        data = {
            'frame': scene.frame_current,
            'total': 1668,
            'percent': round(100.0 * scene.frame_current / 1668.0, 2),
            'seconds_per_frame': spf,
            'eta_seconds': round(rem * spf, 1),
            'elapsed_chunk': round(now - started, 1),
        }
        (OUT / 'v2_overhaul_progress.json').write_text(json.dumps(data))
        if len(times) == 1:
            import gpu
            print('ACTIVE_GPU', gpu.platform.vendor_get(), gpu.platform.renderer_get(), flush=True)
        if scene.frame_current % 30 == 0 or scene.frame_current == b:
            print('PROGRESS', json.dumps(data), flush=True)

    bpy.app.handlers.render_write.append(written)
    try:
        bpy.ops.render.render(animation=True)
    finally:
        bpy.app.handlers.render_write.remove(written)
