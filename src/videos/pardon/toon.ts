// Our own flat 2D cartoon cast (knight, priest, medieval townsfolk) + 2D effects, drawn on a canvas.
// Same construction as the engine cast: superellipse heads, bean torsos, single-stroke limbs with ink-dot hands,
// a thick-thin plum outline weighted away from the light, soft painted crescents, deadpan lidded eyes.
// Construction v2 (characters.md, our own cast): superellipse heads (pointed crown 1.75 / full jaw 2.3, chin taper,
// seeded side bulge + tilt), bean torsos, single-stroke limbs with ink-dot hands, a thick-thin plum outline weighted
// away from the light, soft painted crescents, deadpan lidded eyes, no blush, no catchlights.
// Design space 600 x 1000 units (soles at y = 975); the canvas transform scales it.
export const INK = "#241726";
export const SKIN = "#ffe2c2";
const WHITE = "#ffffff";
const MOUTH = "#5a1e28";
const TONGUE = "#e86e78";
type C3 = [number, number, number];
const SH_SKIN: C3 = [0.94, 0.82, 0.84]; // shadow/lit ratio on skin heads (reference 0.88-0.89 on screen; a touch
                                        // deeper in the drawing since the card tint lifts it again)
const SH_CLOTH: C3 = [0.64, 0.66, 0.74]; // torsos: lit side -> far side ~0.65
const SH_FELT: C3 = [0.62, 0.62, 0.7];

export type Build = "adult" | "stout" | "kid";
export type Outfit = {
  jacket: string; pants: string; boots: string; hat?: string | null; belt?: string | null; buttons?: string; rifle?: boolean;
  sash?: string; sword?: boolean; moustache?: string; skin?: string; head?: number; cap?: string; hair?: string; dress?: string;
  build?: Build;
  /** knight: steel plate seams and rivets over the jacket colour; helm plume colour */
  armor?: boolean; plume?: string;
};
type P2 = [number, number];

const rad = (d: number) => (d * Math.PI) / 180;
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
export const mul = (c: string, m: C3) => {
  const n = parseInt(c.slice(1), 16);
  const ch = (v: number, k: number) => Math.min(255, Math.round(v * k)).toString(16).padStart(2, "0");
  return `#${ch((n >> 16) & 255, m[0])}${ch((n >> 8) & 255, m[1])}${ch(n & 255, m[2])}`;
};
export const shade = (c: string, k: number) => mul(c, [k, k, k]);
export const mix = (a: string, b: string, t: number) => {
  const A = parseInt(a.slice(1), 16), B = parseInt(b.slice(1), 16);
  const ch = (s: number) => Math.round(((A >> s) & 255) * (1 - t) + ((B >> s) & 255) * t).toString(16).padStart(2, "0");
  return `#${ch(16)}${ch(8)}${ch(0)}`;
};
/** deterministic per-character random in [0, 1) */
const rnd = (seed: number, k: number) => { const x = Math.sin(seed * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };
const rotPts = (pts: P2[], a: number, cx: number, cy: number): P2[] =>
  pts.map(([x, y]) => [cx + (x - cx) * Math.cos(a) - (y - cy) * Math.sin(a), cy + (x - cx) * Math.sin(a) + (y - cy) * Math.cos(a)]);
const rotAbout = (q: P2, a: number, c: P2): P2 => rotPts([q], a, c[0], c[1])[0];
const lerp2 = (a: P2, b: P2, t: number): P2 => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
/** smooth curve from a through (near) k to b, as a polyline */
const curve = (a: P2, k: P2, b: P2, n = 10): P2[] => {
  const c: P2 = [2 * k[0] - (a[0] + b[0]) / 2, 2 * k[1] - (a[1] + b[1]) / 2], out: P2[] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, s = 1 - t;
    out.push([s * s * a[0] + 2 * s * t * c[0] + t * t * b[0], s * s * a[1] + 2 * s * t * c[1] + t * t * b[1]]);
  }
  return out;
};

export const RIFLEMAN: Outfit = { jacket: "#357650", pants: "#3d4440", boots: INK, hat: "shako", belt: "#f1efe6", buttons: "#d9dde0", rifle: true };
export const OFFICER: Outfit = { ...RIFLEMAN, hat: "shako_tall", buttons: "#e8c45a", sash: "#c0353a", sword: true, moustache: "#4a3020", rifle: false, belt: null, build: "stout" };
export const KID: Outfit = { jacket: "#f08a2c", pants: "#3b5b9a", boots: "#f4f1ea", hat: "cap", cap: "#e2453c", build: "kid" };
export const PARENT: Outfit = { jacket: "#7b5ac9", pants: "#3b3f52", boots: "#5a3b2a", hat: "hair", hair: "#5a3b2a" };
export const SKINS = [SKIN, "#f5c9a0", "#ecd0b6", "#c99067"];

export const soldier = (v = 0, extra: Partial<Outfit> = {}): Outfit => {
  const o: Outfit = { ...RIFLEMAN, skin: SKINS[v % 4] };
  if (v % 4 === 1) o.moustache = "#4a3426";
  if (v % 4 === 3) o.moustache = "#2a201a";
  return { ...o, ...extra };
};

// ---------------- THE PARDON cast ----------------
/** plate-armoured knight: bright steel, gold belt, red plume on an open bascinet, small gold cross on the chest */
export const KNIGHT: Outfit = {
  jacket: "#b9c2cf", pants: "#98a2b2", boots: "#5f6875", hat: "helm", plume: "#c0353a",
  belt: "#8a6a3a", buttons: "#e8c45a", armor: true, skin: "#f5c9a0", build: "adult",
};
/** portly pardoner in red and gold canonicals with a small red zucchetto */
export const PRIEST: Outfit = {
  jacket: "#a62f36", pants: "#7d2027", boots: "#3a2226", dress: "#c0393f", hat: "skullcap", cap: "#a62f36",
  sash: "#e8c45a", buttons: "#e8c45a", skin: "#f5c9a0", build: "stout",
};
/** medieval townsfolk: coarse tunics, hoods, straw hats, linen bonnets (no rifles, no uniforms) */
export const townsfolk = (v = 0): Outfit => {
  const coats = ["#4f6f9e", "#8c3b4a", "#5d7a3a", "#b5653f", "#2f5f6a", "#7b5ac9"];
  const skin = SKINS[v % 4];
  const base: Outfit = { jacket: coats[v % 6], pants: "#4a4038", boots: "#4a3426", skin };
  switch (v % 4) {
    case 0: return { ...base, hat: "hood", cap: "#3e5a34", dress: "#55713c" };
    case 1: return { ...base, hat: "straw", cap: "#d9b86a" };
    case 2: return { ...base, hat: "bonnet", dress: "#c25a7a" };
    default: return { ...base, hat: "hair", hair: "#5a3b2a" };
  }
};

export class Pen {
  g: CanvasRenderingContext2D;
  ol = 12;
  /** [angle, cx, cy] rotation about (cx, cy), optional post-translation [.., dx, dy] */
  rot: number[] | null = null;
  constructor(g: CanvasRenderingContext2D) { this.g = g; }
  P(x: number, y: number): P2 {
    if (!this.rot) return [x, y];
    const r = this.rot, a = r[0], cx = r[1], cy = r[2], dx = r.length > 3 ? r[3] : 0, dy = r.length > 4 ? r[4] : 0, c = Math.cos(a), s = Math.sin(a);
    return [cx + (x - cx) * c - (y - cy) * s + dx, cy + (x - cx) * s + (y - cy) * c + dy];
  }
  path(pts: P2[], close: boolean) {
    const g = this.g;
    g.beginPath();
    pts.forEach((p, i) => { const [x, y] = this.P(p[0], p[1]); if (i) g.lineTo(x, y); else g.moveTo(x, y); });
    if (close) g.closePath();
  }
  /** filled shape with an ink outline; fill=null draws the outline only */
  poly(pts: P2[], fill: string | null, ol?: number) {
    const g = this.g, w = ol ?? this.ol;
    this.path(pts, true);
    if (fill) { g.fillStyle = fill; g.fill(); }
    if (w) { g.lineWidth = w; g.strokeStyle = INK; g.lineJoin = "round"; g.stroke(); }
  }
  ell(cx: number, cy: number, rx: number, ry: number, fill: string | null, ol?: number, a0 = 0, a1 = 360, rot = 0) {
    this.poly(ellPts(cx, cy, rx, ry, a0, a1, rot), fill, ol);
  }
  /** thick round-capped limb with an ink rim (effects, rope) */
  line(pts: P2[], fill: string, w: number, ink = true) {
    const g = this.g;
    g.lineCap = "round"; g.lineJoin = "round";
    if (ink) { this.path(pts, false); g.strokeStyle = INK; g.lineWidth = w + 2 * this.ol * 0.9; g.stroke(); }
    this.path(pts, false); g.strokeStyle = fill; g.lineWidth = w; g.stroke();
  }
  stroke(pts: P2[], w: number, fill = INK) {
    const g = this.g;
    g.lineCap = "round"; g.lineJoin = "round";
    this.path(pts, false); g.strokeStyle = fill; g.lineWidth = w; g.stroke();
  }
  arc(cx: number, cy: number, rx: number, ry: number, a0: number, a1: number, w: number, fill = INK) {
    const pts: P2[] = [];
    for (let i = 0; i <= 24; i++) pts.push([cx + rx * Math.cos(rad(a0 + ((a1 - a0) * i) / 24)), cy + ry * Math.sin(rad(a0 + ((a1 - a0) * i) / 24))]);
    this.stroke(pts, w, fill);
  }
  dot(cx: number, cy: number, r: number, fill = INK) {
    const [x, y] = this.P(cx, cy);
    this.g.beginPath(); this.g.arc(x, y, r, 0, Math.PI * 2); this.g.fillStyle = fill; this.g.fill();
  }
  /** draw with a closed shape as clip */
  clip(pts: P2[], fn: () => void) { const g = this.g; g.save(); this.path(pts, true); g.clip(); fn(); g.restore(); }
  /** flat fill + soft crescent on the side away from the light (light = canvas angle the light comes FROM).
   *  Radial ramp centred `shift` R toward the light: flat out to ~0.6 R on the far side, full shadow by ~0.8 R. */
  shadedFill(pts: P2[], base: string, shadow: string, light: number, R: number, shift = 0.45, r0 = 1.05, r1 = 1.25) {
    const g = this.g, n = pts.length;
    let cx = 0, cy = 0;
    for (const [x, y] of pts) { cx += x / n; cy += y / n; }
    const [gx, gy] = this.P(cx + Math.cos(light) * shift * R, cy + Math.sin(light) * shift * R);
    const gr = g.createRadialGradient(gx, gy, 0, gx, gy, r1 * R);
    gr.addColorStop(0, base); gr.addColorStop(r0 / r1, base); gr.addColorStop(1, shadow);
    this.path(pts, true); g.fillStyle = gr; g.fill();
  }
  /** broad gradient across a shape along the light: lit edge = base, far edge = shadow (torsos, coats) */
  gradFill(pts: P2[], base: string, shadow: string, light: number, flat = 0.22) {
    const g = this.g, dx = Math.cos(light), dy = Math.sin(light), n = pts.length;
    let cx = 0, cy = 0, lo = Infinity, hi = -Infinity;
    for (const [x, y] of pts) { cx += x / n; cy += y / n; const d = x * dx + y * dy; lo = Math.min(lo, d); hi = Math.max(hi, d); }
    const dc = cx * dx + cy * dy;
    const [ax, ay] = this.P(cx + dx * (hi - dc), cy + dy * (hi - dc)), [bx, by] = this.P(cx + dx * (lo - dc), cy + dy * (lo - dc));
    const gr = g.createLinearGradient(ax, ay, bx, by);
    gr.addColorStop(0, base); gr.addColorStop(flat, base); gr.addColorStop(1, shadow);
    this.path(pts, true); g.fillStyle = gr; g.fill();
  }
  /** thick-thin ink ring: w(θ) = w0 (1 + k cos(θ − thick)), θ from the contour centroid (canvas angles) */
  inkRing(pts: P2[], w0: number, thick: number, k = 0.45, col = INK) {
    const n = pts.length;
    let cx = 0, cy = 0;
    for (const [x, y] of pts) { cx += x / n; cy += y / n; }
    const out: P2[] = [], inn: P2[] = [];
    pts.forEach((q, i) => {
      const a = pts[(i + n - 1) % n], b = pts[(i + 1) % n];
      let nx = b[1] - a[1], ny = a[0] - b[0]; // outward normal for clockwise-on-screen contours
      const l = Math.hypot(nx, ny) || 1; nx /= l; ny /= l;
      const h = 0.5 * w0 * (1 + k * Math.cos(Math.atan2(q[1] - cy, q[0] - cx) - thick));
      out.push([q[0] + nx * h, q[1] + ny * h]); inn.push([q[0] - nx * h, q[1] - ny * h]);
    });
    const g = this.g;
    const trace = (r: P2[]) => { r.forEach(([x0, y0], i) => { const [x, y] = this.P(x0, y0); if (i) g.lineTo(x, y); else g.moveTo(x, y); }); g.closePath(); };
    g.beginPath(); trace(out); trace(inn.reverse());
    g.fillStyle = col; g.fill("evenodd");
  }
  /** flat strap with a thin ink rim (cross belts, sash, rifle, handles) */
  band(pts: P2[], fill: string, w: number, rim: number, cap: CanvasLineCap = "butt") {
    const g = this.g; g.lineCap = cap; g.lineJoin = "round";
    this.path(pts, false); g.strokeStyle = INK; g.lineWidth = w + 2 * rim; g.stroke();
    this.path(pts, false); g.strokeStyle = fill; g.lineWidth = w; g.stroke();
    g.lineCap = "round";
  }
}

