// Framing + camera-intent check for InstantSkillShort (SKILL.md 4.3-4.4, revision brief gates 1 and 5).
//
// There are no in-world easels or placards, so there are no boards to project. What is left to prove is the
// composition itself, and it is proven with numbers before a single pixel renders. The checker knows nothing about
// individual shots: it walks story.ts's declarative staging tables (CAST_SLOTS / PROP_QUADS / COVER_SHELLS /
// SKYLINES / TIGHT_SHOTS), so a 25-shot film is covered by the same laws the 8-shot first act was, automatically.
//
//   HEAD       a character's crown + eye column. PRIMARY subject inside u 15..85 / v 8..92, SECONDARY inside
//              u 8..92. Crown never above v 22: the HUD pill band owns v 14..19 and a head must not enter it.
//   HEADW      the head's own painted width as a fraction of frame width, 11..68. Under 11 the face is a dot and
//              the expression is wasted; over 68 the lens is so close the head crowds both borders.
//   BODY       the painted silhouette, +/-175 design units (shoulders and arms) or +/-260 for a card authored
//              holding something. Nothing may be sliced off the frame border unless the shot says it may.
//   PROP       the 3D king, the cube, the pot, the car, the memory screens: centre and corners inside 12..88.
//   COVER      the plates an INTERIOR set is closed with (COVER_SHELLS per set + any animated row in PROP_QUADS),
//              judged as their UNION: no sample inside the rect the required cast occupies may sit behind a body and
//              on no plate. A corner that falls BEHIND the lens is pushed off the matching side of the frame, which
//              is what lets a 32 m wall plate inside a 13 m room be proven to overfill. The four outdoor sets are
//              exempt — world.ts paints a 900 m gradient dome behind them, so their backdrop is never void.
//   SKYLINE    every outdoor shot in SKYLINES: rooflines sampled ACROSS each block's width, because a 9:16 lens at
//              fov 45 only sees ~27 degrees of azimuth — a block's centre can sit outside the frame while its roof
//              runs right through it. Enough rooflines in shot to read as a place, enough with sky above them that
//              the top of the frame is not a wall, and a limit on how many may be cropped by the top edge.
//   ANGLES     every pair of the 25 shots must differ by azimuth >= 25 deg, subject-distance ratio >= 1.4,
//              lens height >= 0.45 m or view pitch >= 8 deg — the "never repeat a front-on camera" rule.
//   LENS       the primary subject's circle of confusion, in output px: sharp from the shot's first frame.
// Usage: node scripts/is_frame.mjs [step]
import * as S from "../src/videos/instant_skill/story.ts";

const ASPECT = 1080 / 1920;
const SU = 0.00216;
const OFF = 9e9;                     // sentinel: this edge is not merely outside the band, it is off the frame

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

/**
 * Pinhole projection into screen percentages; v is measured from the top edge.
 *
 * A point behind the lens has no screen position at all — the raw formula returns a mirrored, enormous one, which
 * is how a card walking past the camera got reported as "torso sliced off the right border". So those points are
 * mapped onto the side they fall off: off to the right if the perpendicular offset is +, off to the left if -, and
 * off the bottom/top for the vertical. A composition law can then be stated as "inside u 15..85" and still be
 * honest about a subject that has left the frame entirely.
 */
const basis = (c) => {
  const f = norm(sub(c.look, c.pos));
  const r = norm([-f[2], 0, f[0]]);
  return { f, r, up: cross(r, f), t: Math.tan((c.fov * Math.PI) / 360) };
};
const proj = (c, p, B = basis(c)) => {
  const d = sub(p, c.pos);
  const z = dot(d, B.f);
  const x = dot(d, B.r), y = dot(d, B.up);
  if (z <= 0.06) return [(x >= 0 ? OFF : -OFF) * (1 + Math.abs(x) / 10), (y >= 0 ? -OFF : OFF) * 1.1, z];
  return [(x / (z * B.t * ASPECT) + 1) * 50, (1 - y / (z * B.t)) * 50, z];
};

