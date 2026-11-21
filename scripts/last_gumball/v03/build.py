"""The Last Gumball v03: v02 with an rc camera program on the interior chute only.

  python scripts/last_gumball/v03/build.py scratch NAME   # v02 copy -> _iter/NAME.blend, render shot 3 frames
  python scripts/last_gumball/v03/build.py proof          # v02 copy -> last_gumball_v03.blend, reopen, benchmark
  python scripts/last_gumball/v03/build.py stills DIR f.. # frames from the v03 blend
  python scripts/last_gumball/v03/build.py render         # all 300 frames

Only shot 3 (Blender frames 109-186) changes: camera location, rotation,
lens, f-stop and focus distance, plus the screen-compensated prop and
character ink strengths that v01 keyed from that camera. Frame 109 keeps the
v02 camera for the brass-ring match; frame 187 onward is untouched.
"""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "scripts/ricks_v2_kit.py").is_file())
SRC = ROOT / "renders/last_gumball/v02/last_gumball_v02.blend"
OUT = ROOT / "renders/last_gumball/v03"
BLEND = OUT / "last_gumball_v03.blend"
BLENDER = r"D:\tools\Blender\4.2.23\blender.exe"
BENCH = (1, 66, 108, 109, 113, 117, 125, 140, 160, 176, 186, 187)


class Rig:
    def __init__(self, bpy, name="Commuter"):
        o = bpy.data.objects
        self.name, self.head = name, o[name + " | head control"]
        self.root = o[name]
        self.ink_modifiers = [m for x in bpy.data.objects if x.get("ricks_role") == "ink"
                              and (x in self.root.children_recursive or (x.parent and x.parent.get("ricks_role") == "drawn_fist"))
                              for m in x.modifiers if m.type == "DISPLACE"]


