// Timeline of "Coaster" — 10.0 s (300 f @ 30 fps), three shots in one sunny amusement-park build site.
//   1 (0-89)    SET_LOOP:  the builder's hammer slams at f14, the red loop kinks out of shape, the camera cranes
//                          down and pulls wide so the whole bent loop and the hills fill the vertical frame.
//   2 (90-194)  SET_DECK:  a red cart drops off the scaffolding behind the waving builder; he opens his wallet and
//                          it is empty. The camera tracks right and pushes in to a close-up.
//   3 (195-299) SET_RIVAL: a white copy of the loop hangs from a yellow crane, a Ferris wheel turns; push-in and
//                          tilt down to the rival smirking beside his "FRANK'S LOOP" blueprint.
// All three sets share one origin and are toggled per shot (world.ts); everything is a pure function of the frame.
export const FPS = 30;
export const TOTAL = 300;
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
export const seg = (a: number, b: number, x: number) => clamp01((x - a) / (b - a));
export const glide = (u: number) => { const x = clamp01(u); return x * x * x * (x * (6 * x - 15) + 10); };

// ---------------- beat markers ----------------
export const SLAM_AT = 14;          // hammer hits the platform (swingP = 0.5), kick + dust
export const BEND_DUR = 10;         // loop morphs circle -> kinked polygon over f14..24
export const PULL_AT = 12;          // shot 1 crane-down / pull-back starts
export const PULL_END = 75;
export const SHOT2_AT = 90;
export const CART_END = 155;        // cart reaches the bottom of the drop
export const PUSH2_AT = 118;     // v2: scaffold + drop f90-118, eased pan/push, close-up from f148
export const PUSH2_END = 148;
export const WALLET_AT = 136;       // wallet comes out
export const SAD_AT = 165;          // the wallet is empty: happyProud -> brokeSad
export const SHOT3_AT = 195;
export const PUSH3_AT = 205;
export const PUSH3_END = 255;     // v2: natural fov-50 medium shot holds f255-299

/** loop deformation 0 (circle) .. 1 (bent) */
export const bendAt = (f: number) => clamp01((f - SLAM_AT) / BEND_DUR);

export type Light = "sunny";
export type SetName = "loop" | "deck" | "rival";
export type ShotDef = { id: number; a: number; b: number; light: Light; set: SetName };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 90, light: "sunny", set: "loop" },
  { id: 2, a: 90, b: 195, light: "sunny", set: "deck" },
  { id: 3, a: 195, b: TOTAL, light: "sunny", set: "rival" },
];
export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => [{ id: shotAt(f).id, alpha: 1 }];
export const GRADE_OF: Record<Light, string> = { sunny: "vivid" };

// ---------------- landmarks (shared by build.ts, cast.ts and world.ts) ----------------
export const LOOP = {
  center: [0, 8.0, -4.0] as V3, R: 7.5,
  platformY: 3.2, builder: [0, 3.2, 2.5] as V3,
  /** steel rail laid along the platform's front, struck by the hammer at SLAM_AT */
  railY: 3.25, railZ: 2.62,
};
export const DECK = {
  deckY: 3.0, builder: [1.1, 3.0, 1.5] as V3,
  scaffold: [-2.2, 0, -1.5] as V3, scaffoldH: 5.6,
  bgLoop: [9.0, 6.5, -22.0] as V3, bgR: 5.5,
};
export const RIVAL = {
  // v2: pushed back from z -10 to -14 (R 6.5 -> 7) so the natural fov-50 medium shot still sees the open top + crane
  loop: [0, 8.5, -14] as V3, R: 7.0,
  // winch moved +0.1 x (v2.1) so its base's right end sits under the rival's lever fist
  // v2.1: the winch now sits just BEHIND the rival's card plane (z 2.0) with its right end turned toward him, so the
  // 2D arm + fist always draw over the gold side plates; the lever pivot is the right end of its base (y 0.26)
  easel: [-0.9, 0, 1.8] as V3, winch: [-0.07, 0, 1.76] as V3, winchYaw: -0.2, rival: [0.65, 0, 2.0] as V3,
  leverBase: [0.37, 0.3, 1.85] as V3,
  crane: [-8.5, 0, -18] as V3, craneH: 20,
  ferris: [9.0, 8.6, -26] as V3, ferrisR: 7,
};
/** how far the crane has the white arch segment above its seat (m) */
export const archLiftAt = (f: number) => 2.2 - 1.1 * smooth((f - SHOT3_AT) / (TOTAL - SHOT3_AT));

