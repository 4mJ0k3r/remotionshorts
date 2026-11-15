"""Frame-addressable elevator staging, acting, optics and selective set ink.

Embedded in the blend alongside set_ink.py. Run this text after opening the
file if automatic Python execution is disabled, then scrub or render normally.
"""
import bpy
import json
import math
from mathutils import Vector, Quaternion
from bpy.app.handlers import persistent

V=Vector
CUTS=[(1,104,'1A'),(105,223,'1B'),(224,293,'1C'),(294,362,'1D'),(363,449,'2A'),(450,547,'2B'),(548,649,'3A'),(650,767,'3B'),(768,919,'4A'),(920,1031,'4B'),(1032,1139,'4C'),(1140,1277,'5A'),(1278,1409,'5B'),(1410,1519,'6A'),(1520,1598,'6B'),(1599,1778,'6C'),(1779,1946,'6D'),(1947,2145,'6E')]
INK_SYSTEM=None
BUSY=False
LEG_PLANS={}


def ease(a,b,f):
    t=max(0,min(1,(f-a)/max(1,b-a)))
    return t*t*(3-2*t)


def curve(obj,points):
    points=[V(point) for point in points]
    for index,(point,position) in enumerate(zip(obj.data.splines[0].bezier_points,points)):
        tangent=(points[min(index+1,len(points)-1)]-points[max(index-1,0)])*.24
        point.co=position
        point.handle_left_type=point.handle_right_type='FREE'
        point.handle_left=position-tangent
        point.handle_right=position+tangent


def show_family(root,visible):
    root.hide_render=not visible
    for child in root.children_recursive:
        child.hide_render=not visible


def employee_at(f):
    if f<768:
        return V((-.10,.12,0))
    if f<1410:
        return V((-.10,.12+1.26*ease(768,895,f),0))
    if f<1486:
        return V((-.10,1.38,0)).lerp(V((-1.03,-.62,0)),ease(1410,1450,f))
    if f<1599:
        return V((-1.03,-.62,0)).lerp(V((.05,.50,0)),ease(1486,1520,f))
    return V((.05,.50,0)).lerp(V((-.30,-.25,0)),ease(1599,1705,f))


def boss_at(f):
    home=V((.83,-.25,0))
    cctv=V((.95,.45,0))
    return home.lerp(cctv,ease(1486,1520,f)) if f<1599 else cctv.lerp(home,ease(1599,1705,f))


def commuter_at(index,f):
    home=V([(-1.08,1.03,0),(-.05,1.08,0),(.98,1.05,0)][index-1])
    cctv=V([(-1.20,1.40,0),(-.15,1.50,0),(.65,-.40,0)][index-1])
    return home.lerp(cctv,ease(1486,1520,f))


def prepare_leg_plans():
    exec(bpy.data.texts['leg_stepper.py'].as_string(),globals())
    employee_events=[(1,104,.25),(105,160,1),(294,362,.25),(768,895,1),(1140,1200,.35),(1410,1455,1),(1486,1520,1),(1599,1705,.65)]
    LEG_PLANS['employee']=FootStepper(employee_at,employee_events)
    LEG_PLANS['boss']=FootStepper(boss_at,[(1486,1520,.8),(1599,1705,1)],1.03,lambda frame:math.pi*ease(1599,1705,frame))
    for index in range(1,4):
        LEG_PLANS['commuter'+str(index)]=FootStepper(lambda frame,index=index:commuter_at(index,frame),[(1486,1520,.5)],.91)


