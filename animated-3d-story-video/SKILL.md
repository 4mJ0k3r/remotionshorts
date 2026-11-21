---
name: animated-3d-story-video
description: Create and audit vertical shorts with expressive 3D-lit yet 2D-clean cel characters in detailed worlds, using the shared Remotion engine or the requested Blender workflow and staged visual QA.
---

# Animated 2.5D Story Video — v11

House style: crisp hand-inked cel silhouettes, dimensional painterly sets,
purposeful acting and verified contacts. Read the mandatory shared
[cel studio contract](references/cel-studio-contract.md) for recipes and gates.
For Blender requests also follow [BLENDER_SKILL.md](../BLENDER_SKILL.md);
do not substitute a Remotion scene.

Read [the style handoff](../ANIMATION_STYLE_HANDOFF.md) for direction and
reviewed examples. Blender implementation details live in
[production recipes](references/production-recipes.md); Remotion continues
to use `src/engine/`. Transfer the visual decisions between backends, not
their axis conventions, shader parameters or project-specific frame numbers.

Every backend must implement and verify the shared contract's six §7 laws.

1. Keep an independent head pivot and surface-conformed facial decals on
   smooth 3D heads. For the optional flat-card backend, use camera-facing
   heads and grouped painted turns within 20–25% of head radius.
2. Anchor shoulders at the outer contour. Route desk-action controls
   outward and forward with 3 cm tabletop clearance plus ribbon radius.
   For clear-face gestures, keep raised elbows and hands beyond 1.12 head
   radii. Test swept ink; deliberate mouth/temple contact uses named anchors
   and explicit foreground layers instead of this clearance rule.
3. Use received-light cel shadows, real hat-brim occlusion, stable bold ink
   and crisp pupils. The optional flat-card route uses 15% clipped crescents
   and paint-only variation; never animate contour noise.
4. Place tapered alpha-faded ribbons behind the face and resolve droplet
   attachment and release from temple sockets in the current pose.
5. Cast diagonal window shadows and ground furniture and feet. Animate
   directional key, fill, haze and vignette on motivated story beats.
6. Use screen graphics for timers, rules and scans. Reserve world text
   for scene-native writing such as chalk or handwritten notes.

The latest user instruction controls scope. Audit-only means read/extract/
document, without scene edits or renders. Calibration-only ends at the sheet.
Respect “no subtitles” in preview and final output. Never render, upload or
publish beyond the authorized stages.
Default to no subtitles unless requested. A zero-text brief also suppresses
HUD, scene lettering and baked texture labels; permitted story icons are
separate from lettering. If sheet plus video is already requested, the
sheet is a quality gate, not an extra permission gate. Respect a later stop.

## 1. Engine-first module architecture

For Remotion shorts, read `src/engine/README.md` and import the public API:

```ts
import {
  ShortPlayer, makeShotCam, Pool, Actor, Fx, makeChar, talkAt, lidAt,
  handWorldPos, drawKid, kit3d,
} from "../../engine";
```

New shorts in `src/videos/<name>/` author only:

| File | Responsibility |
|---|---|
| `story.ts` | Shots, cues, beats, camera/focus tracks, speakers and frame-addressable staging. |
| `build.ts` | Isolated sets from `kit3d`; return typed fixtures, grip/contact anchors and mechanical assemblies. |
| `world.ts` | Pool/Actor/Fx, lighting, visibility, event poses, IK, contact constraints and resource disposal. |
| `<Name>.tsx` | Stable world factory and thin `ShortPlayer` config; register in `src/Root.tsx`. |

Generate `audioEnv.ts` as data when audio exists:
`python scripts/audio-env.py public/<name>/audio.mp3 src/videos/<name>/audioEnv.ts TOTAL 30`.
Existing shorts may retain data-only `lights.ts`.

Do not copy 15 files or create local `toon.ts`, `cast.ts`, `pen.ts`, `ink.ts`,
`paint.ts`, `shade.ts`, `cardshade.ts`, `grade.ts` or `lensblur.ts`. Improve
shared engine capabilities when authorized. Legacy wrappers are migration
aids. Blender uses its own scene/rig pipeline, not these TypeScript modules.

`character.ts` owns wardrobes, expressions, IK and masked cel art; `pool.ts`
owns caches/placement; `kit3d` owns architecture/props; `shaders/` owns paint,
ink, cel shading and post. `ShortPlayer` owns six ordered post passes, 4× MSAA,
audio, top HUD and optional browser-shaped Hindi subtitles. Do not duplicate.

