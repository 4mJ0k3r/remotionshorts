// Hand-painted canvas textures for the four school zones: floors, classroom walls and blackboard, locker banks,
// black marble lab benches, the school facade and the plaza pavers. Everything is drawn in 2D and mapped by build.ts.
import * as THREE from "three";

const rnd = (i: number) => { const v = Math.sin(i * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };

export const tex = (w: number, h: number, draw: (g: CanvasRenderingContext2D, w: number, h: number) => void) => {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  const g = c.getContext("2d")!;
  draw(g, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
};

const grain = (g: CanvasRenderingContext2D, w: number, h: number, a: number, n = 900, seed = 1) => {
  for (let i = 0; i < n; i++) {
    const x = rnd(i * 3 + seed) * w, y = rnd(i * 7 + seed * 2) * h, s = 1 + rnd(i * 11 + seed) * 3;
    g.fillStyle = `rgba(0,0,0,${a * (0.3 + 0.7 * rnd(i + seed))})`;
    g.fillRect(x, y, s, s * (0.4 + rnd(i * 5) * 2));
  }
};

export const woodFloor = (base: string, seam: string) => tex(1024, 1024, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  const rows = 8, rh = h / rows;
  for (let r = 0; r < rows; r++) {
    const y = r * rh;
    g.fillStyle = r % 2 ? "rgba(255,255,255,0.035)" : "rgba(0,0,0,0.045)";
    g.fillRect(0, y, w, rh);
    for (let k = 0; k < 20; k++) {
      g.strokeStyle = `rgba(60,30,18,${0.05 + 0.06 * rnd(r * 31 + k)})`;
      g.lineWidth = 1 + rnd(k) * 2;
      const yy = y + 6 + rnd(k * 7 + r) * (rh - 12);
      g.beginPath(); g.moveTo(0, yy);
      for (let x = 0; x <= w; x += 64) g.lineTo(x, yy + Math.sin(x * 0.01 + k + r) * 2.5);
      g.stroke();
    }
    g.fillStyle = seam; g.fillRect(0, y + rh - 2, w, 2);
    const cut = Math.floor(rnd(r * 13 + 2) * w);
    g.fillRect(cut, y, 3, rh);
  }
  grain(g, w, h, 0.05, 1200, 6);
});

export const tileFloor = (a: string, b: string, n: number) => tex(1024, 1024, (g, w, h) => {
  const s = w / n;
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    g.fillStyle = (x + y) % 2 ? b : a; g.fillRect(x * s, y * s, s, s);
    g.fillStyle = "rgba(255,255,255,0.06)"; g.fillRect(x * s + 4, y * s + 4, s - 8, 3);
  }
  g.strokeStyle = "rgba(30,30,36,0.25)"; g.lineWidth = 2;
  for (let i = 0; i <= n; i++) { g.beginPath(); g.moveTo(i * s, 0); g.lineTo(i * s, h); g.stroke(); g.beginPath(); g.moveTo(0, i * s); g.lineTo(w, i * s); g.stroke(); }
  grain(g, w, h, 0.03, 500, 9);
});

export const wallPaint = (base: string, shade: string, trim = true) => tex(512, 512, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, base); gr.addColorStop(1, shade);
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  if (trim) {
    g.fillStyle = "rgba(255,255,255,0.05)"; g.fillRect(0, h - 96, w, 4);
    g.fillStyle = "rgba(30,30,36,0.06)"; g.fillRect(0, h - 92, w, 2);
  }
  grain(g, w, h, 0.035, 700, 3);
});

