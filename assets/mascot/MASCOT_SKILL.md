---
name: mascot-character-short
description: Official directing, rigging, expression, and animation specification for vertical 9:16 Blender 4.2 EEVEE Next Shorts featuring our Red-Beanie Yellow-Hoodie Chibi Mascot (`assets/mascot/`).
---

# Official Main Character Skill (`assets/mascot/`)

Use this skill together with [RICKS_STYLE_SKILL.md](../../RICKS_STYLE_SKILL.md), [scripts/ricks_v2_kit.py](../../scripts/ricks_v2_kit.py), and [scripts/ricks_camera.py](../../scripts/ricks_camera.py) whenever a Short features our **Main Character (Red-Beanie Yellow-Hoodie Chibi Mascot)**.

Never rebuild the Mascot from primitives in story scripts—always load the canonical rig via `assets.mascot.mascot_api.load_mascot(...)` and drive acting through `assets.mascot.anim_library` or `hero.pose(...)`.

---

## 1. 3-Line Python Quickstart

```python
from assets.mascot import mascot_api, anim_library
hero = mascot_api.load_mascot(scene.collection)
anim_library.stop_hold_up(hero, 1, 60)
```

For complete Shorts, copy [`starter_scene_template.py`](starter_scene_template.py) to `scripts/<new_short>/v01/build.py`, edit `STORY_BEATS` and `CAMERA_SHOTS`, and run on Modal GPU or locally with `.blender_gpu.lock`.

---

## 2. Mandatory Visual & Render Invariants

1. **Delivery Format:** Native vertical `1080 × 1920` (`resolution_percentage = 100`, `SAR 1:1`), `30 fps`, `BLENDER_EEVEE_NEXT`, `taa_render_samples = 32`, `use_raytracing = False`.
2. **Lens & Sharpness:** Default to a `26 mm` wide perspective lens (`sensor_fit = 'VERTICAL'`, `sensor_height = 36 mm`) placed close to the Mascot for strong comic foreshortening (e.g., outstretched `open_stop` palm in `stop_hold_up`). Keep `camera.data.dof.use_dof = False` by default on Mascot showcase/comic shots so `#141016` outlines and background gags stay razor-sharp (Note: `kit.setup_ricks_compositor(scene, camera=camera)` enables DOF via `setup_ricks_camera`, so explicitly set `camera.data.lens = 26.0` and `camera.data.dof.use_dof = False` afterward).
3. **Marshmallow Head Ratio & Bright Snow-White Paint:**
   - Head dimensions (excluding beanie): `width_x = 0.440 m`, `depth_y = 0.400 m`, `height_z = 0.448 m` (`height_z / width_x = 1.018`, strictly `1.00 <= ratio <= 1.05`). Never squash or non-uniformly scale `hero.head` outside `[1.00, 1.05]`.
   - AgX-compensated snow-white paint (`#FFFDFB`, ~88% pure white face area with soft `#DCE2EE` lower-jaw crescent shade). Light scenes brightly enough that the face never turns muddy grey.
4. **Signature Costume & Triangle Budget:**
   - **Beanie:** `4°`-tilted crimson ribbed knit beanie (`#E62429` / `#AE151B`), plump folded brow cuff, 6 curved `#141016` rib grooves, upper-left glossy highlight.
   - **Hoodie:** Oversized A-line cozy yellow hoodie (`#FFD21F` / `#DF9B12`), snug 3D neck/back hood collar (zero neck gap), 2 black metal eyelets + 2 secondary-animated white drawstrings, kangaroo pouch pocket, sleeved IK arms (`arm_style="hoodie"` default; `"stick"` optional).
   - **Bottoms & Footwear:** Charcoal-navy lounge pants (`bottom_style="pajamas"` default; `"shorts"` optional) and chunky white-and-black sneakers with flat rubber soles at `Z = 0.000 m` (`visible_shadow = True`).
   - **Geometry Budget:** Full Mascot is `< 35,000` triangles, keeping multi-character dressed sets safely below the `< 150,000` triangle RTX 3050 / preflight target.
