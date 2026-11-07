// The cast of "Age 18" as lit flat cards in the 3D world. Each frame every character asks for one drawing (key +
// draw call); the pool keeps one canvas per distinct drawing, so repeated poses share canvases. Cards are yaw
// billboards shaded by cardShade(), get a soft multiply contact blob, and live on the NOINK layer so the world ink
// pass never outlines their quads. Effects and props are unlit cards on the same layer.
import * as THREE from "three";
import {
  Pen, drawHero, drawPerson, DOCTOR, THEO, THEO_OLD, MOM, TELLER, OFFICER,
  Expr, HeroOpts, SupportOpts, Who,
  fxCake, fxSmoke, fxFrostRing, fxSpark, fxSweat, fxPain, fxTablet, fxHazard,
  fxMonitor, fxMonitorIdle, fxPizza, fxMovingBox, fxMug, fxCane, fxSmokeWisp, fxIce, fxShock,
  fxBlob, fxPaper, fxNoBeard, mix,
} from "./toon";
import {
  FPS, SHOTS, DINING, CLINIC, CLINIC5, STREET, LIVING, BATH, BANK, DOCK,
  BLOW_AT, BLOW2_AT, clamp01, smooth, camAt, keyEnd, V3, Light,
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
    else { this.mat.map = t; this.soft.map = t; this.mesh.renderOrder = 0; }
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
/** sun = world direction TOWARD the sun */
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun?: THREE.Vector3 };

const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const q = (v: number, n = 120) => Math.round(v * n) / n;
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

/** drawing resolution by distance (sized for the 1080x1920 frame) */
const tier = (d: number): [number, number, number] =>
  d < 3.2 ? [1800, 3000, 3.0] : d < 6.5 ? [1080, 1800, 1.8] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4];

// ---------------- light ----------------
const SUN = new THREE.Vector3(0.5, 0.75, -0.4).normalize();
const tmp = new THREE.Vector3();
const findSun = (cam: CamInfo, out: THREE.Vector3) => (cam.sun ? out.copy(cam.sun).normalize() : out);
/** canvas angle the sun comes FROM on an upright card facing the camera, in 45-degree steps */
const light2D = (cam: CamInfo) => {
  const sx = SUN.dot(cam.right), sy = -SUN.y;
  return Math.round(Math.atan2(sy, sx) / (Math.PI / 4)) * (Math.PI / 4);
};

/** camera frozen at the end of the current key move: billboard side/front choices stay put through a glide */
const stableView = (id: number, t: number, cam: CamInfo): CamInfo => {
  const c = camAt(id, keyEnd(id, Math.round(t * FPS)));
  const d = new THREE.Vector3(c.look[0] - c.pos[0], c.look[1] - c.pos[1], c.look[2] - c.pos[2]).normalize();
  return { pos: new THREE.Vector3(...c.pos), right: new THREE.Vector3().crossVectors(d, new THREE.Vector3(0, 1, 0)).normalize(), sun: cam.sun };
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

const hero = (cam: CamInfo, x: number, y: number, z: number, fo: HeroOpts, scale = 1): Place => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.2, z)) / scale;
  const [w, h, k] = tier(d);
  const light = light2D(cam);
  const o: HeroOpts = { ...fo, light };
  return { key: `H|${fkey(o)}`, x, y, z, scale, size: [w, h, k], draw: (p) => drawHero(p, o) };
};

const PEOPLE: Record<string, { who: Who; key: string; i: number }> = {
  doctor: { who: DOCTOR, key: "doc", i: 3 },
  theo: { who: THEO, key: "theo", i: 11 },
  theoOld: { who: THEO_OLD, key: "theoOld", i: 12 },
  mom: { who: MOM, key: "mom", i: 21 },
  teller: { who: TELLER, key: "teller", i: 31 },
  officer: { who: OFFICER, key: "officer", i: 41 },
};
const person = (cam: CamInfo, who: keyof typeof PEOPLE, x: number, y: number, z: number, fo: SupportOpts, scale = 1): Place => {
  const P = PEOPLE[who];
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.2, z)) / scale;
  const [w, h, k] = tier(d);
  const light = light2D(cam);
  const o: SupportOpts = { ...fo, light };
  return { key: `P|${P.key}|${fkey(o)}`, x, y, z, scale, size: [w, h, k], draw: (p) => drawPerson(p, P.who, o) };
};

