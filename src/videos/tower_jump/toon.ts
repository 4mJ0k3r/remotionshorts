// Tower Jump cast, drawn to SKILL.md section 2 in the 600 x 1000 design box (soles y 952, card pivot y 975):
//   head  - warm cream #fdfaf2 circle, centre (300, 235), HEAD_R 145, #351f22 ink ring; hats rise above y 85
//   torso - compact pear/bean, top y 375, bottom ~590, shoulders ~120 wide, hips ~145 (about 50 % of the head)
//   legs  - straight parallel sticks at x 265 / 335 down to y 945, small #351f22 pill feet 52 x 24 at y 952
//   eyes  - solid #351f22 oval pupils (rx 16, ry 22), NO highlight dots; brows float at eyeY - 34
//   driver   (Albert Gunter): navy peaked cap with a gold badge, light-blue shirt, dark tie, navy vest, "NO. 78" badge
//   watchman (bridge operator): brown flat cap, white shirt, red braces, dark bow tie, a steaming mug
// Continuous inputs (0..1): leverP (fist pushes the throttle forward + torso lean), bonusP (the "£10 BONUS"
// certificate comes up to the chest), mugP (mug raise). cast.ts quantizes every number to 0.02 before drawing.
// The driver's lever fist is the ONLY hand that touches a 3D object; its design point is driverFist() and world.ts
// pins the lever knob under it (SKILL section 3, Rule B). Every other held prop is drawn here on the 2D hands.
import { Pen, INK } from "./pen";

export { Pen, INK };
type P2 = [number, number];

