"""Six native GPU samples, then the approved 540p preview."""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import BENCH, LENGTH, OUT, ROOT

sys.path.insert(0,str(ROOT/"scripts"))
from shorts_preflight import validate_resources

s=bpy.context.scene
r=s.render
assert (r.resolution_x,r.resolution_y,r.resolution_percentage,r.fps,r.fps_base,s.frame_end)==(1080,1920,100,30,1,LENGTH)
assert all(img.packed_file for img in bpy.data.images if img.source=="FILE")


def benchmark():
    output=OUT/"benchmark_stills"
    output.mkdir(exist_ok=True)
    readings=[]
    errors=[]
    stop=threading.Event()

    def sample_board():
        while not stop.is_set():
            try:
                raw=subprocess.check_output(["nvidia-smi","--query-gpu=memory.used","--format=csv,noheader,nounits"],
                                            text=True,timeout=3,creationflags=subprocess.CREATE_NO_WINDOW)
                readings.append(max(float(s) for s in raw.splitlines())/1024)
            except (ValueError,OSError,subprocess.SubprocessError) as exc:
                errors.append(str(exc))
                return
            stop.wait(.21)

    sample=threading.Thread(target=sample_board,daemon=True)
    checks=[]
    sample.start()
    try:
        s.frame_set(BENCH[0])
        bpy.ops.render.render(write_still=False)
        for f in BENCH:
            s.frame_set(f)
            resources=validate_resources(s)
            r.filepath=str(output/f"frame_{f:04}.png")
            start=time.perf_counter()
            bpy.ops.render.render(write_still=True)
            checks.append({"frame":f,"seconds":time.perf_counter()-start,**resources})
    finally:
        stop.set()
        sample.join(timeout=4)
    peak=max(readings,default=None)
    maximum=max(item["seconds"] for item in checks)
    triangles=max(item["visible_triangles"] for item in checks)
    passed=maximum<=2.0 and peak is not None and peak<=3.3 and triangles<150000 and all(item["pass"] for item in checks)
    report={"status":"PASS" if passed else "FAIL","frames":checks,"max_seconds":maximum,
        "sampled_board_peak_gib":peak,"max_evaluated_triangles":triangles,"telemetry_errors":errors}
    (OUT/"benchmark.json").write_text(json.dumps(report,indent=2))
    print(report["status"],f"{maximum:.3f}s/frame",peak,triangles,flush=True)
    if not passed:
        raise RuntimeError("The six-frame benchmark did not pass.")


phase,*options=sys.argv[sys.argv.index("--")+1:]
if phase=="benchmark":
    benchmark()
elif phase=="preview":
    if json.loads((OUT/"benchmark.json").read_text())["status"]!="PASS":
        raise RuntimeError("The six-frame benchmark must pass before the preview.")
    target=OUT/"preview_540p_frames"
    target.mkdir(exist_ok=True)
    r.resolution_percentage=50
    r.filepath=str(target/"frame_")
    r.use_overwrite=True
    if options:
        ranges=[tuple(map(int,span.split("-"))) for span in options[0].split(",")]
        if any(not 1<=start<=end<=LENGTH for start,end in ranges):
            raise ValueError("Preview range is outside the Part 2 timeline")
    else:
        ranges=[(1,LENGTH)]
    for start,end in ranges:
        s.frame_start,s.frame_end=start,end
        bpy.ops.render.render(animation=True)
