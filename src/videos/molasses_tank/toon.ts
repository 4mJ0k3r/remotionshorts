// 2D cartoon characters for MolassesTankShort in 600x1000 design space (SKILL.md Section 2):
// SU = 0.00216, PIV = 975 at feet, soles at y = 952.
// Warm cream-white head (#fdfaf2) with HEAD_R = 145 at (300, 235), #351f22 ink outlines.
// Compact bean torso width ~135 (y = 375..585).
// Straight parallel vertical legs at x = 265 and 335.
// Solid #351f22 oval pupils with ZERO white anime shine dots.
//
// Characters:
// 1. 'inspector' (Harbor Inspector): grey trench coat (#646c75), dark bowler hat (#2a2d32),
//    holding brass clipboard in 2D hand clear of face.
// 2. 'conductor' (Streetcar Conductor): navy uniform (#1c2d4a) with gold buttons, peaked cap (#d4a236 badge).
//    Action brakeP (0..1) cranks 3D brake lever (fist 168..132, 585). Held cardP ("SWEETEST DISASTER").
import { Pen, INK } from "./pen";

export { Pen, INK };
type P2 = [number, number];

export const HEAD = "#fdfaf2";
export const HEAD_SH = "#ece1cd";
export const HEAD_R = 145;
export const WHITE = "#ffffff";
export const DARK_INK = INK;

export type Expr = "calmSmile" | "panicShock" | "strainGrin";

export type CharOpts = {
  role: "inspector" | "conductor";
  expr: Expr;
  gaze?: number;    // -1..1
  gazeY?: number;   // -1..1
  brakeP?: number;  // 0..1 (conductor)
  boardP?: number;  // 0..1 (inspector clipboard)
  cardP?: number;   // 0..1 (conductor newspaper card)
};

const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

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
      p.stroke([[ex - s * 20, ey - 18], [ex + s * 16, ey], [ex - s * 20, ey + 18]], 11);
      p.stroke([[ex - s * 34, ey - 46], [ex + s * 18, ey - 28]], 12);
    }
    p.ell(hx - 84, my - 6, 22, 12, "#f4b8a8", 0);
    p.ell(hx + 84, my - 6, 22, 12, "#f4b8a8", 0);
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
      p.arc(ex, ey - 48, 24, 14, 195, 345, 10);
      p.ell(ex + px, ey + py, 20, 24, INK, 0);
    }
    p.poly([[hx - 105, ey - 20], [hx - 92, ey - 3], [hx - 118, ey - 3]], "#5ab4f8", 3);
    p.ell(hx - 105, ey + 2, 14, 14, "#5ab4f8", 3);

    const m = smoothClosed([[hx - 28, my - 16], [hx + 28, my - 16], [hx + 34, my + 24], [hx - 34, my + 24]], 5);
    p.poly(m, "#4e1a22", 8);
    p.ell(hx, my + 12, 18, 12, "#d04d44", 0);
    return;
  }

  // calmSmile (default)
  for (const s of S) {
    const ex = hx + s * dx;
    p.arc(ex, ey - 42, 22, 12, 200, 340, 10);
    p.ell(ex + px, ey + py, 16, 22, INK, 0);
  }
  p.ell(hx - 82, my - 6, 22, 12, "#f4bcae", 0);
  p.ell(hx + 82, my - 6, 22, 12, "#f4bcae", 0);

  const m = smoothClosed([
    [hx - 48, my - 10], [hx, my - 6], [hx + 48, my - 10],
    [hx + 32, my + 26], [hx, my + 34], [hx - 32, my + 26]
  ], 5);
  p.poly(m, "#521e24", 8);
  p.poly([[hx - 44, my - 9], [hx + 44, my - 9], [hx + 38, my + 6], [hx - 38, my + 6]], WHITE, 0);
  p.stroke([[hx - 38, my + 6], [hx + 38, my + 6]], 4);
  p.ell(hx, my + 28, 24, 12, "#dc564e", 0);
};

