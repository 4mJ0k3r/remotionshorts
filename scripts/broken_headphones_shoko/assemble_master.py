"""Join native picture on the exact frame grid and validate the finished reel."""
import copy
import json
import subprocess

from master_audio import COUNT, CRASH, FINAL, RATE, mix
from native_pipeline import BOUNDARIES, FPS, PLAN, RENDERS, ROOT, VERSIONS, probe, shell

# Observed story windows, kept on the master narration clock. In the overcast
# scene the intact exterior of the earcup represents the broken audio circuit.
WINDOWS = {
    "w083": (26.43,27.58,"Monday day card"),
    "w093": (45.13,46.03,"Tuesday day card in cool rain"),
    "w097": (46.04,49.36,"Headphone cup visible before Shoko taps it"),
    "w112": (52.20,53.13,"Wednesday day card above Shoko's bed"),
    "w127": (57.20,57.80,"Ringing school alarm"),
    "w133": (58.63,59.47,"Hands closing into the grip"),
    "w136": (60.07,60.99,"Thursday header inside bus"),
    "w138": (59.97,66.50,"Cushioned bus seats and passing brick houses"),
    "w141": (61.47,66.50,"Shoko tilts toward Boy's shoulder and rests"),
    "w143": (61.97,66.50,"Closed eyes and soft blush"),
    "w156": (66.60,67.40,"Friday header in golden hour"),
    "w161": (68.40,69.20,"Friday whisper"),
    "w166": (69.76,71.39,"Both hands on the wireless headset"),
    "w171": (71.56,72.48,"Boy replies and looks toward Shoko"),
    "w175": (72.93,74.69,"Shoko's wide-eyed freeze"),
    "w180": (74.70,77.13,"Crimson cheeks"),
    "w182": (75.40,77.60,"Shoko lifts cardigan sleeves toward her face"),
    "w191": (78.23,80.17,"Shoko runs onto the crossing"),
    "w194": (78.23,80.17,"Shoko runs ahead of Boy"),
    "w200": (81.09,83.43,"Open-armed buildup to the shout"),
    "w204": (82.40,83.43,"Happy eyes and open shout mouth"),
    "w214": (87.67,94.43,"Gravestone and white lilies"),
    "w216": (88.30,94.43,"Pale blue-grey memorial stone"),
    "w221": (90.57,92.03,"Whale carved into the stone"),
    "w232": (95.87,97.33,"Broken headphones represented by the silent earcup"),
    "w233": (95.87,97.33,"Close insert on original matte black earcup"),
    "w236": (94.43,101.77,"Boy walks toward school alone"),
    "w243": (98.87,103.35,"Lily bouquets and crossing railing"),
    "w247": (98.87,103.35,"Boy and the empty crossing"),
    "w252": (101.77,103.35,"Whisper over lilies and empty crosswalk"),
    "w256": (103.37,111.40,"Slow push toward Boy's hollow face"),
    "w258": (104.95,111.40,"Boy holds his stoic face"),
    "repair12": (33.17,35.43,"Lamppost visible before impact"),
    "repair28": (39.83,40.37,"Boy opens wide on KYA"),
}


def write_word_plan():
    plan = copy.deepcopy(PLAN)
    plan["part_boundaries_frames"] = BOUNDARIES
    for item in plan["visual_events"]:
        if item.get("word_id") in WINDOWS:
            item["start"], item["end"], item["visual"] = WINDOWS[item["word_id"]]
        item.pop("status", None)
    dest=FINAL/"master_plan.json"
    dest.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def ff(*args, **kwargs):
    return shell("ffmpeg","-hide_banner","-nostdin",*args,**kwargs)


def manifest():
    shots=[]
    intervals=[]
    cuts=[]
    for index,version in enumerate(VERSIONS):
        source=json.loads((RENDERS/version/"shot_map.json").read_text(encoding="utf-8"))
        offset=BOUNDARIES[index]
        split=[offset,*(offset+f for f in source["cuts"]),BOUNDARIES[index+1]]
        first_id=len(shots)+1
        shots.extend({"id":i,"a":a,"b":b} for i,(a,b) in enumerate(zip(split,split[1:]),first_id))
        cuts.extend(split[:-1])
        intervals.extend((offset+a,offset+b) for a,b in source.get("planned",[]))
    out=FINAL/"shots.json"
    out.write_text(json.dumps({"cuts":cuts[1:],"shots":shots,"planned":intervals},indent=2))
    return out,intervals


def run_metrics(args, filename):
    with (FINAL/filename).open("w",encoding="utf-8") as out:
        try:
            shell("python",*args,stdout=out)
        except subprocess.CalledProcessError as error:
            if error.returncode not in (1, 2):
                raise


