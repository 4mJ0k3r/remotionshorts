/** Pure, seekable camera math. Shot boundaries use [a, b), as Remotion does. */
export type V3 = [number, number, number];
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
export type Kick = { f: number; dur: number; amp: number; freq: number };
export const DOF_MEDIUM = 26, DOF_CLOSE = 22;
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const glide = (u: number, a?: number, b?: number) => {
  const x = clamp01(a === undefined || b === undefined ? u : (u - a) / Math.max(1, b - a));
  return x * x * x * (x * (6 * x - 15) + 10);
};
export const pushK = (f: number, a: number, b: number, dist = 0.06) => clamp01((f - a) / Math.max(1, b - a)) * dist;
const mix = (a: V3, b: V3, t: number): V3 => a.map((v, i) => v + (b[i] - v) * t) as V3;
const sub = (a: V3, b: V3): V3 => a.map((v, i) => v - b[i]) as V3;
const length = (v: V3) => Math.hypot(...v);
/** Move `distance` metres toward the look target without changing the view direction. */
export const dolly = (pos: V3, look: V3, distance: number): V3 => {
  const d = sub(look, pos), l = length(d) || 1;
  return pos.map((v, i) => v + d[i] / l * distance) as V3;
};
/** Yaw orbit in radians around the subject, preserving camera elevation. */
export const orbit = (pos: V3, look: V3, radians: number): V3 => {
  const [x, , z] = sub(pos, look), c = Math.cos(radians), s = Math.sin(radians);
  return [look[0] + x * c + z * s, pos[1], look[2] - x * s + z * c];
};
export const kickOffset = (f: number, kicks: readonly Kick[] = []): V3 => {
  const out: V3 = [0, 0, 0];
  for (const k of kicks) if (f >= k.f && f < k.f + k.dur) {
    const s = Math.sin((f - k.f) * k.freq) * k.amp * (1 - (f - k.f) / k.dur) ** 2;
    out[0] += s * 0.4; out[1] += s; out[2] += s * 0.3;
  }
  return out;
};
export type ShotCam = {
  a: number; b: number;
  from: V3; to: V3;
  look: V3; lookTo?: V3;
  fov?: number; fovTo?: number; roll?: number;
  /** Current subject, not a stale shot-start landmark. Defaults to the moving look target. */
  focus?: V3 | ((f: number) => V3);
  cInf?: number;
  framing?: "medium" | "close";
  /** Share of eased travel versus constant dolly velocity (0..1). */
  easeShare?: number;
  /** Additional horizontal orbit, radians, across the shot. */
  orbit?: number;
  kicks?: readonly Kick[];
};
/** Linear travel blended with glide retains a nonzero velocity at both endpoints.
 * Equal endpoints receive a 6 cm lateral track. This guarantees no held camera
 * transforms in the shot; pixel-level held-frame rates still depend on the scene.
 */
export const makeShotCam = (shot: ShotCam) => {
  if (!(shot.b > shot.a)) throw new Error("Camera shot must have b > a");
  const to: V3 = [...shot.to];
  if (length(sub(to, shot.from)) < 0.000001) to[0] += 0.06;
  const camAt = (f: number): Cam => {
    const t = clamp01((f - shot.a) / (shot.b - shot.a));
    const ease=clamp01(shot.easeShare??0.8);
    const k = ease * glide(t) + (1-ease) * t;
    const look = mix(shot.look, shot.lookTo ?? shot.look, k);
    let pos = mix(shot.from, to, k);
    if (shot.orbit) pos = orbit(pos, look, shot.orbit * t);
    const shake = kickOffset(f, shot.kicks);
    pos = pos.map((v, i) => v + shake[i]) as V3;
    if (length(sub(look, pos)) < 0.000001) throw new Error("Camera position must differ from its look target");
    const fov = (shot.fov ?? 45) + ((shot.fovTo ?? shot.fov ?? 45) - (shot.fov ?? 45)) * k;
    return {pos, look, fov: Math.max(38, Math.min(50, fov)), roll: shot.roll ?? 0};
  };
  const dofAt = (f: number): {focus: number; cInf: number} => {
    const cam = camAt(f), forward = sub(cam.look, cam.pos), l = length(forward);
    const focus = typeof shot.focus === "function" ? shot.focus(f) : shot.focus ?? cam.look;
    const delta = sub(focus, cam.pos);
    // Projection onto the view axis, rather than radial/Euclidean distance.
    return {focus: delta.reduce((s, v, i) => s + v * forward[i] / l, 0), cInf: shot.cInf ?? (shot.framing === "close" ? DOF_CLOSE : DOF_MEDIUM)};
  };
  return {camAt, dofAt};
};
