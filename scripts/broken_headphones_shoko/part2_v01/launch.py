"""Run only the authorized Part 2 jobs under the studio GPU lock."""
import json
import os
import subprocess
import sys
import time
from uuid import uuid4

from timing import HERE, OUT, ROOT

OUT.mkdir(parents=True,exist_ok=True)
lock=ROOT/".blender_gpu.lock"
owner=uuid4().hex
while True:
    try:
        with lock.open("x",encoding="utf-8") as file:
            json.dump({"project":"broken_headphones_shoko/part2_v01","owner":owner,"pid":os.getpid()},file)
        break
    except FileExistsError:
        time.sleep(3)
try:
    for request in sys.argv[1:]:
        phase, _, ranges = request.partition(":")
        args=[os.getenv("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe"),"-b","--factory-startup","--python-exit-code","1"]
        if phase=="build":
            args+=["--python",str(HERE/"part2_scene.py")]
        elif phase in ("benchmark","preview"):
            args+=[str(OUT/"part2_v01.blend"),"--python",str(HERE/"worker.py"),"--",phase]
            if ranges:
                if phase != "preview":
                    raise ValueError("Frame ranges apply only to preview renders")
                args.append(ranges)
        else:
            raise ValueError(phase)
        with (OUT/f"{phase}.log").open("w",encoding="utf-8") as stream:
            subprocess.run(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
finally:
    if json.loads(lock.read_text(encoding="utf-8")).get("owner")==owner:
        lock.unlink()
