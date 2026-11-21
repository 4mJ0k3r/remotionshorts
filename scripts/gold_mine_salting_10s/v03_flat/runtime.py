"""Pure frame-addressable story evaluation. One-based Blender frames."""
import bpy,math,json,sys,traceback,os
import numpy as np
from mathutils import Vector as V,Quaternion,Matrix
import ricks_lookdev as look
from geometry import bezier_points,set_line
S=bpy.context.scene;O=bpy.data.objects
from set_ink import SetInk
WORLD_INK=SetInk(S);look.mark_role(WORLD_INK.output,'ink')
HULLS=[]
for h in [o for o in S.objects if o.get('ink_base_width')]:
 source=h.parent;co=np.empty(len(source.data.vertices)*3,dtype=np.float32);normal=co.copy();source.data.vertices.foreach_get('co',co);source.data.vertices.foreach_get('normal',normal);HULLS.append((h,source,co,normal))
ENV=json.loads(bpy.data.texts['audio_envelope.json'].as_string())
def ease(f,a,b):return look.ease5((f-a)/(b-a))
def window(f,a,b,c,d):return ease(f,a,b)*(1-ease(f,c,d))
def visible(o,value):
 o.hide_render=o.hide_viewport=not value
 for c in o.children_recursive:c.hide_render=c.hide_viewport=not value
def pose_hand(name,side,matrix,radius=.036,rotate=0):
 h=O[name+(' L hand frame' if side<0 else ' R hand frame')]
 h.matrix_world=matrix @ Matrix.Rotation(rotate,4,'X')
 for finger in [c for c in h.children if 'wrapping finger' in c.name]:
  i=int(finger.name.split('wrapping finger ')[1].split('.')[0])
  pts=[(radius*math.cos(a),radius*math.sin(a),-.025+i*.025) for a in [-.3+j*math.pi*1.55/16 for j in range(17)]]
  set_line(finger,pts)
 return h.matrix_world.translation.copy()
def point_matrix(p):return Matrix.Translation(V(p))
def solve_arm(name,side,target):
 root=O[name+' root'];shoulder=O[name+' body'].matrix_world @ V((side*.235,0,1.105))
 t=V(target);a=shoulder;b=a+V((side*.12,-.16,-.11));c=t+V((side*.10,.04,-.10))
 pts=bezier_points(a,b,c,t)
 local=[root.matrix_world.inverted() @ p for p in pts]
 set_line(O[name+(' L arm' if side<0 else ' R arm')],local)
def aim_camera(pos,target,lens=45,fstop=3.5):
 cam=S.camera;cam.location=pos;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(V(target)-cam.location).to_track_quat('-Z','Y')
 cam.data.lens=lens;cam.data.dof.aperture_fstop=fstop;O['Story focus'].location=target
 cam.data.dof.focus_distance=(V(target)-cam.location).length
def set_face(name,f,talk=False,wink=False):
 head=O[name+' head pivot'];blink=window(f,153,155,156,159)>.55 if name=='Miner' else window(f,177,179,180,183)>.55
 for side in [-1,1]:
  pre=name+(' L' if side<0 else ' R');closed=blink or (wink and side<0)
  visible(O[pre+' eye'],not closed);visible(O[pre+' glint'],not closed);visible(O[pre+' closed'],closed)
 mouth=0
 if talk:
  e=ENV[max(0,min(300,f-1))]
  mouth=0 if e<.10 else 1+min(3,int(e*4))
 for i in range(5):visible(O[name+' mouth '+str(i)],i==mouth)
 for k in [2,4]:visible(O[name+' teeth '+str(k)],k==mouth)
 visible(O[name+' tongue 3'],mouth==3)