const ellPts = (cx: number, cy: number, rx: number, ry: number, a0 = 0, a1 = 360, rot = 0, n = 48): P2[] => {
  const r = rad(rot), pts: P2[] = [];
  for (let i = 0; i <= n; i++) {
    const a = rad(a0 + ((a1 - a0) * i) / n), x = rx * Math.cos(a), y = ry * Math.sin(a);
    pts.push([cx + x * Math.cos(r) - y * Math.sin(r), cy + x * Math.sin(r) + y * Math.cos(r)]);
  }
  return pts;
};

const rrect = (x0: number, y0: number, x1: number, y1: number, r: number, n = 8): P2[] => {
  const pts: P2[] = [];
  for (const [cx, cy, a] of [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]])
    for (let i = 0; i <= n; i++) pts.push([cx + r * Math.cos(rad(a + (90 * i) / n)), cy + r * Math.sin(rad(a + (90 * i) / n))]);
  return pts;
};

/** tapered stroke, thick end at a: brows, moustache halves */
const taper = (p: Pen, a: P2, b: P2, wa: number, wb: number, col = INK) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1, nx = -dy / l, ny = dx / l;
  p.poly([[a[0] + nx * wa / 2, a[1] + ny * wa / 2], [b[0] + nx * wb / 2, b[1] + ny * wb / 2],
    [b[0] - nx * wb / 2, b[1] - ny * wb / 2], [a[0] - nx * wa / 2, a[1] - ny * wa / 2]], col, 0);
  p.dot(a[0], a[1], wa / 2, col); p.dot(b[0], b[1], wb / 2, col);
};

// ---------------- contours ----------------
export type Blob = { a: number; b: number; nTop: number; nBot: number; egg: number; asym: number; rot: number; noise: number; seed: number };

/** superellipse "bean": separate crown / jaw exponents, egg taper (neg = narrower chin), one-side bulge, soft noise.
 *  Points run right -> down -> left -> up (clockwise on screen). */
export const blobPts = (cx: number, cy: number, B: Blob, n = 72): P2[] => {
  const ph = [rnd(B.seed, 11), rnd(B.seed, 12), rnd(B.seed, 13)].map((v) => v * Math.PI * 2);
  const pts: P2[] = [];
  for (let i = 0; i < n; i++) {
    const t = (i / n) * Math.PI * 2, c = Math.cos(t), s = Math.sin(t), e = 2 / (s < 0 ? B.nTop : B.nBot);
    let X = Math.sign(c) * Math.abs(c) ** e;
    const Y = Math.sign(s) * Math.abs(s) ** e;
    X *= (1 + B.egg * Y) * (1 + B.asym * Math.sign(X));
    const r = 1 + B.noise * (Math.cos(2 * t + ph[0]) + 0.7 * Math.cos(3 * t + ph[1]) + 0.5 * Math.cos(4 * t + ph[2]));
    const x = B.a * X * r, y = B.b * Y * r;
    pts.push([cx + x * Math.cos(B.rot) - y * Math.sin(B.rot), cy + x * Math.sin(B.rot) + y * Math.cos(B.rot)]);
  }
  return pts;
};

/** measured head: H/W 0.94, slightly pointed crown (1.75), fuller jaw (2.3), chin taper -0.12, 8 % bulge to the facing side */
export const headBlob = (seed: number, a = 118, facing = 0): Blob => ({
  a, b: a * (0.94 + 0.08 * (rnd(seed, 1) - 0.5)),
  nTop: 1.75 + 0.3 * (rnd(seed, 2) - 0.5), nBot: 2.3 + 0.3 * (rnd(seed, 3) - 0.5),
  egg: -0.12 + 0.06 * (rnd(seed, 4) - 0.5),
  asym: (0.06 + 0.04 * rnd(seed, 5)) * (facing || (rnd(seed, 6) < 0.5 ? -1 : 1)),
  rot: rad(8 * (rnd(seed, 7) - 0.5)), noise: 0.008, seed,
});

/** thickest outline direction: away from the light, pulled toward the ground (64 deg measured for upper-left light) */
export const thickAngle = (light: number) => Math.atan2(-Math.sin(light) + 0.8, -Math.cos(light));
const DEF_LIGHT = rad(-120);

// ---------------- faces ----------------
export type Expr = "neutral" | "stern" | "grin" | "laugh" | "whistle" | "nervous" | "shock" | "relief" | "relief_open" | "dazed"
  | "pained" | "smile" | "smile_closed" | "lick" | "wink" | "angry";
type EyeK = "dot" | "small" | "lid" | "slit" | "happy" | "dash" | "squeeze" | "shock" | "shockHalf" | "spiral";
type MouthK = "dash" | "frown" | "smirk" | "smile" | "smileWide" | "grin" | "laugh" | "o" | "O" | "wave" | "teeth" | "lick" | "yell";
/** eyes [back, front], brows [inner, outer] offsets in u (+ = down), mouth kind.
 *  Open eyes are always the same round dot pupil (a blink turns dot -> lid -> slit); arcs are reserved for genuine
 *  closed-eye joy, so an expressive face never reads as a pair of sleepy slits. */
const FACE: Record<Expr, { eye: [EyeK, EyeK]; brow: [number, number]; mouth: MouthK }> = {
  neutral: { eye: ["dot", "dot"], brow: [0, -1], mouth: "dash" },
  stern: { eye: ["dot", "dot"], brow: [4, -3], mouth: "frown" },
  grin: { eye: ["dot", "dot"], brow: [-3, -3], mouth: "grin" },
  laugh: { eye: ["squeeze", "squeeze"], brow: [-4, -4], mouth: "laugh" },
  whistle: { eye: ["happy", "happy"], brow: [-2, -4], mouth: "o" },
  nervous: { eye: ["small", "small"], brow: [-3, 2], mouth: "wave" },
  shock: { eye: ["shock", "shock"], brow: [-7, -6], mouth: "O" },
  relief: { eye: ["happy", "happy"], brow: [-2, 1], mouth: "smileWide" },
  relief_open: { eye: ["happy", "happy"], brow: [-2, 1], mouth: "grin" },
  dazed: { eye: ["spiral", "spiral"], brow: [-3, 2], mouth: "wave" },
  pained: { eye: ["squeeze", "lid"], brow: [-3, 2], mouth: "teeth" },
  smile: { eye: ["dot", "dot"], brow: [0, -1], mouth: "smirk" },
  smile_closed: { eye: ["happy", "happy"], brow: [0, -1], mouth: "smile" },
  lick: { eye: ["dot", "dot"], brow: [0, -1], mouth: "lick" },
  wink: { eye: ["dot", "happy"], brow: [-2, -3], mouth: "smirk" },
  angry: { eye: ["dot", "dot"], brow: [6, -4], mouth: "yell" },
};
const halfLid = (k: EyeK): EyeK => (k === "dot" || k === "small" ? "lid" : k === "lid" ? "slit" : k === "shock" ? "shockHalf" : k);
const eyeKind = (k: EyeK, lid: number): EyeK =>
  lid >= 1 && k !== "happy" && k !== "squeeze" && k !== "spiral" ? "dash" : lid > 0 ? halfLid(k) : k;
const lidOf = (b: boolean | number | undefined) => (b === true ? 1 : Number(b) || 0);

const eye = (p: Pen, kind: EyeK, x: number, ey: number, u: number, side: number, look: number, skin: string) => {
  const lx = x + look * 3 * u, lw = 3.8 * u;
  switch (kind) {
    case "dot": p.ell(lx, ey, 3.8 * u, 5.5 * u, INK, 0); p.dot(lx - 1.1 * u, ey - 1.9 * u, 1.1 * u, "#fff4e2"); break;
    case "small": p.ell(lx, ey, 3 * u, 4.4 * u, INK, 0); break;
    case "lid": p.ell(lx, ey - u, 7 * u, 6 * u, INK, 0, 0, 180); p.stroke([[x - 9 * u, ey - u], [x + 9 * u, ey - u]], lw); break;
    case "slit": p.ell(lx, ey, 7 * u, 2.6 * u, INK, 0, 0, 180); p.stroke([[x - 9 * u, ey], [x + 9 * u, ey]], lw); break;
    case "happy": p.arc(x, ey + 3 * u, 8 * u, 6 * u, 200, 340, lw); break;
    case "dash": p.stroke([[x - 8.5 * u, ey], [x + 8.5 * u, ey]], lw); break;
    case "squeeze": p.stroke([[x + 6 * u * side, ey - 5 * u], [x - 6 * u * side, ey], [x + 6 * u * side, ey + 5 * u]], lw); break;
    case "shock": case "shockHalf":
      p.ell(x, ey, 11 * u, 11 * u, WHITE, 2.6 * u); p.dot(lx - side * 1.5 * u, ey + 1.5 * u, 3 * u);
      if (kind === "shockHalf") { p.ell(x, ey, 11 * u, 11 * u, skin, 0, 180, 360); p.stroke([[x - 11 * u, ey], [x + 11 * u, ey]], 2.6 * u); }
      break;
    default: {
      const s: P2[] = [];
      for (let t = 1; t < 15; t++) s.push([x + Math.cos(t * 0.9) * t * 0.55 * u, ey + Math.sin(t * 0.9) * t * 0.55 * u]);
      p.stroke(s, 2.4 * u);
    }
  }
};

/** open "D" mouth with a white teeth band (+ tongue) */
const dmouth = (p: Pen, mx: number, y: number, rx: number, ry: number, u: number, tongue = false) => {
  p.ell(mx, y, rx, ry, MOUTH, 0, 0, 180);
  p.clip([[mx - rx, y], [mx + rx, y], [mx + rx, y + 3 * u], [mx - rx, y + 3 * u]], () => p.ell(mx, y, rx, ry, WHITE, 0, 0, 180));
  if (tongue) p.ell(mx + 2 * u, y + 0.62 * ry, 0.4 * rx, 0.28 * ry, TONGUE, 0);
  p.ell(mx, y, rx, ry, null, 3 * u, 0, 180);
};

const mouth = (p: Pen, kind: MouthK, mx: number, my: number, u: number, k = 1) => {
  const mw = 4 * u;
  switch (kind) {
    case "dash": p.stroke([[mx - 5.5 * u * k, my], [mx + 5.5 * u * k, my - 0.8 * u]], mw); break;
    case "frown": p.arc(mx, my + 3 * u, 6.5 * u * k, 3.5 * u, 200, 340, mw); break;
    case "smirk": p.arc(mx + u, my - 3 * u, 7 * u * k, 4 * u, 10, 150, mw); break;
    case "smile": p.arc(mx, my - 3 * u, 8 * u * k, 4.5 * u, 20, 160, mw); break;
    case "smileWide": p.arc(mx, my - 4 * u, 11 * u * k, 6 * u, 15, 165, mw); break;
    case "grin": dmouth(p, mx, my - u, 12 * u * k, 8 * u, u); break;
    case "laugh": dmouth(p, mx, my, 16 * u * k, 11 * u, u, true); break;
    case "o": p.ell(mx + 4 * u, my, 3.5 * u, 4 * u, MOUTH, 2.8 * u); break;
    case "O": p.ell(mx, my + 2 * u, 9 * u * k, 11 * u, MOUTH, 3.2 * u); break;
    /** open shouting mouth: a wide dark oval with the upper teeth and tongue, no upturned corners */
    case "yell": {
      const rx = 15 * u * k, ry = 11 * u;
      p.ell(mx, my, rx, ry, MOUTH, 0);
      p.clip([[mx - rx - u, my - ry], [mx + rx + u, my - ry], [mx + rx + u, my - 0.45 * ry], [mx - rx - u, my - 0.45 * ry]],
        () => p.ell(mx, my, rx, ry, WHITE, 0));
      p.clip(ellPts(mx, my, rx, ry, 0, 360), () => p.ell(mx + 1 * u, my + 0.42 * ry, 0.42 * rx, 0.3 * ry, TONGUE, 0));
      p.ell(mx, my, rx, ry, null, 2.6 * u);
      break;
    }
    case "wave": { const s: P2[] = []; for (let i = 0; i <= 12; i++) s.push([mx - 9 * u * k + i * 1.5 * u * k, my + 1.5 * u * Math.sin(i * 1.3)]); p.stroke(s, 3 * u); break; }
    case "teeth":
      p.poly([[mx - 12 * u * k, my - 4 * u], [mx + 12 * u * k, my - 4 * u], [mx + 11 * u * k, my + 4 * u], [mx - 11 * u * k, my + 4 * u]], WHITE, 3 * u);
      for (const j of [-1, 0, 1]) p.stroke([[mx + j * 6 * u * k, my - 4 * u], [mx + j * 6 * u * k, my + 4 * u]], 1.5 * u);
      break;
    case "lick": p.arc(mx, my - 3 * u, 8 * u * k, 4.5 * u, 20, 160, mw); p.ell(mx + 6 * u * k, my + 3 * u, 3.6 * u, 4.6 * u, TONGUE, 2.4 * u); break;
  }
};

