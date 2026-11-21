---
name: ricks-clips-blender-style
description: Proven Blender 4.2 EEVEE Next system for Rick's Clips–style vertical Shorts (3D atmospheric worlds, stick-hybrid comic characters, dramatic lighting, snappy acting, and kinetic 3D camera transitions).
---

# Rick's Clips Style Skill v6 — Portrait Lighting, Cinema Grade and Kinetic Film Grammar

Use this spec and `scripts/ricks_v2_kit.py` for vertical Shorts in the Rick's Clips style. The full native Padoda Billionaire master is the production reference. Part 1 v04 is the approved directing and look-development reference.
- **Keep** all RTX 3050 Laptop 4GB safety & pipeline gates from `BLENDER_SKILL.md` (`BLENDER_EEVEE_NEXT`, RT OFF, `.blender_gpu.lock`, no parallel Chromium, `<150k` visible evaluated tris, `<=2.0s/frame` max, VRAM `<=3.3 GiB`, versioned folders, save/reopen checks).
- **Override** conflicting legacy visual rules in `cel-studio-contract.md` and `ricks_lookdev.py`. Use painted costume details, light-responsive cel faces, dressed sets, and deliberate camera holds on punchlines.

## Measured Film Grammar

1. **Wide immersive lens.** Default to `25–28 mm` on Blender's `36 mm` vertical sensor and place the camera close to actors for strong perspective and parallax. Use the roughly `68–75°` wide look as a framing target. The exact optical range for those focal lengths is about `65.5–71.5°`. Reserve `50–55 mm` strictly for tight macro prop inserts.
2. **Kinetic pacing.** Stage 2–3.5 second visual beats. No static pose or monotonous camera crawl may run longer than 3.0 seconds without a major action, prop event, 0.5–0.8 second macro insert, or a cut to an angle at least 25° away. Push or whip onto new props in under 0.5 seconds. Keep settled still holds to 0.5–0.8 seconds at punchline endings. Keep acting through monologue. Review the actual MP4 for slow stretches and keep smooth native camera speed at or below 55 px/frame.
3. **Six-stage character action without overshoot.** Stage **Notice → Wind-up → Strike → Hit → Settle → STILL** with a fast middle and a clean stop. Use bold changes in posture and eye-line. Disable involuntary blinks during dialogue and map speech to ten mouth shapes. Keep acting during a line and reserve fully settled holds for punchlines.
4. **0.01 s master clock and word-to-visual sync.** Run `faster-whisper` with word timestamps first, round to centiseconds, and record the result in `master_plan.json`. Preserve the full voiceover cadence, including pauses, across every module. Bind each named noun and action to a visible event within `±0.10 s` of the spoken word, with at least `96%` coverage. Show a character face within the opening hook.
5. **Set, lighting and sound changes.** Plan `5–8` sets and `2–3` lighting moods across a full Short. Shift lighting with story pivots and cue background music at a narrative pivot. Score every visible event with clearly audible frame-accurate SFX. Balance genre-matched music and sharp transients under the verbatim, intelligible narration. Listen to the muxed preview at phone playback level.
6. **Context and credit hygiene.** Run the numeric gates before vision inspection. Share compact check sheets sampled every `0.25 s` in place of full-resolution stacks. Start fresh revision turns with concise handover notes and test the hardest custom effect in isolation first.

## Numeric QA Before Full Renders

Run [scripts/ricks_metrics_gate.py](scripts/ricks_metrics_gate.py) against calibration stills, a contiguous motion preview, and the annotated master plan.

```powershell
python scripts/ricks_metrics_gate.py --edge-density renders/short/v01/calibration
python scripts/ricks_metrics_gate.py --cam-velocity renders/short/v01/preview.mp4 renders/short/v01/cuts.json
python scripts/ricks_metrics_gate.py --word-sync scripts/short/v01/master_plan.json
```

