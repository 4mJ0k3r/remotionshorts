# Project Paradox India EP03 — ₹5 Blade Loophole

CURRENT USER SCOPE (2026-11-18): finish design and deliver ONLY the first
10 seconds at 540x960 / 30fps with matching audio. Full 1080p rendering is
not authorized until a new explicit request. `scope.json` enforces this.

Active production, v01. Source narration is identified in the render input manifest.
1401 frames / 46.7s; preserve 46.680833s recording, pad ~19.17ms, never time-stretch.
No subtitles or floating text. Physical coin relief, calendar, jar tags and stamp only.

Latest character clarification: faces, hands, arms and legs must look flat 2D
on screen even if geometry is 3D. Cream graphic faces, dark flat hands/limbs,
bold outlines; no glossy mittens, modeled facial relief or tube highlights.
Match the two supplied example-animation screenshots. Text seen in those
references is excluded by this production's no-subtitle/no-overlay brief.

| Spoken cue | Visible action / camera | Contact and persistence |
|---|---|---|
| 2009 / RBI / paanch rupaye | Coin macro and barber-shop reveal | Coin rests in press slot; calendar is mounted artwork |
| shaving blades | Press stroke, blade exit, customer's frightened mirror reaction | Press on anchored slides; mirror handle wrapped |
| darasal / gayab | Market tracking shot, coins vanish into sack | Jar supported, hand at jar neck; sack mouth stays open |
| cupro-nickel | Heavy coin lands on balance pan, edge macro | Coin supported on pan; scale pivots at central axle |
| smugglers / loophole | Warm amber furnace workshop reveal | Feet supported; gloves/tongs and crucible share semantic grips |
| pighla / chheh razor blades | Coin enters ladle, emissive pour fills six cavities, six blades fan | No fluid sim; stream starts at lip, ends at mold; no blade intersections |
| do rupaye / baarah | Market pan and six ₹2 coins versus one ₹5 | Labels are physical tags; scale loads remain supported |
| chuckle / metal baarah ka | Greedy close-up, finite chuckle and coin gesture | Narration is off-screen VO; reactions do not lip-sync the narrator |
| loss rokne / patle steel | Officer stamp, lever, thin steel coins into chute | Stamp/grips, lever pivot and chute connected mechanically |
| kyunki | Orbital coin reset into matching opening camera/light state | End pose matches opening; FX/music tails loop smoothly |

Outdoor sets use shared warm/cool sky rig. Interior uses INTERIOR_WARM_CAVERN
with no foreground mist. Four sets live in isolated stage groups and only the
active stage/lights render. Root/limb/head poses are stateless by frame.

Approved references inspected: V13 forehead native frame and Gold Mine V4
calibration sheet. Historical files are examples, not runtime source authority.
Reusable primitive/contour/grip constructors adapted from the Gold Mine geometry
helper; approved files remain unmodified. Repository-generated town stall assets are reused
where available and sanitized before calibration. Shader/motion baseline is shared.

Next gates: inspect all shot/contact/junction extremes; actual every-frame
camera/prop clearance; native brim and finger crops; 12-frame timing/VRAM;
full render only after these pass. Full authorized deliverable remains pending.
