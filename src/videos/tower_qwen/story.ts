// Timeline of "Tower Qwen" — 10.0 s (300 f @ 30 fps), three shots, the 1952 Tower Bridge bus jump.
//   1 (0-94)    bridge: the road between the two Gothic towers splits open, a red double-decker keeps coming, the
//               watchman on his pier goes from whistling to panic; crane-out from his shoulder to a full wide.
//   2 (95-194)  cab: cutaway cab — "6 FT GAP AHEAD" on the windscreen header, the driver's fist on the 3D brass
//               throttle; panic snaps to a grin and the lever slams forward as the camera pushes in.
//   3 (195-299) jump: the bus arcs over the gap in the miniature far bridge above the plaza, lands, and the driver
//               holds up his £10 bonus certificate beside the "SAFE LANDING" chalkboard.
// Pure math: no THREE meshes here. Landmark coordinates live here so build.ts, cast.ts and world.ts agree.
export const FPS = 30;
export const TOTAL = 300;
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const seg = (a: number, b: number, x: number) => clamp01((x - a) / (b - a));
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export const lerp3 = (a: V3, b: V3, k: number): V3 => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
export const D2R = Math.PI / 180;

// ---------------- beats ----------------
export const TILT0 = 2;                 // deck angle (deg) at f <= OPEN_AT
export const TILT1 = 26;                // ... at f >= OPEN_END
export const OPEN_AT = 18;
export const OPEN_END = 75;
export const OPEN_KICK = 20;            // road cracks: kick + dust
export const PANIC_AT = 22;             // watchman calmWhistle -> panicShock
export const SHOT2_AT = 95;
export const DETERM_AT = 135;           // panicShock -> determinedGrin, leverP 0 -> 1 starts
export const LEVER_END = 152;
export const SPARK_AT = 145;            // throttle hits the stop: kick + sparks
export const SHOT3_AT = 195;
export const LAND_AT = 235;             // bus lands on the right leaf: kick + dust
export const BONUS_AT = 236;
export const BONUS_END = 268;
export const PUSH1_AT = 16, PUSH1_END = 75;
export const PUSH2_AT = 115, PUSH2_END = 165;
export const PUSH3_AT = 215, PUSH3_END = 268;

/** 0 (nearly flat) .. 1 (26 deg) */
export const openAt = (f: number) => glide((f - OPEN_AT) / (OPEN_END - OPEN_AT));
/** live bascule angle in degrees for a shot at frame f */
export const tiltDegAt = (f: number) => lerp(TILT0, TILT1, openAt(f));

export const leverAt = (f: number) => {
  if (f < DETERM_AT) return 0;
  if (f > LEVER_END) return 1;
  // wind-up is already done at DETERM_AT: fast throw, then a short settle on the stop
  return smooth((f - DETERM_AT) / (LEVER_END - DETERM_AT));
};
export const bonusAt = (f: number) => (f < BONUS_AT ? 0 : glide((f - BONUS_AT) / (BONUS_END - BONUS_AT)));

export type Light = "day" | "cab";
export type SetName = "bridge" | "cab" | "jump";
export type ShotDef = { id: number; a: number; b: number; light: Light; set: SetName };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: SHOT2_AT, light: "day", set: "bridge" },
  { id: 2, a: SHOT2_AT, b: SHOT3_AT, light: "cab", set: "cab" },
  { id: 3, a: SHOT3_AT, b: TOTAL, light: "day", set: "jump" },
];
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => [{ id: shotAt(f).id, alpha: 1 }];
export const GRADE_OF: Record<Light, string> = { day: "day", cab: "warm" };

