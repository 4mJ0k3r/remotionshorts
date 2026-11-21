"""Deterministic 2,124-frame acting and camera timeline. No movie render on load."""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Quaternion
V=Vector;S=bpy.context.scene;O=S.objects;ROOT=Path(S['studio_root']);OUT=ROOT/'renders/crorepati_poop_love'
rig_ns={};exec(bpy.data.texts['crorepati_rig.py'].as_string(),rig_ns);Actor=rig_ns['Actor']
story_ns={};exec(bpy.data.texts['crorepati_story.py'].as_string(),story_ns);SHOTS=story_ns['SHOTS'];OFFSETS=story_ns['OFFSETS']
ENV=json.loads(bpy.data.texts['crorepati_audio_env.json'].as_string())
ns={};exec(bpy.data.texts['studio_set_ink.py'].as_string(),ns);INK=ns['SetInk'](S)
ACT={who:Actor(who) for who in ['broke','millionaire','butler','kid1','kid2']}
GROUPS={name:[O[name]]+list(O[name].children_recursive) for name in [o.name for o in O if o.name.startswith('SET_')]+['EntranceArchitecture','ParkPadlock','CafeKickingBoot','FoldedNewspaper','GoldenPlunger','RingBox','GoldenCrown','AnkleTrousers','GoldenToiletA','GoldenToiletB','ChildPottyA','ChildPottyB','LeatherSuitcase0','LeatherSuitcase1','CuddleBlanket','EmptyPocket0','EmptyPocket1']}
FX=[o for o in O if any(o.name.startswith(p) for p in ['HeartFX','SparkFX','DustFX','ConfettiFX','SteamFX','ProposalRosePetal'])]
FX=list({o.name:o for root in FX for o in [root]+list(root.children_recursive)}.values())
LAST_STAGE=None

def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
def sync():
    if not S.get('_audit_transforms_only',False):bpy.context.view_layer.update()
def ramp(f,a,b):return ease((f-a)/(b-a))
def interp(a,b,t):return V(a).lerp(V(b),t)
def walking_root(f,cut):
    if cut==4:
        t=ramp(f,327,360);y=-.15+1.05*t;return V((75.10,y,.08 if y<.05 else .12))
    if cut==9:
        t=ramp(f,880,935);y=2.75+2.6*t;z=0 if y<3.47 else min(1.08,(int((y-3.47)/.23)+1)*.12);return V((75,y,z))
    t=ramp(f,1178,1293);return V((74.28,1.83+.44*t,0))
leg_ns={};exec(bpy.data.texts['studio_foot_stepper.py'].as_string(),leg_ns);STEPS={}
for c,start,end in [(4,327,360),(9,880,935),(12,1178,1293)]:
    at=lambda f,c=c,start=start,end=end:tuple(walking_root(max(start,min(end,f)),c))
    STEPS[c]=leg_ns['FootStepper'](at,[(start,end,1)],size=.88,step_speed=math.pi/4 if c==9 else .45,frames=2124)
def visible(name,on):
    for o in GROUPS.get(name,[]):o.hide_render=not on
def move(name,p,q=None):
    o=O[name];o.location=p
    if q is not None:o.rotation_mode='QUATERNION';o.rotation_quaternion=q
    return o
def speech(f,a,b):return int(round(ENV[max(0,min(len(ENV)-1,f-1))]*5)) if a<=f<=b else 0
def active(stage):
    global LAST_STAGE
    if stage!=LAST_STAGE:
        for name in OFFSETS:visible('SET_'+name,name==stage)
        colors=O['SET_'+stage].get('sky_colors')
        if colors:
            for element,h in zip(S.world.node_tree.nodes['WorldCameraSkyRamp'].color_ramp.elements,reversed(colors)):
                channels=[int(h[i:i+2],16)/255 for i in (0,2,4)]
                element.color=(*(v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in channels),1)
        LAST_STAGE=stage
def camera(pos,target,focus,two=False,lens=43):
    _,a,b,_=next((v for v in SHOTS if v[1]<=S.frame_current<v[2]),SHOTS[-1])
    u=(S.frame_current-a)/max(1,b-a-1)
    pos=V(target)+(V(pos)-V(target))*(1-.10*u)
    cam=S.camera;cam.location=pos;cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(V(target)-V(pos)).to_track_quat('-Z','Y');cam.data.lens=lens
    cam.data.dof.use_dof=True;cam.data.dof.aperture_fstop=5.8 if two else 4.5;cam.data.dof.focus_distance=(V(focus)-V(pos)).length
    sync();return cam.rotation_quaternion.copy()
