"""Shared Blender 4.2 look development extracted from the V9–V13 work.

Import is inert. Call setup_scene() on a NEW scene or a saved working COPY.
No story coordinates, timeline length, camera path, captions or audio are assumed.
--smoke builds API fixtures only; it does NOT certify pixels or GPU performance.
See SHORTS_PIPELINE.md for the mandatory production gates.
"""
import math
import sys

try:
    import bpy
except ImportError:  # Pure framing/easing utilities are usable outside Blender.
    bpy = None

PALETTES = {
    'skin': ['#C4C8EA', '#E5E4F0', '#FDF5EF', '#FFF9F3'],
    'teal': ['#246A81', '#298E93', '#47B0AC', '#7FD4C5'],
    'red': ['#6C243B', '#A82737', '#D63240', '#EF5E56'],
    'vest': ['#594D65', '#88623E', '#BE9462', '#E1BA83'],
    'copper': ['#8C4725', '#D67A3E', '#F2A868', '#FFE2AC'],
}
NO_SHADOW_ROLES = {'ink', 'cloud', 'wisp', 'smoke', 'streak', 'horizon'}
INTERIOR_WARM_CAVERN = {
    'world_color': '#1A2238', 'world_strength': .12,
    'deep_shadow': '#22140C', 'far_mist_color': '#1A100A',
    'far_mist_start_m': 14., 'far_mist_enabled': False,
    'key_color': '#FFD488', 'practical_color': '#FFA64A',
    'key_to_fill_ratio': 7.,
    'rock': ['#2A190F', '#5C3A22', '#9C6332', '#C88945'],
    'skin': ['#A5A0B8', '#D1BCAE', '#F3DFCA', '#FFF6EC'],
    'red': ['#42191D', '#78231F', '#B82D24', '#D64A31'],
    'teal': ['#10383E', '#14595E', '#1A888B', '#45B0A7'],
    'yellow': ['#674014', '#A66B14', '#E8A620', '#FFCC57'],
}


def apply_lighting_preset(scene, preset='INTERIOR_WARM_CAVERN'):
    """Opt-in interior on a NEW scene/working copy. Outdoor defaults stay intact.

    No foreground haze: the preset disables mist compositing, uses a low dark
    world and only a restrained effect-only bloom. Story builders add motivated
    practical/spot keys after calling it. It never edits other scenes.
    """
    if preset != 'INTERIOR_WARM_CAVERN':
        raise ValueError('Unknown lighting preset: '+preset)
    spec = INTERIOR_WARM_CAVERN
    world = bpy.data.worlds.new('INTERIOR_WARM_CAVERN dark slate')
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    bg, out = nodes.new('ShaderNodeBackground'), nodes.new('ShaderNodeOutputWorld')
    bg.inputs['Color'].default_value = rgba(spec['world_color'])
    bg.inputs['Strength'].default_value = spec['world_strength']
    links.new(bg.outputs[0], out.inputs['Surface'])
    world.mist_settings.start, world.mist_settings.depth = 14., 80.
    scene.world = world
    for light in scene.objects:
        if light.get('ricks_light'):
            light.hide_render = light.hide_viewport = True
    scene.use_nodes = True
    nodes, links = scene.node_tree.nodes, scene.node_tree.links
    if len(nodes) > 2 and not scene.get('ricks_post'):
        raise ValueError('Refusing an unowned compositor; use a versioned working copy')
    nodes.clear()
    for layer in scene.view_layers:
        layer.use_pass_mist = False
        layer.use_pass_z = True
    source = nodes.new('CompositorNodeRLayers')
    glow = nodes.new('CompositorNodeGlare')
    glow.glare_type, glow.quality, glow.threshold, glow.size, glow.mix = 'FOG_GLOW', 'LOW', 1.7, 6, 1
    add = nodes.new('CompositorNodeMixRGB')
    add.blend_type, add.inputs[0].default_value = 'ADD', .035
    composite = nodes.new('CompositorNodeComposite')
    links.new(source.outputs['Image'], glow.inputs[0])
    links.new(source.outputs['Image'], add.inputs[1])
    links.new(glow.outputs[0], add.inputs[2])
    links.new(add.outputs[0], composite.inputs[0])
    scene['ricks_post'] = True
    scene['ricks_lighting_preset'] = preset
    scene['foreground_mist'] = False
    return dict(spec)


