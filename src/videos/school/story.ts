// Timeline of "School Hero" — 122.0 s (3660 f @ 30 fps), ten beats through one lockdown day.
// Four deep zones: the 14x24x5 m classroom (five rows of desks, four fans, tall windows onto the 40 m
// courtyard), the 45 m locker hallway (neon floor line, hologram, stairs), the 26 m chemistry lab
// (marble benches, vent duct) and the 80 m plaza (facade, steps, police cars, news vans).
// Every micro-cut is a real camera move (tilt, whip-pan, truck, dolly, crane, orbit) 20-45 degrees off the
// set axis; DOF keeps the midground characters sharp while the foreground and deep background fall off.
export const FPS = 30;
export const TOTAL = 3660;
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const seg = (a: number, b: number, x: number) => clamp01((x - a) / (b - a));

// ---------------- micro-cut frames ----------------
export const DOWN_AT = 70;         // beat 1: tilt down from the fan to the bored hero
export const PAN_AT = 120;         // beat 1: whip-pan to the window, classmates dive
export const STAND_AT = 245;       // beat 1: dolly-in + orbit, aura + eye fire
export const SIGNAL_AT = 375;      // beat 2: rack focus, two-finger signal
export const WALK_AT = 470;        // beat 2: lateral tracking walk
export const LIFT_AT = 570;        // beat 2: Dutch push-in, chair lift, doorknob
export const DOOR_AT = 660;        // beat 3: door kicks open
export const DUCK_AT = 665;        // beat 3: both friends drop low as the doorway fills
export const BLIND_AT = 700;       // beat 3: HUD blind spot
export const RUN_AT = 700;         // beat 3: friend 1 breaks from the group
export const DROP_AT = 745;        // beat 3: he goes to ground into the ankles
export const SLIDE_AT = 765;       // beat 3: floor-level slide into the ankles
export const FLIP_AT = 800;        // beat 3: the sweep tips the terrorist up
export const LAND_AT = 845;        // beat 3: he is on the floor, counted out
export const SLAM_AT = 885;        // beat 3: leap and chair slam
export const LOOT_AT = 1005;       // beat 4: gear pickup
export const SHADES_AT = 1110;     // beat 4: sunglasses drop
export const STRUT_AT = 1225;      // beat 4: backward dolly strut
export const WALKIE_AT = 1335;     // beat 5: walkie close-up
export const HOLO_AT = 1455;       // beat 5: dive into the hologram
export const STAIRS_AT = 1590;     // beat 5: stairs sprint, HERO METER
export const VENT_AT = 1725;       // beat 6: crane drop from the vent
export const FROST_AT = 1835;      // beat 6: CO2 cone
export const CREW_AT = 1950;       // beat 6: friends punch the frozen goons
export const VAULT_AT = 2055;      // beat 7: lab table slide
export const ORBIT2_AT = 2155;     // beat 7: bullet-time orbit kick
export const SLAM2_AT = 2260;      // beat 7: wall slam K.O.
export const LINE_AT = 2355;       // beat 8: collar brush hero line
export const CRUSH_AT = 2490;      // beat 8: crush blush
export const TEARS_AT = 2615;      // beat 8: waterfall tears, double thumbs-up
export const EXIT_AT = 2760;       // beat 9: courtyard doors burst
export const SALUTE_AT = 2885;     // beat 9: police/news/SWAT/principal salute
export const POSE_AT = 3010;       // beat 9: orbit toss + squad pose
export const HUG_AT = 3135;        // beat 10: crush hug
export const CHALK_AT = 3300;      // beat 10: FPV chalk projectile
export const THWACK_AT = 3360;     // beat 10: chalk hits, snap to classroom
export const BUMP_AT = 3490;       // beat 10: rub bump, grin
export const FAN_AT = 3560;        // beat 10: crane up to the fan, match frame 0

