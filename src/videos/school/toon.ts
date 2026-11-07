// School Hero cast: flat cards built from the model sheet. Glossy black sphere head with one soft specular
// highlight, cream vertical-pill eyes and NO mouth except surprised / scared / shout; 3.5 heads tall. Hero wears a
// red ribbed beanie, an oversized yellow hoodie with white drawstrings and a kangaroo pocket, gray shorts with two
// white side stripes, black stick limbs with ball mitts and rounded shoes. Friends differ only by hoodie colour and
// headgear; terrorists wear balaclavas and tactical vests. Held props are drawn attached to the 2D hands, never as
// separate 3D meshes. Design space 600 x 1000 (soles ~952).
import type { Pen } from "./pen";
import { Pen as PenClass } from "./pen";

export { Pen } from "./pen";
export const INK = "#1a1320";
const WHITE = "#ffffff";
const HEAD_INK = "#111111";
const EYE = "#FFFDF2";
const LIMB = "#111111";
const HEAD_R = 125;

type P2 = [number, number];
const rad = (d: number) => (d * Math.PI) / 180;
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const mixPt = (a: P2, b: P2, t: number): P2 => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
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
const star = (cx: number, cy: number, r0: number, r1: number, n = 5, rot = -Math.PI / 2): P2[] => {
  const pts: P2[] = [];
  for (let i = 0; i < n * 2; i++) {
    const a = rot + (i * Math.PI) / n, r = i % 2 ? r1 : r0;
    pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
  }
  return pts;
};
const rrect = (x0: number, y0: number, x1: number, y1: number, r: number, n = 6): P2[] => {
  const pts: P2[] = [];
  for (const [cx, cy, a] of [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]])
    for (let i = 0; i <= n; i++) pts.push([cx + r * Math.cos(rad(a + (90 * i) / n)), cy + r * Math.sin(rad(a + (90 * i) / n))]);
  return pts;
};
// eye with a flat top and rounded bottom: the heavy lid that closes over the upper half
const halfPill = (cx: number, cy: number, rx: number, ry: number): P2[] => {
  const pts = ellPts(cx, cy, rx, ry, 0, 180);
  pts.unshift([cx + rx, cy - ry * 0.28]);
  return pts;
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
// hollow rim light: transparent core, coloured band, transparent falloff
const rimGlow = (p: Pen, cx: number, cy: number, rx: number, ry: number, col: string, a = 1) => {
  const g = p.g;
  const gr = g.createRadialGradient(cx, cy, 0, cx, cy, Math.max(rx, ry));
  gr.addColorStop(0, "rgba(0,0,0,0)");
  gr.addColorStop(0.72, "rgba(0,0,0,0)");
  gr.addColorStop(0.88, col);
  gr.addColorStop(1, "rgba(0,0,0,0)");
  g.save(); g.globalAlpha = a; g.fillStyle = gr;
  g.beginPath(); g.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2); g.fill(); g.restore();
};

// ---------------- types ----------------
export type Expr = "neutral" | "smile" | "grin" | "laugh" | "wink" | "shock" | "nervous" | "stern" | "sad" | "pained"
  | "amazed" | "suspicious" | "relief" | "smug" | "whistle" | "shout" | "question" | "chew" | "solemn" | "angry" | "cry"
  | "scared" | "sleepy";
export type Mode = "stand" | "walk" | "run" | "sit" | "point" | "pointSelf" | "hold" | "aim" | "kick" | "slide"
  | "punch" | "hug" | "salute" | "throw" | "slump" | "crouch" | "kneel" | "cheer" | "clap" | "bend"
  | "sitChin" | "lift" | "smash" | "vsign" | "highfive";
export type Kind = "hero" | "muscle" | "hoodie" | "crush" | "nerd" | "terror" | "teacher" | "principal" | "cop" | "swat" | "reporter" | "student";
export type PropKind = "none" | "rifle" | "pistol" | "walkie" | "vest" | "extinguisher" | "chalk" | "mic" | "rope"
  | "baton" | "book" | "phone" | "thumbs" | "chair";

export type KidOpts = {
  kind: Kind; expr: Expr; mode: Mode; blink?: number; talk?: number; light?: number; tilt?: number;
  gaze?: number; gazeY?: number; phase?: number;
  aura?: boolean; eyeFire?: boolean; starEyes?: boolean; blush?: boolean; tears?: number; sweat?: number;
  shades?: boolean; prop?: PropKind; hair?: string; top?: string; bottom?: string; accent?: string;
  hurt?: boolean; frost?: number; tied?: boolean; hat?: boolean; scale?: number;
};

// head gear plus hoodie colour are the only things that differentiate the cast — same species, same proportions
export type Gear = "beanie" | "band" | "curls" | "pony" | "bala" | "cap" | "helmet" | "short" | "gray" | "bun";

type Kit = {
  gear: Gear; gearCol: string; top: string; stripe: string; bottom: string; shoes: string;
  vest?: string; tie?: string; badge?: boolean; glasses?: boolean; skirt?: boolean;
};

const KIT: Record<Kind, Kit> = {
  hero: { gear: "beanie", gearCol: "#D93829", top: "#F5B82E", stripe: "#FFFDF2", bottom: "#3A3A3C", shoes: "#111111" },
  muscle: { gear: "band", gearCol: "#F2EAD8", top: "#46A45C", stripe: "#EEF5E6", bottom: "#34455C", shoes: "#111111" },
  hoodie: { gear: "curls", gearCol: "#111114", top: "#F08A2C", stripe: "#FFF3DC", bottom: "#3A3A3C", shoes: "#111111" },
  crush: { gear: "pony", gearCol: "#17171C", top: "#F7C6D8", stripe: "#E8557B", bottom: "#2E2E3A", shoes: "#111111", skirt: true },
  nerd: { gear: "short", gearCol: "#14141A", top: "#4E86C8", stripe: "#EAF2FA", bottom: "#3A3A44", shoes: "#111111", glasses: true },
  terror: { gear: "bala", gearCol: "#1B1E24", top: "#2B3138", stripe: "#9AA6B4", bottom: "#22262C", shoes: "#0C0C10", vest: "#4A5B45" },
  teacher: { gear: "bun", gearCol: "#2A2020", top: "#6A8AB0", stripe: "#EAF0F6", bottom: "#4A4A5A", shoes: "#2A2A30", glasses: true },
  principal: { gear: "gray", gearCol: "#C8C8CC", top: "#4A4A52", stripe: "#E8E8EC", bottom: "#3A3A44", shoes: "#22222A", tie: "#8A2A2A", glasses: true },
  cop: { gear: "cap", gearCol: "#2A3A5A", top: "#2A3A5A", stripe: "#D8B45A", bottom: "#26324C", shoes: "#14141A", badge: true },
  swat: { gear: "helmet", gearCol: "#20242A", top: "#1C2024", stripe: "#5A626C", bottom: "#1C2024", shoes: "#0C0C10", vest: "#2A3034" },
  reporter: { gear: "short", gearCol: "#2A2220", top: "#3A5A7A", stripe: "#D8B45A", bottom: "#3A3A44", shoes: "#22222A", tie: "#D8B45A" },
  student: { gear: "short", gearCol: "#2A221C", top: "#7C93AE", stripe: "#EAF0F6", bottom: "#3E4A5A", shoes: "#2A2A30" },
};

const kitOf = (o: KidOpts): Kit => {
  const k = { ...KIT[o.kind] };
  if (o.hair) k.gearCol = o.hair;
  if (o.top) k.top = o.top;
  if (o.bottom) k.bottom = o.bottom;
  if (o.accent) k.stripe = o.accent;
  return k;
};

