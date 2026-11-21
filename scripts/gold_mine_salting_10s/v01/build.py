import bpy,sys,math,json,random,types
from pathlib import Path
from mathutils import Vector as V
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;P=R/'renders/gold_mine_salting_10s/v01'
sys.path[:0]=[str(R/'scripts'),str(D)]
import ricks_lookdev as look, shorts_preflight as gate
from geometry import *
random.seed(1899)
# Factory source only. No approved scene is loaded or edited.
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
S=bpy.context.scene;look.setup_scene(S,actor_height=1.88,frame_end=301,samples=12)
S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB';S.render.image_settings.compression=0
S.render.film_transparent=False
INK=emission('Marker ink','#211B29');INK.use_backface_culling=True;INK.use_backface_culling_shadow=True
BLACK=emission('Features ink','#211B29');CREAM=emission('Eye cream','#FDF5EF')
skin=look.clean_toon('Warm cream received skin','skin',light_min=.65,light_max=1.2)
look.protect_lower_face(skin,.58,.62)
red=look.clean_toon('Flannel red',stops=[(0,'#6C243B'),(.4,'#A82737'),(1,'#D43B45')],light_min=.06,light_max=.65)
teal=look.clean_toon('Buddy teal',stops=[(0,'#246A81'),(.5,'#298E93'),(1,'#47AAA6')],light_min=.06,light_max=.65)
hat=look.clean_toon('Weathered brown felt','vest',.06,.5)
yellow=look.clean_toon('Knitted ochre',stops=[(0,'#866231'),(.38,'#D0A02C'),(1,'#F5CD58')],light_min=.07,light_max=.6)
dark=look.metal('Dark soft boots','#26232E',0,.93)
wood=look.metal('Oiled gun walnut','#6E3C29',0,.65)
steel=look.metal('Charcoal steel','#424855',.48,.30,emission_strength=.09)
gold=look.metal('Solid brass gold','#F2C854',.42,.28,emission_strength=.3)
white=look.clean_toon('Ceramic cream',stops=[(0,'#98A7BD'),(.5,'#F3EEE0'),(1,'#FFFBEE')],light_min=.05,light_max=.52)
stripe=look.clean_toon('Cream suspenders',stops=[(0,'#9B8792'),(1,'#EACB98')],light_min=.07,light_max=.5)
lanternred=look.metal('Painted red enamel','#96352B',.1,.6)
blue=look.metal('Blue enamel kettle','#356786',.25,.3)
glow=emission('Amber lamp glow','#FFD084',3.5)
goldglow=emission('Gold spark glow','#FFC95A',1.35)
hot=emission('Muzzle hot center','#FFF1BC',5)
def texture(name,c0,c1,scale=3,bump=.12):
 m=look.metal(name,c0,0,.9);nt=m.node_tree;n=nt.nodes;l=nt.links;bs=next(x for x in n if x.type=='BSDF_PRINCIPLED')
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3;tex.inputs['Roughness'].default_value=.72
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=look.rgba(c0);ramp.color_ramp.elements[1].color=look.rgba(c1)
 l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
 b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.045;l.new(tex.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],bs.inputs['Normal'])
 return m
rock=texture('Ochre cavern rock','#382F2B','#896541',3,.28)
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
back=cube('Strike wall',(.85,5.05,1.58),(4.9,.45,3.15),rock,bevel=.14);back['collision']=True
# Sculpted strata over the protected collision backing.
vs=[];fs=[]
for iz in range(6):
 for ix in range(9):
  x=-1.6+ix*.61;z=iz*.63;y=4.81+random.uniform(-.015,.075)
  vs.append((x,y,z))
for iz in range(5):
 for ix in range(8):
  a=iz*9+ix;fs.extend([(a,a+1,a+10),(a,a+10,a+9)])
relief=mesh('Sculpted ochre strike strata',vs,fs,rock,smooth=False);relief['collision']=True
for z in [.5,1.13,2.4]:
 line('Broad natural sediment seam',[(x,4.79,z+.035*math.sin(x*3)) for x in [-1.4+j*.18 for j in range(25)]],.0035,timber)
