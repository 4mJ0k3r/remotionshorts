"""V3 production helpers. Reuse only project-local mesh primitives."""
import bpy,bmesh,math,random,json
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
import scene_lib as old
from scene_lib import Stage,mat,noise_material,rgb,key,linear,V
OUT=old.OUT;ART=OUT/'assets_v3';CACHE={};CONTACTS=[]
AUDIO=json.loads((OUT/'audio_analysis.json').read_text())['rms']
PEAK=max(AUDIO)

def picture(path,lit=True):
    k=(str(path),lit)
    if k in CACHE:return CACHE[k]
    m=bpy.data.materials.new('V3 '+Path(path).stem);m.use_nodes=True;m.surface_render_method='DITHERED' if lit else 'BLENDED';n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    tx=n.new('ShaderNodeTexImage');tx.image=old.image(path);tx.interpolation='Linear'
    em=n.new('ShaderNodeEmission');em.inputs[1].default_value=1;l.new(tx.outputs['Color'],em.inputs[0]);surface=em.outputs[0]
    if lit:
        p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.55;l.new(tx.outputs['Color'],p.inputs['Base Color'])
        mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.25;l.new(p.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);surface=mix.outputs[0]
    trans=n.new('ShaderNodeBsdfTransparent');a=n.new('ShaderNodeMixShader');l.new(tx.outputs['Alpha'],a.inputs[0]);l.new(trans.outputs[0],a.inputs[1]);l.new(surface,a.inputs[2]);o=n.new('ShaderNodeOutputMaterial');l.new(a.outputs[0],o.inputs[0]);CACHE[k]=m;return m

def composite(s,shot,act):
    s.use_nodes=True;n=s.node_tree.nodes;n.clear();l=s.node_tree.links;a=n.new('CompositorNodeRLayers');a.scene=s
    g=n.new('CompositorNodeGlare');g.glare_type='FOG_GLOW';g.threshold=.8;g.mix=-.78 if act=='hero' else -.86;g.quality='MEDIUM';g.size=7;l.new(a.outputs['Image'],g.inputs[0])
    hs=n.new('CompositorNodeHueSat');hs.inputs['Saturation'].default_value=1.12 if act=='lab' else (.83 if act=='disaster' else 1.08);l.new(g.outputs[0],hs.inputs['Image'])
    el=n.new('CompositorNodeEllipseMask');el.width=.72;el.height=.84;bl=n.new('CompositorNodeBlur');bl.filter_type='GAUSS';bl.size_x=170;bl.size_y=260;l.new(el.outputs[0],bl.inputs[0])
    r=n.new('CompositorNodeMapRange');r.inputs['To Min'].default_value=.55;r.inputs['To Max'].default_value=1.;l.new(bl.outputs[0],r.inputs[0]);mu=n.new('CompositorNodeMixRGB');mu.blend_type='MULTIPLY';mu.inputs[0].default_value=1.;l.new(hs.outputs[0],mu.inputs[1]);l.new(r.outputs[0],mu.inputs[2])
    im=n.new('CompositorNodeImage');im.image=old.image(ART/f'hud_{shot}.png');sc=n.new('CompositorNodeScale');sc.space='RENDER_SIZE';l.new(im.outputs[0],sc.inputs[0]);ov=n.new('CompositorNodeAlphaOver');l.new(mu.outputs[0],ov.inputs[1]);l.new(sc.outputs[0],ov.inputs[2]);out=n.new('CompositorNodeComposite');l.new(ov.outputs[0],out.inputs[0])