/** projected rectangle of a point set. `front` = every point was in front of the lens, which is what makes a
 *  rectangle usable as a depth-tested occluder rather than an edge-of-frame smear. */
const rectOf = (c, pts) => {
  const B = basis(c);
  let u0 = OFF, u1 = -OFF, v0 = OFF, v1 = -OFF, z = 0, nz = 0;
  for (const p of pts) {
    const [u, v, zz] = proj(c, p, B);
    if (zz > 0.06) nz++;
    z += zz;
    if (u < u0) u0 = u; if (u > u1) u1 = u;
    if (v < v0) v0 = v; if (v > v1) v1 = v;
  }
  return { u0, u1, v0, v1, z: z / pts.length, front: nz === pts.length };
};

const CH = S.CHESS, PK = S.POKER;
const KING_DROP = 0.07;            // world.ts holds the pinned king's base on the tabletop

/** Rule B, recomputed here instead of trusting the authored rest pose: where the fist actually is this frame.
 *  A 3D prop welded to a 2D hand needs the live camera, so any prop story.ts can only describe as a design-space
 *  point on a card is solved with this — shot 5's king and shot 24's glyph. */
const fistWorld = (camPos, c, dx, dy, scale = S.ACTOR_SCALE) => {
  const yaw = Math.atan2(camPos[0] - c[0], camPos[2] - c[2]);
  const lx = (dx - 300) * SU * scale, ly = (975 - dy) * SU * scale, dep = -0.08;
  return [
    c[0] + Math.cos(yaw) * lx + Math.sin(yaw) * dep,
    c[1] + ly,
    c[2] - Math.sin(yaw) * lx + Math.cos(yaw) * dep,
  ];
};

// ---------------------------------------------------------------- cast, from the tables
const fatal = [];
for (const s of S.SHOTS) {
  const row = S.CAST_SLOTS[s.id];
  if (!row) fatal.push(`s${s.id}: no CAST_SLOTS row - the checker cannot see this shot at all`);
  else {
    const prim = row.filter((x) => x.primary).length;
    if (prim !== 1) fatal.push(`s${s.id}: ${prim} primary cards in CAST_SLOTS (needs exactly 1 - the lens and focus key off it)`);
    const names = new Set(row.map((x) => x.n));
    if (names.size !== row.length) fatal.push(`s${s.id}: duplicate CAST_SLOTS card names - occlusion and crop rows would collide`);
  }
}

/** the cards actually on screen at frame f: [name, feet, scale, primary, slot] */
const castFor = (id, f) =>
  (S.CAST_SLOTS[id] ?? [])
    .filter((s) => !(s.hide && s.hide(f)))
    .map((s) => [s.n, s.path ? s.path(f) : [s.at[0], s.at[1], s.at[2]], s.scale, !!s.primary, s]);

const flagSet = (id, key) => (S.CAST_SLOTS[id] ?? []).filter((s) => s[key]).map((s) => s.n);
const requiredOf = (id) => flagSet(id, "required");
const otsOf = (id) => flagSet(id, "ots");
const heldOf = (id) => flagSet(id, "held");
const noGroundOf = (id) => flagSet(id, "noGround");

const TIGHT = S.TIGHT_SHOTS;

/** metres a SEATED card's whole figure is drawn below standing. toon.ts lowers `drop` by exactly this many design
 *  units, so every point the gate measures on that card - crown, eyes, torso, the occluding masses, the head width -
 *  has to come down by it too, or the gate polices a head the audience is never shown. */
const seatOf = (slot) => (slot && slot.seated !== undefined ? S.seatM(slot.seated, slot.scale) : 0);

