"""Build and render one preview module while holding the shared GPU lock."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

here = Path(__file__).resolve().parent
root = here.parents[1]
part = int(sys.argv[1])
phases = sys.argv[2:]
if part not in (2, 3, 4) or not phases or set(phases)-{"build", "proof", "render"}:
    raise SystemExit("Usage: launch_continuation.py {2,3,4} [build] [proof] [render]")
source = here / f"part{part}_v01"
output = root / f"renders/pokhran_1998_cia/part{part}_v01"
output.mkdir(parents=True, exist_ok=True)
lock = root / ".blender_gpu.lock"
owner = uuid4().hex
while True:
    try:
        with lock.open("x", encoding="utf-8") as file:
            json.dump({"project": f"pokhran_1998_cia/part{part}_v01", "owner": owner, "pid": os.getpid()}, file)
        break
    except FileExistsError:
        time.sleep(4)
try:
    for phase in phases:
        args = [os.getenv("BLENDER_EXE", "D:/tools/Blender/4.2.23/blender.exe"),
                "-b", "--factory-startup", "--python-exit-code", "1"]
        if phase == "build":
            args += ["--python", str(source / "build.py")]
        else:
            args += [str(output / f"pokhran_part{part}_v01.blend"), "--python",
                     str(here / "continuation_preview.py"), "--", phase]
        with (output / f"{phase}.log").open("w", encoding="utf-8") as log:
            subprocess.run(args, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=True)
finally:
    if json.loads(lock.read_text(encoding="utf-8")).get("owner") == owner:
        lock.unlink()
