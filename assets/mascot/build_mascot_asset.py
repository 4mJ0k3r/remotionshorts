"""Procedural Blender 4.2 builder for the Official Mascot (`mascot_master.blend`).

Builds the `"MascotHero"` collection with:
  - Plump 1:1 marshmallow head (`width=0.440m, depth=0.400m, height=0.448m`, ratio `1.018`)
    in AgX-compensated snow-white comic paint (`#FFFDFB`, ~88% pure bright white + subtle
    `#DCE2EE` far-jaw crescent shade)
  - Conformed 3D face decals across all 18 packed PNGs (`12 EXPRESSIONS + 6 VISEMES`)
  - `4°`-tilted crimson ribbed knit beanie (`#E62429` / `#AE151B`), plump folded cuff band,
    6 curved `#141016` vertical knit rib grooves, upper-left glossy highlight
  - Oversized A-line cozy yellow hoodie (`#FFD21F` / `#DF9B12`), snug 3D hood collar +
    sculpted back hood (zero neck gap), 2 black metal eyelets + 2 rigged white drawstrings
    with black aglet tips, front kangaroo pouch pocket, ribbed waist cuff
  - Sleeved IK arms (`arm_style="hoodie"` default + `"stick"` toggle)
  - 7 swappable puffy white cartoon hand poses per side + `hand_socket_L` / `hand_socket_R`
  - Pajama lounge pants (`bottom_style="pajamas"` default + `"shorts"` toggle)
  - Chunky rounded white-and-black cartoon sneakers flat on `Z = 0.000 m` (`visible_shadow=True`)
  - Crisp `#141016` screen-compensated comic outlines (`< 35,000` visible triangles)

Modal GPU invocation:
  modal run scripts/modal_blender.py --mode run --project assets/mascot \\
      --script build_mascot_asset.py --runner blender --out assets/mascot --overwrite
"""
from __future__ import annotations

from argparse import ArgumentParser
import math
import os
from pathlib import Path
import sys

try:
    import bpy
    import bmesh
    from mathutils import Euler, Matrix, Vector
    from mathutils.bvhtree import BVHTree
except ModuleNotFoundError as _exc:
    if _exc.name not in {"bpy", "bmesh", "mathutils"}:
        raise
    bpy = None
    bmesh = None
    Euler = Matrix = Vector = BVHTree = None

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "scripts/ricks_v2_kit.py").is_file())
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

EXPRESSIONS = (
    "idle_cute",
    "curious_o",
    "chill_laugh",
    "hype_letsgo",
    "cringe_teeth",
    "whatever_eyeroll",
    "phone_zombie",
    "sulk_pout",
    "mortified_blush",
    "smug_wink",
    "crush_hearts",
    "ugh_groan",
)

VISEMES = (
    "vis_closed",
    "vis_AA",
    "vis_EE",
    "vis_OH",
    "vis_OO",
    "vis_FV",
)

ALL_EXPRESSIONS = EXPRESSIONS + VISEMES

HAND_POSES = (
    "relaxed_curl",
    "open_stop",
    "power_claw",
    "fist",
    "point",
    "thumbs_up_ok",
    "behind_head",
)

COLLECTION_NAME = "MascotHero"
INK_HEX = "#141016"
SNOW_WHITE_HEX = "#FFFDFB"
SNOW_SHADE_HEX = "#DCE2EE"
BEANIE_LIT_HEX = "#EC1C24"
BEANIE_SHADE_HEX = "#A61118"
HOODIE_LIT_HEX = "#FFB800"
HOODIE_SHADE_HEX = "#CC7A00"
PANTS_LIT_HEX = "#232733"
PANTS_SHADE_HEX = "#171A22"
SOLE_DARK_HEX = "#282B36"
SNEAKER_BLACK_HEX = "#181B24"
STRIPE_WHITE_HEX = "#FFFDFB"

# Exact standing hierarchy & proportions
BODY_REST_Z = 0.560
HEAD_REL_Z = 0.400          # Standing head center Z = 0.960 m
HEAD_WIDTH_M = 0.440        # X span [-0.220, +0.220]
HEAD_DEPTH_M = 0.400        # Y span [-0.200, +0.200]
HEAD_HEIGHT_M = 0.448       # Z span [-0.224, +0.224] -> ratio = 1.01818
SHOULDER_L = (-0.155, 0.0, 0.180)
SHOULDER_R = (+0.155, 0.0, 0.180)
HIP_REL_Z = -0.180          # Standing hip Z = 0.380 m
HIP_X = 0.102

# Face decal bounds on head front (-Y) matching expression_gen.py contract
DECAL_X_RANGE = (-0.190, 0.190)
DECAL_Z_RANGE = (-0.190, 0.070)
DEFAULT_LIGHT_DIR = (-0.48, -0.70, 0.53)

DRAWN_INK_GROUP = "Mascot | drawn ink weight"
CURVE_INK_GROUP = "Mascot | curve comic ink"
WEIGHT_ATTR = "MascotInkWeight"


