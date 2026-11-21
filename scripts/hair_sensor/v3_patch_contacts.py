"""Patch only documented contact ranges in the V3 master, then re-render those ranges."""
import bpy,json,math,time
from pathlib import Path
from mathutils import Vector as V, Matrix, Euler
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');manifest=json.loads((OUT/'shots_v3.json').read_text());patched=[]

s=bpy.data.scenes['V3_1B'];bpy.context.window.scene=s
tool=next(o for o in s.objects if o.name.startswith('Prop_Tweezers grip'))
arms=sorted([o for o in s.objects if o.name.startswith('scientist curved stick arm')],key=lambda o:o.name)
hands=sorted([o for o in s.objects if o.name.startswith('scientist rounded grip')],key=lambda o:o.name)
arm=arms[1];hand=hands[1]
def channel(obj,path,frame):
    value=obj.path_resolve(path);value=list(value) if hasattr(value,'__len__') else value
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            if fc.data_path==path:
                if isinstance(value,list):value[fc.array_index]=fc.evaluate(frame)
                else:value=fc.evaluate(frame)
    return value
for f in range(86,169):
    s.frame_set(f+1);s.frame_set(f);tool.location.x=.76;tool.keyframe_insert('location',frame=f);s.view_layers[0].update();q=Euler(channel(s.camera,'rotation_euler',f)).to_quaternion();grip=V((.76,-.1,1.4))+tool.rotation_euler.to_matrix()@V((0,.015,.61));shoulder=V((0,.34,1.16))+q@V((.245,0,-.012));elbow=shoulder.lerp(grip,.5)+q@V((.16,0,0))
    for bp,pos in zip(arm.data.splines[0].bezier_points,(shoulder,elbow,grip)):bp.co=pos;bp.keyframe_insert('co',frame=f)
    hand.location=grip;hand.keyframe_insert('location',frame=f)
    camera=s.camera;distance=channel(camera.data,'dof.focus_distance',f);position=V(channel(camera,'location',f));focus=position+q@V((0,0,-distance));camera.location=focus+(position-focus)*1.15+q@V((.12,0,0));camera.keyframe_insert('location',frame=f);camera.data.dof.focus_distance=distance*1.15;camera.data.keyframe_insert('dof.focus_distance',frame=f)
hand['contact_target']=tool.name;hand['target_local']=[0,.015,.61];hand['contact_local']=[0,0,0]
patched.append({'shot':'1B','frames':[86,168],'change':'Fingers/hand grip follows actual tweezer handle instead of the jaw.'})

s=bpy.data.scenes['V3_1E'];bpy.context.window.scene=s
for ob in s.objects:
    if ob.name.startswith('Desk lamp'):ob.location.x-=1.15
hair=next(o for o in s.objects if o.name.startswith('Tapered keratin hero filament'))
tool=next(o for o in s.objects if o.name.startswith('Prop_Tweezers grip'))
s.frame_set(290);s.frame_set(291);s.view_layers[0].update();parent=hair.parent;last=V(hair.data.splines[0].bezier_points[-1].co)
parent_world=Matrix.LocRotScale(parent.location,parent.rotation_euler.to_quaternion(),parent.scale)
for f in range(250,292):
    s.frame_set(f+1);s.frame_set(f);s.view_layers[0].update();u=max(0,min(1,(f-250)/24));hair.rotation_euler.y=-(1-u)*math.pi/2
    desired=V(channel(tool,'location',f));hair.location=parent_world.inverted()@desired-hair.rotation_euler.to_matrix()@last
    hair.keyframe_insert('location',frame=f);hair.keyframe_insert('rotation_euler',frame=f)
patched.append({'shot':'1E','frames':[250,291],'change':'The same held filament rotates and lowers into the electrode bridge; endpoint follows tweezer tip.'})
hair['filament_target']=tool.name
for shot,a,b,points in [('2A',292,365,[(-1.6,.04,1.75),(-1.0,.04,1.59)]),('3A',844,885,[(-1.6,-.02,1.20),(-.55,-.02,1.30)])]:
    scene=bpy.data.scenes['V3_'+shot];bpy.context.window.scene=scene
    right=sorted([o for o in scene.objects if o.name.startswith('scientist curved stick arm')],key=lambda o:o.name)[1]
    for f in range(a,b+1):
        for bp,pos in zip(right.data.splines[0].bezier_points[:2],points):bp.co=pos;bp.keyframe_insert('co',frame=f)
    patched.append({'shot':shot,'frames':[a,b],'change':'Offscreen arm extends beyond the crop; semantic fingertip/palm target remains unchanged.'})
for ob in (tool,hair,hand):
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_v3_final.blend'))
(OUT/'v3_patch_manifest.json').write_text(json.dumps({'base':'hair_sensor_v3.blend','final':'hair_sensor_v3_final.blend','patches':patched},indent=2))
exec(compile(Path(r'D:\remotionshorts\scripts\hair_sensor\v3_contacts.py').read_text(), 'v3_contacts.py','exec'))
dest=OUT/'v3_stills_final';dest.mkdir(exist_ok=True)
for row in manifest['shots']:
    if row['shot'] not in ('1B','1E','2A','3A'):continue
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[row['camera']]
    for f in [row['sample']]:
        s.frame_set(f);s.render.filepath=str(dest/f'{f:04d}.png');bpy.ops.render.render(write_still=True,scene=s.name)
print('CONTACT_PATCH_CALIBRATION_READY',flush=True)
