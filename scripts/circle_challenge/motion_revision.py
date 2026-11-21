"""Motion revision for the approved v3 art direction, Blender 4.2."""
import bpy, json, math, random, sys
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT=Path('D:/remotionshorts/scripts/circle_challenge')
OUT=ROOT.parent.parent/'renders/circle_challenge'
ASSETS=OUT/'assets/motion_assets'
sys.path.insert(0,str(ROOT))
from limb_motion import track, make_rig, bake_rig, animate_walk_cycle

s=bpy.context.scene
D=bpy.data.objects
cam=s.camera
helper={}
exec((ROOT/'cinematic.py').read_text(encoding='utf-8-sig').split('# Replace checker blocks')[0],helper)
prop=helper['mesh_prop']
material=helper['material']
label=helper['label']
key=helper['key']

def empty(name,loc=(0,0,0),parent=None):
    obj=bpy.data.objects.new(name,None)
    s.collection.objects.link(obj)
    obj.parent=parent
    obj.location=loc
    return obj

def visibility(obj,start,end):
    track(obj,'scale',[(1,(0,0,0)),(start,tuple(obj.scale)),(end,(0,0,0))],'CONSTANT')

def scalar(obj,prop,values,mode='LINEAR'):
    for frame,value in values:
        owner, attr = (obj.dof, 'focus_distance') if prop=='dof.focus_distance' else (obj,prop)
        setattr(owner,attr,value)
        obj.keyframe_insert(prop,frame=frame)
    for curve in obj.animation_data.action.fcurves:
        if curve.data_path==prop:
            for point in curve.keyframe_points:
                point.interpolation=mode

def apply_camera():
    cuts=[1,144,264,378,459,576,732,930,965,1104,1299,1446,1539,1615,1668,1740,1854,1915,2013,2095,2206]
    sweep=[(-8,7),(-19,9),(15,-4),(-15,6),(24,10),(-21,10),(-17,13),(-8,9),(-10,8),(-14,12),
           (19,-12),(-17,10),(-10,8),(-16,12),(15,-10),(-11,10),(-12,8),(14,-10),(-12,10),(-17,9)]
    bases=[]
    for a in cuts[:-1]:
        s.frame_set(1910 if a==1915 else a)
        bases.append((cam.location.copy(),cam.rotation_euler.to_quaternion(),cam.data.dof.focus_distance,cam.data.lens))
    loc,rot,lenses,focus,hud_scale,hud_loc=[],[],[],[],[],[]
    prev=None
    shake=[(312,322,.095),(1010,1020,.075),(1775,1825,.024),(1885,1898,.12)]
    for i,(a,b) in enumerate(zip(cuts,cuts[1:])):
        eye,q,d,lens=bases[i]
        target=eye+q@Vector((0,0,-d))
        if a==930:
            target=Vector((-2,2,1.61))
            eye=Vector((-2.1,-.25,1.66))
            lens=43
        if a==1854:
            eye.z=1.16
            target.z=1.2
        if a==2013:
            target=Vector((-.55,0,1.55))
            eye=Vector((-.55,-5.9,2.08))
            lens=30
        if a==2095:
            eye=Vector((2.7,-8.6,4.0))
        frames=sorted(set(range(a,b,4))|{b-1}|{f for x,y,_ in shake for f in range(x,y+1) if a<=f<b})
        for f in frames:
            u=(f-a)/max(1,b-a-1)
            theta=math.radians(sweep[i][0]+(sweep[i][1]-sweep[i][0])*u)
            t=target.copy()
            if a==2013:
                t.z-=.28*u
            move=(eye-target)
            dolly=(1-.12*u) if a!=2095 else (1+.18*u)
            if a==930:
                dolly=1-.77*u**4
            if a==1854:
                car=D['Mom family car']
                loc_curves=[curve for curve in car.animation_data.action.fcurves if curve.data_path=='location']
                car_x=loc_curves[0].evaluate(f) if loc_curves else car.location.x
                t.x=car_x*.72
            p=t+Quaternion((0,0,1),theta)@move*dolly
            p.z+=.09*math.sin(math.pi*u)
            for first,last,amp in shake:
                if first<=f<=last:
                    v=(f-first)/(last-first)
                    p+=Vector((math.sin(v*math.tau*3),0,math.sin(v*math.tau*2.5)))*amp*(1-v)**2
            orientation=(t-p).to_track_quat('-Z','Y')
            if prev and orientation.dot(prev)<0:
                orientation.negate()
            prev=orientation.copy()
            distance=(t-p).length
            factor=distance*24/lens/10
            loc.append((f,tuple(p)))
            rot.append((f,tuple(orientation)))
            lenses.append((f,(lens,)))
            focus.append((f,(distance,)))
            hud_scale.append((f,(factor,)*3))
            hud_loc.append((f,(0,0,-distance+factor)))
    overlay=bpy.data.scenes['Circle Challenge HUD pass'].camera
    for camera in (cam,overlay):
        camera.animation_data_clear()
        camera.data.animation_data_clear()
        camera.rotation_mode='QUATERNION'
        camera.delta_location=(0,0,0)
        track(camera,'location',loc)
        track(camera,'rotation_quaternion',rot)
        for f,value in lenses[::1]:
            if f in cuts:
                camera.data.lens=value[0]
                camera.data.keyframe_insert('lens',frame=f)
        for curve in camera.data.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation='CONSTANT'
    scalar(cam.data,'dof.focus_distance',[(f,v[0]) for f,v in focus])
    hud=D['hud_rig']
    track(hud,'scale',hud_scale)
    track(hud,'location',hud_loc)
    for obj in (cam,overlay,hud):
        for curve in obj.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                if round(point.co.x)+1 in cuts:
                    point.interpolation='CONSTANT'

