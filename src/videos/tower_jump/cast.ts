// The "Tower Jump" cast as lit flat cards. Every continuous pose input is quantized to 0.02 (SKILL 2: round(p*50)/50)
// BEFORE it is drawn and keyed, so the canvas key always matches the pixels and the Pool stays small. Cards are yaw
// billboards (pivot at the feet, PIV 975, SU 0.00216, scale 1 so SKILL section 3's billboard formula applies as
// written), shaded by cardShade(), with a soft multiply contact blob, on layer NOINK.
import * as THREE from "three";
import { Pen, drawKid, KidOpts, fxBlob, fxImpact, fxSparks } from "./toon";
import {
  FPS, WATCH, DRV2, DRV3, PEDESTAL, BR1, BR3, BR, PANIC1_AT, OPEN_AT, SLAM_AT, SLAM_END, KICKS, JUMP_END, BONUS_AT, BONUS_END,
  SHOT3_AT, glideF, busShot3, toWorld, clamp01, Light,
} from "./story";
import { NOINK } from "./ink";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";
import { LIGHTS } from "./lights";

// ---------------- canvas pool ----------------
type Entry = { cv: HTMLCanvasElement; tex: THREE.CanvasTexture; w: number; h: number };
export type Req = { key: string; w: number; h: number; k: number; draw: (p: Pen) => void; tex?: THREE.CanvasTexture };
const makeEntry = (w: number, h: number): Entry => {
  const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  return { cv, tex, w, h };
};
export class Pool {
  private live = new Map<string, Entry>();
  private free: Entry[] = [];
  private reqs: Req[] = [];
  req(key: string, w: number, h: number, k: number, draw: (p: Pen) => void) { const r: Req = { key: `${w}x${h}|${key}`, w, h, k, draw }; this.reqs.push(r); return r; }
  flush() {
    const want = new Map<string, Req[]>();
    for (const r of this.reqs) { const l = want.get(r.key); if (l) l.push(r); else want.set(r.key, [r]); }
    for (const [key, e] of this.live) if (!want.has(key)) { this.live.delete(key); this.free.push(e); }
    while (this.free.length > 6) { const e = this.free.shift()!; e.tex.dispose(); e.cv.width = e.cv.height = 1; }
    for (const [key, rs] of want) {
      let e = this.live.get(key);
      if (!e) {
        const r = rs[0], i = this.free.findIndex((x) => x.w === r.w && x.h === r.h);
        e = i >= 0 ? this.free.splice(i, 1)[0] : makeEntry(r.w, r.h);
        const g = e.cv.getContext("2d")!;
        g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, e.w, e.h); g.setTransform(r.k, 0, 0, r.k, 0, 0);
        r.draw(new Pen(g)); e.tex.needsUpdate = true; this.live.set(key, e);
      }
      for (const r of rs) r.tex = e.tex;
    }
    this.reqs = [];
  }
}