def join():
    FINAL.mkdir(exist_ok=True,parents=True)
    listing=FINAL/"parts.ffconcat"
    listing.write_text("ffconcat version 1.0\n"+"".join(
        f"file '../{v}/part{i}_1080p.mp4'\n" for i,v in enumerate(VERSIONS,1)),encoding="utf-8")
    finished=FINAL/"broken_headphones_shoko_FINAL_1080p.mp4"
    pending=finished.with_suffix(".pending.mp4")
    audio=FINAL/"master_audio.wav"
    if not audio.exists():
        mix()
    ff("-v","error","-y","-f","concat","-safe",0,"-i",listing,"-i",audio,
       "-map","0:v","-map","1:a","-c:v","copy","-bsf:v","setts=pts=N*512:dts=N*512:duration=512",
       "-c:a","aac","-b:a","288k","-video_track_timescale",15360,"-movie_timescale",48000,
       "-movflags","+faststart",pending)
    info=probe(pending,BOUNDARIES[-1],audio=True)
    assert abs(float(info["streams"][1]["duration"])-COUNT/RATE)<.000021
    packets=json.loads(shell("ffprobe","-v","error","-select_streams","v:0","-show_packets",
                             "-show_entries","packet=pts,duration","-of","json",pending,
                             capture_output=True).stdout)["packets"]
    assert [(int(p["pts"]),int(p["duration"])) for p in packets]==[(512*i,512) for i in range(BOUNDARIES[-1])]
    crash_frame=round(CRASH*FPS)
    after=BOUNDARIES[3]
    black=ff("-v","error","-i",pending,"-map","0:v:0",
             "-vf",f"trim=start_frame={crash_frame}:end_frame={after},scale=8:8",
             "-an","-fps_mode","passthrough","-pix_fmt","gray","-f","rawvideo","-",capture_output=True).stdout
    assert len(black)==(after-crash_frame)*64 and max(black)<=1
    pending.replace(finished)
    (FINAL/"final_decode_check.json").write_text(json.dumps(info,indent=2))
    return finished


def audit(video, shots, exclusions):
    run_metrics((ROOT/"scripts/short_qa.py",video,FINAL/"qa",shots,"--strict"),"short_qa_stdout.txt")
    plan = write_word_plan()
    run_metrics((ROOT/"scripts/ricks_metrics_gate.py","--word-sync",plan),"word_sync.json")
    # Sample the actual encoded picture at quarter-second intervals. The black
    # crash hold and the closing fade are intentional effects recorded in shots.
    dest=FINAL/"edge_samples"
    dest.mkdir(exist_ok=True)
    conditions="*".join(f"not(between(n,{a},{b}))" for a,b in exclusions)
    ff("-v","error","-y","-i",video,"-vf",f"select='not(mod(n,8))*{conditions}',scale=360:640:flags=lanczos",
       "-fps_mode","vfr","-compression_level",2,dest/"frame_%04d.png")
    run_metrics((ROOT/"scripts/ricks_metrics_gate.py","--edge-density",dest),"final_edge.json")
    run_metrics((ROOT/"scripts/ricks_metrics_gate.py","--cam-velocity",video,shots),"camera_velocity.json")


def summarize(exclusions):
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))

    parts = {}
    for index,version in enumerate(VERSIONS):
        folder = RENDERS/version
        bench = load(folder/"benchmark.json")
        detail = load(folder/"proof_edge.json")
        parts[str(index+1)] = dict(
            frames=BOUNDARIES[index+1]-BOUNDARIES[index],
            max_seconds=bench["max_seconds"], p95_seconds=bench["p95_seconds"],
            sampled_board_peak_gib=bench["sampled_board_peak_gib"],
            max_visible_triangles=bench["max_evaluated_triangles"],
            gpu_status=bench["status"], calibration_edge_mean=detail["mean"], calibration_edge_min=detail["min"],
        )
    word = load(FINAL/"word_sync.json")
    edge = load(FINAL/"final_edge.json")
    cam = load(FINAL/"camera_velocity.json")
    short = load(FINAL/"qa/report.json")
    qa_text = (FINAL/"qa/report.md").read_text(encoding="utf-8")
    data = {
        "video_frames": BOUNDARIES[-1], "native_resolution": [1080,1920], "fps": FPS,
        "duration_s": BOUNDARIES[-1]/FPS, "narration_source_seconds": PLAN["audio_seconds"],
        "part_boundaries_exclusive_frames": BOUNDARIES,
        "crash_blackout_frames": BOUNDARIES[3]-round(CRASH*FPS),
        "planned_black_or_fade_frame_ranges_zero_based": exclusions,
        "decode": "PASS", "parts": parts,
        "word_sync": {key:word[key] for key in ("status","matched","annotated_nouns_and_actions","coverage")},
        "final_edge": {key:edge[key] for key in ("status","mean","min","frame_count","below_minimum_frames")},
        "camera": {key:cam.get(key) for key in ("status","max_smooth_px_per_frame","measured_pairs","eligible_pairs")},
        "short_qa": {key:short[key] for key in ("status","black","white","frozen")},
        "loudness": next(line for line in qa_text.splitlines() if line.startswith("LOUDNESS")),
    }
    (FINAL/"qa_summary.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


if __name__=="__main__":
    video=join()
    shots,black_sections=manifest()
    audit(video,shots,black_sections)
    summarize(black_sections)
    print(video)