export type Light = "classroom" | "alert" | "lockdown" | "hall" | "lab" | "plaza";
export type SetName = "classroom" | "hall" | "lab" | "court";
export type ShotDef = { id: number; a: number; b: number; light: Light; set: SetName };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 375, light: "classroom", set: "classroom" },
  { id: 2, a: 375, b: 660, light: "alert", set: "classroom" },
  { id: 3, a: 660, b: 1005, light: "alert", set: "classroom" },
  { id: 4, a: 1005, b: 1335, light: "hall", set: "hall" },
  { id: 5, a: 1335, b: 1725, light: "hall", set: "hall" },
  { id: 6, a: 1725, b: 2055, light: "lab", set: "lab" },
  { id: 7, a: 2055, b: 2355, light: "lab", set: "lab" },
  { id: 8, a: 2355, b: 2760, light: "hall", set: "hall" },
  { id: 9, a: 2760, b: 3135, light: "plaza", set: "court" },
  { id: 10, a: 3135, b: 3360, light: "plaza", set: "court" },
  { id: 11, a: 3360, b: TOTAL, light: "classroom", set: "classroom" },
];
/** hard cuts inside the same set: no crossfade layers at all */
export const XFADE: Record<number, number> = {};

export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => [{ id: shotAt(f).id, alpha: 1 }];

/** display grade per light (grade.ts presets) */
export const GRADE_OF: Record<Light, string> = { classroom: "day", alert: "day", lockdown: "alarm", hall: "night", lab: "clinic", plaza: "day" };

// ---------------- zone landmarks (shared by build.ts, cast.ts and world.ts) ----------------
export const CLASS = {
  heroDesk: [-1.0, 0, 8.2] as V3,
  hero: [-0.7, 0, 6.1] as V3,
  muscle: [1.0, 0, 6.5] as V3,
  hoodie: [2.3, 0, 6.9] as V3,
  crush: [-3.3, 0, 7.6] as V3,
  teacher: [-2.2, 0, 20.8] as V3,
  door: [6.85, 0, 3.4] as V3,
  thugA: [4.5, 0, 4.1] as V3,
  thugB: [5.6, 0, 4.7] as V3,
  smash: [3.3, 0, 4.0] as V3,
  chair: [2.0, 0, 3.4] as V3,
  fan: [0, 4.35, 6.0] as V3,
};
export const HALL = {
  hero: [0.3, 0, 4.6] as V3,
  muscle: [1.3, 0, 5.0] as V3,
  hoodie: [2.3, 0, 5.4] as V3,
  crush: [1.1, 0, 12.6] as V3,
  downed: [1.7, 0, 2.2] as V3,
  holo: [-1.8, 0, 18.0] as V3,
  holoBase: [-1.8, 0, 18.0] as V3,
  stairs: [0, 0, 33.0] as V3,
  line: [0.3, 0, 12.0] as V3,
};
export const LAB = {
  vent: [0.2, 5.1, 7.6] as V3,
  hero: [0.0, 0, 8.0] as V3,
  goonA: [1.7, 0, 9.8] as V3,
  goonB: [2.9, 0, 10.5] as V3,
  friends: [-1.6, 0, 9.0] as V3,
  kick: [1.6, 0, 10.4] as V3,
  wall: [6.2, 0, 11.0] as V3,
};
export const COURT = {
  doors: [0, 0, 21.4] as V3,
  hero: [0, 0, 16.6] as V3,
  squad: [0, 0, 14.6] as V3,
  crush: [0.9, 0, 11.6] as V3,
  police: [-3.8, 0, 12.8] as V3,
  swat: [-2.0, 0, 13.4] as V3,
  news: [2.4, 0, 12.9] as V3,
  principal: [4.2, 0, 13.5] as V3,
  carA: [-8.5, 0, 10.0] as V3,
  carB: [8.6, 0, 11.4] as V3,
  vanA: [-13.0, 0, 9.4] as V3,
  vanB: [13.6, 0, 10.2] as V3,
};

// ---------------- camera ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Shot = Partial<Cam> & { pos: V3; look: V3 };
type Key = { f: number; dur?: number; cut?: boolean; raw?: boolean; s: (f: number) => Shot };
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
    cur = k.cut || k.raw ? full(k.s(f)) : mix(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
  }
  return cur;
};
const pushK = (f: number, f0: number, rate: number, punch = 0, n = 35) => {
  const x = Math.max(0, f - f0);
  let s = rate * x;
  if (punch > rate) for (let i = 0; i < Math.min(x, n); i++) s += (punch - rate) * Math.max(0, Math.min(1, (i + 0.5) / 8, (n - i - 0.5) / 8));
  return Math.exp(-s);
};
const dolly = (pos: V3, look: V3, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k], look, ...rest });
/** camera on an arc around (cx, cz): a0 -> a1 degrees, radius r, eye rises y0 -> y1 */
const orbit = (cx: number, cz: number, r: number, a0: number, a1: number, f0: number, f1: number, y0: number, y1: number, ly: number, fov = 42, roll = 0) => (f: number) => {
  const u = clamp01((f - f0) / (f1 - f0)), a = ((a0 + (a1 - a0) * u) * Math.PI) / 180;
  return { pos: [cx + Math.cos(a) * r, y0 + (y1 - y0) * u, cz + Math.sin(a) * r] as V3, look: [cx, ly, cz] as V3, fov, roll };
};
const still = (pos: V3, look: V3, fov = 42, roll = 0) => () => ({ pos, look, fov, roll });
const push = (pos: V3, look: V3, f0: number, rate: number, fov = 42, roll = 0, punch = 0) => (f: number) =>
  dolly(pos, look, pushK(f, f0, rate, punch), { fov, roll });

