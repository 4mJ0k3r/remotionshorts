// 2D cartoon characters for HotelLiftShort in 600x1000 design space (SKILL.md Section 2):
// SU = 0.00216, PIV = 975 at feet, soles at y = 952.
// Warm cream-white head (#fdfaf2) with HEAD_R = 145 at (300, 235), #351f22 ink outlines.
// Compact bean torso width ~135 (y = 375..585).
// Straight parallel vertical legs at x = 265 and 335.
// Solid #351f22 oval pupils with ZERO white anime shine dots.
//
// Characters:
// 1. 'engineer' (George Pullman): tan/brass bowler cap (#8c5a2b), brown work vest (#6b4226),
//    cream shirt, red tie, brass gauge. Continuous crankP (0..1) moves fist (168..132, 585).
// 2. 'guest' (Wealthy Hotel Guest): tall Victorian top hat (#2b2628), burgundy dress coat (#7a2032),
//    cream waistcoat with gold buttons. Held props: teaP (teacup), billP ("STILL OPEN / 0 CRACKS" card).
import { Pen, INK } from "./pen";

export { Pen, INK };
type P2 = [number, number];

export const HEAD = "#fdfaf2";
export const HEAD_SH = "#ece1cd";
export const HEAD_R = 145;
export const WHITE = "#ffffff";
export const DARK_INK = INK;

export type Expr = "confidentSmile" | "panicShock" | "strainGrin";

export type CharOpts = {
  role: "engineer" | "guest";
  expr: Expr;
  gaze?: number;    // -1..1
  gazeY?: number;   // -1..1
  crankP?: number;  // 0..1 (engineer)
  whistleP?: number;// 0..1 (engineer)
  teaP?: number;    // 0..1 (guest)
  billP?: number;   // 0..1 (guest)
};

const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const rad = (d: number) => (d * Math.PI) / 180;

/** Catmull-Rom closed polygon for organic bean silhouettes */
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

// ---------------- FACES (Zero white anime shine dots!) ----------------
const drawFace = (p: Pen, hx: number, hy: number, expr: Expr, gaze = 0, gazeY = 0) => {
  const S = [-1, 1];
  const dx = 48, ey = hy + 8, my = hy + 68;
  const px = clamp(gaze, -1, 1) * 9, py = clamp(gazeY, -1, 1) * 8;

  if (expr === "strainGrin") {
    // Heavy V-angled eyebrows, squinting > < eyes, wide clenched-tooth grin
    for (const s of S) {
      const ex = hx + s * dx;
      // > < chevron eyes pointing toward center
      p.stroke([[ex - s * 20, ey - 18], [ex + s * 16, ey], [ex - s * 20, ey + 18]], 11);
      // Heavy V-angled brow tilting steeply down toward nose
      p.stroke([[ex - s * 34, ey - 46], [ex + s * 18, ey - 28]], 12);
    }
    // Cheeks
    p.ell(hx - 84, my - 6, 22, 12, "#f4b8a8", 0);
    p.ell(hx + 84, my - 6, 22, 12, "#f4b8a8", 0);
    // Wide clenched tooth grin
    const x0 = hx - 62, x1 = hx + 62, y0 = my - 22, y1 = my + 24;
    p.poly([[x0, y0], [x1, y0], [x1 + 6, (y0 + y1) / 2], [x1, y1], [x0, y1], [x0 - 6, (y0 + y1) / 2]], WHITE, 8);
    p.stroke([[x0 + 4, my + 1], [x1 - 4, my + 1]], 5);
    for (const t of [-38, -14, 14, 38]) {
      p.stroke([[hx + t, y0 + 3], [hx + t, y1 - 3]], 4);
    }
    return;
  }

  if (expr === "panicShock") {
    // Wide solid dark pupils, high arched brows, open oval mouth, blue sweat drop on temple
    for (const s of S) {
      const ex = hx + s * dx;
      // High arched brows floating high above eyes
      p.arc(ex, ey - 48, 24, 14, 195, 345, 10);
      // Wide circular/oval dark pupil (ZERO shine dots)
      p.ell(ex + px, ey + py, 20, 24, INK, 0);
    }
    // Blue sweat drop on left temple
    p.poly([[hx - 105, ey - 20], [hx - 92, ey - 3], [hx - 118, ey - 3]], "#5ab4f8", 3);
    p.ell(hx - 105, ey + 2, 14, 14, "#5ab4f8", 3);

    // Open shocked oval mouth
    const m = smoothClosed([[hx - 28, my - 16], [hx + 28, my - 16], [hx + 34, my + 24], [hx - 34, my + 24]], 5);
    p.poly(m, "#4e1a22", 8);
    // Dark throat interior
    p.ell(hx, my + 12, 18, 12, "#d04d44", 0);
    return;
  }

  // confidentSmile (default)
  // Solid dark oval pupils, raised eyebrows, cheerful toothed grin
  for (const s of S) {
    const ex = hx + s * dx;
    // Cheerful arched floating eyebrows
    p.arc(ex, ey - 42, 22, 12, 200, 340, 10);
    // Solid dark oval pupils (ZERO shine dots!)
    p.ell(ex + px, ey + py, 16, 22, INK, 0);
  }
  // Soft rosy cheeks
  p.ell(hx - 82, my - 6, 22, 12, "#f4bcae", 0);
  p.ell(hx + 82, my - 6, 22, 12, "#f4bcae", 0);

  // Cheerful toothed smile
  const m = smoothClosed([
    [hx - 48, my - 10], [hx, my - 6], [hx + 48, my - 10],
    [hx + 32, my + 26], [hx, my + 34], [hx - 32, my + 26]
  ], 5);
  p.poly(m, "#521e24", 8);
  // White upper teeth strip
  p.poly([[hx - 44, my - 9], [hx + 44, my - 9], [hx + 38, my + 6], [hx - 38, my + 6]], WHITE, 0);
  p.stroke([[hx - 38, my + 6], [hx + 38, my + 6]], 4);
  // Red tongue
  p.ell(hx, my + 28, 24, 12, "#dc564e", 0);
};

