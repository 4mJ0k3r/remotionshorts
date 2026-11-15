"""Dimensional classroom, washroom, and blue-grid studio sets."""
import bpy,bmesh,math,random
from mathutils import Vector,Matrix
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/washroom_experiment';ART=OUT/'assets'
V=Vector
def rgb(h):
 v=[int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)
class Stage:
 def __init__(self,scene): self.scene=scene;self.materials={}
 def mat(self,h,metal=0,rough=.55,em=0):
  k=(h,metal,rough,em)
  if k in self.materials:return self.materials[k]
  m=bpy.data.materials.new(h);m.use_nodes=True;m.diffuse_color=(*rgb(h),1)
  p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
  p.inputs['Base Color'].default_value=m.diffuse_color;p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
  p.inputs['Emission Color'].default_value=m.diffuse_color;p.inputs['Emission Strength'].default_value=em
  self.materials[k]=m;return m
 def link(self,name,data=None,p=None,xyz=(0,0,0)):
  o=bpy.data.objects.new(name,data);self.scene.collection.objects.link(o);o.parent=p;o.location=xyz;return o
 def mesh(self,name,bm,m,p,xyz):
  d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();d.update()
  if m:d.materials.append(m)
  return self.link(name,d,p,xyz)
 def batch(self,name,spec,m,p=None,bevel=0):
  bm=bmesh.new()
  for xyz,dim in spec:
   v=bmesh.ops.create_cube(bm,size=1)['verts']
   bmesh.ops.transform(bm,verts=v,matrix=Matrix.Translation(xyz)@Matrix.Diagonal((*dim,1)))
  o=self.mesh(name,bm,m,p,(0,0,0))
  if bevel:
   mod=o.modifiers.new('Edge highlights','BEVEL');mod.width=bevel;mod.segments=2
  return o
 def box(self,name,xyz,dim,m,p=None,bevel=.015):
  o=self.batch(name,[((0,0,0),dim)],m,p,bevel);o.location=xyz;return o
 def ball(self,name,xyz,sc,m,p=None):
  bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=18,v_segments=10,radius=1)
  o=self.mesh(name,bm,m,p,xyz);o.scale=sc
  for q in o.data.polygons:q.use_smooth=True
  return o
 def rod(self,name,a,b,r,m,p=None):
  a,b=V(a),V(b);delta=b-a
  bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=16,radius1=r,radius2=r,depth=delta.length)
  o=self.mesh(name,bm,m,p,(a+b)/2);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return o
 def curve(self,name,pts,r,m,p=None,loop=False):
  d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2
  sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
  for v,xyz in zip(sp.points,pts):v.co=(*xyz,1)
  sp.use_cyclic_u=loop;d.materials.append(m);return self.link(name,d,p)
 def light(self,name,kind,xyz,target,energy,h,p=None):
  d=bpy.data.lights.new(name,kind);d.energy=energy;d.color=rgb(h)
  o=self.link(name,d,p,xyz)
  if kind!='POINT':o.rotation_euler=(V(target)-V(xyz)).to_track_quat('-Z','Y').to_euler()
  if kind=='AREA':d.size=3
  if kind=='SUN':d.angle=math.radians(10)
  if kind=='POINT':d.shadow_soft_size=.22
  return o
 def label(self,name,txt,xyz,size,m,p=None):
  d=bpy.data.curves.new(name,'FONT');d.body=txt;d.size=size;d.align_x='CENTER';d.align_y='CENTER';d.extrude=.0006;d.materials.append(m)
  o=self.link(name,d,p,xyz);o.rotation_euler.x=math.pi/2;return o
 def tile_floor(self,name,rows,cols,step,org,colors,p):
  for k,h in enumerate(colors):
   spec=[((org[0]+i*step,org[1]+j*step,-.028),(step-.009,step-.009,.056)) for i in range(cols) for j in range(rows) if (i+j)%len(colors)==k]
   self.batch(name+' '+str(k),spec,self.mat(h,rough=.30),p)
 def door(self,name,x,y,hinge,leaf,wall,p,open_angle=0):
  height=2.1;w=.92
  self.batch(name+' frame',[((x-.055,y,1.09),(.11,.16,2.18)),((x+w+.052,y,1.09),(.106,.16,2.18)),((x+w/2,y,2.14),(w+.20,.16,.12))],wall,p,.016)
  d=self.link(name+' hinge',p=p,xyz=(x,y,.095));d.rotation_euler.z=open_angle
  self.box(name+' panel',(.46,0,1.0),(.91,.060,2),leaf,d)
  self.box(name+' inset',(.46,-.037,1.17),(.68,.018,1.39),leaf,d,.028)
  self.box(name+' handle plate',(.78,-.045,1.03),(.075,.025,.16),hinge,d)
  self.rod(name+' lever',(.78,-.075,1.04),(.66,-.075,1.04),.017,hinge,d)
  return d