const toSrgb = (v: number) => { const c = clamp01(v); return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; };
const hexOf = (c: [number, number, number], k: number) => "#" + c.map((v) => Math.round(255 * toSrgb(1 - (1 - v) * k)).toString(16).padStart(2, "0")).join("");
const blob = (out: Stage, x: number, y: number, z: number, sc = 1, k = 1, light: Light = "warm") => {
  const cc = hexOf(LIGHTS[light].blob, k);
  out.fx.push({ key: `blob|${cc}`, cw: 128, ch: 128, draw: (p) => fxBlob(p, cc), x, y: y + 0.016, z, w: 0.56 * sc, h: 0.42 * sc, flat: true });
};

export type Stage = { places: Place[]; fx: FxPlace[] };

// ---------------- shot 1: the birthday freeze ----------------
const birthday = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage, id: number) => {
  const f = Math.round(t * FPS);
  const lit = f < (id === 1 ? BLOW_AT : BLOW2_AT);
  const loop = id === 12;
  const expr: Expr = loop
    ? (f < 1715 ? "solemn" : f < BLOW2_AT ? "question" : "whistle")
    : (f < 40 ? "smile" : f < 118 ? "grin" : f < 154 ? "whistle" : f < 166 ? "laugh" : "smug");
  // solemn at the candles, then straight to the lens; the face drops toward the cake and lifts on the question
  const gazeY = loop ? 0.62 * (1 - smooth((f - 1715) / 16)) : 0;
  out.places.push(hero(cam, DINING.hero[0], 0, DINING.hero[2],
    { expr, mode: "stand", blink: lidAt(t, 11, loop ? [BLOW2_AT / FPS] : [BLOW_AT / FPS]), look: 0, gaze: 0, gazeY }));
  blob(out, DINING.hero[0], 0, DINING.hero[2], 1, 1, "warm");
  const cake: FxPlace = { key: `cake${lit ? 1 : 0}`, cw: 700, ch: 700, draw: (p) => fxCake(p, loop ? "1000" : "18", lit, t), x: DINING.cake[0], y: DINING.cake[1], z: DINING.cake[2], w: 0.78, h: 0.78 };
  out.fx.push(cake);
  const blow = loop ? BLOW2_AT : BLOW_AT;
  if (f >= blow && f < blow + 34) out.fx.push({ key: `smoke${q((f - blow) / 34, 20)}`, cw: 600, ch: 600, draw: (p) => fxSmoke(p, q((f - blow) / 34, 20)), x: 0, y: DINING.cake[1] + 0.24, z: DINING.cake[2] + 0.04, w: 0.62, h: 0.62 });
  if (!loop && f >= BLOW_AT && f < BLOW_AT + 26) {
    const u = (f - BLOW_AT) / 26;
    out.fx.push({ key: `frost${q(u, 20)}`, cw: 800, ch: 800, draw: (p) => fxFrostRing(p, q(u, 20)), x: 0, y: 1.12, z: 0.62, w: 1.5, h: 1.5, soft: true });
  }
  // four wisps rise off the 1000 candles for the rest of the shot, looping slowly
  if (loop && f >= BLOW2_AT) {
    const u = ((f - BLOW2_AT) / 56) % 1;
    out.fx.push({ key: `wisp${q(u, 20)}`, cw: 700, ch: 700, draw: (p) => fxSmokeWisp(p, q(u, 20)),
      x: DINING.cake[0], y: DINING.cake[1], z: DINING.cake[2] + 0.03, w: 0.78, h: 0.78, soft: true });
  }
};

// ---------------- shot 2: the clinic scan ----------------
const scan = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const bars = f < 190 ? 0 : 18 * smooth((f - 190) / 68);
  const expr: Expr = f < 230 ? "neutral" : f < 300 ? "grin" : "smug";
  // eye contact across the two-shot, then the smug line goes to the lens
  out.places.push(hero(cam, CLINIC.hero[0], 0, CLINIC.hero[2], { expr, mode: "stand", blink: lidAt(t, 11), look: 0, gaze: f < 300 ? -0.85 : 0.05 }));
  blob(out, CLINIC.hero[0], 0, CLINIC.hero[2], 1, 1, "clinic");
  const dexpr: Expr = f < 230 ? "stern" : "smile";
  out.places.push(person(cam, "doctor", CLINIC.doctor[0], 0, CLINIC.doctor[2], { expr: dexpr, mode: f < 290 ? "hold" : "point", blink: lidAt(t, 21), look: 0, gaze: 0.9, tilt: -2.5 }));
  blob(out, CLINIC.doctor[0], 0, CLINIC.doctor[2], 0.95, 1, "clinic");
  out.fx.push({ key: `tablet${q(bars, 40)}`, cw: 800, ch: 560, draw: (p) => fxTablet(p, bars, t), x: CLINIC.tablet[0], y: CLINIC.tablet[1], z: CLINIC.tablet[2], w: 0.82, h: 0.574 });
  if (f >= 238 && f < 262) {
    const u = (f - 238) / 24;
    out.fx.push({ key: `tabspark${q(u, 30)}`, cw: 500, ch: 500, draw: (p) => fxSpark(p, q(u, 30), "#7ff0ff"), x: CLINIC.tablet[0], y: CLINIC.tablet[1], z: CLINIC.tablet[2] - 0.02, w: 0.9, h: 0.9, soft: true });
  }
};

