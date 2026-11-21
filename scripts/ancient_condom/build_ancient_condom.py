"""Build nineteen isolated cuts; rendering is controlled by separate project runners."""
import sys,json,math,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import bpy,bmesh
from mathutils import Vector as V
from primitives import Stage,key,linear,image,rgb
from studio import *
from cel_cast import CoupleActor
from optimize_static import optimize
OUT=Path(r'D:\remotionshorts\renders\ancient_condom'); SHOTS=json.loads((OUT/'shots.json').read_text())
random.seed(731)
bpy.ops.wm.read_factory_settings(use_empty=True)
base=bpy.context.scene;base.name='Courtyard_World';g=Stage(base);anchors=world(g)
# Keep the preparation station outside the tree's finite diagonal canopy shadow.
station_shift=V((-1.8,0,0))
for o in base.objects:
    if o.name.startswith(('Rectangular preparation stone','Shaded grey brick')) or (o.name.startswith('Support-local contact shadow') and abs(o.location.x+2.2)<.01 and abs(o.location.y-1.6)<.01):o.location+=station_shift
anchors['stone']+=station_shift
sun=g.light('Warm diagonal SUN','SUN',(-6,-7,9),(0,0,0),6.2,'fff0d7');sun.data.angle=math.radians(5);sun.data.use_shadow=True
spot=g.light('Diagonal 38 degree local key','SPOT',(-5,-6,9),(0,0,.4),30000,'ffe6c6');spot.data.spot_size=math.radians(76);spot.data.spot_blend=.3;spot.data.use_shadow=True
fill=g.light('Quiet sky rim','AREA',(2,3,6),(0,0,1),160,'c6e2f2');fill.data.size=5
w=bpy.data.worlds.new('Blue daytime sky with low courtyard ambient');w.use_nodes=True;wn=w.node_tree.nodes;wl=w.node_tree.links;ambient=wn.get('Background');ambient.inputs[0].default_value=(*rgb('c1cbd2'),1);ambient.inputs[1].default_value=.20
sky=wn.new('ShaderNodeTexEnvironment');sky.image=image(OUT/'assets/daylight_sky.jpg');skybg=wn.new('ShaderNodeBackground');skybg.name='Visible blue sky';skybg.inputs['Strength'].default_value=2.0;wl.new(sky.outputs[0],skybg.inputs[0]);ray=wn.new('ShaderNodeLightPath');skymix=wn.new('ShaderNodeMixShader');wl.new(ray.outputs['Is Camera Ray'],skymix.inputs[0]);wl.new(ambient.outputs[0],skymix.inputs[1]);wl.new(skybg.outputs[0],skymix.inputs[2]);wl.new(skymix.outputs[0],wn.get('World Output').inputs[0]);base.world=w
report=optimize(base)
shared=bpy.data.collections.new('Shared courtyard static geometry and lights');base.collection.children.link(shared)
for o in list(base.collection.objects):shared.objects.link(o);base.collection.objects.unlink(o)
canopy=bpy.data.collections.new('Tree crown foreground');shared.children.link(canopy)
for o in list(shared.objects):
    if o.type=='MESH' and any(any(h in m.name for h in ['657142','6e7945','4b5b37']) for m in o.data.materials):canopy.objects.link(o);shared.objects.unlink(o)
white=lit('e5dfcf',rough=.38,alpha=.90,gradient=True);pink=lit('cf9792',rough=.42,gradient=True);red=lit('ac594b',rough=.42,gradient=True);gold=lit('d5a342',rough=.20,metal=.42,gradient=True)
gold.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.7
water=lit('536c66',rough=.15,alpha=.76);clear=lit('c6e4dc',rough=.12,alpha=.38);dark=lit('3c4941',rough=.20)

