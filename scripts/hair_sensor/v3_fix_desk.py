"""Put every visible scientist fully behind the actual bench rear edge."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector as V,Quaternion,Matrix
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
rows=json.loads((OUT/'shots_v3.json').read_text())['shots']
changes={'1B':(.96,0,.96),'1E':(.82,0,.82),'2C':(.96,0,.96),'2G':(.78,-.20,0),'3B':(.90,0,.90),'3E':(.20,0,.20)}
sizes={'1B':1,'1E':.95,'2C':1,'2G':.83,'3B':.97,'3E':.9}

def channel(ob,path,f):
    value=list(ob.path_resolve(path))
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            if fc.data_path==path:value[fc.array_index]=fc.evaluate(f)
    return value

def offset_curves(owner,path_prefix,axis,amount):
    if not amount or not owner.animation_data or not owner.animation_data.action:return
    for fc in owner.animation_data.action.fcurves:
        if fc.data_path.startswith(path_prefix) and fc.array_index==axis:
            for k in fc.keyframe_points:k.co.y+=amount
            fc.update()
    owner.animation_data.action.update_tag();owner.update_tag()

def translate(ob,delta):
    delta=V(delta)
    if ob.type=='CURVE' and ('curved stick arm' in ob.name or 'curved leg' in ob.name):
        for sp in ob.data.splines:
            for p in sp.bezier_points:p.co+=delta
        for axis in range(3):offset_curves(ob.data,'splines[',axis,delta[axis])
    else:
        ob.location+=delta
        for axis in range(3):offset_curves(ob,'location',axis,delta[axis])

def adjust_right_arm(scene,body_delta,target_delta):
    right=sorted([o for o in scene.objects if o.name.startswith('scientist curved stick arm')],key=lambda o:o.name)[1]
    hand=sorted([o for o in scene.objects if o.name.startswith('scientist rounded grip')],key=lambda o:o.name)[1]
    difference=target_delta-body_delta
    for idx,weight in ((1,.5),(2,1)):
        prefix=f'splines[0].bezier_points[{idx}].co'
        right.data.splines[0].bezier_points[idx].co.y+=difference*weight
        offset_curves(right.data,prefix,1,difference*weight)
    translate(hand,(0,difference,0))

for shot,(dy,dx,cy) in changes.items():
    s=bpy.data.scenes['V3_'+shot];bpy.context.window.scene=s
    if shot in ('2G','3B','3E'):
        for ob in s.objects:
            if ob.name.startswith('Desk lamp'):translate(ob,(-1.15,0,0))
    for ob in list(s.objects):
        if ob.name.startswith('scientist') and ob.parent is None:translate(ob,(dx,dy,0))
    if cy:translate(s.camera,(0,cy,0))
    if shot=='1B':
        tool=next(o for o in s.objects if o.name.startswith('Prop_Tweezers grip'));translate(tool,(0,dy,0))
    if shot=='1E':
        board=next(o for o in s.objects if o.name.startswith('Prop_PCB_Sensor') and o.parent is None)
        tool=next(o for o in s.objects if o.name.startswith('Prop_Tweezers grip'))
        translate(board,(0,.60,0));translate(tool,(0,.60,0));adjust_right_arm(s,dy,.60)
    if shot=='3B':
        drone=next(o for o in s.objects if o.name.startswith('V3_Drone'));palm=next(o for o in s.objects if o.name.startswith('Opened supporting palm'))
        translate(drone,(0,.60,0));translate(palm,(0,.60,0));adjust_right_arm(s,dy,.60)
    # Derive shoulder sockets in the actual painted torso plane; bury roots under the shirt.
    body=next(o for o in s.objects if o.name.startswith('scientist torso pivot'))
    arms=sorted([o for o in s.objects if o.name.startswith('scientist curved stick arm')],key=lambda o:o.name)
    hands=sorted([o for o in s.objects if o.name.startswith('scientist rounded grip')],key=lambda o:o.name)
    sz=sizes[shot]
    for f in range(s.frame_start,s.frame_end+1):
        q=Quaternion(channel(body,'rotation_quaternion',f));matrix=Matrix.LocRotScale(V(channel(body,'location',f)),q,V((1,1,1)))
        for i,side in enumerate((-1,1)):
            shoulder=matrix@V((side*.18*sz,.18*sz,-.025*sz));target=V(channel(hands[i],'location',f));elbow=shoulder.lerp(target,.5)+q@V((side*.16*sz,0,0))
            if target.z>=1.03:elbow.z=max(elbow.z,1.09)
            for bp,pos in zip(arms[i].data.splines[0].bezier_points,(shoulder,elbow,target)):bp.co=pos;bp.keyframe_insert('co',frame=f)
    for arm in arms:arm.data.animation_data.action.update_tag();arm.data.update_tag()

# Reopen the authored checkpoint so dependency-graph caches cannot retain old rig poses.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_v3_desk_fixed.blend'))
bpy.ops.wm.open_mainfile(filepath=str(OUT/'hair_sensor_v3_desk_fixed.blend'))

report=[]
for row in rows:
    if row['shot'] not in changes:continue
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[row['camera']]
    wardrobe=[o for o in s.objects if o.name.startswith(('scientist shaded pinstriped wardrobe','scientist pelvis','scientist shaded pelvis','scientist curved leg','scientist supported foot'))]
    rear=.30+1.38/2;minimum=100;worst=None
    for f in range(row['start_frame'],row['end_frame']+1):
        s.frame_set(f+1);s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();dg.update()
        for ob in wardrobe:
            e=ob.evaluated_get(dg)
            if ob.type=='CURVE':
                mesh=e.to_mesh();gap=min((e.matrix_world@v.co).y for v in mesh.vertices)-rear;e.to_mesh_clear()
            else:gap=min((e.matrix_world@V(p)).y for p in e.bound_box)-rear
            if gap<minimum:minimum=gap;worst={'object':ob.name,'frame':f,'translation':list(e.matrix_world.translation)}
    report.append({'shot':row['shot'],'frames':[row['start_frame'],row['end_frame']],'bench_rear_y':rear,'minimum_body_hips_legs_feet_clearance_m':minimum,'worst':worst,'pass':minimum>=.03})
(OUT/'v3_desk_clearance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if not all(x['pass'] for x in report):raise RuntimeError('Body/bench clearance failed; do not render video.')
source=OUT/'hair_sensor_v3_final.blend'
(OUT/'v3_desk_patch_manifest.json').write_text(json.dumps({'base':source.name,'base_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'final':'hair_sensor_v3_desk_fixed.blend','patches':[{'shot':r['shot'],'frames':[r['start_frame'],r['end_frame']]} for r in rows if r['shot'] in changes]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_v3_desk_fixed.blend'))
exec(compile(Path(r'D:\remotionshorts\scripts\hair_sensor\v3_contacts.py').read_text(),'v3_contacts.py','exec'))
for row in rows:
    if row['shot'] not in changes:continue
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(row['sample']);s.camera=bpy.data.objects[row['camera']];s.render.filepath=str(OUT/'v3_stills_final'/f"{row['sample']:04d}.png");bpy.ops.render.render(write_still=True,scene=s.name)
print('DESK_FIX_CALIBRATION_COMPLETE',flush=True)
