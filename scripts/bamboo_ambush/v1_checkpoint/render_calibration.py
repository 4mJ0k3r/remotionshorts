"""Render the 12 calibration peak frames at 540x960 (resolution_percentage=50)."""

from pathlib import Path
import time
import bpy

CAL_DIR = Path(r"D:\remotionshorts\renders\bamboo_ambush\calibration")
CAL_DIR.mkdir(parents=True, exist_ok=True)
FRAMES = [45, 140, 240, 345, 430, 495, 560, 660, 735, 800, 860, 910]


def main():
    s = bpy.context.scene
    s.render.resolution_x = 1080
    s.render.resolution_y = 1920
    s.render.resolution_percentage = 50
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    s.render.image_settings.color_depth = "8"
    s.eevee.taa_render_samples = 16

    t0 = time.time()
    for i, f in enumerate(FRAMES, 1):
        out_path = CAL_DIR / f"{f:04d}.png"
        tmp_path = CAL_DIR / f"_tmp_{f:04d}.png"
        s.frame_set(f)
        s.render.filepath = str(tmp_path)
        bpy.ops.render.render(write_still=True)
        tmp_path.replace(out_path)
        print(f"[cal {i}/{len(FRAMES)}] frame={f:04d} -> {out_path.name} ({time.time() - t0:.1f}s)", flush=True)


if __name__ == "__main__":
    main()
