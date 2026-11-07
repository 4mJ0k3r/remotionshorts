// Framing gate for tower_qwen: projects named landmark points through the real camAt() keys and prints screen u/v
// percentages, so SKILL.md 4.3 (fov 44-50, every key subject inside 15..85%) is proven numerically BEFORE rendering.
//   node scripts/tq_frame.mjs                 all shots, every frame
//   node scripts/tq_frame.mjs 2 95,140,190    one shot at given frames
//   node scripts/tq_frame.mjs 1 0 all         one shot, all frames, list every point
import {
  camAt, SHOTS, BRIDGE, CAB, SET1, SET3, bus1At, jumpAt, leafTip, tiltDegAt, onLeaf, TOTAL, PUSH1_AT, PUSH1_END, PUSH3_AT,
} from "../src/videos/tower_qwen/story.ts";

const ASPECT = 1080 / 1920, SU = 0.00216, PIV = 975, SCALE = 0.85;
const LO = 0.15, HI = 0.85;
const CAP_HW = 152 * SU * SCALE;
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const norm = (v) => { const l = Math.hypot(...v); return [v[0] / l, v[1] / l, v[2] / l]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];

const proj = (cam, P) => {
  const f = norm(sub(cam.look, cam.pos)), r = norm(cross(f, [0, 1, 0])), u = cross(r, f);
  const w = sub(P, cam.pos), d = dot(w, f);
  const half = 2 * Math.tan((cam.fov * Math.PI) / 360);
  return { u: 0.5 + dot(w, r) / d / (half * ASPECT), v: 0.5 + dot(w, u) / d / half, d };
};
/** world point of a design-space (dx, dy) on a yaw billboard at pos, pushed `depth` m along char->camera (SKILL 3B) */
const cardPoint = (camPos, pos, dx, dy, depth = 0) => {
  const yaw = Math.atan2(camPos[0] - pos[0], camPos[2] - pos[2]);
  const lx = (dx - 300) * SU * SCALE, ly = (PIV - dy) * SU * SCALE;
  return [pos[0] + Math.cos(yaw) * lx + Math.sin(yaw) * depth, pos[1] + ly, pos[2] - Math.sin(yaw) * lx + Math.cos(yaw) * depth];
};
const headY = (p) => p[1] + (PIV - 235) * SU * SCALE;
const capY = (p) => p[1] + (PIV - 58) * SU * SCALE;

const busPts = (p, pitch, s = 1) => {
  const L = (BRIDGE.bus.len / 2) * s, T = BRIDGE.bus.tall * s, c = Math.cos(pitch), sn = Math.sin(pitch);
  const rot = (x, y) => add(p, [x * c - y * sn, x * sn + y * c, 0]);
  return { "bumper": rot(-L, 0.15 * s), "roofR": rot(L, T), "roofL": rot(-L, T), "nose": rot(L, 0.9 * s) };
};
const boxPts = (c, hx, hy, tag) => [[`${tag} L`, [c[0] - hx, c[1], c[2]]], [`${tag} R`, [c[0] + hx, c[1], c[2]]],
[`${tag} T`, [c[0], c[1] + hy, c[2]]], [`${tag} B`, [c[0], c[1] - hy, c[2]]]];

/** which point names are held to the band at this frame (the rest are scene furniture that may run off frame) */
const TIGHT = ["head", "cap top", "head R edge", "head L edge", "bus roofR", "bus roofL", "bus bumper", "bus nose"];
const WIDE = ["tower-1 top", "tower1 top", "tower-1 outer", "tower1 outer", "tower-1 base", "tower1 base",
  "sign L", "sign R", "sign mid", "leaf tip-1", "leaf tip1", "head", "cap top", "deck centre", "feet",
  "bus roofR", "bus roofL", "bus bumper", "bus nose"];
function required(id, f) {
  if (id === 1) return f <= PUSH1_AT ? [TIGHT, 0.20, 0.80]
    : f < PUSH1_END ? [TIGHT, LO, HI] : [WIDE, LO, HI];
  const set = id === 2
    ? ["head", "cap top", "head L", "head R", "sign L", "sign R", "sign T", "sign B",
      "fist start", "fist end", "fist start L", "fist end L", "hips", "box top"]
    : f <= PUSH3_AT
      ? ["bg tower top-1", "bg tower top1", "bg outer-1", "bg outer1", "bg base-1", "bg base1",
        "bg sign L", "bg sign R", "jump bus roofR", "jump bus roofL", "jump bus bumper", "jump bus nose", "head", "cap top"]
      : ["board L", "board R", "board top", "board bot", "head", "cap top", "head L", "head R", "cert L", "cert R",
        "bg tower top-1", "bg tower top1", "bg outer-1", "bg outer1", "jump bus roofR", "jump bus roofL", "land pt"];
  return [set, LO, HI];
}

