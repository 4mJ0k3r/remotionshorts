// Procedural canvas textures for InstantSkillShort — no image assets are loaded anywhere in this module.
// Everything readable that is part of a set (the chess board, the cube faces, the cash bands, the tower windows)
// is painted here at 2x-4x the size it is finally seen, because the ink pass and the DOF both sharpen
// edges and a texture authored at display size turns to mush under the grade. The stat readouts are NOT painted:
// they are HTML pills in InstantSkill.tsx, so no sign, board or placard texture exists in this file any more.
type C2D = CanvasRenderingContext2D;

const INK = "#351f22";
const BLACK = '"Arial Black", "Segoe UI Black", "Helvetica Neue", Arial, sans-serif';

const mk = (w: number, h: number, draw: (g: C2D, w: number, h: number) => void) => {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const g = c.getContext("2d")!;
  g.imageSmoothingQuality = "high";
  draw(g, w, h);
  return c;
};

// ---------------- floors & ground ----------------
export const makeConcreteTexture = (base = "#c9c5bc", speck = "#8d8880") => mk(1024, 1024, (g) => {
  g.fillStyle = base; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 5200; i++) {
    g.fillStyle = Math.random() > 0.5 ? speck : "#e2ded6";
    g.globalAlpha = 0.10 + Math.random() * 0.30;
    const s = 1 + Math.random() * 4;
    g.fillRect(Math.random() * 1024, Math.random() * 1024, s, s);
  }
  g.globalAlpha = 1;
  // expansion joints: three passes of pale scoring so the slab reads as poured concrete, not paper
  g.strokeStyle = "rgba(90,84,74,0.55)"; g.lineWidth = 7;
  for (let k = 0; k <= 4; k++) {
    const p = (k * 1024) / 4;
    g.beginPath(); g.moveTo(p, 0); g.lineTo(p, 1024); g.stroke();
    g.beginPath(); g.moveTo(0, p); g.lineTo(1024, p); g.stroke();
  }
});

export const makeAsphaltTexture = () => mk(1024, 1024, (g) => {
  g.fillStyle = "#6f6a64"; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 9000; i++) {
    const v = 70 + Math.random() * 110;
    g.fillStyle = `rgba(${v},${v - 4},${v - 10},${0.16 + Math.random() * 0.3})`;
    g.fillRect(Math.random() * 1024, Math.random() * 1024, 1 + Math.random() * 3, 1 + Math.random() * 3);
  }
});

export const makeWoodFloorTexture = (base = "#b07a44", dark = "#7c4f28") => mk(1024, 1024, (g) => {
  g.fillStyle = base; g.fillRect(0, 0, 1024, 1024);
  const planks = 8, ph = 1024 / planks;
  for (let i = 0; i < planks; i++) {
    const k = 0.86 + (i % 3) * 0.07;
    g.fillStyle = `rgb(${Math.round(176 * k)},${Math.round(122 * k)},${Math.round(68 * k)})`;
    g.fillRect(0, i * ph, 1024, ph - 3);
    for (let s = 0; s < 26; s++) {
      g.strokeStyle = `rgba(${110 + Math.random() * 30},${70 + Math.random() * 20},35,${0.08 + Math.random() * 0.12})`;
      g.lineWidth = 1 + Math.random() * 2.5;
      const y = i * ph + Math.random() * ph;
      g.beginPath(); g.moveTo(0, y); g.bezierCurveTo(340, y + 5, 700, y - 5, 1024, y); g.stroke();
    }
    g.fillStyle = dark; g.fillRect(0, (i + 1) * ph - 4, 1024, 4);
  }
});

export const makeGreenFeltTexture = () => mk(512, 512, (g) => {
  g.fillStyle = "#1d6b4a"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 26000; i++) {
    const v = Math.random();
    g.fillStyle = v > 0.5 ? "rgba(46,132,92,0.30)" : "rgba(14,58,38,0.30)";
    g.fillRect(Math.random() * 512, Math.random() * 512, 2, 2);
  }
});

export const makeTileTexture = (a = "#e8dcc4", b = "#cbb994") => mk(512, 512, (g) => {
  const n = 4, s = 512 / n;
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    g.fillStyle = (x + y) % 2 ? b : a;
    g.fillRect(x * s, y * s, s, s);
    g.strokeStyle = "rgba(120,100,74,0.5)"; g.lineWidth = 4;
    g.strokeRect(x * s + 2, y * s + 2, s - 4, s - 4);
  }
});

// ---------------- walls ----------------
export const makePlasterTexture = (base = "#f0e2c6") => mk(512, 512, (g) => {
  g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 7000; i++) {
    g.fillStyle = `rgba(${150 + Math.random() * 90},${130 + Math.random() * 80},${100 + Math.random() * 70},0.06)`;
    g.fillRect(Math.random() * 512, Math.random() * 512, 1 + Math.random() * 5, 1 + Math.random() * 5);
  }
  // wainscot rail: a warm mid-tone so a character standing against the wall never sits on a flat blank field
  g.fillStyle = "rgba(120,86,50,0.35)"; g.fillRect(0, 330, 512, 12);
  g.fillStyle = "rgba(255,248,232,0.18)"; g.fillRect(0, 342, 512, 170);
});

export const makeBrickTexture = (base = "#b4693f", mortar = "#e6d6bd") => mk(1024, 1024, (g) => {
  g.fillStyle = mortar; g.fillRect(0, 0, 1024, 1024);
  const n = parseInt(base.slice(1), 16);
  const br = (n >> 16) & 255, bg = (n >> 8) & 255, bb = n & 255;
  const bh = 64, bw = 128;
  for (let row = 0; row * bh < 1024; row++) {
    const off = (row % 2) * (bw / 2);
    for (let col = -1; col * bw + off < 1024 + bw; col++) {
      const x = col * bw + off, y = row * bh;
      const v = 0.82 + Math.random() * 0.36;
      g.fillStyle = `rgb(${Math.min(255, Math.round(br * v))},${Math.min(255, Math.round(bg * v))},${Math.min(255, Math.round(bb * v))})`;
      g.fillRect(x + 4, y + 4, bw - 8, bh - 8);
    }
  }
});

export const makeLoungeWallTexture = () => mk(512, 1024, (g) => {
  // deep amber walnut panelling with a lit cream upper band: the moody set still clears luma 0.38 because the
  // upper third behind the characters' heads is bright
  g.fillStyle = "#f0dcb4"; g.fillRect(0, 0, 512, 300);
  const gr = g.createLinearGradient(0, 300, 0, 1024);
  gr.addColorStop(0, "#8a5a2c"); gr.addColorStop(1, "#4a2e16");
  g.fillStyle = gr; g.fillRect(0, 300, 512, 724);
  g.strokeStyle = "rgba(30,18,10,0.6)"; g.lineWidth = 8;
  for (let x = 0; x <= 512; x += 84) { g.beginPath(); g.moveTo(x, 320); g.lineTo(x, 1024); g.stroke(); }
  g.strokeRect(4, 4, 504, 292);
  g.fillStyle = "#e0b862"; g.fillRect(0, 292, 512, 14);
});

