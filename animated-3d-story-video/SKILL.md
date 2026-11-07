---
name: "animated-3d-story-video"
description: "End-to-end studio-grade 2.5D vertical (9:16) animated shorts in Remotion + Three.js: generate story ideas, write the script, sync audio, and build expressive 2D canvas-drawn characters inside reactive, ink-outlined 3D worlds with automated visual QA and anti-loop speed caps."
---

# Animated 2.5D Story Video Skill (Master Weaker-Model-Proof Edition v7)

This skill creates vertical (`1080x1920`, `30 fps`) animated shorts (either a 10-second 3-shot benchmark slice in **~5 mins** or a full 45â€“120 second multi-shot film in **~25â€“30 mins**) in our hybrid **2.5D house style** inside `D:\remotionshorts`:
- **World:** Real 3D sets, architecture, terrain, vehicles, and reactive props in `three.js` with procedural painted textures (`paint.ts`), depth-and-normal ink outlines (`ink.ts`, `#351f22`), thin-lens depth of field (`lensblur.ts`), bloom, and display-referred color grading (`grade.ts`).
- **Characters:** 2D cartoon characters drawn procedurally per frame via `Pen` (`pen.ts`) in a `600x1000` design box (`toon.ts`), lit by hemisphere card shading (`cardshade.ts`), standing as yaw-billboard cards (`cast.ts`) on layer `NOINK = 3`.
- **Motion & UI:** Every shot cuts to a distinct 3D camera angle with smooth `glide()` + `pushK()` travel (`story.ts`), continuous `0..1` character action interpolation (never static pose-swapping), physically reactive 3D props (`world.ts`), and sleek top HTML HUD pills (`<Name>.tsx`).

---

## THE USER FLOW (HOW TO START)

- **If the user gives a specific scene/script prompt (e.g. "Build a 10s video about X" or gives a storyboard/audio):** Skip Steps 1â€“2 and jump immediately to **Step 3 (The 4-Stage Autonomous Build)**.
- **If the user asks to start a new video from scratch or gives only a general topic:** Follow Steps 1 -> 2 -> 3:

### Step 1: Ideas
Generate 5 true, surprising story ideas where something physically massive changes on screen (a city rises on jackscrews, a bus jumps a rising drawbridge, a tank bursts, a roller coaster loop bends). For each: one-line title, the visual 3D hook, the escalation (`But / You see / So`), and 2â€“3 verified numbers/names. Ask: *"Which one should I write?"*

### Step 2: Script & Shot Table
Write a tight voiceover script (`3.35 words/sec`):
- **10s Benchmark Slice:** 3 shots (~30â€“35 words, 300 frames).
- **Full Short (40â€“60s):** 9â€“14 shots (~140â€“180 words, 1200â€“1800 frames). Paradox hook in sentence 1 at `t = 0s`, escalation (`But...`, `Then...`), pivot (`You see...` at ~60%), payoff (`So...` at ~85%), punchy closing line.
Show a shot table (`Shot | Time | Words | Spoken Line | 3D Set, Camera Angle & Reactive Action`) and ask: *"Do you want me to build the video from this script?"*

### Step 3: Audio Timing & Autonomous 4-Stage Build
Once approved (or immediately if given a direct build prompt):
- If an audio file exists (`public/<name>/audio.mp3`), transcribe/align shot boundaries to real sentence ends, generate `audioEnv.ts` via `scripts/school_env.py` (if used), and mount `<Audio src={staticFile("<name>/audio.mp3")} />` in `<Name>.tsx`.
- If no audio file exists yet, time shots at `3.35 words/sec` and render single-line bottom subtitles synced to the cues.
- Then execute **Stages 1, 2, 3, and 4 (Section 5)** autonomously without stopping.

---

## HARD SPEED & BUDGET CAPS (ANTI-INFINITE-LOOP LAWS)