def stage(shot,a,b,act='lab'):
    s=bpy.data.scenes.new('V3_'+shot);bpy.context.window.scene=s;s.frame_start=a;s.frame_end=b;s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.use_raytracing=False;s.eevee.taa_render_samples=16
    s.eevee.fast_gi_method='AMBIENT_OCCLUSION_ONLY';s.eevee.fast_gi_distance=.45
    if hasattr(s.eevee,'use_gtao'):s.eevee.use_gtao=True;s.eevee.gtao_distance=.45;s.eevee.gtao_factor=1.3
    s.render.use_simplify=True;s.render.simplify_subdivision=2;s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=50;s.render.fps=30
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.2 if act=='lab' else (.45 if act=='disaster' else .3)
    w=bpy.data.worlds.new('V3 '+act+' sky');w.use_nodes=True;s.world=w;n=w.node_tree.nodes;l=w.node_tree.links;bg=n.get('Background');tc=n.new('ShaderNodeTexCoord');sp=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Normal'],sp.inputs[0]);r=n.new('ShaderNodeValToRGB')
    cols={'lab':('799eb7','cfe8ff'),'disaster':('4a443c','786b59'),'hero':('765745','dab478')}[act]
    r.color_ramp.elements[0].color=(*rgb(cols[0]),1);r.color_ramp.elements[1].color=(*rgb(cols[1]),1);l.new(sp.outputs['Z'],r.inputs[0]);l.new(r.outputs[0],bg.inputs[0]);bg.inputs[1].default_value=.35 if act=='lab' else (.45 if act=='disaster' else .25)
    composite(s,shot,act);g=Stage(s);g.act=act;g.shot=shot
    if act=='lab':
        sun=g.light('Sun through window mullions','SUN',(4,5,5),(0,0,2.5),4.5,'ffe0a3');sun.rotation_euler=V((-.70,-1,-.50)).to_track_quat('-Z','Y').to_euler();sun.data.angle=math.radians(8)
        fill=g.light('Cool clinical fill','AREA',(-2,-4,4),(0,0,1.3),160,'cfe8ff');fill.data.size=5
        win=g.light('Warm exterior window light','AREA',(1,3.8,3),(0,0,1),260,'ffe2a4');win.data.size=1.6
    else:
        sun=g.light('Dust-filtered sunrise' if act=='hero' else 'Muted dusty key','SUN',(-4,-2,6),(0,1,0),5.0 if act=='hero' else 2.4,'ffae52' if act=='hero' else 'b9a27c');sun.data.angle=math.radians(12)
        fill=g.light('Dim environmental fill','AREA',(1,-3,4),(0,1,1),100 if act=='hero' else 145,'b9b4aa');fill.data.size=5
    for o in s.objects:
        if o.type=='LIGHT':o.data.use_shadow=True
    return g

def cam(g,pos,target,lens=55,stop=2.0,push=.12,orbit=0):
    s=g.s;d=bpy.data.cameras.new(g.shot+' moving optics');d.lens=lens;d.sensor_fit='HORIZONTAL';d.sensor_width=36;d.clip_start=.01;d.clip_end=120;d.dof.use_dof=True;d.dof.aperture_fstop=stop
    o=g.obj(g.shot+' camera',d,pos);s.camera=o;g.cam=o;g.focus=V(target)
    start=V(pos);target=V(target);end=target+(start-target)*(1-push);end.x+=orbit
    for f in range(s.frame_start,s.frame_end+1):
        u=(f-s.frame_start)/max(1,s.frame_end-s.frame_start);o.location=start.lerp(end,u);o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler();d.dof.focus_distance=(target-o.location).length
        key(o,'location',f);key(o,'rotation_euler',f);d.keyframe_insert('dof.focus_distance',frame=f)
    linear(o);s.frame_set(s.frame_start);return o

def scalar_keys(obj,prop,rows):
    for f,v in rows:setattr(obj,prop,v);key(obj,prop,f)
    linear(obj)

def organic_hair(g,name,xyz,height=.45,radius=.055,turns=3.2,seed=0,parent=None,glow=False,axis='Z'):
    rng=random.Random(seed);phase=rng.random()*6;d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=.009;d.bevel_resolution=2;sp=d.splines.new('BEZIER');sp.bezier_points.add(55)
    for i,p in enumerate(sp.bezier_points):
        t=i/55;a=t*math.tau*turns+phase;rad=radius*(.85+.16*math.sin(t*12+seed));x=rad*math.cos(a)+.014*math.sin(t*9+seed)*t;y=rad*math.sin(a)+.012*math.sin(t*13+seed)*t;z=height*t
        p.co=(z,x,y+.04*math.sin(math.pi*t)) if axis=='X' else (x,y,z);p.radius=1-.85*t;p.handle_left_type=p.handle_right_type='AUTO'
    d.materials.append(mat('ffb43f',rough=.22,em=3.5) if glow else mat('261710',rough=.22));o=g.obj(name,d,xyz,parent);return o

