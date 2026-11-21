"""Assemble the four exact 30 fps streams and audit the delivery."""
import argparse
import json
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw

from deliver import mix
from native import ENDS, HERE, NAMES, RENDERS, ROOT, probe, run

OUT=RENDERS/"final"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sheet():
    OUT.mkdir(exist_ok=True)
    full=Image.new("RGB",(1500,1650),"#171522")
    d=ImageDraw.Draw(full)
    for j,version in enumerate(NAMES[1:]):
        folder=RENDERS/version
        stats=load(folder/"benchmark.json")
        files=sorted((folder/stats["proofs_dir"]).glob("frame_*.png"))
        for i,ref in enumerate(files):
            x=125*i
            y=j*550+36
            with Image.open(ref) as still:
                # Full view on the top row of the strip and a larger excerpt below.
                still.thumbnail((119,214))
                full.paste(still.convert("RGB"),(x+(125-still.width)//2,y))
            d.text((x+10,y+219),ref.stem,fill="#f3eadb")
        d.text((12,j*550+14),f"PART {j+2}  /  12 native delivery-camera checkpoints",fill="#fff1d5")
        for i,k in enumerate((0,2,4,6,8,11)):
            with Image.open(files[k]) as still:
                still.thumbnail((242,288))
                full.paste(still.convert("RGB"),(i*250+(250-still.width)//2,j*550+255))
    full.save(OUT/"parts234_calibration.png")


def shot_manifest():
    cuts=[]
    spans=[]
    for i,version in enumerate(NAMES):
        data=load(RENDERS/version/"shots.json")
        cuts += [ENDS[i]+x for x in data["cuts"]]
        if i:
            cuts.append(ENDS[i])
        for shot in data["shots"]:
            spans.append({"id":len(spans)+1,"a":ENDS[i]+shot["a"],"b":ENDS[i]+shot["b"]})
    out=OUT/"shots.json"
    out.write_text(json.dumps({"cuts":sorted(cuts),"shots":spans},indent=2))
    return out


def metrics(script,output,*args):
    with (OUT/output).open("w",encoding="utf-8") as log:
        proc=subprocess.run(["python",str(ROOT/"scripts"/script),*map(str,args)],cwd=ROOT,stdout=log)
    if proc.returncode not in (0,1,2):
        raise RuntimeError(f"Could not finish the {script} audit")


def merge():
    OUT.mkdir(exist_ok=True)
    wav=OUT/"master_audio.wav"
    if not wav.is_file():
        mix(full=True)
    files=OUT/"parts.ffconcat"
    files.write_text("ffconcat version 1.0\n"+"".join(f"file '../{v}/part{i}_1080p.mp4'\n"
                     for i,v in enumerate(NAMES,1)),encoding="utf-8")
    output=OUT/"one_year_no_wipe_FINAL_1080p.mp4"
    pending=output.with_suffix(".pending.mp4")
    run("ffmpeg","-v","error","-nostdin","-y","-f","concat","-safe",0,"-i",files,"-i",wav,
        "-map","0:v","-map","1:a","-c:v","copy","-bsf:v","setts=pts=N*512:dts=N*512:duration=512",
        "-c:a","aac","-b:a","256k","-video_track_timescale",15360,"-movie_timescale",48000,
        "-movflags","+faststart",pending)
    check=probe(pending,ENDS[-1],audio=True)
    packets=json.loads(run("ffprobe","-v","error","-select_streams","v:0","-show_packets",
                           "-show_entries","packet=pts,duration","-of","json",pending,capture_output=True).stdout)
    assert [(p["pts"],p["duration"]) for p in packets["packets"]]==[(512*i,512) for i in range(ENDS[-1])]
    pending.replace(output)
    (OUT/"decode.json").write_text(json.dumps(check,indent=2))
    manifest=shot_manifest()
    plan=load(HERE/"master_plan.json")
    plan["part_boundaries_frames"]=ENDS
    plan["scenes"][-1]["end"]=82.8
    plan["final_picture_seconds"]=82.8
    (OUT/"master_plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
    metrics("short_qa.py","short_qa_stdout.txt",output,OUT/"qa",manifest,"--strict")
    metrics("ricks_metrics_gate.py","word_sync.json","--word-sync",OUT/"master_plan.json")
    scan=OUT/"edge_samples"
    scan.mkdir(exist_ok=True)
    run("ffmpeg","-v","error","-y","-i",output,"-vf","select='not(mod(n,8))',scale=360:640:flags=lanczos",
        "-fps_mode","vfr","-compression_level",2,scan/"frame_%04d.png")
    metrics("ricks_metrics_gate.py","edge.json","--edge-density",scan)
    metrics("ricks_metrics_gate.py","camera.json","--cam-velocity",output,manifest)
    reports={
        "video_frames":ENDS[-1],"part_boundaries":ENDS,"format":"1080x1920 at 30 fps","decode":"PASS",
        "parts":{str(i):load(RENDERS/version/"benchmark.json") for i,version in enumerate(NAMES,1)},
        "word_sync":{key:load(OUT/"word_sync.json")[key] for key in ("status","matched","annotated_nouns_and_actions","coverage")},
        "edge":{key:load(OUT/"edge.json")[key] for key in ("status","mean","min","frame_count","below_minimum_frames")},
        "camera":{key:load(OUT/"camera.json").get(key) for key in ("status","measured_pairs","eligible_pairs",
                                                                   "max_smooth_px_per_frame","hop_destination_frames")},
        "loudness":next(row for row in (OUT/"qa/report.md").read_text().splitlines() if row.startswith("LOUDNESS")),
        "short_qa":{key:load(OUT/"qa/report.json")[key] for key in ("status","black","white","frozen")},
    }
    (OUT/"qa_summary.json").write_text(json.dumps(reports,indent=2))
    print(output)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("phase",choices=("sheet","merge"))
    action=parser.parse_args().phase
    sheet() if action=="sheet" else merge()
