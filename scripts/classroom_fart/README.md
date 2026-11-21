# Classroom fart

Current request: surgical V2, complete 1635-frame preview. Approved source is `renders/classroom_fart/classroom_fart_surgical_v2_verified.blend`, locked by `calibration_v2_approved.json`. Run `queue_v2.py` for its fresh frames in `v2_full_frames`; final target is `classroom_fart_v2_full.mp4`. Updated 24-tile review is `sheet_v2.jpg`; numeric evidence is `surgical_v2_contact_audit.json`. The new full-video request supersedes the earlier stop request.

V2 uses a 0.46m seat, +/-0.23m grips, actual sole/seat contact, solid oval eyes, a skull-clipped hair cap, separate centered pressure/rear-stream/desk-haze effects, a supported desktop slump, and a nose target in head-art space. The complete room is rebased by 180 degrees around the hero chair so author +Y is behind the chair; unchanged set/camera/lighting relationships are preserved. Static batching must use evaluated world matrices to include that rebase. The historical V6 details below describe the earlier review export.

Authoritative approved scene: `D:\remotionshorts\renders\classroom_fart\classroom_fart_v6.blend`.
Preview target: `D:\remotionshorts\renders\classroom_fart\classroom_fart_preview.mp4`, 540×960, 1635 frames, 30fps, 54.5s, supplied Hindi narration. Base scene dimensions are 1080×1920.

`calibration_approved.json` locks the source hash. `calibration_frame_map.json`, `sheet_final_contacts.jpg`, the full contact audit and V5/V6 patch manifests record the review evidence. Historical V1–V5 builds and failed calibration sheets are retained as history, not delivery artifacts.

`queue_preview.py` renders the approved source in 300-frame locked runs with 15-second release windows. It resumes complete PNGs, requires the matching source hash for every chunk, and then invokes `finish_preview.py` to mux and run the unchanged shared QA script. `Stop-ClassroomFart.ps1` stops only registered project children and stops the queue.

`build_classroom_fart.py` now consolidates the final staging choices; a fresh rebuild saves separately as `classroom_fart_v6_rebuild.blend` and must be calibrated before use. It does not overwrite the approved V6 scene. Historical patch scripts explain the path from initial build to approved scene; do not execute them for inspection.

No live Blender MCP. Never overwrite/delete another project's GPU lock or touch another project's files. All headless Blender commands must go through the owned GUID-lock launcher.
