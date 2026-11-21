"""Frame-addressable isolated EEVEE scene. Rebuilds deterministically for each phase."""
import bpy
import json
import math
import sys
import time
from pathlib import Path
from math import sin, cos, pi
from mathutils import Vector, Matrix
from bpy.app.handlers import persistent

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from timeline import OUT, FRAMES, BOUNDS, STILLS, beat
SPR=OUT/'sprites'
S={}

def color(hexval):
    values=[int(hexval[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values)+(1,)

def mesh(name,verts,faces,material):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    if material:data.materials.append(material)
    return obj

def material(name,tint,metal=0,emit=0,alpha=1):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=color(tint)
    bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=.48
    bs.inputs['Emission Color'].default_value=color(tint)
    bs.inputs['Emission Strength'].default_value=emit
    bs.inputs['Alpha'].default_value=alpha
    if alpha<1:mat.surface_render_method='BLENDED';mat.use_transparency_overlap=False
    return mat

def sandstone():
    mat=material('Carved warm sandstone','c98a5b')
    n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=13
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=color('7a4e2d')
    ramp.color_ramp.elements[1].color=color('d6ac78')
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],bs.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.035
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
    return mat

def cube(name,loc,size,mat):
    x,y,z=(v/2 for v in size)
    verts=[(a*x+loc[0],b*y+loc[1],c*z+loc[2]) for a,b,c in
           [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    return mesh(name,verts,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat)

def lathe(name,profile,mat,segments=96,rib=0):
    verts=[]
    for z,r in profile:
        for j in range(segments):
            a=2*pi*j/segments
            rr=r*(1+rib*(.5+.5*cos(12*a))**5)
            # Rounded-square ratha plan, curved tapered vertical silhouette.
            xx=rr*cos(a);yy=rr*sin(a)
            verts.append((xx,yy,z))
    faces=[]
    for i in range(len(profile)-1):
        for j in range(segments):
            a=i*segments+j;b=i*segments+(j+1)%segments
            faces.append((a,b,b+segments,a+segments))
    faces.extend([tuple(range(segments-1,-1,-1)),tuple((len(profile)-1)*segments+j for j in range(segments))])
    o=mesh(name,verts,faces,mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def curve(name,points,radius,mat):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=2
    sp=data.splines.new('POLY');sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);data.materials.append(mat)
    return o

def set_curve(obj,points):
    for p,co in zip(obj.data.splines[0].points,points):p.co=(*co,1)

def ring(name,center,radius,mat,tube=.025,vertical=True):
    x,y,z=center
    pts=[(x+radius*cos(j*2*pi/96),y if vertical else y+radius*sin(j*2*pi/96),
          z+radius*sin(j*2*pi/96) if vertical else z) for j in range(97)]
    return curve(name,pts,tube,mat)

def card_material(path,cel=True):
    mat=bpy.data.materials.new(path.stem);mat.use_nodes=True;mat.use_fake_user=True
    n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader')
    transparent=n.new('ShaderNodeBsdfTransparent');tex=n.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(path),check_existing=True);tex.interpolation='Linear'
    emission=n.new('ShaderNodeEmission');l.new(tex.outputs['Color'],emission.inputs[0])
    if cel:
        diffuse=n.new('ShaderNodeBsdfDiffuse');l.new(tex.outputs['Color'],diffuse.inputs[0])
        shading=n.new('ShaderNodeMixShader');shading.inputs[0].default_value=.28
        l.new(emission.outputs[0],shading.inputs[1]);l.new(diffuse.outputs[0],shading.inputs[2])
        source=shading.outputs[0]
    else:source=emission.outputs[0]
    l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1])
    l.new(source,mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
    mat.surface_render_method='DITHERED' if cel else 'BLENDED'
    if not cel:mat.use_transparency_overlap=False
    return mat

def card(name,w,h,mat):
    o=mesh(name,[(-w/2,-h/2,0),(w/2,-h/2,0),(w/2,h/2,0),(-w/2,h/2,0)],[(0,1,2,3)],mat)
    uv=o.data.uv_layers.new()
    for i,co in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[i].uv=co
    return o

def light(name,kind,loc,target,power,tint,size):
    data=bpy.data.lights.new(name,kind);data.energy=power;data.color=color(tint)[:3]
    if kind=='AREA':data.shape='DISK';data.size=size
    if kind=='SPOT':data.spot_size=math.radians(42);data.spot_blend=.65;data.shadow_soft_size=.2
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o

def temple():
    stone=sandstone();trim=material('Deep carved stone recess','69492e')
    gold=material('Aged bronze Neelachakra','d4a359',.78)
    shadow=material('Doorway darkness','17171a')
    cube('Plinth bottom',(0,0,.13),(5.6,4.6,.26),trim)
    for j in range(5):cube('Moulded base course', (0,0,.29+j*.12),(5.35-j*.12,4.35-j*.12,.11),stone)
    profile=[]
    for j in range(81):
        u=j/80;z=.8+8.4*u;r=.63+1.52*(1-u**1.45)
        r-=.045*(.5+.5*cos(j*pi/2))
        profile.append((z,r))
    lathe('Rekha Deula curved ribbed tower',profile,stone,rib=.115)
    # Repeated ratha offsets and bhumi courses articulate the real tower mass.
    for j in range(24):
        z=1.1+j*.335;u=(z-.8)/8.4;r=.63+1.52*(1-u**1.45)
        lathe('Bhumi carved horizontal band',[(z-.025,r+.045),(z+.025,r+.045),(z+.065,r)],trim,96,.11)
        for k in range(12):
            a=k*pi/6;r2=r*1.092
            center=(r2*cos(a),r2*sin(a),z+.16)
            # Recessed sculptural blocks, keeping geometry modest for 4GB.
            o=cube('Carved ratha relief',center,(.12,.12,.18),stone)
    for j in range(4):
        cube('Entrance stair',(0,-2.45-j*.18,.19+(3-j)*.12),(1.50,.32,.15+(3-j)*.24),stone)
    cube('Recessed entrance',(0,-2.24,1.46),(.90,.045,1.47),shadow)
    for x in (-.55,.55):cube('Sandstone jamb',(x,-2.29,1.43),(.17,.16,1.62),stone)
    cube('Entrance lintel',(0,-2.29,2.26),(1.31,.20,.21),stone)
    for j in range(6):
        z=2.40+j*.135;cube('Pidha entry crown',(0,-2.12,z),(1.55-j*.18,.75-j*.05,.11),stone)
    lathe('Neck beneath amalaka',[(9.16,.60),(9.40,.53),(9.50,.65)],trim)
    # Radially fluted amalaka crown, silhouette and grooves visible front-on.
    lathe('Fluted Amalaka crown',[(9.48,.55),(9.54,.86),(9.67,1.01),(9.79,1.02),
          (9.94,.86),(10.02,.60)],stone,192,.09)
    for z,r in [(9.53,.83),(9.93,.83),(10.02,.59)]:ring('Crown moulding',(0,0,z),r,trim,.025,False)
    lathe('Kalasha finial',[(10.01,.35),(10.10,.32),(10.19,.39),(10.37,.31),(10.48,.12),(10.59,.08)],gold)
    # Wheel sits in the front XZ plane, physically supported by the finial.
    ring('Neelachakra outer ring',(0,-.01,11.03),.61,gold,.042)
    ring('Neelachakra inner rim',(0,-.01,11.03),.52,gold,.020)
    for j in range(8):
        a=j*pi/4
        curve('Eight sacred spokes',[(.10*cos(a),-.01,11.03+.10*sin(a)),(.59*cos(a),-.01,11.03+.59*sin(a))],.024,gold)
        ring('Ornate wheel medallion',(.61*cos(a),-.01,11.03+.61*sin(a)),.060,gold,.018)
    ring('Neelachakra hub',(0,-.03,11.03),.11,gold,.035)
    S['mast']=curve('Flag mast',[(.07,-.035,10.45),(.07,-.035,12.13)],.023,gold)
    S['scan']=[]
    wire=material('Gold engineering scan','ffd700',.1,1.8)
    for j in range(8):
        z=9.30+j*.29;r=.68 if j>3 else .94
        o=ring('CAD crown grid',(0,-.01,z),r,wire,.008,False);S['scan'].append(o)
    for r in (.79,1.04,1.26):S['scan'].append(ring('Protractor ring',(0,-.19,11.03),r,wire,.006))

def cloth(name,origin,length,height,direction,mat):
    verts=[];faces=[];uvs=[]
    for i in range(33):
        u=i/32
        for j in range(17):
            v=j/16
            verts.append((direction*length*u,0,-height*v*(1-u)))
            uvs.append((1-u,v))
    for i in range(32):
        for j in range(16):
            a=i*17+j;faces.append((a,a+17,a+18,a+1))
    o=mesh(name,verts,faces,mat);o.location=origin
    uv=o.data.uv_layers.new()
    for poly in o.data.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:uv.data[li].uv=uvs[o.data.loops[li].vertex_index]
    S.setdefault('cloth',[]).append((o,length,height,direction))
    return o

def actor(role,x,y):
    body=card('char_'+role+'_body',.69,.85,card_material(SPR/f'{role}_body.png'))
    head=card('char_'+role+'_head',.94,.94,card_material(SPR/f'{role}_0_0.png'))
    mats={(m,b):card_material(SPR/f'{role}_{m}_{b}.png') for m in range(4) for b in range(3)}
    ink=material(role+' matte stick ink','261f26')
    limbs=[curve(role+'_arm_'+str(j),[(0,0,0)]*13,.020,ink) for j in range(2)]
    legs=[curve(role+'_leg_'+str(j),[(0,0,0)]*3,.018,ink) for j in range(2)]
    hands=[]
    for j in range(2):
        o=lathe(role+'_mitten',[(0,.028),(.045,.028)],ink,16);hands.append(o)
    soles=[]
    for j in range(2):
        o=lathe(role+'_sole_shadow',[(.011,.095),(.012,.095)],material(role+' grounded shadow','101217',alpha=.33),32)
        o.scale=(1,.45,1);soles.append(o)
    result=dict(role=role,x=x,y=y,body=body,head=head,mats=mats,arms=limbs,legs=legs,hands=hands,soles=soles)
    S.setdefault('actors',[]).append(result)
    return result

def ribbons():
    white=material('White cyan tapered sea stream','8ce5fa',emit=3.2,alpha=.54)
    red=material('Crimson reverse eddy ribbon','ff4946',emit=4.2,alpha=.55)
    orange=material('Golden return-flow tracer','ff9e00',emit=4.2,alpha=.70)
    S['streams']=[];S['eddies']=[];S['particles']=[]
    for i in range(18):
        obj=mesh('Sea streamline '+str(i),[(0,0,0)]*50,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(24)],white)
        S['streams'].append(obj)
    for i in range(8):
        obj=mesh('Reverse eddy '+str(i),[(0,0,0)]*82,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(40)],red if i%2 else orange)
        S['eddies'].append(obj)
    for i in range(70):
        o=mesh('Wind tracer '+str(i),[(0,0,0)]*4,[(0,1,2,3)],white if i<40 else orange)
        S['particles'].append(o)
    violet=card_material(SPR/'wake.png',False)
    S['wake']=card('Illustrative low pressure pocket',2.5,1.5,violet)
    S['wake'].location=(.95,.44,11.85);S['wake'].rotation_euler=(pi/2,0,0)

