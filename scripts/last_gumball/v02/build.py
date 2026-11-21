"""The Last Gumball v02: A/B test of the opt-in drawn look on the v01 commuter.

Opens the exact v01 scene (renders/last_gumball/v01/last_gumball_v01.blend),
saves a versioned copy, and changes only the character look. Camera, cuts,
set, lighting, poses, expressions and prop timings come from the v01 file.

  python scripts/last_gumball/v02/build.py proof            # copy, restyle, save, reopen, benchmark
  python scripts/last_gumball/v02/build.py stills DIR f ... # render chosen frames from the v02 blend
  python scripts/last_gumball/v02/build.py render           # render all 300 frames

v02-local look adjustments (the shared module is not changed):
  * keep v01's own asymmetric head warp; skip the drawn-look head warp so
    proportions match v01;
  * drawn light along v01's portrait key direction, fixed for the film;
  * drawn round fists on the v01 mitten grips (the arm-tip bulge would sit
    behind the coin), sized so the coin face stays visible past the knuckles,
    painted v01 cream with drawn ink (a black fist merged with the dark machine);
  * a subtler hair gradient (the default crown highlight read as gloss).
"""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "scripts/ricks_v2_kit.py").is_file())
SRC = ROOT / "renders/last_gumball/v01/last_gumball_v01.blend"
OUT = ROOT / "renders/last_gumball/v02"
BLEND = OUT / "last_gumball_v02.blend"
BLENDER = r"D:\tools\Blender\4.2.23\blender.exe"
END = 300
BENCH = (1, 30, 45, 66, 67, 83, 108, 109, 187, 222, 260, 290)
LIGHT_DIR = (.413, -.763, .497)     # v01 portrait key, world, at frame 1
INK_PIXELS = 3.6                     # v01 used 4.2 px x mean hand-drawn weight ~.75
FIST = ((.046, 0, .006), (.031, .009, .026))   # mitten-local centre and radii (m)


class Rig:
    """Shim over the saved v01 commuter for ricks_drawn_look."""

    def __init__(self, bpy, name="Commuter"):
        o = bpy.data.objects
        self.name = name
        self.root, self.body, self.head = o[name], o[name + " | body control"], o[name + " | head control"]
        self.arms = [o[f"{name} | round-tipped arm {s}"] for s in "LR"]
        self.legs = [o[f"{name} | stick leg {s}"] for s in "LR"]
        self.feet = [o[f"{name} | foot tick {s}"] for s in "LR"]
        self.sweat = o.get(name + " | outlined temple drop")
        self.ink_modifiers = [m for x in self.root.children_recursive if x.get("ricks_role") == "ink"
                              for m in x.modifiers if m.type == "DISPLACE"]


def restyle(bpy):
    sys.path[:0] = [str(ROOT / "scripts")]
    import ricks_v2_kit as kit
    import ricks_drawn_look as drawn

    scene = bpy.context.scene
    col = bpy.data.collections["Last Gumball v01"]
    rig = Rig(bpy)
    assert len(rig.ink_modifiers) == 3, rig.ink_modifiers
    scene.frame_set(1)
    warp = drawn._warp_head
    drawn._warp_head = lambda *a, **k: None       # v02-local: keep v01 head proportions
    try:
        look = drawn.apply_drawn_look(rig, col, light_dir=LIGHT_DIR, fists=False)
    finally:
        drawn._warp_head = warp

    # v02-local: the default crown highlight reads as a glossy sheen on this
    # near-black hair. Keep a subtle drawn gradient instead.
    hair = bpy.data.materials["Commuter charcoal hair | drawn"]
    ramp = next(n for n in hair.node_tree.nodes if n.type == "VALTORGB").color_ramp
    base = hair.diffuse_color
    for element in ramp.elements:
        k = .86 if element.position < .2 else 1.10 if element.position > .8 else 1.0
        element.color = tuple(min(1.0, c * k) for c in base[:3]) + (1,)

    # v02-local: v01's hands are cream. A solid black fist merged with the dark
    # machine in the coin insert, so the drawn fist keeps v01's cream paint
    # (flat, unshaded) and gets the drawn look's light-weighted ink outline.
    cream = drawn._flat_material("Commuter | drawn hand cream", look["body_light"], "#FFF9F0", shade=1.0)
    for hand in (bpy.data.objects["Commuter | mitten -1"], bpy.data.objects["Commuter | mitten 1"]):
        for part in hand.children:
            if part.name.startswith("Commuter | mitten"):
                part.hide_render = part.hide_viewport = True
        fist = kit.ball("Commuter | drawn fist", col, FIST[0], FIST[1], cream, hand, 24, 16)
        fist["ricks_role"] = "drawn_fist"
        hull = kit.apply_character_ink(fist, col)
        hull.id_data.visible_shadow = False
        k = drawn._install_ink(hull, look["body_light"], look["world"], drawn.INK["body"])
        look["ink_scale"][hull.name + "|" + hull.id_data.name] = k
        rig.ink_modifiers.append(hull)
    for obj in bpy.data.objects:
        if obj.name.startswith("Pinch pad cream"):
            obj.data.materials[0] = cream

    camera = scene.camera
    for f in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(f)
        drawn.update_ink(rig, camera, pixels=INK_PIXELS, frame=f)
    for mod in rig.ink_modifiers:
        for curve in mod.id_data.animation_data.action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = "LINEAR"
    scene["ricks_look"] = "drawn"
    scene["ricks_ab_source"] = str(SRC)
    scene.frame_set(1)
    return scene, look


def worker(mode, args):
    import bpy
    sys.path[:0] = [str(ROOT / "scripts")]
    import shorts_preflight as gate

    if mode == "proof":
        OUT.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), copy=False)     # versioned copy first
        scene, _ = restyle(bpy)
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
        scene = bpy.context.scene
        (OUT / "frames").mkdir(exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(OUT / "frames/frame_")
        bpy.ops.render.render(animation=True)


def main():
    mode, rest = sys.argv[1], sys.argv[2:]
    if mode == "proof" and BLEND.exists():
        raise SystemExit(f"{BLEND} exists; v02 is built once. Use a new version folder.")
    lock, owner = ROOT / ".blender_gpu.lock", uuid4().hex
    try:
        with lock.open("x", encoding="utf-8") as fh:
            json.dump({"project": "last_gumball/v02", "pid": os.getpid(), "owner": owner}, fh)
    except FileExistsError:
        raise SystemExit(f"GPU busy. Wait for the owner of {lock}.")
    try:
        source = SRC if mode == "proof" else BLEND
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
