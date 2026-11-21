"""Stage 1 build, native 12-frame gate and 540p render under the studio lock."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import HERE, LENGTH, OUT, ROOT


def worker(phase, bounds=None):
    import bpy

    sys.path.insert(0,str(ROOT/"scripts"))
    import shorts_preflight as gate

    scene=bpy.context.scene
    render=scene.render
    assert (render.resolution_x,render.resolution_y,render.resolution_percentage,
            render.fps,scene.frame_end)==(1080,1920,100,30,LENGTH)
    assert not scene.eevee.use_raytracing
    assert all(image.packed_file for image in bpy.data.images if image.source=="FILE")
    render.image_settings.file_format="PNG"
    render.image_settings.compression=0
    if phase=="proof":
        shots=json.loads((OUT/"shots.json").read_text())
        path=OUT/f"proof_{uuid4().hex[:8]}"
        triangles=[]

        def check(frame):
            v=gate.validate_resources(scene)
            if not v["pass"] or v["target_exceeded"]:
                raise RuntimeError(f"Resource check failed at frame {frame}: {v}")
            triangles.append(v["visible_triangles"])

        report=gate.benchmark(scene,shots["proof_frames"],path,update=check)
        report.update(proofs_dir=path.name,max_visible_triangles=max(triangles))
        (OUT/"benchmark.json").write_text(json.dumps(report,indent=2))
        if report["status"]!="PASS":
            raise RuntimeError("Native RTX benchmark failed")
    elif phase=="preview":
        for gate_file in ("benchmark.json","proof_edge.json"):
            if json.loads((OUT/gate_file).read_text(encoding="utf-8-sig"))["status"]!="PASS":
                raise RuntimeError(f"Preview requires a passing {gate_file}")
        frames=OUT/"preview_frames"
        frames.mkdir(exist_ok=True)
        render.resolution_percentage=50
        render.filepath=str(frames/"frame_")
        render.use_overwrite=True
        if bounds:
            scene.frame_start,scene.frame_end=map(int,bounds.split(":"))
        bpy.ops.render.render(animation=True)


def run(phases):
    OUT.mkdir(exist_ok=True,parents=True)
    lock=ROOT/".blender_gpu.lock"
    owner=uuid4().hex
    while True:
        try:
            with lock.open("x",encoding="utf-8") as out:
                json.dump({"project":"november_doubling_comedy/v01","pid":os.getpid(),"owner":owner},out)
            break
        except FileExistsError:
            time.sleep(3)
    try:
        for item in phases:
            phase,_,bounds=item.partition("=")
            blender=os.getenv("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe")
            args=[blender,"-b","--factory-startup","--python-exit-code","1"]
            if phase=="build":
                args+=["--python",str(HERE/"build_scene.py")]
            else:
                args+=[str(OUT/"part1_v01.blend"),"--python",str(HERE/"render.py"),"--",phase]
                if bounds:
                    args.append(bounds)
            with (OUT/f"{phase}.log").open("w",encoding="utf-8") as out:
                subprocess.run(args,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,check=True)
    finally:
        if json.loads(lock.read_text(encoding="utf-8"))["owner"]==owner:
            lock.unlink()


if __name__=="__main__":
    if "--" in sys.argv:
        worker(*sys.argv[sys.argv.index("--")+1:])
    else:
        run(sys.argv[1:])
