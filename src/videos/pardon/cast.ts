// The cast of "The Pardon" as lit flat cards in the 3D world. Each frame a character asks for one drawing (key +
// draw call); the pool keeps one canvas per distinct drawing, so repeated poses share canvases. Cards are yaw
// billboards shaded by cardShade() (scene tint, bright floor, side gradient toward the sun, painted crescent), get a
// soft multiply contact blob (and by day a tail away from the sun), and live on the NOINK layer so the world ink pass
// never outlines their quads. Effects are unlit cards on the same layer.
import * as THREE from "three";
import {
  Pen, bodyFront, bodySide, KNIGHT, PRIEST, townsfolk, fxNote, fxSpark, fxBurst, fxStars, fxSack, fxSweat, fxShock,
  fxShadow, fxContact, fxPuff, fxSword, fxCoin, fxStamp, Outfit, Expr, FrontOpts, SideOpts,
} from "./toon";
import {
  FPS, D0, SHOTS, PRIEST as PRIEST0, knightWalk, knightPhase, SACK_AT, SACK_POS, STRIKE, knight4,
  PRIEST5, KNIGHT5, knightPayoff, PRIEST6, cartX, CART_V3, smooth, clamp01, camAt, keyEnd, V3,
} from "./story";
import { NOINK } from "./ink";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";

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
const BODY = (() => { const g = new THREE.PlaneGeometry(600 * SU, 1000 * SU); g.translate(0, (975 - 500) * SU, 0); return g; })();
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
    else { this.mat.map = t; this.soft.map = t; this.mesh.renderOrder = 0; }
  }
}

// ---------------- placements ----------------
export type Place = {
  key: string; draw: (p: Pen) => void; x: number; y: number; z: number;
  scale?: number; mirror?: boolean; yaw?: number; roll?: number; size?: [number, number, number];
};
export type FxPlace = { key: string; cw: number; ch: number; draw: (p: Pen) => void; x: number; y: number; z: number; w: number; h: number; flat?: boolean; rot?: number; soft?: boolean };
/** sun = world direction TOWARD the sun */
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun?: THREE.Vector3 };

const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const q = (v: number, n = 120) => Math.round(v * n) / n;
const FOLK = [0, 1, 2, 3, 4, 5].map((v) => townsfolk(v));
/** drawing resolution by distance (sized for the 1080x1920 frame) */
const tier = (d: number): [number, number, number] =>
  d < 3.2 ? [1800, 3000, 3.0] : d < 6.5 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4];

// ---------------- light ----------------
const SUN = new THREE.Vector3(0.5, 0.75, -0.4).normalize();
const tmp = new THREE.Vector3();
let LNAME: "day" | "golden" = "day";
const findSun = (cam: CamInfo, out: THREE.Vector3) => (cam.sun ? out.copy(cam.sun).normalize() : out);
/** canvas angle the sun comes FROM on an upright card facing the camera, in 45-degree steps */
const light2D = (cam: CamInfo, mirror: boolean) => {
  const sx = SUN.dot(cam.right) * (mirror ? -1 : 1), sy = -SUN.y;
  return Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) * (Math.PI / 4);
};

/** camera frozen at the end of the current key move: billboard side/front and mirror choices stay put through a glide */
const stableView = (id: number, t: number, cam: CamInfo): CamInfo => {
  const c = camAt(id, keyEnd(id, Math.round(t * FPS)));
  const d = new THREE.Vector3(c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]).normalize();
  return { pos: new THREE.Vector3(...c.pos), right: new THREE.Vector3().crossVectors(d, new THREE.Vector3(0, 1, 0)).normalize(), sun: cam.sun };
};
/** front / side view and mirroring for someone at (x, z) walking along (dx, dz) */
const viewOf = (cam: CamInfo, x: number, z: number, dx: number, dz: number) => {
  const tx = cam.pos.x - x, tz = cam.pos.z - z, tl = Math.hypot(tx, tz) || 1;
  const c = (tx * dx + tz * dz) / tl;
  return { side: c < 0.57, mirror: dx * cam.right.x + dz * cam.right.z < 0, fs: Math.round(Math.sqrt(Math.max(0, 1 - c * c)) * 20) / 20 };
};