export const blackboard = () => tex(1024, 512, (g, w, h) => {
  g.fillStyle = "#203a30"; g.fillRect(0, 0, w, h);
  g.fillStyle = "rgba(255,255,255,0.035)"; g.fillRect(0, 0, w, 14);
  g.strokeStyle = "rgba(240,244,232,0.7)"; g.lineWidth = 4; g.lineCap = "round";
  g.font = "700 58px 'Courier New', monospace"; g.fillStyle = "rgba(240,244,232,0.78)"; g.textAlign = "left";
  g.fillText("a² + b² = c²", 70, 110);
  g.font = "700 44px 'Courier New', monospace"; g.fillText("H2O + CO2 → H2CO3", 70, 190);
  g.strokeStyle = "rgba(240,244,232,0.5)"; g.lineWidth = 3;
  g.beginPath(); g.arc(760, 140, 58, 0, Math.PI * 2); g.stroke();
  g.beginPath(); g.moveTo(690, 220); g.lineTo(760, 140); g.lineTo(830, 220); g.stroke();
  for (let i = 0; i < 5; i++) { g.beginPath(); g.moveTo(90 + i * 46, 300); g.lineTo(150 + i * 46, 320); g.stroke(); }
  for (let i = 0; i < 900; i++) {
    g.fillStyle = `rgba(255,255,255,${0.02 + rnd(i) * 0.05})`;
    g.fillRect(rnd(i * 3) * w, rnd(i * 7) * h, 2 + rnd(i) * 8, 1.5);
  }
  g.textAlign = "left";
});

export const lockers = (base: string, trim: string) => tex(1024, 1024, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  const cols = 4, rows = 5, cw = w / cols, ch = h / rows;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const x = c * cw, y = r * ch;
    const d = 0.06 + rnd(r * 9 + c) * 0.05;
    g.fillStyle = `rgba(0,0,0,${d})`; g.fillRect(x + 3, y + 3, cw - 6, ch - 6);
    g.fillStyle = "rgba(255,255,255,0.09)"; g.fillRect(x + 6, y + 6, cw - 12, 3);
    g.strokeStyle = trim; g.lineWidth = 3; g.strokeRect(x + 5, y + 5, cw - 10, ch - 10);
    // vent slats
    g.fillStyle = "rgba(20,26,32,0.5)";
    for (let i = 0; i < 4; i++) g.fillRect(x + cw * 0.2, y + ch * 0.12 + i * 12, cw * 0.36, 4);
    // handle + number plate
    g.fillStyle = trim; g.fillRect(x + cw * 0.66, y + ch * 0.46, 10, 44);
    g.fillStyle = "rgba(230,240,250,0.55)"; g.font = "700 26px Arial"; g.textAlign = "center";
    g.fillText(String(100 + r * cols + c), x + cw / 2, y + ch * 0.78);
  }
  grain(g, w, h, 0.04, 600, 17);
});

export const marble = (base: string, vein: string) => tex(1024, 1024, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 26; i++) {
    g.strokeStyle = vein; g.globalAlpha = 0.16 + rnd(i) * 0.34; g.lineWidth = 1 + rnd(i * 3) * 3;
    g.beginPath();
    let x = rnd(i * 7) * w, y = rnd(i * 11) * h;
    g.moveTo(x, y);
    for (let k = 0; k < 9; k++) { x += (rnd(i * 13 + k) - 0.5) * 130; y += (rnd(i * 17 + k) - 0.5) * 90; g.lineTo(x, y); }
    g.stroke();
  }
  g.globalAlpha = 1;
  for (let i = 0; i < 900; i++) {
    g.fillStyle = `rgba(255,255,255,${0.015 + rnd(i) * 0.05})`;
    g.fillRect(rnd(i * 3) * w, rnd(i * 7) * h, 1 + rnd(i) * 3, 1 + rnd(i * 5) * 3);
  }
});

export const asphalt = () => tex(1024, 1024, (g, w, h) => {
  g.fillStyle = "#6a6c70"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 2600; i++) {
    g.fillStyle = `rgba(${40 + rnd(i) * 90},${40 + rnd(i) * 90},${44 + rnd(i) * 90},${0.04 + rnd(i * 7) * 0.1})`;
    g.fillRect(rnd(i * 3) * w, rnd(i * 7) * h, 1 + rnd(i) * 4, 1 + rnd(i * 5) * 3);
  }
  g.strokeStyle = "rgba(30,30,34,0.35)"; g.lineWidth = 2;
  for (let i = 0; i < 7; i++) {
    g.beginPath(); let x = rnd(i * 5) * w, y = rnd(i * 9) * h; g.moveTo(x, y);
    for (let k = 0; k < 6; k++) { x += (rnd(i + k) - 0.5) * 120; y += rnd(i * 3 + k) * 70; g.lineTo(x, y); }
    g.stroke();
  }
});

