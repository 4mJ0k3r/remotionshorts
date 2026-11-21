import bpy,json
from pathlib import Path
from bpy_extras.object_utils import world_to_camera_view as proj
exec(compile(bpy.data.texts['slow_eddie_v6_runtime.py'].as_string(),'runtime','exec'))
o=bpy.data.objects['Copper_bullet']
print('BULLET',o.dimensions[:],o.scale[:])
for m in o.data.materials:
 print('MATERIAL',m.name)
 for n in m.node_tree.nodes:
  print(n.name,n.type,[(x.name,str(x.default_value)) for x in n.inputs if hasattr(x,'default_value')],[(l.from_node.name,l.to_node.name) for l in m.node_tree.links])
for f in [15,60,90]:
 s.frame_set(f);update(s);print('FRAME',f,'BULLET',o.location[:],'GUN',bpy.data.objects['Challenger_revolver'].dimensions[:])
 print('CORNERS',[(x,tuple(proj(s,cam,bpy.data.objects[x].matrix_world@V(c)))[:2]) for x in ['challenger_head','Challenger_revolver','Copper_bullet'] for c in bpy.data.objects[x].bound_box])
