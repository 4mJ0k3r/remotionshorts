"""Assemble the 12 540x960 calibration frames into sheet_v1.jpg (4x3 grid) and report image stats."""

from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\remotionshorts\renders\bamboo_ambush")
CAL_DIR = ROOT / "calibration"
OUT_PATH = ROOT / "sheet_v1.jpg"
SHOTS_PATH = ROOT / "shots.json"
FRAMES = [45, 140, 240, 345, 430, 495, 560, 660, 735, 800, 860, 910]


def main():
    shot_by_peak = {}
    if SHOTS_PATH.exists():
        data = json.loads(SHOTS_PATH.read_text(encoding="utf-8"))
        for sh in data.get("shots", []):
            shot_by_peak[int(sh["peak"])] = sh

    tile_w, tile_h = 540, 960
    cols, rows = 4, 3
    sheet = Image.new("RGB", (cols * tile_w, rows * tile_h), (18, 18, 22))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    lumas = []
    for idx, f in enumerate(FRAMES):
        p = CAL_DIR / f"{f:04d}.png"
        if not p.exists():
            raise FileNotFoundError(f"Missing calibration frame: {p}")
        im = Image.open(p).convert("RGB")
        if im.size != (tile_w, tile_h):
            im = im.resize((tile_w, tile_h), Image.Resampling.LANCZOS)

        arr = np.asarray(im, dtype=np.float32)
        luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
        mean_l = float(np.mean(luma))
        std_l = float(np.std(luma))
        p2, p98 = np.percentile(luma, [2, 98])
        lumas.append(mean_l)

        # Horizontal energy gradient / subject saliency center-of-mass proxy
        gx = np.abs(np.diff(luma, axis=1, prepend=luma[:, :1]))
        col_energy = gx.mean(axis=0)
        xs = np.linspace(0.0, 1.0, tile_w)
        com_x = float(np.sum(col_energy * xs) / max(1e-6, np.sum(col_energy)))

        c = idx % cols
        r = idx // cols
        x0, y0 = c * tile_w, r * tile_h
        sheet.paste(im, (x0, y0))

        sh = shot_by_peak.get(f, {})
        tag = f"Cut {sh.get('shot', '?')} | f{f} ({f / 30.0:.2f}s) | Y={mean_l:.1f}"
        draw.rectangle([x0 + 6, y0 + 6, x0 + 380, y0 + 36], fill=(16, 16, 20))
        draw.text((x0 + 12, y0 + 10), tag, fill=(255, 245, 220), font=font)

        print(
            f"tile {idx+1:02d} Cut={sh.get('shot','?'):>2} f={f:04d} "
            f"mean={mean_l:5.1f} std={std_l:5.1f} p2={p2:4.1f} p98={p98:5.1f} edge_com_x={com_x:.2f}"
        )

    sheet.save(OUT_PATH, quality=92)
    print(f"Saved {OUT_PATH} ({sheet.size[0]}x{sheet.size[1]}), overall mean_luma={np.mean(lumas):.1f}")


if __name__ == "__main__":
    main()
