import bpy,math,sys
from pathlib import Path
from mathutils import Vector as V,Quaternion,Matrix
s=bpy.context.scene;O=bpy.data.objects;cam=s.camera
sys.path.insert(0,'D:/remotionshorts/scripts/studio');from set_ink import SetInk
ink=SetInk(s)
LEG_REST={who:[v.co.copy() for v in O['V5 '+who+' flat vector legs'].data.vertices] for who in ['challenger','eddie']}
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def mix(a,b,t):return V(a).lerp(V(b),t)
def aim(pos,target,lens=42,roll=0):
 cam.location=pos;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(V(target)-cam.location).to_track_quat('-Z','Y')@Quaternion((0,0,1),roll);cam.data.lens=lens

def bullet_path(f):
 t=max(0,min(1,(f-35)/53));u=3*(1-t)**2*t*.62+3*(1-t)*t*t+t**3;return V((-.6,2.0+17.1*u,.80))
def body_basis(root):
 n=cam.location-root;n.z=0;n.normalize();right=V((-n.y,n.x,0));up=V((0,0,1));return Matrix((right,up,n)).transposed().to_quaternion()
def arms(who,basis,root,right_hand):
 o=O['V6 '+who+' continuous arms'];normal=basis@V((0,0,1));verts=[]
 for side in [-1,1]:
  sh=V(((-.305 if side<0 else .303),.211,.002));hand=V((-.34,-.30,.016)) if side<0 else right_hand.copy();control=V(((-.47 if side<0 else .46),-.05,.008))
  if who=='eddie':hand=V((-.36 if side<0 else .34,-.31,.012));control=V((-.47 if side<0 else .47,-.02,.006))
  for i in range(33):
   t=i/32;p=(1-t)**2*sh+2*(1-t)*t*control+t*t*hand;tan=2*(1-t)*(control-sh)+2*t*(hand-control);axis=V((-tan.y,tan.x,0)).normalized();w=.030*(1-t)+.023*t;verts.extend([root+basis@(p+axis*w),root+basis@(p-axis*w)])
  for i in range(24):a=i*math.tau/24;verts.append(root+basis@(hand+V((.033*math.cos(a),.038*math.sin(a),.002))))
 for v,p in zip(o.data.vertices,verts):v.co=p