// ---------------- head ----------------
// glossy minimalist sphere: flat black disc, one soft specular on the lit curve, cool bounce on the far side
const drawHeadBase = (p: Pen, hx: number, hy: number, k: Kit, light: number) => {
  p.ell(hx, hy, HEAD_R, HEAD_R * 0.98, k.gear === "bala" ? "#16181C" : HEAD_INK, 6);
  const g = p.g;
  const lx = hx + Math.cos(light) * HEAD_R * 0.42, ly = hy + Math.sin(light) * HEAD_R * 0.42;
  g.save(); g.globalAlpha = 0.16;
  p.ell(lx, ly, HEAD_R * 0.6, HEAD_R * 0.56, "#4A5568", 0);
  g.restore();
  g.save(); g.globalAlpha = 0.28;
  p.ell(lx - 8, ly - 8, HEAD_R * 0.28, HEAD_R * 0.22, "#8D99AB", 0);
  g.restore();
  // rim bounce on the shaded side keeps the silhouette reading as a sphere, not a sticker
  g.save(); g.globalAlpha = 0.2;
  p.arc(hx, hy, HEAD_R * 0.88, HEAD_R * 0.86, light + 60, light + 130, 9, "#5A7086");
  g.restore();
};

const drawGear = (p: Pen, hx: number, hy: number, k: Kit) => {
  switch (k.gear) {
    case "beanie": {
      // a slouchy ribbed dome, not a plate: the cuff follows the sphere's taper and the crown rounds off above it
      const brimBot = hy - 56, brimTop = hy - 96, wBot = 118, wTop = 104, domeH = 74;
      p.poly(ellPts(hx, brimTop, wTop, domeH, 180, 360), k.gearCol, 7);
      for (let i = 0; i < 7; i++) {
        const a = rad(192 + i * 16);
        const s0 = 0.96, s1 = 0.22;
        p.stroke([[hx + Math.cos(a) * wTop * s0, brimTop + Math.sin(a) * domeH * s0],
          [hx + Math.cos(a) * wTop * s1, brimTop + Math.sin(a) * domeH * s1]], 5, mul(k.gearCol, 0.74));
      }
      p.poly([[hx - wBot, brimBot], [hx + wBot, brimBot], [hx + wTop, brimTop - 2], [hx - wTop, brimTop - 2]],
        mul(k.gearCol, 1.14), 6);
      for (let i = 0; i < 9; i++) {
        const kx = -1 + i / 4;
        p.stroke([[hx + kx * wBot * 0.9, brimBot - 4], [hx + kx * wTop * 0.9, brimTop + 5]], 3, mul(k.gearCol, 0.78));
      }
      break;
    }
    case "band":
      p.poly(ellPts(hx, hy - 12, HEAD_R * 0.9, HEAD_R * 0.84, 180, 360), "#131318", 6);
      p.poly([[hx - HEAD_R * 0.92, hy - 34], [hx + HEAD_R * 0.92, hy - 34],
        [hx + HEAD_R * 0.92, hy - 68], [hx - HEAD_R * 0.92, hy - 68]], k.gearCol, 5);
      p.stroke([[hx - HEAD_R * 0.92, hy - 52], [hx + HEAD_R * 0.92, hy - 52]], 4, mul(k.gearCol, 0.74));
      break;
    case "curls":
      for (let i = 0; i < 9; i++) {
        const a = rad(176 + i * 20.5);
        p.ell(hx + HEAD_R * 0.8 * Math.cos(a), hy - 30 + HEAD_R * 0.68 * Math.sin(a), 30, 30, k.gearCol, 5);
      }
      break;
    case "pony":
      p.poly(ellPts(hx, hy - 20, HEAD_R * 0.92, HEAD_R * 0.88, 180, 360), k.gearCol, 6);
      p.ell(hx + HEAD_R * 0.72, hy + 48, 30, 64, k.gearCol, 7);
      p.ell(hx + HEAD_R * 0.9, hy + 140, 22, 54, k.gearCol, 7);
      p.ell(hx + HEAD_R * 0.44, hy - 78, 15, 12, k.stripe, 5);
      p.ell(hx + HEAD_R * 0.44 - 24, hy - 84, 15, 11, k.stripe, 4);
      p.ell(hx + HEAD_R * 0.44 + 24, hy - 84, 15, 11, k.stripe, 4);
      break;
    case "bala":
      // shell over the crown plus an eye slit and chin seam so the silhouette reads as a balaclava band
      p.poly(ellPts(hx, hy - 12, HEAD_R + 2, HEAD_R + 2, 180, 360), k.gearCol, 6);
      p.stroke([[hx - HEAD_R * 0.56, hy - 12], [hx + HEAD_R * 0.56, hy - 12]], 30, "#0E1013");
      p.stroke([[hx, hy + 34], [hx, hy + 86]], 6, "#0E1013");
      break;
    case "cap":
      p.poly(ellPts(hx, hy - 34, HEAD_R * 0.94, HEAD_R * 0.7, 180, 360), k.gearCol, 7);
      p.poly([[hx - HEAD_R - 8, hy - 44], [hx + HEAD_R + 8, hy - 44],
        [hx + HEAD_R + 8, hy - 20], [hx - HEAD_R - 8, hy - 20]], "#14161C", 6);
      p.dot(hx, hy - 4, 10, "#D8B45A");
      break;
    case "helmet":
      p.poly(ellPts(hx, hy - 16, HEAD_R + 6, HEAD_R + 4, 180, 360), k.gearCol, 8);
      p.poly([[hx - HEAD_R - 12, hy], [hx + HEAD_R + 12, hy],
        [hx + HEAD_R, hy + 26], [hx - HEAD_R, hy + 26]], "#161A20", 7);
      break;
    case "gray":
      p.ell(hx - HEAD_R * 0.74, hy - 8, 28, 46, k.gearCol, 6);
      p.ell(hx + HEAD_R * 0.74, hy - 8, 28, 46, k.gearCol, 6);
      p.poly(ellPts(hx, hy - 44, HEAD_R * 0.78, HEAD_R * 0.42, 180, 360), k.gearCol, 5);
      break;
    case "bun":
      p.poly(ellPts(hx, hy - 18, HEAD_R * 0.9, HEAD_R * 0.86, 180, 360), k.gearCol, 6);
      p.ell(hx - 58, hy - 116, 38, 38, k.gearCol, 6);
      break;
    case "short":
      p.poly(ellPts(hx, hy - 14, HEAD_R * 0.9, HEAD_R * 0.88, 180, 360), k.gearCol, 6);
      p.poly(ellPts(hx, hy - 48, HEAD_R * 0.68, HEAD_R * 0.34, 180, 360), k.gearCol, 5);
      break;
  }
};

// ---------------- face ----------------
type Face = {
  rx: number; ry: number; lid: number; arc: boolean; drop: boolean;
  brow: "none" | "flat" | "v" | "sad" | "high" | "wavy"; mouth: "none" | "o" | "dip";
};

// the model sheet's 8 expressions; the legacy aliases collapse onto them
const faceOf = (e: Expr): Face => {
  switch (e) {
    case "smile": case "grin": case "laugh": case "wink": case "whistle": case "chew": case "relief":
      return { rx: 26, ry: 40, lid: 0, arc: true, drop: false, brow: "none", mouth: "none" };
    case "sad": case "cry": case "pained":
      return { rx: 23, ry: 42, lid: 0, arc: false, drop: true, brow: "sad", mouth: "none" };
    case "stern": case "angry":
      return { rx: 27, ry: 27, lid: 0, arc: false, drop: false, brow: "v", mouth: "none" };
    case "shout":
      return { rx: 26, ry: 26, lid: 0.28, arc: false, drop: false, brow: "v", mouth: "o" };
    case "shock": case "amazed": case "question":
      return { rx: 24, ry: 52, lid: 0, arc: false, drop: false, brow: "high", mouth: "o" };
    case "nervous": case "scared":
      return { rx: 25, ry: 42, lid: 0, arc: false, drop: false, brow: "wavy", mouth: "dip" };
    case "sleepy":
      return { rx: 27, ry: 46, lid: 0.74, arc: false, drop: false, brow: "flat", mouth: "none" };
    case "smug": case "suspicious":
      return { rx: 27, ry: 44, lid: 0.5, arc: false, drop: false, brow: "flat", mouth: "none" };
    default:
      return { rx: 26, ry: 44, lid: 0, arc: false, drop: false, brow: "none", mouth: "none" };
  }
};

