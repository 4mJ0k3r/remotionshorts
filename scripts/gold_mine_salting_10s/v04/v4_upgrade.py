# Apply on this NEW V4 scene only. Earlier delivered sources stay untouched.
O=bpy.data.objects
for name in ['Miner physical hat brim','Buddy black beanie cuff','Buddy yellow cuff stripe']:
 O[name].rotation_euler.x=math.radians(5);O[name].visible_shadow=True
for name in ['Miner pinched hat crown','Buddy beanie crown']:O[name].visible_shadow=True
if O.get('Sweater neck rib'):O['Sweater neck rib'].data.materials[0]=teal
# Focused aim pupils/lids, plus a distinct closed/consonant mouth for Buddy.
for side in [-1,1]:
 x=side*.108
 oval('Miner'+(' L aim pupil' if side<0 else ' R aim pupil'),x,.026,.025,.012,BLACK,O['Miner head pivot'])
 faceline('Miner'+(' L aim lid' if side<0 else ' R aim lid'),[(x-.033,.040),(x,.038),(x+.033,.036)],.005,BLACK,O['Miner head pivot'])
# Feather cone opacity by the actual viewing incidence of its side surface.
nt=coneMat.node_tree;n=nt.nodes;l=nt.links;mix=next(x for x in n if x.type=='MIX_SHADER')
g=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
l.new(g.outputs['Normal'],dot.inputs[0]);l.new(g.outputs['Incoming'],dot.inputs[1])
ab=n.new('ShaderNodeMath');ab.operation='ABSOLUTE';l.new(dot.outputs['Value'],ab.inputs[0])
power=n.new('ShaderNodeMath');power.operation='POWER';power.inputs[1].default_value=1.5;l.new(ab.outputs[0],power.inputs[0])
alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';alpha.inputs[1].default_value=.035;l.new(power.outputs[0],alpha.inputs[0]);l.new(alpha.outputs[0],mix.inputs[0])
# Angular gravel clusters, keeping central ties clear. No spherical mud balls.
for o in list(S.objects):
 if o.name.startswith('Loose ochre shale'):bpy.data.objects.remove(o,do_unlink=True)
random.seed(4041899)
for side in [-1,1]:
 for y in [-2.5,-.8,1.2,2.6,4.1,5.6]:
  x=side*random.uniform(1.75,2.65)
  for j in range(5):
   bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1)
   o=bpy.context.object;o.name='Angular gravel cluster';o.location=(x+random.uniform(-.18,.18),y+random.uniform(-.22,.22),.035)
   scale=(random.uniform(.025,.08),random.uniform(.035,.11),random.uniform(.02,.055))
   for v in o.data.vertices:v.co=V(tuple(v.co[k]*scale[k]*random.uniform(.83,1.15) for k in range(3)))
   o.data.materials.append(rock);o.rotation_euler.z=random.random()*math.tau
# Supply corner is grouped and moved closer behind Buddy, preserving its dress.
corner=obj('Buddy dressed supply corner');corner.location=(-1.6,3.65,0)
prefixes=('Supply crate','Crate upright batten','Crate plank joint','CANDLES /','Tin supply cup')
roots=[o for o in list(S.objects) if o.parent is None and (o.name.startswith(prefixes) or o.name in ['Blue kettle assembly','Red oil lantern','Lantern practical'])]
bpy.context.view_layer.update()
for o in roots:
 mw=o.matrix_world.copy();o.parent=corner;o.matrix_world=mw
corner.location=(-1.10,3.95,.08);corner.scale=(.72,.8,1)
# Proper cylindrical/elliptical wood-grip surface and an explicit closing anchor.
old=O['Shotgun wrist grip']
for child in list(old.children_recursive):bpy.data.objects.remove(child,do_unlink=True)
bpy.data.objects.remove(old,do_unlink=True)
grip=sphere('Shotgun wrist grip',(0,-.13,-.075),(.032,.065,.060),wood,gun,seg=24,rings=12,outline=.0025)
stock=O['Shotgun shaped walnut stock']
for child in list(stock.children_recursive):bpy.data.objects.remove(child,do_unlink=True)
bpy.data.objects.remove(stock,do_unlink=True)
sv=[];sf=[];profile=[(-.47,.040,.065,-.035),(-.36,.047,.070,-.035),(-.27,.040,.055,-.035),(-.24,.024,.030,-.015),(-.18,.016,.020,-.015),(-.10,.018,.020,-.015)]
for y,rx,rz,zc in profile:
 for j in range(32):
  a=j*math.tau/32;sv.append((rx*math.cos(a),y,zc+rz*math.sin(a)))
for k in range(len(profile)-1):
 for j in range(32):a=k*32+j;b=k*32+(j+1)%32;sf.append((a,b,b+32,a+32))
sf += [tuple(reversed(range(32))),tuple(range(len(sv)-32,len(sv)))]
stock=mesh('Shotgun shaped walnut stock',sv,sf,wood,gun,outline=.0025);stock['collision']=True;grip['collision']=True
closeGrip=obj('Shotgun closing wood surface grip',parent=gun);closeGrip.location=(.033,-.13,-.075)
# Brass shell has a true rolled rim, primer and crimp seams.
primer=look.metal('Shell primer steel','#BDB9AB',.6,.32)
cylinder('Shell rolled brass rim',(0,0,-.070),(0,0,-.061),.030,gold,shell,verts=32,outline=.0015)
cylinder('Shell recessed primer',(0,0,-.071),(0,0,-.0695),.010,primer,shell,verts=20)
for j in range(6):
 a=j*math.tau/6
 line('Shell top crimp seam',[(.006*math.cos(a),.006*math.sin(a),.078),(.019*math.cos(a),.019*math.sin(a),.067)],.0012,wood,shell)
