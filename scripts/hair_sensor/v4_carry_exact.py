"""Retain V3's original torso lean while applying only the requested carry offset/supports."""
import bpy,json,math,hashlib,uuid,time
from pathlib import Path
from mathutils import Vector as V,Matrix,Euler,Quaternion
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
def channel(ob,path,f):
    value=ob.path_resolve(path);value=list(value) if hasattr(value,'__len__') else value
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            if fc.data_path==path:
                if isinstance(value,list):value[fc.array_index]=fc.evaluate(f)
                else:value=fc.evaluate(f)
    return value
def matrix_at(ob,f):return Matrix.LocRotScale(V(channel(ob,'location',f)),Quaternion(channel(ob,'rotation_quaternion',f)),V(channel(ob,'scale',f)))
def set_arm(ob,a,b,c,f):
    for p,v in zip(ob.data.splines[0].bezier_points,(a,b,c)):p.co=v;p.keyframe_insert('co',frame=f)
s=bpy.data.scenes['V3_4C'];bpy.context.window.scene=s;sz=.67
body=next(o for o in s.objects if o.name.startswith('victim torso pivot'));head=next(o for o in s.objects if o.name.startswith('victim independent billboard head'));aim=next(o for o in s.objects if o.name.startswith('victim parallel aim'));firebody=next(o for o in s.objects if o.name.startswith('firefighter torso pivot'))
arms=sorted([o for o in s.objects if o.name.startswith('firefighter curved stick arm')],key=lambda o:o.name);hands=sorted([o for o in s.objects if o.name.startswith('firefighter rounded grip')],key=lambda o:o.name);va=sorted([o for o in s.objects if o.name.startswith('victim curved stick arm')],key=lambda o:o.name);vh=sorted([o for o in s.objects if o.name.startswith('victim rounded grip')],key=lambda o:o.name);legs=sorted([o for o in s.objects if o.name.startswith('victim curved leg')],key=lambda o:o.name)
for f in range(s.frame_start,s.frame_end+1):
    q=Euler(channel(s.camera,'rotation_euler',f)).to_quaternion();loc=V(channel(body,'location',f));bq=q@Quaternion((0,0,1),-.22);body.rotation_quaternion=bq;body.keyframe_insert('rotation_quaternion',frame=f);head.location=loc+bq@V((0,.75*sz,0));aim.location=head.location+q@V((0,0,8));head.keyframe_insert('location',frame=f);aim.keyframe_insert('location',frame=f)
    B=Matrix.LocRotScale(loc,bq,V((1,1,1)));F=matrix_at(firebody,f);torso=B@V((-.18*sz,-.10*sz,-.01));knees=[]
    for leg in legs:knees.append(V([next(fc for fc in leg.data.animation_data.action.fcurves if fc.data_path=='splines[0].bezier_points[1].co' and fc.array_index==axis).evaluate(f) for axis in range(3)]))
    knee=(knees[0]+knees[1])/2-V((0,0,.028))
    for i,(side,target) in enumerate(zip((-1,1),(torso,knee))):
        shoulder=F@V((side*.18*1.02,.18*1.02,-.025*1.02));elbow=shoulder.lerp(target,.5)+q@V((side*.12,0,-.035));set_arm(arms[i],shoulder,elbow,target,f);hands[i].location=target;hands[i].keyframe_insert('location',frame=f)
    for i,side in enumerate((-1,1)):
        shoulder=B@V((side*.18*sz,.18*sz,-.025*sz));target=V(channel(vh[i],'location',f));elbow=shoulder.lerp(target,.5)+q@V((side*.10,0,0));set_arm(va[i],shoulder,elbow,target,f)
for ob in (body,head,aim,*hands):
    for fc in ob.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_v4_master.blend'))
s.frame_set(1308);s.render.filepath=str(OUT/'v4_stills/1308.png');bpy.ops.render.render(write_still=True,scene=s.name)
try:
    import gpu
    device={'vendor':gpu.platform.vendor_get(),'renderer':gpu.platform.renderer_get(),'version':gpu.platform.version_get()};(OUT/'v4_gpu_device.json').write_text(json.dumps(device,indent=2));print('GPU_DEVICE',device,flush=True)
except Exception as e:print('GPU_DEVICE_QUERY',str(e),flush=True)
source_hash=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();gate=OUT/f'v4_carry_gate_{uuid.uuid4().hex}.json';(OUT/'v4_carry_ready.json').write_text(json.dumps({'gate':str(gate),'source_sha256':source_hash},indent=2));print('V4_CARRY_REVIEW_READY',flush=True)
deadline=time.monotonic()+120
while not gate.exists() and time.monotonic()<deadline:time.sleep(1)
assert gate.exists() and json.loads(gate.read_text()).get('approved'),'Carry review did not pass'
for f in range(s.frame_start,s.frame_end+1):
    s.frame_set(f);s.render.filepath=str(OUT/'v4_frames'/f'{f:04d}.png');bpy.ops.render.render(write_still=True,scene=s.name)
complete=json.loads((OUT/'v4_render_complete.json').read_text());complete['source_sha256']=source_hash;complete['final_carry_range']=[1273,1344];(OUT/'v4_render_complete.json').write_text(json.dumps(complete,indent=2));print('V4_FINAL_CARRY_COMPLETE',flush=True)
