"""Bind audible named cues and record the agreed Stage 1 timeline."""
import json
from pathlib import Path
import subprocess

import numpy as np

HERE=Path(__file__).resolve().parent
FRAMES=(0,790,1702,1995,2630,3357)
CUES=(
    ("w003","walk","Morning walk toward school",0,4.10),
    ("w004","walk","Planted-foot sidewalk walk",0,4.10),
    ("w007","crush","Shoko by Boy's right shoulder",0,4.10),
    ("w010","whisper","Shoko mouths the whispered line",2.86,3.53),
    ("w018","eyes","Unblinking deadpan eye insert",4.10,6.76),
    ("w022","wire","Headphone cable with three torn strands",6.77,8.47),
    ("w032","headphones","Old headphones on the living-room rug",8.50,14.06),
    ("w033","flashback","Gold YEAR 7 card",8.90,12.23),
    ("w040","puppy","Cream puppy muzzle on the rug",12.30,14.06),
    ("w042","cable","Cable leads from headphones across the rug",12.30,14.06),
    ("w043","chew","Puppy chomps and flicks the cable",12.30,14.06),
    ("w047","wearing","Boy's headphones stay on as he walks past",14.06,17.56),
    ("w049","passes","Boy walks past the waving classmate",14.06,17.56),
    ("w054","avoid-talk","Waving classmate ignored",14.13,17.56),
    ("w059","shoko","Warm close-up on Shoko",17.56,19.23),
    ("w061","locker-hall","Red numbered lockers and books",19.23,21.06),
    ("w066","shy","Shy look while passing lockers",19.23,21.06),
    ("w074","music-mask","Headphones in the courtyard walk",22.06,23.83),
    ("w078","chatter","Chatter close-up with alternating mouths",23.80,25.50),
    ("w080","chatter","Stormcloud and lightning above Shoko during chatter",24.66,25.50),
    ("w083","monday","MONDAY diegetic day card",26.33,27.00),
    ("w090","monday-whisper","Monday whisper on the sidewalk",28.16,30.50),
    ("w093","tuesday","TUESDAY card in rain",44.96,45.72),
    ("w097","headphone-tap","Shoko's fingertip touches headphone shell",46.40,47.70),
    ("w106","panic","Boy flinches with blue sweat bead",49.62,51.82),
    ("w110","pooja","Reaction to Dhinchak Pooja line",50.83,51.88),
    ("w112","wednesday","WEDNESDAY day card and phone",52.06,53.28),
    ("w117","all-nighter","Late-night bedroom study",53.40,56.66),
    ("w119","playlist","Dhinchak Pooja on phone display",54.24,55.82),
    ("w122","forty","40 Songs phone page",55.20,56.12),
    ("w127","fire-drill","Fire alarm and busy outdoor drill",56.95,58.60),
    ("w133","hand-hold","Macro on Shoko taking Boy's hand",58.79,59.78),
    ("w136","thursday","THURSDAY header on bus",59.91,60.74),
    ("w138","bus","Bus seats and passing window light",60.69,66.49),
    ("w141","shoulder","Shoko leans against Boy's shoulder",61.41,66.49),
    ("w143","sleep","Closed eyes and soft blush",61.92,66.49),
    ("w156","friday","FRIDAY header in golden hour",66.49,67.30),
    ("w161","declaration","Shoko whispers the Friday line",68.33,69.29),
    ("w166","removes-headphones","Both hands lift the broken headset",69.76,70.82),
    ("w171","love-you-too","Boy's warm reply",71.51,72.65),
    ("w175","freeze","Shoko stunned eyes",72.86,73.85),
    ("w180","crimson","Shoko flushes",74.62,76.60),
    ("w182","sleeves","Shoko covers her face with cardigan sleeves",75.28,76.81),
    ("w191","crossing","Joyful run at the crossing",78.19,81.33),
    ("w194","sprint","Shoko sprints ahead",78.22,81.33),
    ("w200","shout","Shoko calls across the road",81.15,83.23),
    ("w204","love-you","Happy eyes on the final call",82.26,83.23),
    ("w214","grave","Sunlit gravestone and white lilies",87.67,93.61),
    ("w216","gravestone","Carved memorial stone",87.67,93.61),
    ("w221","whale","Cute whale carved into the monument",90.56,92.14),
    ("w232","broken","Dangling frayed audio lead in overcast light",95.44,96.60),
    ("w233","headphones","Same headphones worn on the walk",94.32,98.45),
    ("w236","school","Lonely walk toward school",94.32,98.45),
    ("w243","corner","Memorial flowers and crosswalk railing",99.22,103.06),
    ("w247","echo","Empty space beside Boy and distant whisper",100.59,103.05),
    ("w252","love-you-echo","Crosswalk echo of Shoko's line",102.37,103.05),
    ("w256","face","Slow push toward Boy's hollow expression",103.24,111.0),
    ("w258","still","Boy holds his stoic face",104.95,110.0),
)


def gap_words():
    """Recover the spoken Monday passage missed by the full-length decode."""
    from faster_whisper import WhisperModel
    from transcribe import NARRATION

    raw=subprocess.check_output(["ffmpeg","-nostdin","-v","error","-i",str(NARRATION),"-ar","16000",
                                 "-ac","1","-f","f32le","-"])
    signal=np.frombuffer(raw,"<f4")[28*16000:46*16000]
    model=WhisperModel("medium",device="cpu",compute_type="int8",cpu_threads=8,local_files_only=True)
    segments,_=model.transcribe(signal,language="hi",beam_size=5,word_timestamps=True,vad_filter=True,
                                condition_on_previous_text=False)
    selected=[]
    for s in segments:
        for w in s.words:
            start,end=round(w.start+28,2),round(w.end+28,2)
            word=w.word.strip()
            if start>=29.18 and start<45.01 and "ट्यूस्ट" not in word:
                selected.append({"id":f"repair{len(selected)+1:02}","text":word,"start":start,"end":end,"kind":"other"})
    return selected


def main():
    data=json.loads((HERE/"transcript.json").read_text(encoding="utf-8"))
    repair_path=HERE/"monday_reviewed_words.json"
    if not repair_path.exists():
        recovery=gap_words()
        repair_path.write_text(json.dumps(recovery,ensure_ascii=False,indent=2),encoding="utf-8")
    else:
        recovery=json.loads(repair_path.read_text(encoding="utf-8"))
    data["words"]=sorted(data["words"]+recovery,key=lambda row:row["start"])
    visual=[{"kind":"face","start":0.0,"end":4.1}]
    event_list=list(CUES)
    for token,event,name,start,end in (
        ("खंबे","lamppost","Boy bonks into a lamp standard",33.04,35.15),
        ("क्या","yell","Boy yells KYA?!",39.76,40.46),
    ):
        word=next((w for w in recovery if token in w["text"]),None)
        if word:
            event_list.append((word["id"],event,name,start,end))
    indexed={row["id"]:row for row in data["words"]}
    for wid,slug,name,a,b in event_list:
        indexed[wid]["kind"]="action" if slug in {"walk","whisper","chew","passes","wearing","chatter","sprint","shout","yell"} else "noun"
        visual.append({"word_id":wid,"kind":"prop","visual":name,"start":a,"end":b,
                       "status":"part1 staging" if b<=26.34 else "planned only"})
    data.update({"visual_events":visual,"hook_end":2.0,"part_boundaries_frames":FRAMES,
                 "brake_placement_note":"Part 4 only, after the final Friday line and before the cemetery entry",
                 "narration_policy":"Original source and cadence, timed on decoded sample boundaries"})
    (HERE/"master_plan.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")


if __name__=="__main__":
    main()
