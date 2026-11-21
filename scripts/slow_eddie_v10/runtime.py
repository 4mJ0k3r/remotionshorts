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

def old_plan(scene):
 f=scene.frame_current;cam.data.shift_x=0;cam.data.shift_y=0
 if f<=30:
  aim((.8,-3.8,1.5),(-.9,0,1.15),32);frame_point((-.9,0,1.075),.28,.50);focus=V((-.9,0,1.3));fs=2
 elif f<=60:
  t=(f-31)/45;bp=V((-.50,2+16.6*H.ease5(t),.78));aim(bp+V((.86,-.13,.11)),bp,28,math.radians(-6));frame_point(bp,.33,.31);focus=bp;fs=1.4
 elif f<=90:
  u=H.ease5((f-61)/29);bp=V((-.50,2+16.6*H.ease5((f-31)/45),.78));start=bp+V((.86,-.13,.11));pos=start.lerp(V((1.6,17.7,1.02)),u);target=bp.lerp(V((-.20,19,.85)),u);aim(pos,target,28+22*u,math.radians(-6)*(1-u));frame_point((0,19,.72),.5+.43*u,.5+.01*u);focus=bp.lerp(V((-.25,18.8,.75)),H.ease5((f-76)/14));fs=1.4+1.4*u
 elif f<=121:
  aim((1.6,17.7,1.02),(-.20,19,.85),50);frame_point((0,19,.72),.93,.51);focus=V((-.25,18.8,.75));fs=2.8
 elif f<=166:
  if f<=150:d=H.interpolate_distance(2.0,8.1,(f-122)/28)
  else:d=H.interpolate_distance(8.1,19.0,(f-150)/16)
  aim((d*.15,19-d*.989,1.35),(0,19,1.1),35);frame_point((0,19,1.075),.85-.20*H.ease5((f-150)/16),.5);focus=V((0,19,1.7));fs=2.2
 elif f<=181:
  u=H.ease5((f-166)/15);aim(mix((2.85,.21,1.35),(.4,-5.3,1.5),u),mix((0,19,1.1),(0,15,1.1),u),35);frame_point((-.9,0,1.075),-.5+.78*u,.46);focus=V((-.9,0,1.7));fs=2.2
 elif f<=210:
  aim((.4,-5.3,1.5),(0,15,1.1),35);frame_point((-.9,0,1.075),.28,.46);focus=V((-.9,0,1.7));fs=2
 elif f<=254:
  d=H.interpolate_distance(24.3,13.1,(f-210)/44);aim((.4,19-d,1.5),(0,19,1.1),35);focus=V((0,19,1.7));fs=2.2
 else:
  d=2.8 if f<=270 else (2.8+(3.85-2.8)*H.ease5((f-270)/10) if f<=280 else 3.85*(1+.18*(f-280)/20))
  aim((.2,19-d,1.05),(0,19,.9),50);frame_point((0,19,.72),.52,.53 if f<=280 else .53-.11*(f-280)/20);focus=V((-.15,18.8,.75));fs=2.8
 cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=36;cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=fs;O['V7 hero focus'].location=focus;cam.data.dof.focus_object=O['V7 hero focus']

def plan(scene):
 old_plan(scene);f=scene.frame_current
 if 31<=f<=90:
  u=H.ease5((f-61)/29);bp=V((-.50,2+16.6*H.ease5((f-31)/45),.78))
  start=bp+V((.15,-1.15,.20));end=V((1.6,17.7,1.02));aim(start.lerp(end,u),(bp+V((0,4,.1))).lerp(V((-.20,19,.85)),u),28+22*u)
  frame_point(bp.lerp(V((0,19,.72)),u),.33+.60*u,.31+.20*u)
  O['V7 hero focus'].location=bp.lerp(V((-.25,18.8,.75)),H.ease5((f-76)/14));cam.data.dof.aperture_fstop=1.4+1.4*u
 if 211<=f<=254:
  u=H.ease5((f-210)/44);d=H.interpolate_distance(24.3,13.1,u);aim((.4,19-d,1.5),(0,19,1.1),35)
 if f>=255:
  u=H.ease5((f-276)/24);d=3.4*(1+.18*u);aim((.15,19-d,1.05),(0,19,1.0),50);frame_point((0,19,.72),.52,.73-.29*H.ease5((f-276)/10)-.02*H.ease5((f-286)/14));cam.data.dof.aperture_fstop=2.8

