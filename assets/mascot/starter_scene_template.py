"""Runnable Mascot Short starter (1080x1920, 30 fps, EEVEE Next, 32 samples, 26mm, DOF off).

Copy to `scripts/<new_short>/v01/build.py`, edit STORY_BEATS & CAMERA_SHOTS, then run:
  Modal GPU : modal run scripts/modal_blender.py --mode run --project <new_short>/v01 --script build.py --runner blender --script-args "--out {out} --render"
  Local GPU : python scripts/<new_short>/v01/build.py --out renders/<new_short>/v01 [--render]
"""
from argparse import ArgumentParser
import inspect, json, os, shutil, subprocess, sys
from pathlib import Path
from uuid import uuid4

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "scripts/ricks_v2_kit.py").is_file())
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import ricks_camera as rc  # noqa: E402

BLENDER = r"D:\tools\Blender\4.2.23\blender.exe"
SIZE, FPS, SAMPLES, LENS_MM, END_FRAME = (1080, 1920), 30, 32, 26.0, 150
CALIBRATION_FRAMES = (1, 30, 78, 135)


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

# --- 1. EDIT STORY BEATS (any anim_library.* calls across 1..END_FRAME) ---
STORY_BEATS = [
    lambda hero, cam: anim_library.walk_to(hero, 1, 54, (0.0, 1.15), (0.0, 0.0)),
    lambda hero, cam: anim_library.stop_hold_up(hero, 55, 102, loc=(0.0, 0.0, 0.0)),
    lambda hero, cam: anim_library.point_at_camera_wink(hero, 103, END_FRAME, loc=(0.0, 0.0, 0.0), camera=cam),
]

# --- 2. EDIT CAMERA SHOTS (hard cuts at shot boundaries; 26mm wide vertical lens) ---
CAMERA_SHOTS = [
    rc.Shot(1, 54, name="walk_arrival",
            pos=rc.Track([(1, (0.52, -2.45, 1.02)), (54, (0.18, -1.90, 0.90))], "carry"),
            aim=rc.Track([(1, (0.0, 0.95, 0.78)), (54, (0.0, 0.0, 0.82))], "ease"), lens=LENS_MM),
    rc.Shot(55, 102, name="hold_up_low_26mm",
            pos=rc.Track([(55, (-0.26, -1.45, 0.70)), (102, (-0.32, -1.58, 0.74))], "ease"),
            aim=(0.0, 0.0, 0.86), lens=LENS_MM),
    rc.Shot(103, END_FRAME, name="wink_payoff",
            pos=rc.Track([(103, (0.36, -1.76, 0.92)), (126, (0.26, -1.64, 0.90))], "ease"),
            aim=(0.0, 0.0, 0.86), lens=LENS_MM),
]


