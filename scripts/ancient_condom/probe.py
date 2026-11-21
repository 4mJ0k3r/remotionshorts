import bpy,json
from pathlib import Path
s=bpy.context.scene
data={'version':bpy.app.version_string,'render_motion':[p.identifier for p in s.render.bl_rna.properties if 'motion_blur' in p.identifier],'eevee_motion':[p.identifier for p in s.eevee.bl_rna.properties if 'motion' in p.identifier]}
font=bpy.data.fonts.load(r'D:\remotionshorts\renders\ancient_condom\assets\Chinese.ttc');data['chinese_font']=font.name
Path(r'D:\remotionshorts\renders\ancient_condom\probe.json').write_text(json.dumps(data,indent=2));print(data,flush=True)
