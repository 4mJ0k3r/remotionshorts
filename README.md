# remotionshorts

A **Remotion + Three.js 2.5D vertical story-animation engine** (1080x1920 @ 30 fps).

Real 3D sets are built in `three.js` via `@remotion/three`, `@react-three/fiber` and `@react-three/postprocessing`. They are drawn with ink outlines, thin-lens depth of field, bloom and a display-referred colour grade. The characters are 2D cartoon cards drawn procedurally on canvas each frame and placed in the 3D world as yaw-billboards. Each short is a self-contained module under `src/videos/<name>/`.

The repo is meant to be cloned, run and upgraded by another developer or AI agent. Start with the skill file and the manifest below.

## Where the docs are

| File | What it is |
|---|---|
| [`animated-3d-story-video/SKILL.md`](animated-3d-story-video/SKILL.md) | **The skill (Master Weaker-Model-Proof Edition v7).** Module architecture, character spec, hand-to-3D-prop contact law, camera/DOF rules, the 4-stage build workflow, the hard speed/budget caps and the visual rules. Read this first. |
| [`PROJECT_MANIFEST.md`](PROJECT_MANIFEST.md) | Architecture brief: runtime stack, render call path, numeric conventions, toolchain, privacy constraints. |
| [`HANDOFF_ELEVATOR_CRUSH.md`](HANDOFF_ELEVATOR_CRUSH.md) | Handoff notes from building `ElevatorCrushShort` (historical, shows the workflow in practice). |

## Modules (`src/videos/`)

Composition IDs are registered in `src/Root.tsx`.

| Folder | Composition ID | What it is |
|---|---|---|
| `coaster` | `CoasterShort` | 10 s roller-coaster benchmark. **Calibrated baseline.** New shorts copy the shared render files from here. |
| `tower_jump`, `tower_qwen` | `TowerJumpShort`, `TowerQwenShort` | 10 s London Tower Bridge bus-jump benchmark (two variants). |
| `hotel_lift` | `HotelLiftShort` | 10 s 1861 Chicago hotel-lift benchmark. |
| `molasses_tank` | `MolassesTankShort` | 10 s 1919 Boston molasses-flood benchmark. |
| `instant_skill` | `InstantSkillShort` | ~124 s full reel (3714 frames). |
| `elevator_crush` | `ElevatorCrushShort` | 111.5 s full reel (3345 frames). Hindi voiceover, 11 shots, cliffhanger ending. |
| `bridge`, `pardon`, `age18`, `school` | `BridgeShort`, `PardonShort`, `Age18Short`, `SchoolHeroShort` | Earlier modules. |

`TestCanvas` is a 1-second sandbox composition.

Each module follows the same layout (see SKILL.md section 1): `story.ts` (time, shots, cameras), `build.ts` (3D sets), `world.ts` (frame-driven world), `cast.ts` (character cards, FX), `toon.ts` (2D drawing), `lights.ts`, `paint.ts`, plus the shared `pen.ts`, `ink.ts`, `lensblur.ts`, `grade.ts`, `cardshade.ts`, `shade.ts`, and `<Name>.tsx` (the composition).

## Quick start

Requirements: Node 20+ (developed on Node 24), Google Chrome. Python 3 with `numpy` and `Pillow`, and `ffmpeg`/`ffprobe` on `PATH`, are needed for the QA scripts.

```bash
npm install
npx tsc --noEmit        # must exit 0
npx remotion studio     # interactive preview
```

Render calibration stills (all frames in ONE command, half scale):

```bash
# bash / macOS / Linux
BRIDGE_ID=CoasterShort node scripts/bridge-stills.mjs out/coaster/cal/f 10,45,75 0.5
```

```powershell
# Windows PowerShell
$env:BRIDGE_ID="CoasterShort"; node scripts/bridge-stills.mjs out/coaster/cal/f 10,45,75 0.5
```

Render a video (`first` and `last` frame, scale, composition ID):

```bash
node scripts/bridge-video.mjs out/coaster/test.mp4 0 299 0.5 CoasterShort
```

Run the automated QA gate (black/white/frozen frames, pops, held frames, per-shot luma, contact sheets):

```bash
python scripts/short_qa.py out/coaster/test.mp4 out/coaster/qa out/coaster/shots.json
```

`shots.json` has the shape `{"shots":[{"id":1,"a":0,"b":95}, ...], "planned":[[a,b], ...]}`. `planned` lists the frame windows for intentional cuts, camera kicks, expression swaps and subtitle changes.

Tip: pass `BRIDGE_PROPS='{"subs":false}'` to render without subtitles so text never hides hands or props during calibration.

### Machine-specific settings in the render scripts

`scripts/bridge-stills.mjs` and `scripts/bridge-video.mjs` currently assume:

- Chrome at `C:/Program Files/Google/Chrome/Application/chrome.exe` (edit `browserExecutable` for your system).
- A temp folder from `REMOTION_TMP` (defaults to `D:/remotion-tmp`). Each bundle copies `public/` there, so use a drive with room.
- `gl: "angle"`. On a laptop with two GPUs, set Chrome to use the high-performance GPU, otherwise renders are several times slower.

## Audio files are not in the repo

Voiceover tracks live at `public/<module>/audio.mp3`. They are **git-ignored** (private, and large), so the modules that mount an `<Audio>` will fail to find the file on a fresh clone. These are `age18`, `elevator_crush`, `instant_skill` and `school`. You have two options:

1. Drop your own `audio.mp3` at `public/<module>/audio.mp3`, for example `public/elevator_crush/audio.mp3`. The subtitle cue frames in each module were timed to the original voiceover.
2. For silent preview renders, comment out the `<Audio ... />` line in `<Module>.tsx`.

The benchmark modules (`coaster`, `tower_*`, `hotel_lift`, `molasses_tank`) have no audio. `character_sheet.png` (reference art for the school cast), rendered outputs (`out/`) and raw voiceover sources are also git-ignored.

## Working on the engine or the skill

- Follow the workflow and caps in `SKILL.md`: type-check first, at most two projection-math checks, at most two still batches, one video render, and half-scale renders unless a full-resolution render is explicitly approved.
- A new short is created by copying the shared files (`pen.ts`, `ink.ts`, `lensblur.ts`, `grade.ts`, `cardshade.ts`, `shade.ts`) from `src/videos/coaster/` and writing the story-specific files, then registering the composition in `src/Root.tsx`.
- `scripts/` holds the tooling: stills/video renderers, framing checks (`*_frame.mjs`), contact-sheet tilers and the QA gate.
- `public/bridge/kenney/` holds the low-poly `.glb` props used by the `bridge` module (Kenney-style nature kit). `scripts/generate-kenney-glb.mjs` generates the props that were missing from that kit.
