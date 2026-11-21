"""Use the approved Part 1 kits for the two new story modules."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "v03"))
from build import activate, act, cam_view, ease, k, key, prop_pose, route, stage, walk
from cast import LEGS, REST, figure
from scenery import block, daylights, lettering, line, outdoor_sky, palette, street
from native_pipeline import BOUNDARIES, FPS, RENDERS


def clock(part):
    return lambda t: round(FPS*t)-BOUNDARIES[part-1]+1


def make_scene(part, label):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    length = BOUNDARIES[part]-BOUNDARIES[part-1]
    k.configure_ricks_scene(scene, frame_end=length, samples=5)
    scene.world = bpy.data.worlds.new(label+" bounce")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs[0].default_value = k.look.rgba("#587299")
    background.inputs[1].default_value = .40
    camera = bpy.data.objects.new(label, bpy.data.cameras.new(label))
    scene.collection.objects.link(camera)
    scene.camera = camera
    k.setup_ricks_compositor(scene, camera=camera)
    return scene, camera, palette(), length


def view(cam, frame, group, position, aim, lens=26, *, focus=None, stop=2.8):
    cam_view(cam, frame, group, position, aim, lens, focus)
    cam.data.dof.aperture_fstop = stop
    key(cam.data, frame, "dof.aperture_fstop")


def glide(cam, f, group, first, last, p, q, a, b, lens=26, *, stop=2.8):
    t = ease(f, first, last)
    view(cam, f, group, Vector(p).lerp(Vector(q), t), Vector(a).lerp(Vector(b), t), lens, stop=stop)


def title(collection, mats, camera, label):
    root = k.empty(label+" day marker", collection, parent=camera)
    outline = lettering(collection, label, (0,.016,0), .136, mats["ink"], root)
    outline.data.offset = .009
    lettering(collection, label, (0,-.006,0), .136, mats["gold"], root)
    return root


def show_title(root, f, first, last):
    reveal = ease(f, first, first+8)*(1-ease(f, last-7, last))
    prop_pose(root, f, (0,.72,-1.60), reveal, (-math.pi/2,0,0))


def fade_to_black(scene, keys, *, hard=False):
    tree = scene.node_tree
    output = next(node for node in tree.nodes if node.type=="COMPOSITE")
    image = output.inputs[0].links[0].from_socket
    fade = tree.nodes.new("CompositorNodeMixRGB")
    fade.name = "Story cut to black" if hard else "Narration tail fade"
    tree.links.new(image, fade.inputs[1])
    fade.inputs[2].default_value = (0,0,0,1)
    tree.links.new(fade.outputs[0], output.inputs[0])
    for f, value in keys:
        fade.inputs[0].default_value = value
        fade.inputs[0].keyframe_insert("default_value", frame=f)


def finish(scene, part, actors, groups, cuts, proofs, planned=()):
    for rig in actors:
        rig.finish_bake()
    for group, ranges in groups:
        activate(group, ranges)
    for action in bpy.data.actions:
        for curve in action.fcurves:
            stepped = "hide_" in curve.data_path or curve.data_path in ("lens", "dof.aperture_fstop")
            for point in curve.keyframe_points:
                point.interpolation = "CONSTANT" if stepped else "LINEAR"
    for at,label in cuts:
        scene.timeline_markers.new(label, frame=at)
    output = RENDERS/f"part{part}_v01"
    output.mkdir(exist_ok=True, parents=True)
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output/f"part{part}_v01.blend"))
    (output/"shot_map.json").write_text(json.dumps({
        "cuts":[at-1 for at,_ in cuts if at>1], "proof_frames":sorted(proofs), "planned":planned,
    }, indent=2))


def from_world(rig, target, elbow):
    body = rig.root.matrix_basis @ rig.body.matrix_basis
    point = body.inverted() @ Vector(target)
    return point - .013*(point-Vector(elbow)).normalized()


def move_hands(rig, f, targets, elbows):
    for arm, side, target, elbow in zip(rig.arms, (-1, 1), targets, elbows):
        if target is not None:
            k.pose_arm(arm, (side*.106,-.003,.342), elbow, from_world(rig,target,elbow), f)
    k.studio_pose_hands(rig,f)


def sunrise(collection):
    for obj in collection.objects:
        if obj.type=="LIGHT":
            if obj.data.type=="SUN":
                obj.location = (-8,5.2,2.7)
                k.aim(obj, (0,.4,0))
                obj.data.color = k.look.rgba("#ffc278")[:3]
                obj.data.energy = 3.8
            elif "rim" in obj.name:
                obj.data.color = k.look.rgba("#ffd093")[:3]
                obj.data.energy *= 1.45
    sky = next(obj for obj in collection.objects if obj.name.startswith("Continuous surrounding"))
    ramp = next(n.color_ramp for n in sky.data.materials[0].node_tree.nodes if n.type=="VALTORGB")
    for swatch,color in zip(ramp.elements, ("#f89360","#ffc28c","#a9bdda","#657aab")):
        swatch.color = k.look.rgba(color)
    glow = k.emission("Sunrise disc", "#ffd99c", 3.5)
    sun = k.ball("Golden sun on the street horizon", collection,(-15,3.9,3.4),(.89,.89,.89),
                 glow,segments=26,rings=14)
    sun.visible_shadow=False
