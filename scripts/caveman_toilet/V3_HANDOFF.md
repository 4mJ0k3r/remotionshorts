# caveman_toilet V3 delivered

- Final: `D:/remotionshorts/renders/caveman_toilet/caveman_toilet_v3_master.mp4`.
- User requested fastest low resolution and 12 samples: 180x320, 30 fps, 1620 frames, exactly 54.000 seconds. Hindi narration unchanged; silence pads the short tail. No 1080p render is authorized by the latest request.
- Sheet: `renders/caveman_toilet/sheet_v3.jpg`, 24 frames rendered at 540x960, 12 samples; input tiles in `calibration_v3_final`.
- Source: `renders/caveman_toilet/caveman_toilet_v3.blend`. V2 blend preserved. Previous scripts retained in `scripts/caveman_toilet/v2_checkpoint`.
- Rig/contact fixes are in `v3_physics.py`, called by `build_caveman_toilet.py`: camera-parallel connected head/torso, sideways floor collapse, evaluated terrain contact, clear walking corridor, opaque shoulder anchor/right nose pinch, shovel grip transforms, three 35-frame strokes, ballistic dirt and grounded ending.
- Hills now meet the base ground continuously; the central acacia moved to the side to avoid masking a walking face. Cave front floor/walls/ceiling reach Y=-8; foreground oval pillars removed. Preserve accepted V2 lighting, HUD and narration.
- `check_v3.py`: 1289 checks, zero errors; maximum consecutive walking-camera height step 0.01544 m.
- `qa_v3/report.md`: 1620 frames, zero black/white frames, zero frozen spans >=12 frames, zero unplanned motion spikes. Original loudness -20.1 LUFS, peak -3.4 dBFS. Narrow planned FX launch/landing events are declared in `qa_v3_shots.json`.
- Manifest and source/output hashes: `renders/caveman_toilet/v3_manifest.json`.

## Safe regeneration

Use the project runner for EVERY Blender invocation; it owns the shared atomic GPU lock and private Blender profile. Do not use live Blender MCP, other project files, shared reference edits, git mutations or image-name process termination. The builder now saves only inside this project, never at repo root.

1. `python scripts/caveman_toilet/run_headless.py build --script build_caveman_toilet.py`
2. `python scripts/caveman_toilet/run_headless.py sheet --script build_caveman_toilet.py -- 540 960 12 v3_final`
3. `python scripts/caveman_toilet/run_headless.py master --script build_caveman_toilet.py --timeout 2400 -- 1 1620 180 320 v3_fast`
4. `python scripts/caveman_toilet/finish_v3.py sheet v3_final`
5. `python scripts/caveman_toilet/finish_v3.py encode`
6. `python scripts/short_qa.py renders/caveman_toilet/caveman_toilet_v3_master.mp4 renders/caveman_toilet/qa_v3 renders/caveman_toilet/qa_v3_shots.json`

`final_pinch_v3.py` and `final_motion_v3.py` are one-off targeted repair runs, not the default full-build workflow. CPU HUD encoding reuses an existing overlay only if it is newer than its source frame; regenerate overlays if the HUD style itself changes.
