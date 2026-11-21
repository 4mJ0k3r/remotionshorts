# Shared cel studio contract

Current Blender baseline: 3D-lit yet 2D-clean cel geometry. §8 supersedes
historical flat-only construction and old production-specific render recipes.

Mandatory for Blender and Remotion skills. This specifies construction and
acceptance, not another creator's private rig. User scope/style wins. Never
execute render recipes during analysis-only work. Use the requested backend.

Use [production recipes](production-recipes.md) for Blender implementation
details and [the style handoff](../../ANIMATION_STYLE_HANDOFF.md) for reviewed
examples. Numeric examples are calibration starting points; preserve the
current brief's anatomy, story, text policy, resolution and permitted stages.

## 1. One coherent cel silhouette: 3D-lit yet 2D-clean

Screen appearance takes precedence over construction dimensionality: faces,
hands, arms and legs read as flat 2D graphic shapes. 3D geometry may support
contact, occlusion and subtle cast shadows, but no glossy mitten hands,
sculpted facial features or rounded tube highlights. Keep face fill simple,
hands/limbs dark and matte, and outlines bold. Hat-brim bands may remain
restrained; do not let wrap shading turn the face into a visibly modeled ball.

Default Blender construction uses smooth 48-segment 3D heads, conformed 2D
facial decals, real hat-brim receiving/casting surfaces, and smooth 2.5D
contoured torsos, vests, hats and props. Preserve the approved rough-round
head design and proportions. No generic sphere redesign or random head noise.
Use #16121C/#292337 inverted-hull ink, clamped around 1.5–3px at 360p through
camera distance/lens changes. Keep dark sidewall shading separate from ink
thickness. All ink shells are non-shadow-casting. §8 is the Blender baseline.

**Banned:** primitive box/cylinder clothing without a designed silhouette,
lumpy/ribbed capsule limbs, thick shell rims, z-fighting, unmasked patterns,
protruding neck/shorts corners, white matte fringes and geometry boil.

The raster/mask recipes below apply to the **optional flat-card backend**
(existing Remotion and explicitly flat Blender briefs). They are not a ban
on 3D geometry. Curved 3D clothing instead shares connected anatomical anchors,
clean mesh joins and smoothly wrapped received light.

Author one stable rest contour per asset. Rough-circle recipe:

```python
from math import sin, cos, pi
def head_contours(cx, cy, rx, ry, count=256, w0=16.5):
    outer, inner = [], []
    for i in range(count):
        a = 2*pi*i/count
        r = 1 + .022*sin(2*a+.6) - .015*cos(3*a-.8) + .008*sin(5*a+1.9)
        w = w0 * max(.25, 1 + .52*cos(a-2.35)
                          + .22*sin(3*a+1.1) + .14*cos(5*a-.7))
        outer.append((cx+(rx*r+w/2)*cos(a), cy+(ry*r+w/2)*sin(a)))
        inner.append((cx+(rx*r-w/2)*cos(a), cy+(ry*r-w/2)*sin(a)))
    return outer, inner
```

Fill outer ink then inner cream. No frame-dependent phase. Scale outline
units with the design box, not output pixels. For arbitrary torso/cap/hair
contours use normals or distance-field insets, **not** a radial inset from
the image center (fails on concavities). Engine garment base width is 12.5.
Low-amplitude static contour irregularity is allowed.

Mask recipe: all inputs have identical supersampled canvas dimensions;
region masks are L-mode; paint layers are RGBA. Neck/shirt/shorts regions
overlap at joins. `body_inner_mask` is the inward offset of their **union**,
not a union of separately inset pieces (which creates dark seam cracks).

```python
from PIL import Image, ImageChops, ImageFilter
body_mask = ImageChops.lighter(neck_mask,
    ImageChops.lighter(shirt_mask, shorts_mask))
cel = Image.new('RGBA', body_mask.size, (53,31,34,0))
for paint, region in [(neck_paint, neck_mask),
                       (shirt_paint, shirt_mask), (shorts_paint, shorts_mask)]:
    clipped = paint.copy()
    clipped.putalpha(ImageChops.multiply(paint.getchannel('A'),
        ImageChops.multiply(region, body_inner_mask)))
    cel = Image.alpha_composite(cel, clipped)
ink_band = ImageChops.subtract(body_mask, body_inner_mask)
ink = Image.new('RGBA', body_mask.size, '#351f22'); ink.putalpha(ink_band)
cel = Image.alpha_composite(cel, ink)
# For the head crescent, use its inner cream mask:
shifted = Image.new('L', head_inner_mask.size, 0)
shifted.paste(head_inner_mask, (12,-10))  # non-wrapping; scale to design size
crescent = ImageChops.subtract(head_inner_mask, shifted)
crescent = crescent.filter(ImageFilter.GaussianBlur(3))
crescent = ImageChops.multiply(crescent, head_inner_mask)
```