5. **Per-Frame Ink & Final Bake:**
   - After baking `STORY_BEATS` and `CAMERA_SHOTS`, loop every frame (`1..END_FRAME`), call `scene.frame_set(f); bpy.context.view_layer.update(); hero.update_ink(camera, frame=f)`, and finish with `hero.finish_bake()`.

---

## 3. Coordinate System & Rig Hierarchy

| Property | Convention / Value |
| :--- | :--- |
| **Forward Direction** | Local `-Y` (`yaw = 0.0` faces a camera at `(0, -d, z)` aiming `+Y`) |
| **Side Convention** | `L = -X` (viewer-left when facing Mascot), `R = +X` (viewer-right), matching `ricks_v2_kit.py` |
| **Floor Contact** | `Z = 0.000 m` — `loc=(x, y, 0.0)` with `leg_L/R` foot `fz = 0.0` plants sneaker soles flat on `Z = 0.000 m` |
| **Total Standing Height** | `≈ 1.28 m` (chunky 3-head-tall chibi silhouette) |
| **`hero.root`** | World-space character root Empty (`loc`, `yaw` around `Z`) |
| **`hero.body`** | Parented to `root` at standing `(0.0, 0.0, 0.56)` (`bounce` offsets `Z`, `body_tilt` pitches `X`, `body_roll` rolls `Y`, `squash` scales `Z` with volume preservation) |
| **`hero.head`** | Parented to `body` at `(0.0, 0.0, 0.40)` (`Z_world ≈ 0.96 m` standing; `head_pitch` = `X`, `head_roll` = `Y`, `head_yaw` = `Z` in radians) |
| **Shoulders (`body`-local)** | `L = (-0.155, 0.0, 0.18)`, `R = (+0.155, 0.0, 0.18)` |
| **`hero.hand_socket_L` / `R`** | World-accurate palm-center Empties for `0.000 m` prop attachment |
| **`hero.foot_L` / `foot_R`** | Sneaker pivot Empties (`Z = 0.000 m` sole contact when `fz = 0.0` at `root.z = 0.0`) |
| **`hero.light_empty`** | Directional comic cel light vector Empty (aliased as `hero.drawn_light`), synced in `update_ink()` |

---

## 4. `mascot_api.py` — Complete API Specification

### Constants
- `mascot_api.EXPRESSIONS`: Tuple of all 12 story expression names.
- `mascot_api.VISEMES`: Tuple of all 6 lip-sync viseme names.
- `mascot_api.ALL_EXPRESSIONS`: `EXPRESSIONS + VISEMES` (all 18 valid decal names).
- `mascot_api.HAND_POSES`: Tuple of all 7 swappable 3D hand pose names.

### Functions & `MascotRig` Methods

#### `load_mascot(collection, name="Mascot", bottom_style="pajamas", arm_style="hoodie") -> MascotRig`
- Appends the `"MascotHero"` collection from `assets/mascot/mascot_master.blend` into `collection` (or builds procedurally on the fly if `mascot_master.blend` is being generated).
- `name`: Unique prefix supporting multiple independent characters in the same scene.
- `bottom_style`: `"pajamas"` (default charcoal lounge pants with white side stripe) or `"shorts"` (charcoal lounge shorts + calves).
- `arm_style`: `"hoodie"` (default puffy `#FFD21F` yellow hoodie sleeves) or `"stick"` (matte `#141016` `r = 0.020 m` stick arms).

