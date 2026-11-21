"""Native HD export of the approved packed scene; separate resumable frames."""
import bpy
import hashlib
import json
import struct
import sys
import time
from pathlib import Path

PROJECT=Path(__file__).resolve().parent.name
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders'/PROJECT
CONFIG={
 'commode_sniper':('commode_sniper_v2_master.blend','commode_runtime.py',1635,'commode_sniper_v2_1080p'),
 'puri_flag_physics':('puri_flag_physics_sky_v2.blend','puri_procedural_runtime.py',2211,'puri_flag_physics_sky_v2_1080p')
}
source_name,runtime,total,tag=CONFIG[PROJECT]
source=OUT/source_name
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
folder=OUT/(tag+'_frames')
folder.mkdir(exist_ok=True)
manifest_path=OUT/(tag+'_source.json')
identity={'source':str(source),'sha256':source_hash,'width':1080,'height':1920,'fps':30,'samples':16,'frames':total}
if manifest_path.exists():
    assert json.loads(manifest_path.read_text())==identity,'Approved source changed; preserve previous HD frames first'
else:
    manifest_path.write_text(json.dumps(identity,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
namespace={'__name__':PROJECT+'_hd_runtime'}
exec(bpy.data.texts[runtime].as_string(),namespace)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1080
scene.render.resolution_y=1920
scene.render.resolution_percentage=100
scene.render.fps=30
scene.render.fps_base=1
scene.render.use_simplify=True
scene.render.simplify_subdivision=2
scene.eevee.use_raytracing=False
scene.eevee.taa_render_samples=16
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.image_settings.compression=6
scene.frame_start=1
scene.frame_end=total
scene.frame_set(1)
scene['hd_approved_source_sha256']=source_hash
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(tag+'_render_source.blend')))
try:
    import gpu
    print('ACTIVE_GPU',gpu.platform.vendor_get(),gpu.platform.renderer_get(),flush=True)
except Exception as error:
    print('GPU metadata unavailable:',error,flush=True)
progress_path=OUT/(tag+'_progress.json')
started=time.time()
rendered=0
def valid(path):
    try:
        with path.open('rb') as file:
            header=file.read(24)
            file.seek(-12,2)
            tail=file.read()
        return header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(1080,1920) and tail[4:8]==b'IEND'
    except (OSError,ValueError,struct.error):
        return False
for frame in range(1,total+1):
    final=folder/f'f{frame:04}.png'
    if valid(final):
        continue
    partial=folder/f'f{frame:04}.part.png'
    scene.frame_set(frame)
    scene.render.filepath=str(partial)
    bpy.ops.render.render(write_still=True)
    assert valid(partial),'Invalid native HD frame '+str(frame)
    partial.replace(final)
    rendered+=1
    progress={'state':'rendering','project':PROJECT,'frame':frame,'total':total,'rendered_this_run':rendered,'elapsed':round(time.time()-started,2),'seconds_per_frame':round((time.time()-started)/rendered,3)}
    temp=progress_path.with_suffix('.tmp')
    temp.write_text(json.dumps(progress))
    temp.replace(progress_path)
    if frame==1 or frame%30==0:
        print('PROBE HD '+json.dumps(progress),flush=True)
progress_path.write_text(json.dumps({'state':'frames_complete','frame':total,'total':total,'elapsed':round(time.time()-started,2)}))
print('HD_FRAMES_COMPLETE',PROJECT,total,flush=True)

