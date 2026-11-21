from pathlib import Path
root=Path('D:/remotionshorts/scripts/circle_challenge')
path=root/'motion_revision.py'
exec(compile(path.read_text(),str(path),'exec'),{})
code=(root/'calibrate.py').read_text().replace(";s=bpy.context.scene","/'v4_frames';OUT.mkdir(exist_ok=True);s=bpy.context.scene")
exec(compile(code,'calibrate.py','exec'),{})
