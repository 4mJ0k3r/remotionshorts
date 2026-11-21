"""Reopen the saved scene for native proofs or a 50 percent preview."""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build import BENCH, END, OUT, PROOFS
import shorts_preflight as gate

s=bpy.context.scene
r=s.render
assert (r.resolution_x,r.resolution_y,r.resolution_percentage,r.fps,r.fps_base,s.frame_end)==(1080,1920,100,30,1,END)
assert all(img.packed_file for img in bpy.data.images if img.source=="FILE")
phase=sys.argv[-1]
if phase=="proof":
    folder=OUT/f"native_proof_{uuid4().hex[:8]}"
    resources=[]
    for f in (*BENCH,*PROOFS):
        s.frame_set(f)
        resources.append(gate.validate_resources(s))
    report=gate.benchmark(s,BENCH,folder,p95_limit=1.8,max_limit=2.0)
    report["max_evaluated_triangles"]=max(x["visible_triangles"] for x in resources)
    report["native_stills_dir"]=folder.name
    if any(not x["pass"] or x["visible_triangles"]>=150000 for x in resources):
        report["status"]="FAIL"
    (OUT/"benchmark.json").write_text(json.dumps(report,indent=2))
    girl=bpy.data.objects["Shoko carrying books"]
    classmates=[bpy.data.objects[name] for name in ("School corridor student","Second school corridor student")]
    books=bpy.data.objects["Schoolbook stack carried in both hands"]

    def planar_bounds(root):
        descendants=[]
        pending=list(root.children)
        while pending:
            child=pending.pop()
            pending.extend(child.children)
            if child.type in ("MESH","CURVE") and not child.hide_render:
                descendants.extend(child.matrix_world@Vector(p) for p in child.bound_box)
        return [(min(v[index] for v in descendants),max(v[index] for v in descendants)) for index in (0,1)]

    gaps=[]
    contacts=[]
    mittens=[obj for obj in girl.children_recursive if obj.name.startswith("Shoko carrying books flat mitten pivot")]
    for f in range(578,633):
        s.frame_set(f)
        girl_bounds=planar_bounds(girl)
        for student in classmates:
            axis_gaps=[max(0,a[0]-b[1],b[0]-a[1]) for a,b in zip(girl_bounds,planar_bounds(student))]
            gaps.append((Vector(axis_gaps).length,f))
        if len(mittens)==2:
            anchors=[books.matrix_world@Vector((dx,.0,.057)) for dx in (-.135,.135)]
            hands=sorted((obj.matrix_world.translation for obj in mittens),key=lambda value:value.x)
            anchors.sort(key=lambda value:value.x)
            contacts.extend((a-b).length for a,b in zip(anchors,hands))
    margin,frame=min(gaps)
    (OUT/"hallway_contacts.json").write_text(json.dumps({"minimum_body_planar_gap_m":margin,
        "min_gap_frame":frame,"max_mitten_to_book_side_m":max(contacts) if contacts else None},indent=2))
    cast=OUT/"cast_stills"
    cast.mkdir(exist_ok=True)
    for f in PROOFS:
        s.frame_set(f)
        r.filepath=str(cast/f"frame_{f:04}.png")
        bpy.ops.render.render(write_still=True)
elif phase=="preview":
    folder=OUT/"preview_540p_frames"
    folder.mkdir(exist_ok=True)
    r.resolution_percentage=50
    r.filepath=str(folder/"frame_")
    span=os.environ.get("SHOKO_V03_PREVIEW_RANGE")
    if span:
        s.frame_start,s.frame_end=map(int,span.split(":"))
    bpy.ops.render.render(animation=True)
