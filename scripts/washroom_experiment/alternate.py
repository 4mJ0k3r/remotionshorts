"""Animate only the alternate washroom ending in a copy of the approved scene."""
import bpy
import json
import math
from mathutils import Quaternion, Vector as V
from build import Actor, ART, OUT, Stage, aim, alpha_mat, draw, ease, flag, key, mix, packed_image, rgb
START=1062
STOP=1737
CUTS=[
 (1062,1281,'4A | Tremor and realization'),
 (1281,1416,'4B | Pressure reversed'),
 (1416,1503,'4C | Fourth-wall stare'),
 (1503,1551,'4D-1 | Work hard'),
 (1551,1626,'4D-2 | Hold it harder'),
 (1626,1737,'4E | Ascension'),
]
STILLS=[(1160,'4A  Tremor'),(1350,'4B  Power awakening'),(1460,'4C  Sigma stare'),(1575,'4D  Power pose'),(1675,'4E  Teleport')]
ANCHOR=V((30.16,2.03,.76))
Z=V((0,0,1))
def child(parent,prefix):
 return next(o for o in parent.children if o.name.startswith(prefix))
def remove_keys(owner,start=START):
 ad=owner.animation_data
 if not ad or not ad.action:return
 for curve in ad.action.fcurves:
  for point in reversed(list(curve.keyframe_points)):
   if point.co.x>=start:curve.keyframe_points.remove(point,fast=True)
  curve.update()
def existing_actor(g):
 h=Actor.__new__(Actor)
 h.g=g;h.size=.89;h.who='hero'
 h.root=next(o for o in g.scene.objects if o.name.startswith('char_protagonist'))
 h.head=child(h.root,'Head_Rig');h.face=child(h.head,'Face parallax')
 h.body=child(h.root,'Torso_Plane');h.shorts=child(h.root,'hero waistband')
 h.heads={k:child(h.head,'hero solid head '+k) for k in ('fffdf9','d8ecff','ffd2cc','back','profile')}
 h.faces={(s,a):child(h.face,f'hero {s} face {a}') for s in ('panic','shock','smug','talk','scream','dizzy','confused','crossed','open','profile') for a in range(5)}
 for s in ('focus','power','proud','speak'):
  for a in range(5 if s=='speak' else 1):
   h.faces[s,a]=draw(g,f'hero {s} face {a}',f'alt_face_{s}_{a}.png',h.size*1.38,h.size*1.38,h.face)
 h.legs=[];h.arms=[];h.drops=[o for o in h.root.children if o.name.startswith('Temple sweat')]
 for side in ('Left','Right'):
  for family,seq in [(h.legs,('Thigh','Shin','Foot')),(h.arms,('UpperArm','Forearm','Mitten'))]:
   parent=h.root;chain=[]
   for name in seq:
    bone=child(parent,side+'_'+name)
    chain.append((bone,child(bone,side+' '+name+' outline'),None))
    parent=bone
   family.append(chain)
 h.bare_foot=[];h.expression=None
 return h
def badge_layers(s):
 nt=s.node_tree;n=nt.nodes;l=nt.links
 remove_keys(nt)
 render=next(x for x in n if x.type=='R_LAYERS');render.scene=s
 output=next(x for x in n if x.type=='COMPOSITE')
 last=output.inputs[0].links[0].from_socket
 for old in [x for x in n if x.type=='ALPHAOVER']:
  old.inputs[0].default_value=0;old.inputs[0].keyframe_insert('default_value',frame=START)
 limits=[1062,1281,1416,1503,1626,STOP]
 for i,(a,b) in enumerate(zip(limits,limits[1:])):
  im=n.new('CompositorNodeImage');im.image=packed_image(ART/f'alt_hud_{i}.png')
  sc=n.new('CompositorNodeScale');sc.space='RENDER_SIZE';l.new(im.outputs[0],sc.inputs[0])
  ov=n.new('CompositorNodeAlphaOver');l.new(last,ov.inputs[1]);l.new(sc.outputs[0],ov.inputs[2]);last=ov.outputs[0]
  for f,on in [(1,0),(a,1),(b,0)]:
   ov.inputs[0].default_value=on;ov.inputs[0].keyframe_insert('default_value',frame=f)
 l.new(last,output.inputs[0])
 for fc in nt.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='CONSTANT'
