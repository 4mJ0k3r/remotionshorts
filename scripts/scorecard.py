# Quantitative look scorecard: same metrics as references/reports/grade.md + outlines.md.
# usage: python scripts/scorecard.py <ours-glob-dir> <ref-dir> [out.csv]
import sys, os, glob, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

OURS_DIR, REF_DIR = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else "out/bridge/scorecard.csv"
SET = os.environ.get("SCORECARD_SET", "bridge")  # bridge: caption band masked, frames keyed to the bridge cut; pardon: no caption
CAP = None if SET == "pardon" else (650, 706)  # caption band in the 540x960 grid, masked for both sets (report method)

def measure(path):
    im = np.asarray(Image.open(path).convert("RGB"), np.float32) / 255.0
    H, W, _ = im.shape
    vr = np.ones((H, W), bool)
    if CAP: vr[CAP[0]:CAP[1]] = False
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Ym = Y[vr]
    # HSV saturation with H max, V > 0.15 (grade.md definition)
    mx = im.max(-1); mn = im.min(-1)
    S = np.where(mx > 0.15, np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0), np.nan)
    # ink mask: 7x7 grey closing top-hat > 0.12 AND Y < 0.30
    th = ndi.grey_closing(Y, size=(7, 7)) - Y
    ink = (th > 0.12) & (Y < 0.30) & vr
    inkd = ndi.binary_dilation(ink, iterations=2)
    # strong edges: Sobel gradient magnitude, top 10 % of valid pixels
    gy = ndi.sobel(Y, 0); gx = ndi.sobel(Y, 1)
    grad = np.hypot(gx, gy)
    t = np.percentile(grad[vr], 90)
    strong = (grad > t) & vr
    edge_ink = (strong & inkd).sum() / max(1, strong.sum())
    # black/white point: mean RGB of darkest/brightest 0.5 % of non-ink pixels
    nz = int(0.005 * Ym.size)
    nb = Ym[~ink[vr]] if (~ink[vr]).any() else Ym
    order = np.argsort(nb)
    idx = np.argwhere(vr)
    allpx = im[vr]; allY = Ym
    o = np.argsort(allY)
    black = allpx[o[:max(1, nz)]].mean(0) * 255
    white = allpx[o[-max(1, nz):]].mean(0) * 255
    return dict(lum_mean=float(Ym.mean()), lum_std=float(Ym.std()), p2=float(np.percentile(Ym, 2)),
                p50=float(np.percentile(Ym, 50)), p98=float(np.percentile(Ym, 98)), p99=float(np.percentile(Ym, 99)),
                sat_mean=float(np.nanmean(S)), sat_p90=float(np.nanpercentile(S, 90)),
                ink=float(ink.sum() / vr.sum()), edge_ink=float(edge_ink),
                black=",".join(f"{v:.0f}" for v in black), white=",".join(f"{v:.0f}" for v in white))

ours = sorted(glob.glob(os.path.join(OURS_DIR, "shot_*.jpg")), key=lambda p: int(os.path.basename(p)[5:-4]))
refs = sorted(glob.glob(os.path.join(REF_DIR, "*.jpg")))
rows = []
for p in ours + refs:
    m = measure(p); m["file"] = os.path.basename(p)
    m["set"] = "ours" if p in ours else "ref"
    rows.append(m)

def agg(sub):
    keys = ["lum_mean", "lum_std", "p2", "p50", "p98", "p99", "sat_mean", "sat_p90", "ink", "edge_ink"]
    return {k: float(np.median([r[k] for r in sub])) if sub else float("nan") for k in keys}

PARDON_DAY = (45, 145, 250)
PARDON_GOLD = (355, 460, 560)
day = [r for r in rows if r["set"] == "ours" and ((int(r["file"][5:-4]) in PARDON_DAY) if SET == "pardon"
       else int(r["file"][5:-4]) <= 1250 or int(r["file"][5:-4]) in (1810, 1900, 2010))]
gold = [r for r in rows if r["set"] == "ours" and ((int(r["file"][5:-4]) in PARDON_GOLD) if SET == "pardon"
       else 1303 <= int(r["file"][5:-4]) < 1735)]
refall = [r for r in rows if r["set"] == "ref"]
A = {"ours_day": agg(day), "ours_golden": agg(gold), "ref_all_mixed": agg(refall),
     "ref_day_target": dict(lum_mean=0.558, lum_std=0.202, p2=0.02, p50=0.571, p98=0.93, p99=0.967, sat_mean=0.439, sat_p90=0.737, ink=0.026, edge_ink=0.451),
     "ref_golden_target": dict(lum_mean=0.508, lum_std=0.182, p2=0.05, p50=0.516, p98=0.90, p99=0.912, sat_mean=0.459, sat_p90=0.671, ink=0.019, edge_ink=0.451)}

with open(OUT, "w", newline="") as f:
    import csv
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("wrote", OUT, "| ours:", len(ours), "refs:", len(refs))
keys = ["lum_mean", "lum_std", "p2", "p50", "p98", "p99", "sat_mean", "sat_p90", "ink", "edge_ink"]
hdr = ["metric", "ours_day", "ref_day_target", "ours_golden", "ref_golden_target"]
print(" | ".join(hdr))
for k in keys:
    print(" | ".join([k] + [f"{A[c][k]:.3f}" for c in ["ours_day", "ref_day_target", "ours_golden", "ref_golden_target"]]))
print("ref frames (38, mixed lighting) medians:", json.dumps({k: round(A["ref_all_mixed"][k], 3) for k in keys}))
print("\nPER FRAME (ours):")
for r in rows:
    if r["set"] == "ours":
        print(f"{r['file']}: mean {r['lum_mean']:.3f} std {r['lum_std']:.3f} p2 {r['p2']:.3f} p98 {r['p98']:.3f} sat {r['sat_mean']:.3f} ink {r['ink']*100:.2f}% edgeInk {r['edge_ink']*100:.1f}% black({r['black']}) white({r['white']})")
