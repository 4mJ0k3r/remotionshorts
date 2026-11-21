import bpy,math,sys
from mathutils import Vector as V,Quaternion
from pathlib import Path
s=bpy.context.scene;O=bpy.data.objects;cam=s.camera
sys.path.insert(0,'D:/remotionshorts/scripts/studio');from set_ink import SetInk
ink_pass=SetInk(s)
# finite events; no body drift. All world art XY basis follows lens, independent head constraints.
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def aim(pos,target,lens=42):
 cam.location=pos;cam.rotation_euler=(V(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;cam.data.dof.focus_distance=(V(target)-cam.location).length

def update(s):
 f=s.frame_current
 if f<=33:aim((1.0,-4.8,2.25),(-.6,0,1.72),45)
 elif f<=96:
  t=(f-34)/62;y=.8+18.3*t;aim((1.2,y-.65,1.02),(.29,y,.80),45)
 elif f<=215:
  t=smooth((f-97)/118);aim((1.2+math.sin(math.pi*t),18.45-25.45*t,1.02+1.03*t),(.1*(1-t)-1.3*t,19.1-11.1*t,.64+.61*t),28+14*t)
 else:
  t=smooth((f-216)/84);aim((.7,14.2+.5*t,2.2),(0,19,1.65),49+3*t)
 bpy.context.view_layer.update();q=cam.matrix_world.to_quaternion()
 for who,y in [('challenger',0),('eddie',19)]:
  x=-1.1 if who=='challenger' else 0
  body=O[who+'_body'];body.location=(x,y,1.09);body.rotation_mode='QUATERNION';body.rotation_quaternion=q
  hp=O[who+'_head_pivot'];hp.location=V((x,y,1.09))+q@V((0,.68,.005));hp.rotation_mode='QUATERNION';hp.rotation_quaternion=q
  O[who+'_parallel_camera_target'].location=hp.location+q@V((0,0,5))
  O[who+'_head'].rotation_euler.z=math.radians(-3)*math.sin(math.pi*smooth((f-255)/30)) if who=='eddie' and 255<=f<=285 else 0
 # single bullet ownership, penetrates holstered gun at frame95 then retired
 b=O['Copper_bullet'];b.hide_render=not 34<=f<=96;b.location=(.29,.8+18.3*max(0,min(1,(f-34)/62)),.80);b.rotation_euler=(0,f*.65,0)
 # challenger's gun and front fingers follow body card-space hand anchor.
 body=O['challenger_body'];hand=body.location+q@V(((795/1024-.5)*2.3,(.5-470/1024)*2.3,.012));gun=O['Challenger_revolver'];gun.rotation_mode='QUATERNION';gun.rotation_quaternion=q@Quaternion((1,0,0),-math.pi/2);gun.location=hand-gun.rotation_quaternion@V((-.20,0,.10))
 O['Challenger grip surface'].location=hand
 for i in range(3):O['Grip finger '+str(i)].location=hand+q@V((.005,.035-i*.027,.023))
 eg=O['Eddie_pearl_revolver'];eg.rotation_mode='QUATERNION';eg.rotation_quaternion=q@Quaternion((0,0,1),-math.pi/2)@Quaternion((1,0,0),-math.pi/2);eg.scale=(.65,.65,.65);eg.location=V((0,19,1.09))+q@V((.30,-.43,.012))-eg.rotation_quaternion@V((0,0,.20*.65))
 # Shoes and receiver-local contact patches derive from the exact artwork sole points.
 for who,y in [('challenger',0),('eddie',19)]:
  body=O[who+'_body'];zfoot=(.5-979/1024)*2.3
  # Keep body upright for pitched cameras: art soles map onto actual ground.
  body.location.z=-((q@V((0,zfoot,0))).z)+.012
  soles=[o for o in O if o.name.startswith(who+' sole contact')]
  for o,xpix in zip(soles,[402,598]):
   p=body.location+q@V(((xpix/1024-.5)*2.3,zfoot,0));o.location=(p.x,p.y,.005)
 O['Temple socket sweat'].hide_render=not 110<=f<=215
 tw=O['Rolling_tumbleweed'];tw.hide_render=not 120<=f<=210;t=max(0,min(1,(f-120)/90));tw.location=(-4+8*t,8,.4);tw.rotation_euler.y=-t*18
 # Camera-relative clearance: put the complete projectile LEFT of Eddie's full holster/gun union.
 if 80<=f<=96:
  arrival=smooth((f-80)/10)
  cam.data.lens=45-17*arrival
  bpy.context.view_layer.update();right=q@V((1,0,0));front=q@V((0,0,1))
  points=[eg.matrix_world@V(c) for c in eg.bound_box]
  pearl=O['Eddie pearl handle'];points.extend(pearl.matrix_world@V(c) for c in pearl.bound_box)
  left=min(p.dot(right) for p in points);center=eg.matrix_world@V((0,0,.2))
  radius=max((b.matrix_world.to_3x3()@v.co).dot(right) for v in b.data.vertices)
  left=min(left,O['eddie_body'].location.dot(right)+.204)
  center+=right*(left-.08-radius-center.dot(right));center+=front*.02
  candidate=center+V((0,-.10*(96-f),0));b.location=b.location.lerp(candidate,arrival)
  oldtarget=V((.29,.8+18.3*max(0,min(1,(f-34)/62)),.80))
  aim(cam.location.copy(),oldtarget.lerp((b.location+eg.location)*.5,arrival),45-17*arrival)
  if f>=90:
   bpy.context.view_layer.update();r=cam.matrix_world.to_quaternion()@V((1,0,0));left=min(p.dot(r) for p in points);extent=max((b.matrix_world@v.co).dot(r) for v in b.data.vertices);b.location+=r*(left-.0801-extent)
 # Finite nervous tremor shared by wrist, gun and fingers; no unmotivated body drift.
 trem=.008*math.sin(f*1.9) if f<=30 else 0
 gun.rotation_quaternion=q@Quaternion((0,1,0),-.35)@Quaternion((1,0,0),-math.pi/2)
 gun.scale=(1.18,1.18,1.18);gun.location=hand-gun.rotation_quaternion@V((-.20*1.18,0,.10*1.18))+q@V((0,trem,0))
 for i in range(3):O['Grip finger '+str(i)].location+=q@V((0,trem,0))
 hp=O['challenger_head'];hp.data.materials[0]=bpy.data.materials['challenger_blink_v2' if 16<=f<=18 else 'challenger_head_v2']
 # muzzle assembly, three lit frames then smoke dissipation
 bpy.context.view_layer.update();muzzle=gun.matrix_world@V((.35,0,.23))
 flash=O['Muzzle flash'];flash.hide_render=not 30<=f<=32;flash.location=muzzle;flash.rotation_mode='QUATERNION';flash.rotation_quaternion=q
 smoke=O['Muzzle smoke'];smoke.hide_render=not 31<=f<=40;age=max(0,f-31);smoke.location=muzzle+V((age*.018,0,age*.025));smoke.scale=(.04+age*.012,)*3
 # Preserve independently camera-parallel head art after the arrival lens adjustment.
 nq=cam.matrix_world.to_quaternion()
 for who in ['challenger','eddie']:
  hp=O[who+'_head_pivot'];hp.rotation_quaternion=nq;O[who+'_parallel_camera_target'].location=hp.location+nq@V((0,0,5))
 bpy.context.view_layer.update();ink_pass.update()

for h in list(bpy.app.handlers.frame_change_post):bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(update);update(s)

