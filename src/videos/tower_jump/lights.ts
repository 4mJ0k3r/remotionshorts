// Light preset for "Coaster": one bright midday outdoor look. Same contract as the school engine: the key light is
// CAMERA-RELATIVE and frozen per shot (az = degrees from the shot's forward axis, +90 = screen right, 180 = behind
// the lens; el = elevation), lit/shade/lift are LINEAR multipliers for shade.ts.
type C3 = [number, number, number];
export type LightName = "sunny";
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
  // warm sun from over the camera's left shoulder, cool blue-violet shade, crisp cast shadows
  sunny: {
    az: -138, el: 48,
    lit: [1.62, 1.54, 1.36], shade: [0.42, 0.44, 0.58], lift: [0.05, 0.05, 0.07], lambert: 0.32, sideK: 0.86, term: 0.16,
    charTint: [1.0, 0.98, 0.95], charShade: 0.88, charGrad: 0.06, bodyGrad: 0.18, sideTint: [0.9, 0.9, 0.98],
    blob: [0.5, 0.52, 0.5], actorShadow: true,
    fog: "#cfe4f4", fogNear: 70, fogFar: 520,
    sunCol: "#fff2dc", sunI: 3.0, sky: "#dcecff", ground: "#8fae68", hemiI: 0.6,
    bias: -0.0004, normalBias: 0.02, exposure: 1.0,
  },
};

export const LOOK: Record<LightName, WorldLook> = {
  sunny: {
    sky: { c: ["#d6ecfa", "#a9d6f6", "#74baf0", "#4f9fe8", "#2f84dc"], e: [0, 3, 9, 20, 50] },
    bounce: [0.02, 0.02, 0.0], sat: 1.06,
  },
};
