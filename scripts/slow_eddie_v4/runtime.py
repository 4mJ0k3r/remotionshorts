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
 cam.data.shift_x=(.09*smooth((f-76)/10) if 76<=f<=96 else (.09*(1-smooth((f-97)/63)) if 97<=f<=159 else 0))
 cam.data.shift_y=-cam.data.shift_x*1.3333333333
 if f<=32:aim((1,-4.8,2.25),(-.6,0,1.72),45)
 elif f<=96:
  t=max(0,min(1,(f-33)/59));y=.8+18.3*t;aim((.5,y-1.0,1.02),(-.6,y,.8),40)
 elif f<210:
  t=smooth((f-97)/63);a=V((.5,18.1,1.02));b=V((.6,-8,2.1));target=V((-.348535478,18.50699997,.742045)).lerp(V((-.55,8,1.3)),t);aim(a.lerp(b,t),target,26+16*t)
 else:
  t=smooth((f-210)/25);aim(V((.6,-8,2.1)).lerp(V((.7,14.7,2.2)),t),V((-.55,8,1.3)).lerp(V((0,19,1.65)),t),42+10*t)
 bpy.context.view_layer.update();q=cam.matrix_world.to_quaternion()
 for who,y in [('challenger',0),('eddie',19)]:
  x=-.9 if who=='challenger' else 0
  body=O[who+'_body'];body.location=(x,y,1.09);body.rotation_mode='QUATERNION';body.rotation_quaternion=q
  hp=O[who+'_head_pivot'];hp.location=V((x,y,1.09))+q@V((0,.68,.005));hp.rotation_mode='QUATERNION';hp.rotation_quaternion=q
  O[who+'_parallel_camera_target'].location=hp.location+q@V((0,0,5))
  O[who+'_head'].rotation_euler.z=math.radians(-3)*math.sin(math.pi*smooth((f-255)/30)) if who=='eddie' and 255<=f<=285 else 0
 # single bullet ownership, penetrates holstered gun at frame95 then retired
 b=O['Copper_bullet'];b.hide_render=not 33<=f<=97;b.location=(-.6,.8+18.3*max(0,min(1,(f-33)/59)),.80);b.rotation_euler=(0,f*.65,0)
 # challenger's gun and front fingers follow body card-space hand anchor.
 body=O['challenger_body'];hand=body.location+q@V(((795/1024-.5)*2.3,(.5-470/1024)*2.3,.012));gun=O['Challenger_revolver'];gun.rotation_mode='QUATERNION';gun.rotation_quaternion=q@Quaternion((1,0,0),-math.pi/2);gun.location=hand-gun.rotation_quaternion@V((-.20,0,.10))
 O['Challenger grip surface'].location=hand
 for i in range(3):O['Grip finger '+str(i)].location=hand+q@V((.005,.035-i*.027,.023))
 eg=O['Eddie_pearl_revolver'];eg.rotation_mode='QUATERNION';eg.rotation_quaternion=q@Quaternion((0,0,1),-math.pi/2+math.radians(14))@Quaternion((1,0,0),-math.pi/2);eg.scale=(.65,.65,.65);eg.location=V((0,19,1.09))+q@V((-.38,-.43,.012))-eg.rotation_quaternion@V((0,0,.20*.65))
 # Shoes and receiver-local contact patches derive from the exact artwork sole points.
 for who,y in [('challenger',0),('eddie',19)]:
  body=O[who+'_body'];zfoot=(.5-979/1024)*2.3
  # Keep body upright for pitched cameras: art soles map onto actual ground.
  body.location.z=-((q@V((0,zfoot,0))).z)+.012
  soles=[o for o in O if o.name.startswith(who+' sole contact')]
  for o,xpix in zip(soles,[402,598]):
   p=body.location+q@V(((xpix/1024-.5)*2.3,zfoot,0));o.location=(p.x,p.y,.005)
 O['Temple socket sweat'].hide_render=not 110<=f<=215
 tw=O['Rolling_tumbleweed'];tw.hide_render=not 130<=f<=185;t=max(0,min(1,(f-130)/55));tw.location=(-.2+1.5*t,9-3*t,.4);tw.rotation_euler.y=-t*18
 # Bullet stays outside the LEFT gun and both legs, in the actual final camera basis.
 if 76<=f<=97:
  arrival=smooth((f-76)/10);bpy.context.view_layer.update();r=q@V((1,0,0));front=q@V((0,0,1))
  pts=[eg.matrix_world@V(c) for c in eg.bound_box];pearl=O['Eddie pearl handle'];pts.extend(pearl.matrix_world@V(c) for c in pearl.bound_box)
  edge=min(min(p.dot(r) for p in pts),O['eddie_body'].location.dot(r)-.31)
  extent=max((b.matrix_world.to_3x3()@v.co).dot(r) for v in b.data.vertices)
  target=eg.location+q@V((0,.15,.02));target+=r*(edge-.1201-extent-target.dot(r))
  target+=V((0,-.1*max(0,92-f),0));b.location=b.location.lerp(target,arrival)
  # Final separating-plane correction cannot move the projectile into a leg.
  if f>=88:
   bpy.context.view_layer.update();actual=max((b.matrix_world@v.co).dot(r) for v in b.data.vertices);b.location+=r*(edge-.1201-actual)
  blend=smooth((f-76)/10);oldtarget=V((-.6,.8+18.3*max(0,min(1,(f-33)/59)),.8));aim(cam.location.copy(),oldtarget.lerp((b.location+eg.location)*.5,blend),40-14*blend)
 # Finite nervous tremor shared by wrist, gun and fingers; no unmotivated body drift.
 trem=.008*math.sin(f*1.9) if f<=30 else 0
 gun.rotation_quaternion=q@Quaternion((0,1,0),-.40)@Quaternion((1,0,0),-math.pi/2)
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
 # Re-solve Eddie's connected assembly after the tracking camera has been reframed.
 eb=O['eddie_body'];eb.rotation_quaternion=nq;foot=(.5-979/1024)*2.3;eb.location.z=-(nq@V((0,foot,0))).z+.012
 eh=O['eddie_head_pivot'];eh.location=eb.location+nq@V((0,.68,.005));O['eddie_parallel_camera_target'].location=eh.location+nq@V((0,0,5))
 eg.rotation_quaternion=nq@Quaternion((0,0,1),-math.pi/2+math.radians(14))@Quaternion((1,0,0),-math.pi/2);eg.location=eb.location+nq@V((-.38,-.43,.012))-eg.rotation_quaternion@V((0,0,.13))
 if 88<=f<=96:
  bpy.context.view_layer.update();r=nq@V((1,0,0));points=[eg.matrix_world@V(c) for c in eg.bound_box];pearl=O['Eddie pearl handle'];points.extend(pearl.matrix_world@V(c) for c in pearl.bound_box);edge=min(min(v.dot(r) for v in points),eb.location.dot(r)-.31);maxb=max((b.matrix_world@v.co).dot(r) for v in b.data.vertices);b.location+=r*(edge-.1201-maxb)
 # Connected, subtle breathing strain leaves soles anchored; one finite nod and blink.
 bob=.006*math.sin((f-236)/64*math.tau) if f>=236 else 0
 body=O['eddie_body'];base=body.get('rest_card_top',1.15)
 for v in body.data.vertices:v.co.y=(-1.15 if v.index<2 else 1.15+bob)
 hp=O['eddie_head_pivot'];hp.location+=q@V((0,bob,0));O['eddie_parallel_camera_target'].location=hp.location+nq@V((0,0,5))
 O['eddie_head'].data.materials[0]=bpy.data.materials['Eddie V3 blink' if 250<=f<=256 else 'Eddie V3 head']
 nod=math.sin(math.pi*max(0,min(1,(f-272)/20))) if 272<=f<=292 else 0
 O['eddie_head'].rotation_euler.z=-.055*nod;O['eddie_head'].location.y=-.018*nod
 straw=O['Eddie mouth-anchored straw'];straw.rotation_euler.z=.025*math.sin((f-236)*.17) if f>=236 else 0
 headart=O['eddie_head'];straw.location=headart.location+headart.rotation_euler.to_quaternion()@V((0,-.25,.006));straw.rotation_euler.z+=headart.rotation_euler.z
 alpha=1-smooth((f-210)/11)
 for m in bpy.data.materials:
  if m.use_nodes and 'V3 shoulder fade' in m.node_tree.nodes:
   m.node_tree.nodes['V3 shoulder fade'].inputs[0].default_value=alpha;m.surface_render_method='BLENDED' if 210<=f<=221 else 'DITHERED'
 for o in O:
  if o.name.startswith('challenger') or o.name.startswith('Grip finger') or o.name in ['Challenger_revolver','Temple socket sweat','Muzzle flash','Muzzle smoke']:
   if f>=222:o.hide_render=True
   elif o.name.startswith('challenger') or o.name.startswith('Grip finger') or o.name=='Challenger_revolver':o.hide_render=False
 ghost=O['Foreground shoulder silhouette'];ghost.hide_render=not 210<=f<=235
 age=max(0,min(1,(f-210)/25));bpy.data.materials['V3 translucent silhouette'].node_tree.nodes['Shoulder alpha'].inputs[0].default_value=.22*math.sin(math.pi*age)
 for m in bpy.data.materials:
  if m.use_nodes and 'V3 prop fade' in m.node_tree.nodes:
   m.node_tree.nodes['V3 prop fade'].inputs[0].default_value=alpha;m.surface_render_method='BLENDED' if 210<=f<=221 else 'DITHERED'
 # Explicit child visibility: empty-parent hide_render does not hide descendants.
 for child in b.children_recursive:child.hide_render=b.hide_render
 for child in tw.children_recursive:child.hide_render=tw.hide_render
 holster=O['Eddie left black holster'];holster.rotation_mode='QUATERNION';holster.rotation_quaternion=nq@Quaternion((0,0,1),math.radians(14));holster.location=O['eddie_body'].location+nq@V((-.38,-.56,.05))
 # Clearly visible attached temple sweat and finite nervous tremor during standoff.
 drop=O['Temple socket sweat'];drop.hide_render=not 135<=f<=215
 if 135<=f<=215:
  u=(f-135)/80;drop.location=(.48,.13-.15*u,.022);pulse=1+.08*math.sin((f-135)*.35);drop.scale=(.048*pulse,.018,.075*pulse)
 tremble=.007*math.sin((f-135)*1.4) if 135<=f<=215 else 0
 cb=O['challenger_body']
 for v in cb.data.vertices:v.co.y=(-1.15 if v.index<2 else 1.15+tremble)
 for o in [gun]+[O['Grip finger '+str(i)] for i in range(3)]:o.location+=nq@V((0,tremble,0))
 # Camera-tracked hero focus; modest aperture protects the entire cel plane.
 cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=6.3
 subject=O['challenger_head_pivot'].location if f<=32 else (b.location if f<=96 else O['eddie_head_pivot'].location)
 cam.data.dof.focus_distance=max(.1,(subject-cam.location).dot(nq@V((0,0,-1))))
 # Thin ribbon width is camera-facing, with a smooth tail alpha fade.
 for j in range(3):
  ribbon=O['V4 wind ribbon '+str(j)];ribbon.hide_render=not 34<=f<=93
  for i in range(21):
   t=i/20;width=.0014*math.sin(math.pi*t);center=b.location+V(((j-1)*.033,-.09-.34*t,(j-1)*.008))
   ribbon.data.vertices[2*i].co=center-(nq@V((1,0,0)))*width;ribbon.data.vertices[2*i+1].co=center+(nq@V((1,0,0)))*width
 bpy.context.view_layer.update();saved_gun_visibility=gun.hide_render
 if 210<=f<=221:gun.hide_render=True
 ink_pass.update();gun.hide_render=saved_gun_visibility

for h in list(bpy.app.handlers.frame_change_post):bpy.app.handlers.frame_change_post.remove(h)
bpy.app.handlers.frame_change_post.append(update);update(s)

