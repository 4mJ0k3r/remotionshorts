// Lighting presets for ElevatorCrushShort. CRITICAL RULE 9: every preset keeps scene luma in
// 0.38..0.65 — "power cut" shots use a rich Amber-Crimson Emergency Glow (~0.44), "blackout embrace"
// shots use a Magical Twilight-Violet / Neon Pink-Crimson rim (~0.41-0.46), NEVER pitch black.
type C3 = [number, number, number];

export type LightName =
  | "amberCyan"   // Shot 1: amber-cyan dual rim
  | "rainy"       // Shot 2: cool rainy blue-violet corridor
  | "emergency"   // Shots 3-6: amber-red emergency glow (power cut) luma ~0.44
  | "violetRim"   // Shot 7: deep violet-crimson rim luma ~0.41
  | "heartbeat"   // Shot 8: crimson-pink heartbeat aura luma ~0.43
  | "goldWarm"    // Shot 9: warm silver-gold rim luma ~0.45
  | "roseGold"    // Shot 10: rose-gold tungsten cabin luma ~0.52
  | "neon";       // Shot 11: neon cyan & violet mystery luma ~0.46

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
  amberCyan: {
    az: -120, el: 42,
    lit: [1.55, 1.35, 1.05], shade: [0.42, 0.38, 0.52], lift: [0.06, 0.05, 0.08], lambert: 0.34, sideK: 0.86, term: 0.18,
    charTint: [1.0, 0.97, 0.94], charShade: 0.88, charGrad: 0.07, bodyGrad: 0.18, sideTint: [0.90, 0.92, 1.0],
    blob: [0.5, 0.5, 0.52], actorShadow: true,
    fog: "#2a2438", fogNear: 8, fogFar: 60,
    sunCol: "#ffd9a0", sunI: 2.6, sky: "#3a3450", ground: "#241f2e", hemiI: 0.55,
    bias: -0.0004, normalBias: 0.02, exposure: 1.0,
  },
  rainy: {
    az: -100, el: 36,
    lit: [1.25, 1.35, 1.80], shade: [0.36, 0.40, 0.62], lift: [0.04, 0.05, 0.10], lambert: 0.38, sideK: 0.88, term: 0.22,
    charTint: [0.96, 0.98, 1.05], charShade: 0.86, charGrad: 0.08, bodyGrad: 0.20, sideTint: [0.88, 0.92, 1.05],
    blob: [0.42, 0.46, 0.55], actorShadow: true,
    fog: "#16223f", fogNear: 6, fogFar: 50,
    sunCol: "#aac4ff", sunI: 2.2, sky: "#1a2a4a", ground: "#0e1626", hemiI: 0.5,
    bias: -0.0004, normalBias: 0.02, exposure: 1.08,
  },
  emergency: {
    az: -130, el: 30,
    lit: [2.0, 0.85, 0.42], shade: [0.48, 0.24, 0.18], lift: [0.12, 0.05, 0.03], lambert: 0.40, sideK: 0.86, term: 0.22,
    charTint: [1.05, 0.92, 0.82], charShade: 0.86, charGrad: 0.09, bodyGrad: 0.22, sideTint: [0.96, 0.86, 0.80],
    blob: [0.45, 0.30, 0.26], actorShadow: true,
    fog: "#2a1210", fogNear: 6, fogFar: 48,
    sunCol: "#ff9a4a", sunI: 2.6, sky: "#3a1a16", ground: "#1c0d0a", hemiI: 0.5,
    bias: -0.0004, normalBias: 0.02, exposure: 1.02,
  },
  violetRim: {
    az: -110, el: 26,
    lit: [1.35, 0.80, 1.85], shade: [0.38, 0.24, 0.58], lift: [0.05, 0.02, 0.09], lambert: 0.42, sideK: 0.86, term: 0.24,
    charTint: [1.0, 0.92, 1.05], charShade: 0.85, charGrad: 0.10, bodyGrad: 0.24, sideTint: [0.94, 0.86, 1.05],
    blob: [0.36, 0.28, 0.48], actorShadow: true,
    fog: "#1c1030", fogNear: 6, fogFar: 46,
    sunCol: "#c07aff", sunI: 2.4, sky: "#241640", ground: "#140b26", hemiI: 0.5,
    bias: -0.0004, normalBias: 0.02, exposure: 1.06,
  },
  heartbeat: {
    az: -120, el: 28,
    lit: [2.0, 0.80, 0.90], shade: [0.50, 0.26, 0.34], lift: [0.09, 0.03, 0.05], lambert: 0.40, sideK: 0.86, term: 0.22,
    charTint: [1.06, 0.92, 0.92], charShade: 0.87, charGrad: 0.09, bodyGrad: 0.22, sideTint: [0.98, 0.86, 0.90],
    blob: [0.48, 0.30, 0.34], actorShadow: true,
    fog: "#2a1018", fogNear: 6, fogFar: 46,
    sunCol: "#ff6a8a", sunI: 2.6, sky: "#381622", ground: "#1e0c12", hemiI: 0.52,
    bias: -0.0004, normalBias: 0.02, exposure: 1.02,
  },
  goldWarm: {
    az: -125, el: 40,
    lit: [1.60, 1.42, 1.02], shade: [0.42, 0.36, 0.28], lift: [0.07, 0.06, 0.03], lambert: 0.36, sideK: 0.88, term: 0.18,
    charTint: [1.04, 0.98, 0.90], charShade: 0.88, charGrad: 0.07, bodyGrad: 0.19, sideTint: [0.98, 0.94, 0.86],
    blob: [0.50, 0.46, 0.40], actorShadow: true,
    fog: "#2e2618", fogNear: 7, fogFar: 52,
    sunCol: "#ffe2a8", sunI: 2.7, sky: "#3a3020", ground: "#241c10", hemiI: 0.55,
    bias: -0.0004, normalBias: 0.02, exposure: 1.03,
  },
  roseGold: {
    az: -115, el: 44,
    lit: [1.62, 1.30, 1.02], shade: [0.46, 0.36, 0.34], lift: [0.07, 0.05, 0.05], lambert: 0.34, sideK: 0.88, term: 0.18,
    charTint: [1.05, 0.98, 0.94], charShade: 0.89, charGrad: 0.06, bodyGrad: 0.18, sideTint: [0.99, 0.94, 0.92],
    blob: [0.52, 0.46, 0.44], actorShadow: true,
    fog: "#33241f", fogNear: 8, fogFar: 56,
    sunCol: "#ffd2b0", sunI: 2.8, sky: "#40302a", ground: "#281c18", hemiI: 0.58,
    bias: -0.0004, normalBias: 0.02, exposure: 1.05,
  },
  neon: {
    az: -105, el: 32,
    lit: [0.70, 1.35, 1.55], shade: [0.22, 0.34, 0.50], lift: [0.03, 0.08, 0.10], lambert: 0.40, sideK: 0.86, term: 0.22,
    charTint: [0.94, 1.02, 1.06], charShade: 0.87, charGrad: 0.10, bodyGrad: 0.24, sideTint: [0.86, 0.96, 1.05],
    blob: [0.34, 0.44, 0.52], actorShadow: true,
    fog: "#101a30", fogNear: 6, fogFar: 46,
    sunCol: "#5ae0ff", sunI: 2.5, sky: "#14244a", ground: "#0a1224", hemiI: 0.52,
    bias: -0.0004, normalBias: 0.02, exposure: 1.1,
  },
};

