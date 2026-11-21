from pathlib import Path
import bpy
root=Path('D:/remotionshorts/scripts/circle_challenge')
ns={}
source=(root/'cinematic.py').read_text(encoding='utf-8-sig')
exec(compile(source.split('# Replace checker blocks')[0],'cinematic helpers','exec'),ns)
exec(compile((root/'cinematic_finish.py').read_text(encoding='utf-8-sig'),'cinematic_finish.py','exec'),ns)
scene=bpy.context.scene
ns['finish'](scene,ns['key'])
scene.frame_set(70)
bpy.ops.wm.save_as_mainfile(filepath='D:/remotionshorts/renders/circle_challenge/circle_challenge.blend')
code=(root/'calibrate.py').read_text().replace(";s=bpy.context.scene","/'v2_frames';OUT.mkdir(exist_ok=True);s=bpy.context.scene")
exec(compile(code,'calibrate.py','exec'),{})
