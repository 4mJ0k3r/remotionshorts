import bpy
for o in bpy.context.scene.objects:
 if o.name.startswith('V8 smooth fitted lapel'):print('PANEL',o.name,len(o.data.vertices),len(o.data.polygons),[(m.type,m.name) for m in o.modifiers])
light=bpy.data.objects['Warm afternoon Sun'].data
print('SHADOWS',[(p.identifier,str(getattr(light,p.identifier))) for p in light.bl_rna.properties if 'shadow' in p.identifier])
