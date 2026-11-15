# Animation style handoff

Use this panel when directing a new short in the `remotionshorts` house style. Read the current brief for story, audio, renderer, subtitles, and render scope. Use the references below to match how we stage and animate the story.

## Read order and authority

1. Read the current user brief and supplied references. Preserve its story,
   audio, output size, text preferences and stopping point.
2. Read [the general animation skill](animated-3d-story-video/SKILL.md) (v10)
   and [the shared cel contract](animated-3d-story-video/references/cel-studio-contract.md).
3. For Blender, also read [BLENDER_SKILL.md](BLENDER_SKILL.md) (v4) and the
   relevant [production recipes](animated-3d-story-video/references/production-recipes.md).
   For Remotion, use [the engine guide](src/engine/README.md) and its actual API.
4. Inspect available reference images/clips, then make the beat and contact plan.
   Descriptive rules alone do not establish that a new render matches visually.

The shared contract is the source of visual requirements; this panel supplies
direction and examples. Old project scripts are implementation references,
not authority over the current brief or proof that every helper is correct.

## What to match

| Reference | What to study |
| --- | --- |
| [Sendha V2 calibration sheet](renders/sendha_namak_science/sheet_v2.jpg) | Rough cream heads, marker ink, lit 3D mouth/clinic sets, a visibly held small prop, tucked-in bed staging, fear expressions, side-by-side tongue/barrier staging, and the centered swollen-mouth insert. These are stills, including the later shots. |
| [Sendha V2 partial movie](renders/sendha_namak_science/sendha_namak_v2_partial_540p.mp4) | Actual delivered motion: f1–1097, 36.567 seconds at 540×960, with Hindi narration. Study the pickup, short lick, chart reveal, phone warning, panic, mouth zoom and microscopic action. It does not include the later dining/safari/faint motion. |
| [Sendha source](scripts/sendha_namak_science/README.md) and [production recipes](animated-3d-story-video/references/production-recipes.md) | Reusable mechanics and local helper locations. Copy the principles and anchors; adapt story-specific coordinates, timings and dimensions. |

Local media is not guaranteed to be checked into GitHub. Verify availability;
provide the sheet and clip to a chat-only agent when it cannot access them.
Such an agent can propose shots/poses and critique supplied frames, but cannot
claim it rendered, verified a grip interval or watched inaccessible footage.

Historical washroom media was removed from this workspace. If supplied again,
study the door-peek at f440, low table reveal at f875, crane/reaction at f1130,
scream close-up at f1230 and consequence pullback at f1365. The alternate
ending's tension, cyan/gold spill, deadpan and empty-room payoff remain useful
directional ideas. Do not treat absent historical files as freshly inspected.

## The signature to preserve

Prioritize a readable joke, believable contact and the right emotion before
decorative FX. A clean held reaction can be stronger than another moving prop.
The characteristic look comes from these decisions working together:

- **Drawn cast:** stable large cream heads, warm uneven marker boundaries,
  restrained inner crescents, solid pupils, compact rounded shirts, connected
  neck/hips and curved matte limbs. Hand-drawn imperfection is fixed artwork,
  not continuous wobble or changing head scale.
- **Dimensional stage:** textured lit geometry, warm contour lines on major
  set/prop boundaries, foreground occlusion, grounded supports and gentle
  optical depth. Texture detail stays subordinate to the action.
- **Specific acting:** mischievous, worried, terrified and deadpan are different
  face/pose combinations. Fear does not reuse a happy speech mouth or blush.
  Listening bodies settle; only the intended eyes/mouth/secondary beat moves.
- **Clear prop action:** the hand visibly wraps a real gripping surface; a
  mouth prop starts in the open aperture; deposits remain after landing.
  Scale stays coherent. Use an insert when a small object needs emphasis.
- **Motivated coverage:** show the action, reveal the consequence, spend the
  close-up on the reaction. Mix viewpoints when useful; a repeated eye-level
  wall view with different props is not varied coverage.
- **Protected faces:** warm/cool world contrast and practical FX spill with
  bright cream and wardrobe colors. Keep bloom, dark mood and background
  ink from washing out or burying the face.

## Direct the short this way

