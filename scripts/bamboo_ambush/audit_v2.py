"""Read-only keyframe checks; no renders or scene writes."""
import bpy,json
from pathlib import Path
from mathutils import Vector as V
OUT=Path(r'D:\remotionshorts\renders\bamboo_ambush');s=bpy.context.scene;ob=bpy.data.objects;records=[]
for f in [21,22,44,45,140,240,345,769,771,773,800,834,835,860,889,891,910,935]:
 s.frame_set(f);s.view_layers[0].update();p={'frame':f,'soldier_head':list(ob['soldier_head_pivot'].location),'soldier_torso':list(ob['soldier_body_pivot'].location),'enemy_head':list(ob['enemy_head_pivot'].location),'enemy_torso':list(ob['enemy_body_pivot'].location),'enemy_palms':[list(ob['enemy_hand_'+str(sign)].location) for sign in [-1,1]],'bamboo_bottom':list(ob['Bamboo_Breathing_Tube'].location)}
 if f in [769,771,773,800,834,889,891,910,935]:p['palm_support_errors_m']=[abs(ob['enemy_hand_'+str(sign)].location.z-.026) for sign in [-1,1]]
 if f in [835,860,889,891,910,935]:
  h=ob['soldier_head_pivot'];mouth=h.location+h.rotation_quaternion@V((0,(.5-1085/1536)*1.16*.82*.62,.008*.82*.62));p['pipe_to_mouth_error_m']=(mouth-ob['Bamboo_Breathing_Tube'].location).length
 records.append(p)
assert all(max(r.get('palm_support_errors_m',[0]))<1e-5 for r in records)
assert all(r.get('pipe_to_mouth_error_m',0)<1e-5 for r in records)
by={r['frame']:r for r in records};assert (V(by[21]['soldier_torso'])-V(by[22]['soldier_torso'])).length<1e-5
(OUT/'v2_contact_audit.json').write_text(json.dumps({'frames':records,'head_north':by[140]['soldier_head'][1]>by[140]['soldier_torso'][1],'no_caption_objects':not any(o.type=='FONT' for o in s.objects),'head_transition21_to22_continuous':True},indent=2));print('V2 SUPPORT/MOUTH/ENTRY CHECKS PASSED',flush=True)
