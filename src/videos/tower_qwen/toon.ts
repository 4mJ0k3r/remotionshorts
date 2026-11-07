// The "Tower Qwen" cast, drawn procedurally in the 600 x 1000 design box (soles y 952, card pivot y 975, head centre
// (300, 235) at HEAD_R 145 so the chin lands on 380 = the cardshade head zone).
//   driver   - navy peaked cap with a dark visor and gold badge (crown above y = 85), light-blue shirt, dark tie,
//              navy transit jacket with a round "78" chest plate. leverP slides the screen-left fist 165 -> 135 at
//              dy 580 (world.ts pins the 3D brass knob under it); bonusP raises the green-and-cream "£10 BONUS"
//              certificate, pinched by both fists at its OUTER edges so the fists never cover the words.
//   watchman - brown flat cap, white shirt, red suspenders, dark bow tie, a white mug of tea steaming in his
//              screen-right hand, kept out at x >= 440 so neither the cup nor the steam crosses the face.
// Every face is warm cream #fdfaf2 with #351f22 ink and solid dark pupils (no shine dots); arms are 2-bone IK so the
// fists land exactly where the rig asks. All continuous inputs are quantised by cast.ts before they are drawn.
import { Pen, INK } from "./pen";

export { Pen, INK };
type P2 = [number, number];