#### `hero.pose(...)`
```python
hero.pose(
    frame,                      # int (inserts keyframes) or None (immediate pose without keys)
    loc=(0, 0, 0),              # World-space (x, y, z) root location; z=0.0 is floor level
    yaw=0.0,                    # Root Z heading in radians (0.0 faces -Y)
    body_tilt=0.0,              # Torso forward/back pitch (radians; + tilts forward toward -Y)
    body_roll=0.0,              # Torso side-to-side tilt (radians)
    bounce=0.0,                 # Vertical Z offset (meters) added to standing body height (0.56 m)
    squash=1.0,                 # Chibi Z squash/stretch factor (1.0 = neutral, <1 = squash, >1 = stretch)
    head_yaw=0.0,               # Head turn left/right in radians
    head_pitch=0.0,             # Head nod up/down in radians
    head_roll=0.0,              # Cute head tilt in radians
    arm_L=None,                 # None (relaxed (-0.22, -0.06, -0.06)), (hx,hy,hz), or ((hx,hy,hz),(ex,ey,ez)) in body-local
    arm_R=None,                 # None (relaxed (+0.22, -0.06, -0.06)), (hx,hy,hz), or ((hx,hy,hz),(ex,ey,ez)) in body-local
    leg_L=None,                 # None ((-0.105, 0.0, 0.0)), (fx,fy,fz), or ((fx,fy,fz),(kx,ky,kz)) in root-local
    leg_R=None,                 # None ((+0.105, 0.0, 0.0)), (fx,fy,fz), or ((fx,fy,fz),(kx,ky,kz)) in root-local
    hand_L="relaxed_curl",      # Any name in HAND_POSES (1-frame CONSTANT swap)
    hand_R="relaxed_curl",      # Any name in HAND_POSES (1-frame CONSTANT swap)
    hand_rot_L=None,            # Optional (rx, ry, rz) Euler override for left hand orientation
    hand_rot_R=None,            # Optional (rx, ry, rz) Euler override for right hand orientation
    foot_rot_L=None,            # Optional (rx, ry, rz) Euler override for left sneaker (e.g., chair cross, toe-off)
    foot_rot_R=None,            # Optional (rx, ry, rz) Euler override for right sneaker
    string_sway=None,           # Optional secondary bounce/sway tuple or scalar for the 2 white hoodie drawstrings
    expr=None,                  # Optional expression/viseme name (calls set_expression(expr, frame))
)
```

#### `hero.set_expression(expr_name, frame=None)`
- Switches conformed face decal artwork across all 18 packed PNGs (`EXPRESSIONS + VISEMES`) using 1-frame `CONSTANT` keyframes so decals never cross-fade or ghost.

#### `hero.auto_lipsync(audio_path, start_frame, end_frame, base_expr="idle_cute", fps=30)`
- Decodes `.wav` / `.mp3` audio via `wave` or `ffmpeg`, computes per-frame RMS amplitude and zero-crossing rate over `[start_frame, end_frame]`, keys crisp `CONSTANT` visemes (`vis_closed`, `vis_AA`, `vis_EE`, `vis_OH`, `vis_OO`, `vis_FV`) on active speech frames, and returns cleanly to `base_expr` during silence.

#### `hero.attach_prop(prop_obj, side="R", f_start=1, f_end=100, offset=(0, 0, 0), rot_euler=(0, 0, 0))`
- World-pins `prop_obj` to `hero.hand_socket_R` (`side="R"`) or `hero.hand_socket_L` (`side="L"`) on every frame in `[f_start, f_end]` with `< 1e-4 m` (`0.000 m`) contact drift, applying local `offset` and `rot_euler`.

#### `hero.update_ink(camera, frame=None, pixels=4.2)`
- Updates (and keys when `frame` is given) all `#141016` backface-culled inverted-hull outline modifiers based on evaluated camera-space depth and `camera.data.lens`.

#### `hero.head_bbox_ratio() -> dict`
- Returns `{"width_m": float, "depth_m": float, "height_m": float, "ratio": float}` and asserts `1.00 <= ratio <= 1.05`.

#### `hero.finish_bake()`
- Enforces `CONSTANT` keyframe interpolation on all `hide_render` / `hide_viewport` swap channels (expressions and 7 hand poses) and `LINEAR` interpolation on densely baked motion and ink channels.

---

## 5. Expressions & Lip-Sync Visemes (`12 + 6 = 18`)

### A. 12 Story Expressions (`assets/mascot/expressions/<name>.png`)

