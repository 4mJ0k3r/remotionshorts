"""Native Blender worker for the approved hook and v02 continuation."""
import json
from pathlib import Path
import sys
from uuid import uuid4

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import shorts_preflight as gate

part, phase, path = sys.argv[-3:]
out = Path(path)
s = bpy.context.scene
settings = s.render
lengths = (444, 414, 372, 422)
assert (settings.resolution_x, settings.resolution_y, settings.fps, settings.fps_base) == (1080,1920,30,1)
assert (s.frame_start,s.frame_end)==(1,lengths[int(part)-1])
settings.resolution_percentage = 100
if phase=="proof":
    plan=json.loads((out/"shot_map.json").read_text())
    frames=plan["proof_frames"]
    assert len(set(frames))==12
    resources=[]
    contacts=[]
    for frame in frames:
        s.frame_set(frame)
        resources.append(gate.validate_resources(s))
        desks=[obj for obj in s.objects if obj.name.endswith(" worktop") and not obj.hide_render]
        for torso in (obj for obj in s.objects if obj.name.endswith(" | graphic pill torso") and not obj.hide_render):
            if not desks:
                break
            desk=min(desks,key=lambda obj:abs(torso.matrix_world.translation.x-obj.matrix_world.translation.x))
            rear=max((desk.matrix_world@Vector(point)).y for point in desk.bound_box)
            front=min((torso.matrix_world@Vector(point)).y for point in torso.bound_box)
            contacts.append({"frame":frame,"actor":torso.name,"clearance_m":front-rear})
    folder=out/f"native_proof_{uuid4().hex[:8]}"
    report=gate.benchmark(s,frames,folder,p95_limit=1.8,max_limit=2.0)
    report["native_stills_dir"]=folder.name
    report["max_evaluated_triangles"]=max(check["visible_triangles"] for check in resources)
    if any(not check["pass"] for check in resources) or report["max_evaluated_triangles"]>=150000:
        report["status"]="FAIL"
    if contacts:
        contact_min=min(contacts,key=lambda item:item["clearance_m"])
        report["sampled_desk_clearance"]=contact_min
        if contact_min["clearance_m"]<0:
            report["status"]="FAIL"
    (out/"benchmark.json").write_text(json.dumps(report,indent=2))
elif phase=="render":
    folder=out/"native_frames"
    folder.mkdir(exist_ok=True)
    settings.filepath=str(folder/"frame_")
    settings.use_overwrite=False
    settings.use_placeholder=False
    bpy.ops.render.render(animation=True)
