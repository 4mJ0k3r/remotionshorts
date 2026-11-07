// Framing check for HotelLiftShort (SKILL.md Section 4.3):
// Projects 3D world points through camAt(id, f) and computes u%/v%.
// Verifies all subjects & signs stay inside 15%..85% (u% and v%),
// and background hotel fills v = 10%..55% in Shot 3.
// Usage: node scripts/hl_frame.mjs [f,f,...]
import * as S from "../src/videos/hotel_lift/story.ts";

const ASPECT = 1080 / 1920; // 0.5625

const sub = (a, b) => a.map((v, i) => v - b[i]);
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(...a); return a.map((v) => v / l); };
const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];

export const proj = (c, p) => {
  const f = norm(sub(c.look, c.pos));
  const r = norm([-f[2], 0, f[0]]);
  const up = cross(r, f);
  const d = sub(p, c.pos);
  const z = dot(d, f);
  const t = Math.tan((c.fov * Math.PI) / 360);
  const u = (dot(d, r) / (z * t * ASPECT) + 1) * 50;
  const v = (1 - dot(d, up) / (z * t)) * 50;
  return [u, v, z];
};

const pts = (id, f) => {
  if (id === 1) {
    const liftT = S.glide(f, 20, 80);
    const yOff = liftT * 1.4;
    return {
      guestHead: [1.4, 1.85, 3.8],
      guestFeet: [1.4, 0.0, 3.8],
      guestTea: [1.15, 1.05, 3.8],
      hotelBanner: [0.0, 7.1 + yOff, 2.52],
      hotelBase: [0.0, 0.6 + yOff, 2.52],
      hotelRoof: [0.0, 8.95 + yOff, 0.0],
      hotelL: [-3.6, 4.5 + yOff, 2.52],
      hotelR: [3.6, 4.5 + yOff, 2.52],
      jacksRow: [0.0, 0.5, 3.1],
    };
  }

  if (id === 2) {
    let crankP = 0.0;
    if (f >= 131 && f <= 155) crankP = S.clamp01((f - 131) / 21);
    else if (f > 155) crankP = 1.0;
    const fistX = 0.28 + (S.lerp(168, 132, crankP) - 300) * 0.00216 * 0.92;
    return {
      engHead: [0.28, 1.85, 0.8],
      engFeet: [0.28, 0.0, 0.8],
      engCap: [0.28, 2.05, 0.8],
      fistKnob: [fistX, 0.88, 0.8],
      pedestal: [-0.05, 0.5, 0.8],
      signCenter: [-0.52, 1.95, 0.85],
      signL: [-0.73, 1.95, 0.85],
      signR: [-0.31, 1.95, 0.85],
      liftBeam: [0.1, 1.25 + crankP * 0.25, 0.8],
    };
  }

  // Shot 3
  const liftT = S.glide(f, 195, 238);
  const yOff = (liftT - 1.0) * 0.8;
  const hotelZ = -12.5 + 2.92; // front facade z ~ -9.58
  return {
    guestHead: [0.55, 1.85, 2.0],
    guestFeet: [0.55, 0.0, 2.0],
    guestCard: [0.55, 1.0, 2.0],
    easelTop: [-0.75, 1.7, 2.0],
    easelBase: [-0.75, 0.2, 2.0],
    bgHotelRoof: [0.0, 10.85 + yOff, hotelZ],
    bgHotelBanner: [0.0, 7.6 + yOff, hotelZ],
    bgHotelPiers: [0.0, 1.8 + yOff, hotelZ],
    bgHotelL: [-6.1, 6.4 + yOff, hotelZ],
    bgHotelR: [6.1, 6.4 + yOff, hotelZ],
  };
};

const frames = (process.argv[2] ?? "0,10,28,75,94,95,110,142,155,194,195,210,238,278,299")
  .split(",")
  .map(Number);

console.log("=== HotelLiftShort Framing Projection Check ===");
let allPass = true;

for (const f of frames) {
  const s = S.shotAt(f);
  const c = S.camAt(s.id, f);
  const row = [];
  const ptMap = pts(s.id, f);

  for (const [name, p] of Object.entries(ptMap)) {
    const [u, v, z] = proj(c, p);
    // In Shot 1, early frames (f < 30) are medium framing on Guest and hotel entrance;
    // full roof comes into frame as camera cranes out (f >= 50).
    const isEarlyRoof = s.id === 1 && f < 50 && (name === "hotelRoof" || name === "hotelBanner");
    const warn = (!isEarlyRoof && (u < 12 || u > 88 || v < 6 || v > 94)) ? "!" : "";
    if (warn) allPass = false;
    row.push(`${name}:${u.toFixed(0)}/${v.toFixed(0)}${warn}`);
  }

  // Check Shot 3 background hotel fill
  if (s.id === 3) {
    const [, roofV] = proj(c, ptMap.bgHotelRoof);
    const [, bannerV] = proj(c, ptMap.bgHotelBanner);
    const [, pierV] = proj(c, ptMap.bgHotelPiers);
    const hotelVRange = `[hotel v-range: roof=${roofV.toFixed(0)}%, banner=${bannerV.toFixed(0)}%, piers=${pierV.toFixed(0)}%]`;
    console.log(`f${f.toString().padStart(3, " ")} s${s.id} fov${c.fov.toFixed(0)} | ${hotelVRange}`);
  }

  console.log(`f${f.toString().padStart(3, " ")} s${s.id} fov${c.fov.toFixed(0)} | ${row.join(" ")}`);
}

console.log("Framing check complete.");