export const makeCabinWallTexture = () => mk(512, 512, (g) => {
  // brushed composite airliner interior: pale grey-cream with a subtle horizontal seam
  g.fillStyle = "#e9eef3"; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 2600; i++) {
    g.fillStyle = `rgba(200,210,222,${0.05 + Math.random() * 0.12})`;
    g.fillRect(Math.random() * 512, Math.random() * 512, 2 + Math.random() * 8, 1);
  }
  g.fillStyle = "rgba(150,164,178,0.5)"; g.fillRect(0, 250, 512, 5);
  g.fillStyle = "rgba(255,255,255,0.55)"; g.fillRect(0, 255, 512, 4);
});

export const makeSeatFabricTexture = (col = "#2f6fb5") => mk(256, 256, (g) => {
  g.fillStyle = col; g.fillRect(0, 0, 256, 256);
  for (let y = 0; y < 256; y += 4) for (let x = 0; x < 256; x += 4) {
    g.fillStyle = ((x + y) / 4) % 2 ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.10)";
    g.fillRect(x, y, 4, 4);
  }
});

/** the bright sky plate inside every oval window — this is what carries the cabin shot's luma */
export const makeSkyWindowTexture = () => mk(512, 512, (g) => {
  const gr = g.createLinearGradient(0, 0, 0, 512);
  gr.addColorStop(0, "#ffffff"); gr.addColorStop(0.35, "#eaf4ff");
  gr.addColorStop(0.7, "#bcdcfb"); gr.addColorStop(1, "#8fc3f2");
  g.fillStyle = gr; g.fillRect(0, 0, 512, 512);
  g.fillStyle = "rgba(255,255,255,0.85)";
  for (let i = 0; i < 7; i++) {
    const cx = Math.random() * 512, cy = 260 + Math.random() * 200, r = 40 + Math.random() * 70;
    g.beginPath(); g.ellipse(cx, cy, r, r * 0.45, 0, 0, Math.PI * 2); g.fill();
  }
});

/** warm dusk city plate for the skatepark background windows / gaps between buildings */
export const makeDuskPlateTexture = () => mk(512, 512, (g) => {
  const gr = g.createLinearGradient(0, 0, 0, 512);
  gr.addColorStop(0, "#ffd9a8"); gr.addColorStop(0.55, "#ffc187"); gr.addColorStop(1, "#f0a06a");
  g.fillStyle = gr; g.fillRect(0, 0, 512, 512);
});

// ---------------- twilight city (Act 1 revision) ----------------
const rng = (seed: number) => {
  let r = seed * 2654435761 % 2147483647;
  return () => ((r = (r * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
};

/**
 * One apartment facade at dusk: brick, a grid of windows, and a fraction of them lit #ffcf56. `seed` gives every
 * block its own lit pattern, which is what stops nine identical boxes reading as one tiled texture sheet. Unlit
 * glass sits only a little darker than the wall on purpose — the ink pass, not the paint, draws the separation.
 */
export const makeFacadeTexture = (o: { wall: string; mortar?: string; glass: string; lit: string; cols?: number; rows?: number; seed?: number }) => {
  const cols = o.cols ?? 5, rows = o.rows ?? 3, rand = rng(o.seed ?? 1);
  return mk(512, 512, (g) => {
    g.fillStyle = o.wall; g.fillRect(0, 0, 512, 512);
    for (let i = 0; i < 70; i++) {
      g.fillStyle = `rgba(0,0,0,${0.04 + rand() * 0.05})`;
      g.fillRect(rand() * 512, rand() * 512, 30 + rand() * 90, 4 + rand() * 8);
    }
    const cw = 512 / cols, ch = 512 / rows, w = cw * 0.52, h = ch * 0.5;
    for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
      const cx = x * cw + (cw - w) / 2, cy = y * ch + (ch - h) / 2;
      const on = rand() < 0.42;
      g.fillStyle = on ? o.lit : o.glass;
      g.fillRect(cx, cy, w, h);
      if (on) {
        // a lit room is brighter at the sill, and the frame is what makes the square read as a window at 15 m
        const gr = g.createLinearGradient(cx, cy, cx, cy + h);
        gr.addColorStop(0, "rgba(255,255,255,0.18)"); gr.addColorStop(1, "rgba(255,150,40,0.32)");
        g.fillStyle = gr; g.fillRect(cx, cy, w, h);
      }
      g.strokeStyle = "rgba(16,12,26,0.75)"; g.lineWidth = 5;
      g.strokeRect(cx, cy, w, h);
      g.beginPath(); g.moveTo(cx + w / 2, cy); g.lineTo(cx + w / 2, cy + h); g.stroke();
    }
    // storey bands so a 5 m block is not one flat sheet of brick when it fills a third of the frame
    g.strokeStyle = "rgba(12,9,20,0.4)"; g.lineWidth = 7;
    for (let y = 1; y < rows; y++) { g.beginPath(); g.moveTo(0, y * ch); g.lineTo(512, y * ch); g.stroke(); }
  });
};

/** additive pool of light (a streetlamp on concrete, a pendant on a table): an ALPHA gradient, so it lays over the
 *  set instead of being baked into it and the ink pass never sees an edge */
export const makeGlowTexture = (col: string, core = 0.9) => mk(256, 256, (g) => {
  const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, col); gr.addColorStop(0.34, col.replace(")", `,${core})`).replace("rgb", "rgba"));
  gr.addColorStop(1, "rgba(0,0,0,0)");
  g.clearRect(0, 0, 256, 256);
  g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
});

/** the night city seen THROUGH an interior window band. With the boards deleted this plate is what carries the
 *  luma for the chess hall, the cabin and the lounge, so it needs a bright horizon glow, real building masses and
 *  scattered lit windows — and it must never fall below ~0.35 mean. */
export const makeNightCityTexture = (seed = 3) => {
  const rand = rng(seed);
  return mk(1024, 512, (g) => {
    const gr = g.createLinearGradient(0, 0, 0, 512);
    gr.addColorStop(0, "#161130"); gr.addColorStop(0.42, "#2d2346");
    gr.addColorStop(0.72, "#5a3a5c"); gr.addColorStop(0.88, "#b8654a"); gr.addColorStop(1, "#ff9a4e");
    g.fillStyle = gr; g.fillRect(0, 0, 1024, 512);
    for (let i = 0; i < 60; i++) {
      g.fillStyle = `rgba(255,240,210,${0.25 + rand() * 0.6})`;
      g.fillRect(rand() * 1024, rand() * 210, 2, 2);
    }
    // two recession layers: a far silhouette, then a nearer block row with lit windows
    for (const [base, hMax, alpha] of [[430, 120, 0.55], [470, 190, 1]] as [number, number, number][]) {
      let x = -20;
      while (x < 1044) {
        const w = 40 + rand() * 90, h = 30 + rand() * hMax;
        g.fillStyle = alpha < 1 ? `rgba(24,18,42,${alpha})` : "#18122a";
        g.fillRect(x, base - h, w, h);
        if (alpha === 1) {
          for (let wy = base - h + 12; wy < base - 14; wy += 22) {
            for (let wx = x + 8; wx < x + w - 10; wx += 18) {
              if (rand() < 0.34) { g.fillStyle = rand() < 0.75 ? "#ffcf56" : "#8fd6ff"; g.fillRect(wx, wy, 7, 9); }
            }
          }
        }
        x += w + 6 + rand() * 26;
      }
    }
  });
};

// ---------------- chess ----------------
export const makeChessBoardTexture = () => mk(512, 512, (g) => {
  const n = 8, s = 512 / n;
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    g.fillStyle = (x + y) % 2 ? "#6b4a2c" : "#f4e7cd";
    g.fillRect(x * s, y * s, s, s);
  }
  g.strokeStyle = INK; g.lineWidth = 8; g.strokeRect(0, 0, 512, 512);
});

