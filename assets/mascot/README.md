# Official Main Character Asset Package (`assets/mascot/`)

Reusable Blender 4.2 LTS (`BLENDER_EEVEE_NEXT`) 3D comic character package for vertical 9:16 Shorts (`1080 × 1920 @ 30 fps`): our **3-head-tall Chibi Mascot** (`≈ 1.28 m`) with a snow-white marshmallow head (`1.00 <= head_h / head_w <= 1.05`), `4°`-tilted crimson ribbed knit beanie, oversized cozy yellow hoodie with 3D hood collar, eyelets, swaying white drawstrings, kangaroo pocket, 7 swappable puffy white cartoon hands, charcoal lounge pants/shorts, and chunky sneakers planted flat at `Z = 0.000 m`.

> **Agents:** Read [`MASCOT_SKILL.md`](MASCOT_SKILL.md) before authoring any Short featuring the Mascot.

---

## Visual Previews (`assets/mascot/previews/`)

| Deliverable | Path | Description |
| :--- | :--- | :--- |
| **3 Hero Reference Poses** | [`previews/hero_3_reference_poses.png`](previews/hero_3_reference_poses.png) | `3240 × 1920` 3-panel showcase (`stop_hold_up`, `power_aura_stance`, `chill_chair_lean`) |
| **4-View Studio Turnaround** | [`previews/turnaround_4views.png`](previews/turnaround_4views.png) | Front, 3/4 Hero, 90° Profile, and Back turnaround showing 3D hood, beanie, pocket & sneakers |
| **18-Expression 3D Grid** | [`previews/expression_grid_18.png`](previews/expression_grid_18.png) | All 12 story expressions + 6 lip-sync visemes rendered on the 3D Mascot head |
| **15s 1080p Demo Reel** | [`previews/mascot_demo_reel_1080p.mp4`](previews/mascot_demo_reel_1080p.mp4) | `1080 × 1920`, `30 fps`, `450` frames continuous multi-zone showcase reel |

---

## 3-Line Python Quickstart

```python
from assets.mascot import mascot_api, anim_library
hero = mascot_api.load_mascot(scene.collection)
anim_library.stop_hold_up(hero, 1, 60)
```

Finish any multi-frame scene by updating screen-compensated `#141016` outlines per frame (`hero.update_ink(camera, frame=f)`) and calling `hero.finish_bake()`.

---

## 1-Line Modal GPU Commands (`scripts/modal_blender.py`)

`assets/mascot/` (`*.py`, `mascot_master.blend`, `expressions/**`) is bundled automatically in `CORE_PATTERNS` for every Modal job—no `--include` flag needed.

```powershell
# 1. Copy starter_scene_template.py to scripts/<new_short>/v01/build.py, edit STORY_BEATS & CAMERA_SHOTS, then build + render + H.264 encode on Modal L4 GPU:
modal run scripts/modal_blender.py --mode run --project <new_short>/v01 --script build.py --runner blender --script-args "--out {out} --render"

# 2. Fast build + calibration stills only (no full animation render):
modal run scripts/modal_blender.py --mode run --project <new_short>/v01 --script build.py --runner blender --script-args "--out {out}"

# 3. Smoke-test starter_scene_template.py directly on Modal GPU:
modal run scripts/modal_blender.py --mode run --project assets/mascot --script starter_scene_template.py --runner blender --script-args "--out {out}/starter_smoke --smoke"

# 4. Run full Mascot unit & animation test suite on Modal GPU:
modal run scripts/modal_blender.py --mode run --project assets/mascot --script tests/test_mascot.py --runner blender
```

---

## Package Layout

```text
assets/mascot/
├── __init__.py                 # Exports mascot_api & anim_library
├── mascot_master.blend         # Packed "MascotHero" collection (< 35k tris, 18 packed PNGs)
├── build_mascot_asset.py       # Deterministic procedural builder for mascot_master.blend
├── expression_gen.py           # 2x supersampled Pillow generator for all 18 1024x1024 decals
├── mascot_api.py               # MascotRig loader, IK pose, expressions, auto_lipsync, prop sockets, ink
├── anim_library.py             # 18 studio-polished S-curve animations with world-pinned stance feet
├── starter_scene_template.py   # ~120-line copy-and-edit 9:16 Short starter (local & Modal ready)
├── render_previews.py          # Modal GPU showcase renderer for previews/
├── MASCOT_SKILL.md             # Complete agent directing skill & API specification
├── README.md                   # Package overview, quickstart & tables
├── expressions/                # 12 story PNGs + visemes/ (6 lip-sync PNGs)
└── previews/                   # 3 proof sheets + 15s 1080x1920 demo reel MP4
```

---

## Coordinate & Rig Conventions