def shot_cam(x,y,u,two=False,close=False,high=False):
    distance=5.05 if two else (2.65 if close else 3.45)
    target=V((x,y,1.20 if not close else 1.58));pos=target+V((.11,-distance,.45 if not high else 2.35))
    return camera(pos,target,(x,y,1.63),two,43 if not high else 39)
def pose(who,p,q,expr='neutral',ward=None,**kw):
    if ward is None:ward={'broke':'ragged','millionaire':'purple','butler':'butler','kid1':'kid1','kid2':'kid2'}[who]
    return ACT[who].pose(p,q,expr,ward,**kw)
def hearts(f,source,start,count=12):
    for i in range(count):
        age=(f-start-i*2)/40
        if age<0 or age>1.8:continue
        age=min(age,1.5);a=i*2.399
        p=V(source)+V((math.cos(a)*(.10+.45*age),-.03-.12*math.sin(a),.06+age*.50))
        o=move('HeartFX%02d'%i,p,S.camera.matrix_world.to_quaternion()@Quaternion((1,0,0),-math.pi/2));o.hide_render=False;o.scale=(.45*(1-min(1,age/1.8)),)*3
def glints(f,source,count=8,scale=1):
    for i in range(count):
        p=V(source)+V((math.sin(i*2.5)*.22,math.cos(i*1.7)*.13,.08+math.sin(i*2)*.18));o=move('SparkFX%02d'%i,p,S.camera.matrix_world.to_quaternion());o.hide_render=False;o.scale=(scale*(.6+.35*math.sin(f*.18+i)),)*3
        for child in o.children_recursive:child.hide_render=False
def held(name,hand,q,local=(0,0,0)):
    visible(name,True);return move(name,V(hand)-q@V(local),q)
def knock(f,localz=(1.15,1.24),left=False):
    door=O['MansionDoorL hinge' if left else 'MansionDoorR hinge'];sync();pts=[]
    phase=(f%12)/12;retract=.055*max(0,math.cos(phase*math.tau))
    for x,z in zip([.45,.72] if left else [-.55,-.28],localz):pts.append(door.matrix_world@V((x,-.080-retract,z)))
    return pts
def steam(f,ch):
    q=ch['q'];n=ch['n'];right=q@V((1,0,0));up=q@V((0,1,0))
    for j in range(4):
        o=O['SteamFX%02d'%j];o.hide_render=False;side=-1 if j<2 else 1;source=ch['head']+q@V((side*.34,.04,-.02));verts=[]
        for k in range(18):
            t=k/17;center=source+up*(t*.52)+right*(side*(.025+.055*math.sin(t*9-(f-1178)*.08+j)))
            width=.035*math.sin(math.pi*t);verts.extend([center-right*width,center+right*width])
        for v,p in zip(o.data.vertices,verts):v.co=p
        o.data.update()
def set_stamp(f,cut):
    title=None
    for number,text,a,b in [(12,'DAY_30',1178,1245),(13,'DAY_60',1293,1350),(14,'DAY_100',1385,1445),(15,'DAY_200_PARIS',1451,1530),(18,'5_YEARS_LATER',1757,1850)]:
        if cut==number and number==18 and a<=f<=b:title=text
    node=S.node_tree.nodes['CalendarImage'];S.node_tree.nodes['CalendarOver'].inputs[0].default_value=1 if title else 0
    if title:node.image=bpy.data.images['stamp_'+title+'.png']

