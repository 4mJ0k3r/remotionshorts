"""Isolated frame-addressable 2.5D bathroom short; all rendered frames are text-free."""
import bpy
import json
import math
import sys
import time
from pathlib import Path
from math import sin,cos,pi
from mathutils import Vector,Matrix
from bpy.app.handlers import persistent

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from timeline import OUT,FRAMES,BOUNDS,STILLS,EXTRA_STILLS,cut
SPR=OUT/'sprites';S={}

def rgba(value):
    c=[int(value[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)

def mesh(name,verts,faces,mat=None):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    if mat:data.materials.append(mat)
    return obj

def material(name,tint,rough=.5,metal=0,emit=0,alpha=1):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    b=mat.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=rgba(tint);b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal;b.inputs['Specular IOR Level'].default_value=0 if name.startswith('Ink') else .38
    b.inputs['Emission Color'].default_value=rgba(tint);b.inputs['Emission Strength'].default_value=emit
    b.inputs['Alpha'].default_value=alpha
    if alpha<1:mat.surface_render_method='BLENDED';mat.use_transparency_overlap=False
    return mat

def plaster(name,a,b):
    mat=material(name,a,.85);n=mat.node_tree.nodes;l=mat.node_tree.links
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=32;noise.inputs['Detail'].default_value=2
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=rgba(a);ramp.color_ramp.elements[1].color=rgba(b)
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.025
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],n['Principled BSDF'].inputs['Base Color'])
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],n['Principled BSDF'].inputs['Normal'])
    return mat

def cube(name,loc,size,mat,bevel=0):
    x,y,z=(v*.5 for v in size)
    verts=[(a*x+loc[0],b*y+loc[1],c*z+loc[2]) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    o=mesh(name,verts,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edge','BEVEL');mod.width=bevel;mod.segments=2
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o

def oval(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
    o.data.transform(Matrix.Diagonal((*scale,1)));o.scale=(1,1,1)
    for p in o.data.polygons:p.use_smooth=True
    return o

def lathe(name,profile,mat,sy=1,segments=64):
    vs=[(r*cos(2*pi*j/segments),sy*r*sin(2*pi*j/segments),z) for z,r in profile for j in range(segments)]
    fs=[(i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j) for i in range(len(profile)-1) for j in range(segments)]
    o=mesh(name,vs,fs,mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def tube(name,mat,radius=.018,count=17):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=2;data.use_fill_caps=True
    sp=data.splines.new('POLY');sp.points.add(count-1)
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);data.materials.append(mat);return o

def points(o,coords):
    for p,co in zip(o.data.splines[0].points,coords):p.co=(*co,1)

def bezier(o,a,b,c):
    n=len(o.data.splines[0].points)
    a,b,c=Vector(a),Vector(b),Vector(c)
    points(o,[(1-u)**2*a+2*(1-u)*u*b+u*u*c for u in [j/(n-1) for j in range(n)]])

def line(name,a,b,r,mat):
    o=tube(name,mat,r,2);points(o,[a,b]);return o

def ring(name,center,rx,ry,mat,r=.014,vertical=False):
    o=tube(name,mat,r,65);x,y,z=center
    points(o,[(x+rx*cos(j*2*pi/64),y if vertical else y+ry*sin(j*2*pi/64),z+ry*sin(j*2*pi/64) if vertical else z) for j in range(65)])
    return o

def empty(name):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);return o

def image_material(name):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_fake_user=True
    n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(SPR/f'{name}.png'),check_existing=True)
    emit=n.new('ShaderNodeEmission');l.new(tex.outputs['Color'],emit.inputs[0])
    diffuse=n.new('ShaderNodeBsdfDiffuse');l.new(tex.outputs['Color'],diffuse.inputs[0])
    lighting=n.new('ShaderNodeMixShader');lighting.inputs[0].default_value=.28
    l.new(emit.outputs[0],lighting.inputs[1]);l.new(diffuse.outputs[0],lighting.inputs[2])
    alpha=n.new('ShaderNodeMixShader');trans=n.new('ShaderNodeBsdfTransparent');out=n.new('ShaderNodeOutputMaterial')
    l.new(tex.outputs['Alpha'],alpha.inputs[0]);l.new(trans.outputs[0],alpha.inputs[1]);l.new(lighting.outputs[0],alpha.inputs[2]);l.new(alpha.outputs[0],out.inputs['Surface'])
    m.surface_render_method='DITHERED';return m

def card(name,w,h,mat):
    o=mesh(name,[(-w/2,-h/2,0),(w/2,-h/2,0),(w/2,h/2,0),(-w/2,h/2,0)],[(0,1,2,3)],mat)
    uv=o.data.uv_layers.new()
    for i,co in enumerate(((0,0),(1,0),(1,1),(0,1))):uv.data[i].uv=co
    return o

def area(name,loc,target,power,size,tint):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=size;data.color=rgba(tint)[:3]
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);obj.location=loc
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();return obj

