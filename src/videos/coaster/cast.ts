// The "Coaster" cast as lit flat cards in three outdoor sets. Every frame each character asks for one drawing
// (key + draw call); the pool keeps one canvas per distinct drawing, so repeated poses share canvases. All continuous
// pose inputs (swingP / walletP / pointP / waveP / gaze / bob) are rounded to 2 decimals BEFORE they are drawn and
// keyed, so the canvas key always matches the pixels and the pool cannot grow without bound.
// Cards are yaw billboards shaded by cardShade(), get a soft multiply contact blob, and live on the NOINK layer.
import * as THREE from "three";
import { Pen, drawKid, KidOpts, fxBlob, fxImpact, fxSparks } from "./toon";
import {
  FPS, LOOP, DECK, RIVAL, SLAM_AT, SHOT2_AT, WALLET_AT, SAD_AT, SHOT3_AT, clamp01, smooth, Light,
} from "./story";
import { NOINK } from "./ink";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";
import { LIGHTS } from "./lights";

// ---------------- canvas pool ----------------
type Entry = { cv: HTMLCanvasElement; tex: THREE.CanvasTexture; w: number; h: number };
export type Req = { key: string; w: number; h: number; k: number; draw: (p: Pen) => void; tex?: THREE.CanvasTexture };
const makeEntry = (w: number, h: number): Entry => {
  const cv = document.createElement("canvas");
  cv.width = w; cv.height = h;
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  return { cv, tex, w, h };
};
export class Pool {
  private live = new Map<string, Entry>();
  private free: Entry[] = [];
  private reqs: Req[] = [];
  req(key: string, w: number, h: number, k: number, draw: (p: Pen) => void) {
    const r: Req = { key: `${w}x${h}|${key}`, w, h, k, draw };
    this.reqs.push(r);
    return r;
  }
  flush() {
    const want = new Map<string, Req[]>();
    for (const r of this.reqs) { const l = want.get(r.key); if (l) l.push(r); else want.set(r.key, [r]); }
    for (const [key, e] of this.live) if (!want.has(key)) { this.live.delete(key); this.free.push(e); }
    // cap the free list so a long continuous animation never accumulates canvases
    while (this.free.length > 6) { const e = this.free.shift()!; e.tex.dispose(); e.cv.width = e.cv.height = 1; }
    for (const [key, rs] of want) {
      let e = this.live.get(key);
      if (!e) {
        const r = rs[0], i = this.free.findIndex((x) => x.w === r.w && x.h === r.h);
        e = i >= 0 ? this.free.splice(i, 1)[0] : makeEntry(r.w, r.h);
        const g = e.cv.getContext("2d")!;
        g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, e.w, e.h); g.setTransform(r.k, 0, 0, r.k, 0, 0);
        r.draw(new Pen(g));
        e.tex.needsUpdate = true;
        this.live.set(key, e);
      }
      for (const r of rs) r.tex = e.tex;
    }
    this.reqs = [];
  }
}

// ---------------- sprite meshes ----------------
const blank = (() => { const c = document.createElement("canvas"); c.width = c.height = 2; return new THREE.CanvasTexture(c); })();
export const SU = 0.00216; // metres per design unit: 1000 units = 2.16 m
export const PIV = 975;    // card pivot (feet) in design units
const BODY = (() => { const g = new THREE.PlaneGeometry(600 * SU, 1000 * SU); g.translate(0, (PIV - 500) * SU, 0); return g; })();
const CARD = new THREE.PlaneGeometry(1, 1);

export class Actor {
  mesh: THREE.Mesh; mat: THREE.MeshLambertMaterial; dmat: THREE.MeshDepthMaterial; r: Req | null = null;
  constructor(parent: THREE.Object3D, geo: THREE.BufferGeometry = BODY) {
    this.mat = cardShade(new THREE.MeshLambertMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide }));
    this.mat.alphaToCoverage = false;
    this.dmat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(geo, this.mat);
    this.mesh.customDepthMaterial = this.dmat;
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
    this.mat.alphaToCoverage = false;
    this.soft = new THREE.MeshBasicMaterial({ map: blank, transparent: true, depthWrite: false, side: THREE.DoubleSide });
    this.blob = blobMaterial(blank);
    this.mesh = new THREE.Mesh(CARD, this.mat);
    this.mesh.visible = false; this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
  }
  use(soft: boolean) { this.mesh.material = soft ? this.soft : this.mat; }
  bind() {
    const t = this.r?.tex;
    if (!t) return;
    if (this.r!.key.includes("|blob|")) {
      if (t.generateMipmaps) { t.generateMipmaps = false; t.minFilter = THREE.LinearFilter; t.needsUpdate = true; }
      this.blob.map = t; this.mesh.material = this.blob; this.mesh.renderOrder = 0.5;
    }
    else { this.mat.map = t; this.soft.map = t; this.mesh.renderOrder = 2; }
  }
  opacity(o: number) {
    this.mat.transparent = o < 0.999; this.mat.opacity = o;
    this.soft.opacity = o; this.soft.transparent = true;
    this.mesh.visible = o > 0.001;
    if (this.mesh.material === this.blob) this.mesh.visible = o > 0.4;
  }
}

