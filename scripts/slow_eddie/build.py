import bpy,math,json,sys,time,os
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path('D:/remotionshorts');OUT=ROOT/'renders/slow_eddie';ART=OUT/'art'
sys.path.insert(0,str(ROOT/'scripts/inside_brain_dog'));sys.path.insert(0,str(ROOT/'scripts/washroom_experiment'));from build_inside_brain_dog import card,cel_material
from sets import Stage,rgb
V=Vector
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.use_raytracing=False;s.eevee.taa_render_samples=12;s.eevee.fast_gi_method='AMBIENT_OCCLUSION_ONLY';s.render.use_simplify=True;s.render.simplify_subdivision=2
s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=50;s.render.fps=30;s.frame_start=1;s.frame_end=300
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(*rgb('54afff'),1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
s.view_settings.view_transform='Standard';s.view_settings.look='Medium High Contrast' if False else 'None'
g=Stage(s)
def empty(n):return g.link(n)
def imported(name,width):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(OUT/'assets'/f'{name}.glb'));obs=list(set(bpy.data.objects)-before);meshes=[o for o in obs if o.type=='MESH'];bpy.context.view_layer.update()
 points=[o.matrix_world@V(c) for o in meshes for c in o.bound_box];lo=V(tuple(min(p[i] for p in points) for i in range(3)));hi=V(tuple(max(p[i] for p in points) for i in range(3)));print('IMPORT',name,list(lo),list(hi),flush=True)
 scale=width/max(hi-lo);center=V(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
 for o in meshes:
  matrix=o.matrix_world.copy();o.parent=None
  for v in o.data.vertices:v.co=(matrix@v.co-center)*scale
  o.matrix_world.identity()
 bpy.ops.object.select_all(action='DESELECT')
 for o in meshes:o.select_set(True)
 bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join();result=bpy.context.object
 for o in obs:
  try:
   if o!=result and o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
  except ReferenceError:pass
 result.name=name;return result

saloon=imported('saloon',7);saloon.location=(7,9,0)
# Asset sanitation BEFORE any rendering: trim material maps and mesh triangle budget.
for image in bpy.data.images:
 if image.type=='IMAGE' and image.size[0] and max(image.size)>1024:
  k=1024/max(image.size);image.scale(max(1,int(image.size[0]*k)),max(1,int(image.size[1]*k)))
for mat in bpy.data.materials:
 if mat.use_nodes:
  for n in list(mat.node_tree.nodes):
   if n.type in ['NORMAL_MAP','BUMP']:mat.node_tree.nodes.remove(n)
# storefront original 203k? decimate to 5000 maximum
for o in [saloon]:
 tris=sum(len(p.vertices)-2 for p in o.data.polygons)
 if tris>5000:
  m=o.modifiers.new('Preimport sanitation triangle budget','DECIMATE');m.ratio=5000/tris;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
# Repeated actual downloaded saloon mesh, alternating painted facade materials.
for side in [-1,1]:
 for j in range(6):
  o=saloon if side==1 and j==0 else saloon.copy()
  if o!=saloon:s.collection.objects.link(o)
  o.location=(side*6.4,j*7-5,0);o.rotation_euler.z=math.pi/2*side
  o['set_ink']=j<3
# Subordinate warm emission-assisted facade colors preserve depth under the sun.
for mat in saloon.data.materials:
 if mat and mat.use_nodes:
  bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if bs:
   bs.inputs['Emission Color'].default_value=bs.inputs['Base Color'].default_value
   bs.inputs['Emission Strength'].default_value=.18
# road noise / warm sun
road=g.box('Dusty Main Street',(0,14,-.07),(13,75,.12),g.mat('ca9c61'));road['set_ink']=False
mat=road.data.materials[0];mat.use_nodes=True;nt=mat.node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=5;noise.inputs['Detail'].default_value=2;ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*rgb('ad804e'),1);ramp.color_ramp.elements[1].color=(*rgb('ddbd83'),1);nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],bs.inputs['Base Color'])
sun=g.light('Warm afternoon Sun','SUN',(-4,-8,10),(0,0,0),3.5,'ffe0aa');sun.data.angle=.18
fill=g.light('Subtle sky fill','AREA',(0,-3,8),(0,9,1),100,'b9d8ff');fill.data.size=8;fill.data.use_shadow=False
camdata=bpy.data.cameras.new('Duel lens');cam=bpy.data.objects.new('Camera',camdata);s.collection.objects.link(cam);s.camera=cam;camdata.lens=42;camdata.clip_end=200;camdata.dof.use_dof=True;camdata.dof.aperture_fstop=5.6
# actor body dimension2.3 square: soles at z0, body center1.08; neck attachment at z1.5.
actors={}
for name,y in [('challenger',0),('eddie',19)]:
 body=card(g,name+'_body',2.3,2.3,cel_material(name+'body',ART/f'{name}_body.png'));headpivot=empty(name+'_head_pivot');head=card(g,name+'_head',1.53,1.53,cel_material(name+'head',ART/f'{name}_head.png'),headpivot)
 target=empty(name+'_parallel_camera_target');con=headpivot.constraints.new('DAMPED_TRACK');con.track_axis='TRACK_Z';con.target=target
 actors[name]=(body,headpivot,target,y)
 for x in [-.245,.193]:
  o=g.ball(name+' sole contact',(x,y,.006),(.14,.08,.006),g.mat('5a493e'));o['set_ink']=False