For flat cards only, apply a soft bottom-left cool grey-blue multiply crescent to the cream
head and the shirt before final ink and facial features. Reuse the recipe
with the respective fill mask and multiply strength `0.15 * crescent / 255`.
Check it through the final grade. For 3D heads use real upper-forehead brim
occlusion instead; keep lower cheeks/jaw warm, not blue-grey.
Keep patterns 0.5–1 outline width inside the boundary, not heavier
than the outline. Edge-dilate transparent RGB from neighboring ink/color,
never white; match renderer alpha mode to avoid halos.

Prefer one composited body cel. Articulated pieces must share art coordinates
and deformation root, overlap inside joints under sleeves/body by at least
1–2 outline widths at maximum bend, mask their union and draw the external
silhouette once. No outlined hidden sockets or shirt-only stretching away
from pants. Layer depth offsets must be invisible in the worst camera view;
there is no universal centimeter offset.

Use a connected, anatomically rounded pelvis, aligned under the torso hem;
no horizontal hip platter. Contoured 2.5D clothing and 3D heads are the default
Blender route. Check visible leg proportions after clothing and occlusion.

Limbs use smooth continuous curved sweeps, or flat ribbons for the card route,
with rounded caps and subtle static pressure variation. Two-bone IK shares
shoulder/hip anchors, outward elbow poles and clamped reach. Round the elbow,
not a rigid right angle. No ring seams or stacked capsules. Contour variation
never moves endpoints. Resolve front/back grips and protect faces.

## 2. Finite beat events and exact holds

**Banned:** free-running `sin(frame*...)` head/body/scale drivers, perpetual
camera NOISE, every-four-frame whole-silhouette swaps, visible particle-reset
teleports and body poses changing with every audio-envelope sample.
Legitimate locomotion/water cycles are phase-driven only while active, with
defined start/stop and contacts; they are not idle filler.

Events declare start, anticipation, extreme, settle and held interval.
6–10 frames is a useful starting point for a snappy transition; tune to the
real beat. Optional overshoot must never break grip/support constraints.

```python
def ease_out(u): return 1-(1-u)**3
def event_progress(f, start, anticipate, extreme, settled):
    assert start < anticipate < extreme < settled
    if f <= start: return 0.0
    if f < anticipate:
        return -.06*ease_out((f-start)/(anticipate-start))
    if f < extreme:
        return -.06+1.14*ease_out((f-anticipate)/(extreme-anticipate))
    if f < settled:
        return 1.08-.08*ease_out((f-extreme)/(settled-extreme))
    return 1.0
```

Use on compatible pose blends, not constrained grips. Bake finite samples
with LINEAR interpolation if needed. After settle, key identical endpoints
and use CONSTANT interpolation over the hold; remove competing drivers and
modifiers. Avoid Bezier tangents overshooting contact. Head/torso/pants settle
together. Only eyes/mouth/intentional secondary effects move during listening.
Head accents are finite vocal/story beats, not continuous envelope shaking.
Use the four-frame ink treatment in §7. Its texture-only noise preserves
the contour geometry, joints, contact endpoints and actor transforms.

Blender 4.2 keyframing pattern, on a clean event-control channel during an
authorized animation build (the pose solver consumes `poseP`, including its
small anticipation/overshoot range):

```python
def bake_pose_event(root, start, anticipate, extreme, settled, hold_end):
    assert hold_end > settled
    # This channel must have no competing driver/modifier or prior keys.
    for f in range(start, settled+1):
        root['poseP'] = event_progress(f, start, anticipate, extreme, settled)
        root.keyframe_insert(data_path='["poseP"]', frame=f)
    root['poseP'] = 1.0
    root.keyframe_insert(data_path='["poseP"]', frame=hold_end)
    fc = next(c for c in root.animation_data.action.fcurves
              if c.data_path == '["poseP"]')
    for k in fc.keyframe_points:
        if start <= k.co.x <= hold_end:
            k.interpolation = 'CONSTANT' if k.co.x >= settled else 'LINEAR'
```

