"""Narration aligned, deterministic shot poses and named surface contacts."""
import bpy
import json
import math
from mathutils import Vector as V, Quaternion
import ricks_lookdev as look
from geometry import bezier_points, set_line

S=bpy.context.scene
O=bpy.data.objects
T=json.loads(bpy.data.texts['timing.json'].as_string())
STAGES=[O['Pawn shop set'],O['Bedroom set']]
SETS=[[root,*root.children_recursive] for root in STAGES]
ACTORS=['Pawn Gamer','Gamer','Papa']
PARTS={name:{part:O[name+' '+part] for part in (
    'torso rig','head pivot','wide mouth','speaking mouth','closed mouth','upper teeth',
    *[f'{part} {side}' for side in (-1,1) for part in ('eye white','pupil','eye catch','blink','eyebrow','arm','leg','hand','sole','grounded contact')],
    *[f'sweat {i}' for i in range(4)])} for name in ACTORS}
CONTACTS={}
_STAGE=None
_LAST=None

def ease(t,a,b):
    return look.ease5((t-a)/(b-a))

def pulse(t,a,b,c,d):
    return ease(t,a,b)*(1-ease(t,c,d))

def visible(obj,show):
    parent=obj.parent
    while show and parent:
        show=not parent.hide_render
        parent=parent.parent
    hidden=not show
    if obj.hide_render is not hidden:
        obj.hide_render=obj.hide_viewport=hidden
        for child in obj.children_recursive:
            child.hide_render=child.hide_viewport=hidden

def world_local(obj,point=(0,0,0)):
    result=V(point)
    while obj:
        rot=obj.rotation_quaternion if obj.rotation_mode=='QUATERNION' else obj.rotation_euler.to_quaternion()
        result=obj.location+rot@V(tuple(result[i]*obj.scale[i] for i in range(3)))
        obj=obj.parent
    return result

def stage_point(stage,point):
    return STAGES[stage].location+V(point)

def aiming(cam,point,target,focal,fstop=3.45):
    cam.location=point
    cam.rotation_mode='QUATERNION'
    cam.rotation_quaternion=(target-point).to_track_quat('-Z','Y')
    cam.data.lens=focal
    cam.data.dof.use_dof=True
    cam.data.dof.aperture_fstop=fstop
    O['Optical focus'].location=target
    cam.data.dof.focus_distance=(target-point).length

