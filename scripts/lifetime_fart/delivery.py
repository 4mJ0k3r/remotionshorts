"""Tile calibration frames and mux Blender chunks with the full Hindi narration."""
from pathlib import Path
import json
import subprocess
import sys
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/lifetime_fart'
TILES=[
 (100,'1A | Sofa hook'),(258,'1B | X-ray count'),(335,'1C | Lifetime count'),
 (440,'2A | 9,000 litres'),(555,'2B | Vehicle fill'),(765,'2C | Ignition'),
 (857,'3A | Plasma speed'),(954,'3B | Speed chart'),(1030,'3C | Sofa debris'),
 (1145,'4A | Thrust'),(1252,'4B | Face warp'),(1360,'4C | Vascular cutaway'),
 (1504,'5A | Mach cones'),(1603,'5B | Roof impact'),(1870,'5C | Meteor ignition'),
 (2040,'6A | Rooftop OTS'),(2143,'6B | Prayer'),(2245,'6C | Wish payoff'),
 (2360,'7A | Unstamped'),(2485,'7B | Stamped'),(2620,'7C | Orbital CTA'),
]
def sheet(version):
 folder=OUT/f'cal_v{version}'
 progress=json.loads((folder/'progress.json').read_text())
 assert progress['status']=='complete',progress
 w,h=216,384
 dst=Image.new('RGB',(7*w,3*(h+22)),'#121b2b');d=ImageDraw.Draw(dst)
 for i,(f,label) in enumerate(TILES):
  img=Image.open(folder/f'{f:04d}.png').convert('RGB').resize((w,h),Image.Resampling.LANCZOS)
  x=(i%7)*w;y=(i//7)*(h+22)
  dst.paste(img,(x,y+22));d.text((x+5,y+4),f'f{f:04d} {label}',fill='#edf5f6')
 dst.save(OUT/('sheet_v4.jpg' if version==4 else 'sheet_v5_final.jpg'),quality=94)
def probe(p):
 return json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_type,width,height,r_frame_rate,nb_frames,duration','-of','json',str(p)]))
def mux(preview):
 folder=OUT/('preview_v4_chunks' if preview else 'master_chunks')
 job=json.loads((folder/'progress.json').read_text())
 assert job['status']=='complete',job
 listing=folder/'concat.txt'
 files=[Path(p) for p in job['files']]
 count=sum(int(probe(p)['streams'][0]['nb_frames']) for p in files)
 assert count==(1358 if preview else 2715),count
 listing.write_text(''.join(f"file '{p.as_posix()}'\n" for p in files))
 dest=OUT/('lifetime_fart_preview_v4.mp4' if preview else 'lifetime_fart_master_1080p.mp4')
 subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(OUT/'narration_source.mp3'),
 '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-af','apad','-t','90.5','-movflags','+faststart',str(dest)],check=True)
 print(probe(dest))
 if not preview:
  cuts=[1,226,306,385,475,637,721,811,901,1009,1087,1207,1297,1426,1585,1621,1705,1816,1975,2116,2176,2235,2287,2455,2533,2716]
  meta=OUT/'master_shots.json'
  meta.write_text(json.dumps({'shots':[{'id':i+1,'a':a-1,'b':b-1} for i,(a,b) in enumerate(zip(cuts,cuts[1:]))],
   'planned':[[1589,1594],[2454,2461]]},indent=2))
  subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(dest),str(OUT/'qa_master'),str(meta)],check=True)
  report=OUT/'qa_master/report.md'
  v=next(s for s in probe(dest)['streams'] if s['codec_type']=='video')
  assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_frames']))==(1080,1920,'30/1',2715)
  preview=json.loads((OUT/'preview_v4_chunks/progress.json').read_text())
  seconds=job.get('seconds',0)
  (OUT/'OVERRUN_MASTER_REPORT.md').write_text(
   "# Lifetime Fart production report\n\n"
   "## Delivery\n\n"
   "- Master `lifetime_fart_master_1080p.mp4` at 1080 × 1920, 30 fps, 2,715 frames and 90.5 seconds.\n"
   "- Editable source `output/blender/lifetime_fart_full.blend`. The pre-overhaul Blender project is backed up separately.\n"
   "- The supplied Hindi voiceover is 90.200813 seconds. The mux adds approximately 0.30 seconds of tail silence. Only HUD cards and diegetic documents appear as on-screen text.\n\n"
   "## Iteration 1\n\n"
   "- Rebuilt from the Part 1 and Part 2 Blender scripts. Retimed all scene groups from the supplied cue map. The sofa remains visible through frame 225. The Mach sequence precedes the roof impact and high-altitude reveal.\n"
   "- Added the detailed highway vehicles and fill, 20 sofa debris pieces, terracotta roof pieces, layered meteor, Earth surface and exterior palettes.\n"
   f"- Reviewed the old preview and `sheet_v3.jpg`, the 21-tile `sheet_v4.jpg` and moving samples from the 270 × 480 v4 preview. The v4 preview rendered in {preview.get('seconds',0):.1f} seconds.\n\n"
   "## Iteration 2\n\n"
   "- Corrected HUD cropping and face clearance, sofa posture and anchor, highway sky occlusion, paper contrast, and the flat meteor artwork. Checked additional frames for the sofa return, altitude reveal and stamp impact.\n"
   "- Checked the paper shader at frames 2454 and 2455. The unstamped page switches to the stamped texture at impact. The neighbor’s speaking mouth follows the measured narration envelope during the two dialogue windows.\n"
   "- Reviewed `sheet_v5_final.jpg` and used the saved calibrated scene for the master.\n"
   f"- Blender 4.2 EEVEE Next rendered the full timeline at 24 samples in about {seconds/60:.1f} minutes. Ray tracing stayed off and Simplify stayed on. Windows denied access to the standalone Store executable, so the active Blender session rendered ten sequential chunks for a lossless video join.\n\n"
   "## Export diagnostics\n\n"
   "The automated frame report below covers the muxed master. Visual quality was reviewed through calibration images and sampled motion. The supplied cue sheet governed word timing.\n\n"
   +report.read_text(encoding='utf8'),encoding='utf8')
if __name__=='__main__':
 arg=sys.argv[1]
 if arg in ('4','5'):sheet(int(arg))
 else:mux(arg=='preview')

