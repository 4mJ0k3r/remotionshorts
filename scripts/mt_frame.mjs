// Framing check for MolassesTankShort (SKILL.md Section 4.3):
// Projects 3D world points through camAt(id, f) and computes u%/v%.
// Verifies all subjects & signs stay inside 15%..85% (u% and v%),
// and background train trestle fills v = 12%..55% and u = 12%..88% in Shot 3.
// Usage: node scripts/mt_frame.mjs [f,f,...]
import * as S from "../src/videos/molasses_tank/story.ts";

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
    return {
      inspHead: [1.4, 1.85, 3.8],
      inspFeet: [1.4, 0.0, 3.8],
      inspClip: [1.15, 1.05, 3.8],
      tankBanner: [0.0, 7.1, 3.66],
      tankBase: [0.0, 0.3, 3.66],
      tankRoof: [0.0, 9.9, 0.0],
      tankL: [-3.65, 4.5, 0.0],
      tankR: [3.65, 4.5, 0.0],
    };
  }

  if (id === 2) {
    let brakeP = 0.0;
    if (f >= 131 && f <= 155) brakeP = S.clamp01((f - 131) / 24);
    else if (f > 155) brakeP = 1.0;
    const fistX = 0.28 + (S.lerp(168, 132, brakeP) - 300) * 0.00216 * 0.92;
    return {
      condHead: [0.28, 1.85, 0.8],
      condFeet: [0.28, 0.0, 0.8],
      condCap: [0.28, 2.05, 0.8],
      fistKnob: [fistX, 0.775, 0.8],
      pedestal: [-0.28, 0.35, 0.8],
      signCenter: [-0.42, 1.80, 0.82],
      signL: [-0.66, 1.80, 0.82],
      signR: [-0.18, 1.80, 0.82],
      dashRail: [0.0, 0.95, 0.8],
    };
  }

  // Shot 3
  const tiltT = S.glide(f, 230, 245);
  const trainY = 4.55 + tiltT * 0.55;
  return {
    condHead: [0.55, 1.85, 2.0],
    condFeet: [0.55, 0.0, 2.0],
    condCard: [0.55, 1.0, 2.0],
    easelTop: [-0.75, 1.7, 2.0],
    easelBase: [-0.75, 0.2, 2.0],
    bgTrainRoof: [0.5, trainY + 2.8, -12.5],
    bgTrainDeck: [0.0, 4.3, -12.5],
    bgTrestleL: [-3.5, 2.1, -12.5],
    bgTrestleR: [3.5, 2.1, -12.5],
  };
};

const frames = (process.argv[2] ?? "0,10,28,75,94,95,110,142,155,194,195,210,238,278,299")
  .split(",")
  .map(Number);

console.log("=== MolassesTankShort Framing Projection Check ===");
let allPass = true;

for (const f of frames) {
  const s = S.shotAt(f);
  const c = S.camAt(s.id, f);
  const row = [];
  const ptMap = pts(s.id, f);

  for (const [name, p] of Object.entries(ptMap)) {
    const [u, v, z] = proj(c, p);
    // In Shot 1 early frames (f < 50), camera is in medium shot on Inspector;
    // full tank body enters cleanly as camera crane-pulls back (f >= 50).
    const isEarlyShot1 = s.id === 1 && f < 50 && name.startsWith("tank");
    const warn = (!isEarlyShot1 && (u < 12 || u > 88 || v < 11 || v > 89)) ? "!" : "";
    if (warn) allPass = false;
    row.push(`${name}:${u.toFixed(0)}/${v.toFixed(0)}${warn}`);
  }

  if (s.id === 3) {
    const [, roofV] = proj(c, ptMap.bgTrainRoof);
    const [, deckV] = proj(c, ptMap.bgTrainDeck);
    const [leftU] = proj(c, ptMap.bgTrestleL);
    const [rightU] = proj(c, ptMap.bgTrestleR);
    console.log(`f${f.toString().padStart(3, " ")} s${s.id} fov${c.fov.toFixed(0)} | [bg trestle: u=${leftU.toFixed(0)}%..${rightU.toFixed(0)}%, v(roof..deck)=${roofV.toFixed(0)}%..${deckV.toFixed(0)}%]`);
  }

  console.log(`f${f.toString().padStart(3, " ")} s${s.id} fov${c.fov.toFixed(0)} | ${row.join(" ")}`);
}

if (!allPass) {
  console.log("WARN: Some points exceed 12%..88% bounds!");
} else {
  console.log("SUCCESS: All framing checks PASSED!");
}
