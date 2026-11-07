// Procedural 2D cast for InstantSkillShort, drawn every frame into the 600 x 1000 design box with Pen.
// SKILL.md Section 2: SU = 0.00216 (1000 units = 2.16 m), PIV = 975 at the feet, soles at y = 952, warm cream-white
// head #fdfaf2 with HEAD_R = 145 centred at (300, 235) -> chin at y = 380, #351f22 ink outlines, compact bean torso
// (shoulders 120 wide / hips 145, y 375..585), straight parallel legs at x = 265 and 335, solid oval pupils
// (rx 16, ry 22) with ZERO white anime shine dots, and hair/hats rising above the head contour (y < 90).
//
// Roles: 'hero' sky-blue hoodie #4ea8de + white drawstrings + kangaroo pocket + light-cream trousers.
//        'skater' backwards dark cap + red hoodie #e63946 (the jaw-dropping bystander, also a poker opponent).
//        'grandmaster' beige cardigan over a white shirt, round gold glasses (also a poker opponent).
//        'friend' green cap + green hoodie #52b788 (also the airplane passenger).
// Every action is a continuous 0..1 parameter, never a discrete pose swap; cast.ts quantizes them to 0.02 in the
// texture key so the Pool caches one canvas per visible stage of the motion.
import { Pen, INK } from "./pen";
import { SIT_DROP } from "./story";

export { Pen, INK };
type P2 = [number, number];

export const HEAD = "#fdfaf2";
export const HEAD_SH = "#ece1cd";
export const HEAD_R = 145;
export const WHITE = "#ffffff";
export const CYAN = "#00f5d4";
export const BLIND = "#2b2638";

const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const clamp01 = (x: number) => clamp(x, 0, 1);
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const seg = (a: number, b: number, x: number) => clamp01((x - a) / (b - a));
const rad = (d: number) => (d * Math.PI) / 180;

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
const mul = (c: string, k: number) => {
  const n = parseInt(c.slice(1), 16);
  const ch = (v: number) => Math.min(255, Math.round(v * k)).toString(16).padStart(2, "0");
  return `#${ch((n >> 16) & 255)}${ch((n >> 8) & 255)}${ch(n & 255)}`;
};

// ---------------- types ----------------
export type Role = "hero" | "skater" | "grandmaster" | "friend";
export type Expr = "confidentSmile" | "smirk" | "panicShock" | "strainGrin" | "brokeSad" | "happyOpen";

export type KidOpts = {
  role: Role;
  expr: Expr;
  gaze?: number;      // -1..1 pupil offset
  gazeY?: number;     // -1..1
  phase?: number;     // 0..1 idle breathing cycle (drives a small bob so a held body is never dead)

  // --- hero overrides (all continuous unless noted) ---
  phoneP?: number;    // 0..1 phone rises from hip to chest beside the face
  cyanEyes?: boolean; // neon #00f5d4 "skill downloaded" eyes with a rim glow
  boardP?: number;    // 0 rolling / 0.5 mid-air kickflip spin / 1.0 landed
  kneePainP?: number; // 0..1 both hands clamp the sore knees, body folds
  blindfold?: boolean; // #2b2638 band over the eyes
  blindUpP?: number;  // 0..1 band slides up onto the forehead (shot 6)
  reachP?: number;    // 0..1 fist travels to the pinned 3D king (Rule B contact)
  cubeP?: number;     // 0..1 Rubik's solve spin, then the table slam
  dictP?: number;     // 0..1 dictionary pages fan open
  shades?: boolean;   // dark sunglasses pushed up over the blindfold look (shot 8)

  // --- hero overrides, Act 2/3 (all continuous 0..1 unless noted) ---
  boardKind?: "skate" | "snow"; // which deck the feet ride; only ever set alongside boardP
  sitP?: number;      // 0..1 the whole upper body comes down to the seat line (cockpit tub, plaza bench)
  sitDrop?: number;   // design units at sitP 1 - the seat's cushion height, solved by cast.ts from story.seatDrop
  wheelP?: number;    // 0..1 both fists forward onto a drawn steering wheel (Rule A)
  leanP?: number;     // 0..1 the torso and skull fold sideways under G-force
  handsUpP?: number;  // 0..1 palms open at the chest, turned toward him: look what these hands did
  pointUpP?: number;  // 0..1 one arm raised, index finger at the sky
  splitP?: number;    // 0..1 one hand clamps the skull, the other the thigh: brain vs body
  headPainP?: number; // 0..1 both palms crush the temples
  earsP?: number;     // 0..1 both palms flatten over the ears
  guitarP?: number;   // 0..1 the guitar is in his arms; back to 0 means his hands are off it, not that it vanished
  strumP?: number;    // 0..1 one strum cycle: a sawtooth, because the offset it drives is a sine over it
  guitarSetP?: number;// 0..1 the same guitar slides out of the grip and rests propped on the ground
  digP?: number;      // 0..1 shovel stroke, cycling: the blade travels down-and-back
  codeP?: number;     // 0..1 the glyph descends into the right fist at design (452, 512)
  walkP?: number;     // 0..1 stride cycle, the two legs in antiphase

  // --- supporting-cast reactions ---
  jawP?: number;      // 0..1 skater's jaw drops
  startleP?: number;  // 0..1 grandmaster recoils, arms up
  gestP?: number;     // 0..1 friend points at the board
  clapP?: number;     // 0..1 passenger claps (palms meet per cycle)
  slumpP?: number;    // 0..1 poker opponents fold forward in defeat
  thumbsP?: number;   // 0..1 double thumbs-up at his own chest
  armsUpP?: number;   // 0..1 smug both-arms-up V
  starP?: number;     // 0..1 gold sparkles on the shoulders
  sweat?: number;     // 0..1 temple bead
  laughP?: number;    // 0..1 doubled over, laughing at him
};

type Kit = {
  top: string; topDk: string; topLt: string; trim: string;
  pants: string; pantsDk: string; shoes: string;
  hat: "none" | "hair" | "capBack" | "cap" | "bald"; hatCol: string; hatDk: string;
  openFront?: boolean; buttons?: boolean;
};

const KIT: Record<Role, Kit> = {
  hero: {
    top: "#4ea8de", topDk: "#2f7cb0", topLt: "#8fd2f4", trim: "#ffffff",
    pants: "#f4f7fb", pantsDk: "#c9d3e2", shoes: "#2b2628",
    // no hair at all: the brief's hero is a clean cream sphere, and the hood collar behind his neck is what gives
    // the head its silhouette. hat stays "none" so drawHeadgear skips him entirely.
    hat: "none", hatCol: "#35261f", hatDk: "#241813",
  },
  skater: {
    top: "#e63946", topDk: "#a51f2b", topLt: "#ff8f98", trim: "#f1faee",
    pants: "#3f5b7a", pantsDk: "#2a3d54", shoes: "#2b2628",
    hat: "capBack", hatCol: "#2b2628", hatDk: "#1b1719",
  },
  grandmaster: {
    top: "#d9c39a", topDk: "#a88d63", topLt: "#efe0c2", trim: "#7a5a34",
    pants: "#4a4038", pantsDk: "#332c26", shoes: "#20191a",
    hat: "bald", hatCol: "#cfc9c2", hatDk: "#a9a29a",
    openFront: true, buttons: true,
  },
  friend: {
    top: "#52b788", topDk: "#33875e", topLt: "#8fd6ab", trim: "#eaf7ee",
    pants: "#c8a86b", pantsDk: "#9d824f", shoes: "#2b2628",
    hat: "cap", hatCol: "#3f9a6d", hatDk: "#2b6f4c",
  },
};

// The Rule B contact point. world.ts maps these design units through the billboard basis with depthOffset = -0.08,
// which lands the knuckles 8 cm in FRONT of the black king's base, so the 2D fist covers the 3D piece with no gap.
// y 478 is not a style choice, it is arithmetic: (975-478)*SU*0.92 = 0.9876 m, minus world.ts KING_BASE_DROP 0.07
// puts the pinned piece's base on the board's top surface (CHESS.board[1] 0.90 + its 0.018 half-depth = 0.918 m).
export const HERO_FIST: P2 = [511, 478];

// Shot 24's downloaded glyph, in the SAME design space. story.ts PROP_QUADS[24] carries this exact pair as
// `{ slot: "hero", hand: [452, 512] }`, which is how the frame checker projects the glyph: it solves the billboard
// for this point on the hero's card, so the number has to be where drawCharacter actually paints it.
export const HERO_CODE: P2 = [452, 512];

