# Calibration V2 — video gate failed

Inspected: sheet_v2_contacts.jpg, native f160/f300/f855, plus all 31 calibration images in the tiled batch. Full-contact audit: 211 chair-grip frames, max grip error 0; seated pelvis normal gap <=3.15e-8 m; settled chair-standing sole gap <=2.10e-8 m. These position checks do not certify limb/furniture clearance or framing.

Resolved from V1: stale Bezier handles crossing faces, visible 3D neck oval, crossed chair-grip arms, unsupported tilted pelvis, poor chair/jump view, classmate screen side, narrator-driven background teaching mouth.

Remaining critical findings: f855 and ending two-shots clip head edges; f940 clips the raised finger; f1446 rises into the HUD; side-angle shirt overlaps the lower face during jump; seated thighs cut the wooden seat before its front lip. V4D includes an unintended cropped foreground classmate.

Prepared in build_classroom_fart.py for revision 3: 35–50% extra camera room on two-shots, 25% on raised-finger/jump coverage; compact torso and lower shoulder anchors keep shirt below the mouth; knee route goes beyond the chair front edge before descending; remove out-of-coverage classmate layer only for the wide blackboard shot. No new render of those changes has been run.

No preview has been rendered or approved. Stop before video because critical visual gates remain failed. A further calibration cycle is required to verify the prepared changes; the initial and confirmation batches have both been used.
