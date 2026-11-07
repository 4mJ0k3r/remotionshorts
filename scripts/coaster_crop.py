# Crop + enlarge one region of several stills side by side: python scripts/coaster_crop.py <prefix> <f,f,..> <x0,y0,x1,y1> <out.jpg> [zoom]
import sys
from PIL import Image, ImageDraw
prefix, frames, box, out = sys.argv[1], [int(x) for x in sys.argv[2].split(",")], [int(v) for v in sys.argv[3].split(",")], sys.argv[4]
zoom = float(sys.argv[5]) if len(sys.argv) > 5 else 2
w, h = int((box[2] - box[0]) * zoom), int((box[3] - box[1]) * zoom)
S = Image.new("RGB", (w * len(frames), h), "black"); d = ImageDraw.Draw(S)
for i, f in enumerate(frames):
    S.paste(Image.open(f"{prefix}{f}.jpg").crop(box).resize((w, h), Image.LANCZOS), (i * w, 0))
    d.rectangle([i * w, 0, i * w + 60, 20], fill="black"); d.text((i * w + 5, 4), f"f{f}", fill="yellow")
S.save(out, quality=92); print(out, S.size)
