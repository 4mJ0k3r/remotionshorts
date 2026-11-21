# 1 Year Without Wiping

The reel and v6 portrait look were approved on 2026-11-21. Native rendering with the v6 look is paused until the user asks to resume.

- Approved look: `renders/one_year_no_wipe/v01/portrait_grade_proof.png`. The before/after stills and timings are in `portrait_grade_frames` alongside it.
- Source scenes: `renders/one_year_no_wipe/part1_v02/part1_v02.blend` and the corresponding `part2_v01`, `part3_v01`, and `part4_v01` folders. The four v6 comparisons were rendered from temporary scene changes. The saved source scenes and the earlier master contain the previous look.
- Locked edit: 2,484 frames at 30 fps, with part boundaries at 0, 837, 1609, 2225, and 2484. The timing plan and continuous audio mix are saved as `master_plan.json` and `master_audio.wav` in `renders/one_year_no_wipe/final/`.

When authorized, apply the v6 focus, lighting, and compositor helpers to versioned copies of the four scenes. Verify the hero focus and readable graphics at each cut, run the RTX 3050 gate under the shared GPU lock, and render at 1080 × 1920. Join the modules on the locked frame grid and decode-check the master with the saved audio mix.