- **Forward Axis:** Local `-Y` (`yaw = 0.0` faces a camera placed at `-Y` looking toward `+Y`).
- **Left / Right Convention:** `L = -X` (viewer-left in front view), `R = +X` (viewer-right in front view), matching `scripts/ricks_v2_kit.py`.
- **Ground Contact Plane:** `Z = 0.000 m` — when `loc=(x, y, 0.0)` and `leg_L` / `leg_R` have `fz = 0.0`, chunky sneaker rubber soles rest flat on `Z = 0.000 m` with zero floor penetration.
- **Standing Pivots:** Total height `≈ 1.28 m`; `hero.body` at `(0, 0, 0.56)` relative to `hero.root`; `hero.head` at `(0, 0, 0.40)` relative to `hero.body` (`Z_center ≈ 0.96 m`); shoulders at `(∓0.155, 0.0, 0.18)` in `body`-local space.
- **Marshmallow Head Invariant:** `width_x = 0.440 m`, `depth_y = 0.400 m`, `height_z = 0.448 m` (`ratio = 1.018`, strictly within `1.00 <= height_z / width_x <= 1.05`).

---

## Expressions & Visemes (`12 + 6 = 18` Packed 1024×1024 Decals)

### 12 Story Expressions (`mascot_api.EXPRESSIONS`)

| # | Expression Name | File | Visual Description | Typical Beats |
| :- | :--- | :--- | :--- | :--- |
| 1 | `idle_cute` | `expressions/idle_cute.png` | Big glossy jet-black `#141016` oval eyes (`~6°` inward tilt) + `//` cheek ticks + tiny cute smile | Default idle, walks, calm beats |
| 2 | `curious_o` | `expressions/curious_o.png` | Big black oval eyes + `//` ticks + surprised/curious open `o` mouth (`#4A121B` interior + `#FF7B89` tongue) | `stop_hold_up` (Img 5), `power_aura_stance` (Img 6), `sneak_to` |
| 3 | `chill_laugh` | `expressions/chill_laugh.png` | Big black oval eyes + `//` ticks + wide happy `D` grin with white upper teeth bar `#FFFDFB` & coral tongue | `chill_chair_lean` (Img 7), relaxed payoffs |
| 4 | `hype_letsgo` | `expressions/hype_letsgo.png` | Wide excited eyes + bold brows + huge open hype mouth with teeth bar, tongue & action ticks | `celebrate_hype`, big wins |
| 5 | `cringe_teeth` | `expressions/cringe_teeth.png` | Squeezed `>` left eye + wide right eye + wide clenched teeth grid + cyan temple sweat drops | `take_hit_recoil`, awkward mishaps |
| 6 | `whatever_eyeroll` | `expressions/whatever_eyeroll.png` | Half-lidded upward eye-roll + unimpressed side air-puff mouth | `shrug_idk`, deadpan sarcasm |
| 7 | `phone_zombie` | `expressions/phone_zombie.png` | Droopy tired lids + under-eye bags + open `o` mouth with tiny drool drop + subtle cool-blue screen glow | `phone_scroll_zombie`, late-night doomscroll |
| 8 | `sulk_pout` | `expressions/sulk_pout.png` | Angled pouty brows + soft pink rosy cheeks + `hmph` pout mouth | Petty disappointment, sulking |
| 9 | `mortified_blush` | `expressions/mortified_blush.png` | Warm rosy-red embarrassed flush + wide shock eyes + wavy `~` mouth + sweat drops | `run_panic_to`, `dramatic_double_take` |
| 10 | `smug_wink` | `expressions/smug_wink.png` | Smooth `—` wink on one eye + confident open eye + cocky smirk | `point_at_camera_wink`, clever punchlines |
| 11 | `crush_hearts` | `expressions/crush_hearts.png` | Glowing pink heart highlights inside big black oval eyes + rosy `///` blush + `:3` cat mouth | Adoration, shiny treasure/food reveal |
| 12 | `ugh_groan` | `expressions/ugh_groan.png` | Tightly squeezed `> <` eyes + tall dramatic groan mouth with long sticking-out coral-pink tongue | `facepalm_groan`, exasperation |

### 6 Lip-Sync Visemes (`mascot_api.VISEMES`)