// ---------------- HEADGEAR (Must rise clearly above HEAD_R = 145 contour, y < 85) ----------------
const drawEngineerCap = (p: Pen, hx: number, hy: number) => {
  // Tan/brass engineer bowler / hard cap (#8c5a2b), brim at y ~ 118, crown rising above y < 80 to y ~ 35
  const brown = "#8c5a2b", darkBrown = "#543314", brass = "#e2b242";

  // Dome crown
  p.poly(smoothClosed([
    [hx - 110, hy - 95], [hx - 80, hy - 170], [hx, hy - 195],
    [hx + 80, hy - 170], [hx + 110, hy - 95]
  ], 6), brown, 9);

  // Dark leather band
  p.poly([[hx - 114, hy - 85], [hx + 114, hy - 85], [hx + 112, hy - 110], [hx - 112, hy - 110]], darkBrown, 6);

  // Brass engineer shield badge on front
  p.poly([[hx - 16, hy - 135], [hx + 16, hy - 135], [hx + 14, hy - 110], [hx, hy - 98], [hx - 14, hy - 110]], brass, 5);
  p.dot(hx, hy - 120, 4, darkBrown);

  // Sturdy curved brim extending past head width
  p.poly(smoothClosed([
    [hx - 152, hy - 82], [hx, hy - 74], [hx + 152, hy - 82],
    [hx + 148, hy - 96], [hx, hy - 90], [hx - 148, hy - 96]
  ], 6), brown, 9);
};

const drawVictorianTopHat = (p: Pen, hx: number, hy: number) => {
  // Tall dark-charcoal Victorian top hat (#2b2628), brim at y ~ 118, top rising high above y < 80 to y ~ 10!
  const charcoal = "#2b2628", darkShade = "#1d191b", burgundy = "#7a2032";

  // Tall cylinder crown
  p.poly([
    [hx - 92, hy - 95], [hx - 86, hy - 225],
    [hx + 86, hy - 225], [hx + 92, hy - 95]
  ], charcoal, 10);

  // Crown top oval lid
  p.ell(hx, hy - 225, 86, 18, charcoal, 10);
  p.ell(hx, hy - 225, 78, 14, "#3d3639", 0);

  // Silk ribbon band (Burgundy)
  p.poly([[hx - 93, hy - 95], [hx + 93, hy - 95], [hx + 91, hy - 128], [hx - 91, hy - 128]], burgundy, 6);
  // Gold ribbon buckle
  p.poly([[hx - 18, hy - 126], [hx + 18, hy - 126], [hx + 18, hy - 97], [hx - 18, hy - 97]], "#e2b242", 4);
  p.poly([[hx - 8, hy - 120], [hx + 8, hy - 120], [hx + 8, hy - 103], [hx - 8, hy - 103]], burgundy, 0);

  // Curved wide Victorian brim
  p.poly(smoothClosed([
    [hx - 156, hy - 86], [hx, hy - 76], [hx + 156, hy - 86],
    [hx + 150, hy - 100], [hx, hy - 92], [hx - 150, hy - 100]
  ], 6), charcoal, 10);
};