- **Edge density.** The gate measures the fraction of pixels with normalized Sobel magnitude at least `0.10` in grayscale frames resampled to a `640 px` long edge. Require mean `>= 0.14` and minimum `>= 0.088`.
- **Camera motion.** Use `{"cuts": [34, 80]}` to declare zero-based destination frames. Use `[]` for a continuous take. The gate estimates dominant screen motion from matching image tiles, including translation, zoom, and roll, at a `1920 px` long edge. It excludes declared cuts and counts motion above `2 px/frame` as moving. A hop is a contiguous run of steps above `55 px/frame`, or a sudden step of at least `35 px/frame` with a change of at least `30 px/frame` from the preceding measured step. Unmeasured non-cut pairs fail the gate. Review the camera track at ambiguous frames because foreground action and effects can defeat image registration. Use moving and still percentages as diagnostics. Judge pacing from visible actions, edit points and payoff duration.
- **Word sync.** Annotate every transcript word as `noun`, `action`, or `other`. Give each a unique ID and its actual spoken `start` and `end`. Bind visible prop, character, or action intervals to IDs. Also record face visibility and set the opening hook limit, which defaults to `2.00 s`. The gate compares word onset to the nearest point in a declared visible interval. Confirm those intervals against the actual preview before using the result as approval evidence.

```json
{
  "hook_end": 2.00,
  "words": [
    {"id": "w1", "text": "coin", "kind": "noun", "start": 1.20, "end": 1.43}
  ],
  "visual_events": [
    {"kind": "face", "start": 0.18, "end": 0.94},
    {"kind": "prop", "word_id": "w1", "start": 1.14, "end": 1.82}
  ]
}
```

The CLI writes JSON to standard output and exits with `0` for pass, `1` for a failed gate, or `2` for invalid input. Keep the reports with the part's proofs and resolve failures before the authorized full render.

## Mandatory 90+ Directing Laws

1. **Graphic cel characters in painterly 3D worlds.** Keep character surfaces at specular IOR level `0.0` and roughness `1.0`. Use crisp 2–3-step bands with `0.03–0.05` transitions, a `#FFF9F0` lit face, and pure unlit `#040407` character outlines. Use roughness `0.65–0.85` on ordinary painted 3D props. For Original Cast, use the authored warm skin palette and espresso-plum `#161020` outlines. Preserve varied head silhouettes, tiny ears, shadow-only halftones, and flat thumb-mitten hands. Dim competing background hubs or practical highlights by about half so the cream face is the brightest focal point. Keep authored material exceptions for surfaces such as wet puddles, glass, or a hero coin.
2. **Physical action and eye-line in the first second.** Within `0.0–1.1 s`, show a distinct weight shift and have the eyes track the key story prop. Check the sequence muted. In Padoda, the planted hand takes the Hero's weight, his eyes follow the rising needle, and his shoulders snap into strain before the insert.
3. **Vary the camera axis.** Limit any straight front-on zoom axis to three seconds. Alternate eye-level mediums, `0.5–0.8 s` tight macro inserts, sweeping wide cranes, and `25–30°` three-quarter angles that reveal the prop's depth and room parallax. Give every cut a story or action cue.
4. **Carry the shape through a two-frame transition.** Prefer geometric matches such as gauge to vault door, bulb to turbine, or photo to scene. Use a two-frame additive flare peak and pull the strongest flare back by about 30% so the circular or directional edge stays readable across the cut. Land immediately on a centered, unclipped subject and clear the remaining bloom promptly.
5. **Complete prop actions against dark space.** Show the pinch or pickup, release, readable airborne arc against a dark background patch, contact, and a clear five- to six-frame catch or landing hold before cutting. Check the prop, reaching hand and contact point together at preview size.
6. **Anchor seated leans and settle the payoff.** Keep the hips planted on the seat and pitch the chest and shoulders forward `12–15°`. Settle the camera before a final expression, wink or punchline, and give the payoff `0.5–0.8 s` to read. Route all flying cash and particles outside the face zone throughout the payoff.

## Autonomous Production Guardrails