const HW = { body: 175 * SU, props: 260 * SU };
// A card is measured 260 units wide only if toon.ts actually paints something out that far - a board under the
// feet, a cube overhead, a book fanned open. Everybody else is shoulders-and-arms at 175, and the checker must not
// slice a figure off the border for a prop it is not holding.
const reachFor = (id, n) => (heldOf(id).includes(n) ? HW.props : HW.body);
const headPts = (feet, scale, seat = 0) => [[feet[0], feet[1] + S.eyeY(scale) - seat, feet[2]], [feet[0], feet[1] + S.headY(scale) - seat, feet[2]]];
// vertical: the chest line (design y 375) or the hip line (design y 600) up to the crown. Feet are covered
// separately, at the shot's first frame.
const bodyPts = (feet, scale, w, tight, seat = 0) => {
  const e = w * scale, low = feet[1] + (975 - (tight ? 375 : 600)) * SU * scale - seat, top = feet[1] + S.headY(scale) - seat;
  return [
    [feet[0] - e, low, feet[2]], [feet[0] + e, low, feet[2]],
    [feet[0] - e, top, feet[2]], [feet[0] + e, top, feet[2]],
  ];
};
/** a flat plate in world space, in whichever axis it lies: "z" faces the lens, "x" is a flank wall, "y" a floor */
const quad = (c, hw2, hh2, axis = "z") => axis === "y"
  ? [[c[0] - hw2, c[1], c[2] - hh2], [c[0] + hw2, c[1], c[2] - hh2],
     [c[0] - hw2, c[1], c[2] + hh2], [c[0] + hw2, c[1], c[2] + hh2]]
  : axis === "x"
    ? [[c[0], c[1] - hh2, c[2] - hw2], [c[0], c[1] - hh2, c[2] + hw2],
       [c[0], c[1] + hh2, c[2] - hw2], [c[0], c[1] + hh2, c[2] + hw2]]
    : [[c[0] - hw2, c[1] - hh2, c[2]], [c[0] + hw2, c[1] - hh2, c[2]],
       [c[0] - hw2, c[1] + hh2, c[2]], [c[0] + hw2, c[1] + hh2, c[2]]];

// the opaque masses toon.ts actually paints, in design units [half-x, y-top, y-bottom]: head, torso+arms, legs
const BLOCKS = [[145, 90, 380], [175, 375, 600], [70, 600, 975]];
// `d` is story.seatDrop in DESIGN units: a seated skull and torso come down with the hip, but the shoes stay on the
// floor by construction (toon.ts pins the seated ankle at design 945 whatever the drop), so the legs block slides
// its top down and keeps its bottom at the pivot.
const cardRects = (feet, scale, d = 0) =>
  BLOCKS.map(([hx, yt, yb], i) => {
    const m = SU * scale, y = (k) => feet[1] + (975 - k) * m;
    const top = yt + d, bot = i === 2 ? 975 : yb + d;
    return [[feet[0] - hx * m, y(top), feet[2]], [feet[0] + hx * m, y(bot), feet[2]]];
  });

/** the head circle's own width, as a fraction of frame width. proj's u is already a frame-width percentage, so the
 *  span of the two silhouette edges is the number - no extra trig. Measured along the camera right axis, which is
 *  what a billboarded card's painted head projects to from any azimuth. */
const headWide = (c, feet, scale, seat = 0) => {
  const B = basis(c);
  const hd = 145 * SU * scale;
  const at = [feet[0], feet[1] + S.eyeY(scale) - seat, feet[2]];
  return Math.abs(proj(c, [at[0] + B.r[0] * hd, at[1], at[2] + B.r[2] * hd], B)[0] -
    proj(c, [at[0] - B.r[0] * hd, at[1], at[2] - B.r[2] * hd], B)[0]);
};

