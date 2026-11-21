import bpy,sys,math,random,json
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v5';s=bpy.context.scene;bpy.app.handlers.frame_change_post.clear()
sys.path.insert(0,str(R/'scripts/washroom_experiment'));sys.path.insert(0,str(R/'scripts/inside_brain_dog'));from sets import Stage,rgb
from build_inside_brain_dog import cel_material,card
G=Stage(s);random.seed(53)
# Proportions: .77m painted skull / .64m shoulders =1.20; height including hat~2.3m.
for who in ['challenger','eddie']:
 o=bpy.data.objects[who+'_body'];o.data.materials[0]=cel_material('V5 '+who+' body',P/'art'/f'{who}_body.png')
 for kind in ['head','blink']:
  m=cel_material('V5 '+who+' '+kind,P/'art'/f'{who}_{kind}.png');m.use_fake_user=True
 bpy.data.objects[who+'_head'].scale=(1.1/1.53,)*3
bpy.data.objects['Eddie mouth-anchored straw'].scale=(1.1/1.53,)*3
bpy.data.objects['Eddie left black holster'].scale=(.68,.68,.68)
for m in list(bpy.data.materials):
 if m.name.startswith('V5 challenger') and m.use_nodes:
  nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');src=out.inputs['Surface'].links[0].from_socket;tr=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader');mix.name='V3 shoulder fade';mix.inputs[0].default_value=1;nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(src,mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs[0])
# Vector-flat tapered legs replace raster limb edges in close-ups; no cylinder shells.
inkleg=G.mat('352329',em=.65)
for who in ['challenger','eddie']:
 body=bpy.data.objects[who+'_body'];vs=[];fs=[]
 for a,b,c in [((450,678),(421,815),(402,972)),((565,678),(579,835),(598,972))]:
  offset=len(vs)
  for i in range(33):
   t=i/32;x=(1-t)**2*a[0]+2*(1-t)*t*b[0]+t*t*c[0];y=(1-t)**2*a[1]+2*(1-t)*t*b[1]+t*t*c[1];dx=2*(1-t)*(b[0]-a[0])+2*t*(c[0]-b[0]);dy=-2*(1-t)*(b[1]-a[1])-2*t*(c[1]-b[1]);n=V((-dy,dx,0)).normalized();center=V(((x/1024-.5)*2.3,(.5-y/1024)*2.3,-.003));w=.033*(1-t)+.019*t;vs.extend([tuple(center+n*w),tuple(center-n*w)])
  for i in range(32):k=offset+2*i;fs.append((k,k+1,k+3,k+2))
  # Flat supported sole silhouette.
  center=V(((c[0]/1024-.5)*2.3,(.5-c[1]/1024)*2.3,-.003));k=len(vs)
  for i in range(24):a=i*math.tau/24;vs.append(tuple(center+V((.06*math.cos(a),.024*math.sin(a),0))))
  fs.append(tuple(range(k,k+24)))
 me=bpy.data.meshes.new('Vector tapered leg ribbons');me.from_pydata(vs,[],fs);o=G.link('V5 '+who+' flat vector legs',me,body);legmat=inkleg.copy() if who=='challenger' else inkleg;me.materials.append(legmat)
 if who=='challenger':
  legmat.name='V5 challenger leg fade';nt=legmat.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');src=out.inputs['Surface'].links[0].from_socket;tr=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader');mix.name='V3 shoulder fade';mix.inputs[0].default_value=1;nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(src,mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs[0])
# Flush thigh strap links the slim sheath to Eddie's supported leg.
strap=G.curve('Eddie thigh holster strap',[(-.37,-.60,.002),(-.25,-.60,.002),(-.13,-.60,.002)],.012,G.mat('62402b',em=.5),bpy.data.objects['eddie_body']);strap.data.bevel_resolution=0
# Reset town to the downloaded stylized saloon geometry + original authored materials.
poses=[]
for o in list(s.objects):
 if o.name.startswith('saloon') and o.type=='MESH':poses.append((tuple(o.location),tuple(o.rotation_euler),o.scale.z));bpy.data.objects.remove(o,do_unlink=True)
 elif o.name.startswith(('Batched architectural','Pitched saloon roof','False-front stepped parapet')):bpy.data.objects.remove(o,do_unlink=True)
