import bpy,math,sys,json,hashlib,random
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v7';s=bpy.context.scene;O=bpy.data.objects
bpy.app.handlers.frame_change_post.clear()
sys.path.insert(0,str(R/'scripts/washroom_experiment'));from sets import rgb

def town_hash():
 prefixes=('Downloaded Western saloon','Quaternius','Porch timber','Porch railing','V5 layered cloud','Red sandstone','Mesa horizontal','Dusty Main Street','GN sidewalk','Grass instance','Painted Western sign','Sign ')
 data=[]
 for o in sorted([o for o in s.objects if o.name.startswith(prefixes)],key=lambda x:x.name):
  geo=([list(v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons]) if o.type=='MESH' else o.type
  data.append((o.name,[list(row) for row in o.matrix_world],geo))
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
before=town_hash()
# Only old actor assemblies and their obsolete FX are removed. Imported town is retained.
keep={'Challenger_revolver','Eddie_pearl_revolver','Copper_bullet','challenger sole contact','challenger sole contact.001','eddie sole contact','eddie sole contact.001'}
remove=[]
for o in list(s.objects):
 if o.name in keep:continue
 if o.name.lower().startswith(('challenger','eddie','grip finger','v5 challenger','v5 eddie','v6 challenger','v6 eddie','temple socket','foreground shoulder','muzzle','holster stitched','v4 curved grip')):remove.append(o)
for o in remove:
 for child in list(o.children_recursive):
  if child not in remove and child.name not in keep:remove.append(child)
for o in remove:
 if o.name in O:bpy.data.objects.remove(o,do_unlink=True)
# Existing downloaded metallic guns are preserved, re-beveled, and no longer crease-wire outlined.
for name in ['Challenger_revolver','Eddie_pearl_revolver']:
 o=O[name];o['set_ink']=False;o.constraints.clear()
 for m in list(o.modifiers):o.modifiers.remove(m)
 for child in list(o.children_recursive):bpy.data.objects.remove(child,do_unlink=True)

def link(name,mesh=None,parent=None):
 o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);o.parent=parent;return o

def shader(name,color,metal=0,rough=.55,cel=True):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();l=nt.links;out=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfPrincipled');base=(*rgb(color),1);bs.inputs['Base Color'].default_value=base;bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 if cel:
  diff=nt.nodes.new('ShaderNodeBsdfDiffuse');diff.inputs[0].default_value=(1,1,1,1);st=nt.nodes.new('ShaderNodeShaderToRGB');l.new(diff.outputs[0],st.inputs[0]);bw=nt.nodes.new('ShaderNodeRGBToBW');l.new(st.outputs[0],bw.inputs[0]);gain=nt.nodes.new('ShaderNodeMath');gain.operation='MULTIPLY';gain.inputs[1].default_value=.62;l.new(bw.outputs[0],gain.inputs[0]);ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.name='Three soft cel light stops';ramp.color_ramp.interpolation='EASE'
  ramp.color_ramp.elements[0].position=.09;ramp.color_ramp.elements[0].color=(.44,.53,.71,1);ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=(1,.95,.82,1);mid=ramp.color_ramp.elements.new(.42);mid.color=(.81,.83,.87,1);l.new(gain.outputs[0],ramp.inputs[0]);mult=nt.nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;mult.inputs[1].default_value=base;l.new(ramp.outputs[0],mult.inputs[2]);em=nt.nodes.new('ShaderNodeEmission');l.new(mult.outputs[0],em.inputs[0]);em.inputs[1].default_value=1.15;mix=nt.nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=.12;l.new(em.outputs[0],mix.inputs[1]);l.new(bs.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0]);m['light_responsive_cel']=True
 else:l.new(bs.outputs[0],out.inputs[0])
 return m