def smooth(a,b,f):
    u=max(0,min(1,(f-a)/(b-a)));return u*u*(3-2*u)

def mix(a,b,u):return a+(b-a)*u

def camera_pose(f):
    b=beat(f);u=smooth(BOUNDS[b],BOUNDS[b+1]-1,f)
    # All camera centres remain exactly on X=0, facing the front +Y axis.
    pairs=[((-4.2,11.45,10.98),(-3.4,11.40,10.98)),
           ((-3.4,11.40,10.98),(-4.5,11.55,10.9)),
           ((-2.25,1.45,1.00),(-2.02,1.47,1.02)),
           ((-4.0,1.5,2.6),(-14.5,6.2,6.0)),
           ((-14.5,6.2,6.0),(-3.6,11.4,10.8)),
           ((-4.0,11.4,10.65),(-3.8,11.4,10.65)),
           ((-4.5,12.2,10.92),(-4.1,12.08,10.92)),
           ((-4.1,12.08,10.92),(-3.85,11.95,10.92)),
           ((-2.75,1.5,1.12),(-4.1,11.45,10.98)),
           ((-4.1,11.45,10.98),(-4.2,11.45,10.98))]
    if b==4:
        u=smooth(786,970,f)
    if b==8:
        u=smooth(1815,1940,f)
    a,c=pairs[b];y,z,t=(mix(a[i],c[i],u) for i in range(3))
    target_y=0
    if b==2:y-=3.2;target_y=-3.2
    if b==3:y-=3.2*(1-u)
    if b==8:y-=3.2*(1-u);target_y=-3.2*(1-u)
    cam=S['camera'];cam.location=(0,y,z)
    cam.rotation_euler=(Vector((0,target_y,t))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.lens=mix(20,33,u) if b==3 else mix(33,20,u) if b==4 else 20

def pose_actor(a,f,b):
    # Actors inhabit a grounded foreground stage. They never move to chase camera.
    x,y=a['x'],a['y'];q=S['camera'].rotation_euler.to_quaternion()
    visible=b==8 or b==2 and a['role']=='host'
    for o in [a['body'],a['head'],*a['arms'],*a['legs'],*a['hands'],*a['soles']]:o.hide_render=not visible
    a['body'].location=(x,y,.85);a['head'].location=(x,y-.018,1.51)
    a['body'].rotation_euler=q.to_euler();a['head'].rotation_euler=q.to_euler()
    blinkphase=(f+(0 if a['role']=='host' else 39))%137
    blink=2 if blinkphase in (0,1) else 1 if blinkphase in (2,136) else 0
    mouth=round(S['env'][min(FRAMES-1,f-1)]*3) if a['role']=='host' and b==2 else 0
    a['head'].data.materials[0]=a['mats'][(mouth,blink)]
    for side,leg,sole in zip((-1,1),a['legs'],a['soles']):
        points=[(x+side*.13,y,.55),(x+side*.145,y,.29),(x+side*.17,y-.02,.05)]
        set_curve(leg,points);sole.location=(x+side*.17,y-.02,0)
    point=smooth(1688,1708,f) if b==8 else 0
    for i,side in enumerate((-1,1)):
        shoulder=Vector((x+side*.16,y-.018,1.09))
        if a['role']=='host' and side==1 and b==2:
            wrist=Vector((x+.44,y-.05,1.17));elbow=Vector((x+.40,y-.04,.91))
        elif b==8 and side==(-1 if a['role']=='host' else 1):
            wrist=Vector((x+side*.49,y-.05,mix(.73,1.77,point)));elbow=Vector((x+side*.62,y-.04,1.20))
        else:
            wrist=Vector((x+side*.33,y-.05,.69));elbow=Vector((x+side*.39,y-.04,.91))
        pts=[]
        for j in range(13):
            u=j/12;pts.append((1-u)**2*shoulder+2*(1-u)*u*elbow+u*u*wrist)
        set_curve(a['arms'][i],pts);a['hands'][i].location=wrist-Vector((0,0,.020))
    if a['role']=='host':
        # Portable test pole owns a grip anchor coincident with his right mitten.
        grip=Vector((x+.44,y-.05,1.17))
        S['bluepole'].location=grip
        S['blueflag'].location=grip+Vector((0,0,.55))

@persistent
def update(scene):
    if not S:return
    f=scene.frame_current;b=beat(max(1,min(FRAMES,f)))
    camera_pose(f)
    for a in S['actors']:pose_actor(a,f,b)
    for o,L,H,direction in S['cloth']:
        for i in range(33):
            u=i/32
            for j in range(17):
                v=j/16;x=direction*L*u
                # phase travels away from the pinned mast; amplitude vanishes there.
                loop=(f-1)*2*pi/FRAMES
                wave=.13*u*sin(12*u-158*loop)+.055*u*cos(23*u-264*loop)
                z=-H*v*(1-u)+.065*u*sin(16*u-211*loop)
                o.data.vertices[i*17+j].co=(x,wave,z)
        o.data.update()
    S['blueflag'].hide_render=b!=2;S['bluepole'].hide_render=b!=2
    S['scarf'].hide_render=b!=8
    # Secondary motion is physical cloth/air, not idle skull or body wobble.
    for j,v in enumerate(S['scarf'].data.vertices):
        u=(j//2)/24;edge=j%2
        v.co=(.75*u,.065*u*sin(u*12-f*.42),-.11*edge+.065*u*sin(u*9-f*.31))
    S['scarf'].data.update()
    reveal=smooth(1010,1060,f);eddy=smooth(1205,1270,f) if f<1992 else 1
    if f<1044:eddy=0
    eddy*=1-smooth(2160,2211,f)
    for i,obj in enumerate(S['streams']):
        stage=b in (2,8) and (b==2 or f<1816)
        zbase=(.35+i*.105) if stage else (8.45+i*.225)
        phase=(((f-1)*56/FRAMES+i*.619)%8)-4
        for j in range(25):
            t=j/24;x=phase+(t-.5)*1.65
            z=zbase+.10*sin(x*1.9+i)
            if not stage and b>=5:z+=.65*reveal*math.exp(-((x+.45)/1.05)**2)
            width=.012*sin(pi*t)
            stream_y=-3.0 if stage else -.30-i*.002
            for edge in range(2):obj.data.vertices[2*j+edge].co=(x,stream_y,z+(1 if edge else -1)*width)
        obj.data.update()
        obj.hide_render=(stage and i%2==1)
    for i,obj in enumerate(S['eddies']):
        obj.hide_render=eddy==0 or (b==8 and f<1816)
        for j in range(41):
            t=j/40;a=2*pi*t+i*.35-f*.038
            cx=.70+.10*sin(i*1.7);rz=.40+.06*(i%3);rx=1.30+.06*(i%2)
            x=cx+rx*cos(a);z=12.00+rz*sin(a)
            # Upper branch flows right, lower branch left towards the flag.
            width=.012*sin(pi*t)*eddy
            for edge in range(2):obj.data.vertices[2*j+edge].co=(x,.17+i*.018,z+(1 if edge else -1)*width)
        obj.data.update()
    for i,obj in enumerate(S['particles']):
        reverse=i>=40;obj.hide_render=reverse and (eddy==0 or (b==8 and f<1816))
        if reverse:
            j=i-40;a=(-(f-1)*2*pi*19/FRAMES+j*2.399)% (2*pi)
            x=.70+(1.30+.08*sin(j))*cos(a);z=12.00+(.44+.05*cos(j))*sin(a)
            dx,dz=.065*sin(a),-.027*cos(a);y=.10
        else:
            x=(((f-1)*128/FRAMES+i*.487)%8)-4
            z=(.36+(i%16)*.10) if b in (2,8) and (b==2 or f<1816) else 8.3+(i%19)*.22
            z+=.09*sin(x*1.3+i);dx,dz=.065,0
            y=-3.0 if b in (2,8) and (b==2 or f<1816) else -.40
        for j,co in enumerate([(x-dx,y,z-dz-.008),(x+dx,y,z+dz-.008),(x+dx,y,z+dz+.008),(x-dx,y,z-dz+.008)]):obj.data.vertices[j].co=co
        obj.data.update()
    S['wake'].hide_render=not (b in (6,7) or b==8 and f>=1816)
    S['wake'].scale=(1+.025*sin(f*.08),1+.02*cos(f*.07),1)
    for obj in S['scan']:
        obj.hide_render=b!=1
        obj.scale=(1+.018*sin(f*.10),)*3
    S['key'].data.energy=650
    S['fill'].data.energy=150 if b<5 else 210

def build():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE_NEXT';sc.eevee.use_raytracing=False
    if hasattr(sc.eevee,'use_fast_gi'):sc.eevee.use_fast_gi=True
    elif hasattr(sc.eevee,'use_fast_gi_approximation'):sc.eevee.use_fast_gi_approximation=True
    sc.render.use_simplify=True;sc.render.simplify_subdivision=2
    sc.render.resolution_x=1080;sc.render.resolution_y=1920;sc.render.resolution_percentage=50
    sc.render.fps=30;sc.frame_start=1;sc.frame_end=FRAMES
    sc.eevee.taa_render_samples=16
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
    sc.world.color=(.002,.002,.003);sc.world.use_nodes=True
    sc.world.node_tree.nodes['Background'].inputs[0].default_value=color('0b0b0e')
    sc.world.node_tree.nodes['Background'].inputs[1].default_value=.15
    temple()
    floor=material('Diagnostic dark stage','171c23')
    cube('Ground support',(0,0,-.045),(60,60,.06),floor)
    mistmat=card_material(SPR/'mist.png',False)
    for x in (-2.2,0,2.2):
        mist=card('Soft base mist',4.6,1.35,mistmat)
        mist.location=(x,-2.4,.54);mist.rotation_euler=(pi/2,0,0)
    # Ground characters stand in front of, rather than inside, the temple base.
    actor('host',-.44,-3.20);actor('pilgrim',.43,-3.20)
    red=card_material(SPR/'temple_flag.png',False)
    S['templeflag']=cloth('Patitapabana Bana',(.07,-.07,12.02),1.63,.78,-1,red)
    blue=material('Blue test flag','279bdf',emit=.34)
    S['blueflag']=cloth('Normal blue test flag',(0,0,0),.47,.30,1,blue)
    S['bluepole']=curve('Hand-held test mast',[(0,0,-.08),(0,0,.59)],.012,material('Test mast','bcb5a5',.5))
    scarfmat=material('Flowing yellow pilgrim scarf','ffd344',emit=.25)
    S['scarf']=mesh('Yellow dupatta',[(0,0,0)]*50,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(24)],scarfmat)
    S['scarf'].location=(.57,-3.24,1.23)
    ribbons()
    S['key']=light('Overhead spot key','SPOT',(-1.9,-3.5,15),(0,0,9),650,'fff3d6',0)
    light('Golden crown rim','AREA',(2.5,1.8,12),(0,0,9.7),1050,'ffd184',4)
    S['fill']=light('Cool cyan front fill','AREA',(-3,-4,8),(0,0,6.2),150,'88bdd5',5)
    light('Ground stage softbox','AREA',(-1,-5,3.3),(0,-3,1),155,'fff3d6',3)
    light('Tower long warm key','AREA',(-3,-4,7),(0,0,5.6),750,'ebc793',5)
    data=bpy.data.cameras.new('Strict front camera');cam=bpy.data.objects.new('Camera',data)
    bpy.context.collection.objects.link(cam);sc.camera=cam;S['camera']=cam
    data.type='PERSP';data.lens=20;data.sensor_fit='VERTICAL';data.sensor_height=36;data.clip_end=150
    data.dof.use_dof=False
    S['env']=json.loads((OUT/'audio_envelope.json').read_text())
    # Wide front ground shots use the same front axis, shifted Y enough to see actors.
    sc.use_nodes=True;n=sc.node_tree.nodes;l=sc.node_tree.links;n.clear()
    layers=n.new('CompositorNodeRLayers');sat=n.new('CompositorNodeHueSat');sat.inputs['Saturation'].default_value=1.18
    bloom=n.new('CompositorNodeGlare');bloom.glare_type='FOG_GLOW';bloom.quality='MEDIUM';bloom.threshold=.75;bloom.mix=-.76
    vignette=n.new('CompositorNodeEllipseMask');vignette.width=.95;vignette.height=.96
    blur=n.new('CompositorNodeBlur');blur.filter_type='FAST_GAUSS';blur.use_relative=True;blur.factor_x=22;blur.factor_y=22
    ramp=n.new('CompositorNodeValToRGB');ramp.color_ramp.elements[0].color=(.78,.78,.78,1);ramp.color_ramp.elements[1].color=(1,1,1,1)
    multiply=n.new('CompositorNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
    comp=n.new('CompositorNodeComposite')
    l.new(layers.outputs['Image'],sat.inputs['Image']);l.new(sat.outputs[0],bloom.inputs[0])
    l.new(vignette.outputs[0],blur.inputs[0]);l.new(blur.outputs[0],ramp.inputs[0])
    l.new(bloom.outputs[0],multiply.inputs[1]);l.new(ramp.outputs[0],multiply.inputs[2]);l.new(multiply.outputs[0],comp.inputs[0])
    bpy.app.handlers.frame_change_pre.clear();bpy.app.handlers.frame_change_pre.append(update)
    sc['project']='puri_flag_physics';sc['science_note']='Illustrative recirculation model, not site-validated CFD. Wheel size in narration unverified.'
    return sc

def embed_runtime(scene):
    # Self-contained, opt-in Blender text module preserves the procedural rig.
    # It only edits this loaded scene; it has no filesystem/network operations.
    def encode(value):
        if isinstance(value,bpy.types.Object):return {'object':value.name}
        if isinstance(value,bpy.types.Material):return {'material':value.name}
        if isinstance(value,dict):return {'pairs':[[encode(k),encode(v)] for k,v in value.items()]}
        if isinstance(value,tuple):return {'tuple':[encode(v) for v in value]}
        if isinstance(value,list):return [encode(v) for v in value]
        return value
    scene['procedural_rig_state']=json.dumps(encode(S))
    preamble='''import bpy, json, math
from math import sin, cos, pi
from mathutils import Vector
from bpy.app.handlers import persistent
FRAMES=2211
BOUNDS=(1,183,356,555,786,1044,1236,1488,1674,1992,2212)
def beat(f):
    return next(i for i in range(10) if BOUNDS[i]<=f<BOUNDS[i+1])
def decode(value):
    if isinstance(value,list):return [decode(v) for v in value]
    if not isinstance(value,dict):return value
    if 'object' in value:return bpy.data.objects[value['object']]
    if 'material' in value:return bpy.data.materials[value['material']]
    if 'tuple' in value:return tuple(decode(v) for v in value['tuple'])
    return {decode(k):decode(v) for k,v in value['pairs']}
S=decode(json.loads(bpy.context.scene['procedural_rig_state']))
'''
    source=Path(__file__).read_text()
    code=preamble+source[source.index('def set_curve('):source.index('def ring(')]
    code+=source[source.index('def smooth('):source.index('def build(')]
    code+='\nbpy.app.handlers.frame_change_pre[:]=[h for h in bpy.app.handlers.frame_change_pre if h.__name__!="update"]\nbpy.app.handlers.frame_change_pre.append(update)\nupdate(bpy.context.scene)\n'
    text=bpy.data.texts.new('puri_procedural_runtime.py');text.write(code);text.use_module=True
    scene['rig_playback']='Allow trusted text execution or run puri_procedural_runtime.py for animated cloth, flow, camera and cast.'

def main():
    phase=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
    OUT.mkdir(exist_ok=True,parents=True);sc=build()
    # Ground camera cannot be behind the actors at Y=-3.2; all shots stay front.
    sc.frame_set(80)
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    source=bpy.data.texts.new('build_puri_flag_physics.py');source.write(Path(__file__).read_text())
    embed_runtime(sc)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'puri_flag_physics.blend'))
    if phase=='build':return
    frames=STILLS if phase=='sheet' else range(1,FRAMES+1)
    folder=OUT/('stills_v1' if phase=='sheet' else 'frames_preview');folder.mkdir(exist_ok=True)
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=12
    t0=time.time()
    for f in frames:
        target=folder/f'f{f:04}.png'
        if phase=='preview' and target.exists():continue
        partial=folder/f'f{f:04}.part.png'
        sc.frame_set(f);sc.render.filepath=str(partial)
        bpy.ops.render.render(write_still=True)
        partial.replace(target)
        print(f'PROBE frame={f} elapsed={time.time()-t0:.1f}s',flush=True)

if __name__=='__main__':main()