def build_scene():
    """Build dressed Rick's studio scene, load Mascot, and bake STORY_BEATS + CAMERA_SHOTS."""
    import bpy, ricks_v2_kit as kit
    global mascot_api, anim_library
    from assets.mascot import anim_library, mascot_api

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = kit.configure_ricks_scene(bpy.context.scene, width=SIZE[0], height=SIZE[1],
                                      fps=FPS, frame_end=END_FRAME, samples=SAMPLES)
    col = scene.collection
    camera, _flash = kit.setup_diorama_camera_and_compositor(
        scene,
        lens_mm=LENS_MM,
        fog_glow_mix=0.08,
        clip_end=250.0,
        portal_flash_keys=(),
        replace=True,
    )

    kit.look.make_world(scene, actor_height=1.28)
    kit.build_beveled_plank_floor(
        col,
        name="Studio | Floor",
        x0=-4.0,
        x1=4.0,
        y0=-3.7,
        y1=4.3,
        z=0.0,
        plank_w=0.18,
    )
    plaster = kit.texture("Studio | Wall", ("#1E2D4D", "#2E436E", "#4A669C"), "plaster")
    timber = kit.make_plank_wood_material("Studio | Plinth Wood", "#8C6245", rough=0.46)
    for name, pos, scale, mat, inked in (
        ("Studio | Backdrop", (0.0, 2.35, 1.55), (7.5, 0.16, 3.20), plaster, False),
        ("Studio | Plinth", (0.85, 0.55, 0.32), (0.52, 0.52, 0.64), timber, True),
    ):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=pos)
        obj = kit.put(bpy.context.object, col, mat=mat)
        obj.name, obj.scale = name, scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if inked:
            kit.apply_prop_ink(obj, col, thickness=0.005)
    kit.ball("Studio | Orb", col, (0.85, 0.55, 0.76), (0.12, 0.12, 0.12), kit.emission("Orb", "#FFC970", 2.4))
    kit.look.make_sun(scene, "Studio | Sun", azimuth=128, elevation=42, energy=1.6, color="#FFE8C8", shadows=True)
    kit.make_ricks_light("Studio | Key", col, (1.35, -1.85, 2.15), (0.0, 0.0, 0.85), "#FFF3E0", 185, size=0.85)
    kit.make_ricks_light("Studio | Rim", col, (-1.45, 1.25, 2.05), (0.0, 0.0, 0.90), "#8CC4FF", 125, size=0.75)

    scene["ricks_camera_cuts"] = rc.bake(camera, rc.CameraProgram(CAMERA_SHOTS))
    camera.data.dof.use_dof = False
    hero = mascot_api.load_mascot(col, name="Mascot", bottom_style="pajamas", arm_style="hoodie")
    for beat in STORY_BEATS:
        beat(hero, camera) if len(inspect.signature(beat).parameters) >= 2 else beat(hero)
    for frame in range(1, END_FRAME + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        hero.update_ink(camera, frame=frame)
    hero.finish_bake()
    scene.frame_set(1)
    return scene, hero, camera


def _parse_args(argv):
    p = ArgumentParser(description=__doc__)
    p.add_argument("pos_out", nargs="?", default=None)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--render", action="store_true")
    p.add_argument("--smoke", action="store_true")
    a = p.parse_args(argv)
    a.out = Path(a.out or a.pos_out or (ROOT / "renders/mascot_starter/v01")).resolve()
    return a


def worker(argv):
    import bpy, shorts_preflight as gate
    args = _parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    blend_path = args.out / "starter.blend"
    if args.render and bpy.data.filepath and Path(bpy.data.filepath).resolve() == blend_path:
        scene, camera = bpy.context.scene, bpy.context.scene.camera
    else:
        scene, hero, camera = build_scene()
        assert 1.00 <= hero.head_bbox_ratio()["ratio"] <= 1.05, hero.head_bbox_ratio()
        try:
            import ricks_guardrails as guardrails
        except ModuleNotFoundError:
            guardrails = None
        if guardrails is not None:
            audit = guardrails.audit_scene(
                scene,
                rigs=(hero,),
                subjects=(hero.head,),
                frames=CALIBRATION_FRAMES,
                expect_deep_focus=True,
            )
            (args.out / "guardrails_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
            if not audit.get("pass", False):
                raise RuntimeError(f"Pre-render guardrails failed: {audit.get('issues', [])}")
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    r = scene.render
    assert (r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps) == ("BLENDER_EEVEE_NEXT", *SIZE, 100, FPS)
    assert scene.eevee.taa_render_samples == SAMPLES and not camera.data.dof.use_dof and abs(camera.data.lens - LENS_MM) < 1e-4
    res = gate.validate_resources(scene)
    if not res["pass"] or res["target_exceeded"]:
        raise RuntimeError(f"Resource gate failed: {res}")
    if args.smoke:
        print(f"MASCOT_STARTER_SMOKE_OK tris={res['visible_triangles']} blend={blend_path}")
        return
    r.image_settings.file_format = "PNG"
    if args.render:
        (args.out / "frames").mkdir(parents=True, exist_ok=True)
        r.filepath = str(args.out / "frames/frame_")
        bpy.ops.render.render(animation=True)
    else:
        (args.out / "calibration").mkdir(parents=True, exist_ok=True)
        for f in CALIBRATION_FRAMES:
            scene.frame_set(f)
            r.filepath = str(args.out / f"calibration/frame_{f:04d}.png")
            bpy.ops.render.render(write_still=True)


def main():
    args = _parse_args(sys.argv[1:])
    lock, owner = ROOT / ".blender_gpu.lock", uuid4().hex
    try:
        with lock.open("x", encoding="utf-8") as fh:
            json.dump({"project": str(args.out), "pid": os.getpid(), "owner": owner}, fh)
    except FileExistsError:
        raise SystemExit(f"GPU busy. Wait for the owner of {lock} before launching Blender.")
    try:
        cmd = [resolve_blender_exe(), "-b", "--factory-startup"]
        if args.render and (args.out / "starter.blend").is_file():
            cmd.append(str(args.out / "starter.blend"))
        fwd = ["--out", str(args.out)] + (["--render"] if args.render else []) + (["--smoke"] if args.smoke else [])
        subprocess.run([*cmd, "--python-exit-code", "1", "--python", str(Path(__file__).resolve()), "--", *fwd], check=True, cwd=ROOT)
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("owner") == owner:
            lock.unlink()


if __name__ == "__main__":
    worker(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []) if "bpy" in sys.modules else main()
