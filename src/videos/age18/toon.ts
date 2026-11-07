// "Age 18" cast: a 3.5-head stick-figure hero with a smooth black head, glowing white oval eyes, white brows,
// a hood-up cyan hoodie (#18a8d8) with white drawstrings and a kangaroo pocket, charcoal shorts with white side
// stripes, thin black limbs and oversized black shoes. Supporting cast (doctor, Theo, Mom, teller, officer) is
// drawn in the same flat card language with normal proportions. Props and effects live on their own cards.
// Design space 600 x 1000 units (soles at y = 975); the Pool transform scales it.
import type { Pen } from "./pen";
import { Pen as PenClass } from "./pen";

export { Pen } from "./pen";
export const INK = "#1a1320";
export const CYAN = "#18a8d8";
export const CYAN_D = "#0d7ba4";
export const CYAN_L = "#6fd6f2";
export const HERO_BLACK = "#0b0a0e";
export const SHORTS = "#363b46";
export const WHITE = "#ffffff";

type P2 = [number, number];
const rad = (d: number) => (d * Math.PI) / 180;
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
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

const ellPts = (cx: number, cy: number, rx: number, ry: number, a0 = 0, a1 = 360, n = 44): P2[] => {
  const pts: P2[] = [];
  for (let i = 0; i <= n; i++) {
    const a = rad(a0 + ((a1 - a0) * i) / n);
    pts.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]);
  }
  return pts;
};
const rrect = (x0: number, y0: number, x1: number, y1: number, r: number, n = 6): P2[] => {
  const pts: P2[] = [];
  for (const [cx, cy, a] of [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]])
    for (let i = 0; i <= n; i++) pts.push([cx + r * Math.cos(rad(a + (90 * i) / n)), cy + r * Math.sin(rad(a + (90 * i) / n))]);
  return pts;
};
const taper = (p: Pen, a: P2, b: P2, wa: number, wb: number, col = INK) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l;
  p.poly([[a[0] + nx * wa / 2, a[1] + ny * wa / 2], [b[0] + nx * wb / 2, b[1] + ny * wb / 2],
    [b[0] - nx * wb / 2, b[1] - ny * wb / 2], [a[0] - nx * wa / 2, a[1] - ny * wa / 2]], col, 0);
  p.dot(a[0], a[1], wa / 2, col); p.dot(b[0], b[1], wb / 2, col);
};
const txt = (p: Pen, s: string, x: number, y: number, size: number, col: string, align: CanvasTextAlign = "center", weight = 700, fam = "Arial") => {
  const g = p.g;
  g.save();
  g.font = `${weight} ${size}px ${fam}`;
  g.fillStyle = col; g.textAlign = align; g.textBaseline = "middle";
  g.fillText(s, x, y);
  g.restore();
};
const glowEll = (p: Pen, cx: number, cy: number, rx: number, ry: number, col: string, blur = 16) => {
  const g = p.g;
  g.save(); g.shadowColor = col; g.shadowBlur = blur;
  p.ell(cx, cy, rx, ry, col, 0);
  g.restore();
};
const softEll = (p: Pen, cx: number, cy: number, rx: number, ry: number, col: string, a = 1) => {
  const g = p.g;
  const gr = g.createRadialGradient(cx, cy, 0, cx, cy, Math.max(rx, ry));
  gr.addColorStop(0, col); gr.addColorStop(0.6, col); gr.addColorStop(1, "rgba(0,0,0,0)");
  g.save(); g.globalAlpha = a; g.fillStyle = gr;
  g.beginPath(); g.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2); g.fill(); g.restore();
};

// ---------------- expressions ----------------
export type Expr = "neutral" | "smile" | "grin" | "laugh" | "wink" | "shock" | "nervous" | "stern" | "sad" | "pained"
  | "amazed" | "suspicious" | "relief" | "smug" | "whistle" | "shout" | "question" | "chew" | "solemn";
export type Mode = "stand" | "walk" | "carry" | "sit" | "lean" | "point" | "pointSelf" | "chin" | "clap" | "hold"
  | "slump" | "shrug" | "eat" | "id";

export type HeroOpts = {
  expr: Expr; mode: Mode; blink?: number; look?: -1 | 0 | 1; phase?: number;
  light?: number; tilt?: number; helm?: number; belt?: number; glasses?: boolean;
  id?: number | null; cane?: boolean; album?: boolean; clap?: number; pizza?: number;
  /** -1 = looks to screen left, +1 = screen right: shifts the whole face plus the shoulder line inside the card */
  gaze?: number; gazeY?: number;
};

export type SupportOpts = {
  expr: Expr; mode: "stand" | "sit" | "bend" | "point" | "amazed" | "suspicious" | "hold" | "slump";
  blink?: number; look?: -1 | 0 | 1; light?: number; tilt?: number; lean?: number;
  gaze?: number; gazeY?: number; bend?: number;
};

// every character shares the reference's dark shadow head; silhouettes come from hair, hats, coats and colours
export const HEAD_DARK = "#101218";
export type Who = {
  hair: string; hairStyle: "short" | "curly" | "grayFluffy" | "bun" | "ponytail" | "officer" | "bald";
  top: string; topDark: string; bottom: string; shoes: string;
  coat?: boolean; glasses?: "round" | "frame"; old?: boolean; tie?: string; badge?: boolean; cardigan?: string;
};
export const DOCTOR: Who = { hair: "#3a2a22", hairStyle: "ponytail", top: "#eef2f2", topDark: "#c8d4d8",
  bottom: "#4a5a6a", shoes: "#2a2a30", coat: true, glasses: "frame" };
export const THEO: Who = { hair: "#5a3a22", hairStyle: "curly", top: "#e07a2a", topDark: "#b85a18",
  bottom: "#3a4a6a", shoes: "#3a2a20", glasses: "frame" };
export const THEO_OLD: Who = { ...THEO, hair: "#dcdcdc", hairStyle: "grayFluffy", top: "#b07a4a", topDark: "#8e5c34", old: true };
export const MOM: Who = { hair: "#f0f0f0", hairStyle: "bun", top: "#b8667e", topDark: "#8e4a60",
  bottom: "#5a4a6a", shoes: "#4a3a40", glasses: "round", old: true, cardigan: "#d08a6e" };
export const TELLER: Who = { hair: "#2a2220", hairStyle: "short", top: "#2a7a6a", topDark: "#1e5a4e",
  bottom: "#3a3a44", shoes: "#2a2a30", tie: "#c8a050", glasses: "frame" };
export const OFFICER: Who = { hair: "#2a2220", hairStyle: "officer", top: "#2a3a5a", topDark: "#1e2a44",
  bottom: "#2a3a5a", shoes: "#1a1a20", badge: true };

// =====================================================================================
// HERO
// =====================================================================================
const EYE = {
  open: { rx: 23, ry: 32 }, wide: { rx: 27, ry: 39 }, soft: { rx: 22, ry: 27 },
};

const heroEyes = (p: Pen, cx: number, cy: number, f: HeroOpts) => {
  const blink = clamp(f.blink ?? 0, 0, 1);
  const e = f.expr;
  const dx = 54;
  // happy closed eyes (^ ^), squeezed eyes (> <), wide ovals for shock, narrow lids for smug/stern
  const happy = e === "smile" || e === "grin" || e === "chew" || e === "whistle";
  const squeeze = e === "pained" || e === "laugh";
  const wide = e === "shock" || e === "amazed";
  const soft = e === "sad" || e === "relief" || e === "smug" || e === "stern" || e === "suspicious" || e === "shout" || e === "nervous" || e === "question" || e === "solemn";
  const g = p.g;
  for (const s of [-1, 1]) {
    const ex = cx + s * dx, ey = cy;
    if (happy || blink > 0.62) {
      g.save(); g.shadowColor = WHITE; g.shadowBlur = 18;
      p.arc(ex, ey + 6, 34, 24, 200, 340, 9, WHITE);
      g.restore();
      continue;
    }
    if (squeeze) {
      g.save(); g.shadowColor = "#cfefff"; g.shadowBlur = 14;
      const pts: P2[] = s < 0 ? [[ex - 17, ey - 17], [ex + 13, ey], [ex - 17, ey + 17]] : [[ex + 17, ey - 17], [ex - 13, ey], [ex + 17, ey + 17]];
      p.stroke(pts, 10, WHITE);
      g.restore();
      continue;
    }
    if (e === "wink" && s === 1) { p.arc(ex, ey + 4, 33, 23, 200, 340, 9, WHITE); continue; }
    let rx = wide ? EYE.wide.rx : EYE.open.rx, ry = wide ? EYE.wide.ry : EYE.open.ry;
    if (soft) { rx = EYE.soft.rx; ry = EYE.soft.ry; }
    if (e === "stern" || e === "suspicious" || e === "smug" || e === "sad" || e === "shout" || e === "question" || e === "solemn") ry *= 0.72;
    ry *= 1 - blink * 0.9;
    // glowing white oval, no pupil: the eyes stay luminous on the black head
    glowEll(p, ex, ey + ry * 0.15, rx, ry, WHITE, 18);
    g.save(); g.globalAlpha = 0.35; p.ell(ex, ey + ry * 0.2, rx * 1.12, ry * 1.12, "#bfeaff", 0); g.restore();
  }
};