// ---------------- rubik ----------------
/** one cube face: solved = 9 clean stickers, scrambled = shuffled colours (the solve is read at a glance) */
export const makeCubeFaceTexture = (solved: boolean, seed = 1) => mk(256, 256, (g) => {
  g.fillStyle = "#141014"; g.fillRect(0, 0, 256, 256);
  const cols = ["#ff3b30", "#ffd60a", "#34c759", "#0a84ff", "#ffffff", "#ff9f0a"];
  const s = 256 / 3, pad = 8;
  let r = seed;
  const rnd = () => ((r = (r * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
  for (let y = 0; y < 3; y++) for (let x = 0; x < 3; x++) {
    const c = solved ? cols[0] : cols[Math.floor(rnd() * cols.length)];
    g.fillStyle = c;
    g.beginPath(); g.roundRect(x * s + pad, y * s + pad, s - 2 * pad, s - 2 * pad, 10); g.fill();
  }
});

// ---------------- cash ----------------
export const makeCashBandTexture = () => mk(512, 256, (g) => {
  g.fillStyle = "#2f7d4f"; g.fillRect(0, 0, 512, 256);
  for (let i = 0; i < 8; i++) {
    g.fillStyle = i % 2 ? "#37915c" : "#2b7248";
    g.fillRect(0, i * 32, 512, 30);
    g.strokeStyle = "rgba(20,50,32,0.7)"; g.lineWidth = 2;
    g.strokeRect(6, i * 32 + 2, 500, 26);
  }
  // the paper strap across the middle of the bundle
  g.fillStyle = "#e8dcc0"; g.fillRect(196, 0, 120, 256);
  g.strokeStyle = "rgba(60,48,30,0.6)"; g.lineWidth = 4; g.strokeRect(196, 0, 120, 256);
  g.fillStyle = INK; g.textAlign = "center"; g.textBaseline = "middle";
  g.font = `900 44px ${BLACK}`; g.fillText("100", 256, 128);
});

// ---------------- graffiti / ramp stripes ----------------
export const makeRampStripeTexture = () => mk(512, 512, (g) => {
  g.fillStyle = "#b9b3a8"; g.fillRect(0, 0, 512, 512);
  for (let i = -512; i < 512; i += 96) {
    g.fillStyle = "rgba(230,120,60,0.55)";
    g.beginPath(); g.moveTo(i, 512); g.lineTo(i + 48, 512); g.lineTo(i + 48 + 512, 0); g.lineTo(i + 512, 0); g.closePath(); g.fill();
  }
  g.strokeStyle = "rgba(90,84,74,0.5)"; g.lineWidth = 6;
  for (let i = 0; i < 512; i += 64) { g.beginPath(); g.moveTo(0, i); g.lineTo(512, i); g.stroke(); }
});

// ---------------- contact shadow ----------------
/** multiply-blend blob: white leaves the ground untouched, the dark core is the contact shadow */
export const makeBlobTexture = () => mk(128, 128, (g) => {
  g.fillStyle = "#ffffff"; g.fillRect(0, 0, 128, 128);
  const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  gr.addColorStop(0, "#3a2e26"); gr.addColorStop(0.35, "#6b584b");
  gr.addColorStop(0.7, "#b8aca0"); gr.addColorStop(1, "#ffffff");
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
});

// =====================================================================================
// ACT 2 / ACT 3 — snow basin, desert highway, neuron chamber, night road.
//
// Same rules as above: procedural canvas only, nothing legible anywhere. The one new primitive is `tile()`,
// which runs a draw callback nine times (the eight wrap offsets) so a mark that leaves the right / bottom edge
// re-enters on the opposite side. The Act 2/3 ground planes tile at 12-30 repeats across the frame, and a
// non-tileable mark there reads as a grid of box seams the instant the camera tracks — which is exactly how the
// Act 1 "expansion joint" trick works, only the joint now has to land on the tile edge.
// =====================================================================================

/** seamless wrap: draws fn at every 1024-class offset so strokes crossing an edge continue on the far side */
const tile = (g: C2D, size: number, fn: () => void) => {
  for (let ox = -1; ox <= 1; ox++) {
    for (let oy = -1; oy <= 1; oy++) {
      g.save(); g.translate(ox * size, oy * size); fn(); g.restore();
    }
  }
};

// ---------------- alpine snow basin (shots 11, 20-22) ----------------
/** wind-carved snowfield. Every element is drawn through tile(), so the piste's 5 m tiles butt together with no
 *  visible grid: the only thing that separates one tile from the next is a sastrugi crest, which is what real
 *  sastrugi do anyway. Cool blue hollows keep the saturation floor up on a set that is otherwise near-white. */
export const makeSnowTexture = (base = "#f5f8ff", hollow = "#bed5ee") => mk(1024, 1024, (g) => {
  g.fillStyle = base; g.fillRect(0, 0, 1024, 1024);
  const rand = rng(71);
  // drift hollows: soft blue bowls, kept inside the tile so a radial gradient never has to wrap
  for (let i = 0; i < 56; i++) {
    const x = 140 + rand() * 744, y = 140 + rand() * 744, r = 70 + rand() * 190;
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, `rgba(150,182,220,${0.10 + rand() * 0.10})`);
    gr.addColorStop(1, "rgba(150,182,220,0)");
    g.fillStyle = gr; g.beginPath(); g.ellipse(x, y, r, r * 0.42, rand() * 3.14, 0, 6.2832); g.fill();
  }
  // sastrugi: 340 wind ribbons, all sheared the same ~20 degrees because one slope has one prevailing wind
  g.lineCap = "round";
  for (let i = 0; i < 340; i++) {
    const x = rand() * 1024, y = rand() * 1024, len = 60 + rand() * 300, dy = (rand() - 0.5) * 26;
    const dark = rand() < 0.45;
    g.strokeStyle = dark ? `rgba(150,180,218,${0.10 + rand() * 0.16})` : `rgba(255,255,255,${0.18 + rand() * 0.34})`;
    g.lineWidth = 1 + rand() * 5;
    tile(g, 1024, () => {
      g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + len * 0.4, y + dy, x + len * 0.65, y - dy, x + len, y); g.stroke();
    });
  }
  // granular glitter + a handful of blown grit so the field is never airbrushed
  for (let i = 0; i < 2600; i++) {
    g.fillStyle = rand() < 0.78 ? "rgba(255,255,255,0.85)" : "rgba(146,172,204,0.45)";
    const s = 1 + rand() * 2.4;
    g.fillRect(rand() * 1024, rand() * 1024, s, s);
  }
  for (let i = 0; i < 90; i++) {
    g.fillStyle = `rgba(96,112,136,${0.14 + rand() * 0.2})`;
    g.beginPath(); g.ellipse(rand() * 1024, rand() * 1024, 2 + rand() * 6, 1 + rand() * 3, rand() * 3.14, 0, 6.2832); g.fill();
  }
  void hollow;
});

/** one mountain mass. v=1 of this canvas is the TOP of the box it is painted on (a BoxGeometry's four side faces
 *  all have their uv v axis running along world +y), which is what lets one texture carry three separate jobs: a
 *  lit snow parapet on the skyline edge, rock-streaked snow down the flank, and a snow apron at the foot.
 *  Horizontally it wraps through tile(), so build.ts is free to repeat it 3x across a 32 m ridge. */
export const makeRidgeTexture = (o: { rock?: string; snow?: string; seed?: number } = {}) => {
  const rock = o.rock ?? "#6d6577";
  const snow = o.snow ?? "#edf3fb";
  const rand = rng(o.seed ?? 5);
  return mk(1024, 1024, (g) => {
    const n = parseInt(rock.slice(1), 16);
    const rr = (n >> 16) & 255, rg = (n >> 8) & 255, rb = n & 255;
    g.fillStyle = rock; g.fillRect(0, 0, 1024, 1024);
    // strata: bands that wrap horizontally, each slightly off-colour, so a 30 m mass has bedding planes
    for (let y = 0; y < 1024; y += 26 + Math.floor(rand() * 44)) {
      const h = 16 + rand() * 52, k = 0.72 + rand() * 0.5;
      g.fillStyle = `rgb(${Math.min(255, rr * k) | 0},${Math.min(255, rg * k) | 0},${Math.min(255, rb * k) | 0})`;
      g.globalAlpha = 0.55 + rand() * 0.4; g.fillRect(0, y, 1024, h);
    }
    g.globalAlpha = 1;
    // fault lines + scarp shading
    g.lineCap = "round";
    for (let i = 0; i < 130; i++) {
      const x = rand() * 1024, y = rand() * 1024, len = 40 + rand() * 220, a = -1.2 + rand() * 2.4;
      g.strokeStyle = `rgba(22,20,34,${0.16 + rand() * 0.24})`; g.lineWidth = 2 + rand() * 7;
      tile(g, 1024, () => { g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(a) * len, y + Math.sin(a) * len); g.stroke(); });
    }
    // snow hanging from the skyline: a solid cap band whose lower boundary is torn, then gullies running down
    g.fillStyle = snow;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(1024, 0); g.lineTo(1024, 150);
    for (let x = 1024; x >= 0; x -= 48) g.lineTo(x, 150 + Math.sin(x * 0.021) * 40 + rand() * 78);
    g.lineTo(0, 150); g.closePath(); g.fill();
    for (let i = 0; i < 46; i++) {
      const x = rand() * 1024, w = 16 + rand() * 60, drop = 190 + rand() * 620;
      const gr = g.createLinearGradient(0, 120, 0, 120 + drop);
      gr.addColorStop(0, snow); gr.addColorStop(0.72, "rgba(237,243,251,0.55)"); gr.addColorStop(1, "rgba(237,243,251,0)");
      g.fillStyle = gr;
      tile(g, 1024, () => {
        g.beginPath(); g.moveTo(x, 120); g.lineTo(x + w, 120);
        g.lineTo(x + w * 1.5, 120 + drop); g.lineTo(x - w * 0.5, 120 + drop); g.closePath(); g.fill();
      });
    }
    // foot apron: the mass meets the basin in snow, not in a sawn box edge
    const af = g.createLinearGradient(0, 1024, 0, 780);
    af.addColorStop(0, "rgba(240,246,254,0.98)"); af.addColorStop(1, "rgba(240,246,254,0)");
    g.fillStyle = af; g.fillRect(0, 780, 1024, 244);
    // parapet highlight: the one crisp line that tells the eye where the roof of the world is
    g.fillStyle = "rgba(255,255,255,0.92)"; g.fillRect(0, 0, 1024, 18);
  });
};

