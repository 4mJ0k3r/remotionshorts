"""CPU-only V4 16-tile sheet, HUD, exact-duration narration mux."""
import ast
import json
import re
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from hud_overlay import draw_pill
from v2_story import hud_for_frame,cut_at

OUT=Path(__file__).resolve().parents[2]/'renders'/'caveman_toilet'


def sheet(tag='v4'):
    tree=ast.parse((Path(__file__).parent/'v4_overhaul.py').read_text())
    frames=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id=='SHEET_FRAMES' for t in n.targets))
    files=[OUT/f'calibration_{tag}'/f'tile_{i:02d}_f{f:04d}.png' for i,f in enumerate(frames)]
    w,h=270,480
    canvas=Image.new('RGB',(w*4,(h+24)*4),(16,16,20))
    d=ImageDraw.Draw(canvas);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',13)
    for i,(f,p) in enumerate(zip(frames,files)):
        im=Image.open(p).convert('RGB');draw_pill(im,hud_for_frame(f))
        x,y=i%4*w,i//4*(h+24)
        canvas.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,y))
        d.text((x+5,y+h+4),f'V4 | f{f:04d} | cut {cut_at(f)[0]:02d} | 12 samples',font=font,fill='white')
    dest=OUT/'sheet_v4.jpg';canvas.save(dest,quality=94);print(dest,flush=True)


def encode():
    src=OUT/'frames_v4_fast';dst=OUT/'frames_v4_fast_hud';dst.mkdir(exist_ok=True)
    files=sorted(src.glob('f*.png'))
    if len(files)!=1620:raise RuntimeError(f'Expected 1620 frames, got {len(files)}')
    for i,p in enumerate(files,1):
        target=dst/p.name
        if target.exists() and target.stat().st_mtime>=p.stat().st_mtime:continue
        im=Image.open(p).convert('RGB');draw_pill(im,hud_for_frame(i));im.save(target)
    target=OUT/'caveman_toilet_v4_master.mp4'
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','warning','-framerate','30','-start_number','1',
        '-i',str(dst/'f%04d.png'),'-i',str(OUT/'narration.mp3'),'-af','apad','-c:v','libx264','-crf','18',
        '-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','54','-movflags','+faststart',str(target)],check=True)
    print(target,flush=True)

if __name__=='__main__':
    import sys
    sheet(sys.argv[2] if len(sys.argv)>2 else 'v4') if sys.argv[1]=='sheet' else encode()
