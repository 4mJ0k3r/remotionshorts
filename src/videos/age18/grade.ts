// Colour grade for the bridge short (post agent): references/grade/GradeEffect.ts (reports/grade.md) verbatim,
// plus GRADES / GRADE_STRENGTH / gradeFor() so the lead can re-fit the presets after the lighting merge.
// The presets were fitted to the OLD unlit stills: after the WORLD lighting lands they will over-correct; re-fit
// (grade.md 5.C) or lower GRADE_STRENGTH. Each Inner (crossfade layer) grades with its own shot's light, so the DOM
// crossfade at XFADE frames (shots 10->11, 13->14) cross-fades the presets as well.
// GradeEffect: the fitted reference-style colour grade as a postprocessing 6.37 Effect.
// Put it LAST in the EffectComposer, after ToneMappingEffect. It works on display-referred values: the input (linear,
// already tone-mapped to 0..1) is encoded to sRGB, graded exactly like scripts/grade.py (validated on our stills), and
// decoded back to linear for the composer's output encoding.
//   1. RGB tone curve: monotone cubic Hermite through 7 knots at x = 0, .1, .25, .5, .75, .9, 1
//   2. saturation around luma Y' (Rec.709 weights on the encoded values), separately for shadows / mids / highlights
//   3. 3-way tint (split tone): zero-luma RGB offsets in shadows, mids, highlights
//   4. vignette: x (1 - k * smoothstep(r0, 1, r)), r = elliptical radius, corners = 1
// `amount` blends the whole grade (0 = bypass) so it can be dialled back once lighting/albedo work brightens the render.
import { Effect, BlendFunction } from "postprocessing";
import { Uniform, Vector3, Vector2 } from "three";

const frag = /* glsl */ `
uniform float gradeKy[7];
uniform float gradeKm[7];
uniform vec3 gradeSat;      // x = shadows, y = mids, z = highlights
uniform vec3 gradeTintS;    // zero-luma RGB offsets (sRGB-encoded units)
uniform vec3 gradeTintM;
uniform vec3 gradeTintH;
uniform vec3 gradeToe;      // warm plum lift for the darkest pixels (sRGB-encoded units)
uniform float gradeSatCap;  // HSV-saturation ceiling: above it chroma is compressed (top decile of sat_p90)
uniform float gradeSatKnee; // how much of the over-cap chroma survives (1 = untouched); low = thin the tail only
uniform vec2 gradeVig;      // x = strength k, y = start radius r0
uniform float gradeAmount;

vec3 gradeEncode(vec3 c) {   // linear -> sRGB
  c = clamp(c, 0.0, 1.0);
  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(vec3(0.0031308), c));
}
vec3 gradeDecode(vec3 c) {   // sRGB -> linear
  return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(vec3(0.04045), c));
}
float gradeHermite(float v, float x0, float x1, float y0, float y1, float m0, float m1) {
  float h = x1 - x0, t = (v - x0) / h, t2 = t * t, t3 = t2 * t;
  return (2.0 * t3 - 3.0 * t2 + 1.0) * y0 + (t3 - 2.0 * t2 + t) * h * m0 + (-2.0 * t3 + 3.0 * t2) * y1 + (t3 - t2) * h * m1;
}
float gradeCurve(float v) {
  v = clamp(v, 0.0, 1.0);
  if (v < 0.1)  return gradeHermite(v, 0.0, 0.1, gradeKy[0], gradeKy[1], gradeKm[0], gradeKm[1]);
  if (v < 0.25) return gradeHermite(v, 0.1, 0.25, gradeKy[1], gradeKy[2], gradeKm[1], gradeKm[2]);
  if (v < 0.5)  return gradeHermite(v, 0.25, 0.5, gradeKy[2], gradeKy[3], gradeKm[2], gradeKm[3]);
  if (v < 0.75) return gradeHermite(v, 0.5, 0.75, gradeKy[3], gradeKy[4], gradeKm[3], gradeKm[4]);
  if (v < 0.9)  return gradeHermite(v, 0.75, 0.9, gradeKy[4], gradeKy[5], gradeKm[4], gradeKm[5]);
  return gradeHermite(v, 0.9, 1.0, gradeKy[5], gradeKy[6], gradeKm[5], gradeKm[6]);
}

void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
  vec3 src = gradeEncode(inputColor.rgb);
  vec3 c = vec3(gradeCurve(src.r), gradeCurve(src.g), gradeCurve(src.b));
  const vec3 W = vec3(0.2126, 0.7152, 0.0722);
  float y = dot(c, W);
  float wS = 1.0 - smoothstep(0.0, 0.55, y);
  float wH = smoothstep(0.45, 1.0, y);
  float wM = 1.0 - wS - wH;
  float s = gradeSat.y + (gradeSat.x - gradeSat.y) * wS + (gradeSat.z - gradeSat.y) * wH;
  c = vec3(y) + s * (c - vec3(y));
  c += wS * gradeTintS + wM * gradeTintM + wH * gradeTintH;
  // lift only the toe: warm plum darks, zero effect by y = 0.18
  c += (1.0 - smoothstep(0.0, 0.18, y)) * gradeToe;
  // saturation ceiling: the reference keeps its most saturated decile at ~.67-.74 HSV; ours ran .85-.95
  // (teal water, green coats). Compress only above the cap, so mid-tones keep the 3-zone punch.
  // Scaling chroma around luma does NOT give ratio sp for bright pixels (mx' shrinks), so solve the scale
  // r that makes (mx'-mn')/mx' exactly sp: r = sp*y2 / ((mx-mn) - sp*(mx-y2)).
  {
    float mx = max(c.r, max(c.g, c.b)), mn = min(c.r, min(c.g, c.b));
    // smx is NOT clamped to 1: a 1.7x mid boost can drive a channel below zero and (mx-mn)/mx then exceeds 1.
    // Clamping it made den wrong and let saturated pixels escape the ceiling (golden sat_p90 .90 vs .67).
    float smx = (mx - mn) / max(mx, 1e-4);
    float sp = smx <= gradeSatCap ? smx : gradeSatCap + (smx - gradeSatCap) * gradeSatKnee;
    float y2 = dot(c, W);
    float den = (mx - mn) - sp * (mx - y2);
    float r = den > 1e-4 ? clamp(sp * y2 / den, 0.0, 1.0) : 1.0;
    c = vec3(y2) + (c - vec3(y2)) * r;
  }
  vec2 p = uv * 2.0 - 1.0;
  float r = length(p) * 0.70710678;
  c *= 1.0 - gradeVig.x * smoothstep(gradeVig.y, 1.0, r);
  c = clamp(c, 0.0, 1.0);
  outputColor = vec4(gradeDecode(mix(src, c, gradeAmount)), inputColor.a);
}`;