ink=bpy.data.materials.new('V7 thin warm ink');ink.use_nodes=True;nt=ink.node_tree;nt.nodes.clear();e=nt.nodes.new('ShaderNodeEmission');e.inputs[0].default_value=(*rgb('352329'),1);out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(e.outputs[0],out.inputs[0]);ink.use_backface_culling=True;ink.use_backface_culling_shadow=True
cream=shader('V7 light responsive cream','FDFAF2');black=shader('V7 matte limb ink','352329',rough=.85);red=shader('V7 scarlet shirt','A72C39');teal=shader('V7 turquoise shirt','259F98');brown=shader('V7 warm leather','97633A');leather=shader('V7 stitched holster leather','302D38');gold=shader('V7 gold metal','D5A440',.8,.23,False);silver=shader('V7 silver metal','C3D3DF',.85,.2,False);steel=shader('V7 dark gunmetal','303643',.80,.22,False);pearl=shader('V7 pearl ivory','EFE8D5',0,.33,True);hatTan=shader('V7 tan felt hat','BC9665');hatBlack=shader('V7 black felt hat','25232C');band=shader('V7 dark hatband','543C2E');stripe=shader('V7 shirt pale stripes','F29D75');strawmat=shader('V7 golden straw','DAC16B');blue=shader('V7 sky sweat','61C9F8',.1,.2,False)
# Thin inverted hulls use real surface normals, with culling: no inflated capsule joints.
def outline(o,width=.006):
 if o.type!='MESH':return
 o.data.update();me=o.data.copy();me.name=o.name+' inverted hull';norm=[v.normal.copy() for v in o.data.vertices]
 for v,n in zip(me.vertices,norm):
  w=.0258*(1+.4*math.cos(math.atan2(-v.co.z,v.co.x)-2.35)) if 'skull' in o.name else width
  v.co+=n*w
 for p in me.polygons:p.flip()
 me.materials.clear();me.materials.append(ink);h=link(o.name+' ink',me,o);h['v7_outline']=True;return h

def mesh(name,verts,faces,mat,parent=None,inkwidth=.010,smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(mat);me.update()
 if inkwidth and len(faces)>2:
  import bmesh
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
 o=link(name,me,parent)
 for p in me.polygons:p.use_smooth=smooth
 if inkwidth:outline(o,inkwidth)
 return o

def sphere(name,xyz,scale,mat,parent=None,segments=32,rings=16,inkwidth=.006):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1);o=bpy.context.object;o.name=name
 for v in o.data.vertices:v.co=V((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2]))
 o.parent=parent;o.location=xyz;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 if inkwidth:outline(o,inkwidth)
 return o

def cube(name,xyz,scale,mat,parent=None,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name
 for v in o.data.vertices:v.co=V((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2]))
 o.parent=parent;o.location=xyz;o.data.materials.append(mat)
 mod=o.modifiers.new('Clean rounded edge','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in o.data.polygons:p.use_smooth=True
 outline(o,.004);return o

def tube(name,points,radius,mat,parent=None,inkwidth=0):
 # One continuous swept mesh, 8 radial samples; no separate capsule ends or joint rings.
 vs=[];faces=[]
 for i,p in enumerate(points):
  p=V(p);t=V(points[min(i+1,len(points)-1)])-V(points[max(i-1,0)]);t.normalize();axis=t.cross(V((0,1,0)))
  if axis.length<.01:axis=t.cross(V((1,0,0)))
  axis.normalize();other=t.cross(axis).normalized();r=radius*(1-(.42 if name.endswith(' leg') else .17)*i/max(1,len(points)-1))
  for j in range(8):a=j*math.tau/8;vs.append(p+r*(math.cos(a)*axis+math.sin(a)*other))
 for i in range(len(points)-1):
  for j in range(8):a=i*8+j;b=i*8+(j+1)%8;faces.append((a,b,b+8,a+8))
 faces+=[tuple(reversed(range(8))),tuple(range((len(points)-1)*8,len(points)*8))]
 return mesh(name,vs,faces,mat,parent,inkwidth)

def curve(name,pts,radius,mat,parent=None):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=radius;cu.bevel_resolution=1;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,v in zip(sp.points,pts):p.co=(*v,1)
 o=link(name,cu,parent);cu.materials.append(mat);return o

def loft(name,rings,mat,parent=None,n=32):
 vs=[];fs=[]
 for z,rx,ry in rings:
  for j in range(n):a=j*math.tau/n;vs.append((rx*math.cos(a),ry*math.sin(a),z))
 for i in range(len(rings)-1):
  for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 fs.append(tuple(reversed(range(n))))
 if 'crown' in name:
  center=len(vs);vs.append((0,0,rings[-1][0]));base=(len(rings)-1)*n;fs.extend([(base+j,base+(j+1)%n,center) for j in range(n)])
 else:fs.append(tuple(range((len(rings)-1)*n,len(rings)*n)))
 return mesh(name,vs,fs,mat,parent,0 if name in ['V7 amber fire','V7 yellow core'] else .010)

def rough(a):return 1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9)
def facepoint(x,z,r=.363,offset=.004):
 radius=r*rough(math.atan2(-z,x));return (x,-.29*math.sqrt(max(.025,1-(x*x+z*z)/(radius*radius)))-offset,z)
