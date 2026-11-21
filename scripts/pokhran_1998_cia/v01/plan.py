"""Bind measured speech cues to the hook and the remaining storyboard."""
import json
from pathlib import Path

p=Path(__file__).with_name("master_plan.json")
plan=json.loads(p.read_text(encoding="utf-8"))
words={item["id"]:item for item in plan["words"]}
bindings=[
    (1,"noun","Console date 1998",1,116),(3,"noun","US surveillance room",1,116),
    (7,"noun","Satellite hero view",117,278),(9,"noun","Rajasthan camera target graphic",145,260),
    (11,"action","Image acquisition sweep",185,215),(20,"action","Camera passes below the desert surface",279,308),
    (21,"noun","Indian test-site exhibit",279,378),(23,"noun","Count of five sealed shapes",295,378),
    (24,"noun","Five symbolic nuclear test markers",295,378),(25,"noun","Five symbolic nuclear test markers",295,378),
    (26,"action","Indicators illuminate on the cutaway",346,378),(30,"noun","CIA boss reaction",379,455),
    (33,"action","Boss remains unaware",402,455),
    (38,"noun","Pokhran photo",484,520),(40,"noun","Desert imagery",504,536),
    (42,"noun","Surveillance desks",530,575),(44,"noun","Investment indicated by monitor array",553,600),
    (46,"noun","Keyhole illustration",580,633),(48,"noun","Satellite image feed",588,633),
    (51,"noun","Period clock",633,653),(54,"noun","Photographic enlargement",660,714),
    (55,"noun","Photographic enlargement",660,714),(56,"action","Camera click",700,714),
    (61,"action","Analyst reacts to possible mistake",751,793),
    (72,"noun","Kalam entrance",870,1002),(73,"noun","Kalam entrance",870,1002),
    (75,"noun","58th Regiment group",908,999),(77,"noun","58th Regiment group",908,999),
    (79,"noun","Illustrative observation display",960,1033),
    (83,"noun","Abstract observation graphic",1015,1055),(84,"noun","Abstract observation graphic",1015,1055),
    (86,"action","Kalam gestures in discussion",1038,1068),(90,"noun","Distant satellite silhouette",1086,1120),
    (93,"noun","Soldiers enter",1136,1209),(95,"noun","Scientists join",1151,1209),
    (98,"noun","Cricket bat and ball",1189,1221),(99,"action","Cricket swing",1196,1221),
    (105,"noun","Illustrative scan leaves picture",1249,1285),
    (110,"noun","Abstract underground cutaway",1293,1360),(111,"noun","Abstract underground cutaway",1293,1360),
    (113,"action","Concealed work shown in silhouette",1324,1367),
    (118,"noun","Wind in stylized desert atmosphere",1369,1409),(122,"noun","Sand texture in foreground",1405,1460),
    (124,"noun","Broom seen in montage",1419,1469),(127,"action","Desert surface transition",1445,1490),
    (131,"noun","Quiet undisturbed desert image",1489,1518),(135,"noun","Distant symbolic dust dome",1538,1568),
    (139,"noun","International reaction montage",1592,1641),(140,"action","War-room reaction",1600,1652),
]
events=[{"kind":"face","start":0,"end":3.83,"status":"hook staging"}]
for i,kind,visual,start,end in bindings:
    word=words[f"w{i:03d}"];word["kind"]=kind
    events.append({"kind":"prop" if kind=="noun" else "action","word_id":word["id"],
                   "start":round((start-1)/30,2),"end":round(end/30,2),"visual":visual,
                   "frames":[start,end],"status":"hook staging" if end<=455 else "storyboard only"})
plan.update({"hook_end":2,"part_boundaries_frames":[0,455,865,1221,1652],
             "visual_events":events,"narration_preservation":"Original supplied audio, including the final loop word"})
p.write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf-8")
