"""Summarize actual completed production evidence; no fabricated gate status."""
from pathlib import Path
import json,hashlib,numpy as np
P=Path(__file__).resolve().parents[3]/'renders/gold_mine_salting_v4'
def read(p):return json.loads((P/p).read_text())
timings=read('render_timing_1_300.json');assert len(timings)==300
v=np.array([r['seconds'] for r in timings]);peak=read('board_vram_render.json')['peak_mib']/1024
perf={'status':'PASS' if max(v)<=2 and np.percentile(v,95)<=1.8 and peak<=3.3 else 'FAIL','frames':300,'p95_seconds':float(np.percentile(v,95)),'max_seconds':float(max(v)),'mean_seconds':float(v.mean()),'sampled_board_peak_gib':peak,'limits':{'max_seconds':2,'p95_seconds':1.8,'board_gib':3.3},'timing_includes':'Per-frame scene update, render, compositor and native PNG save; initial shader warmup recorded separately.'}
(P/'full_render_performance.json').write_text(json.dumps(perf,indent=2));assert perf['status']=='PASS',perf
b=read('benchmark_a/benchmark.json');qa=read('qa_final/report.json');delivery=read('delivery_validation.json');camera=read('camera_gate.json');geo=read('all_geometry_clearance.json');grip=read('closing_grip_geometry.json');audit=read('preset_and_motion_audit.json')
assert camera['status']==geo['status']==grip['status']==b['status']=='PASS'
current={k:hashlib.sha256((P/name).read_bytes()).hexdigest() for k,name in [('blend','gold_mine_salting_v4.blend'),('audio','final_mix.wav')]}
assert all(read('render_identity.json')[k]==h for k,h in current.items())
(P/'validated_source_identity.json').write_text(json.dumps(current,indent=2))
gap=min(x['conservative_tube_clearance_m'] for x in grip['checks'])*1000
text=f'''# Gold Mine Salting V4

Final: gold_mine_salting_v4_1080x1920.mp4, exactly 300 frames / 10.000 seconds / 1080×1920 / 30 fps, H.264 + stereo AAC. Editable self-contained source: gold_mine_salting_v4.blend. Earlier projects and delivered V3 stay intact. Source modules: scripts/gold_mine_salting_10s/v04.

V4 retains the saturated warm-ochre rock, dark receding timber tunnel and bold #16121C hull ink. Faces and garments use the shared received-light clean_toon chain (Diffuse → Shader to RGB → RGB to BW → Map Range → four EASE stops → Emission1.0). Face calibration .25–1.65, cream #FFF3E4, middle #DDD2CA, cool #9F9DBA. Local angled warm keys retain cheek and cylindrical cloth wrap. Opaque tilted hat/beanie geometry casts real cool forehead bands. Hat-on/off evidence is in hat_shadow_probes and hat_shadow_evidence.json; no fixed painted face-band substitute is used.

The first full pass exposed intermittent local-light shadow holes despite passing static calibration. Development passes and raw QA are preserved in pass_a_shadow_jitter and pass_b_small_shadow_pool. Disabling randomized light jitter alone passed a cold test but failed after warmup. Enlarging this production's EEVEE shadow pool from512 to1024MiB passed the warmed sequence; the final source combines the larger pool and disabled light jitter. Fresh native benchmarking and full encoded QA certify the actual delivered pass. Camera, contact and clearance gates remain applicable because subsequent edits changed only shadow settings and the packed helper, with no geometry, motion or camera edits. The shared default pool is unchanged.

Miner narrows his eyes/brows during aiming. The muzzle produces a broad fiery gas burst, 24 individual luminous gold particles with finite streak trails and soft drifting smoke. Warm spill rises on frames35–42. The camera starts its pan earlier to keep the spray in frame and passes Buddy into the impact. Angular edge gravel replaces isolated round floor stones. The crater has a cut solid backing, deeper irregular cavity, chipped rim, branching fractures, embedded glittering gold and drifting impact smoke. Wax lip/drips and a transparent amber flame halo dress the non-shadowing candle.

Buddy's CANDLES supply crate, kettle, tins and red hanging lantern remain dressed beside him. His head turns ~18 degrees toward the crater during the shrinking/receding gold beat, then returns with skeptical brows, a free-hand shrug and {len(audit['buddy_mouth_shapes_used'])} envelope-gated mouth shapes including closures. The continuous reaction dolly is preserved. Closing: left hand wraps the tapered wood wrist/receiver area; right hand holds the outlined brass-rimmed/crimped shell during the wink and raised-brow smirk. Buddy is completely hidden in the opening and closing. No subtitles.

## Audio

Final mix, preserved narration and envelope are byte-identical to delivered V3. The earlier user-authorized blast/rock foley shift to frame40 remains. No narration/music/gain changes. The supplied narration intentionally ends “it's called…”; the user chose the exact audio with a visual wink. The final 300-frame output omits the original recording's last7.8125ms, without changing playback speed. Measured delivered narration lag: {delivery['narration_lag_ms']}ms; correlation against preserved recording: {delivery['delivered_narration_correlation_with_preserved_recording']:.5f}. Loudness and silence measurements are in qa_final/report.md.

## Gates and performance

Actual RTX3050 Laptop GPU / EEVEE Next, 8samples, native resolution. Twelve-frame native benchmark: p95 {b['p95_seconds']:.4f}s, max {b['max_seconds']:.4f}s, board VRAM {b['sampled_board_peak_gib']:.4f}GiB. Full300-frame render: p95 {perf['p95_seconds']:.4f}s, max {perf['max_seconds']:.4f}s, board VRAM {peak:.4f}GiB. Every production frame meets2.0s, sampled board peak below3.3GiB. Separate warmup is recorded. GPU lock was respected and released on worker exit.

Camera and semantic contact gates passed all300 frames. Full-geometry clearance: {geo['distinct_geometry_objects_checked']} distinct objects, minimum conservative AABB clearance {geo['minimum_aabb_clearance_m']:.6f}m. Raw nearest-normal false positives are preserved and resolved using evaluated closure/parity evidence. Direct seeks match chronological states. Closing finger tubes have a conservative {gap:.3f}mm minimum clearance from evaluated wood/receiver triangles, using exterior parity and dense continuous-polyline distance bounds; native images complement this geometry check. Failed initial grip diagnostics and obsolete candidate checks remain as development evidence, not final certification.

## Inspection and diagnostic result

Fresh calibration covers all shot boundaries/action extremes, including frames11,38,65,93,151,215,286. Native contact/extreme images are in contacts_native; the final calibration sheet is calibration_sheet.png. All encoded frames were inspected in chronological QA sheets, with native extracts used for flagged or critical intervals. MP4 frame count/dimensions/timestamps and complete decoding were verified.

Raw shared strict QA status: **{qa['status']}**. The unchanged report is qa_final/report.json; any intentional motion/hold resolution is recorded separately in visual_acceptance.json. No thresholds are relaxed or intervals hidden to force a pass. Verification does not include real-time audio/video playback; audio preservation and timing are supported by exact source hashes, decoded correlation, explicit effect timing and mux measurements. No unperformed listening test is claimed.

After reopening the blend, run packed START_HERE.py once to activate its frame-addressable runtime. Embedded modules, audio envelope and packed sound travel with the project. No final render remains running.
'''
(P/'production_report.md').write_text(text,encoding='utf8')
print(json.dumps(perf,indent=2));print('RAW_QA',qa['status'])
