# Slow Eddie V12 — audited delta patch

Source: `D:/remotionshorts/renders/slow_eddie_v11/slow_eddie_v11.blend`, copied before patching. Outputs live in `D:/remotionshorts/renders/slow_eddie_v12/`. V11 remains intact. Read `D:/remotionshorts/tools/V11_Exit_Gate_Audit/V11_Exit_Gate_Audit.md` and its evidence before working on this version; its measurements are distinguished from proposed settings and subjective scores.

## Camera and motion

The hold and f122 share the exact same transform, lens, sensor shifts and focus target. The following quintic pullback moves monotonically down the street center to the wide standoff. The prior porch-side path and f211 reset are removed. The wide-shot shift carries continuously into the push, with f210→211 position change only about 1.52 mm. The checked static set includes named railings, porches, barrels, crates and imported Western facade geometry; a combined world-space BVH tests camera clearance on every frame. The minimum clearance over f158–181 is about 1.835 m. The junction sheet also checks the actual rendered view; distance alone cannot certify visibility.

The orbit fits both bullet and Eddie in projection instead of trusting endpoints. Camera retreat along its optical axis handles excessive projected separation. The larger copper geometry shows its side while its nose remains aligned with the physical path. During approach the focus racks from bullet to grip over f76–90 at F/2.8. The upright crosshatched ivory grip remains distinct from the dark glove. A projected surface solve positions the arriving bullet at approximately 20.05 px clearance at 360p.

The gun stays elevated into f24. The planned launch view ends at f30, followed by one launch-to-chase cut at f31; the old extra launch-camera reframe at f31/34 is not retained. Smoke material opacity is .045 per wisp, keeping three fully overlapping layers below .15 combined opacity. Existing wisps are flattened/reshaped rather than introducing a simulation. Challenger's lowered gun is hidden until clean entry, with the lowering pose prepared beforehand. Small torso motion is limited to the standoff reaction.

The hands insert favors the holster side and has a small camera drift. The final 50 mm reveal runs f280–300 with quintic distance and framing curves. It no longer finishes at f286. The 10-panel and transition sheets show the measured crop rather than certifying a previous proposed 18% world-distance setting.

## Materials and cast

World ramp stops are #BEE1FF / #6DBCFD / #2D93FB with calibrated ray-elevation mapping. The road's lit ramp stop receives the scene-linear (1.22, 1.19, .98) multiplier; the dark cast-shadow stop, exposure 0 and skin/brim ramps are preserved. Teal and vest lit stops change to #47B0AC and #BE9462. No new lights, samples or volumetric simulation are added.

Added procedural head displacement is removed; the authored rough contour remains. Existing chest cartridge marks are restored. The ink is reduced from V11 rather than thickened globally. The moustache is one filled/extruded five-lobe curve with .008 m total depth and .003 m bevel, replacing the five beads. The straw's existing last segment bends down 12 degrees. Existing seams/lapels are retained.

## Locked audio and captions

The final encode maps V11's AAC stream directly with `-c:a copy`; no loudness filter, resampling or audio encoder is invoked. `verify_delivery.py` compares every audio packet's SHA-256, presentation timestamp and duration against V11, not just LUFS. The previously passed soundtrack sync is retained.

ASS is copied from the existing schedule, with Arial 94/Bold, #FFFFFF fill and 6 px outline. Both adjoining boundaries of “Eddie.” move from 7.933 to 7.900 s (f238). `font_check.log` confirms the local `arialbd.ttf` is loaded and libass selects Arial-BoldMT. Text is burned after Blender's scene/compositor grading, with no subsequent color-grade filter.

## Gates and reproduction

Run stages from `D:/remotionshorts`: `python scripts/slow_eddie_v12/launch.py build`, `audit`, `calibrate`, `editorial`, `benchmark`. Then run `make_junction.py` and `make_sheet.py` and inspect both sheets before `deliver.py`. The shared GPU lock is exclusive; do not run another render or headless Chromium concurrently. The script uses Blender 4.2.23, EEVEE Next, RT off, 24 samples and the preserved stable 512 MiB shadow pool.

Run embedded `slow_eddie_v12_runtime.py` before interactive timeline inspection. Its deterministic camera and pose evaluation mutes inherited camera curves. Source build must start from V11, not repeatedly patch an already modified V12.

`junction_audit.json` records all intermediate camera samples, orbit subject positions and held projected clearance. `transition_junctions_calibration.png` contains the 17 requested frames, using the launch editorial layer where applicable. `transition_junctions_final.png` and `comparison_final.png` are extracted from the encoded MP4. `performance_gate.json`, `vram_*.json`, `full_timing.json` and `delivery_validation.json` report actual measurements. `qa/report.md` retains all diagnostic flags rather than suppressing intended holds or the reveal. No subjective parity percentage is certified by these numerical gates.

## Final delivery measurements

The validated MP4 is native 1080x1920/30fps/300f/10.000 s, with 939 audio packets identical in content, PTS and duration to V11. Base full-render wall time371.428 s; per-frame mean1.231 s, p951.451 s, max1.760 s after separate warmup. Native benchmark max1.553 s. Peak monitored whole-board usage across stages1545 MiB (1.509 GiB), with main-render peak1344 MiB. No black/unplanned-white frames or unplanned MAD spikes in final QA; the holster hold is intentional.

The post-render launch correction changes only bullet visibility from24 to31. Frames24-30 were rerendered and composited; the frame24 main pass was separately warmed, then measured1.078 s. The original runtime and both source hashes are retained in launch_patch_manifest.json, with all other runtime bytes verified identical. This is a bounded frame patch, not a claim that all 300 frames were rerendered after it. To reproduce from the final master, the normal full pipeline includes the corrected visibility automatically.

The caption-only white-mask test measured268x62 px for fastest at1080p, optical center70.44%; font_check.log confirms Arial-BoldMT. Eddie advances to f238. Face-width calibration measured about260 px at360p on286 and151 px on300. Final rendered junction MAD with captions excluded is about1.06 for121/122 and4.41 for210/211; these are image-change diagnostics, not proof that all actor pixels must remain frozen. Exact camera equality and BVH clearance are recorded separately.