// ---------------- shot 3: moving day ----------------
const seg = (a: number, b: number, x: number) => clamp01((x - a) / (b - a));
const moving = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const u = clamp01((f - 369) / 111);
  const hx = lerp(STREET.hero0[0], STREET.hero1[0], u), hz = lerp(STREET.hero0[2], STREET.hero1[2], u);
  const phase = q((((f - 369) / FPS) * 1.9) % 1, 40);
  out.places.push(hero(cam, hx, 0, hz, { expr: "smug", mode: "carry", phase, glasses: true, blink: 0, look: 0, gaze: -0.6 }));
  blob(out, hx, 0, hz, 1.05, 1, "day");
  out.fx.push({ key: "box", cw: 600, ch: 470, draw: fxMovingBox, x: hx + 0.04, y: 0.74, z: hz - 0.3, w: 0.64, h: 0.5 });
  // Theo bends for the box, strains to lift, then snaps upright when the lightning hits his lower back
  const bend1 = f < 380 ? 0 : f < 400 ? seg(380, 400, f) : f < 412 ? 1 : f < 419 ? 1 - 0.82 * seg(412, 419, f) : 0.18;
  const bendK = f < 440 ? bend1 : f < 452 ? 0.18 + 0.5 * seg(440, 452, f) : f < 459 ? 0.68 - 0.5 * seg(452, 459, f) : 0.18;
  const lift1 = f < 400 ? 0 : f < 412 ? 0.3 * seg(400, 412, f) : f < 419 ? 0.3 * (1 - seg(412, 419, f)) : 0;
  const lift2 = f < 440 ? 0 : f < 452 ? 0.22 * seg(440, 452, f) : f < 459 ? 0.22 * (1 - seg(452, 459, f)) : 0;
  const zap = f >= 412 && f < 430 ? seg(412, 430, f) : f >= 452 && f < 470 ? seg(452, 470, f) : -1;
  out.places.push(person(cam, "theo", STREET.theo[0], 0, STREET.theo[2],
    { expr: "pained", mode: "bend", bend: Math.round(bendK * 12) / 12, blink: lidAt(t, 31), look: 0, gaze: 0.8, tilt: zap >= 0 ? -5 : 8 }));
  blob(out, STREET.theo[0], 0, STREET.theo[2], 1.05, 1, "day");
  out.fx.push({ key: "theobox", cw: 600, ch: 470, draw: fxMovingBox, x: STREET.theo[0] - 0.04, y: 0.21 + lift1 + lift2, z: STREET.theo[2] - 0.38, w: 0.5, h: 0.39 });
  if (zap >= 0) out.fx.push({ key: `pain${q(zap, 20)}`, cw: 440, ch: 340, draw: (p) => fxPain(p, q(zap, 20)),
    x: STREET.theo[0] + 0.2, y: 0.88, z: STREET.theo[2] - 0.06, w: 0.5, h: 0.4, soft: true });
};

