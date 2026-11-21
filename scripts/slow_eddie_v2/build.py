import bpy,sys,math,random,json
from pathlib import Path
from mathutils import Vector as V
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v2';s=bpy.context.scene
sys.path.insert(0,str(R/'scripts/washroom_experiment'));sys.path.insert(0,str(R/'scripts/inside_brain_dog'));from sets import Stage,rgb
from build_inside_brain_dog import cel_material
bpy.app.handlers.frame_change_post.clear();g=Stage(s);random.seed(92)
# Keep imported architectural detail, diversify each mesh/material separately.
palette=['2457a7','a93830','c69a54','53372b'];names=['TELEGRAPHS','SALOON','PHOTOGRAPHS','FEED & LIVERY']
buildings=[o for o in s.objects if o.name.startswith('saloon') and o.type=='MESH']
for i,o in enumerate(buildings):
 o.data=o.data.copy();tone=palette[i%4];zscale=[.85,1.1,.95,1.22][i%4];o.scale.z=zscale
 for j,mat in enumerate(list(o.data.materials)):
  if not mat:continue
  m=mat.copy();o.data.materials[j]=m
  if not m.use_nodes:continue
  bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if bs:
   for socket in ['Base Color','Emission Color']:
    for link in list(bs.inputs[socket].links):m.node_tree.links.remove(link)
   c=rgb(tone);factor=[.7,1,.85,1.15][j%4];col=tuple(min(1,x*factor) for x in c)
   if j>0 and j%5==0:col=rgb('422e25')
   bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Emission Color'].default_value=(*col,1);bs.inputs['Emission Strength'].default_value=.25
 side=1 if o.location.x>0 else -1;y=o.location.y;h=6.1*zscale
 # False front gable, dimensional pitched roof or stepped parapet.
 if i%3==0:
  verts=[(-3,-2.7,0),(3,-2.7,0),(3,2.7,0),(-3,2.7,0),(0,-2.7,1.3),(0,2.7,1.3)]
  mesh=bpy.data.meshes.new('Gable');mesh.from_pydata(verts,[],[(0,1,4),(3,5,2),(0,4,5,3),(1,2,5,4),(0,3,2,1)]);roof=g.link('Pitched saloon roof',mesh,xyz=(side*6.4,y,h));roof.data.materials.append(g.mat('643b29'));roof['set_ink']=True
 else:
  roof=g.box('False-front stepped parapet',(side*6.4,y,h),(5.7,5.6,.3),g.mat(tone));roof['set_ink']=True
 # street-facing painted boards, explicit scene lettering, never captions.
 board=g.box('Painted Western sign',(side*2.82,y,3.5*zscale),(.08,4.7,.65),g.mat(tone));board['set_ink']=True
 text=g.label('Sign '+names[i%4],names[i%4],(side*2.76,y,3.5*zscale),.34,g.mat('ffdf9a',em=.65));text.rotation_euler=(math.pi/2,0,-side*math.pi/2)