def shot_camera(name,u,t,stage):
    e=look.ease5(u)
    moves={
        'wait':((-1.64,-1.77,2.05),(-1.43,-1.62,2.04),(-.73,1.41,1.89),45,4.0),
        'launch_year':((-.05,-1.77,2.08),(-.23,-1.57,2.10),(-.73,1.97,2.08),57,3.58),
        'pawn':((-1.76,-2.82,1.89),(-1.51,-2.65,1.83),(-.18,.52,1.31),38,4.4),
        'pawn_cooler':((-1.27,-2.10,1.54),(-1.11,-1.88,1.50),(-.48,.64,1.18),42,3.0),
        'pawn_phone':((1.06,-1.59,1.78),(.84,-1.41,1.72),(-.08,.59,1.095),42,3.3),
        'pawn_bangles':((.32,-1.47,1.87),(.21,-1.28,1.81),(.22,.56,1.05),45,3.0),
        'pc_reveal':((1.64,-.67,1.16),(1.48,-.60,1.25),(.46,1.01,1.32),52,2.8),
        'midnight':((-1.74,-.61,1.33),(-1.64,-.53,1.30),(-1.61,.50,1.061),54,3.1),
        'latch':((2.55,.86,1.61),(2.44,.83,1.60),(.99,1.77,1.22),54,3.15),
        'chips':((1.24,.22,1.52),(1.14,.17,1.53),(-.65,-.22,1.26),43,4.6),
        'start':((.61,-1.03,1.98),(.43,-.92,1.92),(-.66,.12,1.27),40,3.5),
        'neon_display':((-1.19,-1.21,1.64),(-1.03,-1.00,1.64),(-.66,.91,1.42),50,3.7),
        'awe':((1.12,.23,1.78),(.94,.16,1.77),(-.67,-.31,1.48),56,3.3),
        'beach':((-1.89,-2.06,2.12),(-1.73,-1.94,2.09),(-.62,.88,1.49),44,4.5),
        'entry':((.40,-2.59,1.66),(.87,-2.27,1.63),(1.35,1.74,1.28),47,4.7),
        'beach_freeze':((-1.25,-1.12,1.70),(-1.03,-1.06,1.66),(-.66,.90,1.43),52,3.75),
        'keys':((.64,-1.08,1.94),(.51,-.97,1.91),(-.66,.15,1.25),38,3.4),
        'panic':((1.04,.18,1.80),(.92,.11,1.76),(-.67,-.27,1.46),58,3.5),
        'shoe':((2.22,-.75,.68),(2.01,-.67,.77),(1.35,1.12,.51),43,4.7),
        'boss':((2.93,-1.92,1.54),(2.72,-1.65,1.59),(1.18,1.11,1.52),43,4.9),
        'cower':((-1.91,-2.68,1.28),(-1.80,-2.55,1.24),(-1.00,-.79,.70),35,3.6),
    }
    if name in ('orbit','freeze'):
        q=ease(min(t,58.48),53.34,58.48)
        theta=math.pi*q
        at=(1.26+2.19*math.cos(theta),1.17-2.72*math.sin(theta),1.82+.13*math.sin(theta)+.70*q)
        to=(1.18,1.11+.29*ease(q,.61,.92)+.095*pulse(t,56.05,56.90,57.82,58.42),1.54)
        if name=='freeze':
            # Same spatial endpoint, punch in to the freeze graphic on the cut.
            aiming(S.camera,stage_point(stage,at),stage_point(stage,to),31,14)
        else:
            aiming(S.camera,stage_point(stage,at),stage_point(stage,to),31,5.3)
        return
    p0,p1,target,lens,stop=moves['beach_freeze' if name=='freeze_popup' else name]
    point=V(p0).lerp(V(p1),e)
    if name=='midnight' and t>14.18:
        q=ease(t,14.18,446/30)
        point=point.lerp(V(moves['latch'][0]),q)
        point.y-=1.29*math.sin(math.pi*q)
        point.z+=.48*math.sin(math.pi*q)
        target=V(target).lerp(V(moves['latch'][2]),q)
        stop=stop+(3.15-stop)*q
    if name=='entry':
        burst=max(0,t-34.53)
        if 0<burst<.17:point.z+=.028*math.sin(burst*112)*(1-burst/.17)
    if name=='shoe':
        target=V(target).lerp(V((1.12,1.05,1.18)),ease(t,44.69,46.16))
        lens=38
    if name not in ('latch','midnight'):
        stop=min(stop,3.65)
    aiming(S.camera,stage_point(stage,point),stage_point(stage,target),lens,stop)

def body_pose(actor,position,yaw,dz=0.0,roll=0.0):
    root=O[actor]
    root.location=position
    root.rotation_euler=(0,0,yaw)
    body=PARTS[actor]['torso rig']
    body.location=(0,0,dz)
    body.rotation_euler.y=roll
    return root

def arm(actor,side,target,elbow_height=None,elbow_back=0.0):
    parts=PARTS[actor]
    root=O[actor]
    body=parts['torso rig']
    r=root.rotation_euler.to_matrix()
    local=r.inverted()@(target-root.parent.location-root.location)
    shoulder=body.matrix_basis@V((side*.222,-.007,1.083))
    elbow=V((shoulder.x+side*.145,shoulder.y-.10,max(.40,(shoulder.z+local.z)*.53-.07)))
    if elbow_height is not None:elbow.z=elbow_height
    elbow.y+=elbow_back
    wrist=local.lerp(elbow,.23)
    span=bezier_points(shoulder,elbow,wrist,local)
    set_line(parts[f'arm {side}'],span)
    sleeve=O[f'{actor} sleeve {side}']
    cloth=bezier_points(shoulder,elbow,wrist,local,n=26)
    set_line(sleeve,cloth[:20])
    set_line(O[f'{actor} cuff {side}'],cloth[17:21])
    hand=parts[f'hand {side}']
    hand.scale.x=1 if side<0 else -1
    hand.location=local
    hand.rotation_mode='QUATERNION'
    hand.rotation_quaternion=r.to_quaternion().inverted()@(S.camera.location-target).to_track_quat('-Y','Z')