const HEAD = "#fdfaf2", HEAD_SH = "#efe4d0", WHITE = "#ffffff";
export const HEAD_R = 145;
const HX = 300, HY = 235, EYE_DY = 14, EYE_DX = 54, MOUTH_DY = 84;
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
const smoothClosed = (c: P2[], n = 6): P2[] => {
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
/** 2-bone IK: the elbow solution farther from the body centre, so elbows always bend outward */
const elbowOf = (s: P2, h: P2, l1: number, l2: number, away: P2): P2 => {
  const dx = h[0] - s[0], dy = h[1] - s[1], d = Math.hypot(dx, dy) || 1;
  if (d >= l1 + l2 - 1) return [s[0] + dx * 0.5, s[1] + dy * 0.5];
  const a = (l1 * l1 - l2 * l2 + d * d) / (2 * d), hgt = Math.sqrt(Math.max(0, l1 * l1 - a * a));
  const mx = s[0] + (dx * a) / d, my = s[1] + (dy * a) / d;
  const e1: P2 = [mx + (-dy / d) * hgt, my + (dx / d) * hgt], e2: P2 = [mx - (-dy / d) * hgt, my - (dx / d) * hgt];
  return Math.hypot(e1[0] - away[0], e1[1] - away[1]) >= Math.hypot(e2[0] - away[0], e2[1] - away[1]) ? e1 : e2;
};
const txt = (p: Pen, s: string, x: number, y: number, px: number, col: string, weight = 900, fam = "Arial") => {
  const g = p.g; g.save(); g.font = `${weight} ${px}px ${fam}`; g.fillStyle = col; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(s, x, y); g.restore();
};

// ---------------- types ----------------
export type Kind = "driver" | "watchman";
export type Expr = "calmWhistle" | "panicShock" | "determinedGrin" | "proudSmile";
export type Mode = "stand" | "lever" | "proud" | "bonus" | "mug";
export type KidOpts = {
  kind: Kind; expr: Expr; mode: Mode;
  /** 0..1: the screen-left fist pushes the throttle from dx 165 to dx 135 (dy 580) while the torso leans in */
  leverP?: number;
  /** 0..1: the "£10 BONUS" certificate rises from the hips to the chest in both hands */
  bonusP?: number;
  /** 0..1: the watchman's mug rises from the chest toward the chin */
  mugP?: number;
  blink?: number; light?: number; gaze?: number; gazeY?: number; bob?: number;
};
/** design-space centre of the driver's lever fist (the point world.ts pins the 3D knob under) */
export const driverFist = (leverP: number): P2 => [165 - 30 * clamp(leverP, 0, 1), 580];

type Look = { shirt: string; sleeve: string; cuff: string };
const LOOKS: Record<Kind, Look> = {
  driver: { shirt: "#a9cdec", sleeve: "#2b4570", cuff: "#a9cdec" },
  watchman: { shirt: "#f6f4ee", sleeve: "#f6f4ee", cuff: "#e4e0d6" },
};

// ---------------- face ----------------
const pupils = (p: Pen, hx: number, ey: number, px: number, py: number, rx = 16, ry = 22, blink = false) => {
  for (const s of [-1, 1]) {
    const ex = hx + s * EYE_DX;
    if (blink) p.arc(ex, ey + 4, rx + 2, 10, 200, 340, 9);
    else p.ell(ex + px, ey + py, rx, ry, INK, 0);
  }
};
const blush = (p: Pen, hx: number, hy: number) => { for (const s of [-1, 1]) p.ell(hx + s * 92, hy + 60, 24, 13, "#f3b0a4", 0); };
const drawFace = (p: Pen, hx: number, hy: number, o: KidOpts) => {
  const gaze = clamp(o.gaze ?? 0, -1, 1), gy = clamp(o.gazeY ?? 0, -1, 1), px = gaze * 8, py = gy * 6;
  const blink = (o.blink ?? 0) > 0.5, ey = hy + EYE_DY, by = ey - 34, my = hy + MOUTH_DY;
  switch (o.expr) {
    case "calmWhistle": {
      for (const s of [-1, 1]) p.arc(hx + s * EYE_DX, by - 4, 24, 12, 205, 335, 10);         // relaxed raised brows
      pupils(p, hx, ey, px, py, 16, 22, blink);
      blush(p, hx, hy);
      p.ell(hx + 16, my, 15, 13, "#5a1e24", 8);                                               // whistling pucker
      // a little floating note beside the mouth (outside the head, inside the card)
      p.ell(hx + 172, hy + 54, 13, 10, INK, 0); p.stroke([[hx + 183, hy + 52], [hx + 183, hy + 6]], 7); p.stroke([[hx + 183, hy + 6], [hx + 204, hy + 18]], 7);
      return;
    }
    case "panicShock": {
      for (const s of [-1, 1]) p.arc(hx + s * EYE_DX, by - 16, 26, 16, 200, 340, 11);         // high arched brows
      pupils(p, hx, ey, px, py, 18, 26, false);
      p.ell(hx, my + 8, 28, 34, "#4a1a22", 8);                                                // open shocked oval
      p.clip(ellPts(hx, my + 8, 28, 34, 0, 360, 30), () => p.ell(hx, my + 36, 22, 14, "#e0605a", 0));
      p.ell(hx, my + 8, 28, 34, null, 8);
      // blue sweat drop on the temple
      p.poly(smoothClosed([[hx + 120, hy - 70], [hx + 136, hy - 36], [hx + 130, hy - 20], [hx + 110, hy - 20], [hx + 104, hy - 36]], 5), "#7cc8f2", 6);
      return;
    }
    case "determinedGrin": {
      for (const s of [-1, 1]) {
        const ex = hx + s * EYE_DX;
        p.poly([[ex + s * 40, by - 20], [ex - s * 26, by + 10], [ex - s * 22, by + 22], [ex + s * 42, by - 6]], INK, 0); // heavy V brows
        p.stroke([[ex + s * 18, ey - 18], [ex - s * 16, ey], [ex + s * 18, ey + 18]], 12);                        // > <
      }
      const x0 = hx - 64, x1 = hx + 64, y0 = my - 22, y1 = my + 22;
      p.poly(smoothClosed([[x0, y0], [x1, y0], [x1 + 6, my], [x1, y1], [x0, y1], [x0 - 6, my]], 4), WHITE, 8);
      p.stroke([[x0 + 4, my], [x1 - 4, my]], 5);
      for (const t of [-38, -13, 13, 38]) p.stroke([[hx + t, y0 + 4], [hx + t, y1 - 4]], 4);
      return;
    }
    case "proudSmile": {
      for (const s of [-1, 1]) p.stroke([[hx + s * (EYE_DX - 26), by + 2], [hx + s * EYE_DX, by - 10], [hx + s * (EYE_DX + 26), by - 4]], 10); // proud raised brows
      pupils(p, hx, ey, px, py, 16, 22, blink);
      blush(p, hx, hy);
      const m = smoothClosed([[hx - 64, my - 14], [hx, my - 10], [hx + 64, my - 14], [hx + 42, my + 26], [hx, my + 38], [hx - 42, my + 26]], 5);
      p.poly(m, "#5a1e24", 8);
      p.clip(m, () => { p.ell(hx, my + 36, 32, 15, "#e0605a", 0); p.poly([[hx - 66, my - 20], [hx + 66, my - 20], [hx + 58, my + 2], [hx - 58, my + 2]], WHITE, 0); p.stroke([[hx - 58, my + 2], [hx + 58, my + 2]], 4); });
      p.poly(m, null, 8);
      return;
    }
  }
};

// ---------------- head + headgear ----------------
const drawHead = (p: Pen, hx: number, hy: number, o: KidOpts, light: number) => {
  for (const s of [-1, 1]) p.ell(hx + s * 140, hy + 20, 26, 32, HEAD, 9);                      // ears
  const pts = ellPts(hx, hy, HEAD_R, HEAD_R * 0.98, 0, 360, 72);
  p.poly(pts, HEAD, 0);
  p.clip(pts, () => p.ell(hx - Math.cos(light) * 60, hy - Math.sin(light) * 46, HEAD_R * 1.02, HEAD_R, HEAD_SH, 0));
  p.clip(pts, () => p.ell(hx + Math.cos(light) * 20, hy + Math.sin(light) * 16, HEAD_R * 0.96, HEAD_R * 0.94, HEAD, 0));
  p.inkRing(pts, 12, light + Math.PI, 0.35);
  if (o.kind === "driver") {
    const hair = "#5a3a24";
    for (const s of [-1, 1]) p.poly([[hx + s * 128, hy - 62], [hx + s * 142, hy - 10], [hx + s * 120, hy + 6], [hx + s * 112, hy - 40]], hair, 6);
    // navy peaked cap: crown rises to y ~47 (well above the head contour at y 90), band, gold badge, glossy visor
    const navy = "#23395d";
    const crown = smoothClosed([[hx - 152, hy - 108], [hx - 150, hy - 160], [hx - 80, hy - 190], [hx + 80, hy - 190], [hx + 150, hy - 160], [hx + 152, hy - 108]], 6);
    p.gradFill(crown, navy, mul(navy, 0.75), light, 0.4);
    p.poly(crown, null, 10);
    p.stroke([[hx - 120, hy - 170], [hx + 120, hy - 170]], 4, mul(navy, 1.3));
    p.poly([[hx - 148, hy - 122], [hx + 148, hy - 122], [hx + 146, hy - 92], [hx - 146, hy - 92]], "#18263f", 8);
    p.ell(hx, hy - 150, 20, 17, "#e6b93a", 6);
    p.poly(star(hx, hy - 150, 11, 5, 5), "#fff2b0", 0);
    for (const s of [-1, 1]) p.stroke([[hx + s * 22, hy - 152], [hx + s * 44, hy - 158]], 6, "#e6b93a");
    const visor = smoothClosed([[hx - 142, hy - 94], [hx + 142, hy - 94], [hx + 120, hy - 64], [hx, hy - 52], [hx - 120, hy - 64]], 5);
    p.poly(visor, "#141a26", 9);
    p.stroke([[hx - 86, hy - 78], [hx - 10, hy - 70]], 6, "#5a6a86");
  } else {
    const hair = "#9a9a9a";
    for (const s of [-1, 1]) p.poly([[hx + s * 126, hy - 60], [hx + s * 142, hy - 6], [hx + s * 120, hy + 8], [hx + s * 110, hy - 38]], hair, 6);
    const brown = "#7a5232";
    const crown = smoothClosed([[hx - 150, hy - 78], [hx - 132, hy - 150], [hx, hy - 176], [hx + 138, hy - 152], [hx + 158, hy - 84]], 6);
    p.gradFill(crown, brown, mul(brown, 0.75), light, 0.4);
    p.poly(crown, null, 10);
    for (let i = 0; i < 4; i++) p.stroke([[hx - 110 + i * 60, hy - 150 + i * 2], [hx - 90 + i * 60, hy - 96]], 4, mul(brown, 0.8));
    p.poly(smoothClosed([[hx - 120, hy - 84], [hx + 156, hy - 86], [hx + 178, hy - 70], [hx + 30, hy - 60], [hx - 112, hy - 70]], 5), mul(brown, 0.86), 8);
    p.ell(hx + 4, hy - 172, 12, 9, mul(brown, 0.8), 5);
  }
  drawFace(p, hx, hy, o);
};

// ---------------- held props (2D, on the hands) ----------------
const drawCheque = (p: Pen, cx: number, cy: number, s: number) => {
  // 1.4x the base 160 x 100 card: 224 x 140, cream with a green border, "£10" + "BONUS", red-and-gold seal
  const W = 224 * s, H = 140 * s, x0 = cx - W / 2, y0 = cy - H / 2, g = p.g;
  p.poly([[x0, y0], [x0 + W, y0], [x0 + W, y0 + H], [x0, y0 + H]], "#f6efd8", 7);
  g.save(); g.strokeStyle = "#2f7a4a"; g.lineWidth = 6 * s; g.strokeRect(x0 + 9 * s, y0 + 9 * s, W - 18 * s, H - 18 * s); g.restore();
  p.poly([[x0 + 14 * s, y0 + 14 * s], [x0 + 100 * s, y0 + 14 * s], [x0 + 100 * s, y0 + H - 14 * s], [x0 + 14 * s, y0 + H - 14 * s]], "#2f7a4a", 0);
  txt(p, "£10", x0 + 57 * s, cy + 2 * s, 46 * s, "#f6efd8");
  txt(p, "LONDON TRANSPORT", x0 + 162 * s, y0 + 30 * s, 11 * s, "#2f7a4a", 800);
  txt(p, "BONUS", x0 + 158 * s, cy + 4 * s, 26 * s, "#1f5a36");
  // ribbon seal on the lower right corner
  const sx = x0 + W - 22 * s, sy = y0 + H - 14 * s;
  for (const k of [-1, 1]) p.poly([[sx + k * 6 * s, sy], [sx + k * 16 * s, sy + 30 * s], [sx + k * 4 * s, sy + 24 * s]], "#c23a2e", 4);
  p.poly(star(sx, sy, 20 * s, 15 * s, 12, 0), "#e6b93a", 5);
  p.ell(sx, sy, 10 * s, 10 * s, "#c23a2e", 0);
};
const drawMug = (p: Pen, c: P2, tilt: number) => {
  const g = p.g;
  g.save(); g.translate(c[0], c[1]); g.rotate(tilt); g.translate(-c[0], -c[1]);
  const [x, y] = c;
  p.ell(x + 30, y + 2, 16, 18, null, 10);                                                // handle
  p.ell(x + 30, y + 2, 16, 18, null, 0);
  g.save(); g.strokeStyle = WHITE; g.lineWidth = 6; g.beginPath(); g.ellipse(x + 30, y + 2, 16, 18, 0, 0, Math.PI * 2); g.stroke(); g.restore();
  p.poly([[x - 28, y - 30], [x + 28, y - 30], [x + 26, y + 32], [x - 26, y + 32]], WHITE, 8);
  p.ell(x, y - 30, 28, 8, "#6a3a1e", 6);
  p.stroke([[x - 22, y + 4], [x + 22, y + 4]], 5, "#c9d6e2");
  g.restore();
  // steam wisps rise straight up (not tilted)
  g.save(); g.globalAlpha = 0.75;
  for (const k of [-1, 1]) p.stroke([[x + k * 10, y - 44], [x + k * 18, y - 64], [x + k * 6, y - 84], [x + k * 16, y - 104]], 6, "#e8eef2");
  g.restore();
};

// ---------------- the figure ----------------
export const drawKid = (p: Pen, o: KidOpts) => {
  const lk = LOOKS[o.kind], light = o.light ?? -2.3, mode = o.mode;
  const gaze = clamp(o.gaze ?? 0, -1, 1), gazeY = clamp(o.gazeY ?? 0, -1, 1);
  const bob = mode === "lever" ? 0 : o.bob ?? 0;
  const lv = mode === "lever" ? clamp(o.leverP ?? 0, 0, 1) : 0;
  const lean = -0.06 * sm(lv);                                                            // lean into the throttle
  const piv: P2 = [HX, 585];
  const R = (pt: P2) => rotAbout(pt, lean, piv);
  const hx = HX + gaze * 10, hy = HY + bob + gazeY * 6;
  const shY = 375 + bob;

  // ---- legs: straight parallel sticks, small dark pill feet ----
  for (const s of [-1, 1]) {
    const x = HX + s * 35;
    taper(p, [[x, 572], [x, 940]], 20, 17, INK);
    p.ell(x + s * 6, 940, 26, 12, INK, 0);
  }

  // ---- torso + head, leaned about the hip ----
  const g = p.g;
  g.save(); g.translate(piv[0], piv[1]); g.rotate(lean); g.translate(-piv[0], -piv[1]);
  const torso = smoothClosed([[HX - 58, shY + 4], [HX, shY - 4], [HX + 58, shY + 4], [HX + 66, shY + 50], [HX + 70, shY + 130],
    [HX + 74, shY + 186], [HX + 54, shY + 214], [HX, shY + 220], [HX - 54, shY + 214], [HX - 74, shY + 186], [HX - 70, shY + 130], [HX - 66, shY + 50]], 6);
  p.gradFill(torso, lk.shirt, mul(lk.shirt, 0.82), light, 0.35);
  if (o.kind === "driver") {
    const navy = "#2b4570";
    p.clip(torso, () => {
      // navy vest everywhere except the V that shows the shirt and tie
      p.poly([[HX - 90, shY - 10], [HX - 22, shY - 10], [HX, shY + 96], [HX + 22, shY - 10], [HX + 90, shY - 10], [HX + 90, shY + 240], [HX - 90, shY + 240]], navy, 0);
      p.poly([[HX - 90, shY + 200], [HX + 90, shY + 200], [HX + 90, shY + 240], [HX - 90, shY + 240]], mul(navy, 0.8), 0);
    });
    p.stroke([[HX - 22, shY - 6], [HX, shY + 96], [HX + 22, shY - 6]], 6);
    for (const s of [-1, 1]) p.poly([[HX + s * 4, shY + 2], [HX + s * 30, shY - 2], [HX + s * 16, shY + 26]], "#c6dff3", 5);   // collar points
    p.poly([[HX - 9, shY + 6], [HX + 9, shY + 6], [HX + 7, shY + 20], [HX - 7, shY + 20]], "#1f2430", 4);                        // tie knot
    p.poly([[HX - 7, shY + 20], [HX + 7, shY + 20], [HX + 12, shY + 78], [HX, shY + 92], [HX - 12, shY + 78]], "#1f2430", 4);
    for (let i = 0; i < 3; i++) p.dot(HX, shY + 118 + i * 30, 6, "#c9a24a");
    // chest pocket with the silver "NO. 78" badge (screen right)
    p.poly([[HX + 22, shY + 70], [HX + 62, shY + 70], [HX + 62, shY + 112], [HX + 22, shY + 112]], null, 4);
    p.ell(HX + 42, shY + 58, 22, 22, "#d6dbe2", 5);
    p.ell(HX + 42, shY + 58, 15, 15, null, 3);
    txt(p, "NO.", HX + 42, shY + 50, 9, "#2a2226", 900);
    txt(p, "78", HX + 42, shY + 63, 14, "#2a2226", 900);
  } else {
    p.clip(torso, () => p.poly([[HX - 90, shY + 196], [HX + 90, shY + 196], [HX + 90, shY + 240], [HX - 90, shY + 240]], "#5a4632", 0)); // trousers
    for (const s of [-1, 1]) {
      p.band([[HX + s * 34, shY + 2], [HX + s * 36, shY + 110], [HX + s * 34, shY + 206]], "#c8322a", 13, 4);                      // red braces
      p.poly([[HX + s * 28, shY + 186], [HX + s * 42, shY + 186], [HX + s * 42, shY + 198], [HX + s * 28, shY + 198]], "#d8c070", 3);
    }
    for (let i = 0; i < 3; i++) p.dot(HX, shY + 60 + i * 40, 5, "#bdb6a6");
    for (const s of [-1, 1]) p.poly([[HX, shY + 14], [HX + s * 30, shY + 2], [HX + s * 30, shY + 28]], "#1f2430", 4);                 // bow tie
    p.ell(HX, shY + 15, 8, 8, "#1f2430", 0);
  }
  p.poly(torso, null, 11);
  drawHead(p, hx, hy, o, light);
  g.restore();

  // ---- arms: shoulders follow the lean, hands are placed in card space ----
  const shL = R([HX - 56, shY + 22]), shR = R([HX + 56, shY + 22]);
  let hL: P2 = [HX - 78, 600], hR: P2 = [HX + 78, 600];
  let openR = false, mug: { c: P2; tilt: number } | null = null, cheque: { c: P2; s: number } | null = null;
  const hipL: P2 = [HX - 74, 548], hipR: P2 = [HX + 74, 548];
  if (mode === "lever") { hL = driverFist(lv); hR = hipR; }
  else if (mode === "proud") { hL = hipL; hR = hipR; }
  else if (mode === "bonus") {
    const k = clamp(o.bonusP ?? 0, 0, 1), up = sm(k), sc = lerp(0.35, 1, sm(k / 0.45));
    const c = lerpP([HX, 590], [HX, 470], up), W = 224 * sc;
    cheque = { c, s: sc };
    const grip = sm(k / 0.3);
    hL = lerpP(hipL, [c[0] - W / 2 - 16, c[1] + 12], grip); hR = lerpP(hipR, [c[0] + W / 2 + 16, c[1] + 12], grip); // fists pinch the edges, clear of the text
  } else if (mode === "mug") {
    const panic = o.expr === "panicShock";
    const c = lerpP([HX - 50, 500], [HX - 40, 450], sm(o.mugP ?? 0));
    mug = { c, tilt: panic ? -0.42 : 0 };
    hL = [c[0] - 30, c[1] + 6];
    if (panic) { hR = [HX + 172, 300]; openR = true; }
  }
  const body = R([HX, shY + 100]);
  const arm = (s: P2, h: P2) => {
    const e = elbowOf(s, h, 114, 114, body);
    taper(p, [s, e, h], 34, 26, lk.sleeve, 6);
    const cuff = lerpP(e, h, 0.8);
    p.ell(cuff[0], cuff[1], 16, 14, lk.cuff, 5);
  };
  arm(shL, hL);
  arm(shR, hR);
  if (cheque) drawCheque(p, cheque.c[0], cheque.c[1], cheque.s);
  if (mug) drawMug(p, mug.c, mug.tilt);
  const fist = (c: P2, open: boolean) => {
    p.ell(c[0], c[1], 23, 21, INK, 0);
    p.ell(c[0] - 7, c[1] - 8, 7, 5, "#6a5054", 0);
    if (open) for (let i = 0; i < 4; i++) {
      const a = rad(-90 + 12 + (-40 + i * 24));
      taper(p, [[c[0] + Math.cos(a) * 10, c[1] + Math.sin(a) * 10], [c[0] + Math.cos(a) * 46, c[1] + Math.sin(a) * 46]], 14, 11, INK);
    }
  };
  fist(hL, false);
  fist(hR, openR);
};

// =====================================================================================
// FX cards
// =====================================================================================
export const fxBlob = (p: Pen, col: string) => {
  const g = p.g;
  g.fillStyle = WHITE; g.fillRect(0, 0, 128, 128);
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  for (const [r, k] of [[0, 0], [0.32, 0.02], [0.5, 0.22], [0.66, 0.58], [0.82, 0.88], [1, 1]] as const) gr.addColorStop(r, mix(col, WHITE, k));
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
};
/** dust / steam burst: star flash, puffs rolling outward, debris (canvas 600 x 400) */
export const fxImpact = (u: number, big = false) => (p: Pen) => {
  const g = p.g, cx = 300, cy = 300;
  if (u < 0.3) { g.save(); g.globalAlpha = 1 - u / 0.3; p.poly(star(cx, cy - 40, 150 + 220 * u, 50 + 60 * u, 9), "#fff3b0", 6); g.restore(); }
  g.save(); g.globalAlpha = clamp((1 - u) * 1.6, 0, 1);
  const n = big ? 11 : 8;
  for (let i = 0; i < n; i++) {
    const a = Math.PI + (i / (n - 1)) * Math.PI, r = (60 + 170 * Math.sqrt(u)) * (0.75 + 0.25 * Math.sin(i * 2.3));
    const x = cx + Math.cos(a) * r * 1.25, y = cy + Math.sin(a) * r * 0.55, s = (34 + 46 * u) * (0.8 + 0.3 * Math.cos(i * 1.7));
    p.ell(x, y, s, s * 0.82, i % 2 ? "#ecdfca" : "#d9c6a6", 6);
    p.ell(x - s * 0.25, y - s * 0.25, s * 0.4, s * 0.3, "#f8f0e2", 0);
  }
  for (let i = 0; i < 7; i++) { const a = Math.PI * 1.1 + (i / 6) * Math.PI * 0.8, r = 80 + 220 * u; p.poly(star(cx + Math.cos(a) * r, cy - 20 + Math.sin(a) * r * 0.8 + 140 * u * u, 10, 5, 4, i), "#6a5a4a", 3); }
  g.restore();
};
/** orange spark burst: hot core flash + streaks flying up and out (canvas 500 x 400) */
export const fxSparks = (u: number) => (p: Pen) => {
  const g = p.g, cx = 250, cy = 300;
  g.save(); g.globalAlpha = clamp((1 - u) * 1.5, 0, 1);
  if (u < 0.35) { g.save(); g.globalAlpha = 1 - u / 0.35; p.poly(star(cx, cy, 90 + 120 * u, 26 + 20 * u, 8, u * 2), "#ffe27a", 0); p.ell(cx, cy, 40 + 50 * u, 26 + 30 * u, "#fffbe6", 0); g.restore(); }
  for (let i = 0; i < 16; i++) {
    const a = Math.PI + 0.15 + (i / 15) * (Math.PI - 0.3), sp = 0.7 + 0.5 * Math.abs(Math.sin(i * 2.7));
    const r0 = 30 + 200 * u * sp, r1 = r0 + 40 + 30 * (1 - u), drop = 160 * u * u;
    taper(p, [[cx + Math.cos(a) * r0, cy + Math.sin(a) * r0 * 0.9 + drop], [cx + Math.cos(a) * r1, cy + Math.sin(a) * r1 * 0.9 + drop]], 9 * (1 - u) + 3, 2, i % 3 ? "#ff9a2a" : "#ffd84a");
  }
  g.restore();
};
