// Coaster cast: flat 2D cards in the 600 x 1000 design space (soles at y 952, card pivot at the feet).
// Large round cream-white head (#fdfaf2) with a thick, slightly varying #351f22 ink ring, so every expression reads
// against the face. Thin dark tapered stick limbs, dark rounded hands and shoes.
//   builder - red cap with a brown fringe, yellow short-sleeve shirt, blue denim overalls (two straps, yellow
//             buttons, red/white checkered pocket patch).
//   rival   - slicked-back dark brown hair with a widow's peak and sideburns, cream vest over a dark shirt, gold tie
//             and a gold chain, dark trousers.
// Animation is continuous, never a pose switch: swingP (hammer arc), walletP (wallet out + open), pointP (rival's
// gesture) and waveP (waving hand phase) are 0..1 inputs; cast.ts rounds them to 2 decimals for the canvas key.
// Held props (hammer, wallet) are drawn on the 2D hands, never as separate 3D meshes.
import { Pen, INK, handEllPts, wobbleContour } from "./shaders/pen";

export { Pen, INK, handEllPts };
export type P2 = [number, number];

export const HEAD = "#fdfaf2", HEAD_SH = "#eee3cf";
const LIMB = INK, WHITE = "#ffffff";
const HEAD_R0 = 120;            // base frame the head/face are drawn in
export const HEAD_R = 145;             // on-card head radius (v2: bigger head)
const HS = HEAD_R / HEAD_R0;
const WALLET_S = 1.45;           // open wallet scale (v2)
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
/** tapered stroke along a polyline, optional ink rim (ol > 0) */
export const taper = (p: Pen, pts: P2[], w0: number, w1: number, col: string, ol = 0) => {
  // Subdivide with endpoint-pinned low-frequency normal wobble: shoulders, elbows
  // and contact fists remain exact while the drawn contour carries brush pressure.
  const samples: P2[]=[];
  for(let i=1;i<pts.length;i++) {
    const a=pts[i-1],b=pts[i],dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy)||1,n=Math.max(2,Math.ceil(len/12));
    for(let j=0;j<n;j++) {const t=j/n,w=0.85*Math.sin(Math.PI*t)*Math.sin(t*2*Math.PI+0.6+i);samples.push([lerp(a[0],b[0],t)-dy/len*w,lerp(a[1],b[1],t)+dx/len*w]);}
  }
  samples.push(pts[pts.length-1]);pts=samples;
  const width=(u:number,extra:number)=>(lerp(w0,w1,u)+extra)*(1+0.065*Math.sin(3*Math.PI*u+1.1)+0.035*Math.cos(5*Math.PI*u-0.7));
  const L: number[] = [0];
  for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const T = L[L.length - 1] || 1;
  const pass = (extra: number, c: string) => {
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i], wa = width(L[i - 1] / T,extra), wb = width(L[i] / T,extra);
      let nx = b[1] - a[1], ny = a[0] - b[0]; const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
      p.poly([[a[0] + nx * wa / 2, a[1] + ny * wa / 2], [b[0] + nx * wb / 2, b[1] + ny * wb / 2], [b[0] - nx * wb / 2, b[1] - ny * wb / 2], [a[0] - nx * wa / 2, a[1] - ny * wa / 2]], c, 0);
    }
    pts.forEach((q, i) => p.dot(q[0], q[1], width(L[i] / T,extra) / 2, c));
  };
  if (ol > 0) pass(ol * 2, INK);
  pass(0, col);
};
/** 2-bone IK: of the two elbow solutions for shoulder s -> hand h, the one farther from `away` (the body centre),
 *  so elbows always bend outward and never fold across the chest or face */
export const elbowOf = (s: P2, h: P2, l1: number, l2: number, away: P2): P2 => {
  const dx = h[0] - s[0], dy = h[1] - s[1], d = Math.hypot(dx, dy);
  if (d < 0.000001) {
    const ax = s[0] - away[0], ay = s[1] - away[1], n = Math.hypot(ax, ay) || 1;
    return [s[0] + (ax || (ay ? 0 : -1)) * l1 / n, s[1] + ay * l1 / n];
  }
  // Unreachable targets extend along the target ray with the correct upper-bone length.
  if (d >= l1 + l2) return [s[0] + dx * l1 / d, s[1] + dy * l1 / d];
  const a = (l1 * l1 - l2 * l2 + d * d) / (2 * d), hgt = Math.sqrt(Math.max(0, l1 * l1 - a * a));
  const mx = s[0] + (dx * a) / d, my = s[1] + (dy * a) / d;
  const e1: P2 = [mx + (-dy / d) * hgt, my + (dx / d) * hgt], e2: P2 = [mx - (-dy / d) * hgt, my - (dx / d) * hgt];
  return Math.hypot(e1[0] - away[0], e1[1] - away[1]) >= Math.hypot(e2[0] - away[0], e2[1] - away[1]) ? e1 : e2;
};

// ---------------- types ----------------
export const SU = 0.00216;
export const PIV = 975;
export type Kind = "builder" | "rival" | "studentHero" | "crush" | "plaidHero" | "mom";
export type Expr = "neutral" | "strainGrin" | "happyProud" | "brokeSad" | "evilSmirk" | "panicShock" | "shyBlush" | "gentleConcern" | "warmMusic" | "emotionalTears" | "prayerUp" | "flirtyWink" | "blissKiss" | "suspicious";
export type Mode = "stand" | "walk" | "run" | "sit" | "hug" | "wave" | "swing" | "hammerHold" | "wallet" | "point" | "phone" | "fixHair" | "stomachGrowl" | "comfort" | "writePalm" | "palmShow" | "prayer" | "kissPalm" | "toiletSit" | "pressFlush" | "sofaPhone" | "knockDoor" | "peekDoor" | "liftMug";
export type KidOpts = {
  kind: Kind; expr: Expr; mode: Mode;
  shirtColor?: string; outfitStyle?: "jacket" | "top"; pupilScale?: number;
  flushP?: number; lowerP?: number; knockP?: number; peekP?: number; mugP?: number;
  /** 0 wind-up high left, .35 overhead, .5 smash in front of the feet, 1 resting vertical on the ground */
  swingP?: number;
  /** 0 pulling the wallet out of the pocket, 1 fully open in front of the chest */
  walletP?: number;
  /** 0 arm down, 1 arm out gesturing at the blueprint (screen left); the other hand stays on the hip */
  pointP?: number;
  /** rival "point" pose: design-space centre of the screen-left fist on the winch lever knob */
  gripX?: number; gripY?: number;
  /** waving hand phase 0..1 */
  waveP?: number;
  /** how far the waving arm is raised (1 = up, 0 = hanging at the pocket) */
  raiseP?: number;
  /** Continuous action weight, 0 = relaxed, 1 = full action. */
  actionP?: number; walkP?: number; runP?: number; sitP?: number; hugP?: number;
  phoneP?: number; fixHairP?: number; growlP?: number; comfortP?: number;
  writePalmP?: number; palmP?: number; prayerP?: number; kissPalmP?: number;
  /** Audio envelope amplitude, clamped and quantized to 0.2. */
  talk?: number;
  /** Partner direction and split layers support readable inter-character overlaps. */
  partnerSide?: number; drawLayer?: "all" | "body" | "arms"; palmScale?: number;
  lean?: number; handLX?: number; handLY?: number; handRX?: number; handRY?: number;
  palmText?: string; rainDrops?: number; heartBeatP?: number;
  blink?: number; light?: number; gaze?: number; gazeY?: number; bob?: number; sweat?: number;
};

