"""Opt-in drawn-character look for RicksCharacter rigs (Blender 4.2 EEVEE Next).

The default Rick's 3D cel character is unchanged. apply_drawn_look() restyles
an already-built rig so it reads as flat cartoon artwork standing in a lit
3D world, while the rig, poses, limbs and contact anchors stay the same:

  * slightly lopsided round head (egg, tilt and low harmonic lumps), applied
    as one static warp to the head, hair, face decals and their ink;
  * flat paint: cream face, flat costume and hair colours, hair with a soft
    crown-to-nape gradient, no specular and no cel bands;
  * a restrained painted shadow on the side away from a "drawn light";
  * near-black ink hulls that are thin on the lit side and heavy on the shaded
    side, with extra weight under the chin and along the lower body edge;
  * round fists at the arm tips, centred on the same hand anchor.

The shading and ink weights come from the drawn light, a world-oriented empty
that follows the head by position only. The weights depend on surface normals
and that one direction, with no noise, so the contour is stable from frame to
frame and only changes when the character turns relative to the light. Re-aim
it per shot with set_drawn_light(); key it with CONSTANT interpolation.

Hand-to-prop grips: the visible fist is a bulge on the arm curve, centred on
the arm tip. contact_anchors() reports the same world points for both looks,
so a prop placed on the anchor still meets the hand while the camera moves.

Use update_ink(rig, camera, frame=f) for both looks: it delegates to the
kit's RicksCharacter.update_ink for the default look.
"""
import math

try:
    import bpy
    from mathutils import Matrix, Vector
except ModuleNotFoundError as error:
    if error.name not in {"bpy", "mathutils"}:
        raise
    bpy = None
    Matrix = Vector = None

if __package__:
    from . import ricks_v2_kit as kit
else:
    import ricks_v2_kit as kit

WEIGHT_GROUP = "Drawn ink weight"
NODE_GROUP = "Rick's drawn | light-weighted ink"
# Original lopsided presets: egg >0 fuller bottom, tilt in degrees,
# lumps = (harmonic, amount, phase) on the front-view outline.
# "round" (1:1) and "upright" (H/W=1.035) strictly ban horizontal oval squash.
HEAD_SHAPES = {
    "lopsided": {"egg": .08, "tilt": -6.0, "lumps": ((2, .024, .7), (3, .027, 2.2), (5, .010, 2.8))},
    "potato": {"egg": .05, "tilt": 8.0, "lumps": ((2, .032, 2.0), (3, .022, .5), (4, .014, 1.4))},
    "bean": {"egg": .11, "tilt": -3.0, "lumps": ((2, .018, 1.2), (3, .020, 2.4))},
    "round": {"egg": 0.0, "tilt": 0.0, "lumps": (), "x_scale": 1.00, "z_scale": 1.00},
    "upright": {"egg": 0.0, "tilt": 0.0, "lumps": (), "x_scale": 1.00, "z_scale": 1.035},
}
DEFAULT_LIGHT = (-.55, -.62, .56)   # toward the light: front-left and above a camera at -Y
INK = {"head": (.55, 1.2, .9), "body": (.55, 1.2, 1.0), "hair": (.62, 1.25, .5)}  # thin, thick, low-edge extra
DRAWN_PRESETS = {
    "paper_white": {
        "face": kit.PAPER_WHITE_FACE,
        "face_shadow": kit.PAPER_WHITE_SHADOW,
        "face_shadow_amount": 0.05,
        "cloth_shade": 0.84,
        "brightness": 1.26,
        "ink": {
            "head": (0.88, 1.06, 0.06),
            "body": (0.80, 1.12, 0.22),
            "hair": (0.85, 1.08, 0.10),
        },
    },
}


