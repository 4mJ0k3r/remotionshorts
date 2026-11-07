// Light presets for "Age 18". Same contract as the pardon engine: the key light is CAMERA-RELATIVE and frozen
// per shot (az = degrees from the shot's forward axis, +90 = screen right, 180 = behind the lens; el = elevation),
// so the sides we see stay lit through every glide. lit/shade/lift are LINEAR multipliers for shade.ts.
type C3 = [number, number, number];
export type LightName = "warm" | "clinic" | "day" | "night" | "twilight" | "bath" | "bank" | "golden"
  | "classroom" | "alert" | "lockdown" | "hall" | "lab" | "plaza";
export type LightPreset = {
  az: number; el: number;
  lit: C3; shade: C3; lift: C3; lambert: number; sideK: number; term: number;
  charTint: C3; charShade: number; charGrad: number; bodyGrad: number; sideTint: C3;
  blob: C3; actorShadow: boolean;
  top: string; hor: string; skyCurve: C3; fog: string; fogNear: number; fogFar: number; sunDisc: string;
  sunCol: string; sunI: number; sky: string; ground: string; hemiI: number;
  bias: number; normalBias: number; exposure: number;
};
export type WorldLook = {
  sky: { c: string[]; e: number[] };
  bounce: C3;
  sat: number;
  cloud: { lit: string; mid: string; shade: string };
};

