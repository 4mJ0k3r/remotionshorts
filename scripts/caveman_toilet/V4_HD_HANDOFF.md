# V4 native 1080p export

Latest user request: render the approved V4 in high quality at 1080p. Profile: native 1080x1920, 30 fps, 64 EEVEE samples, 1620 frames / 54 seconds. Preserve V4 scene, narration and previous low-resolution output.

## Files and status

- Source: `renders/caveman_toilet/caveman_toilet_v4.blend`, read-only during rendering.
- HD frames: `renders/caveman_toilet/frames_v4_1080p/f0001.png` through `f1620.png`.
- HD overlays: `frames_v4_1080p_hud`; CPU encoding: H.264 CRF16 medium + Hindi AAC192k, exact54s.
- Final: `renders/caveman_toilet/caveman_toilet_v4_1080p_master.mp4`.
- Live renderer status: `renders/caveman_toilet/v4_hd_progress.json`.
- Postprocessing status: `renders/caveman_toilet/v4_hd_completion.json`.
- Successful final manifest: `renders/caveman_toilet/v4_1080p_manifest.json`.
- Final QA: `renders/caveman_toilet/qa_v4_1080p/report.md`.

The full render is resumable and validates its profile against the source blend hash. The first 60 frames were retained during a temporary-frame-saving optimization; all frames use 64 samples. PNG compression is lossless and does not change image quality. Four 1080p benchmark stills were visually inspected; estimated full-render time about 70-90 minutes on this machine.

## Running pipeline

The renderer is launched through the project mutex runner:

`python scripts/caveman_toilet/run_headless.py master --script render_v4_hd.py --timeout 14400`

One CPU-only watcher, `complete_v4_hd.py`, is waiting in the background. Once frame1620 completes it automatically runs `finish_v4_hd.py`, then the shared read-only `scripts/short_qa.py`, validates 1080x1920/30fps/1620frames/54s, and writes the completion manifest. Do not launch a duplicate encoder while the watcher is alive. Its exclusive guard is `renders/caveman_toilet/.hd_finish.lock` and records its PID and unique owner.

The shared GPU lock remains owned by the Blender runner until its render exits. Never remove a foreign lock. Do not use live Blender MCP, touch other project folders, perform git mutations or terminate processes by image name. All scripts/frames/assets remain inside the caveman_toilet folders.

## Delivered and reviewed

Native HD export completed on 2026-11-14: 1080x1920, 30fps, 64 samples, exactly54.000s /1620frames, original Hindi AAC audio, H.264 CRF16. Final video is `caveman_toilet_v4_1080p_master.mp4` (19,875,045 bytes). Prior V4 preview preserved. GPU mutex and CPU finishing guard both released.

Automated QA: zero black frames, zero unplanned white frames, zero unplanned motion spikes. One low-motion span f616-654 was flagged in the held campfire shot. Manual review of all39 decoded frames confirmed moving flames, zero identical adjacent frames, and fire-region adjacent differences .0248-.2668 (mean .1349). The global threshold flagged a quiet approved hold, not an identical-frame freeze. Evidence is in `qa_v4_1080p/fire_hold_review.json` and `.jpg`. The raw automated `qa_clean:false` is retained honestly; the final manifest adds `review_status:approved`, and completion status records `reviewed_pass:true`. Do not rewrite the automated QA report or reanimate the approved shot merely to remove this threshold flag.
