"""Reusable Blender 4.2 EEVEE look and rig for the Padoda v04 Golden Master.

Import from the repository's scripts directory or as scripts.ricks_v2_kit.
The walk evaluator is also usable in ordinary Python. Scene builders require bpy.

Use configure_ricks_scene() and setup_ricks_compositor() in a new scene.
Build actors with build_ricks_character(), bake their poses, and update ink
thickness and camera focus for each shot. For the benchmark artwork, run
scripts/ricks_benchmark_10s/v01c/artwork.py with Pillow and pass its art
directory as art_dir. New shorts can supply their own packed PNG artwork.
"""

import math
from dataclasses import dataclass
from pathlib import Path

try:
    import bpy
except ModuleNotFoundError as error:
    if error.name != "bpy":
        raise
    bpy = None
else:
    from mathutils import Euler, Vector

if __package__:
    from . import ricks_lookdev as look
else:
    import ricks_lookdev as look

HEAD = (.24, .2112, .2256)
FACE_CENTER = 1.237
TORSO_CENTER = .831
RING = 48
HAIR_RADIAL_OFFSET = .008
HERO_EXPRESSIONS = ("suspicious", "excited_awe", "smug_focus", "sneaky", "shock_terror")
HOODED_EXPRESSIONS = ("broker_neutral", "broker_creepy_grin")
CREAM_FACE = "#FFF9F0"
COOL_FACE_SHADOW = "#9EB2D6"
WARM_FACE_SHADOW = "#D9B67A"
CHARACTER_INK = "#040407"
CEL_FEATHER = .04


def _two_step_stops(shadow, light, cutoff):
    if not 0 < cutoff < 1 - CEL_FEATHER:
        raise ValueError("The cel cutoff must leave room for the .04 transition.")
    return ((0, shadow), (cutoff, shadow), (cutoff + CEL_FEATHER, light), (1, light))


HERO_FACE_STOPS = _two_step_stops(COOL_FACE_SHADOW, CREAM_FACE, .28)
HOODED_FACE_STOPS = _two_step_stops("#343954", CREAM_FACE, .34)

