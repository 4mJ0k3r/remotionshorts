// Procedural canvas textures for HotelLiftShort:
// 1. Brick facade & pier texture
// 2. Timber plank texture (shoring beams, boardwalk, trench floor)
// 3. Facade banner: "TREMONT HOTEL"
// 4. Trench timber sign: "5,000 JACKSCREWS"
// 5. Chalkboard easel: "TREMONT HOUSE / RAISED 6 FEET / 0 BROKEN WINDOWS"
// 6. Cast-iron metal & brass textures
// 7. Ground contact shadow blob
import * as THREE from "three";

/** Create a canvas texture with mipmapping & sRGB encoding */
function makeTex(w: number, h: number, draw: (ctx: CanvasRenderingContext2D) => void): THREE.CanvasTexture {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d")!;
  draw(ctx);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  return tex;
}

/** 1860s Red Brick facade texture */
export function makeBrickTexture(): THREE.CanvasTexture {
  return makeTex(512, 512, (g) => {
    g.fillStyle = "#8b382e"; // Base brick red
    g.fillRect(0, 0, 512, 512);

    // Mortar lines & individual brick variations
    const rows = 32;
    const cols = 16;
    const rh = 512 / rows;
    const cw = 512 / cols;

    for (let r = 0; r < rows; r++) {
      const y = r * rh;
      const xOff = (r % 2) * (cw / 2);
      for (let c = -1; c <= cols; c++) {
        const x = c * cw + xOff;
        // Brick color variation
        const shade = ((r * 13 + c * 29) % 7) - 3;
        const rVal = Math.min(255, Math.max(0, 139 + shade * 10));
        const gVal = Math.min(255, Math.max(0, 56 + shade * 6));
        const bVal = Math.min(255, Math.max(0, 46 + shade * 5));
        g.fillStyle = `rgb(${rVal},${gVal},${bVal})`;
        g.fillRect(x + 2, y + 2, cw - 4, rh - 4);

        // subtle speckle
        g.fillStyle = "rgba(0,0,0,0.12)";
        if ((r + c) % 3 === 0) g.fillRect(x + 4, y + 4, cw - 8, rh - 8);
      }
      // Horizontal mortar
      g.fillStyle = "#d8cfc4";
      g.fillRect(0, y, 512, 2);
    }
  });
}

/** Rough Oak Timber / Boardwalk Planks */
export function makeWoodPlankTexture(): THREE.CanvasTexture {
  return makeTex(512, 512, (g) => {
    g.fillStyle = "#8c6846";
    g.fillRect(0, 0, 512, 512);

    const planks = 8;
    const pw = 512 / planks;
    for (let i = 0; i < planks; i++) {
      const x = i * pw;
      const shade = ((i * 17) % 5) - 2;
      const r = Math.min(255, Math.max(0, 140 + shade * 12));
      const gr = Math.min(255, Math.max(0, 104 + shade * 10));
      const b = Math.min(255, Math.max(0, 70 + shade * 8));
      g.fillStyle = `rgb(${r},${gr},${b})`;
      g.fillRect(x + 2, 0, pw - 4, 512);

      // Wood grain lines
      g.fillStyle = "rgba(40, 25, 15, 0.18)";
      for (let k = 0; k < 6; k++) {
        const gx = x + 4 + k * 8;
        g.fillRect(gx, 0, 2, 512);
      }
      // Nail heads
      g.fillStyle = "#2d231c";
      g.beginPath();
      g.arc(x + pw / 2, 32, 4, 0, Math.PI * 2);
      g.arc(x + pw / 2, 480, 4, 0, Math.PI * 2);
      g.fill();

      // Plank seam
      g.fillStyle = "#352316";
      g.fillRect(x, 0, 3, 512);
    }
  });
}

/** Tremont Hotel Grand Facade Banner: "TREMONT HOTEL" */
export function makeTremontBannerTexture(): THREE.CanvasTexture {
  return makeTex(1024, 256, (g) => {
    // Deep navy background
    g.fillStyle = "#1b2538";
    g.fillRect(0, 0, 1024, 256);

    // Gold outer and inner border
    g.lineWidth = 10;
    g.strokeStyle = "#e8b938";
    g.strokeRect(12, 12, 1000, 232);
    g.lineWidth = 4;
    g.strokeRect(24, 24, 976, 208);

    // Corner rosettes
    g.fillStyle = "#e8b938";
    const corners = [[32, 32], [992, 32], [32, 224], [992, 224]];
    for (const [cx, cy] of corners) {
      g.beginPath();
      g.arc(cx, cy, 10, 0, Math.PI * 2);
      g.fill();
    }

    // Bold gold serif typography
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.font = "bold 82px 'Georgia', 'Times New Roman', serif";
    g.fillStyle = "#fadb66";
    g.fillText("TREMONT HOTEL", 512, 120);

    // Subtitle
    g.font = "bold 32px 'Georgia', serif";
    g.fillStyle = "#dfba52";
    g.fillText("• CHICAGO 1861 •", 512, 185);
  });
}

