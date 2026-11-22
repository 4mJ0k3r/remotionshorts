"""Runnable Rick's Clips starter. Use --out NEW_DIR, then --out DIR --render.

Opt-ins (independent; defaults reproduce the original starter):
  --look drawn      flat drawn-character look (scripts/ricks_drawn_look.py)
  --camera handoff  camera program with an in-shot attention handoff
                    (scripts/ricks_camera.py); the hard cut and ring match stay.
"""
from argparse import ArgumentParser
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

ROOT = next(path for path in Path(__file__).resolve().parents
            if (path / "scripts/ricks_v2_kit.py").is_file())
BLENDER = r"D:\tools\Blender\4.2.23\blender.exe"


def resolve_blender_exe(default=BLENDER):
    """Resolve Blender CLI executable: BLENDER_EXE -> default -> PATH blender -> blender-launcher."""
    env_exe = os.environ.get("BLENDER_EXE", "").strip()
    if env_exe:
        return env_exe
    if default and Path(default).is_file():
        return str(default)
    for name in ("blender", "blender-launcher"):
        found = shutil.which(name)
        if found:
            return found
    return str(default)
END, CUT, FPS = 48, 25, 30
SIZE = (1080, 1920)
PROOFS = (1, 5, 9, 13, 18, 23, 24, 25, 26, 32, 40, END)

def expression(bpy, name, surprised):
    """Draw and pack an original 1024px alpha card without external assets."""
    import numpy as np

    y_grid, x_grid = np.ogrid[0:1:1024j, 0:1:1024j]
    pixels = np.zeros((1024, 1024, 4), dtype=np.float32)
    pixels[:, :, :3] = (.006, .006, .009)
    for x, y, rx, ry in ((.31, .57, .035, .05), (.69, .57, .035, .05),
                         (.31, .69, .08, .017), (.69, .69, .08, .017),
                         (.50, .30, .077, .072 if surprised else .015)):
        pixels[((x_grid-x)/rx)**2 + ((y_grid-y)/ry)**2 <= 1, 3] = 1.
    image = bpy.data.images.new(name, width=1024, height=1024, alpha=True)
    image.pixels.foreach_set(pixels.ravel())
    image.pack()
    return image

def handoff_program(rc, eyes_at):
    """Shot A travels while attention hands off from the desk orb to the hero's eyes,
    then settles; shot B is the original 25-degree move after the hard cut."""
    orb = (.88, .23, .83)
    shot_a = rc.Shot(1, CUT-1, name="orb to hero",
                     pos=rc.Track([(1, (.35, -3.40, 1.20)), (13, (.12, -3.16, 1.20)), (CUT-2, (0, -2.96, 1.20))], "carry"),
                     aim=rc.handoff(orb, eyes_at, 4, 15), focus=rc.handoff(orb, eyes_at, 8, 18), lens=28, fstop=1.6)
    angle = math.radians(25)
    radial = lambda d: (d*math.sin(angle), -d*math.cos(angle), 1.20)
    shot_b = rc.Shot(CUT, END, name="three-quarter", pos=rc.Track([(CUT, radial(2.96)), (END, radial(3.20))], "carry"),
                     aim=(0, .03, 1.02), focus=eyes_at, lens=28, fstop=1.6)
    return rc.CameraProgram([shot_a, shot_b])