// Floating brows: one thick ink bar per side, high enough over the lid arcs to stay readable at card scale. The
// tilt IS the emotion, so the table is the whole expression set; `skew` breaks the symmetry for the smirk.
const BROW: Record<Expr, [number, number]> = {
  confidentSmile: [-4, -12],
  smirk: [6, -16],
  panicShock: [-18, -12],
  strainGrin: [10, -8],
  brokeSad: [-16, 10],
  happyOpen: [-14, -8],
};

const drawBrows = (p: Pen, hx: number, ey: number, expr: Expr, skew: number) => {
  const [inn, out] = BROW[expr];
  for (const s of [-1, 1]) {
    const ex = hx + s * 48, k = s > 0 ? skew : -skew;
    p.stroke([[ex - s * 30, ey - 76 + inn + k], [ex + s * 30, ey - 76 + out - k]], 13);
  }
};

// ---------------- face ----------------
const drawFace = (p: Pen, hx: number, hy: number, o: KidOpts) => {
  const dx = 48, ey = hy + 8, my = hy + 68;
  const px = clamp(o.gaze ?? 0, -1, 1) * 9, py = clamp(o.gazeY ?? 0, -1, 1) * 8;
  const pupil = (ex: number, rx: number, ry: number) => {
    if (o.cyanEyes) {
      const g = p.g;
      g.save(); g.shadowColor = CYAN; g.shadowBlur = 26;
      p.ell(ex + px, ey + py, rx, ry, CYAN, 0);
      p.ell(ex + px, ey + py, rx * 0.55, ry * 0.55, "#b6fff2", 0);
      g.restore();
    } else {
      p.ell(ex + px, ey + py, rx, ry, INK, 0);   // solid pupil, no shine dot
    }
  };

  if (o.blindfold && !(o.blindUpP && o.blindUpP > 0.5)) {
    // eyes fully covered: brows hidden under the band, only the mouth carries the expression
    drawMouth(p, hx, my, o);
    return;
  }
  if (o.shades) {
    drawGlassesShades(p, hx, ey);
    drawMouth(p, hx, my, o);
    return;
  }

  switch (o.expr) {
    case "strainGrin":
      for (const s of [-1, 1]) {
        const ex = hx + s * dx;
        p.stroke([[ex - s * 20, ey - 18], [ex + s * 14, ey], [ex - s * 20, ey + 18]], 11);
      }
      break;
    case "panicShock":
      for (const s of [-1, 1]) {
        const ex = hx + s * dx;
        p.arc(ex, ey - 50, 26, 14, 195, 345, 10);
        pupil(ex, 19, 25);
      }
      break;
    case "happyOpen":
      for (const s of [-1, 1]) {
        const ex = hx + s * dx;
        p.arc(ex, ey - 44, 24, 16, 190, 350, 11);
        p.stroke([[ex - 20, ey + 4], [ex - 6, ey - 12], [ex + 8, ey + 4]], 11);
      }
      break;
    case "brokeSad":
      for (const s of [-1, 1]) {
        const ex = hx + s * dx;
        p.stroke([[ex - s * 30, ey - 44], [ex + s * 22, ey - 32]], 11);
        pupil(ex, 15, 21);
        p.ell(ex - s * 4, ey + 30, 9, 16, "#8fd6f0", 2);   // a tear hanging on the cheek
      }
      break;
    case "smirk":
      for (const s of [-1, 1]) {
        const ex = hx + s * dx;
        p.stroke([[ex - s * 30, ey - 42 - (s > 0 ? 6 : 0)], [ex + s * 24, ey - 36 + (s > 0 ? 8 : 0)]], 12);
        pupil(ex, s > 0 ? 16 : 15, s > 0 ? 20 : 14);        // near-lidded on the shaded side
        if (s > 0) p.ell(ex, ey - 8, 18, 10, HEAD, 0);
      }
      break;
    default: // confidentSmile
      for (const s of [-1, 1]) {
        const ex = hx + s * dx;
        p.arc(ex, ey - 42, 22, 12, 200, 340, 10);
        pupil(ex, 16, 22);
      }
  }
  drawBrows(p, hx, ey, o.expr, o.expr === "smirk" ? 9 : 0);
  if (o.role === "grandmaster") drawGMGlasses(p, hx, ey);
  if (o.sweat && o.sweat > 0.05) {
    const a = clamp01(o.sweat);
    p.ell(hx - 108, ey - 26, 12 * a + 4, 16 * a + 5, "#8fd6f0", 3);
  }
  drawMouth(p, hx, my, o);
};

const drawMouth = (p: Pen, hx: number, my: number, o: KidOpts) => {
  const jaw = clamp01(o.jawP ?? 0);
  switch (o.expr) {
    case "strainGrin": {
      const x0 = hx - 60, x1 = hx + 60, y0 = my - 20, y1 = my + 22;
      p.poly([[x0, y0], [x1, y0], [x1 + 5, (y0 + y1) / 2], [x1, y1], [x0, y1], [x0 - 5, (y0 + y1) / 2]], WHITE, 8);
      p.stroke([[x0 + 4, my + 1], [x1 - 4, my + 1]], 5);
      for (const t of [-36, -12, 12, 36]) p.stroke([[hx + t, y0 + 3], [hx + t, y1 - 3]], 4);
      break;
    }
    case "panicShock": {
      const open = 14 + 22 * Math.max(jaw, 0.35);
      const m = smoothClosed([[hx - 28, my - 14], [hx + 28, my - 14], [hx + 32, my + open], [hx - 32, my + open]], 5);
      p.poly(m, "#4e1a22", 8);
      p.ell(hx, my + open * 0.55, 17, 11, "#d04d44", 0);
      break;
    }
    case "happyOpen": {
      const m = smoothClosed([[hx - 52, my - 14], [hx + 52, my - 14], [hx + 44, my + 34], [hx - 44, my + 34]], 5);
      p.poly(m, "#521e24", 8);
      p.poly([[hx - 46, my - 12], [hx + 46, my - 12], [hx + 38, my + 6], [hx - 38, my + 6]], WHITE, 0);
      p.ell(hx, my + 26, 24, 12, "#dc564e", 0);
      break;
    }
    case "brokeSad": {
      p.arc(hx, my + 26, 34, 24, 200, 340, 9);
      p.poly(smoothClosed([[hx - 26, my + 6], [hx + 26, my + 6], [hx + 18, my + 20], [hx - 18, my + 20]], 4), "#521e24", 5);
      break;
    }
    case "smirk": {
      p.stroke([[hx - 34, my + 4], [hx + 2, my + 14], [hx + 44, my - 8]], 10);
      p.stroke([[hx + 30, my - 6], [hx + 46, my - 14]], 8);
      break;
    }
    default: {
      const m = smoothClosed([
        [hx - 46, my - 8], [hx, my - 4], [hx + 46, my - 8],
        [hx + 30, my + 24], [hx, my + 30], [hx - 30, my + 24],
      ], 5);
      p.poly(m, "#521e24", 8);
      p.poly([[hx - 42, my - 7], [hx + 42, my - 7], [hx + 36, my + 6], [hx - 36, my + 6]], WHITE, 0);
      p.ell(hx, my + 24, 22, 11, "#dc564e", 0);
    }
  }
  if (o.expr !== "brokeSad") {
    p.ell(hx - 82, my - 8, 20, 11, "#f4bcae", 0);
    p.ell(hx + 82, my - 8, 20, 11, "#f4bcae", 0);
  }
};

const drawGlassesShades = (p: Pen, hx: number, ey: number) => {
  const g = p.g;
  g.save(); g.globalAlpha = 0.92;
  for (const s of [-1, 1]) p.poly(smoothClosed([[hx + s * 16, ey - 20], [hx + s * 78, ey - 24], [hx + s * 82, ey + 18], [hx + s * 20, ey + 22]], 4), "#22191c", 7);
  p.stroke([[hx - 16, ey - 8], [hx + 16, ey - 8]], 7);
  g.restore();
  g.save(); g.globalAlpha = 0.28;
  for (const s of [-1, 1]) p.stroke([[hx + s * 30, ey + 12], [hx + s * 62, ey - 16]], 7, "#cfd8e6");
  g.restore();
};

