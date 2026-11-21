import bpy,sys,math,json,random,types
from pathlib import Path
from mathutils import Vector as V
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;P=R/'renders/gold_mine_salting_v3/flat_cast_v1'
sys.path[:0]=[str(R/'scripts'),str(D)]
import ricks_lookdev as look, shorts_preflight as gate
from geometry import *
random.seed(1899)
# Factory source only. No approved scene is loaded or edited.
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
S=bpy.context.scene;look.setup_scene(S,actor_height=1.88,frame_end=300,samples=8)
S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB';S.render.image_settings.compression=0
S.render.film_transparent=False
interior=look.apply_lighting_preset(S,'INTERIOR_WARM_CAVERN')
INK=emission('Marker ink','#16121C');INK.use_backface_culling=True;INK.use_backface_culling_shadow=True
BLACK=emission('Features ink','#16121C');CREAM=emission('Eye cream','#FFF3E0')
# Full received-light chain. No generated-Z cream override on either face.
skin=look.clean_toon('Warm cream received skin',stops=list(zip([0,.30,.66,1],interior['skin'])),light_min=.12,light_max=1.30)
red=look.clean_toon('Flannel red',stops=list(zip([0,.30,.68,1],interior['red'])),light_min=.10,light_max=1.1)
teal=look.clean_toon('Buddy teal',stops=list(zip([0,.30,.68,1],interior['teal'])),light_min=.10,light_max=1.1)
hat=look.clean_toon('Weathered brown felt','vest',.06,.5)
yellow=look.clean_toon('Knitted ochre',stops=list(zip([0,.30,.68,1],interior['yellow'])),light_min=.10,light_max=1.1)
dark=look.metal('Dark soft boots','#26232E',0,.93)
glove=look.clean_toon('Buddy dark fingers',stops=[(0,'#211C2C'),(.3,'#302637'),(.68,'#493A44'),(1,'#675054')],light_min=.05,light_max=1.1)
wood=look.metal('Oiled gun walnut','#6E3C29',0,.65)
steel=look.metal('Charcoal steel','#262D39',.48,.34,emission_strength=.025)
gold=look.metal('Solid brass gold','#F2C854',.42,.28,emission_strength=.3)
white=look.clean_toon('Ceramic cream',stops=[(0,'#9CA4B5'),(.30,'#B8B2BA'),(.68,'#E3D4BE'),(1,'#FFFFFF')],light_min=.08,light_max=.85)
stripe=look.clean_toon('Cream suspenders',stops=[(0,'#9B8792'),(1,'#EACB98')],light_min=.07,light_max=.5)
lanternred=look.metal('Painted red enamel','#96352B',.1,.6)
blue=look.metal('Blue enamel kettle','#356786',.25,.3)
glow=emission('Amber lamp glow','#FFD084',2.2)
goldglow=emission('Gold spark glow','#FFC95A',1.35)
hot=emission('Muzzle hot center','#FFCE57',1.6)
orangeFire=emission('Orange gold combustion','#FF780D',1.5)
# Translucent flame envelope exposes the bright inner core instead of reading
# as an opaque orange card when viewed down the barrel axis.
nt=orangeFire.node_tree;n=nt.nodes;l=nt.links;em=next(x for x in n if x.type=='EMISSION');out=next(x for x in n if x.type=='OUTPUT_MATERIAL')
tr=n.new('ShaderNodeBsdfTransparent');blend=n.new('ShaderNodeMixShader');blend.inputs[0].default_value=.40;l.new(tr.outputs[0],blend.inputs[1]);l.new(em.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs[0]);orangeFire.surface_render_method='BLENDED'
def texture(name,c0,c1,scale=3,bump=.12):
 m=look.metal(name,c0,0,.9);nt=m.node_tree;n=nt.nodes;l=nt.links;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED')
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.72
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=look.rgba(c0);ramp.color_ramp.elements[1].color=look.rgba(c1)
 l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
 b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.045;l.new(tex.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],bs.inputs['Normal'])
 return m