/** face v2 (front / 3-4). u = 1 % of the head path width W. Eyes 26u apart on the centre line, brows 20u up, mouth 20u
 *  down, everything slid toward the facing side. No blush, no catchlights. */
const faceFront = (p: Pen, cx: number, cy: number, W: number, expr: Expr, facing: number, look: number, lid: number, brim: boolean,
  skin: string, moustache?: string, stout = false, brow = 0) => {
  const u = W / 100, F = FACE[expr], fx = cx + 7 * u * facing;
  const ex = (F.eye[0] === "shock" ? 12 : 13) * u, ey = cy;
  for (const side of [-1, 1]) {
    const x = fx + side * ex;
    const kind = eyeKind(F.eye[(facing ? side === facing : side > 0) ? 1 : 0], lid);
    eye(p, kind, x, ey, u, side, look, skin);
    const [dI, dO] = F.brow, by = ey - (brim ? 17 : 20) * u - brow * u;
    if (kind === "shock" || kind === "shockHalf") p.arc(x, by - 6 * u, 9 * u, 3 * u, 200, 340, 4 * u);
    else taper(p, [x - side * 8.5 * u, by + dI * u], [x + side * 8.5 * u, by + dO * u], 5 * u, 2.5 * u);
  }
  const mx = cx + 8 * u * facing, my = cy + 20 * u;
  mouth(p, F.mouth, mx, my, u);
  if (moustache) for (const s of [-1, 1])
    taper(p, [mx + s * 1.5 * u, cy + 12.5 * u], [mx + s * (stout ? 19 : 15) * u, cy + (stout ? 10.5 : 15) * u], stout ? 5.5 * u : 4.5 * u, 1.6 * u, moustache);
  if (expr === "nervous") p.ell(cx + 40 * u * (facing || 1), cy - 22 * u, 3 * u, 5 * u, "#9fd4ff", 2 * u);
};

/** profile face (facing screen-right): one eye, brow, nose tick, mouth near the front edge; no skin bump nose, no ear */
const faceSide = (p: Pen, hx: number, hy: number, W: number, expr: Expr, lid: number, brim: boolean, skin: string, moustache?: string, stout = false) => {
  const u = W / 100, F = FACE[expr], ex = hx + 27 * u, ey = hy;
  const kind = eyeKind(F.eye[1], lid);
  eye(p, kind, ex, ey, u, 1, 0.6, skin);
  const by = ey - (brim ? 17 : 20) * u, [dI, dO] = F.brow;
  if (kind === "shock" || kind === "shockHalf") p.arc(ex, by - 6 * u, 9 * u, 3 * u, 200, 340, 4 * u);
  else taper(p, [ex + 8 * u, by + dI * u], [ex - 7 * u, by - u + dO * u], 5 * u, 2.5 * u);
  p.stroke([[hx + 44 * u, hy + 4 * u], [hx + 47.5 * u, hy + 9 * u], [hx + 43 * u, hy + 10 * u]], 3 * u);
  mouth(p, F.mouth, hx + 33 * u, hy + 21 * u, u, 0.62);
  if (moustache) taper(p, [hx + 41 * u, hy + 13.5 * u], [hx + 25 * u, hy + (stout ? 11.5 : 16) * u], stout ? 5.5 * u : 4.5 * u, 1.6 * u, moustache);
  if (expr === "nervous") p.ell(hx - 30 * u, hy - 24 * u, 3 * u, 5 * u, "#9fd4ff", 2 * u);
};

// ---------------- hats ----------------
const BONNET = "#e9cf8f", BONNET_BRIM = "#d6b46a";
/** parts of a hat that sit behind the head (bonnet) */
const hatBehind = (p: Pen, o: Outfit, H: Blob, cx: number, hc: number, light: number, thick: number, ow: number, side: boolean) => {
  if (o.hat !== "bonnet" && o.hat !== "hood") return;
  const col = o.hat === "hood" ? (o.cap ?? "#3e5a34") : BONNET;
  const bb = blobPts(cx - (side ? 12 : 0) * (H.a / 50), hc - 0.07 * 2 * H.b, { ...H, a: H.a * (o.hat === "hood" ? 1.22 : 1.17), b: H.b * 1.13, asym: 0, egg: 0.04, seed: H.seed + 3 });
  p.shadedFill(bb, col, mul(col, SH_CLOTH), light, H.a * 1.17);
  p.inkRing(bb, ow * 0.85, thick);
};

const hatOn = (p: Pen, o: Outfit, hp: P2[], H: Blob, cx: number, hc: number, light: number, seed: number, facing: number, side: boolean) => {
  const W = 2 * H.a, HH = 2 * H.b, u = W / 100, crown = hc - H.b, ow = 0.85 * 5 * u;
  const a = H.rot + rad(4 * (rnd(seed, 20) - 0.5)); // tilt with the head, +-2 deg extra
  const R = (pts: P2[]) => rotPts(pts, a, cx, hc);
  const sag = (yb: number, wb: number): P2[] => {
    const base: P2[] = [];
    for (let i = 0; i <= 12; i++) { const t = i / 12; base.push([cx + wb * (2 * t - 1), yb + 3 * u * (1 - (2 * t - 1) ** 2)]); }
    return base;
  };
  if (o.hat === "shako" || o.hat === "shako_tall") {
    const tall = o.hat === "shako_tall", yb = crown + 0.25 * HH, ht = (tall ? 0.66 : 0.56) * HH, wb = 46 * u, wt = 52 * u;
    const body = R([...sag(yb, wb).reverse(), [cx - wt, yb - ht], [cx + wt, yb - ht]]);
    p.shadedFill(body, "#3a3d47", "#24262d", light, wt, 0.4);
    if (tall) p.clip(body, () => p.band(R([[cx - wt - 5 * u, yb - ht + 0.07 * HH], [cx + wt + 5 * u, yb - ht + 0.07 * HH]]), "#e8c45a", 0.06 * HH, 1.5 * u));
    p.poly(body, null, ow);
    const deg = (a * 180) / Math.PI;
    if (side) {
      p.poly(R([[cx + 36 * u, yb - 1 * u], [cx + 60 * u, yb + 8 * u], [cx + 34 * u, yb + 6 * u]]), "#16171b", 2.5 * u);
      const [tx, ty] = R([[cx + 24 * u, yb - ht - 6 * u]])[0];
      p.ell(tx, ty, 7 * u, 7 * u, "#2b7a4b", 2.5 * u);
    } else {
      const [px, py] = R([[cx + 3 * u * facing, yb + 3 * u]])[0];
      p.ell(px, py, 34 * u, 0.045 * HH, "#16171b", 2.5 * u, 0, 180, deg); // peak
      const [bx, by] = R([[cx, yb - 0.45 * ht]])[0];
      p.ell(bx, by, 7 * u, 6 * u, tall ? "#e8c45a" : "#c9ccd2", 2 * u, 0, 360, deg); // badge plate
      p.arc(bx, by, 3.5 * u, 2.8 * u, 200, 500, 1.6 * u);
      const [tx, ty] = R([[cx, yb - ht - 6 * u]])[0];
      p.ell(tx, ty, 7 * u, 7 * u, "#2b7a4b", 2.5 * u); // green tuft
    }
  } else if (o.hat === "cap" || o.hat === "hair") {
    const cut = crown + (o.hat === "cap" ? 0.3 : 0.42) * HH;
    const keep = (x: number, y: number) => y < cut || (side && o.hat === "hair" && x < cx - 6 * u && y < hc + 0.42 * H.b);
    // start the arc at the first kept point after a dropped one, so the kept run is contiguous and the cut closes it
    const n = hp.length, startIdx = Math.max(0, hp.findIndex(([x, y], i) => keep(x, y) && !keep(hp[(i + n - 1) % n][0], hp[(i + n - 1) % n][1])));
    const arc = [...hp.slice(startIdx), ...hp.slice(0, startIdx)].filter(([x, y]) => keep(x, y))
      .map(([x, y]) => [cx + (x - cx) * 1.03, hc + (y - hc) * 1.03] as P2);
    if (arc.length < 3) return;
    if (o.hat === "hair") { // scalloped lower edge
      const [x0, y0] = arc[arc.length - 1], [x1, y1] = arc[0];
      for (let i = 1; i < 6; i++) arc.push([x0 + ((x1 - x0) * i) / 6, y0 + ((y1 - y0) * i) / 6 + (i % 2 ? 4 * u : 0)]);
    }
    const col = o.hat === "cap" ? o.cap! : o.hair!;
    p.shadedFill(arc, col, mul(col, SH_FELT), light, H.a, 0.35);
    p.poly(arc, null, ow);
    if (o.hat === "hair") {
      const s = side ? -1 : facing || 1;
      p.stroke([[cx + s * 10 * u, cut - 30 * u], [cx + s * 2 * u, cut - 12 * u]], 1.2 * u);
    }
    if (o.hat === "cap") {
      const deg = (a * 180) / Math.PI;
      if (side) p.poly(R([[cx + 40 * u, cut - 2 * u], [cx + 74 * u, cut + 4 * u], [cx + 40 * u, cut + 6 * u]]), shade(col, 0.8), ow);
      else {
        const s = facing || (rnd(seed, 21) < 0.5 ? -1 : 1), [px, py] = R([[cx + s * 4 * u, cut + 1.5 * u]])[0];
        p.ell(px, py, 32 * u, 0.06 * HH, shade(col, 0.8), ow, 0, 180, deg);
      }
    }
  } else if (o.hat === "tophat") {
    const yb = crown + 0.22 * HH, ht = 0.8 * HH, wb = 0.31 * W, wt = 0.33 * W, col = "#2e2a36";
    const body = R([...sag(yb, wb).reverse(), [cx - wt, yb - ht], [cx + wt, yb - ht]]);
    p.shadedFill(body, col, mul(col, SH_FELT), light, wt, 0.4);
    p.clip(body, () => p.band(R([[cx - wt - 4 * u, yb - 0.13 * HH], [cx + wt + 4 * u, yb - 0.13 * HH]]), shade(o.jacket, 0.9), 0.14 * HH, 0.8 * u));
    p.poly(body, null, ow);
    const [bx, by] = R([[cx, yb + 1 * u]])[0];
    p.ell(bx, by, 0.45 * W, 0.05 * HH, "#1d1b22", ow, 0, 360, (a * 180) / Math.PI);
  } else if (o.hat === "bonnet") {
    const [bx, by] = R([[cx + (side ? 6 * u : 0), crown + 0.16 * HH]])[0];
    p.arc(bx, by, 0.5 * W, 0.2 * HH, 200, 340, 7 * u, BONNET_BRIM);
    p.arc(bx, by, 0.5 * W + 3.5 * u, 0.2 * HH + 3.5 * u, 200, 340, 1.2 * u);
    const cy = hc + H.b * 0.98;
    p.stroke([[cx - 14 * u, cy - 4 * u], [cx, cy + 2 * u], [cx + 14 * u, cy - 4 * u]], 2 * u, BONNET_BRIM);
  } else if (o.hat === "helm") {
    // open bascinet: a steel dome over the crown, a riveted brow band, a thin nose guard, one red horsehair plume.
    // Everything is drawn above the eyes: eyes at hc, brows 20u up, the band sits at crown + .3 HH (well clear).
    const steel = "#c3ccd8", dark = "#98a3b2", gold = o.buttons ?? "#e8c45a", plume = o.plume ?? "#c0353a";
    const yb = crown + 0.30 * HH, wb = 0.5 * W, top = crown - 0.02 * HH;
    const body: P2[] = [];
    for (let i = 0; i <= 10; i++) { const t = i / 10; body.push([cx + wb * (2 * t - 1), yb + 3 * u * (1 - (2 * t - 1) ** 2)]); }
    for (let i = 1; i < 12; i++) { const a2 = Math.PI * (i / 12); body.push([cx + wb * Math.cos(a2), yb - (yb - top) * Math.sin(a2)]); }
    p.shadedFill(R(body), steel, dark, light, wb, 0.35);
    p.poly(R(body), null, ow);
    // brow band + rivets
    p.clip(R(body), () => p.band(R([[cx - wb, yb - 3 * u], [cx + wb, yb - 3 * u]]), dark, 0.09 * HH, 1.4 * u));
    for (let i = -2; i <= 2; i++) { const [rx2, ry2] = R([[cx + i * 18 * u, yb + 2 * u]])[0]; p.dot(rx2, ry2, 2.6 * u, gold); }
    // nose guard: only in profile, where it reads as a steel bar down the front of the face; head-on it landed
    // between the eyes and merged with the far eye into a black cross
    if (side) {
      const [gx, gy] = R([[cx + 0.44 * W, yb - 1 * u]])[0];
      p.poly([[gx - 6 * u, gy], [gx + 6 * u, gy], [gx + 3 * u, gy + 0.36 * HH], [gx - 3 * u, gy + 0.36 * HH]], steel, 2.4 * u);
    }
    // plume: tapered horsehair crest, swept back off the dome
    const base: P2 = side ? R([[cx - 0.1 * W, top + 4 * u]])[0] : R([[cx - 6 * u, top + 4 * u]])[0];
    const mid: P2 = side ? [base[0] - 0.34 * W, base[1] - 0.12 * HH] : [base[0] + 0.26 * W, base[1] - 0.22 * HH];
    const tip: P2 = side ? [base[0] - 0.62 * W, base[1] + 0.16 * HH] : [base[0] + 0.46 * W, base[1] + 0.2 * HH];
    for (const [w0, w1, col] of [[17 * u, 10 * u, plume], [10 * u, 3 * u, mul(plume, [0.72, 0.7, 0.74])]] as [number, number, string][]) {
      const sp = curve(base, mid, tip, 8), left = sp.map(([x2, y2], i) => [x2, y2 - w0 + (w1 - w0) * (i / 8)] as P2);
      const right = sp.map(([x2, y2], i) => [x2, y2 + w0 - (w0 - w1) * (i / 8)] as P2).reverse();
      p.poly([...left, ...right], col, 2.2 * u);
    }
    p.dot(base[0], base[1], 5 * u, gold);
  } else if (o.hat === "skullcap") {
    // zucchetto: a small round cap hugging the crown. Rim = a gently arched line about a quarter head below the crown,
    // so the forehead and brows stay completely clear. (The first version drew the lower half of an ellipse: its black
    // rim dipped onto the brow line and hid the whole expression.)
    const col = o.cap ?? o.jacket, red = mul(col, SH_CLOTH), hw = 0.52 * W;
    const rimY = crown + 0.235 * HH, archAt = (x: number) => rimY - 0.035 * HH * (1 - clamp((x - cx) / hw, -1, 1) ** 2);
    const keep = hp.filter(([x, y]) => y < archAt(x));
    if (keep.length > 2) {
      const xa = keep[keep.length - 1][0], xb = keep[0][0], rim: P2[] = [];
      for (let i = 0; i <= 16; i++) { const x = xa + ((xb - xa) * i) / 16; rim.push([x, archAt(x)]); }
      p.gradFill([...keep, ...rim], col, red, light);
      p.stroke(rim, 0.85 * ow);
    }
  } else if (o.hat === "hood") {
    // cloth hood: the rear blob is in hatBehind; the front rim rides the crown of the head
    const col = o.cap ?? "#3e5a34";
    p.clip(hp, () => p.gradFill(ellPts(cx, crown + 0.06 * HH, 0.52 * W, 0.3 * H.b, 0, 360), col, mul(col, SH_CLOTH), light));
    p.ell(cx, crown + 0.22 * HH, 0.44 * W, 0.075 * HH, null, ow * 0.85, 0, 180);
    if (!side) for (const s of [-1, 1]) p.line([[cx + s * 0.3 * W, crown + 0.26 * HH], [cx + s * 0.34 * W, crown + 0.62 * HH]], mul(col, [0.8, 0.82, 0.86]), 2.4 * u);
  } else if (o.hat === "straw") {
    const col = o.cap ?? "#d9b86a", yb = crown + 0.26 * HH;
    const [bx, by] = R([[cx + (side ? 10 * u : 0), yb]])[0];
    p.ell(bx, by + 4 * u, 0.64 * W, 0.13 * HH, mul(col, [0.86, 0.84, 0.8]), ow, 0, 360, (a * 180) / Math.PI);
    p.poly(R([[bx - 0.4 * W, by + 2 * u], [bx + 0.4 * W, by + 2 * u], [bx + 0.36 * W, by - 0.2 * HH], [bx - 0.36 * W, by - 0.2 * HH]]), col, ow);
    p.ell(bx, by - 0.2 * HH, 0.36 * W, 0.09 * HH, col, ow * 0.8, 0, 360, (a * 180) / Math.PI);
    p.poly([[bx - 0.37 * W, by - 0.02 * HH], [bx + 0.37 * W, by - 0.02 * HH], [bx + 0.36 * W, by - 0.11 * HH], [bx - 0.36 * W, by - 0.11 * HH]], "#7a4f33", 1.6 * u);
  }
};