const drawGMGlasses = (p: Pen, hx: number, ey: number) => {
  const gold = "#c8a24a";
  for (const s of [-1, 1]) p.arc(hx + s * 48, ey, 30, 28, 0, 360, 6, gold);
  p.stroke([[hx - 18, ey - 2], [hx + 18, ey - 2]], 5, gold);
  p.stroke([[hx - 78, ey - 6], [hx - 104, ey - 14]], 5, gold);
  p.stroke([[hx + 78, ey - 6], [hx + 104, ey - 14]], 5, gold);
};

// ---------------- headgear (must clear the y < 90 head contour) ----------------
const drawHeadgear = (p: Pen, hx: number, hy: number, k: Kit, o: KidOpts) => {
  if (k.hat === "none") return;
  if (k.hat === "hair") {
    p.poly(smoothClosed([[hx - 128, hy - 62], [hx - 96, hy - 152], [hx - 40, hy - 172], [hx + 20, hy - 184], [hx + 88, hy - 158], [hx + 126, hy - 60], [hx + 96, hy - 118], [hx, hy - 138], [hx - 96, hy - 112]], 6), k.hatCol, 9);
  } else if (k.hat === "capBack") {
    // backwards cap: crown over the skull, brim sticking out to screen-left, front opening showing hair
    p.poly(smoothClosed([[hx - 122, hy - 78], [hx - 108, hy - 164], [hx - 10, hy - 192], [hx + 104, hy - 160], [hx + 122, hy - 74]], 6), k.hatCol, 9);
    p.poly(smoothClosed([[hx - 118, hy - 74], [hx - 186, hy - 58], [hx - 190, hy - 88], [hx - 122, hy - 96]], 5), k.hatDk, 8);
    p.dot(hx - 8, hy - 186, 9, k.hatDk);
    p.stroke([[hx - 60, hy - 96], [hx + 70, hy - 110]], 6, k.hatDk);
  } else if (k.hat === "cap") {
    p.poly(smoothClosed([[hx - 120, hy - 76], [hx - 104, hy - 166], [hx, hy - 194], [hx + 104, hy - 164], [hx + 120, hy - 72]], 6), k.hatCol, 9);
    p.poly(smoothClosed([[hx + 92, hy - 74], [hx + 196, hy - 56], [hx + 198, hy - 84], [hx + 96, hy - 96]], 5), k.hatDk, 8);
    p.dot(hx, hy - 188, 8, k.hatDk);
    p.stroke([[hx - 118, hy - 84], [hx + 118, hy - 86]], 7, k.hatDk);
  } else if (k.hat === "bald") {
    // balding grandmaster: grey ring of hair plus a comb-over that still breaks the head silhouette
    p.poly(smoothClosed([[hx - 138, hy - 40], [hx - 146, hy - 108], [hx - 108, hy - 138], [hx - 40, hy - 148], [hx + 40, hy - 146], [hx + 110, hy - 132], [hx + 142, hy - 96], [hx + 134, hy - 36], [hx + 118, hy - 84], [hx + 40, hy - 112], [hx - 50, hy - 114], [hx - 116, hy - 82]], 6), k.hatCol, 8);
    p.stroke([[hx - 30, hy - 118], [hx + 52, hy - 106]], 9, k.hatDk);
  }
};

const drawBlindfold = (p: Pen, hx: number, ey: number, up: number) => {
  const k = clamp01(up);
  // rolled up = the SAME strap translated onto the forehead, not a narrower one. Narrowing it (an earlier attempt)
  // pulled the ends inside the head circle, and a dark shape that touches the skull silhouette reads as a hair cap;
  // keeping the wrap that pokes past the outline plus the knot keeps it an object tied around the head.
  const yc = lerp(ey, ey - 78, k);
  const tw = lerp(150, 142, k);
  const bw = lerp(152, 150, k);
  const band = smoothClosed([[hx - tw, yc - 26], [hx + tw, yc - 26], [hx + bw, yc + 30], [hx - bw, yc + 30]], 5);
  p.poly(band, BLIND, 9);
  p.stroke([[hx - bw + 12, yc + 2], [hx + bw - 12, yc + 2]], 5, "#4a4258");
  // the knot stays visible in both states: a cloth tie is what tells the eye the band is a blindfold, not hair
  p.ell(hx + bw - 6, yc + 4, 20, 16, mul(BLIND, 0.78), 7);
};

// ---------------- limbs ----------------
const limb = (p: Pen, a: P2, b: P2, col: string, w = 24) => p.line([a, b], col, w);

const drawArm = (p: Pen, sh: P2, el: P2, ha: P2, k: Kit, bare: string, bent = 1) => {
  limb(p, sh, el, k.top, 26 * bent);
  limb(p, el, ha, k.topLt === k.top ? bare : k.top, 22 * bent);
};

// a closed fist: the shape Rule B needs at a known design coordinate
const drawFist = (p: Pen, x: number, y: number, col: string, r = 20) => {
  p.poly(smoothClosed([[x - r, y - r], [x + r, y - r], [x + r + 3, y + r], [x - r, y + r]], 4), col, 7);
  p.stroke([[x - r + 5, y - 1], [x + r - 4, y - 1]], 4);
  p.stroke([[x - r + 4, y + 7], [x + r - 5, y + 7]], 3);
};

const drawOpenHand = (p: Pen, x: number, y: number, col: string, r = 18) => {
  p.ell(x, y, r, r * 1.1, col, 7);
  for (const t of [-9, -3, 3, 9]) p.stroke([[x + t, y - r - 2], [x + t * 1.2, y - r - 16]], 6, col);
};

const drawThumbUp = (p: Pen, x: number, y: number, col: string, s: number) => {
  p.poly(smoothClosed([[x - 16 * s, y - 10 * s], [x + 16 * s, y - 12 * s], [x + 14 * s, y + 18 * s], [x - 14 * s, y + 18 * s]], 4), col, 7);
  p.poly(smoothClosed([[x - 4 * s, y - 12 * s], [x + 2 * s, y - 40 * s], [x + 12 * s, y - 38 * s], [x + 10 * s, y - 10 * s]], 4), col, 7);
};

// ---------------- held props (Rule A: everything portable lives in 2D on the hands) ----------------
const drawPhone = (p: Pen, x: number, y: number, prog: number) => {
  p.rot = [rad(-12), x, y];
  p.poly([[x - 44, y - 78], [x + 44, y - 78], [x + 44, y + 78], [x - 44, y + 78]], "#1b1f2a", 7);
  p.poly([[x - 36, y - 64], [x + 36, y - 64], [x + 36, y + 60], [x - 36, y + 60]], "#0b1a24", 0);
  // tutorial thumbnail: a tiny skater silhouette on a ramp
  p.stroke([[x - 30, y + 6], [x - 6, y - 26], [x + 16, y + 6]], 6, "#2e6f86");
  p.ell(x + 2, y - 34, 8, 8, "#7ee8fa", 0);
  p.stroke([[x - 4, y - 22], [x + 6, y - 8]], 5, "#7ee8fa");
  // download bar
  p.stroke([[x - 30, y + 34], [x + 30, y + 34]], 8, "#22404f");
  p.stroke([[x - 30, y + 34], [x - 30 + 60 * clamp01(prog), y + 34]], 8, CYAN);
  p.stroke([[x - 22, y + 52], [x + 22, y + 52]], 5, "#63d0e6");
  p.rot = null;
};