def settings(s,mono=False):
    s.render.engine='BLENDER_EEVEE_NEXT';s.world=w;s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=30
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.film_transparent=False
    s.render.use_simplify=True;s.render.simplify_subdivision=2;s.eevee.use_raytracing=False;s.eevee.taa_render_samples=48;s.eevee.use_shadows=True;s.eevee.shadow_pool_size='512';s.eevee.shadow_ray_count=2;s.eevee.shadow_step_count=8
    s.render.use_motion_blur=True;s.render.motion_blur_shutter=.65;s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-1.0
    s.use_nodes=True;n=s.node_tree.nodes;n.clear();l=s.node_tree.links
    r=n.new('CompositorNodeRLayers');r.scene=s;gl=n.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='MEDIUM';gl.threshold=1.;gl.mix=-.76;l.new(r.outputs['Image'],gl.inputs[0])
    sat=n.new('CompositorNodeHueSat');sat.inputs['Saturation'].default_value=0 if mono else .96;l.new(gl.outputs[0],sat.inputs['Image'])
    ga=n.new('CompositorNodeGamma');ga.inputs[1].default_value=.88;l.new(sat.outputs[0],ga.inputs[0])
    vig=n.new('CompositorNodeImage');vig.image=image(OUT/'assets/vignette.png');vig.image.colorspace_settings.name='Non-Color'
    scale=n.new('CompositorNodeScale');scale.space='RENDER_SIZE';l.new(vig.outputs[0],scale.inputs[0])
    mul=n.new('CompositorNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;l.new(ga.outputs[0],mul.inputs[1]);l.new(scale.outputs[0],mul.inputs[2])
    comp=n.new('CompositorNodeComposite');l.new(mul.outputs[0],comp.inputs[0]);return r

def disc(g,name,xyz,r,material):return lathe(g,name,[(0,-.008),(r,-.008),(r,0),(0,0)],material,xyz,n=48)
def stream(g,name,start,end,material=clear,r=.018):return g.curve(name,[start,(V(start)+V(end))/2+V((0,0,-.025)),end],r,material)
def animate_stream(o,a,b,f):
    curve_at(o,[a,(V(a)+V(b))/2+V((0,0,-.025)),b],f)
def drops(g,n,material,origin,a,b,r=.018):
    for i in range(n):
        o=g.ball('Contact-born droplet',origin,(r,r,r),material);ang=random.uniform(0,math.tau);d=V((math.cos(ang),math.sin(ang),0))*random.uniform(.08,.32)
        for f in range(a,b+1):
            u=((f-a+i*3)%24)/23;p=V(origin)+d*u+V((0,0,.20*math.sin(math.pi*u)))
            setkey(o,'location',p,f)
def sparkle(g,xyz,a,b):
    m=lit('f7dc7b',rough=.2);m=m.copy();m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=1.7
    for i in range(5):
        root=g.obj('Honey highlight sparkle',xyz=V(xyz)+V((i*.19,0,.10+(i%2)*.08)))
        for axis in [(1,0,0),(0,0,1)]:v=V(axis)*.035;g.rod('Four-point glint',-v,v,.003,m,root)
        for f in range(a,b+1):setkey(root,'scale',(max(0,math.sin((f-a-i*6)*math.pi/30))*.9,)*3,f)

# Camera specifications use physical subject anchors. Each scene contains only its own action.
spec={
1:((-2.25,-1.10,1.05),(-2.25,-6.9,2.0),48),2:((-2.25,-1.10,1.14),(-2.25,-6.9,1.95),48),
3:((-.1,-1.10,.85),(2.5,-4.5,2.6),48),4:((-.1,-1.10,.55),(2.5,-4.5,2.5),48),
5:((0,-.4,1.06),(1.2,-4.5,3.0),45),6:((1.15,-.05,1.27),(3.2,-2.8,2.8),55),7:((1.3,-.05,1.43),(3.1,-3.1,2.65),52),
8:((1.9,-1.7,.63),(3.9,-4.9,2.0),48),9:((4.05,1,1.22),(6.1,-1.8,2.6),55),
10:((0,-.4,1.55),(0,-3.4,1.55),60),11:((-.6,-2.9,.64),(1.2,-5.3,2.4),54),
12:((-2.2,1.6,1.30),(-.4,-1.0,1.75),60),13:((-2.2,1.6,1.49),(-.6,-1.0,1.75),58),14:((-2.2,1.6,1.32),(-.6,-1.0,1.75),58),
15:((-2.05,1.6,1.75),(-.1,-1.4,1.85),48),16:((-2.20,1.6,.98),(-1.2,-2.0,2.4),50),
17:((-2.2,1.6,1.40),(-.6,-1,1.75),62),18:((-2.38,1.6,1.34),(-.8,-1.5,1.80),60),
19:((3.20,.15,1.12),(8.6,-6.5,2.7),42)}
for k in range(12,19):
    t,e,lens=spec[k];spec[k]=(V(t)+station_shift,V(e)+station_shift,lens)
# View the honey action from the left: its former ray intersected the tree trunk.
t,_,lens=spec[16];spec[16]=(t,V((-5.0,-1.7,2.2)),lens)
t,_,_=spec[15];spec[15]=(t,V((-6.5,-2.0,1.6)),52)
scenes={};camera_log=[]
for row in SHOTS['shots']:
    i=row['id'];a=row['start_frame'];b=row['end_frame'];s=bpy.data.scenes.new(row['scene']);scenes[i]=s;s.collection.children.link(shared);settings(s,i==4);s.frame_start=a;s.frame_end=b;g=Stage(s)
    if i==15:s.view_layers[0].layer_collection.children[shared.name].children[canopy.name].exclude=True
    cam=g.obj('Camera Cut %02d'%i,bpy.data.cameras.new('Optics Cut %02d'%i));s.camera=cam;cam.data.lens=spec[i][2];cam.data.sensor_width=36;cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=1.4 if i==10 else 1.6;cam.data.dof.aperture_blades=7
    target0=V(spec[i][0]);eye0=V(spec[i][1]);target_by_frame={};push=.14 if i==2 else .15 if i==18 else .12
    # Anonymous foreground edge, outside the central subject area, creates a visible near layer.
    q=(target0-eye0).to_track_quat('-Z','Y');right=q@V((1,0,0));front=eye0+(target0-eye0)*.68-right*((target0-eye0).length*.68*10.125/cam.data.lens*.98)
    g.rod('Out-of-focus near wooden edge',(front.x,front.y,0),(front.x,front.y,max(1.4,target0.z+.5)),.020,lit('62442b',rough=.8))
    if i in [1,2,19]:
        positions=[(-2.8,-1.10,0),(-1.7,-1.10,0)] if i!=19 else [(2.2,-.70,0),(3.0,-.20,0)]
        actors=[CoupleActor(g,who,p) for who,p in zip(['male','female'],positions)]
        centre=(V(positions[0])+V(positions[1]))/2;gentle=g.light('Gentle scene-lit face readability','AREA',centre+V((0,-3,2.4)),centre+V((0,0,1.4)),180,'e4e4dd');gentle.data.size=2
        if i==1:r=rose(g,(-2.3,-1.34,.93))
        if i==2:
            question=g.curve('Sculpted reaction question',[(0,0,.35),(.10,0,.43),(.24,0,.35),(.18,0,.22),(.10,0,.17),(.10,0,.10)],.018,lit('d7b460',metal=.45));question.location=(-2.35,-1.1,1.94);g.ball('Question punctuation',(-2.25,-1.1,1.98),(.025,.025,.025),lit('d7b460',metal=.45))
        if i==19:
            disc(g,'Rinse water',anchors['rinse'],.35,water);hero=sheath(g,'Rinsed golden sheath',gold,(3.525,1,1.22));hero.rotation_euler.y=math.pi/2;st=stream(g,'Spout-connected clear rinse',anchors['spout'],(4.05,1,1.294));stream(g,'Water falls from sheath to tub',(4.05,1,1.22),(4.05,1,1.10))
        for f in range(a,b+1):
            if i==1:
                u=ease(a+5,b-10,f);grip=V((-2.48+.36*u,-1.34,.93));setkey(r,'location',grip,f)
            target_by_frame[f]=target0
    elif i==3:
        hero=sheep(g,(-.1,-1.1,0));h=hand(g,(0,0,0))
        for f in range(a,b+1):
            z=1.0*(1-ease(a+5,b-20,f));p=V((-.1,-1.1,z));setkey(hero,'location',p,f);setkey(h,'location',p+V((0,0,.88+ease(b-18,b,f)*1.0)),f);target_by_frame[f]=V((-.1,-1.1,.75+z*.35))
    elif i==4:
        hero=sheep(g,(-.1,-1.1,0),True);k=knife(g,(-.5,-1.1,1.1));gut=coil(g,'Uninjured stylized coiled gut',red,(-.1,-1.1,.4),.8)
        shards=[]
        for j in range(27):
            bm=bmesh.new();bmesh.ops.create_icosphere(bm,subdivisions=1,radius=random.uniform(.055,.14));o=g.mesh('Grey clay shard',bm,lit('96958e'));shards.append((o,random.uniform(0,math.tau),random.uniform(.25,1.1)))
        for f in range(a,b+1):
            setkey(hero,'scale',(1,)*3 if f<292 else (0,)*3,f);u=ease(277,298,f);setkey(k,'location',(-.65+1.15*u,-1.17,1.20-.85*u),f);setkey(k,'rotation_euler',(0,-1.2*u,0),f)
            v=ease(291,315,f);setkey(gut,'location',(-.1,-1.1,.35+.7*math.sin(v*math.pi*.65)),f);setkey(gut,'scale',(.8,)*3 if f>=292 else (0,)*3,f)
            for o,angle,d in shards:
                t=max(0,min(1,(f-292)/25));setkey(o,'scale',(1,)*3 if f>=292 else (0,)*3,f);setkey(o,'location',(-.1+d*t*math.cos(angle),-1.1+d*t*math.sin(angle),.05+.45*(1-t)+.6*math.sin(math.pi*t)),f);setkey(o,'rotation_euler',(angle*t,3*t,2*t),f)
    elif i==5:
        pts=[(-.75+j*.025,-.4,.98+.008*math.sin(j)) for j in range(61)];tube(g,'Stretched red intestine',pts,.06,red)
        scraper=g.box('Wood scraper contact block',(0,-.4,1.10),(.22,.25,.12),lit('a37847',rough=.7))
        for x in [-.8,.8]:g.rod('Bench stretching clamp',(x,-.4,.90),(x,-.4,.99),.025,lit('534230'))
        for f in range(a,b+1):
            t=(f-a)/(b-a)*3;u=min(1,t%1/.75);x=-.62+1.24*ease(0,1,u);setkey(scraper,'location',(x,-.4,1.10+(.15*ease(.75,1,t%1))),f)
        drops(g,9,lit('dab54f',rough=.35),(.12,-.48,.917),a,b)
    elif i in [6,7,9]:
        c=anchors['rinse'] if i==9 else anchors['tub'];disc(g,'Liquid inside open barrel',c,.35,water if i==9 else dark);gut=coil(g,'Floating intestine',white if i==9 else pink,c,.70)
        if i==7:pot=teapot(g,c+V((.62,0,.55)));st=stream(g,'Spout-connected vinegar stream',c,c)
        if i==9:st=stream(g,'Bamboo spout clear water',anchors['spout'],c+V((0,0,.035)))
        for f in range(a,b+1):
            if i==6:setkey(gut,'location',c+V((0,0,.66*(1-ease(a+5,b-12,f)))),f)
            if i==7:
                u=ease(a+3,a+22,f);setkey(pot,'rotation_euler',(0,-.50*u,0),f);start=pot.location+pot.rotation_euler.to_quaternion()@V(pot['spout_local']);animate_stream(st,start,c,f);setkey(st,'scale',(1,)*3 if f>a+12 else (0,)*3,f);setkey(gut,'location',c+V((0,0,.15*ease(a+15,b,f))),f)
            if i==9:setkey(gut,'rotation_euler',(0,0,(f-a)*.045),f)
    elif i==8:
        gut=coil(g,'White gut roasting above fire',white,(1.9,-1.7,.80),.85)
        flame_m=lit('f49a35',rough=.4);flame_m=flame_m.copy();flame_m.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=3
        flame=[]
        for j in range(7):
            x=1.9+.22*math.cos(j*2.4);y=-1.7+.2*math.sin(j*2.4);o=lathe(g,'Tapered flame',[(0,0),(.09,.01),(.075,.17),(.025,.32),(0,.48)],flame_m,(x,y,.16),n=16);flame.append(o)
        g.light('Local fire warmth','POINT',(1.9,-1.7,.40),(0,0,0),65,'ff9b48')
        smoke=[g.plane('Soft smoke behind roast',.42,.6,soft('d7d3c5',.14),xyz=(1.9+j*.12,-1.35,1+j*.22)) for j in range(3)]
        for o in smoke:o.rotation_euler.x=math.pi/2
        for f in range(a,b+1):
            setkey(gut,'rotation_euler',(.08*math.sin((f-a)*.04),0,(f-a)*.006),f)
            for j,o in enumerate(flame):setkey(o,'scale',(1,1,.8+.22*math.sin((f-a)*.4+j)),f)
            for j,o in enumerate(smoke):setkey(o,'location',(1.9+.10*math.sin((f-a)*.04+j),-1.35,1+j*.22+(f-a)*.0015),f)
    elif i==10:
        hero=sheath(g,'Exposed paper-thin membrane',white,(0,-.4,1.02));peel=[]
        for j in range(3):peel.append(g.curve('Peeling outer layer',[(0,0,0)]*4,.015,pink))
        for f in range(a,b+1):
            u=ease(a,b,f);setkey(hero,'rotation_euler',(0,.07*math.sin(u*math.pi*2),.02),f)
            for j,o in enumerate(peel):
                sign=1 if j%2 else -1;curve_at(o,[(sign*.075,-.4,1.95-u*.7),(sign*(.12+.2*u),-.4,1.9-u*.45),(sign*(.22+.22*u),-.38,1.6),(sign*(.14+.3*u),-.38,1.35)],f)
    elif i==11:
        stone_m=lit('7b8177',rough=.85);g.ball('Bowl-supporting grey boulder',(-.6,-2.9,.24),(.62,.49,.24),stone_m);shadow(g,(-.6,-2.9),.6,.48)
        lathe(g,'Light blue ceramic bowl',[(0,0),(.23,0),(.38,.13),(.40,.23),(.37,.25),(.34,.12),(.20,.04),(0,.04)],lit('8fbdc4',rough=.25,gradient=True),(-.6,-2.9,.46));disc(g,'Dark wood ash water',(-.6,-2.9,.65),.35,dark);gut=coil(g,'Ash soaking membrane',white,(-.6,-2.9,.655),.58)
        for f in range(a,b+1):setkey(gut,'rotation_euler',(0,0,(f-a)*.003),f)
    elif i in [12,13,14,15,16,17,18]:
        c=anchors['stone'];p=None
        if i!=16:p=peg(g,c)
        if i==12:
            k=knife(g,c+V((.12,0,.65)),True);strips=[]
            for j in range(4):strips.append(g.curve('Peeling peachwood bark strip',[(.075,0,0),(.08,0,.3),(.075,0,.6)],.018,lit('6d462b')))
            for f in range(a,b+1):
                u=ease(a+4,b-4,f);setkey(k,'location',c+V((.08,-.015,.85-.65*u)),f)
                for j,o in enumerate(strips):curve_at(o,[c+V((.075*math.cos(j*1.7),.075*math.sin(j*1.7),.82-.55*u)),c+V((.12+.25*u,(j-1.5)*.06,.55-.25*u)),c+V((.13+.45*u,(j-1.5)*.10,.12))],f)
            drops(g,7,lit('b98650'),c+V((.15,-.10,.015)),a,b,.026)
        elif i in [13,14,15,17,18]:
            hero=sheath(g,'Golden sheath' if i>=17 else 'White ribbed membrane',gold if i>=17 else white,c)
            if i==14:
                g.box('Cool-shade awning',c+V((-1,-1.25,1.85)),(3.0,3.0,.07),lit('777f75'),bevel=.01);g.light('Cool shaded sky fill','AREA',c+V((-.3,-1.4,1.7)),c+V((0,0,.5)),100,'b8d9eb')
                for j in range(3):g.curve('Fine cool breeze',[(c.x-.45,c.y+.20,c.z+.30+j*.25),(c.x,c.y+.28,c.z+.38+j*.25),(c.x+.45,c.y+.20,c.z+.30+j*.25)],.006,soft('b7d9d7',.20))
            if i==15:pot=teapot(g,c+V((.58,0,1.1)),True);st=stream(g,'Warm water from pink spout',c,c);steam=[g.plane('Steam behind warm sheath',.23,.40,soft('f0e9dd',.13),xyz=c+V((j*.14-.14,.16,1.05+j*.15))) for j in range(3)];[setattr(o,'rotation_euler',(math.pi/2,0,0)) for o in steam]
            if i==17:loops=[ring(g,'Fine golden thread loop',(0,0,.82+j*.05),.21,.004,gold,hero) for j in range(3)]
            if i==18:
                font=bpy.data.fonts.load(str(OUT/'assets/Chinese.ttc'));d=bpy.data.curves.new('Diegetic Chinese gold lettering','FONT');d.body='羊\n肠\n套';d.font=font;d.size=.23;d.space_line=1.1;d.extrude=.012;d.bevel_depth=.003;d.materials.append(gold);text=g.obj('Gold 羊肠套',d,c+V((-.60,-.03,.76)));text.rotation_euler.x=math.pi/2
            for f in range(a,b+1):
                if i==13:setkey(hero,'location',c+V((0,0,.90*(1-ease(a+4,b-5,f)))),f)
                if i==15:
                    z=1.05*ease(a+4,a+48,f);setkey(hero,'location',c+V((0,0,z)),f);setkey(pot,'location',c+V((.58,0,z+1.25)),f);setkey(pot,'rotation_euler',(0,-.6*ease(a+12,a+38,f),0),f);start=pot.location+pot.rotation_euler.to_quaternion()@V(pot['spout_local']);animate_stream(st,start,c+V((0,0,z+1.05)),f);setkey(st,'scale',(1,)*3 if f>a+24 else (0,)*3,f);target_by_frame[f]=c+V((.15,0,z+.52))
                if i==17:
                    u=ease(a+5,a+30,f);setkey(hero,'location',c+V((0,0,.35*(1-u))),f)
                    for j,o in enumerate(loops):r=1- .635*ease(a+25+j*6,b-5,f);setkey(o,'scale',(r,r,1),f);setkey(o,'rotation_euler',(0,0,(f-a)*.13),f)
        elif i==16:
            hero=sheath(g,'Sheath on stone for honey',white,c+V((-.525,0,.095)));hero.rotation_euler.y=math.pi/2
            glaze=gold.copy();glaze.name='Contact-progress golden honey glaze';glaze.surface_render_method='DITHERED';n=glaze.node_tree.nodes;l=glaze.node_tree.links;tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Generated'],sep.inputs[0]);less=n.new('ShaderNodeMath');less.operation='LESS_THAN';l.new(sep.outputs['Z'],less.inputs[0]);l.new(less.outputs[0],n.get('Principled BSDF').inputs['Alpha'])
            coat=sheath(g,'Thin honey coating',glaze,hero.location,radius=.076);coat.rotation_euler.y=math.pi/2;h=hand(g,(0,0,0),True)
            sparkle(g,c+V((-.43,-.08,.19)),a,b)
            for f in range(a,b+1):
                u=ease(a+5,b-8,f);x=c.x-.525+1.05*u;setkey(h,'location',(x+.55,c.y+.1125,c.z+.095+.076+.06),f);less.inputs[1].default_value=u;less.inputs[1].keyframe_insert('default_value',frame=f)
    # Camera solve after action. Heads share its orientation, facial decals remain on curved lit heads.
    for f in range(a,b+1):
        u=(f-a)/max(1,b-a);target=V(target_by_frame.get(f,target0));eye=target+(eye0-target0)*(1-push*u)
        if i==11:
            vec=eye-target;angle=.16*u;x=vec.x*math.cos(angle)-vec.y*math.sin(angle);y=vec.x*math.sin(angle)+vec.y*math.cos(angle);eye=target+V((x,y,vec.z))
        if i==4 and 291<=f<=306:
            fade=1-(f-291)/15;eye+=V((.045*math.sin(f*2.1),0,.025*math.cos(f*2.4)))*fade
        if b in SHOTS['whip_ends'] and f>=b-5:
            v=ease(b-5,b,f);nt,ne,_=spec[i+1];target=target.lerp(V(nt),v);eye=eye.lerp(V(ne),v)
        cam.location=eye;cam.rotation_euler=(target-eye).to_track_quat('-Z','Y').to_euler();key(cam,'location',f);key(cam,'rotation_euler',f);cam.data.dof.focus_distance=(target-eye).length;cam.data.dof.keyframe_insert('focus_distance',frame=f)
        if i in [1,2,19]:
            for j,actor in enumerate(actors):
                hands=None
                if i==1:
                    grip=V((-2.48+.36*ease(a+5,b-10,f),-1.34,.93));hands=[(-.30,-.08,.72),tuple(grip-V(positions[j]))] if j==0 else [tuple(grip-V(positions[j])+V((.035,0,0))),(.3,-.08,.72)]
                actor.pose(f,cam,('smile' if j==0 else 'shy') if i==1 else 'panic' if i==2 else 'horror',hands,i!=1)
    for o in list(s.objects):
        if o.name.startswith('Face decal') and o.animation_data:
            for fc in o.animation_data.action.fcurves:
                for k in fc.keyframe_points:k.interpolation='CONSTANT'
        elif o.name not in shared.objects:linear(o)
    camera_log.append({'cut':i,'scene':s.name,'fstop':cam.data.dof.aperture_fstop,'push':push,'range':[a,b],'focus_target':list(target0)})
    print('BUILT CUT',i,len(s.objects),flush=True)
# Only the dissolve scene references the preceding scene. Hold its final authored pose through the dissolve.
s=scenes[14];n=s.node_tree.nodes;l=s.node_tree.links;current=next(x for x in n if x.type=='R_LAYERS');old=n.new('CompositorNodeRLayers');old.scene=scenes[13];mix=n.new('CompositorNodeMixRGB');l.new(old.outputs['Image'],mix.inputs[1]);l.new(current.outputs['Image'],mix.inputs[2]);dest=[x.to_socket for x in list(l) if x.from_node==current and x.from_socket.name=='Image' and x.to_node!=mix]
for socket in dest:l.new(mix.outputs[0],socket)
for f,v in [(1176,0),(1183,1)]:mix.inputs[0].default_value=v;mix.inputs[0].keyframe_insert('default_value',frame=f)
for s in scenes.values():s.frame_set(s.frame_start)
bpy.context.window.scene=scenes[1];bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ancient_condom.blend'),compress=True)
(OUT/'build_report.json').write_text(json.dumps({'static_batching':report,'cameras':camera_log,'render_engine':'BLENDER_EEVEE_NEXT','raytracing':False,'motion_blur':.65,'scope':'20-frame calibration only'},indent=2))
print('BUILD COMPLETE',flush=True)