/** a parchment scroll with a wax seal, drawn at a hand (front or side view); sc = overall size (1 = base),
 *  seal = wax-seal scale around its own centre (0 = not stamped yet, >1 = the fresh pop) */
const drawScroll = (p: Pen, hx: number, hy: number, u: number, ang = 0, sc = 1, seal = 1) => {
  const k = u * sc, R = (pts: P2[]) => rotPts(pts, ang, hx, hy);
  p.poly(R([[hx - 26 * k, hy - 9 * k], [hx + 26 * k, hy - 11 * k], [hx + 28 * k, hy + 10 * k], [hx - 24 * k, hy + 12 * k]]), "#f4e6c6", 2.6 * k);
  // ruled lines with no ink halo: p.line's default rim (2*ol*0.9) is thicker than the parchment itself
  for (let i = 0; i < 3; i++) p.line(R([[hx - 18 * k, hy - 4 * k + i * 5 * k], [hx + 14 * k, hy - 5 * k + i * 5 * k]]), "#9b7550", 1.4 * k, false);
  p.ell(hx - 26 * k, hy + 1.5 * k, 5 * k, 11 * k, "#e3cfa2", 2.4 * k, 0, 360, ang);
  p.ell(hx + 28 * k, hy, 5 * k, 11 * k, "#e3cfa2", 2.4 * k, 0, 360, ang);
  if (seal > 0) {
    const sx = hx + 7 * k, sy = hy + 2 * k;
    p.ell(sx, sy, 6.5 * k * seal, 6.5 * k * seal, "#b3312f", 2.2 * k);
    p.ell(sx, sy, 2.6 * k * seal, 2.6 * k * seal, "#7c1f1e", 0);
  }
};

/** arming sword drawn from a fist, ang = 0 points the blade straight up from the hand */
const drawSword = (p: Pen, hx: number, hy: number, u: number, ang: number) => {
  const R = (pts: P2[]) => rotPts(pts, ang, hx, hy);
  p.band(R([[hx, hy + 16 * u], [hx, hy - 6 * u]]), "#6a4526", 5.5 * u, 1.4 * u, "round");
  p.dot(hx, hy + 17 * u, 4.5 * u, "#d7b25a");
  p.poly(R([[hx - 18 * u, hy - 9 * u], [hx + 18 * u, hy - 9 * u], [hx + 21 * u, hy - 16 * u], [hx - 21 * u, hy - 16 * u]]), "#d7b25a", 2 * u);
  // long enough to read as a sword in the open gap instead of a pocket dagger
  p.poly(R([[hx - 11 * u, hy - 16 * u], [hx + 11 * u, hy - 16 * u], [hx + 8 * u, hy - 172 * u], [hx, hy - 192 * u], [hx - 8 * u, hy - 172 * u]]), "#e3e9f0", 2.2 * u);
  p.line(R([[hx, hy - 22 * u], [hx, hy - 160 * u]]), "#a9b3c0", 1.8 * u);
};

// ---------------- bodies ----------------
export type Arms = [P2[], P2[]];
/** held prop; for the hammer and sword the number is the strike 0 (raised) .. 1 (struck) */
export type Prop = null | "icecream" | "shako" | "scroll" | ["hammer", number] | ["sword", number];

const BUILD: Record<Build, { a: number; torso: number; legs: number; tw: number }> = {
  adult: { a: 118, torso: 1.1, legs: 1.4, tw: 0.8 },
  stout: { a: 118, torso: 1.15, legs: 1.32, tw: 0.92 },
  kid: { a: 112, torso: 0.85, legs: 1.0, tw: 0.72 },
};

export type FrontOpts = {
  phase?: number; expr?: Expr; mode?: "march" | "stroll" | "stand" | "sit" | "fall"; look?: number; blink?: boolean | number; lift?: number;
  prop?: Prop; tilt?: number; headTilt?: number; wave?: number; propScale?: number;
  /** scroll only: 0 = held low by the belt, 1 = presented; >1 overshoots the presentation height */
  propLift?: number;
  /** scroll only: wax-seal scale (0 until the stamp lands) */
  seal?: number;
  /** extra brow lift in u (up = smug); positive raises both brows off the eyes */
  brow?: number;
  /** canvas angle the key light comes FROM (painted crescent + thick outline side) */
  light?: number; facing?: -1 | 0 | 1; seed?: number;
};

const footStroke = (p: Pen, a: P2, b: P2, w: number, col: string) => {
  if (col !== INK) p.stroke([a, b], w + 3, INK);
  p.stroke([a, b], w, col);
};

/** soft shadow the head drops on the top of the torso (a dark band under the jaw, pushed away from the light) */
const chinShadow = (p: Pen, torso: P2[], cx: number, chin: number, hh: number, w: number, light: number) => {
  const g = p.g, r = 0.62 * w, [gx, gy] = p.P(cx - Math.cos(light) * 0.12 * w, chin + 0.1 * hh);
  p.clip(torso, () => {
    const gr = g.createRadialGradient(gx, gy, 0, gx, gy, r);
    gr.addColorStop(0, "rgba(30,18,34,0.30)"); gr.addColorStop(0.55, "rgba(30,18,34,0.15)"); gr.addColorStop(1, "rgba(30,18,34,0)");
    g.fillStyle = gr; g.fillRect(-4000, -4000, 8000, 8000);
  });
};

