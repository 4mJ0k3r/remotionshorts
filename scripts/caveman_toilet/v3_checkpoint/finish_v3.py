"""CPU-only sheet assembly, HUD overlay, encode and metadata for V3."""
import json
import ast
import re
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from hud_overlay import draw_pill
from v2_story import CUTS, hud_for_frame

OUT=Path(__file__).resolve().parents[2]/'renders'/'caveman_toilet'

def sheet(tag='v3'):
    tree=ast.parse((Path(__file__).parent/'v3_physics.py').read_text())
    frames=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='SHEET_FRAMES' for t in n.targets))
    files=[OUT/f'calibration_{tag}'/f'tile_{i:02d}_f{f:04d}.png' for i,f in enumerate(frames)]
    w,h=270,480
    sheet=Image.new('RGB',(4*w,((len(files)+3)//4)*(h+24)),(16,16,20))
    draw=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',13)
    for i,p in enumerate(files):
        f=int(re.search(r'f(\d+)',p.stem)[1])
        im=Image.open(p).convert('RGB')
        draw_pill(im,hud_for_frame(f))
        im.resize((w,h),Image.Resampling.LANCZOS)
        x,y=(i%4)*w,(i//4)*(h+24)
        sheet.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,y))
        c=next((c for c in CUTS if c[1]<=f<c[2]),CUTS[-1])
        draw.text((x+6,y+h+4),f'f{f:04d} | cut {c[0]:02d} | V3 12 samples',font=font,fill='white')
    dest=OUT/'sheet_v3.jpg'
    sheet.save(dest,quality=94)
    print(dest,flush=True)

def encode():
    src=OUT/'frames_v3_fast'
    dst=OUT/'frames_v3_fast_hud'
    dst.mkdir(exist_ok=True)
    files=sorted(src.glob('f*.png'))
    if len(files)!=1620:
        raise RuntimeError(f'Expected 1620 frames, found {len(files)}')
    for i,p in enumerate(files,1):
        target_frame=dst/p.name
        if target_frame.exists() and target_frame.stat().st_mtime>=p.stat().st_mtime:
            continue
        im=Image.open(p).convert('RGB')
        draw_pill(im,hud_for_frame(i))
        im.save(target_frame)
    target=OUT/'caveman_toilet_v3_master.mp4'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','warning',
        '-framerate','30','-start_number','1','-i',str(dst/'f%04d.png'),
        '-i',str(OUT/'narration.mp3'),'-af','apad',
        '-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p',
        '-c:a','aac','-b:a','192k','-t','54','-movflags','+faststart',str(target)],check=True)
    print(target,flush=True)

if __name__=='__main__':
    sheet(sys.argv[2] if len(sys.argv)>2 else 'v3') if sys.argv[1]=='sheet' else encode()