| Viseme Name | File | Mouth Shape / Phoneme Group |
| :--- | :--- | :--- |
| `vis_closed` | `expressions/visemes/vis_closed.png` | Closed / bilabial rest (`M`, `B`, `P`, micro-pauses) with iconic black oval eyes + `//` ticks |
| `vis_AA` | `expressions/visemes/vis_AA.png` | Wide open vowel (`AA`, `AH`, `AY` — high RMS open jaw with tongue) |
| `vis_EE` | `expressions/visemes/vis_EE.png` | Wide horizontal smile-vowel (`EE`, `IH`, `EY`, `S`, `Z` — upper teeth visible) |
| `vis_OH` | `expressions/visemes/vis_OH.png` | Rounded medium-tall vowel (`OH`, `AW`, `OR`) |
| `vis_OO` | `expressions/visemes/vis_OO.png` | Tight small rounded vowel (`OO`, `UW`, `W`, `Q`) |
| `vis_FV` | `expressions/visemes/vis_FV.png` | Labiodental / fricative (`F`, `V`, `TH` — upper teeth touching lower lip) |

---

## Hand Poses & Prop Sockets (`mascot_api.HAND_POSES`)

| Hand Pose Name | Silhouette & Finger Layout | Signature Use |
| :--- | :--- | :--- |
| `relaxed_curl` | Cute puffy 4-finger cartoon mitt in natural relaxed curl | Default idle, walks, general acting |
| `open_stop` | Big expressive 5-finger spread palm facing outward | `stop_hold_up` (Reference Image 5), `shrug_idk`, `facepalm_groan` |
| `power_claw` | Dramatic upturned curled tension fingers | `power_aura_stance` (Reference Image 6) |
| `fist` | Plump clenched cartoon fist | `celebrate_hype`, `jump_parabolic`, punchy emphasis |
| `point` | Crisp index-finger point with curled fingers | `point_at_camera_wink`, directing viewer eye-line |
| `thumbs_up_ok` | Upbeat cartoon thumbs-up / approval mitt | Approval beats, `pickup_and_present` |
| `behind_head` | Smooth tucked mitt contoured to cradle behind the red beanie | `chill_chair_lean` (Reference Image 7) |

- **Zero-Slip Prop Sockets:** `hero.hand_socket_L` and `hero.hand_socket_R` sit at the exact palm centers. Call `hero.attach_prop(prop_obj, side="R", f_start=1, f_end=100, offset=(0,0,0), rot_euler=(0,0,0))` for `0.000 m` world-pinned grips across `[f_start, f_end]`.

---

## `mascot_api.py` Reference

| Function / Method | Exact Signature | Behavior |
| :--- | :--- | :--- |
| `load_mascot` | `load_mascot(collection, name="Mascot", bottom_style="pajamas", arm_style="hoodie") -> MascotRig` | Appends `"MascotHero"` from `mascot_master.blend` (or builds procedurally if absent); supports `"pajamas"`/`"shorts"` and `"hoodie"`/`"stick"`, plus multiple named instances. |
| `hero.pose` | `hero.pose(frame, loc=(0,0,0), yaw=0.0, body_tilt=0.0, body_roll=0.0, bounce=0.0, squash=1.0, head_yaw=0.0, head_pitch=0.0, head_roll=0.0, arm_L=None, arm_R=None, leg_L=None, leg_R=None, hand_L="relaxed_curl", hand_R="relaxed_curl", hand_rot_L=None, hand_rot_R=None, foot_rot_L=None, foot_rot_R=None, string_sway=None, expr=None)` | Applies (`frame=None`) or keyframes (`frame=int`) full-body IK pose, hand swaps, drawstring sway, and expression. `arm_L/R` in `body`-local `(hx,hy,hz)` or `((hx,hy,hz),(ex,ey,ez))`; `leg_L/R` in `root`-local `(fx,fy,fz)` or `((fx,fy,fz),(kx,ky,kz))` (`fz=0.0` = flat sole on `root.z`). |
| `hero.set_expression` | `hero.set_expression(expr_name, frame=None)` | Instant 1-frame `CONSTANT` visibility snap across all 18 story expressions & visemes. |
| `hero.auto_lipsync` | `hero.auto_lipsync(audio_path, start_frame, end_frame, base_expr="idle_cute", fps=30)` | Decodes WAV/MP3 via `wave`/`ffmpeg`, computes RMS + zero-crossing rate, keys `CONSTANT` visemes during speech, and restores `base_expr` on silence. |
| `hero.attach_prop` | `hero.attach_prop(prop_obj, side="R", f_start=1, f_end=100, offset=(0,0,0), rot_euler=(0,0,0))` | World-pins `prop_obj` to `hand_socket_R` or `hand_socket_L` over `[f_start, f_end]` (`< 1e-4 m` error). |
| `hero.update_ink` | `hero.update_ink(camera, frame=None, pixels=4.2)` | Compensates `#141016` inverted-hull outline thickness for camera distance & focal length. |
| `hero.head_bbox_ratio` | `hero.head_bbox_ratio() -> dict` | Returns `{"width_m", "depth_m", "height_m", "ratio"}` and verifies `1.00 <= ratio <= 1.05`. |
| `hero.finish_bake` | `hero.finish_bake()` | Enforces `CONSTANT` interpolation on expression/hand visibility swaps and clean linear/baked motion curves. |

