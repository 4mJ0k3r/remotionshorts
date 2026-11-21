"""Diagnostic: evaluate the saved blend at sheet frames and report transforms."""
import bpy
from mathutils import Vector

OUT = "D:/remotionshorts/renders/poop_city/"
bpy.ops.wm.open_mainfile(filepath=OUT + "poop_city.blend")
sc = bpy.context.scene
cam = sc.camera
dg = bpy.context.evaluated_depsgraph_get()


def world(ob):
    return ob.evaluated_get(dg).matrix_world.translation


for f in (40, 150, 400, 470, 1030, 1250):
    sc.frame_set(f)
    dg.update()
    print(f"--- frame {f} cam {tuple(round(v, 2) for v in world(cam))} "
          f"lens {cam.data.lens:.0f}")
    for name in ("root_sperm", "billboard_sperm", "card_sperm", "sperm_tail",
                 "root_potato", "card_potato", "root_swirl", "card_swirl",
                 "root_buff", "card_buff", "buff_body", "sperm_hardhat",
                 "face_sperm", "sperm_eyes_wide", "sperm_eyes_closed",
                 "sperm_eyes_open", "sperm_mouth_mid", "hud_pill"):
        ob = bpy.data.objects.get(name)
        if not ob:
            print(f"  {name}: MISSING")
            continue
        ev = ob.evaluated_get(dg)
        w = ev.matrix_world.translation
        cs = cam.matrix_world.inverted() @ w
        print(f"  {name}: world=({w.x:.2f},{w.y:.2f},{w.z:.2f}) "
              f"cam=({cs.x:.2f},{cs.y:.2f},{cs.z:.2f}) "
              f"scale=({ev.scale.x:.2f},{ev.scale.y:.2f},{ev.scale.z:.2f}) "
              f"hide={ob.hide_render}")