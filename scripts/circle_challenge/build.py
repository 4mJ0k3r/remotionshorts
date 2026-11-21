"""Blender 4.2 standalone scene builder. No handlers, image swaps or video render."""
import bpy, math, random, json, sys
from pathlib import Path
from mathutils import Vector
BASE=Path('D:/remotionshorts'); OUT=BASE/'renders/circle_challenge'; AS=OUT/'assets'
random.seed(42)
for old in list(bpy.data.objects):bpy.data.objects.remove(old,do_unlink=True)
s=bpy.context.scene;s.name='Circle Challenge | calibration master'
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.use_raytracing=False;s.eevee.taa_render_samples=16
s.render.use_simplify=True;s.render.simplify_subdivision=2
s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=50
s.render.fps=30;s.frame_start=1;s.frame_end=2205
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
s.render.image_settings.file_format='PNG';s.render.film_transparent=False
s.world=bpy.data.worlds.new('Four-act sky');s.world.use_nodes=True
world=s.world.node_tree.nodes.get('Background');world.inputs['Strength'].default_value=.65
def rgb(h):
    h=h.lstrip('#');v=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)
def mat(name,color,emit=0,alpha=1):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb(color),alpha);p.inputs['Roughness'].default_value=.72
    p.inputs['Emission Color'].default_value=(*rgb(color),1);p.inputs['Emission Strength'].default_value=emit
    p.inputs['Alpha'].default_value=alpha
    if alpha<1:m.surface_render_method='BLENDED'
    return m
M={k:mat(k,c) for k,c in {'ink':'#182237','grass':'#5cb85c','road':'#bf9467','gold':'#ebba45','red':'#e94a50','white':'#fff7e8','wood':'#97633f','blue':'#1389c0','mint':'#7cdfb4','tire':'#18212c','pink':'#be4d73','console':'#47253f'}.items()}
M['glow']=mat('Boundary warm-white emission','#fff1d3',2)
M['green']=mat('Toxic lime transparent','#92ed35',.6,.28)
M['ribbon']=mat('Tapered translucent stink','#63cf35',.35,.58)
M['alarm']=mat('Red alarm emission','#ff163c',3)
def key(o,path,f,value,interp='CONSTANT'):
    setattr(o,path,value);o.keyframe_insert(data_path=path,frame=f)
    for fc in o.animation_data.action.fcurves:
        if fc.data_path==path:
            for k in fc.keyframe_points:
                if abs(k.co.x-f)<.01:k.interpolation=interp
def visible(o,a,b):
    base=tuple(o.scale);key(o,'scale',1,(0,0,0));key(o,'scale',a,base);key(o,'scale',b,(0,0,0))