// ---------------- CHARACTER DRAWING ENTRY ----------------
export function drawCharacter(ctx: CanvasRenderingContext2D, opts: CharOpts) {
  const p = new Pen(ctx);
  const hx = 300, hy = 235; // Head center (SKILL.md Section 2)

  // 1. LEGS (Straight parallel vertical sticks at x = 265 and 335, soles at y = 952)
  const legX1 = 265, legX2 = 335;
  const legTopY = 575, legBottomY = 945;
  const legColor = opts.role === "engineer" ? "#4a3c31" : "#241f23";

  // Left leg
  p.stroke([[legX1, legTopY], [legX1, legBottomY]], 22, legColor);
  // Right leg
  p.stroke([[legX2, legTopY], [legX2, legBottomY]], 22, legColor);

  // FEET (Small dark rounded pills width = 52, height = 24 at y = 952)
  p.poly(smoothClosed([[legX1 - 22, 940], [legX1 + 34, 940], [legX1 + 36, 958], [legX1 - 22, 958]], 4), INK, 6);
  p.poly(smoothClosed([[legX2 - 22, 940], [legX2 + 34, 940], [legX2 + 36, 958], [legX2 - 22, 958]], 4), INK, 6);

  // 2. TORSO (Compact bean shape width ~ 135 from y = 375 to 585)
  // Lean torso slightly if cranking
  const crank = clamp(opts.crankP ?? 0, 0, 1);
  const leanOffset = opts.role === "engineer" ? lerp(-4, 12, crank) : 0;

  const tx = hx + leanOffset;
  const torsoShape = smoothClosed([
    [tx - 58, 380], // left shoulder
    [tx + 58, 380], // right shoulder
    [tx + 72, 490], // right waist
    [tx + 70, 585], // right hip
    [tx - 70, 585], // left hip
    [tx - 72, 490], // left waist
  ], 6);

  if (opts.role === "engineer") {
    // Cream shirt base
    p.poly(torsoShape, "#f2ebe0", 11);

    // Brown leather work vest (#6b4226) over shirt
    const vestShape = smoothClosed([
      [tx - 56, 384], [tx - 24, 388], [tx - 16, 470], [tx - 40, 582], [tx - 68, 582], [tx - 70, 485]
    ], 5);
    p.poly(vestShape, "#6b4226", 7);
    const vestRight = smoothClosed([
      [tx + 56, 384], [tx + 24, 388], [tx + 16, 470], [tx + 40, 582], [tx + 68, 582], [tx + 70, 485]
    ], 5);
    p.poly(vestRight, "#6b4226", 7);

    // Red neckband / necktie
    p.poly([[tx - 14, 376], [tx + 14, 376], [tx + 10, 430], [tx, 445], [tx - 10, 430]], "#b22b27", 5);

    // Brass pocket pressure gauge on chest
    p.ell(tx + 40, 460, 16, 16, "#e2b242", 5);
    p.ell(tx + 40, 460, 12, 12, WHITE, 2);
    // Gauge needle
    p.stroke([[tx + 40, 460], [tx + 46, 454]], 3, INK);

    // Gold vest buttons
    for (const by of [460, 495, 530]) {
      p.dot(tx - 20, by, 4, "#e2b242");
    }
  } else {
    // Guest: Burgundy dress coat (#7a2032) over cream waistcoat with gold buttons & dark bow tie
    // Waistcoat base
    p.poly(torsoShape, "#ede4d0", 11);

    // Burgundy dress coat lapels
    const coatLeft = smoothClosed([
      [tx - 60, 382], [tx - 22, 388], [tx - 18, 480], [tx - 38, 584], [tx - 72, 584], [tx - 72, 480]
    ], 5);
    p.poly(coatLeft, "#7a2032", 8);
    const coatRight = smoothClosed([
      [tx + 60, 382], [tx + 22, 388], [tx + 18, 480], [tx + 38, 584], [tx + 72, 584], [tx + 72, 480]
    ], 5);
    p.poly(coatRight, "#7a2032", 8);

    // Dark silk bow tie
    p.poly([[tx, 388], [tx - 26, 376], [tx - 24, 400], [tx, 390], [tx + 24, 400], [tx + 26, 376]], "#22191c", 5);
    p.dot(tx, 389, 5, "#22191c");

    // Gold waistcoat buttons
    for (const by of [450, 485, 520]) {
      p.dot(tx, by, 4, "#e2b242");
    }
  }

  // 3. ARMS & HAND ACTIONS
  if (opts.role === "engineer") {
    // Engineer's Screen-Left hand (his right arm) cranks the 3D lever!
    // As crankP goes 0 -> 1, fist moves from dx = 168 to dx = 132 (dy = 585).
    const fistX = lerp(168, 132, crank);
    const fistY = 585;

    // Right arm (screen left): reaches down and forward to fist
    const shoulderL: P2 = [tx - 56, 395];
    const elbowL: P2 = [lerp(tx - 110, tx - 130, crank), lerp(480, 490, crank)];
    p.line([shoulderL, elbowL], "#f2ebe0", 22); // rolled-up sleeve upper arm
    p.line([elbowL, [fistX, fistY]], "#fdfaf2", 18); // bare forearm

    // Closed fist gripping the wrench knob (designed at exact dx, dy)
    p.poly(smoothClosed([
      [fistX - 16, fistY - 14], [fistX + 16, fistY - 14],
      [fistX + 18, fistY + 16], [fistX - 16, fistY + 16]
    ], 4), "#fdfaf2", 6);
    // Knuckles
    p.stroke([[fistX - 12, fistY - 2], [fistX + 12, fistY - 2]], 4, INK);

    // Left arm (screen right): resting on hip or holding clipboard
    const whistle = clamp(opts.whistleP ?? 0, 0, 1);
    const shoulderR: P2 = [tx + 56, 395];
    if (whistle > 0.05) {
      // Holds clipboard/flag clear of face
      const handR: P2 = [tx + 140, 420];
      p.line([shoulderR, [tx + 110, 450], handR], "#f2ebe0", 20);
      // Brass clipboard
      p.poly([[handR[0] - 15, handR[1] - 45], [handR[0] + 35, handR[1] - 45], [handR[0] + 35, handR[1] + 25], [handR[0] - 15, handR[1] + 25]], "#e2b242", 5);
      // Paper sheet
      p.poly([[handR[0] - 10, handR[1] - 38], [handR[0] + 30, handR[1] - 38], [handR[0] + 30, handR[1] + 20], [handR[0] - 10, handR[1] + 20]], WHITE, 2);
      // Hand gripping board
      p.ell(handR[0] - 5, handR[1] - 5, 12, 12, "#fdfaf2", 5);
    } else {
      // Braced on hip
      const handR: P2 = [tx + 75, 520];
      p.line([shoulderR, [tx + 105, 460], handR], "#f2ebe0", 20);
      p.ell(handR[0], handR[1], 14, 14, "#fdfaf2", 6);
    }
  } else {
    // Guest arms & held props (Rule A)
    const tea = clamp(opts.teaP ?? 0, 0, 1);
    const bill = clamp(opts.billP ?? 0, 0, 1);

    if (bill > 0.05) {
      // Shot 3: Holds up card "STILL OPEN / 0 CRACKS" in front of chest.
      // Both hands pinching outer edges so fists NEVER cover the text!
      const cardW = 240, cardH = 110;
      const cardX = tx - cardW / 2, cardY = 445;

      // Card body (crisp cream and gold)
      p.poly([
        [cardX, cardY], [cardX + cardW, cardY],
        [cardX + cardW, cardY + cardH], [cardX, cardY + cardH]
      ], "#fffaf0", 7);
      // Gold inner border
      p.poly([
        [cardX + 6, cardY + 6], [cardX + cardW - 6, cardY + 6],
        [cardX + cardW - 6, cardY + cardH - 6], [cardX + 6, cardY + cardH - 6]
      ], null, 3);

      // Printed Text inside card
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#8a2434";
      ctx.font = "900 24px 'Arial Black', sans-serif";
      ctx.fillText("STILL OPEN", tx, cardY + 32);
      ctx.fillStyle = "#1e7232";
      ctx.font = "900 28px 'Arial Black', sans-serif";
      ctx.fillText("0 CRACKS", tx, cardY + 74);

      // Both arms holding edges
      const handL: P2 = [cardX - 4, cardY + cardH / 2];
      const handR: P2 = [cardX + cardW + 4, cardY + cardH / 2];

      p.line([[tx - 56, 395], [tx - 110, 460], handL], "#7a2032", 20);
      p.line([[tx + 56, 395], [tx + 110, 460], handR], "#7a2032", 20);

      // Fists pinching the outer edges (clear of text!)
      p.ell(handL[0], handL[1], 12, 14, "#fdfaf2", 5);
      p.ell(handR[0], handR[1], 12, 14, "#fdfaf2", 5);
    } else if (tea > 0.05) {
      // Shot 1: Holds porcelain teacup and saucer in 2D hand clear of face
      const handL: P2 = [tx - 115, 475];
      p.line([[tx - 56, 395], [tx - 95, 440], handL], "#7a2032", 20);

      // White porcelain saucer
      p.ell(handL[0], handL[1] + 10, 32, 8, WHITE, 5);
      // White porcelain teacup with gold rim
      p.poly([
        [handL[0] - 18, handL[1] + 8], [handL[0] + 18, handL[1] + 8],
        [handL[0] + 22, handL[1] - 18], [handL[0] - 22, handL[1] - 18]
      ], WHITE, 5);
      // Tea surface
      p.ell(handL[0], handL[1] - 18, 20, 6, "#6a3518", 2);
      // Cup handle
      p.arc(handL[0] + 24, handL[1] - 6, 8, 8, 270, 90, 4, INK);

      // Hand holding cup base
      p.ell(handL[0], handL[1] + 14, 12, 10, "#fdfaf2", 5);

      // Right arm relaxing by side
      p.line([[tx + 56, 395], [tx + 85, 480], [tx + 75, 540]], "#7a2032", 20);
      p.ell(tx + 75, 540, 12, 12, "#fdfaf2", 5);
    } else {
      // Idle arms
      p.line([[tx - 56, 395], [tx - 85, 480], [tx - 75, 540]], "#7a2032", 20);
      p.line([[tx + 56, 395], [tx + 85, 480], [tx + 75, 540]], "#7a2032", 20);
      p.ell(tx - 75, 540, 12, 12, "#fdfaf2", 5);
      p.ell(tx + 75, 540, 12, 12, "#fdfaf2", 5);
    }
  }

  // 4. HEAD (Warm cream-white circle #fdfaf2, HEAD_R = 145 at (300, 235))
  p.ell(hx, hy, HEAD_R, HEAD_R, HEAD, 12);

  // 5. EXPRESSION & FACE
  drawFace(p, hx, hy, opts.expr, opts.gaze, opts.gazeY);

  // 6. HEADGEAR (Drawn over head, rising above y < 85)
  if (opts.role === "engineer") {
    drawEngineerCap(p, hx, hy);
  } else {
    drawVictorianTopHat(p, hx, hy);
  }
}

