"""Original four-stage ₹5 story. Approved productions are never loaded or edited."""
import bpy,sys,math,json,random
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent
P=R/'renders/project_paradox_india_ep03_5rs_blade/v01'
sys.path[:0]=[str(R/'scripts'),str(D)]
import ricks_lookdev as look,shorts_preflight as gate
import geometry as G
from geometry import *
random.seed(509)
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
S=bpy.context.scene;look.setup_scene(S,frame_end=1401,samples=32)
S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB';S.render.image_settings.compression=15
outdoor=S.world;outdoor.name='Sunny Indian lane world'
look.apply_lighting_preset(S,'INTERIOR_WARM_CAVERN');indoor=S.world;indoor.name='Workshop slate interior world';indoor.use_fake_user=True
S.world=outdoor;look.install_post(S,replace=True)
for o in S.objects:
 if o.get('ricks_light'):o.hide_render=o.hide_viewport=False
INK=emission('Marker ink','#16121C');INK.use_backface_culling=True
BLACK=emission('Graphic limbs and features','#211B28');CREAM=emission('Graphic cream face','#FDF5EF')
SHADE=emission('Restrained cool face crescent','#D2D3E7')
white=look.clean_toon('White cotton',stops=[(0,'#9295AF'),(.3,'#CBCBD3'),(.7,'#F1EBDD'),(1,'#FFF9EF')])
teal=look.clean_toon('Petrol turquoise','teal');red=look.clean_toon('Brick crimson','red')
navy=look.clean_toon('Officer navy',stops=[(0,'#272639'),(.5,'#354563'),(1,'#576A83')])
dark=look.metal('Dark leather','#292735',0,.9);gold=look.metal('Brass','#E5BA65',.35,.26,emission_strength=.25)
silver=look.metal('Silver razor and steel coin','#B8C9D4',.38,.23,emission_strength=.08)
coinmat=look.metal('Cupro nickel warm silver','#B2AAA0',.3,.29,emission_strength=.08)
orange=emission('Molten orange','#FF7A15',2);hot=emission('Furnace yellow core','#FFD07A',2.2)
def texture(name,a,b,scale=5):
 m=look.metal(name,a,0,.86);nt=m.node_tree;n=nt.nodes;l=nt.links;bs=n.get('Principled BSDF')
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=2
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=look.rgba(a);ramp.color_ramp.elements[1].color=look.rgba(b)
 l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color']);return m
wood=texture('Warm wood grain','#6D412B','#BA8450',8);sand=texture('Warm dusty street','#B58D68','#E4C193',18)
brick=texture('Workshop fired brick','#61382B','#A66B46',7);plaster=texture('Cream painted plaster','#C8B39A','#F6DEB1',4)
blue=texture('Cobalt storefront paint','#164A78','#346C9E',5);tiles=look.metal('Mint pale tile','#C1DAD5',0,.7)
glass=look.metal('Transparent jar glass','#B6E4EE',0,.2);bs=glass.node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=.18;glass.surface_render_method='BLENDED';glass.diffuse_color=(.6,.8,.9,.18)
windowglass=look.metal('Pale blue window glass','#91C8E5',0,.3);windowglass.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.10;windowglass.surface_render_method='BLENDED'
font=bpy.data.fonts.load('C:/Windows/Fonts/Nirmala.ttc')
def text(name,body,xyz,size,parent,mat=BLACK):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.font=font;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.0003
 o=obj(name,cu,parent);o.location=xyz;o.rotation_euler.x=math.pi/2;cu.materials.append(mat);return o
def box(name,xyz,size,mat,parent,outline=.003,bevel=.025):
 o=cube(name,xyz,size,mat,parent,bevel,outline);o['collision']=True;return o
def table(name,parent,z=.85):
 box(name+' top',(0,.35,z),(2.7,.9,.14),wood,parent)
 for x in [-1.1,1.1]:
  for y in [0,.7]:box(name+' leg',(x,y,z/2),(.11,.11,z),wood,parent,0,.015)
