"""Read-only final checks on saved V4; never executes the authoring module."""
import ast,bpy,json,hashlib
from pathlib import Path
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
source=Path(r'D:\remotionshorts\scripts\hair_sensor\v4_polish.py').read_text()
tree=ast.parse(source);names={'animations','stable_value','properties','node_tree','invariant_snapshot','digest'}
subset=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
ns={'bpy':bpy,'json':json,'hashlib':hashlib,'ROWS':json.loads((OUT/'shots_v4.json').read_text())['shots']}
exec(compile(subset,'v4_invariant_functions','exec'),ns)
current=ns['digest'](ns['invariant_snapshot']());original=json.loads((OUT/'v4_invariants.json').read_text())['before_sha256']
report={'unchanged':current==original,'v3_protected_sha256':original,'v4_protected_sha256':current}
(OUT/'v4_final_invariants.json').write_text(json.dumps(report,indent=2));print('FINAL_PROTECTED_FIELDS',report,flush=True)
assert report['unchanged'],'Protected fields differ from V3'
checks=Path(r'D:\remotionshorts\scripts\hair_sensor\v4_verify_render.py').read_text().split("\nfull='--full'")[0]
exec(compile(checks,'v4_contact_checks_only','exec'))
