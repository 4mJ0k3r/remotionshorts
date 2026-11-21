# User reference override: illustrated 2D cast in dimensional mine/prop geometry.
# Rest artwork is shallow, camera-facing and stable. Contacts stay in world space.
flatSkin=emission('Illustrated cream face','#FFF6EC')
# Restrained painted edge accent, not broad spherical light wrap.
nt=flatSkin.node_tree;n=nt.nodes;l=nt.links;em=next(x for x in n if x.type=='EMISSION')
tex=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');ramp=n.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position=.02;ramp.color_ramp.elements[0].color=look.rgba('#E2DEEA')
ramp.color_ramp.elements[1].position=.19;ramp.color_ramp.elements[1].color=look.rgba('#FFF6EC');ramp.color_ramp.interpolation='EASE'
l.new(tex.outputs['Generated'],sep.inputs[0]);l.new(sep.outputs['X'],ramp.inputs[0]);l.new(ramp.outputs[0],em.inputs['Color'])
paint={
 'Flannel red':emission('Illustrated crimson flannel','#B82D24'),
 'Buddy teal':emission('Illustrated teal sweater','#1A888B'),
 'Knitted ochre':emission('Illustrated golden beanie','#E8A620'),
 'Weathered brown felt':emission('Illustrated brown hat','#A77B45'),
 'Cream suspenders':emission('Illustrated cream suspenders','#EBC995'),
 'Buddy dark fingers':emission('Illustrated dark glove','#2B2531'),
 'Dark soft boots':emission('Illustrated dark limbs','#211B29'),
 'Oiled gun walnut':emission('Illustrated brown garment details','#563927'),
 'Solid brass gold':emission('Illustrated brass trim','#E9B84D'),
}
for name in ['Miner','Buddy']:
 root=bpy.data.objects[name+' root'];head=bpy.data.objects[name+' head pivot']
 headSet={o.as_pointer() for o in [head]+list(head.children_recursive)}
 skull=bpy.data.objects[name+' rough-round head']
 for v in skull.data.vertices:v.co.y*=.12549
 skull.data.update()
 for o in root.children_recursive:
  if o.get('ricks_role')=='ink':continue
  if o.type in {'MESH','CURVE'}:
   for slot in o.material_slots:
    if slot.material==skin:slot.material=flatSkin
    elif slot.material and slot.material.name in paint:slot.material=paint[slot.material.name]
  # Compress clothing and its patterns together into a coherent shallow cel.
  if o.as_pointer() not in headSet and o.parent and o.parent!=root and 'hand frame' not in o.parent.name:
   if o.type=='MESH':
    for v in o.data.vertices:v.co.y*=.25
    o.location.y*=.25;o.data.update()
   elif o.type=='CURVE':
    for sp in o.data.splines:
     for p in sp.points:p.co.y*=.25
    o.location.y*=.25
 # Rebuild shallow hulls from the updated artwork before runtime captures rest data.
 for h in root.children_recursive:
  if not h.get('ink_base_width'):continue
  source=h.parent;source.data.update()
  if len(h.data.vertices)==len(source.data.vertices):
   for v,base in zip(h.data.vertices,source.data.vertices):v.co=base.co+base.normal*h['ink_base_width']
   h.data.update()
S['cast_style']='Illustrated 2D shallow cels / camera-facing heads / flat paint / restrained edge accent; dimensional world and props'