def bathroom():
    olive=plaster('Olive beige mineral plaster','8b8973','b4ad94')
    grout=material('Warm grout','8c826d',.82)
    tile=[plaster('Warm floor tile '+str(i),a,b) for i,(a,b) in enumerate((('a9997c','c9b99d'),('ab9e84','c4b398'),('9f947d','c3b49a')))]
    wood=material('Dark olive trim','6f6c58',.65);chrome=material('Brushed chrome','9aa1a3',.22,.80)
    cube('Floor grout',(0,0,-.045),(6,5,.08),grout)
    for i in range(12):
        for j in range(10):cube('Ceramic floor tile',(-2.75+i*.5,-2.25+j*.5,-.005),(.492,.492,.035),tile[(i+j*2)%3])
    # Recessed rear window with actual openings and structural mullions.
    for loc,size in [((-2.2,1.36,1.5),(.8,.12,3)),((.95,1.36,1.5),(3.3,.12,3)),((-1.25,1.36,.68),(1.1,.12,1.36)),((-1.25,1.36,2.71),(1.1,.12,.58))]:cube('Olive bathroom wall',loc,size,olive)
    cube('Left return wall',(-2.65,0,1.5),(.12,2.7,3),olive)
    cube('Rear baseboard',(0,1.25,.08),(5.2,.09,.14),wood)
    for x in (-1.84,-.66):cube('Window timber jamb',(x,1.31,1.88),(.10,.16,1.08),wood)
    for z in (1.35,2.42):cube('Window sill',( -1.25,1.30,z),(1.3,.21,.1),wood)
    for x in (-1.54,-1.25,-.96):cube('Window vertical bar',(x,1.31,1.9),(.035,.07,1),wood)
    cube('Window crossbar',(-1.25,1.31,1.87),(1.12,.06,.035),wood)
    sky=material('Soft daylight outside window','d7e2dc',emit=.7)
    cube('Window exterior',(-1.25,1.68,1.9),(1.16,.02,1.02),sky)
    cube('Mirror frame',(1.05,1.24,2.08),(1.0,.10,.87),chrome,.035)
    cube('Mirror muted glass',(1.05,1.18,2.08),(.91,.025,.78),material('Mirror glass','899b9a',.13,.55),.02)
    cube('Vanity cabinet',(1.25,.89,.48),(.80,.55,.94),wood,.035)
    cube('Vanity stone top',(1.25,.85,.98),(.88,.65,.08),tile[1],.035)
    soap=lathe('Soap dispenser',[(0,.07),(.18,.07),(.20,.05)],material('Amber soap','aa8d52',.22));soap.location=(1.43,.90,1.02)
    line('Soap pump',(1.43,.9,1.22),(1.34,.9,1.22),.015,chrome)
    roll=lathe('Toilet paper roll',[(0,.10),(.18,.10)],material('Unused paper roll','f5f1e6',.75));roll.location=(-1.30,.73,.93);roll.rotation_euler.y=pi/2
    line('Paper holder spindle',(-1.33,.74,.93),(-1.07,.74,.93),.025,chrome)
    area('Warm bathroom key',(-1.6,-1.8,3.1),(0,0,1.0),180,2.2,'fff0d8')
    area('Soft front fill',(2,-1.1,2.2),(0,0,.8),110,2.1,'e6edee')
    area('Golden back rim',(.2,1,2.8),(-.3,0,1.1),80,1.8,'ffe1b2')
    # A window-shaped spot adds grounded diagonal bar shadows on the floor.
    data=bpy.data.lights.new('Window diagonal key','SPOT');data.energy=95;data.spot_size=1.0;data.shadow_soft_size=.12
    lamp=bpy.data.objects.new('Window diagonal key',data);bpy.context.collection.objects.link(lamp);lamp.location=(-1.7,1.9,2.7)
    lamp.rotation_euler=(Vector((-.1,-.5,.1))-lamp.location).to_track_quat('-Z','Y').to_euler()

def toilet():
    white=material('Glazed porcelain','f8fafc',.10)
    chrome=bpy.data.materials['Brushed chrome']
    base=lathe('Contoured porcelain pedestal',[(.025,.23),(.08,.25),(.12,.22),(.42,.19),(.52,.26)],white,1.25)
    # Continuous open lip and descending inner basin; there is no cap over the bowl.
    profile=[(.43,.20),(.55,.32),(.72,.43),(.79,.46),(.83,.46),(.845,.435),(.82,.407),(.72,.365),(.61,.29),(.48,.19),(.405,.135)]
    S['bowl']=lathe('Deep open porcelain bowl',profile,white,1.34,128)
    ring('Porcelain rim highlight',(0,0,.823),.445,.596,white,.022)
    cube('Toilet cistern',(0,.66,1.04),(.68,.28,.62),white,.065)
    cube('Cistern cover',(0,.66,1.365),(.73,.32,.055),white,.025)
    oval('Flush button',(0,.66,1.398),(.065,.035,.01),chrome)
    # Hinged raised seat and lid remain behind the open bowl aperture.
    lid=oval('Raised toilet lid',(0,.60,1.15),(.46,.025,.34),white)
    ring('Raised hollow seat',(0,.51,1.17),.405,.30,white,.033,True)
    for x in (-.24,.24):line('Seat hinge',(x,.46,.84),(x,.60,.84),.027,chrome)
    water=material('Bowl water','8dbbc1',.08,emit=.05,alpha=.72)
    S['water']=mesh('Recessed water surface',[(0,0,.452)]+[(.184*cos(j*2*pi/96),.247*sin(j*2*pi/96),.452) for j in range(96)],[(0,j+1,(j+1)%96+1) for j in range(96)],water)
    S['water_rings']=[ring('Bowl water ripple',(0,0,.455),.10,.14,material('Soft foam ripple '+str(j),'d7f0ec',.3,emit=.1,alpha=.34),.003) for j in range(3)]
    S['water_mat']=water
    contact=material('Grounded contact patch','473e32',alpha=.25)
    oval('Pedestal contact shadow',(0,.03,.017),(.27,.34,.004),contact)
    S['wallwet']=mesh('Wet porcelain film',[(0,0,0)]*80,[(j*8+k,j*8+k+1,(j+1)*8+k+1,(j+1)*8+k) for j in range(9) for k in range(7)],material('Thin shimmering water film','b1e3ec',.04,emit=.06,alpha=.15))
    for j in range(10):
        z=.465+j*.032;r=bowl_radius(z)-.002
        for k in range(8):
            a=-.40+k*.114;S['wallwet'].data.vertices[j*8+k].co=(r*cos(a),1.34*r*sin(a),z)

def bowl_radius(z):
    profile=((.405,.135),(.48,.19),(.61,.29),(.72,.365),(.82,.407))
    for (za,ra),(zb,rb) in zip(profile,profile[1:]):
        if z<=zb:return ra+(rb-ra)*max(0,(z-za)/(zb-za))
    return .407

