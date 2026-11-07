// Timeline of "Age 18" — 61.6 s (1848 f @ 30 fps), twelve shots through one life that never ages.
// Places: the birthday dining room (1, 12), the clinic (2, 5), the street outside the house (3), the night
// living room (4, 10), the bathroom (6), the bank counter (7, 8), the golden lakeside bench (9) and the night
// window (11). Camera grammar as in the calibrated shorts: smootherstep glides 18-40 f, holds push in
// 0.1-0.35 %/f, reframes are cuts, impacts are 7-frame alternating kicks. Cuts between places crossfade 6 f.
export const FPS = 30;
export const TOTAL = 1848;
export const D0 = 0;
export type V3 = [number, number, number];

export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };

// ---------------- places (shared by world.ts and cast.ts) ----------------
export const DINING = { hero: [0, 0, 1.02] as V3, table: [0, 0, 0.15] as V3, cake: [0, 1.06, 0.22] as V3, lamp: [0, 2.18, 0.2] as V3 };
export const CLINIC = {
  hero: [-0.5, 0, 0.4] as V3, doctor: [0.62, 0, 0.55] as V3, tablet: [0.32, 1.05, 0.12] as V3,
  bed: [-1.35, 0, 0.62] as V3, ecg: [1.85, 0, 1.5] as V3, poster: [-1.9, 2.0, 2.72] as V3,
};
export const CLINIC5 = {
  hero: [-0.6, 0, 0.5] as V3, doctor: [0.42, 0, 0.62] as V3,
  // three fanned cards between the two, chest height, small enough to clear the doctor's face and the frame edge
  cards: [[-0.32, 0.98, 0.3], [-0.2, 1.02, 0.32], [-0.08, 1.06, 0.34]] as V3[],
};
export const STREET = {
  hero0: [-0.7, 0, 0.9] as V3, hero1: [-0.3, 0, 0.78] as V3, theo: [0.42, 0, 0.68] as V3,
  box: [0.45, 0, 1.0] as V3, van: [-4.8, 0, 3.0] as V3,
};
export const LIVING = {
  sofa: [0, 0, 0.82] as V3, hero: [-0.1, 0, 0.72] as V3, friend: [0.9, 0, 0.74] as V3,
  tv: [1.15, 0.5, 2.55] as V3, clock: [0.92, 2.05, 2.94] as V3,
};
export const BATH = { hero: [-0.5, 0, 0.3] as V3, sink: [-0.5, 0.9, 1.9] as V3, mirror: [-0.5, 1.56, 2.08] as V3 };
export const BANK = { hero: [-0.6, 0, 0.5] as V3, teller: [0.3, 0, 1.75] as V3, officer: [0.72, 0, 1.52] as V3, monitor: [1.55, 1.5, 1.2] as V3 };
export const DOCK = { hero: [0, 0, 0.75] as V3, mom: [-0.85, 0, 0.78] as V3, theo: [0.9, 0, 0.78] as V3, bench: [0, 0.44, 1.24] as V3 };
export const WINDOW = { hero: [0, 0, 0.55] as V3, win: [0.55, 1.65, 2.36] as V3 };

// ---------------- beats ----------------
/** the 18/18/18 spark on the doctor's tablet (measured drop of the track at 8.15 s = f245; script beat f240) */
export const FLASH_AT = 240;
/** candle blow-out in the hook: whistle mouth, smoke, cyan frost ring */
export const BLOW_AT = 138;
/** final loop: the double clap measured in the track at 60.00 s / 60.65 s (f1800 / f1819); the hero blows on the first */
export const CLAP1 = 1800;
export const CLAP2 = 1819;
export const BLOW2_AT = 1800;

export type Light = "warm" | "clinic" | "day" | "night" | "twilight" | "bath" | "bank" | "golden";
export type SetName = "dining" | "clinic" | "street" | "living" | "bath" | "bank" | "dock" | "window";
export type ShotDef = { id: number; a: number; b: number; light: Light; set: SetName };
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 174, light: "warm", set: "dining" },
  { id: 2, a: 174, b: 369, light: "clinic", set: "clinic" },
  { id: 3, a: 369, b: 480, light: "day", set: "street" },
  { id: 4, a: 480, b: 654, light: "night", set: "living" },
  { id: 5, a: 654, b: 864, light: "clinic", set: "clinic" },
  { id: 6, a: 864, b: 966, light: "bath", set: "bath" },
  { id: 7, a: 966, b: 1086, light: "bank", set: "bank" },
  { id: 8, a: 1086, b: 1194, light: "bank", set: "bank" },
  { id: 9, a: 1194, b: 1344, light: "golden", set: "dock" },
  { id: 10, a: 1344, b: 1464, light: "twilight", set: "living" },
  { id: 11, a: 1464, b: 1620, light: "night", set: "window" },
  { id: 12, a: 1620, b: TOTAL, light: "warm", set: "dining" },
];
export const XFADE: Record<number, number> = { 2: 6, 3: 6, 4: 6, 5: 6, 6: 6, 7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 12: 6 };

