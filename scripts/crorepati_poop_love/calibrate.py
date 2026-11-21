"""Reopen the packed source; fail on callback errors instead of rendering stale poses."""
import bpy,json,sys,time,traceback,os,math
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/crorepati_poop_love';S=bpy.context.scene
mode=sys.argv[sys.argv.index('--')+1];ns={'__name__':'crorepati_runtime'};exec(bpy.data.texts['crorepati_runtime.py'].as_string(),ns)
original=ns['update']
def checked(scene,*unused):
    try:original(scene)
    except BaseException:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(3)
for h in list(bpy.app.handlers.frame_change_pre):
    if getattr(h,'__name__','')=='update':bpy.app.handlers.frame_change_pre.remove(h)
bpy.app.handlers.frame_change_pre.append(checked)
if mode=='sheet':
    directory=OUT/'calibration_v2';directory.mkdir(exist_ok=True)
    S.render.resolution_percentage=50;S.eevee.taa_render_samples=16
    for cut,a,b,f in ns['SHOTS']:
        S.frame_set(f);S.render.filepath=str(directory/f'{f:04}.png');bpy.ops.render.render(write_still=True);print('CALIBRATION_FRAME',f,flush=True)
elif mode=='insert':
    directory=OUT/'staging_checks_v2';directory.mkdir(exist_ok=True)
    S.render.resolution_percentage=50;S.eevee.taa_render_samples=16
    S.frame_set(1810);S.render.filepath=str(directory/'1810.png');bpy.ops.render.render(write_still=True)
elif mode=='verify':
    S['set_ink_enabled']=False;maximum=0;dof_disabled=[];head_bounds=[];peaks={v[3] for v in ns['SHOTS']};held=0;last=None
    for f in range(1,2125):
        if f%250==0:print('POSE_CHECK',f,flush=True)
        # Direct transform audit across every frame; evaluate the dependency
        # graph normally for the exact rendered calibration samples.
        S['_audit_transforms_only']=f not in peaks
        S.frame_current=f;original(S)
        q=S.camera.rotation_quaternion;normal=q@Vector((0,0,1))
        if last is not None and (S.camera.location-last).length<1e-7:held+=1
        last=S.camera.location.copy()
        if not S.camera.data.dof.use_dof:dof_disabled.append(f)
        for who in ns['ACT']:
            head=S.objects[who+'_head']
            if not head.hide_render:maximum=max(maximum,(head.rotation_quaternion@Vector((0,0,1))-normal).length)
            if f in peaks and not head.hide_render:
                qh=head.rotation_quaternion;radius=.445*ns['ACT'][who].size
                points=[world_to_camera_view(S,S.camera,head.location+qh@Vector((radius*math.cos(i*math.tau/64),radius*math.sin(i*math.tau/64),0))) for i in range(64)]
                bounds=[min(p.x for p in points),min(p.y for p in points),max(p.x for p in points),max(p.y for p in points)]
                head_bounds.append({'frame':f,'actor':who,'bounds':[round(v,5) for v in bounds],'inside':min(bounds[:2])>=0 and max(bounds[2:])<=1})
    assert maximum<1e-5 and not dof_disabled
    assert S.frame_end==2124 and S.render.fps==30
    S['_audit_transforms_only']=False;contacts=[]
    for f in [390,425,520,535]:
        S.frame_set(f);expected=ns['knock'](f,left=f>=519)
        error=max((S.objects['broke_hand'+side].location-target).length for side,target in zip(['L','R'],expected));contacts.append({'frame':f,'hand_target_error_m':error});assert error<.005
    data={'timeline_frames':2124,'poses_checked':2124,'audit_method':'direct frame-addressed head/camera transforms and DOF; evaluated dependency graph at calibration peaks and grip checks','max_head_normal_error':maximum,'held_camera_frames':held,'dof_disabled_at_checked_frames':dof_disabled,'calibration_head_bounds':head_bounds,'door_contact_checks':contacts,'scope':'18 calibration stills only; full movie awaits user audit','native_size':[1080,1920],'review_size':[540,960]}
    assert all(v['inside'] for v in head_bounds),[v for v in head_bounds if not v['inside']]
    seats=[]
    for f,actors,seat_z,front in [(980,['broke'],.605,0),(1980,['broke','millionaire','kid1','kid2'],.61,-.19)]:
        S.frame_set(f)
        for who in actors:
            for side in ['L','R']:
                leg=S.objects[who+'_leg'+side];hip,knee,ankle=[Vector(leg[k]) for k in ['hip','knee','ankle']]
                angle=math.degrees((hip-knee).angle(ankle-knee))
                assert 90<=angle<=103 and ankle.y<front and knee.y<front+.03
                assert abs(hip.z-(seat_z+.022))<.001
                # Every lower-shin sample must stay on the camera side of the
                # bowl / sofa front. The rounded knee clears the support top.
                lower=[Vector(p.co[:3]) for p in leg.data.splines[0].points[15:]]
                assert max(p.y for p in lower)<front+.03
                seats.append({'frame':f,'actor':who,'side':side,'knee_angle_deg':angle,'ankle_y':ankle.y,'support_z':seat_z})
    S.frame_set(860)
    left=S.objects['broke_head'];right=S.objects['millionaire_head'];head_gap=(right.location-left.location).length-2*.40
    assert head_gap>=0
    S.frame_set(1810);toilet_visibility={name:not S.objects[name+' seat rim'].hide_render for name in ['GoldenToiletA','GoldenToiletB','ChildPottyA','ChildPottyB']};assert all(toilet_visibility.values())
    toilet_bounds=[]
    for f in [1757,1810,1879]:
        S.frame_set(f)
        for name in toilet_visibility:
            pts=[world_to_camera_view(S,S.camera,obj.matrix_world@Vector(corner)) for obj in S.objects[name].children_recursive if obj.type=='MESH' for corner in obj.bound_box]
            bounds=[min(p.x for p in pts),min(p.y for p in pts),max(p.x for p in pts),max(p.y for p in pts)]
            assert min(bounds[:2])>.015 and max(bounds[2:])<.985,(f,name,bounds)
            toilet_bounds.append({'frame':f,'prop':name,'bounds':bounds})
    data.update({'revision':2,'seated_leg_checks':seats,'kiss_head_gap_m':head_gap,'four_toilets_visible_f1810':toilet_visibility,'toilet_insert_bounds':toilet_bounds,'montage_day_stamps':'removed; only 5 YEARS LATER retained at f1757-1850'})
    (OUT/'rig_checks_v2.json').write_text(json.dumps(data,indent=2));print('RIG_CHECKS',json.dumps(data),flush=True)
