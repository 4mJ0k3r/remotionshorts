import bpy,sys,ast,math
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v13';s=bpy.context.scene;O=bpy.data.objects
sys.path.insert(0,str(R/'tools/V9_Parity_Packet/V9_Parity_Packet'));import v9_patch_helpers as H
sys.path.insert(0,str(R/'scripts/washroom_experiment'));from sets import rgb
ink=bpy.data.materials['V7 thin warm ink'];black=bpy.data.materials['V7 matte limb ink'];cream=bpy.data.materials['V9 skin'];tree=ast.parse((R/'scripts/slow_eddie_v7/build.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),'constructors','exec'))
m=H.metal('V13 pearl diamond hatch','#A58F76',0,.85)
for i in range(-2,3):curve('V13 reverse grip hatch',[(i*.008-.015,-.026,.03),(i*.008+.015,-.026,-.03)],.00055,m,O['V7 pearl revolver butt'])
t=bpy.data.texts['slow_eddie_v13_runtime.py'];t.from_string((R/'scripts/slow_eddie_v13/runtime.py').read_text());exec(compile(t.as_string(),t.name,'exec'));s.frame_set(1);update(s);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v13.blend'))
