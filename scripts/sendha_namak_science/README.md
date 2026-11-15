# Rock salt visual comedy — V2

Blender 4.2.23 / EEVEE Next, 30 fps, frames 1–1728. Native layout is
1080×1920; the authorized preview and calibration tiles are 540×960 with
16 samples. This production has no subtitles, HUD or scene lettering.
Question marks and the medical/prohibition symbols are drawn icons.

`build_sendha_namak.py` constructs five isolated stages (the microscopic
tissue stage belongs to the mouth set), cel rigs and props. It reuses the
existing `Stage`, card/material helpers and `scripts/studio/set_ink.py`.
`assets.py` authors stable RGBA artwork; `runtime.py` evaluates acting,
billboards, optical focus, grips and finite events at arbitrary frames.
All runtime code and images are embedded in the saved blend. The audio
envelope remains an explicit generated dependency in the render folder.

Run from the repository root:

```powershell
$env:BLENDER_EXE = "C:/path/to/blender.exe"
$env:NARRATION_AUDIO = "C:/path/to/narration.mp3"
python scripts/sendha_namak_science/run.py build
python scripts/sendha_namak_science/run.py verify
python scripts/sendha_namak_science/run.py sheet
# Inspect renders/sendha_namak_science/sheet_v2.jpg before the next step.
python scripts/sendha_namak_science/run.py movie
```

The launcher claims the shared GPU lock exclusively, waits for other Blender
owners, and releases only its own lock. Movie spans contain 144 frames and
resume from verified PNGs. A SHA-256 manifest rejects changed source/audio
when resuming. The source is `sendha_namak_science.blend`; audio preparation
uses `NARRATION_AUDIO` (or `public/sendha_namak_science/audio.mp3`), pads/trims
to this example's 57.600-second timeline, and builds a normalized 30 Hz
attack/release envelope. Bring the intended voice track; it is not in Git.
For another story, adapt the timing and frame count instead of truncating its audio.

V2 uses a 0.11 m hand-held strawberry, two short lick events, a sculpted
navy quilt, terrified blush-free faces, rounded navy hips, persistent macro
salt, a barrel-surface shaker grip with wrapping fingers, a separate pink
safari tongue/barrier, and a mouth-centered hanging swollen tongue.

Deliverables live under `renders/sendha_namak_science/`: `sheet_v2.jpg`,
`sendha_namak_v2_master.mp4`, `v2_delivery_probe.json`, `qa_v2/` and
`rig_verification_v2.json`. V2 frames and frozen source are isolated from
V1's 218-frame partial delivery. The audit checks all poses, head normals,
semantic hand-to-prop contacts, arm reach, visible crystals and font objects.
It complements the calibration and delivered-movie visual review.