export const bodyFront = (p: Pen, o: Outfit, opts: FrontOpts) => {
  const { phase = 0, expr = "neutral", mode = "march", look = 0, blink = false, lift = 60, prop = null, tilt = 0, headTilt = 0, wave,
    propScale = 1, propLift = 1, seal = 1, brow = 0, light = DEF_LIGHT, facing = 0, seed = 1 } = opts;
  const Bd = BUILD[o.build ?? "adult"], skin = o.skin ?? SKIN, two = Math.PI * 2, lid = lidOf(blink);
  const H = headBlob(seed, Bd.a, facing), W = 2 * H.a, HH = 2 * H.b, u = W / 100;
  const tall = (1 + Bd.torso + Bd.legs) * HH, sole = 975;
  // body bob 5 % (march) / 3 % (stroll) of the height, lowest at contact (phase 0 and 0.5)
  const bob = mode === "march" ? 0.025 * tall * Math.cos(2 * two * phase) : mode === "stroll" ? 0.015 * tall * Math.cos(2 * two * phase) : 0;
  const torsoBot = mode === "sit" ? sole - 0.05 * HH : sole - Bd.legs * HH + bob;
  const chin = torsoBot - Bd.torso * HH, hc = chin - H.b, crown = hc - H.b, hipY = torsoBot - 0.12 * HH;
  const thick = thickAngle(light), ow = 5 * u;
  const legCol = mix(o.pants, INK, 0.55), armCol = mix(o.jacket, INK, 0.5), footCol = o.boots;
  const legW = 5.8 * u, footW = 7.5 * u;
  // ---- legs + feet (not rotated) ----
  p.rot = null;
  if (mode === "sit") {
    // seated on the ground: short legs tucked behind the coat, the boots are redrawn in front of the hem below
    for (const side of [-1, 1]) p.stroke([[300 + side * 12 * u, hipY], [300 + side * 18 * u, sole - 6 * u]], legW, legCol);
  } else if (mode === "fall") {
    const legs: [P2, P2, P2][] = [
      [[300 - 15 * u, hipY], [300 - 46 * u, hipY + 0.5 * HH], [300 - 70 * u, hipY + 0.72 * HH]],
      [[300 + 15 * u, hipY], [300 + 50 * u, hipY + 0.45 * HH], [300 + 76 * u, hipY + 0.22 * HH]],
    ];
    legs.forEach(([h, k, f], i) => {
      p.stroke(curve(h, k, f), legW, legCol);
      footStroke(p, f, [f[0] + (i ? 14 : -14) * u, f[1] + (i ? -6 : 4) * u], footW, footCol);
    });
  } else if (o.dress) {
    // the hem hides the knees, so the step reads through the boots: one lifts while the other plants
    for (const [side, ph] of [[-1, 0], [1, 0.5]] as const) {
      const up = mode === "march" ? Math.max(0, Math.sin(two * (phase + ph))) * 0.1 * HH : 0;
      const fx = 300 + side * 12 * u, fy = sole - 4 * u - up;
      p.stroke([[fx, sole - 0.4 * HH], [fx + side * u, fy]], legW, legCol);
      footStroke(p, [fx - side * 3 * u, fy], [fx + side * 12 * u, fy + u], footW, footCol);
    }
  } else {
    // march: each foot clears 35 % of the leg length (45 % when the stomp peaks) and the raised knee bows outward;
    // the lifted sole tilts toe-down so the step reads in a straight-on view as well
    const legLen = sole - 4 * u - hipY, amp = clamp(lift / 60, 0, 1.5);
    const L = mode === "march" ? legLen * (0.15 + 0.2 * amp) : mode === "stroll" ? lift * 0.55 : 0;
    for (const [side, ph] of [[-1, 0], [1, 0.5]] as const) {
      const up = Math.max(0, Math.sin(two * (phase + ph))) * L, kUp = L > 0 ? clamp(up / L, 0, 1) : 0;
      const hx = 300 + side * 15 * u, fx = 300 + side * (22 + 11 * kUp) * u, fy = sole - 4 * u - up;
      const k: P2 = [(hx + fx) / 2 + side * (1.5 * u + 0.6 * up), (hipY + fy) / 2 - 0.2 * up];
      p.stroke(curve([hx, hipY], k, [fx, fy]), legW, legCol);
      if (kUp > 0.12) footStroke(p, [fx - side * 4 * u, fy - 2 * u], [fx + side * 9 * u, fy + 9 * u], footW, footCol);
      else footStroke(p, [fx - side * 3 * u, fy], [fx + side * 13 * u, fy + 0.5 * u], footW, footCol);
    }
  }
  // ---- upper body: rotates about the hips (tilt + a small weight-shift sway on every step) ----
  const sway = mode === "march" ? 1.6 * Math.sin(two * phase) : mode === "stroll" ? 1.0 * Math.sin(two * phase) : 0;
  const A = tilt + sway;
  p.rot = A ? [rad(A), 300, hipY] : null;
  const dress = !!o.dress && mode !== "sit" && mode !== "fall";
  const T: Blob = { a: ((Bd.tw / 2) * W) / 1.06, b: 0.5 * (torsoBot - (chin - 0.25 * HH)), nTop: 2.2, nBot: 2.6, egg: o.build === "stout" ? 0.17 : 0.12,
    asym: 0.04 * facing, rot: 0, noise: 0.006, seed: seed + 7 };
  const tcx = 300 + 3 * u * facing, tcy = torsoBot - T.b, tp = blobPts(tcx, tcy, T);
  const sh = (side: number): P2 => [tcx + side * 0.85 * T.a, chin + 0.12 * HH];
  const hang = (side: number, fwd: number): [P2, P2, P2] => {
    const S = sh(side), ex = tcx + side * (1.12 * T.a + 4 * u);
    const hx = ex + side * 3 * u - side * 6 * u * Math.max(0, fwd) + side * 4 * u * Math.max(0, -fwd);
    return [S, [ex, S[1] + 0.48 * HH], [hx, chin + 1.04 * HH - Math.abs(fwd) * 9 * u]];
  };
  const sw = mode === "march" || mode === "stroll" ? Math.sin(two * phase) : 0;
  // rifle at the order: butt by the right hip, held by the hanging right hand, muzzle past the crown
  const R0: P2 = [300 + 47 * u, torsoBot + 0.12 * HH], R1: P2 = [300 + 64 * u, crown - 0.32 * HH];
  const rifle = !!o.rifle && (mode === "march" || mode === "stand" || mode === "stroll");
  type Arm = { pts: [P2, P2, P2]; front: boolean };
  const arms: Arm[] = [];
  if (mode === "sit") for (const side of [-1, 1]) arms.push({ pts: [sh(side), [tcx + side * (1.1 * T.a + 6 * u), sh(side)[1] + 0.4 * HH], [tcx + side * (1.2 * T.a + 10 * u), torsoBot + 0.04 * HH]], front: false });
  else if (mode === "fall") for (const side of [-1, 1]) arms.push({ pts: [sh(side), [tcx + side * (1.15 * T.a + 12 * u), sh(side)[1] - 0.25 * HH], [tcx + side * (1.3 * T.a + 24 * u), sh(side)[1] - 0.68 * HH]], front: false });
  else {
    arms.push({ pts: prop === "shako" ? hang(-1, 0) : hang(-1, -sw), front: false });
    if (rifle) {
      const G0 = lerp2(R0, R1, 0.1), G: P2 = [G0[0] + 2.2 * u * sw, G0[1] - 0.5 * u * Math.abs(sw)];
      arms.push({ pts: [sh(1), [tcx + 1.12 * T.a + 5 * u + 1.4 * u * sw, sh(1)[1] + 0.45 * HH], G], front: false });
    } else if (wave !== undefined) {
      const S = sh(1);
      arms.push({ pts: [S, [tcx + 1.1 * T.a + 10 * u + 3 * u * wave, S[1] - 0.22 * HH], [tcx + 1.18 * T.a + 16 * u + 12 * u * wave, S[1] - 0.6 * HH]], front: false });
    } else if (prop === "icecream") {
      const S = sh(1);
      arms.push({ pts: [S, [tcx + 1.05 * T.a + 4 * u, S[1] + 0.45 * HH], [tcx + 0.5 * T.a, S[1] + 0.4 * HH]], front: true });
    } else if (prop === "scroll") {
      // presented at chest height so the parchment clears the booth counter; propLift walks the hand up from the
      // belt and may overshoot past 1 for the bouncy settle
      const S = sh(1), L = clamp(propLift, 0, 1.25);
      const E: P2 = [tcx + (0.98 - 0.03 * (1 - L)) * T.a + 8 * u, S[1] + (0.42 - 0.22 * L) * HH];
      const Hd: P2 = [tcx + (0.4 - 0.1 * L) * T.a, S[1] + (0.55 - 0.4 * L) * HH];
      arms.push({ pts: [S, E, Hd], front: true });
    } else if (Array.isArray(prop) && prop[0] === "sword") {
      const S = sh(1), k = clamp(prop[1], 0, 1);
      const E = lerp2([tcx + 1.05 * T.a + 10 * u, S[1] + 0.3 * HH], [tcx + 1.2 * T.a + 14 * u, S[1] + 0.34 * HH], k);
      const Hd = lerp2([tcx + 1.3 * T.a + 26 * u, S[1] + 0.28 * HH], [tcx + 1.5 * T.a + 34 * u, S[1] + 0.3 * HH], k);
      arms.push({ pts: [S, E, Hd], front: true });
    } else if (Array.isArray(prop)) {
      const S = sh(1), k = clamp(prop[1], 0, 1);
      const E = lerp2([tcx + 1.1 * T.a + 10 * u, S[1] - 0.15 * HH], [tcx + 1.2 * T.a + 10 * u, S[1] + 0.3 * HH], k);
      const Hd = lerp2([tcx + 1.15 * T.a + 14 * u, S[1] - 0.55 * HH], [tcx + 1.45 * T.a + 22 * u, S[1] + 0.35 * HH], k);
      arms.push({ pts: [S, E, Hd], front: true });
    } else arms.push({ pts: hang(1, sw), front: false });
  }
  const drawArm = (a: Arm) => { p.stroke(curve(a.pts[0], a.pts[1], a.pts[2]), 5.2 * u, armCol); p.dot(a.pts[2][0], a.pts[2][1], 5.5 * u); };
  // behind the body: rifle, sword, arms
  if (rifle) {
    p.band([R0, R1], "#7a4b2a", 5 * u, 1.5 * u, "round");
    p.band([lerp2(R0, R1, 0.6), R1], "#8d949c", 2.4 * u, 1.2 * u, "round");
  }
  if (o.sword && mode !== "sit") {
    const s0: P2 = [tcx - 0.75 * T.a, torsoBot - 0.2 * HH];
    p.band([s0, [s0[0] - Math.sin(rad(25)) * 0.8 * HH, s0[1] + Math.cos(rad(25)) * 0.8 * HH]], "#c9ccd2", 3 * u, 1.2 * u, "round");
  }
  for (const a of arms) if (!a.front) drawArm(a);
  // torso / dress: shaded fill -> clothing clipped to it -> thick-thin ink ring
  if (dress) {
    const D: Blob = { a: 0.5 * W * 0.98, b: 0.5 * ((sole - 0.35 * HH) - (chin - 0.2 * HH)), nTop: 2.0, nBot: 3.0, egg: 0.35, asym: 0.03 * facing, rot: 0, noise: 0.006, seed: seed + 9 };
    const dp = blobPts(300, sole - 0.35 * HH - D.b, D);
    p.gradFill(dp, o.dress!, mul(o.dress!, SH_CLOTH), light);
    // gold canonicals: hem, two stoles and a chest cross (the portly pardoner must read as a priest at a glance)
    const gold = o.buttons ?? "#e8c45a", hem = sole - 0.40 * HH;
    p.clip(dp, () => {
      p.band([[300 - W, hem], [300 + W, hem]], gold, 0.05 * HH, 1.5 * u);
      for (const s of [-1, 1]) p.band([[300 + s * 24 * u, chin + 0.16 * HH], [300 + s * 33 * u, hem]], gold, 9 * u, 1.3 * u);
      p.band([[300, chin + 0.26 * HH], [300, chin + 0.5 * HH]], gold, 5 * u, 1.1 * u);
      p.band([[300 - 13 * u, chin + 0.37 * HH], [300 + 13 * u, chin + 0.37 * HH]], gold, 5 * u, 1.1 * u);
    });
    p.inkRing(dp, ow, thick);
    const Sw: Blob = { a: 0.37 * W, b: 0.3 * HH, nTop: 2.2, nBot: 2.4, egg: 0.1, asym: 0, rot: 0, noise: 0.006, seed: seed + 8 };
    const sp = blobPts(300, chin + 0.12 * HH, Sw);
    p.gradFill(sp, o.jacket, mul(o.jacket, SH_CLOTH), light);
    p.inkRing(sp, ow * 0.9, thick);
  } else {
    p.gradFill(tp, o.jacket, mul(o.jacket, SH_CLOTH), light);
    p.clip(tp, () => {
      if (o.belt) {
        for (const s of [-1, 1]) p.band([[tcx - s * 0.75 * T.a, chin - 0.05 * HH], [tcx + s * 0.8 * T.a, torsoBot - 0.1 * HH]], o.belt!, 5.5 * u, 1.8 * u);
        const xc = tcx + 0.025 * T.a, yc = chin - 0.05 * HH + (torsoBot - 0.1 * HH - (chin - 0.05 * HH)) * (0.75 / 1.55);
        p.poly([[xc - 3.5 * u, yc - 3.5 * u], [xc + 3.5 * u, yc - 3.5 * u], [xc + 3.5 * u, yc + 3.5 * u], [xc - 3.5 * u, yc + 3.5 * u]], "#d9dde0", 1.5 * u);
      }
      if (o.sash) p.band([[tcx - 1.3 * T.a, torsoBot - 0.32 * HH], [tcx + 1.3 * T.a, torsoBot - 0.32 * HH]], o.sash, 0.13 * HH, 1.8 * u);
      for (let i = 0; i < 4; i++) {
        const y = chin + 0.12 * HH + i * 0.2 * HH;
        if (o.sash && Math.abs(y - (torsoBot - 0.32 * HH)) < 0.08 * HH) continue;
        p.dot(tcx + 2 * u * facing, y, 2.2 * u + 0.8 * u, INK); p.dot(tcx + 2 * u * facing, y, 2.2 * u, o.buttons ?? shade(o.jacket, 0.7));
      }
    });
    if (o.sash) { const s = facing || 1; p.poly([[tcx + s * 0.55 * T.a, torsoBot - 0.3 * HH], [tcx + s * 0.75 * T.a, torsoBot + 0.05 * HH], [tcx + s * 0.45 * T.a, torsoBot + 0.02 * HH]], o.sash, 1.6 * u); }
    chinShadow(p, tp, tcx, chin, HH, W, light);
    p.inkRing(tp, ow, thick);
    if (mode === "sit") for (const side of [-1, 1]) {
      // boots resting in front of the hem (legs straight out toward the camera), so he reads as seated, not legless
      const bx = 300 + side * 19 * u, by = sole - 5 * u;
      p.ell(bx, by, 10 * u, 5.5 * u, footCol, 2.2 * u);
      p.arc(bx, by, 6 * u, 3.2 * u, 200, 340, 1.4 * u, shade(footCol, 0.55));
    }
    if (o.armor) {
      // plate seams + pauldrons over the jacket (the steel outfit reads as armour, not a grey coat)
      p.clip(tp, () => {
        p.line([[tcx, chin + 0.18 * HH], [tcx, torsoBot - 0.16 * HH]], "#7f8897", 1.7 * u);
        for (const s of [-1, 1]) p.arc(tcx, chin + 0.55 * HH, 0.42 * T.a, 0.3 * HH, s < 0 ? 20 : 160, s < 0 ? 160 : 300, 1.7 * u, "#7f8897");
      });
      for (const s of [-1, 1]) {
        const [px, py] = sh(s);
        const pp = ellPts(px + s * 0.02 * T.a, py + 0.02 * HH, 0.3 * T.a, 0.135 * HH, 0, 360);
        p.gradFill(pp, "#c9d3df", "#8d98a7", light);
        p.inkRing(pp, ow * 0.8, thick);
        p.line([[px - s * 0.16 * T.a, py + 0.03 * HH], [px + s * 0.16 * T.a, py + 0.08 * HH]], "#7f8897", 1.5 * u);
      }
    }
  }
  // in front of the body: hands holding props
  for (const a of arms) if (a.front) {
    drawArm(a);
    const [hx, hy] = a.pts[2];
    if (prop === "icecream") {
      p.poly([[hx - 8 * u, hy - 12 * u], [hx + 8 * u, hy - 12 * u], [hx, hy + 7 * u]], "#e0a35a", 1.8 * u);
      p.ell(hx, hy - 19 * u, 11 * u, 10 * u, "#f7c6d9", 2.2 * u);
      p.dot(hx, hy, 5.5 * u);
    } else if (prop === "scroll") {
      drawScroll(p, hx, hy - 4 * u, u, -0.08, propScale, seal);
      p.dot(hx, hy, 5.5 * u);
    } else if (Array.isArray(prop) && prop[0] === "sword") {
      drawSword(p, hx, hy, u, rad(82 + 8 * clamp(prop[1], 0, 1)));
      p.dot(hx, hy, 5.5 * u);
    } else if (Array.isArray(prop)) {
      const ang = rad(-70 + 105 * clamp(prop[1], 0, 1));
      const Rh = (pts: P2[]) => rotPts(pts, ang, hx, hy);
      p.band(Rh([[hx, hy + 12 * u], [hx, hy - 44 * u]]), "#8a5a34", 5 * u, 1.5 * u, "round");
      p.poly(Rh([[hx - 12 * u, hy - 58 * u], [hx + 20 * u, hy - 58 * u], [hx + 20 * u, hy - 42 * u], [hx - 12 * u, hy - 42 * u]]), "#7d848c", 2.2 * u);
      p.dot(hx, hy, 5.5 * u);
    }
  }
  if (prop === "shako") { // carried by the left hand
    const [hx, hy] = arms[0].pts[2];
    p.poly([[hx - 14 * u, hy + 3 * u], [hx + 14 * u, hy + 3 * u], [hx + 16 * u, hy + 30 * u], [hx - 16 * u, hy + 30 * u]], "#3a3d47", 2.2 * u);
    p.ell(hx, hy + 31 * u, 3.5 * u, 3.5 * u, "#2b7a4b", 1.5 * u);
    p.dot(hx, hy, 5.5 * u);
  }
  // ---- head: rotates with the body, plus its own tilt about the chin ----
  const Ah = A + headTilt, [cpx, cpy] = rotAbout([300, chin], rad(A), [300, hipY]);
  p.rot = Ah ? [rad(Ah), 300, chin, cpx - 300, cpy - chin] : null;
  hatBehind(p, o, H, 300, hc, light, thick, ow, false);
  const hp = blobPts(300, hc, H);
  p.gradFill(hp, skin, mul(skin, SH_SKIN), light, 0.4);
  p.inkRing(hp, ow, thick);
  hatOn(p, o, hp, H, 300, hc, light, seed, facing, false);
  const brim = !!o.hat && o.hat !== "hair" && o.hat !== "bonnet" && o.hat !== "cap";
  faceFront(p, 300, hc, W, expr, facing, look, lid, brim, skin, o.moustache, o.build === "stout", brow);
  p.rot = null;
};