// ---------------- sprite meshes ----------------
const blank = (() => { const c = document.createElement("canvas"); c.width = c.height = 2; return new THREE.CanvasTexture(c); })();
export const SU = 0.00216, PIV = 975;
const BODY = (() => { const g = new THREE.PlaneGeometry(600 * SU, 1000 * SU); g.translate(0, (PIV - 500) * SU, 0); return g; })();
const CARD = new THREE.PlaneGeometry(1, 1);
export class Actor {
  mesh: THREE.Mesh; mat: THREE.MeshLambertMaterial; dmat: THREE.MeshDepthMaterial; r: Req | null = null;
  constructor(parent: THREE.Object3D) {
    this.mat = cardShade(new THREE.MeshLambertMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide }));
    this.dmat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(BODY, this.mat); this.mesh.customDepthMaterial = this.dmat;
    this.mesh.onBeforeRender = (r) => { const rt = r.getRenderTarget(); CARD_K.uPx.value = (rt ? rt.height : r.domElement.height) / 1920; };
    this.mesh.castShadow = false; this.mesh.receiveShadow = true; this.mesh.visible = false;
    this.mesh.rotation.order = "YXZ"; this.mesh.renderOrder = 1; this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
  }
  bind() { const t = this.r?.tex; if (t) { this.mat.map = t; this.dmat.map = t; } }
  opacity(o: number) { this.mat.transparent = o < 0.999; this.mat.opacity = o; this.mat.needsUpdate = true; this.mesh.visible = o > 0.001; }
}
export class Fx {
  mesh: THREE.Mesh; mat: THREE.MeshBasicMaterial; soft: THREE.MeshBasicMaterial; blob: THREE.MeshBasicMaterial; r: Req | null = null;
  constructor(parent: THREE.Object3D) {
    this.mat = new THREE.MeshBasicMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.soft = new THREE.MeshBasicMaterial({ map: blank, transparent: true, depthWrite: false, side: THREE.DoubleSide });
    this.blob = blobMaterial(blank);
    this.mesh = new THREE.Mesh(CARD, this.mat); this.mesh.visible = false; this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
  }
  use(soft: boolean) { this.mesh.material = soft ? this.soft : this.mat; }
  bind() {
    const t = this.r?.tex; if (!t) return;
    if (this.r!.key.includes("|blob|")) {
      if (t.generateMipmaps) { t.generateMipmaps = false; t.minFilter = THREE.LinearFilter; t.needsUpdate = true; }
      this.blob.map = t; this.mesh.material = this.blob; this.mesh.renderOrder = 0.5;
    } else { this.mat.map = t; this.soft.map = t; this.mesh.renderOrder = 2; }
  }
  opacity(o: number) {
    this.mat.transparent = o < 0.999; this.mat.opacity = o; this.soft.opacity = o; this.soft.transparent = true;
    this.mesh.visible = o > 0.001; if (this.mesh.material === this.blob) this.mesh.visible = o > 0.4;
  }
}

// ---------------- placements ----------------
export type Place = { key: string; draw: (p: Pen) => void; x: number; y: number; z: number; scale?: number; yaw?: number; roll?: number; size?: [number, number, number]; opacity?: number };
export type FxPlace = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number; flat?: boolean; rot?: number; soft?: boolean; opacity?: number };
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun?: THREE.Vector3 };
export type Stage = { places: Place[]; fx: FxPlace[] };

const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
/** SKILL 2: quantize continuous floats to 0.02 steps */
export const q50 = (v: number) => Math.round(v * 50) / 50;
const tier = (d: number): [number, number, number] =>
  d < 3.6 ? [1800, 3000, 3.0] : d < 7 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4];
const SUN = new THREE.Vector3(0.5, 0.75, -0.4).normalize();
const tmp = new THREE.Vector3();
const light2D = (cam: CamInfo) => Math.round(Math.atan2(-SUN.y, SUN.dot(cam.right)) / (Math.PI / 4)) * (Math.PI / 4);
const LID = [0.5, 1, 1, 0.5];
const lidAt = (f: number, i: number) => {
  let s = Math.round(-40 * hh(i, 9));
  for (let n = 0; s <= f && n < 100; n++) { const k = f - s; if (k >= 0 && k < 4) return LID[k]; s += Math.round(40 + 50 * hh(i * 31 + n, 13)); }
  return 0;
};
const kid = (cam: CamInfo, at: readonly number[], fo: KidOpts): Place => {
  const [x, y, z] = at, d = cam.pos.distanceTo(tmp.set(x, y + 1.0, z)), [w, h, k] = tier(d);
  const raw: KidOpts = { ...fo, light: fo.light ?? light2D(cam) };
  const o = Object.fromEntries(Object.entries(raw).map(([kk, v]) => [kk, typeof v === "number" ? q50(v) : v])) as KidOpts;
  return { key: `K|${JSON.stringify(o)}`, x, y, z, scale: 1, size: [w, h, k], draw: (p) => drawKid(p, o) };
};
const toSrgb = (v: number) => { const c = clamp01(v); return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; };
const hexOf = (c: [number, number, number], k: number) => "#" + c.map((v) => Math.round(255 * toSrgb(1 - (1 - v) * k)).toString(16).padStart(2, "0")).join("");
const blob = (out: Stage, at: readonly number[], sc = 1, light: Light = "sunny") => {
  const cc = hexOf(LIGHTS[light].blob, 1);
  out.fx.push({ key: `blob|${cc}`, cw: 128, ch: 128, draw: (p) => fxBlob(p, cc), x: at[0], y: at[1] + 0.016, z: at[2], w: 0.62 * sc, h: 0.44 * sc, flat: true });
};
const burst = (out: Stage, key: string, f: number, f0: number, n: number, at: readonly number[], w: number, h: number, draw: (u: number) => (p: Pen) => void, opacity = 1) => {
  if (f < f0 || f >= f0 + n) return;
  const u = q50((f - f0) / n);
  out.fx.push({ key: `${key}${u}`, cw: 600, ch: 400, draw: draw(u), x: at[0], y: at[1], z: at[2], w, h, soft: true, opacity });
};