/** per-shot point sets: [name, kind, points] */
const pointsFor = (id, f, camPos) => {
  const o = [];
  for (const [n, feet, scale, primary, slot] of castFor(id, f)) {
    const seat = seatOf(slot);
    o.push([n, primary ? "HEAD*" : "HEAD", headPts(feet, scale, seat)]);
    o.push([n, primary ? "BODY*" : "BODY", bodyPts(feet, scale, reachFor(id, n), !!TIGHT[id], seat)]);
  }
  // shot 5's pinned king: it rests on its square until REACH_START_AT, then rides the fist
  if (id === 5) {
    const reach = S.glide(f, S.REACH_START_AT, S.KING_FALL_AT);
    const kp = f >= S.REACH_START_AT
      ? fistWorld(camPos, CH.hero, S.lerp(392, 511, reach), S.lerp(560, 478, reach))
      : CH.king;
    o.push(["king", "PROP", quad([kp[0], kp[1] + 0.17 - KING_DROP, kp[2]], 0.09, 0.17)]);
  }
  for (const q of S.PROP_QUADS[id] ?? []) {
    if (q.window && (f < q.window[0] || f > q.window[1])) continue;
    const slot = q.slot ? castFor(id, f).find((x) => x[0] === q.slot) : null;
    const c = q.hand && slot
      ? fistWorld(camPos, slot[1], q.hand[0], q.hand[1], slot[2])
      : q.live ? q.live(f) : q.c;
    o.push([q.n, q.kind === "COVER" ? "COVER" : q.kind === "BG" ? "BG" : "PROP", quad(c, q.hw, q.hh, q.axis)]);
  }
  for (const q of S.COVER_SHELLS[S.SHOTS[id - 1].set] ?? []) {
    o.push([q.n, "COVER", quad(q.c, q.hw, q.hh, q.axis)]);
  }
  return o;
};

const BAND = {
  "HEAD*": [15, 85], HEAD: [8, 92],
  "BODY*": [2, 98], BODY: [2, 98],
  PROP: [12, 88], BG: [0, 100],
  HEADW: [11, 68],
};

const fmt = (n) => (n <= -OFF ? "..L" : n >= OFF ? "R.." : n.toFixed(1));
const sfmt = (n, w) => (Math.abs(n) >= OFF ? fmt(n) : n.toFixed(1).padStart(w));

// ---------------------------------------------------------------- run
const step = +(process.argv.slice(2).find((r) => /^\d+$/.test(r)) ?? 5);
const agg = new Map();
const occl = new Map();
const lens = new Map();
const fovSeen = [99, 0];

const bump = (key) => {
  let a = agg.get(key);
  if (!a) agg.set(key, (a = { u0: OFF, u1: -OFF, v0: OFF, v1: -OFF }));
  return a;
};

for (let f = 0; f <= S.TOTAL - 1; f += step) {
  const s = S.shotAt(f);
  const c = S.camAt(s.id, f);
  fovSeen[0] = Math.min(fovSeen[0], c.fov);
  fovSeen[1] = Math.max(fovSeen[1], c.fov);

  for (const [name, kind, pts] of pointsFor(s.id, f, c.pos)) {
    const a = bump(`${s.id}|${kind}|${name}`);
    const B = basis(c);
    for (const p of pts) {
      const [u, v] = proj(c, p, B);
      if (u < a.u0) a.u0 = u; if (u > a.u1) a.u1 = u;
      if (v < a.v0) a.v0 = v; if (v > a.v1) a.v1 = v;
    }
  }
  // head width is a scalar per frame, so it borrows the u slots: u0 = narrowest, u1 = widest the lens ever sees
  for (const [n, feet, scale, , slot] of castFor(s.id, f)) {
    const a = bump(`${s.id}|HEADW|${n}`);
    const w = headWide(c, feet, scale, seatOf(slot));
    if (w < a.u0) a.u0 = w;
    if (w > a.u1) a.u1 = w;
  }

  // a 2D card is opaque, so a nearer body may never paint over a face the shot is answerable for
  const cast = castFor(s.id, f);
  for (const [n, feet, scale, , slot] of cast) {
    if (!requiredOf(s.id).includes(n)) continue;
    const seat = seatOf(slot);
    const face = rectOf(c, [[feet[0] - 0.30, feet[1] + S.headY(scale) - 0.30 - seat, feet[2]], [feet[0] + 0.30, feet[1] + S.eyeY(scale) - 0.20 - seat, feet[2]]]);
    if (face.z < 0.2 || !face.front) continue;
    // only the part of the face the audience can actually see counts as covered
    const vu0 = Math.max(face.u0, 0), vu1 = Math.min(face.u1, 100), vv0 = Math.max(face.v0, 0), vv1 = Math.min(face.v1, 100);
    const area = Math.max(1e-6, (vu1 - vu0) * (vv1 - vv0));
    if (area < 0.25 * Math.max(1e-6, (face.u1 - face.u0) * (face.v1 - face.v0))) continue;
    let worst = 0, by = "-";
    for (const [cn, cfeet, cscale, , cslot] of cast) {
      if (cn === n) continue;
      for (const blk of cardRects(cfeet, cscale, cslot?.seated !== undefined ? S.seatDrop(cslot.seated, cscale) : 0)) {
        const b = rectOf(c, blk);
        // an occluder has to be a well-defined plane in FRONT of the lens: a card whose own corners straddle the
        // lens plane is an edge-of-frame smear, not something that paints over a face at frame centre
        if (b.z >= face.z || !b.front) continue;
        const cov = Math.max(0, Math.min(vu1, b.u1) - Math.max(vu0, b.u0)) *
          Math.max(0, Math.min(vv1, b.v1) - Math.max(vv0, b.v0)) / area;
        if (cov > worst) { worst = cov; by = cn; }
      }
    }
    const key = `${s.id}|${n}`;
    const cur = occl.get(key);
    if (!cur || worst > cur.cov) occl.set(key, { cov: worst, by, f });
  }

  // the subject's circle of confusion must be zero from the shot's first frame, not racked in later
  const dof = S.dofAt(f);
  const sub = cast.find((x) => x[3]);
  const subj = sub[1];
  const B = basis(c);
  const zs = proj(c, [subj[0], subj[1] + 1.3 - seatOf(sub[4]), subj[2]], B)[2];
  const zf = proj(c, dof.focus(f), B)[2];
  const px = dof.cInf * Math.abs(1 - zf / zs);
  const cur = lens.get(`${s.id}`);
  if (!cur || px > cur.px) lens.set(`${s.id}`, { px, f });
}

