"""Blender worker: one calibration batch or one restartable movie span."""
import bpy, sys, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/sendha_namak_science'
args=sys.argv[sys.argv.index('--')+1:];mode=args[0]
S=bpy.context.scene
runtime={'__name__':'sendha_runtime'}
exec(bpy.data.texts['sendha_runtime.py'].as_string(),runtime)
original=runtime['update']
# Blender normally logs and swallows frame-handler exceptions. Fail this worker
# explicitly, so a stale pose can never be mistaken for a completed shot.
def checked(scene,*unused):
    try:original(scene)
    except BaseException:
        import traceback,os
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(3)
for h in list(bpy.app.handlers.frame_change_pre):
    if getattr(h,'__name__','')=='update':bpy.app.handlers.frame_change_pre.remove(h)
bpy.app.handlers.frame_change_pre.append(checked)
S.render.resolution_percentage=50;S.eevee.taa_render_samples=16
S.render.use_lock_interface=True
if mode=='verify':
    from mathutils import Vector,Quaternion
    S['set_ink_enabled']=False;max_normal_error=0;max_grip=0;max_fruit=0;max_reach=0;visible_heads=0;min_crystals=100
    assert not any(o.type=='FONT' for o in S.objects),'Unexpected screen/scene text'
    for f in range(1,1729):
        S.frame_set(f)
        cq=S.camera.matrix_world.to_quaternion();cn=cq@Vector((0,0,1))
        for kind in ['boy','partner','doctor']:
            head=S.objects[kind+'_head']
            if not head.hide_render:
                hn=head.rotation_quaternion@Vector((0,0,1));max_normal_error=max(max_normal_error,(hn-cn).length);visible_heads+=1
        if 1<=f<86 or 1326<=f<1481:
            shaker=S.objects['SaltShaker'];socket=S.objects['ShakerGrip']
            anchor=shaker.location+shaker.rotation_quaternion@socket.location
            max_grip=max(max_grip,(anchor-S.objects['boy_handR'].location).length)
        if f<86:
            fruit=S.objects['Strawberry'];local=Vector((0,-.20*fruit.scale.y,-.10*fruit.scale.z))
            max_fruit=max(max_fruit,(fruit.location+fruit.rotation_quaternion@local-S.objects['boy_handL'].location).length)
        if 650<=f<855:min_crystals=min(min_crystals,sum(not S.objects['EmbeddedSalt%02d'%i].hide_render for i in range(36)))
        if 266<=f<447:
            assert all(not S.objects['boy_'+part].hide_render for part in ['hips','legL','legR','shoeL','shoeR'])
        max_reach=max(max_reach,S.get('max_arm_reach_m',0))
        if f%144==0:print('AUDIT_FRAME',f,flush=True)
    assert max_normal_error<1e-5 and max_grip<1e-6 and max_fruit<1e-5 and max_reach<=.49501 and min_crystals>=30
    report={'frames_evaluated':1728,'visible_head_samples':visible_heads,'max_head_normal_error':max_normal_error,'max_shaker_surface_grip_error_m':max_grip,'max_fruit_surface_grip_error_m':max_fruit,'max_arm_reach_m':max_reach,'min_embedded_salt_count':min_crystals,'font_objects':0,'video_resolution':[540,960],'audio_envelope_frames':len(runtime['ENV'])}
    (OUT/'rig_verification_v2.json').write_text(json.dumps(report,indent=2));print('RIG_VERIFIED',json.dumps(report),flush=True)
elif mode=='sheet':
    directory=OUT/'calibration_v2';directory.mkdir(exist_ok=True)
    frames=[60,120,240,360,560,800,960,1210,1298,1415,1585,1710]
    for f in frames:
        S.frame_set(f);S.render.filepath=str(directory/f'{f:04}.png');bpy.ops.render.render(write_still=True)
        print('CALIBRATION',f,flush=True)
else:
    a,b=map(int,args[1:3]);directory=OUT/'v2_frames';directory.mkdir(exist_ok=True)
    S.frame_start=a;S.frame_end=b;S.render.filepath=str(directory/'frame_')
    last=time.time();started=last;times=[]
    def written(scene,*unused):
        global last
        now=time.time();times.append(now-last);last=now
        data={'frame':scene.frame_current,'total':1728,'seconds_per_frame':round(sum(times[-20:])/len(times[-20:]),3),'elapsed_chunk':round(now-started,1)}
        (OUT/'v2_progress.json').write_text(json.dumps(data))
        if len(times)==1:
            import gpu
            print('ACTIVE_GPU',gpu.platform.vendor_get(),gpu.platform.renderer_get(),flush=True)
        if scene.frame_current%30==0:print('PROGRESS',json.dumps(data),flush=True)
    bpy.app.handlers.render_write.append(written)
    try:bpy.ops.render.render(animation=True)
    finally:bpy.app.handlers.render_write.remove(written)
