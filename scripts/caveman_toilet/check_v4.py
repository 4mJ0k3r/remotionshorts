"""V4 regression and lighting/shader contract verification, headless only."""
import sys
import json
import hashlib
from array import array
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).parent))
from v2_common import OUT
from v4_overhaul import SHEET_FRAMES
from v2_story import cut_at


def motion_snapshot():
    result={}
    prefixes=('root_','torso_','headpivot_','head_','arm_','leg_','hand_','foot_','fx_shovel','clod_')
    for ob in bpy.data.objects:
        if not ob.name.startswith(prefixes) or not ob.animation_data or not ob.animation_data.action:continue
        for fc in ob.animation_data.action.fcurves:
            if fc.data_path not in ('location','rotation_quaternion','scale','hide_render'):continue
            values=array('f',[0.])*(len(fc.keyframe_points)*2)
            fc.keyframe_points.foreach_get('co',values)
            if ob.name=='headpivot_caveman' and fc.data_path=='location':
                values=array('f',[v for i in range(0,len(values),2) if not 735<=values[i]<828 for v in values[i:i+2]])
            result[(ob.name,fc.data_path,fc.array_index)]=hashlib.sha256(values.tobytes()).hexdigest()
    return result

bpy.ops.wm.open_mainfile(filepath=str(OUT/'caveman_toilet_v3.blend'))
baseline=motion_snapshot()
bpy.ops.wm.open_mainfile(filepath=str(OUT/'caveman_toilet_v4.blend'))
current=motion_snapshot()
errors=[]
for key,value in baseline.items():
    if current.get(key)!=value:errors.append(f'Approved motion changed: {key}')
materials=[m for m in bpy.data.materials if m.name.startswith('V4_') and m.name[3:].startswith(('head_','torso_'))]
for m in materials:
    nodes=m.node_tree.nodes
    p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    e=next(n for n in nodes if n.type=='EMISSION')
    mix=nodes['Hotspot-proof 72 percent emission']
    if abs(p.inputs['Roughness'].default_value-1)>1e-6 or p.inputs['Specular IOR Level'].default_value>1e-6:errors.append(m.name+' not matte')
    if abs(mix.inputs[0].default_value-.72)>1e-6 or abs(e.inputs['Strength'].default_value-.88)>1e-6:errors.append(m.name+' wrong emission balance')
if len(materials)!=42:errors.append(f'Expected 42 character materials, got {len(materials)}')
objects=bpy.data.objects
for deleted in ('arch_rim','cave_left','cave_right','cave_ceil','Toxic'):
    if objects.get(deleted):errors.append('Old geometry/light remains: '+deleted)
for prefix,count in [('V4 mouth boulder ',7),('V4 drifting fog ',15),('V4 poop mound ',4)]:
    actual=sum(o.name.startswith(prefix) for o in objects)
    if actual!=count:errors.append(f'{prefix} expected {count}, got {actual}')
fill=objects['CaveFill'].data
if fill.type!='AREA' or fill.energy!=150 or abs(fill.size-6.5)>1e-5 or fill.use_shadow:errors.append('Wrong cave fill')
toxic=objects['V4 broad toxic overhead'].data
if toxic.type!='AREA' or toxic.energy!=95 or toxic.size!=4.5:errors.append('Wrong wide toxic light')
bulb=bpy.data.lights['BulbLight'];energies=[k.co.y for fc in bulb.animation_data.action.fcurves if fc.data_path=='energy' for k in fc.keyframe_points]
if max(energies)>25.0001 or max(energies)<24.9:errors.append('Bulb exceeds/does not reach 25W')
sc=bpy.context.scene
if sc.eevee.use_raytracing or not sc.render.use_simplify or sc.render.simplify_subdivision>2:errors.append('GPU budget configuration changed')
for f in (540,620,800,950,1180,1250,1330):
    sc.frame_set(f)
    if objects['CaveFill'].hide_render or objects['Campfire'].hide_render:errors.append(f'f{f} missing cave fill/key')
    if not objects['Sun'].hide_render or not objects['Sunset'].hide_render:errors.append(f'f{f} outdoor sun leaks into cave')
    for cn in ('caveman','buddy','elder'):
        torso=objects[f'torso_{cn}']
        head=objects[f'headpivot_{cn}']
        if torso.hide_render:continue
        target=.355+.248*(.78 if cn=='caveman' and 735<=f<828 else .88)
        distance=(head.matrix_world.translation-torso.matrix_world.translation).length
        expected=(target**2+.012**2)**.5
        if abs(distance-expected)>.0002:errors.append(f'f{f} {cn} neck disconnected {distance}')
report={'motion_channels_preserved':len(baseline),'character_materials':len(materials),
        'intentional_motion_adjustment':'Corner-squat head lowered 0.0248m along torso up to close neck',
        'bulb_peak_watts':max(energies),'errors':errors}
regions=[]
sc.render.resolution_x=540;sc.render.resolution_y=960
for tile,f in enumerate(SHEET_FRAMES):
    sc.frame_set(f)
    for char in cut_at(f)[5]:
        torso=objects[f'torso_{char}']
        points=[world_to_camera_view(sc,sc.camera,torso.matrix_world@Vector((x,y,0)))
                for x in (-.22,.22) for y in (-.04,.24)]
        xs=[p.x*540 for p in points];ys=[(1-p.y)*960 for p in points]
        regions.append({'frame':f,'tile':tile,'char':char,'box':[int(min(xs)),int(min(ys)),int(max(xs))+1,int(max(ys))+1]})
(OUT/'qa_v4_regions.json').write_text(json.dumps(regions,indent=2))
(OUT/'qa_v4_scene.json').write_text(json.dumps(report,indent=2))
print(f'BUILD V4 verified {len(baseline)} motion channels, {len(materials)} materials; errors={len(errors)}',flush=True)
for error in errors[:25]:print('BUILD '+error,flush=True)
if errors:raise RuntimeError('V4 scene verification failed')