// ---------------------------------------------------------------- report
const fails = [...fatal];
console.log(`=== InstantSkillShort framing, ${S.SHOTS.length} shots, f0..${S.TOTAL - 1} step ${step} | fov ${fovSeen[0].toFixed(1)}..${fovSeen[1].toFixed(1)} (inside 43..49) ===`);
let last = 0;
for (const [key, a] of [...agg].sort((x, y) => x[0].localeCompare(y[0], undefined, { numeric: true }))) {
  const [idS, kind, ...rest] = key.split("|");
  const id = +idS, name = rest.join("|");
  if (id !== last) {
    const s = S.SHOTS[id - 1];
    console.log(`\n-- shot ${id}: ${s.a}..${s.b} (${s.set}, ${s.light}${TIGHT[id] ? ", tight: hips-up framing)" : ", full figure)"}) --`);
    last = id;
  }
  const bad = [];
  const required = requiredOf(id).includes(name);
  const leaves = a.u0 <= -OFF || a.u1 >= OFF || a.v0 <= -OFF || a.v1 >= OFF;
  if (kind === "COVER") {
    // judged as a union in the cover section below: a room is closed by five plates, not by one that spans the frame
  } else if (kind === "BG") {
    // background dressing: a ridge or a hovering ship may legitimately run off any edge; reported only
  } else if (kind === "HEADW") {
    const [lo, hi] = BAND.HEADW;
    if (a.u0 < lo || a.u1 > hi) bad.push(`head width ${a.u0.toFixed(1)}..${a.u1.toFixed(1)}% of frame ! ${lo}..${hi}`);
  } else {
    const foreground = otsOf(id).includes(name) && kind.startsWith("BODY");
    const [lo, hi] = BAND[kind];
    if (!foreground) {
      if (leaves) bad.push(`leaves the frame at u ${sfmt(a.u0, 5)}..${sfmt(a.u1, 5)} v ${sfmt(a.v0, 5)}..${sfmt(a.v1, 5)}`);
      else {
        if (a.u0 < lo - 0.05 || a.u1 > hi + 0.05) bad.push(`u ${sfmt(a.u0, 7)}..${sfmt(a.u1, 7)} ! ${lo}..${hi}`);
        // a tight shot is authored chest-up, so the silhouette is MEANT to run off the bottom edge
        if (!(kind.startsWith("BODY") && TIGHT[id])) {
          if (a.v0 < lo - 0.05 || a.v1 > hi + 0.05) bad.push(`v ${sfmt(a.v0, 7)}..${sfmt(a.v1, 7)} ! ${lo}..${hi}`);
        }
      }
    }
    if (kind.startsWith("HEAD") && a.v0 < 22) bad.push(`crown v ${a.v0.toFixed(1)} enters the HUD pill band (needs >= 22)`);
  }
  if (bad.length && required) fails.push(`s${id} ${kind} ${name}: ${bad.join(", ")}`);
  console.log(
    `  ${kind.padEnd(7)} ${name.padEnd(12)} u ${sfmt(a.u0, 7)}..${sfmt(a.u1, 7)}` +
    `   v ${kind === "HEADW" ? "        -" + " " + "-     " : sfmt(a.v0, 7) + ".." + sfmt(a.v1, 7)}   ${bad.length ? (required ? "FAIL" : "note") : "ok"}`,
  );
}

