"""Check actual saved V3 transforms, grip contact and final FX visibility."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).parent))
from v2_common import OUT
from v2_story import cut_at

bpy.ops.wm.open_mainfile(filepath=str(OUT/'caveman_toilet_v3.blend'))
sc=bpy.context.scene
errors=[]
checks=0
samples=sorted(set(range(1,1621,8))|{159,365,395,429,540,1038,1125,1145,1165,1180,1370,1380,1392,1427,1462,1493,1494,1560,1620})
for f in samples:
    sc.frame_set(f)
    normal=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1))
    for char in cut_at(f)[5]:
        torso=bpy.data.objects[f'torso_{char}']
        head=bpy.data.objects[f'headpivot_{char}']
        for ob in (torso,head):
            n=ob.matrix_world.to_quaternion()@Vector((0,0,1))
            if n.dot(normal)<.9999:
                errors.append(f'f{f} {ob.name} not camera-parallel')
            checks+=1
        d=(head.matrix_world.translation-torso.matrix_world.translation).length
        if abs(d-((.355+.248*.88)**2+.012**2)**.5)>1e-4:
            errors.append(f'f{f} {char} neck offset changed {d}')
        checks+=1
        if cut_at(f)[0] == 13:
            for j in range(3):
                point=bpy.data.objects[f'arm_{char}_1_p{j}'].matrix_world.translation
                view=world_to_camera_view(sc,sc.camera,point)
                if not (.015<view.x<.985):
                    errors.append(f'f{f} {char} pinch arm cropped: {view.x}')
                checks+=1
    if 1370<=f<1494:
        shovel=bpy.data.objects['fx_shovel']
        origin=shovel.matrix_world.translation
        direction=shovel.matrix_world.to_quaternion()@Vector((0,0,1))
        for side,grip in ((-1,.66),(1,.38)):
            hand=bpy.data.objects[f'hand_caveman_{side}'].matrix_world.translation
            if (hand-(origin+direction*grip)).length>1e-4:
                errors.append(f'f{f} shovel grip {side} lost contact')
            checks+=1
    if f>=1494:
        for i in range(5):
            ob=bpy.data.objects[f'clod_{i}']
            if ob.scale.length>1e-6 or not ob.hide_render:
                errors.append(f'f{f} ending clod {i} still visible')
            checks+=1
        shovel=bpy.data.objects['fx_shovel']
        if shovel.hide_render or abs(shovel.location.x-.75)>1e-5:
            errors.append(f'f{f} shovel not planted')
        for char in ('caveman','elder'):
            head=bpy.data.objects[f'headpivot_{char}']
            for x in (-.33,.33):
                for y in (-.33,.33):
                    p=head.matrix_world@Vector((x,y,0))
                    view=world_to_camera_view(sc,sc.camera,p)
                    if not (.01<view.x<.99 and .07<view.y<.96):
                        errors.append(f'f{f} {char} head out of safe frame {tuple(view)}')
                    checks+=1
camera_z=sc.camera.animation_data.action.fcurves.find('location',index=2)
max_step=max(abs(camera_z.evaluate(f)-camera_z.evaluate(f-1))
             for a,b in ((159,306),(429,540)) for f in range(a+1,b))
if max_step>.09:
    errors.append(f'Walking camera height jump {max_step:.4f}m')
checks+=1
report=dict(checks=checks,errors=errors,max_walking_camera_step_m=max_step,
            frames=1620,resolution=[180,320],samples=12)
(OUT/'qa_v3_rig.json').write_text(json.dumps(report,indent=2))
print('BUILD V3 rig checks:',checks,'errors:',len(errors),flush=True)
for e in errors[:20]: print('BUILD '+e,flush=True)
if errors: raise RuntimeError('V3 rig verification failed')
