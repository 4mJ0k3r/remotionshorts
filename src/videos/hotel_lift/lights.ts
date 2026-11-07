// Lighting presets for HotelLiftShort:
// Shot 1 & 3: "day" (bright historic Chicago morning/midday sky, wooden plank streets, red brick Tremont hotel).
// Shot 2: "trench" (warm timber shoring gallery with lantern glow and warm shadows).
import { LightName as _LN } from "./lights"; // self-reference safe type
type C3 = [number, number, number];

export type LightName = "day" | "trench";
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
  day: {
    az: -135, el: 50,
    lit: [1.60, 1.52, 1.38], shade: [0.44, 0.46, 0.58], lift: [0.05, 0.05, 0.07], lambert: 0.32, sideK: 0.86, term: 0.16,
    charTint: [1.0, 0.98, 0.95], charShade: 0.88, charGrad: 0.06, bodyGrad: 0.18, sideTint: [0.90, 0.90, 0.98],
    blob: [0.5, 0.52, 0.5], actorShadow: true,
    fog: "#d4e6f4", fogNear: 40, fogFar: 280,
    sunCol: "#fff5e4", sunI: 3.0, sky: "#d6ecfa", ground: "#8a7b68", hemiI: 0.6,
    bias: -0.0004, normalBias: 0.02, exposure: 1.0,
  },
  trench: {
    az: -110, el: 38,
    lit: [1.70, 1.45, 1.15], shade: [0.50, 0.42, 0.38], lift: [0.08, 0.06, 0.05], lambert: 0.40, sideK: 0.88, term: 0.20,
    charTint: [1.02, 0.96, 0.90], charShade: 0.85, charGrad: 0.08, bodyGrad: 0.22, sideTint: [0.92, 0.85, 0.80],
    blob: [0.45, 0.42, 0.4], actorShadow: true,
    fog: "#2b221a", fogNear: 15, fogFar: 75,
    sunCol: "#ffddaa", sunI: 2.8, sky: "#523c28", ground: "#38291a", hemiI: 0.5,
    bias: -0.0004, normalBias: 0.02, exposure: 1.05,
  },
};

export const LOOK: Record<LightName, WorldLook> = {
  day: {
    sky: { c: ["#eef6fc", "#cae5f9", "#94cbf4", "#5aaef0", "#308ad8"], e: [0, 4, 12, 25, 55] },
    bounce: [0.03, 0.025, 0.01], sat: 1.05,
  },
  trench: {
    sky: { c: ["#3d2e22", "#302319", "#241a12", "#18110b", "#0d0906"], e: [0, 5, 15, 30, 60] },
    bounce: [0.05, 0.03, 0.01], sat: 1.10,
  },
};
