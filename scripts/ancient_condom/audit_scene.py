import bpy,json
from pathlib import Path
out={}
out['material_shadow_controls']=[p.identifier for p in bpy.types.Material.bl_rna.properties if 'shadow' in p.identifier or 'culling' in p.identifier]
for name in ['AC_01','AC_03','AC_18']:
 s=bpy.data.scenes[name];out[name]={'eevee':{p.identifier:str(getattr(s.eevee,p.identifier)) for p in s.eevee.bl_rna.properties if 'shadow' in p.identifier or 'bokeh' in p.identifier},'lights':[{p.identifier:str(getattr(o.data,p.identifier)) for p in o.data.bl_rna.properties if 'shadow' in p.identifier or p.identifier in ['energy','type']} for o in s.objects if o.type=='LIGHT']}
Path(r'D:\remotionshorts\renders\ancient_condom\qa\scene_settings.json').write_text(json.dumps(out,indent=2))
