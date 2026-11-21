import bpy,json,hashlib
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');cam=bpy.data.objects['Delivery camera'];row=next(r for r in json.loads((OUT/'shots_v2.json').read_text())['shots'] if r['shot']=='4C')
for f in range(row['start_frame'],row['end_frame']+1):cam.data.lens=23;cam.data.keyframe_insert('lens',frame=f)
cam.data.animation_data.action.update_tag();cam.data.update_tag()
bpy.context.window.scene=bpy.data.scenes['CF_1A'];bpy.context.scene.frame_set(1)
source=OUT/'classroom_fart_surgical_v2_verified.blend';bpy.ops.wm.save_as_mainfile(filepath=str(source))
s=bpy.data.scenes['CF_4C'];bpy.context.window.scene=s
for f in [1083,1145,1214]:s.frame_set(f);s.render.filepath=str(OUT/'v2_surgical_calibration_final'/f'{f:04}.png');bpy.ops.render.render(write_still=True)
p=OUT/'v2_calibration_manifest.json';d=json.loads(p.read_text());d.update(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),safe_area_patch={'frames':[1083,1214],'lens_mm':23,'other_animation_and_scene_data':'unchanged'});p.write_text(json.dumps(d,indent=2))
