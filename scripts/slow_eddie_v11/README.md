# Slow Eddie V11

Copied from `D:/remotionshorts/renders/slow_eddie_v10/slow_eddie_v10.blend` and saved separately in `D:/remotionshorts/renders/slow_eddie_v11/`. V10 remains intact. Road, sky, source audio mix and supplied caption file are retained.

## Changes

EEVEE shadow pool 512 MiB, shadow rays 2, supported light maximum shadow resolution .025, shadow jitter disabled. Ink hulls, clouds, smoke, wind ribbons and mesas have shadow visibility disabled. Source geometry and cast shadows remain; no shadow-map resolution is silently relaxed beyond the requested value.

Copper uses #E88B4A, metallic .25, roughness .24 and low warm emission to keep its color under the cool street environment with RT off. Smoke uses transparent/emission mixing at .16 opacity. Existing smaller directional flame is retained. The narrower ivory crosshatched grip is distinct from the dark hand/finger meshes; its white color is intentionally retained as pearl, not used as a mitten.

The bullet has one baked world-space position dictionary, embedded as `V11 flight.json`. Camera tracking uses that same path. The initial forward flight curves through two Bezier controls into the holster approach. For frames 25–90, nose +Y is oriented to the exact forward difference of actual consecutive positions, with spin about local +Y afterward. The first held position is f91; this gives f90 a nonzero last tangent. It remains held through f121 and exits afterward. `velocity_audit.json` measures actual runtime positions and axes, not merely the intended curve.

Hip framing centers the buckle. The late insert holds a tight waist crop through f275 before the reveal. Brim width is expanded, belt loops moved down from the chest, brows slanted, Challenger root/feet rotated 25 degrees through f171–180, and sweat lowered on the temple.

The centered hip composition uses a left-side bullet arrival at 8% frame width, with projectile scale 1.2, so the complete bullet remains visible beside the grip rather than hiding behind the torso. The initial full render was stopped on discovering that occlusion; the corrected delivery restarts from frame 1 and overwrites the complete sequence. The actual trajectory is regenerated from the corrected framing and its forward-difference audit is rerun after source changes.

## Validation

`opening/` contains all 30 opening calibration frames at 540×960, plus `opening_review.jpg` for sequential inspection. `opening_stability.json` reports a stationary road region; it does not claim the entire image is identical while the actor, recoil and FX move. Additional quiet-frame shadow-region checks at x0–90/y520–750 changed by mean .033 and maximum adjacent mean .052 in 8-bit values; two other background patches were unchanged. No obvious background shadow pop was observed in the contact sequence. A universal zero-flicker claim is not made from these sampled regions.

`benchmark.json` measures twelve native 1080p frames after warmup, with a strict max/p95 ≤1.8 s gate. Whole-board sampled VRAM is in `vram_*.json`. The final render separately warms frame 1 before timing the 300-frame animation. `delivery_validation.json` excludes that extra warmup Time line from the 300-frame statistics.

Delivery renders native PNGs, separate gun-side launch coverage, the launch/hands dissolves, unchanged supplied ASS using Arial Bold, and the preserved normalized reference mix. All-frame QA runs on the actual MP4. Review `qa/report.md` for retained diagnostic flags. The final comparison shows the ten specified timestamps beside the saved reference at equal full-frame display sizes.

## Reproduce

From `D:/remotionshorts`, run `python scripts/slow_eddie_v11/launch.py build`, `finish`, `calibrate`, `benchmark`, then `opening`. Inspect those before running `python scripts/slow_eddie_v11/deliver.py`. Run `python scripts/slow_eddie_v11/verify_delivery.py` after encoding. The launcher exclusively owns the shared GPU lock during each Blender stage; never run another GPU render or headless Chromium concurrently.

Run embedded `slow_eddie_v11_runtime.py` before interactive timeline inspection. The deterministic runtime owns camera/pose evaluation and mutes inherited V9 camera curves. Build stages must start from V10, not be repeatedly applied to already patched V11 geometry.

The result is a stylized reconstruction, not a certified pixel-identical reference. Forehead shading and facial details remain authored approximations. Actual measurements and specific review limits are retained rather than claiming complete aesthetic parity.

Final validation: 10.000 s, native1080x1920/30fps/300f, H.264/AAC, decode passed. Full animation384.270 s; frame mean1.274 s, p951.501 s, max1.720 s, all under1.8 s. Benchmark p951.531/max1.548 s. Peak across monitored stages1626 MiB (1.588 GiB). Audio -14.33 LUFS/-3.29 dBTP. Velocity audit maximum0.0 degrees in Blender float precision. No black/unplanned-white frames; hold106-120 is intentional and QA spikes277-283 coincide with the reveal. The static opening-background patches are stable within the recorded limits. Forehead band/face details remain approximations rather than an exact reference match.