const drawFace = (p: Pen, hx: number, hy: number, o: KidOpts, k: Kit) => {
  const g = p.g;
  const e = o.expr;
  const f = faceOf(e);
  const blink = clamp(o.blink ?? 0, 0, 1);
  const slit = k.gear === "bala";
  const dx = slit ? 48 : 54;
  const ey = hy + (slit ? 2 : 6);
  const my = hy + 92;

  if (o.shades) {
    p.poly(rrect(hx - 106, ey - 32, hx - 8, ey + 26, 12), "#0C0E12", 6);
    p.poly(rrect(hx + 8, ey - 32, hx + 106, ey + 26, 12), "#0C0E12", 6);
    p.stroke([[hx - 10, ey - 14], [hx + 10, ey - 14]], 9, "#0C0E12");
    for (const [x0, x1] of [[hx - 106, hx - 8], [hx + 8, hx + 106]] as const)
      p.stroke([[x0, ey - 32], [x1, ey - 32], [x1, ey + 26], [x0, ey + 26], [x0, ey - 32]], 3, "rgba(150,200,225,0.7)");
    p.stroke([[hx - 92, ey - 16], [hx - 44, ey - 22]], 6, "rgba(140,210,240,0.75)");
    p.stroke([[hx + 22, ey - 22], [hx + 70, ey - 16]], 6, "rgba(140,210,240,0.75)");
    return;
  }

  // brows: only the sheet's expressions that have them
  const by = ey - f.ry - 14;
  const brow = (s: number) => {
    if (f.brow === "none") return;
    const cx = hx + s * dx, half = 44;
    if (f.brow === "flat") p.stroke([[cx - half, by], [cx + half, by - 3]], 11, EYE);
    else if (f.brow === "v") p.stroke([[cx + s * half, by - 14], [cx, by + 16], [cx - s * half, by + 24]], 11, EYE);
    else if (f.brow === "sad") p.stroke([[cx - half, by + 14], [cx + half, by - 12]], 10, EYE);
    else if (f.brow === "high") p.arc(cx, by + 26, half, 26, 190, 350, 10, EYE);
    else p.stroke([[cx - half, by + 8], [cx - half * 0.4, by - 12], [cx + half * 0.1, by + 10], [cx + half, by - 10]], 9, EYE);
  };
  for (const s of [-1, 1]) brow(s);

  const eye = (s: number) => {
    const ex = hx + s * dx;
    if (o.starEyes) {
      g.save(); g.shadowColor = "#ffe066"; g.shadowBlur = 20;
      p.poly(star(ex, ey, 34, 15, 5), "#fff0a8", 0);
      p.dot(ex, ey, 9, WHITE);
      g.restore();
      return;
    }
    if (f.arc || blink > 0.68) {
      // HAPPY: ^ ^ upward arcs
      g.save(); g.shadowColor = EYE; g.shadowBlur = 14;
      p.arc(ex, ey + 12, 32, 28, 180, 360, 13, EYE);
      g.restore();
      return;
    }
    const ry = f.ry * (1 - blink * 0.86);
    if (slit) {
      p.poly(s < 0
        ? [[ex - 32, ey - 15], [ex + 26, ey], [ex - 32, ey + 15]]
        : [[ex + 32, ey - 15], [ex - 26, ey], [ex + 32, ey + 15]], EYE, 0);
      return;
    }
    if (f.drop) {
      // SAD: droopy tear-drop eyes
      p.poly([[ex, ey - ry], [ex + f.rx * 0.72, ey + ry * 0.24], [ex + f.rx * 0.42, ey + ry],
        [ex - f.rx * 0.42, ey + ry], [ex - f.rx * 0.72, ey + ry * 0.24]], EYE, 0);
      p.stroke([[ex - f.rx * 0.62, ey + ry + 10], [ex + f.rx * 0.62, ey + ry + 3]], 6, EYE);
      return;
    }
    if (f.lid > 0) {
      // half-closed: flat heavy lid across the top, rounded bottom
      p.poly(halfPill(ex, ey + ry * (0.32 * f.lid), f.rx, ry * (1 - 0.46 * f.lid)), EYE, 0);
      return;
    }
    // the model sheet's eye is a cream pill, so the angry power-up is a cyan halo BEHIND it, not a white-hot core
    // that replaced the eye shape and turned the hero into a pair of goggles
    if (o.eyeFire) {
      g.save(); g.shadowColor = "#5FDCFF"; g.shadowBlur = 26;
      p.ell(ex, ey, f.rx * 1.34, ry * 1.24, "#79E0FF", 0);
      g.restore();
    }
    glowEll(p, ex, ey, f.rx, ry, EYE, 14);
  };
  for (const s of [-1, 1]) eye(s);

  // tears
  if ((o.tears ?? 0) > 0 && e !== "neutral") {
    const t = o.tears ?? 0;
    g.save(); g.globalAlpha = 0.9;
    for (const s of [-1, 1]) {
      const x = hx + s * dx;
      p.poly([[x - 11, ey + 44], [x + 11, ey + 44], [x + 17, ey + 214 + 40 * t], [x - 5, ey + 234 + 40 * t]], "#8fdcff", 4);
      for (let i = 0; i < 3; i++) p.ell(x + (i - 1) * 15, ey + 254 + 60 * t + i * 16, 9, 13, "#bfeaff", 3);
    }
    g.restore();
  }
  // blush
  if (o.blush) {
    for (const s of [-1, 1]) {
      g.save(); g.globalAlpha = 0.65;
      p.ell(hx + s * 84, hy + 66, 30, 16, "#f07a8a", 0);
      g.strokeStyle = "#c85a6a"; g.lineWidth = 3;
      for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(hx + s * 84 - 21 + i * 15, hy + 77); g.lineTo(hx + s * 84 - 14 + i * 15, hy + 55); g.stroke(); }
      g.restore();
    }
  }

  // mouth: the sheet has NO mouth on normal expressions
  const talk = clamp(o.talk ?? 0, 0, 1);
  if (talk > 0.32 || f.mouth !== "none") {
    g.save(); g.lineCap = "round"; g.lineJoin = "round";
    if (f.mouth === "o" || (f.mouth === "none" && talk > 0.32)) {
      const w = f.mouth === "o" ? 21 : 14 + 12 * talk;
      const h = f.mouth === "o" ? 27 : 10 + 16 * talk;
      p.ell(hx, my, w, h, WHITE, 0);
      p.ell(hx, my, w * 0.6, h * 0.64, "#2A1018", 0);
    } else if (f.mouth === "dip") {
      g.strokeStyle = WHITE; g.lineWidth = 9;
      g.beginPath(); g.arc(hx, my + 24, 26, 1.16 * Math.PI, 1.84 * Math.PI); g.stroke();
    }
    g.restore();
  }

  if (o.hurt) {
    g.save(); g.shadowColor = "#ff4a4a"; g.shadowBlur = 14;
    p.poly(star(hx + 70, hy - 92, 24, 10, 5), "#ff5040", 3);
    p.stroke([[hx + 46, hy - 116], [hx + 38, hy - 140]], 5, "#ff7a6a");
    p.stroke([[hx + 98, hy - 112], [hx + 110, hy - 134]], 5, "#ff7a6a");
    g.restore();
  }
  if ((o.sweat ?? 0) > 0) {
    g.save(); g.globalAlpha = 0.9;
    p.poly([[hx + 112, hy - 4], [hx + 128, hy + 34], [hx + 112, hy + 48], [hx + 96, hy + 34]], "#a8e4ff", 4);
    g.restore();
  }
};