Use normalized real audio envelopes, speech gating/noise floor, short attack/
release smoothing and 0.2 mouth quantization. Gate by speaker/spoken cue.
Narration/internal thought may keep a held mouth only when labeled that way.
Smile/teeth expressions need speaking variants. Blinks are deterministic
with varied intervals; do not synchronize all actors or move the skull.

Expressions are coordinated sets of brows, lid aperture, gaze, mouth and
cheek treatment. Select a fear-compatible speaking mouth for fear; remove
incompatible smile/blush layers. Validate the full expression at the actual
small-screen size, including silent and speaking extremes.

Each frame must establish its shot state independently. Temporary blanket
occlusion, hidden legs, mouth scale, accessory scale, material tint and prop
ownership cannot leak into the next shot. Evaluate cut−1/cut/cut+1 and compare
direct seeks with sequential playback. Cache visibility only if nested groups
and manual per-object overrides invalidate that cache correctly.

Brows/lids/pupils/teeth change on beats. Emotional tint affects cream without
tinting ink/eyes. Event-gated sweat/tears/steam follow arcs, fade to zero before
reset and preserve readability. No mandatory hop at every expression swap.

## 3. Semantic grips and full-interval contact

Name grip/contact frames with position **and orientation**. Contact states:
approach → touch → press/hold → release → retract. A fixed fixture owns its
world anchor and legal travel. IK hands follow it despite body/camera motion.

```python
# mathutils matrices evaluated at the SAME frame:
target_world = fixture.matrix_world @ contact_local
target_in_card = card.matrix_world.inverted() @ target_world
# Solve current shoulder -> target_in_card. contact_local accounts for the
# surface normal/finger pad, not a guessed wrist-Z offset.

# Portable prop with named grip matrix:
prop.matrix_world = hand_grip_world @ prop_grip_local.inverted()
```

Place `prop_grip_local` on the actual handle or barrel surface, including its
orientation and inherited scale. Zero distance between the hand and an arbitrary
prop origin can still produce a visibly floating prop. Check the finger pads,
front/back wrap, surface normals and their projected overlap in rendered crops.
If IK clamps an unreachable target, audit the resulting hand rather than the
requested target and move the actor/support into reach.

If unreachable (or outside the optional flat-card plane), reposition actor/shot or stage a
coherent arm layer; do not teleport the fixture. Image X/Y alone is not
contact: verify depth, normal, fingertip and readable occlusion. Front
fingers cover the handle and rear fingers pass behind it. Parent cup-center
to wrist is not a grip. Cel props use the same recipe in design coordinates.

Check every contact frame, including between peaks, worst camera angles and
motion-blur subframes if enabled. Choose screen tolerance from delivery size
(target <=1 output pixel) and corresponding world distance; report both.
Check full contact points, not only Z. Finger and moving button share travel,
remain connected, then release in the proper order.

For sitting, locate the pelvis support patch on the actual seat surface.
Solve thighs, knees and floor-supported feet from it, not an arbitrary root
height. Correctly occlude far/near legs around the seat. A ground shadow does
not repair hovering hips.

For a bed pose, derive the supported pelvis and recline from the mattress,
headboard and pillows. Drape real cloth geometry or an equivalent depth-aware
layer over the lap/lower torso; hiding legs alone is not a tucked-in pose.
Retain correct contact underneath and restore hidden parts on the next shot.

Mouth attachments use the visible aperture's art/UV anchor, transformed through
the evaluated face group and head billboard. Widen the mouth sprite to admit
the prop before extending it. Inspect first emergence, peaks and retraction;
no tongue/tool may originate at a cheek or detached sprite center. Use a
continuous rounded tongue silhouette, with accessories attached to its tip.

## 4. Depth, identity and door mechanics

Declare near/far order for every overlapping body/prop region. Check world
clearance and camera-projected occlusion. A rim may occlude a supported pelvis,
not slice across an unrelated torso. No fixed +/-8 cm offset replaces
geometry checks. Use segmented/depth-aware cel passes when necessary;
topmost character overlays without world occlusion are not a shortcut.

Maintain a prop identity/dimensions table across cuts and macro sets. Compare
world size, projected silhouette and **visible fraction**. Rising opaque
water or a low rim angle can make a fixed-size object look shrunken. Diagnose
scale vs occlusion vs camera before scaling. Floating objects follow support
surfaces when intended; sinking needs a visible story event. Water stays
inside its cavity and never bleeds across isolated sets.

Record dimensions of the entire prop assembly, including parent scale,
leaves/lids/handles and recurring copies. Distinguish physical scale from an
explicitly magnified macro set. Choose grain, droplet and accessory size relative
to the subject: grains appropriate in a macro insert can bury a normal fruit.
Persistent deposits, damage, flags and stains need lifetimes spanning their
story interval; do not clear them with a general per-frame FX reset. Transition
between falling and deposited states without visible reset teleports.