_pose_frame=None
def update(scene):
 global _pose_frame
 f=scene.frame_current
 if _pose_frame==f:return
 plan(scene)
 bpy.context.view_layer.update()
 cq=cam.matrix_world.to_quaternion();bases={};roots={}
 for who,y in [('challenger',0),('eddie',19)]:
  pre='V7 '+who+' ';root=O[pre+'root'];root.location=(-.9 if who=='challenger' else 0,y,0);q=facing(root.location);root.rotation_mode='QUATERNION';root.rotation_quaternion=q;roots[who]=root;bases[who]=q
  # Low-amplitude authored acting, with a steady planted root and supported soles.
  if who=='challenger':bob=0
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
     kick={21:.6885,22:1.,23:.8033}.get(f,0);hand=V((.46-.025*kick,-.24+.035*kick,1.48+.085*kick+bob));hand.x+=.005*math.sin(f*1.8);hand.z+=.006*math.cos(f*1.5)
    else:
     drop=H.ease5((f-171)/9);hand=V((.41-.14*drop,-.20+.10*drop,1.02-.28*drop+bob))
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
 gun=O['Challenger_revolver'];gun.scale=(1.5625,1.50,1.50);direction=cb@V((.85,-.75,.10));q=direction.to_track_quat('X','Z');kick={21:.6885,22:1.,23:.8033}.get(f,0);q=q@Quaternion((0,1,0),-math.radians(61)*kick if f<=30 else math.radians(80)*H.ease5((f-171)/9))
 gun.rotation_mode='QUATERNION';gun.rotation_quaternion=q;gun.location=hw-q@V((-.20*1.5625,0,.10*1.50));O['V7 aiming grip'].location=hw
 # A curved ivory palm wraps the rear grip; imported frame continues through the hand.
 er=roots['eddie'];eb=bases['eddie'];eg=O['Eddie_pearl_revolver'];eg.scale=(.50,)*3;eg.rotation_mode='QUATERNION';eg.rotation_quaternion=eb@Quaternion((0,1,0),math.pi/2+math.radians(-13));eg.location=er.matrix_world@V((-.225,-.125,.94+O['V7 eddie torso'].location.z))-eg.rotation_quaternion@V((-.20*.50,0,.10*.50))
 # Separately authored projectile and firing clocks.
 b=O['Copper_bullet'];b.scale=(1.55,)*3;b.hide_render=not 24<=f<=126;b.rotation_mode='QUATERNION';b.rotation_quaternion=V((0,1,0)).to_track_quat('Y','Z')@Quaternion((0,1,0),f*.18)
 if f<=76:
  t=max(0,min(1,(f-31)/45));b.location=(-.50,2+16.6*H.ease5(t),.78)
 else:
  b.location=V((-.52,18.65,.78))
  bpy.context.view_layer.update();cq=cam.matrix_world.to_quaternion();forward=cq@V((0,0,-1));right=cq@V((1,0,0));up=cq@V((0,1,0));depth=(b.location-cam.location).dot(forward);h=depth*36/cam.data.lens;w=h*9/16;b.location=cam.location+forward*depth+right*((.36-.5)*w+cam.data.shift_x*h)+up*((.545-.5)*h+cam.data.shift_y*h)
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
  root=roots[who];hidden=(who=='challenger' and 31<=f<171) or (who=='eddie' and f<=30)
  for ch in [root]+list(root.children_recursive):
   if not any(t in ch.name for t in ['blink','temple sweat']):ch.hide_render=hidden
   if who=='challenger' and ('teeth' in ch.name or 'clenched mouth' in ch.name or 'separator' in ch.name):ch.hide_render=hidden or f<=18
   if ch.name=='V10 cocky smirk':ch.hide_render=hidden or f>18
 O['Challenger_revolver'].hide_render=31<=f<171
 for ch in O['Challenger_revolver'].children_recursive:ch.hide_render=O['Challenger_revolver'].hide_render
 # Hollow twigs roll and hop with exact rotation-aware ground support.
 tw=O['Rolling_tumbleweed'];tw.hide_render=not 205<=f<=242;t=max(0,min(1,(f-205)/37));tw.location=(-.9+1.8*t,17+3*t,.4);tw.rotation_mode='QUATERNION';tw.rotation_quaternion=Quaternion(V((-3,1.8,0)).normalized(),-16*t)
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
   depth=(parent.matrix_world.translation-cam.location).length;thickness=min(.025,max(.002,9.0*depth*36/(1920*cam.data.lens)))
   if parent.name=='Copper_bullet':thickness=min(thickness,.005)
   elif 'revolver' in parent.name.lower():thickness=min(thickness,.006)
   for i,(v,p) in enumerate(zip(o.data.vertices,parent.data.vertices)):v.co=p.co+p.normal*(thickness*(1+.12*math.sin(p.co.x*21+p.co.z*17)))
 material=bpy.data.materials.get('V9 speed streaks')
 if material:material.node_tree.nodes['V9 streak alpha'].inputs[0].default_value=.75*max(0,min(1,(f-33)/2 if f<=35 else (41-f)/6))
 bpy.context.view_layer.update();ink.update();_pose_frame=f

bpy.app.handlers.frame_change_post.clear();bpy.app.handlers.frame_change_post.append(update);update(s)
