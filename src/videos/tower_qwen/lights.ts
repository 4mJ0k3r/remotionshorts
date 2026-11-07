// Light presets for "Tower Qwen": `day` = bright midday over the Thames (the wide bridge shots), `cab` = the bus
// driver's cutaway cab, sunlit through the windscreen. Same contract as the rest of the house engine: the key light
// is CAMERA-RELATIVE and frozen per shot (az = degrees from the shot's mean forward axis, +90 = screen right,
// 180 = behind the lens, 0 = straight ahead; el = elevation), and lit/shade/lift are LINEAR multipliers for shade.ts.
import { Light } from "./story";
type C3 = [number, number, number];
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

export const LIGHTS: Record<Light, LightPreset> = {
  // high summer sun off the camera's left shoulder, cool blue-violet shade, crisp shadows on the stone
  day: {
    az: -136, el: 52,
    lit: [1.58, 1.50, 1.32], shade: [0.40, 0.44, 0.60], lift: [0.05, 0.05, 0.07], lambert: 0.32, sideK: 0.86, term: 0.16,
    charTint: [1.0, 0.98, 0.95], charShade: 0.88, charGrad: 0.06, bodyGrad: 0.18, sideTint: [0.9, 0.9, 0.98],
    blob: [0.46, 0.5, 0.56], actorShadow: true,
    fog: "#cfe4f4", fogNear: 60, fogFar: 460,
    sunCol: "#fff2dc", sunI: 3.0, sky: "#dcecff", ground: "#54788c", hemiI: 0.62,
    bias: -0.0004, normalBias: 0.02, exposure: 1.0,
  },
  // interior: the same daylight coming in over the dash, but bounced warm off the red-brass cab and hemi-heavy
  cab: {
    az: -150, el: 34,
    lit: [1.46, 1.38, 1.22], shade: [0.52, 0.46, 0.46], lift: [0.09, 0.07, 0.06], lambert: 0.38, sideK: 0.78, term: 0.2,
    charTint: [1.0, 0.97, 0.9], charShade: 0.9, charGrad: 0.05, bodyGrad: 0.16, sideTint: [0.96, 0.9, 0.86],
    blob: [0.44, 0.4, 0.38], actorShadow: true,
    fog: "#d9cdb8", fogNear: 14, fogFar: 130,
    sunCol: "#fff4e2", sunI: 2.5, sky: "#eae4d8", ground: "#6a5a48", hemiI: 0.9,
    bias: -0.0005, normalBias: 0.012, exposure: 1.04,
  },
};

export const LOOK: Record<Light, WorldLook> = {
  day: {
    sky: { c: ["#dceeff", "#b8ddf7", "#8cc8f0", "#63b0e8", "#409ade"], e: [0, 3, 9, 20, 50] },
    bounce: [0.03, 0.03, 0.01], sat: 1.06,
  },
  cab: {
    sky: { c: ["#eef2f4", "#d6e4f0", "#b8d2e8", "#9cc2e2", "#82b2dc"], e: [0, 3, 9, 20, 50] },
    bounce: [0.06, 0.04, 0.02], sat: 1.02,
  },
};
