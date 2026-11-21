# Hair sensor — calibration scope

Project folders: `scripts/hair_sensor/` and `renders/hair_sensor/`.
Narration: supplied Viraj MP3, measured 47.072667 s. Master: 1,413 frames at 30 fps.
The supplied Hindi script is the wording reference; CPU Whisper word times are provisional timing evidence, with transcription errors preserved in `transcript.json`.
Voice is external narration. Scientist, survivor and rescuer have intentional listening/reaction mouths, rather than speaking along with the narrator.

| Time / frames | Narration cue | Visible action | Pose and gaze | Camera and focus | Contact / effect |
| --- | --- | --- | --- | --- | --- |
| 0–5.6 / 1–168 | Hair seems useless | Select one hero curl from the forest | Scientist offscreen | Shallow low macro, hero filament | Chrome jaws approach filament |
| 5.6–8.3 / 169–249 | Scientist plucks it | Stretch, snap and settle | Grip follows tool | Macro push, filament | Release near 7.95 s; finite recoil |
| 8.3–9.7 / 250–291 | Install on PCB | Lower into electrode assembly | Proud smirk, look to bench | Eye-level medium close | Filament-to-electrode and tweezer grip |
| 9.7–12.17 / 292–365 | Perfume scent | Atomizer and scent ribbon | Spray pose, eyes on sensor | Low tabletop macro | Atomizer grip; tapered petals/ribbon |
| 12.17–19.17 / 366–575 | Faster signal, machines fail | Orange filament response, delayed conventional sensors | Scientific insert | Macro then wider rack-focus comparison | Orange interactive point light, green LED |
| 19.17–28.1 / 576–843 | Computer and navigation software | Cable carries signal; waveform becomes map | Over-shoulder rear artwork | Push to monitor | USB path; timed monitor-plane visibility |
| 28.1–30.7 / 844–921 | Mounted on mini drone | Rotor startup and palm launch | Proud launch pose | Low close, drone focus | Landing feet meet palm until lift |
| 30.7–34.3 / 922–1029 | No remote, follows smell | Finite banked flight along scent | Autonomous drone | Behind-drone follow | Orange sensor and pink trail |
| 34.3–36.97 / 1030–1109 | Finds other curly hairs | Specimen dish reveal | Scientist celebrates | Over-drone reveal | Dish supports hair cluster |
| 36.97–39.17 / 1110–1175 | Emergency use | Drone scans damaged buildings | Drone foreground | Low establishing track | Green spot, transparent air beam, floor rings |
| 39.17–42.4 / 1176–1272 | Living people under rubble | Find survivor in crevice | Worried survivor raises hand | Low crevice close | Slab occlusion, human scent plume |
| 42.4–47.1 / 1273–1413 | Career punchline | Firefighter carries survivor; sensor beauty | Happy rescue pose | Low medium then macro at f1355 | Supporting arm, career stamp |

## Construction and identity

- Characters: stable cream heads, 15% clipped cool crescents, solid oval eyes, horizontal blink masking, independent camera-facing head pivots. Flat shared-coordinate torso and limb artwork; scene-lit 78% Principled / 22% emission.
- Sensor board: 1.03 × 0.65 m in laboratory layout; on-drone board uses a consistent miniature assembly factor .43. Macro framing changes optics, not the board proportions.
- Hero hair: dark-brown .008 m curve bevel, chrome tweezers, three electrode blocks. Wired form is an intentionally reshaped version for the PCB.
- Drone: four motor pods and rotors; model proportions stay fixed. Explicit scene staging scales are documented in code for macro/hero inserts; calibration must compare projected proportions.
- Light: warm key / cool fill in lab; dusty warm/cool disaster set; event-associated pink, orange and green effects. Ray tracing off, simplify on, subdivision cap 2.
- Graphics: English ASCII screen overlays after grade/vignette; no subtitles. Monitor content is diegetic scene artwork.

## Isolation and authorized stopping point

`run_blender.py` claims the shared root GPU lock with O_EXCL, GUID ownership and project/PID/phase JSON. Every headless invocation uses it, including scene builds. It checks headless processes rather than idle GUI Blender, waits 15 s, and never removes a foreign/stale lock. Profile/temp/log output is project-local. The existing former-project standalone Blender executable is used read-only; no live MCP or other-agent files are accessed.

This stage ends at visual calibration. One 12-frame batch at 540×960 / 16 EEVEE samples, inspected as a contact sheet and native frames. A consolidated correction and confirmation batch can follow if needed. Full video and full-interval motion/contact validation remain pending after this stage. A contact sheet does not certify animation or lip sync.
