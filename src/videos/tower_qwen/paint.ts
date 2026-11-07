// Procedural canvas textures for the Tower Bridge short (no image assets): the tidal Thames, Portland-stone tower
// masonry, asphalt road with lane dashes, the riverside paving, the "TOWER BRIDGE" walkway sign, the cab's
// "6 FT GAP AHEAD" warning plate, the plaza "SAFE LANDING" chalkboard and both faces of the red double-decker.
import * as THREE from "three";

const rnd = (i: number) => { const v = Math.sin(i * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };

export const tex = (w: number, h: number, draw: (g: CanvasRenderingContext2D, w: number, h: number) => void, repeat?: [number, number]) => {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  draw(c.getContext("2d")!, w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  return t;
};

/** auto-shrunk, centred bold caption */
const fit = (g: CanvasRenderingContext2D, s: string, cx: number, cy: number, px: number, col: string, min = 10) => {
  let n = px;
  g.font = `900 ${n}px Arial`;
  while (g.measureText(s).width > 0.86 * g.canvas.width && n > min) { n -= 2; g.font = `900 ${n}px Arial`; }
  g.fillStyle = col; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(s, cx, cy);
};

/** teal river water: horizontal ripple strips + foam flecks, tiles cleanly for a scrolling offset */
export const water = (rep: [number, number] = [26, 26]) => tex(512, 512, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, "#2b6f83"); gr.addColorStop(1, "#1f5b70");
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 60; i++) {
    const y = rnd(i) * h, lw = 30 + rnd(i + 7) * 150, k = i % 4;
    g.strokeStyle = k === 0 ? "rgba(180,230,235,0.30)" : k === 1 ? "rgba(255,255,255,0.16)" : "rgba(12,48,62,0.28)";
    g.lineWidth = 2 + rnd(i + 3) * 5;
    g.beginPath();
    for (let x = -20; x <= w + 20; x += 16) g.lineTo(x, y + Math.sin((x / w) * Math.PI * 2 + i) * (3 + rnd(i) * 5));
    g.stroke();
    void lw;
  }
  for (let i = 0; i < 300; i++) {
    g.fillStyle = "rgba(225,245,250,0.22)";
    g.fillRect(rnd(i + 900) * w, rnd(i + 1900) * h, 2 + rnd(i) * 10, 2);
  }
}, rep);

/** pale Portland stone: courses of blocks, mortar, soot streaks and a few carved mouldings */
export const stone = (rep: [number, number] = [2, 3]) => tex(512, 512, (g, w, h) => {
  g.fillStyle = "#e6dcc2"; g.fillRect(0, 0, w, h);
  const rows = 12, bh = h / rows;
  for (let r = 0; r < rows; r++) {
    const off = (r % 2) * 42;
    for (let x = -42; x < w; x += 84) {
      const v = rnd(r * 31 + x);
      g.fillStyle = `rgb(${Math.round(232 - v * 26)},${Math.round(222 - v * 26)},${Math.round(196 - v * 24)})`;
      g.fillRect(x + off + 2, r * bh + 2, 80, bh - 4);
    }
    g.strokeStyle = "rgba(150,138,112,0.55)"; g.lineWidth = 3;
    g.beginPath(); g.moveTo(0, r * bh); g.lineTo(w, r * bh); g.stroke();
  }
  for (let i = 0; i < 26; i++) {
    g.fillStyle = "rgba(88,84,74,0.10)";
    const x = rnd(i + 12) * w;
    g.fillRect(x, 0, 3 + rnd(i) * 9, h);
  }
  g.fillStyle = "rgba(120,112,94,0.22)";
  for (let i = 0; i < 160; i++) g.fillRect(rnd(i + 55) * w, rnd(i + 66) * h, 3, 3);
}, rep);

/** dark asphalt carriageway with a dashed centre line and pale kerb edges */
export const asphalt = (rep: [number, number] = [4, 1]) => tex(512, 256, (g, w, h) => {
  g.fillStyle = "#3f4148"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 1200; i++) {
    g.fillStyle = rnd(i) > 0.5 ? "rgba(90,92,100,0.35)" : "rgba(24,26,30,0.35)";
    g.fillRect(rnd(i + 4) * w, rnd(i + 9) * h, 2 + rnd(i) * 3, 2 + rnd(i + 1) * 3);
  }
  g.fillStyle = "rgba(238,232,214,0.9)";
  for (let x = 0; x < w; x += 128) g.fillRect(x + 12, h / 2 - 7, 74, 14);
  g.fillStyle = "rgba(238,232,214,0.45)";
  g.fillRect(0, 6, w, 7); g.fillRect(0, h - 13, w, 7);
}, rep);

