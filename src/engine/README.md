# Shared short-video engine

`shaders/` owns the calibrated Pen, world ink, two-stage lens blur, grade,
two-tone world shading, cream-head card shading, and procedural textures.
The coaster and elevator shader files are compatibility re-exports, so fixes
now have one implementation. Other videos can migrate their imports gradually.

`character.ts` extends the coaster drawing implementation. `Kind` selects a
wardrobe, `Expr` selects a face, and `Mode` selects an action solver. All poses
use the same shoulder anchors and outward two-bone IK. The head is rendered
after the arms to occlude any limb passing behind the face. The standing head
centre is `(300,235)`; seated motion lowers the complete connected upper body.
Use `sitP` to blend into the seated pose. Other actions have a named progress
input (for example `phoneP`, `hugP`, `prayerP`) and a common `actionP` fallback.
`walkP` and `runP` are cycle phases. `waveP` is a phase and `raiseP` is its weight.

`pool.ts` supplies reusable `Pool`, `Actor`, and `Fx` instances. Request all
drawings, call `pool.flush()`, then call each actor/effect's `bind()` before
rendering. `makeChar()` returns a placement with distance-tiered texture size
and a key generated from the same quantized options used to draw. Close-ups
use 1800×3000 textures. Call `dispose()` when the owning world is released.
`talkAt(frame, envelope)` expects one normalized audio-envelope sample per
composition frame and returns one of `0,.2,.4,.6,.8,1`. Pass it as `talk`.
`handWorldPos` takes absolute design coordinates, includes character scale,
and offsets the contact prop 8 cm behind the yaw-billboard card by default.

`camera.ts` is pure frame-addressable math:

```tsx
const camera = makeShotCam({
  a: 0, b: 180,
  from: [-1.2, 1.55, 4.5], to: [-0.6, 1.48, 3.6],
  look: [0, 1.4, 1.3], fov: 46,
  focus: f => [heroX(f), 1.2, 1.3],
});
```

Travel includes a linear velocity floor across the entire shot; equal endpoints
receive a lateral track. FOV is clamped to 38–50°. `dofAt` projects the current
subject onto the camera's forward axis, including any kick/orbit. A world-space
camera move cannot guarantee a particular pixel-level held-frame rate for every
possible scene; rendered QA still verifies the ≤2% target.

`ShortPlayer` accepts a stable `createWorld` factory, shot metadata, camera/DOF
functions, optional public audio path, and inclusive subtitle cues:

```tsx
const createWorld = () => new StoryWorld(); // stable: define outside the component
const shots = [{id: 1, a: 0, b: 180, hud: "HOUR 1", grade: "warm"}];

export const StoryShort = () => (
  <ShortPlayer createWorld={createWorld} shots={shots}
    camAt={camera.camAt} dofAt={camera.dofAt}
    audio="story/audio.mp3" cues={[[0,179,"तुम्हें कुछ नहीं होगा।"]]} />
);
```

`StoryWorld` owns `root`, `update(id, frame, camera, scene)`, and optional
`dispose()`. Keep set visibility, lights and story staging in that world.
If `camAt` is provided, `update` should leave the camera transform alone;
otherwise the world can own camera placement. Register `StoryShort` in a
Remotion composition with the intended duration, 1080×1920 size and 30 fps.

The player mounts Ink → LensBlur pre → LensBlur main → Bloom → neutral tone
mapping → Grade with 4× MSAA. HUD sits at 10%; subtitles sit at 18% from the
bottom, fit a single line, and use browser-shaped Devanagari text with the
specified Noto/Nirmala/Mangal fallback stack. Bundle a Noto font through the
composition's font loading setup when identical typography across machines is
required. `subs={false}` hides subtitles for calibration.

`kit3d` exports `lam`, `lit`, `tx`, `mesh`, `box`, `cyl`, `strut`, `beamBox`,
`lattice`, `aFrame`, `tree`, `land`, `plankStack`, `crate`, `dirtDisc`, and
`dirtPath`. Coordinates and sizes are metres; supply a parent for primitives.
Use namespaced keys for custom `lam` and `tx` cache entries. Cached materials
and textures are shared; disposing an instance only releases its owned resources.

`buildElevatorCabin({width:4.6, depth:4.2, height:3.8, doorGap:0})` returns
`root`, `setDoorGap(0..1)`, `doors`, `led.redraw(text,flash)`, `panel`, six
`buttons`, `buttonWorldPosition(name)`, `pinButton(name, worldPoint)`,
`grate`, `cables`, and `dispose()`. The front faces +Z and the +Z fourth wall
is removed. Control positions remain correct under transformed parent groups.
A 3D control linkage can join a pinned knob to its fixed panel attachment.

`buildRainCorridor()` returns an isolated hallway `root`, `rain` texture,
`redrawRain(seed)`, open `doorway`, warm `sconces`, and `dispose()`.

ElevatorCrushShort is the first full engine consumer: four authored story modules,
lighting data, and generated `audioEnv.ts`. Legacy local shader/character/cast
entry points are compatibility re-exports. The composition is registered in
`src/Root.tsx`. Calibration sheets are reviewed separately from video rendering.


The permanent character style uses `handEllPts` (stable low-frequency harmonic
skull contour), pressure-varying `Pen.inkRing`, `Pen.organic` garment/hair
silhouettes, and endpoint-pinned limb wobble. No randomness depends on frame or
canvas resolution. Card shading uses 2.4/0.9 form-gradient gains, a 0.90 shadow
floor, 1.12 overall gain and 18% extra saturation.

Camera DOF defaults are `DOF_MEDIUM = 26` and `DOF_CLOSE = 22`; set
`framing: "close"` on a shot for the latter. `focus` should resolve to the live
foreground character. CoC grows with `cInf` in this lens implementation.
`ShortPlayer` reuses InkPass's world-only depth to protect NOINK character
cutouts in both lens stages, with a 6–10 reference-pixel background blur radius
once scenery is at least 1.2 m behind focus. At scale 0.5 this becomes 3–5
output pixels. Character colours and ink are never filtered by the lens.

For partner contact, project a shoulder/upper-arm point from
`handWorldPos(cam, partnerPos, partnerScale, dx, dy, 0)` into the actor's card
using `worldToCardPoint`. Feed the resulting design coordinates to `handLX/Y`
and `handRX/Y`, with `hugP`/`comfortP` driving the continuous reach. `drawLayer`
can split `body` and `arms` into matching Actor cards, so a partner's opaque
shirt cannot hide the contact hands. Foreground arm cards keep depth writing
and render after the bodies; own-head cutouts prevent face crossing. Keep
contact targets below the partner's chin and within the card design bounds.
`partnerSide` controls generic hugging/comfort direction without a partner.
`palmScale` defaults to 1.35 when revealing a `palmText` number.


Bathroom-story extensions: `plaidHero` wears a green check shirt, `mom` has a
bun/bindi/hoop earrings and pink kurti. `crush` accepts `shirtColor` and
`outfitStyle: "top"` to use a lavender top without changing existing jackets.
`toiletSit` and `pressFlush` share connected seated proportions and ankle
boxers; `flushFist(flushP)` returns the exact design point for Rule B.
`sofaPhone` supports `lowerP`, `knockDoor`/`peekDoor` use `knockP`/`peekP`, and
`liftMug` draws the portable pink mug at its animated hand (Rule A).