# ------------------------------------------------------------------ shape
def head_warp(shape="lopsided", width=None):
    """Return f(Vector head-local) -> Vector for a front-view head silhouette warp.

    Legacy lopsided shapes default to `x_scale=1.04, z_scale=0.97`.
    `"round"` uses `x_scale=1.00, z_scale=1.00` (1:1) and `"upright"` uses
    `x_scale=1.00, z_scale=1.035` so horizontal oval squash is strictly eliminated.
    """
    spec = HEAD_SHAPES[shape] if isinstance(shape, str) else shape
    egg, lumps = spec["egg"], spec["lumps"]
    tilt = math.radians(spec["tilt"])
    x_scale = float(spec.get("x_scale", 1.04)) if width is None else float(width)
    z_scale = float(spec.get("z_scale", 0.97))
    rx, rz = kit.HEAD[0], kit.HEAD[2]
    c, s = math.cos(tilt), math.sin(tilt)

    def warp(p):
        x, y, z = p
        a = math.atan2(-z / rz, x / rx)          # front view, y-down angle: sin(a) > 0 is the lower half
        # Full shape on the outline, none at the face centre where the angle is undefined.
        w = min(1.0, math.hypot(x / rx, z / rz)) ** 2
        r = 1 + w * (egg * math.sin(a) + sum(amt * math.sin(h * a + ph) for h, amt, ph in lumps))
        nx, nz = x * r * x_scale, z * r * z_scale + egg * .35 * rz
        nx, nz = nx * c - nz * s, nx * s + nz * c
        res = (nx, y * (1 + .5 * (r - 1)), nz)
        return Vector(res) if Vector is not None else res
    return warp


def _warp_head(rig, warp):
    head = rig.head
    to_head = head.matrix_world.inverted()
    for obj in head.children_recursive:
        if obj == rig.sweat:
            continue                              # its pose path is analytic; leave the drop shape alone
        local = to_head @ obj.matrix_world
        back = local.inverted()
        if obj.type == "MESH":
            for v in obj.data.vertices:
                v.co = back @ warp(local @ v.co)
            obj.data.update()
        elif obj.type == "CURVE":
            for spline in obj.data.splines:
                for p in spline.bezier_points:
                    p.co = back @ warp(local @ p.co)
                    p.handle_left = back @ warp(local @ p.handle_left)
                    p.handle_right = back @ warp(local @ p.handle_right)


# ------------------------------------------------------------------ drawn light
def _world_axes(collection):
    obj = bpy.data.objects.get("Drawn look | world axes")
    if obj is None:
        obj = bpy.data.objects.new("Drawn look | world axes", None)
        collection.objects.link(obj)
    return obj


def _light_rotation(direction):
    d = Vector(direction).normalized()
    return d.to_track_quat("Z", "Y").to_euler()


def set_drawn_light(rig, direction, frame=None):
    """Point the drawn light (toward the light, world space); optionally key a CONSTANT step."""
    look = rig.drawn_look
    light = look["light"]
    light.rotation_euler = _light_rotation(direction)
    if frame is not None:
        light.keyframe_insert("rotation_euler", frame=frame)
        for curve in light.animation_data.action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT"
    return light


# ------------------------------------------------------------------ ink
def _ink_node_group():
    group = bpy.data.node_groups.get(NODE_GROUP)
    if group is not None:
        return group
    group = bpy.data.node_groups.new(NODE_GROUP, "GeometryNodeTree")
    io = group.interface
    io.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    io.new_socket(name="Light", in_out="INPUT", socket_type="NodeSocketObject")
    io.new_socket(name="World", in_out="INPUT", socket_type="NodeSocketObject")
    for name, value in (("Thin", .55), ("Thick", 1.2), ("Low edge", .9)):
        sock = io.new_socket(name=name, in_out="INPUT", socket_type="NodeSocketFloat")
        sock.default_value = value
    io.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n, l = group.nodes, group.links
    gin, gout = n.new("NodeGroupInput"), n.new("NodeGroupOutput")

    def math_node(op, a=None, b=None):
        node = n.new("ShaderNodeMath")
        node.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                node.inputs[i].default_value = v
            else:
                l.new(v, node.inputs[i])
        return node.outputs[0]

    def axis(obj_socket, vec):
        info = n.new("GeometryNodeObjectInfo")
        info.transform_space = "RELATIVE"
        l.new(obj_socket, info.inputs["Object"])
        const = n.new("FunctionNodeInputVector")
        const.vector = vec
        rot = n.new("FunctionNodeRotateVector")
        l.new(const.outputs[0], rot.inputs["Vector"])
        l.new(info.outputs["Rotation"], rot.inputs["Rotation"])
        return rot.outputs[0]

    normal = n.new("GeometryNodeInputNormal").outputs[0]
    outward = n.new("ShaderNodeVectorMath")
    outward.operation = "SCALE"
    l.new(normal, outward.inputs[0])
    outward.inputs["Scale"].default_value = -1.0       # hull faces are reversed
    toward_light = axis(gin.outputs["Light"], (0, 0, 1))
    down = axis(gin.outputs["World"], (0, 0, -1))

    def vdot(a, b):
        node = n.new("ShaderNodeVectorMath")
        node.operation = "DOT_PRODUCT"
        l.new(a, node.inputs[0])
        l.new(b, node.inputs[1])
        return node.outputs["Value"]

    lit = vdot(outward.outputs[0], toward_light)
    shade = math_node("MULTIPLY", math_node("SUBTRACT", 1.0, lit), .5)
    shade = math_node("POWER", math_node("MAXIMUM", shade, 0.0), 1.4)
    span = math_node("SUBTRACT", gin.outputs["Thick"], gin.outputs["Thin"])
    f = math_node("ADD", gin.outputs["Thin"], math_node("MULTIPLY", span, shade))
    low = math_node("POWER", math_node("MAXIMUM", vdot(outward.outputs[0], down), 0.0), 1.5)
    f = math_node("MULTIPLY", f, math_node("ADD", 1.0, math_node("MULTIPLY", gin.outputs["Low edge"], low)))
    fmax = math_node("MULTIPLY", gin.outputs["Thick"], math_node("ADD", 1.0, gin.outputs["Low edge"]))
    weight = math_node("DIVIDE", f, fmax)
    store = n.new("GeometryNodeStoreNamedAttribute")
    store.data_type = "FLOAT"
    store.domain = "POINT"
    store.inputs["Name"].default_value = WEIGHT_GROUP
    l.new(gin.outputs["Geometry"], store.inputs["Geometry"])
    l.new(weight, store.inputs["Value"])
    l.new(store.outputs["Geometry"], gout.inputs["Geometry"])
    return group


