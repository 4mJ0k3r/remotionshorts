// Light presets for InstantSkillShort. Eight looks, one per set. v2 art direction: the film is a NIGHT film, not a
// magic-hour film — the city exteriors are twilight violet with the light coming from lit windows and practical
// lamps, and the three interiors are graded down so no shot sits at daylight luma. short_qa measures the per-shot
// luma mean and saturation; the target band is 0.38..0.62 luma with saturation >= 0.28. The shade-side colours are
// therefore chromatic (violet outdoors, umber indoors) rather than the near-neutral greys v1 used, which is what
// keeps saturation up while the overall level drops.
// The two bright exteriors (snow, asphalt) sit at the TOP of the same band on purpose: they are the only daylight in
// the film, and both are the "body protests" gags, so they read as a different world from the twilight city.
// The key light is CAMERA-RELATIVE and frozen per shot (world.ts shotSun()): az = degrees from the shot's forward
// axis (+90 = screen right, 180 = behind the lens), el = elevation. lit/shade/lift are LINEAR multipliers consumed by
// shade.ts, charTint/charGrad/bodyGrad/sideTint by cardshade.ts. LOOK.sky colours go through untone(), so the hex is
// approximately the on-screen value before the grade curve.
// story.ts owns the LightName union: a new set that needs its own look has to be added there first, and TypeScript
// then points at whichever of LIGHTS or LOOK is still missing it.
import type { LightName } from "./story";
export type { LightName };

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