def update(scene):
 f=scene.frame_current;bp=bullet_path(f);cam.data.shift_x=0;cam.data.shift_y=0;cam.data.sensor_fit='AUTO'
 recoil=({29:.2,30:1.,31:.65,32:-.1}.get(f,0))
 if f<=34:
  t=(f-1)/33;k=({29:.035,30:-.025,31:.014,32:0}.get(f,0));aim((.35+.06*t,-3.15+.08*t,1.17),(-.42,0,1.80),38,math.radians(-3)+k)
 elif f<=96:
  t=max(0,min(1,(f-35)/53));a=math.radians(-52+107*smooth(min(1,t*1.6)));offset=V((2.65*math.sin(a),-2.65*math.cos(a),.22));pos=bp+offset
  w=smooth((f-80)/8);pos=pos.lerp(V((1.6,16.4,1.35)),w);target=bp.lerp(V((-.4,19.0,.82)),w);cam.data.sensor_fit='HORIZONTAL';aim(pos,target,60+5*t)
 elif f<215:
  if f<=160:
   t=smooth((f-97)/63);pos=mix((1.6,16.4,1.35),(.6,-7.8,2.1),t);target=mix((-.4,19,.82),(-.55,8,1.3),t);lens=36.5625+(42-36.5625)*smooth((f-97)/13)
  else:
   t=(f-160)/55;pos=mix((.6,-7.8,2.1),(.4,-8.4,2.15),t);target=mix((-.55,8,1.3),(-.65,8.6,1.35),t);lens=42+.5*t
  aim(pos,target,lens)
 elif f<=235:
  t=smooth((f-215)/20);aim(mix((.4,-8.4,2.15),(.4,13.3,2.05),t),mix((-.65,8.6,1.35),(0,19,1.68),t),42.5+22.5*t)
 else:
  t=(f-236)/64;aim((.4,13.3+.114*t,2.05),(0,19,1.68),65)
 bpy.context.view_layer.update();cq=cam.matrix_world.to_quaternion()
 # Each shot reestablishes roots, masks and props; body planes remain vertical and soles supported.
 roots={};bases={}
 for who,y in [('challenger',0),('eddie',19)]:
  root=V((-.9 if who=='challenger' else 0,y,1.058));basis=body_basis(root);body=O[who+'_body'];body.location=root;body.rotation_mode='QUATERNION';body.rotation_quaternion=basis;roots[who]=root;bases[who]=basis
  stepped=math.floor((f-1)*12/30)/12
  bob=(.012*math.sin(stepped*math.tau*1.1) if who=='challenger' and f<=28 else (.010*math.sin((f-96)*.17) if who=='challenger' and 96<=f<=215 else (.012*math.sin((f-236)*.10) if who=='eddie' and f>=236 else 0)))
  for v in body.data.vertices:v.co.y=-1.15 if v.index<2 else 1.15+bob
  hp=O[who+'_head_pivot'];hp.location=root+basis@V((0,.68+bob,.005));hp.rotation_mode='QUATERNION';hp.rotation_quaternion=cq;O[who+'_parallel_camera_target'].location=hp.location+cq@V((0,0,5))
  head=O[who+'_head'];head.location=(0,0,0);head.rotation_euler=(0,0,0)
  head.data.materials[0]=bpy.data.materials[('V5 '+who+' blink') if ((who=='challenger' and (14<=f<=17 or 173<=f<=176)) or (who=='eddie' and 248<=f<=254)) else ('V5 '+who+' head')]
  if who=='challenger' and 96<=f<=215 and not 173<=f<=176:head.data.materials[0]=bpy.data.materials['V6 challenger downstreet gaze']
  if who=='eddie' and 268<=f<=288:
   dip=(smooth((f-268)/12) if f<=280 else (1-1.16*smooth((f-280)/6) if f<=286 else -.16*(1-smooth((f-286)/2))));head.rotation_euler.x=math.radians(-10)*dip;head.location.y=-.035*dip
  leg=O['V5 '+who+' flat vector legs'];rest=LEG_REST[who]
  for v,p in zip(leg.data.vertices,rest):
   w=max(0,min(1,(p.y+1.058)/.72));knee=.013*math.sin((f-96)*.17)*math.sin(math.pi*w) if who=='challenger' and 96<=f<=215 else 0;v.co=p+V((knee*(1 if p.x>0 else -1),bob*w*.25,0))
  for idx,x in enumerate([-.247,.193]):
   patches=sorted([o for o in O if o.name.startswith(who+' sole contact')],key=lambda o:o.name)
   if idx<len(patches):p=root+basis@V((x,-1.058,0));patches[idx].location=(p.x,p.y,.004)
 # Grip-local portable frame: gun/hand recoil together; elbow route remains outward.
 cr=roots['challenger'];cb=bases['challenger'];hand=V((.48,.18,.10));pitch=0
 if f<=28:hand+=V((.008*math.sin(f*2.0),.009*math.cos(f*1.7),0))
 if 29<=f<=35:hand+=V((-.055*recoil,.085*recoil,.025*recoil));pitch=.30*recoil
 if 96<=f<=215:
  lower=smooth((f-96)/26);hand+=V((-.015,-.13*lower+.015*math.sin((f-96)*.8),0));pitch=-.17*lower+.025*math.sin(f*.8)
 gun=O['Challenger_revolver'];gun.rotation_mode='QUATERNION';gun.rotation_quaternion=cb@Quaternion((0,0,1),pitch)@Quaternion((0,1,0),-.66)@Quaternion((1,0,0),-math.pi/2);gun.scale=(1.25*(1+.10*recoil),1.25*(1-.07*recoil),1.25*(1-.05*recoil));hw=cr+cb@hand;gun.location=hw-gun.rotation_quaternion@V((-.20*gun.scale.x,0,.10*gun.scale.z));O['Challenger grip surface'].location=hw
 for i in range(3):O['Grip finger '+str(i)].location=hw+cb@V((.005,.035-i*.027,.025))
 arms('challenger',cb,cr,hand);arms('eddie',bases['eddie'],roots['eddie'],V((.34,-.31,.012)))
 er=roots['eddie'];eb=bases['eddie'];eg=O['Eddie_pearl_revolver'];eg.rotation_mode='QUATERNION';eg.rotation_quaternion=eb@Quaternion((0,0,1),-math.pi/2+math.radians(14))@Quaternion((1,0,0),-math.pi/2);eg.scale=(.5,)*3;eg.location=er+eb@V((-.32,-.43,.012))-eg.rotation_quaternion@V((0,0,.1))
 holster=O['Eddie left black holster'];holster.rotation_mode='QUATERNION';holster.rotation_quaternion=eb@Quaternion((0,0,1),math.radians(14));holster.location=er+eb@V((-.32,-.52,.05))
 b=O['Copper_bullet'];b.location=bp;b.rotation_euler=(0,(f-35)*.23,0);b.hide_render=not 35<=f<=96
 if 80<=f<=96:
  bpy.context.view_layer.update();right=cq@V((1,0,0));pts=[o.matrix_world@V(c) for o in [eg,holster,O['Eddie pearl handle']] for c in o.bound_box];edge=min(p.dot(right) for p in pts);extent=max((b.matrix_world.to_3x3()@v.co).dot(right) for v in b.data.vertices);target=er+eb@V((-.5,-.34,.08));target+=right*(edge-.1201-extent-target.dot(right));w=smooth((f-80)/8);b.location=b.location.lerp(target,w)
 # Recoil flash/smoke and socket-bound sweat.
 bpy.context.view_layer.update();muzzle=gun.matrix_world@V((.35,0,.23));flash=O['Muzzle flash'];flash.hide_render=not 29<=f<=31;flash.location=muzzle;flash.rotation_mode='QUATERNION';flash.rotation_quaternion=cq
 smoke=O['Muzzle smoke'];smoke.hide_render=not 30<=f<=39;age=max(0,f-30);smoke.location=muzzle+V((.02*age,0,.025*age));smoke.scale=(.035+age*.014,)*3
 drop=O['Temple socket sweat'];drop.hide_render=not 110<=f<=221
 if 110<=f<=221:
  u=(f-110)/111;pulse=1+.14*math.sin((f-110)*.36);drop.location=(.345,.10-.15*u,.022);drop.scale=(.035*pulse,.014,.054*pulse)
 tw=O['Rolling_tumbleweed'];tw.hide_render=not 123<=f<=203;t=max(0,min(1,(f-123)/80));tw.location=(-.15+1.6*t,10-4*t,.4+.065*abs(math.sin(t*math.pi*5)));tw.rotation_euler.y=-20*t
 rotation=tw.rotation_euler.to_matrix();low=min((rotation@V(point.co[:3])).z for child in tw.children if child.type=='CURVE' for spline in child.data.splines for point in spline.points);tw.location.z=.007-low+.065*abs(math.sin(t*math.pi*5))
 for child in tw.children_recursive:child.hide_render=tw.hide_render
 for child in b.children_recursive:child.hide_render=b.hide_render
 # Mouth prop inherits real head+hat pitch; base stays in painted aperture.
 ha=O['eddie_head'];straw=O['Eddie mouth-anchored straw'];straw.location=ha.location+ha.rotation_euler.to_quaternion()@V((0,-.25*(1.1/1.53),.006));straw.rotation_mode='QUATERNION';straw.rotation_quaternion=ha.rotation_euler.to_quaternion()@Quaternion((0,0,1),.03*math.sin((f-236)*.15) if f>=236 else 0)
 # Twelve-frame translucent shoulder bridge, including all new vector limbs.
 alpha=1-smooth((f-215)/11)
 for m in bpy.data.materials:
  if m.use_nodes:
   for tag in ['V3 shoulder fade','V3 prop fade']:
    if tag in m.node_tree.nodes:m.node_tree.nodes[tag].inputs[0].default_value=alpha;m.surface_render_method='BLENDED' if 215<=f<=226 else 'DITHERED'
 for o in O:
  if o.name.startswith(('challenger','Grip finger','V5 challenger','V6 challenger')) or o.name in ['Challenger_revolver','Temple socket sweat']:
   if f>=227:o.hide_render=True
   elif o.name!='Temple socket sweat':o.hide_render=False
 ghost=O['Foreground shoulder silhouette'];ghost.hide_render=not 215<=f<=235;age=max(0,min(1,(f-215)/20));bpy.data.materials['V3 translucent silhouette'].node_tree.nodes['Shoulder alpha'].inputs[0].default_value=.25*math.sin(math.pi*age)
 # True camera DOF and an optical hero target, not a post blur.
 cam.data.dof.use_dof=f<=96 or f>=235;cam.data.dof.aperture_fstop=.85
 subject=O['challenger_head_pivot'].location if f<=34 else (b.location if f<=96 else O['eddie_head_pivot'].location);O['V5 hero focus target'].location=subject;cam.data.dof.focus_object=O['V5 hero focus target']
 fill=O['Subtle sky fill'];fill.data.energy=220 if 35<=f<=96 else 350;fill.data.size=3 if 35<=f<=96 else 8
 fill.location=b.location+V((1,-1,2.3)) if 35<=f<=96 else V((0,-3,7));target=b.location if 35<=f<=96 else V((0,9,1));fill.rotation_euler=(target-fill.location).to_track_quat('-Z','Y').to_euler()
 # Existing tapered wind ribbons stay attached and camera-facing.
 for j in range(3):
  ribbon=O['V4 wind ribbon '+str(j)];ribbon.hide_render=not 35<=f<=93
  for i in range(21):
   t=i/20;w=.0018*math.sin(math.pi*t);center=b.location+V(((j-1)*.035,-.16-.40*t,(j-1)*.008));ribbon.data.vertices[2*i].co=center-(cq@V((1,0,0)))*w;ribbon.data.vertices[2*i+1].co=center+(cq@V((1,0,0)))*w
 bpy.context.view_layer.update();vis=gun.hide_render
 if 215<=f<=226:gun.hide_render=True
 ink.update();gun.hide_render=vis

bpy.app.handlers.frame_change_post.clear();bpy.app.handlers.frame_change_post.append(update);update(s)