## 2. Character and motion contract

Blender defaults to smooth 48-segment heads, conformed decals, contoured
2.5D clothing/props and shadow-free inverted-hull ink #16121C/#292337
(1.5–3px at 360p). Separate dark sidewalls from outline thickness. Use
`../scripts/ricks_lookdev.py`; full requirements are in contract §8.
The following design-box/mask/cache details describe the existing Remotion
flat-card backend, not restrictions on Blender geometry.

- Engine design box: `600×1000`, `SU = 0.00216`, `PIV = 975`, soles `y = 952`,
  standing head `(300,235)`, `HEAD_R = 145`, cream `#fdfaf2`, ink `#351f22`,
  compact bean torso. Read the actual shoulder/hip anchors before changing
  modes. Three.js is Y-up; Blender Z-up requires an explicit conversion.
- Stable organic skull and pressure-varying boundary: head base width 16.5,
  garment/hair width 12.5 design units and thinner inner details.
  Four-frame ink variation stays inside fixed silhouette alpha. Ban
  contour motion, white halo and joint stretching. Preserve this backend
  geometry until a dimensional implementation is explicitly authorized.
- Use asymmetric painted three-quarter poses and curved outward IK. Sitting
  lowers the connected upper body; arms attach to its current shoulders.
  Place pelvis on the actual support and keep feet supported.
- Coordinate brows, lids, mouth and cheek treatment for each emotion. Lip-sync
  must preserve the intended expression, rather than replacing panic with a
  smile. Attach mouth props to the visible aperture's declared art anchor.
- Interpolate `0..1` during defined events, then hold the exact endpoint.
  Resting mode selection is valid; unplanned popping is not. Ban unconditional
  sine/noise/root/head/body wobble.
- Quantize draw-key parameters at 0.02 and talk at 0.2 for caching. Evaluate
  constraints against the same quantized pose or check resulting contact error.
  Use distance-tiered textures for close-ups.
- Gate `talkAt(f, AUDIO_ENV)` to the active speaker's dialogue range; use
  `lidAt` to drive the clipped eyelid aperture. Expressions must support speech without
  freezing mouths or bouncing the whole head on each envelope sample.

## 3. Contact, depth and camera

- **Rule A, portable props:** use attached cel props or 3D props with an
  explicit grip frame. Hand meets handle, not cup center/wrist. Correctly
  order front/back fingers around it.
- **Rule B, fixed fixtures:** keep the fixture's world anchor and legal
  mechanical travel. Inverse-project that anchor into the current actor card
  with the engine world-to-card helper; solve anchored shoulder/elbow/hand
  every contact frame. `handWorldPos` verifies contacts or locates partner
  targets. Never relocate a switch to chase a fist. Its historical default
  `depthOffset = -0.08` is not universal clearance; use explicit geometry-based
  contact surfaces/offsets.
- Helper availability is not proof of compliance. If `makeShotCam` forces
  drift for equal endpoints or a kit pin helper relocates a fixed fixture,
  use a frame-addressable wrapper or improve the shared implementation within
  authorized scope. Do not claim it already supports stable holds/fixed
  contacts. Old README held-frame targets/fixture-chasing examples are
  superseded by this contract; do not silently edit runtime during an audit.
- Isolate shot sets in groups. Preserve prop identity/dimensions across
  macro shots; compare visible area as well as scale under occlusion.
- Define a physical prop-size ledger and named surface grips before posing.
  Validate apparent finger contact as well as grip-frame arithmetic. Scale
  particles and accessories with their subject; an insert is preferable to
  making a hand-held object table-sized just to read it.
- Derive shot visibility and pose state from the requested frame. Reset
  temporary hidden limbs, mouth scales, prop ownership and FX on transitions;
  compare direct seeking with chronological evaluation.
- Use meaningful near/mid/far layers, detailed openings, natural silhouettes
  and local contrast. No bare box room or flat-wall staging by default.
  Dark/emergency scenes are valid if faces, ink and contacts remain readable.
- Ink world silhouettes and hard creases in the cast's warm near-black family,
  with thinner screen-space lines and depth falloff. Do not ink texture detail.
  Keep the lit render underneath and inspect a medium/close comparison when
  introducing or changing the line pass.
- Default engine FOV 38–50°. Pull back/reframe instead of fisheye. Check
  projected subject/prop bounds at action extremes.
- Camera moves serve beats; locked holds are valid. No per-frame motion floor,
  continuous noise, fixed angle-delta quota or compulsory cut interval.
