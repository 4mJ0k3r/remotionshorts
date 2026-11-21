"""Surgical V2 pose/contact overrides. V1 remains the unchanged timing/set source."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import bpy
from mathutils import Vector as V,Quaternion,Matrix
import build_bamboo_ambush as b
OUT=b.OUT;b.ART=OUT/'assets_v2';b.BLEND_PATH=OUT/'bamboo_ambush_v2.blend'
CUTS=b.CUTS;actors={};OriginalActor=b.Actor;original_camera=b.shot_camera
PIPE_Y=.58+(.5-1085/1536)*(1.16*.82)
def cut_at(f):return next(c for c,a,z,p in CUTS if a<=f<=z)
def pulse(f):return (0,.5,1,.5,0)[(f-769)%5]
def mark(o,path,f):b.key(o,path,f)
def put(o,path,value,f):setattr(o,path,value);mark(o,path,f)
def head_mouth(actor):
 return actor.head.location+actor.head.rotation_quaternion@V((actor.face_group.location.x,(.5-1085/1536)*1.16*actor.size,.008*actor.size))
class ActorV2(OriginalActor):
 def __init__(self,g,who,size=.85):
  super().__init__(g,who,size);actors[who]=self;self.rest_scales=[(o,o.scale.copy()) for o in [self.head,self.body_pivot,self.pelvis_ink,self.pelvis_fill]+self.hands]
 def pose(self,hip,spine_dir,cam_rot,face_state,turn_x,feet_pos,hands_pos,leg_pole,arm_pole,f,sweat_mode=0,drop_shadow=True):
  cut=cut_at(f);prone=self.who=='enemy' and cut in ['5A','5C'];supine=self.who=='soldier' and cut in ['1A','1B','2A','2B'] and (cut!='1A' or f>=22);below=self.who=='soldier' and cut in ['5B','5C']
  if self.who=='soldier' and f==22:
   obs=[self.head,self.body_pivot,self.pelvis_ink,self.pelvis_fill]+self.hands+self.feet;curves=self.arms_ink+self.arms_fill+self.legs_ink+self.legs_fill;self.entry_locations=[(o,o.location.copy()) for o in obs];self.entry_rotations=[(o,o.rotation_quaternion.copy()) for o in [self.head,self.body_pivot,self.pelvis_ink,self.pelvis_fill]];self.entry_curves=[(o,[v.co.copy() for v in o.data.splines[0].bezier_points]) for o in curves]
  for o,scale in self.rest_scales:put(o,'scale',scale,f)
  if supine:
   p=b.ease((f-22)/22) if cut=='1A' else 1.;hip=V((0,-.18,-.38));spine_dir=(0,1,0);feet_pos=[(-.12,-.62,-.38),(.12,-.62,-.38)];hands_pos=[(-.25,.10,-.34),(.25,.10,-.34)]
   if cut=='2A':hands_pos=[(-.070,PIPE_Y,-.29),(.070,PIPE_Y,-.275)]
   super().pose(hip,spine_dir,Quaternion(),face_state,0,feet_pos,hands_pos,(1,0,0),(0,1,0),f,drop_shadow=False)
   put(self.body_pivot,'location',V((0,.05,-.38)),f);put(self.head,'location',V((0,.58,-.32)),f)
   for j,sign in enumerate([-1,1]):
    foot=V((sign*.12,-.62,-.38));leg=[V((sign*.10,-.18,-.38)),V((sign*.14,-.43,-.38)),foot];b.set_bezier_3(self.legs_ink[j],leg,f);b.set_bezier_3(self.legs_fill[j],[v+V((0,0,.005)) for v in leg],f)
    grip=V(hands_pos[j]) if cut=='2A' else V((sign*.23,-.05,-.34));elbow=V((sign*.28,.23,-.32)) if cut=='2A' else V((sign*.26,.08,-.36));pts=[V((sign*.16,.15,-.36)),elbow,grip];b.set_bezier_3(self.arms_ink[j],pts,f);b.set_bezier_3(self.arms_fill[j],[v+V((0,0,.005)) for v in pts],f);put(self.hands[j],'location',grip,f)
   if cut=='1A' and p<1:
    for o,start in self.entry_locations:put(o,'location',start.lerp(o.location,p),f)
    for o,start in self.entry_rotations:put(o,'rotation_quaternion',start.slerp(o.rotation_quaternion,p),f)
    for o,start in self.entry_curves:b.set_bezier_3(o,[v.lerp(k.co,p) for v,k in zip(start,o.data.splines[0].bezier_points)],f)
   self.head_card['orientation']='helmet north +Y, chin south -Y toward chest';return
  if below:
   k=pulse(f);hip=V((.76,PIPE_Y,-.52));axis=V((-1,0,.10)).normalized();feet_pos=[(1.12,PIPE_Y-.10,-.60),(1.12,PIPE_Y+.10,-.60)];hands_pos=[(.65,PIPE_Y-.21,-.55),(.17,PIPE_Y-.04,-.21)];face_state='gag_out' if k>.4 else 'gag_in'
   super().pose(hip,axis,cam_rot,face_state,0,feet_pos,hands_pos,(0,-1,0),(0,-1,0),f,sweat_mode=1,drop_shadow=False)
   put(self.head,'location',V((.15,PIPE_Y,-.42)),f);put(self.head,'scale',(.62,)*3,f);put(self.body_pivot,'location',V((.55,PIPE_Y,-.51)),f);put(self.body_pivot,'scale',(.67,)*3,f)
   # Keep the whole horizontal uniform/shoulders in the trench, supported just above its floor.
   for o in [self.pelvis_ink,self.pelvis_fill]:put(o,'scale',(.14,.07,.06),f)
   return
  if prone:
   k=pulse(f);hip=V((.15-.025*k,PIPE_Y,.22-.14*k));feet_pos=[(.96,PIPE_Y-.12,.055),(.91,PIPE_Y+.14,.055)];hands_pos=[(-.72,PIPE_Y-.28,.026),(-.95,PIPE_Y+.22,.026)]
   super().pose(hip,(-1,0,.18),cam_rot,'creepy_grin_2',-.16,feet_pos,hands_pos,(0,0,-1),(0,-.7,-.2),f)
   put(self.body_pivot,'location',V((-.15-.025*k,PIPE_Y,.28-.055*k)),f);put(self.body_pivot,'scale',(.76,1,1),f);put(self.head,'location',V((-.45-.015*k,PIPE_Y-.025,.42+.015*k)),f);put(self.head,'rotation_quaternion',cam_rot@Quaternion((0,0,1),math.radians(-9)),f)
   for o in [self.pelvis_ink,self.pelvis_fill]:put(o,'scale',(.19,.085,.055 if o==self.pelvis_ink else .050),f)
   # Actual palm contact: flatten black cel mitts to rest on the ground plane.
   for o in self.hands:put(o,'scale',(.052,.045,.026),f)
   # Upper arms pass behind the cream head, then reach the two fixed palm supports.
   palm=[V((0,PIPE_Y-.38,.026)),V((-.80,PIPE_Y+.03,.026))]
   for j,sign in enumerate([-1,1]):
    shoulder=V((-.25,PIPE_Y+.06+j*.09,.30-.045*k));elbow=V((-.06 if j==0 else -.65,PIPE_Y-.28 if j==0 else PIPE_Y+.18,.16));pts=[shoulder,elbow,palm[j]]
    b.set_bezier_3(self.arms_ink[j],pts,f);b.set_bezier_3(self.arms_fill[j],[v+V((0,-.006,0)) for v in pts],f);put(self.hands[j],'location',palm[j],f)
    ankle=V((.91 if j==0 else .85,PIPE_Y+sign*.12,.042));leg=[V((.28-.025*k,PIPE_Y+sign*.07,.20-.12*k)),V((.59,PIPE_Y+sign*.10,.095)),ankle];b.set_bezier_3(self.legs_ink[j],leg,f);b.set_bezier_3(self.legs_fill[j],[v+V((0,-.006,0)) for v in leg],f);put(self.feet[j],'location',ankle,f);put(self.shadows[j],'location',(ankle.x,ankle.y,.004),f)
   return
  # Restore scale after an underground or prone pose and protect the full chin in upright shots.
  for o in [self.head,self.body_pivot]:put(o,'scale',(1,1,1),f)
  if self.who=='enemy' and cut in ['4A','4B']:
   delta=V((0,PIPE_Y+.4,0));hip=V(hip)+delta;feet_pos=[V(x)+delta for x in feet_pos];hands_pos=[V(x)+delta for x in hands_pos]
  axis=V(spine_dir).normalized();pose_hip=V(hip)-axis*.12 if self.who=='enemy' else hip
  super().pose(pose_hip,spine_dir,cam_rot,face_state,turn_x,feet_pos,hands_pos,leg_pole,arm_pole,f,sweat_mode,drop_shadow)
  if self.who=='enemy':
   q=self.body_pivot.rotation_quaternion;put(self.head,'location',self.head.location+axis*.12,f);put(self.body_pivot,'location',self.body_pivot.location-(q@V((0,0,.025))),f)
b.Actor=ActorV2
def shot_camera(cut,u,f):
 if cut=='2A':
  p=b.lerp((.12,-.80,1.02),(.10,-.67,.92),u);t=V((0,.44,-.28));return p,t,37.,4.8,t
 if cut=='2B':
  p=b.lerp((0,PIPE_Y,2.25),(0,PIPE_Y,2.0),u);t=V((0,PIPE_Y,0));return p,t,34.,4.8,t
 if cut=='5A':
  p=b.lerp((.05,-3.90,1.0),(.05,-3.60,.95),u);t=V((.02,PIPE_Y,.30));return p,t,32.,5.6,V((-.15,PIPE_Y,.30))
 if cut=='5B':
  p=b.lerp((.48,-2.65,-.23),(.46,-2.45,-.24),u);t=V((.50,PIPE_Y,-.43));return p,t,32.,5.6,t
 if cut=='5C':
  p=b.lerp((.10,-4.10,.14),(.10,-3.85,.12),u);t=V((.10,PIPE_Y,-.04));return p,t,32.,6.,t
 p,t,l,stop,focus=original_camera(cut,u,f)
 if cut in ['4A','4B']:
  delta=V((0,PIPE_Y+.4,0));p+=delta;t+=delta;focus+=delta
 return p,t,l,stop,focus
b.shot_camera=shot_camera
b.main()
s=bpy.context.scene;g=b.Stage(s);bamboo=bpy.data.objects['Bamboo_Breathing_Tube'];soldier=actors['soldier'];enemy=actors['enemy'];floor=bpy.data.objects['Pit_Floor'];tent=bpy.data.objects['Military_Beach_Tent'];tree=bpy.data.objects['Bare_Coastal_Tree']
# Tight four-piece cover. Its outside overlaps existing sand; only a 9cm collar hole remains.
sand=bpy.data.materials['Sand_Top'];roof=g.obj('V2_Continuous_Sand_Cover')
for name,xyz,dim in [('North',(0,(1.08-PIPE_Y+.046)/2,-.015),(1.20,1.08-PIPE_Y-.046,.03)),('South',(0,(-1.08-PIPE_Y-.046)/2,-.015),(1.20,1.08+PIPE_Y-.046,.03)),('Left',(-.323,0,-.015),(.554,.092,.03)),('Right',(.323,0,-.015),(.554,.092,.03))]:g.box('V2_Cover_'+name,xyz,dim,sand,roof,bevel=.003)
# A wide cutaway reveals the same horizontal adult body instead of a ceiling-mounted floating head.
underground=g.obj('V2_Underground_Floor_And_Earth');soil=bpy.data.materials['Sand_Floor'];wall=bpy.data.materials['Sand_Wall'];g.box('V2_Lower_Trench_Floor',(.38,PIPE_Y,-.68),(1.85,1.40,.06),soil,underground,bevel=.01);g.box('V2_Lower_Trench_Back',(.38,1.13,-.34),(1.85,.05,.63),wall,underground,bevel=.01)
for x in [-.55,1.30]:g.box('V2_Cutaway_Side', (x,PIPE_Y,-.34),(.04,1.40,.63),wall,underground,bevel=.01)
arm=g.curve('V2_Soldier_Reaching_Forearm',[(0,0,0)]*3,.023,b.mat('9c8468',rough=.7,em=.14));grip=g.curve('V2_Hand_Grips_Waist',[(0,0,0)]*3,.017,b.mat('fdfaf2',rough=.7,em=.14))
palm=g.ball('V2_Waist_Contact_Palm',(0,0,0),(.04,.02,.045),b.mat('fdfaf2',rough=.7,em=.14));fingers=[g.curve('V2_Waist_Grip_Finger_'+str(j),[(0,0,0)]*3,.008,b.mat('fdfaf2',rough=.7,em=.14)) for j in range(3)]
for f in range(1,936):
 cut=cut_at(f);s.frame_set(f);camq=s.camera.rotation_quaternion;last=cut in ['5A','5B','5C'];below=cut in ['5B','5C'];k=pulse(f) if last else 0
 # Disable only the superseded cover meshes, never the base terrain or unrelated props.
 for name in ['Sand_Cover_2B_Body','Sand_Cover_2B_Apron','Sand_Cover_Full']:
  root=bpy.data.objects[name]
  for o in [root]+list(root.children_recursive):b.set_vis(o,False,f)
 roof_on=cut in ['2B','3A','4A','4B','5A','5B','5C']
 for o in [roof]+list(roof.children_recursive):b.set_vis(o,roof_on,f)
 cx=.15 if last else (.15*b.ease((f-697)/71) if cut=='4B' else 0)
 slide=1.5*(1-b.ease((f-286)/39)) if cut=='2B' else 0;put(roof,'location',(cx,PIPE_Y+slide,0),f)
 if cut in ['2A','2B','3A','4A','4B']:
  mouth=V((cx,PIPE_Y,-.32+.008*.82));put(bamboo,'location',mouth,f);put(bamboo,'rotation_euler',(0,0,0),f);put(bamboo,'scale',(1,1,1),f)
 elif last:
  # The lower end owns the mouth contact; compression owns the upper contact, so neither tip floats.
  mouth=V((.15,PIPE_Y,-.42))+camq@V((0,(.5-1085/1536)*1.16*.82*.62,.008*.82*.62));contact=.165-.14*k;length=contact-mouth.z;put(bamboo,'location',mouth,f);put(bamboo,'rotation_euler',(0,0,0),f);put(bamboo,'scale',(1,1,length/.82),f);put(roof,'location',(.15,mouth.y,0),f)
  waist=V((.15-.025*k,PIPE_Y,.22-.14*k));b.set_bezier_3(arm,[V((.17,PIPE_Y-.04,-.21)),V((.32,PIPE_Y-.05,.01)),waist+V((.13,-.05,.015))],f);b.set_bezier_3(grip,[waist+V((.13,-.05,.015)),waist+V((.07,-.09,.05)),waist+V((.015,-.09,.045))],f)
  put(palm,'location',waist+V((.10,-.09,.025)),f)
  for j,o in enumerate(fingers):x=.065+j*.026;b.set_bezier_3(o,[waist+V((x,-.102,.005)),waist+V((x,-.106,.05)),waist+V((x-.014,-.075,.069))],f)
 for o in [arm,grip,palm]+fingers:b.set_vis(o,cut in ['5A','5C'],f)
 for o in [underground]+list(underground.children_recursive):b.set_vis(o,below,f)
 for name in ['Pit_Floor','Pit_Wall_Left','Pit_Wall_Right','Pit_Wall_Back']:
  o=bpy.data.objects[name];b.set_vis(o,not below,f)
 put(floor,'location',(0,0,-.45 if cut in ['1A','1B','2A','2B'] else -.68),f)
 for name in ['Beach_Sand_Left','Beach_Sand_Right','Beach_Sand_Back']:
  o=bpy.data.objects[name];put(o,'scale',(1,.5443 if below and name!='Beach_Sand_Back' else 1,.0333 if below else 1),f);loc=o.location.copy();loc.z=-.015 if below else -.45;loc.y=5.0125 if below and name!='Beach_Sand_Back' else (5.975 if name=='Beach_Sand_Back' else 0);put(o,'location',loc,f)
 for name in ['Pit_Berm_0','Pit_Berm_1','Pit_Berm_2','Pit_Berm_3']:
  b.set_vis(bpy.data.objects[name],not below,f)
 for name in ['Cutaway_Soil_Border_Left','Cutaway_Soil_Border_Right','Cutaway_Soil_Border_Bottom']:b.set_vis(bpy.data.objects[name],False,f)
 put(tent,'location',(.25,3.2,0) if last else (-2.2,4.5,0),f);put(tree,'location',(-1.1,1.7,0) if last else (1.8,3.5,0),f)
# Discrete cut boundaries and visibility never interpolate through walls or scale swaps.
ends={z for c,a,z,p in CUTS}
for o in list(s.objects):
 if o.animation_data and o.animation_data.action:
  for fc in o.animation_data.action.fcurves:
   for kp in fc.keyframe_points:
    kp.interpolation='CONSTANT' if fc.data_path.startswith('hide_') or '_face_' in o.name or o in [soldier.root,enemy.root] or (round(kp.co.x) in ends and kp.co.x<935) else 'LINEAR'
s.frame_set(45);s.render.resolution_percentage=50
if hasattr(s.render,'compositor_device'):s.render.compositor_device='GPU'
bpy.ops.wm.save_as_mainfile(filepath=str(b.BLEND_PATH));print('V2 POSES AND CONTACTS SAVED',b.BLEND_PATH,flush=True)
