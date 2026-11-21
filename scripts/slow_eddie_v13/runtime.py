import bpy,math,sys
from pathlib import Path
from mathutils import Vector as V,Quaternion,Matrix
s=bpy.context.scene;O=bpy.data.objects;cam=s.camera
# Retain baked channels for inspection; the deterministic renderer owns their evaluation.
for data in [cam,cam.data]:
 if data.animation_data and data.animation_data.action:
  for fc in data.animation_data.action.fcurves:fc.mute=True
sys.path.insert(0,'D:/remotionshorts/scripts/studio');from set_ink import SetInk
ink=SetInk(s)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def mix(a,b,t):return V(a).lerp(V(b),t)
def aim(pos,target,lens,roll=0):
 cam.location=pos;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(V(target)-cam.location).to_track_quat('-Z','Y')@Quaternion((0,0,1),roll);cam.data.lens=lens;cam.data.sensor_fit='VERTICAL';cam.data.shift_x=0;cam.data.shift_y=0

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

sys.path.insert(0,'D:/remotionshorts/tools/V9_Parity_Packet/V9_Parity_Packet')
import v9_patch_helpers as H
from bpy_extras.object_utils import world_to_camera_view as project

def frame_point(world,x,y):
 bpy.context.view_layer.update();uv=project(s,cam,V(world));cam.data.shift_x+=(uv.x-x)*s.render.resolution_x/s.render.resolution_y;cam.data.shift_y+=uv.y-y

def flight(f):
 import json
 if '_flight12' not in globals():globals()['_flight12']=json.loads(bpy.data.texts['V12 flight.json'].as_string()) if 'V12 flight.json' in bpy.data.texts else json.loads(bpy.data.texts['V11 flight.json'].as_string())
 return V(_flight12[str(max(25,min(91,f)))])

def plan(scene):
 f=scene.frame_current;cam.data.shift_x=0;cam.data.shift_y=0
 if f<=30:
  aim((.8,-3.8,1.5),(-.9,0,1.15),32);frame_point((-.9,0,1.075),.28,.50);focus=V((-.9,0,1.3));fs=2
 elif f<=90:
  bp=flight(f);u=H.ease5((f-75)/15);start=bp+V((.52,-1.6,.2));aim(start.lerp(V((.8,17.4,1.05)),u),V((0,19,1.0)).lerp(V((0,19,.85)),u),28+22*u)
  bpy.context.view_layer.update();vb=project(s,cam,bp);ve=project(s,cam,V((0,19,1.0)));xcenter=(vb.x+ve.x)/2
  cam.data.shift_x+=(xcenter-.5)*9/16;sx,sy=cam.data.shift_x,cam.data.shift_y
  frame_point((0,19,.72),.89,.5);cam.data.shift_x=sx+(cam.data.shift_x-sx)*u;cam.data.shift_y=sy+(cam.data.shift_y-sy)*u
  # Fit both tracked subjects continuously; retreat along the existing optical axis if their span exceeds the gate.
  if f<90:
   forward=cam.matrix_world.to_quaternion()@V((0,0,-1));margin=.15-.11*H.ease5((f-80)/10)
   for fit in range(40):
    bpy.context.view_layer.update();ub=project(s,cam,bp);ue=project(s,cam,V((0,19,.85)))
    if ub.z>0 and ue.z>0 and abs(ub.x-ue.x)<=1-2*margin:break
    cam.location-=forward*.2
   lo=margin-min(ub.x,ue.x);hi=1-margin-max(ub.x,ue.x);dx=max(lo,min(hi,0));cam.data.shift_x-=dx*9/16
  focus=bp.lerp(V((-.25,18.8,.75)),H.ease5((f-76)/14));fs=2.8
 elif f<=122:
  aim((.8,17.4,1.05),(0,19,.85),50);frame_point((0,19,.72),.89,.5);focus=V((-.25,18.8,.75));fs=2.8
 elif f<=181:
  u=H.ease5((f-122)/59);pos=mix((.8,17.4,1.05),(0,-7.5,1.5),u);aim(pos,mix((0,19,.85),(0,19,1.1),u),50)
  frame_point((0,19,.72),.89,.5);sx,sy=cam.data.shift_x,cam.data.shift_y
  w=H.ease5((f-150)/16);frame_point((-.9,0,1.075),-.25+.53*H.ease5((f-166)/15),.46);cam.data.shift_x=sx+(cam.data.shift_x-sx)*w;cam.data.shift_y=sy+(cam.data.shift_y-sy)*w
  focus=mix((-.25,18.8,.75),(-.9,0,1.7),u);fs=2.8
 elif f<=254:
  u=H.ease5((f-210)/44);aim((0,-7.5+13.4*u,1.5),(0,19,1.1),50)
  # Carry the established wide-shot shift into the push rather than resetting at211.
  if '_wide_shift' not in globals():
   saved=scene.frame_current;scene.frame_current=181;plan(scene);globals()['_wide_shift']=(cam.data.shift_x,cam.data.shift_y);scene.frame_current=saved;aim((0,-7.5+13.4*u,1.5),(0,19,1.1),50)
  cam.data.shift_x=_wide_shift[0]*(1-u);cam.data.shift_y=_wide_shift[1]*(1-u)
  focus=mix((-.9,0,1.7),(0,19,1.7),u);fs=2.8
 else:
  u=H.ease5((f-280)/20);d=2.3+(4.55-2.3)*u;aim((.18,19-d,1.05),(0,19,1.0),50)
  by=.5 if f<=280 else (.5-.30*H.ease5((f-280)/6) if f<=286 else .20+.22*H.ease5((f-286)/14))
  frame_point((0,19,.72),.62,by);cam.location.x+=.006*math.sin((f-255)*.09);focus=V((-.15,18.8,.75));fs=2.8
 cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=36;cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=fs;O['V7 hero focus'].location=focus;cam.data.dof.focus_object=O['V7 hero focus']

