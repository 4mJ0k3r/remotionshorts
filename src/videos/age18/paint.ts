// Hand-painted canvas textures for the age18 sets: floors, walls, bunting, lawn, lake, screens and signage.
// Everything is drawn at 2D canvas resolution and mapped onto simple three.js planes/boxes by build.ts.
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

/** warm/cool timber planks, runs along x */
export const woodFloor = (base: string, seam: string) => tex(1024, 1024, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  const rows = 8, rh = h / rows;
  for (let r = 0; r < rows; r++) {
    const y = r * rh;
    g.fillStyle = r % 2 ? "rgba(255,255,255,0.035)" : "rgba(0,0,0,0.045)";
    g.fillRect(0, y, w, rh);
    for (let k = 0; k < 22; k++) {
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

export const wallPaint = (base: string, shade: string, stripes = false) => tex(512, 512, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, base); gr.addColorStop(1, shade);
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  if (stripes) for (let x = 0; x < w; x += 42) { g.fillStyle = "rgba(255,255,255,0.045)"; g.fillRect(x, 0, 18, h); }
  grain(g, w, h, 0.035, 700, 3);
});

export const wallpaperDots = (base: string) => tex(512, 512, (g, w, h) => {
  g.fillStyle = base; g.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 64) for (let x = 0; x < w; x += 64) {
    g.fillStyle = "rgba(255,255,255,0.055)";
    g.beginPath(); g.arc(x + 32 + (y / 64 % 2) * 16, y + 32, 7, 0, Math.PI * 2); g.fill();
  }
  grain(g, w, h, 0.03, 500, 12);
});

/** birthday bunting: rope + triangle flags, transparent elsewhere */
export const bunting = () => tex(1024, 256, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  g.strokeStyle = "#4a3628"; g.lineWidth = 7;
  g.beginPath();
  for (let x = 0; x <= w; x += 16) g.lineTo(x, 44 + Math.sin((x / w) * Math.PI) * 30);
  g.stroke();
  const cols = ["#36c4e0", "#ffd35a", "#f07a8c", "#f4f1e8", "#7fd08a"];
  for (let i = 0; i < 12; i++) {
    const x = 40 + i * 82, y = 44 + Math.sin(((x / w) * Math.PI)) * 30;
    g.fillStyle = cols[i % cols.length];
    g.beginPath(); g.moveTo(x - 34, y + 6); g.lineTo(x + 34, y + 6); g.lineTo(x, y + 96); g.closePath(); g.fill();
    g.strokeStyle = "rgba(35,23,34,0.55)"; g.lineWidth = 4; g.stroke();
  }
});

export const lawn = () => tex(512, 512, (g, w, h) => {
  g.fillStyle = "#5e8f46"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 2600; i++) {
    const x = rnd(i * 3) * w, y = rnd(i * 7) * h;
    g.strokeStyle = rnd(i) > 0.5 ? "rgba(110,164,80,0.55)" : "rgba(50,90,44,0.45)";
    g.lineWidth = 1.5;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + (rnd(i * 5) - 0.5) * 5, y - 4 - rnd(i * 9) * 7); g.stroke();
  }
});

export const driveway = () => tex(512, 512, (g, w, h) => {
  g.fillStyle = "#b9b2a4"; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 700; i++) {
    g.fillStyle = `rgba(70,66,60,${0.04 + rnd(i) * 0.06})`;
    g.beginPath(); g.arc(rnd(i * 3) * w, rnd(i * 7) * h, 1 + rnd(i) * 2.5, 0, Math.PI * 2); g.fill();
  }
  g.strokeStyle = "rgba(80,76,70,0.35)"; g.lineWidth = 3;
  for (let y = 0; y < h; y += 128) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y + 6); g.stroke(); }
});

export const siding = () => tex(512, 512, (g, w, h) => {
  g.fillStyle = "#e9dfc8"; g.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 34) {
    g.fillStyle = "rgba(90,74,58,0.18)"; g.fillRect(0, y + 30, w, 4);
    g.fillStyle = "rgba(255,255,255,0.16)"; g.fillRect(0, y + 2, w, 3);
  }
  grain(g, w, h, 0.03, 400, 21);
});

/** lake surface: cool blues by day, warm glints by golden hour; mapped on a large plane */
export const lake = (golden: boolean) => tex(1024, 512, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h);
  // cool water against the cream sky: the lake is the only mid-value band at the horizon, so it must not be peach
  if (golden) { gr.addColorStop(0, "#2f4c60"); gr.addColorStop(0.45, "#4a6280"); gr.addColorStop(1, "#8f7e9a"); }
  else { gr.addColorStop(0, "#a8cce4"); gr.addColorStop(0.5, "#4c8db8"); gr.addColorStop(1, "#26608f"); }
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 500; i++) {
    const y = rnd(i * 3) * h, x = rnd(i * 7) * w, len = 20 + rnd(i) * 110;
    g.fillStyle = golden ? `rgba(255,214,150,${0.1 + rnd(i * 5) * 0.24})` : `rgba(220,240,255,${0.04 + rnd(i * 5) * 0.1})`;
    g.fillRect(x, y, len, 1.5 + rnd(i * 9) * 2);
  }
});

