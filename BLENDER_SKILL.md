---
name: blender-25d-story-video
description: Build and audit 3D-lit yet 2D-clean cel characters in rich Blender 4.2 sets, with beat-driven acting, verified contacts, stable silhouettes and staged visual QA.
---

# Blender 2.5D Story Video — v5 visual contract

For Blender work, read the mandatory shared
[cel studio contract](animated-3d-story-video/references/cel-studio-contract.md)
before character, animation, camera or prop work. Its implementation recipes
and acceptance gates also apply to the Remotion engine skill.

For direction and reviewed examples, read
[ANIMATION_STYLE_HANDOFF.md](ANIMATION_STYLE_HANDOFF.md). For Blender-specific
construction and production mechanics, use
[production recipes](animated-3d-story-video/references/production-recipes.md).
The shared contract owns visual requirements; the recipes provide starting
values and implementation examples, not a new story or compulsory prop list.

The six laws in the shared contract's §7 are required for every build.

1. Give heads an independent pose pivot and conformed facial decals. Smooth
   3D heads retain authored contours and real hat-brim shadows. The optional
   flat-card route uses camera-facing tracking and grouped feature parallax
   within 20–25% of head radius. Check side and high angles.
2. Set shoulders at the torso edges. Route desk-action elbows and curve
   controls outward, forward and above the surface by 3 cm plus ink radius.
   For gestures that should clear the face, keep raised elbows and hands
   outside 1.12 head radii and test the swept ribbon against furniture/head
   masks. Intentional mouth/temple contact uses explicit contact anchors and
   foreground layers while protecting the eyes and other unrelated features.
3. Use light-driven cool shadows and warm cream faces, including actual
   hat-brim occlusion. For flat-card projects only, use 15% clipped crescents.
   Keep ink stable and pupils crisp; ground shadows at the soles.
4. Use tapered alpha-blended ribbons behind the cast and attach sweat and
   tears to temple sockets until the authored release.
5. Cast diagonal window-bar shadows with a warm Sun or Spot, ground each
   support point and cue changes to key, fill, haze and vignette by beat.
   Use the EEVEE 4.2 grounding recipe in §7.5 for the active GPU profile.
6. Composite timers, rule callouts and scans as screen graphics. Keep
   natural chalk and handwritten notes as scene artwork.

## 1. Scope and source of truth

- The latest user instruction controls the permitted stages. Audit-only
  permits reading code/scene metadata and extracting existing movie frames,
  **not** saving a changed scene or rendering new stills/video.
- Calibration-only ends with the inspected contact sheet. Do not launch a
  video render until that stage is authorized.
- A request for calibration followed by a full render already authorizes
  both stages. Inspect and correct the sheet, then continue without asking
  for the same permission again. A later stop/partial-delivery instruction
  overrides that plan. Documentation-only work does not resume rendering.
- Record the exact input `.blend`, scripts, audio and delivered movie. Audit
  the delivered movie including patched ranges; the master alone does not
  prove what was delivered.
- Verify reference claims against the supplied reference. State unavailable
  intervals and distinguish visible style from inferred implementation.
  Never claim an exact rig, shader, timing or HUD from a still.

## 2. Hardware and crash safety

- Default output: vertical 1080×1920, 30 fps; respect requested review size.
  Budget for RTX 3050 Laptop / 4 GB VRAM unless detected otherwise.
- Blender 4.2: `BLENDER_EEVEE_NEXT`, ray tracing off on this VRAM budget,
  simplify on, subdivision cap 2. Prefer procedural world materials and modest
  image assets over large PBR texture sets.
- Verify active renderer/device and representative frame time. NVENC proves
  GPU **encoding**, not GPU frame rendering. Estimate a range from measured
  frames at the same scene/settings; never promise an exact render duration.
- Never run headless Chromium rendering alongside Blender rendering.
- Before any background Blender process, follow the shared
  `.blender_gpu.lock` convention: claim exclusively with project/PID/owner,
  wait for the current owner, and release only your own claim after its
  child exits. Reuse the owner-checked launcher pattern in the recipes.
  Never clear another project's lock or kill all Blender processes.
- Use named version folders, a frozen render source and audio/source hashes.
  Resume only matching, validated frames. A preview-sized master is still
  preview-sized; report its actual dimensions and completed frame range.
