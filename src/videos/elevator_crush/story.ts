// Single source of truth for ElevatorCrushShort time, beats, 11 shots, camera paths, kicks, DOF.
// Pure math only — no Three.js meshes. 1080x1920 @ 30 fps, TOTAL = 3345 frames (111.5 s).
export const FPS = 30;
export const TOTAL = 3345;

export type LightName =
  | "amberCyan" | "rainy" | "emergency" | "violetRim"
  | "heartbeat" | "goldWarm" | "roseGold" | "neon";

export type ShotDef = {
  id: number;
  a: number; // inclusive start
  b: number; // exclusive end
  light: LightName;
  desc: string;
};

export const SHOTS: ShotDef[] = [
  { id: 1,  a: 0,    b: 210,  light: "amberCyan",  desc: "Hook: trapped 3 hours with crush, doors slide shut" },
  { id: 2,  a: 210,  b: 405,  light: "rainy",      desc: "1 sec before closing in the rain, crush enters" },
  { id: 3,  a: 405,  b: 660,  light: "emergency",  desc: "BHADAAM! power cut stuck at floor 4" },
  { id: 4,  a: 660,  b: 906,  light: "emergency",  desc: "Hour 1: pin-drop silence, zero network" },
  { id: 5,  a: 906,  b: 1170, light: "emergency",  desc: "Fixing hair vs inspecting floor buttons (Rule B)" },
  { id: 6,  a: 1170, b: 1524, light: "emergency",  desc: "Dry throat cough & loud stomach growl" },
  { id: 7,  a: 1524, b: 1818, light: "violetRim",  desc: "Hour 2: cable grinds & 2-foot drop" },
  { id: 8,  a: 1818, b: 2196, light: "heartbeat",  desc: "She hugs you tight + 160 BPM heartbeat" },
  { id: 9,  a: 2196, b: 2466, light: "goldWarm",   desc: "Trembling hands, safety brakes locked" },
  { id: 10, a: 2466, b: 2835, light: "roseGold",   desc: "Dim light returns & eye contact" },
  { id: 11, a: 2835, b: 3345, light: "neon",       desc: "Cliffhanger: secret & mystery number on palm" },
];

export const shotAt = (f: number): ShotDef => {
  for (const s of SHOTS) if (f >= s.a && f < s.b) return s;
  return SHOTS[SHOTS.length - 1];
};

export const layersAt = (f: number): { id: number; alpha: number }[] => {
  const s = shotAt(f);
  return [{ id: s.id, alpha: 1.0 }];
};

// ---- math helpers ----
export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
export const glide = (f: number, a: number, b: number) => {
  const t = clamp01((f - a) / Math.max(1, b - a));
  return t * t * (3 - 2 * t);
};
export const lerp = (v0: number, v1: number, t: number) => v0 + (v1 - v0) * t;
export const v3Lerp = (
  p0: [number, number, number], p1: [number, number, number], t: number
): [number, number, number] => [lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t), lerp(p0[2], p1[2], t)];

/** Subtle continuous drift so held frames <= 2% */
export const pushK = (f: number, a: number, b: number, dist = 0.06) => {
  const t = clamp01((f - a) / Math.max(1, b - a));
  return t * dist;
};

// ---- KEY BEAT FRAMES ----
export const DOORS_AT = 90;      // shot 1 doors fully shut
export const RAIN_IN_AT = 285;   // shot 2 crush steps in
export const RAIN_BURST_AT = 310;// rain droplet sparkle burst
export const BHDAM_AT = 486;      // power cut impact (16.2s)
export const PHONE_AT = 780;     // shot 4 phones raise
export const COUGH_AT = 1248;    // 41.6s cough
export const GROWL_AT = 1355;    // 45.2s stomach growl
export const CABLE_AT = 1665;    // 55.5s cable grind sparks
export const DROP_AT = 1710;     // 57.0s elevator 2-ft drop
export const HUG_AT = 1885;      // crush hugs hero, heart burst
export const HEART_AT = 1980;     // heartbeat rings start
export const LIGHTS_BACK_AT = 2480; // shot 10 dim light returns
export const SPARKLE_AT = 2720;   // shot 10 golden sparkles
export const WRITE_AT = 3020;    // shot 11 palm writing ends
export const PALM_AT = 3150;     // shot 11 cyan eyes + burst
export const END_AT = 3344;

// ---- KICKS (impact camera shakes) ----
export type Kick = { f: number; dur: number; amp: number; freq: number };
export const KICKS: Kick[] = [
  { f: BHDAM_AT, dur: 12, amp: 0.11, freq: 2.0 },  // power cut bhadaam
  { f: GROWL_AT, dur: 10, amp: 0.08, freq: 2.4 },  // stomach growl
  { f: CABLE_AT, dur: 12, amp: 0.09, freq: 2.2 },  // cable grind
  { f: DROP_AT,  dur: 14, amp: 0.13, freq: 1.8 },  // 2-foot drop
];