// ---------------- props: always drawn on the 2D hands ----------------
// a wooden classroom chair in the same colours as the 3D desks, so lifting it reads as lifting that chair
const drawChair = (p: Pen, cx: number, cy: number, rot: number, s = 1) => {
  p.rot = [rot, 0, 0, cx, cy];
  const seat = -10 * s, back = -152 * s;
  p.poly([[-96 * s, seat - 13 * s], [96 * s, seat - 13 * s], [96 * s, seat + 15 * s], [-96 * s, seat + 15 * s]], "#B06A32", 6);
  for (const sgn of [-1, 1])
    p.poly([[sgn * 70 * s, back], [sgn * 84 * s, back], [sgn * 84 * s, seat - 10 * s], [sgn * 70 * s, seat - 10 * s]], "#8A4E26", 5);
  for (let i = 0; i < 2; i++) {
    const y = back + (16 + i * 54) * s;
    p.poly([[-84 * s, y], [84 * s, y], [84 * s, y + 26 * s], [-84 * s, y + 26 * s]], "#B06A32", 5);
  }
  for (const sgn of [-1, 1]) {
    p.poly([[sgn * 76 * s, seat + 13 * s], [sgn * 92 * s, seat + 13 * s], [sgn * 100 * s, 134 * s], [sgn * 84 * s, 134 * s]], "#8A4E26", 5);
    p.poly([[sgn * 44 * s, seat + 13 * s], [sgn * 56 * s, seat + 13 * s], [sgn * 52 * s, 128 * s], [sgn * 40 * s, 128 * s]], "#8A4E26", 4);
  }
  p.stroke([[-96 * s, seat + 5 * s], [96 * s, seat + 5 * s]], 3, mul("#B06A32", 0.7));
  p.rot = null;
};

const drawProp = (p: Pen, kind: PropKind, hx: number, hy: number, handL: P2, handR: P2, scale = 1, rot = 0) => {
  if (kind === "none") return;
  const mid: P2 = [(handL[0] + handR[0]) / 2, (handL[1] + handR[1]) / 2];
  switch (kind) {
    case "chair":
      drawChair(p, mid[0], mid[1], rot, scale);
      break;
    case "rifle": {
      const g = p.g;
      g.save();
      p.poly(rrect(mid[0] - 150 * scale, mid[1] - 16 * scale, mid[0] + 120 * scale, mid[1] + 8 * scale, 5), "#2a2e34", 6);
      p.poly([[mid[0] + 100 * scale, mid[1] - 12 * scale], [mid[0] + 190 * scale, mid[1] - 8 * scale], [mid[0] + 190 * scale, mid[1] + 2 * scale], [mid[0] + 100 * scale, mid[1] + 6 * scale]], "#3a4048", 4);
      p.poly(rrect(mid[0] - 60 * scale, mid[1] + 6 * scale, mid[0] - 20 * scale, mid[1] + 54 * scale, 4), "#20242a", 4);
      p.poly(rrect(mid[0] - 150 * scale, mid[1] + 2 * scale, mid[0] - 96 * scale, mid[1] + 34 * scale, 4), "#4a3a28", 4);
      p.stroke([[mid[0] + 60 * scale, mid[1] - 16 * scale], [mid[0] + 82 * scale, mid[1] - 44 * scale]], 6, "#2a2e34");
      g.restore();
      break;
    }
    case "pistol":
      p.poly(rrect(handR[0] - 10, handR[1] - 30, handR[0] + 60, handR[1] - 6, 4), "#2a2e34", 5);
      p.poly(rrect(handR[0] + 4, handR[1] - 8, handR[0] + 34, handR[1] + 34, 4), "#20242a", 4);
      break;
    case "walkie":
      p.poly(rrect(handR[0] - 26, handR[1] - 34, handR[0] + 26, handR[1] + 46, 8), "#22262c", 6);
      p.poly(rrect(handR[0] - 16, handR[1] - 22, handR[0] + 16, handR[1] - 2, 3), "#6fe8d0", 0);
      p.stroke([[handR[0] + 22, handR[1] - 34], [handR[0] + 30, handR[1] - 86]], 5, "#22262c");
      p.dot(handR[0] - 12, handR[1] + 20, 4, "#c84a4a");
      break;
    case "vest":
      p.poly(rrect(hx - 106, hy + 190, hx + 106, hy + 404, 16), "#2E3A2C", 7);
      for (let i = 0; i < 3; i++) p.poly(rrect(hx - 92, hy + 220 + i * 60, hx - 12, hy + 262 + i * 60, 6), "#3E4A3A", 4);
      p.poly([[hx + 12, hy + 220], [hx + 96, hy + 220], [hx + 96, hy + 330], [hx + 12, hy + 330]], "#2A3026", 4);
      break;
    case "extinguisher": {
      const x = handL[0] - 26, y = handL[1] - 20;
      p.poly(rrect(x - 30, y - 10, x + 30, y + 140, 14), "#c02a2a", 7);
      p.poly(rrect(x - 12, y - 34, x + 12, y - 6, 5), "#2a2a30", 5);
      p.stroke([[x + 24, y - 20], [x + 68, y + 10], [x + 64, y + 70]], 9, "#20242a");
      p.poly([[x - 44, y - 14], [x - 76, y - 34], [x - 50, y + 6]], "#2a2a30", 4);
      break;
    }
    case "chalk":
      p.poly(rrect(handR[0] - 10, handR[1] - 24, handR[0] + 10, handR[1] + 16, 4), "#f2f0e8", 4);
      break;
    case "mic":
      p.stroke([[handR[0], handR[1] + 20], [handR[0] + 16, handR[1] - 52]], 7, "#20242a");
      p.ell(handR[0] + 20, handR[1] - 62, 18, 22, "#3a4048", 5);
      p.ell(handR[0] + 20, handR[1] - 62, 12, 16, "#8a949c", 0);
      break;
    case "rope":
      p.stroke([[hx - 66, hy + 402], [hx - 24, hy + 436], [hx + 24, hy + 436], [hx + 66, hy + 402]], 8, "#c8b48a");
      break;
    case "baton":
      p.stroke([[handR[0], handR[1]], [handR[0] + 8, handR[1] - 150]], 12, "#20242a");
      break;
    case "book":
      p.poly(rrect(mid[0] - 46, mid[1] - 8, mid[0] + 46, mid[1] + 34, 4), "#c84a4a", 5);
      p.stroke([[mid[0], mid[1]], [mid[0], mid[1] + 30]], 4, "#f2ead8");
      break;
    case "phone":
      p.poly(rrect(handR[0] - 18, handR[1] - 44, handR[0] + 18, handR[1] + 34, 6), "#121418", 5);
      p.poly(rrect(handR[0] - 12, handR[1] - 36, handR[0] + 12, handR[1] + 18, 3), "#7fd8f0", 0);
      break;
    case "thumbs": {
      const g = p.g;
      g.save();
      for (const c of [handL, handR]) {
        p.ell(c[0], c[1], 32, 30, "#F2F0EA", 6);
        p.poly(rrect(c[0] - 9, c[1] - 82, c[0] + 9, c[1] - 24, 7), "#F2F0EA", 5);
        p.stroke([[c[0] - 16, c[1] + 18], [c[0] + 16, c[1] + 18]], 4, "#C8C4BA");
      }
      g.restore();
      break;
    }
  }
};

