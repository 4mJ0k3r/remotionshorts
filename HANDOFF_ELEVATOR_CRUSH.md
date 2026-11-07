# HANDOFF — `ElevatorCrushShort` (Remotion 2.5D story short)

> Handoff for the next AI agent. Read `animated-3d-story-video/SKILL.md` (Master Weaker-Model-Proof Edition v7) FIRST — this file only records project-specific state. **Obey all 4 Hard Speed & Budget Caps in SKILL.md.**

---

## 1. ORIGINAL TASK (what the user asked for)

Build & verify a brand-new full reel **`ElevatorCrushShort`** in `src/videos/elevator_crush/`, registered in `src/Root.tsx`, outputting to `out/elevator_crush/`.

- **Specs:** `1080x1920`, `30 fps`, `TOTAL = 3345` frames (111.5 s). Composition id **`ElevatorCrushShort`**.
- **Audio:** mount `<Audio src={staticFile("elevator_crush/audio.mp3")} />` in `ElevatorCrush.tsx` (audio already copied).
- **Shared files:** copy `pen.ts`, `ink.ts`, `lensblur.ts`, `grade.ts`, `cardshade.ts` (head chin UV `v ~ 0.62`), `shade.ts` from `src/videos/coaster/` (+ `paint.ts` is also needed for `makeBlobTexture`).
- **Story:** Coaching-student hero + his crush get stuck in a coaching-centre elevator for 3 hours. 11 scenes synced to real Hindi audio, cliffhanger ending (mystery number `"98XXXXXX??"` written on his palm → "COMMENT PART 2").
- **Hard Speed Caps (v7):**
  1. Run framing check `scripts/ec_frame.mjs` **at most 2 times** (never rewrite the checker to chase 1% grazes).
  2. Render **at most 2 still batches** — ALL 11 calibration frames in ONE `bridge-stills.mjs` command.
  3. Render the video **once** on the discrete GPU (never kill mid-render unless < 180 frames/min).
  4. Never render 1080p without permission — stills/video at scale `0.5`.
- **Lighting rule (Rule 9):** every shot `0.38 <= luma <= 0.65`. "Power cut" = Amber-Crimson emergency glow (`~0.44`); "blackout embrace" = Twilight-Violet / Neon Pink-Crimson rim (`~0.41–0.46`). **NEVER pitch black.**
- **No wooden easels/poster boards on sticks** (Rule 6). Status callouts = top HTML HUD pills.
- **FOV strictly 40–50°**, continuous `glide()` + `pushK` drift, held frames ≤ 2%.

---

## 2. WHAT HAS BEEN DONE (current state on disk)

### Created directories
- `src/videos/elevator_crush/`
- `public/elevator_crush/`
- `out/elevator_crush/` (currently EMPTY — no stills/video/QA yet)

### Audio (DONE)
- Copied `D:\remotionshorts\crushpart1.MP3` → `public/elevator_crush/audio.mp3` (2,682,721 bytes). ✅