def tiles_and_lab(g,desk=True):
    # Individually beveled ceramics; no line/grid stand-ins or fake floor ovals.
    tile=noise_material('Glazed scuffed ceramic','6a98ac','d2dfe0',7,.15,.035)
    for x in range(-5,6):
        for y in range(-3,6):g.box('Glazed ceramic tile',(x*.65,y*.65,-.035),(.643,.643,.065),tile,bevel=.008)
    navy=mat('244151');wall=mat('a8c4cf');trim=mat('dde8e8',rough=.27)
    g.box('Wall lower panel',(0,3.6,.62),(8,.20,1.24),wall)
    g.box('Wall lintel',(0,3.6,3.60),(8,.20,.40),wall)
    glass=mat('c7e3ee',rough=.07).copy();p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Alpha'].default_value=.25;p.inputs['Transmission Weight'].default_value=.65;glass.surface_render_method='BLENDED'
    for x in (-2.6,0,2.6):
        g.box('Window wall pier',(x-1.22,3.6,2.38),(.15,.25,2.3),wall)
        g.box('Glass pane',(x,3.63,2.35),(2.25,.018,1.95),glass,bevel=.005)
        for dx in (-1.15,0,1.15):g.box('Real depth window mullion',(x+dx,3.45,2.35),(.045,.15,2.06),navy,bevel=.008)
        for z in (1.32,2.35,3.38):g.box('Window cross bar',(x,3.45,z),(2.36,.15,.055),navy,bevel=.008)
        g.box('Projecting window sill',(x,3.36,1.29),(2.5,.47,.09),trim)
    for x in (-2.8,2.8):
        g.box('Lab cabinet',(x,2.8,.52),(1.3,.7,1.04),mat('416d83'))
        for z in (.20,.5,.8):
            g.box('Drawer face',(x,2.43,z),(1.2,.06,.24),mat('729cae'))
            g.rod('Chrome drawer handle',(x-.16,2.37,z),(x+.16,2.37,z),.015,mat('c4d2d5',metal=.8))
        for i in range(3):
            g.rod('Test tube', (x-.30+i*.27,2.7,1.08),(x-.30+i*.27,2.7,1.45),.036,mat('88b7c5',rough=.15))
    if desk:
        wood=noise_material('V3 warm wood grain','74452c','c58d52',6,.25,.08,True)
        g.box('Lab bench receiver',(0,.3,.97),(3.5,1.38,.14),wood,bevel=.045)
        for x in (-1.48,1.48):
            for y in (-.22,.82):g.box('Grounded metal desk leg',(x,y,.45),(.08,.08,.9),mat('243744',metal=.65),bevel=.012)
        g.box('Bench front apron',(0,-.30,.82),(3.3,.08,.22),wood)
        # Practical desk lamp and shade, casting true shadow maps.
        g.rod('Desk lamp base',(-1.20,.62,1.05),(-1.20,.62,1.09),.14,mat('244151',metal=.5))
        g.curve('Desk lamp gooseneck',[(-1.2,.62,1.08),(-1.15,.65,1.7),(-.85,.57,1.9)],.018,mat('43545f',metal=.7))
        g.ball('Desk lamp shade',(-.85,.57,1.87),(.16,.14,.075),mat('e4bd65',metal=.4))
        lamp=g.light('Desk lamp shadow-casting pool','AREA',(-.85,.55,1.82),(0,0,1.05),24,'ffdd97');lamp.data.size=.23;lamp.data.use_shadow=True