rock=texture('Ochre cavern rock','#2A190F','#C88945',3,.28)
# Layer broad mineral breakup, pitted cells and fine sandy grain in world units.
nt=rock.node_tree;n=nt.nodes;l=nt.links;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED')
noise=next(x for x in n if x.type=='TEX_NOISE');noise.inputs['Scale'].default_value=2.4;noise.inputs['Detail'].default_value=4
ramp=next(x for x in n if x.type=='VALTORGB');ramp.color_ramp.elements[0].color=look.rgba('#2A190F');ramp.color_ramp.elements[1].color=look.rgba('#C88945')
ramp.color_ramp.elements.new(.44).color=look.rgba('#5C3A22')
vor=n.new('ShaderNodeTexVoronoi');vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=11
grain=n.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=92;grain.inputs['Detail'].default_value=2
mixgrain=n.new('ShaderNodeMath');mixgrain.operation='MULTIPLY';mixgrain.inputs[1].default_value=.24;l.new(grain.outputs['Fac'],mixgrain.inputs[0])
sumgrain=n.new('ShaderNodeMath');sumgrain.operation='ADD';l.new(mixgrain.outputs[0],sumgrain.inputs[0]);l.new(vor.outputs['Distance'],sumgrain.inputs[1])
bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.55;bump.inputs['Distance'].default_value=.07;l.new(sumgrain.outputs[0],bump.inputs['Height'])
oldb=next(x for x in n if x.type=='BUMP' and x!=bump);oldb.inputs['Strength'].default_value=.45;oldb.inputs['Distance'].default_value=.09;l.new(oldb.outputs[0],bump.inputs['Normal']);l.new(bump.outputs[0],bs.inputs['Normal'])
# World-space sampling avoids stretched Generated coordinates on thin wall meshes.
pos=n.new('ShaderNodeNewGeometry')
for texnode in [x for x in n if x.type in {'TEX_NOISE','TEX_VORONOI'}]:l.new(pos.outputs['Position'],texnode.inputs['Vector'])
timber=texture('Sawn timber grain','#38271E','#765033',6,.18)
dirt=texture('Mineral earth floor','#302921','#65533B',9,.18)
crateMat=texture('Supply pine grain','#8A683E','#BD965C',5,.12)
scar=look.metal('Broken dark crater','#241F22',0,1)
# Interior shell: authored individual low-poly longitudinal surfaces, ample camera clearance.
floor=cube('Mine dirt support',(0,1.5,-.12),(7.2,15,.24),dirt,bevel=0);floor['collision']=True
for side in [-1,1]:
 vs=[];fs=[]
 for j,y in enumerate([-5,-2,1,4,7,10]):
  for k,z in enumerate([0,.8,1.7,2.55,3.2]):
   vs.append((side*(3.3+random.uniform(-.13,.13)-.18*max(0,z-1.7)),y,z))
 for j in range(5):
  for k in range(4):a=j*5+k;fs.append((a,a+1,a+6,a+5))
 wall=mesh(('West' if side<0 else 'East')+' cavern wall',vs,fs,rock,smooth=False);wall['collision']=True
 solid=wall.modifiers.new('Closed rock collision thickness','SOLIDIFY');solid.thickness=.25
roof=cube('Rock ceiling',(0,2,3.35),(6.2,15,.30),rock,bevel=.10);roof['collision']=True
# Rear wall leaves a deep side passage on screen left.
back=cube('Strike wall',(1.76,5.15,1.58),(3.28,.45,3.15),rock,bevel=.08);back['collision']=True
# Sculpted strata over the protected collision backing.
vs=[];fs=[]
nx,nz=21,21
for iz in range(nz):
 for ix in range(nx):
  x=.12+ix*3.28/(nx-1);z=iz*3.15/(nz-1)
  rad=math.hypot(x-.55,z-1.6)
  y=4.81+random.uniform(-.025,.08)+.045*math.sin(x*6+z*4)
  if rad<.27:y=4.85+.045*max(0,1-rad/.27)
  vs.append((x,y,z))
for iz in range(nz-1):
 for ix in range(nx-1):
  a=iz*nx+ix
  center=(V(vs[a])+V(vs[a+1])+V(vs[a+nx])+V(vs[a+nx+1]))/4
  if math.hypot(center.x-.55,center.z-1.6)<.15:continue
  fs.extend([(a,a+1,a+nx+1),(a,a+nx+1,a+nx)])
relief=mesh('Sculpted ochre strike strata',vs,fs,rock,smooth=False);relief['collision']=True
deep=cube('Cool black tunnel depth',(-1.25,21,1.4),(2.75,.3,3.0),scar,bevel=0);deep['collision']=True
# A real off-centre passage continues beyond the strike alcove, with successively
# smaller projected arches and warm lamps receding into cool darkness.
for y in [5.4,8,11,14.5,18.5]:
 for x in [-2.52,.03]:
  o=cube('Receding tunnel post',(x,y,1.3),(.13,.18,2.6),timber,bevel=.018);o['collision']=True;o['set_ink']=True
 o=cube('Receding tunnel arch',(-1.245,y,2.62),(2.7,.18,.16),timber,bevel=.02);o['collision']=True;o['set_ink']=True
for side in [-1,1]:
 xx=-2.65 if side<0 else .13
 vs2=[(xx+random.uniform(-.08,.04),y,z) for y in [5,8,12,16,21] for z in [0,.8,1.7,2.8]]
 fs2=[(a,a+1,a+5,a+4) for a in [j*4+k for j in range(4) for k in range(3)]]
 o=mesh('Distant pitted tunnel flank',vs2,fs2,rock,smooth=False);o['collision']=True
for i,y in enumerate([7,12,17]):
 x=-1.15
 for z in [2.34,2.54]:cylinder('Distant lantern cap',(x,y,z-.02),(x,y,z+.02),.06,lanternred,verts=12,outline=.002)
 sphere('Distant warm lantern',(x,y,2.44),(.045,.045,.09),glow,seg=12,rings=6)
 line('Distant lantern chain',[(x,y,2.56),(x,y,2.72)],.006,steel)
