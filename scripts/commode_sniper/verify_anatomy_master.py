"""Independent saved-scene checks for the seven requested anatomy/staging fixes."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[2]/'renders'/'commode_sniper'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'commode_sniper_v2_master.blend'))
runtime=bpy.data.texts['commode_runtime.py']
runtime_source=runtime.as_string()
if 'def pose_boy_legacy(' in runtime_source:
    a=runtime_source.index('def pose_boy_legacy(');b=runtime_source.index('def pose_boy(',a+1)
    runtime_source=runtime_source[:a]+runtime_source[b:];runtime.clear();runtime.write(runtime_source)
ns={'__name__':'anatomy_master_runtime'}
exec(compile(runtime_source,'commode_runtime','exec'),ns)
S=ns['S'];sc=bpy.context.scene
def bounds(obj):
    corners=[obj.matrix_world@Vector(c) for c in obj.bound_box]
    return [min(v[i] for v in corners) for i in range(3)],[max(v[i] for v in corners) for i in range(3)]
def endpoint(obj):return obj.matrix_world@Vector(obj.data.splines[0].points[-1].co[:3])

sc.frame_set(25)
assert abs(S['boy_hips'].matrix_world.translation.z-.52)<1e-6
assert abs(S['boy_hips'].dimensions.x-.22)<1e-5
assert S['boy_spine'].hide_render and not S['boy_torso'].hide_render
for f in range(1,43):
    sc.frame_set(f)
    start=S['jet'].matrix_world@Vector(S['jet'].data.splines[0].points[0].co[:3])
    assert abs(start.z-.49)<1e-6
    assert all(abs(hand.matrix_world.translation.z-.50)<1e-6 for hand in S['boy_hands'])
    assert S['boy_head'].data.materials[0].name.startswith('boy_relaxedturn')
hidden_frames=list(range(43,84))+list(range(141,236))+list(range(306,346))
for f in hidden_frames:
    sc.frame_set(f);assert S['jet'].hide_render
tank_lo,tank_hi=bounds(bpy.data.objects['Toilet cistern'])
deck_lo,deck_hi=bounds(bpy.data.objects['Connected cistern rear deck'])
assert tank_lo[2]<deck_hi[2]
assert min(tank_hi[1],deck_hi[1])>max(tank_lo[1],deck_lo[1])
assert abs(bpy.data.objects['Toilet paper roll'].location.z-.68)<1e-6
assert bounds(bpy.data.objects['Extended rear wall'])[1][2]>=3.599
assert abs(bounds(bpy.data.objects['Warm bathroom ceiling'])[0][2]-3.50)<1e-6
mouth_error=0.;apertures=set();scales=[]
for f in range(346,417):
    sc.frame_set(f)
    target=S['physical_root'].matrix_world@Vector(S['gulp_mouth_socket'])
    tip=endpoint(S['jet']);mouth_error=max(mouth_error,(tip-target).length)
    local=S['gulp_cavity'].matrix_world.inverted()@tip
    assert (local.x/.085)**2+(local.y/.060)**2+(local.z/.015)**2<1
    assert all(obj.hide_render for obj in S['splashes'])
    apertures.add(round(S['gulp_aperture'],2));scales.append(S['poop_root'].scale.x)
assert mouth_error<1e-6 and apertures=={.85,1.18} and max(scales)>1.279
sc.frame_set(520)
oil=S['oil'][0].data.materials[0].node_tree.nodes['Principled BSDF']
assert abs(oil.inputs['Alpha'].default_value-.76)<1e-5
assert abs(oil.inputs['Roughness'].default_value-.04)<1e-5
assert abs(oil.inputs['Specular IOR Level'].default_value-.8)<1e-5
assert not S['oil_ribbon'].hide_render and all(obj.hide_render for obj in S['snacks'])
digits=[obj for obj in S['open_palm'].children if 'finger' in obj.name or 'thumb' in obj.name]
assert len(digits)==5
for f in range(1171,1248):
    sc.frame_set(f);assert S['finger'].hide_render and not S['open_palm'].hide_render
brush_error=0.;radii=[]
for f in range(1539,1636):
    sc.frame_set(f);brush_error=max(brush_error,S['brush_grip_error']);radii.append(S['red_arm'].data.bevel_depth)
    assert not S['boy_hands'][1].hide_render and not S['boy_arms'][1].hide_render
assert brush_error<1e-6 and max(radii)>min(radii)*1.2
assert not [obj for obj in sc.objects if obj.type=='FONT']
report={'groin_stream_world_z_m':.49,'hands_world_z_m':.50,'hips_world_z_m':.52,'pelvis_width_m':.22,
        'tank_and_deck_overlap':True,'paper_roll_wall_height_m':.68,'wall_top_m':3.6,'ceiling_underside_m':3.5,
        'reaction_frames_stream_hidden':len(hidden_frames),'gulp_frames_checked':71,
        'maximum_mouth_socket_error_m':mouth_error,'stream_ends_inside_mouth_cavity':True,
        'gulp_aperture_factors':sorted(apertures),'maximum_body_growth':max(scales),
        'continuous_oil_pour':True,'opaque_food_clumps_removed':True,'open_palm_digits':len(digits),
        'maximum_brush_grip_error_m':brush_error,'normal_black_forearm_retained':True,
        'pain_aura_radii_m':[min(radii),max(radii)],'text_objects':0}
(OUT/'anatomy_rig_checks.json').write_text(json.dumps(report,indent=2))
sc.frame_set(25)
source=bpy.data.texts.get('build_commode_sniper.py') or bpy.data.texts.new('build_commode_sniper.py')
source.clear();source.write((Path(__file__).resolve().parent/'build_commode_sniper.py').read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'commode_sniper_v2_master.blend'))
print('QA seven anatomy and staging checks passed',flush=True)
