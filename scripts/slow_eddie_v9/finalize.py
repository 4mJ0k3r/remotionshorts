import bpy,sys
from pathlib import Path
sys.path.insert(0,'D:/remotionshorts/tools/V9_Parity_Packet/V9_Parity_Packet');import v9_patch_helpers as H
P=Path('D:/remotionshorts/renders/slow_eddie_v9');s=bpy.context.scene;nt=bpy.data.objects['Dusty Main Street'].data.materials[0].node_tree;ramp=next(n for n in nt.nodes if n.type=='VALTORGB');ramp.color_ramp.elements[1].position=.85
mat=H.metal('V9 dry twig','#9B714A',0,.9)
for o in bpy.data.objects['Rolling_tumbleweed'].children:
 if o.type=='CURVE':o.data.materials.clear();o.data.materials.append(mat)
t=bpy.data.texts['slow_eddie_v9_runtime.py'];t.from_string(Path('D:/remotionshorts/scripts/slow_eddie_v9/runtime.py').read_text());exec(compile(t.as_string(),t.name,'exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v9.blend'))