cube('Distant tunnel roof',(-1.25,13,2.9),(2.8,16,.24),rock,bevel=.04)['collision']=True
cube('Distant tunnel earth',(-1.25,13,-.13),(2.8,16,.26),dirt if 'dirt' in globals() else rock,bevel=0)['collision']=True
for y in [-2.8,0.8,4.65,7.5]:
 for x in [-2.7,2.7]:
  beam=cube('Timber post',(x,y,1.42),(.24,.28,2.84),timber,bevel=.035);beam['collision']=True;beam['set_ink']=True
  for z in [.4,2.45]:sphere('Forged post bolt',(x,y-.15,z),(.038,.018,.038),steel,seg=12,rings=6)
 lintel=cube('Timber crossbeam',(0,y,2.86),(5.7,.30,.25),timber,bevel=.035);lintel['collision']=True;lintel['set_ink']=True
 for x in [-2.45,2.45]:
  brace=cube('Angled timber brace',(x,y,2.6),(.15,.18,.65),timber,bevel=.02);brace.rotation_euler.y=math.radians(38*(1 if x>0 else -1));brace['collision']=True
for y in [i*.52-4.7 for i in range(15)]:
 cube('Railway sleeper',(0,y,.025),(1.65,.20,.09),timber,bevel=.015)
 for x in [-.52,.52]:
  cube('Rail chair',(x,y,.075),(.18,.19,.025),steel,bevel=.005)
  for dx in [-.065,.065]:sphere('Rail spike',(x+dx,y,.10),(.016,.016,.01),steel,seg=8,rings=4)
for x in [-.52,.52]:
 rail=cube('Iron mine rail',(x,-1.0,.115),(.065,7.6,.075),steel,bevel=.012);rail['collision']=True
# Loose stones define the mine edges rather than cluttering the action.
for i in range(45):
 x=random.choice([-1,1])*random.uniform(1.65,3.0);y=random.uniform(-3.2,7)
 o=sphere('Loose ochre shale',(x,y,.06),(.07+random.random()*.1,.07+random.random()*.1,.05+random.random()*.08),rock,seg=8,rings=4)
 o.rotation_euler=(random.random(),random.random(),random.random())
# Supply corner.
for i,(xyz,size) in enumerate([((-1.6,3.65,.35),(1.0,.7,.7)),((-1.92,4.25,.92),(.65,.62,.46))]):
 c=cube('Supply crate '+str(i),xyz,size,crateMat,bevel=.025);c['collision']=True;c['set_ink']=True
 for zoff in [-.22,.02,.23]:line('Crate plank joint',[(xyz[0]-.47,xyz[1]-.355,xyz[2]+zoff),(xyz[0]+.47,xyz[1]-.355,xyz[2]+zoff)],.004,timber)
 for xoff in [-.4,.4]:cube('Crate upright batten',(xyz[0]+xoff,xyz[1]-.37,xyz[2]),(.07,.035,size[2]-.03),timber,bevel=.008)
 if i==0:
  cu=bpy.data.curves.new('Native crate stencil','FONT');cu.body='CANDLES';cu.size=.095;cu.extrude=.0001;cu.align_x='CENTER'
  text=obj('CANDLES / scene-native crate stencil',cu);cu.materials.append(dark);text.location=(xyz[0],xyz[1]-.391,.33);text.rotation_euler=(math.pi/2,0,0)
kettle=obj('Blue kettle assembly');kettle.location=(-1.65,3.65,.78)
sphere('Enamel kettle body',(0,0,.10),(.14,.12,.15),blue,kettle,outline=.003)
loft('Kettle lid',[(.2,.13,.11),(.23,.09,.08)],blue,kettle,outline=.002)
sphere('Kettle lid knob',(0,0,.26),(.026,.026,.025),dark,kettle,seg=12,rings=6)
line('Kettle pouring spout',[(.1,0,.08),(.2,0,.15),(.24,0,.22)],.035,blue,kettle)
line('Kettle arched handle',[(-.13,0,.12),(-.15,0,.30),(0,0,.37),(.15,0,.30),(.13,0,.12)],.012,dark,kettle)
for x in [-1.3,-1.1]:cylinder('Tin supply cup',(x,3.48,.72),(x,3.48,.84),.045,steel)
# Stump seat with top rings and visibly supported seated pelvis.
stump=cylinder('Buddy stump support',(-.52,3.45,0),(-.52,3.45,.63),.27,timber,verts=32,outline=.004);stump['collision']=True
for rad in [.10,.17,.23]:line('Stump growth ring',[(-.52+rad*math.cos(i*math.tau/48),3.45+rad*math.sin(i*math.tau/48),.635) for i in range(49)],.0035,crateMat)
# Practical lamp housing overhead and a translucent tapered cone, no opaque smoke.
lamp=obj('Ceiling lamp assembly');lamp.location=(0,0,2.98)
cylinder('Lamp suspension',(0,0,0),(0,0,.32),.012,steel,lamp,verts=12)
loft('Circular overhead shade',[(-.04,.26,.26),(.03,.28,.28),(.13,.13,.13)],steel,lamp,n=32)
sphere('Overhead glowing lens',(0,0,-.035),(.22,.22,.025),glow,lamp,seg=24,rings=8)
spot=light('Motivated overhead spot','SPOT',(0,-.12,2.89),(0,.2,0),980,'#FFD488',.10)
spot.data.spot_size=math.radians(74)
# Subtle cone surface is additive-looking transparent emission, not volumetric fog.
coneMat=bpy.data.materials.new('Fine dust lamp cone');coneMat.use_nodes=True;coneMat.surface_render_method='BLENDED'
n=coneMat.node_tree.nodes;n.clear();l=coneMat.node_tree.links;tr=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=look.rgba('#F4D6A6');em.inputs[1].default_value=.45
mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.048;l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);out=n.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],out.inputs[0])
vs=[]
for z,rad in [(2.92,.10),(.12,1.10)]:
 for j in range(32):a=j*math.tau/32;vs.append((rad*math.cos(a),rad*math.sin(a),z))