export type SideOpts = {
  phase?: number; expr?: Expr; mode?: "march" | "stand" | "swing" | "push"; blink?: boolean | number; stomp?: number; pose?: number;
  /** step length as a multiple of 0.8 m (370 units): matches 1.6 m/s at 2 steps/s; scale by the view's foreshortening */
  stride?: number; light?: number; seed?: number;
  /** push mode: where the hands land at pose 1, in final canvas units (e.g. the swing kid's back) */
  hand?: [number, number];
  /** held prop (side view): parchment, raised/struck sword (0..1) or a shaking fist */
  prop?: "scroll" | "fist" | ["sword", number]; propScale?: number;
  /** sword only as a fist (the blade is drawn as a separate camera-facing card when it has to cross the gap) */
  blade?: boolean;
};

/** two-bone leg, knee bending forward (+x) */
const ik = (hip: P2, ank: P2, l1: number, l2: number): P2 => {
  const dx = ank[0] - hip[0], dy = ank[1] - hip[1], d = clamp(Math.hypot(dx, dy), 1, l1 + l2 - 0.01);
  const A = Math.acos(clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)), k = Math.atan2(dy, dx) - A;
  return [hip[0] + l1 * Math.cos(k), hip[1] + l1 * Math.sin(k)];
};

/** hip height of the seated kid in `swing` mode (design units); swingKid seats the torso bottom on the plank */
const SWING_HIP = 733;

/** side view facing screen-right; march footfalls land at phase 0 (near foot) and 0.5 (far foot), like the front view.
 *  The stance foot is planted: it slides back at exactly the walking speed while the hip rises and falls over it. */
export const bodySide = (p: Pen, o: Outfit, opts: SideOpts) => {
  const { phase = 0, expr = "neutral", mode = "march", blink = false, stomp = 1, pose = 0, stride = 1, light = DEF_LIGHT, seed = 1 } = opts;
  const Bd = BUILD[o.build ?? "adult"], skin = o.skin ?? SKIN, two = Math.PI * 2, lid = lidOf(blink);
  const H: Blob = { ...headBlob(seed, Bd.a, 1), asym: 0.12, rot: rad((rnd(seed, 7) - 0.5) * 8) };
  const W = 2 * H.a, HH = 2 * H.b, u = W / 100, sole = 975, ankY = sole - 4 * u;
  const thick = thickAngle(light), ow = 5 * u;
  const legLen = (Bd.legs + 0.12) * HH - 4 * u, l1 = legLen / 2, l2 = legLen / 2;
  const nearCol = mix(o.pants, INK, 0.55), farCol = mix(o.pants, INK, 0.75), footCol = o.boots;
  type LegS = { ank: P2; pitch: number; near: boolean };
  const legs: LegS[] = [];
  let hipY = ankY - legLen * 0.995, lean = 0, nearFwd = 0;
  if (mode === "march") {
    const S = 370 * stride, liftH = Math.max(22, 40 + 70 * (stomp - 1));
    const st = (ph: number) => {
      const c = (((phase + ph) % 1) + 1) % 1;
      if (c < 0.5) { const s = c / 0.5; return { x: S / 2 - S * s, h: 0, stance: true, s }; }
      const s = (c - 0.5) / 0.5; // swing: cycloid in world space, so the foot leaves and lands at zero ground speed
      return { x: -S / 2 + S * s - (S / Math.PI) * Math.sin(2 * Math.PI * s), h: liftH * Math.sin(Math.PI * s), stance: false, s };
    };
    const nL = st(0), fL = st(0.5), stance = nL.stance ? nL : fL;
    const Leff = legLen * (1 - 0.035 * Math.sin(Math.PI * stance.s));
    hipY = ankY - Math.sqrt(Math.max(1, Leff * Leff - stance.x * stance.x));
    // extra rise at passing: reference side walks bob 3-7 % of height (the stance-foot geometry alone gives ~1.8 %)
    hipY -= 18 * (1 - Math.cos(2 * two * phase));
    for (const [L, near] of [[fL, false], [nL, true]] as const)
      legs.push({ ank: [300 + L.x, ankY - L.h], pitch: L.stance ? 0 : rad(35 * Math.sin(Math.PI * L.s) * (1 - 1.6 * L.s)), near });
    lean = 4 + 3 * Math.cos(2 * two * phase); // 7 deg at contact, 1 deg at passing
    nearFwd = nL.x / (S / 2);
  } else if (mode === "push") {
    hipY = ankY - 0.87 * legLen;
    legs.push({ ank: [300 - 0.5 * legLen, ankY], pitch: rad(-8), near: false }, { ank: [300 + 0.32 * legLen, ankY], pitch: 0, near: true });
    lean = 14 * pose;
  } else if (mode === "swing") {
    hipY = SWING_HIP;
    const a = rad(60 * pose);
    for (const [dx, near] of [[-6, false], [0, true]] as const) {
      const knee: P2 = [300 + l1 * 0.98 + dx * u, hipY + 6 * u];
      legs.push({ ank: [knee[0] + l2 * Math.sin(a), knee[1] + l2 * Math.cos(a)], pitch: -a * 0.5, near });
    }
  } else {
    legs.push({ ank: [300 - 4 * u, ankY], pitch: 0, near: false }, { ank: [300 + 4 * u, ankY], pitch: 0, near: true });
  }
  const torsoBot = hipY + 0.12 * HH, chin = torsoBot - Bd.torso * HH, hc = chin - H.b, crown = hc - H.b, hip: P2 = [300, hipY];
  p.rot = null;
  for (const L of legs) {
    const knee = mode === "swing" ? ([300 + l1 * 0.98 + (L.near ? 0 : -6 * u), hipY + 6 * u] as P2) : ik(hip, L.ank, l1, l2);
    const hp0: P2 = [300 + (L.near ? 0 : -5 * u), hipY];
    p.stroke(curve(hp0, knee, L.ank), 5.8 * u, L.near ? nearCol : farCol);
    const c = Math.cos(L.pitch), s = Math.sin(L.pitch);
    footStroke(p, [L.ank[0] - 3 * u * c, L.ank[1] - 3 * u * s], [L.ank[0] + 13 * u * c, L.ank[1] + 13 * u * s + 0.5 * u],
      7.5 * u, L.near ? footCol : footCol === INK ? INK : shade(footCol, 0.82));
  }
  // ---- upper body leans about the hip ----
  if (opts.prop === "fist" && mode === "stand") lean = 7; // shouting: chest and head thrust toward his target
  p.rot = lean ? [rad(lean), 300, hipY] : null;
  const T: Blob = { a: (o.build === "stout" ? 0.36 : 0.31) * W, b: 0.5 * (torsoBot - (chin - 0.25 * HH)), nTop: 2.2, nBot: 2.5, egg: 0.1, asym: 0.06,
    rot: 0, noise: 0.006, seed: seed + 7 };
  const tcx = 300 + 2 * u, tcy = torsoBot - T.b, tp = blobPts(tcx, tcy, T);
  const armCol = mix(o.jacket, INK, 0.5), farArm = mix(o.jacket, INK, 0.68);
  const S: P2 = [tcx + 0.05 * T.a, chin + 0.14 * HH], aLen = 0.95 * HH;
  const swingArm = (ang: number): [P2, P2, P2] => {
    const e: P2 = [S[0] + Math.sin(ang) * aLen * 0.5, S[1] + Math.cos(ang) * aLen * 0.5], a2 = ang + rad(16) * Math.sign(ang || 1);
    return [S, e, [e[0] + Math.sin(a2) * aLen * 0.5, e[1] + Math.cos(a2) * aLen * 0.5]];
  };
  const rifle = !!o.rifle && (mode === "march" || mode === "stand");
  const B0: P2 = [tcx + 0.72 * T.a, chin + 0.58 * HH], B1: P2 = [tcx - 0.95 * T.a - 22 * u, crown - 0.4 * HH];
  let near: [P2, P2, P2], far: [P2, P2, P2] | null;
  if (mode === "swing") { near = [S, [S[0] + 12 * u, S[1] - 0.16 * HH], [300 + 6 * u, chin - 0.3 * HH]]; far = [S, [S[0] + 8 * u, S[1] - 0.18 * HH], [300 + 2 * u, chin - 0.36 * HH]]; }
  else if (mode === "push") {
    // both arms live at real arm length, reaching forward to the swing all the time and extending on the push beat
    // (the old 0.55HH rest reach curled them into stubs at the chest between pushes)
    const SP: P2 = [tcx + 0.62 * T.a, chin + 0.24 * HH], armLen = 0.95 * HH;
    let aim: P2 = [SP[0] + armLen, SP[1] + 0.02 * HH];
    if (opts.hand) {
      // target is in final canvas units; the arm is drawn inside the lean rotation, so undo it
      const th = -rad(lean), dx = opts.hand[0] - 300, dy = opts.hand[1] - hipY;
      aim = [300 + dx * Math.cos(th) - dy * Math.sin(th), hipY + dx * Math.sin(th) + dy * Math.cos(th)];
    }
    const ax = aim[0] - SP[0], ay = aim[1] - SP[1], al = Math.hypot(ax, ay) || 1;
    const reach = armLen * (0.74 + 0.24 * pose);
    const hN: P2 = [SP[0] + (ax / al) * reach, SP[1] + (ay / al) * reach];
    // rubber-hose push: the elbow drops away from the shoulder-hand line, straightening as the arms extend
    const bow = (0.08 - 0.05 * pose) * HH;
    near = [SP, [(SP[0] + hN[0]) / 2 - 4 * u, (SP[1] + hN[1]) / 2 + bow], hN];
    far = [SP, [(SP[0] + hN[0]) / 2 - 10 * u, (SP[1] + hN[1]) / 2 + bow * 1.1], [hN[0] - 5 * u, hN[1] + 5 * u]];
  } else if (rifle) { near = [S, [S[0] - 4 * u, S[1] + 0.42 * HH], B0]; far = mode === "march" ? swingArm(rad(30) * nearFwd) : swingArm(0); }
  else if (opts.prop === "fist") {
    // the fist is up beside the head, outside its silhouette (inside it the head blob covered the whole fist),
    // jittering with the shake beat (pose 0..1)
    const j = 0.5 + 0.5 * clamp(pose, 0, 1);
    near = [S, [S[0] + (0.5 + 0.04 * j) * aLen, S[1] - (0.34 + 0.04 * j) * aLen], [S[0] + (0.72 + 0.05 * j) * aLen, S[1] - (0.56 + 0.08 * j) * aLen]];
    far = swingArm(0);
  }
  else if (opts.prop === "scroll") {
    near = [S, [S[0] + 0.52 * aLen, S[1] + 0.36 * aLen], [S[0] + 0.9 * aLen, S[1] + 0.3 * aLen]];
    far = [S, [S[0] + 0.26 * aLen, S[1] + 0.5 * aLen], [S[0] + 0.52 * aLen, S[1] + 0.44 * aLen]];
  } else if (Array.isArray(opts.prop)) {
    // sword arm thrust forward at chest height, driven further forward on the hit; kept inside the 600-unit card
    // so the fist stays well clear of the sprite edge (the blade itself is a separate world card)
    const k = clamp(opts.prop[1], 0, 1);
    near = [S, [S[0] + (0.38 + 0.1 * k) * aLen, S[1] + (0.14 - 0.03 * k) * aLen], [S[0] + (0.7 + 0.14 * k) * aLen, S[1] + (0.04 - 0.02 * k) * aLen]];
    far = [S, [S[0] + (0.34 + 0.1 * k) * aLen, S[1] + 0.3 * aLen], [S[0] + (0.62 + 0.12 * k) * aLen, S[1] + 0.22 * aLen]];
  }
  else { near = swingArm(rad(-30) * nearFwd); far = mode === "march" ? swingArm(rad(30) * nearFwd) : null; }
  if (far) { p.stroke(curve(far[0], far[1], far[2]), 5.2 * u, farArm); p.dot(far[2][0], far[2][1], 5.5 * u); }
  // full-length robe in profile (the front view already had one; without it the priest walked around in a short coat)
  if (o.dress && mode !== "swing") {
    const D: Blob = { a: 0.48 * W, b: 0.5 * ((sole - 0.35 * HH) - (chin - 0.2 * HH)), nTop: 2.0, nBot: 3.0, egg: 0.32,
      asym: 0.05, rot: 0, noise: 0.006, seed: seed + 9 };
    const dp = blobPts(300 + 6 * u, sole - 0.35 * HH - D.b, D), hem = sole - 0.40 * HH, gold = o.buttons ?? "#e8c45a";
    p.gradFill(dp, o.dress, mul(o.dress, SH_CLOTH), light);
    p.clip(dp, () => {
      p.band([[300 - W, hem], [300 + W, hem]], gold, 0.05 * HH, 1.5 * u);
      p.band([[300 + 52 * u, chin + 0.2 * HH], [300 + 74 * u, hem]], gold, 9 * u, 1.3 * u);
    });
    p.inkRing(dp, ow, thick);
  }
  p.gradFill(tp, o.jacket, mul(o.jacket, SH_CLOTH), light);
  p.clip(tp, () => {
    if (o.belt) p.band([[tcx - 0.65 * T.a, chin - 0.05 * HH], [tcx + 0.75 * T.a, torsoBot - 0.1 * HH]], o.belt!, 5.5 * u, 1.8 * u);
    if (o.sash) p.band([[tcx - 1.3 * T.a, torsoBot - 0.32 * HH], [tcx + 1.3 * T.a, torsoBot - 0.32 * HH]], o.sash, 0.13 * HH, 1.8 * u);
    if (!o.dress) for (let i = 0; i < 3; i++) { const y = chin + 0.16 * HH + i * 0.24 * HH; p.dot(tcx + 0.8 * T.a, y, 3 * u, INK); p.dot(tcx + 0.8 * T.a, y, 2.2 * u, o.buttons ?? shade(o.jacket, 0.7)); }
  });
  chinShadow(p, tp, tcx, chin, HH, W, light);
  p.inkRing(tp, ow, thick);
  if (o.armor) {
    p.clip(tp, () => {
      p.line([[tcx + 0.1 * T.a, chin + 0.2 * HH], [tcx - 0.05 * T.a, torsoBot - 0.14 * HH]], "#7f8897", 1.7 * u);
      p.line([[tcx - 0.6 * T.a, chin + 0.42 * HH], [tcx + 0.5 * T.a, chin + 0.5 * HH]], "#7f8897", 1.6 * u);
    });
    const pp = ellPts(S[0] + 0.1 * u, S[1] + 0.04 * HH, 0.22 * W, 0.12 * HH, 0, 360);
    p.gradFill(pp, "#c9d3df", "#8d98a7", light);
    p.inkRing(pp, ow * 0.8, thick);
  }
  if (rifle) {
    p.band([B0, B1], "#7a4b2a", 5 * u, 1.5 * u, "round");
    p.band([lerp2(B0, B1, 0.6), B1], "#8d949c", 2.4 * u, 1.2 * u, "round");
  }
  p.stroke(curve(near[0], near[1], near[2]), 5.2 * u, armCol); p.dot(near[2][0], near[2][1], 5.5 * u);
  if (opts.prop === "fist") {
    // clenched fist on the raised arm: skin knuckles over the wrist, shake marks in the open air above it
    const fx = near[2][0], fy = near[2][1], fcx = fx + 2 * u, fcy = fy - 3 * u;
    // clenched mitt: three knuckle bumps on the outer edge, a thumb on the near side (a plain ball read as a lollipop)
    const K: [number, number][] = [[-12, 10], [-14, 0], [-10, -9], [-4, -13], [-0.5, -10], [3, -13.5], [3.5, -10],
      [7.5, -12], [8, -8], [13, -6], [14, 1], [9, 7], [10, 11], [0, 13], [-8, 12]];
    const fp = K.map(([x, y]) => [fcx + x * u, fcy + y * u] as P2);
    p.gradFill(fp, skin, mul(skin, SH_SKIN), light, 0.4);
    p.inkRing(fp, 3.2 * u, thick);
    p.line([[fcx + 12.5 * u, fcy - 1 * u], [fcx + 8.5 * u, fcy + 6.5 * u]], shade(skin, 0.58), 1.9 * u, false);
  }
  if (opts.prop === "scroll") drawScroll(p, near[2][0] + 8 * u * (opts.propScale ?? 1), near[2][1] - 3 * u, u, -0.1, opts.propScale ?? 1);
  else if (Array.isArray(opts.prop) && opts.blade !== false) drawSword(p, near[2][0], near[2][1], u, rad(80 + 18 * clamp(opts.prop[1], 0, 1)));
  // ---- head ----
  const hx = 300 + 4 * u;
  hatBehind(p, o, H, hx, hc, light, thick, ow, true);
  const hp = blobPts(hx, hc, H);
  p.gradFill(hp, skin, mul(skin, SH_SKIN), light, 0.4);
  p.inkRing(hp, ow, thick);
  hatOn(p, o, hp, H, hx, hc, light, seed, 1, true);
  const brim = !!o.hat && o.hat !== "hair" && o.hat !== "bonnet" && o.hat !== "cap";
  faceSide(p, hx, hc, W, expr, lid, brim, skin, o.moustache, o.build === "stout");
  p.rot = null;
};