export const LIGHTS: Record<LightName, LightPreset> = {
  // CITY SKATEPARK AT TWILIGHT: the sun has almost set, so what rakes the concrete is a low ember key and the
  // ambient IS the violet sky (hemi.sky is purple, not cream). Shade sides fall to violet-blue; the frame's luma is
  // carried by the apartment windows, the streetlamp pools and the ember horizon, not by the sun.
  dusk: {
    az: -128, el: 21,
    lit: [1.26, 1.1, 1.0], shade: [0.4, 0.36, 0.56], lift: [0.085, 0.075, 0.115],
    lambert: 0.34, sideK: 0.82, term: 0.18,
    charTint: [0.96, 0.95, 1.02], charShade: 0.8, charGrad: 0.09, bodyGrad: 0.22, sideTint: [0.86, 0.84, 1.0],
    blob: [0.38, 0.36, 0.46], actorShadow: true,
    fog: "#584677", fogNear: 38, fogFar: 185,
    sunCol: "#ffc892", sunI: 2.3, sky: "#8570b8", ground: "#3a2c46", hemiI: 0.68,
    bias: -0.0004, normalBias: 0.02, exposure: 0.97,
  },

  // CHESS TOURNAMENT HALL: after-hours. One pendant over the table plus a narrow lit window band on the back wall,
  // so most of the plaster is shade-side umber. lit drops ~15% from v1 and the hemi is halved; the green rug and the
  // cream head cards still carry the mid-tones.
  hall: {
    az: -96, el: 40,
    lit: [1.42, 1.3, 1.1], shade: [0.5, 0.45, 0.42], lift: [0.1, 0.09, 0.085],
    lambert: 0.36, sideK: 0.82, term: 0.18,
    charTint: [1.0, 0.98, 0.94], charShade: 0.84, charGrad: 0.07, bodyGrad: 0.2, sideTint: [0.93, 0.89, 0.85],
    blob: [0.44, 0.4, 0.36], actorShadow: true,
    fog: "#c0a987", fogNear: 26, fogFar: 130,
    sunCol: "#ffe4b8", sunI: 2.05, sky: "#d3ba95", ground: "#5f4c3a", hemiI: 0.6,
    bias: -0.0004, normalBias: 0.02, exposure: 0.99,
  },

  // NIGHT CABIN: the windows are a deep blue-black and the only warm source is the aisle strip, so this is the
  // coolest preset in the film. A raised lift keeps the seat fabric from crushing under the ink lines.
  cabin: {
    az: -132, el: 48,
    lit: [1.32, 1.33, 1.4], shade: [0.5, 0.52, 0.6], lift: [0.1, 0.11, 0.13],
    lambert: 0.38, sideK: 0.8, term: 0.2,
    charTint: [0.98, 0.99, 1.02], charShade: 0.83, charGrad: 0.06, bodyGrad: 0.18, sideTint: [0.88, 0.9, 0.96],
    blob: [0.42, 0.44, 0.5], actorShadow: true,
    fog: "#2b3350", fogNear: 22, fogFar: 120,
    sunCol: "#cfe0ff", sunI: 1.95, sky: "#9caed4", ground: "#454558", hemiI: 0.62,
    bias: -0.0004, normalBias: 0.02, exposure: 1.01,
  },

  // HIGH-ROLLER POKER LOUNGE: the most deliberate set — one shade over the felt, gold cove light on the back wall,
  // everything else umber. The felt is mid-green so the floor still reads when the walls go dark.
  lounge: {
    az: -104, el: 36,
    lit: [1.44, 1.28, 1.0], shade: [0.46, 0.41, 0.38], lift: [0.1, 0.085, 0.07],
    lambert: 0.36, sideK: 0.84, term: 0.18,
    charTint: [1.02, 0.98, 0.9], charShade: 0.85, charGrad: 0.07, bodyGrad: 0.2, sideTint: [0.94, 0.88, 0.78],
    blob: [0.42, 0.38, 0.32], actorShadow: true,
    fog: "#2f2418", fogNear: 26, fogFar: 145,
    sunCol: "#ffd493", sunI: 2.2, sky: "#ab885c", ground: "#463522", hemiI: 0.58,
    bias: -0.0004, normalBias: 0.02, exposure: 1.02,
  },

  // ALPINE SNOWBAWL AT HIGH NOON: the only preset in the film whose ambient comes from BELOW — the ground hemi is a
  // bright blue-white because a snowfield bounces almost as much light as the sky gives it, and that bounce is what
  // fills the shadows under his chin. Snow shade is blue, never grey, which is the whole trick to keeping
  // saturation up on a set that is otherwise white. exposure is pulled to 0.88 so the frame lands at the TOP of the
  // 0.38..0.62 luma band instead of blowing through it.
  snow: {
    az: -150, el: 56,
    lit: [1.3, 1.31, 1.34], shade: [0.66, 0.72, 0.88], lift: [0.13, 0.145, 0.17],
    lambert: 0.36, sideK: 0.8, term: 0.2,
    charTint: [1.0, 1.0, 1.03], charShade: 0.86, charGrad: 0.06, bodyGrad: 0.18, sideTint: [0.88, 0.92, 1.0],
    blob: [0.5, 0.52, 0.58], actorShadow: true,
    fog: "#c8d8ef", fogNear: 26, fogFar: 130,
    sunCol: "#fff6e6", sunI: 2.6, sky: "#bcd2f0", ground: "#d6e2f2", hemiI: 0.85,
    bias: -0.0004, normalBias: 0.02, exposure: 0.88,
  },

  // OPEN-ROAD ASPHALT, LAST HOUR: a low sun rakes the tarmac from screen-left so the guardrails throw long shadows
  // and the road plane itself carries the motion. lit is warm, shade keeps a violet cast so the asphalt never reads
  // neutral grey; the grade is "vivid", which spends the colour budget on the orange band at the horizon.
  asphalt: {
    az: -95, el: 18,
    lit: [1.34, 1.16, 0.92], shade: [0.48, 0.46, 0.58], lift: [0.11, 0.09, 0.08],
    lambert: 0.34, sideK: 0.86, term: 0.16,
    charTint: [1.02, 0.98, 0.92], charShade: 0.85, charGrad: 0.08, bodyGrad: 0.2, sideTint: [0.95, 0.9, 0.84],
    blob: [0.46, 0.42, 0.4], actorShadow: true,
    fog: "#d99b6a", fogNear: 45, fogFar: 220,
    sunCol: "#ffd08a", sunI: 2.8, sky: "#8fa8c8", ground: "#6b533c", hemiI: 0.6,
    bias: -0.0004, normalBias: 0.02, exposure: 0.92,
  },

  // NEON BRAIN CHAMBER: a windowless room, so there is no sun in the physical sense — the directional is only there
  // to give the cards a lit side. The real key is the emissive core (build.ts) and the bounce is a cold cyan from
  // every wall at once, which is why lambert is the highest in the film and the lift is blue-grey and strong.
  mind: {
    az: -60, el: 62,
    lit: [1.16, 1.24, 1.3], shade: [0.44, 0.5, 0.62], lift: [0.14, 0.16, 0.19],
    lambert: 0.42, sideK: 0.7, term: 0.24,
    charTint: [0.98, 1.0, 1.05], charShade: 0.88, charGrad: 0.05, bodyGrad: 0.14, sideTint: [0.82, 0.94, 1.0],
    blob: [0.36, 0.4, 0.46], actorShadow: true,
    fog: "#1b2a3a", fogNear: 14, fogFar: 60,
    sunCol: "#cfeaff", sunI: 1.7, sky: "#6f9fc4", ground: "#232c38", hemiI: 0.72,
    bias: -0.0004, normalBias: 0.02, exposure: 1.0,
  },

  // SUBURBAN STREET AT 02:14: one sodium lamp is the sun, so the lit side goes deep orange and the shade side goes
  // blue-black — the largest lit/shade colour split in the film, which is what makes the beam's cyan arrival read
  // as foreign. hemi is the lowest value here (the sky gives nothing back at night), so exposure sits above 1 to
  // hold the luma floor without lifting the blacks.
  night: {
    az: -120, el: 30,
    lit: [1.42, 1.18, 0.86], shade: [0.34, 0.38, 0.58], lift: [0.09, 0.1, 0.14],
    lambert: 0.32, sideK: 0.88, term: 0.14,
    charTint: [1.0, 0.97, 0.95], charShade: 0.8, charGrad: 0.1, bodyGrad: 0.24, sideTint: [0.84, 0.86, 1.0],
    blob: [0.34, 0.34, 0.42], actorShadow: true,
    fog: "#141b30", fogNear: 20, fogFar: 110,
    sunCol: "#ffc873", sunI: 2.4, sky: "#4a5578", ground: "#1e2233", hemiI: 0.5,
    bias: -0.0004, normalBias: 0.02, exposure: 1.05,
  },
};