const HEAD = "#fdfaf2", HEAD_SH = "#ecdcc4", SKIN_SH = "#f0e2cd";
const WHITE = "#ffffff", NAVY = "#2b4570", NAVY_D = "#1e3253", CAP = "#23395d", CAP_D = "#182742";
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const lerpP = (a: P2, b: P2, k: number): P2 => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
const sm = (x: number) => { const u = clamp(x, 0, 1); return u * u * (3 - 2 * u); };
const rad = (d: number) => (d * Math.PI) / 180;
export const mul = (c: string, k: number) => {
  const n = parseInt(c.slice(1), 16);
  const ch = (v: number) => Math.min(255, Math.round(v * k)).toString(16).padStart(2, "0");
  return `#${ch((n >> 16) & 255)}${ch((n >> 8) & 255)}${ch(n & 255)}`;
};
export const mix = (a: string, b: string, t: number) => {
  const A = parseInt(a.slice(1), 16), B = parseInt(b.slice(1), 16);
  const ch = (s: number) => Math.round(((A >> s) & 255) * (1 - t) + ((B >> s) & 255) * t).toString(16).padStart(2, "0");
  return `#${ch(16)}${ch(8)}${ch(0)}`;
};
const ellPts = (cx: number, cy: number, rx: number, ry: number, a0 = 0, a1 = 360, n = 40): P2[] => {
  const pts: P2[] = [];
  for (let i = 0; i <= n; i++) { const a = rad(a0 + ((a1 - a0) * i) / n); pts.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]); }
  return pts;
};
/** closed Catmull-Rom through the control points */
const round = (c: P2[], n = 6): P2[] => {
  const out: P2[] = [], N = c.length;
  for (let i = 0; i < N; i++) {
    const p0 = c[(i - 1 + N) % N], p1 = c[i], p2 = c[(i + 1) % N], p3 = c[(i + 2) % N];
    for (let k = 0; k < n; k++) {
      const t = k / n, t2 = t * t, t3 = t2 * t;
      const f = (a: number, b: number, cc: number, d: number) => 0.5 * (2 * b + (-a + cc) * t + (2 * a - 5 * b + 4 * cc - d) * t2 + (-a + 3 * b - 3 * cc + d) * t3);
      out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  return out;
};
const star = (cx: number, cy: number, r0: number, r1: number, n = 5, rot = -Math.PI / 2): P2[] => {
  const pts: P2[] = [];
  for (let i = 0; i < n * 2; i++) { const a = rot + (i * Math.PI) / n, r = i % 2 ? r1 : r0; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
  return pts;
};
const rotAbout = (pt: P2, a: number, c: P2): P2 => {
  const s = Math.sin(a), co = Math.cos(a), x = pt[0] - c[0], y = pt[1] - c[1];
  return [c[0] + x * co - y * s, c[1] + x * s + y * co];
};
/** tapered stroke along a polyline with an optional ink rim */
const taper = (p: Pen, pts: P2[], w0: number, w1: number, col: string, ol = 0) => {
  const L: number[] = [0];
  for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const T = L[L.length - 1] || 1;
  const pass = (extra: number, c: string) => {
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i], wa = lerp(w0, w1, L[i - 1] / T) + extra, wb = lerp(w0, w1, L[i] / T) + extra;
      let nx = b[1] - a[1], ny = a[0] - b[0]; const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
      p.poly([[a[0] + nx * wa / 2, a[1] + ny * wa / 2], [b[0] + nx * wb / 2, b[1] + ny * wb / 2], [b[0] - nx * wb / 2, b[1] - ny * wb / 2], [a[0] - nx * wa / 2, a[1] - ny * wa / 2]], c, 0);
    }
    pts.forEach((q, i) => p.dot(q[0], q[1], (lerp(w0, w1, L[i] / T) + extra) / 2, c));
  };
  if (ol > 0) pass(ol * 2, INK);
  pass(0, col);
};
/** 2-bone IK: pick the elbow solution that bends AWAY from the body centre, so arms never fold through the chest */
const elbowOf = (s: P2, h: P2, l1: number, l2: number, away: P2): P2 => {
  const dx = h[0] - s[0], dy = h[1] - s[1], d = Math.hypot(dx, dy) || 1;
  if (d >= l1 + l2 - 1) return [s[0] + dx * 0.5, s[1] + dy * 0.5];
  const a = (l1 * l1 - l2 * l2 + d * d) / (2 * d), hgt = Math.sqrt(Math.max(0, l1 * l1 - a * a));
  const mx = s[0] + (dx * a) / d, my = s[1] + (dy * a) / d;
  const e1: P2 = [mx + (-dy / d) * hgt, my + (dx / d) * hgt], e2: P2 = [mx - (-dy / d) * hgt, my - (dx / d) * hgt];
  return Math.hypot(e1[0] - away[0], e1[1] - away[1]) >= Math.hypot(e2[0] - away[0], e2[1] - away[1]) ? e1 : e2;
};
/** centred, auto-shrunk caption inside a 2D prop */
const caption = (p: Pen, s: string, cx: number, cy: number, px: number, col: string, maxW: number) => {
  const g = p.g;
  let n = px;
  g.font = `900 ${n}px Arial`;
  while (g.measureText(s).width > maxW && n > 8) { n -= 2; g.font = `900 ${n}px Arial`; }
  g.fillStyle = col; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(s, cx, cy);
};

// ---------------- types ----------------
export type Who = "driver" | "watchman";
export type Expr = "calmWhistle" | "panicShock" | "determinedGrin" | "proudSmile";
export type ToonOpts = {
  who: Who; expr: Expr;
  /** "lever" = the screen-left fist is pinned on the 3D cab throttle; "free" = arms at rest */
  mode?: "lever" | "free";
  leverP?: number;   // 0..1 fist travels design x 165 -> 135 at dy 580
  bonusP?: number;   // 0..1 certificate raise (both fists to the paper's outer edges)
  mugP?: number;     // 1 mug up at the watchman's shoulder, 0 mug dropped to his side
  lean?: number;     // torso lean, radians about the hip
  bob?: number; sway?: number;
  blink?: number; gaze?: number; gazeY?: number; light?: number;
};

const HEAD_R = 145, HCY = 235, CHIN = 380, SH_Y = 400, HIP_Y = 585, SOLE = 952;
const SX = 300, ARM_U = 118, ARM_L = 118;

// ---------------- face ----------------
const drawFace = (p: Pen, hx: number, hy: number, o: ToonOpts) => {
  const e = o.expr, gx = clamp(o.gaze ?? 0, -1, 1) * 9, gy = clamp(o.gazeY ?? 0, -1, 1) * 7;
  const blink = (o.blink ?? 0) > 0.5, dx = 47, ey = hy + 8, my = hy + 66;
  if (e === "determinedGrin") {
    for (const s of [-1, 1]) {
      const ex = hx + s * dx;
      p.stroke([[ex - s * 20, ey - 20], [ex + s * 18, ey - 2], [ex - s * 20, ey + 16]], 12);   // > < squint
      p.stroke([[ex - s * 34, ey - 52], [ex + s * 22, ey - 34]], 11);                          // brows driven down
    }
    const x0 = hx - 56, x1 = hx + 56, y0 = my - 20, y1 = my + 22;
    p.poly(round([[x0, y0], [x1, y0], [x1 + 3, (y0 + y1) / 2], [x1, y1], [x0, y1], [x0 - 3, (y0 + y1) / 2]], 4), WHITE, 8);
    p.stroke([[x0 + 3, my], [x1 - 3, my]], 5);
    for (const t of [-40, -20, 0, 20, 40]) p.stroke([[hx + t, y0 + 3], [hx + t, y1 - 3]], 4);
    p.ell(hx - 86, my - 4, 18, 10, "#f0b7a6", 0); p.ell(hx + 86, my - 4, 18, 10, "#f0b7a6", 0);
    return;
  }
  if (e === "panicShock") {
    for (const s of [-1, 1]) {
      const ex = hx + s * dx;
      p.arc(ex, ey - 62, 26, 15, 210, 330, 10);                                    // brows flown up
      if (blink) { p.stroke([[ex - 20, ey], [ex + 20, ey]], 9); continue; }
      p.ell(ex + gx * 0.4, ey + 2 + gy * 0.4, 19, 25, INK, 0);                      // huge dark pupils, no shine
      p.stroke([[ex - 24, ey - 28], [ex + 24, ey - 28]], 4, SKIN_SH);
    }
    p.ell(hx, my + 12, 26, 30, "#4a1a22", 8);                                       // open, breathless mouth
    p.ell(hx, my + 26, 14, 12, "#d9695f", 0);
    p.poly(round([[hx + 108, hy - 46], [hx + 128, hy - 4], [hx + 118, hy + 22], [hx + 96, hy - 4]], 5), "#7cc8f2", 5);
    p.ell(hx + 108, hy - 2, 6, 9, "#e2f4ff", 0);
    return;
  }
  if (e === "proudSmile") {
    for (const s of [-1, 1]) {
      const ex = hx + s * dx;
      p.arc(ex, ey - 54, 24, 12, 200, 340, 9);
      if (blink) { p.arc(ex, ey + 6, 19, 13, 200, 340, 10); continue; }
      p.ell(ex + gx, ey + 4 + gy, 14, 21, INK, 0);
    }
    p.ell(hx - 88, my - 10, 21, 12, "#f2ada0", 0); p.ell(hx + 88, my - 10, 21, 12, "#f2ada0", 0);
    const m = round([[hx - 52, my - 12], [hx, my - 8], [hx + 52, my - 12], [hx + 34, my + 26], [hx, my + 36], [hx - 34, my + 26]], 5);
    p.poly(m, "#5a1e24", 8);
    p.clip(m, () => {
      p.ell(hx, my + 34, 27, 13, "#e0605a", 0);
      p.poly([[hx - 56, my - 16], [hx + 56, my - 16], [hx + 48, my + 6], [hx - 48, my + 6]], WHITE, 0);
      p.stroke([[hx - 48, my + 6], [hx + 48, my + 6]], 4);
    });
    p.poly(m, null, 8);
    return;
  }
  // calmWhistle: lidded, easy eyes and a small round whistling mouth
  for (const s of [-1, 1]) {
    const ex = hx + s * dx;
    p.stroke([[ex - s * 30, ey - 44], [ex + s * 24, ey - 48]], 10);
    if (blink) { p.stroke([[ex - 18, ey + 2], [ex + 18, ey + 2]], 8); continue; }
    p.clip([[ex - 26, ey - 6], [ex + 26, ey - 10], [ex + 26, ey + 26], [ex - 26, ey + 26]], () => p.ell(ex + gx, ey + 6 + gy, 13, 17, INK, 0));
    p.stroke([[ex - 24, ey - 7], [ex + 24, ey - 11]], 9);
  }
  p.ell(hx + 6, my + 4, 15, 17, "#8f3f36", 7);
  p.ell(hx + 6, my + 4, 7, 8, "#3a161c", 0);
};

// ---------------- heads ----------------
const headBase = (p: Pen, hx: number, hy: number, light: number) => {
  for (const s of [-1, 1]) p.ell(hx + s * 138, hy + 18, 24, 32, HEAD, 8);                       // ears
  const pts = ellPts(hx, hy, HEAD_R, HEAD_R * 0.99, 0, 360, 64);
  p.poly(pts, HEAD, 0);
  p.clip(pts, () => p.ell(hx - Math.cos(light) * 54, hy - Math.sin(light) * 42, HEAD_R * 1.02, HEAD_R, HEAD_SH, 0));
  p.clip(pts, () => p.ell(hx + Math.cos(light) * 20, hy + Math.sin(light) * 16, HEAD_R * 0.94, HEAD_R * 0.92, HEAD, 0));
  p.inkRing(pts, 13, light + Math.PI, 0.4);
};
const drawHead = (p: Pen, hx: number, hy: number, o: ToonOpts, light: number) => {
  headBase(p, hx, hy, light);
  if (o.who === "driver") {
    // navy peaked cap: crown well above the head contour, cream sweep band, dark visor, gold plate. Everything stays
    // above y = 172 so the visor never covers the brows (ey - 62 = 181) or the eyes (ey = 243).
    const dome = ellPts(hx, hy - 100, 146, 92, 176, 362, 44);                                   // top y = 43
    p.gradFill(dome, CAP, CAP_D, light, 0.3);
    p.poly(dome, null, 9);
    p.stroke([[hx - 58, hy - 172], [hx - 24, hy - 118]], 5, CAP_D);
    p.stroke([[hx + 26, hy - 178], [hx + 40, hy - 120]], 5, CAP_D);
    p.poly([[hx - 152, hy - 115], [hx + 152, hy - 115], [hx + 150, hy - 85], [hx - 150, hy - 85]], "#efe6d2", 8);
    p.stroke([[hx - 146, hy - 100], [hx + 146, hy - 100]], 4, mul(CAP, 0.86));
    p.poly(round([[hx - 134, hy - 85], [hx + 134, hy - 85], [hx + 150, hy - 67], [hx, hy - 63], [hx - 150, hy - 67]], 5), CAP_D, 8);
    p.ell(hx, hy - 131, 29, 29, "#e8c04a", 7);                                                  // gold badge on the band
    p.poly([[hx - 17, hy - 139], [hx + 17, hy - 139], [hx + 11, hy - 123], [hx - 11, hy - 123]], CAP, 0);
    p.ell(hx, hy - 145, 8, 6, "#f6e39c", 3);
    for (const s of [-1, 1]) p.poly([[hx + s * 140, hy - 20], [hx + s * 150, hy + 34], [hx + s * 124, hy + 26], [hx + s * 126, hy - 14]], "#4a2f22", 5);
  } else {
    // brown flat cap: a low, soft crown that tips forward and overhangs the brow on the screen-right brim
    const crown = ellPts(hx - 6, hy - 104, 154, 74, 172, 368, 40);
    p.gradFill(crown, "#8a5a34", "#6a4226", light, 0.3);
    p.poly(round([...crown, [hx + 156, hy - 62], [hx - 158, hy - 66]], 5), "#8a5a34", 0);
    p.poly(crown, null, 9);
    for (let i = 0; i < 5; i++) p.stroke([[hx - 110 + i * 52, hy - 168 + 8 * Math.abs(2 - i)], [hx - 70 + i * 52, hy - 100]], 4, "#6a4226");
    p.dot(hx - 6, hy - 172, 9, "#6a4226");
    p.poly(round([[hx + 60, hy - 74], [hx + 172, hy - 70], [hx + 186, hy - 44], [hx + 60, hy - 52]], 4), "#6a4226", 7);
    p.stroke([[hx - 150, hy - 62], [hx + 70, hy - 66]], 5, "#5a3420");
    for (const s of [-1, 1]) p.poly([[hx + s * 142, hy - 22], [hx + s * 152, hy + 30], [hx + s * 126, hy + 24]], "#5a3a24", 5);
  }
  drawFace(p, hx, hy, o);
};

// ---------------- held 2D props ----------------
/** white enamel mug + handle + tea, steam curling up and to the screen-right, away from the face */
const drawMug = (p: Pen, c: P2, sway: number) => {
  const x = c[0], y = c[1];
  const body: P2[] = [[x - 40, y - 46], [x + 40, y - 46], [x + 34, y + 34], [x - 34, y + 34]];
  p.poly(round(body, 4), WHITE, 8);
  p.clip(round(body, 4), () => { p.poly([[x + 8, y - 46], [x + 44, y - 46], [x + 38, y + 36], [x + 2, y + 36]], "#dfd8c8", 0); });
  p.ell(x, y - 46, 40, 13, "#6b4a2c", 6);
  p.band([[x + 44, y - 22], [x + 74, y - 6], [x + 70, y + 16], [x + 40, y + 20]], NAVY_D, 12, 5, "round");
  const s = sm(sway);
  p.g.save(); p.g.globalAlpha = 0.5 + 0.4 * s;
  for (let i = 0; i < 3; i++) {
    const x0 = x - 16 + i * 18, len = 90 + 40 * ((i % 2) + s);
    p.stroke([[x0, y - 62], [x0 + 16, y - 62 - len * 0.35], [x0 - 8, y - 62 - len * 0.7], [x0 + 14, y - 62 - len]], 9 - i * 2, "#f4f8fa");
  }
  p.g.restore();
};

/** the green-and-cream "£10 BONUS" certificate, pinched by both fists at its two OUTER edges so the words stay clear */
const drawCert = (p: Pen, l: P2, r: P2, k: number) => {
  if (k < 0.02) return;
  const cx = (l[0] + r[0]) / 2, cy = (l[1] + r[1]) / 2;
  const hw = (r[0] - l[0]) / 2, hh = 56 + 34 * k;
  const face = round([[cx - hw, cy - hh], [cx, cy - hh - 8], [cx + hw, cy - hh], [cx + hw, cy + hh], [cx, cy + hh + 6], [cx - hw, cy + hh]], 6);
  p.poly(face, "#f8f3e2", 9);
  p.clip(face, () => {
    p.poly([[cx - hw, cy - hh], [cx + hw, cy - hh], [cx + hw, cy - hh + 24], [cx - hw, cy - hh + 24]], "#2f7a4a", 0);
    p.poly([[cx - hw, cy + hh - 24], [cx + hw, cy + hh - 24], [cx + hw, cy + hh], [cx - hw, cy + hh]], "#2f7a4a", 0);
    p.stroke([[cx - hw + 30, cy + hh - 44], [cx + hw - 30, cy + hh - 44]], 5, mix("#2f7a4a", "#f8f3e2", 0.45));
    caption(p, "£10 BONUS", cx, cy - 4, 64, "#1d5a36", 2 * hw - 96);
    caption(p, "LONDON TRANSPORT", cx + 16, cy + hh - 62, 26, "#7a6f5c", 2 * hw - 150);
    p.ell(cx - hw + 52, cy + hh - 62, 22, 22, "#d8a828", 6);
    p.ell(cx - hw + 52, cy + hh - 62, 13, 13, mul("#d8a828", 1.15), 0);
  });
  p.poly(face, null, 9);
};

// ---------------- the figure ----------------
export const drawToon = (p: Pen, o: ToonOpts) => {
  const light = o.light ?? -2.2;
  const bob = o.bob ?? 0, lean = o.lean ?? 0;
  const hipY = HIP_Y + bob * 0.35, shY = SH_Y + bob;
  const piv: P2 = [SX, hipY];
  const R = (pt: P2) => rotAbout(pt, lean, piv);
  const hx = SX + clamp(o.gaze ?? 0, -1, 1) * 10, hy = HCY + bob + clamp(o.gazeY ?? 0, -1, 1) * 7;

  // ---- legs: straight parallel sticks, dark pill feet flat on the sole line ----
  const trousers = o.who === "driver" ? NAVY_D : "#3b3a44";
  for (const s of [-1, 1]) {
    taper(p, [[SX + s * 35, hipY + 14], [SX + s * 35, SOLE - 14]], 30, 24, trousers, 6);
    p.ell(SX + s * (35 + 11), SOLE - 10, 26, 12, "#241a1e", 7);
    p.ell(SX + s * (35 + 11) - 8, SOLE - 16, 9, 4, "#4a3a40", 0);
  }

  // ---- torso: compact bean, shoulders 120 across, hips 145 ----
  p.rot = [lean, piv[0], piv[1]];
  p.poly([[hx - 18, hy + 118], [hx + 18, hy + 118], [SX + 18, shY + 6], [SX - 18, shY + 6]], HEAD, 5);
  const torso = round([[SX - 58, shY - 4], [SX, shY - 14], [SX + 58, shY - 4], [SX + 68, shY + 56], [SX + 72, hipY - 6],
    [SX, hipY + 10], [SX - 72, hipY - 6], [SX - 68, shY + 56]], 6);
  if (o.who === "driver") {
    p.gradFill(torso, "#bcdcf0", "#8fb6d2", light, 0.4);                    // light-blue shirt under the jacket
    p.poly(torso, null, 10);
    const half: P2[] = [[SX - 20, shY + 2], [SX - 58, shY - 2], [SX - 70, shY + 34], [SX - 74, hipY - 6], [SX - 14, hipY - 2], [SX - 16, shY + 6]];
    for (const s of [-1, 1]) {
      const panel = half.map(([x, y]) => [SX + s * (x - SX), y] as P2);
      p.gradFill(panel, NAVY, NAVY_D, light, 0.42);
      p.poly(panel, null, 8);
    }
    for (const s of [-1, 1]) p.poly([[SX + s * 18, shY + 6], [SX + s * 30, shY + 46], [SX + s * 20, shY + 48], [SX + s * 8, shY + 12]], "#a9d2ea", 4);
    p.poly([[SX - 9, shY + 10], [SX + 9, shY + 10], [SX + 14, shY + 92], [SX, shY + 106], [SX - 14, shY + 92]], "#22262e", 5);  // dark tie
    p.ell(SX + 44, shY + 58, 22, 22, "#e8c04a", 6);                          // round "78" chest plate
    caption(p, "78", SX + 44, shY + 58, 24, NAVY_D, 34);
    p.stroke([[SX - 66, hipY - 26], [SX - 40, hipY - 26]], 4, NAVY_D);
    p.stroke([[SX + 66, hipY - 26], [SX + 40, hipY - 26]], 4, NAVY_D);
  } else {
    p.gradFill(torso, "#f6f4ee", "#d9d4c6", light, 0.45);                    // white shirt
    p.poly(torso, null, 10);
    for (const s of [-1, 1]) {                                               // red braces
      p.band([[SX + s * 44, shY - 2], [SX + s * 50, shY + 60], [SX + s * 52, hipY + 2]], "#c03a2e", 22, 5, "butt");
      p.ell(SX + s * 47, shY + 74, 8, 8, "#e8c04a", 3);
    }
    p.band([[SX - 66, hipY + 2], [SX + 66, hipY + 4]], "#c03a2e", 16, 5, "butt");
    p.stroke([[SX, shY + 8], [SX, hipY - 6]], 4, "#d8d2c4");
    for (let i = 0; i < 3; i++) p.dot(SX + 5, shY + 44 + i * 52, 5, "#c9c2b2");
    p.poly([[SX - 12, shY - 2], [SX + 12, shY - 2], [SX + 22, shY + 12], [SX, shY + 22], [SX - 22, shY + 12]], "#2a2130", 6);  // bow tie
    p.poly([[SX - 30, shY + 4], [SX - 12, shY + 12], [SX - 30, shY + 22]], "#2a2130", 5);
    p.poly([[SX + 30, shY + 4], [SX + 12, shY + 12], [SX + 30, shY + 22]], "#2a2130", 5);
  }
  p.rot = null;

  // ---- arms: the fists are placed by the rig, the elbows solve themselves ----
  const shL = R([SX - 52, shY + 16]), shR = R([SX + 52, shY + 16]);
  const body = R([SX, shY + 96]);
  const k = clamp(o.leverP ?? 0, 0, 1), bk = clamp(o.bonusP ?? 0, 0, 1);
  let hL: P2 = [SX - 86, hipY + 4], hR: P2 = [SX + 86, hipY + 4];
  if (bk > 0.001) {                                                          // both fists out wide on the paper's edges
    hL = lerpP([SX - 96, hipY + 8], [SX - 208, 476], sm(bk));
    hR = lerpP([SX + 96, hipY + 8], [SX + 208, 476], sm(bk));
  } else if (o.mode === "lever") {
    hL = [165 - 30 * k, 580];
    hR = [SX + 92, hipY - 8];
  } else if (o.who === "watchman") {
    const mk = clamp(o.mugP ?? 1, 0, 1);
    hR = lerpP([SX + 132, hipY + 34], [SX + 152, shY + 22], sm(mk));
    const fl = sm(1 - mk);
    hL = lerpP([SX - 86, hipY + 4], [SX - 138, shY - 6], fl);
  }
  const arm = (s: P2, h: P2, sleeve: string, sleeveSh: string, cuff: string | null) => {
    const e = elbowOf(s, h, ARM_U, ARM_L, body);
    taper(p, [s, e, h], 30, 22, sleeve, 6);
    if (cuff) {
      const c = lerpP(e, h, 0.86);
      p.poly([[c[0] - 16, c[1] - 12], [c[0] + 16, c[1] - 12], [c[0] + 14, c[1] + 12], [c[0] - 14, c[1] + 12]], cuff, 5);
    }
    const mid = lerpP(s, e, 0.4);
    p.ell(mid[0], mid[1], 20, 17, sleeveSh, 0);
    return e;
  };
  const sleeve = o.who === "driver" ? NAVY : "#f6f4ee", sleeveSh = o.who === "driver" ? NAVY_D : "#dcd6c8";
  arm(shL, hL, sleeve, sleeveSh, o.who === "driver" ? "#cfe6f4" : null);
  arm(shR, hR, sleeve, sleeveSh, o.who === "driver" ? "#cfe6f4" : null);
  if (bk > 0.001) drawCert(p, hL, hR, bk);
  drawHead(p, hx, hy, o, light);
  const fist = (c: P2) => { p.ell(c[0], c[1], 22, 20, HEAD, 7); p.stroke([[c[0] - 12, c[1] - 4], [c[0] + 12, c[1] - 4]], 4, SKIN_SH); };
  fist(hL); fist(hR);
  if (o.who === "watchman" && bk < 0.001) drawMug(p, hR, sm(clamp(o.mugP ?? 1, 0, 1)));
};

// =====================================================================================
// FX cards (unlit 2D sprites)
// =====================================================================================
/** ground contact blob: multiplies the ground under a card (canvas 128 x 128) */
export const fxBlob = (p: Pen, col: string) => {
  const g = p.g;
  g.fillStyle = WHITE; g.fillRect(0, 0, 128, 128);
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  for (const [r, k] of [[0, 0], [0.32, 0.02], [0.5, 0.22], [0.66, 0.58], [0.82, 0.88], [1, 1]] as const) gr.addColorStop(r, mix(col, WHITE, k));
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
};
/** stone / road dust rolling out of a crack, plus chips (canvas 600 x 400) */
export const fxDust = (u: number, big = false) => (p: Pen) => {
  const g = p.g, cx = 300, cy = 320;
  if (u < 0.28) {
    g.save(); g.globalAlpha = 1 - u / 0.28;
    p.poly(star(cx, cy - 30, 130 + 200 * u, 44 + 54 * u, 9), "#fff0bc", 5);
    g.restore();
  }
  g.save(); g.globalAlpha = clamp((1 - u) * 1.5, 0, 1);
  const n = big ? 12 : 8;
  for (let i = 0; i < n; i++) {
    const a = Math.PI + (i / (n - 1)) * Math.PI, r = (56 + 180 * Math.sqrt(u)) * (0.75 + 0.25 * Math.sin(i * 2.3));
    const x = cx + Math.cos(a) * r * 1.3, y = cy + Math.sin(a) * r * 0.5 - 40 * u, s = (30 + 52 * u) * (0.8 + 0.3 * Math.cos(i * 1.7));
    p.ell(x, y, s, s * 0.84, i % 2 ? "#dcd2c0" : "#c4b8a4", 6);
    p.ell(x - s * 0.22, y - s * 0.26, s * 0.42, s * 0.3, "#f2ece0", 0);
  }
  for (let i = 0; i < (big ? 9 : 6); i++) {
    const a = Math.PI * 1.05 + (i / ((big ? 9 : 6) - 1)) * Math.PI * 0.9, r = 70 + 230 * u;
    p.poly(star(cx + Math.cos(a) * r, cy - 30 + Math.sin(a) * r * 0.7 + 150 * u * u, 11, 5, 4, i * 1.3), "#9a9080", 3);
  }
  g.restore();
};
/** brass-on-brass sparks as the lever slams home (canvas 500 x 400) */
export const fxSparks = (u: number) => (p: Pen) => {
  const g = p.g, cx = 250, cy = 300;
  g.save(); g.globalAlpha = clamp((1 - u) * 1.5, 0, 1);
  if (u < 0.34) {
    g.save(); g.globalAlpha = 1 - u / 0.34;
    p.poly(star(cx, cy, 84 + 120 * u, 24 + 20 * u, 8, u * 2), "#ffe27a", 0);
    p.ell(cx, cy, 36 + 48 * u, 24 + 28 * u, "#fffbe6", 0);
    g.restore();
  }
  for (let i = 0; i < 15; i++) {
    const a = Math.PI + 0.18 + (i / 14) * (Math.PI - 0.36), sp = 0.7 + 0.5 * Math.abs(Math.sin(i * 2.7));
    const r0 = 26 + 190 * u * sp, r1 = r0 + 38 + 28 * (1 - u), drop = 170 * u * u;
    taper(p, [[cx + Math.cos(a) * r0, cy + Math.sin(a) * r0 * 0.9 + drop], [cx + Math.cos(a) * r1, cy + Math.sin(a) * r1 * 0.9 + drop]], 9 * (1 - u) + 3, 2, i % 3 ? "#ff9a2a" : "#ffd84a");
  }
  g.restore();
};
