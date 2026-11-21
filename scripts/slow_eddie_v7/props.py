import bpy
m=bpy.data.materials['V7 thin warm ink'];print('INK_PROPS',[(p.identifier,str(getattr(m,p.identifier))) for p in m.bl_rna.properties if any(w in p.identifier for w in ['shadow','backface','surface'])]);print('SHADOW_OBJ',[p.identifier for p in bpy.types.Object.bl_rna.properties if 'shadow' in p.identifier])
