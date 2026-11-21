"""Frame-accurate Part 2 boundaries and cues on the original narration clock."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SHARED=HERE.parent/"v03"
OUT=ROOT/"renders/broken_headphones_shoko/part2_v01"
PLAN=json.loads((SHARED/"master_plan.json").read_text(encoding="utf-8"))
START,STOP=PLAN["part_boundaries_frames"][1:3]
LENGTH=STOP-START
RATE=48000
FPS=30


def frame(seconds):
    return round(seconds*FPS)-START+1


BONK=frame(34.36)
TAP=frame(46.98)
SCRATCH=frame(49.68)
PHONE=frame(54.18)
PHONE_END=PHONE+36
CUTS=(1,frame(30.78),frame(33.18),frame(35.43),frame(38.45),frame(40.53),
      frame(45.04),frame(46.04),frame(49.36),frame(52.12),PHONE,PHONE_END)
BENCH=(frame(29.64),BONK,frame(45.50),TAP,frame(51.12),PHONE+13)