def _socket_ids(group):
    return {item.name: item.identifier for item in group.interface.items_tree
            if item.item_type == "SOCKET" and item.in_out == "INPUT"}


def _install_ink(displace, light, world, weights):
    obj = displace.id_data
    if WEIGHT_GROUP not in obj.vertex_groups:
        vg = obj.vertex_groups.new(name=WEIGHT_GROUP)
        vg.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
    group = _ink_node_group()
    mod = obj.modifiers.new("Drawn ink weight", "NODES")
    mod.node_group = group
    ids = _socket_ids(group)
    mod[ids["Light"]] = light
    mod[ids["World"]] = world
    thin, thick, low = weights
    mod[ids["Thin"]], mod[ids["Thick"]], mod[ids["Low edge"]] = thin, thick, low
    index = list(obj.modifiers).index(displace)
    obj.modifiers.move(len(obj.modifiers) - 1, index)
    displace.vertex_group = WEIGHT_GROUP
    return thick * (1 + low)


# ------------------------------------------------------------------ paint
def _rgb(color):
    return kit.look.rgba(color) if isinstance(color, str) else tuple(color)


def _shade_mask(nodes, links, light, start=-.08, end=-.68):
    coords = nodes.new("ShaderNodeTexCoord")
    coords.object = light
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Object"], split.inputs[0])
    ramp = nodes.new("ShaderNodeMapRange")
    ramp.interpolation_type = "SMOOTHERSTEP"
    ramp.inputs["From Min"].default_value, ramp.inputs["From Max"].default_value = start, end
    ramp.inputs["To Min"].default_value, ramp.inputs["To Max"].default_value = 0.0, 1.0
    links.new(split.outputs["Z"], ramp.inputs["Value"])
    return ramp.outputs[0]


