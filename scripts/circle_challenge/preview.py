"""Build the approved preview from the calibrated scene and refreshed pose art."""
import bpy, json, time
from pathlib import Path

ROOT = Path('D:/remotionshorts/scripts/circle_challenge')
OUT = ROOT.parent.parent/'renders/circle_challenge'
scene = bpy.context.scene
delivery = globals().get('delivery', False)
revision = 'v2' if scene.get('motion_revision') == 4 else 'v1'
if delivery and revision != 'v2':
    raise RuntimeError('The approved motion revision is required for this render.')
if revision == 'v1':
    art = {}
    exec((ROOT/'reference_art.py').read_text(), art)
    art['refresh_art'](bpy, OUT/'assets')

for shot_scene in (scene, bpy.data.scenes['Circle Challenge HUD pass']):
    shot_scene.render.engine = 'BLENDER_EEVEE_NEXT'
    shot_scene.eevee.use_raytracing = False
    shot_scene.eevee.taa_render_samples = 16
    shot_scene.render.resolution_x = 1080 if delivery else 540
    shot_scene.render.resolution_y = 1920 if delivery else 960
    shot_scene.render.resolution_percentage = 100
    shot_scene.render.fps = 30
    shot_scene.frame_start = 1
    shot_scene.frame_end = 2205
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH' if delivery else 'MEDIUM'
scene.render.ffmpeg.audio_codec = 'NONE'
raw_name = 'circle_challenge_raw.mp4' if revision == 'v1' else 'circle_challenge_preview_v2_raw.mp4'
if delivery:
    raw_name = 'circle_challenge_1080p_raw.mp4'
scene.render.filepath = str(OUT/raw_name)
scene.render.use_file_extension = False
scene.render.use_sequencer = False
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'circle_challenge.blend'))

started = time.monotonic()
progress = OUT/('render_1080p_progress.json' if delivery else
                'preview_progress.json' if revision == 'v1' else 'preview_v2_progress.json')

def update(status, frame):
    data = dict(status=status, frame=frame, total=2205, seconds=round(time.monotonic()-started,1))
    temporary = progress.with_suffix('.tmp')
    temporary.write_text(json.dumps(data))
    temporary.replace(progress)

def after_frame(rendered_scene, *_):
    if rendered_scene == scene and (scene.frame_current == 1 or scene.frame_current % 15 == 0):
        update('rendering', scene.frame_current)

update('rendering',0)
bpy.app.handlers.render_post.append(after_frame)
try:
    result = bpy.ops.render.render(animation=True, scene=scene.name)
    if 'FINISHED' not in result:
        raise RuntimeError(str(result))
    update('complete',2205)
except Exception:
    update('failed',scene.frame_current)
    raise
finally:
    bpy.app.handlers.render_post.remove(after_frame)