def rgba(hex_color):
    """Display sRGB hex to scene-linear RGBA, exactly once."""
    values = [int(hex_color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values)+(1.,)


def ease5(u):
    u = max(0., min(1., u))
    return u*u*u*(u*(u*6-15)+10)


def distance_for_height(height_m, screen_height_fraction, lens_mm, sensor_height=36):
    if min(height_m, screen_height_fraction, lens_mm, sensor_height) <= 0:
        raise ValueError('Framing dimensions must be positive')
    return height_m*lens_mm/(sensor_height*screen_height_fraction)


def interpolate_distance(d0, d1, u):
    """Quintic interpolation in projected size rather than world distance."""
    if min(d0, d1) <= 0:
        raise ValueError('Distances must be positive')
    e = ease5(u)
    return 1/((1-e)/d0+e/d1)


def configure_scene(scene, width=1080, height=1920, fps=30, frame_end=None, samples=32):
    if bpy.app.version[:2] != (4, 2):
        raise RuntimeError('Validated API profile requires Blender 4.2')
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.fps, scene.render.fps_base = fps, 1
    if frame_end is not None:
        scene.frame_start, scene.frame_end = 1, frame_end
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
    scene.render.use_motion_blur = False
    scene.render.use_simplify = True
    scene.render.simplify_subdivision = 2
    scene.render.simplify_subdivision_render = 2
    e = scene.eevee
    e.use_raytracing = False
    e.taa_render_samples = samples
    e.shadow_pool_size = '512'
    e.shadow_ray_count, e.shadow_step_count = 2, 6
    e.use_bokeh_jittered = False
    e.bokeh_max_size, e.bokeh_threshold = 24*width/1080, 2
    scene['ricks_pipeline'] = 1
    return scene


def _ramp(node, stops, interpolation='EASE'):
    ramp = node.color_ramp
    while len(ramp.elements) > 2:
        ramp.elements.remove(ramp.elements[-1])
    for element, (pos, color) in zip(ramp.elements, (stops[0], stops[-1])):
        element.position, element.color = pos, rgba(color)
    for pos, color in stops[1:-1]:
        ramp.elements.new(pos).color = rgba(color)
    ramp.interpolation = interpolation


def make_world(scene, actor_height=1.8):
    if actor_height <= 0:
        raise ValueError('actor_height must be positive')
    world = bpy.data.worlds.new('Ricks sky')
    world.use_nodes = True
    scene.world = world
    n, l = world.node_tree.nodes, world.node_tree.links
    n.clear()
    tex = n.new('ShaderNodeTexCoord')
    sep = n.new('ShaderNodeSeparateXYZ')
    elevation = n.new('ShaderNodeMath')
    elevation.operation = 'MULTIPLY'
    elevation.inputs[1].default_value = -1  # World Normal opposes the viewing ray.
    ramp = n.new('ShaderNodeValToRGB')
    _ramp(ramp, [(0, '#BEE1FF'), (.28, '#69BBFF'), (.72, '#2D93FB'), (1, '#1475D8')])
    bg, out = n.new('ShaderNodeBackground'), n.new('ShaderNodeOutputWorld')
    bg.inputs['Strength'].default_value = 1
    l.new(tex.outputs['Normal'], sep.inputs[0])
    l.new(sep.outputs['Z'], elevation.inputs[0])
    l.new(elevation.outputs[0], ramp.inputs[0])
    l.new(ramp.outputs[0], bg.inputs['Color'])
    l.new(bg.outputs[0], out.inputs['Surface'])
    world.mist_settings.start = 12*actor_height/1.8
    world.mist_settings.depth = 70*actor_height/1.8
    world.mist_settings.falloff = 'LINEAR'
    return world


def make_sun(scene, name, azimuth, elevation, energy, color, shadows, angle=4):
    from mathutils import Vector
    a, e = map(math.radians, (azimuth, elevation))
    to_light = Vector((math.sin(a)*math.cos(e), math.cos(a)*math.cos(e), math.sin(e)))
    data = bpy.data.lights.new(name, 'SUN')
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.rotation_euler = (-to_light).to_track_quat('-Z', 'Y').to_euler()
    data.energy, data.color, data.angle = energy, rgba(color)[:3], math.radians(angle)
    data.use_shadow = shadows
    data.use_shadow_jitter = False
    data.shadow_maximum_resolution = .025
    return obj


def install_lights(scene, key_azimuth=115, key_elevation=38, replace_existing=False):
    """Idempotent owned rig. Explicit replacement hides, never deletes, old lights."""
    foreign = [o for o in scene.objects if o.type == 'LIGHT' and not o.hide_render and not o.get('ricks_light')]
    if foreign and not replace_existing:
        raise ValueError('Existing lights: explicitly replace them in the working copy')
    for o in foreign:
        o.hide_render = o.hide_viewport = True
    for o in list(scene.objects):
        if o.get('ricks_light'):
            bpy.data.objects.remove(o, do_unlink=True)
    key = make_sun(scene, 'Ricks key', key_azimuth, key_elevation, 2.2, '#FFE4BE', True)
    fill = make_sun(scene, 'Ricks cool fill', key_azimuth-180, 70, .55, '#9BAEFF', False, 20)
    key['ricks_light'] = fill['ricks_light'] = True
    return key, fill


def clean_toon(name, palette='skin', light_min=.30, light_max=.78, stops=None):
    """Actual received light/shadow drives the ramp. Calibrate on a brim crop.

    Defaults are starting thresholds, not a substitute for the visual gate.
    Optional stops are [(normalized_position, '#sRGB'), ...].
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    n, l = mat.node_tree.nodes, mat.node_tree.links
    n.clear()
    diff = n.new('ShaderNodeBsdfDiffuse')
    diff.inputs['Color'].default_value = (1, 1, 1, 1)
    rgb, bw = n.new('ShaderNodeShaderToRGB'), n.new('ShaderNodeRGBToBW')
    remap = n.new('ShaderNodeMapRange')
    remap.name = 'Received light calibration'
    remap.clamp = True
    remap.inputs['From Min'].default_value = light_min
    remap.inputs['From Max'].default_value = light_max
    ramp = n.new('ShaderNodeValToRGB')
    _ramp(ramp, stops or list(zip([0, .28, .65, 1], PALETTES[palette])))
    em, out = n.new('ShaderNodeEmission'), n.new('ShaderNodeOutputMaterial')
    em.inputs['Strength'].default_value = 1
    for a, b in [(diff.outputs[0], rgb.inputs[0]), (rgb.outputs[0], bw.inputs[0]),
                 (bw.outputs[0], remap.inputs['Value']), (remap.outputs[0], ramp.inputs[0]),
                 (ramp.outputs[0], em.inputs['Color']), (em.outputs[0], out.inputs['Surface'])]:
        l.new(a, b)
    return mat


def protect_lower_face(material, band_start, band_end, warm='#FDF5EF'):
    """Optional V13 receiver mask in normalized Generated.Z coordinates.

    Derive band bounds from THIS head/brim, never copy Eddie coordinates.
    The upper zone still requires a real opaque shadow-casting hat brim.
    """
    if not 0 <= band_start < band_end <= 1:
        raise ValueError('Expected normalized head-local band bounds')
    n, l = material.node_tree.nodes, material.node_tree.links
    em = next(x for x in n if x.type == 'EMISSION')
    source = em.inputs['Color'].links[0].from_socket
    tex, sep = n.new('ShaderNodeTexCoord'), n.new('ShaderNodeSeparateXYZ')
    mask = n.new('ShaderNodeMapRange')
    mask.clamp = True
    mask.inputs['From Min'].default_value, mask.inputs['From Max'].default_value = band_start, band_end
    mix = n.new('ShaderNodeMixRGB')
    mix.inputs[1].default_value = rgba(warm)
    l.new(tex.outputs['Generated'], sep.inputs[0])
    l.new(sep.outputs['Z'], mask.inputs['Value'])
    l.new(mask.outputs[0], mix.inputs[0])
    l.new(source, mix.inputs[2])
    l.new(mix.outputs[0], em.inputs['Color'])


def metal(name, color, metallic=.25, roughness=.29, emission_strength=0., stylized_tint=None):
    """Principled metal; optional V13 received-light tint for RT-off copper."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = rgba(color)
    bs.inputs['Metallic'].default_value, bs.inputs['Roughness'].default_value = metallic, roughness
    bs.inputs['Specular IOR Level'].default_value = .5
    bs.inputs['Emission Color'].default_value = rgba(color)
    bs.inputs['Emission Strength'].default_value = emission_strength
    if stylized_tint is not None:
        n, l = mat.node_tree.nodes, mat.node_tree.links
        rgb = n.new('ShaderNodeShaderToRGB')
        tint = n.new('ShaderNodeVectorMath'); tint.operation = 'MULTIPLY'
        tint.inputs[1].default_value = stylized_tint
        em = n.new('ShaderNodeEmission')
        out = next(x for x in n if x.type == 'OUTPUT_MATERIAL')
        l.new(bs.outputs[0], rgb.inputs[0]); l.new(rgb.outputs[0], tint.inputs[0])
        l.new(tint.outputs[0], em.inputs['Color']); l.new(em.outputs[0], out.inputs['Surface'])
    return mat


def copper_metal(name):
    """Final V13 copper jacket treatment, without projectile geometry/coordinates."""
    return metal(name, '#E5A16B', .25, .29, emission_strength=.20, stylized_tint=(1.24, .70, .33))


def mark_role(obj, role):
    obj['ricks_role'] = role
    if role in NO_SHADOW_ROLES:
        obj.visible_shadow = False
    return obj


def enforce_shadow_policy(scene, *_):
    if not scene.get('ricks_pipeline'):
        return
    for obj in scene.objects:
        tokens = obj.name.lower().replace('_', ' ').replace('-', ' ').split()
        inferred = bool(set(tokens) & {'ink', 'outline', 'cloud', 'wisps', 'wisp', 'smoke', 'streak'})
        if obj.get('ricks_role') in NO_SHADOW_ROLES or obj.get('v7_outline') or inferred:
            obj.visible_shadow = False


def install_shadow_policy(scene):
    """Idempotent; never clears another project's handlers. Tag horizon props."""
    from bpy.app.handlers import persistent
    callback = persistent(enforce_shadow_policy)
    callback._ricks_policy = True
    for handlers in (bpy.app.handlers.frame_change_post, bpy.app.handlers.render_pre):
        for old in list(handlers):
            if getattr(old, '_ricks_policy', False):
                handlers.remove(old)
        handlers.append(callback)
    enforce_shadow_policy(scene)


def configure_camera(cam, focus, lens=50, fstop=2.8):
    cam.data.type = 'PERSP'
    cam.data.sensor_fit, cam.data.sensor_height = 'VERTICAL', 36
    cam.data.lens, cam.data.clip_start, cam.data.clip_end = lens, .05, 250
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object, cam.data.dof.aperture_fstop = focus, fstop
    cam.data.dof.aperture_blades = 0


def ink_width(camera_depth, lens_mm, pixels_at_360=2.25):
    """World-space hull thickness; sample per frame as distance/lens changes."""
    px = max(1.5, min(3., pixels_at_360))
    return max(0., camera_depth)*36/lens_mm*px/640  # 360x640 reference height.


def bake_channel(obj, data_path, index, f0, f1, v0, v1, easing=ease5):
    if f1 <= f0:
        raise ValueError('Nonempty bake range required')
    for frame in range(f0, f1+1):
        getattr(obj, data_path)[index] = v0+(v1-v0)*easing((frame-f0)/(f1-f0))
        obj.keyframe_insert(data_path=data_path, index=index, frame=frame)
    for fc in obj.animation_data.action.fcurves:
        if fc.data_path == data_path and fc.array_index == index:
            for key in fc.keyframe_points:
                if f0 <= key.co.x <= f1:
                    key.interpolation = 'LINEAR'


def align_to_velocity_tangent(obj, position_at, frame, nose_axis='Y', up_axis='Z', spin=0., fallback=None):
    """Stateless orientation. spin is radians about the LOCAL nose axis.

    position_at returns WORLD positions and must accept frame+1 even on the
    last visible frame. For a stop supply an authored arrival tangent.
    """
    from mathutils import Vector, Quaternion
    velocity = Vector(position_at(frame+1))-Vector(position_at(frame))
    if velocity.length < 1e-9:
        if fallback is None:
            raise ValueError('Stationary projectile needs an explicit arrival tangent')
        velocity = Vector(fallback)
    if velocity.length < 1e-9:
        raise ValueError('Zero fallback tangent')
    local_velocity = velocity
    if obj.parent:
        parent_basis = (obj.parent.matrix_world @ obj.matrix_parent_inverse).to_3x3()
        local_velocity = parent_basis.inverted() @ velocity
    axis = Vector((int(nose_axis[-1] == 'X'), int(nose_axis[-1] == 'Y'), int(nose_axis[-1] == 'Z')))
    if nose_axis.startswith('-'):
        axis.negate()
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = local_velocity.to_track_quat(nose_axis, up_axis) @ Quaternion(axis, spin)
    return velocity.normalized()


def install_post(scene, replace=False):
    """Explicit replacement only; refuses to erase an existing unowned graph."""
    scene.use_nodes = True
    n, l = scene.node_tree.nodes, scene.node_tree.links
    default_graph = len(n) == 2 and {x.type for x in n} == {'R_LAYERS', 'COMPOSITE'}
    if not replace and len(n) and not default_graph and not scene.get('ricks_post'):
        raise ValueError('Existing compositor: use replace=True only on a saved working copy')
    n.clear()
    for layer in scene.view_layers:
        layer.use_pass_mist = layer.use_pass_z = True
    rl = n.new('CompositorNodeRLayers')
    power = n.new('CompositorNodeMath'); power.operation = 'POWER'; power.inputs[1].default_value = 1.35
    gain = n.new('CompositorNodeMath'); gain.operation = 'MULTIPLY'; gain.inputs[1].default_value = .45
    valid = n.new('CompositorNodeMath'); valid.operation = 'LESS_THAN'; valid.inputs[1].default_value = 250
    factor = n.new('CompositorNodeMath'); factor.operation = 'MULTIPLY'
    mist = n.new('CompositorNodeMixRGB'); mist.inputs[2].default_value = rgba('#DFCEB4')
    for a, b in [(rl.outputs['Mist'], power.inputs[0]), (power.outputs[0], gain.inputs[0]),
                 (rl.outputs['Depth'], valid.inputs[0]), (valid.outputs[0], factor.inputs[0]),
                 (gain.outputs[0], factor.inputs[1]), (factor.outputs[0], mist.inputs[0]),
                 (rl.outputs['Image'], mist.inputs[1])]:
        l.new(a, b)
    glow = n.new('CompositorNodeGlare')
    glow.glare_type, glow.quality, glow.threshold, glow.size, glow.mix = 'FOG_GLOW', 'LOW', 1.3, 6, 1
    add = n.new('CompositorNodeMixRGB'); add.blend_type = 'ADD'; add.inputs[0].default_value = .08
    out = n.new('CompositorNodeComposite')
    l.new(mist.outputs[0], glow.inputs[0]); l.new(mist.outputs[0], add.inputs[1])
    l.new(glow.outputs[0], add.inputs[2]); l.new(add.outputs[0], out.inputs[0])
    scene['ricks_post'] = True


def setup_scene(scene, actor_height=1.8, replace_post=False, replace_lights=True, **settings):
    """Whole-scene baseline; by default hide old lights, preserving their data."""
    configure_scene(scene, **settings)
    make_world(scene, actor_height)
    install_lights(scene, replace_existing=replace_lights)
    install_post(scene, replace=replace_post)
    install_shadow_policy(scene)
    return scene


def smoke():
    """Construction and invariant checks only; no render or saved .blend."""
    from mathutils import Vector
    s = setup_scene(bpy.context.scene, actor_height=3.6)
    assert s.world.mist_settings.start == 24 and s.world.mist_settings.depth == 140
    for palette in PALETTES:
        m = clean_toon('Smoke '+palette, palette)
        assert any(x.type == 'MAP_RANGE' for x in m.node_tree.nodes)
    protect_lower_face(m := clean_toon('Smoke brim receiver'), .6, .61)
    copper_metal('Smoke copper'); metal('Smoke buckle', '#E9C777', .6, .18)
    focus = bpy.data.objects.new('Smoke focus', None); s.collection.objects.link(focus)
    configure_camera(s.camera, focus)
    bake_channel(s.camera, 'location', 0, 1, 10, 0, 1)
    for f in (1, 6, 10):
        align_to_velocity_tangent(focus, lambda t: (t*.1, t*t*.01, 0), f, spin=.3)
        tangent = Vector(((f+1)*.1-f*.1, ((f+1)**2-f*f)*.01, 0)).normalized()
        assert (focus.rotation_quaternion @ Vector((0, 1, 0))).dot(tangent) > .99999
    for role in NO_SHADOW_ROLES:
        mark_role(focus, role); focus.visible_shadow = True; enforce_shadow_policy(s)
        assert not focus.visible_shadow
    install_shadow_policy(s); install_lights(s); install_post(s)
    assert sum(bool(o.data.use_shadow) for o in s.objects if o.type == 'LIGHT' and o.data.type == 'SUN') == 1
    assert s.eevee.shadow_pool_size == '512' and s.eevee.taa_render_samples == 32
    assert s.camera.data.sensor_fit == 'VERTICAL' and not s.render.use_motion_blur
    assert abs(distance_for_height(1.8, .8, 50)-3.125) < 1e-9
    assert ink_width(4, 50, 100) == ink_width(4, 50, 3)
    print('RICKS_SMOKE_OK', bpy.app.version_string, 'NO_RENDER_NO_PERFORMANCE_OR_VISUAL_CERTIFICATION')


if __name__ == '__main__':
    if '--smoke' not in sys.argv:
        raise SystemExit('Import this module, or run Blender with -- --smoke')
    smoke()
