---
name: ricks-clips-blender-style
description: Proven Blender 4.2 EEVEE Next v7 system for Rick's Clips–style vertical Shorts (6:1 chiaroscuro 3D dioramas, multi-node PBR worlds, Official Mascot + upright/1:1 stick-hybrid cast, pixel-locked expressions, deep-focus 26–28 mm camera choreography, and pre-render guardrails).
---

# Rick's Clips Style Skill v7 — Chiaroscuro Dioramas, Pixel-Locked Acting & Pre-Render Guardrails

Use this spec with [`scripts/ricks_v2_kit.py`](scripts/ricks_v2_kit.py), [`scripts/ricks_guardrails.py`](scripts/ricks_guardrails.py), and [`scripts/templates/diorama_short_template.py`](scripts/templates/diorama_short_template.py) for all new vertical 9:16 Shorts (`1080 × 1920 @ 30 fps`, `BLENDER_EEVEE_NEXT`, `use_raytracing = False`).
- **Official Main Character:** Whenever a Short features the Red-Beanie Yellow-Hoodie Chibi Mascot, **never rebuild him from primitives** — load [`assets/mascot/`](assets/mascot/MASCOT_SKILL.md) via `mascot_api.load_mascot(collection)` and start from [`assets/mascot/starter_scene_template.py`](assets/mascot/starter_scene_template.py).
- **Keep Hardware & Pipeline Safety:** `< 150,000` visible evaluated tris, `<= 2.0 s/frame` max (`<= 1.8 s` p95) and `<= 3.3 GiB` VRAM on RTX 3050, `.blender_gpu.lock` on local GPU, versioned project folders (`scripts/<short>/v01/`), and save/reopen checks.
- **Quarantined Legacy Docs:** Do NOT follow archived flat-card, V13 lookdev, or static-hold rules in [`docs/archive/`](docs/archive/README.md) (`BLENDER_SKILL.md`, `ANIMATION_STYLE_HANDOFF.md`, `SHORTS_PIPELINE.md`) or `animated-3d-story-video/` unless explicitly requested.

---

## 1. The Five Non-Negotiable v7 Craft Upgrades

1. **6:1 Directional Chiaroscuro + Contact AO (Zero Flat Ambient Boxes):**
   - Call `kit.setup_chiaroscuro_lighting(scene, col, world_color="#182236", world_strength=0.16, key_watts=180.0, fill_watts=30.0, gtao_distance=0.55)`.
   - Keeps world ambient low (`0.14–0.38`), enables `fast_gi_method = 'AMBIENT_OCCLUSION_ONLY'` with contact GTAO (`0.45–0.65`), drives a 6:1 directional warm key against a shadowless cool fill/rim, and uses `kit.make_subtle_light_cone(..., peak_alpha=0.013)` strictly capped at `peak_alpha <= 0.015`.
2. **Rich Multi-Node PBR + Real Geometry (Zero Stretched Noise Cubes or Sphere Soup):**
   - Build architectural floors with `kit.build_beveled_plank_floor(...)` (`0.18 m` beveled wood planks in 3 oak tones merged into 3 low-draw-call meshes).
   - Shade sets and hero props with `kit.make_plank_wood_material`, `kit.make_brushed_metal_material`, `kit.make_editorial_brick_material`, `kit.make_tile_material` (matte grout vs. glossy tile), and animated glossy liquids via `kit.make_glossy_fluid_material` (returns `(mat, mapping_node)`).
   - Sculpt continuous curved props with `kit.build_lofted_tube(...)` and `kit.build_lathe_prop(...)` — never assemble props from stacked raw spheres.
3. **AgX Bright Paper-White Faces + Pixel-Locked Speech (`0` Upper-Face Diff):**
   - Use `kit.make_bright_paper_face_material(...)` (`PAPER_WHITE_FACE = "#FAF9F6"`, `PAPER_WHITE_SHADOW = "#EAE8E1"`) so faces read crisp paper-white under AgX Medium High Contrast (never muddy grey).
   - Generate closed/open mouth pairs using `kit.render_pixel_locked_expression_pair(...)` and validate with `ricks_guardrails.check_upper_face_pixel_lock(closed, open)` (`split_y_frac=0.55`, `max_abs_diff=0`). Zero syllable eye-flutter.
