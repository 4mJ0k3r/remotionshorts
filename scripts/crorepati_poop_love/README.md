# Crorepati Poop Love — V2 calibration production

Current authorization ends at the V2 contact sheet. **Do not render the full movie until the user approves `sheet_v2.jpg`.** Both `crorepati_poop_love_v2.blend` and the main `crorepati_poop_love.blend` contain the updated scene, 1080×1920, 30 fps, frames 1–2124 (70.8 seconds). Review stills are 540×960. No subtitles, persistent HUD or montage day stamps. The brief `5 YEARS LATER` story stamp remains at f1757–1850; cafe lettering is scene-native.

## Inputs and reproduction

Run from the repository root using Python with Pillow and NumPy, FFmpeg on PATH, and Blender 4.2. Set `BLENDER_EXE` and `NARRATION_AUDIO` to the current machine's executable and supplied Hindi narration. The controller defaults to the paths supplied for this production. Audio, generated textures, review renders and Blender binaries remain local.

```powershell
python scripts/crorepati_poop_love/run.py build
python scripts/crorepati_poop_love/run.py sheet
python scripts/crorepati_poop_love/run.py verify
```

The controller checks the shared `.blender_gpu.lock` and background Blender processes before launching, and removes only its own lock afterward. There is deliberately no full-video command. These commands rebuild assets, the complete timeline, the exact 18 calibration stills/contact sheet, and the pose audit respectively.

## Source map

- `story.py`: authoritative 30 fps boundaries and 18 specified calibration frames; ignore the old 45-second JSON timings.
- `assets.py`, `rig.py`: continuous 1536px neck/shirt/trouser cel, 14px warm ink, 82% Principled / 18% emission, organic heads, independent camera-plane alignment, outward arm IK, knees, seated supports and audio-driven mouth textures.
- `kit.py`, `part1_sets_and_cuts_1_to_9.py`, `part2_cuts_10_to_18_and_sheet.py`: eight dimensional environments, hinged doors and attached hardware, procedural surfaces, shadows, props and 3D effects.
- `runtime.py`: deterministic acting, physical grip anchors, wardrobe changes, 10% linear shot pushes, DOF, FX and calendar state. Shared foot stepping and set ink are embedded from the existing studio helpers.
- `build_crorepati.py`: packs textures, runtime, rig, beat map and amplitude envelope into the saved project.
- `calibrate.py`: fails on runtime callbacks; checks all 2,124 head normals and DOF states, plus projected head bounds at the 18 calibration frames. Still review is not motion approval.

To scrub the saved project interactively, run its embedded `crorepati_runtime.py` text once from Blender's Text Editor. This installs the frame callback; opening a `.blend` with automatic scripts disabled does not itself animate the procedural rig. The calibration worker bootstraps this explicitly.

## Outputs

`renders/crorepati_poop_love/` preserves `sheet_v1.jpg`, `calibration_v1/*.png`, `rig_checks.json`, `source_v1/` and `crorepati_poop_love_v1.blend`. V2 uses `sheet_v2.jpg`, `calibration_v2/*.png` and `rig_checks_v2.json`. The exact same 18 sample frames remain in a 6×3 layout. Each label is outside the video image. `staging_checks_v2/1810.png` is an additional bathroom-insert still for checking all four toilets, not an extra sheet tile. No full-video output is authorized or produced.

V2 changes are scoped to seated thigh/knee/shin routing beyond the bowl/sofa front; an actual hollow gold bowl with its cavity recessed; same-depth nonoverlapping kiss heads and protected facial FX; a dreamy smile and chin contact; foreground/midground hallway spacing; a raised rear cuddle head/backrest clearance and draped blanket; cloth pocket flaps; populated street/cafe/estate backdrops; and removal of montage day stamps. Existing timing, shader mix, interior lighting and narration remain the V1 baseline.

Quoted character speech uses the narration envelope for the plea at frames 645–744 and the Paris dialogue windows; narration elsewhere does not make all characters talk. The exact character voices are not separate isolated stems, so the envelope follows the supplied mixed narration.
