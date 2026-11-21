# Slow Eddie V9 delivery

V9 is a copy-derived upgrade of `D:/remotionshorts/renders/slow_eddie_v8/slow_eddie_v8.blend`. V8 and earlier versions remain intact. The final scene is `D:/remotionshorts/renders/slow_eddie_v9/slow_eddie_v9.blend`; the delivery is `slow_eddie_v9_1080p.mp4` in that directory.

## Inputs and implementation

Read and used the complete forensic specification and helper at `D:/remotionshorts/tools/V9_Parity_Packet/V9_Parity_Packet/`. Helper-authored lighting, world gradient, cel palettes, metallic surfaces, haze and glow are adapted for Blender 4.2.23. The character contours, downloaded Western town and original props are retained from V8. Constructors are imported from V7 without executing its production entrypoint. Asset credits remain in the V5 production documentation.

The delivered scene uses EEVEE Next, ray tracing off, native 1080×1920, 30 fps, frames 1–300, **24 samples and 128 MiB shadow pool**. This is a measured performance fallback from the packet's initial 32 samples / 256 MiB setting. Runtime pose evaluation is cached per frame to avoid repeated mesh updates during render callbacks. The saved camera keys are LINEAR; the embedded runtime mutes them while it evaluates the complete scene procedurally. Run the embedded `slow_eddie_v9_runtime.py` text before previewing the timeline in an interactive Blender session. Opening the file alone does not automatically execute text scripts.

Color calibration retains the specified road Principled albedo/noise but grades its light response through a light-driven ramp. Distant architectural shadow casting is disabled; local character/hat/prop shadows remain. The world Normal-Z gradient is inverted to match Blender's ray direction. Skin uses the packet's Map Range plus additional light contrast for the brim band. These are documented adaptations, not a recovered original RicksClips rig.

Camera choreography includes the earlier frame-21 recoil, side-on chase, approach and held hip composition, continuous backward retreat, lowered-gun standoff, small late tumbleweed, hands insert and late reveal. The additional gun-side launch coverage is rendered separately. FFmpeg delivery uses the supplied ASS unchanged, with local Arial Bold supplied to libass. The original locally available reference mix is used for audio, not newly generated speech or separately synthesized effects.

## Delivery and validation

All paths below are relative to `D:/remotionshorts/renders/slow_eddie_v9/`:

- `comparison_calibration.png`: current 50% calibration at the ten specified frames.
- `comparison_final.png`: ten matched timestamps from the encoded 1080p delivery beside the saved 360×640 reference. Both shown full frame at equal display size.
- `benchmark.json`, `performance_gate.json`, `warmup.json`: twelve measured native frames after separate shader warmup.
- `vram_benchmark.json`, `vram_render.json`, `vram_editorial.json`: sampled whole-board GPU memory, not just Blender allocation.
- `full_timing.json`, `render.log`: whole animation wall time and per-frame Blender timings.
- `editorial_layers.json`: launch dissolve f24–26 and hands dissolve f255–258. Dissolves are applied to rendered PNGs before encoding; they are not a single-camera effect inside the blend.
- `delivery_validation.json`: decoded dimensions/frame count, loudness, timings, source hashes and limits of the visual review.
- `qa/report.md`, `qa/sheet_*.jpg`: all-frame statistical checks and contact sheets. The diagnostic reports are not aesthetic acceptance certificates.

The packet's original 303-frame reference file is absent locally. The available 300-frame saved reference is used at `t=(frame-1)/30`; the supplied ASS provides its caption reconstruction. No claim is made that the available compressed clip is byte-identical to the packet's original.

## Reproduction

From `D:/remotionshorts`, use `python scripts/slow_eddie_v9/launch.py STAGE` for Blender stages. It exclusively acquires `.blender_gpu.lock`, starts Blender, logs output and releases only its own lock. Do not run another render or headless Chromium concurrently. The scene build sequence from V8 is `build`, `tune24`, `final_materials`, `last_fit`, then `calibrate`, `benchmark`. `last_fit` is a one-time source patch: do not apply it repeatedly to an already patched V9, as it widens the brim. Inspect calibration before proceeding. Run `python scripts/slow_eddie_v9/make_sheet.py` to refresh the calibration sheet.

After the performance gate passes, `python scripts/slow_eddie_v9/deliver.py` renders all frames and launch coverage, composites the two editorial transitions, burns captions, normalizes/muxes audio, decodes the result, runs `D:/remotionshorts/scripts/short_qa.py`, and creates the comparison sheet. `python scripts/slow_eddie_v9/verify_delivery.py` independently validates the finished files and creates the delivery report. The render scripts always bootstrap the embedded runtime explicitly.

## Honest visual status

This is a V9 candidate, **not a certified ≥90% match**. Main remaining differences are the opening town geometry/camera azimuth, a wider late reveal at f286, and approximations in the mustache, glove contact and cel-shadow boundary. The comparison uses matched timestamps without compensating crops or grading. Still/contact-sheet inspection and automated QA do not substitute for a direct motion/aural review or an independently defined parity score.

Latest validated delivery: 10.000 seconds, 300 decoded frames, 1080×1920, H.264/AAC. Native render wall time 348.605 seconds; frame-log mean 1.155 s, p95 1.411 s, max 1.990 s. The separate twelve-frame gate measured p95 1.474148 s and max 1.537236 s. Whole-board sampled peak 1262 MiB (1.232 GiB). Audio measures −14.33 LUFS, −3.29 dBTP after AAC encoding; this stays below the −2.9 dBTP ceiling.

Automated QA found no black or unplanned white frames. It flags two low-motion spans during the explicitly requested holster hold and spikes at zero-based frames 189, 194, 195, 201, 202 and 271. Contact-sheet review shows small held-shot changes and onset of the late reveal rather than missing frames; these diagnostic flags are retained in the report rather than suppressed. The final file decoded without errors, and the saved scene hash did not change during rendering.
