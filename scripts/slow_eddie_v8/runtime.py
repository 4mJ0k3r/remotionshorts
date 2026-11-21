import bpy,math,sys
from pathlib import Path
from mathutils import Vector as V,Quaternion,Matrix
s=bpy.context.scene;O=bpy.data.objects;cam=s.camera
sys.path.insert(0,'D:/remotionshorts/scripts/studio');from set_ink import SetInk
ink=SetInk(s)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def mix(a,b,t):return V(a).lerp(V(b),t)
def aim(pos,target,lens,roll=0):
 cam.location=pos;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(V(target)-cam.location).to_track_quat('-Z','Y')@Quaternion((0,0,1),roll);cam.data.lens=lens;cam.data.sensor_fit='AUTO';cam.data.shift_x=0;cam.data.shift_y=0

def facing(root,front=None):
 n=V(front) if front is not None else cam.location-root;n.z=0;n.normalize();right=V((-n.y,n.x,0));return Matrix((right,-n,V((0,0,1)))).transposed().to_quaternion()
def bend_arm(o,a,b,c,radius=.032):
 pts=[]
 for i in range(21):
  t=i/20;pts.append((1-t)**2*a+2*(1-t)*t*b+t*t*c)
 verts=[]
 for i,p in enumerate(pts):
  tangent=(pts[min(i+1,20)]-pts[max(i-1,0)]).normalized();axis=tangent.cross(V((0,1,0)))
  if axis.length<.01:axis=tangent.cross(V((1,0,0)))
  axis.normalize();other=tangent.cross(axis).normalized();r=radius*(1-.17*i/20)
  for j in range(8):a=j*math.tau/8;verts.append(p+r*(math.cos(a)*axis+math.sin(a)*other))
 for v,p in zip(o.data.vertices,verts):v.co=p