// ---------------- life: blinks ----------------
const LID = [0.5, 1, 1, 0.5];
const lidAt = (t: number, i: number, swaps: number[] = []) => {
  const f = Math.round(t * FPS);
  for (const ts of swaps) { const k = f - Math.round(ts * FPS) + 1; if (k >= 0 && k < 4) return LID[k]; }
  let s = Math.round(-60 * hh(i, 9));
  for (let n = 0; s <= f && n < 400; n++) {
    const k = f - s;
    if (k >= 0 && k < 4) return LID[k];
    s += Math.round(15 + 54 * hh(i * 31 + n, 13));
  }
  return 0;
};
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v));

type Who = { i: number; o: Outfit; okey: string };
const person = (cam: CamInfo, who: Who, x: number, y: number, z: number, view: { side: boolean; mirror: boolean }, fo: FrontOpts, so: SideOpts, scale = 1): Place => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.2, z)) / scale;
  const [w, h, k] = tier(d);
  const mirror = view.side && view.mirror, light = light2D(cam, mirror), seed = (who.i % 7) + 1;
  const f2: FrontOpts = { ...fo, light, seed }, s2: SideOpts = { ...so, light, seed };
  const key = view.side ? `S|${who.okey}|${fkey(s2)}` : `F|${who.okey}|${fkey(f2)}`;
  return {
    key, x, y, z, scale, mirror,
    draw: (p) => (view.side ? bodySide(p, who.o, s2) : bodyFront(p, who.o, f2)),
    size: [w, h, k],
  };
};

const CONTACT: Record<"day" | "golden", [number, number, number]> = { day: [0.2, 0.21, 0.33], golden: [0.24, 0.2, 0.33] };
const TAIL: [number, number, number] = [0.42, 0.44, 0.62];
const toSrgb = (v: number) => { const c = clamp01(v); return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; };
const hexOf = (c: [number, number, number], k: number) => "#" + c.map((v) => Math.round(255 * toSrgb(1 - (1 - v) * k)).toString(16).padStart(2, "0")).join("");
const blob = (out: Stage, x: number, y: number, z: number, sc = 1, k = 1) => {
  const hl = Math.hypot(SUN.x, SUN.z) || 1, ox = -SUN.x / hl, oz = -SUN.z / hl, rot = Math.atan2(-ox, -oz);
  if (LNAME === "day") {
    const el = Math.asin(Math.min(0.99, Math.max(0.1, SUN.y)));
    const len = Math.min(2.4, Math.max(0.5, 1.6 / Math.tan(el))) * sc, h = len + 0.55 * sc, c = 0.3 * h;
    const tc = hexOf(TAIL, k);
    out.fx.push({ key: `blob|shadow|${tc}`, cw: 128, ch: 256, draw: (p) => fxShadow(p, tc), x: x + ox * c, y: y + 0.018, z: z + oz * c,
      w: 0.72 * sc, h, flat: true, rot });
  }
  const cc = hexOf(CONTACT[LNAME], k);
  out.fx.push({ key: `blob|contact|${cc}`, cw: 128, ch: 128, draw: (p) => fxContact(p, cc), x: x + ox * 0.03 * sc, y: y + 0.022, z: z + oz * 0.03 * sc,
    w: 0.52 * sc, h: 0.4 * sc, flat: true, rot });
};

export type Stage = { places: Place[]; fx: FxPlace[] };

const knightWho = (i = 1): Who => ({ i, o: KNIGHT, okey: "knight" });
const priestWho = (i = 2): Who => ({ i, o: PRIEST, okey: "priest" });
const folkWho = (i: number, v: number): Who => ({ i, o: FOLK[v % 6], okey: `f${v % 6}` });