// BT.709 zero-luma chroma basis (sRGB-encoded units): unit Cb and unit Cr as RGB offsets with Y' unchanged
const E_CB: [number, number, number] = [0.0, -0.18733, 1.8556];
const E_CR: [number, number, number] = [1.5748, -0.46813, 0.0];
export const tintRGB = (cb: number, cr: number) =>
  new Vector3(cb * E_CB[0] + cr * E_CR[0], cb * E_CB[1] + cr * E_CR[1], cb * E_CB[2] + cr * E_CR[2]);

/** Fritsch-Carlson monotone tangents for the 7 fixed knots (same as scripts/grade.py `tangents`) */
export const KX = [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1];
export function monoTangents(ky: number[]): number[] {
  const n = KX.length, h: number[] = [], d: number[] = [], m = new Array(n).fill(0);
  for (let k = 0; k < n - 1; k++) { h.push(KX[k + 1] - KX[k]); d.push((ky[k + 1] - ky[k]) / h[k]); }
  m[0] = d[0]; m[n - 1] = d[n - 2];
  for (let k = 1; k < n - 1; k++) {
    if (d[k - 1] * d[k] <= 0) { m[k] = 0; continue; }
    const w1 = 2 * h[k] + h[k - 1], w2 = h[k] + 2 * h[k - 1];
    m[k] = (w1 + w2) / (w1 / d[k - 1] + w2 / d[k]);
  }
  return m;
}

export type GradeParams = {
  ky: number[];                                  // 7 curve values at KX
  sat: [number, number, number];                 // shadows, mids, highlights
  tintS: [number, number]; tintM: [number, number]; tintH: [number, number];   // (Cb, Cr) per zone
  toe: [number, number, number];                 // warm plum offset for y < 0.18 (sRGB units)
  satCap: number;                                // HSV-saturation ceiling (above it chroma is compressed)
  satKnee: number;                               // fraction of over-cap chroma kept (tail-only compression)
  vig: [number, number];                         // strength, start radius
};