const CUBECOL = ["#ffffff", "#ffd23f", "#e63946", "#2a9d34", "#2f6fd0", "#ff8c1a"];
const cubeFace = (p: Pen, x: number, y: number, s: number, solved: boolean, seed: number) => {
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      const c = solved ? CUBECOL[0] : CUBECOL[(i * 3 + j + seed) % 6];
      p.poly([[x + (i - 1.5) * s, y + (j - 1.5) * s], [x + (i - 0.5) * s, y + (j - 1.5) * s], [x + (i - 0.5) * s, y + (j - 0.5) * s], [x + (i - 1.5) * s, y + (j - 0.5) * s]], c, 4);
    }
  }
};
const drawCube = (p: Pen, x: number, y: number, prog: number, solved: boolean) => {
  const s = 30;
  const spin = clamp01(prog) * 900;
  p.rot = [rad(Math.sin(spin * 0.0174533) * 18), x, y];
  const blur = clamp01(prog) < 0.98 ? 1 : 0;
  p.poly([[x - s * 1.5, y - s * 1.5], [x + s * 1.5, y - s * 1.5], [x + s * 1.5, y + s * 1.5], [x - s * 1.5, y + s * 1.5]], "#14121a", 7);
  cubeFace(p, x, y, s, solved, Math.floor(prog * 26));
  // top and right faces for a solid 3D read
  p.poly([[x - s * 1.5, y - s * 1.5], [x - s * 0.6, y - s * 2.3], [x + s * 2.4, y - s * 2.3], [x + s * 1.5, y - s * 1.5]], "#1b1822", 6);
  p.poly([[x + s * 1.5, y - s * 1.5], [x + s * 2.4, y - s * 2.3], [x + s * 2.4, y + s * 0.7], [x + s * 1.5, y + s * 1.5]], "#1b1822", 6);
  for (let j = 0; j < 3; j++) {
    const c = solved ? CUBECOL[1] : CUBECOL[(j + 2 + Math.floor(prog * 9)) % 6];
    p.poly([[x + s * (1.6 + j * 0.28), y - s * (1.5 - j * 0.28)], [x + s * (1.6 + (j + 1) * 0.28), y - s * (1.5 - (j + 1) * 0.28)],
    [x + s * (1.6 + (j + 1) * 0.28), y + s * (0.7 - j * 0.28)], [x + s * (1.6 + j * 0.28), y + s * (0.7 - j * 0.28)]], c, 0);
  }
  if (blur) {
    const g = p.g; g.save(); g.globalAlpha = 0.35;
    for (const sgn of [-1, 1]) p.stroke([[x + sgn * 60, y - 40], [x + sgn * 96, y - 60]], 8, "#cfe9ff");
    g.restore();
  }
  p.rot = null;
};

const drawDict = (p: Pen, x: number, y: number, prog: number, labelCol: string) => {
  const w = 120, h = 92;
  p.poly([[x - w, y - h], [x + w, y - h], [x + w, y + h], [x - w, y + h]], labelCol, 9);
  p.poly([[x - w + 12, y - h + 10], [x + w - 12, y - h + 10], [x + w - 12, y + h - 10], [x - w + 12, y + h - 10]], "#f6f0dd", 5);
  // fanned pages: the spread grows with prog
  const n = 5;
  for (let i = 0; i < n; i++) {
    const t = (i + 1) / n, a = -22 * prog * t;
    p.rot = [rad(a), x, y + h - 12];
    p.poly([[x - w + 16, y + h - 14], [x + w - 16, y + h - 14], [x + w - 20, y + h - 4], [x - w + 20, y + h - 4]], "#fffaf0", 3);
    p.rot = null;
  }
  for (const ly of [-40, -14, 12]) p.stroke([[x - 74, y + ly], [x + 74, y + ly]], 4, "#b9ad8f");
  p.stroke([[x - 74, y - 60], [x + 40, y - 60]], 7, "#ffffff");
};

const drawBoard = (p: Pen, x: number, y: number, rot: number, flip: number, snow = false) => {
  p.rot = [rad(rot), x, y];
  const th = 1 - 0.62 * Math.abs(flip);                      // the deck foreshortens as it flips edge-over-edge
  if (snow) {
    // a snowboard is one continuous cambered plank, boots strapped mid-deck: no trucks, no wheels, and the tips
    // curl up on BOTH ends, which is what separates it from the skate deck at card scale
    p.poly(smoothClosed([[x - 108, y + 2 * th], [x - 92, y - 15 * th], [x + 92, y - 15 * th], [x + 108, y + 2 * th],
      [x + 92, y + 15 * th], [x - 92, y + 15 * th]], 5), "#e9edf4", 8);
    p.stroke([[x - 78, y + 1], [x + 78, y + 1]], 6, "#4ea8de");
    for (const s of [-1, 1]) {
      p.poly([[x + s * 44 - 22, y - 14 * th], [x + s * 44 + 22, y - 14 * th], [x + s * 44 + 20, y + 12 * th], [x + s * 44 - 20, y + 12 * th]], "#2b2628", 5);
    }
  } else {
    for (const s of [-1, 1]) {
      p.ell(x + s * 46, y + 16 + 6 * th, 13 * (0.6 + 0.4 * th), 13, "#e6c227", 5);
    }
    p.poly(smoothClosed([[x - 84, y - 6 * th], [x - 60, y - 15 * th], [x + 60, y - 15 * th], [x + 84, y - 6 * th], [x + 60, y + 5 * th], [x - 60, y + 5 * th]], 5), "#7a4a24", 8);
    p.stroke([[x - 70, y - 4 * th], [x + 70, y - 4 * th]], 5, "#c8b49a");
  }
  if (Math.abs(flip) > 0.35) {
    const g = p.g; g.save(); g.globalAlpha = clamp01(Math.abs(flip));
    p.arc(x, y, 96, 26 * th + 8, flip > 0 ? 20 : 200, flip > 0 ? 160 : 340, 6, "#dff0ff");
    g.restore();
  }
  p.rot = null;
};

// ---------------- Act 2/3 held props (Rule A: everything portable is painted on the 2D hands) ----------------
/** map a canonical offset through a rotation about (cx, cy), the same transform Pen.P applies */
const rotPt = (cx: number, cy: number, dx: number, dy: number, deg: number): P2 => {
  const a = rad(deg), c = Math.cos(a), s = Math.sin(a);
  return [cx + dx * c - dy * s, cy + dx * s + dy * c];
};

// The rim is two strokes, not a fill: an ellipse filled would paint an opaque disc over the hero's chest and read as
// a steering WHEEL-shaped brick. Ink under-stroke + colour over-stroke = an outlined ring with the torso showing
// through the middle, and the fists get re-drawn on top of it so they stay in front of the rim.
const drawWheel = (p: Pen, x: number, y: number, turn: number) => {
  p.rot = [rad(turn), x, y];
  p.arc(x, y, 92, 88, 0, 360, 30, INK);
  p.arc(x, y, 92, 88, 0, 360, 18, "#2b2f38");
  for (const a of [-90, 28, 152]) {
    const q = rotPt(x, y, 0, 0, a);
    p.stroke([q, rotPt(x, y, Math.cos(rad(a)) * 86, Math.sin(rad(a)) * 82, a)], 13, "#2b2f38");
  }
  p.ell(x, y, 24, 24, "#3a4150", 7);
  p.rot = null;
};

// Canonical form: the body sits at (x, y) and the neck runs up-and-left 260 units, so the headstock lands near
// design x 100 for any body placed right of centre. `ang` is the whole guitar's tilt about the body.
const drawGuitar = (p: Pen, x: number, y: number, ang: number, wood: string) => {
  const q = (dx: number, dy: number) => rotPt(x, y, dx, dy, ang);
  p.rot = [rad(ang), x, y];
  p.line([q(-66, -40), q(-206, -116)], "#5b3a22", 22);
  p.line([q(-64, -40), q(-204, -116)], "#7d5233", 12);
  for (const t of [0.28, 0.52, 0.76]) p.stroke([q(-66 - 186 * t, -40 - 105 * t + 15), q(-66 - 186 * t, -40 - 105 * t - 15)], 4, "#cbb79a");
  p.poly(smoothClosed([q(-202, -104), q(-246, -132), q(-258, -110), q(-216, -84)], 4), wood, 7);
  for (const t of [0.15, 0.5, 0.85]) { const [px, py] = q(-216 - 30 * t, -122 - 18 * t); p.dot(px, py, 6, "#e8dcc0"); }
  // the bout: two overlapping ellipses give the waist without a bezier fight
  p.ell(x + 26, y + 26, 76, 62, wood, 11);
  p.ell(x - 6, y - 26, 58, 48, wood, 11);
  p.ell(x + 8, y + 2, 46, 42, mul(wood, 0.9), 0);
  p.ell(x + 6, y + 2, 26, 24, "#1a1216", 6);
  p.poly(smoothClosed([[x - 4, y + 44], [x + 40, y + 44], [x + 40, y + 58], [x - 4, y + 58]], 4), "#3a2a1e", 5);
  for (const t of [-12, 0, 12]) p.stroke([[x + 6 + t * 0.4, y - 46], [x + 22 + t, y + 50]], 3, "#e6edf6");
  p.rot = null;
};

