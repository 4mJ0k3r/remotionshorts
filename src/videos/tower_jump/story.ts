// Timeline of "Tower Jump" — 10.0 s (300 f @ 30 fps). The 1952 Tower Bridge incident: bus driver Albert Gunter was
// halfway across when the bascules began to rise, and he jumped the No. 78 double-decker across the gap.
//   1 (0-94)    SET_BRIDGE_WIDE: watchman on his balcony, the bus climbing the left leaf as both leaves tilt 2 -> 26
//                                deg; the camera cranes out to reveal both towers and the "TOWER BRIDGE" sign.
//   2 (95-194)  SET_CAB_DECK:    the driver in his cutaway cab, the "6 FT GAP AHEAD" sign; he slams the 3D brass
//                                throttle (his 2D fist is pinned to the lever knob, SKILL Rule B).
//   3 (195-299) SET_JUMP_FINISH: the bus arcs across the gap and lands on the lower leaf; push-in to the driver with
//                                his "£10 BONUS" next to the "SAFE LANDING" chalkboard.
// Pure data + pure functions only (no three.js objects), so scripts can import it for framing checks.
export const FPS = 30;
export const TOTAL = 300;
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
/** smootherstep of a 0..1 value */
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
/** smootherstep of frame f across [f0, f1] */
export const glideF = (f: number, f0: number, f1: number) => glide((f - f0) / (f1 - f0));
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const deg = (d: number) => (d * Math.PI) / 180;

// ---------------- beat markers ----------------
export const OPEN_AT = 18, OPEN_END = 75;    // shot 1: the leaves tilt 2 -> 26 deg
export const PANIC1_AT = 22;                 // watchman: calmWhistle -> panicShock
export const PULL_AT = 16, PULL_END = 75;    // shot 1 crane-out
export const SHOT2_AT = 95;
export const SLAM_AT = 135, SLAM_END = 152;  // throttle 0 -> 1
export const PUSH2_AT = 115, PUSH2_END = 165;
export const SHOT3_AT = 195;
export const JUMP_END = 235;                 // the bus lands
export const BONUS_AT = 236, BONUS_END = 256;
export const PUSH3_AT = 215, PUSH3_END = 268;

export type Light = "sunny";
export type SetName = "wide" | "cab" | "finish";
export type ShotDef = { id: number; a: number; b: number; light: Light; set: SetName };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 95, light: "sunny", set: "wide" },
  { id: 2, a: 95, b: 195, light: "sunny", set: "cab" },
  { id: 3, a: 195, b: TOTAL, light: "sunny", set: "finish" },
];
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => [{ id: shotAt(f).id, alpha: 1 }];
export const GRADE_OF: Record<Light, string> = { sunny: "vivid" };

// ---------------- bridge geometry (bridge-local metres; water surface = local y 0) ----------------
export const BR = { hingeX: 6.5, leafLen: 6.4, towerX: 8.5, towerW: 3.6, towerD: 6.4, roadHalf: 2.4, towerAbove: 15 };
/** a bridge instance: group position, uniform scale, deck (hinge) height in local units */
export type BridgeInst = { pos: V3; scale: number; deckY: number };
export const BR1: BridgeInst = { pos: [0, 0, 0], scale: 1, deckY: 2.8 };
/** shot 3: a higher, smaller bridge seen from the riverside plaza (water 1.5 m below the plaza) */
export const BR3: BridgeInst = { pos: [0, -1.5, -15], scale: 0.7, deckY: 9 };
export const toWorld = (b: BridgeInst, x: number, y: number, z = 0): V3 =>
  [b.pos[0] + b.scale * x, b.pos[1] + b.scale * y, b.pos[2] + b.scale * z];