// ---------------- shot 4: 3 a.m. pizza ----------------
const pizza = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const seated = f < 566;
  const expr: Expr = f < 528 ? "chew" : f < 566 ? "grin" : f < 600 ? "wink" : "laugh";
  out.places.push(hero(cam, LIVING.hero[0], 0, LIVING.hero[2],
    { expr, mode: seated ? "eat" : "pointSelf", pizza: seated ? 1 : undefined, blink: seated ? 0 : lidAt(t, 11, [566 / FPS]), look: 0, gaze: seated ? -0.75 : 0.05, tilt: seated ? -1.5 : 0 }));
  blob(out, LIVING.hero[0], 0, LIVING.hero[2], 1.5, 1, "night");
  if (seated) out.fx.push({ key: "pizzabox", cw: 600, ch: 400, draw: (p) => fxPizza(p, t), x: LIVING.hero[0] + 0.5, y: 0.7, z: LIVING.hero[2] - 0.94, w: 0.7, h: 0.467 });
  const texpr: Expr = f < 566 ? "smile" : f < 596 ? "amazed" : "smile";
  // Theo leans back out of the tightening push so the pan never halves him on the frame edge
  const back = smooth((f - 574) / 22);
  const theo = person(cam, "theo", LIVING.friend[0], 0, LIVING.friend[2] + 0.24 * back, { expr: texpr, mode: "sit", blink: lidAt(t, 31), look: 0, gaze: 0.85, tilt: -3 + 6 * back });
  theo.opacity = 1 - back;
  out.places.push(theo);
  if (back < 0.99) blob(out, LIVING.friend[0], 0, LIVING.friend[2], 1.4, 1 - back, "night");
};

// ---------------- shot 5: hazard cards, helmet, seatbelt ----------------
const HAZ = [720, 765, 805] as const;
const HAZARD: ("bullet" | "car" | "bio")[] = ["bullet", "car", "bio"];
const hazards = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const helm = smooth((f - 690) / 26), belt = smooth((f - 712) / 24);
  const expr: Expr = f < 700 ? "grin" : f < 745 ? "nervous" : "shock";
  out.places.push(hero(cam, CLINIC5.hero[0], 0, CLINIC5.hero[2],
    { expr, mode: f >= 820 ? "stand" : "hold", blink: lidAt(t, 11), helm, belt, look: 0, gaze: -0.85, tilt: expr === "shock" ? -2 : 0 }));
  blob(out, CLINIC5.hero[0], 0, CLINIC5.hero[2], 1, 1, "clinic");
  out.places.push(person(cam, "doctor", CLINIC5.doctor[0], 0, CLINIC5.doctor[2], { expr: f < 700 ? "stern" : "suspicious", mode: "point", blink: lidAt(t, 21), look: 0, gaze: 0.9, lean: 0.4 }));
  blob(out, CLINIC5.doctor[0], 0, CLINIC5.doctor[2], 0.95, 1, "clinic");
  let newest = -1;
  for (let i = 0; i < 3; i++) if (f >= HAZ[i]) newest = i;
  for (let i = 0; i <= newest; i++) {
    const age = (f - HAZ[i]) / 10;
    const pop = age < 0.6 ? 0.45 + 0.62 * (age / 0.6) : 1.07 - 0.07 * Math.min(1, (age - 0.6) / 0.4);
    const back = newest - i;
    const c = CLINIC5.cards[i];
    out.fx.push({ key: `haz|${HAZARD[i]}|${q(pop, 20)}`, cw: 500, ch: 620, draw: (p) => fxHazard(p, HAZARD[i]),
      x: c[0], y: c[1], z: c[2], w: 0.425 * pop, h: 0.527 * pop, rot: -back * 0.06 });
  }
  if (f >= 745 && f < 763) out.fx.push({ key: `shock${q((f - 745) / 18, 20)}`, cw: 400, ch: 400, draw: fxShock, x: CLINIC5.hero[0], y: 1.52, z: CLINIC5.hero[2] - 0.1, w: 0.7, h: 0.7, soft: true });
  if (f >= 750 && f < 806) out.fx.push({ key: `sweat${q((f - 750) / 56, 20)}`, cw: 300, ch: 300, draw: (p) => fxSweat(p, q((f - 750) / 56, 20)), x: CLINIC5.hero[0] + 0.3, y: 1.6, z: CLINIC5.hero[2] - 0.06, w: 0.34, h: 0.34 });
};

// ---------------- shot 6: the smooth chin ----------------
const shave = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const expr: Expr = f < 884 ? "nervous" : f < 918 ? "stern" : "sad";
  // the hand climbs to the jaw and rubs while the NO BEARD card pops beside the cheek
  const phase = q(((f / FPS) * 1.1) % 1, 40);
  out.places.push(hero(cam, BATH.hero[0], 0, BATH.hero[2], { expr, mode: f < 930 ? "chin" : "stand", blink: lidAt(t, 11, [918 / FPS]), look: 0, tilt: -2, phase }));
  blob(out, BATH.hero[0], 0, BATH.hero[2], 1, 1, "bath");
  if (f >= 886 && f < 960) {
    const u = q(clamp01((f - 886) / 30), 24);
    out.fx.push({ key: `nobeard${u}`, cw: 520, ch: 420, draw: (p) => fxNoBeard(p, u),
      x: BATH.hero[0] - 0.36, y: 1.52, z: BATH.hero[2] - 0.18, w: 0.46, h: 0.372,
      opacity: f < 938 ? 1 : 1 - smooth((f - 938) / 20) });
  }
};

