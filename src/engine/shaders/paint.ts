// Procedural canvas textures for the coaster sets (no image assets): grass, dirt, wood planks, red/cream deck planks,
// concrete, the "FRANK'S LOOP" blueprint board and the cart's side banner. Flat paint with light wear.
import * as THREE from "three";

const rnd = (i: number) => { const v = Math.sin(i * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };

export const tex = (w: number, h: number, draw: (g: CanvasRenderingContext2D, w: number, h: number) => void, repeat?: [number, number]) => {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  _seed = 0x5eed1234;
  draw(c.getContext("2d")!, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  return t;
};

/** flat grass with darker tufts and lighter flecks */
export const grass = (base = "#4da83b", rep: [number, number] = [60, 60]) => tex(512, 512, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 900; i++) {
    const x = rnd(i) * w, y = rnd(i + 5000) * h, s = 2 + rnd(i + 9000) * 5;
    g.fillStyle = i % 3 ? "rgba(40,110,40,0.32)" : "rgba(170,220,110,0.28)";
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + s * 0.5, y - s * 2.2); g.lineTo(x + s, y); g.fill();
  }
  for (let i = 0; i < 26; i++) {
    g.fillStyle = "rgba(30,90,30,0.12)";
    g.beginPath(); g.ellipse(rnd(i + 300) * w, rnd(i + 700) * h, 20 + rnd(i) * 40, 10 + rnd(i + 1) * 20, 0, 0, Math.PI * 2); g.fill();
  }
}, rep);

/** packed dirt, warm orange-brown with pebbles */
export const dirt = (base = "#b86b43", rep: [number, number] = [4, 4]) => tex(512, 512, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 700; i++) {
    const x = rnd(i + 40) * w, y = rnd(i + 4040) * h, r = 1 + rnd(i + 8040) * 4;
    g.fillStyle = i % 2 ? "rgba(120,60,30,0.35)" : "rgba(230,170,120,0.3)";
    g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
  }
  for (let i = 0; i < 12; i++) {
    g.strokeStyle = "rgba(110,55,28,0.25)"; g.lineWidth = 3;
    g.beginPath(); const y = rnd(i + 99) * h; g.moveTo(0, y); g.bezierCurveTo(w * 0.3, y + 20, w * 0.6, y - 20, w, y + 6); g.stroke();
  }
}, rep);

/** wood planks running along u, with seams, grain and nail dots */
export const planks = (a = "#c08850", b = "#a8723e", n = 6, rep: [number, number] = [1, 1], seam = "#5a3420") => tex(512, 512, (g, w, h) => {
  const ph = h / n;
  for (let i = 0; i < n; i++) {
    g.fillStyle = i % 2 ? a : b; g.fillRect(0, i * ph, w, ph);
    g.strokeStyle = "rgba(90,50,25,0.28)"; g.lineWidth = 2;
    for (let k = 0; k < 4; k++) {
      const y = i * ph + ph * (0.2 + 0.2 * k) + (rnd(i * 7 + k) - 0.5) * 6;
      g.beginPath(); g.moveTo(0, y); g.bezierCurveTo(w * 0.3, y + 4, w * 0.7, y - 4, w, y + 2); g.stroke();
    }
    const cut = rnd(i + 33) * w;
    g.fillStyle = seam; g.fillRect(cut, i * ph, 4, ph);
    g.fillStyle = "rgba(60,35,20,0.7)";
    for (const x of [cut - 14, cut + 18]) { g.beginPath(); g.arc(x, i * ph + ph * 0.3, 3, 0, 7); g.arc(x, i * ph + ph * 0.7, 3, 0, 7); g.fill(); }
  }
  g.fillStyle = seam;
  for (let i = 0; i <= n; i++) g.fillRect(0, i * ph - 2, w, 4);
}, rep);

/** red / cream alternating deck boards */
export const deckPlanks = () => planks("#d24a3a", "#f3e6c8", 8, [1, 1], "#6a2a22");

export const concrete = () => tex(256, 256, (g, w, h) => {
  g.fillStyle = "#c9c4b8"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 400; i++) { g.fillStyle = i % 2 ? "rgba(90,90,90,0.12)" : "rgba(255,255,255,0.15)"; g.fillRect(rnd(i) * w, rnd(i + 77) * h, 2, 2); }
  g.strokeStyle = "rgba(80,80,80,0.25)"; g.lineWidth = 2; g.beginPath(); g.moveTo(30, 40); g.lineTo(90, 120); g.lineTo(80, 200); g.stroke();
});

