"""Check the fast motion pass at delivery size before rendering the whole reel."""
import hashlib
import json
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "renders/ricks_benchmark_10s/v01c"
sys.path.insert(0,str(ROOT/"scripts"))
import shorts_preflight as gate

scene = bpy.context.scene
camera = scene.camera
checks = (23,30,96,105,139,147,181,216,230,252,268,285)
scene.render.resolution_percentage = 50
assert scene.render.engine=="BLENDER_EEVEE_NEXT" and not scene.eevee.use_raytracing
assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,300,30)
feet = [scene.objects[f"Hero B | foot tick {side}"] for side in ("L","R")]
previous = [None,None]
max_drift = 0
cube_gap = 0
top = scene.objects["Pawn counter | worktop"]
cube = scene.objects["Memory cube | glowing chassis"]
entry = None
for frame in range(139,265):
    scene.frame_set(frame)
    if frame==139:
        head = scene.objects["Hero B | ellipsoid head"]
        entry = [list(world_to_camera_view(scene,camera,head.matrix_world @ Vector(v))) for v in head.bound_box]
    for i,(obj,start) in enumerate(zip(feet,(139,134))):
        center = obj.matrix_world.translation.copy()
        if 140<=frame<=220 and 0<(frame-start)%10<=4:
            max_drift = max(max_drift,(center-previous[i]).length)
        previous[i] = center
    if frame>=226:
        bottom = min((cube.matrix_world @ Vector(p)).z for p in cube.bound_box)
        tabletop = max((top.matrix_world @ Vector(p)).z for p in top.bound_box)
        cube_gap = max(cube_gap,abs(bottom-tabletop))
assert max_drift<.0001,max_drift
assert cube_gap<.0001,cube_gap
assert max(v[0] for v in entry)>.07 and min(v[0] for v in entry)<.93,entry
max_triangles = 0
for f in checks:
    scene.frame_set(f)
    resources=gate.validate_resources(scene)
    assert resources["pass"],resources
    max_triangles=max(max_triangles,resources["visible_triangles"])
assert max_triangles<150000,max_triangles
target=OUT/"benchmark_540p"
if target.exists():
    import uuid
    target=OUT/("benchmark_540p_"+uuid.uuid4().hex[:8])
report=gate.benchmark(scene,checks,target,resolution=(1080,1920,50),p95_limit=2.0,max_limit=2.0)
with (OUT/"ricks_benchmark_v01c.blend").open("rb") as master:
    report["blend_sha256"]=hashlib.file_digest(master,"sha256").hexdigest()
report.update(max_sampled_evaluated_triangles=max_triangles,
              native_stills_dir=target.name,
              max_planted_foot_drift_m=max_drift,max_cube_bottom_gap_m=cube_gap,
              hero_entry_projected_bounds=entry)
(OUT/"benchmark.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
assert report["status"]=="PASS",report
