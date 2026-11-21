"""Stateless original Hindi coin story; one-based Blender frames."""
import bpy,math,json,sys,os,traceback
import numpy as np
from mathutils import Vector as V,Matrix
from geometry import bezier_points,set_line
import ricks_lookdev as look
S=bpy.context.scene;O=bpy.data.objects
ENV=json.loads(bpy.data.texts['audio_envelope.json'].as_string())
SHOTS=[('coin',1,75,0),('barber_press',76,174,0),('customer_blades',175,285,0),
 ('market_vanish',286,456,1),('heavy_metal',457,615,1),('loophole',616,720,2),
 ('ladle',721,795,2),('six_blades',796,879,2),('blade_price',880,957,1),
 ('twelve',958,1055,1),('chuckle',1056,1167,1),('stamp',1168,1215,3),
 ('mint',1216,1339,3),('loop',1340,1401,0)]
ACTORS=['Barber','Customer','Shopkeeper','Smuggler','Trader','Officer']
STAGES=['BARBER stage','MARKET stage','WORKSHOP stage','MINT stage']
BASE={n:O[n].location.copy() for n in ACTORS}
GROUPS={n:[O[n]]+list(O[n].children_recursive) for n in STAGES}
KETTLE=[o for o in O if o.name.startswith(('Brass chai kettle','Chai kettle spout','Chai kettle arch handle'))]
HULLS=[]
for hull in [o for o in S.objects if o.get('ink_base_width')]:
 source=hull.parent
 co=np.empty(len(source.data.vertices)*3,np.float32);norm=co.copy()
 source.data.vertices.foreach_get('co',co);source.data.vertices.foreach_get('normal',norm)
 center=sum((V(p) for p in source.bound_box),V())/8
 HULLS.append((hull,source,co.reshape(-1,3),norm.reshape(-1,3),center))
def lineage(obj):
 while obj:
  yield obj
  obj=obj.parent
def visible(obj,value):
 ancestor=obj.parent
 while ancestor:
  if 'stage' in ancestor and ancestor['stage']!=S.get('active_stage',0):value=False;break
  if ancestor.get('story_hidden',False):value=False;break
  ancestor=ancestor.parent
 obj['story_hidden']=not value
 if obj.hide_render==value:obj.hide_render=obj.hide_viewport=not value
 for child in obj.children_recursive:
  if child.hide_render==value:child.hide_render=child.hide_viewport=not value
def ease(f,a,b):return look.ease5((f-a)/max(1,b-a))
def pulse(f,a,b,c,d):return ease(f,a,b)*(1-ease(f,c,d))
def locate(stage,xyz):return O[STAGES[stage]].location+V(xyz)
def camera(stage,position,target,lens=50,fstop=2.8):
 cam=S.camera;cam.location=locate(stage,position);target=locate(stage,target)
 cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(target-cam.location).to_track_quat('-Z','Y')
 cam.data.lens=lens;cam.data.dof.aperture_fstop=min(fstop,2.45) if lens>=50 else fstop;O['Story focus'].location=target
 cam.data.dof.focus_distance=(target-cam.location).length
def arm(name,side,target):
 root=O[name];body=O[name+' body'];shoulder=body.matrix_world@V((side*.23,0,1.1));target=V(target)
 elbow=shoulder+V((side*.12,-.12,-.13));wrist=target+V((side*.08,.05,-.07))
 pts=bezier_points(shoulder,elbow,wrist,target)
 set_line(O[name+f' arm {side}'],[root.matrix_world.inverted()@p for p in pts])
 h=O[name+f' hand {side}'];q=(S.camera.location-target).to_track_quat('-Y','Z')
 h.matrix_world=Matrix.Translation(target)@q.to_matrix().to_4x4()
