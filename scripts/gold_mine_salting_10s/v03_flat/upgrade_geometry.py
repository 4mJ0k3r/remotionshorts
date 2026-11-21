# Runs only inside this new production's builder, before packing the scene.
# Chiseled shelves / overhangs break wall boundaries without adding heavy assets.
random.seed(3031899)
for side in [-1,1]:
 for y in [-1.4,.4,2.2,4.0,5.8]:
  for z in [.42,1.22,2.20,2.88]:
   center=V((side*3.10,y+random.uniform(-.17,.17),z))
   radius=(random.uniform(.23,.42),random.uniform(.42,.68),random.uniform(.16,.34))
   o=sphere('Chiseled sidewall shelf',center,radius,rock,seg=7,rings=4)
   for p in o.data.polygons:p.use_smooth=False
   for v in o.data.vertices:v.co*=random.uniform(.87,1.12)
   o['collision']=True
for x in [.25,1.35,2.5]:
 for z in [.35,2.52,2.9]:
  o=sphere('Layered strike alcove ledge',(x,4.78,z),(.35,.14,.17),rock,seg=7,rings=4)
  for p in o.data.polygons:p.use_smooth=False
  for v in o.data.vertices:v.co*=random.uniform(.88,1.13)
  o['collision']=True
for y in [-1,1.4,3.9,6.1]:
 for x in [-2.3,2.3]:
  o=sphere('Jagged ceiling overhang',(x,y,3.0),(.57,.78,.24),rock,seg=7,rings=4)
  for p in o.data.polygons:p.use_smooth=False
  o['collision']=True
for x in [-2.6,2.6]:
 o=cube('Foreground rustic timber jamb',(x,1.8,1.38),(.22,.3,2.76),timber,bevel=.03,outline=.005);o['collision']=True
spill=light('Rock flash spill','POINT',(.50,4.30,1.64),(.55,4.8,1.6),0,'#FFA64A',.2);spill.data.use_shadow=False
# The deep end receives no outdoor sky/fog. The floor and end wall carry
# a rich espresso surface that still responds to the sparse practical lights.
espresso=look.metal('Deep tunnel espresso','#22140C',0,1)
for name in ['Cool black tunnel depth','Distant tunnel earth']:
 O=bpy.data.objects.get(name)
 if O:O.data.materials.clear();O.data.materials.append(espresso)
# Fixed authored low-frequency irregularity follows the head rest contour.
# It is already applied by geometry.rough(), also used by conformed face art.
S['head_contour']='Static low-frequency harmonic displacement, peak <=0.008m; no frame-dependent phase'