def _flat_material(name, light, pigment, *, shade_color=None, shade=.8, strength=1.0, gradient=None,
                   image=None):
    """Flat emission paint with a painted shade on the side away from `light`."""
    m = bpy.data.materials.new(name)
    m.diffuse_color = _rgb(pigment)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    if image is not None:
        tex = n.new("ShaderNodeTexImage")
        tex.image = image
        color = tex.outputs["Color"]
    else:
        rgb = n.new("ShaderNodeRGB")
        rgb.outputs[0].default_value = _rgb(pigment)
        color = rgb.outputs[0]
    if gradient is not None:                   # hair: darker nape, base, lighter crown (object Z)
        lo, base_z, hi = gradient
        coords = n.new("ShaderNodeTexCoord")
        split = n.new("ShaderNodeSeparateXYZ")
        l.new(coords.outputs["Object"], split.inputs[0])
        ramp = n.new("ShaderNodeValToRGB")
        c = _rgb(pigment)
        dark = tuple(v * .72 for v in c[:3]) + (1,)
        light_c = tuple(v + (1 - v) * .22 for v in c[:3]) + (1,)
        ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, dark
        ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 1.0, light_c
        ramp.color_ramp.elements.new(.45).color = c
        ramp.color_ramp.interpolation = "EASE"
        span = n.new("ShaderNodeMapRange")
        span.inputs["From Min"].default_value, span.inputs["From Max"].default_value = lo, hi
        l.new(split.outputs["Z"], span.inputs["Value"])
        l.new(span.outputs[0], ramp.inputs[0])
        color = ramp.outputs[0]
    mix = n.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY" if shade_color is None else "MIX"
    mask = _shade_mask(n, l, light)
    fac = n.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    l.new(mask, fac.inputs[0])
    fac.inputs[1].default_value = 1.0
    l.new(fac.outputs[0], mix.inputs[0])
    l.new(color, mix.inputs[1])
    if shade_color is None:
        mix.inputs[2].default_value = (shade, shade, shade, 1)
    else:
        mix.inputs[2].default_value = _rgb(shade_color)
    paint = n.new("ShaderNodeEmission")
    paint.label = "Drawn flat paint"
    paint.inputs["Strength"].default_value = strength
    l.new(mix.outputs[0], paint.inputs["Color"])
    shader = paint.outputs[0]
    if image is not None:
        m.surface_render_method = "BLENDED"
        clear, alpha = n.new("ShaderNodeBsdfTransparent"), n.new("ShaderNodeMixShader")
        l.new(tex.outputs["Alpha"], alpha.inputs[0])
        l.new(clear.outputs[0], alpha.inputs[1])
        l.new(shader, alpha.inputs[2])
        shader = alpha.outputs[0]
    l.new(shader, out.inputs["Surface"])
    m["ricks_drawn"] = True
    return m


def _is_cel(material):
    return (material is not None and material.use_nodes
            and any(node.type == "SHADERTORGB" for node in material.node_tree.nodes))


def _image_of(material):
    return next((node.image for node in material.node_tree.nodes if node.type == "TEX_IMAGE"), None)


