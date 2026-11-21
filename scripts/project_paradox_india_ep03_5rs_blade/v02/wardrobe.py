"""Surface-conformed costume accents; faces and limbs retain graphic shading."""
import bpy,math
import geometry as G
import ricks_lookdev as look
RINGS=[(.67,.16,.085),(.72,.205,.1),(1.05,.24,.11),(1.16,.21,.095),(1.21,.085,.06)]
def surface(x,z,offset=.004):
 for a,b in zip(RINGS,RINGS[1:]):
  if a[0]<=z<=b[0]:
   t=(z-a[0])/(b[0]-a[0]);rx=a[1]+t*(b[1]-a[1]);ry=a[2]+t*(b[2]-a[2]);break
 else:rx,ry=.10,.07
 return x,-ry*math.sqrt(max(.01,1-(x/rx)**2))-offset,z
def cloth(name,points,material,body):
 center=tuple(sum(p[i] for p in points)/len(points) for i in [0,1]);triangles=[(center,points[i],points[(i+1)%len(points)]) for i in range(len(points))]
 for _ in range(3):
  refined=[]
  for a,b,c in triangles:
   ab=tuple((a[i]+b[i])/2 for i in [0,1]);bc=tuple((b[i]+c[i])/2 for i in [0,1]);ca=tuple((c[i]+a[i])/2 for i in [0,1])
   refined.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
  triangles=refined
 vertices=[];faces=[]
 for triangle in triangles:
  faces.append(tuple(range(len(vertices),len(vertices)+3)));vertices.extend(surface(x,z) for x,z in triangle)
 o=G.mesh(name,vertices,faces,material,body)
 contour=[]
 for a,b in zip(points,points[1:]+[points[0]]):
  contour.extend(surface(a[0]+(b[0]-a[0])*j/8,a[1]+(b[1]-a[1])*j/8,.0055) for j in range(8))
 contour.append(contour[0])
 edge=G.line(name+' ink seam',contour,.003,bpy.data.materials['Graphic limbs and features'],body)
 look.mark_role(edge,'ink');return o
def apply(force=False):
 O=bpy.data.objects
 if force:
  prefixes=['Officer tailored lapel','Officer white collar','Officer red silk tie','Trader charcoal vest','Smuggler charcoal vest','Shopkeeper small apron']
  for o in list(O):
   if any(o.name.startswith(prefix) for prefix in prefixes):bpy.data.objects.remove(o,do_unlink=True)
 if O.get('Officer tailored lapel -1'):return
 old=O.get('Officer tie')
 if old:bpy.data.objects.remove(old,do_unlink=True)
 white=bpy.data.materials['White cotton'];red=bpy.data.materials['Brick crimson'];dark=bpy.data.materials['Dark leather']
 lapel=look.clean_toon('Officer lapel blue',stops=[(0,'#293448'),(.4,'#4C5D79'),(1,'#7B8DA5')])
 body=O['Officer body']
 for side in [-1,1]:
  cloth('Officer tailored lapel '+str(side),[(side*.06,1.18),(side*.20,1.13),(side*.10,1.04),(side*.05,.94),(side*.15,1.02)],lapel,body)
  cloth('Officer white collar '+str(side),[(side*.055,1.20),(side*.13,1.15),(side*.052,1.095)],white,body)
 cloth('Officer red silk tie',[(-.024,1.17),(.024,1.17),(.042,.99),(0,.94),(-.042,.99)],red,body)
 for name in ['Trader','Smuggler']:
  O[name+' connected torso'].data.materials[0]=white
  for side in [-1,1]:
   cloth(name+' charcoal vest '+str(side),[(side*.065,1.18),(side*.205,1.13),(side*.19,.75),(side*.065,.735),(side*.075,.99)],dark,O[name+' body'])
 apron=look.clean_toon('Shopkeeper tan apron','vest')
 cloth('Shopkeeper small apron',[(-.12,1.09),(.12,1.09),(.16,.76),(-.16,.76)],apron,O['Shopkeeper body'])