| # | Name | Eyes & Brows | Mouth & Comic Details | Best Story Use |
| :- | :--- | :--- | :--- | :--- |
| 1 | `idle_cute` | Big solid `#141016` glossy ovals (`~6°` inward tilt) | `//` cheek ticks + tiny sweet smile | Default calm, walks, reaction setups |
| 2 | `curious_o` | Big solid black ovals (pure glossy black, no dots) | `//` ticks + surprised open `o` (`#4A121B` + `#FF7B89` tongue) | `stop_hold_up` (Img 5), `power_aura_stance` (Img 6), `sneak_to` |
| 3 | `chill_laugh` | Big solid black ovals | `//` ticks + wide happy `D` grin, `#FFFDFB` top teeth bar & coral tongue | `chill_chair_lean` (Img 7), upbeat payoffs |
| 4 | `hype_letsgo` | Wide excited eyes + bold angled brows | Huge hype open mouth + top teeth bar + tongue + action ticks | `celebrate_hype`, breakthroughs |
| 5 | `cringe_teeth` | Left `>` squeezed + right wide shock eye | Wide clenched teeth grid + cyan `#51C8F2` temple sweat drops | `take_hit_recoil`, second-hand embarrassment |
| 6 | `whatever_eyeroll` | Half-lidded upward eye-roll | Side air-puff mouth | `shrug_idk`, unimpressed reactions |
| 7 | `phone_zombie` | Droopy tired lids + dark under-eye bags | Open `o` mouth with tiny drool drop + subtle cool-blue screen tint | `phone_scroll_zombie`, exhaustion |
| 8 | `sulk_pout` | Angled pouty brows over black ovals | Soft pink rosy cheeks + `hmph` pout mouth | Being ignored, petty loss |
| 9 | `mortified_blush` | Wide shock eyes | Warm rosy-red full-face flush + wavy `~` mouth + sweat drops | `run_panic_to`, `dramatic_double_take` |
| 10 | `smug_wink` | Smooth `—` wink on one eye + confident eye | Cocky side smirk | `point_at_camera_wink`, outsmarting rival |
| 11 | `crush_hearts` | Glowing pink heart highlights inside big black ovals | Rosy cheeks + `///` blush lines + `:3` cat mouth | Falling in love with object/money/food |
| 12 | `ugh_groan` | Tightly squeezed `> <` eyes | Tall open groan mouth + long sticking-out coral-pink tongue | `facepalm_groan`, total annoyance |

### B. 6 Lip-Sync Visemes (`assets/mascot/expressions/visemes/<name>.png`)

| Name | Phoneme / Acoustic Trigger | Visual Mouth Shape (with Iconic Black Ovals + `//` Ticks) |
| :--- | :--- | :--- |
| `vis_closed` | Silence threshold / bilabials (`M`, `B`, `P`) | Clean closed comic line smile |
| `vis_AA` | High RMS open vowels (`AA`, `AH`, `AY`) | Wide tall open mouth with maroon interior & coral tongue |
| `vis_EE` | High zero-crossing / bright vowels (`EE`, `IH`, `S`, `Z`) | Wide horizontal grin showing crisp white top teeth bar |
| `vis_OH` | Mid-high RMS rounded vowels (`OH`, `AW`, `OR`) | Medium-large rounded oval mouth |
| `vis_OO` | Low-ZCR tight rounded vowels (`OO`, `UW`, `W`) | Compact small pursed `o` mouth |
| `vis_FV` | Fricatives (`F`, `V`, `TH`) | Upper white teeth tucked cleanly against lower lip |

---

## 6. 7 Swappable Hand Poses & Prop Attachment (`mascot_api.HAND_POSES`)

| Pose Name | Geometry | Typical Pairing |
| :--- | :--- | :--- |
| `relaxed_curl` | Puffy 4-finger cartoon mitt with natural curl | `idle_breathe`, `walk_to`, `sneak_to` |
| `open_stop` | Wide 5-finger spread palm (Ref Image 5) | `stop_hold_up`, `shrug_idk`, `facepalm_groan` |
| `power_claw` | Dramatic upturned curled claws (Ref Image 6) | `power_aura_stance` |
| `fist` | Plump clenched cartoon fist | `celebrate_hype`, `jump_parabolic`, `take_hit_recoil` |
| `point` | Extended index finger + curled fingers | `point_at_camera_wink`, `talk_explain` |
| `thumbs_up_ok` | Puffy cartoon thumbs-up mitt | `pickup_and_present`, approval holds |
| `behind_head` | Smooth contoured mitt tucked behind beanie (Ref Image 7) | `chill_chair_lean` |