1. **Cut to the joke.** Listen to the actual narration. Mark the word or pause that triggers each setup, reveal, reaction, escalation, and payoff. Assign each cut one visual job. Use a wide or two-shot for spatial relationships, an insert for an action the audience must see, and a close-up when the face is the joke. Let a deadpan beat sit long enough to land. On mute, the shot should still communicate who acts and what changes.
2. **Keep the cast drawn and the world dimensional.** Give the head a stable, slightly irregular cream silhouette, thick dark marker ink with directional pressure, a restrained crescent, and solid oval pupils. Match the shirt, shorts, and limbs to the same flat silhouette. Keep paint within the ink, bury limb joins under the body, and turn with painted profile or rear variants when needed. Give the set real depth with door jambs, desk edges, tiled planes, beveled fixtures, and objects that overlap. Carry the staging and palette from the reference into the new setting in ways that serve the story.
3. **Animate reactions as events.** Author a clear held pose, anticipation, a readable extreme, and a settle. Keep the root and head steady between beats. Use the actual voice envelope to drive mouth shapes for the active speaker and give the listener a deliberate expression or eye-line. Add a short shake, tilt, or squash only on a specific impact or reaction, with a defined end. A hand-drawn contour is a stable art decision. Check that it does not cause frame-to-frame head jitter.
4. **Make touch believable.** Name the support surface or grip before posing. Solve hands and feet against that target every frame of the contact interval. For a flush, show approach, first touch, button travel with the fingertip, and release. For a mug, anchor the grip to its handle. For a door peek, use the actual hinge and opening to stage the head inside the gap. Track the start, middle, and end of contact from the delivery camera. Check that recurring props keep their size across cuts.
5. **Move the camera for a reason.** Choose one move that supports the beat, such as a push on realization, a crane to reveal the subject, or a pullback to show the consequence. Frame the face and any story-critical hand or prop for the vertical crop. Use foreground edges and background planes for parallax. Focus on the active character plane and let farther set details soften gently. Judge sharpness, occlusion, and crop in the rendered image.
6. **Light for depth and keep the face readable.** Give the world a motivated directional key, quieter fill, and contact shadows. Favor a clear warm/cool split, such as warm desks against a cool tiled hall. Protect the cream head and wardrobe color in dark scenes. Tie bloom and colored spill to the effect and its timing, as in the gold ribbons and cyan orbs lighting the washroom. Use screen-space HUD only when it adds story information. Follow the brief for subtitles.

## Build and review

- Start with a beat table containing `time/frame | narration cue | visible action | pose and gaze | camera and focus | contact or FX`. Use it to catch repeated framing, missing inserts, and motion without a story cue before building.
- For Blender, read [BLENDER_SKILL.md](BLENDER_SKILL.md), the [cel studio contract](animated-3d-story-video/references/cel-studio-contract.md) and the source map in [production recipes](animated-3d-story-video/references/production-recipes.md). Prefer the current Sendha examples for surface grips, expressions and mouth attachments. Older washroom code remains useful for room construction and direction, but contains earlier rig choices; do not copy those over the current contract.
- For Remotion, read [SKILL.md](animated-3d-story-video/SKILL.md) and the [shared engine guide](src/engine/README.md). Reuse the engine’s character, camera, and player. Carry the same shot and acting decisions across renderers.
- Calibrate one representative still per cut, plus contact and peak-action frames. Inspect the sheet at phone size. Fix the largest visual problems, then watch short motion previews of the speaking, contact, and reaction beats. Stills can establish composition. They can’t establish stable holds, lip-sync, or whether a grip slides. Report the exact frames or intervals checked and any remaining problems. Follow the current brief’s render scope.

## Give the next agent a concrete handoff

Include the current brief/audio, one available contact sheet, an actual motion
excerpt, the source paths and the exact requested deliverable. Ask it to produce
a beat map and identify prop/support/mouth anchors before building. For each
important action it should be able to answer:

- What must read immediately in the vertical crop, even on mute?
- Where does the hand/foot/mouth prop actually attach, and is it within reach?
- Which emotion is visible at silence and at maximum speech opening?
- What persists after this beat, and what state must reset on the next cut?
- What was verified in images, in motion and numerically—and what remains unrendered?

These are reproducible directing and construction decisions, not a promise
that prose will make every agent's first render identical. Use the same visible
reference and review loop to close the remaining gap.