type Look = { shirt: string; body: string; bodySh: string; legs: string; shoes: string };
const LOOKS: Record<Kind, Look> = {
  plaidHero: {shirt:"#3a9d5d",body:"#3a9d5d",bodySh:"#246a3c",legs:LIMB,shoes:"#351f22"},
  mom: {shirt:"#e05a8a",body:"#e05a8a",bodySh:"#b83866",legs:"#552e4a",shoes:"#351f22"},
  studentHero: { shirt: "#f4b942", body: "#f4b942", bodySh: "#ca8c25", legs: LIMB, shoes: "#2a1a1c" },
  crush: { shirt: "#ff6b6b", body: "#ffffff", bodySh: "#eee3cf", legs: "#243b60", shoes: "#ffffff" },
  builder: { shirt: "#f5c22e", body: "#3b6ea5", bodySh: "#2c5584", legs: LIMB, shoes: "#2a1a1c" },
  rival: { shirt: "#2b2730", body: "#f1e6cc", bodySh: "#d8c8a6", legs: "#2a2430", shoes: "#20151a" },
};

// ---------------- hammer swing keys ----------------
type SwingKey = { p: number; hand: P2; ang: number; lean: number; crouch: number };
const SWING: SwingKey[] = [
  // every key keeps the steel head inside the 600 x 1000 card (head = hand + HAMMER_L along ang)
  { p: 0.0, hand: [140, 330], ang: -122, lean: -0.08, crouch: 6 },
  { p: 0.2, hand: [186, 250], ang: -96, lean: -0.04, crouch: 0 },
  { p: 0.35, hand: [300, 214], ang: -40, lean: 0.02, crouch: 0 },
  { p: 0.5, hand: [400, 700], ang: 65, lean: 0.14, crouch: 30 },
  { p: 0.65, hand: [430, 690], ang: 80, lean: 0.06, crouch: 16 },
  { p: 1.0, hand: [452, 690], ang: 90, lean: 0.0, crouch: 0 },
];
const swingAt = (p: number): SwingKey => {
  const u = clamp(p, 0, 1);
  let i = 0; while (i + 1 < SWING.length - 1 && u > SWING[i + 1].p) i++;
  const a = SWING[i], b = SWING[i + 1], k = sm((u - a.p) / (b.p - a.p));
  return { p: u, hand: lerpP(a.hand, b.hand, k), ang: lerp(a.ang, b.ang, k), lean: lerp(a.lean, b.lean, k), crouch: lerp(a.crouch, b.crouch, k) };
};
const HAMMER_L = 212;
const drawHammer = (p: Pen, grip: P2, angDeg: number) => {
  const a = rad(angDeg), dx = Math.cos(a), dy = Math.sin(a);
  const end: P2 = [grip[0] - dx * 30, grip[1] - dy * 30], head: P2 = [grip[0] + dx * HAMMER_L, grip[1] + dy * HAMMER_L];
  taper(p, [end, head], 22, 20, "#b47a44", 5);
  p.stroke([[lerp(end[0], head[0], 0.15), lerp(end[1], head[1], 0.15)], [lerp(end[0], head[0], 0.8), lerp(end[1], head[1], 0.8)]], 4, "#d9a066");
  // steel head block, perpendicular to the handle
  const nx = -dy, ny = dx, hw = 50, hd = 30;
  const c = (s: number, t: number): P2 => [head[0] + nx * s + dx * t, head[1] + ny * s + dy * t];
  p.poly([c(-hw, -hd), c(hw, -hd), c(hw, hd), c(-hw, hd)], "#6f7d8c", 7);
  p.poly([c(-hw + 8, -hd + 6), c(hw - 8, -hd + 6), c(hw - 8, -hd + 16), c(-hw + 8, -hd + 16)], "#a9b6c4", 0);
  for (const s of [-1, 1]) p.poly([c(s * hw, -hd - 4), c(s * (hw + 10), -hd), c(s * (hw + 10), hd), c(s * hw, hd + 4)], "#55606c", 5);
};

// ---------------- wallet ----------------
const drawWallet = (p: Pen, cx: number, cy: number, open: number) => {
  const W = 66, H = 80, k = clamp(open, 0, 1);
  const brown = "#7a4a2a", dark = "#5a3420", inner = "#a0683e";
  // right leaf (always facing us), spine at cx
  p.poly([[cx, cy - H / 2], [cx + W, cy - H / 2 + 2], [cx + W, cy + H / 2 - 2], [cx, cy + H / 2]], k > 0.15 ? inner : brown, 6);
  if (k > 0.15) {
    // empty card slots + an empty money pocket
    for (let i = 0; i < 3; i++) p.stroke([[cx + 8, cy - 22 + i * 16], [cx + W - 8, cy - 22 + i * 16]], 4, dark);
    p.poly([[cx + 6, cy + 16], [cx + W - 6, cy + 16], [cx + W - 6, cy + H / 2 - 8], [cx + 6, cy + H / 2 - 8]], mul(inner, 0.85), 3);
  } else {
    p.stroke([[cx + 6, cy - H / 2 + 8], [cx + W - 6, cy - H / 2 + 8]], 3, "#c8955c");
  }
  // left leaf swings open about the spine
  const lw = W * k;
  if (lw > 4) {
    p.poly([[cx, cy - H / 2], [cx - lw, cy - H / 2 + 2 + 6 * (1 - k)], [cx - lw, cy + H / 2 - 2 - 6 * (1 - k)], [cx, cy + H / 2]], k > 0.4 ? inner : brown, 6);
    if (k > 0.55) {
      // the tiny photo card in the left window
      const x0 = cx - lw + 10, x1 = cx - 10, y0 = cy - 26, y1 = cy + 18;
      p.poly([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], WHITE, 3);
      p.poly([[x0 + 5, y0 + 5], [x1 - 5, y0 + 5], [x1 - 5, y1 - 5], [x0 + 5, y1 - 5]], "#9fd0f5", 0);
      p.ell((x0 + x1) / 2, y0 + 17, 7, 7, HEAD, 2);
      p.poly([[(x0 + x1) / 2 - 10, y1 - 5], [(x0 + x1) / 2 + 10, y1 - 5], [(x0 + x1) / 2 + 6, y0 + 26], [(x0 + x1) / 2 - 6, y0 + 26]], "#d93a2e", 0);
    }
  }
  p.stroke([[cx, cy - H / 2], [cx, cy + H / 2]], 6, dark);
};

