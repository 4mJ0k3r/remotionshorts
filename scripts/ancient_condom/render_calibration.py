"""Exactly twenty stills, then a paired shadow diagnostic; never renders animation."""
import bpy,json,time,sys
from pathlib import Path
from mathutils import Vector as V
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');data=json.loads((OUT/'shots.json').read_text());times=[];version='v3' if '--v3' in sys.argv else 'v2' if '--v2' in sys.argv else 'v1';cal=OUT/('calibration_'+version if version!='v1' else 'calibration');cal.mkdir(exist_ok=True)
for f in data['samples']:
    row=next(x for x in data['shots'] if x['start_frame']<=f<=x['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.resolution_percentage=50
    # The preceding scene is no longer needed once the 8-frame dissolve is complete.
    if row['id']==14:
        for n in s.node_tree.nodes:
            if n.type=='R_LAYERS' and n.scene and n.scene.name=='AC_13':n.mute=True
    s.render.filepath=str(cal/f'f{f:04}.png');t=time.monotonic();bpy.ops.render.render(write_still=True,scene=s.name);assert Path(s.render.filepath).is_file();times.append({'frame':f,'seconds':time.monotonic()-t});(OUT/f'calibration_times_{version}.json').write_text(json.dumps(times,indent=2));print('CALIBRATED',f,times[-1]['seconds'],flush=True)
# Paired diagnostic: identical receiving earth pixels with real shadow visibility toggled.
s=bpy.data.scenes['AC_03'];bpy.context.window.scene=s;s.frame_set(210);s.render.resolution_percentage=50;s.render.use_motion_blur=False;s.camera.data.dof.use_dof=False
cam=bpy.data.objects.new('QA overhead ground receiver',bpy.data.cameras.new('QA overhead optics'));s.collection.objects.link(cam);cam.location=(.2,-1.35,5);target=V((.2,-1.35,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.;s.camera=cam
for enabled in [True,False]:
    for o in s.objects:
        if o.type=='LIGHT':o.data.use_shadow=enabled
    s.render.filepath=str(OUT/'qa'/('shadow_on.png' if enabled else 'shadow_off.png'));bpy.ops.render.render(write_still=True,scene=s.name)
print('CALIBRATION COMPLETE',flush=True)