def classroom(g):
 r=g.link('Classroom_Corridor_Set');m=g.mat;ink=m('263343');teal=m('538d84');wood=m('bf8150');legs=m('283849')
 g.tile_floor('Warm classroom pavers',12,12,.48,(-2.64,.15),['ccaf94','e2c4a4'],r)
 g.tile_floor('Glossy corridor checker',21,8,.48,(-1.68,5.91),['2d64a0','d1e8ee'],r)
 g.box('Classroom far plaster',(0,5.8,1.54),(5.8,.15,3.08),teal,r)
 g.box('Teaching board',(0,5.68,1.77),(3.7,.1,1.24),ink,r)
 g.box('Teal chalkboard',(0,5.61,1.77),(3.52,.042,1.08),m('205a54'),r)
 g.label('Classroom board lettering','HINDI   /   PERIOD  04',(0,5.58,1.81),.14,m('f1e4c9',em=.35),r)
 g.box('Classroom front wall',(0,-2.35,1.62),(5.8,.12,3.24),teal,r)
 g.box('Rear teaching board surround',(-.46,-2.24,1.78),(3.51,.13,1.25),ink,r)
 g.box('Rear teaching board',(-.46,-2.16,1.78),(3.37,.04,1.12),m('256c61'),r)
 for words,xyz in [('E=mc²',(-1.10,-2.128,2.06)),('BIO 101',(.42,-2.128,1.79))]:
  chalk=g.label('Board chalk formula',words,xyz,.19,m('f4f5d5',em=.4),r)
  chalk.rotation_euler.z=math.pi
 g.batch('Right window recessed masonry',[((2.82,-1.05,.48),(.19,2.36,.96)),((2.82,-1.05,2.96),(.19,2.36,.50)),((2.82,-2.25,1.62),(.19,.25,3.24)),((2.82,.17,1.62),(.19,.25,3.24))],teal,r)
 g.box('Sunlit sky beyond classroom window',(3.22,-1.05,1.92),(.06,2.15,1.66),m('b6ddff',rough=.22,em=.65),r)
 for y in [-2.14,-1.43,-.71,.04]:g.box('Recessed window vertical bar',(2.78,y,1.90),(.16,.065,1.87),ink,r)
 for z in [1.02,1.87,2.76]:g.box('Recessed window rail',(2.78,-1.05,z),(.16,2.23,.069),ink,r)
 g.light('Warm right window sunlight','AREA',(2.64,-.89,2.12),(0,.52,.54),380,'ffe0ac',r)
 for j in range(5):
  g.box('Chalk notes',(-.56+.45*(j%2),-2.130,1.50+.14*j),(1.17-.10*j,.008,.014),m('c9d8b0'),r,.003)
 for z in [.70,1.12,1.54]:
  g.box('Classroom bookshelf', (2.11,-2.05,z),(.93,.36,.055),wood,r)
  for j in range(6):
   g.box('Classroom shelf books',(1.76+.12*j,-2.07,z+.13),(.082,.24,.24),m(['e4ad6e','68a9c6','aa5e58'][j%3]),r)
 for y in [1.15,2.64,4.04]:
  for x in [-1.52,0,1.52]:
   g.box('Desk walnut worktop',(x,y,.77),(1.06,.55,.105),wood,r,.046)
   g.box('Bench padded top',(x,y-.64,.43),(.90,.33,.082),m('805138'),r,.039)
   g.batch('Desk and bench frames',[((x+dx,y+dy,z),(.056,.058,h)) for dx in [-.42,.42] for dy,z,h in [(-.18,.36,.72),(.19,.36,.72),(-.64,.20,.40)]],legs,r,.01)
   for i in range(2):
    o=g.box('Exercise book',(x+.16,y+.03+i*.08,.835+i*.012),(.24,.18,.018),m(['2256a0','d6bf55'][i]),r,.008);o.rotation_euler.z=.1*i
 for j in range(3):
  y=1.2+j*1.52
  for dy in [-.61,0,.61]:g.box('Real window mullion',(-2.78,y+dy,1.96),(.105,.068,1.6),ink,r)
  for z in [1.15,1.95,2.74]:g.box('Window horizontal mullion',(-2.78,y,z),(.108,1.28,.062),ink,r)
 g.batch('Classroom window-wall masonry',[((-2.87,2.9,.53),(.13,5.8,1.06)),((-2.87,2.9,2.93),(.13,5.8,.30))],teal,r)
 for side in [-1,1]:
  x=side*1.94
  g.box('Corridor colored plaster',(x,10.8,1.62),(.14,10,3.24),m('539b9f' if side<0 else '7aaca1'),r)
  for j in range(11):
   y=6.38+j*.74
   if side<0:
    g.box('School locker cabinet',(x+.22,y,1.10),(.42,.65,2.08),m(['28638c','4082a0'][j%2]),r,.036)
    for z in [.48,1.38]:g.box('Locker stamped door',(x+.45,y,z),(.026,.56,.82),m('629cb3'),r,.021)
    g.box('Locker latch',(x+.47,y-.17,1.25),(.023,.052,.18),ink,r)
   elif j%2==0:
    g.box('Hall art frame',(x-.091,y,1.82),(.05,.55,.63),ink,r)
    g.box('Hall art',(x-.122,y,1.82),(.022,.47,.54),m(['ddad68','99ceea','d29393'][j%3]),r)
 g.box('Hall end',(0,15.8,1.58),(4,.15,3.2),m('3c697c'),r)
 g.door('Hall classroom door',-.48,15.69,m('adbac9',.6),m('588ebd'),ink,r)
 g.light('Classroom diagonal sun','SUN',(-5,1,5),(0,2,0),5,'fff2cd',r)
 g.light('Classroom bounce','AREA',(2,-2,3),(0,1.4,1),115,'b0d5ff',r)
 for y in [7,10.5,14]:g.light('Corridor ceiling bounce','AREA',(0,y,3),(0,y,0),95,'ccedff',r)
 return r