# downloaded real 3D props
GUN=imported('revolver',.7);GUN.name='Challenger_revolver';GUN['set_ink']=True
ED=GUN.copy();ED.data=GUN.data.copy();s.collection.objects.link(ED);ED.name='Eddie_pearl_revolver';ED['set_ink']=True
BULLET=imported('bullet',.18);BULLET.name='Copper_bullet';BULLET['set_ink']=True;BULLET.data.materials.clear();BULLET.data.materials.append(g.mat('bf7948',metal=.7,rough=.32))
BULLET.data.materials.clear();BULLET.data.materials.append(g.mat('c17b46',metal=.45,rough=.35))
TW=imported('tumbleweed',.8);TW.name='Rolling_tumbleweed'
for v in TW.data.vertices:v.co.z-=.4
CACT=imported('cactus',2)
for i in range(8):
 o=CACT if i==0 else CACT.copy()
 if i:s.collection.objects.link(o)
 o.location=((-1 if i%2 else 1)*10, i*6-5,0)
# Real material override on the two hero guns, retaining imported 3D shape.
GUN.data.materials.clear();GUN.data.materials.append(g.mat('34323b',metal=.45))
ED.data.materials.clear();ED.data.materials.append(g.mat('594b43',metal=.4))
pearl=g.box('Eddie pearl handle',(-.20,-.027,.10),(.10,.018,.16),g.mat('f5e8cf'));pearl.parent=ED
# actor mouth anchored straw; geometry curve in the same face plane.
straw=g.curve('Eddie mouth-anchored straw',[(0,0,0),(.17,-.035,0),(.31,-.06,0)],.009,g.mat('e9cb78',em=.7));straw.parent=actors['eddie'][1];straw.location=(0,-.25,.006)
sweat=g.ball('Temple socket sweat',(0,0,0),(.036,.014,.072),g.mat('71c7e3',em=.6));sweat.parent=actors['challenger'][1];sweat.location=(.48,.12,.018)
# gun grip manual named anchor, with front fingers derived from same frame.
grip=empty('Challenger grip surface');fingers=[]
for i in range(3):fingers.append(g.ball('Grip finger '+str(i),(0,0,0),(.035,.025,.014),g.mat('fdfaf2',em=.7)))
# assert triangle and image budget, pack all dependencies
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0]:
  cap=1024 if 'saloon' in im.name.lower() or 'head' in im.name or 'body' in im.name else 512
  if max(im.size)>cap:
   k=cap/max(im.size);im.scale(max(1,int(im.size[0]*k)),max(1,int(im.size[1]*k)))
  im.pack()
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in s.objects if o.type=='MESH');assert tris<150000,tris
(OUT/'sanitation.json').write_text(json.dumps({'triangles':tris,'image_sizes':{im.name:list(im.size) for im in bpy.data.images},'lights':2,'samples':12},indent=2))
# store executable animation separately and embedded, explicitly bootstrapped on reopen.
sys.path.insert(0,str(ROOT/'scripts/studio'));from set_ink import SetInk
INK=SetInk(s)
runtime=ROOT/'scripts/slow_eddie/runtime.py';txt=bpy.data.texts.load(str(runtime));txt.name='slow_eddie_runtime.py';exec(compile(txt.as_string(),txt.name,'exec'))
for f in [1,30,31,95,96,150,180,215,216,280,300]:s.frame_set(f)
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'slow_eddie_v1.blend'))
print('BUILD_OK triangles',tris,flush=True)
