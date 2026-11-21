import bpy,sys,math
from pathlib import Path
import hashlib,json
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v6';s=bpy.context.scene;bpy.app.handlers.frame_change_post.clear()
sys.path.insert(0,str(R/'scripts/inside_brain_dog'));from build_inside_brain_dog import cel_material
sys.path.insert(0,str(R/'scripts/washroom_experiment'));from sets import rgb
def town_hash():
 names=('Downloaded Western saloon','Quaternius','Porch timber','Porch railing','V5 layered cloud','Red sandstone','Mesa horizontal','Dusty Main Street','GN sidewalk','Grass instance','Painted Western sign','Sign ')
 data=[]
 for o in sorted([o for o in s.objects if o.name.startswith(names)],key=lambda o:o.name):
  geometry=([list(v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons]) if o.type=='MESH' else str(o.type)
  data.append((o.name,[list(row) for row in o.matrix_world],geometry))
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
before_town=town_hash()
# Town geometry, placement and imported assets are intentionally untouched.
for name in ['Eddie thigh holster strap']:
 if name in bpy.data.objects:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
for who in ['challenger','eddie']:
 m=cel_material('V6 '+who+' clean torso',P/'art'/f'{who}_body.png');bpy.data.objects[who+'_body'].data.materials[0]=m
 if who=='challenger':
  nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');src=out.inputs['Surface'].links[0].from_socket;tr=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader');mix.name='V3 shoulder fade';mix.inputs[0].default_value=1;nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(src,mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs[0])
m=cel_material('V6 challenger downstreet gaze',P/'art/challenger_gaze.png');m.use_fake_user=True
def emission(name,color,strength=.95):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(*rgb(color),1);em.inputs[1].default_value=strength;nt.links.new(em.outputs[0],out.inputs[0]);return m
for who in ['challenger','eddie']:
 me=bpy.data.meshes.new('Clean continuous vector arms');me.from_pydata([(0,0,0)]*(2*(66+24)),[],[(base+2*i,base+2*i+1,base+2*i+3,base+2*i+2) for base in [0,90] for i in range(32)]+[tuple(range(base+66,base+90)) for base in [0,90]])
 o=bpy.data.objects.new('V6 '+who+' continuous arms',me);s.collection.objects.link(o);me.materials.append(emission('V6 '+who+' solid arm ink','251c20'));me.materials.append(emission('V6 '+who+' hand cream','fdfaf2'))
 for p in me.polygons:p.material_index=int(len(p.vertices)==24)
 if who=='challenger':
  for m in me.materials:
   nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');src=out.inputs['Surface'].links[0].from_socket;tr=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader');mix.name='V3 prop fade';mix.inputs[0].default_value=1;nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(src,mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs[0])
# Protected cel paint under Standard; brightness no longer comes from overexposed diffuse.
for m in bpy.data.materials:
 if m.use_nodes and any(n.type=='TEX_IMAGE' and n.image and any(k in n.image.name for k in ['head','blink','body']) for n in m.node_tree.nodes):
  for n in m.node_tree.nodes:
   if n.type=='EMISSION':n.inputs[1].default_value=.94
   if n.type=='MIX_SHADER' and not n.inputs[0].is_linked and n.name not in ['V3 shoulder fade','V3 prop fade']:n.inputs[0].default_value=1
# Material-only saturation edits; every existing town mesh and transform is preserved.
colors=['245dd0','b83d2f','d19d39','69442e']
from sets import rgb
for i,o in enumerate(sorted([o for o in s.objects if o.name.startswith('Downloaded Western saloon')],key=lambda o:(o.location.x,o.location.y))):
 for j,mat in enumerate(list(o.data.materials)):
  mat=mat.copy();o.data.materials[j]=mat
  if mat.use_nodes:
   for bs in [n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED']:
    source=bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].links else None
    if source:
     node=mat.node_tree.nodes.new('ShaderNodeMixRGB');node.blend_type='COLOR';node.inputs[0].default_value=.55;node.inputs[2].default_value=(*rgb(colors[i%4]),1);mat.node_tree.links.new(source,node.inputs[1]);mat.node_tree.links.new(node.outputs[0],bs.inputs['Base Color'])
for i,mat in enumerate(bpy.data.objects['Copper_bullet'].data.materials):
 if mat.use_nodes:
  for bs in [n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED']:
   color=(.95,.20,.025,1) if i==0 else (1,.52,.04,1);bs.inputs['Base Color'].default_value=color;bs.inputs['Emission Color'].default_value=color;bs.inputs['Emission Strength'].default_value=.45
for o in bpy.data.objects['Copper_bullet'].children_recursive:
 if 'cap' in o.name.lower() or 'rim' in o.name.lower():
  for mat in o.data.materials:
   if mat.use_nodes:
    for bs in [n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED']:bs.inputs['Base Color'].default_value=(.75,.48,.08,1);bs.inputs['Emission Color'].default_value=(1,.52,.04,1);bs.inputs['Emission Strength'].default_value=.45
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=-.25
sun=bpy.data.objects['Warm afternoon Sun'];sun.data.energy=2.;sun.data.color=rgb('ffe0af')
s.world.node_tree.nodes['Background'].inputs[0].default_value=(*rgb('3ba5ff'),1);s.world.node_tree.nodes['Background'].inputs[1].default_value=1.1
s.camera.data.dof.aperture_fstop=.85;s.eevee.taa_render_samples=16
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0] and not im.packed_file:im.pack()
after_town=town_hash();assert after_town==before_town;(P/'town_preservation.json').write_text(json.dumps({'before':before_town,'after':after_town,'unchanged':True},indent=2))
t=bpy.data.texts.load(str(R/'scripts/slow_eddie_v6/runtime.py'));t.name='slow_eddie_v6_runtime.py';exec(compile(t.as_string(),t.name,'exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v6.blend'))