export const pavers = () => tex(1024, 1024, (g, w, h) => {
  const s = 128;
  for (let y = 0; y < h; y += s) for (let x = 0; x < w; x += s) {
    g.fillStyle = (x / s + y / s) % 2 ? "#b8b0a2" : "#c4bcae"; g.fillRect(x, y, s, s);
    g.fillStyle = "rgba(60,56,50,0.18)"; g.fillRect(x, y + s - 3, s, 3); g.fillRect(x + s - 3, y, 3, s);
    g.fillStyle = "rgba(255,255,255,0.05)"; g.fillRect(x + 4, y + 4, s - 10, 2);
  }
  grain(g, w, h, 0.04, 900, 23);
});

export const facade = (base: string, band: string) => tex(1024, 1024, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 64) {
    g.fillStyle = "rgba(0,0,0,0.05)"; g.fillRect(0, y + 60, w, 4);
    if ((y / 64) % 5 === 0) { g.fillStyle = band; g.fillRect(0, y, w, 22); }
  }
  for (let x = 0; x < w; x += 256) { g.fillStyle = "rgba(255,255,255,0.04)"; g.fillRect(x, 0, 3, h); }
  grain(g, w, h, 0.035, 700, 29);
});

export const periodic = () => tex(1024, 512, (g, w, h) => {
  g.fillStyle = "#e8ece4"; g.fillRect(0, 0, w, h);
  g.fillStyle = "#2a4a58"; g.font = "700 44px Arial"; g.textAlign = "center"; g.fillText("PERIODIC TABLE", w / 2, 56);
  const cols = 18, rows = 7, cw = (w - 80) / cols, ch = 44;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    if ((c > 1 && c < 12) && r > 2) continue;
    const x = 40 + c * cw, y = 84 + r * ch;
    g.fillStyle = `hsl(${24 + rnd(r * 19 + c) * 300},52%,62%)`; g.fillRect(x + 2, y + 2, cw - 4, ch - 4);
    g.fillStyle = "rgba(20,24,30,0.8)"; g.font = "700 12px Arial"; g.fillText(String(1 + r * cols + c), x + cw / 2, y + 18);
  }
  g.textAlign = "left";
});

export const sciencePoster = () => tex(512, 700, (g, w, h) => {
  g.fillStyle = "#f0ead8"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#2a4a58"; g.lineWidth = 10; g.strokeRect(10, 10, w - 20, h - 20);
  g.fillStyle = "#2a4a58"; g.font = "700 52px Arial"; g.textAlign = "center"; g.fillText("SCIENCE", w / 2, 78);
  g.font = "700 30px Arial"; g.fillText("LAB RULES", w / 2, 120);
  g.strokeStyle = "#4a6a72"; g.lineWidth = 8;
  g.beginPath(); g.moveTo(120, 470); g.lineTo(170, 250); g.lineTo(230, 330); g.lineTo(290, 230); g.lineTo(390, 470); g.closePath(); g.stroke();
  for (const [x, y, r] of [[190, 420, 16], [250, 380, 12], [310, 400, 20], [350, 340, 9]] as const) { g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fillStyle = "#7fc8d8"; g.fill(); g.stroke(); }
  g.fillStyle = "#2a4a58"; g.font = "700 24px Arial";
  g.fillText("GOGGLES ON", w / 2, 560); g.fillText("NO FOOD", w / 2, 596); g.fillText("REPORT SPILLS", w / 2, 632);
  g.textAlign = "left";
});

export const schoolSign = () => tex(1024, 256, (g, w, h) => {
  g.fillStyle = "#203048"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#d8c070"; g.lineWidth = 8; g.strokeRect(12, 12, w - 24, h - 24);
  g.fillStyle = "#f4f0e2"; g.font = "700 110px Georgia, serif"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText("RIVERSIDE HIGH", w / 2, h / 2 + 4);
  g.textAlign = "left"; g.textBaseline = "alphabetic";
});

export const ceiling = (base: string) => tex(512, 512, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  g.strokeStyle = "rgba(50,54,60,0.22)"; g.lineWidth = 3; g.strokeRect(0, 0, w, h);
  grain(g, w, h, 0.025, 300, 33);
});