class Actor:
    """One connected head/body assembly, finite pose events, semantic hand targets."""
    def __init__(self,g,who,foot=(0,0,0),size=1,exp='smug',pose='rest',talk=True):
        self.g=g;self.who=who;self.foot=V(foot);self.size=size;self.exp=exp;self.pose=pose;self.talk=talk
        self.body=g.obj(who+' torso pivot');g.plane(who+' shaded pinstriped wardrobe',.76*size,.96*size,picture(ART/f'{who}_body.png'),parent=self.body)
        self.head=g.obj(who+' independent billboard head');self.head.rotation_mode='QUATERNION'
        self.aim=g.obj(who+' parallel aim');c=self.head.constraints.new('DAMPED_TRACK');c.track_axis='TRACK_Z';c.target=self.aim
        g.plane(who+' cream shaded head and stylized hair',1.18*size,1.18*size,picture(ART/f'{who}_head.png'),parent=self.head)
        self.faces={}
        for mouth in ('closed','half','wide','teeth'):
            for blink in (False,True):
                o=g.plane(who+' '+exp+' '+mouth+str(blink),1.18*size,1.18*size,picture(ART/f'face_{exp}_{mouth}_{int(blink)}.png'),(0,0,.005*size),self.head);self.faces[(mouth,blink)]=o
        self.pelvis=g.ball(who+' pelvis ink',(0,0,0),(.24*size,.085*size,.14*size),mat('211b21'))
        self.pelvisfill=g.ball(who+' shaded pelvis capsule',(0,0,0),(.217*size,.079*size,.117*size),mat('274e82' if who=='scientist' else '3a4047',rough=.65))
        self.arms=[];self.hands=[];self.legs=[];self.feet=[]
        for side in (-1,1):
            self.arms.append(g.curve(who+' curved stick arm',[(0,0,0),(0,0,.1),(0,0,.2)],.021*size,mat('211b21')))
            self.hands.append(g.ball(who+' rounded grip',(0,0,0),(.043*size,.031*size,.043*size),mat('211b21')))
            self.legs.append(g.curve(who+' curved leg',[(0,0,0),(0,0,.1),(0,0,.2)],.022*size,mat('211b21')))
            self.feet.append(g.ball(who+' supported foot',(0,0,0),(.08*size,.045*size,.035*size),mat('211b21')))
        self.sweat=g.plane(who+' temple sweat',.12*size,.17*size,picture(ART/'sweat.png',False),(.46*size,.06*size,.009),self.head)
        self.last=None

    def bake(self,targets=None,root_event=None):
        g=self.g;s=g.s;sz=self.size
        for f in range(s.frame_start,s.frame_end+1):
            s.frame_set(f);q=g.cam.rotation_euler.to_quaternion();p=self.foot+(V(root_event(f)) if root_event else V((0,0,0)));age=f-s.frame_start;u=age/max(1,s.frame_end-s.frame_start)
            self.body.location=p+V((0,0,.98*sz));self.body.rotation_mode='QUATERNION';self.body.rotation_quaternion=q @ Quaternion((0,0,1),-.22) if self.pose=='carried' else q
            self.head.location=(self.body.location+self.body.rotation_quaternion@V((0,.75*sz,0))) if self.pose=='carried' else p+V((0,0,1.73*sz));self.head.rotation_quaternion=q;self.aim.location=self.head.location+q@V((0,0,8))
            for ob,props in [(self.body,['location','rotation_quaternion']),(self.head,['location','rotation_quaternion']),(self.aim,['location'])]:
                for prop in props:key(ob,prop,f)
            for ob,depth in [(self.pelvis,-.005),(self.pelvisfill,.005)]:ob.location=p+V((0,0,.56*sz))+q@V((0,0,depth));ob.rotation_mode='QUATERNION';ob.rotation_quaternion=q;key(ob,'location',f);key(ob,'rotation_quaternion',f)
            extra=targets(f,p,q) if targets else {}
            for i,side in enumerate((-1,1)):
                shoulder=self.body.location+q@V((side*.18*sz,.18*sz,-.025*sz))
                if self.pose in ('celebrate','panic'):
                    target=p+V((0,0,(1.95 if self.pose=='celebrate' else 1.55)*sz))+q@V((side*.68*sz,0,.018))
                elif self.pose in ('focus','launch','carry') and side==1:target=p+V((0,0,1.37*sz))+q@V((.63*sz,0,.02))
                else:target=p+V((0,0,.77*sz))+q@V((side*.49*sz,0,.015))
                target=V(extra.get('right' if side==1 else 'left',target))
                elbow=shoulder.lerp(target,.5)+q@V((side*.16*sz,0,0))
                if target.z>=1.03 and g.act=='lab':elbow.z=max(elbow.z,1.09)
                pts=self.arms[i].data.splines[0].bezier_points
                for bp,pos in zip(pts,(shoulder,elbow,target)):bp.co=pos;bp.keyframe_insert('co',frame=f)
                self.hands[i].location=target;key(self.hands[i],'location',f)
                hip=p+V((0,0,.55*sz))+q@V((side*.13*sz,0,-.02));foot=p+q@V((side*.22*sz,-.06*sz,0));foot.z=max(.035*sz,p.z+.035*sz)
                knee=hip.lerp(foot,.5)+q@V((side*.035*sz,0,0))
                if self.pose=='carried':
                    knee=p+V((0,0,.37*sz))+q@V(((.36+side*.07)*sz,0,.01));foot=p+V((0,0,.60*sz))+q@V(((.70+side*.09)*sz,0,.015))
                for bp,pos in zip(self.legs[i].data.splines[0].bezier_points,(hip,knee,foot)):bp.co=pos;bp.keyframe_insert('co',frame=f)
                self.feet[i].location=foot;key(self.feet[i],'location',f)
            if age%3==0 or f==s.frame_end:
                amp=AUDIO[min(f-1,len(AUDIO)-1)]/PEAK
                mouth=('closed' if amp<.06 else 'half' if amp<.23 else 'wide') if self.talk else 'closed'
                if self.exp in ('focus','panic') and age<15:mouth='teeth'
                if self.exp=='shock' and age<20:mouth='wide'
                blink=age%89 in (36,37,38,39,40)
                for combo,ob in self.faces.items():ob.scale=(1,)*3 if combo==(mouth,blink) else (0,)*3;key(ob,'scale',f)
            sweat=(self.exp in ('shock','panic','focus')) and 8<age<min(53,s.frame_end-s.frame_start)
            self.sweat.scale=(1,)*3 if sweat else (0,)*3;self.sweat.location.y=(.06-.0018*max(0,age-8))*sz;key(self.sweat,'scale',f);key(self.sweat,'location',f)
        for ob in [self.body,self.head,self.aim,self.pelvis,self.pelvisfill]+self.hands+self.feet:linear(ob)
        for ob in list(self.faces.values())+[self.sweat]:
            for fc in ob.animation_data.action.fcurves:
                if fc.data_path=='scale':
                    for k in fc.keyframe_points:k.interpolation='CONSTANT'
        s.frame_set(s.frame_start)

