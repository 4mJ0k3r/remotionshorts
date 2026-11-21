import bpy,json
from pathlib import Path
out=[]
for o in bpy.context.scene.objects:
 if any(x in o.name.lower() for x in ['challenger','eddie','gun','pearl','holster','bullet','grip','sweat','silhouette','ink','muzzle']):out.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'children':[c.name for c in o.children],'bounds':[list(v) for v in o.bound_box],'set_ink':o.get('set_ink'),'mats':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else []})
Path('D:/remotionshorts/renders/slow_eddie_v7/scene_inventory.json').write_text(json.dumps(out,indent=2))
print([(o['name'],o['parent']) for o in out])
