// Procedural canvas textures for MolassesTankShort:
// 1. Riveted steel plate texture for massive 50ft tank
// 2. Tank sign: "PURITY DISTILLING / 2,000,000 GAL"
// 3. Streetcar cab warning sign: "DANGER: 35 MPH WAVE"
// 4. Chalkboard easel: "BOSTON HARBOR 1919 / 25 FT TALL / 35 MPH SYRUP WAVE"
// 5. Boston harbor cobblestones & boardwalk planks
// 6. Red elevated train car livery
import * as THREE from "three";

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

/** Dark riveted industrial steel plate texture */
export function makeRivetedSteelTexture(): THREE.CanvasTexture {
  return makeTex(512, 512, (g) => {
    // Industrial dark blue-grey steel base
    g.fillStyle = "#343a42";
    g.fillRect(0, 0, 512, 512);

    // 4 horizontal steel plates
    const plates = 4;
    const ph = 512 / plates;
    for (let i = 0; i < plates; i++) {
      const y = i * ph;
      // Slight tone shift per plate
      const v = 52 + ((i * 17) % 7) * 3;
      g.fillStyle = `rgb(${v}, ${v + 6}, ${v + 12})`;
      g.fillRect(0, y + 2, 512, ph - 4);

      // Plate overlap seam shadow & highlight
      g.fillStyle = "#1e2228";
      g.fillRect(0, y, 512, 4);
      g.fillStyle = "#58626e";
      g.fillRect(0, y + 4, 512, 2);

      // Row of rivets along the seam
      g.fillStyle = "#181a1f";
      for (let x = 16; x < 512; x += 32) {
        // Rivet drop shadow
        g.beginPath();
        g.arc(x, y + 14, 5, 0, Math.PI * 2);
        g.fill();
      }
      g.fillStyle = "#727d8c";
      for (let x = 16; x < 512; x += 32) {
        // Rivet highlight
        g.beginPath();
        g.arc(x - 1, y + 13, 3.5, 0, Math.PI * 2);
        g.fill();
      }
    }
  });
}

/** Tank Facade Banner: "PURITY DISTILLING / 2,000,000 GAL" */
export function makePurityDistillingBanner(): THREE.CanvasTexture {
  return makeTex(1024, 256, (g) => {
    // Dark cast-iron/steel plate
    g.fillStyle = "#22272e";
    g.fillRect(0, 0, 1024, 256);

    // Industrial brass riveted border
    g.lineWidth = 12;
    g.strokeStyle = "#c89438";
    g.strokeRect(14, 14, 996, 228);
    g.lineWidth = 3;
    g.strokeRect(26, 26, 972, 204);

    // Corner rivets
    g.fillStyle = "#e0aa42";
    const rivets = [[32, 32], [992, 32], [32, 224], [992, 224], [512, 32], [512, 224]];
    for (const [rx, ry] of rivets) {
      g.beginPath();
      g.arc(rx, ry, 8, 0, Math.PI * 2);
      g.fill();
    }

    // Bold clean industrial lettering
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.font = "900 74px 'Arial Black', sans-serif";
    g.fillStyle = "#f4f6f8";
    g.fillText("PURITY DISTILLING", 512, 105);

    g.font = "900 48px 'Arial Black', sans-serif";
    g.fillStyle = "#e2a83e";
    g.fillText("2,000,000 GAL • BOSTON 1919", 512, 180);
  });
}

/** Streetcar Cab Warning Sign: "DANGER: 35 MPH WAVE" */
export function makeCabWarningSign(): THREE.CanvasTexture {
  return makeTex(512, 256, (g) => {
    // Caution yellow enamel
    g.fillStyle = "#f5bc28";
    g.fillRect(0, 0, 512, 256);

    // Heavy black hazard border
    g.lineWidth = 16;
    g.strokeStyle = "#1a1614";
    g.strokeRect(10, 10, 492, 236);

    // Bold black warning typography
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.fillStyle = "#181412";
    g.font = "900 68px 'Arial Black', sans-serif";
    g.fillText("DANGER!", 256, 85);

    g.font = "900 44px 'Arial Black', sans-serif";
    g.fillText("35 MPH WAVE", 256, 168);
  });
}

