# V3 — illustrated 2D cast revision

Latest user references override the previous rounded light-wrapped cast.
Output is under `renders/gold_mine_salting_v3/flat_cast_v1`; the prior V3
candidate remains intact. The characters use shallow head artwork (0.064m
depth), camera-facing independent pivots, surface-conformed expressions,
flat cream paint with a restrained fixed edge accent, solid wardrobe colors,
compressed clothing/pattern depth, slim dark emission limbs and bold ink.
There is no broad spherical lighting gradient on the cast. The mine, lighting,
wood/steel shotgun, mug, shell and physical grip anchors remain dimensional.
No time-dependent contour wobble is used.

All V3 timing remains: fire40–44, smooth pan to impact, continuous Buddy
dolly115–268, deposits shrink/recede121–181, solo closing wink. Original
lip-sync and mug-grip solvers are retained; narration/music remain unchanged,
with only the user-authorized earlier blast/rock foley. Exactly300frames,
1080×1920,30fps. Subtitles remain off.

The shared INTERIOR_WARM_CAVERN preset is reused, with no foreground haze.
Original supplied PNG references are copied into the output's `user_references`
folder. `character_review_a` and `illustrated_cast_native_review.jpg` show the
new character treatment. Benchmark_a: p95 1.1920s, maximum1.1946s, sampled
board VRAM1.5820GiB, native RTX3050 EEVEE/RT off/8samples. These are benchmark
measurements; final full-pass performance is recorded separately.

Run the packed START_HERE.py after opening the final blend. Workers do this
explicitly; all runtime/geometry/lookdev/envelope/set-ink/audio dependencies
are packed. The source/audio identity is frozen before movie frames. The GPU
launcher honors the shared owner-checked lock and never changes V1/V2/other
productions. Gates, current calibration and final mux review are recorded
beside the output. Old rounded-cast QA cannot certify this revision.
