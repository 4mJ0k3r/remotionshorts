# Hair sensor V3 — production plan

The latest user overhaul supersedes the V2 design and authorizes a 540×960 narrated preview after visual calibration. All source/assets/output remain in the hair_sensor namespaces. Every headless Blender call goes through run_blender.py; no live MCP, shared references, other-agent files or Git state are modified.

## Source and timing

- Supplied Viraj narration: 47.072667 s; decoded master remains unchanged.
- 1,413 frames, 30 fps; final preview 47.100 s, padding only the final 27.3 ms of audio silence.
- 21 cuts. Macro selection, scientist focus, stretch, snap, install; perfume, signal, shock, conventional sensor comparison; cable, waveform, map; mount, launch, flight, sensor insert, target reveal; disaster scan, trapped survivor, supported carry, sensor beauty.
- Every camera has an authored 8–17% linear distance move. Projection safety reframing retains the move. No added image noise or dither to defeat freeze metrics.
- Scientist is the on-camera presenter where shown; 3-frame mouth sampling uses the measured voice envelope. Victim/rescuer react rather than lip-syncing every narrator word.

## Ten overhaul gates and implementation

| Gate | V3 implementation / evidence to inspect |
| --- | --- |
| Grounding | No floor stickers. All tile/desk/prop contacts use mesh supports and shadow-casting sun, window area and desk lamp. Actual 4.2.23 API exposes fast_gi_method/distance and legacy GTAO controls; set AO method and .45 m, ray tracing stays off. Verify visible shadow results, not a nonexistent use_fast_gi flag. |
| Rich environments | Convex subdivided displaced skin, Voronoi pore bump, follicle mounds, dish rim, f/1.4 macro. Beveled scuffed glossy ceramic tiles, alpha .25 glass, actual mullions, window light and sun 4.5. |
| Character design | Brown angular hair cap/streaks; round spectacles; thinner stable ink, baked warm/cool gradient; blue pinstriped shirt/red tie, shaded pelvis capsule; 75% Principled / 25% emission. |
| Cadence/cameras | 21 explicit scene/camera pairs. Macro inserts alternate with large focus/shock reactions. Explicit camera identity eliminates stale timeline-marker selection. |
| Three-act atmosphere | Cool clinical lab/gold sunlight; warm-grey/amber dusty rescue with dimmer ambient and 80 drifting ash cards plus true density volume; gold sunrise hero Sun 5.0. Vignette floor .55 before HUD. |
| Detailed props | Irregular tapered keratin curves (.15 tip/base radius ratio), traced PCB, motor bells/vents, carbon noise shader, concentric alpha rotor discs 45 degrees/frame; jagged aggregate, bent rebar, solid broken facades and boolean bites. |
| FX light | 35 alpha-faded pink scent puffs, 3D petals and moving 60W pink point; real 450W green 38-degree shadow-casting spot below drone, scattering in actual dust volume. |
| Single HUD | One top-center dark navy rounded pill with 2px gold border. No bottom badge, field-notes text, subtitles or second career stamp. Monitor graphics remain diegetic. |
| Acting | Independent head billboard, expression bank, audio-envelope mouth planes, deterministic blink, attached finite temple sweat, curved articulated arms, semantic tweezer/atomizer grips and palm-supported launch; finite wave/lift/carry. |
| Delivery | 12-tile sheet plus all 21 cut samples; same approved saved scene for full 540×960 preview; original short_qa.py plus exact decoded-frame duplicate hashes, frame count/audio checks. |

## Contact and camera verification

v3_contacts.py evaluates every frame of the tweezer grip and atomizer press, measuring world and projected delivery-pixel error. Four landing feet are checked throughout palm support. Touch and support use actual saved-object transforms; 1 output pixel / 2 mm are acceptance ceilings. Additional rescue and action continuity must be judged on rendered frame sequences, not inferred from numerical checks.

Calibrate all 21 cut middles, with 12 representative samples in sheet_v3.jpg. The initial/correction sheets were followed by targeted contact refinements of four cuts found during actual-frame review. Their explicit ranges and reasons are retained in v3_patch_manifest.json. The base source is hair_sensor_v3.blend; the final source is hair_sensor_v3_final.blend. Unchanged ranges use the same base geometry/animation; four replaced ranges use the final source. Preserve first sheets and backups, and check both sides of every replacement. Run the unchanged shared QA script on the final muxed MP4; preserve all flags without weakening thresholds.

User's desk correction: final delivery source is now `hair_sensor_v3_desk_fixed.blend`. Six visible scientist shots were moved behind the actual bench rear edge, with camera/framing compensation, re-anchored shoulders, and hand targets preserved. `v3_desk_patch_manifest.json` records the six replacement ranges; `v3_desk_clearance.json` checks actual evaluated body/hips/leg/foot meshes on every frame. Minimum clearance is approximately 13 cm. Mesh-based curve checks are used because Blender's evaluated curve bounding boxes retain stale bounds despite correctly updated mesh vertices. Re-render all six ranges before mux; only those complete replacement ranges may supersede the earlier frame sequence.