def empty(name,loc=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None);s.collection.objects.link(o);o.location=loc;o.parent=parent;return o
ARENA=empty('Arena_Set'); BRAIN=empty('Brain_Set',(50,0,0))
def cube(name,loc,scale,ma,bev=.06,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev:mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bev;mod.segments=2;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    o.data.materials.append(ma);o.parent=parent;return o
def sphere(name,loc,scale,ma,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(ma);o.parent=parent
    for p in o.data.polygons:p.use_smooth=True
    return o
def cyl(name,loc,r,depth,ma,parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(ma);o.parent=parent;return o
def rod(name,a,b,r,ma,parent=None):
    a=Vector(a);b=Vector(b);o=cyl(name,(a+b)/2,r,(b-a).length,ma,parent);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return o
def curve(name,pts,r,ma,parent=None):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=2
    sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
    for p,co in zip(sp.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,c);s.collection.objects.link(o);o.data.materials.append(ma);o.parent=parent;return o
def image_mat(name,path):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.surface_render_method='BLENDED'
    n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);tex.image.alpha_mode='STRAIGHT';tex.interpolation='Linear'
    e=n.new('ShaderNodeEmission');e.inputs['Strength'].default_value=1.08;p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=1
    mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.95;t=n.new('ShaderNodeBsdfTransparent');a=n.new('ShaderNodeMixShader')
    l=m.node_tree.links;l.new(tex.outputs['Color'],e.inputs['Color']);l.new(tex.outputs['Color'],p.inputs['Base Color']);l.new(p.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);l.new(tex.outputs['Alpha'],a.inputs[0]);l.new(t.outputs[0],a.inputs[1]);l.new(mix.outputs[0],a.inputs[2]);l.new(a.outputs[0],out.inputs['Surface']);return m
def plane(name,w,h,ma,parent=None,loc=(0,0,0)):
    me=bpy.data.meshes.new(name);me.from_pydata([(-w/2,-h/2,0),(w/2,-h/2,0),(w/2,h/2,0),(-w/2,h/2,0)],[],[(0,1,2,3)]);me.uv_layers.new()
    for i,uv in enumerate([(0,0),(1,0),(1,1),(0,1)]):me.uv_layers.active.data[i].uv=uv
    o=bpy.data.objects.new(name,me);s.collection.objects.link(o);o.data.materials.append(ma);o.parent=parent;o.location=loc;return o
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='StoryCamera';s.camera=cam;cam.data.type='ORTHO';cam.data.lens=45;cam.data.dof.use_dof=False
def billboard(o):
    c=o.constraints.new('COPY_ROTATION');c.target=cam
def card(name,asset,w,h,loc,parent=None,face=False):
    o=plane(name,w,h,image_mat(name,AS/f'{asset}.png'),parent,loc)
    if face:billboard(o)
    else:o.rotation_euler=(math.pi/2,0,0)
    return o
def text(name,txt,loc,size,ma,parent=None,face=True):
    c=bpy.data.curves.new(name,'FONT');c.body=txt;c.align_x='CENTER';c.size=size;c.extrude=.003
    o=bpy.data.objects.new(name,c);s.collection.objects.link(o);o.location=loc;o.parent=parent;c.materials.append(ma)
    if face:billboard(o)
    else:o.rotation_euler=(math.pi/2,0,0)
    return o
# Outdoor stage: checker grass, low-poly landmarks, dimensional fixtures.
ground=cube('Grass field',(0,4,-.19),(65,65,.35),M['grass'],0)
nt=M['grass'].node_tree;n=nt.nodes;tex=n.new('ShaderNodeTexChecker');tex.inputs['Color1'].default_value=(*rgb('#5cb85c'),1);tex.inputs['Color2'].default_value=(*rgb('#53ac54'),1);tex.inputs['Scale'].default_value=24;nt.links.new(tex.outputs['Color'],n.get('Principled BSDF').inputs['Base Color'])
cube('Foreground dirt road',(0,-8,-.015),(50,3,.1),M['road'])
for j in range(96):
    a=j*math.tau/96;b=(j+1)*math.tau/96
    curve('Raised circle boundary',[(6.5*math.cos(a),6.5*math.sin(a),.08),(6.5*math.cos(b),6.5*math.sin(b),.08)],.095,M['red'] if j%8<2 else M['glow'])
cube('Massive stage',(0,8.5,.42),(10,3,.84),M['ink'],.12)
for z in range(3):cube('Stage stair',(0,6.7-z*.38,.15+z*.14),(3,.5,.3),M['ink'])
cube('Scoreboard housing',(0,9.1,4.9),(9.2,.5,3.7),M['gold'],.12)
score=card('Prize LED','score',8.9,3.34,(0,8.81,4.9));visible(score,1,1668)
win=card('Winner LED','winner',8.9,3.34,(0,8.8,4.9));visible(win,1668,2206)
for x in (-4.1,4.1):cube('Scoreboard structural post',(x,9.1,2),( .2,.3,4),M['ink'])
for x,y in [(-9,7),(9,9),(-11,14),(11,16),(-7,17),(6,19),(-14,2),(14,4)]:
    cyl('Pine trunk',(x,y,1),.22,2,M['wood'])
    for z,r in [(2,1.6),(3,1.25),(4,.9)]:
        bpy.ops.mesh.primitive_cone_add(vertices=7,radius1=r,radius2=0,depth=2.7,location=(x,y,z));bpy.context.object.data.materials.append(mat(f'Pine {x} {z}',random.choice(['#24845b','#18724f','#399765'])))
for x in (-7.5,7.5):
    rod('Floodlight mast',(x,7,0),(x,7,8),.1,M['ink']);cube('Floodlight bar',(x,7,8),(2,.4,.8),M['ink'])
    for dx in (-.65,0,.65):cube('Floodlight lamp',(x+dx,6.75,8),(.5,.08,.48),M['glow'])
for x in (-8,-5):rod('Crew tent pole',(x,3,0),(x,3,3),.06,M['white']);rod('Crew rear tent pole',(x,5,0),(x,5,3),.06,M['white'])
for j in range(8):
    x=-8+j*.43
    mesh=bpy.data.meshes.new('Tent roof');mesh.from_pydata([(x,2.7,2.8),(x+.44,2.7,2.8),(x+.44,4,3.8),(x,4,3.8),(x,5.3,2.8),(x+.44,5.3,2.8)],[],[(0,1,2,3),(3,2,5,4)]);o=bpy.data.objects.new('Striped crew canopy',mesh);s.collection.objects.link(o);o.data.materials.append(M['red'] if j%2 else M['white'])
for x,y in [(-5,-3),(5,-3),(-7,1)]:
    for dx,dy in [(-.4,-.3),(.4,-.3),(0,.4)]:rod('TV tripod',(x+dx,y+dy,.05),(x,y,1.5),.035,M['ink'])
    cube('TV camera',(x,y,1.65),(.65,.8,.42),M['ink']);lens=cyl('Camera lens',(x,y-.48,1.65),.17,.25,M['blue']);lens.rotation_euler.x=math.pi/2
# Portable toilet, open recess, hinged leaf and complete hardware.
toilet=empty('PortaPotty',(4.5,2,0))
for name,loc,dim in [('Back',(0,.75,1.65),(1.8,.13,3.3)),('Left',(-.84,0,1.65),(.13,1.5,3.3)),('Right',(.84,0,1.65),(.13,1.5,3.3)),('Roof',(0,0,3.35),(2,1.8,.18)),('Base',(0,0,.1),(1.9,1.7,.2))]:cube('Toilet '+name,loc,dim,M['blue'] if name!='Roof' else M['white'],parent=toilet)
hinge=empty('ToiletDoor_HINGE',(-.8,-.8,.14),toilet)
cube('Door leaf',(.8,0,1.52),(1.56,.12,3.02),M['blue'],parent=hinge)
cube('Door recessed panel',(.8,-.075,1.45),(1.3,.025,2.1),mat('Door darker panel','#07689d'),parent=hinge)
cube('Door handle rosette',(1.38,-.1,1.5),(.13,.05,.2),M['white'],parent=hinge);rod('Door lever',(1.38,-.15,1.5),(1.2,-.15,1.5),.035,M['gold'],hinge)
card('WC sign','toilet',.85,.32,(.8,-.085,2.65),hinge)
for f,v in [(1,0),(2095,-1.5),(2120,-1.5),(2140,0)]:key(hinge,'rotation_euler',f,(0,0,v),'LINEAR' if f==2120 else 'CONSTANT')
sphere('Interior toilet bowl',(0,.25,.7),(.5,.65,.45),M['white'],toilet)
# Cast, separate head pivots and CONSTANT pose scales.
S=3/1474
def actor(name,who,loc,pose_events,scale=1):
    root=empty(name,loc);root.scale=(scale,)*3
    bodypivot=empty(name+'_body_billboard',parent=root);billboard(bodypivot)
    headpivot=empty(name+'_head_independent_pivot',(0,(1474-380)*S,0),bodypivot);billboard(headpivot)
    poses=sorted(set(p for _,p in pose_events));pieces={}
    for p in poses:
        body=plane(name+'_'+p+'_body',1024*S,1536*S,image_mat(who+p+'body',AS/f'{who}_{p}_body.png'),bodypivot,(0,(1474-768)*S,0))
        head=plane(name+'_'+p+'_head',512*S,512*S,image_mat(who+p+'head',AS/f'{who}_{p}_head.png'),headpivot,(0,0,.008))
        pieces[p]=(body,head)
        for f,active in pose_events:
            for ob in (body,head):key(ob,'scale',f,(1,1,1) if p==active else (0,0,0))
    shadowmat=mat(name+' grounded contact','#253332',alpha=.2)
    shadow=sphere(name+' sole contact',(0,0,.015),(.46,.23,.013),shadowmat,root)
    root['pose_method']='separate head/body planes; CONSTANT child scales; no image mutation'
    return root,bodypivot,headpivot
you,ybody,yhead=actor('char_you','you',(0,0,0),[(1,'happy'),(210,'belly'),(312,'shock'),(378,'panic'),(459,'panic'),(485,'squat'),(535,'shock'),(576,'smug'),(1299,'smug'),(1668,'happy'),(1740,'phone'),(1770,'shout'),(1805,'phone'),(1820,'shout'),(1854,'smug'),(2013,'hug'),(2095,'smug')])
host,hbody,hhead=actor('char_youtuber','host',(0,7,.84),[(1,'happy'),(1299,'happy'),(1355,'sniff'),(1385,'run'),(1668,'sniff'),(1740,'shock')])
rival,rbody,rhead=actor('char_rival','rival',(-1.5,1,0),[(1,'happy'),(1446,'cry'),(1539,'cry'),(1615,'run')]);visible(rival,1446,1668)
mom,mbody,mhead=actor('char_mummy','mom',(-1.5,-4,0),[(1,'raise'),(2013,'hug'),(2095,'smug')]);visible(mom,1910,2206)
op,obody,ohead=actor('char_brain_op','operator',(49.1,0,.1),[(1,'panic'),(1000,'raise'),(1015,'press'),(1040,'shock')],.85);visible(op,965,1104)
# Walks and finite recoil have real keyframed root motion, with exact settles.
for f,loc in [(1,(0,0,0)),(378,(0,-5.6,0)),(459,(0,0,0)),(2095,(4.5,.5,0)),(2120,(4.5,2,.05))]:key(you,'location',f,loc,'LINEAR' if f==2095 else 'CONSTANT')
for f,loc in [(1,(0,7,.84)),(1299,(-2.6,.1,0)),(1310,(-2.7,.1,0)),(1355,(-1.5,.1,0)),(1385,(-1.5,.1,0)),(1390,(-1.35,.1,0)),(1438,(-4.4,.1,0)),(1446,(-4.5,.1,0)),(1668,(-3.3,.8,0)),(1740,(-1.8,.35,0))]:key(host,'location',f,loc,'LINEAR' if 1299<=f<=1438 else 'CONSTANT')
for f,x in [(1446,-1.6),(1615,-1.6),(1622,-1.45),(1667,-7.1)]:key(rival,'location',f,(x,0,0),'LINEAR')
for f,loc in [(1910,(-.6,-5,0)),(2013,(-1,-.1,0)),(2095,(3,1,0))]:key(mom,'location',f,loc)
# Body event bobs during movement only. Stable roots outside these ranges.
def bobs(root,a,b,amp=.06,step=10):
    z=root.location.z
    for f in range(a,b+1,step):key(root,'delta_location',f,(0,0,amp if ((f-a)//step)%2 else 0),'LINEAR')
    key(root,'delta_location',b,(0,0,0))
bobs(host,1299,1355);bobs(host,1385,1445,.1,6);bobs(rival,1615,1667,.08,6)
for f,z in [(480,0),(485,.03),(515,-.16),(530,-.16),(535,.06),(542,0)]:key(you,'delta_location',f,(0,0,z),'LINEAR' if f<542 else 'CONSTANT')
# 38 crowd members, 18 animated fleeing contestants. No lead overlap in the foreground.
crowd=[]
for i in range(38):
    x=random.uniform(-5.2,5.2);y=random.uniform(1.8,5.2)
    if x*x+y*y>37:x*=.65
    a,_,_=actor(f'Contestant_{i:02d}','extra',(x,y,0),[(1,'happy'),(1104+i*2,'sniff'),(1120+i*2,'run')],random.uniform(.58,.73));crowd.append(a)
    if i<18:
        start=1104+i*4;end=start+100;side=-1 if x<0 else 1
        key(a,'location',1,(x,y,0));key(a,'location',start,(x,y,0),'LINEAR');key(a,'location',end,(side*(8+i*.08),y-3,0));bobs(a,start,end,.07,8)
    visible(a,1,1299 if i<18 else 1104)
# Tapered mesh ribbons; animated finite rise/fade episodes, always behind the cel.
def ribbon(name,loc,height=2.4,parent=None,seed=0):
    verts=[];faces=[]
    for j in range(25):
        t=j/24;x=.15*math.sin(t*10+seed);w=.085*math.sin(math.pi*t)*(1-t*.6)
        verts.extend([(x-w,0,t*height),(x+w,0,t*height)])
    for j in range(24):faces.append((j*2,j*2+1,j*2+3,j*2+2))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);o.location=loc;o.parent=parent;o.data.materials.append(M['ribbon']);return o
for i in range(3):
    r=ribbon('Rear pants stink ribbon',(.52+i*.19,.16,.55),1.7,you,i);visible(r,315,2095)
    for a in (315,576,732,1104,1299,1446,1740,2013):
        for f,dz in [(a,0),(a+12,.06),(a+28,.13),(a+44,.17)]:key(r,'delta_location',f,(0,0,dz),'LINEAR' if f<a+44 else 'CONSTANT')
for i in range(3):r=ribbon('Toilet stink ribbon',(4.05+i*.4,2.2,3.4),2,None,i);visible(r,2120,2206)
# Warning rings and the finite accident shockwave.
def ring(name,loc,r,ma):
    return curve(name,[(loc[0]+r*math.cos(j*math.tau/64),loc[1],loc[2]+r*math.sin(j*math.tau/64)) for j in range(65)],.035,ma)
for i in range(3):
    r=ring('Stomach warning', (0,-.13,1.35),.35+i*.12,M['red']);visible(r,210+i*8,264)
burst=sphere('Cartoon brown shockwave',(0,.7,.9),(1.7,.15,.9),mat('Brown shockwave','#a66b3b',alpha=.3));visible(burst,312,337)
for f,sc in [(312,(.2,.1,.2)),(318,(1.9,.1,1.1)),(330,(2.2,.1,1.3)),(337,(0,0,0))]:key(burst,'scale',f,sc,'LINEAR')
for i in range(8):
    r=ribbon('Bio aura ray',(-1.1+i*.31,.6,.1),3.5,None,i);visible(r,576,930)
for i in range(3):
    r=ring('37C heat ring',(0,.4,1.4),.9+i*.35,M['gold']);visible(r,732,930)
for i,(label,x,z) in enumerate([('SKATOLE',-1.0,3.8),('H2S',1.1,3.3),('37°C',-.9,.6)]):
    o=sphere('Chemical sphere '+label,(x,.2,z),(.58,.12,.4),M['green']);visible(o,732,930)
    t=text('Chemical label '+label,label,(x,-.05,z-.06),.21,M['ink']);visible(t,732,930)
gas=sphere('Expanding toxic dome',(0,1,1.1),(3.5,2.6,1.5),mat('Very light gas dome','#a3e941',.05,.065));visible(gas,732,1446)
# Brain control room at X=50, cutaway wall and practical neural tubes.
cube('Brain floor',(50,1,-.2),(10,9,.4),M['pink']);cube('Brain back wall',(50,4,3.3),(10,.3,6.6),M['console'])
for i in range(7):
    x=46+i*1.3
    curve('Glowing neural tube',[(x,3.75,.4),(x-.4,3.7,1.8),(x+.3,3.7,3.4),(x-.3,3.7,5.8)],.10,mat('Neural pink '+str(i),'#fa82ac',1))
cube('Brain control console',(50,1,.6),(4,1.6,1.2),M['console'],.14)
cube('Console deck',(50,.8,1.25),(4.2,1.8,.17),M['pink'])
button=cyl('Fixed VOMIT CENTER button',(50.55,.5,1.49),.5,.35,M['alarm'])
for f,z in [(1000,1.49),(1015,1.49),(1030,1.36),(1040,1.36),(1055,1.49)]:key(button,'location',f,(50.55,.5,z),'LINEAR')
card('Vomit center wall sign','brain',4.2,1.55,(50,3.5,4.45))
for i in range(6):
    cube('Console key',(48.5+i*.36,-.05,1.38),(.22,.2,.09),M['gold'] if i%2 else M['blue'])
for x in (46.7,53.3):
    o=sphere('Alarm dome',(x,3.3,3.5),(.26,.25,.35),M['alarm'])
    bpy.ops.object.light_add(type='POINT',location=(x,2.9,3.4));bpy.context.object.data.energy=70;bpy.context.object.data.color=(1,.04,.06)
# Ghost soul: a tapered white floating cartoon with attached expressive eyes.
ghost=empty('Rival ghost soul',(-1.55,-.25,2.1));visible(ghost,1539,1615)
gmat=mat('Ghost translucent white','#f7fcff',.6,.65)
sphere('Ghost head',(0,0,.6),(.33,.12,.38),gmat,ghost)
curve('Ghost taper',[(0,0,.5),(.15,0,.22),(.12,0,0),(.33,0,-.17)],.16,gmat,ghost)
for x in (-.11,.11):sphere('Ghost black eye',(x,-.13,.65),(.035,.022,.075),M['ink'],ghost)
for f,pos in [(1539,(-1.55,-.25,2.1)),(1600,(-.8,-.25,3.25)),(1614,(-.5,-.25,3.75))]:key(ghost,'location',f,pos,'LINEAR')
# Prize check and 3m pole, then discarded cheque behind the hug.
check=card('Prize check','check',3,1.12,(-.15,-.3,1.2));visible(check,1668,1740)
pole=rod('Three meter award pole',(-3.2,.0,1.1),(-.2,0,1.1),.045,M['wood']);visible(pole,1668,1740)
for f,x in [(1668,-1),(1680,-1.1),(1720,.3),(1730,.2)]:key(check,'delta_location',f,(x,0,0),'LINEAR')
ignored=card('Ignored cheque on grass','check',3,1.12,(.4,1.5,.08));ignored.rotation_euler=(0,0,-.25);visible(ignored,2013,2206)
for i in range(55):
    x=random.uniform(-4,4);y=random.uniform(-1,3);z=random.uniform(4,8)
    o=cube('Victory confetti',(x,y,z),(.09,.04,.19),random.choice([M['red'],M['blue'],M['gold'],M['mint']]),0);visible(o,1668,1854)
    key(o,'location',1668,(x,y,z),'LINEAR');key(o,'location',1853,(x+.7,y,z-5));o.rotation_euler=(random.random()*3,random.random()*3,random.random()*3)
# Mint-green dimensional car and finite drift.
car=empty('Mom family car',(-12,-8,.5));visible(car,1854,2013)
cube('Car lower body',(0,0,.45),(3.8,1.6,.8),M['mint'],.28,car);cube('Car cabin',(-.25,0,1.15),(2.15,1.45,.8),M['mint'],.2,car)
for x in (-.8,.3):cube('Car side window',(x,-.74,1.23),(.85,.03,.48),M['blue'],.06,car)
for x in (-1.2,1.2):
    for y in (-.8,.8):
        o=cyl('Car tire',(x,y,.25),.41,.22,M['tire'],car);o.rotation_euler.x=math.pi/2
        o=cyl('Wheel hub',(x,y*1.13,.25),.19,.23,M['white'],car);o.rotation_euler.x=math.pi/2
for x in (-1.9,1.9):cube('Car bumper',(x,0,.34),(.13,1.35,.2),M['white'],.04,car)
for f,p in [(1854,(-12,-8,.25)),(1865,(-12.5,-8,.25)),(1900,(.4,-8,.25)),(1910,(0,-8,.25))]:key(car,'location',f,p,'LINEAR')
for f,r in [(1854,0),(1890,0),(1900,-.18),(1910,0)]:key(car,'rotation_euler',f,(0,0,r),'LINEAR')
for i in range(6):
    smoke=sphere('Tire smoke',(-2-i*.55,-7.8,.4),(.55,.4,.35),mat('Smoke '+str(i),'#fff6e7',alpha=.35));visible(smoke,1885,1920)
# Mom's roll uses the raised-hand art anchor, front fingers sit over the roll edge.
roll=empty('Right hand toilet roll socket',((835-512)*S,(1474-300)*S,.08),mbody)
o=cyl('Bright white toilet roll',(0,0,0),.23,.4,M['white'],roll);o.rotation_euler.x=math.pi/2
o=cyl('Roll cardboard core',(0,-.207,0),.075,.01,M['wood'],roll);o.rotation_euler.x=math.pi/2
cube('Paper hanging end',(.18,0,-.22),(.12,.04,.38),M['white'],.02,roll);visible(roll,1910,2013)
for i in range(8):
    a=i*math.tau/8
    ray=rod('Mom sunburst ray',(-.6+1.8*math.cos(a),-4.5,1.8+1.8*math.sin(a)),(-.6+2.4*math.cos(a),-4.5,1.8+2.4*math.sin(a)),.035,M['gold']);visible(ray,1910,2013)
for i in range(7):
    x=random.uniform(-1.8,1.4);z=random.uniform(3.2,4.7)
    t=text('Love heart','♥',(x,.4,z),.45,mat('Heart '+str(i),'#fa639e',.7));visible(t,2013,2095)
    t=text('Toilet love heart','♥',(4+random.random(),2.0,4+random.random()),.4,M['red']);visible(t,2120,2206)
# Lighting: keyed sky and Sun moods, shadow maps and grounded cast contacts.
bpy.ops.object.light_add(type='SUN',location=(0,-5,12));sun=bpy.context.object;sun.name='Four-act warm directional Sun';sun.rotation_euler=(.45,-.55,-.5);sun.data.angle=math.radians(15);sun.data.energy=4.8
for f,sky,energy,col in [(1,'#63bff5',4.8,(1,.91,.76)),(576,'#f5b68b',3.8,(1,.72,.44)),(1446,'#a77caa',2.9,(1,.48,.3)),(1668,'#8ecbf5',4.8,(1,.91,.75)),(1854,'#f5a080',3.6,(1,.62,.34))]:
    world.inputs['Color'].default_value=(*rgb(sky),1);world.inputs['Color'].keyframe_insert('default_value',frame=f)
    sun.data.energy=energy;sun.data.keyframe_insert('energy',frame=f);sun.data.color=col;sun.data.keyframe_insert('color',frame=f)
for data in (sun.data,s.world.node_tree):
    for fc in data.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.interpolation='CONSTANT'
bpy.ops.object.light_add(type='AREA',location=(0,-5,8));bpy.context.object.data.energy=450;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=10
for i in range(9):sphere('Low-poly cloud',(random.uniform(-20,20),random.uniform(16,22),random.uniform(9,13)),(2.2,1, .65),M['white'])
# Camera shot grammar, every hard cut keys location, rotation, lens and ortho scale.
shots=[(1,(0,-22,17),(0,2,1),23),(144,(0,-17,5),(0,0,1.6),6.6),(264,(.25,-16,4.4),(.25,0,1.65),5.9),(378,(0,-17,2.9),(0,-5.6,1.25),5.7),(459,(.45,-16,4),(.45,0,1.55),6),(576,(0,-16,3.2),(0,0,1.6),6.6),(732,(0,-17,4.7),(0,0,1.9),7.8),(930,(-2,-15,4),(-2,2,1.4),5.6),(965,(50,-15,7),(50,1,2.15),8.8),(1104,(0,-18,7),(0,1,1.3),14),(1299,(-.7,-17,4.8),(-.7,.2,1.7),8.6),(1446,(-.7,-17,4.4),(-.7,0,1.7),8.2),(1539,(-1.15,-16,4.7),(-1.15,0,2.05),6.5),(1668,(-1,-19,6),(-1,1,2),11),(1740,(-.6,-17,4.5),(-.6,0,1.9),7.7),(1854,(0,-23,6),(0,-8,1.2),10),(1910,(-.6,-20,3.5),(-.6,-5,1.8),7.2),(2013,(-.4,-17,4.6),(-.4,0,1.8),7.8),(2095,(4,-15,6),(4,2,2),9)]
for f,pos,target,height in shots:
    key(cam,'location',f,pos);rot=(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler();key(cam,'rotation_euler',f,rot)
    cam.data.ortho_scale=height;cam.data.keyframe_insert('ortho_scale',frame=f);cam.data.lens=45;cam.data.keyframe_insert('lens',frame=f)
    marker=s.timeline_markers.new('CUT '+str(f),frame=f);marker.camera=cam
for fc in cam.data.animation_data.action.fcurves:
    for k in fc.keyframe_points:k.interpolation='CONSTANT'
# Finite crane push, low-angle hero orbit and trauma shake (six frames).
for f,pos,target in [(70,(0,-21,15),(0,2,1.4)),(130,(0,-20,13),(0,2,1.7))]:
    key(cam,'location',f,pos,'LINEAR');key(cam,'rotation_euler',f,(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler(),'LINEAR')
for f,dx in [(312,.045),(313,-.05),(314,.04),(315,-.03),(316,.02),(317,0)]:key(cam,'delta_location',f,(dx,0,0))
for f,x in [(576,-.3),(610,-.2),(690,.3),(720,.3)]:
    pos=(x,-16,3.2);key(cam,'location',f,pos,'LINEAR' if f<690 else 'CONSTANT');key(cam,'rotation_euler',f,(Vector((0,0,1.6))-Vector(pos)).to_track_quat('-Z','Y').to_euler(),'LINEAR' if f<690 else 'CONSTANT')
# Camera-parented HUD always occupies the same top safe region; no bottom subtitles.
hudroot=empty('hud_rig',parent=cam)
for f,_,_,height in shots:key(hudroot,'scale',f,(height/10,)*3)
starts=[1,144,264,378,459,576,732,930,1104,1299,1446,1539,1668,1854,2013,1170,1230,1136]
ends=[144,264,378,459,576,732,930,1104,1136,1446,1539,1668,1854,2013,2206,1230,1299,1170]
for i,(a,b) in enumerate(zip(starts,ends)):
    o=plane('HUD pose '+str(i),5.3,1.276,image_mat('HUD '+str(i),AS/f'hud_{i}.png'),hudroot,(0,3.83,-1));visible(o,a,b)
# Compositor required by brief.
s.use_nodes=True;n=s.node_tree.nodes;n.clear();rl=n.new('CompositorNodeRLayers');g=n.new('CompositorNodeGlare');g.glare_type='FOG_GLOW';g.quality='MEDIUM';g.mix=.14;g.threshold=.85
h=n.new('CompositorNodeHueSat');h.inputs['Saturation'].default_value=1.22;h.inputs['Value'].default_value=1.06;out=n.new('CompositorNodeComposite')
for a,b in [(rl.outputs['Image'],g.inputs['Image']),(g.outputs['Image'],h.inputs['Image']),(h.outputs['Image'],out.inputs['Image'])]:s.node_tree.links.new(a,b)
audio='C:/Users/lavis/Downloads/ElevenLabs_2026-11-10T20_54_05_Viraj - Rich, Confident and Expressive_pvc_s40_sim75_v4.mp3'
seq=s.sequence_editor_create();seq.sequences.new_sound('Hindi narration • supplied source',audio,channel=1,frame_start=1)
s['audio_source_duration_seconds']=73.795875;s['authorized_stage']='15 calibration stills only';s['reference_video']='not supplied'
s['motion_review']='Pending authorized preview; stills cannot certify full-interval contacts.'
for f,v in [(1,1),(144,0),(1299,1),(1446,0),(1668,1),(1854,0)]:key(host,'scale',f,(v,v,v))
for image in bpy.data.images:
    if image.source=='FILE':image.pack()
s.frame_set(70)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'circle_challenge.blend'))
print('BUILD_COMPLETE',len(bpy.data.objects),'objects',flush=True)
exec(compile((BASE/'scripts/circle_challenge/correct.py').read_text(), 'correct.py','exec'),{})
cinematic = BASE/'scripts/circle_challenge/cinematic.py'
exec(compile(cinematic.read_text(encoding='utf-8-sig'),str(cinematic),'exec'),{})
reference = BASE/'scripts/circle_challenge/reference_v3.py'
exec(compile(reference.read_text(encoding='utf-8-sig'),str(reference),'exec'),{})
