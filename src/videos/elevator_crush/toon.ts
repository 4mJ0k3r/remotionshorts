// 2D cartoon characters for ElevatorCrushShort in 600x1000 design space (SKILL.md Section 2):
// SU = 0.00216, PIV = 975 at feet, soles at y = 952. Warm cream-white head (#fdfaf2), HEAD_R = 145 at (300, 235),
// #351f22 ink. Compact bean torso (shoulders +-58, hips +-70, y = 375..585). Parallel stick legs at x = 265 / 335.
// Solid #351f22 oval pupils, ZERO white anime shine dots.
//
// Roles:
//  'hero'  : coaching student (character_sheet.png): snug red ribbed beanie #d62828 (crown rises to y ~ 60), warm-yellow
//            hoodie #f4b942 with drawstrings + kangaroo pocket, dark backpack straps, dark-grey shorts, dark stick legs.
//            Params: btnPressP (closed fist pinned at dx = 145, dy = 565 — Rule B), phoneP, heartBeatP (+beat),
//            growlP, comfortP, palmP ("98XXXXXX??"), waveP.
//  'crush' : dark-brown shoulder-length hair + pink hairband & star clip, pastel-pink rain jacket #e56b6f / #b56576 over a
//            white top, denim legs. Params: rainDrops, fixHairP, phoneP, hugP, writePalmP, waveP.
// Every action is a continuous 0..1 float (quantized to 0.02 in cast.ts drawKey). Held props are drawn here (Rule A).
import { Pen, INK } from "./pen";

export { Pen, INK };
type P2 = [number, number];

export const HEAD = "#fdfaf2";
export const HEAD_R = 145;
export const WHITE = "#ffffff";
const SKIN = "#fdfaf2";

export type Expr = "neutral" | "nervous" | "panicShock" | "confidentSmile" | "shy" | "strain";

export type CharOpts = {
  role: "hero" | "crush";
  expr: Expr;
  gaze?: number;      // -1..1 pupils left/right
  gazeY?: number;     // -1..1 pupils up/down
  blush?: number;     // 0..1
  sweat?: boolean;
  cyanEyes?: boolean;
  toward?: number;    // -1 = partner on screen-left, +1 = screen-right (hug / comfort / phone / write / palm side)
  waveP?: number;     // 0..1 wave at viewer (both)
  phoneP?: number;    // 0..1 raise phone "NO SIGNAL" (both)
  // hero
  btnPressP?: number;
  heartBeatP?: number;
  beat?: number;      // 0..1 heartbeat pulse amount
  growlP?: number;
  comfortP?: number;
  palmP?: number;
  numP?: number;      // 0..1 reveal of the written number on the palm
  // crush
  rainDrops?: boolean;
  fixHairP?: number;
  hugP?: number;
  writePalmP?: number;
};

const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const lp = (a: P2, b: P2, k: number): P2 => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
const ease = (t: number) => { const u = clamp(t, 0, 1); return u * u * (3 - 2 * u); };