def asset(name,path,size,cap=1600):
 before=set(s.objects);bpy.ops.import_scene.gltf(filepath=str(path));new=list(set(s.objects)-before);meshes=[o for o in new if o.type=='MESH'];bpy.context.view_layer.update();points=[o.matrix_world@V(v) for o in meshes for v in o.bound_box];lo=V([min(v[i] for v in points) for i in range(3)]);hi=V([max(v[i] for v in points) for i in range(3)]);scale=size/max(hi-lo);center=V(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
 for o in meshes:
  mat=o.matrix_world.copy();o.parent=None
  for v in o.data.vertices:v.co=(mat@v.co-center)*scale
  o.matrix_world=Matrix.Identity(4)
 bpy.ops.object.select_all(action='DESELECT')
 for o in meshes:o.select_set(True)
 bpy.context.view_layer.objects.active=meshes[0]
 if len(meshes)>1:bpy.ops.object.join()
 result=bpy.context.object
 for o in new:
  try:
   if o!=result and o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
  except ReferenceError:pass
 result.name=name;tri=sum(len(p.vertices)-2 for p in result.data.polygons)
 if tri>cap:
  mod=result.modifiers.new('VRAM sanitation','DECIMATE');mod.ratio=cap/tri;bpy.context.view_layer.objects.active=result;bpy.ops.object.modifier_apply(modifier=mod.name)
 return result
base=asset('Downloaded Western saloon',R/'renders/slow_eddie/assets/saloon.glb',7,2400)
for i,(loc,rot,height) in enumerate(poses):
 o=base if i==0 else base.copy()
 if i:s.collection.objects.link(o)
 o.data=base.data.copy();o.location=loc;o.rotation_euler=rot;o.scale.z=height;o['set_ink']=abs(loc[1])<8
 # Tint original material texture, retaining wood-plank color and recess detail.
 tint=[(1,.87,.72),(.85,.95,1.15),(1.1,.75,.61),(.80,.85,.65)][i%4]
 for j,m in enumerate(list(o.data.materials)):
  m=m.copy();o.data.materials[j]=m
  if m.use_nodes:
   for node in m.node_tree.nodes:
    if node.type=='BSDF_PRINCIPLED':
     node.inputs['Roughness'].default_value=.82
     if node.inputs['Base Color'].links:
      source=node.inputs['Base Color'].links[0].from_socket;mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.42;mix.inputs[2].default_value=(*tint,1);m.node_tree.links.new(source,mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],node.inputs['Base Color'])
 # Connected porch railing / hitching beams, narrow enough to preserve entrances.
 side=1 if loc[0]>0 else -1
 for dy in [-2.1,2.1]:
  for z in [.6,1.05]:G.rod('Porch timber rail',(side*2.9,loc[1]+dy-.55,z),(side*2.9,loc[1]+dy+.55,z),.035,G.mat('765238'))
  for offset in [-.55,.55]:G.rod('Porch railing stake',(side*2.9,loc[1]+dy+offset,.1),(side*2.9,loc[1]+dy+offset,1.12),.045,G.mat('68472e'))
barrel=asset('Quaternius CC0 wooden keg',P/'assets/barrel.glb',.72,700);crate=asset('Quaternius CC0 crate',P/'assets/crate.glb',.65,650)
for m in crate.data.materials:
 if m and m.use_nodes:
  for n in m.node_tree.nodes:
   if n.type=='BSDF_PRINCIPLED':
    n.inputs['Base Color'].default_value=(*rgb('98633e'),1);n.inputs['Roughness'].default_value=.9
for i in range(12):
 for source,offset in [(barrel,0),(crate,.9)]:
  o=source if i==0 else source.copy()
  if i:s.collection.objects.link(o)
  o.location=((-1 if i%2 else 1)*(2.1+offset*.3),-2+i*2.7+offset,.015);o['set_ink']=i<3
