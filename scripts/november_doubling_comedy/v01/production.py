"""Serial, resumable native jobs for both authorized reels."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import BOUNDARIES, HERE, ROOT


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(*args,**kwargs):
    return subprocess.run(list(map(str,args)),cwd=ROOT,check=True,**kwargs)


def config(reel,part):
    base=ROOT/"renders"/("november_doubling_comedy" if reel=="november" else "one_year_no_wipe")
    starts=BOUNDARIES if reel=="november" else (0,837,1609,2225,2484)
    version="v02" if part==1 else "v01"
    dest=base/f"part{part}_{version}" if reel=="november" else base/"v6"/f"part{part}"
    return base,dest,starts


def probe(path,length,has_audio):
    info=json.loads(run("ffprobe","-v","error","-count_frames","-show_streams","-of","json",path,capture_output=True).stdout)
    v,*extra=info["streams"]
    assert (v["width"],v["height"],v["sample_aspect_ratio"],v["avg_frame_rate"],
            int(v["nb_read_frames"]),int(v["start_pts"]))==(1080,1920,"1:1","30/1",length,0)
    assert len(extra)==int(has_audio)
    if has_audio:
        a=extra[0]
        assert (a["codec_type"],a["start_pts"],a["duration_ts"])==("audio",0,length*1600)
    run("ffmpeg","-v","error","-nostdin","-xerror","-i",path,"-map",0,"-f","null","-")
    return info


def worker(reel,part,phase,path):
    import bpy
    sys.path.insert(1,str(ROOT/"scripts"))
    import shorts_preflight as gate

    _,out,starts=config(reel,part)
    length=starts[part]-starts[part-1]
    if phase=="build":
        if reel=="wipe":
            from wipe_regrade import build
            build(part,out,path)
        elif part==1:
            from build_scene import build
            build(out,polish=True)
        else:
            from feature import build
            build(part,out,path)
        return
    scene=bpy.context.scene
    r=scene.render
    assert (r.resolution_x,r.resolution_y,r.resolution_percentage,r.fps,scene.frame_end)==(1080,1920,100,30,length)
    assert all(im.packed_file for im in bpy.data.images if im.source=="FILE")
    r.image_settings.file_format="PNG"
    r.image_settings.compression=0
    if not r.film_transparent:
        r.image_settings.color_mode="RGB"
    if phase=="proof":
        dest=out/f"proof_{uuid4().hex[:8]}"
        shots=load(out/"shots.json")
        counts=[]

        def check(frame):
            stats=gate.validate_resources(scene)
            counts.append(stats["visible_triangles"])
            if not stats["pass"] or stats["target_exceeded"]:
                raise RuntimeError(f"Visible resources exceeded at {frame}: {stats}")

        report=gate.benchmark(scene,shots["proof_frames"],dest,update=check)
        report.update(max_visible_triangles=max(counts),proofs_dir=dest.name)
        (out/"benchmark.json").write_text(json.dumps(report,indent=2))
        if report["status"]!="PASS":
            raise RuntimeError("Native benchmark failed")
    else:
        for check in ("benchmark.json","edge.json"):
            if load(out/check)["status"]!="PASS":
                raise RuntimeError(f"Native render requires passing {check}")
        dest=out/"frames"
        dest.mkdir(exist_ok=True)
        r.filepath=str(dest/"frame_")
        r.use_overwrite=False
        scene.frame_set(scene.frame_start)
        bpy.ops.render.render(write_still=False)
        bpy.ops.render.render(animation=True)


def sheet(out,part):
    from PIL import Image, ImageDraw
    bench=load(out/"benchmark.json")
    source=out/bench["proofs_dir"]
    with (out/"edge.json").open("w",encoding="utf-8") as log:
        subprocess.run(["python",str(ROOT/"scripts/ricks_metrics_gate.py"),"--edge-density",str(source)],
                       cwd=ROOT,stdout=log,check=False)
    canvas=Image.new("RGB",(1200,1680),"#171725")
    draw=ImageDraw.Draw(canvas)
    for index,still in enumerate(sorted(source.glob("*.png"))):
        x=index%4*300
        y=index//4*560
        with Image.open(still) as image:
            image.thumbnail((292,515))
            canvas.paste(image.convert("RGB"),(x+(300-image.width)//2,y+6))
        draw.text((x+16,y+533),f"Part {part}   |   {still.stem}",fill="#f0e5df")
    canvas.save(out/f"part{part}_calibration.png",compress_level=4)
    if load(out/"edge.json")["status"]!="PASS":
        raise RuntimeError("Native calibration edge density failed")


def blender(reel,part,out,scene,phase):
    lock=ROOT/".blender_gpu.lock"
    token=uuid4().hex
    while True:
        try:
            with lock.open("x",encoding="utf8") as file:
                json.dump({"project":f"{reel}/{out.name}","pid":os.getpid(),"owner":token},file)
            break
        except FileExistsError:
            time.sleep(3)
    try:
        exe=os.getenv("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe")
        options=[scene] if phase!="build" else []
        with (out/f"{phase}.log").open("w",encoding="utf8") as log:
            run(exe,"-b","--factory-startup","--python-exit-code",1,*options,"--python",__file__,"--",
                reel,part,phase,scene,stdout=log,stderr=subprocess.STDOUT)
    finally:
        if load(lock)["owner"]==token:
            lock.unlink()


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("reel",choices=("november","wipe"))
    cli.add_argument("part",type=int,choices=range(1,5))
    cli.add_argument("phases",nargs="+",choices=("build","proof","render","encode"))
    args=cli.parse_args()
    base,out,starts=config(args.reel,args.part)
    out.mkdir(exist_ok=True,parents=True)
    scene=out/(out.name+("_v6.blend" if args.reel=="wipe" else ".blend"))
    for phase in args.phases:
        if phase!="encode":
            blender(args.reel,args.part,out,scene,phase)
            if phase=="proof":
                sheet(out,args.part)
        else:
            length=starts[args.part]-starts[args.part-1]
            dest=out/f"part{args.part}_1080p.mp4"
            pending=dest.with_suffix(".pending.mp4")
            run("ffmpeg","-v","error","-nostdin","-y","-framerate",30,"-i",out/"frames/frame_%04d.png",
                "-frames:v",length,"-an","-vf","setsar=1","-c:v","libx264","-preset","fast","-crf",16,"-bf",0,
                "-pix_fmt","yuv420p","-video_track_timescale",15360,"-movflags","+faststart",pending)
            report=probe(pending,length,False)
            (out/"decode.json").write_text(json.dumps(report,indent=2))
            pending.replace(dest)
            print(dest,flush=True)


if __name__=="__main__":
    if "--" in sys.argv:
        reel,part,phase,path=sys.argv[sys.argv.index("--")+1:]
        worker(reel,int(part),phase,Path(path))
    else:
        main()
