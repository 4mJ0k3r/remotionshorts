"""Render the benchmark hook stills and the four brand panels only."""
import json
from pathlib import Path
import sys
from uuid import uuid4

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import BENCH, OUT
import shorts_preflight as gate

scene=bpy.context.scene
assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage)==(1080,1920,100)
assert all(i.packed_file for i in bpy.data.images if i.source=="FILE")
dest=OUT/f"benchmark_{uuid4().hex[:8]}"
counts=[]
for frame in BENCH:
    scene.frame_set(frame)
    resources=gate.validate_resources(scene)
    counts.append(resources["visible_triangles"])
    if not resources["pass"] or resources["target_exceeded"]:
        raise RuntimeError((frame,resources))
report=gate.benchmark(scene,BENCH,dest,p95_limit=1.75,max_limit=1.75)
report["native_stills_dir"]=dest.name
report["max_evaluated_triangles"]=max(counts)
if report["sampled_board_peak_gib"] is None or report["sampled_board_peak_gib"]>2.6 or report["telemetry_errors"]:
    report["status"]="FAIL"
(OUT/"benchmark.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
sign=bpy.data.objects["1998 / INTELLIGENCE"]
contacts=json.loads((OUT/"desk_contacts.json").read_text())
for frame in (1,89,405,452):
    scene.frame_set(frame)
    coords=[world_to_camera_view(scene,scene.camera,sign.matrix_world@Vector(point)) for point in sign.bound_box]
    x=[v.x for v in coords]; y=[v.y for v in coords]
    margin=min(min(x)/(max(x)-min(x)),(1-max(x))/(max(x)-min(x)),
               min(y)/(max(y)-min(y)),(1-max(y))/(max(y)-min(y)))
    contacts[str(frame)]["sign_margin_fraction"]=margin
(OUT/"desk_contacts.json").write_text(json.dumps(contacts,indent=2))
portraits=OUT/"cast_stills"; portraits.mkdir(exist_ok=True)
for frame in (501,502,503,504):
    scene.frame_set(frame)
    scene.render.filepath=str(portraits/f"frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