def disk(name,parent,xyz,r=.06,depth=.012,mat=coinmat,label='₹5'):
 root=obj(name,parent=parent);root.location=xyz
 cylinder(name+' milled body',(0,-depth/2,0),(0,depth/2,0),r,mat,root,verts=40,outline=.001)
 for i in range(24):
  a=i*math.tau/24;line(name+' edge milling',[(r*math.cos(a),-depth*.4,r*math.sin(a)),(r*math.cos(a),depth*.4,r*math.sin(a))],.00065,mat,root)
 if label:
  text(name+' physical relief',label,(0,-depth/2-.0015,0),r*.70,root,BLACK)
  back=text(name+' reverse relief',label,(0,depth/2+.0015,0),r*.70,root,BLACK);back.rotation_euler.z=math.pi
 for sign in [-1,1]:
  line(name+' recessed minted border',[(r*.88*math.cos(a),sign*(depth/2+.0006),r*.88*math.sin(a)) for a in [j*math.tau/48 for j in range(49)]],r*.010,mat,root)
 root['prop_type']='coin';return root
def blade(name,parent,xyz,scale=1):
 root=obj(name,parent=parent);root.location=xyz;root.scale=(scale,scale,scale)
 pts=[(-.065,-.032),(-.052,-.044),(.052,-.044),(.065,-.032),(.065,.032),(.052,.044),(-.052,.044),(-.065,.032)]
 me=mesh(name+' silver bevel',[(x,-.002,z) for x,z in pts]+[(x,.002,z) for x,z in pts],
  [tuple(reversed(range(8))),tuple(range(8,16))]+[(j,(j+1)%8,(j+1)%8+8,j+8) for j in range(8)],silver,root,.0015,False)
 box(name+' dark center slot',(0,-.003,0),(.045,.001,.009),BLACK,root,0,.003)
 for x in [-.022,.022]:sphere(name+' slot hole',(x,-.004,0),(.006,.001,.006),BLACK,root,12,6)
 root['prop_type']='blade';return root
stages=[]
for i,name in enumerate(['BARBER','MARKET','WORKSHOP','MINT']):
 root=obj(name+' stage');root.location=(i*22,0,0);root['stage']=i;stages.append(root)
 floor=box(name+' support floor',(0,1,-.13),(10,14,.26),tiles if i==3 else sand if i<2 else brick,root,0,0)
 if i==2:back=box(name+' back wall',(0,3,1.8),(8,.22,3.6),brick,root,0,.04)
 else:
  box(name+' lower wall',(0,3,.85),(8,.22,1.7),plaster,root,0,.02)
  box(name+' upper wall',(0,3,3.15),(8,.22,.9),plaster,root,0,.02)
  for lo,hi in [(-4,-2.925),(-1.875,-1.325),(-.275,.275),(1.325,1.875),(2.925,4)]:
   box(name+' window masonry pier',((lo+hi)/2,3,2.2),(hi-lo,.22,1),plaster,root,0,.02)
 for x in [-3.4,3.4]:
  box(name+' side jamb',(x,1.7,1.6),(.18,2.8,3.2),wood if i<3 else navy,root)
  box(name+' roof crossbeam',(0,2.7,3.25),(7,.24,.22),wood,root)
 for x in [-2.4,-.8,.8,2.4]:
  if i==2:
   for z in [.3,.65,1,1.35,1.7,2.05,2.4,2.75]:
    line('Mortar joint',[(x-.7,2.875,z),(x+.7,2.875,z)],.008,dark,root)
  else:
   pane=box(name+' recessed window',(x,2.85,2.2),(1.05,.08,1.0),windowglass,root,outline=0);pane.visible_shadow=False
   for dz in [-.51,0,.51]:box(name+' window cream frame',(x,2.78,2.2+dz),(1.12,.07,.045),white,root,0,.008)
 if i!=2:
  for j in range(6):
   x=(j-2.5)*1.65;h=1.8+(j%3)*.45
   box('Indian lane varied facade',(x,5.5,h/2),(1.5,.8,h),[blue,red,teal,plaster][j%4],root,0,.05)
   for z in [.65,1.5]:
    box('Street recessed door/window',(x,5.06,z),(.65,.03,.55),dark,root,0,.01)
  for j in range(3):
   cloud=sphere('Cloud soft silhouette',(j*3-3,8,5+j*.2),(1.2,.2,.25),CREAM,root,20,10);look.mark_role(cloud,'cloud')
   for k in range(2):
    lobe=sphere('Varied cloud lobe',(j*3-3-.45+k*.70,8,5+j*.2+.16+(j%2)*.09),(.38+.08*j,.18,.24+.04*k),CREAM,root,16,8);look.mark_role(lobe,'cloud')
