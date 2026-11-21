"""Run Stage 1 build or native stills under the shared GPU lock."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

here=Path(__file__).resolve().parent
root=here.parents[2]
output=root/"renders/padoda_billionaire/part3_v01"
lock=root/".blender_gpu.lock"
stage=sys.argv[1]
if stage not in ("build","proof","render_final"):
    raise SystemExit("Choose build, proof or render_final.")
if stage=="render_final" and json.loads((output/"benchmark.json").read_text())["status"]!="PASS":
    raise SystemExit("The native benchmark must pass before final rendering.")
owner=uuid4().hex
while True:
    try:
        with lock.open("x",encoding="utf-8") as file:
            json.dump({"project":"padoda_billionaire/part3_v01","owner":owner,"pid":os.getpid()},file)
        break
    except FileExistsError:
        time.sleep(5)
try:
    args=[os.getenv("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe"),"-b","--factory-startup",
          "--python-exit-code","1"]
    if stage!="build":
        args.append(str(output/"padoda_part3_v01.blend"))
    with (output/f"{stage}.log").open("w",encoding="utf-8") as file:
        subprocess.run([*args,"--python",str(here/f"{stage}.py")],cwd=root,check=True,
                       stdout=file,stderr=subprocess.STDOUT)
finally:
    if json.loads(lock.read_text(encoding="utf-8")).get("owner")==owner:
        lock.unlink()