def speedlines(g,actor):
    for i in range(12):
        a=math.tau*i/12;r=.68*actor.size;rr=.83*actor.size
        g.curve('Shock radial white speedline',[(r*math.cos(a),r*math.sin(a),-.025),(rr*math.cos(a),rr*math.sin(a),-.025)],.007,mat('fff4d9',em=.7),actor.head)

def puffs(g,start,end,color='pink',count=35):
    start,end=V(start),V(end);rng=random.Random(97)
    for i in range(count):
        o=g.plane('Soft scent puff',.24,.24,picture(ART/f'puff_{color}.png',False));c=o.constraints.new('COPY_ROTATION');c.target=g.cam
        phase=i/count
        for f in range(g.s.frame_start,g.s.frame_end+1,3):
            t=(f-g.s.frame_start)/max(1,g.s.frame_end-g.s.frame_start);travel=t*1.25-phase*.65
            pos=start.lerp(end,max(0,min(1,travel)))+V((0,.055*math.sin(i*3),.065*math.sin(i*1.7)))
            fade=max(0,min(1,travel*8,(1-travel)*8));o.location=pos;o.scale=(fade,)*3;key(o,'location',f);key(o,'scale',f)
        linear(o)
    light=g.light('Moving scent interactive light','POINT',start,(0,0,0),60 if color=='pink' else 24,'ff83b9' if color=='pink' else 'c4e99b')
    scalar_keys(light,'location',[(g.s.frame_start,start),(g.s.frame_end,end)])
    if color=='pink':
        for i in range(7):
            petal=g.ball('Floating 3D perfume petal',start,(.026,.011,.047),mat('e58bb2',rough=.4))
            for f,p in [(g.s.frame_start,start),(g.s.frame_end,end+V((0,.04*math.sin(i),.07*math.cos(i))))]:petal.location=p;petal.rotation_euler=(i*.4,i*.8,math.pi*(f-g.s.frame_start)/25);key(petal,'location',f);key(petal,'rotation_euler',f)
            linear(petal)

def pcb(g,xyz=(0,0,1.04),scale=1,glow=False,parent=None):
    r,h=old.pcb(g,xyz,scale,parent,False)
    # Three contacts share one continuous organic/tapered sensing filament.
    h=organic_hair(g,'Tapered keratin hero filament',(-.3,0,.22),.60,.055,3.1,11,r,glow,axis='X')
    for x,index in zip((-.3,0,.3),(0,28,55)):
        endpoint=V(h.location)+h.data.splines[0].bezier_points[index].co
        g.rod('Electrode bridge bond',(x,0,.182),endpoint,.006,mat('bca75e',metal=.7),r)
    return r,h