deep=cube('Cool black tunnel depth',(-2.1,9,1.4),(2.3,.3,3.0),scar,bevel=0);deep['collision']=True
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
spot=light('Motivated overhead spot','SPOT',(0,-.12,2.89),(0,.2,0),780,'#FFD49B',.10)
spot.data.spot_size=math.radians(74)
# Subtle cone surface is additive-looking transparent emission, not volumetric fog.
coneMat=bpy.data.materials.new('Fine dust lamp cone');coneMat.use_nodes=True;coneMat.surface_render_method='BLENDED'
n=coneMat.node_tree.nodes;n.clear();l=coneMat.node_tree.links;tr=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=look.rgba('#F4D6A6');em.inputs[1].default_value=.45
mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.022;l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);out=n.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],out.inputs[0])
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
light('Candle practical','POINT',(.99,4.48,2.0),(.99,4,1.7),46,'#FFBD6B').data.shadow_soft_size=.08
# Red oil lantern hanging above the supply corner.
lantern=obj('Red oil lantern');lantern.location=(-1.5,3.9,2.15)
for z in [-.14,.14]:cylinder('Red lantern cap',(0,0,z-.025),(0,0,z+.025),.095,lanternred,lantern,verts=20,outline=.002)
sphere('Lantern amber glass',(0,0,0),(.07,.07,.13),glow,lantern,seg=20,rings=10)
for x in [-.08,.08]:line('Lantern iron guard',[(x,0,-.15),(x,0,.15)],.008,lanternred,lantern)
line('Lantern hanging loop',[(-.07,0,.15),(-.10,0,.26),(0,0,.31),(.10,0,.26),(.07,0,.15)],.009,steel,lantern)
light('Lantern practical','POINT',(-1.5,3.78,2.15),(-.5,3.4,1.3),60,'#FFC17C').data.shadow_soft_size=.15
light('Buddy warm portrait bounce','AREA',(-.5,1.9,2.5),(-.5,3.45,1.3),45,'#FFD8AA',.7)
light('Miner warm face bounce','AREA',(0,-.7,2.65),(0,0,1.4),45,'#FFE2BA',.55)
light('Cool tunnel separation','AREA',(-2.2,4.2,2.4),(0,0,1.4),150,'#7A9BD5',2)
# Retain the actual shadow-casting overhead, candle and actor keys; broad bounce does not need shadow maps.
for name in ['Lantern practical','Cool tunnel separation']:
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
  loft('Buddy black beanie cuff',[(.19,.30,.235),(.23,.30,.235)],dark,head,n=48,outline=.003)
  loft('Buddy yellow cuff stripe',[(.208,.304,.239),(.22,.304,.239)],yellow,head,n=48,outline=0)
  for j in range(26):
   a=j*math.tau/26
   line('Beanie knitted rib',[(rx*math.cos(a),ry*math.sin(a),z) for z,rx,ry in [(.24,.29,.23),(.31,.27,.21),(.38,.21,.165),(.42,.12,.10)]],.0018,stripe,head)
  # Stable dark fringe under cuff.
  for x in [-.21,-.14,-.07,0,.07,.14,.21]:oval('Buddy dark fringe',x,.173,.032,.034,dark,head)
 else:
  vs=[];fs=[]
  for rad in [.0,.65,1]:
   for j in range(48):a=j*math.tau/48;vs.append((.40*rad*math.cos(a),(.36 if math.sin(a)<0 else .25)*rad*math.sin(a),.205+.03*rad*rad*abs(math.cos(a))**3))
  for i in range(2):
   for j in range(48):a=i*48+j;b=i*48+(j+1)%48;fs.append((a,b,b+48,a+48))
  brim=mesh('Miner physical hat brim',vs,fs,hat,head,outline=.005)
  mod=brim.modifiers.new('Felt physical thickness','SOLIDIFY');mod.thickness=.012
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
stock=sphere('Shotgun shaped walnut stock',(0,-.32,-.045),(.068,.24,.10),wood,gun,seg=24,rings=12,outline=.003)
cube('Shotgun butt pad',(0,-.53,-.045),(.12,.035,.17),dark,gun,bevel=.02,outline=.002)
cube('Shotgun wrist grip',(0,-.13,-.075),(.065,.14,.14),wood,gun,bevel=.025,outline=.002)
barrels=obj('Shotgun barrel hinge',parent=gun);barrels.location=(0,.06,0)
for x in [-.031,.031]:
 cylinder('Shotgun steel barrel',(x,0,.015),(x,.74,.015),.029,steel,barrels,verts=24,outline=.0018)
 cylinder('Shotgun dark bore',(x,.741,.015),(x,.744,.015),.022,BLACK,barrels,verts=24)
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
snack=cube('Buddy lap snack pouch',(-.52,3.15,.76),(.17,.12,.18),crateMat,bevel=.03,outline=.003)
# Impact cavity and cracks have persistent embedded gold after the shot.
impact=obj('Impact persistent assembly');impact.location=(.55,4.805,1.60)
hole=sphere('Dark struck crater',(0,-.016,0),(.13,.026,.115),scar,impact,seg=24,rings=12)
for i in range(9):
 a=i*math.tau/9+.12;length=random.uniform(.27,.53)
 pts=[(0,-.04,0),(.11*math.cos(a),-.04,.11*math.sin(a)),(.21*math.cos(a+.13),-.035,.21*math.sin(a+.13)),(length*math.cos(a),-.03,length*math.sin(a))]
 line('Radiating rock crack '+str(i),pts,.007,scar,impact)
 line('Embedded fine gold vein '+str(i),[(x,y-.006,z) for x,y,z in pts[:3]],.0024,gold,impact)