cone=mesh('Overhead dust cone',vs,[(j,(j+1)%32,(j+1)%32+32,j+32) for j in range(32)],coneMat);look.mark_role(cone,'wisp')
# Candle near the impact receiver.
cube('Candle sconce wall plate',(.99,4.78,1.77),(.11,.04,.25),steel,bevel=.01)
line('Candle sconce arm',[(.99,4.75,1.7),(.99,4.52,1.7)],.014,steel)
cylinder('Wax candle',(.99,4.51,1.72),(.99,4.51,1.93),.037,white,verts=16)
flame=sphere('Candle amber flame',(.99,4.51,1.975),(.026,.023,.064),glow,seg=16,rings=8)
for v in flame.data.vertices:v.co.x*=.7-.3*v.co.z/.064
light('Candle practical','POINT',(.99,4.48,2.0),(.99,4,1.7),22,'#FFA64A').data.shadow_soft_size=.08
# Red oil lantern hanging above the supply corner.
lantern=obj('Red oil lantern');lantern.location=(-1.5,3.9,2.15)
for z in [-.14,.14]:cylinder('Red lantern cap',(0,0,z-.025),(0,0,z+.025),.095,lanternred,lantern,verts=20,outline=.002)
sphere('Lantern amber glass',(0,0,0),(.07,.07,.13),glow,lantern,seg=20,rings=10)
for x in [-.08,.08]:line('Lantern iron guard',[(x,0,-.15),(x,0,.15)],.008,lanternred,lantern)
line('Lantern hanging loop',[(-.07,0,.15),(-.10,0,.26),(0,0,.31),(.10,0,.26),(.07,0,.15)],.009,steel,lantern)
light('Lantern practical','POINT',(-1.5,3.78,2.15),(-.5,3.4,1.3),65,'#FFA64A').data.shadow_soft_size=.15
light('Buddy warm portrait bounce','AREA',(-.9,2.6,2.8),(-.5,3.45,1.3),72,'#FFD488',.10)
light('Miner warm face bounce','AREA',(-1.1,-1.45,2.45),(0,0,1.4),86,'#FFD488',.12)
light('Cool tunnel separation','AREA',(1.4,2.4,2.4),(0,0,1.4),12,'#4D5B82',2)
# Retain the actual shadow-casting overhead, candle and actor keys; broad bounce does not need shadow maps.
for name in ['Lantern practical','Cool tunnel separation','Candle practical']:
 bpy.data.objects[name].data.use_shadow=False