/** rope + seat + seated kid on a 700 x 2300 canvas; the pivot is design (350, 20); kid drawn at 0.92 scale */
export const swingKid = (p: Pen, o: Outfit, kick: number, expr: Expr, light = DEF_LIGHT, blink: number = 0) => {
  const rope = 1830, k = 1.22, HH = 2 * headBlob(5, BUILD[o.build ?? "adult"].a, 1).b;
  // two ropes from the pivot to the ends of a wide plank, the kid framed between them: a single rope behind the kid
  // ended at the cap and read as a hanging. Far rope behind the kid, near rope drawn over (clear of the face).
  const seat = rope + 18, x0 = 150, x1 = 550;
  p.line([[350, 20], [x0 + 16, seat + 4]], "#a07a4c", 10);
  p.poly(rrect(x0, seat, x1, seat + 36, 10), "#b5653f", 9);
  const g = p.g;
  g.save();
  g.translate(350 - 300 * k, rope + 18 - (SWING_HIP + 0.12 * HH) * k);
  g.scale(k, k);
  bodySide(new Pen(g), o, { expr, mode: "swing", pose: kick, light, seed: 5, blink });
  g.restore();
  p.line([[350, 20], [x1 - 16, seat + 4]], "#a07a4c", 10);
};

// ---------------- effects ----------------
export const fxNote = (p: Pen, kind: number, col = "#1f2a44") => {
  // draw the silhouette twice: a crisp cream halo underneath so the navy note separates from the sky, pale stone and
  // the dark coats (the notes are NOINK cards and get no world outline of their own)
  const shapes = (fill: string, pad: number, ink: number) => {
    p.ell(70, 200, 46 + pad, 34 + pad, fill, ink, 0, 360, -20);
    p.stroke([[110, 190], [110, 40]], 14 + 2 * pad, ink ? INK : fill);
    if (kind === 0) p.poly([[110, 40], [170, 70], [170, 110], [110, 82]], fill, ink);
    else {
      p.ell(150, 170, 40 + pad, 30 + pad, fill, ink, 0, 360, -20);
      p.stroke([[186, 160], [186, 20]], 14 + 2 * pad, ink ? INK : fill);
      p.poly([[110, 40], [186, 20], [186, 50], [110, 70]], fill, ink);
    }
  };
  shapes("#fff8e4", 10, 0);
  shapes(col, 0, 8);
};

/** spark / impact star on a 500 x 500 canvas; t in 0..1 */
export const fxBurst = (p: Pen, t: number, col = "#fff3b0", rays = 10, r0 = 40, r1 = 230) => {
  const c = 250, e = 1 - (1 - t) ** 3;
  for (let i = 0; i < rays; i++) {
    const a = rad((i * 360) / rays + 7 * (i % 2)), ra = r0 + (r1 - r0) * e * (0.75 + 0.25 * (i % 2));
    p.poly([[c + r0 * 0.5 * Math.cos(a + 0.18), c + r0 * 0.5 * Math.sin(a + 0.18)], [c + ra * Math.cos(a), c + ra * Math.sin(a)],
      [c + r0 * 0.5 * Math.cos(a - 0.18), c + r0 * 0.5 * Math.sin(a - 0.18)]], col, Math.max(3, 8 * (1 - t)));
  }
  if (t < 0.5) p.ell(c, c, r0 * (1.4 - t), r0 * (1.4 - t), WHITE, 8);
};

/** chunky comic spark on a 500 x 500 canvas: yellow star with a hot cream core; t in 0..1 */
export const fxSpark = (p: Pen, t: number, col = "#ffd93d") => {
  const c = 250, R = 80 + 155 * (1 - (1 - t) ** 2), pts: P2[] = [];
  for (let i = 0; i < 24; i++) {
    const a = rad(i * 15 - 90), r = i % 2 ? R * 0.42 : R;
    pts.push([c + r * Math.cos(a), c + r * Math.sin(a)]);
  }
  p.poly(pts, col, 9);
  p.ell(c, c, R * 0.3, R * 0.3, "#fffbe8", 7);
};

/** water splash crown on an 800 x 800 canvas; t in 0..1 */
export const fxSplash = (p: Pen, t: number) => {
  // the crown comes up fast (a third of a second after the slam) so it stands in front of the last falling soldiers
  const c = 400, size = 800, rise = Math.sin(Math.min(1, t * 2.1) * Math.PI);
  const blue = "#bfe8ff", deep = "#6cc0f0";
  if (rise > 0.02) {
    const pts: P2[] = [];
    for (let i = 0; i < 19; i++) {
      const h = (i % 2 ? 300 : 150) * rise * (0.7 + 0.3 * Math.sin(i * 1.7));
      pts.push([c - 360 + (720 * i) / 18, size - 120 - h]);
    }
    p.poly([...pts, [c + 360, size - 90], [c - 360, size - 90]], blue, 10);
    p.ell(c, size - 100, 392, 50, deep, 10);
  }
  for (let i = 0; i < 8; i++) {
    const a = rad(200 + i * 18), d = 120 + 380 * t, y = size - 160 + d * Math.sin(a) + 520 * t * t, r = 26 * (1 - t) + 6;
    if (t > 0.08 && y < size - 40) p.ell(c + d * Math.cos(a), y, r, r * 1.25, blue, 7);
  }
};

