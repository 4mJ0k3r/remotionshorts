"""Render stages for the isolated v01 project. Run from the repository root."""
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/"renders/pigeon_inspector/v01"
BLEND = OUT/"pigeon_inspector_v01.blend"
BLENDER = r"D:\tools\Blender\4.2.23\blender.exe"
BENCH = (1,33,48,97,126,147,157,160,171,218,239,291)


def worker(stage, args):
    import bpy
    sys.path[:0] = [str(Path(__file__).parent),str(ROOT/"scripts")]

    if stage == "build":
        from scene import bake
        bake(OUT)
        if args:
            bpy.ops.wm.open_mainfile(filepath=str(BLEND))
            worker("stills",["verified_contacts","1","45","61","70","147","160","168","201","239","291"])
            worker("bench",[args[0]])
            worker("motion",["landing_proof","61","92"])
        return
    scene = bpy.context.scene
    if stage == "bench":
        import shorts_preflight as gate
        path = OUT/args[0]
        def validate(frame):
            result = gate.validate_resources(scene)
            if not result["pass"] or result["target_exceeded"]:
                raise RuntimeError(f"Resource gate at frame {frame}: {result}")
        result = gate.benchmark(scene,BENCH,path,update=validate,resolution=(540,960,100))
        print("BENCHMARK",json.dumps(result),flush=True)
        if len(args) > 1:
            worker("stills",["contacts_b","45","50","142","153","163","180","201","211","249","269","281","299"])
            worker("motion",[args[1],"61","156"])
        return
    folder = OUT/args[0]
    folder.mkdir(parents=True,exist_ok=True)
    scene.render.filepath = str(folder/"frame_")
    if stage == "stills":
        for frame in map(int,args[1:]):
            scene.frame_set(frame)
            scene.render.filepath = str(folder/f"frame_{frame:04d}.png")
            bpy.ops.render.render(write_still=True)
        return
    first,last = map(int,args[1:]) if len(args)>1 else (1,300)
    if stage == "motion":
        scene.render.resolution_percentage = 67
    scene.frame_start,scene.frame_end = first,last
    bpy.ops.render.render(animation=True)


def main():
    stage,*args = sys.argv[1:]
    if stage not in {"build","bench","stills","motion","render"}:
        raise SystemExit("Use build, bench, stills, motion or render.")
    if stage == "build":
        OUT.mkdir(parents=True,exist_ok=True)
    elif not BLEND.is_file():
        raise SystemExit("Build the v01 scene before opening it for proof or render.")
    if stage == "render":
        report = json.loads((OUT/args[1]/"benchmark.json").read_text(encoding="utf-8"))
        if report["status"] != "PASS" or report["telemetry_errors"]:
            raise SystemExit("Full preview requires a passing native benchmark.")
        args = args[:1]
        if (OUT/args[0]/"frame_0001.png").exists():
            raise SystemExit("The first full preview already has a render directory.")
    lock,owner = ROOT/".blender_gpu.lock",uuid4().hex
    try:
        with lock.open("x",encoding="utf-8") as handle:
            json.dump({"project":"pigeon_inspector/v01","pid":os.getpid(),"owner":owner},handle)
    except FileExistsError:
        raise SystemExit("GPU busy. Wait for the owner of .blender_gpu.lock.")
    try:
        cmd = [os.environ.get("BLENDER_EXE",BLENDER),"-b","--factory-startup"]
        if stage != "build":
            cmd.append(str(BLEND))
        with (OUT/(stage+".log")).open("w",encoding="utf-8") as log:
            subprocess.run([*cmd,"--python-exit-code","1","--python",str(Path(__file__).resolve()),
                            "--",stage,*args],check=True,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("owner") == owner:
            lock.unlink()


if __name__ == "__main__":
    if "--" in sys.argv:
        stage,*args = sys.argv[sys.argv.index("--")+1:]
        worker(stage,args)
    else:
        main()