/** Chalkboard Easel: "BOSTON HARBOR 1919 / 25 FT TALL / 35 MPH SYRUP WAVE" */
export function makeEaselBoardTexture(): THREE.CanvasTexture {
  return makeTex(512, 640, (g) => {
    // Slate blackboard
    g.fillStyle = "#1e2622";
    g.fillRect(0, 0, 512, 640);

    // Chalk border
    g.lineWidth = 6;
    g.strokeStyle = "rgba(240, 245, 240, 0.75)";
    g.strokeRect(18, 18, 476, 604);

    g.textAlign = "center";
    g.textBaseline = "middle";
    g.fillStyle = "#ffffff";

    g.font = "bold 42px sans-serif";
    g.fillText("BOSTON HARBOR 1919", 256, 75);

    g.fillStyle = "#f5bc28";
    g.font = "900 48px sans-serif";
    g.fillText("25 FT TALL WAVE", 256, 145);

    // Chalk diagram of wave cresting over street and trestle
    g.strokeStyle = "rgba(255, 255, 255, 0.85)";
    g.lineWidth = 5;
    // Wave crest curve
    g.beginPath();
    g.moveTo(70, 360);
    g.bezierCurveTo(150, 350, 220, 210, 310, 210);
    g.bezierCurveTo(360, 210, 410, 250, 440, 340);
    g.stroke();

    // Trestle legs
    g.strokeStyle = "#8ec5ee";
    g.lineWidth = 4;
    g.beginPath();
    g.moveTo(370, 230); g.lineTo(370, 380);
    g.moveTo(420, 260); g.lineTo(420, 380);
    g.stroke();
    // Tilted train car on trestle
    g.fillStyle = "#d04238";
    g.save();
    g.translate(390, 230);
    g.rotate(-0.35);
    g.fillRect(-35, -16, 70, 32);
    g.restore();

    g.fillStyle = "#ff6b58";
    g.font = "900 42px sans-serif";
    g.fillText("35 MPH SYRUP", 256, 440);

    g.fillStyle = "#5de060";
    g.font = "bold 32px sans-serif";
    g.fillText("ELEVATED TRAIN HIT", 256, 520);

    g.fillStyle = "#d0d8e0";
    g.font = "bold 26px sans-serif";
    g.fillText("2.3 MILLION GALLONS", 256, 580);
  });
}

/** Boston harbor cobblestone street texture */
export function makeCobblestoneTexture(): THREE.CanvasTexture {
  return makeTex(512, 512, (g) => {
    g.fillStyle = "#4a4f56";
    g.fillRect(0, 0, 512, 512);

    const rows = 16;
    const cols = 16;
    const rh = 512 / rows;
    const cw = 512 / cols;

    for (let r = 0; r < rows; r++) {
      const y = r * rh;
      const xOff = (r % 2) * (cw / 2);
      for (let c = -1; c <= cols; c++) {
        const x = c * cw + xOff;
        const shade = ((r * 11 + c * 23) % 7) - 3;
        const val = Math.min(255, Math.max(0, 95 + shade * 8));
        g.fillStyle = `rgb(${val}, ${val + 2}, ${val + 4})`;
        g.beginPath();
        g.roundRect(x + 2, y + 2, cw - 4, rh - 4, 6);
        g.fill();
      }
    }
  });
}

/** Harbor wooden boardwalk planks */
export function makeWoodPlankTexture(): THREE.CanvasTexture {
  return makeTex(512, 512, (g) => {
    g.fillStyle = "#7a624a";
    g.fillRect(0, 0, 512, 512);

    const planks = 8;
    const pw = 512 / planks;
    for (let i = 0; i < planks; i++) {
      const x = i * pw;
      const shade = ((i * 13) % 5) - 2;
      const r = Math.min(255, Math.max(0, 128 + shade * 12));
      const gr = Math.min(255, Math.max(0, 100 + shade * 10));
      const b = Math.min(255, Math.max(0, 75 + shade * 8));
      g.fillStyle = `rgb(${r},${gr},${b})`;
      g.fillRect(x + 2, 0, pw - 4, 512);

      g.fillStyle = "rgba(40, 25, 15, 0.2)";
      for (let k = 0; k < 5; k++) {
        g.fillRect(x + 4 + k * 9, 0, 2, 512);
      }
      g.fillStyle = "#2d2015";
      g.fillRect(x, 0, 3, 512);
    }
  });
}

/** Red Boston Elevated train car texture */
export function makeTrainCarTexture(): THREE.CanvasTexture {
  return makeTex(512, 256, (g) => {
    // Boston crimson red
    g.fillStyle = "#98282e";
    g.fillRect(0, 0, 512, 256);

    // Cream roofline stripe
    g.fillStyle = "#eae4d2";
    g.fillRect(0, 12, 512, 16);

    // Window band
    for (let x = 20; x < 500; x += 64) {
      g.fillStyle = "#1e2832";
      g.fillRect(x, 48, 48, 80);
      g.lineWidth = 4;
      g.strokeStyle = "#eae4d2";
      g.strokeRect(x, 48, 48, 80);
    }

    // Gold coach number & transit crest
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.fillStyle = "#e5b542";
    g.font = "bold 26px sans-serif";
    g.fillText("BOSTON ELEVATED RY. • NO. 418", 256, 185);

    // Dark undercarriage band
    g.fillStyle = "#181a1d";
    g.fillRect(0, 220, 512, 36);
  });
}
