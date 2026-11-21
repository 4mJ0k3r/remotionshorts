"""Full anatomy/staging revision, preserving previous deliverables."""
import sys
import time
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import build_commode_sniper as scene
from timeline import OUT,STILLS,EXTRA_STILLS,FRAMES

phase=sys.argv[sys.argv.index('--')+1]
sc=scene.build();sc.frame_set(25)
for image in bpy.data.images:
    if image.source=='FILE':image.pack();image.use_fake_user=True
scene.embed_runtime(sc);sc['revision']='Seven anatomy and staging fixes; full master'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'commode_sniper_v2_master.blend'))
if phase=='build':raise SystemExit(0)
folder=OUT/('stills_anatomy_v2' if phase=='sheet' else 'frames_anatomy_v2');folder.mkdir(exist_ok=True)
frames=(520,) if phase=='sheet' and 'oil-only' in sys.argv else sorted(set(STILLS+EXTRA_STILLS+(1,42,82,184,234,344,348,400,615,1239,1539,1635))) if phase=='sheet' else range(1,FRAMES+1)
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=6
started=time.time()
for f in frames:
    dest=folder/f'f{f:04}.png'
    if phase=='preview' and dest.exists():continue
    part=folder/f'f{f:04}.part.png';sc.frame_set(f);sc.render.filepath=str(part)
    bpy.ops.render.render(write_still=True);part.replace(dest)
    if phase=='sheet' or f%30==0:print(f'PROBE anatomy frame={f}/{FRAMES} elapsed={time.time()-started:.1f}s',flush=True)
