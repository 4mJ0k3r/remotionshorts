# `D:\remotionshorts` — project manifest / architecture brief

> **What this document is.** A self-contained description of this folder so an AI model that cannot see the
> files can still reason about the codebase accurately. It covers what the project is, the runtime stack, the
> full file architecture, the per-module responsibilities and public API, the rendering model, the numeric
> conventions every validator depends on, the toolchain, and the current verified state with measured numbers.
> It does **not** contain the source code itself (≈1.3 MB of TypeScript, 15 files in the active module).

---

## 1. What this project actually is

A **Remotion** (code-driven video) workspace that produces **vertical 1080×1920 / 30 fps animated shorts** in a
specific hybrid look: a real **three.js 3D world** (rooms, props, lighting, camera) populated by **2D
canvas-drawn cartoon characters rendered as lit billboard cards**. The team calls this "**2.5D**".

There is no 3D character modelling and no imported animation. Every cartoon figure is procedurally drawn, per
frame, into an off-screen `CanvasRenderingContext2D` by a vector helper class (`Pen`), then uploaded as a
`CanvasTexture` on a camera-facing plane inside the 3D scene. The 3D engine therefore supplies depth, shadows,
perspective, ink outlines, depth of field, bloom and colour grading, while the characters stay hand-drawn.

Four shorts live in this repo as parallel modules. One is the active work; three are completed predecessors that
share the same code skeleton (same file names, same pipeline, different story/sets/characters).

| Module | Composition id | Length | Frames | Status |
|---|---|---|---|---|
| `src/videos/bridge` | `BridgeShort` | 67.5 s | 2025 | finished, calibrated |
| `src/videos/pardon` | `PardonShort` | 20.0 s | 600 | finished |
| `src/videos/age18` | `Age18Short` | 61.6 s | 1848 | finished |
| `src/videos/school` | `SchoolHeroShort` | **122.0 s** | **3660** | **active** — Act 1 verified, Acts 2–3 not yet |

`SchoolHeroShort` is the current target: 11 shots / 10 story beats across one school "lockdown day"
(classroom → locker hallway → chemistry lab → courtyard plaza → back to classroom).

### Story of `SchoolHeroShort` (our own, original)

A bored student dozes at his desk; an alarm locks the school down; classmates panic while he stands up, calm and
glowing; he signals to his friends, takes a chair, and drops a masked intruder at the doorway with a chair slam;
he loots the gear, struts, gets a walkie-talkie briefing and a hologram, sprints the stairs with a "HERO METER"
HUD, freezes two more goons with a CO₂ extinguisher in the lab, knocks a third into a wall, gets flustered by a
classmate, is congratulated by police/SWAT/news/principal in the plaza, is hugged, throws chalk in first-person
view, and the film match-cuts back to the classroom fan from frame 0.

---

## 2. Runtime stack (exact, from `package.json`)

```
remotion                ^4.0.540      @remotion/three         ^4.0.540
@react-three/fiber      ^9.8.2        @react-three/postprocessing ^3.2.2
postprocessing          ^6.39.6       three                 ^0.187.0
react / react-dom       ^19.3.1
typescript (dev)        ^7.0.2        @remotion/{bundler,cli,renderer} ^4.0.540
```