export const kickOffset = (f: number): [number, number, number] => {
  let ox = 0, oy = 0, oz = 0;
  for (const k of KICKS) {
    if (f >= k.f && f < k.f + k.dur) {
      const u = (f - k.f) / k.dur;
      const decay = (1 - u) * (1 - u);
      const s = Math.sin((f - k.f) * k.freq) * k.amp * decay;
      ox += s * 0.4; oy += s * 1.0; oz += s * 0.3;
    }
  }
  return [ox, oy, oz];
};

// ---- CAMERAS ----
export type CamState = { pos: [number, number, number]; look: [number, number, number]; fov: number };

type CamDef = {
  posA: [number, number, number]; posB: [number, number, number];
  look: [number, number, number]; lookB?: [number, number, number]; fov: number;
};

// The cabin is a cut-away set: front doors wall at z = -1.8, side walls x = +-2.3, walls/floor/ceiling run past the
// camera (z = 5.6) so no set edge is ever visible. Cameras sit in the open "fourth wall" side looking toward -z.
// Shot 5 pans (lookA -> lookB) from the crush in the front-left corner to the hero at the brass panel (front-right).
const CAMS: Record<number, CamDef> = {
  1:  { posA: [-1.0, 1.55, 5.6],  posB: [-0.6, 1.5, 4.6],   look: [0.0, 1.3, 1.3],  fov: 46 },
  2:  { posA: [1.4, 1.5, 5.4],    posB: [0.8, 1.45, 4.4],   look: [0.0, 1.3, 0.6],  fov: 46 },
  3:  { posA: [-0.9, 1.0, 4.6],   posB: [-0.5, 1.1, 3.9],   look: [0.0, 1.6, 1.0],  fov: 48 },
  4:  { posA: [0.0, 1.5, 5.4],    posB: [0.3, 1.45, 4.6],   look: [0.0, 1.3, 0.8],  fov: 48 },
  5:  { posA: [-0.2, 1.5, 2.6],   posB: [0.1, 1.45, 1.9],   look: [-1.0, 1.3, -0.8], lookB: [1.2, 1.15, -1.45], fov: 45 },
  6:  { posA: [0.85, 1.75, 4.0],  posB: [0.55, 1.6, 3.3],   look: [0.0, 1.25, 1.1], fov: 44 },
  7:  { posA: [0.0, 1.05, 5.2],   posB: [0.0, 1.15, 4.6],   look: [0.0, 2.3, 0.8],  fov: 50 },
  8:  { posA: [-1.1, 1.48, 4.2],  posB: [-0.65, 1.44, 3.3], look: [0.0, 1.35, 1.3], fov: 43 },
  9:  { posA: [1.05, 1.52, 4.6],  posB: [0.75, 1.48, 4.0] , look: [-0.05, 1.36, 1.4], fov: 42 },
  10: { posA: [-1.05, 1.46, 4.7], posB: [-0.7, 1.44, 4.1] , look: [0.0, 1.36, 1.4], fov: 42 },
  11: { posA: [0.0, 1.6, 5.6],    posB: [0.0, 1.5, 4.2]  ,  look: [0.0, 1.36, 1.35], fov: 44 },
};

export const camAt = (id: number, f: number): CamState => {
  const s = SHOTS[id - 1];
  const c = CAMS[id];
  const [kx, ky, kz] = kickOffset(f);
  const span = s.b - s.a;
  const moveEnd = s.a + Math.floor(span * 0.72);
  const t = glide(f, s.a, moveEnd);
  const drift = pushK(f, moveEnd, s.b, 0.07);
  const pos = v3Lerp(c.posA, c.posB, t);
  pos[2] -= drift;
  const look = c.lookB ? v3Lerp(c.look, c.lookB, glide(f, s.a + 60, s.a + 190)) : c.look;
  return {
    pos: [pos[0] + kx, pos[1] + ky, pos[2] + kz],
    look,
    fov: c.fov,
  };
};

/** Per-frame light: shot 3 stays in the normal cabin look until the BHADAAM power cut. */
export const lightAt = (id: number, f: number): LightName => {
  if (id === 3 && f < BHDAM_AT) return "amberCyan";
  return SHOTS[id - 1].light;
};

// ---- DOF ----
export type DofSpec = { focus: (f: number) => [number, number, number]; cInf: number };

// Focus follows the live look target (which sits on the characters) so subjects are sharp from f = 0.
export const dofAt = (f: number): DofSpec => {
  const s = shotAt(f);
  const look = camAt(s.id, f).look;
  return { focus: () => [look[0], look[1], look[2]], cInf: 6 };
};
