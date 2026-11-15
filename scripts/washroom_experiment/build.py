"""Bake the 14-cut performance into a portable Blender scene."""
import bpy,math,json,traceback,time
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from sets import Stage,OUT,ART,rgb,classroom,washroom,office
V=Vector
IMAGES={}
def packed_image(path):
 path=str(path)
 if path not in IMAGES:
  image=bpy.data.images.load(path,check_existing=False)
  image.pack()
  IMAGES[path]=image
 return IMAGES[path]
CUTS=[
 (1,204,100,'1A  Classroom panic'),(205,300,250,'1B  Rise from bench'),(301,390,345,'1C  Corridor run'),
 (391,495,440,'2A  Entrance reveal'),(496,663,580,'2B  Cabin shock'),
 (664,786,725,'3A  Elevated chair'),(787,846,815,'3B  Reaction'),
 (847,906,875,'3C  Low table angle'),(907,954,930,'3D  Tight reaction'),
 (955,1014,985,'3E  Office shoulder angle'),(1015,1062,1040,'3F  Soul pop'),
 (1063,1194,1130,'4A  Crane tilt-up'),(1195,1263,1230,'4B-1  Scream close-up'),
 (1264,1330,1295,'4B-2  Side profile'),(1331,1404,1365,'4C  Foam pullback')]
def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def mix(a,b,t):return V(a).lerp(V(b),t)
def key(o,p,f):o.keyframe_insert(data_path=p,frame=f)
def flag(o,on,f):
 o.hide_render=o.hide_viewport=not on
 key(o,'hide_render',f);key(o,'hide_viewport',f)
def aim(a,b):return (V(b)-V(a)).to_track_quat('-Z','Y')
def knee(a,b,l,r,pole):
 a,b=V(a),V(b);d=b-a;axis=d.normalized();h=min(l+r-.001,max(.002,d.length))
 x=(l*l-r*r+h*h)/(2*h);y=math.sqrt(max(0,l*l-x*x))
 p=V(pole)-axis*axis.dot(V(pole))
 if p.length<1e-6:p=axis.cross(V((0,1,0)))
 return a+axis*x+p.normalized()*y