# The shared directional rig is retained as quiet warm/cool fill inside the enclosed set.
bpy.data.objects['Ricks key'].data.energy=.35;bpy.data.objects['Ricks cool fill'].data.energy=.12
def make_actor(name,position,buddy=False):
 root=obj(name+' root');root.location=position;root['ricks_role']='actor'
 body=obj(name+' body',parent=root)
 head=obj(name+' head pivot',parent=body);head.location=(0,0,1.49)
 skull=sphere(name+' rough-round head',(0,0,0),(.32,.255,.32),skin,head,48,20)
 for v in skull.data.vertices:a=math.atan2(-v.co.z,v.co.x);rr=rough(a);v.co.x*=rr;v.co.z*=rr
 ink(skull,.009)
 sphere(name+' neck',(0,0,1.21),(.075,.07,.12),skin,body,seg=20,rings=10,outline=.004)
 shirt=loft(name+' contoured shirt',[(.69,.18,.11),(.72,.22,.13),(.79,.23,.14),(1.09,.255,.13),(1.18,.22,.105),(1.23,.12,.075)],teal if buddy else red,body,n=32,outline=.006)
 pelvis=sphere(name+' connected pelvis',(0,0,.665),(.185,.12,.11),dark,body,outline=.004)
 if not buddy:
  for x in [-.17,-.11,-.05,.05,.11,.17]:
   pts=[]
   for j in range(20):z=.76+j*.39/19;rx=.23;pts.append((x,-.14*math.sqrt(max(.03,1-(x/rx)**2))-.002,z))
   line('Flannel fine vertical stripe',pts,.0035,wood,body)
  for z in [.83,.95,1.07]:
   pts=[(x,-.143*math.sqrt(max(.03,1-(x/.25)**2))-.002,z) for x in [-.21+i*.42/24 for i in range(25)]]
   line('Flannel horizontal check',pts,.003,wood,body)
  for x in [-.105,.105]:
   line('Cream suspender',[(x,-.154,.75),(x,-.153,1.08),(x*.85,-.112,1.19)],.014,stripe,body)
   cube('Suspender metal clip',(x,-.17,.78),(.035,.015,.045),gold,body,bevel=.006)
  cube('Miner leather belt',(0,-.005,.72),(.43,.27,.065),wood,body,bevel=.02,outline=.003)
  cube('Miner brass buckle',(0,-.155,.72),(.08,.02,.055),gold,body,bevel=.01)
 else:
  line('Sweater neck rib',[(-.085,-.08,1.205),(0,-.115,1.18),(.085,-.08,1.205)],.008,dark,body)
 for side in [-1,1]:
  arm=line(name+(' L arm' if side<0 else ' R arm'),[(side*.24,0,1.10)]*20,.026,dark,root)
  # Rounded hands live in semantic grip frames; fingers wrap actual surfaces.
  hand=obj(name+(' L hand frame' if side<0 else ' R hand frame'),parent=root)
  sphere(name+' palm',(0,.024,0),(.044,.028,.043),skin,hand,seg=16,rings=8,outline=.003)
  for i in range(3):
   line(name+' wrapping finger '+str(i),[(.038*math.cos(a),.026*math.sin(a),-.025+i*.025) for a in [-.3+j*math.pi*1.55/16 for j in range(17)]],.010,skin,hand)
  leg=line(name+(' L leg' if side<0 else ' R leg'),[(0,0,0)]*20,.032,dark,root)
  boot=sphere(name+(' L boot' if side<0 else ' R boot'),(side*.16,-.04,.045),(.067,.11,.044),dark,root,seg=20,rings=10,outline=.003)
  # Support-local dark grounding discs do not cast secondary shadows.
  contact=sphere(name+(' L sole contact' if side<0 else ' R sole contact'),(side*.16,-.04,.004),(.09,.13,.003),dark,root,seg=16,rings=6)
  look.mark_role(contact,'ink')
 # Eyes are conformed surface patches and separate closed strokes, never floating brackets.
 for side in [-1,1]:
  x=side*.108
  oval(name+(' L eye' if side<0 else ' R eye'),x,.028,.025,.037 if buddy else .025,BLACK,head)
  oval(name+(' L glint' if side<0 else ' R glint'),x-.006,.033,.004,.005,CREAM,head,.008)
  faceline(name+(' L brow' if side<0 else ' R brow'),[(x-.048,.113),(x,.12 if buddy else .105),(x+.048,.113 if buddy else .09)],.0075,BLACK,head)
  faceline(name+(' L closed' if side<0 else ' R closed'),[(x-.03,.028),(x,.014),(x+.03,.028)],.005,BLACK,head)
 # Mouth states are static, fully conformed patches: actual audio selects shapes.
 faceline(name+' mouth 0',[(-.06,-.109),(-.02,-.108),(.035,-.110),(.06,-.111)] if buddy else [(-.06,-.104),(-.02,-.116),(.035,-.113),(.067,-.093)],.006,BLACK,head)
 for k,(rx,rz) in enumerate([(.045,.024),(.063,.038),(.055,.057),(.075,.043)],1):
  oval(name+' mouth '+str(k),0,-.11,rx,rz,BLACK,head)
  if k in (2,4):patch(name+' teeth '+str(k),[(-rx*.72,-.11+rz*.75),(rx*.72,-.11+rz*.75),(rx*.63,-.11+rz*.25),(-rx*.63,-.11+rz*.25)],CREAM,head,.009)
  if k==3:oval(name+' tongue 3',.008,-.139,.027,.015,red,head,.010)
 if buddy:
  # Beanie crown with a clean lower cuff; black stripes stay inside the knit.
  cap=loft('Buddy beanie crown',[(.19,.29,.23),(.25,.29,.23),(.33,.26,.20),(.40,.19,.15),(.435,.07,.06)],yellow,head,n=48,outline=.006)
  loft('Buddy black beanie cuff',[(.17,.305,.278),(.23,.305,.270)],dark,head,n=48,outline=.003)
  loft('Buddy yellow cuff stripe',[(.188,.309,.282),(.211,.309,.277)],yellow,head,n=48,outline=0)
  for j in range(26):
   a=j*math.tau/26
   line('Beanie knitted rib',[(rx*math.cos(a),ry*math.sin(a),z) for z,rx,ry in [(.24,.29,.23),(.31,.27,.21),(.38,.21,.165),(.42,.12,.10)]],.0018,stripe,head)
  # Three connected, tapered curved tufts; no repeated circular beads.
  for x,side in [(-.205,-1),(.005,1),(.205,1)]:
   coords=[(x-.05,.181),(x+.045,.183)]
   for controls in [[(.045,.183),(.040,.155),(.020,.137),(.002,.144)],[(.002,.144),(.005,.162),(-.028,.148),(-.05,.181)]]:
    for j in range(1,9):
     t=j/8;a,b,c,d=controls;coords.append((x+(1-t)**3*a[0]+3*(1-t)**2*t*b[0]+3*(1-t)*t*t*c[0]+t**3*d[0],(1-t)**3*a[1]+3*(1-t)**2*t*b[1]+3*(1-t)*t*t*c[1]+t**3*d[1]))
   patch('Buddy smooth hair tuft',coords,BLACK,head,.008)
 else:
  vs=[];fs=[]
  for rad in [.0,.65,1]:
   for j in range(48):a=j*math.tau/48;vs.append((.40*rad*math.cos(a),(.36 if math.sin(a)<0 else .25)*rad*math.sin(a),.205+.03*rad*rad*abs(math.cos(a))**3))
  for i in range(2):
   for j in range(48):a=i*48+j;b=i*48+(j+1)%48;fs.append((a,b,b+48,a+48))
  brim=mesh('Miner physical hat brim',vs,fs,hat,head,outline=0)
  mod=brim.modifiers.new('Felt physical thickness','SOLIDIFY');mod.thickness=.012
  bpy.context.view_layer.objects.active=brim;bpy.ops.object.modifier_apply(modifier=mod.name);ink(brim,.005)
  loft('Miner pinched hat crown',[(.21,.23,.22),(.26,.23,.20),(.35,.21,.17),(.39,.19,.14)],hat,head,n=32,outline=.005)
  loft('Miner dark hatband',[(.215,.235,.225),(.265,.233,.205)],wood,head,n=32,outline=.002)
  cylinder('Round golden headlamp badge',(0,-.229,.29),(0,-.248,.29),.055,gold,head,verts=24,outline=.002)
  cylinder('Headlamp cream lens',(0,-.25,.29),(0,-.255,.29),.030,glow,head,verts=24)
 return root