const heroBrows = (p: Pen, cx: number, cy: number, f: HeroOpts) => {
  const e = f.expr;
  const dx = 54, by = cy - 62, w = 50;
  let inner = 0, outer = 0, raise = 0;
  switch (e) {
    // worried brows: the inner ends climb, the outer ends sag
    case "shock": case "amazed": inner = -15; outer = 12; raise = -8; break;
    case "shout": case "nervous": inner = -12; outer = 7; raise = -8; break;
    case "stern": case "suspicious": inner = 10; outer = -2; break;
    case "sad": inner = -10; outer = 5; break;
    case "solemn": inner = -14; outer = 8; raise = -2; break;
    case "pained": inner = -12; outer = 6; break;
    default: raise = -2;
  }
  if (e === "question" || e === "nervous") { inner = -8; outer = 4; }
  const leftA: P2 = [cx - dx - w / 2, by + outer + raise], leftB: P2 = [cx - dx + w / 2, by + inner + raise];
  const rightA: P2 = [cx + dx - w / 2, by + inner + raise], rightB: P2 = [cx + dx + w / 2, by + outer + raise];
  taper(p, leftA, leftB, 13, 11, WHITE);
  taper(p, rightA, rightB, 11, 13, WHITE);
  if (e === "question" || e === "nervous") {
    // one brow cocked higher: the question face
    p.stroke([[cx + dx - w / 2, by + inner + raise - 16], [cx + dx + w / 2, by + outer + raise - 16]], 11, WHITE);
  }
};

const heroMouth = (p: Pen, cx: number, cy: number, f: HeroOpts) => {
  const e = f.expr;
  const my = cy + 76;
  const g = p.g;
  g.save();
  g.lineCap = "round"; g.lineJoin = "round";
  const line = (w: number, col = WHITE) => { g.strokeStyle = col; g.lineWidth = w; };
  // near-black head: open mouths drop the ink stroke and get a white rim so every shape reads
  const openMouth = (x0: number, y0: number, x1: number, y1: number, r: number, rim: number) => {
    const rr = rrect(x0, y0, x1, y1, r);
    p.poly(rr, "#3a1020", 0);
    closeTrace(p, rr, rim, WHITE);
  };
  // big curved open smile: dark cavity, white teeth band clipped inside, tongue at the bottom
  const smile = (w: number, deep: number, rim: number) => {
    const pts = ellPts(cx, my - 2, w, deep, 0, 180);
    p.poly(pts, "#3a1020", 0);
    p.clip(pts, () => {
      p.poly(rrect(cx - w, my - 26, cx + w, my + 6, 4), WHITE, 0);
      p.ell(cx, my - 2 + deep * 0.82, w * 0.34, deep * 0.22, "#e86e78", 0);
    });
    closeTrace(p, pts, rim, WHITE);
  };
  switch (e) {
    case "smile": case "relief": line(9); g.beginPath(); g.arc(cx, my - 6, 34, 0.16 * Math.PI, 0.84 * Math.PI); g.stroke(); break;
    case "grin": case "wink": smile(48, 30, 7); break;
    case "smug":
      // closed smirk that lifts at one corner
      p.stroke([[cx - 40, my + 8], [cx - 14, my + 16], [cx + 16, my + 12], [cx + 42, my - 4]], 9, WHITE);
      break;
    case "laugh": smile(54, 38, 8); break;
    case "shout":
      openMouth(cx - 40, my - 22, cx + 40, my + 40, 22, 8);
      p.poly(rrect(cx - 30, my - 18, cx + 30, my - 2, 6), WHITE, 0);
      p.ell(cx, my + 26, 14, 8, "#e86e78", 0);
      break;
    case "shock": case "amazed":
      // white rim so the open mouth still reads on the black head
      p.ell(cx, my + 6, 23, 28, WHITE, 0);
      p.ell(cx, my + 6, 19, 24, "#3a1020", 0);
      p.ell(cx, my + 2, 11, 12, "#e86e78", 0);
      break;
    case "nervous": line(7); g.beginPath(); g.moveTo(cx - 34, my + 6); g.lineTo(cx - 12, my - 4); g.lineTo(cx + 10, my + 8); g.lineTo(cx + 34, my - 4); g.stroke(); break;
    case "pained": line(8); g.beginPath(); g.moveTo(cx - 32, my + 12); g.lineTo(cx - 10, my + 2); g.lineTo(cx + 10, my + 12); g.lineTo(cx + 32, my + 2); g.stroke(); break;
    case "sad": line(8); g.beginPath(); g.arc(cx, my + 26, 30, 1.18 * Math.PI, 1.82 * Math.PI); g.stroke(); break;
    case "solemn":
      // small, level mouth with the corners barely down: pensive, not a frown
      line(8); g.beginPath(); g.moveTo(cx - 24, my + 6);
      g.quadraticCurveTo(cx, my + 11, cx + 24, my + 6); g.stroke();
      break;
    case "stern": case "suspicious": line(9); g.beginPath(); g.moveTo(cx - 26, my + 8); g.lineTo(cx + 26, my + 4); g.stroke(); break;
    case "whistle":
      // pursed 'o' with a white rim: it has to read at phone size
      p.ell(cx, my + 4, 12, 14, WHITE, 0);
      p.ell(cx, my + 4, 6.5, 8.5, "#3a1020", 0);
      break;
    case "question": line(8); g.beginPath(); g.moveTo(cx - 26, my + 10); g.quadraticCurveTo(cx - 2, my + 16, cx + 24, my - 2); g.stroke(); break;
    case "chew":
      // chewing with the mouth open: white rim, dark cavity, tongue
      p.ell(cx, my + 4, 22, 14, WHITE, 0);
      p.ell(cx, my + 5, 16, 9, "#3a1020", 0);
      p.ell(cx, my + 3, 8, 5, "#e86e78", 0);
      break;
    default: line(8); g.beginPath(); g.moveTo(cx - 20, my + 4); g.lineTo(cx + 20, my + 4); g.stroke();
  }
  g.restore();
};

const shoes = (p: Pen, xL: number, xR: number, y: number) => {
  for (const [x, rot] of [[xL, -0.08], [xR, 0.08]] as const) {
    p.ell(x, y, 62, 27, HERO_BLACK, 10, 0, 360, rot);
    p.stroke([[x - 34, y - 10], [x + 34, y - 10]], 4, "#2a2a36");
  }
};

const heroCane = (p: Pen, hx: number, hy: number) => {
  p.line([[hx, hy], [hx - 16, 965]], "#7a5230", 11);
  p.arc(hx, hy + 2, 22, 18, 180, 350, 11, "#7a5230");
};