for i in range(24):
 a=random.random()*math.tau;r=random.uniform(.02,.20)
 o=sphere('Persistent embedded gold '+str(i),(r*math.cos(a),-.06,r*math.sin(a)),(.015,.009,.022),gold,impact,seg=8,rings=4);o.rotation_euler.y=random.random()*math.pi
# Spark particles and elongated streaks follow deterministic physical trajectories.
for i in range(16):
 sphere('Flying gold '+str(i),(0,0,0),(.019,.035,.018),goldglow,seg=8,rings=4)
 line('Gold streak '+str(i),[(0,0,0),(0,0,.1)],.006,goldglow)
for i in range(9):
 sphere('Rock scatter '+str(i),(0,0,0),(.028,.024,.022),rock,seg=8,rings=4)
for i in range(5):
 sphere('Thin impact wisp '+str(i),(0,0,0),(.12,.025,.08),coneMat,seg=16,rings=8);look.mark_role(bpy.context.object,'smoke')
flash=obj('Muzzle flare root')
for k in range(5):
 a=k*math.tau/5
 mesh('Pointed muzzle flame',[(0,0,0),(.055*math.cos(a),.1,.055*math.sin(a)),(0,.30 if k%2 else .22,0),(.055*math.cos(a+1),.1,.055*math.sin(a+1))],[(0,1,2,3)],hot,flash)
flashLight=light('Blast light','POINT',(0,1,1.5),(0,2,1.5),0,'#FFBD60');flashLight.data.shadow_soft_size=.12;flashLight.data.use_shadow=False
# Final camera uses shared sensor / optics. No camera noise, only motivated finite moves.
camdata=bpy.data.cameras.new('Portrait cinema');cam=obj('Story camera',camdata);S.camera=cam
focus=obj('Story focus');look.configure_camera(cam,focus,lens=45,fstop=3.5);cam.data.sensor_width=20.25
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
S['production']='gold_mine_salting_10s/v01';S['subtitles']=False;S['runtime_instructions']='Run packed START_HERE.py once after opening. All dependencies and audio are embedded.'
S.render.fps=30;S.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(P/'gold_mine_salting_v01.blend'))
print('BUILD_OK',resources,flush=True)
