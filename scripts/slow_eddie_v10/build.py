import bpy,math,sys,ast
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v10';s=bpy.context.scene;O=bpy.data.objects
bpy.app.handlers.frame_change_post.clear();bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v10.blend'))
sys.path.insert(0,str(R/'scripts/washroom_experiment'));from sets import rgb
sys.path.insert(0,str(R/'tools/V9_Parity_Packet/V9_Parity_Packet'));import v9_patch_helpers as H
ink=bpy.data.materials['V7 thin warm ink'];black=bpy.data.materials['V7 matte limb ink'];cream=bpy.data.materials['V9 skin'];brown=bpy.data.materials['V7 dark hatband']
tree=ast.parse((R/'scripts/slow_eddie_v7/build.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),'constructors','exec'))
for n in ink.node_tree.nodes:
 if n.type=='EMISSION':n.inputs[0].default_value=H.rgba('#16121C')
for who in ['challenger','eddie']:
 for o in list(O):
  if o.name.startswith('V7 '+who) and 'skull' in o.name and not o.get('v7_outline'):
   for v in o.data.vertices:v.co.x*=1.05
   tex=bpy.data.textures.new('V10 '+who+' organic contour',type='CLOUDS');tex.noise_scale=.35;tex.noise_depth=1
   for ob in [o]+[c for c in o.children if c.get('v7_outline')]:
    mod=ob.modifiers.new('Stable hand drawn contour','DISPLACE');mod.texture=tex;mod.texture_coords='LOCAL';mod.strength=.010;mod.mid_level=.5
for o in O:
 if ('hand' in o.name.lower() or 'finger' in o.name.lower()) and o.type=='MESH' and not o.get('v7_outline'):
  o.data.materials.clear();o.data.materials.append(black)
for n in black.node_tree.nodes:
 if n.type=='BSDF_PRINCIPLED':n.inputs['Base Color'].default_value=H.rgba('#2B2438')
steel=H.metal('V10 charcoal steel','#232A38',.85,.25);O['Challenger_revolver'].data.materials.clear();O['Challenger_revolver'].data.materials.append(steel)
mr=cream.node_tree.nodes.get('V9 calibrated light interval');mr.inputs['From Min'].default_value=.33;mr.inputs['From Max'].default_value=.78
for name in ['V7 eddie curved brim','V7 eddie curved brim ink']:
 if name in O:
  for v in O[name].data.vertices:
   if v.co.y<0:v.co.y*=1.18;v.co.z-=.012
# Smirk and five overlapping rounded moustache lobes; all conform to the existing face.
faceline('V10 cocky smirk',[(-.08,-.125),(-.025,-.145),(.035,-.14),(.09,-.105)],.008,O['V7 challenger head pivot'])
for o in list(O):
 if 'moustache' in o.name or 'mustache' in o.name:bpy.data.objects.remove(o,do_unlink=True)
for i in range(5):
 x=(i-2)*.048;sphere('V10 rounded mustache lobe',(x,-.288,-.115+abs(i-2)*.003),(.033,.025,.029),brown,O['V7 eddie head pivot'],inkwidth=0)
st=O['V7 eddie mouth straw'];st.data.bevel_depth=.009
for dz in [-.008,.008]:curve('V10 frayed straw',[(.22,-.235,-.17),(.27,-.215,-.18+dz)],.0035,st.data.materials[0],O['V7 eddie head pivot'])
t=bpy.data.texts.new('slow_eddie_v10_runtime.py');t.from_string((R/'scripts/slow_eddie_v10/runtime.py').read_text());exec(compile(t.as_string(),t.name,'exec'));s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v10.blend'))