def build(bpy, kit, look="cel", camera_mode="keyed"):
    if look not in {"cel", "drawn"} or camera_mode not in {"keyed", "handoff"}:
        raise ValueError(f"Unknown opt-in: look={look!r}, camera={camera_mode!r}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    kit.configure_ricks_scene(scene, width=SIZE[0], height=SIZE[1], fps=FPS, frame_end=END, samples=6)
    col = scene.collection
    bpy.ops.object.camera_add()
    camera = scene.camera = bpy.context.object
    camera.data.lens = 28
    # Peak on both sides of the cut at 70% of the untrimmed flare.
    flash = ((1, 0), (CUT-2, 0), (CUT-1, .007), (CUT, .007), (CUT+1, 0))
    kit.setup_ricks_compositor(scene, camera=camera, portal_flash_keys=flash)
    hero = kit.build_ricks_character("Hero", col, expression_images={
        "curious": expression(bpy, "Curious", False), "surprised": expression(bpy, "Surprised", True)})
    if look == "drawn":
        import ricks_drawn_look as drawn
        drawn.apply_drawn_look(hero, col)

    def block(name, position, size, mat, ink=False):
        bpy.ops.mesh.primitive_cube_add(size=1, location=position)
        obj = kit.put(bpy.context.object, col, mat=mat)
        obj.name = name
        obj.scale = size
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if ink:
            kit.apply_prop_ink(obj, col, depth=4., lens_mm=38, pixels=1.)

    plaster = kit.texture("Painterly indigo", ("#17213c", "#263352", "#455273"), "plaster")
    wood = kit.texture("Matte amber timber", ("#3d2633", "#83523c", "#ba8054"), "wood")
    block("Wall", (0, 1.7, 1.5), (6, .15, 3), plaster)
    block("Floor", (0, 0, -.1), (6, 8, .2), wood)
    block("Desk", (.86, .22, .59), (.88, .52, .12), wood, ink=True)
    for x in (.56, 1.19):
        block("Desk leg", (x, .20, .28), (.075, .075, .56), wood, ink=True)
    for z in (.84, 1.08, 1.32, 1.56, 1.80):
        block("Window blind", (-.77, 1.59, z), (1.03, .095, .08), wood, ink=True)
    amber = kit.emission("Warm practical", "#ffc56c", 2.6)
    kit.ball("Warm desk orb", col, (.88, .23, .83), (.13, .13, .13), amber)
    kit.make_light_cone("Amber cone", col, (.88, .24, 1.77), (.63, .19, .69), .10, .40, "#ffc56c")
    kit.make_ricks_light("Warm key", col, (1.20, -1.45, 2.45), (0, 0, 1.05), "#ffbc80", 215, 1.1)
    kit.make_ricks_light("Cool rim", col, (-1.20, .91, 2.05), (0, 0, 1.05), "#8aaaff", 125, .78)
    eyes = kit.empty("Focus | Hero eyes", col, (0, -.16, .04), hero.head)
    program = focus = None
    if camera_mode == "handoff":
        import ricks_camera as rc
        program = handoff_program(rc, lambda f: tuple(eyes.matrix_world.translation))
        focus = kit.empty("Focus | camera program", col)
        kit.apply_portrait_dof(camera, focus)
    else:
        kit.apply_portrait_dof(camera, eyes)
    kit.setup_hero_portrait_lighting(hero.head)

    # The circular edge occupies the same screen position on the two cut frames.
    ring = kit.tube("Matched gold ring", col, [
        (.51*math.cos(i*math.tau/48), .51*math.sin(i*math.tau/48), -2.10) for i in range(49)
    ], .007, amber, camera)
    legs = [((side*.12, -.025, .027), (side*.13, -.10, .32)) for side in (-1, 1)]
    turn = None
    for frame in range(1, END+1):
        lean = kit.look.ease5((frame-1)/17)
        arms = [((-.20, -.10, .13), (-.23, -.03, .24)),
                ((.21 + .095*lean, -.16 + .07*lean, .12-.05*lean), (.27, -.01, .24))]
        if program is None:
            third = frame >= CUT
            t = kit.look.ease5((frame-CUT)/(END-CUT) if third else (frame-1)/(CUT-2))
            angle = math.radians(25 if third else 0)
            distance = 2.96+.24*t if third else 3.42-.46*t
            camera.location = (distance*math.sin(angle), -distance*math.cos(angle), 1.20)
            kit.aim(camera, (0, .03, 1.02))
            for prop in ("location", "rotation_quaternion"):
                camera.keyframe_insert(prop, frame=frame)
            hero.pose(frame, (0, 0, 0), .16*lean, .12*lean, arms, legs, head_yaw=.30*lean)
        else:
            # Pose first: the aim and focus tracks follow the evaluated eyes.
            hero.pose(frame, (0, 0, 0), .16*lean, .12*lean, arms, legs, head_yaw=.30*lean)
            bpy.context.view_layer.update()
            turn = rc.key_camera(camera, program.evaluate(frame), frame, focus, turn)
        bpy.context.view_layer.update()
        if look == "drawn":
            drawn.update_ink(hero, camera, frame=frame)
        else:
            hero.update_ink(camera, frame=frame)
    hero.display("curious", 1)  # The kit bakes CONSTANT hide_render/hide_viewport switches.
    hero.display("surprised", CUT)
    for prop in ("hide_render", "hide_viewport"):
        ring.driver_add(prop).driver.expression = f"frame < {CUT-1} or frame > {CUT}"
    hero.finish_bake()
    if program is not None:
        for block in (camera, camera.data, focus):
            for curve in block.animation_data.action.fcurves:
                for key in curve.keyframe_points:
                    key.interpolation = "LINEAR"
        scene["ricks_camera_cuts"] = program.cuts
    scene["ricks_look"], scene["ricks_camera"] = look, camera_mode
    scene.frame_set(1)
    return scene

def worker(out, render, look="cel", camera_mode="keyed"):
    import bpy
    sys.path.insert(0, str(ROOT / "scripts"))
    import ricks_v2_kit as kit
    import shorts_preflight as gate

    scene = bpy.context.scene if render else build(bpy, kit, look, camera_mode)
    settings = scene.render
    actual = (settings.resolution_x, settings.resolution_y, settings.resolution_percentage,
              settings.fps, settings.fps_base, settings.pixel_aspect_x, settings.pixel_aspect_y)
    if actual != (*SIZE, 100, FPS, 1, 1, 1):
        raise RuntimeError(f"Expected native 9:16 delivery settings, got {actual}")
    settings.image_settings.file_format = "PNG"
    settings.filepath = "//frames/frame_"
    if render:
        (out / "frames").mkdir()
        bpy.ops.render.render(animation=True)
        return
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "starter.blend"))
    def check_assets(frame):
        assets = gate.validate_resources(scene)
        if not assets["pass"] or assets["target_exceeded"]:
            raise RuntimeError(f"Frame {frame} exceeds asset gates: {assets}")

    report = gate.benchmark(scene, PROOFS, out / "benchmark", update=check_assets)
    if report["status"] != "PASS" or report["telemetry_errors"]:
        raise RuntimeError(f"Benchmark gate failed: {out / 'benchmark/benchmark.json'}")

