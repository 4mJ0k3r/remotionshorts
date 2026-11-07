// Procedural canvas textures for ElevatorCrushShort:
// brushed steel, warm wood trim, brushed brass, rain-streaked window, LED floor indicator,
// control-panel label, hoist cable, and the ground contact shadow blob.
import * as THREE from "three";

// Deterministic PRNG (mulberry32) so every Remotion render worker paints identical textures.
let _seed = 0x5eed1234;
const R = () => {
  _seed |= 0; _seed = (_seed + 0x6d2b79f5) | 0;
  let t = Math.imul(_seed ^ (_seed >>> 15), 1 | _seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

/** Create a canvas texture with mipmapping & sRGB encoding */
export function tex(w: number, h: number, draw: (ctx: CanvasRenderingContext2D, w: number, h: number) => void): THREE.CanvasTexture {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d")!;
  draw(ctx, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = THREE.RepeatWrapping;
  t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8;
  return t;
}

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

/** Ground contact shadow blob */
export function makeBlobTexture(): THREE.CanvasTexture {
  return tex(128, 128, (g) => {
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, "rgba(0, 0, 0, 0.85)");
    grad.addColorStop(0.5, "rgba(0, 0, 0, 0.45)");
    grad.addColorStop(1, "rgba(0, 0, 0, 0.0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, 128, 128);
  });
}