4. **Upright / `1:1` Round Heads (Strictly Ban Squashed Horizontal Ovals):**
   - Pass `head_radii=kit.ROUND_HEAD` `(0.235, 0.205, 0.235)` or `kit.UPRIGHT_HEAD` `(0.230, 0.205, 0.238)` to `build_ricks_character(...)` (or call `kit.normalize_head_proportions(rig)`), keeping evaluated `0.98 <= H/W <= 1.12`.
   - For the Official Mascot (`assets/mascot/`), preserve his exact marshmallow ratio `1.00 <= H/W <= 1.05` (`0.440 × 0.400 × 0.448 m`).
   - With `scripts/ricks_drawn_look.py`, use `shape="round"` (`z_scale=1.00`) or `"upright"` and optional `preset="paper_white"`.
5. **Deep-Focus 26–28 mm Diorama Camera + Alive Beat Drift:**
   - Call `kit.setup_diorama_camera_and_compositor(scene, camera, lens_mm=27.0, fog_glow_mix=0.08, clip_end=250.0, portal_flash_keys=())`.
   - Strictly enforces `sensor_fit = 'VERTICAL'`, `sensor_height = 36.0`, `camera.data.dof.use_dof = False` **after** `setup_ricks_compositor()` (preventing accidental background blur on comic/diorama shots), crisp `0.08` Fog Glow, and zero unauthored portal flashes.
   - Keep beats alive (`2–6 px/frame` gentle motion) using `ricks_camera.beat_drift(p0, p1, f0, f1)`. Use shallow portrait DOF (`kit.apply_portrait_dof(...)`, `f/1.5–1.8`) only when explicitly authoring a portrait close-up shot (pass `expect_deep_focus=False` to `audit_scene`).

---

## 2. Three Supported GPU Execution Workflows

Choose the workflow that fits the task; **all CPU QA (`ricks_guardrails.py` expression checks, `ricks_metrics_gate.py`, `short_qa.py`, `ffprobe`, unit tests) stays local and free**.

### Workflow 1 — Local PC + Local RTX 3050 GPU (4 GB VRAM)
Run from the repo root. Every local Blender launcher MUST exclusively create `.blender_gpu.lock` (`project`, `pid`, `owner`), wait for its child process, and release only its own lock. Keep Chromium GPU renders out of the same window.

```powershell
$env:BLENDER_EXE = 'D:\tools\Blender\4.2.23\blender.exe'
python scripts/templates/diorama_short_template.py --out renders/diorama_starter/v01
# Inspect calibration stills + guardrail report. Run native render only when authorized:
python scripts/templates/diorama_short_template.py --out renders/diorama_starter/v01 --render
ffmpeg -n -framerate 30 -i renders/diorama_starter/v01/frames/frame_%04d.png -c:v libx264 -vf setsar=1 -pix_fmt yuv420p renders/diorama_starter/v01/starter.mp4
```

### Workflow 2 — Local PC + Modal Serverless Cloud GPU (`scripts/modal_blender.py`)
Runs Blender `4.2.23` headless via hardware NVIDIA EGL on L4/T4 (`single_use_containers=True`, zero idle billing). Automatically uploads core kit (`scripts/*.py`, `scripts/templates/**`, `scripts/studio/**`), `assets/mascot/`, and ONE project folder; mirrors outputs into `renders/` and never touches local `.blender_gpu.lock`.

```powershell
# Proof of hardware EGL + Blender 4.2 on Modal L4:
modal run scripts/modal_blender.py --mode verify

# Build + pre-render guardrails + calibration stills:
modal run scripts/modal_blender.py --mode run --project <short>/v01 --script build.py --runner blender --script-args "--out {out}"

# Authorized full 1080x1920 @ 30fps render + H.264 MP4 encode:
modal run scripts/modal_blender.py --mode run --project <short>/v01 --script build.py --runner blender --script-args "--out {out} --render"
```

### Workflow 3 — Local PC + Remote Linux / Colab Cloud GPU via SSH
Run headless Linux Blender (`BLENDER_EXE=/opt/blender42/blender`) directly over SSH, or submit authenticated jobs through `tools/blender_remote_bridge/` (`server.py` + `blender_worker.py`) when bridging a GUI session.

```bash
BLENDER_EXE=/opt/blender42/blender /opt/blender42/blender -b --factory-startup \
    --python scripts/<short>/v01/build.py -- --out renders/<short>/v01
```

---

## 3. Mandatory Pre-Render Guardrails & Numeric QA Gates

### Step A — Fast Pre-Render Guardrails (`scripts/ricks_guardrails.py`)
Run inside `build.py` right before rendering (or CLI `--blend`) to catch defects in milliseconds:

