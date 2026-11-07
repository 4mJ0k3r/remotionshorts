// Per-frame sweep for the defect is_frame's aggregate min/max hides: a card whose HEAD straddles a frame border in
// some single frame, i.e. the audience sees a face cut in half. Aggregate rows smear a card that walks cleanly out
// of frame with one that is sliced on the edge, so this samples frame by frame.
import * as S from "../src/videos/instant_skill/story.ts";

const ASPECT = 1080 / 1920;
const SU = 0.00216;
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const basis = (c) => {
  const f = norm(sub(c.look, c.pos));
  const r = norm([-f[2], 0, f[0]]);
  return { f, r, up: cross(r, f), t: Math.tan((c.fov * Math.PI) / 360) };
};
const proj = (c, p, B = basis(c)) => {
  const d = sub(p, c.pos);
  const z = dot(d, B.f);
  if (z <= 0.06) return null;
  return [(dot(d, B.r) / (z * B.t * ASPECT) + 1) * 50, (1 - dot(d, B.up) / (z * B.t)) * 50, z];
};

const half = new Map();   // frames where the face is between 30% and 95% on screen
let hits = 0;
for (const s of S.SHOTS) {
  const row = S.CAST_SLOTS[s.id] ?? [];
  const worst = new Map();
  const span = new Map();
  for (let f = s.a; f < s.b; f += 2) {
    const c = S.camAt(s.id, f);
    const B = basis(c);
    for (const slot of row) {
      if (slot.hide && slot.hide(f)) continue;
      if (slot.primary || slot.required || slot.ots) continue;   // already policed by is_frame
      const at = slot.path ? slot.path(f) : slot.at;
      const m = SU * slot.scale;
      const seat = slot.seated !== undefined ? S.seatM(slot.seated, slot.scale) : 0;
      // The painted head is a circle of r = 145 design units in the CARD plane. A card is yaw-billboarded, so that
      // plane holds the camera-right axis and world up - offsetting along world x instead of B.r measures a chord
      // that shrinks toward the horizon and fakes a half-cut on any card shot from the side. Four corners of the
      // in-plane square that bounds the circle, projected.
      const r = 145 * m;
      const ctr = [at[0], at[1] + S.eyeY(slot.scale) - seat, at[2]];
      const rt = B.r;
      const corners = [[+1, +1], [+1, -1], [-1, +1], [-1, -1]]
        .map(([sr, su]) => proj(c, [ctr[0] + sr * r * rt[0], ctr[1] + su * r, ctr[2] + sr * r * rt[2]], B));
      if (corners.some((p) => !p)) continue;
      const u0 = Math.min(...corners.map((p) => p[0])), u1 = Math.max(...corners.map((p) => p[0]));
      const v0 = Math.min(...corners.map((p) => p[1])), v1 = Math.max(...corners.map((p) => p[1]));
      // the share of the head that is actually on screen
      const su = Math.max(0, Math.min(u1, 100) - Math.max(u0, 0)) / Math.max(1e-6, u1 - u0);
      const sv = Math.max(0, Math.min(v1, 100) - Math.max(v0, 0)) / Math.max(1e-6, v1 - v0);
      const inside = su * sv;
      if (inside > 0.12 && inside < 0.97) {
        const key = slot.n;
        span.set(key, (span.get(key) ?? 0) + 2);
        if (inside > 0.3 && inside < 0.95) half.set(`${s.id}|${key}`, (half.get(`${s.id}|${key}`) ?? 0) + 2);
        const cur = worst.get(key);
        if (!cur || inside > cur.inside) worst.set(key, { inside, f, u0, u1, v0, v1 });
      }
    }
  }
  for (const [n, w] of worst) {
    const frames = half.get(`${s.id}|${n}`) ?? 0;
    if (frames < 8) continue;                       // a camera sweep passing a card slices it for a few frames; that
    hits++;                                        // is a move, not a composition, so only a sustained half-face counts
    console.log(`s${String(s.id).padEnd(2)} f${String(w.f).padEnd(4)} ${n.padEnd(11)} head u ${w.u0.toFixed(1)}..${w.u1.toFixed(1)} ` +
      `v ${w.v0.toFixed(1)}..${w.v1.toFixed(1)} -> ${(w.inside * 100).toFixed(0)}% on screen, ` +
      `half-cut for ${frames} of ${s.b - s.a} frames`);
  }
}
console.log(hits ? `${hits} unpoliced cards are sliced by a frame edge somewhere` : "SUCCESS: every unpoliced card is either wholly in frame or wholly out");
