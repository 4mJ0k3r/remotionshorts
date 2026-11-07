// Procedural canvas textures for "Tower Jump" (no image assets): asphalt with lane markings, Portland-stone blocks
// with painted gothic windows, river water, plaza pavers, slate, red/white barrier stripes, and every in-world label
// ("TOWER BRIDGE", "6 FT GAP AHEAD", "78 LONDON", "LONDON TRANSPORT", the SAFE LANDING chalkboard).
import * as THREE from "three";

const rnd = (i: number) => { const v = Math.sin(i * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
export const tex = (w: number, h: number, draw: (g: CanvasRenderingContext2D, w: number, h: number) => void, repeat?: [number, number]) => {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  draw(c.getContext("2d")!, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  return t;
};
/** text fitted to a max width */
const fit = (g: CanvasRenderingContext2D, s: string, x: number, y: number, px: number, maxW: number, weight = 900, fam = "Arial") => {
  let k = px; g.font = `${weight} ${k}px ${fam}`;
  while (g.measureText(s).width > maxW && k > 8) { k -= 2; g.font = `${weight} ${k}px ${fam}`; }
  g.fillText(s, x, y);
};

/** dark asphalt; u runs along the road: dashed centre line, solid edge lines, wear patches */
export const asphalt = (rep: [number, number] = [1, 1], lanes = true) => tex(1024, 512, (g, w, h) => {
  g.fillStyle = "#3b3d42"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 2600; i++) { g.fillStyle = i % 2 ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.12)"; g.fillRect(rnd(i) * w, rnd(i + 7) * h, 2, 2); }
  for (let i = 0; i < 10; i++) { g.fillStyle = "rgba(20,20,24,0.18)"; g.beginPath(); g.ellipse(rnd(i + 50) * w, rnd(i + 90) * h, 60, 18, 0, 0, 7); g.fill(); }
  if (!lanes) return;
  g.fillStyle = "#f2f0e6";
  g.fillRect(0, h * 0.07, w, 10); g.fillRect(0, h * 0.93 - 10, w, 10);
  for (let x = 20; x < w; x += 170) g.fillRect(x, h / 2 - 7, 100, 14);
}, rep);

/** Portland stone blocks; `windows` paints two rows of pointed gothic windows with dark glass */
export const stone = (base = "#cdbf9f", windows = false) => tex(512, 1024, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  const bh = 32;
  for (let r = 0; r * bh < h; r++) {
    const off = r % 2 ? 48 : 0;
    g.fillStyle = "rgba(90,74,52,0.35)"; g.fillRect(0, r * bh, w, 3);
    for (let x = off; x < w; x += 96) g.fillRect(x, r * bh, 3, bh);
    for (let x = off; x < w; x += 96) { g.fillStyle = `rgba(${rnd(r * 9 + x) > 0.5 ? "255,250,235" : "120,100,70"},0.10)`; g.fillRect(x + 4, r * bh + 4, 88, bh - 6); g.fillStyle = "rgba(90,74,52,0.35)"; }
  }
  if (!windows) return;
  const win = (cx: number, top: number, ww: number, hh: number) => {
    g.fillStyle = "#e9dfc6"; g.beginPath(); g.moveTo(cx - ww / 2 - 10, top + hh + 8); g.lineTo(cx - ww / 2 - 10, top + ww * 0.5);
    g.quadraticCurveTo(cx - ww / 2 - 10, top - 14, cx, top - 26); g.quadraticCurveTo(cx + ww / 2 + 10, top - 14, cx + ww / 2 + 10, top + ww * 0.5);
    g.lineTo(cx + ww / 2 + 10, top + hh + 8); g.closePath(); g.fill();
    g.fillStyle = "#24304a"; g.beginPath(); g.moveTo(cx - ww / 2, top + hh); g.lineTo(cx - ww / 2, top + ww * 0.5);
    g.quadraticCurveTo(cx - ww / 2, top, cx, top - 12); g.quadraticCurveTo(cx + ww / 2, top, cx + ww / 2, top + ww * 0.5);
    g.lineTo(cx + ww / 2, top + hh); g.closePath(); g.fill();
    g.fillStyle = "#e9dfc6"; g.fillRect(cx - 3, top, 6, hh); g.fillRect(cx - ww / 2, top + hh * 0.55, ww, 5);
  };
  for (const y of [150, 520]) for (const x of [140, 372]) win(x, y, 84, 220);
});
export const slate = () => tex(256, 256, (g, w, h) => {
  g.fillStyle = "#56606e"; g.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 16) for (let x = (y / 16) % 2 ? 0 : 12; x < w; x += 24) { g.fillStyle = rnd(x + y * 3) > 0.5 ? "#606b7a" : "#4b5462"; g.fillRect(x, y, 22, 14); }
});
/** teal river: soft ripple bands + glints; the texture offset is animated in world.ts */
export const water = () => tex(512, 512, (g, w, h) => {
  g.fillStyle = "#2f8f9a"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 70; i++) {
    const y = rnd(i) * h, x = rnd(i + 30) * w, L = 40 + rnd(i + 60) * 120;
    g.strokeStyle = i % 3 ? "rgba(120,210,220,0.35)" : "rgba(20,90,110,0.35)"; g.lineWidth = 3 + rnd(i + 9) * 3;
    g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + L * 0.3, y - 6, x + L * 0.6, y + 6, x + L, y); g.stroke();
  }
  for (let i = 0; i < 40; i++) { g.fillStyle = "rgba(235,250,255,0.55)"; g.fillRect(rnd(i + 200) * w, rnd(i + 300) * h, 10 + rnd(i) * 16, 2); }
}, [40, 40]);
export const pavers = (rep: [number, number] = [8, 8]) => tex(512, 512, (g, w, h) => {
  const s = 64;
  for (let y = 0; y < h; y += s) for (let x = 0; x < w; x += s) {
    const k = rnd(x * 3 + y); g.fillStyle = k > 0.66 ? "#c9c1b0" : k > 0.33 ? "#bdb5a4" : "#d3cbb9"; g.fillRect(x, y, s, s);
    g.strokeStyle = "rgba(90,80,64,0.45)"; g.lineWidth = 3; g.strokeRect(x + 1.5, y + 1.5, s - 3, s - 3);
  }
}, rep);
export const stripes = () => tex(256, 64, (g, w, h) => {
  for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? "#f4f1ea" : "#d62828"; g.beginPath(); g.moveTo(i * 32 - 16, h); g.lineTo(i * 32 + 16, 0); g.lineTo(i * 32 + 48, 0); g.lineTo(i * 32 + 16, h); g.fill(); }
}, [6, 1]);
export const hazard = () => tex(128, 512, (g, w, h) => {
  for (let i = 0; i < 12; i++) { g.fillStyle = i % 2 ? "#1d1d22" : "#f2c230"; g.beginPath(); g.moveTo(0, i * 48); g.lineTo(w, i * 48 - 40); g.lineTo(w, i * 48 + 8); g.lineTo(0, i * 48 + 48); g.fill(); }
});

