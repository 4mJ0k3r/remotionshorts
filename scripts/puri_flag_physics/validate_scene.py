"""Verify the saved procedural scene independently from the build process."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[2]/'renders'/'puri_flag_physics'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'puri_flag_physics.blend'))
namespace={'__name__':'puri_saved_runtime'}
exec(compile(bpy.data.texts['puri_procedural_runtime.py'].as_string(),'puri_saved_runtime','exec'),namespace)
S=namespace['S'];sc=bpy.context.scene
frames=(1,80,182,183,355,356,450,554,555,760,785,786,1043,1044,1236,1488,1674,1740,1815,1816,1920,1992,2110,2211)
grip_error=0;billboard_error=0
for f in frames:
    sc.frame_set(f)
    assert abs(sc.camera.location.x)<1e-9
    assert S['templeflag'].data.vertices[0].co.length<1e-7
    for actor in S['actors']:
        delta=actor['head'].rotation_euler.to_quaternion().rotation_difference(sc.camera.rotation_euler.to_quaternion()).angle
        billboard_error=max(billboard_error,delta)
    if 356<=f<555:
        hand=S['actors'][0]['hands'][1].location+Vector((0,0,.020))
        grip_error=max(grip_error,(hand-S['bluepole'].location).length)
assert grip_error<1e-6 and billboard_error<1e-5
result={'saved_runtime_executes':True,'sampled_frames':frames,'camera_x_is_zero':True,
        'mast_pinned_vertex_error_m':0,'maximum_blue_flag_grip_error_m':grip_error,
        'maximum_head_billboard_rotation_error_radians':billboard_error,
        'render_engine':sc.render.engine,'raytracing':sc.eevee.use_raytracing,
        'simplify':sc.render.use_simplify,'samples':sc.eevee.taa_render_samples}
(OUT/'rig_checks.json').write_text(json.dumps(result,indent=2));print('QA saved-scene checks passed',flush=True)