/** "THE ORIGINAL / FRANK'S LOOP" dark slate blueprint with a white border and a drawn white loop diagram */
export const blueprint = () => tex(1024, 800, (g, w, h) => {
  g.fillStyle = "#24323f"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "rgba(255,255,255,0.08)"; g.lineWidth = 2;
  for (let x = 0; x < w; x += 48) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
  for (let y = 0; y < h; y += 48) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
  g.strokeStyle = "#f6f2e8"; g.lineWidth = 16; g.strokeRect(22, 22, w - 44, h - 44);
  g.textAlign = "center"; g.textBaseline = "middle";
  g.fillStyle = "#e8443a"; g.font = "900 78px Arial"; g.fillText("THE ORIGINAL", w / 2, 110);
  g.fillStyle = "#ffffff"; g.font = "900 118px Arial"; g.fillText("FRANK'S LOOP", w / 2, 230);
  // loop diagram: circle + lead-in / lead-out track + dimension marks
  g.strokeStyle = "#ffffff"; g.lineWidth = 12;
  g.beginPath(); g.arc(w / 2, 505, 170, 0, Math.PI * 2); g.stroke();
  g.beginPath(); g.moveTo(130, 690); g.lineTo(w / 2 - 20, 680); g.moveTo(w / 2 + 20, 680); g.lineTo(w - 130, 690); g.stroke();
  g.lineWidth = 5; g.setLineDash([16, 12]);
  g.beginPath(); g.moveTo(w / 2, 335); g.lineTo(w / 2, 675); g.moveTo(w / 2 - 170, 505); g.lineTo(w / 2 + 170, 505); g.stroke();
  g.setLineDash([]);
  g.font = "700 40px Arial"; g.fillText("R = 7.5 m", w / 2 + 300, 430);
  g.beginPath(); g.moveTo(w / 2 + 300, 460); g.lineTo(w / 2 + 120, 500); g.stroke();
});

/** white banner panel for the cart's side */
export const banner = () => tex(512, 128, (g, w, h) => {
  g.fillStyle = "#fbf6ea"; g.fillRect(0, 0, w, h);
  g.fillStyle = "#d8402e"; g.fillRect(0, 0, w, 12); g.fillRect(0, h - 12, w, 12);
  const s = "UPSIDE-DOWNER";
  let px = 70;
  g.font = "900 " + px + "px Arial";
  while (g.measureText(s).width > w - 36 && px > 20) { px -= 2; g.font = "900 " + px + "px Arial"; }
  g.fillStyle = "#c2352a"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(s, w / 2, h / 2 + 3);
});

/** low-poly cloud-free sky fallback is the world shader; this is the board for easel back / crate labels */
export const crateLabel = (s: string) => tex(256, 128, (g, w, h) => {
  g.fillStyle = "#d9b27a"; g.fillRect(0, 0, w, h);
  g.fillStyle = "#5a3420"; g.font = "900 48px Arial"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(s, w / 2, h / 2);
});

