---
name: animated-3d-story-video
description: Create and audit vertical shorts with flat expressive cel characters in detailed 3D worlds, using the shared Remotion engine or the requested Blender workflow and staged visual QA.
---

# Animated 2.5D Story Video — v9

House style: crisp hand-inked flat characters, dimensional painterly sets,
purposeful acting and verified contacts. Read the mandatory shared
[cel studio contract](references/cel-studio-contract.md) for recipes and gates.
For Blender requests also follow [BLENDER_SKILL.md](../BLENDER_SKILL.md);
do not substitute a Remotion scene.

Every backend must implement and verify the shared contract's six §7 laws.

1. Keep an independent camera-facing head pivot. Slide eyes, brows and
   mouth together by up to 20–25% of head radius for painted turns.
2. Anchor shoulders at the outer contour. Route desk-action controls
   outward and forward with 3 cm tabletop clearance plus ribbon radius.
   Keep raised elbows and hands beyond 1.12 head radii. Test swept ink.
3. Paint 15% clipped head/shirt crescents, use variable ink with paint-only
   four-frame variation and clip solid pupils with horizontal lid masks.
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

- Engine design box: `600×1000`, `SU = 0.00216`, `PIV = 975`, soles `y = 952`,
  standing head `(300,235)`, `HEAD_R = 145`, cream `#fdfaf2`, ink `#351f22`,
  compact bean torso. Read the actual shoulder/hip anchors before changing
  modes. Three.js is Y-up; Blender Z-up requires an explicit conversion.
- Stable organic skull and pressure-varying boundary: head base width 16.5,
  garment/hair width 12.5 design units and thinner inner details.
  Four-frame ink variation stays inside fixed silhouette alpha. Ban
  contour motion, shine dots, white halo, joint stretching and 3D shirts.
- Use asymmetric painted three-quarter poses and curved outward IK. Sitting
  lowers the connected upper body; arms attach to its current shoulders.
  Place pelvis on the actual support and keep feet supported.
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
- Use meaningful near/mid/far layers, detailed openings, natural silhouettes
  and local contrast. No bare box room or flat-wall staging by default.
  Dark/emergency scenes are valid if faces, ink and contacts remain readable.
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
subtitles because audio is missing. If enabled, one line at bottom 18% with
browser HarfBuzz and Noto Sans Devanagari/Nirmala UI/Mangal fallbacks. HUD at
top 10% serves the story and avoids faces/hands/contact points.

1. **Build/check:** implement authorized changes; `npx tsc --noEmit` must
   exit 0 for TypeScript work. At most two projection passes. Main subjects
   usually fit 15–85% bounds, secondary 5–95%; intentional close-up crops are
   valid. Never waive a clipped face/hand/story prop as a minor border graze.
2. **Calibration:** when authorized, batch all critical shot/transition/
   contact frames in one `bridge-stills.mjs` invocation, usually scale 0.5,
   subtitles off. Tile fresh `sheet_v1.jpg`; inspect native-size crops too.
   One consolidated fix pass, at most one confirmation batch with a fresh
   filename. Inspect all six §7 gates at the relevant camera and pose
   extremes. If a critical gate still fails, report it and stop before video.
   Batch caps never waive defects. Show the sheet at the user's stopping point.
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