def rotor_disc(g,parent,x,y):
    verts=[(0,0,0)];faces=[];segs=48
    for radius in (.05,.12,.21,.27):
        for i in range(segs):verts.append((radius*math.cos(i*math.tau/segs),radius*math.sin(i*math.tau/segs),0))
    for i in range(segs):faces.append((0,1+i,1+(i+1)%segs))
    for ring in range(3):
        a=1+ring*segs;b=a+segs
        for i in range(segs):faces.append((a+i,a+(i+1)%segs,b+(i+1)%segs,b+i))
    me=bpy.data.meshes.new('Concentric rotor opacity');me.from_pydata(verts,[],faces);att=me.color_attributes.new(name='rotor_alpha',type='FLOAT_COLOR',domain='CORNER')
    for loop in me.loops:
        rr=V(me.vertices[loop.vertex_index].co).length;alpha=.025 if rr>.26 else .1+(.09 if .17<rr<.23 else 0);att.data[loop.index].color=(1,1,1,alpha)
    m=old.alpha_mat('Gradient rotor sweep','bfd1d8',.15);n=m.node_tree.nodes;l=m.node_tree.links;a=n.new('ShaderNodeAttribute');a.attribute_name='rotor_alpha';mix=next(z for z in n if z.type=='MIX_SHADER');l.new(a.outputs['Alpha'],mix.inputs[0]);me.materials.append(m)
    o=g.obj('Spinning alpha-gradient rotor disc',me,(x,y,.17),parent)
    scalar_keys(o,'rotation_euler',[(g.s.frame_start,(0,0,0)),(g.s.frame_end,(0,0,math.radians(45)*(g.s.frame_end-g.s.frame_start)))])

def drone(g,xyz,scale=.8,scanner=False,glow=False):
    # Carbon-weave shader and motor bells replace the rectangular placeholder body.
    r=g.obj('V3_Drone',xyz=xyz);r.scale=(scale,)*3;carbon=noise_material('Carbon fiber weave','111e27','40505b',70,.28,.08)
    g.ball('Sculpted carbon drone fuselage',(0,0,0),(.25,.23,.105),carbon,r)
    g.box('Carbon top deck',(0,0,.07),(.37,.33,.07),carbon,r,.07)
    for x in (-.4,.4):
        for y in (-.32,.32):
            g.rod('Tapered carbon arm',(x*.2,y*.2,0),(x,y,.035),.032,carbon,r)
            g.rod('Motor bell housing',(x,y,.015),(x,y,.14),.069,mat('a7b3bc',metal=.85,rough=.22),r)
            for j in range(6):
                a=j*math.tau/6;g.box('Motor bell vent',(x+.065*math.cos(a),y+.065*math.sin(a),.087),(.015,.015,.05),mat('25333b'),r,.003)
            rotor_disc(g,r,x,y)
            g.rod('Landing strut',(x*.6,y*.65,-.04),(x*.6,y*.65,-.21),.015,carbon,r)
    for x in (-.14,0,.14):g.ball('Warm front LED',(x,-.222,.01),(.025,.015,.025),mat('ffcf57',em=2.5),r)
    pcb(g,(0,0,.16),.43,glow,r)
    if scanner:
        lamp=g.light('Real green rescue scanner','SPOT',(0,0,0),(0,0,-1),450,'22ff66');lamp.parent=r;lamp.location=(0,0,-.13);lamp.rotation_euler=(0,0,0);lamp.data.spot_size=math.radians(38);lamp.data.spot_blend=.42;lamp.data.use_shadow=True
    return r

def flight(g,drone,start,end,bob=.035,bank=.12):
    for f in range(g.s.frame_start,g.s.frame_end+1):
        u=(f-g.s.frame_start)/max(1,g.s.frame_end-g.s.frame_start);drone.location=V(start).lerp(V(end),u)+V((0,0,bob*math.sin(math.tau*u*1.5)));drone.rotation_euler=(.04*math.sin(math.tau*u),bank*math.sin(math.tau*u),.08*math.sin(math.tau*u));key(drone,'location',f);key(drone,'rotation_euler',f)
    linear(drone)