export const shotAt = (f: number) => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
export const layersAt = (f: number): { id: number; alpha: number }[] => {
  for (const s of SHOTS) {
    const x = XFADE[s.id];
    if (x && f >= s.a - x / 2 && f < s.a + x / 2) return [{ id: s.id - 1, alpha: 1 }, { id: s.id, alpha: (f - (s.a - x / 2) + 1) / (x + 1) }];
  }
  return [{ id: shotAt(f).id, alpha: 1 }];
};

/** HUD age: 18 -> 28 -> 40 -> 70 -> 1,000; LOOKS [18] never moves. Shot 10 ticks through 100/300/700 before 1,000. */
export const badgeAge = (id: number, f: number): number => {
  if (id <= 2) return 18;
  if (id <= 5) return 28;
  if (id <= 8) return 40;
  if (id === 9) return 70;
  if (id === 10) return f < 1372 ? 70 : f < 1398 ? 100 : f < 1424 ? 300 : f < 1450 ? 700 : 1000;
  return 1000;
};

// ---------------- camera ----------------
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
const pushK = (f: number, f0: number, rate: number, punch = 0, n = 35) => {
  const x = Math.max(0, f - f0);
  let s = rate * x;
  if (punch > rate) for (let i = 0; i < Math.min(x, n); i++) s += (punch - rate) * Math.max(0, Math.min(1, (i + 0.5) / 8, (n - i - 0.5) / 8));
  return Math.exp(-s);
};
const dolly = (pos: V3, look: V3, k: number, rest: Partial<Cam> = {}): Shot =>
  ({ pos: [look[0] + (pos[0] - look[0]) * k, look[1] + (pos[1] - look[1]) * k, look[2] + (pos[2] - look[2]) * k], look, ...rest });

// shot 1: birthday wide -> medium, hero behind the cake
const S1a = (f: number) => dolly([0.1, 1.58, -3.35], [0, 1.16, 0.62], pushK(f, 0, 0.0016), { fov: 44 });
const S1b = (f: number) => dolly([0.05, 1.54, -2.9], [0.02, 1.14, 0.56], pushK(f, 96, 0.0012), { fov: 42, roll: -0.008 });
// shot 2: exam two-shot -> tablet insert. 2b keeps both heads in the safe zone while the tablet reads between them
const S2a = (f: number) => dolly([0.15, 1.55, -4.4], [0.02, 1.28, 0.5], pushK(f, 174, 0.001), { fov: 44 });
const S2b = (f: number) => dolly([0.14, 1.4, -3.05], [0.02, 1.14, 0.38], pushK(f, 285, 0.0011), { fov: 50, roll: 0.01 });
// shot 3: the street, hero hauling; glide toward Theo's aching back
const S3a = (f: number) => dolly([0.0, 1.55, -4.5], [0.0, 1.12, 0.8], pushK(f, 369, 0.0012), { fov: 46 });
const S3b = (f: number) => dolly([0.1, 1.5, -3.85], [0.0, 1.18, 0.65], pushK(f, 424, 0.001), { fov: 44, roll: 0.008 });
// shot 4: pizza on the sofa -> stand, wink, point at himself
const S4a = (f: number) => dolly([0.2, 1.5, -3.6], [0.25, 1.08, 0.72], pushK(f, 480, 0.0013), { fov: 44 });
const S4b = (f: number) => dolly([0.1, 1.44, -2.9], [-0.1, 1.32, 0.72], pushK(f, 562, 0.0011), { fov: 42, roll: 0.012 });
// shot 5: hazard cards -> helmet + seatbelt panic
const S5a = (f: number) => dolly([-0.2, 1.55, -4.7], [-0.2, 1.28, 0.55], pushK(f, 654, 0.0006), { fov: 46 });
const S5b = (f: number) => dolly([-0.4, 1.5, -3.9], [-0.4, 1.35, 0.5], pushK(f, 772, 0.0011), { fov: 44 });
// shot 6: the bathroom mirror, pulled back and higher so the torso clears the vanity
const S6a = (f: number) => dolly([0.25, 1.63, -3.18], [-0.5, 1.22, 0.35], pushK(f, 864, 0.0016), { fov: 42 });
const S6b = (f: number) => dolly([0.18, 1.58, -2.95], [-0.48, 1.27, 0.32], pushK(f, 922, 0.0011), { fov: 39, roll: -0.01 });
// shot 7: ID held out at the bank counter, officer behind the counter on the left
const S7a = (f: number) => dolly([0.2, 1.55, -4.7], [0.02, 1.26, 1.0], pushK(f, 966, 0.001), { fov: 48 });
const S7b = (f: number) => dolly([0.03, 1.5, -3.25], [-0.35, 1.3, 0.7], pushK(f, 1032, 0.001), { fov: 42, roll: 0.01 });
// shot 8: monitor close-up, the frozen stamp
const S8a = (f: number) => dolly([1.2, 1.56, -1.7], [1.5, 1.54, 1.2], pushK(f, 1086, 0.0015), { fov: 40 });
const S8b = (f: number) => dolly([1.15, 1.54, -1.55], [1.5, 1.54, 1.2], pushK(f, 1140, 0.0009), { fov: 38, roll: 0.01 });
// shot 9: the bench, the lake, the two who fade
const S9a = (f: number) => dolly([0.1, 1.5, -4.2], [0, 1.05, 0.9], pushK(f, 1194, 0.0011), { fov: 46 });
const S9b = (f: number) => dolly([0.1, 1.47, -3.95], [-0.02, 1.07, 0.9], pushK(f, 1288, 0.0008), { fov: 44, roll: -0.008 });
// shot 10: alone with the album, the badge ticking toward 1,000
const S10a = (f: number) => dolly([0.74, 1.4, -3.4], [-0.16, 0.98, 0.72], pushK(f, 1344, 0.0013), { fov: 41 });
const S10b = (f: number) => dolly([0.66, 1.36, -3.15], [-0.14, 1.0, 0.72], pushK(f, 1408, 0.0009), { fov: 39, roll: 0.01 });
// shot 11: night window close on the heavy eyes
const S11a = (f: number) => dolly([0.26, 1.43, -2.65], [0, 1.28, 0.6], pushK(f, 1464, 0.0014), { fov: 37 });
const S11b = (f: number) => dolly([0.2, 1.4, -2.45], [-0.02, 1.3, 0.6], pushK(f, 1548, 0.0008), { fov: 35, roll: -0.01 });
// shot 12: back at the table with the 1000 cake; clap, look to lens, candles die
const S12a = (f: number) => dolly([0.36, 1.56, -2.96], [0.05, 1.12, 0.58], pushK(f, 1620, 0.0018), { fov: 44 });
const S12b = (f: number) => dolly([0.3, 1.5, -2.58], [0.05, 1.14, 0.54], pushK(f, 1746, 0.0012), { fov: 41, roll: 0.01 });

