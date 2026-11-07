// The "Tower Qwen" cast as lit 2D cards standing in the three.js sets. Each frame every character asks for one
// drawing (key + draw call); Pool keeps one canvas per distinct drawing, so a held pose costs nothing. Every
// continuous rig input (leverP / bonusP / mugP / bob / gaze) is rounded BEFORE it is drawn and keyed, so the canvas
// key always matches the pixels and the cache cannot grow.
// Cards are yaw billboards shaded by cardShade(), get a multiply contact blob, and live on the NOINK layer so the ink
// pass never outlines them.
import * as THREE from "three";
import { Pen, drawToon, ToonOpts, fxBlob, fxDust, fxSparks } from "./toon";
import {
  FPS, BRIDGE, SET1, SET3, CAB, PANIC_AT, DETERM_AT, SPARK_AT, OPEN_KICK, LAND_AT,
  leverAt, bonusAt, onLeaf, Light,
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
export const SU = 0.00216;   // metres per design unit (1000 units = 2.16 m)
export const PIV = 975;      // card pivot = the feet, in design units
export const SCALE = 0.85;   // ~1.84 m tall
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
    } else { this.mat.map = t; this.soft.map = t; this.mesh.renderOrder = 2; }
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
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/** drawing resolution by camera distance (sized for the 1080 x 1920 frame) */
const tier = (d: number): [number, number, number] =>
  d < 3.2 ? [1800, 3000, 3.0] : d < 6.5 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4];

const SUN = new THREE.Vector3(0.5, 0.75, -0.4).normalize();
const tmp = new THREE.Vector3();
const light2D = (cam: CamInfo) => {
  const sx = SUN.dot(cam.right), sy = -SUN.y;
  return Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) * (Math.PI / 4);
};
const LID = [0.5, 1, 1, 0.5];
/** irregular blinks: the first frame of a lid sequence inside the last 40 frames, else 0 */
const lidAt = (f: number, i: number) => {
  let s = Math.round(-40 * hh(i, 9));
  for (let n = 0; s <= f && n < 100; n++) {
    const k = f - s;
    if (k >= 0 && k < 4) return LID[k];
    s += Math.round(40 + 50 * hh(i * 31 + n, 13));
  }
  return 0;
};

const toon = (cam: CamInfo, x: number, y: number, z: number, fo: ToonOpts, scale = SCALE): Place => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.0 * scale, z)) / scale;
  const [w, h, k] = tier(d);
  const raw: ToonOpts = { ...fo, light: fo.light ?? light2D(cam) };
  const o = Object.fromEntries(Object.entries(raw).map(([kk, v]) => [kk, typeof v === "number" ? q2(v) : v])) as ToonOpts;
  return { key: `T|${JSON.stringify(o)}`, x, y, z, scale, size: [w, h, k], draw: (p) => drawToon(p, o) };
};
const blob = (out: Stage, light: Light, x: number, y: number, z: number, sc = 1, k = 1) => {
  const c = LIGHTS[light].blob;
  const s = (v: number) => Math.round(255 * Math.max(0, Math.min(1, 1.055 * (1 - (1 - v) * k) ** (1 / 2.4) - 0.055)))
    .toString(16).padStart(2, "0");
  const cc = "#" + c.map((v) => s(v)).join("");
  out.fx.push({ key: `blob|${cc}`, cw: 128, ch: 128, draw: (p) => fxBlob(p, cc), x, y: y + 0.016, z, w: 0.66 * sc, h: 0.47 * sc, flat: true });
};
/** world point of a design-space point on a yaw billboard standing at `pos` (identical math to world.ts) */
export const cardPoint = (camPos: THREE.Vector3, pos: readonly number[], scale: number, dx: number, dy: number, out = new THREE.Vector3()) => {
  const yaw = Math.atan2(camPos.x - pos[0], camPos.z - pos[2]);
  const ox = (dx - 300) * SU * scale, oy = (PIV - dy) * SU * scale;
  return out.set(pos[0] + Math.cos(yaw) * ox, pos[1] + oy, pos[2] - Math.sin(yaw) * ox);
};
const D2M = SU * SCALE;

/** the driver's screen-left fist, in design space: the 3D throttle knob is pinned under it every frame (SKILL §3 B) */
export const driverGrip = (f: number): [number, number] => {
  const tremble = f < DETERM_AT ? 2.2 * Math.sin((f - SPARK_AT) * 0.55) : 0;
  return [q2(165 - 30 * leverAt(f) + tremble), q2(580)];
};
/** world position of the knob: the fist point, pushed 8 cm BEHIND the card plane so the drawn fist covers its base */
export const knobWorld = (camPos: THREE.Vector3, f: number, out = new THREE.Vector3()) => {
  const [gx, gy] = driverGrip(f);
  cardPoint(camPos, CAB.driver, SCALE, gx, gy, out);
  // away from the lens = BEHIND the card plane (SKILL 3B depthOffset = -0.08), so the drawn fist covers the knob
  return out.addScaledVector(out.clone().sub(camPos).normalize(), 0.08);
};