// -------- Act 1: locked-down setups. One view per 5-8 s, 20-30 deg off the set axis, a single slow 8% --------
// -------- push-in (pushK rate 0.00022-0.0003/frame) and no orbits or whip-pans: the characters move, --------
// -------- the camera does not. Beats 2-3 share one diagonal line so the trio stays depth-staggered in frame. --------
const CAMS: Record<number, Key[]> = {
  // beat 1: wide classroom (fans + windows + desk rows) -> settle on the seated hero -> he stands.
  // look x is pulled to -1.4 so the left-wall windows (x -6.9) fall inside the frame; the hero's desk sits at
  // (-1.5, 7.7), which is the axis the shot keeps re-centring on.
  1: [
    { f: 0, s: push([3.4, 1.95, 0.9], [-1.40, 1.20, 8.60], 0, 0.00016, 44) },
    { f: PAN_AT, dur: 50, s: push([2.3, 1.66, 2.4], [-1.45, 1.15, 8.20], PAN_AT, 0.00026, 42) },
    { f: STAND_AT, dur: 55, s: push([1.1, 1.56, 3.6], [-1.30, 1.30, 7.70], STAND_AT, 0.0003, 40) },
  ],
  // beat 2: one static setup in the aisle behind row 1 (x -1.05, z 7.25 is clear floor between the -1.5 and 1.4
  // columns; the row-2 desks at z 7.39+ stay behind the lens). fov 60 aimed 0.6 m left of the door puts the breach
  // on the right third and leaves room for three upright heads inside u 20-80. The lens sits 2.1 m high so the
  // blurred row-1 desk plank crosses only their shins, never a face.
  2: [
    { f: SIGNAL_AT, s: push([-1.05, 2.10, 7.25], [5.22, 1.15, 2.62], SIGNAL_AT, 0.00026, 60) },
  ],
  // beat 3: the SAME setup, re-armed at the cut, so f660 is seamless (no orbit, no whip, one doorway framing for
  // the breach, the slide, the flip, the chair slam and the K.O.). pos is exactly where beat 2's push has arrived
  // at f660 (look + (pos-look)*exp(-0.00026*285)); re-arming from the un-pushed pos would snap the lens back out.
  3: [
    { f: DOOR_AT, s: push([-0.61, 2.03, 6.91], [5.22, 1.15, 2.62], DOOR_AT, 0.00020, 60) },
  ],
  4: [
    { f: LOOT_AT, s: still([2.6, 1.55, -1.0], [0.4, 1.05, 4.0], 46) },
    { f: 1060, dur: 42, s: still([1.6, 1.3, 0.2], [0.7, 0.9, 2.8], 42) },
    { f: SHADES_AT, dur: 46, s: still([1.2, 1.42, 1.2], [0.5, 1.38, 3.4], 39, 0.02) },
    { f: STRUT_AT, dur: 50, s: still([1.6, 1.42, 9.6], [0.2, 1.2, 5.4], 43, -0.02) },
    { f: 1335, dur: 105, s: still([1.9, 1.5, 15.4], [0.2, 1.2, 8.0], 41) },
  ],
  5: [
    { f: WALKIE_AT, s: still([1.9, 1.35, 3.4], [0.4, 1.4, 6.4], 36) },
    { f: 1400, dur: 40, s: still([1.1, 1.3, 5.6], [0.2, 1.35, 8.4], 38) },
    { f: HOLO_AT, dur: 46, s: still([0.2, 1.2, 9.4], [-1.6, 2.0, 18.2], 48) },
    { f: 1550, dur: 22, s: still([0.6, 1.18, 13.2], [-1.7, 1.95, 18.2], 46, -0.01) },
    { f: STAIRS_AT, dur: 55, s: still([2.8, 1.35, 26.2], [0.1, 2.35, 32.2], 46, -0.03) },
    { f: 1700, dur: 30, s: still([2.4, 1.6, 27.5], [0.0, 2.5, 32.8], 44, -0.02) },
  ],
  6: [
    { f: VENT_AT, s: still([2.9, 3.5, 2.4], [0.0, 3.3, 7.3], 44) },
    { f: 1790, dur: 42, s: still([-1.2, 1.52, 3.2], [1.35, 1.12, 9.3], 46) },
    { f: FROST_AT, dur: 38, s: still([-0.9, 1.46, 3.8], [1.5, 1.05, 9.6], 44, 0.02) },
    { f: CREW_AT, dur: 42, s: still([0.6, 1.6, 2.6], [0.0, 1.0, 9.0], 50) },
    { f: 2020, dur: 35, s: still([0.4, 1.5, 3.4], [1.0, 1.0, 9.8], 46) },
  ],
  7: [
    { f: VAULT_AT, s: still([-3.0, 0.8, 5.6], [0.9, 0.95, 10.0], 50, 0.03) },
    { f: 2100, dur: 55, s: still([-1.4, 0.95, 6.3], [1.1, 1.0, 10.2], 48, 0.02) },
    { f: ORBIT2_AT, raw: true, s: orbit(1.9, 10.5, 5.3, -128, 52, ORBIT2_AT, SLAM2_AT, 0.95, 1.5, 1.2, 44, 0.02) },
    { f: SLAM2_AT, dur: 1, cut: true, s: still([1.6, 1.35, 6.6], [4.9, 1.15, 10.75], 42, 0.05) },
    { f: 2310, dur: 45, s: still([2.3, 1.3, 7.3], [4.9, 1.1, 10.7], 40, 0.02) },
  ],
  8: [
    { f: LINE_AT, s: still([3.5, 1.52, 8.9], [0.7, 1.33, 12.3], 48) },
    { f: CRUSH_AT, dur: 55, s: still([3.1, 1.48, 9.4], [0.75, 1.33, 12.4], 46, 0.01) },
    { f: TEARS_AT, dur: 50, s: still([2.8, 1.44, 9.8], [0.8, 1.3, 12.45], 44) },
    { f: 2720, dur: 40, s: still([2.7, 1.42, 9.9], [0.85, 1.28, 12.5], 44) },
  ],
  9: [
    { f: EXIT_AT, s: still([7.6, 1.7, 2.1], [0.2, 1.55, 16.0], 50) },
    { f: 2820, dur: 45, s: still([5.0, 1.62, 3.0], [0.0, 1.5, 15.0], 48) },
    { f: SALUTE_AT, dur: 55, s: still([0.6, 1.58, 9.8], [-3.8, 1.38, 12.8], 40, -0.01) },
    { f: 2940, dur: 55, s: still([0.7, 1.58, 9.8], [4.2, 1.4, 13.5], 40, 0.01) },
    { f: POSE_AT, cut: true, raw: true, s: orbit(0.4, 15.5, 8.2, -140, -75, POSE_AT, 3135, 1.75, 1.38, 1.35, 44, 0.02) },
  ],
  10: [
    { f: HUG_AT, s: still([3.0, 1.5, 6.2], [0.1, 1.32, 10.7], 40) },
    { f: 3220, dur: 55, s: still([2.2, 1.46, 7.1], [0.1, 1.34, 10.7], 39, 0.01) },
    { f: CHALK_AT, dur: 1, s: still([1.5, 1.5, 7.9], [0.0, 1.55, 10.9], 46) },
    { f: 3320, dur: 38, raw: true, s: (f) => {
      const u = clamp01((f - 3320) / 40);
      return { pos: [1.5 - 1.25 * u, 1.5 + 0.06 * u, 7.9 + 3.1 * u] as V3, look: [0, 1.55, 10.9] as V3, fov: 46 + 34 * u, roll: 0.35 * u * u };
    } },
  ],
  11: [
    { f: THWACK_AT, s: still([2.2, 1.55, 2.4], [-0.7, 1.4, 6.6], 44) },
    { f: 3420, dur: 30, s: still([1.5, 1.4, 3.2], [-0.8, 1.3, 6.6], 41, 0.02) },
    { f: BUMP_AT, dur: 45, s: still([1.5, 1.35, 3.9], [-0.7, 1.32, 6.6], 39, 0.01) },
    { f: FAN_AT, dur: 60, s: still([2.0, 1.8, 4.2], [-0.2, 1.45, 6.6], 42, 0) },
    { f: 3625, dur: 35, s: still([3.2, 3.3, -0.6], [0, 4.05, 6.4], 46, 0) },
  ],
};