export const drawHero = (p: Pen, f: HeroOpts) => {
  const light = f.light ?? -2.3;
  const mode = f.mode;
  const seated = mode === "sit" || mode === "lean" || mode === "eat";
  const hy = seated ? 352 : mode === "slump" ? 312 : 285;
  const hip = seated ? 762 : 700;
  const shY = seated ? 505 : mode === "slump" ? 478 : 448;
  const hemY = seated ? 782 : 742;
  const walk = mode === "walk" || mode === "carry";
  const ph = f.phase ?? 0;
  const sw = Math.sin(ph * Math.PI * 2);
  const liftL = walk ? Math.max(0, sw) * 32 : 0;
  const liftR = walk ? Math.max(0, -sw) * 32 : 0;
  // 3/4 gaze: the face shifts inside the head silhouette and the shoulder line turns with it
  const gz = clamp(f.gaze ?? 0, -1, 1), gv = clamp(f.gazeY ?? 0, -1, 1);
  const gx = gz * 30, gy = gv * 12, tq = gz * 9;

  // ---- legs ----
  if (seated) {
    // knees out past the shorts so the thigh reads under the hem, then a straight shin to the floor
    for (const s of [-1, 1] as const) {
      const kx = 300 + s * 62;
      p.line([[300 + s * 34, hip - 10], [kx, 846]], HERO_BLACK, 22);
      p.line([[kx, 840], [kx - s * 10, 930]], HERO_BLACK, 16);
      p.dot(kx, 846, 12, HERO_BLACK);
    }
    shoes(p, 238, 362, 944);
  } else {
    p.line([[270, hip], [262 + sw * 12, (hip + 930) / 2 - liftL * 0.4], [255 + sw * 18, 930 - liftL]], HERO_BLACK, 16);
    p.line([[330, hip], [338 - sw * 12, (hip + 930) / 2 - liftR * 0.4], [345 - sw * 18, 930 - liftR]], HERO_BLACK, 16);
    shoes(p, 252 + sw * 16, 348 - sw * 16, 948);
  }

  // ---- shorts ----
  const shorts = rrect(234, hip - 52, 366, hip + (seated ? 40 : 62), 14);
  p.gradFill(shorts, SHORTS, mix(SHORTS, "#0c0e14", 0.4), light, 0.3);
  p.poly(shorts, null, 10);
  for (const x of [244, 356]) p.stroke([[x, hip - 42], [x, hip + 50]], 6, "#e8eef2");
  p.stroke([[300, hip + 24], [300, hip + 58]], 5, "#22262e");

  // ---- hoodie torso (oversized) ----
  const torso: P2[] = [
    [208 + tq, shY + 6], [392 + tq, shY + 6], [416 + tq * 0.7, shY + 40], [450 + tq * 0.3, hemY - 34], [438 + tq * 0.2, hemY],
    [162 + tq * 0.2, hemY], [150 + tq * 0.3, hemY - 34], [184 + tq * 0.7, shY + 40],
  ];
  p.gradFill(torso, CYAN, mix(CYAN, "#07202c", 0.42), light, 0.24);
  p.poly(torso, null, 13);
  // hem ribbing + pocket
  for (let i = 0; i < 7; i++) p.stroke([[172 + i * 43 + tq * 0.2, hemY - 6], [176 + i * 43 + tq * 0.2, hemY - 30]], 4, mul(CYAN, 0.82));
  const pk = tq * 0.55;
  const pocket = rrect(216 + pk, hemY - 148, 384 + pk, hemY - 26, 24);
  p.poly(pocket, CYAN_D, 8);
  p.stroke([[248 + pk, hemY - 140], [232 + pk, hemY - 88], [300 + pk, hemY - 70], [368 + pk, hemY - 88], [352 + pk, hemY - 140]], 7, mul(CYAN, 0.7));

  // ---- arms / sleeves ----
  // slender curved sleeves that taper to a small dark hand: no wrist ring, no hanging tube
  const shoulderL: P2 = [206 + tq, shY + 28], shoulderR: P2 = [394 + tq, shY + 28];
  let L: P2 = [176, shY + 152], R: P2 = [424, shY + 152];
  let handL: P2 = [209, hemY - 60], handR: P2 = [391, hemY - 60];
  if (walk) { L = [170 - sw * 14, shY + 160]; R = [430 + sw * 14, shY + 160]; handL = [200 - sw * 22, hemY - 62]; handR = [400 + sw * 22, hemY - 62]; }
  if (seated) { handL = [232, hip - 4]; handR = [368, hip - 4]; L = [186, shY + 152]; R = [414, shY + 152]; }
  if (mode === "carry" || mode === "hold" || mode === "id") { L = [168, shY + 128]; R = [432, shY + 128]; handL = [246, shY + 204]; handR = [354, shY + 204]; }
  if (mode === "clap") { L = [220, shY + 120]; R = [380, shY + 120]; handL = [286, shY + 185]; handR = [314, shY + 185]; }
  if (mode === "point") { R = [466, shY + 96]; handR = [520, shY + 82]; }
  if (mode === "pointSelf") { R = [386, shY + 116]; handR = [352, shY + 172]; }
  if (mode === "chin") {
    // elbow flares out, forearm climbs so the hand rests on the jaw
    const rub = Math.sin(ph * Math.PI * 2) * 7;
    R = [462 + tq, shY + 122]; handR = [356 + rub + tq, hy + 150];
  }
  if (mode === "shrug") { L = [150, shY + 100]; R = [450, shY + 100]; handL = [128, shY + 78]; handR = [472, shY + 78]; }
  if (f.album && seated) { L = [190, shY + 138]; R = [410, shY + 138]; handL = [168, hip - 28]; handR = [432, hip - 28]; }
  if (mode === "slump") { handL = [186, shY + 280]; handR = [414, shY + 280]; L = [178, shY + 168]; R = [422, shY + 168]; }
  if (mode === "eat" || mode === "lean") { R = [430, shY + 90]; handR = [372, shY + 130]; }
  const sleeve = (sh: P2, el: P2, hd: P2) => {
    const dx = hd[0] - el[0], dy = hd[1] - el[1], l = Math.hypot(dx, dy) || 1;
    const wr: P2 = [hd[0] - (dx / l) * 15, hd[1] - (dy / l) * 15];
    p.line([sh, el], CYAN, 50);
    p.line([el, wr], CYAN, 32);
    // cuff rib across the wrist
    p.stroke([[wr[0] - (dy / l) * 15, wr[1] + (dx / l) * 15], [wr[0] + (dy / l) * 15, wr[1] - (dx / l) * 15]], 7, CYAN_D);
    // small rounded hand, no hole: dark mitt with a soft top rim
    p.ell(hd[0], hd[1], 18, 21, HERO_BLACK, 7);
    p.arc(hd[0], hd[1], 14, 17, 198, 322, 4, "#31586a");
  };
  sleeve(shoulderL, L, handL);
  sleeve(shoulderR, R, handR);

  // ---- hood ring + head ----
  const hcx = 300, hcy = hy + 14, tilt = f.tilt ?? 0;
  const hoodOuter = ellPts(hcx, hcy + 18, 202, 198);
  const hoodInner = ellPts(hcx, hcy - 4, 150, 144);
  const g = p.g;
  g.save();
  g.beginPath();
  const trace = (pts: P2[]) => { pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); };
  trace(hoodOuter.map(([x, y]) => [x, y] as P2)); trace(hoodInner.map(([x, y]) => [x, y] as P2));
  const hg = g.createLinearGradient(120, 120, 480, 480);
  hg.addColorStop(0, mode === "slump" ? mul(CYAN, 0.8) : mix(CYAN, WHITE, 0.16));
  hg.addColorStop(0.55, CYAN);
  hg.addColorStop(1, mix(CYAN, "#062432", 0.36));
  g.fillStyle = hg; g.fill("evenodd");
  g.strokeStyle = INK; g.lineWidth = 12; g.stroke();
  g.restore();
  // hood rim highlight around the opening
  p.arc(hcx, hcy - 4, 150, 144, 200, 340, 7, CYAN_L);
  // drawn strings
  p.stroke([[268 + tq * 0.45, shY + 8], [262 + tq * 0.45, shY + 92]], 6, WHITE);
  p.stroke([[332 + tq * 0.45, shY + 8], [338 + tq * 0.45, shY + 92]], 6, WHITE);
  p.dot(261 + tq * 0.45, shY + 100, 8, "#e8eef2");
  p.dot(339 + tq * 0.45, shY + 100, 8, "#e8eef2");

  // neck
  p.line([[300, hcy + 118], [300 + tq * 0.5, shY + 16]], HERO_BLACK, 34);

  // head + face (tilt about the head centre); gaze shifts the features, never the hood
  p.rot = [rad(tilt), hcx, hcy];
  p.ell(hcx, hcy, 142, 140, HERO_BLACK, 12);
  // rim light on the head
  p.arc(hcx, hcy, 139, 137, 196, 330, 6, "#2e5a70");
  heroEyes(p, hcx + gx, hcy - 8 + gy, f);
  heroBrows(p, hcx + gx * 0.92, hcy - 2 + gy * 0.7, f);
  heroMouth(p, hcx + gx * 0.95, hcy + gy * 0.5, f);
  if (f.glasses) {
    // solid black glossy shades: cyan top rim, one diagonal shine, eyes hidden
    const sx0 = hcx + gx * 1.05;
    for (const s of [-1, 1]) {
      const lx = sx0 + s * 62;
      const lens = rrect(lx - 56, hcy - 50, lx + 56, hcy + 34, 26);
      p.poly(lens, "#0a0e14", 0);
      closeTrace(p, lens, 4, "#1e2e3c");
      // thin cyan top rim hugging the upper edge
      p.arc(lx, hcy - 14, 54, 40, 204, 336, 5, CYAN);
      // one diagonal reflection slash, plus a short glint
      p.stroke([[lx - 34, hcy + 16], [lx + 26, hcy - 34]], 8, "rgba(255,255,255,0.9)");
      p.stroke([[lx - 12, hcy + 22], [lx + 6, hcy + 4]], 4, "rgba(255,255,255,0.5)");
    }
    // dark bridge and temple arms: they disappear into the head instead of drawing white bars
    p.stroke([[sx0 - 12, hcy - 10], [sx0 + 12, hcy - 10]], 8, "#0e141c");
    p.stroke([[sx0 - 116, hcy - 30], [sx0 - 148, hcy - 38]], 5, "#0e141c");
    p.stroke([[sx0 + 116, hcy - 30], [sx0 + 148, hcy - 38]], 5, "#0e141c");
  }
  if ((f.helm ?? 0) > 0.02) {
    const k = clamp(f.helm!, 0, 1);
    const dome = ellPts(hcx, hcy - 26, 172, 125 * k + 10, 180, 360);
    p.poly(dome, "#f2f4f0", 12);
    p.poly(rrect(hcx - 184, hcy - 44, hcx + 184, hcy - 14, 12), "#e2e6e0", 10);
    p.stroke([[hcx - 120, hcy - 86], [hcx + 40, hcy - 118]], 8, "#ffffff");
    p.stroke([[hcx - 90, hcy - 16], [hcx + 90, hcy - 16]], 4, "#b8c0bc");
  }
  p.rot = null;

  // the chin-rub forearm belongs in front of the face, not hidden behind the head
  if (mode === "chin") sleeve(shoulderR, R, handR);

  // seatbelt across the chest
  if ((f.belt ?? 0) > 0.02) {
    const k = clamp(f.belt!, 0, 1);
    const y0 = shY + 20, y1 = hemY - 20;
    p.band([[394 - 10 * k, y0], [248 + 10 * k, y1]], "#5a6470", 30 * k + 4, 5);
    p.poly(rrect(316, hemY - 130, 352, hemY - 96, 6), "#c8a050", 6);
  }

  // props held at chest
  if (f.id != null) {
    // 35% larger than the first pass: the age line has to read at phone size
    const cx = 404, cy = shY + 148, k = 1.35;
    g.save(); g.translate(cx, cy); g.scale(k, k); g.translate(-cx, -cy);
    const card = rrect(cx - 82, cy - 52, cx + 82, cy + 52, 10);
    p.poly(card, "#f6f8f6", 7);
    p.poly(rrect(cx - 82, cy - 52, cx + 82, cy - 18, 8), "#18a8d8", 0);
    txt(p, "ID", cx - 58, cy - 29, 22, WHITE, "left", 700);
    // portrait left, age block right: the old centred AGE sat under the photo
    p.poly(rrect(cx - 66, cy - 8, cx - 16, cy + 36, 6), "#cfe2ea", 0);
    p.ell(cx - 41, cy + 6, 10, 11, HERO_BLACK, 0);
    p.ell(cx - 41, cy + 6, 3, 4, WHITE, 0);
    p.ell(cx - 41, cy + 25, 14, 6, CYAN, 0);
    txt(p, `AGE ${f.id}`, cx - 6, cy + 6, 21, "#1a2430", "left", 800);
    txt(p, "ALWAYS 18", cx - 6, cy + 34, 13, "#5a6a76", "left", 700);
    g.restore();
  }
  if (f.cane) heroCane(p, handL[0], handL[1]);
  if (f.album && seated) {
    // held up against the chest: at lap height the sofa cushion crops the whole album
    const ax = 300, ay = hip - 102;
    p.poly(rrect(ax - 158, ay - 96, ax + 158, ay + 84, 14), "#5a2a2a", 11);
    p.poly(rrect(ax - 144, ay - 82, ax - 6, ay + 70, 6), "#f0e6d2", 5);
    p.poly(rrect(ax + 6, ay - 82, ax + 144, ay + 70, 6), "#f0e6d2", 5);
    p.poly(rrect(ax - 130, ay - 68, ax - 34, ay + 2, 3), "#ffffff", 3);
    p.ell(ax - 82, ay - 34, 15, 16, HERO_BLACK, 0);
    p.ell(ax - 82, ay - 34, 3.5, 4.5, WHITE, 0);
    txt(p, "1992", ax - 82, ay + 16, 22, "#8a3a3a", "center", 700);
    p.poly(rrect(ax + 34, ay - 68, ax + 130, ay + 2, 3), "#ffffff", 3);
    p.stroke([[ax + 54, ay - 26], [ax + 70, ay - 50]], 5, CYAN);
    p.stroke([[ax + 106, ay - 26], [ax + 90, ay - 50]], 5, "#e07a2a");
    txt(p, "18 ♥", ax + 82, ay + 22, 22, "#8a3a3a", "center", 700);
    for (const x of [ax - 132, ax + 132]) {
      p.dot(x, ay + 74, 20, HERO_BLACK);
      p.arc(x, ay + 74, 21, 21, 150, 330, 4, "#3a4a56");
    }
  }
  if (f.pizza != null && (mode === "eat" || mode === "lean")) {
    // slice tip up toward the mouth, crust along the hand end so it reads at chest size
    const px = 372, py = shY + 128;
    p.poly([[px, py - 78], [px - 58, py + 30], [px + 58, py + 34]], "#f6cf6a", 6);
    p.poly([[px, py - 58], [px - 42, py + 24], [px + 42, py + 27]], "#d8402e", 0);
    for (const [dx, dy] of [[-16, -4], [12, 6], [-4, 14]] as const) p.ell(px + dx, py + dy, 9, 6, "#b02a20", 0);
    p.poly([[px - 58, py + 30], [px + 58, py + 34], [px + 52, py + 48], [px - 64, py + 44]], "#e0a24a", 5);
  }
};

