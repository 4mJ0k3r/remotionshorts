---
name: blender-25d-story-video
description: Build and audit flat cel characters in rich 3D Blender 4.2 sets, with beat-driven acting, verified contacts, stable silhouettes and staged visual QA.
---

# Blender 2.5D Story Video — v3 visual contract

For Blender work, read the mandatory shared
[cel studio contract](animated-3d-story-video/references/cel-studio-contract.md)
before character, animation, camera or prop work. Its implementation recipes
and acceptance gates also apply to the Remotion engine skill.

The six laws in the shared contract's §7 are required for every build.

1. Give heads an independent camera-facing pivot using Damped Track or
   camera-relative Locked Track. Turn the face through grouped feature
   parallax within 20–25% of the head radius. Check side and high angles.
2. Set shoulders at the torso edges. Route desk-action elbows and curve
   controls outward, forward and above the surface by 3 cm plus ink radius.
   Keep raised elbows and hands outside 1.12 head radii and test the swept
   ribbon against furniture and head masks through the entire action.
3. Paint 15% clipped cool crescents on heads and shirts. Weight ink toward
   the shaded edge and step paint-only variation on fours. Use horizontal
   lid masks on solid pupils and anchor ground shadows at the soles.
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
- During authorized builds, checkpoint before/after major stages and before
  rendering; preserve previous versions. Never save during read-only audits.
  Avoid destructive BMesh round trips on evaluated/modifier meshes. Use
  supported evaluated-mesh APIs on copies with cleanup or configure modifiers.

## 3. Flat cel cast in a dimensional world

- Heads, torso, shorts, neck, limbs, hands and held cel props share a coherent
  flat drawing style. Ban volumetric block/cylinder shirts and thick shell
  rims. The old blanket **0.025 m Solidify recipe is withdrawn**. Prefer
  alpha-cut planes/ribbons with no visible sidewall. A separate shadow caster
  may ground a cel without thickening its visible edge.
- Use a stable organic cream head, variable dark marker boundary, interior
  cool shadow crescent, solid pupils and no white alpha halo. No continuously
  changing contour geometry or head scale. Apply four-frame ink variation
  only inside the fixed alpha boundary as specified in §7.3.
- Torso/neck/shorts form a unified masked cel assembly. Patterns stay inside
  final outer ink; limb roots disappear under sleeves/body. Composite shared
  seams once. Ban independent breathing transforms at connected joints.
- Draw a 15–20° three-quarter **pose** using asymmetric artwork and anchors;
  do not independently yaw a thick torso away from head and pants.
- Rounded curved limbs terminate at anatomical anchors and rounded hands.
  Solve outward elbows; no rigid L arms or unintended face crossings.
- Test emission-assisted cel color through final color management. Do not
  globally overexpose heads to hide lighting errors.
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
  useful story HUD requires an explicit design decision.

## 5. Mandatory acceptance gates

1. **Plan:** shot/audio beat map, physical anchors, prop dimensions, contact
   phases, occlusion order and authorized stages.
2. **Build checks:** Python syntax/API, hierarchy, driver, hinge, grip, seat
   and continuity checks. Never execute a build script just to inspect it.
3. **Pre-render visual gate:** use `blender.look` or the available equivalent
   active-camera viewport capture at shot start/mid/end, transition extremes,
   contact start/peak/release and worst-angle joints. Apply the six §7 gates
   to the actual camera and composite. Label viewport captures;
   they are not final renders. When authorized, inspect one calibration batch
   and native-size joint/contact crops. One consolidated correction pass;
   if a critical defect remains, report failure rather than waive it for a cap.
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
