"""The edit clock and Stage 1 scene spans at 30 fps."""
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/november_doubling_comedy/v01"
SOURCE=Path.home()/"Downloads"/"ElevenLabs_2026-11-20T19_36_01_Viraj - Confident and Natural_pvc_s30_sim75_v4.mp3"
FPS=30
BOUNDARIES=(0,660,1134,1465,1948)
LENGTH=BOUNDARIES[1]


def at(seconds):
    return round(FPS*seconds)+1


DAY1=9.80
DAY2=14.77
PHONE_IN=11.53
PHONE_OUT=12.13
WRONG_NUMBER=11.63
DROP=20.13
CLANK=20.37