// __GRADES__ (fitted by scripts/fit2.py, written by scripts/emit_ts.py)
export const GRADE_DAY: GradeParams = {
  ky: [0.0345, 0.1828, 0.3812, 0.6605, 0.8814, 0.9631, 1],   // tangents: [1.4831, 1.4038, 1.2198, 0.9867, 0.6608, 0.4346, 0.3693]
  sat: [0.9831, 1.2727, 1.4573],
  tintS: [-0.0291, 0.0411], tintM: [0.0376, -0.0104], tintH: [0.0144, -0.0047], toe: [0, 0, 0], satCap: 1, satKnee: 0.4,
  vig: [0.1, 0.45],
};
//   shadows tint: hue 20 deg, RGB offset (+16.5, -3.5, -13.8)/255
//   mids tint: hue 230 deg, RGB offset (-4.2, -0.6, +17.8)/255
//   highlights tint: hue 228 deg, RGB offset (-1.9, -0.1, +6.8)/255
export const GRADE_GOLDEN: GradeParams = {
  ky: [0.0311, 0.1877, 0.4017, 0.6754, 0.875, 0.9582, 1],   // tangents: [1.5667, 1.498, 1.2526, 0.9235, 0.6445, 0.4724, 0.4183]
  sat: [0.8316, 0.8799, 1.7061],
  tintS: [0.0528, 0.0004], tintM: [0.0583, -0.0003], tintH: [0, 0], toe: [0, 0, 0], satCap: 1, satKnee: 0.4,
  vig: [0.16, 0.4],
};
//   shadows tint: hue 246 deg, RGB offset (+0.2, -2.6, +25.0)/255
//   mids tint: hue 245 deg, RGB offset (-0.1, -2.7, +27.6)/255
//   highlights tint: hue 0 deg, RGB offset (+0.0, -0.0, +0.0)/255

export class GradeEffect extends Effect {
  constructor(p: GradeParams, amount = 1) {
    super("GradeEffect", frag, {
      blendFunction: BlendFunction.NORMAL,
      uniforms: new Map<string, Uniform>([
        ["gradeKy", new Uniform(p.ky.slice())],
        ["gradeKm", new Uniform(monoTangents(p.ky))],
        ["gradeSat", new Uniform(new Vector3(...p.sat))],
        ["gradeTintS", new Uniform(tintRGB(...p.tintS))],
        ["gradeTintM", new Uniform(tintRGB(...p.tintM))],
        ["gradeTintH", new Uniform(tintRGB(...p.tintH))],
        ["gradeToe", new Uniform(new Vector3(...p.toe))],
        ["gradeSatCap", new Uniform(p.satCap)],
        ["gradeSatKnee", new Uniform(p.satKnee)],
        ["gradeVig", new Uniform(new Vector2(...p.vig))],
        ["gradeAmount", new Uniform(amount)],
      ]),
    });
  }
  /** switch preset per shot (day <-> golden) or blend two presets during a crossfade/time-of-day change */
  set(p: GradeParams, q?: GradeParams, t = 0) {
    const L = (a: number, b: number) => a + (b - a) * t;
    const r: GradeParams = q ? {
      ky: p.ky.map((v, i) => L(v, q.ky[i])),
      sat: [L(p.sat[0], q.sat[0]), L(p.sat[1], q.sat[1]), L(p.sat[2], q.sat[2])],
      tintS: [L(p.tintS[0], q.tintS[0]), L(p.tintS[1], q.tintS[1])], tintM: [L(p.tintM[0], q.tintM[0]), L(p.tintM[1], q.tintM[1])],
      tintH: [L(p.tintH[0], q.tintH[0]), L(p.tintH[1], q.tintH[1])],
      toe: [L(p.toe[0], q.toe[0]), L(p.toe[1], q.toe[1]), L(p.toe[2], q.toe[2])], satCap: L(p.satCap, q.satCap),
      satKnee: L(p.satKnee, q.satKnee),
      vig: [L(p.vig[0], q.vig[0]), L(p.vig[1], q.vig[1])],
    } : p;
    const u = this.uniforms;
    u.get("gradeKy")!.value = r.ky.slice();
    u.get("gradeKm")!.value = monoTangents(r.ky);
    (u.get("gradeSat")!.value as Vector3).set(...r.sat);
    u.get("gradeTintS")!.value = tintRGB(...r.tintS);
    u.get("gradeTintM")!.value = tintRGB(...r.tintM);
    u.get("gradeTintH")!.value = tintRGB(...r.tintH);
    (u.get("gradeToe")!.value as Vector3).set(...r.toe);
    u.get("gradeSatCap")!.value = r.satCap;
    u.get("gradeSatKnee")!.value = r.satKnee;
    (u.get("gradeVig")!.value as Vector2).set(...r.vig);
  }
  get amount() { return this.uniforms.get("gradeAmount")!.value as number; }
  set amount(v: number) { this.uniforms.get("gradeAmount")!.value = v; }
}

