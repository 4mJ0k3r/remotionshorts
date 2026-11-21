"""Verify v2 blend animation integrity (runs headless, no render)."""
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "caveman_toilet"
bpy.ops.wm.open_mainfile(filepath=str(OUT / "caveman_toilet.blend"))

def report(obname, path):
    ob = bpy.data.objects.get(obname)
    if not ob or not ob.animation_data or not ob.animation_data.action:
        print(f"VERIFY {obname}: NO ACTION")
        return
    act = ob.animation_data.action
    fcs = [fc for fc in act.fcurves if fc.data_path == path]
    info = [(fc.array_index, len(fc.keyframe_points)) for fc in fcs]
    print(f"VERIFY {obname} {path}: {info}")
    for fc in fcs:
        if len(fc.keyframe_points):
            v = fc.evaluate(500)
            print(f"   idx{fc.array_index} f500={v:.4f}")

report("torso_caveman", "location")
report("torso_caveman", "rotation_quaternion")
report("torso_buddy", "rotation_quaternion")
report("headpivot_caveman", "location")
report("arm_caveman_-1_p0", "location")
report("Camera", "location")
cam = bpy.data.objects["Camera"]
print("VERIFY camera lens fcurves:", [(fc.array_index, len(fc.keyframe_points))
      for fc in cam.data.animation_data.action.fcurves if fc.data_path == "lens"])
print("VERIFY camera focus fcurves:", [(fc.array_index, len(fc.keyframe_points))
      for fc in cam.data.animation_data.action.fcurves if fc.data_path == "dof.focus_distance"])
# expression keys
h = bpy.data.objects["head_caveman_confused"]
fc = h.animation_data.action.fcurves.find("hide_render")
print("VERIFY head_caveman_confused hide keys:", len(fc.keyframe_points) if fc else None)
# scene sanity
sc = bpy.context.scene
print("VERIFY objects:", len(bpy.data.objects), "frame_end:", sc.frame_end,
      "engine:", sc.render.engine)
print("VERIFY DONE")