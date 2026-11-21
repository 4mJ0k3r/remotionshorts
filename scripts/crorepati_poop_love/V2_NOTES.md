# V2 surgical calibration patch

Delivery gate: inspect `renders/crorepati_poop_love/sheet_v2.jpg` and wait for user approval. No movie render. The 18 requested sample frames and 540×960 review size are unchanged. Native scene remains 1080×1920, 30 fps, frames 1–2124.

## Changes

- Toilet/family seating uses surface-height pelvis placement, actual thigh and shin segments, a rounded knee corner and lower legs beyond the furniture front. A quadratic using the knee only as a control point did not pass through the knee and looked like standing legs. Adult knee angles are about 94.4°, children about 97.3°. Sole heights are floor-contact for adults and dangling for children.
- The commode is now a hollow double-walled bowl. Its dark cavity is recessed by 0.12 m; it cannot draw a flat disc across the waist. Trousers remain at the ankles.
- The kiss has equal character depth and stable head scale. Current painted heads are about 0.8 m across, so literal ±0.21 m centers would intersect. Centers settle at ±0.405 m around the mansion origin; facial features retain 22% radius parallax. Hero closes his eyes, millionaire shows surprise/blush, lip shapes meet at the inner edges and hearts rise above the actual head tops. The brief's lower FX heights would intersect these taller rigs' faces.
- Love-struck millionaire has a curved smile and a jaw/lower-lip hand target that leaves the mouth visible. The three hallway characters now occupy left foreground, center rear and right midground, with angry red butler face and ear steam.
- The cuddle has higher/rear and lower/front poses, head/backrest clearance and a folded red blanket with gold trim covering the legs. Family seating remains independently articulated.
- Street horizon has a stone wall, wrought iron fence, warm-window facades and layered foliage. Empty pockets are lit white cloth flaps attached at the hips rather than detached ellipsoids.
- Cafe doorway has warm interior light, timber jambs/header and scene-native CAFE lettering beneath the striped awning. The kick boot uses cafe-local coordinates, the airborne actor is forward of the facade, and the camera keeps the complete head inside frame.
- Wedding background has lawn, hedges, flowering trees and a white stone balustrade. Camera and front-left pew staging keep the crying butler fully visible.
- Montage day stamps for cuts 12–15 are removed. Only the brief 5 YEARS LATER stamp remains at frames 1757–1850; there are no subtitles or permanent HUD.
- The four-toilet bathroom insert has additional framing margin. An extra f1810 staging still is separate from the exact 18-tile sheet.

## Evidence and scope

`calibrate.py verify` checks all 2,124 directly assigned head/camera transforms and DOF states, evaluates the dependency graph for calibration peaks, checks projected head bounds and four door-contact targets, checks ten seated leg poses and the kiss head gap, and tests complete toilet bounds at f1757/f1810/f1879. `rig_checks_v2.json` records the results. These metadata checks and calibration stills are not a review of a fully rendered motion clip.

Previous V1 sources, blend and sheet are preserved under `renders/crorepati_poop_love/source_v1/`, `crorepati_poop_love_v1.blend`, `calibration_v1/` and `sheet_v1.jpg`. Both the main `.blend` and `_v2.blend` contain the updated scene. Use the owner-checked launcher for every background Blender operation and release only its own GPU lock.