def update(scene,*unused):
    f=scene.frame_current;cut,a,b,peak=next((v for v in SHOTS if v[1]<=f<v[2]),SHOTS[-1]);u=(f-a)/max(1,b-a-1)
    for actor in ACT.values():actor.visible(False)
    for o in FX:o.hide_render=True
    for name in ['FoldedNewspaper','GoldenPlunger','RingBox','GoldenCrown','AnkleTrousers','CafeKickingBoot','LeatherSuitcase0','LeatherSuitcase1']:visible(name,False)
    O['AmberShockwave'].hide_render=True;O['RollingBronzeCoin'].hide_render=True
    for i in range(2):visible('EmptyPocket'+str(i),False)
    O['PinkHeartLight'].data.energy=0
    visible('EntranceArchitecture',cut in [4,5,6,7] or cut==9 and f<886)
    for i,name in enumerate(['GoldenToiletA','GoldenToiletB','ChildPottyA','ChildPottyB']):visible(name,cut==10 and f<1015 and i==0 or cut==18 and f<1880)
    set_stamp(f,cut)
    O['MansionDoorL hinge'].rotation_euler.z=0;O['MansionDoorR hinge'].rotation_euler.z=0
    O['CafeDoor hinge'].rotation_euler.z=0;O['ParkPadlock'].rotation_euler=(0,0,0)
    O['ChandelierPivot'].rotation_euler=(0,0,0)
    O['GoldenToiletA'].location=(0,.65,0)
    # The reclined rear head must stay ahead of the sofa's backrest rather
    # than being cut in half by its front face in the high cuddle camera.
    for obj in O:
        if obj.name.startswith('Sofa buttoned back'):obj.location.y=1.48 if cut==13 else 1.20
        elif obj.name.startswith('Velvet tuft button'):obj.location.y=1.335 if cut==13 else 1.055
    if cut in [1,2]:
        active('STREET');q=shot_cam(0,0,u,close=cut==2)
        if cut==1:
            pull=ramp(f,8,30);hands=[V((sgn*(.18+.025*pull),-.13,.57)) for sgn in [-1,1]]
            ch=pose('broke',(0,0,0),q,'sad',hands=hands)
            for i,sgn in enumerate([-1,1]):
                visible('EmptyPocket'+str(i),True);o=move('EmptyPocket'+str(i),V((sgn*.175,-.09,.72))+ch['n']*.035,q);o.scale=(1,.65+.35*pull,1)
            coin=move('RollingBronzeCoin',(-.25+.60*ramp(f,10,66),-.38,.055));coin.hide_render=False;coin.rotation_euler=(math.pi/2,f*.14,0)
        else:
            hands=[V((-.03,-.10,.92)),V((.26,.16,.65))]
            feet=[V((-.11+.025*math.sin(f*.7),0,.047)),V((.11-.025*math.sin(f*.7),0,.047))]
            ch=pose('broke',(0,0,0),q,'panic',hands=hands,feet=feet,tears=True)
            rig_ns['swap'](O['broke_head'],'head_broke_flush')
            O['BellyWarning'].hide_render=False;move('BellyWarning',(.0,-.08,.95));O['BellyWarning'].data.energy=18+12*math.sin(f*.35)
            if 120<=f<=160:S.camera.location.x+=.008*math.sin((f-120)*2)*math.sin(math.pi*(f-120)/40)
    elif cut==3 and f<264:
        active('PARK');q=shot_cam(25,.55,u)
        O['ParkPadlock'].rotation_euler.x=.08*math.sin((f-204)*.9);sync()
        lock=O['ParkPadlock'].matrix_world;hands=[lock@V((-.11,-.12,-.23)),lock@V((.11,-.12,-.23))]
        pose('broke',(25,.43,0),q,'panic',hands=hands)
    elif cut==3:
        active('CAFE')
        O['CafeDoor hinge'].rotation_euler.z=math.radians(70)*ramp(f,264,274)
        t=ramp(f,270,305);pos=V((50+.4*t,-.50-.35*t,.35*math.sin(math.pi*t)))
        aim=50+.4*t+.85*math.sin(math.pi*t)
        q=camera((aim,-4.8,2.0),(aim,-.35,1.10),(aim,-.85,1.35),False,35)
        roll=-62*math.sin(math.pi*t)*(1-ramp(f,305,321));ch=pose('broke',pos,q,'panic',ward='booted',roll=roll)
        visible('CafeKickingBoot',f<299);O['CafeKickingBoot'].location=(0,.80-.50*ramp(f,265,278),.88)
    elif cut in [4,5,6,7]:
        active('MANSION');visible('EntranceArchitecture',True)
        q=shot_cam(75.0,.93,u,two=cut in [5,6,7],close=False)
        if cut==4:
            q=camera((74.0,-2.25,1.05),(75.25,1.0,1.35),(75.35,.9,1.82),False,39)
            root=walking_root(f,4);hands=knock(f)
            pose('broke',root,q,'panic',hands=hands,feet=STEPS[4].at(min(360,f))['feet'])
        elif cut==5:
            openp=ramp(f,453,466)*(1-ramp(f,488,498));O['MansionDoorR hinge'].rotation_euler.z=-math.radians(65)*openp
            pose('broke',(74.53,.55,.13),q,'shock',turn=1)
            pose('butler',(75.36,1.68,.12),q,'angry',turn=-.3)
            if 498<=f<=504:S.camera.location.x+=.018*math.sin((f-498)*2)*max(0,1-(f-498)/7)
        elif cut==6:
            p=ramp(f,550,570);O['MansionDoorL hinge'].rotation_euler.z=math.radians(78)*p;O['MansionDoorR hinge'].rotation_euler.z=-math.radians(78)*p
            pose('broke',(74.57,.65,.13),q,'plead',hands=knock(f,left=True) if f<546 else None,turn=1)
            if f>=550:pose('millionaire',(75.30,1.69,.12),q,'warm',turn=-.4)
        else:
            O['MansionDoorL hinge'].rotation_euler.z=math.radians(78);O['MansionDoorR hinge'].rotation_euler.z=-math.radians(78)
            root=V((74.55,.62,-.12));prayer=[root+V((.05,-.06,1.16)),root+V((.12,-.06,1.16))]
            ch=pose('broke',root,q,'plead',hands=prayer,kneel=True,tears=True,talk=speech(f,645,744),turn=.7,ground=.12)
            pose('millionaire',(75.45,1.5,.12),q,'warm',turn=-.5)
    elif cut==8:
        active('MANSION');visible('EntranceArchitecture',False);q=shot_cam(75,2.85,u,close=True)
        pose('millionaire',(75,2.85,0),q,'warm',hands=[None,V((75.38,2.90,1.45))],turn=.3)
    elif cut==9 and f<886:
        active('MANSION');visible('EntranceArchitecture',True);q=shot_cam(75,.83,u,two=True)
        O['MansionDoorL hinge'].rotation_euler.z=math.radians(80);O['MansionDoorR hinge'].rotation_euler.z=-math.radians(80)
        kiss=ramp(f,830,848)*(1-ramp(f,875,885));sep=.53-.125*kiss
        rich=pose('millionaire',(75+sep,1.0,.10),q,'surprisedBlush',turn=-1,mouth_style='o')
        cheek=rich['head'];hands=[cheek+q@V((-.32,-.18,.035)),cheek+q@V((-.13,-.30,.035))]
        hero=pose('broke',(75-sep,1.0,.10),q,'kiss' if kiss>.85 else 'warm',hands=hands if kiss>.5 else None,turn=1)
        if 848<=f<=875:
            for who,ch,sgn in [('broke',hero,1),('millionaire',rich,-1)]:
                O[who+'_mouth'].location=ch['head']+q@V((sgn*(sep-.035),-.13,.025))
            O['KissLips'].hide_render=False;move('KissLips',(hero['head']+rich['head'])*.5+q@V((0,-.13,.045)),q)
            hearts(f,(75,1.0,max(hero['head'].z,rich['head'].z)+.44),848)
            O['PinkHeartLight'].location=(75,.6,1.7);O['PinkHeartLight'].data.energy=25
    elif cut==9:
        active('MANSION');visible('EntranceArchitecture',False)
        root=walking_root(f,9);q=shot_cam(75,root.y,u,high=True)
        pose('broke',root,q,'warm',feet=STEPS[9].at(f)['feet'])
    elif cut==10 and f<1015:
        active('BATHROOM');visible('GoldenToiletA',True);q=camera((100.95,-3.6,2.15),(100,.45,1.05),(100,.54,1.70),False,41)
        seat=.605;front=.65-.57-.08
        ch=pose('broke',(100,.54,seat-.65*.88),q,'relief',ward='bath',seated=True,seat_z=seat,front_y=front)
        visible('AnkleTrousers',True);move('AnkleTrousers',(100,front-.025,.015))
        if f>=965:
            t=(f-965)/50;o=move('AmberShockwave',(100,.55,.62));o.hide_render=False;o.scale=(1+6*t,1+6*t,1+.2*t)
            glints(f,(100,.5,.75))
    elif cut==10:
        active('MANSION');visible('EntranceArchitecture',False)
        q=camera((75.1,.4,1.75),(75,2.7,3.25),(75,2.7,3.25),False,39)
        age=f-1015;O['ChandelierPivot'].rotation_euler.x=math.radians(18)*math.sin(age*.22)*math.exp(-age/130)
        for i in range(18):o=move('DustFX%02d'%i,(75+math.sin(i*2)*.65,2.4+math.cos(i)*.4,3.4-((age+i*4)%70)*.02));o.hide_render=False
    elif cut==11:
        active('MANSION');visible('EntranceArchitecture',False);q=shot_cam(75,2.65,u,close=True)
        root=V((75,2.65,0));hand=root+q@V((.075,-.265,.035))+V((0,0,1.92*.88))
        ch=pose('millionaire',root,q,'hearts',hands=[None,hand],mouth_style='dream')
        hearts(f,ch['head']+V((0,0,.12)),1085,16)
    elif cut==12:
        active('MANSION');visible('EntranceArchitecture',False);q=camera((75,-3.7,2.05),(75,2.65,1.2),(75,2.65,1.63),True,40)
        root=walking_root(f,12);feet=STEPS[12].at(f)['feet']
        ch=pose('broke',root,q,'warm',feet=feet,hands=[None,root+V((.38,-.02,1.42))])
        held('FoldedNewspaper',ch['hands'][0],q)
        butler=pose('butler',(75.78,2.55,0),q,'angry');steam(f,butler)
        rig_ns['swap'](O['butler_head'],'head_butler_flush')
        pose('millionaire',(75.02,2.95,0),q,'warm',hands=[None,(75.37,2.85,1.46)])
    elif cut==13:
        active('LIVING');q=camera((124.90,-4.4,3.85),(124.90,.65,.92),(124.85,.55,.98),True,36)
        axis=V((-1,0,.12));mid=V((124.78,.59,.83))
        breath=.003*math.sin(math.pi*(f-1293)/(1385-1293))
        a=pose('broke',(126.23,.13,.65+breath),q,'sleep',roll=90,spine=axis,feet=[(126.25,.08,.59),(126.18,.33,.62)],hands=[None,mid])
        b=pose('millionaire',(125.64,1.06,.84+breath),q,'sleep',roll=90,spine=axis,feet=[(125.73,.86,.68),(125.65,1.10,.68)],hands=[mid,None])
        # A near arm rests over the partner's chest; far arm remains behind the body.
        hearts(f,(124.65,.65,1.4),1293,8)
    elif cut==14:
        active('MANSION');visible('EntranceArchitecture',False);q=shot_cam(75,2.6,u,two=True)
        hero=pose('broke',(74.55,2.6,0),q,'warm',ward='blue',hands=[None,V((74.85,2.48,1.15))])
        pose('millionaire',(75.45,2.66,0),q,'warm',hands=[V((74.72,2.62,1.24)),None],turn=-.6)
        held('GoldenPlunger',hero['hands'][1],Quaternion(),(0,0,.40))
        for i in range(2):visible('LeatherSuitcase'+str(i),True) if 'LeatherSuitcase'+str(i) in GROUPS else None;move('LeatherSuitcase'+str(i),(74.10+i*.44,2.22,0))
    elif cut==15:
        active('PARIS');q=shot_cam(150,.45,u,two=True)
        middle=V((150,.36,1.02))
        pose('broke',(149.56,.45,0),q,'warm',ward='blue',hands=[None,middle],turn=1,talk=speech(f,1515,1541))
        pose('millionaire',(150.44,.45,0),q,'warm',hands=[middle,None],turn=-1,talk=speech(f,1542,1570))
        hearts(f,(150,.7,1.55),1476,12)
    elif cut==16:
        active('MANSION');visible('EntranceArchitecture',False)
        if f<1646:
            q=shot_cam(75,2.7,u,two=True);target=V((74.92,2.45,.99))
            rich=pose('millionaire',(75.42,2.75,-.30),q,'warm',kneel='one',hands=[target,None],turn=-1)
            hero=pose('broke',(74.5,2.7,0),q,'shock',ward='blue',hands=[(74.16,2.63,1.48),(74.84,2.63,1.48)],turn=.4)
            held('RingBox',rich['hands'][0],Quaternion(),(0,0,-.05))
        else:
            visible('RingBox',True);move('RingBox',(75,2.4,1.10),Quaternion());q=camera((75.02,1.83,1.44),(75,2.4,1.24),(75,2.4,1.24),False,56)
            glints(f,(75,2.39,1.35),3,.18)
        for o in FX:
            if o.name.startswith('ProposalRosePetal'):o.hide_render=False;o.location.x=75+math.sin(int(o.name[-2:])*2.4)*(0.3+int(o.name[-2:])%7*.21);o.location.y=2.7+math.cos(int(o.name[-2:])*2.4)*(.3+int(o.name[-2:])%7*.21)
    elif cut==17:
        active('WEDDING');q=camera((174.8,-4.1,2.45),(174.8,.95,1.4),(175,.85,1.65),True,31)
        middle=V((175,1.02,1.03));pose('broke',(174.55,1.0,0),q,'warm',ward='tux',hands=[None,middle],turn=.6)
        pose('millionaire',(175.45,1.0,0),q,'warm',ward='rich_tux',hands=[middle,None],turn=-.6)
        ch=pose('butler',(173.75,1.35,.49-.65*.83),q,'cry',seated=True,seat_z=.49,front_y=1.065,tears=True,hands=[(173.80,1.1,1.30),None])
        O['ButlerTissue'].hide_render=False;move('ButlerTissue',ch['hands'][0]+V((0,-.015,0)),q)
        for i in range(35):o=move('ConfettiFX%02d'%i,(175+math.sin(i*2.4)*1.5,.3+math.cos(i)*1.2,3.2-((f-1707+i*3)%100)*.025));o.hide_render=False
    elif cut==18 and f<1880:
        active('BATHROOM')
        for name in ['GoldenToiletA','GoldenToiletB','ChildPottyA','ChildPottyB']:visible(name,True)
        move('GoldenToiletA',(0,1.1,0));O['GoldenToiletA'].location.x=-.75
        ua=(f-1757)/(1880-1757)
        q=camera((100.15,-5.1,2.2),(100.15,.7,.8),(100.15,.7,.65),True,34);glints(f,(100,.7,1.1),8)
    else:
        active('LIVING');q=camera((125,-5.0,2.4),(125,.5,1.16),(125,.6,1.42),True,33)
        wave=0
        for start,end in [(1885,1930),(1960,2005),(2040,2090)]:
            if start<=f<=end:phase=(f-start)/(end-start);wave=.03*math.sin(phase*math.pi*3)*math.sin(phase*math.pi)
        laugh=2 if (f//12)%2 else 0
        a=pose('broke',(124.56,.35,.61-.65*.88),q,'warm',ward='tux',seated=True,seat_z=.61,front_y=-.19,hands=[(124.21+wave,.28,1.45),None],talk=laugh)
        pose('millionaire',(125.42,.35,.61-.65*.88),q,'warm',ward='rich_tux',seated=True,seat_z=.61,front_y=-.19,talk=2-laugh)
        pose('kid1',(123.80,.30,.61-.65*.528),q,'warm',seated=True,seat_z=.61,front_y=-.19,foot_z=.28,hands=[(123.53+wave*.5,.25,1.15),None],talk=laugh)
        pose('kid2',(126.20,.30,.61-.65*.528),q,'warm',seated=True,seat_z=.61,front_y=-.19,foot_z=.28,hands=[None,(126.47-wave*.5,.25,1.15)],talk=2-laugh)
        held('GoldenCrown',a['head']+V((0,0,.32)),Quaternion())
        for i in range(35):o=move('ConfettiFX%02d'%i,(125+math.sin(i*2.4)*1.8,.3+math.cos(i)*1.2,3.2-((f-1880+i*3)%110)*.025));o.hide_render=False
    if cut!=2:O['BellyWarning'].data.energy=0
    if not(cut==9 and 848<=f<=875):O['KissLips'].hide_render=True
    if cut!=17:O['ButlerTissue'].hide_render=True
    for i,name in enumerate(['GoldenToiletA','GoldenToiletB','ChildPottyA','ChildPottyB']):visible(name,cut==10 and f<1015 and i==0 or cut==18 and f<1880)
    visible('CuddleBlanket',cut==13)
    sync()
    if S.get('set_ink_enabled',True):INK.update()

for h in list(bpy.app.handlers.frame_change_pre):
    if getattr(h,'__name__','')=='update':bpy.app.handlers.frame_change_pre.remove(h)
bpy.app.handlers.frame_change_pre.append(update)
update(S)