### Shared shader/post files copied from `src/videos/coaster/` (DONE)
- `pen.ts`, `ink.ts`, `lensblur.ts`, `grade.ts`, `shade.ts` — copied verbatim. ✅
- `cardshade.ts` — copied **and edited**: head chin UV changed from coaster's `smoothstep(0.53, 0.565, vMapUv.y)` to **`smoothstep(0.60, 0.64, vMapUv.y)`** (head center y=235 → v=0.765, chin y≈380 → v≈0.62). ✅
- `paint.ts` — **REWRITTEN fresh** (coaster's `paint.ts` did NOT export `makeBlobTexture`, which `cast.ts` needs). New exports:
  - `tex`, `makeSteelTexture`, `makeWoodTrimTexture`, `makeBrassTexture`, `makeRainWindowTexture`, `redrawRainWindow(tex, seed)`, `makeLEDTexture() => { tex, redraw(text, flash) }`, `makePanelLabelTexture`, `makeCableTexture`, `makeBlobTexture`. ✅

### Story-specific files written (DONE)
- **`lights.ts`** — 8 presets for the 8 moods: `amberCyan` (S1), `rainy` (S2), `emergency` (S3–6), `violetRim` (S7), `heartbeat` (S8), `goldWarm` (S9), `roseGold` (S10), `neon` (S11). Exports `LIGHTS`, `LOOK`, `LightName`, `LightPreset`, `WorldLook`. All tuned toward Rule 9 luma. ✅
- **`story.ts`** — `FPS=30`, `TOTAL=3345`, `SHOTS` (all 11 with exact a/b/light/desc), `shotAt`, `layersAt`, `clamp01`, `glide`, `lerp`, `v3Lerp`, `pushK`, beat constants (`DOORS_AT=90`, `RAIN_IN_AT=285`, `RAIN_BURST_AT=310`, `BHDAM_AT=486`, `PHONE_AT=780`, `COUGH_AT=1248`, `GROWL_AT=1355`, `CABLE_AT=1665`, `DROP_AT=1710`, `HUG_AT=1885`, `HEART_AT=1980`, `LIGHTS_BACK_AT=2480`, `SPARKLE_AT=2720`, `WRITE_AT=3020`, `PALM_AT=3150`, `END_AT=3344`), `KICKS` (486, 1355, 1665, 1710), `kickOffset`, `camAt` (all 11 camera paths from the mission), `dofAt`. ✅

### NOT YET DONE (see §3)
- `toon.ts`, `build.ts`, `world.ts`, `cast.ts`, `ElevatorCrush.tsx` — **not written**.
- `src/Root.tsx` — **NOT registered yet** (grep for `Elevator` returns nothing).
- `scripts/ec_frame.mjs` — **not written**.
- `tsc`, stills, video, `shots.json`, `short_qa.py`, report — **not run**.

---

## 3. WHAT'S NEXT (exact remaining work, in order)

### Stage 1 — finish code + typecheck (DO THIS FIRST)
1. **Write `toon.ts`** — 600×1000 design box, `SU=0.00216`, `PIV=975`, soles y=952, cream head `#fdfaf2`, `HEAD_R=145` at `(300,235)`, ink `#351f22`, compact bean torso width ~135, parallel legs at x=265 & 335, **solid dark oval pupils, ZERO white anime shine dots**. Two roles:
   - **`hero`** (coaching student): snug red knit beanie `#d62828` (cuff above y<85), warm-yellow tee/hoodie `#f4b942`, dark backpack straps, dark trousers. Continuous params: `btnPressP` (closed fist at **dx=145, dy=565** — Rule B pin), `phoneP` ("NO SERVICE ❌" clear of face), `heartBeatP` (chest icon pulse + red waves), `growlP` (hands clutch stomach + neon-green "GURRRR!" + blush), `comfortP` (hands on Crush shoulders), `palmP` (open palm with glowing cyan `"98XXXXXX??"`).
   - **`crush`**: dark-brown shoulder-length hair + hairband/clips, pastel-pink/lavender rain jacket `#e56b6f`/`#b56576` over white top. Params: `rainDrops` (bool → blue droplet sparkle), `fixHairP` (twirl lock + side-glance), `phoneP`, `hugP` (arms around neck/chest + pink blush), `writePalmP` (lean in, hold hero's hand, write).
   - Also export `drawFx` (dust/sparks/sparkle/heart) and `drawFxBlob`, matching `cast.ts` expectations.
2. **Write `build.ts`** — 2 isolated `THREE.Group` sets, clean architecture (NO easels):
   - `SET_CORRIDOR_LIFT` (Shot 2): hallway, rain-streaked glass window left (use `makeRainWindowTexture`/`redrawRainWindow`), open stainless-steel elevator doorway with sliding 3D doors (`doorGap` animated).
   - `SET_ELEVATOR_CABIN` (Shots 1, 3–11): brushed-steel + warm-wood-trim cabin `width=4.6, depth=4.2, height=3.8`; sliding metallic front doors at `z=-1.8`; red LED indicator `"FLOOR 4 / STUCK"` high above doors at `y=2.95` (use `makeLEDTexture`); right-side brushed-brass control panel with illuminated 3D floor buttons `1,2,3,4,G,FAN` (for Rule B pinning); overhead ceiling light panel + openable upper cable-shaft grate at `y=3.5` revealing steel hoist cables that fray/spark (S7).
   - Expose refs needed by `world.ts` (e.g. door meshes, LED redraw handle, cable meshes, button panel position, rain window texture).
3. **Write `world.ts`** — mirror `hotel_lift/world.ts` structure: `root`, sky sphere (NOINK), hemi+sun, `buildSets()`, `update(id,f,cam,scene)` toggles set visibility exclusively (`setGroup.visible = (shotId === k)`), animates doors/LED/cables/rain, pins the 3D brass `"FLOOR 4 / FAN"` knob to hero's 2D fist via **Rule B** (`handWorldPos(cam.position, charPos, scale, dx=145, dy=565, depthOffset=-0.08)`), stages actors + FX, syncs `TONE`/`CHAR` uniforms from `LIGHTS`.
4. **Write `cast.ts`** — copy `hotel_lift/cast.ts` (Pool/Actor/Fx/stage/handWorldPos) and adapt: `SU`, `PIV`, quantization `q2`, `makeChar` (quantize ALL new params), `blob`, and `stage(id,t,cam)` implementing every shot's staging (positions, expressions, action params, FX bursts at the beat frames). Reuse `handWorldPos` exactly (Rule B).
5. **Write `ElevatorCrush.tsx`** — copy `hotel_lift/HotelLift.tsx` structure:
   - Post chain in exact order: `InkPass -> LensBlur.pre -> LensBlur.main -> Bloom -> ToneMapping(NEUTRAL) -> Grade`.
   - `GRADE_OF` map per light (e.g. amberCyan→"warm", rainy→"twilight", emergency→"alarm", violetRim→"night", heartbeat→"alarm"/"warm", goldWarm→"warm", roseGold→"warm", neon→"twilight"). **Verify these grade preset keys exist in `grade.ts` `GRADES`** (has vivid/day/golden/warm/clinic/night/twilight/bath/bank/alarm).
   - Mount `<Audio src={staticFile("elevator_crush/audio.mp3")} />`.
   - Accept `{ subs?: boolean }` prop (default true).
   - **Top HUD pill** per shot (see §4 table), styled like SKILL Rule 6: `top: 10%`, `background: rgba(22,18,34,0.86)`, `border: 2px solid rgba(255,255,255,0.2)`, `borderRadius: 999`.
   - **Bottom single-line subtitles** at `bottom: 18%`, bold white sans, thick `#1a1214` outline, 4-frame `#d8d8d8 -> #ffffff` luma ease, ONE line only (see §4 cues).
   - Export `ELEVATOR_CRUSH_FRAMES = TOTAL`.
6. **Register in `src/Root.tsx`**: `import { ElevatorCrushShort, ELEVATOR_CRUSH_FRAMES } from "./videos/elevator_crush/ElevatorCrush";` + `<Composition id="ElevatorCrushShort" component={ElevatorCrushShort} durationInFrames={ELEVATOR_CRUSH_FRAMES} fps={30} width={1080} height={1920} />`.
7. **Run `npx tsc --noEmit`** and fix until exit 0. Do NOT render if TS errors.
8. **Write `scripts/ec_frame.mjs`** (copy `scripts/hl_frame.mjs`, adapt `pts()` to all 11 shots + `camAt`), run **≤ 2 times** on frames like `100,320,500,800,1050,1380,1720,1950,2350,2700,3150`. Accept ≤5% grazes in writing.

### Stage 2 — ONE still batch (≤ 2 total)
- Render ALL 11 frames in ONE command with subs off:
  ```
  $env:BRIDGE_ID="ElevatorCrushShort"; $env:BRIDGE_PROPS='{"subs":false}'; node scripts/bridge-stills.mjs out/elevator_crush/cal_v1/ 100,320,500,800,1050,1380,1720,1950,2350,2700,3150 0.5
  ```
- Tile: `python scripts/coaster_sheet.py out/elevator_crush/cal_v1/ 100,320,500,800,1050,1380,1720,1950,2350,2700,3150 out/elevator_crush/sheet_v1.jpg 4`
- Inspect `sheet_v1.jpg` against the 9-point checklist (cream heads, solid pupils, Rule B button contact S5, no easels, luma 0.38–0.65, distinct angles, props in-card, structures in-frame, single subtitle line). Fix ALL defects in ONE consolidated edit; optional ONE confirmation batch (`sheet_v2.jpg`).

### Stage 3 — ONE video render (discrete GPU, never kill mid-way)
```
$env:BRIDGE_ID="ElevatorCrushShort"; node scripts/bridge-video.mjs out/elevator_crush/elevator_crush_v1.mp4 0 3344 0.5
```
(uses `src/index.ts` entry, ANGLE/Chrome, h264, audio from composition). Expect ≥ 250 frames/min.

### Stage 4 — QA gate
- Write `out/elevator_crush/shots.json`: `{"shots":[{"id":1,"a":0,"b":210}, ... 11 ...], "planned":[[...cut/kick/subtitle cue windows...]]}` (declare hard cuts, KICKS, expression swaps, subtitle transitions).
- Run: `python scripts/short_qa.py out/elevator_crush/elevator_crush_v1.mp4 out/elevator_crush/qa out/elevator_crush/shots.json`
- Pass: black `[]`, unplanned white `[]`, frozen `[]`, unplanned pops `[]`, held ≤ 3%, per-shot luma `0.38–0.68`.
- Inspect ≥ 2 `qa/sheet_*.jpg` with vision tool.
- Write `out/elevator_crush/elevator_crush_report.md` (summary + any accepted grazes).

---

## 4. REFERENCE SPEC TABLES (paste-ready for `cast.ts` / `ElevatorCrush.tsx`)

### Shot table (frames / light / HUD pill)
| # | a..b (excl) | time | light | HUD pill |
|---|---|---|---|---|
| 1 | 0..210 | 0–7.0s | amberCyan | `😱 TRAPPED WITH CRUSH • 03:00:00` |
| 2 | 210..405 | 7.0–13.5s | rainy | `🌧️ 1 SEC BEFORE CLOSING!` |
| 3 | 405..660 | 13.5–22.0s | emergency | `⚡ POWER CUT • STUCK AT FLOOR 4!` |
| 4 | 660..906 | 22.0–30.2s | emergency | `📵 HOUR 1 • ZERO NETWORK` |
| 5 | 906..1170 | 30.2–39.0s | emergency | `💀 ACTING NATURAL: 0%` |
| 6 | 1170..1524 | 39.0–50.8s | emergency | `😭 STOMACH GROWLED IN SILENCE!` |
| 7 | 1524..1818 | 50.8–60.6s | violetRim | `⚠️ HOUR 2 • CABLE SLIPS 2 FEET!` |
| 8 | 1818..2196 | 60.6–73.2s | heartbeat | `❤️ HEART RATE: 160 BPM!` |
| 9 | 2196..2466 | 73.2–82.2s | goldWarm | `🔥 'जब तक मैं हूँ, तुम्हें कुछ नहीं होगा'` |
| 10 | 2466..2835 | 82.2–94.5s | roseGold | `✨ AWKWARDNESS: 0% • EYE CONTACT` |
| 11 | 2835..3345 | 94.5–111.5s | neon | `👇 COMMENT 'PART 2' NOW! 🔥` (pulses from f=3206) |

### Camera paths (already in `story.ts` `CAMS`)
1 `[-1.2,1.55,4.5]→[-0.6,1.48,3.6]` look `[0,1.4,1.3]` fov46 · 2 `[1.5,1.5,4.8]→[0.8,1.45,3.7]` look `[0,1.35,1.2]` fov46 · 3 `[-0.9,1.15,4.1]→[-0.5,1.25,3.4]` look `[0,1.55,1.2]` fov48 · 4 `[0,1.5,4.9]→[0.35,1.42,3.9]` look `[0,1.35,1.4]` fov48 · 5 `[-1.35,1.48,3.8]→[-0.85,1.42,3.1]` look `[0.25,1.35,1.3]` fov45 · 6 `[0.85,1.75,3.6]→[0.55,1.55,2.85]` look `[0,1.25,1.4]` fov44 · 7 `[0,1.1,4.3]→[0,1.25,3.6]` look `[0,1.85,1.2]` fov48 · 8 `[-1.1,1.48,3.6]→[-0.65,1.44,2.75]` look `[0,1.38,1.5]` fov43 · 9 `[0.95,1.52,3.1]→[0.65,1.48,2.55]` look `[-0.1,1.42,1.5]` fov42 · 10 `[-0.95,1.46,3.2]→[-0.6,1.44,2.65]` look `[0.05,1.42,1.5]` fov42 · 11 `[0,1.52,3.8]→[0,1.48,2.6]` look `[0,1.42,1.5]` fov44.

### Subtitle cues (exact, single-line, `bottom: 18%`)
```
0..104      सोचो अगर शाम की कोचिंग के बाद,
105..209    तुम और तुम्हारी क्रश 3 घंटों के लिए लिफ्ट में फँस जाओ!
210..305    बाहर तेज़ बारिश है, तुम लिफ्ट में अकेले हो...
306..404    और दरवाज़ा बंद होने से 1 सेकंड पहले वो अंदर आती है!
405..485    अभी तुम अपनी धड़कनें संभाल ही रहे होते हो
486..570    कि अचानक—भड़ाम! पूरी बिल्डिंग की लाइट कट जाती है,
571..659    और लिफ्ट चौथे फ्लोर के बीचों-बीच अटक जाती है!
660..775    पहला घंटा... भाई, एकदम जानलेवा ऑकवर्डनेस!
776..905    पिन-ड्रॉप साइलेंस है, और फ़ोन में नेटवर्क ज़ीरो।
906..1030   वो एक कोने में खड़ी अपने बाल ठीक कर रही है,
1031..1169  और तुम दूसरे कोने में फ्लोर बटन्स घूर रहे हो!
1170..1310  तुम कुछ बोलने के लिए मुँह खोलते हो, पर गला सूख जाता है।
1311..1420  ऊपर से खाली पेट में ज़ोर से गुड़गुड़ होती है—
1421..1523  लगता है धरती फट जाए और तुम समा जाओ!
1524..1664  तभी दूसरा घंटा... और केबल से आवाज़ आती है—खड़-खड़-खड़!
1665..1817  लिफ्ट 2 फीट नीचे खिसकती है और इमरजेंसी लाइट भी बंद!
1818..1995  डर से वो दौड़कर सीधा तुम्हारे सीने से लिपट जाती है!
1996..2195  तुम्हारे दिल की धड़कन सीधा उसके कानों में सुनाई देती है।
2196..2330  तुम काँपते हाथों से उसके कंधे को थामते हो—
2331..2465  'डरो मत, सेफ्टी ब्रेक्स लॉक हैं। तुम्हें कुछ नहीं होगा।'
2466..2630  5 सेकंड बाद डिम लाइट आती है, पर वो तुम्हें नहीं छोड़ती।
2631..2834  वो तुम्हारी आँखों में देखती है और ऑकवर्डनेस गायब!
2835..3020  पर असली खेल अब शुरू होता है—वो एक राज़ खोलने वाली है,
3021..3205  और तुम्हारी हथेली पर कुछ ऐसा लिखकर जाएगी कि होश उड़ जाएँगे!
3206..3344  आगे जानने के लिए अभी कमेंट करो 'PART 2' और फॉलो कर लो!
```

### Staging / action beats per shot (summary)
- **S1:** hero `[-0.55,0,1.4]` `panicShock`; crush `[0.55,0,1.2]` soft pink aura. Doors slide shut f0..90.
- **S2:** hero `[-0.5,0,1.0]`; at f=285 doors bounce open, crush `x 1.2→0.45, z=1.3`, `rainDrops=true`, `fxImpact` sparkle f=310; hero jaw drop `panicShock`.
- **S3:** heartBeatP f405..484; at f=486 heavy shake (`KICKS`), orange spark burst, both jolt +0.18m, emergency glow, LED flashes `"FLOOR 4 • STUCK ⚡"`.
- **S4:** hero `[-0.75,0,1.4]`, crush `[0.75,0,1.4]` at opposite walls, temple sweat; f780..905 both raise phones `phoneP 0→1` "NO SERVICE ❌".
- **S5:** crush `[-0.65,0,1.6]` `fixHairP 0→1`; hero `[0.55,0,1.3]` leans to right brass panel, `btnPressP` fist pinned via Rule B `depthOffset=-0.08` to `"FLOOR 4 / FAN"` knob.
- **S6:** hero `[0.2,0,1.5]` tight, crush `[-0.7,0,1.1]` bg. f=1248 cough dust puff; f=1355 `growlP 0→1` green "GURRRR!" + `KICKS`, purple/red blush, crouch.
- **S7:** overhead cable grate vibrates; f=1665 sparks (`fxImpact`) + `KICKS`; f=1710 drop `KICKS`, both bounce +0.25m `panicShock`, violet-crimson rim.
- **S8:** f1818..1890 crush runs `x 0.65→0.18` into hero chest `x=-0.15,z=1.5`, `hugP 0→1`, pink heart burst f=1885; f1980..2195 `heartBeatP=1` red pulse rings, frozen blushed hero.
- **S9:** `comfortP 0→1` hands on crush shoulders, hero `confidentSmile`, golden star particles.
- **S10:** dim light returns f=2480, `hugP=1`, crush lifts head soft blush `confidentSmile`, golden sparkles f=2720.
- **S11:** f2835..3020 crush `writePalmP 0→1` cyan question/secret aura; f3021..3205 hero `palmP 0→1` palm `"98XXXXXX??"`, `panicShock`→`confidentSmile` + `cyanEyes=true` f=3150, `fxImpact`; f3206..3344 both point/wave at viewer, golden sparkles, HUD pulses.

---

## 5. KEY GOTCHAS / NOTES FOR NEXT AGENT
- **`paint.ts` was intentionally rewritten** (not copied verbatim) because `cast.ts` imports `makeBlobTexture`. Keep that export.
- **`cardshade.ts` chin UV already fixed** to `smoothstep(0.60,0.64,...)` — do not revert to coaster's 0.53/0.565.
- **`lights.ts` grade keys**: the `GRADE_OF` map in `ElevatorCrush.tsx` must map light names to presets that exist in `grade.ts` `GRADES` (`vivid/day/golden/warm/clinic/night/twilight/bath/bank/alarm`).
- **Rule B pinning** (S5) is the only hand-to-3D-prop contact: `dx=145, dy=565`, `depthOffset=-0.08`; place the 3D brass knob at `handWorldPos(...)` every frame.
- **Set isolation** is mandatory: toggle `setCorridor.visible=(id===2)`, `setCabin.visible=(id!==2)`.
- **Speed discipline:** do NOT loop the frame checker or still batches. Fix everything in one pass.
- Windows shell is **PowerShell** — `&&` does not work; use `;` or separate commands. `ls -la` is invalid (use `Get-ChildItem`). Prefer `Get-ChildItem`, `Select-String`.
- Build/render scripts use `BRIDGE_ID`, `BRIDGE_PROPS`, `REMOTION_TMP=D:/remotion-tmp`, Chrome ANGLE.
- Audio is Hindi; subtitle cues above are the authoritative timing.

## 6. FILE MANIFEST (expected final)
```
src/videos/elevator_crush/
  pen.ts ink.ts lensblur.ts grade.ts cardshade.ts shade.ts paint.ts   (shared, DONE)
  lights.ts story.ts                                                   (DONE)
  toon.ts build.ts world.ts cast.ts ElevatorCrush.tsx                  (TODO)
scripts/ec_frame.mjs                                                   (TODO)
src/Root.tsx                                                           (register TODO)
public/elevator_crush/audio.mp3                                        (DONE)
out/elevator_crush/
  cal_v1/*.jpg sheet_v1.jpg                                           (TODO)
  elevator_crush_v1.mp4                                               (TODO)
  shots.json qa/* elevator_crush_report.md                            (TODO)
```
