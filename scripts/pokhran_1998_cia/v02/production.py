"""Serialize Blender work and produce exact native video-only part streams."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=ROOT/"renders/pokhran_1998_cia/v02"
BOUNDS=(0,444,858,1230,1652)


def run(part,phase):
    out=BASE/f"part{part}_v02"
    out.mkdir(parents=True,exist_ok=True)
    count=BOUNDS[part]-BOUNDS[part-1]
    if phase=="encode":
        frames=out/"native_frames"
        for i in range(1,count+1):
            if not (frames/f"frame_{i:04}.png").is_file():
                raise FileNotFoundError(frames/f"frame_{i:04}.png")
        target=BASE/f"pokhran_part{part}_v02_1080p.mp4"
        pending=target.with_stem(target.stem+".pending")
        subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-framerate","30","-start_number","1","-i",
                        str(frames/"frame_%04d.png"),"-frames:v",str(count),"-an","-c:v","libx264",
                        "-threads","5","-preset","fast","-crf","17","-pix_fmt","yuv420p",
                        "-video_track_timescale","15360","-movie_timescale","48000","-movflags","+faststart",
                        str(pending)],check=True)
        stream=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames",
                   "-show_streams","-of","json",str(pending)]))["streams"][0]
        assert (stream["width"],stream["height"],stream["r_frame_rate"],int(stream["nb_read_frames"]))==(1080,1920,"30/1",count)
        subprocess.run(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(pending),"-f","null","-"],check=True)
        pending.replace(target)
        (out/"stream.json").write_text(json.dumps(stream,indent=2))
        return
    if phase=="render" and part>1:
        benchmark=json.loads((out/"benchmark.json").read_text())
        edge=json.loads((out/"edge_density.json").read_text())
        if benchmark["status"]!="PASS" or not edge["pass"]:
            raise RuntimeError(f"Part {part} still has a failed pre-render gate.")
    lock=ROOT/".blender_gpu.lock"
    owner=uuid4().hex
    while True:
        try:
            with lock.open("x",encoding="utf-8") as file:
                json.dump({"project":f"pokhran_1998_cia/v02/part{part}","owner":owner,"pid":os.getpid()},file)
            break
        except FileExistsError:
            time.sleep(3)
    try:
        args=[os.getenv("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe"),
              "-b","--factory-startup","--python-exit-code","1"]
        if phase=="build":
            args += ["--python",str(HERE/"build_continuation.py"),"--",str(part)]
        else:
            source=(BASE.parent/"v02b/pokhran_part1_v02b.blend") if part==1 else out/f"part{part}_v02.blend"
            args += [str(source),"--python",str(HERE/"native_job.py"),"--",str(part),phase,str(out)]
        with (out/f"{phase}.log").open("w",encoding="utf-8") as log:
            subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    finally:
        if json.loads(lock.read_text(encoding="utf-8")).get("owner")==owner:
            lock.unlink()


if __name__=="__main__":
    for phase in sys.argv[2:]:
        run(int(sys.argv[1]),phase)
