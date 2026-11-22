# AGENTS.md — Master Router (`remotionshorts`)

Default engine for all new animated Shorts: **Blender 4.2 LTS (`BLENDER_EEVEE_NEXT`, `1080 × 1920 @ 30 fps`, RT OFF)** using the Rick's Clips v7 workflow.
Read this router first, then [RICKS_STYLE_SKILL.md (v7)](RICKS_STYLE_SKILL.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
An explicitly requested renderer (such as Remotion in `src/engine/`) or archived look takes precedence for that task only.

---

## 1. Decision Tree (Start Here)

### Step A — Cast: Official Main Character vs. Custom Cast
- **Featuring our Main Character (Red-Beanie Yellow-Hoodie Chibi Mascot)?** Use [`assets/mascot/`](assets/mascot/README.md) directly. **NEVER rebuild him from primitives.** Copy [`assets/mascot/starter_scene_template.py`](assets/mascot/starter_scene_template.py) to `scripts/<short_name>/v01/build.py`.
- **Custom / stick-hybrid cast or diorama explainer?** Start from [`scripts/templates/diorama_short_template.py`](scripts/templates/diorama_short_template.py) (flagship v7 starter) or [`scripts/templates/ricks_short_template.py`](scripts/templates/ricks_short_template.py) (baseline/opt-in smoke) and import [`scripts/ricks_v2_kit.py`](scripts/ricks_v2_kit.py) + [`scripts/ricks_camera.py`](scripts/ricks_camera.py).

### Step B — Pick Your GPU Execution Workflow (3 Supported Paths)

| # | Workflow | Hardware / Lock Rule | Exact Command |
| :- | :--- | :--- | :--- |
| **1** | **Local PC + Local RTX 3050 GPU** | Exclusive `.blender_gpu.lock` (`project`, `pid`, `owner`), `<150k` tris, `<=2.0s/f`, `<=3.3 GiB` VRAM, no parallel Chromium | `$env:BLENDER_EXE='D:\tools\Blender\4.2.23\blender.exe'; python scripts/<short>/v01/build.py --out renders/<short>/v01` (add `--render` when authorized) |
| **2** | **Local PC + Modal Serverless Cloud GPU** *(recommended for heavy renders)* | NVIDIA L4/T4 headless EGL (`/opt/blender42/blender`), zero idle billing, auto-bundles core kit + `assets/mascot/` + ONE project; **never touches `.blender_gpu.lock`** | `modal run scripts/modal_blender.py --mode run --project <short>/v01 --script build.py --runner blender --script-args "--out {out} --render"` |
| **3** | **Local PC + Remote Linux / Colab Cloud GPU via SSH** | Direct Linux Blender 4.2 CLI (`BLENDER_EXE=/opt/blender42/blender`); optional authenticated desktop bridge in `tools/blender_remote_bridge/` | `BLENDER_EXE=/opt/blender42/blender /opt/blender42/blender -b --factory-startup --python scripts/<short>/v01/build.py -- --out renders/<short>/v01` |

---

## 2. Official Main Character (`assets/mascot/`) — Do NOT Rebuild From Scratch

Our permanent 3D Main Character — the chunky 3-head-tall **Chibi Mascot** with a `4°`-tilted crimson ribbed knit beanie, snow-white marshmallow head (`1.00 <= H/W <= 1.05`), big glossy black oval eyes, and oversized yellow hoodie — lives in [`assets/mascot/mascot_master.blend`](assets/mascot/mascot_master.blend) and is **auto-synced to Modal** by `scripts/modal_blender.py` (`CORE_PATTERNS`).

1. Read [`assets/mascot/MASCOT_SKILL.md`](assets/mascot/MASCOT_SKILL.md) and [`assets/mascot/README.md`](assets/mascot/README.md) before authoring.
2. Import `from assets.mascot import mascot_api, anim_library` or copy [`assets/mascot/starter_scene_template.py`](assets/mascot/starter_scene_template.py) to `scripts/<short_name>/v01/build.py`.
3. Load with `hero = mascot_api.load_mascot(collection)` (`bottom_style="pajamas"|"shorts"`, `arm_style="hoodie"|"stick"`).
4. Use his built-in studio tools: **12 story expressions**, **6 lip-sync visemes** via `hero.auto_lipsync(audio_path, f0, f1)`, **7 swappable 3D hand poses**, zero-gap prop sockets via `hero.attach_prop(prop, side="R", f_start=..., f_end=...)`, and **18 studio-ready actions** in `anim_library.py` (`stop_hold_up`, `power_aura_stance`, `chill_chair_lean`, `walk_to`, `run_panic_to`, `talk_explain`, etc.).
5. Per frame, call `hero.update_ink(camera, frame=f)` and close every bake with `hero.finish_bake()`.

---

## 3. Five Non-Negotiable Visual & Craft Laws (v7)

All five laws are implemented directly in [`scripts/ricks_v2_kit.py`](scripts/ricks_v2_kit.py) and demonstrated runnable in [`scripts/templates/diorama_short_template.py`](scripts/templates/diorama_short_template.py):

1. **6:1 Chiaroscuro + Contact AO (No Flat Ambient Boxes):** Low-ambient cool slate world (`0.14–0.38`), `fast_gi_method='AMBIENT_OCCLUSION_ONLY'`, `gtao_distance=0.45–0.65`, 6:1 directional warm key vs. shadowless cool fill/rim (`kit.setup_chiaroscuro_lighting(...)`), and feathered light cones capped at `peak_alpha <= 0.015` (`kit.make_subtle_light_cone(...)`).
2. **Multi-Node PBR + Real Geometry (No Stretched Cubes or Sphere Soup):** Use beveled 3D wood planks (`kit.build_beveled_plank_floor`), brushed metal (`kit.make_brushed_metal_material`), editorial brick/tile (`kit.make_editorial_brick_material`, `kit.make_tile_material`), animated glossy fluids (`kit.make_glossy_fluid_material`), and continuous lofted/lathed props (`kit.build_lofted_tube`, `kit.build_lathe_prop`).
3. **AgX Paper-White Faces + Pixel-Locked Speech (`0` Upper-Face Diff):** Use `kit.make_bright_paper_face_material(...)` (`#FAF9F6` / `#EAE8E1`) so faces never turn muddy grey under AgX. Generate closed/open mouth pairs via `kit.render_pixel_locked_expression_pair(...)` so the upper `55%` of the face is pixel-identical (`max_abs_diff == 0`) — zero syllable eye-flutter.
4. **Upright / `1:1` Round Heads (Strictly Ban Squashed Ovals):** Pass `head_radii=kit.ROUND_HEAD` `(0.235, 0.205, 0.235)` or `kit.UPRIGHT_HEAD` `(0.230, 0.205, 0.238)` (or `kit.normalize_head_proportions(rig)`), keeping `0.98 <= H/W <= 1.12` (Mascot `[1.00, 1.05]`). In `ricks_drawn_look.py`, use `shape="round"` / `"upright"` (`z_scale >= 1.00`).
5. **Deep-Focus 26–28 mm Diorama Camera + Alive Beat Drift:** Call `kit.setup_diorama_camera_and_compositor(scene, camera, lens_mm=27.0, fog_glow_mix=0.08)` which strictly enforces `camera.data.dof.use_dof = False` *after* compositor setup, zero portal flashes unless authored, and alive `2–6 px/f` motion via `ricks_camera.beat_drift(...)`.

---

## 4. Mandatory Pre-Render Guardrails & QA Gates

Run **BEFORE** any GPU render (zero wasted cloud/local GPU time):

1. **Scene Guardrails ([`scripts/ricks_guardrails.py`](scripts/ricks_guardrails.py)):** Call `ricks_guardrails.audit_scene(scene, rigs=[...], subjects=[...], frames=[...])` inside build scripts or via `--blend`. Verifies head ratio (`0.98–1.12`), 9:16 frustum safe margin (`0.04`), limb stretch (`<=1.25x`), camera facing (`dot >= 0.15`), viewport/render parity, EEVEE contract (`BLENDER_EEVEE_NEXT`, RT OFF, `1080×1920 @ 30fps`, `use_dof=False`, `<150k` tris), and upper-face pixel lock (`check_upper_face_pixel_lock`). Fix every reported `fix_hint` before rendering.
2. **Preflight & Post-Render Gates (CPU-local):**
   - `scripts/shorts_preflight.py` (visible tris, asset sanitization, camera clearance)
   - `scripts/ricks_metrics_gate.py` (`--edge-density`, `--cam-velocity`, `--word-sync`)
   - `scripts/short_qa.py` + `ffprobe` / `ffmpeg -v error -xerror -i <mp4> -f null -` (verify native `1080 × 1920`, `SAR 1:1`, `30 fps`, full decode).

---

## 5. Visual Reference Catalog on Disk

Inspect these local references before lookdev or posing (git-ignored refs stay local — never commit them):
- **Official Mascot Proofs:** `assets/mascot/previews/` (`turnaround_4views.png`, `expression_grid_18.png`, `hero_3_reference_poses.png`, `mascot_demo_reel_1080p.mp4`)
- **Style Reference Stills & Motion:** `example-animation/` (8 reference screenshots + `washroom_experiment_1080p.mp4`)
- **Vendor Study Kits (personal-use, git-ignored):** `refs/vendor/` (`ricksclips_v1.1/`, `tickingatlas_v12/`, `README_LOCAL.md`)
- **School Cast Sheet:** `character_sheet.png`

---

## 6. Repo Map & Operating Rules

- **Full Architecture:** See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the directory tree, dependency graph, and active production layout.
- **Quarantined Legacy Docs (Do NOT use as default rules for new Shorts):** [`docs/archive/`](docs/archive/README.md) (`BLENDER_SKILL.md`, `ANIMATION_STYLE_HANDOFF.md`, `PROJECT_MANIFEST.md`, `SHORTS_PIPELINE.md`) and `animated-3d-story-video/`. `scripts/ricks_lookdev.py` is an internal kit dependency; enter through `scripts/ricks_v2_kit.py`.
- **Paused Local Handoff (`gold_mine_salting_10s` / `gold_mine_salting_v2`):** Read `HANDOFF_GOLD_MINE_SALTING_V2.md` first if present. Stopped on 2026-11-17 to switch accounts; no native V2 final has been rendered. Resume **only** when the user explicitly asks to continue.
- **Brief Hygiene & Defaults:** Use only the current story, assets, backend, text preferences, and authorized render stage. Do not resume a prior production just because its scripts exist. Default to **no subtitles** unless requested; a zero-text brief also excludes HUD and baked scene lettering.
- **Stop / Partial Delivery:** On a stop or partial-delivery request, stop only the owned job and deliver its validated completed prefix with matching audio. Never silently restart afterward.
- **Remotion Override:** When Remotion is explicitly requested, reuse `src/engine/`, register in `src/Root.tsx`, and verify `npx tsc --noEmit`.
- **Excluded Assets:** Voice tracks, Blender binaries, private references, and renders are git-ignored; a missing local MP4 is not evidence of reviewed motion. Always inspect calibration stills and contact extremes before full renders.
