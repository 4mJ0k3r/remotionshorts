import json,sys
from pathlib import Path
from uuid import uuid4
import bpy
H=Path(__file__).resolve().parent
R=H.parents[2]
O=R/"renders/padoda_billionaire/v01"
sys.path[:0]=[str(H),str(R/"scripts")]
from build import CAL,BENCH
import shorts_preflight as gate
s=bpy.context.scene
preview=sys.argv[-1]=="preview"
if preview:
    d=O/"preview";d.mkdir(exist_ok=True)
    s.render.resolution_percentage=42
    for f in CAL:
        s.frame_set(f);s.render.filepath=str(d/f"frame_{f:04}.png")
        bpy.ops.render.render(write_still=True)
else:
    d=O/"benchmark"
    if d.exists():d=O/f"benchmark_{uuid4().hex[:8]}"
    counts=[]
    for f in BENCH:
        s.frame_set(f);counts.append(gate.validate_resources(s))
    print("GEOMETRY_MAX",max(x["visible_triangles"] for x in counts),flush=True)
    report=gate.benchmark(s,BENCH,d,p95_limit=1.8,max_limit=2.0)
    report["max_evaluated_triangles"]=max(x["visible_triangles"] for x in counts)
    if report["max_evaluated_triangles"]>=150000 or not all(x["pass"] for x in counts):report["status"]="FAIL"
    report["native_stills_dir"]=d.name
    (O/"benchmark.json").write_text(json.dumps(report,indent=2))
