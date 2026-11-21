"""Original story geometry; shaders and camera baseline come from ricks_lookdev."""
import bpy, math
from mathutils import Vector as V
import ricks_lookdev as look
S=bpy.context.scene
def obj(name,data=None,parent=None):
 o=bpy.data.objects.new(name,data);S.collection.objects.link(o);o.parent=parent;return o
def emission(name,color,strength=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear()
 e=n.new('ShaderNodeEmission');e.inputs[0].default_value=look.rgba(color);e.inputs[1].default_value=strength
 out=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],out.inputs[0]);return m
def ink(o,width=.005):
 o.data.update();me=o.data.copy();me.materials.clear();me.materials.append(bpy.data.materials['Marker ink'])
 for v,n in zip(me.vertices,[v.normal.copy() for v in o.data.vertices]):v.co+=n*width
 for p in me.polygons:p.flip()
 h=obj(o.name+' / ink',me,o);look.mark_role(h,'ink');h['ink_base_width']=width;return h
def mesh(name,vs,fs,mat,parent=None,outline=0,smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(mat);me.update()
 import bmesh
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
 o=obj(name,me,parent)
 for p in me.polygons:p.use_smooth=smooth
 if outline:ink(o,outline)
 return o
def sphere(name,xyz,scale,mat,parent=None,seg=24,rings=12,outline=0):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1)
 o=bpy.context.object;o.name=name;o.parent=parent;o.location=xyz
 for v in o.data.vertices:v.co=V((v.co.x*scale[0],v.co.y*scale[1],v.co.z*scale[2]))
 o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 if outline:ink(o,outline)
 return o
def cube(name,xyz,size,mat,parent=None,bevel=.02,outline=0):
 bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name=name;o.parent=parent;o.location=xyz
 for v in o.data.vertices:v.co=V((v.co.x*size[0],v.co.y*size[1],v.co.z*size[2]))
 o.data.materials.append(mat)
 if bevel:
  mod=o.modifiers.new('Soft crafted edge','BEVEL');mod.width=bevel;mod.segments=2
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 if outline:ink(o,outline)
 return o
def line(name,pts,r,mat,parent=None):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=2
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=obj(name,cu,parent);cu.materials.append(mat);return o
def bezier_points(a,b,c,d,n=20):
 a,b,c,d=map(V,(a,b,c,d));return [(1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d for t in [i/(n-1) for i in range(n)]]
def set_line(o,pts):
 for p,co in zip(o.data.splines[0].points,pts):p.co=(*co,1)
def cylinder(name,a,b,r,mat,parent=None,verts=24,outline=0):
 a,b=V(a),V(b);bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=(b-a).length)
 o=bpy.context.object;o.name=name;o.parent=parent;o.location=(a+b)/2;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
 if outline:ink(o,outline)
 return o
def loft(name,rings,mat,parent=None,n=32,outline=.005):
 vs=[];fs=[]
 for z,rx,ry in rings:
  for j in range(n):a=j*math.tau/n;vs.append((rx*math.cos(a),ry*math.sin(a),z))
 for i in range(len(rings)-1):
  for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
 fs+=[tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]
 return mesh(name,vs,fs,mat,parent,outline)
def rough(a):return 1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9)+.025*(.6*math.sin(4*a+.3)+.4*math.cos(7*a-1.2))
def facepoint(x,z,offset=.004):
 r=.32*rough(math.atan2(-z,x));return (x,-.032*math.sqrt(max(.035,1-(x*x+z*z)/(r*r)))-offset,z)
def patch(name,coords,mat,parent,offset=.004):
 cx=sum(x for x,z in coords)/len(coords);cz=sum(z for x,z in coords)/len(coords)
 tris=[((cx,cz),coords[i],coords[(i+1)%len(coords)]) for i in range(len(coords))]
 for depth in range(2):
  sub=[]
  for a,b,c in tris:
   ab=tuple((a[i]+b[i])/2 for i in (0,1));bc=tuple((b[i]+c[i])/2 for i in (0,1));ca=tuple((c[i]+a[i])/2 for i in (0,1))
   sub.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
  tris=sub
 vs=[];fs=[];lookup={}
 for tri in tris:
  ids=[]
  for x,z in tri:
   key=(round(x,8),round(z,8))
   if key not in lookup:lookup[key]=len(vs);vs.append(facepoint(x,z,offset))
   ids.append(lookup[key])
  fs.append(tuple(ids))
 return mesh(name,vs,fs,mat,parent)
def oval(name,x,z,rx,rz,mat,parent,offset=.006):
 return patch(name,[(x+rx*math.cos(i*math.tau/24),z+rz*math.sin(i*math.tau/24)) for i in range(24)],mat,parent,offset)
def faceline(name,pts,r,mat,parent):return line(name,[facepoint(x,z,.009) for x,z in pts],r,mat,parent)
def light(name,kind,xyz,target,energy,color,size=1):
 data=bpy.data.lights.new(name,kind);o=obj(name,data);o.location=xyz;o.rotation_euler=(V(target)-o.location).to_track_quat('-Z','Y').to_euler()
 data.energy=energy;data.color=look.rgba(color)[:3]
 if kind=='AREA':data.shape='DISK';data.size=size
 if kind=='SPOT':data.spot_size=math.radians(68);data.spot_blend=.65;data.shadow_soft_size=size
 return o