def update_character_legs(char,frame,is_stepping,step_speed=.45,step_dir=(0,1)):
    name=char['name']
    scene=char['scene']
    size=char['size']
    hip=char['hip']
    base=char['base']
    forward=char['forward']
    seated=char['seated']
    if not seated:
        plan=LEG_PLANS[name]
        if plan.nominal_speed!=step_speed or plan.step_dir!=tuple(step_dir):
            LEG_PLANS[name]=FootStepper(plan.root_at,plan.windows,plan.size,plan.yaw_at,step_speed,step_dir,plan.frames)
    gait=LEG_PLANS[name].at(frame) if not seated else None
    yaw=math.pi*ease(1599,1705,frame) if name=='boss' else 0
    sideways=V((math.cos(yaw),math.sin(yaw),0))
    knee_forward=V((math.sin(yaw),-math.cos(yaw),0))
    for index,sign in enumerate([-1,1]):
        if gait:
            foot=V(gait['feet'][index] if is_stepping else LEG_PLANS[name].neutral(frame,index))
        else:
            foot=base+V((sign*.13*size,-.09,.24*size))
        lift=gait['lift'][index] if gait and is_stepping else 0
        ankle=foot+V((0,0,.065*size)) if not seated else foot
        anchor=hip+sideways*(sign*.105*size)
        pole=knee_forward*(.10+.12*(lift/.11))+sideways*(sign*.025)
        if seated:
            length=.20*size
        else:
            resting_ankle=V(LEG_PLANS[name].neutral(frame,index))+V((0,0,.065*size))
            resting_anchor=anchor-V((0,0,gait['bob']))
            resting_distance=(resting_anchor-resting_ankle).length
            length=math.sqrt((resting_distance*.5)**2+(.055*size)**2)
        knee=V(knee_of(tuple(anchor),tuple(ankle),tuple(pole),length,length))
        curve(scene.objects[f'{name}_leg_{index}'],[anchor,knee,ankle])
        core=scene.objects.get(f'{name}_trouser_{index}')
        if core:
            offset=forward*.018
            curve(core,[anchor+offset,knee+offset,ankle+offset])
        shoe=scene.objects[f'{name}_shoe_{index}']
        shoe.location=foot
        shoe.rotation_euler.z=gait['yaw'][index] if gait else 0
        shoe.rotation_euler.x=0
        contact=scene.objects[f'{name}_contact_{index}']
        contact.location=(foot.x,foot.y,.003)
        contact.hide_render=seated or lift>.025


def first_payload_at(f):
    u=ease(965,1095,f)
    result=V((-.24,1.05,.036)).lerp(V((.54,-.44,.036)),u)
    if f<965:
        result.y=1.29-.24*ease(935,950,f)
        result.z=.04+.10*(1-ease(935,950,f))
    else:
        result.z=.04+.034*abs(math.sin(u*math.tau*2))
    return result


def second_payload_at(f):
    cuff=max(LEG_PLANS['boss'].at(1840)['feet'],key=lambda point:point[0])
    clearance=ease(1840,1855,f)*(1-ease(1865,1880,f))
    return V((cuff[0]+.18*clearance,cuff[1]-.22*ease(1865,1880,f),.04+.10*(1-ease(1840,1855,f))))