// ---------------- shot 1: the market square ----------------
/** the sack: carried at the knight's side, then a short hop onto the counter */
const sack = (f: number, kx: number, kz: number, out: Stage) => {
  const t0 = SACK_AT - 10;
  const carried: V3 = [kx + 0.4, 0.72, kz + 0.02];
  let pos = carried, w = 0.5, rot = -0.12;
  if (f >= t0) {
    const u = clamp01((f - t0) / 10);
    pos = [carried[0] + (SACK_POS[0] - carried[0]) * u, carried[1] + (SACK_POS[1] - carried[1]) * u + 0.42 * Math.sin(Math.PI * u), carried[2] + (SACK_POS[2] - carried[2]) * u];
    rot = -0.12 + 0.34 * u;
    w = 0.5 + 0.12 * u;
  }
  out.fx.push({ key: "sack", cw: 300, ch: 280, draw: fxSack, x: pos[0], y: pos[1], z: pos[2], w, h: w * 0.93, rot });
  if (f >= SACK_AT) out.fx.push({ key: `puff${q((f - SACK_AT) / 10, 20)}`, cw: 300, ch: 300, draw: (p) => fxPuff(p, clamp01((f - SACK_AT) / 10)), x: pos[0], y: pos[1] - 0.05, z: pos[2], w: 0.7, h: 0.55 });
};

const square = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS), walking = f < 64, w = knightWalk(f);
  const kx = walking ? w.x : -0.05;
  // He walks in front-on (he is heading almost straight at the lens). On the beat he turns into profile facing
  // screen-left, i.e. toward the pardoner, so the push-in never ends on a figure staring down the barrel.
  const kview = f < 64 ? viewOf(vcam, kx, w.z, 1, 0) : { side: true, mirror: true };
  const fo: FrontOpts = { mode: walking ? "march" : "stand", phase: walking ? q(knightPhase(f), 40) : 0, expr: "grin",
    blink: lidAt(t, 11), look: -1, facing: -1 };
  const so: SideOpts = { mode: walking ? "march" : "stand", phase: walking ? q(knightPhase(f), 40) : 0, expr: "grin",
    blink: lidAt(t, 11), stride: 0.8 };
  out.places.push(person(cam, knightWho(), kx, D0, w.z, kview, fo, so));
  blob(out, kx, D0, w.z);
  const pv = viewOf(vcam, PRIEST0.x, PRIEST0.z, 0, -1);
  // he watches the sack: a satisfied grin while it is still in hand, licking his lips once it lands
  const lifted = f >= SACK_AT - 10;
  const pexpr: Expr = f < SACK_AT - 14 ? "smile" : f < SACK_AT + 8 ? "grin" : "lick";
  out.places.push(person(cam, priestWho(), PRIEST0.x, D0, PRIEST0.z, pv,
    { mode: "stand", expr: pexpr, blink: lidAt(t, 21), look: lifted ? 1 : 0, headTilt: lifted ? 2 : 0 }, {}));
  blob(out, PRIEST0.x, D0, PRIEST0.z);
  sack(f, kx, w.z, out);
  // coins bounce out of the sack and settle on the counter on the landing beat
  if (f >= SACK_AT && f < SACK_AT + 24) {
    for (let i = 0; i < 3; i++) {
      const u = clamp01((f - SACK_AT - i * 3) / 18);
      if (u <= 0 || u >= 1) continue;
      const hop = Math.abs(Math.sin(2 * Math.PI * u)) * (1 - 0.45 * u);
      out.fx.push({ key: `coin${i}`, cw: 128, ch: 128, draw: fxCoin, x: SACK_POS[0] + (i - 1) * 0.17 + 0.04 * Math.sin(u * 7 + i),
        y: SACK_POS[1] + 0.02 + 0.3 * hop, z: SACK_POS[2] - 0.04 - i * 0.03, w: 0.14, h: 0.14, rot: 9 * u + i });
    }
  }
  // two idlers further back in the square
  for (const [i, x, z, v, d] of [[0, -5.8, 7.4, 3, 1], [1, 7.6, 8.2, 1, -1]] as const) {
    const idle = [0, 1, 2, 3][Math.floor((t + i * 0.9) / 3.1) % 4];
    const fo2: FrontOpts = { mode: "stand", expr: (["smile", "smile_closed", "neutral"] as Expr[])[i], blink: lidAt(t, 40 + i), look: d as -1 | 1,
      headTilt: idle - 1.5, tilt: idle * 0.4, facing: d as -1 | 1 };
    out.places.push(person(cam, folkWho(200 + i, v), x, D0, z, { side: false, mirror: false }, fo2, {}));
    blob(out, x, D0, z);
  }
};