const CAMS: Record<number, Key[]> = {
  1: [{ f: 0, s: S1a }, { f: 96, dur: 38, s: S1b }],
  2: [{ f: 174, s: S2a }, { f: 285, dur: 38, s: S2b }],
  3: [{ f: 369, s: S3a }, { f: 424, dur: 30, s: S3b }],
  4: [{ f: 480, s: S4a }, { f: 562, dur: 34, s: S4b }],
  5: [{ f: 654, s: S5a }, { f: 772, dur: 36, s: S5b }],
  6: [{ f: 864, s: S6a }, { f: 922, dur: 28, s: S6b }],
  7: [{ f: 966, s: S7a }, { f: 1032, dur: 30, s: S7b }],
  8: [{ f: 1086, s: S8a }, { f: 1140, dur: 28, s: S8b }],
  9: [{ f: 1194, s: S9a }, { f: 1288, dur: 34, s: S9b }],
  10: [{ f: 1344, s: S10a }, { f: 1408, dur: 30, s: S10b }],
  11: [{ f: 1464, s: S11a }, { f: 1548, dur: 34, s: S11b }],
  12: [{ f: 1620, s: S12a }, { f: 1746, dur: 34, s: S12b }],
};

const KICKS: [number, number][] = [[FLASH_AT, 0.8], [1800, 0.9], [1819, 0.9]];
export const kickAt = (t: number) => {
  let a = 0;
  for (const [t0, g] of KICKS) {
    const n = Math.floor((t - t0 / FPS) * FPS + 1e-6);
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
  { f: 0, cInf: 10, focus: () => [0, 1.45, 1.02] },
  { f: 96, cInf: 13, focus: () => [0, 1.3, 0.8] },
  { f: 174, cInf: 15, focus: () => [0.02, 1.3, 0.45] },
  { f: 285, cInf: 20, focus: () => [0.32, 1.05, 0.12] },
  { f: 369, cInf: 9, focus: () => [-0.25, 1.3, 0.78] },
  { f: 424, cInf: 11, dur: 24, focus: () => [0.15, 1.25, 0.68] },
  { f: 480, cInf: 12, focus: () => [0, 1.2, 0.74] },
  { f: 562, cInf: 15, dur: 24, focus: () => [-0.1, 1.42, 0.72] },
  { f: 654, cInf: 16, focus: () => [-0.6, 1.45, 0.5] },
  { f: 772, cInf: 20, focus: () => [-0.4, 1.45, 0.5] },
  { f: 864, cInf: 12, focus: () => [-0.5, 1.42, 0.3] },
  { f: 922, cInf: 16, focus: () => [-0.48, 1.38, 0.3] },
  { f: 966, cInf: 10, focus: () => [-0.6, 1.35, 0.5] },
  { f: 1032, cInf: 13, dur: 24, focus: () => [-0.55, 1.38, 0.55] },
  { f: 1086, cInf: 9, focus: () => [1.5, 1.54, 1.2] },
  { f: 1194, cInf: 12, focus: () => [0, 1.15, 0.78] },
  { f: 1288, cInf: 14, dur: 24, focus: () => [0, 1.2, 0.78] },
  { f: 1344, cInf: 10, focus: () => [0, 1.05, 0.72] },
  { f: 1464, cInf: 10, focus: () => [0, 1.45, 0.6] },
  { f: 1620, cInf: 12, focus: () => [0, 1.2, 0.9] },
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