# --------------------------------------------------------------------------- Color & Object Utilities
def _srgb_to_linear(hex_color: str) -> tuple[float, float, float, float]:
    vals = [int(hex_color.lstrip("#")[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in vals]
    return (lin[0], lin[1], lin[2], 1.0)


def _link_only(obj, col, parent=None, mat=None):
    for c in tuple(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    if mat is not None and obj.data is not None and hasattr(obj.data, "materials"):
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    obj.hide_render = False
    obj.hide_viewport = False
    return obj


def _make_empty(name: str, col, loc=(0.0, 0.0, 0.0), parent=None, tag: str | None = None, display_size: float = 0.05):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = display_size
    _link_only(obj, col, parent=parent)
    obj.location = loc
    if tag:
        obj["mascot_tag"] = tag
    return obj


def _make_mesh(name: str, col, verts, faces, mat, *, parent=None, smooth: bool = True, uv=None, tag: str | None = None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = _link_only(bpy.data.objects.new(name, data), col, parent=parent, mat=mat)
    if smooth:
        for poly in data.polygons:
            poly.use_smooth = True
    if uv is not None:
        layer = data.uv_layers.new(name="SurfaceUV")
        for loop in data.loops:
            layer.data[loop.index].uv = uv[loop.vertex_index]
    if tag:
        obj["mascot_tag"] = tag
    return obj


# --------------------------------------------------------------------------- Shaders & Geometry Node Groups
def _make_ink_material(prefix: str):
    name = f"{prefix} | comic ink"
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = _srgb_to_linear(INK_HEX)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = _srgb_to_linear(INK_HEX)
    em.inputs["Strength"].default_value = 1.0
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(em.outputs[0], out.inputs["Surface"])
    return mat


def _make_unlit_material(name: str, hex_color: str, strength: float = 1.0):
    mat = bpy.data.materials.new(name)
    rgba = _srgb_to_linear(hex_color)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = rgba
    em.inputs["Strength"].default_value = strength
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(em.outputs[0], out.inputs["Surface"])
    return mat


def _make_comic_cel_material(
    name: str,
    lit_hex: str,
    shade_hex: str,
    *,
    strength: float = 1.30,
    cutoff_start: float = 0.04,
    cutoff_end: float = -0.14,
    under_bias: float = 0.20,
    max_shade: float = 1.0,
    light_dir=DEFAULT_LIGHT_DIR,
):
    """AgX-calibrated 2-tone comic paint driven by world surface normal & light vector.

    Exposes a named `ShaderNodeCombineXYZ` (`"MascotLightVec"`) updated by `update_ink`
    so scene-specific comic light angles steer cel shadows consistently across every part.
    """
    mat = bpy.data.materials.new(name)
    lit_rgba = _srgb_to_linear(lit_hex)
    shade_rgba = _srgb_to_linear(shade_hex)
    mat.diffuse_color = lit_rgba
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    d = Vector(light_dir).normalized()
    lvec = nodes.new("ShaderNodeCombineXYZ")
    lvec.name = "MascotLightVec"
    lvec.label = "MascotLightVec"
    lvec.inputs["X"].default_value = d.x
    lvec.inputs["Y"].default_value = d.y
    lvec.inputs["Z"].default_value = d.z

    geom = nodes.new("ShaderNodeNewGeometry")
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    links.new(geom.outputs["Normal"], dot.inputs[0])
    links.new(lvec.outputs["Vector"], dot.inputs[1])

    sep_n = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geom.outputs["Normal"], sep_n.inputs[0])

    # Downward-facing under-folds catch subtle comic shadow naturally
    bias_mul = nodes.new("ShaderNodeMath")
    bias_mul.operation = "MULTIPLY"
    links.new(sep_n.outputs["Z"], bias_mul.inputs[0])
    bias_mul.inputs[1].default_value = under_bias

    lit_term = nodes.new("ShaderNodeMath")
    lit_term.operation = "ADD"
    links.new(dot.outputs["Value"], lit_term.inputs[0])
    links.new(bias_mul.outputs[0], lit_term.inputs[1])

    ramp = nodes.new("ShaderNodeMapRange")
    ramp.interpolation_type = "SMOOTHERSTEP"
    ramp.inputs["From Min"].default_value = cutoff_start
    ramp.inputs["From Max"].default_value = cutoff_end
    ramp.inputs["To Min"].default_value = 0.0
    ramp.inputs["To Max"].default_value = max_shade
    links.new(lit_term.outputs[0], ramp.inputs["Value"])

    mix = nodes.new("ShaderNodeMixRGB")
    mix.blend_type = "MIX"
    links.new(ramp.outputs["Result"], mix.inputs["Fac"])
    mix.inputs["Color1"].default_value = lit_rgba
    mix.inputs["Color2"].default_value = shade_rgba

    em = nodes.new("ShaderNodeEmission")
    em.label = "Mascot AgX Comic Paint"
    em.inputs["Strength"].default_value = strength
    links.new(mix.outputs["Color"], em.inputs["Color"])

    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(em.outputs[0], out.inputs["Surface"])
    mat["mascot_cel"] = True
    return mat


def _make_decal_material(name: str, image):
    """Crisp alpha-blended comic expression decal with AgX snow-white teeth parity."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.surface_render_method = "BLENDED"
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.extension = "CLIP"
    tex.interpolation = "Linear"
    if tex.image.source == "FILE" and not tex.image.packed_file:
        tex.image.pack()

    em = nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.25
    links.new(tex.outputs["Color"], em.inputs["Color"])

    transp = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    links.new(transp.outputs[0], mix.inputs[1])
    links.new(em.outputs[0], mix.inputs[2])

    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


def _ensure_drawn_ink_group():
    group = bpy.data.node_groups.get(DRAWN_INK_GROUP)
    if group is not None:
        return group
    group = bpy.data.node_groups.new(DRAWN_INK_GROUP, "GeometryNodeTree")
    io = group.interface
    io.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    io.new_socket(name="Light", in_out="INPUT", socket_type="NodeSocketObject")
    io.new_socket(name="World", in_out="INPUT", socket_type="NodeSocketObject")
    for s_name, val in (("Thin", 0.62), ("Thick", 1.18), ("Low edge", 0.55)):
        sock = io.new_socket(name=s_name, in_out="INPUT", socket_type="NodeSocketFloat")
        sock.default_value = val
    io.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    n, l = group.nodes, group.links
    gin, gout = n.new("NodeGroupInput"), n.new("NodeGroupOutput")

    def mnode(op, a=None, b=None):
        nd = n.new("ShaderNodeMath")
        nd.operation = op
        for idx, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                nd.inputs[idx].default_value = v
            else:
                l.new(v, nd.inputs[idx])
        return nd.outputs[0]

    def axis(obj_sock, vec):
        info = n.new("GeometryNodeObjectInfo")
        info.transform_space = "RELATIVE"
        l.new(obj_sock, info.inputs["Object"])
        const = n.new("FunctionNodeInputVector")
        const.vector = vec
        rot = n.new("FunctionNodeRotateVector")
        l.new(const.outputs[0], rot.inputs["Vector"])
        l.new(info.outputs["Rotation"], rot.inputs["Rotation"])
        return rot.outputs[0]

    def vdot(a, b):
        nd = n.new("ShaderNodeVectorMath")
        nd.operation = "DOT_PRODUCT"
        l.new(a, nd.inputs[0])
        l.new(b, nd.inputs[1])
        return nd.outputs["Value"]

    normal = n.new("GeometryNodeInputNormal").outputs[0]
    outward = n.new("ShaderNodeVectorMath")
    outward.operation = "SCALE"
    l.new(normal, outward.inputs[0])
    outward.inputs["Scale"].default_value = -1.0  # Inverted hull faces inward

    toward_light = axis(gin.outputs["Light"], (0.0, 0.0, 1.0))
    down = axis(gin.outputs["World"], (0.0, 0.0, -1.0))

    lit = vdot(outward.outputs[0], toward_light)
    shade = mnode("MULTIPLY", mnode("SUBTRACT", 1.0, lit), 0.5)
    shade = mnode("POWER", mnode("MAXIMUM", shade, 0.0), 1.35)
    span = mnode("SUBTRACT", gin.outputs["Thick"], gin.outputs["Thin"])
    f = mnode("ADD", gin.outputs["Thin"], mnode("MULTIPLY", span, shade))
    low = mnode("POWER", mnode("MAXIMUM", vdot(outward.outputs[0], down), 0.0), 1.5)
    f = mnode("MULTIPLY", f, mnode("ADD", 1.0, mnode("MULTIPLY", gin.outputs["Low edge"], low)))
    fmax = mnode("MULTIPLY", gin.outputs["Thick"], mnode("ADD", 1.0, gin.outputs["Low edge"]))
    weight = mnode("DIVIDE", f, fmax)

    store = n.new("GeometryNodeStoreNamedAttribute")
    store.data_type = "FLOAT"
    store.domain = "POINT"
    store.inputs["Name"].default_value = WEIGHT_ATTR
    l.new(gin.outputs["Geometry"], store.inputs["Geometry"])
    l.new(weight, store.inputs["Value"])
    l.new(store.outputs["Geometry"], gout.inputs["Geometry"])
    return group


def _ensure_curve_ink_group():
    """Convert a 3D radius-tapered curve into a smooth cloth tube + flipped `#141016` ink hull."""
    group = bpy.data.node_groups.get(CURVE_INK_GROUP)
    if group is not None:
        return group
    group = bpy.data.node_groups.new(CURVE_INK_GROUP, "GeometryNodeTree")
    io = group.interface
    io.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    w_sock = io.new_socket(name="Ink Width", in_out="INPUT", socket_type="NodeSocketFloat")
    w_sock.default_value = 0.0055
    io.new_socket(name="Cloth Mat", in_out="INPUT", socket_type="NodeSocketMaterial")
    io.new_socket(name="Ink Mat", in_out="INPUT", socket_type="NodeSocketMaterial")
    r_sock = io.new_socket(name="Profile Res", in_out="INPUT", socket_type="NodeSocketInt")
    r_sock.default_value = 18
    io.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    n, l = group.nodes, group.links
    gin, gout = n.new("NodeGroupInput"), n.new("NodeGroupOutput")

    circle = n.new("GeometryNodeCurvePrimitiveCircle")
    circle.inputs["Radius"].default_value = 1.0
    l.new(gin.outputs["Profile Res"], circle.inputs["Resolution"])

    to_mesh = n.new("GeometryNodeCurveToMesh")
    to_mesh.inputs["Fill Caps"].default_value = True
    l.new(gin.outputs["Geometry"], to_mesh.inputs["Curve"])
    l.new(circle.outputs["Curve"], to_mesh.inputs["Profile Curve"])

    smooth = n.new("GeometryNodeSetShadeSmooth")
    smooth.inputs["Shade Smooth"].default_value = True
    l.new(to_mesh.outputs["Mesh"], smooth.inputs["Geometry"])

    cloth = n.new("GeometryNodeSetMaterial")
    l.new(smooth.outputs["Geometry"], cloth.inputs["Geometry"])
    l.new(gin.outputs["Cloth Mat"], cloth.inputs["Material"])

    normal = n.new("GeometryNodeInputNormal")
    scale_n = n.new("ShaderNodeVectorMath")
    scale_n.operation = "SCALE"
    l.new(normal.outputs["Normal"], scale_n.inputs[0])
    l.new(gin.outputs["Ink Width"], scale_n.inputs["Scale"])

    extrude = n.new("GeometryNodeSetPosition")
    l.new(smooth.outputs["Geometry"], extrude.inputs["Geometry"])
    l.new(scale_n.outputs["Vector"], extrude.inputs["Offset"])

    flip = n.new("GeometryNodeFlipFaces")
    l.new(extrude.outputs["Geometry"], flip.inputs["Mesh"])

    ink = n.new("GeometryNodeSetMaterial")
    l.new(flip.outputs["Mesh"], ink.inputs["Geometry"])
    l.new(gin.outputs["Ink Mat"], ink.inputs["Material"])

    join = n.new("GeometryNodeJoinGeometry")
    l.new(cloth.outputs["Geometry"], join.inputs["Geometry"])
    l.new(ink.outputs["Geometry"], join.inputs["Geometry"])
    l.new(join.outputs["Geometry"], gout.inputs["Geometry"])
    return group


def _socket_id_map(group) -> dict[str, str]:
    return {
        item.name: item.identifier
        for item in group.interface.items_tree
        if item.item_type == "SOCKET" and item.in_out == "INPUT"
    }


def _add_mesh_ink_hull(
    obj,
    col,
    ink_mat,
    light_empty,
    world_empty,
    *,
    base_thickness: float = 0.0055,
    ink_scale: float = 1.0,
    weights=(0.62, 1.18, 0.55),
    clamp_floor_z: float | None = None,
):
    """Create backface-culled `#141016` inverted hull child mesh."""
    verts = [tuple(v.co) for v in obj.data.vertices]
    faces = [tuple(reversed(p.vertices)) for p in obj.data.polygons]
    ink_obj = _make_mesh(obj.name + " • ink", col, verts, faces, ink_mat, parent=obj, smooth=True)
    for p_dst, p_src in zip(ink_obj.data.polygons, obj.data.polygons):
        p_dst.use_smooth = p_src.use_smooth
    ink_obj.visible_shadow = False
    ink_obj["ricks_role"] = "ink"
    ink_obj["mascot_ink_scale"] = float(ink_scale)

    vg = ink_obj.vertex_groups.new(name=WEIGHT_ATTR)
    if clamp_floor_z is not None:
        # Zero vertical displacement on flat sole vertices so ink never pokes below Z=0.000m
        for idx, v in enumerate(ink_obj.data.vertices):
            w = 0.0 if v.co.z <= clamp_floor_z + 0.0025 else 0.88
            vg.add([idx], w, "REPLACE")
    else:
        vg.add(list(range(len(verts))), 1.0, "REPLACE")
        group = _ensure_drawn_ink_group()
        gmod = ink_obj.modifiers.new("Mascot Drawn Weight", "NODES")
        gmod.node_group = group
        ids = _socket_id_map(group)
        gmod[ids["Light"]] = light_empty
        gmod[ids["World"]] = world_empty
        gmod[ids["Thin"]], gmod[ids["Thick"]], gmod[ids["Low edge"]] = weights

    disp = ink_obj.modifiers.new("Screen-compensated hull", "DISPLACE")
    disp.mid_level = 0.0
    disp.strength = -base_thickness * ink_scale
    disp.vertex_group = WEIGHT_ATTR
    return ink_obj, disp


def _make_inked_curve(
    name: str,
    col,
    coords,
    radii,
    cloth_mat,
    ink_mat,
    *,
    parent=None,
    profile_res: int = 14,
    resolution_u: int = 7,
    ink_scale: float = 0.92,
    tag: str | None = None,
):
    """Create a Bezier curve sleeve/pant with GeoNodes smooth cloth + `#141016` ink hull."""
    cdata = bpy.data.curves.new(name, "CURVE")
    cdata.dimensions = "3D"
    cdata.resolution_u = resolution_u
    cdata.bevel_depth = 0.0
    spline = cdata.splines.new("BEZIER")
    spline.bezier_points.add(len(coords) - 1)
    for pt, co, rad in zip(spline.bezier_points, coords, radii):
        pt.co = co
        pt.radius = rad
        pt.handle_left_type = pt.handle_right_type = "AUTO"
    obj = _link_only(bpy.data.objects.new(name, cdata), col, parent=parent)
    obj.data.materials.append(cloth_mat)
    obj.data.materials.append(ink_mat)
    if tag:
        obj["mascot_tag"] = tag
    obj["mascot_ink_scale"] = float(ink_scale)

    group = _ensure_curve_ink_group()
    mod = obj.modifiers.new("Mascot Curve Ink", "NODES")
    mod.node_group = group
    ids = _socket_id_map(group)
    mod[ids["Ink Width"]] = 0.0055 * ink_scale
    mod[ids["Cloth Mat"]] = cloth_mat
    mod[ids["Ink Mat"]] = ink_mat
    mod[ids["Profile Res"]] = profile_res
    return obj, mod


def _make_simple_tube(name: str, col, coords, radius: float, mat, *, parent=None, res_u: int = 3, bevel_res: int = 1, shadow: bool = False):
    cdata = bpy.data.curves.new(name, "CURVE")
    cdata.dimensions = "3D"
    cdata.resolution_u = res_u
    cdata.bevel_resolution = bevel_res
    cdata.bevel_depth = radius
    cdata.use_fill_caps = True
    spline = cdata.splines.new("BEZIER")
    spline.bezier_points.add(len(coords) - 1)
    for pt, co in zip(spline.bezier_points, coords):
        pt.co = co
        pt.handle_left_type = pt.handle_right_type = "AUTO"
    obj = _link_only(bpy.data.objects.new(name, cdata), col, parent=parent, mat=mat)
    obj.visible_shadow = shadow
    return obj


# --------------------------------------------------------------------------- Sculpted Component Builders
def _build_marshmallow_head(prefix: str, col, head_ctrl, face_mat):
    """Build plump 1:1 marshmallow head (`0.440 x 0.400 x 0.448 m`, ratio `1.018`)."""
    segs, rings = 40, 28
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co.x, v.co.y, v.co.z
        # Subtle mochi lower-cheek fullness matching Reference Images 5, 6, 7
        cheek_swell = 1.0 + 0.048 * max(0.0, -z) * math.sqrt(max(0.0, 1.0 - z * z))
        v.co.x = x * cheek_swell
        v.co.y = y * (1.0 + 0.025 * max(0.0, -z))
        v.co.z = z

    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    sx = HEAD_WIDTH_M / (max(xs) - min(xs))
    sy = HEAD_DEPTH_M / (max(ys) - min(ys))
    sz = HEAD_HEIGHT_M / (max(zs) - min(zs))
    cx = 0.5 * (max(xs) + min(xs))
    cy = 0.5 * (max(ys) + min(ys))
    cz = 0.5 * (max(zs) + min(zs))
    for v in bm.verts:
        v.co.x = (v.co.x - cx) * sx
        v.co.y = (v.co.y - cy) * sy
        v.co.z = (v.co.z - cz) * sz

    mesh = bpy.data.meshes.new(f"{prefix} | head")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth = True
    obj = _link_only(bpy.data.objects.new(f"{prefix} | head", mesh), col, parent=head_ctrl, mat=face_mat)
    obj["mascot_tag"] = "head_mesh"
    return obj


def _build_conformed_face_decals(prefix: str, col, head_ctrl, head_mesh_obj, expr_images: dict):
    """Project 18 conformed face decals onto exact front marshmallow head surface."""
    verts_local = [v.co.copy() for v in head_mesh_obj.data.vertices]
    polys_local = [tuple(p.vertices) for p in head_mesh_obj.data.polygons]
    bvh = BVHTree.FromPolygons(verts_local, polys_local)

    nx, nz = 25, 23
    x0, x1 = DECAL_X_RANGE
    z0, z1 = DECAL_Z_RANGE
    base_verts, base_faces, base_uv = [], [], []
    rx, ry, rz = HEAD_WIDTH_M * 0.5, HEAD_DEPTH_M * 0.5, HEAD_HEIGHT_M * 0.5

    for j in range(nz):
        v = j / (nz - 1)
        z = z0 + v * (z1 - z0)
        for i in range(nx):
            u = i / (nx - 1)
            x = x0 + u * (x1 - x0)
            hit_loc, hit_norm, _, _ = bvh.ray_cast(Vector((x, -0.55, z)), Vector((0.0, 1.0, 0.0)), 1.0)
            if hit_loc is not None and hit_loc.y < 0.0:
                p = hit_loc + hit_norm * 0.0028
            else:
                inside = max(0.03, 1.0 - (x / rx) ** 2 - (z / rz) ** 2)
                p = Vector((x, -ry * math.sqrt(inside) - 0.0028, z))
            base_verts.append((p.x, p.y, p.z))
            base_uv.append((u, v))
            if i > 0 and j > 0:
                k = len(base_verts) - 1
                base_faces.append((k - nx - 1, k - nx, k, k - 1))

    decal_objs = {}
    for expr_name in ALL_EXPRESSIONS:
        img = expr_images[expr_name]
        mat = _make_decal_material(f"{prefix} | expr_{expr_name}", img)
        obj = _make_mesh(
            f"{prefix} | expr_{expr_name}",
            col,
            base_verts,
            base_faces,
            mat,
            parent=head_ctrl,
            smooth=True,
            uv=base_uv,
            tag=f"expr:{expr_name}",
        )
        obj.visible_shadow = False
        is_default = expr_name == "idle_cute"
        obj.hide_render = not is_default
        obj.hide_viewport = not is_default
        decal_objs[expr_name] = obj
    return decal_objs


def _beanie_rim_z(azimuth: float) -> float:
    """Smooth brow-to-nape rim curve (`a = -pi/2` is front `-Y`, `a = +pi/2` is back `+Y`)."""
    # Front (-Y): sin(a) = -1 -> z = +0.068m (clears big oval eyes & raised brows)
    # Sides (±X): sin(a) = 0  -> z = -0.022m (hugs temples cozily like Images 5, 6, 7)
    # Back (+Y):  sin(a) = +1 -> z = -0.072m (wraps nape cleanly above yellow hood)
    s = math.sin(azimuth)
    front = max(0.0, -s)
    back = max(0.0, s)
    return -0.022 + 0.090 * (front ** 0.85) - 0.050 * (back ** 1.05)


def _build_crimson_beanie(prefix: str, col, head_ctrl, beanie_mat, ink_mat, highlight_mat, light_empty, world_empty):
    """Build `4°`-tilted crimson knit beanie dome, plump folded cuff, 6 dark ribs & highlight."""
    pivot = _make_empty(f"{prefix} | beanie_pivot", col, loc=(0.0, 0.0, 0.0), parent=head_ctrl)
    pivot.rotation_euler = Euler((math.radians(-2.5), math.radians(4.0), 0.0), "XYZ")

    ink_records = []
    ring_n = 36
    rx_base = HEAD_WIDTH_M * 0.5 + 0.012   # 0.232 m
    ry_base = HEAD_DEPTH_M * 0.5 + 0.012   # 0.212 m
    z_crown = 0.318                        # Standing top ~ 0.960 + 0.318 = 1.278 m

    # 1. Plump Ribbed Knit Dome (tucked inside cuff at base, rising to rounded crown)
    dome_verts, dome_faces = [], []
    dome_rows = 13
    for j in range(dome_rows):
        t = j / (dome_rows - 1)  # 0 = base under cuff, 1 = near crown
        polar = (1.0 - t) * (math.pi * 0.49) + 0.02
        sin_p = math.sin(polar)
        cos_p = math.cos(polar)
        for i in range(ring_n):
            a = math.tau * i / ring_n
            rib_swell = 1.0 + 0.014 * abs(math.cos(3.0 * (a + math.pi * 0.5))) * (sin_p ** 0.7)
            z_rim = _beanie_rim_z(a) + 0.022
            z = z_rim + (z_crown - z_rim) * (cos_p ** 0.86)
            puff = 1.0 + 0.08 * math.sin(math.pi * (1.0 - t))
            x = rx_base * sin_p * puff * rib_swell * math.cos(a)
            y = ry_base * sin_p * puff * rib_swell * math.sin(a) + 0.004
            dome_verts.append((x, y, z))
            if j > 0:
                k = j * ring_n + i
                nxt = j * ring_n + ((i + 1) % ring_n)
                dome_faces.append((k - ring_n, nxt - ring_n, nxt, k))
    # Cap crown pole cleanly
    crown_idx = len(dome_verts)
    dome_verts.append((0.0, 0.004, z_crown + 0.002))
    top_start = (dome_rows - 1) * ring_n
    for i in range(ring_n):
        nxt = (i + 1) % ring_n
        dome_faces.append((top_start + i, top_start + nxt, crown_idx))
    # Close inner base ring so hull is manifold
    bot_idx = len(dome_verts)
    dome_verts.append((0.0, 0.0, 0.06))
    for i in range(ring_n):
        nxt = (i + 1) % ring_n
        dome_faces.append((nxt, i, bot_idx))

    dome_obj = _make_mesh(f"{prefix} | beanie_dome", col, dome_verts, dome_faces, beanie_mat, parent=pivot, smooth=True)
    ink_records.append(_add_mesh_ink_hull(dome_obj, col, ink_mat, light_empty, world_empty, ink_scale=1.05))

    # 2. Plump Folded Cuff Band (360° closed tube cross-section hugging brow & temples)
    cuff_verts, cuff_faces = [], []
    prof_n = 10
    cuff_half_h = 0.046
    cuff_thick = 0.024
    for i in range(ring_n):
        a = math.tau * i / ring_n
        ca, sa = math.cos(a), math.sin(a)
        z_bot = _beanie_rim_z(a)
        z_mid = z_bot + cuff_half_h
        rib_cuff = 1.0 + 0.010 * abs(math.cos(3.0 * (a + math.pi * 0.5)))
        # Inner wall covers head surface completely down to bottom rim (zero side/back white sliver!)
        r_in_x = HEAD_WIDTH_M * 0.5 * math.sqrt(max(0.56, 1.0 - (z_bot / 0.245) ** 2)) + 0.004
        r_in_y = HEAD_DEPTH_M * 0.5 * math.sqrt(max(0.56, 1.0 - (z_bot / 0.245) ** 2)) + 0.004
        r_mid_x = (r_in_x + cuff_thick) * rib_cuff
        r_mid_y = (r_in_y + cuff_thick) * rib_cuff
        for p in range(prof_n):
            theta = math.tau * p / prof_n
            # Pillowy stadium cross-section around cuff ring
            rad_t = 0.5 + 0.5 * math.cos(theta)  # 1 = outer face, 0 = inner face against head
            rx = r_in_x + (r_mid_x - r_in_x + 0.010) * rad_t
            ry = r_in_y + (r_mid_y - r_in_y + 0.010) * rad_t
            zz = z_mid + cuff_half_h * math.sin(theta)
            cuff_verts.append((rx * ca, ry * sa + 0.002, zz))
    for i in range(ring_n):
        ni = (i + 1) % ring_n
        for p in range(prof_n):
            np_ = (p + 1) % prof_n
            v0 = i * prof_n + p
            v1 = ni * prof_n + p
            v2 = ni * prof_n + np_
            v3 = i * prof_n + np_
            cuff_faces.append((v0, v1, v2, v3))

    cuff_obj = _make_mesh(f"{prefix} | beanie_cuff", col, cuff_verts, cuff_faces, beanie_mat, parent=pivot, smooth=True)
    ink_records.append(_add_mesh_ink_hull(cuff_obj, col, ink_mat, light_empty, world_empty, ink_scale=0.98))

    # 3. Curved `#141016` Vertical Knit Rib Grooves across Dome & Cuff (matching Images 5, 6, 7)
    # 6 primary front/side curved ribs + 4 back ribs so turnaround Back view is equally detailed!
    rib_angles = [
        -math.pi * 0.5 + math.radians(deg)
        for deg in (-74, -44, -15, 15, 44, 74, 112, 148, -148, -112)
    ]
    for r_idx, a in enumerate(rib_angles):
        ca, sa = math.cos(a), math.sin(a)
        z_rim = _beanie_rim_z(a)
        # Dome rib curve from top of cuff up toward crown
        dome_pts = []
        for s_i in range(7):
            u = s_i / 6.0
            polar = (1.0 - u * 0.82) * (math.pi * 0.47) + 0.06
            sin_p, cos_p = math.sin(polar), math.cos(polar)
            puff = 1.0 + 0.08 * math.sin(math.pi * (1.0 - u * 0.85))
            rib_swell = 1.0 + 0.014 * abs(math.cos(3.0 * (a + math.pi * 0.5))) * (sin_p ** 0.7)
            zz = (z_rim + 0.022) + (z_crown - z_rim - 0.022) * (cos_p ** 0.86)
            xx = (rx_base * sin_p * puff * rib_swell + 0.0025) * ca
            yy = (ry_base * sin_p * puff * rib_swell + 0.0025) * sa + 0.004
            dome_pts.append((xx, yy, zz))
        rib_curve = _make_simple_tube(f"{prefix} | beanie_rib_{r_idx}", col, dome_pts, 0.0046, ink_mat, parent=pivot)
        for k_i, pt in enumerate(rib_curve.data.splines[0].bezier_points):
            pt.radius = 0.55 + 0.45 * math.sin(math.pi * (k_i + 0.6) / 7.2)

        # Matching short curved rib tick on the folded cuff band
        r_in_x = HEAD_WIDTH_M * 0.5 * math.sqrt(max(0.56, 1.0 - (z_rim / 0.245) ** 2)) + 0.004
        r_in_y = HEAD_DEPTH_M * 0.5 * math.sqrt(max(0.56, 1.0 - (z_rim / 0.245) ** 2)) + 0.004
        cuff_pts = []
        for c_i in range(5):
            th = -math.pi * 0.42 + (c_i / 4.0) * (math.pi * 0.84)
            rad_t = 0.5 + 0.5 * math.cos(th)
            rx = r_in_x + (cuff_thick + 0.0115) * rad_t
            ry = r_in_y + (cuff_thick + 0.0115) * rad_t
            zz = z_rim + cuff_half_h + cuff_half_h * math.sin(th)
            cuff_pts.append((rx * ca, ry * sa + 0.002, zz))
        _make_simple_tube(f"{prefix} | beanie_cuff_rib_{r_idx}", col, cuff_pts, 0.0042, ink_mat, parent=pivot)

    # 4. Crisp Glossy White Comic Highlight Stroke on Upper-Left Beanie Dome Curve
    hl_pts = []
    for i in range(8):
        t = i / 7.0
        a = -math.pi * 0.5 - math.radians(42.0 - 26.0 * t)
        polar = 0.94 - 0.36 * t
        sin_p, cos_p = math.sin(polar), math.cos(polar)
        puff = 1.0 + 0.08 * math.sin(math.pi * (1.0 - 0.55 * t))
        rib_swell = 1.0 + 0.014 * abs(math.cos(3.0 * (a + math.pi * 0.5))) * (sin_p ** 0.7)
        z_rim = _beanie_rim_z(a) + 0.022
        zz = z_rim + (z_crown - z_rim) * (cos_p ** 0.86) + 0.004
        xx = (rx_base * sin_p * puff * rib_swell + 0.0065) * math.cos(a)
        yy = (ry_base * sin_p * puff * rib_swell + 0.0065) * math.sin(a) + 0.004
        hl_pts.append((xx, yy, zz))
    hl = _make_simple_tube(f"{prefix} | beanie_highlight", col, hl_pts, 0.0072, highlight_mat, parent=pivot)
    for i, pt in enumerate(hl.data.splines[0].bezier_points):
        pt.radius = 0.18 + 0.82 * math.sin(math.pi * i / 7.0)

    return ink_records


def _build_yellow_hoodie(prefix: str, col, body_ctrl, hoodie_mat, white_mat, ink_mat, highlight_mat, light_empty, world_empty):
    """Build A-line cozy yellow hoodie, 3D collar + back hood, kangaroo pocket & rigged drawstrings."""
    ink_records = []
    ring_n = 36

    # 1. Plump A-Line Bell/Pear Hoodie Torso (z_body in [-0.205, +0.205])
    # Format: (z, rx, ry, y_offset)
    torso_profile = [
        (-0.205, 0.178, 0.136, -0.004),  # Bottom hem inner lip
        (-0.192, 0.192, 0.148, -0.006),  # Ribbed waist cuff mid
        (-0.162, 0.194, 0.150, -0.007),  # Ribbed waist cuff top
        (-0.148, 0.204, 0.160, -0.010),  # Cozy oversized belly puff above cuff!
        (-0.105, 0.206, 0.164, -0.012),  # Widest bell contour (~0.412m wide)
        (-0.045, 0.194, 0.154, -0.010),
        (0.025, 0.178, 0.142, -0.006),
        (0.095, 0.162, 0.128, -0.003),
        (0.155, 0.146, 0.116, 0.000),
        (0.195, 0.124, 0.100, 0.002),    # Shoulder/neck base
    ]
    t_verts, t_faces = [], []
    for j, (zz, rx, ry, y0) in enumerate(torso_profile):
        for i in range(ring_n):
            a = math.tau * i / ring_n
            # Slightly fuller front belly than flat lower back
            front_belly = 1.0 + 0.045 * max(0.0, -math.sin(a)) * max(0.0, 1.0 - abs(zz + 0.08) / 0.14)
            x = rx * math.cos(a)
            y = ry * math.sin(a) * front_belly + y0
            t_verts.append((x, y, zz))
            if j > 0:
                k = j * ring_n + i
                nxt = j * ring_n + ((i + 1) % ring_n)
                t_faces.append((k - ring_n, nxt - ring_n, nxt, k))
    bot_c = len(t_verts)
    t_verts.append((0.0, -0.004, -0.206))
    for i in range(ring_n):
        t_faces.append(((i + 1) % ring_n, i, bot_c))
    top_c = len(t_verts)
    t_verts.append((0.0, 0.002, 0.202))
    top_base = (len(torso_profile) - 1) * ring_n
    for i in range(ring_n):
        t_faces.append((top_base + i, top_base + ((i + 1) % ring_n), top_c))

    torso_obj = _make_mesh(f"{prefix} | hoodie_torso", col, t_verts, t_faces, hoodie_mat, parent=body_ctrl, smooth=True)
    ink_records.append(_add_mesh_ink_hull(torso_obj, col, ink_mat, light_empty, world_empty, ink_scale=1.05))

    # Crisp `#141016` waist-cuff seam ring around z = -0.160
    cuff_seam_pts = []
    for i in range(17):
        a = math.tau * (i % 16) / 16
        front_belly = 1.0 + 0.045 * max(0.0, -math.sin(a)) * 0.43
        cuff_seam_pts.append((0.197 * math.cos(a), 0.153 * math.sin(a) * front_belly - 0.008, -0.160))
    _make_simple_tube(f"{prefix} | hoodie_waist_seam", col, cuff_seam_pts, 0.0032, ink_mat, parent=body_ctrl, res_u=2, bevel_res=1)

    # 2. Dark Inner Chin/Neck Shadow Plug (guarantees ZERO neck gap from any angle + V-hollow shadow)
    neck_plug_verts, neck_plug_faces = [], []
    for j, (zz, rr) in enumerate([(0.155, 0.105), (0.205, 0.112), (0.248, 0.108)]):
        for i in range(24):
            a = math.tau * i / 24
            neck_plug_verts.append((rr * math.cos(a), rr * 0.92 * math.sin(a) - 0.005, zz))
            if j > 0:
                k = j * 24 + i
                nxt = j * 24 + ((i + 1) % 24)
                neck_plug_faces.append((k - 24, nxt - 24, nxt, k))
    n_top = len(neck_plug_verts)
    neck_plug_verts.append((0.0, -0.005, 0.250))
    for i in range(24):
        neck_plug_faces.append((48 + i, 48 + ((i + 1) % 24), n_top))
    neck_plug = _make_mesh(f"{prefix} | neck_recess", col, neck_plug_verts, neck_plug_faces, ink_mat, parent=body_ctrl, smooth=True)
    neck_plug.visible_shadow = False

    # 3. 3D Sculpted Cozy Hood Collar (snugly bunched around chin & cheeks, V-crossover in front)
    collar_verts, collar_faces = [], []
    col_n, prof_n = 32, 10
    for i in range(col_n):
        a = math.tau * i / col_n  # -pi/2 is front (-Y), +pi/2 is back (+Y)
        ca, sa = math.cos(a), math.sin(a)
        front_dip = max(0.0, -sa) ** 1.6  # Cute V-dip right at center-front under chin
        side_puff = abs(ca) ** 0.9
        z_center = 0.194 - 0.026 * front_dip + 0.016 * side_puff + 0.012 * max(0.0, sa)
        rx_c = 0.148 + 0.022 * side_puff
        ry_c = 0.132 + 0.020 * max(0.0, sa)
        tube_r = 0.036 + 0.008 * side_puff
        for p in range(prof_n):
            th = math.tau * p / prof_n
            rad_off = tube_r * math.cos(th)
            zz = z_center + tube_r * 0.92 * math.sin(th)
            collar_verts.append(((rx_c + rad_off) * ca, (ry_c + rad_off) * sa - 0.006, zz))
    for i in range(col_n):
        ni = (i + 1) % col_n
        for p in range(prof_n):
            np_ = (p + 1) % prof_n
            collar_faces.append((i * prof_n + p, ni * prof_n + p, ni * prof_n + np_, i * prof_n + np_))

    collar_obj = _make_mesh(f"{prefix} | hood_collar", col, collar_verts, collar_faces, hoodie_mat, parent=body_ctrl, smooth=True)
    ink_records.append(_add_mesh_ink_hull(collar_obj, col, ink_mat, light_empty, world_empty, ink_scale=0.95))

    # Center-front collar overlap V-seam line (matching Images 6 & 7)
    _make_simple_tube(
        f"{prefix} | collar_v_seam",
        col,
        [(-0.024, -0.148, 0.176), (0.004, -0.156, 0.144), (0.018, -0.160, 0.088)],
        0.0036,
        ink_mat,
        parent=body_ctrl,
    )

    # 4. Sculpted Draped 3D Back Hood resting behind neck/shoulders (for Side & Back turnaround!)
    bh_bm = bmesh.new()
    bmesh.ops.create_uvsphere(bh_bm, u_segments=22, v_segments=14, radius=1.0)
    for v in bh_bm.verts:
        x, y, z = v.co.x, v.co.y, v.co.z
        # Soft teardrop cloth pouch draped onto upper back (+Y)
        drape = 1.0 + 0.25 * max(0.0, -z)
        nx = x * 0.168 * drape
        ny = 0.118 + max(-0.04, y * 0.095) + 0.035 * max(0.0, -z)
        nz = 0.145 + z * 0.095 - 0.025 * (x * x)
        v.co = Vector((nx, ny, nz))
    bh_mesh = bpy.data.meshes.new(f"{prefix} | back_hood")
    bh_bm.to_mesh(bh_mesh)
    bh_bm.free()
    bh_mesh.update()
    for p in bh_mesh.polygons:
        p.use_smooth = True
    bh_obj = _link_only(bpy.data.objects.new(f"{prefix} | back_hood", bh_mesh), col, parent=body_ctrl, mat=hoodie_mat)
    ink_records.append(_add_mesh_ink_hull(bh_obj, col, ink_mat, light_empty, world_empty, ink_scale=0.95))

    # Subtle fold crease on back hood
    _make_simple_tube(
        f"{prefix} | back_hood_fold",
        col,
        [(-0.085, 0.212, 0.155), (0.0, 0.228, 0.112), (0.085, 0.212, 0.155)],
        0.0035,
        ink_mat,
        parent=body_ctrl,
    )

    # 5. Front Kangaroo Pouch Pocket + Stitched `#141016` Ink Seams
    pk_nx, pk_nz = 17, 11
    pk_verts, pk_faces = [], []
    for j in range(pk_nz):
        v = j / (pk_nz - 1)  # 0 = bottom (-0.158), 1 = top (-0.018)
        zz = -0.158 + v * 0.140
        # Classic trapezoid kangaroo pocket: wider near bottom/mid, narrower flat top
        half_w = 0.142 - 0.048 * (v ** 1.15) if v > 0.32 else 0.136 + 0.018 * (v / 0.32)
        puff_out = 0.013 * math.sin(math.pi * min(1.0, v * 1.12))
        base_ry = 0.158 + 0.010 * math.sin(math.pi * v)
        for i in range(pk_nx):
            u = i / (pk_nx - 1)
            xx = (2.0 * u - 1.0) * half_w
            edge_taper = math.cos(0.42 * math.pi * (2.0 * u - 1.0))
            ang = math.asin(max(-0.92, min(0.92, xx / 0.205)))
            yy = -(base_ry + puff_out * edge_taper) * math.cos(ang) - 0.011
            pk_verts.append((xx, yy, zz))
            if i > 0 and j > 0:
                k = len(pk_verts) - 1
                pk_faces.append((k - pk_nx - 1, k - pk_nx, k, k - 1))
    pocket_obj = _make_mesh(f"{prefix} | kangaroo_pocket", col, pk_verts, pk_faces, hoodie_mat, parent=body_ctrl, smooth=True)
    pocket_obj.visible_shadow = False

    # Crisp `#141016` pocket seam lines (top edge + left/right angled hand openings)
    def _surface_front_y(xx: float, zz: float, extra: float = 0.012) -> float:
        ang = math.asin(max(-0.92, min(0.92, xx / 0.206)))
        ry = 0.160 + 0.008 * max(0.0, 1.0 - abs(zz + 0.09) / 0.12)
        return -(ry + extra) * math.cos(ang) - 0.011

    top_seam = [(xx, _surface_front_y(xx, -0.018, 0.009), -0.018) for xx in (-0.094, -0.047, 0.0, 0.047, 0.094)]
    _make_simple_tube(f"{prefix} | pocket_seam_top", col, top_seam, 0.0036, ink_mat, parent=body_ctrl)
    for side, s_lbl in ((-1, "L"), (1, "R")):
        side_pts = [
            (side * 0.094, _surface_front_y(side * 0.094, -0.018, 0.009), -0.018),
            (side * 0.126, _surface_front_y(side * 0.126, -0.068, 0.012), -0.068),
            (side * 0.146, _surface_front_y(side * 0.146, -0.115, 0.010), -0.115),
            (side * 0.138, _surface_front_y(side * 0.138, -0.158, 0.006), -0.158),
        ]
        _make_simple_tube(f"{prefix} | pocket_seam_{s_lbl}", col, side_pts, 0.0036, ink_mat, parent=body_ctrl)

    # Subtle white comic highlight stroke on upper-left hoodie chest
    hl_hoodie = [
        (-0.132, -0.095, 0.135),
        (-0.158, -0.105, 0.055),
        (-0.175, -0.112, -0.035),
    ]
    h_tube = _make_simple_tube(f"{prefix} | hoodie_highlight", col, hl_hoodie, 0.0045, highlight_mat, parent=body_ctrl)
    for i, pt in enumerate(h_tube.data.splines[0].bezier_points):
        pt.radius = 0.25 + 0.75 * math.sin(math.pi * i / 2.0)

    # 6. 2 Black Metal Eyelets + 2 Rigged 3D White Hoodie Drawstrings with Black Outlines & Aglet Tips
    string_pivots = []
    for side, s_lbl in ((-1, "L"), (1, "R")):
        ex, ey, ez = side * 0.048, -0.171, 0.154
        # Bold jet-black metal eyelet seated visibly on the front hood-collar lip (Images 5/6/7)
        ey_bm = bmesh.new()
        bmesh.ops.create_uvsphere(ey_bm, u_segments=14, v_segments=10, radius=1.0)
        for v in ey_bm.verts:
            v.co = Vector((v.co.x * 0.016, v.co.y * 0.010, v.co.z * 0.016))
        ey_mesh = bpy.data.meshes.new(f"{prefix} | eyelet_{s_lbl}")
        ey_bm.to_mesh(ey_mesh)
        ey_bm.free()
        ey_obj = _link_only(bpy.data.objects.new(f"{prefix} | eyelet_{s_lbl}", ey_mesh), col, parent=body_ctrl, mat=ink_mat)
        ey_obj.location = (ex, ey, ez)
        ey_obj.rotation_euler = Euler((0.14, side * -0.16, 0.0), "XYZ")
        ey_obj.visible_shadow = False

        # Drawstring pivot Empty hanging cleanly outside collar & upper chest
        s_piv = _make_empty(
            f"{prefix} | string_{s_lbl}",
            col,
            loc=(ex, -0.175, ez - 0.004),
            parent=body_ctrl,
            tag=f"string_{s_lbl}",
            display_size=0.03,
        )
        # Snow-white 3D cord + crisp `#141016` comic outline + black aglet tip
        cord_len = 0.134
        cord_verts, cord_faces = [], []
        c_segs = 12
        cord_rings = [
            (0.0, 0.0, 0.0, 0.0080),
            (side * 0.003, 0.002, -0.044, 0.0086),
            (side * 0.006, 0.004, -0.092, 0.0086),
            (side * 0.008, 0.005, -cord_len, 0.0082),
            (side * 0.008, 0.005, -cord_len - 0.002, 0.001),
        ]
        for j, (cx, cy, cz, cr) in enumerate(cord_rings):
            for i in range(c_segs):
                a = math.tau * i / c_segs
                cord_verts.append((cx + cr * math.cos(a), cy + cr * math.sin(a), cz))
                if j > 0:
                    k = j * c_segs + i
                    nxt = j * c_segs + ((i + 1) % c_segs)
                    cord_faces.append((k - c_segs, nxt - c_segs, nxt, k))
        cord_obj = _make_mesh(f"{prefix} | drawstring_{s_lbl}", col, cord_verts, cord_faces, white_mat, parent=s_piv, smooth=True)
        cord_obj.visible_shadow = False
        ink_records.append(
            _add_mesh_ink_hull(
                cord_obj,
                col,
                ink_mat,
                light_empty,
                world_empty,
                base_thickness=0.0048,
                ink_scale=0.94,
                weights=(0.95, 1.10, 0.35),
            )
        )

        # Black aglet tip at bottom of cord
        ag_verts, ag_faces = [], []
        ag_rings = [
            (side * 0.007, 0.0045, -cord_len + 0.018, 0.0092),
            (side * 0.008, 0.0050, -cord_len - 0.005, 0.0088),
            (side * 0.008, 0.0050, -cord_len - 0.008, 0.001),
        ]
        for j, (ax, ay, az, ar) in enumerate(ag_rings):
            for i in range(10):
                a = math.tau * i / 10
                ag_verts.append((ax + ar * math.cos(a), ay + ar * math.sin(a), az))
                if j > 0:
                    k = j * 10 + i
                    nxt = j * 10 + ((i + 1) % 10)
                    ag_faces.append((k - 10, nxt - 10, nxt, k))
        ag_obj = _make_mesh(f"{prefix} | aglet_{s_lbl}", col, ag_verts, ag_faces, ink_mat, parent=s_piv, smooth=True)
        ag_obj.visible_shadow = False
        string_pivots.append(s_piv)

    return ink_records, string_pivots


# --------------------------------------------------------------------------- Sculpted 7 Hand Poses
def _append_ellipsoid(bm, center, radii, rot_euler=(0.0, 0.0, 0.0), u_seg: int = 14, v_seg: int = 10):
    tmp = bmesh.new()
    bmesh.ops.create_uvsphere(tmp, u_segments=u_seg, v_segments=v_seg, radius=1.0)
    rot_m = Euler(rot_euler, "XYZ").to_matrix()
    ctr = Vector(center)
    rx, ry, rz = radii
    vmap = {}
    for v in tmp.verts:
        p = Vector((v.co.x * rx, v.co.y * ry, v.co.z * rz))
        vmap[v.index] = bm.verts.new(ctr + (rot_m @ p))
    for f in tmp.faces:
        bm.faces.new([vmap[v.index] for v in f.verts])
    tmp.free()


def _append_finger_capsule(bm, points, radii, segs: int = 9):
    """Append a smooth closed cartoon sausage finger with rounded hemispherical end-caps."""
    pts = [Vector(p) for p in points]
    n_pts = len(pts)
    # Build smooth interpolated spine
    dense_pts, dense_rad = [], []
    steps_per = 3
    for idx in range(n_pts - 1):
        p0, p1 = pts[idx], pts[idx + 1]
        r0, r1 = radii[idx], radii[idx + 1]
        cnt = steps_per if idx < n_pts - 2 else steps_per + 1
        for s in range(cnt):
            t = s / steps_per
            # Smooth Catmull-like midpoint curve when 3+ points
            if n_pts == 3:
                u = (idx + t) / 2.0
                pos = ((1 - u) ** 2) * pts[0] + 2 * (1 - u) * u * pts[1] + (u ** 2) * pts[2]
                rad = (1 - u) * radii[0] + u * radii[-1]
                if idx == 0 or s > 0:
                    dense_pts.append(pos)
                    dense_rad.append(rad)
            else:
                if idx == 0 or s > 0:
                    dense_pts.append(p0.lerp(p1, t))
                    dense_rad.append(r0 + (r1 - r0) * t)

    # Deduplicate if needed
    clean_pts, clean_rad = [dense_pts[0]], [dense_rad[0]]
    for p, r in zip(dense_pts[1:], dense_rad[1:]):
        if (p - clean_pts[-1]).length > 1e-4:
            clean_pts.append(p)
            clean_rad.append(r)

    tangents = []
    for i in range(len(clean_pts)):
        if i == 0:
            t = (clean_pts[1] - clean_pts[0]).normalized()
        elif i == len(clean_pts) - 1:
            t = (clean_pts[-1] - clean_pts[-2]).normalized()
        else:
            t = (clean_pts[i + 1] - clean_pts[i - 1]).normalized()
        tangents.append(t)

    # Add rounded start & tip hemisphere rings
    rings = []
    t0 = tangents[0]
    r0 = clean_rad[0]
    rings.append((clean_pts[0] - t0 * (r0 * 0.78), t0, r0 * 0.42))
    rings.append((clean_pts[0] - t0 * (r0 * 0.35), t0, r0 * 0.82))
    for p, t, r in zip(clean_pts, tangents, clean_rad):
        rings.append((p, t, r))
    t_end = tangents[-1]
    r_end = clean_rad[-1]
    rings.append((clean_pts[-1] + t_end * (r_end * 0.45), t_end, r_end * 0.84))
    rings.append((clean_pts[-1] + t_end * (r_end * 0.82), t_end, r_end * 0.45))

    # Parallel transport frame along spine
    up = Vector((0.0, 0.0, 1.0)) if abs(rings[0][1].z) < 0.9 else Vector((1.0, 0.0, 0.0))
    n_vec = rings[0][1].cross(up).normalized()
    ring_verts = []
    prev_t = rings[0][1]
    for p, t, r in rings:
        rot_q = prev_t.rotation_difference(t)
        n_vec = (rot_q @ n_vec).normalized()
        b_vec = t.cross(n_vec).normalized()
        prev_t = t
        row = []
        for k in range(segs):
            ang = math.tau * k / segs
            v = bm.verts.new(p + (n_vec * math.cos(ang) + b_vec * math.sin(ang)) * r)
            row.append(v)
        ring_verts.append(row)

    for j in range(1, len(ring_verts)):
        r_prev, r_curr = ring_verts[j - 1], ring_verts[j]
        for k in range(segs):
            nk = (k + 1) % segs
            bm.faces.new((r_prev[k], r_prev[nk], r_curr[nk], r_curr[k]))

    v_start = bm.verts.new(clean_pts[0] - t0 * (r0 * 0.96))
    for k in range(segs):
        nk = (k + 1) % segs
        bm.faces.new((ring_verts[0][nk], ring_verts[0][k], v_start))

    v_tip = bm.verts.new(clean_pts[-1] + t_end * (r_end * 0.98))
    for k in range(segs):
        nk = (k + 1) % segs
        bm.faces.new((ring_verts[-1][k], ring_verts[-1][nk], v_tip))


def _build_hand_pose_mesh(prefix: str, col, wrist_pivot, side: int, pose_name: str, hand_mat, ink_mat, light_empty, world_empty):
    """Build one of the 7 puffy snow-white marshmallow hand poses for `side` (-1=L, +1=R).

    Wrist local frame: `-Y` points outward along forearm; `+Z` points up; `-side*X` is inward.
    """
    s_lbl = "L" if side < 0 else "R"
    inw = -float(side)  # Inward toward body centerline
    outw = float(side)  # Outward away from body centerline
    bm = bmesh.new()

    if pose_name == "open_stop":
        # Hero Image 5: Big expressive 5-finger spread palm facing -Y camera!
        _append_ellipsoid(bm, (0.0, -0.012, 0.004), (0.034, 0.024, 0.032))
        _append_ellipsoid(bm, (outw * 0.006, -0.038, 0.032), (0.056, 0.030, 0.058), u_seg=20, v_seg=14)
        # Inward chunky horizontal thumb
        _append_finger_capsule(
            bm,
            [(inw * 0.022, -0.036, 0.014), (inw * 0.060, -0.042, 0.022), (inw * 0.094, -0.046, 0.030)],
            [0.022, 0.020, 0.0185],
        )
        # 4 wide-fanned plump cartoon fingers (index -> pinky)
        fan_specs = [
            ([(inw * 0.026, -0.038, 0.062), (inw * 0.036, -0.043, 0.108), (inw * 0.044, -0.047, 0.146)], [0.019, 0.018, 0.017]),
            ([(outw * 0.004, -0.039, 0.068), (outw * 0.011, -0.044, 0.118), (outw * 0.016, -0.048, 0.158)], [0.0195, 0.0185, 0.0175]),
            ([(outw * 0.030, -0.037, 0.058), (outw * 0.058, -0.042, 0.102), (outw * 0.080, -0.046, 0.136)], [0.0185, 0.0175, 0.0165]),
            ([(outw * 0.044, -0.034, 0.036), (outw * 0.080, -0.038, 0.062), (outw * 0.108, -0.042, 0.084)], [0.0175, 0.0165, 0.0155]),
        ]
        for pts, rads in fan_specs:
            _append_finger_capsule(bm, pts, rads)

    elif pose_name == "power_claw":
        # Hero Image 6: Dramatic upturned cupped palm + 4 separated curled claw fingers + outward thumb!
        _append_ellipsoid(bm, (0.0, -0.015, 0.0), (0.032, 0.024, 0.028))
        _append_ellipsoid(bm, (0.0, -0.044, 0.002), (0.052, 0.040, 0.028), u_seg=16, v_seg=12)
        # Outward upturned thumb fanned clearly away from index finger
        _append_finger_capsule(
            bm,
            [(outw * 0.042, -0.036, 0.008), (outw * 0.076, -0.050, 0.042), (outw * 0.072, -0.042, 0.084)],
            [0.0155, 0.0140, 0.0125],
        )
        # 4 fanned upturned claw fingers (`~34-40 mm` apart at mid/tips so each has its own `#141016` outline!)
        claw_specs = [
            ([(outw * 0.035, -0.065, 0.006), (outw * 0.048, -0.098, 0.044), (outw * 0.044, -0.084, 0.094)], [0.0132, 0.0122, 0.0112]),
            ([(outw * 0.011, -0.072, 0.008), (outw * 0.014, -0.106, 0.052), (outw * 0.012, -0.090, 0.104)], [0.0135, 0.0125, 0.0114]),
            ([(inw * 0.014, -0.071, 0.007), (inw * 0.020, -0.104, 0.048), (inw * 0.018, -0.088, 0.098)], [0.0130, 0.0120, 0.0110]),
            ([(inw * 0.038, -0.064, 0.004), (inw * 0.052, -0.094, 0.040), (inw * 0.048, -0.080, 0.086)], [0.0124, 0.0114, 0.0104]),
        ]
        for pts, rads in claw_specs:
            _append_finger_capsule(bm, pts, rads)

    elif pose_name == "behind_head":
        # Hero Image 7: Smooth tucked pillowy mitt nestled cleanly behind red beanie
        _append_ellipsoid(bm, (0.0, -0.038, 0.0), (0.044, 0.054, 0.032), u_seg=18, v_seg=14)
        _append_ellipsoid(bm, (inw * 0.012, -0.076, -0.004), (0.038, 0.034, 0.026), u_seg=14, v_seg=10)

    elif pose_name == "fist":
        _append_ellipsoid(bm, (0.0, -0.042, 0.0), (0.048, 0.044, 0.038), u_seg=18, v_seg=14)
        for fx in (-0.027, -0.009, 0.009, 0.027):
            _append_finger_capsule(
                bm,
                [(fx, -0.066, 0.014), (fx, -0.082, -0.004), (fx, -0.062, -0.022)],
                [0.015, 0.0145, 0.014],
            )
        _append_finger_capsule(
            bm,
            [(inw * 0.036, -0.038, 0.014), (inw * 0.020, -0.068, 0.020), (outw * 0.008, -0.072, 0.012)],
            [0.017, 0.016, 0.015],
        )

    elif pose_name == "point":
        _append_ellipsoid(bm, (0.0, -0.040, 0.0), (0.046, 0.042, 0.036), u_seg=18, v_seg=14)
        # Bold index finger pointing straight forward along -Y
        _append_finger_capsule(
            bm,
            [(inw * 0.018, -0.062, 0.014), (inw * 0.015, -0.106, 0.016), (inw * 0.012, -0.146, 0.016)],
            [0.0185, 0.0175, 0.0165],
        )
        # 3 curled lower fingers
        for fx in (0.0, outw * 0.018, outw * 0.034):
            _append_finger_capsule(
                bm,
                [(fx, -0.064, 0.004), (fx, -0.078, -0.012), (fx, -0.058, -0.024)],
                [0.0145, 0.014, 0.0135],
            )
        _append_finger_capsule(
            bm,
            [(inw * 0.036, -0.038, 0.010), (inw * 0.028, -0.066, -0.004)],
            [0.0165, 0.015],
        )

    elif pose_name == "thumbs_up_ok":
        _append_ellipsoid(bm, (0.0, -0.042, 0.0), (0.046, 0.044, 0.038), u_seg=18, v_seg=14)
        # Big cheerful cartoon thumb pointing straight UP (+Z)
        _append_finger_capsule(
            bm,
            [(inw * 0.020, -0.042, 0.024), (inw * 0.018, -0.044, 0.068), (inw * 0.014, -0.042, 0.106)],
            [0.020, 0.019, 0.018],
        )
        for z_off in (0.014, -0.004, -0.022):
            _append_finger_capsule(
                bm,
                [(outw * 0.012, -0.068, z_off), (inw * 0.012, -0.080, z_off), (inw * 0.026, -0.062, z_off)],
                [0.015, 0.0145, 0.014],
            )

    else:  # "relaxed_curl" (cute default 4-finger puffy cartoon mitt)
        _append_ellipsoid(bm, (0.0, -0.040, 0.0), (0.046, 0.046, 0.033), u_seg=18, v_seg=14)
        for fx in (inw * 0.026, inw * 0.008, outw * 0.010, outw * 0.028):
            _append_finger_capsule(
                bm,
                [(fx, -0.068, 0.006), (fx * 0.95, -0.096, -0.006), (fx * 0.90, -0.108, -0.026)],
                [0.0155, 0.0148, 0.014],
            )
        _append_finger_capsule(
            bm,
            [(inw * 0.034, -0.036, 0.008), (inw * 0.046, -0.068, -0.004), (inw * 0.042, -0.088, -0.016)],
            [0.017, 0.016, 0.015],
        )

    mesh = bpy.data.meshes.new(f"{prefix} | hand_{s_lbl}_{pose_name}")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    for p in mesh.polygons:
        p.use_smooth = True

    obj = _link_only(
        bpy.data.objects.new(f"{prefix} | hand_{s_lbl}_{pose_name}", mesh),
        col,
        parent=wrist_pivot,
        mat=hand_mat,
    )
    obj["mascot_tag"] = f"hand_{s_lbl}:{pose_name}"
    ink_obj, disp = _add_mesh_ink_hull(
        obj, col, ink_mat, light_empty, world_empty, base_thickness=0.0040, ink_scale=0.68
    )
    ink_obj["mascot_tag"] = f"hand_ink_{s_lbl}:{pose_name}"

    is_default = pose_name == "relaxed_curl"
    extra_items = []
    if pose_name == "open_stop":
        # Curved `#141016` thumb-pad palm crease on `-Y` palm face (Reference Image 5!)
        crease = _make_simple_tube(
            f"{prefix} | hand_{s_lbl}_open_stop_crease",
            col,
            [
                (inw * 0.034, -0.063, 0.034),
                (inw * 0.014, -0.069, 0.022),
                (outw * 0.004, -0.068, 0.004),
            ],
            0.0036,
            ink_mat,
            parent=wrist_pivot,
            res_u=3,
            bevel_res=1,
            shadow=False,
        )
        crease["mascot_tag"] = f"hand_{s_lbl}:{pose_name}"
        extra_items.append(crease)
    elif pose_name == "power_claw":
        # Subtle cupped-palm comic crease inside upturned palm (Reference Image 6!)
        p_crease = _make_simple_tube(
            f"{prefix} | hand_{s_lbl}_power_claw_crease",
            col,
            [
                (outw * 0.028, -0.056, 0.030),
                (0.0, -0.062, 0.028),
                (inw * 0.026, -0.054, 0.028),
            ],
            0.0032,
            ink_mat,
            parent=wrist_pivot,
            res_u=3,
            bevel_res=1,
            shadow=False,
        )
        p_crease["mascot_tag"] = f"hand_{s_lbl}:{pose_name}"
        extra_items.append(p_crease)

    for item in (obj, ink_obj, *extra_items):
        item.hide_render = not is_default
        item.hide_viewport = not is_default
    return obj, ink_obj, disp


# --------------------------------------------------------------------------- Chunky Cartoon Sneaker (`Z = 0.000 m`)
def _build_chunky_sneaker(prefix: str, col, foot_pivot, side: int, white_mat, sole_mat, panel_black_mat, ink_mat, light_empty, world_empty):
    """Build chunky white-and-black cartoon skate sneaker with exact `Z = 0.000 m` flat rubber sole."""
    s_lbl = "L" if side < 0 else "R"
    ink_records = []

    def _footprint_xy(a: float) -> tuple[float, float]:
        # Plump rounded skate shoe footprint: y in [-0.145, +0.075], x in [-0.068, +0.068]
        ca, sa = math.cos(a), math.sin(a)
        front_w = 1.0 + 0.08 * max(0.0, -sa)  # Wide cute rounded toe box
        x = 0.067 * ca * front_w
        y = -0.035 + 0.110 * sa
        return x, y

    # 1. Multi-material Sneaker Body (Flat dark outsole z=0.000..0.008 + white foxing wall + white toe/upper)
    ring_n = 28
    # (z, scale_xy, y_shift, mat_idx): 0=sole_dark, 1=white, 2=panel_black
    layers = [
        (0.0000, 0.96, 0.000, 0),  # Exact Z = 0.0000 m flat rubber ground contact!
        (0.0075, 1.00, 0.000, 0),  # Dark tread bevel
        (0.0085, 1.01, 0.000, 1),  # White rubber midsole foxing wall bottom
        (0.0260, 1.01, 0.000, 1),  # White rubber midsole foxing wall top
        (0.0480, 0.94, 0.006, 1),  # Plump white toe cap & upper mid
        (0.0720, 0.74, 0.024, 2),  # Ankle collar rim
        (0.0860, 0.56, 0.036, 2),  # Inner cuff top tucked into pajama pant
    ]
    verts, faces, face_mats = [], [], []
    for j, (zz, sc, y_sh, m_idx) in enumerate(layers):
        for i in range(ring_n):
            a = math.tau * i / ring_n
            bx, by = _footprint_xy(a)
            # Lower the front toe dome gently while keeping tongue/ankle high
            toe_factor = max(0.0, -math.sin(a))
            z_adj = zz
            if j >= 4:
                z_adj = zz * (1.0 - 0.24 * toe_factor * ((j - 3) / 3.0))
            verts.append((bx * sc, by * sc + y_sh, max(0.0, z_adj)))
            if j > 0:
                k = j * ring_n + i
                nxt = j * ring_n + ((i + 1) % ring_n)
                faces.append((k - ring_n, nxt - ring_n, nxt, k))
                # Side/back quarter panels in sleek black (`#181B24`), front toe cap in snow-white!
                if j in (4, 5) and math.sin(a) > -0.18:
                    face_mats.append(2)
                else:
                    face_mats.append(m_idx)

    # Exact flat Z = 0.0000 m bottom sole cap
    bot_idx = len(verts)
    verts.append((0.0, -0.035, 0.0000))
    for i in range(ring_n):
        nxt = (i + 1) % ring_n
        faces.append((nxt, i, bot_idx))
        face_mats.append(0)

    top_idx = len(verts)
    verts.append((0.0, 0.008, 0.0860))
    top_base = (len(layers) - 1) * ring_n
    for i in range(ring_n):
        nxt = (i + 1) % ring_n
        faces.append((top_base + i, top_base + nxt, top_idx))
        face_mats.append(2)

    shoe_obj = _make_mesh(
        f"{prefix} | sneaker_{s_lbl}",
        col,
        verts,
        faces,
        sole_mat,
        parent=foot_pivot,
        smooth=True,
        tag=f"sneaker_{s_lbl}",
    )
    shoe_obj.data.materials.append(white_mat)
    shoe_obj.data.materials.append(panel_black_mat)
    for poly, m_i in zip(shoe_obj.data.polygons, face_mats):
        poly.material_index = m_i
        if m_i == 0 and poly.normal.z < -0.8:
            poly.use_smooth = False
    shoe_obj.visible_shadow = True

    # Floor-clamped ink hull so `min_z == 0.0000 m` strictly!
    ink_obj, disp = _add_mesh_ink_hull(
        shoe_obj,
        col,
        ink_mat,
        light_empty,
        world_empty,
        base_thickness=0.0046,
        ink_scale=0.82,
        clamp_floor_z=0.0,
    )
    ink_records.append((ink_obj, disp))

    # Crisp black midsole foxing stripe + 2 puffy white cartoon shoelace bars
    foxing_pts = []
    for i in range(17):
        a = math.tau * (i % 16) / 16
        bx, by = _footprint_xy(a)
        foxing_pts.append((bx * 1.02, by * 1.02, 0.0255))
    _make_simple_tube(f"{prefix} | sneaker_foxing_{s_lbl}", col, foxing_pts, 0.0026, ink_mat, parent=foot_pivot, res_u=2, bevel_res=1)

    for l_idx, (ly, lz) in enumerate([(-0.068, 0.060), (-0.044, 0.070)]):
        lace = _make_simple_tube(
            f"{prefix} | sneaker_lace_{s_lbl}_{l_idx}",
            col,
            [(-0.028, ly, lz - 0.004), (0.0, ly - 0.005, lz + 0.005), (0.028, ly, lz - 0.004)],
            0.0058,
            white_mat,
            parent=foot_pivot,
        )
        lace.visible_shadow = False

    return shoe_obj, ink_records


# --------------------------------------------------------------------------- Expression Image Loader / Fallback
def _load_or_generate_expression_images(prefix: str) -> dict:
    """Load all 18 PNGs from `assets/mascot/expressions/` (calling `expression_gen` if present)."""
    expr_dir = ROOT / "assets" / "mascot" / "expressions"
    expected_paths = {name: expr_dir / f"{name}.png" for name in EXPRESSIONS}
    for v_name in VISEMES:
        expected_paths[v_name] = expr_dir / "visemes" / f"{v_name}.png"

    if not all(p.is_file() for p in expected_paths.values()):
        gen_file = ROOT / "assets" / "mascot" / "expression_gen.py"
        if gen_file.is_file():
            from assets.mascot import expression_gen

            generated = expression_gen.generate_all(expr_dir)
            if isinstance(generated, dict):
                for k, v in generated.items():
                    expected_paths[k] = Path(v)

    loaded = {}
    import numpy as np

    for name in ALL_EXPRESSIONS:
        p = expected_paths[name]
        if p.is_file():
            img = bpy.data.images.load(str(p.resolve()), check_existing=True)
            if not img.packed_file:
                img.pack()
            loaded[name] = img
        else:
            # Clean in-memory fallback ONLY if `expression_gen.py` hasn't run yet during isolated dev
            w, h = 512, 512
            yy, xx = np.ogrid[0:1:512j, 0:1:512j]
            arr = np.zeros((h, w, 4), dtype=np.float32)
            arr[:, :, :3] = (0.007, 0.005, 0.008)
            for cx in (0.31, 0.69):
                mask = ((xx - cx) / 0.12) ** 2 + ((yy - 0.58) / 0.16) ** 2 <= 1.0
                arr[mask, 3] = 1.0
            mouth = ((xx - 0.50) / 0.08) ** 2 + ((yy - 0.28) / 0.06) ** 2 <= 1.0
            arr[mouth, 3] = 1.0
            img = bpy.data.images.new(f"{prefix}_{name}_fallback", width=w, height=h, alpha=True)
            img.pixels.foreach_set(arr.ravel())
            img.pack()
            loaded[name] = img
    return loaded


# --------------------------------------------------------------------------- Master Collection Builder
def build_mascot_in_collection(collection, name: str = "MascotHero") -> dict:
    """Build a complete, self-contained Mascot rig inside `collection`."""
    if bpy is None:
        raise RuntimeError("build_mascot_in_collection requires Blender 4.2 Python (`bpy`).")

    root = _make_empty(name, collection, loc=(0.0, 0.0, 0.0), tag="root", display_size=0.12)
    body = _make_empty(f"{name} | body", collection, loc=(0.0, 0.0, BODY_REST_Z), parent=root, tag="body", display_size=0.08)
    head = _make_empty(f"{name} | head", collection, loc=(0.0, 0.0, HEAD_REL_Z), parent=body, tag="head", display_size=0.08)

    world_axes = _make_empty(f"{name} | world_axes", collection, loc=(0.0, 0.0, 0.0), tag="world_axes", display_size=0.04)
    light_empty = _make_empty(f"{name} | light_empty", collection, loc=(0.0, 0.0, 0.0), tag="light_empty", display_size=0.08)
    light_empty.empty_display_type = "SINGLE_ARROW"
    c_loc = light_empty.constraints.new("COPY_LOCATION")
    c_loc.target = head
    light_empty.rotation_euler = Vector(DEFAULT_LIGHT_DIR).normalized().to_track_quat("Z", "Y").to_euler()

    # Materials (AgX-calibrated comic cel palette: pure bright snow-white & rich golden-yellow)
    ink_mat = _make_ink_material(name)
    face_mat = _make_comic_cel_material(
        f"{name} | snow_white_face",
        SNOW_WHITE_HEX,
        SNOW_SHADE_HEX,
        strength=2.35,
        cutoff_start=-0.12,
        cutoff_end=-0.46,
        under_bias=0.10,
        max_shade=0.36,
    )
    hand_mat = _make_comic_cel_material(
        f"{name} | snow_white_hand",
        SNOW_WHITE_HEX,
        SNOW_SHADE_HEX,
        strength=2.35,
        cutoff_start=-0.06,
        cutoff_end=-0.40,
        under_bias=0.14,
        max_shade=0.36,
    )
    beanie_mat = _make_comic_cel_material(
        f"{name} | crimson_beanie",
        BEANIE_LIT_HEX,
        BEANIE_SHADE_HEX,
        strength=1.45,
        cutoff_start=0.05,
        cutoff_end=-0.14,
        under_bias=0.16,
    )
    hoodie_mat = _make_comic_cel_material(
        f"{name} | yellow_hoodie",
        HOODIE_LIT_HEX,
        HOODIE_SHADE_HEX,
        strength=1.48,
        cutoff_start=0.06,
        cutoff_end=-0.12,
        under_bias=0.22,
    )
    pants_mat = _make_comic_cel_material(
        f"{name} | charcoal_pants",
        PANTS_LIT_HEX,
        PANTS_SHADE_HEX,
        strength=1.18,
        cutoff_start=0.05,
        cutoff_end=-0.15,
        under_bias=0.18,
    )
    sole_mat = _make_comic_cel_material(
        f"{name} | sneaker_sole",
        SOLE_DARK_HEX,
        "#181A22",
        strength=1.14,
        cutoff_start=0.04,
        cutoff_end=-0.16,
        under_bias=0.12,
    )
    panel_black_mat = _make_comic_cel_material(
        f"{name} | sneaker_black",
        SNEAKER_BLACK_HEX,
        "#0E1016",
        strength=1.10,
        cutoff_start=0.04,
        cutoff_end=-0.16,
        under_bias=0.12,
    )
    highlight_beanie = _make_unlit_material(f"{name} | beanie_gloss", "#FFFDFB", strength=2.65)
    highlight_hoodie = _make_unlit_material(f"{name} | hoodie_gloss", "#FFFDF2", strength=2.55)
    stripe_mat = _make_unlit_material(f"{name} | side_stripe", STRIPE_WHITE_HEX, strength=2.25)
    stick_limb_mat = _make_unlit_material(f"{name} | stick_limb", INK_HEX, strength=1.0)

    # 1. Head + 18 Conformed Face Decals + Crimson Beanie
    head_mesh = _build_marshmallow_head(name, collection, head, face_mat)
    _add_mesh_ink_hull(head_mesh, collection, ink_mat, light_empty, world_axes, ink_scale=1.02)

    expr_imgs = _load_or_generate_expression_images(name)
    _build_conformed_face_decals(name, collection, head, head_mesh, expr_imgs)
    _build_crimson_beanie(name, collection, head, beanie_mat, ink_mat, highlight_beanie, light_empty, world_axes)

    # 2. Oversized Cozy Yellow Hoodie + Collar + Back Hood + Drawstrings + Kangaroo Pocket
    _build_yellow_hoodie(name, collection, body, hoodie_mat, hand_mat, ink_mat, highlight_hoodie, light_empty, world_axes)

    # 3. Sleeved IK Arms ("hoodie" default + "stick" toggle) + 7 Swappable Hands + Sockets
    for side, s_lbl in ((-1, "L"), (1, "R")):
        sh = Vector((side * 0.155, 0.0, 0.180))
        el = Vector((side * 0.215, 0.015, 0.055))
        hd = Vector((side * 0.220, -0.060, -0.060))
        arm_pts = [
            tuple(sh),
            tuple(sh.lerp(el, 0.52)),
            tuple(el),
            tuple(el.lerp(hd, 0.68)),
            tuple(hd),
        ]
        # Cozy tapered yellow hoodie sleeve swelling into a puffy wrist cuff
        sleeve_obj, _ = _make_inked_curve(
            f"{name} | sleeve_{s_lbl}",
            collection,
            arm_pts,
            (0.055, 0.059, 0.062, 0.066, 0.055),
            hoodie_mat,
            ink_mat,
            parent=body,
            profile_res=14,
            resolution_u=7,
            ink_scale=0.92,
            tag=f"sleeve_{s_lbl}",
        )
        sleeve_obj["mascot_arm_style"] = "hoodie"

        # Optional stick arm ("stick" toggle)
        stick_obj = _make_simple_tube(
            f"{name} | stick_arm_{s_lbl}",
            collection,
            arm_pts,
            0.020,
            stick_limb_mat,
            parent=body,
            res_u=10,
            bevel_res=4,
            shadow=True,
        )
        stick_obj["mascot_tag"] = f"stick_arm_{s_lbl}"
        stick_obj["mascot_arm_style"] = "stick"
        stick_obj.hide_render = True
        stick_obj.hide_viewport = True

        # Wrist pivot & dark inner cuff ring
        wrist = _make_empty(f"{name} | wrist_{s_lbl}", collection, loc=tuple(hd), parent=body, tag=f"wrist_{s_lbl}", display_size=0.04)
        cuff_bm = bmesh.new()
        bmesh.ops.create_uvsphere(cuff_bm, u_segments=18, v_segments=10, radius=1.0)
        for v in cuff_bm.verts:
            v.co = Vector((v.co.x * 0.046, v.co.y * 0.012 + 0.006, v.co.z * 0.046))
        cuff_mesh = bpy.data.meshes.new(f"{name} | cuff_opening_{s_lbl}")
        cuff_bm.to_mesh(cuff_mesh)
        cuff_bm.free()
        cuff_ring = _link_only(
            bpy.data.objects.new(f"{name} | cuff_opening_{s_lbl}", cuff_mesh),
            collection,
            parent=wrist,
            mat=ink_mat,
        )
        cuff_ring.visible_shadow = False
        cuff_ring["mascot_tag"] = f"cuff_ring_{s_lbl}"
        cuff_ring["mascot_arm_style"] = "hoodie"

        # World-accurate palm grip socket (`0.000 m` prop attachment)
        _make_empty(
            f"{name} | hand_socket_{s_lbl}",
            collection,
            loc=(0.0, -0.052, 0.0),
            parent=wrist,
            tag=f"hand_socket_{s_lbl}",
            display_size=0.04,
        )

        for pose_name in HAND_POSES:
            _build_hand_pose_mesh(name, collection, wrist, side, pose_name, hand_mat, ink_mat, light_empty, world_axes)

    # 4. Pelvis + Pajama Lounge Pants ("pajamas" default) + Shorts ("shorts" toggle) + Sneakers
    pelvis_bm = bmesh.new()
    bmesh.ops.create_uvsphere(pelvis_bm, u_segments=24, v_segments=14, radius=1.0)
    for v in pelvis_bm.verts:
        v.co = Vector((v.co.x * 0.162, v.co.y * 0.125, v.co.z * 0.072))
    pelvis_mesh = bpy.data.meshes.new(f"{name} | pelvis")
    pelvis_bm.to_mesh(pelvis_mesh)
    pelvis_bm.free()
    for p in pelvis_mesh.polygons:
        p.use_smooth = True
    pelvis_obj = _link_only(bpy.data.objects.new(f"{name} | pelvis", pelvis_mesh), collection, parent=body, mat=pants_mat)
    pelvis_obj.location = (0.0, 0.0, -0.185)

    for side, s_lbl in ((-1, "L"), (1, "R")):
        hip = Vector((side * HIP_X, 0.0, BODY_REST_Z + HIP_REL_Z))
        knee = Vector((side * 0.104, -0.025, 0.220))
        ankle = Vector((side * 0.105, 0.012, 0.068))
        leg_pts = [
            tuple(hip),
            tuple(hip.lerp(knee, 0.55)),
            tuple(knee),
            tuple(ankle),
        ]

        # Default `bottom_style="pajamas"`: baggy charcoal-navy lounge pants + white side stripe
        paj_obj, _ = _make_inked_curve(
            f"{name} | pajama_{s_lbl}",
            collection,
            leg_pts,
            (0.070, 0.075, 0.080, 0.072),
            pants_mat,
            ink_mat,
            parent=root,
            profile_res=14,
            resolution_u=7,
            ink_scale=0.90,
            tag=f"pajama_{s_lbl}",
        )
        paj_obj["mascot_bottom_style"] = "pajamas"

        stripe_pts = [
            (p[0] + side * r * 0.96, p[1] - 0.004, p[2])
            for p, r in zip(leg_pts, (0.070, 0.075, 0.080, 0.072))
        ]
        stripe_obj = _make_simple_tube(
            f"{name} | pajama_stripe_{s_lbl}",
            collection,
            stripe_pts,
            0.0052,
            stripe_mat,
            parent=root,
            res_u=6,
            bevel_res=1,
            shadow=False,
        )
        stripe_obj["mascot_tag"] = f"stripe_{s_lbl}"
        stripe_obj["mascot_bottom_style"] = "pajamas"

        # Toggle `bottom_style="shorts"`: charcoal lounge shorts + dark leg calves
        short_pts = [tuple(hip), tuple(hip.lerp(knee, 0.50)), tuple(knee)]
        short_obj, _ = _make_inked_curve(
            f"{name} | short_{s_lbl}",
            collection,
            short_pts,
            (0.074, 0.080, 0.076),
            pants_mat,
            ink_mat,
            parent=root,
            profile_res=14,
            resolution_u=6,
            ink_scale=0.90,
            tag=f"short_{s_lbl}",
        )
        short_obj["mascot_bottom_style"] = "shorts"
        short_obj.hide_render = True
        short_obj.hide_viewport = True

        calf_pts = [tuple(knee), tuple(knee.lerp(ankle, 0.5)), tuple(ankle)]
        calf_obj = _make_simple_tube(
            f"{name} | calf_{s_lbl}",
            collection,
            calf_pts,
            0.024,
            stick_limb_mat,
            parent=root,
            res_u=8,
            bevel_res=3,
            shadow=True,
        )
        calf_obj["mascot_tag"] = f"calf_{s_lbl}"
        calf_obj["mascot_bottom_style"] = "shorts"
        calf_obj.hide_render = True
        calf_obj.hide_viewport = True

        # Foot pivot at exact `Z = 0.000 m` floor plane + chunky cartoon sneaker
        foot_piv = _make_empty(
            f"{name} | foot_{s_lbl}",
            collection,
            loc=(side * 0.105, 0.0, 0.0),
            parent=root,
            tag=f"foot_{s_lbl}",
            display_size=0.05,
        )
        _build_chunky_sneaker(
            name, collection, foot_piv, side, hand_mat, sole_mat, panel_black_mat, ink_mat, light_empty, world_axes
        )

    bpy.context.view_layer.update()
    return {"root": root, "body": body, "head": head, "head_mesh": head_mesh, "light_empty": light_empty}


# --------------------------------------------------------------------------- Standalone Master `.blend` Builder
def build_master_blend(out_dir: Path | None = None) -> Path:
    """Build, pack, purge, save, and verify `assets/mascot/mascot_master.blend`."""
    if bpy is None:
        raise RuntimeError("Run inside Blender 4.2 (`blender -b --factory-startup --python ...`).")

    import ricks_v2_kit as kit
    import shorts_preflight as gate
    from assets.mascot import mascot_api

    target_dir = Path(out_dir or os.environ.get("MODAL_OUT_DIR") or (ROOT / "assets/mascot")).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    blend_path = target_dir / "mascot_master.blend"

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = kit.configure_ricks_scene(bpy.context.scene, width=1080, height=1920, fps=30, frame_end=60, samples=32)

    hero_col = bpy.data.collections.new(COLLECTION_NAME)
    scene.collection.children.link(hero_col)
    build_mascot_in_collection(hero_col, name=COLLECTION_NAME)

    # Pose cleanly in canonical standing rest pose via MascotRig
    rig = mascot_api.MascotRig.from_collection(hero_col, prefix=COLLECTION_NAME)
    rig.pose(None, loc=(0.0, 0.0, 0.0), expr="idle_cute")
    bpy.context.view_layer.update()

    # Strict geometric & resource assertions BEFORE saving
    bbox = rig.head_bbox_ratio()
    if not (1.00 <= bbox["ratio"] <= 1.05):
        raise RuntimeError(f"Head bbox ratio out of [1.00, 1.05]: {bbox}")

    res = gate.validate_resources(scene)
    if not res["pass"] or res["visible_triangles"] >= 35000:
        raise RuntimeError(f"Mascot triangle/resource budget failed (<35k required): {res}")

    # Verify exact Z = 0.000 m sneaker sole contact
    deps = bpy.context.evaluated_depsgraph_get()
    sole_mins = []
    for s_lbl in ("L", "R"):
        shoe = next(o for o in hero_col.objects if o.get("mascot_tag") == f"sneaker_{s_lbl}")
        ev = shoe.evaluated_get(deps)
        m = ev.to_mesh()
        try:
            zs = [(ev.matrix_world @ v.co).z for v in m.vertices]
            sole_mins.append(min(zs))
        finally:
            ev.to_mesh_clear()
    if any(abs(z) > 1e-4 for z in sole_mins):
        raise RuntimeError(f"Sneaker soles not flat at Z=0.000m: {sole_mins}")

    # Pack all textures & purge all orphan datablocks recursively
    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)
        elif not img.packed_file:
            img.pack()
    for _ in range(4):
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), compress=True)

    # Reopen & verify clean round-trip, packed images, and zero orphans
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
    reopened_col = bpy.data.collections.get(COLLECTION_NAME)
    if reopened_col is None:
        raise RuntimeError(f"Collection {COLLECTION_NAME!r} missing on reopen!")
    unpacked = [img.name for img in bpy.data.images if img.users > 0 and not img.packed_file]
    if unpacked:
        raise RuntimeError(f"Unpacked images in {blend_path}: {unpacked}")
    orphans = [
        f"{kind}:{blk.name}"
        for kind, pool in (
            ("mesh", bpy.data.meshes),
            ("mat", bpy.data.materials),
            ("img", bpy.data.images),
            ("curve", bpy.data.curves),
        )
        for blk in pool
        if blk.users == 0
    ]
    if orphans:
        raise RuntimeError(f"Orphan datablocks remained in {blend_path}: {orphans}")

    re_rig = mascot_api.MascotRig.from_collection(reopened_col, prefix=COLLECTION_NAME)
    re_bbox = re_rig.head_bbox_ratio()
    re_tris = gate.visible_triangles(bpy.context.scene)
    print(
        f"MASCOT_MASTER_OK path={blend_path} tris={re_tris} head_bbox={re_bbox} "
        f"sole_min_z={[round(z, 6) for z in sole_mins]} packed_images={len(bpy.data.images)}",
        flush=True,
    )
    return blend_path


def _main(argv: list[str]):
    p = ArgumentParser(description=__doc__)
    p.add_argument("pos_out", nargs="?", default=None)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args(argv)
    out = args.out or (Path(args.pos_out) if args.pos_out else None)
    build_master_blend(out)


if __name__ == "__main__":
    tail = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    _main(tail)
