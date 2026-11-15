"""Check evaluated arm attachments, face visibility, and final camera hold."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/inside_brain_dog'
scene=bpy.context.scene
arms=[scene.objects[name] for name in ['Left anchored curved arm','Right anchored curved arm']]
hands=[scene.objects[name] for name in ['Left matte mitten','Right matte mitten']]
faces=[obj for obj in scene.objects if obj.name.startswith('face_')]
max_error=0
face_errors=[]
positions=[]
for frame in range(1,166):
    scene.frame_set(frame)
    graph=bpy.context.evaluated_depsgraph_get()
    for arm,hand in zip(arms,hands):
        evaluated=arm.evaluated_get(graph)
        mesh=evaluated.to_mesh()
        endpoint=evaluated.matrix_world@((mesh.vertices[48].co+mesh.vertices[49].co)/2)
        max_error=max(max_error,(endpoint-hand.matrix_world.translation).length)
        evaluated.to_mesh_clear()
    active=[obj for obj in faces if not obj.hide_render]
    if len(active)!=1:
        face_errors.append([frame,len(active)])
    if frame>=138:
        positions.append(list(scene.camera.matrix_world.translation))
assert max_error<1e-5,max_error
assert not face_errors,face_errors
assert all(Vector(item)==Vector(positions[0]) for item in positions)
report={'evaluated_frames':165,'max_hand_arm_endpoint_error_m':max_error,'face_visibility_errors':face_errors,'camera_hold':'f138..165 exact','notes':'Geometric checks complement rendered contact sheet and frame sequence review.'}
(OUT/'evaluated_rig_checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