const KICKS: [number, number][] = [[DOOR_AT, 0.5], [SLAM_AT + 18, 0.8], [FROST_AT, 0.5], [SLAM2_AT + 20, 0.9], [THWACK_AT, 1.4]];
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
export const keyEnd = (id: number, f: number) => {
  let e = 0;
  for (const k of CAMS[id]) if (f >= k.f) e = k.f + (k.cut || k.raw ? 0 : k.dur ?? 24);
  return Math.max(f, e);
};

// ---------------- lens ----------------
export type Dof = { f: number; dur?: number; cInf: number; focus?: (f: number) => V3 };
// Act 1 lens: no off-axis focus points - the thin lens sits on the camera's look target (always dead centre),
// so the frame can never go uniformly soft. cInf is kept mid-band: desks and windows melt, characters stay crisp.
export const DOF: Dof[] = [
  { f: 0, cInf: 30 },
  { f: DOWN_AT, cInf: 28 },
  { f: PAN_AT, cInf: 26 },
  { f: STAND_AT, cInf: 26 },
  { f: 375, cInf: 26 },
  { f: SIGNAL_AT, cInf: 26 },
  { f: WALK_AT, cInf: 25 },
  { f: LIFT_AT, cInf: 24 },
  { f: DOOR_AT, cInf: 26 },
  { f: SLIDE_AT, cInf: 25 },
  { f: SLAM_AT, cInf: 25 },
  { f: LOOT_AT, cInf: 18, focus: () => [0.6, 1.1, 3.0] },
  { f: SHADES_AT, cInf: 18, focus: () => [0.4, 1.4, 4.5] },
  { f: STRUT_AT, cInf: 21, focus: () => [0.4, 1.2, 6.0] },
  { f: WALKIE_AT, cInf: 17, focus: () => [0.3, 1.4, 4.7] },
  { f: HOLO_AT, cInf: 24, focus: () => [-1.6, 1.9, 18.0] },
  { f: STAIRS_AT, cInf: 26, focus: () => [0.1, 1.9, 31.6] },
  { f: VENT_AT, cInf: 24, focus: (f) => [0.0, 1.0 + 2.0 * (1 - clamp01((f - VENT_AT) / 100)), 8.1] },
  { f: FROST_AT, cInf: 20, focus: () => [0.5, 1.1, 8.8] },
  { f: CREW_AT, cInf: 18, focus: () => [0.4, 1.05, 9.1] },
  { f: VAULT_AT, cInf: 12, focus: () => [0.0, 0.95, 9.8] },
  { f: ORBIT2_AT, cInf: 17, focus: () => [1.7, 1.2, 10.4] },
  { f: SLAM2_AT, cInf: 18, focus: () => [4.8, 1.2, 10.8] },
  { f: LINE_AT, cInf: 16, focus: () => [0.7, 1.33, 12.3] },
  { f: CRUSH_AT, cInf: 14, focus: () => [0.75, 1.33, 12.4] },
  { f: TEARS_AT, cInf: 15, focus: () => [0.8, 1.3, 12.45] },
  { f: EXIT_AT, cInf: 24, focus: () => [0.0, 1.4, 14.5] },
  { f: SALUTE_AT, cInf: 20 },
  { f: 2940, cInf: 20 },
  { f: POSE_AT, cInf: 22, focus: () => [0.4, 1.3, 15.5] },
  { f: HUG_AT, cInf: 16, focus: () => [0.2, 1.35, 10.7] },
  { f: CHALK_AT, cInf: 14, focus: () => [0, 1.5, 10.9] },
  { f: THWACK_AT, cInf: 18, focus: () => [-0.7, 1.3, 6.6] },
  { f: BUMP_AT, cInf: 16, focus: () => [-0.7, 1.3, 6.6] },
  { f: FAN_AT, cInf: 22, focus: () => [0, 2.2, 6.4] },
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