apply_camera()
ink=material('Motion plum ink',(.036,.016,.022),.22)
phone_glass=material('Phone glass cool blue',(.09,.29,.46),.12)
image_cache={}
def bind_image(obj,name):
    if name not in image_cache:
        art=bpy.data.images.load(str(ASSETS/(name+'.png')),check_existing=False)
        art.pack()
        image_cache[name]=art
    mat=obj.active_material.copy()
    obj.active_material=mat
    node=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
    node.image=image_cache[name]

def face_plates(actor,who,first,last,forced=None):
    """Select static cel plates with baked visibility curves."""
    originals=[o for o in actor.children_recursive if o.type=='MESH' and o.name.endswith('_head')]
    source=originals[0]
    base={}
    for head in originals:
        pose=head.name.removeprefix(actor.name+'_').removesuffix('_head')
        base[pose]=next(c for c in head.animation_data.action.fcurves if c.data_path=='scale')
    pool={}
    events=[]
    speech=json.loads((ASSETS/'speech.json').read_text())
    rng=random.Random(actor.name)
    blinks=set()
    f=first+rng.randint(28,53)
    while f<last:
        blinks.update((f,f+1))
        f+=rng.randint(55,85)
    old=None
    for f in range(first,last+1):
        pose=forced or next((p for p,c in base.items() if c.evaluate(f)>.5),next(iter(base)))
        if who=='operator':
            pose='press'
        if who=='you' and 1775<=f<=1835:
            pose='shout'
        suffix='head'
        if f in blinks:
            suffix='blink'
        elif (who=='rival' and 1539<=f<1615) or (who=='you' and 1775<=f<=1835):
            amp=speech[min(f-1,len(speech)-1)]
            level=0 if amp<220 else min(4,max(1,round(math.sqrt(amp/350)*1.5)))
            suffix=f'mouth{level}'
        elif who in ('you','host','rival') and any(a<=f<b for a,b in [(144,264),(378,459),(576,732),(1299,1446),(1446,1539)]):
            phase=(f//14)%4
            suffix=('head','left','head','right')[phase]
        name=f'{who}_{pose}_{suffix}'
        if not (ASSETS/(name+'.png')).exists():
            name=f'{who}_{pose}_head'
        if name!=old:
            events.append((f,name))
            old=name
    for name in set(n for _,n in events):
        obj=source.copy()
        obj.data=source.data.copy()
        obj.animation_data_clear()
        s.collection.objects.link(obj)
        obj.name=actor.name+' animated face '+name
        bind_image(obj,name)
        keys=[(1,(0,0,0))]+[(f,(1,1,1) if n==name else (0,0,0)) for f,n in events]+[(last+1,(0,0,0))]
        track(obj,'scale',keys,'CONSTANT')
    for head in originals:
        if first==1:
            head.hide_render=True
        else:
            keys=[(1,(False,)),(first,(True,)),(last+1,(False,))]
            scalar(head,'hide_render',[(f,v[0]) for f,v in keys],'CONSTANT')

you,host,rival,mom,op=[D[n] for n in ('char_you','char_youtuber','char_rival','char_mummy','char_brain_op')]
dome=D['Mounted alarm dome']
s.frame_set(1005)
press_world=dome.matrix_world.translation+Vector((0,0,.13))
# Keep the button travel attached to the original console mount.
track(dome,'delta_location',[(965,(0,0,.11)),(1000,(0,0,.11)),(1005,(0,0,0)),(1010,(0,0,0)),(1023,(0,0,.11))])
press_world.z-=.10
for actor in (you,host,rival,mom,op):
    track(actor,'delta_location',[(1,(0,0,0))])

track(you,'location',[(1,(0,0,0)),(378,(0,-5.6,0)),(459,(0,0,0)),(2013,(-.39,-.10,0)),(2095,(3.9,-.18,0)),(2103,(4.5,.47,0)),(2117,(4.5,1.55,.1)),(2120,(4.5,2,.1))])
for curve in you.animation_data.action.fcurves:
    if curve.data_path=='location':
        for point in curve.keyframe_points:
            if point.co.x<2095:
                point.interpolation='CONSTANT'
track(mom,'location',[(1,(-1.5,-4,0)),(1910,(-1.48,-4.88,0)),(1929,(-.56,-5,0)),(2013,(-.71,-.17,0)),(2095,(2.55,.23,0)),(2113,(3.0,1,0))])
for curve in mom.animation_data.action.fcurves:
    if curve.data_path=='location':
        for point in curve.keyframe_points:
            if int(point.co.x) in (1,1929,2013):
                point.interpolation='CONSTANT'
hinge=D['ToiletDoor_HINGE']
track(hinge,'rotation_euler',[(1,(0,0,0)),(2094,(0,0,0)),(2095,(0,0,-1.36)),(2118,(0,0,0)),(2205,(0,0,0))])
track(you,'scale',[(1,(1,1,1)),(1854,(0,0,0)),(2013,(1,1,1)),(2117,(0,0,0))],'CONSTANT')

samples=sorted(set(range(1,2206,4))|{2205,198,262,378,459,485,535,965,1005,1010,1104,1299,1355,1385,1445,1539,1615,1667,1745,1770,1835,1910,1929,2013,2094,2095,2117})
for actor,who in [(you,'you'),(host,'host'),(rival,'rival'),(mom,'mom'),(op,'operator')]:
    for body in actor.children_recursive:
        if body.type=='MESH' and body.name.endswith('_body'):
            pose=body.name.removeprefix(actor.name+'_').removesuffix('_body')
            if (ASSETS/f'{who}_{pose}_body.png').exists():
                bind_image(body,f'{who}_{pose}_body')
            elif who=='operator':
                bind_image(body,'operator_press_body')
    rig=make_rig(actor,(empty,prop,ink))
    if actor==host:
        animate_walk_cycle(rig,1299,1355,1/21)
        animate_walk_cycle(rig,1385,1445,1/13,True,True)
    if actor==rival:
        animate_walk_cycle(rig,1615,1667,1/13,True,True)
    if actor==mom:
        animate_walk_cycle(rig,1910,1929,1/20)
        animate_walk_cycle(rig,2095,2113,1/22)
    if actor==you:
        animate_walk_cycle(rig,2095,2117,1/18)
    def acting(f,i,a,b,k):
        sign=-1 if i%2==0 else 1
        if i<2:
            if actor==you and 378<=f<459 and i==1:
                b.y=.12+.027*math.sin(f*1.26)
                b.x=.42
            if actor==you and 485<=f<535:
                b.x=sign*.29
                k.x=sign*(.26+.045*math.sin((f-485)*.10))
            return a,b,k
        if actor==you and 198<=f<264:
            b=Vector((sign*.10,1.38+.035*math.sin(f*.48),.063))
        if actor==you and 1740<=f<1854 and i==3:
            u=max(0,min(1,(f-1745)/25))
            b=Vector((.37+.08*u,1.36+.88*u,.11))
        if actor==mom and 1910<=f<2013 and i==3:
            u=max(0,min(1,(f-1916)/28))
            b=Vector((.53+.09*u,1.12+1.24*u,.13))
        if 2013<=f<2095 and actor in (you,mom):
            u=max(0,min(1,(f-2013)/15))
            b=Vector((.27 if actor==mom else -.28,1.02+u*.71,.09+(.055 if i==3 else 0)))
        if actor==mom and 2095<=f:
            b=Vector((sign*.23,1.24,.10))
        if actor==host and 1355<=f<1385 and i==3:
            b=Vector((.04,2.13,.09))
        if actor==op:
            if 1005<=f<=1010:
                s.frame_set(f)
                b=rig['pivot'].matrix_world.inverted()@(press_world+Vector((sign*.10,0,0)))
            else:
                b=Vector((sign*(.46+.10*math.sin(f*.42)),1.85+.45*math.sin(f*.31+i),.08))
        return a,b,k
    bake_rig(rig,samples,acting)
    face_plates(actor,who,1,2205)
    if actor in (mom,you):
        tip=rig['chains'][3][2]
        if actor==you:
            mobile=prop('Articulated smartphone',(0,.045,.024),(.037,.084,.016),ink,tip)
            prop('Smartphone glass',(0,0,.017),(.027,.065,.004),phone_glass,mobile)
            # Glass is parented to the unscaled wrist tip instead of the phone block.
            glass=mobile.children[0]
            glass.parent=tip
            glass.location=(0,.045,.042)
            visibility(mobile,1740,1854)
            visibility(glass,1740,1854)
        else:
            original=D['Right hand toilet roll socket']
            original.parent=tip
            original.location=(.035,.07,.047)
            track(original,'scale',[(1,(0,0,0)),(1910,(1,1,1)),(2013,(0,0,0)),(2095,(1,1,1))],'CONSTANT')
for index in range(18):
    actor=D[f'Contestant_{index:02d}']
    rng=random.Random(index+17)
    x=(index%8-3.5)*.49+rng.uniform(-.27,.27)
    y=rng.uniform(.7,3.9)
    end_x=x*1.65+rng.uniform(-.75,.75)
    start=1104+index*2
    exit_frame=1244+index*3
    s.frame_set(1103)
    location_curves=[c for c in actor.animation_data.action.fcurves if c.data_path=='location']
    original=[(f,tuple(c.evaluate(f) for c in location_curves)) for f in (1,144,264,378,459,576,732)]
    track(actor,'location',original+[(1104,(x,y,0)),(start,(x,y,0)),(1197+index,(x*1.16,-5.6,0)),(exit_frame,(end_x,-9.7,0))])
    for curve in actor.animation_data.action.fcurves:
        if curve.data_path=='location':
            for point in curve.keyframe_points:
                if point.co.x<1104:
                    point.interpolation='CONSTANT'
    track(actor,'delta_location',[(1,(0,0,0))])
    for obj in list(actor.children_recursive):
        if obj.type=='MESH' and obj.name.endswith('_body'):
            clean=obj.copy()
            clean.data=obj.data.copy()
            clean.animation_data_clear()
            s.collection.objects.link(clean)
            clean.name=actor.name+' running torso'
            bind_image(clean,'extra_choke_body')
            visibility(clean,1104,1299)
            break
    for obj in actor.children_recursive:
        if obj.type=='MESH' and obj.name.endswith('_body'):
            scalar(obj,'hide_render',[(1,False),(1104,True),(1299,False)],'CONSTANT')
    rig=make_rig(actor,(empty,prop,ink))
    animate_walk_cycle(rig,start,exit_frame,1/(13+index%4),True)
    for upper,*_ in rig['chains']:
        visibility(upper,1104,1299)
    def gag(f,i,a,b,k):
        if i==3:
            b=Vector((.025,2.19,.105))
            k.x=.24
        if i==2:
            b.x-=.12
            b.y+=.40+.16*math.sin((f-index*3)*.29)
        return a,b,k
    bake_rig(rig,sorted(set(range(1104,1299,3))|{1298}),gag)
    face_plates(actor,'extra',1104,1298,'choke')

# Isolate the nauseous contestant in the push through to the brain set.
s.frame_set(930)
sniffer=D['Contestant_20']
existing=[c for c in sniffer.animation_data.action.fcurves if c.data_path=='location']
for f,value in [(930,(-2,2,0)),(965,(-2,2,0))]:
    key(sniffer,'location',f,value)
key(sniffer,'scale',930,(.69,)*3)
face_plates(sniffer,'extra',930,964,'sniff')
sniff_rig=make_rig(sniffer,(empty,prop,ink))
for upper,*_ in sniff_rig['chains']:
    visibility(upper,930,965)
for obj in sniffer.children_recursive:
    if obj.type=='MESH' and obj.name.endswith('_body'):
        scalar(obj,'hide_render',[(1,False),(930,True),(965,False)],'CONSTANT')
body_src=next(o for o in sniffer.children_recursive if o.type=='MESH' and o.name.endswith('_body'))
clean=body_src.copy()
clean.data=body_src.data.copy()
clean.animation_data_clear()
clean.hide_render=False
s.collection.objects.link(clean)
bind_image(clean,'extra_sniff_body')
visibility(clean,930,965)
def sniff(f,i,a,b,k):
    if i==3:
        b=Vector((.03,2.20,.12))
    return a,b,k
bake_rig(sniff_rig,[930,964],sniff)

for obj in list(s.objects):
    if obj.name.startswith(('Stomach warning','37C heat ring','Bio aura ray','Chemical sphere','Mom sunburst ray')):
        obj.hide_render=True
    if 'heart' in obj.name.lower():
        obj.hide_render=True
    if obj.name.startswith(('Rear pants stink ribbon','Toilet stink ribbon')):
        obj.hide_render=True

def wisp(name,parent,location,first,last,seed):
    mesh=bpy.data.meshes.new(name)
    verts=[]
    faces=[]
    for i in range(26):
        t=i/25
        x=.063*math.sin(t*math.tau*1.18+seed)
        width=.042*math.sin(math.pi*t)**.65+.002
        verts.extend([(x-width,0,t*.45),(x+width,0,t*.45)])
        if i:
            n=i*2
            faces.append((n-2,n-1,n+1,n))
    mesh.from_pydata(verts,[],faces)
    colors=mesh.color_attributes.new(name='Tip fade',type='FLOAT_COLOR',domain='POINT')
    for i,data in enumerate(colors.data):
        t=i//2/25
        data.color=(1,1,1,.38*(math.sin(math.pi*t)**.78))
    obj=bpy.data.objects.new(name,mesh)
    s.collection.objects.link(obj)
    obj.parent=parent
    obj.location=location
    if not bpy.data.materials.get('Lime mist with tapered alpha'):
        mat=material('Lime mist with tapered alpha',(.38,.87,.11),.32)
        mat.surface_render_method='BLENDED'
        attr=mat.node_tree.nodes.new('ShaderNodeVertexColor')
        attr.layer_name='Tip fade'
        mat.node_tree.links.new(attr.outputs['Alpha'],mat.node_tree.nodes.get('Principled BSDF').inputs['Alpha'])
    obj.data.materials.append(bpy.data.materials['Lime mist with tapered alpha'])
    visibility(obj,first,last)
    track(obj,'rotation_euler',[(f,(0,.10*math.sin(f*.12+seed),.15*math.sin(f*.075+seed))) for f in range(first,last+1,7)])
    return obj

for i in range(3):
    wisp('Short trouser vapor',you,(.18+i*.098,.15,1.28+i*.03),315,2095,i)
    wisp('Vent vapor',None,(4.22+i*.21,2.2,3.4),2118,2206,i)
wisp('Sniff close-up vapor',sniffer,(.01,-.17,1.82),930,965,0)

for i,(word,color,x) in enumerate([('H2S',(.22,.81,.06),.96),('SKATOLE',(.82,.44,.075),-1.03)]):
    root=empty(word+' floating molecule',(x,-.18,2.6))
    ball=prop(word+' painted molecule',(0,0,0),(.35,.24,.33),material(word+' gas color',color,.22),root,'sphere')
    for ex in (-.105,.105):
        prop(word+' squint eye',(ex,-.223,.072),(.054,.035,.042),ink,root,'sphere')
    prop(word+' grin',(0,-.238,-.067),(.087,.016,.041),ink,root,'sphere')
    old=D.get('Chemical label '+word)
    if old:
        old.hide_render=True
    tag=label(word+' caption',word,(x,-.47,2.2),.14,ink)
    tag.parent=root
    tag.location=(0,-.12,-.45)
    visibility(root,732,930)
    track(root,'location',[(732,(x*.5,.21,1.5)),(783,(x,-.18,2.6)),(830,(x*1.08,-.24,2.76)),(929,(x*1.22,.06,3.05))])

# A soft thermal/rumble sheen, rendered with faded translucent material.
def sheen(name,color,location,start,end,scale):
    mat=material(name+' material',color,.55)
    mat.surface_render_method='BLENDED'
    shader=mat.node_tree.nodes.get('Principled BSDF')
    coord=mat.node_tree.nodes.new('ShaderNodeTexCoord')
    distance=mat.node_tree.nodes.new('ShaderNodeVectorMath')
    distance.operation='DISTANCE'
    distance.inputs[1].default_value=(.5,.5,.5)
    mat.node_tree.links.new(coord.outputs['Generated'],distance.inputs[0])
    fade=mat.node_tree.nodes.new('ShaderNodeMapRange')
    fade.inputs['From Min'].default_value=.05
    fade.inputs['From Max'].default_value=.48
    fade.inputs['To Min'].default_value=.28
    fade.inputs['To Max'].default_value=0
    mat.node_tree.links.new(distance.outputs['Value'],fade.inputs['Value'])
    mat.node_tree.links.new(fade.outputs[0],shader.inputs['Alpha'])
    obj=prop(name,location,scale,mat,kind='cube')
    visibility(obj,start,end)
    track(obj,'delta_scale',[(f,(1+.10*math.sin(f*.36),1,1+.07*math.sin(f*.36))) for f in range(start,end+1,4)])
    return obj
sheen('Abdominal pulse glow',(1,.22,.035),(0,-.30,1.46),198,264,(.46,.034,.36))
sheen('Thermal rise',(1,.39,.085),(0,.3,1.91),732,930,(.54,.055,.75))
# Car suspension settle, wheel roll and dust trails.
car=D['Mom family car']
for child in car.children:
    if child.name.startswith(('Car tire','Wheel hub')):
        base=child.rotation_euler.copy()
        track(child,'rotation_euler',[(1854,tuple(base)),(1895,(base.x,base.y+15,base.z)),(1915,(base.x,base.y+15.6,base.z))])
track(car,'delta_rotation_euler',[(1854,(0,0,0)),(1886,(0,.018,0)),(1895,(0,-.107,0)),(1903,(0,.035,0)),(1913,(0,0,0))])
dust=material('Tire dust cream',(.80,.76,.63),.15)
dust.surface_render_method='BLENDED'
dust.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.22
s.frame_set(1885)
car_pos=car.location.copy()
for i in range(6):
    first=1870+i*4
    puff=prop('Billowing roadside dust',(car_pos.x-1.1+i*.46,-8.36,.24),(.46,.26,.29),dust,kind='sphere')
    scale=puff.scale.copy()
    track(puff,'scale',[(1,(0,0,0)),(first-1,(0,0,0)),(first,tuple(scale*.16)),(first+12,tuple(scale*1.4)),(first+28,(0,0,0))])
    track(puff,'delta_location',[(first,(0,0,0)),(first+28,(-.79,0,.81))])

heart=material('Small pink love heart',(.93,.13,.38),.35)
def floating_heart(name,loc,start,end,seed):
    mesh=bpy.data.meshes.new(name)
    coords=[(0,0,0)]
    for i in range(48):
        t=i*math.tau/48
        x=16*math.sin(t)**3
        z=13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
        coords.append((x*.008,0,z*.008))
    mesh.from_pydata(coords,[],[(0,i+1,(i+1)%48+1) for i in range(48)])
    obj=bpy.data.objects.new(name,mesh)
    s.collection.objects.link(obj)
    mesh.materials.append(heart)
    obj.location=loc
    track(obj,'scale',[(1,(0,0,0)),(start-1,(0,0,0)),(start,(.26,)*3),(start+6,(1,)*3),(end-8,(.87,)*3),(end,(0,0,0))])
    track(obj,'delta_location',[(start,(0,0,0)),(end,(seed*.22,0,1.03))])
    track(obj,'rotation_euler',[(start,(0,.22*seed,-.22)),(end,(0,-.22*seed,.26))])
for i in range(5):
    floating_heart('Hug heart',(-.64+(i-2)*.18,-.04,2.94),2024+i*9,2061+i*8,(i-2)/2)
    floating_heart('Vent heart',(4.48+(i-2)*.12,1.98,3.51),2120+i*10,2164+i*10,(i-2)/2)
if D.get('Interior toilet bowl'):
    D['Interior toilet bowl'].hide_render=True

beam=material('Golden transparent sun ray',(1,.61,.15),.7)
beam.surface_render_method='BLENDED'
beam.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.14
rays=empty('Rescue sunlight fan',(-.56,-4.3,2.1))
visibility(rays,1915,2013)
for i in range(12):
    angle=i*math.tau/12
    outer=Vector((math.cos(angle)*2.55,0,math.sin(angle)*2.55))
    width=Vector((-.15*math.sin(angle),0,.15*math.cos(angle)))
    mesh=bpy.data.meshes.new('Rescue ray mesh')
    mesh.from_pydata([(0,0,0),outer-width,outer+width],[],[(0,1,2)])
    ray=bpy.data.objects.new('Soft rescue sunlight ray',mesh)
    s.collection.objects.link(ray)
    ray.parent=rays
    ray.data.materials.append(beam)
track(rays,'rotation_euler',[(1915,(0,0,0)),(2012,(0,.35,0))])

sun=D['Four-act warm directional Sun']
sun.data.animation_data_clear()
sun.data.energy=5.2
sun.data.angle=math.radians(8)
sun.data.use_shadow=True
sun.rotation_euler=(math.radians(36),math.radians(-29),math.radians(35))
for obj in s.objects:
    if obj.type=='LIGHT' and obj.data.type=='POINT' and obj.location.x>40:
        scalar(obj.data,'energy',[(965,18),(995,30),(1005,330),(1011,75),(1021,265),(1030,65),(1042,190),(1060,38),(1104,18)])

shadow=material('Prop contact ground shading',(.012,.019,.008))
shadow.surface_render_method='BLENDED'
shadow.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.25
for x in (-1.2,1.2):
    for y in (-.79,.79):
        prop('Car tire contact shadow',(x,y,-.12),(.23,.13,.013),shadow,car,'sphere')
prop('Porta-potty base contact shadow',(4.5,2,.021),(1.02,.92,.023),shadow,kind='sphere')
s.frame_set(70)
s['motion_revision']=4
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'circle_challenge.blend'))

