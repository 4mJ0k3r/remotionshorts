from pathlib import Path
root=Path('D:/remotionshorts/scripts/circle_challenge')
path=root/'reference_v3.py'
exec(compile(path.read_text(encoding='utf-8-sig'),str(path),'exec'),{})
code=(root/'calibrate.py').read_text().replace(";s=bpy.context.scene","/'v3_frames';OUT.mkdir(exist_ok=True);s=bpy.context.scene")
exec(compile(code,'calibrate.py','exec'),{})