def face(name,f,mood='smirk'):
 closed=any(a<=f<=b for a,b in [(120,123),(348,352),(674,678),(1082,1086),(1253,1257)])
 for side in [-1,1]:
  visible(O[name+f' eye {side}'],not closed);visible(O[name+f' closed {side}'],closed)
  eye_snap=ease(f,222,226)
  overshoot=pulse(f,225,227,228,233)
  O[name+f' eye {side}'].scale.z=1+.52*eye_snap+.28*overshoot if mood=='fear' else .75 if mood=='greed' else 1
  O[name+f' eye {side}'].scale.x=1+.15*eye_snap if mood=='fear' else 1
  O[name+f' brow {side}'].rotation_euler.y=side*(.1 if mood=='fear' else -.08 if mood=='stern' else 0)
 volume=ENV[min(f-1,len(ENV)-1)]
 shape=3 if mood=='fear' else (2 if volume>.32 else 1 if volume>.10 else 0) if mood=='laugh' else 0
 if mood=='fear':
  reaction=ease(f,220,231)
  O[name+' mouth 3'].scale.z=.50+.56*reaction+.35*math.sin((f-223)*.52)*pulse(f,222,225,248,270)
  O[name+' mouth 3'].scale.x=1-.13*ease(f,226,239)+.05*math.sin(f*.37)
 visible(O[name+' smirk'],shape==0 and mood not in ['stern','tired'])
 visible(O[name+' frown'],shape==0 and mood in ['stern','tired'])
 for k in range(1,4):visible(O[name+f' mouth {k}'],shape==k)
 visible(O[name+' teeth'],shape==2)