// ---------------- main character ----------------
export const drawKid = (p: Pen, o: KidOpts) => {
  const k = kitOf(o);
  const light = o.light ?? -2.3;
  const gaze = clamp(o.gaze ?? 0, -1, 1), gazeY = clamp(o.gazeY ?? 0, -1, 1);
  const mode = o.mode;
  const seated = mode === "sit" || mode === "sitChin";
  const phase = o.phase ?? 0;
  const swing = Math.sin(phase * Math.PI * 2);
  // 3.5 heads tall: one head, one torso, one legs, half a pair of shoes
  const shY = seated ? 520 : mode === "crouch" ? 500 : mode === "kneel" ? 600 : mode === "slide" ? 528
    : mode === "slump" ? 630 : mode === "lift" ? 400 : 350;
  const hip = seated ? 735 : mode === "crouch" ? 700 : mode === "kneel" ? 780 : mode === "slide" ? 748
    : mode === "slump" ? 800 : mode === "lift" ? 620 : 560;
  const lean = mode === "run" ? 34 : mode === "slide" ? 46 : mode === "kick" ? 24 : mode === "bend" ? 66 : mode === "punch" ? 20 : 0;
  const sx = 300 + gaze * 12 + lean;
  const hx = sx + gaze * 22 + lean * 0.45;
  const hy = shY - 145 + gazeY * 10;
  const tw = o.kind === "muscle" ? 156 : 148;
  const hw = o.kind === "muscle" ? 158 : 150;
  const hem = hip + 26;
  const shortsHem = hip + 152;
  const sole = 952;

  // subtle cyan rim, no spikes
  if (o.aura) rimGlow(p, sx, hy + 330, 232, 430, "rgba(96,224,255,0.5)", 1);

  // hood resting behind the shoulders
  if (k.gear !== "bala" && k.gear !== "helmet" && k.gear !== "cap")
    p.poly(ellPts(sx, shY + 4, tw + 14, 56, 180, 360), mul(k.top, 0.78), 6);

  // legs: black sticks, bent knees, heel-toe shoe angle
  const shoe = (x: number, y: number, tilt: number) => {
    p.ell(x, y, 62, 42, k.shoes, 8, 0, 360, tilt);
    p.ell(x - 18, y - 17, 21, 9, "#3A3F4A", 0);
  };
  const leg = (a: P2, b: P2, c: P2) => p.line([a, b, c], LIMB, 26);
  if (seated) {
    for (const s of [-1, 1]) {
      leg([sx + s * 48, hip + 4], [sx + s * 62, hip + 112], [sx + s * 56, sole - 48]);
      shoe(sx + s * 58, sole - 22, 0);
    }
  } else if (mode === "kneel") {
    leg([sx - 44, hip], [sx - 96, hip + 76], [sx - 100, sole - 36]);
    shoe(sx - 106, sole - 14, 0);
    leg([sx + 44, hip], [sx + 108, hip + 26], [sx + 132, sole - 60]);
    shoe(sx + 142, sole - 36, -0.3);
  } else if (mode === "slide") {
    leg([sx - 34, hip], [sx - 122, hip + 44], [sx - 200, sole - 60]);
    shoe(sx - 226, sole - 46, -0.34);
    leg([sx + 34, hip], [sx + 98, hip + 58], [sx + 94, sole - 32]);
    shoe(sx + 104, sole - 14, -0.2);
  } else if (mode === "kick") {
    leg([sx - 40, hip], [sx - 58, 806], [sx - 54, sole - 46]);
    shoe(sx - 58, sole - 22, 0);
    leg([sx + 36, hip - 18], [sx + 164, hip - 20], [sx + 262, hip - 92]);
    shoe(sx + 288, hip - 104, -0.5);
  } else if (mode === "crouch") {
    for (const s of [-1, 1]) {
      leg([sx + s * 46, hip - 4], [sx + s * 112, hip + 44], [sx + s * 86, sole - 46]);
      shoe(sx + s * 92, sole - 22, s * 0.26);
    }
  } else if (mode === "slump") {
    for (const s of [-1, 1]) {
      leg([sx + s * 54, hip], [sx + s * 100, hip + 64], [sx + s * 86, sole - 42]);
      shoe(sx + s * 96, sole - 20, s * 0.24);
    }
  } else {
    const gait = mode === "walk" || mode === "run";
    const reach = mode === "run" ? 158 : 112;
    const hop = mode === "run" ? 126 : 68;
    for (const s of [-1, 1]) {
      const ph = gait ? swing * s : 0;
      const footX = sx + s * 44 + ph * reach;
      const footY = sole - (gait ? Math.max(0, ph) * hop : 0);
      const kneeY = hip + (shortsHem - hip) * 0.58 - (gait ? Math.max(0, ph) * 42 : 0);
      leg([sx + s * 42, hip - 6], [sx + s * 50 + ph * reach * 0.45, kneeY], [footX, footY - 36]);
      shoe(footX + s * 4, footY - 14, clamp(-ph, -1, 1) * 0.42);
    }
  }

  // shorts with two vertical white side stripes
  const shorts: P2[] = [
    [sx - tw + 8, hip - 16], [sx + tw - 8, hip - 16],
    [sx + hw - 6, shortsHem - 22], [sx + 28, shortsHem], [sx + 24, hip + 54],
    [sx - 24, hip + 54], [sx - 28, shortsHem], [sx - hw + 6, shortsHem - 22],
  ];
  p.poly(shorts, k.bottom, 8);
  if (k.skirt)
    p.poly([[sx - tw - 6, hip - 22], [sx + tw + 6, hip - 22],
      [sx + hw + 26, hip + 104], [sx - hw - 26, hip + 104]], mul(k.top, 0.84), 8);
  for (const s of [-1, 1])
    for (let i = 0; i < 2; i++) {
      const x = sx + s * (tw - 26 - i * 17);
      p.stroke([[x, hip + 6], [x + s * 7, shortsHem - 26]], i ? 6 : 11, k.stripe);
    }
  // neck stick
  p.line([[hx, hy + 98], [sx + (hx - sx) * 0.4, shY + 28]], LIMB, 46);

  // oversized bell-tapered hoodie
  const torso: P2[] = [
    [sx - tw + 10, shY + 36], [sx - tw + 2, shY + 8], [sx - tw * 0.56, shY - 10],
    [sx + tw * 0.56, shY - 10], [sx + tw - 2, shY + 8], [sx + tw - 10, shY + 36],
    [sx + hw, hem - 44], [sx + hw - 6, hem - 4], [sx + hw * 0.5, hem + 8], [sx, hem + 3],
    [sx - hw * 0.5, hem + 8], [sx - hw + 6, hem - 4], [sx - hw, hem - 44],
  ];
  p.gradFill(torso, k.top, mul(k.top, 0.68), light, 0.3);
  p.poly(torso, null, 11);
  for (const s of [-1, 1]) p.stroke([[sx + s * (hw - 16), hem - 40], [sx + s * (hw - 20), hem - 2]], 4, mul(k.top, 0.62));
  // kangaroo pocket
  p.poly(rrect(sx - 92, hem - 100, sx + 92, hem + 2, 20), mul(k.top, 0.84), 6);
  p.stroke([[sx - 88, hem - 92], [sx + 88, hem - 92]], 4, mul(k.top, 0.64));
  // hood collar + white drawstrings with round tips
  p.band([[sx - 76, shY + 10], [sx, shY + 34], [sx + 76, shY + 10]], mul(k.top, 0.82), 40, 8);
  for (const s of [-1, 1]) {
    p.line([[sx + s * 26, shY + 32], [sx + s * 32, shY + 104], [sx + s * 27, shY + 128]], k.stripe, 9);
    p.dot(sx + s * 27, shY + 138, 10, k.stripe);
  }

  // tactical vest / tie / badge / glasses are the only silhouette extras
  if (k.vest) {
    p.poly(rrect(sx - 104, shY + 40, sx + 104, hem - 24, 14), k.vest, 7);
    for (const s of [-1, 1]) for (let i = 0; i < 2; i++)
      p.poly(rrect(sx + s * 76 - 14, shY + 66 + i * 62, sx + s * 76 + 14, shY + 110 + i * 62, 5), mul(k.vest, 1.3), 3);
    p.poly([[sx - 14, shY + 44], [sx + 14, shY + 44], [sx + 14, hem - 28], [sx - 14, hem - 28]], mul(k.top, 1.25), 3);
  }
  if (k.tie) {
    p.poly([[sx - 15, shY + 18], [sx + 15, shY + 18], [sx + 20, shY + 44], [sx + 6, shY + 58], [sx - 6, shY + 58], [sx - 20, shY + 44]], k.tie, 4);
    p.poly([[sx - 11, shY + 58], [sx + 11, shY + 58], [sx + 26, shY + 196], [sx, shY + 222], [sx - 26, shY + 196]], k.tie, 4);
  }
  if (k.badge) {
    p.poly(star(sx - 68, shY + 96, 16, 7, 5), "#D8B45A", 2);
    p.stroke([[sx - 94, shY + 140], [sx - 44, shY + 140]], 6, "#D8B45A");
  }
  if (k.glasses && !o.shades) {
    const gy = hy + 6;
    p.stroke([[hx - 90, gy - 4], [hx - 10, gy - 4]], 6, "#2A2E38");
    p.stroke([[hx + 10, gy - 4], [hx + 90, gy - 4]], 6, "#2A2E38");
    p.ell(hx - 52, gy, 36, 30, null, 5);
    p.ell(hx + 52, gy, 36, 30, null, 5);
  }

  // arms: stick limbs with a cuffed sleeve, round ball mitt, bent pumping elbows in the gaits
  const shL: P2 = [sx - tw * 0.84, shY + 30], shR: P2 = [sx + tw * 0.84, shY + 30];
  let eL: P2 = [sx - 118, shY + 190], hL: P2 = [sx - 112, shY + 330];
  let eR: P2 = [sx + 118, shY + 190], hR: P2 = [sx + 112, shY + 330];
  let hand: "fist" | "v" | "open" = "fist";
  switch (mode) {
    case "walk": case "run": {
      const amp = mode === "run" ? 1.6 : 1;
      eL = [sx - 112, shY + 178 - swing * 26 * amp]; hL = [sx - 92 - swing * 62 * amp, shY + 258 - swing * 56 * amp];
      eR = [sx + 112, shY + 178 + swing * 26 * amp]; hR = [sx + 92 + swing * 54 * amp, shY + 258 + swing * 46 * amp];
      break;
    }
    case "point": eR = [sx + 150, shY + 96]; hR = [sx + 268, shY + 78]; break;
    case "pointSelf": eR = [sx + 96, shY + 124]; hR = [sx + 16, shY + 150]; break;
    case "hold": eL = [sx - 96, shY + 138]; hL = [sx - 54, shY + 208]; eR = [sx + 96, shY + 138]; hR = [sx + 54, shY + 208]; break;
    case "aim": eR = [sx + 104, shY + 128]; hR = [sx + 150, shY + 158]; eL = [sx - 62, shY + 142]; hL = [sx + 26, shY + 156]; break;
    case "kick": eL = [sx - 160, shY + 30]; hL = [sx - 232, shY + 58]; eR = [sx + 150, shY + 10]; hR = [sx + 212, shY + 56]; break;
    case "slide": eL = [sx - 128, shY + 118]; hL = [sx - 176, shY + 202]; eR = [sx + 124, shY + 128]; hR = [sx + 162, shY + 212]; break;
    case "punch": eR = [sx + 138, shY + 118]; hR = [sx + 238, shY + 100]; eL = [sx - 92, shY + 186]; hL = [sx - 44, shY + 232]; break;
    case "hug": eL = [sx - 88, shY + 104]; hL = [sx - 168, shY + 140]; eR = [sx + 88, shY + 104]; hR = [sx + 168, shY + 140]; break;
    case "salute": eR = [sx + 132, shY + 34]; hR = [sx + 48, shY - 40]; break;
    case "throw": eR = [sx + 110, shY - 24]; hR = [sx + 50, shY - 110]; eL = [sx - 110, shY + 170]; hL = [sx - 136, shY + 262]; break;
    case "cheer": eL = [sx - 142, shY - 24]; hL = [sx - 182, shY - 130]; eR = [sx + 142, shY - 24]; hR = [sx + 182, shY - 130]; break;
    case "slump": eL = [sx - 104, shY + 158]; hL = [sx - 96, shY + 288]; eR = [sx + 104, shY + 158]; hR = [sx + 96, shY + 288]; break;
    case "clap": eL = [sx - 82, shY + 130]; hL = [sx - 16, shY + 164]; eR = [sx + 82, shY + 130]; hR = [sx + 16, shY + 164]; break;
    case "bend": eL = [sx - 128, shY + 208]; hL = [sx - 96, shY + 330]; eR = [sx + 128, shY + 208]; hR = [sx + 96, shY + 330]; break;
    case "sit": eL = [sx - 116, shY + 176]; hL = [sx - 94, hip + 12]; eR = [sx + 116, shY + 176]; hR = [sx + 94, hip + 12]; break;
    case "sitChin":
      // one elbow braced forward with the fist under the chin, the other arm folded across the lap
      eL = [sx - 74, shY + 122]; hL = [sx - 34, shY - 30];
      eR = [sx + 112, shY + 172]; hR = [sx + 40, shY + 198];
      break;
    case "lift":
      // both arms straight up, hands gripping the seat either side above the crown
      eL = [sx - 118, shY - 84]; hL = [sx - 96, shY - 250];
      eR = [sx + 118, shY - 84]; hR = [sx + 96, shY - 250];
      break;
    case "smash":
      // both arms driven down in front, the chair angled into the floor
      eR = [sx + 120, shY + 58]; hR = [sx + 68, shY + 168];
      eL = [sx - 96, shY + 82]; hL = [sx - 16, shY + 176];
      break;
    case "vsign":
      eR = [sx + 112, shY + 66]; hR = [sx + 70, shY - 76];
      eL = [sx - 116, shY + 178]; hL = [sx - 108, shY + 316];
      hand = "v";
      break;
    case "highfive":
      eR = [sx + 138, shY - 44]; hR = [sx + 70, shY - 166];
      eL = [sx - 130, shY - 22]; hL = [sx - 174, shY - 126];
      hand = "open";
      break;
  }
  const mitt = (c: P2) => {
    p.dot(c[0], c[1], 31, LIMB);
    p.ell(c[0] - 10, c[1] - 12, 12, 8, "#3A3F4A", 0);
  };
  const arm = (a: P2, b: P2, c: P2) => {
    p.line([a, b, c], LIMB, 24);
    p.band([a, mixPt(a, b, 0.55)], k.top, 58, 8, "round");   // oversized sleeve on the upper arm
    const cuff = mixPt(a, b, 0.62);
    p.ell(cuff[0], cuff[1], 30, 24, mul(k.top, 0.86), 6);
    if (hand === "fist") mitt(c);
    else {
      mitt(c);
      const n = hand === "v" ? 2 : 4;
      for (let i = 0; i < n; i++) {
        const spread = (i - (n - 1) / 2) * (hand === "v" ? 19 : 13);
        p.stroke([[c[0] + spread * 0.35, c[1] - 18], [c[0] + spread, c[1] - 66]], 12, LIMB);
      }
    }
  };
  arm(shL, eL, hL);
  arm(shR, eR, hR);

  const prop: PropKind = o.prop ?? (o.kind === "terror" || o.kind === "swat" ? "rifle" : o.kind === "cop" ? "pistol" : "none");
  const chairOver = prop === "chair" && mode === "lift";
  // overhead the chair goes SIDE-ways, not upside-down: inverted, its four parallel legs stuck up out of the crown and
  // read as a spiky tiptop. Turned 90 degrees the profile is seat-plank / backrest one side, splayed legs the other,
  // and the two ends clear the head on either side, so the silhouette is a chair and not a headdress.
  const chairRot = mode === "lift" ? Math.PI / 2 - 0.16 : mode === "smash" ? 0.55 : 0.1;
  const chairScale = o.kind === "terror" ? 0.86 : mode === "lift" ? 1.18 : mode === "smash" ? 1 : 0.9;
  // an overhead chair sits behind the crown; a slamming chair comes down in front of everything
  if (chairOver) drawProp(p, prop, hx, hy, hL, hR, chairScale, chairRot);

  // head last so the card reads face-first
  drawHeadBase(p, hx, hy, k, light);
  drawGear(p, hx, hy, k);
  drawFace(p, hx, hy, o, k);
  if (chairOver) { mitt(hL); mitt(hR); }
  if (!chairOver) drawProp(p, prop, hx, hy, hL, hR, prop === "chair" ? chairScale : 1, prop === "chair" ? chairRot : 0);
  if (prop === "chair" && !chairOver) { mitt(hL); mitt(hR); }
  if (o.tied) drawProp(p, "rope", hx, hy, hL, hR);
  if ((o.frost ?? 0) > 0) {
    const g = p.g;
    g.save(); g.globalAlpha = Math.min(0.85, o.frost ?? 0);
    for (const [x, y, r] of [[sx - 96, shY + 80, 22], [sx + 92, shY + 160, 18], [hx - 60, hy + 30, 16], [sx + 40, hip - 20, 20]] as const) {
      p.poly(star(x, y, r, r * 0.4, 6), "#cfeeff", 0);
      p.stroke([[x - r, y], [x + r, y]], 3, "#e8f8ff");
      p.stroke([[x, y - r], [x, y + r]], 3, "#e8f8ff");
    }
    g.restore();
  }
  p.rot = null;
};