// ---------------- placements ----------------
export type Place = {
  key: string; draw: (p: Pen) => void; x: number; y: number; z: number;
  scale?: number; mirror?: boolean; yaw?: number; roll?: number; size?: [number, number, number]; opacity?: number;
};
export type FxPlace = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number; flat?: boolean; rot?: number; soft?: boolean; opacity?: number };
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun?: THREE.Vector3 };
export type Stage = { places: Place[]; fx: FxPlace[] };

const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const q2 = (v: number) => Math.round(v * 100) / 100;
const qn = (v: number, n: number) => Math.round(v * n) / n;

/** drawing resolution by distance (sized for the 1080x1920 frame) */
const tier = (d: number): [number, number, number] =>
  d < 3.2 ? [1800, 3000, 3.0] : d < 6.5 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4];

const SUN = new THREE.Vector3(0.5, 0.75, -0.4).normalize();
const tmp = new THREE.Vector3();
const light2D = (cam: CamInfo) => {
  const sx = SUN.dot(cam.right), sy = -SUN.y;
  return Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) * (Math.PI / 4);
};

const LID = [0.5, 1, 1, 0.5];
const lidAt = (f: number, i: number) => {
  let s = Math.round(-40 * hh(i, 9));
  for (let n = 0; s <= f && n < 100; n++) {
    const k = f - s;
    if (k >= 0 && k < 4) return LID[k];
    s += Math.round(40 + 50 * hh(i * 31 + n, 13));
  }
  return 0;
};

/** a character card: every number in the options is rounded to 2 decimals first, then drawn and keyed */
const SCALE = 0.85;
const kid = (cam: CamInfo, x: number, y: number, z: number, fo: KidOpts, scale = SCALE): Place => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.0 * scale, z)) / scale;
  const [w, h, k] = tier(d);
  const raw: KidOpts = { ...fo, light: fo.light ?? light2D(cam) };
  const o = Object.fromEntries(Object.entries(raw).map(([kk, v]) => [kk, typeof v === "number" ? q2(v) : v])) as KidOpts;
  return { key: `K|${JSON.stringify(o)}`, x, y, z, scale, size: [w, h, k], draw: (p) => drawKid(p, o) };
};
const toSrgb = (v: number) => { const c = clamp01(v); return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; };
const hexOf = (c: [number, number, number], k: number) => "#" + c.map((v) => Math.round(255 * toSrgb(1 - (1 - v) * k)).toString(16).padStart(2, "0")).join("");
const blob = (out: Stage, x: number, y: number, z: number, sc = 1, k = 1, light: Light = "sunny") => {
  const cc = hexOf(LIGHTS[light].blob, k);
  out.fx.push({ key: `blob|${cc}`, cw: 128, ch: 128, draw: (p) => fxBlob(p, cc), x, y: y + 0.016, z, w: 0.62 * sc, h: 0.44 * sc, flat: true });
};
/** offset along the card's own right (perpendicular to the card -> camera line) */
const cardRight = (cam: CamInfo, x: number, z: number, off: number): [number, number] => {
  const dx = cam.pos.x - x, dz = cam.pos.z - z, l = Math.hypot(dx, dz) || 1;
  return [x + (dz / l) * off, z - (dx / l) * off];
};
const D2M = SU * SCALE; // design units -> metres on a card

