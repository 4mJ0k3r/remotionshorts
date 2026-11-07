// Framing check for ElevatorCrushShort (SKILL.md Section 4.3): projects 3D points through camAt(id, f) -> u% / v%.
// Main subjects (heads, hats, waists, key props) must sit inside 15..85 %, secondary points inside 5..95 %.
// Also prints the camera yaw per shot so cut-to-cut angle changes can be checked.
// Usage: node scripts/ec_frame.mjs [f,f,...]
import * as S from "../src/videos/elevator_crush/story.ts";

const ASPECT = 1080 / 1920;
const SU = 0.00216, HS = 0.92, CS = 0.86;
const sub = (a, b) => a.map((v, i) => v - b[i]);
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(...a); return a.map((v) => v / l); };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const proj = (c, p) => {
  const f = norm(sub(c.look, c.pos));
  const r = norm([-f[2], 0, f[0]]);
  const up = cross(r, f);
  const d = sub(p, c.pos);
  const z = dot(d, f);
  const t = Math.tan((c.fov * Math.PI) / 360);
  return [(dot(d, r) / (z * t * ASPECT) + 1) * 50, (1 - dot(d, up) / (z * t)) * 50, z];
};
const Y = (dy, s) => (975 - dy) * SU * s;
// main = [x,z] of a character -> head / hat top / waist, and side edges of the body (secondary)
const ch = (name, x, z, s, main = true) => ({
  [`${name}Head`]: { p: [x, Y(235, s), z], main },
  [`${name}Top`]: { p: [x, Y(70, s), z], main },
  [`${name}Waist`]: { p: [x, Y(560, s), z], main: false },
  [`${name}L`]: { p: [x - 0.16, Y(400, s), z], main: false },
  [`${name}R`]: { p: [x + 0.16, Y(400, s), z], main: false },
});

const pts = (id, f) => {
  switch (id) {
    case 1: return { ...ch("hero", -0.4, 1.5, HS), ...ch("crush", 0.42, 1.15, CS), led: { p: [0, 2.95, -1.7], main: false } };
    case 2: {
      const o = { ...ch("hero", -0.45, 0.9, HS), doors: { p: [0, 1.2, -1.9], main: false }, window: { p: [0, 1.75, -4.74], main: false } };
      if (f >= 335) Object.assign(o, ch("crush", 0.42, 1.25, CS));
      return o;
    }
    case 3: return { ...ch("hero", -0.4, 1.3, HS), ...ch("crush", 0.42, 0.95, CS), sparkL: { p: [-0.55, 2.9, -1.55], main: false } };
    case 4: return { ...ch("hero", -0.6, 0.7, HS), ...ch("crush", 0.6, 0.95, CS), phoneH: { p: [-0.6 + 108 * SU * HS, Y(410, HS), 0.7], main: true } };
    case 5: {
      const o = {};
      if (f < 1020) Object.assign(o, ch("crush", -1.15, -0.8, CS));
      if (f > 1060) Object.assign(o, ch("hero", 1.55, -1.4, HS), { knob: { p: [1.55 - 155 * SU * HS * 0.93, Y(565, HS), -1.6], main: true } });
      return o;
    }
    case 6: return { ...ch("hero", 0.15, 1.35, HS), ...ch("crush", -0.55, 0.25, CS, false), growl: { p: [0.15 - 150 * SU * HS, Y(640, HS), 1.35], main: false } };
    case 7: return { ...ch("hero", -0.42, 1.2, HS), ...ch("crush", 0.45, 0.9, CS), hatch: { p: [0, 3.8, 0.5], main: true } };
    case 8: return { ...ch("hero", -0.15, 1.4, HS), ...ch("crush", f >= 1880 ? 0.2 : 0.75, f >= 1880 ? 1.58 : 1.1, CS) };
    case 9: case 10: return { ...ch("hero", -0.17, 1.35, HS), ...ch("crush", 0.17, 1.58, CS) };
    default: return { ...ch("hero", -0.22, 1.3, HS), ...ch("crush", 0.24, 1.5, CS), palm: { p: [-0.22 + 150 * SU * HS, Y(430, HS), 1.3], main: true } };
  }
};

const frames = (process.argv[2] ?? "100,320,500,800,960,1100,1380,1720,1950,2350,2700,3150").split(",").map(Number);
console.log("=== ElevatorCrushShort framing check (main 15..85 %, secondary 5..95 %) ===");
let bad = 0;
for (const f of frames) {
  const s = S.shotAt(f);
  const c = S.camAt(s.id, f);
  const row = [];
  for (const [name, { p, main }] of Object.entries(pts(s.id, f))) {
    const [u, v, z] = proj(c, p);
    const lo = main ? 15 : 5, hi = main ? 85 : 95;
    const warn = z <= 0 || u < lo || u > hi || v < lo || v > hi ? (main ? "!!" : "!") : "";
    if (warn === "!!") bad++;
    row.push(`${name}:${u.toFixed(0)}/${v.toFixed(0)}${warn}`);
  }
  const yaw = (Math.atan2(c.look[0] - c.pos[0], -(c.look[2] - c.pos[2])) * 180) / Math.PI;
  const dist = Math.hypot(...sub(c.look, c.pos));
  console.log(`f${String(f).padStart(4)} s${String(s.id).padStart(2)} fov${c.fov} yaw${yaw.toFixed(0)} d${dist.toFixed(2)} | ${row.join(" ")}`);
}
console.log(`main-subject violations: ${bad}`);