def patch(name,coords,mat,parent,offset=.004):
 cx=sum(x for x,z in coords)/len(coords);cz=sum(z for x,z in coords)/len(coords);triangles=[((cx,cz),coords[i],coords[(i+1)%len(coords)]) for i in range(len(coords))]
 for depth in range(2):
  sub=[]
  for a,b,c in triangles:
   ab=((a[0]+b[0])/2,(a[1]+b[1])/2);bc=((b[0]+c[0])/2,(b[1]+c[1])/2);ca=((c[0]+a[0])/2,(c[1]+a[1])/2);sub.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
  triangles=sub
 vs=[];fs=[];lookup={}
 for tri in triangles:
  face=[]
  for x,z in tri:
   key=(round(x,8),round(z,8))
   if key not in lookup:lookup[key]=len(vs);vs.append(facepoint(x,z,offset=offset))
   face.append(lookup[key])
  fs.append(tuple(face))
 return mesh(name,vs,fs,mat,parent,0,True)
def oval(name,x,z,rx,rz,mat,parent):return patch(name,[(x+rx*math.cos(i*math.tau/24),z+rz*math.sin(i*math.tau/24)) for i in range(24)],mat,parent,.006)
def faceline(name,coords,radius,parent,mat=black):return curve(name,[facepoint(x,z,offset=.009) for x,z in coords],radius,mat,parent)
def roundrect(x,z,w,h,r=.02):
 pts=[]
 for cx,cz,start in [(x+w/2-r,z+h/2-r,0),(x-w/2+r,z+h/2-r,90),(x-w/2+r,z-h/2+r,180),(x+w/2-r,z-h/2+r,270)]:
  for i in range(6):a=math.radians(start+i*90/5);pts.append((cx+r*math.cos(a),cz+r*math.sin(a)))
 return pts

