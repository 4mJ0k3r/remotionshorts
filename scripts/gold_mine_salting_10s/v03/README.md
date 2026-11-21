# Gold Mine Salting V3

Output: `renders/gold_mine_salting_v3`, exactly 300 frames at 1080×1920/30fps.
V1 and V2 remain intact. New source uses the shared `INTERIOR_WARM_CAVERN`
preset: dark slate low ambient, no foreground mist, amber practical keys,
saturated crimson/teal/gold wardrobes and bright lit skin/ceramic. Outdoor
pipeline defaults are unchanged. Procedural rock shelves/ceiling overhangs
add real uneven boundaries. Head irregularity is fixed low-frequency authored
geometry (peak about .008m) shared by decal conformance and ink, never animated
noise. Inverted hulls use #16121C and 3px at 360p via shared projection scaling.

The user authorized moving only the blast/rock foley from ~1.96 seconds to
1.30 seconds (frame40). It is applied as a deterministic old/new foley delta
to the locked mix; narration, music, other foley, gain and time scale are
preserved. Exact 10-second delivery excludes the last 7.8125ms of the supplied
10.0078125-second recording. Original full recording stays unchanged on disk.
No replacement narration or subtitles.

Timing: f1–30 clean Miner solo beneath cone; f31–75 barrel load/level,
fire40–44 and finite pan toward the impact; f76–110 rich warm crater insert;
f111–270 Buddy with the preserved mug grip/lip-sync/vanish mechanic and
continuous dolly115–268; f271–300 diagonal shoulder gun, shell and wink, Buddy
fully hidden. Gold recedes/shrinks121–181. Candle practical/flame are off in
opening and closing to avoid bright circles behind the head/elbow.

The source packs its runtime, geometry helpers, current lookdev, envelope,
set ink and mix. Run `START_HERE.py` after opening the saved blend. Workers
bootstrap explicitly and fail on callback errors. Source/audio hashes freeze
before render. Owned lock convention prevents concurrent background Blender
jobs or interference with other projects. Cached frames require valid dimensions
and decoding before resume.

Native benchmark_a: p95 1.6485s, maximum1.7570s, sampled board1.6133GiB,
RTX3050 GPU, EEVEE Next/RT off/10samples. Actual full-pass performance,
camera/contact audits, calibration and delivered-mux QA are recorded beside
the outputs. Numerical grip evidence complements visual finger/surface review.
