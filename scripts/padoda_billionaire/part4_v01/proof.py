"""Validate native delivery settings and benchmark the twelve Stage 1 stills."""
import json
from pathlib import Path
import sys
from uuid import uuid4

import bpy

here=Path(__file__).resolve().parent
sys.path.insert(0,str(here))
from build import BENCH, END, OUT
import shorts_preflight as gate

scene=bpy.context.scene
assert (scene.frame_start,scene.frame_end,scene.render.fps)==(1,END,30)
assert scene.render.engine=="BLENDER_EEVEE_NEXT" and not scene.eevee.use_raytracing
assert all(image.packed_file for image in bpy.data.images if image.source=="FILE")
destination=OUT/f"benchmark_{uuid4().hex[:8]}"
resources=[]
for frame in BENCH:
    scene.frame_set(frame)
    resources.append(gate.validate_resources(scene))
report=gate.benchmark(scene,BENCH,destination,p95_limit=1.8,max_limit=2.0)
report["max_evaluated_triangles"]=max(row["visible_triangles"] for row in resources)
report["native_stills_dir"]=destination.name
if not all(row["pass"] for row in resources) or report["max_evaluated_triangles"]>=150000:
    report["status"]="FAIL"
(OUT/"benchmark.json").write_text(json.dumps(report,indent=2))