console.log("\n=== cover: no unpainted hole may sit behind a figure the shot is answerable for ===");
// A room is closed by a floor, a ceiling, a back and two flanks. Testing each plate against the frame borders asked
// one wall to do five walls' job, so the law is aggregate now: the shot's COVER plates are unioned in screen space
// and sampled across the rect its REQUIRED cast occupies. A sample behind a body that lands inside no plate is a
// hole the audience would see straight through the set. Screen-space boxes are an approximation (a tilted plate
// projects to a quad, and its bounding box is slightly generous), and depth order is not tested - a plate in FRONT
// of the cast still counts as cover. The four outdoor sets are skipped outright: world.ts wraps every scene in a
// 900 m gradient dome, so above the ground plate there is never an unpainted void, and a finite ground quad can
// never project up to the horizon anyway. What fills the top of an outdoor frame is the skyline law's business.
for (const s of S.SHOTS) {
  const id = s.id;
  if (S.SKY_SETS.includes(s.set)) {
    console.log(`  shot ${id}: outdoor - the 900 m gradient dome is the backdrop, the skyline law answers for it`);
    continue;
  }
  const plates = [];
  for (const [k, a] of agg) {
    const [kid, kind] = k.split("|");
    if (+kid === id && kind === "COVER") plates.push(a);
  }
  if (!plates.length) continue;
  const band = { u0: 9e9, u1: -9e9, v0: 9e9, v1: -9e9 };
  for (const [k, a] of agg) {
    const [kid, kind, ...rest] = k.split("|");
    if (+kid !== id) continue;
    if (!(kind.startsWith("HEAD") || kind.startsWith("BODY"))) continue;
    if (!requiredOf(id).includes(rest.join("|"))) continue;
    band.u0 = Math.min(band.u0, a.u0); band.u1 = Math.max(band.u1, a.u1);
    band.v0 = Math.min(band.v0, a.v0); band.v1 = Math.max(band.v1, a.v1);
  }
  if (band.u1 < -9e8) continue;
  const bu0 = Math.max(0, band.u0), bu1 = Math.min(100, band.u1);
  const bv0 = Math.max(0, band.v0), bv1 = Math.min(100, band.v1);
  if (bu1 <= bu0 || bv1 <= bv0) continue;
  let holes = 0, at = "-";
  for (let i = 0; i < 13; i++) {
    for (let j = 0; j < 21; j++) {
      const u = bu0 + ((bu1 - bu0) * i) / 12, v = bv0 + ((bv1 - bv0) * j) / 20;
      if (plates.some((p) => u >= p.u0 && u <= p.u1 && v >= p.v0 && v <= p.v1)) continue;
      holes++;
      if (at === "-") at = `u ${u.toFixed(0)} v ${v.toFixed(0)}`;
    }
  }
  const n = 13 * 21;
  const bad = holes > 0;
  if (bad) fails.push(`s${id}: ${holes}/${n} samples behind the cast land on no plate (first at ${at}) - void in the set`);
  console.log(`  shot ${id}: cast band u ${bu0.toFixed(0)}..${bu1.toFixed(0)} v ${bv0.toFixed(0)}..${bv1.toFixed(0)}, ` +
    `${plates.length} plates, interior, ${holes}/${n} uncovered  ${bad ? "FAIL" : "ok"}`);
}