1. **Modular long-Short architecture.** For any Short longer than 15 seconds, split at story or phrase boundaries into separate versioned `.blend` parts, typically 10–15 seconds each. Keep a shared integer-frame timeline at 30 fps. Each part must stay below 150,000 visible evaluated triangles and within the RTX 3050 speed and VRAM gates. Render each part as native 1080 × 1920 video with matching settings. Concatenate the video-only streams on the exact 30 fps grid and mux one continuous master narration with balanced SFX. Retain the original narration timing and verify joins, decoded frame count, and audio alignment. Use the exact beat durations from the current brief.
2. **Diegetic text and sign clearance.** At every intended read, leave at least 10% clearance around the projected ink bounds of signs, labels, and gauges, measured against label width horizontally and height vertically. Check the camera crop and swept bounds of levers, handles, and hands at their extremes. Keep every letter visible. Keep high-intensity punctual or emissive light sources at least 0.8 m from white decals and confirm contrast after compositing.
3. **Approach clearance and eating anticipation.** During a rocket or projectile approach, preserve separate readable silhouettes. For an orbit or stop, maintain at least 0.25 times the target radius between the approaching silhouette and target surface. For deliberate contact, make the first contact frame explicit with an impact burst. For eating and prop-to-mouth gags, switch to the open mouth 2–3 frames before the food reaches the lips. Verify the approach, contact, and settle frames in sequence.
4. **Golden code reference.** Before writing scene code, inspect [scripts/ricks_v2_kit.py](scripts/ricks_v2_kit.py) and the runnable [starter](scripts/templates/ricks_short_template.py). Use the local Blender executable `D:\tools\Blender\4.2.23\blender.exe` and the shared lock pattern below. Verify each exported video is native 9:16 at 1080 × 1920 and 30 fps with `ffprobe`. Fill the vertical frame directly. A 16:9 frame with letterboxing fails this check.

### Local Blender and GPU lock

Run from the repo root. The starter exclusively creates `.blender_gpu.lock` with project, PID, and owner metadata, waits for its Blender child, and releases only its own lock after the child exits. If the lock is busy, wait for that job to finish. Keep Chromium GPU renders out of the same window. For adapted launchers, use the same exclusive-create and ownership pattern around every Blender subprocess, including smoke checks.

```powershell
$env:BLENDER_EXE = 'D:\tools\Blender\4.2.23\blender.exe'
python scripts/templates/ricks_short_template.py --out renders/ricks_starter/v01
# Inspect the benchmark stills. Run the native render when authorized.
python scripts/templates/ricks_short_template.py --out renders/ricks_starter/v01 --render
ffmpeg -n -framerate 30 -i renders/ricks_starter/v01/frames/frame_%04d.png -c:v libx264 -vf setsar=1 -pix_fmt yuv420p renders/ricks_starter/v01/starter.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,sample_aspect_ratio,r_frame_rate,nb_frames -of json renders/ricks_starter/v01/starter.mp4
```

### Optional drawn look and camera program (opt-in, off by default)

Both opt-ins are independent. Without them the starter and the 3D cel character stay the default and the comparison baseline. Renderer, GPU lock, 30 fps timeline, QA and silent text-free previews are unchanged.

```powershell
python scripts/templates/ricks_short_template.py --out renders/ricks_starter/v01_drawn --look drawn
python scripts/templates/ricks_short_template.py --out renders/ricks_starter/v01_handoff --camera handoff
python tests/blender_optin_smoke.py   # construction check for all four combinations; takes the GPU lock, no render
```