def foot(actor,side,stage_foot,lift=0.0,seated=False):
    root=O[actor]
    parts=PARTS[actor]
    body=parts['torso rig']
    local=root.rotation_euler.to_matrix().inverted()@(V(stage_foot)-root.location)
    top=body.matrix_basis@V((side*.115,0,.68))
    tip=local+V((0,0,.072+lift))
    knee=V((side*(.20 if seated else .15),-.27 if seated else -.08,max(tip.z+.10,(top.z+tip.z)*.50)))
    set_line(parts[f'leg {side}'],bezier_points(top,knee,knee.lerp(tip,.36),tip))
    parts[f'sole {side}'].location=local+V((0,0,.058+lift))
    parts[f'grounded contact {side}'].location=local+V((0,0,.004))
    visible(parts[f'grounded contact {side}'],lift<.024)

def face(actor,mood,t,direction=None,roll=0):
    parts=PARTS[actor]
    root=O[actor]
    head=parts['head pivot']
    head.rotation_mode='XYZ'
    head.rotation_euler=(0,0,0)
    at=world_local(head)
    view=(S.camera.location-at) if direction is None else V(direction)
    facing=view.to_track_quat('-Y','Z')
    body=parts['torso rig']
    head.rotation_mode='QUATERNION'
    head.rotation_quaternion=(root.rotation_euler.to_quaternion()@body.rotation_euler.to_quaternion()).inverted()@facing@Quaternion((0,1,0),roll)
    blink=any(a<=t<a+.10 for a in (.61,3.83,6.92,16.51,24.13,28.04,37.72,47.31,48.88,52.50))
    if mood=='tired':blink=.60<=t<.69
    if mood in ('awe','panic','fear'):blink=any(a<=t<a+.075 for a in (24.20,25.04,43.33,52.03))
    fear=mood in ('panic','fear')
    broad=fear or mood=='awe'
    voice=.5+.5*math.sin(t*37+.7*math.sin(t*10))
    talking=mood=='stern talk' and voice>.24
    for side in (-1,1):
        for part in ('eye white','pupil','eye catch'):
            obj=parts[f'{part} {side}']
            visible(obj,not blink and (part!='eye white' or broad))
            if part=='pupil':
                obj.scale.z=(1.14 if broad else .72 if mood=='tired' else .91)
                obj.scale.x=.92 if fear else 1.04
            if part=='eye white':
                obj.scale.z=1.22 if mood=='panic' else 1.06
        visible(parts[f'blink {side}'],blink)
        parts[f'eyebrow {side}'].rotation_euler.y=side*(.35 if mood.startswith('stern') else .22 if fear else -.07)
        if actor!='Papa':
            visible(O[f'{actor} eye neon {side}'],mood=='awe' and not blink)
            visible(O[f'{actor} tired bag {side}'],mood=='tired')
            visible(O[f'{actor} tired lid {side}'],mood=='tired' and not blink)
    visible(parts['wide mouth'],broad)
    visible(parts['speaking mouth'],talking)
    visible(parts['closed mouth'],not broad and not talking and mood!='tired')
    if actor!='Papa':visible(O[actor+' tired mouth'],mood=='tired')
    visible(parts['upper teeth'],fear or talking and actor!='Papa' and voice>.65)
    parts['wide mouth'].scale.z=(.92+.15*math.sin(t*21)) if fear else .88+.19*ease(t,22.8,23.4)
    parts['speaking mouth'].scale.z=.75+.29*voice
    for j in range(4):
        drop=parts[f'sweat {j}']
        local=(((t-40.37)+j*.146)%.69)/.69
        side=-1 if j%2==0 else 1
        drop.location=(side*(.247+.091*ease(local,.42,1)),-.069,.14-.20*local)
        drop.scale=(.82+.35*local,1,.77+.43*local)
        visible(drop,fear)

