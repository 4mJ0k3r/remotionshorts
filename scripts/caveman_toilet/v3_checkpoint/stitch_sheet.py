"""Stitch the 16 v2 calibration tiles into sheet_v2.jpg (4 cols x 4 rows).

System python (has PIL). Reads renders/caveman_toilet/calibration_<tag>/
tile_XX_fYYYY.png, burns a frame/cut label under each tile, footer in its own
band, writes renders/caveman_toilet/sheet_<tag>.jpg.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "caveman_toilet"

# (frame, cut#, act, short label) in tile order — mirrors v2 SHEET_FRAMES
TILES = [
    (40, 1, 1, "confused hook"), (230, 3, 1, "real walk cycle"),
    (330, 4, 1, "cramp clutch"), (382, 5, 1, "squat descent"),
    (415, 5, 1, "relief + plume"), (480, 6, 1, "trio walk"),
    (620, 8, 2, "campfire huddle"), (700, 9, 2, "lion panic"),
    (800, 10, 2, "corner sneak-squat"), (850, 11, 3, "elder nausea CU"),
    (950, 12, 3, "toxic corner"), (1180, 14, 3, "collapse + souls"),
    (1250, 15, 4, "eureka bulb"), (1330, 16, 4, "point outside"),
    (1452, 17, 4, "dig trench + clods"), (1560, 18, 4, "sunset latrine"),
]
COLS, ROWS = 4, 4
LABEL_H = 34
FOOT_H = 44


def font(sz):
    for name in ("arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            pass
    return ImageFont.load_default()


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "v2"
    cal = OUT / (sys.argv[2] if len(sys.argv) > 2 else f"calibration_{tag}")
    files = sorted(cal.glob("tile_*.png"))
    if len(files) < 16:
        print(f"only {len(files)} tiles found in {cal}; need 16", flush=True)
        return 1
    tiles = [Image.open(f).convert("RGB") for f in files[:16]]
    tw, th = tiles[0].size
    sheet_w = COLS * tw
    sheet_h = ROWS * (th + LABEL_H) + FOOT_H
    sheet = Image.new("RGB", (sheet_w, sheet_h), (16, 16, 20))
    d = ImageDraw.Draw(sheet)
    f_lab = font(20)
    f_title = font(26)
    for i, im in enumerate(tiles):
        c, r = i % COLS, i // COLS
        x, y = c * tw, r * (th + LABEL_H)
        sheet.paste(im, (x, y))
        fr, cut, act, desc = TILES[i]
        lab = f"f{fr:04d}  cut{cut:02d} A{act}  {desc}"
        d.rectangle([x, y + th, x + tw, y + th + LABEL_H], fill=(16, 16, 20))
        d.text((x + 8, y + th + 6), lab, font=f_lab, fill=(235, 225, 200))
    d.text((10, sheet_h - 34),
           f"caveman_toilet  sheet_{tag}  {tw}x{th} @16 samples  EEVEE Next  v2 studio",
           font=f_title, fill=(212, 163, 89))
    dst = OUT / f"sheet_{tag}.jpg"
    sheet.save(dst, quality=92)
    print(f"saved {dst}  {sheet_w}x{sheet_h}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())