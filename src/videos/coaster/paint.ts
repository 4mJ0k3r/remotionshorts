// Procedural canvas textures for the coaster sets (no image assets): grass, dirt, wood planks, red/cream deck planks,
// concrete, the "FRANK'S LOOP" blueprint board and the cart's side banner. Flat paint with light wear.
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
