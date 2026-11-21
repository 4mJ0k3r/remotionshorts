"""Resumable preview renderer for frames 1..935 at 540x960 (resolution_percentage=50)."""

from pathlib import Path
import time
import bpy

FRAMES_DIR = Path(r"D:\remotionshorts\renders\bamboo_ambush\frames")
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
TOTAL_FRAMES = 935


def main():
    s = bpy.context.scene
    s.frame_start = 1
    s.frame_end = TOTAL_FRAMES
    s.render.fps = 30
    s.render.resolution_x = 1080
    s.render.resolution_y = 1920
    s.render.resolution_percentage = 50
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    s.render.image_settings.color_depth = "8"
    s.eevee.taa_render_samples = 16

    rendered = 0
    skipped = 0
    t0 = time.time()
    for f in range(1, TOTAL_FRAMES + 1):
        out_path = FRAMES_DIR / f"{f:04d}.png"
        if out_path.exists() and out_path.stat().st_size > 1024:
            skipped += 1
            continue
        tmp_path = FRAMES_DIR / f"_tmp_{f:04d}.png"
        s.frame_set(f)
        s.render.filepath = str(tmp_path)
        bpy.ops.render.render(write_still=True)
        tmp_path.replace(out_path)
        rendered += 1
        if rendered == 1 or rendered % 25 == 0 or f == TOTAL_FRAMES:
            elapsed = time.time() - t0
            rate = rendered / max(1e-3, elapsed)
            rem = (TOTAL_FRAMES - f) / max(1e-3, rate)
            print(
                f"[preview] f={f:04d}/{TOTAL_FRAMES} rendered={rendered} skipped={skipped} "
                f"elapsed={elapsed:.1f}s rate={rate:.2f}fps eta={rem:.0f}s",
                flush=True,
            )


if __name__ == "__main__":
    main()
