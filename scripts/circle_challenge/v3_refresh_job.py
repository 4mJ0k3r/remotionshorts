from pathlib import Path
import bpy
root=Path('D:/remotionshorts/scripts/circle_challenge')
out=root.parent.parent/'renders/circle_challenge'
ns={}
exec((root/'reference_art.py').read_text(),ns)
ns['refresh_art'](bpy,out/'assets')
ns['add_hats'](bpy,out/'assets')
bpy.context.scene.frame_set(70)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'circle_challenge.blend'))
code=(root/'calibrate.py').read_text().replace(";s=bpy.context.scene","/'v3_frames';OUT.mkdir(exist_ok=True);s=bpy.context.scene")
exec(compile(code,'calibrate.py','exec'),{})