/** dust puff on a 300 x 300 canvas; t in 0..1 */
export const fxPuff = (p: Pen, t: number) => {
  for (let i = 0; i < 5; i++) {
    const a = rad(160 + i * 55), d = 40 + 70 * t, r = (34 + 20 * (i % 2)) * (1 - 0.6 * t);
    p.ell(150 + d * Math.cos(a), 180 + d * 0.45 * Math.sin(a), r, r * 0.8, `rgba(238,225,205,${(1 - t).toFixed(3)})`, 0);
  }
};

/** circling stars on a 420 x 210 canvas */
export const fxStars = (p: Pen, t: number) => {
  for (let i = 0; i < 4; i++) {
    const a = t * Math.PI * 2 + (i * Math.PI) / 2, x = 210 + 150 * Math.cos(a), y = 110 + 40 * Math.sin(a), pts: P2[] = [];
    for (let k = 0; k < 10; k++) { const r = k % 2 ? 14 : 34, b = rad(k * 36 - 90); pts.push([x + r * Math.cos(b), y + r * Math.sin(b)]); }
    p.poly(pts, "#ffd84a", 6);
  }
};

/** three jittering strain ticks on a 300 x 300 canvas */
export const fxCreak = (p: Pen, t: number) => {
  const j = 6 * Math.sin(t * 40);
  for (const a of [-30, 0, 30]) {
    const b = rad(a - 90);
    p.stroke([[150 + 70 * Math.cos(b) + j, 230 + 70 * Math.sin(b)], [150 + 100 * Math.cos(b) + 10 + j, 230 + 100 * Math.sin(b)],
      [150 + 130 * Math.cos(b) + j, 230 + 130 * Math.sin(b)]], 10);
  }
};

/** flat water ring (drawn top-down) on a 600 x 600 canvas; t in 0..1 */
export const fxRing = (p: Pen, t: number) => {
  // dark waterline under each light ripple: the rings are NOINK cards, so this painted line is all the ink the
  // water close-ups get from them (the reading reference has outlined ripples)
  const g = p.g;
  for (let k = 0; k < 3; k++) {
    const u = t - k * 0.22;
    if (u <= 0 || u >= 1) continue;
    const r = 60 + 230 * u, w = 9 * (1 - u) + 3;
    g.beginPath(); g.ellipse(300, 300, r, r, 0, 0, Math.PI * 2);
    g.strokeStyle = "#10304e"; g.lineWidth = w + 6; g.stroke();
    g.beginPath(); g.ellipse(300, 300, r, r, 0, 0, Math.PI * 2);
    g.strokeStyle = k === 0 ? "#f6fcff" : "#cfe8fa"; g.lineWidth = w; g.stroke();
  }
};

/** text-free sign on a 700 x 520 canvas: "no marching in step on the bridge". A bridge (deck + arch + piers), four
 *  identical pairs of marching legs in the same stride (in step), a bold red X over all of it. */
export const fxSign = (p: Pen) => {
  const g = p.g, RED = "#d42f2f";
  p.poly(rrect(14, 14, 686, 506, 40), "#f6ecd2", 0);
  p.poly(rrect(14, 14, 686, 506, 40), null, 14);
  // bridge: deck, stone arch underneath, two piers
  p.poly(rrect(70, 352, 630, 384, 8), "#8a5a3a", 9);
  g.beginPath(); g.moveTo(112, 470); g.quadraticCurveTo(350, 300, 588, 470);
  g.strokeStyle = INK; g.lineWidth = 16; g.lineCap = "round"; g.stroke();
  for (const x of [88, 612]) p.poly(rrect(x - 16, 384, x + 16, 470, 4), "#8a5a3a", 9);
  // four identical soldiers' legs mid-stride: same leg forward on every one = in step
  for (const x of [150, 278, 406, 534]) {
    p.poly(rrect(x - 30, 150, x + 30, 214, 14), "#357650", 9);                  // coat hem
    p.stroke([[x - 8, 210], [x + 34, 262], [x + 46, 338]], 15, INK);           // front leg
    p.stroke([[x + 6, 210], [x - 12, 274], [x - 36, 336]], 15, INK);           // back leg
    p.poly(rrect(x + 30, 330, x + 74, 350, 9), INK, 0);                          // boots point forward
    p.poly(rrect(x - 52, 328, x - 8, 348, 9), INK, 0);
  }
  // big red X
  for (const [a, b] of [[[96, 70], [604, 452]], [[604, 70], [96, 452]]] as [[number, number], [number, number]][]) {
    p.stroke([a, b], 58, "#ffffff");
    p.stroke([a, b], 42, RED);
  }
};

/** soft cartoon cloud on a 600 x 300 canvas */
export const fxCloud = (p: Pen, seed: number) => {
  const blobs: [number, number, number][] = [[150, 190, 80], [250, 150, 105], [360, 160, 95], [450, 195, 70], [300, 210, 90]];
  for (const [x, y, r] of blobs) p.ell(x + ((seed * 37) % 20) - 10, y, r, r * 0.8, "#ffffff", 0);
  p.ell(300, 235, 230, 40, "#ffffff", 0);
};

/** cast shadow on a 128 x 256 canvas: dark soft contact pool at the feet (y 205) and a softer tail that runs up the
 *  canvas = away from the sun, fading with distance; multiply colour (sRGB-encoded linear ratio), white = no change */
export const fxShadow = (p: Pen, col: string) => {
  const g = p.g;
  g.fillStyle = WHITE; g.fillRect(0, 0, 128, 256);
  g.save(); g.filter = "blur(9px)";
  const lg = g.createLinearGradient(0, 205, 0, 22);
  lg.addColorStop(0, mix(col, WHITE, 0.08)); lg.addColorStop(0.55, mix(col, WHITE, 0.3)); lg.addColorStop(1, mix(col, WHITE, 0.85));
  g.fillStyle = lg;
  g.beginPath(); g.moveTo(40, 205); g.bezierCurveTo(36, 120, 46, 50, 64, 30); g.bezierCurveTo(82, 50, 92, 120, 88, 205); g.closePath(); g.fill();
  g.fillStyle = col; g.beginPath(); g.ellipse(64, 205, 30, 17, 0, 0, Math.PI * 2); g.fill();
  g.restore();
};

/** tight contact shadow right under the feet on a 128 x 128 canvas: dark core, short fall-off (multiply colour) */
export const fxContact = (p: Pen, col: string) => {
  const g = p.g;
  g.fillStyle = WHITE; g.fillRect(0, 0, 128, 128);
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  for (const [r, k] of [[0, 0], [0.32, 0.02], [0.5, 0.22], [0.66, 0.58], [0.82, 0.88], [1, 1]] as const) gr.addColorStop(r, mix(col, WHITE, k));
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
};

/** floating wooden plank, side-on, on a 320 x 110 canvas */
export const fxPlank = (p: Pen) => {
  p.poly(rrect(14, 30, 306, 78, 10), "#a8744a", 9);
  p.line([[40, 46], [150, 44], [270, 50]], "#7d5234", 4);
  p.line([[60, 62], [200, 64], [284, 60]], "#7d5234", 4);
  p.dot(36, 54, 5, INK); p.dot(284, 54, 5, INK);
};

/** floating marching drum (no text) on a 260 x 240 canvas: white shell, red hoops, ink zig-zag cord */
export const fxDrum = (p: Pen) => {
  p.poly(rrect(40, 70, 220, 190, 16), "#f1ece0", 9);
  p.poly(rrect(32, 58, 228, 86, 12), "#c9373a", 8);
  p.poly(rrect(32, 176, 228, 204, 12), "#c9373a", 8);
  p.line([[52, 88], [82, 172], [112, 88], [142, 172], [172, 88], [202, 172]], INK, 6);
  p.ell(130, 58, 98, 18, "#f7f3ea", 8);
};

/** soft ground contact blob on a 128 x 128 canvas, multiply colour (sRGB-encoded linear ratio) in the centre */
export const fxBlob = (p: Pen, col: string) => {
  const g = p.g;
  g.fillStyle = WHITE; g.fillRect(0, 0, 128, 128);
  // soft contact shadow: flat core, then a long smooth (roughly gaussian) fall-off to white = no change
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  for (const [r, k] of [[0, 0], [0.5, 0.04], [0.64, 0.18], [0.76, 0.42], [0.87, 0.72], [0.95, 0.92], [1, 1]] as const) gr.addColorStop(r, mix(col, WHITE, k));
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
};

/** heavy leather coin sack on a 260 x 240 canvas: plump body, tied neck, two gold coins spilling at the base */
export const fxSack = (p: Pen) => {
  const body: P2[] = [];
  for (let i = 0; i <= 18; i++) {
    const a = Math.PI * (i / 18), r = 92 + 10 * Math.sin(i * 1.9);
    body.push([130 + r * Math.cos(a), 150 + r * 0.78 * Math.sin(a)]);
  }
  for (let i = 0; i <= 8; i++) { const t = i / 8; body.push([130 + 30 - 60 * t, 150 - 48 - 16 * Math.sin(t * Math.PI)]); }
  p.poly(body, "#c79a5c", 8);
  p.line([[104, 132], [96, 154], [108, 168]], "#8d6738", 4);
  p.line([[156, 132], [166, 152], [156, 168]], "#8d6738", 4);
  // tied neck
  p.poly([[100, 96], [160, 96], [150, 118], [110, 118]], "#a87c44", 7);
  p.line([[98, 100], [162, 100]], "#6f4d2a", 6);
  for (const [x, y, r] of [[66, 214, 16], [206, 216, 15]] as const) {
    p.ell(x, y, r, r * 0.55, "#f2c94c", 6);
    p.ell(x - 3, y - 2, r * 0.45, r * 0.24, "#fff0b0", 0);
  }
  p.ell(130, 216, 16, 10, "#f2c94c", 6);
  p.stroke([[92, 196], [168, 196]], 3.4, "#8d6738");
};

/** one gold coin on a 128 x 128 canvas, stamped "P" for pardon; the card's rot spins it */
export const fxCoin = (p: Pen) => {
  p.ell(64, 64, 44, 44, "#f2c94c", 6);
  p.ell(64, 64, 32, 32, null, 3);
  p.line([[52, 48], [52, 80]], "#a9822a", 4, false);
  p.line([[52, 48], [76, 48]], "#a9822a", 4, false);
  p.line([[52, 63], [71, 63]], "#a9822a", 4, false);
  p.dot(64, 64, 5, "#a9822a");
};

/** brass hand stamp on a 260 x 360 canvas, base plate flush with the bottom edge: the seal press for the pardon */
export const fxStamp = (p: Pen) => {
  p.band([[130, 56], [130, 140]], "#8a5a34", 46, 7, "round");
  p.band([[130, 92], [130, 128]], "#6f4526", 22, 4, "round");
  p.poly([[66, 140], [194, 140], [204, 292], [56, 292]], "#c9a14c", 7);
  p.line([[76, 184], [184, 184]], "#a5823a", 5, false);
  p.poly([[56, 292], [204, 292], [204, 356], [56, 356]], "#8c6a2e", 7);
  p.poly([[62, 346], [198, 346], [198, 356], [62, 356]], "#b3312f", 4);
};

/** arming sword on a 640 x 240 canvas, pivoted at the grip (canvas centre): the blade runs toward the left edge,
 *  so a card can point it forward past the 600-unit sprite card that would otherwise clip it */
export const fxSword = (p: Pen) => {
  const y = 120;
  p.band([[320, y], [386, y]], "#6a4526", 11, 3.5, "round");
  p.dot(390, y, 10, "#d7b25a");
  p.poly([[296, y - 40], [324, y - 40], [326, y + 40], [298, y + 40]], "#d7b25a", 4.5);
  p.poly([[300, y - 17], [300, y + 17], [64, y + 11], [22, y], [64, y - 11]], "#e3e9f0", 5);
  p.line([[292, y - 3], [58, y - 2]], "#a9b3c0", 3.5, false);
  p.line([[300, y - 12], [70, y - 8]], "#ffffff", 2.5, false);
};

/** one sweat drop (side / head) on an 80 x 120 canvas */
export const fxSweat = (p: Pen) => {
  const pts: P2[] = [];
  for (let i = 0; i <= 14; i++) {
    const a = Math.PI * (i / 14);
    pts.push([40 + 26 * Math.cos(a), 76 + 24 * Math.sin(a)]);
  }
  pts.push([52, 14], [40, 4], [28, 14]);
  p.poly(pts, "#a9d8ff", 5);
  p.ell(30, 74, 7, 10, "#eaf7ff", 0);
};

/** manga shock lines round a 300 x 300 canvas (no fill: the character's head shows through the middle) */
export const fxShock = (p: Pen) => {
  for (let i = 0; i < 9; i++) {
    const a = rad(-90 + i * 40 + 8), r0 = 92, r1 = 138;
    p.stroke([[150 + r0 * Math.cos(a), 150 + r0 * Math.sin(a)], [150 + r1 * Math.cos(a), 150 + r1 * Math.sin(a)]], 9);
  }
};