- During authorized builds, checkpoint before/after major stages and before
  rendering; preserve previous versions. Never save during read-only audits.
  Avoid destructive BMesh round trips on evaluated/modifier meshes. Use
  supported evaluated-mesh APIs on copies with cleanup or configure modifiers.

## 3. 3D-lit yet 2D-clean cel cast

- Default to smooth 48-segment 3D heads with an authored rough-round contour,
  conformed 2D eyes/brows/mouth decals, and actual hat-brim cast shadows.
  Preserve approved character proportions; no automatic spherical redesign,
  random head noise, geometry boil, or white alpha fringe.
- Use smooth 2.5D contoured torsos, flush beveled vest panels, hats and props;
  smooth continuous curved limbs, not stacked/ribbed capsules. Connect neck,
  shoulders and hips through poses. Patterns stay within garment boundaries.
  The blanket **0.025 m Solidify recipe remains withdrawn**.
- Use dark inverted-hull ink #16121C/#292337, distance/lens compensated and
  clamped to about 1.5–3px at 360p. Continuous dark sidewall shading is a
  separate surface/lighting treatment, never an inflated outline. Ink shells
  never cast shadows. Retain real receiving/casting surfaces beneath them.
- Keep upper forehead under the hat cool (#C4C8EA) while cheeks/jaw stay
  warm (#FDF5EF). Calibrate the received-light ramp and actual brim occlusion,
  not a global blue chin crescent. §7.3 covers the optional flat-card route.
- Flat alpha-card/ribbon assemblies remain valid for existing projects or
  explicit briefs. Their overlap/mask and billboard recipes are conditional,
  not a ban on 3D heads or contoured shirts. Three-quarter 3D poses turn the
  connected rig and keep decals attached to the evaluated face surface.
- Rounded curved limbs terminate at anatomical anchors and rounded hands.
  Solve outward elbows; no rigid L arms or unintended face crossings.
- Test emission-assisted cel color through final color management. Do not
  globally overexpose heads to hide lighting errors.
- Use a coordinated expression tuple: brows, lids, pupils, mouth and cheek
  treatment. Panic must not inherit a smiling speech sprite or cute blush.
  Declare the visible mouth aperture's art-space anchor before attaching
  a tongue, food or instrument; texture center alone is not that anchor.
- Environments/fixtures remain detailed 3D: recessed openings, connected
  hardware, painterly materials, practical light, grounded shadows and depth.
  Cut away camera-facing walls when needed; use organic natural silhouettes.

## 4. Acting, contacts, optics and coverage

- Stable listening holds are required. Ban unconditional sine breathing,
  idle root/head sway, perpetual scale drivers and continuous camera noise.
  Use finite events: anticipation, action, optional overshoot, exact settle.
  Blinks and syllable mouths may move during body holds.
- Classify audio as spoken dialogue, narration or internal thought. Assign
  speaker/time ranges; drive only that speaker from the real envelope. Never
  freeze a speaking shot's mouth to preserve its smile or animate everyone
  from the entire narration track.
- Fixed fixtures drive hand targets; hands never drag switches across the
  set. Portable props use grip anchors and front/back finger occlusion.
  Validate position and normal throughout contact, not just selected peaks.
- Seated hips meet the actual seat. Door leaf, panels, rosette, spindle and
  lever form a mechanical hierarchy with a hinge pivot. Peeking heads stay
  inside the actual aperture. A right latch does not imply a right hinge.
- Focus tracks the intended subject plane. World blur must not soften cel
  ink; use separate depth-aware cel/world passes when one DOF pass cannot
  satisfy both. Preserve foreground occlusion and ground shadows.
- Use distinct motivated views/pushes/pans/cuts. Locked cameras and reaction
  holds are valid. Never add drift/shake to defeat frozen-frame metrics.
  ~1.7–2.5 s is an optional energetic pacing guide, not a compulsory interval.
- Respect text preferences. “No subtitles” applies to final packaging too;
  default to no subtitles unless requested. HUD and scene lettering follow
  the brief. “Zero text” also excludes baked image labels and overlays;
  story symbols are allowed only when the brief permits them.
- Evaluate every shot from declared state: visibility, scale, expression,
  prop ownership, materials and FX. A hidden bed-shot leg must be restored
  in the following standing shot. Check boundary frames and out-of-order
  seeking, not only a chronological sheet.
- Keep silhouette/crease ink on selected set meshes and props in the same
  warm ink family as the cast. Preserve lit textures, shadows and DOF;
  do not outline texture/grout detail. See the shared contract's set-ink recipe.

## 5. Mandatory acceptance gates

1. **Plan:** shot/audio beat map, physical anchors, prop dimensions, contact
   phases, occlusion order and authorized stages.
2. **Build checks:** Python syntax/API, hierarchy, driver, hinge, grip, seat
   and continuity checks. Never execute a build script just to inspect it.
3. **Pre-render visual gate:** use `blender.look` or the available equivalent
   active-camera viewport capture at shot start/mid/end, transition extremes,
   contact start/peak/release and worst-angle joints. Apply the six §7 gates
   to the actual camera and composite. Label viewport captures;
   they are not final renders. When authorized, inspect a calibration batch
   and native-size joint/contact crops. Consolidate corrections, then confirm
   affected shots. Honor any user-imposed batch cap; without one, continue
   focused corrections until critical defects clear. Never waive a defect.
4. **Video, only when authorized:** render/assemble the approved source once.
   Record scene version, frame mapping and splice ranges. Verify the whole
   final movie against the approved source, including both sides of patches.
5. **Post-render:** after final audio/mux/patching run
   `python scripts/short_qa.py <movie> <qa_dir> <shots.json>`. Verify dimensions,
   frame count, duration, audio alignment and image diagnostics; watch every
   contact/action span at normal and slow speed. Apply the shared checklist.
   Planned holds are legitimate; missing movement during an action is not.
   No held-frame percentage quota, universal luma quota or blanket exclusions.
6. **Report honestly:** list inspected artifacts, defects and limits. A clean
   script or seven exact press peaks cannot certify visual quality between
   those peaks. No instruction guarantees first-pass perfection.
7. **Stop and partial delivery:** on “give whatever is rendered,” stop only
   this production's controller/worker, verify its children exited, and
   release its owned lock. Validate the contiguous complete frame prefix,
   mux precisely that duration with the matching audio prefix, decode-check
   it, and deliver it promptly. Preserve resumable frames. Never call a
   partial delivery a finished full movie or silently restart it afterward.

## 6. Shared baseline for new original Shorts

Use [scripts/ricks_lookdev.py](scripts/ricks_lookdev.py) on a new scene or
versioned working copy; do not paste a previous story's coordinates/runtime.
Use [shorts_preflight.py](scripts/shorts_preflight.py) and the mandatory
[contract §8](animated-3d-story-video/references/cel-studio-contract.md#8-shared-blender-production-baseline).
The [pipeline guide](scripts/SHORTS_PIPELINE.md) gives executable calls and
the QA/calibration manifest. Importing a library alone does not run a gate.

- Baseline: Standard/None, exposure 0, gamma 1; EEVEE Next, RT off, 32 samples,
  shadow pool 512, 2 rays/6 steps, bokeh jitter and motion blur off. Use the
  gradient/mist/glow and 4:1 rig in the shared module. Keep one shadowed Sun.
- Sanitize imported CC0/free assets before calibration: props <=512px,
  hero sets <=1024px; target <150k visible evaluated triangles, hard <200k.
  Record license/source. Exclude actors from destructive decimation.
- Before full render: 12 distinct native-frame GPU benchmark, p95 <=1.8s,
  max <=2.0s, sampled board VRAM <=3.3 GiB; unknown VRAM is unverified.
  Tune samples/resources only with fresh calibration and measurements.
- Check >=0.30m camera clearance on every frame, explicit cut destinations,
  continuous transform/lens/focus junctions, projected bounds, projectile
  oblique aspect and nose aligned to 3D velocity. Inspect pixel evidence too.
- Use intermediate-junction calibration and brim/grip close-ups, then
  `short_qa.py --strict` with declared cuts, continuous junctions and static
  or tracked shadow ROIs. A missing ROI is unverified, not a pass.
- Preserve supplied audio. For newly produced narration/mixes target dry
  compressed VO ~210–230 WPM, mix -14.3 LUFS, <=-3.0 dBTP and narrow LRA.
  Captions remain opt-in: actual Bold white sans-serif, post-grade FFmpeg
  burn, ~20px glyph height at 360p (~60–84px at 1080p), ~2px/6px black
  stroke, optical center y=70.5%, <=1 frame sync. See contract §8 for limits.