def alpha_mat(name,path=None,h=None,a=1,head=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.surface_render_method='DITHERED'
 n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission')
 if path:
  tex=n.new('ShaderNodeTexImage');tex.image=packed_image(path)
  em.inputs[1].default_value=1.35 if head else 1.12;l.new(tex.outputs['Color'],em.inputs[0])
  diffuse=n.new('ShaderNodeBsdfPrincipled');diffuse.inputs['Roughness'].default_value=1
  l.new(tex.outputs['Color'],diffuse.inputs['Base Color'])
  mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.96 if head else .95
  l.new(diffuse.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);surface=mix.outputs[0];alpha=tex.outputs['Alpha']
 else:
  em.inputs[0].default_value=(*rgb(h),1);em.inputs[1].default_value=1.2;surface=em.outputs[0];alpha=None
 if a<1 or path:
  trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=a
  if alpha:l.new(alpha,mix.inputs[0])
  l.new(trans.outputs[0],mix.inputs[1]);l.new(surface,mix.inputs[2]);surface=mix.outputs[0]
 l.new(surface,out.inputs[0]);return m
def quad(g,name,w,h,mat,p):
 d=bpy.data.meshes.new(name);d.from_pydata([(-w/2,-h/2,0),(w/2,-h/2,0),(w/2,h/2,0),(-w/2,h/2,0)],[],[(0,1,2,3)])
 for u,v in zip(d.uv_layers.new().data,[(0,0),(1,0),(1,1),(0,1)]):u.uv=v
 d.materials.append(mat);return g.link(name,d,p)
def draw(g,name,art,w,h,p,head=False):
 return quad(g,name,w,h,alpha_mat(name,ART/art,head=head),p)
def compose(s):
 s.use_nodes=True;n=s.node_tree.nodes;n.clear();l=s.node_tree.links
 a=n.new('CompositorNodeRLayers');a.scene=s
 g=n.new('CompositorNodeGlare');g.glare_type='FOG_GLOW';g.mix=.14;g.threshold=.85;g.size=7;g.quality='MEDIUM'
 l.new(a.outputs['Image'],g.inputs[0])
 h=n.new('CompositorNodeHueSat');h.inputs['Saturation'].default_value=1.2;h.inputs['Value'].default_value=1.05;l.new(g.outputs[0],h.inputs['Image'])
 last=h.outputs[0]
 ranges=[(1,390),(391,663),(664,1062),(1063,1330),(1331,1404)]
 badges=[(f'hud_{i}.png',[(1,0),(a,1),(b+1,0)]) for i,(a,b) in enumerate(ranges)]
 warning_keys=[(1,0)]+[(f,.68 if (f-1264)//5%2 else 1) for f in range(1264,1331,5)]+[(1331,0)]
 badges.append(('warnings.png',warning_keys))
 for image,events in badges:
  im=n.new('CompositorNodeImage');im.image=packed_image(ART/image)
  sc=n.new('CompositorNodeScale');sc.space='RENDER_SIZE';l.new(im.outputs[0],sc.inputs[0])
  ov=n.new('CompositorNodeAlphaOver');l.new(last,ov.inputs[1]);l.new(sc.outputs[0],ov.inputs[2]);last=ov.outputs[0]
  for f,val in events:
   ov.inputs[0].default_value=val;ov.inputs[0].keyframe_insert('default_value',frame=f)
 for fc in s.node_tree.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='CONSTANT'
 o=n.new('CompositorNodeComposite');l.new(last,o.inputs[0])
def world(s):
 w=bpy.data.worlds.new('Blue cyclorama gradient');w.use_nodes=True;s.world=w
 n=w.node_tree.nodes;l=w.node_tree.links
 bg=next(x for x in n if x.type=='BACKGROUND');tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Normal'],sep.inputs[0])
 m=n.new('ShaderNodeMapRange');m.inputs['From Min'].default_value=-.52;m.inputs['From Max'].default_value=.12;l.new(sep.outputs['Z'],m.inputs[0])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*rgb('5d84df'),1);ramp.color_ramp.elements[1].color=(*rgb('bfdcff'),1)
 l.new(m.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=.75
class Actor:
 def __init__(self,g,name,who,size):
  self.g=g;self.name=name;self.size=size;self.who=who
  self.root=g.link(name);self.head=g.link('Head_Rig',p=self.root);self.face=g.link('Face parallax',p=self.head)
  self.body=draw(g,'Torso_Plane',who+'_torso.png',size*(.60 if who=='hero' else .76),size*(.77 if who=='hero' else .86),self.root)
  self.heads={c:draw(g,who+' solid head '+c,f'{who}_{c}.png',size*1.38,size*1.38,self.head,head=True) for c in (['fffdf9','d8ecff','ffd2cc'] if who=='hero' else ['fffdf9'])}
  if who in ('hero','licker'):
   self.heads['back']=draw(g,who+' solid head back',f'{who}_back.png',size*1.38,size*1.38,self.head)
  if who=='hero':
   self.heads['profile']=draw(g,'hero solid head profile','hero_profile.png',size*1.38,size*1.38,self.head,head=True)
  self.faces={(st,i):draw(g,f'{who} {st} face {i}',f'face_{st}_{i}.png',size*1.38,size*1.38,self.face) for st in ('panic','shock','smug','talk','scream','dizzy','confused','crossed','open','profile') for i in range(5)}
  dark=alpha_mat('Matte ink limbs',h='211820')
  trousers=g.mat({'hero':'241a24','beti':'16a34a','licker':'808d9f'}[who],em=.31)
  sleeves=g.mat({'hero':'241a24','beti':'295dd3','licker':'8e9bad'}[who],em=.31)
  self.shorts=g.ball(who+' waistband',(0,0,0),(size*.19,.080,size*.106),g.mat({'hero':'1e3a8a','beti':'16843f','licker':'758195'}[who],em=.35),self.root)
  self.legs=[];self.arms=[]
  for side in ('Left','Right'):
   for family,material,chain,names in [('leg',trousers,self.legs,('Thigh','Shin','Foot')),('arm',sleeves,self.arms,('UpperArm','Forearm','Mitten'))]:
    bones=[];par=self.root
    for i,k in enumerate(names):
     bone=g.link(side+'_'+k,p=par);par=bone
     o=g.ball(side+' '+k+' outline',(0,0,0),(1,1,1),dark,bone)
     core=g.ball(side+' '+k+' fill',(0,0,0),(1,1,1),material,bone) if i<2 and who!='hero' else None
     bones.append((bone,o,core))
    chain.append(bones)
  self.drops=[g.ball('Temple sweat', (0,0,0),(.026,.017,.055),g.mat('61cafc',em=.7),self.root) for _ in range(6)] if who=='hero' else []
  self.bare_foot=[]
  if who=='beti':
   bone=self.legs[1][2][0]
   ink=alpha_mat('Bare foot outline',h='2c1d22')
   cream=alpha_mat('Cream foot and big toe',h='fffdf9')
   for name,xyz,dim in [('Bare foot',(.052,0,0),(.096,.049,.047)),('Big toe',(.145,0,.017),(.047,.041,.037))]:
    g.ball(name+' outline',xyz,dim,ink,bone)
    fill=g.ball(name+' cream',xyz,(dim[0]*.90,dim[1]*.93,dim[2]*.91),cream,bone)
    self.bare_foot.append((fill,V(xyz)))
  self.expression=None
 def pick(self,color,sty,i,f):
  values=(color,sty,i)
  if values==self.expression:return
  old=self.expression;self.expression=values
  for k,o in self.heads.items():
   if old is None or k in (old[0],color):
    o.scale=(1,)*3 if k==color else (.00001,)*3;key(o,'scale',f)
  for k,o in self.faces.items():
   if old is None or k in (old[1:],(sty,i)):
    o.scale=(1,)*3 if k==(sty,i) else (.00001,)*3;key(o,'scale',f)
 def paint(self,hip,camrot,face_turn,color,style,amount,f):
  size=self.size;self.hip=V(hip);self.q=camrot
  self.head.location=self.hip+V((0,0,size*.97));self.head.rotation_mode='QUATERNION';self.head.rotation_quaternion=camrot
  self.face.location=(size*.17*face_turn,0,.014)
  depth=.152 if self.who=='hero' else .065
  self.body.location=self.hip+V((0,0,size*.325))-camrot@V((0,0,depth));self.body.rotation_mode='QUATERNION';self.body.rotation_quaternion=camrot
  self.shorts.location=self.hip
  for o,p in [(self.head,'location'),(self.head,'rotation_quaternion'),(self.face,'location'),(self.body,'location'),(self.body,'rotation_quaternion'),(self.shorts,'location')]:key(o,p,f)
  self.pick(color,style,amount,f)
 def chain(self,chain,a,b,c,f,kind,bare_axis=None,tiptoe=False):
  parent=Matrix.Identity(4)
  rad=self.size*(.036 if self.who=='hero' else .061)
  for j,(bone,shape,core) in enumerate(chain):
   start,end=(a,b) if j==0 else (b,c) if j==1 else (c,c+V((0,0,.10)))
   start,end=V(start),V(end);delta=end-start
   if delta.length<.002:delta=V((0,0,.002))
   if j<2:q=delta.to_track_quat('Z','Y')
   elif bare_axis is not None:q=bare_axis.to_track_quat('X','Z')
   else:q=Quaternion((1,0,0),.44) if tiptoe else Quaternion()
   world=Matrix.LocRotScale(start,q,V((1,1,1)));local=parent.inverted()@world;parent=world
   bone.location=local.translation;bone.rotation_mode='QUATERNION';bone.rotation_quaternion=local.to_quaternion()
   key(bone,'location',f);key(bone,'rotation_quaternion',f)
   if j<2:
    shape.location.z=delta.length/2;shape.scale=(rad,rad*.82,delta.length/2+rad*.66)
    if core:
     core.location=shape.location;core.scale=(rad*.79,rad*.85,delta.length/2+rad*.47)
     key(core,'scale',f);key(core,'location',f)
   elif kind=='arm':shape.location=(0,0,0);shape.scale=(rad*1.30,rad*.90,rad*1.22)
   elif bare_axis is not None:
    shape.scale=(.00001,)*3
    offset=q.inverted()@(self.q@V((0,0,.027)))
    for fill,xyz in self.bare_foot:
     fill.location=xyz+offset;key(fill,'location',f)
   else:shape.location=(.018,-.024,.007);shape.scale=(rad*1.83,rad*1.59,rad*.82)
   key(shape,'scale',f);key(shape,'location',f)
 def support(self,feet,hands,forward,f,seated=False,bare_axis=None,low_elbows=False,temple=False,knee_rattle=0,tiptoe=False):
  sz=self.size;side=V((1,0,0))
  for j,s in enumerate((-1,1)):
   hip=self.hip+side*(s*sz*.132)
   foot=V(feet[j]);kp=forward*(1.0 if seated else .78)+side*s*.23
   k=knee(hip,foot,sz*.435,sz*.433,kp)
   k.x-=s*knee_rattle
   self.chain(self.legs[j],hip,k,foot,f,'leg',bare_axis if j==1 else None,tiptoe)
   table=self.who=='licker'
   shoulder=self.hip+V((-.025,s*sz*.207,sz*.585) if table else (s*sz*.207,0,sz*.585))
   hand=V(hands[j])
   pole=V((0,s*.30,-1)) if table else side*s+forward*.25+V((0,0,-1.6 if low_elbows else 0))
   if table:
    arm=(hand-shoulder).length/(2*math.sin(math.radians(55)))
    e=knee(shoulder,hand,arm,arm,pole)
   elif temple:e=self.head.location+self.q@V((s*.51,-.46,.035))
   else:e=knee(shoulder,hand,sz*.305,sz*.318,pole)
   self.chain(self.arms[j],shoulder,e,hand,f,'arm')
 def sweat(self,f,mode):
  for i,o in enumerate(self.drops):
   if not mode:
    o.scale=(.00001,)*3;key(o,'scale',f);continue
   t=((f+i*9)%28)/28 if mode!=2 else .33
   o.location=self.head.location+self.q@V((((-1)**i)*(.29+t*.24),.15-t*.47,.045))
   a=.53+.40*math.sin(t*math.pi);o.scale=(.024*a,.019*a,.058*a)
   key(o,'location',f);key(o,'scale',f)
def shot_view(i,t,hip):
 z=hip.z
 if i==0:return mix((1.60,3.25,1.70),(1.14,2.90,1.56),t),mix((0,.63,1.10),(0,.66,1.18),t),40,0
 if i==1:return mix((1.00,-1.55,.72),(.85,-1.18,.83),t),V((.02,.15,1.11)),31,-.026
 if i==2:return V((.89-.28*t,hip.y+2.82-.34*t,1.34+.17*t)),hip+V((0,0,.34)),39,-.035
 if i==3:return mix((30.12,-2.55,1.69),(30.28,-.36,1.76),t),mix((30.14,3.15,1.43),(30.46,4.30,1.46),t),30,-.02
 if i in (4,6,8,10):
  a,b,l,roll={4:(1.92,1.67,39,.025),6:(1.61,1.42,36,.175),8:(1.40,1.20,45,-.175),10:(1.76,1.58,37,.07)}[i]
  d=a+(b-a)*t
  if i==4:return V((hip.x+.31-.12*t,hip.y-d,z+1.04+.06*t)),hip+V((.16,0,.94)),l,roll
  height=1.15 if i==6 else 1.04 if i!=10 else 1.14
  return V((hip.x+.45-.18*t,hip.y-d,z+.98+.10*t)),hip+V((.02,0,height)),l,roll
 if i==5:return mix((62.14,-3.92,3.47),(61.86,-3.61,3.30),t),mix((60.02,-.04,1.12),(60.10,.03,1.15),t),41,-.035
 if i==7:return mix((61.08,-3.79,.47),(60.82,-3.54,.60),t),V((60.08,.03,1.32)),34,-.055
 if i==9:return mix((61.63,-3.01,2.38),(61.44,-2.71,2.27),t),mix((60.10,.01,1.36),(60.02,.02,1.40),t),35,.055
 if i==11:
  tilt=1-(1-t)**2.8
  return mix((30.51,.40,.38),(30.51,.76,1.28),t),mix((30.16,2.03,.33),(30.16,2.03,1.63),tilt),27,-.025
 if i==12:return mix((30.34,.58,1.43),(30.27,.91,1.42),t),V((30.16,2.03,1.56)),27,-math.radians(9)
 if i==13:return mix((28.20,1.47,.95),(28.34,1.56,1.00),t),mix((30.24,2.11,.94),(30.18,2.12,.91),t),29,.035
 return mix((31.46,.43,1.85),(32.06,.21,2.15),t),mix((30.23,2.55,.92),(30.48,2.73,.88),t),29,-.035
def make():
 IMAGES.clear()
 s=bpy.data.scenes.new('Shuddh Hindi Washroom Experiment')
 g=Stage(s);world(s)
 room=classroom(g);wash,door,gl=washroom(g);studio=office(g)
 s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.use_raytracing=False;s.eevee.taa_render_samples=16
 s.render.use_simplify=True;s.render.simplify_subdivision_render=2
 s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=30;s.frame_start=1;s.frame_end=1404
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
 s.render.use_sequencer=False;compose(s)
 audio=s.sequence_editor_create().sequences.new_sound('Hindi narration',str(OUT/'narration.wav'),channel=1,frame_start=1)
 audio.sound.pack()
 d=bpy.data.cameras.new('Portrait moving camera');cam=g.link('Portrait moving camera',d);s.camera=cam
 d.sensor_fit='VERTICAL';d.sensor_height=36;d.clip_end=90;d.dof.use_dof=True;d.dof.aperture_fstop=2.6
 h=Actor(g,'char_protagonist','hero',.89);b=Actor(g,'char_beti','beti',.76);l=Actor(g,'char_licker','licker',.75)
 rings=[]
 for j in range(4):
  m=alpha_mat('Cabin luminous sound ribbon',h=('c85aff' if j%2 else '44ffd1'),a=.60)
  rings.append(g.curve('Cabin sound wave',[(0,.43*math.cos(k*math.tau/72),.43*math.sin(k*math.tau/72)) for k in range(72)],.020,m,wash,True))
  rings[-1].rotation_euler.z=math.pi/2
 soul=draw(g,'Translucent spiral-eyed ghost-soul','ghost.png',.65,.70,None)
 scream_lines=draw(g,'White scream speed lines','scream_lines.png',1.41,1.41,None)
 questions=[draw(g,'Yellow question mark','question.png',.29,.32,None) for _ in range(3)]
 streams=[g.curve('Temple waterfall',[(sign*(.285+.012*math.sin(k*.8)),.15-k*.040,.040) for k in range(15)],.020,alpha_mat('Cyan sweat stream',h='8be0ff',a=.85),h.head) for sign in (-1,1)]
 foam=[]
 for j in range(39):
  foam.append(g.ball('Foam particle', (0,0,0),(.10,.10,.10),g.mat(['e8f9ff','d4eeff','fbfffe'][j%3],em=.38,rough=.32)))
 foam_mat=g.mat('f5fbff',em=.53)
 jet=g.curve('Continuous white foam arc',[(30.16+.20*t,2.11+1.58*t,.53+.48*math.sin(math.pi*t)-.48*t) for t in (k/40 for k in range(41))],.096,foam_mat)
 puddle=g.ball('Spreading floor foam',(30.36,3.72,.035),(.65,.49,.034),foam_mat)
 speed_lines=[]
 for j in range(12):
  a=j*math.tau/12;v=V((math.cos(a),math.sin(a),0));o=g.curve('Floor radial speed line',[(30.36+v.x*r,3.72+v.y*r,.052) for r in (.54,.92+.1*(j%3))],.011,alpha_mat('White impact ink',h='e7f7ff',a=.74))
  speed_lines.append(o)
 art=json.loads((ART/'envelope.json').read_text())
 for i,(start,end,rep,name) in enumerate(CUTS):
  s.timeline_markers.new(name,frame=start)
  office_shot=i in (5,7,9)
  for f in range(start,end+1):
   u=(f-start)/max(1,end-start);t=ease(u);beat=math.sin((f-start)*math.tau/6)
   if i==0:hip=V((.016*math.sin(f*.51),.53,.52+.011*math.sin(f*.69)))
   elif i==1:hip=V((.01,.15,.52+.25*ease(u*2)+.019*beat))
   elif i==2:hip=V((.10*math.sin(f*.24),6.50+6.18*u,.742+.021*math.sin(f*math.tau/12)**2))
   elif i==3:hip=V((29.70+.10*t,-.36+1.12*t,.76))
   else:hip=V((30.32 if i==4 else 30.16,2.03 if i>=11 else 2.91 if i==4 else 1.96,.76))
   if i==13:
    hip.y+=.094*beat
    hip.z-=.105+.065*beat
   if i==14:hip.z+=.034*ease(u*3)
   p,q,lens,roll=shot_view(i,t,hip)
   if i==10 and f<start+6:p.x+=.041*math.sin((f-start)*2)*(1-(f-start)/6)
   if i==12 and 1220<=f<1224:
    impact=(1-(f-1220)/4)
    p+=V((.012*impact*(-1)**f,.037*impact,.009*impact*(-1)**f))
   cam.location=p;rot=aim(p,q)@Quaternion((0,0,1),roll)
   cam.rotation_mode='QUATERNION';cam.rotation_quaternion=rot;d.lens=lens
   d.shift_x=-.10 if i==14 else 0
   focus=V((60.07,-.02,1.57)) if office_shot else hip+V((0,0,.91))
   if i==3:focus=V((30.5,3.1,1.29))
   if i==11:focus=hip+V((0,0,.16+.74*t))
   if i==14:focus=V((30.21,2.7,1.12))
   d.dof.focus_distance=max(.36,(focus-p).dot(rot@V((0,0,-1))))
   for o,path in [(cam,'location'),(cam,'rotation_quaternion'),(d,'lens'),(d,'shift_x'),(d,'dof.focus_distance')]:key(o,path,f)
   if f==start:
    for actor,on in [(h,not office_shot),(b,office_shot),(l,office_shot)]:
     actor.root.scale=(1,)*3 if on else (.000001,)*3
     if not on:actor.root.location=(-125,0,0)
     else:actor.root.location=(0,0,0)
     key(actor.root,'location',f);key(actor.root,'scale',f)
   if not office_shot:
    color='d8ecff' if i==8 else 'profile' if i==13 else 'fffdf9'
    sty={4:'shock',6:'confused',8:'crossed',10:'dizzy',12:'scream',13:'profile',14:'dizzy'}.get(i,'panic')
    amount=art[f-1] if i in (12,13) else 0
    h.paint(hip,rot,.47*math.sin(f*.31) if i==0 else (-.32 if i in (4,6,8) else .05),'back' if i==3 else color,'back' if i==3 else sty,amount,f)
    forward=V((0,1 if i<3 else -1,0))
    feet=[];hands=[]
    for j,sign in enumerate((-1,1)):
     fx=hip.x+sign*.19;fy=hip.y;fz=.050
     if i==0:
      fy+=.38;fz+=.035+.035*math.sin(f*math.tau/2.5+j*1.1)
     elif i==2:
      stride=18;phase=((f-start+j*9)%stride)/stride
      first=f-((f-start+j*9)%stride)
      speed=6.18/(end-start)
      f_y=6.5+speed*(first-start)+.34
      fy=f_y+(.0 if phase<.51 else speed*stride*ease((phase-.51)/.49))
      fz+=.27*max(0,math.sin(math.pi*(phase-.51)/.49)) if phase>=.51 else 0
     elif i==13:
      fy=1.79;fx+=sign*.21
     elif i==14:
      fy-=.05;fz=.084
     feet.append((fx,fy,fz))
     if i==0:hand=(hip.x+sign*.24,hip.y+.43,.852)
     elif i==3 and j==1:
      angle=.0+1.41*ease((f-start)/64)
      hand=(29.53+.70*math.cos(angle),.05+.70*math.sin(angle),1.15)
     elif i==8:hand=hip+V((sign*.36,-.035,.80))
     elif i==10:hand=h.head.location+rot@V((sign*.48,.14,.037))
     elif i==12:hand=h.head.location+rot@V((sign*.378,-.205,.071))
     elif i in (11,13):
      tremor=.024*beat if i==11 else 0
      hand=hip+V((sign*.20+tremor,.14 if j==0 else -.13,-.032+tremor if j==0 else .018+tremor))
     else:hand=hip+V((sign*.17,.095 if j==0 else -.15,.02 if j==0 else .12))
     hands.append(hand)
    h.support(feet,hands,forward,f,seated=i==0,low_elbows=i==13,temple=i in (10,12),
              knee_rattle=.04*beat if i==11 else 0,tiptoe=i==14)
    h.body.scale=(.78,1,1) if i==13 else (1,1,1);key(h.body,'scale',f)
    if i==11:
     h.body.location-=rot@V((0,.018,.22-.06*t));key(h.body,'location',f)
    if i==13:
     h.body.location-=rot@V((0,.035,.04));key(h.body,'location',f)
     h.body.rotation_quaternion=rot@Quaternion((0,0,1),.22+.075*beat)
     h.shorts.rotation_euler.x=.19*beat;key(h.body,'rotation_quaternion',f);key(h.shorts,'rotation_euler',f)
    elif f==start:
     h.shorts.rotation_euler.x=0;key(h.shorts,'rotation_euler',f)
    h.sweat(f,2 if i==4 else 1 if i not in (6,8,10,11,14) else 0)
   else:
    base1=V((59.46,.17,1.30));base2=V((60.61,-.08,.548))
    phase=math.sin((f-start)*math.tau/(9 if i==9 else 13));off=.045*phase
    base2.x+=off
    b.paint(base1,rot,.33,'fffdf9','smug',art[f-1],f)
    l.paint(base2,rot,-.40,'fffdf9','open',max(1,art[f-1]),f)
    mouth=l.head.location+rot@V((-.051,-.115,.064))
    leg_axis=(mouth-base1).normalized()
    ankle=mouth+leg_axis*(-.145+.060*phase)-V((0,0,.017))
    b.support([(59.32,-.20,.83),ankle],[(59.14,.03,1.52),(59.76,-.12,1.43)],V((.8,-.35,0)),f,True,leg_axis)
    l.support([(60.31,-.39,.061),(60.82,-.44,.061)],[(60.09,-.24,.814),(60.11,.21,.814)],V((-.54,-.72,0)),f,True)
   if i==3:
    door.rotation_euler.z=1.41*ease((f-start)/64);key(door,'rotation_euler',f)
   if i in (3,4,6,8,10,11,12,13,14):
    gl.data.energy=135+115*math.sin(f*.125)**2;key(gl.data,'energy',f)
   if i==3 or f in (1,496):
    for j,o in enumerate(rings):
     u2=((f-start+j*9)%42)/42;k=.28+u2*1.34
     o.location=(1.28,4.13-u2*.78,1.13);o.scale=(k,)*3;key(o,'scale',f);key(o,'location',f)
     if f in (1,start,496):flag(o,i==3,f)
   if f in (1,1015,1063,1331) or i in (10,14):
    if f in (1,1015,1063,1331):flag(soul,i in (10,14),f)
    ghost_offset=(.24,.37+.17*t,.07) if i==10 else (.54,.29+.12*t,.07)
    soul.location=h.head.location+rot@V(ghost_offset);soul.rotation_mode='QUATERNION';soul.rotation_quaternion=rot
    key(soul,'location',f);key(soul,'rotation_quaternion',f)
   if f in (1,787,847):
    for o in questions:flag(o,i==6,f)
   if i==6:
    for j,o in enumerate(questions):
     x,y=[(-.24,.45),(.02,.56),(.33,.43)][j]
     o.location=h.head.location+rot@V((x,y+.023*math.sin(f*.18+j),.055))
     o.rotation_mode='QUATERNION';o.rotation_quaternion=rot@Quaternion((0,0,1),.23*(j-1))
     key(o,'location',f);key(o,'rotation_quaternion',f)
   if f in (1,907,955):
    for o in streams:flag(o,i==8,f)
   if f in (1,1195,1264):flag(scream_lines,i==12,f)
   if i==12:
    scream_lines.location=h.head.location-rot@V((0,0,.19))
    scream_lines.rotation_mode='QUATERNION';scream_lines.rotation_quaternion=rot
    k=1+.055*math.sin(f*.70);scream_lines.scale=(k,)*3
    for path in ('location','rotation_quaternion','scale'):key(scream_lines,path,f)
   if f==1 or i==14:
    if f in (1,1331):
     for o in [jet,puddle]+speed_lines:flag(o,i==14,f)
    if i==14:
     k=.28+.72*ease((f-1331)/25);puddle.scale=(.65*k,.49*k,.034);key(puddle,'scale',f)
     jet.scale.z=.93+.095*math.sin(f*.8);key(jet,'scale',f)
    for j,o in enumerate(foam):
     if f in (1,1331):flag(o,i==14,f)
     t2=((f-1331+j*3)%49)/49
     spr=math.sin(j*2.39);o.location=(30.08+spr*(.13+.81*t2),2.02+3.20*t2,.095+.87*math.sin(math.pi*t2)*(1-.48*(j%4)/4))
     r=(.048+(j%5)*.023)*(.5+.7*math.sin(math.pi*t2));o.scale=(r,r*1.8,r*.86)
     key(o,'location',f);key(o,'scale',f)
 # Cuts and swaps stay discrete. Pose, camera and focus interpolate between samples.
 discrete={end for _,end,_,_ in CUTS}
 for owner in list(s.objects)+[d,gl.data]:
  ad=owner.animation_data
  if ad and ad.action:
   for fc in ad.action.fcurves:
    swap=' face ' in owner.name or ' solid head ' in owner.name or owner in (h.root,b.root,l.root)
    for kp in fc.keyframe_points:kp.interpolation='CONSTANT' if swap or fc.data_path.startswith('hide_') or round(kp.co.x) in discrete else 'LINEAR'
 s['Scope']='Director refinement: fifteen calibration frames and 540 × 960 preview';s['Narration']='46.80 seconds from Untitled design.mp4; source picture discarded'
 s.frame_set(100)
 bpy.data.libraries.write(str(OUT/'washroom_experiment.blend'),{s},fake_user=True,compress=True)
 bpy.app.driver_namespace['washroom_experiment']=s
 return s