- **Drawn character** ([scripts/ricks_drawn_look.py](scripts/ricks_drawn_look.py)). Call `drawn.apply_drawn_look(rig, collection)` after `build_ricks_character()` and before posing. It gives the head a slightly lopsided round outline, paints it flat cream with a restrained grey shadow on the side away from a world-space *drawn light*, and flattens hair and costume colour. The ink is near-black, thin on the lit side and heavier on the shaded side, under the chin and along the lower body. The arm tips become round fists. Use `drawn.update_ink(rig, camera, frame=f)` in place of `rig.update_ink(...)`; it works for both looks. Re-aim the light per shot with `drawn.set_drawn_light(rig, direction, frame=f)`. The rig, poses, feet and occlusion stay 3D, so `drawn.contact_anchors(rig)` returns the same hand, elbow, foot, eye and root points as the default look. Put grips on those anchors.
- **Camera program** ([scripts/ricks_camera.py](scripts/ricks_camera.py)). Build `rc.Shot(f0, f1, pos=..., aim=..., focus=..., lens=...)` objects and join them in an `rc.CameraProgram`. Position, aim, focus, lens, roll and f-stop are separate tracks. A shot boundary is always a hard cut, so match cuts and cut-on-action stay exactly where they are authored. `"carry"` position tracks keep their momentum through waypoints; `"ease"` tracks settle on each key. Use `rc.handoff(a, b, start, end)` to shift attention while the camera is still travelling, `rc.lead(subject, frames)` and `rc.damped(...)` to follow a moving subject, `rc.parallax_reveal(...)` to size a truck past a foreground occluder, and `rc.matched_distance(...)` to keep a circle the same screen size across a match cut. Bake with `rc.key_camera(camera, program.evaluate(f), f, focus_empty)` inside the frame loop, or with `rc.bake(...)`. `rc.screen_speed(program)` is a pre-render estimate only. The rendered MP4 still goes through `ricks_metrics_gate.py --cam-velocity`.
- **Reference examples (The Last Gumball v01).** Keep its brass-ring match: a hard cut, with `matched_distance`. Keep its cut on the falling ball: a hard cut whose next shot opens on the motion. The lower chute is the lesson: per-segment eased waypoints read clearly but lose momentum. Use a `"carry"` position track with a `lead` aim there.
- The source kits' cut counts, rest-creep rates and motion percentages are reference observations, not targets. The staged vendor packages live in the git-ignored `refs/vendor/` and must not be committed or redistributed (personal-use licence).

## 1. Character Construction (Stick-Hybrid Formula)
1. **Head:** Smooth 48-segment 3D ellipsoid (`r ≈ 0.24 m`, `Z ≈ 0.94`, `Y ≈ 0.88`) seated **directly snug on top of the pill torso** — ZERO visible cylindrical neck tube or gap.
2. **Torso:** Smooth high-subdivision **pill/bean capsule** (`h ≈ 0.46 m`, `w ≈ 0.25 m`, `d ≈ 0.17 m`) carrying **crisp 2D illustrated/UV-mapped costume art** (jackets, lanyards, armor bands, kurtas, stripes) — NEVER sculpted 3D cloth sleeves or puffy cuffs.
3. **Stick Limbs & Hands:** Ultra-thin pure matte jet-black (`#0A0A0E`) smooth Bezier/noodle curve tubes (`r = 0.015–0.018 m`).
   - **Hands:** Clean rounded tips of the stick arm itself (`~1.1×` arm radius). **BANNED:** oversized spherical hand balls, bulky sculpted mittens, or thick fabric sleeves.
   - **Feet:** Small clean black foot ticks (`~0.06 m`), never chunky sculpted boots unless specifically stylized.
   - **Seated legs:** Measure both splines in the standing reference pose with `rig.measure_leg_lengths()`. Plant the feet on the seat's footrest or the ground and pass those measurements as `leg_lengths` to `rig.pose()`. Fit the knee bend to the reference lengths and check foot contact at the strongest lean.
   - **Off-Hands:** Keep resting/inactive hands tucked cleanly behind or beside counters/torsos so no stray black dot peeks onto tabletops.
4. **Hair & Hoods:**
   - Offset hair caps radially `+0.008 m` outside the head sphere with Subdivision Level 2 so hair and head ink hulls never show stepping/z-fighting seams at the crown in close-ups. Use soft curved hair-highlight strokes, never rigid parallel bars.
   - Hoods use **soft draped cloth silhouettes** (never rigid circular pipes/torus rings) with pitch-dark interiors (`#0B0D18`) casting deep shadow over the upper face.

## 2. Light-Responsive Cel Shading & Bold Vector Expressions
1. **Face and torso shading.** The kit uses a white diffuse lighting probe, Shader to RGB and an eased two-step ramp with a `0.04` transition. The default face pairs lit cream with `#9EB2D6` cool shadows. For an amber set, pass `face_shadow=WARM_FACE_SHADOW` (`#D9B67A`) and `face_cutoff=.32` to the rig. Hair and costume use the same tight light bands over their authored pigment, and facial decals retain their crisp alpha artwork.
2. **Unified comic outlines.** Use backface-culled, non-shadow-casting inverted hulls.
   - **Characters (head, hair/hood, pill torso)** use pure `#040407` emission at `~2.5–3.5 px` (360p equivalent), compensated for distance.
   - **Major 3D set architecture and hero props** use subtle `#0B0A10` ink at `~1.0–1.5 px`. Exclude sky, rain streaks, and puddle noise.
