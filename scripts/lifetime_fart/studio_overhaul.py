"""Frame-addressable final pass for the Lifetime Fart Blender builders."""
import math
import random
import re
from pathlib import Path

import bpy
from mathutils import Vector, Matrix
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'out/lifetime_fart'
ART=ROOT/'output/blender/lifetime_fart_art'
ART.mkdir(parents=True,exist_ok=True)
# Inclusive frame ranges. Old shot samples are pulled back into the new cue map.
MAP=[
 (1,225,1,144),(226,305,145,264),(306,384,265,384),
 (385,474,385,465),(475,636,466,630),(637,720,631,710),(721,810,711,804),
 (811,900,805,900),(901,1008,901,1005),(1009,1086,1006,1086),
 (1087,1206,1087,1206),(1207,1296,1207,1296),(1297,1425,1297,1425),
 (1426,1584,1546,1686),(1585,1620,1426,1444),(1621,1704,1445,1545),
 (1705,1974,1687,1974),(1975,2115,1975,2070),(2116,2175,2071,2160),
 (2176,2234,2161,2209),(2235,2286,2210,2274),(2287,2454,2275,2445),
 (2455,2532,2455,2526),(2533,2715,2527,2715),
]
CAL=[100,258,335,440,555,685,765,857,954,1030,1145,1252,1360,1504,1603,1660,1870,2040,2143,2245,2360,2455,2485,2620]
C=Vector
def rgb(s):
 x=[int(s[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(a/12.92 if a<=.04045 else ((a+.055)/1.055)**2.4 for a in x)
def ease(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def key(o,p,f):o.keyframe_insert(data_path=p,frame=f)
def constant(o,p):
 if not o.animation_data or not o.animation_data.action:return
 for fc in o.animation_data.action.fcurves:
  if fc.data_path==p:
   for k in fc.keyframe_points:k.interpolation='CONSTANT'
def vis(o,windows,recursive=False):
 for ob in [o]+(list(o.children_recursive) if recursive else []):
  if ob.animation_data and ob.animation_data.action:
   act=ob.animation_data.action
   for fc in list(act.fcurves):
    if fc.data_path in ['hide_render','hide_viewport']:act.fcurves.remove(fc)
  events={1}
  for a,b in windows:events.update([a,b+1])
  for f in sorted(events):
   ob.hide_viewport=ob.hide_render=not any(a<=f<=b for a,b in windows)
   key(ob,'hide_render',f);key(ob,'hide_viewport',f)
  constant(ob,'hide_render');constant(ob,'hide_viewport')
def retime():
 samples=[(f,c+(d-c)*(f-a)/max(1,b-a)) for a,b,c,d in MAP for f in range(a,b+1)]
 boundaries={a for a,b,c,d in MAP}|{b for a,b,c,d in MAP}
 for action in bpy.data.actions:
  for fc in action.fcurves:
   if not fc.keyframe_points:continue
   vals=[(f,fc.evaluate(t)) for f,t in samples]
   flat=fc.data_path.endswith(('hide_render','hide_viewport')) or all(k.interpolation=='CONSTANT' for k in fc.keyframe_points)
   keep=[v for i,v in enumerate(vals) if v[0] in boundaries or (abs(vals[i-1][1]-v[1])>1e-6 if flat else abs(vals[i-1][1]+vals[i+1][1]-2*v[1])>1e-6)]
   for k in reversed(list(fc.keyframe_points)):fc.keyframe_points.remove(k,fast=True)
   fc.keyframe_points.add(len(keep));fc.keyframe_points.foreach_set('co',[x for v in keep for x in v])
   for k in fc.keyframe_points:k.interpolation='CONSTANT' if flat or int(k.co.x) in boundaries else 'LINEAR'
   fc.update()
def emission(name,color,strength=1,alpha=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(*rgb(color),1);e.inputs[1].default_value=strength
 o=n.new('ShaderNodeOutputMaterial')
 if alpha==1:l.new(e.outputs[0],o.inputs[0])
 else:
  t=n.new('ShaderNodeBsdfTransparent');x=n.new('ShaderNodeMixShader');x.inputs[0].default_value=alpha
  l.new(t.outputs[0],x.inputs[1]);l.new(e.outputs[0],x.inputs[2]);l.new(x.outputs[0],o.inputs[0]);m.surface_render_method='DITHERED'
 return m
def opaque(name,color,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 p.inputs['Base Color'].default_value=(*rgb(color),1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.58
 return m
def cel_strength(m,strength=1.12):
 n=m.node_tree.nodes;l=m.node_tree.links
 im=next((x for x in n if x.type=='TEX_IMAGE'),None)
 if im is None:return
 o=next(x for x in n if x.type=='OUTPUT_MATERIAL')
 e=n.new('ShaderNodeEmission');e.inputs[1].default_value=strength;l.new(im.outputs['Color'],e.inputs[0])
 t=n.new('ShaderNodeBsdfTransparent');x=n.new('ShaderNodeMixShader')
 l.new(im.outputs['Alpha'],x.inputs[0]);l.new(t.outputs[0],x.inputs[1]);l.new(e.outputs[0],x.inputs[2]);l.new(x.outputs[0],o.inputs[0])
 m.surface_render_method='DITHERED'
 return im
def world_gradient(scene):
 w=bpy.data.worlds.new('Vertical exterior gradients and independent fill');scene.world=w;w.use_nodes=True
 n=w.node_tree.nodes;n.clear();l=w.node_tree.links
 tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Normal'],sep.inputs[0])
 # World Normal points into the visible hemisphere; map horizon and zenith.
 mapn=n.new('ShaderNodeMapRange');mapn.inputs['From Min'].default_value=-.58;mapn.inputs['From Max'].default_value=.11
 l.new(sep.outputs['Z'],mapn.inputs[0]);combine=n.new('ShaderNodeCombineXYZ');l.new(mapn.outputs[0],combine.inputs['X'])
 tex=n.new('ShaderNodeTexGradient');l.new(combine.outputs[0],tex.inputs[0])
 palettes=[('1b6ca8','56b4e9','e8f4f8'),('060d1f','16428b','68d8ff'),('080b1a','1a1b4b','3c245c'),('040d18','0b2633','12333d'),('35243c','6b453b','b67a56')]
 ramps=[]
 for i,p in enumerate(palettes):
  ramp=n.new('ShaderNodeValToRGB');ramp.label=['Day','Stratosphere','Rooftop','X-ray','Interior'][i]
  a,b=ramp.color_ramp.elements;a.position=.06;b.position=.97;a.color=(*rgb(p[0]),1);b.color=(*rgb(p[2]),1)
  ramp.color_ramp.elements.new(.64).color=(*rgb(p[1]),1);l.new(tex.outputs['Fac'],ramp.inputs[0]);ramps.append(ramp)
 last=ramps[0].outputs[0]
 beats=[(1,4),(226,3),(475,0),(637,4),(721,3),(1009,4),(1087,3),(1207,0),(1426,1),(1585,0),(1621,1),(1816,2),(1975,2),(2287,4),(2533,1)]
 for i,r in enumerate(ramps[1:],1):
  x=n.new('ShaderNodeMixRGB');l.new(last,x.inputs[1]);l.new(r.outputs[0],x.inputs[2]);last=x.outputs[0]
  for f,j in beats:x.inputs[0].default_value=float(i==j);x.inputs[0].keyframe_insert('default_value',frame=f)
 constant(w.node_tree,'none')
 for fc in w.node_tree.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='CONSTANT'
 bg=n.new('ShaderNodeBackground');l.new(last,bg.inputs[0]);bg.inputs[1].default_value=1
 amb=n.new('ShaderNodeBackground');amb.inputs[0].default_value=(.43,.54,.76,1);amb.inputs[1].default_value=.30
 path=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');o=n.new('ShaderNodeOutputWorld')
 l.new(path.outputs['Is Camera Ray'],mix.inputs[0]);l.new(amb.outputs[0],mix.inputs[1]);l.new(bg.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],o.inputs[0])
def compositor(scene):
 scene.use_nodes=True;n=scene.node_tree.nodes;n.clear();l=scene.node_tree.links
 inp=n.new('CompositorNodeRLayers');g=n.new('CompositorNodeGlare');g.glare_type='FOG_GLOW';g.threshold=.82;g.size=7;g.mix=.18
 g.quality='MEDIUM';l.new(inp.outputs['Image'],g.inputs[0])
 im=Image.new('RGB',(320,568));vals=[]
 for y in range(568):
  for x in range(320):
   u=abs(2*x/319-1);v=abs(2*y/567-1)
   a=ease((max(u,v)-.76)/.24)*(.30+.70*min(u,v)**1.3)
   # Linear multiplier encoded into the mask's sRGB image.
   shade=round(255*(1.055*(1-.18*a)**(1/2.4)-.055));vals.append((shade,)*3)
 im.putdata(vals);path=ART/'vignette.png';im.save(path)
 mask=n.new('CompositorNodeImage');mask.image=bpy.data.images.load(str(path));mask.image.pack()
 size=n.new('CompositorNodeScale');size.space='RENDER_SIZE';l.new(mask.outputs[0],size.inputs[0])
 m=n.new('CompositorNodeMixRGB');m.blend_type='MULTIPLY';m.inputs[0].default_value=1
 l.new(g.outputs[0],m.inputs[1]);l.new(size.outputs[0],m.inputs[2]);o=n.new('CompositorNodeComposite');l.new(m.outputs[0],o.inputs[0])
def light(scene,name,typ,loc,target,col,power,windows,parent=None):
 d=bpy.data.lights.new(name,typ);d.color=rgb(col);d.energy=power;d.use_shadow=True
 if typ=='SUN':d.angle=math.radians(12)
 if typ=='AREA':d.shape='DISK';d.size=2.0
 if typ=='POINT':d.shadow_soft_size=.30
 o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.parent=parent;o.location=loc
 if typ!='POINT':o.rotation_euler=(C(target)-C(loc)).to_track_quat('-Z','Y').to_euler()
 vis(o,windows);return o
def lighting(scene):
 windows={
  'LR_':[(1,225),(637,720),(1009,1086)],'VH_':[(475,636)],'SKY_':[(1207,1425)],
  'XR_':[(226,474),(721,1008),(1087,1206)],'ST_':[(1426,1974)],
  'NR_':[(1975,2286)],'CD_':[(2287,2532)],'OS_':[(2533,2715)]}
 for o in [o for o in scene.objects if o.type=='LIGHT']:
  tag=o.name[:o.name.index('_')+1] if '_' in o.name else ''
  if tag not in windows:continue
  o.data.animation_data_clear()
  if o.data.type=='SUN':
   o.data.energy=3.8 if tag not in ('NR_','XR_') else .47
   o.data.angle=math.radians(12);o.data.use_shadow=True
  elif o.data.type=='AREA':o.data.energy=min(100,max(60,o.data.energy))
  else:o.data.energy=0
  vis(o,windows[tag])
 for tag,ranges in windows.items():
  night=tag in ('NR_','XR_','OS_')
  light(scene,'Studio '+tag+' cool fill','AREA',(2.1,-1.8,2.4),(0,0,.8),'b7c7ff',75 if night else 95,ranges)
  light(scene,'Studio '+tag+' back rim','AREA',(-1.25,2.4,2.5),(0,0,1),'82d2ff' if night else 'ffbc79',80,ranges)
 light(scene,'Studio desk directional key','SUN',(-2.5,-2.5,3.5),(0,0,0),'ffddb1',3.8,windows['CD_'])
 core=bpy.data.objects.get('Hero_Root')
 gas=light(scene,'Blast-driven green point','POINT',(0,-.14,.34),(0,0,0),'39ff5a',250,[(226,474),(637,1206)],core)
 for f,val in [(226,250),(385,360),(474,520),(637,250),(720,300),(721,800),(810,580),(811,800),(1008,280),(1009,800),(1086,380),(1087,800),(1206,300)]:
  gas.data.energy=val;key(gas.data,'energy',f)
 for name,win,loc in [('ST_MeteorFire_Grp',[(1816,1974)],(0,-.24,.25)),('NR_MeteorStreak',[(1975,2286)],(0,-.1,0))]:
  light(scene,name+' moving golden light','POINT',loc,(0,0,0),'ff8822',500,win,bpy.data.objects.get(name))
def bevel(o,r):
 m=o.modifiers.new('Soft manufactured edge','BEVEL');m.width=r;m.segments=2
 return o
def cube(name,dims,loc,m,par,col,bevel_size=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.view_layer.objects.active;o.name=name
 o.data.transform(Matrix.Diagonal((*dims,1)));o.parent=par
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(m)
 if bevel_size:bevel(o,bevel_size)
 return o
def ball(name,loc,sc,m,par,col):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=loc)
 o=bpy.context.view_layer.objects.active;o.name=name;o.scale=sc;o.parent=par
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o
def cylinder(name,r,h,loc,m,par,col,axis='Z'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=r,depth=h,location=loc)
 o=bpy.context.view_layer.objects.active;o.name=name;o.parent=par
 if axis=='X':o.rotation_euler.y=math.pi/2
 if axis=='Y':o.rotation_euler.x=math.pi/2
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(m);return o

def correction(scene):
 """Single review pass after the v4 calibration and moving preview."""
 from io import BytesIO
 O=bpy.data.objects;K=bpy.data.collections;cam=scene.camera;D=cam.data
 for name in ['VH_SkyWall','VH_RoadFloor','XR_NozzleRing','XR_LaserCone']:
  if O.get(name):vis(O[name],[])
 for o in list(O.values()):
  if o.name.startswith('Tanker rear ladder'):vis(o,[(475,636)])
 # Keep HUD boxes inside a true camera-projected safe zone, including zooms.
 for o in [o for o in scene.objects if o.name.startswith('HUD_Card_')]:
  xs=[v.co.x for v in o.data.vertices];ys=[v.co.y for v in o.data.vertices]
  target=.84 if not o.name.endswith(('you_tag','nozzle_1s','still_sitting')) else .64
  for f in [1,475,636,721,810,1426,1585,1621,1705,1975,2287,2533,2715]:
   scene.frame_set(f)
   lens=37 if 475<=f<=636 else 42
   frame=D.view_frame(scene=scene);x=max(abs(v.x/v.z) for v in frame)*D.lens/lens
   y=max(abs(v.y/v.z) for v in frame)*D.lens/lens
   depth=.72
   w=2*x*depth*target
   scale=w/(max(xs)-min(xs))
   h=(max(ys)-min(ys))*scale
   o.location=(0,min(.70*y*depth,y*depth-h/2-.045*y*depth),-depth)
   o.scale=(scale,scale,1)
   for p in ['location','scale']:key(o,p,f)
   constant(o,'location');constant(o,'scale')
 # Space labels distinguish the ascent and high-altitude story beats.
 from part2_scenes_5_to_7_and_calibration import generate_hud_banner, generate_part2_head_sprite
 def replace_hud(name,title,sub,windows):
  o=O.get('HUD_Card_'+name)
  if not o:return
  p=generate_hud_banner('v5_hud_'+name+'.png',title,sub)
  m=o.data.materials[0];t=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
  t.image=bpy.data.images.load(p);t.image.pack();vis(o,windows)
 replace_hud('mach8_top','2 KM UP','< STILL SITTING!',[(1621,1704)])
 replace_hud('sound_behind','MACH 8','THE SOUND IS BACK THERE',[(1426,1584)])
 replace_hud('meteor_mode','METHANE + AIR FRICTION','HUMAN METEOR IGNITION',[(1816,1974)])
 if O.get('HUD_Card_still_sitting'):vis(O['HUD_Card_still_sitting'],[])
 replace_hud('cnt_130k','1,30,000 FARTS','BY AGE 25',[(306,384)])
 replace_hud('cnt_14','14 FARTS / DAY','DAILY HUMAN AVERAGE',[(235,270)])
 replace_hud('cnt_38k','38,269 FARTS','ESTIMATED BY AGE 8',[(271,305)])
 # Keep the paper and the stamped impression independent of the bright key.
 paper=O['CD_NewspaperCard'];overlay=O['CD_StampOverlayCard']
 for o in [paper,overlay]:cel_strength(o.data.materials[0],.86)
 def packed_image(o):
  n=next(q for q in o.data.materials[0].node_tree.nodes if q.type=='TEX_IMAGE')
  im=n.image
  return Image.open(BytesIO(im.packed_file.data) if im.packed_file else bpy.path.abspath(im.filepath)).convert('RGBA')
 talk=O.get('Neighbor_Head_pray_talk')
 wink=O.get('Neighbor_Head_one_eye_wish')
 if talk and wink:
  import json
  env=json.loads((OUT/'voice_env.json').read_text())
  idle=packed_image(wink)
  speaking=packed_image(talk)
  w,h=idle.size
  # Keep the wink artwork and replace only the mouth region, sampling five amplitudes.
  src=(int(.438*w),int(.574*h),int(.596*w),int(.646*h))
  mouth=speaking.crop(src)
  clear=idle.crop((src[0],int(.558*h),src[2],int(.574*h))).resize((src[2]-src[0],src[3]-src[1]))
  states=[]
  for idx in range(1,6):
   img=idle.copy()
   img.paste(clear,src[:2])
   mk=mouth.resize((mouth.width,max(1,round(mouth.height*idx/5))),Image.Resampling.LANCZOS)
   img.paste(mk,(src[0],src[1]+(mouth.height-mk.height)//2))
   path=ART/f'neighbor_wink_syllable_{idx}.png'
   img.save(path)
   ob=wink.copy();ob.data=wink.data.copy();ob.animation_data_clear()
   wink.users_collection[0].objects.link(ob)
   mat=wink.data.materials[0].copy();ob.data.materials[0]=mat
   node=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
   node.image=bpy.data.images.load(str(path));node.image.pack()
   states.append(ob)
  def spans(frame_iter):
   ranges=[]
   for f in frame_iter:
    if ranges and ranges[-1][1]==f-1:ranges[-1][1]=f
    else:ranges.append([f,f])
   return ranges
  def syllable(f):return min(5,max(0,round(env[f-1]*5)))
  vis(talk,spans(f for f in range(2116,2176) if env[f-1]>.18))
  closed=O.get('Neighbor_Head_pray_closed')
  if closed:vis(closed,spans(f for f in range(2116,2176) if env[f-1]<=.18))
  vis(wink,spans(f for f in range(2176,2287) if syllable(f)==0))
  for j,ob in enumerate(states,1):vis(ob,spans(f for f in range(2176,2287) if syllable(f)==j))
 for ob in [o for o in O.values() if o.name.startswith('Hero_Head_') and 'meteor' in o.name.lower()]:
  m=ob.data.materials[0];tex=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
  path=generate_part2_head_sprite('v5_meteor_face.png','hero_meteor_face')
  tex.image=bpy.data.images.load(path);tex.image.pack()
 clean=packed_image(paper);stamp=packed_image(overlay)
 clean.save(ART/'coroner_unstamped.png')
 w,h=clean.size
 stamp=stamp.resize((round(w*.50/.62),round(h*.16/.93)),Image.Resampling.LANCZOS).rotate(-4.5,Image.Resampling.BICUBIC,expand=True)
 final=clean.copy();final.alpha_composite(stamp,(round(w*.5-stamp.width*.5),round(h*(.5+.30/.93)-stamp.height*.5)))
 final.save(ART/'coroner_stamped.png')
 pm=paper.data.materials[0];nt=pm.node_tree
 n1=next(q for q in nt.nodes if q.type=='TEX_IMAGE');n1.image=bpy.data.images.load(str(ART/'coroner_unstamped.png'));n1.image.pack()
 n2=nt.nodes.new('ShaderNodeTexImage');n2.image=bpy.data.images.load(str(ART/'coroner_stamped.png'));n2.image.pack()
 mix=nt.nodes.new('ShaderNodeMixRGB');links=nt.links
 links.new(n1.outputs[0],mix.inputs[1]);links.new(n2.outputs[0],mix.inputs[2])
 active=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL').inputs[0].links[0].from_node
 e=active.inputs[2].links[0].from_node
 links.new(mix.outputs[0],e.inputs[0])
 for f,t in [(1,0),(2454,0),(2455,1),(2715,1)]:mix.inputs[0].default_value=t;mix.inputs[0].keyframe_insert('default_value',frame=f)
 for fc in nt.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='CONSTANT'
 vis(overlay,[])
 # Give the sofa actor enough forward clearance for the projected seated ankles.
 hero=O['Hero_Root']
 for a,b in [(1,225),(637,720)]:
  for f in range(a,b+1):
   scene.frame_set(f);hero.location.y=-.055;hero.location.z=.012;key(hero,'location',f)
 root=O['ROOT_LIVING_ROOM'];col=K['SET_LIVING_ROOM']
 for side in [-1,1]:
  o=shadow('Sofa seated ankle contact',(side*.145,-.094,.444),(.099,.07),root,col);vis(o,[(1,225),(637,720)])
 plasma=emission('Sofa blowout core','55ff7b',2.15,.51)
 halo=emission('Sofa blowout soft envelope','46fc7a',1.5,.21)
 for j,(m,radius) in enumerate([(plasma,.045),(halo,.102)]):
  jet=ball('Layered sofa blowout jet',(0,.12,.13), (radius,radius,.35),m,hero,col)
  vis(jet,[(1009,1086)])
  for f,s in [(1009,.6),(1014,1.3),(1030,1),(1070,.72),(1086,.48)]:
   jet.scale=(radius*s,radius*s,.43*s);key(jet,'scale',f)
 # Pre-impact and ascent coverage keeps the head below the top graphics.
 def shoot(f,p,q,lens):
  cam.location=p;cam.rotation_euler=(C(q)-cam.location).to_track_quat('-Z','Y').to_euler();D.lens=lens
  for o,path in [(cam,'location'),(cam,'rotation_euler'),(D,'lens')]:key(o,path,f)
 for f in range(1,2716):
  if f==1:D.lens=42;key(D,'lens',f)
  if 475<=f<=636:
   t=ease((f-475)/161);shoot(f,(.46-.77*t,-5.68+.25*t,1.77),(.04,0,.84),37)
  if f in [474,637,1425,1621,1704,1975]:D.lens=42;key(D,'lens',f)
  if 1426<=f<=1620:
   scene.frame_set(f);x,y,z=hero.matrix_world.translation
   t=ease((f-1585)/35)
   if f<1585:shoot(f,(.12,-3.30,z+1.03),(x,.28,z+.78),40)
   else:shoot(f,(.31,-3.60,z+1.15),(x,.28,z+.67-.08*t),41)
  if 1705<=f<=1974:
   t=ease((f-1705)/269)
   scene.frame_set(f)
   hero.location.x=-.34+.64*t;hero.location.z=.21+.59*t;key(hero,'location',f)
   shoot(f,(-.17+.31*t,-3.27,.96+.34*t),(-.08+.19*t,.32,.94+.30*t),41)
 # Keep the source 500 W bound to the real moving plasma core.
 if O.get('ST_MeteorFire_Grp moving golden light'):
  li=O['ST_MeteorFire_Grp moving golden light'];li.parent=hero;li.location=(0,.05,.38)
 if O.get('Blast-driven green point'):
  O['Blast-driven green point'].location=(0,-.53,.22)
 heat=light(scene,'Friction heat build','POINT',(0,-.03,.28),(0,0,0),'ef4a23',0,[(1705,1815)],hero)
 for f,e in [(1705,0),(1760,35),(1810,220),(1815,370)]:
  heat.data.energy=e;key(heat.data,'energy',f)
 hot=emission('Friction corona','ef4328',1.15,.11)
 heat_shell=ball('Friction heat shell',(.0,.22,.66),(.30,.13,.63),hot,hero,K['SET_STRATOSPHERE'])
 vis(heat_shell,[(1735,1815)])
 for f,s in [(1735,.25),(1780,.62),(1815,1)]:
  heat_shell.scale=(.30*s,.13*s,.63*s);key(heat_shell,'scale',f)
 # Hide the old flat illustrated flames and use the same seated body through the ignition.
 body=next((o for o in O.values() if o.name=='Hero_Body_Bloated'),None)
 meteor=next((o for o in O.values() if o.name.startswith('Hero_Body_') and 'meteor' in o.name.lower()),None)
 if body and meteor:
  meteor.data.materials[0]=body.data.materials[0]
 for o in list(O.values()):
  if o.name.startswith(('Hero_Body_','Hero_Head_')):
   if o.type!='MESH' or not o.data.materials:continue
   m=o.data.materials[0];nt=m.node_tree
   if not nt:continue
   for e in nt.nodes:
    if e.type=='EMISSION':
     tex=e.inputs[0].links[0].from_socket if e.inputs[0].is_linked else None
     if tex and tex.node.type=='TEX_IMAGE':
      protect=nt.nodes.new('ShaderNodeMixRGB');protect.blend_type='MULTIPLY'
      protect.inputs[0].default_value=1;protect.inputs[2].default_value=(.9,.9,.9,1)
      nt.links.new(tex,protect.inputs[1]);nt.links.new(protect.outputs[0],e.inputs[0])
 # Plume shells taper to transparent at their edges and scroll along the plume.
 for m in [m for m in bpy.data.materials if m.name.startswith(('Meteor white-yellow','Meteor gold plasma','Meteor vermilion','Meteor methane'))]:
  n=m.node_tree.nodes;l=m.node_tree.links;x=next(q for q in n if q.type=='MIX_SHADER')
  a=x.inputs[0].default_value
  w=n.new('ShaderNodeLayerWeight')
  inv=n.new('ShaderNodeMath');inv.operation='SUBTRACT';inv.inputs[0].default_value=1;l.new(w.outputs['Facing'],inv.inputs[1])
  tc=n.new('ShaderNodeTexCoord');tx=n.new('ShaderNodeTexNoise');tx.noise_dimensions='4D';tx.inputs['Scale'].default_value=4.5;l.new(tc.outputs['Generated'],tx.inputs[0])
  for f in [1816,1895,1974]:
   tx.inputs['W'].default_value=(f-1816)*.049;tx.inputs['W'].keyframe_insert('default_value',frame=f)
  mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(inv.outputs[0],mul.inputs[0]);l.new(tx.outputs['Fac'],mul.inputs[1])
  amp=n.new('ShaderNodeMath');amp.operation='MULTIPLY';amp.inputs[1].default_value=a*1.35;l.new(mul.outputs[0],amp.inputs[0]);l.new(amp.outputs[0],x.inputs[0])
  m.surface_render_method='BLENDED'
 for o in list(O.values()):
  if o.name.startswith('Layered meteor plasma'):
   if o.data.materials[0].name.startswith('Meteor white-yellow'):o.location.z=.18
   else:o.location.z+=.19
 # Add a tapering, softly animated steam trail above each toasted paratha.
 st=emission('Paratha rising steam','d2e3f4',.84,.28)
 for side,name in enumerate(['OS_MooliParatha_L','OS_MooliParatha_R']):
  p=O.get(name)
  if not p:continue
  for j in range(3):
   pts=[(-.09+j*.08+.012*math.sin(i*.65+j),.13+i*.013,.01) for i in range(18)]
   o=stroke('Warm paratha steam ribbon',pts,.007,st,p,K['SET_OUTER_SPACE'])
   vis(o,[(2533,2715)])
   for f in range(2533,2716,9):
    o.scale.y=.79+.18*math.sin((f-2533)*.17+j);o.location.x=.012*math.sin((f-2533)*.17+j);key(o,'scale',f);key(o,'location',f)
 # A 7-frame shake immediately after stamp contact.
 for f in range(2455,2463):
  scene.frame_set(f);u=(f-2455)/7
  a=max(0,1-u);cam.location.x+=.019*a*math.cos((f-2455)*2.4)
  cam.location.y+=.020*a*math.sin((f-2455)*2.4);key(cam,'location',f)
 scene.frame_set(100);bpy.ops.file.pack_all()

def final_alignment(scene):
 """Apply measured contact and HUD clearance in the final camera."""
 hero=bpy.data.objects['Hero_Root'];cam=scene.camera
 for a,b in [(1,225),(637,720)]:
  for f in range(a,b+1):
   scene.frame_set(f);hero.location.y=-.055;hero.location.z=.012;key(hero,'location',f)
 for a,b,dz in [(721,810,.13),(1087,1206,.41),(1297,1425,.27)]:
  values=[]
  for f in range(a,b+1):
   scene.frame_set(f);values.append((f,cam.location.copy()))
  for f,p in values:
   cam.location=p+C((0,0,dz));key(cam,'location',f)
 for mat in bpy.data.materials:
  if mat.name.startswith('Mat_HUD_'):mat.surface_render_method='BLENDED'
 scene.frame_set(100)


def decorate(scene):
 O=bpy.data.objects;K=bpy.data.collections
 cloud=opaque('Porcelain cloud top','f7f9fd');asphalt=opaque('Slate aggregate highway','303d4d');sand=opaque('Horizon amber verge','b2a77f')
 white=opaque('Road enamel','eee9c9');rubber=opaque('Charcoal trim','18232e');silver=opaque('Machined wheel caps','889ca7',.65)
 red=emission('Amber marker lenses','ff7125',1.2);headlamp=emission('Cream lamp lenses','ffe8aa',1.45)
 glass=emission('Blue-green glass','386580',1,.40)
 sky=O.get('SKY_Backdrop')
 if sky:vis(sky,[])
 rng=random.Random(780)
 col=K['SET_VEHICLES'];root=O['ROOT_VEHICLES']
 cube('Asphalt with painted lanes',(15,18,.09),(0,4,-.046),asphalt,root,col)
 for x in [-3.25,3.25]:
  cube('Ochre highway shoulder',(3.0,18,.12),(x,4,-.069),sand,root,col)
 for y in [-2.25,1.35,3.85]:
  for x in range(-6,7):
   cube('Dashed highway markings',(.70,.035,.006),(x*1.1,y,.006),white,root,col)
 for i in range(11):
  x=-5+i*1.0;y=5.7+rng.random()*2.7
  cube('Verge guardrail post',(.035,.05,.39),(x,y,.20),silver,root,col)
 cube('Highway guardrail',(12,.045,.055),(0,6.6,.33),silver,root,col)
 for name in ['VH_SchoolBus','VH_WaterTanker']:
  o=O[name];is_bus=name.endswith('Bus')
  for y in [-.39,.39]:
   for z in ([.47,.64,.99] if is_bus else [.42,.60]):
    cube('School bus charcoal belt' if is_bus else 'Tanker side trim',(1.22 if is_bus else .83,.014,.038),(.02,y,z),rubber,o,col,.005)
   if is_bus:
    for i in range(7):
     cube('School bus window mullion',(.025,.024,.36),(-.57+i*.19,y,.84),rubber,o,col,.005)
    for i in range(6):
     w=cube('Bus cutaway glass window',(.165,.012,.305),(-.475+i*.19,y,.84),glass,o,col,.005)
     for f,s in [(475,1),(512,1),(545,1.25),(636,1.25)]:w.scale.y=s;key(w,'scale',f)
   for x in [-.44,.47]:
    cylinder('Wheel polished rim',.092,.026,(x,y*1.12,.18),silver,o,col,'Y')
    cylinder('Wheel black hub',.039,.031,(x,y*1.15,.18),rubber,o,col,'Y')
    shadow('Contact shadow below tire',(x,y*.86,.006),(.21,.15),o,col)
   for x in [-.56,.52]:ball('Marker light',(x,y*.97,1.105 if is_bus else .90),(.038,.023,.025),red,o,col)
  x=-.86 if is_bus else -.706
  for z in [.34,.39,.44]:cube('Front grille metal bar',(.018,.38,.021),(x,0,z),silver,o,col,.006)
  for y in [-.26,.26]:ball('Headlight lens',(x,y,.43),(.024,.065,.044),headlamp,o,col)
  if not is_bus:
   for x in [-.16,.23,.56]:
    # Steel hoops frame the translucent cylindrical tanker.
    pts=[(x,.365*math.cos(i*math.tau/48),.70+.365*math.sin(i*math.tau/48)) for i in range(49)]
    stroke('Painted tanker hoop',pts,.016,white,o,col)
   for y in [-.17,.17]:
    stroke('Tanker rear ladder rail',[(.64,y,.31),(.66,y,.93),(.61,y,1.06)],.022,silver,o,col)
   for j in range(6):stroke('Tanker rear ladder rung',[(.655,-.17,.39+j*.1),(.655,.17,.39+j*.1)],.017,silver,o,col)
  for child in o.children:
   if child.name.startswith(('Bus_LowerBody','Bus_Roof','Bus_Nose','Tanker_Cab')):bevel(child,.035)
 for i,(coll,par,win) in enumerate([(col,root,[(475,636)]),(K['SET_SKY_ASCENT'],O['ROOT_SKY_ASCENT'],[(1207,1425)])]):
  for g in range(6):
   x=(-1)**g*(.85+.49*g);y=3.7+g*.66;z=1.85+(g%3)*.57
   for j in range(4):
    o=ball('Layered sunlit cumulus',(x+(j-1.5)*.29,y+.12*j,z+.08*math.sin(j*2)),(.42,.31,.19+.08*rng.random()),cloud,par,coll);vis(o,win)
 for o in list(scene.objects):
  if o.name.startswith(('Bus_','Tanker_','School bus','Tanker side','Painted tanker','Front grille','Headlight lens','Wheel ','Marker light','Contact shadow below tire','Ochre highway','Asphalt with','Dashed highway','Highway guard','Verge guard','Bus cutaway')):
   vis(o,[(475,636)])
  if o.name.startswith(('Bus_GlassCab','Bus_Window_')):vis(o,[])
 for name,win in [('Bus_RisingGas',(480,545)),('Tanker_RisingGas',(540,625))]:
  o=O.get(name)
  if o:
   o.animation_data_clear();vis(o,[(475,636)])
   z=.19 if name.startswith('Bus') else .39
   for f,s in [(475,.001),(win[0],.001),(win[1],1),(636,1)]:
    o.scale.z=s;o.location.z=z+(.37 if name.startswith('Bus') else .30)*s;key(o,'scale',f);key(o,'location',f)
 for o in scene.objects:
  if o.name.startswith('Tanker_DrumShell'):
   for f,s in [(540,1),(585,1.015),(625,1.06),(636,1.06)]:o.scale.x=s;o.scale.y=s;key(o,'scale',f)
 sofa=O['LR_Sofa_Intact'];vis(sofa,[(1,225),(637,720)],True)
 col=K['SET_LIVING_ROOM'];root=O['ROOT_LIVING_ROOM']
 for i,child in enumerate(sofa.children):
  if child.name.startswith(('Sofa_Base','Sofa_Seat','Sofa_Arm','Sofa_Back')):bevel(child,.058)
  if child.name.startswith('Sofa_Leg'):
   o=shadow('Sofa foot contact',(*child.location[:2],.005),(.14,.14),root,col);vis(o,[(1,225),(637,720)])
 if O.get('LR_SofaContactShadow'):vis(O['LR_SofaContactShadow'],[])
 fabrics=[opaque('Frayed sofa fabric '+str(i),h) for i,h in enumerate(['ac5841','8c483b','d18159'])]
 timber=opaque('Splintered warm birch','9b6142');spring=opaque('Steel sofa springs','9cabae',.74)
 for o in list(scene.objects):
  if o.name.startswith('Shred_'):vis(o,[])
 def fling(o,f0,last,loc,vel,rot):
  vis(o,[(f0,last)])
  for f in list(range(f0,last,3))+[last]:
   t=(f-f0)/30
   o.location=(loc[0]+t*vel[0],loc[1]+t*vel[1],max(.045,loc[2]+vel[2]*t-1.9*t*t))
   o.rotation_euler=tuple(t*k for k in rot);key(o,'location',f);key(o,'rotation_euler',f)
 for j in range(20):
  x=rng.uniform(-.82,.82);loc=(x,.41,.32+rng.random()*.39)
  if j<6:o=cube('Flying frayed sofa cushion',(.21+rng.random()*.27,.23+rng.random()*.17,.12),loc,fabrics[j%3],root,col,.046)
  elif j<14:o=cube('Flying splintered frame plank',(.25+rng.random()*.31,.084,.042),loc,timber,root,col,.012)
  else:
   pts=[(.063*math.cos(i*math.tau/12),.063*math.sin(i*math.tau/12),i*.006) for i in range(49)]
   o=stroke('Flying coiled metal sofa spring',pts,.012,spring,root,col)
  fling(o,1009,1086,loc,((1 if x>0 else -1)*rng.uniform(.5,1.9),rng.uniform(-1.8,.6),rng.uniform(1.4,2.8)),[rng.uniform(-7,7) for _ in range(3)])
 col=K['SET_STRATOSPHERE'];root=O['ROOT_STRATOSPHERE']
 roof=O['ST_RoofSlope_L'].parent
 tiles=[opaque('Terracotta '+str(i),h) for i,h in enumerate(['a84932','c46343','b95b43','8a352b'])]
 for side in [-1,1]:
  for j in range(5):
   for k in range(5):
    x=side*(.36+.22*j);y=-.55+.43*k;z=.78-.48*abs(x)
    o=cube('Lapped terracotta roof tile',(.25,.47,.05),(x,y,z),tiles[(j+k)%4],roof,col,.025)
    if (j+k)%2==0 and j<4:
     fling(o,1590,1620,(x,y,z),(side*rng.uniform(1.2,3.4),rng.uniform(-2,2),rng.uniform(1.7,4.2)),[rng.uniform(-7,7) for _ in range(3)])
     # Keep these tiles attached before the explosion.
     vis(o,[(1585,1620)])
    else:vis(o,[(1585,1620)])
 for j in range(6):
  o=cube('Split roof rafter',(.60,.10,.11),(0,.1,.65),timber,roof,col,.015)
  fling(o,1590,1620,(rng.uniform(-.3,.3),-.55+.34*j,.67),(rng.uniform(-3,3),rng.uniform(-2,2),rng.uniform(2,4)),(3,-4,5))
 for o in O.values():
  if o.name.startswith('ST_MachCone_'):
   m=emission(o.name+' luminous thin shell','b5e5ff',1.4,.16);o.data.materials.clear();o.data.materials.append(m)
 if O.get('ST_LaserBeam'):vis(O['ST_LaserBeam'],[(1426,1584),(1621,1815)])
 if O.get('XR_WireframeSofa'):vis(O['XR_WireframeSofa'],[])
 for o in O.values():
  if o.name.startswith(('XR_ShockRing_','XR_GasSphere_9000L')):
   if 'GasSphere' in o.name:vis(o,[(385,474)])
   else:vis(o,[(811,900)])
 for o in list(scene.objects):
  if o.name.startswith(('XR_ShockRing_','XR_GasSphere_9000L')):
   m=emission(o.name+' thin FX skin','43fa6e',1.55,.19 if 'GasSphere' in o.name else .24);o.data.materials.clear();o.data.materials.append(m)
   if o.name.startswith('XR_ShockRing_'):
    # Use a narrow ring rather than an opaque floor disc.
    o.hide_render=True;vis(o,[])
    colx=K['SET_XRAY_GRID'];px=O['ROOT_XRAY_GRID']
    q=stroke('Radiating green shock ring',[(.48*math.cos(i*math.tau/72),.38+.48*math.sin(i*math.tau/72),.022) for i in range(73)],.016,m,px,colx);vis(q,[(811,900)])
    q.location.y=.38; q.data.transform(Matrix.Translation((0,-.38,0)))
    for f,t in [(811,.30),(831,1.25),(870,2.45),(900,3.4)]:q.scale=(t,t,1);key(q,'scale',f)
 star=emission('Small night stars','edf1ff',1.6)
 nr=O['ROOT_NEIGHBOR_ROOFTOP'];cn=K['SET_NEIGHBOR_ROOFTOP']
 for j in range(45):
  o=ball('Twinkling star',((rng.random()-.5)*16,7+rng.random()*6,1.6+rng.random()*7),(.015,)*3,star,nr,cn)
  vis(o,[(1975,2286)])
  for f in [1975,2030,2090,2150,2210,2286]:
   o.scale=(.008+rng.random()*.013,)*3;key(o,'scale',f)
 for name,pos,size in [('Rooftop water tank contact',(-1.35,1.65,.005),(.62,.63)),('Neighbor sole contact',(0,.33,.005),(.37,.25))]:
  o=shadow(name,pos,size,nr,cn);vis(o,[(1975,2286)])
def fire_and_earth(scene):
 O=bpy.data.objects;K=bpy.data.collections;rng=random.Random(37)
 col=K['SET_STRATOSPHERE'];met=O['ST_MeteorFire_Grp']
 for o in list(met.children):vis(o,[])
 core=emission('Meteor white-yellow core','ffecb0',4.4,.72)
 yellow=emission('Meteor gold plasma','ffbe37',3.7,.52)
 orange=emission('Meteor vermilion envelope','ff5322',2.7,.38)
 green=emission('Meteor methane center','58ff72',2.6,.45)
 hero=O['Hero_Root']
 for j,(mat,sc) in enumerate([(orange,(.43,.30,.75)),(yellow,(.31,.24,.58)),(core,(.21,.18,.30)),(green,(.13,.13,.38))]):
  o=ball('Layered meteor plasma',(.0,.22,-.12-j*.085),sc,mat,hero,col);vis(o,[(1816,1974)])
  for f in range(1816,1975,8):
   q=.87+rng.random()*.23;o.scale=tuple(s*q for s in sc);key(o,'scale',f)
 for j in range(24):
  o=ball('Meteor ember bead',(0,0,0),(.033,)*3,yellow if j%3 else orange,hero,col);vis(o,[(1816,1974)])
  for f in range(1816,1975,4):
   t=((f-1816+j*4)%65)/65;a=j*2.4
   o.location=(math.cos(a)*(.11+t*.72),.16+math.sin(a)*t*.39,-.22-t*1.7)
   o.scale=(.014+.043*(1-t),)*3;key(o,'location',f);key(o,'scale',f)
 # Extra ember streaks are carried by the same rooftop meteor that owns the moving lamp.
 met2=O['NR_MeteorStreak'];cn=K['SET_NEIGHBOR_ROOFTOP']
 for j in range(9):
  o=ball('Rooftop meteor ember',(-.22-j*.15,.05,.04+j*.055),(.065-j*.004,.023,.022),yellow,met2,cn);vis(o,[(1975,2286)])
 earth=O['OS_EarthSphere']
 mat=earth.data.materials[0];nt=mat.node_tree;n=nt.nodes;l=nt.links
 p=next(q for q in n if q.type=='BSDF_PRINCIPLED')
 p.inputs['Emission Strength'].default_value=.10
 tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=4.25;noise.inputs['Detail'].default_value=5;l.new(tc.outputs['Generated'],noise.inputs[0])
 r=n.new('ShaderNodeValToRGB')
 ramp=r.color_ramp;ramp.elements[0].position=.31;ramp.elements[0].color=(*rgb('114d9c'),1)
 ramp.elements[1].position=.70;ramp.elements[1].color=(*rgb('bdba76'),1)
 for f,c in [(.47,'277ac8'),(.53,'3a93bc'),(.55,'3b8154'),(.63,'668d50')]:ramp.elements.new(f).color=(*rgb(c),1)
 l.new(noise.outputs['Fac'],r.inputs[0])
 wind=n.new('ShaderNodeVectorMath');wind.operation='MULTIPLY';wind.inputs[1].default_value=(2,2,5);l.new(tc.outputs['Generated'],wind.inputs[0])
 clouds=n.new('ShaderNodeTexNoise');clouds.inputs['Scale'].default_value=7;clouds.inputs['Roughness'].default_value=.54;l.new(wind.outputs[0],clouds.inputs[0])
 cr=n.new('ShaderNodeMapRange');cr.inputs['From Min'].default_value=.56;cr.inputs['From Max'].default_value=.71;l.new(clouds.outputs['Fac'],cr.inputs[0])
 mix=n.new('ShaderNodeMixRGB');l.new(cr.outputs[0],mix.inputs[0]);l.new(r.outputs[0],mix.inputs[1]);mix.inputs[2].default_value=(*rgb('f8fcff'),1)
 l.new(mix.outputs[0],p.inputs['Base Color']);l.new(mix.outputs[0],p.inputs['Emission Color'])
 for o in O.values():
  if o.name.startswith('OS_Continent_'):vis(o,[])
 for name in ['OS_EarthAtmosphere','ST_CurvedEarth']:
  o=O.get(name)
  if not o:continue
  if name=='OS_EarthAtmosphere':
   m=emission('Fresnel Earth atmosphere','68d8ff',2.1,.34);o.data.materials.clear();o.data.materials.append(m)
   n=m.node_tree.nodes;l=m.node_tree.links
   w=n.new('ShaderNodeLayerWeight');q=n.new('ShaderNodeMath');q.operation='POWER';q.inputs[1].default_value=4;l.new(w.outputs['Facing'],q.inputs[0]);l.new(q.outputs[0],next(v for v in n if v.type=='MIX_SHADER').inputs[0])
  else:
   mm=mat.copy();o.data.materials.clear();o.data.materials.append(mm)
 for o in list(scene.objects):
  if ('Exhaust' in o.name or 'Puff' in o.name or 'Plume' in o.name) and o.name.startswith(('OS_','Hero_')):vis(o,[])
 puff=ball('Soft mint space exhaust',(0,.18,.30),(.10,.095,.15),emission('Soft mint methane','57ff86',1.25,.18),hero,K['SET_OUTER_SPACE'])
 vis(puff,[(2533,2715)])
 for f in range(2533,2716,7):
  q=.77+.18*math.sin((f-2533)*.24);puff.scale=(.08*q,.08*q,.13*q);key(puff,'scale',f)
def assets_and_acting(scene,envelope):
 O=bpy.data.objects
 for m in bpy.data.materials:
  if m.use_nodes and re.search(r'(Mat_.*(Head|Body|Neighbor|Thought|Bubble)|Mat_HUD)',m.name,re.I):
   cel_strength(m,1.12 if 'HUD' not in m.name else .96)
 # The short and ankle bend are redrawn in each seated image, leaving the torso alpha untouched.
 from io import BytesIO
 for o in [o for o in O.values() if o.name.startswith('Hero_Body_') and o.type=='MESH' and 'vascular' not in o.name.lower()]:
  if not o.data.materials:continue
  m=o.data.materials[0];node=next((n for n in m.node_tree.nodes if n.type=='TEX_IMAGE'),None)
  if not node or not node.image:continue
  img=node.image
  try:
   src=Image.open(BytesIO(img.packed_file.data) if img.packed_file else bpy.path.abspath(img.filepath)).convert('RGBA')
  except Exception:continue
  W,H=src.size;fac=W/1024
  d=ImageDraw.Draw(src);d.rectangle((0,int(937*H/1536),W,H),fill=(22,18,25,0))
  def pt(x,y):return (round(x*W/1024),round(y*H/1536))
  for s in [-1,1]:
   pts=[pt(512+s*53,904),pt(512+s*133,928),pt(512+s*156,961),pt(512+s*156,1101)]
   d.line(pts,fill=(22,18,25,255),width=max(2,round(20*fac)),joint='curve')
   x=512+s*156
   d.ellipse([pt(x-47,1080),pt(x+47,1132)],fill=(22,18,25,255))
  f=ART/(o.name.replace('.','_')+'_seated.png');src.save(f)
  node.image=bpy.data.images.load(str(f));node.image.pack()
 # Neighbor speech is sampled only in the two spoken lines.
 heads={k:next((o for o in O.values() if o.name.startswith('Neighbor_Head_'+k)),None) for k in ['pray_closed','pray_talk','one_eye_wish']}
 flags={k:[] for k in heads}
 for f in range(2116,2287):
  amp=envelope[min(f-1,len(envelope)-1)]
  k='pray_talk' if amp>.18 else 'pray_closed' if f<2176 else 'one_eye_wish'
  flags[k].append(f)
 for k,o in heads.items():
  if not o:continue
  spans=[]
  for f in flags[k]:
   if spans and spans[-1][1]==f-1:spans[-1][1]=f
   else:spans.append([f,f])
  vis(o,spans)
 for o in O.values():
  if o.name.startswith('CD_StampOverlay'):vis(o,[(2455,2532)])
  if o.name=='CD_RubberStamp3D':
   o.animation_data_clear();vis(o,[(2450,2480)],True)
   for f,p in [(2450,(0,-.30,.63)),(2454,(0,-.30,.22)),(2455,(0,-.30,.013)),(2465,(0,-.30,.013)),(2480,(.38,-.45,.78))]:
    o.location=p;o.rotation_euler.z=math.radians(-4.5);key(o,'location',f);key(o,'rotation_euler',f)
 for o in O.values():
  if o.name.startswith('HUD_Card_') or o.name.startswith('P2_HUD'):
   o.location.y=max(o.location.y,.44*abs(o.location.z))
 # Eliminate the flashcard frame of the meteor body so depth and fire are legible.
 for o in O.values():
  if 'Meteor' in o.name and o.name.startswith('Hero_Body'):
   o.rotation_euler.x=math.pi/2
def finish(scene):
 import json
 env=json.loads((OUT/'voice_env.json').read_text())
 retime();world_gradient(scene);compositor(scene);lighting(scene);decorate(scene);fire_and_earth(scene);assets_and_acting(scene,env)
 scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0
 scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.use_raytracing=False;scene.eevee.taa_render_samples=24
 scene.render.use_simplify=True;scene.render.simplify_subdivision=2;scene.render.simplify_subdivision_render=2
 scene.frame_start=1;scene.frame_end=2715;scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100
 scene.render.fps=30;scene.render.fps_base=1;scene.render.film_transparent=False
 scene['Overhaul']='Audio cue map, seated silhouettes, dimensional destruction and scene-specific lighting'
 scene.render.use_sequencer=False
 bpy.ops.file.pack_all()
 scene.frame_set(100)

def stroke(name,pts,r,m,par,col):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2
 sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,v in zip(sp.points,pts):p.co=(*v,1)
 o=bpy.data.objects.new(name,d);col.objects.link(o);o.parent=par;d.materials.append(m);return o
def shadow(name,loc,sc,par,col):
 m=bpy.data.materials.get('Soft painted contact shadow')
 if not m:
  m=emission('Soft painted contact shadow','17202a',1,.36);n=m.node_tree.nodes;l=m.node_tree.links
  t=n.new('ShaderNodeTexCoord');v=n.new('ShaderNodeVectorMath');v.operation='DISTANCE';v.inputs[1].default_value=(.5,.5,0);l.new(t.outputs['UV'],v.inputs[0])
  r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.40,)*3+(1,);r.color_ramp.elements[0].position=.11
  r.color_ramp.elements[1].color=(0,0,0,1);r.color_ramp.elements[1].position=.50;l.new(v.outputs['Value'],r.inputs[0]);l.new(r.outputs[0],next(x for x in n if x.type=='MIX_SHADER').inputs[0])
 bpy.ops.mesh.primitive_plane_add(size=2,location=loc);o=bpy.context.view_layer.objects.active;o.name=name;o.scale=(*sc,1);o.parent=par
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(m);return o


