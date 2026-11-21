import bpy
from mathutils import Vector
from pathlib import Path
root=Path('D:/remotionshorts/scripts/circle_challenge')
out=root.parent.parent/'renders/circle_challenge'
ns={}
exec((root/'cinematic.py').read_text(encoding='utf-8-sig').split('# Replace checker blocks')[0],ns)
key=ns['key']
s=bpy.context.scene
pole=bpy.data.objects['Three meter award pole']
key(pole,'location',1740,(-2.64,-.33,.49))
key(pole,'rotation_euler',1,pole.rotation_euler.copy())
key(pole,'rotation_euler',1740,Vector((1,0,.41)).to_track_quat('Z','Y').to_euler())
s.frame_set(70)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'circle_challenge.blend'))
s.frame_set(1795)
s.render.filepath=str(out/'v3_frames/frame_1795.png')
bpy.ops.render.render(write_still=True)
s.frame_set(70)