O=bpy.data.objects
O['challenger_body'].data.materials[0]=cel_material('Challenger asymmetrical threequarter body',P/'art/challenger_body.png')
bpy.data.objects['challenger_body'].data.materials[0]=cel_material('Challenger painted three quarter body',P/'art/challenger_body.png')
# Soft desaturated shadows, warm sand. One Sun and one fill.
s.world.node_tree.nodes['Background'].inputs[0].default_value=(*rgb('81bcec'),1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.8
sun=bpy.data.objects['Warm afternoon Sun'];sun.data.angle=.36;sun.data.energy=2.4;sun.rotation_euler=V((1,.6,-2)).to_track_quat('-Z','Y').to_euler()
fill=bpy.data.objects['Subtle sky fill'];fill.data.energy=550;fill.data.color=rgb('eee5d7');fill.data.size=12
road=bpy.data.objects['Dusty Main Street'];bs=next(n for n in road.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED');nt=road.data.materials[0].node_tree
for n in nt.nodes:
 if n.type=='VALTORGB':n.color_ramp.elements[0].color=(*rgb('c7a573'),1);n.color_ramp.elements[1].color=(*rgb('e2c08a'),1)
bs.inputs['Emission Color'].default_value=(*rgb('D9B47E'),1);bs.inputs['Emission Strength'].default_value=.22
# Close the complete far frustum with overlapping low-poly red canyon buttes.
for i in range(11):
 x=-35+i*7;z=4+random.random()*4
 bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=6.5,radius2=4,depth=z,location=(x,51+random.uniform(-3,3),z/2-.2));o=bpy.context.object;o.name='Red sandstone mesa';o.data.materials.append(g.mat(['b65b3b','cf7850','a34c38'][i%3]));o['set_ink']=False
 cap=g.box('Mesa horizontal cap',(x,o.location.y,z-.2),(8,6,.35),g.mat('db9163'),bevel=.12)
for i,(x,y,z) in enumerate([(-12,45,13),(6,49,15),(22,50,12)]):
 for k in range(4):g.ball('Puffy white cloud',(x+k*1.2,y,z+(.5 if k in [1,2] else 0)),(1.6,.5,.8),g.mat('fff6e6',em=.55))
# Truly hollow tumbleweed: thin interwoven loops, no center mass.
old=bpy.data.objects['Rolling_tumbleweed'];bpy.data.objects.remove(old,do_unlink=True);tw=g.link('Rolling_tumbleweed')
for j in range(11):
 pts=[]
 for k in range(30):
  a=k*math.tau/30;r=.36*(1+.11*math.sin(5*a+j));v=V((r*math.cos(a),r*math.sin(a),.04*math.sin(3*a+j)));v.rotate(__import__('mathutils').Euler((j*.57,j*.89,j*.33)));pts.append(v)
 o=g.curve('Hollow dry twig',pts,.007,g.mat('997044'),tw,loop=True);o.data.bevel_resolution=0
# Seam-free lathed copper bullet (axis+Y), brass rear casing.
old=bpy.data.objects['Copper_bullet'];bpy.data.objects.remove(old,do_unlink=True)
verts=[];faces=[];profile=[(-.075,.027),(-.035,.027),(.012,.027),(.05,.019),(.078,.001)]
for y,r in profile:
 for j in range(20):a=j*math.tau/20;verts.append((r*math.cos(a),y,r*math.sin(a)))
for k in range(len(profile)-1):
 for j in range(20):a=k*20+j;b=k*20+(j+1)%20;faces.append((a,b,b+20,a+20))
mesh=bpy.data.meshes.new('Smooth lathed projectile');mesh.from_pydata(verts,[],faces);bullet=g.link('Copper_bullet',mesh);mesh.materials.append(g.mat('d76c28',metal=.65,rough=.23,em=.45));mesh.materials.append(g.mat('e1af35',metal=.5,rough=.25,em=.35))
for i,p in enumerate(mesh.polygons):p.material_index=int(i<20);p.use_smooth=True
# Flat flash and cheap smoke tied to physical muzzle.
mesh=bpy.data.meshes.new('Flash star');vs=[]
for j in range(12):a=j*math.tau/12;r=.19 if j%2==0 else .055;vs.append((math.cos(a)*r,math.sin(a)*r,0))
mesh.from_pydata(vs,[],[tuple(range(12))]);flash=g.link('Muzzle flash',mesh);mesh.materials.append(g.mat('ffe297',em=3))
smoke=g.ball('Muzzle smoke',(0,0,0),(.08,.08,.08),g.mat('d4c8b5',em=.25))
# Head variants stay packed and referenced across reopen.
for who in ['challenger','eddie']:
 for mode in ['head','blink']:
  mat=cel_material(who+'_'+mode+'_v2',P/'art'/f'{who}_{mode}.png');mat.use_fake_user=True
s.render.resolution_percentage=50;s.eevee.taa_render_samples=12
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0]:im.pack()
# Remove previous runtime text, retain v1 source file untouched.
t=bpy.data.texts.load(str(R/'scripts/slow_eddie_v2/runtime.py'));t.name='slow_eddie_v2_runtime.py';exec(compile(t.as_string(),t.name,'exec'))
s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v2.blend'))
(P/'scene_stats.json').write_text(json.dumps({'mesh_triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in s.objects if o.type=='MESH')},indent=2))