To prevent multi-hour LLM reasoning or rendering loops (such as running a framing script 60 times or launching 19 separate still bundles), you MUST obey these 4 strict caps:
1. **Max 2 Projection-Math Iterations:** Run your framing projection check (`scripts/<prefix>_frame.mjs`) **at most 2 times**. Never rewrite the checker script itself to chase 1% border grazes! Main subjects must sit inside `u = 15%..85%, v = 15%..85%`; secondary characters/props inside `u = 5%..95%` are automatically accepted. If a minor graze (`<= 5%`) remains after 2 camera adjustments, log it in the report as accepted in writing and move on immediately.
2. **Max 2 Still-Render Batches (`bridge-stills.mjs`):** Each invocation of `bridge-stills.mjs` pays a full Webpack + browser startup tax. Always pass **all calibration frame numbers for all shots in ONE single comma-separated command**. Inspect the tiled contact sheet, fix all visual defects in one consolidated batch edit, and run **at most ONE** follow-up still batch (`2 still batches total`).
3. **Single Video Render Rule & GPU Pre-Flight (Never Kill Mid-Render):** Before rendering video, ensure Chrome/ANGLE runs on the discrete GPU (`>= 250 frames/min` at `0.5` scale). Render the full video **once** in Stage 3. Never kill a running video render at 40%â€“50% to tweak a minor detail; only abort if a measured GPU/adapter fault drops throughput below `180 frames/min`.
4. **Never Render 1080p Without Explicit User Permission:** All calibration stills and review videos MUST render at `0.5` scale (`540x960`).

---

## HARD VISUAL RULES (NEVER VIOLATE)

1. **Always check types first:** Run `npx tsc --noEmit` after batching your code edits. Never render if TypeScript has errors.
2. **Never skip the Still-Frame Calibration Gate:** You must render key stills (with subtitles hidden first via `subs: false` so text never hides hands/props), tile them into a contact sheet, and visually inspect them with your vision tool BEFORE rendering any `.mp4`.
3. **Never use black silhouette heads:** Character heads are ALWAYS warm cream-white (`#fdfaf2`) with `#351f22` ink outlines so facial expressions read clearly.
4. **Never use wide-angle fish-eye FOV to fix framing:** Keep camera `fov` strictly between **`38` and `52` degrees**. If objects are clipped at frame edges, pull the camera further back (`z` distance), never crank `fov > 55`.
5. **Multi-Angle Camera Coverage (Never Hold the Same Front-On Camera Across Cuts!):** Every shot cut MUST change camera angle by at least `30Â°` or change shot scale by `>= 1.8x` (alternating between *3/4 Wide Establishing*, *Macro Prop Close-Up*, *Over-the-Shoulder Two-Shot*, and *Tight Face Portrait*). Never stage 3 characters in a flat side-by-side horizontal police-lineup row (`same z`) facing the camera!
6. **Zero Wooden Easel Clutter in 3D Sets:** Do NOT place multiple wooden easels or white poster boards on sticks inside 3D rooms/parksâ€”they block characters and ruin the 3D environment. Keep 3D sets 100% clean architecture/props, and render stat/status callouts (`"10 SEC TUTORIAL"`, `"WIN ODDS: 99.8%"`, `"0:15.00"`) as sleek **top HTML HUD Pill Badges** (`top: 10%`, `background: rgba(22, 18, 34, 0.86)`, `border: 2px solid rgba(255,255,255,0.2)`, `borderRadius: 999px`) in `<Name>.tsx`. Only use an in-world sign if it is a single natural building facade banner, road sign, or dedicated story chalkboard.
7. **Never Use BoxGeometry for Mountains/Cliffs/Trees:** Natural mountains, cliffs, and peaks must use `THREE.ConeGeometry` (slate-rock base cones topped with white snow-cap cones) and tiered cone pine treesâ€”never rectangular shipping-container boxes with striped lines!
8. **Strict 3D Set Isolation (No Water/Floor Bleed Across Shots):** Every shot's 3D set MUST live inside its own isolated `THREE.Group` toggled exclusively in `world.update()` (`setGroup.visible = (shotId === k)`). Never leave a global water plane, road, or terrain mesh visible across shots where it can slice through an indoor/cab floor or cut across a character's legs!
9. **Background Brightness & Rich Contrast (`0.38 <= Luma <= 0.65`):** Because character outlines (`#351f22`), limbs, hats, and uniforms are dark, **never place a character in front of a pitch-black wall (`luma < 0.35`)**, and **never wash out rooms into flat white/beige (`luma > 0.72`)**. Use rich twilight skies (`#2d2346`) with glowing warm yellow windows (`#ffcf56`), open windscreens, or warm mid-tone wood/brick walls so every shot achieves **`0.38 <= luma mean <= 0.68`** in `short_qa.py`.
10. **Never render two overlapping subtitle strings:** Switch subtitles cleanly on the cue frame at `bottom: 18%` with a 4-frame `#d8d8d8 -> #ffffff` brightness ease, and declare all cue/cut/impact frames in `shots.json` `"planned"` windows.
11. **Always use fresh filenames when re-rendering calibration stills:** Image viewers cache filenames (`sheet_v1.jpg` -> `sheet_v2.jpg`). Never overwrite a still filename you already viewed in the same session.

