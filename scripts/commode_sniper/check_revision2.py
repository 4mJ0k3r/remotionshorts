"""Verify rear stance, alternating real grips and unobstructed pressure limbs."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT=Path(__file__).resolve().parents[2]/'renders'/'commode_sniper'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'commode_sniper_v2.blend'))
ns={'__name__':'commode_revision2_check'}
exec(compile(bpy.data.texts['commode_runtime.py'].as_string(),'commode_runtime','exec'),ns)
S=ns['S'];sc=bpy.context.scene
minimum_inset=100.;minimum_screen=1.;maximum_screen=0.;body_z=[];slipped=[]
for f in range(1,43):
    sc.frame_set(f)
    assert S['boy_head'].data.materials[0].name.startswith('boy_rear_0_0')
    assert S['stream_source'][2]>.90
    assert abs(S['boy_spine'].data.splines[0].points[0].co.z-.83)<1e-5
for f in range(236,306):
    sc.frame_set(f);body_z.append(S['poop_position'][2])
    distances=[]
    for i,side in enumerate((-1,1)):
        hand=S['suckers'][i]
        wall=ns['wall_anchor'](hand.location.z,hand.location.y)
        distances.append(wall.x-hand.location.x)
        for corner in hand.bound_box:
            p=world_to_camera_view(sc,sc.camera,hand.matrix_world@Vector(corner))
            minimum_screen=min(minimum_screen,p.x,p.y);maximum_screen=max(maximum_screen,p.x,p.y)
    assert min(distances)<1e-5,'Both hands released at once'
    slipped.append(max(distances))
    for curve in S['poop_arms']+S['poop_legs']:
        for p in curve.data.splines[0].points:
            r=ns['bowl_radius'](p.co.z)
            surface=r*math.sqrt(max(.001,1-(p.co.y/(1.34*r))**2))
            minimum_inset=min(minimum_inset,surface-p.co.x)
assert minimum_inset>.0115
assert minimum_screen>0 and maximum_screen<1
assert max(slipped)>.02 and max(body_z)-min(body_z)>.04
report={'rear_stance_frames':42,'pressure_frames_checked':70,'at_least_one_hand_attached':True,
        'minimum_limb_centerline_wall_inset_m':minimum_inset,'maximum_hand_release_distance_m':max(slipped),
        'body_slip_travel_m':max(body_z)-min(body_z),'grip_bounds_ndc':[minimum_screen,maximum_screen],
        'all_hand_caps_in_frame':True,'text_objects':[o.name for o in sc.objects if o.type=='FONT']}
(OUT/'revision2_rig_checks.json').write_text(json.dumps(report,indent=2))
print('QA revision2 stance, grip, clearance and framing passed',flush=True)