miner=make_actor('Miner',(0,0,0));buddy=make_actor('Buddy',(-.52,3.45,0),True)
# Shotgun: stable physical dimensions, barrel hinge and named real surface grips.
gun=obj('Shotgun root')
gun['physical_length_m']=1.19
receiver=cube('Shotgun steel receiver',(0,-.04,0),(.115,.24,.10),steel,gun,bevel=.018,outline=.003)
stock=sphere('Shotgun shaped walnut stock',(0,-.285,-.035),(.046,.19,.073),wood,gun,seg=24,rings=12,outline=.003)
cube('Shotgun butt pad',(0,-.46,-.035),(.09,.025,.135),dark,gun,bevel=.015,outline=.002)
cube('Shotgun wrist grip',(0,-.13,-.075),(.065,.14,.14),wood,gun,bevel=.025,outline=.002)
barrels=obj('Shotgun barrel hinge',parent=gun);barrels.location=(0,.06,0)
for x in [-.031,.031]:
 cylinder('Shotgun steel barrel',(x,0,.015),(x,.74,.015),.024,steel,barrels,verts=24,outline=.0018)
 cylinder('Shotgun dark bore',(x,.741,.015),(x,.744,.015),.0185,BLACK,barrels,verts=24)
cube('Shotgun wooden forend',(0,.30,-.035),(.105,.34,.075),wood,barrels,bevel=.025,outline=.002)
line('Shotgun trigger guard',[(-.03,-.17,-.09),(-.03,-.14,-.17),(-.03,-.02,-.17),(-.03,.015,-.085)],.009,steel,gun)
line('Shotgun trigger',[(0,-.08,-.08),(0,-.08,-.135)],.007,steel,gun)
right=obj('Shotgun trigger surface grip',parent=gun);right.location=(0,-.135,-.065)
left=obj('Shotgun forend surface grip',parent=barrels);left.location=(0,.32,-.03)
muzzle=obj('Shotgun muzzle anchor',parent=barrels);muzzle.location=(0,.75,.015)
shell=obj('Gold shell root')
cylinder('Gold shell brass barrel',(0,0,-.065),(0,0,.055),.024,gold,shell,verts=24,outline=.0016)
cylinder('Gold shell rim',(0,0,-.067),(0,0,-.057),.029,gold,shell,verts=24)
sphere('Gold shell golden load',(0,0,.06),(.023,.023,.02),gold,shell,seg=16,rings=8)
shellGrip=obj('Gold shell surface grip',parent=shell);shellGrip.location=(0,0,-.015)
# White mug with a real hollow cavity and front/back finger ordering around its handle.
mug=obj('Buddy mug root')
vs=[];fs=[];n=32
for z,r in [(-.10,.072),(-.085,.082),(.10,.086),(.10,.069),(-.075,.066)]:
 for j in range(n):a=j*math.tau/n;vs.append((r*math.cos(a),r*math.sin(a),z))