/** the avalanche wall's leading face. Same v=1-is-the-top trick as the ridge, plus a hard shadowed undercut band
 *  at v=0 because a class-4 slab rides on a cushion of air and debris, not on the ground. */
export const makeAvalancheTexture = (o: { base?: string; core?: string; seed?: number } = {}) => {
  const base = o.base ?? "#e9f2fd";
  const core = o.core ?? "#9dc4e8";
  const rand = rng(o.seed ?? 17);
  return mk(1024, 512, (g) => {
    g.fillStyle = base; g.fillRect(0, 0, 1024, 512);
    // vertical fluting: the torn face of a slab that broke into teeth on the way down
    for (let i = 0; i < 150; i++) {
      const x = rand() * 1024, w = 8 + rand() * 42, top = rand() * 90, h = 150 + rand() * 330;
      const gr = g.createLinearGradient(x, 0, x + w, 0);
      const dark = rand() < 0.5;
      gr.addColorStop(0, dark ? "rgba(118,156,196,0.0)" : `rgba(118,156,196,${0.18 + rand() * 0.3})`);
      gr.addColorStop(0.5, dark ? `rgba(118,156,196,${0.16 + rand() * 0.34})` : "rgba(255,255,255,0.6)");
      gr.addColorStop(1, dark ? "rgba(118,156,196,0.0)" : `rgba(118,156,196,${0.14 + rand() * 0.26})`);
      g.fillStyle = gr;
      tile(g, 1024, () => { g.beginPath(); g.moveTo(x, top); g.lineTo(x + w, top + 14); g.lineTo(x + w * 1.4, top + h); g.lineTo(x - w * 0.4, top + h - 18); g.closePath(); g.fill(); });
    }
    // crown: a lit lip across the whole top edge, so the wall reads as an overhang rather than a painted flat
    const cg = g.createLinearGradient(0, 0, 0, 92);
    cg.addColorStop(0, "rgba(255,255,255,0.96)"); cg.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = cg; g.fillRect(0, 0, 1024, 92);
    // blue interior: dense old ice shows through the torn shoulder
    for (let i = 0; i < 26; i++) {
      const x = rand() * 1024, y = 150 + rand() * 240, r = 30 + rand() * 90;
      const gr = g.createRadialGradient(x, y, 0, x, y, r);
      gr.addColorStop(0, `rgba(96,168,214,${0.30 + rand() * 0.26})`); gr.addColorStop(1, "rgba(96,168,214,0)");
      g.fillStyle = gr; g.beginPath(); g.ellipse(x, y, r, r * 0.6, rand() * 3.14, 0, 6.2832); g.fill();
    }
    // the rumble line: rock and ice rubble carried at the base, plus the shadow the whole wall throws under itself
    for (let i = 0; i < 220; i++) {
      const v = 60 + rand() * 90;
      g.fillStyle = `rgba(${v},${v + 4},${v + 16},${0.3 + rand() * 0.4})`;
      g.beginPath(); g.ellipse(rand() * 1024, 430 + rand() * 70, 3 + rand() * 16, 2 + rand() * 7, rand() * 3.14, 0, 6.2832); g.fill();
    }
    const bg = g.createLinearGradient(0, 380, 0, 512);
    bg.addColorStop(0, "rgba(58,80,110,0)"); bg.addColorStop(1, `rgba(52,74,104,0.62)`);
    g.fillStyle = bg; g.fillRect(0, 380, 1024, 132);
    void core;
  });
};

