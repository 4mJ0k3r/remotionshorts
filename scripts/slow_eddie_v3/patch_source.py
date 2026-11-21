import bpy,json,hashlib
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v3');R=Path('D:/remotionshorts/scripts/slow_eddie_v3');s=bpy.context.scene
old=hashlib.sha256((P/'slow_eddie_v3.blend').read_bytes()).hexdigest();text=bpy.data.texts['slow_eddie_v3_runtime.py'];text.clear();text.write((R/'runtime.py').read_text());exec(compile(text.as_string(),'runtime','exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v3.blend'))
(P/'patch_mapping.json').write_text(json.dumps({'reason':'Straw follows head-art mouth anchor through nod','original_source_sha256':old,'final_source_sha256':hashlib.sha256((P/'slow_eddie_v3.blend').read_bytes()).hexdigest(),'rerender_frames':[272,292],'unchanged_frames':[[1,271],[293,300]]},indent=2))
s.frame_set(282);update(s);s.render.resolution_percentage=50;s.render.filepath=str(P/'patch_cal_282.png');bpy.ops.render.render(write_still=True)