def boy():
    ink=material('Ink boy matte','141215',.96)
    S['boy_head']=card('char_sniper_boy expressive head',.94,.94,image_material('boy_relaxed_0_0'))
    S['boy_faces']={}
    for path in SPR.glob('boy_*.png'):S['boy_faces'][path.stem]=image_material(path.stem)
    S['boy_spine']=tube('Curved stick spine',ink,.026)
    S['boy_arms']=[tube('Articulated boy arm '+str(i),ink,.021) for i in range(2)]
    S['boy_legs']=[tube('Bent planted leg '+str(i),ink,.022) for i in range(2)]
    S['boy_hands']=[oval('Rounded mitten '+str(i),(0,0,0),(.033,.027,.034),ink) for i in range(2)]
    S['boy_shoes']=[oval('Grounded sole '+str(i),(0,0,.022),(.065,.11,.022),ink) for i in range(2)]
    shadow=material('Anchored foot contact','433d32',alpha=.30)
    S['boy_shadows']=[oval('Foot shadow '+str(i),(0,0,.015),(.10,.14,.003),shadow) for i in range(2)]
    S['speedlines']=card('Strain radial marker lines',1.30,1.30,image_material('speedlines'))
    S['red_arm']=tube('Swollen sore red forearm',material('Sore red arm','ff4d4d',.8,emit=.65),.038)
    S['finger']=tube('Raised index finger',ink,.010,2)
    tear=material('Glossy cartoon tears','4cceec',.08,emit=.4,alpha=.78)
    S['tears']=[tube('Attached tear stream '+str(i),tear,.009) for i in range(2)]
    S['tear_drops']=[oval('Falling tear '+str(i),(0,0,0),(.012,.010,.026),tear) for i in range(6)]
    S['boy_objects']=[S['boy_head'],S['boy_spine'],*S['boy_arms'],*S['boy_legs'],*S['boy_hands'],*S['boy_shoes'],*S['boy_shadows']]

def poop():
    brown=material('Sticky glossy brown','5c3818',.25);dark=material('Ink poop rubber hose','331d0a',.96)
    root=empty('char_poop_monster');S['poop_root']=root
    body=lathe('Glossy droplet turd',[(0,.027),(.022,.075),(.065,.101),(.115,.085),(.165,.054),(.205,.018),(.225,.001)],brown, .75,48)
    body.parent=root;body.location.z=-.105;S['poop_body']=body
    S['poop_face']=card('Monster expressive eyes and mouth',.19,.20,image_material('poop_idle'))
    S['poop_faces']={s:image_material('poop_'+s) for s in ('idle','cling','gulp','cool')}
    S['poop_arms']=[tube('Rubber hose turd arm '+str(i),dark,.009) for i in range(2)]
    S['poop_legs']=[tube('Rubber hose turd leg '+str(i),dark,.008) for i in range(2)]
    S['suckers']=[oval('Brown suction cup '+str(i),(0,0,0),(.019,.012,.019),brown) for i in range(4)]
    S['jaw']=oval('Hinged enormous lower jaw',(0,0,0),(.104,.030,.042),brown)
    S['armor']=oval('Translucent hydrophobic fat dome',(0,0,0),(.15,.13,.17),material('Glossy golden fat and mucus','ffd60a',.08,emit=.11,alpha=.42))
    S['strain_sweat']=[oval('Pressure struggle sweat '+str(i),(0,0,0),(.007,.004,.013),material('Pressure sweat '+str(i),'65cdeb',.1,emit=.3,alpha=.8)) for i in range(2)]
    S['poop_objects']=[root,body,S['poop_face'],*S['poop_arms'],*S['poop_legs'],*S['suckers'],S['jaw']]

def vessel(name,mat,rad,height):
    root=empty(name)
    body=lathe(name+' hollow container',[(0,rad*.78),(.02,rad*.86),(height,rad),(height+.01,rad*.98),(height,rad*.87),(.035,rad*.69)],mat,1,48);body.parent=root
    handle=ring(name+' curved handle',(rad,0,height*.55),rad*.55,height*.30,mat,.014,True);handle.parent=root
    return root,[body,handle]

def props():
    gold=material('Oil and ghee','e7ac2a',.15,emit=.12,alpha=.85)
    fried=material('Fried snack golden crust','b77b29',.6)
    blue=material('Blue plastic','2987c5',.24)
    silver=bpy.data.materials['Brushed chrome'];white=bpy.data.materials['Glazed porcelain']
    S['oil']=[oval('Falling golden oil droplet '+str(i),(0,0,0),(.025,.022,.046),gold) for i in range(8)]
    S['snacks']=[]
    for i in range(4):
        root=empty('Fried snack '+str(i))
        a=oval('Fried dumpling body',(0,0,0),(.047,.025,.029),fried);a.parent=root
        for j in range(4):
            crease=line('Fried crimp',(-.032+j*.020,-.022,.005),(-.032+j*.020,.022,.005),.005,fried);crease.parent=root
        S['snacks'].append(root)
    S['spoon']=empty('Ghee spoon')
    a=oval('Spoon bowl',(0,0,0),(.06,.10,.015),silver);a.parent=S['spoon']
    a=oval('Golden ghee in spoon',(0,0,.012),(.047,.082,.009),gold);a.parent=S['spoon']
    a=line('Spoon handle',(0,.07,0),(0,.34,.025),.015,silver);a.parent=S['spoon']
    S['bucket'],S['bucket_parts']=vessel('Blue water bucket',blue,.15,.23)
    S['mug'],S['mug_parts']=vessel('Blue water mug',blue,.10,.14)
    water=material('Blue pouring water','79d2e7',.08,emit=.14,alpha=.60)
    S['cascade']=mesh('Wide water cascade',[(0,0,0)]*50,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(24)],water)
    S['jet']=tube('Pale yellow liquid stream',material('Yellow liquid','f4e285',.12,emit=.18,alpha=.72),.012,33)
    S['splashes']=[oval('Impact droplet '+str(i),(0,0,0),(.009,.009,.014),S['water_mat']) for i in range(25)]
    S['paper']=mesh('White toilet paper ramp',[(0,0,0)]*50,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(24)],material('Wet toilet paper','fffdf2',.66))
    S['paper_edges']=[tube('Paper ramp soft edge '+str(i),material('Paper edge grey '+str(i),'bab8a8',.8),.0018,25) for i in range(2)]
    S['brush']=empty('White bristle toilet brush')
    a=line('Brush long white handle',(0,0,0),(0,0,.55),.014,white);a.parent=S['brush']
    a=oval('Brush bristle core',(0,0,0),(.052,.049,.070),white);a.parent=S['brush']
    bristle=material('Brush white bristle tips','d9ded8',.84)
    for i in range(28):
        a=i*2*pi/28;z=((i%5)-2)*.019
        o=line('Individual radial brush bristle',(.035*cos(a),.035*sin(a),z),(.066*cos(a),.066*sin(a),z-.010),.003,bristle);o.parent=S['brush']
    S['plate']=empty('Momos plate')
    p=lathe('White ceramic food plate',[(0,.18),(.012,.21),(.028,.23),(.042,.225),(.027,.17),(.015,.0)],white);p.parent=S['plate']
    dumpling=material('Steamed momo dough','faf4dc',.61)
    for i in range(5):
        a=i*2*pi/5;pos=(.115*cos(a),.115*sin(a),.065)
        o=oval('Steamed momo',pos,(.047,.042,.044),dumpling);o.parent=S['plate']
        for j in range(4):
            q=(pos[0]+(j-1.5)*.012,pos[1],pos[2]+.025)
            o=line('Pleated momo fold',(q[0],q[1]-.020,q[2]),(q[0],q[1]+.018,q[2]+.005),.003,white);o.parent=S['plate']
    chutney=material('Red chutney','b53521',.30)
    o=lathe('Chutney dipping cup',[(0,.045),(.045,.057),(.05,.055),(.045,.045),(.008,.036)],white);o.parent=S['plate'];o.location=(0,0,.02)
    o=oval('Red chutney dip',(0,0,.057),(.044,.044,.004),chutney);o.parent=S['plate']
    S['bite']=oval('Momo held at mouth',(0,0,0),(.047,.041,.044),dumpling)

