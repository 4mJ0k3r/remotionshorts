"""Assemble native visual proofs and the exact ungraded edge-test images."""
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parents[3]/"renders/pokhran_1998_cia/v01"
report=json.loads((OUT/"benchmark.json").read_text())
source=OUT/report["native_stills_dir"]
pure=OUT/"calibration_frames";pure.mkdir(exist_ok=True)
HOOK=[(1,"CIA opening"),(89,"Rajasthan hologram"),(143,"Spy satellite"),(190,"Red scan"),
      (284,"Desert cross-section"),(329,"Five test markers"),(405,"Boss sips coffee"),(452,"Still payoff")]
for old in pure.glob("frame_0393.png"):
    old.unlink()
for n,_ in HOOK:
    path=source/f"frame_{n:04d}.png"
    shutil.copyfile(path,pure/path.name)

def sheet(filename,title,directory,frames):
    w,h=330,587
    canvas=Image.new("RGB",(1398,93+((len(frames)+3)//4)*650),"#1c1727")
    draw=ImageDraw.Draw(canvas)
    heading=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",37)
    label=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",20)
    draw.text((22,18),title,fill="#fce9d5",font=heading)
    for i,(n,caption) in enumerate(frames):
        x,y=21+i%4*345,84+i//4*650
        with Image.open(directory/f"frame_{n:04d}.png") as im:
            canvas.paste(im.convert("RGB").resize((w,h),Image.Resampling.LANCZOS),(x,y))
        draw.text((x,y+h+12),f"f{n:03}  {caption}",fill="#f9c69e",font=label)
    canvas.save(OUT/filename)

sheet("original_cast_lookdev.png","Original studio cast  /  Pokhran-II",OUT/"cast_stills",
      [(501,"Dr. A.P.J. Abdul Kalam"),(502,"58th Regiment engineer"),(503,"CIA boss"),(504,"Halftone and thumb mitten")])
sheet("part1_hook_calibration.png","Pokhran-II  /  Part 1 hook",pure,HOOK)
