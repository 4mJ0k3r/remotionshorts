"""Keep the upright head above its neck while reclining; clear jump coverage."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector as V
OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
head=bpy.data.objects['char_you independent camera-facing head'];aim=bpy.data.objects['you camera parallel head aim'];hip=bpy.data.objects['char_you glossy royal-blue pelvis']
def at(o,f):
    vals=list(o.location)
    for fc in o.animation_data.action.fcurves:
        if fc.data_path=='location':vals[fc.array_index]=fc.evaluate(f)
    return V(vals)
changes=[]
for f in range(971,1299):
    old=at(head,f);h=at(hip,f);axis=(old-h)/.84;new=h+axis*.40+V((0,0,.44));delta=new-old;oldaim=at(aim,f)
    head.location=new;head.keyframe_insert('location',frame=f);aim.location=oldaim+delta;aim.keyframe_insert('location',frame=f)
    if f in [971,1021,1034,1083,1145,1298]:changes.append({'frame':f,'old':list(old),'new':list(new)})
for o in [head,aim]:o.animation_data.action.update_tag();o.update_tag()
for o in bpy.data.objects:
    if not o.name.startswith(('friend','char_friend')) or o.name.endswith('neck connection'):continue
    for f,hidden in [(1409,False),(1410,True),(1483,True),(1484,False)]:o.hide_render=hidden;o.keyframe_insert('hide_render',frame=f)
    for fc in o.animation_data.action.fcurves:
        if fc.data_path=='hide_render':
            for k in fc.keyframe_points:k.interpolation='CONSTANT'
bpy.context.window.scene=bpy.data.scenes['CF_1A'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'classroom_fart_v6.blend'))
cal=OUT/'calibration_v6';cal.mkdir(exist_ok=True);rows=json.loads((OUT/'shots.json').read_text())['shots']
for f in [768,970,971,1007,1034,1060,1145,1245,1410,1446,1466,1483,1580,1635]:
    r=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);s=bpy.data.scenes[r['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.filepath=str(cal/f'{f:04}.png');bpy.ops.render.render(write_still=True)
(OUT/'v6_patch_manifest.json').write_text(json.dumps({'head_frames':[971,1298],'friend_visibility_frames':[1410,1483],'head_checks':changes,'all_other_data':'unchanged from V5','source_sha256':hashlib.sha256((OUT/'classroom_fart_v6.blend').read_bytes()).hexdigest()},indent=2))
print('V6 recline-neck and jump coverage confirmation complete.',flush=True)