# ------------------------------------------------------------------ public API
def apply_drawn_look(rig, collection, *, light_dir=DEFAULT_LIGHT, head_shape="lopsided", head_width=None,
                     face=None, face_shadow=None, face_shadow_amount=None, cloth_shade=None,
                     ink=None, fists=True, brightness=None, preset=None):
    """Restyle a built RicksCharacter in place and return its look record.

    Call after build_ricks_character()/build_studio_character() and before
    posing. The rig keeps its controls, arms, legs, feet and expressions.
    Pass `preset="paper_white"` for AgX-calibrated bright paper-white faces
    (`#FAF9F6` / `#EAE8E1`, `face_shadow_amount=0.05`, `brightness=1.26`).
    """
    if bpy is None:
        raise RuntimeError("apply_drawn_look requires Blender 4.2 Python.")
    if getattr(rig, "drawn_look", None):
        raise ValueError(f"{rig.name} already has the drawn look.")
    if preset is not None and preset not in DRAWN_PRESETS:
        raise ValueError(f"Unknown drawn preset {preset!r}; expected one of {tuple(DRAWN_PRESETS)}")

    p_cfg = DRAWN_PRESETS.get(preset, {})
    face = p_cfg.get("face", "#FFF9F0") if face is None else face
    face_shadow = p_cfg.get("face_shadow", "#C9C9CE") if face_shadow is None else face_shadow
    face_shadow_amount = p_cfg.get("face_shadow_amount", .62) if face_shadow_amount is None else face_shadow_amount
    cloth_shade = p_cfg.get("cloth_shade", .78) if cloth_shade is None else cloth_shade
    brightness = p_cfg.get("brightness", 1.0) if brightness is None else brightness
    ink = {**INK, **p_cfg.get("ink", {}), **(ink or {})}
    world = _world_axes(collection)
    light = bpy.data.objects.new(f"Drawn look | {rig.name} light", None)
    collection.objects.link(light)
    light.empty_display_type = "SINGLE_ARROW"
    hold = light.constraints.new("COPY_LOCATION")
    hold.target = rig.head
    light.rotation_euler = _light_rotation(light_dir)
    r = kit.HEAD[0] * max(rig.head.scale)
    light.scale = (r, r, r)
    body_light = bpy.data.objects.new(f"Drawn look | {rig.name} body light", None)
    collection.objects.link(body_light)
    hold = body_light.constraints.new("COPY_LOCATION")
    hold.target = rig.body
    hold.use_offset = True
    body_light.location = (0, 0, kit.TORSO_CENTER - .59)
    turn = body_light.constraints.new("COPY_ROTATION")
    turn.target = light
    body_light.scale = (.14, .14, .14)
    bpy.context.view_layer.update()

    _warp_head(rig, head_warp(head_shape, head_width))

    head_objects = set(rig.head.children_recursive)
    face_obj = bpy.data.objects.get(rig.name + " | ellipsoid head")
    face_source = face_obj.data.materials[0] if face_obj else None
    replaced = {}
    face_mat = _flat_material(rig.name + " | drawn face", light, face, shade_color=None, strength=brightness)
    # Face: cream mixed toward a painted grey, restrained so the middle stays light.
    nodes = face_mat.node_tree.nodes
    mix = next(n for n in nodes if n.type == "MIX_RGB")
    mix.blend_type = "MIX"
    mix.inputs[2].default_value = _rgb(face_shadow)
    fac = next(n for n in nodes if n.type == "MATH")
    fac.inputs[1].default_value = face_shadow_amount
    if face_source is not None:
        replaced[face_source.name] = face_mat

    for obj in rig.root.children_recursive:
        if obj.get("ricks_role") == "ink" or obj.type not in {"MESH", "CURVE"} or obj.data is None:
            continue
        mats = obj.data.materials
        for i, m in enumerate(mats):
            if m is None or not _is_cel(m):
                continue
            if m.name not in replaced:
                near = light if obj in head_objects else body_light
                image = _image_of(m)
                hair = "hair cap" in obj.name
                replaced[m.name] = _flat_material(
                    m.name + " | drawn", near, m.diffuse_color[:3] + (1,), shade=cloth_shade, strength=brightness,
                    image=image, gradient=(-.07, .08, .25) if hair else None)
            mats[i] = replaced[m.name]

    scale = {}
    for mod in rig.ink_modifiers:
        obj = mod.id_data
        kind = "hair" if "hair" in obj.name else "head" if obj.parent and obj.parent in head_objects | {rig.head} \
            and "torso" not in obj.name else "body"
        near = light if kind in {"head", "hair"} else body_light
        scale[mod.name + "|" + obj.name] = _install_ink(mod, near, world, ink[kind])

    if fists:
        for arm in rig.arms:
            for point, radius in zip(arm.data.splines[0].bezier_points, (1, 1, 2.3, 2.1, .9)):
                point.radius = radius

    rig.drawn_look = {"light": light, "body_light": body_light, "world": world, "ink_scale": scale,
                      "shape": head_shape}
    return rig.drawn_look


def update_ink(rig, camera, *, pixels=3.0, frame=None):
    """Key screen-compensated ink for either look (same call in scene loops)."""
    look = getattr(rig, "drawn_look", None)
    if not look:
        return rig.update_ink(camera, pixels=pixels, frame=frame)
    inverse = camera.matrix_world.inverted()
    for hull in rig.ink_modifiers:
        obj = hull.id_data
        depth = -(inverse @ obj.matrix_world.translation).z
        if depth <= 0:
            continue
        k = look["ink_scale"].get(hull.name + "|" + obj.name, 1.0)
        width = kit._ink_thickness(depth, camera.data.lens, pixels, .006)
        hull.strength = -min(.015 * k, width * k)
        if frame is not None:
            hull.keyframe_insert("strength", frame=frame)


def contact_anchors(rig):
    """World-space contact points shared by both looks (evaluate after frame_set)."""
    out = {}
    for side, arm in zip(("L", "R"), rig.arms):
        points = arm.data.splines[0].bezier_points
        out["hand_" + side] = arm.matrix_world @ points[2].co
        out["elbow_" + side] = arm.matrix_world @ points[1].co
    for side, foot in zip(("L", "R"), rig.feet):
        out["foot_" + side] = foot.matrix_world.translation.copy()
    out["eyes"] = rig.head.matrix_world @ Vector((0, -.17, .03))
    out["head"] = rig.head.matrix_world.translation.copy()
    out["root"] = rig.root.matrix_world.translation.copy()
    return {k: Vector(v) for k, v in out.items()}
