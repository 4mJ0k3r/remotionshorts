"""Frame-addressable acting, prop grips and exact camera-plane billboards."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector, Quaternion

V=Vector; S=bpy.context.scene; O=S.objects
ROOT=Path(S.get('studio_root','D:/remotionshorts')); OUT=ROOT/'renders/sendha_namak_science'
ENV=json.loads((OUT/'audio_env.json').read_text())
ns={'__name__':'studio_ink'};exec(bpy.data.texts['studio_set_ink.py'].as_string(),ns)
INK=ns['SetInk'](S)
GROUPS={}
for name in ['SET_BEDROOM','SET_DINING','SET_CLINIC','SET_MOUTH','SET_TISSUE','SaltShaker','Phone','Prohibition','MedicalShield','SprayBottle','SafariHelmet','DoctorMirror','PenFlashlight','Strawberry worktable','MedicalBoard','Strawberry','TuckedQuilt']:
    root=O[name];GROUPS[name]=[root]+list(root.children_recursive)
for kind in ['boy','partner','doctor']:GROUPS[kind]=[o for o in O if o.name.startswith(kind+'_') or o.name=='char_'+kind]
VIS={}
FX=[o for o in O if any(o.name.startswith(p) for p in ['SaltCrystal','SpiceFlake','EmbeddedSalt','Smoke','Sweat','TongueSpot','SprayMist'])]
GERMS=['Germ%02d'%i for i in range(25)]
BOSSES=['VirusBoss'+str(i) for i in range(3)]
FLAGS=['ConquestFlag'+str(i) for i in range(3)]
for name in GERMS+BOSSES+FLAGS:GROUPS[name]=[O[name]]+list(O[name].children_recursive)
SHOTS=[('1A',1,156),('1B',156,266),('1C',266,447),('2A',447,633),('2B',633,855),('2C',855,1023),('2D',1023,1263),('3A',1263,1326),('3B',1326,1481),('3C',1481,1634),('3D',1634,1729)]

def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def ramp(f,a,b):return ease((f-a)/(b-a))
def lerp(a,b,t):return V(a).lerp(V(b),t)
def vis(name,on):
    if VIS.get(name)==on:return
    for o in (GROUPS[name] if name in GROUPS else [O[name]]):o.hide_render=not on
    if name.startswith('SET_'):
        for nested,items in GROUPS.items():
            if nested!=name and items[0] in GROUPS[name]:VIS.pop(nested,None)
    VIS[name]=on
def move(name,p,q=None):
    o=O[name];o.location=p
    if q is not None:o.rotation_mode='QUATERNION';o.rotation_quaternion=q
    return o
def material(name,mat):
    o=O[name]
    if not o.data.materials or o.data.materials[0]!=bpy.data.materials[mat]:o.data.materials.clear();o.data.materials.append(bpy.data.materials[mat])
def polycurve(name,points):
    sp=O[name].data.splines[0]
    for p,co in zip(sp.points,points):p.co=(*co,1)
def limb(name,a,b,side,q,bend=.065):
    delta=b-a;dist=delta.length
    normal=q@V((0,0,1));axis=q@V((side,0,0))
    pole=axis-delta.normalized()*axis.dot(delta.normalized()) if dist>1e-5 else axis
    if pole.length<1e-5:pole=q@V((side,.1,0))
    pole.normalize();mid=(a+b)*.5+pole*bend
    points=[]
    for i in range(25):
        t=i/24;points.append((1-t)**2*a+2*(1-t)*t*mid+t*t*b)
    polycurve(name,points)
def talk(f):return round(min(1,max(0,ENV[min(len(ENV)-1,max(0,f-1))]))*5)
def blink(f,seed):
    # Deterministic but unsynchronised; a blink changes only eyelids.
    return any(abs(f-(seed+137*i+17*(i%3)))<=2 for i in range(15))

def actor(kind,pos,expr='neutral',pose='rest',f=1,roll=0,seated=False,spoken=True,targets=None,mouth_state=None,turn_x=0):
    for part in GROUPS[kind]:
        if part.hide_render:part.hide_render=False
    root=V(pos);cam=S.camera;q=cam.matrix_world.to_quaternion();n=q@V((0,0,1));right=q@V((1,0,0));up=q@V((0,1,0))
    qr=Quaternion(n,math.radians(roll))
    # A flat torso adopts half of camera pitch. Faint roll is in the image plane.
    el=math.atan2(cam.location.z-(root.z+1.3),max(.01,math.hypot(cam.location.x-root.x,cam.location.y-root.y)))
    tq=qr@Quaternion((0,0,1),math.atan2(right.y,right.x))@Quaternion((1,0,0),math.pi/2-el*.5)
    def point(x,z,depth=0):return root+qr@(V((0,0,z))+right*x+n*depth)
    lower=.12 if seated else 0
    hc=point(0,1.76-lower)
    hq=qr@q
    move(kind+'_head',hc,hq);move(kind+'_torso',point(0,.965-lower)-n*.009,tq)
    hips=move(kind+'_hips',point(0,.59-lower)-n*.105,qr)
    ex='blink' if expr not in ['spiral','panic','profile'] and blink(f,63+{'boy':0,'partner':38,'doctor':75}[kind]) else expr
    material(kind+'_head',kind+'_head' if ex=='neutral' else kind+'_'+ex)
    state=mouth_state or ('panic' if expr=='panic' else ('o' if expr=='hypno' else ('flat' if expr in ['worry','spiral'] else 'smile')))
    amount=talk(f) if spoken else 0
    material(kind+'_mouth',f'mouth_{state}_{amount}')
    mouthpos=hc+hq@V((turn_x,-.145,.018));mouth=move(kind+'_mouth',mouthpos,hq)
    mouth.scale=(1,1.45,1) if state in ['panic','open'] else (1,1,1)
    if state=='panic':mouth.scale.y=1.25+.25*amount/5
    hands=[]
    for i,side in enumerate([-1,1]):
        letter='L' if side<0 else 'R';a=point(side*.172,1.20-lower,.008)
        # Connected, clamped 50cm arms. Raised hands stay at the head's outer edge.
        x,z=side*.24,.83-lower;dep=.018
        if pose=='panic':x,z,dep=side*.42,1.59-lower,.035
        if pose=='shrug':x,z=side*.45,1.25-lower
        if pose=='pour' and side==1:x,z,dep=.33,1.26-lower,.22
        if pose=='phone':x,z,dep=side*.11,1.13-lower,.22
        if pose=='inspect' and side<0:x,z,dep=-.40,1.28,.14
        b=V(targets[i]) if targets and targets[i] is not None else point(x,z,dep)
        delta=b-a
        if delta.length>.495:b=a+delta.normalized()*.495
        S['max_arm_reach_m']=max(S.get('max_arm_reach_m',0),(b-a).length)
        limb(f'{kind}_arm{letter}',a,b,side,hq,.11 if pose in ['panic','shrug'] else .065)
        move(kind+'_hand'+letter,b,hq);hands.append(b)
        hip=point(side*.105,.510-lower)
        if seated:
            knee=point(side*.12,.38,.20);foot=root+right*(side*.15)+V((0,-.34,.047))
            points=[]
            for j in range(25):
                t=j/24;points.append((1-t)**2*hip+2*(1-t)*t*knee+t*t*foot)
            polycurve(kind+'_leg'+letter,points)
        else:
            foot=point(side*.14,.047,.015);limb(kind+'_leg'+letter,hip,foot,side,hq,.028)
        move(kind+'_shoe'+letter,foot,hq)
        ground=V((foot.x,foot.y,.006));move(kind+'_contact'+letter,ground)
        O[kind+'_contact'+letter].hide_render=abs(roll)>2
    return {'head':hc,'mouth':mouthpos,'q':hq,'normal':n,'hands':hands,'root':root}

def grip_shaker(hand,q):
    # The contact socket is on the visible barrel, not at the prop origin.
    contact=V(O['ShakerGrip'].location)
    prop=move('SaltShaker',V(hand)-q@contact,q)
    S['shaker_grip_error_m']=(prop.location+q@contact-V(hand)).length
    return prop.location+q@V((0,0,.145))

def camera(pos,target,focus,lens=43):
    cam=S.camera;cam.location=pos;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(V(target)-V(pos)).to_track_quat('-Z','Y');cam.data.lens=lens
    bpy.context.view_layer.update()
    forward=cam.matrix_world.to_quaternion()@V((0,0,-1));cam.data.dof.focus_distance=max(.10,(V(focus)-V(pos)).dot(forward))

def icon(name,p,size=None):
    o=move(name,p,S.camera.matrix_world.to_quaternion());o.hide_render=False
    if size is not None:o.scale=(size,size,size)
    return o

def tongue(a,b,width=.055,swollen=False,arch=.006):
    q=S.camera.matrix_world.to_quaternion();n=q@V((0,0,1));right=q@V((1,0,0));up=q@V((0,1,0))
    delta=b-a
    if delta.length<.012:b=a+right*.012;delta=b-a
    axis=delta.normalized();perp=n.cross(axis).normalized()
    # A single continuous round-ended ribbon, with a matching continuous ink boundary.
    for name,extra,depth in [('TongueInk',.006,0),('TongueFill',0,.002)]:
        points=[];r=width+extra
        for i in range(25):
            t=i/24;points.append(a.lerp(b,t)+perp*r+up*(arch*math.sin(math.pi*t))+n*depth)
        for i in range(1,9):
            angle=math.pi/2-i*math.pi/8;points.append(b+axis*r*math.cos(angle)+perp*r*math.sin(angle)+n*depth)
        for i in range(25):
            t=1-i/24;points.append(a.lerp(b,t)-perp*r+up*(arch*math.sin(math.pi*t))+n*depth)
        for i in range(1,9):
            angle=-math.pi/2-i*math.pi/8;points.append(a+axis*r*math.cos(angle)+perp*r*math.sin(angle)+n*depth)
        o=O[name];o.hide_render=False
        for v,p in zip(o.data.vertices,points):v.co=p
        o.data.update()
    material('TongueFill','ec3658' if swollen else 'ff758f')
    for i in range(12):
        o=O['TongueSpot%02d'%i];o.hide_render=not swollen
        if swollen:
            t=.2+.75*(i//3)/3;p=a.lerp(b,t)+right*((i%3-1)*width*.52)+n*.006
            move(o.name,p,q)

def sprinkle(f,a,b,source,target,count=35,grain_scale=.15):
    # Particles only reset after reaching the destination surface, never in mid-air.
    for i in range(count):
        o=O['SaltCrystal%02d'%i];o.hide_render=False
        o.scale=(grain_scale,)*3
        birth=a+i*.72;u=((f-birth)%27)/27
        if f<birth or f>b:o.hide_render=True;continue
        p=lerp(source,target,u*u);p.x+=(math.sin(i*2.4)*.075)*u;p.y+=math.cos(i*3.1)*.055*u;o.location=p

def set_active(name):
    for group in ['SET_BEDROOM','SET_DINING','SET_CLINIC','SET_MOUTH','SET_TISSUE']:vis(group,group==name)

def update(scene,*args):
    f=scene.frame_current
    S['max_arm_reach_m']=0
    shot=next((item for item in SHOTS if item[1]<=f<item[2]),SHOTS[-1]);name,a,b=shot;u=ramp(f,a,b-1)
    vis('boy',name in ['1A','1B','1C','3A','3B','3C','3D'] or name=='2A' and f<491)
    vis('partner',name=='1C');vis('doctor',name=='3D')
    enabled={'SaltShaker':name=='1A' and f<86 or name=='3B','Phone':name=='1B','Prohibition':name=='1B' and f>=216,'MedicalShield':name=='3C' and f>=1548,'SprayBottle':name=='3C' and f>=1548,'SafariHelmet':name=='3C','DoctorMirror':name=='3D','PenFlashlight':name=='3D','TuckedQuilt':name=='1B'}
    for group,on in enabled.items():vis(group,on)
    for o in FX:
        if not o.hide_render:o.hide_render=True
    for key in ['QuestionIcon','DoctorSoul','Golden halo','TongueInk','TongueFill','DoctorFaintShadow']:O[key].hide_render=True
    O['Emergency red wash'].data.energy=0
    for root in GERMS:vis(root,name=='2C' or name=='2A' and f>=491)
    for root in BOSSES:vis(root,name=='2D')
    for i,root in enumerate(FLAGS):vis(root,name=='2D' and f>=1141+i*14)
    if name=='1A':
        set_active('SET_BEDROOM');vis('boy',True)
        for group in ['Strawberry worktable','MedicalBoard','Strawberry']:vis(group,True)
        pan=ramp(f,86,112);target=lerp((-.35,.0,1.50),(.67,.25,1.52),pan)
        pos=target+lerp((.08,-2.65,.22),(.16,-3.38,.32),pan)*(1-.09*u)
        camera(pos,target,(-.38,0,1.60),44)
        q=S.camera.matrix_world.to_quaternion();hc=V((-.38,0,1.76));mp=hc+q@V((0,-.145,.018));lift=ramp(f,1,35)
        fruit=lerp((-.30,-.20,.903),mp+q@V((.09,-.03,.062)),lift)
        fruitq=q@Quaternion((1,0,0),-math.pi/2)
        left=fruit+fruitq@V((0,-.04,-.0172))
        right=lerp((-.11,-.23,1.17),mp+q@V((.29,-.02,.11)),lift)
        ch=actor('boy',(-.38,.0,0),'smirk' if f<86 else 'worry','pour' if f<86 else 'shrug',f,spoken=f>85,targets=[left,right] if f<86 else None,mouth_state='open' if 36<=f<86 else None)
        move('Strawberry',fruit if f<86 else V((-.30,-.20,.903)),fruitq if f<86 else Quaternion())
        if f<86:
            vis('SaltShaker',True)
            angle=math.radians(142+5*math.sin(math.pi*((f-1)%20)/20))
            sq=q@Quaternion((0,0,1),angle)@Quaternion((1,0,0),-math.pi/2)
            pour=grip_shaker(ch['hands'][1],sq);sprinkle(f,5,85,pour,fruit+q@V((0,.035,.01)),24)
            if f>=36:
                pulse=sum(max(0,1-abs(f-peak)/10) for peak in [48,68])
                tip=ch['mouth']+q@V((.058,-.028+.035*pulse,.035))
                tongue(ch['mouth']+q@V((0,0,.006)),tip,.0225,arch=.003)
        else:icon('QuestionIcon',(.98,.46,2.31+.07*math.sin(math.pi*ramp(f,86,104))),1)
    elif name=='1B':
        set_active('SET_BEDROOM');vis('boy',True)
        for group in ['Strawberry worktable','MedicalBoard','Strawberry']:vis(group,False)
        target=V((-1.85,2.40,1.65));camera(target+V((.12,-3.20,.24))*(1-.10*u),target,(-1.85,2.50,1.98),43)
        ch=actor('boy',(-1.85,2.88,.29),'hypno' if f<216 else 'panic','phone',f,seated=True,spoken=False)
        vis('TuckedQuilt',True);O['Folded teal blanket'].hide_render=True
        for part in ['hips','legL','legR','shoeL','shoeR','contactL','contactR']:O['boy_'+part].hide_render=True
        vis('Phone',True);p=(ch['hands'][0]+ch['hands'][1])*.5;move('Phone',p,Quaternion())
        if f>=216:
            vis('Prohibition',True);move('Prohibition',p+V((0,-.10,.2+(1-ramp(f,216,226))*.8)))
    elif name=='1C':
        set_active('SET_BEDROOM');vis('boy',True);vis('partner',True)
        for group in ['Strawberry worktable','MedicalBoard','Strawberry']:vis(group,False)
        camera((.0,-4.1+u*.34,2.12),(0,.35,1.32),(0,.15,1.60),32)
        ch=actor('boy',(-.51,0,0),'panic','panic',f);ch2=actor('partner',(.52,.13,0),'panic','panic',f,spoken=False)
        p=ramp(f,277,328)
        for i in range(2):
            O['HealthPillar'+str(i)].location.x=-1.16 if i==0 else 1.16
            O['HealthPillar'+str(i)].location.y=.35
            o=O['Health meter fill' if i==0 else 'Health meter fill.001'];o.scale.z=max(.03,1-.97*p);o.location.z=.28+.77*(1-p)
            pr=next(n for n in o.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED');pr.inputs['Base Color'].default_value=(.8,.015,.025,1) if p>.65 else (.05,.7,.2,1)
        O['Emergency red wash'].data.energy=75+80*(.5+.5*math.sin((f-266)*.09))
        for i in range(8):
            person=ch if i<4 else ch2;t=((f-274+i*5)%34)/34
            o=move('Sweat%02d'%i,person['head']+person['q']@V(((-1 if i%2 else 1)*(.37+t*.18),.08-t*.25,.04)));o.hide_render=f<274;o.scale=(.018,.01,.04*(1-t*.4))
        for i in range(10):
            t=((f-305+i*8)%69)/69;o=move('Smoke%02d'%i,((-.65 if i<5 else .65)+.15*math.sin(i),1.0,1.8+t*.6));o.hide_render=f<305;o.scale=(.09*(1-t),)*3
    elif name=='2A' and f<491:
        set_active('SET_BEDROOM');vis('boy',True)
        t=ramp(f,447,490);target=V((-.48,0,1.63));camera(target+V((0,-(2.0-1.60*t),.06)),target,target,46)
        ch=actor('boy',(-.48,0,0),'panic','rest',f,spoken=False)
        O['boy_mouth'].scale=(1+2*t,1+2*t,1)
    elif name in ['2A','2D']:
        set_active('SET_MOUTH')
        target=V((20,.90,1.55));camera((20+.20*(1-u),-3.22+u*.38,1.8),target,(20,1.15,1.5),33)
        if name=='2A':
            for i in range(25):
                root='Germ%02d'%i;vis(root,True);x=(i%5-2)*.41;y=-.12+(i//5)*.48
                local=(f-491+i*3)%36;hop=.11*max(0,math.sin(math.pi*local/18))
                move(root,(20+x,y,.84+hop));size=.72+.28*ramp(f,491+i*3,522+i*3);O[root].scale=(size,)*3
        else:
            targets=[V((19.3,1.74,2.02)),V((20.7,1.74,2.02)),V((20,.40,.95))]
            for i in range(3):
                vis('VirusBoss'+str(i),True);t=ramp(f,1028+i*15,1100+i*15);p=V((20+(i-1)*.6,-1.7,.7)).lerp(targets[i],t)+V((0,0,1.0*math.sin(math.pi*t)));move('VirusBoss'+str(i),p)
                if f>=1141+i*14:
                    vis('ConquestFlag'+str(i),True);move('ConquestFlag'+str(i),targets[i]+V((.15,.0,-.10+(1-ramp(f,1141+i*14,1153+i*14))*.35)))
            for i in range(2):O['Hanging tonsil'+str(i)].scale=(.31*(1+.28*ramp(f,1100,1190)),.31,.57*(1+.12*ramp(f,1100,1190)))
    elif name in ['2B','2C']:
        set_active('SET_TISSUE');p=ramp(f,741,814) if name=='2B' else 1
        if name=='2B':camera((80+.22*u,-2.5+.34*u,2.15),(80,.55,.38),(80,.6,.35),47)
        else:camera((80.3,-2.25+.25*u,1.15),(80,.8,.55),(80,.6,.4),40)
        for o in [O['MicroCracks']]+list(O['MicroCracks'].children_recursive):o.hide_render=p<=0
        O['MicroCracks'].scale=(1,1,1)
        O['Pink tissue slab'].data.shape_keys.key_blocks['Micro-cut depression'].value=p
        pr=next(n for n in O['Pink tissue slab'].data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        if name=='2C':
            t=ramp(f,860,958);pr.inputs['Base Color'].default_value=(.63-.31*t,.23-.13*t,.32+.10*t,1)
        else:pr.inputs['Base Color'].default_value=(.71,.23,.32,1)
        if name=='2B':
            sprinkle(f,634,740,(80,.7,2.8),(80,.6,.36),55,1.8)
            if f>=650:
                for i in range(36):
                    row=i//6;column=i%6;col=2+column//2
                    y=-.05+row*.28+.03*math.sin(i*3)
                    j=max(0,min(9.999,(y+.65)/.34));lo=int(j);t=j-lo
                    x=-1.5+col*.45+.13*((1-t)*math.sin(lo*2+col)+t*math.sin((lo+1)*2+col))+(column%2-.5)*.045
                    scrape=.028*math.sin(math.pi*ramp(f,650+i%9,730+i%9))
                    o=move('EmbeddedSalt%02d'%i,(80+x+scrape,y,.30-.035*p));o.hide_render=False
                    o.scale=(1,1,1)
            for i in range(28):
                o=O['SpiceFlake%02d'%i];t=((f-633+i*4)%45)/45;o.hide_render=False
                if f<740:o.location=(80+math.sin(i*2.5)*.85,.2+(i%5)*.26,2.7-2.3*t*t)
                else:o.location=(80+math.sin(i*2.5)*.85,.2+(i%5)*.26,.295-.025*p)
                o.scale=(1.4,1.4,1.4)
        else:
            for i in range(25):
                root='Germ%02d'%i;vis(root,True);t=ramp(f,855+i*2,910+i*2);x=(i%5-2)*.34;y=(i//5)*.49-.1
                move(root,(80+x+.12*t,y,.62+math.sin(math.pi*t)*.42-.38*t));O[root].scale=(1,1,1)
            for i in range(20):
                t=((f-870+i*7)%90)/90;o=move('Smoke%02d'%i,(80+math.sin(i*2.1)*.82,.3+(i%5)*.28,.38+t*.85));o.hide_render=f<870+i*2;o.scale=(.16*(1-t),)*3
    elif name=='3A':
        set_active('SET_DINING');vis('boy',True);camera((40,-2.55+.22*u,1.94),(40,0,1.53),(40,0,1.73),48)
        ch=actor('boy',(40,.04,0),'worry','shrug',f);icon('QuestionIcon',(40.30,.02,2.16),.8)
    elif name=='3B':
        set_active('SET_DINING');vis('boy',True);camera((40.22,-2.95+.28*u,2.03),(40,-.10,1.29),(40,0,1.58),46)
        ch=actor('boy',(39.75,.14,.0),'smile','pour',f,seated=True);O['Golden halo'].hide_render=False;move('Golden halo',ch['head']+V((0,0,.48)))
        vis('SaltShaker',True)
        q=ch['q']@Quaternion((0,0,1),math.radians(142+4*math.sin(math.pi*((f-1326)%24)/24)))@Quaternion((1,0,0),-math.pi/2)
        source=grip_shaker(ch['hands'][1],q);target=V((40.18,-.48,.98)) if f<1410 else V((39.50,-.47,.94));sprinkle(f,1330,1475,source,target)
    elif name=='3C':
        set_active('SET_DINING');vis('boy',True);camera((39.96,-3.10+.23*u,1.95),(39.96,0,1.63),(39.65,0,1.73),40)
        ch=actor('boy',(39.65,0,0),'profile','rest',f,spoken=False,mouth_state='open',turn_x=.14)
        t=ramp(f,1485,1520);reach=.15*t
        tip=ch['mouth']+ch['q']@V((reach,-.035*t,.012));base=ch['mouth']+ch['normal']*.006
        tongue(base,tip,.0225,arch=.003)
        vis('SafariHelmet',True);move('SafariHelmet',tip+ch['q']@V((0,.035,.006)),ch['q']@Quaternion((1,0,0),-math.pi/2))
        if f>=1548:
            vis('MedicalShield',True);vis('SprayBottle',True)
            drop=.7*(1-ramp(f,1548,1556))
            # Keep the barrier beside/below the cheek; the top-left corner is
            # outside the head silhouette instead of painting over the face.
            arrival=1-ramp(f,1548,1556)
            p=V((40.185+.30*arrival,tip.y-.04,tip.z-.18+drop));move('MedicalShield',p)
            O['MedicalShield'].scale=(.64,.64,.64)
            bottle=V((40.50+.30*arrival,tip.y-.035,tip.z-.12+drop));move('SprayBottle',bottle)
            O['SprayBottle'].scale=(.60,.60,.60)
            for i in range(8):
                o=move('SprayMist%02d'%i,bottle+V((-.05-.012*i,-.03,.10+.004*i)));o.hide_render=False;o.scale=(.007+.001*i,)*3
    elif name=='3D':
        set_active('SET_CLINIC');vis('boy',True);vis('doctor',True)
        p=ramp(f,1676,1695)
        camera((60.25,-4.08+.32*u,1.93),(60.25,.18,1.13),(60,.0,1.65),29-3*p)
        ch=actor('boy',(59.30,.05,0),'panic','rest',f,spoken=False,mouth_state='open')
        doc=actor('doctor',(60.53+1.20*p,.12,.18*p),'spiral' if p>.55 else 'panic','inspect',f,roll=80*p,spoken=False)
        vis('DoctorMirror',True);move('DoctorMirror',doc['head']+doc['q']@V((0,.29,.035)),doc['q']@Quaternion((1,0,0),math.pi/2))
        vis('PenFlashlight',True);hand=doc['hands'][0];move('PenFlashlight',hand,(ch['mouth']-hand).to_track_quat('Z','Y'))
        base=ch['mouth']+ch['normal']*.007
        tip=base+ch['q']@V((0,-.20,.012));tongue(base,tip,.062,True,arch=0)
        S['swollen_mouth_anchor_error_m']=(base-(ch['mouth']+ch['normal']*.007)).length
        if p>.45:
            icon('DoctorSoul',doc['head']+V((.08,0,.30+.37*p)))
            move('DoctorFaintShadow',(doc['head'].x,doc['head'].y,.006));O['DoctorFaintShadow'].hide_render=False
    # A room visibility change invalidates its nested groups. Restore prop
    # availability after staging, preserving the per-frame child transforms.
    for group,on in enabled.items():vis(group,on)
    O['Warning red lamp'].hide_render=name!='1C';O['Warning lamp mount'].hide_render=name!='1C'
    for kind in ['key','fill','rim']:
        O['SET_BEDROOM '+kind].data.energy=({'key':35,'fill':12,'rim':25} if name=='1B' else {'key':280,'fill':85,'rim':150})[kind]
    bpy.context.view_layer.update()
    if S.get('set_ink_enabled',True):INK.update()

for handler in list(bpy.app.handlers.frame_change_pre):
    if getattr(handler,'__name__','')=='update':bpy.app.handlers.frame_change_pre.remove(handler)
bpy.app.handlers.frame_change_pre.append(update)
update(S)
