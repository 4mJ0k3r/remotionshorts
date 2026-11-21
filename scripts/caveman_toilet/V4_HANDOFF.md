# caveman_toilet V4

V4 upgrades the preserved `renders/caveman_toilet/caveman_toilet_v3.blend` directly, keeping the approved baked motion. The current entry point is `build_caveman_toilet.py`; its default build calls `v4_overhaul.build_scene()`. It never overwrites the V3 blend. V3 source scripts are checkpointed in `scripts/caveman_toilet/v3_checkpoint`.

## Requested outputs and profile

- `renders/caveman_toilet/caveman_toilet_v4.blend`
- `renders/caveman_toilet/sheet_v4.jpg`: 16 frames, rendered 540x960 at 12 samples; final tiles in `calibration_v4_final`.
- `renders/caveman_toilet/caveman_toilet_v4_master.mp4`: preserved fast 180x320, 30 fps, 12-sample preview; 1620 frames / 54 seconds with original Hindi narration and silence padding.
- Latest user request explicitly authorizes a high-quality 1080x1920 export. The native HD render uses 64 samples and writes `caveman_toilet_v4_1080p_master.mp4`. Read `v4_hd_completion.json` for its current state and `v4_1080p_manifest.json` for verified completion.
- `v4_manifest.json`, `qa_v4_scene.json`, `qa_v4_calibration.json`, and final `qa_v4/report.md` contain the measured state. Consult the manifest status before calling the video delivered.

## Changes

- 42 card materials: roughness 1, specular 0, 72% emission at strength .88, 28% Principled; opaque sprite interiors use DITHERED depth for correct focus and fog occlusion.
- CPU-generated day and cave warm-left/warm-right sprites in `sprites_v4`. A keyed per-character group chooses the cave palette and fire-facing direction. Elder beard is scalloped and clipped inside the circular face.
- Corner-squat head is lowered 0.0248m along torso up, changing the neck overlap from .88 to .78 head radius. Other approved motion is preserved. The checker compares 387 motion channels against V3.
- Cave uses a sculpted barrel vault and bowed rear rock wall with a real opening; three subdivision passes are applied once to modest topology (50,240 total faces), followed by Voronoi/cloud displacement totalling .55m. Seven displaced boulders replace the tube arch. Rock roughness .88, bump distance .04m.
- A small normal-dependent ambient response in the stone shader keeps the dark rock readable in fast EEVEE without a GI bake. This was verified in the confirmation sheet; removing it makes the ceiling nearly black despite the specified light powers.
- Cave fill: AREA 150W, size6.5, slate blue, no shadows, at (0,-1.5,3.2). Fire: POINT 65W with gentle +/-3W noise, orange, radius .85, at (0,.2,.45). Toxic: one AREA 95W, size4.5, at (.5,1.2,2.6), replacing the old green point light. Bulb peak clamped25W, radius .6, mesh emission3.5 and restrained FOG_GLOW.
- Fifteen soft radial-density volumetric fog ellipsoids, alpha control .18, sit behind actors. Surface-alpha spheres were rejected because they obscured/blurred faces in depth of field.
- Outdoors: SUN3.5, angle15 degrees, warm day/sunset colors, plus 15m AREA240W sky fill. Matte world-coordinate three-color grass noise and shallow bump replace stretched texture bands. Recessed pit walls darken with depth.
- Four native 3D poop mounds each contain three torus coils, a peak and a soft floor contact disc.
- Held cave shots 7, 10 and 16 have visible flame motion; the offscreen-fire squat also has restrained bounced-light variation. This removes frozen stretches exposed by the lower light powers without changing character acting.

## Verified delivery

Final video: 180x320, 30 fps, exactly 54.000 seconds / 1620 frames, H.264 + Hindi AAC mono. Full-video QA: zero black frames, unplanned white frames, frozen spans >=12 frames or unplanned motion spikes. Narration remains -20.1 LUFS, peak -3.4 dBFS. Scene check: 387 approved motion channels preserved, 42 correct character materials, zero errors. Final calibration: 24 shirt regions show zero white/pink clipping; ten cave tiles have upper-band luma >=0.07526. GPU lock released after verification.

## Regeneration

Every headless Blender command MUST use the project runner and its atomic shared GPU mutex/private profile. Never use live Blender MCP, another project's files, git mutations, shared reference edits or image-name process termination.

1. `python scripts/caveman_toilet/sprites_caveman_v4.py` (CPU only; needed only after sprite changes)
2. `python scripts/caveman_toilet/run_headless.py build --script build_caveman_toilet.py`
3. `python scripts/caveman_toilet/run_headless.py build --script check_v4.py`
4. `python scripts/caveman_toilet/run_headless.py sheet --script build_caveman_toilet.py -- 540 960 12 v4_confirm`
5. `python scripts/caveman_toilet/finish_v4.py sheet v4_confirm`
6. `python scripts/caveman_toilet/measure_v4_sheet.py v4_confirm`
7. `python scripts/caveman_toilet/run_headless.py master --script build_caveman_toilet.py --timeout 2400 -- 1 1620 180 320 v4_fast`
8. `python scripts/caveman_toilet/finish_v4.py encode`
9. `python scripts/short_qa.py renders/caveman_toilet/caveman_toilet_v4_master.mp4 renders/caveman_toilet/qa_v4 renders/caveman_toilet/qa_v4_shots.json`

The legacy V3 one-off repair launchers and V4 `final_fire_v4.py` / `final_bounce_v4.py` are not full-build entry points. The default V4 build already includes their final corrections. Scene simplification remains enabled at subdivision cap2, EEVEE Next ray tracing stays off. All writes remain inside the two caveman_toilet project folders, except the shared GPU lock owned by the runner.
