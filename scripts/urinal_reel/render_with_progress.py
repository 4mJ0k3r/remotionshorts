import bpy
import os
import sys

PROGRESS_FILE = "D:/remotionshorts/renders/urinal_dilemma/render_progress.txt"
TOTAL_FRAMES = 855

def on_render_post(scene):
    f = scene.frame_current
    pct = (f / float(TOTAL_FRAMES)) * 100.0
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as fp:
            fp.write(f"{f}:{TOTAL_FRAMES}:{pct:.1f}\n")
    except Exception:
        pass

bpy.app.handlers.render_post.clear()
bpy.app.handlers.render_post.append(on_render_post)

try:
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as fp:
        fp.write(f"0:{TOTAL_FRAMES}:0.0\n")
except Exception:
    pass

print(f"[Blender] Starting animation render (Frames 1 to {TOTAL_FRAMES})...", flush=True)
bpy.ops.render.render(animation=True)
print("[Blender] Animation render completed successfully!", flush=True)