// ---------------- landmarks ----------------
/** the live bridge assembly. Both copies (full size in shot 1, miniature backdrop in shot 3) share it. */
export const BRIDGE = {
  hinge: 6.4,          // m: towers / bascule pivots at x = +-hinge
  leafL: 6.4,          // m: each road leaf, tips meet at x = 0 when flat
  deckY: 1.7,          // m: road surface over the river
  roadW: 3.8,          // m: carriageway width (z from -1.9 to +1.9); the towers' legs stand on the pavements
  towerW: 1.8, towerD: 2.6, towerH: 11.8,
  legZ: 3.3,             // m: each tower's masonry leg is centred at z = +-legZ (the road runs through the portal)
  walkY0: 8.6, walkY1: 9.7,   // high-level walkway slab
  signY: 9.15, signZ: 1.5, signW: 4.8, signH: 1.0,   // "TOWER BRIDGE" on the walkway's river face
  barH: 0.5,           // red/white safety barrier height
  bus: { z: 0.0, len: 2.9, wide: 1.2, tall: 1.7 },
};
/** raised tip of a leaf (bridge-local), for a given tilt in degrees */
export const leafTip = (tiltDeg: number, side: 1 | -1): V3 => {
  const t = tiltDeg * D2R;
  return [side * (BRIDGE.hinge - BRIDGE.leafL * Math.cos(t)), BRIDGE.deckY + BRIDGE.leafL * Math.sin(t), 0];
};
/** a point s metres along a leaf from its hinge, on the road surface (bridge-local) */
export const onLeaf = (tiltDeg: number, side: 1 | -1, s: number): { p: V3; pitch: number } => {
  const t = tiltDeg * D2R;
  return { p: [side * (BRIDGE.hinge - s * Math.cos(t)), BRIDGE.deckY + s * Math.sin(t), 0], pitch: -side * t };
};

export const SET1 = {
  watchman: [1.9, 1.95, 5.5] as V3,    // stone pier balcony, river-side pavement just ahead of the near tower
};

export const CAB = {
  driver: [-0.05, 0, 0.3] as V3,
  sign: [-0.66, 1.84, -0.42] as V3,      // "6 FT GAP AHEAD" bolted to the windscreen header, clear of the cap
  signW: 0.38, signH: 0.27,
  winZ: -0.62, winY0: 1.12, winY1: 1.95, winHalfW: 1.12,
  boxTop: [-0.27, 0.52, 0.0] as V3,    // pivot of the 3D brass throttle lever
  bg: [-0.45, 0.5, -18] as V3, bgScale: 0.24,   // far bridge seen through the windscreen, centred on the cab's view axis
};

export const SET3 = {
  driver: [0.55, 0, 2.0] as V3,
  easel: [-0.62, 0, 1.55] as V3,
  boardW: 1.4, boardH: 0.98, boardY: 1.00,   // chalk face centre
  bg: [0, 0.15, -15.5] as V3, bgScale: 0.42,
  // bridge-local take-off / landing along-leaf distances (m from the hinge)
  takeS: 6.0, landS: 4.8, jumpRise: 1.6,
};

/** shot-1 bus: it drives the left leaf out from under the near tower up to the very lip of the raised tip */
export const BUS1 = { s0: 2.6, s1: 4.8 };
export const bus1At = (f: number) => {
  const o = onLeaf(tiltDegAt(f), -1, lerp(BUS1.s0, BUS1.s1, clamp01(f / 94)));
  return { p: [o.p[0], o.p[1], BRIDGE.bus.z] as V3, pitch: o.pitch };
};