/** Catmull-Rom closed polygon for organic silhouettes */
const smoothClosed = (c: P2[], n = 6): P2[] => {
  const out: P2[] = [], N = c.length;
  for (let i = 0; i < N; i++) {
    const p0 = c[(i - 1 + N) % N], p1 = c[i], p2 = c[(i + 1) % N], p3 = c[(i + 2) % N];
    for (let k = 0; k < n; k++) {
      const t = k / n, t2 = t * t, t3 = t2 * t;
      const f = (a: number, b: number, cc: number, d: number) =>
        0.5 * (2 * b + (-a + cc) * t + (2 * a - 5 * b + 4 * cc - d) * t2 + (-a + 3 * b - 3 * cc + d) * t3);
      out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  return out;
};

// ---------------- FACE ----------------
const drawFace = (p: Pen, hx: number, hy: number, o: CharOpts) => {
  const g = p.g;
  const S = [-1, 1];
  const dx = 50, ey = hy + 10, my = hy + 70;
  const px = clamp(o.gaze ?? 0, -1, 1) * 10, py = clamp(o.gazeY ?? 0, -1, 1) * 9;
  const crush = o.role === "crush";
  const pupil = o.cyanEyes ? "#36e3ff" : INK;
  const blush = clamp(o.blush ?? 0, 0, 1);
  const e = o.expr;

  // Blush first (under features)
  const cheekA = 0.35 + 0.65 * blush;
  if (blush > 0.02 || e === "confidentSmile" || e === "shy") {
    g.globalAlpha = Math.min(1, e === "confidentSmile" && blush < 0.02 ? 0.45 : cheekA);
    const col = o.growlP && o.growlP > 0.2 ? "#d0587e" : "#f58fa0";
    p.ell(hx - 88, my - 8, 26 + 6 * blush, 14 + 3 * blush, col, 0);
    p.ell(hx + 88, my - 8, 26 + 6 * blush, 14 + 3 * blush, col, 0);
    g.globalAlpha = 1;
    if (blush > 0.5) for (const s of S) for (let i = 0; i < 3; i++) {
      const cx = hx + s * 88 - 12 + i * 12;
      p.stroke([[cx + 4, my - 18], [cx - 4, my + 2]], 4, "#c9445e");
    }
  }

  const solidEyes = (rx: number, ry: number) => {
    for (const s of S) {
      const ex = hx + s * dx;
      if (o.cyanEyes) { g.save(); g.shadowColor = "#36e3ff"; g.shadowBlur = 22; }
      p.ell(ex + px, ey + py, rx, ry, pupil, o.cyanEyes ? 5 : 0);
      if (o.cyanEyes) g.restore();
      if (crush) { // eyelashes on outer upper corner
        p.stroke([[ex + px + s * rx * 0.7, ey + py - ry * 0.7], [ex + px + s * (rx + 12), ey + py - ry - 6]], 5);
        p.stroke([[ex + px + s * rx * 0.2, ey + py - ry * 0.95], [ex + px + s * (rx * 0.4 + 6), ey + py - ry - 12]], 5);
      }
    }
  };

  if (e === "panicShock") {
    for (const s of S) p.arc(hx + s * dx, ey - 50, 24, 14, 195, 345, 10);
    solidEyes(20, 25);
    const m = smoothClosed([[hx - 26, my - 16], [hx + 26, my - 16], [hx + 32, my + 26], [hx - 32, my + 26]], 5);
    p.poly(m, "#4e1a22", 8);
    p.ell(hx, my + 13, 17, 11, "#d04d44", 0);
  } else if (e === "nervous") {
    // worried brows (inner ends up), wobbly mouth
    for (const s of S) { const ex = hx + s * dx; p.stroke([[ex - s * 24, ey - 30], [ex + s * 20, ey - 42]], 10); }
    solidEyes(16, 21);
    const w: P2[] = [];
    for (let i = 0; i <= 8; i++) w.push([hx - 32 + i * 8, my + 4 + (i % 2 ? -6 : 5)]);
    p.stroke(w, 7);
  } else if (e === "strain") {
    for (const s of S) {
      const ex = hx + s * dx;
      p.stroke([[ex - s * 20, ey - 18], [ex + s * 16, ey], [ex - s * 20, ey + 18]], 11);
      p.stroke([[ex - s * 26, ey - 36], [ex + s * 20, ey - 48]], 10);
    }
    const w: P2[] = [];
    for (let i = 0; i <= 10; i++) w.push([hx - 40 + i * 8, my + 6 + (i % 2 ? -7 : 6)]);
    p.stroke(w, 7);
  } else if (e === "shy") {
    for (const s of S) p.arc(hx + s * dx, ey - 40, 20, 9, 200, 340, 9);
    solidEyes(14, 19);
    p.arc(hx, my - 6, 22, 14, 20, 160, 8);
  } else if (e === "confidentSmile") {
    for (const s of S) p.arc(hx + s * dx, ey - 44, 22, 12, 200, 340, 10);
    solidEyes(16, 22);
    const m = smoothClosed([
      [hx - 46, my - 10], [hx, my - 6], [hx + 46, my - 10],
      [hx + 30, my + 24], [hx, my + 32], [hx - 30, my + 24],
    ], 5);
    p.poly(m, "#521e24", 8);
    p.poly([[hx - 42, my - 9], [hx + 42, my - 9], [hx + 36, my + 5], [hx - 36, my + 5]], WHITE, 0);
    p.stroke([[hx - 36, my + 5], [hx + 36, my + 5]], 4);
    p.ell(hx, my + 26, 22, 10, "#dc564e", 0);
  } else {
    // neutral
    for (const s of S) p.stroke([[hx + s * dx - 22, ey - 40], [hx + s * dx + 22, ey - 40]], 9);
    solidEyes(16, 22);
    p.stroke([[hx - 22, my + 2], [hx + 22, my + 2]], 7);
  }

  if (o.sweat || e === "panicShock" || e === "nervous") {
    const sx = hx - 112, sy = ey - 30;
    p.poly([[sx, sy - 22], [sx + 12, sy], [sx - 12, sy]], "#6cc4ff", 4);
    p.ell(sx, sy + 4, 13, 13, "#6cc4ff", 4);
  }
};

// ---------------- HEADWEAR / HAIR ----------------
const drawBeanie = (p: Pen, hx: number, hy: number) => {
  const red = "#d62828", dark = "#9e1717";
  // crown dome rising well above the head contour (top y ~ 58)
  const dome = smoothClosed([
    [hx - 150, hy - 70], [hx - 128, hy - 140], [hx - 60, hy - 176], [hx, hy - 182],
    [hx + 60, hy - 176], [hx + 128, hy - 140], [hx + 150, hy - 70],
  ], 6);
  p.poly(dome, red, 11);
  // ribs
  for (let i = -4; i <= 4; i++) {
    const x = hx + i * 30;
    p.stroke([[x, hy - 82], [x * 0.96 + hx * 0.04, hy - 160 + Math.abs(i) * 6]], 4, dark);
  }
  // folded cuff band (snug at the head contour)
  p.poly(smoothClosed([
    [hx - 156, hy - 58], [hx, hy - 48], [hx + 156, hy - 58],
    [hx + 152, hy - 104], [hx, hy - 112], [hx - 152, hy - 104],
  ], 6), red, 10);
  for (let i = -6; i <= 6; i++) {
    const x = hx + i * 23;
    p.stroke([[x, hy - 104 + Math.abs(i) * 0.6], [x, hy - 58 + Math.abs(i) * 0.8]], 4, dark);
  }
};

const HAIR = "#4a2c20";
const drawCrushHairBack = (p: Pen, hx: number, hy: number) => {
  // shoulder-length bob behind the head
  p.poly(smoothClosed([
    [hx - 150, hy - 40], [hx - 120, hy - 140], [hx, hy - 160], [hx + 120, hy - 140], [hx + 150, hy - 40],
    [hx + 168, hy + 90], [hx + 150, hy + 180], [hx + 96, hy + 196], [hx - 96, hy + 196], [hx - 150, hy + 180], [hx - 168, hy + 90],
  ], 6), HAIR, 11);
};
const drawCrushHairFront = (p: Pen, hx: number, hy: number, fix: number) => {
  // side-swept fringe over the forehead + hairband rising above the contour (top y ~ 78)
  p.poly(smoothClosed([
    [hx - 146, hy - 10], [hx - 138, hy - 96], [hx - 60, hy - 152], [hx + 40, hy - 156], [hx + 128, hy - 110],
    [hx + 148, hy - 20], [hx + 116, hy - 66], [hx + 40, hy - 78], [hx - 20, hy - 60], [hx - 96, hy - 66],
  ], 6), HAIR, 10);
  p.stroke([[hx - 40, hy - 140], [hx - 70, hy - 80]], 4, "#6b4232");
  p.stroke([[hx + 40, hy - 140], [hx + 70, hy - 84]], 4, "#6b4232");
  // pink hairband
  p.arc(hx, hy - 20, 150, 140, 205, 335, 20, INK);
  p.arc(hx, hy - 20, 150, 140, 206, 334, 12, "#ff8fab");
  // star clip
  const cx = hx - 120, cy = hy - 70;
  const st: P2[] = [];
  for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + (i * Math.PI) / 5, r = i % 2 ? 9 : 20; st.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
  p.poly(st, "#ffd23f", 4);
  // side lock that gets twirled (screen-right)
  const lx = hx + 150 + 10 * fix, ly = hy + 60;
  p.poly(smoothClosed([[lx - 18, ly - 70], [lx + 14, ly - 40], [lx + 12, ly + 60], [lx - 6, ly + 90 - 30 * fix], [lx - 22, ly + 40]], 5), HAIR, 8);
  if (fix > 0.3) p.arc(lx - 2, ly + 40 - 30 * fix, 14, 14, 0, 300, 5, "#6b4232");
};

// ---------------- LIMBS ----------------
const arm = (p: Pen, sh: P2, el: P2, hand: P2, sleeve: string, w = 22) => {
  p.line([sh, el, hand], sleeve, w);
};
const fist = (p: Pen, h: P2, r = 22) => {
  p.poly(smoothClosed([[h[0] - r, h[1] - r * 0.8], [h[0] + r, h[1] - r * 0.8], [h[0] + r * 1.05, h[1] + r * 0.8], [h[0] - r, h[1] + r * 0.85]], 4), SKIN, 6);
  p.stroke([[h[0] - r * 0.6, h[1] - 2], [h[0] + r * 0.6, h[1] - 2]], 4);
};
const mitt = (p: Pen, h: P2, r = 17) => p.ell(h[0], h[1], r, r * 1.05, SKIN, 6);
const openHand = (p: Pen, h: P2, r: number, up = true) => {
  const d = up ? -1 : 1;
  for (let i = 0; i < 4; i++) {
    const fx = h[0] - r * 0.6 + i * r * 0.4;
    p.line([[fx, h[1] + d * r * 0.3], [fx + (i - 1.5) * 3, h[1] + d * r * 1.25]], SKIN, r * 0.32);
  }
  p.line([[h[0] - r * 0.8, h[1] + r * 0.3], [h[0] - r * 1.3, h[1] - d * r * 0.2]], SKIN, r * 0.34);
  p.ell(h[0], h[1] + r * 0.2, r * 0.85, r * 0.8, SKIN, 6);
};

const drawPhone = (p: Pen, c: P2) => {
  const g = p.g;
  const w = 66, h = 112;
  p.poly([[c[0] - w / 2, c[1] - h / 2], [c[0] + w / 2, c[1] - h / 2], [c[0] + w / 2, c[1] + h / 2], [c[0] - w / 2, c[1] + h / 2]], "#24262e", 7);
  p.poly([[c[0] - w / 2 + 7, c[1] - h / 2 + 9], [c[0] + w / 2 - 7, c[1] - h / 2 + 9], [c[0] + w / 2 - 7, c[1] + h / 2 - 9], [c[0] - w / 2 + 7, c[1] + h / 2 - 9]], "#6fa8e8", 0);
  // red X + "NO SIGNAL"
  p.stroke([[c[0] - 14, c[1] - 34], [c[0] + 14, c[1] - 6]], 8, "#ff2d2d");
  p.stroke([[c[0] + 14, c[1] - 34], [c[0] - 14, c[1] - 6]], 8, "#ff2d2d");
  g.fillStyle = WHITE;
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.font = "900 15px 'Arial Black', sans-serif";
  g.fillText("NO", c[0], c[1] + 14);
  g.fillText("SIGNAL", c[0], c[1] + 32);
};

// ---------------- CHARACTER ENTRY ----------------
export function drawCharacter(ctx: CanvasRenderingContext2D, o: CharOpts) {
  const p = new Pen(ctx);
  const hx = 300;
  const tw = o.toward ?? 1;
  const growl = clamp(o.growlP ?? 0, 0, 1);
  const crouch = ease(growl) * 26; // body sinks when the stomach growls
  const hy = 235 + crouch;
  const tx = 300;
  const T = (y: number) => y + crouch;

  const hero = o.role === "hero";
  const legCol = hero ? "#2a2326" : "#3c4a78";

  // 1. LEGS — parallel vertical sticks, soles at 952
  for (const lx of [265, 335]) p.line([[lx, T(575)], [lx, 940]], legCol, hero ? 16 : 22);
  for (const lx of [265, 335]) {
    const fill = hero ? "#2a2326" : WHITE;
    p.poly(smoothClosed([[lx - 24, 936], [lx + 30, 934], [lx + 34, 956], [lx - 24, 958]], 4), fill, 6);
  }

  // 2. BACK LAYER: backpack (hero) / hair (crush)
  if (hero) {
    p.poly(smoothClosed([[tx - 82, T(400)], [tx + 82, T(400)], [tx + 86, T(560)], [tx - 86, T(560)]], 4), "#2f3b52", 9);
  } else {
    drawCrushHairBack(p, hx, hy);
  }

  // 3. TORSO
  const torso = smoothClosed([
    [tx - 58, T(380)], [tx + 58, T(380)], [tx + 72, T(490)], [tx + 70, T(585)], [tx - 70, T(585)], [tx - 72, T(490)],
  ], 6);
  if (hero) {
    // shorts
    p.poly([[tx - 72, T(560)], [tx + 72, T(560)], [tx + 74, T(690)], [tx + 6, T(690)], [tx, T(640)], [tx - 6, T(690)], [tx - 74, T(690)]], "#3d3d44", 9);
    p.stroke([[tx - 66, T(585)], [tx - 68, T(684)]], 5, "#e8e8e8");
    p.stroke([[tx + 66, T(585)], [tx + 68, T(684)]], 5, "#e8e8e8");
    // hoodie
    p.poly(torso, "#f4b942", 11);
    p.poly(smoothClosed([[tx - 50, T(500)], [tx + 50, T(500)], [tx + 58, T(560)], [tx - 58, T(560)]], 3), "#e6a92f", 6); // pocket
    // straps
    p.line([[tx - 50, T(384)], [tx - 46, T(470)]], "#2f3b52", 14);
    p.line([[tx + 50, T(384)], [tx + 46, T(470)]], "#2f3b52", 14);
    // hood rim + drawstrings
    p.poly(smoothClosed([[tx - 62, T(372)], [tx, T(400)], [tx + 62, T(372)], [tx + 40, T(360)], [tx, T(372)], [tx - 40, T(360)]], 4), "#e6a92f", 7);
    p.stroke([[tx - 14, T(394)], [tx - 17, T(452)]], 5, WHITE);
    p.stroke([[tx + 14, T(394)], [tx + 17, T(452)]], 5, WHITE);
    p.dot(tx - 17, T(456), 6, WHITE);
    p.dot(tx + 17, T(456), 6, WHITE);
  } else {
    p.poly(smoothClosed([
      [tx - 58, T(380)], [tx + 58, T(380)], [tx + 74, T(490)], [tx + 82, T(605)], [tx - 82, T(605)], [tx - 74, T(490)],
    ], 6), "#e56b6f", 11);
    // white top
    p.poly([[tx - 26, T(384)], [tx + 26, T(384)], [tx + 20, T(600)], [tx - 20, T(600)]], WHITE, 6);
    // lavender zip trims + pocket flaps
    p.stroke([[tx - 24, T(386)], [tx - 20, T(600)]], 6, "#b56576");
    p.stroke([[tx + 24, T(386)], [tx + 20, T(600)]], 6, "#b56576");
    p.stroke([[tx - 66, T(530)], [tx - 36, T(530)]], 6, "#b56576");
    p.stroke([[tx + 66, T(530)], [tx + 36, T(530)]], 6, "#b56576");
    // collar
    p.poly([[tx - 58, T(376)], [tx - 24, T(396)], [tx - 40, T(410)]], "#b56576", 6);
    p.poly([[tx + 58, T(376)], [tx + 24, T(396)], [tx + 40, T(410)]], "#b56576", 6);
  }

  // heartbeat icon on chest (hero)
  const hb = clamp(o.heartBeatP ?? 0, 0, 1);
  if (hero && hb > 0.02) {
    const beat = clamp(o.beat ?? 0, 0, 1);
    const k = (0.7 + 0.5 * beat) * (0.5 + 0.5 * hb);
    const cx = tx + 22, cy = T(455);
    const heart: P2[] = [];
    for (let i = 0; i < 40; i++) {
      const t = (i / 40) * Math.PI * 2;
      heart.push([cx + 16 * Math.pow(Math.sin(t), 3) * 2.0 * k, cy - (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) * 2.0 * k]);
    }
    p.poly(heart, "#ff2d55", 6);
    if (beat > 0.15) {
      ctx.globalAlpha = beat * hb;
      for (const s of [-1, 1]) {
        p.arc(cx, cy, 60 + 30 * beat, 52 + 26 * beat, s > 0 ? -40 : 140, s > 0 ? 40 : 220, 7, "#ff2d55");
        p.arc(cx, cy, 92 + 34 * beat, 80 + 30 * beat, s > 0 ? -32 : 148, s > 0 ? 32 : 212, 6, "#ff6a8a");
      }
      ctx.globalAlpha = 1;
    }
  }

  // 4. ARMS (shoulders at tx +- 56, y 395)
  const sleeve = hero ? "#f4b942" : "#e56b6f";
  const shL: P2 = [tx - 56, T(395)], shR: P2 = [tx + 56, T(395)];
  const restL: P2 = [tx - 82, T(560)], restR: P2 = [tx + 82, T(560)];
  const elRestL: P2 = [tx - 88, T(480)], elRestR: P2 = [tx + 88, T(480)];
  // target (hand, elbow, kind) per side: kind 0 mitt, 1 fist, 2 open palm, 3 phone, 4 pen
  type H = { h: P2; e: P2; kind: number; w: number };
  let L: H = { h: restL, e: elRestL, kind: 0, w: 0 };
  let R: H = { h: restR, e: elRestR, kind: 0, w: 0 };
  const blendTo = (cur: H, h: P2, e: P2, kind: number, wgt: number): H => {
    if (wgt <= cur.w) return cur;
    return { h: lp(cur.h, h, ease(wgt)), e: lp(cur.e, e, ease(wgt)), kind: wgt > 0.5 ? kind : cur.kind, w: wgt };
  };
  // side helpers: "near" = toward partner
  const nearIsR = tw > 0;
  const setNear = (h: P2, e: P2, kind: number, w: number) => { if (nearIsR) R = blendTo(R, h, e, kind, w); else L = blendTo(L, h, e, kind, w); };
  const setFar = (h: P2, e: P2, kind: number, w: number) => { if (nearIsR) L = blendTo(L, h, e, kind, w); else R = blendTo(R, h, e, kind, w); };
  const sx = (d: number) => tx + tw * d; // x offset toward partner

  const btn = clamp(o.btnPressP ?? 0, 0, 1);
  if (hero && btn > 0) L = blendTo(L, [145, 565], [190, T(500)], 1, btn); // Rule B fist — dy fixed at 565 (no crouch in S5)
  const ph = clamp(o.phoneP ?? 0, 0, 1);
  if (ph > 0) setNear([sx(108), T(450)], [sx(92), T(520)], 3, ph);
  if (hero && growl > 0) {
    L = blendTo(L, [tx - 30, T(530)], [tx - 92, T(470)], 0, growl);
    R = blendTo(R, [tx + 30, T(540)], [tx + 92, T(480)], 0, growl);
  }
  const cf = clamp(o.comfortP ?? 0, 0, 1);
  if (hero && cf > 0) {
    setNear([sx(205), T(420)], [sx(140), T(470)], 0, cf);
    setFar([sx(150), T(440)], [sx(40), T(500)], 0, cf);
  }
  const palm = clamp(o.palmP ?? 0, 0, 1);
  if (hero && palm > 0) setNear([sx(150), T(430)], [sx(118), T(520)], 2, palm);
  const fix = clamp(o.fixHairP ?? 0, 0, 1);
  if (!hero && fix > 0) R = blendTo(R, [tx + 150, T(300)], [tx + 128, T(430)], 0, fix);
  const hug = clamp(o.hugP ?? 0, 0, 1);
  if (!hero && hug > 0) {
    setNear([sx(220), T(410)], [sx(130), T(440)], 0, hug);
    setFar([sx(150), T(470)], [sx(30), T(500)], 0, hug);
  }
  const wr = clamp(o.writePalmP ?? 0, 0, 1);
  if (!hero && wr > 0) {
    setNear([sx(160), T(415)], [sx(100), T(500)], 4, wr);
  }
  const wave = clamp(o.waveP ?? 0, 0, 1);
  if (wave > 0) {
    // wave with the far hand (screen side away from partner) so the near hand keeps its prop
    setFar([sx(-150), T(250)], [sx(-118), T(360)], 2, wave);
  }

  const drawArm = (sh: P2, a: H) => {
    arm(p, sh, a.e, a.h, sleeve);
    if (a.kind === 1) fist(p, a.h, 24);
    else if (a.kind === 2) openHand(p, a.h, 44);
    else if (a.kind === 3) { drawPhone(p, [a.h[0], a.h[1] - 40]); mitt(p, a.h, 16); }
    else if (a.kind === 4) {
      // pen with glowing cyan tip
      p.line([[a.h[0] - tw * 8, a.h[1] + 6], [a.h[0] + tw * 34, a.h[1] - 26]], "#3a3f6a", 9);
      ctx.save(); ctx.shadowColor = "#36e3ff"; ctx.shadowBlur = 18;
      p.dot(a.h[0] + tw * 36, a.h[1] - 28, 7, "#36e3ff");
      ctx.restore();
      mitt(p, a.h, 16);
    } else mitt(p, a.h);
  };

  // arms reaching across the chest are drawn after the torso; head is drawn after arms that stay below the chin
  drawArm(shL, L);
  drawArm(shR, R);

  // open palm with the mystery number (drawn on top of the palm)
  const num = clamp(o.numP ?? 0, 0, 1);
  if (hero && palm > 0.5 && num > 0.02) {
    const a = nearIsR ? R : L;
    const c: P2 = [a.h[0], a.h[1] + 4];
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.shadowColor = "#36e3ff";
    ctx.shadowBlur = 16;
    ctx.fillStyle = "#08a8d8";
    ctx.font = "900 22px 'Arial Black', sans-serif";
    const full = "98XXXXXX??", n = Math.ceil(num * full.length), shown = full.slice(0, n);
    ctx.fillText(shown.slice(0, 6), c[0], c[1] - 4);
    if (n > 6) ctx.fillText(shown.slice(6), c[0], c[1] + 16);
    ctx.restore();
  }

  // 5. HEAD
  p.ell(hx, hy, HEAD_R, HEAD_R, HEAD, 12);
  drawFace(p, hx, hy, o);

  // 6. HAIR / HAT
  if (hero) drawBeanie(p, hx, hy);
  else drawCrushHairFront(p, hx, hy, fix);

  // 7. growl text "GURRRR!" (neon green, beside the stomach, inside the card)
  if (hero && growl > 0.15) {
    const k = clamp((growl - 0.15) / 0.5, 0, 1);
    ctx.save();
    ctx.translate(sx(150), T(640));
    ctx.rotate(-0.14);
    ctx.scale(0.6 + 0.4 * k, 0.6 + 0.4 * k);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "900 50px 'Arial Black', sans-serif";
    ctx.lineJoin = "round";
    ctx.lineWidth = 14;
    ctx.strokeStyle = INK;
    ctx.strokeText("GURRRR!", 0, 0);
    ctx.fillStyle = "#7dff4a";
    ctx.fillText("GURRRR!", 0, 0);
    ctx.restore();
    // wobble lines around stomach
    for (const s of [-1, 1]) p.arc(tx, T(530), 100, 50, s > 0 ? -30 : 150, s > 0 ? 30 : 210, 6, "#7dff4a");
  }

  // 8. rain droplets on the crush (blue sparkle)
  if (!hero && o.rainDrops) {
    const drops: P2[] = [[170, 150], [420, 120], [470, 300], [150, 330], [230, 470], [380, 520], [260, 590], [350, 430], [200, 250], [440, 210]];
    for (const [x, y] of drops) {
      p.poly([[x, y - 16], [x + 8, y], [x - 8, y]], "#8fd3ff", 3);
      p.ell(x, y + 3, 8, 8, "#8fd3ff", 3);
    }
  }
}

// ---------------- 2D UNLIT FX CARDS (400 x 400 design) ----------------
export type FxType = "dust" | "sparks" | "sparkle" | "hearts" | "stars" | "aura" | "drops" | "cyan";

export function drawFxBlob(ctx: CanvasRenderingContext2D) {
  ctx.fillStyle = WHITE;
  ctx.fillRect(0, 0, 128, 128);
  const gr = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, "#3a2e26");
  gr.addColorStop(0.35, "#6b584b");
  gr.addColorStop(0.7, "#b8aca0");
  gr.addColorStop(1.0, "#ffffff");
  ctx.fillStyle = gr;
  ctx.fillRect(0, 0, 128, 128);
}

const star = (p: Pen, cx: number, cy: number, r: number, fill: string, ol = 4) => {
  const pts: P2[] = [];
  for (let i = 0; i < 8; i++) { const a = -Math.PI / 2 + (i * Math.PI) / 4, rr = i % 2 ? r * 0.32 : r; pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr]); }
  p.poly(pts, fill, ol);
};
const heartAt = (p: Pen, cx: number, cy: number, s: number, fill: string) => {
  const pts: P2[] = [];
  for (let i = 0; i < 32; i++) {
    const t = (i / 32) * Math.PI * 2;
    pts.push([cx + 16 * Math.pow(Math.sin(t), 3) * s, cy - (13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) * s]);
  }
  p.poly(pts, fill, 5);
};

