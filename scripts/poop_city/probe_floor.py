import bpy
from pathlib import Path

OUT = Path(r"D:\remotionshorts\renders\poop_city")
bpy.ops.wm.open_mainfile(filepath=str(OUT / "poop_city_v4.blend"))
sc = bpy.context.scene
sc.render.resolution_x = 540
sc.render.resolution_y = 960
sc.eevee.taa_render_samples = 16
nt = sc.node_tree
for n in nt.nodes:
    if n.type == "ELLIPSEMASK":
        n.width = 540
        n.height = 960
hs = nt.nodes["grade_sat"]
expo = next(n for n in nt.nodes if n.type == "EXPOSURE")
filt = next(n for n in nt.nodes if n.type == "FILTER")
mul = next(n for n in nt.nodes if n.type == "MIX_RGB" and n.blend_type == "MULTIPLY")
sc.frame_set(216)


def shot(tag):
    sc.render.filepath = str(OUT / f"probe_floor_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print(f"PROBE saved {tag}", flush=True)


sat = hs.inputs["Sat"] if "Sat" in hs.inputs else hs.inputs[2]
print("PROBE sat value f216:", sat.default_value, "expo:", expo.inputs["Exposure"].default_value,
      "filt:", filt.filter_type, filt.inputs["Fac"].default_value, flush=True)
hs.mute = True
shot("nohs")
hs.mute = False
expo.inputs["Exposure"].default_value = 0.0
shot("noexpo")
expo.inputs["Exposure"].default_value = 0.30
filt.mute = True
shot("nofilt")
filt.mute = False
mul.mute = True
shot("nomul")