```python
# Blender Z-up: build hinge-local, leaf extends toward the latch.
door_leaf.parent = hinge
door_leaf.location = (width/2, 0, height/2)
panels.parent = hinge
handle_assembly.parent = hinge  # rosette + spindle + lever below assembly
# Rotate hinge.rotation_euler.z; lever depresses around its own spindle.
```

Set parent inverses/local transforms explicitly. Preserve world transforms
when reparenting existing objects. Verify hinge/leaf/panels/rosette/lever
move together; mounting plate/spindle touch the leaf with no gap. Inspect
complete hardware in wide views and background close-ups, not only angles.

Derive the visible aperture from leaf sweep/jambs. Peeking face/hand stay
inside it and behind correct door/frame edges, never outside a jamb into
the wall. Check whole head silhouette, not center only. Determine hinge/latch
from construction; a right latch does not imply a right hinge. Sample
closed/mid/open states and maintain assembly transforms throughout.

## 5. Rich world, sharp cels, purposeful coverage

Use near/mid/far depth, recessed openings, connected fixtures, architectural
trim and painterly surface variation, soft grounded shadows and practical
lights. Avoid bare box rooms, unmotivated flat-wall staging, uniform white/
beige wash or lost dark ink. Mood shifts are valid; local contrast must read.

Carry the warm character ink into selected set/prop silhouettes, borders and
hard creases. At 1080-wide delivery, roughly 3–4 px outer set lines and half-width
inner creases are useful starting points, subordinate to the cast. Preserve
screen-space weight across medium/close views, fade distant lines, and exclude
texture normals, brick mortar and grout. Keep textured lighting, contact shadows,
optical depth and restrained bloom underneath. A geometry edge pass must not
turn every surface texture into a wireframe.

Stage the whole camera frustum inside finished architecture or an authored
cutaway/backdrop. Verify high angles and frame corners against actual wall and
ceiling extents. A universal wall height or a sky color does not prove enclosure.
For a face plus barrier/prop action, allocate separate readable screen regions
and inspect the swept approach as well as the final pose. If literal coordinates
collide, resolve units/space and reframe or adjust legal staging; do not knowingly
cover the face to match an inconsistent coordinate list.

Optical focus is `dot(subject_position-camera_position, camera_forward)`.
Track active face/contact plane, not back wall/old look target. Test geometry
1.5–3 m behind subject for soft separation at delivery size. An initial
3–6 output-pixel background blur can be useful; tune per shot while preserving
sharp cel ink. Inspect depth halos. Blender F-stop and shader `cInf` differ:
verify actual response. Separate world/cel passes when required, preserving
foreground world occlusion and character shadows.

Plan coverage around reveals/reactions: locked holds, eased pushes, short
zoom punches, motivated pans. Finite impact impulses settle to stable views.
No continuous noise/drift or universal cut interval/angle delta. Optional
science HUD uses coherent viewfinder/scan/leader hierarchy, readable units
and anchored labels. Never attribute X-rays/blueprints to a reference that
doesn't show them. Disabled subtitles stay disabled; technical labels are a
separate deliberate design choice, not a caption workaround.

## 6. Acceptance evidence, not success-by-metric

Before an authorized full render, inspect active-camera `blender.look` or
equivalent viewport captures, then authorized calibration stills. Batch all
shots/action/contact extremes; inspect native crops too. A still cannot
validate motion/contact. Register to actor-local space when assessing body
hold stability so a planned camera move isn't mistaken for wobble.

Required visual checklist:

1. Stable rough cream head, variable dark ink, no halo, cool received shadow,
   solid readable pupils/features.
2. Smooth contoured body (or authored flat-card body), clipped pattern and
   seamless neck/shoulder/shorts at extremes; no thick rims/protruding corners.
3. Connected curved limbs and anchors, supported pelvis/feet, stable holds,
   finite reactions, no perpetual drivers.
4. Fixture contact aligns in 3D and screen space for entire touch/hold,
   including between peaks; correct finger/handle occlusion.
5. Portable prop grip orientation, finger wrap, ownership and dimensions
   remain continuous; no cup glued to forearm.
6. Visible mass persists across cuts; water/foreground doesn't erase story
   props; no clipping or set bleed.
7. Complete door hardware/aperture passes closed/mid/open and background
   views; peeking faces stay inside opening with correct occlusion.
