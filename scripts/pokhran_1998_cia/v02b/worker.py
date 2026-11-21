"""Native calibration and 540p-only motion preview for the isolated hook."""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

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
    plaque=bpy.data.objects["1998 / INTELLIGENCE"]
    shafts=[o for o in bpy.data.objects if o.name.startswith("Industrial shaft steel outer frame")]

    def horizontal_margin(objects):
        xs=[world_to_camera_view(scene,scene.camera,obj.matrix_world@Vector(point)).x
            for obj in objects for point in obj.bound_box]
        return min(min(xs),1-max(xs))

    margins={}
    for name,objects,frames in (
        ("desk_sign",[plaque],[*range(1,67),*range(397,445)]),
        ("all_five_shafts",shafts,[*range(175,295),*range(338,370)]),
    ):
        measures=[]
        for f in frames:
            scene.frame_set(f)
            measures.append((horizontal_margin(objects),f))
        value,frame=min(measures)
        margins[name]={"min_side_fraction":value,"frame":frame}
    suit=bpy.data.objects["CIA Boss | graphic pill torso"]
    desk=bpy.data.objects["Front console worktop"]
    apron=bpy.data.objects["Opaque whole front desk panel"]
    legs=[obj for obj in bpy.data.objects if obj.name.startswith("CIA Boss | ") and "leg" in obj.name
          and obj.type=="CURVE"]
    rear=max((desk.matrix_world@Vector(point)).y for point in desk.bound_box)
    apron_rear=max((apron.matrix_world@Vector(point)).y for point in apron.bound_box)
    tested=[]
    leg_checks=[]
    for f in (*range(1,67),*range(397,445)):
        scene.frame_set(f)
        nearest=min((suit.matrix_world@Vector(point)).y for point in suit.bound_box)
        tested.append((nearest-rear,f))
        if legs:
            nearest_leg=min((leg.matrix_world@position).y-leg.data.bevel_depth
                            for leg in legs for spline in leg.data.splines for point in spline.bezier_points
                            for position in (point.handle_left,point.co,point.handle_right))
            leg_checks.append((nearest_leg-apron_rear,f))
    depth,frame=min(tested)
    margins["suit_behind_worktop"]={"minimum_clearance_m":depth,"frame":frame}
    if leg_checks:
        depth,frame=min(leg_checks)
        margins["legs_behind_desk_apron"]={"minimum_clearance_m":depth,"frame":frame}
    (OUT/"framing_checks.json").write_text(json.dumps(margins,indent=2))
    folder=OUT/"proof_frames"
    folder.mkdir(exist_ok=True)
    settings.resolution_percentage=50
    for f in (25,31,215,290,315,420,429,444):
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