for who in ['challenger','eddie']:
 pre='V7 '+who+' ';root=link(pre+'root');torso=link(pre+'torso',parent=root);head=link(pre+'head pivot',parent=torso);head.location=(0,0,1.92)
 skull=sphere(pre+'rough skull',(0,0,0),(.363,.29,.363),cream,head,64,24,0)
 for v in skull.data.vertices:
  a=math.atan2(-v.co.z,v.co.x);rr=rough(a);v.co.x*=rr;v.co.z*=rr
 outline(skull,.0258)
 # Smooth spherical skin, all creases/features independently conformed.
 body=loft(pre+'tailored shirt',[(.88,.20,.11),(.91,.25,.14),(.98,.27,.15),(1.40,.315,.145),(1.49,.31,.14),(1.56,.25,.105),(1.60,.12,.085)],red if who=='challenger' else teal,torso)
 sphere(pre+'neck',(0,0,1.59),(.095,.09,.15),cream,torso,20,12,.003)
 # Belt is a beveled leather volume wrapped through front/side torso.
 belt=cube(pre+'belt',(0,-.008,.94),(.53,.30,.105),band,torso,.027)
 buck=cube(pre+'buckle',(0,-.174,.94),(.145,.035,.105),gold,torso,.020)
 curve(pre+'brass buckle engraving',[(.047*math.cos(i*math.tau/48),-.199,.94+.034*math.sin(i*math.tau/48)) for i in range(49)],.004,hatTan,torso)
 curve(pre+'brass buckle center',[(0,-.201,.912),(0,-.201,.968)],.004,hatTan,torso)
 if who=='challenger':
  # Surface-conforming narrow shirt stripes run along the tailored front, not through silhouette edges.
  for x in [-.22,-.16,-.10,-.04,.04,.10,.16,.22]:
   pts=[]
   for i in range(18):z=1.03+i*.46/17;rx=.27+(z-1.03)*.09;y=-.15*math.sqrt(max(.05,1-(x/rx)**2))-.003;pts.append((x,y,z))
   curve(pre+'woven red stripe',pts,.0055,stripe,torso)
 else:
  # Open vest panels are tailored bevel volumes with flared lower corners and sewn lapels.
  for side in [-1,1]:
   vs=[(side*.12,-.15,1.56),(side*.28,-.105,1.48),(side*.31,-.13,.98),(side*.09,-.18,.98),(side*.14,-.18,1.30)];vs2=[(x,y+.035,z) for x,y,z in vs];verts=vs+vs2;n=len(vs);faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)];vest=mesh(pre+'flared vest',verts,faces,brown,torso,.005);mod=vest.modifiers.new('Vest edge tailoring','BEVEL');mod.width=.008;mod.segments=2
   curve(pre+'vest lapel',[(side*.12,-.191,1.55),(side*.19,-.194,1.35),(side*.13,-.198,1.27)],.009,hatTan,torso)
 # Genuine 3D curved arm tubes, built as one smooth sweep each. Runtime deforms the same mesh.
 for side in [-1,1]:
  pts=[(side*(.30+.10*math.sin(t*math.pi)),0,1.46-.53*t) for t in [i/20 for i in range(21)]];tube(pre+('left' if side<0 else 'right')+' arm',pts,.032,black,root)
  sphere(pre+('left' if side<0 else 'right')+' hand',(side*.30,0,.93),(.043,.035,.047),cream,root,16,10,.003)
 # Tapered long clean legs use continuous meshes; foot endpoints remain grounded.
 for side in [-1,1]:
  a=V((-.139 if side<0 else .119,0,.685));b=V((-.204 if side<0 else .151,.025,.377 if side<0 else .332));c=V((-.247 if side<0 else .193,-.045,.020));pts=[(1-t)**2*a+2*(1-t)*t*b+t*t*c for t in [i/24 for i in range(25)]];tube(pre+('left' if side<0 else 'right')+' leg',pts,.033,black,root)
  sphere(pre+('left' if side<0 else 'right')+' boot',(-.247 if side<0 else .193,-.045,.009),(.060,.075,.018),black,root,16,10,.002)
 # Real curved brim + pinched crown: opaque meshes cast mapped Sun shadows on spherical skin.
 hatmat=hatBlack if who=='challenger' else hatTan;vs=[];fs=[]
 for ri,rr in enumerate([0,.65,1]):
  for j in range(48):a=j*math.tau/48;rx=.415 if who=='eddie' else .405;ry=.42 if math.sin(a)<0 else .27;z=.185+(.035 if who=='eddie' else .012)*rr**2*abs(math.cos(a))**3;vs.append((rx*rr*math.cos(a),ry*rr*math.sin(a),z))
 for i in range(2):
  for j in range(48):a=i*48+j;b=i*48+(j+1)%48;fs.append((a,b,b+48,a+48))
 brim=mesh(pre+'curved brim',vs,fs,hatmat,head,.010)
 solid=brim.modifiers.new('Physical felt brim thickness','SOLIDIFY');solid.thickness=.014
 crown=loft(pre+'pinched crown',[(.19,.23,.30),(.23,.23,.28),(.34,.22,.20),(.405,.19,.13),(.41,.17,.12)],hatmat,head,32)
 for v in crown.data.vertices:
  if who=='eddie' and v.co.z>.34:v.co.z-=.055*max(0,1-abs(v.co.x)/.15)
 # Recompute crown hull after pinching.
 for c in list(crown.children):bpy.data.objects.remove(c,do_unlink=True)
 outline(crown,.010)
 loft(pre+'hatband',[(.20,.235,.305),(.25,.232,.285)],band,head,32)
 # V6 expressions, coordinates and proportions transferred to the curved rough surface.
 for side in [-1,1]:
  x=-.131 if side<0 else .121
  if who=='challenger':
   oval(pre+'open pupil',x,.036,.031,.039,black,head)
   faceline(pre+'brow',[(x-.069,.143),(x+.057,.109)],.010,head)
  else:
   coords=[(x-.025,.020),(x+.025,.020)]+[(x+.025*math.cos(a),.020-.035*math.sin(a)) for a in [i*math.pi/16 for i in range(17)]]
   patch(pre+'open pupil',coords,black,head,.006)
   oval(pre+'eye glint',x-.006,.005,.0045,.0045,cream,head)
   faceline(pre+'upper lid',[(x-.044+.088*i/20,.028+.010*math.sin(i*math.pi/20)) for i in range(21)],.0045,head)
   faceline(pre+'brow',[(x-.067+.134*i/20,.126+.018*math.sin(i*math.pi/20)) for i in range(21)],.0075,head)
  blink=faceline(pre+'blink',[(x-.040+.080*i/20,.022-.012*math.sin(i*math.pi/20)) for i in range(21)],.0055,head);blink.hide_render=True
 if who=='challenger':
  patch(pre+'clenched mouth',roundrect(-.005,-.131,.206,.091,.028),black,head,.006)
  patch(pre+'teeth',roundrect(-.005,-.130,.174,.056,.014),cream,head,.009)
  for x in [-.055,-.011,.034]:faceline(pre+'tooth separator',[(x,-.157),(x,-.104)],.0027,head)
  faceline(pre+'tooth row',[(-.091,-.131),(.083,-.131)],.0027,head)
 else:
  # Exact V6 moustache polygon and small asymmetric mouth aperture.
  scale=1.1/1024
  px=[(510,604),(460,600),(413,635),(385,671),(452,669),(510,637),(565,669),(634,673),(594,628),(552,603)]
  patch(pre+'mustache',[((x-512)*scale,(540-y)*scale) for x,y in px],band,head,.010)
  oval(pre+'mouth aperture',-.027,-.126,.050,.025,black,head)
  curve(pre+'mouth straw',[(-.02,-.285,-.132),(.10,-.276,-.157),(.24,-.21,-.177)],.006,strawmat,head)
 # Smooth single teardrop deformation, attached to curved temple socket.
 if who=='challenger':
  drop=sphere(pre+'temple sweat',(.31,-.18,.10),(.030,.018,.065),blue,head,16,12,.002)
  for v in drop.data.vertices:v.co.x*=.75-.35*v.co.z/.065