def camera_pose(cut,f):
    a,b,_=CUTS[cut]
    t=ease(a,b,f)
    employee=V((-.10,.12,1.64))
    boss=V((.83,-.25,1.67))
    baby=V((-.91,-.57,.98))
    if cut==0:
        return V((-.16,-1.18+.10*t,1.80)),employee,49,employee
    if cut==1:
        if f<=160:
            return V((-.13,-1.65+.10*ease(105,160,f),1.35)),V((-.10,.12,1.12)),43,employee
        # Door-peek coverage. Jamb and a partly closed leaf occlude the edge.
        return V((-.56,-4.45+.28*ease(161,223,f),1.91)),V((-.05,.2,1.25)),40,V((0,.1,1.40))
    if cut==2:
        z=1.43+.72*t
        return V((.70,-1.02,z)),V((1.70,-.54,z-.06)),57,V((1.70,-.54,z-.06))
    if cut==3:
        return V((-1.14+.13*t,-.78,1.82)),employee,52,employee
    if cut==4:
        return V((-.12,-1.31,.66+.10*t)),V((-.10,.12,1.91)),37,employee
    if cut==5:
        if f<496:
            return V((-.27,1.25-.10*t,.67)),V((-.10,.10,.95)),41,V((-.10,.10,1.0))
        return V((.10,-2.12+.15*t,1.80)),V((0,1.0,1.52)),42,V((0,1.0,1.62))
    if cut==6:
        if f<596:
            return V((-.24,-1.13+.08*t,1.95)),employee,48,employee
        return V((-.94,-1.87+.08*t,1.10)),baby,50,baby
    if cut==7:
        return V((-.94,-1.85+.10*t,1.10)),baby,49,baby
    if cut==8:
        center=employee_at(f)
        position=center+V((.20+.12*t,-1.90+.15*t,1.29))
        return position,center+V((0,0,1.02)),40,center+V((0,0,1.64))
    if cut==9:
        return V((-.40,.17+.10*t,.23)),V((-.24,1.05,.18)),52,V((-.24,1.05,.08))
    if cut==10:
        point=first_payload_at(f)
        return point+V((-.13,-.78+.07*t,.14)),point,58,point
    if cut==11:
        center=employee_at(f)
        return center+V((.02,-2.07+.12*t,1.72)),center+V((0,0,1.47)),44,center+V((0,0,1.64))
    if cut==12:
        return V((.72,-1.54+.10*t,.87)),V((.83,-.25,1.58)),44,boss
    if cut==13:
        focus=V((-1.59,-.72,1.20))
        return V((-.82,-1.42+.08*t,1.39)),focus,55,focus
    if cut==14:
        position=V((-1.10,-1.45+.025*t,2.55))
        target=V((.05,.45,1.15))
        return position,target,20,V((0,.45,1.20))
    if cut==15:
        center=boss_at(f)
        wide=center+V((.15,-2.30,1.40))
        close=V((1.19,-1.62+.11*t,1.67))
        weight=ease(1705,1735,f)
        target=(center+V((0,0,1.02))).lerp(V((.83,-.25,1.56-.19*ease(1696,1778,f))),weight)
        return wide.lerp(close,weight),target,42+4*weight,center+V((0,0,1.64))
    if cut==16:
        cuff=max(LEG_PLANS['boss'].at(1840)['feet'],key=lambda point:point[0])
        if f<1876:
            return V((cuff[0]+.21,cuff[1]+.89-.08*t,.23)),V((cuff[0]-.024,cuff[1]+.06,.25)),51,V((cuff[0]-.024,cuff[1]+.06,.18))
        point=second_payload_at(f)
        return point+V((.06,-.49+.06*t,.14)),point,54,point
    return V((.26,-3.0+.12*t,1.75)),V((.26,-.25,1.12)),43,V((.26,-.25,1.58))


