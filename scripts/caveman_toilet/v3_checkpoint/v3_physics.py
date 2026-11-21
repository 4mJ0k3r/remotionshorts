"""V3 contact fixes. Geometry, poses and tool FX share one source of truth."""
import math
import bpy
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
import v2_story as story
from v2_common import bake, hide_keys, cam_quat

_pose = story.pose_state
_camera = story.camera_at
_terrain = None
MOUND = Vector((0.75, 1.4, 0.34))


def smooth(u):
    u = max(0., min(1., u))
    return u*u*(3-2*u)


def configure_sets():
    global _terrain
    # The original floating ellipsoids ended at a positive-Z equator, making
    # a real terrain step. A quartic dome preserves each peak and footprint
    # while meeting the base ground continuously with a horizontal tangent.
    for ob in bpy.data.objects:
        if ob.name.startswith('hill_'):
            radius=max(abs(v.co.z) for v in ob.data.vertices)
            height=ob.location.z+radius*ob.scale.z
            for vertex in ob.data.vertices:
                nz=vertex.co.z/radius
                vertex.co.z=(height*nz**4 if nz>=0 else -.025*abs(nz))/ob.scale.z
            ob.location.z=0
            ob.data.update()
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for ob in list(bpy.data.objects):
        if ob.name == 'savanna_ground' or ob.name.startswith('hill_'):
            ev = ob.evaluated_get(deps)
            mesh = ev.to_mesh()
            offset = len(verts)
            verts.extend(ev.matrix_world @ v.co for v in mesh.vertices)
            polys.extend(tuple(offset+i for i in p.vertices) for p in mesh.polygons)
            ev.to_mesh_clear()
    _terrain = BVHTree.FromPolygons(verts, polys)
    for ob in list(bpy.data.objects):
        if ob.name.startswith(('outcrop_', 'hide_rock_2')):
            # Leave the full rock bounds outside the 1.6m pedestrian corridor.
            side = -1 if ob.location.x < 0 else 1
            radius = max(abs(v[0]) for v in ob.bound_box)*abs(ob.scale.x) + .2
            ob.location.x = side*max(abs(ob.location.x), 1.1+radius)
            ob.location.z += get_ground_z(ob.location.x, ob.location.y)
        if ob.name.startswith(('fg_pillar_', 'fg_rock_')):
            bpy.data.objects.remove(ob, do_unlink=True)
    rock = bpy.data.objects['hide_rock_main']
    rock.location = (0, -.35, .22)
    bpy.data.objects['soil_mound'].location = (.75, 1.4, .12)
    for name in ('cave_floor', 'cave_roof', 'cave_ceil', 'cave_ceiling', 'cave_left', 'cave_right', 'cave_L', 'cave_R'):
        ob = bpy.data.objects.get(name)
        if ob:
            ob.location.y = -1.25
            ob.scale.y = 13.5
    # Match by parent as well, so wall names cannot leave a front-edge sky leak.
    for ob in bpy.data.objects['set_B'].children_recursive:
        if ob.type == 'MESH' and ob.name.startswith(('cave_side', 'ceiling')):
            ob.location.y = -1.25
            ob.scale.y = 13.5
    bpy.context.view_layer.update()


def get_ground_z(x, y, set_name='A'):
    if set_name != 'A' or _terrain is None:
        return 0.
    hit = _terrain.ray_cast(Vector((x, y, 10)), Vector((0, 0, -1)), 30)[0]
    return hit.z if hit else 0.


def camera_at(f):
    pos, look, lens = _camera(f)
    cid = story.cut_at(f)[0]
    if cid in (3, 6):
        start, end = ((story.WALK3_START, story.WALK3_END) if cid == 3
                      else (story.WALK6_START, story.WALK6_END))
        cut = story.cut_at(f)
        xy = story.walk_state(f, cut[1], cut[2], start, end)['pelvis'][:2]
        z = get_ground_z(*xy)
        pos = (pos[0], pos[1], pos[2]+z)
        look = (look[0], look[1], look[2]+z)
    if cid == 14:
        # Accommodate the two outward rolled heads without cropping them.
        pos, look, lens = (0, -2.8, 2.25), (0, .75, .45), 34
    if cid == 13:
        lens = 42
    if cid == 18:
        pos, look, lens = (.05, -3.8, 1.4), (.05, .6, .85), 34
    return pos, look, lens


