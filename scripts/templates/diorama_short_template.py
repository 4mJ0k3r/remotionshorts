"""Flagship Cutaway Diorama Short Starter (1080x1920, 30 fps, EEVEE Next, AgX, 27 mm, DOF off).

Copy this file to `scripts/<new_short>/v01/build.py`, customize the set, props,
story beats, and `CAMERA_SHOTS`, then run on any of the 3 GPU workflows:

  1. Local RTX 3050 GPU (takes `.blender_gpu.lock` automatically):
       python scripts/<new_short>/v01/build.py --out renders/<new_short>/v01 --smoke
       python scripts/<new_short>/v01/build.py --out renders/<new_short>/v01
       python scripts/<new_short>/v01/build.py --out renders/<new_short>/v01 --render

  2. Modal Serverless Cloud GPU (NVIDIA L4/T4, zero local GPU lock):
       modal run scripts/modal_blender.py --mode run --project <new_short>/v01 ^
           --script build.py --runner blender --script-args "--out {out} --smoke"

  3. Remote Linux / Colab GPU via SSH:
       BLENDER_EXE=/opt/blender42/blender python3 scripts/<new_short>/v01/build.py ^
           --out renders/<new_short>/v01 --smoke

Built-in 5 Studio Visual Patterns:
  1. 6:1 directional chiaroscuro lighting + Contact AO (`kit.setup_chiaroscuro_lighting`,
     `kit.make_subtle_light_cone(..., peak_alpha=0.013)`).
  2. Multi-node PBR + continuous geometry (`kit.build_beveled_plank_floor`,
     `kit.make_editorial_brick_material`, `kit.make_brushed_metal_material`,
     `kit.make_glossy_fluid_material`, `kit.build_lofted_tube`, `kit.build_lathe_prop`).
  3. AgX bright paper-white 1:1 round head (`kit.ROUND_HEAD`, `drawn.apply_drawn_look(...,
     head_shape="round", preset="paper_white")`) + pixel-locked closed/talk speech pairs
     (`kit.render_pixel_locked_expression_pair` + `kit.verify_upper_face_lock`).
  4. Deep-focus 27 mm cutaway diorama camera (`kit.setup_diorama_camera_and_compositor`
     with `use_dof=False`, `fog_glow_mix=0.08`, `portal_flash_keys=()`).
  5. Alive 2–6 px/frame camera drift (`rc.beat_drift`) + automatic pre-render
     `ricks_guardrails.audit_scene(...)` check.
"""
from __future__ import annotations

from argparse import ArgumentParser
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from uuid import uuid4

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "scripts/ricks_v2_kit.py").is_file())
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ricks_camera as rc  # noqa: E402

BLENDER = r"D:\tools\Blender\4.2.23\blender.exe"
SIZE = (1080, 1920)
FPS = 30
SAMPLES = 10
LENS_MM = 27.0
FOG_GLOW_MIX = 0.08
CUT_FRAME = 46
END_FRAME = 90
CALIBRATION_FRAMES = (1, 24, CUT_FRAME - 1, CUT_FRAME, 68, END_FRAME)


def resolve_blender_exe(default: str = BLENDER) -> str:
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


def build_camera_program() -> rc.CameraProgram:
    """Two-shot cutaway diorama program with alive 2–6 px/f beat drift and a hard cut."""
    shot_a = rc.Shot(
        1,
        CUT_FRAME - 1,
        name="diorama_wide_drift",
        pos=rc.beat_drift((-0.20, -2.78, 1.12), (0.20, -2.62, 1.10), 1, CUT_FRAME - 1),
        aim=rc.beat_drift((-0.14, 0.0, 0.91), (0.14, 0.0, 0.93), 1, CUT_FRAME - 1),
        lens=LENS_MM,
    )
    shot_b = rc.Shot(
        CUT_FRAME,
        END_FRAME,
        name="three_quarter_talk_drift",
        pos=rc.beat_drift((0.76, -2.35, 1.16), (0.48, -2.26, 1.14), CUT_FRAME, END_FRAME),
        aim=rc.beat_drift((0.10, 0.0, 0.94), (-0.10, 0.0, 0.98), CUT_FRAME, END_FRAME),
        lens=LENS_MM,
    )
    return rc.CameraProgram([shot_a, shot_b])


def _add_box(kit, bpy, name, col, loc, size, mat, *, parent=None, ink=False, ink_t=0.0035):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, 0.0))
    obj = kit.put(bpy.context.object, col, parent=parent, mat=mat)
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.location = loc
    if ink:
        kit.apply_prop_ink(obj, col, thickness=ink_t)
    return obj


