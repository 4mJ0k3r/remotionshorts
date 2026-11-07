// Single source of truth for MolassesTankShort time, shots, camera paths, kicks, and DOF tracking.
// Pure math only — no Three.js meshes.
export const FPS = 30;
export const TOTAL = 300;

export type ShotDef = {
  id: number;
  a: number; // inclusive start frame
  b: number; // exclusive end frame
  light: "boston_day" | "cab_warm";
  desc: string;
};

export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 95, light: "boston_day", desc: "50-foot steel tank filled with two million gallons of molasses bulges and rivets pop" },
  { id: 2, a: 95, b: 195, light: "cab_warm", desc: "Conductor in streetcar cab slams emergency brake lever" },
  { id: 3, a: 195, b: 300, light: "boston_day", desc: "35 mph syrup wave knocks elevated train off its tracks" },
];

export const shotAt = (f: number): ShotDef => {
  for (const s of SHOTS) {
    if (f >= s.a && f < s.b) return s;
  }
  return SHOTS[SHOTS.length - 1];
};

export const layersAt = (f: number): { id: number; alpha: number }[] => {
  const s = shotAt(f);
  return [{ id: s.id, alpha: 1.0 }];
};

// Math helpers
export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/** Smooth Hermite S-curve glide */
export const glide = (f: number, a: number, b: number) => {
  const t = clamp01((f - a) / Math.max(1, b - a));
  return t * t * (3 - 2 * t);
};

export const lerp = (v0: number, v1: number, t: number) => v0 + (v1 - v0) * t;

export const v3Lerp = (
  p0: [number, number, number],
  p1: [number, number, number],
  t: number
): [number, number, number] => [
  lerp(p0[0], p1[0], t),
  lerp(p0[1], p1[1], t),
  lerp(p0[2], p1[2], t),
];

/** Subtle continuous drift forward so held frames = 0% */
export const pushK = (f: number, a: number, b: number, dist = 0.05) => {
  const t = clamp01((f - a) / Math.max(1, b - a));
  return t * dist;
};

// ---------------- KICKS (Impact camera shakes) ----------------
export type Kick = { f: number; dur: number; amp: number; freq: number };
export const KICKS: Kick[] = [
  { f: 22, dur: 12, amp: 0.08, freq: 1.8 },   // Tank belly bulges & rivets pop
  { f: 142, dur: 10, amp: 0.07, freq: 2.2 },  // Conductor slams emergency brake lever
  { f: 235, dur: 14, amp: 0.09, freq: 1.6 },  // Syrup wave impacts elevated train trestle
];

export const kickOffset = (f: number): [number, number, number] => {
  let ox = 0, oy = 0, oz = 0;
  for (const k of KICKS) {
    if (f >= k.f && f < k.f + k.dur) {
      const u = (f - k.f) / k.dur;
      const decay = (1 - u) * (1 - u);
      const s = Math.sin((f - k.f) * k.freq) * k.amp * decay;
      ox += s * 0.4;
      oy += s * 1.0;
      oz += s * 0.3;
    }
  }
  return [ox, oy, oz];
};

// ---------------- CAMERAS ----------------
export type CamState = {
  pos: [number, number, number];
  look: [number, number, number];
  fov: number;
};

/**
 * Camera paths for each shot.
 * All shots begin motion on frame shot.a (0, 95, 195) with no stationary wait,
 * smoothly transitioning to pushK drift so held frames <= 2%.
 * fov is strictly 42° to 50°.
 */
