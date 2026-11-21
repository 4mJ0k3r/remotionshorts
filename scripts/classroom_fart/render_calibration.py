"""Single batch covering every cut, its sub-cuts and the key support extremes."""
import bpy,json,time,hashlib,gpu
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');REV=Path(bpy.data.filepath).stem.rsplit('_',1)[-1]
CAL=OUT/f'calibration_{REV}';CAL.mkdir(exist_ok=True)
ROWS=json.loads((OUT/'shots.json').read_text())['shots']
# Implied background teaching is independent of the narrator's voice envelope.
for ob in bpy.data.objects:
    if not ob.name.startswith('teacher face ') or not ob.animation_data:continue
    expression=ob.name.removeprefix('teacher face ')
    for fc in ob.animation_data.action.fcurves:
        for k in fc.keyframe_points:
            f=round(k.co.x)
            if 1215<=f<1299:k.co.y=float(expression==['talk_a','talk_b','look_left'][((f-1215)//3)%3])
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
FRAMES=[60,160,232,300,385,455,520,620,702,751,786,855,940,1007,1060,1145,1245,1360,1446,1490,1580,266,335,1034,1035,1082,1410,1422,1466,1483,1565]
records=[]
for f in FRAMES:
    row=next(r for r in ROWS if r['start_frame']<=f<=r['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f)
    s.render.resolution_percentage=50;s.eevee.taa_render_samples=16;s.render.filepath=str(CAL/f'{f:04}.png')
    t=time.monotonic();bpy.ops.render.render(write_still=True)
    records.append({'frame':f,'shot':row['shot'],'seconds':round(time.monotonic()-t,3)})
    print('CALIBRATION',f,records[-1]['seconds'],flush=True)
(OUT/f'calibration_{REV}_times.json').write_text(json.dumps(records,indent=2))
(OUT/'gpu_device.json').write_text(json.dumps({'vendor':gpu.platform.vendor_get(),'renderer':gpu.platform.renderer_get(),'version':gpu.platform.version_get()},indent=2))
print('Calibration complete. Inspect before any video render.',flush=True)
# Three lighting probes keep face readability decisions tied to actual EEVEE pixels.
PROBE=OUT/f'{REV}_exposure_probe';PROBE.mkdir(exist_ok=True)
for f in [160,520,1410]:
    row=next(r for r in ROWS if r['start_frame']<=f<=r['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f)
    old=s.view_settings.exposure;s.view_settings.exposure=.25;s.render.filepath=str(PROBE/f'{f:04}.png')
    bpy.ops.render.render(write_still=True);s.view_settings.exposure=old
import runpy
runpy.run_path(r'D:\remotionshorts\scripts\classroom_fart\audit_contacts.py',run_name='__main__')
