"""Join frame-locked native modules and check the whole master."""
import argparse
import json
import re
import subprocess

from delivery import audio
from production import config, load, probe, run
from timing import HERE, ROOT


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def metadata(reel, starts, folders, out):
    cuts=[]
    for offset,folder in zip(starts,folders):
        cuts.extend(offset+i for i in load(folder/"shots.json")["cuts"])
    cuts=sorted({*cuts,*starts[1:-1]})
    spans=[0,*cuts,starts[-1]]
    write(out/"shots.json",{"cuts":cuts,"shots":[{"id":i,"a":a,"b":b}
          for i,(a,b) in enumerate(zip(spans,spans[1:]),1)]})
    if reel=="november":
        plan=load(HERE/"master_plan.json")
        for part in plan["parts"]:
            part["status"]="rendered"
        for event in plan["visual_events"]:
            event["status"]="rendered"
    else:
        base=folders[0].parents[1]
        plan=load(base/"final/master_plan.json")
    plan["final_picture_seconds"]=starts[-1]/30
    write(out/"master_plan.json",plan)


def measure(script,out,*args):
    with out.open("w",encoding="utf8") as log:
        command=["python",str(ROOT/"scripts"/script),*map(str,args)]
        result=subprocess.run(command,cwd=ROOT,stdout=log)
    if result.returncode not in (0,1,2):
        raise RuntimeError(f"Couldn't run {script}")


def assemble(reel):
    base,_,starts=config(reel,1)
    out=base/"final" if reel=="november" else base/"v6"
    out.mkdir(exist_ok=True,parents=True)
    product="november_doubling_FINAL_1080p.mp4" if reel=="november" else "one_year_no_wipe_V6_FINAL_1080p.mp4"
    folders=[config(reel,part)[1] for part in range(1,5)]
    manifest=out/"parts.ffconcat"
    videos=[folder/f"part{i}_1080p.mp4" for i,folder in enumerate(folders,1)]
    for video in videos:
        if not video.is_file():
            raise FileNotFoundError(video)
    manifest.write_text("ffconcat version 1.0\n"+"".join(f"file '{p.as_posix()}'\n" for p in videos),
                        encoding="utf8")
    wav=audio(out/"master_audio.wav") if reel=="november" else base/"final/master_audio.wav"
    audio_info=json.loads(run("ffprobe","-v","error","-show_entries","stream=sample_rate,duration_ts",
                              "-of","json",wav,capture_output=True).stdout)["streams"][0]
    assert (audio_info["sample_rate"],audio_info["duration_ts"])==("48000",starts[-1]*1600)
    final=out/product
    pending=final.with_suffix(".pending.mp4")
    run("ffmpeg","-v","error","-nostdin","-y","-f","concat","-safe",0,"-i",manifest,"-i",wav,
        "-map","0:v:0","-map","1:a:0","-c:v","copy","-bsf:v","setts=pts=N*512:dts=N*512:duration=512",
        "-c:a","aac","-b:a","256k","-video_track_timescale",15360,"-movie_timescale",48000,
        "-movflags","+faststart",pending)
    n=starts[-1]
    decoded=probe(pending,n,True)
    raw=run("ffprobe","-v","error","-select_streams","v:0","-show_packets",
            "-show_entries","packet=pts,duration","-of","json",pending,capture_output=True).stdout
    packets=json.loads(raw)["packets"]
    assert len(packets)==n and all((p["pts"],p["duration"])==(i*512,512) for i,p in enumerate(packets))
    pending.replace(final)
    write(out/"decode.json",decoded)
    metadata(reel,starts,folders,out)
    print(final,flush=True)
    return out,final,folders,starts


def qa(out,final,folders,starts):
    measure("short_qa.py",out/"short_qa_stdout.txt",final,out/"qa",out/"shots.json","--strict")
    measure("ricks_metrics_gate.py",out/"word_sync.json","--word-sync",out/"master_plan.json")
    edge=out/"edge_samples"
    edge.mkdir(exist_ok=True)
    run("ffmpeg","-v","error","-nostdin","-y","-i",final,
        "-vf","select='not(mod(n,4))',scale=360:640:flags=lanczos","-fps_mode","vfr",
        "-compression_level",2,edge/"frame_%04d.png")
    measure("ricks_metrics_gate.py",out/"edge.json","--edge-density",edge)
    measure("ricks_metrics_gate.py",out/"camera.json","--cam-velocity",final,out/"shots.json")
    parts=[]
    for folder in folders:
        bench=load(folder/"benchmark.json")
        part={key:bench[key] for key in
              ("status","max_seconds","p95_seconds","sampled_board_peak_gib","max_visible_triangles")}
        log=(folder/"render.log").read_text(encoding="utf8",errors="replace")
        native=[60*int(m)+float(s) for m,s in re.findall(r"Time: (\d+):(\d+\.\d+) \(Saving:",log)]
        part.update(native_logged_frames=len(native),native_frame_max_seconds=max(native,default=None))
        parts.append(part)
    report={"frame_count":starts[-1],"part_boundaries_frames":starts,"decode":"PASS","parts":parts}
    keys = {
        "word_sync.json":("status","matched","annotated_nouns_and_actions","coverage"),
        "edge.json":("status","mean","min","frame_count","below_minimum_frames"),
        "camera.json":("status","eligible_pairs","measured_pairs","max_smooth_px_per_frame","hop_destination_frames"),
        "qa/report.json":("status","black","white","frozen"),
    }
    for file,columns in keys.items():
        data=load(out/file)
        report[file]={column:data.get(column) for column in columns}
    report["loudness"]=next(line for line in (out/"qa/report.md").read_text(encoding="utf8").splitlines()
                            if line.startswith("LOUDNESS "))
    write(out/"qa_summary.json",report)


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("reel",choices=("november","wipe"))
    args=cli.parse_args()
    qa(*assemble(args.reel))