def surface(name, color, rough=.78, metal=0., glow=0.):
    m = bpy.data.materials.new(name)
    m.diffuse_color = look.rgba(color)
    m.use_nodes = True
    b = next(node for node in m.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = m.diffuse_color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = .32
    if glow:
        b.inputs["Emission Color"].default_value = m.diffuse_color
        b.inputs["Emission Strength"].default_value = glow
    return m


def emission(name, color, strength=1):
    m = bpy.data.materials.new(name)
    m.diffuse_color = look.rgba(color)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    light, out = n.new("ShaderNodeEmission"), n.new("ShaderNodeOutputMaterial")
    light.inputs[0].default_value, light.inputs[1].default_value = m.diffuse_color, strength
    l.new(light.outputs[0], out.inputs[0])
    return m


def _make_matte(material):
    matte = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    for socket, value in (("Roughness", 1.), ("Specular IOR Level", 0.), ("Metallic", 0.)):
        matte.inputs[socket].default_value = value


def _cel_ramp(material, stops):
    nodes, links = material.node_tree.nodes, material.node_tree.links
    _make_matte(material)
    probe = nodes.new("ShaderNodeBsdfDiffuse")
    probe.label = "White matte received-light probe"
    probe.inputs["Color"].default_value = (1, 1, 1, 1)
    lit = nodes.new("ShaderNodeShaderToRGB")
    luma = nodes.new("ShaderNodeRGBToBW")
    ramp = nodes.new("ShaderNodeValToRGB")
    look._ramp(ramp, stops, "EASE")
    links.new(probe.outputs[0], lit.inputs[0])
    links.new(lit.outputs[0], luma.inputs[0])
    links.new(luma.outputs[0], ramp.inputs[0])
    return ramp.outputs[0]


def _cel_output(material, pigment, strength, alpha=None):
    nodes, links = material.node_tree.nodes, material.node_tree.links
    output = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    paint = nodes.new("ShaderNodeEmission")
    paint.label = "Graphic cel paint"
    paint.inputs["Strength"].default_value = strength
    links.new(pigment, paint.inputs["Color"])
    shader = paint.outputs[0]
    if alpha is not None:
        clear = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        links.new(alpha, mix.inputs[0])
        links.new(clear.outputs[0], mix.inputs[1])
        links.new(shader, mix.inputs[2])
        shader = mix.outputs[0]
    links.new(shader, output.inputs["Surface"])


def make_lit_cel_face_material(name, tone=None, stops=None, *, hood_shadow=False,
                               shadow=None, cutoff=None):
    """Make a light-responsive face with a tight two-step cream palette.

    Use WARM_FACE_SHADOW and cutoff=.32 for amber sets. Custom ramp stops
    remain supported. A hood keeps its geometric upper-face recess.
    """
    if tone is None:
        tone = CREAM_FACE
    if stops is None:
        if shadow is None:
            shadow = "#343954" if hood_shadow else COOL_FACE_SHADOW
        if cutoff is None:
            cutoff = .34 if hood_shadow else .28
        stops = _two_step_stops(shadow, tone, cutoff)
    m = surface(name, tone, 1.)
    n, l = m.node_tree.nodes, m.node_tree.links
    shade = _cel_ramp(m, stops)
    if hood_shadow:
        coords, axis = n.new("ShaderNodeTexCoord"), n.new("ShaderNodeSeparateXYZ")
        l.new(coords.outputs["Generated"], axis.inputs[0])
        band = n.new("ShaderNodeMapRange")
        band.interpolation_type = "SMOOTHERSTEP"
        band.inputs["From Min"].default_value, band.inputs["From Max"].default_value = .28, .52
        band.inputs["To Min"].default_value, band.inputs["To Max"].default_value = 1, .065
        l.new(axis.outputs["Z"], band.inputs["Value"])
        recess = n.new("ShaderNodeMixRGB")
        recess.inputs[1].default_value = look.rgba("#0B0D18")
        l.new(band.outputs[0], recess.inputs[0])
        l.new(shade, recess.inputs[2])
        shade = recess.outputs[0]
    _cel_output(m, shade, 1.48)
    return m


STUDIO_INK = "#161020"
STUDIO_PORTRAITS = {
    "kalam": ((.90, .88, 1.08), .0, "#E3B58A", "#B0825C", "#93929C"),
    "engineer": ((1.04, .95, .95), .25, "#DDB084", "#9A684F", "#28232B"),
    "analyst": ((1.03, .92, 1.03), .34, "#F6D9C0", "#C4A592", "#6C4739"),
}


def studio_shadow_dots(material, cutoff=.28, *, contrast=1.):
    """Darken small stylized dots in the received-light shadow only."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    light = next((n for n in nodes if n.type == "SHADERTORGB"), None)
    paint = next(n for n in nodes if n.type == "EMISSION")
    if light is None or not paint.inputs["Color"].is_linked:
        return
    source = paint.inputs["Color"].links[0].from_socket
    coords = nodes.new("ShaderNodeTexCoord")
    plane = nodes.new("ShaderNodeVectorMath")
    plane.operation = "MULTIPLY"
    plane.inputs[1].default_value = (1, 0, 1)
    dots = nodes.new("ShaderNodeTexVoronoi")
    dots.inputs["Scale"].default_value = 38
    dots.inputs["Randomness"].default_value = 0
    links.new(coords.outputs["Generated"], plane.inputs[0])
    links.new(plane.outputs["Vector"], dots.inputs["Vector"])
    dot_mask = nodes.new("ShaderNodeMath")
    dot_mask.operation = "LESS_THAN"
    dot_mask.inputs[1].default_value = .19
    links.new(dots.outputs["Distance"], dot_mask.inputs[0])
    shadow = nodes.new("ShaderNodeMapRange")
    shadow.inputs["From Min"].default_value = cutoff-.035
    shadow.inputs["From Max"].default_value = cutoff
    shadow.inputs["To Min"].default_value = 1
    shadow.inputs["To Max"].default_value = 0
    links.new(light.outputs["Color"], shadow.inputs["Value"])
    mask = nodes.new("ShaderNodeMath")
    mask.operation = "MULTIPLY"
    links.new(dot_mask.outputs[0], mask.inputs[0])
    links.new(shadow.outputs[0], mask.inputs[1])
    tint = nodes.new("ShaderNodeMixRGB")
    tint.blend_type = "MULTIPLY"
    tint.inputs[2].default_value = tuple(max(0., 1.-contrast*drop) for drop in (.19,.26,.21)) + (1.,)
    links.new(mask.outputs[0], tint.inputs[0])
    links.new(source, tint.inputs[1])
    links.new(tint.outputs[0], paint.inputs["Color"])


def build_studio_character(name, collection, *, portrait, costume_image=None, expression_images=None,
                           skin=None, dot_contrast=1.):
    """Opt-in espresso-ink portrait. Existing Rick's characters keep their defaults."""
    scale, jaw, lit, shade, hair_color = STUDIO_PORTRAITS[portrait]
    rig = build_ricks_character(name, collection, costume_image=costume_image,
                                expression_images=expression_images)
    face = bpy.data.objects[name + " | ellipsoid head"]
    hair = bpy.data.objects[name + " | shaped hair cap"]
    skin_material = make_lit_cel_face_material(name + " painted portrait", tone=skin or lit, shadow=shade)
    studio_shadow_dots(skin_material, contrast=dot_contrast)
    face.data.materials[0] = skin_material
    hair.data.materials[0] = make_cel_character_material(name + " portrait hair", hair_color)
    ink = bpy.data.materials.get("Studio | espresso hull")
    if ink is None:
        ink = emission("Studio | espresso hull", STUDIO_INK)
        ink.use_backface_culling = True
    limb_ink = emission(name + " tapered espresso limbs", STUDIO_INK)
    for modifier in rig.ink_modifiers:
        modifier.id_data.data.materials[0] = ink
    for arm in (*rig.arms, *rig.legs, *rig.feet):
        arm.data.materials[0] = limb_ink
        if arm.type == "CURVE":
            for i, point in enumerate(arm.data.splines[0].bezier_points):
                point.radius = min(point.radius, 1.05-.14*i)
    highlight = make_cel_character_material(name + " hair sheen", "#CFCCD0" if portrait=="kalam" else "#94705F")
    for obj in rig.head.children:
        if obj.type=="CURVE" and "highlight" in obj.name:
            obj.data.materials[0] = highlight
    for sign in (-1,1):
        ear = ball(name + " side ear", collection, (sign*.234, .008, -.030),
                   (.033,.023,.043), skin_material, rig.head, 14, 10)
        hull = apply_character_ink(ear, collection)
        hull.id_data.data.materials[0] = ink
        rig.ink_modifiers.append(hull)
        if portrait=="kalam":
            lock = ball(name+" swept silver temple lock",collection,(sign*.183,.012,.010),
                        (.057,.166,.175),hair.data.materials[0],rig.head,20,14)
            lock.rotation_euler.y = sign*-.15
            hull = apply_character_ink(lock,collection)
            hull.id_data.data.materials[0] = ink
            rig.ink_modifiers.append(hull)
    rig.head.scale = scale
    for obj in (face,*rig.expressions.values(),*(m.id_data for m in rig.ink_modifiers if m.id_data.parent==face)):
        for vertex in obj.data.vertices:
            vertex.co.x *= 1 + jaw*max(0.,-vertex.co.z/HEAD[2])
    for obj in rig.body.children:
        if obj.type=="MESH" and ("pill torso" in obj.name or "costume art" in obj.name):
            studio_shadow_dots(obj.data.materials[0], .24, contrast=dot_contrast)
    rig.studio_hands = []
    contour = [(-.028,.019),(.002,.024),(.028,.018),(.040,.005),(.036,-.013),
               (.017,-.023),(-.009,-.019),(-.020,-.008),(-.034,-.011),(-.042,-.002)]
    for sign in (-1,1):
        obj = empty(name + " flat mitten pivot", collection, parent=rig.body)
        for size, depth, material in ((1.,0.,limb_ink),(.79,-.001,skin_material)):
            points = [(x*size*sign,depth,z*size) for x,z in contour]
            layer = mesh(name+" flat thumb mitten",collection,points,[tuple(range(len(points)))],material,obj)
            layer.visible_shadow = False
        rig.studio_hands.append(obj)
    return rig


def studio_pose_hands(rig, frame=None):
    """Place the flat mittens at the baked arm tips, without adding glove volume."""
    for hand, arm in zip(rig.studio_hands, rig.arms):
        points = arm.data.splines[0].bezier_points
        hand.location = points[-1].co
        direction = points[-1].co-points[-3].co
        hand.rotation_euler.y = -math.atan2(direction.z,direction.x)
        if frame is not None:
            hand.keyframe_insert("location",frame=frame)
            hand.keyframe_insert("rotation_euler",frame=frame)


def _cel_pigment(material, pigment, *, alpha=None, lit=True):
    if lit:
        nodes, links = material.node_tree.nodes, material.node_tree.links
        bands = _cel_ramp(material, _two_step_stops("#777F9B", "#FFFFFF", .24))
        tint = nodes.new("ShaderNodeMixRGB")
        tint.blend_type = "MULTIPLY"
        tint.inputs[0].default_value = 1.
        links.new(pigment, tint.inputs[1])
        links.new(bands, tint.inputs[2])
        pigment = tint.outputs[0]
    else:
        _make_matte(material)
    _cel_output(material, pigment, 1.23 if lit else .98, alpha)
    return material


def make_cel_character_material(name, color):
    """Light-responsive matte pigment for hair, cloth and painted accessories."""
    material = surface(name, color, 1.)
    pigment = material.node_tree.nodes.new("ShaderNodeRGB")
    pigment.outputs[0].default_value = material.diffuse_color
    return _cel_pigment(material, pigment.outputs[0])


def texture(name, colors, kind, roughness=(.58, .84)):
    m = surface(name, colors[0], roughness[0])
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(node for node in n if node.type == "BSDF_PRINCIPLED")
    coord = n.new("ShaderNodeTexCoord")
    mapping = n.new("ShaderNodeVectorMath")
    mapping.operation = "MULTIPLY"
    mapping.inputs[1].default_value = {"wood": (.72, 7.4, 5.9), "asphalt": (1.5, 1.5, 1.5),
                                      "plaster": (3, 3, 3)}[kind]
    l.new(coord.outputs["Object"], mapping.inputs[0])
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 7 if kind == "wood" else 3
    noise.inputs["Detail"].default_value = 2.3
    l.new(mapping.outputs[0], noise.inputs["Vector"])
    ramp = n.new("ShaderNodeValToRGB")
    look._ramp(ramp, [(0.16, colors[0]), (.48, colors[1]), (.79, colors[2])])
    l.new(noise.outputs["Fac"], ramp.inputs[0])
    l.new(ramp.outputs[0], p.inputs["Base Color"])
    rough = n.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value, rough.inputs["To Max"].default_value = roughness
    if kind == "asphalt":
        basin = n.new("ShaderNodeTexNoise")
        basin.inputs["Scale"].default_value = 1.45
        basin.inputs["Detail"].default_value = 2
        l.new(mapping.outputs[0],basin.inputs["Vector"])
        rough.interpolation_type = "SMOOTHERSTEP"
        rough.inputs["From Min"].default_value, rough.inputs["From Max"].default_value = .46,.58
        l.new(basin.outputs["Fac"],rough.inputs["Value"])
    else:
        l.new(noise.outputs["Fac"], rough.inputs["Value"])
    l.new(rough.outputs[0], p.inputs["Roughness"])
    fine = n.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 68 if kind == "asphalt" else 15
    l.new(mapping.outputs[0], fine.inputs["Vector"])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .065 if kind == "asphalt" else .13
    bump.inputs["Distance"].default_value = .008 if kind == "asphalt" else .025
    l.new(fine.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs[0], p.inputs["Normal"])
    return m


def make_wet_puddle_material(name="Wet asphalt", colors=("#182236", "#282640", "#343248")):
    """Make v01c's procedural .04 slick puddles and .45 damp asphalt."""
    return texture(name, colors, "asphalt", roughness=(.04, .45))


def artwork(name, source, glow=.15, *, cel=None):
    """Load and pack an alpha decal. Cel mode uses lit costume or flat expression ink."""
    m = surface(name, "#FFFFFF", .83)
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(node for node in n if node.type == "BSDF_PRINCIPLED")
    out = next(node for node in n if node.type == "OUTPUT_MATERIAL")
    img = n.new("ShaderNodeTexImage")
    if isinstance(source, bpy.types.Image):
        img.image = source
    else:
        img.image = bpy.data.images.load(str(Path(source).expanduser().resolve()), check_existing=True)
    if img.image.source == "FILE" and not img.image.packed_file:
        img.image.pack()
    l.new(img.outputs["Color"], p.inputs["Base Color"])
    l.new(img.outputs["Color"], p.inputs["Emission Color"])
    p.inputs["Emission Strength"].default_value = glow
    m.surface_render_method = "BLENDED"
    if cel is not None:
        return _cel_pigment(m, img.outputs["Color"], alpha=img.outputs["Alpha"], lit=cel)
    transparent = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    l.new(img.outputs["Alpha"], mix.inputs[0])
    l.new(transparent.outputs[0], mix.inputs[1])
    l.new(p.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs[0])
    return m


def put(obj, col, parent=None, mat=None):
    for existing in tuple(obj.users_collection):
        existing.objects.unlink(obj)
    col.objects.link(obj)
    obj.parent = parent
    if mat and obj.data:
        obj.data.materials.append(mat)
    return obj


def empty(name, col, loc=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    put(obj, col, parent)
    obj.location = loc
    return obj


def mesh(name, col, vertices, faces, mat, parent=None, smoothing=False, uv=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = put(bpy.data.objects.new(name, data), col, parent, mat)
    if smoothing:
        for polygon in data.polygons:
            polygon.use_smooth = True
    if uv:
        layer = data.uv_layers.new(name="Surface artwork")
        for loop in data.loops:
            layer.data[loop.index].uv = uv[loop.vertex_index]
    return obj


def _ink_hull(obj, col, thickness, *, color, strength):
    # Resolve by name each time so a factory reset or .blend reload cannot
    # leave the module holding a reference to a freed Blender material.
    ink_name = f"Rick's V2 | {color} outline"
    material = bpy.data.materials.get(ink_name)
    if material is None:
        material = emission(ink_name, color, strength)
        material.use_backface_culling = True
    vertices = [tuple(v.co) for v in obj.data.vertices]
    faces = [tuple(reversed(p.vertices)) for p in obj.data.polygons]
    ink = mesh(obj.name + " • ink", col, vertices, faces, material, obj)
    for polygon, source in zip(ink.data.polygons, obj.data.polygons):
        polygon.use_smooth = source.use_smooth
    d = ink.modifiers.new("Screen-compensated hull", "DISPLACE")
    d.mid_level, d.strength = 0, -thickness
    look.mark_role(ink, "ink")
    return d


def _ink_thickness(depth, lens_mm, pixels, default):
    if depth is None and lens_mm is None:
        return default
    if depth is None or lens_mm is None or depth <= 0 or lens_mm <= 0 or pixels <= 0:
        raise ValueError("Supply positive camera depth, focal length and line width.")
    return depth * 36 * pixels / (lens_mm * 640)


def apply_character_ink(obj, collection=None, *, depth=None, lens_mm=None, pixels=3.0):
    """Add character ink to a mesh and return the animatable hull modifier.

    Pass camera-space depth (meters) and lens (mm) for a 360×640 reference
    width. The rig can update the same modifier as the camera moves.
    """
    width = _ink_thickness(depth, lens_mm, pixels, .006)
    return _ink_hull(obj, collection or obj.users_collection[0], width, color=CHARACTER_INK, strength=1.)


def apply_prop_ink(obj, collection=None, *, depth=None, lens_mm=None, pixels=1.25, thickness=.006):
    """Add slim, shadowless ink to a selected prop or architecture mesh.

    Use the v01c fixed scene-unit thickness for static sets, or supply the
    camera depth and focal length for a screen-based width.
    """
    width = _ink_thickness(depth, lens_mm, pixels, thickness)
    return _ink_hull(obj, collection or obj.users_collection[0], width, color="#0B0A10", strength=.55)


def ball(name, col, loc, radii, mat, parent=None, segments=24, rings=16, stretch=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings)
    obj = bpy.context.object
    obj.name = name
    for vert in obj.data.vertices:
        z = vert.co.z
        for axis, radius in enumerate(radii):
            vert.co[axis] *= radius
        if stretch:
            vert.co.z += stretch * (1 if z > .00001 else -1 if z < -.00001 else 0)
    put(obj, col, parent, mat)
    obj.location = loc
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def cylinder(name, col, loc, radius, depth, mat, parent=None, r2=None, length_segments=24):
    bpy.ops.mesh.primitive_cone_add(vertices=length_segments, radius1=radius,
                                   radius2=radius if r2 is None else r2, depth=depth)
    obj = bpy.context.object
    obj.name = name
    put(obj, col, parent, mat)
    obj.location = loc
    for p in obj.data.polygons:
        p.use_smooth = len(p.vertices) == 4
    return obj


def tube(name, col, coords, radius, mat, parent=None):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u, data.bevel_resolution = 9, 3
    data.bevel_depth, data.use_fill_caps = radius, True
    b = data.splines.new("BEZIER")
    b.bezier_points.add(len(coords) - 1)
    for p, co in zip(b.bezier_points, coords):
        p.co = co
        p.handle_left_type = p.handle_right_type = "AUTO"
    return put(bpy.data.objects.new(name, data), col, parent, mat)


def tube_pose(obj, coords, frame):
    for i, (point, co) in enumerate(zip(obj.data.splines[0].bezier_points, coords)):
        point.co = co
        if frame is not None:
            obj.data.keyframe_insert(f"splines[0].bezier_points[{i}].co", frame=frame)


def _fit_leg_knee(leg, hip, knee, ankle, length):
    """Keep hip and foot planted while fitting the knee to a measured spline length."""
    hip, knee, ankle = map(Vector, (hip, knee, ankle))
    axis = ankle - hip
    if length < axis.length:
        raise ValueError("The hip and ankle are farther apart than the reference leg length.")
    if axis.length_squared > 1e-10:
        center = hip + max(0., min(1., (knee-hip).dot(axis)/axis.length_squared)) * axis
    else:
        center = hip
    bend = knee - center
    if bend.length_squared < 1e-10:
        bend = Vector((0, -1, 0)).cross(axis).cross(axis) * -1
        if bend.length_squared < 1e-10:
            bend = Vector((1, 0, 0))
    bend.normalize()
    spline = leg.data.splines[0]
    low, high = 0., length
    for _ in range(15):
        offset = (low+high)/2
        tube_pose(leg, (hip, center+bend*offset, ankle), None)
        if spline.calc_length() < length:
            low = offset
        else:
            high = offset
    return center+bend*((low+high)/2)


def aim(obj, target):
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = (Vector(target) - obj.location).to_track_quat("-Z", "Y")


def make_ricks_light(name, col, loc, target, color, watts, size=.3, kind="AREA", angle=55):
    """Aim a v01c-style area or spot light from `loc` toward `target`."""
    if kind not in {"AREA", "SPOT"}:
        raise ValueError("Rick's practical light helpers support AREA and SPOT lights.")
    data = bpy.data.lights.new(name, kind)
    data.color, data.energy = look.rgba(color)[:3], watts
    data.use_shadow = True
    data.use_shadow_jitter = False
    if kind == "AREA":
        data.size = size
    else:
        data.shadow_soft_size = size
        data.spot_size = math.radians(angle)
        data.spot_blend = .65
    obj = put(bpy.data.objects.new(name, data), col)
    obj.location = loc
    aim(obj, target)
    return obj


def make_light_cone(name, col, top, bottom, narrow, wide, color):
    """Low-opacity cone with volume-free feathering for the RT-off profile."""
    m = emission(name, color, .8)
    m.surface_render_method = "BLENDED"
    n, l = m.node_tree.nodes, m.node_tree.links
    em = next(node for node in n if node.type == "EMISSION")
    out = next(node for node in n if node.type == "OUTPUT_MATERIAL")
    geom, clear, mix = n.new("ShaderNodeLayerWeight"), n.new("ShaderNodeBsdfTransparent"), n.new("ShaderNodeMixShader")
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (.0, .0, .0, 1)
    ramp.color_ramp.elements[1].color = (.034, .034, .034, 1)
    l.new(geom.outputs["Facing"], ramp.inputs[0])
    l.new(ramp.outputs[0], mix.inputs[0])
    l.new(clear.outputs[0], mix.inputs[1])
    l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs[0])
    top, bottom = Vector(top), Vector(bottom)
    obj = cylinder(name, col, (top+bottom)/2, wide, (top-bottom).length, m, r2=narrow)
    obj.rotation_euler = (top-bottom).to_track_quat("Z", "Y").to_euler()
    look.mark_role(obj, "wisp")
    return obj


def pose_arm(arm, shoulder, elbow, hand, frame):
    shoulder, elbow, hand = map(Vector,(shoulder,elbow,hand))
    upper = (elbow-shoulder).normalized()
    lower = (hand-elbow).normalized()
    turn = (upper+lower).normalized()
    positions = (shoulder,elbow,hand,hand+lower*.009,hand+lower*.016)
    tangents = (upper,turn,lower,lower,lower)
    # Key the handles as well as the knots. Auto handles left at a later pose
    # can jut past a moving elbow or curl a short tip back on itself.
    for i,(point,knot,tangent) in enumerate(zip(arm.data.splines[0].bezier_points,positions,tangents)):
        rest = len(positions)-1
        left = (knot-positions[i-1]).length/3 if i else 0
        right = (positions[i+1]-knot).length/3 if i<rest else 0
        if i==1:
            left=right=.29*min((elbow-shoulder).length,(hand-elbow).length)
        point.co = knot
        point.handle_left_type = point.handle_right_type = "FREE"
        point.handle_left = knot-tangent*left
        point.handle_right = knot+tangent*right
        if frame is not None:
            for channel in ("co","handle_left","handle_right"):
                arm.data.keyframe_insert(f"splines[0].bezier_points[{i}].{channel}",frame=frame)


def decal(name, col, parent, mat, half, center, radii):
    width, height = half
    nx, nz = 31, 29
    verts, faces, uv = [], [], []
    for j in range(nz):
        v = j/(nz-1)
        z = (2*v-1)*height
        for i in range(nx):
            u = i/(nx-1)
            x = (2*u-1)*width
            center_z = z + center
            if radii == HEAD:
                curve = (center_z/radii[2])**2
            else:
                curve = (max(0, abs(z)-.102)/.128)**2
            y = -radii[1]*math.sqrt(max(.035, 1-(x/radii[0])**2-curve))-.0033
            verts.append((x, y, center_z))
            uv.append((u, v))
            if i and j:
                k = len(verts)-1
                faces.append((k-nx-1,k-nx,k,k-1))
    obj = mesh(name, col, verts, faces, mat, parent, True, uv)
    obj.visible_shadow = False
    return obj


def scalp(name, col, head, mat):
    verts, faces = [], []
    # Preserve v01c's authored crown rise and chestnut profile in addition
    # to the minimum radial allowance over the head and its ink.
    rx = HEAD[0] + HAIR_RADIAL_OFFSET + .003
    ry = HEAD[1] + HAIR_RADIAL_OFFSET + .0018
    rz = HEAD[2] + HAIR_RADIAL_OFFSET + .0124
    for j in range(14):
        for i in range(RING):
            a = math.tau*i/RING
            front = max(0., -math.sin(a))
            contour = 1.87-.60*front + .12*math.sin(7*a+.5) + .08*math.sin(11*a)
            polar = .012+(contour-.012)*j/13
            verts.append((rx*math.sin(polar)*math.cos(a), ry*math.sin(polar)*math.sin(a)+.012,
                          rz*math.cos(polar)+.017))
            if j:
                k, nxt = j*RING+i, j*RING+(i+1)%RING
                faces.append((k-RING,k,nxt,nxt-RING))
    faces.extend((tuple(reversed(range(RING))), tuple(range(13*RING,14*RING))))
    return mesh(name, col, verts, faces, mat, head, True)


def hood(name, col, head, cloth, lining):
    verts, faces = [], []
    # Width, depth, top and hem for the lining, folded lip and outer cloth.
    # The narrow upper opening and flared lower panels create a bell profile.
    rings = [
        (.223,-.137,.185,-.205), (.225,-.247,.186,-.230),
        (.237,-.260,.194,-.246), (.255,-.228,.229,-.266),
        (.275,-.173,.279,-.287), (.285,-.090,.313,-.294),
        (.277,.014,.327,-.296), (.254,.109,.310,-.285),
        (.205,.186,.267,-.253), (.110,.244,.191,-.165),
        (.028,.268,.066,-.032), (.006,.274,.026,.010),
    ]
    for j,(width,y,top,hem) in enumerate(rings):
        for i in range(RING):
            a = math.tau*i/RING
            h = math.sin(a)
            brow = max(0,h)
            fall = max(0,-h)
            shoulder = 1-.22*brow+.23*fall
            drape = max(0,1-abs(j-5)/5)
            ripple = .018*drape*math.cos(6*a+.7)
            x = math.cos(a)*(width*shoulder+ripple)
            z = top*brow**.79+hem*fall**1.20 + .025*(1-abs(h))
            depth = y-(.093*brow**2+.027*fall)*max(0,1-j/8)
            depth += drape*.017*math.sin(5*a+.33)
            verts.append((x,depth,z))
            if j:
                k, nxt = j*RING+i,j*RING+(i+1)%RING
                faces.append((k-RING,k,nxt,nxt-RING))
    faces.append(tuple(reversed(range((len(rings)-1)*RING,len(verts)))))
    obj = mesh(name+" | draped pointed wool hood",col,verts,faces,cloth,head,True)
    obj.data.materials.append(lining)
    for panel in obj.data.polygons[:2*RING]:
        panel.material_index = 1
    return obj


class RicksCharacter:
    """Built rig with body/head controls, curve limbs, and conformed artwork."""

    def __init__(self, name, col, hooded, costume_image, expression_images, *, face_shadow=None, face_cutoff=None):
        self.name = name
        self.root = empty(name, col)
        self.body = empty(name+" | body control", col, (0,0,.59), self.root)
        self.head = empty(name+" | head control", col, (0,0,FACE_CENTER-.59), self.body)
        self.ink_modifiers = []
        ink = emission(name+" | matte stick ink", "#050508")
        face_material = make_lit_cel_face_material(name+" | lit cel face", hood_shadow=hooded,
                                                 shadow=face_shadow, cutoff=face_cutoff)
        face = ball(name+" | ellipsoid head",col,(0,0,0),HEAD,face_material,
                    self.head,48,32)
        self.ink_modifiers.append(apply_character_ink(face,col))
        jacket = make_cel_character_material(name+" | costume", "#181A28" if hooded else "#E5A928")
        torso = ball(name+" | graphic pill torso",col,(0,0,TORSO_CENTER-.59),(.125,.085,.128),
                     jacket,self.body,48,32,stretch=.102)
        self.ink_modifiers.append(apply_character_ink(torso,col))
        tuft = make_cel_character_material(name+" | silhouette cloth or layered chestnut",
                                          "#262944" if hooded else "#542C24")
        accent = make_cel_character_material(name+" | hand-painted warm edging",
                                            "#424667" if hooded else "#90543A")
        if hooded:
            lining = emission(name+" | matte black-indigo lining", "#0B0D18")
            cap = hood(name,col,self.head,tuft,lining)
            tube(name+" | piped cloak fold",col,[(-.058,-.076,.23),(.04,-.09,.18),(.078,-.067,.098)],
                 .008,accent,self.body)
            ball(name+" | antique closure",col,(.032,-.093,.30),(.02,.007,.02),accent,self.body,12,10)
        else:
            cap = scalp(name+" | shaped hair cap",col,self.head,tuft)
            for stripe,(start,length,base,arc) in enumerate((
                (3.43,1.17,.87,.20), (3.49,.88,1.031,.22), (3.73,.61,1.137,.13)
            )):
                points = []
                for i in range(15):
                    t = i/14
                    a = start+length*t
                    polar = base-.26*t-arc*math.sin(math.pi*t)
                    points.append((.2525*math.sin(polar)*math.cos(a),.2225*math.sin(polar)*math.sin(a)+.012,
                                   .248*math.cos(polar)+.017))
                stroke = tube(name+" | swept chestnut highlight",col,points,.008-.0014*stripe,accent,self.head)
                for i,point in enumerate(stroke.data.splines[0].bezier_points):
                    point.radius = .09+.91*math.sin(math.pi*i/14)**.88
        if costume_image is not None:
            mat = artwork(name+" | costume art", costume_image, cel=True)
            decal(name+" | conformed costume art", col, self.body, mat, (.102,.195),
                  TORSO_CENTER-.59,(.125,.085,.128))
        hull = apply_character_ink(cap,col)
        self.ink_modifiers.append(hull)
        if not hooded:
            for mesh_obj in (cap,hull.id_data):
                smooth = mesh_obj.modifiers.new("Smooth crown","SUBSURF")
                smooth.levels = smooth.render_levels = 2
                if mesh_obj != cap:
                    mesh_obj.modifiers.move(1,0)
        self.expressions = {}
        for expr, image in expression_images.items():
            mat = artwork(name+" | "+expr, image, cel=False)
            self.expressions[expr] = decal(name+" | "+expr,col,self.head,mat,(.175,.141),
                                           .013 if hooded else -.024,HEAD)
        self.arms, self.legs, self.feet = [],[],[]
        for side in (-1,1):
            side_name = "L" if side < 0 else "R"
            end = Vector((side*.21,-.16,.21))
            arc = tube(name+" | round-tipped arm "+side_name,col,
                       [(side*.11,0,.36),(side*.18,-.04,.24),end,end+Vector((0,-.009,0)),
                        end+Vector((0,-.016,0))],.015,ink,self.body)
            for point,radius in zip(arc.data.splines[0].bezier_points,(1,1,1.1,.82,.015)):
                point.radius = radius
            self.arms.append(arc)
            self.legs.append(tube(name+" | stick leg "+side_name,col,[(side*.058,0,.65),(side*.084,-.04,.33),
                                                                   (side*.12,0,.029)],.015,ink,self.root))
            self.feet.append(ball(name+" | foot tick "+side_name,col,(0,0,0),(.027,.035,.017),
                                  ink,self.root,14,10))
        self.sweat = None
        if not hooded:
            blue = make_cel_character_material(name+" | comic sweat cyan", "#51C8F2")
            border = emission(name+" | comic sweat ink", "#0A0A0E", .85)
            contour = [(0,.033),(-.007,.024),(-.015,.013),(-.019,.002),(-.019,-.009),
                       (-.014,-.017),(-.006,-.022),(.005,-.022),(.014,-.018),(.019,-.011),
                       (.020,-.002),(.016,.008),(.007,.020)]
            outer = [(x,0,z) for x,z in contour]
            inner = [(x*.77,-.0008,z*.84-.0005) for x,z in contour]
            count = len(outer)
            strips = [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
            self.sweat = mesh(name+" | outlined temple drop",col,outer+inner,
                              [*strips,tuple(range(count,2*count))],border,self.head)
            self.sweat.data.materials.append(blue)
            self.sweat.data.polygons[-1].material_index = 1
            self.sweat.visible_shadow = False

    def display(self, expression, frame=None):
        """Set a named expression and optionally bake an instant visibility snap."""
        if expression is None:
            return
        if expression not in self.expressions:
            raise ValueError(f"Unknown expression {expression!r} for {self.name}.")
        for name, obj in self.expressions.items():
            obj.hide_render = name != expression
            obj.hide_viewport = name != expression
            if frame is not None:
                for channel in ("hide_render","hide_viewport"):
                    obj.keyframe_insert(channel,frame=frame)
                    curve = obj.animation_data.action.fcurves.find(channel)
                    for key in curve.keyframe_points:
                        key.interpolation = "CONSTANT"

    def measure_leg_lengths(self):
        """Return left and right curve lengths from the current standing reference pose."""
        return tuple(leg.data.splines[0].calc_length() for leg in self.legs)

    def pose(self, frame, location, yaw, tilt, arms, legs, expression=None, *,
             bounce=0, head_tilt=0, head_yaw=0, squash=1, sweat=None, leg_lengths=None):
        """Apply or bake a pose. Pass None for frame to pose without keyframes.

        `arms` are (tip, elbow) pairs in body-local coordinates. `legs` are
        (ankle, knee) pairs in root-local coordinates. Both are left then right.
        `yaw`, `tilt` and head angles are radians. `sweat` is None or 0–1 along
        the temple path. Pass `expression` at its first key and when it changes.
        Pass measured standing `leg_lengths` to fit the knees without moving
        the planted ankles of a seated pose.
        """
        self.root.location, self.root.rotation_euler.z = location, yaw
        self.body.location.z, self.body.rotation_euler.x = .59+bounce, tilt
        self.body.scale.z = squash
        self.head.rotation_euler.x, self.head.rotation_euler.z = head_tilt, head_yaw
        for obj, channels in ((self.root,("location","rotation_euler")),
                              (self.body,("location","rotation_euler","scale")),
                              (self.head,("rotation_euler",))):
            for channel in channels:
                if frame is not None:
                    obj.keyframe_insert(channel,frame=frame)
        for i, side in enumerate((-1,1)):
            hand, elbow = arms[i]
            foot, knee = legs[i]
            pose_arm(self.arms[i],(side*.106,-.003,.342),elbow,hand,frame)
            hip = (Euler((tilt,0,0)).to_matrix() @ Vector((side*.060,0,.070*squash))
                   + Vector((0,0,.59+bounce)))
            if leg_lengths is not None:
                hip = self.body.rotation_euler.to_matrix() @ Vector((side*.060,0,.070*squash))
                hip += self.body.location
                knee = _fit_leg_knee(self.legs[i], hip, knee, foot, leg_lengths[i])
            tube_pose(self.legs[i],[hip,knee,foot],frame)
            self.feet[i].location = Vector(foot)+Vector((0,-.021,-.010))
            if frame is not None:
                self.feet[i].keyframe_insert("location",frame=frame)
        self.display(expression,frame)
        if self.sweat:
            self.sweat.hide_render = self.sweat.hide_viewport = sweat is None
            if frame is not None:
                for prop in ("hide_render","hide_viewport"):
                    self.sweat.keyframe_insert(prop,frame=frame)
            if sweat is not None:
                x,z = -.122-.024*sweat,.081-.060*sweat
                y = -HEAD[1]*math.sqrt(1-(x/HEAD[0])**2-(z/HEAD[2])**2)
                self.sweat.location = (x,y-.008,z)
                self.sweat.rotation_euler = (.10, -.24, -.44)
                if frame is not None:
                    self.sweat.keyframe_insert("location",frame=frame)

    def update_ink(self, camera, *, pixels=3.0, frame=None):
        """Set or key the stroke width from the evaluated camera and hull depths."""
        inverse = camera.matrix_world.inverted()
        for hull in self.ink_modifiers:
            depth = -(inverse @ hull.id_data.matrix_world.translation).z
            if depth <= 0:
                continue
            hull.strength = -min(.015, _ink_thickness(depth, camera.data.lens, pixels, .006))
            if frame is not None:
                hull.keyframe_insert("strength",frame=frame)

    def finish_bake(self):
        """Use linear interpolation between baked poses and constant expression keys."""
        targets = [self.root,self.body,self.head,*self.feet,*self.expressions.values()]
        targets.extend(curve.data for curve in (*self.arms,*self.legs))
        targets.extend(mod.id_data for mod in self.ink_modifiers)
        if self.sweat:
            targets.append(self.sweat)
        for target in targets:
            if not target.animation_data or not target.animation_data.action:
                continue
            for curve in target.animation_data.action.fcurves:
                is_visibility = curve.data_path in {"hide_render","hide_viewport"}
                for key in curve.keyframe_points:
                    key.interpolation = "CONSTANT" if is_visibility else "LINEAR"


def build_ricks_character(name, collection, *, hooded=False, art_dir=None, costume_image=None,
                          expression_images=None, initial_expression=None, face_shadow=None,
                          face_cutoff=None):
    """Build a neckless, UV-ready Rick's stick-hybrid rig in `collection`.

    Pass paths or Blender images for `costume_image` and the named
    `expression_images` mapping. `art_dir` fills in the v01c PNG names, with
    caller-supplied images taking precedence. Without art, the rig is ready
    for a later costume or face pass. Its forward direction is local -Y.
    Set `face_shadow` and `face_cutoff` for the shot lighting palette.
    """
    if bpy is None:
        raise RuntimeError("Build Rick's characters from Blender 4.2 Python.")
    images = dict(expression_images or {})
    if art_dir is not None:
        folder = Path(art_dir)
        defaults = HOODED_EXPRESSIONS if hooded else HERO_EXPRESSIONS
        images = {**{key:folder/f"{key}.png" for key in defaults},**images}
        if not hooded and costume_image is None:
            costume_image = folder/"jacket.png"
    if initial_expression is None:
        initial_expression = next(iter(images),None)
    if initial_expression is not None and initial_expression not in images:
        raise ValueError(f"Initial expression {initial_expression!r} has no supplied image.")
    rig = RicksCharacter(name,collection,hooded,costume_image,images,
                         face_shadow=face_shadow,face_cutoff=face_cutoff)
    arms = [((side*.18,-.05,.12),(side*.18,.00,.24)) for side in (-1,1)]
    legs = [((side*.10,-.02,.027),(side*.095,-.06,.32)) for side in (-1,1)]
    rig.pose(None,(0,0,0),0,0,arms,legs,initial_expression)
    return rig


def configure_ricks_scene(scene, *, width=1080, height=1920, fps=30, frame_end=None, samples=8):
    """Apply v01c's RT-off EEVEE defaults before building a new shot or scene."""
    look.configure_scene(scene, width=width, height=height, fps=fps, frame_end=frame_end, samples=samples)
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 1,4
    scene.eevee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
    scene.render.film_transparent = False
    return scene


def setup_ricks_camera(camera, *, lens=38, fstop=2.85, clip_end=110):
    """Set the portrait sensor and focus-by-distance DOF from v01c."""
    look.configure_camera(camera,None,lens=lens,fstop=fstop)
    camera.data.clip_end = clip_end
    return camera


def set_ricks_camera_focus(camera, target, *, frame=None):
    """Focus on a world-space target's axial plane and optionally key the DOF."""
    depth = -(camera.matrix_world.inverted() @ Vector(target)).z
    camera.data.dof.focus_object = None
    camera.data.dof.focus_distance = max(.085,depth)
    if frame is not None:
        camera.data.keyframe_insert("dof.focus_distance",frame=frame)
    return camera.data.dof.focus_distance


def apply_portrait_dof(camera, target_obj, fstop=1.6):
    """Track the face-plane object without per-frame focus keys or lens changes."""
    if camera.type != "CAMERA" or camera.data.type != "PERSP":
        raise ValueError("Portrait DOF requires a perspective camera")
    if target_obj is None or target_obj == camera or not math.isfinite(fstop) or fstop <= 0:
        raise ValueError("Provide a face-plane target and a positive f-stop")
    dof = camera.data.dof
    dof.use_dof = True
    dof.focus_object = target_obj
    dof.aperture_fstop = fstop
    dof.aperture_blades = 6
    return dof


def setup_hero_portrait_lighting(hero_obj, bg_dim=0.68):
    """Set the environment fill and add a close key and rim parented to the hero.

    Pass the head control (local -Y faces forward), or a face-height anchor
    parented to it. Build after placing the environment lights. The spot
    cones and finite ranges limit spill on EEVEE 4.2. Keep one portrait
    anchor active per shot.
    """
    if not 0 < bg_dim <= 1:
        raise ValueError("bg_dim must be greater than zero and at most one")
    scene = bpy.context.scene
    if scene.objects.get(hero_obj.name) != hero_obj:
        raise ValueError("The hero anchor must be in the active scene")
    collection = next((col for col in hero_obj.users_collection if col in
                       [scene.collection, *scene.collection.children_recursive]), scene.collection)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("Portrait world")
    if scene.world.users > 1:
        scene.world = scene.world.copy()
    if not scene.world.use_nodes:
        scene.world.use_nodes = True
    tree = scene.world.node_tree
    for background in (node for node in tree.nodes if node.type == "BACKGROUND"):
        strength = background.inputs["Strength"]
        link = strength.links[0] if strength.is_linked else None
        if link and link.from_node.get("ricks_portrait_world_scale"):
            link.from_node.inputs[1].default_value = bg_dim
        else:
            scale = tree.nodes.new("ShaderNodeMath")
            scale.name = scale.label = "Portrait world fill"
            scale["ricks_portrait_world_scale"] = True
            scale.operation = "MULTIPLY"
            scale.inputs[0].default_value = strength.default_value
            scale.inputs[1].default_value = bg_dim
            if link:
                tree.links.new(link.from_socket, scale.inputs[0])
            tree.links.new(scale.outputs[0], strength)

    environment = {obj.data for obj in scene.objects if obj.type == "LIGHT" and not obj.get("ricks_portrait_light")}
    for light in environment:
        light["ricks_environment_energy"] = light.get("ricks_environment_energy", light.energy)
        light.energy = light["ricks_environment_energy"] * bg_dim
    if not any(obj.type == "LIGHT" and obj.data.type == "SUN" and obj.data.use_shadow
               and not obj.hide_render for obj in scene.objects):
        sun = next((obj for obj in collection.objects if obj.get("ricks_portrait_light") == "Sun"), None)
        if sun is None:
            data = bpy.data.lights.new("Portrait | angled sun", "SUN")
            sun = put(bpy.data.objects.new(data.name, data), collection)
            sun["ricks_portrait_light"] = "Sun"
            sun.location = (-4, -3, 4)
            aim(sun, (0, 0, 0))
            data.color = look.rgba("#ffe1bb")[:3]
            data.energy, data.angle = .21, .035
            data.use_shadow, data.use_shadow_jitter = True, False

    lights = []
    for role, position, target, color, watts, distance, angle in (
        ("Key", (-.57,-.96,.66), (0,0,-.10), "#ffe4c4", 105, 1.65, 52),
        ("Rim", (.52,.56,.37), (0,0,-.10), "#a9c4ff", 45, 1.25, 57),
    ):
        light = next((obj for obj in hero_obj.children if obj.get("ricks_portrait_light") == role), None)
        if light is None:
            light = make_ricks_light(f"Portrait | {role}", collection, position, target, color,
                                     watts, size=.19, kind="SPOT", angle=angle)
            light.parent = hero_obj
            light["ricks_portrait_light"] = role
            light.data.use_custom_distance = True
            light.data.cutoff_distance = distance
            light.data.use_shadow = role == "Key"
        lights.append(light)
    return tuple(lights)


def setup_ricks_compositor(scene, *, camera=None, portal_flash_keys=(), replace=False, cinema_grade=True):
    """Install the cinema grade, packed vignette and additive portal flash.

    `portal_flash_keys` contains ascending (frame, strength) pairs with
    zero at both ends. Key the final zero before the first revealed frame.
    The returned flash node exposes its strength on input 0. With a camera,
    initialize the portrait sensor. An existing tracked focus is preserved.
    Use cinema_grade=False to reproduce the archived compositor.
    """
    keys = tuple(portal_flash_keys)
    if keys and (
        keys[0][1] != 0 or keys[-1][1] != 0
        or any(not 0 <= value <= 1 for _,value in keys)
        or any(a[0] >= b[0] for a,b in zip(keys,keys[1:]))
    ):
        raise ValueError("Flash keys must increase in time and start and end at zero strength.")
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    if camera is not None and camera.data.dof.focus_object is None:
        setup_ricks_camera(camera,lens=camera.data.lens)
    scene.use_nodes = True
    n, l = scene.node_tree.nodes, scene.node_tree.links
    is_default = len(n)==2 and {node.type for node in n}=={"R_LAYERS","COMPOSITE"}
    if n and not is_default and not replace:
        raise ValueError("The scene has a compositor already. Use replace=True to rebuild it.")
    if replace and scene.node_tree.animation_data and scene.node_tree.animation_data.action:
        action = scene.node_tree.animation_data.action
        for curve in tuple(action.fcurves):
            if curve.data_path=='nodes["Portal | additive warm-gold flash"].inputs[0].default_value':
                action.fcurves.remove(curve)
    n.clear()
    source, output = n.new("CompositorNodeRLayers"), n.new("CompositorNodeComposite")
    picture = source.outputs["Image"]
    if cinema_grade:
        balance = n.new("CompositorNodeColorBalance")
        balance.name = balance.label = "Cinema | Lift Gamma Gain"
        balance.correction_method = "LIFT_GAMMA_GAIN"
        balance.lift = (.981,.988,1.001)
        balance.gamma = (1.007,.997,.990)
        balance.gain = (1.034,1.010,.991)
        l.new(picture,balance.inputs["Image"])
        saturation = n.new("CompositorNodeHueSat")
        saturation.name = saturation.label = "Cinema | Saturation 1.12"
        saturation.inputs["Saturation"].default_value = 1.12
        l.new(balance.outputs[0],saturation.inputs["Image"])
        picture = saturation.outputs[0]
    glow = n.new("CompositorNodeGlare")
    glow.glare_type, glow.quality, glow.threshold, glow.size, glow.mix = "FOG_GLOW","LOW",.88 if cinema_grade else .9,7,1
    l.new(picture,glow.inputs[0])
    add = n.new("CompositorNodeMixRGB")
    add.blend_type, add.inputs[0].default_value = "ADD", .24 if cinema_grade else .30
    l.new(picture,add.inputs[1])
    l.new(glow.outputs[0],add.inputs[2])
    # A packed radial mask gives the same soft falloff without computing
    # a large Gaussian blur on every 1080x1920 compositing pass.
    size = 128
    amount = .22 if cinema_grade else .20
    image = bpy.data.images.new(f"Vignette | radial {amount:.0%}",size,size)
    image.colorspace_settings.name = "Non-Color"
    pixels = []
    for y in range(size):
        for x in range(size):
            radius = math.hypot((2*x+1)/size-1,(2*y+1)/size-1)
            value = 1-amount*look.ease5((radius-.29)/(math.sqrt(2)-.29 if cinema_grade else 1.09))
            pixels.extend((value,value,value,1.))
    image.pixels.foreach_set(pixels)
    image.pack()
    mask = n.new("CompositorNodeImage")
    mask.image = image
    scaled = n.new("CompositorNodeScale")
    scaled.space = "RENDER_SIZE"
    scaled.frame_method = "STRETCH"
    l.new(mask.outputs["Image"],scaled.inputs["Image"])
    mult = n.new("CompositorNodeMixRGB")
    mult.blend_type, mult.inputs[0].default_value = "MULTIPLY",1
    l.new(scaled.outputs[0],mult.inputs[2])
    l.new(add.outputs[0],mult.inputs[1])
    flash = n.new("CompositorNodeMixRGB")
    flash.name = "Portal | additive warm-gold flash"
    flash.blend_type = "ADD"
    flash.inputs[2].default_value = (18.0,10.0,4.6,1)
    l.new(mult.outputs[0],flash.inputs[1])
    l.new(flash.outputs[0],output.inputs[0])
    strength = flash.inputs[0]
    strength.default_value = 0.0
    for frame,value in keys:
        strength.default_value = value
        strength.keyframe_insert("default_value",frame=frame)
    if keys:
        curve = scene.node_tree.animation_data.action.fcurves.find(strength.path_from_id("default_value"))
        for key in curve.keyframe_points:
            key.interpolation = "LINEAR"
    return flash


@dataclass(frozen=True)
class StickWalkPose:
    """Inputs for RicksCharacter.pose plus contact samples for motion QA."""

    location: tuple
    yaw: float
    tilt: float
    bounce: float
    arms: tuple
    legs: tuple
    feet_world: tuple
    planted: tuple


def eval_stick_walk_cycle(frame, route_at, yaw, *, start_frame=1, stop_frame=None,
                          plant_yaw=math.pi, strength=1.0, ground_z=0.0):
    """Sample v01c's 10-frame gait without mutating Blender state.

    `route_at(frame)` gives the world-space rig root. `yaw` is its current
    heading in radians, with local -Y forward. `plant_yaw` is a fixed
    heading or a callable sampled once per contact for curved routes.
    Both world X and Y stay fixed during stance, including across turning
    roots. Order is left/right in the returned limbs and foot samples.
    Fade `strength` at entry/exit as desired to reduce bob, lean and swing.
    `ground_z` is the height of the flat receiving surface in world meters.
    """
    if stop_frame is not None and stop_frame < start_frame:
        raise ValueError("stop_frame must be on or after start_frame.")
    strength = min(1.0,max(0.0,strength))
    root = tuple(route_at(frame))
    sin_yaw,cos_yaw = math.sin(yaw),math.cos(yaw)
    q = (frame-start_frame)*math.tau/10
    arms,legs,feet,planted = [],[],[],[]

    def anchor(strike, side):
        sample = max(strike+2,start_frame-2)
        if stop_frame is not None:
            sample = min(sample,stop_frame)
        x,y,_ = route_at(sample)
        heading = plant_yaw(sample) if callable(plant_yaw) else plant_yaw
        s,c = math.sin(heading),math.cos(heading)
        return (x+side*.103*c+.032*s,y+side*.103*s-.032*c)

    for side,first,phase_offset in ((-1,start_frame,0),(1,start_frame-5,math.pi)):
        strike = first+10*math.floor((frame-first)/10)
        phase = frame-strike
        toe_off = max(0.0,(phase-4)/6)
        a,b = anchor(strike,side),anchor(strike+10,side)
        travel = look.ease5(toe_off)
        x,y = (u+(v-u)*travel for u,v in zip(a,b))
        lift = .165
        if stop_frame is not None:
            lift *= 1-.64*look.ease5((strike-(stop_frame-11))/12)
        height = lift*math.sin(math.pi*toe_off)**1.3 if a!=b else 0.0
        z = ground_z+.017+height
        dx,dy = x-root[0],y-root[1]
        fx = cos_yaw*dx+sin_yaw*dy
        fy = -sin_yaw*dx+cos_yaw*dy+.021
        ankle = (fx,fy,z-root[2]+.010)
        knee = (.68*side*.095+.32*fx,min(-.059,fy*.42)-.70*height,.318+.43*height)
        swing = math.cos(q+phase_offset)*strength
        arms.append(((side*.156,-.075+.244*swing,.082+.098*max(0,-swing)),
                     (side*.179,.042+.128*swing,.237+.044*swing)))
        legs.append((ankle,knee))
        feet.append((x,y,z))
        planted.append(toe_off==0 or a==b)

    bounce = .060*strength*(.5-.5*math.cos(2*q))**1.18
    return StickWalkPose(root,yaw,.332*strength,bounce,tuple(arms),tuple(legs),tuple(feet),tuple(planted))