def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--render", action="store_true", help="Render the saved, benchmarked scene")
    parser.add_argument("--look", choices=("cel", "drawn"), default="cel",
                        help="cel = default 3D cel character; drawn = opt-in flat drawn look")
    parser.add_argument("--camera", choices=("keyed", "handoff"), default="keyed",
                        help="keyed = original camera; handoff = opt-in camera program")
    args = parser.parse_args()
    out = args.out.resolve()
    lock, owner = ROOT / ".blender_gpu.lock", uuid4().hex
    try:
        with lock.open("x", encoding="utf-8") as file:
            json.dump({"project": str(out), "pid": os.getpid(), "owner": owner}, file)
    except FileExistsError:
        raise SystemExit(f"GPU busy. Wait for the owner of {lock} before launching Blender.")
    try:
        cmd = [resolve_blender_exe(), "-b", "--factory-startup"]
        if args.render:
            report = json.loads((out / "benchmark/benchmark.json").read_text(encoding="utf-8"))
            if report["status"] != "PASS" or report["telemetry_errors"]:
                raise SystemExit("A passing benchmark is required.")
            cmd.append(str(out / "starter.blend"))
        else:
            out.mkdir(parents=True)
        subprocess.run([*cmd, "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
                        "--", str(out), "render" if args.render else "proof", args.look, args.camera],
                       check=True, cwd=ROOT)
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("owner") == owner:
            lock.unlink()

if __name__ == "__main__":
    if "--" not in sys.argv:
        main()
    else:  # Blender worker; the launcher owns the shared lock.
        tail = sys.argv[sys.argv.index("--")+1:]
        worker(Path(tail[0]), tail[1] == "render", *tail[2:4])