/** additive spray sheet: one soft core plus forward-raking filaments, all in ALPHA (same contract as
 *  makeGlowTexture: pass "rgb(255,255,255)" and set the colour on the material, so the tone map owns the hue) */
export const makeSprayTexture = () => mk(512, 512, (g) => {
  g.clearRect(0, 0, 512, 512);
  const rand = rng(404);
  const base = g.createRadialGradient(256, 330, 10, 256, 330, 210);
  base.addColorStop(0, "rgba(255,255,255,0.95)"); base.addColorStop(0.45, "rgba(255,255,255,0.34)");
  base.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = base; g.beginPath(); g.ellipse(256, 330, 210, 150, 0, 0, 6.2832); g.fill();
  g.globalCompositeOperation = "lighter";
  for (let i = 0; i < 54; i++) {
    const x = 90 + rand() * 330, y = 330 - rand() * 60, len = 90 + rand() * 260, a = -1.9 + rand() * 0.9;
    const gr = g.createLinearGradient(x, y, x + Math.cos(a) * len, y + Math.sin(a) * len);
    gr.addColorStop(0, `rgba(255,255,255,${0.3 + rand() * 0.5})`); gr.addColorStop(1, "rgba(255,255,255,0)");
    g.strokeStyle = gr; g.lineWidth = 4 + rand() * 20; g.lineCap = "round";
    g.beginPath(); g.moveTo(x, y);
    g.quadraticCurveTo(x + Math.cos(a) * len * 0.6, y + Math.sin(a) * len * 0.6 - 30, x + Math.cos(a) * len, y + Math.sin(a) * len);
    g.stroke();
  }
  for (let i = 0; i < 260; i++) {
    g.fillStyle = `rgba(255,255,255,${0.2 + rand() * 0.6})`;
    const s = 2 + rand() * 7;
    g.beginPath(); g.arc(rand() * 512, rand() * 512, s, 0, 6.2832); g.fill();
  }
  g.globalCompositeOperation = "source-over";
});

// ---------------- desert highway (shots 12-13) ----------------
/** one lane-marking period, transparent everywhere the paint is not. build.ts tiles this vertically at
 *  STRIPE_LEN / HIGHWAY.stripeZ, so one canvas == one painted dash + one gap and world.ts can wrap the plane by
 *  exactly HIGHWAY.stripeZ without ever showing a jump. */
export const makeDashTexture = () => mk(128, 1024, (g) => {
  g.clearRect(0, 0, 128, 1024);
  const rand = rng(909);
  const x0 = 24, x1 = 104, y0 = 88, y1 = 690;
  const gr = g.createLinearGradient(x0, 0, x1, 0);
  gr.addColorStop(0, "#d8d2c2"); gr.addColorStop(0.4, "#f6f2e6"); gr.addColorStop(1, "#cec7b6");
  g.fillStyle = gr;
  g.beginPath();
  g.moveTo(x0 + 6, y0); g.lineTo(x1 - 2, y0 + 10); g.lineTo(x1 - 8, y1); g.lineTo(x0 + 2, y1 - 14); g.closePath(); g.fill();
  // sun-baked wear: the paint chips off in long patches along the wheel path
  g.globalCompositeOperation = "destination-out";
  for (let i = 0; i < 120; i++) {
    g.fillStyle = `rgba(0,0,0,${0.25 + rand() * 0.55})`;
    g.fillRect(x0 + rand() * (x1 - x0), y0 + rand() * (y1 - y0), 3 + rand() * 26, 2 + rand() * 9);
  }
  for (let i = 0; i < 16; i++) {
    g.fillStyle = "rgba(0,0,0,0.9)";
    g.fillRect(x0, y0 + rand() * (y1 - y0), x1 - x0, 2 + rand() * 4);
  }
  g.globalCompositeOperation = "source-over";
  // tyre smear at both ends so the dash dies into the tarmac instead of being cut
  const eg = g.createLinearGradient(0, y1, 0, 1024);
  eg.addColorStop(0, "rgba(210,204,190,0)"); eg.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = eg; g.fillRect(0, y1, 128, 1024 - y1);
});

/** open-wheel livery. Panel seams, rivet rows, a sun-bleached crown and an accent arrow — deliberately NO racing
 *  number and no letters anywhere, because the only text in this film is the subtitle line. */
export const makeCarPaintTexture = (o: { base?: string; accent?: string; dark?: string } = {}) => {
  const base = o.base ?? "#c8391f";
  const accent = o.accent ?? "#f2ede0";
  const dark = o.dark ?? "#7d2412";
  return mk(1024, 512, (g) => {
    const gr = g.createLinearGradient(0, 0, 0, 512);
    gr.addColorStop(0, "#ffffff"); gr.addColorStop(0.18, base); gr.addColorStop(1, dark);
    g.fillStyle = base; g.fillRect(0, 0, 1024, 512);
    g.fillStyle = gr; g.globalAlpha = 0.35; g.fillRect(0, 0, 1024, 512); g.globalAlpha = 1;
    // accent arrow running along the body, drawn as chevrons so it reads at 42 cm off the tarmac
    g.fillStyle = accent;
    for (let i = 0; i < 3; i++) {
      const y = 150 + i * 96;
      g.beginPath(); g.moveTo(60 + i * 130, y); g.lineTo(430 + i * 130, y + 30); g.lineTo(60 + i * 130, y + 60);
      g.lineTo(150 + i * 130, y + 30); g.closePath(); g.fill();
    }
    // panel breaks + a rivet line under each one
    g.strokeStyle = "rgba(40,16,10,0.55)"; g.lineWidth = 4;
    for (const x of [120, 400, 690, 900]) {
      g.beginPath(); g.moveTo(x, 0); g.lineTo(x + 18, 512); g.stroke();
      g.fillStyle = "rgba(255,240,225,0.35)";
      for (let y = 18; y < 512; y += 34) g.beginPath(), g.arc(x + (y / 512) * 18, y, 4, 0, 6.2832), g.fill();
    }
    // desert dust along the bottom third: everything down there is thrown up by the car in front of it
    const dg = g.createLinearGradient(0, 300, 0, 512);
    dg.addColorStop(0, "rgba(190,158,120,0)"); dg.addColorStop(1, "rgba(196,166,126,0.55)");
    g.fillStyle = dg; g.fillRect(0, 300, 1024, 212);
    const rand = rng(713);
    for (let i = 0; i < 900; i++) {
      g.fillStyle = `rgba(226,206,178,${0.05 + rand() * 0.2})`;
      g.fillRect(rand() * 1024, 250 + rand() * 262, 1 + rand() * 5, 1 + rand() * 3);
    }
  });
};