// ---------------- shot 2: the priest and the scroll ----------------
const WATCHERS: [number, number, number][] = [[-2.6, 7.4, 2], [-1.3, 9.0, 4], [0.4, 7.2, 3]];
const booth = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const pv = viewOf(vcam, PRIEST0.x, PRIEST0.z, 0, -1);
  // f95-120: the scroll comes up from the belt with a damped-spring overshoot (peaks ~1.11 around f106)
  const lf = clamp01((f - 95) / 25);
  const lift = Math.max(0, Math.min(1.2, 1 - Math.exp(-5 * lf) * Math.cos(6.5 * lf)));
  // f122-130: the brass stamp comes down; f130 it slams, the wax seal pops fresh and he turns smug
  const stamped = f >= 130;
  const seal = stamped ? 1 + 0.55 * Math.max(0, 1 - (f - 130) / 9) : 0;
  const expr: Expr = stamped ? "grin" : "smile";
  // brows snap up over 3 f on the slam and stay there: smug, not just smiling
  const brow = 6 * smooth(Math.max(0, Math.min(1, (f - 129) / 3)));
  const fo: FrontOpts = { mode: "stand", expr, blink: lidAt(t, 21, [133 / FPS]), prop: "scroll", propScale: 1.25,
    propLift: lift, seal, brow, look: stamped ? 1 : 0, headTilt: q(-3.5 + 2.2 * Math.sin((f - 95) / 22), 1) };
  out.places.push(person(cam, priestWho(), PRIEST0.x, D0, PRIEST0.z, pv, fo, {}));
  blob(out, PRIEST0.x, D0, PRIEST0.z);
  // the scroll's wax-seal spot in world space (front card, near hand at design ~351, 483 = 1.06 m up)
  const sx = PRIEST0.x + 0.111 * cam.right.x, sz = PRIEST0.z + 0.111 * cam.right.z, sy = 1.06;
  // the brass stamp slides in at chest height from screen-right (never over the face) and presses on f130
  if (f >= 124 && f < 132) {
    const k = f < 130 ? smooth((f - 124) / 6) : 1, dip = f < 130 ? 0 : 0.012;
    const off = 0.5 * (1 - k);
    out.fx.push({ key: `stamp${q(k, 20)}`, cw: 260, ch: 360, draw: fxStamp,
      x: sx + cam.right.x * off, y: sy + 0.105 - dip, z: sz + cam.right.z * off - 0.03, w: 0.15, h: 0.21, rot: 0.05 });
  }
  // f131: the seal pops. A chunky star blooms up-right of the wax (the paper is light cream, so the old thin
  // hairline burst was invisible on it) and keeps clear of the seal itself and the face.
  // Cards are billboards: a world spot that reads right on paper can sit a few cm behind the plane and be
  // depth-rejected, so the star is also pulled 0.16 m back along the camera axis (right x -z is the view dir).
  if (f >= 131 && f < 139) {
    const u = (f - 131) / 8, k = f < 134 ? 0.6 + 0.133 * (f - 131) : 1;
    const px = sx + cam.right.x * 0.075 - cam.right.z * 0.16, pz = sz + cam.right.z * 0.075 + cam.right.x * 0.16;
    out.fx.push({ key: `sealPop${q(u, 20)}`, cw: 500, ch: 500, draw: (p) => fxSpark(p, q(u, 30), "#ffc93a"),
      x: px, y: sy + 0.045, z: pz, w: 0.26 * k, h: 0.26 * k, rot: -0.12 });
  }
  // the sack the knight paid with still rests on the counter where it landed
  out.fx.push({ key: "sack", cw: 300, ch: 280, draw: fxSack, x: SACK_POS[0], y: SACK_POS[1], z: SACK_POS[2], w: 0.62, h: 0.58, rot: 0.22 });
  WATCHERS.forEach(([x, z, v], i) => {
    const loll = [0.6, -0.8, 0.4][i] * Math.sin(t * 1.1 + i * 2.0);
    const fo2: FrontOpts = { mode: "stand", expr: t < 5.4 ? "neutral" : i === 1 ? "nervous" : "smile_closed", blink: lidAt(t, 60 + i),
      look: i === 0 ? -1 : 0, headTilt: loll, tilt: [0, 1, -1][i] };
    out.places.push(person(cam, folkWho(210 + i, v), x, D0, z, { side: false, mirror: false }, fo2, {}));
    blob(out, x, D0, z);
  });
};