export const tvScreen = () => tex(1024, 576, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, w, h);
  gr.addColorStop(0, "#8ee6ff"); gr.addColorStop(0.55, "#4b9df0"); gr.addColorStop(1, "#2a4c9e");
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  g.fillStyle = "rgba(255,255,255,0.9)";
  g.beginPath(); g.arc(w * 0.36, h * 0.38, 74, 0, Math.PI * 2); g.fill();
  g.fillStyle = "#ffd35a"; g.beginPath(); g.arc(w * 0.68, h * 0.55, 54, 0, Math.PI * 2); g.fill();
  g.fillStyle = "#f4f1e8";
  for (let i = 0; i < 5; i++) g.fillRect(140 + i * 150, 430 + (i % 2) * 22, 90, 34);
  g.fillStyle = "rgba(20,30,60,0.35)"; g.fillRect(0, 0, w, h);
});

export const ecgScreen = (bpm: number) => tex(512, 512, (g, w, h) => {
  g.fillStyle = "#0a1a16"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "rgba(80,220,160,0.12)"; g.lineWidth = 1;
  for (let x = 0; x < w; x += 32) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
  for (let y = 0; y < h; y += 32) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
  g.strokeStyle = "#63ffb4"; g.lineWidth = 5; g.shadowColor = "#63ffb4"; g.shadowBlur = 18;
  g.beginPath();
  for (let x = 0; x <= w; x += 4) {
    const u = (x / w) * 4 % 1;
    let y = h * 0.55;
    if (u > 0.32 && u < 0.38) y -= 46;
    if (u >= 0.38 && u < 0.42) y += 84;
    if (u >= 0.42 && u < 0.47) y -= 130;
    if (u >= 0.47 && u < 0.55) y += 20;
    if (u > 0.55 && u < 0.72) y -= 16 * Math.sin((u - 0.55) / 0.17 * Math.PI);
    x === 0 ? g.moveTo(x, y) : g.lineTo(x, y);
  }
  g.stroke();
  g.shadowBlur = 0;
  g.fillStyle = "#d9fff0"; g.font = "700 54px 'Courier New', monospace"; g.fillText(`${bpm}`, 30, 74);
  g.font = "700 26px 'Courier New', monospace"; g.fillText("BPM", 120, 74);
});

export const skeletonPoster = () => tex(512, 700, (g, w, h) => {
  g.fillStyle = "#eef2ec"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#2e4a58"; g.lineWidth = 8; g.strokeRect(8, 8, w - 16, h - 16);
  g.fillStyle = "#2e4a58"; g.font = "700 40px Arial"; g.textAlign = "center"; g.fillText("SKELETON", w / 2, 62);
  g.strokeStyle = "#4a5c68"; g.lineWidth = 9; g.fillStyle = "#f4f2e6";
  g.beginPath(); g.arc(w / 2, 150, 54, 0, Math.PI * 2); g.fill(); g.stroke();
  g.fillStyle = "#4a5c68";
  g.beginPath(); g.arc(w / 2 - 20, 140, 9, 0, Math.PI * 2); g.fill();
  g.beginPath(); g.arc(w / 2 + 20, 140, 9, 0, Math.PI * 2); g.fill();
  g.fillRect(w / 2 - 4, 210, 8, 250);
  for (let i = 0; i < 6; i++) {
    const y = 236 + i * 34, half = 76 - i * 8;
    g.beginPath(); g.moveTo(w / 2, y); g.quadraticCurveTo(w / 2 - half, y + 6, w / 2 - half, y + 26); g.stroke();
    g.beginPath(); g.moveTo(w / 2, y); g.quadraticCurveTo(w / 2 + half, y + 6, w / 2 + half, y + 26); g.stroke();
  }
  g.beginPath(); g.moveTo(w / 2 - 40, 470); g.lineTo(w / 2 - 20, 600); g.stroke();
  g.beginPath(); g.moveTo(w / 2 + 40, 470); g.lineTo(w / 2 + 20, 600); g.stroke();
  g.beginPath(); g.moveTo(w / 2 - 46, 450); g.lineTo(w / 2 - 90, 520); g.stroke();
  g.beginPath(); g.moveTo(w / 2 + 46, 450); g.lineTo(w / 2 + 90, 520); g.stroke();
  g.font = "700 24px Arial"; g.fillStyle = "#2e4a58"; g.fillText("206 BONES", w / 2, 660);
  g.textAlign = "left";
});

