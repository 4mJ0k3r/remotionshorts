import bpy
from pathlib import Path
s=bpy.context.scene
# Hide the off-shot stage host during protagonist inserts.
h=bpy.data.objects['char_youtuber']
for f,v in [(1,1),(144,0),(1299,1),(1446,0),(1668,1),(1854,0)]:
    h.scale=(v,v,v);h.keyframe_insert('scale',frame=f)
for fc in h.animation_data.action.fcurves:
    if fc.data_path=='scale':
        for k in fc.keyframe_points:k.interpolation='CONSTANT'
# Preserve view settings but remove editor overlays from viewport inspection.
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':a.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(Path('D:/remotionshorts/renders/circle_challenge/circle_challenge.blend')))
exec(compile(Path('D:/remotionshorts/scripts/circle_challenge/calibrate.py').read_text(), 'calibrate.py','exec'),{})