# Dirt with broad ochre variation, broken wheel ruts and subtle microbump.
road=bpy.data.objects['Dusty Main Street'];m=G.mat('c49b62',rough=.96);road.data.materials.clear();road.data.materials.append(m);nt=m.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');tc=nt.nodes.new('ShaderNodeTexCoord');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.7;noise.inputs['Detail'].default_value=3;nt.links.new(tc.outputs['Object'],noise.inputs['Vector']);ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.17;ramp.color_ramp.elements[0].color=(*rgb('987044'),1);ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(*rgb('dbb97b'),1);nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(tc.outputs['Object'],sep.inputs[0]);mask=None
for x in [-.9,-.75,.75,.9]:
 sub=nt.nodes.new('ShaderNodeMath');sub.operation='SUBTRACT';nt.links.new(sep.outputs['X'],sub.inputs[0]);sub.inputs[1].default_value=x;ab=nt.nodes.new('ShaderNodeMath');ab.operation='ABSOLUTE';nt.links.new(sub.outputs[0],ab.inputs[0]);band=nt.nodes.new('ShaderNodeMath');band.operation='LESS_THAN';band.inputs[1].default_value=.045;nt.links.new(ab.outputs[0],band.inputs[0])
 if mask is None:mask=band.outputs[0]
 else:
  add=nt.nodes.new('ShaderNodeMath');add.operation='MAXIMUM';nt.links.new(mask,add.inputs[0]);nt.links.new(band.outputs[0],add.inputs[1]);mask=add.outputs[0]
strength=nt.nodes.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.21;nt.links.new(mask,strength.inputs[0]);mix=nt.nodes.new('ShaderNodeMixRGB');nt.links.new(strength.outputs[0],mix.inputs[0]);nt.links.new(ramp.outputs[0],mix.inputs[1]);mix.inputs[2].default_value=(*rgb('7f603d'),1);nt.links.new(mix.outputs[0],bs.inputs['Base Color']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.035;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],bs.inputs['Normal'])
# Actual Geometry Nodes curb pebble instancing, isolated to strips at road edges.
me=bpy.data.meshes.new('Curb scatter strips');me.from_pydata([(-2.35,-5,.03),(-1.85,-5,.03),(-1.85,34,.03),(-2.35,34,.03),(1.85,-5,.03),(2.35,-5,.03),(2.35,34,.03),(1.85,34,.03)],[],[(0,1,2,3),(4,5,6,7)]);curb=G.link('GN sidewalk pebbles and tufts',me);ng=bpy.data.node_groups.new('Western curb scatter','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');mod=curb.modifiers.new('Curb detail via Geometry Nodes','NODES');mod.node_group=ng;n=ng.nodes;l=ng.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');points=n.new('GeometryNodeDistributePointsOnFaces');points.inputs['Density'].default_value=3;l.new(inp.outputs[0],points.inputs['Mesh']);ico=n.new('GeometryNodeMeshIcoSphere');ico.inputs['Radius'].default_value=.04;ico.inputs[' subdivisions' if False else 'Subdivisions'].default_value=1;sm=n.new('GeometryNodeSetMaterial');sm.inputs['Material'].default_value=G.mat('8e704e');l.new(ico.outputs['Mesh'],sm.inputs[0]);inst=n.new('GeometryNodeInstanceOnPoints');l.new(points.outputs['Points'],inst.inputs['Points']);l.new(sm.outputs[0],inst.inputs['Instance']);rv=n.new('FunctionNodeRandomValue');rv.data_type='FLOAT_VECTOR';rv.inputs['Min'].default_value=(.5,.4,.4);rv.inputs['Max'].default_value=(1.5,1,1);l.new(rv.outputs['Value'],inst.inputs['Scale']);l.new(inst.outputs['Instances'],out.inputs[0])
# Grass tufts share the curb scatter graph as a second low-density instance stream.
mesh=bpy.data.meshes.new('Dry grass tuft prototype');mesh.from_pydata([(-.04,0,0),(0,0,.16),(.03,0,0),(0,-.04,0),(0,0,.12),(0,.04,0)],[],[(0,1,2),(3,4,5)]);tuft=G.link('Grass instance source',mesh);mesh.materials.append(G.mat('877443'));tuft.hide_render=True;info=n.new('GeometryNodeObjectInfo');info.inputs['Object'].default_value=tuft;info.inputs['As Instance'].default_value=True;grasspts=n.new('GeometryNodeDistributePointsOnFaces');grasspts.inputs['Density'].default_value=.6;grasspts.inputs['Seed'].default_value=23;l.new(inp.outputs[0],grasspts.inputs['Mesh']);gi=n.new('GeometryNodeInstanceOnPoints');l.new(grasspts.outputs['Points'],gi.inputs['Points']);l.new(info.outputs['Geometry'],gi.inputs['Instance']);join=n.new('GeometryNodeJoinGeometry');l.new(inst.outputs[0],join.inputs[0]);l.new(gi.outputs[0],join.inputs[0]);l.new(join.outputs[0],out.inputs[0])
# Layered flat cloud silhouettes instead of sphere clusters.
for o in list(s.objects):
 if o.name.startswith('V3 varied cloud'):bpy.data.objects.remove(o,do_unlink=True)
