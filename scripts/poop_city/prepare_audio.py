"""Measure the 29 dialogue beats inside the tightened master.

The master had dead air removed inside lines as well as between them, so raw
windows do not map contiguously. Each master speech block is matched back against
every raw segment window, then a monotonic alignment assigns blocks to segments
in dialogue order with every segment owning at least one block.
"""
import json
import sys
import wave
from pathlib import Path

import numpy as np
from scipy.signal import fftconvolve

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "poop_city"
FPS = 30
RATE = 16000
HOP = 160   # 10 ms
WIN = 320   # 20 ms
MIN_GAP_S = 0.15
MIN_BLOCK_S = 0.09
PAD_S = 0.30
KEEP_END_S = 75.35  # briefing: drop the duplicate take after this raw timestamp

SEGMENTS = [
    (1, 0.10, 2.95, "sperm", "अरे यार... आखिर पहुंच ही गया।", "gap 0.15"),
    (2, 3.35, 4.55, "sperm", "अंडा कहां है बे?", "gap 0.15"),
    (3, 5.10, 5.85, "potato", "अंडा?", "gap 0.12"),
    (4, 6.25, 8.35, "potato", "अबे रुक... ये क्या चीज़ है?", "gap 0.12"),
    (5, 8.80, 10.65, "swirl", "भैया ये तो स्पर्म है यार!", "sfx horror scream 0.90"),
    (6, 11.10, 13.75, "buff", "ठीक है भाई, बोल, क्या कर रहा है इधर?", "gap 0.12"),
    (7, 14.15, 16.05, "sperm", "मैं... अंडा ढूंढ रहा हूं।", "gap 0.10"),
    (8, 16.45, 17.25, "potato", "अंडा?", "gap 0.10"),
    (9, 17.55, 20.45, "swirl", "अबे साले, ये अंडा वाला इलाका नहीं है!", "gap 0.10"),
    (10, 20.85, 22.15, "sperm", "क्या? मतलब?", "sfx sitcom laugh 1.10"),
    (11, 22.55, 24.75, "sperm", "तेरा मैप सीधा जाने को बोल रहा था ना?", "gap 0.10"),
    (12, 25.10, 27.25, "buff", "हां, और तू सीधा ही निकल आया!", "gap 0.10"),
    (13, 27.50, 29.55, "potato", "सारे एग्जिट मिस कर दिए तूने!", "gap 0.10"),
    (14, 29.95, 32.85, "swirl", "जीपीएस ने ही चूना लगा दिया इसको!", "gap 0.12"),
    (15, 33.30, 35.40, "sperm", "तो भाई, मैं अभी कहां हूं?", "gap 0.10"),
    (16, 35.75, 38.25, "buff", "स्वागत है, टट्टी सिटी में!", "gap 0.10"),
    (17, 38.65, 40.25, "sperm", "टट्टी सिटी यार?!", "gap 0.10"),
    (18, 40.65, 42.35, "swirl", "यहां सिर्फ हम ही हैं।", "sfx red siren 1.00"),
    (19, 42.80, 45.85, "buff", "अब जब आ ही गया है, तो हमारे लिए काम करेगा।", "hard-hat clunk"),
    (20, 46.25, 48.05, "sperm", "अबे क्या बकवास कर रहा है?!", "gap 0.10"),
    (21, 48.45, 51.35, "swirl", "बधाई हो! अब तू वेस्ट मैनेजमेंट में है!", "sfx crowd cheer 0.85"),
    (22, 51.80, 54.65, "sperm", "मैंने पूरी ज़िंदगी ट्रेनिंग की थी बड़ा बनने के लिए...", "gap 0.10"),
    (23, 55.00, 58.25, "buff", "और अब तू गिनती करेगा कितनी टट्टी है!", "gap 0.10"),
    (24, 58.65, 60.35, "sperm", "ये सपना तो नहीं ना?", "gap 0.10"),
    (25, 60.75, 62.65, "buff", "लाइफ बहुत फास्ट आती है यार।", "gap 0.10"),
    (26, 63.00, 66.20, "swirl", "तेरे केस में, बहुत फास्ट तैर के आती है!", "sfx sitcom laugh 0.90"),
    (27, 66.60, 68.55, "sperm", "मुझे तो लाइफ बनानी थी...", "gap 0.10"),
    (28, 68.90, 70.65, "buff", "और तू हमें मिल गया!", "gap 0.10"),
    (29, 70.95, 75.35, "buff_all", "कल सुबह आठ बजे आ जाना! आठ बजे! हाहाहा!", "stop 75.35"),
]


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2, path
        r = w.getframerate()
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    return d.astype(np.float64) / 32768.0, r