# Refit downloaded hero guns, retain only silhouette hulls and real metal response.
for name in ['Challenger_revolver','Eddie_pearl_revolver']:
 o=O[name];o.data.materials.clear();o.data.materials.append(steel);o.hide_render=False
 for p in o.data.polygons:p.use_smooth=False
 mod=o.modifiers.new('Metal bevel highlights','BEVEL');mod.width=.007;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);outline(o,.0035)
for i in range(3):sphere('V7 aiming curled finger '+str(i),(-.18,-.055,.07+i*.025),(.032,.022,.014),cream,O['Challenger_revolver'],12,8,.002)
# Eddie's hip assembly is one clean contoured sheath, genuine trim + stitched surface.
h=link('V7 eddie holster root',parent=O['V7 eddie torso']);h.location=(-.255,-.105,.78);h.scale=(.75,.85,.70);h.rotation_euler.y=math.radians(-13)
poly=[(-.105,.14),(.105,.11),(.095,-.18),(.035,-.34),(-.045,-.33),(-.10,-.23)]
verts=[(x,y,z) for y in [-.12,-.02] for x,z in poly];n=len(poly);faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
mesh('V7 eddie contoured sheath',verts,faces,leather,h,.004)
for i in range(len(poly)):
 a=V((poly[i][0]*.85,-.126,poly[i][1]*.88));b=V((poly[(i+1)%n][0]*.85,-.126,poly[(i+1)%n][1]*.88));steps=max(2,int((b-a).length/.025))
 for j in range(steps):curve('V7 eddie sheath stitch',[a.lerp(b,(j+.20)/steps),a.lerp(b,(j+.65)/steps)],.0014,hatTan,h)
