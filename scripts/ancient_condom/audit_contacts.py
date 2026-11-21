"""Read-only scene verification; no renders or saved scene changes."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');data=json.loads((OUT/'shots.json').read_text());audit={'cuts':[],'checks':{}}
for row in data['shots']:
 s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;cam=s.camera;records=[]
 for f in [row['start_frame'],(row['start_frame']+row['end_frame'])//2,row['end_frame']-6 if row['end_frame'] in data['whip_ends'] else row['end_frame']]:
  s.frame_set(f);s.view_layers[0].update();records.append({'frame':f,'eye':list(cam.matrix_world.translation),'focus_distance':cam.data.dof.focus_distance})
 audit['cuts'].append({'id':row['id'],'fstop':cam.data.dof.aperture_fstop,'shadow_enabled':s.eevee.use_shadows,'records':records})
s=bpy.data.scenes['AC_15'];s.frame_set(1315);s.view_layers[0].update();pot=next(o for o in s.objects if o.name.startswith('Pink warm-water teapot') and o.type=='EMPTY');hero=next(o for o in s.objects if o.name.startswith('White ribbed membrane root'));tip=pot.matrix_world@V(pot['spout_local']);closed=hero.matrix_world@V((0,0,1.05));audit['checks']['warm_water_drop_m']=tip.z-closed.z
s=bpy.data.scenes['AC_16'];bpy.context.window.scene=s;s.frame_set(1435);s.view_layers[0].update();hand=next(o for o in s.objects if o.name.startswith('3D hand') and o.type=='EMPTY') if any(o.name.startswith('3D hand') and o.type=='EMPTY' for o in s.objects) else next(o for o in s.objects if 'index_pad_local' in o);pad=hand.matrix_world@V(hand['index_pad_local']);audit['checks']['honey_pad_xyz']=list(pad);audit['checks']['honey_surface_z']=.8+.095+.076;audit['checks']['honey_contact_error_m']=abs(pad.z-audit['checks']['honey_surface_z'])
audit['checks']['real_outline_shadow_culling']=all(m.use_backface_culling_shadow for m in bpy.data.materials if m.name.startswith('Paint 382821') and m.use_backface_culling)
audit['checks']['no_hud']=all(o.type!='FONT' or o.data.body=='羊\n肠\n套' for o in bpy.data.objects)
(OUT/'qa/contact_audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit['checks']),flush=True)
