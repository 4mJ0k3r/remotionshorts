# Classroom fart — isolated build plan

2026-11-13 authorization: user answered "Yes—continue until verified" to additional calibration cycles followed by the passing preview. This supersedes the default two-batch calibration limit for this project; no repeat approval is needed for corrective verification.

Source: user briefing, 18 named cuts, 1–1635 at 30 fps. Shared end/start labels are resolved by assigning each boundary frame to the incoming cut (no overlap). The 3B and 4B inserts remain within their named cut.

Audio: Downloads/ElevenLabs_2026-11-12T19_21_24_Viraj - Rich, Confident and Expressive_pvc_s30_sim75_v4.mp3, measured 54.5175 seconds. Output is 54.5 seconds; only the trailing 17.5 ms is outside the movie. CPU transcription provides timing evidence, with machine-recognition errors retained. Main audio is narration/internal thought; protagonist mouths follow the real envelope only during the quoted ending, 52.14–54.30 seconds. Teacher's teaching beat has independent speaking poses, not global narrator lip-sync.

Contact anchors: real chair seat top Z=.58; seated pelvis center Z=.71, radius=.13. Desk top Z=1.0125, rear edge Y=.30, actor center Y=-.20. Chair grips lie on X=±.325, Y=.02, Z=.58 relative to the chair floor pivot. Floor soles at Z=.019; final perched soles at Z=.58. Seat, backrest and actor use one finite chair-rock transform; 45° lean is baked around the supported hip and mechanically tilts the backrest. Airborne interval deliberately releases feet; they return to the same seat.

Occlusion: actual furniture depth occludes lower bodies, independently facing head pivots protect faces. Near/far curved arms follow shoulder anchors; head-touch routes go outside the skull. Vapor originates behind/below the torso and is depth occluded. Foreground wall is cut away for side coverage. HUD is composited after grade/vignette; no subtitles.

Character intent: cream irregular heads, cool clipped crescents, brown variable ink, polygon hair with caramel strokes, solid pupils with lid masks, separate pose planes switched on constant keys, light-sensitive 78/22 head shader. Blue/red/white hero and lime/orange friend; explicit glossy pelvis as requested. Independent camera-facing heads and grouped feature parallax. Finite acting, exact holds, no arbitrary idle wobble.

Stages: author -> locked headless build -> 15-tile calibration plus additional all-cut/contact frames -> inspect native contact frames -> one consolidated correction if needed -> reviewed-source preview at 540x960 -> Hindi mux -> unchanged shared short_qa.py -> inspect delivered frames. Saved scene retains 1080x1920 base dimensions.

Isolation: all new writes under scripts/classroom_fart and renders/classroom_fart, except atomic shared GPU lock. Read-only Blender executable reused; private user resources and temp directories. No live Blender MCP, shared Git writes, foreign process termination or other-project file access. Atomic owner GUID lock is held across each Blender run and removed only by its owner. GPU rendering yields between bounded chunks. Stop-ClassroomFart.ps1 stops only registered owned children.

Reference limit: DUAL URGE sheet was named but no accessible file was supplied. Match the explicit written DNA and the available house contracts; do not claim a verified visual match to that unavailable sheet.