def set_context(stage):
    global _STAGE
    if _STAGE!=stage:
        for i,group in enumerate(SETS):
            for o in group:o.hide_render=o.hide_viewport=i!=stage
        _STAGE=stage

def boss_pose_time(t):
    return min(t,58.435) if t>=58.48 else t

def update(frame,force=False):
    global _LAST,CONTACTS
    if _LAST==frame and not force:return
    _LAST=frame
    idx=max(0,min(T['frames']-1,frame-1))
    t=idx/30
    shot=next(s for s in T['shots'] if s['a']<=idx<s['b'])
    name=shot['id']
    u=(idx-shot['a'])/max(1,shot['b']-shot['a']-1)
    stage=0 if t<10.70 else 1
    set_context(stage)
    CONTACTS={}
    shot_camera(name,u,t,stage)
    S['stage']=stage
    S['shot']=name
    speed=14.30<t<14.76 or 34.52<t<34.69
    visible(O['Whip pan action lines'],speed)
    if speed:
        S.camera.data.dof.use_dof=False
    glint=pulse(t,20.52,22.5,25.7,26.10)
    bpy.data.materials['Warm cream face'].node_tree.nodes['Monitor face reflection'].inputs[0].default_value=.64*glint
    visible(O['Last frame original warning'],name=='freeze')
    show_stars=name in ('orbit','freeze') and t>=56.40
    visible(O['Wanted star cluster'],show_stars)
    if show_stars:
        S.camera.data.dof.use_dof=False
    S.node_tree.nodes['Payoff grade'].inputs['Saturation'].default_value=.23 if name=='freeze' else 1
    if stage==0:
        age=round(2013+13*ease(t,.32,3.17))
        for yr in range(2013,2027):
            visible(O[f'Calendar year {yr}'],yr==age)
        for i in range(6):
            o=O[f'Calendar flying paper {i}'];life=((t+i*.13)%.66)/.66
            visible(o,name in ('wait','launch_year') and .36<t<3.56)
            o.location=(-.73+(i-2.5)*.086+(.42+i*.021)*life,1.86-.65*life,2.17+.29*math.sin(life*math.pi)-.54*life)
            o.rotation_euler=(life*2.1,i*.33+life*3.4,life*.61)
        bx= -.24 if name in ('pawn_phone','pawn_bangles') else -.57 if name!='wait' else -.72
        by=1.12 if name not in ('wait','launch_year') else 1.34
        visible(O['Pawn Gamer'],name!='pc_reveal' or t<12.9)
        visible(O['Pawn waiting display'],name in ('wait','launch_year'))
        body_pose('Pawn Gamer',(bx,by,0),0,-.072 if name=='wait' else 0,-.09 if name=='wait' else 0)
        face('Pawn Gamer','tired' if name in ('wait','launch_year') and t<4.04 else 'awe' if name=='launch_year' else 'smirk',t,roll=-.09 if t<2.6 else 0)
        for side in (-1,1):
            foot('Pawn Gamer',side,(bx+side*.145,by-.044,.0))
            arm('Pawn Gamer',side,stage_point(stage,(bx+side*.35,by-.24,1.00)))
        for prop,at,z in [('Kidney cooler',7.36,.869),('Old cracked phone',8.43,.883),('Mothers bangles',9.71,.869)]:
            o=O[prop]
            visible(o,t>=at-.54)
            lift=(1-ease(t,at-.43,at))*.29
            o.location.z=z+lift
            if at-.42<=t<=at+.06:
                points={'Kidney cooler':world_local(O['Cooler handle anchor']),
                        'Old cracked phone':world_local(o,(.057,-.014,.042)),
                        'Mothers bangles':world_local(o,(.081,-.008,.061))}
                p=points[prop]
                arm('Pawn Gamer',1,p,1.012)
                CONTACTS[('Pawn Gamer',1)]=p
        visible(O['Pawn receipt'],t>=10.36)
        return

    tt=boss_pose_time(t)
    finale=name in ('orbit','freeze')
    for prop in ('Walnut desk','Curved widescreen monitor','Wide stitched keyboard mat','RGB keyboard',
                 'RGB mouse grip','Bedroom RGB tower','Desk digital clock','Gaming chair'):
        visible(O[prop],not finale)
    hinge=O['Room door hinge']
    hinge.rotation_euler.z=-.60*(1-ease(t,15.07,16.10))-.10*ease(t,33.92,34.51)-1.34*ease(t,34.53,34.86)+.057*pulse(t,34.85,34.97,35.02,35.27)
    O['Sliding latch bolt'].location.x=-1.08-.082*ease(t,16.11,16.58)
    visible(O['Chips packet'],name not in ('midnight','orbit','freeze'))
    visible(O['Clock before midnight'],t<14.13)
    visible(O['Clock at midnight'],t>=14.13)
    visible(O['Loading display'],t<21.53)
    visible(O['Original beach display'],t>=21.53)
    visible(O['Freeze warning popup'],t>=41.96)
    p=O['Original beach walker']
    ptime=min(t,41.95)
    walk=math.sin((ptime-20.1)*10.5)
    p.location=(.06-.34*ease(ptime,27.3,31.70),-.045,-.278+.012*abs(walk))
    p.rotation_euler.z=.26+.17*walk
    for side in (-1,1):
        off=side*walk
        set_line(O[f'Beach walker arm {side}'],[(side*.036,0,.246),(side*.056,-.012+.019*off,.194),
                 (side*.048,-.016+.041*off,.157)])
        z=.011+max(0,off)*.035
        y=.007+off*.044
        set_line(O[f'Beach walker leg {side}'],[(side*.024,0,.135),(side*.030,y*.60,.068),(side*.029,y,z)])
        O[f'Beach walker shoe {side}'].location=(side*.029,y-.013,z)
    on=ease(t,19.90,20.32)
    pop=pulse(t,34.47,34.67,35.01,35.54)
    O['TV warm pink bounce'].data.energy=12+on*65
    O['TV cold cyan bounce'].data.energy=12+on*43
    O['Door hallway practical'].data.energy=64+270*pop+168*ease(t,34.7,35.42)
    O['Door rim to Papa'].data.energy=45+67*ease(t,34.45,34.90)
    alarm=pulse(t,55.97,56.36,58.36,58.48)
    value=.5+.5*math.sin((t-56.07)*math.tau*1.75)
    O['Siren warm sweep'].data.energy=alarm*(50+164*value)
    O['Siren cool sweep'].data.energy=alarm*(50+164*(1-value))
    for key in ('ALT key','TAB key','Enter key'):
        at=t
        toggle=math.sin(at*82+(1.2 if key=='ALT key' else .0))
        g=pulse(at,40.48,40.67,42.02,42.27)*max(0,toggle)
        if key=='Enter key':g=max(g,pulse(at,20.00,20.10,20.18,20.27))
        O[key].location.z=.030-.014*g
    at_door=name in ('midnight','latch')
    gamer_show=at_door or name not in ('pc_reveal','neon_display','beach_freeze','freeze_popup','shoe','boss','orbit','freeze')
    visible(O['Gamer'],gamer_show)
    seated=not at_door and name not in ('cower','orbit','freeze')
    x,y=-.67,-.30
    yaw=math.pi if name in ('start','beach','keys') else -.22
    dz=-.04 if seated else 0
    if name in ('chips','awe','panic','cower'):
        # Put the shoulders on the same viewing side as the face on close-ups.
        delta=S.camera.location-V((x,y,1.45))
        yaw=math.atan2(delta.x,-delta.y)
    if at_door:
        latch=world_local(O['Door hand latch anchor'])
        x,y=latch.x-.08,latch.y-.58
        yaw=3.1
    if name in ('cower','orbit','freeze'):
        retreat=ease(tt,50.75,51.65)
        x,y=-.72-.30*retreat,-.38-.42*retreat
        dz=-.55*retreat
        delta=S.camera.location-V((x,y,1.04))
        yaw=math.atan2(delta.x,-delta.y)
    gamer=body_pose('Gamer',(x,y,0),yaw,dz,.12 if name in ('cower','orbit','freeze') else -.08 if name=='panic' else 0)
    PARTS['Gamer']['torso rig'].rotation_euler.x=.18 if name=='cower' else 0
    mood={'awe':'awe','neon_display':'awe','panic':'panic','keys':'panic','cower':'fear','orbit':'fear','freeze':'fear'}.get(name,'smirk')
    face('Gamer',mood,t if name!='freeze' else tt,(0,1,-.02) if name in ('beach','start','keys') else None,
         .18*pulse(t,42.95,43.04,43.40,43.7) if name=='panic' else 0)
    for side in (-1,1):
        # Foot contact follows the fixed floor/seat state; seated knees reach toward the screen.
        px=x+math.cos(yaw)*side*.148
        py=y+(.27 if yaw>2 and seated else -.24 if seated else -.11)
        foot('Gamer',side,(px,py,0 if at_door else .025),seated=seated)
        w=world_local(gamer,(side*.344,-.11,.79+dz))
        arm('Gamer',side,w)
    if at_door:
        p=world_local(O['Door hand latch anchor'])
        resting=world_local(gamer,(-.344,-.11,.79))
        reach=ease(t,14.69,15.78)
        arm('Gamer',-1,resting.lerp(p,reach))
        if reach>=1:
            CONTACTS[('Gamer',-1)]=p
    if name=='chips':
        bag=O['Chips packet']
        forward=V((math.sin(yaw),-math.cos(yaw),0))
        bag.location=V((x,y,1.015+.043*ease(t,17.25,17.92)))+forward*.232
        bag.rotation_euler=(0,.13*math.sin((t-17.2)*12)*pulse(t,17.28,17.75,18.35,18.68),yaw)
        for side,n in [(-1,'Bag left seam grip'),(1,'Bag right seam grip')]:
            p=world_local(O[n])
            arm('Gamer',side,p,1.07)
            CONTACTS[('Gamer',side)]=p
    else:
        O['Chips packet'].location=(-1.49,.22,.989)
        O['Chips packet'].rotation_euler=(0,0,0)
    visible(O['Chip bag rip seal'],t<18.07)
    for i in range(6):
        chip=O[f'Airborne potato chip {i}']
        q=max(0,min(1,(t-18.06-i*.016)/.51))
        scatter=(i-2.5)*(.034+.11*q)
        launch=O['Chips packet'].location
        chip.location=(launch.x+math.cos(yaw)*scatter+.075*q,launch.y+math.sin(yaw)*scatter,
                       launch.z+.235+(.27-.022*i)*math.sin(math.pi*q)-.18*q)
        chip.rotation_euler=(q*5.1+i*.24,q*4,q*2)
        visible(chip,name=='chips' and 0<q<1)
    if name in ('start','beach','keys'):
        key=O['ALT key'] if name=='keys' else O['Enter key']
        target=world_local(key,(0,0,.044))
        if name=='keys':
            second=world_local(O['TAB key'],(0,0,.041))
        else:second=world_local(O['RGB mouse grip'],(0,-.002,.055))
        if name=='keys':
            # Left palm remains over the modifier cluster; its fingers alternate between the keys.
            blend=.5+.5*math.sin((t-40.36)*38)
            key_contact=target.lerp(second,blend)
            arm('Gamer',1,key_contact,1.085)
            CONTACTS[('Gamer',1)]=key_contact
            second=world_local(O['RGB mouse grip'],(0,-.002,.055))
        else:
            arm('Gamer',1,target,1.085)
            CONTACTS[('Gamer',1)]=target
        arm('Gamer',-1,second,1.078)
        CONTACTS[('Gamer',-1)]=second
    if name=='awe':
        reach=pulse(t,23.08,23.66,24.73,25.61)
        for side in (-1,1):
            target=world_local(gamer,(side*.353,-.15,.80)).lerp(world_local(PARTS['Gamer']['head pivot'],(side*.335,-.03,.016)),reach)
            arm('Gamer',side,target,1.17)
    if name in ('panic','cower','orbit','freeze'):
        hide_time=ease(tt,50.85,51.56) if name not in ('panic',) else .74
        for side in (-1,1):
            shape=(side*.238,-.058,.23) if name=='cower' else (side*.342,-.065,.145*hide_time)
            target=world_local(PARTS['Gamer']['head pivot'],shape)
            arm('Gamer',side,target,1.21+dz)

    for i in range(3):
        wisp=O[f'Keyboard fault smoke {i}']
        q=(t-41.91-i*.095)/.67
        visible(wisp,name in ('keys','freeze_popup','panic') and 0<q<1)
        if 0<q<1:
            wisp.location=(-.83+i*.11+.12*q,.46+.066*i,1.11+.25*q)
            fade=math.sin(math.pi*q)
            wisp.scale=(.56+.38*q,1,.31+.69*fade)
            wisp.rotation_euler.z=.32*math.sin(q*4+i)
    appear=t>=33.95
    visible(O['Papa'],appear and name not in ('beach_freeze','freeze_popup','keys','panic'))
    step=ease(tt,34.56,36.58)
    px=1.42-.09*step
    py=2.72-1.55*step
    crouch=pulse(tt,43.73,44.54,45.07,46.16)
    dad=body_pose('Papa',(px,py,0),.07,-.385*crouch,.15*crouch)
    face('Papa','stern talk' if 46.24<=t<50.0 else 'stern',tt,roll=-.05-.065*crouch)
    for side in (-1,1):
        original_y=2.72-1.55*ease(tt,34.56+(.13 if side>0 else 0),36.52+(.08 if side<0 else 0))
        stride=pulse(tt,34.58,34.81,36.11,36.62)*max(0,math.sin((tt-34.54)*6.9+side*math.pi/2))
        right=side==-1
        slip=O['Papa right chappal' if right else 'Papa left chappal']
        backward=.06 if right else -.03
        floor=(px+side*.147,original_y+backward,0)
        hop=.072*stride
        removed=ease(tt,43.91,44.49) if right else 0
        foot('Papa',side,(floor[0],floor[1]-.19*removed,0),.047*(1-removed)+hop+.089*math.sin(math.pi*removed))
        slip.location=(floor[0],floor[1],hop)
        slip.rotation_euler=(0,0,.07)
        arm('Papa',side,world_local(dad,(side*.345,-.13,.83-.36*crouch)))
        visible(slip,appear)
    right=O['Papa right chappal']
    pick=ease(tt,44.74,45.72)
    up=ease(tt,45.68,46.43)
    if pick>0:
        wind=pulse(tt,52.28,54.00,57.92,58.43)
        pre_hold=ease(tt,57.94,58.43)
        side_push=.54*ease(tt,54.75,56.94)
        right.location=V((px-.147,py+.06,0)).lerp(V((px-.53,py-.16,.72)),pick)
        right.location=right.location.lerp(V((px-.48-.10*wind,py-.17+.24*wind+side_push,1.970+.13*wind-.085*pre_hold)),up)
        right.rotation_euler=(1.18*pick+.36*wind,.38*up+.17*wind,-.43*up-.24*wind)
    if tt>=44.44:
        target=world_local(O['Papa right chappal hand seat'])
        if tt<44.74:
            travel=ease(tt,44.44,44.74)
            target=world_local(dad,(-.34,-.17,.53)).lerp(target,travel)
        arm('Papa',-1,target,elbow_back=.30*ease(tt,54.75,56.94))
        if tt>=44.74:CONTACTS[('Papa',-1)]=target
    if show_stars:
        for j in range(5):
            item=O[f'Original wanted star {j}']
            a=56.4+j*.243
            visible(item,t>=a)
            size=1+.30*pulse(t,a,a+.076,a+.087,a+.20)
            item.scale=(size,size,size)

def handler(scene,*unused):
    update(scene.frame_current)

def register():
    for fn in list(bpy.app.handlers.frame_change_post):
        if getattr(fn,'_gta_story',False):bpy.app.handlers.frame_change_post.remove(fn)
    handler._gta_story=True
    bpy.app.handlers.frame_change_post.append(handler)
    look.install_shadow_policy(S)
    update(S.frame_current,True)
