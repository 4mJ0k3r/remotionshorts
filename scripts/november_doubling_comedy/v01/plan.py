"""Store word-level times and separate animated cues from the later storyboard."""
from hashlib import sha256
import json

from timing import BOUNDARIES, CLANK, DAY1, DAY2, HERE, SOURCE, WRONG_NUMBER


def make():
    original=json.loads((HERE/"transcript.json").read_text(encoding="utf8"))
    first,second,last=json.loads((HERE/"chunk_transcript.json").read_text(encoding="utf8"))
    words=[*original[:44],*first[4:],*second[:2],*second[3:19],*last,*original[54:]]
    words.sort(key=lambda w:w["start"])
    cues=(
        (2.48,2.33,3.18,"November calendar comes into view","noun"),
        (3.60,3.20,6.46,"Calendar in the background as Hero points","noun"),
        (4.68,4.36,6.47,"Hero sizes up the doubling with both palms","noun"),
        (5.04,4.92,6.44,"Two-handed doubling gesture","action"),
        (6.48,6.38,9.80,"Hero notices November's last row on the calendar","noun"),
        (7.94,7.74,9.80,"Eyes widen at the thought of day thirty","action"),
        (9.84,DAY1,14.77,"DAY 1 / 8 cm / LIKE ORANGES HUD","noun"),
        (11.04,10.81,12.13,"2:00 clock and handset","noun"),
        (11.64,WRONG_NUMBER,12.3,"Wrong number text enters on the phone","noun"),
        (12.48,12.13,13.65,"Phone stays in Hero's hand on the reaction","noun"),
        (13.42,12.86,14.77,"Crushed deadpan heartbreak","action"),
        (14.80,DAY2,21.99,"DAY 2 / 16 cm / LIKE MELONS HUD","noun"),
        (16.16,DAY2,21.99,"Grey fabric pads and LIKE MELONS comparison","noun"),
        (17.72,DAY2,21.99,"Gym rack and weights behind Hero","noun"),
        (18.20,17.67,20.05,"Short planted penguin waddle","action"),
        (18.86,17.67,20.05,"Stiff shoulders and low sneaker lift through the waddle","action"),
        (20.16,20.10,21.99,"Leg day abandoned; dumbbell drops, then awkward exit","action"),
        (23.36,22.00,27.64,"Café counter and barista","noun"),
        (23.74,23.68,25.65,"Barista reaction and cup handoff","noun"),
        (24.20,24.13,26.83,"Coffee cup graphic insert","noun"),
        (24.88,24.80,26.83,"Token 47 printed on the cup","noun"),
        (26.08,26.02,27.64,"Hero sees the matching token number","noun"),
        (27.72,27.68,33.51,"Day 4 / 64 cm HUD","noun"),
        (28.4,28.38,32.46,"Office stand-up meeting and scene depth","noun"),
        (29.0,28.92,32.46,"Clipboard and coworkers during meeting","noun"),
        (30.76,30.69,32.51,"Soft bean-bag pose against the padded sweatpants","noun"),
        (31.66,31.59,32.57,"Hero slumps onto pads","action"),
        (33.52,33.46,37.79,"Day 6 / 2.56 m HUD","noun"),
        (34.54,34.49,37.73,"Apartment doorway and stuck silhouette","noun"),
        (35.12,35.05,36.18,"Padded outfit jams in the doorway","action"),
        (35.76,35.69,37.73,"Two neighbors in the hall","noun"),
        (36.22,36.13,37.72,"Neighbor push and release","action"),
        (38.12,38.05,43.62,"Day 8 / 10.2 m HUD","noun"),
        (38.86,38.80,43.62,"Three-storey building comparison","noun"),
        (40.50,40.43,41.37,"Hero sits at roof height","action"),
        (41.36,41.28,43.63,"Fire brigade arrives and extends ladder","noun"),
        (42.24,42.16,43.95,"Grocery bag handoff","noun"),
        (45.64,45.58,48.73,"Phone in hand over timer safe","noun"),
        (46.58,46.53,48.73,"December 1 countdown display","noun"),
        (47.18,47.12,48.73,"Timer safe opening","noun"),
        (47.74,47.69,48.82,"Safe locks","action"),
        (49.08,49.02,55.81,"Day 30 / 42,950 km HUD","noun"),
        (50.82,50.73,55.83,"Deep-space reveal","noun"),
        (52.28,52.20,55.85,"Three Earth widths indicated graphically","noun"),
        (53.46,53.39,55.87,"Satellite silhouette","noun"),
        (54.60,54.52,55.88,"Satellite swerves clear","action"),
        (57.60,57.54,59.85,"December 1 calendar","noun"),
        (58.20,58.13,59.80,"Midnight timer","noun"),
        (59.24,59.17,60.07,"Safe clicks open","action"),
        (60.96,60.90,62.12,"Challenge success payoff","action"),
        (62.80,62.74,64.94,"Deadpan final reaction","action"),
    )
    events=[{"kind":"face","start":0,"end":2.33,"status":"stage1","visual":"Hero opens on camera"}]
    for i,w in enumerate(words):
        w.update(id=f"w{i:03}",kind="other")
        w["end"]=max(w["start"],w["end"])
    for t,a,b,visual,kind in cues:
        match=min(words,key=lambda w:abs(w["start"]-t))
        if abs(match["start"]-t)>.025 or match["kind"]!="other":
            raise RuntimeError(f"Unmatched or duplicate cue at {t:.2f} for {visual}")
        match["kind"]=kind
        events.append({"kind":"prop" if kind=="noun" else kind,"word_id":match["id"],"start":a,"end":b,"visual":visual,
                       "status":"stage1" if t<22 else "planned"})
    plan={
        "fps":30,"source_audio":{"file":SOURCE.name,"sha256":sha256(SOURCE.read_bytes()).hexdigest(),"duration_seconds":64.91425},
        "part_boundaries_frames":BOUNDARIES,
        "parts":[
            {"number":1,"beats":["November hook","Day 1 wrong number","Day 2 gym"],"status":"stage1"},
            {"number":2,"beats":["Day 3 café","Day 4 office","Day 6 doorway"],"status":"planned"},
            {"number":3,"beats":["Day 8 fire brigade and groceries","Phone timer box"],"status":"planned"},
            {"number":4,"beats":["Day 30 satellite swerve","December 1 midnight","Deadpan payoff"],"status":"planned"},
        ],
        "clank_seconds":CLANK,"hook_end":2.0,"words":words,"visual_events":events,
    }
    (HERE/"master_plan.json").write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding="utf8")


if __name__=="__main__":
    make()