bar,market,work,mint=stages
box('Workshop closed ceiling',(0,1.4,3.55),(8,4.5,.22),brick,work,0,.04)
for x in [-3.7,3.7]:box('Workshop side masonry',(x,1.4,1.75),(.22,3.5,3.5),brick,work,0,.04)
table('Barber counter',bar);table('Kirana counter',market);table('Workshop bench',work);table('Mint blueprint desk',mint)
for o in list(S.objects):
 if o.name.startswith('Barber counter'):o.location.x-=1.2
 if o.name.startswith('Mint blueprint desk'):
  if 'top' in o.name:o.location.x=-1.8;o.scale.x=1.5/2.7
  elif 'leg' in o.name:o.location.x=-1.8+(.6 if o.location.x>0 else -.6)
# Barber set: mirror, mounted calendar, striped pole and fully supported chair.
box('Mounted mirror frame',(-1.45,2.65,1.8),(1.45,.10,1.65),wood,bar)
box('Mirror face',(-1.45,2.58,1.8),(1.32,.025,1.52),silver,bar,0,.01)
box('Calendar physical backing',(1.75,2.64,2.2),(.7,.05,.75),white,bar)
text('Calendar year','2009',(1.75,2.60,2.32),.22,bar)
for j in range(5):line('Calendar printed row',[(1.48,2.6,2.12-j*.07),(2.02,2.6,2.12-j*.07)],.003,red,bar)
for j in range(14):cylinder('Barber striped pole',(2.95,.7,.3+j*.12),(2.95,.7,.42+j*.12),.10,red if j%2 else white,bar,16)
chair=box('Barber chair seat',(.8,.0,.59),(.63,.6,.15),red,bar)
cylinder('Barber chair pedestal',(.8,.0,.03),(.8,.0,.52),.12,silver,bar,24)
cylinder('Barber chair supported base',(.8,0,.01),(.8,0,.05),.36,silver,bar,32)
box('Chair padded back',(.8,.26,.94),(.62,.12,.6),red,bar)
for x in [.43,1.17]:box('Chair armrest',(x,-.03,.83),(.10,.58,.08),dark,bar)
press=obj('Barber press',parent=bar);press.location=(-.65,.58,.94)
for x in [-.20,.20]:box('Press guide',(x,.1,.27),(.06,.09,.54),navy,press)
box('Press base',(0,0,.025),(.58,.42,.05),silver,press)
cylinder('Supported coin die',(0,0,.05),(0,0,.084),.078,silver,press,24,outline=.002)
box('Blade receiving tray',(0,-.34,.064),(.35,.34,.04),silver,press)
ram=box('Barber press moving ram',(0,0,.34),(.38,.32,.09),silver,press)
presscoin=disk('Hook coin in press',press,(0,-.08,.09));presscoin.rotation_euler.x=-math.pi/2
hookblade=blade('Pressed blade',press,(0,-.28,.0864),1.2);hookblade.rotation_euler.x=-math.pi/2
mirror=obj('Customer hand mirror',parent=bar);mirror.location=(1,-.4,.94)
sphere('Hand mirror silver',(.0,0,.13),(.14,.018,.18),silver,mirror,32,16,outline=.003)
cylinder('Mirror handle',(0,0,-.15),(0,0,.03),.021,wood,mirror,16)
mirrorgrip=obj('Mirror actual handle grip',parent=mirror);mirrorgrip.location=(0,0,-.055)
# Market: glass jar, shop stock and brass balance.
jar=obj('Empty jar assembly',parent=market);jar.location=(-.7,.50,.921)
loft('Hollow glass coin jar',[(0,.19,.19),(.04,.21,.21),(.41,.21,.21),(.47,.16,.16),(.47,.14,.14),(.08,.17,.17)],glass,jar,n=32,outline=0)
for z,r in [(0,.19),(.47,.16)]:line('Jar rim',[(r*math.cos(a),r*math.sin(a),z) for a in [j*math.tau/32 for j in range(33)]],.005,silver,jar)
box('Jar physical price tag',(0,-.214,.24),(.20,.005,.13),white,jar,0,.008);text('Jar ₹5 label','₹5',(0,-.22,.24),.095,jar)
jargrip=obj('Jar neck grip',parent=jar);jargrip.location=(.17,0,.38)
sack=obj('Smuggler burlap sack',parent=market);sack.location=(.65,.50,.921)
sackmat=texture('Burlap weave','#8C6844','#C6A476',75)
loft('Burlap open sack',[(0,.23,.18),(.08,.28,.22),(.36,.23,.19),(.45,.16,.14),(.46,.13,.11),(.10,.17,.12)],sackmat,sack,n=24,outline=.004)
line('Sack open mouth',[(.16*math.cos(a),.14*math.sin(a),.46) for a in [j*math.tau/24 for j in range(25)]],.01,wood,sack)
jarcoins=[disk('Jar vanishing coin '+str(i),market,(-.7+(i%3-1)*.07,.50+(i//3%2)*.06,1.02+i*.018),r=.045) for i in range(12)]
scale=obj('Market balance',parent=market);scale.location=(.35,.22,.921)
box('Scale foot',(0,0,.025),(.55,.35,.05),gold,scale)
cylinder('Scale central axle',(0,0,.05),(0,0,.65),.025,gold,scale,20)
beam=obj('Balance pivot',parent=scale);beam.location=(0,0,.62)
line('Balance brass beam',[(-.48,0,0),(0,0,.035),(.48,0,0)],.018,gold,beam)
pans=[]
for side in [-1,1]:
 pan=obj('Scale pan '+str(side),parent=beam);pan.location=(side*.48,0,-.30);pans.append(pan)
 for dx in [-.13,.13]:line('Pan suspension',[(dx,0,0),(0,0,.3)],.003,gold,pan)
 loft('Brass scale pan',[(-.035,.08,.08),(0,.22,.18),(.015,.22,.18)],gold,pan,n=32,outline=.002)
single=disk('Single five coin',pans[0],(0,0,.021),r=.07);single.rotation_euler.x=-math.pi/2
paycoins=[disk('Payment two coin '+str(i),pans[1],(0,0,.021+i*.012),r=.065,mat=gold,label='₹2') for i in range(6)]
for c in paycoins:c.rotation_euler.x=-math.pi/2
for side,label in [(-1,'₹5'),(1,'₹12')]:
 cylinder('Price tag support post',(side*.7,-.12,.03),(side*.7,-.12,.13),.006,gold,scale,12)
 box('Price board '+label,(side*.7,-.12,.19),(.29,.03,.18),white,scale,0,.008);text('Physical price '+label,label,(side*.7,-.143,.19),.1,scale)
for i in range(7):
 x=-2.5+(i%4)*.45;z=1.2+(i//4)*.55
 cylinder('Stock tin',(x,2.47,z),(x,2.47,z+.33),.15,[teal,red,gold,white][i%4],market,16,outline=.002)
for z in [1.13,1.69,2.25]:box('Kirana stocked shelf',(-1.85,2.54,z),(2.5,.5,.09),wood,market)
ket=sphere('Brass chai kettle',(2.0,.5,1.08),(.20,.17,.23),gold,market,24,12,outline=.003)
line('Chai kettle spout',[(2.12,.5,1.11),(2.32,.5,1.22),(2.4,.5,1.3)],.04,gold,market)
line('Chai kettle arch handle',[(1.8,.5,1.1),(1.78,.5,1.42),(2,.5,1.51),(2.22,.5,1.42),(2.2,.5,1.1)],.02,dark,market)
# Furnace workshop with amber source and slate separation, no volumetrics.
furnace=obj('Furnace',parent=work);furnace.location=(-.95,1.5,0)
box('Furnace brick body',(0,0,.65),(1.3,.75,1.3),brick,furnace)
box('Furnace dark mouth',(0,-.39,.56),(.77,.025,.64),BLACK,furnace,0,.18)
sphere('Furnace orange opening',(0,-.42,.51),(.33,.02,.22),orange,furnace,24,12)
for j in range(7):sphere('Lobed living furnace flame',(-.22+j*.075,-.44,.53),(.06,.018,.12+j%3*.04),hot if j%2 else orange,furnace,12,6)
ladle=obj('Molten ladle',parent=work);ladle.location=(-.45,-.12,1.22)
loft('Iron ladle bowl',[(-.09,.055,.055),(-.06,.11,.11),(.04,.13,.13),(.045,.105,.105),(-.04,.08,.08)],dark,ladle,n=24,outline=.003)
sphere('Liquid metal surface',(0,0,.025),(.105,.105,.008),hot,ladle,24,8)
cylinder('Ladle tong handle',(.11,0,0),(.50,0,0),.018,silver,ladle,16)
ladlegrip=obj('Ladle handle surface grip',parent=ladle);ladlegrip.location=(.40,0,0)
molten=line('Animated molten stream',[(0,0,0)]*16,.023,orange,work);look.mark_role(molten,'streak')
tray=obj('Six cavity blade tray',parent=work);tray.location=(.45,-.02,.96)
box('Mold tray slab',(0,0,0),(.92,.42,.065),dark,tray)
anvil=obj('Workshop iron anvil',parent=work);anvil.location=(1.04,.54,.92)
box('Anvil foot',(0,0,.04),(.48,.25,.08),dark,anvil)
loft('Anvil shaped waist',[(.08,.18,.10),(.16,.11,.07),(.25,.22,.10)],dark,anvil,n=20,outline=.003)
box('Anvil hardened top',(.02,0,.285),(.48,.22,.075),silver,anvil)
cylinder('Anvil horn',(-.23,0,.28),(-.40,0,.27),.055,silver,anvil,16)
box('Workshop rear tool shelf',(.7,2.65,2.05),(1.9,.45,.12),wood,work)
for j in range(4):
 line('Hanging iron tool',[(.12+j*.40,2.62,1.94),(.12+j*.40,2.62,1.55)],.014,silver,work)
 line('Forged tool fork',[(.08+j*.40,2.62,1.52),(.12+j*.40,2.62,1.55),(.16+j*.40,2.62,1.52)],.015,silver,work)
blades=[]
for i in range(6):
 x=-.37+i*.148
 coords=[(x+dx,dy,.033) for dx,dy in [(-.06,-.033),(-.05,-.04),(.05,-.04),(.06,-.033),(.06,.033),(.05,.04),(-.05,.04),(-.06,.033)]]
 mesh('Empty blade mold cavity '+str(i),coords,[tuple(range(8))],BLACK,tray,smooth=False)
 b=blade('Six output blade '+str(i),tray,(x,0,.042),.85);b.rotation_euler.x=-math.pi/2;blades.append(b)
workcoin=disk('Coin dropped into ladle',work,(-.45,-.12,1.6),r=.06)
for i,xyz in enumerate([(-1.2,-1.2,2.8),(1.6,-.2,2.3)]):
 o=light('Workshop amber key' if i==0 else 'Workshop slate fill','AREA',xyz,(0,.2,1),450 if i==0 else 55,'#FFD488' if i==0 else '#7687B7',1.2);o.parent=work;o['stage_light']=2
 o.data.use_shadow=i==0
o=light('Furnace amber practical','POINT',(-.95,1.0,.65),(0,0,0),100,'#FF8D35',.2);o.parent=work;o['stage_light']=2;o.data.use_shadow=False
# Mint: mechanical press, lever and coin chute.
machine=obj('Mint press assembly',parent=mint);machine.location=(.65,.9,0)
for x in [-.52,.52]:box('Mint machine column',(x,0,1.15),(.19,.40,2.3),navy,machine)
box('Mint head crossbar',(0,0,2.3),(1.35,.6,.28),navy,machine)
box('Mint base',(0,0,.37),(1.45,.9,.7),navy,machine)
mintRam=box('Mint piston head',(0,0,1.25),(.67,.43,.18),silver,machine)
cylinder('Mint piston',(0,0,1.35),(0,0,2.15),.10,silver,machine)
lever=obj('Mint lever pivot',parent=machine);lever.location=(-.70,-.70,1.15)
line('Mint lever bar',[(0,0,0),(-.35,0,.48)],.024,silver,lever)
grip=sphere('Lever dark grip',(-.35,0,.48),(.055,.04,.09),dark,lever,16,8)
levergrip=obj('Lever hand anchor',parent=lever);levergrip.location=(-.35,0,.48)
chute=box('Coin chute',(0,-.61,.57),(.46,1.1,.045),silver,machine);chute.rotation_euler.x=.25
box('Coin receiving tray',(0,-1.45,.37),(.6,.55,.06),silver,machine)
for x in [-.3,.3]:box('Receiving tray rim',(x,-1.45,.42),(.035,.55,.10),navy,machine)
mintcoins=[disk('Thin steel output '+str(i),machine,(0,-.4,.65),r=.055,depth=.003,mat=silver) for i in range(8)]
for c in mintcoins:c.rotation_euler.x=-math.pi/2
box('RBI wall plaque',(0,2.8,3.05),(1.75,.08,.36),navy,mint);text('Mint plaque','RBI MINT',(0,2.75,3.05),.23,mint,CREAM)
stamp=obj('Officer rubber stamp',parent=mint);stamp.location=(-1.3,-.12,1.2)
box('Stamp red block',(0,0,0),(.48,.30,.10),red,stamp)
cylinder('Stamp actual handle',(0,0,.05),(0,0,.27),.035,wood,stamp,20,outline=.002)
stampgrip=obj('Stamp hand surface grip',parent=stamp);stampgrip.location=(0,0,.20)
box('Cancelled coin mold',(-1.3,.1,.97),(.6,.48,.08),silver,mint)
stamped=text('Physical red cancelled impression','BAND',(-1.3,-.13,1.015),.18,mint,red);stamped.rotation_euler.x=0
# Flat-on-screen cast. Small depth supports contact, not glossy 3D hands/faces.
def facepoint_flat(x,z,offset=.004):
 r=.32*rough(math.atan2(-z,x));return (x,-.063*math.sqrt(max(.035,1-(x*x+z*z)/(r*r)))-offset,z)
G.facepoint=facepoint_flat
def actor(name,parent,xyz,costume,kind):
 root=obj(name,parent=parent);root.location=xyz;root['actor']=kind
 body=obj(name+' body',parent=root);head=obj(name+' head',parent=body);head.location=(0,0,1.5)
 skull=sphere(name+' cream rough head',(0,0,0),(.32,.063,.32),CREAM,head,48,20)
 for v in skull.data.vertices:
  rr=rough(math.atan2(-v.co.z,v.co.x));v.co.x*=rr;v.co.z*=rr
 ink(skull,.009)
 loft(name+' connected torso',[(.67,.16,.085),(.72,.205,.1),(1.05,.24,.11),(1.16,.21,.095),(1.21,.085,.06)],costume,body,n=32,outline=.006)
 for side in [-1,1]:
  line(name+f' arm {side}',[(side*.23,0,1.1)]*20,.024,BLACK,root)
  hand=obj(name+f' hand {side}',parent=root)
  sphere(name+' flat dark hand',(0,0,0),(.048,.012,.049),BLACK,hand,20,10)
  for j in range(3):line(name+' flat grip finger',[(.035,-.012,-.024+j*.021),(.010,-.018,-.029+j*.021),(-.018,-.013,-.025+j*.021)],.008,BLACK,hand)
  line(name+f' leg {side}',[(side*.12,0,.7)]*20,.025,BLACK,root)
  sphere(name+f' foot {side}',(side*.14,-.05,.04),(.075,.105,.035),BLACK,root,20,10)
  sh=sphere(name+' sole shadow',(side*.14,-.05,.005),(.10,.12,.003),dark,root,16,6);look.mark_role(sh,'ink')
  x=side*.105
  oval(name+f' eye {side}',x,.025,.024,.034,BLACK,head)
  faceline(name+f' brow {side}',[(x-.04,.11),(x,.12),(x+.04,.105)],.009,BLACK,head)
  faceline(name+f' closed {side}',[(x-.027,.02),(x,.01),(x+.027,.02)],.006,BLACK,head)
 faceline(name+' smirk',[(-.055,-.105),(-.012,-.127),(.035,-.115),(.065,-.083)],.007,BLACK,head)
 faceline(name+' frown',[(-.055,-.13),(0,-.106),(.055,-.13)],.007,BLACK,head)
 for k,(rx,rz) in enumerate([(.045,.025),(.06,.045),(.075,.060)],1):
  oval(name+f' mouth {k}',0,-.12,rx,rz,BLACK,head)
  if k==2:patch(name+' teeth',[(-.045,-.09),(.045,-.09),(.04,-.11),(-.04,-.11)],CREAM,head,.01)
 if kind in ['barber','officer']:
  for side in [-1,1]:faceline(name+' mustache',[(-.01*side,-.065),(.035*side,-.06),(.065*side,-.076)],.014,BLACK,head)
 if kind=='customer':
  for x in [-.21,.21]:sphere('Customer lather',(x,-.045,-.08),(.1,.025,.11),white,head,16,10)
 if kind=='smuggler':
  for x in [-.105,.105]:oval('Smuggler dark glasses',x,.03,.065,.046,BLACK,head,.012)
  faceline('Glasses bridge',[(-.05,.04),(.05,.04)],.008,BLACK,head)
  loft('Smuggler cap',[(.19,.29,.10),(.30,.26,.09),(.35,.12,.05)],dark,head,n=32,outline=.005)
  box('Cap projecting brim',(0,-.09,.19),(.55,.18,.025),dark,head,0,.03)
 if kind=='shopkeeper':
  for x in [-.105,.105]:line('Shopkeeper round glasses',[facepoint_flat(x+.064*math.cos(a),.025+.053*math.sin(a),.014) for a in [j*math.tau/32 for j in range(33)]],.005,gold,head)
 if kind=='officer':
  patch('Officer red tie',[(-.035,1.16),(.035,1.16),(.055,.95),(0,.9),(-.05,.95)],red,body,.015) if False else None
  box('Officer tie',(0,-.12,1.02),(.055,.012,.23),red,body,0,.005)
 return root
barber=actor('Barber',bar,(-1.0,1.0,0),white,'barber')
customer=actor('Customer',bar,(.8,0,0),white,'customer')
keeper=actor('Shopkeeper',market,(-.85,1.0,0),white,'shopkeeper')
smuggler=actor('Smuggler',work,(-.25,.48,0),dark,'smuggler')
trader=actor('Trader',market,(.85,1.0,0),white,'smuggler')
officer=actor('Officer',mint,(-.7,.35,0),navy,'officer')
import wardrobe
wardrobe.apply()
hero=disk('Loop hero coin',bar,(0,-.45,1.35),r=.16,depth=.025)
coinref=blade('Coin reflected razor silhouette',hero,(0,-.016,0),1.1)
edgecoin=disk('Heavy coin macro',market,(-.13,.22,1.38),r=.13,depth=.027)
text('Physical edge alloy','CUPRO-NICKEL',(0,-.016,-.075),.021,edgecoin)
box('Blade display plinth',(.5,.28,.95),(.7,.35,.06),wood,market)
saleBlade=blade('Single sale blade',market,(.35,.13,1.051),1.6)
saleTag=box('Blade price physical card',(.7,.13,1.10),(.27,.025,.17),white,market,0,.01);text('Two rupee blade price','₹2',(.7,.11,1.10),.11,market)
cylinder('Blade price card support',(.7,.13,.98),(.7,.13,1.04),.007,gold,market,12)
# Explicit licensed set imports; no textures beyond sanitation limits.
imported=[]
for filename,stage,xyz in [('stall-green.glb',market,(2.5,2.8,0)),('stall-red.glb',bar,(-2.8,3.7,0))]:
 path=R/'public/bridge/kenney'/filename
 if path.exists():
  before=set(S.objects);bpy.ops.import_scene.gltf(filepath=str(path));new=list(set(S.objects)-before)
  root=obj('Local generated town kit '+filename,parent=stage);root.location=xyz;root.scale=(.7,.7,.7)
  for o in new:
   if o.parent not in new:o.parent=root
   if o.type=='MESH':imported.append(o)
report=gate.sanitize_assets(S,imported);(P/'asset_report.json').write_text(json.dumps(report,indent=2))
focus=obj('Story focus');camera_data=bpy.data.cameras.new('Story camera');camera=obj('Story camera',camera_data);S.camera=camera;look.configure_camera(camera,focus,50,2.8)
# Embed all production dependencies; reopening requires only packed START_HERE.py.
for filename in ['geometry.py','runtime.py']:
 t=bpy.data.texts.new(filename);t.from_string((D/filename).read_text(encoding='utf-8'))
for filename in ['audio_envelope.json','input_manifest.json']:
 t=bpy.data.texts.new(filename);t.from_string((P/filename).read_text(encoding='utf-8'))
t=bpy.data.texts.new('ricks_lookdev.py');t.from_string((R/'scripts/ricks_lookdev.py').read_text(encoding='utf-8'))
bootstrap="""import bpy,sys,types
for name in ['ricks_lookdev','geometry','runtime']:
 m=types.ModuleType(name);sys.modules[name]=m
 exec(compile(bpy.data.texts[name+'.py'].as_string(),name+'.py','exec'),m.__dict__)
sys.modules['runtime'].register()
"""
t=bpy.data.texts.new('START_HERE.py');t.from_string(bootstrap)
sound=bpy.data.sounds.load(str(P/'narration_preserved.wav'));sound.pack();sound.use_fake_user=True
bpy.ops.file.pack_all()
exec(bootstrap)
S.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'project_paradox_ep03_v01.blend'))
print('ORIGINAL_FOUR_SET_BUILD_SAVED',len(S.objects))