def actor(scene,who,position,size,style,amount,cut,f,seat=False):
    gait=LEG_PLANS[who].at(f) if not seat else None
    position=V(position)+V((0,0,gait['bob'] if gait else 0))
    root=scene.objects[who+'_root']
    root.location=position
    head_q=scene.camera.matrix_world.to_quaternion()
    direction=head_q@V((0,0,-1))
    heading=math.atan2(-direction.x,direction.y)
    pitch=math.atan2(-direction.z,math.hypot(direction.x,direction.y))
    q=Quaternion((0,0,1),heading)@Quaternion((1,0,0),math.pi/2-pitch*.5)
    body=scene.objects[who+'_body']
    head=scene.objects[who+'_head']
    body.location=(0,0,(.58 if seat else 1.02)*size)
    body.rotation_mode='QUATERNION'
    body.rotation_quaternion=q
    body.scale=(1.18 if who=='employee' and 105<=f<=160 else 1,1,1)
    head.location=(0,0,(.98 if seat else 1.64)*size)
    head_forward=head_q@V((0,0,1))
    head.location+=head_forward*(.075*size)
    normal=q@V((0,0,1))
    separation=(head.location-body.location).dot(normal)
    angle=head_q.rotation_difference(q).angle
    clearance=.365*size*abs(math.sin(angle))+.02
    if separation<clearance:
        head.location+=head_forward*((clearance-separation)/max(.1,head_forward.dot(normal)))
    head.rotation_mode='QUATERNION'
    head.rotation_quaternion=head_q
    turn=0
    if who.startswith('commuter') and 496<=f<=547:
        turn=(1 if who!='commuter2' else -1)*ease(496,519,f)*.75
    if who=='employee' and cut==6:
        turn=-.7
    if who=='boss' and cut==15:
        turn=.9*(1-ease(1696,1730,f))
    scene.objects[who+'_face_group'].location=(turn*.365*.22*size,0,.007)
    rear=(who=='employee' and cut==8 and f>=820) or (who=='boss' and 1650<=f<1696)
    back_body=scene.objects[who+'_body_rear']
    back_body.location=body.location
    back_body.rotation_mode='QUATERNION'
    back_body.rotation_quaternion=q
    back_body.scale=body.scale
    body.hide_render=rear
    back_body.hide_render=not rear
    scene.objects[who+'_head_art'].hide_render=rear
    scene.objects[who+'_back_art'].hide_render=not rear
    blink=(f+(21 if who=='boss' else 37 if who=='baby' else 0))%137 in [71,72,73]
    actual_style='blink' if blink else style
    for obj in scene.objects[who+'_face_group'].children:
        obj.hide_render=rear or (who=='baby' and f>=670) or obj.get('expression')!=actual_style or obj.get('mouth')!=amount
    if who=='baby':
        scene.objects['baby_masked_head_art'].hide_render=f<670
        scene.objects[who+'_head_art'].hide_render=f>=670 or rear
    base=V(position)
    side=q@V((1,0,0))
    up=q@V((0,1,0))
    forward=q@V((0,0,1))
    center=base+body.location
    shoulders=[center+side*(sign*.203*size)+up*(.20*size)+forward*.008 for sign in [-1,1]]
    hands=[base+side*(sign*.29*size)+V((0,-.04,(.82 if seat else .88)*size)) for sign in [-1,1]]
    elbows=[shoulders[index]+side*(sign*.19*size)-up*.24*size for index,sign in enumerate([-1,1])]
    if gait and gait['active']:
        swing=V(gait['direction'])*(.35*gait['arm_swing'])
        for index,sign in enumerate([-1,1]):
            hands[index]+=swing*sign
            elbows[index]+=swing*(sign*.5)
    if who=='employee':
        if cut==4:
            for index in range(2):
                scene.objects[f'Whistle music note {index}'].hide_render=False
        else:
            for index in range(2):
                scene.objects[f'Whistle music note {index}'].hide_render=True
        if cut==8:
            hands=[base+V((sign*.07,-.06,.68)) for sign in [-1,1]]
            elbows=[base+V((sign*.25,-.09,.88)) for sign in [-1,1]]
        if cut==11 or cut==17:
            weight=ease(1140,1154,f) if cut==11 else ease(1947,1961,f)
            reach=.48 if cut==17 else .65
            elbow_span=.51 if cut==17 else .64
            for index,sign in enumerate([-1,1]):
                target=base+side*(sign*reach)+V((0,0,1.49))+forward*.04
                hands[index]=hands[index].lerp(target,weight)
                elbows[index]=base+side*(sign*elbow_span)+V((0,0,1.08))
        if cut==13:
            button=scene.objects['Emergency mushroom']
            target=button.location+V((.081,0,0))
            weight=ease(1428,1450,f)*(1-ease(1464,1486,f))
            hands[0]=hands[0].lerp(target,weight)
            elbows[0]=base+V((-.38,-.18,1.06))
    if who=='boss' and cut==17:
        hands[1]=base+head.location+head_q@V((.16,.02,.04))
        elbows[1]=base+side*.44+V((0,0,1.18))
    if who=='baby' and cut==7:
        weight=ease(650,675,f)*(1-ease(701,724,f))
        for index,sign in enumerate([-1,1]):
            target=base+head.location+head_q@V((sign*.245*size,-.02*size,.08))
            hands[index]=hands[index].lerp(target,weight)
            elbows[index]=base+side*(sign*.37*size)+V((0,0,.71*size))
    for index in range(2):
        curve(scene.objects[f'{who}_arm_{index}'],[shoulders[index],elbows[index],hands[index]])
        scene.objects[f'{who}_hand_{index}'].location=hands[index]
    hip=base+V((0,0,(.43 if seat else .70)*size))
    pelvis=scene.objects[who+'_pelvis']
    pelvis.location=hip.copy()
    pelvis.scale=(.16*size,.075*size,.095*size)
    if who=='boss':
        pelvis.location.y+=.04
        extent=math.sqrt(sum((pelvis.scale[index]*forward[index])**2 for index in range(3)))
        overlap=(pelvis.location-center).dot(forward)+extent+.008
        if overlap>0:
            pelvis.location-=forward*overlap
    leg_hip=pelvis.location.copy() if who=='boss' else hip
    update_character_legs({'name':who,'scene':scene,'size':size,'hip':leg_hip,'base':base,'forward':forward,'seated':seat},f,gait['active'] if gait else False)
    for index in range(6 if who=='employee' else 0):
        drop=scene.objects[f'{who}_sweat_{index}']
        active=cut in [0,1,3,6,8,11,17]
        drop.hide_render=not active
        # Droplets remain attached to a temple socket until they fade out.
        age=((f+index*17)%47)/47
        drop.location=base+head.location+head_q@V((((-1)**index)*(.245+.035*age),.20-.18*age,.016))
        drop.rotation_mode='QUATERNION'
        drop.rotation_quaternion=head_q
        fade=1 if age<.82 else (1-age)/.18
        drop.scale=(.012*fade,.026*fade,.008*fade)