const drawShovel = (p: Pen, top: P2, blade: P2) => {
  const a = Math.atan2(blade[1] - top[1], blade[0] - top[0]);
  p.line([top, blade], "#8b6a3e", 17);
  p.line([top, blade], "#a9855a", 9);
  p.dot(top[0], top[1], 13, "#6b4f2c");
  const dx = Math.cos(a), dy = Math.sin(a);
  p.poly(smoothClosed([[blade[0] - dy * 42, blade[1] + dx * 42], [blade[0] + dy * 42, blade[1] - dx * 42],
    [blade[0] + dx * 58 - dy * 30, blade[1] + dy * 58 + dx * 30], [blade[0] + dx * 66, blade[1] + dy * 66],
    [blade[0] + dx * 58 + dy * 30, blade[1] + dy * 58 - dx * 30]], 5), "#9aa3b2", 9);
};

// The downloaded glyph: a small dark card of code with a cyan glow, the same neon as the eyes. It is what the
// PROP_QUADS row for shot 24 projects, so it must be centred exactly where cast.ts says the fist catches it.
const drawGlyph = (p: Pen, x: number, y: number, a: number) => {
  const g = p.g;
  g.save(); g.globalAlpha = clamp01(a); g.shadowColor = CYAN; g.shadowBlur = 30;
  p.poly(smoothClosed([[x - 44, y - 58], [x + 44, y - 58], [x + 44, y + 58], [x - 44, y + 58]], 4), "#0c1622", 8);
  g.shadowBlur = 12;
  for (const [ly, w] of [[-34, 52], [-14, 66], [8, 40], [30, 58]] as [number, number][]) {
    p.stroke([[x - 30, y + ly], [x - 30 + w, y + ly]], 8, CYAN);
  }
  g.shadowBlur = 0;
  p.stroke([[x - 34, y - 46], [x - 34, y + 46]], 7, "#7ee8fa");
  p.stroke([[x + 34, y - 46], [x + 34, y + 46]], 7, "#7ee8fa");
  g.restore();
};

/** a fist with the index finger up: the accusation gesture, and the only hand shape that reads as "you" at 600 px */
const drawPointHand = (p: Pen, x: number, y: number, col: string) => {
  p.poly(smoothClosed([[x - 17, y - 6], [x + 17, y - 8], [x + 15, y + 20], [x - 15, y + 20]], 4), col, 7);
  p.poly(smoothClosed([[x - 6, y - 8], [x - 4, y - 46], [x + 8, y - 46], [x + 8, y - 6]], 4), col, 7);
};


const drawKneeBolts = (p: Pen, x: number, y: number, a: number) => {
  const g = p.g;
  g.save(); g.globalAlpha = a;
  for (const s of [-1, 1]) {
    const cx = x + s * 44;
    p.poly([[cx - 6, y - 44], [cx + 10, y - 8], [cx + 1, y - 6], [cx + 14, y + 34], [cx - 10, y - 6], [cx - 1, y - 8]], "#ffe14a", 5);
  }
  g.restore();
};

