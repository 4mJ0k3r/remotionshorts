"""Native calibration and 540p-only motion preview for the isolated hook."""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_hook import BENCH, CONTACT, END, OUT
import shorts_preflight as gate

scene=bpy.context.scene
settings=scene.render
assert (settings.resolution_x,settings.resolution_y,settings.fps,scene.frame_end)==(1080,1920,30,END)
assert all(img.packed_file for img in bpy.data.images if img.source=="FILE")
phase=sys.argv[-1]
if phase=="proof":
    dest=OUT/f"native_benchmark_{uuid4().hex[:8]}"
    counts=[]
    for f in (*BENCH,*CONTACT):
        scene.frame_set(f)
        counts.append(gate.validate_resources(scene)["visible_triangles"])
    report=gate.benchmark(scene,BENCH,dest,p95_limit=1.8,max_limit=2.0)
    report["max_evaluated_triangles"]=max(counts)
    report["native_stills_dir"]=dest.name
    if max(counts)>=150000 or report["sampled_board_peak_gib"] is None or report["sampled_board_peak_gib"]>3.3:
        report["status"]="FAIL"
    (OUT/"benchmark.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    folder=OUT/"cast_stills"
    folder.mkdir(exist_ok=True)
    settings.resolution_percentage=50
    for f in (501,502,503,504):
        scene.frame_set(f)
        settings.filepath=str(folder/f"frame_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
elif phase=="preview":
    settings.resolution_percentage=50
    folder=OUT/"preview_540p_frames"
    folder.mkdir(exist_ok=True)
    settings.filepath=str(folder/"frame_")
    bounds=os.environ.get("POKHRAN_V02_PREVIEW_RANGE")
    if bounds:
        scene.frame_start,scene.frame_end=map(int,bounds.split(":"))
    bpy.ops.render.render(animation=True)