for j,(x,z,w) in enumerate([(-8,11,6),(-1,14,4),(6,12,7),(12,16,5)]):
 verts=[]
 for i in range(80):a=i*math.tau/80;r=1+.12*math.sin(5*a+j)+.06*math.cos(3*a);verts.append((math.cos(a)*w*.5*r,0,math.sin(a)*.8*r))
 me=bpy.data.meshes.new('Layered painted cloud');me.from_pydata(verts,[],[tuple(range(80))]);o=G.link('V5 layered cloud',me,xyz=(x,48,z));me.materials.append(G.mat('fff4db',em=.65));shade=o.copy();shade.data=o.data.copy();s.collection.objects.link(shade);shade.location+=(V((.2,.03,-.2)));shade.scale=(1,.98,.76);shade.data.materials.clear();shade.data.materials.append(G.mat('e2d2b8',em=.55))
sun=bpy.data.objects['Warm afternoon Sun'];sun.data.energy=2.5;sun.data.color=rgb('ffe0aa');sun.rotation_euler=V((.65,.35,-.85)).to_track_quat('-Z','Y').to_euler();sun.data.angle=.10
fill=bpy.data.objects['Subtle sky fill'];fill.data.energy=600;fill.data.color=rgb('f5d9af');fill.data.size=10;s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.15
focus=G.link('V5 hero focus target');s.camera.data.dof.focus_object=focus;s.camera.data.dof.aperture_fstop=2.0
# Glossy hero bullet and genuine metallic downloaded revolvers.
b=bpy.data.objects['Copper_bullet'];b.scale=(2.5,)*3
for i,m in enumerate(b.data.materials):
 if m and m.use_nodes:
  bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if bs:bs.inputs['Base Color'].default_value=(*((.8,.32,.12) if i==0 else (.65,.42,.08)),1);bs.inputs['Metallic'].default_value=.9;bs.inputs['Roughness'].default_value=.2;bs.inputs['Emission Color'].default_value=bs.inputs['Base Color'].default_value;bs.inputs['Emission Strength'].default_value=.10
# Machined brass rear cap and circumferential rim retain a readable rear-side hero view.
b=bpy.data.objects['Copper_bullet'];mat=G.mat('c59a3f',metal=.9,rough=.2)
me=bpy.data.meshes.new('Machined brass rear cap');me.from_pydata([(.027*math.cos(i*math.tau/32),-.076,.027*math.sin(i*math.tau/32)) for i in range(32)],[],[tuple(reversed(range(32)))]);cap=G.link('Brass cartridge cap',me,b);me.materials.append(mat)
for r in [.023,.027]:G.curve('Machined rear rim',[(r*math.cos(i*math.tau/32),-.077,r*math.sin(i*math.tau/32)) for i in range(32)],.0008,mat,b,loop=True).data.bevel_resolution=0
for mat in [mat for mat in bpy.data.materials if mat.name.startswith('c59a3f')]:
 if mat.use_nodes:
  for node in mat.node_tree.nodes:
   if node.type=='BSDF_PRINCIPLED':node.inputs['Base Color'].default_value=(.65,.42,.08,1);node.inputs['Emission Color'].default_value=(.65,.42,.08,1);node.inputs['Emission Strength'].default_value=.06
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0]:
  cap=1024 if any(k in im.name.lower() for k in ['head','body','saloon']) else 512
  if max(im.size)>cap:
   r=cap/max(im.size);im.scale(max(1,int(im.size[0]*r)),max(1,int(im.size[1]*r)))
  im.pack()
for mat in bpy.data.materials:
 if mat.use_nodes:
  for node in list(mat.node_tree.nodes):
   if node.type=='NORMAL_MAP':mat.node_tree.nodes.remove(node)
s.eevee.taa_render_samples=20;s.eevee.use_raytracing=False;s.render.use_simplify=True;s.render.simplify_subdivision=2
text=bpy.data.texts.load(str(R/'scripts/slow_eddie_v5/runtime.py'));text.name='slow_eddie_v5_runtime.py';exec(compile(text.as_string(),text.name,'exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v5.blend'))
