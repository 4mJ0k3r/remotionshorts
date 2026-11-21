"""Retain currently unused speech/blink materials in the editable scene."""
import bpy
import json
import re
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from build_puri_flag_physics import card_material, OUT, SPR
bpy.ops.wm.open_mainfile(filepath=str(OUT/'puri_flag_physics.blend'))
state=json.loads(bpy.context.scene['procedural_rig_state'])
names=set()
def collect(value):
    if isinstance(value,list):
        for v in value:collect(v)
    elif isinstance(value,dict):
        if 'material' in value:names.add(value['material'])
        for v in value.values():collect(v)
collect(state)
for name in names:
    if name not in bpy.data.materials:
        filename=re.sub(r'\.\d{3}$','',name)+'.png'
        restored=card_material(SPR/filename);restored.name=name
    bpy.data.materials[name].use_fake_user=True
for image in bpy.data.images:
    if image.source=='FILE':image.pack();image.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'puri_flag_physics.blend'))
print('QA restored saved speech/blink materials',flush=True)