// ---------------- HEADGEAR (Rising clearly above HEAD_R = 145 contour, y < 85) ----------------
const drawBowlerHat = (p: Pen, hx: number, hy: number) => {
  // Dark charcoal grey bowler hat (#2a2d32), brim at y ~ 118, dome rising to y ~ 35
  const charcoal = "#2a2d32", dark = "#181a1d";

  // Rounded dome
  p.poly(smoothClosed([
    [hx - 110, hy - 95], [hx - 80, hy - 175], [hx, hy - 200],
    [hx + 80, hy - 175], [hx + 110, hy - 95]
  ], 6), charcoal, 9);

  // Black ribbon band
  p.poly([[hx - 114, hy - 85], [hx + 114, hy - 85], [hx + 112, hy - 110], [hx - 112, hy - 110]], dark, 6);

  // Curved brim
  p.poly(smoothClosed([
    [hx - 152, hy - 82], [hx, hy - 74], [hx + 152, hy - 82],
    [hx + 148, hy - 96], [hx, hy - 90], [hx - 148, hy - 96]
  ], 6), charcoal, 9);
};

const drawConductorCap = (p: Pen, hx: number, hy: number) => {
  // Navy blue peaked conductor cap (#1c2d4a), gold transit badge (#d4a236)
  const navy = "#1c2d4a", dark = "#101b2d", gold = "#d4a236";

  // Crown
  p.poly(smoothClosed([
    [hx - 115, hy - 92], [hx - 95, hy - 180], [hx, hy - 198],
    [hx + 95, hy - 180], [hx + 115, hy - 92]
  ], 6), navy, 9);

  // Black shiny band with gold chin strap
  p.poly([[hx - 116, hy - 84], [hx + 116, hy - 84], [hx + 114, hy - 112], [hx - 114, hy - 112]], dark, 6);
  p.stroke([[hx - 110, hy - 90], [hx + 110, hy - 90]], 4, gold);

  // Gold transit shield badge
  p.poly([[hx - 16, hy - 140], [hx + 16, hy - 140], [hx + 14, hy - 112], [hx, hy - 100], [hx - 14, hy - 112]], gold, 5);
  p.dot(hx, hy - 124, 4, dark);

  // Black glossy visor
  p.poly(smoothClosed([
    [hx - 145, hy - 80], [hx, hy - 68], [hx + 145, hy - 80],
    [hx + 130, hy - 92], [hx, hy - 84], [hx - 130, hy - 92]
  ], 6), dark, 9);
};

