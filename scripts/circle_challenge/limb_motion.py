"""Bake editable 2.5D limb hierarchies and finite acting beats."""
import math
from mathutils import Vector, Quaternion

def track(obj, prop, keys, mode='LINEAR'):
    """Replace one transform channel with a sampled curve."""
    if not obj.animation_data:
        obj.animation_data_create()
    if not obj.animation_data.action:
        import bpy
        obj.animation_data.action=bpy.data.actions.new(obj.name)
    action=obj.animation_data.action
    for curve in list(action.fcurves):
        if curve.data_path==prop:
            action.fcurves.remove(curve)
    keys=sorted(dict(keys).items())
    for axis in range(len(keys[0][1])):
        curve=action.fcurves.new(prop,index=axis)
        curve.keyframe_points.add(len(keys))
        curve.keyframe_points.foreach_set('co',[v for frame,value in keys for v in (frame,value[axis])])
        for point in curve.keyframe_points:
            point.interpolation=mode
        curve.update()

def animate_walk_cycle(rig, f_start, f_end, speed, is_run=False, is_backward=False):
    rig['cycles'].append((f_start,f_end,speed,is_run,is_backward))

def chain(name,parent,ctx,thickness):
    empty,prop,ink=ctx
    upper=empty(name+' Upper',parent=parent)
    lower=empty(name+' Lower',parent=upper)
    tip=empty(name+' Tip',parent=lower)
    shaft=prop(name+' proximal ink',(0,0,0),(1,1,1),ink,upper,'sphere')
    calf=prop(name+' distal ink',(0,0,0),(1,1,1),ink,lower,'sphere')
    prop(name+' rounded joint',(0,0,0),(thickness,)*3,ink,lower,'sphere')
    cap=(.094,.03,.047) if 'Leg' in name else (thickness*1.45,)*3
    prop(name+' dark cap',(0,0,0),cap,ink,tip,'sphere')
    return (upper,lower,tip,shaft,calf,thickness)

def make_rig(actor,ctx):
    pivot=next(child for child in actor.children if child.name.endswith('_body_billboard'))
    chains=[chain(actor.name+f' {side} {kind}',pivot,ctx,.023 if kind=='Arm' else .024)
            for kind in ('Leg','Arm') for side in ('L','R')]
    return {'actor':actor,'pivot':pivot,'chains':chains,'cycles':[],'tips':{}}

def bake_rig(rig, samples, acting):
    paths=[{} for _ in rig['chains']]
    for frame in samples:
        active=next((cycle for cycle in rig['cycles'] if cycle[0]<=frame<=cycle[1]),None)
        for index,chains in enumerate(rig['chains']):
            sign=-1 if index%2==0 else 1
            is_leg=index<2
            start=Vector((sign*(.107 if is_leg else .144),1.22 if is_leg else 1.68,0))
            end=Vector((sign*(.226 if is_leg else .29),.031 if is_leg else .91,.006))
            bend=Vector((sign*(.04 if is_leg else .14),0,.018))
            if active:
                f0,_,speed,run,back=active
                phase=((frame-f0)*speed+(.5 if sign>0 else 0))%1
                direction=-1 if back else 1
                stride=.43 if run else .25
                if phase<.58:
                    reach=1-2*phase/.58
                    lift=0
                else:
                    u=(phase-.58)/.42
                    reach=-math.cos(math.pi*u)
                    lift=(.38 if run else .22)*math.sin(math.pi*u)
                if is_leg:
                    end.x+=direction*stride*reach
                    end.y+=lift
                    end.z+=.10*reach
                    bend.x+=direction*(.15+.12*lift)
                    bend.z+=.11
                else:
                    end.x-=direction*stride*.72*reach
                    end.y+=.16+.16*abs(reach)
                    bend.z+=.08
            start,end,bend=acting(frame,index,start,end,bend)
            mid=(start+end)/2+bend
            upper_q=(mid-start).to_track_quat('Z','Y')
            lower_q=(end-mid).to_track_quat('Z','Y')
            l1=(mid-start).length
            l2=(end-mid).length
            upper,lower,tip,shaft,calf,w=chains
            values=[
                (upper,'location',start),(upper,'rotation_quaternion',upper_q),
                (lower,'location',(0,0,l1)),(lower,'rotation_quaternion',upper_q.inverted()@lower_q),
                (tip,'location',(0,0,l2)),(tip,'rotation_quaternion',lower_q.inverted()),
                (shaft,'location',(0,0,l1/2)),(shaft,'scale',(w,w,l1/2+w)),
                (calf,'location',(0,0,l2/2)),(calf,'scale',(w,w,l2/2+w)),
            ]
            for obj,prop,value in values:
                paths[index].setdefault((obj,prop),[]).append((frame,tuple(value)))
    for channels in paths:
        for (obj,prop),keys in channels.items():
            if prop=='rotation_quaternion':
                obj.rotation_mode='QUATERNION'
                stable=[]
                previous=None
                for frame,value in keys:
                    q=Quaternion(value)
                    if previous is not None and q.dot(previous)<0:
                        q.negate()
                    stable.append((frame,tuple(q)))
                    previous=q
                keys=stable
            track(obj,prop,keys)
