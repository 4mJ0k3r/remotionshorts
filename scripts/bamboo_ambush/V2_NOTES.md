# V2 review source

Latest user scope: V2 corrections and360p preview are complete; user now explicitly authorized1080p (correcting a180p typo). Full-HD job uses1080x1920/30fps/32samples,935frames and the same original audio. V1files and360p preview remain preserved. `run_1080p_v2.py` queues locked headless rendering then automatic mux/technicalQA; live state is `v2_1080_pipeline.json` / `v2_1080_progress.json`, output `bamboo_ambush_v2_1080p.mp4`.

- `prepare_assets_v2.py` imports the V1 drawing helpers but writes `assets_v2`. Recessed V-neck with no green tab; clean solid pupils for ordinary poses; veins retained only grenade/gag extremes; brass chin buckle removed.
- `build_bamboo_ambush_v2.py` imports the original timed build and overrides poses/contacts. Original script's sole compatibility edit is an optional BLEND_PATH override. Pre-edit script copies are in `v1_checkpoint`.
- Supine head(0,+.58,-.32), torso(0,+.05,-.38), bootsY-.62; head/torso artwork lies north-up in the pit. Initial entry blends smoothly from f21 through44. Fully closed four-piece camouflage cover in2B; only the breathing-pipe collar remains open.
- Enemy torso/pelvis lowered.12m relative to head in ordinary shots; full chin stays visible and jersey17remains readable.
- Prone5A/5C: headleft(-.45,Z.42), chest(-.15,Z.28), hips(.15,Z.22→.08), jeans/legsright. Two fixed ground palms have centresZ.026 and flattened radiusZ.026. Three articulated fingers and a palm grip the waist from the hole. Five-frame pumping cycle startsf769, preserving existingGOPaudio start25.6s.
- Underground5B/5C: smaller upright headZ-.42 plus horizontal khaki torso/boots on the lower floor; vertical pipe bottom stays in the mouth while its upper contact compresses. `audit_v2.py` checks palm supports, mouth error and entry continuity.
- Tent/tree move only in finale to the supplied reference arrangement; all12cut boundaries and audio unchanged. No text overlays; lettering is confined to the existing diegetic jersey.

Calibration: `sheet_v2.jpg` initial; `sheet_v2_confirmation.jpg` corrected confirmation. Twelve540x960peak tiles plus contact extremes in `calibration_v2_confirm`. Macro2A's final push lets the upper tube extend beyond frame; head, eyes and mouth contact stay visible.

Preview: isolated `run_blender.py` -> buildV2/auditV2/render_preview_v2.py, then `finish_preview_v2.py`. Frames in `frames_v2_360`; source/profile SHA guarded by `v2_preview_config.json`. Output `bamboo_ambush_v2_360p.mp4`; QA `qa_v2`. Preserve the existing narration/sfx file and never regenerate audio for this revision.

Use the shared atomic owner-GUID GPU lock before every headless Blender launch. No live MCP, git writes, shared-reference edits or cross-project file access.