// ---------------- main entry ----------------
export const drawCharacter = (p: Pen, o: KidOpts) => {
  const k = KIT[o.role];
  const phase = clamp01(o.phase ?? 0);
  const bob = Math.sin(phase * Math.PI * 2) * 5;

  const boardP = clamp01(o.boardP ?? -1);
  const onBoard = o.boardP !== undefined;
  const wind = onBoard ? Math.sin(Math.PI * seg(0.0, 0.26, boardP)) : 0;   // crouch-out then straighten
  const air = onBoard ? Math.sin(Math.PI * seg(0.18, 0.9, boardP)) : 0;
  // one full edge-over-edge flip between the pop and the catch; a snowboard backflip is the SAME sine run twice,
  // because `flip` is a foreshortening factor, not an angle, so 4*PI is 720 degrees of deck.
  const flip = onBoard ? Math.sin(seg(0.2, 0.86, boardP) * Math.PI * (o.boardKind === "snow" ? 4 : 2)) * air : 0;
  const pain = clamp01(o.kneePainP ?? 0);
  const slump = clamp01(o.slumpP ?? 0);
  const reach = clamp01(o.reachP ?? 0);
  const up = clamp01(o.armsUpP ?? 0);
  const thumbs = clamp01(o.thumbsP ?? 0);
  const clap = clamp01(o.clapP ?? 0);
  const gest = clamp01(o.gestP ?? 0);
  const startle = clamp01(o.startleP ?? 0);

  // ---- Act 2/3 floats ----
  const snow = o.boardKind === "snow";
  const sit = clamp01(o.sitP ?? 0);
  const laugh = clamp01(o.laughP ?? 0);
  const wheel = clamp01(o.wheelP ?? 0);
  const lean = clamp01(o.leanP ?? 0);
  const handsUp = clamp01(o.handsUpP ?? 0);
  const pointUp = clamp01(o.pointUpP ?? 0);
  const split = clamp01(o.splitP ?? 0);
  const headPain = clamp01(o.headPainP ?? 0);
  const ears = clamp01(o.earsP ?? 0);
  const guitar = clamp01(o.guitarP ?? 0);
  const strum = clamp01(o.strumP ?? 0);
  const guitarSet = clamp01(o.guitarSetP ?? 0);
  const dig = clamp01(o.digP ?? 0);
  // The dig SCENE and the dig STROKE are different things. `digP` is a sawtooth that returns to exactly 0 once per
  // 26-frame cycle, so gating the prop on the value made the shovel vanish for a frame in the middle of every
  // stroke. The caller only ever passes it while he is digging, so its presence is the hold flag.
  const digging = o.digP !== undefined;
  const code = clamp01(o.codeP ?? 0);
  const walk = clamp01(o.walkP ?? 0);
  // a stride is a CYCLE, not a pose: walkP is 0..1 travel, so 3.2 steps fit inside it and the amplitude ramps in so
  // the figure is never half-way between standing and marching at the instant he starts.
  const strideT = walk * 3.2 * Math.PI * 2;
  const strideA = Math.min(1, walk * 6);

  // SIT_DROP is the default; cast.ts passes story.seatDrop(cushion, scale) per seated slot so the drawn hip lands
  // exactly on that set's cushion, which is what makes a seated card read as SEATED and not as a boy squatting.
  // The same function is what scripts/is_frame.mjs subtracts from his crown, so the two files cannot disagree.
  // digP is a SAWTOOTH (one stroke per 0..1 ramp), so the body lean has to be a hump that is zero at both ends:
  // folding by `dig` itself would snap him upright at the top of every stroke.
  const digH = Math.sin(dig * Math.PI);
  const fold = Math.max(pain * 0.75, slump, startle * 0.2, wind * 0.55, laugh * 0.62, digH * 0.3, lean * 0.45);
  const drop = fold * 58 + sit * (o.sitDrop ?? SIT_DROP);
  const tx = 300 + lerp(0, -14, pain) + lerp(0, 10, slump) + lean * 30;
  const hy = 235 + drop + bob - startle * 6;
  const hx = tx + (pain ? 6 : 0) - lean * 8;
  const headTilt = lean * 15 + split * 9 - pointUp * 11 - laugh * 7 + handsUp * 3;

  // ---- legs: vertical sticks at x = 265 / 335, hinging at the knee only when the body folds ----
  const legX = [tx - 35, tx + 35];
  const hipY = 575 + drop;
  // A seated front view foreshortens the thigh to almost nothing and leaves the knee OUT and slightly ABOVE the hip
  // (a real seat puts the knees level with the cushion), then the shin drops the whole rest of the way to the floor.
  // That is what makes a card anchored on the floor read as seated; pulling the knee UP toward the torso, as an
  // earlier pass did, put both shoes in mid-air under the bench.
  const bendK = clamp01(pain * 0.9 + wind * 0.7 + slump * 0.3 + laugh * 0.55 + dig * 0.25);
  const kneeBend = bendK * 34 + sit * 62 + strideA * 8;
  const footY = 945;
  const boardLift = air * 118;
  const knees: P2[] = [];
  const ankles: P2[] = [];
  for (let i = 0; i < 2; i++) {
    const s = i ? 1 : -1;
    const knee: P2 = [legX[i] + s * kneeBend, lerp(lerp(762, 716, bendK), hipY - 55, sit)];
    // the shoes ride the deck; lifting the ankles only 0.35x left the board drawn above the feet at the apex
    const swing = walk > 0.001 ? Math.sin(strideT + i * Math.PI) : 0;
    const ankle: P2 = [
      legX[i] + s * kneeBend * 0.35 + swing * 26 * strideA,
      lerp(footY - boardLift * 1.05, footY, sit) - Math.max(0, swing) * 30 * strideA,
    ];
    knees.push(knee); ankles.push(ankle);
    limb(p, [legX[i], hipY], knee, k.pants, 26);
    limb(p, knee, ankle, k.pantsDk, 23);
    const fy = ankle[1] + 7;
    p.poly(smoothClosed([[ankle[0] - 26, fy - 12], [ankle[0] + 26, fy - 12], [ankle[0] + 30, fy + 12], [ankle[0] - 28, fy + 12]], 4), k.shoes, 7);
  }
  if (pain > 0.1) for (const q of knees) p.ell(q[0], q[1], 22 * pain, 16 * pain, "#e8635a", 0);

  // ---- skateboard (2D, Rule A) under the feet ----
  if (onBoard) {
    const by = 968 - boardLift;
    const rot = lerp(0, -30, seg(0.18, 0.42, boardP)) + lerp(0, 26, seg(0.78, 1, boardP));
    drawBoard(p, tx + 6, by, rot, flip, snow);
    if (air > 0.15) {
      const g = p.g; g.save(); g.globalAlpha = clamp01(air);
      for (const s of [-1, 1]) p.stroke([[tx + s * 90, by + 26], [tx + s * 130, by + 62]], 7, "#cfe9ff");
      g.restore();
    }
  }

  // ---- torso: compact bean, shoulders 120 / hips 145, y 375..585 ----
  const torso = smoothClosed([
    [tx - 60, 375 + drop], [tx + 60, 375 + drop],
    [tx + 72, 490 + drop], [tx + 72, 585 + drop],
    [tx - 72, 585 + drop], [tx - 72, 490 + drop],
  ], 6);
  p.poly(torso, k.top, 11);
  // shaded side of the hoodie keeps the bean reading as a volume
  const g0 = p.g;
  g0.save(); g0.globalAlpha = 0.5;
  p.clip(torso, () => p.poly([[tx - 74, 373 + drop], [tx - 24, 373 + drop], [tx - 24, 587 + drop], [tx - 74, 587 + drop]], k.topDk, 0));
  g0.restore();

  if (k.openFront) {
    p.poly([[tx - 26, 378 + drop], [tx + 26, 378 + drop], [tx + 10, 585 + drop], [tx - 10, 585 + drop]], "#f7f2e6", 6);
    p.stroke([[tx - 26, 380 + drop], [tx - 6, 470 + drop]], 7, k.trim);
    p.stroke([[tx + 26, 380 + drop], [tx + 6, 470 + drop]], 7, k.trim);
    if (k.buttons) for (const by of [470, 510, 550]) p.dot(tx, by + drop, 6, k.trim);
  } else {
    // kangaroo pocket + drawstrings
    p.poly(smoothClosed([[tx - 52, 512 + drop], [tx + 52, 512 + drop], [tx + 56, 574 + drop], [tx - 56, 574 + drop]], 4), mul(k.top, 0.82), 7);
    if (o.role !== "grandmaster") {
      for (const s of [-1, 1]) {
        p.stroke([[tx + s * 14, 392 + drop], [tx + s * 20, 442 + drop]], 6, k.trim);
        p.dot(tx + s * 20, 448 + drop, 5, k.trim);
      }
      // hood collar gathered behind the neck
      p.poly(smoothClosed([[tx - 74, 392 + drop], [tx - 40, 372 + drop], [tx + 40, 372 + drop], [tx + 74, 392 + drop], [tx + 58, 424 + drop], [tx - 58, 424 + drop]], 5), k.topDk, 8);
    }
  }

  // ---- held-prop geometry, solved BEFORE the arms so every fist is pinned to the object it holds (Rule A) ----
  // Playing: the neck rises to screen-left at +16 degrees and the bout sits on the lower chest. Set down: the same
  // guitar rotates to -14 and drops 40 units across the lap, while the hands go back to the knees. One object, two
  // continuous parameters, nothing that can pop.
  const gAng = lerp(16, -14, guitarSet);
  const gPos: P2 = [tx + 46, 532 + drop * 0.85 + guitarSet * 40];
  const gFret = rotPt(gPos[0], gPos[1], -150, -84, gAng);
  const gStrum = rotPt(gPos[0], gPos[1], 16, -8, gAng);
  const digSw = Math.sin(dig * Math.PI * 2);
  const shTop: P2 = [tx - 128 - digSw * 20, hipY - 152 - digSw * 26];
  const shBlade: P2 = [tx + 118 + digSw * 34, 902 + digSw * 30];
  const shMid: P2 = [(shTop[0] + shBlade[0]) / 2, (shTop[1] + shBlade[1]) / 2];

  // ---- arms ----
  const shL: P2 = [tx - 58, 396 + drop], shR: P2 = [tx + 58, 396 + drop];
  let haL: P2 = [tx - 92, 545 + drop * 0.4];
  let haR: P2 = [tx + 92, 545 + drop * 0.4];
  let elL: P2 = [tx - 80, 470 + drop * 0.6];
  let elR: P2 = [tx + 80, 470 + drop * 0.6];
  let fistR = false;
  let openL = false, openR = false, pointHand = false;

  if (clap > 0.01) {
    const gap = lerp(74, 8, Math.abs(Math.sin(clap * Math.PI * 3)));
    haL = [tx - gap, 470 + drop * 0.4]; haR = [tx + gap, 470 + drop * 0.4];
    elL = [tx - 96, 500 + drop * 0.5]; elR = [tx + 96, 500 + drop * 0.5];
  } else if (up > 0.01) {
    haL = [tx - 150, 300 + drop]; haR = [tx + 150, 300 + drop];
    elL = [tx - 118, 400 + drop * 0.7]; elR = [tx + 118, 400 + drop * 0.7];
  } else if (thumbs > 0.01) {
    haL = [tx - 74, 452 + drop]; haR = [tx + 74, 452 + drop];
    elL = [tx - 92, 520 + drop * 0.6]; elR = [tx + 92, 520 + drop * 0.6];
  } else if (pain > 0.01) {
    // both fists clamp the knees they just ruined
    haL = [knees[0][0] + 16, knees[0][1] - 4]; haR = [knees[1][0] - 16, knees[1][1] - 4];
    elL = [tx - 96, 620]; elR = [tx + 96, 620];
  } else if (startle > 0.01) {
    haL = [tx - 140, 356 + drop]; haR = [tx + 140, 356 + drop];
    elL = [tx - 104, 430 + drop]; elR = [tx + 104, 430 + drop];
  } else if (gest > 0.01) {
    haR = [lerp(tx + 92, tx - 30, gest), lerp(545, 640, gest) + drop * 0.3];
    elR = [tx + 86, 520 + drop * 0.5];
    haL = [tx - 88, 540 + drop * 0.4];
  } else if (o.cubeP !== undefined) {
    const cp = clamp01(o.cubeP);
    const slam = seg(0.86, 1.0, cp);
    // the solve holds the cube at chest height, the slam drops the hands to design y ~512 = 0.92 m world. That is
    // the tabletop: the 3D solved cube takes over at 1.04 m and settles on the felt, so the two drawings hand over
    // within a few centimetres instead of the 2D hands punching down through the wood.
    const cyh = lerp(470, 512, slam) + drop * 0.4;
    haL = [tx - 58 * (1 - slam * 0.4), cyh]; haR = [tx + 58 * (1 - slam * 0.4), cyh + slam * 8];
    elL = [tx - 84, 500 + drop * 0.5]; elR = [tx + 84, 500 + drop * 0.5];
    if (slam > 0.55) {
      haL = [tx - 74, cyh - 4]; haR = [tx + 70, cyh + 10];
      elL = [tx - 92, 516 + drop]; elR = [tx + 90, 520 + drop];
    }
  } else if (o.dictP !== undefined) {
    const dp = clamp01(o.dictP);
    haL = [tx - 96 - dp * 6, 500 + drop * 0.4]; haR = [tx + 96 + dp * 6, 500 + drop * 0.4];
    elL = [tx - 96, 540 + drop * 0.5]; elR = [tx + 96, 540 + drop * 0.5];
  } else if (o.phoneP !== undefined) {
    const pp = clamp01(o.phoneP);
    haR = [lerp(tx + 96, tx + 152, pp), lerp(548, 430 + drop * 0.4, pp)];
    elR = [lerp(tx + 84, tx + 120, pp), lerp(520, 500, pp)];
    haL = [tx - 90, 545 + drop * 0.4];
  } else if (onBoard) {
    // balance out wide while riding
    const bal = Math.sin(boardP * Math.PI * 2) * 16;
    haL = [tx - 152, 400 + drop * 0.5 - bal]; haR = [tx + 152, 420 + drop * 0.5 + bal];
    elL = [tx - 112, 452 + drop * 0.6]; elR = [tx + 112, 462 + drop * 0.6];
  } else if (reach > 0.01) {
    haR = [lerp(tx + 92, HERO_FIST[0], reach), lerp(545, HERO_FIST[1], reach)];
    elR = [lerp(tx + 84, tx + 128, reach), lerp(520, 528, reach)];
    fistR = reach > 0.55;
  } else if (slump > 0.01) {
    haL = [tx - 78, 620 + drop]; haR = [tx + 78, 620 + drop];
    elL = [tx - 74, 520 + drop]; elR = [tx + 74, 520 + drop];

  // ---- ACT 2/3 ----
  } else if (guitar > 0.01) {
    // the strum is 18 units of travel over the soundhole, and the elbow only half follows it: a wrist, not a shove
    const so = Math.sin(strum * Math.PI * 2) * 18;
    haL = gFret; haR = [gStrum[0] - so * 0.2, gStrum[1] + so];
    elL = [tx - 118, 470 + drop * 0.85]; elR = [tx + 104, 500 + drop * 0.85 + so * 0.45];
    fistR = true;
  } else if (digging) {
    haL = [shTop[0] + 12, shTop[1] + 26]; haR = [shMid[0] + 14, shMid[1] - 10];
    elL = [tx - 126, shTop[1] + 118]; elR = [tx + 110, shMid[1] + 64];
    fistR = true;
  } else if (code > 0.01) {
    haR = [lerp(tx + 92, HERO_CODE[0], code), lerp(545 + drop * 0.4, HERO_CODE[1], code)];
    elR = [lerp(tx + 84, tx + 122, code), lerp(520, 536, code)];
    haL = [tx - 96, 560 + drop * 0.4];
    fistR = code > 0.45;
  } else if (ears > 0.01) {
    // palms FLAT over the ears, so the hand is drawn open and the ink rim of the palm reads as the seal
    haL = [hx - 118, hy + 10]; haR = [hx + 118, hy + 10];
    elL = [tx - 158, hy + 108]; elR = [tx + 158, hy + 108];
    openL = openR = true;
  } else if (headPain > 0.01) {
    haL = [hx - 104, hy - 34]; haR = [hx + 104, hy - 34];
    elL = [tx - 162, hy + 62]; elR = [tx + 162, hy + 62];
    openL = openR = true;
  } else if (wheel > 0.01) {
    // AFTER headPain, not before: shot 13 has him driving AND clutching his skull, and the rim keeps drawing on
    // `wheelP` even while the hands have left it. Ranked any earlier and the despair beat could never fire.
    // The rim's centre is hipY - 100: at the cockpit's seat drop that is design 805 = world 0.62 m, exactly
    // HIGHWAY.wheel, so the drawn wheel and the drawn fists agree at every camera angle.
    const wy = hipY - 100;
    haL = [tx - 84, wy + 4]; haR = [tx + 84, wy + 4];
    elL = [tx - 108, wy + 76]; elR = [tx + 108, wy + 76];
    fistR = true;
  } else if (split > 0.01) {
    haR = [lerp(tx + 92, hx + 104, split), lerp(545 + drop * 0.4, hy - 30, split)];
    elR = [tx + 152, hy + 66];
    haL = [tx - 90, hipY + 96]; elL = [tx - 106, hipY + 22];
    fistR = split > 0.5;
  } else if (handsUp > 0.01) {
    haL = [tx - 108, 462 + drop * 0.6]; haR = [tx + 108, 462 + drop * 0.6];
    elL = [tx - 128, 556 + drop * 0.6]; elR = [tx + 128, 556 + drop * 0.6];
    openL = openR = true;
  } else if (pointUp > 0.01) {
    haR = [lerp(tx + 92, tx + 138, pointUp), lerp(545 + drop * 0.4, 250, pointUp)];
    elR = [lerp(tx + 84, tx + 104, pointUp), lerp(520, 372, pointUp)];
    haL = [tx - 94, 552 + drop * 0.4];
    pointHand = pointUp > 0.5;
  } else if (laugh > 0.01) {
    // doubled over: one arm across the gut, the other hanging loose with the shoulder
    haL = [tx - 40, hipY - 74]; haR = [tx + 96, 600 + drop * 0.6];
    elL = [tx - 108, hipY - 40]; elR = [tx + 112, 660 + drop * 0.5];
  }
  if (o.role === "grandmaster" && startle < 0.01 && o.expr !== "panicShock") {
    // hands rest on the table edge when idle
    haL = [tx - 66, 610 + drop * 0.4]; haR = [tx + 66, 610 + drop * 0.4];
  }

  // back arm (screen left) first, then the head, then the reaching arm
  drawArm(p, shL, elL, haL, k, HEAD);
  handFor(p, haL, o, clap, thumbs, false, openL, false);

  // ---- head ----
  // the skull hinges at the neck, not at its own centre: lean/split/point all cant it, and rotating about the neck
  // keeps the jaw connected to the collar instead of floating the whole sphere off the shoulders.
  p.rot = [rad(headTilt), hx, hy + 130];
  p.ell(hx, hy, HEAD_R, HEAD_R, HEAD, 12);
  const g1 = p.g;
  g1.save(); g1.globalAlpha = 0.35;
  p.clip([[hx - HEAD_R, hy], [hx - HEAD_R * 0.6, hy - HEAD_R], [hx + HEAD_R * 0.2, hy - HEAD_R], [hx + HEAD_R * 0.5, hy + HEAD_R * 0.4], [hx - HEAD_R * 0.4, hy + HEAD_R]].map((q) => [q[0], q[1]] as P2), () => {
    p.ell(hx - 40, hy + 20, HEAD_R, HEAD_R, HEAD_SH, 0);
  });
  g1.restore();
  drawFace(p, hx, hy, o);
  drawHeadgear(p, hx, hy, k, o);
  if (o.blindfold) drawBlindfold(p, hx, hy + 8, clamp01(o.blindUpP ?? 0));
  p.rot = null;

  // ---- front arm + held props on top of the head layer order ----
  drawArm(p, shR, elR, haR, k, HEAD);
  handFor(p, haR, o, clap, thumbs, fistR, openR, pointHand);

  // ---- Act 2/3 held props, drawn over the arms so the object is IN the hands, not behind them ----
  if (wheel > 0.01) {
    const wy = hipY - 100;
    drawWheel(p, tx, wy, Math.sin(phase * Math.PI * 2) * 4 - lean * 40);
    // the rim crosses both forearms, so the fists that grip it are painted a second time, on top of the ring
    drawFist(p, haL[0], haL[1], HEAD); drawFist(p, haR[0], haR[1], HEAD);
  }
  if (guitar + guitarSet > 0.01) drawGuitar(p, gPos[0], gPos[1], gAng, "#8a5a2b");
  if (digging) drawShovel(p, shTop, shBlade);
  // the glyph lands ON the projected contact point story.ts PROP_QUADS[24] declares, not near it
  if (code > 0.01) drawGlyph(p, haR[0], haR[1], code);

  if (o.phoneP !== undefined && clamp01(o.phoneP) > 0.02) drawPhone(p, haR[0] + 30, haR[1] - 46, clamp01(o.phoneP));
  if (o.cubeP !== undefined) {
    const cp = clamp01(o.cubeP);
    const solved = cp >= 0.999;
    const cxp = (haL[0] + haR[0]) / 2, cyp = (haL[1] + haR[1]) / 2 - 26;
    drawCube(p, cxp, cyp, cp, solved);
  }
  if (o.dictP !== undefined && clamp01(o.dictP) > 0.02) drawDict(p, (haL[0] + haR[0]) / 2, haL[1] - 16, clamp01(o.dictP), k.topDk);
  if (pain > 0.15) for (const q of knees) drawKneeBolts(p, q[0], q[1], clamp01(pain));
  if (o.starP !== undefined && clamp01(o.starP) > 0.02) {
    const a = clamp01(o.starP);
    for (const [sx, sy] of [[tx - 76, 400 + drop], [tx + 78, 396 + drop], [tx - 120, 350], [tx + 124, 344]]) {
      star4(p, sx, sy, 16 + 10 * a, "#ffd23f", a);
    }
  }
};

