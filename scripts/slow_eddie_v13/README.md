# Slow Eddie V13 — visual-only polish

Copied from `D:/remotionshorts/renders/slow_eddie_v12/slow_eddie_v12.blend`. Output: `D:/remotionshorts/renders/slow_eddie_v13/`. V12 remains intact.

## Locks

The main camera/flight/aim/framing functions remain identical to V12. `camera_lock.json` records equality of all 300 main-camera position, quaternion, lens, shift, aperture and focus states before/after the visual patch. The gun-side camera states are captured from V12 before changing the gun pose and replayed exactly by `editorial.py`; the actor/weapon moves inside that fixed view. Existing f122/f211 camera continuity and the street-center collision path are therefore retained. No set geometry, global key direction, road, sky, exposure or sample count is changed.

The supplied V12 ASS is copied byte-for-byte. V12 AAC audio is stream-copied with no remaster, resample, encoder or sync offset. Final verification checks packet content and timestamps against the delivered V12 MP4, plus exact caption-file identity.

## Visual changes

- Eddie's isolated skin receiver quantizes actual received light/shadow into a cool #C4C8EA brim band, with a narrow object-space transition, while protecting the cheeks/jaw at warm #FDF5EF. The real opaque felt brim remains shadow-casting and is slightly lowered at its front. The spatial guard prevents the broad cool gradient from darkening the lower face; it is a cel-receiver treatment, not a claim of an unmodified physically based skin shader.
- The projectile is rebuilt as a closed ogive with corrected outward normals, a dark solid #9E6238 bronze rear cap and a small groove. The pale recessed primer/cup and thick internal rim are removed. Received Principled shading is remapped toward warm copper without increasing reflection cost; the thin inverted hull remains for the silhouette.
- The existing pearl grip is seated at the holster mouth, tilted upward about 55 degrees from horizontal. Crossing hatch strokes add texture; hand/finger surfaces remain dark #2B2438. The white pearl handle is retained as a handle, not removed as if it were a mitten.
- Challenger has cream upper-lid masks, relaxed lid strokes and a single asymmetric smirk in f1–18. Opening clenched teeth are restricted to f19–25, preserving the later V12 standoff expression. The gun is posed nearly horizontally in the fixed barrel camera for f25–33, with its muzzle held at the original insert anchor. The arm/hand grip is re-solved to the moved gun.
- The twelve-branch irregular tumbleweed rolls on the dirt left of center during f205–235. Its scale is solved to about 3% frame height, with readable #9B714A twig strokes. The existing V12 camera never follows it.
- The twelve-lobe buckle receives a dark center ring, a polished medallion and a bright curved silver/gold specular accent.

## Stages and checks

From `D:/remotionshorts`, run `python scripts/slow_eddie_v13/launch.py build`, `polish_materials`, `finalize`, `calibrate`, `editorial`, `benchmark`. Material/detail stages are one-time patches after a fresh build; do not repeatedly apply `finalize` to an already patched V13. Inspect f15, f26, f60, f90, f222, f286 before `deliver.py`. The full comparison is `make_sheet.py`; the auxiliary junction sheet is `make_junction.py`.

All Blender stages use the exclusive shared GPU lock. Do not run another GPU render or headless Chromium concurrently. Rendering is EEVEE Next, native 1080×1920, 30 fps, frames1–300, RT off, 24 samples and the preserved 512 MiB shadow pool. Shader warmup is separate from measured animation frames. The benchmark gate is max/p95 ≤1.8 s, whole-board sampled VRAM ≤3.3 GiB.

Run embedded `slow_eddie_v13_runtime.py` before inspecting the timeline in Blender. It owns deterministic actor/camera evaluation; inherited baked camera curves remain muted. The final delivery composites the same launch and hands transitions as V12, burns unchanged captions after scene grading and muxes unchanged audio. `verify_delivery.py` checks the decoded file, source hash, camera-function identity, camera lock report, audio packets and caption identity. All-frame diagnostic flags remain in `qa/report.md`; a held holster pose is intentional.

Calibration and decoded sheets establish the inspected visuals. They do not establish a subjective percentage match to the reference or constitute direct aural review.

## Final measurements

Native1080x1920/30fps/300f/10.000s validated and decoded without errors. Audio939 packet payloads, presentation times and durations are identical to V12; ASS is byte-identical. All300 main camera/lens/focus states and the fixed insert states are retained. Forehead calibration samples #C4C8EA; cheek and jaw #FDF5EF. The V12 source hash remains unchanged.

Benchmark: p951.311/max1.320s, peak1444MiB. First full pass:379.871s, p951.511s, max2.140s, with five frames over1.8s. Those exact unchanged-source frames272/274/275/276/292 were rerendered after separate warmup at1.116-1.532s, with24 samples and no scene/camera changes. Delivered-frame timing uses those replacements: max1.760s, p951.471s. This is not a claim that the first complete pass met the strict maximum; its failed first-pass flag remains in delivery_validation.json. Peak monitored whole-board VRAM1448MiB (1.414GiB). Warmup is reported separately.

Final QA: no black/unplanned-white frames or unplanned MAD spikes. The106-120 holster hold is intentional. Corrected frames were encoded again with the locked AAC copy and captions; comparison_final.png comes from that final MP4.