// ---------------- shot 1 (0-94): the watchman on his pier ----------------
const s1 = (f: number, cam: CamInfo, out: Stage) => {
  const [x, y, z] = SET1.watchman;
  const panic = f >= PANIC_AT;
  const drop = clamp01((f - PANIC_AT) / 12);                       // the mug comes down as the road starts to move
  out.places.push(toon(cam, x, y, z, {
    who: "watchman", mode: "free", expr: panic ? "panicShock" : "calmWhistle",
    mugP: q2(1 - drop), blink: panic ? 0 : lidAt(f, 3),
    gaze: panic ? 0.15 : qn(-0.2 + 0.2 * Math.sin(f * 0.1), 20),
    gazeY: panic ? -0.5 : 0.2,
    bob: panic ? qn(2.4 * Math.sin(f * 0.55), 10) : qn(2.4 * Math.sin(f * 0.15), 10),
    lean: panic ? q2(-0.05) : 0,
  }));
  blob(out, "day", x, y, z, 1.25);
  // the carriageway tears along the joint: three puffs roll out of the crack as the leaves lift
  if (f >= OPEN_KICK && f < OPEN_KICK + 34) {
    for (const [zz, d0, dur, sc] of [[-1.35, 0, 26, 1.5], [1.35, 3, 26, 1.5], [0, 7, 30, 2.1]] as const) {
      const u = qn((f - OPEN_KICK - d0) / dur, dur);
      if (u < 0 || u > 1) continue;
      out.fx.push({ key: `dust1${d0}_${u}`, cw: 600, ch: 400, draw: fxDust(u), x: 0.1, y: BRIDGE.deckY + 0.35, z: zz, w: 3.4 * sc, h: 2.3 * sc, soft: true, opacity: 0.92 });
    }
  }
};

// ---------------- shot 2 (95-194): the cab ----------------
const s2 = (f: number, cam: CamInfo, out: Stage) => {
  const [x, y, z] = CAB.driver;
  const lp = leverAt(f);
  out.places.push(toon(cam, x, y, z, {
    who: "driver", mode: "lever", expr: f < DETERM_AT ? "panicShock" : "determinedGrin",
    leverP: q2(lp), blink: f < DETERM_AT ? lidAt(f, 7) : 0,
    gaze: qn(-0.35 + 0.25 * lp, 20), gazeY: f < DETERM_AT ? 0.5 : -0.1,
    bob: f < DETERM_AT ? qn(3.4 * Math.sin(f * 0.9), 10) : qn(2.2 * Math.sin((f - DETERM_AT) * 0.4), 10),
    lean: q2(0.03 + 0.1 * Math.sin(Math.PI * clamp01((f - DETERM_AT) / 20))),
  }));
  blob(out, "cab", x, y, z, 1.1);
  // the lever hits its stop: a spark burst right at the knob the fist is holding
  if (f >= SPARK_AT && f < SPARK_AT + 14) {
    const u = qn((f - SPARK_AT) / 14, 14);
    const k = knobWorld(cam.pos, f).clone();
    out.fx.push({ key: `spark${u}`, cw: 500, ch: 400, draw: fxSparks(u), x: k.x + (30 - 300) * D2M * 0.35, y: k.y + 0.12, z: k.z, w: 0.72, h: 0.58, soft: true });
  }
};

// ---------------- shot 3 (195-299): the plaza ----------------
const s3 = (f: number, cam: CamInfo, out: Stage) => {
  const [x, y, z] = SET3.driver;
  const bp = bonusAt(f);
  out.places.push(toon(cam, x, y, z, {
    who: "driver", mode: "free", expr: "proudSmile", bonusP: q2(bp),
    blink: bp > 0.9 ? lidAt(f, 11) : 0, gaze: qn(0.1 * Math.sin(f * 0.12), 20), gazeY: -0.1,
    bob: qn(2.6 * Math.sin(f * 0.2), 10), lean: q2(-0.02),
  }));
  blob(out, "day", x, y, z, 1.3);
  // the bus comes down on the far leaf: a big stone puff at the landing point
  if (f >= LAND_AT && f < LAND_AT + 30) {
    const u = qn((f - LAND_AT) / 30, 30);
    const land = onLeaf(26, 1, SET3.landS).p;
    const wx = SET3.bg[0] + SET3.bgScale * land[0], wy = SET3.bg[1] + SET3.bgScale * land[1];
    out.fx.push({ key: `dustL${u}`, cw: 600, ch: 400, draw: fxDust(u, true), x: wx, y: wy + 0.5, z: SET3.bg[2], w: 4.6, h: 3.1, soft: true, opacity: 0.9 });
    out.fx.push({ key: `dustL2${u}`, cw: 600, ch: 400, draw: fxDust(qn(u * 0.75, 20), true), x: wx - 0.7, y: wy + 0.2, z: SET3.bg[2] + 0.9, w: 3.2, h: 2.2, soft: true, opacity: 0.75 });
  }
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