console.log("\n=== skyline: ranges fill the upper frame but still leave a sky strip at the top ===");
// A roofline counts when any sample ACROSS the block's width lands inside the frame horizontally: at fov 45 in 9:16
// the view wedge is only ~27 deg wide, so a 32 m ridge 30 m back is in shot even when its centre is off to one side.
// Its reported height is the sample nearest the frame centre, which is the silhouette the audience actually sees.
for (const idS of Object.keys(S.SKYLINES)) {
  const id = +idS, pol = S.SKYLINES[id];
  const s = S.SHOTS[id - 1], c = S.camAt(id, s.a);
  const B = basis(c);
  const tops = pol.blocks.map((b) => {
    const samples = [-0.42, -0.21, 0, 0.21, 0.42].map((k) => proj(c, [b.c[0] + b.w * k, b.c[1] + b.h / 2, b.c[2]], B));
    const inFrame = samples.filter((x) => x[0] >= 0 && x[0] <= 100);
    if (!inFrame.length) return null;
    return inFrame.reduce((best, x) => (Math.abs(x[0] - 50) < Math.abs(best[0] - 50) ? x : best))[1];
  }).filter((v) => v !== null);
  const vis = tops.filter((v) => v <= 96).length;
  const withSky = tops.filter((v) => v >= 12 && v <= 96).length;
  const cropped = tops.filter((v) => v < 12).length;
  const bad = [];
  if (vis < pol.minInside) bad.push(`only ${vis}/${pol.blocks.length} rooflines reach the frame (needs ${pol.minInside}) - the place is not in shot`);
  if (withSky < pol.minSky) bad.push(`only ${withSky}/${pol.blocks.length} roofs keep a sky strip above them (needs ${pol.minSky}) - the top of the frame is wall`);
  if (cropped > pol.maxCropped) bad.push(`${cropped} blocks run off the top edge (needs <= ${pol.maxCropped}) - the frame is a wall, not a skyline`);
  if (bad.length) fails.push(`s${id}: ${bad.join("; ")}`);
  console.log(`  shot ${id}: roof v ${tops.map((v) => v.toFixed(0).padStart(5)).join(" ")}  visible ${vis} sky ${withSky} cropped ${cropped} of ${pol.blocks.length}  ${bad.length ? "FAIL" : "ok"}`);
}

console.log("\n=== grounding at each shot's first frame (a full-figure shot must show the contact point) ===");
for (const s of S.SHOTS) {
  if (TIGHT[s.id]) { console.log(`  shot ${s.id}: tight by design, hips-up`); continue; }
  const c = S.camAt(s.id, s.a);
  const ng = noGroundOf(s.id), ots = otsOf(s.id);
  const rows = [];
  let bad = false;
  for (const [n, feet, , primary] of castFor(s.id, s.a)) {
    const v = proj(c, feet)[1];
    // a chest-up card, a foreground shoulder or an airborne/seated figure has no contact line to show
    const anchored = !TIGHT[s.id] && !ots.includes(n) && !ng.includes(n);
    const ok = !anchored || v <= 94;
    if (primary && anchored && !ok) bad = true;
    rows.push(`${n} v ${v.toFixed(1)}${ok ? "" : " (off bottom)"}${anchored ? "" : " (cropped by design)"}`);
  }
  if (bad) fails.push(`s${s.id}: the subject's feet leave the frame at the shot's first frame`);
  console.log(`  shot ${s.id}: ${rows.join(", ")}  ${bad ? "FAIL" : "ok"}`);
}