def fracture(g,name,xyz,scale,material,seed):
    rng=random.Random(seed);bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=1)
    for v in bm.verts:v.co.x*=scale[0]*(.75+rng.random()*.45);v.co.y*=scale[1]*(.75+rng.random()*.45);v.co.z*=scale[2]*(.7+rng.random()*.5)
    o=g.mesh(name,bm,material,xyz);return o

def disaster(g):
    rng=random.Random(401);con=noise_material('Jagged concrete aggregate','5c554a','aaa18a',20,.92,.32);dark=mat('312e2a');steel=mat('79553d',metal=.7,rough=.7)
    g.box('Dust-covered ground',(0,3,-.12),(18,18,.2),noise_material('Ash and grit ground','534b40','94836b',17,.95,.12),bevel=0)
    for i in range(75):
        x=rng.uniform(-5,5);y=rng.uniform(-.4,7)
        if abs(x)<.9 and y<1.6:continue
        fracture(g,'Fractured concrete chunk',(x,y,.15+rng.random()*.3),(rng.uniform(.2,.65),rng.uniform(.18,.55),rng.uniform(.12,.35)),con,i)
    for i in range(70):
        x=rng.uniform(-4,4);y=rng.uniform(-.8,6);fracture(g,'Broken aggregate gravel',(x,y,.025),(.035+rng.random()*.07,.035+rng.random()*.07,.03+rng.random()*.05),con,500+i)
    for x,y,tilt in [(-3.0,4.2,.14),(2.7,5.1,-.18),(0,7.6,.11)]:
        root=g.obj('Damaged wall facade',xyz=(x,y,0));root.rotation_euler.y=tilt
        for story in range(4):
            z=.65+story*1.13
            g.box('Concrete facade spandrel',(0,0,z-.45),(2.6,.30,.42),con,root,.012)
            for dx in (-1.18,0,1.18):g.box('Solid facade wall pier',(dx,0,z),(.40,.32,.9),con,root,.015)
            for dx in (-.6,.6):
                g.box('Recessed ruined room',(dx,.54,z),(.78,.10,.64),dark,root,.01)
                for dz in (-.32,.32):g.box('Broken metal window frame',(dx,-.19,z+dz),(.78,.045,.035),steel,root,.004)
                g.rod('Broken diagonal window spar',(dx-.4,-.20,z-.38),(dx+.1,-.2,z+.1),.018,steel,root)
        # Boolean break through an actual solid corner panel.
        wall=g.box('Fractured remaining solid wall',(1.1,.2,1.5),(.6,.45,2.9),con,root,.01)
        cutter=g.ball('Hidden fracture boolean cutter',(1.0,-.05,2.7),(.65,.65,.68),con,root);cutter.hide_render=True;cutter.display_type='WIRE';mod=wall.modifiers.new('Missing broken concrete bite','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter
    for i in range(12):
        x=-3.3+i*.58;y=2.0+(i%3)*.5;g.curve('Bent protruding reinforcing steel',[(x,y,.15),(x+.10,y,.75),(x+.28,y+.1,.95)],.013,steel)
    for i in range(80):
        p=V((rng.uniform(-4,4),rng.uniform(-.8,6),rng.uniform(.25,4.8)));dust=g.plane('Floating warm ash mote',.045,.045,picture(ART/'puff_dust.png',False),p);c=dust.constraints.new('COPY_ROTATION');c.target=g.cam
        scalar_keys(dust,'location',[(g.s.frame_start,p),(g.s.frame_end,p+V((.08,0,-.1)))])
    # Real density volume allows the spot to scatter through dust, at low 4GB cost.
    haze=g.box('Thin airborne dust volume',(0,2,2.2),(11,12,5),mat('8d7b64'),bevel=0)
    m=bpy.data.materials.new('Dust density');m.use_nodes=True;n=m.node_tree.nodes;n.clear();v=n.new('ShaderNodeVolumePrincipled');v.inputs['Density'].default_value=.013 if g.act=='disaster' else .008;v.inputs['Color'].default_value=(*rgb('a38e6f'),1);v.inputs['Anisotropy'].default_value=.25;o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(v.outputs[0],o.inputs['Volume']);haze.data.materials.clear();haze.data.materials.append(m)
    return con