// ---------------- face ----------------
const drawBaseFace = (p: Pen, hx: number, hy: number, o: KidOpts) => {
  const e = o.expr, gaze = clamp(o.gaze ?? 0, -1, 1), gy = clamp(o.gazeY ?? 0, -1, 1);
  const lid = clamp(o.blink ?? 0, 0, 1), blink = lid >= 0.95;
  const dx = 46, ey = hy + 8, my = hy + 66, px = gaze * 9, py = gy * 8;
  const S = [-1, 1];
  if (e === "strainGrin") {
    for (const s of S) {
      const ex = hx + s * dx;
      // > <  squint: the point of each chevron aims at the nose
      p.stroke([[ex - s * 18, ey - 17], [ex + s * 16, ey], [ex - s * 18, ey + 17]], 11);
      p.stroke([[ex - s * 30, ey - 44], [ex + s * 18, ey - 32]], 11);
    }
    p.ell(hx - 82, my - 6, 20, 11, "#f3b9a8", 0); p.ell(hx + 82, my - 6, 20, 11, "#f3b9a8", 0);
    const x0 = hx - 60, x1 = hx + 60, y0 = my - 22, y1 = my + 24;
    p.poly(smoothClosed([[x0, y0], [x1, y0], [x1 + 4, (y0 + y1) / 2], [x1, y1], [x0, y1], [x0 - 4, (y0 + y1) / 2]], 4), WHITE, 8);
    p.stroke([[x0 + 4, my + 1], [x1 - 4, my + 1]], 5);
    for (const t of [-36, -12, 12, 36]) p.stroke([[hx + t, y0 + 4], [hx + t, y1 - 4]], 4);
    return;
  }
  if (e === "happyProud") {
    for (const s of S) {
      const ex = hx + s * dx;
      // floating raised brows + solid dark oval pupils straight on the white face (no sclera, no shine)
      p.arc(ex, ey - 50, 22, 11, 205, 335, 9);
      if (blink) { p.arc(ex, ey + 4, 18, 12, 200, 340, 10); continue; }
      p.ell(ex + px, ey + py, 13, 20 * (1 - lid), INK, 0);
    }
    p.ell(hx - 84, my - 8, 22, 12, "#f3b0a4", 0); p.ell(hx + 84, my - 8, 22, 12, "#f3b0a4", 0);
    const m = smoothClosed([[hx - 50, my - 14], [hx, my - 10], [hx + 50, my - 14], [hx + 32, my + 24], [hx, my + 34], [hx - 32, my + 24]], 5);
    p.poly(m, "#5a1e24", 8);
    p.clip(m, () => {
      p.ell(hx, my + 32, 28, 14, "#e0605a", 0);
      // crisp white top teeth
      p.poly([[hx - 54, my - 18], [hx + 54, my - 18], [hx + 46, my + 4], [hx - 46, my + 4]], WHITE, 0);
      p.stroke([[hx - 46, my + 4], [hx + 46, my + 4]], 4);
    });
    p.poly(m, null, 8);
    return;
  }
  if (e === "brokeSad") {
    for (const s of S) {
      const ex = hx + s * dx;
      // - -  heavy flat lids drooping at the outer ends, the pupils peeking under them, looking down
      p.stroke([[ex - s * 28, ey - 46], [ex + s * 20, ey - 58]], 9);
      // solid dark pupil cut flat by the heavy lid, looking down
      p.clip([[ex - 30, ey - 2 + (s < 0 ? 6 : -2)], [ex + 30, ey - 2 + (s < 0 ? -2 : 6)], [ex + 30, ey + 40], [ex - 30, ey + 40]], () => {
        p.ell(ex + px, ey + 6 + Math.max(0, py) * 0.5, 14, 16 * (1 - lid), INK, 0);
      });
      p.stroke([[ex - 30, ey - 2 + (s < 0 ? 6 : -2)], [ex + 30, ey - 2 + (s < 0 ? -2 : 6)]], 11);
      p.arc(ex, ey + 24, 16, 6, 20, 160, 3, mul(HEAD_SH, 0.85));
    }
    p.stroke([[hx - 32, my + 8], [hx + 32, my + 8]], 9);
    return;
  }
  if (e === "evilSmirk") {
    for (const s of S) {
      const ex = hx + s * dx;
      // heavy brows slashing down to the nose
      p.poly([[ex - s * 36, ey - 56], [ex + s * 26, ey - 30], [ex + s * 22, ey - 18], [ex - s * 34, ey - 42]], INK, 0);
      if (blink) { p.stroke([[ex - 22, ey + 4], [ex + 22, ey + 2]], 9); continue; }
      // sly side-glance: a solid dark half-oval pupil slid to the side, cut flat by the lid line
      p.clip([[ex - 34, ey - 5], [ex + 34, ey - 8], [ex + 34, ey + 30], [ex - 34, ey + 30]], () => p.ell(ex - 10 + px, ey + 2, 14, 15 * (1 - lid), INK, 0));
      p.stroke([[ex - 30, ey - 5], [ex + 30, ey - 8]], 9);
    }
    // sharp-toothed smirk, the right corner pulled up
    const m: P2[] = [[hx - 40, my + 2], [hx - 6, my + 10], [hx + 48, my - 18], [hx + 38, my - 4], [hx + 4, my + 24], [hx - 34, my + 12]];
    p.poly(m, "#4a1a22", 7);
    p.clip(m, () => {
      const teeth: P2[] = [];
      for (let i = 0; i <= 8; i++) {
        const t = i / 8, x = lerp(hx - 40, hx + 48, t), y = lerp(my + 2, my - 18, t * t) + (t < 0.4 ? t * 20 : 8 - (t - 0.4) * 12);
        teeth.push([x, y - 6], [x + 5.5, y + (i % 2 ? 10 : 14)]);
      }
      teeth.push([hx + 50, my - 30], [hx - 42, my - 12]);
      p.poly(teeth, WHITE, 0);
    });
    p.poly(m, null, 7);
    p.stroke([[hx + 44, my - 16], [hx + 56, my - 24]], 6);
    return;
  }
  // neutral
  for (const s of S) {
    const ex = hx + s * dx;
    if (blink) p.stroke([[ex - 14, ey], [ex + 14, ey]], 8);
    else p.ell(ex + px, ey + py, 11, 15 * (1 - lid), INK, 0);
  }
  p.arc(hx, my - 6, 24, 14, 20, 160, 8);
};

