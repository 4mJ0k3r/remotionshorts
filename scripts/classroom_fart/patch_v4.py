"""Focused camera staging patch; reuse the verified V3 rig and contacts."""
import bpy,ast,json,sys
from pathlib import Path
from mathutils import Vector as V
HERE=Path(__file__).resolve().parent;OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
sys.path.insert(0,str(HERE));from primitives import key,linear
CAM=bpy.data.objects['Delivery camera'];FOCUS=bpy.data.objects['Active face or physical contact focus']
tree=ast.parse((HERE/'build_classroom_fart.py').read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='camera_pose')
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HERE/'build_classroom_fart.py'),'exec'),globals())
rows=json.loads((OUT/'shots.json').read_text())['shots']
for row in rows:
    if row['shot'] not in ['3B','3C','4B']:continue
    for f in range(row['start_frame'],row['end_frame']+1):camera_pose(f,row)
for ob in [CAM,CAM.data,FOCUS]:linear(ob)
teachers={o for o in bpy.data.objects if o.name.startswith(('teacher','char_teacher')) and not o.name.endswith('neck connection')}
def descendants(o):
    for child in o.children:yield child;yield from descendants(child)
teachers.update(descendants(bpy.data.objects['char_teacher independent camera-facing head']))
for o in teachers:
    for f,on in [(1,False),(803,False),(804,True),(904,True),(905,False),(1483,False),(1484,True),(1635,True)]:
        o.hide_render=on;key(o,'hide_render',f)
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            if fc.data_path=='hide_render':
                for k in fc.keyframe_points:k.interpolation='CONSTANT'
for s in bpy.data.scenes:s.view_settings.exposure=.25
bpy.context.window.scene=bpy.data.scenes['CF_1A'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'classroom_fart_v4.blend'))
print('V4 camera staging and exposure saved; verified rig unchanged.',flush=True)