// ---------------- shot 3: leaving town with the gold ----------------
const road = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS), cx = cartX(3, f);
  const px = cx + 1.1, pz = 2.45;
  // stride phase from ground speed: 2.6 m/s over a 1.2 m step cycle, so the boots land exactly where the road passes
  const ph = q(((t - 6.5) * CART_V3 / 1.2) % 1, 40);
  const expr: Expr = t < 7.4 ? "smile" : "whistle";
  const view = viewOf(vcam, px, pz, 1, 0);
  const fo: FrontOpts = { mode: "march", phase: ph, expr, blink: expr === "whistle" ? 0 : lidAt(t, 21), look: 0 };
  const so: SideOpts = { mode: "march", phase: ph, expr, blink: lidAt(t, 21), stride: 0.8 * view.fs };
  out.places.push(person(cam, priestWho(), px, D0, pz, view, fo, so));
  blob(out, px, D0, pz);
  if (expr === "whistle") for (let n = 0; n < 4; n++) {
    const age = ((t - 7.4 + n * 0.42) % 1.68) / 1.68;
    if (age < 0 || age > 0.9) continue;
    const pop = Math.min(1, age * 7) * (age > 0.82 ? (1 - age) / 0.08 : 1);
    if (pop <= 0.02) continue;
    const side = 0.22 + 0.36 * age + 0.05 * Math.sin(age * 9 + n);
    out.fx.push({ key: `note${n % 2}`, cw: 220, ch: 260, draw: (p) => fxNote(p, n % 2), x: px + cam.right.x * side, y: 1.66 + 0.9 * age,
      z: pz + cam.right.z * side - 0.1, w: 0.18 * pop, h: 0.21 * pop, rot: 0.3 * Math.sin(age * 6 + n) });
  }
  // dust behind the rear wheels
  for (const [dz, o] of [[-0.55, 0], [0.55, 0.4]] as const) {
    const u = ((t * 2.4 + o) % 1);
    out.fx.push({ key: `puff${q(u, 20)}`, cw: 300, ch: 300, draw: (p) => fxPuff(p, q(u, 20)), x: cx - 1.35, y: 0.24 + 0.18 * u, z: 1.6 + dz, w: 0.65 + 0.4 * u, h: 0.5 + 0.3 * u, soft: false });
  }
};

// ---------------- shot 4: the ambush ----------------
const armFx = (cam: CamInfo, x: number, y: number, z: number, kind: "spark" | "core" | "star", u: number, out: Stage, size = 1) => {
  if (kind === "spark") out.fx.push({ key: `spark${q(u, 30)}`, cw: 500, ch: 500, draw: (p) => fxSpark(p, q(u, 30)), x, y, z, w: 1.5 * size, h: 1.5 * size });
  else if (kind === "core") out.fx.push({ key: `core${q(u, 30)}`, cw: 500, ch: 500, draw: (p) => fxBurst(p, q(u, 30), "#ffffff", 8, 26, 120), x, y, z, w: 0.9 * size, h: 0.9 * size });
  else out.fx.push({ key: `stars${q(u, 30)}`, cw: 420, ch: 210, draw: (p) => fxStars(p, q(u, 30)), x, y, z, w: 0.85, h: 0.42 });
  void cam;
};
/** sword strike 0 raised .. 1 struck: held up through the wind-up, one frame to the hit, then held low */
const strikeK = (t: number) =>
  t < STRIKE ? 0 : t < STRIKE + 0.5 ? Math.min(1, (t - STRIKE) / 0.05) : 0.6 + 0.4 * Math.max(0, 1 - (t - STRIKE - 0.5) / 0.8);