// =====================================================================================
// FX / HUD cards
// =====================================================================================
export const fxBlob = (p: Pen, col: string) => {
  const g = p.g;
  g.fillStyle = WHITE; g.fillRect(0, 0, 128, 128);
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  for (const [r, k] of [[0, 0], [0.32, 0.02], [0.5, 0.22], [0.66, 0.58], [0.82, 0.88], [1, 1]] as const) gr.addColorStop(r, mix(col, WHITE, k));
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
};

export const fxBlindSpot = (u: number) => (p: Pen) => {
  const a = clamp(u * 3, 0, 1) * clamp((1 - u) * 6, 0, 1);
  const g = p.g;
  g.save(); g.globalAlpha = Math.max(0.001, a);
  p.poly(rrect(20, 40, 680, 380, 26), "rgba(6,14,22,0.9)", 8);
  g.strokeStyle = "rgba(90,232,255,0.95)"; g.lineWidth = 6; g.strokeRect(20, 40, 660, 340);
  // corners
  for (const [x, y, sx, sy] of [[20, 40, 1, 1], [680, 40, -1, 1], [20, 380, 1, -1], [680, 380, -1, -1]] as const) {
    g.beginPath(); g.moveTo(x + 34 * sx, y); g.lineTo(x, y); g.lineTo(x, y + 34 * sy); g.stroke();
  }
  txt(p, "0.25s", 350, 160, 118, "#eafcff", "center", 900, "'Courier New', monospace");
  txt(p, "BLIND SPOT", 350, 268, 52, "#5fe4ff", "center", 800);
  g.strokeStyle = "rgba(95,228,255,0.6)"; g.lineWidth = 3;
  for (let i = 0; i < 3; i++) { g.beginPath(); g.moveTo(58, 320 + i * 14); g.lineTo(642, 320 + i * 14); g.stroke(); }
  p.ell(350, 160, 196, 96, null, 3);
  p.stroke([[350, 88], [350, 112]], 6, "#5fe4ff"); p.stroke([[350, 208], [350, 232]], 6, "#5fe4ff");
  p.stroke([[278, 160], [302, 160]], 6, "#5fe4ff"); p.stroke([[398, 160], [422, 160]], 6, "#5fe4ff");
  g.restore();
};

