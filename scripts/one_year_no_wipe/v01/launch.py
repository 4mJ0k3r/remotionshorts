"""Run Stage 1 jobs with exclusive access to the RTX 3050."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/one_year_no_wipe/v01"


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    lock=ROOT/".blender_gpu.lock"
    owner=uuid4().hex
    while True:
        try:
            with lock.open("x",encoding="utf-8") as file:
                json.dump({"project":"one_year_no_wipe/v01","pid":os.getpid(),"owner":owner},file)
            break
        except FileExistsError:
            time.sleep(3)
    try:
        for phase in sys.argv[1:]:
            options=["--python",str(HERE/"build.py")] if phase=="build" else [
                str(OUT/"part1_v01.blend"),"--python",str(HERE/"worker.py"),"--",phase]
            args=[os.getenv("BLENDER_EXE",r"D:\tools\Blender\4.2.23\blender.exe"),"-b","--factory-startup",
                  "--python-exit-code","1",*options]
            with (OUT/f"{phase}.log").open("w",encoding="utf-8") as log:
                subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    finally:
        if json.loads(lock.read_text(encoding="utf-8")).get("owner")==owner:
            lock.unlink()


if __name__=="__main__":
    main()
