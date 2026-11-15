# remotionshorts

A **Remotion + Three.js 2.5D vertical story-animation engine** (1080x1920 @ 30 fps).

Real 3D sets are built in `three.js` via `@remotion/three`, `@react-three/fiber` and `@react-three/postprocessing`. They are drawn with ink outlines, thin-lens depth of field, bloom and a display-referred colour grade. The characters are 2D cartoon cards drawn procedurally on canvas each frame and placed in the 3D world as yaw-billboards. Each short is a self-contained module under `src/videos/<name>/`.

New Remotion shorts share the studio engine in `src/engine/`. Each short supplies its own story, sets, and frame-driven world.

## Start here with another AI agent

Clone this repository and tell the agent to read [AGENTS.md](AGENTS.md) and
[ANIMATION_STYLE_HANDOFF.md](ANIMATION_STYLE_HANDOFF.md) first. Supply the new
story, voice track, desired renderer, text preferences and permitted render
stage. The handoff links to the current contracts, reusable source and review
process. Code and guidance are included; private reference clips, narration,
Blender binaries and generated media are deliberately excluded.

```bash
git clone https://github.com/4mJ0k3r/remotionshorts.git
cd remotionshorts
```

Use the Remotion quick start below for a silent baseline without external
assets. For Blender, install Blender 4.2 LTS and FFmpeg separately, then
`python -m pip install -r requirements-blender.txt`. The production launchers
currently target Windows/PowerShell. The latest example accepts explicit paths:

```powershell
$env:BLENDER_EXE = "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe"
$env:NARRATION_AUDIO = "C:/path/to/your/narration.mp3"
# Use only when building this example is the requested task:
python scripts/sendha_namak_science/run.py build
python scripts/sendha_namak_science/run.py sheet
```

The example's timing is specific to its 57.6-second story. A new short needs
its own beat map and audio analysis; cloning does not authorize starting an
old render. Older example launchers may contain machine-specific paths—adapt
them before execution. The recipes distinguish reference code from verified
output, and a text-only agent can plan/critique without claiming to render.

## Where the docs are

| File | What it is |
|---|---|
| [Remotion skill v10](animated-3d-story-video/SKILL.md) | Shared-engine architecture and the Remotion build and review workflow. |
| [Blender skill v4](BLENDER_SKILL.md) | Blender scene setup, rigging, contact checks, and render workflow. |
| [Cel studio contract](animated-3d-story-video/references/cel-studio-contract.md) | Shared visual and acceptance rules for both workflows. |
| [Style handoff](ANIMATION_STYLE_HANDOFF.md) | Directing priorities, available visual references and what to give another agent. |
| [Production recipes](animated-3d-story-video/references/production-recipes.md) | Billboard axes, surface grips, mouth anchors, shot resets and resumable delivery. |
| [Project manifest](PROJECT_MANIFEST.md) | Runtime stack, rendering conventions, toolchain, and privacy rules. |

## Shared engine

- `ShortPlayer.tsx` mounts the composition, render passes, audio, HUD, and optional subtitles.
- `character.ts` and `pool.ts` provide cel drawing, poses, actor cards, effects, lip sync, and hand placement.
- `camera.ts` handles shot motion and depth of field. `kit3d.ts` provides reusable set and prop builders. `shaders/` holds shared materials and post-processing.

See the [engine README](src/engine/README.md) for the module entry points.

## Modules (`src/videos/`)

Composition IDs are registered in `src/Root.tsx`.

| Folder | Composition ID | What it is |
|---|---|---|
| `coaster` | `CoasterShort` | 10 s roller-coaster benchmark and calibrated visual baseline. |
| `tower_jump`, `tower_qwen` | `TowerJumpShort`, `TowerQwenShort` | 10 s London Tower Bridge bus-jump benchmark (two variants). |
| `hotel_lift` | `HotelLiftShort` | 10 s 1861 Chicago hotel-lift benchmark. |
| `molasses_tank` | `MolassesTankShort` | 10 s 1919 Boston molasses-flood benchmark. |
| `instant_skill` | `InstantSkillShort` | ~124 s full reel (3714 frames). |
| `elevator_crush` | `ElevatorCrushShort` | 111.5 s full reel (3345 frames). Hindi voiceover, 11 shots, cliffhanger ending. |
| `crush_bathroom` | `CrushBathroomShort` | Bathroom comedy built on the shared engine. |
| `bridge`, `pardon`, `age18`, `school` | `BridgeShort`, `PardonShort`, `Age18Short`, `SchoolHeroShort` | Earlier modules. |

`TestCanvas` is a 1-second sandbox composition.

New shorts use `story.ts` for timing and shots, `build.ts` for sets, `world.ts` for frame updates, and `<Name>.tsx` for the composition. Import reusable components from `src/engine/` and register the composition in `src/Root.tsx`.

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

Voiceover tracks live at `public/<module>/audio.mp3`. They are **git-ignored**. Compositions that use them, including `age18`, `crush_bathroom`, `elevator_crush`, `instant_skill` and `school`, need local audio. You have two options:

1. Drop your own `audio.mp3` at `public/<module>/audio.mp3`, for example `public/elevator_crush/audio.mp3`. The subtitle cue frames in each module were timed to the original voiceover.
2. For silent previews, omit the audio prop from `ShortPlayer` or disable the composition's direct `<Audio>` mount.

The benchmark modules (`coaster`, `tower_*`, `hotel_lift`, `molasses_tank`) have no audio. `character_sheet.png` (reference art for the school cast), rendered outputs (`out/`) and raw voiceover sources are also git-ignored.

## Working on the engine or the skill

- Follow the current Remotion or Blender skill for type-checking, calibration, and render approval.
- `scripts/` holds the tooling: stills/video renderers, framing checks (`*_frame.mjs`), contact-sheet tilers and the QA gate.
- `public/bridge/kenney/` holds the low-poly `.glb` props used by the `bridge` module (Kenney-style nature kit). `scripts/generate-kenney-glb.mjs` generates the props that were missing from that kit.