const ambush = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS), cx = cartX(4, f), k = knight4(t);
  // knight: stalks the cart's front corner (always screen-right of the pardoner), steps into the road at 11.5 s,
  // strikes at 12.23 s. His stride phase is driven by the distance he actually covers, so the feet never slide.
  const kview = viewOf(vcam, k.x, k.z, 1, 0.2);
  const kd = k.x - cartX(4, 300);                          // metres walked since the shot opened
  const stepPh = q(((kd / 0.576) / 2) % 1, 40);
  const walking = t < STRIKE;
  const fo: FrontOpts = { mode: walking ? "march" : "stand", phase: walking ? stepPh : 0, expr: t < STRIKE ? "stern" : "grin",
    prop: ["sword", q(strikeK(t), 40)], blink: lidAt(t, 11), look: 0, facing: 1 };
  const so: SideOpts = { mode: walking ? "march" : "stand", phase: walking ? stepPh : 0, expr: t < STRIKE ? "stern" : "grin",
    prop: ["sword", q(strikeK(t), 40)], blade: false, blink: lidAt(t, 11), stride: 0.7 * kview.fs, stomp: 1.2 };
  out.places.push(person(cam, knightWho(), k.x, D0, k.z, kview, fo, so));
  blob(out, k.x, D0, k.z);
  // the pardoner walks ~1 m ahead of the knight; he spins toward him the moment he jumps out, then recoils
  const jolt = smooth((t - 11.55) / 0.22), back = smooth((t - STRIKE) / 0.32), px = cx + 1.9 + 0.3 * back, pz = 0.62 + 0.25 * back;
  const pexpr: Expr = t < 11.5 ? "smile" : t < STRIKE + 0.9 ? "shock" : "nervous";
  const pview: { side: boolean; mirror: boolean } = jolt > 0 ? { side: false, mirror: false } : viewOf(vcam, px, pz, 1, 0);
  const pfo: FrontOpts = { mode: jolt > 0.2 ? "stand" : "march", phase: jolt > 0.2 ? 0 : q(((t - 10) * 0.5 / 0.6 / 2) % 1, 40), expr: pexpr,
    blink: lidAt(t, 21), look: 0, wave: back > 0.25 && back < 1 ? q(0.62 * back, 20) : undefined, tilt: -7 * jolt - 2 * back };
  const pso: SideOpts = { mode: jolt > 0.2 ? "stand" : "march", phase: jolt > 0.2 ? 0 : q(((t - 10) * 0.5 / 0.6 / 2) % 1, 40), expr: pexpr,
    blink: lidAt(t, 21), stride: 0.62 * 0.6, prop: back > 0.25 ? "fist" : undefined };
  out.places.push(person(cam, priestWho(), px, D0, pz, pview, pfo, pso));
  blob(out, px, D0, pz);
  // the blade: its own camera-facing card, pivoted at the fist and angled up across the gap. The 600-unit sprite
  // card clips anything past its right edge, so the sword cannot be drawn inside the knight's own drawing.
  const ks = strikeK(t), handS = 0.36 + 0.05 * ks, BANG = 0.94, BL = 0.52, BW = (BL * 640) / 298;
  const fdx = cam.pos.x - k.x, fdz = cam.pos.z - k.z, fl = Math.hypot(fdx, fdz) || 1;
  const gx = k.x - cam.right.x * handS + (fdx / fl) * 0.04, gz = k.z - cam.right.z * handS + (fdz / fl) * 0.04;
  out.fx.push({ key: `blade${q(ks, 20)}`, cw: 640, ch: 240, draw: fxSword, x: gx, y: 1.1, z: gz, w: BW, h: (BW * 240) / 640, rot: -BANG });
  // the flares sit on the blade tip, in the open gap in front of the pardoner's face
  const sx = gx - cam.right.x * BL * Math.cos(BANG), sz = gz - cam.right.z * BL * Math.cos(BANG), sy = 1.1 + BL * Math.sin(BANG);
  if (t >= 11.55 && t < STRIKE - 0.03) {
    // the sword catches the sun as he steps out, so the blade reads before the hit
    const u = ((t - 11.55) / 0.6) % 1;
    armFx(cam, sx, sy, sz, "spark", u, out, 0.2);
  }
  if (t >= STRIKE && t < STRIKE + 0.4) {
    const u = (t - STRIKE) / 0.4;
    armFx(cam, sx, sy, sz, "spark", u, out, 0.85);
    armFx(cam, sx, sy, sz, "core", u, out, 0.85);
  }
  if (t >= 11.55 && t < 11.55 + 1.3) {
    const u = (t - 11.55) / 1.3;
    out.fx.push({ key: `shock${q(u, 20)}`, cw: 300, ch: 300, draw: fxShock, x: px, y: 1.95, z: pz, w: 0.72, h: 0.72 });
    for (const s of [-1, 1]) out.fx.push({ key: "sweat", cw: 80, ch: 120, draw: fxSweat, x: px + s * 0.34 - 0.05, y: 1.78 + 0.36 * u, z: pz - 0.12, w: 0.1, h: 0.15, rot: s * 0.2 });
  }
  // dust behind the rolling wheels: behind the rear wheel's rim, never inside the spokes
  for (const [dz, o] of [[-0.55, 0], [0.55, 0.45]] as const) {
    const u = ((t * 1.5 + o) % 1);
    out.fx.push({ key: `puff${q(u, 20)}`, cw: 300, ch: 300, draw: (p) => fxPuff(p, q(u, 20)), x: cx - 1.5, y: 0.24 + 0.18 * u, z: 1.6 + dz, w: 0.6 + 0.4 * u, h: 0.5 + 0.3 * u });
  }
};
// ---------------- shot 5: the ironic receipt ----------------
const receipt = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  // priest screen-left, in profile, shouting and shaking his raised fist at the knight
  const pv = viewOf(vcam, PRIEST5.x, PRIEST5.z, 1, 0);
  const shake = q(0.55 + 0.45 * Math.sin(t * 11), 20);
  const so: SideOpts = { mode: "stand", expr: "angry", blink: lidAt(t, 21), prop: "fist", pose: shake };
  out.places.push(person(cam, priestWho(), PRIEST5.x, D0, PRIEST5.z, pv, {}, so));
  blob(out, PRIEST5.x, D0, PRIEST5.z);
  // knight screen-right, front on, winking with the stamped pardon held out large
  const fexpr: Expr = t < 14.15 ? "grin" : t < 15.6 ? "wink" : "laugh";
  const fo: FrontOpts = { mode: "stand", expr: fexpr, blink: lidAt(t, 11, [14.15, 15.6]), prop: "scroll", propScale: 1.3, look: 0, facing: -1, headTilt: 2.5 };
  out.places.push(person(cam, knightWho(), KNIGHT5.x, D0, KNIGHT5.z, { side: false, mirror: false }, fo, {}));
  blob(out, KNIGHT5.x, D0, KNIGHT5.z);
};