3. **Bold Marker Expressions (`CONSTANT` 1-Frame Snaps):**
   - 1024×1024 transparent PNG decals with dark RGB edge dilation (zero white halo), conformed cleanly to the face surface with zero detached cheek shadows.
   - Match **Padoda v4 eye scale, brow weight and expression contrast** across tall oval, boxy jaw, pear and other head shapes. Check at phone size. Reject tiny sleepy dots even on calm faces. Use huge white-sclera `O_O` eyes, a wide dropped jaw, raised hands and a strong lighting change for peak panic.
   - Use **thick, confident marker weight**: bold solid black pill-bar eyebrows, bold black rings on wide white-sclera shock eyes, expressive mouths (smirk, teeth grin, open gasp, wobbly panic `ω`), and crisp dark-outlined sweat drops placed safely inside the temple silhouette.
   - For shadowed/hooded figures, use solid glowing pale eyes (no thin black eye outline rings) and a crisp eerie crescent grin popping out of darkness.
   - **Lip-sync.** Map the ten mouth poses on dialogue frames. During third-person narration, act silently with expressive brows, eyes, smirks, and body poses.

## 3. Dressed 3D Worlds, Lighting & Compositor
1. **Zero Empty Box Rooms:** Every camera frustum must contain **foreground + midground + background dressing** (blinds, lamps, books, plants, framed art, mugs, wet reflective streets, glowing shop windows, moonlit clouds/buildings).
2. **Strong 2-Tone Warm/Cool Color Scripting Per Scene:** e.g., deep cobalt night room (`#142042`) vs. warm tungsten lamp (`#FF9F40`); wet indigo alley (`#161B38`) vs. glowing amber shopfront (`#FFB347`) + neon accents.
3. **Cheap Atmospheric Depth (RTX 3050 Safe):**
   - Use translucent alpha-gradient **light cone meshes** (`visible_shadow = False`) for lamp pools and window shafts instead of heavy raymarched volumetrics.
   - Wet streets use sharp puddle-vs-asphalt roughness contrast (`0.04` glossy puddles vs. `0.45` damp asphalt) with smooth low-frequency bump (no harsh sandpaper grain).
4. **Portrait mode is the default in bright/daytime and night scenes.** Call `apply_portrait_dof(camera, face_plane, fstop=1.6)` with a target parented near the hero's eyes. Use a 26–32 mm lens, six aperture blades and f/1.5–1.8 for character shots. Give walls and props depth behind the actor so they fall out of focus. Check both eyes and the face ink at native size. Cut to a separate focus target for readable prop inserts or use an explicit deeper-focus shot when the story needs it.
5. **Give the hero priority in the lighting.** Call `setup_hero_portrait_lighting(hero.head, bg_dim=0.68)` after placing the environment lights. Start with environment fill at 68% of its authored level, then use the close warm key and restrained cool rim to separate the hero. Keep the environment's angled directional shadows. On Blender 4.2 EEVEE, the key and rim use short-range spotlights. Aim them into the actor and check for spill on nearby walls. On shots with multiple anchors, switch the lights with the shot. Target a lit face roughly 25–35% brighter than the immediately adjacent backdrop in the delivery frame. Check that relationship on the rendered image, since set palette, distance and cel bands affect brightness. Daytime walls, lockers and tiles should sit below the face in both brightness and sharpness. Keep night highlights controlled and preserve enough separation to read the face.
6. **Use the cinema compositor by default.** Call `setup_ricks_compositor(scene, camera=camera)` during setup. It uses AgX Medium High Contrast, a cool-shadow and warm-highlight Lift/Gamma/Gain grade, 1.12 saturation, Fog Glow at a 0.88 threshold with a 0.24 effect-only add, and a packed radial vignette with 22% corner falloff. Keep the additive portal flash after the grade. Recheck edge density with the blurred background and keep story-critical labels and hands inside the sharp plane.

