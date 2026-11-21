from pathlib import Path
root=Path('D:/remotionshorts/scripts/circle_challenge')
exec(compile((root/'cinematic.py').read_text(encoding='utf-8-sig'),'cinematic.py','exec'),{})
code=(root/'calibrate.py').read_text().replace(";s=bpy.context.scene","/'v2_frames';OUT.mkdir(exist_ok=True);s=bpy.context.scene")
exec(compile(code,'calibrate.py','exec'),{})
