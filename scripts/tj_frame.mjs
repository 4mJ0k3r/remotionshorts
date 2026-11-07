// Framing check for TowerJumpShort (SKILL 4.3): projects named world points through camAt(id, f) and prints u%/v%.
// usage: node scripts/tj_frame.mjs [f,f,...]
import * as S from "../src/videos/tower_jump/story.ts";
const ASPECT = 1080 / 1920;
const proj = (c, p) => {
  const f = norm(sub(c.look, c.pos)), r = norm([-f[2], 0, f[0]]), up = cross(r, f), d = sub(p, c.pos);
  const z = dot(d, f), t = Math.tan((c.fov * Math.PI) / 360);
  return [(dot(d, r) / (z * t * ASPECT) + 1) * 50, (1 - dot(d, up) / (z * t)) * 50, z];
};
const sub = (a, b) => a.map((v, i) => v - b[i]), dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(...a); return a.map((v) => v / l); };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const H = 1.91, HW = 0.32; // card head top (975-90)*SU, head half width 145*SU
const busW = (b, pose) => S.toWorld(b, pose.x, pose.y + 2.0 * (b === S.BR1 ? 1 : 1), 0);
const pts = (id, f) => {
  if (id === 1) {
    const w = S.WATCH, bp = S.busShot1(f), bus = S.toWorld(S.BR1, bp.x, bp.y + 1.9);
    return { watchHead: [w[0], w[1] + H, w[2]], watchFeet: w, watchL: [w[0] - HW, w[1] + 1.6, w[2]], watchR: [w[0] + HW + 0.15, w[1] + 1.4, w[2]],
      busC: bus, busRear: S.toWorld(S.BR1, bp.x - 3, bp.y + 1), busFront: S.toWorld(S.BR1, bp.x + 3, bp.y + 3.8),
      towerLout: S.toWorld(S.BR1, -10.3, 10), towerRout: S.toWorld(S.BR1, 10.3, 10), towerTop: S.toWorld(S.BR1, 8.5, 2.8 + 15 + 3.5), sign: S.toWorld(S.BR1, 0, 11.4, 1.9), water: [0, 0, 6] };
  }
  if (id === 2) {
    const d = S.DRV2;
    return { headTop: [d[0], H, d[2]], headL: [d[0] - HW, 1.62, d[2]], headR: [d[0] + HW, 1.62, d[2]], fist: [d[0] - 0.335, 0.853, d[2]],
      feet: [d[0], 0, d[2]], pedL: [-0.4, 0.5, 2.0], sign: [S.GAPSIGN[0], 2.41, S.GAPSIGN[2]], signL: [S.GAPSIGN[0] - 0.32, 2.18, S.GAPSIGN[2]], signR: [S.GAPSIGN[0] + 0.32, 2.18, S.GAPSIGN[2]] };
  }
  const d = S.DRV3, bp = S.busShot3(f);
  return { headTop: [d[0], H, d[2]], drvR: [d[0] + 0.36, 1.2, d[2]], feet: [d[0], 0, d[2]], cheque: [d[0], 1.06, d[2] + 0.02],
    easelL: [S.EASEL[0] - 0.42, 1.4, S.EASEL[2]], easelTop: [S.EASEL[0], 1.75, S.EASEL[2]], bus: busW(S.BR3, bp),
    towerL: S.toWorld(S.BR3, -10.3, 15), towerR: S.toWorld(S.BR3, 10.3, 15), towerTop: S.toWorld(S.BR3, 8.5, 9 + 18.5), lamp: [S.LAMP[0], 3.3, S.LAMP[2]] };
};
const frames = (process.argv[2] ?? "0,10,28,75,94,95,110,155,194,195,210,238,278,299").split(",").map(Number);
for (const f of frames) {
  const id = S.shotAt(f).id, c = S.camAt(id, f);
  const row = Object.entries(pts(id, f)).map(([k, p]) => { const [u, v] = proj(c, p); const bad = u < 0 || u > 100 || v < 0 || v > 100 ? "!" : u < 15 || u > 85 || v < 8 || v > 92 ? "~" : ""; return `${k} ${u.toFixed(0)}/${v.toFixed(0)}${bad}`; });
  console.log(`f${f} s${id} fov${c.fov.toFixed(0)} | ${row.join("  ")}`);
}