/** Solid pupils and continuous eyelids; mouth animation shares the expression's face frame. */
export const drawFace = (p: Pen, hx: number, hy: number, o: KidOpts) => {
  const talk = Math.round(clamp(o.talk ?? 0, 0, 1) * 5) / 5;
  const blink = clamp(o.blink ?? 0, 0, 1);
  const base = ["neutral", "happyProud", "strainGrin", "brokeSad", "evilSmirk"].includes(o.expr);
  const eyes = () => {
    if (base) { drawBaseFace(p, hx, hy, o); return; }
    const e = o.expr, ey = hy + 8, px = clamp(o.gaze ?? 0, -1, 1) * 9, py = clamp(o.gazeY ?? (e === "prayerUp" ? -0.8 : 0), -1, 1) * 8;
    for (const side of [-1, 1]) {
      const x = hx + side * 46;
      const closed = e === "blissKiss" || e === "warmMusic" || (e === "flirtyWink" && side === 1);
      if (closed) p.arc(x, ey, 18, 10, 20, 160, 8);
      else if (blink >= 0.95) p.stroke([[x - 15, ey], [x + 15, ey]], 8);
      else p.ell(x + px, ey + py, e === "panicShock" ? 16*(o.pupilScale??1) : 13, (e === "panicShock" ? 26*(o.pupilScale??1) : 20) * (1 - blink), INK, 0);
      const concern = e === "gentleConcern" || e === "emotionalTears";
      if(e==="suspicious"&&side===-1)p.arc(x,ey-48,25,12,200,340,9);
      p.stroke([[x - side * 22, ey - (concern ? 50 : 43)], [x + side * 20, ey - 35]], 8);
      if (e === "emotionalTears") taper(p, [[x, ey + 26], [x + side * 6, ey + 69]], 13, 8, "#65bde9");
    }
    if (e === "panicShock") p.ell(hx, hy + 66, 23, 29, "#5a1e24", 7);
    else if (e === "blissKiss") p.stroke([[hx - 10, hy + 60], [hx + 7, hy + 67], [hx - 10, hy + 74]], 7);
    else p.arc(hx, hy + 54, 25, 15, e === "gentleConcern" ? 200 : 20, e === "gentleConcern" ? 340 : 160, 7);
  };
  // Mouth-free eye region avoids repainting over the directional cream crescent.
  p.clip([[hx - 120, hy - 100], [hx + 120, hy - 100], [hx + 120, hy + 36], [hx - 120, hy + 36]], eyes);
  if (talk > 0) {
    p.ell(hx, hy + 66, 17 + talk * 13, 4 + talk * 26, "#5a1e24", 7);
    p.ell(hx, hy + 70 + talk * 12, 10 + talk * 8, 2 + talk * 5, "#e0605a", 0);
  } else p.clip([[hx - 120, hy + 36], [hx + 120, hy + 36], [hx + 120, hy + 118], [hx - 120, hy + 118]], eyes);
  if (["shyBlush", "flirtyWink", "blissKiss", "emotionalTears"].includes(o.expr) || o.kind === "crush") {
    for (const side of [-1, 1]) for (let j = 0; j < 3; j++) {
      const x = hx + side * 78 + j * 8;
      p.stroke([[x - 4, hy + 44], [x + 2, hy + 30]], 4, "#f58298");
    }
  }
  if (o.kind === "crush") for (const side of [-1, 1])
    p.arc(hx + side * 57, hy + 2, 22, 15, side < 0 ? 180 : 280, side < 0 ? 260 : 360, 5);
};

const drawSweat = (p: Pen, x: number, y: number) => {
  p.poly(smoothClosed([[x, y - 30], [x + 16, y + 4], [x + 10, y + 20], [x - 10, y + 20], [x - 16, y + 4]], 5), "#7cc8f2", 5);
  p.ell(x - 4, y + 4, 4, 7, "#e6f6ff", 0);
};

// ---------------- head ----------------
const drawHead = (p: Pen, hx: number, hy: number, o: KidOpts, light: number) => {
  // ears behind the head
  for (const s of [-1, 1]) p.ell(hx + s * 116, hy + 16, 24, 30, HEAD, 8);
  const pts = handEllPts(hx, hy, HEAD_R0, HEAD_R0 * 0.98);
  p.poly(pts, HEAD, 0);
  // soft shade crescent on the side away from the light
  p.clip(pts, () => p.ell(hx - Math.cos(light) * 52, hy - Math.sin(light) * 40, HEAD_R0 * 1.02, HEAD_R0, HEAD_SH, 0));
  p.clip(pts, () => p.ell(hx + Math.cos(light) * 18, hy + Math.sin(light) * 14, HEAD_R0 * 0.96, HEAD_R0 * 0.94, HEAD, 0));
  p.inkRing(pts, 16.5, light + Math.PI, 0.52);
  if (o.kind === "builder") {
    // brown fringe peeking out under the cap, then the red cap with a front brim
    const hair = "#6b3d22";
    const fr: P2[] = [[hx - 104, hy - 46], [hx - 92, hy - 8], [hx - 72, hy - 34], [hx - 52, hy - 4], [hx - 30, hy - 34], [hx - 6, hy - 10], [hx + 16, hy - 36], [hx + 40, hy - 12], [hx + 62, hy - 38], [hx + 84, hy - 14], [hx + 104, hy - 46]];
    p.poly(fr, hair, 6);
    for (const s of [-1, 1]) p.poly([[hx + s * 112, hy - 40], [hx + s * 120, hy + 2], [hx + s * 104, hy - 10]], hair, 5);
    const red = "#d93a2e";
    const dome = ellPts(hx, hy - 42, 122, 92, 180, 360, 40);
    p.organic(dome, red, 12.5, light + Math.PI);
    p.clip(dome, () => p.ell(hx - Math.cos(light) * 60, hy - 60 - Math.sin(light) * 30, 120, 80, mul(red, 0.82), 0));
    p.organic(dome, null, 12.5, light + Math.PI);
    p.stroke([[hx, hy - 132], [hx - 8, hy - 44]], 4, mul(red, 0.7));
    p.arc(hx, hy - 42, 70, 82, 200, 245, 4, mul(red, 0.7));
    p.arc(hx, hy - 42, 70, 82, 295, 340, 4, mul(red, 0.7));
    p.ell(hx, hy - 132, 13, 8, mul(red, 0.85), 5);
    p.poly(smoothClosed([[hx - 128, hy - 46], [hx + 128, hy - 46], [hx + 150, hy - 30], [hx + 110, hy - 18], [hx - 110, hy - 18], [hx - 150, hy - 30]], 5), mul(red, 0.9), 8);
    // a cream patch on the crown
    p.ell(hx, hy - 82, 26, 20, "#f4ead2", 5);
    p.stroke([[hx - 10, hy - 82], [hx + 10, hy - 82]], 4, red);
  } else if (o.kind === "plaidHero") {
    p.stroke([[hx-12,hy-121],[hx-5,hy-134],[hx+2,hy-126]],5);
  } else if (o.kind === "mom") {
    p.organic(handEllPts(hx+72,hy-132,32,30),"#352221",12.5,light+Math.PI);
    p.organic(smoothClosed([[hx-119,hy-28],[hx-115,hy-105],[hx-63,hy-132],[hx+45,hy-136],[hx+113,hy-100],[hx+121,hy-18],[hx+101,hy-62],[hx+28,hy-95],[hx-31,hy-61],[hx-100,hy-72]]),"#352221",12.5,light+Math.PI);
    for(const side of [-1,1])p.arc(hx+side*119,hy+43,17,24,0,360,6,"#e9bb48");
    p.ell(hx,hy-55,4.5,6,"#8f2344",0);
  } else if (o.kind === "studentHero") {
    const cap = ellPts(hx, hy - 100, 118, 55, 180, 360, 48);
    p.organic(cap, "#d62828", 12.5, light + Math.PI);
    for (let x = -96; x <= 96; x += 16) {
      const top = hy - 100 - 55 * Math.sqrt(1 - (x / 118) ** 2);
      p.stroke([[hx + x, top + 12], [hx + x, hy - 117]], 3, "#bb2429");
    }
    const cuff=wobbleContour([[hx - 119, hy - 113], [hx + 119, hy - 113], [hx + 116, hy - 89], [hx - 116, hy - 89]]);
    p.poly(cuff,"#d62828",0);
    for (let x = -104; x <= 104; x += 13) p.stroke([[hx + x, hy - 110], [hx + x, hy - 93]], 3, "#9f2028");
    p.inkRing(cuff,12.5,light+Math.PI,0.52);
  } else if (o.kind === "crush") {
    p.organic(smoothClosed([[hx - 121, hy - 28], [hx - 118, hy - 132], [hx - 65, hy - 157], [hx + 45, hy - 157], [hx + 117, hy - 125], [hx + 123, hy + 94], [hx + 99, hy + 109], [hx + 94, hy - 61], [hx + 20, hy - 96], [hx - 24, hy - 60], [hx - 85, hy - 78], [hx - 98, hy + 108], [hx - 125, hy + 92]], 7), "#4a2511", 12.5, light + Math.PI);
    p.arc(hx, hy - 39, 119, 104, 198, 342, 11, "#ff85a2");
    p.poly(star(hx - 79, hy - 93, 17, 8), "#ffd447", 3);
  } else {
    p.g.save(); p.g.translate(hx, hy); p.g.scale(1, 0.8); p.g.translate(-hx, -hy);
    // voluminous swept-back pompadour: the crown rises ~65 units ABOVE the head circle, a quiff bulges up at the
    // front-right, the hairline dips into a widow's peak, sideburns run down past the ears
    const hair = "#3a2418";
    const top = ellPts(hx + 6, hy - 62, 132, 122, 176, 364, 36);
    const quiff: P2[] = top.map(([x, y]) => [x, y - 22 * Math.exp(-(((x - (hx + 40)) / 46) ** 2))]);
    const h: P2[] = [...quiff, [hx + 128, hy - 6],
      [hx + 108, hy - 2], [hx + 102, hy - 52], [hx + 64, hy - 74], [hx + 22, hy - 72], [hx, hy - 40], [hx - 22, hy - 72], [hx - 64, hy - 74], [hx - 102, hy - 52], [hx - 108, hy - 2], [hx - 124, hy - 6]];
    p.organic(h, hair, 12.5, light + Math.PI);
    for (const s of [-1, 1]) p.poly([[hx + s * 122, hy - 16], [hx + s * 120, hy + 34], [hx + s * 102, hy + 30], [hx + s * 104, hy - 12]], hair, 6);
    // comb lines sweeping back over the crown
    for (const [x0, y0] of [[-40, -96], [0, -110], [40, -128], [78, -116]] as const)
      p.stroke([[hx + x0, hy + y0], [hx + x0 - 40, hy + y0 - 34], [hx + x0 - 96, hy + y0 - 30]], 5, "#6a4a36");
    p.stroke([[hx + 20, hy - 168], [hx + 62, hy - 196], [hx + 96, hy - 182]], 6, "#7a5a44");
    p.g.restore();
  }
  drawFace(p, hx, hy, o);
  if ((o.sweat ?? 0) > 0 || o.expr === "brokeSad") drawSweat(p, hx + 98, hy - 14);
};