8. Rich world depth, soft background optics, sharp saturated cels and local
   contrast; no unintended dim/blown/featureless scenes.
9. Speaker mouths follow syllables; expressions read; camera/FX settle;
   text obeys preferences and avoids faces/hands/contact.

Apply all six §7 gates as part of calibration and final movie review.

After final mux/patches, run existing `short_qa.py` and inspect the delivered
movie, not just stats/master scene. Check count/resolution/duration/audio.
Distinguish intentional holds/fades/cuts/flashes from freezes/corruption/pops.
Preserve raw flags and narrow documented exceptions; never change thresholds,
add noise/dither or blanket-mask scenes just to pass. Review all contact spans
in playback. Peak-only assertions/pixel stats cannot certify visual quality.
Partial rerenders need recorded frame/time mapping and both splice edges
checked. Never silently ship an old bake outside patched ranges after the
master changes.

Separate observed facts, code evidence, inferred causes and unverified claims.
If a time/batch cap is reached with a critical failure, stop before the next
stage and report it. Evidence gates prevent declaring known defects complete;
instructions alone cannot guarantee first-pass perfection.

Save/reopen is part of acceptance: preserve dynamically selected materials,
images and runtime dependencies, bootstrap the saved scene, and inspect that
reopened source. Blender may discard unreferenced expression materials, and
frame-handler exceptions may be logged while rendering a stale pose. Make the
worker fail on those errors rather than treating a completed PNG as success.
Frozen source/audio identity must match resumed frames. Keep version/resolution
folders separate. A contact sheet can cover an ending that has never been
rendered in motion; label that distinction and the delivered frame range.

## 7. Six mandatory visual laws and recipes

### 7.1 Independent head pivots and attached facial features

For 3D cel heads, use a dedicated pose pivot, 48-segment smooth mesh and
surface-conformed facial decals that stay attached during turns/nods. Hats
and facial features follow that pivot; the brim remains a real shadow caster.
Camera-relative orientation is an art choice, not mandatory billboarding of a
3D face. Inspect side/high views for decal clipping and readable pupils.

For the optional flat-card route only, use a dedicated head billboard pivot. Take its position from the evaluated
neck anchor and solve its orientation from the active camera independently
of torso pitch, yaw and scale. Use a unit-scale pivot with local XY art,
+Z facing out and +Y up. In Blender use `DAMPED_TRACK` with `TRACK_Z`.
`LOCKED_TRACK` with `TRACK_Z` and `LOCK_Y` is suitable for yaw-only coverage
when the locked axis is camera-relative and the projected contour passes.
For high or off-axis views use a full camera-facing solution. With a tracking
constraint, aim at a helper located at the head position plus the camera's
world +Z direction. Align the pivot's roll basis to camera up. This keeps
the art parallel to the image plane even near the frame edge. Update the
helper and roll basis after camera evaluation and on every camera cut.
Use the camera world quaternion as the unconstrained rotation basis so the
shortest-arc correction keeps the intended up direction. An existing XZ
card needs a fixed mesh-to-pivot axis conversion.

In a frame-addressable renderer, the equivalent full billboard is
`headWorldRotation = cameraWorldRotation`, with local +Z facing out.
If parented under a rigid transform, convert that rotation to local space
using the inverse parent world quaternion. Keep the billboard outside any
nonuniformly scaled hierarchy. Retain intentional roll in a child art layer.
For an exact overhead insert, stage hands and prop independently and compose
the face out of frame when appropriate.

Animate an authored turn scalar in `[-1, 1]`. Shift the grouped eyes, brows
and mouth by `turn * radius * 0.22` in head art coordinates. Keep the maximum
travel within 20–25% of the head radius and clip the group to its safe face
mask. Preserve independent eye gaze and syllable motion inside that group.
Pose turns must preserve skull dimensions and the neck attachment.
Check projected contour proportions against the front view at matching
screen scale on side aisles, high angles and orbit extremes.

### 7.2 Furniture and head clearance

Place shoulders at the outer torso contours with enough under-sleeve overlap
to hide the root seam. Derive desk top height from the actual fixture.
In actor-facing Blender coordinates, route seated desk-action elbows and
tabletop-span curve controls outward along ±X and forward along −Y.
Their centers must clear `desk_top_z + 0.03 m` plus the ribbon half-width.
Convert these directions through the actor basis for rotated desks and use
the backend's up axis. Shoulder anchors remain anatomical. Hands at a
deliberate desk grip follow their authored surface anchors.

