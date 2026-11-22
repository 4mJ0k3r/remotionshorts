# Shared Shorts pipeline

## Indoor cavern preset

For a new interior scene or versioned copy, call
`look.apply_lighting_preset(scene, 'INTERIOR_WARM_CAVERN')` after
`look.setup_scene(...)` and before adding story practical lights. This opt-in
preset replaces the outdoor sky with #1A2238 at strength 0.12, hides the
pipeline Sun rig, and installs restrained glow with **no foreground mist**.
It exposes warm stone/skin/crimson/teal/yellow palettes and a 7:1 starting
key/fill ratio through `look.INTERIOR_WARM_CAVERN`. Add motivated amber spots,
lanterns and candle lights, then calibrate the actual received cel shading.
The optional far-mist specification starts at 14 m and is disabled by default.
Existing outdoor setup behavior is unchanged; this call never migrates approved
scenes automatically. Render and GPU gates still apply.

This is the new-build baseline, not a migration script for approved projects.
The numerical contract is in `animated-3d-story-video/references/cel-studio-contract.md`
§8. Imports do nothing to Blender. Call the helpers from each new story builder;
do not copy the Slow Eddie runtime, absolute coordinates or 300-frame duration.
No library or prompt can guarantee artistic acceptance on the first render.

## Build a new scene or versioned copy

```python
import sys
sys.path.insert(0, str(repo_root / 'scripts'))
import ricks_lookdev as look
import shorts_preflight as gate

look.setup_scene(scene, actor_height=actor_height, frame_end=total_frames)
skin = look.clean_toon('Hero skin', 'skin')
copper = look.copper_metal('Copper')  # final V13 RT-off received-light tint
metal = look.metal('Buckle', '#E9C777', .6, .18)
look.configure_camera(camera, focus_empty, lens=50, fstop=2.8)
# Tag ALL horizon props, ink shells, clouds, smoke, wisps and streaks.
look.mark_role(ink_shell, 'ink')
look.mark_role(distant_mesa, 'horizon')
asset_report = gate.sanitize_assets(scene, imported_meshes, hero_objects=hero_sets)
assert asset_report['pass']
assert gate.validate_resources(scene)['pass']
```

Keep the approved rough-round character design. Smooth 48-segment heads and
conformed facial decals receive actual hat-brim shadows. Match contoured clothes,
continuous limbs and clean mesh joins. `clean_toon` exposes received-light Map
Range thresholds; calibrate them visually. `protect_lower_face` is an optional
normalized local receiver mask: derive its bounds from the current head, not
Eddie's old values. `ink_width(depth, lens)` computes distance-compensated hull
thickness (1.5–3px at 360x640); update it per frame and inspect native crops.
Dark sidewalls remain a separate shading surface. Preserve exact connected joints.

The installed shadow handler enforces explicit roles and common ink/cloud/FX
names in pipeline-enabled scenes. It does not clear other handlers. Imports
created later must be tagged immediately. Reinstall it in the saved scene's
bootstrap after reopening: module imports/handlers are not embedded in a blend
automatically. Save/reopen and compare direct-seek poses with chronological ones.
`setup_scene` replaces the visible lighting rig by hiding previous lights
(including the factory point light), preserving their data. Add motivated
practicals only afterward. Standalone `install_lights` refuses foreign visible
lights unless `replace_existing=True` is explicit.

`sanitize_assets` copies mesh/material/image data, caps and packs textures,
removes unlinked image nodes and decimates only explicit imported set assets.
It does not edit downloaded files. Tag actors `actor`; do not pass rigged actors
as imported set assets. Remove unused orphan image/material datablocks in the
working copy before final packaging, preserving runtime/fake-user dependencies.
No speculative download URLs or blanket CC0 claims: keep an asset license ledger.
Nested shader groups are copied and capped too. Resource validation blocks
render-only objects/collections or modifier detail absent from the pre-render
evaluation; align evaluation with the final render before trusting its count.

## Validate motion and prepare calibration

Story update is a stateless `update(frame)` callback. Use `ease5`,
`interpolate_distance` and `bake_channel` for LINEAR frame samples. Moving
projectiles use `align_to_velocity_tangent(projectile, position_at, frame, ...)`
with the actual local nose axis and local axial spin. Stationary arrival needs
an explicit fallback tangent. Check projected oblique aspect and grip separation
in the calibration crops; world alignment alone cannot establish framing.