function points(id, f) {
  const P = [];
  if (id === 1) {
    const w = SET1.watchman, cam = camAt(1, f);
    // the watchman is a yaw billboard, so his screen edges are the card's own left/right, not world +-x
    P.push(["head", cardPoint(cam.pos, w, 300, 235)], ["cap top", cardPoint(cam.pos, w, 300, 58)],
      ["head R edge", cardPoint(cam.pos, w, 452, 235)], ["head L edge", cardPoint(cam.pos, w, 148, 235)],
      ["feet", w]);
    for (const side of [-1, 1]) {
      P.push([`tower${side} top`, [side * BRIDGE.hinge, BRIDGE.towerH, 0]],
        [`tower${side} outer`, [side * (BRIDGE.hinge + BRIDGE.towerW / 2), BRIDGE.towerH * 0.55, BRIDGE.legZ]],
        [`tower${side} base`, [side * (BRIDGE.hinge + BRIDGE.towerW / 2), 0, BRIDGE.legZ]]);
      const t = leafTip(tiltDegAt(f), side);
      P.push([`leaf tip${side}`, [t[0], t[1], BRIDGE.roadW / 2]]);
    }
    P.push(["sign L", [-BRIDGE.signW / 2, BRIDGE.signY + BRIDGE.signH / 2, BRIDGE.signZ]],
      ["sign R", [BRIDGE.signW / 2, BRIDGE.signY + BRIDGE.signH / 2, BRIDGE.signZ]],
      ["sign mid", [0, BRIDGE.signY, BRIDGE.signZ]],
      ["deck centre", [0, BRIDGE.deckY, BRIDGE.roadW / 2]]);
    const b = bus1At(f);
    for (const [k, v] of Object.entries(busPts(b.p, b.pitch))) P.push([`bus ${k}`, v]);
  } else if (id === 2) {
    const d = CAB.driver, cam = camAt(2, f);
    P.push(["head", [d[0], headY(d), d[2]]], ["cap top", [d[0], capY(d), d[2]]],
      ["head L", [d[0] - CAP_HW, headY(d), d[2]]], ["head R", [d[0] + CAP_HW, headY(d), d[2]]],
      ["feet", d], ["hips", [d[0], d[1] + (PIV - 585) * SU * SCALE, d[2]]]);
    for (const [dx, dy, tag] of [[165, 580, "fist start"], [135, 580, "fist end"]]) {
      const k = cardPoint(cam.pos, d, dx, dy, -0.08);
      P.push([tag, k], [`${tag} L`, [k[0] - 0.055, k[1], k[2]]]);
    }
    P.push(...boxPts(CAB.sign, CAB.signW / 2, CAB.signH / 2, "sign"));
    P.push(["win L", [-CAB.winHalfW, CAB.winY1, CAB.winZ]], ["win R", [CAB.winHalfW, CAB.winY1, CAB.winZ]],
      ["dash top", [0, CAB.winY0, CAB.winZ]], ["box top", CAB.boxTop]);
    for (const side of [-1, 1]) {
      const t = leafTip(26, side);
      P.push([`bg tip${side}`, add(CAB.bg, mul([t[0], t[1], 0], CAB.bgScale))],
        [`bg top${side}`, add(CAB.bg, mul([side * (BRIDGE.hinge + 1.3), BRIDGE.towerH, 0], CAB.bgScale))]);
    }
  } else {
    const d = SET3.driver, g = SET3.bg, s = SET3.bgScale;
    P.push(["head", [d[0], headY(d), d[2]]], ["cap top", [d[0], capY(d), d[2]]],
      ["head L", [d[0] - CAP_HW, headY(d), d[2]]], ["head R", [d[0] + CAP_HW, headY(d), d[2]]],
      ["cert L", [d[0] - 208 * SU * SCALE, d[1] + (PIV - 476) * SU * SCALE, d[2]]],
      ["cert R", [d[0] + 208 * SU * SCALE, d[1] + (PIV - 476) * SU * SCALE, d[2]]],
      ["feet", d]);
    const e = SET3.easel;
    P.push(["board L", [e[0] - SET3.boardW / 2, SET3.boardY, e[2]]], ["board R", [e[0] + SET3.boardW / 2, SET3.boardY, e[2]]],
      ["board top", [e[0], SET3.boardY + SET3.boardH / 2, e[2]]], ["board bot", [e[0], SET3.boardY - SET3.boardH / 2, e[2]]]);
    for (const side of [-1, 1]) {
      P.push([`bg tower top${side}`, add(g, mul([side * BRIDGE.hinge, BRIDGE.towerH, 0], s))],
        [`bg outer${side}`, add(g, mul([side * (BRIDGE.hinge + BRIDGE.towerW / 2), BRIDGE.towerH * 0.6, 0], s))],
        [`bg base${side}`, add(g, mul([side * (BRIDGE.hinge + BRIDGE.towerW / 2), 0, 0], s))]);
      const t = leafTip(26, side);
      P.push([`bg tip${side}`, add(g, mul(t, s))]);
    }
    P.push(["bg sign L", add(g, mul([-BRIDGE.signW / 2, BRIDGE.signY, 0], s))],
      ["bg sign R", add(g, mul([BRIDGE.signW / 2, BRIDGE.signY, 0], s))]);
    const j = jumpAt(f);
    for (const [k, v] of Object.entries(busPts(add(g, mul(j.p, s)), j.pitch, s))) P.push([`jump bus ${k}`, v]);
    P.push(["land pt", add(g, mul(onLeaf(26, 1, SET3.landS).p, s))]);
  }
  return P;
}

