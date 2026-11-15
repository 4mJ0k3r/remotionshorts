"""Calibration geometry evidence. This does not certify unrendered playback."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/elevator_leak'
scene=bpy.context.scene
scene['set_ink_enabled']=False
namespace={'__name__':'elevator_runtime'}
exec(bpy.data.texts['elevator_runtime.py'].as_string(),namespace)
max_attachment_error=0
max_press_error=0
frames=sorted(set([50,130,190,260,320,400,510,570,620,690,885,970,1090,1210,1340,1460,1560,1710,1840,1910,2050,2145]+list(range(1450,1465))))
for frame in frames:
    scene.frame_set(frame)
    for who in ['employee','boss','baby','commuter1','commuter2','commuter3']:
        for index in range(2):
            arm=scene.objects[f'{who}_arm_{index}']
            endpoint=arm.matrix_world@arm.data.splines[0].bezier_points[-1].co
            hand=scene.objects[f'{who}_hand_{index}'].matrix_world.translation
            max_attachment_error=max(max_attachment_error,(endpoint-hand).length)
    if 1450<=frame<=1464:
        hand=scene.objects['employee_hand_0'].location
        button=scene.objects['Emergency mushroom'].location
        # A .031-m mitten meets the .050-m exposed button face on +X.
        max_press_error=max(max_press_error,(hand-(button+Vector((.081,0,0)))).length)
    assert sum(node.inputs[0].default_value>.5 for node in scene.node_tree.nodes if node.name.startswith('HUD_GATE_'))==1
assert max_attachment_error<1e-5,max_attachment_error
assert max_press_error<1e-5,max_press_error
widths={}
for frame in [190,1340]:
    scene['set_ink_enabled']=True
    scene.frame_set(frame)
    namespace['update'](scene)
    ink=scene.objects['WORLD_INK_PASS']
    measurements=[]
    for start in range(0,min(len(ink.data.vertices),12000),4):
        a=world_to_camera_view(scene,scene.camera,ink.data.vertices[start].co)
        b=world_to_camera_view(scene,scene.camera,ink.data.vertices[start+1].co)
        pixels=math.hypot((a.x-b.x)*1080,(a.y-b.y)*1920)
        if .8<pixels<5:
            measurements.append(pixels)
    measurements.sort()
    widths[str(frame)]={'measured_segments':len(measurements),'median_width_1080px':measurements[len(measurements)//2],'outer_target_1080px':3.78,'crease_target_1080px':1.89,'within_0_15px_of_either_target':sum(min(abs(value-3.78),abs(value-1.89))<.15 for value in measurements)/len(measurements)}
    assert widths[str(frame)]['within_0_15px_of_either_target']>.99,widths[str(frame)]
report={'sampled_pose_frames':len(frames),'arm_to_hand_error_m':max_attachment_error,'press_contact_frames':'1450..1464 inclusive','button_to_mitten_surface_error_m':max_press_error,'screen_width_checks':widths,'timeline':{'fps':30,'frames':2145,'duration_seconds':71.5},'delivery_scope':'Rig checks complement the calibration images and movie QA.'}
if 'LEG_PLANS' in namespace:
    gait_checks={}
    for name,plan in namespace['LEG_PLANS'].items():
        maximum_drift=0
        maximum_lift=0
        tested_stances=0
        for frame in range(2,2146):
            previous=plan.at(frame-1)
            current=plan.at(frame)
            maximum_lift=max(maximum_lift,*current['lift'])
            for side in range(2):
                if previous['active'] and current['active'] and previous['lift'][side]<1e-8 and current['lift'][side]<1e-8:
                    maximum_drift=max(maximum_drift,(Vector(previous['feet'][side])-Vector(current['feet'][side])).length)
                    tested_stances+=1
        assert maximum_drift<1e-8,(name,maximum_drift)
        gait_checks[name]={'planted_frame_pairs':tested_stances,'max_stance_slide_m':maximum_drift,'max_foot_lift_m':maximum_lift}
    report['gait_checks']=gait_checks
    max_angle=0
    max_ratio_error=0
    for frame in [50,130,320,400,690,885,1340,1460,1520,1560,1598,1640,1710,2050]:
        scene['set_ink_enabled']=False
        scene.frame_set(frame)
        camera_q=scene.camera.matrix_world.to_quaternion()
        for who in ['employee','boss','baby','commuter1','commuter2','commuter3']:
            head=scene.objects[who+'_head']
            head_q=head.matrix_world.to_quaternion()
            alignment=abs(head_q.dot(camera_q))
            max_angle=max(max_angle,2*math.acos(min(1,alignment)))
            points=[world_to_camera_view(scene,scene.camera,head.matrix_world@Vector(point)) for point in [(-.4,-.4,0),(.4,-.4,0),(-.4,.4,0)]]
            width=math.hypot((points[1].x-points[0].x)*1080,(points[1].y-points[0].y)*1920)
            height=math.hypot((points[2].x-points[0].x)*1080,(points[2].y-points[0].y)*1920)
            max_ratio_error=max(max_ratio_error,abs(width/height-1))
        if 1520<=frame<=1598:
            x,y,z=scene.camera.location
            assert -1.73<x<1.73 and -1.65<y<1.65 and 0<z<2.74
            assert all(not obj.hide_render for obj in scene.objects if obj.get('ceiling'))
    assert max_ratio_error<.0001,max_ratio_error
    report['head_billboards']={'max_world_rotation_error_rad':max_angle,'max_projected_square_aspect_error':max_ratio_error,'cctv_camera_inside_cabin':True,'ceiling_visible':True}
(OUT/'calibration_checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
for frame in [940,1840,1847,1853,1860]:
    scene['set_ink_enabled']=False
    scene.frame_set(frame)
    item=scene.objects['Prop_Turd_1' if frame<1000 else 'Prop_Turd_2']
    screen=world_to_camera_view(scene,scene.camera,item.matrix_world.translation)
    print('PAYLOAD_PROJECTION',frame,list(item.location),[screen.x,screen.y,screen.z],item.hide_render)
