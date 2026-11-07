// Timeline of "The Pardon" — a 20 s (600 f @ 30 fps) original short. Six shots over one continuous
// town-and-road location: the market square (shots 1-2, day), the road out of town (shot 3, day), the
// forest ambush (shots 4-5, golden hour) and the payoff on the road (shot 6, golden hour).
// Camera grammar is the same measured one as the bridge short: every move is a symmetric smootherstep glide
// of 18-40 f, holds push in at 0.15-0.35 %/f, reframes are cuts, impacts are 7-frame alternating kicks.
export const FPS = 30;
export const TOTAL = 600;
export const D0 = 0; // ground level
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };

// ---------------- the place ----------------
/** PARDONS booth: centre of the counter line; the priest stands 0.75 m behind it */
export const BOOTH: V3 = [0, 0, 3.0];
export const COUNTER_Z = 1.75;
export const COUNTER_Y = 1.02;
export const PRIEST = { x: 1.0, z: 2.5 };
/** cart rides the road at z = 1.6; the road runs along +x from the square (x 11) into the forest (x 130) */
export const CART_Z = 1.6;
/** cart speed: the wheels are rolled by distance / radius in world.ts, so any speed stays physically geared */
export const CART_V3 = 2.6; // m/s, shot 3
export const cartX = (id: number, f: number): number => {
  const t = f / FPS;
  switch (id) {
    case 3: return 17.5 + CART_V3 * (t - 6.5);             // 17.5 -> 26.6: the town slides past at 2.6 m/s
    case 4: return Math.min(63.3, 61.4 + 0.85 * (t - 10)); // ambush: rolls in and brakes as the knight steps out
    case 5: return 63.2;
    case 6: return 71.8;
    default: return 63.2;
  }
};

/** knight's march in shot 1: he enters frame right and walks all the way in to the centre of the counter, face
 *  turned toward the pardoner. The square camera sits west of the booth, so its screen-right is +x: he walks -x. */
export const KNIGHT1_Z = 0.95;
export const knightWalk = (f: number) => {
  const u = Math.min(f, 64) / 64;                        // arrives and stands at f64 (2.13 s)
  return { x: -2.15 + 2.1 * u, z: KNIGHT1_Z };
};
export const knightPhase = (f: number) => {
  const d = 2.1 * Math.min(f, 64) / 64;
  return (((d / 0.576) / 2) % 1 + 1) % 1;                // 0.576 m per step at ~0.85 m/s
};
/** the sack of gold lands on the counter 2 f after the knight stops (counter surface is y 1.04) */
export const SACK_AT = 66;
export const SACK_POS: V3 = [0.35, 1.33, 1.62];
/** ambush: the knight stalks the cart's front corner on the south verge, so he is always screen-RIGHT of the pardoner
 *  (who walks 1.9 m ahead of the cart) and never crosses the pardoner's x. His lead over the cart grows 0 -> 0.94 m
 *  over the shot: he starts beside the bed (hidden by the verge trees) and arrives at the cart's nose as it brakes.
 *  At t = 11.5 s he steps sideways into the road and strikes at t = 12.23 s, then holds still (the cart is stopped). */
export const STRIKE = 12.233;
export const KNIGHT4 = { z0: -0.3, z1: 0.55, lead0: 0, lead1: 0.94 };
export const stepOut = (t: number) => smooth((t - 11.5) / 0.33);
const ambushLead = (t: number) => KNIGHT4.lead0 + (KNIGHT4.lead1 - KNIGHT4.lead0) * clamp01((t - 10) / (STRIKE - 10));
export const knight4 = (t: number) => ({
  x: cartX(4, Math.round(t * FPS)) + ambushLead(t),
  z: KNIGHT4.z0 + (KNIGHT4.z1 - KNIGHT4.z0) * stepOut(t),
});
/** receipt: the pair stands south of the cart, knight screen-right of the priest */
export const PRIEST5 = { x: 62.8, z: 3.0 };
export const KNIGHT5 = { x: 63.55, z: 2.9 };
/** payoff: the knight marches up the middle of the road (z 1.5) for a full 7.2 m over f515-599, at 2.57 m/s so the
 *  stride cycle and the ground speed match; he recedes into the distance instead of treading by a fence post */
export const PAYOFF_X0 = 72.9;
export const PAYOFF_DX = 7.2;
export const knightPayoff = (f: number) => {
  const u = clamp01((f - 515) / FPS / 2.8);
  return { x: PAYOFF_X0 + PAYOFF_DX * u, z: 1.5 - 0.1 * u };
};
export const PRIEST6 = { x: 70.6, z: 4.95 };

