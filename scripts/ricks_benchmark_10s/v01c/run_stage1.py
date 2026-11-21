"""Run only Stage 1 with exclusive Blender GPU ownership."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "renders/ricks_benchmark_10s/v01c"
LOCK = ROOT / ".blender_gpu.lock"
SOURCE = OUT / "ricks_benchmark_v01c.blend"
BLENDER = os.getenv("BLENDER_EXE") or shutil.which("blender") or "D:/tools/Blender/4.2.23/blender.exe"


def invoke(args, log_name):
    with (OUT / log_name).open("w", encoding="utf-8") as log:
        subprocess.run([BLENDER, "-b", "--factory-startup", "--python-exit-code", "1", *map(str,args)],
                       cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)


def main():
    stage = sys.argv[1]
    if stage not in {"build", "gate"}:
        raise SystemExit("Choose build or gate.")
    owner = uuid.uuid4().hex
    with LOCK.open("x", encoding="utf-8") as lock:
        json.dump({"project":"ricks_benchmark_10s/v01c","owner":owner,"pid":os.getpid()},lock)
    try:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        os.environ.update(PYTHONDONTWRITEBYTECODE=env["PYTHONDONTWRITEBYTECODE"])
        if stage == "build":
            subprocess.run([sys.executable,str(HERE / "artwork.py")],check=True)
            invoke(["--python",HERE / "build.py"],"build.log")
        else:
            invoke([SOURCE,"--python",HERE / "motion_gate.py"],stage+".log")
    finally:
        if json.loads(LOCK.read_text(encoding="utf-8")).get("owner")==owner:
            LOCK.unlink()


if __name__ == "__main__":
    main()
