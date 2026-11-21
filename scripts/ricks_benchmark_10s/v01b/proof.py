"""Evaluate the saved animation, render Stage 1 frames, and record native measurements."""
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "renders/ricks_benchmark_10s/v01b"
sys.path[:0] = [str(HERE), str(ROOT / "scripts")]
import shorts_preflight as gate
from model import aim

CAL = (15,30,80,122,134,180,250,285)
BENCHMARK = (15,30,54,80,122,129,134,162,180,217,250,285)


def still(scene, path):
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def proofs(scene, output, scale):
    data = scene.camera.data.copy()
    cam = bpy.data.objects.new("Proof camera • unsaved",data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    data.lens = 45
    scene.render.resolution_percentage = scale
    for name,f,loc,target,lens,aperture in (
        ("hero_front",24,(.10,-1.79,1.365),(.13,.47,1.026),42,5.6),
        ("hero_three_quarter",13,(-1.07,-1.64,1.386),(.10,.49,1.06),45,4.8),
        ("broker_hood",250,(33.97,1.62,1.379),(34.13,3.05,1.235),44,3.5),
        ("hero_terror",287,(33.84,3.22,1.245),(33.690,1.936,1.113),44,3.5),
    ):
        scene.frame_set(f)
        cam.location = loc
        aim(cam,target)
        data.lens = lens
        data.dof.aperture_fstop = aperture
        data.dof.focus_distance = (Vector(loc)-Vector(target)).length
        still(scene,output / (name+".png"))


def verify_scene(scene):
    snapshots = {}
    for frame in (1,15,30,80,122,129,130,134,180,217,225,244,250,266,285,300):
        scene.frame_set(frame)
        snapshots[frame] = {
            "resources":gate.validate_resources(scene),
            "camera_position":list(scene.camera.location),
            "expressions":[o.name for o in scene.objects if "local_hide_render" in o and not o.hide_render],
        }
    checks = {f:frame["resources"]["visible_triangles"] for f,frame in snapshots.items()}
    flash = scene.node_tree.nodes["Portal | additive warm-gold flash"]
    portal = {}
    for frame in range(126,135):
        scene.frame_set(frame)
        portal[frame] = flash.inputs[0].default_value
    assert flash.blend_type == "ADD" and portal[133] == portal[134] == 0.0
    assert scene.frame_start == 1 and scene.frame_end == 300
    assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.fps) == (1080,1920,30)
    assert scene.render.engine == "BLENDER_EEVEE_NEXT" and not scene.eevee.use_raytracing
    result = {"max_sampled_evaluated_triangles":max(checks.values()),"frames":snapshots,
              "portal_additive_strength":portal}
    (OUT/"scene_checks.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("SCENE_MAX_TRIANGLES",result["max_sampled_evaluated_triangles"],flush=True)
    if result["max_sampled_evaluated_triangles"]>=150000:
        print("BENCHMARK_TRIANGLE_LIMIT_FAILED",flush=True)


def main():
    scene = bpy.context.scene
    verify_scene(scene)
    stage=sys.argv[-1]
    if stage=="preview":
        output=OUT/"preview"
        output.mkdir(exist_ok=True)
        scene.render.resolution_percentage=43
        for f in CAL:
            scene.frame_set(f)
            still(scene,output / f"frame_{f:04d}.png")
        proofs(scene,output,43)
        return
    target=OUT/"benchmark"
    if target.exists():
        import uuid
        target=OUT/("benchmark_"+uuid.uuid4().hex[:8])
    scene.render.resolution_percentage=100
    # The shared runner retains first-pass measurements and separates warmup.
    report=gate.benchmark(scene,BENCHMARK,target,p95_limit=2.,max_limit=2.)
    scene_checks=json.loads((OUT/"scene_checks.json").read_text())
    report["max_sampled_evaluated_triangles"]=scene_checks["max_sampled_evaluated_triangles"]
    if report["max_sampled_evaluated_triangles"]>=150000:
        report["status"]="FAIL"
    report["native_stills_dir"]=target.name
    master=OUT/"ricks_benchmark_v01b.blend"
    with master.open("rb") as source:
        report["blend_sha256"]=hashlib.file_digest(source,"sha256").hexdigest()
    (OUT/"benchmark.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    output=OUT/"lookdev"
    output.mkdir(exist_ok=True)
    proofs(scene,output,76)


main()
