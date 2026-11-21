"""21-cut V3 rebuild. Isolated CLI only; invoked through the GUID GPU mutex."""
import sys,math,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from v3_lib import *
import scene_lib as old

CUTS=[
 ('1A',1,85,'macro','The unlikely hair'),('1B',86,168,'focus','Scientist concentrates'),('1C',169,217,'stretch','Grip and stretch'),('1D',218,249,'snap','Elastic release'),('1E',250,291,'install','Install the sensor'),
 ('2A',292,365,'perfume','Perfume reaches the hair'),('2B',366,420,'signal','Instant cellular signal'),('2C',421,465,'shock','Scientist shock reaction'),('2D',466,575,'compare','Electronic sensors lag'),('2E',576,651,'computer','Cable to computer'),('2F',652,725,'wave','Read the live waveform'),('2G',726,843,'map','A direction from scent'),
 ('3A',844,885,'mount','Sensor on palm-sized drone'),('3B',886,921,'launch','Lift off the palm'),('3C',922,979,'flight','Follow the scent'),('3D',980,1029,'home','The living sensor steers'),('3E',1030,1109,'target','Other curly hairs found'),
 ('4A',1110,1175,'scan','Search the earthquake rubble'),('4B',1176,1272,'survivor','Find a living person'),('4C',1273,1344,'rescue','Carry the survivor to safety'),('4D',1345,1413,'beauty','Career unlocked')]
CALIBRATION=['1A','1B','1D','1E','2A','2C','2G','3B','3C','4A','4B','4C']

def new(row):
    shot,a,b,kind,title=row;act='hero' if kind in ('rescue','beauty') else ('disaster' if shot.startswith('4') else 'lab')
    return stage(shot,a,b,act)