// ---------------- shot 7: "it's a real ID, brother!" ----------------
const counter = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const expr: Expr = f < 1002 ? "stern" : f < 1016 ? "nervous" : f < 1068 ? "shout" : "sad";
  const mode = f < 1068 ? (f < 1002 ? "stand" : "hold") : "slump";
  // glare at the teller, then the "real ID" line goes straight to the lens
  const hg = f < 1016 ? -0.9 : f < 1068 ? 0 : -0.45;
  out.places.push(hero(cam, BANK.hero[0], 0, BANK.hero[2], { expr, mode, id: 40, blink: lidAt(t, 11), look: 0, gaze: hg }));
  blob(out, BANK.hero[0], 0, BANK.hero[2], 1, 1, "bank");
  const texpr: Expr = f < 1030 ? "suspicious" : "stern";
  out.places.push(person(cam, "teller", BANK.teller[0], 0, BANK.teller[2], { expr: texpr, mode: "suspicious", blink: lidAt(t, 31), look: 0, gaze: 0.9, tilt: -3 }));
  out.places.push(person(cam, "officer", BANK.officer[0], 0, BANK.officer[2], { expr: "suspicious", mode: "point", blink: lidAt(t, 47), look: 0, gaze: 0.9, tilt: 2 }));
  out.fx.push({ key: "monitorIdle", cw: 900, ch: 560, draw: fxMonitorIdle, x: BANK.monitor[0], y: BANK.monitor[1] + 0.06, z: BANK.monitor[2] - 0.1, w: 0.54, h: 0.336 });
};

// ---------------- shot 8: frozen ----------------
const frozen = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const u = clamp01((f - 1086) / 108);
  out.fx.push({ key: `monitor${q(u, 40)}`, cw: 900, ch: 560, draw: (p) => fxMonitor(p, q(u, 40), f < 1098), x: BANK.monitor[0], y: BANK.monitor[1] + 0.06, z: BANK.monitor[2] - 0.12, w: 0.86, h: 0.535 });
  // paperwork thrown off the counter, drifting down and away
  for (let i = 0; i < 3; i++) {
    const a = Math.max(0, (f - 1094 - i * 6) / 70);
    if (a <= 0) continue;
    const px = BANK.monitor[0] - 0.34 + hh(i, 3) * 0.78, py = 1.2 + 0.5 * a - 0.35 * a * a, pz = BANK.monitor[2] - 0.3 - a * 0.5;
    out.fx.push({ key: `paper${i}`, cw: 300, ch: 400, draw: fxPaper, x: px, y: py, z: pz, w: 0.15, h: 0.19, rot: (hh(i, 7) - 0.5) * 2 + a * 2.4, opacity: clamp01(1 - a * 0.5) });
  }
  if (f >= 1146 && f < 1174) out.fx.push({ key: `ice${q((f - 1146) / 28, 20)}`, cw: 400, ch: 400, draw: (p) => fxIce(p, q((f - 1146) / 28, 20)), x: BANK.monitor[0], y: BANK.monitor[1] + 0.06, z: BANK.monitor[2] - 0.16, w: 0.9, h: 0.56, soft: true });
};

