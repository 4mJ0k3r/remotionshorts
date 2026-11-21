"""Build isolated 3D sets, Shatabdi Express train, courtroom, soft grass clumps, props, 20 top HUD pills & elevator_leak_v3-grade 2.5D cast."""
import bpy
import math
import sys
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts' / 'washroom_experiment'))
sys.path.insert(0, str(ROOT / 'scripts' / 'inside_brain_dog'))
from sets import Stage, rgb
from build_inside_brain_dog import card, cel_material, image

OUT = ROOT / 'renders' / 'farmer_owns_train'
ART = OUT / 'assets'
random.seed(2017)


def sky_gradient_material(name='GoldenMorningSky'):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    em = nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 0.95
    tc = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    ramp = nodes.new('ShaderNodeValToRGB')
    elts = ramp.color_ramp.elements
    elts[0].position = 0.05
    elts[0].color = (*rgb('ffcb77'), 1.0)
    mid = elts.new(0.45)
    mid.color = (*rgb('60a5fa'), 1.0)
    elts[-1].position = 0.90
    elts[-1].color = (*rgb('1d4ed8'), 1.0)
    links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], em.inputs['Color'])
    links.new(em.outputs['Emission'], out.inputs['Surface'])
    return mat


def configure_world_sky(world):
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputWorld')
    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 0.65
    tc = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    map_range = nodes.new('ShaderNodeMapRange')
    map_range.inputs['From Min'].default_value = -0.1
    map_range.inputs['From Max'].default_value = 0.6
    ramp = nodes.new('ShaderNodeValToRGB')
    elts = ramp.color_ramp.elements
    elts[0].position = 0.0
    elts[0].color = (*rgb('ffcb77'), 1.0)
    mid = elts.new(0.45)
    mid.color = (*rgb('60a5fa'), 1.0)
    elts[-1].position = 1.0
    elts[-1].color = (*rgb('1d4ed8'), 1.0)
    links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    links.new(sep.outputs['Z'], map_range.inputs['Value'])
    links.new(map_range.outputs['Result'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bg.inputs['Color'])
    links.new(bg.outputs['Background'], out.inputs['Surface'])


def main():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    s = bpy.context.scene
    s.name = 'FarmerOwnsTrain'
    s['studio_root'] = str(ROOT)
    s.render.engine = 'BLENDER_EEVEE_NEXT'
    s.eevee.use_raytracing = False
    if hasattr(s.eevee, 'use_fast_gi'):
        s.eevee.use_fast_gi = True
    if hasattr(s.eevee, 'fast_gi_method'):
        s.eevee.fast_gi_method = 'AMBIENT_OCCLUSION_ONLY'
    s.eevee.taa_render_samples = 16
    s.render.use_simplify = True
    s.render.simplify_subdivision = 2
    s.render.resolution_x = 1080
    s.render.resolution_y = 1920
    s.render.resolution_percentage = 50
    s.render.fps = 30
    s.frame_start = 1
    s.frame_end = 1668
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGB'
    s.render.image_settings.compression = 15
    s.view_settings.view_transform = 'AgX'
    s.view_settings.look = 'AgX - Medium High Contrast'

    configure_world_sky(s.world)
    sky_mat = sky_gradient_material()

    g = Stage(s)
    m = g.mat

    def box(n, p, d, c, parent=None, ink=True, bevel=0.015, rough=0.55, metal=0.0, em=0.0):
        mat_obj = c if isinstance(c, bpy.types.Material) else m(c, metal=metal, rough=rough, em=em)
        o = g.box(n, p, d, mat_obj, parent, bevel=bevel)
        o['set_ink'] = ink
        return o

    def ball(n, p, d, c, parent=None, em=0.0, rough=0.55, metal=0.0, ink=False):
        mat_obj = c if isinstance(c, bpy.types.Material) else m(c, metal=metal, rough=rough, em=em)
        o = g.ball(n, p, d, mat_obj, parent)
        if ink:
            o['set_ink'] = True
        return o

    def rod(n, a, b, r, c, parent=None, ink=False, metal=0.0, rough=0.55, em=0.0):
        mat_obj = c if isinstance(c, bpy.types.Material) else m(c, metal=metal, rough=rough, em=em)
        o = g.rod(n, a, b, r, mat_obj, parent)
        o['set_ink'] = ink
        return o

    def cel(n, path, blended=False):
        # Exact elevator_leak_v3 Hotspot-Proof Character Shader:
        # 74% Emission Strength 1.02 + 26% Principled BSDF (Roughness=1.0, Specular=0.0)
        mat = cel_material(n, path)
        mat.use_fake_user = True
        if blended:
            mat.surface_render_method = 'BLENDED'
        for nd in mat.node_tree.nodes:
            if nd.type == 'EMISSION':
                nd.inputs[1].default_value = 1.02
            if nd.type == 'BSDF_PRINCIPLED':
                nd.inputs['Roughness'].default_value = 1.0
                if 'Specular IOR Level' in nd.inputs:
                    nd.inputs['Specular IOR Level'].default_value = 0.0
            if nd.type == 'MIX_SHADER' and not any(l.from_node.type == 'TEX_IMAGE' for l in nd.inputs[0].links):
                nd.inputs[0].default_value = 0.74
        return mat

    def pic(n, path, size, parent=None, blended=False):
        return card(g, n, *size, cel(n, ART / path, blended=blended), parent)

    def leg_curve(name, radius, mat_obj):
        data = bpy.data.curves.new(name, 'CURVE')
        data.dimensions = '3D'
        data.bevel_depth = radius
        data.bevel_resolution = 4
        data.use_fill_caps = True
        sp = data.splines.new('POLY')
        sp.points.add(24)
        data.materials.append(mat_obj)
        return g.link(name, data)

    # =========================================================================
    # SET 1: 3D INDIAN RAILWAY STATION & SWARNA SHATABDI EXPRESS (X = 0)
    # =========================================================================
    station = g.link('SET_STATION', xyz=(0, 0, 0))
    box('Platform sub slab', (-2.65, 0.0, -0.44), (4.6, 56.0, 0.84), '94a3b8', station, ink=True, bevel=0.02, rough=0.45)
    box('Platform coping edge', (-0.42, 0.0, -0.015), (0.16, 56.0, 0.05), 'e2e8f0', station, ink=True, bevel=0.008, rough=0.22)
    box('Yellow tactile safety line', (-0.64, 0.0, 0.012), (0.13, 54.0, 0.010), 'facc15', station, ink=False, bevel=0.003, rough=0.22)

    terrazzo_a = m('d8dde6', metal=0.06, rough=0.18)
    terrazzo_b = m('cfd6e2', metal=0.06, rough=0.18)
    for ix in range(4):
        tx = -4.25 + ix * 1.02
        for iy in range(-14, 16):
            ty = iy * 1.15
            tmat = terrazzo_a if (ix + iy) % 2 == 0 else terrazzo_b
            box('TerrazzoTile', (tx, ty, 0.0), (0.99, 1.12, 0.022), tmat, station, ink=False, bevel=0.008)

    box('Station back wall', (-5.85, 0.0, 2.7), (0.30, 56.0, 5.4), 'f1e9db', station, ink=False, bevel=0.0, rough=0.55)
    box('Station wall dado', (-5.68, 0.0, 0.72), (0.08, 56.0, 1.44), 'b45309', station, ink=True, bevel=0.01, rough=0.40)
    box('Station far sky dome', (1.2, 27.5, 4.2), (24.0, 0.30, 9.6), sky_mat, station, ink=False, bevel=0.0)
    box('Station near sky dome', (1.2, -27.5, 4.2), (24.0, 0.30, 9.6), sky_mat, station, ink=False, bevel=0.0)
    box('Opposite platform bank', (5.4, 0.0, 0.35), (3.4, 56.0, 2.2), 'cbd5e1', station, ink=True, bevel=0.02, rough=0.45)
    box('Opposite sky dome', (7.2, 0.0, 4.2), (0.30, 56.0, 9.6), sky_mat, station, ink=False, bevel=0.0)

    for by in [-6.0, 3.0, 12.0]:
        box('Station bench seat', (-3.55, by, 0.45), (0.55, 1.75, 0.08), 'b45309', station, ink=True, rough=0.38)
        box('Station bench back', (-3.78, by, 0.78), (0.08, 1.75, 0.45), 'b45309', station, ink=True, rough=0.38)
        for dy in [-0.72, 0.72]:
            box('Station bench leg', (-3.55, by + dy, 0.22), (0.45, 0.08, 0.44), '334155', station, ink=True)

    box('Station canopy roof', (-2.6, 1.0, 4.15), (4.6, 46.0, 0.14), '334155', station, ink=True, bevel=0.02, metal=0.35, rough=0.35)
    for cy in range(-14, 22, 6):
        box('Canopy beam', (-2.6, cy, 4.02), (4.5, 0.18, 0.18), '1e293b', station, ink=True)
        rod('Canopy steel pillar', (-3.95, cy, 0.0), (-3.95, cy, 4.05), 0.11, '64748b', station, ink=True, metal=0.65, rough=0.28)

    led_housing_mat = m('1e293b', metal=0.5, rough=0.35)
    led_panel_mat = m('fff8eb', em=3.2)
    for idx, ly in enumerate([-5.5, -1.5, 2.5, 6.5]):
        box(f'Canopy LED frame {idx}', (-1.75, ly, 4.03), (0.92, 1.35, 0.06), led_housing_mat, station, ink=True, bevel=0.01)
        box(f'Canopy LED panel {idx}', (-1.75, ly, 3.99), (0.82, 1.24, 0.02), led_panel_mat, station, ink=False, bevel=0.006)
        led_area = g.light(f'Canopy warm area {idx}', 'AREA', (-1.75, ly, 3.85), (-1.2, ly, 0.8), 180, 'fff8eb', station)
        led_area.data.size = 2.4
        led_area.data.use_shadow = False

    box('Track gravel ballast', (1.45, 0.0, -0.84), (3.8, 56.0, 0.14), '6b665e', station, ink=False, bevel=0.0, rough=0.88)
    for sy in range(-26, 27):
        box('Concrete sleeper', (0.98, sy * 0.68, -0.74), (2.25, 0.24, 0.10), '94a3b8', station, ink=False, bevel=0.008)
    for rx in [0.28, 1.68]:
        box('Steel rail', (rx, 0.0, -0.66), (0.09, 56.0, 0.10), 'cbd5e1', station, ink=True, bevel=0.006, metal=0.82, rough=0.22)

    # Station Lighting: Sun + Warm Key SPOT + Cool Rim AREA + Sky Fill AREA
    sun_st = g.light('Station sun', 'SUN', (5.5, -7.5, 5.2), (-1.5, 0.0, 0.5), 4.8, 'ffe5b4', station)
    sun_st.data.angle = math.radians(10)
    sun_st.data.use_shadow = True
    spot_st = g.light('Station key spot', 'SPOT', (-2.4, -4.8, 3.4), (-1.1, -1.6, 1.4), 320, 'fff1d0', station)
    spot_st.data.spot_size = math.radians(65)
    spot_st.data.spot_blend = 0.45
    spot_st.data.use_shadow = False
    fill_st = g.light('Station sky fill', 'AREA', (-3.2, -5.0, 3.2), (-0.5, 0.0, 1.3), 180, 'd5e9ff', station)
    fill_st.data.size = 3.6
    fill_st.data.use_shadow = False
    rim_st = g.light('Station cool rim', 'AREA', (2.8, 2.5, 3.5), (-1.0, 0.0, 1.2), 125, '60a5fa', station)
    rim_st.data.size = 3.0
    rim_st.data.use_shadow = False

    # --- DETAILED 3D SWARNA SHATABDI EXPRESS TRAIN (TrainRoot at X=0.98, Y=0, Z=0) ---
    train = g.link('TrainRoot', p=station, xyz=(0.98, 0.0, 0.0))
    blue_mat = m('1d4ed8', metal=0.28, rough=0.26)
    silver_mat = m('f1f5f9', metal=0.32, rough=0.24)
    gold_mat = m('f59e0b', metal=0.45, rough=0.24, em=0.15)
    dark_glass = m('0f172a', metal=0.15, rough=0.12)
    headlight_mat = m('fff6d1', em=5.0)
    red_light_mat = m('ef4444', em=3.2)
    steel_mat = m('475569', metal=0.72, rough=0.28)
    panto_mat = m('dc2626', metal=0.35, rough=0.35)
    wheel_mat = m('64748b', metal=0.80, rough=0.25)
    curtain_mat = m('2563eb', rough=0.70)

    loco = g.link('ShatabdiLoco', p=train, xyz=(0, 0, 0))
    box('Loco lower body', (0.0, 0.35, 0.72), (2.44, 7.2, 1.25), blue_mat, loco, ink=True, bevel=0.04)
    box('Loco upper rear', (0.0, 1.18, 2.02), (2.42, 5.50, 1.38), silver_mat, loco, ink=True, bevel=0.04)
    box('Loco upper front pier', (0.0, -3.02, 2.02), (2.42, 0.42, 1.38), silver_mat, loco, ink=True, bevel=0.04)
    box('Loco window sill', (0.0, -2.20, 1.40), (2.42, 1.24, 0.16), silver_mat, loco, ink=True, bevel=0.02)
    box('Loco window header', (0.0, -2.20, 2.50), (2.42, 1.24, 0.42), silver_mat, loco, ink=True, bevel=0.02)
    # Deep cab interior so loco_pilot can stand INSIDE the cab behind the X_local=-1.22 (X_world=-0.24) blue wall!
    box('Loco cab far wall', (0.65, -2.20, 1.88), (1.10, 1.24, 0.84), silver_mat, loco, ink=False, bevel=0.01)
    box('Cab frame top', (-1.22, -2.20, 2.30), (0.06, 1.22, 0.05), steel_mat, loco, ink=True, bevel=0.01)
    box('Cab frame bottom', (-1.22, -2.20, 1.47), (0.06, 1.22, 0.05), steel_mat, loco, ink=True, bevel=0.01)
    box('Cab frame front', (-1.22, -2.80, 1.88), (0.06, 0.05, 0.84), steel_mat, loco, ink=True, bevel=0.01)
    box('Cab frame rear', (-1.22, -1.60, 1.88), (0.06, 0.05, 0.84), steel_mat, loco, ink=True, bevel=0.01)
    box('Cab window dark backing', (-0.18, -2.20, 1.88), (0.06, 1.18, 0.82), dark_glass, loco, ink=False, bevel=0.0)
    box('Loco gold stripe', (0.0, 0.35, 1.32), (2.47, 7.22, 0.14), gold_mat, loco, ink=False, bevel=0.01)
    box('Loco roof crown', (0.0, 0.35, 2.75), (2.20, 7.0, 0.16), 'e2e8f0', loco, ink=True, bevel=0.03)

    nose_low = box('Loco nose lower', (0.0, -3.55, 0.72), (2.36, 1.30, 1.24), blue_mat, loco, ink=True, bevel=0.06)
    nose_low.rotation_euler.x = math.radians(-10)
    nose_cab = box('Loco cab front', (0.0, -3.35, 1.92), (2.34, 1.15, 1.24), silver_mat, loco, ink=True, bevel=0.06)
    nose_cab.rotation_euler.x = math.radians(-18)
    box('Loco nose gold band', (0.0, -3.62, 1.30), (2.40, 1.24, 0.14), gold_mat, loco, ink=False, bevel=0.01)
    ws = box('Loco windshield', (0.0, -3.72, 2.02), (1.92, 0.12, 0.66), dark_glass, loco, ink=True, bevel=0.02)
    ws.rotation_euler.x = math.radians(-18)
    box('Windshield center mullion', (0.0, -3.76, 2.02), (0.08, 0.14, 0.68), steel_mat, loco, ink=False, bevel=0.0)

    for hx in [-0.72, 0.72]:
        ball('Loco headlight', (hx, -4.18, 0.92), (0.14, 0.08, 0.14), headlight_mat, loco)
        ball('Loco marker light', (hx * 1.15, -4.14, 0.60), (0.07, 0.05, 0.07), red_light_mat, loco)
    ball('Loco top center headlight', (0.0, -3.52, 2.58), (0.16, 0.10, 0.12), headlight_mat, loco)
    hl_glow = g.light('Loco headlight glow', 'POINT', (0.0, -4.45, 0.92), (0, 0, 0), 55, 'fff2c2', loco)
    hl_glow.data.use_shadow = False
    box('Loco buffer beam', (0.0, -4.16, 0.22), (2.40, 0.24, 0.34), steel_mat, loco, ink=True, bevel=0.02)
    box('Loco front cowcatcher', (0.0, -4.18, -0.10), (2.20, 0.34, 0.34), '1e293b', loco, ink=True, bevel=0.02)
    box('Loco front coupler', (0.0, -4.34, 0.22), (0.28, 0.28, 0.22), steel_mat, loco, ink=True)
    for vy in [-0.4, 0.8, 2.0, 3.2]:
        box('Loco side louver', (-1.22, vy, 1.98), (0.05, 0.72, 0.65), '94a3b8', loco, ink=True, bevel=0.01)

    for py in [-1.6, 2.4]:
        box('Roof transformer housing', (0.0, py, 2.94), (1.35, 1.25, 0.24), steel_mat, loco, ink=True)
        for ix in [-0.38, 0.38]:
            rod('Panto insulator', (ix, py, 3.05), (ix, py, 3.20), 0.05, '991b1b', loco, ink=False)
    rod('Panto lower arm L', (-0.30, -1.6, 3.20), (0.0, -1.1, 3.56), 0.028, panto_mat, loco, ink=True)
    rod('Panto lower arm R', (0.30, -1.6, 3.20), (0.0, -1.1, 3.56), 0.028, panto_mat, loco, ink=True)
    rod('Panto upper arm L', (0.0, -1.1, 3.56), (-0.42, -1.6, 3.88), 0.024, panto_mat, loco, ink=True)
    rod('Panto upper arm R', (0.0, -1.1, 3.56), (0.42, -1.6, 3.88), 0.024, panto_mat, loco, ink=True)
    rod('Panto contact bow', (-0.65, -1.6, 3.88), (0.65, -1.6, 3.88), 0.026, steel_mat, loco, ink=True)

    train_wheels = []
    def add_bogies(parent_obj, y_positions):
        for by in y_positions:
            box('Bogie frame', (0.0, by, -0.22), (2.05, 2.2, 0.28), steel_mat, parent_obj, ink=True)
            for dy in [-0.72, 0.72]:
                rod('Wheel axle', (-0.82, by + dy, -0.27), (0.82, by + dy, -0.27), 0.06, steel_mat, parent_obj)
                for wx in [-0.72, 0.72]:
                    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.34, depth=0.14, location=(0, 0, 0))
                    w = bpy.context.object
                    w.name = f'TrainWheel_{len(train_wheels)}'
                    w.parent = parent_obj
                    w.location = (wx, by + dy, -0.27)
                    w.rotation_euler.y = math.pi / 2
                    w.data.materials.append(wheel_mat)
                    w['set_ink'] = True
                    train_wheels.append(w)

    add_bogies(loco, [-2.2, 2.2])

    passenger_cards = []
    for p_idx in range(3):
        cel(f'passenger_{p_idx}_worry', ART / f'passenger_{p_idx}_worry.png')
        cel(f'passenger_{p_idx}_smile', ART / f'passenger_{p_idx}_smile.png')

    for c_idx, c_y in enumerate([9.6, 20.2]):
        coach = g.link(f'ShatabdiCoach{c_idx}', p=train, xyz=(0.0, c_y, 0.0))
        box('Vestibule bellows', (0.0, -5.25, 1.35), (1.45, 0.55, 2.35), '1e293b', coach, ink=True)
        box('Coach lower body', (0.0, 0.0, 0.72), (2.44, 10.1, 1.25), blue_mat, coach, ink=True, bevel=0.03)
        box('Coach upper body', (0.0, 0.0, 2.02), (2.42, 10.1, 1.38), silver_mat, coach, ink=True, bevel=0.03)
        box('Coach gold stripe', (0.0, 0.0, 1.32), (2.47, 10.12, 0.14), gold_mat, coach, ink=False, bevel=0.01)
        box('Coach roof', (0.0, 0.0, 2.75), (2.22, 10.0, 0.16), 'e2e8f0', coach, ink=True, bevel=0.03)
        for w_idx in range(6):
            wy = -3.5 + w_idx * 1.4
            box('Window frame', (-1.215, wy, 1.92), (0.03, 0.98, 0.72), steel_mat, coach, ink=True, bevel=0.008)
            box('Window glass', (-1.232, wy, 1.92), (0.016, 0.88, 0.62), dark_glass, coach, ink=False, bevel=0.0)
            box('Window curtain', (-1.242, wy + 0.28, 1.92), (0.010, 0.22, 0.58), curtain_mat, coach, ink=False, bevel=0.0)
            if c_idx == 0 and w_idx in [0, 1, 2]:
                p_i = len(passenger_cards)
                pc = pic(f'PassengerPeek{p_i}', f'passenger_{p_i}_worry.png', (0.64, 0.64), coach)
                pc.location = (-1.252, wy - 0.05, 1.89)
                pc.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
                passenger_cards.append(pc)
        add_bogies(coach, [-3.3, 3.3])

    # =========================================================================
    # SET 2: STREET CAR-TOW & PUNJAB FARMLAND + OFFICE SET (X = 50)
    # =========================================================================
    street_farm = g.link('SET_STREET_FARM', xyz=(50.0, 0.0, 0.0))

    box('Street asphalt', (0.0, 0.0, -0.06), (13.0, 16.0, 0.12), '475569', street_farm, ink=False, bevel=0.0, rough=0.55)
    box('Street sidewalk', (0.0, 3.2, 0.06), (13.0, 3.6, 0.16), 'e2e8f0', street_farm, ink=True, bevel=0.02, rough=0.35)
    box('Street yellow curb', (0.0, 1.42, 0.07), (13.0, 0.14, 0.16), 'facc15', street_farm, ink=False, bevel=0.0)
    box('Street bank facade', (0.0, 4.9, 2.7), (13.5, 0.40, 5.4), 'f3e5d0', street_farm, ink=True, bevel=0.0, rough=0.50)
    box('Street side wall L', (-6.4, 0.0, 2.7), (0.40, 16.0, 5.4), 'e5d3b8', street_farm, ink=False, bevel=0.0)
    box('Street side wall R', (6.4, 0.0, 2.7), (0.40, 16.0, 5.4), 'e5d3b8', street_farm, ink=False, bevel=0.0)
    for wx in [-3.2, 0.0, 3.2]:
        box('Facade window frame', (wx, 4.68, 2.3), (1.35, 0.12, 1.55), '334155', street_farm, ink=True)
        box('Facade window glass', (wx, 4.65, 2.3), (1.18, 0.06, 1.38), '7dd3fc', street_farm, ink=False, em=0.25)
    rod('Streetlamp pole', (-2.4, 1.8, 0.1), (-2.4, 1.8, 3.9), 0.06, '334155', street_farm, ink=True)
    ball('Streetlamp bulb', (-2.4, 1.8, 3.95), (0.20, 0.20, 0.12), 'fef08a', street_farm, em=2.0)

    # 3D Red Hatchback Car (#e63946)
    car = g.link('RedCar', p=street_farm, xyz=(-0.6, -0.5, 0.0))
    car_red = m('e63946', metal=0.28, rough=0.22)
    chrome_mat = m('e2e8f0', metal=0.85, rough=0.20)
    box('Car lower chassis', (0.0, 0.0, 0.48), (2.45, 1.38, 0.62), car_red, car, ink=True, bevel=0.05)
    box('Car cabin greenhouse', (-0.15, 0.0, 0.98), (1.38, 1.24, 0.54), car_red, car, ink=True, bevel=0.06)
    box('Car side glass', (-0.15, 0.0, 1.00), (1.20, 1.26, 0.40), dark_glass, car, ink=False, bevel=0.01)
    box('Car front windshield', (0.56, 0.0, 0.98), (0.10, 1.12, 0.44), dark_glass, car, ink=True, bevel=0.01)
    box('Car front bumper', (1.24, 0.0, 0.30), (0.12, 1.32, 0.16), chrome_mat, car, ink=True, bevel=0.02)
    for hy in [-0.46, 0.46]:
        ball('Car headlight', (1.22, hy, 0.50), (0.06, 0.12, 0.10), headlight_mat, car)
    for wx in [-0.78, 0.78]:
        for wy in [-0.66, 0.66]:
            bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.26, depth=0.16, location=(0, 0, 0))
            cw = bpy.context.object
            cw.name = 'CarWheel'
            cw.parent = car
            cw.location = (wx, wy, 0.26)
            cw.rotation_euler.x = math.pi / 2
            cw.data.materials.append(m('1e293b', rough=0.75))
            cw['set_ink'] = True
            ball('CarHub', (wx, wy + (-0.085 if wy < 0 else 0.085), 0.26), (0.13, 0.02, 0.13), chrome_mat, car, ink=True)

    # 3D Tow Chain links ONLY (DELETED floating black box TowHitchBumper & TowHitchArm!)
    tow_chain = g.link('TowChain', p=street_farm, xyz=(0, 0, 0))
    for i in range(9):
        box(f'ChainLink{i}', (i * 0.11, 0, 0.065 * i), (0.14, 0.052, 0.052), 'e2e8f0', tow_chain, ink=True, metal=0.78, rough=0.22, bevel=0.006)
    g.link('TowGrip', p=tow_chain, xyz=(0.92, 0.0, 0.55))

    # --- Zone 2B/2C: Punjab Farmland with Soft Green/Golden Grass Clumps (ZERO orange cones!) ---
    box('Farmland green soil', (0.0, 22.0, -0.10), (16.0, 16.0, 0.20), '4d7c0f', street_farm, ink=False, bevel=0.0, rough=0.88)
    for fx in [-3.6, -2.1, -0.7, 0.8, 2.3, 3.7]:
        box('Meadow furrow strip', (fx, 23.2, 0.015), (0.95, 10.5, 0.04), '65a30d', street_farm, ink=False, bevel=0.01, rough=0.88)

    grass_colors = [m('3f6212', rough=0.85), m('4d7c0f', rough=0.85), m('65a30d', rough=0.82), m('ca8a04', rough=0.78)]
    grass_clusters = [
        (-2.6, 19.6), (-1.9, 20.2), (-1.3, 19.5), (-0.8, 20.4), (0.7, 19.6), (1.5, 20.1), (2.4, 19.7),
        (-2.8, 21.8), (-2.0, 22.4), (-1.2, 23.1), (-0.4, 23.6), (0.5, 23.4), (1.7, 23.2), (2.6, 22.6),
        (-2.5, 26.8), (-1.4, 27.1), (-0.2, 26.9), (1.0, 27.2), (2.2, 26.8),
    ]
    for c_i, (cx, cy) in enumerate(grass_clusters):
        for s_i in range(6):
            ang = s_i * math.tau / 6 + c_i * 0.45
            ox = cx + 0.12 * math.cos(ang)
            oy = cy + 0.12 * math.sin(ang)
            dx = 0.16 * math.cos(ang)
            dy = 0.16 * math.sin(ang)
            h_blade = 0.24 + 0.06 * ((c_i + s_i) % 3)
            pts = [
                (ox, oy, 0.0),
                (ox + dx * 0.35, oy + dy * 0.35, h_blade * 0.55),
                (ox + dx * 0.80, oy + dy * 0.80, h_blade * 0.92),
                (ox + dx * 1.15, oy + dy * 1.15, h_blade * 0.78),
            ]
            blade = g.curve(f'GrassBlade_{c_i}_{s_i}', pts, 0.016, grass_colors[(c_i + s_i) % len(grass_colors)], street_farm)
            blade['set_ink'] = False

    box('Farmland railway embankment', (0.0, 25.2, 0.08), (15.0, 1.9, 0.28), '78716c', street_farm, ink=True, bevel=0.03, rough=0.82)
    for rx in range(-12, 13):
        box('Farm sleeper', (rx * 0.55, 25.2, 0.22), (0.22, 1.35, 0.08), '57534e', street_farm, ink=False, bevel=0.0)
    for ry in [24.75, 25.65]:
        box('Farm steel rail', (0.0, ry, 0.28), (15.0, 0.08, 0.09), 'cbd5e1', street_farm, ink=True, metal=0.78, rough=0.25)
    box('Farmland sky backdrop', (0.0, 29.8, 3.8), (22.0, 0.30, 8.6), sky_mat, street_farm, ink=False, bevel=0.0)

    desk = g.link('OfficeDesk', p=street_farm, xyz=(0.78, 21.6, 0.0))
    box('Desk mahogany top', (0.0, 0.0, 0.78), (1.35, 0.75, 0.09), '7f4f24', desk, ink=True, bevel=0.02, rough=0.38)
    for dx in [-0.56, 0.56]:
        for dy in [-0.28, 0.28]:
            box('Desk leg', (dx, dy, 0.37), (0.07, 0.07, 0.74), '4a2c12', desk, ink=True)
    box('Desk ledger', (-0.25, -0.05, 0.85), (0.36, 0.28, 0.05), '1e3a8a', desk, ink=True)
    box('Desk brass stamp', (0.22, -0.10, 0.87), (0.10, 0.10, 0.09), 'd97706', desk, ink=True, metal=0.7)

    for i in range(8):
        pg = g.link(f'CalendarPage{i}', p=street_farm)
        box(f'PageSheet{i}', (0, 0, 0), (0.20, 0.012, 0.25), 'ffffff', pg, ink=True, bevel=0.002)
        box(f'PageTopBand{i}', (0, -0.007, 0.09), (0.18, 0.004, 0.040), 'dc2626', pg, ink=False, bevel=0.0)
        for ln in range(3):
            box(f'PageLine{i}_{ln}', (0, -0.007, 0.02 - ln * 0.042), (0.14, 0.003, 0.010), 'cbd5e1', pg, ink=False, bevel=0.0)

    sun_sf = g.light('StreetFarm sun', 'SUN', (45.0, -4.0, 9.5), (50.0, 2.0, 0.0), 4.5, 'ffe5b4', street_farm)
    sun_sf.data.angle = math.radians(10)
    sun_sf.data.use_shadow = True
    spot_sf = g.light('StreetFarm key spot', 'SPOT', (48.5, -2.8, 3.6), (49.5, 0.4, 1.4), 320, 'fff1d0', street_farm)
    spot_sf.data.spot_size = math.radians(65)
    spot_sf.data.spot_blend = 0.45
    spot_sf.data.use_shadow = False
    fill_sf = g.light('StreetFarm fill', 'AREA', (50.0, -2.5, 4.5), (50.0, 1.5, 1.0), 220, 'd5e9ff', street_farm)
    fill_sf.data.size = 4.5
    fill_sf.data.use_shadow = False
    rim_sf = g.light('StreetFarm cool rim', 'AREA', (51.8, 2.5, 3.4), (49.8, 0.5, 1.3), 120, '60a5fa', street_farm)
    rim_sf.data.size = 3.0
    rim_sf.data.use_shadow = False
    front_sf = g.light('StreetFarm front bounce', 'AREA', (49.5, 18.2, 3.2), (49.8, 22.0, 1.2), 210, 'fff3d6', street_farm)
    front_sf.data.size = 3.5
    front_sf.data.use_shadow = False

    # =========================================================================
    # SET 3: 3D LUDHIANA COURTROOM SET (X = 100)
    # =========================================================================
    court = g.link('SET_COURTROOM', xyz=(100.0, 0.0, 0.0))
    box('Courtroom parquet floor', (0.0, 0.0, -0.06), (8.4, 9.6, 0.12), '8d5b36', court, ink=False, bevel=0.0, rough=0.32)
    box('Courtroom back wall', (0.0, 3.2, 2.7), (8.4, 0.25, 5.6), '5c3a21', court, ink=False, bevel=0.0, rough=0.42)
    for px in [-2.7, -1.35, 0.0, 1.35, 2.7]:
        box('Mahogany wall panel', (px, 3.04, 2.35), (1.12, 0.06, 3.20), '7f4f24', court, ink=True, bevel=0.015, rough=0.36)
        box('Mahogany panel inset', (px, 3.00, 2.35), (0.88, 0.04, 2.75), '663c18', court, ink=True, bevel=0.01, rough=0.38)
    box('Courtroom cornice', (0.0, 3.00, 4.10), (8.2, 0.16, 0.22), '4a2c12', court, ink=True, bevel=0.02)

    for sx in [-4.0, 4.0]:
        box('Courtroom side wall', (sx, 0.0, 2.7), (0.25, 9.6, 5.6), '663c18', court, ink=False, bevel=0.0, rough=0.45)
        box('Courtroom side wainscot', (sx - math.copysign(0.13, sx), 0.0, 0.90), (0.06, 9.4, 1.80), '4a2c12', court, ink=True)
    for p_x in [-2.4, 2.4]:
        rod('Courtroom classical column', (p_x, 2.85, 0.0), (p_x, 2.85, 4.2), 0.18, 'f5ebe0', court, ink=True, rough=0.35)
        box('Column capital', (p_x, 2.85, 4.15), (0.50, 0.50, 0.20), 'e5d3b8', court, ink=True)
        box('Column base', (p_x, 2.85, 0.12), (0.50, 0.50, 0.24), 'e5d3b8', court, ink=True)

    box('Judge dais step 1', (0.0, 1.4, 0.12), (4.6, 2.8, 0.24), '7f4f24', court, ink=True, bevel=0.02)
    box('Judge dais step 2', (0.0, 1.6, 0.34), (4.0, 2.3, 0.22), '9c6644', court, ink=True, bevel=0.02)
    box('Judge bench body', (0.0, 0.95, 0.88), (2.9, 0.85, 0.92), '7f4f24', court, ink=True, bevel=0.03, rough=0.34)
    box('Judge bench front panel', (0.0, 0.51, 0.88), (2.5, 0.06, 0.72), '9c6644', court, ink=True, bevel=0.02)
    box('Judge bench gold trim', (0.0, 0.49, 1.28), (2.75, 0.08, 0.08), gold_mat, court, ink=False, bevel=0.01)
    box('Judge bench top', (0.0, 0.95, 1.36), (3.08, 0.96, 0.08), '582f0e', court, ink=True, bevel=0.02, rough=0.28)
    for rx in [-2.1, 2.1]:
        box('Witness railing post', (rx, -0.35, 0.48), (0.14, 0.14, 0.96), '582f0e', court, ink=True)
    box('Witness railing bar', (-1.45, -0.35, 0.92), (1.35, 0.10, 0.08), '582f0e', court, ink=True)
    box('Witness railing bar R', (1.45, -0.35, 0.92), (1.35, 0.10, 0.08), '582f0e', court, ink=True)

    scales = g.link('JusticeScales', p=court, xyz=(-0.82, 0.82, 1.40))
    ball('Scale base', (0, 0, 0.03), (0.11, 0.11, 0.03), gold_mat, scales, ink=True)
    rod('Scale pillar', (0, 0, 0.04), (0, 0, 0.42), 0.020, gold_mat, scales, ink=True)
    rod('Scale crossbar', (-0.20, 0, 0.40), (0.20, 0, 0.40), 0.015, gold_mat, scales, ink=True)
    for sx in [-0.18, 0.18]:
        rod('Scale chain', (sx, 0, 0.40), (sx, 0, 0.22), 0.006, gold_mat, scales)
        ball('Scale pan', (sx, 0, 0.21), (0.085, 0.085, 0.020), gold_mat, scales, ink=True)

    # Large 3D Gavel, Sound Block, Shockwave Ring & Bench Warrant Scroll
    ball('Gavel sound block', (0.36, 0.82, 1.42), (0.14, 0.14, 0.040), '4a2511', court, ink=True, rough=0.35)
    gavel = g.link('CourtGavel', p=court, xyz=(0.36, 0.82, 1.50))
    rod('Gavel handle', (0, -0.26, 0), (0, 0.06, 0), 0.022, 'b45309', gavel, ink=True, rough=0.35)
    rod('Gavel mallet head', (-0.11, 0.06, 0), (0.11, 0.06, 0), 0.056, '78350f', gavel, ink=True, rough=0.32)
    rod('Gavel gold band', (-0.025, 0.06, 0), (0.025, 0.06, 0), 0.059, gold_mat, gavel, ink=False)
    g.link('GavelGrip', p=gavel, xyz=(0, -0.18, 0))

    shock_ring = g.link('GavelShockRing', p=court, xyz=(0.36, 0.82, 1.41))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.18, minor_radius=0.016, major_segments=32, minor_segments=12, location=(0, 0, 0))
    s_torus = bpy.context.object
    s_torus.name = 'GavelShockTorus'
    s_torus.parent = shock_ring
    s_torus.data.materials.append(m('fbbf24', em=2.6))

    bench_warrant = g.link('BenchWarrant', p=court, xyz=(-0.22, 0.78, 1.41))
    box('Bench parchment', (0, 0, 0), (0.44, 0.32, 0.018), 'fffdf7', bench_warrant, ink=True, bevel=0.004)
    ball('Bench wax seal', (0.10, -0.06, 0.015), (0.068, 0.068, 0.022), m('dc2626', em=1.8), bench_warrant)

    sun_ct = g.light('Courtroom sun', 'SUN', (95.0, -3.0, 6.5), (100.0, 1.0, 1.4), 4.2, 'ffe4b5', court)
    sun_ct.data.angle = math.radians(10)
    sun_ct.data.use_shadow = True
    spot_ct = g.light('Courtroom key spot', 'SPOT', (99.4, -1.6, 3.5), (100.0, 1.2, 1.7), 320, 'fff1d0', court)
    spot_ct.data.spot_size = math.radians(62)
    spot_ct.data.spot_blend = 0.45
    spot_ct.data.use_shadow = False
    key_ct = g.light('Courtroom overhead', 'AREA', (100.0, -0.6, 3.6), (100.0, 1.2, 1.5), 280, 'fff3d6', court)
    key_ct.data.size = 2.6
    key_ct.data.use_shadow = False
    rim_ct = g.light('Courtroom azure rim', 'AREA', (101.6, 2.2, 2.9), (100.0, 1.2, 1.6), 120, '60a5fa', court)
    rim_ct.data.size = 2.0
    rim_ct.data.use_shadow = False

    # =========================================================================
    # PORTABLE & STORY PROPS
    # =========================================================================
    warrant = g.link('WarrantScroll')
    box('Warrant paper', (0, 0, 0.14), (0.28, 0.018, 0.34), 'fffdf7', warrant, ink=True, bevel=0.004)
    rod('Warrant bottom roll', (-0.15, 0, -0.02), (0.15, 0, -0.02), 0.028, 'f5e6c8', warrant, ink=True)
    rod('Warrant top roll', (-0.15, 0, 0.31), (0.15, 0, 0.31), 0.025, 'f5e6c8', warrant, ink=True)
    ball('Warrant red seal', (0.06, -0.015, 0.08), (0.052, 0.018, 0.052), 'dc2626', warrant, em=0.85, ink=True)
    box('Warrant ribbon', (0.06, -0.012, 0.03), (0.024, 0.010, 0.09), 'b91c1c', warrant, ink=False, bevel=0.0)
    g.link('WarrantGrip', p=warrant, xyz=(0.0, 0.0, -0.02))

    coin_group = g.link('GoldCoin')
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.16, depth=0.036, location=(0, 0, 0))
    c_mesh = bpy.context.object
    c_mesh.name = 'CoinDisc'
    c_mesh.parent = coin_group
    c_mesh.rotation_euler.x = math.pi / 2
    c_mesh.data.materials.append(m('f59e0b', metal=0.65, rough=0.22, em=0.45))
    c_mesh['set_ink'] = True
    # Raised Rupee relief bars on coin face
    box('CoinRupeeTop', (0.0, -0.020, 0.055), (0.11, 0.008, 0.018), 'fef08a', coin_group, ink=False, em=0.6)
    box('CoinRupeeMid', (0.0, -0.020, 0.022), (0.11, 0.008, 0.016), 'fef08a', coin_group, ink=False, em=0.6)
    box('CoinRupeeDiag', (0.01, -0.020, -0.032), (0.020, 0.008, 0.095), 'fef08a', coin_group, ink=False, em=0.6)

    ban = g.link('BanRing')
    bpy.ops.mesh.primitive_torus_add(major_radius=0.24, minor_radius=0.034, major_segments=32, minor_segments=12, location=(0, 0, 0))
    ring = bpy.context.object
    ring.name = 'ProhibitionTorus'
    ring.parent = ban
    ring.rotation_euler.x = math.pi / 2
    ring.data.materials.append(m('ef4444', em=0.95))
    rod('ProhibitionBar', (-0.165, -0.01, 0.165), (0.165, -0.01, -0.165), 0.030, 'ef4444', ban, em=0.95)

    arrows = g.link('ReverseArrows')
    arrow_mat = m('fbbf24', metal=0.45, rough=0.22, em=1.45)
    for a_idx, offset_angle in enumerate([0, math.pi]):
        pts = []
        for i in range(18):
            ang = offset_angle + i * (math.pi * 0.72) / 17
            pts.append((0.48 * math.cos(ang), 0.48 * math.sin(ang), 0.06 * math.sin(ang * 2)))
        g.curve(f'ReverseArc{a_idx}', pts, 0.034, arrow_mat, arrows)
        tip_ang = offset_angle + math.pi * 0.72
        tip_pos = (0.48 * math.cos(tip_ang), 0.48 * math.sin(tip_ang), 0.06 * math.sin(tip_ang * 2))
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.075, depth=0.15, location=(0, 0, 0))
        cone = bpy.context.object
        cone.name = f'ArrowHead{a_idx}'
        cone.parent = arrows
        cone.location = tip_pos
        tangent = Vector((-math.sin(tip_ang), math.cos(tip_ang), 0.12 * math.cos(tip_ang * 2))).normalized()
        cone.rotation_euler = tangent.to_track_quat('Z', 'Y').to_euler()
        cone.data.materials.append(arrow_mat)

    bag = g.link('EmptyBag')
    burlap_mat = m('b08968', rough=0.90)
    ball('EmptyBagPouch', (0, 0, -0.15), (0.135, 0.065, 0.165), burlap_mat, bag, ink=True)
    rod('EmptyBagNeck', (0, 0, -0.02), (0, 0, 0.04), 0.042, '7f5539', bag, ink=True, rough=0.88)
    bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=0.038, radius2=0.075, depth=0.065, location=(0, 0, 0))
    ruffle = bpy.context.object
    ruffle.name = 'EmptyBagRuffle'
    ruffle.parent = bag
    ruffle.location = (0, 0, 0.065)
    ruffle.data.materials.append(burlap_mat)
    ruffle['set_ink'] = True
    g.link('BagGrip', p=bag, xyz=(0, 0, 0.02))

    crown = g.link('GoldCrown')
    crown_mat = m('fbbf24', metal=0.80, rough=0.20, em=2.80)
    bpy.ops.mesh.primitive_cylinder_add(vertices=28, radius=0.45, depth=0.24, location=(0, 0, 0.12))
    cb = bpy.context.object
    cb.name = 'CrownBand'
    cb.parent = crown
    cb.data.materials.append(crown_mat)
    cb['set_ink'] = True
    for i in range(6):
        ang = i * math.tau / 6
        px, py = 0.41 * math.cos(ang), 0.41 * math.sin(ang)
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.13, depth=0.38, location=(0, 0, 0))
        sp = bpy.context.object
        sp.name = f'CrownSpike{i}'
        sp.parent = crown
        sp.location = (px, py, 0.39)
        sp.data.materials.append(crown_mat)
        sp['set_ink'] = True
        ball(f'CrownJewel{i}', (px, py, 0.60), (0.068, 0.068, 0.068), 'ef4444' if i % 2 == 0 else '10b981', crown, em=1.8, ink=True)

    flag = g.link('GreenFlag')
    rod('FlagStaff', (0, 0, -0.08), (0, 0, 0.44), 0.018, '78350f', flag, ink=True)
    box('FlagCloth', (0.16, 0.0, 0.30), (0.30, 0.014, 0.22), '16a34a', flag, ink=True, bevel=0.004, em=0.35)
    g.link('FlagGrip', p=flag, xyz=(0, 0, 0.02))

    # 6 Glossy Temple Sweat Drops + 10 Soft Translucent Alpha=0.25 Steam Puffs (ZERO solid white snowballs!)
    for i in range(6):
        ball(f'Sweat{i:02d}', (0, 0, 0), (0.016, 0.012, 0.032), '9ee9ff', rough=0.18, em=0.45)
    for i in range(10):
        pic(f'Steam{i:02d}', 'steam_puff.png', (0.48, 0.36), None, blended=True)

    # =========================================================================
    # 2.5D CAST WITH 3D TAILORED TROUSER LEGS, PELVIS & GLOSSY SHOES
    # =========================================================================
    trouser_colors = {
        'farmer': ('f1f5f9', 0.14, '2b1810'),
        'bailiff': ('8c7355', 0.10, '111317'),
        'bank_officer': ('262a30', 0.08, '111317'),
        'judge': ('181a1f', 0.06, '111317'),
        'loco_pilot': ('1e3a8a', 0.08, '111317'),
        'common_man': ('2b3a4a', 0.08, '111317'),
    }
    limb_mat = m('161219', rough=0.96)
    limb_mat.use_fake_user = True
    shadow_mat = m('11131b', rough=1.0)

    for kind in ['farmer', 'judge', 'bailiff', 'loco_pilot', 'common_man', 'bank_officer']:
        t_hex, t_em, shoe_hex = trouser_colors[kind]
        t_mat = m(t_hex, rough=0.92, em=t_em)
        t_mat.use_fake_user = True
        shoe_mat = m(shoe_hex, rough=0.20)
        shoe_mat.use_fake_user = True

        g.link(f'char_{kind}')
        pic(f'{kind}_head', f'{kind}_neutral.png', (1.00, 1.00), None)
        for exp in ['smile', 'smirk', 'wink', 'worry', 'panic', 'shock', 'angry', 'blink']:
            cel(f'{kind}_{exp}', ART / f'{kind}_{exp}.png')
        pic(f'{kind}_torso', f'body_{kind}.png', (0.58, 0.88), None)
        ball(f'{kind}_hips', (0, 0, 0.58), (0.165, 0.075, 0.095), t_mat, ink=False)
        pic(f'{kind}_mouth', 'mouth_smile_0.png', (0.24, 0.15), None)
        for side in ['L', 'R']:
            g.curve(f'{kind}_arm{side}', [(0, 0, 0)] * 25, 0.019, limb_mat)
            leg_curve(f'{kind}_leg{side}', 0.048, limb_mat)
            leg_curve(f'{kind}_trouser{side}', 0.042, t_mat)
            ball(f'{kind}_hand{side}', (0, 0, 0), (0.036, 0.025, 0.040), limb_mat)
            ball(f'{kind}_shoe{side}', (0, 0, 0.035), (0.074, 0.128, 0.048), shoe_mat, ink=False)
            ball(f'{kind}_contact{side}', (0, 0, 0.003), (0.095, 0.142, 0.003), shadow_mat, ink=False)

    for state in ['smile', 'o', 'flat', 'panic', 'open', 'smirk', 'clenched']:
        for talk_i in range(6):
            cel(f'mouth_{state}_{talk_i}', ART / f'mouth_{state}_{talk_i}.png')

    # Camera + Compositor (FOG_GLOW + HueSat + Vignette + Single Top Screen-Space HUD Pill)
    cam = g.link('StoryCamera', bpy.data.cameras.new('Story lens'))
    s.camera = cam
    cam.data.lens = 42
    cam.data.sensor_fit = 'HORIZONTAL'
    cam.data.clip_start = 0.03
    cam.data.clip_end = 180
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 2.2
    cam.data.dof.aperture_blades = 6

    # Preload 20 HUD pill images into bpy.data.images
    hud_imgs = []
    for i in range(20):
        im_hud = image(ART / f'hud_{i}.png')
        im_hud.name = f'HUD_IMG_{i}'
        im_hud.use_fake_user = True
        hud_imgs.append(im_hud)

    s.use_nodes = True
    nt = s.node_tree
    nt.nodes.clear()
    lk = nt.links
    rl = nt.nodes.new('CompositorNodeRLayers')
    gl = nt.nodes.new('CompositorNodeGlare')
    gl.glare_type = 'FOG_GLOW'
    gl.threshold = 0.80
    gl.mix = 0.18
    gl.size = 7
    lk.new(rl.outputs['Image'], gl.inputs[0])
    sat = nt.nodes.new('CompositorNodeHueSat')
    sat.inputs['Saturation'].default_value = 1.16
    lk.new(gl.outputs[0], sat.inputs['Image'])
    vi = nt.nodes.new('CompositorNodeImage')
    vi.image = image(ART / 'vignette.png')
    resize = nt.nodes.new('CompositorNodeScale')
    resize.space = 'RENDER_SIZE'
    lk.new(vi.outputs[0], resize.inputs[0])
    mul = nt.nodes.new('CompositorNodeMixRGB')
    mul.blend_type = 'MULTIPLY'
    mul.inputs[0].default_value = 1.0
    lk.new(sat.outputs[0], mul.inputs[1])
    lk.new(resize.outputs[0], mul.inputs[2])

    hud_src = nt.nodes.new('CompositorNodeImage')
    hud_src.name = 'HUD_SOURCE'
    hud_src.image = hud_imgs[0]
    hud_scale = nt.nodes.new('CompositorNodeScale')
    hud_scale.space = 'RENDER_SIZE'
    lk.new(hud_src.outputs[0], hud_scale.inputs[0])
    hud_over = nt.nodes.new('CompositorNodeAlphaOver')
    hud_over.name = 'HUD_GATE'
    hud_over.inputs[0].default_value = 1.0
    lk.new(mul.outputs[0], hud_over.inputs[1])
    lk.new(hud_scale.outputs[0], hud_over.inputs[2])

    out_node = nt.nodes.new('CompositorNodeComposite')
    lk.new(hud_over.outputs[0], out_node.inputs[0])

    for name, path in [
        ('farmer_runtime.py', Path(__file__).with_name('runtime.py')),
        ('studio_set_ink.py', ROOT / 'scripts' / 'studio' / 'set_ink.py'),
    ]:
        tx = bpy.data.texts.get(name) or bpy.data.texts.new(name)
        tx.clear()
        tx.write(path.read_text())

    s['set_ink_enabled'] = True
    s['production'] = 'farmer_owns_train V2 Overhaul; 20 rapid-fire cuts; 1668f; 30fps; elevator_leak_v3 HUD + close-ups'
    ns = {'__name__': 'farmer_runtime'}
    exec(bpy.data.texts['farmer_runtime.py'].as_string(), ns)
    s.frame_set(1)
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'farmer_owns_train.blend'))
    print('FARMER_BUILD_COMPLETE', len(s.objects), flush=True)


if __name__ == '__main__':
    main()