---

## `anim_library.py` — All 18 Studio Animations

| # | Function & Exact Signature | Summary |
| :- | :--- | :--- |
| 1 | `idle_breathe(hero, f0, f1, *, loc=(0,0,0), yaw=0.0, expr="idle_cute")` | Subtle chibi chest breathing, gentle head micro-bob, planted sneakers, calm `idle_cute`. |
| 2 | `walk_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="idle_cute")` | World-pinned stance feet (`0.000 m` skating), bouncy chibi stride, opposite-phase sleeve swing & string bounce. |
| 3 | `run_panic_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="mortified_blush")` | Forward-leaning fast stride, flailing raised `open_stop` hands, heavy drawstring whip, `mortified_blush`. |
| 4 | `sneak_to(hero, f0, f1, start_xy, end_xy, *, ground_z=0.0, expr="curious_o")` | Hunched tiptoe gait, tucked elbows, left-right cautious head peeks, `curious_o`. |
| 5 | `stop_hold_up(hero, f0, f1, *, loc=(0,0,0), yaw=0.0)` | **Ref Image 5:** Lean back + viewer-left `arm_L` thrust toward `-Y` lens with big `open_stop` palm, `curious_o`. |
| 6 | `power_aura_stance(hero, f0, f1, aura=True, *, loc=(0,0,0), yaw=0.0, collection=None)` | **Ref Image 6:** Heroic wide stance, raised `power_claw` hands, `curious_o` + animated cyan `#3BE8FF` lightning arcs on `[f0, f1]`. |
| 7 | `chill_chair_lean(hero, f0, f1, seat_z=0.42, *, loc=(0,0,0), yaw=0.0, build_chair=True, collection=None)` | **Ref Image 7:** Reclined in sleek 3D studio chair, `behind_head` hands cradling beanie, crossed sneaker sole, `chill_laugh`. |
| 8 | `talk_explain(hero, f0, f1, audio_path=None, *, loc=(0,0,0), yaw=0.0, base_expr="idle_cute")` | Two-hand conversational beat gestures + `auto_lipsync` (with `audio_path`) or rhythmic viseme cycling. |
| 9 | `point_at_camera_wink(hero, f0, f1, *, loc=(0,0,0), yaw=0.0, camera=None)` | Anticipation wind-up → snappy `point` at camera/lens + head tilt + `smug_wink` settled hold. |
| 10 | `shrug_idk(hero, f0, f1, *, loc=(0,0,0), yaw=0.0)` | Raised shoulders + wide upturned `open_stop` palms + tilted head + `whatever_eyeroll`. |
| 11 | `jump_parabolic(hero, f0, f1, start_xyz, end_xyz, jump_height=0.55)` | Anticipation crouch → ballistic parabolic jump arc → squash knee-bend landing & clean settle. |
| 12 | `celebrate_hype(hero, f0, f1, *, loc=(0,0,0), yaw=0.0)` | Double-`fist` joyful victory hops, energetic drawstring bounce, `hype_letsgo`. |
| 13 | `facepalm_groan(hero, f0, f1, *, loc=(0,0,0), yaw=0.0)` | Hand slap to brow/face + exasperated torso slump + `ugh_groan`. |
| 14 | `take_hit_recoil(hero, f0, f1, from_side="L", *, loc=(0,0,0), yaw=0.0)` | Snappy impact knockback away from `from_side` (`"L"` or `"R"`), squash recovery, `cringe_teeth`. |
| 15 | `phone_scroll_zombie(hero, f0, f1, *, loc=(0,0,0), yaw=0.0, collection=None)` | Hunched holding built-in glowing 3D smartphone in `L` hand (`[f0, f1]`), `R` thumb scroll, `phone_zombie`. |
| 16 | `pickup_and_present(hero, f0, f1, prop_obj, *, loc=(0,0,0), yaw=0.0, side="R")` | Crouch & reach to `prop_obj` → exact `0.000 m` socket grab → rise & proudly present with `hype_letsgo`/`chill_laugh`. |
| 17 | `throw_prop_at(hero, f0, f1, prop_obj, target_xyz, *, loc=(0,0,0), yaw=0.0, side="R")` | Held in hand → wind-up → release → clean ballistic arc landing squarely on `target_xyz`. |
| 18 | `dramatic_double_take(hero, f0, f1, look_target, *, loc=(0,0,0), yaw=0.0)` | Calm glance → look away → rapid snap whip toward `look_target` with shock squash + `mortified_blush`. |
