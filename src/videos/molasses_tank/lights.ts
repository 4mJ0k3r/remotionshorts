// Lighting presets for MolassesTankShort:
// Shot 1 & 3: "boston_day" (chilly crisp winter morning 1919 Boston harbor, steel tanks, cobblestone).
// Shot 2: "cab_warm" (interior streetcar cab lighting with emergency warning glow).
type C3 = [number, number, number];

export type LightName = "boston_day" | "cab_warm";
export type LightPreset = {
  az: number; el: number;
  lit: C3; shade: C3; lift: C3; lambert: number; sideK: number; term: number;
  charTint: C3; charShade: number; charGrad: number; bodyGrad: number; sideTint: C3;
  blob: C3; actorShadow: boolean;
  fog: string; fogNear: number; fogFar: number;
  sunCol: string; sunI: number; sky: string; ground: string; hemiI: number;
  bias: number; normalBias: number; exposure: number;
};
export type WorldLook = {
  sky: { c: string[]; e: number[] };
  bounce: C3;
  sat: number;
};

export const LIGHTS: Record<LightName, LightPreset> = {
  boston_day: {
    az: -130, el: 48,
    lit: [1.58, 1.50, 1.40], shade: [0.44, 0.46, 0.56], lift: [0.05, 0.05, 0.07], lambert: 0.32, sideK: 0.86, term: 0.16,
    charTint: [1.0, 0.98, 0.95], charShade: 0.88, charGrad: 0.06, bodyGrad: 0.18, sideTint: [0.90, 0.90, 0.98],
    blob: [0.5, 0.52, 0.5], actorShadow: true,
    fog: "#cfdfee", fogNear: 45, fogFar: 280,
    sunCol: "#fff6e6", sunI: 3.0, sky: "#d2e6f8", ground: "#6a6e72", hemiI: 0.6,
    bias: -0.0004, normalBias: 0.02, exposure: 1.0,
  },
  cab_warm: {
    az: -115, el: 40,
    lit: [1.68, 1.46, 1.18], shade: [0.48, 0.40, 0.36], lift: [0.08, 0.06, 0.05], lambert: 0.38, sideK: 0.88, term: 0.18,
    charTint: [1.02, 0.96, 0.90], charShade: 0.85, charGrad: 0.08, bodyGrad: 0.22, sideTint: [0.92, 0.85, 0.80],
    blob: [0.45, 0.42, 0.4], actorShadow: true,
    fog: "#2e221a", fogNear: 15, fogFar: 75,
    sunCol: "#ffe0b2", sunI: 2.8, sky: "#543c26", ground: "#32251a", hemiI: 0.5,
    bias: -0.0004, normalBias: 0.02, exposure: 1.05,
  },
};

export const LOOK: Record<LightName, WorldLook> = {
  boston_day: {
    sky: { c: ["#edf4fb", "#c4e0f6", "#8ec5ee", "#52a5e8", "#2b82d0"], e: [0, 4, 12, 25, 55] },
    bounce: [0.03, 0.025, 0.01], sat: 1.05,
  },
  cab_warm: {
    sky: { c: ["#3d2c20", "#302216", "#24180f", "#180f08", "#0d0704"], e: [0, 5, 15, 30, 60] },
    bounce: [0.05, 0.03, 0.01], sat: 1.10,
  },
};