const onlyShot = process.argv[2] && process.argv[2] !== "all" ? Number(process.argv[2]) : 0;
const framesArg = process.argv[3] === "all" ? null : process.argv[3];
const verbose = process.argv[4] === "all";
let bad = 0, checked = 0;
const worst = {};
for (const s of SHOTS) {
  if (onlyShot && s.id !== onlyShot) continue;
  const frames = framesArg ? framesArg.split(",").map(Number)
    : Array.from({ length: s.b - s.a }, (_, i) => s.a + i);
  console.log(`\n=== SHOT ${s.id} (${s.set}) f${s.a}-${s.b - 1} ===`);
  let reveal = null;
  for (const f of frames) {
    const cam = camAt(s.id, f);
    if (cam.fov < 44 || cam.fov > 50) { console.log(`FOV OUT f${f} ${cam.fov}`); bad++; }
    const [keep, lo, hi] = required(s.id, f);
    const pts = points(s.id, f);
    if (s.id === 1 && reveal === null && pts.every(([, p]) => { const r = proj(cam, p); return r.d > 1 && r.u >= lo && r.u <= hi && r.v >= lo && r.v <= hi; })) reveal = f;
    for (const [n, p] of pts) {
      const r = proj(cam, p), ok = r.d > 1 && r.u >= lo && r.u <= hi && r.v >= lo && r.v <= hi;
      checked++;
      if (!keep.includes(n)) { if (verbose) console.log(`  . ${n.padEnd(15)} u ${(r.u * 100).toFixed(1).padStart(5)}% v ${(r.v * 100).toFixed(1).padStart(5)}% (free)`); continue; }
      const w = worst[n] === undefined || Math.abs(r.u - 0.5) + Math.abs(r.v - 0.5) > worst[n][0]
        ? [Math.abs(r.u - 0.5) + Math.abs(r.v - 0.5), r.u, r.v, f] : worst[n];
      worst[n] = w;
      if (!ok) {
        bad++;
        console.log(`  OUT f${String(f).padStart(3)} ${n.padEnd(15)} u ${(r.u * 100).toFixed(1).padStart(5)}% v ${(r.v * 100).toFixed(1).padStart(5)}% d ${r.d.toFixed(2)}m`);
      }
    }
  }
  const fovs = frames.map((f) => camAt(s.id, f).fov);
  const c0 = camAt(s.id, s.a), cE = camAt(s.id, s.b - 1);
  console.log(`  fov ${Math.min(...fovs).toFixed(1)}..${Math.max(...fovs).toFixed(1)}  pos f${s.a} [${c0.pos.map((v) => v.toFixed(1))}] -> f${s.b - 1} [${cE.pos.map((v) => v.toFixed(1))}]`);
  if (s.id === 1) console.log(`  every landmark inside the band from f${reveal} (move lands at f${PUSH1_END})`);
  console.log(`  worst-in-shot:`);
  for (const [n, [s2, u, v, f]] of Object.entries(worst)) {
    if (onlyShot) console.log(`    ${n.padEnd(15)} u ${(u * 100).toFixed(1).padStart(5)}% v ${(v * 100).toFixed(1).padStart(5)}% @f${f}`);
  }
  for (const k of Object.keys(worst)) delete worst[k];
}
console.log(`\n${checked} point-frames projected, ${bad} required-point violations`);