export const bankSign = () => tex(1024, 256, (g, w, h) => {
  g.fillStyle = "#123a5e"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#d8b45a"; g.lineWidth = 8; g.strokeRect(12, 12, w - 24, h - 24);
  g.fillStyle = "#f4f1e8"; g.font = "700 130px Georgia, serif"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText("BANK", w / 2, h / 2 + 6);
  g.textAlign = "left"; g.textBaseline = "alphabetic";
});

export const tellerSign = () => tex(512, 256, (g, w, h) => {
  g.fillStyle = "#f4f1e8"; g.fillRect(0, 0, w, h);
  g.strokeStyle = "#123a5e"; g.lineWidth = 10; g.strokeRect(8, 8, w - 16, h - 16);
  g.fillStyle = "#123a5e"; g.font = "700 64px Arial"; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText("TELLER 3", w / 2, h / 2);
  g.font = "700 30px Arial"; g.fillText("ACCOUNTS · DEPOSITS", w / 2, h / 2 + 62);
  g.textAlign = "left"; g.textBaseline = "alphabetic";
});

export const clock300 = () => tex(512, 256, (g, w, h) => {
  g.fillStyle = "#120e10"; g.fillRect(0, 0, w, h);
  g.fillStyle = "#ff3636"; g.font = "700 150px 'Courier New', monospace"; g.textAlign = "center"; g.textBaseline = "middle";
  g.shadowColor = "#ff2020"; g.shadowBlur = 26;
  g.fillText("3:00", w / 2, h / 2 + 4);
  g.shadowBlur = 0; g.font = "700 28px Arial"; g.fillStyle = "#ff9a9a"; g.fillText("AM", w - 74, h - 22);
  g.textAlign = "left"; g.textBaseline = "alphabetic";
});

export const windowNight = () => tex(512, 512, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, 0, h);
  gr.addColorStop(0, "#0a1230"); gr.addColorStop(0.55, "#182a4e"); gr.addColorStop(1, "#2a3a60");
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 90; i++) {
    g.fillStyle = `rgba(255,255,255,${0.2 + rnd(i) * 0.7})`;
    g.fillRect(rnd(i * 3) * w, rnd(i * 7) * h * 0.6, 2, 2);
  }
  g.fillStyle = "#f4e6b0"; g.beginPath(); g.arc(w * 0.72, h * 0.22, 40, 0, Math.PI * 2); g.fill();
  g.fillStyle = "#0a1230"; g.beginPath(); g.arc(w * 0.72 + 20, h * 0.22 - 8, 36, 0, Math.PI * 2); g.fill();
  for (let i = 0; i < 16; i++) {
    const x = i * 34 + rnd(i) * 10, bh = 60 + rnd(i * 3) * 120;
    g.fillStyle = "#131c34"; g.fillRect(x, h - bh, 30, bh);
    for (let k = 0; k < 8; k++) if (rnd(i * 11 + k) > 0.45) {
      g.fillStyle = "rgba(255,214,130,0.85)"; g.fillRect(x + 5 + (k % 3) * 8, h - bh + 10 + Math.floor(k / 3) * 18, 5, 7);
    }
  }
});

export const mirrorTex = () => tex(512, 512, (g, w, h) => {
  const gr = g.createLinearGradient(0, 0, w, h);
  gr.addColorStop(0, "#dcecf4"); gr.addColorStop(0.45, "#b8d2e0"); gr.addColorStop(1, "#8fb4c8");
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  g.fillStyle = "rgba(255,255,255,0.4)";
  g.beginPath(); g.moveTo(60, 0); g.lineTo(190, 0); g.lineTo(30, h); g.lineTo(-60, h); g.closePath(); g.fill();
  g.fillStyle = "rgba(255,255,255,0.18)";
  g.beginPath(); g.moveTo(260, 0); g.lineTo(310, 0); g.lineTo(150, h); g.lineTo(100, h); g.closePath(); g.fill();
});

export const rugTex = () => tex(512, 512, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  g.fillStyle = "#8e4a4a"; g.beginPath(); g.ellipse(w / 2, h / 2, w * 0.48, h * 0.44, 0, 0, Math.PI * 2); g.fill();
  g.strokeStyle = "#e8c45a"; g.lineWidth = 10;
  g.beginPath(); g.ellipse(w / 2, h / 2, w * 0.4, h * 0.36, 0, 0, Math.PI * 2); g.stroke();
  g.strokeStyle = "#d9a0a0"; g.lineWidth = 5;
  g.beginPath(); g.ellipse(w / 2, h / 2, w * 0.28, h * 0.24, 0, 0, Math.PI * 2); g.stroke();
  grain(g, w, h, 0.05, 800, 4);
});
