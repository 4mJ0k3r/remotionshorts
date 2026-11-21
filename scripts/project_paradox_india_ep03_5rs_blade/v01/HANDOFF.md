# Current state

User changed scope: finish design, deliver first 10 seconds at 540p only.
Preview MP4 is complete and validated: renders/project_paradox_india_ep03_5rs_blade/v01/Project_Paradox_EP03_first10s_540p.mp4.
300 frames, 540x960, 30fps, 10.000s, AAC narration/music/foley. No subtitles.
Master: project_paradox_ep03_v01.blend, designed for 1401 frames / 46.7s.
Full rendering has NOT started. scope.json blocks it; do not resume without a new request.

All four sets and cast are built. Latest finishing: tessellated conformed clothes,
real open windows (opaque inverted-hull backs removed from transparent panes),
flat graphic faces/hands/limbs, camera-compensated character ink, mechanical supports.
Packed START_HERE.py activates the scene runtime after reopening.

Preview QA raw flags are retained and individually resolved in
qa_preview/inspection_resolution.json; native tracked wall patch is stable.
Full-film validation remains separate: the all-geometry AABB audit has false
positives from cached bounds of curves initially hidden at frame1. Before any
future full render, derive/cache curve bounds from evaluated meshes upon first
visibility (refresh dynamic curves), then rerun fresh calibration/gates/benchmark.
Do not relabel the failed full audit as passed. Source changed since older native
benchmarks, so do not reuse their hashes. Expected native timing measured earlier
was ~1.33s/frame at32 samples; this is not a fresh final-source certification.

Current code: prepare audio identity/envelope in input_manifest/audio_envelope;
audio.py synthesizes/packs the mix; launch.py owns GPU lock; worker.py executes
stages. deliver_preview.py packages and validates the authorized preview.
Approved older productions remain untouched.
