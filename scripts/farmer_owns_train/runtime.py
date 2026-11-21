"""Frame-addressable 20-cut rapid-fire acting, 3D tailored trouser legs, 12cm stepping, close-up cameras, top HUD pills & camera-quaternion billboards."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector, Quaternion

V = Vector
S = bpy.context.scene
O = S.objects
ROOT = Path(S.get('studio_root', 'D:/remotionshorts'))
OUT = ROOT / 'renders' / 'farmer_owns_train'
ENV = json.loads((OUT / 'audio_env.json').read_text())

ns = {'__name__': 'studio_ink'}
exec(bpy.data.texts['studio_set_ink.py'].as_string(), ns)
INK = ns['SetInk'](S)

GROUPS = {}
for name in [
    'SET_STATION', 'SET_STREET_FARM', 'SET_COURTROOM',
    'TrainRoot', 'RedCar', 'TowChain', 'OfficeDesk', 'JusticeScales',
    'CourtGavel', 'GavelShockRing', 'BenchWarrant', 'WarrantScroll',
    'GoldCoin', 'BanRing', 'ReverseArrows', 'EmptyBag', 'GoldCrown', 'GreenFlag',
] + [f'CalendarPage{i}' for i in range(8)]:
    root = O[name]
    GROUPS[name] = [root] + list(root.children_recursive)

ACTORS = ['farmer', 'judge', 'bailiff', 'loco_pilot', 'common_man', 'bank_officer']
for kind in ACTORS:
    GROUPS[kind] = [o for o in O if o.name.startswith(kind + '_') or o.name == 'char_' + kind]

VIS = {}
FX = [o for o in O if any(o.name.startswith(p) for p in ['Sweat', 'Steam'])]
TRAIN_WHEELS = [o for o in O if o.name.startswith('TrainWheel_')]
CAR_WHEELS = [o for o in O if o.name.startswith('CarWheel')]
PASSENGER_CARDS = [O[f'PassengerPeek{i}'] for i in range(3) if f'PassengerPeek{i}' in O]

# 20 rapid-fire micro-cuts (~2.5s avg) with HUD index 0..19
SHOTS = [
    ('1A-1', 1, 110, 0),
    ('1A-2', 110, 222, 1),
    ('1B-1', 222, 275, 2),
    ('1B-2', 275, 333, 3),
    ('2A-1', 333, 420, 4),
    ('2A-2', 420, 507, 5),
    ('2B', 507, 570, 6),
    ('2C-1', 570, 680, 7),
    ('2C-2', 680, 792, 8),
    ('3A-1', 792, 885, 9),
    ('3A-2', 885, 981, 10),
    ('3B', 981, 1095, 11),
    ('3C-1', 1095, 1165, 12),
    ('3C-2', 1165, 1221, 13),
    ('4A-1', 1221, 1275, 14),
    ('4A-2', 1275, 1329, 15),
    ('4B', 1329, 1422, 16),
    ('4C-1', 1422, 1505, 17),
    ('4C-2', 1505, 1585, 18),
    ('4C-3', 1585, 1669, 19),
]


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def ramp(f, a, b):
    if b <= a:
        return 1.0
    return ease((f - a) / (b - a))


def lerp(a, b, t):
    return V(a).lerp(V(b), t)


def vis(name, on):
    if VIS.get(name) == on:
        return
    for o in (GROUPS[name] if name in GROUPS else [O[name]]):
        o.hide_render = not on
    if name.startswith('SET_'):
        for nested, items in GROUPS.items():
            if nested != name and items[0] in GROUPS[name]:
                VIS.pop(nested, None)
    VIS[name] = on


def move(name, p, q=None):
    o = O[name]
    o.location = p
    if q is not None:
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = q
    return o


def move_world(name, p, q=None):
    o = O[name]
    offset = o.parent.matrix_world.translation if o.parent else V((0, 0, 0))
    o.location = V(p) - offset
    if q is not None:
        o.rotation_mode = 'QUATERNION'
        o.rotation_quaternion = q
    return o


def material(name, mat_name):
    o = O[name]
    mat = bpy.data.materials[mat_name]
    if not o.data.materials or o.data.materials[0] != mat:
        o.data.materials.clear()
        o.data.materials.append(mat)


def polycurve(name, points, radii=None):
    sp = O[name].data.splines[0]
    for idx, (pt, co) in enumerate(zip(sp.points, points)):
        pt.co = (*co, 1.0)
        if radii is not None:
            pt.radius = radii[idx]


def limb_pole(name, a, b, side, q, bend=0.065, radii=None):
    delta = b - a
    dist = delta.length
    axis = q @ V((side, 0, 0))
    pole = axis - delta.normalized() * axis.dot(delta.normalized()) if dist > 1e-5 else axis
    if pole.length < 1e-5:
        pole = q @ V((side, 0.1, 0))
    pole.normalize()
    mid = (a + b) * 0.5 + pole * bend
    points = []
    for i in range(25):
        t = i / 24.0
        points.append((1 - t) ** 2 * a + 2 * (1 - t) * t * mid + t * t * b)
    polycurve(name, points, radii)


def knee_of(hip, ankle, pole, len_a=0.255, len_b=0.255):
    delta = ankle - hip
    dist = delta.length
    axis = delta.normalized() if dist > 1e-5 else V((0, 0, -1))
    stretch = max(1.0, (dist + 0.0001) / (len_a + len_b))
    la = len_a * stretch
    lb = len_b * stretch
    dist = max(0.0001, dist)
    along = (la ** 2 - lb ** 2 + dist ** 2) / (2.0 * dist)
    height = math.sqrt(max(0.0, la ** 2 - along ** 2))
    perp = pole - axis * pole.dot(axis)
    if perp.length < 1e-5:
        perp = V((0, -1, 0))
    return hip + axis * along + perp.normalized() * height


def limb_through_joint(name, a, joint, b, radii=None):
    ctrl = joint * 1.75 - (a + b) * 0.375
    points = []
    for i in range(25):
        t = i / 24.0
        points.append((1 - t) ** 2 * a + 2 * (1 - t) * t * ctrl + t * t * b)
    polycurve(name, points, radii)


def talk(f):
    idx = min(len(ENV) - 1, max(0, int(f) - 1))
    return round(min(1.0, max(0.0, ENV[idx])) * 5.0)


def blink(f, seed):
    return any(abs(f - (seed + 137 * i + 17 * (i % 3))) <= 2 for i in range(15))


TROUSER_RADII = [1.06 - 0.10 * (i / 24.0) for i in range(25)]


def update_character_legs(kind, root, right, n, hq, yaw_q, lower, seated, walk_phase, walk_dir, hide_lower):
    w_dir = V(walk_dir).normalized() if walk_phase is not None else V((0, 1, 0))
    walk_bob = 0.022 * abs(math.sin(walk_phase)) if walk_phase is not None else 0.0
    max_foot_lift = 0.0
    for i, side in enumerate([-1, 1]):
        letter = 'L' if side < 0 else 'R'
        hip = root + right * (side * 0.108) + V((0, 0, 0.58 - lower + walk_bob)) - n * 0.028
        if seated:
            knee = root + right * (side * 0.12) + V((0, 0, 0.36)) + n * 0.18
            foot = root + right * (side * 0.14) + V((0, -0.30, 0.042))
            ankle = foot + V((0, 0, 0.045))
            limb_through_joint(f'{kind}_leg{letter}', hip, knee, ankle, TROUSER_RADII)
            limb_through_joint(f'{kind}_trouser{letter}', hip + n * 0.008, knee + n * 0.014, ankle + n * 0.014, TROUSER_RADII)
            lift = 0.0
        elif walk_phase is not None:
            p_phase = walk_phase + (0.0 if side < 0 else math.pi)
            # Upgrade: 12 cm (0.12m) peak vertical foot lift for energetic stride!
            lift = max(0.0, math.sin(p_phase)) * 0.12
            max_foot_lift = max(max_foot_lift, lift)
            stride = math.cos(p_phase) * 0.21
            foot = root + right * (side * 0.118) + w_dir * stride + V((0, 0, 0.036 + lift))
            ankle = foot + V((0, 0, 0.048))
            pole = w_dir * (0.16 + 0.16 * (lift / 0.12)) + right * (side * 0.03) + n * 0.06
            knee = knee_of(hip, ankle, pole, 0.265, 0.265)
            limb_through_joint(f'{kind}_leg{letter}', hip, knee, ankle, TROUSER_RADII)
            limb_through_joint(f'{kind}_trouser{letter}', hip + n * 0.009, knee + n * 0.015, ankle + n * 0.015, TROUSER_RADII)
        else:
            lift = 0.0
            foot = root + right * (side * 0.122) + V((0, 0, 0.036)) - n * 0.01
            ankle = foot + V((0, 0, 0.048))
            pole = n * 0.10 + right * (side * 0.03)
            knee = knee_of(hip, ankle, pole, 0.265, 0.265)
            limb_through_joint(f'{kind}_leg{letter}', hip, knee, ankle, TROUSER_RADII)
            limb_through_joint(f'{kind}_trouser{letter}', hip + n * 0.009, knee + n * 0.015, ankle + n * 0.015, TROUSER_RADII)

        pitch = -0.26 * (lift / 0.12) if lift > 0.01 else 0.0
        shoe_q = yaw_q @ Quaternion((1, 0, 0), pitch) if lift > 0.01 else yaw_q
        move(f'{kind}_shoe{letter}', foot, shoe_q)
        ground = V((foot.x, foot.y, root.z + 0.003))
        contact = move(f'{kind}_contact{letter}', ground, yaw_q)
        contact.hide_render = hide_lower or seated or lift > 0.025

    if hide_lower:
        for part in ['hips', 'legL', 'legR', 'trouserL', 'trouserR', 'shoeL', 'shoeR', 'contactL', 'contactR']:
            O[f'{kind}_{part}'].hide_render = True
    if walk_phase is not None:
        S['max_walk_lift_m'] = max(S.get('max_walk_lift_m', 0.0), max_foot_lift)


def actor(
    kind, pos, expr='neutral', pose='rest', f=1, roll=0,
    seated=False, spoken=True, targets=None, mouth_state=None,
    turn_x=0, walk_phase=None, walk_dir=(0, 1, 0), hide_lower=False,
):
    for part in GROUPS[kind]:
        if part.hide_render:
            part.hide_render = False
    VIS[kind] = True

    root = V(pos)
    cam = S.camera
    q = cam.matrix_world.to_quaternion()
    n = q @ V((0, 0, 1))
    right = q @ V((1, 0, 0))
    qr = Quaternion(n, math.radians(roll))
    el = math.atan2(cam.location.z - (root.z + 1.3), max(0.01, math.hypot(cam.location.x - root.x, cam.location.y - root.y)))
    yaw_q = Quaternion((0, 0, 1), math.atan2(right.y, right.x))
    tq = qr @ yaw_q @ Quaternion((1, 0, 0), math.pi / 2 - el * 0.5)
    walk_bob = 0.022 * abs(math.sin(walk_phase)) if walk_phase is not None else 0.0

    def point(x, z, depth=0.0):
        return root + qr @ (V((0, 0, z + walk_bob)) + right * x + n * depth)

    lower = 0.12 if seated else 0.0
    hc = point(0, 1.76 - lower) + n * 0.025
    hq = qr @ q
    move(kind + '_head', hc, hq)
    move(kind + '_torso', point(0, 0.965 - lower) - n * 0.008, tq)
    hips = move(kind + '_hips', point(0, 0.68 - lower) - n * 0.058, qr @ yaw_q)
    hips.scale = (0.130, 0.052, 0.065)

    seed = 63 + ACTORS.index(kind) * 31
    ex = 'blink' if expr not in ['panic', 'shock', 'wink', 'angry'] and blink(f, seed) else expr
    mat_head = f'{kind}_head' if ex == 'neutral' else f'{kind}_{ex}'
    material(kind + '_head', mat_head)

    state = mouth_state or (
        'clenched' if expr == 'panic' else
        'open' if expr == 'shock' else
        'flat' if expr == 'worry' else
        'smirk' if expr in ('smirk', 'wink') else
        'o' if expr == 'angry' else
        'smile'
    )
    amount = talk(f) if spoken else 0
    material(kind + '_mouth', f'mouth_{state}_{amount}')
    mouth_z = -0.145 if kind != 'farmer' else -0.168
    mouthpos = hc + hq @ V((turn_x, mouth_z, 0.018))
    mouth = move(kind + '_mouth', mouthpos, hq)
    mouth.scale = (1.0, 1.45, 1.0) if state in ['panic', 'open'] else (1.05, 1.15, 1.0) if state == 'clenched' else (1.0, 1.0, 1.0)

    w_dir = V(walk_dir).normalized() if walk_phase is not None else V((0, 1, 0))
    hands = []
    for i, side in enumerate([-1, 1]):
        letter = 'L' if side < 0 else 'R'
        a = point(side * 0.178, 1.20 - lower, 0.008)
        x, z, dep = side * 0.24, 0.83 - lower, 0.020
        bend = 0.065
        if pose == 'panic':
            # Clutching head at temples in panic
            x, z, dep = side * 0.36, 1.62 - lower, 0.045
            bend = 0.12
        elif pose == 'shrug':
            # Both hands open & expressive
            x, z, dep = side * 0.42, 1.22 - lower, 0.045
            bend = 0.10
        elif pose in ('confident_open', 'crossed'):
            # Route 2 normal curved black arms from outer shoulders (NEVER cross X-lines over chest!)
            x, z, dep = side * 0.34, 1.02 - lower, 0.035
            bend = 0.11
        elif pose == 'point' and side == 1:
            x, z, dep = 0.42, 1.30 - lower, 0.14
        elif pose == 'hero_hip' and side == -1:
            x, z, dep = -0.27, 0.78 - lower, 0.03
            bend = 0.09
        elif pose == 'desk':
            x, z, dep = side * 0.24, 0.90, -0.16

        if targets and targets[i] is not None:
            b = V(targets[i])
        elif walk_phase is not None:
            # Upgrade: +/-28 deg energetic arm swing (0.23m arc)
            arm_phase = walk_phase + (math.pi if side < 0 else 0.0)
            b = point(x, z + 0.045 * abs(math.cos(arm_phase)), dep) + w_dir * (math.cos(arm_phase) * 0.23)
        else:
            b = point(x, z, dep)

        delta = b - a
        if delta.length > 0.495:
            b = a + delta.normalized() * 0.495
        S['max_arm_reach_m'] = max(S.get('max_arm_reach_m', 0.0), (b - a).length)
        limb_pole(f'{kind}_arm{letter}', a, b, side, hq, bend)
        move(kind + '_hand' + letter, b, hq)
        hands.append(b)

    update_character_legs(kind, root, right, n, hq, qr @ yaw_q, lower, seated, walk_phase, walk_dir, hide_lower)
    return {'head': hc, 'mouth': mouthpos, 'q': hq, 'normal': n, 'hands': hands, 'root': root}


def grip_prop(prop_name, grip_name, hand, q_rot, err_key):
    contact = V(O[grip_name].location)
    prop = move_world(prop_name, V(hand) - q_rot @ contact, q_rot)
    parent_offset = prop.parent.matrix_world.translation if prop.parent else V((0, 0, 0))
    S[err_key] = max(S.get(err_key, 0.0), (parent_offset + prop.location + q_rot @ contact - V(hand)).length)
    return prop


def camera(pos, target, focus, lens=42, fstop=2.2):
    cam = S.camera
    cam.location = pos
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = (V(target) - V(pos)).to_track_quat('-Z', 'Y')
    cam.data.lens = lens
    cam.data.dof.aperture_fstop = fstop
    bpy.context.view_layer.update()
    forward = cam.matrix_world.to_quaternion() @ V((0, 0, -1))
    cam.data.dof.focus_distance = max(0.10, (V(focus) - V(pos)).dot(forward))


def attach_temple_sweat(ch_info, f):
    for i in range(6):
        drop = O[f'Sweat{i:02d}']
        drop.hide_render = False
        age = ((f + i * 11) % 32) / 32.0
        side = -1 if i % 2 == 0 else 1
        row = (i // 2) * 0.08
        sx = side * (0.29 + 0.04 * age)
        sy = 0.22 - row - 0.22 * age
        drop.location = ch_info['head'] + ch_info['q'] @ V((sx, sy, 0.022))
        drop.rotation_mode = 'QUATERNION'
        drop.rotation_quaternion = ch_info['q']
        fade = 1.0 if age < 0.80 else (1.0 - age) / 0.20
        drop.scale = (0.016 * fade, 0.012 * fade, 0.034 * fade)


def set_active(name):
    for group in ['SET_STATION', 'SET_STREET_FARM', 'SET_COURTROOM']:
        vis(group, group == name)


def spin_train_wheels(train_y):
    ang = -train_y / 0.34
    base_q = Quaternion((0, 1, 0), math.pi / 2)
    spin_q = Quaternion((1, 0, 0), ang) @ base_q
    for w in TRAIN_WHEELS:
        w.rotation_mode = 'QUATERNION'
        w.rotation_quaternion = spin_q


def spin_car_wheels(car_dx):
    ang = car_dx / 0.26
    base_q = Quaternion((1, 0, 0), math.pi / 2)
    spin_q = Quaternion((0, 1, 0), ang) @ base_q
    for w in CAR_WHEELS:
        w.rotation_mode = 'QUATERNION'
        w.rotation_quaternion = spin_q


def update(scene, *args):
    f = scene.frame_current
    S['max_arm_reach_m'] = 0.0
    S['max_walk_lift_m'] = 0.0
    S['warrant_grip_error_m'] = 0.0
    S['flag_grip_error_m'] = 0.0
    S['bag_grip_error_m'] = 0.0
    S['gavel_grip_error_m'] = 0.0

    shot = next((item for item in SHOTS if item[1] <= f < item[2]), SHOTS[-1])
    name, a, b, hud_idx = shot
    u = ramp(f, a, b - 1)

    # Update Single Top Screen-Space HUD Pill in Compositor
    if S.use_nodes and S.node_tree:
        hud_node = S.node_tree.nodes.get('HUD_SOURCE')
        hud_gate = S.node_tree.nodes.get('HUD_GATE')
        hud_img = bpy.data.images.get(f'HUD_IMG_{hud_idx}')
        if hud_node and hud_img:
            hud_node.image = hud_img
        if hud_gate:
            hud_gate.inputs[0].default_value = 1.0 if S.get('hud_enabled', True) else 0.0

    for k in ACTORS:
        vis(k, False)
    for fx in FX:
        fx.hide_render = True
    for prop in [
        'WarrantScroll', 'GoldCoin', 'BanRing', 'ReverseArrows',
        'EmptyBag', 'GoldCrown', 'GreenFlag', 'TowChain', 'GavelShockRing',
    ] + [f'CalendarPage{i}' for i in range(8)]:
        vis(prop, False)

    in_station = name.startswith(('1A', '1B', '3B', '3C', '4A', '4B', '4C'))
    vis('TrainRoot', in_station)

    if name == '1A-1':
        # 1A-1 (f1-110): Low-angle hero medium shot of char_farmer in front of 3D Shatabdi Express raising WarrantScroll (20% camera push)
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.50, 0.0))
        spin_train_wheels(0.50)
        O['Loco headlight glow'].data.energy = 65.0
        camera(lerp((-1.95, -5.85, 1.25), (-1.55, -4.75, 1.32), u), (-0.08, -0.85, 1.44), (-0.98, -1.55, 1.55), 38, fstop=2.8)
        raise_hand = V((-0.56, -1.52, 1.38 + 0.10 * u))
        ch = actor('farmer', (-0.98, -1.55, 0.0), 'smile', 'hero_hip', f, spoken=True, targets=[None, raise_hand])
        vis('WarrantScroll', True)
        wq = ch['q'] @ Quaternion((1, 0, 0), -math.pi / 2) @ Quaternion((0, 1, 0), math.radians(-8))
        grip_prop('WarrantScroll', 'WarrantGrip', ch['hands'][1], wq, 'warrant_grip_error_m')

    elif name == '1A-2':
        # 1A-2 (f110-222): TIGHT CHEST-UP CLOSE-UP (lens=58mm, head fills ~60% of frame width, DOF fstop=2.2) on char_farmer smiling proudly
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.50, 0.0))
        spin_train_wheels(0.50)
        O['Loco headlight glow'].data.energy = 65.0
        camera(lerp((-1.05, -4.18, 1.66), (-1.01, -3.65, 1.68), u), (-0.92, -1.55, 1.56), (-0.98, -1.55, 1.72), 58, fstop=2.2)
        raise_hand = V((-0.60, -1.52, 1.44 + 0.04 * math.sin((f - 110) * 0.12)))
        ch = actor('farmer', (-0.98, -1.55, 0.0), 'smile', 'hero_hip', f, spoken=True, targets=[None, raise_hand])
        vis('WarrantScroll', True)
        wq = ch['q'] @ Quaternion((1, 0, 0), -math.pi / 2) @ Quaternion((0, 1, 0), math.radians(-10))
        grip_prop('WarrantScroll', 'WarrantGrip', ch['hands'][1], wq, 'warrant_grip_error_m')

    elif name == '1B-1':
        # 1B-1 (f222-275): Macro insert on spinning 3D golden Rupee coin as red BanRing slams over it with camera shake!
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.50, 0.0))
        spin_train_wheels(0.50)
        slam_t = ramp(f, 228, 236)
        shake_z = 0.038 * math.sin((f - 236) * 2.4) * math.exp(-(f - 236) * 0.42) if 236 <= f <= 243 else 0.0
        shake_x = 0.024 * math.cos((f - 236) * 2.9) * math.exp(-(f - 236) * 0.42) if 236 <= f <= 243 else 0.0
        cam_p = lerp((-0.92, -3.15, 1.62), (-0.92, -2.75, 1.62), u) + V((shake_x, 0.0, shake_z))
        camera(cam_p, (-0.92 + shake_x * 0.5, -1.65, 1.62 + shake_z * 0.5), (-0.92, -1.65, 1.62), 58, fstop=2.2)
        actor('farmer', (-1.58, -1.65, 0.0), 'smirk', 'shrug', f, spoken=True)
        vis('GoldCoin', True)
        vis('BanRing', True)
        coin_sc = 1.45 * (0.20 + 0.80 * ramp(f, 222, 230))
        ban_sc = 1.45 * (2.20 - 1.20 * slam_t) if f >= 228 else 0.001
        cam_right = S.camera.matrix_world.to_quaternion() @ V((1, 0, 0))
        cam_yaw = Quaternion((0, 0, 1), math.atan2(cam_right.y, cam_right.x))
        coin_q = cam_yaw @ Quaternion((0, 0, 1), (f - 222) * 0.16)
        move_world('GoldCoin', (-0.92, -1.65, 1.62), coin_q).scale = (coin_sc, coin_sc, coin_sc)
        move_world('BanRing', (-0.92, -1.72, 1.62), cam_yaw).scale = (ban_sc, ban_sc, ban_sc)

    elif name == '1B-2':
        # 1B-2 (f275-333): Tight chest-up close-up on char_farmer winking/smirking and gesturing with both hands open
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.50, 0.0))
        spin_train_wheels(0.50)
        camera(lerp((-1.42, -4.15, 1.66), (-1.40, -3.65, 1.68), u), (-1.42, -1.65, 1.56), (-1.45, -1.65, 1.72), 58, fstop=2.2)
        f_expr = 'wink' if 285 <= f <= 315 else 'smirk'
        actor('farmer', (-1.45, -1.65, 0.0), f_expr, 'shrug', f, spoken=True)
        vis('GoldCoin', True)
        vis('BanRing', True)
        cam_right = S.camera.matrix_world.to_quaternion() @ V((1, 0, 0))
        cam_yaw = Quaternion((0, 0, 1), math.atan2(cam_right.y, cam_right.x))
        coin_q = cam_yaw @ Quaternion((0, 0, 1), (f - 222) * 0.14)
        move_world('GoldCoin', (-1.02, -1.72, 1.82), coin_q).scale = (0.85, 0.85, 0.85)
        move_world('BanRing', (-1.02, -1.77, 1.82), cam_yaw).scale = (0.85, 0.85, 0.85)

    elif name == '2A-1':
        # 2A-1 (f333-420): Street shot: char_bank_officer (dark charcoal suit & red tie, zero floating black box!)
        # hooks tow-chain to 3D red car and yanks it rightward while char_common_man runs after it (real 4-phase running steps!)
        set_active('SET_STREET_FARM')
        vis('RedCar', True)
        vis('TowChain', True)
        vis('OfficeDesk', False)
        O['StreetFarm fill'].location = (50.2, -2.5, 4.5)
        O['StreetFarm key spot'].location = (49.8, -3.2, 3.6)
        car_x = -1.65 + 1.45 * u
        move_world('RedCar', (50.0 + car_x, -0.35, 0.0))
        spin_car_wheels(car_x + 1.65)
        chain_pos = V((50.0 + car_x + 1.24, -0.35, 0.34))
        move_world('TowChain', chain_pos)
        camera(lerp((49.45, -5.35, 1.34), (49.95, -4.55, 1.36), u), (49.65 + 0.55 * u, -0.15, 0.96), (50.0 + car_x, -0.35, 1.15), 34, fstop=2.8)
        run_phase = (f - 333) * 0.32
        off_x = 50.0 + car_x + 2.32
        chain_grip_world = chain_pos + V((0.92, 0.0, 0.55))
        actor('bank_officer', (off_x, -0.25, 0.0), 'smirk', 'rest', f, spoken=False, targets=[chain_grip_world, None], walk_phase=run_phase + math.pi, walk_dir=(1, 0, 0))
        cm_x = 47.85 + 1.45 * u
        cm = actor('common_man', (cm_x, 0.35, 0.0), 'panic', 'panic', f, spoken=True, mouth_state='panic', walk_phase=run_phase, walk_dir=(1, 0, 0))
        attach_temple_sweat(cm, f)

    elif name == '2A-2':
        # 2A-2 (f420-507): Tight Chest-Up Close-Up on char_common_man with elevator_leak_v3 gridded clenched teeth + 6 glossy temple sweat drops clutching head!
        set_active('SET_STREET_FARM')
        vis('RedCar', True)
        vis('TowChain', False)
        vis('OfficeDesk', False)
        move_world('RedCar', (50.45, -0.35, 0.0))
        camera(lerp((49.10, -2.05, 1.66), (49.10, -1.55, 1.68), u), (49.10, 0.55, 1.56), (49.10, 0.55, 1.72), 58, fstop=2.2)
        cm = actor('common_man', (49.10, 0.55, 0.0), 'panic', 'panic', f, spoken=False, mouth_state='clenched')
        attach_temple_sweat(cm, f)

    elif name == '2B':
        # 2B (f507-570): Fast whip-pan close-up on char_farmer smirking confidently as 2 glowing golden 3D reverse arrows spin rapidly around him
        # (2 normal curved black arms from outer shoulders - zero black X-lines on his chest!)
        set_active('SET_STREET_FARM')
        vis('RedCar', False)
        vis('OfficeDesk', False)
        O['StreetFarm fill'].location = (49.5, 19.5, 4.8)
        whip = (1.0 - ramp(f, 507, 516)) * 0.48
        camera(lerp((49.50 - whip, 19.35, 1.64), (49.50, 19.85, 1.66), u), (49.50 + whip * 0.3, 22.00, 1.54), (49.50, 22.00, 1.70), 58, fstop=2.2)
        actor('farmer', (49.50, 22.00, 0.0), 'smirk', 'confident_open', f, spoken=True)
        vis('ReverseArrows', True)
        spin = (f - 507) * 0.18
        pop = 0.92 * ramp(f, 507, 516)
        arr_q = Quaternion((1, 0, 0), math.radians(-74)) @ Quaternion((0, 0, 1), spin)
        move_world('ReverseArrows', (49.50, 21.76, 1.12), arr_q).scale = (pop, pop, pop)

    elif name == '2C-1':
        # 2C-1 (f570-680): Farmland medium shot: char_farmer stands beside railway tracks holding empty money sack (soft green/golden grass clumps, zero cones!)
        set_active('SET_STREET_FARM')
        vis('RedCar', False)
        vis('OfficeDesk', False)
        O['StreetFarm fill'].location = (49.6, 19.5, 4.8)
        camera(lerp((49.45, 17.35, 1.48), (49.42, 18.25, 1.46), u), (49.40, 21.65, 1.32), (49.36, 21.45, 1.50), 40, fstop=2.6)
        bag_hand = V((49.68, 21.30, 1.08 + 0.03 * math.sin((f - 570) * 0.12)))
        ch = actor('farmer', (49.36, 21.45, 0.0), 'worry', 'rest', f, spoken=True, targets=[None, bag_hand])
        vis('EmptyBag', True)
        bag_q = Quaternion((0, 0, 1), math.atan2((ch['q'] @ V((1, 0, 0))).y, (ch['q'] @ V((1, 0, 0))).x))
        grip_prop('EmptyBag', 'BagGrip', ch['hands'][1], bag_q, 'bag_grip_error_m')

    elif name == '2C-2':
        # 2C-2 (f680-792): Tight close-up on char_bank_officer (railway official in glasses & suit at desk) arrogantly waving hand dismissively while calendar pages fly past lens!
        set_active('SET_STREET_FARM')
        vis('RedCar', False)
        vis('OfficeDesk', True)
        O['StreetFarm fill'].location = (50.6, 19.5, 4.8)
        camera(lerp((50.72, 19.15, 1.54), (50.76, 19.65, 1.56), u), (50.78, 21.85, 1.44), (50.78, 21.85, 1.58), 56, fstop=2.2)
        wave_x = 50.48 + 0.14 * math.sin((f - 680) * 0.28)
        wave_z = 1.24 + 0.05 * math.cos((f - 680) * 0.28)
        actor('bank_officer', (50.78, 21.85, 0.0), 'smirk', 'desk', f, seated=True, spoken=True, targets=[V((wave_x, 21.52, wave_z)), None])
        for i in range(8):
            vis(f'CalendarPage{i}', True)
            pt = ((f - 680 + i * 11) % 44) / 44.0
            side = -1.0 if (i % 2 == 0) else 1.0
            px = 50.76 + side * (0.34 + 0.22 * pt) + 0.04 * math.sin(pt * math.tau + i)
            py = 21.25 - 1.15 * pt
            pz = 1.72 - 0.42 * pt + 0.08 * math.sin(pt * math.pi + i)
            pq = Quaternion((0.35, 0.55, 0.72), pt * 4.2 + i * 0.7)
            move_world(f'CalendarPage{i}', (px, py, pz), pq)

    elif name == '3A-1':
        # 3A-1 (f792-885): Tight chest-up close-up on char_judge glaring furiously over spectacles (V-brows + talkAt) and raising 3D wooden gavel high above shoulder!
        set_active('SET_COURTROOM')
        vis('CourtGavel', True)
        vis('GavelShockRing', False)
        camera(lerp((100.05, -1.25, 1.98), (100.05, -0.72, 2.00), u), (100.02, 1.38, 1.88), (100.00, 1.38, 2.02), 58, fstop=2.2)
        raise_u = ramp(f, 795, 860)
        gavel_hand = V((100.38, 0.96, 1.72 + 0.22 * raise_u))
        jg = actor('judge', (100.00, 1.38, 0.34), 'angry', 'desk', f, seated=True, spoken=True, targets=[None, gavel_hand])
        gq = jg['q'] @ Quaternion((1, 0, 0), math.radians(-58 - 28 * raise_u))
        grip_prop('CourtGavel', 'GavelGrip', jg['hands'][1], gq, 'gavel_grip_error_m')

    elif name == '3A-2':
        # 3A-2 (f885-981): Macro Insert on Gavel & Warrant: gavel slams down at high speed (f895) onto sound block with finite 6-frame camera impact shake + expanding golden shockwave ring!
        set_active('SET_COURTROOM')
        vis('CourtGavel', True)
        vis('WarrantScroll', True)
        if f < 895:
            slam = ramp(f, 885, 895)
            gz = 1.94 - 0.43 * slam
            gpitch = -86 + 86 * slam
        elif f <= 912:
            gz = 1.51
            gpitch = 0.0
        else:
            rec = ramp(f, 912, 940)
            gz = 1.51 + 0.12 * rec
            gpitch = -22 * rec

        shake_z = 0.045 * math.sin((f - 895) * 2.6) * math.exp(-(f - 895) * 0.45) if 895 <= f <= 901 else 0.0
        shake_x = 0.028 * math.cos((f - 895) * 3.1) * math.exp(-(f - 895) * 0.45) if 895 <= f <= 901 else 0.0
        cam_p = lerp((100.12, -0.88, 1.78), (100.10, -0.52, 1.74), u) + V((shake_x, 0.0, shake_z))
        camera(cam_p, (100.04 + shake_x * 0.5, 0.85, 1.54 + shake_z * 0.5), (100.08, 0.82, 1.52), 55, fstop=2.2)

        gavel_hand = V((100.36, 0.64 + 0.18 * math.cos(math.radians(gpitch)), gz - 0.18 * math.sin(math.radians(gpitch))))
        warrant_hand = V((99.72, 0.86, 1.62 + 0.12 * ramp(f, 902, 935)))
        jg = actor('judge', (100.00, 1.38, 0.34), 'angry', 'desk', f, seated=True, spoken=True, targets=[warrant_hand, gavel_hand])
        gq = jg['q'] @ Quaternion((1, 0, 0), math.radians(gpitch))
        grip_prop('CourtGavel', 'GavelGrip', jg['hands'][1], gq, 'gavel_grip_error_m')
        wq = jg['q'] @ Quaternion((1, 0, 0), -math.pi / 2) @ Quaternion((0, 1, 0), math.radians(8))
        grip_prop('WarrantScroll', 'WarrantGrip', jg['hands'][0], wq, 'warrant_grip_error_m')

        if 895 <= f <= 914:
            vis('GavelShockRing', True)
            st_t = ramp(f, 895, 914)
            ring_sc = 0.65 + 1.55 * st_t
            move_world('GavelShockRing', (100.36, 0.82, 1.42)).scale = (ring_sc, ring_sc, 1.0)
        seal_pulse = 1.0 + 0.36 * math.sin(math.pi * ramp(f, 895, 912)) if 895 <= f <= 912 else 1.0
        O['Bench wax seal'].scale = (0.068 * seal_pulse, 0.068 * seal_pulse, 0.022 * seal_pulse)

    elif name == '3B':
        # 3B (f981-1095): Dynamic low-angle tracking shot as char_farmer and char_bailiff stride briskly toward camera (12cm foot lift + +/-28 deg arm swing!)
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 22.0, 0.0))
        spin_train_wheels(22.0)
        O['Loco headlight glow'].data.energy = 0.0
        walk_t = (f - 981) / (1095 - 981)
        walk_phase = (f - 1035) * 0.26 + math.pi / 2.0
        fy = -5.20 + 3.20 * walk_t
        by = -5.45 + 3.20 * walk_t
        cam_p = lerp((-1.25, -8.35, 1.08), (-1.22, -4.65, 1.12), u)
        cam_t = V((-1.32, fy, 1.02))
        camera(cam_p, cam_t, (-1.32, fy, 1.15), 42, fstop=2.6)
        actor('farmer', (-1.68, fy, 0.0), 'smirk', 'rest', f, spoken=True, walk_phase=walk_phase, walk_dir=(0, -1, 0))
        bh_r = V((-0.78, by - 0.24, 1.12 + 0.03 * math.sin(walk_phase)))
        bl = actor('bailiff', (-0.98, by, 0.0), 'neutral', 'rest', f, spoken=False, targets=[None, bh_r], walk_phase=walk_phase + math.pi, walk_dir=(0, -1, 0))
        vis('WarrantScroll', True)
        wq = bl['q'] @ Quaternion((1, 0, 0), -math.pi / 2)
        grip_prop('WarrantScroll', 'WarrantGrip', bl['hands'][1], wq, 'warrant_grip_error_m')

    elif name == '3C-1':
        # 3C-1 (f1095-1165): Fast angled platform shot as 3D 12029 Swarna Shatabdi Express rushes in at high speed (Y from +18m to +1.5m) & brakes hard with camera jolt + translucent steam!
        set_active('SET_STATION')
        train_y = 18.0 * (1.0 - u) + 1.50 * u
        move('TrainRoot', (0.98, train_y, 0.0))
        spin_train_wheels(train_y)
        O['Loco headlight glow'].data.energy = 85.0
        jolt_z = 0.032 * math.sin((f - 1148) * 2.5) * math.exp(-(f - 1148) * 0.35) if f >= 1148 else 0.0
        cam_p = lerp((-1.15, -7.85, 1.24), (-0.95, -6.45, 1.28), u) + V((0.0, 0.0, jolt_z))
        camera(cam_p, (0.15, -1.10, 1.38 + jolt_z * 0.5), (-0.65, -1.65, 1.40), 35, fstop=2.8)
        actor('farmer', (-1.58, -1.85, 0.0), 'smirk', 'rest', f, spoken=True)
        bh_r = V((-0.62, -1.38, 1.18))
        bl = actor('bailiff', (-0.82, -1.55, 0.0), 'neutral', 'rest', f, spoken=False, targets=[None, bh_r])
        vis('WarrantScroll', True)
        wq = bl['q'] @ Quaternion((1, 0, 0), -math.pi / 2)
        grip_prop('WarrantScroll', 'WarrantGrip', bl['hands'][1], wq, 'warrant_grip_error_m')
        if f >= 1135:
            cq = S.camera.matrix_world.to_quaternion()
            for i in range(6):
                t = ((f - 1135 + i * 5) % 28) / 28.0
                st = O[f'Steam{i:02d}']
                st.hide_render = False
                st.rotation_mode = 'QUATERNION'
                st.rotation_quaternion = cq
                st.location = (-0.18 - 0.25 * t, train_y - 2.4 + i * 0.65, 0.08 + t * 0.55)
                sc = 0.65 + 0.75 * t
                st.scale = (sc, sc, sc)

    elif name == '3C-2':
        # 3C-2 (f1165-1221): Tight two-shot of char_farmer and char_bailiff stepping right up to stopped locomotive cab door and raising Warrant scroll (ZERO steam balls by knee!)
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.50, 0.0))
        spin_train_wheels(0.50)
        O['Loco headlight glow'].data.energy = 65.0
        step_phase = (f - 1165) * 0.22
        camera(lerp((-1.25, -4.95, 1.52), (-1.18, -4.25, 1.56), u), (-1.15, -1.55, 1.48), (-1.18, -1.55, 1.58), 48, fstop=2.4)
        actor('farmer', (-1.56, -1.62 + 0.18 * u, 0.0), 'smirk', 'point', f, spoken=True, walk_phase=step_phase if f < 1192 else None, walk_dir=(0, 1, 0))
        bh_r = V((-0.56, -1.42 + 0.18 * u, 1.38 + 0.12 * u))
        bl = actor('bailiff', (-0.82, -1.52 + 0.18 * u, 0.0), 'smirk', 'rest', f, spoken=False, targets=[None, bh_r], walk_phase=step_phase + math.pi if f < 1192 else None, walk_dir=(0, 1, 0))
        vis('WarrantScroll', True)
        wq = bl['q'] @ Quaternion((1, 0, 0), -math.pi / 2) @ Quaternion((0, 1, 0), math.radians(-10))
        grip_prop('WarrantScroll', 'WarrantGrip', bl['hands'][1], wq, 'warrant_grip_error_m')

    elif name == '4A-1':
        # 4A-1 (f1221-1275): Close-up on char_bailiff thrusting the red-sealed Warrant scroll up into the cab window
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.0, 0.0))
        spin_train_wheels(0.0)
        O['Loco headlight glow'].data.energy = 55.0
        camera(lerp((-2.95, -4.45, 1.62), (-2.55, -3.85, 1.66), u), (-0.65, -1.85, 1.62), (-0.95, -1.65, 1.68), 56, fstop=2.2)
        handoff = V((-0.58, -1.85, 1.54 + 0.08 * u))
        actor('farmer', (-1.88, -1.25, 0.0), 'smirk', 'point', f, spoken=True)
        bl = actor('bailiff', (-0.98, -1.58, 0.0), 'smirk', 'rest', f, spoken=False, targets=[None, handoff])
        # Loco pilot inside the cab window behind X_world=-0.24 blue locomotive wall!
        actor('loco_pilot', (0.04, -2.20, 0.12), 'shock', 'rest', f, spoken=False, mouth_state='open', hide_lower=True)
        vis('WarrantScroll', True)
        wq = bl['q'] @ Quaternion((1, 0, 0), -math.pi / 2) @ Quaternion((0, 1, 0), math.radians(-14))
        grip_prop('WarrantScroll', 'WarrantGrip', bl['hands'][1], wq, 'warrant_grip_error_m')

    elif name == '4A-2':
        # 4A-2 (f1275-1329): Tight Close-Up on char_loco_pilot INSIDE the Cab Window (lower torso & pelvis tucked INSIDE locomotive body behind blue wall!),
        # eyes bulging wide with giant open O shock mouth and flying sweat drops!
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.0, 0.0))
        spin_train_wheels(0.0)
        O['Loco headlight glow'].data.energy = 55.0
        camera(lerp((-2.35, -3.15, 1.86), (-1.92, -2.85, 1.88), u), (0.04, -2.20, 1.84), (0.04, -2.20, 1.88), 58, fstop=2.2)
        handoff = V((-0.48, -2.02, 1.62))
        bl = actor('bailiff', (-0.88, -1.62, 0.0), 'smirk', 'rest', f, spoken=False, targets=[None, handoff])
        vis('WarrantScroll', True)
        wq = bl['q'] @ Quaternion((1, 0, 0), -math.pi / 2) @ Quaternion((0, 1, 0), math.radians(-14))
        grip_prop('WarrantScroll', 'WarrantGrip', bl['hands'][1], wq, 'warrant_grip_error_m')
        lp = actor('loco_pilot', (0.04, -2.20, 0.12), 'shock', 'rest', f, spoken=False, mouth_state='open', hide_lower=True, targets=[V((-0.18, -2.48, 1.55)), V((-0.18, -1.92, 1.55))])
        attach_temple_sweat(lp, f)

    elif name == '4B':
        # 4B (f1329-1422): Heroic low-angle shot pushing in as 3D Golden Crown bounces onto locomotive roof and char_farmer places hand proudly on his train!
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.50, 0.0))
        spin_train_wheels(0.50)
        O['Loco headlight glow'].data.energy = 65.0
        camera(lerp((-2.35, -7.45, 1.20), (-1.88, -6.15, 1.28), u), (0.12, -2.40, 1.88), (-0.75, -3.25, 1.55), 36, fstop=2.6)
        touch_bumper = V((-0.34, -3.42, 1.15))
        ch = actor('farmer', (-0.78, -3.35, 0.0), 'smile', 'rest', f, spoken=True, targets=[None, touch_bumper])
        vis('WarrantScroll', True)
        wq = ch['q'] @ Quaternion((1, 0, 0), -math.pi / 2) @ Quaternion((0, 1, 0), math.radians(10))
        grip_prop('WarrantScroll', 'WarrantGrip', ch['hands'][0], wq, 'warrant_grip_error_m')
        vis('GoldCrown', True)
        pop_t = ramp(f, 1331, 1352)
        over = 1.0 + 0.16 * math.sin(math.pi * pop_t) if f < 1352 else 1.0
        crown_sc = 2.10 * (0.25 + 0.75 * pop_t) * over
        crown = move_world('GoldCrown', (0.62, -2.45, 2.94 + 0.55 * (1.0 - pop_t)), Quaternion((0, 0, 1), math.radians(18)))
        crown.scale = (crown_sc, crown_sc, crown_sc)

    elif name == '4C-1':
        # 4C-1 (f1422-1505): Medium close-up on 3D blue passenger coach windows as passengers look out worriedly (gridded teeth), then smile in relief!
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.50, 0.0))
        spin_train_wheels(0.50)
        O['Loco headlight glow'].data.energy = 65.0
        camera(lerp((-2.45, 5.15, 1.88), (-1.95, 5.65, 1.90), u), (-0.24, 7.55, 1.90), (-0.24, 7.45, 1.90), 52, fstop=2.4)
        p_mode = 'worry' if f < 1464 else 'smile'
        for p_i, pc in enumerate(PASSENGER_CARDS):
            material(pc.name, f'passenger_{p_i}_{p_mode}')
        wave = math.sin((f - 1422) * 0.26) * 0.35
        flag_hand = V((-1.42, 2.75, 1.48 + 0.08 * math.sin((f - 1422) * 0.26)))
        ch = actor('farmer', (-1.78, 2.80, 0.0), 'smile', 'hero_hip', f, spoken=True, targets=[None, flag_hand])
        vis('GreenFlag', True)
        fq = Quaternion((0, 0, 1), math.atan2((ch['q'] @ V((1, 0, 0))).y, (ch['q'] @ V((1, 0, 0))).x)) @ Quaternion((0, 1, 0), wave)
        grip_prop('GreenFlag', 'FlagGrip', ch['hands'][1], fq, 'flag_grip_error_m')

    elif name == '4C-2':
        # 4C-2 (f1505-1585): Tight chest-up close-up on char_farmer smiling warmly and waving the 3D Green Signal Flag vigorously back and forth!
        set_active('SET_STATION')
        move('TrainRoot', (0.98, 0.50, 0.0))
        spin_train_wheels(0.50)
        O['Loco headlight glow'].data.energy = 65.0
        camera(lerp((-1.48, -4.15, 1.66), (-1.44, -3.62, 1.68), u), (-1.38, -1.55, 1.58), (-1.45, -1.55, 1.72), 58, fstop=2.2)
        wave = math.sin((f - 1505) * 0.34) * 0.44
        flag_hand = V((-1.02 + 0.08 * math.sin((f - 1505) * 0.34), -1.52, 1.46 + 0.09 * math.cos((f - 1505) * 0.34)))
        ch = actor('farmer', (-1.45, -1.55, 0.0), 'smile', 'hero_hip', f, spoken=True, targets=[None, flag_hand])
        vis('GreenFlag', True)
        fq = Quaternion((0, 0, 1), math.atan2((ch['q'] @ V((1, 0, 0))).y, (ch['q'] @ V((1, 0, 0))).x)) @ Quaternion((0, 1, 0), wave)
        grip_prop('GreenFlag', 'FlagGrip', ch['hands'][1], fq, 'flag_grip_error_m')

    elif name == '4C-3':
        # 4C-3 (f1585-1668): Wide heroic platform shot as Shatabdi Express glides forward with soft translucent Alpha=0.25 steam puffs
        # and camera settles into the exact Cut 1A-1 framing for a seamless loop!
        set_active('SET_STATION')
        O['Loco headlight glow'].data.energy = 65.0
        train_y = 0.50 - 7.20 * math.sin(u * math.pi * 0.5) if f < 1645 else 0.50
        move('TrainRoot', (0.98, train_y, 0.0))
        spin_train_wheels(train_y)
        camera(lerp((-2.35, -7.25, 1.38), (-1.95, -5.85, 1.25), u), (-0.08, -0.85, 1.44), (-0.98, -1.55, 1.55), 38, fstop=2.8)
        wave = math.sin((f - 1585) * 0.26) * 0.30
        flag_hand = V((-0.62, -1.52, 1.44 + 0.06 * math.sin((f - 1585) * 0.26)))
        ch = actor('farmer', (-0.98, -1.55, 0.0), 'smile', 'hero_hip', f, spoken=True, targets=[None, flag_hand])
        vis('GreenFlag', True)
        fq = Quaternion((0, 0, 1), math.atan2((ch['q'] @ V((1, 0, 0))).y, (ch['q'] @ V((1, 0, 0))).x)) @ Quaternion((0, 1, 0), wave)
        grip_prop('GreenFlag', 'FlagGrip', ch['hands'][1], fq, 'flag_grip_error_m')
        cq = S.camera.matrix_world.to_quaternion()
        for i in range(6):
            t = ((f - 1585 + i * 6) % 36) / 36.0
            st = O[f'Steam{i:02d}']
            st.hide_render = False
            st.rotation_mode = 'QUATERNION'
            st.rotation_quaternion = cq
            st.location = (-0.22 - 0.28 * t, train_y - 2.0 + i * 0.75, 0.10 + t * 0.58)
            sc = 0.55 + 0.65 * t
            st.scale = (sc, sc, sc)

    for pc in PASSENGER_CARDS:
        pc.hide_render = not name.startswith('4C')

    bpy.context.view_layer.update()
    if S.get('set_ink_enabled', True):
        INK.update()


for handler in list(bpy.app.handlers.frame_change_pre):
    if getattr(handler, '__name__', '') == 'update':
        bpy.app.handlers.frame_change_pre.remove(handler)
bpy.app.handlers.frame_change_pre.append(update)
update(S)
