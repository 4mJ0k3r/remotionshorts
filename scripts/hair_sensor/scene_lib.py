"""Project-local Blender 4.2 construction helpers; no live Blender connection."""
import bpy, bmesh, math, random, json
from pathlib import Path
from mathutils import Vector, Matrix
V=Vector
ROOT=Path(r'D:\remotionshorts');OUT=ROOT/'renders/hair_sensor';ART=OUT/'assets'
IMAGES={};MATS={}

def rgb(h):
    v=[int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4 for c in v)

def image(path):
    p=str(path)
    if p not in IMAGES:
        IMAGES[p]=bpy.data.images.load(p,check_existing=False);IMAGES[p].pack()
    return IMAGES[p]

def key(o,prop,f):o.keyframe_insert(data_path=prop,frame=f)
def linear(o):
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'

def mat(h,metal=0,rough=.55,em=0):
    k=(h,metal,rough,em)
    if k in MATS:return MATS[k]
    m=bpy.data.materials.new('Paint '+h);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb(h),1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*rgb(h),1);p.inputs['Emission Strength'].default_value=em
    MATS[k]=m;return m

def celmat(path):
    k=('cel',str(path))
    if k in MATS:return MATS[k]
    m=bpy.data.materials.new('Scene-lit cel '+Path(path).stem);m.use_nodes=True;m.surface_render_method='DITHERED'
    n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    tex=n.new('ShaderNodeTexImage');tex.image=image(path);tex.interpolation='Linear'
    p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.55;l.new(tex.outputs['Color'],p.inputs['Base Color'])
    e=n.new('ShaderNodeEmission');e.inputs[1].default_value=1;l.new(tex.outputs['Color'],e.inputs[0])
    mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.22;l.new(p.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2])
    t=n.new('ShaderNodeBsdfTransparent');a=n.new('ShaderNodeMixShader');l.new(tex.outputs['Alpha'],a.inputs[0]);l.new(t.outputs[0],a.inputs[1]);l.new(mix.outputs[0],a.inputs[2])
    o=n.new('ShaderNodeOutputMaterial');l.new(a.outputs[0],o.inputs[0]);MATS[k]=m;return m

def alpha_mat(name,h,alpha=.55):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.surface_render_method='BLENDED';n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    t=n.new('ShaderNodeBsdfTransparent');p=n.new('ShaderNodeEmission');p.inputs[0].default_value=(*rgb(h),1)
    mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=alpha;l.new(t.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);o=n.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],o.inputs[0]);return m

class Stage:
    def __init__(self,s):self.s=s
    def obj(self,name,data=None,xyz=(0,0,0),parent=None):
        o=bpy.data.objects.new(name,data);self.s.collection.objects.link(o);o.location=xyz;o.parent=parent;return o
    def mesh(self,name,bm,m,xyz=(0,0,0),parent=None):
        d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();d.update()
        if m:d.materials.append(m)
        return self.obj(name,d,xyz,parent)
    def box(self,name,xyz,dim,m,parent=None,bevel=.025):
        bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,verts=list(bm.verts),vec=dim);o=self.mesh(name,bm,m,xyz,parent)
        if bevel:
            mod=o.modifiers.new('Soft edge highlights','BEVEL');mod.width=bevel;mod.segments=2
            o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
        return o
    def ball(self,name,xyz,scale,m,parent=None):
        bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=20,v_segments=12,radius=1);o=self.mesh(name,bm,m,xyz,parent);o.scale=scale
        for p in o.data.polygons:p.use_smooth=True
        return o
    def rod(self,name,a,b,r,m,parent=None):
        a,b=V(a),V(b);delta=b-a;bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=16,radius1=r,radius2=r,depth=delta.length)
        o=self.mesh(name,bm,m,(a+b)/2,parent);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return o
    def curve(self,name,pts,r,m,parent=None,closed=False):
        d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2;d.resolution_u=12
        sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
        for v,p in zip(sp.bezier_points,pts):v.co=p;v.handle_left_type=v.handle_right_type='AUTO'
        sp.use_cyclic_u=closed;d.materials.append(m);return self.obj(name,d,parent=parent)
    def plane(self,name,w,h,m,xyz=(0,0,0),parent=None,offset_y=0):
        d=bpy.data.meshes.new(name);d.from_pydata([(-w/2,-h/2-offset_y,0),(w/2,-h/2-offset_y,0),(w/2,h/2-offset_y,0),(-w/2,h/2-offset_y,0)],[],[(0,1,2,3)])
        uv=d.uv_layers.new()
        for a,b in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):a.uv=b
        d.materials.append(m);return self.obj(name,d,xyz,parent)
    def light(self,name,kind,xyz,target,energy,h):
        d=bpy.data.lights.new(name,kind);d.energy=energy;d.color=rgb(h);o=self.obj(name,d,xyz)
        if kind!='POINT':o.rotation_euler=(V(target)-o.location).to_track_quat('-Z','Y').to_euler()
        if kind=='AREA':d.size=4
        if kind=='SUN':d.angle=math.radians(15)
        if kind=='POINT':d.shadow_soft_size=.15
        return o