_last_frame=None
def update(frame,force=False):
 global _last_frame
 f=max(1,min(1401,int(frame)))
 if _last_frame==f and not force:return
 shot=next(x for x in SHOTS if x[1]<=f<=x[2]);name,a,b,stage=shot;u=(f-a)/max(1,b-a);e=look.ease5(u)
 S['active_stage']=stage
 active={0:['Barber','Customer'],1:['Shopkeeper','Trader'],2:['Smuggler'],3:['Officer']}[stage]
 for i,n in enumerate(STAGES):
  for o in GROUPS[n]:
   if o.hide_render!=(i!=stage):o.hide_render=o.hide_viewport=i!=stage
 S.world=bpy.data.worlds['Workshop slate interior world'] if stage==2 else bpy.data.worlds['Sunny Indian lane world']
 for n in S.node_tree.nodes:
  if n.type=='MATH' and n.operation=='MULTIPLY' and abs(n.inputs[1].default_value-.45)<.001:n.name='Story mist gain'
 if 'Story mist gain' in S.node_tree.nodes:S.node_tree.nodes['Story mist gain'].inputs[1].default_value=0 if stage==2 else .45
 for o in S.objects:
  if o.get('ricks_light'):o.hide_render=o.hide_viewport=stage==2
 # Camera lens fixed within each shot; all moves are finite authored curves.
 if name=='coin':camera(0,(.06+.10*e,-2.1+.12*e,1.52),(0,-.45,1.35),72,2.8)
 elif name=='barber_press':camera(0,(-1.4+.2*e,-4.8+.20*e,1.90),(-.10,.48,1.18),34,3.2)
 elif name=='customer_blades':
  q=ease(f,198,232);pos=V((-.65,-1.5,1.55)).lerp(V((1.5-.16*e,-2.9+.12*e,1.76)),q)
  target=V((-.65,.08,1.0264)).lerp(V((.65,.02,1.25)),q);camera(0,pos,target,56,3.2)
 elif name=='market_vanish':camera(1,(-.35+.7*e,-4.9,1.85),(.05,.14,1.1),40,3.5)
 elif name=='heavy_metal':camera(1,(-.65+.25*e,-1.5,1.58),(-.13,.22,1.35),72,2.8)
 elif name=='loophole':camera(2,(-1.5+.3*e,-4.3+.3*e,2.05),(-.4+.1*e,.65,1.3),40,3.2)
 elif name=='ladle':camera(2,(-.20,-1.4+.12*e,1.92),(-.4,-.1,1.19),65,2.8)
 elif name=='six_blades':
  theta=-.20+.55*e;camera(2,(.45+3*math.sin(theta),-.02-3*math.cos(theta),2.3),(.45,-.02,1.03),55,3.2)
 elif name=='blade_price':camera(1,(.42+.11*e,-1.40,1.85),(.53,.13,1.02),52,3.2)
 elif name=='twelve':camera(1,(.5-.3*e,-3.8,1.9),(.35,.22,1.27),45,3.5)
 elif name=='chuckle':camera(1,(1.0+.1*e,-2.6+.18*e,1.90),(.85,.6,1.35),60,3.2)
 elif name=='stamp':camera(3,(-1.65+.15*e,-3.1,1.95),(-1.06,.12,1.24),45,3.2)
 elif name=='mint':camera(3,(1.9-1.0*e,-4.7,2.05),(.0,.5,1.3),40,3.5)
 else:
  # Match the complete opening coin/camera/lighting state at the loop endpoint.
  theta=(1-e)*1.1;camera(0,(.06+math.sin(theta)*.55,-2.1+(1-math.cos(theta))*.55,1.52+.15*(1-e)),(0,-.45,1.35),72,2.8)
 # Brief impacts decay over three frames.
 for impact in (151,1018,1198):
  d=f-impact
  if 0<=d<=2:
   S.camera.location.z += (.023,-.014,.005)[d]
 # Per-frame root/body defaults ensure direct seeking gives the same state.
 for actor in active:
  root=O[actor];root.location=BASE[actor];root.rotation_euler=(0,0,0)
  body=O[actor+' body'];body.location=(0,0,0);body.rotation_euler=(0,0,0)
  if actor=='Customer':
   react=ease(f,211,229) if name=='customer_blades' else 0
   body.location.z=-.03+.032*react+.016*math.sin((f-221)*.66)*pulse(f,219,223,232,245)
   body.rotation_euler.x=-.10*react-.10*pulse(f,219,223,226,236)
  elif actor=='Barber':
   body.rotation_euler.x=.08*pulse(f,125,148,156,174)
  if actor=='Trader' and name=='chuckle':
   tremble=math.sin((f-1056)*.48)*pulse(f,1056,1064,1150,1167)
   body.location.z=.035*tremble
   body.rotation_euler.y=.11*tremble
   body.rotation_euler.x=.09*tremble
  for side in [-1,1]:
   if actor=='Customer':pts=bezier_points((side*.12,0,.65),(side*.18,-.35,.55),(side*.2,-.54,.4),(side*.2,-.57,.08));foot=(side*.2,-.58,.035)
   else:pts=bezier_points((side*.12,0,.69),(side*.12,.015,.45),(side*.14,-.01,.25),(side*.14,-.03,.07));foot=(side*.14,-.05,.035)
   set_line(O[actor+f' leg {side}'],pts);O[actor+f' foot {side}'].location=foot
 # Prop state: base positions reset before each authored action.
 visible(O['Loop hero coin'],name in ['coin','loop'])
 for actor in ['Trader','Shopkeeper']:visible(O[actor],name not in ['heavy_metal','blade_price','twelve'])
 visible(O['Smuggler burlap sack'],name=='market_vanish')
 visible(O['Market balance'],name in ['heavy_metal','twelve'])
 for kettle_prop in KETTLE:
  visible(kettle_prop,name=='market_vanish')
 O['Loop hero coin'].rotation_euler=(0,0,math.tau*e)
 visible(O['Coin reflected razor silhouette'],name=='coin' and 67<=f<=75)
 visible(O['V2 coin glint'],name=='coin' and 66<=f<=75)
 O['V2 coin glint'].location.x=-.100+.21*ease(f,66,75)
 O['V2 rotating barber pole'].rotation_euler.z=f*.047
 O['Customer hand mirror'].rotation_euler.y=.17*math.sin((f-218)*.72)*pulse(f,216,224,251,276)
 visible(O['V2 press spark'],name=='barber_press' and 150<=f<=155)
 O['V2 press spark'].scale=(max(.05,1-(f-150)*.15),)*3
 visible(O['Heavy coin macro'],name=='heavy_metal');O['Heavy coin macro'].location=(-.13,.22,1.38+.14*(1-ease(f,506,520)))
 O['Heavy coin macro'].rotation_euler.z=.25-.10*e
 visible(O['Single sale blade'],name=='blade_price');visible(O['Blade price physical card'],name=='blade_price');visible(O['Two rupee blade price'],name=='blade_price')
 O['Barber press moving ram'].location.z=.34-.20*pulse(f,143,151,163,176)
 visible(O['Hook coin in press'],f<153 or name=='loop');visible(O['Pressed blade'],f>=153 and name!='loop')
 O['Pressed blade'].location=(0,-.28-.22*ease(f,156,174),.0864)
 for i in range(12):
  coin=O['Jar vanishing coin '+str(i)];q=ease(f,306+i*10,330+i*10)
  coin.location=V((-.7+(i%3-1)*.07,.50+(i//3%2)*.06,1.02+i*.018)).lerp(V((.65,.50,1.21)),q)+V((0,0,.53*math.sin(math.pi*q)))
  coin.rotation_euler=(.3+i*.18+q*5,0,q*6)
  coin.scale=(1+.32*math.sin(math.pi*q),)*3
  visible(coin,name=='market_vanish' and q<.98)
 O['Balance pivot'].rotation_euler.y=-.06*ease(f,520,540) if f<958 else .54*ease(f,1007,1018)+.09*math.sin((f-1018)*.48)*pulse(f,1017,1019,1021,1048)
 for i in range(6):
  drop=1009+i
  coin=O['Payment two coin '+str(i)]
  coin.location.z=.021+i*.012+.36*(1-ease(f,drop,1018+i))
  visible(coin,name=='twelve' and f>=drop)
  blade=O[f'V2 scale blade {i}']
  blade.location.z=.029+i*.004+.40*(1-ease(f,drop-2,1016+i))
  visible(blade,name=='twelve' and f>=drop-2)
 visible(O['Single five coin'],name in ['twelve','chuckle'])
 # Molten stream joins the moving ladle lip and mold; no simulation/cache.
 O['Molten ladle'].location=(-.45,-.12,1.22);O['Molten ladle'].rotation_euler.y=.65*pulse(f,792,806,832,848)
 O['Coin dropped into ladle'].location=(-.45,-.12,1.68-.43*ease(f,739,765))
 visible(O['Coin dropped into ladle'],stage==2 and 721<=f<768)
 visible(O['Animated molten stream'],stage==2 and 803<=f<=839)
 bpy.context.view_layer.update()
 for side in [-1,1]:
  pan=O['Scale pan '+str(side)];pan.rotation_euler.y=-O['Balance pivot'].rotation_euler.y
 bpy.context.view_layer.update()
 for side in [-1,1]:
  pan=O['Scale pan '+str(side)];top=pan.matrix_world.inverted()@(O['Balance pivot'].matrix_world@V((side*.48,0,0)))
  for chain in pan.children:
   if chain.name.startswith('Pan suspension'):set_line(chain,[(chain.data.splines[0].points[0].co.x,0,0),top])
 heavy=O['Heavy coin macro'];height=.145+.14*(1-ease(f,506,520))
 heavy.location=O['MARKET stage'].matrix_world.inverted()@(O['Scale pan -1'].matrix_world@V((0,0,height)))
 lip=O['Molten ladle'].matrix_world@V((.12,0,.02));end=locate(2,(.18,-.02,1.0))
 stream_points=[O['WORKSHOP stage'].matrix_world.inverted()@p for p in bezier_points(lip,lip+V((.08,0,-.08)),end+V((-.1,0,.1)),end,16)]
 set_line(O['Animated molten stream'],stream_points)
 set_line(O['V3 molten white core'],stream_points)
 visible(O['V3 molten white core'],stage==2 and 803<=f<=839)
 spill=O['V3 molten interactive spill']
 spill.location=O['Molten ladle'].location+V((.08,-.06,.12))
 spill.data.energy=22+47*pulse(f,739,762,774,793)+59*pulse(f,802,808,835,848)+4*math.sin(f*.47)
 for i in range(6):
  blade=O['Six output blade '+str(i)];q=ease(f,830+i*4,846+i*4)
  height=.0335+.85*(.044*math.sin(.35*q)+.002*math.cos(.35*q))+.02*math.sin(math.pi*q)
  blade.location=(-.37+i*.148,-.03*math.sin(i),height);blade.rotation_euler=(-math.pi/2+.35*q,0,(i-2.5)*.05*q)
  visible(blade,stage==2 and f>=822+i*5)
 # Stamp face contacts mold at f1200; hand follows the real handle.
 down=pulse(f,1180,1198,1205,1218);O['Officer rubber stamp'].location=(-1.3-.26*ease(f,1205,1215),-.12,1.24-.18*down+.16*ease(f,1205,1215))
 visible(O['Physical red cancelled impression'],stage==3 and f>=1198)
 O['Mint lever pivot'].rotation_euler.x=-.75*ease(f,1220,1253)
 O['Mint piston head'].location.z=1.25-.50*pulse(f,1245,1252,1260,1270)
 piston=O['Mint piston'];ramtop=O['Mint piston head'].location.z+.09
 piston.location.z=(2.15+ramtop)/2;piston.scale.z=(2.15-ramtop)/.8
 for i in range(8):
  coin=O['Thin steel output '+str(i)];q=ease(f,1262+i*7,1292+i*7)
  coin.location=(.05*math.sin(i*2),-.40-q*1.05,.65-(.248-i*.0031)*q)
  visible(coin,stage==3 and f>=1262+i*7)
 # Camera-facing graphic faces/hands, independent of the dimensional set.
 bpy.context.view_layer.update()
 for actor in active:
  head=O[actor+' head'];world=head.matrix_world.translation
  worldq=(S.camera.location-world).to_track_quat('-Y','Z')
  head.rotation_mode='QUATERNION';head.rotation_quaternion=O[actor+' body'].matrix_world.to_quaternion().inverted()@worldq
  face(actor,f,'fear' if actor=='Customer' and f>=222 and name!='loop' else 'laugh' if actor=='Trader' and name=='chuckle' else 'greed' if actor in ['Trader','Smuggler'] else 'stern' if actor=='Officer' else 'tired' if actor=='Shopkeeper' else 'smirk')
  root=O[actor]
  for side in [-1,1]:arm(actor,side,root.matrix_world@V((side*.30,-.12,.76)))
 bpy.context.view_layer.update()
 if stage==0:
  arm('Barber',1,O['Barber press moving ram'].matrix_world@V((-.13,-.24,.05)))
  arm('Barber',-1,locate(0,(-1.0,.75,.97)))
  arm('Customer',1,O['Mirror actual handle grip'].matrix_world.translation)
  arm('Customer',-1,locate(0,(.43,-.13,.927)))
 elif stage==1:
  arm('Shopkeeper',1,O['Jar neck grip'].matrix_world.translation)
  arm('Trader',-1,locate(1,(.80,.50,1.30)))
  arm('Trader',1,locate(1,(1.30,-.03,1.18+.12*pulse(f,1060,1080,1130,1155))))
 elif stage==2:
  arm('Smuggler',1,O['Ladle handle surface grip'].matrix_world.translation)
  arm('Smuggler',-1,O['Molten ladle'].matrix_world@V((.27,0,.015)))
 else:
  arm('Officer',-1,O['Stamp hand surface grip'].matrix_world.translation)
  arm('Officer',1,O['Lever hand anchor'].matrix_world.translation)
 # Keep the drawn boundary readable through wide and close camera coverage.
 camera_inverse=S.camera.matrix_world.inverted()
 for hull,source,base,norm,center in HULLS:
  if hull.hide_render:continue
  depth=max(.05,-(camera_inverse@(source.matrix_world@center)).z)
  pixels=2.45 if 'rough head' in source.name else 2.13
  if any(word in source.name for word in ('blade','slot','rim','milled body')):
   pixels=1.7
  if 'edge' in source.name or 'thin steel' in source.name.lower():pixels=1.5
  if not any(ancestor.get('actor') for ancestor in lineage(source)) and not any(word in source.name.lower() for word in ('blade','press','mirror','coin','milled body','stamp')):
   continue
  width=look.ink_width(depth,S.camera.data.lens,pixels)
  hull.data.vertices.foreach_set('co',(base+norm*width).ravel());hull.data.update()
 look.enforce_shadow_policy(S)
 S['story_shot']=name;S['story_stage']=stage
 _last_frame=f
def _handler(scene,*args):
 try:update(scene.frame_current)
 except BaseException:traceback.print_exc();sys.stdout.flush();os._exit(3)
def register():
 for h in list(bpy.app.handlers.frame_change_post):
  if getattr(h,'_coin_story',False):bpy.app.handlers.frame_change_post.remove(h)
 _handler._coin_story=True;bpy.app.handlers.frame_change_post.append(_handler)
 look.install_shadow_policy(S);update(S.frame_current)