// ---------------- shots ----------------
export type Light = "day" | "golden";
export type Crowd = "square" | "booth" | "road" | "ambush" | "receipt" | "payoff";
export type ShotDef = { id: number; a: number; b: number; light: Light; crowd: Crowd; tau: (t: number) => number };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 95, light: "day", crowd: "square", tau: (t) => t },
  { id: 2, a: 95, b: 195, light: "day", crowd: "booth", tau: (t) => t },
  { id: 3, a: 195, b: 300, light: "day", crowd: "road", tau: (t) => t },
  { id: 4, a: 300, b: 410, light: "golden", crowd: "ambush", tau: (t) => t },
  { id: 5, a: 410, b: 515, light: "golden", crowd: "receipt", tau: (t) => t },
  { id: 6, a: 515, b: TOTAL, light: "golden", crowd: "payoff", tau: (t) => t },
];
/** crossfades (frames) at place/time changes; the hook ends on a 4-frame white flash */
export const XFADE: Record<number, number> = { 2: 6, 3: 8, 4: 6, 5: 6, 6: 8 };
export const FLASH_AT = 92;

export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => {
  for (const s of SHOTS) {
    const x = XFADE[s.id];
    if (x && f >= s.a - x / 2 && f < s.a + x / 2) return [{ id: s.id - 1, alpha: 1 }, { id: s.id, alpha: (f - (s.a - x / 2) + 1) / (x + 1) }];
  }
  return [{ id: shotAt(f).id, alpha: 1 }];
};

// ---------------- camera ----------------
// Grammar (motion.md): symmetric smootherstep glides of 18-40 f, peak speed = 1.875 x distance / dur; a reframe
// bigger than ~half a frame width or 40 % zoom is a hard cut. Holds push in 0.15-0.35 %/f. Rolls 4-6 deg on
// emphasis beats only.
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Shot = Partial<Cam> & { pos: V3; look: V3 };
type Key = { f: number; dur?: number; cut?: boolean; s: (f: number) => Shot };
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
const mix = (a: Cam, b: Cam, k: number): Cam => ({
  pos: a.pos.map((v, i) => v + (b.pos[i] - v) * k) as V3, look: a.look.map((v, i) => v + (b.look[i] - v) * k) as V3,
  fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k,
});
const full = (c: Shot): Cam => ({ fov: 40, roll: 0, ...c });
const run = (keys: Key[], f: number) => {
  let cur = full(keys[0].s(f));
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? full(k.s(f)) : mix(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
  }
  return cur;
};
const T = (f: number) => f / FPS;
/** push-in factor since f0: the subject grows ~rate per frame; `punch` raises it (8 f soft edges) for n frames */
const pushK = (f: number, f0: number, rate: number, punch = 0, n = 35) => {
  const x = Math.max(0, f - f0);
  let s = rate * x;
  if (punch > rate) for (let i = 0; i < Math.min(x, n); i++) s += (punch - rate) * Math.max(0, Math.min(1, (i + 0.5) / 8, (n - i - 0.5) / 8));
  return Math.exp(-s);
};
const dolly = (pos: V3, look: V3, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k], look, ...rest });
const zoom = (pos: V3, look: V3, fov: number, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos, look, fov: (360 / Math.PI) * Math.atan(Math.tan((fov * Math.PI) / 360) * k), ...rest });
const rolled = (s: (f: number) => Shot, roll: number) => (f: number): Shot => ({ ...s(f), roll });

