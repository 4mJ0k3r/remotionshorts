import json,sys
from pathlib import Path
from uuid import uuid4
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
H=Path(__file__).resolve().parent
R=H.parents[2]
O=R/"renders/padoda_billionaire/v03"
sys.path[:0]=[str(H),str(R/"scripts")]
from build import BENCH
import shorts_preflight as gate
s=bpy.context.scene

def screen_bounds(obj):
    points=[world_to_camera_view(s,s.camera,obj.matrix_world@Vector(corner)) for corner in obj.bound_box]
    return tuple((min(p[i] for p in points),max(p[i] for p in points)) for i in range(3))

def audit_framing():
    arms=[obj for obj in s.objects if obj.name.startswith("Hero workshop | round-tipped arm")]
    notes=[obj for obj in s.objects if obj.name.startswith("Emerald bank note")]
    coin=bpy.data.objects["Coin bevelled grip edge"]
    face=bpy.data.objects["Hero vault | wink"]
    workshop_margin=1.0
    coin_margin=1.0
    face_intersections=[]
    for frame in (*range(53,78),*range(172,203),*range(235,262)):
        s.frame_set(frame)
        depsgraph=bpy.context.evaluated_depsgraph_get()
        if frame<=77:
            for arm in arms:
                evaluated=arm.evaluated_get(depsgraph)
                mesh=evaluated.to_mesh()
                for vertex in mesh.vertices:
                    xy=world_to_camera_view(s,s.camera,evaluated.matrix_world@vertex.co)
                    workshop_margin=min(workshop_margin,xy.x,1-xy.x)
                evaluated.to_mesh_clear()
        elif frame<=202:
            x,y,_=screen_bounds(coin.evaluated_get(depsgraph))
            coin_margin=min(coin_margin,x[0],1-x[1],y[0],1-y[1])
        else:
            face_x,face_y,_=screen_bounds(face.evaluated_get(depsgraph))
            for note in notes:
                x,y,depth=screen_bounds(note.evaluated_get(depsgraph))
                if depth[0]>0 and x[0]<face_x[1] and x[1]>face_x[0] and y[0]<face_y[1] and y[1]>face_y[0]:
                    face_intersections.append([frame,note.name])
    (O/"framing_check.json").write_text(json.dumps({
        "min_workshop_arm_horizontal_margin_fraction":workshop_margin,
        "min_coin_frame_margin_fraction":coin_margin,
        "cash_projection_overlaps_on_face":face_intersections,
    },indent=2))

stage=sys.argv[-1]
if stage in {"motion","coin"}:
    audit_framing()
    d=O/"motion_frames"
    d.mkdir(exist_ok=stage=="coin")
    s.render.resolution_percentage=50
    s.render.filepath=str(d/"frame_")
    if stage=="coin":
        s.frame_start,s.frame_end=152,202
    bpy.ops.render.render(animation=True)
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
