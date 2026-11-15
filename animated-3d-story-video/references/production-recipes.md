# Blender production recipes

Read with [the shared contract](cel-studio-contract.md). These are reusable
construction patterns learned from local productions, not a compulsory story,
cast, camera move or set of world dimensions. The current brief wins.

## 1. Start with the visual action, then assign geometry

Before building, write `cue/frame range | what changes | audience must see |
contact/support | camera/focus | prop/FX lifetime`. Each shot needs a clear
setup, action or reaction. An insert buys readability for a small physical
prop; enlarging every prop changes the joke and breaks the world scale.

Declare a compact size ledger: character height, head radius, shoulder and
hip anchors, limb reach, seat/table surfaces, complete prop bounds and named
grips. In a human-scale example, an 11 cm fruit stays hand-held; a microscopic
crystal close-up uses an explicitly different magnification. Those dimensions
are examples, not requirements for another story. Check grain-to-fruit and
hat-to-tongue ratios independently of the camera zoom.

Prefer unit-scale rig and grip roots with dimensions authored into geometry
or their child meshes. Otherwise account for the full inherited scale when
measuring contacts, normals and assembly bounds. Do not trust an empty root's
`dimensions` to measure its children.

## 2. Cel artwork and protected shading

House starting palette: cream `#fdfaf2`; warm marker `#351f22` or the approved
project's `#2b1810`; dark brown hair with restrained warm streaks. Use the
stable harmonic contour in the contract, pressure-weighted ink, an inner
15% cool crescent, solid pupils and layered expressions. Keep garment paint
inside its final boundary. Clear transparent art with neighboring dark RGB,
not white, and verify the final alpha blend at native delivery size.

For 1024-square head artwork, about 15–17 px base head ink is a useful start;
scale it with the art, not frame width. Separate the skull/hair base from the
face group so gaze/profile variants never erase paint with a visible rectangle.
Record anchors in the same coordinates used to draw the features.

The recent Blender starting profile is 74% Emission at strength 0.96 plus
26% Principled, roughness 1 and specular IOR level 0. Treat these as calibration
values through AgX, not a universal material law. Connect image color to both
branches and image alpha to a transparent mix. Verify cream, wardrobe and
ink in bright and dark shots; do not fix a hotspot by overexposing the scene.
Do not stack Three.js gain/shadow constants onto a Blender recipe by analogy.

For EEVEE review, 16 samples, ray tracing off, simplify subdivision cap 2 and
modest assets fit the local RTX 3050 4 GB profile. Inspect the installed RNA:
Blender 4.2.23 exposes `eevee.fast_gi_method='AMBIENT_OCCLUSION_ONLY'`, not the
often-pasted `use_fast_gi` property. Verify available settings rather than
silently skipping errors or assuming another Blender version's API.

## 3. Full head billboards and connected bodies

Inspect the card mesh's actual axes first. For local XY artwork with +Z front
and +Y up, an unparented head uses:

```python
from mathutils import Quaternion
cam_q = camera.matrix_world.to_quaternion()
head.rotation_mode = 'QUATERNION'
head.rotation_quaternion = cam_q @ Quaternion((0, 0, 1), roll_radians)
```

No extra 90-degree conversion belongs on an already-XY card. An XZ card needs
a verified mesh-axis conversion. For a rigid parent, convert the desired
world quaternion through the parent's inverse world quaternion. Keep
nonuniformly scaled parents out of billboard hierarchies.

Check transformed front normals and camera-up/roll at high and off-axis
views, plus the rendered head proportions. Point-at-camera alone does not
guarantee parallel image planes across a wide frame. A sideways faint uses
camera-plane roll plus a supported fall trajectory, never head pitch that
turns the circle edge-on. Solve connected torso, pelvis, limbs and accessories
from the same posed anchors. Partial torso pitch compensation is optional;
it must pass neck/hip continuity at the actual camera.

Rounded hips, when requested, belong under the hem with an anatomical
vertical axis. Measure visible leg length after the hem/pelvis overlap, and
solve shoes on the support plane. For walking, derive travel from actual root
motion and pin the stance foot; a root translation plus rigid legs is skating.

## 4. Portable grips that look held

Create a semantic surface frame: handle grip, bottle barrel, fruit underside,
pen shaft. Include position and orientation, not just an object origin.
For unit-scale roots, with all matrices evaluated at the same frame:

```python
prop.matrix_world = hand_grip_world @ prop_grip_local.inverted()
contact_world = prop.matrix_world @ prop_grip_local
```

Check the resulting surface frame against the actual solved hand. If the
solver clamps reach, target-to-target equality proves nothing about the hand.
Route the elbow outward, move the actor/seat/prop into legal reach and solve
again. Inspect fingertip overlap: a rear palm and two or three front mitten
fingers can make a small round barrel read as firmly held. Keep fingers on
the portable assembly or derive them from its evaluated grip transform.
Do not attach a jar center to a wrist and call the arithmetic error a grip test.

Sample pickup, approach, hold, shake, release and set-down, including between
extremes. Preserve ownership through pans/cuts unless a visible transfer or
set-down explains the change. Source and deposited particles share a declared
lifetime; separate falling particles from persistent residues/damage.