For `raise_hand`, project the shoulder, curve and hand into current head
art coordinates. Route the elbow and hand outside `1.12 * head_radius`,
allowing extra room for ink width and the mitten silhouette. Keep the
upper arm under the chin until it clears the side of the head. Test the
whole visible swept ribbon against the skull/hair mask and its width against
the actual furniture geometry. Use tabletop, apron, leg and chair clearance
volumes, including where a curve bows between controls. If a reach fails,
adjust the elbow route or rest pose and solve again with the same anchors.
Approve approach, contact, release and transitions at every evaluated
frame, with subframe checks when motion blur is enabled.

This clearance rule is for gestures that must stay outside the face. An
intentional temple clutch, eating action or examination instead uses a named
surface/aperture contact and explicit front/back layers. Keep unrelated eyes,
brows and the readable action clear; do not make the intended contact float
outside the head just to satisfy a generic radius threshold.

### 7.3 Received-light shadows, stable ink and eyelid masks

For 3D cel heads use Diffuse -> Shader to RGB -> luminance -> Map Range ->
EASE ramp -> Emission 1.0. Tune received-light thresholds against the actual
hat/brim crop. Upper 20–25% forehead under the brim receives #C4C8EA with an
approximately 1–2px transition at 360p; cheeks/jaw stay warm #FDF5EF. A local
receiver mask can protect the lower face while retaining real upper-zone
occlusion; derive it from the current head, never old character coordinates.
Do not invert the band onto the chin. Shirt/vest surfaces receive smooth
warm/cool wrap shading; continuous sidewalls do not inflate the outline.

For flat cards only, use the clipped §1 crescent at 15% cool grey-blue with
a soft bottom-left edge. Both routes ground actual supporting soles. Fixed
contour pressure can weight the shaded ink edge; never animate head noise.

For the flat-card route, optionally apply subtle deterministic noise to a paint-only ink weight or texture
channel sampled on fours. In Blender use Noise followed by Stepped
Interpolation with step size 4, or bake the same channel with constant
four-frame samples. Keep the perturbation on the interior edge of the ink
band or in its texture and within half a delivery pixel at the closest
shot. Lock the outer alpha, vertices, camera and head/body transforms.
Hold the ink sample during exact story holds and gate changes to authored
acting beats. In a stateless renderer, use the shot-relative index
`floor((frame - shotStart) / 4)` and freeze it for the authored hold.

Draw solid dark oval pupils through a horizontal lid aperture in the same
face group. Intersect the oval mask with `top <= y <= bottom`, where the
animated lids close the aperture to zero. Use Canvas clipping, a raster
alpha intersection, or equivalent shader masking. A closed blink can use
one stroke exactly at the closed aperture. Ban floating parentheses and
baked curved eye strokes that remain visible when the pupil closes.
Check open, half-lidded, squint and closed states at native size.

### 7.4 Tapered ribbons and attached droplets

Build flat, depth-aware alpha-blended ribbons. Use Blender 4.2's
`surface_render_method = "BLENDED"` and verify translucent draw order
against the opaque depth or holdout pass. For normalized height
`t` in `[0, 1]`, offset the centerline by
`amplitude * sin(frequency * t - speed * eventAge + seed)` and use
`halfWidth = maxWidth * sin(pi * t)`. Start at about 40% transparency
(alpha 0.60), multiply by a top fade and the event's fade-in/out envelope.
Keep the tips pointed and transparent. Place the source behind or below
the torso and depth-occlude it with the cast and furniture. Check the
projected face mask throughout camera motion and route or mask away any
overlap. Reset a ribbon cycle only at zero alpha.

Author sweat and tear sockets on the upper temple in head-art space,
inside or overlapping the ink edge. Resolve them through the evaluated
billboard transform every frame. Slide attached drops along a cheek path
in head-art coordinates. For a beat-driven release, start the arc at the
current attached point with matching initial position and motion. Fade
and retire the drop at the end. Verify birth, attachment and release from
side and high angles. Use teardrop silhouettes with soft taper.

### 7.5 Directional light, grounding and mood

Build a warm shadow-casting key through real window openings and mullions.
In Blender use the §8 4:1 warm/cool rig: key strength 2.2, angular diameter
4°, shadows enabled, and unshadowed cool fill strength 0.55. These are starting
values for scene calibration, not an exemption from the received-shadow gate.

```python
from math import radians

sun.data.energy = 2.2
sun.data.angle = radians(4)
sun.data.use_shadow = True
sun.data.use_shadow_jitter = False
sun.data.shadow_maximum_resolution = 0.025
# Sun light travels along local -Z. direction points into the room.
sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
```