// shot 1: market square, wide 3/4 from the east -> medium two-shot as the sack lands
const S1a = (f: number) => dolly([5.0, 2.35, -5.2], [-0.5, 1.6, 2.35], pushK(f, 0, 0.0018), { fov: 42 });
// the end-of-push frame centres the gap BETWEEN the pair: at 44 deg both heads sit inside 60 % of the half-width
const S1b = (f: number) => dolly([3.9, 2.1, -3.7], [0.55, 1.52, 1.6], pushK(f, 50, 0.0016), { fov: 44, roll: -0.016 });
// shot 2: OTS-ish close on the priest and the scroll; the townsfolk behind go soft
const S2a = (f: number) => dolly([2.35, 1.72, -0.55], [1.02, 1.36, 2.5], pushK(f, 95, 0.0017), { fov: 38 });
const S2b = (f: number) => dolly([2.0, 1.68, 0.05], [1.02, 1.38, 2.5], pushK(f, 150, 0.0012), { fov: 35, roll: 0.015 });
// shot 3: the cart rolls toward the lens; the side-tracking camera keeps priest and cart apart and the town sliding past
// (the closer key used to crop the pardoner's boots, which is where the matched step cycle reads)
const S3a = (f: number) => { const cx = cartX(3, f); return dolly([cx + 5.6, 1.75, 4.2], [cx + 0.2, 1.35, 1.55], pushK(f, 195, 0.0012), { fov: 40, roll: 0.01 }); };
const S3b = (f: number) => { const cx = cartX(3, f); return dolly([cx + 5.1, 1.7, 4.1], [cx + 0.3, 1.35, 1.6], pushK(f, 252, 0.001), { fov: 39 }); };
// shot 4: the ambush from the open south verge. The camera stays nearly square to the road so the pardoner (ahead) and
// the knight (behind him) keep a clean gap; a 24-frame whip glide in, then a closer lens on the strike (+ kick)
// (aimed 0.27 m screen-right of the old look: at f300-310 the knight was still half off the right border as he
// stepped out from behind the cart, which read as a clipped head rather than an entrance)
const S4a = (f: number) => dolly([cartX(4, f) - 1.5, 1.95, -5.8], [63.58, 1.42, 0.9], pushK(f, 300, 0.0015), { fov: 46 });
// once the cart brakes, the look sits on the midpoint between the knight and the recoiling pardoner, so neither head
// rides the frame edge (the old look at 64.15 pushed the pardoner to 85 % of the half-width, half out of frame)
const S4b = (f: number) => dolly([cartX(4, f) - 0.4, 1.86, -5.9], [64.85, 1.38, 0.75], pushK(f, 340, 0.0012), { fov: 42, roll: -0.02 });
// shot 5: the receipt, close two-shot from the south side (priest left, knight right), full figures in frame
const S5a = (f: number) => dolly([63.15, 1.7, 6.7], [63.15, 1.18, 2.95], pushK(f, 410, 0.0014), { fov: 42 });
const S5b = (f: number) => dolly([63.15, 1.62, 6.1], [63.15, 1.2, 2.95], pushK(f, 462, 0.0011), { fov: 38, roll: 0.013 });
// shot 6: payoff wide down the golden road; cart centre-left, dazed priest right, knight receding
// (pulled back a step from the old framing: at f585 the seated priest was riding the 90 % safe-zone edge)
const S6a = (f: number) => dolly([63.4, 2.7, 6.4], [74.7, 1.15, 2.55], pushK(f, 515, 0.0012), { fov: 50 });
const S6b = (f: number) => dolly([64.0, 2.6, 6.3], [74.3, 1.12, 2.45], pushK(f, 562, 0.001), { fov: 48 });

const CAMS: Record<number, Key[]> = {
  1: [{ f: 0, s: S1a }, { f: 50, dur: 34, s: S1b }],
  2: [{ f: 95, s: S2a }, { f: 150, dur: 28, s: S2b }],
  3: [{ f: 195, s: S3a }, { f: 252, dur: 26, s: S3b }],
  4: [{ f: 300, s: S4a }, { f: 340, dur: 24, s: S4b }],
  5: [{ f: 410, s: S5a }, { f: 462, dur: 30, s: S5b }],
  6: [{ f: 515, s: S6a }, { f: 562, dur: 30, s: S6b }],
};

// impact kicks: the image offset flips sign every frame (~3 px at 720p per unit), decays to 0 in 7 f.
const KICKS: [number, number][] = [[STRIKE, 1.0]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor((t - t0) * FPS + 1e-6);
    if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5;
  }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  const c = run(CAMS[id], f), a = kickAt(T(f));
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1;
  const m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};
export const keyEnd = (id: number, f: number) => {
  let e = 0;
  for (const k of CAMS[id]) if (f >= k.f) e = k.f + (k.cut ? 0 : k.dur ?? 24);
  return Math.max(f, e);
};

// ---------------- lens (depth of field) ----------------
export type Dof = { f: number; dur?: number; cInf: number; focus?: (f: number) => V3 };
export const DOF: Dof[] = [
  { f: 0, cInf: 9, focus: () => [-1.3, 1.5, 1.0] },                      // knight marching in, town soft
  { f: 50, cInf: 12, focus: () => [0.2, 1.5, 1.5] },                     // two-shot at the counter
  { f: 95, cInf: 17, focus: () => [1.02, 1.4, 2.5] },                    // priest + scroll, folk bokeh
  { f: 195, cInf: 7, focus: (f) => [cartX(3, f) - 0.3, 1.5, 2.0] },      // cart + whistler
  { f: 300, cInf: 10, focus: (f) => { const k = knight4(f / FPS); return [k.x, 1.5, k.z + 0.4]; } }, // ambush knight
  { f: 410, cInf: 16, focus: () => [63.15, 1.5, 2.95] },                 // receipt two-shot
  { f: 515, cInf: 8, focus: () => [71.4, 1.2, 4.6] },                    // payoff: cart + dazed priest
];
export const dofAt = (f: number) => {
  let i = 0; while (i + 1 < DOF.length && f >= DOF[i + 1].f) i++;
  const d = DOF[i], p = DOF[Math.max(0, i - 1)];
  const k = d.dur ? Math.min(1, (f - d.f) / d.dur) : 1;
  return { cInf: p.cInf + (d.cInf - p.cInf) * k, focus: d.focus };
};
export const focusAt = (id: number, f: number): V3 => {
  const d = dofAt(f);
  return d.focus ? d.focus(f) : camAt(id, f).look;
};