export const LIGHTS: Record<LightName, LightPreset> = {
  // tungsten dining room: warm key from the pendant side, plum shadows
  warm: {
    az: 152, el: 38,
    lit: [1.46, 1.24, 0.94], shade: [0.30, 0.25, 0.27], lift: [0.05, 0.038, 0.036], lambert: 0.38, sideK: 0.84, term: 0.22,
    charTint: [1.0, 0.94, 0.88], charShade: 0.9, charGrad: 0.08, bodyGrad: 0.22, sideTint: [0.92, 0.88, 0.95],
    blob: [0.46, 0.4, 0.39], actorShadow: false,
    top: "#2a2140", hor: "#4a3a52", skyCurve: [0, 0.6, 1.0], fog: "#2a201c", fogNear: 8, fogFar: 42, sunDisc: "#000000",
    sunCol: "#ffd9a8", sunI: 2.2, sky: "#ffe4c0", ground: "#6a4a38", hemiI: 0.5,
    bias: -0.0003, normalBias: 0.018, exposure: 1.0,
  },
  // cool clinical white with blue shadow lift
  clinic: {
    az: 136, el: 36,
    lit: [1.48, 1.54, 1.58], shade: [0.33, 0.39, 0.46], lift: [0.035, 0.045, 0.06], lambert: 0.34, sideK: 0.86, term: 0.2,
    charTint: [1.0, 1.0, 1.02], charShade: 0.92, charGrad: 0.07, bodyGrad: 0.2, sideTint: [0.89, 0.92, 0.99],
    blob: [0.4, 0.44, 0.5], actorShadow: false,
    top: "#8fb4d8", hor: "#d6e6f2", skyCurve: [0, 0.5, 0.6], fog: "#b6c8d6", fogNear: 9, fogFar: 48, sunDisc: "#000000",
    sunCol: "#eef6ff", sunI: 2.6, sky: "#dfefff", ground: "#7a8794", hemiI: 0.55,
    bias: -0.00028, normalBias: 0.016, exposure: 1.0,
  },
  // clear noon outside the house
  day: {
    az: 146, el: 42,
    lit: [1.58, 1.5, 1.33], shade: [0.32, 0.30, 0.30], lift: [0.05, 0.048, 0.055], lambert: 0.35, sideK: 0.84, term: 0.2,
    charTint: [1.0, 0.94, 0.92], charShade: 0.86, charGrad: 0.075, bodyGrad: 0.2, sideTint: [0.9, 0.89, 0.95],
    blob: [0.62, 0.58, 0.58], actorShadow: false,
    top: "#3e7fd2", hor: "#b8d0ec", skyCurve: [0.0, 0.5, 0.6], fog: "#b8d0ec", fogNear: 25, fogFar: 300, sunDisc: "#000000",
    sunCol: "#fff3e0", sunI: 2.8, sky: "#dcecff", ground: "#b49a78", hemiI: 0.55,
    bias: -0.00025, normalBias: 0.015, exposure: 1.0,
  },
  // late-night living room lit by a TV: deep blue room, cool key from the screen side
  night: {
    az: 118, el: 16,
    lit: [0.56, 0.64, 0.96], shade: [0.10, 0.12, 0.24], lift: [0.008, 0.012, 0.03], lambert: 0.42, sideK: 0.82, term: 0.3,
    charTint: [0.86, 0.92, 1.08], charShade: 0.94, charGrad: 0.1, bodyGrad: 0.24, sideTint: [0.8, 0.86, 1.05],
    blob: [0.18, 0.2, 0.3], actorShadow: false,
    top: "#0a1024", hor: "#1a2540", skyCurve: [0, 0.5, 1], fog: "#131a2c", fogNear: 7, fogFar: 38, sunDisc: "#000000",
    sunCol: "#8fb4ff", sunI: 0.9, sky: "#26344f", ground: "#0e1420", hemiI: 0.3,
    bias: -0.0003, normalBias: 0.018, exposure: 1.12,
  },
  // violet dusk living room
  twilight: {
    az: 148, el: 22,
    lit: [0.78, 0.7, 0.98], shade: [0.16, 0.16, 0.31], lift: [0.018, 0.018, 0.042], lambert: 0.4, sideK: 0.84, term: 0.28,
    charTint: [0.94, 0.92, 1.04], charShade: 0.94, charGrad: 0.1, bodyGrad: 0.24, sideTint: [0.82, 0.84, 1.02],
    blob: [0.24, 0.24, 0.36], actorShadow: false,
    top: "#2a2350", hor: "#6a5490", skyCurve: [0, 0.6, 1], fog: "#3a345e", fogNear: 8, fogFar: 42, sunDisc: "#000000",
    sunCol: "#bcaaff", sunI: 1.3, sky: "#8f7fc0", ground: "#3a2f4a", hemiI: 0.4,
    bias: -0.0003, normalBias: 0.018, exposure: 1.06,
  },
  // clean bathroom white
  bath: {
    az: 150, el: 34,
    lit: [1.44, 1.44, 1.4], shade: [0.35, 0.36, 0.4], lift: [0.04, 0.042, 0.045], lambert: 0.34, sideK: 0.86, term: 0.2,
    charTint: [1.0, 1.0, 1.0], charShade: 0.9, charGrad: 0.07, bodyGrad: 0.2, sideTint: [0.9, 0.91, 0.96],
    blob: [0.42, 0.43, 0.45], actorShadow: false,
    top: "#a8c4d8", hor: "#e2eef4", skyCurve: [0, 0.5, 0.6], fog: "#c8d8e0", fogNear: 8, fogFar: 44, sunDisc: "#000000",
    sunCol: "#eef2f6", sunI: 2.0, sky: "#e8f0f6", ground: "#8a9098", hemiI: 0.5,
    bias: -0.0003, normalBias: 0.018, exposure: 1.0,
  },
  // neutral marble bank, warm-white fluorescents
  bank: {
    az: 160, el: 30,
    lit: [1.46, 1.44, 1.36], shade: [0.33, 0.33, 0.38], lift: [0.035, 0.038, 0.045], lambert: 0.36, sideK: 0.85, term: 0.2,
    charTint: [1.0, 0.99, 0.98], charShade: 0.9, charGrad: 0.07, bodyGrad: 0.2, sideTint: [0.91, 0.9, 0.96],
    blob: [0.44, 0.44, 0.47], actorShadow: false,
    top: "#8fa8c0", hor: "#e0eaf0", skyCurve: [0, 0.5, 0.6], fog: "#a8b4bc", fogNear: 9, fogFar: 46, sunDisc: "#000000",
    sunCol: "#fff4e2", sunI: 2.1, sky: "#e9f0f4", ground: "#7c7f88", hemiI: 0.5,
    bias: -0.0003, normalBias: 0.018, exposure: 1.0,
  },
  // golden hour on the lake
  golden: {
    az: 150, el: 10,
    lit: [1.78, 1.10, 0.56], shade: [0.40, 0.31, 0.27], lift: [0.075, 0.06, 0.06], lambert: 0.35, sideK: 0.86, term: 0.24,
    charTint: [1.0, 0.88, 0.74], charShade: 0.95, charGrad: 0.1, bodyGrad: 0.22, sideTint: [0.92, 0.87, 0.96],
    blob: [0.8, 0.78, 0.87], actorShadow: true,
    top: "#6a4f8c", hor: "#ffd9a8", skyCurve: [0.05, 0.6, 1.0], fog: "#ffd9a8", fogNear: 40, fogFar: 420, sunDisc: "#ffe0b0",
    sunCol: "#ffc98e", sunI: 4.0, sky: "#e2c2c0", ground: "#9a7a68", hemiI: 0.6,
    bias: -0.0006, normalBias: 0.03, exposure: 1.0,
  },
  // school day: key comes in from the tall left windows, cream bounce off the desks
  classroom: {
    az: 202, el: 34,
    lit: [1.52, 1.46, 1.28], shade: [0.30, 0.29, 0.32], lift: [0.055, 0.052, 0.06], lambert: 0.36, sideK: 0.85, term: 0.2,
    charTint: [1.0, 0.97, 0.92], charShade: 0.88, charGrad: 0.075, bodyGrad: 0.2, sideTint: [0.9, 0.9, 0.96],
    blob: [0.55, 0.53, 0.55], actorShadow: true,
    top: "#3e7fd2", hor: "#b8d0ec", skyCurve: [0.0, 0.5, 0.6], fog: "#c4d4e4", fogNear: 14, fogFar: 80, sunDisc: "#000000",
    sunCol: "#fff0d8", sunI: 2.9, sky: "#dcecff", ground: "#b49a78", hemiI: 0.58,
    bias: -0.0003, normalBias: 0.018, exposure: 1.0,
  },
  // the school day WHILE the alarm is sounding: the window key stays the key, so the cards, desks and cream walls keep
  // their colour and the lockdown is only a red rim plus the strobes. "lockdown" tints every light in the scene and
  // flattened the doorway shots into one magenta sheet.
  alert: {
    az: 202, el: 34,
    lit: [1.52, 1.44, 1.26], shade: [0.31, 0.29, 0.31], lift: [0.06, 0.05, 0.055], lambert: 0.36, sideK: 0.85, term: 0.22,
    charTint: [1.02, 0.96, 0.92], charShade: 0.88, charGrad: 0.075, bodyGrad: 0.2, sideTint: [0.95, 0.87, 0.93],
    blob: [0.55, 0.5, 0.52], actorShadow: true,
    top: "#3e7fd2", hor: "#b8d0ec", skyCurve: [0.0, 0.5, 0.6], fog: "#c6d2e0", fogNear: 14, fogFar: 80, sunDisc: "#000000",
    sunCol: "#ffeed4", sunI: 2.8, sky: "#dcecff", ground: "#b49a78", hemiI: 0.58,
    bias: -0.0003, normalBias: 0.018, exposure: 1.02,
  },
  // red lockdown: alarm strobes paint everything from screen right, cold window spill on the left. Kept for the
  // corridor/courtyard beats, where the whole building is under the alarm.
  lockdown: {
    az: 118, el: 28,
    lit: [1.42, 0.84, 0.76], shade: [0.34, 0.15, 0.17], lift: [0.055, 0.026, 0.03], lambert: 0.4, sideK: 0.8, term: 0.26,
    charTint: [1.04, 0.95, 0.93], charShade: 0.96, charGrad: 0.09, bodyGrad: 0.24, sideTint: [0.94, 0.86, 0.92],
    blob: [0.34, 0.2, 0.22], actorShadow: false,
    top: "#3a0e16", hor: "#661722", skyCurve: [0, 0.5, 0.8], fog: "#3a1016", fogNear: 12, fogFar: 62, sunDisc: "#000000",
    sunCol: "#ff6a54", sunI: 2.2, sky: "#6a1c24", ground: "#3a1a1e", hemiI: 0.42,
    bias: -0.0003, normalBias: 0.018, exposure: 1.06,
  },
  // locker hallway at night: cyan neon floor line, lavender ceiling panels, deep magenta falloff
  hall: {
    az: 168, el: 26,
    lit: [1.14, 1.24, 1.52], shade: [0.22, 0.25, 0.42], lift: [0.024, 0.03, 0.058], lambert: 0.42, sideK: 0.82, term: 0.28,
    charTint: [0.94, 0.98, 1.06], charShade: 0.94, charGrad: 0.1, bodyGrad: 0.24, sideTint: [0.84, 0.9, 1.06],
    blob: [0.2, 0.24, 0.34], actorShadow: false,
    top: "#0a1024", hor: "#1a2540", skyCurve: [0, 0.5, 1], fog: "#101a30", fogNear: 10, fogFar: 60, sunDisc: "#000000",
    sunCol: "#a8d8ff", sunI: 2.0, sky: "#2a3c5f", ground: "#0e1626", hemiI: 0.5,
    bias: -0.0003, normalBias: 0.018, exposure: 1.2,
  },
  // chemistry lab: cold top light, green glass bounce, frost blue shadows
  lab: {
    az: 154, el: 40,
    lit: [1.28, 1.4, 1.38], shade: [0.24, 0.32, 0.34], lift: [0.028, 0.045, 0.052], lambert: 0.38, sideK: 0.84, term: 0.24,
    charTint: [0.98, 1.02, 1.0], charShade: 0.92, charGrad: 0.08, bodyGrad: 0.22, sideTint: [0.88, 0.95, 1.02],
    blob: [0.34, 0.4, 0.42], actorShadow: false,
    top: "#6e8a96", hor: "#c2d2d4", skyCurve: [0, 0.5, 0.6], fog: "#9db4b8", fogNear: 12, fogFar: 60, sunDisc: "#000000",
    sunCol: "#eefaff", sunI: 2.1, sky: "#dfeff0", ground: "#6a7c80", hemiI: 0.44,
    bias: -0.0003, normalBias: 0.017, exposure: 0.9,
  },
  // courtyard midday: hard sun from the facade side, asphalt bounce
  plaza: {
    az: 138, el: 46,
    lit: [1.66, 1.56, 1.36], shade: [0.32, 0.3, 0.3], lift: [0.05, 0.048, 0.052], lambert: 0.34, sideK: 0.84, term: 0.19,
    charTint: [1.0, 0.95, 0.9], charShade: 0.86, charGrad: 0.075, bodyGrad: 0.2, sideTint: [0.9, 0.89, 0.95],
    blob: [0.64, 0.6, 0.58], actorShadow: true,
    top: "#3e7fd2", hor: "#b8d0ec", skyCurve: [0.0, 0.5, 0.6], fog: "#b8d0ec", fogNear: 40, fogFar: 460, sunDisc: "#fff0c8",
    sunCol: "#fff3e0", sunI: 3.1, sky: "#dcecff", ground: "#a89078", hemiI: 0.6,
    bias: -0.0004, normalBias: 0.02, exposure: 1.0,
  },
};

