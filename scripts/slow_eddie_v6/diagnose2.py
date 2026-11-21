import bpy
s=bpy.context.scene
for o in [s.camera,bpy.data.objects['Copper_bullet'],bpy.data.objects['challenger_body']]:
 print(o.name,'ANIM',o.animation_data,'DATA_ANIM',o.data.animation_data,'CONSTRAINTS',[(c.name,c.type) for c in o.constraints])
 if o.animation_data and o.animation_data.action:print([(f.data_path,len(f.keyframe_points)) for f in o.animation_data.action.fcurves])
 if o.data.animation_data and o.data.animation_data.action:print('DATA',[(f.data_path,len(f.keyframe_points)) for f in o.data.animation_data.action.fcurves])
for m in bpy.data.objects['Copper_bullet'].data.materials:
 print(m.name,[(n.name,n.inputs['Base Color'].is_linked) for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'])
print('COMPOSITOR',s.use_nodes,[(n.name,n.type) for n in s.node_tree.nodes] if s.node_tree else '')