// Elevator cabin textures. Each paint call restarts its PRNG for worker/order independence.
let _seed = 0x5eed1234;
const R = () => { _seed |= 0; _seed = (_seed + 0x6d2b79f5) | 0; let t = Math.imul(_seed ^ (_seed >>> 15), 1 | _seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
/** Brushed stainless steel (elevator walls / doors) */
export function makeSteelTexture(base = "#aeb6bd", dark = "#8a939b"): THREE.CanvasTexture {
  return tex(512, 512, (g, w, h) => {
    g.fillStyle = base;
    g.fillRect(0, 0, w, h);
    // Vertical brushed streaks
    for (let i = 0; i < 900; i++) {
      const x = R() * w;
      const a = R() * 0.10;
      g.fillStyle = R() > 0.5 ? `rgba(255,255,255,${a})` : `rgba(20,26,32,${a})`;
      g.fillRect(x, 0, 1 + R() * 2, h);
    }
    // Subtle horizontal sheen bands
    for (let y = 0; y < h; y += 64) {
      g.fillStyle = "rgba(255,255,255,0.05)";
      g.fillRect(0, y, w, 8);
    }
    // Slight vignette per panel
    const gr = g.createLinearGradient(0, 0, 0, h);
    gr.addColorStop(0, "rgba(255,255,255,0.06)");
    gr.addColorStop(0.5, "rgba(0,0,0,0)");
    gr.addColorStop(1, "rgba(0,0,0,0.10)");
    g.fillStyle = gr;
    g.fillRect(0, 0, w, h);
    void dark;
  });
}

/** Warm wood trim (elevator cabin handrail / ceiling trim) */
export function makeWoodTrimTexture(): THREE.CanvasTexture {
  return tex(512, 256, (g, w, h) => {
    g.fillStyle = "#9a6b42";
    g.fillRect(0, 0, w, h);
    const planks = 4;
    const ph = h / planks;
    for (let i = 0; i < planks; i++) {
      const y = i * ph;
      const shade = ((i * 23) % 5) - 2;
      g.fillStyle = `rgb(${154 + shade * 10},${107 + shade * 8},${66 + shade * 5})`;
      g.fillRect(0, y + 2, w, ph - 4);
      // grain
      g.fillStyle = "rgba(50,30,15,0.22)";
      for (let k = 0; k < 14; k++) {
        g.fillRect(R() * w, y + 4 + R() * (ph - 8), 2 + R() * 3, ph - 8);
      }
      g.fillStyle = "#4a2f1a";
      g.fillRect(0, y, w, 3);
    }
  });
}

/** Brushed brass (control panel face) */
export function makeBrassTexture(): THREE.CanvasTexture {
  return tex(512, 512, (g, w, h) => {
    g.fillStyle = "#c9a24a";
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 700; i++) {
      const x = R() * w;
      const a = R() * 0.08;
      g.fillStyle = R() > 0.5 ? `rgba(255,240,200,${a})` : `rgba(90,60,20,${a})`;
      g.fillRect(x, 0, 1 + R() * 2, h);
    }
  });
}

/** Rain-streaked glass window (corridor, monsoon outside) — animated streaks added in world.ts via redraw */
export function makeRainWindowTexture(): THREE.CanvasTexture {
  return tex(512, 768, (g, w, h) => {
    // Blue monsoon night sky gradient outside
    const gr = g.createLinearGradient(0, 0, 0, h);
    gr.addColorStop(0, "#16305a");
    gr.addColorStop(0.5, "#1e4a86");
    gr.addColorStop(1, "#0c1c3a");
    g.fillStyle = gr;
    g.fillRect(0, 0, w, h);
    // Distant city glow blobs
    for (let i = 0; i < 22; i++) {
      const x = R() * w, y = h * 0.45 + R() * h * 0.5;
      const r = 6 + R() * 22;
      const rg = g.createRadialGradient(x, y, 0, x, y, r);
      rg.addColorStop(0, "rgba(255,214,120,0.85)");
      rg.addColorStop(1, "rgba(255,214,120,0)");
      g.fillStyle = rg;
      g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
    }
    // Rain streaks
    g.strokeStyle = "rgba(170,210,255,0.55)";
    g.lineWidth = 2;
    for (let i = 0; i < 90; i++) {
      const x = R() * w, y = R() * h, len = 20 + R() * 70;
      g.beginPath(); g.moveTo(x, y); g.lineTo(x - 3, y + len); g.stroke();
    }
  });
}

/** Redraw the rain window with fresh animated streak positions (called each frame in Shot 2) */
export function redrawRainWindow(t: THREE.CanvasTexture, seed: number): void {
  const c = t.image as HTMLCanvasElement;
  const g = c.getContext("2d")!;
  const w = c.width, h = c.height;
  const gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, "#16305a");
  gr.addColorStop(0.5, "#1e4a86");
  gr.addColorStop(1, "#0c1c3a");
  g.fillStyle = gr;
  g.fillRect(0, 0, w, h);
  for (let i = 0; i < 22; i++) {
    const x = ((i * 137 + seed * 53) % w + w) % w;
    const y = h * 0.45 + ((i * 211 + seed * 31) % (h * 0.5));
    const r = 6 + (i % 5) * 4;
    const rg = g.createRadialGradient(x, y, 0, x, y, r);
    rg.addColorStop(0, "rgba(255,214,120,0.85)");
    rg.addColorStop(1, "rgba(255,214,120,0)");
    g.fillStyle = rg;
    g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill();
  }
  g.strokeStyle = "rgba(170,210,255,0.6)";
  g.lineWidth = 2;
  for (let i = 0; i < 110; i++) {
    const x = ((i * 89 + seed * 67) % w + w) % w;
    const y = ((i * 151 + seed * 97) % h + h) % h;
    const len = 20 + (i % 6) * 12;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x - 3, y + len); g.stroke();
  }
  t.needsUpdate = true;
}