// ---------------- labels ----------------
export const towerSign = () => tex(1024, 168, (g, w, h) => {
  g.fillStyle = "#1f4f8f"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#e6b93a"; g.lineWidth = 12; g.strokeRect(10, 10, w - 20, h - 20);
  g.lineWidth = 3; g.strokeRect(26, 26, w - 52, h - 52);
  g.fillStyle = "#f2c94c"; g.textAlign = "center"; g.textBaseline = "middle"; fit(g, "TOWER BRIDGE", w / 2, h / 2 + 4, 110, w - 120, 900, "Georgia");
});
export const gapSign = () => tex(512, 360, (g, w, h) => {
  g.fillStyle = "#f2c230"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#1d1d22"; g.lineWidth = 18; g.strokeRect(14, 14, w - 28, h - 28);
  g.fillStyle = "#1d1d22"; g.textAlign = "center"; g.textBaseline = "middle";
  fit(g, "6 FT GAP", w / 2, 132, 108, w - 70); fit(g, "AHEAD", w / 2, 250, 100, w - 70);
});
export const routeBoard = () => tex(512, 112, (g, w, h) => {
  g.fillStyle = "#141418"; g.fillRect(0, 0, w, h);
  g.fillStyle = "#fbf6e0"; g.textAlign = "center"; g.textBaseline = "middle"; fit(g, "78  LONDON", w / 2, h / 2 + 3, 76, w - 30);
});
export const fleetName = () => tex(1024, 96, (g, w, h) => {
  g.fillStyle = "#efe2bd"; g.fillRect(0, 0, w, h);
  g.fillStyle = "#8a1c1c"; g.textAlign = "center"; g.textBaseline = "middle"; fit(g, "LONDON TRANSPORT", w / 2, h / 2 + 3, 66, w - 200, 900, "Georgia");
});
export const chalkboard = () => tex(768, 640, (g, w, h) => {
  g.fillStyle = "#26372f"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 300; i++) { g.fillStyle = "rgba(255,255,255,0.03)"; g.fillRect(rnd(i) * w, rnd(i + 3) * h, 30, 2); }
  g.strokeStyle = "#8a5a34"; g.lineWidth = 26; g.strokeRect(13, 13, w - 26, h - 26);
  g.textAlign = "center"; g.textBaseline = "middle";
  g.fillStyle = "#f2d46a"; fit(g, "LONDON TRANSPORT", w / 2, 82, 54, w - 90, 800);
  g.fillStyle = "#ffffff"; fit(g, "SAFE LANDING", w / 2, 170, 92, w - 80, 900);
  // chalk diagram: the two tilted leaves, the dashed jump arc, a tiny bus
  g.strokeStyle = "#f4f4ee"; g.lineWidth = 9; g.lineCap = "round";
  g.beginPath(); g.moveTo(90, 470); g.lineTo(330, 380); g.moveTo(430, 400); g.lineTo(680, 450); g.stroke();
  g.setLineDash([18, 14]); g.lineWidth = 6; g.beginPath(); g.moveTo(320, 370); g.quadraticCurveTo(390, 250, 470, 380); g.stroke(); g.setLineDash([]);
  g.fillStyle = "#e85a4a"; g.fillRect(250, 340, 56, 34); g.fillRect(250, 330, 50, 12);
  g.fillStyle = "#ffffff"; fit(g, "0 BROKEN BONES", w / 2, 560, 66, w - 90, 900);
});
export const dial = () => tex(256, 256, (g, w, h) => {
  g.fillStyle = "#f4efe0"; g.beginPath(); g.arc(128, 128, 118, 0, 7); g.fill();
  g.strokeStyle = "#2a2226"; g.lineWidth = 10; g.stroke();
  for (let i = 0; i <= 8; i++) { const a = Math.PI * (0.8 + 1.4 * (i / 8)); g.lineWidth = 6; g.beginPath(); g.moveTo(128 + Math.cos(a) * 92, 128 + Math.sin(a) * 92); g.lineTo(128 + Math.cos(a) * 108, 128 + Math.sin(a) * 108); g.stroke(); }
  g.strokeStyle = "#d62828"; g.lineWidth = 8; g.beginPath(); g.moveTo(128, 128); g.lineTo(128 + Math.cos(-0.5) * 90, 128 + Math.sin(-0.5) * 90); g.stroke();
});
export const planks = (a = "#9a6a42", b = "#875a36", n = 8, rep: [number, number] = [1, 1]) => tex(512, 512, (g, w, h) => {
  const ph = h / n;
  for (let i = 0; i < n; i++) {
    g.fillStyle = i % 2 ? a : b; g.fillRect(0, i * ph, w, ph);
    g.strokeStyle = "rgba(60,35,20,0.3)"; g.lineWidth = 2;
    for (let k = 0; k < 3; k++) { const y = i * ph + ph * (0.25 + 0.25 * k); g.beginPath(); g.moveTo(0, y); g.bezierCurveTo(w * 0.3, y + 3, w * 0.7, y - 3, w, y); g.stroke(); }
    g.fillStyle = "#4a2c1a"; g.fillRect(0, i * ph - 2, w, 4);
  }
}, rep);