const handFor = (p: Pen, h: P2, o: KidOpts, clap: number, thumbs: number, fist: boolean, open = false, point = false) => {
  if (point) { drawPointHand(p, h[0], h[1], HEAD); return; }
  if (fist) { drawFist(p, h[0], h[1], HEAD); return; }
  if (open) { drawOpenHand(p, h[0], h[1], HEAD, 19); return; }
  if (thumbs > 0.05) { drawThumbUp(p, h[0], h[1] - 4, HEAD, thumbs); return; }
  if (clap > 0.05) { drawOpenHand(p, h[0], h[1], HEAD, 17); return; }
  if (o.cubeP !== undefined || o.dictP !== undefined || o.phoneP !== undefined) { drawFist(p, h[0], h[1], HEAD, 17); return; }
  drawFist(p, h[0], h[1], HEAD, 17);
};

const star4 = (p: Pen, x: number, y: number, r: number, col: string, a = 1) => {
  const g = p.g;
  g.save(); g.globalAlpha = a; g.shadowColor = col; g.shadowBlur = 18;
  p.poly([[x, y - r], [x + r * 0.28, y - r * 0.28], [x + r, y], [x + r * 0.28, y + r * 0.28], [x, y + r], [x - r * 0.28, y + r * 0.28], [x - r, y], [x - r * 0.28, y - r * 0.28]], col, 0);
  g.restore();
};