**Attaching a 3D Prop (`0.000 m` Grip):**
```python
# Pin prop to right palm from frame 35 to 90, then release or hold:
hero.attach_prop(coin_obj, side="R", f_start=35, f_end=90, offset=(0.0, -0.02, 0.0))
```

---

## 7. `anim_library.py` — Complete 18-Function Directing Catalog

Every function in `anim_library.ANIMATION_NAMES` follows Rick's Clips **Notice → Wind-up → Strike → Hit → Settle → STILL** quintic S-curve timing, pins stance feet in world space (`0.000 m` skating), animates chibi squash/bob + secondary hoodie drawstring sway, and returns a metadata `dict` (`animation`, `f0`, `f1`, `stance_windows_L/R`, plus any spawned helper objects):

| # | Exact Signature | Behavior, Expression & Props/VFX |
| :- | :--- | :--- |
| 1 | `idle_breathe(hero, f0, f1, *, loc=(0,0,0), yaw=0.0, expr="idle_cute")` | Gentle chest breathing cycle, micro head bob, planted sneakers at `loc`, sets `expr`. |
| 2 | `walk_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="idle_cute")` | Travels from `start_xy` to `end_xy` on `ground_z` facing travel heading; world-pinned stance feet, bouncy stride, opposite-phase sleeve swing. |
| 3 | `run_panic_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="mortified_blush")` | High-tempo panic sprint with forward lean, raised flailing `open_stop` hands, energetic string whip, `mortified_blush`. |
| 4 | `sneak_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="curious_o")` | Hunched tiptoe stealth walk with high step arcs, tucked `power_claw` hands, and cautious left/right head scans. |
| 5 | `stop_hold_up(hero, f0, f1, *, loc=(0,0,0), yaw=0.0)` | **Exact Reference Image 5:** Anticipation dip → slight backward lean + viewer-left `arm_L` thrust forward toward `-Y` lens with big `hand_L="open_stop"` palm, `arm_R` counter-balanced back, `curious_o`. Pair with a low-angle `26 mm` camera close to the left palm! |
| 6 | `power_aura_stance(hero, f0, f1, aura=True, *, loc=(0,0,0), yaw=0.0, collection=None)` | **Exact Reference Image 6:** Heroic wide stance, crouch wind-up → power surge with both `power_claw` hands raised at chest/shoulder level, slight upward head tilt, `curious_o`. When `aura=True`, spawns animated glowing cyan `#3BE8FF` 3D lightning/aura curve arcs visible strictly on `[f0, f1]`. |
| 7 | `chill_chair_lean(hero, f0, f1, seat_z=0.42, *, loc=(0,0,0), yaw=0.0, build_chair=True, collection=None)` | **Exact Reference Image 7:** Reclines back in a sleek procedural 3D maroon/walnut studio chair (when `build_chair=True`, visible on `[f0, f1]`), both yellow-sleeved elbows flared wide with `behind_head` hands cradling the red beanie, crossed leg showing chunky sneaker sole toward camera, `chill_laugh`. |
| 8 | `talk_explain(hero, f0, f1, audio_path=None, *, loc=(0,0,0), yaw=0.0, base_expr="idle_cute")` | Natural conversational torso shifts and alternating two-hand beat gestures (`relaxed_curl` / `open_stop` / `point`); runs `hero.auto_lipsync(audio_path, f0, f1, base_expr=base_expr)` if `audio_path` is supplied, or procedural syllable visemes otherwise. |
| 9 | `point_at_camera_wink(hero, f0, f1, *, loc=(0,0,0), yaw=0.0, camera=None)` | Slight wind-up → snappy `point` hand aimed directly toward `camera` (or `-Y` front) with confident head tilt and `smug_wink` settled hold. |
| 10 | `shrug_idk(hero, f0, f1, *, loc=(0,0,0), yaw=0.0)` | Raises shoulders, spreads both `open_stop` palms outward/upward, tilts head, snaps `whatever_eyeroll`, then settles. |
| 11 | `jump_parabolic(hero, f0, f1, start_xyz, end_xyz, jump_height=0.55)` | Anticipation squash crouch at `start_xyz` → true parabolic ballistic arc peaking `+jump_height` above higher endpoint → impact squash knee-bend at `end_xyz` → crisp recovery to standing. |
| 12 | `celebrate_hype(hero, f0, f1, *, loc=(0,0,0), yaw=0.0)` | Joyful double-`fist` vertical victory hops with squash-and-stretch landings, lively drawstring bounce, and `hype_letsgo`. |
| 13 | `facepalm_groan(hero, f0, f1, *, loc=(0,0,0), yaw=0.0)` | Sharp inhale wind-up → `open_stop` hand slaps to brow/face followed by slow defeated torso slump and `ugh_groan`. |
| 14 | `take_hit_recoil(hero, f0, f1, from_side="L", *, loc=(0,0,0), yaw=0.0)` | Instant 3-frame impact jolt away from `from_side` (`"L"` or `"R"`), protective raised arms, `cringe_teeth`, damped slide-free recovery. |
| 15 | `phone_scroll_zombie(hero, f0, f1, *, loc=(0,0,0), yaw=0.0, collection=None)` | Hunched posture holding a built-in glowing 3D smartphone prop in `L` hand (auto-hidden outside `[f0, f1]`), repetitive `R` thumb flicks, `phone_zombie`. |
| 16 | `pickup_and_present(hero, f0, f1, prop_obj, *, loc=(0,0,0), yaw=0.0, side="R")` | Bends knees & reaches `side` hand to `prop_obj`'s starting world position → zero-slip socket grab → stands tall and presents `prop_obj` forward with `chill_laugh` / `hype_letsgo`. |
| 17 | `throw_prop_at(hero, f0, f1, prop_obj, target_xyz, *, loc=(0,0,0), yaw=0.0, side="R")` | Carries `prop_obj` in `side` socket through pitcher wind-up → releases cleanly on strike frame → keys unclipped ballistic arc + spin landing accurately on `target_xyz`. |
| 18 | `dramatic_double_take(hero, f0, f1, look_target, *, loc=(0,0,0), yaw=0.0)` | Casual brief glance toward `look_target` → casual return forward → delayed realization → ultra-fast 4-frame whip-snap back at `look_target` with shock stretch/squash and `mortified_blush`. |

