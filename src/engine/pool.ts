/** Shared card texture cache, distance tiers and yaw-billboard actors. */
import * as THREE from "three";
import { Pen, drawKid, fxBlob, type KidOpts, SU, PIV } from "./character";
import { NOINK } from "./shaders/ink";
import { cardShade, blobMaterial, CARD_K } from "./shaders/cardshade";
export { SU, PIV } from "./character";
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
    if (!(w > 0 && h > 0 && k > 0)) throw new Error("Canvas dimensions and drawing scale must be positive");
    const r: Req = { key: `${w}x${h}|${k}|${key}`, w, h, k, draw };
    this.reqs.push(r);
    return r;
  }
  dispose() {
    for (const e of [...this.live.values(), ...this.free]) { e.tex.dispose(); e.cv.width = e.cv.height = 1; }
    this.live.clear(); this.free = []; this.reqs = [];
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
const blank = new THREE.Texture(); // no DOM access at import time
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
  dispose() { this.mesh.removeFromParent(); this.mat.dispose(); this.dmat.dispose(); }
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
  dispose() { this.mesh.removeFromParent(); this.mat.dispose(); this.soft.dispose(); this.blob.dispose(); }
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
export const q2 = (v: number) => Math.round(v * 50) / 50;

/** drawing resolution by distance (sized for the 1080x1920 frame) */
export const tier = (d: number): [number, number, number] =>
  d < 3.2 ? [1800, 3000, 3.0] : d < 6.5 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4];

const SUN = new THREE.Vector3(0.5, 0.75, -0.4).normalize();
const tmp = new THREE.Vector3();
const light2D = (cam: CamInfo) => {
  const sun = cam.sun ?? SUN;
  const sx = sun.dot(cam.right), sy = -sun.y;
  return Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) * (Math.PI / 4);
};

const LID = [0.5, 1, 1, 0.5];
export const lidAt = (f: number, i: number) => {
  let s = Math.round(-40 * hh(i, 9));
  for (let n = 0; s <= f; n++) {
    const k = f - s;
    if (k >= 0 && k < 4) return LID[k];
    s += Math.round(40 + 50 * hh(i * 31 + n, 13));
  }
  return 0;
};

/** a character card: every number in the options is rounded to 2 decimals first, then drawn and keyed */
const SCALE = 0.85;
export const makeChar = (cam: CamInfo, x: number, y: number, z: number, fo: KidOpts, scale = SCALE): Place => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.0 * scale, z)) / scale;
  const [w, h, k] = tier(d);
  const raw: KidOpts = { ...fo, light: fo.light ?? light2D(cam) };
  const o = Object.fromEntries(Object.entries(raw).map(([kk, v]) => [kk, typeof v === "number" ? (kk === "talk" ? Math.round(Math.max(0, Math.min(1, v)) * 5) / 5 : q2(v)) : v])) as KidOpts;
  return { key: `K|${JSON.stringify(o)}`, x, y, z, scale, size: [w, h, k], draw: (p) => drawKid(p, o) };
};

/** Envelope samples are one normalized RMS amplitude per video frame. */
export const talkAt = (f: number, envelope: ArrayLike<number>, gain = 1): number => {
  if (!envelope.length || !Number.isFinite(f)) return 0;
  const v = envelope[Math.max(0, Math.min(envelope.length - 1, Math.round(f)))] ?? 0;
  return Math.round(Math.max(0, Math.min(1, Number.isFinite(v) ? v * gain : 0)) * 5) / 5;
};
/** Add a white-edged multiply contact shadow to the shared stage. */
export const blob = (out: Stage, x: number, y: number, z: number, scale = 1, color = "#594757") => {
  out.fx.push({key: `blob|${color}`, cw: 128, ch: 128, draw: p => fxBlob(p, color),
    x, y: y + 0.016, z, w: 0.62 * scale, h: 0.44 * scale, flat: true});
};
/** Rule B: design-space hand -> yaw-billboard world point, with the handle behind the card. */
export const handWorldPos = (
  camPos: THREE.Vector3, charPos: readonly number[], scale: number,
  dx: number, dy: number, depthOffset = -0.08, out = new THREE.Vector3(),
): THREE.Vector3 => {
  const [cx, cy, cz] = charPos, yaw = Math.atan2(camPos.x - cx, camPos.z - cz);
  const localX = (dx - 300) * SU * scale, localY = (PIV - dy) * SU * scale;
  return out.set(cx + Math.cos(yaw) * localX + Math.sin(yaw) * depthOffset,
    cy + localY, cz - Math.sin(yaw) * localX + Math.cos(yaw) * depthOffset);
};

/** Project a partner's world contact onto this character's yaw card along the camera ray.
 * Depth differences then preserve screen contact while cameras travel around the pair.
 */
export const worldToCardPoint = (camPos: THREE.Vector3, charPos: readonly number[], scale: number, target: THREE.Vector3): [number,number] => {
  const origin=new THREE.Vector3(...charPos as [number,number,number]);
  const yaw=Math.atan2(camPos.x-origin.x,camPos.z-origin.z);
  const normal=new THREE.Vector3(Math.sin(yaw),0,Math.cos(yaw));
  const right=new THREE.Vector3(Math.cos(yaw),0,-Math.sin(yaw));
  const ray=target.clone().sub(camPos),den=ray.dot(normal);
  if(Math.abs(den)<1e-7)throw new Error("Partner contact ray is parallel to character card");
  const hit=camPos.clone().addScaledVector(ray,origin.clone().sub(camPos).dot(normal)/den).sub(origin);
  return [300+hit.dot(right)/(SU*scale),PIV-hit.y/(SU*scale)];
};
