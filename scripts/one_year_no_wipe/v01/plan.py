"""Bind the transcribed narration to the first-stage shots and later storyboards."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=Path.home()/"Downloads"/"ElevenLabs_2026-11-20T14_52_07_Viraj - Confident and Natural_pvc_s30_sim75_v4.mp3"


def make_plan():
    original=json.loads((HERE/"transcript.json").read_text(encoding="utf-8"))
    patch=json.loads((HERE/"chunk_transcript.json").read_text(encoding="utf-8"))
    patch[0]["start"]=28.20
    original[78]["start"]=patch[48]["start"]
    words=[*original[:73],*patch[:23],*patch[27:48],*original[78:]]
    scenes=[
        (0,6.27,"Bathroom hook"),(6.27,13.07,"Day 1 empty roll"),(13.07,27.90,"Day 2 classroom"),
        (27.90,37.30,"Microscope disco"),(37.30,46.52,"City bus and skatole"),
        (46.52,53.63,"Wilted florist display"),(53.63,65.00,"Month 1 mushroom tourists"),
        (65.00,74.17,"Month 6 dogs and follow alerts"),(74.17,81.23,"Day 365 escaping underwear"),
        (81.23,82.3667,"Toilet-paper avalanche, visual punchline"),
    ]
    windows=[
        (2.78,2.67,4.66,"Toilet and seated Boy","noun"),
        (3.54,2.67,4.66,"Boy glances toward the roll holder","action"),
        (6.30,6.30,7.67,"DAY 1 calendar","noun"),
        (7.44,7.23,8.39,"Reach to the wall-mounted toilet-paper holder","noun"),
        (7.76,7.67,8.39,"Empty cardboard core macro","noun"),
        (8.04,7.67,8.97,"Bare tube rotates and settles","action"),
        (10.22,10.17,11.90,"Raised shoulders and outward palms","noun"),
        (10.62,10.17,11.90,"Boy shrugs and gives a cocky smirk","action"),
        (13.06,13.07,15.38,"DAY 2 calendar and classroom","noun"),
        (16.28,15.85,18.17,"Boy squirms and winces at his desk","action"),
        (18.10,17.16,20.39,"Boy growing uncomfortable, clothed","noun"),
        (18.58,18.17,20.39,"Classmate's frowning side-eye","action"),
        (20.42,20.39,22.60,"Fidgeting intensifies","action"),
        (22.64,22.60,23.55,"Medical-punchline camera setup","noun"),
        (23.60,23.57,25.05,"PRURITUS ANI red stamp","noun"),
        (24.42,23.57,25.05,"PRURITUS ANI red stamp held","noun"),
        (25.56,25.43,27.90,"Teacher at the water-cycle board","noun"),
        (26.62,26.60,27.90,"Teacher speaks and raises his pointing arm","action"),
        (27.06,27.04,27.90,"Teacher's articulated scold","action"),
        (27.36,27.34,27.90,"Boy freezes as the teacher scolds","action"),
        (30.74,30.62,33.60,"Scale change and microscopic gram sample","noun"),
        (32.84,32.75,37.30,"Glowing bacteria and x1000 graphic","noun"),
        (34.64,34.57,37.30,"Abstract skin-texture dance floor","noun"),
        (35.84,35.77,37.30,"Bacteria disco party","action"),
        (37.30,37.27,39.75,"DAY 3 card on city bus","noun"),
        (39.24,39.20,41.15,"Stylized odor swirls and passengers' reactions","noun"),
        (41.40,41.37,46.52,"SKATOLE graphic","noun"),
        (46.52,46.49,52.70,"Florist's bouquet","noun"),
        (47.18,46.49,50.10,"Flowers and the fragrance comparison","noun"),
        (48.48,48.43,49.81,"Perfume bottle on florist counter","noun"),
        (50.70,50.64,53.62,"Flowers wilt in the exaggerated gag","action"),
        (53.62,53.60,55.12,"MONTH 1 calendar","noun"),
        (56.58,56.54,60.30,"Purple mushroom tourists with luggage","noun"),
        (60.38,60.34,64.83,"Warm icon","noun"),
        (61.08,61.04,64.83,"Wet icon","noun"),
        (61.88,61.84,64.83,"Dark icon","noun"),
        (62.60,62.57,64.83,"Three icons and confetti","action"),
        (65.00,64.97,66.73,"MONTH 6 calendar","noun"),
        (66.78,66.71,73.90,"Five dogs join the parade","noun"),
        (68.46,68.42,71.45,"Dogs sniff as a visual gag","action"),
        (69.00,68.96,73.80,"Comic follow notifications","noun"),
        (72.98,72.92,73.92,"Crowded viral dog parade","action"),
        (74.18,74.13,75.90,"DAY 365 calendar","noun"),
        (79.58,79.53,81.23,"Underwear prepares to crawl away","noun"),
        (81.00,80.94,81.70,"Underwear escapes","action"),
    ]
    events=[{"kind":"face","start":0,"end":6.26,"status":"Stage 1"}]
    used=set()
    for at,a,b,label,kind in windows:
        candidates=[i for i,w in enumerate(words) if i not in used and abs(w["start"]-at)<=.03]
        if not candidates:
            raise ValueError(f"No recorded word for {at}: {label}")
        i=candidates[0]
        used.add(i)
        events.append({"kind":"prop" if kind=="noun" else "action","word_id":f"w{i:03}",
                       "start":a,"end":b,"visual":label,"status":"Stage 1" if at<27.9 else "planned"})
    for i,word in enumerate(words):
        word.update(id=f"w{i:03}",kind="other")
    for event,window in zip(events[1:],windows):
        words[int(event["word_id"][1:])]["kind"]=window[-1]
    duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
                                             "-of","csv=p=0",str(SOURCE)]))
    dst=HERE/"master_plan.json"
    dst.write_text(json.dumps({"narration_seconds":duration,"source_audio":{"file":SOURCE.name,
        "sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest()},"part_boundaries_frames":[0,837,1609,2225,2471],
        "hook_end":2,"words":words,"visual_events":events,"scenes":[{"scene":i,"start":a,"end":b,"beat":label}
                                                                for i,(a,b,label) in enumerate(scenes,1)]},
        ensure_ascii=False,indent=2),encoding="utf-8")
    return dst


if __name__=="__main__":
    print(make_plan())