// =====================================================================================
// SUPPORTING CAST
// =====================================================================================
const closeTrace = (p: Pen, pts: P2[], w: number, col: string) => p.stroke([...pts, pts[0]], w, col);

const supportHair = (p: Pen, cx: number, cy: number, w: Who) => {
  const cap: P2[] = [
    [cx - 82, cy - 22], [cx - 74, cy - 74], [cx - 30, cy - 96], [cx + 30, cy - 96], [cx + 74, cy - 74], [cx + 82, cy - 22],
    [cx + 58, cy - 46], [cx + 22, cy - 56], [cx - 22, cy - 56], [cx - 58, cy - 46],
  ];
  if (w.hairStyle === "short") {
    p.poly(cap, w.hair, 8);
  } else if (w.hairStyle === "curly" || w.hairStyle === "grayFluffy") {
    // a crown of overlapping curls: the silhouette that reads as Theo at any distance
    const r = w.hairStyle === "grayFluffy" ? 27 : 25;
    for (let i = 0; i < 9; i++) {
      const a = Math.PI * (0.04 + i * 0.115);
      p.ell(cx + Math.cos(a) * 76, cy - 14 - Math.sin(a) * 76, r, r * 0.92, w.hair, 7);
    }
    // side tufts down to the ears
    p.ell(cx - 80, cy + 6, r * 0.8, r, w.hair, 7);
    p.ell(cx + 80, cy + 6, r * 0.8, r, w.hair, 7);
  } else if (w.hairStyle === "bun") {
    p.poly(cap, w.hair, 8);
    p.ell(cx, cy - 104, 40, 35, w.hair, 8);
    p.arc(cx - 2, cy - 104, 32, 27, 200, 340, 4, "#cfcfcf");
    p.stroke([[cx - 64, cy - 54], [cx + 64, cy - 54]], 4, "#cfcfcf");
  } else if (w.hairStyle === "ponytail") {
    p.poly(cap, w.hair, 8);
    // tail swept behind the left shoulder
    p.poly([[cx + 62, cy - 66], [cx + 100, cy - 24], [cx + 112, cy + 58], [cx + 88, cy + 50], [cx + 74, cy - 8], [cx + 54, cy - 40]], w.hair, 8);
    p.dot(cx + 66, cy - 62, 15, w.hair);
  } else if (w.hairStyle === "officer") {
    p.poly([[cx - 86, cy - 48], [cx - 78, cy - 98], [cx - 28, cy - 116], [cx + 28, cy - 116], [cx + 78, cy - 98], [cx + 86, cy - 48], [cx + 40, cy - 60], [cx - 40, cy - 60]], "#1e2a44", 9);
    p.poly(rrect(cx - 80, cy - 54, cx + 80, cy - 36, 8), "#141c30", 7);
    p.poly(rrect(cx - 98, cy - 38, cx + 98, cy - 26, 7), "#0a0f1c", 6);
    p.ell(cx, cy - 88, 15, 15, "#c8a050", 5);
    txt(p, "★", cx, cy - 88, 20, "#f2e2b0", "center", 700);
  } else if (w.hairStyle === "bald") {
    p.arc(cx, cy - 8, 80, 84, 200, 340, 5, "#29313e");
  }
};

const supportEyes = (p: Pen, cx: number, cy: number, w: Who, f: SupportOpts) => {
  const blink = clamp(f.blink ?? 0, 0, 1);
  const look = f.look ?? 0;
  const e = f.expr;
  const dx = 40, ey = cy - 4;
  const happy = e === "smile" || e === "grin" || e === "relief" || e === "laugh";
  const wince = e === "pained";
  const g = p.g;
  for (const s of [-1, 1]) {
    const ex = cx + s * dx;
    if (happy || blink > 0.6) {
      // ^ ^ happy arcs
      g.save(); g.shadowColor = "#c8efff"; g.shadowBlur = 14;
      p.arc(ex, ey + 5, 25, 17, 200, 340, 7, WHITE);
      g.restore();
      continue;
    }
    if (wince) {
      // > < wince, squeezed toward the nose
      g.save(); g.shadowColor = "#c8efff"; g.shadowBlur = 12;
      const pts: P2[] = s < 0 ? [[ex - 16, ey - 16], [ex + 12, ey], [ex - 16, ey + 16]] : [[ex + 16, ey - 16], [ex - 12, ey], [ex + 16, ey + 16]];
      p.stroke(pts, 9, WHITE);
      g.restore();
      continue;
    }
    const wide = e === "shock" || e === "amazed";
    const narrow = e === "stern" || e === "suspicious" || e === "sad";
    const rx = wide ? 21 : 17;
    const ry = wide ? 28 : narrow ? 13 : 20;
    // glowing white oval, no pupil: the reference never shows a black pupil on the white
    glowEll(p, ex + look * 4, ey, rx, ry, WHITE, 16);
  }
  // white brows, angled per mood
  const by = cy - 48;
  const w0 = 9;
  if (e === "pained" || e === "sad") {
    taper(p, [cx - dx - 24, by + 6], [cx - dx + 20, by - 4], w0, 6, WHITE);
    taper(p, [cx + dx - 20, by - 4], [cx + dx + 24, by + 6], 6, w0, WHITE);
  } else if (e === "shock" || e === "amazed") {
    taper(p, [cx - dx - 24, by - 4], [cx - dx + 20, by - 14], w0, 6, WHITE);
    taper(p, [cx + dx - 20, by - 14], [cx + dx + 24, by - 4], 6, w0, WHITE);
  } else if (e === "suspicious" || e === "stern") {
    taper(p, [cx - dx - 24, by + 4], [cx - dx + 20, by + 6], w0, 6, WHITE);
    taper(p, [cx + dx - 20, by - 8], [cx + dx + 24, by - 6], 6, w0, WHITE);
  } else {
    taper(p, [cx - dx - 24, by + 2], [cx - dx + 20, by], w0, 6, WHITE);
    taper(p, [cx + dx - 20, by], [cx + dx + 24, by + 2], 6, w0, WHITE);
  }
  if (w.glasses) {
    const frame = "#e8f2f8";
    for (const s of [-1, 1]) {
      const lx = cx + s * dx;
      const rr = w.glasses === "round" ? ellPts(lx, ey, 31, 28) : rrect(lx - 31, ey - 26, lx + 31, ey + 22, 10);
      closeTrace(p, rr, 5, frame);
    }
    p.stroke([[cx - 12, ey - 4], [cx + 12, ey - 4]], 5, frame);
    p.stroke([[cx - dx - 30, ey - 6], [cx - dx - 54, ey - 12]], 5, frame);
    p.stroke([[cx + dx + 30, ey - 6], [cx + dx + 54, ey - 12]], 5, frame);
  }
};

const supportMouth = (p: Pen, cx: number, cy: number, f: SupportOpts) => {
  const e = f.expr;
  const my = cy + 60;
  const g = p.g;
  g.save(); g.lineCap = "round"; g.lineJoin = "round";
  const line = (w0: number) => { g.strokeStyle = WHITE; g.lineWidth = w0; };
  if (e === "smile" || e === "relief" || e === "grin") { line(7); g.beginPath(); g.arc(cx, my - 8, 24, 0.15 * Math.PI, 0.85 * Math.PI); g.stroke(); }
  else if (e === "laugh") {
    p.ell(cx, my, 22, 17, WHITE, 4);
    p.ell(cx, my + 1, 17, 12, "#2a1420", 0);
  } else if (e === "amazed" || e === "shock") {
    // white ring so the open mouth reads on the dark head
    p.ell(cx, my, 15, 19, WHITE, 0);
    p.ell(cx, my + 1, 10, 14, "#2a1420", 0);
  } else if (e === "pained") {
    line(7); g.beginPath(); g.moveTo(cx - 22, my + 8); g.lineTo(cx - 8, my - 2); g.lineTo(cx + 8, my + 8); g.lineTo(cx + 22, my - 2); g.stroke();
  } else if (e === "sad") {
    line(7); g.beginPath(); g.arc(cx, my + 18, 24, 1.18 * Math.PI, 1.82 * Math.PI); g.stroke();
  } else if (e === "suspicious") {
    line(7); g.beginPath(); g.moveTo(cx - 20, my + 2); g.lineTo(cx + 20, my - 2); g.stroke();
  } else if (e === "stern") {
    line(7); g.beginPath(); g.moveTo(cx - 18, my + 1); g.lineTo(cx + 18, my + 1); g.stroke();
  } else {
    line(6); g.beginPath(); g.moveTo(cx - 15, my + 1); g.lineTo(cx + 15, my + 1); g.stroke();
  }
  g.restore();
};

