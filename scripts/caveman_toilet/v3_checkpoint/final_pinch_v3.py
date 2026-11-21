"""Rebuild the V3 source and refresh only the nose-pinch cut and sheet tile."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import bpy
import build_caveman_toilet as build
from v2_common import OUT
build.build_scene()
import check_v3
sc=bpy.context.scene
sc.render.resolution_x=540
sc.render.resolution_y=960
sc.eevee.taa_render_samples=12
sc.frame_set(1080)
sc.render.filepath=str(OUT/'calibration_v3_final'/'tile_10_f1080.png')
bpy.ops.render.render(write_still=True)
build.do_video(1038,1124,180,320,'v3_fast')
