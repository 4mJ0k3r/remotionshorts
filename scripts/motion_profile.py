# Camera motion profile of a rendered short, same classes as references/reports/motion.md:
#   per-frame similarity fit (translation + zoom + roll) on 3 height bands x 3 tiles, caption band excluded,
#   speed = translation + zoom x 734 px (720x1280 units), holds < 0.3 px/f, drift < 2, move >= 2.
# Usage: python scripts/motion_profile.py <video.mp4> [out.json]
import json, sys
import cv2
import numpy as np

vid = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else None
cap = cv2.VideoCapture(vid)
W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
FPS = cap.get(cv2.CAP_PROP_FPS) or 30.0
CONV = 720.0 / W  # measured px -> 720x1280 reference px
BANDS = [(0.03, 0.29), (0.29, 0.56), (0.80, 0.97)]  # 3-29 %, 29-56 %, 80-97 % of height (bottom caption band out)
SPEED = []; ROLL = []; ZOOM = []; DX = []; DY = []
prev = None
lk = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
while True:
    ok, fr = cap.read()
    if not ok: break
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    if prev is not None:
        tx, ty, sc, rot, n = [], [], [], [], 0
        for (y0, y1) in BANDS:
            for k in range(3):
                x0, x1 = int(W * k / 3), int(W * (k + 1) / 3)
                a = prev[int(H * y0):int(H * y1), x0:x1]
                b = g[int(H * y0):int(H * y1), x0:x1]
                pts = cv2.goodFeaturesToTrack(a, 120, 0.01, 6)
                if pts is None or len(pts) < 8: continue
                q, st, _ = cv2.calcOpticalFlowPyrLK(a, b, pts, None, **lk)
                good = st.ravel() == 1
                if good.sum() < 8: continue
                M, _ = cv2.estimateAffinePartial2D(pts[good], q[good], method=cv2.RANSAC, ransacReprojThreshold=2.0)
                if M is None: continue
                tx.append(M[0, 2]); ty.append(M[1, 2]); sc.append(np.hypot(M[0, 0], M[1, 0])); rot.append(np.degrees(np.arctan2(M[1, 0], M[0, 0]))); n += 1
        if n:
            mx, my, ms, mr = np.median(tx), np.median(ty), np.median(sc), np.median(rot)
        else:
            mx = my = mr = 0.0; ms = 1.0
        tr = np.hypot(mx, my) * CONV
        zm = abs(ms - 1.0) * 734.0  # frame-corner radius at 720x1280
        SPEED.append(float(tr + zm)); DX.append(float(mx * CONV)); DY.append(float(my * CONV))
        ZOOM.append(float((ms - 1.0) * 100.0)); ROLL.append(float(mr))
    prev = g
cap.release()
S = np.array(SPEED); n = len(S)
if n == 0: raise SystemExit("no frames read: " + vid)
# hard cuts read as huge one-frame jumps: mask them and their neighbours
for i in np.where(S > 200)[0]:
    S[max(0, i - 1):i + 2] = np.nan
    ZOOM = np.array(ZOOM); ROLL = np.array(ROLL); DX = np.array(DX); DY = np.array(DY)
    ZOOM[max(0, i - 1):i + 2] = np.nan; ROLL[max(0, i - 1):i + 2] = np.nan; DX[max(0, i - 1):i + 2] = np.nan; DY[max(0, i - 1):i + 2] = np.nan
ok = ~np.isnan(S)
S = S[ok]; ZOOM = np.array(ZOOM)[ok]; ROLL = np.array(ROLL)[ok]; DX = np.array(DX)[ok]; DY = np.array(DY)[ok]
n = len(S)
q = np.percentile
hold = float((S < 0.3).mean() * 100); drift = float(((S >= 0.3) & (S < 2)).mean() * 100); move = float((S >= 2).mean() * 100)
# bursts: local peaks >= 6 px/f, attack/release to 10 % of peak
bursts = []
for i in range(1, n - 1):
    if S[i] >= 6 and S[i] >= S[i - 1] and S[i] > S[i + 1]:
        lo = S[i] * 0.1
        a = i
        while a > 0 and S[a - 1] > lo: a -= 1
        b = i
        while b < n - 1 and S[b + 1] > lo: b += 1
        if not bursts or i - bursts[-1]["peak"] > 4:
            bursts.append({"peak": i, "v": float(S[i]), "attack": i - a, "release": b - i})
Z = np.array(ZOOM); quiet = S < 2
res = {"video": vid, "size": [W, H], "fps": FPS, "frames": n,
  "hold_pct": hold, "drift_pct": drift, "move_pct": move,
  "median_speed": float(np.median(S)), "p90_speed": float(q(S, 90)), "max_speed": float(S.max()),
  "zoom_rate_quiet_median_pct": float(np.median(np.abs(Z[quiet]))) if quiet.any() else 0.0,
  "zoom_in_share_pct": float((Z[quiet] > 0.05).mean() * 100) if quiet.any() else 0.0,
  "roll_abs_median_deg": float(np.median(np.abs(ROLL))),
  "bursts": bursts[:80],
  "moves_per_10s": float(sum(1 for b in bursts if b["v"] >= 2) * 10.0 / (n / FPS)),
  "attack_median": float(np.median([b["attack"] for b in bursts])) if bursts else 0,
  "release_median": float(np.median([b["release"] for b in bursts])) if bursts else 0}
print(json.dumps({k: v for k, v in res.items() if k != "speed"}, indent=1));
if out:
    json.dump(res, open(out, "w"), indent=1)
    np.savez(out.replace(".json", ".npz"), speed=S, dx=np.array(DX), dy=np.array(DY), zoom=Z, roll=np.array(ROLL))