const supportFace = (p: Pen, cx: number, cy: number, w: Who, f: SupportOpts) => {
  const gz = clamp(f.gaze ?? 0, -1, 1), gv = clamp(f.gazeY ?? 0, -1, 1);
  const gx = gz * 22, gy = gv * 10;
  // dark shadow head, same family as the hero
  p.ell(cx, cy, 84, 90, HEAD_DARK, 12);
  p.arc(cx, cy, 80, 86, 198, 334, 6, "#2c3948");
  supportHair(p, cx, cy, w);
  supportEyes(p, cx + gx, cy - 2 + gy, w, f);
  supportMouth(p, cx + gx * 0.95, cy + gy * 0.5, f);
  if (w.old) {
    p.stroke([[cx - 62, cy + 26], [cx - 40, cy + 34]], 3, "rgba(220,230,240,0.35)");
    p.stroke([[cx + 62, cy + 26], [cx + 40, cy + 34]], 3, "rgba(220,230,240,0.35)");
    p.stroke([[cx - 54, cy + 84], [cx - 32, cy + 92]], 3, "rgba(220,230,240,0.3)");
  }
};

export const drawPerson = (p: Pen, w: Who, f: SupportOpts) => {
  const light = f.light ?? -2.3;
  const seated = f.mode === "sit";
  // 0 = upright, 1 = fully doubled over toward the box; shot 3 animates Theo's failed lift with this
  const bendK = f.mode === "bend" ? clamp(f.bend ?? 1, 0, 1) : 0;
  const gz = clamp(f.gaze ?? 0, -1, 1), gv = clamp(f.gazeY ?? 0, -1, 1);
  const gx = gz * 22, gy = gv * 10, tq = gz * 8;
  const hip = seated ? 748 : 660;
  const shS = w.old ? 352 : 338;
  const shY = seated ? 452 : shS + (455 - shS) * bendK;
  const cx = 300;                       // hip centre
  const sx = (seated ? 300 : 300 + tq) + 96 * bendK; // shoulder centre: the bend throws the chest forward
  const hx = 300 + 140 * bendK + gx * 0.35;          // head centre
  const hyS = w.old ? 246 : 232;
  const hy = seated ? 336 : hyS + (330 - hyS) * bendK + gy * 0.3;
  const tw = w.coat ? 102 : 94;
  const waist = w.coat ? 88 : 84;

  // legs first so the torso hem overlaps them
  if (seated) {
    p.line([[cx - 40, hip + 8], [cx - 74, hip + 44], [cx - 60, 930]], w.bottom, 24);
    p.line([[cx + 40, hip + 8], [cx + 74, hip + 44], [cx + 60, 930]], w.bottom, 24);
    p.ell(cx - 78, 946, 44, 20, w.shoes, 8);
    p.ell(cx + 78, 946, 44, 20, w.shoes, 8);
  } else {
    p.line([[cx - 38, hip], [cx - 48, 800], [cx - 46, 936]], w.bottom, 24);
    p.line([[cx + 38, hip], [cx + 48, 800], [cx + 46, 936]], w.bottom, 24);
    p.ell(cx - 52, 950, 46, 21, w.shoes, 8);
    p.ell(cx + 52, 950, 46, 21, w.shoes, 8);
  }
  // neck: drawn before the torso, so the head is always attached and the collar hides the joint
  p.line([[hx, hy + 56], [sx + (hx - sx) * 0.35, shY + 10]], HEAD_DARK, 40);
  // rounded-shoulder torso: hips below, wide curved shoulders, no rectangle
  const bot = hip + (seated ? 48 : 22);
  const torso: P2[] = [
    [cx - waist, bot], [cx - waist - 2, hip - 92],
    [sx - tw, shY + 58], [sx - tw + 8, shY + 16], [sx - tw * 0.6, shY - 2],
    [sx + tw * 0.6, shY - 2], [sx + tw - 8, shY + 16], [sx + tw, shY + 58],
    [cx + waist + 2, hip - 92], [cx + waist, bot],
  ];
  p.gradFill(torso, w.top, w.topDark, light, 0.28);
  p.poly(torso, null, 11);
  if (w.coat) {
    // white lab coat: open front, lapels, pocket, stethoscope
    p.poly([[sx - 46, shY + 4], [sx + 46, shY + 4], [sx + 26, hip + 10], [sx - 26, hip + 10]], w.top, 6);
    p.stroke([[sx - 46, shY + 6], [sx - 12, shY + 96], [sx - 18, hip + 14]], 6, "#8e9aa2");
    p.stroke([[sx + 46, shY + 6], [sx + 12, shY + 96], [sx + 18, hip + 14]], 6, "#8e9aa2");
    p.poly([[sx + 34, shY + 120], [sx + 74, shY + 120], [sx + 70, shY + 176], [sx + 30, shY + 176]], "#e2eaec", 5);
    p.stroke([[sx + 52, shY + 128], [sx + 52, shY + 156]], 4, "#2a5a6a");
    p.stroke([[sx - 48, shY + 8], [sx - 62, shY + 120], [sx - 6, shY + 162]], 5, "#2a2e38");
    p.stroke([[sx + 48, shY + 8], [sx + 62, shY + 120], [sx + 6, shY + 162]], 5, "#2a2e38");
    p.dot(sx, shY + 170, 13, "#9aa6ae"); p.dot(sx, shY + 170, 7, "#4a5864");
  }
  if (w.cardigan) {
    p.stroke([[sx - 40, shY + 10], [sx - 10, shY + 96], [sx - 14, hip + 10]], 13, w.cardigan);
    p.stroke([[sx + 40, shY + 10], [sx + 10, shY + 96], [sx + 14, hip + 10]], 13, w.cardigan);
    p.stroke([[sx - 44, shY + 58], [sx - 6, shY + 120], [sx + 44, shY + 58]], 5, mul(w.cardigan, 0.82));
    for (let i = 0; i < 4; i++) p.dot(sx - 2, shY + 126 + i * 44, 4, "#f0e6d0");
  }
  if (w.tie) {
    p.poly([[sx - 10, shY + 16], [sx + 10, shY + 16], [sx + 8, shY + 92], [sx, shY + 112], [sx - 8, shY + 92]], w.tie, 5);
  }
  if (w.badge) {
    for (let i = 0; i < 3; i++) p.dot(sx - 2, shY + 104 + i * 48, 6, "#d8b45a");
    p.stroke([[sx - 74, shY + 92], [sx - 34, shY + 92]], 8, "#d8b45a");
    p.stroke([[sx + 34, shY + 92], [sx + 74, shY + 92]], 8, "#d8b45a");
    p.dot(sx - 46, shY + 60, 12, "#d8b45a"); p.dot(sx - 46, shY + 60, 5, "#8a6a2a");
    txt(p, "★", sx - 46, shY + 60, 16, "#f6e6b0", "center", 700);
  }
  // smooth rubber-hose arms with dark hands
  const arm = (a: P2, b: P2, c: P2, col = w.top) => {
    p.line([a, b, c], col, 26);
    p.dot(c[0], c[1], 15, HEAD_DARK);
    p.arc(c[0], c[1], 15, 15, 150, 330, 3, "#3a4654");
  };
  const shL: P2 = [sx - tw * 0.84, shY + 34];
  const shR: P2 = [sx + tw * 0.84, shY + 34];
  if (bendK > 0.01) {
    // left hand clamped to the lower back (elbow flared out), right arm reaching for the box; blended by bendK
    const hangL: [P2, P2, P2] = [shL, [sx - 106, shY + 168], [sx - 102, shY + 286]];
    const hangR: [P2, P2, P2] = [shR, [sx + 106, shY + 168], [sx + 102, shY + 286]];
    const bentL: [P2, P2, P2] = [shL, [sx - 178, shY + 118], [sx - 146, hip - 20]];
    const bentR: [P2, P2, P2] = [shR, [sx + 122, shY + 186], [sx + 96, hip + 46]];
    const mixP = (a: [P2, P2, P2], b: [P2, P2, P2]): [P2, P2, P2] =>
      a.map((u, i) => [u[0] + (b[i][0] - u[0]) * bendK, u[1] + (b[i][1] - u[1]) * bendK] as P2) as [P2, P2, P2];
    const L = mixP(hangL, bentL), R = mixP(hangR, bentR);
    arm(L[0], L[1], L[2]); arm(R[0], R[1], R[2]);
  } else if (seated) {
    arm(shL, [cx - 112, shY + 176], [cx - 84, hip + 10]);
    arm(shR, [cx + 112, shY + 176], [cx + 84, hip + 10]);
  } else if (f.mode === "point") {
    arm(shL, [sx - 112, shY + 150], [sx - 96, shY + 262]);
    arm(shR, [sx + 150, shY + 92], [sx + 190, shY + 80]);
  } else if (f.mode === "amazed") {
    arm(shL, [sx - 150, shY + 78], [sx - 162, shY + 14]);
    arm(shR, [sx + 150, shY + 78], [sx + 162, shY + 14]);
  } else if (f.mode === "suspicious") {
    arm(shL, [sx - 96, shY + 120], [sx + 26, shY + 96]);
    arm(shR, [sx + 96, shY + 128], [sx - 30, shY + 112]);
  } else if (f.mode === "hold") {
    arm(shL, [sx - 118, shY + 116], [sx - 38, shY + 186]);
    arm(shR, [sx + 118, shY + 116], [sx + 38, shY + 186]);
  } else if (f.mode === "slump") {
    arm(shL, [sx - 104, shY + 186], [sx - 92, shY + 298]);
    arm(shR, [sx + 104, shY + 186], [sx + 92, shY + 298]);
  } else {
    arm(shL, [sx - 106, shY + 168], [sx - 102, shY + 286]);
    arm(shR, [sx + 106, shY + 168], [sx + 102, shY + 286]);
  }
  if (w.old && !seated) {
    p.line([[sx + 108, shY + 286], [sx + 124, 962]], "#7a5230", 10);
    p.arc(sx + 108, shY + 288, 20, 17, 180, 350, 10, "#7a5230");
  }
  p.rot = [rad(f.tilt ?? 0), hx, hy];
  supportFace(p, hx, hy, w, f);
  p.rot = null;
};