---

## 1. THE 15-FILE MODULE ARCHITECTURE (`src/videos/<name>/`)

When creating any new short in `D:\remotionshorts`, copy the shared rendering/shader infrastructure (`pen.ts`, `ink.ts`, `lensblur.ts`, `grade.ts`, `cardshade.ts`, `shade.ts`) from `src/videos/coaster/` (our calibrated baseline; ensure `cardshade.ts` head vertical UV matches `y = 235, chin ~ 380 -> v ~ 0.62`) and write the story-specific files for `<name>`:

| File | Exact Responsibility |
|---|---|
| `<Name>.tsx` | Remotion composition (`1080x1920`, `30 fps`). Mounts `<ThreeCanvas>`, builds `<EffectComposer multisampling={4}>` in exact order (`InkPass -> LensBlur.pre -> LensBlur.main -> Bloom -> ToneMapping -> Grade`), mounts `<Audio>` (if present), accepts input prop `{ subs?: boolean }` (default `true`), and renders the top HTML HUD Pill badge + bottom single-line HTML subtitles. |
| `story.ts` | Single source of truth for time: `FPS = 30`, `TOTAL`, beat constants (`*_AT`), `SHOTS`, `CAMS[id]`, `KICKS` (impact shakes), `DOF` (focus distance `dofAt`, 100% sharp from `f = 0`), `glide`, `clamp01`, `pushK`. Pure math onlyâ€”no `THREE` meshes. |
| `build.ts` | Builds clean, isolated `THREE.Group` sets (`Sets`) for each environmentâ€”buildings with glowing windows, rooms, streets, cone mountains, vehicles, bridges, machines, and articulated 3D props. |
| `world.ts` | Owns `root: THREE.Group`. `update(id, f, camera, scene)` toggles the active 3D set exclusively, animates 3D meshes/vehicles/structures as a pure function of frame `f`, pins 3D world controls to 2D hand world coordinates, and updates `cast.stage()`. |
| `cast.ts` | `Pool` (canvas texture cache keyed by `WxH|drawKey`), `Actor` (yaw billboard card, pivot at feet `PIV = 975`, scale `SU = 0.00216`), `Fx` (unlit 2D effect cards like dust, sparks, smoke, splashes), and `stage(id, t, cam)`. |
| `toon.ts` | Procedural 2D character, outfit, held-prop & FX drawing engine in `600x1000` design space using `Pen`. |
| `lights.ts` & `paint.ts` | Per-shot lighting/sky/fog presets (day, golden hour, twilight, night, indoor, alarm) and procedural canvas textures (wood, brick, metal, stone, asphalt, posters, signs). |

Register the composition in `src/Root.tsx`.

---

## 2. UNIVERSAL CHARACTER SPEC (`toon.ts` â€” DO NOT GUESS PROPORTIONS)

Every character in every story shares the same base proportions inside a **`600 x 1000` design coordinate box** (`SU = 0.00216`, so `1000` units = `2.16 m` in 3D space; pivot `PIV = 975` at the feet; soles sit at `y = 952`).

### Mandatory Base Proportions & Face Rules
- **Ink Outline (`INK`):** `#351f22` on every shape. Head/body outline width = `10â€“12` units; inner details = `6â€“8` units.
- **Head:** Large warm cream-white circle (`#fdfaf2`), center `(300, 235)`, radius **`HEAD_R = 145`**. Never use black or dark heads. Any blindfold or headband must clip cleanly to the head sphere width (`x = 155..445`, `height = 52`) so it never sticks out past the head like a hat brim.
- **Torso (Compact Bean/Pear Shape):** Narrower than the head! Shoulder width `~120`, hip width `~145` (approx `55%` of head width), top `y = 375`, bottom `y = 585`. Never draw a wide boxy rectangle torso.
- **Wardrobe / Archetypes (Adapt per Story):**
  - *Everyday / Modern Hero:* Smooth cream-white sphere head (no hair cap needed for minimalist hoodie protagonist), pullover hoodie (`#4ea8de` or story color) with two vertical white drawstring cords and front kangaroo pocket.
  - *Worker / Engineer / Inventor:* Cap or hard hat, collared shirt under overalls or utility vest with chest patch/pocket.
  - *Boss / Rival / Official:* Suit vest or blazer with lapels, tie or pocket watch chain, pompadour or slicked hair.
  - *Uniform / Historical / Guard:* Peaked cap or top hat, belted tunic/coat, badge or shoulder straps.