# Wide, lobe-shaped hot gas burst rather than the old stiff spear.
for o in list(flash.children_recursive):bpy.data.objects.remove(o,do_unlink=True)
for label,mat,factor in [('Broad orange muzzle fire',orangeFire,1),('Bright golden muzzle core',hot,.56)]:
 vv=[];ff=[];nr=18
 for y,r in [(0,.025),(.08,.13),(.22,.145),(.38,.08),(.52,.004)]:
  for j in range(nr):
   a=j*math.tau/nr;rr=r*(1+.22*math.sin(5*a+y*16)+.10*math.cos(3*a-y*11))*factor
   vv.append((rr*math.cos(a),y*(.9 if factor<1 else 1),rr*math.sin(a)))
 for k in range(4):
  for j in range(nr):a=k*nr+j;b=k*nr+(j+1)%nr;ff.append((a,b,b+nr,a+nr))
 o=mesh(label,vv,ff,mat,flash);look.mark_role(o,'streak')
# Deepen the cavity, cutting the solid rock backing rather than painting a disc.
rim=O['Jagged recessed crater rim'];core=O['Recessed dark crater core']
for v in rim.data.vertices:
 v.co.x*=1.12;v.co.z*=1.12
 if v.co.y>0:v.co.y=.16
for v in core.data.vertices:v.co.y=.27;v.co.x*=1.08;v.co.z*=1.08
ring=[V(v.co) for v in rim.data.vertices[:19]]
cv=[(.55+p.x*.72,y,1.6+p.z*.72) for y in [4.65,5.6] for p in ring]
cf=[(j,(j+1)%19,(j+1)%19+19,j+19) for j in range(19)]+[tuple(reversed(range(19))),tuple(range(19,38))]
cutter=mesh('Temporary crater cavity cutter',cv,cf,scar,smooth=False)
back=O['Strike wall'];mod=back.modifiers.new('Actual recessed strike cavity','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
bpy.context.view_layer.objects.active=back;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
for v in O['Unbroken strike surface'].data.vertices:
 v.co.x=.55+(v.co.x-.55)*1.17;v.co.z=1.6+(v.co.z-1.6)*1.17
for o in [o for o in S.objects if o.name.startswith('Persistent embedded gold')]:
 o.location.y=.12;o['deposit_rest']=list(o.location)
for i in range(9):
 a=i*2.39996;p=ring[(i*2)%19]
 o=sphere('Broken crater edge chip',p,(.027,.025,.033),rock,impact,seg=7,rings=4)
 for face in o.data.polygons:face.use_smooth=False
 line('Crater radial hairline',[(p.x,-.045,p.z),(p.x*1.3,-.04,p.z*1.3),((p.x+.025*math.sin(a))*1.55,-.025,p.z*1.55)],.0012,scar,impact)
# Candle wax lip and drips; halos follow flame visibility so closing stays clean.
wax=look.metal('Warm candle wax lip','#F4D8B4',0,.75)
lip=loft('Candle curled wax lip',[(0,.037,.037),(.012,.044,.044),(.023,.034,.034)],wax,n=24,outline=.0015);lip.location=(.99,4.51,1.91)
for dx in [-.018,.022]:line('Soft candle wax drip',[(.99+dx,4.473,1.93),(.99+dx*.8,4.471,1.88),(.99+dx*.7,4.475,1.84)],.004,wax)
haloMat=coneMat.copy();haloMat.name='Soft amber candle halo';nt=haloMat.node_tree
for link in list(nt.links):
 if link.to_node.type=='MIX_SHADER' and link.to_socket==link.to_node.inputs[0]:nt.links.remove(link)
next(n for n in nt.nodes if n.type=='MIX_SHADER').inputs[0].default_value=.035
next(n for n in nt.nodes if n.type=='EMISSION').inputs[0].default_value=look.rgba('#FF8E25')
for i,scale in enumerate([(.065,.05,.105),(.10,.07,.15)]):
 mat=haloMat if i==0 else haloMat.copy()
 if i:next(n for n in mat.node_tree.nodes if n.type=='MIX_SHADER').inputs[0].default_value=.012
 o=sphere('Candle warm glow halo',(0,0,0),scale,mat,O['Candle amber flame'],seg=20,rings=12);look.mark_role(o,'wisp')
S['cast_style']='Clean inked cel cast with calibrated interior light wrap and real hat occlusion; V3 stage retained'
for o in S.objects:
 if ' aim pupil' in o.name or ' aim lid' in o.name:o.visible_shadow=False
for i in range(6):
 o=sphere('Blast drifting smoke '+str(i),(0,0,0),(.10,.16,.09),smokeMat,seg=16,rings=8);look.mark_role(o,'smoke')
for o in S.objects:
 if o.type=='FONT':o.visible_shadow=False
for i in range(8):
 parent=O['Persistent embedded gold '+str(i*2)]
 for axis in [0,2]:
  pts=[(0,-.010,0),(0,-.010,0)];pts[0]=list(pts[0]);pts[1]=list(pts[1]);pts[0][axis]=-.006;pts[1][axis]=.006
  o=line('Embedded gold sparkle '+str(i)+' '+str(axis),pts,.001,goldglow,parent);look.mark_role(o,'streak')
