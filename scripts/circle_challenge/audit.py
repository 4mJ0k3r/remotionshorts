"""Read-only scene assertions and projection evidence; no renders or scene save."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
s=bpy.context.scene
frames=[70,205,330,420,515,655,830,1030,1200,1380,1495,1600,1795,1950,2140]
subjects=['char_you']*7+['char_brain_op','char_you','char_you','char_rival','char_rival','char_you','char_mummy','char_mummy']
data={'renderer':s.render.engine,'raytracing':s.eevee.use_raytracing,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'samples':s.eevee.taa_render_samples,'fps':s.render.fps,'range':[s.frame_start,s.frame_end],'objects':len(s.objects),'pose_nonconstant_keys':[],'handlers_required':False,'projection':[]}
for o in s.objects:
    if ('_body' in o.name or '_head' in o.name or o.name.startswith('HUD pose')) and o.type=='MESH' and o.animation_data:
        for fc in o.animation_data.action.fcurves:
            if fc.data_path=='scale':
                for k in fc.keyframe_points:
                    if k.interpolation!='CONSTANT':data['pose_nonconstant_keys'].append([o.name,k.co.x])
for f,name in zip(frames,subjects):
    s.frame_set(f);bpy.context.view_layer.update();root=bpy.data.objects[name]
    pos=root.matrix_world.translation;foot=world_to_camera_view(s,s.camera,pos)
    hp=bpy.data.objects[name+'_head_independent_pivot'];head=world_to_camera_view(s,s.camera,hp.matrix_world.translation)
    data['projection'].append({'frame':f,'subject':name,'foot':[round(foot.x,3),round(foot.y,3)],'head':[round(head.x,3),round(head.y,3)]})
assert data['pose_nonconstant_keys']==[]
assert (s.frame_start,s.frame_end,s.render.fps)==(1,2205,30)
Path('D:/remotionshorts/renders/circle_challenge/scene_audit.json').write_text(json.dumps(data,indent=2))
s.frame_set(70)
