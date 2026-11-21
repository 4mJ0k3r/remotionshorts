import bpy,json
from pathlib import Path
s=bpy.context.scene
print('RL',[(n.name,[x.name for x in n.outputs]) for n in s.node_tree.nodes if n.type=='R_LAYERS'])
for o in s.objects:
 if any(x in o.name for x in ['flared vest','tailored shirt','pearl','rear','cap','groove','Rolling_tumbleweed']):print('OBJ',o.name,o.type,'parent',o.parent.name if o.parent else None,'location',tuple(o.location),'scale',tuple(o.scale))
for ch in bpy.data.objects['Rolling_tumbleweed'].children[:2]:print('TWIG',ch.name,ch.data.bevel_depth,[m.name for m in ch.data.materials])
print('WORLDBG',[(n.name,list(n.inputs[0].default_value) if n.inputs[0].type=='RGBA' else '') for n in s.world.node_tree.nodes if n.type=='BACKGROUND'])