def washroom(g):
 r=g.link('Washroom_Set',xyz=(30,0,0));m=g.mat
 azure=m('287fbd',rough=.28);dark=m('183454');cer=m('f5f6ea',rough=.21);metal=m('9eb8c7',.58,.24)
 g.box('White grout bed',(0,3.0,-.06),(5.5,7,.09),m('dcecf1'),r)
 g.tile_floor('Washroom azure ceramic',14,11,.48,(-2.4,.05),['327dac','418ec0','2d70a3'],r)
 for x in [-2.58,2.58]:
  g.box('Slate tile backing',(x,3.12,1.59),(.10,6.5,3.2),m('34495b'),r)
  for j in range(3):
   spec=[((x-math.copysign(.07,x),i*.49,.17+k*.30),(.045,.476,.286)) for i in range(14) for k in range(10) if (i+2*k)%3==j]
   g.batch('Glazed staggered slate tile',spec,m(['5b7280','526878','677c86'][j],rough=.38),r)
 g.box('Stall back wall',(0,6.25,1.55),(5.2,.15,3.10),m('566b79'),r)
 for i in range(3):
  x=-1.96+1.38*i;y=4.32
  g.box('Cabin partition',(x,y+.63,1.12),(.085,1.40,1.99),azure,r)
  g.box('Cabin frame rail',(x+.58,y,2.17),(1.27,.12,.07),dark,r)
  g.door(f'Cabin_{i+1}',x+.115,y,metal,azure,dark,r,0 if i<2 else math.radians(25))
  g.label('Stall number',f'0{i+1}',(x+.57,y-.105,2.31),.145,m('a9e9ff',em=.55),r)
 g.box('Last cabin outer partition',(2.30,4.98,1.15),(.085,1.49,2.12),azure,r)
 for y in [1.3,2.23,3.16]:
  g.box('Floating ceramic sink',(-2.21,y,.84),(.58,.68,.20),cer,r,.075)
  g.ball('Blue basin recess',(-2.10,y,.949),(.19,.21,.010),m('7dacc2',rough=.16),r)
  g.curve('Tap neck',[(-2.40,y,.96),(-2.40,y,1.11),(-2.33,y,1.16),(-2.25,y,1.12)],.019,metal,r)
  g.box('Framed sink mirror',(-2.49,y,1.64),(.049,.65,.89),dark,r)
  g.box('Mirror glass',(-2.456,y,1.64),(.02,.59,.83),m('80adb9',.42,.18),r)
 g.batch('Entrance wall around door',[((-1.45,.05,1.56),(1.6,.13,3.12)),((1.45,.05,1.56),(1.6,.13,3.12)),((0,.05,2.63),(1.3,.13,.9))],m('548e96'),r)
 d=g.door('Washroom entry',-.47,.05,metal,m('477bb3'),dark,r)
 for y in [1.02,3.20,5.52]:
  g.box('Milk glass overhead diffuser',(0,y,2.99),(1.47,.39,.065),m('d7efff',em=.55),r)
  g.light('Warm-cool washroom ceiling','AREA',(0,y,2.94),(0,y,0),125,'c3e3ff',r)
 gl=g.light('Cabin 3 violet interference','POINT',(1.43,4.52,1.15),(0,0,0),250,'f25cff',r)
 return r,d,gl
