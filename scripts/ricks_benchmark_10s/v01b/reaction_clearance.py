"""Clear the shelf during the opening reaction without changing the approved master."""
from pathlib import Path

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parents[3] / "renders/ricks_benchmark_10s/v01b"
FRAMES = OUT / "reaction_clearance_540p"

scene = bpy.context.scene
camera = scene.camera
scene.render.resolution_percentage = 50
scene.render.image_settings.file_format = "PNG"


def ease(t):
    return t**3*(t*(6*t-15)+10)


positions = {}
for frame in range(265, 285):
    scene.frame_set(frame)
    positions[frame] = camera.location.copy()

# Rendering updates the dependency graph, so detach the baked channels in
# this transient session before substituting the corrected camera samples.
camera.animation_data_clear()
camera.data.animation_data_clear()

for frame, original in positions.items():
    scene.frame_set(frame)
    # Leave a smooth entrance to the original path before the approved f285.
    cap, feather = 3.33, .07
    influence = max(0., feather-abs(original.y-cap))
    camera.location = original
    camera.location.y = min(original.y,cap)-influence**2/(4*feather)
    reaction = min(1.,max(0.,(frame-266)/4))
    settle = min(1.,max(0.,(frame-270)/4))
    amount = 1.08*ease(reaction)-.08*ease(settle)
    target = Vector((33.687,2.04+(1.935-2.04)*amount,1.22-.136*amount))
    focus = target+Vector((.01,.09,.045))
    forward = (target-camera.location).normalized()
    camera.rotation_quaternion = forward.to_track_quat("-Z","Y")
    camera.data.dof.focus_distance = (focus-camera.location).dot(forward)
    bpy.context.view_layer.update()
    scene.render.filepath = str(FRAMES / f"frame_{frame:04d}.png")
    bpy.ops.render.render(write_still=True)