/** riverside paving flags */
export const quay = (rep: [number, number] = [12, 12]) => tex(512, 512, (g, w, h) => {
  g.fillStyle = "#b9b2a4"; g.fillRect(0, 0, w, h);
  const n = 6, s = w / n;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const v = rnd(i * 17 + j * 31);
    g.fillStyle = `rgb(${Math.round(196 - v * 34)},${Math.round(190 - v * 34)},${Math.round(176 - v * 32)})`;
    g.fillRect(i * s + 3, j * s + 3, s - 6, s - 6);
  }
  for (let i = 0; i < 400; i++) { g.fillStyle = "rgba(90,86,78,0.12)"; g.fillRect(rnd(i) * w, rnd(i + 77) * h, 2, 2); }
}, rep);

/** the blue-and-gold "TOWER BRIDGE" board painted on the high-level walkway's river face */
export const towerSign = () => tex(1024, 220, (g, w, h) => {
  g.fillStyle = "#1d3f7a"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#e5be5a"; g.lineWidth = 16; g.strokeRect(18, 18, w - 36, h - 36);
  g.strokeStyle = "rgba(229,190,90,0.6)"; g.lineWidth = 5; g.strokeRect(42, 42, w - 84, h - 84);
  fit(g, "TOWER BRIDGE", w / 2, h / 2 + 6, 128, "#f4d98c");
});

/** the cab's yellow-and-black "6 FT GAP AHEAD" warning plate (hanging sign, so the face only matters) */
export const gapSign = () => tex(512, 360, (g, w, h) => {
  g.fillStyle = "#f2c230"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#241f22"; g.lineWidth = 22; g.strokeRect(20, 20, w - 40, h - 40);
  g.fillStyle = "#241f22";
  fit(g, "6 FT", w / 2, 118, 150, "#241f22");
  fit(g, "GAP AHEAD", w / 2, 236, 92, "#241f22");
  g.fillRect(74, 292, w - 148, 12);
});