def rekey(bpy):
    sys.path[:0] = [str(HERE), str(ROOT / "scripts")]
    from mathutils import Vector
    import plan
    import ricks_camera as rc
    import ricks_drawn_look as drawn

    scene = bpy.context.scene
    cam = scene.camera
    prog = plan.program()
    f0, f1 = plan.F0, plan.F1

    # Infer each prop hull's authored pixel width from its v02 keys (shot 3).
    rig = Rig(bpy)
    char_hulls = {id(m) for m in rig.ink_modifiers}
    props = []
    for obj in bpy.data.objects:
        if obj.get("ricks_role") != "ink":
            continue
        for mod in obj.modifiers:
            if mod.type != "DISPLACE" or id(mod) in char_hulls or obj.parent is None:
                continue
            src = obj.parent
            samples = []
            for f in range(f0, f1 + 1):
                scene.frame_set(f)
                center = src.matrix_world @ (sum((Vector(c) for c in src.bound_box), Vector()) / 8)
                depth = -(cam.matrix_world.inverted() @ center).z
                s = -mod.strength
                if depth > .02 and .0003 < s < .008:
                    samples.append(s * cam.data.lens * 640 / (depth * 36))
            if samples:
                samples.sort()
                props.append((src, mod, samples[len(samples) // 2]))

    q = None
    scene.frame_set(f0 - 1)
    q = cam.matrix_world.to_quaternion()
    first = prog.evaluate(f0)
    for f in range(f0, f1 + 1):
        state = prog.evaluate(f)
        q = rc.key_camera(cam, state, f, None, q)
    if (Vector(first.pos) - Vector(plan.START)).length > 1e-9:
        raise RuntimeError("Frame 109 must keep the ring-match position.")
    for block in (cam, cam.data):
        for curve in block.animation_data.action.fcurves:
            for key in curve.keyframe_points:
                if f0 <= key.co.x <= f1:
                    key.interpolation = "LINEAR"

    pixels = 3.6
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        inv = cam.matrix_world.inverted()
        for src, mod, px in props:
            center = src.matrix_world @ (sum((Vector(c) for c in src.bound_box), Vector()) / 8)
            depth = -(inv @ center).z
            if depth <= .02:
                depth = 1.0
            mod.strength = -max(.0003, min(.008, depth * 36 * px / (cam.data.lens * 640)))
            mod.keyframe_insert("strength", frame=f)
        drawn.update_ink(rig_for_drawn(bpy, rig), cam, pixels=pixels, frame=f)
    scene["ricks_camera_v03"] = "rc program on frames 109-186"
    scene.frame_set(1)
    return scene, prog, len(props)


def rig_for_drawn(bpy, rig):
    """Rebuild the drawn-look record (ink_scale) from the saved v02 modifiers."""
    if getattr(rig, "drawn_look", None):
        return rig
    import ricks_drawn_look as drawn
    scale = {}
    for hull in rig.ink_modifiers:
        obj = hull.id_data
        geo = next((m for m in obj.modifiers if m.type == "NODES"), None)
        ids = drawn._socket_ids(geo.node_group)
        scale[hull.name + "|" + obj.name] = geo[ids["Thick"]] * (1 + geo[ids["Low edge"]])
    rig.drawn_look = {"ink_scale": scale}
    return rig


def render_range(bpy, folder, a, b):
    scene = bpy.context.scene
    folder.mkdir(parents=True, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.frame_start, scene.frame_end = a, b
    scene.render.filepath = str(folder / "frame_")
    bpy.ops.render.render(animation=True)


def worker(mode, args):
    import bpy
    sys.path[:0] = [str(ROOT / "scripts")]
    import shorts_preflight as gate

    if mode == "scratch":
        path = OUT / "_iter" / f"{args[0]}.blend"
        path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(path))
        _, _, n = rekey(bpy)
        bpy.ops.wm.save_mainfile()
        print("PROP_HULLS", n)
        render_range(bpy, OUT / "_iter" / args[0], 106, 190)
    elif mode == "proof":
        OUT.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
        scene, _, n = rekey(bpy)
        print("PROP_HULLS", n)
        scene.render.filepath = "//frames/frame_"
        bpy.ops.wm.save_mainfile()
        bpy.ops.wm.open_mainfile(filepath=str(BLEND))
        scene = bpy.context.scene
        print("ASSETS", json.dumps(gate.validate_resources(scene)))
        result = gate.benchmark(scene, BENCH, OUT / "benchmark", resolution=(540, 960, 100))
        print("BENCH", result["status"], result["p95_seconds"], result["max_seconds"], result["sampled_board_peak_gib"])
    elif mode == "stills":
        scene = bpy.context.scene
        folder = OUT / args[0]
        folder.mkdir(parents=True, exist_ok=True)
        for fr in map(int, args[1:]):
            scene.frame_set(fr)
            scene.render.filepath = str(folder / f"frame_{fr:04d}.png")
            bpy.ops.render.render(write_still=True)
    elif mode == "render":
        render_range(bpy, OUT / "frames", 1, 300)


def main():
    mode, rest = sys.argv[1], sys.argv[2:]
    if mode == "proof" and BLEND.exists():
        raise SystemExit(f"{BLEND} exists; v03 is built once.")
    lock, owner = ROOT / ".blender_gpu.lock", uuid4().hex
    try:
        with lock.open("x", encoding="utf-8") as fh:
            json.dump({"project": "last_gumball/v03", "pid": os.getpid(), "owner": owner}, fh)
    except FileExistsError:
        raise SystemExit(f"GPU busy. Wait for the owner of {lock}.")
    try:
        source = SRC if mode in {"scratch", "proof"} else BLEND
        subprocess.run([os.environ.get("BLENDER_EXE", BLENDER), "-b", "--factory-startup", str(source),
                        "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
                        "--", mode, *rest], check=True, cwd=ROOT)
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("owner") == owner:
            lock.unlink()


if __name__ == "__main__":
    if "--" in sys.argv:
        i = sys.argv.index("--")
        worker(sys.argv[i + 1], sys.argv[i + 2:])
    else:
        main()
