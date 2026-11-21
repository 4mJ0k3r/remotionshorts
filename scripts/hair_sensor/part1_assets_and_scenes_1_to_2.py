"""Authored macro/lab beats. Imported by the isolated project build."""
from scene_lib import *

SHOT_ROWS=[
 ('1A',1,168,110,'Question / choose the unlikely hair','Shallow macro; tweezers approach the hero'),
 ('1B',169,249,238,'Pluck the single hair','Stretch, release at 7.95 s, recoil then settle'),
 ('1C',250,291,278,'Install on circuit board','Hand-to-tweezer grip; filament meets three electrodes'),
 ('2A',292,365,343,'Perfume scent reaches hair','Atomizer grip; tapered scent and petals cross PCB'),
 ('2B',366,575,440,'Hair beats ordinary sensors','Orange signal pulse; delayed breadboards'),
 ('2C',576,843,727,'Computer turns scent into directions','Over shoulder; waveform becomes navigation map'),
 ('3A',844,921,900,'Mount mini drone','Palm support, rotor start, lift'),
 ('3B',922,1029,994,'No remote: scent-guided flight','Behind-drone chase, finite banking'),
 ('3C',1030,1109,1080,'Reveal the second hair cluster','Drone arrives at specimen dish'),
 ('4A',1110,1175,1150,'Emergency rescue scan','Low wide rubble reveal and green scanner'),
 ('4B',1176,1272,1234,'Find the living survivor','Crevice insert, waving survivor and scent plume'),
 ('4C',1273,1413,1380,'Career payoff','Firefighter carries survivor; sensor hero push')]

def settings(shot):
    row=next(x for x in SHOT_ROWS if x[0]==shot);return new_scene(shot,row[1],row[2],shot.startswith('4'))

def macro(shot):
    g=settings(shot);skin=noise_material('Warm neutral skin with micro pores','b67b5d','e9b18c',140,.45,.18)
    p=skin.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.12
    g.ball('Neutral warm skin dome',(0,0,-.39),(2.5,2.5,.4),skin)
    hairmat=mat('241610',rough=.28);random.seed(19)
    for i in range(58):
        x=random.uniform(-1.1,1.1);y=random.uniform(-.15,1.3)
        if abs(x)<.19 and y<.35:x+=.3
        z=-.39+.4*math.sqrt(max(0,1-(x*x+y*y)/6.25))
        coil(g,'Forest spiral hair %02d'%i,(x,y,z),random.uniform(.03,.06),random.uniform(.19,.34),random.uniform(2.5,4.6),hairmat,seed=i)
    h=coil(g,'Prop_Hero_Hair / pluck',(0,0,.01),.065,.50,3.7,hairmat)
    tool=tweezers(g,(.02,0,.49));tool.rotation_euler.y=.30
    camera(g,(.28,-1.48,.61),(0,0,.30),65,2.4,endpos=(.23,-1.37,.59),endtarget=(0,0,.30))
    if shot=='1A':
        for f,p in [(1,(.48,.05,.96)),(130,(.03,0,.49)),(168,(.02,0,.49))]:tool.location=p;key(tool,'location',f)
    else:
        for f,stretch,z in [(169,1,0),(226,1.55,0),(238,.94,.30),(244,1.03,.35),(249,1,.35)]:
            h.scale.z=stretch;h.location.z=.01+z;key(h,'scale',f);key(h,'location',f)
            tool.location=(.02,0,.49*stretch+z);key(tool,'location',f)
        linear(h)
        for i in range(3):
            g.curve('Release speed accent',[(.12+i*.04,0,.25),(.17+i*.04,0,.35)],.004,mat('ffe1a4',em=.3))
    linear(tool)
    return g

def install():
    g=settings('1C');lab(g)
    camera(g,(1.35,-3.25,2.02),(.0,.20,1.60),55,2.0,endpos=(1.25,-3.0,2.0))
    a=actor(g,'scientist','inspect','smirk',(-.70,.62,0),1)
    board,h=pcb(g,(.58,-.15,1.08),1,hero=True)
    # Tween the free hair into the grounded electrode assembly.
    tool=tweezers(g,(.66,-.13,1.49));tool.rotation_euler.y=-.7
    for f,p in [(250,(.68,-.13,1.76)),(278,(.66,-.13,1.49)),(291,(.66,-.13,1.53))]:tool.location=p;key(tool,'location',f)
    linear(tool)
    # Explicit hand-grip bridge; portable tool never floats unowned.
    arm=g.curve('Scientist grip to tweezers',[a['right'],a['right']+V((.08,-.03,.03)),(.25,-.13,1.98)],.025,mat('161219'))
    mitten=g.ball('Curled mitten around tweezer grip',(0,.015,.61),(.06,.037,.06),mat('161219'),tool)
    for f in range(250,292):
        g.s.frame_set(f);grip=tool.matrix_world@V((0,.015,.61));points=arm.data.splines[0].bezier_points
        points[1].co=a['right'].lerp(grip,.6)+V((.10,0,0));points[2].co=grip
        points[1].keyframe_insert('co',frame=f);points[2].keyframe_insert('co',frame=f)
    for f,on in [(250,False),(276,True)]:h.scale=(1,)*3 if on else (0,)*3;key(h,'scale',f)
    for fc in h.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.interpolation='CONSTANT'
    return g

