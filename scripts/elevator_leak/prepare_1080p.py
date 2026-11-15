"""Save the approved scene as a native 1080p preset without rendering."""
import bpy
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/elevator_leak'
source=ROOT/'elevator_leak.blend'
target=OUT/'elevator_leak_v3_1080p_render_source.blend'
profile=OUT/'v3_1080p_ready.json'
audio_source=OUT/'narration.wav'
audio_target=OUT/'narration_v3_1080p.wav'


def digest(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file,'sha256').hexdigest()


def prepare():
    if profile.exists():
        existing=json.loads(profile.read_text())
        if target.exists() and existing['source_sha256']==digest(target) and existing['origin_sha256']==digest(source) and audio_target.exists() and existing['audio_sha256']==digest(audio_target):
            print('1080p preset is already prepared. No frames rendered.')
            return
    if (OUT/'v3_1080p_render_manifest.json').exists():
        raise RuntimeError('An existing 1080p run owns this preset. Resume it without replacing its source.')
    scene=bpy.context.scene
    assert scene.get('elevator_leak') and scene.frame_end==2145
    assert all(name in bpy.data.texts for name in ['elevator_runtime.py','leg_stepper.py','studio_set_ink.py'])
    scene.render.resolution_x=1080
    scene.render.resolution_y=1920
    scene.render.resolution_percentage=100
    scene.render.fps=30
    scene.frame_start=1
    scene.frame_end=2145
    scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.eevee.use_raytracing=False
    scene.eevee.taa_render_samples=16
    scene.render.use_simplify=True
    scene.render.simplify_subdivision=2
    scene.render.use_lock_interface=True
    scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGB'
    scene.render.image_settings.compression=15
    scene.render.filepath=str(OUT/'v3_1080p_frames'/'frame_')
    scene['render_profile']='V3 native 1080x1920, 30 fps, 16 EEVEE samples'
    shutil.copy2(audio_source,audio_target)
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    data={'state':'ready_not_started','origin':str(source),'origin_sha256':digest(source),'source':str(target),'source_sha256':digest(target),'audio':str(audio_target),'audio_sha256':digest(audio_target),'width':1080,'height':1920,'fps':30,'frames':2145,'duration_seconds':71.5,'samples':16,'engine':'BLENDER_EEVEE_NEXT','raytracing':False,'rendered_1080p_frames':0,'movie':str(OUT/'elevator_leak_v3_1080p_master.mp4')}
    profile.write_text(json.dumps(data,indent=2))
    print(json.dumps(data,indent=2))


prepare()