// ---------------- the figure ----------------
// Proportions (v2): head radius HEAD_R 145, a compact bean torso ~172 wide (~59 % of the 290 head), thin straight
// parallel legs with hips 35 units either side of centre and small pill feet.
export const TW = 86;   // torso half width at the hips
const HIP_X = 35;
/** the head is drawn in its 120-unit base frame and scaled up to HEAD_R about its centre (follows the lean) */
const drawHeadAt = (p: Pen, hx: number, hy: number, o: KidOpts, light: number, lean: number, piv: P2) => {
  const saved = p.rot; p.rot = null;
  const [cx, cy] = lean ? rotAbout([hx, hy], lean, piv) : [hx, hy];
  const g = p.g;
  g.save(); g.translate(cx, cy); g.rotate(lean); g.scale(HS, HS); g.translate(-hx, -hy);
  drawHead(p, hx, hy, o, light);
  g.restore();
  p.rot = saved;
};
export const drawKid = (p: Pen, o: KidOpts) => {
  const armsOnly=o.drawLayer==="arms",bodyOnly=o.drawLayer==="body";
  if(armsOnly){p.g.save();p.g.globalAlpha=0;}
  const lk = {...LOOKS[o.kind],...(o.shirtColor?{shirt:o.shirtColor}:{})}, light = o.light ?? -2.3;
  const gaze = clamp(o.gaze ?? 0, -1, 1), gazeY = clamp(o.gazeY ?? 0, -1, 1), bob = o.bob ?? 0;
  const sx = 300, sole = 952;
  const mode = o.mode;
  const sw = mode === "swing" || mode === "hammerHold" ? swingAt(mode === "hammerHold" ? 1 : o.swingP ?? 0) : null;
  const lean = sw ? sw.lean : o.lean ?? 0;
  const crouch = sw ? sw.crouch : 0;
  const seated = ["sit","toiletSit","pressFlush","sofaPhone"].includes(mode) ? sm(o.sitP ?? o.actionP ?? 1) : 0;
  const hipY = lerp(590, 790, seated) + crouch + bob * 0.4;
  const shY = lerp(375, 560, seated) + bob + crouch * 0.6;
  const piv: P2 = [sx, hipY];
  const R = (pt: P2) => rotAbout(pt, lean, piv);
  const hx = sx + gaze * 12, hy = 235 + seated * 185 + bob + gazeY * 8 + crouch * 0.6;

  // ---- legs: thin straight vertical sticks, small dark pill feet (not leaned) ----
  const gait = mode === "walk" || mode === "run" ? Math.sin((mode === "run" ? o.runP ?? o.walkP ?? 0 : o.walkP ?? 0) * Math.PI * 2) * (mode === "run" ? 65 : 35) * clamp(o.actionP ?? 1, 0, 1) : 0;
  for (const side of [-1, 1]) {
    const top: P2 = [sx + side * HIP_X, hipY + 16];
    const footX = sx + side * HIP_X + seated * 65 + side * gait;
    const bot: P2 = [footX, sole - 16 - Math.max(0, side * gait) * 0.45];
    const knee: P2 = [lerp(top[0], bot[0], 0.5) + seated * 48, lerp(top[1], bot[1], 0.5)];
    const pants = o.kind === "rival" || o.kind === "crush";
    taper(p, [top, knee, bot], pants ? 32 : 18, pants ? 26 : 15, lk.legs, pants ? 5 : 0);
    p.ell(footX + side * 8, bot[1] + 6, 26, 12, lk.shoes, 6);
    if (o.kind === "studentHero") {
      taper(p, [top, lerpP(top, knee, 0.65)], 43, 36, "#202c48", 4);
      p.stroke([[top[0] + side * 13, top[1] + 4], [lerp(top[0], knee[0], 0.65) + side * 13, lerp(top[1], knee[1], 0.65)]], 5, "#91a4c5");
    }
  }

  // ---- torso: compact bean, leaned about the hip ----
  p.rot = [lean, piv[0], piv[1]];
  p.poly([[hx - 20, hy + 120], [hx + 20, hy + 120], [sx + 20, shY + 8], [sx - 20, shY + 8]], HEAD, 6);
  const torso = wobbleContour(smoothClosed([[sx - 60, shY - 2], [sx, shY - 12], [sx + 60, shY - 2], [sx + 78, shY + 60], [sx + TW + 2, shY + 160],
    [sx + TW - 2, hipY + 8], [sx, hipY + 22], [sx - TW + 2, hipY + 8], [sx - TW - 2, shY + 160], [sx - 78, shY + 60]], 6));
  p.gradFill(torso, lk.shirt, mul(lk.shirt, 0.8), light, 0.35);
  p.inkRing(torso,12.5,light+Math.PI,0.52);
  if (o.kind === "plaidHero") {
    p.clip(torso,()=>{
      for(let x=sx-90;x<=sx+90;x+=29)p.stroke([[x,shY-10],[x+3,hipY+25]],10,"#246a3c");
      for(let y=shY+15;y<=hipY+20;y+=32)p.stroke([[sx-92,y],[sx+92,y+2]],10,"#246a3c");
      for(let x=sx-80;x<=sx+90;x+=29)p.stroke([[x,shY-10],[x+2,hipY+25]],3,"#eaf4ec");
      for(let y=shY+7;y<=hipY+20;y+=32)p.stroke([[sx-92,y],[sx+92,y+1]],3,"#eaf4ec");
    });
    p.inkRing(torso,12.5,light+Math.PI,0.52);
  } else if(o.kind==="mom") {
    p.arc(sx,shY+3,36,27,0,180,7,"#e8bd59");
    p.stroke([[sx,shY+25],[sx,shY+100]],5,"#e8bd59");
    for(let j=0;j<3;j++)p.dot(sx,shY+40+j*20,4,"#f6dd90");
  } else if (o.kind === "builder") {
    for (const s of [-1, 1]) p.poly([[sx + s * 5, shY - 8], [sx + s * 38, shY - 5], [sx + s * 22, shY + 24]], mul(lk.shirt, 0.92), 5);
    const ov: P2[] = [[sx - 44, shY + 40], [sx + 44, shY + 40], [sx + 46, shY + 118], [sx + 82, shY + 134], [sx + TW + 2, hipY + 44],
      [sx + 12, hipY + 48], [sx, hipY + 28], [sx - 12, hipY + 48], [sx - TW - 2, hipY + 44], [sx - 82, shY + 134], [sx - 46, shY + 118]];
    p.gradFill(ov, lk.body, lk.bodySh, light, 0.4);
    p.organic(ov,null,12.5,light+Math.PI);
    p.stroke([[sx - 80, shY + 140], [sx + 80, shY + 140]], 4, lk.bodySh);
    for (const s of [-1, 1]) {
      p.band([[sx + s * 38, shY + 48], [sx + s * 48, shY + 14], [sx + s * 56, shY - 4]], lk.body, 18, 4, "round");
      p.ell(sx + s * 37, shY + 56, 10, 10, "#f5d33a", 4);
    }
    const x0 = sx - 26, y0 = shY + 66, c = 13;
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++)
      p.poly([[x0 + i * c, y0 + j * c], [x0 + (i + 1) * c, y0 + j * c], [x0 + (i + 1) * c, y0 + (j + 1) * c], [x0 + i * c, y0 + (j + 1) * c]], (i + j) % 2 ? WHITE : "#d93a2e", 0);
    p.poly([[x0, y0], [x0 + 4 * c, y0], [x0 + 4 * c, y0 + 4 * c], [x0, y0 + 4 * c]], null, 4);
  } else if (o.kind === "studentHero") {
    for (const side of [-1, 1]) {
      p.stroke([[sx + side * 54, shY + 2], [sx + side * 43, shY + 96]], 13, "#293044");
      p.stroke([[sx + side * 17, shY + 24], [sx + side * 20, shY + 78]], 5, WHITE);
    }
    p.poly(smoothClosed([[sx - 39, shY + 121], [sx + 39, shY + 121], [sx + 48, shY + 166], [sx - 48, shY + 166]]), "#e4a436", 5);
    p.arc(sx, shY + 11, 30, 20, 0, 180, 7, "#ca8c25");
  } else if (o.kind === "crush" && o.outfitStyle!=="top") {
    p.poly([[sx - 23, shY + 7], [sx + 23, shY + 7], [sx + 25, hipY + 7], [sx - 25, hipY + 7]], WHITE, 5);
    for (const side of [-1, 1]) p.stroke([[sx + side * 31, shY + 18], [sx + side * 27, hipY - 4]], 5, "#ce4a58");
  } else if (o.kind === "crush") {
    p.arc(sx,shY+6,28,17,0,180,5,mul(lk.shirt,0.8));
  } else {
    const v: P2[] = [[sx - 60, shY + 2], [sx - 22, shY + 4], [sx, shY + 112], [sx + 22, shY + 4], [sx + 60, shY + 2], [sx + 80, shY + 50],
      [sx + TW, hipY - 10], [sx + 22, hipY + 6], [sx, hipY + 32], [sx - 22, hipY + 6], [sx - TW, hipY - 10], [sx - 80, shY + 50]];
    p.gradFill(v, lk.body, lk.bodySh, light, 0.4);
    p.organic(v,null,12.5,light+Math.PI);
    p.poly([[sx - 11, shY - 2], [sx + 11, shY - 2], [sx + 15, shY + 20], [sx, shY + 30], [sx - 15, shY + 20]], "#d9a62e", 5);
    p.poly([[sx - 9, shY + 30], [sx + 9, shY + 30], [sx + 18, shY + 100], [sx, shY + 118], [sx - 18, shY + 100]], "#d9a62e", 5);
    for (let i = 0; i < 3; i++) p.dot(sx + 3, shY + 146 + i * 32, 6, "#7a6a50");
    for (let i = 0; i <= 8; i++) { const t = i / 8; p.dot(lerp(sx + 6, sx + 70, t), shY + 166 + Math.sin(t * Math.PI) * 24, 4, "#e8b830"); }
    p.poly([[sx + 48, shY + 190], [sx + 80, shY + 186], [sx + 80, shY + 197], [sx + 48, shY + 201]], lk.bodySh, 4);
    for (const s of [-1, 1]) p.poly([[sx + s * 22, shY + 4], [sx + s * 36, shY + 58], [sx + s * 25, shY + 62], [sx + s * 9, shY + 38]], mul(lk.body, 0.93), 4);
  }
  p.rot = null;
  // during the wind-up / overhead arc the arms and hammer go BEHIND the head, so no arm ever crosses the face
  const headLast = true; // head occludes any raised arm: no limb can cross the face
  if (!headLast) drawHeadAt(p, hx, hy, o, light, lean, piv);

  if(armsOnly)p.g.restore();
  if(bodyOnly){p.g.save();p.g.globalAlpha=0;}
  // ---- arms: shoulders follow the lean, hands are placed in canvas space ----
  const shL = R([sx - 70, shY + 22]), shR = R([sx + 70, shY + 22]);
  let hL: P2 = [sx - 96, hipY + 6], hR: P2 = [sx + 96, hipY + 6];
  let open: "L" | "R" | null = null;
  let walletAt: { c: P2; k: number } | null = null;
  if (sw) {
    const a = rad(sw.ang), d: P2 = [Math.cos(a), Math.sin(a)];
    hR = sw.hand; hL = [sw.hand[0] + d[0] * 56, sw.hand[1] + d[1] * 56];
    if (sw.p > 0.8) hL = [sw.hand[0] - 14, sw.hand[1] - 14];
    drawHammer(p, sw.hand, sw.ang);
  } else if (mode === "wave") {
    const w = Math.sin((o.waveP ?? 0) * Math.PI * 2);
    const up = sm(o.raiseP ?? 1);
    hR = lerpP([sx + 96, hipY + 6], [sx + 150 + w * 34, shY - 150 + Math.abs(w) * 8], up); open = up > 0.5 ? "R" : null;
  } else if (mode === "wallet") {
    const k = clamp(o.walletP ?? 0, 0, 1), up = sm(k / 0.45), opn = sm((k - 0.35) / 0.65);
    const c = lerpP([sx + 40, hipY - 6], [sx - 2, shY + 112], up);
    walletAt = { c, k: opn };
    const W = 66 * WALLET_S;
    hR = [c[0] + W + 6, c[1] + 16];
    hL = opn > 0.05 ? [c[0] - W * opn - 8, c[1] + 16] : [sx - 96, hipY + 6];
  } else if (mode === "point") {
    // rival: screen-left fist closed around the knob of the 3D gold winch lever (world.ts puts the knob exactly
    // under this design point every frame), screen-right hand on the hip. Nothing is drawn in the fist.
    const point = sm(o.pointP ?? o.actionP ?? 1);
    hL = lerpP(hL, [o.gripX ?? 145, o.gripY ?? 590], point);
    hR = lerpP(hR, [sx + 82, hipY - 34], point);
  }
  const weight = (value: number | undefined) => sm(value ?? o.actionP ?? 1);
  const pose = (left: P2, right: P2, value?: number) => { const k = weight(value); hL = lerpP(hL, left, k); hR = lerpP(hR, right, k); };
  if (mode === "walk" || mode === "run") pose([sx - 110 - gait, shY + 170], [sx + 110 - gait, shY + 170]);
  const toward=(o.partnerSide??(o.kind==="crush"?-1:1))<0?-1:1;
  if (mode === "hug") pose([sx+toward*175,shY+70],[sx+toward*220,shY+105],o.hugP);
  if (mode === "phone" || mode === "sofaPhone") pose(hL,[sx+145,shY+30],mode==="sofaPhone"?1-(o.lowerP??0):o.phoneP);
  if(mode==="pressFlush") hR=flushFist(o.flushP??1);
  if(mode==="knockDoor") pose(hL,[sx+145+8*Math.sin((o.knockP??0)*Math.PI*2),shY+55]);
  if(mode==="peekDoor")pose([sx-95,shY+100],[sx+90,shY+55],o.peekP);
  if(mode==="liftMug")hR=lerpP([sx+155,620],[sx+145,shY+65],sm(o.mugP??0));
  if (mode === "fixHair") pose(hL, [sx + 158, shY - 65], o.fixHairP);
  if (mode === "stomachGrowl") pose([sx - 27, shY + 160], [sx + 27, shY + 166], o.growlP);
  if (mode === "comfort") pose([sx+toward*168,shY+55],[sx+toward*216,shY+85],o.comfortP);
  if (mode === "writePalm") pose([sx - 130, shY + 133], [sx - 85, shY + 119], o.writePalmP);
  if (mode === "palmShow") { pose(hL, [sx + 70, shY + 102], o.palmP); open = "R"; }
  if (mode === "prayer") pose([sx - 15, shY + 65], [sx + 15, shY + 65], o.prayerP);
  if (mode === "kissPalm") pose([sx - 32, shY - 13], [sx + 32, shY - 13], o.kissPalmP);
  const reach=["hug","comfort"].includes(mode)?weight(mode==="hug"?o.hugP:o.comfortP):1;
  if (o.handLX !== undefined) hL[0] = lerp(sx-96,o.handLX,reach);
  if (o.handLY !== undefined) hL[1] = lerp(hipY+6,o.handLY,reach);
  if (o.handRX !== undefined) hR[0] = lerp(sx+96,o.handRX,reach);
  if (o.handRY !== undefined) hR[1] = lerp(hipY+6,o.handRY,reach);
  const body = R([sx, ["hug","comfort","writePalm","prayer","kissPalm"].includes(mode) ? shY - 180 : shY + 110]);
  const arm = (s: P2, h: P2, side: number) => {
    const e = elbowOf(s, h, 142, 142, body);
    if (o.kind === "rival") {
      taper(p, [s, e, h], 32, 24, lk.shirt, 6);
      const cuff = lerpP(e, h, 0.82);
      p.ell(cuff[0], cuff[1], 16, 14, "#f4f0e6", 5);
    } else {
      taper(p, [s, e, h], 18, 13, LIMB);
      const sl = lerpP(s, e, 0.28);
      p.ell(sl[0], sl[1], 34, 30, lk.shirt, 7);
      p.ell(sl[0] + side * 4, sl[1] + 4, 24, 17, mul(lk.shirt, 0.9), 0);
    }
  };
  arm(shL, hL, -1);
  arm(shR, hR, 1);
  if (walletAt) {
    const g = p.g, [cx, cy] = walletAt.c;
    g.save(); g.translate(cx, cy); g.scale(WALLET_S, WALLET_S); g.translate(-cx, -cy);
    drawWallet(p, cx, cy, walletAt.k);
    g.restore();
  }
  const hand = (c: P2, isOpen: boolean, dir: number) => {
    p.ell(c[0], c[1], 23, 21, LIMB, 0);
    p.ell(c[0] - 7, c[1] - 8, 7, 5, "#6a5054", 0);
    if (isOpen) for (let i = 0; i < 4; i++) {
      const a = rad(-90 + dir * (-40 + i * 24));
      taper(p, [[c[0] + Math.cos(a) * 10, c[1] + Math.sin(a) * 10], [c[0] + Math.cos(a) * 44, c[1] + Math.sin(a) * 44]], 14, 11, LIMB);
    }
  };
  if (mode === "phone" || mode === "sofaPhone") {
    const [x,y] = hR;
    p.poly([[x-23,y-65],[x+23,y-65],[x+23,y+8],[x-23,y+8]], "#273346", 6);
    p.poly([[x-16,y-55],[x+16,y-55],[x+16,y-5],[x-16,y-5]], "#8bd4e5", 0);
    const g=p.g;g.save();g.fillStyle=INK;g.font="900 7px Arial";g.textAlign="center";g.fillText("NO",x,y-37);g.fillText("SIGNAL",x,y-26);g.restore();
    p.stroke([[x-5,y-18],[x+5,y-8]],3,"#d62828");p.stroke([[x+5,y-18],[x-5,y-8]],3,"#d62828");
  }
  if (mode === "writePalm") taper(p, [[hR[0]-14,hR[1]+15],[hR[0]+10,hR[1]-25]], 7, 3, "#236b86", 2);
  if(mode==="liftMug"){
    const x=hR[0]+37,y=hR[1]+12;
    p.arc(x+35,y+15,20,24,0,360,9,"#ff5ca8");
    p.organic(smoothClosed([[x-30,y-27],[x+29,y-27],[x+26,y+42],[x-23,y+42]]),"#ff5ca8",8);
    p.ell(x,y-27,30,9,"#ffb0d2",6);p.stroke([[x-15,y-16],[x-17,y+25]],5,"#ffe0ef");
  }
  hand(hL, false, -1);
  hand(hR, open === "R", 1);
  if(bodyOnly)p.g.restore();
  if (headLast && !armsOnly) drawHeadAt(p, hx, hy, o, light, lean, piv);
  if(armsOnly){
    p.g.save();p.g.globalCompositeOperation="destination-out";
    drawHeadAt(p,hx,hy,o,light,lean,piv);p.g.restore();return;
  }
  if (mode === "palmShow" && o.palmText) {
    const g=p.g,scale=o.palmScale??1.35;
    g.save();g.translate(hR[0],hR[1]);g.scale(scale,scale);
    p.organic(handEllPts(0,-4,24,27),HEAD,5.5);
    for(let i=0;i<4;i++)taper(p,[[(-16+i*10),-16],[(-19+i*11),-47-Math.sin(i*Math.PI/3)*7]],9,7,HEAD,2.2);
    g.fillStyle="#166d80";g.font="900 7px Arial";g.textAlign="center";g.fillText(o.palmText,0,0);
    g.font="900 23px Arial";g.strokeStyle=INK;g.lineWidth=7;
    g.shadowColor="#3bffff";g.shadowBlur=12;g.strokeText(o.palmText,-15,63);
    g.fillStyle="#7cffff";g.fillText(o.palmText,-15,63);g.shadowBlur=0;
    g.restore();
  }
  if(["toiletSit","pressFlush"].includes(mode)) {
    p.organic([[sx-73,886],[sx+75,886],[sx+74,927],[sx+8,927],[sx,914],[sx-8,927],[sx-73,927]],"#d62828",7);
    p.stroke([[sx-69,892],[sx+71,892]],5,"#f4b4a9");
  }
  if ((o.rainDrops??0)>0) for(let i=0;i<9;i++) {
    const x=170+(i*79)%265,y=340+(i*53)%340;
    p.stroke([[x,y],[x-4,y+13]],4,"#78cfff");
  }
  if (mode === "stomachGrowl" && (o.growlP??0)>0.1) {
    const g=p.g;g.save();g.globalAlpha=clamp((o.growlP??0)*2,0,1);g.font="900 31px Arial";g.textAlign="center";g.strokeStyle=INK;g.lineWidth=9;g.strokeText("GURRRR!",sx,hipY+78);g.fillStyle="#c4ff58";g.fillText("GURRRR!",sx,hipY+78);g.restore();
  }
  if ((o.heartBeatP??0)>0) {
    const k=o.heartBeatP??0;
    p.poly(smoothClosed([[sx,shY+92],[sx-26,shY+67],[sx-27,shY+48],[sx-12,shY+45],[sx,shY+57],[sx+12,shY+45],[sx+27,shY+48],[sx+26,shY+67]]),"#f24f72",4);
    for(const side of [-1,1]) p.arc(sx+side*35,shY+64,20+12*k,29,side<0?110:290,side<0?250:430,3,"#ff708e");
  }
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

