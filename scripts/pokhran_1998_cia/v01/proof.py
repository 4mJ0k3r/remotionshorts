"""Render the benchmark hook stills and the four brand panels only."""
import json
from pathlib import Path
import sys
from uuid import uuid4

import bpy

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
report=gate.benchmark(scene,BENCH,dest)
report["native_stills_dir"]=dest.name
report["max_evaluated_triangles"]=max(counts)
(OUT/"benchmark.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
portraits=OUT/"cast_stills"; portraits.mkdir(exist_ok=True)
for frame in (501,502,503,504):
    scene.frame_set(frame)
    scene.render.filepath=str(portraits/f"frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
