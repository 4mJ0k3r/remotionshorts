"""Persist smooth blend treatment on FX generated before the source correction."""
import bpy
from pathlib import Path
for m in bpy.data.materials:
    if m.name.startswith(('V3 puff_','V3 sweat')):m.surface_render_method='BLENDED'
bpy.ops.wm.save_as_mainfile(filepath=str(Path(r'D:\remotionshorts\renders\hair_sensor\hair_sensor_v3.blend')))