- **Node:** v24.22.1. **Platform:** Windows 11 (win32, x64), shell = Git Bash.
- **`tsconfig.json`:** `target ES2022`, `module ESNext`, `moduleResolution bundler`, `jsx react-jsx`,
  **`strict: true`**, **`noEmit: true`** (type-check only; Remotion's bundler emits), `skipLibCheck`,
  `esModuleInterop`, `include: ["src"]`.
- **Not a git repository.** There is no `.git`, no branches, no commit history. Backups are folder copies under
  `out/*/before*` and `backup/`.
- WebGL is forced through **ANGLE** in the render scripts so headless renders get GPU acceleration.
- Output is always **540×960 (scale 0.5) for review** and 1080×1920 only with explicit approval.

**Deliberately absent** (so a model does not go looking for them): no `.git`, no `.gitignore`, no README, no
ESLint/Prettier config, no test framework, no CI, no bundler config beyond `tsconfig.json` (Remotion's webpack
does the bundling), no `.env`. `remotion.config.ts` does not exist — render options are passed as CLI/env
arguments inside the two Node harnesses. The only Markdown files in the repo are this one plus reports under
`out/`.

### Root files

```
D:\remotionshorts\
├── package.json              # scripts: "studio" (remotion studio), "still" (node scripts/bridge-stills.mjs)
├── package-lock.json
├── tsconfig.json
├── character_sheet.png       # 1.97 MB — the authoritative model sheet for the school cast (private design ref)
├── src/                      # 1.3 MB TypeScript, 58 files
├── public/                   # staticFile() assets — 3.8 MB
│   ├── school/audio.mp3      # 1.95 MB — authorized voice track for SchoolHeroShort (see §8)
│   ├── age18/audio.mp3       # 1.5 MB
│   └── bridge/kenney/        # 372 KB of .glb low-poly props used by the bridge module
├── scripts/                  # 11 build/QA tools (Node .mjs + Python)
└── out/                      # rendered mp4s, stills, QA reports, contact sheets (build artifacts)
    ├── bridge/  (many probe/qa/cal subfolders)
    ├── pardon/qa/
    ├── age18/{qa,_audiochk}/
    └── school/{act1_frames, qa, qa_full} + 81 files
```

`node_modules/` is 1.1 GB and is **not** part of the description — it is stock npm output.

---

## 3. Entry points and how a render is launched

```
src/index.ts            →  registerRoot(RemotionRoot)
src/Root.tsx            →  5 <Composition> registrations (the 4 shorts + TestCanvas), all 1080x1920 @ 30 fps
src/TestCanvas.tsx      →  17 lines, a 30-frame sanity canvas used to prove the WebGL stack works
```

Render commands actually used (all go through the two Node harnesses, which set
`REMOTION_TMP=D:/remotion-tmp` because each bundle copies `public/` into the temp dir):

```bash
npx tsc --noEmit                                             # type gate, always run first
node scripts/bridge-stills.mjs <prefix> <f,f,f> [scale]      # JPEG stills, bundles once
node scripts/bridge-video.mjs <out.mp4> [first] [last] [scale] [compId]
python scripts/short_qa.py <video.mp4> <outdir> [shots.json] # frame-by-frame QA
python scripts/scorecard.py <ours-dir> <ref-dir> [out.csv]   # numeric look metrics
python scripts/bridge_shots.py > out/school/shots.json       # shot windows for QA
```

Note: `bridge-stills.mjs` / `bridge-video.mjs` are **generic** harnesses despite the name — the composition id is
an argument, so they render the school module too.

---

## 4. Module architecture — `src/videos/school` (the active one)

15 files, **4,679 lines**. The dependency graph is strictly layered; no cycles.

```
                    School.tsx  (React composition, post chain, HUD, audio)
                        │
        ┌───────────────┼─────────────────────────────┐
        │               │                             │
     world.ts        ink.ts / lensblur.ts / grade.ts  │      (three.js scene assembly)
        │               │                             │
   ┌────┼────────────┬──┴────────────────────────────┴───┐
   │    │            │             │                      │
build.ts cast.ts   lights.ts    shade.ts / cardshade.ts   story.ts
   │      │            │                                     (pure timeline: shots, cams, beats)
 paint.ts toon.ts ── pen.ts
   │       │
   └── audioEnv.ts (generated data)
```

### File-by-file

| File | LOC | Responsibility | Key exports |
|---|---|---|---|
| `School.tsx` | 168 | The Remotion component. Mounts one `ThreeCanvas` per visible shot layer, builds the post chain, drives `delayRender`/`continueRender` on first real draw, renders the HTML HUD overlays and the 4-frame white flash. | `SCHOOL_FRAMES`, `SchoolHeroShort` |
| `story.ts` | 324 | **The single source of truth for time.** Frame rate, total, all 38 beat markers (`*_AT` absolute-frame constants), the 11-shot table, the four zone landmark coordinate tables, the camera key lists `CAMS[1..11]`, camera primitives, the impact-shake `KICKS`, depth-of-field keys `DOF`, grade lookup. Pure data + pure functions, no three.js scene objects. | `FPS`, `TOTAL`, `SHOTS`, `shotAt`, `layersAt`, `camAt`, `keyEnd`, `dofAt`, `focusAt`, `kickAt`, `CLASS`/`HALL`/`LAB`/`COURT`, `GRADE_OF`, all `*_AT` constants, `clamp01`, `smooth`, `glide`, `seg` |
| `world.ts` | 258 | Owns the three.js `root` group. `update(id, f, camera, scene)` is a **pure function of (shot id, frame)**: picks the set, toggles visibility, poses animated props (fans, strobes, doors, chair, vent, hologram, light bars, helicopter), freezes a per-shot sun/camera-relative key light, sets the gradient sky, then asks `cast.stage()` for the cards and pushes them into the pools. | `class World` |
| `build.ts` | 635 | Geometry + materials for the four sets: 24 m classroom, 45 m locker hallway, 26 m chemistry lab, 80 m plaza. Also the material registry `lam/lit/screenMat` and the `Sets` type. | `lam`, `lit`, `screenMat`, `type Sets`, `buildSets` |
| `cast.ts` | 696 | Turns story state into sprite placement. `Pool` = canvas texture cache keyed by `WxH\|drawKey` (repeated poses share a canvas). `Actor` = one billboard card (pivot at the **feet**), `Fx` = unlit effect card. `stage(id, t, cam)` returns `{places, fx}` for a frame — this is where all choreography lives. | `class Pool`, `class Actor`, `class Fx`, `SU`, `type Place/FxPlace/CamInfo/Stage`, `stage`, `FPS` |
| `toon.ts` | 982 | **The character drawing engine.** `drawKid(p, opts)` renders one figure into a 600×1000 design space from the model sheet. 12 character kinds (`Kind`), 24 expressions (`Expr`), 25 pose modes (`Mode`), 10 headgear types (`Gear`), 13 held-prop types (`PropKind`) — all props drawn **attached to the 2D hands**. `KidOpts` also carries blink/talk/aura/eyeFire/starEyes/blush/tears/sweat/shades/frost/tied overrides. Plus 20 effect-card drawers. | `drawKid`, types `Expr/Mode/Kind/PropKind/KidOpts/Gear`, `fxBlob`, `fxBlindSpot`, `fxMeter`, `fxImpact`, `fxKO`, `fxHearts`, `fxChalk`, `fxFrost`, `fxCO2`, `fxShades`, `fxRifle`, `fxChair`, `fxWalkie`, `fxVest`, `fxSpeed`, `fxFlash`, `fxTie`, `fxQuestion`, `fxSweat`, `fxRope`, `fxStarBurst`, `INK`, `mul`, `mix` |
| `pen.ts` | 104 | Thin OO wrapper over `CanvasRenderingContext2D`: rounded polys, ellipses, arcs, tapered limbs, star bursts, quadratic paths. Everything in `toon.ts` is drawn through it. | `class Pen` |
| `ink.ts` | 399 | Custom `Pass` that re-renders **world-only** (layer 0) into normal/coverage/depth targets and derives depth-silhouette + normal-crease ink lines, then composites them back before DOF. Characters/effects/sky live on layer `NOINK = 3` so they never get quad outlines. | `class InkPass`, `NOINK`, `noInkFallback`, `type InkOptions` |
| `lensblur.ts` | 139 | Thin-lens depth of field as a pre-pass + main pass, plus a separate film-grain effect. | `class LensBlurEffect`, `class LensBlur`, `class GrainEffect` |
| `grade.ts` | 262 | Display-referred colour grade as a single `Effect` with 10 named presets and a Catmull-Rom tone curve. | `GRADE_DAY/GOLDEN/DAY2/GOLDEN2/WARM/CLINIC/NIGHT/TWILIGHT/BANK/ALARM`, `GRADES`, `GRADE_STRENGTH`, `gradeFor`, `class GradeEffect`, `tintRGB`, `monoTangents` |
| `lights.ts` | 227 | Light presets (sun azimuth/elevation, intensities, fog, exposure) and world look per lighting name. | `LIGHTS`, `LOOK`, types `LightName/LightPreset/WorldLook` |
| `cardshade.ts` | 85 | Injects a hemisphere-style gradient shade into the character cards' `MeshLambertMaterial` via `onBeforeCompile` (head ×6, torso ×1.6, tint ×0.55) so flat cards read as volumetric. | `GRAD_K`, `GRAD_KB`, `TINT_K`, `CARD_K`, `cardShade`, `blobMaterial` |
| `shade.ts` | 77 | Two-tone material patcher (`twoTone`) and the tone/character constant tables; patches three's `lights_fragment_begin` shader chunk. | `TONE`, `CHAR`, `LFB`, `twoTone`, `untone` |
| `paint.ts` | 198 | Procedural canvas textures for surfaces — no image assets: wood/tile/marble/asphalt/paver floors, wall paint, blackboard, lockers, facade, periodic table, science poster, school sign, ceiling. | `tex`, `woodFloor`, `tileFloor`, `wallPaint`, `blackboard`, `lockers`, `marble`, `asphalt`, `pavers`, `facade`, `periodic`, `sciencePoster`, `schoolSign`, `ceiling` |
| `audioEnv.ts` | 125 | **Generated file** (by `scripts/school_env.py`): one amplitude value per composition frame, used for mouth/aura reaction. Do not hand-edit. | `AUDIO_ENV: number[]` |

### Sibling modules

`bridge`, `pardon`, `age18` use the **same file names and the same pipeline shape**, so a fix found in one is
normally back-ported to the others. `bridge` additionally loads Kenney `.glb` props; `age18` has its own
`build.ts`/`cast.ts` with a different set of beats; `pardon` is a 20-second medieval sketch. `bridge` is the one
the QA scripts were originally written for (hence `bridge_shots.py`, `bridge-stills.mjs`).

---

## 5. How one frame is produced (call path)

```
SchoolHeroShort(f)
  ├─ layersAt(f) -> [{id: shotAt(f).id, alpha: 1}]            # hard cuts only; XFADE is empty
  ├─ <Audio src=staticFile("school/audio.mp3") />
  ├─ ShotView -> <ThreeCanvas 1080x1920 shadows="percentage" fov 40 near .2 far 1500>
  │     └─ Inner
  │         ├─ new World() once (useMemo), fx objects once (InkPass, LensBlur, Bloom, ToneMapping, Grade, Grain)
  │         ├─ world.update(id, f, camera, scene)
  │         │     ├─ camAt(id, f)  -> pos/look/fov/roll  (+ kickAt shake offset)
  │         │     ├─ set visibility, pose animated props, per-shot sun + sky
  │         │     └─ stage(id, t, cam) -> {places, fx}
  │         │           ├─ each Actor: drawKey -> Pool.req(key, w, h, k, draw)
  │         │           └─ Pool.flush()  -> reuse/create canvases, Pen draw, CanvasTexture upload
  │         ├─ noInkFallback(world.root)
  │         ├─ dofAt(f) -> lens focus distance along view axis
  │         ├─ gradeFor(grade, GRADE_OF[light]); gl.toneMappingExposure = LIGHTS[light].exposure
  │         └─ <EffectComposer multisampling={4}>
  │               InkPass -> LensBlur.pre -> LensBlur.main -> Bloom -> ToneMapping(NEUTRAL) -> Grade [-> Grain]
  ├─ <HeroMeter/>  HTML overlay (crisp text, not rasterised by WebGL)
  └─ 4-frame white AbsoluteFill at THWACK_AT
```

**Post-chain order is load-bearing** and documented in the header of `School.tsx`: ink *before* DOF (so the
outlines blur with the background), bloom *after*, grade display-referred, bloom is emissive-only
(`luminanceThreshold: 1.0`) with its MIP chain pinned to a 1920-height equivalent regardless of output size so
0.5-scale tests look identical to full-res.

---

## 6. Numeric conventions (these are what every validator assumes)

**World space.** metres, `+y` up, `+z` toward the camera side of each set. Landmark tables in `story.ts` are
`[x, y, z]` at the feet, `y` always 0 for standing characters.

**Design space.** Characters are drawn in a **600 × 1000 unit** canvas coordinate box, 3.5 heads tall (one head,
one torso, one legs, half a pair of shoes), soles at y ≈ 952, head radius `HEAD_R = 125`, eye line
`hy = shY − 145`. Shoulder/hip heights per pose mode (design units): default `stand/walk/run/cheer/highfive/smash`
350/560, `lift` 400/620, `sit`+`sitChin` 520/735, `crouch` 500/700, `slide` 528/748, `kneel` 600/780,
`slump` 630/800. Conversion to metres: `SU = 0.00216` (1000 design units = 2.16 m). Card pivot is at the **feet**,
and the plane geometry is pre-translated by `PIV = 975` units, so `mesh.rotation` is a hip/foot roll, not a centre
roll. Cards are yaw billboards (`mesh.rotation.set(0, yaw, roll)`).

**Projection used by all measurement scripts.** `ASPECT = 1080/1920`. Given camera `pos`/`look`:
`f = normalize(look − pos)`, `r = normalize([−f.z, 0, f.x])`, `up = r × f`. Then for a world point at distance `d`
with lateral offset `lat` and vertical offset `vy`:
`u% = (lat / (d · tan(fov/2) · ASPECT) + 1) · 50`, `v% = (1 − vy / (d · tan(fov/2))) · 50`.
Framing rule: characters must land inside the **middle 20–80 %** of both axes.

**Camera primitives** (`story.ts`): `still`, `dolly`, `push`, `pushK(f, f0, rate, punch) = exp(−rate·max(0, f−f0))`
for the slow push-in, `orbit(cx, cz, r, a0→a1, f0→f1, y0→y1, …)`, `glide` = smootherstep for eased keys.
Key format: `{ f, dur?, cut?, raw?, s(f) }` — `dur` = eased move, `cut` = hard cut, `raw` = no interpolation.
`kickAt` adds a 7-frame alternating decaying shake at each impact in `KICKS`.

**The locked-down camera recipe** (Act 1, and the standard Acts 2–3 have not been brought up to it yet):
one setup per 5–8 s, camera 20–30° off the set axis, a single gentle ≈8 % push-in over the shot
(`pushK` rate 0.00022–0.0003 per frame), **no 180° orbits, no whip-pans, no empty wall in frame** — the
characters move, the camera does not.

**Props rule (hard).** Any prop a character holds — chair, rifle, walkie-talkie, extinguisher, chalk — is drawn
**attached to the 2D hands inside `toon.ts`**, never as a separate 3D mesh floating in the scene. A held prop that
leaves the hands must continue to exist as a 2D FX card (e.g. `fxChair` settles onto the floor after the slam).

---

## 7. Toolchain — `scripts/`

| Script | What it does |
|---|---|
| `bridge-stills.mjs` | Bundles once, renders arbitrary frame lists to JPEG at a scale; `BRIDGE_ENTRY` env swaps in a sandbox copy. |
| `bridge-video.mjs` | Renders a range to 540×960 h264 mp4; args `first last scale compositionId`. |
| `short_qa.py` | **The main QA tool.** Every frame at 30 fps: SPECS, LOUDNESS (LUFS/LRA/peak), silence gaps, black/white/frozen-frame detection, POPS (frame-diff > 3× local median, excluding declared `planned` windows), MOTION (mean diff, % held frames), per-shot luma/sat, 2 s contact sheets with burned-in frame numbers. |
| `motion_profile.py` | Camera motion from the rendered video: 3 height bands × 3 tiles similarity fit, hold < 0.3 px/f, drift < 2, move ≥ 2. Includes character motion. |
| `cam-profile.mjs` | **Camera-only** motion profile (authoritative for "is the camera actually still?") by projecting a 5×5 grid through `camAt(id,f)` vs `camAt(id,f+1)`. |
| `scorecard.py` | Quantitative look metrics (grade + outline measurements) comparing ours against a reference directory. |
| `sbs_sheet.py` | Side-by-side review sheet (our frames row 1, reference row 2). |
| `bridge_shots.py` | Parses `story.ts` into `shots.json` for `short_qa.py`. |
| `bridge_merge.py` | Merges look-sandbox folders back into `src/videos/bridge` by file ownership. |
| `school_env.py` | Regenerates `src/videos/school/audioEnv.ts` from the voice wav. |
| `generate-kenney-glb.mjs` | Generates missing low-poly `.glb` props for the bridge module. |

Ad-hoc numeric validators are written as throwaway `fbNN.mjs` scripts at the repo root when a specific staging
question needs answering (e.g. "does the lifted chair clear the head", "where can the discarded chair rest without
covering anyone"). They import `camAt`/`stage` directly and apply the §6 projection.

---

## 8. Assets, audio, and privacy constraints

- `public/school/audio.mp3` (1,946,654 B) is the **authorized** voice track, mounted with `<Audio>` in
  `School.tsx`; `AUDIO_ENV` is derived from it by `scripts/school_env.py`. It may be used in renders but must not
  be republished elsewhere.
- `character_sheet.png` is the authoritative model sheet for the school cast — `toon.ts` is written to match it.
- **Reference material is private.** Earlier iterations of this project were studied against third-party videos
  that must never be uploaded, published or shared, and whose scripts, characters, shot lists and channel name
  must not be copied. Nothing in this folder reproduces them.
- Measurement-target documents referenced in code comments as `references/reports/*.md` (motion, grade, outlines)
  live **outside this folder**, in the associated skill directory. They are not part of this repo.
- **No full-resolution 1080p final render without explicit approval.** All current outputs are 0.5 scale.

---

## 9. Current state, with measured numbers

**Act 1 (`SchoolHeroShort`, f0–1005, shots 1–3) is rebuilt and verified.** It was rewritten to fix three specific
defects: too much camera movement, 3D props detached from 2D hands, and character design off the model sheet.

| Check | Result |
|---|---|
| `npx tsc --noEmit` | clean |
| Camera push-in measured | beat 2 **7.1 %** over 285 f, beat 3 **6.7 %** over 345 f (target ≈8 %) |
| Orbits / whip-pans in Act 1 | **0** |
| Framing: characters inside middle 20–80 % | all frames, per `cam-profile` |
| Held props | chair / rifle / walkie / extinguisher / chalk all drawn in `toon.ts` hands; discarded chair persists as `fxChair` |
| QA on `out/school/act1_test.mp4` | POPS `[]`, no black/white/frozen frames, held frames ≈3 % |
| Per-shot luma/sat | 1: 0.565/0.406 · 2: 0.567/0.418 · 3: 0.575/0.400 |

Deliverables: `out/school/act1_test.mp4` (6.67 MB, 0–1005, 0.5, with audio) and
`out/school/act1_report.md` (9 sections: deliverables, camera target-vs-measured, props table, character/exposure
checks, staging metrics, audio, QA, six known gaps, integrity note).

**The complete film has been rendered once for review:** `out/school/school_full_05.mp4` — 23,026,543 B,
540×960 @ 30 fps, 3660 frames, 122.000 s video / 122.005 s audio (aac 48 kHz stereo), 28.0 min render at 0.5.

Whole-film QA (`python scripts/short_qa.py out/school/school_full_05.mp4 out/school/qa_full out/school/shots_full.json`):

```
LOUDNESS I -22.1 LUFS | LRA 3.9 LU | Peak -5.1 dBFS | 24 silence gaps (longest 1.698 s tail)
black [1249] | white [] | frozen >=12f: (1320,1334)(1335,1400)(1876,1906)(1915,1949)(1993,2019)(2055,2070)(2996,3009)
POPS (23): 1110 1455 1590 1915 1950 2155 2157 2170 2177 2178 2188 2194 2196 2198 2199 2290 2490 2615 3301 3481 3483 3490 3560
MOTION mean diff 4.46 | held frames (diff<0.3) 751 = 21%
luma/sat  4 0.296/0.510  5 0.374/0.451  6 0.595/0.242  7 0.490/0.329  8 0.305/0.483  9 0.695/0.176  10 0.696/0.168  11 0.549/0.403
```

**Diagnosis:** the Act-1 lock-down was never applied to shots 4–11. `CAMS[4..11]` still contain a 180°
`orbit(…, −128, 52, ORBIT2_AT, SLAM2_AT, …)` at f2155–2260, a 65° `orbit(…, −140, −75, POSE_AT, 3135, …)` at
f3010–3135, a raw `fov 46→80 / roll→0.35` whip at f3320, and 4–5 camera keys per shot instead of one setup per
5–8 s. The 9 pops inside f2155–2199 are that orbit reading as jitter. f1249 is a genuine near-black dropout;
f1335–1400 is a 65-frame frozen extreme close-up of one character card filling the frame; shots 4/8 are ~half the
brightness of Act 1 and shots 9/10 are washed out (sat 0.17 vs 0.40).

**Remaining work is code, not rendering:** camera lock-down for shots 4–11, extend the staging validator past
f1005, fix f1249, break up the 7 frozen spans, kill the orbit jitter, rebalance shots 4/8/9/10 exposure — then
re-render at 0.5 for review. 1080p stays unauthorized until explicitly approved.

---

## 10. Glossary

- **card / sprite** — one 2D character drawing on a camera-facing plane in the 3D scene.
- **stage** — the per-frame `{places, fx}` list produced by `cast.ts`; the choreography layer.
- **key** — one entry in a shot's camera list `CAMS[id]`: a frame plus a function returning pos/look/fov/roll.
- **kick** — a 7-frame decaying camera shake injected at an impact frame.
- **beat marker** — a named absolute frame constant (`SLAM_AT = 885`, …) used by `world`, `cast` and `story`.
- **pop** — a frame whose difference from its neighbours exceeds 3× the local median, i.e. a visual glitch or
  undeclared cut. Declared cut/kick windows go in `shots.json` under `planned` so they are not counted.
- **held frame** — frame diff < 0.3, i.e. nothing in the image moves. 21 % over the whole film is the main defect.
- **NOINK** — three.js layer 3; anything on it is skipped by the ink-outline pass (cards, sky, effects).
- **look sandbox** — a copied module the stills harness can target via `BRIDGE_ENTRY=src/sandboxes/<name>/index.tsx`
  to A/B a look change before merging it back with `bridge_merge.py`. That folder is **not present right now**;
  the mechanism is historical.