/** dust burst for the hammer impact: a white star flash, puffs rolling outward and debris (canvas 600 x 400) */
export const fxImpact = (u: number, big = false) => (p: Pen) => {
  const g = p.g, cx = 300, cy = 300;
  if (u < 0.3) {
    g.save(); g.globalAlpha = 1 - u / 0.3;
    p.poly(star(cx, cy - 40, 150 + 220 * u, 50 + 60 * u, 9), "#fff3b0", 6);
    g.restore();
  }
  const fade = clamp((1 - u) * 1.6, 0, 1);
  g.save(); g.globalAlpha = fade;
  const n = big ? 11 : 8;
  for (let i = 0; i < n; i++) {
    const a = Math.PI + (i / (n - 1)) * Math.PI, r = (60 + 170 * Math.sqrt(u)) * (0.75 + 0.25 * Math.sin(i * 2.3));
    const x = cx + Math.cos(a) * r * 1.25, y = cy + Math.sin(a) * r * 0.55, s = (34 + 46 * u) * (0.8 + 0.3 * Math.cos(i * 1.7));
    p.ell(x, y, s, s * 0.82, i % 2 ? "#e9d2ac" : "#d8b88a", 6);
    p.ell(x - s * 0.25, y - s * 0.25, s * 0.4, s * 0.3, "#f6ead2", 0);
  }
  for (let i = 0; i < 7; i++) {
    const a = Math.PI * 1.1 + (i / 6) * Math.PI * 0.8, r = 80 + 220 * u;
    p.poly(star(cx + Math.cos(a) * r, cy - 20 + Math.sin(a) * r * 0.8 + 140 * u * u, 10, 5, 4, i), "#8a5a34", 3);
  }
  g.restore();
};

