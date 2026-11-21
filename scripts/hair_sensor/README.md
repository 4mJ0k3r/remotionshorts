# hair_sensor

Current delivery is `renders/hair_sensor/hair_sensor_v3_preview.mp4`; authoritative saved scene is `renders/hair_sensor/hair_sensor_v3_desk_fixed.blend`. V2 scripts/checkpoints are retained as history.

V3 asset authoring: `v3_assets.py`. Scene authoring: `v3_build.py` and `v3_lib.py`. `v3_preflight.py` handles geometric framing. Targeted later authoring is recorded by `v3_patch_contacts.py` and `v3_fix_desk.py`; the latter includes the user's behind-desk correction and shoulder sockets. Saved-scene source/range mappings are in the render folder's manifests and `V3_DELIVERY_REVIEW.md`.

Every headless Blender invocation MUST use `run_blender.py`, including read-only Blender inspection. It claims the shared GPU lock atomically and releases only its GUID-owned lock. Never use the shared live MCP, touch poop_city, make Git writes, or stop processes by image name.

`v3_render.py` renders saved scenes for calibration or preview. It caches existing preview PNGs; changed scenes must use a fresh versioned destination or explicit complete-range replacement. `v3_patch_render.py` and `v3_render_desk_fix.py` perform the documented replacements. Do not mux a partly replaced frame sequence.

`v3_finish.py` checks the completed source hash, encodes the 540×960 preview with narration, runs unchanged shared short_qa.py and checks exact decoded-frame hashes. `v3_review_sequences.py --encoded` and `v3_boundary_review.py --encoded` generate review artifacts from the actual delivered MP4. New creative changes require a new source version and review; do not assume the V3 checks cover later changes.