Angle it across the room to create diagonal bars on at least
the story surface and floor. Adjust softness/exposure against the actual
image so the bars read. A Spot uses calibrated power, cone size and source
radius in place of Sun units. Keep fill subordinate to the directional key.
In Three.js use the equivalent shadowed directional or spot source with
shadow maps sized and biased for the visible receivers.

Enable ambient occlusion or raytraced contacts when the renderer and
measured budget support them. In EEVEE 4.2 use the Fast GI ambient
occlusion option where available. On the ray-tracing-off profile use
shadow maps and receiver-local contact discs or baked AO at desk legs,
chair legs and shoe soles. Anchor each patch on its actual support surface.
Carry grounding in the world pass when sharp cels are composited separately.
Verify contact, no float, and no double shadow in the final composite.
EEVEE 4.2 replaced the old per-light Contact Shadows switch with virtual
shadow maps. Use the version's render method and shadow controls.
[Blender 4.2 migration notes](https://developer.blender.org/docs/release_notes/4.2/eevee_migration/)

Author a beat table for key color/intensity, world/fill color, haze and
edge vignette. Ease between motivated looks such as warm daylight,
blue-violet warning, green dispersion and rose-gold payoff. Stabilize
each look after the beat. Protect cream faces and legible ink through
each change. Apply the vignette to the graded image before screen UI.

### 7.6 Screen-space status and diegetic writing

Status, timers, warnings, rule callouts and technical scans belong in
screen space. Ban wooden wall planks and 3D label boxes for these cues.
Use a timed, shaped UI overlay or full-frame graphic for a countdown,
satellite view, thermal view, X-ray or dispersion diagram. Composite it
after world depth, grade and vignette. Keep one source of timing, maintain
safe areas and check legibility at delivery size. Keep subtitles independently
controlled by the user's preference. Reserve world text for diegetic writing
such as chalk on an existing blackboard or handwriting on a real note.


## 8. Shared Blender production baseline

New original Blender Shorts must call `scripts/ricks_lookdev.py` on a new
scene or a versioned working copy. Import is inert. Never modify an approved
source/render to adopt new defaults. Existing flat-card productions remain
valid; these rules govern new builds unless the current brief overrides them.
Use `scripts/SHORTS_PIPELINE.md` for calls, metadata and evidence artifacts.

### 8.1 Look development and anti-flicker

- Blender 4.2 EEVEE Next; Standard/None; exposure 0.0, gamma 1.0; RT off;
  32 render samples; shadow pool 512, 2 rays, 6 steps; bokeh jitter OFF,
  motion blur OFF; Simplify ON, subdivision cap 2. A measured lower sample
  count is allowed only after repeat calibration and a passing native benchmark.
- Vertical 36mm camera sensor. Derive distance from actor height, lens and
  desired screen fraction. Lock focal length per continuous shot. Use quintic
  ease5 and LINEAR per-frame baked samples to avoid Bezier overshoot.
- Visible world gradient: #BEE1FF horizon -> #69BBFF -> #2D93FB -> #1475D8
  zenith. Verify world ray direction. Mist start 12m, depth 70m, both scaled
  by actor height/1.8; compositor Depth <250m excludes sky; mist gain <=0.45.
  Fog Glow threshold 1.3, size 6, effect-only additive contribution 0.08.
- Daylight starting rig: warm key Sun #FFE4BE at E=2.2, cool fill Sun
  #9BAEFF at E=0.55 (4:1). Key shadows ON, maximum resolution 0.025m,
  jitter OFF; fill shadows OFF. At most one visible shadowed Sun.
- Light-driven cel chain: Diffuse -> Shader to RGB -> RGB to BW -> Map
  Range -> EASE ColorRamp -> Emission 1.0. Calibrate Map Range against real
  upper-forehead brim occlusion. A warm unshaded chin is not proof that the
  brim casts correctly; inspect the delivered forehead crop.
- Disable shadow casting automatically on every inverted-hull ink shell,
  cloud, smoke/wisp, projectile streak and distant horizon prop. Tag roles
  through `mark_role`; all imported horizon objects need explicit tags.
  Keep actual hats/body/props shadow-capable. Clean continuous ink and
  sidewalls, no lumpy capsules, collar cracks, sleeve seams or z-fighting.

### 8.2 Assets and 4GB GPU gate

Prefer licensed CC0/free stylized kits; retain source/license records.
Before rendering, sanitize every imported asset: props <=512px and hero
architecture <=1024px, unused normal/displacement image nodes removed,
no unused 4K maps retained in the production file. Pack resized copies;
never overwrite source asset images. Decimate eligible imported set meshes
before rigging/calibration, preserving actor geometry and silhouettes.
Count evaluated visible triangles including instances/modifiers: target
<150,000, hard <200,000. Dense invisible meshes are not a substitute for
proper visibility and texture cleanup.

Claim the shared GPU lock before any background Blender process. No parallel
Chromium render. Benchmark 12 distinct frames spread over ALL shots and worst
FX/DOF/contact states at the exact final 1080x1920/30fps settings. Record a
separate warmup, unmodified first-pass wall times including frame update/save,
p95 <=1.8s, maximum <=2.0s, and sampled board VRAM <=3.3 GiB. Keep sampling
through the render; samples cannot guarantee no brief peak. Missing GPU/VRAM
telemetry is UNVERIFIED, never a pass. Optimize and re-calibrate on failure;
retain failed measurements rather than substituting fast retries. A smoke
check proves API/node construction only, not this gate or visual quality.

### 8.3 Camera, projectile and junction gate

Measure camera clearance >=0.30m from every porch, railing, barrel, facade
and prop on EVERY frame, with evaluated moving geometry. Declare collision
meshes and shot-specific active subjects. Check camera-to-subject occlusion,
projected bounds and intentional crops from delivery cameras. A proxy check
cannot certify an omitted obstacle or a clear silhouette.

Declare actual cut destination frames separately from shot labels. Continuous
junctions must have continuous camera transform, focal and focus curves;
no undocumented resets at segment boundaries. Lens is fixed per continuous
shot, rack focus is smooth. Inspect both sides plus intermediate frames of
every transition, and any fast move/rail pass. MAD spikes outside declared
cuts/flashes/dissolves flag review, not automatic proof of collision. Do not
blanket-exempt shot boundaries. Preserve raw results and explicit reasons.

Projectiles point their local nose strictly along `pos(f+1)-pos(f)` using
`to_track_quat`, with optional LOCAL axial spin; no broadside crabbing.
Supply a deterministic arrival tangent when stopped. Check projected oblique
aspect (side and nose visible, typically >=1.6:1 elongated for a hero bullet),
not just world orientation. Record projected prop/grip separation per frame;
geometry anchors plus native crops must prove zero intersection or floating
hand/white grip ovals. Pixel clearance targets depend on the current brief.

### 8.4 Sensory and caption gate

Preserve supplied/locked narration, timing and mix unless authorized otherwise.
For newly produced fast narration target dry compressed VO ~210–230 WPM;
measure against the actual transcript/duration. Full mix target -14.3 LUFS
(within 0.5 LU), true peak <=-3.0 dBTP, narrow LRA (working target <=5 LU).
Use FFmpeg ebur128/true-peak measurements on the DELIVERED mux; word alignment
requires actual timestamp/transcript or listening evidence, not loudness stats.

Captions default OFF. When requested, burn AFTER grading using FFmpeg/libass
and the actual Bold sans-serif font file (correct shaping for the language),
pure #FFFFFF, about 20px NON-DESCENDER glyph height at 360p (~60–84px at
1080p), about 2px/6px black stroke, optical center y=70.5%, sync <=1 frame.
ASS font size and alignment alone do not establish optical glyph height or
y-position; inspect rendered glyph masks and word timing. Avoid story-critical
faces/hands. Existing locked captions/audio are not silently reformatted.

### 8.5 Required evidence before delivery

Use `scripts/calibration_sheet.py` and a story manifest to include shot
start/mid/end, action/contact extremes, junction +/-1 and +/-2 neighbors,
intermediate transition samples, and explicit native hat-brim + hand/prop
crops. Missing semantic crops/anchors are UNVERIFIED, never guessed.
Inspect the sheet and close-ups before the already-authorized full render.
Review actual movement, contact intervals and opening shadow holds in motion.

Run `scripts/short_qa.py movie.mp4 qa_dir manifest.json --strict` on the final
mux. New manifests declare cuts (possibly []), continuous junctions, action
ranges, and locked-camera or per-frame registered shadow-receiver regions.
Test opening shadow stability only where real camera/actor/lighting holds
make a pixel comparison meaningful. Missing regions are UNVERIFIED. Captions
may have explicit narrow MAD exclusions, but raw differences are retained.
Review diagnostics and keep narrow written resolutions for intentional motion;
a report PASS is not artistic acceptance. Respect user scope and stopping point.