def skin_set(g,kind):
    cam(g,(.20,-1.45,.72),(0,0,.37),65,1.4,.12,.03)
    skin=noise_material('Subsurface skin / Voronoi pores','c78e6f','e0a888',125,.42,.13)
    p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.18
    n=skin.node_tree.nodes;l=skin.node_tree.links;vor=n.new('ShaderNodeTexVoronoi');vor.inputs['Scale'].default_value=145
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.007;l.new(vor.outputs['Distance'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    dome=g.ball('Sculpted convex skin dome',(0,0,-.34),(1.8,1.8,.39),skin)
    sub=dome.modifiers.new('Smooth macro skin subdivision','SUBSURF');sub.levels=2;sub.render_levels=2
    tex=bpy.data.textures.new('Organic microscopic pores',type='VORONOI');tex.noise_scale=.038
    disp=dome.modifiers.new('Very subtle skin displacement','DISPLACE');disp.texture=tex;disp.strength=.003;disp.mid_level=.5
    g.ball('Creamy macro lab background',(0,4,1.1),(6,.2,4),mat('c5c6b5',rough=1))
    rng=random.Random(48)
    for i in range(52):
        x=rng.uniform(-.9,.9);y=rng.uniform(-.04,1.3)
        if abs(x)<.18 and y<.40:x+=.30
        z=-.34+.39*math.sqrt(max(0,1-(x*x+y*y)/1.8**2))
        mound=g.ball('Raised follicle mound',(x,y,z),(.035,.035,.012),skin)
        organic_hair(g,'Organic tapered curly hair',(x,y,z+.006),rng.uniform(.20,.34),rng.uniform(.035,.06),rng.uniform(2.6,4.0),i)
    glass=mat('c3dadb',metal=.15,rough=.1)
    g.curve('Petri dish glass rolled rim',[(1.58*math.cos(i*math.tau/100),1.58*math.sin(i*math.tau/100),-.035) for i in range(100)],.026,glass,closed=True)
    hero=organic_hair(g,'Hero curly hair',(0,0,.05),.52,.06,3.6,9)
    tip=V(hero.data.splines[0].bezier_points[-1].co)+hero.location
    tool=old.tweezers(g,tip);tool.rotation_euler.y=.16
    for f in range(g.s.frame_start,g.s.frame_end+1):
        u=(f-g.s.frame_start)/max(1,g.s.frame_end-g.s.frame_start)
        if kind=='macro':stretch=1;dz=0;approach=V((.28*(1-u),0,.30*(1-u)))
        elif kind=='stretch':stretch=1+.5*u;dz=0;approach=V((0,0,0))
        else:
            e=max(0,min(1,(f-234)/8));stretch=1.5 if f<234 else 1+.18*math.exp(-e*3)*math.sin(e*math.pi*3);dz=.34*e;approach=V((0,0,0))
        hero.scale.z=stretch;hero.location.z=.05+dz;tool.location=V((tip.x,tip.y,.05+dz+tip.z*stretch-.05*stretch))+approach
        key(hero,'scale',f);key(hero,'location',f);key(tool,'location',f)
    linear(hero);linear(tool)

def reaction(g,kind):
    tiles_and_lab(g)
    cam(g,(.22,-2.65,1.95),(0,.25,1.66),65,2.0,.13,-.09)
    exp='focus' if kind=='focus' else 'shock'
    a=Actor(g,'scientist',(0,.34,0),1,exp,'focus' if kind=='focus' else 'panic')
    if kind=='shock':
        speedlines(g,a);p,h=pcb(g,(.65,-.01,1.04),.47,True);g.light('Orange sensor response spill','POINT',(.42,.2,1.5),(0,0,0),15,'ffb944')
    else:
        tool=old.tweezers(g,(.76,-.10,1.4));tool.rotation_euler.y=-.3
        for f in (g.s.frame_start,g.s.frame_end):key(tool,'location',f)
    if kind=='focus':
        a.bake(lambda f,p,q:{'right':V((.76,-.10,1.4))+tool.rotation_euler.to_matrix()@V((0,.015,.61))})
        a.hands[1]['contact_target']=tool.name;a.hands[1]['target_local']=[0,.015,.61];a.hands[1]['contact_local']=[0,0,0]
        for f in range(g.s.frame_start,g.s.frame_end+1):
            g.s.frame_set(f);q=g.cam.rotation_euler.to_quaternion();distance=g.cam.data.dof.focus_distance;focus=g.cam.location+q@V((0,0,-distance));g.cam.location=focus+(g.cam.location-focus)*1.15+q@V((.12,0,0));key(g.cam,'location',f);g.cam.data.dof.focus_distance=distance*1.15;g.cam.data.keyframe_insert('dof.focus_distance',frame=f)
    else:a.bake()

def install(g):
    tiles_and_lab(g);cam(g,(.45,-3.1,2.02),(-.10,.15,1.55),58,2.0,.12,.04)
    for ob in g.s.objects:
        if ob.name.startswith('Desk lamp'):ob.location.x-=1.15
    board,hair=pcb(g,(.37,-.03,1.04),.83)
    endpoint=V((.37,-.03,1.04))+V(hair.location)*.83+V(hair.data.splines[0].bezier_points[-1].co)*.83
    tool=old.tweezers(g,endpoint);tool.rotation_euler.y=-.22
    for f in range(g.s.frame_start,g.s.frame_end+1):
        u=max(0,min(1,(f-250)/24));tool.location=endpoint+V((0,0,.27*(1-u)))
        key(tool,'location',f)
        # Keep the same continuous keratin curve gripped through the full rotation/lowering event.
        hair.rotation_euler.y=-(1-u)*math.pi/2
        hair.location=(endpoint+V((0,0,.27*(1-u)))-V((.37,-.03,1.04)))/.83-hair.rotation_euler.to_matrix()@V(hair.data.splines[0].bezier_points[-1].co)
        key(hair,'location',f);key(hair,'rotation_euler',f)
    linear(tool)
    a=Actor(g,'scientist',(-.62,.48,0),.95,'focus','focus')
    hair['filament_target']=tool.name
    def target(f,p,q):
        g.s.view_layers[0].update();return {'right':tool.matrix_world@V((0,.015,.61))}
    a.bake(target)
    a.hands[1]['contact_target']=tool.name;a.hands[1]['target_local']=[0,.015,.61];a.hands[1]['contact_local']=[0,0,0]
    # Fingers occlude both sides of the actual handle and inherit its transform.
    for x in (-.028,.028):g.ball('Fingers wrapped around tweezer handle',(x,.015,.60),(.025,.025,.055),mat('211b21'),tool)

def perfume(g):
    tiles_and_lab(g);cam(g,(.38,-2.60,1.96),(-.04,.10,1.38),60,2.0,.12,-.03)
    pcb(g,(.20,.03,1.04),.90)
    r=g.obj('Rose perfume bottle',xyz=(-.70,.04,1.04));gold=mat('cfb06d',metal=.7,rough=.23)
    g.box('Glass perfume body',(0,0,.13),(.22,.19,.26),mat('cb879f',rough=.16),r,.05)
    g.box('Gold atomizer collar',(0,0,.29),(.12,.12,.06),gold,r,.01)
    button=g.box('Travelling spray button',(0,0,.345),(.14,.10,.05),gold,r,.01)
    g.rod('Perfume nozzle',(0,0,.345),(.13,0,.345),.019,gold,r)
    a=Actor(g,'scientist',(-1.26,.65,0),.85,'focus','focus',False)
    def press(f,p,q):
        u=(f-g.s.frame_start)/max(1,g.s.frame_end-g.s.frame_start);travel=.018*math.sin(math.pi*u);button.location.z=.345-travel;key(button,'location',f)
        return {'right':V((-.70,.04,1.04+.37-travel+.043*.85))}
    a.bake(press);puffs(g,(-.55,.02,1.39),(.60,.03,1.38))
    a.hands[1]['contact_target']=button.name;a.hands[1]['target_local']=[0,0,.025];a.hands[1]['contact_local']=[0,0,-1]
    # This is a hand/atomizer macro insert: no clipped face at the left edge.
    for part in [a.body,a.head,a.pelvis,a.pelvisfill,a.arms[0],a.hands[0]]+a.legs+a.feet:
        part.hide_render=True
        for child in part.children_recursive:child.hide_render=True
    for f in range(g.s.frame_start,g.s.frame_end+1):
        for bp,pos in zip(a.arms[1].data.splines[0].bezier_points[:2],[(-1.6,.04,1.75),(-1.0,.04,1.59)]):bp.co=pos;bp.keyframe_insert('co',frame=f)

def signal(g,compare=False):
    tiles_and_lab(g)
    if compare:cam(g,(1.10,-4.4,2.0),(.55,.08,1.32),60,1.8,.12,.03)
    else:cam(g,(.55,-2.1,1.80),(.08,.08,1.34),65,1.8,.12,.02)
    pcb(g,(-.18,.0,1.04),.95,True)
    lamp=g.light('Golden keratin activation','POINT',(-.08,.02,1.36),(0,0,0),18,'ffa637')
    for f in range(g.s.frame_start,g.s.frame_end+1,3):lamp.data.energy=12+7*math.sin((f-g.s.frame_start)*.18)**2;lamp.data.keyframe_insert('energy',frame=f)
    if compare:
        from part1_assets_and_scenes_1_to_2 import breadboard
        breadboard(g,(.90,.14,1.04));breadboard(g,(1.55,.14,1.04))
    else:puffs(g,(-.6,0,1.37),(.4,0,1.35),count=35)

def computer(g,kind):
    tiles_and_lab(g)
    if kind=='computer':cam(g,(-1.35,-2.9,2.1),(.22,.24,1.72),53,2.0,.15,.10)
    elif kind=='wave':cam(g,(.20,-2.0,2.05),(.20,.46,1.96),65,1.8,.14,.03)
    else:cam(g,(.35,-3.1,2.02),(-.08,.3,1.66),57,2.0,.12,-.06)
    m=old.monitor(g,(.30,.45,1.04));pcb(g,(-.95,.05,1.04),.50,True)
    g.box('Grounded keyboard tray',(0,-.345,.050),(1.50,.40,.100),mat('bac7c6',rough=.4),m,.015)
    # Override the old static maps with actual animated graph geometry at the screen.
    for o in g.s.objects:
        if o.name.startswith('Live monitor'):
            for f in (g.s.frame_start,g.s.frame_end):o.scale=(0,0,0);key(o,'scale',f)
    screen=g.plane('Live digital monitor content',1.53,.956,picture(old.ART/('monitor_map.png' if kind=='map' else 'monitor_wave.png'),False),(0,-.038,.92),m);screen.rotation_euler=(math.pi/2,0,0)
    if kind!='map':
        dot=g.ball('Live oscilloscope sweep',(0,0,0),(.018,.007,.018),mat('65ffc1',em=2))
        for f in range(g.s.frame_start,g.s.frame_end+1):
            u=(f-g.s.frame_start)/max(1,g.s.frame_end-g.s.frame_start);dot.location=(-.38+1.32*u,.404,1.99+.10*math.sin(u*math.tau*3));key(dot,'location',f)
        linear(dot)
    else:
        a=Actor(g,'scientist',(-.86,.52,0),.83,'proud','celebrate');a.bake()
        arrow=g.ball('Moving scent location marker',(.50,.40,2.0),(.018,.008,.018),mat('d8ff9f',em=2))
        scalar_keys(arrow,'location',[(g.s.frame_start,(.10,.398,1.83)),(g.s.frame_end,(.82,.398,2.20))])
    g.curve('Real grounded USB cable',[(-.95,-.01,1.08),(-.65,-.26,1.07),(.3,-.25,1.07),(1.55,.5,1.21)],.013,mat('d9ded8'))
    signal=g.ball('Moving cable data pulse',(-.8,-.2,1.09),(.021,.021,.021),mat('ff8565',em=2))
    scalar_keys(signal,'location',[(g.s.frame_start,(-.8,-.2,1.09)),(g.s.frame_end,(1.5,.45,1.21))])

def mount(g,launch=False):
    tiles_and_lab(g)
    if launch:cam(g,(.50,-3.05,1.98),(-.12,.2,1.52),60,2.0,.13,-.03)
    else:cam(g,(.75,-2.00,1.88),(.32,.00,1.55),60,1.8,.12,-.03)
    palm=V((.32,-.02,1.31));sz=.70
    support_z=.035
    r=drone(g,palm+V((0,0,.21*sz+support_z)),sz,glow=False)
    # Organic cream mitten with a flat support patch, not a rectangular phone-like slab.
    ring=[V((.31*math.cos(i*math.tau/40),.26*math.sin(i*math.tau/40),support_z)) for i in range(40)]
    me=bpy.data.meshes.new('Organic open-palm mesh');me.from_pydata([tuple(v) for v in ring]+[(0,0,support_z)],[],[(40,i,(i+1)%40) for i in range(40)]);me.materials.append(mat('f1dbc0',rough=.65));support=g.obj('Opened supporting palm',me,palm)
    g.curve('Ink boundary of rounded human palm',[tuple(v) for v in ring],.007,mat('211b21'),support,True)
    g.ball('Human thumb at palm socket',(-.22,-.12,.014),(.10,.065,.035),mat('f1dbc0'),support)
    for y in (-.13,-.04,.05,.14):g.curve('Subtle finger articulation',[(.16,y,.037),(.265,y*.80,.037)],.004,mat('685142'),support)
    r['support_plane_z']=palm.z+support_z;r['support_until']=g.s.frame_start if launch else g.s.frame_end
    for f in range(g.s.frame_start,g.s.frame_end+1):
        u=(f-g.s.frame_start)/max(1,g.s.frame_end-g.s.frame_start);rise=(.44*u*u) if launch else 0;r.location=palm+V((0,0,.21*sz+support_z+rise));key(r,'location',f)
    linear(r)
    a=Actor(g,'scientist',(-.63,.40,0),.97,'proud','launch');a.bake(lambda f,p,q:{'right':palm})
    if not launch:
        for part in [a.body,a.head,a.pelvis,a.pelvisfill,a.arms[0],a.hands[0]]+a.legs+a.feet:
            part.hide_render=True
            for child in part.children_recursive:child.hide_render=True
        for f in range(g.s.frame_start,g.s.frame_end+1):
            for bp,pos in zip(a.arms[1].data.splines[0].bezier_points[:2],[(-1.6,-.02,1.20),(-.55,-.02,1.30)]):bp.co=pos;bp.keyframe_insert('co',frame=f)
    # Landing gear aligns to the top of the mitten, then clears it during lift.

def fly(g,home=False):
    tiles_and_lab(g,False)
    if home:cam(g,(.25,-1.05,2.10),(.0,.50,2.03),65,1.6,.12,.025)
    else:cam(g,(.30,-2.25,2.20),(.0,.45,1.85),55,2.0,.12,.09)
    r=drone(g,(0,.45,1.85),.85,glow=True)
    flight(g,r,(-.12,.38,1.83),(.12,.66,1.91),.035,.12)
    puffs(g,(-.42,.45,1.95),(.45,.80,1.98),count=35)

def target(g):
    tiles_and_lab(g);cam(g,(.45,-3.3,2.12),(.10,.23,1.50),55,2.0,.13,.04)
    # Dish and drone occupy the right half; celebration stays left and behind.
    from part2_scenes_3_to_4_and_sheet import dish
    dish(g,(.54,.05,1.04))
    # Replace every uniform dish spring with an organic tapered strand.
    for o in list(g.s.objects):
        if o.name.startswith('Second curly hair cluster'):o.hide_render=True
    rng=random.Random(73)
    for i in range(24):
        a=rng.random()*math.tau;rr=rng.random()*.26;organic_hair(g,'Second organic hair specimen',(.54+rr*math.cos(a),.05+rr*math.sin(a),1.09),rng.uniform(.11,.24),.025,rng.uniform(2,3.5),100+i)
    r=drone(g,(.31,.48,1.72),.59,glow=True);flight(g,r,(.22,.58,1.76),(.38,.45,1.70),.025,.06)
    a=Actor(g,'scientist',(-.72,1.10,0),.90,'proud','celebrate');a.bake()

def scan(g):
    cam(g,(2.15,-5.0,2.0),(0,1,1.45),48,2.2,.13,-.10);disaster(g)
    r=drone(g,(0,.90,2.0),1.12,True,True);flight(g,r,(-.32,.7,2.04),(.18,1.0,1.98),.035,.06)

def survivor(g):
    cam(g,(.90,-3.35,1.58),(-.10,.52,1.19),57,2.0,.12,-.03);con=disaster(g)
    roof=g.box('Angled fallen concrete beam',(-.23,1.02,2.14),(2.35,.55,.27),con);roof.rotation_euler.y=.15
    for x in (-1.1,.95):fracture(g,'Slab anchoring crevice',(x,.6,.75),(.5,.65,.65),con,11 if x<0 else 12)
    a=Actor(g,'victim',(-.33,.64,-.22),.85,'panic','panic',False)
    def wave(f,p,q):
        age=f-g.s.frame_start;w=math.sin(min(1,age/60)*math.tau*2)*.09 if age<60 else 0
        return {'right':p+V((.61+w,0,1.45))}
    a.bake(wave)
    slab=g.box('Concrete trapping the lower legs',(-.3,.19,.32),(1.6,.55,.39),con);slab.rotation_euler.y=-.08
    r=drone(g,(.63,.3,1.81),.56,True,True);flight(g,r,(.60,.3,1.86),(.63,.4,1.79),.02,.04)
    puffs(g,(.1,.64,.69),(.64,.39,1.74),'gold',20)
    g.light('Warm reflection protects survivor face','AREA',(-.6,-1,2.0),(-.3,.6,1.2),55,'d4c7b1')

def rescue(g):
    cam(g,(.60,-4.0,1.74),(.04,.54,1.42),55,2.2,.13,-.08);disaster(g)
    rescuer=Actor(g,'firefighter',(-.36,.75,0),1.02,'proud','carry',False)
    victim=Actor(g,'victim',(.46,.30,.48),.67,'proud','carried',False)
    # Defined lift event, then a supported carried hold; both share the same path.
    def event(f):
        t=max(0,min(1,(f-g.s.frame_start)/29));e=t*t*(3-2*t);return V((0,-.13*e,.16*e))
    victim.bake(root_event=event)
    def support(f,p,q):return {'right':V((.46,.30,.48))+event(f)+V((.32,-.03,.25)),'left':V((.46,.30,.48))+event(f)+V((-.27,.01,.64))}
    rescuer.bake(support)
    r=drone(g,(1.00,.65,1.85),.60,False,True);flight(g,r,(1,.65,1.84),(1,.74,1.90),.025,.04)
    g.light('Golden hero face fill','AREA',(-1,-2,3),(.1,.6,1.4),130,'ffdc9f')

def beauty(g):
    cam(g,(.66,-1.60,2.05),(0,.2,1.75),65,1.8,.14,-.07);disaster(g)
    r=drone(g,(0,.2,1.5),1.05,False,True);flight(g,r,(-.03,.2,1.50),(.03,.2,1.54),.025,.03)
    g.light('Hero gold sensor sparkle','POINT',(.1,.2,1.91),(0,0,0),18,'ffd177')

def main():
    bpy.context.scene.render.engine='BLENDER_EEVEE_NEXT'
    manifest=[]
    for row in CUTS:
        shot,a,b,kind,title=row;print('BUILD V3',shot,kind,flush=True);g=new(row)
        if kind in ('macro','stretch','snap'):skin_set(g,kind)
        elif kind in ('focus','shock'):reaction(g,kind)
        elif kind=='install':install(g)
        elif kind=='perfume':perfume(g)
        elif kind in ('signal','compare'):signal(g,kind=='compare')
        elif kind in ('computer','wave','map'):computer(g,kind)
        elif kind in ('mount','launch'):mount(g,kind=='launch')
        elif kind in ('flight','home'):fly(g,kind=='home')
        elif kind=='target':target(g)
        elif kind=='scan':scan(g)
        elif kind=='survivor':survivor(g)
        elif kind=='rescue':rescue(g)
        else:beauty(g)
        # Record explicit camera identity; no stale marker-bound camera can leak across cuts.
        g.s.camera=g.cam;f=241 if kind=='snap' else (a+b)//2;g.s.frame_set(f)
        manifest.append({'id':len(manifest)+1,'shot':shot,'scene':g.s.name,'camera':g.cam.name,'a':a-1,'b':b,'start_frame':a,'end_frame':b,'sample':f,'title':title,'act':g.act,'kind':kind,'calibration':shot in CALIBRATION,'push':.12,'narration_role':'scientist presenter lip-sync when visible; other actors react'})
    (OUT/'shots_v3.json').write_text(json.dumps({'fps':30,'frames':1413,'audio_seconds':47.0726666667,'shots':manifest},indent=2))
    bpy.context.window.scene=bpy.data.scenes['V3_1E']
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_v3.blend'))
    print('V3 BUILD COMPLETE',flush=True)

if __name__=='__main__':main()