---

## 8. Building & Rendering a New Mascot Short (`scripts/modal_blender.py`)

### Workflow
1. Copy `assets/mascot/starter_scene_template.py` to a new versioned folder `scripts/<short_name>/v01/build.py`.
2. Edit `END_FRAME`, `STORY_BEATS`, `CAMERA_SHOTS`, and custom 3D set dressing.
3. Run calibration stills or full render on **Modal L4 GPU** (recommended—keeps local PC GPU free and never touches `.blender_gpu.lock`) or locally via `.blender_gpu.lock`:

```powershell
# Modal GPU — 1-line build + calibration stills (downloads starter.blend + calibration/*.png):
modal run scripts/modal_blender.py --mode run --project <short_name>/v01 --script build.py --runner blender --script-args "--out {out}"

# Modal GPU — 1-line full 1080x1920 @ 30fps render + automatic H.264 MP4 encode (frames_h264.mp4):
modal run scripts/modal_blender.py --mode run --project <short_name>/v01 --script build.py --runner blender --script-args "--out {out} --render"

# Rebuild canonical mascot_master.blend on Modal GPU (only if modifying rig/costume):
modal run scripts/modal_blender.py --mode run --project assets/mascot --script build_mascot_asset.py --runner blender --out assets/mascot --overwrite

# Local GPU (ONLY when explicitly authorized; automatically acquires/releases .blender_gpu.lock):
python scripts/<short_name>/v01/build.py --out renders/<short_name>/v01 --render
```

### Post-Render QA Checklist (Local CPU)
```powershell
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=width,height,sample_aspect_ratio,r_frame_rate,pix_fmt,nb_read_frames -of json renders/<short_name>/v01/frames_h264.mp4
ffmpeg -nostdin -v error -xerror -i renders/<short_name>/v01/frames_h264.mp4 -f null -
python scripts/ricks_metrics_gate.py --edge-density renders/<short_name>/v01/calibration
python scripts/ricks_metrics_gate.py --cam-velocity renders/<short_name>/v01/frames_h264.mp4 renders/<short_name>/v01/cuts.json
```
