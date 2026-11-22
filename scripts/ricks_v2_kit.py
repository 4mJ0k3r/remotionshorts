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
import random
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
ROUND_HEAD = (0.235, 0.205, 0.235)
UPRIGHT_HEAD = (0.230, 0.205, 0.238)
FACE_CENTER = 1.237
TORSO_CENTER = .831
RING = 48
HAIR_RADIAL_OFFSET = .008
HERO_EXPRESSIONS = ("suspicious", "excited_awe", "smug_focus", "sneaky", "shock_terror")
HOODED_EXPRESSIONS = ("broker_neutral", "broker_creepy_grin")
CREAM_FACE = "#FFF9F0"
PAPER_WHITE_FACE = "#FAF9F6"
PAPER_WHITE_SHADOW = "#EAE8E1"
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


def make_bright_paper_face_material(name, *, face_color=PAPER_WHITE_FACE,
                                    shadow_color=PAPER_WHITE_SHADOW, cutoff=0.18,
                                    strength=1.26):
    """AgX-calibrated bright paper-white cel face (#FAF9F6 / #EAE8E1).

    Prevents grey/muddy midtones under AgX Medium High Contrast while keeping
    clean contact shading and crisp contrast behind dark eye/mouth decals.
    """
    stops = _two_step_stops(shadow_color, face_color, cutoff)
    m = surface(name, face_color, 1.)
    shade = _cel_ramp(m, stops)
    _cel_output(m, shade, float(strength))
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


def decal(name, col, parent, mat, half, center, radii, *, ellipsoid=None):
    width, height = half
    nx, nz = 31, 29
    is_ellipsoid = (radii == HEAD) if ellipsoid is None else bool(ellipsoid)
    verts, faces, uv = [], [], []
    for j in range(nz):
        v = j/(nz-1)
        z = (2*v-1)*height
        for i in range(nx):
            u = i/(nx-1)
            x = (2*u-1)*width
            center_z = z + center
            if is_ellipsoid:
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


