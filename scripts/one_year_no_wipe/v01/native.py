"""Versioned 1080p jobs and verification under the shared GPU lock."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RENDERS=ROOT/"renders/one_year_no_wipe"
ENDS=(0,837,1609,2225,2484)
NAMES=("part1_v02","part2_v01","part3_v01","part4_v01")


def run(*args,**kwargs):
    return subprocess.run(list(map(str,args)),cwd=ROOT,check=True,**kwargs)


def probe(video,length,audio=False):
    info=json.loads(run("ffprobe","-v","error","-count_frames","-show_streams","-of","json",video,capture_output=True).stdout)
    stream,*others=info["streams"]
    assert (stream["width"],stream["height"],stream["sample_aspect_ratio"],stream["avg_frame_rate"],
            int(stream["nb_read_frames"]),stream["start_pts"])==(1080,1920,"1:1","30/1",length,0)
    assert len(others)==int(audio)
    if audio:
        assert others[0]["codec_type"]=="audio" and others[0]["start_pts"]==0 and others[0]["duration_ts"]==length*1600
    run("ffmpeg","-v","error","-nostdin","-xerror","-i",video,"-map",0,"-f","null","-")
    return info


def worker(number,phase,span=None):
    import bpy
    import shorts_preflight as gate

    output=RENDERS/NAMES[number-1]
    if phase=="build":
        if number==1:
            from build import build
            build(output,polish=True)
        else:
            from later import build
            build(number,output)
        return
    s=bpy.context.scene
    r=s.render
    length=ENDS[number]-ENDS[number-1]
    assert (r.resolution_x,r.resolution_y,r.resolution_percentage,r.fps,s.frame_end)==(1080,1920,100,30,length)
    assert all(image.packed_file for image in bpy.data.images if image.source=="FILE")
    r.image_settings.file_format="PNG"
    r.image_settings.compression=0
    if phase=="proof":
        path=output/f"proof_{uuid4().hex[:8]}"
        shots=json.loads((output/"shots.json").read_text())
        triangles=[]

        def resource(frame):
            stats=gate.validate_resources(s)
            triangles.append(stats["visible_triangles"])
            if not stats["pass"] or stats["target_exceeded"]:
                raise RuntimeError(f"Resource audit failed at {frame}: {stats}")

        report=gate.benchmark(s,shots["proof_frames"],path,update=resource)
        report.update(proofs_dir=path.name,max_visible_triangles=max(triangles))
        (output/"benchmark.json").write_text(json.dumps(report,indent=2))
        if report["status"]!="PASS":
            raise RuntimeError("GPU benchmark failed")
    else:
        if any(json.loads((output/name).read_text())["status"]!="PASS" for name in ("benchmark.json","edge.json")):
            raise RuntimeError("Native render requires passing proof reports")
        frames=output/"frames"
        frames.mkdir(exist_ok=True)
        r.filepath=str(frames/"frame_")
        ranges=[tuple(map(int,item.split(":"))) for item in span.split(",")] if span else [(1,length)]
        if any(not 1<=a<=b<=length for a,b in ranges):
            raise ValueError("Render span is outside the saved timeline")
        r.use_overwrite=bool(span)
        for a,b in ranges:
            s.frame_start,s.frame_end=a,b
            bpy.ops.render.render(animation=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("part",type=int,choices=range(1,5))
    parser.add_argument("phases",nargs="+",choices=("build","proof","render","encode"))
    parser.add_argument("--span")
    args=parser.parse_args()
    part=args.part
    output=RENDERS/NAMES[part-1]
    output.mkdir(parents=True,exist_ok=True)
    blend=output/(NAMES[part-1]+".blend")
    length=ENDS[part]-ENDS[part-1]
    lock=ROOT/".blender_gpu.lock"
    for phase in args.phases:
        if phase=="encode":
            video=output/f"part{part}_1080p.mp4"
            pending=video.with_suffix(".pending.mp4")
            run("ffmpeg","-v","error","-nostdin","-y","-framerate",30,"-i",output/"frames/frame_%04d.png",
                "-frames:v",length,"-an","-vf","setsar=1","-c:v","libx264","-preset","fast","-crf",16,
                "-bf",0,"-pix_fmt","yuv420p","-video_track_timescale",15360,"-movflags","+faststart",pending)
            report=probe(pending,length)
            pending.replace(video)
            (output/"decode.json").write_text(json.dumps(report,indent=2))
            continue
        owner=uuid4().hex
        while True:
            try:
                with lock.open("x",encoding="utf-8") as log:
                    json.dump({"project":"one_year_no_wipe/"+output.name,"pid":os.getpid(),"owner":owner},log)
                break
            except FileExistsError:
                time.sleep(3)
        try:
            command=[os.getenv("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe"),"-b","--factory-startup","--python-exit-code",1]
            if phase!="build":
                command.append(blend)
            with (output/f"{phase}.log").open("w",encoding="utf-8") as log:
                extra=[args.span] if args.span and phase=="render" else []
                run(*command,"--python",__file__,"--",part,phase,*extra,stdout=log,stderr=subprocess.STDOUT)
        finally:
            if json.loads(lock.read_text(encoding="utf-8"))["owner"]==owner:
                lock.unlink()
        if phase=="proof":
            report=json.loads((output/"benchmark.json").read_text())
            with (output/"edge.json").open("w",encoding="utf-8") as log:
                run("python",ROOT/"scripts/ricks_metrics_gate.py","--edge-density",output/report["proofs_dir"],stdout=log)


if __name__=="__main__":
    if "--" in sys.argv:
        sys.path[:0]=[str(HERE),str(ROOT/"scripts")]
        number,phase,*options=sys.argv[sys.argv.index("--")+1:]
        worker(int(number),phase,*options)
    else:
        main()
