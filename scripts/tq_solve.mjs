// Tiny aim solver for a still key: find the yaw/pitch of a camera at a fixed position that puts each anchor point at
// the requested screen u/v. Used to author the CAMS keys in story.ts, then tq_frame.mjs gates the result.
//   node scripts/tq_solve.mjs 1 "4.6,3.4,10.6" 46 "3.0,3.9,9.0:70,62" "-11,2.6,0.78:30,42"
import { camAt } from "../src/videos/tower_qwen/story.ts";
const ASPECT = 1080 / 1920;
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const norm = (v) => { const l = Math.hypot(...v); return [v[0] / l, v[1] / l, v[2] / l]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const fwd = (yaw, pitch) => [Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)];

const uvOf = (pos, f, fov, P) => {
  const n = norm(f), r = norm(cross(f, [0, 1, 0])), u = cross(r, f);
  const w = sub(P, pos), d = dot(w, f);
  const half = 2 * Math.tan((fov * Math.PI) / 360);
  return { u: 0.5 + dot(w, r) / d / (half * ASPECT), v: 0.5 + dot(w, u) / d / half, d };
};

const [, , shot, posS, fovS, ...anchors] = process.argv;
const pos = posS.split(",").map(Number);
const fov = Number(fovS);
const A = anchors.map((s) => {
  const [p, t] = s.split(":");
  const [u, v] = t.split(",").map((k) => Number(k) / 100);
  return { p: p.split(",").map(Number), u, v };
});
const err = (yaw, pitch) => {
  let a = 0;
  for (const t of A) {
    const r = uvOf(pos, fwd(yaw, pitch), fov, t.p);
    if (r.d < 1) return Infinity;   // anchors behind the lens are not "framed", they are invisible
    a += (r.u - t.u) ** 2 + (r.v - t.v) ** 2;
  }
  return a;
};
let best = [0, 0, Infinity];
for (let yi = -180; yi <= 180; yi++) for (let pi = -40; pi <= 40; pi++) {
  const e = err((yi * Math.PI) / 180, (pi * Math.PI) / 180);
  if (e < best[2]) best = [(yi * Math.PI) / 180, (pi * Math.PI) / 180, e];
}
for (let step = 0.1; step > 1e-4; step /= 3) {
  for (const dy of [-step, 0, step]) for (const dp of [-step, 0, step]) {
    const y = best[0] + dy, p = best[1] + dp, e = err(y, p);
    if (e < best[2]) best = [y, p, e];
  }
}
const f = fwd(best[0], best[1]);
const D = Math.min(...A.map((t) => Math.hypot(...sub(t.p, pos))));
const look = pos.map((v, i) => v + f[i] * D * 1.6);
console.log(`shot ${shot} yaw ${(best[0] * 180 / Math.PI).toFixed(2)}deg pitch ${(best[1] * 180 / Math.PI).toFixed(2)}deg rms ${Math.sqrt(best[2] / A.length).toFixed(4)}`);
console.log(`  pos  [${pos.map((v) => v.toFixed(2)).join(", ")}]`);
console.log(`  look [${look.map((v) => v.toFixed(2)).join(", ")}]  (fov ${fov})`);
A.forEach((t, i) => { const r = uvOf(pos, f, fov, t.p); console.log(`  anchor${i}: want u${(t.u * 100).toFixed(0)} v${(t.v * 100).toFixed(0)} -> u ${(r.u * 100).toFixed(1)} v ${(r.v * 100).toFixed(1)} d ${r.d.toFixed(2)}`); });
if (shot) { const c = camAt(Number(shot), 0); console.log(`  (current story.ts key at f0: pos [${c.pos.map((v) => v.toFixed(2))}] look [${c.look.map((v) => v.toFixed(2))}] fov ${c.fov})`); }