def scalp(name, col, head, mat, head_radii=HEAD):
    verts, faces = [], []
    # Preserve v01c's authored crown rise and chestnut profile in addition
    # to the minimum radial allowance over the head and its ink.
    rx = head_radii[0] + HAIR_RADIAL_OFFSET + .003
    ry = head_radii[1] + HAIR_RADIAL_OFFSET + .0018
    rz = head_radii[2] + HAIR_RADIAL_OFFSET + .0124
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

    def __init__(self, name, col, hooded, costume_image, expression_images, *, face_shadow=None, face_cutoff=None,
                 head_radii=None):
        self.name = name
        self.head_radii = tuple(float(v) for v in (HEAD if head_radii is None else head_radii))
        self.root = empty(name, col)
        self.body = empty(name+" | body control", col, (0,0,.59), self.root)
        self.head = empty(name+" | head control", col, (0,0,FACE_CENTER-.59), self.body)
        self.ink_modifiers = []
        ink = emission(name+" | matte stick ink", "#050508")
        face_material = make_lit_cel_face_material(name+" | lit cel face", hood_shadow=hooded,
                                                 shadow=face_shadow, cutoff=face_cutoff)
        face = ball(name+" | ellipsoid head",col,(0,0,0),self.head_radii,face_material,
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
            cap = scalp(name+" | shaped hair cap",col,self.head,tuft,head_radii=self.head_radii)
            hx = self.head_radii[0] + .0125
            hy = self.head_radii[1] + .0113
            hz = self.head_radii[2] + .0224
            for stripe,(start,length,base,arc) in enumerate((
                (3.43,1.17,.87,.20), (3.49,.88,1.031,.22), (3.73,.61,1.137,.13)
            )):
                points = []
                for i in range(15):
                    t = i/14
                    a = start+length*t
                    polar = base-.26*t-arc*math.sin(math.pi*t)
                    points.append((hx*math.sin(polar)*math.cos(a),hy*math.sin(polar)*math.sin(a)+.012,
                                   hz*math.cos(polar)+.017))
                stroke = tube(name+" | swept chestnut highlight",col,points,.008-.0014*stripe,accent,self.head)
                for i,point in enumerate(stroke.data.splines[0].bezier_points):
                    point.radius = .09+.91*math.sin(math.pi*i/14)**.88
        if costume_image is not None:
            mat = artwork(name+" | costume art", costume_image, cel=True)
            decal(name+" | conformed costume art", col, self.body, mat, (.102,.195),
                  TORSO_CENTER-.59,(.125,.085,.128),ellipsoid=False)
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
                                           .013 if hooded else -.024,self.head_radii,ellipsoid=True)
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
                hr = getattr(self, "head_radii", HEAD)
                x,z = -.122-.024*sweat,.081-.060*sweat
                y = -hr[1]*math.sqrt(max(.01, 1-(x/hr[0])**2-(z/hr[2])**2))
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
                          face_cutoff=None, head_radii=None):
    """Build a neckless, UV-ready Rick's stick-hybrid rig in `collection`.

    Pass paths or Blender images for `costume_image` and the named
    `expression_images` mapping. `art_dir` fills in the v01c PNG names, with
    caller-supplied images taking precedence. Without art, the rig is ready
    for a later costume or face pass. Its forward direction is local -Y.
    Set `face_shadow` and `face_cutoff` for the shot lighting palette.
    Pass `head_radii=ROUND_HEAD` (1:1) or `UPRIGHT_HEAD` (H/W=1.035) to
    prevent horizontal oval head squash on new Shorts.
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
                         face_shadow=face_shadow,face_cutoff=face_cutoff,head_radii=head_radii)
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


# ------------------------------------------------------------------ V7 Foundation Upgrades
# Additive helpers for:
#   1. 1:1 / upright head proportions (banning squashed horizontal ovals)
#   2. AgX bright paper-white faces + pixel-locked upper-face speech pairs
#   3. 6:1 directional chiaroscuro lighting + contact AO + subtle light cones
#   4. Multi-node PBR materials & continuous lofted/lathed geometry
#   5. Deep-focus cutaway diorama camera & compositor (DOF strictly OFF)


def _find_head_mesh(rig_or_head_obj):
    """Resolve a rig or head object to its primary head mesh object."""
    if hasattr(rig_or_head_obj, "head") and hasattr(rig_or_head_obj, "name"):
        if bpy is not None:
            by_name = bpy.data.objects.get(f"{rig_or_head_obj.name} | ellipsoid head")
            if by_name is not None:
                return by_name
        children = getattr(rig_or_head_obj.head, "children", ())
        for child in children:
            if getattr(child, "type", None) == "MESH":
                low = getattr(child, "name", "").lower()
                if "ink" not in low and "hair" not in low and "hood" not in low and "decal" not in low:
                    return child
        return rig_or_head_obj.head
    return rig_or_head_obj


def measure_head_ratio(rig_or_head_obj):
    """Measure a head mesh's width, depth, height and H/W ratio (detects oval squash).

    Accepts a `RicksCharacter`, a `MascotRig` (with `head_bbox_ratio()`),
    a Blender mesh object, or a pure-Python mock object exposing `.data.vertices`.
    """
    if hasattr(rig_or_head_obj, "head_bbox_ratio") and callable(rig_or_head_obj.head_bbox_ratio):
        info = dict(rig_or_head_obj.head_bbox_ratio())
        ratio = float(info.get("ratio", 1.0))
        info.setdefault("hw_ratio", ratio)
        info.setdefault("is_squashed", ratio < 0.98)
        return info

    head_obj = _find_head_mesh(rig_or_head_obj)
    data = getattr(head_obj, "data", None)
    verts = getattr(data, "vertices", None)
    if not verts:
        raise ValueError(f"Cannot measure head ratio: no mesh vertices on {head_obj!r}")

    scale = tuple(getattr(head_obj, "scale", (1.0, 1.0, 1.0)))
    parent = getattr(head_obj, "parent", None)
    if parent is not None and hasattr(parent, "scale"):
        ps = tuple(parent.scale)
        scale = (scale[0] * ps[0], scale[1] * ps[1], scale[2] * ps[2])

    xs = [float(v.co[0]) * abs(scale[0]) for v in verts]
    ys = [float(v.co[1]) * abs(scale[1]) for v in verts]
    zs = [float(v.co[2]) * abs(scale[2]) for v in verts]
    width_m = max(xs) - min(xs)
    depth_m = max(ys) - min(ys)
    height_m = max(zs) - min(zs)
    ratio = height_m / max(1e-9, width_m)
    return {
        "width_m": round(width_m, 6),
        "depth_m": round(depth_m, 6),
        "height_m": round(height_m, 6),
        "ratio": round(ratio, 6),
        "hw_ratio": round(ratio, 6),
        "xz_aspect": round(width_m / max(1e-9, height_m), 6),
        "is_squashed": ratio < 0.98,
    }


def normalize_head_proportions(rig, *, radii=ROUND_HEAD):
    """Normalize a built RicksCharacter's head mesh, ink hull, hair, and decals to exact `radii`.

    Eliminates horizontal oval squash (e.g. from legacy `HEAD` or `head_warp`) by
    vertex-normalizing the head silhouette to `ROUND_HEAD` (1:1) or `UPRIGHT_HEAD`
    (`H/W = 1.035`), resetting `rig.head.scale = (1, 1, 1)`, and re-conforming all
    expression decals smoothly onto the new ellipsoid surface.
    """
    if bpy is None:
        raise RuntimeError("normalize_head_proportions requires Blender 4.2 Python.")
    rx, ry, rz = (float(radii[0]), float(radii[1]), float(radii[2]))
    if min(rx, ry, rz) <= 0.0:
        raise ValueError(f"Head radii must be positive, got {radii!r}")

    rig.head.scale = (1.0, 1.0, 1.0)
    face = _find_head_mesh(rig)
    if face is None or face.type != "MESH":
        raise RuntimeError(f"Could not find head mesh for {rig.name!r}")
    face.scale = (1.0, 1.0, 1.0)

    cur_rx = max(abs(v.co.x) for v in face.data.vertices)
    cur_ry = max(abs(v.co.y) for v in face.data.vertices)
    cur_rz = max(abs(v.co.z) for v in face.data.vertices)
    sx = rx / max(1e-9, cur_rx)
    sy = ry / max(1e-9, cur_ry)
    sz = rz / max(1e-9, cur_rz)

    expr_set = set(getattr(rig, "expressions", {}).values())
    sweat = getattr(rig, "sweat", None)
    for obj in rig.head.children_recursive:
        if obj in expr_set or obj == sweat or obj.data is None:
            continue
        if obj.type == "MESH":
            obj.scale = (1.0, 1.0, 1.0)
            for v in obj.data.vertices:
                v.co.x *= sx
                v.co.y *= sy
                v.co.z *= sz
            obj.data.update()
        elif obj.type == "CURVE":
            obj.scale = (1.0, 1.0, 1.0)
            for spline in obj.data.splines:
                for p in spline.bezier_points:
                    for attr in ("co", "handle_left", "handle_right"):
                        pt = getattr(p, attr)
                        setattr(p, attr, (pt.x * sx, pt.y * sy, pt.z * sz))

    # Re-conform expression decals directly onto the normalized ellipsoid surface
    for expr_obj in expr_set:
        mesh_data = expr_obj.data
        if not mesh_data.uv_layers:
            for v in mesh_data.vertices:
                v.co.x *= sx
                v.co.z *= sz
                inside = max(0.035, 1.0 - (v.co.x / rx) ** 2 - (v.co.z / rz) ** 2)
                v.co.y = -ry * math.sqrt(inside) - 0.0033
        else:
            xs = [v.co.x for v in mesh_data.vertices]
            zs = [v.co.z for v in mesh_data.vertices]
            half_w = 0.5 * (max(xs) - min(xs)) * sx
            half_h = 0.5 * (max(zs) - min(zs)) * sz
            center_z = 0.5 * (max(zs) + min(zs)) * sz
            uv_layer = mesh_data.uv_layers[0]
            uv_by_vert = {}
            for loop in mesh_data.loops:
                uv_by_vert[loop.vertex_index] = tuple(uv_layer.data[loop.index].uv)
            for vi, vert in enumerate(mesh_data.vertices):
                u, v = uv_by_vert[vi]
                x = (2.0 * u - 1.0) * half_w
                z = (2.0 * v - 1.0) * half_h + center_z
                inside = max(0.035, 1.0 - (x / rx) ** 2 - (z / rz) ** 2)
                y = -ry * math.sqrt(inside) - 0.0033
                vert.co = (x, y, z)
        mesh_data.update()
        expr_obj.visible_shadow = False

    rig.head_radii = (rx, ry, rz)
    return measure_head_ratio(rig)


def _write_rgba_png(path, arr):
    """Write an (H, W, 4) uint8 RGBA array to a standard 8-bit PNG without PIL."""
    import struct
    import zlib
    import numpy as np

    rgba = np.ascontiguousarray(arr, dtype=np.uint8)
    if rgba.ndim != 3 or rgba.shape[2] != 4:
        raise ValueError(f"Expected (H, W, 4) RGBA array, got {rgba.shape}")
    h, w = rgba.shape[:2]
    raw = np.concatenate(
        [np.zeros((h, 1), dtype=np.uint8), rgba.reshape(h, w * 4)],
        axis=1,
    ).tobytes()

    def _chunk(tag, payload):
        crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, level=6))
        + _chunk(b"IEND", b"")
    )
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(png_bytes)
    return out_path


def _read_rgba_png(path):
    """Read an 8-bit non-interlaced PNG (RGBA/RGB/GA/G) into an (H, W, 4) uint8 array without PIL."""
    import struct
    import zlib
    import numpy as np

    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a valid PNG file: {path}")

    pos = 8
    w = h = bit_depth = color_type = interlace = None
    idat_parts = []
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            w, h, bit_depth, color_type, _comp, _flt, interlace = struct.unpack(">IIBBBBB", payload)
        elif tag == b"IDAT":
            idat_parts.append(payload)
        elif tag == b"IEND":
            break

    if w is None or h is None or bit_depth != 8 or interlace != 0:
        raise ValueError(f"Unsupported PNG header in {path}: bit_depth={bit_depth}, interlace={interlace}")
    channels_map = {0: 1, 2: 3, 4: 2, 6: 4}
    if color_type not in channels_map:
        raise ValueError(f"Unsupported PNG color_type={color_type} in {path} (install Pillow for indexed PNGs).")
    bpp = channels_map[color_type]
    stride = w * bpp
    raw = zlib.decompress(b"".join(idat_parts))

    out = np.zeros((h, stride), dtype=np.uint8)
    idx = 0
    for y in range(h):
        ftype = raw[idx]
        row = np.frombuffer(raw, dtype=np.uint8, count=stride, offset=idx + 1).copy()
        idx += 1 + stride
        prior = out[y - 1] if y > 0 else np.zeros(stride, dtype=np.uint8)
        if ftype == 0:
            out[y] = row
        elif ftype == 1:  # Sub
            for i in range(bpp, stride):
                row[i] = (int(row[i]) + int(row[i - bpp])) & 0xFF
            out[y] = row
        elif ftype == 2:  # Up
            out[y] = ((row.astype(np.uint16) + prior.astype(np.uint16)) & 0xFF).astype(np.uint8)
        elif ftype == 3:  # Average
            for i in range(stride):
                a = int(row[i - bpp]) if i >= bpp else 0
                b = int(prior[i])
                row[i] = (int(row[i]) + ((a + b) >> 1)) & 0xFF
            out[y] = row
        elif ftype == 4:  # Paeth
            for i in range(stride):
                a = int(row[i - bpp]) if i >= bpp else 0
                b = int(prior[i])
                c = int(prior[i - bpp]) if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (int(row[i]) + pr) & 0xFF
            out[y] = row
        else:
            raise ValueError(f"Unsupported PNG filter type {ftype} in {path}")

    img = out.reshape((h, w, bpp))
    if color_type == 6:
        return img
    rgba = np.full((h, w, 4), 255, dtype=np.uint8)
    if color_type == 2:
        rgba[:, :, :3] = img
    elif color_type == 4:
        rgba[:, :, :3] = img[:, :, 0:1]
        rgba[:, :, 3] = img[:, :, 1]
    else:  # color_type == 0
        rgba[:, :, :3] = img[:, :, 0:1]
    return rgba


def _load_rgba_array(source):
    """Load a Path, str, PIL Image, or numpy array into an (H, W, C) uint8 array.

    Uses Pillow when available and falls back cleanly to pure-NumPy PNG decoding
    inside stock Blender 4.2 Python where Pillow is not preinstalled.
    """
    import numpy as np

    if isinstance(source, np.ndarray):
        arr = source
        if arr.ndim == 2:
            arr = arr[:, :, None]
        return arr.astype(np.uint8, copy=False)

    try:
        from PIL import Image
    except ModuleNotFoundError:
        Image = None

    if isinstance(source, (str, Path)):
        if Image is not None:
            with Image.open(source) as im:
                return np.asarray(im.convert("RGBA"), dtype=np.uint8)
        return _read_rgba_png(source)

    if Image is not None and isinstance(source, Image.Image):
        return np.asarray(source.convert("RGBA"), dtype=np.uint8)
    raise TypeError(f"Unsupported image source type: {type(source)!r}")


def verify_upper_face_lock(img_closed, img_open, *, split_y_frac=0.55, max_abs_diff=0):
    """Prove pixel-locked upper-face speech (zero eye/brow flutter when lips move).

    Compares the upper face (`y < int(height * split_y_frac)`) between a closed-mouth
    expression and its open/talk counterpart. Pure-Python (NumPy; Pillow optional; no bpy).
    """
    if not 0.0 < float(split_y_frac) < 1.0:
        raise ValueError(f"split_y_frac must be in (0, 1), got {split_y_frac!r}")
    import numpy as np

    a = _load_rgba_array(img_closed)
    b = _load_rgba_array(img_open)
    if a.shape != b.shape:
        raise ValueError(f"Expression pair dimensions mismatch: {a.shape} vs {b.shape}")

    h, w = a.shape[:2]
    split_y = int(round(h * float(split_y_frac)))
    upper_diff = np.abs(a[:split_y].astype(np.int16) - b[:split_y].astype(np.int16))
    lower_diff = np.abs(a[split_y:].astype(np.int16) - b[split_y:].astype(np.int16))
    max_diff = int(upper_diff.max()) if upper_diff.size else 0
    nonzero_pixels = int(np.any(upper_diff > int(max_abs_diff), axis=-1).sum())
    lower_changed = int(np.any(lower_diff > 0, axis=-1).sum())
    passed = max_diff <= int(max_abs_diff)
    return {
        "pass": passed,
        "locked": passed,
        "max_diff": max_diff,
        "max_abs_diff": int(max_abs_diff),
        "nonzero_pixels": nonzero_pixels,
        "total_upper_pixels": int(split_y * w),
        "lower_changed_pixels": lower_changed,
        "split_y_px": split_y,
        "split_y_frac": float(split_y_frac),
        "size": (int(w), int(h)),
    }


def _hex_rgba_u8(hex_color, alpha=255):
    c = hex_color.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), int(alpha))


def _draw_pill_curve(draw, pts, width, fill):
    w = max(1, int(round(width)))
    pts = [(float(x), float(y)) for x, y in pts]
    draw.line(pts, fill=fill, width=w, joint="curve")
    r = w / 2.0
    for x, y in (pts[0], pts[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=fill)


def _cubic_pts(p0, p1, p2, p3, steps=32):
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1.0 - t
        b0, b1, b2, b3 = u ** 3, 3 * u * u * t, 3 * u * t * t, t ** 3
        out.append((
            b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0],
            b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1],
        ))
    return out


def _render_expression_pair_numpy(
    out_dir,
    name,
    *,
    mood,
    sz,
    split_y_frac,
    ink_rgba,
    sclera_rgba,
    lid_rgba,
    mouth_rgba,
    tongue_rgba,
    teeth_rgba,
):
    """Crisp 2x-supersampled pure-NumPy fallback renderer (zero PIL dependency)."""
    import numpy as np

    ss = 2
    W = H = sz * ss
    split_y_px = int(round(sz * float(split_y_frac)))

    def _rgba_f(c):
        return np.array([c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, c[3] / 255.0], dtype=np.float32)

    ink_f = _rgba_f(ink_rgba)
    sclera_f = _rgba_f(sclera_rgba)
    lid_f = _rgba_f(lid_rgba)
    mouth_f = _rgba_f(mouth_rgba)
    tongue_f = _rgba_f(tongue_rgba)
    teeth_f = _rgba_f(teeth_rgba)

    def _blend_over(dst, y0, y1, x0, x1, color_f, cov):
        sa = np.clip(cov, 0.0, 1.0) * color_f[3]
        if not np.any(sa > 0.0):
            return
        sub = dst[y0:y1, x0:x1]
        da = sub[:, :, 3]
        out_a = sa + da * (1.0 - sa)
        safe = np.where(out_a > 1e-6, out_a, 1.0)
        for ch in range(3):
            sub[:, :, ch] = (color_f[ch] * sa + sub[:, :, ch] * da * (1.0 - sa)) / safe
        sub[:, :, 3] = out_a

    def _alpha_composite_arr(base_f, over_f):
        out = base_f.copy()
        sa = over_f[:, :, 3]
        da = out[:, :, 3]
        out_a = sa + da * (1.0 - sa)
        safe = np.where(out_a > 1e-6, out_a, 1.0)
        for ch in range(3):
            out[:, :, ch] = (over_f[:, :, ch] * sa + out[:, :, ch] * da * (1.0 - sa)) / safe
        out[:, :, 3] = out_a
        return out

    def _bbox(x0, y0, x1, y1, pad=2):
        ix0 = max(0, int(math.floor(x0 - pad)))
        iy0 = max(0, int(math.floor(y0 - pad)))
        ix1 = min(W, int(math.ceil(x1 + pad)))
        iy1 = min(H, int(math.ceil(y1 + pad)))
        return ix0, iy0, ix1, iy1

    def _ellipse_cov(cx, cy, rx, ry, ix0, iy0, ix1, iy1):
        xs = np.arange(ix0, ix1, dtype=np.float32) + 0.5
        ys = np.arange(iy0, iy1, dtype=np.float32) + 0.5
        dx = (xs[None, :] - cx) / max(1e-3, rx)
        dy = (ys[:, None] - cy) / max(1e-3, ry)
        dist = np.sqrt(dx * dx + dy * dy)
        aa = 1.0 / max(1.0, min(rx, ry))
        return np.clip((1.0 - dist) / max(1e-4, aa) + 0.5, 0.0, 1.0)

    def _fill_ellipse(dst, cx, cy, rx, ry, color_f):
        ix0, iy0, ix1, iy1 = _bbox(cx - rx, cy - ry, cx + rx, cy + ry)
        if ix1 <= ix0 or iy1 <= iy0:
            return
        cov = _ellipse_cov(cx, cy, rx, ry, ix0, iy0, ix1, iy1)
        _blend_over(dst, iy0, iy1, ix0, ix1, color_f, cov)

    def _stroke_ellipse(dst, cx, cy, rx, ry, stroke_w, color_f):
        half_w = 0.5 * stroke_w
        ix0, iy0, ix1, iy1 = _bbox(cx - rx - half_w, cy - ry - half_w, cx + rx + half_w, cy + ry + half_w)
        if ix1 <= ix0 or iy1 <= iy0:
            return
        outer = _ellipse_cov(cx, cy, rx + half_w, ry + half_w, ix0, iy0, ix1, iy1)
        inner = _ellipse_cov(cx, cy, max(0.5, rx - half_w), max(0.5, ry - half_w), ix0, iy0, ix1, iy1)
        _blend_over(dst, iy0, iy1, ix0, ix1, color_f, np.clip(outer - inner, 0.0, 1.0))

    def _fill_rect(dst, x0, y0, x1, y1, color_f):
        ix0, iy0, ix1, iy1 = _bbox(x0, y0, x1, y1, pad=0)
        if ix1 <= ix0 or iy1 <= iy0:
            return
        cov = np.ones((iy1 - iy0, ix1 - ix0), dtype=np.float32)
        _blend_over(dst, iy0, iy1, ix0, ix1, color_f, cov)

    def _pill_curve(dst, pts, width, color_f):
        rad = max(0.5, 0.5 * float(width))
        pxs = [p[0] for p in pts]
        pys = [p[1] for p in pts]
        ix0, iy0, ix1, iy1 = _bbox(min(pxs) - rad, min(pys) - rad, max(pxs) + rad, max(pys) + rad)
        if ix1 <= ix0 or iy1 <= iy0:
            return
        xs = np.arange(ix0, ix1, dtype=np.float32)[None, :] + 0.5
        ys = np.arange(iy0, iy1, dtype=np.float32)[:, None] + 0.5
        min_d2 = np.full((iy1 - iy0, ix1 - ix0), np.inf, dtype=np.float32)
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            vx, vy = bx - ax, by - ay
            l2 = vx * vx + vy * vy
            if l2 < 1e-6:
                d2 = (xs - ax) ** 2 + (ys - ay) ** 2
            else:
                t = np.clip(((xs - ax) * vx + (ys - ay) * vy) / l2, 0.0, 1.0)
                d2 = (xs - (ax + t * vx)) ** 2 + (ys - (ay + t * vy)) ** 2
            min_d2 = np.minimum(min_d2, d2)
        dist = np.sqrt(min_d2)
        cov = np.clip(rad - dist + 0.5, 0.0, 1.0)
        _blend_over(dst, iy0, iy1, ix0, ix1, color_f, cov)

    def draw_eye(canvas, cx, cy, *, r_outer, ring_w, pupil_r, dx=0.0, dy=0.0, lid_top=0.0, lid_bot=0.0):
        _fill_ellipse(canvas, cx, cy, r_outer, r_outer, ink_f)
        r_in = max(1.0, r_outer - ring_w)
        _fill_ellipse(canvas, cx, cy, r_in, r_in, sclera_f)

        layer = np.zeros((H, W, 4), dtype=np.float32)
        px, py = cx + dx, cy + dy
        _fill_ellipse(layer, px, py, pupil_r, pupil_r, ink_f)
        cr = max(3.0, pupil_r * 0.28)
        _fill_ellipse(layer, px - pupil_r * 0.35, py - pupil_r * 0.35, cr, cr, sclera_f)
        if lid_top > 0.0:
            ly = (cy - r_in) + (2.0 * r_in) * lid_top
            _fill_rect(layer, cx - r_outer, cy - r_outer, cx + r_outer, ly, lid_f)
            _fill_rect(layer, cx - r_outer, ly - ring_w * 0.45, cx + r_outer, ly + ring_w * 0.45, ink_f)
        if lid_bot > 0.0:
            ly = (cy + r_in) - (2.0 * r_in) * lid_bot
            _fill_rect(layer, cx - r_outer, ly, cx + r_outer, cy + r_outer, lid_f)
            _fill_rect(layer, cx - r_outer, ly - ring_w * 0.45, cx + r_outer, ly + ring_w * 0.45, ink_f)

        ix0, iy0, ix1, iy1 = _bbox(cx - r_in, cy - r_in, cx + r_in, cy + r_in)
        mask = np.zeros((H, W), dtype=np.float32)
        if ix1 > ix0 and iy1 > iy0:
            mask[iy0:iy1, ix0:ix1] = _ellipse_cov(cx, cy, r_in, r_in, ix0, iy0, ix1, iy1)
        layer[:, :, 3] *= mask
        canvas[:] = _alpha_composite_arr(canvas, layer)
        _stroke_ellipse(canvas, cx, cy, r_outer - ring_w * 0.5, r_outer - ring_w * 0.5, ring_w, ink_f)

    # 1. Upper face ONCE strictly above split_y_frac
    upper_hi = np.zeros((H, W, 4), dtype=np.float32)
    cx_l, cx_r = W * 0.325, W * 0.675
    eye_y = H * 0.405
    r_eye = W * 0.112
    ring_w = max(4.0, W * 0.022)
    pupil_r = W * 0.043
    brow_w = max(5.0, W * 0.032)

    if mood == "neutral":
        for s, cx in ((-1, cx_l), (1, cx_r)):
            draw_eye(upper_hi, cx, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r, dy=H * 0.004)
            _pill_curve(upper_hi, _cubic_pts(
                (cx - W * 0.095, H * 0.250 + s * H * 0.004), (cx - W * 0.03, H * 0.224),
                (cx + W * 0.03, H * 0.224), (cx + W * 0.095, H * 0.250 - s * H * 0.004)), brow_w, ink_f)
    elif mood == "happy":
        for s, cx in ((-1, cx_l), (1, cx_r)):
            draw_eye(upper_hi, cx, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r * 1.05, lid_bot=0.22)
            _pill_curve(upper_hi, _cubic_pts(
                (cx - W * 0.095, H * 0.238), (cx - W * 0.03, H * 0.198),
                (cx + W * 0.03, H * 0.198), (cx + W * 0.095, H * 0.238)), brow_w, ink_f)
    elif mood == "smug":
        for s, cx in ((-1, cx_l), (1, cx_r)):
            draw_eye(upper_hi, cx, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r * 0.92,
                     dx=W * 0.015, lid_top=0.40)
            _pill_curve(upper_hi, _cubic_pts(
                (cx - W * 0.095, H * (0.242 if s < 0 else 0.220)),
                (cx, H * (0.226 if s < 0 else 0.205)),
                (cx + W * 0.05, H * (0.232 if s < 0 else 0.214)),
                (cx + W * 0.095, H * (0.252 if s < 0 else 0.232))), brow_w, ink_f)
    elif mood == "skeptical":
        draw_eye(upper_hi, cx_l, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r * 0.90,
                 dx=W * 0.025, lid_top=0.35)
        draw_eye(upper_hi, cx_r, eye_y, r_outer=r_eye * 1.04, ring_w=ring_w, pupil_r=pupil_r * 0.90,
                 dx=W * 0.025, lid_top=0.10)
        _pill_curve(upper_hi, _cubic_pts(
            (cx_l - W * 0.095, H * 0.255), (cx_l, H * 0.245),
            (cx_l + W * 0.05, H * 0.250), (cx_l + W * 0.095, H * 0.268)), brow_w, ink_f)
        _pill_curve(upper_hi, _cubic_pts(
            (cx_r - W * 0.095, H * 0.225), (cx_r - W * 0.02, H * 0.185),
            (cx_r + W * 0.04, H * 0.185), (cx_r + W * 0.095, H * 0.228)), brow_w, ink_f)
    elif mood == "surprised":
        for s, cx in ((-1, cx_l), (1, cx_r)):
            draw_eye(upper_hi, cx, eye_y, r_outer=r_eye * 1.08, ring_w=ring_w, pupil_r=pupil_r * 0.72)
            _pill_curve(upper_hi, _cubic_pts(
                (cx - W * 0.095, H * 0.215), (cx - W * 0.03, H * 0.175),
                (cx + W * 0.03, H * 0.175), (cx + W * 0.095, H * 0.215)), brow_w, ink_f)
    elif mood == "worried":
        for s, cx in ((-1, cx_l), (1, cx_r)):
            draw_eye(upper_hi, cx, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r * 0.88, dy=H * 0.01)
            _pill_curve(upper_hi, _cubic_pts(
                (cx - W * 0.095, H * (0.265 if s < 0 else 0.218)),
                (cx - W * 0.03, H * 0.236),
                (cx + W * 0.03, H * 0.236),
                (cx + W * 0.095, H * (0.218 if s < 0 else 0.265))), brow_w, ink_f)

    def _downsample_2x(arr_f):
        # Premultiply -> 2x2 box average -> unpremultiply for crisp fringe-free AA
        pm = arr_f.copy()
        pm[:, :, :3] *= pm[:, :, 3:4]
        ds = pm.reshape(sz, ss, sz, ss, 4).mean(axis=(1, 3))
        a = ds[:, :, 3:4]
        safe = np.where(a > 1e-6, a, 1.0)
        ds[:, :, :3] = np.clip(ds[:, :, :3] / safe, 0.0, 1.0)
        ds[:, :, 3] = np.clip(ds[:, :, 3], 0.0, 1.0)
        return ds

    upper_down = _downsample_2x(upper_hi)

    def _build_mouth_layer(is_open):
        layer_hi = np.zeros((H, W, 4), dtype=np.float32)
        mx, my = W * 0.50, H * 0.72
        mw = W * 0.15
        stroke = max(5.0, W * 0.026)
        if not is_open:
            if mood in ("happy", "smug"):
                _pill_curve(layer_hi, _cubic_pts(
                    (mx - mw, my - H * 0.015), (mx - mw * 0.4, my + H * 0.045),
                    (mx + mw * 0.4, my + H * 0.045), (mx + mw, my - H * 0.025)), stroke, ink_f)
            elif mood in ("worried", "skeptical"):
                _pill_curve(layer_hi, _cubic_pts(
                    (mx - mw * 0.85, my + H * 0.020), (mx - mw * 0.3, my - H * 0.018),
                    (mx + mw * 0.3, my - H * 0.018), (mx + mw * 0.85, my + H * 0.020)), stroke, ink_f)
            elif mood == "surprised":
                r_o = W * 0.055
                _fill_ellipse(layer_hi, mx, my, r_o, r_o * 1.1, mouth_f)
                _stroke_ellipse(layer_hi, mx, my, r_o, r_o * 1.1, stroke, ink_f)
            else:
                _pill_curve(layer_hi, _cubic_pts(
                    (mx - mw * 0.82, my), (mx - mw * 0.3, my + H * 0.014),
                    (mx + mw * 0.3, my + H * 0.014), (mx + mw * 0.82, my)), stroke, ink_f)
        else:
            rx_m = W * (0.105 if mood != "surprised" else 0.088)
            ry_m = H * (0.078 if mood != "surprised" else 0.095)
            cy_m = my + ry_m * 0.15
            _fill_ellipse(layer_hi, mx, cy_m, rx_m, ry_m * 0.90, mouth_f)
            interior = np.zeros((H, W, 4), dtype=np.float32)
            _fill_rect(interior, mx - rx_m, my - ry_m * 0.80, mx + rx_m, my - ry_m * 0.30, teeth_f)
            _fill_ellipse(interior, mx, my + ry_m * 0.65, rx_m * 0.65, ry_m * 0.50, tongue_f)
            ix0, iy0, ix1, iy1 = _bbox(mx - rx_m, cy_m - ry_m * 0.90, mx + rx_m, cy_m + ry_m * 0.90)
            m_mask = np.zeros((H, W), dtype=np.float32)
            if ix1 > ix0 and iy1 > iy0:
                m_mask[iy0:iy1, ix0:ix1] = _ellipse_cov(mx, cy_m, rx_m, ry_m * 0.90, ix0, iy0, ix1, iy1)
            interior[:, :, 3] *= m_mask
            layer_hi[:] = _alpha_composite_arr(layer_hi, interior)
            _stroke_ellipse(layer_hi, mx, cy_m, rx_m, ry_m * 0.90, stroke, ink_f)

        mouth_down = _downsample_2x(layer_hi)
        mouth_down[:split_y_px, :, :] = 0.0
        return mouth_down

    def _compose_u8(mouth_down):
        comp = _alpha_composite_arr(upper_down, mouth_down)
        arr = np.round(np.clip(comp, 0.0, 1.0) * 255.0).astype(np.uint8)
        zero_a = arr[:, :, 3] <= 2
        arr[zero_a, 0:3] = ink_rgba[:3]
        arr[zero_a, 3] = 0
        return arr

    closed_arr = _compose_u8(_build_mouth_layer(False))
    talk_arr = _compose_u8(_build_mouth_layer(True))
    lock = verify_upper_face_lock(closed_arr, talk_arr, split_y_frac=split_y_frac, max_abs_diff=0)
    if not lock["pass"]:
        raise RuntimeError(f"Pixel-locked upper face assertion failed: {lock}")

    closed_path = talk_path = None
    if out_dir is not None:
        folder = Path(out_dir)
        folder.mkdir(parents=True, exist_ok=True)
        closed_path = _write_rgba_png(folder / f"{name}_closed.png", closed_arr)
        talk_path = _write_rgba_png(folder / f"{name}_talk.png", talk_arr)

    return {
        "closed": closed_path,
        "talk": talk_path,
        "closed_image": closed_arr,
        "talk_image": talk_arr,
        "lock": lock,
    }


def render_pixel_locked_expression_pair(
    out_dir,
    name,
    *,
    mood="neutral",
    size=1024,
    split_y_frac=0.55,
    outline_color="#08080C",
    sclera_color="#FFFFFF",
    face_lid_color=PAPER_WHITE_FACE,
    mouth_fill="#3A151B",
    tongue_color="#E86A7A",
    teeth_color="#FFFFFF",
    upper_drawer=None,
    mouth_closed_drawer=None,
    mouth_open_drawer=None,
):
    """Render a 2x-supersampled closed/talk RGBA expression pair with 0-diff upper-face lock.

    Draws eyes and eyebrows ONCE in the upper region (`y < split_y_frac`) and
    composites closed vs open mouths strictly below `split_y_frac` after
    downsampling, mathematically guaranteeing 0 pixel difference on `y < split_y_px`
    so eyes never blink or flutter during dialogue lip-sync.

    Uses Pillow when installed and falls back automatically to a pure-NumPy + stdlib
    PNG renderer inside stock Blender 4.2 Python (no `PIL` required). Pass
    `out_dir=None` to skip disk writes.
    """
    import numpy as np

    if not 0.35 <= float(split_y_frac) <= 0.75:
        raise ValueError(f"split_y_frac should be in [0.35, 0.75], got {split_y_frac!r}")
    valid_moods = ("neutral", "happy", "smug", "skeptical", "surprised", "worried")
    if upper_drawer is None and mood not in valid_moods:
        raise ValueError(f"Unknown mood {mood!r}; expected one of {valid_moods}")

    sz = int(size)
    ink_rgba = _hex_rgba_u8(outline_color, 255)
    sclera_rgba = _hex_rgba_u8(sclera_color, 255)
    lid_rgba = _hex_rgba_u8(face_lid_color, 255)
    mouth_rgba = _hex_rgba_u8(mouth_fill, 255)
    tongue_rgba = _hex_rgba_u8(tongue_color, 255)
    teeth_rgba = _hex_rgba_u8(teeth_color, 255)

    try:
        from PIL import Image, ImageChops, ImageDraw
    except ModuleNotFoundError:
        if any(fn is not None for fn in (upper_drawer, mouth_closed_drawer, mouth_open_drawer)):
            raise RuntimeError("Custom PIL ImageDraw callbacks require Pillow (PIL).")
        return _render_expression_pair_numpy(
            out_dir,
            name,
            mood=mood,
            sz=sz,
            split_y_frac=split_y_frac,
            ink_rgba=ink_rgba,
            sclera_rgba=sclera_rgba,
            lid_rgba=lid_rgba,
            mouth_rgba=mouth_rgba,
            tongue_rgba=tongue_rgba,
            teeth_rgba=teeth_rgba,
        )

    ss = 2
    W = H = sz * ss
    split_y_px = int(round(sz * float(split_y_frac)))
    bg_transparent = _hex_rgba_u8(outline_color, 0)

    def draw_eye(canvas, cx, cy, *, r_outer, ring_w, pupil_r, dx=0.0, dy=0.0, lid_top=0.0, lid_bot=0.0):
        dr = ImageDraw.Draw(canvas)
        dr.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer), fill=ink_rgba)
        r_in = r_outer - ring_w
        dr.ellipse((cx - r_in, cy - r_in, cx + r_in, cy + r_in), fill=sclera_rgba)

        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ed = ImageDraw.Draw(layer)
        px, py = cx + dx, cy + dy
        ed.ellipse((px - pupil_r, py - pupil_r, px + pupil_r, py + pupil_r), fill=ink_rgba)
        cr = max(3.0, pupil_r * 0.28)
        ed.ellipse(
            (px - pupil_r * 0.35 - cr, py - pupil_r * 0.35 - cr,
             px - pupil_r * 0.35 + cr, py - pupil_r * 0.35 + cr),
            fill=sclera_rgba,
        )
        if lid_top > 0.0:
            ly = (cy - r_in) + (2.0 * r_in) * lid_top
            ed.rectangle((cx - r_outer, cy - r_outer, cx + r_outer, ly), fill=lid_rgba)
            ed.rectangle((cx - r_outer, ly - ring_w * 0.45, cx + r_outer, ly + ring_w * 0.45), fill=ink_rgba)
        if lid_bot > 0.0:
            ly = (cy + r_in) - (2.0 * r_in) * lid_bot
            ed.rectangle((cx - r_outer, ly, cx + r_outer, cy + r_outer), fill=lid_rgba)
            ed.rectangle((cx - r_outer, ly - ring_w * 0.45, cx + r_outer, ly + ring_w * 0.45), fill=ink_rgba)

        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).ellipse((cx - r_in, cy - r_in, cx + r_in, cy + r_in), fill=255)
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
        canvas.alpha_composite(layer)
        ImageDraw.Draw(canvas).ellipse(
            (cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer),
            outline=ink_rgba,
            width=max(1, int(round(ring_w))),
        )

    # 1. Draw upper face ONCE strictly above split_y_frac
    upper_hi = Image.new("RGBA", (W, H), bg_transparent)
    ud = ImageDraw.Draw(upper_hi)
    if upper_drawer is not None:
        upper_drawer(ud, W, H)
    else:
        cx_l, cx_r = W * 0.325, W * 0.675
        eye_y = H * 0.405
        r_eye = W * 0.112
        ring_w = max(4.0, W * 0.022)
        pupil_r = W * 0.043
        brow_w = max(5.0, W * 0.032)
        if mood == "neutral":
            for s, cx in ((-1, cx_l), (1, cx_r)):
                draw_eye(upper_hi, cx, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r, dy=H * 0.004)
                ud = ImageDraw.Draw(upper_hi)
                _draw_pill_curve(ud, _cubic_pts(
                    (cx - W * 0.095, H * 0.250 + s * H * 0.004), (cx - W * 0.03, H * 0.224),
                    (cx + W * 0.03, H * 0.224), (cx + W * 0.095, H * 0.250 - s * H * 0.004)), brow_w, ink_rgba)
        elif mood == "happy":
            for s, cx in ((-1, cx_l), (1, cx_r)):
                draw_eye(upper_hi, cx, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r * 1.05, lid_bot=0.22)
                ud = ImageDraw.Draw(upper_hi)
                _draw_pill_curve(ud, _cubic_pts(
                    (cx - W * 0.095, H * 0.238), (cx - W * 0.03, H * 0.198),
                    (cx + W * 0.03, H * 0.198), (cx + W * 0.095, H * 0.238)), brow_w, ink_rgba)
        elif mood == "smug":
            for s, cx in ((-1, cx_l), (1, cx_r)):
                draw_eye(upper_hi, cx, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r * 0.92,
                         dx=W * 0.015, lid_top=0.40)
                ud = ImageDraw.Draw(upper_hi)
                _draw_pill_curve(ud, _cubic_pts(
                    (cx - W * 0.095, H * (0.242 if s < 0 else 0.220)),
                    (cx, H * (0.226 if s < 0 else 0.205)),
                    (cx + W * 0.05, H * (0.232 if s < 0 else 0.214)),
                    (cx + W * 0.095, H * (0.252 if s < 0 else 0.232))), brow_w, ink_rgba)
        elif mood == "skeptical":
            draw_eye(upper_hi, cx_l, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r * 0.90,
                     dx=W * 0.025, lid_top=0.35)
            draw_eye(upper_hi, cx_r, eye_y, r_outer=r_eye * 1.04, ring_w=ring_w, pupil_r=pupil_r * 0.90,
                     dx=W * 0.025, lid_top=0.10)
            ud = ImageDraw.Draw(upper_hi)
            _draw_pill_curve(ud, _cubic_pts(
                (cx_l - W * 0.095, H * 0.255), (cx_l, H * 0.245),
                (cx_l + W * 0.05, H * 0.250), (cx_l + W * 0.095, H * 0.268)), brow_w, ink_rgba)
            _draw_pill_curve(ud, _cubic_pts(
                (cx_r - W * 0.095, H * 0.225), (cx_r - W * 0.02, H * 0.185),
                (cx_r + W * 0.04, H * 0.185), (cx_r + W * 0.095, H * 0.228)), brow_w, ink_rgba)
        elif mood == "surprised":
            for s, cx in ((-1, cx_l), (1, cx_r)):
                draw_eye(upper_hi, cx, eye_y, r_outer=r_eye * 1.08, ring_w=ring_w, pupil_r=pupil_r * 0.72)
                ud = ImageDraw.Draw(upper_hi)
                _draw_pill_curve(ud, _cubic_pts(
                    (cx - W * 0.095, H * 0.215), (cx - W * 0.03, H * 0.175),
                    (cx + W * 0.03, H * 0.175), (cx + W * 0.095, H * 0.215)), brow_w, ink_rgba)
        elif mood == "worried":
            for s, cx in ((-1, cx_l), (1, cx_r)):
                draw_eye(upper_hi, cx, eye_y, r_outer=r_eye, ring_w=ring_w, pupil_r=pupil_r * 0.88, dy=H * 0.01)
                ud = ImageDraw.Draw(upper_hi)
                _draw_pill_curve(ud, _cubic_pts(
                    (cx - W * 0.095, H * (0.265 if s < 0 else 0.218)),
                    (cx - W * 0.03, H * 0.236),
                    (cx + W * 0.03, H * 0.236),
                    (cx + W * 0.095, H * (0.218 if s < 0 else 0.265))), brow_w, ink_rgba)

    upper_down = upper_hi.resize((sz, sz), Image.Resampling.LANCZOS)

    def _build_mouth_layer(is_open):
        layer_hi = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        md = ImageDraw.Draw(layer_hi)
        if not is_open and mouth_closed_drawer is not None:
            mouth_closed_drawer(md, W, H)
        elif is_open and mouth_open_drawer is not None:
            mouth_open_drawer(md, W, H)
        else:
            mx = W * 0.50
            my = H * 0.72
            mw = W * 0.15
            stroke = max(5.0, W * 0.026)
            if not is_open:
                if mood in ("happy", "smug"):
                    _draw_pill_curve(md, _cubic_pts(
                        (mx - mw, my - H * 0.015), (mx - mw * 0.4, my + H * 0.045),
                        (mx + mw * 0.4, my + H * 0.045), (mx + mw, my - H * 0.025)), stroke, ink_rgba)
                elif mood in ("worried", "skeptical"):
                    _draw_pill_curve(md, _cubic_pts(
                        (mx - mw * 0.85, my + H * 0.020), (mx - mw * 0.3, my - H * 0.018),
                        (mx + mw * 0.3, my - H * 0.018), (mx + mw * 0.85, my + H * 0.020)), stroke, ink_rgba)
                elif mood == "surprised":
                    r_o = W * 0.055
                    md.ellipse((mx - r_o, my - r_o * 1.1, mx + r_o, my + r_o * 1.1),
                               fill=mouth_rgba, outline=ink_rgba, width=max(4, int(round(stroke))))
                else:
                    _draw_pill_curve(md, _cubic_pts(
                        (mx - mw * 0.82, my), (mx - mw * 0.3, my + H * 0.014),
                        (mx + mw * 0.3, my + H * 0.014), (mx + mw * 0.82, my)), stroke, ink_rgba)
            else:
                rx_m = W * (0.105 if mood != "surprised" else 0.088)
                ry_m = H * (0.078 if mood != "surprised" else 0.095)
                box = (mx - rx_m, my - ry_m * 0.75, mx + rx_m, my + ry_m * 1.05)
                md.ellipse(box, fill=mouth_rgba)
                # Clipped upper teeth + lower tongue inside mouth interior
                interior = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                idraw = ImageDraw.Draw(interior)
                idraw.rectangle((mx - rx_m, my - ry_m * 0.8, mx + rx_m, my - ry_m * 0.30), fill=teeth_rgba)
                idraw.ellipse((mx - rx_m * 0.65, my + ry_m * 0.15, mx + rx_m * 0.65, my + ry_m * 1.15),
                              fill=tongue_rgba)
                m_mask = Image.new("L", (W, H), 0)
                ImageDraw.Draw(m_mask).ellipse(box, fill=255)
                interior.putalpha(ImageChops.multiply(interior.getchannel("A"), m_mask))
                layer_hi.alpha_composite(interior)
                ImageDraw.Draw(layer_hi).ellipse(box, outline=ink_rgba, width=max(4, int(round(stroke))))

        layer_down = layer_hi.resize((sz, sz), Image.Resampling.LANCZOS)
        # Strictly zero any Lanczos ringing above split_y_px so upper face is 100% locked
        arr = np.asarray(layer_down, dtype=np.uint8).copy()
        arr[:split_y_px, :, :] = 0
        return Image.fromarray(arr, mode="RGBA")

    def _compose_with_dark_bleed(mouth_layer):
        out = upper_down.copy()
        out.alpha_composite(mouth_layer)
        arr = np.asarray(out, dtype=np.uint8).copy()
        zero_a = arr[:, :, 3] <= 2
        arr[zero_a, 0:3] = ink_rgba[:3]
        arr[zero_a, 3] = 0
        return Image.fromarray(arr, mode="RGBA")

    closed_img = _compose_with_dark_bleed(_build_mouth_layer(False))
    talk_img = _compose_with_dark_bleed(_build_mouth_layer(True))
    lock = verify_upper_face_lock(closed_img, talk_img, split_y_frac=split_y_frac, max_abs_diff=0)
    if not lock["pass"]:
        raise RuntimeError(f"Pixel-locked upper face assertion failed: {lock}")

    closed_path = talk_path = None
    if out_dir is not None:
        folder = Path(out_dir)
        folder.mkdir(parents=True, exist_ok=True)
        closed_path = folder / f"{name}_closed.png"
        talk_path = folder / f"{name}_talk.png"
        closed_img.save(closed_path, "PNG")
        talk_img.save(talk_path, "PNG")

    return {
        "closed": closed_path,
        "talk": talk_path,
        "closed_image": closed_img,
        "talk_image": talk_img,
        "lock": lock,
    }


def setup_chiaroscuro_lighting(
    scene,
    col,
    *,
    world_color="#182236",
    world_strength=0.16,
    key_watts=180.0,
    fill_watts=30.0,
    rim_watts=75.0,
    key_color="#FFD49A",
    fill_color="#89B2FF",
    rim_color="#9BC4FF",
    key_loc=(1.9, -2.0, 2.7),
    fill_loc=(-2.0, -1.6, 1.8),
    rim_loc=(-1.6, 1.6, 2.2),
    target=(0.0, 0.0, 0.9),
    key_size=0.95,
    fill_size=1.6,
    rim_size=0.85,
    gtao_distance=0.55,
    prefix="Chiaroscuro",
    sun_energy=0.0,
    sun_color="#FFE8C8",
):
    """Configure 6:1 directional chiaroscuro lighting + EEVEE Next Contact AO.

    Installs a low-ambient cool slate World (zero flat ambient wash), enables
    `AMBIENT_OCCLUSION_ONLY` contact AO (`gtao_distance`), adds one shadow-casting
    warm directional key and a shadowless cool fill at `key_watts : fill_watts`
    (default 180 W : 30 W = 6:1), plus an optional shadowless cool rim.
    """
    if bpy is None:
        raise RuntimeError("setup_chiaroscuro_lighting requires Blender 4.2 Python.")
    eevee = scene.eevee
    eevee.use_raytracing = False
    if hasattr(eevee, "fast_gi_method"):
        eevee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
    if hasattr(eevee, "gtao_distance"):
        eevee.gtao_distance = float(gtao_distance)
    eevee.shadow_ray_count = 2
    eevee.shadow_step_count = 6

    world = bpy.data.worlds.new(f"{prefix} | Slate World")
    world.use_nodes = True
    wn, wl = world.node_tree.nodes, world.node_tree.links
    wn.clear()
    bg = wn.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = look.rgba(world_color)
    bg.inputs["Strength"].default_value = float(world_strength)
    wout = wn.new("ShaderNodeOutputWorld")
    wl.new(bg.outputs[0], wout.inputs["Surface"])
    scene.world = world

    key = make_ricks_light(f"{prefix} | Warm Key", col, key_loc, target, key_color, float(key_watts), size=key_size)
    key.data.use_shadow = True
    key.data.use_shadow_jitter = False

    fill = make_ricks_light(f"{prefix} | Cool Fill", col, fill_loc, target, fill_color, float(fill_watts), size=fill_size)
    fill.data.use_shadow = False

    rim = None
    if rim_watts and float(rim_watts) > 0.0:
        rim = make_ricks_light(f"{prefix} | Cool Rim", col, rim_loc, target, rim_color, float(rim_watts), size=rim_size)
        rim.data.use_shadow = False

    sun = None
    if sun_energy and float(sun_energy) > 0.0:
        sun = look.make_sun(scene, f"{prefix} | Sun", azimuth=128, elevation=40,
                            energy=float(sun_energy), color=sun_color, shadows=True)

    return {
        "world": world,
        "key": key,
        "fill": fill,
        "rim": rim,
        "sun": sun,
        "key_to_fill_ratio": float(key_watts) / max(1e-6, float(fill_watts)),
    }


def make_subtle_light_cone(name, col, top, bottom, narrow, wide, color="#FFC970", *,
                           peak_alpha=0.013, emission_strength=1.15, segments=20):
    """Volume-free feathered light cone strictly clamped to `peak_alpha <= 0.015`.

    Replaces milky high-alpha cones with a soft LayerWeight + vertical Z fade
    that preserves dark chiaroscuro contrast under AgX.
    """
    if bpy is None:
        raise RuntimeError("make_subtle_light_cone requires Blender 4.2 Python.")
    clamped = min(0.015, max(0.001, float(peak_alpha)))
    m = emission(name, color, float(emission_strength))
    m.surface_render_method = "BLENDED"
    n, l = m.node_tree.nodes, m.node_tree.links
    em = next(nd for nd in n if nd.type == "EMISSION")
    out = next(nd for nd in n if nd.type == "OUTPUT_MATERIAL")
    geom = n.new("ShaderNodeLayerWeight")
    geom.inputs["Blend"].default_value = 0.45
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.85
    ramp.color_ramp.elements[1].color = (clamped, clamped, clamped, 1.0)
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    fade = n.new("ShaderNodeMapRange")
    fade.interpolation_type = "SMOOTHERSTEP"
    fade.inputs["From Min"].default_value = 0.0
    fade.inputs["From Max"].default_value = 0.95
    fade.inputs["To Min"].default_value = 0.15
    fade.inputs["To Max"].default_value = 1.0
    mul = n.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    clear = n.new("ShaderNodeBsdfTransparent")
    mix = n.new("ShaderNodeMixShader")
    l.new(geom.outputs["Facing"], ramp.inputs[0])
    l.new(tc.outputs["Generated"], sep.inputs[0])
    l.new(sep.outputs["Z"], fade.inputs["Value"])
    l.new(ramp.outputs[0], mul.inputs[0])
    l.new(fade.outputs[0], mul.inputs[1])
    l.new(mul.outputs[0], mix.inputs[0])
    l.new(clear.outputs[0], mix.inputs[1])
    l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], out.inputs[0])
    top_v, bot_v = Vector(top), Vector(bottom)
    obj = cylinder(name, col, (top_v + bot_v) / 2, wide, (top_v - bot_v).length, m,
                   r2=narrow, length_segments=int(segments))
    obj.rotation_euler = (top_v - bot_v).to_track_quat("Z", "Y").to_euler()
    look.mark_role(obj, "wisp")
    return obj


def make_plank_wood_material(name, base_hex="#7D5335", *, rough=0.45,
                             grain_scale=(1.6, 14.0, 4.0), bump_strength=0.08):
    """Multi-node oak plank wood PBR material with fine horizontal grain and satin sheen."""
    m = surface(name, base_hex, rough=rough)
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = tuple(grain_scale)
    ns = n.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 5.5
    ns.inputs["Detail"].default_value = 4.0
    ns.inputs["Roughness"].default_value = 0.62
    c = look.rgba(base_hex)
    c_dark = (c[0] * 0.72, c[1] * 0.68, c[2] * 0.65, 1.0)
    c_lite = (min(1.0, c[0] * 1.14), min(1.0, c[1] * 1.12), min(1.0, c[2] * 1.08), 1.0)
    rmp = n.new("ShaderNodeValToRGB")
    rmp.color_ramp.elements[0].position, rmp.color_ramp.elements[0].color = 0.25, c_dark
    rmp.color_ramp.elements[1].position, rmp.color_ramp.elements[1].color = 0.78, c_lite
    rmp.color_ramp.elements.new(0.52).color = c
    mr = n.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = max(0.30, rough - 0.08)
    mr.inputs["To Max"].default_value = min(0.70, rough + 0.10)
    bmp = n.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = float(bump_strength)
    bmp.inputs["Distance"].default_value = 0.008
    l.new(tc.outputs["Object"], mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], ns.inputs["Vector"])
    l.new(ns.outputs["Fac"], rmp.inputs[0])
    l.new(rmp.outputs[0], p.inputs["Base Color"])
    l.new(ns.outputs["Fac"], mr.inputs["Value"])
    l.new(mr.outputs[0], p.inputs["Roughness"])
    l.new(ns.outputs["Fac"], bmp.inputs["Height"])
    l.new(bmp.outputs[0], p.inputs["Normal"])
    p.inputs["Specular IOR Level"].default_value = 0.45
    return m


def build_beveled_plank_floor(
    col,
    name="Floor | Beveled Planks",
    x0=-4.0,
    x1=4.0,
    y0=-3.0,
    y1=4.0,
    z=0.0,
    *,
    plank_w=0.18,
    tones=("#6E472B", "#7D5335", "#8B5E3C"),
    rough=0.45,
    seed=42,
    subfloor=True,
):
    """Build real 0.18 m beveled 3D wood planks merged into 3 oak-tone meshes.

    Replaces stretched wood floor cubes with crisp staggered-seam planks across
    3 oak tones merged into 3 low-draw-call meshes plus an optional dark subfloor.
    Top walking surface sits cleanly at world `Z = z`.
    """
    if bpy is None:
        raise RuntimeError("build_beveled_plank_floor requires Blender 4.2 Python.")
    rng = random.Random(seed)
    tones = tuple(tones)
    if len(tones) != 3:
        raise ValueError("build_beveled_plank_floor expects exactly 3 oak tone hex colors.")
    mats = [make_plank_wood_material(f"{name} | Oak {i}", hex_c, rough=rough) for i, hex_c in enumerate(tones)]

    objs = []
    if subfloor:
        m_seam = surface(f"{name} | Dark Seam Base", "#281910", rough=0.90)
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.5 * (x0 + x1), 0.5 * (y0 + y1), z - 0.064))
        sub_obj = put(bpy.context.object, col, mat=m_seam)
        sub_obj.name = f"{name} | Subfloor"
        sub_obj.scale = (x1 - x0, y1 - y0, 0.12)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        objs.append(sub_obj)

    buckets = [([], []) for _ in range(3)]
    gap = 0.004
    bev = 0.008
    h_plank = 0.018
    row_i = 0
    y = float(y0)
    while y < y1 - 1e-4:
        ry0 = y + gap * 0.5
        ry1 = min(float(y1), y + float(plank_w)) - gap * 0.5
        if ry1 - ry0 < 0.03:
            break
        offset = (row_i % 3) * 0.62 + rng.uniform(-0.12, 0.12)
        x = float(x0) - (offset % 1.45)
        while x < x1 - 1e-4:
            plen = rng.uniform(1.15, 1.75)
            px0 = max(float(x0), x) + gap * 0.5
            px1 = min(float(x1), x + plen) - gap * 0.5
            x += plen
            if px1 - px0 < 0.06:
                continue
            tone_idx = (row_i + rng.randint(0, 2)) % 3
            verts, faces = buckets[tone_idx]
            k = len(verts)
            zb, zt = float(z) - h_plank, float(z)
            b = min(bev, 0.25 * (px1 - px0), 0.25 * (ry1 - ry0))
            verts.extend([
                (px0, ry0, zb), (px1, ry0, zb), (px1, ry1, zb), (px0, ry1, zb),
                (px0 + b, ry0 + b, zt), (px1 - b, ry0 + b, zt), (px1 - b, ry1 - b, zt), (px0 + b, ry1 - b, zt),
            ])
            faces.extend([
                (k + 4, k + 5, k + 6, k + 7),
                (k + 0, k + 1, k + 5, k + 4),
                (k + 1, k + 2, k + 6, k + 5),
                (k + 2, k + 3, k + 7, k + 6),
                (k + 3, k + 0, k + 4, k + 7),
            ])
        y += float(plank_w)
        row_i += 1

    for i, (verts, faces) in enumerate(buckets):
        if verts:
            objs.append(mesh(f"{name} | Planks Tone {i}", col, verts, faces, mats[i], smoothing=False))
    return objs


def make_brushed_metal_material(name, color="#C8CDD4", *, metallic=0.82, roughness=0.28,
                                brush_scale=(16.0, 16.0, 2.5), bump_strength=0.05, glow=0.0):
    """Anisotropic-feel brushed metal PBR shader with micro-streak roughness & subtle bump."""
    m = surface(name, color, rough=roughness, metal=metallic, glow=glow)
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    p.inputs["Specular IOR Level"].default_value = 0.60
    tc = n.new("ShaderNodeTexCoord")
    mul = n.new("ShaderNodeVectorMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = tuple(brush_scale)
    l.new(tc.outputs["Object"], mul.inputs[0])
    ns = n.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 4.2
    ns.inputs["Detail"].default_value = 2.5
    l.new(mul.outputs["Vector"], ns.inputs["Vector"])
    rmap = n.new("ShaderNodeMapRange")
    rmap.inputs["From Min"].default_value = 0.25
    rmap.inputs["From Max"].default_value = 0.75
    rmap.inputs["To Min"].default_value = max(0.12, roughness - 0.06)
    rmap.inputs["To Max"].default_value = min(0.58, roughness + 0.08)
    l.new(ns.outputs["Fac"], rmap.inputs["Value"])
    l.new(rmap.outputs[0], p.inputs["Roughness"])
    if bump_strength and float(bump_strength) > 0.0:
        bmp = n.new("ShaderNodeBump")
        bmp.inputs["Strength"].default_value = float(bump_strength)
        bmp.inputs["Distance"].default_value = 0.005
        l.new(ns.outputs["Fac"], bmp.inputs["Height"])
        l.new(bmp.outputs["Normal"], p.inputs["Normal"])
    return m


def make_editorial_brick_material(name, color1="#8C4A3A", color2="#73392C", mortar="#2D2322", *,
                                  scale=3.6, brick_w=0.44, row_h=0.20, mortar_sz=0.028,
                                  rough=0.86, bump_strength=0.14, glow=0.0):
    """Editorial masonry wall shader with subtle plaster patina and recessed mortar bump."""
    m = surface(name, color1, rough=rough)
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    p.inputs["Specular IOR Level"].default_value = 0.14
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    add_xy = n.new("ShaderNodeMath")
    add_xy.operation = "ADD"
    comb = n.new("ShaderNodeCombineXYZ")
    l.new(tc.outputs["Object"], sep.inputs[0])
    l.new(sep.outputs["X"], add_xy.inputs[0])
    l.new(sep.outputs["Y"], add_xy.inputs[1])
    l.new(add_xy.outputs[0], comb.inputs["X"])
    l.new(sep.outputs["Z"], comb.inputs["Y"])

    ns = n.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 3.2
    ns.inputs["Detail"].default_value = 3.5
    ns.inputs["Roughness"].default_value = 0.55
    l.new(tc.outputs["Object"], ns.inputs["Vector"])

    mot = n.new("ShaderNodeMixRGB")
    mot.inputs[1].default_value = look.rgba(color2)
    mot.inputs[2].default_value = look.rgba(color1)
    l.new(ns.outputs["Fac"], mot.inputs[0])

    brk = n.new("ShaderNodeTexBrick")
    brk.offset = 0.5
    brk.inputs["Color1"].default_value = look.rgba(color1)
    brk.inputs["Color2"].default_value = look.rgba(color2)
    brk.inputs["Mortar"].default_value = look.rgba(mortar)
    brk.inputs["Scale"].default_value = float(scale)
    brk.inputs["Mortar Size"].default_value = float(mortar_sz)
    brk.inputs["Mortar Smooth"].default_value = 0.05
    brk.inputs["Brick Width"].default_value = float(brick_w)
    brk.inputs["Row Height"].default_value = float(row_h)
    l.new(comb.outputs["Vector"], brk.inputs["Vector"])
    l.new(mot.outputs[0], brk.inputs["Color1"])
    l.new(brk.outputs["Color"], p.inputs["Base Color"])
    if glow and float(glow) > 0.0:
        l.new(brk.outputs["Color"], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = float(glow)
    bm = n.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value = float(bump_strength)
    bm.inputs["Distance"].default_value = 0.015
    l.new(brk.outputs["Fac"], bm.inputs["Height"])
    l.new(bm.outputs["Normal"], p.inputs["Normal"])
    return m


def make_tile_material(name, color1="#E2EFEF", color2="#CEE3E4", mortar="#4B5B64", *,
                       scale=4.8, tile_w=0.52, row_h=0.22, mortar_sz=0.018,
                       rough=0.20, grout_rough=0.85, bump_strength=0.24, axis_xz=True):
    """Glossy ceramic wall/floor tile shader with matte grout contrast and crisp joint bump."""
    m = surface(name, color1, rough=rough)
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    p.inputs["Specular IOR Level"].default_value = 0.65
    tc = n.new("ShaderNodeTexCoord")
    if axis_xz:
        sep = n.new("ShaderNodeSeparateXYZ")
        comb = n.new("ShaderNodeCombineXYZ")
        l.new(tc.outputs["Object"], sep.inputs[0])
        l.new(sep.outputs["X"], comb.inputs["X"])
        l.new(sep.outputs["Z"], comb.inputs["Y"])
        l.new(sep.outputs["Y"], comb.inputs["Z"])
        vec_out = comb.outputs["Vector"]
    else:
        vec_out = tc.outputs["Object"]
    brk = n.new("ShaderNodeTexBrick")
    brk.offset = 0.5
    brk.inputs["Color1"].default_value = look.rgba(color1)
    brk.inputs["Color2"].default_value = look.rgba(color2)
    brk.inputs["Mortar"].default_value = look.rgba(mortar)
    brk.inputs["Scale"].default_value = float(scale)
    brk.inputs["Brick Width"].default_value = float(tile_w)
    brk.inputs["Row Height"].default_value = float(row_h)
    brk.inputs["Mortar Size"].default_value = float(mortar_sz)
    brk.inputs["Mortar Smooth"].default_value = 0.15
    mr = n.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = float(rough)
    mr.inputs["To Max"].default_value = float(grout_rough)
    inv = n.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    bmp = n.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = float(bump_strength)
    bmp.inputs["Distance"].default_value = 0.015
    l.new(vec_out, brk.inputs["Vector"])
    l.new(brk.outputs["Color"], p.inputs["Base Color"])
    l.new(brk.outputs["Fac"], mr.inputs["Value"])
    l.new(mr.outputs[0], p.inputs["Roughness"])
    l.new(brk.outputs["Fac"], inv.inputs[1])
    l.new(inv.outputs[0], bmp.inputs["Height"])
    l.new(bmp.outputs[0], p.inputs["Normal"])
    return m


def make_glossy_fluid_material(name, base_hex="#1D7FA8", glow_hex="#68D8F5", *,
                               rough=0.06, glow=0.45, alpha=0.92, wave_scale=8.5,
                               bump_strength=0.22, use_uv=True):
    """Glossy animated liquid shader returning `(material, mapping_node)`.

    Keyframe `mapping_node.inputs["Location"].default_value` along Y/V to drive
    continuous ripple flow along lofted tubes or water planes without sphere soup.
    """
    m = surface(name, base_hex, rough=rough)
    if alpha < 0.99:
        m.surface_render_method = "BLENDED"
    n, l = m.node_tree.nodes, m.node_tree.links
    p = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    p.inputs["Specular IOR Level"].default_value = 0.92
    if "Coat Weight" in p.inputs:
        p.inputs["Coat Weight"].default_value = 0.90
        p.inputs["Coat Roughness"].default_value = 0.04
    p.inputs["Alpha"].default_value = float(alpha)
    p.inputs["Emission Color"].default_value = look.rgba(glow_hex)
    p.inputs["Emission Strength"].default_value = float(glow)

    tc = n.new("ShaderNodeTexCoord")
    mp = n.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.5, 6.0, 1.5) if use_uv else (2.5, 2.5, 2.5)
    ns = n.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = float(wave_scale)
    ns.inputs["Detail"].default_value = 3.5
    ns.inputs["Roughness"].default_value = 0.55

    rmp = n.new("ShaderNodeValToRGB")
    rmp.color_ramp.elements[0].position, rmp.color_ramp.elements[0].color = 0.25, look.rgba(base_hex)
    rmp.color_ramp.elements[1].position, rmp.color_ramp.elements[1].color = 0.80, look.rgba(glow_hex)

    bmp = n.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = float(bump_strength)
    bmp.inputs["Distance"].default_value = 0.03

    src = tc.outputs["UV"] if use_uv else tc.outputs["Object"]
    l.new(src, mp.inputs["Vector"])
    l.new(mp.outputs["Vector"], ns.inputs["Vector"])
    l.new(ns.outputs["Fac"], rmp.inputs[0])
    l.new(rmp.outputs[0], p.inputs["Base Color"])
    l.new(ns.outputs["Fac"], bmp.inputs["Height"])
    l.new(bmp.outputs[0], p.inputs["Normal"])
    return m, mp


def build_lofted_tube(name, col, points, radii, mat, *, parent=None, segments=16,
                      cap_ends=True, closed=False, smooth=True):
    """Build a continuous lofted quad-strip tube along 3D `points` with clean flow UVs.

    Uses parallel-transport (Bishop) frames to avoid Frenet twist flips and accepts
    either a constant float radius or a per-point radius sequence.
    """
    if bpy is None:
        raise RuntimeError("build_lofted_tube requires Blender 4.2 Python.")
    pts = [Vector(p) for p in points]
    n_pts = len(pts)
    if n_pts < 2:
        raise ValueError("build_lofted_tube requires at least 2 centerline points.")
    if isinstance(radii, (int, float)):
        rad_list = [float(radii)] * n_pts
    else:
        rad_list = [float(r) for r in radii]
        if len(rad_list) != n_pts:
            raise ValueError(f"Expected {n_pts} radii, got {len(rad_list)}")

    seg = max(3, int(segments))
    tangents = []
    for i in range(n_pts):
        if closed:
            t = pts[(i + 1) % n_pts] - pts[(i - 1) % n_pts]
        elif i == 0:
            t = pts[1] - pts[0]
        elif i == n_pts - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        if t.length_squared < 1e-12:
            t = tangents[-1] if tangents else Vector((0.0, 0.0, 1.0))
        else:
            t = t.normalized()
        tangents.append(t)

    # Parallel-transport frame initialization
    t0 = tangents[0]
    ref = Vector((0.0, 0.0, 1.0)) if abs(t0.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    normal = (ref - t0 * ref.dot(t0)).normalized()
    frames = [(normal, t0.cross(normal).normalized())]
    for i in range(1, n_pts):
        ti = tangents[i]
        n_prev = frames[-1][0]
        n_proj = n_prev - ti * n_prev.dot(ti)
        if n_proj.length_squared < 1e-10:
            alt = Vector((1.0, 0.0, 0.0)) if abs(ti.x) < 0.9 else Vector((0.0, 1.0, 0.0))
            n_proj = alt - ti * alt.dot(ti)
        n_cur = n_proj.normalized()
        b_cur = ti.cross(n_cur).normalized()
        frames.append((n_cur, b_cur))

    cum = [0.0]
    for i in range(1, n_pts):
        cum.append(cum[-1] + (pts[i] - pts[i - 1]).length)
    total_len = max(1e-6, cum[-1])

    stride = seg + 1
    verts, faces, uvs = [], [], []
    for i, (pt, r, (n_vec, b_vec)) in enumerate(zip(pts, rad_list, frames)):
        v_coord = cum[i] / total_len
        for j in range(stride):
            a = math.tau * j / seg
            offset = (n_vec * math.cos(a) + b_vec * math.sin(a)) * r
            verts.append(tuple(pt + offset))
            uvs.append((j / seg, v_coord))

    ring_pairs = list(range(n_pts - 1))
    for i in ring_pairs:
        base0 = i * stride
        base1 = (i + 1) * stride
        for j in range(seg):
            faces.append((base0 + j, base0 + j + 1, base1 + j + 1, base1 + j))
    if closed and n_pts >= 3:
        base0 = (n_pts - 1) * stride
        base1 = 0
        for j in range(seg):
            faces.append((base0 + j, base0 + j + 1, base1 + j + 1, base1 + j))
    elif cap_ends:
        faces.append(tuple(reversed(range(seg))))
        last = (n_pts - 1) * stride
        faces.append(tuple(range(last, last + seg)))

    return mesh(name, col, verts, faces, mat, parent=parent, smoothing=smooth, uv=uvs)


def build_lathe_prop(name, col, profile_rz, mat, *, loc=(0.0, 0.0, 0.0), parent=None,
                     segments=24, smooth=True, cap_bottom=True, cap_top=False):
    """Build a continuous surface-of-revolution prop from `[(radius, z), ...]` profile points."""
    if bpy is None:
        raise RuntimeError("build_lathe_prop requires Blender 4.2 Python.")
    profile = [(max(1e-4, float(r)), float(z)) for r, z in profile_rz]
    n_rings = len(profile)
    if n_rings < 2:
        raise ValueError("build_lathe_prop requires at least 2 (radius, z) profile points.")

    seg = max(6, int(segments))
    stride = seg + 1
    verts, faces, uvs = [], [], []
    for j, (r, z) in enumerate(profile):
        v_coord = j / (n_rings - 1)
        for i in range(stride):
            a = math.tau * i / seg
            verts.append((r * math.cos(a), r * math.sin(a), z))
            uvs.append((i / seg, v_coord))

    for j in range(n_rings - 1):
        b0 = j * stride
        b1 = (j + 1) * stride
        for i in range(seg):
            faces.append((b0 + i, b0 + i + 1, b1 + i + 1, b1 + i))

    if cap_bottom:
        faces.append(tuple(reversed(range(seg))))
    if cap_top:
        last = (n_rings - 1) * stride
        faces.append(tuple(range(last, last + seg)))

    obj = mesh(name, col, verts, faces, mat, parent=parent, smoothing=smooth, uv=uvs)
    obj.location = loc
    return obj


def setup_diorama_camera_and_compositor(
    scene,
    camera=None,
    *,
    lens_mm=27.0,
    fog_glow_mix=0.08,
    clip_end=250.0,
    clip_start=0.05,
    portal_flash_keys=(),
    replace=True,
    glare_threshold=None,
    cinema_grade=True,
):
    """Configure a crisp deep-focus 9:16 cutaway diorama camera & compositor.

    Sets `sensor_fit="VERTICAL"`, `sensor_height=36.0`, `clip_start=0.05`,
    `clip_end=clip_end`, installs `setup_ricks_compositor`, tunes Fog Glow mix
    to `fog_glow_mix` (default `0.08`), and strictly enforces `use_dof = False`
    AFTER `setup_ricks_compositor()` (which otherwise re-enables shallow DOF).
    """
    if bpy is None:
        raise RuntimeError("setup_diorama_camera_and_compositor requires Blender 4.2 Python.")
    if camera is None:
        camera = scene.camera
    if camera is None:
        cam_data = bpy.data.cameras.new("Camera | Diorama")
        camera = bpy.data.objects.new("Camera | Diorama", cam_data)
        scene.collection.objects.link(camera)
        scene.camera = camera

    camera.data.type = "PERSP"
    camera.data.sensor_fit = "VERTICAL"
    camera.data.sensor_height = 36.0
    camera.data.lens = float(lens_mm)
    camera.data.clip_start = float(clip_start)
    camera.data.clip_end = float(clip_end)

    flash_node = setup_ricks_compositor(
        scene,
        camera=camera,
        portal_flash_keys=portal_flash_keys,
        replace=replace,
        cinema_grade=cinema_grade,
    )

    nodes = scene.node_tree.nodes
    glare = next((nd for nd in nodes if nd.type == "GLARE"), None)
    if glare is not None:
        if glare_threshold is not None:
            glare.threshold = float(glare_threshold)
        for link in scene.node_tree.links:
            if link.from_node == glare and link.to_node.type == "MIX_RGB" and link.to_node.blend_type == "ADD":
                link.to_node.name = "Cinema | Fog Glow Mix"
                link.to_node.label = f"Fog Glow Mix {float(fog_glow_mix):.2f}"
                link.to_node.inputs[0].default_value = float(fog_glow_mix)

    # CRITICAL: strictly enforce deep focus & vertical sensor AFTER setup_ricks_compositor()
    camera.data.type = "PERSP"
    camera.data.sensor_fit = "VERTICAL"
    camera.data.sensor_height = 36.0
    camera.data.lens = float(lens_mm)
    camera.data.clip_start = float(clip_start)
    camera.data.clip_end = float(clip_end)
    camera.data.dof.use_dof = False
    return camera, flash_node