/** the jumping bus of shot 3, in shot-3 background-bridge local coordinates */
export const jumpAt = (f: number) => {
  const u = clamp01((f - SHOT3_AT) / (LAND_AT - SHOT3_AT));
  const a = onLeaf(TILT1, -1, SET3.takeS), b = onLeaf(TILT1, 1, SET3.landS);
  const p: V3 = [lerp(a.p[0], b.p[0], u), lerp(a.p[1], b.p[1], u) + 4 * SET3.jumpRise * u * (1 - u), 0];
  // tangent of the parabola -> nose attitude; blended into the leaf angles at both ends so the bus sits flush on the
  // deck it leaves and the deck it lands on
  const dy = (b.p[1] - a.p[1]) + 4 * SET3.jumpRise * (1 - 2 * u), dx = b.p[0] - a.p[0];
  const raw = Math.atan2(dy, dx), t1 = TILT1 * D2R;
  const pitch = lerp(lerp(raw, t1, smooth((0.18 - u) / 0.18)), -t1, smooth((u - 0.78) / 0.22));
  return { p, pitch, u };
};

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
const still = (pos: V3, look: V3, fov = 46, roll = 0) => () => ({ pos, look, fov, roll });
/** pushK: after the move lands the lens keeps creeping toward the look point, so no frame is ever frozen */
const drift = (pos: V3, look: V3, f0: number, rate: number, fov = 46, roll = 0) => (f: number) => {
  const k = Math.exp(-rate * Math.max(0, f - f0));
  return { pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k] as V3, look, fov, roll };
};

const CAMS: Record<number, Key[]> = {
  // 1: medium over the watchman's right shoulder - he fills the right of the frame, the bus climbs the splitting
  //    road dead ahead of him - then a smooth crane-up and pull-back that lands with both towers, the walkway sign,
  //    both leaf tips, the bus and his pier all inside the vertical frame.
  1: [
    { f: 0, s: still([5.17, 3.4, 10.56], [-0.81, 3.45, 2.98], 46) },
    { f: PUSH1_AT, dur: PUSH1_END - PUSH1_AT, s: drift([0, 4.8, 45.5], [0, 4.6, 0], PUSH1_END, 0.0006, 50) },
  ],
  // 2: medium on sign + pedestal + driver, then a slow push into the determined grin and the lever.
  2: [
    { f: SHOT2_AT, s: still([-0.02, 1.14, 4.25], [-0.16, 1.02, 0.0], 46) },
    { f: PUSH2_AT, dur: PUSH2_END - PUSH2_AT, s: drift([-0.10, 1.30, 3.66], [-0.22, 1.10, 0.0], PUSH2_END, 0.0015, 44) },
  ],
  // 3: wide on the jump between the towers, then push in to the chalkboard / certificate medium two-shot.
  3: [
    { f: SHOT3_AT, s: drift([0.15, 1.4, 17.0], [0.1, 1.15, 5.0], SHOT3_AT, 0.006, 50) },
    { f: PUSH3_AT, dur: PUSH3_END - PUSH3_AT, s: drift([0.10, 1.66, 9.00], [-0.15, 1.45, -2.0], PUSH3_END, 0.0010, 48) },
  ],
};

/** 7-frame alternating decaying shake: road crack, throttle slam, landing */
export const KICKS: [number, number][] = [[OPEN_KICK, 0.9], [SPARK_AT, 1.25], [LAND_AT, 1.5]];
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
export type Dof = { cInf: number; focus: (f: number) => V3 };
export const dofAt = (f: number): Dof => {
  if (f < SHOT2_AT) {
    const k = glide((f - PUSH1_AT) / (PUSH1_END - PUSH1_AT));
    return { cInf: 9 + 9 * k, focus: () => lerp3(SET1.watchman, [0, 5.0, 0], k) };
  }
  if (f < SHOT3_AT) {
    const k = glide((f - PUSH2_AT) / (PUSH2_END - PUSH2_AT));
    return { cInf: 7.5 - 2.5 * k, focus: () => lerp3([CAB.driver[0], 1.2, CAB.driver[2]], [CAB.driver[0] - 0.15, 1.05, CAB.driver[2]], k) };
  }
  const k = glide((f - PUSH3_AT) / (PUSH3_END - PUSH3_AT));
  return { cInf: 11 - 4.5 * k, focus: () => lerp3([0, 2.6, SET3.bg[2]], [SET3.driver[0], 1.25, SET3.driver[2]], k) };
};