def shovel_pose(f):
    if f >= 1494:
        return MOUND.copy(), Quaternion(), 0.
    if f < 1370:
        f = 1370
    age = f-1370
    phase = age % 35 if age < 105 else 34
    # Blade and both grips are derived from the same rigid shaft transform.
    if phase <= 10:
        u = smooth(phase/10)
        p = Vector((0, .28+.18*u, .12-.40*u))
        thrust = u
    elif phase <= 22:
        u = smooth((phase-10)/12)
        p = Vector((.08*u, .46-.15*u, -.28+.88*u))
        thrust = 1-u
    else:
        u = smooth((phase-22)/12)
        p = Vector((.08*(1-u), .31-.03*u, .60-.48*u))
        thrust = 0.
    direction = Vector((-.45, -.55, .707)).normalized()
    camera_pos, camera_look, _ = camera_at(1370)
    normal = cam_quat(camera_pos,camera_look) @ Vector((0,0,1))
    actor_center = Vector((0,-.15,.80))
    forward = max((actor_center-(p+direction*g)).dot(normal) for g in (.38,.66))+.065
    p += normal*max(0.,forward)
    return p, direction.to_track_quat('Z', 'Y'), thrust


def pose_state(char, f):
    # Keep the nose pinch intact until its cut ends; the V2 story started
    # a different collapse five frames before the V3 collapse cut.
    source_frame=min(f,1119) if 1038<=f<1125 else f
    st = _pose(char, source_frame)
    if st is None:
        return None
    st = dict(st, frame=f, char=char)
    cid, _, _, _, sn, _, _ = story.cut_at(f)
    ground = get_ground_z(*st['pelvis'][:2], sn)
    st['ground_z'] = ground
    st['pelvis'] = (*st['pelvis'][:2], st['pelvis'][2]+ground)
    st['hands'] = [(x,y,z+ground) for x,y,z in st['hands']]
    st['feet'] = [(x,y,get_ground_z(x,y,sn)+z+.004,p) for x,y,z,p in st['feet']]
    st['shoulder_drop'] = 0.
    if cid == 14:
        delay = 0 if char == 'caveman' else 5
        u = smooth((f-1125-delay)/(40-delay))
        x,y = story.PINCH_POS[char]
        st.update(pelvis=(x,y,.50-.32*u), lean=0., tilt=0.,
                  roll=math.radians(78 if char == 'caveman' else -78)*u,
                  collapse=u, expr='knockout')
    if cid == 17:
        p,q,thrust = shovel_pose(f)
        direction = q @ Vector((0,0,1))
        st['hands'] = [tuple(p+direction*.66), tuple(p+direction*.38)]
        st['lean'] = math.radians(12)*thrust
        if f>=1475:
            st['pelvis']=(*st['pelvis'][:2],st['pelvis'][2]+.015*math.sin((f-1475)*.35))
            st['tilt']=.02*math.sin((f-1475)*.35)
    return st


def rig_solve(st, cam_pos):
    f = st['frame']
    cid = story.cut_at(f)[0]
    pos, look, _ = camera_at(f)
    qcam = cam_quat(pos, look)
    normal = qcam @ Vector((0,0,1))
    right = qcam @ Vector((1,0,0))
    up = qcam @ Vector((0,1,0))
    P = Vector(st['pelvis'])
    roll = st.get('roll', -.20*st['lean'])
    q = qcam @ Quaternion((0,0,1), roll)
    R = q @ Vector((1,0,0))
    U = q @ Vector((0,1,0))
    torso = P+U*.30
    # Alpha bounds: torso top +.355, head lower radius .248. Slight overlap
    # ensures a continuous neck, including the deepest squat and sideways fall.
    head = torso+U*(.355+.248*.88)+normal*.012
    shoulders = [P+U*.57+R*(side*.21)-normal*.018 for side in (-1,1)]
    if cid == 13:
        # Attach inside the opaque shirt shoulder, not its transparent margin.
        shoulders[1] = P+U*.54+R*.145+normal*.065
    hips = [P+U*.02+R*(side*.09) for side in (-1,1)]
    arms, legs = [], []
    from v2_common import ik2
    fall = st.get('collapse', 0.)
    hands = list(st['hands'])
    if cid not in (13,17,18):
        hands.sort(key=lambda p: Vector(p).dot(right))
    for idx,side in enumerate((-1,1)):
        hand = Vector(hands[idx])
        foot = Vector(st['feet'][idx][:3])
        if cid == 13:
            if side == 1:
                hand = head-up*.045+normal*.045
            else:
                hand = P-right*.29+up*.11+normal*.025
        if cid == 18:
            if st['char'] == 'caveman':
                hand = (P+right*(side*(.31+.055*math.sin((f-1494)*.20)))
                        +up*(.82 if side == 1 else .12)+normal*.04)
            else:
                gap = .025+.13*abs(math.sin((f-1494)*.24))
                hand = P+up*.52+right*(side*gap)+normal*.16
        if fall:
            spread = P+right*(side*.48)+Vector((0,-.12,0))
            spread.z = .06
            hand = hand.lerp(spread,fall)
            dest = P-right*(.38 if st['char']=='caveman' else -.38)+Vector((side*.20,-.18,0))
            dest.z = .06
            foot = foot.lerp(dest,fall)
        pole = right*(side*.65)+normal*.10
        elbow = ik2(shoulders[idx], hand, .28, .28, pole)
        if cid == 13 and side == 1:
            elbow = shoulders[idx]+right*.22+up*.12+normal*.02
        knee = ik2(hips[idx], foot, .29, .29, right*(side*.5)+normal*.22)
        if story.set_for_frame(f) == 'A':
            knee.z = max(knee.z, get_ground_z(knee.x,knee.y)+.065)
            # NURBS order-3 is a quadratic Bezier. Clear the actual terrain
            # along its entire arc, not only at the three control points.
            raise_by = 0.
            for j in range(1,20):
                t=j/20
                sample=hips[idx]*(1-t)**2+knee*(2*t*(1-t))+foot*t*t
                needed=get_ground_z(sample.x,sample.y)+.022-sample.z
                raise_by=max(raise_by,needed/(2*t*(1-t)))
            knee.z+=max(0.,raise_by)
        if fall:
            knee.z = knee.z*(1-fall)+.06*fall
            elbow.z = elbow.z*(1-fall)+.06*fall
        arms.append((shoulders[idx],elbow,hand))
        legs.append((hips[idx],knee,foot))
    return dict(torso_c=torso, torso_q=q, head_c=head,
                head_q=q @ Quaternion((0,0,1), st['tilt']),
                arms=arms, legs=legs, foot_q=[Quaternion(),Quaternion()], P=P)