def envelope(x):
    n = 1 + (len(x) - WIN) // HOP
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    return np.sqrt(np.mean(x[idx] ** 2, axis=1) + 1e-12)


def ncc_search(needle, hay):
    """Normalized cross-correlation, energy-gated and numerically stable."""
    L = len(needle)
    if L < 3 or len(hay) < L:
        return None, 0.0
    a = needle - needle.mean()
    an = np.linalg.norm(a)
    if an < 1e-9:
        return None, 0.0
    h = hay - hay.mean()
    cross = fftconvolve(h, a[::-1], mode="valid")
    cs = np.concatenate([[0.0], np.cumsum(h)])
    cs2 = np.concatenate([[0.0], np.cumsum(h * h)])
    m = len(cross)
    s1, s2 = cs[L:L + m] - cs[:m], cs2[L:L + m] - cs2[:m]
    var = np.maximum(s2 / L - (s1 / L) ** 2, 0.0)
    rms = np.sqrt(np.maximum(s2 / L, 0.0))
    den = np.sqrt(var * L) * an
    ncc = np.divide(cross, den, out=np.zeros_like(cross), where=den > 1e-12)
    # a near-silent hay window cannot own a voiced block
    ncc[rms < 0.30 * float(np.sqrt(np.mean(needle ** 2)))] = 0.0
    ncc = np.clip(ncc, -1.0, 1.0)
    i = int(np.argmax(ncc))
    return i, float(ncc[i])


def speech_blocks(env, thresh):
    voiced = env > thresh
    blocks, i, n = [], 0, len(voiced)
    while i < n:
        if not voiced[i]:
            i += 1
            continue
        j = i
        while j < n:
            if voiced[j]:
                j += 1
                continue
            k = j
            while k < n and not voiced[k]:
                k += 1
            if (k - j) * HOP / RATE < MIN_GAP_S and k < n:
                j = k
            else:
                break
        blocks.append((i * HOP / RATE, j * HOP / RATE))
        i = j
    return [(a, b) for a, b in blocks if b - a >= MIN_BLOCK_S]


def align(score):
    """Monotonic assignment: every segment owns >=1 block, order preserved."""
    B, S = score.shape
    NEG = -1e9
    dp = np.full((B, S), NEG)
    par = np.zeros((B, S), dtype=np.int8)
    dp[0, 0] = score[0, 0]
    for b in range(1, B):
        for s in range(S):
            if B - b < S - s:      # not enough blocks left to cover segments
                continue
            stay = dp[b - 1, s]
            adv = dp[b - 1, s - 1] if s > 0 else NEG
            if stay >= adv:
                dp[b, s], par[b, s] = stay + score[b, s], 0
            else:
                dp[b, s], par[b, s] = adv + score[b, s], 1
    if dp[B - 1, S - 1] <= NEG / 2:
        return None
    assign, s = [0] * B, S - 1
    for b in range(B - 1, -1, -1):
        assign[b] = s
        if b > 0 and par[b, s] == 1:
            s -= 1
    return assign


