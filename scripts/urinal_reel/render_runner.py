import os
import bpy

LOG_PATH = "D:/remotionshorts/renders/urinal_dilemma/render_progress.txt"

# 1. Register sprite and HUD swap handler
txt = bpy.data.texts.get("rc_sprite_swap_register.py")
if txt:
    exec(txt.as_string())
    print("[Render Runner] Successfully registered rc_sprite_swap_register.py handler.")

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 855

# Ensure output path
scene.render.filepath = "D:/remotionshorts/renders/urinal_dilemma/preview_raw.mp4"

def on_frame_render_post(scene):
    f = scene.frame_current
    with open(LOG_PATH, "w", encoding="utf-8") as fp:
        pct = (f / scene.frame_end) * 100.0
        fp.write(f"Frame {f} / {scene.frame_end} ({pct:.1f}%)\n")

bpy.app.handlers.render_post.append(on_frame_render_post)

with open(LOG_PATH, "w", encoding="utf-8") as fp:
    fp.write(f"Starting render: 1 to {scene.frame_end}...\n")

bpy.ops.render.render(animation=True)

with open(LOG_PATH, "w", encoding="utf-8") as fp:
    fp.write("DONE\n")

print("[Render Runner] Animation render completed successfully!")
