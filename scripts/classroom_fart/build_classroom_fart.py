"""Isolated Blender 4.2 classroom short. All animation is baked and portable."""
import bpy,bmesh,math,json,sys,time,hashlib
from pathlib import Path
from mathutils import Vector as V,Matrix,Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from primitives import Stage,mat,rgb,celmat,image,noise_material,alpha_mat,key,linear
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');ART=OUT/'assets_surgical_v2'
SEAT=.46;DESK_TOP=1.0125;CHAIR_Y=-.2;SHOE_R=.015
HEAD_LOWER=json.loads((ART/'head_bounds.json').read_text())['you_lower_world'];SLUMP_PITCH=math.acos(.18/HEAD_LOWER)
# At the end, rebase the complete room by 180 degrees around the chair.
# This preserves its appearance and makes author +Y the chair's rear.
def author(p):return V((-p[0],-p[1]-.2,p[2]))
ROWS=json.loads((OUT/'shots.json').read_text())['shots'];ENV=json.loads((OUT/'audio_envelope.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
S=bpy.context.scene;S.name='Classroom_Master';G=Stage(S)
S.render.engine='BLENDER_EEVEE_NEXT';S.eevee.use_raytracing=False
if hasattr(S.eevee,'use_fast_gi'):S.eevee.use_fast_gi=True
S.eevee.taa_render_samples=16;S.render.use_simplify=True;S.render.simplify_subdivision=2
S.render.resolution_x=1080;S.render.resolution_y=1920;S.render.resolution_percentage=50;S.render.fps=30
S.frame_start=1;S.frame_end=1635;S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB'
S.render.film_transparent=False;S.view_settings.view_transform='AgX';S.view_settings.look='AgX - Medium High Contrast'
S.view_settings.exposure=.25
W=bpy.data.worlds.new('Quiet blue daylight');W.use_nodes=True;S.world=W
W.node_tree.nodes.get('Background').inputs[0].default_value=(*rgb('b4d5eb'),1)
W.node_tree.nodes.get('Background').inputs[1].default_value=.32
INK=mat('141115',rough=.72);METAL=mat('2b4c6f',metal=.35,rough=.35)
WOOD=noise_material('Honey oak grain','b16a32','e0a760',5,.32,.075,True)
DESK=noise_material('Orange tan desk grain','c7803e','f1be78',7,.26,.05,True)
def setloc(o,p,f):o.location=p;key(o,'location',f)
def scale(o,s,f):o.scale=(s,)*3 if isinstance(s,(float,int)) else s;key(o,'scale',f)
def curve_set(o,pts,f):
    pts=[V(p) for p in pts]
    for i,(p,pos) in enumerate(zip(o.data.splines[0].bezier_points,pts)):
        tangent=(pts[min(2,i+1)]-pts[max(0,i-1)])*(.25 if i==1 else .30)
        p.handle_left_type=p.handle_right_type='FREE';p.co=pos;p.handle_left=pos-tangent;p.handle_right=pos+tangent
        for prop in ['co','handle_left','handle_right']:p.keyframe_insert(prop,frame=f)
def ease(a,b,f):
    u=max(0.,min(1.,(f-a)/(b-a)));return u*u*(3-2*u)
def lerp(a,b,u):return V(a).lerp(V(b),u)
def text3(name,body,xyz,size,material,parent=None,align='CENTER'):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x=align;d.align_y='CENTER';d.extrude=0;d.materials.append(material)
    return G.obj(name,d,xyz,parent)
def patch(name,xyz,sx,sy):
    m=alpha_mat(name+' soft receiver','253440',.16)
    return G.ball(name,xyz,(sx,sy,.004),m)
def floor():
    G.box('Parquet foundation',(0,0,-.1),(8.4,10,.18),mat('8a5136'),bevel=0)
    # Actual short parquet blocks: alternating laid directions and restrained grain.
    mats=[noise_material('Parquet hue '+str(i),a,b,6,.20,.025,True) for i,(a,b) in enumerate([('bd7947','dca26d'),('c58c59','e6b479'),('ac6d3d','cf935d')])]
    for i in range(-7,8):
        for j in range(-8,9):
            x=i*.6;y=j*.6
            for k in range(3):
                dim=(.594,.194,.035) if (i+j)%2==0 else (.194,.594,.035)
                p=(x,y+(k-1)*.2,-.003) if (i+j)%2==0 else (x+(k-1)*.2,y,-.003)
                G.box('Parquet laid block',p,dim,mats[(i+j+k)%3],bevel=.003)
def room():
    floor();blue=mat('4ea8de',rough=.78);trim=mat('e4e7da')
    G.box('Front blue classroom wall',(0,4.25,2.1),(8.4,.18,4.2),blue,bevel=.01)
    cutaway=G.box('Camera-side cutaway right wall',(4.15,.4,2.1),(.18,7.8,4.2),blue,bevel=.01);cutaway.hide_render=True
    # Left wall built around real recessed window openings.
    G.box('Window wall sill',(-4.15,0,.53),(.2,8.5,1.06),blue,bevel=.01)
    G.box('Window wall lintel',(-4.15,0,3.82),(.2,8.5,.76),blue,bevel=.01)
    glass=mat('b1def1',rough=.12);p=glass.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.92;p.inputs['Alpha'].default_value=.16;glass.surface_render_method='BLENDED'
    for yc in [-2.85,-.05,2.75]:
        for yy in [yc-1.32,yc+1.32]:G.box('Window recess upright',(-4.13,yy,2.24),(.28,.13,2.45),trim)
        for z in [1.06,2.24,3.45]:G.box('Window frame cross rail',(-4.13,yc,z),(.3,2.73,.085),trim)
        G.box('Window central mullion',(-4.13,yc,2.24),(.27,.075,2.36),trim)
        G.box('Recessed translucent window glass',(-4.24,yc,2.24),(.018,2.5,2.30),glass,bevel=0)
        G.box('Deep window sill',(-3.99,yc,1.05),(.50,2.86,.11),mat('ecdbba'))
    for yc in [-4.2,-1.45,1.35,4.15]:G.box('Window wall stone pier',(-4.15,yc,2.2),(.2,.18,2.5),blue)
    for side in [-1,1]:G.box('Wall skirting',(side*4.02,0,.15),(.1,8.2,.24),mat('257294'))
    G.box('Front skirting',(0,4.10,.15),(8.1,.10,.24),mat('257294'))
    G.box('Blackboard wooden surround',(0,4.05,2.48),(4.6,.12,1.83),WOOD,bevel=.045)
    G.box('Dark teal chalk slate',(0,3.966,2.48),(4.39,.035,1.62),mat('0f5c6e',rough=.86),bevel=.01)
    chalk=mat('e6f1dd',rough=.9,em=.12)
    # Board front normal points toward -Y.
    for body,pos,size in [('E = mc²',(-.65,3.938,2.66),.38),('F = ma',(1.2,3.936,2.43),.19),('Physics / Energy',(0,3.936,3.02),.15)]:
        t=text3('Diegetic physics chalk',body,pos,size,chalk);t.rotation_euler=(math.pi/2,0,0)
    for i in range(4):G.curve('Chalk working line',[(-1.6,3.932,2.37-i*.15),(-.4+i*.12,3.932,2.37-i*.15)],.006,chalk)
    G.box('Chalk tray',(0,3.84,1.65),(4.55,.24,.08),WOOD)
    G.box('Teacher desk',(.9,3.02,.89),(1.7,.7,.12),DESK)
    for x in [.2,1.6]:
        for y in [2.76,3.27]:G.box('Teacher desk leg',(x,y,.43),(.075,.075,.85),METAL)
    G.box('Book on teacher desk',(.95,3.04,.99),(.42,.28,.07),mat('cc6044'))
    # Rear reading shelf provides another depth layer without text clutter.
    G.box('Bookcase back',(3.8,2.6,1.28),(.15,1.4,2.25),WOOD)
    for z in [.23,.94,1.65,2.35]:G.box('Bookcase ledge',(3.58,2.6,z),(.55,1.48,.06),WOOD)
    for n in range(12):G.box('Colored library spine',(3.53,2.0+n*.1,1.2+(n%2)*.01),(.30,.07,.44),mat(['b9553a','d6bd5b','4b8d8e'][n%3]),bevel=.009)
def desk(x,y):
    G.box('Rounded wooden student desk',(x,y,.96),(1.30,.70,.105),DESK,bevel=.045)
    G.box('Under desk wooden apron',(x,y,.845),(1.14,.59,.12),WOOD,bevel=.015)
    for dx in [-.53,.53]:
        for dy in [-.25,.25]:
            G.rod('Tubular student desk leg',(x+dx,y+dy,.04),(x+dx,y+dy,.86),.028,METAL)
            patch('Desk leg contact',(x+dx,y+dy,.019),.055,.055)
    G.box('Closed notebook',(x-.22,y+.04,1.024),(.40,.29,.028),mat('f4e7c5'),bevel=.009)
    G.box('Notebook cover stripe',(x-.22,y+.04,1.04),(.40,.035,.006),mat('5486ac'),bevel=0)
    G.rod('Blue pencil',(x+.14,y-.08,1.03),(x+.42,y+.03,1.03),.011,mat('31739c'))
def chair(x,y,name):
    root=G.obj(name+' floor pivot',xyz=(x,y,0))
    hero=abs(x)<.01 and abs(y-CHAIR_Y)<.01;half=.23 if hero else .325
    G.box(name+' supported seat',(0,0,SEAT-.03),(half*2,.61,.06),DESK,root,.025)
    for dx in [-half+.06,half-.06]:
        for dy in [-.23,.23]:G.rod(name+' connected metal leg',(dx,dy,.035),(dx,dy,SEAT-.05),.025,METAL,root)
    for dx in [-.26,.26]:G.rod(name+' lower side brace',(dx,-.22,.22),(dx,.22,.22),.018,METAL,root)
    back=G.obj(name+' backrest hinge',xyz=(0,-.29,SEAT),parent=root)
    for dx in [-.255,.255]:G.rod(name+' back upright',(dx,0,0),(dx,0,.68),.023,METAL,back)
    G.box(name+' contoured backrest',(0,0,.53),(.65,.065,.31),DESK,back,.07)
    for dx in [-.245,.245]:
        for dy in [-.23,.23]:patch(name+' grounded foot',(x+dx,y+dy,.019),.06,.055)
    return root,back
room();CHAIRS={}
for x in [-1.9,0,1.9]:
    for y in [-1.2,.65,2.5]:
        desk(x,y);CHAIRS[(x,y)]=chair(x,y-.85,'Chair %.1f %.1f'%(x,y))
SUN=G.light('Diagonal window sunlight','SUN',(-5,-2,6),(1,2,0),4.5,'ffe1ac');SUN.data.angle=math.radians(10);SUN.data.use_shadow=True
FILL=G.light('Quiet cool classroom bounce','AREA',(2.7,1.5,4.5),(0,-.2,1.1),190,'b7e2ff');FILL.data.size=5
G.light('Warm classroom ceiling bounce','AREA',(-1,-2,4),(0,0,0),120,'ffe8c6').data.size=4
G.light('Warm face-side window bounce','AREA',(1,4.5,3.5),(0,-.2,1.2),520,'ffead2').data.size=4.5
cd=bpy.data.cameras.new('Classroom optics');cd.lens=48;cd.sensor_fit='HORIZONTAL';cd.sensor_width=36;cd.clip_start=.03;cd.clip_end=80;cd.dof.use_dof=True;cd.dof.aperture_fstop=2.4
CAM=G.obj('Delivery camera',cd);S.camera=CAM
FOCUS=G.obj('Active face or physical contact focus');cd.dof.focus_object=FOCUS
def faceplane(name,path,w,h,parent):return G.plane(name,w,h,celmat(ART/path),parent=parent)
class Actor:
    def __init__(self,name,pos,teacher=False):
        self.name=name;self.pos=V(pos);self.teacher=teacher
        self.pelvis=G.ball('char_'+name+' glossy royal-blue pelvis',(0,0,0),(.245,.16,.13),mat('1d5dec',rough=.25))
        self.body=G.obj('char_'+name+' connected torso pivot');faceplane(name+' painted rounded shirt',name+'_torso.png',.82,.48,self.body)
        self.head=G.obj('char_'+name+' independent camera-facing head')
        self.aim=G.obj(name+' camera parallel head aim')
        tr=self.head.constraints.new('DAMPED_TRACK');tr.track_axis='TRACK_Z';tr.target=self.aim
        faceplane(name+' polygon hair cream head',name+'_head.png',1.13,1.13,self.head)
        self.features=G.obj(name+' grouped painted face turn',xyz=(0,0,.003),parent=self.head)
        self.faces={}
        for exp in ['look_left','look_right','clenched','scream','skeptical','smug','soul','talk_a','talk_b','talk_c','blink']:
            self.faces[exp]=faceplane(name+' face '+exp,'face_'+exp+'.png',1.13,1.13,self.features)
        if teacher:
            for x in [-.177,.177]:
                pts=[(x+.121*math.cos(i*math.tau/48),-.012+.124*math.sin(i*math.tau/48),.008) for i in range(48)]
                G.curve('Teacher round glasses',pts,.006,INK,self.head,True)
            G.curve('Glasses nose bridge',[(-.055,0,.008),(0,.013,.008),(.055,0,.008)],.005,INK,self.head)
        self.neck=G.ball(name+' neck connection',(0,0,0),(.073,.065,.13),mat('fdfaf2'))
        self.neck.hide_render=True  # Masked torso overlaps the head; no visible volumetric neck oval.
        self.arms=[];self.hands=[];self.legs=[];self.feet=[]
        for sign in [-1,1]:
            self.arms.append(G.curve(name+' curved stick arm '+str(sign),[(0,0,0)]*3,.022,INK))
            self.hands.append(G.ball(name+' rounded mitten '+str(sign),(0,0,0),(.057,.043,.062),INK))
            self.legs.append(G.curve(name+' curved stick leg '+str(sign),[(0,0,0)]*3,.024,INK))
            self.feet.append(G.ball(name+' oval grounded foot '+str(sign),(0,0,0),(.105,.15,SHOE_R),INK))
        self.drops=[]
        for i in range(4):
            drop=G.plane(name+' temple-attached cyan sweat',.10,.15,celmat(ART/'drop.png'),xyz=((-1 if i<2 else 1)*(.43+.035*(i%2)),.10-.17*(i%2),.012),parent=self.head);self.drops.append(drop)
        self.soul=G.obj(name+' translucent soul head pivot')
        soulmat=celmat(ART/(name+'_head.png')).copy();soulmat.name=name+' cyan ghost head'
        # Transparent/emissive cyan soul with actual head silhouette.
        nn=soulmat.node_tree.nodes;ll=soulmat.node_tree.links
        final=next(n for n in nn if n.type=='OUTPUT_MATERIAL');old=final.inputs[0].links[0].from_socket
        trans=nn.new('ShaderNodeBsdfTransparent');mix=nn.new('ShaderNodeMixShader');mix.inputs[0].default_value=.30
        ll.new(trans.outputs[0],mix.inputs[1]);ll.new(old,mix.inputs[2]);ll.new(mix.outputs[0],final.inputs[0]);soulmat.surface_render_method='BLENDED'
        plane=G.plane(name+' released ghostly soul bubble',.63,.63,soulmat,parent=self.soul)
        gl=G.ball(name+' cyan soul halo',(0,0,-.02),(.35,.35,.012),alpha_mat(name+' ghost cyan','78e6ff',.18),self.soul)
        self.finger=G.curve(name+' pointing index finger',[(0,0,0)]*3,.019,INK)
        self.shadows=[patch(name+' shoe contact',(0,0,.02),.12,.16) for i in range(2)]
    def pose(self,f,action,chairpair=None):
        base=self.pos.copy();standing=self.teacher;lean=0.;jump=0.;soul=0.;face='look_left';squash=1.;strain=0.;slump=0.
        if self.name=='you':
            if action in ['belly','grip','sigh','nose']:face='clenched'
            if action=='nose' and f>=1354:face='scream'
            elif action in ['head','roar','cough','jump','blame']:face='scream'
            elif action=='soul':face='soul';soul=ease(810,838,f);slump=ease(804,828,f)
            elif action in ['point_up','lean','release','teach']:face='smug'
            if action=='nervous':face='look_left' if f<42 or f>91 else 'look_right'
            if 266<=f<477:
                squash=.82;env=ease(266,272,f)*(1-ease(469,476,f));strain=.008*math.sin((f-266)*math.tau/4)*env
            if f>=978:lean=math.radians(45)*ease(978,1000,f)
            if f>=1299:lean*=1-ease(1299,1318,f)
            if f>=1410:
                if f<1422:jump=0;lean=-math.radians(8)*ease(1410,1422,f)
                elif f<1446:jump=.94*ease(1422,1446,f);lean=-math.radians(8)*(1-ease(1422,1430,f))
                elif f<1466:jump=.94-.42*ease(1446,1466,f)
                else:jump=.52+.025*(1-ease(1466,1475,f))
            if f>=1565 and ENV[f-1]>.10:face=['talk_a','talk_b','talk_c'][min(2,int(ENV[(f//3)*3-1]*3))]
        elif self.name=='friend':
            face='skeptical' if f>=804 else 'look_right'
            if f>=1484:face='scream';soul=ease(1530,1565,f)
        else:
            face='scream' if 579<=f<663 else 'look_left'
            if 1215<=f<1299:face=['talk_a','talk_b','look_left'][((f-1215)//3)%3]
            base.x+=.18*ease(490,579,f)-.18*ease(1215,1250,f)
        if (f+{'you':0,'friend':37,'teacher':81}[self.name])%121 in [0,1,2] and face not in ['scream','soul']:face='blink'
        rock=0
        if self.name=='you' and 769<=f<804:rock=math.radians(7)*math.sin((f-769)/35*math.tau*2)*math.sin((f-769)/35*math.pi)
        rootm=Matrix.Translation(base)@Matrix.Rotation(rock,4,'Y')
        hip=rootm@V((0,0,(SEAT+.13*squash if not standing else .68)+jump))
        hip.x+=strain
        if self.name=='you' and f>=978:hip.y+=.07*max(0,min(1,lean/math.radians(45)))
        axis=rootm.to_3x3()@V((0,-math.sin(lean),math.cos(lean)))
        if slump:axis=V((0,math.sin(math.radians(30)*slump),math.cos(math.radians(30)*slump)))
        normal=V((CAM.location.x-base.x,CAM.location.y-base.y,0)).normalized();right=axis.cross(normal).normalized();normal=right.cross(axis).normalized()
        q=Matrix((right,axis,normal)).transposed().to_quaternion();camq=CAM.rotation_euler.to_quaternion()
        self.pelvis.location=hip;self.pelvis.scale=(.245,.16,.13*squash);self.pelvis.rotation_euler=(0,rock,0)
        for path in ['location','scale','rotation_euler']:key(self.pelvis,path,f)
        self.body.location=hip+axis*.20;self.body.scale=(1,1+.15*slump,1);self.body.rotation_mode='QUATERNION';self.body.rotation_quaternion=q
        if slump:self.body.location=lerp(self.body.location,(0,.15,DESK_TOP-.10),slump)
        for path in ['location','scale','rotation_quaternion']:key(self.body,path,f)
        head=hip+axis*.84
        if self.name=='you' and 978<=f<1299:head=hip+axis*.40+V((0,0,.44))
        headq=camq
        if slump:
            head=lerp(head,(0,.50,DESK_TOP+.18),slump)
            basis=Matrix((V((-1,0,0)),V((0,0,1)),V((0,1,0)))).transposed().to_quaternion()
            faceup=Quaternion(V((1,0,0)),SLUMP_PITCH)@basis;headq=camq.slerp(faceup,slump)
        self.head.location=head;self.head.rotation_euler=headq.to_euler();key(self.head,'location',f);key(self.head,'rotation_euler',f)
        self.aim.location=head+headq@V((0,0,8));key(self.aim,'location',f)
        self.neck.location=hip+axis*.54;key(self.neck,'location',f)
        turn=0
        if self.name=='you' and action=='nervous':turn=-.5 if face=='look_left' else .5
        if self.name=='friend' and 804<=f<905:turn=.9
        if self.name=='you' and action=='blame':turn=.6
        self.features.location.x=.10*turn;key(self.features,'location',f);self.head['turn_x']=turn;self.head.keyframe_insert('["turn_x"]',frame=f)
        for exp,ob in self.faces.items():scale(ob,1 if exp==face else 0,f)
        for drop in self.drops:scale(drop,1 if face=='clenched' or (action=='blame' and self.name=='friend') else 0,f)
        self.soul.location=head+V((0,0,.2+.72*soul));self.soul.rotation_euler=CAM.rotation_euler;key(self.soul,'location',f);key(self.soul,'rotation_euler',f);scale(self.soul,soul if soul else 0,f)
        finger_on=False;finger_end=None;finger_hand=None
        for i,sign in enumerate([-1,1]):
            shoulder=self.body.location+axis*.11+right*(sign*.225)-normal*.015
            elbow=shoulder+right*(sign*.16)-axis*.22;hand=hip+right*(sign*.31)+axis*.03+normal*.045
            if self.name=='you':
                if action in ['belly','roar']:
                    hand=hip+axis*.27+right*(sign*.09)+normal*.06;elbow=hip+right*(sign*.42)+axis*.28
                    if action=='roar':hand+=axis*(.035*math.sin((f-477)/102*math.tau*3)*math.sin((f-477)/102*math.pi))
                elif action=='head':hand=head+right*(sign*.48)+V((0,0,.22));elbow=head+right*(sign*.70)+V((0,0,-.18))
                elif action in ['grip','sigh']:
                    side=sign*(1 if right.x>=0 else -1);hand=rootm@V((side*.23,0,SEAT));elbow=shoulder+V((side*.14,-.10,-.16))
                elif action=='cough':
                    beat=max(0,math.sin((f-663)/72*math.pi*6))*.055;hand=head+camq@V((0,-.24,.08)) if i==1 else hip+axis*(.37+beat)+normal*.09;elbow=shoulder+right*(sign*.28)-axis*.18
                elif action=='scuff_rock' and f>=769:hand=hip+axis*.35-right*(sign*.14)+normal*.07
                elif action=='soul':
                    hand=lerp(hand,(sign*.33,.40,DESK_TOP+.04),slump);elbow=lerp(elbow,(sign*.48,.20,DESK_TOP+.055),slump)
                elif action=='point_up' and i==1:
                    hand=head+right*.65+V((0,0,.03));elbow=head+right*.77+V((0,0,-.40));finger_on=True;finger_hand=hand;finger_end=hand+V((0,0,.20))
                elif action=='nose' and i==1:
                    hand=head+headq@V((0,-.14,.045));elbow=head+headq@V((.67,-.48,.015))
                elif action=='blame':
                    if i==0:hand=hip+V((1.0,-.05,.45));elbow=shoulder+V((.34,-.06,.02));finger_on=True;finger_hand=hand;finger_end=hand+V((.20,0,-.015))
                    else:hand=head+right*.72+V((0,0,.43));elbow=head+right*.79+V((0,0,-.20))
            elif self.name=='friend' and f>=1484:hand=hip+right*(sign*.74)+axis*.52;elbow=hip+right*(sign*.56)+axis*.29
            elif self.teacher:
                if 1215<=f<1299 and i==1:hand=hip+right*.53+axis*(.71+.09*ease(1215,1245,f));elbow=shoulder+right*.37
                elif 579<=f<663:hand=hip+right*(sign*.54)+axis*.44;elbow=hip+right*(sign*.46)+axis*.17
            curve_set(self.arms[i],[shoulder,elbow,hand],f);setloc(self.hands[i],hand,f)
            perched=self.name=='you' and f>=1466
            foot_r=SHOE_R+(.035-SHOE_R)*ease(1422,1434,f) if self.name=='you' else SHOE_R
            self.feet[i].scale=(.105,.15,foot_r);key(self.feet[i],'scale',f)
            land=base+V((sign*.12,sign*.10,SEAT+foot_r))
            if standing or perched:
                foot=land if perched else base+V((sign*.18,.04,.03));knee=lerp(hip+right*(sign*.13),foot,.54)+V((0,.06,0))
            elif self.name=='you' and 1422<=f<1466:
                u=ease(1422,1434,f);v=ease(1446,1466,f)
                foot=lerp(base+V((sign*.15,.49,.03)),hip+V((sign*.17,.11+sign*.10,-.43)),u)
                knee=lerp(base+V((sign*.15,.40,SEAT+.02)),hip+V((sign*.15,.25,-.18)),u)
                foot=lerp(foot,land,v);knee=lerp(knee,lerp(hip+right*(sign*.13),land,.54)+V((0,.06,0)),v)
            else:
                scuff=0
                if self.name=='you' and 735<=f<769:
                    t=(f-735+i*4)%8;scuff=-.12+.06*t if t<=4 else .12-.06*(t-4)
                foot=base+V((sign*.15,.49+scuff,.03));knee=base+V((sign*.15,.40,SEAT+.02))
            thigh=hip+V((sign*.13,0,-.03));curve_set(self.legs[i],[thigh,knee,foot],f);setloc(self.feet[i],foot,f)
            setloc(self.shadows[i],(foot.x,foot.y,SEAT+.002 if perched else .0155),f);scale(self.shadows[i],0 if self.name=='you' and 1422<=f<1466 else (.12,.16,.004),f)
        if finger_on:curve_set(self.finger,[finger_hand,lerp(finger_hand,finger_end,.5),finger_end],f)
        scale(self.finger,1 if finger_on else 0,f)
        if chairpair and self.name=='you':
            cr,back=chairpair;cr.rotation_euler.y=rock;key(cr,'rotation_euler',f);back.rotation_euler.x=max(0,lean)/3;key(back,'rotation_euler',f)
        return {'hip':list(hip),'head':list(head),'lean_degrees':math.degrees(lean),'slump':slump,'squash':squash,'strain_x':strain}

YOU=Actor('you',(0,-.2,0));FRIEND=Actor('friend',(1.9,-.2,0));TEACHER=Actor('teacher',(-1.1,3.25,0),True)
BELLY=G.light('Internal pressure pulse','POINT',(0,-.2,1.01),(0,0,0),0,'badc46');BELLY.data.shadow_soft_size=.22
GASLIGHT=G.light('Translucent vapor local bounce','POINT',(0,-.6,.80),(0,0,0),0,'8bff69');GASLIGHT.data.shadow_soft_size=.7
def vapor_material(name,alpha,emission,tint='afff6c',radial=True):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.surface_render_method='BLENDED'
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=image(ART/'vapor.png')
    p.inputs['Base Color'].default_value=(*rgb(tint),1);p.inputs['Emission Color'].default_value=(*rgb(tint),1);p.inputs['Emission Strength'].default_value=emission;p.inputs['Roughness'].default_value=1
    oi=n.new('ShaderNodeObjectInfo');mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=alpha
    if radial:l.new(tex.outputs['Alpha'],mult.inputs[0])
    else:mult.inputs[0].default_value=1
    gate=n.new('ShaderNodeMath');gate.operation='MULTIPLY';l.new(mult.outputs[0],gate.inputs[0]);l.new(oi.outputs['Alpha'],gate.inputs[1]);l.new(gate.outputs[0],p.inputs['Alpha']);return m
VM=vapor_material('V2 rear stream alpha .36 emission 2.4',.36,2.4)
STREAM=[G.plane('V2 rear fart stream '+str(i),2,2,VM) for i in range(14)]
HM=vapor_material('V2 toxic haze alpha .28',.28,1.2,'d1ff69');HAZE=[G.plane('V2 desk toxic haze '+str(i),2,2,HM) for i in range(16)]
PM=vapor_material('V2 compressed seat pressure',.25,2.4,'89ff42',False)
PRESSURE=[G.ball('V2 centered compressed pressure '+str(i),(0,CHAIR_Y,SEAT+.03),(.13-i*.025,.11-i*.02,.018-i*.004),PM) for i in range(3)]
RINGS=[G.curve('Generator acoustic wave '+str(i),[(math.cos(k*math.tau/64),math.sin(k*math.tau/64),0) for k in range(64)],.015,alpha_mat('Sound ring '+str(i),'ef9a37',.48),closed=True) for i in range(3)]
QUESTIONS=[text3('Elastic question mark '+str(i),'?',(0,0,0),.40,mat('ffd75d',em=.5)) for i in range(3)]
CM=VM.copy();CM.name='Soft radial white cough vapor';cp=CM.node_tree.nodes.get('Principled BSDF')
for slot in ['Base Color','Emission Color']:
    for link in list(cp.inputs[slot].links):CM.node_tree.links.remove(link)
    cp.inputs[slot].default_value=(*rgb('f5eee2'),1)
cp.inputs['Emission Strength'].default_value=.4
COUGHS=[G.plane('White soft cough puff '+str(i),.24,.24,CM) for i in range(4)]
def camera_pose(f,row):
    a,b=row['start_frame'],row['end_frame'];u=(f-a)/max(1,b-a);shot=row['shot'];lens=48
    # Explicit motivated coverage; main subjects are staged in the portrait safe area.
    views={
    '1A':((1.35,2.45,2.35),(0,-.2,1.10),48),
    '1B':((.40,1.90,1.65),(0,-.2,1.45),55),
    '1C':((.7,2.3,2.0),(0,-.2,1.45),45),
    '2A':((1.28,.2,.63),(0,-.2,.49),65),
    '2B':((.45,2.55,1.75),(0,-.2,1.10),52),
    '2C':((.18,2.55,1.70),(0,-.2,1.56),75),
    '2D':((1.1,2.1,1.75),(0,-.2,1.25),48),
    '2E':((1.8,-1.0,2.1),(-1.1,3.25,1.5),60),
    '3A':((-.5,2.4,1.8),(0,-.2,1.35),52),
    '3B':((.55,1.35,.27),(0,.49,.08),58),
    '3C':((.75,2.0,4.5),(.75,.35,1.1),35),
    '4A':((.2,2.55,1.85),(0,-.2,1.55),58),
    '4B':(tuple(author((1.65,-.55,1.05))),tuple(author((-.10,.10,.95))),28),
    '4C':(tuple(author((1.15,.45,.82))),tuple(author((0,.20,.66))),23),
    '4D':((2.1,-3.6,2.55),(-.25,1.4,1.31),40),
    '5A':((.4,2.45,1.8),(0,-.2,1.30),52),
    '5B':((-2.6,.1,1.2),(0,-.2,1.25),43),
    '5C':((-1.2,2.5,2.25),(.81,-.31,1.70),43)}
    p,t,lens=views[shot]
    if shot=='3B' and f>=769:p,t,lens=((1.15,2.55,1.8),(0,-.2,1.1),48);u=(f-769)/34
    if shot=='4B' and f>=1035:p,t,lens=(tuple(author((1.05,-.25,.72))),tuple(author((0,-.07,.59))),50);u=(f-1035)/47
    p,t=V(p),V(t)
    margin={'3B':1.5 if f<769 else 1.,'4A':1.25,'5B':1.25,'5C':1.50}.get(shot,1.)
    p=t+(p-t)*margin*(1-.10*u);p.x+=.055*u
    CAM.location=p;CAM.rotation_euler=(t-p).to_track_quat('-Z','Y').to_euler();CAM.data.lens=lens
    FOCUS.location=V((.23,CHAIR_Y,SEAT+.05)) if shot=='2A' else author((.23,-.07,SEAT+.06)) if shot=='4B' and f>=1035 else t
    key(CAM,'location',f);key(CAM,'rotation_euler',f);CAM.data.keyframe_insert('lens',frame=f);key(FOCUS,'location',f)
def effects(f,row,pose):
    action=row['action'];head=V(pose['head']);q=CAM.rotation_euler.to_quaternion()
    BELLY.data.energy=(35+20*math.sin((f-123)/75*math.tau*3)) if action=='belly' else 0;BELLY.data.keyframe_insert('energy',frame=f)
    GASLIGHT.data.energy=22 if action in ['release','nose'] else 14 if action=='grip' else 0;GASLIGHT.data.keyframe_insert('energy',frame=f)
    active_pressure=action in ['grip','sigh']
    pressure_pos=V((0,CHAIR_Y,SEAT+.03))
    for i,p in enumerate(PRESSURE):
        setloc(p,pressure_pos,f);scale(p,(.23-i*.025,.19-i*.025,.018-i*.004) if active_pressure else 0,f)
        p.color=(1,1,1,1 if active_pressure else 0);p.keyframe_insert('color',index=3,frame=f)
    gaspos=pressure_pos if active_pressure else V(pose['hip'])+V((0,-.12,.04))
    if action=='nose':gaspos=head+V((.25,.12,-.12))
    setloc(GASLIGHT,gaspos,f)
    GASLIGHT.data.energy=12 if active_pressure or action=='release' else (45+18*math.sin((f-1299)*math.tau/18)) if action=='nose' else 0
    GASLIGHT.data.keyframe_insert('energy',frame=f)
    for i,p in enumerate(STREAM):
        on=0;pos=V(pose['hip'])+V((0,-.12,0));pos.z=SEAT+.04;r=.07
        if action=='release' and f>=1085:
            age=f-1085-i*9
            if 0<=age<80:
                t=age;u=t/80;on=ease(0,8,t)*(1-ease(60,80,t))*(1-ease(1204,1215,f))
                pos+=V((.06*math.sin(i*1.7+u*2),-.90*u,.20*u));r=.06+.05*u
        p.location=pos;p.rotation_euler=CAM.rotation_euler;p.scale=(r,r*(1.1+.2*math.sin(i)),1) if on else (0,0,0)
        p.color=(1,1,1,on)
        for path in ['location','rotation_euler','scale']:key(p,path,f)
        p.keyframe_insert('color',index=3,frame=f)
    for i,p in enumerate(HAZE):
        on=0;r=.25+.2*((i*7)%16)/15;age=f-1299-i*3;u=max(0,min(1,age/75))
        side=-1 if i%2==0 else 1;foreground=i%4<2
        pos=V((side*(.45+.14*((i//2)%4)),(.55+.10*(i%3)) if foreground else (-.45-.15*(i%3)),(DESK_TOP+.06 if foreground else .69)+.18*u))
        if action=='nose' and age>=0:on=ease(0,12,age)*(1-ease(1400,1410,f))
        p.location=pos;p.rotation_euler=CAM.rotation_euler;p.scale=(r,r*.70,1) if on else (0,0,0);p.color=(1,1,1,on)
        for path in ['location','rotation_euler','scale']:key(p,path,f)
        p.keyframe_insert('color',index=3,frame=f)
    for i,r in enumerate(RINGS):
        age=(f-477-i*24);u=max(0,min(1,age/60));on=math.sin(math.pi*u) if action=='roar' and 0<age<60 else 0
        r.location=V(pose['hip'])+V((0,.20,.30));r.rotation_euler=CAM.rotation_euler;key(r,'location',f);key(r,'rotation_euler',f);scale(r,((.2+.65*u)*on,)*3,f)
    for i,t in enumerate(QUESTIONS):
        on=ease(201+i*3,213+i*3,f) if action=='head' else 0
        t.location=head+q@V(((i-1)*.38,.59+.09*math.sin(min(1,on)*math.pi),.02));t.rotation_euler=CAM.rotation_euler;key(t,'location',f);key(t,'rotation_euler',f);scale(t,on,f)
    for i,p in enumerate(COUGHS):
        age=f-668-i*15;u=max(0,min(1,age/25));on=math.sin(u*math.pi) if action=='cough' and 0<age<25 else 0
        p.location=head+q@V((.10+.45*u,-.18+.12*u,.15));p.rotation_euler=CAM.rotation_euler;key(p,'location',f);key(p,'rotation_euler',f);scale(p,on*(1+u),f)
    # Motivated warning/dispersion changes remain subordinate to readable daylight.
    FILL.data.energy=190 if action not in ['nose','release'] else 160;FILL.data.keyframe_insert('energy',frame=f)
def compose(scene,row):
    scene.use_nodes=True;n=scene.node_tree.nodes;n.clear();l=scene.node_tree.links
    rl=n.new('CompositorNodeRLayers');rl.scene=scene
    glow=n.new('CompositorNodeGlare');glow.glare_type='FOG_GLOW';glow.threshold=.8;glow.mix=-.64;glow.quality='MEDIUM';glow.size=7;l.new(rl.outputs['Image'],glow.inputs[0])
    # -0.64 is 18% glow in Blender 4.2's [-1,1] mix convention.
    hs=n.new('CompositorNodeHueSat');hs.inputs['Saturation'].default_value=1.16;l.new(glow.outputs[0],hs.inputs['Image'])
    mask=n.new('CompositorNodeEllipseMask');mask.width=.96;mask.height=.98
    blur=n.new('CompositorNodeBlur');blur.filter_type='GAUSS';blur.size_x=150;blur.size_y=250;l.new(mask.outputs[0],blur.inputs[0])
    mp=n.new('CompositorNodeMapRange');mp.inputs['To Min'].default_value=.91;mp.inputs['To Max'].default_value=1.;l.new(blur.outputs[0],mp.inputs['Value'])
    mult=n.new('CompositorNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;l.new(hs.outputs[0],mult.inputs[1]);l.new(mp.outputs[0],mult.inputs[2])
    ui=n.new('CompositorNodeImage');ui.image=image(ART/f'hud_{row["shot"]}.png');sc=n.new('CompositorNodeScale');sc.space='RENDER_SIZE';l.new(ui.outputs[0],sc.inputs[0])
    over=n.new('CompositorNodeAlphaOver');l.new(mult.outputs[0],over.inputs[1]);l.new(sc.outputs[0],over.inputs[2]);out=n.new('CompositorNodeComposite');l.new(over.outputs[0],out.inputs[0])
print('Baking finite poses, camera coverage and physical supports...',flush=True)
checks=[]
for row in ROWS:
    for f in range(row['start_frame'],row['end_frame']+1):
        camera_pose(f,row);pose=YOU.pose(f,row['action'],CHAIRS[(0,.65)]);FRIEND.pose(f,row['action']);TEACHER.pose(f,row['action']);effects(f,row,pose)
        if f in [1,266,336,971,1021,1035,1083,1410,1446,1466,1484,1635]:checks.append({'frame':f,**pose})
    print('Baked cut',row['shot'],flush=True)
for o in bpy.data.objects:
    linear(o)
    if o.type in ['CURVE','LIGHT','CAMERA']:linear(o.data)
    # Discrete cels switch scale with CONSTANT interpolation, all other channels are baked linear.
    if ' face ' in o.name and o.animation_data:
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='CONSTANT'
    # Wide blackboard shot: the adjacent foreground pupil is outside coverage;
    # hide that camera-side staging layer instead of showing a cropped face.
    if o.name.startswith(('friend','char_friend')) and o!=FRIEND.neck:
        for f,hidden in [(1,False),(1214,False),(1215,True),(1298,True),(1299,False),(1409,False),(1410,True),(1483,True),(1484,False),(1635,False)]:
            o.hide_render=hidden;key(o,'hide_render',f)
        if o.animation_data and o.animation_data.action:
            for fc in o.animation_data.action.fcurves:
                if fc.data_path=='hide_render':
                    for k in fc.keyframe_points:k.interpolation='CONSTANT'
def children_recursive(o):
    for child in o.children:yield child;yield from children_recursive(child)
teacher_layers={o for o in bpy.data.objects if o.name.startswith(('teacher','char_teacher')) and o!=TEACHER.neck}
teacher_layers.update(children_recursive(TEACHER.head))
for o in teacher_layers:
    for f,hidden in [(1,False),(803,False),(804,True),(904,True),(905,False),(1483,False),(1484,True),(1635,True)]:o.hide_render=hidden;key(o,'hide_render',f)
    for fc in o.animation_data.action.fcurves:
        if fc.data_path=='hide_render':
            for k in fc.keyframe_points:k.interpolation='CONSTANT'
scenes=[]
for row in ROWS:
    s=S.copy();s.name='CF_'+row['shot'];s.frame_start=row['start_frame'];s.frame_end=row['end_frame'];s.camera=CAM;compose(s,row)
    row['scene']=s.name;row['camera']=CAM.name;scenes.append(s)
S.use_nodes=False
OUT.joinpath('shots.json').write_text(json.dumps({'fps':30,'frames':1635,'shots':ROWS},indent=2))
OUT.joinpath('shots_v2.json').write_text(json.dumps({'fps':30,'frames':1635,'shots':ROWS},indent=2))
OUT.joinpath('build_contacts_v2.json').write_text(json.dumps({'seat_top_z':SEAT,'grip_x':[-.23,.23],'seated_pelvis_bottom':SEAT,'standing_feet_bottom':SEAT,'lean_target_degrees':45,'slump_head_center_z':DESK_TOP+.18,'poses':checks},indent=2))
stage=G.obj('V2 world coordinate rebase');stage.location=(0,-.2,0);stage.rotation_euler.z=math.pi
for o in list(S.objects):
    if o!=stage and o.parent is None:o.parent=stage;o.matrix_parent_inverse=Matrix.Identity(4)
for s in scenes:
    if stage.name not in s.objects:s.collection.objects.link(stage)
bpy.context.window.scene=scenes[0];scenes[0].frame_set(1)
S['project']='classroom_fart';S['audio_source']='ElevenLabs_2026-11-12T19_21_24_Viraj';S['narration']='Internal/narrator except quoted protagonist dialogue frames 1565..1635; teacher teaching gesture frames1215..1298.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'classroom_fart_surgical_v2_raw.blend'))
from optimize_static import optimize
optimization=optimize(scenes[0]);OUT.joinpath('static_optimization_v2.json').write_text(json.dumps(optimization,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'classroom_fart_surgical_v2.blend'))
print('Saved isolated build.',flush=True)
