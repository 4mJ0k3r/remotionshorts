# Tile every jpg in a folder into one labelled contact sheet, sorted by the frame number in the filename.
# ffmpeg's image2 muxer pads with -frame_pts, so renaming by hand is how the last batch got clobbered; this reads
# the names as they are. Usage: python scripts/dir_sheet.py <dir> <out.jpg> [cols]
import os
import re
import sys
from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 5
names = sorted((n for n in os.listdir(d) if n.endswith(".jpg")),
               key=lambda n: int(re.sub(r"\D", "", n) or 0))
ims = [(int(re.sub(r"\D", "", n) or 0), Image.open(os.path.join(d, n))) for n in names]
w, h = ims[0][1].size
rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (w * cols, h * rows), "black")
dr = ImageDraw.Draw(S)
for i, (f, im) in enumerate(ims):
    x, y = (i % cols) * w, (i // cols) * h
    S.paste(im.resize((w, h)), (x, y))
    dr.rectangle([x, y, x + 70, y + 22], fill="black")
    dr.text((x + 6, y + 5), f"f{f}", fill="yellow")
S.save(out, quality=90)
print(out, S.size, len(ims), "frames")