```python
kit.setup_ricks_compositor(scene, camera=camera)
face_plane = kit.empty("Focus | hero eyes", collection, (0, -.16, .04), hero.head)
kit.apply_portrait_dof(camera, face_plane)
kit.setup_hero_portrait_lighting(hero.head)
```

## 4. Kinetic Camera Choreography & Seamless Scene Switching
1. **Flow and intentional holds.** Stage the actor or action on frame one after each cut. Glide through setup and action, then settle the camera completely on the key payoff words. Check beat length, physical action, insert timing and screen speed on the motion preview.
2. **Smooth S-Curve Motion:** All camera moves use smooth cubic/quintic ease-in-out curves (never robotic linear starts/stops).
3. **Signature Camera Vocabulary:**
   - Continuous push-ins with subtle lateral parallax on story beats.
   - Object-locked tracking & scale-bridging crane/drone glides.
   - Fast **4–6 frame punch-in / whip zoom-outs** + subtle 3-frame micro impact-shake on shock/comedy beats.
   - Emotional pull-back/orbit reveals that bring a second character into frame.
4. **Shape-carried transitions.**
   - **Portal / frame match-zoom** (Polaroid, screen, card, window). Accelerate into the frame, carry its edge through the two-frame additive peak and land on the next set with the subject already framed. Keep the landing clear of haze and return the flash to `0.0` immediately after the handoff. Retract any holding stick hand before the object fills the camera.
   - Also use **puddle/reflection morphs**, **prop/motion match cuts**, **graphic-to-3D pullbacks**, and **peak-anticipation smash cuts**.

## 5. Snappy Pose-to-Pose Acting & Motion Hygiene
1. **Timing.** Give fast strikes a brief middle, ease into and out of them, and recover cleanly without overshoot. Expressions snap in one frame with `CONSTANT` keys.
2. **Walk / Sneak-Run Cycle:** Pin each planted stance foot in world-X during ground contact (zero moonwalk/skating), bend knees forward in the travel direction, add a **snappy vertical body bob** per stride, tilt pill torso forward `15–22°`, and swing thin stick arms in **opposite phase** to the legs.
3. **Prop & OTS Continuity:**
   - Never block a character's eyes with a held prop before a zoom unless intentional — frame eyes peeking over the top edge.
   - Keep sliding props grounded cleanly on table/counter surfaces across the entire move.
   - When cutting to an over-the-shoulder (OTS) shot after a walk/run, slide the foreground character's silhouette smoothly into frame over the first 6–8 frames to sell physical arrival.

## 6. Production and Self-Audit Workflow
1. **Calibrate each part.** Build and save a versioned scene, reopen it, and benchmark 12 distinct native frames on RTX 3050 (`<=1.8s` p95, `<=2.0s` max, `<=3.3 GiB` sampled board VRAM). Include first, last, cuts, effects, and worst-case action views. Unknown telemetry leaves the gate unverified. Validate the visible triangle count and render/viewport parity. Run the numeric gates before assembling and inspecting the visual proofs.
   - `lookdev_turnaround.png` (front, 3/4, warm/cool lighting split, extreme expression close-up)
   - `calibration_8frames.png` (key beats, transitions, lighting, framing)
2. **Mandatory hook approval.** Render the opening 10–15 seconds at 540 × 960, 30 fps with the synced voice, music, and SFX. Present the actual MP4 and the cast lookdev sheet. Stop for user motion approval before building Part 2 or later. Verify contact, planted feet, gestures, camera clearance, flare peaks and text clearance using the stills and motion clip.
3. **Mandatory multi-part calibration.** After hook approval, build the later modules and present a combined calibration sheet covering Parts 2–4 and any further parts. Inspect those stills and resolve gate failures before any native render. Follow the user's authorized render stage.
4. **Deliver native.** Render at **1080 × 1920 @ 30 fps**, monitor full-render wall times and board VRAM, and keep versioned sources and proof reports. Mux the locked narration and SFX with no subtitles unless requested. Use a shot-aware manifest with `shorts_qa.py --strict` and a full FFmpeg decode. Check both streams with `ffprobe`, including total frame count and join timing, and report actual results.