// ---------------- camera ----------------
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Shot = Partial<Cam> & { pos: V3; look: V3 };
type Key = { f: number; dur?: number; cut?: boolean; s: (f: number) => Shot };
const mix = (a: Cam, b: Cam, k: number): Cam => ({
  pos: a.pos.map((v, i) => v + (b.pos[i] - v) * k) as V3, look: a.look.map((v, i) => v + (b.look[i] - v) * k) as V3,
  fov: a.fov + (b.fov - a.fov) * k, roll: a.roll + (b.roll - a.roll) * k,
});
const full = (c: Shot): Cam => ({ fov: 45, roll: 0, ...c });
const run = (keys: Key[], f: number) => {
  let cur = full(keys[0].s(f));
  for (let i = 1; i < keys.length; i++) {
    const k = keys[i];
    if (f < k.f) break;
    cur = k.cut ? full(k.s(f)) : mix(cur, full(k.s(f)), glide((f - k.f) / (k.dur ?? 24)));
  }
  return cur;
};
const still = (pos: V3, look: V3, fov = 45, roll = 0) => () => ({ pos, look, fov, roll });
/** slow residual push toward the look point after a move has landed, so no shot ever holds a dead frame */
const drift = (pos: V3, look: V3, f0: number, rate: number, fov = 45, roll = 0) => (f: number) => {
  const k = Math.exp(-rate * Math.max(0, f - f0));
  return { pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k] as V3, look, fov, roll };
};

const CAMS: Record<number, Key[]> = {
  // shot 1: low-angle medium on the platform looking up at the swing, then crane down + pull back so the whole bent
  // loop and the hills fill the frame with the builder small at its base.
  1: [
    { f: 0, s: still([0.3, 4.1, 5.2], [0, 4.4, 2.5], 55) },
    { f: PULL_AT, dur: PULL_END - PULL_AT, s: drift([0, 2.2, 19.5], [0, 7.5, -4.0], PULL_END, 0.0012, 62) },
  ],
  // shot 2: medium-wide on the scaffolding + builder, then track right and push in to the wallet close-up
  2: [
    { f: SHOT2_AT, s: drift([-1.4, 4.6, 6.2], [-0.7, 4.9, -0.8], SHOT2_AT, 0.002, 50) },
    { f: PUSH2_AT, dur: PUSH2_END - PUSH2_AT, s: drift([1.1, 3.95, 4.15], [1.1, 3.82, 1.5], PUSH2_END, 0.0016, 48) },
  ],
  // shot 3: wide on the white loop, crane and Ferris wheel, then an eased push-in and tilt down to the medium shot
  3: [
    { f: SHOT3_AT, s: still([0.0, 2.6, 11.5], [0.0, 5.2, -4.0], 60) },
    { f: PUSH3_AT, dur: PUSH3_END - PUSH3_AT, s: drift([-0.15, 0.55, 7.6], [-0.15, 2.25, 2.0], PUSH3_END, 0.0012, 50) },
  ],
};

/** 7-frame alternating decaying shake at each impact */
export const KICKS: [number, number][] = [[SLAM_AT, 1.2]];
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
// focus follows the subject: the builder through the swing, the loop once the pull-back passes it, etc.
export type Dof = { cInf: number; focus: (f: number) => V3 };
const lerp3 = (a: V3, b: V3, k: number): V3 => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
export const dofAt = (f: number): Dof => {
  if (f < SHOT2_AT) {
    const k = glide((f - PULL_AT) / (PULL_END - PULL_AT));
    return { cInf: 12 - 5 * k, focus: () => lerp3([0, 4.3, 2.5], [0, 6.0, -1.0], k) };
  }
  if (f < SHOT3_AT) {
    // focus rides with the dropping cart / scaffold, then racks onto the builder as the camera pushes in
    const k2 = glide((f - PUSH2_AT) / (PUSH2_END - PUSH2_AT));
    return { cInf: 9 + 2 * k2, focus: () => lerp3([-1.0, 4.6, -1.2], [1.1, 3.9, 1.5], k2) };
  }
  const k = glide((f - PUSH3_AT) / (PUSH3_END - PUSH3_AT));
  return { cInf: 7 + 6 * k, focus: () => lerp3([0, 3.0, -2.0], [0.0, 1.4, 1.9], k) };
};