/** shot 1 leaf tilt (rad): nearly flat, then both leaves rise to 26 deg */
export const tilt1At = (f: number) => deg(2 + 24 * glideF(f, OPEN_AT, OPEN_END));
export const TILT3_L = deg(26), TILT3_R = deg(12);
/** road surface point at distance s from a hinge (s < 0 = on the flat approach behind the hinge) */
export const leafPoint = (b: BridgeInst, side: -1 | 1, s: number, tilt: number): [number, number] => {
  // the left leaf (side -1) runs +x from its hinge, the right leaf (side +1) runs -x; behind a hinge the road is flat
  const hx = side * BR.hingeX;
  if (s <= 0) return [hx - side * s, b.deckY];
  return [hx - side * s * Math.cos(tilt), b.deckY + s * Math.sin(tilt)];
};

// ---------------- the bus ----------------
export const BUS = { len: 6.0, wheelbase: 4.0, height: 3.9, width: 2.3 };
export type BusPose = { x: number; y: number; pitch: number };
/** shot 1: the bus climbs the left leaf, rear wheels on the flat approach at first (bridge-local) */
export const busShot1 = (f: number): BusPose => {
  const u = clamp01(f / 94);
  const rear = -4.6 + 5.4 * (u - 0.12 * u * u) / 0.88, front = rear + BUS.wheelbase, t = tilt1At(f);
  const [rx, ry] = leafPoint(BR1, -1, rear, t), [fx, fy] = leafPoint(BR1, -1, front, t);
  return { x: (rx + fx) / 2, y: (ry + fy) / 2, pitch: Math.atan2(fy - ry, fx - rx) };
};
/** shot 3: launch off the left tip, parabolic arc, land on the lower right leaf, roll on (BR3-local) */
const LAUNCH_S = BR.leafLen - BUS.wheelbase / 2 - 0.1, LAND_S = 4.4;
export const busShot3 = (f: number): BusPose => {
  const [x0, y0] = leafPoint(BR3, -1, LAUNCH_S, TILT3_L);
  if (f <= JUMP_END) {
    const [x1, y1] = leafPoint(BR3, 1, LAND_S, TILT3_R);
    const u = clamp01((f - SHOT3_AT) / (JUMP_END - SHOT3_AT));
    return { x: lerp(x0, x1, u), y: lerp(y0, y1, u) + 2.0 * 4 * u * (1 - u), pitch: lerp(TILT3_L, -TILT3_R, smooth(u)) };
  }
  const k = clamp01((f - JUMP_END) / (TOTAL - 1 - JUMP_END)), s = LAND_S - 1.2 * (1 - (1 - k) ** 2);
  const [x, y] = leafPoint(BR3, 1, s, TILT3_R);
  const n = f - JUMP_END, bounce = 0.32 * Math.exp(-n / 6) * Math.abs(Math.sin(n * 0.55));
  return { x, y: y + bounce, pitch: -TILT3_R + 0.05 * Math.exp(-n / 6) * Math.sin(n * 0.55) };
};

// ---------------- characters / props (world metres, feet positions) ----------------
export const WATCH: V3 = [2.2, 2.5, 4.5];
export const DRV2: V3 = [0.45, 0, 2.1];
export const DRV3: V3 = [0.55, 0, 2.0];
export const PEDESTAL: V3 = [-0.15, 0, 2.0];
/** lever pivot on the pedestal's top right corner, under the driver's fist */
export const LEVER_PIVOT: V3 = [0.0, 0.5, 2.0];
export const GAPSIGN: V3 = [-0.4, 0, 0.2];   // hung from the windscreen header, board y 1.95..2.41
export const EASEL: V3 = [-0.95, 0, 1.9];
export const LAMP: V3 = [3.4, 0, 0.2];       // kept out of the bus's landing line of sight

// ---------------- camera ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Shot = Partial<Cam> & { pos: V3; look: V3 };
type Key = { f: number; dur?: number; cut?: boolean; s: (f: number) => Shot };
const mix = (a: Cam, b: Cam, k: number): Cam => ({
  pos: a.pos.map((v, i) => v + (b.pos[i] - v) * k) as V3, look: a.look.map((v, i) => v + (b.look[i] - v) * k) as V3,
  fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k,
});
const full = (c: Shot): Cam => ({ fov: 46, roll: 0, ...c });
const run = (keys: Key[], f: number) => {
  let cur = full(keys[0].s(f));
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? full(k.s(f)) : mix(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
  }
  return cur;
};
/** pushK micro-drift: the camera keeps creeping toward its look point after a move lands (never a dead frame) */
export const pushK = (f: number, f0: number, rate: number) => Math.exp(-rate * Math.max(0, f - f0));
const drift = (pos: V3, look: V3, f0: number, rate: number, fov: number) => (f: number) => {
  const k = pushK(f, f0, rate);
  return { pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k] as V3, look, fov, roll: 0 };
};

