"""Read-only full-contact interval checks and camera evidence."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');ROWS=json.loads((OUT/'shots.json').read_text())['shots']
chair=bpy.data.objects['Chair 0.0 0.7 floor pivot'];pelvis=bpy.data.objects['char_you glossy royal-blue pelvis']
grip=[];seat=[];landing=[];bounds=[];seat_penetrations=[]
for row in ROWS:
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s
    for f in range(row['start_frame'],row['end_frame']+1):
        s.frame_set(f)
        if 266<=f<477:
            for sign in [-1,1]:
                hand=bpy.data.objects['you rounded mitten '+str(sign)];target=chair.matrix_world@V((-sign*.325,.02,.58));grip.append((hand.matrix_world.translation-target).length)
        if f<1422:
            seatpoint=chair.matrix_world@V((0,0,.58));normal=(chair.matrix_world.to_3x3()@V((0,0,1))).normalized()
            p=pelvis.matrix_world;radius=math.sqrt(sum((normal.dot(p.to_3x3().col[i]))**2 for i in range(3)))
            seat.append(abs(normal.dot(p.translation-seatpoint)-radius))
            inv=chair.matrix_world.inverted()
            for sign in [-1,1]:
                leg=bpy.data.objects['you curved stick leg '+str(sign)];points=leg.data.splines[0].bezier_points
                for a,b in zip(points,points[1:]):
                    for j in range(13):
                        t=j/12;u=1-t;co=u**3*a.co+3*u*u*t*a.handle_right+3*u*t*t*b.handle_left+t**3*b.co
                        local=inv@(leg.matrix_world@co)
                        if abs(local.x)<.349 and abs(local.y)<.329 and .496<local.z<.604:seat_penetrations.append(f)
        if f>=1475:
            for sign in [-1,1]:
                foot=bpy.data.objects['you oval grounded foot '+str(sign)];landing.append(abs(foot.location.z-.042-.58))
    for f in [row['start_frame'],(row['start_frame']+row['end_frame'])//2,row['end_frame']]:
        s.frame_set(f);names=['you']
        if row['shot'] in ['3C','4B','5C']:names.append('friend')
        if row['shot'] in ['2E','4D']:names=['teacher']
        for name in names:
            h=bpy.data.objects['char_'+name+' independent camera-facing head'];center=h.matrix_world.translation;q=s.camera.rotation_euler.to_quaternion()
            p=[world_to_camera_view(s,s.camera,center+q@V((x,y,0))) for x in [-.49,.49] for y in [-.49,.49]]
            bounds.append({'shot':row['shot'],'frame':f,'actor':name,'x':[min(v.x for v in p),max(v.x for v in p)],'y':[min(v.y for v in p),max(v.y for v in p)]})
result={'grip_frames':211,'max_grip_error_m':max(grip),'max_seated_normal_gap_m':max(seat),'max_settled_sole_gap_m':max(landing),'thigh_seat_penetration_frames':sorted(set(seat_penetrations)),'head_bounds':bounds}
(OUT/'contact_audit.json').write_text(json.dumps(result,indent=2))
print('CONTACT AUDIT',json.dumps({k:v for k,v in result.items() if k!='head_bounds'}),flush=True)
assert max(grip)<1e-5 and max(seat)<1e-4 and max(landing)<1e-5
assert not seat_penetrations,'Swept leg ink intersects the chair seat'