def micro_set():
    white=plaster('Magnified ceramic porcelain','ccd8d8','f3f6ed')
    vs=[];fs=[];centers=[(-.54,.48),(-.18,.48),(.18,.48),(.54,.48),(-.54,.85),(-.18,.85),(.18,.85),(.54,.85),(-.54,1.22),(-.18,1.22),(.18,1.22),(.54,1.22)]
    for j in range(91):
        z=.20+j*1.3/90
        for i in range(121):
            x=-.90+i*1.8/120
            depth=sum(.115*math.exp(-((x-cx)**2+(z-cz)**2)/.0054) for cx,cz in centers)
            vs.append((20+x,depth,z))
    for j in range(90):
        for i in range(120):a=j*121+i;fs.append((a,a+1,a+122,a+121))
    S['micro']=mesh('Concave microscopic porcelain pores',vs,fs,white)
    for p in S['micro'].data.polygons:p.use_smooth=True
    cube('Ceramic slab cross-section',(20,.23,.85),(1.8,.23,1.3),white)
    area('Microscope warm key',(19,-2,2.6),(20,0,.8),180,2,'fff0d8')
    area('Microscope cool fill',(21,-1,1.5),(20,0,.8),110,1.6,'dfeeee')
    area('Microscope rim',(20,1,2),(20,0,.8),80,1.4,'ffe1af')
    S['glue']=empty('Tiny yellow and blue glue tube')
    yellow=material('Yellow glue tube','eac328',.4);blue=material('Blue glue tube cap','286ab5',.30)
    o=lathe('Flexible glue body',[(0,.025),(.12,.033),(.15,.020)],yellow,1,32);o.parent=S['glue']
    o=lathe('Glue nozzle',[(.145,.022),(.175,.016),(.210,.003)],blue,1,32);o.parent=S['glue']
    S['glue_drops']=[oval('Golden adhesive drop '+str(i),(0,0,0),(.018,.018,.026),material('Adhesive amber '+str(i),'dcae2d',.12,emit=.20)) for i in range(6)]

def hide(obj,hidden):
    obj.hide_render=hidden
    for child in obj.children_recursive:child.hide_render=hidden

def ease(a,b,f):
    u=max(0,min(1,(f-a)/(b-a)));return u*u*(3-2*u)

def lerp(a,b,u):return a+(b-a)*u

def pulse(a,p,b,f):return ease(a,p,f)*(1-ease(p,b,f))

def wall_anchor(z,y):
    r=bowl_radius(z)
    return Vector((r*math.sqrt(max(.001,1-(y/(1.34*r))**2))-.012,y,z))

def keep_inside_bowl(curve):
    # Keep the entire swept rubber-hose stroke on the cavity side of porcelain.
    # 12 mm centreline inset exceeds its 9 mm ink radius, including curvature.
    for p in curve.data.splines[0].points:
        limit=wall_anchor(p.co.z,p.co.y).x
        p.co.x=min(p.co.x,limit)