## 5. Mouth anchors and readable prop staging

Define the visible aperture center in image coordinates; the texture rectangle
may have transparent padding or an off-center drawing. For top-origin pixel
coordinates on an XY card:

```python
from mathutils import Vector
local_anchor = Vector(((pixel_x / image_w - .5) * card_w,
                       (.5 - pixel_y / image_h) * card_h,
                       front_depth))
mouth_world = face_group.matrix_world @ local_anchor
```

Include painted-turn offsets in `face_group`. Position the tongue/tool base
inside a sufficiently open mouth at this anchor. Use one continuous rounded
ribbon/mesh with a centerline, explicit width and tip socket. Size the open
aperture to admit the base; accessories follow the tip. Check the rendered
first emergence and the retracted, extended, turned and swollen states.
Do not build a tongue as separated balls or substitute nearby smoke puffs.

For a tongue plus shield/spray gag, reserve separate screen regions for face,
tongue/hat and barrier. Check head/prop silhouettes through the entire slam
trajectory, not only the resting frame. A barrier can arrive outside the head
and settle beside/below the cheek. Use actual world clearance and projected
bounds; resolve contradictory coordinate/scale instructions by preserving the
visible action and face readability, documenting a material adjustment.

## 6. Shot state, persistence and reopened-scene checks

Use pure frame-addressable shot state. Establish each actor's visible parts,
mouth scale, expression, materials, props and FX for that shot. Reset manual
per-object hiding when leaving a bed/cutaway shot. Restore nested visibility
after a parent set changes, or invalidate its cached descendants. Check
boundary frames and seeking a later frame directly from a fresh scene.

In Blender, dynamically selected expression materials/images need real users
or `use_fake_user=True` so they survive saving. Pack images or declare their
dependencies. Reload the saved source and explicitly bootstrap its runtime
in the render worker; do not assume editor callbacks persist in a new process.
Make frame-handler failures abort that owned worker. Blender can otherwise
log a handler exception yet successfully save an image of an old pose.

## 7. Calibration, render and interruption

Use shot and contact extremes in one calibration batch when practical. Inspect
the contact sheet and native crops, then action strips/short previews as
authorized. Check visibly held props, emotions, cloth/support, deposits and
the first frame after a hidden-body shot. A tiny numerical grip error is
complementary evidence, not a substitute for the image.

Use the shared exclusive GPU lock before any `blender -b` work. Record owner,
project and controller PID. Wait for other jobs; release only the owned lock
after children exit. Log the actual renderer after a rendered frame. Measure
representative shots; one simple macro frame is not a full-film ETA.

Freeze the approved blend/runtime/audio identity and separate frame folders
by version and actual resolution. Check contiguous PNGs for readable data and
correct size before resuming. Chunked `render(animation=True)` avoids repeated
still-render setup; chunk size is a resource choice, not a style requirement.
Do not reuse old frames after an unrecorded source change. Record patch ranges
and verify both splice edges if an authorized patch is used.

On a stop/partial request: stop the owned controller before it starts another
chunk, stop its owned worker, verify exit, release the owned lock, validate the
complete prefix, mux precisely `completed_frames / fps` with matching audio,
probe and decode-check the result. Preserve frames for a requested resume.
Report actual duration and resolution. Run full delivery QA only when there
is a full delivery; partial prefix validation is not a whole-film visual pass.

## 8. Source examples, with limits

| Local source | Reuse/study |
| --- | --- |
| [Stage helpers](../../scripts/washroom_experiment/sets.py) | Reusable meshes, materials, fixture geometry and lights; avoid copying unrelated story labels. |
| [Card helpers](../../scripts/inside_brain_dog/build_inside_brain_dog.py) | Actual XY/+Z card construction and cel material scaffolding; calibrate material values for the new brief. |
| [Set ink](../../scripts/studio/set_ink.py) | Selected geometry boundaries, screen-space weight and depth falloff over a lit world. |
| [Foot stepper](../../scripts/elevator_leak/stepper.py) | Deterministic stance-foot pinning and active stepping; adapt to the new character/support geometry. |
| [Sendha assets](../../scripts/sendha_namak_science/assets.py) | Stable head art, coordinated expressions and centered mouth variants. |
| [Sendha runtime](../../scripts/sendha_namak_science/runtime.py) | Camera-plane heads, surface grips, cloth-shot visibility reset and mouth/tip attachments. |
| [Sendha launcher](../../scripts/sendha_namak_science/run.py) | Owner-checked lock, versioned source identity, chunked render and mux. Adapt project paths, frame count and delivery settings. |
| [Partial delivery](../../scripts/sendha_namak_science/deliver_partial.py) | Validated contiguous prefix and duration-matched audio packaging after the owned job stops. |

These sources contain project-specific choices and are not compliance proofs.
Read the implementation before reusing it. The current Sendha V2 movie is a
1,097-frame / 36.567-second 540×960 partial; later shots have calibration
stills, not a delivered motion review. Never describe that partial as a full
master or assume local render media exists in a GitHub-only checkout.