/** additive speed ribbons alongside the car, running along +u so build.ts can lay them down the road axis */
export const makeStreakTexture = () => mk(1024, 128, (g) => {
  g.clearRect(0, 0, 1024, 128);
  g.globalCompositeOperation = "lighter";
  const rand = rng(211);
  for (let i = 0; i < 44; i++) {
    const y = rand() * 128, len = 180 + rand() * 780, x = rand() * (1024 - len);
    const gr = g.createLinearGradient(x, 0, x + len, 0);
    gr.addColorStop(0, "rgba(255,255,255,0)");
    gr.addColorStop(0.42, `rgba(255,255,255,${0.30 + rand() * 0.5})`);
    gr.addColorStop(1, "rgba(255,255,255,0)");
    g.strokeStyle = gr; g.lineWidth = 2 + rand() * 9; g.lineCap = "round";
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + len, y + (rand() - 0.5) * 8); g.stroke();
  }
  g.globalCompositeOperation = "source-over";
});

// ---------------- neuron chamber (shots 14-16) ----------------
/** the soma's own skin: an organic membrane field. Sits under an emissive cyan material, so the dark plates are
 *  what the two-tone ramp multiplies and the bright veins are what the bloom pass catches when the core runs red. */
export const makeMembraneTexture = () => mk(1024, 1024, (g) => {
  const gr = g.createLinearGradient(0, 0, 1024, 1024);
  gr.addColorStop(0, "#12506c"); gr.addColorStop(0.5, "#0d3c58"); gr.addColorStop(1, "#14586e");
  g.fillStyle = gr; g.fillRect(0, 0, 1024, 1024);
  const rand = rng(88);
  // cell field: blotches with a darker rim, the classic histology look, no two the same size
  for (let i = 0; i < 190; i++) {
    const x = rand() * 1024, y = rand() * 1024, r = 18 + rand() * 96;
    const rg = g.createRadialGradient(x, y, r * 0.2, x, y, r);
    rg.addColorStop(0, `rgba(${30 + rand() * 40 | 0},${130 + rand() * 70 | 0},${160 + rand() * 60 | 0},0.34)`);
    rg.addColorStop(0.78, "rgba(10,44,64,0.20)"); rg.addColorStop(1, "rgba(8,32,48,0.52)");
    g.fillStyle = rg; g.beginPath(); g.ellipse(x, y, r, r * (0.62 + rand() * 0.5), rand() * 3.14, 0, 6.2832); g.fill();
  }
  // Nissl speckle
  for (let i = 0; i < 5200; i++) {
    g.fillStyle = `rgba(${8 + rand() * 30 | 0},${70 + rand() * 90 | 0},${92 + rand() * 70 | 0},${0.06 + rand() * 0.2})`;
    g.fillRect(rand() * 1024, rand() * 1024, 1 + rand() * 4, 1 + rand() * 4);
  }
  // membrane veins, tiled so the wrap survives the sphere's uv seam
  g.lineCap = "round";
  for (let i = 0; i < 70; i++) {
    const x = rand() * 1024, y = rand() * 1024, len = 90 + rand() * 420, a = rand() * 6.2832;
    g.strokeStyle = `rgba(${150 + rand() * 90 | 0},${240 + rand() * 15 | 0},255,${0.16 + rand() * 0.3})`;
    g.lineWidth = 2 + rand() * 6;
    tile(g, 1024, () => {
      g.beginPath(); g.moveTo(x, y);
      g.bezierCurveTo(x + Math.cos(a) * len * 0.4, y + Math.sin(a) * len * 0.4, x + Math.cos(a + 0.7) * len * 0.7, y + Math.sin(a + 0.7) * len * 0.7, x + Math.cos(a) * len, y + Math.sin(a) * len);
      g.stroke();
    });
  }
  // the nucleus: one pale mass the lens can lock onto wherever the sphere happens to be facing
  const ng = g.createRadialGradient(360, 430, 20, 360, 430, 200);
  ng.addColorStop(0, "rgba(206,252,255,0.72)"); ng.addColorStop(0.55, "rgba(84,190,214,0.30)"); ng.addColorStop(1, "rgba(20,80,104,0)");
  g.fillStyle = ng; g.beginPath(); g.ellipse(360, 430, 200, 168, 0.3, 0, 6.2832); g.fill();
});

/** the chamber wall: big windowless panels with a cove of cyan strip light along the top, so the only brightness
 *  in shots 14-16 comes from fixtures that are physically in the room. */
export const makeNeonPanelTexture = () => mk(1024, 1024, (g) => {
  const gr = g.createLinearGradient(0, 0, 0, 1024);
  gr.addColorStop(0, "#243542"); gr.addColorStop(0.22, "#1a2836"); gr.addColorStop(1, "#141f2a");
  g.fillStyle = gr; g.fillRect(0, 0, 1024, 1024);
  const rand = rng(512);
  for (let i = 0; i < 4200; i++) {
    g.fillStyle = `rgba(${120 + rand() * 60 | 0},${160 + rand() * 60 | 0},${190 + rand() * 50 | 0},${0.02 + rand() * 0.05})`;
    g.fillRect(rand() * 1024, rand() * 1024, 2 + rand() * 26, 1);
  }
  // panel grid: 4 x 4 units, each with a lit seam on its top edge and a shadow line under it
  const s = 256;
  for (let y = 0; y < 4; y++) {
    for (let x = 0; x < 4; x++) {
      g.strokeStyle = "rgba(6,14,20,0.85)"; g.lineWidth = 9;
      g.strokeRect(x * s + 10, y * s + 12, s - 20, s - 24);
      g.strokeStyle = "rgba(122,232,255,0.30)"; g.lineWidth = 4;
      g.beginPath(); g.moveTo(x * s + 12, y * s + 12); g.lineTo(x * s + s - 12, y * s + 12); g.stroke();
      if ((x + y) % 2 === 0) {
        g.fillStyle = "rgba(96,180,214,0.05)"; g.fillRect(x * s + 22, y * s + 22, s - 44, s - 44);
      }
    }
  }
  // the cove: a continuous cyan strip the whole width, and its falloff below it
  const cg = g.createLinearGradient(0, 0, 0, 96);
  cg.addColorStop(0, "rgba(126,236,255,0.62)"); cg.addColorStop(0.3, "rgba(96,206,238,0.20)"); cg.addColorStop(1, "rgba(96,206,238,0)");
  g.fillStyle = cg; g.fillRect(0, 0, 1024, 96);
  g.fillStyle = "rgba(196,250,255,0.85)"; g.fillRect(0, 4, 1024, 7);
  // abstract service marks — deliberately glyph-shaped and deliberately unreadable
  g.strokeStyle = "rgba(150,222,244,0.22)";
  for (let i = 0; i < 26; i++) {
    g.lineWidth = 3 + rand() * 4;
    const x = rand() * 1000, y = 160 + rand() * 800;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + 14 + rand() * 60, y); g.stroke();
    g.beginPath(); g.arc(x + 78, y + 22, 6 + rand() * 10, 0, 6.2832); g.stroke();
  }
});

