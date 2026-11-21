"""Read-only full-interval checks for the five user-requested fixes."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
s=bpy.data.scenes['Classroom_Master'];bpy.context.window.scene=s
hip=bpy.data.objects['char_you glossy royal-blue pelvis'];body=bpy.data.objects['char_you connected torso pivot'];head=bpy.data.objects['char_you independent camera-facing head'];chair=bpy.data.objects['Chair 0.0 0.7 floor pivot']
originals=(hip,body,head,chair)
lower=json.loads((OUT/'assets_surgical_v2/head_bounds.json').read_text())['you_lower_world']
err={'grip':[],'pelvis_seat':[],'scuff_z':[],'slump_z':[],'slump_contact':[],'pitch':[],'forward_slide':[],'nose':[],'landing':[]};strain=[];shoe_y=[[],[]];stream_y=[];stream_z=[];nose_eye_overlap=[]
for f in list(range(266,477))+list(range(735,769))+list(range(804,905))+list(range(978,1215))+list(range(1299,1636)):
    s.frame_set(f);s.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get()
    hip,body,head,chair=[o.evaluated_get(dg) for o in originals]
    if 266<=f<477:
        for sign in [-1,1]:
            hand=bpy.data.objects['you rounded mitten '+str(sign)].evaluated_get(dg).matrix_world.translation
            targets=[chair.matrix_world@V((x,0,.46)) for x in [-.23,.23]];err['grip'].append(min((hand-t).length for t in targets))
        err['pelvis_seat'].append(abs(hip.matrix_world.translation.z-hip.scale.z-.46));strain.append(hip.matrix_world.translation.x)
    if 735<=f<769:
        for i,sign in enumerate([-1,1]):
            foot=bpy.data.objects['you oval grounded foot '+str(sign)].evaluated_get(dg).matrix_world.translation;err['scuff_z'].append(abs(foot.z-.03));shoe_y[i].append(foot.y)
    if 828<=f<905:
        err['slump_z'].append(abs(head.matrix_world.translation.z-1.1925));up=head.matrix_world.to_quaternion()@V((0,1,0));err['slump_contact'].append(abs(head.matrix_world.translation.z-lower*abs(up.z)-1.0125))
    if 1000<=f<1215:
        up=body.matrix_world.to_quaternion()@V((0,1,0));pitch=math.degrees(math.atan2(up.y,up.z));err['pitch'].append(abs(pitch-45));err['forward_slide'].append(abs(hip.matrix_world.translation.y+.07))
    if 1085<=f<1215:
        for i in range(14):
            p=bpy.data.objects['V2 rear fart stream '+str(i)].evaluated_get(dg)
            if p.color[3]>.001:
                delta=p.matrix_world.translation.y-hip.matrix_world.translation.y;stream_y.append(delta);stream_z.append(p.matrix_world.translation.z)
                assert delta>=.1199 and p.matrix_world.translation.z<.70,'Stream moves toward the torso or neck'
    if 1299<=f<1410:
        hand=bpy.data.objects['you rounded mitten 1'].evaluated_get(dg).matrix_world.translation;local=head.matrix_world.inverted()@hand;err['nose'].append((local-V((0,-.14,.045))).length)
        # Eye inner edges are +/-0.14m; the nose mitten stays within +/-0.06m.
        nose_eye_overlap.append(abs(local.x)+.062>.14)
    if f>=1466:
        for sign in [-1,1]:
            fo=bpy.data.objects['you oval grounded foot '+str(sign)].evaluated_get(dg);foot=fo.matrix_world.translation;err['landing'].append(abs(foot.z-fo.scale.z-.46));local=chair.matrix_world.inverted()@foot
            assert abs(local.x)+.105<=.2301 and abs(local.y)+.15<=.3051,f'Foot beyond seat f={f} sign={sign} local={list(local)} world={list(foot)} chair={list(chair.matrix_world.translation)}'
result={k+'_max_error':max(v) if v else None for k,v in err.items()}
result.update(strain_range=[min(strain),max(strain)],scuff_y_ranges=[[min(x),max(x)] for x in shoe_y],stream_rear_offset_min=min(stream_y),stream_z_range=[min(stream_z),max(stream_z)],stream_objects=14,haze_objects=16,pressure_objects=3,nose_eye_overlap=any(nose_eye_overlap))
(OUT/'surgical_v2_contact_audit.json').write_text(json.dumps(result,indent=2));print('SURGICAL V2 AUDIT',json.dumps(result),flush=True)
assert all(max(v)<1e-4 for k,v in err.items() if v),'Contact or true pitch check failed'
assert min(strain)<-.0079 and max(strain)>.0079 and not any(nose_eye_overlap)
assert all(max(x)-min(x)>.239 for x in shoe_y)