def replace_bake(ob, path, frames, values):
    if ob.animation_data and ob.animation_data.action:
        action = ob.animation_data.action
        for fc in list(action.fcurves):
            if fc.data_path == path:
                action.fcurves.remove(fc)
    bake(ob,path,frames,values)


def bake_tools(fx, frames):
    shovel = fx['shovel']['ob']
    shovel.rotation_mode = 'QUATERNION'
    fx['shovel']['cuts'] = [17,18]
    poses = [shovel_pose(f) for f in frames]
    replace_bake(shovel,'location',frames,[tuple(p[0]) for p in poses])
    replace_bake(shovel,'rotation_quaternion',frames,[tuple(p[1]) for p in poses])
    # Three 35-frame strokes; ballistic flight begins at the actual blade.
    for i in range(5):
        ob = fx[f'clod_{i}']['ob']
        locs, scales, hidden, quats = [], [], [], []
        for f in frames:
            point = Vector((0,0,-2))
            active = False
            for cycle in range(3):
                launch = 1370+35*cycle+22+i
                flight = 13+i
                if launch <= f <= launch+flight and f < 1494:
                    start = shovel_pose(launch)[0]
                    target = MOUND+Vector(((i-1.5)*.09, (i%2)*.12, 0))
                    T = flight/30
                    t = (f-launch)/30
                    velocity = (target-start)/T+Vector((0,0,9.81*T/2))
                    point = start+velocity*t-Vector((0,0,9.81*t*t/2))
                    active = True
                    break
            locs.append(tuple(point))
            scales.append((.13,.13,1) if active else (0,0,0))
            hidden.append(not active)
            quats.append(tuple(cam_quat(*camera_at(f)[:2])))
        ob.rotation_mode='QUATERNION'
        replace_bake(ob,'location',frames,locs)
        replace_bake(ob,'scale',frames,scales)
        replace_bake(ob,'rotation_quaternion',frames,quats)
        replace_bake(ob,'hide_render',frames,hidden)
        for fc in ob.animation_data.action.fcurves:
            if fc.data_path=='hide_render':
                for k in fc.keyframe_points:
                    k.interpolation='CONSTANT'
    for char in ('caveman','buddy'):
        for i in range(3):
            ob=fx[f'soul_{char}_{i}']['ob']
            launch=1165+i*8
            origin=rig_solve(pose_state(char,1165),camera_at(1165)[0])['head_c']
            values=[]
            for f in frames:
                u=max(0,min(1,(f-launch)/30))
                values.append(tuple(origin+Vector((.04*math.sin(u*6+i),0,.9*u))))
            replace_bake(ob,'location',frames,values)
            ob.rotation_mode='QUATERNION'
            replace_bake(ob,'rotation_quaternion',frames,[tuple(cam_quat(*camera_at(f)[:2])) for f in frames])


SHEET_FRAMES = [40,159,230,382,415,429,480,560,620,800,1080,1125,
                1145,1165,1180,1200,1380,1392,1399,1427,1462,1494,1560,1620]
