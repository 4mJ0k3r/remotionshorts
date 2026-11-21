import bpy
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath=r"D:\remotionshorts\renders\poop_city\poop_city.blend")
sc = bpy.context.scene
sc.frame_set(214)
dg = bpy.context.evaluated_depsgraph_get()
for n in ("root_buff", "billboard_buff", "buff_body", "card_buff", "face_buff",
          "root_sperm", "sperm_tail"):
    ob = bpy.data.objects.get(n)
    if not ob:
        print(n, "MISSING")
        continue
    ev = ob.evaluated_get(dg)
    bb = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    zs = [v.z for v in bb]
    ys = [v.y for v in bb]
    print(f"{n}: loc={tuple(round(v,3) for v in ob.matrix_world.translation)} "
          f"scale={tuple(round(v,3) for v in ob.scale)} "
          f"worldz=({min(zs):.3f},{max(zs):.3f}) worldy=({min(ys):.3f},{max(ys):.3f})")