def build_scene(art_dir: Path | None = None):
    """Build the dressed cutaway diorama, AgX paper-white 1:1 round-head actor, and camera."""
    import bpy
    import ricks_drawn_look as drawn
    import ricks_v2_kit as kit

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = kit.configure_ricks_scene(
        bpy.context.scene,
        width=SIZE[0],
        height=SIZE[1],
        fps=FPS,
        frame_end=END_FRAME,
        samples=SAMPLES,
    )
    col = scene.collection

    # 1. Deep-focus 27 mm cutaway diorama camera & compositor (DOF strictly OFF)
    camera, _flash = kit.setup_diorama_camera_and_compositor(
        scene,
        lens_mm=LENS_MM,
        fog_glow_mix=FOG_GLOW_MIX,
        clip_end=250.0,
        portal_flash_keys=(),
        replace=True,
    )

    # 2. 6:1 Directional chiaroscuro lighting + EEVEE Next Contact AO
    kit.setup_chiaroscuro_lighting(
        scene,
        col,
        world_color="#182236",
        world_strength=0.16,
        key_watts=180.0,
        fill_watts=30.0,
        rim_watts=75.0,
        gtao_distance=0.55,
    )
    kit.make_subtle_light_cone(
        "Diorama | Practical Beam",
        col,
        top=(0.95, 0.30, 2.35),
        bottom=(0.75, 0.18, 0.62),
        narrow=0.10,
        wide=0.46,
        color="#FFC970",
        peak_alpha=0.013,
    )

    # 3. Rich multi-node PBR architectural set & continuous lofted/lathed props
    kit.build_beveled_plank_floor(
        col,
        name="Diorama | Oak Floor",
        x0=-3.6,
        x1=3.6,
        y0=-2.2,
        y1=2.4,
        z=0.0,
        plank_w=0.18,
    )
    m_brick = kit.make_editorial_brick_material("Diorama | Editorial Brick")
    m_tile = kit.make_tile_material("Diorama | Ceramic Dado")
    m_metal = kit.make_brushed_metal_material("Diorama | Brushed Brass", "#D4A857", metallic=0.84, roughness=0.26)
    m_wood = kit.make_plank_wood_material("Diorama | Workbench Wood", "#7A4E2F", rough=0.42)
    m_fluid, fluid_mapping = kit.make_glossy_fluid_material("Diorama | Flowing Fluid", "#1D7FA8", "#68D8F5")

    _add_box(kit, bpy, "Diorama | Back Brick Wall", col, (0.0, 2.10, 1.55), (7.2, 0.18, 3.10), m_brick)
    _add_box(kit, bpy, "Diorama | Ceramic Dado", col, (0.0, 1.98, 0.45), (7.2, 0.04, 0.90), m_tile)
    _add_box(kit, bpy, "Diorama | Workbench Top", col, (0.88, 0.35, 0.64), (0.92, 0.56, 0.08), m_wood, ink=True)
    for lx in (0.50, 1.26):
        _add_box(kit, bpy, f"Diorama | Bench Leg {lx:.2f}", col, (lx, 0.35, 0.30), (0.07, 0.46, 0.60), m_wood, ink=True)

    # Lathed continuous brass flask (zero sphere soup)
    flask_profile = [
        (0.085, 0.00),
        (0.095, 0.05),
        (0.082, 0.13),
        (0.036, 0.21),
        (0.032, 0.28),
        (0.044, 0.30),
    ]
    flask = kit.build_lathe_prop("Diorama | Lathed Brass Flask", col, flask_profile, m_metal,
                                 loc=(0.82, 0.28, 0.68), segments=24, cap_bottom=True, cap_top=False)
    kit.apply_prop_ink(flask, col, thickness=0.003)

    # Continuous lofted tube carrying animated glossy fluid
    pipe_pts = [
        (0.82, 0.28, 0.96),
        (0.82, 0.38, 1.18),
        (1.06, 0.50, 1.24),
        (1.18, 0.48, 0.92),
        (1.18, 0.40, 0.68),
    ]
    kit.build_lofted_tube("Diorama | Fluid Stream", col, pipe_pts, 0.022, m_fluid, segments=16)
    fluid_mapping.inputs["Location"].default_value = (0.0, 0.0, 0.0)
    fluid_mapping.inputs["Location"].keyframe_insert("default_value", frame=1)
    fluid_mapping.inputs["Location"].default_value = (0.0, -3.0, 0.0)
    fluid_mapping.inputs["Location"].keyframe_insert("default_value", frame=END_FRAME)

    # 4. Pixel-locked closed/talk expressions + 1:1 round AgX paper-white character
    expr_dir = Path(art_dir) if art_dir is not None else (ROOT / "renders/_template_art")
    pair = kit.render_pixel_locked_expression_pair(expr_dir, "hero_neutral", mood="neutral", size=512)
    assert pair["lock"]["pass"], f"Upper-face lock failed: {pair['lock']}"

    hero = kit.build_ricks_character(
        "Hero",
        col,
        head_radii=kit.ROUND_HEAD,
        expression_images={"closed": pair["closed"], "talk": pair["talk"]},
        initial_expression="closed",
    )
    drawn.apply_drawn_look(hero, col, head_shape="round", preset="paper_white")
    ratio_info = kit.normalize_head_proportions(hero, radii=kit.ROUND_HEAD)
    assert not ratio_info["is_squashed"], f"Unexpected head squash: {ratio_info}"

    # 5. Bake alive beat-drift camera & expressive dialogue pose
    program = build_camera_program()
    scene["ricks_camera_cuts"] = rc.bake(camera, program)
    camera.data.dof.use_dof = False

    stand_legs = [((s * 0.11, -0.02, 0.027), (s * 0.10, -0.07, 0.32)) for s in (-1, 1)]
    for f in range(1, END_FRAME + 1):
        u = (f - 1) / max(1, END_FRAME - 1)
        gesture = math.sin(math.tau * 2.0 * u)
        arms = [
            ((-0.20, -0.09, 0.14 + 0.03 * gesture), (-0.23, -0.02, 0.24)),
            ((0.23, -0.14, 0.18 + 0.06 * max(0.0, gesture)), (0.25, -0.02, 0.25)),
        ]
        # Pixel-locked closed/talk lip-sync syllables (eyes stay 100% locked!)
        expr = "talk" if ((f // 5) % 2 == 1 and 8 <= f <= END_FRAME - 6) else "closed"
        hero.pose(
            f,
            location=(0.0, 0.0, 0.0),
            yaw=0.10 * math.sin(math.pi * u),
            tilt=0.04 * math.sin(math.tau * u),
            arms=arms,
            legs=stand_legs,
            expression=expr,
            bounce=0.008 * abs(math.sin(math.tau * 2.0 * u)),
            head_yaw=0.08 * math.sin(math.tau * u),
        )
        scene.frame_set(f)
        bpy.context.view_layer.update()
        drawn.update_ink(hero, camera, frame=f)

    hero.finish_bake()
    scene.frame_set(1)
    return scene, hero, camera


def run_pre_render_guardrails(scene, hero, out_dir: Path) -> dict | None:
    """Run `ricks_guardrails.audit_scene(...)` pre-render gate and save JSON report."""
    try:
        import ricks_guardrails as guardrails
    except ModuleNotFoundError:
        return None
    audit = guardrails.audit_scene(
        scene,
        rigs=(hero,),
        subjects=(hero.head,),
        frames=CALIBRATION_FRAMES,
        expect_deep_focus=True,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "guardrails_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    if not audit.get("pass", False):
        hints = "\n".join(
            f"  - [{iss.get('severity', 'ERROR')}] {iss.get('check')}: {iss.get('detail')} -> {iss.get('fix_hint')}"
            for iss in audit.get("issues", [])
        )
        raise RuntimeError(f"Pre-render guardrails failed:\n{hints}")
    return audit


def _parse_args(argv):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "renders/diorama_starter/v01")
    parser.add_argument("--smoke", action="store_true", help="Build, audit, validate resources, and save .blend only")
    parser.add_argument("--render", action="store_true", help="Render full 1080x1920 animation PNG frames")
    args = parser.parse_args(argv)
    args.out = args.out.resolve()
    return args


def worker(argv):
    import bpy
    import shorts_preflight as gate

    args = _parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    blend_path = args.out / "diorama.blend"
    art_dir = args.out / "art"

    if args.render and bpy.data.filepath and Path(bpy.data.filepath).resolve() == blend_path:
        scene, camera = bpy.context.scene, bpy.context.scene.camera
        hero = None
    else:
        scene, hero, camera = build_scene(art_dir=art_dir)
        run_pre_render_guardrails(scene, hero, args.out)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    r = scene.render
    actual = (r.engine, r.resolution_x, r.resolution_y, r.resolution_percentage, r.fps)
    if actual != ("BLENDER_EEVEE_NEXT", *SIZE, 100, FPS):
        raise RuntimeError(f"Expected native 1080x1920 @ 30fps EEVEE Next, got {actual}")
    if camera.data.dof.use_dof:
        raise RuntimeError("Deep-focus cutaway diorama requires camera.data.dof.use_dof == False")

    res = gate.validate_resources(scene)
    if not res["pass"] or res["target_exceeded"]:
        raise RuntimeError(f"Resource gate failed: {res}")

    if args.smoke:
        print(f"DIORAMA_STARTER_SMOKE_OK tris={res['visible_triangles']} blend={blend_path}")
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
        if args.render and (args.out / "diorama.blend").is_file():
            cmd.append(str(args.out / "diorama.blend"))
        fwd = ["--out", str(args.out)]
        if args.smoke:
            fwd.append("--smoke")
        if args.render:
            fwd.append("--render")
        subprocess.run(
            [*cmd, "--python-exit-code", "1", "--python", str(Path(__file__).resolve()), "--", *fwd],
            check=True,
            cwd=ROOT,
        )
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("owner") == owner:
            lock.unlink()


if __name__ == "__main__":
    if "bpy" in sys.modules:
        worker(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    else:
        main()