```python
camera_report = gate.validate_camera_path(
    scene, update, obstacles=all_collision_meshes,
    subjects=[(hero, first_frame, last_frame)], cuts=actual_cut_frames)
# Save report; REVIEW/UNVERIFIED blocks full render until resolved.
# Speed diagnostics have per-story thresholds; do not blanket-exempt junctions.
```

Collision/cut frames passed to Blender helpers are ONE-based. Include all
porches/rails/barrels/facades and moving props. Intentional crops are documented
per shot, not checked as full-body subjects. Camera distance and center rays
do not prove a whole silhouette is unobstructed: inspect images and playback.

Copy `shorts_qa.example.json` into the NEW production and replace every interval
and ROI. All JSON indices are ZERO-based. `cuts` are destination indices; `[]`
means no cuts. `continuous_junctions` override all exemptions at those frames.
Legacy manifests without `cuts` retain old shot-boundary exemptions; new builds
must supply `cuts` explicitly. Do not copy example ROIs and claim verification.

```powershell
python scripts/calibration_sheet.py --meta <manifest.json> --frame-count <N> --output <new-plan.json> --plan-only --strict
```

Render `blender_frames` from that plan under the shared GPU lock, at calibration
scale 0.5 and additionally native resolution for brim/grip crops. Point the sheet
generator at the native files (a common scale is required per invocation):

```powershell
python scripts/calibration_sheet.py --meta <manifest.json> --frame-count <N> --frames-dir <new-calibration-dir> --pattern "frame_%04d.png" --output <new-sheet.png> --strict
```

The plan includes start/mid/end, action/extreme frames, +/-1/2 junction neighbors,
quarter/mid transition samples and specified close-ups. Missing source images
fail; missing brim/grip semantic crops are UNVERIFIED (strict mode blocks).
The sheet labels both JSON index and one-based Blender frame. Review crops,
not just shrunk thumbnails. For existing movies use `--video` instead.

## Native performance and final delivery

Claim `.blender_gpu.lock` exclusively with project/PID/owner before any background
Blender, including smoke. Wait for other owners and release only after your child
exits. Never render Chromium concurrently. Under the owned lock, call:

```python
report = gate.benchmark(scene, twelve_distinct_spread_frames, fresh_benchmark_dir, update)
assert report['status'] == 'PASS'
```

The benchmark keeps the warmup separate, records native first-pass wall times
including PNG write, and samples whole-board VRAM every ~0.2s. It reports
linearly interpolated p95 and the maximum separately.
Limits: p95 <=1.8s, max <=2.0s, sampled board memory <=3.3 GiB. No telemetry
means failure to verify. Brief spikes may escape sampling. Keep monitoring in
the full-render launcher; this helper only monitors its own benchmark. Reduce
resource/sample costs only after fresh visual and native timing gates.

After the authorized full render, grade, then burn requested captions with the
actual Bold font and mux the supplied audio. Preserve locks on existing audio
and captions. Measure final loudness/true peak; listen to word timing. Caption
optical glyph size/position and sync require actual frame/timestamp evidence.

```powershell
python scripts/short_qa.py <final.mp4> <fresh-qa-dir> <manifest.json> --strict
```

Reports include relative and absolute non-cut MAD spikes, frozen actions,
black/white frames and opening shadow stability. Static shadow regions need
`registration: "locked-camera"`; moving shots need `regions_by_frame` mapping
every index to tracked normalized ROIs. Compare only static lighting/acting
holds. Missing coverage is UNVERIFIED. Explicit caption MAD exclusions retain
raw frame differences. Strict mode exits 2 for REVIEW/UNVERIFIED; legacy CLI
still produces reports without forcing old projects to adopt the new schema.
MAD is a review flag, not proof of a collision. Keep reports and narrow written
resolutions for intentional motion. Never hide failures by relaxing thresholds.

## Construction smoke check (no production render)

```powershell
blender -b --factory-startup --python scripts/ricks_lookdev.py -- --smoke
```

Expected marker: `RICKS_SMOKE_OK`. This creates no movie or saved blend and
does not claim benchmark, visual, audio or caption acceptance.