for i in range(4):
 for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
fs.append(tuple(range(4*n,5*n)))
mesh('Hollow ceramic mug',vs,fs,white,mug,outline=.002)
cylinder('Coffee surface',(0,0,.064),(0,0,.067),.067,wood,mug,verts=32)
line('Ceramic mug handle',[(.081+.048*math.cos(a),0,.004+.063*math.sin(a)) for a in [-math.pi/2+i*math.pi/24 for i in range(25)]],.014,white,mug)
gr=obj('Mug handle surface grip',parent=mug);gr.location=(.13,0,.004)
# Buddy's lap is intentionally clear.
# Impact cavity and cracks have persistent embedded gold after the shot.
impact=obj('Impact persistent assembly');impact.location=(.55,4.805,1.60)
contour=[]
for j in range(19):
 a=j*math.tau/19;r=.145*(1+random.uniform(-.18,.20));contour.append((r*math.cos(a),r*.83*math.sin(a)))
vsR=[(x,-.04+random.uniform(-.015,.01),z) for x,z in contour]+[(x*.63,.060,z*.63) for x,z in contour]
facesR=[(j,(j+1)%19,(j+1)%19+19,j+19) for j in range(19)]
mesh('Jagged recessed crater rim',vsR,facesR,rock,impact,outline=.002,smooth=False)
mesh('Recessed dark crater core',[(x*.70,.068,z*.70) for x,z in contour],[tuple(range(19))],scar,impact,smooth=False)
# A removable rock skin covers the cavity before the strike.
cover=mesh('Unbroken strike surface',[(x+.55,4.755,z+1.6) for x,z in contour],[tuple(range(19))],rock,smooth=False)
for i,(a,length) in enumerate([(.32,.32),(1.91,.21),(3.35,.37),(4.65,.26)]):
 pts=[]
 for j in range(5):
  r=.115+j*length/4;ang=a+random.uniform(-.18,.18);pts.append((r*math.cos(ang),-.026+random.uniform(-.008,.004),r*math.sin(ang)))
 line('Natural fractured seam '+str(i),pts,.0032,scar,impact)
 if i%2==0:
  p=V(pts[2]);line('Fracture fine branch',[p,p+V((.035,-.002,.045)),p+V((.08,0,.073))],.0016,scar,impact)
for i in range(20):
 a=random.random()*math.tau;r=random.uniform(.015,.093)
 o=sphere('Persistent embedded gold '+str(i),(r*math.cos(a),.036,r*.83*math.sin(a)),(.009,.008,.014),gold,impact,seg=8,rings=4)
 o.rotation_euler.y=random.random()*math.pi;o['deposit_rest']=list(o.location)
# Spark particles and elongated streaks follow deterministic physical trajectories.
for i in range(24):
 sphere('Flying gold '+str(i),(0,0,0),(.019,.035,.018),goldglow,seg=8,rings=4)
 line('Gold streak '+str(i),[(0,0,0),(0,0,.1)],.006,goldglow)
for i in range(9):
 sphere('Rock scatter '+str(i),(0,0,0),(.028,.024,.022),rock,seg=8,rings=4)
smokeMat=coneMat.copy();smokeMat.name='Thin dissipating impact smoke';next(n for n in smokeMat.node_tree.nodes if n.type=='MIX_SHADER').inputs[0].default_value=.009
for i in range(5):
 sphere('Thin impact wisp '+str(i),(0,0,0),(.08,.06,.10),smokeMat,seg=16,rings=8);look.mark_role(bpy.context.object,'smoke')
flash=obj('Muzzle flare root')
for label,mat,factor in [('Orange flame envelope',orangeFire,1),('Golden flame core',hot,.55)]:
 vv=[];ff=[];nr=12
 for y,r in [(0,.015),(.10,.060),(.30,.027),(.62,.001)]:
  for j in range(nr):
   a=j*math.tau/nr;rr=r*(1+.28*math.sin(a*3+y*20))*factor;vv.append((rr*math.cos(a),y*(.90 if factor<1 else 1),rr*math.sin(a)))
 for k in range(3):
  for j in range(nr):a=k*nr+j;b=k*nr+(j+1)%nr;ff.append((a,b,b+nr,a+nr))
 o=mesh(label,vv,ff,mat,flash,smooth=True);look.mark_role(o,'streak')
