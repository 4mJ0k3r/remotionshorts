"""CPU-only HD HUD, high quality encode and exact Hindi-audio duration."""
from pathlib import Path
import subprocess
from PIL import Image
from hud_overlay import draw_pill
from v2_story import hud_for_frame
OUT=Path(__file__).resolve().parents[2]/'renders'/'caveman_toilet'
src=OUT/'frames_v4_1080p';dst=OUT/'frames_v4_1080p_hud';dst.mkdir(exist_ok=True)
for f in range(1,1621):
    p=src/f'f{f:04d}.png';q=dst/p.name
    if not p.exists():raise RuntimeError(f'Missing frame {f}')
    if q.exists() and q.stat().st_mtime>=p.stat().st_mtime:continue
    im=Image.open(p).convert('RGB')
    if im.size!=(1080,1920):raise RuntimeError(f'Wrong HD dimensions: {p}')
    draw_pill(im,hud_for_frame(f));im.save(q,compress_level=0)
    if f%120==0:print(f'HD HUD {f}/1620',flush=True)
target=OUT/'caveman_toilet_v4_1080p_master.mp4'
subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','warning','-framerate','30','-start_number','1',
    '-i',str(dst/'f%04d.png'),'-i',str(OUT/'narration.mp3'),'-af','apad','-c:v','libx264',
    '-crf','16','-preset','medium','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',
    '-t','54','-movflags','+faststart',str(target)],check=True)
print(target,flush=True)
