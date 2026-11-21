"""Screen-space HUD pill overlay for caveman_toilet v2 (PIL, exact colors).

Top 7% band: dark navy #0d1826 pill, 2 px gold #d4a359 border, bold white
uppercase text (Arial Bold). One pill across all 17 cuts, text keyed to frame.

Usage: python hud_overlay.py <src_dir> <dst_dir> [--pattern GLOB]
Reads PNGs named *f<NNNN>*.png, writes overlaid PNGs to dst_dir.
"""
import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from v2_story import hud_for_frame

NAVY = (13, 24, 38)        # #0d1826
GOLD = (212, 163, 89)      # #d4a359
WHITE = (255, 255, 255)
FONT = "C:/Windows/Fonts/arialbd.ttf"


def draw_pill(img, text):
    w, h = img.size
    d = ImageDraw.Draw(img)
    band = int(h * 0.07)
    pw, ph = int(w * 0.92), int(band * 0.78)
    x0 = (w - pw) // 2
    y0 = int(band * 0.12)
    r = ph // 2
    d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=r,
                        fill=NAVY, outline=GOLD, width=max(1,round(w/270)))
    size = int(ph * 0.52)
    while size > 3:
        font = ImageFont.truetype(FONT, size)
        tw = d.textlength(text, font=font)
        if tw <= pw - max(8,28*w/540):
            break
        size -= 1
    font = ImageFont.truetype(FONT, size)
    tw = d.textlength(text, font=font)
    tx = x0 + (pw - tw) / 2
    ty = y0 + (ph - size) / 2 - size * 0.12
    d.text((tx, ty), text, font=font, fill=WHITE)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--pattern", default="*.png")
    a = ap.parse_args()
    src, dst = Path(a.src), Path(a.dst)
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob(a.pattern))
    if not files:
        print(f"no PNGs in {src}")
        return 1
    for p in files:
        m = re.search(r"f(\d{4})", p.name)
        if not m:
            print(f"skip (no frame id): {p.name}")
            continue
        f = int(m.group(1))
        img = Image.open(p).convert("RGB")
        draw_pill(img, hud_for_frame(f))
        img.save(dst / p.name)
    print(f"HUD overlay: {len(files)} frames -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