def update(scene):
    global INK_SYSTEM,BUSY
    if BUSY or not scene.get('elevator_leak'):
        return
    BUSY=True
    try:
        f=scene.frame_current
        cut=next((index for index,(a,b,_) in enumerate(CUTS) if a<=f<=b),17)
        position,target,lens,focus=camera_pose(cut,f)
        camera=scene.camera
        camera.location=position
        camera.rotation_mode='QUATERNION'
        camera.rotation_quaternion=(target-position).to_track_quat('-Z','Y')
        camera.data.lens=lens
        camera.data.dof.focus_distance=(focus-position).dot(camera.rotation_quaternion@V((0,0,-1)))
        camera.data.dof.aperture_fstop=3.2 if cut in [1,14,17] else 2.8
        bpy.context.view_layer.update()
        # Camera-visible cutaway surfaces are explicitly controlled.
        for obj in scene.objects:
            if obj.get('ceiling'):
                obj.hide_render=False
            if obj.get('front_door'):
                obj.hide_render=not (cut==1 and f>=161 or cut==8 and f>=843)
            if obj.name.startswith(('Back brushed panel','Tubular back handrail','Back rail support')):
                obj.hide_render=cut==8 and position.y>1.68
            if obj.get('stroller'):
                obj.hide_render=cut==17
        scene.objects['Left sliding door'].location.x=-1.65 if cut==1 else -.64
        scene.objects['Right sliding door'].location.x=1.65 if cut==1 else .64
        depression=ease(1445,1450,f)*(1-ease(1464,1475,f))
        scene.objects['Emergency mushroom'].location.x=-1.59-.032*depression
        alarm_active=ease(1449,1456,f)
        phase=max(0,f-1450)%30/15
        pulse=phase if phase<=1 else 2-phase
        scene.objects['Alarm wash'].data.energy=alarm_active*(45+75*pulse)
        scene.objects['Overhead soft ceiling'].data.energy=160-64*alarm_active
        scene.objects['Front diffused fill'].data.energy=75-25*alarm_active
        scene.objects['Warm golden directional key'].data.energy=280-70*alarm_active
        scene.objects['Cool rear rim'].data.energy=95-20*alarm_active
        env=json.loads(scene['audio_envelope'])
        amount=env[min(len(env)-1,max(0,f-1))]
        for obj in scene.objects:
            if obj.get('cast_owner'):
                obj.hide_render=False
        employee_position=employee_at(f)
        actor(scene,'employee',employee_position,1,'horror' if cut==17 else 'laugh' if cut==11 else 'whistle_up' if cut==4 else 'angry' if cut==6 else 'panic',amount if cut==11 else 0,cut,f)
        actor(scene,'boss',boss_at(f),1.03,'horror' if cut==17 else 'angry',amount if cut==12 else 0,cut,f)
        stroller_offset=V((.26,.82,0))*ease(1486,1520,f)
        scene.objects['Stroller assembly root'].location=stroller_offset
        actor(scene,'baby',V((-.91,-.57,.16))+stroller_offset,.78,'angry' if cut in [6,7] else 'baby',0,cut,f,seat=True)
        for index in range(1,4):
            actor(scene,'commuter'+str(index),commuter_at(index,f),.91,'angry' if f>=496 else 'baby',0,cut,f)
        mask=scene.objects['Baby gas mask assembly']
        show_family(mask,f>=670)
        mask.scale=(1.18,)*3
        mask.location=(0,.05,.045)
        if 650<=f<670:
            show_family(mask,True)
            mask.location.y=-.35+.40*ease(650,670,f)
        first=scene.objects['Prop_Turd_1']
        second=scene.objects['Prop_Turd_2']
        show_family(first,f>=935)
        show_family(second,f>=1840)
        u=ease(965,1095,f)
        first.location=first_payload_at(f)
        first.rotation_euler=(0,math.pi/2*(1-ease(935,965,f))+u*math.tau*2,-.4+u*.8)
        second.location=second_payload_at(f)
        second.rotation_euler.y=math.pi/2*(1-ease(1840,1860,f))+.30*ease(1840,1875,f)
        for index,payload in [(1,first),(2,second)]:
            wisp=scene.objects[f'Payload heat wisp {index}']
            wisp.hide_render=payload.hide_render
            wisp.rotation_mode='QUATERNION'
            wisp.rotation_quaternion=camera.rotation_quaternion
            wisp.location=payload.location+V((0,0,.13+.025*math.sin(f*.09)))
            shadow=scene.objects[f'Payload floor contact {index}']
            shadow.hide_render=payload.hide_render or payload.location.z>.08
            shadow.location=(payload.location.x,payload.location.y,.002)
        gas=scene.objects['Green smell ribbon']
        gas.hide_render=not (450<=f<=547)
        gas.location=(-.10,.25,.68)
        gas.rotation_mode='QUATERNION'
        gas.rotation_quaternion=camera.rotation_quaternion
        gas.scale=(.9+ease(450,495,f),1.1+ease(450,495,f),1)
        for index in range(18):
            scene.node_tree.nodes[f'HUD_GATE_{index}'].inputs[0].default_value=1 if index==cut else 0
        featured={0:['employee'],2:[],3:['employee'],4:['employee'],6:['employee'] if f<596 else ['baby'],7:['baby'],8:['employee'],9:['employee','baby'],10:['boss'],11:['employee'],12:['boss'],13:['employee'],15:['boss'],16:['boss'],17:['employee','boss']}.get(cut)
        if cut==5 and f>=496:
            featured=['commuter1','commuter2','commuter3']
        if featured is not None:
            for obj in scene.objects:
                if obj.get('cast_owner') and obj['cast_owner'] not in featured:
                    obj.hide_render=True
        bpy.context.view_layer.update()
        if INK_SYSTEM is None:
            exec(bpy.data.texts['studio_set_ink.py'].as_string(),globals())
            INK_SYSTEM=SetInk(scene)
        INK_SYSTEM.output.hide_render=not scene.get('set_ink_enabled',True)
        if scene.get('set_ink_enabled',True):
            INK_SYSTEM.update()
    finally:
        BUSY=False


@persistent
def elevator_frame(scene,*args):
    update(scene)


def register():
    prepare_leg_plans()
    for callback in list(bpy.app.handlers.frame_change_pre):
        if callback.__name__=='elevator_frame':
            bpy.app.handlers.frame_change_pre.remove(callback)
    bpy.app.handlers.frame_change_pre.append(elevator_frame)
    update(bpy.context.scene)


register()