```python
import ricks_guardrails as gr

report = gr.audit_scene(
    scene,
    rigs=[hero],
    subjects=[hero],
    frames=[1, 30, 60, 90],
    expect_deep_focus=True,
    allow_back_view=(),
)
print(gr.format_report(report))
assert report["pass"], "Fix all guardrail errors before GPU rendering!"
```

CLI verification modes:
```powershell
# Inside Blender (audit saved .blend):
blender -b --factory-startup --python scripts/ricks_guardrails.py -- --blend renders/<short>/v01/scene.blend --frames 1,30,60

# Pure-Python host check (zero Blender needed — verify closed/talk upper-face pixel lock):
python scripts/ricks_guardrails.py --check-expr-pair art/talk_closed.png art/talk_open.png
```

`audit_scene(...)` enforces:
1. **Head proportion (`head_ratio`):** `0.98 <= H/W <= 1.12` (bans squashed ovals).
2. **9:16 frustum safe margin (`frustum_clipping`):** all subject bounds inside `[0.04, 0.96]` NDC and in front of lens.
3. **Limb stretch (`limb_stretch`):** arms & legs `<= 1.25×` rest length, zero collapsed joints.
4. **Camera facing (`facing_camera`):** `dot(forward_xy, to_cam_xy) >= 0.15` unless listed in `allow_back_view`.
5. **Viewport/render parity (`viewport_render_parity`):** collections, objects, modifiers, and subsurf levels match between viewport and render.
6. **EEVEE contract & triangle budget (`eevee_contract`, `triangle_budget`):** `BLENDER_EEVEE_NEXT`, `use_raytracing=False`, `1080×1920 @ 100%`, `30 fps`, `use_dof=False` (when `expect_deep_focus=True`), evaluated visible tris `< 150,000`.

### Step B — Post-Stills / Post-Preview Numeric Gates (`scripts/ricks_metrics_gate.py` & `short_qa.py`)

```powershell
python scripts/ricks_metrics_gate.py --edge-density renders/<short>/v01/calibration
python scripts/ricks_metrics_gate.py --cam-velocity renders/<short>/v01/preview.mp4 renders/<short>/v01/cuts.json
python scripts/ricks_metrics_gate.py --word-sync scripts/<short>/v01/master_plan.json
python scripts/short_qa.py renders/<short>/v01/final.mp4 renders/<short>/v01/qa renders/<short>/v01/shots.json
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,sample_aspect_ratio,r_frame_rate,nb_frames -of json renders/<short>/v01/final.mp4
ffmpeg -nostdin -v error -xerror -i renders/<short>/v01/final.mp4 -f null -
```

- **Edge density:** Normalized Sobel `>= 0.10` at 640 px long edge; require mean `>= 0.14`, min `>= 0.088`.
- **Camera velocity:** Smooth native motion `<= 55 px/frame` excluding declared cuts (`cuts.json`), zero unmeasured non-cut hops.
- **Word sync:** `faster-whisper` centisecond `master_plan.json` binding named nouns & actions to visible events within `±0.10 s` (`>= 96%` coverage) and a character face inside the opening `2.00 s` hook.

---

## 4. Measured Film Grammar & Directing Laws

1. **Wide Immersive Lens:** Default `26–28 mm` on Blender's `36 mm` vertical sensor (`~65.5–71.5°` vertical FOV) placed close to actors for strong diorama parallax. Reserve `50–55 mm` for tight macro prop inserts.
2. **Kinetic Pacing & Beat Drift:** Stage `2.0–3.5 s` visual beats. Never leave a static pose or flat hold longer than `3.0 s` without a major action, prop beat, `0.5–0.8 s` macro insert, or `>= 25°` angle cut. Keep beats alive with `ricks_camera.beat_drift(...)` (`2–6 px/f`) and settle cleanly (`0.5–0.8 s`) only on punchlines.
3. **Six-Stage Action Without Overshoot:** **Notice → Wind-up → Strike → Hit → Settle → STILL** using smooth S-curves. Expressions snap on 1 frame with `CONSTANT` keyframes. Disable involuntary blinks during dialogue.
4. **Physical Action & Eye-Line in the First Second:** Show a clear weight shift and eyes tracking the hero prop within `0.0–1.1 s` (verify muted).
5. **Vary the Camera Axis:** Limit straight front-on zooms to `3 s`. Alternate eye-level mediums, `25–30°` three-quarter angles, `0.5–0.8 s` tight macro inserts, and crane/push reveals. Give every cut a story or action cue.
6. **Complete Prop Actions Against Dark Space:** Show pinch/pickup, readable airborne arc against a darker backdrop, explicit contact frame, and a 5–6 frame catch/landing hold before cutting. For eating/mouth gags, open mouth 2–3 frames before contact.
7. **Anchor Seated Leans & Diegetic Clearance:** Plant hips on the seat, pitch chest forward `12–15°`, keep `>= 10%` projected ink clearance around signs/labels/gauges, and route flying particles outside the face zone during payoffs.
8. **Modular Long-Short Architecture (`> 15 s`):** Split into `10–15 s` versioned `.blend` parts on a shared 30 fps integer timeline, render native `1080 × 1920`, concatenate video-only streams, and mux one continuous master narration + SFX track.