// ---------------- shot 1: the hammer (0-89) ----------------
export const swingAt = (f: number) => {
  if (f <= SLAM_AT) return 0.5 * (f / SLAM_AT) ** 1.6;
  if (f <= SLAM_AT + 6) return 0.5;
  return 0.5 + 0.5 * smooth((f - SLAM_AT - 6) / 22);
};
const s1 = (f: number, cam: CamInfo, out: Stage) => {
  const [x, y, z] = LOOP.builder;
  const sp = swingAt(f), rest = sp >= 0.999;
  const settle = clamp01((f - 44) / 20);
  out.places.push(kid(cam, x, y, z, {
    kind: "builder", expr: f < SLAM_AT + 8 ? "strainGrin" : "happyProud", mode: rest ? "hammerHold" : "swing", swingP: sp,
    blink: f > 30 ? lidAt(f, 3) : 0, gaze: f < SLAM_AT + 8 ? 0.3 : 0.1 * (1 - settle), gazeY: f < SLAM_AT ? -0.3 : 0,
    bob: rest ? qn(3 * Math.sin(f * 0.22), 2) : 0,
  }));
  blob(out, x, y, z, 1.3);
  // the hammer head (design x ~490 -> 0.35 m card-right) comes down on the steel rail laid along the platform front:
  // an orange spark burst right on the rail, then a small dust puff
  if (f >= SLAM_AT && f < SLAM_AT + 16) {
    const u = qn((f - SLAM_AT) / 16, 16);
    const [ix] = cardRight(cam, x, z, (490 - 300) * D2M);
    const ry = LOOP.railY + 0.06, rz = LOOP.railZ + 0.04;
    out.fx.push({ key: `spark${u}`, cw: 500, ch: 400, draw: fxSparks(u), x: ix, y: ry + 0.2, z: rz, w: 1.05, h: 0.84, soft: true });
    out.fx.push({ key: `imp${u}`, cw: 600, ch: 400, draw: fxImpact(Math.min(1, u * 1.1)), x: ix, y: ry + 0.12, z: rz - 0.02, w: 0.95, h: 0.63, soft: true, opacity: 0.8 });
  }
  // the shock runs down to the loop's footing: a big dust cloud rolls out around its base
  if (f >= SLAM_AT + 2 && f < 76) {
    const u = qn((f - SLAM_AT - 2) / 60, 60);
    out.fx.push({ key: `impB${u}`, cw: 600, ch: 400, draw: fxImpact(u, true), x: LOOP.center[0], y: 1.6, z: LOOP.center[2] + 1.2, w: 9, h: 6, soft: true, opacity: 0.95 });
  }
};

// ---------------- shot 2: wave, wallet, broke (90-194) ----------------
const s2 = (f: number, cam: CamInfo, out: Stage) => {
  const [x, y, z] = DECK.builder;
  const bob = qn(3 * Math.sin(f * 0.2), 2);
  if (f < WALLET_AT) {
    // waving, the arm lowers toward the pocket over the last 10 frames so the wallet pull is continuous
    const lower = smooth((f - (WALLET_AT - 10)) / 10);
    out.places.push(kid(cam, x, y, z, {
      kind: "builder", expr: "happyProud", mode: "wave", waveP: ((f - SHOT2_AT) / 16) % 1, raiseP: 1 - lower,
      blink: lidAt(f, 5), gaze: -0.25 * (1 - lower), bob,
    }));
  } else {
    const wp = smooth((f - WALLET_AT) / 14);
    const sad = f >= SAD_AT;
    out.places.push(kid(cam, x, y, z, {
      kind: "builder", expr: sad ? "brokeSad" : "happyProud", mode: "wallet", walletP: wp,
      blink: sad ? 0 : lidAt(f, 5), gaze: 0, gazeY: sad ? 0.9 : 0.45 * smooth((f - WALLET_AT - 4) / 10), bob: sad ? 0 : bob,
    }));
  }
  blob(out, x, y, z, 1.3);
};

// ---------------- shot 3: the rival (195-299) ----------------
/** rival's screen-left fist in design space: on the lever knob, rocking the lever a little (rounded = drawn = keyed) */
export const rivalGrip = (f: number): [number, number] =>
  [q2(145 + 7 * Math.sin((f - SHOT3_AT) * 0.09)), q2(590 + 3 * Math.sin((f - SHOT3_AT) * 0.18))];
/** world position of a design-space point on a yaw billboard at `pos` (same math as world.ts card placement) */
export const cardPoint = (camPos: THREE.Vector3, pos: readonly number[], scale: number, dx: number, dy: number, out = new THREE.Vector3()) => {
  const yaw = Math.atan2(camPos.x - pos[0], camPos.z - pos[2]);
  const ox = (dx - 300) * SU * scale, oy = (PIV - dy) * SU * scale;
  return out.set(pos[0] + Math.cos(yaw) * ox, pos[1] + oy, pos[2] - Math.sin(yaw) * ox);
};
export const RIVAL_SCALE = SCALE;
const s3 = (f: number, cam: CamInfo, out: Stage) => {
  const [x, y, z] = RIVAL.rival;
  const [gx, gy] = rivalGrip(f);
  out.places.push(kid(cam, x, y, z, {
    kind: "rival", expr: "evilSmirk", mode: "point", gripX: gx, gripY: gy,
    blink: lidAt(f, 9), gaze: -0.7, bob: qn(3 * Math.sin(f * 0.18), 2),
  }));
  blob(out, x, y, z, 1.3);
};

// ---------------- stage ----------------
export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  if (cam.sun) SUN.copy(cam.sun).normalize();
  const f = Math.round(t * FPS);
  if (id === 1) s1(f, cam, out);
  else if (id === 2) s2(f, cam, out);
  else s3(f, cam, out);
  return out;
};

export { FPS };