export const fxMeter = (k: number) => (p: Pen) => {
  const g = p.g;
  p.poly(rrect(16, 40, 624, 210, 20), "rgba(4,12,20,0.9)", 7);
  g.strokeStyle = "rgba(255,220,90,0.9)"; g.lineWidth = 5; g.strokeRect(16, 40, 608, 170);
  txt(p, "HERO METER", 44, 84, 34, "#cfeaff", "left", 800);
  txt(p, k > 1 ? ">100%" : `${Math.round(k * 100)}%`, 596, 84, 38, "#ffe066", "right", 900);
  p.poly(rrect(44, 116, 596, 172, 12), "#101a26", 4);
  const w = clamp(k, 0, 1.18) * 540;
  const g2 = p.g;
  g2.save(); g2.shadowColor = "#ffd83a"; g2.shadowBlur = 22;
  p.poly(rrect(48, 120, 48 + w, 168, 10), "#ffd83a", 0);
  g2.restore();
  for (let i = 0; i < 10; i++) p.stroke([[94 + i * 52, 116], [94 + i * 52, 172]], 2, "rgba(6,12,18,0.45)");
  if (k > 1) {
    g.save(); g.shadowColor = "#ff7a3a"; g.shadowBlur = 26;
    txt(p, "MAX!", 596, 196, 30, "#ff9a4a", "right", 900);
    g.restore();
  }
};

export const fxImpact = (label: string, col: string, u: number) => (p: Pen) => {
  const g = p.g;
  const k = clamp(u * 4, 0, 1);
  const sc = 0.6 + 0.6 * k + 0.12 * Math.sin(u * 10);
  g.save(); g.translate(300, 300); g.scale(sc, sc); g.rotate(-0.12);
  g.globalAlpha = clamp((1 - u) * 2.2, 0, 1);
  g.shadowColor = col; g.shadowBlur = 30;
  const burst: P2[] = [];
  for (let i = 0; i < 20; i++) {
    const a = (i / 20) * Math.PI * 2;
    const r = i % 2 ? 150 : 250;
    burst.push([Math.cos(a) * r, Math.sin(a) * r]);
  }
  p.poly(burst, col, 8);
  p.poly(star(0, 0, 170, 70, 8), "#ffffff", 0);
  g.fillStyle = "#1a1320"; txt(p, label, 0, 2, 82, "#1a1320", "center", 900);
  txt(p, label, 0, 0, 82, "#ffffff", "center", 900);
  g.restore();
};

export const fxKO = (u: number) => (p: Pen) => {
  const g = p.g;
  const k = clamp(u * 4, 0, 1);
  g.save(); g.globalAlpha = 0.95 * k;
  g.translate(200, 200);
  g.rotate(u * 3);
  for (let i = 0; i < 3; i++) {
    const a = (i / 3) * Math.PI * 2;
    g.save(); g.shadowColor = "#ffe066"; g.shadowBlur = 20;
    p.poly(star(Math.cos(a) * 92, Math.sin(a) * 92, 44, 18, 5), "#ffe066", 4);
    g.restore();
  }
  g.restore();
  g.save(); g.globalAlpha = k;
  txt(p, "K.O.", 200, 200, 96, "#ffffff", "center", 900);
  g.restore();
};

