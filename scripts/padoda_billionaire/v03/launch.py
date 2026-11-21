"""Run the Blender build, stills or motion preview under the exclusive GPU lock."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

here=Path(__file__).resolve().parent
root=here.parents[2]
out=root/"renders/padoda_billionaire/v03"
lock=root/".blender_gpu.lock"
stage=sys.argv[1]
if stage not in {"build","motion","proof","coin"}:
    raise SystemExit("Choose build, proof, motion or coin.")
if stage in {"motion","coin"} and json.loads((out/"benchmark.json").read_text())["status"]!="PASS":
    raise SystemExit("The native benchmark must pass before the motion preview.")
owner=uuid.uuid4().hex
while True:
    try:
        with lock.open("x",encoding="utf-8") as f:
            json.dump({"project":"padoda_billionaire/v03","owner":owner,"pid":os.getpid()},f)
        break
    except FileExistsError:
        time.sleep(8)
try:
    args=[os.getenv("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe"),
          "-b","--factory-startup","--python-exit-code","1"]
    if stage=="build":
        args+=["--python",str(here/"build.py")]
    else:
        args += [str(out/"padoda_hook_v03.blend"),"--python",str(here/"proof.py"),"--",stage]
    with (out/f"{stage}.log").open("w",encoding="utf-8") as log:
        subprocess.run(args,check=True,cwd=root,stdout=log,stderr=subprocess.STDOUT)
finally:
    if json.loads(lock.read_text(encoding="utf-8")).get("owner")==owner:
        lock.unlink()