// ---------------- shot 9: the bench by the lake ----------------
const bench = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  const fade = 1 - smooth((f - 1260) / 60);
  const expr: Expr = f < 1300 ? "smile" : "sad";
  out.places.push(hero(cam, DOCK.hero[0], 0, DOCK.hero[2], { expr, mode: "sit", blink: lidAt(t, 11), look: 0, gaze: f < 1260 ? 0.8 : 0, gazeY: f < 1260 ? 0 : 0.35, tilt: f < 1250 ? 2 : -2 }));
  blob(out, DOCK.hero[0], 0, DOCK.hero[2], 1.9, 1, "golden");
  const mom = person(cam, "mom", DOCK.mom[0], 0, DOCK.mom[2], { expr: "smile", mode: "sit", blink: lidAt(t, 21), look: 0, gaze: -0.8 });
  mom.opacity = fade;
  out.places.push(mom);
  if (fade > 0.01) blob(out, DOCK.mom[0], 0, DOCK.mom[2], 1.5, fade, "golden");
  const theo = person(cam, "theoOld", DOCK.theo[0], 0, DOCK.theo[2], { expr: f < 1260 ? "smile" : "relief", mode: "sit", blink: lidAt(t, 31), look: 0, gaze: 0.8 });
  theo.opacity = fade;
  out.places.push(theo);
  if (fade > 0.01) blob(out, DOCK.theo[0], 0, DOCK.theo[2], 1.5, fade, "golden");
  // the mug and cane sit on the bench for the whole shot and stay behind after Mom and Theo fade
  // mug set down on the front edge of the seat plank: a flat contact shadow ties it to the wood
  const mugX = DOCK.mom[0] + 0.33, mugZ = DOCK.bench[2] - 0.16;
  blob(out, mugX, 0.465, mugZ, 0.55, 0.75, "golden");
  out.fx.push({ key: "mug", cw: 260, ch: 260, draw: fxMug, x: mugX, y: 0.515, z: mugZ, w: 0.19, h: 0.19 });
  out.fx.push({ key: "cane", cw: 260, ch: 520, draw: fxCane, x: DOCK.theo[0] - 0.32, y: 0.46, z: DOCK.bench[2] - 0.19, w: 0.45, h: 0.9, rot: 0.1 });
};

// ---------------- shot 10: the album at twilight ----------------
const album = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  const f = Math.round(t * FPS);
  out.places.push(hero(cam, LIVING.hero[0], 0, LIVING.hero[2], { expr: "sad", mode: "sit", album: true, blink: lidAt(t, 11), look: 0, tilt: 3 }));
  blob(out, LIVING.hero[0], 0, LIVING.hero[2], 1.6, 1, "twilight");
};

// ---------------- shot 11: the window ----------------
const windowShot = (t: number, cam: CamInfo, vcam: CamInfo, out: Stage) => {
  out.places.push(hero(cam, 0, 0, 0.55, { expr: "sad", mode: "stand", cane: true, blink: lidAt(t, 11), look: 0, tilt: 0 }));
  blob(out, 0, 0, 0.55, 1, 1, "night");
};

// ---------------- badge anchor ----------------
/** world point the HUD age badge floats above (null = no head in this shot) */
export const badgeAt = (id: number, f: number): V3 | null => {
  switch (id) {
    case 1: return [DINING.hero[0], 1.99, DINING.hero[2]];
    case 2: return [CLINIC.hero[0], 1.99, CLINIC.hero[2]];
    case 3: return [lerp(STREET.hero0[0], STREET.hero1[0], clamp01((f - 369) / 111)), 1.99, lerp(STREET.hero0[2], STREET.hero1[2], clamp01((f - 369) / 111))];
    case 4: return [LIVING.hero[0], f < 566 ? 1.87 : 1.99, LIVING.hero[2]];
    case 5: return [CLINIC5.hero[0], 1.99, CLINIC5.hero[2]];
    case 6: return [BATH.hero[0], 1.99, BATH.hero[2]];
    case 7: return [BANK.hero[0], 1.99, BANK.hero[2]];
    case 8: return null;
    case 9: return [DOCK.hero[0], 1.87, DOCK.hero[2]];
    case 10: return [LIVING.hero[0], 1.87, LIVING.hero[2]];
    case 11: return [0, 1.99, 0.55];
    default: return [DINING.hero[0], 1.99, DINING.hero[2]];
  }
};

/** everything with a face in shot `id` at time t */
export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const s = SHOTS[id - 1];
  findSun(cam, SUN);
  const vcam = stableView(id, t, cam);
  switch (s.set) {
    case "dining": birthday(t, cam, vcam, out, id); break;
    case "clinic": if (id === 2) scan(t, cam, vcam, out); else hazards(t, cam, vcam, out); break;
    case "street": moving(t, cam, vcam, out); break;
    case "living": if (id === 4) pizza(t, cam, vcam, out); else album(t, cam, vcam, out); break;
    case "bath": shave(t, cam, vcam, out); break;
    case "bank": if (id === 7) counter(t, cam, vcam, out); else frozen(t, cam, vcam, out); break;
    case "dock": bench(t, cam, vcam, out); break;
    case "window": windowShot(t, cam, vcam, out); break;
  }
  return out;
};

export { FPS };