for x in [-.07,.07]:sphere('V7 eddie holster rivet',(x,-.132,.085),(.010,.006,.010),silver,h,10,8,0)
# Pearl grip is curved and volumetric, seated onto imported frame, no white box or dangling flap.
for gunname in ['Eddie_pearl_revolver']:
 gun=O[gunname];g=sphere('V7 pearl revolver butt',(-.205,-.035,.105),(.065,.045,.105),pearl,gun,20,12,.003)
 for z in [.07,.14]:sphere('V7 pearl grip screw',(-.205,-.082,z),(.008,.004,.008),silver,gun,8,6,0)
# High key golden side-Sun, broad cool area fill, gradient sky and restrained glow.
sun=O['Warm afternoon Sun'];sun.data.energy=5.1;sun.data.color=rgb('FFF0D0');sun.rotation_euler=V((.65,.24,-.82)).to_track_quat('-Z','Y').to_euler();sun.data.angle=math.radians(9);sun.data.use_shadow=True
fill=O['Subtle sky fill'];fill.data.energy=1800;fill.data.color=rgb('8CB5F3');fill.data.size=10;fill.location=(-2,-3,7);fill.rotation_euler=(V((0,9,1.3))-fill.location).to_track_quat('-Z','Y').to_euler()
nt=s.world.node_tree;nt.nodes.clear();l=nt.links;out=nt.nodes.new('ShaderNodeOutputWorld');bg=nt.nodes.new('ShaderNodeBackground');bg.inputs[1].default_value=1.05;tc=nt.nodes.new('ShaderNodeTexCoord');sep=nt.nodes.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Normal'],sep.inputs[0]);neg=nt.nodes.new('ShaderNodeMath');neg.operation='MULTIPLY';neg.inputs[1].default_value=-1;l.new(sep.outputs['Z'],neg.inputs[0]);ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=(*rgb('D9E4EC'),1);ramp.color_ramp.interpolation='EASE';ramp.color_ramp.elements[1].position=.22;ramp.color_ramp.elements[1].color=(*rgb('3876DC'),1);l.new(neg.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],bg.inputs[0]);l.new(bg.outputs[0],out.inputs[0])
# A broad low-intensity warm lobe in the world only, rather than a flat sky card.
dot=nt.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=V((-.3,-.45,-.83)).normalized();l.new(tc.outputs['Normal'],dot.inputs[0]);pwr=nt.nodes.new('ShaderNodeMath');pwr.operation='POWER';pwr.inputs[1].default_value=16;l.new(dot.outputs['Value'],pwr.inputs[0]);warm=nt.nodes.new('ShaderNodeMixRGB');warm.blend_type='ADD';warm.inputs[2].default_value=(*rgb('FFC877'),1);strength=nt.nodes.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.15;l.new(pwr.outputs[0],strength.inputs[0]);l.new(strength.outputs[0],warm.inputs[0]);l.new(ramp.outputs[0],warm.inputs[1]);l.new(warm.outputs[0],bg.inputs[0])
s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='MEDIUM';gl.threshold=1.3;gl.size=7;gl.mix=1;blend=nt.nodes.new('CompositorNodeMixRGB');blend.blend_type='ADD';blend.inputs[0].default_value=.15;nt.links.new(rl.outputs['Image'],gl.inputs[0]);nt.links.new(rl.outputs['Image'],blend.inputs[1]);nt.links.new(gl.outputs['Image'],blend.inputs[2]);co=nt.nodes.new('CompositorNodeComposite');nt.links.new(blend.outputs[0],co.inputs[0])
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=-.15;s.eevee.taa_render_samples=16;s.eevee.use_raytracing=False;s.render.engine='BLENDER_EEVEE_NEXT';s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=30;s.frame_start=1;s.frame_end=300
# Receiver-local cel road keeps actual cast shadows but maps shade to indigo and direct Sun to gold.
road=O['Dusty Main Street'];m=road.data.materials[0].copy();road.data.materials[0]=m;nt=m.node_tree;l=nt.links;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');source=bs.inputs['Base Color'].links[0].from_socket;diff=nt.nodes.new('ShaderNodeBsdfDiffuse');diff.inputs[0].default_value=(1,1,1,1);st=nt.nodes.new('ShaderNodeShaderToRGB');l.new(diff.outputs[0],st.inputs[0]);bw=nt.nodes.new('ShaderNodeRGBToBW');l.new(st.outputs[0],bw.inputs[0]);gain=nt.nodes.new('ShaderNodeMath');gain.operation='MULTIPLY';gain.inputs[1].default_value=.62;l.new(bw.outputs[0],gain.inputs[0]);rp=nt.nodes.new('ShaderNodeValToRGB');rp.color_ramp.interpolation='EASE';rp.color_ramp.elements[0].position=.08;rp.color_ramp.elements[0].color=(*rgb('687DA8'),1);rp.color_ramp.elements[1].position=.75;rp.color_ramp.elements[1].color=(*rgb('EBD09B'),1);l.new(gain.outputs[0],rp.inputs[0]);value=nt.nodes.new('ShaderNodeRGBToBW');l.new(source,value.inputs[0]);nr=nt.nodes.new('ShaderNodeMapRange');nr.inputs['From Min'].default_value=.10;nr.inputs['From Max'].default_value=.65;nr.inputs['To Min'].default_value=.82;nr.inputs['To Max'].default_value=1.08;l.new(value.outputs[0],nr.inputs['Value']);mult=nt.nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;l.new(rp.outputs[0],mult.inputs[1]);l.new(nr.outputs[0],mult.inputs[2]);em=nt.nodes.new('ShaderNodeEmission');em.inputs[1].default_value=1.1;l.new(mult.outputs[0],em.inputs[0]);mx=nt.nodes.new('ShaderNodeMixShader');mx.inputs[0].default_value=.12;l.new(em.outputs[0],mx.inputs[1]);l.new(bs.outputs[0],mx.inputs[2]);l.new(mx.outputs[0],out.inputs[0])
# Orange-yellow directional flame meshes and volumetric smoke puffs, not a white star.
fx=link('V7 muzzle FX root');hot=shader('V7 blast hot','FFF49B',0,.5,False);outer=shader('V7 blast amber','FF6C10',0,.5,False)
for mat,c,power in [(hot,'FFF49B',6),(outer,'FF6C10',3)]:
 bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Emission Color'].default_value=(*rgb(c),1);bs.inputs['Emission Strength'].default_value=power