/** Digital red LED floor indicator — returns a texture plus a redraw(text) handle */
export function makeLEDTexture(): { tex: THREE.CanvasTexture; redraw: (text: string, flash: boolean) => void } {
  const c = document.createElement("canvas");
  c.width = 512; c.height = 192;
  const g = c.getContext("2d")!;
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  const redraw = (text: string, flash: boolean) => {
    g.fillStyle = "#12060a";
    g.fillRect(0, 0, c.width, c.height);
    // dark bezel inner
    g.fillStyle = "#1c0a10";
    g.fillRect(10, 10, c.width - 20, c.height - 20);
    // `flash` = the dim half of a blink cycle (world.ts drives it from the frame number — deterministic).
    g.textAlign = "center";
    g.textBaseline = "middle";
    const size = text.length > 9 ? 64 : 92;
    if (flash) {
      g.font = `900 ${size}px 'Arial Black', monospace`;
      g.fillStyle = "#5a1414";
      g.fillText(text, c.width / 2, c.height / 2 + 2);
    } else {
      g.font = `900 ${size}px 'Arial Black', 'Segoe UI Black', monospace`;
      g.shadowColor = "#ff2a2a";
      g.shadowBlur = 26;
      g.fillStyle = "#ff3b30";
      g.fillText(text, c.width / 2, c.height / 2 + 4);
      g.shadowBlur = 0;
      g.fillStyle = "#ff8a80";
      g.font = `900 ${size - 4}px 'Arial Black', monospace`;
      g.fillText(text, c.width / 2, c.height / 2 + 2);
    }
    t.needsUpdate = true;
  };
  redraw("FLOOR 4", false);
  return { tex: t, redraw };
}

/** Control panel label plate (small text under the brass buttons) */
export function makePanelLabelTexture(): THREE.CanvasTexture {
  return tex(256, 512, (g, w, h) => {
    g.fillStyle = "#2a2118";
    g.fillRect(0, 0, w, h);
    g.fillStyle = "#e8d9b0";
    g.textAlign = "center";
    g.textBaseline = "middle";
    const labels = ["4", "3", "2", "1", "G", "FAN"];
    // labels on the left half; the 3D buttons sit on the right half of each row (build.ts)
    g.strokeStyle = "#8a6a2a";
    g.lineWidth = 6;
    g.strokeRect(8, 8, w - 16, h - 16);
    for (let i = 0; i < labels.length; i++) {
      g.font = labels[i].length > 1 ? "900 40px 'Arial Black', sans-serif" : "900 56px 'Arial Black', sans-serif";
      g.fillText(labels[i], w * 0.3, 48 + i * 78);
    }
  });
}

/** Hoist cable (dark steel rope) */
export function makeCableTexture(): THREE.CanvasTexture {
  return tex(64, 256, (g, w, h) => {
    g.fillStyle = "#3a3f45";
    g.fillRect(0, 0, w, h);
    g.strokeStyle = "rgba(0,0,0,0.5)";
    g.lineWidth = 3;
    for (let i = 0; i < 6; i++) {
      g.beginPath();
      g.moveTo(i * 12 + 3, 0);
      g.lineTo(i * 12 - 3, h);
      g.stroke();
    }
    g.strokeStyle = "rgba(255,255,255,0.18)";
    g.lineWidth = 2;
    for (let i = 0; i < 6; i++) {
      g.beginPath();
      g.moveTo(i * 12 + 6, 0);
      g.lineTo(i * 12, h);
      g.stroke();
    }
  });
}

/** Opaque multiply contact shadow: white exterior leaves the ground unchanged. */
export function makeBlobTexture(color = "#594757"): THREE.CanvasTexture {
  const t = tex(128, 128, (g, w, h) => {
    g.fillStyle = "#ffffff"; g.fillRect(0, 0, w, h);
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, color); grad.addColorStop(0.35, color); grad.addColorStop(1, "#ffffff");
    g.fillStyle = grad; g.fillRect(0, 0, w, h);
  });
  t.generateMipmaps = false; t.minFilter = THREE.LinearFilter;
  return t;
}