// ---------------- shot 6: the payoff ----------------
const payoff = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS), k = knightPayoff(f);
  const kview = viewOf(vcam, k.x, k.z, 1, -0.03);
  // 2.57 m/s over a 1.4 m stride cycle: the feet plant where the road passes, so he recedes instead of treading water
  const ph = q((((f - 515) / FPS) * 1.83) % 1, 40);
  // full stride + a springy bob: he is walking away, so the profile reads with a visible alternating cycle
  const so: SideOpts = { mode: "march", phase: ph, expr: "grin", blink: lidAt(t, 11), stride: 0.875, stomp: 1.3 };
  out.places.push(person(cam, knightWho(), k.x, D0, k.z, kview, {}, so));
  blob(out, k.x, D0, k.z);
  // the dazed pardoner, sitting on the grass against the empty cart: contact shadow keeps him grounded
  const fo: FrontOpts = { mode: "sit", expr: "dazed", blink: 0, look: 0, headTilt: 9 * Math.sin(t * 2.1), tilt: 2 };
  out.places.push(person(cam, priestWho(), PRIEST6.x, D0, PRIEST6.z, { side: false, mirror: false }, fo, {}));
  // seated, so the contact patch has to be wider than his hem to show at all
  blob(out, PRIEST6.x, D0, PRIEST6.z + 0.22, 2.4);
  const u = (t * 0.9) % 1;
  out.fx.push({ key: `stars${q(u, 30)}`, cw: 420, ch: 210, draw: (p) => fxStars(p, q(u, 30)), x: PRIEST6.x, y: 1.26, z: PRIEST6.z, w: 0.68, h: 0.34 });
};

/** everything with a face in shot `id` at time t */
export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const s = SHOTS[id - 1];
  LNAME = s.light;
  findSun(cam, SUN);
  const vcam = stableView(id, t, cam);
  switch (s.crowd) {
    case "square": square(t, cam, vcam, out); break;
    case "booth": booth(t, cam, vcam, out); break;
    case "road": road(t, cam, vcam, out); break;
    case "ambush": ambush(t, cam, vcam, out); break;
    case "receipt": receipt(t, cam, vcam, out); break;
    case "payoff": payoff(t, cam, vcam, out); break;
  }
  return out;
};

export { FPS };