/** the plaza A-frame slate: three chalk captions plus a chalk jump diagram */
export const chalkBoard = () => tex(768, 560, (g, w, h) => {
  g.fillStyle = "#28363a"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(226,238,232,${0.012 + rnd(i) * 0.03})`; g.fillRect(rnd(i + 3) * w, rnd(i + 8) * h, 3 + rnd(i) * 9, 2); }
  g.strokeStyle = "rgba(226,238,232,0.5)"; g.lineWidth = 5; g.strokeRect(24, 24, w - 48, h - 48);
  g.textAlign = "center"; g.textBaseline = "middle"; g.fillStyle = "#eef4ee";
  g.font = "900 56px Arial"; g.fillText("LONDON TRANSPORT", w / 2, 92);
  g.font = "900 82px Arial"; g.fillText("SAFE LANDING", w / 2, 186);
  g.font = "900 62px Arial"; g.fillText("0 BROKEN BONES", w / 2, 476);
  // the chalk diagram: rising leaves, a dashed parabola and a little bus over the gap
  g.strokeStyle = "rgba(238,244,238,0.85)"; g.lineWidth = 7;
  for (const s of [-1, 1]) {
    g.beginPath(); g.moveTo(w / 2 + s * 40, 350); g.lineTo(w / 2 + s * 250, 300); g.stroke();
  }
  g.setLineDash([16, 14]); g.lineWidth = 6;
  g.beginPath();
  for (let i = 0; i <= 40; i++) { const u = i / 40, x = w / 2 - 210 + 420 * u, y = 320 - 150 * 4 * u * (1 - u); if (i) g.lineTo(x, y); else g.moveTo(x, y); }
  g.stroke(); g.setLineDash([]);
  g.fillStyle = "#d2452f"; g.fillRect(w / 2 - 46, 216, 92, 44);
  g.fillStyle = "#f3e6c8"; g.fillRect(w / 2 - 46, 236, 92, 9);
  g.fillStyle = "#22282a"; g.beginPath(); g.arc(w / 2 - 26, 264, 10, 0, 7); g.arc(w / 2 + 26, 264, 10, 0, 7); g.fill();
});

/** painted red/cream panel: the double-decker's long side (u = along the bus, v = up) */
export const busSide = () => tex(1024, 600, (g, w, h) => {
  g.fillStyle = "#d62828"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 700; i++) { g.fillStyle = "rgba(120,20,20,0.10)"; g.fillRect(rnd(i) * w, rnd(i + 5) * h, 3, 3); }
  // upper deck glazing
  const win = (x: number, y: number, ww: number, hh: number) => {
    g.fillStyle = "#f6ead0"; g.fillRect(x - 6, y - 6, ww + 12, hh + 12);
    g.fillStyle = "#2c4356"; g.fillRect(x, y, ww, hh);
    g.fillStyle = "rgba(190,220,235,0.35)"; g.fillRect(x + 4, y + 4, ww - 8, hh * 0.22);
  };
  for (let i = 0; i < 6; i++) win(60 + i * 156, 60, 120, 120);
  // the cream waistband with the operator's name
  g.fillStyle = "#f6ead0"; g.fillRect(0, 236, w, 82);
  g.fillStyle = "#243040"; g.font = "900 58px Arial"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText("LONDON TRANSPORT", w / 2, 278);
  // lower deck glazing + the red skirt with a route box
  for (let i = 0; i < 5; i++) win(96 + i * 190, 350, 150, 118);
  g.fillStyle = "#a81f22"; g.fillRect(0, 508, w, 92);
  g.fillStyle = "#f6ead0"; g.fillRect(60, 520, 120, 68);
  g.fillStyle = "#243040"; g.font = "900 52px Arial"; g.fillText("78", 120, 556);
  g.fillStyle = "#f6ead0"; g.fillRect(w - 300, 520, 240, 68);
  g.fillStyle = "#243040"; g.font = "900 44px Arial"; g.fillText("LONDON", w - 180, 556);
});

/** the double-decker's front / rear panel */
export const busEnd = (rear = false) => tex(512, 600, (g, w, h) => {
  g.fillStyle = "#d62828"; g.fillRect(0, 0, w, h);
  const win = (x: number, y: number, ww: number, hh: number) => {
    g.fillStyle = "#f6ead0"; g.fillRect(x - 6, y - 6, ww + 12, hh + 12);
    g.fillStyle = "#2c4356"; g.fillRect(x, y, ww, hh);
  };
  win(70, 60, 372, 130);
  g.fillStyle = "#f6ead0"; g.fillRect(0, 232, w, 74);
  win(84, 340, 150, 120); win(278, 340, 150, 120);
  g.fillStyle = "#f6ead0"; g.fillRect(150, 44, 212, 60);
  g.fillStyle = "#243040"; g.textAlign = "center"; g.textBaseline = "middle";
  g.font = "900 46px Arial"; g.fillText(rear ? "78" : "78 TOWER", 256, 74);
  g.fillStyle = "#2c4356"; g.fillRect(56, 512, 74, 60); g.fillRect(w - 130, 512, 74, 60);
  g.fillStyle = "#f2c230"; g.fillRect(176, 470, 160, 30);
});

/** cream stripe panel used for the cab's dash top and the certificate-free 3D trim */
export const brassPanel = () => tex(256, 256, (g, w, h) => {
  g.fillStyle = "#c9962a"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 400; i++) { g.fillStyle = rnd(i) > 0.5 ? "rgba(255,232,150,0.25)" : "rgba(120,80,10,0.18)"; g.fillRect(rnd(i + 2) * w, rnd(i + 6) * h, 8, 3); }
});

/** red leather-ish cab upholstery */
export const cabPaint = () => tex(256, 256, (g, w, h) => {
  g.fillStyle = "#8f1f22"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 500; i++) { g.fillStyle = "rgba(40,8,10,0.22)"; g.fillRect(rnd(i) * w, rnd(i + 3) * h, 4, 4); }
  g.strokeStyle = "rgba(255,200,160,0.12)"; g.lineWidth = 3;
  for (let x = 0; x < w; x += 32) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
});