for name,mat,length,radius in [('amber fire',outer,.30,.075),('yellow core',hot,.22,.045)]:
 o=loft('V7 '+name,[(0,radius,radius),(.10,radius*.9,radius*.9),(length,0.002,.002)],mat,fx,16);o.rotation_euler.y=math.pi/2
smokeMat=shader('V7 smoke grey','BDC4CF',0,.9,False);smokeMat.surface_render_method='BLENDED';next(n for n in smokeMat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Alpha'].default_value=.25
for i in range(3):sphere('V7 smoke '+str(i),(0,0,0),(.06,.06,.06),smokeMat,None,16,10,0)
# Existing copper geometry is smooth and beveled; materials stay true metallic copper/brass.
b=O['Copper_bullet'];b['set_ink']=False
for i,m in enumerate(b.data.materials):
 if m.use_nodes:
  for bs in [n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED']:
   bs.inputs['Base Color'].default_value=(*rgb('CF763F' if i==0 else 'CFAB54'),1);bs.inputs['Metallic'].default_value=.9;bs.inputs['Roughness'].default_value=.2;bs.inputs['Emission Strength'].default_value=.12
for p in b.data.polygons:p.use_smooth=True
# Runtime root and contact empties.
link('V7 hero focus');link('V7 aiming grip');
after=town_hash();assert before==after;(P/'town_preservation.json').write_text(json.dumps({'before':before,'after':after,'unchanged':True},indent=2))
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0] and not im.packed_file:im.pack()
t=bpy.data.texts.load(str(R/'scripts/slow_eddie_v7/runtime.py'));t.name='slow_eddie_v7_runtime.py';exec(compile(t.as_string(),t.name,'exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v7.blend'));print('BUILD V7 OK',flush=True)
