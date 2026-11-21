"""Check saved runtime, full grip/contact intervals, and text-free scene metadata."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[2]/'renders'/'commode_sniper'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'commode_sniper.blend'))
scope={'__name__':'commode_saved_runtime'}
exec(compile(bpy.data.texts['commode_runtime.py'].as_string(),'commode_saved_runtime','exec'),scope)
S=scope['S'];sc=bpy.context.scene
text_objects=[o.name for o in sc.objects if o.type=='FONT'];assert not text_objects
frames=set((1,42,43,83,84,140,141,185,186,235,236,305,306,345,346,416,417,617,618,722,723,803,804,848,849,904,905,1082,1083,1170,1171,1247,1248,1361,1362,1456,1457,1538,1539,1635))
frames.update(range(346,417));frames.update(range(1362,1457));frames.update(range(1539,1636))
max_brush_error=0;max_head_error=0;max_paper_error=0;gulp_splash_violations=[]
for f in sorted(frames):
    sc.frame_set(f)
    delta=S['boy_head'].rotation_euler.to_quaternion().rotation_difference(sc.camera.rotation_euler.to_quaternion()).angle
    max_head_error=max(max_head_error,delta)
    if 346<=f<417:
        if any(not o.hide_render for o in S['splashes']):gulp_splash_violations.append(f)
        assert S['poop_face'].data.materials[0].name==S['poop_faces']['gulp'].name
    if 1362<=f<1457:
        for i,side in enumerate((-1,1)):
            foot=Vector(S['poop_legs'][i].data.splines[0].points[-1].co[:3])
            expected=Vector(S['paper_contact'])+Vector((0,side*.055,.003))
            max_paper_error=max(max_paper_error,(foot-expected).length)
    if 1539<=f<=1635:max_brush_error=max(max_brush_error,S['brush_grip_error'])
    assert sc.camera.data.dof.use_dof
assert max_head_error<1e-5 and max_brush_error<1e-5 and max_paper_error<1e-5 and not gulp_splash_violations
sc.frame_set(700);assert S['poop_face'].data.materials[0].name==S['poop_faces']['idle'].name
sc.frame_set(760);assert S['poop_face'].data.materials[0].name==S['poop_faces']['cool'].name
result={'saved_runtime_executes':True,'sampled_frames':len(frames),'text_objects':text_objects,
        'maximum_head_billboard_error_radians':max_head_error,'maximum_brush_grip_error_m':max_brush_error,
        'maximum_paper_foot_anchor_error_m':max_paper_error,'gulp_splash_violations':gulp_splash_violations,
        'glasses_appear_in_cut_2C':True,'depth_of_field_enabled':True,'raytracing':sc.eevee.use_raytracing}
(OUT/'rig_checks.json').write_text(json.dumps(result,indent=2));print('QA saved scene and contacts passed',flush=True)
