# remotionshorts

A **vertical 9:16 animated Shorts studio (`1080 × 1920 @ 30 fps`)** powered by **Blender 4.2 LTS (`BLENDER_EEVEE_NEXT`)** with a reusable **Official 3D Main Character (`assets/mascot/`)**, automated pre-render guardrails, **3 GPU execution workflows** (Local RTX 3050, Modal Serverless L4/T4, Remote Linux/Colab SSH), and a secondary **Remotion + Three.js** TypeScript engine (`src/engine/`).

---

## Start Here (Humans & AI Agents)

1. Read **[`AGENTS.md`](AGENTS.md)** first — it is the single master router for all AI agents (`CLAUDE.md`, `GEMINI.md`, and `.cursorrules` delegate directly to it).
2. Read **[`RICKS_STYLE_SKILL.md` (v7)](RICKS_STYLE_SKILL.md)** for the 5 visual craft laws, film grammar, and QA gates.
3. Read **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** for the full directory map, dependency graph, and module specifications.
4. For Shorts featuring our **Red-Beanie Yellow-Hoodie Chibi Mascot**, read **[`assets/mascot/MASCOT_SKILL.md`](assets/mascot/MASCOT_SKILL.md)** and **[`assets/mascot/README.md`](assets/mascot/README.md)** — never rebuild him from scratch.

```bash
git clone https://github.com/4mJ0k3r/remotionshorts.git
cd remotionshorts
python -m pip install -r requirements-blender.txt
```

> **Note:** Private reference clips, narration audio, Blender binaries, and rendered outputs are git-ignored. Supply your own story brief, audio track, and authorized render stage.

---

## Core Documentation Map

| File | Purpose |
| :--- | :--- |
| [`AGENTS.md`](AGENTS.md) | Master agent router: decision tree, Official Mascot rule, 3 GPU paths, 5 craft laws, guardrails. |
| [`RICKS_STYLE_SKILL.md`](RICKS_STYLE_SKILL.md) | v7 Blender 4.2 visual, chiaroscuro lighting, PBR, camera, acting, and numeric QA spec. |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Full modular layout, dependency diagram, Guardrail API catalog, active vs. archived Shorts. |
| [`assets/mascot/MASCOT_SKILL.md`](assets/mascot/MASCOT_SKILL.md) | Official Main Character rig API, 18 expressions/visemes, 7 hands, and 18 studio animations. |
| [`docs/archive/README.md`](docs/archive/README.md) | Quarantined legacy docs (`BLENDER_SKILL.md`, `ANIMATION_STYLE_HANDOFF.md`, `PROJECT_MANIFEST.md`, `SHORTS_PIPELINE.md`). |
| [`src/engine/README.md`](src/engine/README.md) | Secondary Remotion + Three.js shared engine entrypoints. |

---

## Quick Start — Default Blender 4.2 Pipeline (3 GPU Workflows)

### 1. Choose a Starter
- **Official Main Character Short:** Copy [`assets/mascot/starter_scene_template.py`](assets/mascot/starter_scene_template.py) to `scripts/<short>/v01/build.py`.
- **Custom Cast / Diorama Explainer Short:** Copy [`scripts/templates/diorama_short_template.py`](scripts/templates/diorama_short_template.py) to `scripts/<short>/v01/build.py`.

### 2. Run on Any of the 3 GPU Backends

```powershell
# Path A — Modal Serverless Cloud GPU (NVIDIA L4/T4, zero idle billing, auto-syncs core kit + assets/mascot/):
modal run scripts/modal_blender.py --mode verify
modal run scripts/modal_blender.py --mode run --project <short>/v01 --script build.py --runner blender --script-args "--out {out}"
modal run scripts/modal_blender.py --mode run --project <short>/v01 --script build.py --runner blender --script-args "--out {out} --render"

# Path B — Local PC + Local RTX 3050 GPU (uses exclusive .blender_gpu.lock):
$env:BLENDER_EXE = 'D:\tools\Blender\4.2.23\blender.exe'
python scripts/templates/diorama_short_template.py --out renders/diorama_starter/v01
python scripts/templates/diorama_short_template.py --out renders/diorama_starter/v01 --render
```

```bash
# Path C — Remote Linux / Colab Cloud GPU via SSH (optional GUI bridge in tools/blender_remote_bridge/):
BLENDER_EXE=/opt/blender42/blender /opt/blender42/blender -b --factory-startup \
    --python scripts/<short>/v01/build.py -- --out renders/<short>/v01
```

### 3. Run Local CPU Tests, Guardrails & QA Gates

```powershell
# Pure-Python unit tests (no Blender required on host):
python -m unittest discover -s tests -p "test_*.py" -v

# Pre-render expression upper-face pixel-lock check:
python scripts/ricks_guardrails.py --check-expr-pair art/talk_closed.png art/talk_open.png

# Post-render numeric & video QA gates:
python scripts/ricks_metrics_gate.py --edge-density renders/<short>/v01/calibration
python scripts/ricks_metrics_gate.py --cam-velocity renders/<short>/v01/final.mp4 renders/<short>/v01/cuts.json
python scripts/short_qa.py renders/<short>/v01/final.mp4 renders/<short>/v01/qa renders/<short>/v01/shots.json
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,sample_aspect_ratio,r_frame_rate,nb_frames -of json renders/<short>/v01/final.mp4
```

---

## Secondary Engine — Remotion + Three.js (`src/engine/`)

Use Remotion when a brief explicitly requests it. Shared engine modules live in `src/engine/`, and individual compositions live in `src/videos/<name>/` (registered in `src/Root.tsx`).

Requirements: Node 20+ (developed on Node 24), Google Chrome, Python 3 (`numpy`, `Pillow`), and `ffmpeg`/`ffprobe` on `PATH`.

```bash
npm install
npx tsc --noEmit        # must exit 0
npx remotion studio     # interactive preview
```

Render half-scale calibration stills and video previews:

```powershell
# Calibration stills (Windows PowerShell):
$env:BRIDGE_ID="CoasterShort"; node scripts/bridge-stills.mjs out/coaster/cal/f 10,45,75 0.5

# Preview video + QA gate:
node scripts/bridge-video.mjs out/coaster/test.mp4 0 299 0.5 CoasterShort
python scripts/short_qa.py out/coaster/test.mp4 out/coaster/qa out/coaster/shots.json
```

> Tip: pass `BRIDGE_PROPS='{"subs":false}'` to render without subtitles during calibration. Voice tracks (`public/<module>/audio.mp3`) are git-ignored; supply your own or omit `<Audio>` for silent previews.

---

## Visual References & Excluded Files

- **Tracked Mascot Previews:** [`assets/mascot/previews/`](assets/mascot/previews/) (`turnaround_4views.png`, `expression_grid_18.png`, `hero_3_reference_poses.png`).
- **Git-Ignored Local Assets:** `renders/`, `out/`, `output/`, `example-animation/`, `refs/vendor/`, `character_sheet.png`, `public/*/audio.mp3`, `.env`, and `_scratch/`.