/** the driver's lever amount for frame f, already quantized (shared with world.ts's knob pin) */
export const leverAt = (f: number) => q50(f < SLAM_AT ? 0 : glideF(f, SLAM_AT, SLAM_END));
export const KICK2 = KICKS[1][0];

// ---------------- shot 1: the watchman sees the road split (0-94) ----------------
const s1 = (f: number, cam: CamInfo, out: Stage) => {
  const panic = f >= PANIC1_AT;
  out.places.push(kid(cam, WATCH, {
    kind: "watchman", expr: panic ? "panicShock" : "calmWhistle", mode: "mug",
    mugP: 0.3 + 0.12 * Math.sin(f * 0.15), blink: panic ? 0 : lidAt(f, 3), gaze: panic ? -0.6 : -0.2, gazeY: panic ? -0.2 : 0,
    bob: 2 * Math.sin(f * 0.21),
  }));
  blob(out, WATCH, 1.3);
  // dust + steam rolling off both hinges as the leaves break free
  for (const s of [-1, 1]) burst(out, `hinge${s}`, f, OPEN_AT, 34, toWorld(BR1, s * BR.hingeX, BR1.deckY + 0.6, BR.roadHalf + 0.6), 4.2, 2.8, (u) => fxImpact(u, true), 0.95);
};

// ---------------- shot 2: shock, then the throttle (95-194) ----------------
const s2 = (f: number, cam: CamInfo, out: Stage) => {
  out.places.push(kid(cam, DRV2, {
    kind: "driver", expr: f < SLAM_AT ? "panicShock" : "determinedGrin", mode: "lever", leverP: leverAt(f),
    blink: 0, gaze: f < SLAM_AT ? -0.3 : 0, gazeY: f < SLAM_AT ? -0.3 : 0,
  }));
  blob(out, DRV2, 1.25);
  // orange spark / speed burst at the pedestal base as the lever hits the stop
  const base: [number, number, number] = [PEDESTAL[0] + 0.1, 0.28, PEDESTAL[2] + 0.25];
  burst(out, "spark2", f, KICK2, 16, base, 0.95, 0.76, fxSparks);
  burst(out, "dust2", f, KICK2, 16, [base[0], 0.16, base[2] - 0.02], 1.0, 0.66, (u) => fxImpact(u), 0.85);
};

// ---------------- shot 3: the landing and the bonus (195-299) ----------------
const s3 = (f: number, cam: CamInfo, out: Stage) => {
  const bonus = f >= BONUS_AT;
  out.places.push(kid(cam, DRV3, {
    kind: "driver", expr: "proudSmile", mode: bonus ? "bonus" : "proud", bonusP: bonus ? glideF(f, BONUS_AT, BONUS_END) : 0,
    blink: lidAt(f, 7), gaze: bonus ? 0 : -0.35, gazeY: bonus ? 0 : -0.4, bob: 2 * Math.sin((f - SHOT3_AT) * 0.19),
  }));
  blob(out, DRV3, 1.25);
  // dust + sparks where the bus slams onto the lower leaf
  const land = busShot3(JUMP_END), lw = toWorld(BR3, land.x, land.y + 0.5, BR.roadHalf + 0.8);
  burst(out, "land3", f, JUMP_END, 20, lw, 4.6, 3.1, (u) => fxImpact(u, true));
  burst(out, "spark3", f, JUMP_END, 14, [lw[0], lw[1] - 0.2, lw[2] + 0.2], 3.0, 2.4, fxSparks);
};

export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  if (cam.sun) SUN.copy(cam.sun).normalize();
  const f = Math.round(t * FPS);
  if (id === 1) s1(f, cam, out); else if (id === 2) s2(f, cam, out); else s3(f, cam, out);
  return out;
};
export { FPS };
