// Shot 20 occlusion gate: does any part of the avalanche stand BETWEEN the lens and a drawn figure?
//
// A 2D card is a billboard quad, so the only thing that can hide a body is 3D geometry closer to the lens along the
// view axis. The avalanche is one box plus 30-odd children, and build.ts hangs teeth and foot-debris several metres
// downstage of that box while the slab's lean swings the whole field toward the camera as well. At the old authored
// end position that put a 4 m drift ball at torso height 2.5 m IN FRONT of the hero card, and the film's central
// dramatic beat rendered as two pairs of legs and a cap under a white band.
//
// The layout below mirrors build.ts's buildSnow() avalanche loop (same hash, same offsets, same Euler order). If that
// loop changes, change this one; the numbers are short on purpose.
import * as S from "../src/videos/instant_skill/story.ts";

const SU = 0.00216;
const snowSlope = (z) => 1.34 * 0.052 * Math.pow(Math.max(0.001, z - (S.SNOW.landPad[2] + 0.6)), 0.34);
const hash = (i, k = 0) => { const s = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return s - Math.floor(s); };

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(...a) || 1; return a.map((v) => v / l); };
const m3 = (A, B) => [0, 1, 2].map((i) => [0, 1, 2].map((j) => A[i][0] * B[0][j] + A[i][1] * B[1][j] + A[i][2] * B[2][j]));
const ap = (M, v) => [dot(M[0], v), dot(M[1], v), dot(M[2], v)];
const ID = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
/** THREE's Euler order "ZXY" is the intrinsic product R = Rz * Rx * Ry */
const zxy = (x, y, z) => {
  const cx = Math.cos(x), sx = Math.sin(x), cy = Math.cos(y), sy = Math.sin(y), cz = Math.cos(z), sz = Math.sin(z);
  return m3(m3([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]),
    [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]);
};

const SN = S.SNOW;
const [aw, ah, ad] = SN.avalSize;
const Mp = zxy(Math.atan(snowSlope(SN.avalStartZ)), 0, 0.07);   // the slab's authored lean, set once in build.ts

const kids = [];
for (let i = 0; i < 11; i++) {
  const tw = (aw / 11) * (0.74 + hash(i, 2) * 0.5);
  const th = ah * (0.42 + hash(i, 5) * 0.5);
  const td = 0.8 + hash(i, 8) * 1.3;
  const tx = -aw / 2 + (i + 0.5) * (aw / 11);
  kids.push({ n: `tooth${i}`, kind: "box", c: [tx, -ah / 2 + th / 2, -ad / 2 - td * 0.36], h: [tw / 2, th / 2, td / 2],
    rot: [0, (hash(i, 15) - 0.5) * 0.12, (hash(i, 12) - 0.5) * 0.09] });
  kids.push({ n: `debris${i}`, kind: "ell", c: [tx + 1.2, -ah / 2 + 0.3, -ad / 2 - td - 0.3], h: [tw * 0.7, 0.42, td * 0.55] });
}
for (let i = 0; i < 7; i++) {
  kids.push({ n: `crown${i}`, kind: "ell", c: [-aw / 2 + (i + 0.5) * (aw / 7), ah / 2 - 0.2, -ad / 2 - 0.35], h: [aw / 7 * 0.72, 0.55, 1.15] });
}
kids.push({ n: "coping", kind: "box", c: [0, ah / 2 - 0.15, -ad / 2 - 0.2], h: [aw / 2, 0.15, 0.25] });