/** the chamber floor: a polished dark plate with a metric grid. The grid is what sells the room's size when the
 *  camera pulls back in shot 14, and the sheen streaks keep it from reading as a mat. */
export const makeLabFloorTexture = () => mk(512, 512, (g) => {
  g.fillStyle = "#1b2733"; g.fillRect(0, 0, 512, 512);
  const rand = rng(303);
  for (let i = 0; i < 2600; i++) {
    g.fillStyle = `rgba(${70 + rand() * 60 | 0},${110 + rand() * 60 | 0},${132 + rand() * 60 | 0},${0.02 + rand() * 0.05})`;
    g.fillRect(rand() * 512, rand() * 512, 2 + rand() * 30, 1 + rand() * 3);
  }
  g.strokeStyle = "rgba(12,20,28,0.95)"; g.lineWidth = 9;
  g.strokeRect(0, 0, 512, 512);
  g.strokeStyle = "rgba(122,226,255,0.30)"; g.lineWidth = 3;
  g.strokeRect(6, 6, 500, 500);
  // guide line down the middle of every slab, plus bolt pads at the corners
  g.strokeStyle = "rgba(150,232,255,0.14)"; g.lineWidth = 6;
  g.beginPath(); g.moveTo(256, 8); g.lineTo(256, 504); g.stroke();
  g.beginPath(); g.moveTo(8, 256); g.lineTo(504, 256); g.stroke();
  g.fillStyle = "rgba(160,236,255,0.30)";
  for (const [x, y] of [[42, 42], [470, 42], [42, 470], [470, 470]] as [number, number][]) {
    g.beginPath(); g.arc(x, y, 9, 0, 6.2832); g.fill();
  }
});

/** the three memory screens: 0 waveform, 1 concentric rings, 2 a tile field. All cyan, all abstract — the read
 *  the audience gets is the HUD pill, this is only the light the chamber is lit by. Each index is its OWN canvas
 *  because build.ts gives every screen a private material world.ts fades in one at a time. */
export const makeScreenTexture = (i: number) => mk(512, 256, (g) => {
  const gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, "#0a2230"); gr.addColorStop(1, "#061520");
  g.fillStyle = gr; g.fillRect(0, 0, 512, 256);
  const rand = rng(60 + i * 13);
  const cyan = "rgba(126,240,255,";
  if (i === 0) {
    // a waveform: a mirrored envelope plus a zero-line and its faint ticks
    g.strokeStyle = cyan + "0.28)"; g.lineWidth = 2;
    g.beginPath(); g.moveTo(16, 128); g.lineTo(496, 128); g.stroke();
    g.strokeStyle = cyan + "0.92)"; g.lineWidth = 3; g.lineJoin = "round";
    g.beginPath();
    for (let x = 16; x <= 496; x += 4) {
      const env = 0.35 + 0.65 * Math.abs(Math.sin(x * 0.021 + rand() * 0.02));
      const y = 128 - Math.sin(x * 0.12) * Math.sin(x * 0.026) * 92 * env;
      if (x === 16) g.moveTo(x, y); else g.lineTo(x, y);
    }
    g.stroke();
    g.strokeStyle = cyan + "0.34)"; g.lineWidth = 2;
    for (let x = 16; x < 496; x += 24) { g.beginPath(); g.moveTo(x, 216); g.lineTo(x + 10, 216); g.stroke(); }
  } else if (i === 1) {
    // concentric memory rings: one centre, uneven gaps, a couple of radial spokes
    const cx = 256, cy = 128;
    for (let k = 1; k <= 8; k++) {
      g.strokeStyle = cyan + `${(0.85 - k * 0.07).toFixed(2)})`; g.lineWidth = k % 3 === 0 ? 5 : 2;
      g.beginPath(); g.arc(cx, cy, k * 13 + rand() * 4, 0, 6.2832); g.stroke();
    }
    g.fillStyle = cyan + "0.95)"; g.beginPath(); g.arc(cx, cy, 9, 0, 6.2832); g.fill();
    g.strokeStyle = cyan + "0.42)"; g.lineWidth = 3;
    for (let k = 0; k < 5; k++) {
      const a = k * 1.27 + 0.4;
      g.beginPath(); g.moveTo(cx + Math.cos(a) * 30, cy + Math.sin(a) * 30); g.lineTo(cx + Math.cos(a) * 112, cy + Math.sin(a) * 112); g.stroke();
    }
  } else {
    // a tile field: 12 x 6 abstract blocks, some lit, some empty — "everything, all at once"
    const tw = 512 / 12, th = 256 / 6;
    for (let y = 0; y < 6; y++) for (let x = 0; x < 12; x++) {
      const k = rand();
      g.fillStyle = k > 0.72 ? cyan + "0.85)" : k > 0.45 ? cyan + "0.34)" : "rgba(24,70,92,0.6)";
      g.fillRect(x * tw + 4, y * th + 4, tw - 9, th - 9);
      if (k > 0.86) { g.strokeStyle = "rgba(226,255,255,0.9)"; g.lineWidth = 3; g.strokeRect(x * tw + 4, y * th + 4, tw - 9, th - 9); }
    }
  }
  // every screen shares the same furniture: a hot inner frame and a scanline veil, so the three read as one system
  g.fillStyle = "rgba(6,18,26,0.34)";
  for (let y = 0; y < 256; y += 4) g.fillRect(0, y, 512, 2);
  g.strokeStyle = "rgba(178,248,255,0.9)"; g.lineWidth = 6; g.strokeRect(3, 3, 506, 250);
  g.fillStyle = "rgba(126,240,255,0.16)"; g.fillRect(0, 0, 512, 14);
});

/** the "snow angle solved" read: a slope arc, a filled wedge, a ring of tick marks and a hair cross. Purely
 *  geometric — this is the one 3D readout in the film and it still has to carry no legible symbol. */
export const makeAngleReadTexture = () => mk(512, 512, (g) => {
  g.clearRect(0, 0, 512, 512);
  const cx = 256, cy = 320, R = 190;
  const a0 = -0.10, a1 = -0.95;
  // the measured slope, drawn as a wedge from the horizontal datum up to the failure angle
  g.fillStyle = "rgba(126,240,255,0.30)";
  g.beginPath(); g.moveTo(cx, cy);
  g.arc(cx, cy, R, a0, a1, true); g.closePath(); g.fill();
  g.strokeStyle = "rgba(186,250,255,0.95)"; g.lineWidth = 9;
  g.beginPath(); g.arc(cx, cy, R, a0, a1, true); g.stroke();
  g.lineWidth = 6;
  g.beginPath(); g.moveTo(cx - R * 0.2, cy); g.lineTo(cx + R * 1.16, cy); g.stroke();
  g.beginPath(); g.moveTo(cx, cy); g.lineTo(cx + Math.cos(a1) * R * 1.16, cy + Math.sin(a1) * R * 1.16); g.stroke();
  // tick ring, every fourth one long
  for (let i = 0; i <= 24; i++) {
    const a = a0 + ((a1 - a0) * i) / 24;
    const L = i % 4 === 0 ? 34 : 16;
    g.strokeStyle = i % 4 === 0 ? "rgba(232,255,255,1)" : "rgba(150,236,255,0.7)";
    g.lineWidth = i % 4 === 0 ? 7 : 4;
    g.beginPath();
    g.moveTo(cx + Math.cos(a) * (R - L), cy + Math.sin(a) * (R - L));
    g.lineTo(cx + Math.cos(a) * R, cy + Math.sin(a) * R);
    g.stroke();
  }
  // a hair cross and three datum dashes so the plate reads as an instrument, not an ornament
  g.strokeStyle = "rgba(198,250,255,0.9)"; g.lineWidth = 5;
  g.beginPath(); g.arc(392, 132, 34, 0, 6.2832); g.stroke();
  g.beginPath(); g.moveTo(348, 132); g.lineTo(436, 132); g.stroke();
  g.beginPath(); g.moveTo(392, 88); g.lineTo(392, 176); g.stroke();
  for (let i = 0; i < 3; i++) { g.fillStyle = "rgba(150,236,255,0.8)"; g.fillRect(60, 424 + i * 22, 150 - i * 44, 9); }
});