// ---------------- 2D effect cards (unlit, drawn in a normalised 600 x 600 box) ----------------
export type FxKind = "spark" | "burst" | "dust" | "stars" | "rays" | "glow" | "blob" | "cash";

export const fxBlob = (p: Pen) => {
  const g = p.g;
  g.fillStyle = "#ffffff"; g.fillRect(0, 0, 600, 600);
  const gr = g.createRadialGradient(300, 300, 0, 300, 300, 300);
  gr.addColorStop(0, "#3a2e26"); gr.addColorStop(0.35, "#6b584b"); gr.addColorStop(0.72, "#b8aca0"); gr.addColorStop(1, "#ffffff");
  g.fillStyle = gr; g.fillRect(0, 0, 600, 600);
};

// One language speech bubble, drawn in a 660 x 240 box (cast.ts sizes the card 0.55 x 0.20 m). This replaces the
// v1 in-world placards: the line is spoken, not posted, so it gets a tail toward the hero's side of the frame.
export const drawBubble = (p: Pen, text: string) => {
  const g = p.g;
  const body = smoothClosed([[24, 16], [636, 16], [636, 176], [470, 176], [500, 226], [420, 176], [24, 176]], 5);
  p.poly(body, HEAD, 10);
  g.textAlign = "center"; g.textBaseline = "middle";
  let size = 78;
  for (; size > 26; size--) {
    g.font = `700 ${size}px "Segoe UI", "Yu Gothic", Meiryo, "Helvetica Neue", Arial, sans-serif`;
    if (g.measureText(text).width <= 560) break;
  }
  g.fillStyle = "#2b2433";
  g.fillText(text, 330, 96);
};

// One buried friend's glove, waving out of a snow mound (shot 21). A card cannot do this job: to get the mitt above
// the mound its own crown would have to clear the snow too, so the arm that reads is a 2D FX card, not a body.
// Drawn in the same normalised 600 x 600 box the other effect cards use, wrist at the bottom, waving about it.
export const drawGlove = (p: Pen, u: number) => {
  const a = Math.sin(clamp01(u) * Math.PI * 2) * 16;
  p.rot = [rad(a), 300, 470];
  p.line([[300, 470], [300, 300]], "#4ea8de", 74);
  p.poly(smoothClosed([[252, 320], [348, 320], [356, 214], [300, 186], [244, 214]], 5), "#f4f7fb", 9);
  p.stroke([[258, 300], [344, 300]], 8, "#2f7cb0");
  p.ell(352, 250, 26, 34, "#f4f7fb", 8);   // the thumb
  p.rot = null;
};

export const drawFx = (p: Pen, kind: FxKind, u: number, col = "#ffd23f") => {
  const t = clamp01(u);
  const g = p.g;
  const C = 300;
  if (kind === "blob") { fxBlob(p); return; }
  if (kind === "glow") {
    g.save(); g.globalAlpha = 1 - t;
    p.ell(C, C, 60 + 220 * t, 60 + 220 * t, null, 0);
    const gr = g.createRadialGradient(C, C, 20, C, C, 60 + 220 * t);
    gr.addColorStop(0, col); gr.addColorStop(0.6, col); gr.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = gr; g.beginPath(); g.arc(C, C, 60 + 220 * t, 0, Math.PI * 2); g.fill();
    g.restore();
    return;
  }
  if (kind === "dust") {
    g.save(); g.globalAlpha = (1 - t) * 0.85;
    const rBase = lerp(30, 210, Math.sqrt(t));
    for (const [ox, oy, sc] of [[0, 0, 1], [-70, 26, 0.8], [74, 14, 0.85], [-130, 44, 0.6], [136, 36, 0.7], [10, -60, 0.62]]) {
      p.ell(C + ox, C + oy, rBase * sc, rBase * sc * 0.78, "#e2d8cb", 0);
      p.arc(C + ox, C + oy, rBase * sc, rBase * sc * 0.78, 180, 360, 4, "#b4a694");
    }
    g.restore();
    return;
  }
  if (kind === "stars") {
    g.save();
    for (let i = 0; i < 7; i++) {
      const a = rad(i * 51.4 + t * 40), r = lerp(60, 240, t);
      star4(p, C + Math.cos(a) * r, C + Math.sin(a) * r * 0.8, lerp(34, 10, t), i % 2 ? "#ffe98a" : col, 1 - t);
    }
    g.restore();
    return;
  }
  if (kind === "rays") {
    g.save(); g.globalAlpha = (1 - t) * 0.8;
    for (let i = 0; i < 12; i++) {
      const a = rad(i * 30 + t * 22), r0 = lerp(40, 120, t), r1 = lerp(140, 290, t);
      p.stroke([[C + Math.cos(a) * r0, C + Math.sin(a) * r0], [C + Math.cos(a) * r1, C + Math.sin(a) * r1]], lerp(14, 3, t), col);
    }
    g.restore();
    return;
  }
  if (kind === "cash") {
    g.save(); g.globalAlpha = 1 - t * 0.6;
    for (let i = 0; i < 9; i++) {
      const a = rad(i * 40 + 20 + t * 26), r = lerp(40, 230, t);
      const x = C + Math.cos(a) * r, y = C + Math.sin(a) * r * 0.72 - 40 * t;
      p.rot = [rad(a * 2 + t * 120), x, y];
      p.poly([[x - 26, y - 12], [x + 26, y - 12], [x + 26, y + 12], [x - 26, y + 12]], "#5f9e6b", 4);
      p.stroke([[x - 14, y], [x + 14, y]], 4, "#dfe9d6");
      p.rot = null;
    }
    g.restore();
    return;
  }
  // "spark" and "burst": radial shards; burst adds a white core flash
  const n = kind === "burst" ? 14 : 11;
  g.save(); g.globalAlpha = 1 - t * 0.85;
  if (kind === "burst") {
    g.save(); g.globalAlpha = (1 - t) * 0.9;
    p.poly(Array.from({ length: 24 }, (_, i) => {
      const a = (i * Math.PI) / 12, r = i % 2 ? lerp(40, 120, t) : lerp(90, 210, t);
      return [C + Math.cos(a) * r, C + Math.sin(a) * r] as P2;
    }), "#fffbe6", 8);
    g.restore();
  }
  for (let i = 0; i < n; i++) {
    const a = rad(i * (360 / n) + t * 26);
    const r0 = lerp(12, 70, t), r1 = lerp(60, 250, Math.sqrt(t));
    p.stroke([[C + Math.cos(a) * r0, C + Math.sin(a) * r0], [C + Math.cos(a) * r1, C + Math.sin(a) * r1]], lerp(11, 3, t), i % 2 ? "#ffcc33" : "#ff5522");
  }
  g.restore();
};