const segBox = (o, d, c, h, M) => {
  const Mi = [[M[0][0], M[1][0], M[2][0]], [M[0][1], M[1][1], M[2][1]], [M[0][2], M[1][2], M[2][2]]];
  const L = (v) => [dot(Mi[0], v), dot(Mi[1], v), dot(Mi[2], v)];
  const lo = L(sub(o, c)), ld = L(d);
  let t0 = 0, t1 = 1;
  for (let i = 0; i < 3; i++) {
    if (Math.abs(ld[i]) < 1e-9) { if (Math.abs(lo[i]) > h[i]) return null; continue; }
    let a = (-h[i] - lo[i]) / ld[i], b = (h[i] - lo[i]) / ld[i];
    if (a > b) [a, b] = [b, a];
    t0 = Math.max(t0, a); t1 = Math.min(t1, b);
    if (t0 > t1) return null;
  }
  return t0;
};
const segEll = (o, d, c, h) => {
  const q = (v) => [v[0] / h[0], v[1] / h[1], v[2] / h[2]];
  const lo = q(sub(o, c)), ld = q(d);
  const A = dot(ld, ld), B = 2 * dot(lo, ld), C = dot(lo, lo) - 1;
  const disc = B * B - 4 * A * C;
  if (disc <= 0) return null;
  const t = (-B - Math.sqrt(disc)) / (2 * A);
  return t > 0 && t < 1 ? t : null;
};

const shot = S.SHOTS[19];
const hits = [];
let minGap = 1e9, minAt = "";
for (let f = shot.a; f <= shot.b; f++) {
  const zc = S.avalPos(f)[2];
  const cam = S.camAt(20, f);
  const ks = kids.map((k) => ({
    ...k,
    cW: [SN.hero[0] + ap(Mp, k.c)[0], SN.avalY + ap(Mp, k.c)[1], zc + ap(Mp, k.c)[2]],
    Mw: m3(Mp, k.rot ? zxy(k.rot[0], k.rot[1], k.rot[2]) : ID),
  }));
  for (const who of ["hero", "friend"]) {
    const at = who === "hero" ? SN.hero : SN.friend;
    // the painted silhouette, crown to sole, on the card's own plane
    for (const [label, dy] of [["crown", 90], ["eye", 235], ["shoulder", 375], ["chest", 470], ["hip", 585], ["knee", 800], ["sole", 952]]) {
      const p = [at[0], at[1] + (975 - dy) * SU * S.ACTOR_SCALE, at[2]];
      const d = sub(p, cam.pos);
      let best = null;
      for (const k of ks) {
        const t = k.kind === "box" ? segBox(cam.pos, d, k.cW, k.h, k.Mw) : segEll(cam.pos, d, k.cW, k.h);
        if (t !== null && (!best || t < best.t)) best = { t, n: k.n };
      }
      if (best) hits.push(`f${f} ${who}.${label} hidden by ${best.n} at ${(best.t * 100).toFixed(0)}% of the ray`);
    }
  }
  // how much clear air is left between the nearest avalanche surface and the hero card plane
  const near = Math.min(...ks.flatMap((k) => {
    const pts = [];
    for (const sx of [-1, 1]) for (const sy of [-1, 1]) for (const sz of [-1, 1]) {
      pts.push(ap(k.Mw, [sx * k.h[0], sy * k.h[1], sz * k.h[2]])[2] + k.cW[2]);
    }
    return pts;
  }));
  const gap = near - SN.hero[2];
  if (gap < minGap) { minGap = gap; minAt = `f${f}`; }
}

console.log(`shot 20 ${shot.a}..${shot.b}: avalanche children ${kids.length}, ` +
  `wall z ${S.avalPos(shot.a)[2].toFixed(2)} -> ${S.avalPos(shot.b)[2].toFixed(2)}`);
console.log(`nearest child surface to the hero card plane: ${minGap.toFixed(2)} m (${minAt}) — needs >= 0.30 m behind it`);
if (hits.length) {
  console.log(`FAIL: ${hits.length} occlusions`);
  for (const h of hits.slice(0, 12)) console.log("  " + h);
  process.exit(1);
}
if (minGap < 0.30) {
  console.log(`FAIL: the debris field is only ${minGap.toFixed(2)} m upstage of the hero card`);
  process.exit(1);
}
console.log(`SUCCESS: nothing in the avalanche stands between the lens and either figure, on all ${shot.b - shot.a + 1} frames of shot 20`);
