// Camera-only motion profile (the "Ours" method in references/reports/motion.md): project a 5x5 point grid on the
// subject plane through camAt(id, f) and camAt(id, f+1), fit the similarity, integrate the same speed classes.
// This isolates the camera from character motion (the rendered-video measure in motion_profile.py includes both).
// Usage: node scripts/cam-profile.mjs [firstFrame] [lastFrame] [out.json]
import fs from "node:fs";
import * as THREE from "three";
import { camAt, shotAt, SHOTS } from "../src/videos/bridge/story.ts";

const [first = "0", last = "1500", out] = process.argv.slice(2);
const F0 = Number(first), F1 = Number(last), FPS = 30, W = 720, H = 1280;
const GRID = [-0.8, -0.4, 0, 0.4, 0.8];
const makeCam = (c) => {
  const cam = new THREE.PerspectiveCamera(c.fov, W / H, 0.1, 2000);
  cam.position.set(...c.pos);
  cam.up.set(0, 1, 0);
  cam.lookAt(new THREE.Vector3(...c.look));
  cam.rotateZ(c.roll);
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();
  return cam;
};
const src = [];
for (const y of GRID) for (const x of GRID) src.push([(x * 0.5 + 0.5) * W, (0.5 - y * 0.5) * H]);
const world = (c, nx, ny) => {
  const cam = makeCam(c);
  const d = new THREE.Vector3(nx, ny, 0.5).unproject(cam).sub(cam.position).normalize();
  const L = new THREE.Vector3(...c.look).distanceTo(cam.position);
  return cam.position.clone().addScaledVector(d, L / d.dot(new THREE.Vector3(...c.look).sub(cam.position).normalize()));
};
const fit = (dst) => {
  let sx = 0, sy = 0, dx = 0, dy = 0;
  for (const p of src) { sx += p[0]; sy += p[1]; }
  for (const q of dst) { dx += q[0]; dy += q[1]; }
  const n = src.length; sx /= n; sy /= n; dx /= n; dy /= n;
  let aa = 0, bb = 0, den = 0;
  for (let i = 0; i < n; i++) {
    const px = src[i][0] - sx, py = src[i][1] - sy, qx = dst[i][0] - dx, qy = dst[i][1] - dy;
    aa += px * qx + py * qy; bb += px * qy - py * qx; den += px * px + py * py;
  }
  const a = aa / den, b = bb / den;
  const tx = dx - (a * sx - b * sy), ty = dy - (b * sx + a * sy);
  return { dx: tx, dy: ty, scale: Math.hypot(a, b), rot: (Math.atan2(b, a) * 180) / Math.PI };
};
const speeds = [], zooms = [], rolls = [], dxs = [], cut = [];
for (let f = F0; f < F1; f++) {
  const a = shotAt(f), b = shotAt(f + 1);
  if (a.id !== b.id) { cut.push(f + 1); speeds.push(NaN); zooms.push(NaN); rolls.push(NaN); dxs.push(NaN); continue; }
  const c0 = camAt(a.id, f), c1 = camAt(a.id, f + 1);
  const dst = [];
  for (const y of GRID) for (const x of GRID) {
    const p = world(c0, x, y).project(makeCam(c1));
    dst.push([(p.x * 0.5 + 0.5) * W, (0.5 - p.y * 0.5) * H]);
  }
  const r = fit(dst);
  const tr = Math.hypot(r.dx, r.dy), zm = Math.abs(r.scale - 1) * 734;
  speeds.push(tr + zm); zooms.push((r.scale - 1) * 100); rolls.push(r.rot); dxs.push(r.dx);
}
// hard cuts inside a shot (CAMS cut keys) land as a huge one-frame jump: mask them and their neighbours
for (let i = 0; i < speeds.length; i++) if (!Number.isNaN(speeds[i]) && speeds[i] > 200) {
  for (const j of [i - 1, i, i + 1]) if (j >= 0 && j < speeds.length) { speeds[j] = NaN; zooms[j] = NaN; rolls[j] = NaN; dxs[j] = NaN; }
}
const S = speeds.filter((x) => !Number.isNaN(x));
const q = (p) => [...S].sort((x, y) => x - y)[Math.floor((S.length - 1) * p)];
const hold = 100 * S.filter((x) => x < 0.3).length / S.length;
const drift = 100 * S.filter((x) => x >= 0.3 && x < 2).length / S.length;
const move = 100 * S.filter((x) => x >= 2).length / S.length;
const bursts = [];
for (let i = 1; i < speeds.length - 1; i++) {
  if (!(speeds[i] >= 6) || !(speeds[i] >= speeds[i - 1]) || !(speeds[i] > speeds[i + 1])) continue;
  const lo = speeds[i] * 0.1;
  let a = i, b = i;
  while (a > 0 && speeds[a - 1] > lo) a--;
  while (b < speeds.length - 1 && speeds[b + 1] > lo) b++;
  if (!bursts.length || i - bursts[bursts.length - 1].peak > 6) bursts.push({ peak: i + F0, v: +speeds[i].toFixed(1), attack: i - a, release: b - i });
}
const quiet = speeds.map((v, i) => (v < 2 ? i : -1)).filter((i) => i >= 0);
const zq = quiet.map((i) => Math.abs(zooms[i]));
const rq = rolls.filter((x) => !Number.isNaN(x)).map(Math.abs).sort((a, b) => a - b);
const res = { frames: S.length, cut_frames: cut.length, hold_pct: +hold.toFixed(1), drift_pct: +drift.toFixed(1), move_pct: +move.toFixed(1),
  median_speed: +q(0.5).toFixed(2), p90_speed: +q(0.9).toFixed(2), max_speed: +Math.max(...S).toFixed(1),
  zoom_rate_quiet_median_pct: +zq.sort((a, b) => a - b)[Math.floor(zq.length / 2)].toFixed(3),
  zoom_in_share_pct: +(100 * quiet.filter((i) => zooms[i] > 0.05).length / quiet.length).toFixed(1),
  roll_abs_median_deg: +rq[Math.floor(rq.length / 2)].toFixed(2),
  moves_per_10s: +(bursts.length * 10 / (S.length / FPS)).toFixed(1), attack_median: bursts.length ? bursts.map((b) => b.attack).sort((a, b) => a - b)[Math.floor(bursts.length / 2)] : 0,
  release_median: bursts.length ? bursts.map((b) => b.release).sort((a, b) => a - b)[Math.floor(bursts.length / 2)] : 0,
  bursts: bursts.sort((a, b) => b.v - a.v).slice(0, 24) };
console.log(JSON.stringify({ ...res, bursts: undefined }, null, 1));
console.log("top bursts", res.bursts);
if (out) {
  fs.writeFileSync(out, JSON.stringify(res, null, 1));
  fs.writeFileSync(out.replace(/\.json$/, "_speeds.csv"), "f,speed,zoom,roll,dx\n" + speeds.map((v, i) => `${i + F0},${v},${zooms[i]},${rolls[i]},${dxs[i]}`).join("\n"));
}