/** bright orange spark burst for steel-on-steel: hot core flash + streaks flying up and out (canvas 500 x 400) */
export const fxSparks = (u: number) => (p: Pen) => {
  const g = p.g, cx = 250, cy = 300;
  const fade = clamp((1 - u) * 1.5, 0, 1);
  g.save(); g.globalAlpha = fade;
  if (u < 0.35) {
    g.save(); g.globalAlpha = 1 - u / 0.35;
    p.poly(star(cx, cy, 90 + 120 * u, 26 + 20 * u, 8, u * 2), "#ffe27a", 0);
    p.ell(cx, cy, 40 + 50 * u, 26 + 30 * u, "#fffbe6", 0);
    g.restore();
  }
  for (let i = 0; i < 16; i++) {
    const a = Math.PI + 0.15 + (i / 15) * (Math.PI - 0.3), sp = 0.7 + 0.5 * Math.abs(Math.sin(i * 2.7));
    const r0 = 30 + 200 * u * sp, r1 = r0 + 40 + 30 * (1 - u);
    const drop = 160 * u * u;
    const A: P2 = [cx + Math.cos(a) * r0, cy + Math.sin(a) * r0 * 0.9 + drop], B: P2 = [cx + Math.cos(a) * r1, cy + Math.sin(a) * r1 * 0.9 + drop];
    taper(p, [A, B], 9 * (1 - u) + 3, 2, i % 3 ? "#ff9a2a" : "#ffd84a");
  }
  g.restore();
};

export const drawCharacter = drawKid;
export type CharOpts = KidOpts;
export const drawFxBlob = fxBlob;

/** Ready-to-press hover -> full depression, fixed design target for Rule B cistern controls. */
export const flushFist=(flushP:number):P2=>{
 const k=sm(flushP);return [lerp(160,145,k),lerp(540,565,k)];
};