flashLight=light('Blast light','POINT',(0,1,1.5),(0,2,1.5),0,'#FFBD60');flashLight.data.shadow_soft_size=.12;flashLight.data.use_shadow=False
# Final camera uses shared sensor / optics. No camera noise, only motivated finite moves.
camdata=bpy.data.cameras.new('Portrait cinema');cam=obj('Story camera',camdata);S.camera=cam
focus=obj('Story focus');look.configure_camera(cam,focus,lens=45,fstop=3.5);cam.data.sensor_width=20.25
# Bold non-shadowing hulls cover every hero prop, including curved handles.
def outlined_prop(o):
 if o.type=='CURVE':
  bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
  me=bpy.data.meshes.new_from_object(ev);name=o.name;parent=o.parent;basis=o.matrix_basis.copy()
  bpy.data.objects.remove(o,do_unlink=True);o=obj(name,me,parent);o.matrix_basis=basis
 if o.type=='MESH' and not o.get('ricks_role')=='ink':
  o['bold_prop']=True;o['set_ink']=False
  if not any(c.get('ink_base_width') for c in o.children):ink(o,.004)
 return o
for root in [gun,shell,mug,kettle,lantern]:
 for o in list(root.children_recursive):
  if o.get('ricks_role')=='ink' or o.type not in {'MESH','CURVE'}:continue
  if 'glass' in o.name.lower():continue
  outlined_prop(o)
for o in list(S.objects):
 if o.name.startswith(('Supply crate','Crate upright batten','Tin supply cup')):outlined_prop(o)
for h in [O for O in S.objects if O.name.startswith('Buddy') and O.get('ricks_role')!='ink' and ('palm' in O.name or 'wrapping finger' in O.name)]:
 h.data.materials.clear();h.data.materials.append(glove)
for o in S.objects:
 if o.name.startswith(('Miner physical hat brim','Miner pinched hat crown','Buddy beanie crown','Buddy black beanie cuff','Buddy yellow cuff stripe')) and not o.get('ricks_role')=='ink':o.visible_shadow=True
 # Candle and its complete sconce never occlude their own practical light.
 if o.name.startswith(('Candle sconce','Candle amber flame','Wax candle')):o.visible_shadow=False
 # Eyes and drawn expression decals receive their authored color without
 # casting detached little geometric shadows across the cheek surface.
 if o.name.startswith(('Miner','Buddy')) and any(x in o.name for x in [' eye',' glint',' brow',' closed',' mouth',' teeth',' tongue',' hair tuft']):o.visible_shadow=False
# Tag all cast descendants and all nonreceiving ink / FX explicitly.
for root in [miner,buddy]:
 for o in root.children_recursive:
  if not o.get('ricks_role'):look.mark_role(o,'actor')
for o in list(S.objects):
 if 'streak' in o.name.lower() or 'flare' in o.name.lower():look.mark_role(o,'streak')
# Evaluate moving props as camera obstacles as well as static architecture.
for root in [gun,mug,kettle,shell]:
 for o in root.children_recursive:
  if o.type=='MESH' and o.get('ricks_role')!='ink':o['collision']=True
exec(compile((D/'upgrade_geometry.py').read_text(),'upgrade_geometry.py','exec'))
exec(compile((D/'flat_cast.py').read_text(),'flat_cast.py','exec'))
# Original procedural assets: no downloaded images or unknown licenses.
asset=gate.sanitize_assets(S,[]);resources=gate.validate_resources(S)
(P/'asset_report.json').write_text(json.dumps({'license':'All geometry, procedural surfaces, foley and underscore authored for this production; no external assets.','sanitation':asset,'resources':resources},indent=2))
assert resources['pass'],resources
for fname in ['geometry.py','runtime.py']:
 t=bpy.data.texts.new('gold_mine_'+fname);t.from_string((D/fname).read_text())
for name,path in [('ricks_lookdev.py',R/'scripts/ricks_lookdev.py'),('audio_envelope.json',P/'audio_envelope.json'),('set_ink.py',R/'scripts/studio/set_ink.py')]:
 t=bpy.data.texts.new(name);t.from_string(path.read_text())
bootstrap="""# Run this text once after reopening to activate the self-contained story runtime.
import bpy,types,sys
for module_name,text_name in [('ricks_lookdev','ricks_lookdev.py'),('geometry','gold_mine_geometry.py'),('set_ink','set_ink.py')]:
    module=types.ModuleType(module_name);sys.modules[module_name]=module
    exec(compile(bpy.data.texts[text_name].as_string(),text_name,'exec'),module.__dict__)
exec(compile(bpy.data.texts['gold_mine_runtime.py'].as_string(),'gold_mine_runtime.py','exec'))
"""
t=bpy.data.texts.new('START_HERE.py');t.from_string(bootstrap)
# The original mix is packed for an editable self-contained audio strip.
seq=S.sequence_editor_create();strip=seq.sequences.new_sound('Supplied narration + original foley',str(P/'final_mix.wav'),channel=1,frame_start=1);strip.sound.pack()
S.render.use_sequencer=False
exec(compile(bootstrap,'START_HERE.py','exec'))
S.frame_set(1);update(1)
S['production']='gold_mine_salting_v3';S['subtitles']=False;S['runtime_instructions']='Run packed START_HERE.py once after opening. All dependencies and audio are embedded.'
S.render.fps=30;S.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(P/'gold_mine_salting_v3.blend'))
print('BUILD_OK',resources,flush=True)
