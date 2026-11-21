"""Assemble native calibration and run per-part and final gate reports."""
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

from production import BASE, BOUNDS, HERE, ROOT

sys.path.insert(0,str(ROOT/"scripts"))
from ricks_metrics_gate import edge_density


def report(path, data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")


def checked_edges(folder, exclusions=()):
    data=edge_density(folder)
    excluded=set(exclusions)
    valid=[f for f in data["frames"] if int(Path(f["file"]).stem.rsplit("_",1)[-1]) not in excluded]
    if not valid:
        raise ValueError("No eligible edge-density frames")
    avg=sum(f["density"] for f in valid)/len(valid)
    lowest=min(f["density"] for f in valid)
    checks={"mean_at_least_0_14":avg>=.14,"min_at_least_0_088":lowest>=.088}
    return {**data,"mean":avg,"min":lowest,"checks":checks,"pass":all(checks.values()),
            "excluded_flash_frames":sorted(excluded),
            "below_minimum_frames":[f["file"] for f in valid if f["density"]<.088]}


def preflight(part):
    out=BASE/f"part{part}_v02"
    plan=json.loads((out/"shot_map.json").read_text())
    benchmark=json.loads((out/"benchmark.json").read_text())
    data=checked_edges(out/benchmark.get("native_stills_dir","native_proof"),plan.get("flashes",[]))
    report(out/"edge_density.json",data)
    print(part,benchmark["status"],benchmark["max_seconds"],benchmark["sampled_board_peak_gib"],
          benchmark["max_evaluated_triangles"],data["pass"],data["mean"],data["min"],data["below_minimum_frames"])
    return data["pass"] and benchmark["status"]=="PASS"


def calibration():
    font=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",31)
    small=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",16)
    canvas=Image.new("RGB",(1900,1412),"#181322")
    draw=ImageDraw.Draw(canvas)
    draw.text((22,14),"POKHRAN-II  /  PARTS 2–4  /  NATIVE V02 CALIBRATION",font=font,fill="#fde5cd")
    selections=((0,2,4,5,6,7,8,10),(0,1,3,4,6,8,9,10),(0,2,3,4,7,8,10,11))
    for j,(part,selection) in enumerate(zip((2,3,4),selections)):
        out=BASE/f"part{part}_v02"
        plan=json.loads((out/"shot_map.json").read_text())
        benchmark=json.loads((out/"benchmark.json").read_text())
        for col,index in enumerate(selection):
            f=plan["proof_frames"][index]
            x,y=22+233*col,77+442*j
            with Image.open(out/benchmark.get("native_stills_dir","native_proof")/f"frame_{f:04d}.png") as source:
                canvas.paste(source.convert("RGB").resize((217,386),Image.Resampling.LANCZOS),(x,y))
            tin=(BOUNDS[part-1]+f-1)/30
            draw.text((x,y+397),f"PART {part}     f{f:03}     {tin:.2f} s",font=small,fill="#f4be9e")
    canvas.save(BASE/"parts234_v02_calibration.png")


def manifests():
    old=json.loads((HERE.parent/"v01b/master_plan.json").read_text(encoding="utf-8"))
    hook=json.loads((HERE.parent/"v02b/master_plan.json").read_text(encoding="utf-8"))
    old["visual_events"]=hook["visual_events"]+[
        {"word_id":wid,"kind":"prop","visual":name,"start":a,"end":b} for wid,name,a,b in [
          ("w038","CIA Pokhran image review on wall",14.8,17.46),("w040","Desert scan monitor",14.8,17.46),
          ("w042","CIA analysts at consoles",14.8,19.40),("w044","US orbital control center",17.47,19.40),
          ("w046","Keyhole lens and aperture",19.40,20.20),("w048","Keyhole optical insert",19.40,20.20),
          ("w051","Time index on image review terminal",20.20,23.81),
          ("w054","Enlarged Pokhran image",20.20,23.81),("w055","Aerial image CRT",20.20,23.81),
          ("w056","Magnifier traverses image",20.20,23.81),("w061","Track alert",23.81,28.60),
          ("w072","Dr. Kalam in tent",28.60,33.43),("w073","Dr. Kalam in tent",28.60,33.43),
          ("w075","58th Engineers in tent",28.60,33.43),("w077","Engineer beside Kalam",31.12,33.43),
          ("w079","Orbital globe and chalk orbit drawing",31.12,33.43),
          ("w083","Chalk orbit diagram",33.62,34.36),("w084","Blindspot heading on board",33.62,34.36),
          ("w086","Kalam confident response",34.36,35.60),("w090","Illustrative satellite pass",35.60,38.32),
          ("w093","Bowler Engineer delivers ball",35.60,38.31),("w095","Kalam cheers beside pitch",38.32,40.30),
          ("w098","Cricket stroke",38.32,40.30),("w099","Cricket stroke and follow-through",38.32,40.30),
          ("w105","Green scenic blindspot label",41.00,43.20),("w110","Abstract industrial shaft scene",43.21,45.20),
          ("w111","Abstract glowing shaft scene",43.21,45.20),("w113","Winch prop action",43.21,45.20),
          ("w118","Wind past raised mitten",45.20,46.00),("w122","Foreground sand",46.00,50.60),
          ("w124","Two straw brooms",46.00,50.60),("w127","Graphic impressions fading",47.33,49.43),
          ("w131","Clean-sand hold",49.90,50.60),("w135","Stylized seismic event",50.94,52.05),
          ("w139","CIA alarm reaction",52.32,55.07),("w140","CIA shocked faces",52.61,55.07)
        ]]
    old["part_boundaries_frames"]=BOUNDS
    report(BASE/"master_plan.json",old)
    cuts=json.loads((BASE.parent/"v02b/cuts.json").read_text())["cuts"]
    excluded=[]
    for index,start in enumerate(BOUNDS[1:-1],2):
        plan=json.loads((BASE/f"part{index}_v02/shot_map.json").read_text())
        cuts.extend(start+frame-1 for frame in plan["cuts"])
        excluded.extend(start+frame for frame in plan.get("flashes",[]))
    shots=[{"id":j,"a":a,"b":b} for j,(a,b) in enumerate(zip((0,*cuts),(*cuts,BOUNDS[-1])),1)]
    intervals=[[min(excluded)-1,max(excluded)-1]] if excluded else []
    report(BASE/"shots.json",{"cuts":cuts,"shots":shots,"planned":intervals})
    return excluded


def diagnostics():
    clip=BASE/"pokhran_1998_v02_FINAL_1080p.mp4"
    qa=BASE/"final_qa"
    qa.mkdir(exist_ok=True)
    excluded=manifests()
    commands=(
        ("short_qa.log",[str(ROOT/"scripts/short_qa.py"),str(clip),str(qa),str(BASE/"shots.json")]),
        ("word_sync.json",[str(ROOT/"scripts/ricks_metrics_gate.py"),"--word-sync",str(BASE/"master_plan.json")]),
        ("camera_velocity.json",[str(ROOT/"scripts/ricks_metrics_gate.py"),"--cam-velocity",str(clip),str(BASE/"shots.json")]),
    )
    jobs=[]
    for filename,args in commands:
        with (qa/filename).open("w",encoding="utf-8") as log:
            jobs.append(subprocess.Popen([sys.executable,*args],stdout=log,stderr=subprocess.STDOUT))
    edge_dir=qa/"decoded_edge_frames"
    edge_dir.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg","-nostdin","-v","error","-y","-i",str(clip),"-an","-vf","scale=360:640:flags=bilinear",
                    "-start_number","1",str(edge_dir/"frame_%04d.png")],check=True)
    result=checked_edges(edge_dir,excluded)
    report(qa/"edge_density.json",result)
    print("Full reel edge density:",result["mean"],result["min"],result["pass"])
    print("Diagnostic exits:",[job.wait() for job in jobs])


if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="calibrate":
        results=[preflight(part) for part in (2,3,4)]
        calibration()
        raise SystemExit(int(not all(results)))
    if mode=="final":
        diagnostics()
    else:
        raise SystemExit(int(not preflight(int(mode))))
