import bpy,math,sys,json,hashlib,random,ast
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v8';s=bpy.context.scene;O=bpy.data.objects;bpy.app.handlers.frame_change_post.clear()
sys.path.insert(0,str(R/'scripts/washroom_experiment'));from sets import rgb
# Reuse only vetted constructor functions, not V7's scene rebuilding entry point.
ink=bpy.data.materials['V7 thin warm ink'];black=bpy.data.materials['V7 matte limb ink'];cream=bpy.data.materials['V7 light responsive cream'];hatTan=bpy.data.materials['V7 tan felt hat'];brown=bpy.data.materials['V7 warm leather'];steel=bpy.data.materials['V7 dark gunmetal']
tree=ast.parse((R/'scripts/slow_eddie_v7/build.py').read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef)];exec(compile(ast.Module(body=functions,type_ignores=[]),'v7_constructor_functions','exec'))
before=town_hash()
def identity_hash():
 names=[o for o in O if o.type=='MESH' and o.name.startswith('V7 ') and any(x in o.name for x in ['rough skull','crown','curved brim','hatband',' boot',' leg'])];data=[(o.name,[list(v.co) for v in o.data.vertices]) for o in sorted(names,key=lambda o:o.name)];return hashlib.sha256(json.dumps(data).encode()).hexdigest()
identity_before=identity_hash()
def remove_names(names):
 all_names=set(names)
 for name in names:
  if name in O:all_names.update(c.name for c in O[name].children_recursive)
 for name in all_names:
  if name in O:bpy.data.objects.remove(O[name],do_unlink=True)
# Keep the existing contour, pose proportions and DOF; deepen only the rounded torso cross-section.
profiles=[(.88,.20,.11),(.91,.25,.14),(.98,.27,.15),(1.40,.315,.145),(1.49,.31,.14),(1.56,.25,.105),(1.60,.12,.085)]
def body_y(x,z):
 for i in range(len(profiles)-1):
  a,b=profiles[i],profiles[i+1]
  if z<=b[0]:
   t=max(0,min(1,(z-a[0])/(b[0]-a[0])));rx=a[1]+(b[1]-a[1])*t;ry=(a[2]+(b[2]-a[2])*t)*1.22;return -ry*math.sqrt(max(.04,1-(x/rx)**2))
 return -.10