def update(scene):
 f=scene.frame_current
 if f<=36:
  t=(f-1)/35;k={30:.022,31:-.015,32:.009,33:0}.get(f,0);aim((.05+.05*t,-3.45+.06*t,1.20),(-.43,0,1.54),40,math.radians(-3)+k)
 elif f<=84:
  t=(f-37)/47;u=3*(1-t)**2*t*.35+3*(1-t)*t*t*.80+t**3;bp=V((-.72+.18*u,3+15.45*u,1.02-.28*t));aim(bp+V((.65,-2.30,.55)),(0,25,1.25),28)
 elif f<=105:
  t=(f-85)/20;aim((-.32,16.5+.04*t,1.05),(-.32,19,.78),70)
 elif f<=160:
  t=(f-106)/54;y=20.9-.7*smooth((f-106)/29) if f<=135 else 20.2-2.2*smooth((f-135)/25);aim((.50,y,1.55+.03*t),(-.9,0,2.60),32)
 elif f<=204:
  t=(f-161)/43;aim(mix((.55,-8.0,2.5),(.15,-8.5,2.5),t),mix((-.25,8,1.35),(-.1,8.8,1.4),t),40)
 elif f<=245:
  t=smooth((f-205)/40);aim(mix((.15,-8.5,2.5),(.25,15.5,1.40),t),mix((-.1,8.8,1.4),(0,19,1.40),t),40+20*t)
 else:
  t=(f-246)/54;aim((.25,15.5+.070*t,1.40),(0,19,1.40),60)
 bpy.context.view_layer.update()
 cq=cam.matrix_world.to_quaternion();bases={};roots={}
 for who,y in [('challenger',0),('eddie',19)]:
  pre='V7 '+who+' ';root=O[pre+'root'];root.location=(-.9 if who=='challenger' else 0,y,0);q=facing(root.location);root.rotation_mode='QUATERNION';root.rotation_quaternion=q;roots[who]=root;bases[who]=q
  # Low-amplitude authored acting, with a steady planted root and supported soles.
  if who=='challenger':bob=.009*math.sin(math.floor((f-1)*12/30)*.58) if f<=28 else (.009*math.sin((f-161)*.18) if 161<=f<=215 else 0)
  else:bob=.009*math.sin((f-246)*.11) if f>=246 else 0
  O[pre+'torso'].location.z=-.22+bob;head=O[pre+'head pivot'];head.rotation_euler=(0,0,0)
  if who=='eddie' and 268<=f<=292:
   t=(f-268)/24;dip=math.sin(t*math.pi)**2;head.rotation_euler.x=math.radians(10)*dip
  blink=(who=='challenger' and (14<=f<=17 or 175<=f<=178)) or (who=='eddie' and 249<=f<=254)
  for o in root.children_recursive:
   if any(tag in o.name for tag in ['open pupil','eye glint','upper lid']):o.hide_render=blink
   if 'blink' in o.name:o.hide_render=not blink
  # Counter-posed soft elbows, continuous swept surfaces, rounded connected hand endpoints.
  for side,label in [(-1,'left'),(1,'right')]:
   hand=V((side*.32,-.055,.76+bob));shoulder=V((side*.30,0,1.25+bob));elbow=V((side*.46,-.02,.98+bob))
   if who=='challenger' and side==1:
    if f<=36:
     kick={29:.20,30:.75,31:1.,32:.55,33:-.10,34:0}.get(f,0);hand=V((.46-.025*kick,-.24+.035*kick,1.35+.085*kick+bob));hand.x+=.005*math.sin(f*1.8);hand.z+=.006*math.cos(f*1.5)
    else:hand=V((.41,-.20,1.02+.012*math.sin(f*.65)+bob))
    elbow=V((.48,-.05,1.13+bob))
   bend_arm(O[pre+label+' arm'],shoulder,elbow,hand);O[pre+label+' hand'].location=hand
  if who=='challenger':
   drop=O[pre+'temple sweat'];drop.hide_render=not 161<=f<=225;u=max(0,min(1,(f-161)/64));z=.13-.13*u;a=math.atan2(-z,.31);rr=.363*(1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9));drop.location=(.31,-.29*math.sqrt(max(.025,1-(.31*.31+z*z)/(rr*rr)))-.014,z);drop.scale=(1+.10*math.sin(f*.4),1,1+.08*math.sin(f*.4))
 # Downloaded gun + real front/back gripping fingers are solved from one local surface frame.
 bpy.context.view_layer.update()
 for who in ['challenger','eddie']:
  for idx,label in enumerate(['left','right']):
   patch=O[who+' sole contact'+('' if idx==0 else '.001')];foot=O['V7 '+who+' '+label+' boot'];p=roots[who].matrix_world@foot.location;patch.location=(p.x,p.y,-.0095);patch.scale=(.080,.062,.0005);patch.rotation_mode='QUATERNION';patch.rotation_quaternion=bases[who]
 cr=roots['challenger'];cb=bases['challenger'];hw=cr.matrix_world@O['V7 challenger right hand'].location
 gun=O['Challenger_revolver'];gun.scale=(1.25,)*3;direction=cb@V((.85,-.75,.10));q=direction.to_track_quat('X','Z');kick={29:.20,30:.75,31:1.,32:.55,33:-.10,34:0}.get(f,0);q=q@Quaternion((0,1,0),-.25*kick if f<=36 else .10)
 gun.rotation_mode='QUATERNION';gun.rotation_quaternion=q;gun.location=hw-q@V((-.20*1.25,0,.10*1.25));O['V7 aiming grip'].location=hw
 # A curved ivory palm wraps the rear grip; imported frame continues through the hand.
 er=roots['eddie'];eb=bases['eddie'];eg=O['Eddie_pearl_revolver'];eg.scale=(.50,)*3;eg.rotation_mode='QUATERNION';eg.rotation_quaternion=eb@Quaternion((0,1,0),math.pi/2+math.radians(-13));eg.location=er.matrix_world@V((-.325,-.125,.94+O['V7 eddie torso'].location.z))-eg.rotation_quaternion@V((-.20*.50,0,.10*.50))
 b=O['Copper_bullet'];b.scale=(2.5,)*3;b.hide_render=not 34<=f<=105;b.rotation_mode='QUATERNION';level=smooth((f-76)/12);direction=V((.24*(1-level)+.12*level,.97,-.23*(1-level))).normalized();b.rotation_quaternion=direction.to_track_quat('Y','Z')@Quaternion((0,1,0),(f-34)*.23)
 if f<=84:
  t=max(0,min(1,(f-37)/47));u=3*(1-t)**2*t*.35+3*(1-t)*t*t*.80+t**3;b.location=(-.72+.18*u,3+15.45*u,1.02-.28*t)
 else:
  bpy.context.view_layer.update();target=er.matrix_world@V((-.52,-.27,.72));right=cq@V((1,0,0));props=[O['V7 eddie contoured sheath'],eg,O['V7 pearl revolver butt']];edge=min((o.matrix_world@V(c)).dot(right) for o in props for c in o.bound_box);extent=max((b.matrix_world.to_3x3()@v.co).dot(right) for v in b.data.vertices);target+=right*(edge-.020-extent-target.dot(right));b.location=target
 for child in b.children_recursive:child.hide_render=b.hide_render
 # Burst follows the actual muzzle, travels along barrel, with orange edge and hot yellow core.
 bpy.context.view_layer.update();fx=O['V7 muzzle FX root'];fx.location=gun.matrix_world@V((.35,0,.23));fx.rotation_mode='QUATERNION';fx.rotation_quaternion=q
 for child in fx.children_recursive:child.hide_render=not 30<=f<=35
 fx.scale=({30:.55,31:1.,32:.88,33:.65,34:.35,35:.15}.get(f,1.),)*3
 for j in range(3):
  spark=O['V8 spark '+str(j)];spark.hide_render=not 30<=f<=36;age=max(0,f-30);a=j*math.tau/3+.25;start=V((.24+.05*age,(.045+.015*age)*math.cos(a),(.045+.015*age)*math.sin(a)));end=start+V((.05,.006*math.cos(a),.006*math.sin(a)))
  for p,v in zip(spark.data.splines[0].points,[start,end]):p.co=(*v,1)
 if 34<=f<=36:
  launch={34:.06,35:.22,36:.48}[f];b.scale=(1.,)*3;b.location=fx.location+(q@V((launch,0,0)));b.rotation_quaternion=(q@V((1,0,0))).to_track_quat('Y','Z')@Quaternion((0,1,0),(f-34)*.5)
 for child in fx.children:
  if child.name.startswith('V8 ragged flame'):
   age=max(0,f-30);i=int(child.name.rsplit(' ',1)[1]);child.scale=(1.,1+.12*math.sin(age*2+i),1+.15*math.cos(age*2.3+i))
 for i in range(3):
  smoke=O['V7 smoke '+str(i)];age=f-32-i*2;smoke.hide_render=not 0<=age<=15;smoke.location=fx.location+q@V((.04*max(0,age)+i*.02,0,.024*max(0,age)));smoke.scale=(.65+.22*max(0,age),)*3
  bs=next(n for n in smoke.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Alpha'].default_value=.28*max(0,1-max(0,age)/15)
 # Hollow twigs roll and hop with exact rotation-aware ground support.
 tw=O['Rolling_tumbleweed'];tw.hide_render=not 160<=f<=205;t=max(0,min(1,(f-160)/45));tw.location=(-.9+1.8*t,9-2*t,.4);tw.rotation_euler=(.1,-16*t,.1)
 rot=tw.rotation_euler.to_matrix();low=min((rot@V(p.co[:3])).z for ch in tw.children if ch.type=='CURVE' for sp in ch.data.splines for p in sp.points);tw.location.z=.008-low+.05*abs(math.sin(t*math.pi*4))
 for ch in tw.children_recursive:ch.hide_render=tw.hide_render
 # No static shoulder overlay: the real 3D actor passes outside the left edge during push-in.
 # Focus is driven by the relevant physical surface, not a generic subject center.
 cam.data.dof.use_dof=not 106<=f<=245;cam.data.dof.aperture_fstop=2.0 if f<=84 else (2.8 if f<=105 else 1.8)
 if f<=36:focus=roots['challenger'].matrix_world@V((.10,-.18,1.55))
 elif f<=105:focus=b.location if f<=84 else er.matrix_world@V((-.25,-.20,.73))
 else:focus=er.matrix_world@V((0,-.28,1.70))
 O['V7 hero focus'].location=focus;cam.data.dof.focus_object=O['V7 hero focus'];cam.data.dof.focus_distance=(focus-cam.location).length
 # Keep the cool broad fill on the subjects as camera moves along the long street.
 fill=O['Subtle sky fill'];fill.location=(-3,8 if 37<=f<=84 else (17 if f>=85 and f<=160 or f>=246 else -2),7);target=V((0,10 if 37<=f<=84 else (19 if f>=85 and f<=160 or f>=246 else 0),1.5));fill.rotation_euler=(target-fill.location).to_track_quat('-Z','Y').to_euler()
 for j in range(3):
  rib=O['V4 wind ribbon '+str(j)];rib.hide_render=not 37<=f<=84
  for i in range(21):
   t=i/20;w=.002*math.sin(math.pi*t);center=b.location+V(((j-1)*.025,-.22-.45*t,(j-1)*.012));rib.data.vertices[2*i].co=center-cq@V((w,0,0));rib.data.vertices[2*i+1].co=center+cq@V((w,0,0))
 bpy.context.view_layer.update();ink.update()

bpy.app.handlers.frame_change_post.clear();bpy.app.handlers.frame_change_post.append(update);update(s)
