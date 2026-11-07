# Tile calibration stills into one labelled sheet: python scripts/coaster_sheet.py <prefix> <f,f,...> <out.jpg> [cols]
import sys
from PIL import Image, ImageDraw
prefix, frames, out = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], sys.argv[3]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
ims = [Image.open(f"{prefix}{f}.jpg") for f in frames]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (w * cols, h * rows), "black")
d = ImageDraw.Draw(S)
for i, (f, im) in enumerate(zip(frames, ims)):
    x, y = (i % cols) * w, (i // cols) * h
    S.paste(im, (x, y))
    d.rectangle([x, y, x + 70, y + 22], fill="black"); d.text((x + 6, y + 5), f"f{f}", fill="yellow")
S.save(out, quality=90)
print(out, S.size)
