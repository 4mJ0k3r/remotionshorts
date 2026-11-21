"""Pair the original v01 renders with matched v02 look-development stills."""
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


BASE = Path(__file__).resolve().parents[3] / "renders/pigeon_inspector"
SHOTS = ((1,"Opening commuter","01_opening_commuter"),
         (105,"Ticket beneath the bench","02_under_bench"),
         (147,"Pigeon pins the ticket","03_pigeon_pin"))


def compare(candidate):
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")
    font = ImageFont.truetype(str(font_path),23) if font_path.is_file() else ImageFont.load_default(size=23)
    out = BASE/"v02"
    for frame, title, filename in SHOTS:
        sheet = Image.new("RGB",(1092,1008),"#161C26")
        draw = ImageDraw.Draw(sheet)
        filename_in = f"frame_{frame:04d}.png"
        for x, label, folder in ((0,"v01",BASE/"v01/frames"),(552,"v02",out/candidate)):
            with Image.open(folder/filename_in) as img:
                if img.size!=(540,960):
                    raise ValueError(f"Expected 540 × 960 in {folder/filename_in}.")
                sheet.paste(img.convert("RGB"),(x,48))
            draw.text((x+16,9),f"{label}  ·  {title}  ·  {(frame-1)/30:.3f} s",font=font,fill="#E8E8E0")
        sheet.save(out/(filename+".png"))


if __name__=="__main__":
    compare(sys.argv[1] if len(sys.argv)>1 else "stills")