// =====================================================================================
// PROPS / EFFECTS (each drawn on its own card)
// =====================================================================================
const frameCard = (p: Pen, w: number, h: number, r: number, fill: string) => { p.poly(rrect(8, 8, w - 8, h - 8, r), fill, 8); };

const flame = (p: Pen, x: number, y: number, s: number, u: number) => {
  const k = 0.9 + 0.18 * Math.sin(u * 23 + x);
  const g = p.g;
  g.save(); g.shadowColor = "#ffb020"; g.shadowBlur = 26 * s;
  p.poly([[x, y - 40 * s * k], [x + 15 * s, y - 6 * s], [x, y + 10 * s], [x - 15 * s, y - 6 * s]], "#ffb020", 5);
  p.poly([[x, y - 24 * s * k], [x + 8 * s, y - 4 * s], [x, y + 5 * s], [x - 8 * s, y - 4 * s]], "#ffe680", 0);
  g.restore();
};

export const fxCake = (p: Pen, label: string, lit: boolean, u: number) => {
  const W = 700, H = 700;
  // plate
  p.ell(350, 616, 250, 40, "#e8eef0", 8);
  p.ell(350, 606, 220, 30, "#f6faf8", 0);
  // cake body + frosting
  p.poly(rrect(170, 470, 530, 612, 18), "#e0a878", 10);
  p.poly(rrect(160, 448, 540, 506, 22), "#f6e6d0", 10);
  for (let i = 0; i < 7; i++) {
    const x = 186 + i * 50;
    p.poly(ellPts(x, 506 + (i % 2) * 10, 22, 22, 0, 180), "#f6e6d0", 0);
  }
  p.stroke([[180, 540], [520, 540]], 4, "#c88858");
  p.stroke([[180, 576], [520, 576]], 4, "#c88858");
  // sprinkles
  for (let i = 0; i < 18; i++) {
    const x = 190 + (i % 9) * 40, y = 528 + Math.floor(i / 9) * 34 + (i % 3) * 4;
    p.poly(rrect(x, y, x + 16, y + 6, 3, 2), ["#e0566a", "#36b4d8", "#f2c04a", "#7ac86a"][i % 4], 0);
  }
  // digit candles: the label drawn as thick cream numerals with flames on the top edge
  const n = label.length;
  const size = n <= 2 ? 250 : 150;
  const total = n * size * 0.72;
  for (let i = 0; i < n; i++) {
    const x = 350 - total / 2 + size * 0.36 + i * size * 0.72;
    const ch = label[i];
    const g = p.g;
    g.save();
    g.font = `700 ${size}px Arial`; g.textAlign = "center"; g.textBaseline = "middle";
    g.lineWidth = 26; g.strokeStyle = INK; g.strokeText(ch, x, 400);
    g.fillStyle = "#f6e6d0"; g.fillText(ch, x, 400);
    g.restore();
    // wick + flame on top of the digit
    if (lit) flame(p, x, 400 - size * 0.46, 1.0, u + i * 0.7);
    else {
      p.stroke([[x, 400 - size * 0.44], [x, 400 - size * 0.54]], 5, "#3a3034");
      p.stroke([[x - 7, 400 - size * 0.6], [x + 2, 400 - size * 0.55], [x - 2, 400 - size * 0.48]], 4, "#c8ccd0");
    }
  }
  txt(p, "HAPPY BIRTHDAY", 350, 660, 24, "#8a3a3a", "center", 700);
  void W; void H;
};

export const fxSmoke = (p: Pen, u: number) => {
  const g = p.g;
  g.save();
  g.globalAlpha = clamp(1 - u, 0, 1);
  for (let i = 0; i < 3; i++) {
    const ph = u * 1.6 + i * 0.5;
    const x = 190 + i * 90 + Math.sin(ph * 5) * 16;
    const y = 240 - 190 * clamp(u - i * 0.08, 0, 1);
    g.strokeStyle = "rgba(120,132,140,0.85)"; g.lineWidth = 12 - i * 2; g.lineCap = "round";
    g.beginPath();
    for (let k = 0; k <= 10; k++) {
      const yy = y + k * 9;
      const xx = x + Math.sin(ph * 6 + k * 0.7) * 14;
      k ? g.lineTo(xx, yy) : g.moveTo(xx, yy);
    }
    g.stroke();
  }
  g.restore();
};

export const fxFrostRing = (p: Pen, u: number) => {
  const g = p.g;
  const r = 90 + 300 * u;
  g.save();
  g.globalAlpha = clamp(1 - u * 0.85, 0, 1);
  g.strokeStyle = "#7fd8f0"; g.lineWidth = 14; g.shadowColor = "#38c8f0"; g.shadowBlur = 24;
  g.beginPath(); g.arc(400, 400, r, 0, Math.PI * 2); g.stroke();
  g.lineWidth = 8;
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2 + u;
    const x = 400 + Math.cos(a) * (r + 16), y = 400 + Math.sin(a) * (r + 16);
    g.beginPath(); g.moveTo(400 + Math.cos(a) * (r - 10), 400 + Math.sin(a) * (r - 10)); g.lineTo(x, y); g.stroke();
    g.beginPath();
    g.moveTo(x + Math.cos(a - 0.5) * 22, y + Math.sin(a - 0.5) * 22);
    g.lineTo(x, y);
    g.lineTo(x + Math.cos(a + 0.5) * 22, y + Math.sin(a + 0.5) * 22);
    g.stroke();
  }
  g.restore();
};

export const fxSpark = (p: Pen, u: number, color = "#ffe066") => {
  const g = p.g;
  const k = Math.min(1, u * 3) * (u > 0.8 ? (1 - u) / 0.2 : 1);
  g.save(); g.translate(250, 250); g.scale(k, k); g.shadowColor = color; g.shadowBlur = 30;
  for (let i = 0; i < 10; i++) {
    const a = (i / 10) * Math.PI * 2 + u * 0.8, r0 = 34, r1 = i % 2 ? 120 : 190;
    const w = i % 2 ? 16 : 26;
    p.poly([[Math.cos(a) * r0, Math.sin(a) * r0], [Math.cos(a + 0.2) * r1, Math.sin(a + 0.2) * r1],
      [Math.cos(a) * r1, Math.sin(a) * r1], [Math.cos(a - 0.2) * r1, Math.sin(a - 0.2) * r1]], color, 0);
    void w;
  }
  p.ell(0, 0, 46, 46, "#ffffff", 6);
  g.restore();
};

export const fxSweat = (p: Pen, u: number) => {
  const g = p.g;
  g.save(); g.globalAlpha = 0.9;
  for (let i = 0; i < 3; i++) {
    const x = 90 + i * 60 + Math.sin(u * 12 + i) * 8, y = 200 - ((u * 60 + i * 40) % 90);
    p.poly([[x, y - 34], [x + 14, y], [x, y + 16], [x - 14, y]], "#a8e4ff", 4);
    p.dot(x - 4, y - 2, 4, "#ffffff");
  }
  g.restore();
};

export const fxPain = (p: Pen, u: number) => {
  // red/yellow lightning bolts radiating from the lower back: bright, jagged, unmistakably 'pain'
  const g = p.g;
  const cx = 220, cy = 170;
  const bolt = (a: number, r: number, len: number, wd: number, col: string) => {
    const ca = Math.cos(a), sa = Math.sin(a);
    const pts: P2[] = [
      [r, -3], [r + len * 0.45, -wd], [r + len * 0.42, -wd * 0.18],
      [r + len * 0.74, -wd * 0.55], [r + len * 0.7, wd * 0.32], [r + len, 0],
      [r + len * 0.44, wd * 0.78], [r + len * 0.5, wd * 0.06], [r + len * 0.16, wd * 0.62],
    ].map(([x, y]) => [cx + x * ca - y * sa, cy + x * sa + y * ca] as P2);
    g.save(); g.shadowColor = col; g.shadowBlur = 26;
    p.poly(pts, col, 4);
    g.restore();
  };
  const f = 0.88 + 0.12 * Math.sin(u * 22);
  bolt(-2.4, 34, 112 * f, 19, "#ffd23a");
  bolt(-0.72, 38, 120 * f, 17, "#ff4030");
  bolt(0.62, 34, 104 * f, 19, "#ffd23a");
  bolt(2.42, 40, 110 * f, 16, "#ff4030");
  g.save(); g.shadowColor = "#ffdd55"; g.shadowBlur = 30;
  p.ell(cx, cy, 25, 25, "#ff5040", 4);
  p.ell(cx, cy, 13, 13, "#ffe680", 0);
  g.restore();
};

export const fxPuff = (p: Pen, u: number) => {
  const g = p.g;
  g.save(); g.globalAlpha = clamp(1 - u, 0, 1) * 0.8;
  for (let i = 0; i < 4; i++) {
    const a = i * 1.7 + u * 2;
    p.ell(150 + Math.cos(a) * 40 * u, 150 + Math.sin(a) * 30 * u, 40 + 40 * u, 32 + 34 * u, "#c8ccd0", 0);
  }
  g.restore();
};

export const fxQuestion = (p: Pen, u: number) => {
  const g = p.g;
  g.save(); g.globalAlpha = clamp(u * 2, 0, 1);
  g.shadowColor = "#7fe4ff"; g.shadowBlur = 22;
  txt(p, "?", 150, 170 + Math.sin(u * 8) * 8, 190, WHITE, "center", 900);
  txt(p, "?", 260, 110 + Math.sin(u * 8 + 2) * 8, 120, "#7fe4ff", "center", 900);
  g.restore();
};

