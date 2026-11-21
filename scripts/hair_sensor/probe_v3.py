import bpy,json
from pathlib import Path
s=bpy.context.scene
keys=[p.identifier for p in s.eevee.bl_rna.properties]
data={'version':bpy.app.version_string,'eevee_properties':keys,'gi':{k:str(getattr(s.eevee,k)) for k in keys if 'gi' in k or 'ao' in k},'light_properties':[p.identifier for p in bpy.data.lights.new('Probe','AREA').bl_rna.properties]}
Path(r'D:\remotionshorts\renders\hair_sensor\v3_api.json').write_text(json.dumps(data,indent=2))
print(json.dumps(data),flush=True)