// every fov is inside 40..52 deg (SKILL rule 5): framing is fixed by distance, never by widening the lens
export const CAMS: Record<number, Key[]> = {
  1: [
    // the brief's [1.6,3.8,8.2] -> [-1,3.5,0] puts the watchman at u157% and the bus at u-97%: this diagonal from behind his right shoulder keeps him (u84) and the bus front (u27) in one frame
    { f: 0, s: drift([5.8, 4.0, 9.5], [-1.3, 4.0, 2.4], 0, 0.0016, 46) },
    // the towers sit at x +-8.5 (outer faces +-10.3): at fov 50 the frame is only 0.262*d wide each side, so the
    // reveal has to pull back to d 42 for both towers to fit (pulled back, not widened)
    { f: PULL_AT, dur: PULL_END - PULL_AT, s: drift([0.0, 7.0, 42.0], [0.0, 7.0, 0.0], PULL_END, 0.0012, 50) },
  ],
  2: [
    // pulled back from z 6.2 to 7.1 so the "6 FT GAP AHEAD" sign and the driver both fit at fov 46
    { f: SHOT2_AT, s: drift([-0.4, 1.55, 7.1], [0.0, 1.3, 2.0], SHOT2_AT, 0.0012, 46) },
    { f: PUSH2_AT, dur: PUSH2_END - PUSH2_AT, s: drift([0.2, 1.5, 5.9], [0.2, 1.25, 2.0], PUSH2_END, 0.0016, 44) },
  ],
  3: [
    { f: SHOT3_AT, s: drift([0.0, 3.0, 14.0], [0.0, 5.0, -6.0], SHOT3_AT, 0.0012, 50) },
    { f: PUSH3_AT, dur: PUSH3_END - PUSH3_AT, s: drift([-0.23, 1.7, 8.8], [-0.23, 1.9, 1.9], PUSH3_END, 0.0012, 48) },
  ],
};

/** 7-frame alternating decaying shake at each impact */
export const KICKS: [number, number][] = [[20, 0.9], [145, 1.1], [JUMP_END, 1.0]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor(t * FPS - t0 + 1e-6);
    if (n >= 0 && n < 7) a += g * (n % 2 ? -1 : 1) * (1 - n / 7) ** 1.5;
  }
  return a;
};
export const camAt = (id: number, f: number): Cam => {
  const c = run(CAMS[id], f), a = kickAt(f / FPS);
  if (!a) return c;
  const d: V3 = [c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]];
  const L = Math.hypot(...d), h = Math.hypot(d[0], d[2]) || 1;
  const m = (3 / 640) * Math.tan((c.fov * Math.PI) / 360) * L * a;
  return { ...c, look: [c.look[0] - (d[2] / h) * m, c.look[1] + 0.6 * m, c.look[2] + (d[0] / h) * m], roll: c.roll + a * 0.004 };
};

// ---------------- lens ----------------
export type Dof = { cInf: number; focus: V3 };
const lerp3 = (a: V3, b: V3, k: number): V3 => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
export const dofAt = (f: number): Dof => {
  if (f < SHOT2_AT) {
    const k = glideF(f, PULL_AT, PULL_END);
    return { cInf: 9 - 4 * k, focus: lerp3([1.0, 4.0, 3.0], [0, 5, 0], k) };
  }
  if (f < SHOT3_AT) return { cInf: 9, focus: [0.4, 1.2, 2.05] };
  const k = glideF(f, PUSH3_AT, PUSH3_END);
  return { cInf: 5 + 3 * k, focus: lerp3([0, 4, -12], [0.3, 1.2, 2.0], k) };
};