def camera_at(f):
    H=(-.76,-.25,1.60);P=(.26,0,.68)
    # Subshots preserve all brief action boundaries; push distance is 10%.
    specs=[
        (1,43,(-2.40,.95,2.15),(-.50,-.12,1.02),25.5),
        (43,84,(-.76,-2.05,1.70),H,37),
        (84,141,(.50,-1.25,2.50),(.06,0,.64),42),
        (141,186,(-.76,-2.05,1.70),H,37),
        (186,236,(-.76,-2.00,1.68),H,38),
        (236,306,(-.30,-.50,1.25),P,34),
        (306,346,(-.76,-2.05,1.70),H,37),
        (346,417,(.58,-.48,1.64),P,47),
        (417,618,(.90,-.80,1.85),(.18,0,.82),52),
        (618,723,(.58,-.48,1.64),P,47),
        (723,804,(.58,-.48,1.64),P,47),
        (804,849,(.58,-.48,1.64),P,47),
        (849,905,(1.1,-1.1,2.20),(.15,0,.92),52),
        (905,1083,(20,-2.8,1.2),(20,0,.85),55),
        (1083,1171,(-.76,-2.05,1.70),H,37),
        (1171,1248,(-.58,-3.05,1.85),(-.60,-.25,1.43),43),
        (1248,1362,(1.1,-1.1,2.20),(.10,0,.87),52),
        (1362,1457,(.75,-.85,1.90),(.17,-.03,.61),47),
        (1457,1539,(-.70,-2.45,1.70),(-.74,-.25,1.25),48),
        (1539,1636,(1.25,-3.0,3.20),(-.40,0,1.05),40),
    ]
    a,b,loc,target,lens=next(v for v in specs if v[0]<=f<v[1])
    u=ease(a,b-1,f);t=Vector(target);v=Vector(loc)-t
    cam=S['camera'];cam.location=t+v*(1-.10*u)
    cam.rotation_euler=(t-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
    forward=cam.rotation_euler.to_quaternion()@Vector((0,0,-1))
    cam.data.dof.focus_distance=max(.05,(t-cam.location).dot(forward))
    cam.data.dof.aperture_fstop=8 if b<=43 or a>=84 and a not in (141,186,306,1083,1171,1457) else 5.6
    S['active_subshot']=(a,b)

def pose_boy(f,c):
    q=S['camera'].rotation_euler.to_quaternion()
    upper=0
    if 186<=f<236 or 1083<=f<1171:
        start,end=(186,236) if f<236 else (1083,1171)
        upper=.008*sin(f*2.5)*ease(start,start+5,f)*(1-ease(end-5,end,f))
    H=Vector((-.76+upper,-.25,1.60));S['head_position']=tuple(H)
    head=S['boy_head'];head.location=H;head.rotation_euler=q.to_euler()
    state='relaxed'
    if f<43:state='rear'
    if 43<=f<141:state='target'
    if 141<=f<186:state='smirk'
    if 186<=f<306:state='fury'
    if 306<=f<417:state='shock'
    if 1083<=f<1171:state='vein'
    if 1171<=f<1248:state='no'
    if c==12:state='momos'
    if c==13:state='cry'
    blinkphase=f%149;blink=2 if blinkphase in (0,1) else 1 if blinkphase in (2,148) else 0
    if state=='rear':blink=0
    if state in ('fury','vein','shock','cry'):blink=0
    variant=(f//4)%2 if state=='vein' else (f//5)%2 if state=='momos' else 0
    head.data.materials[0]=S['boy_faces'][f'boy_{state}_{blink}_{variant}']
    # Narration drives the story; these reactions are not lip-synced dialogue.
    visible=c in (0,1,2,3,9,12,13)
    for o in S['boy_objects']:hide(o,not visible)
    neck=H+q@Vector((0,-.33,0));hip=Vector((-.82 if f<417 else -.76,-.25,.83 if f<417 else .59))
    spine_control=Vector((-.79+upper,-.25,1.08 if f<417 else .96))
    bezier(S['boy_spine'],hip,spine_control,neck)
    for i,side in enumerate((-1,1)):
        foot=Vector((-.76+side*.16,-.25-.025*side,.032))
        if f<43:
            lateral=Vector((-.30,.954,0))
            foot=Vector((-.86,-.26,.032))+lateral*(side*.14)+Vector((side*.035,0,0))
        bezier(S['boy_legs'][i],hip+Vector((side*.015,0,0)),(-.76+side*.12,-.23,.31),foot)
        S['boy_shoes'][i].location=foot-Vector((0,.015,.010))
        S['boy_shadows'][i].location=(foot.x,foot.y,.015)
        S['boy_shoes'][i].rotation_euler.z=-1.265 if f<43 else 0
    source=Vector((-.69,-.21,.965)) if f<417 else Vector((-.54,-.28,.88));S['stream_source']=tuple(source)
    wrists=[source+Vector((-.05,-.016,.01)),source+Vector((.025,-.01,.015))]
    elbows=[Vector((-1.02,-.34,.90)),Vector((-.41,-.32,1.01))]
    if f<43:
        lateral=Vector((-.30,.954,0))
        wrists=[source+lateral*(-.024)+Vector((0,0,.012)),source+lateral*.024+Vector((0,0,.016))]
        elbows=[hip+lateral*(-.18)+Vector((-.04,0,.28)),hip+lateral*.18+Vector((-.03,0,.28))]
    if 1171<=f<1248:
        # Finger gesture stays outside the head silhouette after an anticipation.
        u=ease(1171,1186,f);side=Vector((-.27+.015*sin((f-1186)*.30)*u,-.35,1.69))
        wrists[1]=source.lerp(side,u);elbows[1]=Vector((-.25,-.40,1.11))
    if c==12:
        plate=Vector((-.77,-.52,1.07));S['plate'].location=plate
        wrists[0]=plate+Vector((-.03,0,-.015));elbows[0]=Vector((-1.13,-.45,1.04))
        age=f-1457
        u=ease(3,19,age)*(1-ease(30,44,age)) if age<45 else ease(45,61,age)*(1-ease(72,82,age))
        pick=plate+Vector((.10,-.05,.085));mouth=H+q@Vector((.008,-.176,.055))
        wrists[1]=pick.lerp(mouth,u);elbows[1]=Vector((-.33,-.51,1.22))
        S['bite'].location=wrists[1]+q@Vector((0,0,.025));S['bite'].scale=(1-.35*u,)*3
    if c==13:
        z=.63+.047*sin((f-1539)*.62)
        center=Vector((bowl_radius(z)-.050,-.045,z))
        grip=Vector((-.10,-.36,1.08+.038*sin((f-1539)*.62)))
        S['brush'].location=center
        S['brush'].rotation_euler=(grip-center).to_track_quat('Z','Y').to_euler()
        S['brush'].scale=(1,1,(grip-center).length/.55)
        wrists[1]=grip;elbows[1]=Vector((-.39,-.59,1.15))
        S['brush_contact']=tuple(center)
        S['brush_grip_error']=(center+(S['brush'].rotation_euler.to_quaternion()@Vector((0,0,.55*S['brush'].scale.z)))-grip).length
        bezier(S['red_arm'],elbows[1],elbows[1].lerp(grip,.5)+Vector((0,-.02,.01)),grip)
        wrists[0]=Vector((-.95,-.42,.91));elbows[0]=Vector((-1.08,-.37,1.03))
    for i,side in enumerate((-1,1)):
        t=.83
        shoulder=(1-t)**2*hip+2*(1-t)*t*spine_control+t*t*neck+q@Vector((side*.013,0,0))
        bezier(S['boy_arms'][i],shoulder,elbows[i],wrists[i]);S['boy_hands'][i].location=wrists[i]
        if c==13 and i==1:
            points(S['red_arm'],[(1-u)**2*shoulder+2*(1-u)*u*elbows[i]+u*u*wrists[i] for u in [.5+j/32 for j in range(17)]])
    hide(S['finger'],not 1171<=f<1248)
    points(S['finger'],[wrists[1],wrists[1]+q@Vector((.02*sin(f*.3),.085,0))])
    hide(S['plate'],c!=12);hide(S['bite'],c!=12);hide(S['brush'],c!=13);hide(S['red_arm'],c!=13)
    active_strain=state in ('fury','vein') and (186<=f<236 or 1083<=f<1171)
    S['speedlines'].location=H+q@Vector((0,0,-.004));S['speedlines'].rotation_euler=q.to_euler();hide(S['speedlines'],not active_strain)
    for i,tear in enumerate(S['tears']):
        hide(tear,c!=13)
        sign=(-1,1)[i]
        coords=[]
        for j in range(17):
            u=j/16;local=Vector((sign*.10+.014*sin(u*5-f*.20)*u,.035-.29*u,.045))
            coords.append(H+q@local)
        points(tear,coords)
    for i,drop in enumerate(S['tear_drops']):
        hide(drop,c!=13);u=((f-1539+i*5)%22)/22
        drop.location=H+q@Vector(((-1 if i%2 else 1)*.11,-.17-.35*u,.05));drop.scale=(1-u*.85,)*3

def pose_monster(f,c):
    q=S['camera'].rotation_euler.to_quaternion();P=Vector((.265,-.015,.665));scale=1.0
    state='idle';visible=84<=f<1083 or c==11
    if 236<=f<306:state='cling'
    pressure=236<=f<306
    force1=pulse(236,247,258,f) if pressure else 0
    force2=pulse(258,269,282,f) if pressure else 0
    force3=pulse(282,293,306,f) if pressure else 0
    if pressure:
        P+=Vector((.008*(force1+force2+force3),0,-.034*force1-.060*force2-.042*force3))
        q=q@Matrix.Rotation(.12*(force1-force2+force3),4,'Z').to_quaternion()
    if 346<=f<417:state='gulp';scale=lerp(1,1.25,ease(346,401,f))
    if 723<=f<905:state='cool'
    if c==8:P=Vector((20,-.13,.83));scale=1.55;state='idle'
    if c==11:
        u=ease(1380,1451,f)
        contact=Vector((.30,0,.737)).lerp(Vector((.08,-.025,.464)),u)+Vector((0,0,.10*(1-ease(1362,1382,f))))
        normal=Vector((-.78,0,.625)).normalized()
        sink=Vector((0,0,-.26*ease(1446,1457,f)))
        P=contact+normal*.11+sink;S['paper_contact']=tuple(contact+sink)
        state='cling'
    root=S['poop_root'];root.location=P;root.scale=(scale,)*3
    root.rotation_euler=(0,.09*(force1-force2),.08*(force2-force3))
    for o in S['poop_objects']:hide(o,not visible)
    face=S['poop_face'];face.location=P+q@Vector((0,.008,(.175 if 618<=f<905 else .083)*scale));face.rotation_euler=q.to_euler();face.scale=(scale,)*3
    face.data.materials[0]=S['poop_faces'][state]
    S['poop_position']=tuple(P);S['poop_scale']=scale
    for i,side in enumerate((-1,1)):
        start=P+q@Vector((side*.069*scale,-.005,.015))
        if c==8:
            wrist=Vector((20+side*.18,.065,.85));elbow=P+q@Vector((side*.18,.09,.02))
        elif c==11:
            wrist=P+q@Vector((side*.16,.03+.025*sin(f*.5),.03));elbow=P+q@Vector((side*.20,-.04,.03))
        elif state=='cling':
            slip=pulse(248,255,268,f) if side==1 else pulse(274,281,294,f)
            wrist=wall_anchor(.790-.060*slip,.22 if side<0 else -.14)+Vector((-.032*slip,0,0))
            elbow=P+q@Vector((side*.18,.12-.035*(force1+force2),.01))
        elif state=='gulp':
            wrist=P+q@Vector((side*.16,.12,.04));elbow=P+q@Vector((side*.19,.015,.03))
        elif state=='cool':
            wrist=P+q@Vector((-side*.025,-.005,.12));elbow=P+q@Vector((side*.14,-.05,.04))
        else:
            wrist=Vector((bowl_radius(.705)-.004,side*.095,.705));elbow=P+q@Vector((side*.15,.03,.02))
        bezier(S['poop_arms'][i],start,elbow,wrist)
        if pressure:keep_inside_bowl(S['poop_arms'][i])
        S['suckers'][i].location=wrist
        S['suckers'][i].rotation_euler=(0,0,pi/2 if pressure else 0)
        hip=P+q@Vector((side*.04,-.065,.02))
        foot=Vector(S['paper_contact'])+Vector((0,side*.055,.003)) if c==11 else Vector((bowl_radius(.565)-.003,side*.075,.565)) if c!=8 else P+q@Vector((side*.10,-.15,.02))
        if pressure:foot=wall_anchor(.565 if side<0 else .550,side*.075)
        bezier(S['poop_legs'][i],hip,P+q@Vector((side*.12,-.10,.02)),foot)
        if pressure:keep_inside_bowl(S['poop_legs'][i])
        S['suckers'][i+2].location=foot
        S['suckers'][i+2].rotation_euler=(0,0,pi/2 if pressure else 0)
    jaw=S['jaw'];hide(jaw,state!='gulp')
    opening=.012 if (f//4)%2 else .047
    jaw.location=P+q@Vector((0,-.065-opening,.07));jaw.rotation_euler=q.to_euler();jaw.scale=(scale,)*3
    jaw.rotation_euler.rotate_axis('X',.20 if opening<.02 else .80)
    armor=S['armor'];armor.location=P+Vector((0,0,.02));armor.scale=(1,1,1)
    hide(armor,not 618<=f<905)
    if 618<=f<650:armor.scale=(.05+.95*ease(618,650,f),)*3
    for i,drop in enumerate(S['strain_sweat']):
        hide(drop,not pressure)
        u=((f-236+i*13)%26)/26
        drop.location=P+q@Vector(((-1 if i else 1)*.086,.075-.16*u,.095))
        drop.scale=(max(.001,sin(pi*u)),)*3

def animate_effects(f,c):
    P=Vector(S['poop_position']);q=S['camera'].rotation_euler.to_quaternion();scale=S['poop_scale']
    source=Vector(S['stream_source']);target=Vector((0,0,.455))
    # Aim transition is anchored to the actual wall target, not the face center.
    if 84<=f<141:target=target.lerp(P+q@Vector((0,.01,.07)),ease(84,111,f))
    elif 141<=f<417:target=P+q@Vector((0,.005,.075))
    if 236<=f<306:target=P+q@Vector((-.045,-.035,.045))
    if 346<=f<417:target=P+q@Vector((0,-.026,.095*scale))
    if 804<=f<849:target=P+(source-P).normalized()*.155
    jet_on=f<417 or 804<=f<849
    hide(S['jet'],not jet_on)
    S['jet'].data.bevel_depth=.026 if 236<=f<306 else .014
    control=source.lerp(target,.5)+Vector((0,0,.19 if f<141 else .10))
    bezier(S['jet'],source,control,target)
    for i,p in enumerate(S['jet'].data.splines[0].points):p.radius=1+.10*sin(i*.8-f*(1.4 if 236<=f<306 else .8))
    # No splash particles exist during the gulp: the jet terminates in the jaw.
    splash_on=84<=f<306 or 804<=f<905 or 1248<=f<1362 or 1436<=f<1457 or c==13
    splash_origin=target if f<905 else Vector((.25,0,.63)) if c==10 else Vector((.08,-.02,.46)) if c==11 else Vector(S.get('brush_contact',(.27,0,.65)))
    for i,drop in enumerate(S['splashes']):
        hide(drop,not splash_on)
        age=((f+i*3)%23)/23;a=i*2.399
        v=Vector((.14*cos(a),.14*sin(a),.22))
        drop.location=splash_origin+v*age+Vector((0,0,-.26*age*age))
        drop.scale=(max(.01,sin(pi*age)),)*3
    for i,ripple in enumerate(S['water_rings']):
        u=((f+i*13)%46)/46;ripple.scale=(.3+u,.3+u,1);hide(ripple,not splash_on)
    hide(S['wallwet'],c not in (10,11))
    for i,drop in enumerate(S['oil']):
        hide(drop,c!=4);u=((f-417+i*11)%58)/58
        drop.location=P+Vector((-.07+.13*sin(i*3),.04*cos(i*2),.41*(1-u)))
        drop.scale=(max(.01,min(1,u*7,(1-u)*8)),)*3
    for i,root in enumerate(S['snacks']):
        hide(root,c!=4);u=((f-417+i*17)%86)/86
        root.location=P+Vector((.14*sin(i*1.9),.11*cos(i*2.3),.48*(1-u)))
        root.rotation_euler=(.4+u*3.2,i+u*2,0);root.scale=(max(.01,min(1,u*6,(1-u)*7)),)*3
    hide(S['spoon'],c!=4);S['spoon'].location=P+Vector((-.17,.06,.38));S['spoon'].rotation_euler=(.7+.20*sin((f-417)*.07),-.35,-.7)
    bucket_on=849<=f<905;mug_on=c==10
    hide(S['bucket'],not bucket_on);hide(S['mug'],not mug_on)
    vessel=S['bucket'] if bucket_on else S['mug']
    vessel.location=P+Vector((-.27,.01,.44)) if bucket_on else Vector((-.12,-.02,1.12))
    tilt=ease(849,861,f) if bucket_on else ease(1248,1266,f)
    vessel.rotation_euler=(.90*tilt,.45*tilt,-.30)
    # Lip is evaluated from the same rigid transform as the open vessel.
    lip=Vector((0,-.15 if bucket_on else -.10,.22 if bucket_on else .14))
    start=vessel.location+vessel.rotation_euler.to_quaternion()@lip
    hit=P+Vector((-.08,-.10,.07)) if bucket_on else Vector((.27,-.03,.67))
    hide(S['cascade'],not(bucket_on or mug_on))
    for j in range(25):
        u=j/24;center=start.lerp(hit,u)+Vector((-.025*sin(pi*u),0,.05*sin(pi*u)))
        width=(.025+.055*u)*tilt
        for k,sign in enumerate((-1,1)):
            S['cascade'].data.vertices[j*2+k].co=center+Vector((sign*width,.012*sin(u*18-f*.9),.008*sin(u*20-f*.7)))
    S['cascade'].data.update()
    hide(S['paper'],c!=11)
    for edge in S['paper_edges']:hide(edge,c!=11)
    settle=1-ease(1362,1382,f)
    for j in range(25):
        u=j/24;center=Vector((.30,0,.737)).lerp(Vector((.08,-.025,.464)),u)+Vector((0,0,.10*settle))
        for k,sign in enumerate((-1,1)):
            S['paper'].data.vertices[j*2+k].co=center+Vector((.003*sin(u*13),sign*.075,.003*sin(u*7)))
    S['paper'].data.update()
    for k,edge in enumerate(S['paper_edges']):points(edge,[S['paper'].data.vertices[j*2+k].co for j in range(25)])
    hide(S['glue'],c!=8)
    glue=S['glue'];glue.location=P+q@Vector((-.17,.01,.025));glue.rotation_euler=(pi/2,.35,-.30)
    for i,drop in enumerate(S['glue_drops']):
        hide(drop,c!=8);u=((f-905+i*6)%36)/36
        start=glue.location+glue.rotation_euler.to_quaternion()@Vector((0,0,.21))
        end=Vector((20+(-.18 if i%2 else .18),.10,.85 if i<3 else .48))
        drop.location=start.lerp(end,u);drop.scale=(max(.01,sin(pi*u)),)*3

@persistent
def update(sc):
    if not S:return
    f=max(1,min(FRAMES,sc.frame_current));c=cut(f)
    camera_at(f);pose_boy(f,c);pose_monster(f,c);animate_effects(f,c)

def build():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE_NEXT';sc.eevee.use_raytracing=False
    if hasattr(sc.eevee,'use_fast_gi'):sc.eevee.use_fast_gi=True
    elif hasattr(sc.eevee,'use_fast_gi_approximation'):sc.eevee.use_fast_gi_approximation=True
    sc.render.use_simplify=True;sc.render.simplify_subdivision=2
    sc.render.resolution_x=1080;sc.render.resolution_y=1920;sc.render.resolution_percentage=50
    sc.render.fps=30;sc.frame_start=1;sc.frame_end=FRAMES;sc.eevee.taa_render_samples=16
    sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=rgba('a6a08a');sc.world.node_tree.nodes['Background'].inputs[1].default_value=.24
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
    bathroom();toilet();boy();poop();props();micro_set()
    data=bpy.data.cameras.new('Story camera');cam=bpy.data.objects.new('Camera',data);bpy.context.collection.objects.link(cam)
    data.sensor_fit='VERTICAL';data.sensor_height=36;data.clip_start=.005;data.clip_end=80;data.dof.use_dof=True
    sc.camera=cam;S['camera']=cam
    sc.use_nodes=True;n=sc.node_tree.nodes;l=sc.node_tree.links;n.clear()
    layer=n.new('CompositorNodeRLayers');sat=n.new('CompositorNodeHueSat');sat.inputs['Saturation'].default_value=1.15
    bloom=n.new('CompositorNodeGlare');bloom.glare_type='FOG_GLOW';bloom.threshold=.80;bloom.mix=-.82;bloom.quality='MEDIUM'
    ellipse=n.new('CompositorNodeEllipseMask');ellipse.width=1.0;ellipse.height=.98
    blur=n.new('CompositorNodeBlur');blur.filter_type='FAST_GAUSS';blur.use_relative=True;blur.factor_x=24;blur.factor_y=24
    ramp=n.new('CompositorNodeValToRGB');ramp.color_ramp.elements[0].color=(.84,.84,.84,1)
    multiply=n.new('CompositorNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
    out=n.new('CompositorNodeComposite')
    l.new(layer.outputs[0],sat.inputs['Image']);l.new(sat.outputs[0],bloom.inputs[0]);l.new(ellipse.outputs[0],blur.inputs[0]);l.new(blur.outputs[0],ramp.inputs[0]);l.new(bloom.outputs[0],multiply.inputs[1]);l.new(ramp.outputs[0],multiply.inputs[2]);l.new(multiply.outputs[0],out.inputs[0])
    bpy.app.handlers.frame_change_pre.clear();bpy.app.handlers.frame_change_pre.append(update)
    sc['project']='commode_sniper';sc['text_overlays']='NONE';sc['audio_mode']='Hindi narration, non-speaking visual reactions'
    return sc

def embed_runtime(sc):
    def encode(v):
        if isinstance(v,bpy.types.Object):return {'object':v.name}
        if isinstance(v,bpy.types.Material):v.use_fake_user=True;return {'material':v.name}
        if isinstance(v,dict):return {'pairs':[[encode(a),encode(b)] for a,b in v.items()]}
        if isinstance(v,tuple):return {'tuple':[encode(x) for x in v]}
        if isinstance(v,list):return [encode(x) for x in v]
        return v
    sc['rig_state']=json.dumps(encode(S))
    preamble='''import bpy,math,json
from math import sin,cos,pi
from mathutils import Vector,Matrix
from bpy.app.handlers import persistent
FRAMES=1635
BOUNDS=(1,84,186,306,417,618,723,804,905,1083,1248,1362,1457,1539,1636)
def cut(f):return next(i for i in range(14) if BOUNDS[i]<=f<BOUNDS[i+1])
def decode(v):
    if isinstance(v,list):return [decode(x) for x in v]
    if not isinstance(v,dict):return v
    if 'object' in v:return bpy.data.objects[v['object']]
    if 'material' in v:return bpy.data.materials[v['material']]
    if 'tuple' in v:return tuple(decode(x) for x in v['tuple'])
    return {decode(a):decode(b) for a,b in v['pairs']}
S=decode(json.loads(bpy.context.scene['rig_state']))
'''
    source=Path(__file__).read_text()
    code=preamble+source[source.index('def points('):source.index('def line(')]+source[source.index('def bowl_radius('):source.index('def boy(')]
    code+=source[source.index('def hide('):source.index('def build(')]
    code+='\nbpy.app.handlers.frame_change_pre[:]=[h for h in bpy.app.handlers.frame_change_pre if h.__name__!="update"]\nbpy.app.handlers.frame_change_pre.append(update)\nupdate(bpy.context.scene)\n'
    text=bpy.data.texts.new('commode_runtime.py');text.write(code);text.use_module=True

def main():
    phase=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
    sc=build();sc.frame_set(25)
    for image in bpy.data.images:
        if image.source=='FILE':image.pack();image.use_fake_user=True
    embed_runtime(sc)
    source=bpy.data.texts.new('build_commode_sniper.py');source.write(Path(__file__).read_text())
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'commode_sniper_v2.blend'))
    if phase=='build':return
    folder=OUT/('stills_revision2_full' if phase=='sheet' else 'frames_revision2_full');folder.mkdir(exist_ok=True)
    frames=(760,1205,1410,1590) if phase=='sheet' and 'targeted' in sys.argv else sorted(set(STILLS+EXTRA_STILLS)) if phase=='sheet' else range(1,FRAMES+1)
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=6
    started=time.time()
    for f in frames:
        dest=folder/f'f{f:04}.png'
        if phase=='preview' and dest.exists():continue
        partial=folder/f'f{f:04}.part.png';sc.frame_set(f);sc.render.filepath=str(partial)
        bpy.ops.render.render(write_still=True);partial.replace(dest)
        if phase=='sheet' or f%30==0:print(f'PROBE frame={f}/{FRAMES} elapsed={time.time()-started:.1f}s',flush=True)

if __name__=='__main__':main()

