"""Render the authorized calibration batch only, under run_blender.py's mutex."""
import bpy,json,time,sys
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
manifest=json.loads((OUT/'segments_timeline.json').read_text())
results=[]
for row in manifest['shots']:
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(row['representative_frame'])
    s.render.resolution_percentage=50;s.eevee.taa_render_samples=16
    version='_v2' if '--v2' in sys.argv else ''
    s.render.filepath=str(OUT/('frame_'+row['shot']+version+'.png'));t=time.time()
    bpy.ops.render.render(write_still=True,scene=s.name)
    results.append({'shot':row['shot'],'frame':s.frame_current,'seconds':round(time.time()-t,2),'camera':s.camera.name,'fstop':s.camera.data.dof.aperture_fstop,'raytracing':s.eevee.use_raytracing})
    (OUT/('calibration_timings'+version+'.json')).write_text(json.dumps(results,indent=2));print('CALIBRATION',results[-1],flush=True)
if '--v2' in sys.argv:
    for shot,f,tag in [('1B',226,'stretch'),('1C',276,'electrodes'),('3A',888,'palm'),('4C',1315,'carry')]:
        s=bpy.data.scenes[shot];bpy.context.window.scene=s;s.frame_set(f);s.render.filepath=str(OUT/f'contact_{tag}_f{f}.png');bpy.ops.render.render(write_still=True,scene=s.name)
print('Calibration still batch completed. Full animation has not been rendered.',flush=True)
