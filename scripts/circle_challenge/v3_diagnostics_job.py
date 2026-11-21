import bpy
from pathlib import Path
rows=[]
for obj in (bpy.data.objects['HUD pose 0'],bpy.data.objects['char_you_belly_body'],bpy.data.objects['Contestant_01_happy_head']):
    for node in obj.active_material.node_tree.nodes:
        if node.type=='TEX_IMAGE':
            rows.append((obj.name,node.image.name,node.image.filepath,node.image.packed_file.size))
Path('D:/remotionshorts/renders/circle_challenge/art_diagnostics.txt').write_text(repr(rows))