export const fxClap = (p: Pen, u: number) => {
  const g = p.g;
  g.save(); g.globalAlpha = clamp(1 - u, 0, 1);
  g.strokeStyle = "#ffffff"; g.lineWidth = 12; g.shadowColor = "#9fe8ff"; g.shadowBlur = 26;
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2;
    const r0 = 60 + 120 * u, r1 = r0 + 60;
    g.beginPath(); g.moveTo(200 + Math.cos(a) * r0, 200 + Math.sin(a) * r0); g.lineTo(200 + Math.cos(a) * r1, 200 + Math.sin(a) * r1); g.stroke();
  }
  g.restore();
};

export const fxTablet = (p: Pen, bars: number, u: number) => {
  frameCard(p, 800, 560, 34, "#151a22");
  p.poly(rrect(24, 24, 776, 536, 26), "#1e2630", 0);
  txt(p, "DIAGNOSTICS", 60, 78, 52, "#8fe4ff", "left", 700);
  txt(p, "LIFETIME SCAN", 60, 122, 24, "#5a8a9a", "left", 700);
  const rows = [["BONES", bars, "#48e0ff"], ["HEART", bars, "#48e0ff"], ["SKIN ", bars, "#48e0ff"]] as const;
  rows.forEach(([name, val, col], i) => {
    const y = 200 + i * 110;
    txt(p, name, 60, y, 40, "#cfe8f0", "left", 700);
    p.poly(rrect(270, y - 24, 700, y + 24, 11), "#0c1016", 0);
    const w = clamp(val / 18, 0, 1) * 424;
    const g = p.g;
    g.save(); g.shadowColor = col; g.shadowBlur = 24;
    p.poly(rrect(274, y - 20, 274 + w, y + 20, 9), col, 0);
    g.restore();
    txt(p, `${Math.round(val)}`, 752, y, 44, val >= 18 ? "#ffffff" : "#5a8a9a", "center", 700);
  });
  txt(p, bars >= 18 ? "ALL SYSTEMS 18 — PERFECT" : "SCANNING...", 60, 500, 30, bars >= 18 ? "#7ff0c0" : "#5a8a9a", "left", 700);
  p.stroke([[60, 470], [760, 470]], 2, "#2a3a44");
  void u;
};

export const fxHazard = (p: Pen, kind: "bullet" | "car" | "bio") => {
  frameCard(p, 500, 620, 26, "#f6f2ea");
  p.poly(rrect(8, 8, 492, 132, 22), "#c02a2a", 0);
  txt(p, "HAZARD", 250, 72, 56, "#ffffff", "center", 900);
  const g = p.g;
  g.save();
  g.strokeStyle = "#c02a2a"; g.fillStyle = "#c02a2a"; g.lineWidth = 14; g.lineCap = "round";
  if (kind === "bullet") {
    p.poly([[180, 380], [320, 380], [320, 420], [180, 420]], "#c8a050", 8);
    p.poly([[320, 380], [370, 400], [320, 420]], "#a87a30", 8);
    g.beginPath(); g.moveTo(180, 400); g.lineTo(90, 400); g.stroke();
    for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(120 - i * 26, 340 + i * 14); g.lineTo(90 - i * 22, 340 + i * 14); g.stroke(); }
  } else if (kind === "car") {
    p.poly(rrect(120, 330, 380, 430, 18), "#c02a2a", 10);
    p.poly([[170, 330], [210, 280], [320, 280], [350, 330]], "#c02a2a", 10);
    p.ell(175, 445, 34, 34, "#3a2020", 7); p.ell(325, 445, 34, 34, "#3a2020", 7);
    g.strokeStyle = "#c02a2a"; g.lineWidth = 10;
    for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(400, 300 + i * 30); g.lineTo(450, 300 + i * 30); g.stroke(); }
  } else {
    for (let i = 0; i < 3; i++) {
      const a = (i / 3) * Math.PI * 2 - Math.PI / 2;
      g.beginPath(); g.arc(250 + Math.cos(a) * 62, 340 + Math.sin(a) * 62, 68, 0, Math.PI * 2); g.stroke();
    }
    g.beginPath(); g.arc(250, 340, 34, 0, Math.PI * 2); g.fill();
  }
  g.restore();
  txt(p, kind === "bullet" ? "BULLET" : kind === "car" ? "CRASH" : "INFECTION", 250, 530, 40, "#1a2430", "center", 900);
  txt(p, kind === "bullet" ? "LEAD EXPOSURE" : kind === "car" ? "TRAFFIC" : "GERMS", 250, 574, 22, "#6a5a5a", "center", 700);
};

export const fxMonitor = (p: Pen, u: number, flash: boolean) => {
  frameCard(p, 900, 560, 24, "#0c1424");
  p.poly(rrect(20, 20, 880, 540, 16), flash && u < 0.5 ? "#1a0808" : "#0e1a30", 0);
  // scanlines
  const g = p.g;
  g.save(); g.globalAlpha = 0.18; g.strokeStyle = "#5a8ab0"; g.lineWidth = 2;
  for (let y = 30; y < 540; y += 8) { g.beginPath(); g.moveTo(26, y); g.lineTo(874, y); g.stroke(); }
  g.restore();
  // header bar
  p.poly(rrect(24, 24, 876, 128, 12), "#b82020", 0);
  txt(p, "AGE 40 · ID MISMATCH", 450, 80, 44, "#ffffff", "center", 900);
  txt(p, "ACCOUNT FROZEN", 450, 190, 38, "#ff8a8a", "center", 800);
  txt(p, "The identity chip reads 18.", 450, 250, 26, "#9ab0c8", "center", 700);
  txt(p, "The face has not changed since 1992.", 450, 286, 26, "#9ab0c8", "center", 700);
  // fake account rows
  for (let i = 0; i < 3; i++) {
    p.stroke([[100, 340 + i * 46], [800, 340 + i * 46]], 2, "#2a3a52");
    p.poly(rrect(100, 348 + i * 46, 220 + i * 90, 368 + i * 46, 6), "#26384e", 0);
  }
  // frost
  g.save(); g.globalAlpha = 0.85; g.strokeStyle = "#a8ecff"; g.lineWidth = 7; g.shadowColor = "#6fd6f2"; g.shadowBlur = 18;
  for (const [bx, by, s] of [[70, 500, 1], [820, 470, -1], [760, 60, 1]] as const) {
    for (let i = 0; i < 5; i++) {
      const a = (i / 5) * Math.PI * 2 + 0.3;
      g.beginPath(); g.moveTo(bx, by); g.lineTo(bx + Math.cos(a) * 46 * s, by + Math.sin(a) * 46 * s); g.stroke();
      g.beginPath(); g.moveTo(bx + Math.cos(a) * 26 * s, by + Math.sin(a) * 26 * s);
      g.lineTo(bx + Math.cos(a + 0.5) * 38 * s, by + Math.sin(a + 0.5) * 38 * s); g.stroke();
    }
  }
  g.restore();
  // FROZEN stamp slams in at u > 0.55
  if (u > 0.55) {
    const k = clamp((u - 0.55) / 0.15, 0, 1), sc = 1.5 - 0.5 * k;
    g.save(); g.translate(450, 430); g.rotate(-0.16); g.scale(sc, sc); g.globalAlpha = k;
    g.strokeStyle = "#ff3a3a"; g.lineWidth = 14; g.shadowColor = "#ff2020"; g.shadowBlur = 30;
    g.strokeRect(-230, -56, 460, 112);
    txt(p, "FROZEN", 0, 4, 86, "#ff3a3a", "center", 900);
    g.restore();
  }
};

export const fxMonitorIdle = (p: Pen) => {
  frameCard(p, 900, 560, 24, "#0c1424");
  p.poly(rrect(20, 20, 880, 540, 16), "#0e1a30", 0);
  txt(p, "CITIZEN BANK", 450, 80, 40, "#7fd8f0", "center", 800);
  txt(p, "ACCOUNT · A-0018", 100, 160, 30, "#cfe8f0", "left", 700);
  for (let i = 0; i < 4; i++) {
    p.stroke([[100, 210 + i * 60], [800, 210 + i * 60]], 2, "#2a3a52");
    p.poly(rrect(100, 224 + i * 60, 300 + i * 120, 250 + i * 60, 8), "#26384e", 0);
  }
  p.ell(760, 400, 48, 48, "#1e3a52", 0);
  txt(p, "18", 760, 402, 34, "#7fd8f0", "center", 900);
};

export const fxAlbum = (p: Pen, u: number) => {
  // unused placeholder kept out of the card (album is drawn inside the hero card)
  void p; void u;
};

export const fxPizza = (p: Pen, u: number) => {
  // art fills the whole 600x400 lid: the coffee table crops the card's lower edge, so nothing may live only there
  p.poly(rrect(8, 8, 592, 392, 18), "#c88a4a", 10);
  p.poly(rrect(26, 26, 574, 374, 10), "#b07a42", 0);
  p.ell(300, 224, 196, 104, "#f6c04a", 8);
  p.ell(300, 224, 176, 88, "#e8a02a", 0);
  for (let i = 0; i < 9; i++) p.ell(196 + (i % 3) * 104, 190 + Math.floor(i / 3) * 40, 21, 14, "#d83a2a", 0);
  p.poly([[300, 224], [438, 258], [352, 306]], "#f0d8a8", 5);
  txt(p, "PIZZA", 300, 104, 62, "#fff0d0", "center", 900);
  txt(p, "OPEN 3:00 AM", 300, 352, 24, "#ffe0b0", "center", 700);
  const g = p.g;
  g.save(); g.globalAlpha = 0.5; g.strokeStyle = "#ffffff"; g.lineWidth = 8; g.lineCap = "round";
  for (let i = 0; i < 2; i++) {
    const x = 240 + i * 120, y = 220 - Math.sin(u * 5 + i) * 12;
    g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + 16, y - 40, x - 16, y - 70, x + 6, y - 110); g.stroke();
  }
  g.restore();
};