_pose_frame=None
def update(scene):
 global _pose_frame
 f=scene.frame_current
 if _pose_frame==f:return
 plan(scene)
 bpy.context.view_layer.update()
 cq=cam.matrix_world.to_quaternion();bases={};roots={}
 for who,y in [('challenger',0),('eddie',19)]:
  pre='V7 '+who+' ';root=O[pre+'root'];root.location=(-.9 if who=='challenger' else 0,y,0);q=facing(root.location);q=q@Quaternion((0,0,1),math.radians(25)*H.ease5((f-160)/11)) if who=='challenger' else q;root.rotation_mode='QUATERNION';root.rotation_quaternion=q;roots[who]=root;bases[who]=q
  # Low-amplitude authored acting, with a steady planted root and supported soles.
  if who=='challenger':bob=.003*math.sin((f-184)*.15) if 184<=f<=210 else 0
  else:bob=0
  O[pre+'torso'].location.z=-.22+bob;head=O[pre+'head pivot'];head.rotation_euler=(0,0,0)
  if False:
   t=(f-268)/24;dip=math.sin(t*math.pi)**2;head.rotation_euler.x=math.radians(10)*dip
  blink=False
  if who=='challenger' and f>=171:head.rotation_euler.z=math.radians(25)
  if who=='challenger' and f>=211:root.location.x-=.10*(f-210)
  for o in root.children_recursive:
   if any(tag in o.name for tag in ['open pupil','eye glint','upper lid']):o.hide_render=blink
   if 'blink' in o.name:o.hide_render=not blink
  # Counter-posed soft elbows, continuous swept surfaces, rounded connected hand endpoints.
  for side,label in [(-1,'left'),(1,'right')]:
   hand=V((side*.26,-.055,.76+bob));shoulder=V((side*.24,0,1.25+bob));elbow=V((side*.46,-.02,.98+bob))
   if who=='challenger' and side==1:
    if f<=30:
     kick={21:.6885,22:1.,23:.8033,24:.8033,25:.72,26:.6}.get(f,0);hand=V((.46-.025*kick,-.24+.035*kick,1.48+.085*kick+bob));hand.x+=.005*math.sin(f*1.8);hand.z+=.006*math.cos(f*1.5)
    else:
     drop=H.ease5((f-160)/11);hand=V((.41-.14*drop,-.20+.10*drop,1.02-.28*drop+bob))
    elbow=V((.48,-.05,1.13+bob))
   bend_arm(O[pre+label+' arm'],shoulder,elbow,hand);O[pre+label+' hand'].location=hand
  if who=='challenger':
   drop=O[pre+'temple sweat'];drop.hide_render=not 161<=f<=225;u=max(0,min(1,(f-161)/64));z=.04-.09*u;a=math.atan2(-z,.31);rr=.363*(1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9));drop.location=(.31,-.29*math.sqrt(max(.025,1-(.31*.31+z*z)/(rr*rr)))-.014,z);drop.scale=(1+.10*math.sin(f*.4),1,1+.08*math.sin(f*.4))
 # Downloaded gun + real front/back gripping fingers are solved from one local surface frame.
 bpy.context.view_layer.update()
 for who in ['challenger','eddie']:
  for idx,label in enumerate(['left','right']):
   patch=O[who+' sole contact'+('' if idx==0 else '.001')];foot=O['V7 '+who+' '+label+' boot'];p=roots[who].matrix_world@foot.location;patch.location=(p.x,p.y,-.0095);patch.scale=(.080,.062,.0005);patch.rotation_mode='QUATERNION';patch.rotation_quaternion=bases[who]
 cr=roots['challenger'];cb=bases['challenger'];hw=cr.matrix_world@O['V7 challenger right hand'].location
 gun=O['Challenger_revolver'];gun.scale=(1.5625,1.50,1.50);direction=cb@V((.85,-.75,.10));q=direction.to_track_quat('X','Z');kick={21:.6885,22:1.,23:.8033,24:.8033,25:.72,26:.6}.get(f,0);q=q@Quaternion((0,1,0),-math.radians(61)*kick if f<=30 else math.radians(80)*H.ease5((f-160)/11))
 gun.rotation_mode='QUATERNION';gun.rotation_quaternion=q;gun.location=hw-q@V((-.20*1.5625,0,.10*1.50));O['V7 aiming grip'].location=hw
 if 25<=f<=33 and 'V13 locked editorial.json' in bpy.data.texts:
  import json
  state=json.loads(bpy.data.texts['V13 locked editorial.json'].as_string())[str(f)];cq0=Quaternion(state['rotation']);direction=cq0@V((math.cos(math.radians(8)),math.sin(math.radians(8)),-.1));q=direction.to_track_quat('X','Z');gun.rotation_quaternion=q;gun.location=V(state['muzzle'])-q@V((.35*1.5625,0,.23*1.5));hw=gun.location+q@V((-.20*1.5625,0,.10*1.50));local=cr.matrix_world.inverted()@hw;O['V7 challenger right hand'].location=local;bend_arm(O['V7 challenger right arm'],V((.24,0,1.25)),V((.48,-.05,1.25)),local);O['V7 aiming grip'].location=hw

 # A curved ivory palm wraps the rear grip; imported frame continues through the hand.
 er=roots['eddie'];eb=bases['eddie'];eg=O['Eddie_pearl_revolver'];eg.scale=(.50,)*3;eg.rotation_mode='QUATERNION';eg.rotation_quaternion=eb@Quaternion((0,1,0),math.pi/2+math.radians(-13));eg.location=er.matrix_world@V((-.225,-.125,.94+O['V7 eddie torso'].location.z))-eg.rotation_quaternion@V((-.20*.50,0,.10*.50))
 # Separately authored projectile and firing clocks.
 b=O['Copper_bullet'];size=3.0-(3.0-1.2)*H.ease5((f-76)/14);b.scale=(size,)*3;b.hide_render=not 31<=f<=126;b.rotation_mode='QUATERNION';b.rotation_quaternion=V((0,1,0)).to_track_quat('Y','Z')@Quaternion((0,1,0),f*.18)
 if f<=76:
  t=max(0,min(1,(f-31)/45));b.location=(-.50,2+16.6*H.ease5(t),.78)
 else:
  b.location=V((-.52,18.65,.78))
  bpy.context.view_layer.update();cq=cam.matrix_world.to_quaternion();forward=cq@V((0,0,-1));right=cq@V((1,0,0));up=cq@V((0,1,0));depth=(b.location-cam.location).dot(forward);h=depth*36/cam.data.lens;w=h*9/16;b.location=cam.location+forward*depth+right*((.08-.5)*w+cam.data.shift_x*h)+up*((.545-.5)*h+cam.data.shift_y*h)
  # Side-on hold reads in screen space, never a primer-facing disk.
  b.rotation_quaternion=(cam.matrix_world.to_quaternion()@V((1,0,0))).to_track_quat('Y','Z')@Quaternion((0,1,0),f*.18)
 if f>=122:b.location+=(cam.matrix_world.to_quaternion()@V((-1,0,0)))*(.35*(f-121)**1.6)
 if 31<=f<=90:b.rotation_quaternion=(cam.matrix_world.to_quaternion()@V((1,.15,0))).to_track_quat('Y','Z')@Quaternion((0,1,0),f*.18)
 for ch in b.children_recursive:ch.hide_render=b.hide_render
 bpy.context.view_layer.update();fx=O['V7 muzzle FX root'];fx.location=gun.matrix_world@V((.35,0,.23));fx.rotation_mode='QUATERNION';fx.rotation_quaternion=q;fx.scale=(.65,)*3
 for ch in fx.children_recursive:ch.hide_render=not 21<=f<=33
 for i in range(3):
  smoke=O['V7 smoke '+str(i)];smoke.hide_render=not 22<=f<=35;smoke.location=fx.location+V((.02*(f-22),0,.015*(f-22)));smoke.scale=(1+.15*max(0,f-22),)*3
 if 24<=f<=30:b.location=fx.location+(q@V((.05+.06*(f-24),0,0)));b.rotation_quaternion=(q@V((1,0,0))).to_track_quat('Y','Z')
 # Fixed directional expression / relaxed hands; source blink and nod removed.
 for who in ['challenger','eddie']:
  root=roots[who];hidden=(who=='challenger' and 31<=f<160) or (who=='eddie' and f<=30)
  for ch in [root]+list(root.children_recursive):
   if not any(t in ch.name for t in ['blink','temple sweat']):ch.hide_render=hidden
   if who=='challenger' and ('teeth' in ch.name or 'clenched mouth' in ch.name or 'separator' in ch.name):ch.hide_render=hidden or (not 19<=f<=25 if f<=30 else False)
   if ch.name=='V10 cocky smirk':ch.hide_render=hidden or not (f<=18 or 26<=f<=30)
   if ch.name.startswith('V13 smirk lid'):ch.hide_render=hidden or f>18
 O['Challenger_revolver'].hide_render=31<=f<171
 for ch in O['Challenger_revolver'].children_recursive:ch.hide_render=O['Challenger_revolver'].hide_render
 # Hollow twigs roll and hop with exact rotation-aware ground support.
 tw=O['Rolling_tumbleweed'];tw.hide_render=not 205<=f<=235;t=max(0,min(1,(f-205)/30));forward=cam.matrix_world.to_quaternion()@V((0,0,-1));forward.z=0;forward.normalize();right=cam.matrix_world.to_quaternion()@V((1,0,0));p=cam.location+forward*7+right*(-1.4+.8*t);tw.location=(p.x,p.y,0);depth=7;rad=max(V(v.co[:3]).length for c in tw.children if c.type=='CURVE' for sp in c.data.splines for v in sp.points);sc=.03*(depth*36/cam.data.lens)/(2*rad);tw.scale=(sc,)*3;tw.rotation_mode='QUATERNION';tw.rotation_quaternion=Quaternion(V((-3,1.8,0)).normalized(),-16*t)
 rot=tw.rotation_quaternion.to_matrix();low=min((rot@V(p.co[:3])).z for ch in tw.children if ch.type=='CURVE' for sp in ch.data.splines for p in sp.points);tw.location.z=.008-low*tw.scale.z+.020*abs(math.sin(t*math.pi*4))
 for ch in tw.children_recursive:ch.hide_render=tw.hide_render or not ch.get('v9_branch',False)
 for j in range(3):
  rib=O['V4 wind ribbon '+str(j)];rib.hide_render=not 34<=f<=40
  for i in range(21):
   t=i/20;w=.002*math.sin(math.pi*t);center=b.location+V(((j-1)*.025,-.22-.45*t,(j-1)*.012));rib.data.vertices[2*i].co=center-cq@V((w,0,0));rib.data.vertices[2*i+1].co=center+cq@V((w,0,0))
 # Distance-aware actor ink; preserve thin metal/projectile edges.
 for o in O:
  if o.get('v7_outline') and o.parent and o.parent.type=='MESH' and len(o.data.vertices)==len(o.parent.data.vertices):
   parent=o.parent
   depth=(parent.matrix_world.translation-cam.location).length;thickness=min(.025,max(.002,7.0*depth*36/(1920*cam.data.lens)))
   if parent.name=='Copper_bullet':thickness=min(thickness,.0015)
   elif 'revolver' in parent.name.lower():thickness=min(thickness,.006)
   for i,(v,p) in enumerate(zip(o.data.vertices,parent.data.vertices)):v.co=p.co+p.normal*(thickness*(1+.12*math.sin(p.co.x*21+p.co.z*17)))
 material=bpy.data.materials.get('V9 speed streaks')
 if material:material.node_tree.nodes['V9 streak alpha'].inputs[0].default_value=.75*max(0,min(1,(f-33)/2 if f<=35 else (41-f)/6))
 if 'V12 flight.json' in bpy.data.texts:
  import json
  if '_flight' not in globals():globals()['_flight']=json.loads(bpy.data.texts['V12 flight.json'].as_string())
  if 25<=f<=121:
   p=V(_flight[str(min(f,91))]);v=V(_flight[str(min(f+1,91))])-p if f<=90 else V(_flight['91'])-V(_flight['90'])
   b.location=p;b.rotation_quaternion=v.normalized().to_track_quat('Y','Z')@Quaternion((0,1,0),f*.18)
 bpy.context.view_layer.update();ink.update();_pose_frame=f

bpy.app.handlers.frame_change_post.clear();bpy.app.handlers.frame_change_post.append(update);update(s)
