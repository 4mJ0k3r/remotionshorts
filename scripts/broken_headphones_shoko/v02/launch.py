"""Use the shared exclusive lock around each Blender session in this version."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

here=Path(__file__).resolve().parent
root=here.parents[2]
out=root/"renders/broken_headphones_shoko/v02"
out.mkdir(parents=True,exist_ok=True)
lock=root/".blender_gpu.lock"
owner=uuid4().hex
while True:
    try:
        with lock.open("x",encoding="utf-8") as stream:
            json.dump({"project":"broken_headphones_shoko/v02","owner":owner,"pid":os.getpid()},stream)
        break
    except FileExistsError:
        time.sleep(3)
try:
    for phase in sys.argv[1:]:
        args=[os.getenv("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe"),"-b","--factory-startup","--python-exit-code","1"]
        if phase=="build":
            args+=["--python",str(here/"build.py")]
        elif phase in ("proof","preview"):
            args+=[str(out/"part1_v02.blend"),"--python",str(here/"worker.py"),"--",phase]
        else:
            raise ValueError(phase)
        with (out/f"{phase}.log").open("w",encoding="utf-8") as log:
            subprocess.run(args,cwd=root,stdout=log,stderr=subprocess.STDOUT,check=True)
finally:
    if json.loads(lock.read_text(encoding="utf-8")).get("owner")==owner:
        lock.unlink()
