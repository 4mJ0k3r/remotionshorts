"""Refresh only three held cave shots with visible natural fire movement."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import build_caveman_toilet as build
import v4_overhaul
v4_overhaul.build_scene()
import check_v4
for start,end in ((540,589),(735,827),(1293,1369)):
    build.do_video(start,end,180,320,'v4_fast')