export const camAt = (id: number, f: number): CamState => {
  const [kx, ky, kz] = kickOffset(f);

  if (id === 1) {
    // Shot 1 (f = 0..94):
    // Starts in medium framing Inspector on right boardwalk & steel tank base.
    // Continuous crane-out and wide pull back (f = 0..75) into wide view
    // showing entire 50-ft cylindrical tank with PURITY DISTILLING banner inside 12%..88% with sky margins.
    // Followed by gentle push drift f = 75..94.
    const t = glide(f, 0, 75);
    const drift = pushK(f, 75, 94, 0.25);

    const posA: [number, number, number] = [0.8, 1.65, 7.6];
    const lookA: [number, number, number] = [0.8, 1.28, 3.5];
    const fovA = 46;

    const posB: [number, number, number] = [0.0, 3.8, 22.0];
    const lookB: [number, number, number] = [0.0, 4.3, 0.0];
    const fovB = 50;

    const basePos = v3Lerp(posA, posB, t);
    const baseLook = v3Lerp(lookA, lookB, t);
    const fov = lerp(fovA, fovB, t);

    basePos[2] -= drift;
    baseLook[2] -= drift;

    return {
      pos: [basePos[0] + kx, basePos[1] + ky, basePos[2] + kz],
      look: [baseLook[0], baseLook[1], baseLook[2]],
      fov,
    };
  }

  if (id === 2) {
    // Shot 2 (f = 95..194):
    // Streetcar cab platform looking out at DANGER warning sign on upper left,
    // Conductor on right, and emergency brake lever in center.
    // Continuous push-in starting from f = 95.
    const t = glide(f, 95, 165);
    const drift = pushK(f, 165, 194, 0.10);

    const posA: [number, number, number] = [-0.05, 1.25, 5.2];
    const lookA: [number, number, number] = [-0.05, 1.10, 0.8];
    const fovA = 46;

    const posB: [number, number, number] = [-0.05, 1.20, 4.6];
    const lookB: [number, number, number] = [-0.05, 1.08, 0.8];
    const fovB = 45;

    const basePos = v3Lerp(posA, posB, t);
    const baseLook = v3Lerp(lookA, lookB, t);
    const fov = lerp(fovA, fovB, t);

    basePos[2] -= drift;
    baseLook[2] -= drift;

    return {
      pos: [basePos[0] + kx, basePos[1] + ky, basePos[2] + kz],
      look: [baseLook[0], baseLook[1], baseLook[2]],
      fov,
    };
  }

  // Shot 3 (f = 195..299):
  // Boardwalk Plaza with easel on left, Conductor on right holding card,
  // and elevated train trestle bridge + wave surge filling upper frame behind them.
  // Continuous smooth push-in starting immediately at f = 195.
  const t = glide(f, 195, 265);
  const drift = pushK(f, 265, 299, 0.12);

  const posA: [number, number, number] = [-0.05, 1.60, 9.5];
  const lookA: [number, number, number] = [-0.05, 1.48, 1.8];
  const fovA = 47;

  const posB: [number, number, number] = [-0.05, 1.55, 8.0];
  const lookB: [number, number, number] = [-0.05, 1.48, 1.8];
  const fovB = 46;

  const basePos = v3Lerp(posA, posB, t);
  const baseLook = v3Lerp(lookA, lookB, t);
  const fov = lerp(fovA, fovB, t);

  basePos[2] -= drift;
  baseLook[2] -= drift;

  return {
    pos: [basePos[0] + kx, basePos[1] + ky, basePos[2] + kz],
    look: [baseLook[0], baseLook[1], baseLook[2]],
    fov,
  };
};

// ---------------- DYNAMIC DOF FOCUS TRACKING ----------------
export type DofSpec = {
  focus: (f: number) => [number, number, number];
  cInf: number;
};

export const dofAt = (f: number): DofSpec => {
  const s = shotAt(f);
  if (s.id === 1) {
    const t = glide(f, 0, 75);
    return {
      focus: () => [
        lerp(1.2, 0.0, t),
        lerp(1.6, 4.3, t),
        lerp(3.8, 0.0, t),
      ],
      cInf: 10,
    };
  }
  if (s.id === 2) {
    return {
      focus: () => [0.1, 1.05, 0.8],
      cInf: 10,
    };
  }
  // Shot 3:
  // Starts with focus on background elevated train at z ~ -4.0, racks smoothly to foreground Conductor & easel (z ~ 2.0) by f = 225
  const t = glide(f, 195, 225);
  return {
    focus: () => [
      lerp(0.0, -0.1, t),
      lerp(4.0, 1.35, t),
      lerp(-4.0, 2.0, t),
    ],
    cInf: 7.0, // Crisp thin-lens DOF
  };
};