export const fxHearts = (u: number, n = 5, col = "#ff7aa8") => (p: Pen) => {
  const g = p.g;
  for (let i = 0; i < n; i++) {
    const ph = (u + i / n) % 1;
    const x = 140 + i * 70 + Math.sin(ph * 8 + i) * 22;
    const y = 320 - ph * 240;
    const s = 0.7 + 0.5 * Math.sin(ph * Math.PI);
    g.save(); g.globalAlpha = clamp(1 - ph, 0, 1) * 0.95; g.translate(x, y); g.scale(s, s);
    g.shadowColor = col; g.shadowBlur = 22;
    p.poly([[-24, -8], [-24, -22], [-8, -26], [0, -12], [8, -26], [24, -22], [24, -8], [0, 26]], col, 4);
    g.restore();
  }
};

export const fxChalk = (u: number) => (p: Pen) => {
  const g = p.g;
  g.save();
  g.globalAlpha = 1;
  for (let i = 0; i < 4; i++) {
    p.stroke([[40, 160 + i * 18], [260 - i * 20, 150 + i * 18]], 5 - i, "rgba(240,244,255,0.55)");
  }
  g.shadowColor = "#ffffff"; g.shadowBlur = 18;
  p.poly(rrect(280, 120, 392, 176, 18), "#f6f4e8", 5);
  p.poly(rrect(392, 130, 430, 166, 12), "#e8e4d4", 4);
  g.restore();
  void u;
};

export const fxFrost = (u: number) => (p: Pen) => {
  const g = p.g;
  g.save(); g.globalAlpha = clamp(u * 2, 0, 1) * 0.85;
  for (let i = 0; i < 14; i++) {
    const a = (i / 14) * Math.PI * 2, r = 120 + (i % 3) * 66;
    const x = 300 + Math.cos(a) * r, y = 360 + Math.sin(a) * r * 1.1;
    const s = 18 + (i % 4) * 8;
    g.shadowColor = "#8fe8ff"; g.shadowBlur = 16;
    p.poly(star(x, y, s, s * 0.34, 6), "#cfeeff", 0);
    p.stroke([[x - s, y], [x + s, y]], 3, "#ffffff");
    p.stroke([[x, y - s], [x, y + s]], 3, "#ffffff");
  }
  g.restore();
  p.poly(rrect(140, 480, 460, 620, 24), "rgba(220,246,255,0.25)", 4);
  txt(p, "-78°C", 300, 550, 74, "#dff8ff", "center", 900, "'Courier New', monospace");
};

export const fxCO2 = (u: number) => (p: Pen) => {
  const g = p.g;
  const k = clamp(u * 3, 0, 1);
  g.save(); g.globalAlpha = clamp((1 - u) * 1.8, 0, 1) * 0.9;
  g.translate(140, 340);
  g.rotate(-0.08);
  for (let i = 0; i < 10; i++) {
    const r = 30 + i * 22 * k;
    softEll(p, i * 44 * k, Math.sin(i * 1.7) * 34 * k, r, r * 0.8, "rgba(230,250,255,0.55)", 1);
  }
  g.restore();
};

export const fxShades = (p: Pen) => {
  p.poly(rrect(40, 60, 220, 112, 14), "#0c0e12", 6);
  p.poly(rrect(236, 60, 416, 112, 14), "#0c0e12", 6);
  p.stroke([[220, 80], [236, 80]], 10, "#0c0e12");
  p.stroke([[70, 82], [150, 74]], 6, "rgba(140,210,240,0.8)");
  p.stroke([[270, 74], [350, 82]], 6, "rgba(140,210,240,0.8)");
};

export const fxRifle = (p: Pen) => {
  const g = p.g;
  g.save(); g.translate(200, 150); g.rotate(-0.22);
  p.poly(rrect(-170, -18, 120, 12, 6), "#2a2e34", 6);
  p.poly([[100, -14], [196, -8], [196, 4], [100, 8]], "#3a4048", 4);
  p.poly(rrect(-72, 10, -20, 70, 5), "#20242a", 4);
  p.poly(rrect(-170, 2, -104, 40, 5), "#4a3a28", 4);
  p.stroke([[70, -18], [96, -54]], 7, "#2a2e34");
  g.restore();
};

// the chair he slammed with, once it leaves his hands: the same 2D drawing, dropped flat on the floor beside the
// counted-out man. A held prop that simply stops existing on one frame reads as a rendering glitch.
export const fxChair = (p: Pen) => drawChair(p, 260, 260, 0, 1);

export const fxWalkie = (p: Pen) => {
  p.poly(rrect(60, 180, 140, 300, 12), "#22262c", 7);
  p.poly(rrect(74, 196, 126, 236, 4), "#6fe8d0", 0);
  p.stroke([[100, 180], [110, 100]], 7, "#22262c");
  p.dot(96, 270, 6, "#c84a4a");
  txt(p, "CH 4", 100, 254, 22, "#081018", "center", 800);
};

export const fxVest = (p: Pen) => {
  p.poly(rrect(120, 150, 280, 420, 18), "#2e3a2c", 8);
  for (let i = 0; i < 3; i++) p.poly(rrect(138, 172 + i * 68, 196, 220 + i * 68, 6), "#3e4a3a", 4);
  p.poly([[212, 172], [262, 172], [262, 330], [212, 330]], "#2a3026", 4);
  txt(p, "S.W.A.T.", 250, 250, 20, "#c8d4b8", "center", 800);
};

export const fxSpeed = (u: number) => (p: Pen) => {
  const g = p.g;
  g.save(); g.globalAlpha = 0.7 * (1 - u);
  for (let i = 0; i < 16; i++) {
    const x = 40 + (i * 61) % 520, y = 40 + (i * 97) % 540;
    p.stroke([[x, y], [x + 90 + (i % 4) * 30, y - 12]], 4 + (i % 3), "rgba(235,248,255,0.8)");
  }
  g.restore();
};

export const fxFlash = (u: number) => (p: Pen) => {
  const g = p.g;
  const k = clamp(u * 3, 0, 1);
  g.save(); g.globalAlpha = clamp((1 - u) * 1.6, 0, 1);
  g.translate(200, 200);
  g.shadowColor = "#fff8d0"; g.shadowBlur = 34;
  p.poly(star(0, 0, 180 * k, 54 * k, 10), "#fff6d0", 0);
  p.ell(0, 0, 46 * k, 46 * k, "#ffffff", 0);
  g.restore();
};

export const fxTie = (p: Pen) => {
  p.poly([[250, 80], [350, 80], [372, 210], [300, 300], [228, 210]], "#c83a3a", 8);
  p.poly([[268, 60], [332, 60], [340, 104], [300, 124], [260, 104]], "#a82a2a", 7);
  for (let i = 0; i < 4; i++) p.stroke([[268 + i * 18, 130 + i * 30], [318 + i * 12, 118 + i * 30]], 4, "#e86a6a");
};

export const fxQuestion = (p: Pen) => {
  const g = p.g;
  g.save(); g.shadowColor = "#7fe4ff"; g.shadowBlur = 22;
  txt(p, "?", 150, 170, 180, "#ffffff", "center", 900);
  txt(p, "?", 260, 110, 110, "#7fe4ff", "center", 900);
  g.restore();
};

export const fxSweat = (p: Pen) => {
  p.poly([[170, 150], [196, 216], [170, 240], [144, 216]], "#a8e4ff", 5);
  p.dot(162, 200, 6, "#ffffff");
};

export const fxRope = (p: Pen) => {
  p.stroke([[60, 240], [200, 290], [340, 240]], 14, "#c8b48a");
  p.stroke([[120, 272], [280, 272]], 8, "#a8946a");
};

export const fxStarBurst = (p: Pen) => {
  const g = p.g;
  g.save(); g.shadowColor = "#ffe066"; g.shadowBlur = 26;
  p.poly(star(200, 200, 120, 34, 6), "#ffe066", 4);
  p.poly(star(200, 200, 60, 20, 6), "#ffffff", 0);
  g.restore();
};

// keep the class import used in the type position only
export type PenLike = PenClass;