- Optical focus is `dot(subject - camera, forward)`, positive and updated
  with camera/subject. Protect cel cards from world DOF. Test shader parameter
  direction: current engine CoC grows with `cInf`; do not blindly lower it
  assuming more blur. Use depth-aware separated passes when required.

## 4. Story and authorized build stages

Use supplied prompts/audio directly. For an open topic propose ideas and a
shot table before building. Match real sentence/beat boundaries; word-rate
estimates are provisional. Label spoken/internal/narrator cues. Do not add
subtitles because audio is missing. When requested, place captions at optical
center y=70.5%, using the actual Bold sans-serif font and proper Indic shaping.
Blender captions are burned after grading with FFmpeg; Remotion uses browser
HarfBuzz with an actual Bold Noto Sans Devanagari/Nirmala UI/Mangal font. HUD at
top 10% serves the story and avoids faces/hands/contact points.

1. **Build/check:** implement authorized changes; `npx tsc --noEmit` must
   exit 0 for TypeScript work. Check projections before expensive renders
   and consolidate framing corrections; honor explicit pass limits. Main subjects
   usually fit 15–85% bounds, secondary 5–95%; intentional close-up crops are
   valid. Never waive a clipped face/hand/story prop as a minor border graze.
2. **Calibration:** when authorized, batch all critical shot/transition/
   contact frames in one `bridge-stills.mjs` invocation, usually scale 0.5,
   subtitles off. Tile fresh `sheet_v1.jpg`; inspect native-size crops too.
   Consolidate corrections and confirm affected frames with a fresh filename.
   Inspect all six §7 gates at the relevant camera and pose extremes. Honor
   any explicit batch cap; otherwise continue focused fixes until critical
   gates clear. Batch caps never waive defects. Show the sheet at the user's
   stopping point; continue to already-authorized video after it passes.
3. **Video:** only when authorized, render the approved review once. Verify
   discrete GPU use and measured representative throughput, not a universal
   frames/min threshold. Isolate Blender/Chromium rendering. Review default
   is 0.5 scale; full resolution requires authorization.
4. **Delivery QA:** after final mux/patching run
   `python scripts/short_qa.py <movie> <qa_dir> <shots.json>`. Inspect generated
   sheets and actual movie at normal/slow speed. Check dimensions/frame count/
   audio and shared visual checklist. Expected cuts/holds may explain flags;
   preserve raw results and narrow reasons. Ban blanket exclusions or adding
   noise to lower held-frame counts. No universal held-frame/luma quotas.
   A clean pixel-stat report is not a visual pass; report remaining defects.
5. **Version/resume/stop:** freeze source and audio identity, isolate each
   version and resolution, and validate cached frames before reuse. On a
   partial-delivery request, stop the owned job and package only its complete
   contiguous prefix with matching audio. State duration/resolution, preserve
   resumable output, and do not resume until requested.

## 5. Reusable first-build baseline and gates

For Blender, start new scenes/versioned copies with
[`ricks_lookdev.py`](../scripts/ricks_lookdev.py), not a copied production
runtime. Follow [contract §8](references/cel-studio-contract.md#8-shared-blender-production-baseline)
and the [pipeline guide](../scripts/SHORTS_PIPELINE.md). This preserves the
V13 construction decisions; story-specific visual calibration is still required.

- Asset sanitation: <=512px prop / <=1024px hero textures; target <150k,
  hard <200k visible evaluated triangles; max one shadowed Sun. Record CC0
  or other permitted free-asset licenses; do not claim every free asset is CC0.
- Full-render gate on RTX 3050 4GB: 12 native frames, p95 <=1.8s,
  max <=2.0s, sampled VRAM <=3.3 GiB. Missing telemetry is unverified.
- Check every-frame camera clearance >=0.30m from sets/props, continuous
  junction transforms/lens/focus, projected framing and oblique projectile
  aspect; orient a moving projectile to its 3D velocity tangent.
- Generate intermediate-junction calibration plus hat-brim and hand/prop
  close-ups. Use explicit cuts and static/tracked shadow regions in
  `short_qa.py --strict`; keep raw diagnostics and review each flagged interval.
- Preserve supplied/locked audio. New narration target: dry compressed VO
  ~210–230 WPM, mix -14.3 LUFS / <=-3.0 dBTP / narrow LRA. When captions
  are requested: actual Bold white sans-serif, ~20px glyph height at 360p
  (~60–84px at 1080p), ~2px/6px black stroke, y=70.5%, <=1 frame sync;
  Blender burns them after grading with FFmpeg. Default remains no subtitles.