export const LOOK: Record<LightName, WorldLook> = {
  dusk: {
    // ember at the waterline of the skyline, then straight into violet: the sky is the film's colour identity and
    // the band the buildings punch through is the saturated rose, not v1's pale cream.
    // cal_v2 measurement: shot 3 looks up into the zenith and the frame landed at luma .307, under the .38 floor,
    // because the top two stops were near-black violet (corner .129). The zenith stops are now chromatic violets
    // that keep the hue identity at ~3x the luma, and the breakpoints push them up so the whole upper cone is lit
    // sky rather than a dark cap.
    sky: { c: ["#f2a868", "#d4788f", "#a865b0", "#8457b3", "#6a44a0"], e: [0, 2.5, 9, 22, 48] },
    bounce: [0.035, 0.025, 0.045], sat: 1.16,
  },
  hall: {
    sky: { c: ["#f2d9ae", "#dcb887", "#b8905f", "#8a6844", "#5c4530"], e: [0, 3, 10, 22, 48] },
    bounce: [0.05, 0.04, 0.028], sat: 1.1,
  },
  cabin: {
    // what the oval windows show: night sky, brighter toward the zenith, no sun.
    sky: { c: ["#16203f", "#1b2748", "#223057", "#2a3a68", "#39477a"], e: [0, 4, 12, 26, 48] },
    bounce: [0.04, 0.04, 0.05], sat: 1.08,
  },
  lounge: {
    sky: { c: ["#5c452c", "#48351f", "#34251a", "#241812", "#170f0b"], e: [0, 4, 12, 26, 52] },
    bounce: [0.055, 0.038, 0.018], sat: 1.14,
  },
  snow: {
    // a snowfield has no horizon line of its own: the range IS the skyline, so the band above it goes from a pale
    // cyan at the ridge to a real blue at the zenith. Bounce is the brightest in the film.
    sky: { c: ["#dfe9f5", "#cfe0f2", "#bcd2ea", "#a8c2e2", "#96b3da"], e: [0, 3, 10, 24, 48] },
    bounce: [0.06, 0.065, 0.075], sat: 1.05,
  },
  asphalt: {
    // the last hour burns out at the waterline and cools fast overhead, which is the same rose-to-violet ramp the
    // twilight city uses, pushed further into orange because there is nothing between here and the horizon.
    sky: { c: ["#f4a86a", "#e2886f", "#b77a90", "#8b6a9a", "#5f4a72"], e: [0, 2, 8, 20, 44] },
    bounce: [0.05, 0.038, 0.03], sat: 1.2,
  },
  mind: {
    // no windows: this "sky" is only the dome colour the hemisphere light reads, so it is the room's own cold glow
    // and it is deliberately dark — every luma and saturation point in shots 14-16 is spent on the emissive core.
    sky: { c: ["#243545", "#2a3f52", "#1e2d3c", "#16202c", "#101820"], e: [0, 4, 12, 26, 48] },
    bounce: [0.03, 0.045, 0.055], sat: 1.12,
  },
  night: {
    // light-polluted suburban night: a sodium-ember band where the lamp glows into the haze, then straight down
    // into blue-black. The top stops are chromatic, not neutral, or the night shots lose the saturation floor.
    sky: { c: ["#3d3a52", "#2a2c46", "#1e2338", "#171b2c", "#121522"], e: [0, 3, 10, 24, 48] },
    bounce: [0.04, 0.035, 0.05], sat: 1.1,
  },
};