---

## 5. Character Construction (Official Mascot vs. Custom Stick-Hybrid)

### A. Official Main Character (`assets/mascot/`)
- Always use `mascot_api.load_mascot(collection)` — crimson ribbed beanie, snow-white marshmallow head (`1.00–1.05` H/W), yellow hoodie (`arm_style="hoodie"|"stick"`), charcoal pants (`bottom_style="pajamas"|"shorts"`), 12 story expressions, 6 lip-sync visemes (`hero.auto_lipsync(...)`), 7 swappable hands, zero-slip prop sockets (`hero.attach_prop`), 18 studio animations in `anim_library.py`, `< 35k` tris. See [`assets/mascot/MASCOT_SKILL.md`](assets/mascot/MASCOT_SKILL.md).

### B. Custom Stick-Hybrid Characters (`scripts/ricks_v2_kit.py`)
1. **Head:** 48-segment 3D ellipsoid using `head_radii=kit.ROUND_HEAD` or `kit.UPRIGHT_HEAD` (`0.98 <= H/W <= 1.12`), seated snug on the pill torso with zero neck gap.
2. **Torso:** Smooth high-subdivision pill capsule (`h ≈ 0.46 m`) carrying crisp 2D UV-mapped costume art (never puffy sculpted 3D sleeves unless using Official Mascot).
3. **Stick Limbs & Hands:** Matte jet-black (`#0A0A0E`) Bezier curve tubes (`r = 0.015–0.018 m`) with clean rounded stick tips (`~1.1×` arm radius) and small foot ticks (`~0.06 m`). Measure standing legs with `rig.measure_leg_lengths()` and pass `leg_lengths=` when seating/bending so knees fit cleanly without stretching.
4. **Hair, Hoods & Ink:** Offset hair caps `+0.008 m` outside head sphere (Subsurf 2 in both viewport and render). Use `#040407` distance-compensated backface-culled inverted hulls (`~2.5–3.5 px` on actors, `#0B0A10` `~1.0–1.5 px` on hero architecture/props).
5. **Opt-In Drawn Look & Camera Program:**
   - `scripts/ricks_drawn_look.py`: `drawn.apply_drawn_look(rig, col, shape="round", preset="paper_white")` + `drawn.update_ink(rig, camera, frame=f)` + `drawn.set_drawn_light(...)`.
   - `scripts/ricks_camera.py`: `rc.Shot`, `rc.CameraProgram`, `rc.beat_drift`, `rc.handoff`, `rc.lead`, `rc.damped`, `rc.parallax_reveal`, `rc.matched_distance`.
   - Smoke check: `python tests/blender_optin_smoke.py`.

---

## 6. Production & Self-Audit Workflow

1. **Build & Guardrail Pass:** Build and save a versioned `.blend` (`scripts/<short>/v01/build.py`), run `ricks_guardrails.audit_scene(...)`, reopen saved `.blend`, and render calibration stills (`lookdev_turnaround.png`, `calibration_8frames.png`).
2. **Benchmark (Local RTX 3050 or Modal L4):** Verify `< 150k` visible tris and viewport/render parity; on RTX 3050 also log `<= 1.8 s` p95, `<= 2.0 s` max, `<= 3.3 GiB` VRAM.
3. **Hook Approval:** Render the opening `10–15 s` preview (`540 × 960 @ 30 fps`) with synced audio/SFX and stop for motion approval before building Part 2+.
4. **Native Delivery:** When authorized, render native `1080 × 1920 @ 30 fps`, mux verbatim audio + balanced SFX (no subtitles unless requested), run `short_qa.py`, `ricks_metrics_gate.py`, `ffprobe`, and full `ffmpeg` null-decode check.
