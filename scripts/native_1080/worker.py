"""Render an approved packed procedural source at native delivery resolution."""
import json
import os
from pathlib import Path
import sys
import time
import traceback

import bpy

arguments = sys.argv[sys.argv.index('--') + 1:]
config = json.loads(Path(arguments[0]).read_text())
mode = arguments[1]
scene = bpy.context.scene
out = Path(config['directory'])
namespace = {'__name__': config['runtime'].removesuffix('.py')}
exec(bpy.data.texts[config['runtime']].as_string(), namespace)
original = namespace['update']


def checked(current, *_):
    try:
        if config['id'] == 'farmer_owns_train':
            frame = current.frame_current
            for name, enabled in [('Station sun', not 333 <= frame < 981),
                                  ('StreetFarm sun', 333 <= frame < 792),
                                  ('Courtroom sun', 792 <= frame < 981)]:
                light = current.objects.get(name)
                if light:
                    light.data.use_shadow = enabled
        original(current)
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(3)


for callback in list(bpy.app.handlers.frame_change_pre):
    if getattr(callback, '__name__', '') == 'update':
        bpy.app.handlers.frame_change_pre.remove(callback)
bpy.app.handlers.frame_change_pre.append(checked)

# Preserve the Farmer delivery worker's light and contour behavior.
if config['id'] == 'farmer_owns_train':
    for obj in scene.objects:
        if obj.type == 'LIGHT' and obj.data.type != 'SUN':
            obj.data.use_shadow = False
    ink = namespace.get('INK')
    if ink and getattr(ink, 'sources', None):
        material = bpy.data.materials.get('Warm marker / depth faded set contours')
        if material:
            material.surface_render_method = 'DITHERED'
        ink_update = ink.update
        sources = list(ink.sources)
        starts = {shot[1] for shot in namespace['SHOTS']}
        last_frame = None

        def optimized_ink():
            global last_frame
            frame = scene.frame_current
            if last_frame is not None and frame not in starts and frame % 3 != 1:
                return
            last_frame = frame
            position = scene.camera.matrix_world.translation
            ink.sources = [entry for entry in sources if not entry[0].hide_render
                           and (entry[0].matrix_world.translation - position).length < 20
                           and abs(entry[0].matrix_world.to_3x3().determinant()) > 1e-6]
            ink_update()

        ink.update = optimized_ink

scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.eevee.use_raytracing = False
scene.eevee.taa_render_samples = 16
scene.render.use_simplify = True
scene.render.simplify_subdivision = 2
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.render.fps_base = 1
scene.frame_step = 1
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.compression = 15
scene.render.use_file_extension = True
scene.render.use_sequencer = False
scene.render.use_lock_interface = True
frames = out / 'frames'
frames.mkdir(exist_ok=True)
started = last = time.monotonic()
timings = []


def written(current, *_):
    global last
    now = time.monotonic()
    timings.append(now - last)
    last = now
    data = {'frame': current.frame_current, 'total': config['frames'],
            'seconds_per_frame': round(sum(timings[-20:]) / len(timings[-20:]), 3),
            'chunk_seconds': round(now - started, 1), 'mode': mode}
    target = out / 'progress.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(data))
    temporary.replace(target)
    if len(timings) == 1:
        import gpu
        print('ACTIVE_GPU', gpu.platform.vendor_get(), gpu.platform.renderer_get(), flush=True)
        print('SETTINGS', scene.render.engine, 1080, 1920, 100, 16, flush=True)
    print('FRAME', current.frame_current, flush=True)


bpy.app.handlers.render_write.append(written)
if mode == 'benchmark':
    measurements = []
    for frame in config['samples']:
        scene.frame_set(frame)
        scene.render.filepath = str(frames / f'frame_{frame:04d}.png')
        before = time.monotonic()
        bpy.ops.render.render(write_still=True)
        measurements.append({'frame': frame, 'seconds': round(time.monotonic() - before, 3)})
    (out / 'benchmark.json').write_text(json.dumps(measurements, indent=2))
else:
    scene.frame_start = int(arguments[2])
    scene.frame_end = int(arguments[3])
    scene.render.filepath = str(frames / 'frame_')
    bpy.ops.render.render(animation=True)