def ribbon(g,index):
 d=bpy.data.meshes.new('Tapered aura ribbon')
 vertices=[];faces=[]
 for j in range(24):
  t=j/23
  x=.073*math.sin(t*8.3+index*.74)
  w=(.042+.039*math.sin(math.pi*t))*(1-t)**.70+.002
  vertices.extend([(x-w,0,1.37*t),(x+w,0,1.37*t)])
  if j:faces.append((2*j-2,2*j-1,2*j+1,2*j))
 d.from_pydata(vertices,[],faces)
 uv=d.uv_layers.new()
 for polygon in d.polygons:
  for loop in polygon.loop_indices:
   i=d.loops[loop].vertex_index
   uv.data[loop].uv=(i%2,(i//2)/23)
 m=alpha_mat('Tapered flame emission',h='8efbff' if index%3==0 else 'ffca55',a=.62)
 n=m.node_tree.nodes;l=m.node_tree.links
 tex=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['UV'],sep.inputs[0])
 ramp=n.new('ShaderNodeValToRGB')
 ramp.color_ramp.elements[0].color=(.12,.12,.12,1)
 ramp.color_ramp.elements.new(.26).color=(.76,.76,.76,1)
 ramp.color_ramp.elements[1].color=(0,0,0,1)
 l.new(sep.outputs['Y'],ramp.inputs[0]);l.new(ramp.outputs[0],next(x for x in n if x.type=='MIX_SHADER').inputs[0])
 next(x for x in n if x.type=='EMISSION').inputs[1].default_value=2.5
 d.materials.append(m);return g.link('Golden cyan aura ribbon',d)
def timed(items,a,b):
 for o in items:
  for f,on in [(1,False),(a,True),(b,False)]:flag(o,on,f)
def halo(g,name,r,m):
 return g.curve(name,[(r*math.cos(i*math.tau/80),r*math.sin(i*math.tau/80),0) for i in range(80)],.019,m,loop=True)
def camera_pose(i,t):
 x,y,_=ANCHOR
 if i==0:
  p=V((x+.35,y-1.65+.31*t,.38+.90*t))
  q=V((x,y,.30+1.26*(1-(1-t)**2.7)))
  return p,q,28,0
 if i==1:
  a=math.radians(14+22*t);d=1.6+.5*t
  return V((x+math.sin(a)*d,y-math.cos(a)*d,.62)),V((x,y,1.00)),28,0
 if i==2:
  return V((x+.16-.14*t,y-1.95+.80*t,1.38)),V((x,y,1.63)),26+1.3*t,0
 if i==3:
  return V((x+.21-.08*t,y-1.47+.13*t,1.44)),V((x,y,1.48)),27,-math.radians(8)
 if i==4:
  return V((x+.38,y-1.81,.70)),V((x,y,1.16)),29,math.radians(8)
 return V((x+1.69-.28*t,y-1.68+.17*t,1.15)),V((x,y,1.03)),29,0
def make():
 project=OUT/'washroom_experiment.blend'
 with bpy.data.libraries.load(str(project)) as (source,target):
  target.scenes=source.scenes
 s,=target.scenes;s.name='Washroom Experiment | Alternate Ending'
 assert s.render.engine=='BLENDER_EEVEE_NEXT'
 s.frame_start=START;s.frame_end=STOP-1;s.render.fps=30
 s.render.resolution_percentage=50;s.eevee.taa_render_samples=16
 g=Stage(s);h=existing_actor(g);cam=s.camera
 s.frame_set(START-1)
 for o in [cam,cam.data,h.root,*h.root.children_recursive]:remove_keys(o)
 for o in list(s.objects):
  if o.name.startswith(('Translucent spiral-eyed ghost','White scream speed','Temple waterfall','Foam particle','Continuous white foam','Spreading floor foam','Floor radial speed line','Cabin sound wave')):
   remove_keys(o);flag(o,False,START)
  if o.name.startswith(('char_beti','char_licker')):
   remove_keys(o);o.scale=(.000001,)*3;o.location=(-125,0,0);key(o,'scale',START);key(o,'location',START)
 for marker in list(s.timeline_markers):
  if marker.frame>=START:s.timeline_markers.remove(marker)
 for a,_,name in CUTS:s.timeline_markers.new(name,frame=a)
 badge_layers(s)
 for strip in list(s.sequence_editor.sequences):
  if strip.type=='SOUND' and strip.frame_final_end>START:strip.frame_final_end=START
 audio=s.sequence_editor.sequences.new_sound('Alternate Hindi narration',str(OUT/'alt_narration.wav'),channel=2,frame_start=START)
 audio.sound.pack()
 gold=g.mat('ffcc57',rough=.26,em=2.0);cyan=g.mat('6cfbff',rough=.24,em=2.5)
 rings=[halo(g,'Imploding energy ring',.48,gold if j%2 else cyan) for j in range(3)]
 timed(rings,1281,1330)
 flames=[ribbon(g,j) for j in range(11)]
 timed(flames,1330,1626)
 orbs=[g.ball('Levitating cyan orb',(0,0,0),(.045,)*3,cyan) for _ in range(6)]
 timed(orbs,1330,1626)
 lamp=g.light('Cyan power spill','POINT',ANCHOR+V((.21,-.21,.42)),(0,0,0),0,'5cefff')
 warm=g.light('Gold aura spill','POINT',ANCHOR+V((-.38,.12,.41)),(0,0,0),0,'ffc763')
 marks=draw(g,'Fourth-wall speed lines','scream_lines.png',1.55,1.55,None)
 timed([marks],1503,1551)
 fingers=g.link('Pointing finger contact')
 ink=alpha_mat('Dark finger ink',h='211820')
 g.rod('Extended index finger',(0,0,0),(0,0,.12),.022,ink,fingers)
 g.ball('Rounded index tip',(0,0,.121),(.022,)*3,ink,fingers)
 timed([fingers,*fingers.children],1503,1551)
 salute=g.link('Two-finger salute')
 for offset in [-.025,.025]:
  g.rod('Saluting finger',(offset,0,0),(offset*1.18,.114,0),.017,ink,salute)
  g.ball('Salute finger cap',(offset*1.18,.114,0),(.017,)*3,ink,salute)
 timed([salute,*salute.children],1635,1671)
 burst=halo(g,'White-gold teleport ring',.59,gold)
 flash=g.ball('Golden-white teleport flash',(0,0,0),(.1,.1,.1),g.mat('fff8d7',em=3.0))
 pop=draw(g,'POP lettering','alt_pop.png',.87,.86,None)
 stars=[]
 for j in range(12):
  star=g.link('Stardust spark')
  for axis in range(2):
   p=g.ball('Spark ray',(0,0,0),(.015,.014,.061),gold,star);p.rotation_euler.y=axis*math.pi/2
  stars.append(star)
 timed([flash],1662,1673);timed([burst,pop],1671,1696)
 for o in stars:timed([o,*o.children],1671,1735)
 envelope=json.loads((ART/'alt_envelope.json').read_text())
 # Existing washroom overheads retain their approved intensity outside the stare.
 overhead=[o for o in s.objects if o.name.startswith('Warm-cool washroom ceiling')]
 values=[o.data.energy for o in overhead]
 for f in range(START,STOP):
  i=next(i for i,(a,b,_) in enumerate(CUTS) if a<=f<b)
  a,b,_=CUTS[i];t=ease((f-a)/(b-a-1))
  p,q,lens,roll=camera_pose(i,t)
  if i==4 and 1566<=f<=1571:
   strength=1-(f-1566)/6
   p+=V((.013*strength*(-1)**f,.031*strength,.017*strength*(-1)**f))
  rot=aim(p,q)@Quaternion((0,0,1),roll)
  cam.location=p;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=rot
  cam.data.lens=lens;cam.data.shift_x=0
  focus=ANCHOR+Z*((.14+.74*t) if i==0 else .80 if i<4 else .57)
  cam.data.dof.focus_distance=(focus-p).dot(rot@V((0,0,-1)))
  for o,path in [(cam,'location'),(cam,'rotation_quaternion'),(cam.data,'lens'),(cam.data,'shift_x'),(cam.data,'dof.focus_distance')]:key(o,path,f)
  hip=ANCHOR.copy();beat=math.sin((f-START)*math.tau/6)
  sty='panic' if i==0 and f<1250 else 'focus' if i==0 or (i==2 and f<1495) else 'power' if i==1 else 'speak' if i in (2,3,4) else 'proud'
  level=max(1,envelope[f-START]) if sty=='speak' else 0
  h.paint(hip,rot,0,'fffdf9',sty,level,f)
  if i in (0,1,4):
   h.body.location-=rot@V((0,.015,.15));key(h.body,'location',f)
  if i==2:
   h.head.rotation_quaternion=rot@Quaternion((1,0,0),.055*t);key(h.head,'rotation_quaternion',f)
  side=rot@V((1,0,0))
  hands=[hip+V((-.20,.13,-.04)),hip+V((.20,-.13,.015))]
  if i==0 and f<1250:
   hands=[pt+V((.023*beat,0,.018*beat)) for pt in hands]
  if i==1:
   v=ease((f-1281)/41)
   hands=[pt.lerp(hip+V((sign*.37,-.04,.21)),v) for sign,pt in zip((-1,1),hands)]
  if i==2:hands=[hip+V((-.32,-.07,.18)),hip+V((.32,-.07,.18))]
  if i==3:
   hands=[hip+V((-.31,.01,.19)),h.head.location+rot@V((.24,-.37,.57))]
  if i==4:
   hands=[h.head.location+rot@V((sign*.52,-.23,.045)) for sign in (-1,1)]
  if i==5:
   v=ease((f-1626)/15)
   hands[1]=hands[1].lerp(h.head.location+rot@V((.47,.03,.055)),v)
  feet=[(hip.x+sign*(.10 if i==4 else .18),hip.y-.06,.05) for sign in (-1,1)]
  h.support(feet,hands,V((0,-1,0)),f,low_elbows=i<3,knee_rattle=.045*beat if i==0 and f<1250 else .07 if i==4 else 0)
  h.sweat(f,1 if i==0 and f<1250 else 0)
  h.root.scale=(1,1,1);h.root.location=(0,0,0)
  if f>=1662:
   v=ease((f-1662)/9)
   sc=V((1-.95*v,1-.95*v,1+.80*v)) if f<1672 else V((0,0,0))
   h.root.scale=sc
   h.root.location=hip-V(tuple(hip[j]*sc[j] for j in range(3)))
  for prop in ('location','scale'):key(h.root,prop,f)
  power=ease((f-1329)/13)*(1-ease((f-1624)/19))
  lamp.data.energy=76*power;warm.data.energy=123*power
  if 1662<=f<=1672:warm.data.energy+=138*math.sin(math.pi*(f-1662)/10)
  key(lamp.data,'energy',f);key(warm.data,'energy',f)
  for fixture,value in zip(overhead,values):
   fixture.data.energy=value*(1-.24*(math.sin(math.pi*t)**.5 if i==2 else 0));key(fixture.data,'energy',f)
  if i==1 and f<1330:
   for j,o in enumerate(rings):
    u=ease((f-1281-j*3)/(48-j*3))
    o.location=hip+Z*(.16+j*.19);o.rotation_euler=(.12*j,0,.28*t)
    o.scale=(2.2-2.1*u,)*3
    for prop in ('location','rotation_euler','scale'):key(o,prop,f)
  if 1330<=f<1626:
   for j,o in enumerate(flames):
    k=j*math.tau/len(flames);osc=math.sin((f-1330)*.18+j*.73)
    o.location=hip+V((.49*math.cos(k),.25*math.sin(k)+.17,-.52+.06*osc))
    o.rotation_euler.z=(f-1330)*.012+k
    s0=.66+.26*(.5+.5*osc);o.scale=(s0,s0,s0*(1+.15*math.cos(k)))
    for prop in ('location','rotation_euler','scale'):key(o,prop,f)
   for j,o in enumerate(orbs):
    u=((f-1330+j*11)%79)/79;k=j*math.tau/6+u*.60
    o.location=hip+V((.51*math.cos(k),.29*math.sin(k),-.61+1.50*u))
    o.scale=(.035*(.53+.47*math.sin(math.pi*u)),)*3
    key(o,'location',f);key(o,'scale',f)
  if i==3:
   fingers.location=hands[1];fingers.rotation_mode='QUATERNION'
   fingers.rotation_quaternion=rot;key(fingers,'location',f);key(fingers,'rotation_quaternion',f)
   marks.location=h.head.location-rot@V((0,0,.21));marks.rotation_mode='QUATERNION';marks.rotation_quaternion=rot
   marks.scale=(1+.045*beat,)*3
   for prop in ('location','rotation_quaternion','scale'):key(marks,prop,f)
  if i==5:
   salute.location=hands[1];salute.rotation_mode='QUATERNION';salute.rotation_quaternion=rot
   key(salute,'location',f);key(salute,'rotation_quaternion',f)
  if 1662<=f<=1696:
   if f<=1673:
    k=max(.001,math.sin(math.pi*(f-1662)/11))*.65
    flash.location=hip+Z*.38;flash.scale=(k*.58,k*.38,k);key(flash,'location',f);key(flash,'scale',f)
   if f>=1671:
    u=(f-1671)/25
    burst.location=hip+Z*.35;burst.rotation_mode='QUATERNION';burst.rotation_quaternion=rot
    burst.scale=(.26+1.65*ease(u),)*3
    pop.location=hip+rot@V((.33,.45,.12));pop.rotation_mode='QUATERNION';pop.rotation_quaternion=rot
    pop.scale=(.62+.30*math.sin(math.pi*u),)*3
    for o in (burst,pop):
     for prop in ('location','rotation_quaternion','scale'):key(o,prop,f)
  if 1671<=f<1735:
   for j,o in enumerate(stars):
    u=(f-1671)/64;k=j*math.tau/12
    distance=.11+(.97+.22*(j%3))*ease(u)
    o.location=hip+V((math.cos(k)*distance,math.sin(k)*distance*.59,.34+.52*math.sin(math.pi*u)-.78*u+.08*(j%3)))
    o.scale=(max(.001,(1-u)*(.62+.35*math.sin(f*.41+j)**2)),)*3
    o.rotation_euler.y=.12*(f-1671)+j
    for prop in ('location','scale','rotation_euler'):key(o,prop,f)
 last={b-1 for _,b,_ in CUTS}
 for o in list(s.objects)+[cam.data,lamp.data,warm.data,*[x.data for x in overhead]]:
  if not o.animation_data or not o.animation_data.action:continue
  for fc in o.animation_data.action.fcurves:
   for kp in fc.keyframe_points:
    f=round(kp.co.x)
    if f<START:continue
    swap=' face ' in o.name or ' solid head ' in o.name or fc.data_path.startswith('hide_')
    kp.interpolation='CONSTANT' if swap or f in last else 'LINEAR'
 s.frame_set(1160)
 s['Scope']='Alternate ending only | frames 1062–1736 inclusive | 675 frames'
 bpy.data.libraries.write(str(OUT/'washroom_experiment_alt.blend'),{s},fake_user=True,compress=True)
 bpy.app.driver_namespace['washroom_alt']=s
 return s