- **Legs (Parallel Vertical Sticks):** Hip attachment at `x = 300 Â± 35` (`265` and `335`), dropping straight down vertically to `y = 945`. Never bow legs outward in a cowboy stance. When a character jumps (skateboard kickflip, snowboard backflip), translate the character card upward parabolically (`+0.35m to +0.50m`) in `cast.ts` so they physically leave the ground!
- **Feet:** Small dark `#351f22` or white rounded pills (`width = 52, height = 24`) resting flat at `y = 952`.
- **Eyes (No Anime Shine Dots!):**
  - Default / Happy / Sad / Smirk / Shocked eyes use **solid `#351f22` oval pupils** (`rx = 16, ry = 22`) with **zero white anime highlight dots**.
  - Squinting/Strain/Laughing eyes use bold `#351f22` `> <` or `^ ^` chevrons.
  - Pair eyes with thick, expressive floating `#351f22` eyebrows (`y = eyeY - 34`) that tilt or arch to show emotion.
- **Hair & Hats:** When a character wears a hat or hair cap, it must rise **above** the `HEAD_R = 145` head contour (`y < 90`) so it reads as a distinct silhouette, not painted flat inside the forehead.

### Continuous Action Interpolation (No Static Pose Popping!)
Never switch poses with discrete boolean steps (`mode = 'idle'` -> `mode = 'action'`). Instead, pass continuous `0..1` float parameters in `KidOpts` (e.g., `actionP?: number`, `holdP?: number`, `reachP?: number`):
1. **Quantize in `drawKey`:** Always round continuous floats in `drawKey` to `0.02` steps (`Math.round(p * 50) / 50`) so `Pool` caches textures cleanly without memory leaks.
2. **3-Phase Motion Curve:** Drive every physical action through:
   - *Wind-up / Anticipation* (`0.0 -> 0.35`, eased with `glide`)
   - *Fast Impact / Extreme* (`0.35 -> 0.55`, steep step + `KICKS` camera shake + 2D FX burst at impact frame)
   - *Follow-Through / Settle* (`0.55 -> 1.0`, gentle ease into resting hold)
3. **Layer Ordering During Overlaps:** If an arm or held tool swings across the upper chest/neck, draw the **head after the back arm** and keep all held props strictly inside `x: [40..560], y: [30..980]` so nothing is clipped by the `600x1000` canvas border or blocks the character's face.

---

## 3. THE 2D-HAND TO 3D-PROP CONTACT LAW (`world.ts` & `toon.ts`)

A 2D character is a camera-facing billboard (`yaw = atan2(cam.x - char.x, cam.z - char.z)`). If you place a 3D prop in world space and draw a 2D hand at a fixed spot, **parallax will break alignment whenever the camera moves.**

Always follow **ONE** of these two rules:

### Rule A: Self-Contained 2D Held Props (Preferred for Portable Items)
Any portable object a character picks up, swings, rides, or holds (tools, skateboards, snowboards, Rubik's cubes, weapons, wallets, phones, books, guitars, shovels, certificates, mugs) MUST be drawn directly inside `toon.ts` attached to the 2D hands/feet `(hx, hy)` with hands pinching the outer edges so fists never cover text on signs/certificates.

### Rule B: Pinning a 3D World Object (Levers, Wheels, Chess Pieces, Switches) to a 2D Fist
When a 2D character must touch, tip over, pull, or grip a part of the 3D environment:
1. Draw the character's hand as a closed fist at a known design-space coordinate `(dx, dy)` (e.g. `dx = 145, dy = 590`).
2. In `world.ts` every frame, compute the exact 3D world position of that `(dx, dy)` point using the character card's billboard basis:
   ```ts
   // charPos = [cx, cy, cz] at feet; camPos = camera position
   const yaw = Math.atan2(camPos.x - cx, camPos.z - cz);
   const rightX = Math.cos(yaw), rightZ = -Math.sin(yaw);
   const fwdX = Math.sin(yaw),   fwdZ = Math.cos(yaw);
   const localX = (dx - 300) * SU;          // horizontal offset from card center (300)
   const localY = (975 - dy) * SU;          // vertical offset above feet pivot (975)
   const depthOffset = -0.08;               // 8 cm BEHIND card plane so 2D fist covers 3D handle!
   const handWorldX = cx + rightX * localX + fwdX * depthOffset;
   const handWorldY = cy + localY;
   const handWorldZ = cz + rightZ * localX + fwdZ * depthOffset;
   ```
3. Place the handle/knob/piece of the 3D object at `(handWorldX, handWorldY, handWorldZ)` every frame. Because `depthOffset = -0.08` pushes the 3D knob 8 cm behind the billboard plane, the 2D fist cleanly covers the knob while the 3D shaft/mechanism connects to the 3D world with **zero gap at every camera angle**!

---

## 4. CAMERA, DOF, FRAMING & 3D ARCHITECTURE RULES (`story.ts` & `build.ts`)

1. **Continuous Camera Travel from Frame `shot.a` (NEVER Hold Still at Shot Start!):**
   - Never start a shot with a `still` camera wait segment.
   - Every shot's primary `glide(f, shot.a, moveEndF)` camera move MUST start on the very first frame of the shot (`shot.a`), and immediately transition into a gentle `pushK` drift (`1%â€“2%` over the remaining frames until `shot.b`) so **every single frame of the video has smooth motion (`held frames <= 2%`)**.
2. **Exact Depth-of-Field Focus Tracking (`dofAt` â€” Sharp from Frame 0!):**
   - Never start a shot out-of-focus! Always compute `dofAt(f)` dynamically as the Euclidean distance along the view axis from `cam.pos` to the **current active subject** (interpolating from background landmark in wide views to foreground character `[cx, cy + 1.2, cz]` as the camera pushes in).
3. **FOV, Framing Math & 3D Building Sky Margins (`ASPECT = 1080 / 1920 = 0.5625`):**
   - Keep `fov` between **`38Â°` and `52Â°`**.
   - At distance `d` from the look-at target:
     - `Visible Height = 2 * d * tan(fov * PI / 360)`
     - `Visible Width  = Visible Height * 0.5625`
   - Verify via a 2-pass projection script that main subjects sit within **`15% to 85%`** (`u%` and `v%`).
   - **Background Landmark Scale & Sky Margin Rule:** In wide and medium shots featuring a background building/tower/bridge/tank (`z ~ -12..-16m`), scale its height so it fills `v = 12%..55%`, AND constrain its horizontal width so its left and right edges stay within **`u = 12%..88%`** (leaving visible sky and 3D side-wall depth on both sidesâ€”never a flat wall-to-wall wallpaper covering 100% of the frame width!).
4. **Architectural Detail & Background Contrast (No Dark Voids, Blank Boxes, or Ice-Cube Mountains):**
   - Never use a plain white or black un-detailed rectangle for a building entrance or window. Every building entrance must have recessed wooden/glass double doors, a dark trim frame, and transom/mullion lines.
   - Never use `BoxGeometry` for mountains or buried snow figuresâ€”use `ConeGeometry` for mountain peaks and pine trees, and bury actual character rigs partially in snow (`y = -1.1m -> 0.0m`) rather than placeholder cylinders.
   - **Indoor / Cutaway Cab Contrast:** Always include either a large open window showing the twilight/day sky with glowing city windows behind the character OR warm, well-lit mid-tone walls (`0.38 <= luma mean <= 0.65` required in every shot).
   - Mount any building facade banner in a dedicated upper frieze/cornice band with at least `0.4m` vertical clearance from window sillsâ€”never let a sign overlap windows!

---

## 5. MANDATORY 4-STAGE EXECUTION WORKFLOW (FOLLOW IN ORDER, OBEY SPEED CAPS)

Execute all 4 stages autonomously when asked to build a short or scene. Do not skip Stage 2, and do not exceed the iteration caps.

### Stage 1: Build, Type-Check & 2-Pass Projection Math Check
1. Implement or update the module files in `src/videos/<name>/` and register in `src/Root.tsx`.
2. Run `npx tsc --noEmit` and fix all errors until it exits `0`.
3. Write and run a projection math check script (`scripts/<prefix>_frame.mjs`) **at most 2 times** to verify main subjects sit inside `u = 15%..85%`, `v = 15%..85%` and camera angles change across cuts. Accept any minor secondary-character border graze (`5%..95%`) in writing rather than looping.

### Stage 2: Single-Batch Subtitles-Off Calibration Stills & Visual Inspection Gate
1. Pick 1â€“2 critical frames per shot and render **all calibration frames in ONE single `bridge-stills.mjs` command** at `0.5` scale (`540x960`) with **`subs: false`** first so Webpack bundles only once:
   `BRIDGE_ID=<CompId> node scripts/bridge-stills.mjs out/<name>/cal/f <f1,f2,f3,...> 0.5`
2. Tile the stills into a contact sheet under a **fresh filename** (`sheet_v1.jpg`) and render close-up crops on any Rule B hand-to-prop contact points. **Inspect the images using your vision tool.**
3. **Visual Checklist (Must Check All 9 Before Video Render):**
   - [ ] Are all character heads cream-white (`#fdfaf2`) with `#351f22` outlines, solid dark pupils (no anime white shine dots), and snug headwear/blindfolds?
   - [ ] Are torsos compact (`~55%` of head width) with straight vertical parallel legs grounded on the floor/platform (or parabolically airborne during jumps)?
   - [ ] **Set Isolation Check:** Is there any stray water plane, terrain, or floor mesh from another set slicing horizontally through characters' legs or indoor rooms? (Must be zero!)
   - [ ] **Multi-Angle & Zero-Easel-Clutter Check:** Does every shot cut to a distinct 3D camera angle (`>= 30Â°` or scale change), and is the 3D set free of cluttered wooden easel signboards (using top HTML HUD pills instead)?
   - [ ] **Background Brightness Check:** Are all backgrounds behind characters well-balanced (`0.38 <= luma <= 0.65`, no pitch-black voids and no washed-out white rooms)?
   - [ ] Are held 2D tools/props completely inside the `600x1000` card (not clipped at the top edge) and NOT crossing over the character's face or covering text on held cards?
   - [ ] For any 3D prop touched by a 2D hand (Rule B), is the 2D fist cleanly covering the 3D attachment point with zero air gap and zero stray pegs?
   - [ ] Do large 3D structures fit inside `u = 12%..88%` and `v = 10%..85%` at `fov <= 52Â°` with visible sky margins, detailed doors, and `ConeGeometry` mountains/trees (no boxy ice-cube walls)?
   - [ ] When subtitles are re-enabled (`subs: true`), is there only ONE subtitle line visible at a time (no double-text ghosting)?
4. Fix all visual defects found in the stills in **one consolidated code pass**, re-render only the changed frames in **at most one confirmation batch** (`sheet_v2.jpg`), and proceed immediately to Stage 3.

### Stage 3: Single 0.5-Scale Video Render via Discrete GPU
1. Confirm discrete GPU throughput (`>= 250 frames/min` at `0.5` scale; never kill a healthy render mid-way).
2. Render the video once at `540x960` (`0.5` scale):
   `node scripts/bridge-video.mjs out/<name>/<name>_v1.mp4 0 <lastFrame> 0.5 <CompId>`

### Stage 4: Automated `short_qa.py` Gate
1. Write `out/<name>/shots.json` with all shot ranges `{"id", "a", "b"}` and `"planned"` windows for hard cuts, impact shakes (`KICKS`), expression swaps, and subtitle cue transitions.
2. Run:
   `python scripts/short_qa.py out/<name>/<name>_v1.mp4 out/<name>/qa out/<name>/shots.json`
3. **Hard Pass Criteria:**
   - `black frames`: `[]` (none)
   - `white frames` (unplanned): `[]` (none)
   - `frozen spans >= 12f`: `[]` (none)
   - `POPS` (unplanned): `[]` (none)
   - `held frames`: `<= 3%`
   - `per-shot luma mean`: `0.38 <= luma <= 0.68` on every daytime/twilight/indoor shot
4. Inspect at least two generated QA contact sheets (`out/<name>/qa/sheet_0000.jpg`) with your vision tool to confirm the final rendered video matches the stills. Write the summary report to `out/<name>/<name>_report.md`.