export function drawFx(ctx: CanvasRenderingContext2D, type: FxType, progress: number) {
  const p = new Pen(ctx);
  const u = clamp(progress, 0, 1);
  const C = 200;
  if (type === "dust") {
    ctx.globalAlpha = (1 - u) * 0.85;
    const r0 = lerp(20, 80, Math.sqrt(u));
    for (const [x, y, k] of [[200, 220, 1], [150, 240, 0.75], [250, 235, 0.8], [190, 170, 0.6]]) {
      p.ell(x, y - u * 40, r0 * k, r0 * k * 0.75, "#e9e0d4", 0);
      p.arc(x, y - u * 40, r0 * k, r0 * k * 0.75, 180, 360, 4, "#b4a694");
    }
  } else if (type === "sparks") {
    ctx.globalAlpha = 1 - u * 0.8;
    for (let i = 0; i < 14; i++) {
      const a = (i * Math.PI * 2) / 14 + 0.3;
      const r0 = lerp(10, 60, u), r1 = lerp(50, 180, Math.sqrt(u));
      p.stroke([[C + Math.cos(a) * r0, C + Math.sin(a) * r0], [C + Math.cos(a) * r1, C + Math.sin(a) * r1 + u * 30]], 7, i % 2 ? "#ffd23f" : "#ff6a1f");
    }
    star(p, C, C, 40 * (1 - u) + 6, "#fff2a8", 0);
  } else if (type === "sparkle" || type === "stars" || type === "cyan") {
    const col = type === "cyan" ? "#56e8ff" : type === "stars" ? "#ffd23f" : "#ffe680";
    ctx.globalAlpha = u < 0.75 ? 1 : (1 - u) * 4;
    const pts: [number, number, number][] = [[80, 120, 1], [320, 90, 0.8], [290, 300, 1.1], [110, 310, 0.7], [200, 60, 0.6], [350, 220, 0.7], [50, 220, 0.8]];
    pts.forEach(([x, y, k], i) => {
      const tw = 0.5 + 0.5 * Math.sin(u * 12 + i * 1.7);
      star(p, x, y - u * 30, (18 + 16 * tw) * k, col, 4);
    });
  } else if (type === "hearts") {
    ctx.globalAlpha = u < 0.7 ? 1 : (1 - u) / 0.3;
    for (let i = 0; i < 7; i++) {
      const a = (i / 7) * Math.PI * 2;
      const r = lerp(20, 160, Math.sqrt(u));
      heartAt(p, C + Math.cos(a) * r, C + Math.sin(a) * r * 0.8 - u * 30, 1.2 + (i % 3) * 0.35, i % 2 ? "#ff5c8a" : "#ff2d55");
    }
  } else if (type === "aura") {
    // soft pink glow puffs (used with soft material)
    const gr = ctx.createRadialGradient(C, C, 0, C, C, 190);
    gr.addColorStop(0, "rgba(255,150,190,0.55)");
    gr.addColorStop(0.6, "rgba(255,120,170,0.25)");
    gr.addColorStop(1, "rgba(255,120,170,0)");
    ctx.fillStyle = gr;
    ctx.fillRect(0, 0, 400, 400);
    for (let i = 0; i < 4; i++) heartAt(p, 70 + i * 85, 330 - ((u * 400 + i * 90) % 260), 0.9, "#ff8fb1");
  } else if (type === "drops") {
    ctx.globalAlpha = 1 - u;
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      const r = lerp(30, 170, Math.sqrt(u));
      const x = C + Math.cos(a) * r, y = C + Math.sin(a) * r;
      p.poly([[x, y - 14], [x + 7, y], [x - 7, y]], "#8fd3ff", 3);
      p.ell(x, y + 3, 7, 7, "#8fd3ff", 3);
    }
  }
  ctx.globalAlpha = 1;
}