_last_frame=None
def update(frame):
 global _last_frame
 f=int(frame)
 if _last_frame==f:return
 t=(f-1)/30
 miner=O['Miner root'];buddy=O['Buddy root'];miner.location=(0,0,0);miner.rotation_euler=(0,0,0);buddy.location=(-.52,3.45,0)
 visible(buddy,True);visible(O['Buddy mug root'],True)
 visible(O['Overhead dust cone'],f<=30)
 for name in ['Miner','Buddy']:
  O[name+' body'].location=(0,0,.075 if name=='Buddy' else 0);O[name+' body'].rotation_euler=(0,0,0)
  head=O[name+' head pivot'];head.location=(0,0,1.49);head.rotation_euler=(0,0,0)
 # Body support remains exact and independent of face accents.
 for name in ['Miner','Buddy']:
  for side in [-1,1]:
   if name=='Miner':
    a=(side*.115,0,.66);b=(side*.14,.01,.42);c=(side*.16,-.04,.15);foot=(side*.16,-.04,.115)
   else:
    a=(side*.115,0,.745);b=(side*.22,-.42,.58);c=(side*.22,-.60,.08);foot=(side*.22,-.60,.045)
   set_line(O[name+(' L leg' if side<0 else ' R leg')],bezier_points(a,b,b,c))
   O[name+(' L boot' if side<0 else ' R boot')].location=foot
   O[name+(' L sole contact' if side<0 else ' R sole contact')].location=(foot[0],foot[1],.074 if name=='Miner' else .004)
 # Shoulder / stock / breach all share a consistent physical weapon assembly.
 gun=O['Shotgun root'];barrels=O['Shotgun barrel hinge'];loading=1-ease(f,22,35);raiseP=ease(f,26,45)
 raiseP=ease(f,22,33)
 p=V((-.03,-.24,1.04)).lerp(V((.04,.10,1.22)),raiseP)
 direction=V((.80,.58,.09)).lerp(V((.12,.99,.075)),raiseP).normalized()
 recoil=window(f,39,41,43,50)
 p-=direction*.065*recoil
 if f>=271:
  p=V((.20,-.015,1.34));direction=V((.72,.12,.68)).normalized()
 gun.rotation_mode='QUATERNION';gun.matrix_world=Matrix.Translation(p) @ direction.to_track_quat('Y','Z').to_matrix().to_4x4()
 barrels.rotation_euler.x=-.30*loading if f<45 else 0
 O['Miner head pivot'].rotation_euler.y=-.035*window(f,30,42,65,75)
 # Final shell and wink are finite actions, then stable endpoint.
 shell=O['Gold shell root']
 if f<30:
  shell.matrix_world=gun.matrix_world @ Matrix.Translation(V((.031,.02,.10*(1-ease(f,8,25))+.025))) @ Matrix.Rotation(math.pi/2,4,'X')
 elif f>=271:
  q=ease(f,271,281);shell.location=V((-.25,-.23,.92)).lerp(V((-.29,-.25,1.08)),q);shell.rotation_mode='XYZ';shell.rotation_euler=(.0,-.15,-.18)
 else:shell.matrix_world=Matrix.Translation(V((0,0,-4)))
 visible(shell,f<30 or f>=271)
 bpy.context.view_layer.update()
 right=O['Shotgun trigger surface grip'];left=O['Shotgun forend surface grip']
 rpos=pose_hand('Miner',1,right.matrix_world,.044)
 if f<30 or f>=271:
  lpos=pose_hand('Miner',-1,O['Gold shell surface grip'].matrix_world,.035)
 else:lpos=pose_hand('Miner',-1,left.matrix_world,.061,math.pi/2)
 solve_arm('Miner',1,rpos);solve_arm('Miner',-1,lpos)
 # Buddy watches the strike, lowers the mug and turns toward camera for his line.
 turn=window(f,116,140,182,201)
 O['Buddy head pivot'].rotation_euler.z=-.20*turn
 O['Buddy head pivot'].rotation_euler.y=.035*window(f,224,232,241,248)
 mug=O['Buddy mug root'];lift=window(f,143,158,165,181)
 mug.location=(-.51,3.17,1.0+.11*lift);mug.rotation_euler=(.03*lift,0,0)
 bpy.context.view_layer.update()
 rpos=pose_hand('Buddy',1,O['Mug handle surface grip'].matrix_world,.026)
 free=V((-.70,3.13,.76))
 lpos=pose_hand('Buddy',-1,point_matrix(free),.025)
 solve_arm('Buddy',1,rpos);solve_arm('Buddy',-1,lpos)
 set_face('Buddy',f,talk=201<=f<=269)
 set_face('Miner',f,talk=False,wink=284<=f<=294)
 O['Miner head pivot'].rotation_euler.z=-.045*window(f,273,283,294,307)
 # Shot geometry and persistent deposits.
 impact=V((.55,4.735,1.60));visible(O['Impact persistent assembly'],f>=50)
 visible(O['Unbroken strike surface'],f<50)
 # Each deposited flake shrinks AND retreats into the actual recessed cavity.
 vanish=ease(f,121,181)
 for o in [x for x in O if x.name.startswith('Persistent embedded gold')]:
  rest=V(o['deposit_rest']);o.location=rest+V((0,.025*vanish+.10*ease(f,170,181),0));o.scale=(max(.001,1-vanish),)*3
 bpy.context.view_layer.update();muzzle=O['Shotgun muzzle anchor'].matrix_world.translation
 for i in range(24):
  a=i*2.39996;offset=V((.14*math.cos(a),0,.10*math.sin(a)));end=impact+offset
  def position_at(ff):
   u=max(0,min(1,(ff-40-i*.08)/9));return muzzle.lerp(end,u)
  pellet=O['Flying gold '+str(i)];active=40+i*.08<=f<50+i*.08
  visible(pellet,active);pellet.location=position_at(f)
  if active:look.align_to_velocity_tangent(pellet,position_at,f,nose_axis='Y',fallback=(end-muzzle))
  streak=O['Gold streak '+str(i)];visible(streak,active)
  here=position_at(f);tail=position_at(f-1.15);set_line(streak,[tail,here])
 for i in range(9):
  o=O['Rock scatter '+str(i)];age=(f-50)/30;a=i*2.4
  visible(o,50<=f<=95)
  o.location=impact+V((math.cos(a)*age*.8,-age*.9,math.sin(a)*age*.8-2.8*age*age))
  if o.location.z<.05:o.location.z=.05
 for i in range(5):
  o=O['Thin impact wisp '+str(i)];age=max(0,(f-50)/30)
  visible(o,50<=f<=100);o.location=impact+V((.055*math.cos(i*2.1)*age,-.08-.06*age,.03+i*.04+.15*age))
  o.scale=(1+.7*age,1,max(.01,1-ease(f,83,101)))
 flash=O['Muzzle flare root'];flash.matrix_world=O['Shotgun muzzle anchor'].matrix_world;visible(flash,40<=f<=44)
 O['Blast light'].location=muzzle;O['Blast light'].data.energy=260*window(f,38,40,43,47)
 O['Rock flash spill'].data.energy=320*window(f,40,43,48,56)
 # Small deterministic candle flicker is local; opening portrait receiver is stable.
 O['Candle practical'].data.energy=(0 if f<=30 or f>=271 else 22)*(1+.07*math.sin(f*.73))
 visible(O['Candle amber flame'],30<f<271)
 O['Candle amber flame'].scale=(1,1,1+.05*math.sin(f*.73))
 # Camera paths have explicit cuts and fixed lens within every continuous shot.
 if f<=30:aim_camera((0,-4.1,1.72),(0,0,1.43),43,4.5)
 elif f<=75:
  u=ease(f,45,70);aim_camera(V((-.85,-.10,1.40)).lerp(V((-.9,.25,1.50)),u),V((.10,.70,1.27)).lerp(V((.55,4.75,1.60)),u),34,5.6)
 elif f<=110:
  u=ease(f,76,110);aim_camera(V((.75,2.55,1.72)).lerp(V((.75,2.75,1.72)),u),(.75,4.8,1.70),48,5.6)
 elif f<=270:
  u=max(0,min(1,(f-115)/153));u=u*u*(3-2*u);aim_camera(V((-.77,.40,1.62)).lerp(V((-.64,1.08,1.58)),u),V((-.25,3.48,1.10)).lerp(V((-.48,3.45,1.25)),u),42,4)
 else:
  u=ease(f,271,281);aim_camera(V((.1,-2.45,.96)).lerp(V((.1,-2.32,1.0)),u),(0,0,1.26),43,4.5)
 # Camera-facing shallow head artwork retains a stable rough-round face.
 for name in ['Miner','Buddy']:
  head=O[name+' head pivot'];pos=head.matrix_world.translation.copy()
  roll=-.045*window(f,273,283,294,307) if name=='Miner' else .025*window(f,224,232,241,248)
  head.matrix_world=Matrix.Translation(pos) @ (S.camera.rotation_quaternion @ Quaternion((1,0,0),-math.pi/2) @ Quaternion((0,1,0),roll)).to_matrix().to_4x4()
 bpy.context.view_layer.update()
 # Distance-compensated inverted hulls; sidewall shading is never outline inflation.
 cam=S.camera;forward=cam.rotation_quaternion @ V((0,0,-1))
 for h,source,base_co,base_normal in HULLS:
  depth=(source.matrix_world.translation-cam.location).dot(forward)
  width=max(.0005,look.ink_width(max(.1,depth),cam.data.lens,3.0))
  h.data.vertices.foreach_set('co',base_co+base_normal*width)
  h.data.update()
 WORLD_INK.update()
 # Explicitly reset the cast on every seek, then suppress the complete rear
 # character assembly during the closing shot, including facial child objects.
 if f<=30 or f>=271:
  visible(O['Buddy root'],False);visible(O['Buddy mug root'],False)
 else:
  # The next evaluation restores the body before expression masks are applied.
  pass
 look.enforce_shadow_policy(S)
 _last_frame=f
def handler(scene):
 try:update(scene.frame_current)
 except BaseException:
  traceback.print_exc();sys.stdout.flush()
  if os.environ.get('GOLD_MINE_WORKER')=='1':os._exit(7)
  raise
handler._gold_mine=True
for h in list(bpy.app.handlers.frame_change_post):
 if getattr(h,'_gold_mine',False):bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(handler)
look.install_shadow_policy(S)
update(S.frame_current)
