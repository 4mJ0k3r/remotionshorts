"""Check physical contacts, then render selected calibration or full affected ranges."""
import bpy,json,sys,math,hashlib,time,uuid
from pathlib import Path
from mathutils import Vector as V,Matrix,Quaternion,Euler
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');DATA=json.loads((OUT/'shots_v4.json').read_text());CHANGED={'1A','1C','1D','3A','3B','4B','4C'}

def channel(ob,path,f):
    value=ob.path_resolve(path);value=list(value) if hasattr(value,'__len__') else value
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            if fc.data_path==path:
                if isinstance(value,list):value[fc.array_index]=fc.evaluate(f)
                else:value=fc.evaluate(f)
    return value

def matrix_at(ob,f):
    q=Quaternion(channel(ob,'rotation_quaternion',f)) if ob.rotation_mode=='QUATERNION' else Euler(channel(ob,'rotation_euler',f)).to_quaternion()
    m=Matrix.LocRotScale(V(channel(ob,'location',f)),q,V(channel(ob,'scale',f)))
    return matrix_at(ob.parent,f)@m if ob.parent else m

checks=[]
for row in DATA['shots']:
    if row['shot'] not in CHANGED:continue
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s
    if row['shot'] in ('1A','1C','1D'):
        h=next(o for o in s.objects if 'v4_grip_index' in o);t=bpy.data.objects[h['v4_tweezer']];point=V(h.data.splines[0].bezier_points[h['v4_grip_index']].co)
        error=0;airgap=0;root=[];caps=[o for o in t.children if o.name.startswith('V4 pinching jaw contact cap')]
        for f in range(max(35,s.frame_start),s.frame_end+1):
            error=max(error,(matrix_at(h,f)@point-matrix_at(t,f).translation).length);root.append(channel(h,'location',f)[2])
            airgap=max(airgap,max(0,(matrix_at(caps[0],f).translation-matrix_at(caps[1],f).translation).length-.036))
        checks.append({'shot':row['shot'],'contact_error_m':error,'closed_jaw_air_gap_m':airgap,'root_z_first_last':root[::max(1,len(root)-1)],'pass':error<.00001 and airgap<.00001})
        if row['shot']=='1C':checks.append({'shot':'1C','snap_frame':185,'root_lift_by_frame_210':channel(h,'location',210)[2]-.05,'pass':abs(channel(h,'location',210)[2]-.5)<.00001})
    if row['shot'] in ('3A','3B'):
        pad=next(o for o in s.objects if 'v4_bottom_z' in o);d=next(o for o in s.objects if 'v4_support_pad' in o);bottom=pad.location.z-.01;top=pad.location.z+.01;worst=0
        for f in range(s.frame_start,int(d['support_until'])+1):
            for x in (-.4,.4):
                for y in (-.32,.32):worst=max(worst,abs((matrix_at(d,f)@V((x*.6,y*.65,-.21))).z-top))
        checks.append({'shot':row['shot'],'desk_pad_gap_m':bottom-pad['v4_desk_top'],'landing_foot_gap_m':worst,'pass':abs(bottom-pad['v4_desk_top'])<.00001 and worst<.00001})
    if row['shot']=='4C':
        b=next(o for o in s.objects if 'v4_supported_carry' in o);hands=sorted([o for o in s.objects if o.name.startswith('firefighter rounded grip')],key=lambda o:o.name);legs=sorted([o for o in s.objects if o.name.startswith('victim curved leg')],key=lambda o:o.name);worst=0
        for f in range(s.frame_start,s.frame_end+1):
            B=matrix_at(b,f);torso=B@V((-.18*.67,-.10*.67,-.01));knees=[]
            for leg in legs:knees.append(V([next(fc for fc in leg.data.animation_data.action.fcurves if fc.data_path=='splines[0].bezier_points[1].co' and fc.array_index==axis).evaluate(f) for axis in range(3)]))
            knee=(knees[0]+knees[1])/2-V((0,0,.028))
            for hand,target in zip(hands,(torso,knee)):worst=max(worst,(matrix_at(hand,f).translation-target).length)
        checks.append({'shot':'4C','victim_x_offset':b['v4_x_shift'],'support_hand_error_m':worst,'pass':worst<.00001})
    if row['shot']=='4B':
        m=bpy.data.materials.get('V4 translucent pale green gold human scent');opacity=next(n for n in m.node_tree.nodes if n.type=='MATH');emission=next(n for n in m.node_tree.nodes if n.type=='EMISSION');puffs=[o for o in s.objects if o.name.startswith('Soft scent puff')]
        attached=all(o.data.materials[0]==m for o in puffs);alpha=opacity.inputs[1].default_value;strength=emission.inputs[1].default_value
        checks.append({'shot':'4B','alpha_multiplier':alpha,'emission_strength':strength,'blend_method':m.surface_render_method,'puffs_assigned':len(puffs),'pass':attached and abs(alpha-.22)<1e-6 and abs(strength-2.5)<1e-6 and m.surface_render_method=='BLENDED'})
(OUT/'v4_contact_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2),flush=True)
assert all(x['pass'] for x in checks),'V4 contact check failed'

full='--full' in sys.argv
samples={'1A':[35,65],'1C':[184,185,205,217],'1D':[234],'3A':[864],'3B':[886,911],'4B':[1224],'4C':[1308]}
finished=[]
for row in DATA['shots']:
    if row['shot'] not in CHANGED:continue
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[row['camera']]
    for f in (range(s.frame_start,s.frame_end+1) if full else samples[row['shot']]):
        s.frame_set(f);s.render.filepath=str(OUT/('v4_frames' if full else 'v4_stills')/f'{f:04d}.png');bpy.ops.render.render(write_still=True,scene=s.name)
    finished.append(row['shot']);print('V4_RANGE_COMPLETE',row['shot'],flush=True)
if not full and '--calibration-only' not in sys.argv:
    token=uuid.uuid4().hex;gate=OUT/f'v4_gate_{token}.json';source_hash=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
    (OUT/'v4_calibration_ready.json').write_text(json.dumps({'gate':str(gate),'source_sha256':source_hash,'token':token,'ready':True},indent=2));print('V4_CALIBRATION_READY',str(gate),flush=True)
    deadline=time.monotonic()+120
    while not gate.exists() and time.monotonic()<deadline:time.sleep(1)
    assert gate.exists(),'Calibration review timed out; lock will be released without full render.'
    decision=json.loads(gate.read_text());assert decision.get('approved') and decision.get('source_sha256')==source_hash,'Calibration did not pass; do not render.'
    for row in DATA['shots']:
        if row['shot'] not in CHANGED:continue
        s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[row['camera']]
        for f in range(s.frame_start,s.frame_end+1):
            s.frame_set(f);s.render.filepath=str(OUT/'v4_frames'/f'{f:04d}.png');bpy.ops.render.render(write_still=True,scene=s.name)
        print('V4_MASTER_RANGE_COMPLETE',row['shot'],flush=True)
    full=True
if full:
    (OUT/'v4_render_complete.json').write_text(json.dumps({'completed':True,'shots':finished,'source':bpy.data.filepath,'source_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()},indent=2))