console.log("\n=== faces: worst fraction of a head painted over by a nearer card ===");
for (const [key, a] of [...occl].sort((x, y) => +x[0].split("|")[0] - +y[0].split("|")[0] || y[1].cov - x[1].cov)) {
  const [id, name] = key.split("|");
  const bad = a.cov > 0.05;
  if (bad) fails.push(`s${id} ${name}: ${(a.cov * 100).toFixed(0)}% of the face covered by ${a.by} @f${a.f}`);
  console.log(`  s${id} ${name.padEnd(12)} worst ${(a.cov * 100).toFixed(0).padStart(3)}% by ${a.by.padEnd(12)} @f${String(a.f).padStart(4)}  ${bad ? "FAIL" : "ok"}`);
}

console.log("\n=== lens: subject circle of confusion, px at 1080x1920 (0 = sharp) ===");
for (const [id, a] of [...lens].sort((x, y) => +x[0] - +y[0])) {
  const bad = a.px > 0.6;
  if (bad) fails.push(`s${id}: subject soft by ${a.px.toFixed(2)} px @f${a.f} - focus must sit on the subject from frame 0`);
  console.log(`  shot ${id}: worst ${a.px.toFixed(2)} px @f${a.f}  ${bad ? "FAIL" : "ok"}`);
}

console.log("\n=== camera angles around each shot's own subject (first frame) ===");
const prof = S.SHOTS.map((s) => {
  const sub = castFor(s.id, s.a).find((x) => x[3]);
  const feet = sub[1];
  return { id: s.id, ...S.camToSubject(s.id, s.a, [feet[0], feet[1] + 1.3 - seatOf(sub[4]), feet[2]]) };
});
for (const p of prof) {
  console.log(`  shot ${p.id}: az ${p.az.toFixed(1).padStart(6)}  d ${p.d.toFixed(2)} m  h ${p.h.toFixed(2)} m  pitch ${p.pitch.toFixed(1).padStart(5)}  fov ${p.fov.toFixed(1)}`);
}
let pairs = 0, same = 0;
for (let i = 0; i < prof.length; i++) {
  for (let j = i + 1; j < prof.length; j++) {
    const a = prof[i], b = prof[j];
    let daz = Math.abs(a.az - b.az); if (daz > 180) daz = 360 - daz;
    const ratio = Math.max(a.d, b.d) / Math.min(a.d, b.d);
    const dh = Math.abs(a.h - b.h), dp = Math.abs(a.pitch - b.pitch);
    pairs++;
    if (daz >= 25 || ratio >= 1.4 || dh >= 0.45 || dp >= 8) continue;
    same++;
    fails.push(`shots ${a.id}/${b.id} look the same: daz ${daz.toFixed(1)}, d ratio ${ratio.toFixed(2)}, dh ${dh.toFixed(2)} m, dpitch ${dp.toFixed(1)}`);
    console.log(`  SAME ${a.id}/${b.id}: daz ${daz.toFixed(1)}  ratio ${ratio.toFixed(2)}  dh ${dh.toFixed(2)}  dp ${dp.toFixed(1)}`);
  }
}
console.log(`  ${pairs - same}/${pairs} shot pairs are separated by at least one camera number`);

console.log("\n=== depth staging: the hero separated from EVERY opponent along the view axis, not side by side ===");
for (const [name, trio] of [["chess", [CH.hero, CH.friend, CH.gm]], ["poker", [PK.hero, PK.oppL, PK.oppR]]]) {
  const [hero, ...rest] = trio;
  // both hall and crane cameras sit at large +z, so depth along the view axis is a difference in z
  const gaps = rest.map((p) => Math.abs(p[2] - hero[2]));
  const ok = gaps.every((g) => g >= 1.19);
  if (!ok) fails.push(`${name}: the hero is only ${Math.min(...gaps).toFixed(2)} m along the view axis from an opponent (needs 1.2)`);
  console.log(`  ${name}: hero z ${hero[2].toFixed(2)}, opponents ${gaps.map((g) => g.toFixed(2)).join(" / ")} m  ${ok ? "ok" : "FAIL"}`);
}

console.log(`\n${fails.length ? `${fails.length} FRAMING FAILURES` : `SUCCESS: ${S.SHOTS.length} shots - angles all distinct, faces clear, subjects sharp from frame 0, nothing off-frame`}`);
for (const x of fails) console.log("  " + x);
process.exit(fails.length ? 1 : 0);