export const fxIdCard = (p: Pen, age: number) => {
  p.poly(rrect(8, 8, 492, 312, 22), "#f6f8f6", 10);
  p.poly(rrect(8, 8, 492, 74, 18), "#18a8d8", 0);
  txt(p, "IDENTITY CARD", 48, 42, 32, "#ffffff", "left", 800);
  p.poly(rrect(34, 96, 190, 270, 10), "#cfe2ea", 6);
  p.ell(112, 160, 34, 36, HERO_BLACK, 0);
  p.ell(100, 158, 7, 9, WHITE, 0); p.ell(124, 158, 7, 9, WHITE, 0);
  p.ell(112, 200, 40, 20, CYAN, 0);
  txt(p, "NAME", 220, 120, 18, "#6a7a86", "left", 700);
  txt(p, "THE FOREVER BOY", 220, 150, 24, "#1a2430", "left", 800);
  txt(p, "AGE", 220, 200, 18, "#6a7a86", "left", 700);
  txt(p, `${age}`, 220, 240, 44, "#c02a2a", "left", 900);
  txt(p, "DOB 1992 · NEVER", 220, 278, 18, "#6a7a86", "left", 700);
  for (let i = 0; i < 18; i++) p.stroke([[34 + i * 8, 286], [34 + i * 8, 296]], i % 3 ? 2 : 5, "#1a2430");
};

export const fxMovingBox = (p: Pen) => {
  p.poly(rrect(20, 90, 580, 470, 12), "#c08a52", 10);
  p.poly(rrect(20, 90, 580, 150, 8), "#a8723e", 0);
  p.poly(rrect(270, 90, 330, 470, 4), "#e8d8b0", 0);
  txt(p, "FRAGILE", 300, 230, 48, "#7a3a2a", "center", 900);
  p.stroke([[120, 300], [180, 300]], 8, "#7a3a2a");
  p.poly([[140, 350], [190, 350], [165, 310]], "#7a3a2a", 0);
  txt(p, "THIS SIDE UP", 300, 400, 24, "#7a3a2a", "center", 800);
  p.stroke([[470, 180], [520, 180]], 5, "#7a3a2a");
};

/** floating speech bubble next to the cheek: beard icon, then a red NO BEARD stamp slams over it */
export const fxNoBeard = (p: Pen, u: number) => {
  const k = clamp(u, 0, 1), g = p.g;
  g.save();
  g.globalAlpha = clamp(k * 4, 0, 1);
  // tail on the left edge: the card sits screen-right of the cheek and points back at it
  p.poly([[86, 262], [26, 292], [88, 336]], "#f8fbfc", 8);
  p.poly(rrect(28, 16, 492, 352, 28), "#f8fbfc", 9);
  p.poly(rrect(28, 16, 492, 86, 26), "#e8444a", 0);
  txt(p, "NO BEARD", 260, 58, 50, "#ffffff", "center", 900);
  const bx = 238, by = 224;
  p.ell(bx, by - 14, 62, 68, "#f2d8bc", 7);
  p.arc(bx, by - 20, 58, 62, 196, 344, 9, "#5a3a26");
  p.stroke([[bx - 46, by - 32], [bx - 14, by - 38]], 10, "#3a2a20");
  p.stroke([[bx + 14, by - 38], [bx + 46, by - 32]], 10, "#3a2a20");
  p.dot(bx - 22, by - 10, 5, "#2a1e18"); p.dot(bx + 22, by - 10, 5, "#2a1e18");
  // full moustache + jaw beard
  p.stroke([[bx - 44, by + 14], [bx - 20, by + 8], [bx, by + 18], [bx + 20, by + 8], [bx + 44, by + 14]], 11, "#5a3a26");
  p.stroke([[bx - 40, by + 26], [bx - 52, by + 58], [bx - 30, by + 80], [bx, by + 90], [bx + 30, by + 80], [bx + 52, by + 58], [bx + 40, by + 26]], 9, "#5a3a26");
  for (let i = -2; i <= 2; i++) p.stroke([[bx + i * 16, by + 26], [bx + i * 13, by + 70]], 4, "#7a5236");
  // the red stamp lands over the beard (not the face) with a short overshoot
  const a = clamp((k - 0.4) / 0.22, 0, 1), sc = 1.15 - 0.3 * a;
  if (a > 0.01) {
    g.globalAlpha = a * clamp(k * 4, 0, 1);
    g.save(); g.translate(bx, by + 46); g.scale(sc, sc);
    g.strokeStyle = "#e83038"; g.lineWidth = 19; g.lineCap = "round"; g.shadowColor = "#ff2030"; g.shadowBlur = 14;
    g.beginPath(); g.moveTo(-52, -40); g.lineTo(52, 40); g.stroke();
    g.beginPath(); g.moveTo(52, -40); g.lineTo(-52, 40); g.stroke();
    g.restore();
  }
  g.restore();
};

export const fxMug = (p: Pen) => {
  p.poly(rrect(40, 60, 180, 200, 18), "#f6f8f6", 8);
  p.arc(180, 130, 30, 34, -90, 90, 16, "#f6f8f6");
  p.ell(110, 70, 66, 16, "#6a3a22", 0);
  const g = p.g; g.save(); g.globalAlpha = 0.5; g.strokeStyle = "#ffffff"; g.lineWidth = 7; g.lineCap = "round";
  g.beginPath(); g.moveTo(90, 40); g.bezierCurveTo(110, 10, 80, -10, 100, -40); g.stroke();
  g.restore();
};

export const fxCane = (p: Pen) => {
  p.line([[120, 40], [70, 470]], "#7a5230", 18);
  p.arc(120, 40, 38, 32, 180, 350, 18, "#7a5230");
  p.stroke([[110, 60], [76, 300]], 4, "#a87a50");
};

export const fxSmokeWisp = (p: Pen, u: number) => {
  // four plumes rising off the "1000" candles: bright enough to read over the black hoodie, fading as they climb
  const g = p.g;
  g.save();
  const xs = [188, 296, 404, 512], y0 = 330;
  const grad = g.createLinearGradient(0, y0, 0, y0 - 210);
  grad.addColorStop(0, "rgba(226,234,238,0.05)");
  grad.addColorStop(0.16, "rgba(226,234,238,0.78)");
  grad.addColorStop(0.6, "rgba(205,214,220,0.5)");
  grad.addColorStop(1, "rgba(190,200,206,0)");
  g.strokeStyle = grad; g.lineWidth = 13; g.lineCap = "round";
  g.shadowColor = "rgba(222,232,238,0.55)"; g.shadowBlur = 16;
  for (let i = 0; i < 4; i++) {
    const ph = u + i * 0.13;
    g.beginPath();
    for (let k = 0; k <= 16; k++) {
      const t = k / 16;
      const y = y0 - 4 - t * (150 + 45 * u);
      const x = xs[i] + Math.sin(t * 4.4 + ph * 7 + i * 1.3) * (4 + 17 * t) + Math.sin(u * 6.3 + i * 1.7) * 8 * t;
      k ? g.lineTo(x, y) : g.moveTo(x, y);
    }
    g.stroke();
  }
  g.restore();
};

export const fxIce = (p: Pen, u: number) => {
  const g = p.g; g.save(); g.globalAlpha = clamp(u * 2, 0, 1) * clamp(1 - u, 0, 1);
  g.strokeStyle = "#bff0ff"; g.lineWidth = 6; g.shadowColor = "#6fd6f2"; g.shadowBlur = 18;
  for (let i = 0; i < 14; i++) {
    const a = (i / 14) * Math.PI * 2, r = 40 + 150 * u;
    const x = 200 + Math.cos(a) * r, y = 200 + Math.sin(a) * r;
    g.beginPath(); g.moveTo(200 + Math.cos(a) * (r - 20), 200 + Math.sin(a) * (r - 20)); g.lineTo(x, y); g.stroke();
  }
  g.restore();
};

export const fxShock = (p: Pen) => {
  const g = p.g;
  g.save(); g.strokeStyle = "#ffe066"; g.lineWidth = 12; g.shadowColor = "#ffc030"; g.shadowBlur = 20;
  for (let i = 0; i < 8; i++) {
    const a = (i / 8) * Math.PI * 2;
    g.beginPath(); g.moveTo(200 + Math.cos(a) * 70, 200 + Math.sin(a) * 70); g.lineTo(200 + Math.cos(a) * 150, 200 + Math.sin(a) * 150); g.stroke();
  }
  g.restore();
};

/** ground contact blob (multiply): the canvas must start WHITE, then darken radially - transparent black would
 *  black out the whole quad under Zero/SrcColor blending */
export const fxBlob = (p: Pen, col: string) => {
  const g = p.g;
  g.fillStyle = WHITE; g.fillRect(0, 0, 128, 128);
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  for (const [r, k] of [[0, 0], [0.32, 0.02], [0.5, 0.22], [0.66, 0.58], [0.82, 0.88], [1, 1]] as const) gr.addColorStop(r, mix(col, WHITE, k));
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
};

/** one sheet of bank paperwork: dense enough to read as a form at card size */
export const fxPaper = (p: Pen) => {
  p.poly(rrect(10, 10, 290, 390, 6), "#f4f6f4", 8);
  p.poly(rrect(10, 10, 290, 52, 5), "#d8e2e6", 0);
  txt(p, "ACCOUNT", 30, 32, 20, "#4a5a66", "left", 800);
  for (let i = 0; i < 7; i++) p.stroke([[30, 84 + i * 36], [270 - (i % 3) * 40, 84 + i * 36]], 4, "#9aaab4");
  p.poly(rrect(30, 344, 180, 372, 4), "#c85a5a", 0);
  p.stroke([[30, 60], [270, 60]], 2, "#aab6be");
};

// keep the class import used in the type position only
export type PenLike = PenClass;
