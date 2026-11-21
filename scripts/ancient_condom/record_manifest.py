from pathlib import Path
import json,hashlib,datetime
ROOT=Path(r'D:\remotionshorts');OUT=ROOT/'renders/ancient_condom';SRC=ROOT/'scripts/ancient_condom'
paths=[OUT/'ancient_condom.blend',OUT/'audio_master.wav',OUT/'sheet_cel_v2.jpg',OUT/'shots.json']+list(SRC.glob('*.py'))
manifest={'local_time':datetime.datetime.now().isoformat(timespec='seconds'),'scope':'stills only','style_reference_override':'latest user screenshots: flat cel cast in 3D world','tile_source':'calibration_cel_v2; four new character tiles; other16 inspected process tiles','files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths]}
(OUT/'input_manifest.json').write_text(json.dumps(manifest,indent=2));print('Recorded source, audio and inspection-sheet manifest.')