/** Shoring Gallery Sign: "5,000 JACKSCREWS" */
export function makeJackSignTexture(): THREE.CanvasTexture {
  return makeTex(512, 256, (g) => {
    // Cream painted wooden sign
    g.fillStyle = "#f5efe2";
    g.fillRect(0, 0, 512, 256);

    // Dark brown/black ink border
    g.lineWidth = 14;
    g.strokeStyle = "#2b1e16";
    g.strokeRect(10, 10, 492, 236);
    g.lineWidth = 4;
    g.strokeRect(24, 24, 464, 208);

    // Bold dark lettering
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.fillStyle = "#221611";
    g.font = "900 64px 'Arial Black', sans-serif";
    g.fillText("5,000", 512 / 2, 90);
    g.font = "900 44px 'Arial Black', sans-serif";
    g.fillText("JACKSCREWS", 512 / 2, 165);
  });
}

/** Plaza Chalkboard Easel: "TREMONT HOUSE / RAISED 6 FEET / 0 BROKEN WINDOWS" */
export function makeEaselBoardTexture(): THREE.CanvasTexture {
  return makeTex(512, 640, (g) => {
    // Dark slate blackboard
    g.fillStyle = "#212826";
    g.fillRect(0, 0, 512, 640);

    // Light chalk border
    g.lineWidth = 6;
    g.strokeStyle = "rgba(240, 245, 240, 0.75)";
    g.strokeRect(18, 18, 476, 604);

    g.textAlign = "center";
    g.textBaseline = "middle";
    g.fillStyle = "#ffffff";

    g.font = "bold 44px sans-serif";
    g.fillText("TREMONT HOUSE", 256, 75);

    g.fillStyle = "#ffe46b"; // highlighted yellow chalk
    g.font = "900 48px sans-serif";
    g.fillText("RAISED 6 FEET", 256, 145);

    // Chalk diagram of building with lift arrows
    g.strokeStyle = "rgba(255, 255, 255, 0.85)";
    g.lineWidth = 5;
    // Building box
    g.strokeRect(130, 210, 252, 170);
    // Roof triangle
    g.beginPath();
    g.moveTo(110, 210);
    g.lineTo(256, 170);
    g.lineTo(402, 210);
    g.closePath();
    g.stroke();
    // Windows on diagram
    for (let wy = 235; wy <= 340; wy += 45) {
      for (let wx = 160; wx <= 320; wx += 55) {
        g.strokeRect(wx, wy, 24, 28);
      }
    }
    // Upward arrows underneath
    g.fillStyle = "#5de060";
    g.strokeStyle = "#5de060";
    g.lineWidth = 4;
    for (const ax of [170, 256, 342]) {
      g.beginPath();
      g.moveTo(ax, 430);
      g.lineTo(ax, 395);
      g.stroke();
      g.beginPath();
      g.moveTo(ax - 10, 405);
      g.lineTo(ax, 388);
      g.lineTo(ax + 10, 405);
      g.fill();
    }

    g.fillStyle = "#ffffff";
    g.font = "bold 32px sans-serif";
    g.fillText("GEORGE PULLMAN, ENG.", 256, 480);

    g.fillStyle = "#5de060";
    g.font = "900 40px sans-serif";
    g.fillText("0 BROKEN WINDOWS", 256, 545);
    g.font = "bold 26px sans-serif";
    g.fillStyle = "#cccccc";
    g.fillText("GUESTS REMAIN INSIDE", 256, 588);
  });
}

/** Ground contact shadow blob */
export function makeBlobTexture(): THREE.CanvasTexture {
  return makeTex(128, 128, (g) => {
    const grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, "rgba(0, 0, 0, 0.85)");
    grad.addColorStop(0.5, "rgba(0, 0, 0, 0.45)");
    grad.addColorStop(1, "rgba(0, 0, 0, 0.0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, 128, 128);
  });
}
