"""Refresh the offscreen-fire squat's soft ambient bounce only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import bpy
import v4_overhaul as v4
import build_caveman_toilet as build
from v2_common import OUT
bpy.ops.wm.open_mainfile(filepath=str(OUT/'caveman_toilet_v4.blend'))
v4.animate_squat_fire_bounce()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'caveman_toilet_v4.blend'))
build.do_video(735,827,180,320,'v4_fast')
build.do_sheet(540,960,12,'v4_final')
