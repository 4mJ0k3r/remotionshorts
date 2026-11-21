import bpy,json,time,runpy,gpu,hashlib
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');CAL=OUT/'v2_surgical_calibration_final';CAL.mkdir(exist_ok=True)
runpy.run_path(r'D:\remotionshorts\scripts\classroom_fart\audit_surgical_v2.py',run_name='__main__')
rows=json.loads((OUT/'shots_v2.json').read_text())['shots']
main=[60,160,232,300,385,455,520,620,702,751,786,855,940,1007,1060,1145,1245,1360,1410,1446,1466,1484,1580,1635]
extra=[266,335,735,768,804,828,904,1034,1083,1214,1299,1409,1430,1455,1483]
records=[]
for f in main+extra:
    row=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.filepath=str(CAL/f'{f:04}.png');t=time.monotonic();bpy.ops.render.render(write_still=True);records.append({'frame':f,'seconds':time.monotonic()-t});print('V2 STILL',f,flush=True)
(OUT/'v2_calibration_manifest.json').write_text(json.dumps({'source':bpy.data.filepath,'source_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'main_frames':main,'extra_frames':extra,'times':records,'gpu':gpu.platform.renderer_get()},indent=2))