def perfume():
    g=settings('2A');lab(g);camera(g,(.45,-2.35,1.85),(-.03,.03,1.40),55,2.0,endpos=(.4,-2.2,1.80))
    board,h=pcb(g,(.15,0,1.08),1)
    r=g.obj('Perfume atomizer',xyz=(-.75,-.01,1.17));gold=mat('cfb56f',metal=.75)
    g.box('Rose glass perfume bottle',(0,0,.09),(.24,.20,.25),mat('d4899f',rough=.2),r,.055)
    g.box('Atomizer gold collar',(0,0,.26),(.12,.12,.07),gold,r,.015)
    g.box('Depressing spray button',(0,0,.32),(.16,.11,.05),gold,r,.012)
    g.rod('Atomizer nozzle',(0,0,.32),(.12,0,.32),.023,gold,r)
    g.curve('Offscreen scientist arm',[(-1.5,.04,1.78),(-1.03,.04,1.63),(-.75,.04,1.50)],.026,mat('161219'))
    g.ball('Fingertip presses atomizer',(-.75,0,1.515),(.045,.03,.035),mat('161219'))
    g.curve('Bottle support grip',[(-1.4,.04,1.15),(-1.02,.04,1.20),(-.87,0,1.28)],.023,mat('161219'))
    ribbon(g,(-.65,0,1.49),(.49,0,1.43));g.light('Perfume rosy interactive spill','POINT',(-.35,0,1.58),(0,0,0),12,'f7a3b8')
    return g

def breadboard(g,xyz):
    r=g.obj('Ordinary electronic scent sensor',xyz=xyz);g.box('Breadboard',(0,0,.04),(.62,.39,.08),mat('e0e0d3'),r,.035)
    for i in range(12):
        for j in range(4):g.ball('Breadboard pin socket',(-.25+i*.045,-.14+j*.09,.082),(.009,.009,.004),mat('3d4a4e'),r)
    g.rod('Conventional metal sensor can',(0,0,.08),(0,0,.27),.085,mat('a9b8bd',metal=.7),r)
    for k,h in enumerate(('ecb74b','d9584e')):g.curve('Jumper cable',[(-.22,.09,.08),(-.2,.05,.34),(.22,-.06,.30),(.23,-.1,.08)],.009,mat(h),r)
    g.ball('Lagging amber indicator',(.24,.11,.10),(.024,.024,.014),mat('e09b38',em=.8),r)
    return r

def instant():
    g=settings('2B');lab(g);board,h=pcb(g,(-.15,-.1,1.08),1)
    camera(g,(.9,-2.15,1.75),(.15,-.1,1.37),60,2.0,endpos=(1.4,-2.65,1.85),endtarget=(.68,.05,1.34))
    breadboard(g,(.96,.16,1.08));breadboard(g,(1.65,.2,1.08))
    h.data.materials.clear();h.data.materials.append(mat('ff9e24',rough=.28,em=4.5))
    g.light('Cellular signal warm spill','POINT',(-.12,-.05,1.48),(0,0,0),19,'ffac3c')
    for i in range(5):
        x=-.42+i*.14;g.ball('Cellular pulse node',(x,-.1,1.41),(.017,.017,.017),mat('ffd46a',em=4))
    g.ball('Instant green PCB LED',(-.50,-.28,1.18),(.034,.025,.025),mat('57f1a1',em=3))
    ribbon(g,(-.7,-.12,1.42),(.03,-.1,1.42),height=.10)
    return g

def computer():
    g=settings('2C');lab(g);m=monitor(g,(.25,.40,1.08));pcb(g,(-1.05,-.03,1.08),.55)
    camera(g,(-2.3,-3.7,2.55),(.27,.35,1.93),50,2.0,endpos=(-.15,-1.9,2.10),endtarget=(.25,.42,2.0))
    actor(g,'scientist','back','back',(-1.65,-.40,0),1)
    g.curve('White USB data cable',[(-1.1,-.1,1.12),(-.8,-.45,1.1),(.3,-.45,1.1),(1.4,.32,1.3)],.017,mat('e9e8dc'))
    for i in range(5):g.ball('Red data signal on cable',(-.7+i*.29,-.43,1.11),(.024,.024,.024),mat('ff685c',em=2))
    return g

def build():
    scenes=[macro('1A'),macro('1B'),install(),perfume(),instant(),computer()]
    bpy.context.window.scene=scenes[-1].s
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_stage1.blend'))
    print('Saved isolated stage 1 checkpoint',flush=True)
    return scenes