// ---------------- CHARACTER DRAWING ENTRY ----------------
export function drawCharacter(ctx: CanvasRenderingContext2D, opts: CharOpts) {
  const p = new Pen(ctx);
  const hx = 300, hy = 235;

  // 1. LEGS (Straight parallel vertical sticks at x = 265 and 335, soles at y = 952)
  const legX1 = 265, legX2 = 335;
  const legTopY = 575, legBottomY = 945;
  const legColor = opts.role === "inspector" ? "#383d44" : "#141f33";

  p.stroke([[legX1, legTopY], [legX1, legBottomY]], 22, legColor);
  p.stroke([[legX2, legTopY], [legX2, legBottomY]], 22, legColor);

  // Feet
  p.poly(smoothClosed([[legX1 - 22, 940], [legX1 + 34, 940], [legX1 + 36, 958], [legX1 - 22, 958]], 4), INK, 6);
  p.poly(smoothClosed([[legX2 - 22, 940], [legX2 + 34, 940], [legX2 + 36, 958], [legX2 - 22, 958]], 4), INK, 6);

  // 2. TORSO (Compact bean shape width ~ 135 from y = 375 to 585)
  const brake = clamp(opts.brakeP ?? 0, 0, 1);
  const leanOffset = opts.role === "conductor" ? lerp(-4, 12, brake) : 0;

  const tx = hx + leanOffset;
  const torsoShape = smoothClosed([
    [tx - 58, 380],
    [tx + 58, 380],
    [tx + 72, 490],
    [tx + 70, 585],
    [tx - 70, 585],
    [tx - 72, 490],
  ], 6);

  if (opts.role === "inspector") {
    // Grey inspector trench coat (#646c75)
    p.poly(torsoShape, "#646c75", 11);

    // Darker lapels
    const lapelL = smoothClosed([[tx - 56, 384], [tx - 18, 388], [tx - 12, 470], [tx - 40, 582], [tx - 68, 582], [tx - 70, 485]], 5);
    p.poly(lapelL, "#4a515a", 7);
    const lapelR = smoothClosed([[tx + 56, 384], [tx + 18, 388], [tx + 12, 470], [tx + 40, 582], [tx + 68, 582], [tx + 70, 485]], 5);
    p.poly(lapelR, "#4a515a", 7);

    // Collared shirt & dark red tie
    p.poly([[tx - 16, 376], [tx + 16, 376], [tx + 10, 430], [tx, 445], [tx - 10, 430]], "#882328", 5);

    // Coat buttons
    for (const by of [460, 495, 530]) p.dot(tx - 20, by, 4, "#24272c");
  } else {
    // Conductor: Navy blue uniform (#1c2d4a) with gold buttons
    p.poly(torsoShape, "#1c2d4a", 11);

    // Double-breasted front with double gold buttons
    for (const by of [440, 475, 510, 545]) {
      p.dot(tx - 22, by, 4.5, "#d4a236");
      p.dot(tx + 22, by, 4.5, "#d4a236");
    }

    // White stand collar
    p.poly([[tx - 24, 376], [tx + 24, 376], [tx + 22, 396], [tx - 22, 396]], WHITE, 5);
  }

  // 3. ARMS & ACTIONS
  if (opts.role === "conductor") {
    const card = clamp(opts.cardP ?? 0, 0, 1);
    if (card > 0.05) {
      // Shot 3: Holds up "SWEETEST DISASTER" newspaper card in front of chest
      // Hands pinching outer edges clear of text
      const cardW = 260, cardH = 124;
      const cardX = tx - cardW / 2, cardY = 410;

      p.poly([[cardX, cardY], [cardX + cardW, cardY], [cardX + cardW, cardY + cardH], [cardX, cardY + cardH]], "#fffef8", 8);
      p.poly([[cardX + 6, cardY + 6], [cardX + cardW - 6, cardY + 6], [cardX + cardW - 6, cardY + cardH - 6], [cardX + 6, cardY + cardH - 6]], null, 3);

      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#8a2434";
      ctx.font = "900 22px 'Arial Black', sans-serif";
      ctx.fillText("★ THE BOSTON POST ★", tx, cardY + 28);
      ctx.fillStyle = "#16191f";
      ctx.font = "900 27px 'Arial Black', sans-serif";
      ctx.fillText("SWEETEST DISASTER", tx, cardY + 66);
      ctx.font = "bold 17px sans-serif";
      ctx.fillStyle = "#4a5360";
      ctx.fillText("35 MPH SYRUP WAVE SURGE", tx, cardY + 98);

      const handL: P2 = [cardX - 4, cardY + cardH / 2];
      const handR: P2 = [cardX + cardW + 4, cardY + cardH / 2];

      p.line([[tx - 56, 395], [tx - 110, 450], handL], "#1c2d4a", 20);
      p.line([[tx + 56, 395], [tx + 110, 450], handR], "#1c2d4a", 20);

      p.ell(handL[0], handL[1], 13, 15, "#fdfaf2", 5);
      p.ell(handR[0], handR[1], 13, 15, "#fdfaf2", 5);
    } else {
      // Shot 2: Gripping & slamming 3D brake lever
      // Screen-left fist (his right arm) moves from dx = 168 to dx = 132 (dy = 585)
      const fistX = lerp(168, 132, brake);
      const fistY = 585;

      const shoulderL: P2 = [tx - 56, 395];
      const elbowL: P2 = [lerp(tx - 110, tx - 130, brake), lerp(480, 490, brake)];
      p.line([shoulderL, elbowL], "#1c2d4a", 22);
      p.line([elbowL, [fistX, fistY]], "#1c2d4a", 19);

      // Closed fist gripping the 3D brake knob (pinned via Rule B)
      p.poly(smoothClosed([
        [fistX - 16, fistY - 14], [fistX + 16, fistY - 14],
        [fistX + 18, fistY + 16], [fistX - 16, fistY + 16]
      ], 4), "#fdfaf2", 6);
      p.stroke([[fistX - 12, fistY - 2], [fistX + 12, fistY - 2]], 4, INK);

      // Left arm resting on rail/hip
      const shoulderR: P2 = [tx + 56, 395];
      const handR: P2 = [tx + 75, 520];
      p.line([shoulderR, [tx + 105, 460], handR], "#1c2d4a", 20);
      p.ell(handR[0], handR[1], 14, 14, "#fdfaf2", 6);
    }
  } else {
    // Inspector: holds brass clipboard in 2D hand clear of face
    const shoulderL: P2 = [tx - 56, 395];
    const handL: P2 = [tx - 110, 480];
    p.line([shoulderL, [tx - 90, 440], handL], "#646c75", 20);

    // Brass clipboard
    const cbX = handL[0] - 10, cbY = handL[1] - 30;
    p.poly([[cbX - 20, cbY - 40], [cbX + 35, cbY - 40], [cbX + 35, cbY + 40], [cbX - 20, cbY + 40]], "#c89438", 5);
    p.poly([[cbX - 15, cbY - 34], [cbX + 30, cbY - 34], [cbX + 30, cbY + 34], [cbX - 15, cbY + 34]], WHITE, 2);
    // Clip at top
    p.poly([[cbX, cbY - 44], [cbX + 16, cbY - 44], [cbX + 16, cbY - 34], [cbX, cbY - 34]], "#444950", 2);
    // Hand holding clipboard
    p.ell(handL[0], handL[1], 14, 12, "#fdfaf2", 5);

    // Right arm at side
    p.line([[tx + 56, 395], [tx + 85, 480], [tx + 75, 540]], "#646c75", 20);
    p.ell(tx + 75, 540, 12, 12, "#fdfaf2", 5);
  }

  // 4. HEAD
  p.ell(hx, hy, HEAD_R, HEAD_R, HEAD, 12);

  // 5. EXPRESSION
  drawFace(p, hx, hy, opts.expr, opts.gaze, opts.gazeY);

  // 6. HEADGEAR
  if (opts.role === "inspector") {
    drawBowlerHat(p, hx, hy);
  } else {
    drawConductorCap(p, hx, hy);
  }
}

// ---------------- 2D UNLIT FX CARDS ----------------
export type FxType = "dust" | "sparks" | "syrup" | "blob";

export function drawFxBlob(ctx: CanvasRenderingContext2D) {
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

  if (type === "syrup") {
    // Amber-brown molasses syrup splash/jets bursting outward
    const alpha = (1 - pr);
    ctx.globalAlpha = alpha;
    const n = 14;
    for (let i = 0; i < n; i++) {
      const a = (i * Math.PI * 2) / n + pr * 0.4;
      const r0 = lerp(15, 60, pr);
      const r1 = lerp(50, 160, Math.sqrt(pr));
      const x0 = 300 + Math.cos(a) * r0;
      const y0 = 500 + Math.sin(a) * r0;
      const x1 = 300 + Math.cos(a) * r1;
      const y1 = 500 + Math.sin(a) * r1;
      p.stroke([[x0, y0], [x1, y1]], 7, i % 2 ? "#5e2d14" : "#8c441b");
      p.dot(x1, y1, 6, "#4a210d");
    }
    ctx.globalAlpha = 1.0;
  } else if (type === "dust") {
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
  } else if (type === "sparks") {
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
