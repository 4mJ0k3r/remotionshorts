"""Refresh the corrected terrain act and two short transition ranges."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import build_caveman_toilet as build
build.build_scene()
import check_v3
build.do_sheet(540,960,12,'v3_final')
for start,end in ((1,539),(1120,1124),(1475,1493)):
    build.do_video(start,end,180,320,'v3_fast')