for who in ['challenger','eddie']:
 shirt=O['V7 '+who+' tailored shirt'];remove_names([c.name for c in shirt.children])
 for v in shirt.data.vertices:v.co.y*=1.22
 for p in shirt.data.polygons:p.use_smooth=True
 for edge in shirt.data.edges:
  zs=[shirt.data.vertices[i].co.z for i in edge.vertices];edge.use_edge_sharp=max(zs)-min(zs)<1e-5 and (min(zs)<.881 or max(zs)>1.599)
 normal=shirt.modifiers.new('V8 smooth weighted torso wrap','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=25;outline(shirt,.010)
for o in O:
 if o.name.startswith('V7 challenger woven red stripe'):
  for spline in o.data.splines:
   for p in spline.points:p.co.y=body_y(p.co.x,p.co.z)-.0055
# Replace both folded polygon vests with closed, smoothly curved, rounded lapel panels.
remove_names([o.name for o in O if o.name.startswith('V7 eddie ') and any(t in o.name for t in ['flared vest','vest lapel'])])
zs=[.99,1.025,1.18,1.39,1.49,1.54];inner=[.112,.103,.104,.118,.125,.12];outer=[.227,.267,.292,.299,.275,.222]
def interp(values,z):
 for i in range(len(zs)-1):
  if z<=zs[i+1]:
   t=max(0,min(1,(z-zs[i])/(zs[i+1]-zs[i])));t=t*t*(3-2*t);return values[i]+(values[i+1]-values[i])*t
 return values[-1]
for side in [-1,1]:
 nu=12;nz=24;vs=[];fs=[]
 for layer in [0,1]:
  for i in range(nz+1):
   z=.99+.55*i/nz;ix=interp(inner,z);ox=interp(outer,z)
   for j in range(nu+1):
    x=side*(ix+(ox-ix)*j/nu);vs.append((x,body_y(x,z)-.020+layer*.022,z))
 count=(nu+1)*(nz+1)
 for layer in [0,1]:
  for i in range(nz):
   for j in range(nu):
    a=layer*count+i*(nu+1)+j;face=(a,a+1,a+nu+2,a+nu+1);fs.append(face if layer==0 else tuple(reversed(face)))
 boundary=list(range(nu+1))+[i*(nu+1)+nu for i in range(1,nz+1)]+[nz*(nu+1)+j for j in range(nu-1,-1,-1)]+[i*(nu+1) for i in range(nz-1,0,-1)]
 for i,a in enumerate(boundary):b=boundary[(i+1)%len(boundary)];fs.append((a,b,b+count,a+count))
 panel=mesh('V8 smooth fitted lapel',vs,fs,brown,O['V7 eddie torso'],0,True);mod=panel.modifiers.new('Rounded sewn panel edges','BEVEL');mod.width=.007;mod.segments=3;mod.limit_method='ANGLE';mod.angle_limit=.5;bpy.context.view_layer.objects.active=panel;bpy.ops.object.modifier_apply(modifier=mod.name);mod=panel.modifiers.new('Cloth weighted normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=20;outline(panel,.007)
 pts=[]
 for i in range(26):
  t=i/25;z=1.525-.25*t;x=side*(.125+.022*math.sin(t*math.pi));pts.append((x,body_y(x,z)-.033,z))
 curve('V8 rounded lapel piping',pts,.006,hatTan,O['V7 eddie torso'])
# Tighten the tense grin while keeping the V6 face and its art-space anchors.
remove_names([o.name for o in O if o.name.startswith('V7 challenger ') and any(t in o.name for t in ['clenched mouth','teeth','tooth separator','tooth row'])])
hp=O['V7 challenger head pivot'];patch('V7 challenger clenched mouth',roundrect(-.005,-.129,.207,.071,.020),black,hp,.006);patch('V7 challenger teeth',roundrect(-.005,-.128,.174,.044,.012),cream,hp,.009)
for x in [-.055,-.011,.034]:faceline('V7 challenger tooth separator',[(x,-.148),(x,-.109)],.0023,hp)
faceline('V7 challenger tooth row',[(-.091,-.128),(.083,-.128)],.0023,hp)
# A curved ivory grip with shallow nacre grain, seated into the imported steel frame.
remove_names([o.name for o in O if o.name.startswith('V7 pearl')])
pearl=shader('V8 warm nacre ivory','EFE8D5',0,.31,False);nt=pearl.node_tree;l=nt.links;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Coat Weight'].default_value=.2;bs.inputs['Coat Roughness'].default_value=.23;bs.inputs['Emission Color'].default_value=(*rgb('EFE8D5'),1);bs.inputs['Emission Strength'].default_value=.25
noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=85;noise.inputs['Detail'].default_value=2;wave=nt.nodes.new('ShaderNodeValToRGB');wave.color_ramp.elements[0].color=(*rgb('D7D2C1'),1);wave.color_ramp.elements[1].color=(*rgb('F5EFDE'),1);l.new(noise.outputs['Fac'],wave.inputs[0]);l.new(wave.outputs[0],bs.inputs['Base Color']);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.07;bump.inputs['Distance'].default_value=.0008;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
grip=loft('V7 pearl revolver butt',[(-.065,.007,.006),(-.055,.021,.016),(-.030,.033,.022),(0,.035,.023),(.030,.032,.023),(.055,.022,.017),(.065,.007,.006)],pearl,O['V7 eddie torso'],24);grip.location=(-.355,-.185,.970);grip.rotation_euler.y=math.radians(-50);remove_names([c.name for c in grip.children]);outline(grip,.003)
# A small dark cuff meets both the ivory butt and the actual revolver frame.
cube('V8 revolver grip seat',(-.314,-.150,.935),(.055,.045,.038),steel,O['V7 eddie torso'],.009)
# Preserve a single clean waist silhouette after deepening the shirt cross-section.
for who in ['challenger','eddie']:
 belt=O['V7 '+who+' belt'];remove_names([c.name for c in belt.children])
 for v in belt.data.vertices:v.co.y*=1.23
 outline(belt,.004)
 for o in O:
  if o.name=='V7 '+who+' buckle':o.location.y-=.05
  elif o.name.startswith('V7 '+who+' brass buckle'):
   for sp in o.data.splines:
    for point in sp.points:point.co.y-=.05
# Sleek copper ogive with a short recessed chamfered brass rim, not a yellow disk.
b=O['Copper_bullet'];remove_names([c.name for c in b.children]);copper=shader('V8 copper jacket','CC794A',.9,.22,False);brass=shader('V8 aged brass rim','AE8242',.85,.27,False);primer=shader('V8 recessed primer','705439',.7,.38,False)
for mat in [copper,brass]:
 bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Emission Color'].default_value=bs.inputs['Base Color'].default_value;bs.inputs['Emission Strength'].default_value=.05 if mat==copper else .015
profile=[(-.064,.005),(-.066,.014),(-.070,.019),(-.068,.022),(-.062,.022),(-.058,.0205),(-.049,.021),(.005,.021),(.025,.020),(.045,.017),(.060,.011),(.073,.004),(.077,.0005)]
vs=[];faces=[];mats=[];n=32
for y,r in profile:
 for j in range(n):a=j*math.tau/n;vs.append((r*math.cos(a),y,r*math.sin(a)))
for i in range(len(profile)-1):
 for j in range(n):a=i*n+j;c=i*n+(j+1)%n;faces.append((a,c,c+n,a+n));mats.append(1 if i<6 else 0)
vs.append((0,-.064,0));center=len(vs)-1
for j in range(n):faces.append((center,(j+1)%n,j));mats.append(2)
faces.append(tuple(range((len(profile)-1)*n,len(profile)*n)));mats.append(0)
me=bpy.data.meshes.new('V8 copper ogive and recessed rim');me.from_pydata(vs,[],faces);me.materials.clear()
for m in [copper,brass,primer]:me.materials.append(m)
b.data=me
for p,idx in zip(me.polygons,mats):p.use_smooth=True;p.material_index=idx
# Fix outward normals on the new closed projectile.
import bmesh
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();outline(b,.0006)
# Ragged multi-lobed HDR flame, hot core and small spark trails.
fx=O['V7 muzzle FX root'];remove_names([c.name for c in fx.children])
def glow(name,hex,strength):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(*rgb(hex),1);em.inputs[1].default_value=strength;out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(em.outputs[0],out.inputs[0]);return m
amber=glow('V8 amber flame','FF610A',3.5);hot=glow('V8 hot flame core','FFF3A1',7.0);spark=glow('V8 sparks','FFD67B',5.0)
nt=amber.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');em=out.inputs[0].links[0].from_socket;tr=nt.nodes.new('ShaderNodeBsdfTransparent');mx=nt.nodes.new('ShaderNodeMixShader');mx.inputs[0].default_value=.55;nt.links.new(tr.outputs[0],mx.inputs[1]);nt.links.new(em,mx.inputs[2]);nt.links.new(mx.outputs[0],out.inputs[0]);amber.surface_render_method='BLENDED';amber.use_backface_culling=True
for index,(length,radius,mat) in enumerate([(.28,.050,amber),(.20,.027,hot),(.25,.026,amber),(.21,.024,amber)]):
 verts=[];polys=[];rings=8;steps=20;angle=index*2.399
 for i in range(rings):
  t=i/(rings-1);rad=radius*math.sin(math.pi*(.10+.89*t))*(1-.50*t);off=.12*(t**1.4)*(0 if index<2 else 1)
  for j in range(steps):
   a=j*math.tau/steps;r=rad*(1+.23*math.sin(5*a+index+t*3)+.12*math.sin(3*a-.7));x=length*t+.018*t*math.sin(3*a+index);verts.append((x,off*math.cos(angle)+r*math.cos(a),off*math.sin(angle)+r*math.sin(a)))
 for i in range(rings-1):
  for j in range(steps):a=i*steps+j;c=i*steps+(j+1)%steps;polys.append((a,c,c+steps,a+steps))
 polys.extend([tuple(reversed(range(steps))),tuple(range((rings-1)*steps,rings*steps))]);mesh('V8 ragged flame '+str(index),verts,polys,mat,fx,0,True)
for j in range(3):curve('V8 spark '+str(j),[(0,0,0),(.08,0,0)],.0016,spark,fx)
for j in range(3):
 smoke=O['V7 smoke '+str(j)];m=smoke.data.materials[0].copy();m.name='V8 soft smoke '+str(j);smoke.data.materials[0]=m;m.surface_render_method='BLENDED'
# Readable hollow twig silhouette; no filled core is added.
twigmat=shader('V8 dry twig contrast','59452F',0,.9,False)
for child in O['Rolling_tumbleweed'].children:
 if child.type=='CURVE':child.data.bevel_depth*=1.5;child.data.materials.clear();child.data.materials.append(twigmat)
# Warm front-right key and controlled periwinkle fill; physical hat shadows remain enabled.
sun=O['Warm afternoon Sun'];sun.data.energy=5.5;sun.data.color=rgb('FFE6B5');sun.rotation_euler=V((-.70,.75,-.60)).to_track_quat('-Z','Y').to_euler();sun.data.angle=math.radians(8);sun.data.use_shadow=True
fill=O['Subtle sky fill'];fill.data.energy=850;fill.data.color=rgb('7C94C8');fill.data.size=10
for m in bpy.data.materials:
 if m.use_nodes and m.get('light_responsive_cel'):
  ramp=m.node_tree.nodes.get('Three soft cel light stops')
  if ramp:
   ramp.inputs[0].links[0].from_node.inputs[1].default_value=.84;ramp.color_ramp.elements[0].color=(*rgb('7C94C8'),1);ramp.color_ramp.elements[1].color=(.70,.73,.80,1);ramp.color_ramp.elements[2].color=(1,.91,.74,1)
w=s.world.node_tree;bg=next(n for n in w.nodes if n.type=='BACKGROUND');source=bg.inputs[0].links[0].from_socket;mix=w.nodes.new('ShaderNodeMixRGB');mix.name='V8 periwinkle sky illumination';mix.inputs[0].default_value=.18;mix.inputs[2].default_value=(*rgb('7C94C8'),1);w.links.new(source,mix.inputs[1]);w.links.new(mix.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=1.0
# Z-depth aerial haze precedes the existing subtle Fog Glow; sky is excluded from dust mixing.
for layer in s.view_layers:layer.use_pass_z=True
nt=s.node_tree;l=nt.links;rl=next(n for n in nt.nodes if n.type=='R_LAYERS');gl=next(n for n in nt.nodes if n.type=='GLARE');co=next(n for n in nt.nodes if n.type=='COMPOSITE');base=co.inputs[0].links[0].from_node
mr=nt.nodes.new('CompositorNodeMapRange');mr.name='V8 haze 18m start 45m depth';mr.inputs['From Min'].default_value=18;mr.inputs['From Max'].default_value=63;mr.inputs['To Min'].default_value=0;mr.inputs['To Max'].default_value=.45;mr.use_clamp=True;l.new(rl.outputs['Depth'],mr.inputs['Value'])
mask=nt.nodes.new('CompositorNodeMath');mask.operation='LESS_THAN';mask.inputs[1].default_value=s.camera.data.clip_end*.99;l.new(rl.outputs['Depth'],mask.inputs[0]);mult=nt.nodes.new('CompositorNodeMath');mult.operation='MULTIPLY';l.new(mask.outputs[0],mult.inputs[0]);l.new(mr.outputs[0],mult.inputs[1]);haze=nt.nodes.new('CompositorNodeMixRGB');haze.name='V8 warm dusty aerial perspective';haze.inputs[2].default_value=(*rgb('DFCEB4'),1);l.new(mult.outputs[0],haze.inputs[0]);l.new(rl.outputs['Image'],haze.inputs[1]);l.new(haze.outputs[0],gl.inputs[0]);l.new(haze.outputs[0],base.inputs[1])
after=town_hash();assert before==after;identity_after=identity_hash();assert identity_before==identity_after
(P/'town_preservation.json').write_text(json.dumps({'before':before,'after':after,'unchanged':True,'head_hat_leg_geometry_before':identity_before,'head_hat_leg_geometry_after':identity_after,'character_identity_unchanged':True},indent=2))
# Bake static weighted normals; keep native output, optics, geometry and actual shadow reception.
for o in list(O):
 for mod in list(o.modifiers):
  if mod.type=='WEIGHTED_NORMAL' and o.type=='MESH':
   bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
gl.quality='LOW'
s.render.resolution_percentage=100;s.eevee.taa_render_samples=12
text=bpy.data.texts.load(str(R/'scripts/slow_eddie_v8/runtime.py'));text.name='slow_eddie_v8_runtime.py';exec(compile(text.as_string(),text.name,'exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v8.blend'));print('V8 BUILD PASSED',flush=True)