export const LOOK: Record<LightName, WorldLook> = {
  amberCyan: { sky: { c: ["#3a3450", "#2c2740", "#1e1a30", "#141126", "#0c0a1c"], e: [0, 5, 15, 30, 60] }, bounce: [0.04, 0.03, 0.02], sat: 1.08 },
  rainy:     { sky: { c: ["#1a2a4a", "#16223f", "#101a30", "#0a1224", "#060a16"], e: [0, 5, 15, 30, 60] }, bounce: [0.03, 0.04, 0.08], sat: 1.10 },
  emergency: { sky: { c: ["#3a1a16", "#2a1210", "#1c0c0a", "#120806", "#0a0404"], e: [0, 5, 15, 30, 60] }, bounce: [0.09, 0.03, 0.02], sat: 1.12 },
  violetRim: { sky: { c: ["#241640", "#1c1030", "#140a26", "#0c0618", "#060310"], e: [0, 5, 15, 30, 60] }, bounce: [0.05, 0.02, 0.10], sat: 1.12 },
  heartbeat: { sky: { c: ["#381622", "#2a1018", "#1e0c12", "#140810", "#0a0408"], e: [0, 5, 15, 30, 60] }, bounce: [0.10, 0.03, 0.05], sat: 1.12 },
  goldWarm:  { sky: { c: ["#3a3020", "#2e2618", "#241c10", "#181208", "#0e0a04"], e: [0, 5, 15, 30, 60] }, bounce: [0.07, 0.05, 0.02], sat: 1.08 },
  roseGold:  { sky: { c: ["#40302a", "#33241f", "#281c18", "#1c1210", "#100a08"], e: [0, 5, 15, 30, 60] }, bounce: [0.07, 0.05, 0.04], sat: 1.06 },
  neon:      { sky: { c: ["#14244a", "#101a30", "#0a1224", "#060c1a", "#040810"], e: [0, 5, 15, 30, 60] }, bounce: [0.02, 0.08, 0.10], sat: 1.14 },
};
