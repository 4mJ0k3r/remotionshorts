"""Make labeled contact sheets from the rendered Blender frames."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

folder = Path(sys.argv[1])
frames = [int(f) for f in sys.argv[2:]] or [
    int(p.stem.split("_")[1]) for p in sorted(folder.glob("frame_*.png"))
]
columns = min(6, len(frames))
w, h, label = 180, 320, 21
sheet = Image.new("RGB",(columns*w,((len(frames)+columns-1)//columns)*(h+label)),"#202331")
draw = ImageDraw.Draw(sheet)
for i, frame in enumerate(frames):
    x, y = (i%columns)*w, (i//columns)*(h+label)
    with Image.open(folder/f"frame_{frame:04d}.png") as image:
        sheet.paste(image.resize((w,h),Image.Resampling.LANCZOS),(x,y))
    draw.text((x+7,y+h+3),f"f{frame:03d} | {(frame-1)/30:.3f} s",fill="#EEDFCC")
sheet.save(folder/"contact.jpg",quality=94)
