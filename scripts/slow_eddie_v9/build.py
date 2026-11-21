import bpy,math,sys,ast,json,hashlib
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v9';K=R/'tools/V9_Parity_Packet/V9_Parity_Packet';s=bpy.context.scene;O=bpy.data.objects;bpy.app.handlers.frame_change_post.clear()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v9.blend'))
sys.path.insert(0,str(K));import v9_patch_helpers as H
sys.path.insert(0,str(R/'scripts/washroom_experiment'));from sets import rgb
ink=bpy.data.materials['V7 thin warm ink'];black=bpy.data.materials['V7 matte limb ink'];cream=bpy.data.materials['V7 light responsive cream'];hatTan=bpy.data.materials['V7 tan felt hat'];brown=bpy.data.materials['V7 warm leather'];steel=bpy.data.materials['V7 dark gunmetal']
tree=ast.parse((R/'scripts/slow_eddie_v7/build.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),'constructors','exec'))
H.configure_scene(s,1080);s.eevee.taa_render_samples=24;s.eevee.shadow_pool_size='128';H.make_world(s)
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
H.install_lights(s);H.install_post(s)
# Correct verified world-ray sign for this scene's sky while keeping supplied stop values.
nt=s.world.node_tree;sep=next(n for n in nt.nodes if n.type=='SEPXYZ');ramp=next(n for n in nt.nodes if n.type=='VALTORGB');neg=nt.nodes.new('ShaderNodeMath');neg.operation='MULTIPLY';neg.inputs[1].default_value=-1;nt.links.new(sep.outputs['Z'],neg.inputs[0]);nt.links.new(neg.outputs[0],ramp.inputs[0])
toons={}
for key in H.PALETTES:
 m=H.clean_toon('V9 '+key,key);nt=m.node_tree;ramp=next(n for n in nt.nodes if n.type=='VALTORGB');src=ramp.inputs[0].links[0].from_socket;mr=nt.nodes.new('ShaderNodeMapRange');mr.name='V9 calibrated light interval';mr.inputs['From Min'].default_value=.22;mr.inputs['From Max'].default_value=.90;mr.clamp=True;nt.links.new(src,mr.inputs['Value']);nt.links.new(mr.outputs[0],ramp.inputs[0]);toons[key]=m
mapping={'V7 light responsive cream':'skin','V7 scarlet shirt':'red','V7 turquoise shirt':'teal','V7 warm leather':'vest'}
for o in list(O):
 if o.type not in ['MESH','CURVE']:continue
 for i,m in enumerate(o.data.materials):
  if m and m.name in mapping:o.data.materials[i]=toons[mapping[m.name]]
 for mod in o.modifiers:
  if mod.type=='SUBSURF':mod.render_levels=min(1,mod.render_levels)
# Actual material road albedo, no blue-shadow emission override.
road=O['Dusty Main Street'];mat=H.metal('V9 warm sand','#D7B78A',0,.92);nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=.7;tex.inputs['Detail'].default_value=1;mr=nt.nodes.new('ShaderNodeMapRange');mr.inputs['To Min'].default_value=.90;mr.inputs['To Max'].default_value=1.08;nt.links.new(tex.outputs['Fac'],mr.inputs['Value']);mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=H.rgba('#D7B78A');nt.links.new(mr.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],bs.inputs['Base Color']);road.data.materials.clear();road.data.materials.append(mat)
for o in O:
 if o.name.startswith('Downloaded Western saloon'):
  for i,m in enumerate(o.data.materials):
   m=m.copy();o.data.materials[i]=m
   for bs in [n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']:
    base=bs.inputs['Base Color'];src=base.links[0].from_socket if base.links else None
    if src:
     mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='COLOR';mix.inputs[0].default_value=.70;mix.inputs[2].default_value=H.rgba('#41669C' if o.location.x<0 else '#B89B76');m.node_tree.links.new(src,mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],base)
 if o.name.startswith(('Red sandstone','Mesa horizontal')):
  for m in o.data.materials:
   if m.use_nodes:
    for bs in [n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']:bs.inputs['Base Color'].default_value=H.rgba('#8C3D37')
gunmat=H.metal('V9 gun','#34425B',.85,.28);gold=H.metal('V9 rosette gold','#E9C777',.8,.30);copper=H.metal('V9 copper','#E5A16B',.75,.26);glove=shader('V9 gloves','2B2438',0,.9,False)
for name in ['Challenger_revolver','Eddie_pearl_revolver']:
 O[name].data.materials.clear();O[name].data.materials.append(gunmat)
for o in O:
 if 'hand' in o.name or 'curled finger' in o.name:
  if o.type=='MESH' and not o.get('v7_outline'):o.data.materials.clear();o.data.materials.append(glove)
# Calibrated lighting contrast still derives entirely from real received light/shadow.
m=toons['skin'];nt=m.node_tree;mr=nt.nodes.get('V9 calibrated light interval');source=mr.inputs['Value'].links[0].from_socket;contrast=nt.nodes.new('ShaderNodeMath');contrast.operation='MULTIPLY_ADD';contrast.inputs[1].default_value=2.8;contrast.inputs[2].default_value=-1.2;nt.links.new(source,contrast.inputs[0]);nt.links.new(contrast.outputs[0],mr.inputs['Value'])
for name in ['V7 pearl revolver butt','V7 eddie holster root','V8 revolver grip seat']:
 O[name].location.x+=.10
for i in range(2):curve('V9 barrel highlight',[(.02,-.025,.245+i*.008),(.32,-.025,.245+i*.008)],.0015,cream,O['Challenger_revolver'])
# Narrow cloth silhouette without scaling skull, hats, root rig or legs.
for o in O:
 if o.name.startswith(('V7 challenger tailored shirt','V7 eddie tailored shirt','V8 smooth fitted lapel','V8 rounded lapel')):
  if o.type=='MESH':
   for v in o.data.vertices:v.co.x*=.80
# Short cartridge marks replace pinstripes.
for o in list(O):
 if o.name.startswith('V7 challenger woven red stripe'):bpy.data.objects.remove(o,do_unlink=True)
for i in range(9):
 x=-.18+i*.045;curve('V9 chest cartridge',[(x,-.178,1.40),(x,-.178,1.33)],.006,hatTan,O['V7 challenger torso'])
# Circular 12-lobe buckle instead of rectangular plate.
for who in ['challenger','eddie']:
 for o in list(O):
  if o.name.startswith('V7 '+who) and any(k in o.name for k in ['buckle','brass buckle']):
   if o.name in O:bpy.data.objects.remove(o,do_unlink=True)
 pts=[]
 for i in range(96):a=i*math.tau/96;r=.065*(1+.08*math.cos(12*a));pts.append((r*math.cos(a),-.245,.94+r*math.sin(a)))
 disc=mesh('V9 '+who+' rosette',pts,[tuple(range(96))],gold,O['V7 '+who+' torso'],0,False);mod=disc.modifiers.new('Metal thickness','SOLIDIFY');mod.thickness=.014;sphere('V9 '+who+' medallion',(0,-.259,.94),(.028,.009,.028),gold,O['V7 '+who+' torso'],24,12,.002)
for i in range(3):sphere('V9 vest button',(0,-.215,1.08+i*.13),(.018,.009,.018),gold,O['V7 eddie torso'],16,8,.002)
# Retention straps over the actual sheath; ivory crosshatch follows the grip local surface.
h=O['V7 eddie holster root']
for z in [-.06,.065]:cube('V9 retention strap',(0,-.137,z),(.21,.009,.025),black,h,.004)
grip=O['V7 pearl revolver butt'];mat=H.metal('V9 ivory','#E6E0CF',0,.55);grip.data.materials.clear();grip.data.materials.append(mat)
for i in range(-3,4):
 curve('V9 grip crosshatch',[(i*.008-.015,-.025,-.03),(i*.008+.015,-.025,.03)],.0007,hatTan,grip)
# Refined rounded moustache and three-segment straw.
for o in list(O):
 if o.name.startswith('V7 eddie mustache'):bpy.data.objects.remove(o,do_unlink=True)
coords=[(-.13,.0),(-.10,.025),(-.04,.03),(0,.025),(.05,.03),(.10,.02),(.13,0)]
for i in range(31):x=.13-.26*i/30;coords.append((x,-.025-.015*(.5+.5*math.cos((x+.13)/.26*5*math.tau))))
patch('V9 rounded moustache',[(x,z-.105) for x,z in coords],brown,O['V7 eddie head pivot'],.010)
straw=O['V7 eddie mouth straw'];sp=straw.data.splines[0];straw.data.splines.clear();sp=straw.data.splines.new('POLY');sp.points.add(3)
for p,co in zip(sp.points,[(-.02,-.285,-.132),(.10,-.28,-.14),(.19,-.26,-.16),(.25,-.22,-.173)]):p.co=(*co,1)
for o in list(O):
 if o.name.startswith('V7 challenger open pupil') or o.name.startswith('V7 challenger tooth separator'):bpy.data.objects.remove(o,do_unlink=True)
for x in [-.131,.121]:oval('V9 narrowed pupil',x,.036,.031,.023,black,O['V7 challenger head pivot'])
for x in [-.034,.024]:faceline('V9 grin separator',[(x,-.148),(x,-.109)],.003,O['V7 challenger head pivot'])
# Projectiles: side-view 2.2:1 copper slug; original source remains intact.
b=O['Copper_bullet']
for v in b.data.vertices:v.co.y*=.66
for ch in b.children:
 if ch.type=='MESH':
  for v in ch.data.vertices:v.co.y*=.66
b.data.materials.clear();b.data.materials.append(copper)
for p in b.data.polygons:p.material_index=0
# Ink shells: preserve rough drawing contours, adjust thickness from source surfaces.
for o in list(O):
 if o.get('v7_outline') and o.parent and o.parent.type=='MESH' and len(o.data.vertices)==len(o.parent.data.vertices):
  for v,p in zip(o.data.vertices,o.parent.data.vertices):v.co=p.co+p.normal*.008
  o.visible_shadow=False
for n in ink.node_tree.nodes:
 if n.type=='EMISSION':n.inputs[0].default_value=H.rgba('#292337')
# Smaller irregular twig assembly, twelve existing branches only.
tw=O['Rolling_tumbleweed'];tw.scale=(.55,)*3
for i,o in enumerate(tw.children):
 if o.type=='CURVE':o.hide_render=i>=12;o['v9_branch']=i<12;o.data.bevel_depth=.003
# Restrict background shadow casters while preserving key shadows on cast and near props.
for o in O:
 if o.name.startswith(('Downloaded Western','Porch timber','Porch railing')):
  o.visible_shadow=False
  for m in o.data.materials:
   if hasattr(m,'shadow_method'):m.shadow_method='NONE'
# Light-driven road grade: retain specified Principled albedo/noise and localize cool shadows.
nt=road.data.materials[0].node_tree;l=nt.links;out=nt.nodes.get('Material Output');bs=nt.nodes.get('Principled BSDF');diff=nt.nodes.new('ShaderNodeBsdfDiffuse');diff.inputs[0].default_value=(1,1,1,1);st=nt.nodes.new('ShaderNodeShaderToRGB');l.new(diff.outputs[0],st.inputs[0]);bw=nt.nodes.new('ShaderNodeRGBToBW');l.new(st.outputs[0],bw.inputs[0]);ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.50;ramp.color_ramp.elements[0].color=H.rgba('#616391');ramp.color_ramp.elements[1].position=1.40;ramp.color_ramp.elements[1].color=H.rgba('#D3AC83');l.new(bw.outputs[0],ramp.inputs[0]);em=nt.nodes.new('ShaderNodeEmission');l.new(ramp.outputs[0],em.inputs[0]);l.new(em.outputs[0],out.inputs[0])
focus=O['V7 hero focus'];H.configure_camera(s.camera,focus,35,2)
text=bpy.data.texts.load(str(R/'scripts/slow_eddie_v9/runtime.py'));text.name='slow_eddie_v9_runtime.py';exec(compile(text.as_string(),text.name,'exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v9.blend'))
bpy.app.handlers.frame_change_post.clear();s.camera.animation_data_clear();s.camera.data.animation_data_clear();samples=[]
for frame in range(1,301):
 s.frame_current=frame;plan(s);samples.append((frame,s.camera.location.copy(),s.camera.rotation_quaternion.copy(),s.camera.data.lens,s.camera.data.shift_x,s.camera.data.shift_y))
H.bake_channel(s.camera,'location',0,1,20,samples[0][1].x,samples[19][1].x,H.ease5)
for frame,loc,rot,lens,sx,sy in samples:
 s.camera.location=loc;s.camera.rotation_quaternion=rot;s.camera.data.lens=lens;s.camera.data.shift_x=sx;s.camera.data.shift_y=sy;s.camera.keyframe_insert(data_path='location',frame=frame);s.camera.keyframe_insert(data_path='rotation_quaternion',frame=frame)
 for path in ['lens','shift_x','shift_y']:s.camera.data.keyframe_insert(data_path=path,frame=frame)
for data in [s.camera,s.camera.data]:
 for fc in data.animation_data.action.fcurves:
  for key in fc.keyframe_points:key.interpolation='LINEAR'
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v9.blend'))
(P/'build_parameters.json').write_text(json.dumps({'source':'../slow_eddie_v8/slow_eddie_v8.blend','samples':24,'packet':str(K),'palette_light_map':[.22,.90],'performance_verified':False,'parity_certified':False},indent=2));print('V9 BUILD OK')
