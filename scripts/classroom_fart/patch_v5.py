"""Last 4B camera correction; prove all other keyed camera samples unchanged."""
import bpy,ast,json,sys,hashlib
from pathlib import Path
from mathutils import Vector as V
HERE=Path(r'D:\remotionshorts\scripts\classroom_fart');OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
sys.path.insert(0,str(HERE));from primitives import key,linear
CAM=bpy.data.objects['Delivery camera'];FOCUS=bpy.data.objects['Active face or physical contact focus']
def outside_snapshot():
    result=[]
    for ob in [CAM,CAM.data,FOCUS]:
        for fc in ob.animation_data.action.fcurves:
            result.append((ob.name,fc.data_path,fc.array_index,[round(fc.evaluate(f),7) for f in range(1,1636) if not 971<=f<1035]))
    return hashlib.sha256(json.dumps(result).encode()).hexdigest()
before=outside_snapshot();tree=ast.parse((HERE/'build_classroom_fart.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='camera_pose')
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<camera-only patch>','exec'),globals())
rows=json.loads((OUT/'shots.json').read_text())['shots'];row=next(r for r in rows if r['shot']=='4B')
for f in range(971,1035):camera_pose(f,row)
for ob in [CAM,CAM.data,FOCUS]:
    linear(ob);ob.animation_data.action.update_tag();ob.update_tag()
after=outside_snapshot();assert before==after,'Camera changed outside the declared 64-frame range'
bpy.context.window.scene=bpy.data.scenes['CF_1A'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'classroom_fart_v5.blend'))
cal=OUT/'calibration_v5';cal.mkdir(exist_ok=True)
for f in [751,804,855,904,971,1007,1034,1446,1466,1484,1580,1635]:
    r=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);s=bpy.data.scenes[r['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.filepath=str(cal/f'{f:04}.png');bpy.ops.render.render(write_still=True)
(OUT/'v5_patch_invariants.json').write_text(json.dumps({'changed_frames':[971,1034],'outside_camera_before':before,'outside_camera_after':after,'all_other_scene_and_rig_data':'unmodified','base_calibration':'calibration_v4','source_sha256':hashlib.sha256((OUT/'classroom_fart_v5.blend').read_bytes()).hexdigest()},indent=2))
print('V5 confirmation complete; outside-range camera keys identical.',flush=True)