// ---------------- night road (shots 23-25) ----------------
/** suburban lap siding with a corner trim and a frieze, built for the house's +z face. The lit window and the
 *  door are separate meshes at ROAD.door, so this plate is intentionally openings-free. */
export const makeHouseFrontTexture = (o: { base?: string; board?: string; trim?: string } = {}) => {
  const base = o.base ?? "#4a4257";
  const board = o.board ?? "#332d3f";
  const trim = o.trim ?? "#6e6480";
  return mk(1024, 1024, (g) => {
    g.fillStyle = base; g.fillRect(0, 0, 1024, 1024);
    const rand = rng(999);
    // lap boards: a shadow line under every course, a lit line above it, staggered butt joints
    const ch = 46;
    for (let y = 0, row = 0; y < 1024; y += ch, row++) {
      g.fillStyle = board; g.fillRect(0, y + ch - 7, 1024, 7);
      g.fillStyle = "rgba(255,248,232,0.055)"; g.fillRect(0, y, 1024, 4);
      const jx = 90 + ((row * 337) % 860);
      g.fillStyle = "rgba(20,16,28,0.5)"; g.fillRect(jx, y, 5, ch - 7);
    }
    for (let i = 0; i < 3200; i++) {
      g.fillStyle = `rgba(${140 + rand() * 80 | 0},${130 + rand() * 70 | 0},${160 + rand() * 70 | 0},${0.015 + rand() * 0.05})`;
      g.fillRect(rand() * 1024, rand() * 1024, 2 + rand() * 18, 1 + rand() * 3);
    }
    // weather streaking under the eaves, and a darker skirt where the splashes come back off the pavement
    const sg = g.createLinearGradient(0, 1024, 0, 830);
    sg.addColorStop(0, "rgba(14,12,22,0.55)"); sg.addColorStop(1, "rgba(14,12,22,0)");
    g.fillStyle = sg; g.fillRect(0, 830, 1024, 194);
    const eg = g.createLinearGradient(0, 0, 0, 120);
    eg.addColorStop(0, "rgba(10,9,18,0.5)"); eg.addColorStop(1, "rgba(10,9,18,0)");
    g.fillStyle = eg; g.fillRect(0, 0, 1024, 120);
    // corner boards + a frieze band: the two verticals are what stop the box reading as a shed
    g.fillStyle = trim; g.fillRect(0, 0, 34, 1024); g.fillRect(990, 0, 34, 1024);
    g.fillRect(0, 990, 1024, 34);
    g.fillStyle = "rgba(210,220,240,0.20)"; g.fillRect(34, 990, 956, 5);
  });
};

/** the alien readout that rides the beam: rows of stems, hooks, bowls and bars. Abstract by law — the glyph that
 *  actually lands in the hero's fist is drawn on the 2D card in toon.ts. */
export const makeGlyphPlateTexture = () => mk(512, 256, (g) => {
  g.clearRect(0, 0, 512, 256);
  const gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, "rgba(10,40,54,0.30)"); gr.addColorStop(0.5, "rgba(18,74,96,0.22)"); gr.addColorStop(1, "rgba(10,40,54,0.30)");
  g.fillStyle = gr; g.fillRect(0, 0, 512, 256);
  g.strokeStyle = "rgba(150,244,255,0.75)"; g.lineWidth = 4; g.strokeRect(10, 10, 492, 236);
  const rand = rng(1234);
  const ink = "rgba(196,252,255,";
  for (let row = 0; row < 4; row++) {
    let x = 40;
    const y = 46 + row * 48;
    while (x < 452) {
      const w = 16 + rand() * 18, k = Math.floor(rand() * 6);
      g.strokeStyle = ink + `${(0.5 + rand() * 0.5).toFixed(2)})`; g.lineWidth = 4 + rand() * 3; g.lineCap = "round";
      g.beginPath();
      if (k === 0) { g.moveTo(x, y - 14); g.lineTo(x, y + 14); g.moveTo(x, y - 14); g.lineTo(x + w * 0.6, y - 6); }
      else if (k === 1) { g.arc(x + w * 0.4, y, w * 0.4, 0.3, 5.2); }
      else if (k === 2) { g.moveTo(x, y + 12); g.lineTo(x + w * 0.5, y - 13); g.lineTo(x + w, y + 12); }
      else if (k === 3) { g.moveTo(x, y - 12); g.lineTo(x + w, y - 12); g.moveTo(x + w * 0.5, y - 12); g.lineTo(x + w * 0.5, y + 12); g.moveTo(x + w * 0.2, y + 12); g.lineTo(x + w * 0.8, y + 12); }
      else if (k === 4) { g.moveTo(x, y); g.lineTo(x + w, y); g.moveTo(x + w * 0.7, y - 9); g.lineTo(x + w, y); g.lineTo(x + w * 0.7, y + 9); }
      else { g.arc(x + w * 0.4, y, w * 0.36, 0, 6.2832); g.moveTo(x + w * 0.4, y - w * 0.5); g.lineTo(x + w * 0.4, y + w * 0.5); }
      g.stroke();
      x += w + 14 + rand() * 12;
    }
  }
  g.fillStyle = "rgba(150,244,255,0.30)"; g.fillRect(30, 122, 452, 3);
});

/** the beam column: alpha only, faded at both caps and at both lateral edges, so a cone mesh looks like light
 *  that has nowhere to land rather than a painted bucket. build.ts lays it point-first out of the disc. */
export const makeBeamTexture = () => mk(256, 512, (g) => {
  g.clearRect(0, 0, 256, 512);
  for (let x = 0; x < 256; x++) {
    const dx = Math.abs(x - 128) / 128;
    const side = Math.pow(1 - dx, 2.2);
    for (let y = 0; y < 512; y++) {
      const v = y / 511;
      const along = Math.pow(v, 0.75) * (1 - 0.72 * Math.pow(v, 4.2));
      const a = side * along * (0.72 + 0.28 * Math.sin(x * 0.12 + v * 22));
      g.fillStyle = `rgba(255,255,255,${Math.max(0, Math.min(1, a)).toFixed(3)})`;
      g.fillRect(x, y, 1, 1);
    }
  }
});
