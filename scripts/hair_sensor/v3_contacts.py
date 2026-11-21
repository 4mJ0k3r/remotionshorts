"""Evaluate full real contact intervals on the saved scene, rather than peak assertions."""
import bpy,json,math
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');rows=json.loads((OUT/'shots_v3.json').read_text())['shots'];results=[]
for row in rows:
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.camera=bpy.data.objects[row['camera']]
    for hand in [o for o in s.objects if 'contact_target' in o]:
        target=bpy.data.objects[hand['contact_target']];maxworld=0;maxpx=0
        for f in range(row['start_frame'],row['end_frame']+1):
            s.frame_set(f+1);s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();dg.update()
            a=hand.evaluated_get(dg).matrix_world@V(hand['contact_local']);b=target.evaluated_get(dg).matrix_world@V(hand['target_local']);err=(a-b).length;maxworld=max(maxworld,err)
            ca=world_to_camera_view(s,s.camera.evaluated_get(dg),a);cb=world_to_camera_view(s,s.camera.evaluated_get(dg),b);maxpx=max(maxpx,math.hypot((ca.x-cb.x)*540,(ca.y-cb.y)*960))
        results.append({'shot':row['shot'],'contact':hand.name,'target':target.name,'frames':[row['start_frame'],row['end_frame']],'maximum_world_error_m':maxworld,'maximum_screen_error_px':maxpx,'pass':maxworld<.002 and maxpx<=1})
    for drone in [o for o in s.objects if 'support_plane_z' in o]:
        maximum=0
        for f in range(row['start_frame'],int(drone['support_until'])+1):
            s.frame_set(f+1);s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();dg.update();m=drone.evaluated_get(dg).matrix_world
            for x in (-.4,.4):
                for y in (-.32,.32):maximum=max(maximum,abs((m@V((x*.6,y*.65,-.21))).z-drone['support_plane_z']))
        results.append({'shot':row['shot'],'contact':'four landing feet / palm top','frames':[row['start_frame'],int(drone['support_until'])],'maximum_world_error_m':maximum,'pass':maximum<.002})
    for hair in [o for o in s.objects if 'filament_target' in o]:
        maximum=0;target=bpy.data.objects[hair['filament_target']];tip=V(hair.data.splines[0].bezier_points[-1].co)
        for f in range(row['start_frame'],row['end_frame']+1):
            s.frame_set(f+1);s.frame_set(f);dg=bpy.context.evaluated_depsgraph_get();dg.update();a=hair.evaluated_get(dg).matrix_world@tip;b=target.evaluated_get(dg).matrix_world.translation;maximum=max(maximum,(a-b).length)
        results.append({'shot':row['shot'],'contact':'held filament endpoint / tweezer jaws','frames':[row['start_frame'],row['end_frame']],'maximum_world_error_m':maximum,'pass':maximum<.002})
(OUT/'v3_contact_checks.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2),flush=True)
if not all(r['pass'] for r in results):raise RuntimeError('Contact validation failed; do not render preview.')
