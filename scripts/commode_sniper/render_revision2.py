"""Re-render only first four cuts for corrected stance and pressure acting."""
import sys
import time
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import build_commode_sniper as scene
from timeline import OUT

phase=sys.argv[sys.argv.index('--')+1]
sc=scene.build();sc.frame_set(25)
for image in bpy.data.images:
    if image.source=='FILE':image.pack();image.use_fake_user=True
scene.embed_runtime(sc)
sc['revision']='V2 natural rear/side stance and pressure slip/regrip acting'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'commode_sniper_v2.blend'))
if phase=='build':raise SystemExit(0)
frames=(12,25,40,242,255,269,282,300) if phase=='sheet' else range(1,417)
folder=OUT/('stills_revision2' if phase=='sheet' else 'frames_revision2');folder.mkdir(exist_ok=True)
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=6
started=time.time()
for f in frames:
    dest=folder/f'f{f:04}.png'
    if phase=='preview' and dest.exists():continue
    part=folder/f'f{f:04}.part.png';sc.frame_set(f);sc.render.filepath=str(part)
    bpy.ops.render.render(write_still=True);part.replace(dest)
    if phase=='sheet' or f%30==0:print(f'PROBE revision2 frame={f}/416 elapsed={time.time()-started:.1f}s',flush=True)