/** Presets per light (plain objects: edit / re-fit freely). */
// Round 3 re-fit for the reference targets (scorecard, 2026-11-03): warm toe lift, brighter day highlights,
// golden exposure/haze handled in the lights + tone stage.
//   day: toe lifted to ~0.03-0.06 with a warm plum offset, highlights raised (p98 .891 -> .93), highlight
//        saturation eased (sat_p90 .853 -> ~.74) while mids keep the punch.
//   golden: brighter mid/high knots, highlight saturation pulled in, violet shadow tint kept, warm toe.
export const GRADE_DAY2: GradeParams = {
  ky: [0.012, 0.058, 0.285, 0.6, 0.9, 0.995, 1],
  sat: [1.0, 1.35, 0.62], satCap: 0.63, satKnee: 0.3,
  tintS: [0.004, 0.008], tintM: [0, 0], tintH: [0.004, 0],
  toe: [0.04, 0.014, 0.01],
  vig: [0.12, 0.45],
};
export const GRADE_GOLDEN2: GradeParams = {
  ky: [0.02, 0.085, 0.34, 0.65, 0.87, 0.93, 1],
  sat: [1.0, 1.3, 0.9], satCap: 0.6, satKnee: 0.25,
  tintS: [0.045, 0.0005], tintM: [0.03, 0], tintH: [0.014, -0.003],
  toe: [0.03, 0.012, 0.01],
  vig: [0.16, 0.4],
};
// Extra interior looks for the age18 short. Same monotone curve family, different chroma intent:
// warm = tungsten living rooms (golden mids, plum shadows), clinic/bank/bath = neutral fluorescents with a cool
// shadow lift, night = deep blue with a cool toe, twilight = violet dusk.
export const GRADE_WARM: GradeParams = {
  ky: [0.016, 0.075, 0.305, 0.615, 0.885, 0.975, 1],
  sat: [1.0, 1.22, 0.8], satCap: 0.64, satKnee: 0.3,
  tintS: [0.03, 0.012], tintM: [0.02, 0.002], tintH: [0.012, 0],
  toe: [0.042, 0.018, 0.01],
  vig: [0.15, 0.42],
};
export const GRADE_CLINIC: GradeParams = {
  ky: [0.018, 0.07, 0.295, 0.6, 0.88, 0.972, 1],
  sat: [0.98, 1.1, 0.78], satCap: 0.62, satKnee: 0.3,
  tintS: [0.012, 0.012], tintM: [0.008, 0], tintH: [0, 0],
  toe: [0.02, 0.014, 0.016],
  vig: [0.1, 0.46],
};
export const GRADE_NIGHT: GradeParams = {
  ky: [0.01, 0.05, 0.26, 0.57, 0.86, 0.965, 1],
  sat: [0.92, 1.05, 0.82], satCap: 0.6, satKnee: 0.28,
  tintS: [0.012, 0.05], tintM: [0.006, 0.026], tintH: [0, 0.008],
  toe: [0, 0.012, 0.03],
  vig: [0.2, 0.38],
};
export const GRADE_TWILIGHT: GradeParams = {
  ky: [0.012, 0.056, 0.275, 0.59, 0.87, 0.968, 1],
  sat: [0.95, 1.12, 0.84], satCap: 0.61, satKnee: 0.3,
  tintS: [0.022, 0.042], tintM: [0.012, 0.02], tintH: [0.006, 0.004],
  toe: [0.01, 0.012, 0.026],
  vig: [0.18, 0.4],
};
export const GRADE_BANK: GradeParams = {
  ky: [0.02, 0.078, 0.31, 0.625, 0.89, 0.976, 1],
  sat: [0.97, 1.14, 0.8], satCap: 0.62, satKnee: 0.3,
  tintS: [0.018, 0.014], tintM: [0.01, 0.002], tintH: [0.004, 0],
  toe: [0.024, 0.014, 0.012],
  vig: [0.1, 0.46],
};
export const GRADES: Record<string, GradeParams> = {
  day: GRADE_DAY2, golden: GRADE_GOLDEN2, warm: GRADE_WARM, clinic: GRADE_CLINIC,
  night: GRADE_NIGHT, twilight: GRADE_TWILIGHT, bath: GRADE_CLINIC, bank: GRADE_BANK,
};
/** One strength (0..1, the effect's `amount`) per preset, set against the NEW world (bridge_world, 2026-10-31): full-strength
 *  presets overshot (day median Y' .59-.67 vs target .571, golden .58 vs .52); day 0.65 / golden 0.45 land at
 *  .54-.62 / ~.52. Re-fit the presets (grade.md 5.C) after the merge and raise these again. */
export const GRADE_STRENGTH: Record<string, number> = { day: 1, golden: 1 };
/** Apply the preset of a light to the effect (only touches uniforms when the light changes). */
export function gradeFor(fx: GradeEffect, light: string) {
  const tag = fx as unknown as { _light?: string };
  if (tag._light !== light) { fx.set(GRADES[light] ?? GRADES.day); tag._light = light; }
  fx.amount = GRADE_STRENGTH[light] ?? 1;
}