// ---------------- 2D UNLIT FX CARDS (Dust puffs, sparks & shadow blobs) ----------------
export type FxType = "dust" | "sparks" | "blob";

export function drawFxBlob(ctx: CanvasRenderingContext2D) {
  // Multiply blend target: white (#ffffff) leaves ground unchanged, dark creates soft shadow
  ctx.fillStyle = WHITE;
  ctx.fillRect(0, 0, 128, 128);
  const gr = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, "#3a2e26");
  gr.addColorStop(0.35, "#6b584b");
  gr.addColorStop(0.70, "#b8aca0");
  gr.addColorStop(1.0, "#ffffff");
  ctx.fillStyle = gr;
  ctx.fillRect(0, 0, 128, 128);
}

export function drawFx(ctx: CanvasRenderingContext2D, type: FxType, progress: number) {
  const p = new Pen(ctx);
  const pr = clamp(progress, 0, 1);

  if (type === "dust") {
    // Expanding warm cream-grey dust cloud puffs
    const alpha = (1 - pr) * 0.85;
    ctx.globalAlpha = alpha;
    const rBase = lerp(20, 110, Math.sqrt(pr));
    const puffs = [
      [300, 500, rBase * 1.0],
      [240, 520, rBase * 0.8],
      [360, 510, rBase * 0.85],
      [200, 540, rBase * 0.65],
      [400, 535, rBase * 0.7],
    ];
    for (const [x, y, r] of puffs) {
      p.ell(x, y, r, r * 0.75, "#e2d8cb", 0);
      p.arc(x, y, r, r * 0.75, 180, 360, 4, "#b4a694");
    }
    ctx.globalAlpha = 1.0;
  } else {
    // Sharp orange & yellow spark burst lines
    const alpha = (1 - pr);
    ctx.globalAlpha = alpha;
    const n = 12;
    for (let i = 0; i < n; i++) {
      const a = (i * Math.PI * 2) / n + pr * 0.5;
      const r0 = lerp(10, 50, pr);
      const r1 = lerp(40, 140, Math.sqrt(pr));
      const x0 = 300 + Math.cos(a) * r0;
      const y0 = 500 + Math.sin(a) * r0;
      const x1 = 300 + Math.cos(a) * r1;
      const y1 = 500 + Math.sin(a) * r1;
      p.stroke([[x0, y0], [x1, y1]], 5, i % 2 ? "#ffcc33" : "#ff5522");
    }
    ctx.globalAlpha = 1.0;
  }
}