def office(g):
 r=g.link('Blue_Grid_Office_Set',xyz=(60,0,0));m=g.mat;black=m('151e33',.22);blue=m('174b9f',rough=.37)
 g.box('Blue stage foundation',(0,3,-.09),(42,42,.15),m('7aa8ff'),r)
 spec=[((i*.48,3,.003),(.010,42,.008)) for i in range(-42,43)]
 spec.extend(((0,i*.48,.003),(42,.010,.008)) for i in range(-38,51))
 g.batch('Periwinkle perspective grid',spec,m('dbeafe',em=.52),r)
 grout=m('c9d8e5');slates=['2b3648','34435a','394b62'];panel=m('1d4ed8',rough=.35)
 for side in [-1,1]:
  x=side*1.83
  g.box('Stall side grout wall',(x,.65,1.53),(.10,2.36,3.07),grout,r)
  for k,c in enumerate(slates):
   g.batch('Stall side slate ceramic',[((x-side*.057,-.42+j*.38,.18+i*.34),(.036,.366,.327)) for i in range(9) for j in range(7) if (i+j)%3==k],m(c,rough=.38),r,.004)
  g.box('Cobalt stall partition',(side*1.58,.91,1.17),(.075,1.29,2.10),panel,r,.035)
  g.box('Stainless top bracing rail',(side*1.58,.91,2.25),(.105,1.36,.062),m('9aaec5',.63),r)
 g.box('Cabin rear white grout',(0,1.82,1.54),(3.72,.10,3.10),grout,r)
 for k,c in enumerate(slates):
  g.batch('Rear slate tile grid',[((-1.66+j*.37,1.759,.17+i*.34),(.355,.044,.326)) for i in range(9) for j in range(10) if (i+j)%3==k],m(c,rough=.35),r,.004)
 steel=m('aebfd1',.58);porcelain=m('fffcf3',rough=.23)
 g.box('Cabin door latch backing',(-1.526,.35,1.26),(.042,.18,.12),steel,r)
 g.rod('Cabin door latch',(-1.495,.29,1.26),(-1.495,.42,1.26),.018,steel,r)
 g.label('Cabin number plaque','03',(-.23,1.719,2.58),.24,m('d8eeff',em=.8),r)
 tx,ty=1.01,1.35
 g.box('Porcelain flush tank',(tx,ty+.20,.88),(.42,.19,.49),porcelain,r,.075)
 g.box('Tank lid',(tx,ty+.20,1.15),(.45,.21,.053),porcelain,r,.029)
 g.ball('Toilet pedestal',(tx,ty-.08,.21),(.15,.19,.22),porcelain,r)
 g.ball('Porcelain bowl',(tx,ty-.16,.37),(.245,.31,.17),porcelain,r)
 g.ball('Dark ceramic basin recess',(tx,ty-.16,.512),(.16,.211,.022),m('859fb3',rough=.26),r)
 g.curve('Toilet seat rim',[(tx+.202*math.cos(i*math.tau/64),ty-.16+.25*math.sin(i*math.tau/64),.529) for i in range(64)],.031,porcelain,r,True)
 g.box('Side paper dispenser',(-1.506,1.31,1.10),(.16,.24,.20),steel,r,.045)
 g.box('Exposed toilet paper tab',(-1.425,1.30,1.02),(.025,.12,.16),porcelain,r)
 g.box('Cabin ceiling diffuser',(0,1.12,2.95),(1.34,.37,.073),m('d8f1ff',em=1.05),r)
 g.light('Cabin violet bounce','POINT',(-1.19,1.30,1.74),(0,0,0),52,'b56cff',r)
 g.light('Cabin cyan bounce','POINT',(1.26,1.39,1.80),(0,0,0),46,'5ee9ff',r)
 g.box('Walnut table top',(-.43,.12,.752),(1.20,.90,.056),m('754529'),r,.034)
 for x in [-.96,.09]:
  for y in [-.27,.51]:g.box('Square black table leg',(x,y,.361),(.062,.063,.722),black,r)
 def chair(name,xyz,angle):
  o=g.link(name,p=r,xyz=xyz);o.rotation_euler.z=angle
  for j in range(5):
   a=j*math.tau/5;end=(.30*math.cos(a),.30*math.sin(a),.052)
   g.rod('Five-star chair spoke',(0,0,.10),end,.023,black,o)
   g.ball('Chair caster',end,(.045,.041,.045),black,o)
  g.rod('Swivel gas cylinder',(0,0,.08),(0,0,.39),.039,black,o)
  g.box('Blue office cushion',(0,0,.425),(.49,.44,.115),blue,o,.052)
  g.rod('Steel backrest mount',(0,.15,.38),(0,.22,.68),.036,black,o)
  g.box('Curved charcoal backrest',(0,.205,.745),(.45,.105,.54),black,o,.072)
  for x in [-.265,.265]:
   g.rod('Chair arm mount',(x,0,.45),(x,0,.635),.026,black,o)
   g.box('Chair arm pad',(x,-.01,.638),(.07,.32,.046),black,o,.021)
  return o
 chair('Upper office chair on tabletop',(-.53,.20,.780),math.radians(44))
 chair('Lower office chair on grid',(.66,-.015,0),math.radians(-50))
 pot=(.25,-.64);g.rod('Gold fern planter',(*pot,.008),(*pot,.235),.10,m('cc9b3d',.51,.31),r)
 g.ball('Planter soil',(*pot,.235),(.093,.093,.014),m('3e2c29'),r)
 for i in range(9):
  a=i*math.tau/9;pts=[(*pot,.23)]
  for j in range(1,8):
   t=j/7;x=pot[0]+math.cos(a)*.21*t;y=pot[1]+math.sin(a)*.21*t;z=.23+.28*math.sin(t*1.8)
   pts.append((x,y,z))
   for side in [-1,1]:
    o=g.ball('Fern leaflet',(x+side*.023*math.sin(a),y-side*.023*math.cos(a),z),(.041,.014,.012),m(['357449','4a9550','65ac61'][j%3]),r);o.rotation_euler.z=a+side*.69
  g.curve('Fern frond',pts,.005,m('407d4e'),r)
 g.light('Office daylight key','AREA',(-3,-2,6),(0,0,1),480,'fff0cc',r)
 g.light('Blue studio fill','AREA',(4,1,3),(0,0,1),310,'b3d5ff',r)
 return r