def main():
    raw, rate = read_wav(OUT / "_raw_ref.wav")
    tight, _ = read_wav(OUT / "_tight_ref.wav")
    assert rate == RATE
    raw_env, tight_env = envelope(raw), envelope(tight)
    total_s = len(tight) / RATE

    p95 = float(np.percentile(tight_env, 95))
    thresh = max(10 ** (-35 / 20), 0.10 * p95)
    blocks = speech_blocks(tight_env, thresh)
    S = len(SEGMENTS)
    print(f"master {total_s:.3f}s  frames@30 {total_s * FPS:.1f}  "
          f"thresh {thresh:.4f}  blocks {len(blocks)}  segments {S}")

    score = np.zeros((len(blocks), S))
    raw_at = np.zeros((len(blocks), S))
    for bi, (a, b) in enumerate(blocks):
        ne = tight_env[int(a * RATE / HOP):int(b * RATE / HOP)]
        for si, (_, rs, re_, *_rest) in enumerate(SEGMENTS):
            lo = max(0, int((rs - PAD_S) * RATE / HOP))
            hi = min(len(raw_env), int((re_ + PAD_S) * RATE / HOP))
            off, sc = ncc_search(ne, raw_env[lo:hi])
            score[bi, si] = sc
            raw_at[bi, si] = (lo + off) * HOP / RATE if off is not None else -1

    assign = align(score)
    if assign is None:
        print("ALIGNMENT FAILED")
        return 1

    print(f"\n{'blk':>3} {'start':>7} {'end':>7} {'dur':>5} -> {'seg':>3} "
          f"{'score':>6} {'raw@':>7}  (best other)")
    for bi, (a, b) in enumerate(blocks):
        s = assign[bi]
        order = np.argsort(score[bi])[::-1]
        other = f"seg{order[0] + 1}={score[bi, order[0]]:.3f}" if order[0] != s else "-"
        print(f"{bi:>3} {a:>7.3f} {b:>7.3f} {b - a:>5.2f} -> {s + 1:>3} "
              f"{score[bi, s]:>6.3f} {raw_at[bi, s]:>7.3f}  {other}")

    # The briefing mandates dropping the duplicate second take after raw 75.35 s.
    # Check every block against the whole raw file, not just its own window.
    dup = []
    for bi, (a, b) in enumerate(blocks):
        ne = tight_env[int(a * RATE / HOP):int(b * RATE / HOP)]
        off, sc = ncc_search(ne, raw_env)
        rt = off * HOP / RATE if off is not None else -1.0
        if rt > KEEP_END_S and sc > 0.90:
            dup.append(dict(block=bi, start_s=round(a, 4), end_s=round(b, 4),
                            raw_s=round(rt, 3), score=round(sc, 4)))
    trim_s = None
    if dup:
        kept = [bi for bi in range(len(blocks)) if bi not in {d["block"] for d in dup}]
        trim_s = round(blocks[max(kept)][1] + 0.20, 4)
        print(f"\nDUPLICATE TAKE PRESENT: {len(dup)} blocks "
              f"{dup[0]['start_s']:.3f}-{dup[-1]['end_s']:.3f}s "
              f"map to raw {dup[0]['raw_s']:.2f}-{dup[-1]['raw_s']:.2f}s "
              f"(> {KEEP_END_S}s cut point)")
        print(f"  suggested trim point {trim_s:.3f}s -> {int(round(trim_s * FPS))} frames")

    rows = []
    for si, (sid, rs, re_, spk, text, note) in enumerate(SEGMENTS):
        idxs = [bi for bi in range(len(blocks)) if assign[bi] == si]
        a = blocks[idxs[0]][0]
        b = blocks[idxs[-1]][1]
        rows.append(dict(id=sid, speaker=spk, text=text, note=note,
                         raw_start=rs, raw_end=re_, blocks=idxs,
                         start_s=round(a, 4), end_s=round(b, 4),
                         start_frame=int(round(a * FPS)), end_frame=int(round(b * FPS)),
                         match_score=round(float(min(score[bi, si] for bi in idxs)), 4)))

    print(f"\n{'seg':>3} {'spk':<9} {'score':>6} {'start':>7} {'end':>7} "
          f"{'f0':>5} {'f1':>5} {'dur':>5} {'gap':>5}")
    problems, prev = [], 0.0
    for r in rows:
        gap = r["start_s"] - prev
        if gap < -0.005:
            problems.append(f"seg{r['id']}: overlaps previous")
        if r["match_score"] < 0.90:
            problems.append(f"seg{r['id']}: weak match {r['match_score']}")
        prev = r["end_s"]
        print(f"{r['id']:>3} {r['speaker']:<9} {r['match_score']:>6.3f} "
              f"{r['start_s']:>7.3f} {r['end_s']:>7.3f} {r['start_frame']:>5} "
              f"{r['end_frame']:>5} {r['end_s'] - r['start_s']:>5.2f} {gap:>5.2f}")

    covered = sum(1 for r in rows if r["blocks"])
    scores = [r["match_score"] for r in rows]
    if dup:
        problems.append(f"duplicate take present: {len(dup)} blocks after {dup[0]['start_s']}s")
    print(f"\ncovered {covered}/{S}  min {min(scores):.3f}  "
          f"median {float(np.median(scores)):.3f}  "
          f"speech {sum(r['end_s'] - r['start_s'] for r in rows):.2f}s of {total_s:.2f}s")
    print("problems:", problems if problems else "none")

    payload = dict(
        source="tatti-city-dialogue-v2-tight.mp3",
        master="renders/poop_city/audio_master.wav",
        duration_s=round(total_s, 4), fps=FPS,
        total_frames=int(round(total_s * FPS)),
        method="master blocks matched to raw windows + monotonic alignment",
        block_thresh=round(thresh, 5), min_gap_s=MIN_GAP_S,
        complete=covered == S and not problems,
        min_score=round(min(scores), 4), problems=problems,
        duplicate_take_blocks=dup, suggested_trim_s=trim_s,
        suggested_trim_frames=int(round(trim_s * FPS)) if trim_s else None,
        segments=rows,
    )
    (OUT / "segments_timeline.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT / 'segments_timeline.json'}")
    return 0 if payload["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())