export const LOOK: Record<LightName, WorldLook> = {
  warm: {
    sky: { c: ["#2a2140", "#3a2d4e", "#4a3858", "#2e2338", "#1a1326"], e: [0, 4, 10, 24, 48] },
    bounce: [0.02, 0.012, 0.008], sat: 1.0, cloud: { lit: "#4a3a52", mid: "#382c44", shade: "#241c30" },
  },
  clinic: {
    sky: { c: ["#d6e6f2", "#c4d9ea", "#a8c6de", "#8fb2cc", "#7098b8"], e: [0, 5, 12, 24, 40] },
    bounce: [0, 0, 0], sat: 1.0, cloud: { lit: "#f4f8fc", mid: "#e2ecf4", shade: "#c8d8e6" },
  },
  day: {
    sky: { c: ["#b8d0ec", "#9cbfea", "#6a9fe0", "#4f8cdb", "#3373cc"], e: [0, 3, 8, 16, 40] },
    bounce: [0, 0, 0], sat: 1.0, cloud: { lit: "#fbf8f1", mid: "#e1e5f3", shade: "#c3cbe9" },
  },
  night: {
    sky: { c: ["#1a2540", "#152038", "#101a2e", "#0c1424", "#080e1a"], e: [0, 5, 12, 24, 40] },
    bounce: [0, 0, 0.01], sat: 0.96, cloud: { lit: "#26344f", mid: "#1c2840", shade: "#131a2c" },
  },
  twilight: {
    sky: { c: ["#6a5490", "#5a4880", "#463a6e", "#332c58", "#241f42"], e: [0, 6, 14, 26, 44] },
    bounce: [0.02, 0.01, 0.02], sat: 0.98, cloud: { lit: "#b49ac8", mid: "#8a74a8", shade: "#5e4e7c" },
  },
  bath: {
    sky: { c: ["#e2eef4", "#d6e6ee", "#c4dae6", "#b0cad8", "#98b8ca"], e: [0, 5, 12, 24, 40] },
    bounce: [0, 0, 0], sat: 1.0, cloud: { lit: "#f4f8fc", mid: "#e6eef4", shade: "#d0e0ea" },
  },
  bank: {
    sky: { c: ["#e0eaf0", "#d4e2ea", "#c0d2de", "#a8c0d0", "#8fa8bc"], e: [0, 5, 12, 24, 40] },
    bounce: [0, 0, 0], sat: 1.0, cloud: { lit: "#f4f8fc", mid: "#e4ecf2", shade: "#ccdae4" },
  },
  golden: {
    // tight bands: the visible sky above the lake is only 0-18 degrees, so the sunset has to turn inside it
    sky: { c: ["#ffeacb", "#ffcf92", "#f09a86", "#a8729a", "#6a5486"], e: [0, 3, 8, 15, 26] },
    bounce: [0.05, 0.03, 0.0], sat: 0.98, cloud: { lit: "#ffe6c4", mid: "#f7b79c", shade: "#b49ac8" },
  },
  classroom: {
    sky: { c: ["#b8d0ec", "#9cbfea", "#6a9fe0", "#4f8cdb", "#3373cc"], e: [0, 3, 8, 16, 40] },
    bounce: [0.03, 0.02, 0.0], sat: 1.0, cloud: { lit: "#fbf8f1", mid: "#e1e5f3", shade: "#c3cbe9" },
  },
  alert: {
    sky: { c: ["#b8d0ec", "#9cbfea", "#6a9fe0", "#4f8cdb", "#3373cc"], e: [0, 3, 8, 16, 40] },
    bounce: [0.03, 0.018, 0.004], sat: 0.99, cloud: { lit: "#fbf8f1", mid: "#e1e5f3", shade: "#c3cbe9" },
  },
  lockdown: {
    sky: { c: ["#3a0e18", "#4a1420", "#5a1a26", "#40141c", "#2a0c14"], e: [0, 4, 10, 24, 48] },
    bounce: [0.04, 0.008, 0.0], sat: 0.96, cloud: { lit: "#6a2430", mid: "#4a1822", shade: "#2a0e16" },
  },
  hall: {
    sky: { c: ["#101a30", "#0c1426", "#0a1020", "#080c18", "#060812"], e: [0, 5, 12, 24, 40] },
    bounce: [0, 0.006, 0.02], sat: 0.98, cloud: { lit: "#26344f", mid: "#1c2840", shade: "#131a2c" },
  },
  lab: {
    sky: { c: ["#d6e4e6", "#c8dade", "#b4ccd0", "#9cb8be", "#84a4ac"], e: [0, 5, 12, 24, 40] },
    bounce: [0, 0.01, 0.01], sat: 1.0, cloud: { lit: "#f4f8fc", mid: "#e2ecf0", shade: "#c8d8dc" },
  },
  plaza: {
    sky: { c: ["#b8d0ec", "#9cbfea", "#6a9fe0", "#4f8cdb", "#3373cc"], e: [0, 3, 8, 16, 40] },
    bounce: [0.02, 0.012, 0.0], sat: 1.0, cloud: { lit: "#fbf8f1", mid: "#e1e5f3", shade: "#c3cbe9" },
  },
};