def noise_material(name,h1,h2,scale=4,rough=.55,bump=.08,wood=False):
    m=mat(h1,rough=rough).copy();m.name=name;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    tc=n.new('ShaderNodeTexCoord');mp=n.new('ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(1,18,4) if wood else (1,1,1);l.new(tc.outputs['Generated'],mp.inputs[0])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=3;l.new(mp.outputs[0],noise.inputs[0])
    r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(*rgb(h1),1);r.color_ramp.elements[1].color=(*rgb(h2),1);l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])
    b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.035;l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal']);return m

def shadow(g,xyz,scale=(.25,.15,.006)):
    return g.ball('Receiver-local soft contact',xyz,scale,alpha_mat('Contact alpha .55','16222b',.55))

def world(s,disaster=False):
    w=bpy.data.worlds.new(s.name+' / gradient sky');w.use_nodes=True;s.world=w;n=w.node_tree.nodes;l=w.node_tree.links;bg=n.get('Background')
    tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Normal'],sep.inputs[0]);mp=n.new('ShaderNodeMapRange');mp.inputs['From Min'].default_value=-.5;mp.inputs['From Max'].default_value=.45;l.new(sep.outputs['Z'],mp.inputs[0])
    r=n.new('ShaderNodeValToRGB');cols=['2b5876','4e798c','c4b6a6'] if disaster else ['307da5','8fc4da','dcf0ec']
    r.color_ramp.elements[0].color=(*rgb(cols[0]),1);r.color_ramp.elements[1].color=(*rgb(cols[2]),1);r.color_ramp.elements.new(.55).color=(*rgb(cols[1]),1);l.new(mp.outputs[0],r.inputs[0]);l.new(r.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=.45 if disaster else .55

def compose(s,shot):
    s.use_nodes=True;n=s.node_tree.nodes;n.clear();l=s.node_tree.links
    a=n.new('CompositorNodeRLayers');a.scene=s
    glow=n.new('CompositorNodeGlare');glow.glare_type='FOG_GLOW';glow.threshold=.8;glow.mix=-.8;glow.quality='MEDIUM';glow.size=7;l.new(a.outputs['Image'],glow.inputs[0])
    hs=n.new('CompositorNodeHueSat');hs.inputs['Saturation'].default_value=1.18;l.new(glow.outputs[0],hs.inputs['Image'])
    ellipse=n.new('CompositorNodeEllipseMask');ellipse.width=.92;ellipse.height=.95
    blur=n.new('CompositorNodeBlur');blur.filter_type='GAUSS';blur.size_x=150;blur.size_y=250;l.new(ellipse.outputs[0],blur.inputs[0])
    ramp=n.new('CompositorNodeMapRange');ramp.inputs['To Min'].default_value=.90;ramp.inputs['To Max'].default_value=1.;l.new(blur.outputs[0],ramp.inputs['Value'])
    mult=n.new('CompositorNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;l.new(hs.outputs[0],mult.inputs[1]);l.new(ramp.outputs[0],mult.inputs[2])
    im=n.new('CompositorNodeImage');im.image=image(ART/f'hud_{shot}.png');sc=n.new('CompositorNodeScale');sc.space='RENDER_SIZE';l.new(im.outputs[0],sc.inputs[0])
    over=n.new('CompositorNodeAlphaOver');l.new(mult.outputs[0],over.inputs[1]);l.new(sc.outputs[0],over.inputs[2]);out=n.new('CompositorNodeComposite');l.new(over.outputs[0],out.inputs[0])

def new_scene(shot,start,end,disaster=False):
    s=bpy.data.scenes.new(shot);s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.use_raytracing=False;s.eevee.taa_render_samples=16
    s.render.use_simplify=True;s.render.simplify_subdivision=2;s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=50;s.render.fps=30
    s.frame_start=start;s.frame_end=end;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.film_transparent=False
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.25;s.render.use_file_extension=True
    world(s,disaster);compose(s,shot);g=Stage(s)
    g.light('Warm motivated key','AREA',(-3,-4,6),(0,0,1),650 if disaster else 500,'ffe2ac')
    g.light('Quiet blue fill','AREA',(4,0,4),(0,0,1),400 if disaster else 230,'8ed3f6')
    sun=g.light('Directional late sun','SUN',(-4,3,7),(0,0,0),2.1 if disaster else 1.6,'ffe5bd')
    return g

def camera(g,pos,target,lens=48,stop=2.4,endpos=None,endtarget=None):
    s=g.s;d=bpy.data.cameras.new(s.name+' optics');d.lens=lens;d.sensor_fit='HORIZONTAL';d.sensor_width=36;d.clip_start=.01;d.clip_end=200;d.dof.use_dof=True;d.dof.aperture_fstop=stop
    o=g.obj(s.name+' delivery camera',d,pos);s.camera=o
    focus=g.obj('Active subject focus',xyz=target);d.dof.focus_object=focus
    for f,p,t in [(s.frame_start,pos,target),(s.frame_end,endpos or pos,endtarget or target)]:
        o.location=p;o.rotation_euler=(V(t)-V(p)).to_track_quat('-Z','Y').to_euler();d.dof.focus_distance=(V(t)-V(p)).dot(o.rotation_euler.to_matrix()@V((0,0,-1)));focus.location=t
        key(o,'location',f);key(o,'rotation_euler',f);key(focus,'location',f);d.keyframe_insert('dof.focus_distance',frame=f)
    linear(o);linear(focus);s.frame_set(s.frame_start);return o

def actor(g,who,pose,expression,foot,size=1):
    s=g.s;cam=s.camera;q=cam.rotation_euler.to_quaternion();root=g.obj('char_'+who,xyz=foot)
    def point(px,py):return V(foot)+q@V(((px-512)/1024*1.8*size,(1536-py)/1536*2.7*size,0))
    # Separate full-art layer pivots preserve a shared silhouette and a stable skull.
    body=g.obj(who+' torso billboard',xyz=point(512,768));body.rotation_euler=cam.rotation_euler
    c=body.constraints.new('COPY_ROTATION');c.target=cam
    g.plane(who+' '+pose,1.8*size,2.7*size,celmat(ART/f'{who}_body_{pose}.png'),parent=body)
    head=g.obj(who+' independent head billboard',xyz=point(512,465));head.rotation_euler=cam.rotation_euler
    helper=g.obj(who+' camera parallel aim',xyz=head.location+q@V((0,0,8)))
    track=head.constraints.new('DAMPED_TRACK');track.track_axis='TRACK_Z';track.target=helper
    # Pose/expression planes use scale switching, never image swaps.
    for exp in (expression,'blink'):
        plane=g.plane(who+' expression '+exp,1.8*size,2.7*size,celmat(ART/f'{who}_head_{exp}.png'),parent=head,offset_y=(768-465)/1536*2.7*size)
        plane.scale=(1,1,1) if exp==expression else (0,0,0);key(plane,'scale',s.frame_start)
        blink=min(s.frame_end-5,s.frame_start+37)
        for f,on in [(blink,exp=='blink'),(blink+4,exp==expression)]:plane.scale=(1,1,1) if on else (0,0,0);key(plane,'scale',f)
        for fc in plane.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='CONSTANT'
    for f in (s.frame_start,s.frame_end):
        s.frame_set(f);qf=cam.rotation_euler.to_quaternion();body.location=V(foot)+qf@V((0,1.35*size,0));head.location=V(foot)+qf@V((0,(1536-465)/1536*2.7*size,0));head.rotation_euler=cam.rotation_euler
        helper.location=head.location+qf@V((0,0,8));key(body,'location',f);key(head,'location',f);key(head,'rotation_euler',f);key(helper,'location',f)
    s.frame_set(s.frame_start)
    sockets=json.loads((ART/'sockets.json').read_text())[f'{who}_{pose}']
    shadow(g,(foot[0]-.17*size,foot[1],foot[2]+.007),(.2*size,.1*size,.004));shadow(g,(foot[0]+.23*size,foot[1],foot[2]+.007),(.2*size,.1*size,.004))
    return {'root':root,'body':body,'head':head,'right':point(*sockets['right']),'left':point(*sockets['left']),'foot':V(foot)}

def coil(g,name,xyz,radius=.055,height=.36,turns=3.3,material=None,parent=None,seed=1):
    pts=[]
    for i in range(90):
        t=i/89;a=t*turns*2*math.pi+seed
        pts.append((radius*math.cos(a),radius*math.sin(a),height*t))
    o=g.curve(name,pts,.008,material or mat('241610',rough=.28),parent);o.location=xyz;return o

def tweezers(g,contact,parent=None):
    r=g.obj('Prop_Tweezers grip',xyz=contact,parent=parent);m=mat('c3d6dc',metal=.92,rough=.23)
    for sign in (-1,1):g.curve('Chrome tweezer jaw',[(sign*.011,0,0),(sign*.075,0,.27),(sign*.06,.01,.52),(0,.015,.64)],.018,m,r)
    return r

def pcb(g,xyz=(0,0,1.02),scale=1,parent=None,hero=True):
    r=g.obj('Prop_PCB_Sensor',xyz=xyz,parent=parent);r.scale=(scale,)*3
    green=mat('0e6b2e',rough=.32);gold=mat('ddba51',metal=.72,rough=.3);black=mat('192027');silver=mat('a8bac3',metal=.8)
    g.box('Green fiberglass PCB',(0,0,.025),(1.03,.65,.05),green,r,.035)
    for x in (-.44,.44):
        for y in (-.23,.23):g.rod('PCB mounting screw',(x,y,.045),(x,y,.071),.03,silver,r)
    for i in range(9):
        x=-.42+i*.10
        g.curve('Gold copper trace',[(x,-.25,.056),(x,-.08,.056),(x+.05,-.02,.056),(x+.05,.23,.056)],.005,gold,r)
    for x in (-.3,0,.3):
        g.box('Black electrode terminal',(x,0,.115),(.12,.18,.12),black,r,.012)
        g.rod('Electrode gold contact',(x,0,.17),(x,0,.188),.034,gold,r)
    for i in range(5):g.box('SMD resistor',(-.4+i*.16,-.20,.082),(.07,.032,.024),black,r,.004)
    for x in (-.38,.34):g.rod('Capacitor can',(x,.20,.06),(x,.20,.20),.047,silver,r)
    h=None
    if hero:
        # The same hero filament bridges three electrode tops.
        pts=[(-.3+.6*i/100,.055*math.sin(i/100*6*math.pi),.21+.095*(1+math.cos(i/100*6*math.pi))) for i in range(101)]
        h=g.curve('Prop_Hero_Hair wired across electrodes',pts,.008,mat('382011',rough=.28),r)
        for x in (-.3,0,.3):g.curve('Electrode bond',[(x,0,.183),(x,0,.21)],.01,gold,r)
    return r,h

def lab(g,desk=True):
    wood=noise_material('Warm walnut / long grain','6e3924','c79458',6,.25,.12,True);navy=mat('183f56');pale=mat('80adba');metal=mat('284958',metal=.4)
    g.box('Teal tile foundation',(0,1,-.10),(12,12,.16),mat('4c7f8b'),bevel=0)
    for i in range(-6,7):
        g.rod('Floor grout X',(-6,i,-.012),(6,i,-.012),.008,mat('a3c9ce'));g.rod('Floor grout Y',(i,-6,-.012),(i,6,-.012),.008,mat('a3c9ce'))
    g.box('Laboratory back wall',(0,4.4,2.2),(12,.2,4.4),pale)
    g.box('Dark teal dado',(0,4.26,.65),(12,.055,1.3),navy)
    # Real openings and bars create visible parallax and directional shadows.
    for x in (-4,-2,2,4):
        g.box('Window sill',(x,4.13,2.0),(1.5,.34,.12),mat('d4e9e7'))
        g.box('Window sky glass',(x,4.25,2.85),(1.4,.03,1.55),mat('82bdd7',rough=.22,em=.3))
        for dx in (-.72,0,.72):g.box('Window vertical mullion',(x+dx,4.08,2.85),(.065,.12,1.7),navy)
        for z in (2.02,2.84,3.68):g.box('Window horizontal mullion',(x,4.08,z),(1.52,.12,.065),navy)
    for x in (-2.8,2.8):
        g.box('Cabinet',(x,3.4,.7),(1.5,.8,1.4),mat('356a7c'))
        for z in (.3,.7,1.1):
            g.box('Cabinet drawer',(x,2.975,z),(1.35,.06,.33),mat('46899a'))
            g.rod('Brushed drawer pull',(x-.20,2.91,z),(x+.20,2.91,z),.022,mat('d4dfe2',metal=.7))
        for i in range(3):
            g.rod('Laboratory glass flask',(x-.4+i*.4,3.1,1.46),(x-.4+i*.4,3.1,1.8),.06,mat('73bdb6',rough=.16))
    if desk:
        g.box('Walnut bench top',(0,.25,1.0),(4.5,1.65,.13),wood,bevel=.055)
        g.box('Bench front apron',(0,-.48,.82),(4.3,.09,.26),wood)
        for x in (-1.95,1.95):
            for y in (-.35,.88):g.box('Bench leg',(x,y,.45),(.10,.1,.9),metal);shadow(g,(x,y,.005),(.12,.12,.004))

def monitor(g,xyz=(.1,.7,1.07)):
    r=g.obj('Desktop PC assembly',xyz=xyz);dark=mat('13232c',rough=.3)
    g.box('Monitor base',(0,.05,.04),(.75,.44,.08),dark,r)
    g.box('Monitor stand',(0,.12,.36),(.12,.12,.65),mat('9baeb5',metal=.6),r)
    g.box('Beveled desktop monitor',(0,.05,.92),(1.70,.15,1.13),dark,r,.055)
    for mode in ('wave','map'):
        tex=celmat(ART/f'monitor_{mode}.png');o=g.plane('Live monitor '+mode,1.53,.956,tex,(0,-.035,.92),r);o.rotation_euler=(math.pi/2,0,0)
        # Calibrated real content switches via scale, not texture mutation.
        for f,on in [(g.s.frame_start,mode=='wave'),(691,mode=='map')]:
            o.scale=(1,)*3 if on else (0,)*3;key(o,'scale',f)
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='CONSTANT'
    g.box('PC tower',(1.22,.17,.50),(.50,.65,1.0),mat('1d3542'),r,.04)
    for z in (.28,.45,.62):g.box('Tower vents',(1.22,-.165,z),(.34,.02,.05),mat('0e171c'),r,.008)
    g.ball('Power LED',(1.38,-.177,.83),(.024,.012,.024),mat('5df4bc',em=2),r)
    for x in range(13):
        for y in range(4):g.box('Keyboard key',(-.7+x*.10,-.45+y*.07,.12),(.082,.052,.035),mat('e1e4df'),r,.006)
    return r

def drone(g,xyz,scale=1,scanner=False):
    r=g.obj('Prop_Drone',xyz=xyz);r.scale=(scale,)*3
    carbon=mat('263944',metal=.45,rough=.28);gold=mat('d0af5f',metal=.7);silver=mat('a5b7c0',metal=.8)
    g.box('Drone central shell',(0,0,0),(.43,.36,.16),carbon,r,.07)
    for x in (-.39,.39):
        for y in (-.31,.31):
            g.rod('Carbon diagonal arm',(x*.18,y*.18,0),(x,y,.035),.037,carbon,r)
            g.rod('Brushed metal rotor motor',(x,y,.01),(x,y,.15),.075,silver,r)
            g.rod('Rotor gold collar',(x,y,.12),(x,y,.14),.08,gold,r)
            hub=g.obj('Spinning rotor spindle',xyz=(x,y,.17),parent=r)
            blade=g.box('Rotor blade',(0,0,0),(.52,.043,.012),carbon,hub,.016)
            # Finite flight-phase rotation only; the shutter blur is represented by a faint disc.
            for f,a in [(g.s.frame_start,0),(g.s.frame_end,(g.s.frame_end-g.s.frame_start)*1.8)]:hub.rotation_euler.z=a;key(hub,'rotation_euler',f)
            linear(hub);g.ball('Semi-transparent rotor sweep',(x,y,.166),(.25,.25,.003),alpha_mat('Rotor motion blur','c7dce3',.10),r)
            g.rod('Landing leg',(x*.6,y*.65,-.04),(x*.6,y*.65,-.25),.018,carbon,r)
    for x in (-.14,0,.14):g.ball('Yellow LED headlight',(x,-.193,.014),(.032,.017,.028),mat('ffcd47',em=4),r)
    p,h=pcb(g,(0,0,.17),.43,r)
    if scanner:
        lamp=g.light('Green scanner SPOT','SPOT',xyz,V(xyz)+V((0,0,-2)),110,'43ff83');lamp.parent=r;lamp.location=(0,0,-.15);lamp.rotation_euler=(0,0,0);lamp.data.spot_size=math.radians(42);lamp.data.spot_blend=.45
        for rad in (.28,.55,.84):g.curve('Ground green scanner ring',[(rad*math.cos(i*math.tau/60),rad*math.sin(i*math.tau/60),.018) for i in range(60)],.008,mat('43ee91',em=2),closed=True)
    return r,h

def ribbon(g,start,end,h='f87dae',height=.23):
    start,end=V(start),V(end);count=42;verts=[];faces=[]
    for i in range(count):
        t=i/(count-1);p=start.lerp(end,t)+V((0,.13*math.sin(t*math.tau*1.5),.16*math.sin(t*math.tau)))
        w=height*math.sin(math.pi*t)
        verts.extend([tuple(p+V((0,0,-w))),tuple(p),tuple(p+V((0,0,w)))])
        if i:
            for side in (0,1):faces.append((3*i-3+side,3*i-2+side,3*i+1+side,3*i+side))
    me=bpy.data.meshes.new('Tapered scent ribbon');me.from_pydata(verts,[],faces);o=g.obj('FX_Scent_Ribbon',me)
    colors=me.color_attributes.new(name='scent_opacity',type='FLOAT_COLOR',domain='CORNER')
    for loop in me.loops:
        idx=loop.vertex_index;t=(idx//3)/(count-1);a=.38*math.sin(math.pi*t)**.6 if idx%3==1 else 0
        colors.data[loop.index].color=(1,1,1,a)
    m=alpha_mat('Scent / faded edges and pointed tips',h,.4);n=m.node_tree.nodes;l=m.node_tree.links
    att=n.new('ShaderNodeAttribute');att.attribute_name='scent_opacity';mix=next(x for x in n if x.type=='MIX_SHADER');l.new(att.outputs['Alpha'],mix.inputs[0]);me.materials.append(m)
    for i in range(4 if h=='f87dae' else 0):
        t=(i+.5)/4;p=start.lerp(end,t)+V((0,.06*math.sin(i),.10*math.cos(i)))
        petal=g.ball('3D flower petal',p,(.032,.012,.052),mat('e88eb7',rough=.48));petal.rotation_euler=(i*.4,i*.7,i)
    return o

def rubble(g):
    random.seed(419);con=noise_material('Fractured concrete / pores','596774','b5b1a2',9,.85,.25);rust=mat('815a3f',metal=.48,rough=.7)
    g.box('Dusty earthquake ground',(0,2,-.15),(22,22,.25),noise_material('Dust ground','5f696c','c6b496',6,.95,.08),bevel=0)
    for i in range(72):
        x=random.uniform(-6,6);y=random.uniform(-1,8)
        if abs(x)<1.25 and y<2:continue
        ob=g.box('Fractured concrete slab', (x,y,random.uniform(.08,.65)),(random.uniform(.3,1.4),random.uniform(.3,1.1),random.uniform(.15,.6)),con,bevel=.04);ob.rotation_euler=(random.uniform(-.4,.4),random.uniform(-.4,.4),random.uniform(-3,3))
    for x,y,tilt in [(-4,5,.18),(3.7,6,-.18),(-.7,8,.11)]:
        r=g.obj('Tilted damaged building',xyz=(x,y,0));r.rotation_euler.y=tilt
        # Floors, columns and incomplete wall sections leave genuine voids.
        for z in (1.4,2.8,4.2,5.6):
            g.box('Broken floor plate',(0,0,z),(2.5,1.2,.19),con,r)
            for dx in (-1.1,0,1.1):g.box('Structural column',(dx,0,z-.65),(.2,.3,1.3),con,r)
            for dx in (-.65,.60):g.box('Dark recessed window',(dx,.17,z-.65),(.72,.15,.8),mat('253e49'),r,.01)
    for i in range(7):
        x=-3+i*.95;y=2.6+(i%3)*.45
        g.curve('Bent reinforcing rebar',[(x,y,.2),(x+.12,y,1.1),(x+.4,y+.1,1.4)],.018,rust)
    for i in range(4):
        beam=g.obj('Twisted steel I-beam',xyz=(-3+i*1.8,3,.6));beam.rotation_euler=(.2,.3,i*.8)
        g.box('I-beam web',(0,0,0),(1.7,.055,.24),rust,beam)
        for z in (-.13,.13):g.box('I-beam flange',(0,0,z),(1.7,.26,.045),rust,beam)
    return con
