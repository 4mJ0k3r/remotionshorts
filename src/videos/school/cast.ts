// The "School Hero" cast as lit flat cards in four deep 3D sets. Every frame each character asks for one drawing
// (key + draw call); the pool keeps one canvas per distinct drawing, so repeated poses share canvases. Cards are
// yaw billboards shaded by cardShade(), get a soft multiply contact blob, and live on the NOINK layer so the world
// ink pass never outlines their quads. Effects and props are unlit cards on the same layer.
import * as THREE from "three";
import {
  Pen, drawKid, KidOpts, Expr, Mode, PropKind,
  fxBlob, fxShades, fxRifle, fxCO2, fxFrost, fxKO, fxImpact, fxHearts, fxChalk, fxFlash, fxStarBurst, fxSpeed, fxBlindSpot, fxChair,
} from "./toon";
import {
  FPS, SHOTS, CLASS, HALL, LAB, COURT,
  DOWN_AT, PAN_AT, STAND_AT, SIGNAL_AT, WALK_AT, LIFT_AT, DOOR_AT, DUCK_AT, BLIND_AT, RUN_AT, DROP_AT,
  SLIDE_AT, FLIP_AT, LAND_AT, SLAM_AT, LOOT_AT, SHADES_AT,
  STRUT_AT, WALKIE_AT, HOLO_AT, STAIRS_AT, VENT_AT, FROST_AT, CREW_AT, VAULT_AT, ORBIT2_AT, SLAM2_AT,
  LINE_AT, CRUSH_AT, TEARS_AT, EXIT_AT, SALUTE_AT, POSE_AT, HUG_AT, CHALK_AT, THWACK_AT, BUMP_AT,
  clamp01, smooth, camAt, V3, Light,
} from "./story";
import { NOINK } from "./ink";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";
import { LIGHTS } from "./lights";
import { AUDIO_ENV } from "./audioEnv";

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
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun?: THREE.Vector3 };

const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const q = (v: number, n = 120) => Math.round(v * n) / n;
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
const lerp3 = (a: V3, b: V3, k: number): V3 => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];

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

// ---------------- life: blinks / voice ----------------
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
/** lip-sync from the real VO envelope, quantized so repeated frames reuse a canvas */
const talkAt = (f: number) => {
  const v = AUDIO_ENV[Math.max(0, Math.min(AUDIO_ENV.length - 1, Math.round(f)))] ?? 0;
  return Math.round(v * 5) / 5;
};
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v));

// ---------------- helpers ----------------
const kid = (cam: CamInfo, x: number, y: number, z: number, fo: KidOpts, scale = 1): Place => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.2, z)) / scale;
  const [w, h, k] = tier(d);
  const o: KidOpts = { ...fo, light: fo.light ?? light2D(cam) };
  return { key: `K|${fkey(o)}`, x, y, z, scale, size: [w, h, k], draw: (p) => drawKid(p, o) };
};

const toSrgb = (v: number) => { const c = clamp01(v); return c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055; };
const hexOf = (c: [number, number, number], k: number) => "#" + c.map((v) => Math.round(255 * toSrgb(1 - (1 - v) * k)).toString(16).padStart(2, "0")).join("");
const blob = (out: Stage, x: number, y: number, z: number, sc = 1, k = 1, light: Light = "classroom") => {
  const cc = hexOf(LIGHTS[light].blob, k);
  out.fx.push({ key: `blob|${cc}`, cw: 128, ch: 128, draw: (p) => fxBlob(p, cc), x, y: y + 0.016, z, w: 0.56 * sc, h: 0.42 * sc, flat: true });
};

export type Stage = { places: Place[]; fx: FxPlace[] };

// a billboard spins in its own plane about its feet (world.ts rotation.set(0, yaw, roll)), so anything that has to
// sit over a tipped card - the K.O. stars over a counted-out head - is offset along the card's local right, not the
// world axes. card local +x is the horizontal perpendicular to the card->camera direction.
const cardRight = (cam: CamInfo, x: number, z: number, off: number): [number, number] => {
  const dx = cam.pos.x - x, dz = cam.pos.z - z, l = Math.hypot(dx, dz) || 1;
  return [x + (dz / l) * off, z - (dx / l) * off];
};

// ---------------- Act 1 beats 2-3 blocking ----------------
// Solved against the one fov-60 setup shots 2 and 3 share (story.ts CAMS 2/3). Every stop is placed by the head it
// has to land on screen: hero u50-58, friend 1 u34-72, friend 2 u22-36, the terrorist pinned to the door aperture,
// so at most three upright heads ever share the u 20-80 band and the fourth (the slide, the duck, the K.O.) is low.
// Measured over f375-1005 (fb42.mjs, every card in every frame): 0 head-centre band breaks, 0 heads near the edge,
// 0 ink off-frame, 0 head occlusions in a HELD pose - the only eclipses are the 45-frame run past the hero's chair
// (f714-758) and the tackle itself. Contacts inside real reach: slide 0.16 m, chair slam 0.57 m, flip clearance 0.46 m.
const A = {
  heroWait: [5.99, 2.06] as const, heroLift: [5.62, 2.57] as const, heroSlam: [5.15, 2.85] as const,
  heroPose: [5.05, 2.83] as const,
  // where the discarded chair ends up: u49-62 v59-71 at every celebration frame, so it lies across the counted-out
  // man's legs without covering his head, the K.O. stars or any of the three bros
  chairRest: [4.30, 3.55] as const,
  muscleWait: [5.30, 1.54] as const, muscleMid: [5.57, 1.58] as const, muscleRun: [6.42, 2.15] as const,
  muscleSlide: [6.62, 2.92] as const, muscleHigh: [6.37, 3.17] as const,
  hoodieWait: [5.03, 0.93] as const, hoodieCheer: [5.13, 1.82] as const,
  // the door leaf swings on x 6.92 and the wall plane is x 7.0, so he has to stay inside 6.85 or the wall eats him.
  // tAAir is the Bezier CONTROL point of the flip, not a stop he ever occupies. It sits 0.2 m on the lens side of the
  // doorway->flop chord, so the flying card passes IN FRONT of the hero at a 0.46 m clearance instead of threading his
  // own card at 0.13 m, and it is the routing that keeps his head box inside u 43-87 for the whole 1.5 s arc.
  tA0: [6.85, 2.70] as const, tA1: [6.72, 3.05] as const, tAAir: [5.66, 3.03] as const,
  // he is flipped toward the lens, so the counted-out body is the NEAREST card in the celebration frame: at the old
  // z 2.70 the friends' upright cards drew over his head and the K.O. read as an empty floor. The landing has to come
  // off the door and toward the camera at the same time - x 6.25 z 3.55 was near enough but hung off the right edge
  // (head u88, ink to u101), and this corner lays him dead-centre at head u59 with the whole body inside u38-73.
  tAFlop: [4.60, 3.00] as const,
};
// the card spins about its own FEET (world.ts rotation.set(0, yaw, roll)), so the count-out is a body tipped sideways
// with the head 1.058*cos(r) up and 1.058*sin(r) to one side. -0.42 read as a sit-up; -0.95 puts the head down at
// 0.61 m and the feet 0.86 m out, which is the flattest the flop point takes without running the ink off frame
// (measured over f845-1005: 0 band breaks, 0 edge heads, 0 ink off-frame at every roll down to -1.42).
const KO_ROLL = -0.95, FLIP_ROLL = 0.38, FLIP_LIFT = 1.05;
const mv = (a: readonly number[], b: readonly number[], k: number): [number, number] => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
// the count-out arc: tA1 -> control tAAir -> tAFlop, so the body leaves the doorway and reaches the floor on one curve
const flight = (k: number): [number, number] => {
  const w0 = (1 - k) * (1 - k), w1 = 2 * k * (1 - k), w2 = k * k;
  return [w0 * A.tA1[0] + w1 * A.tAAir[0] + w2 * A.tAFlop[0], w0 * A.tA1[1] + w1 * A.tAAir[1] + w2 * A.tAFlop[1]];
};

// ---------------- beat 1: sleepy at his desk -> lockdown flash -> he stands (0-375) ----------------
const SEAT: [number, number] = [-1.5, 8.32];
// beat 1 pushes in from fov 44 to 40, and at 40 the frame is only 2.1 m wide at the hero's depth, so of the 19 real
// chair desks just three are even inside the lens: (-4.4,11.22) holds u68-74 for all 376 frames, (-4.4,14.12)
// u37-45, and (-4.4,17.02) u15-26. The 17.02 sitter only stays there through the wide establishing shot, so she is
// dropped on the f120 cut instead of hanging half out of frame in the tighter shots. The 14.12 sitter is dropped on
// the f245 stand: from this lens the camera->hero line runs straight down column -4.4, so once his card goes upright
// it covers that desk's head box 100% of the time - drawing him there would be a stacked card, not a classmate.
// The near chair's sitter is the one measured exception to the 20-80 band: his far shoulder reaches 86% of frame
// width at f375, still 14% clear of the edge. Every other desk projects off the lens, so those classmates are not
// drawn at all - nobody sits on bare floor or walks in from outside the frame.
const MATES: { kind: "muscle" | "hoodie" | "crush"; z: number; until?: number }[] = [
  { kind: "muscle", z: 11.22 },
  { kind: "hoodie", z: 14.12, until: STAND_AT },
  { kind: "crush", z: 17.02, until: PAN_AT },
];

const s1 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const up = f >= STAND_AT;
  const duck = f >= PAN_AT && !up;
  const heroExpr: Expr = duck ? "shock" : f < PAN_AT ? "sleepy" : f < 340 ? "smug" : "angry";
  out.places.push(kid(cam, SEAT[0], 0, SEAT[1], {
    kind: "hero", expr: heroExpr, mode: up ? "stand" : duck ? "sit" : "sitChin",
    blink: lidAt(t, 11, [PAN_AT / FPS, STAND_AT / FPS]),
    gaze: up ? 0 : duck ? -0.75 : -0.35, gazeY: up ? 0 : duck ? 0.1 : -0.35,
    aura: up, eyeFire: up && f >= STAND_AT + 24, sweat: duck ? 1 : 0,
  }));
  blob(out, SEAT[0], 0, SEAT[1], 1.1, 1, "classroom");

  // friend 1 and friend 2 on their chairs, the crush one desk further under the windows. They duck at the flash and
  // STAY ducked: `up` only releases the hero, so a mate who pops back to sit when the camera settles on his feet
  // would be diving for cover twice.
  const cover = f >= PAN_AT;
  for (const m of MATES) {
    if (m.until !== undefined && f >= m.until) continue;
    const x = -4.4;
    out.places.push(kid(cam, x, 0, m.z, {
      kind: m.kind, expr: cover ? "scared" : "smile", mode: cover ? "crouch" : "sit",
      blink: lidAt(t, 23 + m.z * 3, cover ? [PAN_AT / FPS] : []),
      gaze: cover ? -0.55 : 0.15, gazeY: cover ? 0.25 : 0, sweat: cover ? 1 : 0,
    }));
    blob(out, x, 0, m.z, 1, 1, "classroom");
  }
};

// ---------------- beat 2: the signal, the step in, the chair goes up (375-660) ----------------
const s2 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const walk = smooth((f - WALK_AT) / 42);
  const lift = f >= LIFT_AT;
  const [hx, hz] = mv(A.heroWait, A.heroLift, walk);
  const heroMode: Mode = lift ? "lift" : walk > 0 && walk < 1 ? "walk" : f < WALK_AT ? "vsign" : "stand";
  out.places.push(kid(cam, hx, 0, hz, {
    kind: "hero", expr: lift ? "angry" : "smug", mode: heroMode, prop: lift ? "chair" : "none",
    phase: heroMode === "walk" ? q((((f - WALK_AT) / FPS) * 1.9) % 1, 40) : 0,
    blink: lidAt(t, 11, [SIGNAL_AT / FPS]), gaze: lift ? 0.2 : 0.45, gazeY: lift ? -0.15 : 0,
    aura: true, eyeFire: lift,
  }));
  blob(out, hx, 0, hz, 1.1, 1, "alert");

  const [mx, mz] = mv(A.muscleWait, A.muscleMid, smooth((f - 520) / 60));
  out.places.push(kid(cam, mx, 0, mz, {
    kind: "muscle", expr: f < LIFT_AT ? "nervous" : "grin", mode: "stand",
    blink: lidAt(t, 23), gaze: 0.35, sweat: f < LIFT_AT ? 1 : 0,
  }));
  blob(out, mx, 0, mz, 1.15, 1, "alert");
  out.places.push(kid(cam, A.hoodieWait[0], 0, A.hoodieWait[1], {
    kind: "hoodie", expr: f < LIFT_AT ? "scared" : "grin", mode: "stand",
    blink: lidAt(t, 31), gaze: 0.25, sweat: f < LIFT_AT ? 1 : 0,
  }));
  blob(out, A.hoodieWait[0], 0, A.hoodieWait[1], 1.1, 1, "alert");

  if (lift) {
    // the 2D chair glints as it comes off his hands - there is no 3D mesh to lose track of it
    const uu = q(clamp01((f - LIFT_AT) / 34), 30);
    if (uu < 1) out.fx.push({ key: `spark${uu}`, cw: 500, ch: 500, draw: fxStarBurst, x: hx + 0.1, y: 1.9, z: hz - 0.15, w: 0.5, h: 0.5, soft: true, opacity: 0.75 * (1 - uu) });
  }
};

// ---------------- beat 3: breach, blind spot, leg sweep, chair slam, K.O. (660-1005) ----------------
// one framing, no camera move: the door fills the right third, the three bros hold the centre lane, and every
// body that has to share the shot with an upright head is drawn low (duck, slide, K.O.).
const s3 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const breach = smooth((f - (DOOR_AT - 20)) / 60);
  const flipK = clamp01((f - FLIP_AT) / (LAND_AT - FLIP_AT));
  const down = f >= LAND_AT;
  const slam = f >= SLAM_AT;

  // the terrorist: shoulders through the door, read as blind to the room, then flipped and counted out.
  // The flip is one continuous quadratic Bezier - ankle contact, apex over the aisle, count-out. Snapping straight to
  // the air slot teleported him 0.57 m in a single frame.
  const [tx, tz] = down ? A.tAFlop : f >= FLIP_AT ? flight(flipK) : mv(A.tA0, A.tA1, breach);
  const ty = f >= FLIP_AT && !down ? Math.sin(Math.PI * flipK) * FLIP_LIFT : 0;
  const ta = kid(cam, tx, ty, tz, {
    kind: "terror", expr: down ? "pained" : f >= FLIP_AT ? "shock" : f < SLIDE_AT ? "amazed" : "scared",
    mode: down ? "slump" : f >= FLIP_AT ? "stand" : f >= SLIDE_AT ? "stand" : "aim",
    prop: f >= FLIP_AT ? "none" : "rifle", blink: 0, gaze: -0.6 - 0.3 * breach,
    hurt: down, starEyes: down, sweat: f >= SLIDE_AT && f < FLIP_AT ? 1 : 0,
  });
  // the card spins about its own feet, so the flip is a tip and the count-out is a body slumped sideways on the
  // floor with its head 0.43 m to one side - not the 1.42 rad version that buried half the ink under the floor
  ta.roll = down ? KO_ROLL : f >= FLIP_AT ? -FLIP_ROLL * Math.sin(Math.PI * flipK) : 0;
  out.places.push(ta);
  blob(out, tx, 0, tz, down ? 1.2 : 1.05, 1, "alert");
  if (down) {
    const ku = q(clamp01((f - LAND_AT) / 90), 20);
    const [hx2, hz2] = cardRight(cam, tx, tz, 1.058 * Math.sin(-KO_ROLL));
    out.fx.push({ key: `ko3${ku}`, cw: 420, ch: 420, draw: fxKO(ku), x: hx2, y: ty + 1.058 * Math.cos(KO_ROLL) + 0.42, z: hz2, w: 0.9, h: 0.9, soft: true });
  }
  // the HUD badge floats over HIS head, not the corner of the frame - and pulled 0.6 m toward the interior, because
  // centred on a man standing at u74 its 1.32 m width ran off the right edge and clipped "BLIND SPOT" in half
  if (f >= BLIND_AT - 2 && f < SLIDE_AT + 8) {
    const bu = q(clamp01((f - BLIND_AT) / 66), 22);
    const [bx2, bz2] = cardRight(cam, tx, tz, -0.6);
    out.fx.push({ key: `blind${bu}`, cw: 700, ch: 420, draw: fxBlindSpot(bu), x: bx2, y: 1.93 + 0.62, z: bz2, w: 1.32, h: 0.79 });
  }

  // friend 1: ducks as the doorway fills, breaks at f700, is already low by the time he reaches the ankles, and
  // pops up behind the counted-out man for the celebration
  const [wx, wz] = f >= LAND_AT + 10 ? A.muscleHigh
    : mv(f < RUN_AT ? A.muscleMid : f < DROP_AT ? A.muscleMid : A.muscleRun,
      f < RUN_AT ? A.muscleMid : f < DROP_AT ? A.muscleRun : A.muscleSlide,
      f < RUN_AT ? smooth((f - 520) / 60) : f < DROP_AT ? smooth((f - RUN_AT) / (DROP_AT - RUN_AT)) : smooth((f - DROP_AT) / (SLIDE_AT - DROP_AT)));
  const sliding = f >= SLIDE_AT - 15 && f < LAND_AT + 10;
  out.places.push(kid(cam, wx, 0, wz, {
    kind: "muscle", expr: sliding ? "angry" : f >= SLAM_AT ? "grin" : f >= DUCK_AT ? "scared" : "nervous",
    mode: sliding ? "slide" : f < RUN_AT ? (f >= DUCK_AT ? "crouch" : "stand")
      : f < LAND_AT + 10 ? "run" : f >= 940 ? "highfive" : "stand",
    phase: sliding || (f >= RUN_AT && f < LAND_AT + 10) ? q((((f - RUN_AT) / FPS) * 2.6) % 1, 40) : 0,
    blink: lidAt(t, 23), gaze: sliding ? 0.5 : -0.2,
  }));
  blob(out, wx, 0, wz, 1.15, 1, "alert");
  if (sliding) {
    const su = q(clamp01((f - SLIDE_AT + 15) / 55), 24);
    out.fx.push({ key: `speed3${su}`, cw: 600, ch: 600, draw: fxSpeed(su), x: wx - 0.35, y: 0.55, z: wz + 0.3, w: 1.5, h: 1.5, soft: true });
  }
  if (f >= FLIP_AT && f < FLIP_AT + 60) {
    const ru = q(clamp01((f - FLIP_AT) / 60), 24);
    out.fx.push({ key: `fly3${ru}`, cw: 460, ch: 340, draw: fxRifle, x: tx + 0.45 * ru, y: 1.5 + 1.1 * ru - 2.2 * ru * ru, z: tz - 0.25 * ru, w: 0.9, h: 0.66, rot: ru * 4.2 });
  }

  // friend 2 stays down through the breach and only rises into the cheer after the man is on the floor, so no
  // upright head shares the frame with the slide or the slam
  const [cx, cz] = mv(A.hoodieWait, A.hoodieCheer, smooth((f - 875) / 45));
  out.places.push(kid(cam, cx, 0, cz, {
    kind: "hoodie", expr: f >= 885 ? "laugh" : "nervous",
    mode: f >= DUCK_AT && f < 880 ? "crouch" : f >= 940 ? "cheer" : "stand",
    blink: lidAt(t, 31), gaze: -0.15, sweat: f < 885 ? 1 : 0,
  }));
  blob(out, cx, 0, cz, 1.1, 1, "alert");

  // the hero: chair still overhead, then the leap and the slam, then the pose with both arms up
  const slamK = smooth((f - SLAM_AT) / 22);
  const [hx, hz] = !slam ? A.heroLift
    : f < SLAM_AT + 25 ? mv(A.heroLift, A.heroSlam, slamK)
    : f < SLAM_AT + 75 ? mv(A.heroSlam, A.heroPose, smooth((f - SLAM_AT - 40) / 35))
    : A.heroPose;
  const hy = slam && slamK < 1 ? Math.sin(Math.PI * slamK) * 0.3 : 0;
  const heroMode: Mode = !slam ? "lift" : slamK < 1 ? "smash" : f >= 940 ? "highfive" : "cheer";
  out.places.push(kid(cam, hx, hy, hz, {
    kind: "hero", expr: slam ? "grin" : "angry", mode: heroMode, prop: f < SLAM_AT + 25 ? "chair" : "none",
    blink: 0, gaze: slam ? -0.45 : 0.2, gazeY: slam ? 0.2 : -0.1,
    aura: true, eyeFire: true,
  }));
  blob(out, hx, 0, hz, 1.1, 1, "alert");
  if (slam && slamK < 1) {
    const iu = q(slamK, 20);
    out.fx.push({ key: `impact3${iu}`, cw: 700, ch: 700, draw: fxImpact("SLAM", "#ffd23a", iu), x: tx, y: 0.95, z: tz, w: 2.1, h: 2.1, soft: true });
  }
  // the chair he lets go of at the bottom of the slam does not evaporate - it topples across the man it flattened
  // and stays in the shot. A held prop that stops existing on one frame reads as a dropped texture, not a throw.
  if (f >= SLAM_AT + 25) {
    const dk = q(smooth((f - (SLAM_AT + 25)) / 18), 24);
    const [dx, dz] = mv([hx, hz], A.chairRest, dk);
    out.fx.push({ key: `chair${dk}`, cw: 520, ch: 520, draw: fxChair, x: dx, y: lerp(0.95, 0.40, dk), z: dz,
      w: 1.25, h: 1.25, rot: lerp(2.05, 1.32, dk), soft: dk < 1 });
  }
};

// ---------------- shot 4: gear, shades, strut (1005-1335) ----------------
const s4 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const walk = f >= STRUT_AT;
  const u = smooth((f - STRUT_AT) / 110);
  const hz = walk ? lerp(HALL.hero[2], 9.0, u) : HALL.hero[2];
  const gear: PropKind = f < 1055 ? "rifle" : f < 1090 ? "vest" : "walkie";
  const shades = f >= SHADES_AT;
  out.places.push(kid(cam, HALL.hero[0], 0, hz, {
    kind: "hero", expr: shades ? "smug" : "stern", mode: walk ? "walk" : "hold", prop: walk ? "rifle" : gear,
    phase: walk ? q(((f - STRUT_AT) / FPS) * 1.6 % 1, 40) : 0, shades, blink: lidAt(t, 11, [SHADES_AT / FPS]), gaze: -0.2,
  }));
  blob(out, HALL.hero[0], 0, hz, 1.05, 1, "hall");
  out.places.push(kid(cam, 1.3, 0, 5.0, { kind: "muscle", expr: "grin", mode: walk ? "walk" : "stand", phase: walk ? 0.4 : 0, blink: lidAt(t, 23), gaze: -0.2 }));
  blob(out, 1.3, 0, 5.0, 1.1, 1, "hall");
  out.places.push(kid(cam, 2.3, 0, 5.4, { kind: "hoodie", expr: "grin", mode: walk ? "walk" : "stand", phase: walk ? 0.7 : 0, blink: lidAt(t, 31), gaze: -0.25 }));
  blob(out, 2.3, 0, 5.4, 1.05, 1, "hall");
  // the downed gunman, kneeling by the lockers
  out.places.push(kid(cam, HALL.downed[0], 0, HALL.downed[2], {
    kind: "terror", expr: "pained", mode: "kneel", blink: 0, gaze: 0.2, tied: true, prop: "none",
  }));
  blob(out, HALL.downed[0], 0, HALL.downed[2], 1, 1, "hall");
  if (!walk && f < 1080) {
    const ku = q(clamp01((f - LOOT_AT) / 70), 20);
    out.fx.push({ key: `ko4${ku}`, cw: 400, ch: 400, draw: fxKO(ku), x: HALL.downed[0], y: 1.9, z: HALL.downed[2], w: 0.8, h: 0.8, soft: true, opacity: 1 - ku * 0.6 });
  }
  // sunglasses drop into his hand
  if (f >= SHADES_AT - 26 && f < SHADES_AT + 2) {
    const su = q(clamp01((f - (SHADES_AT - 26)) / 26), 20);
    out.fx.push({ key: `shades${su}`, cw: 460, ch: 180, draw: fxShades, x: HALL.hero[0] + 0.06, y: lerp(2.15, 1.55, su), z: HALL.hero[2] + 0.4, w: 0.5, h: 0.2, rot: -0.1 });
  }
};

// ---------------- shot 5: walkie, hologram, stairs (1335-1725) ----------------
const s5 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  if (f < HOLO_AT) {
    out.places.push(kid(cam, HALL.hero[0], 0, HALL.hero[2], {
      kind: "hero", expr: "grin", mode: "hold", prop: "walkie", blink: lidAt(t, 11), gaze: 0.05, talk: talkAt(f),
    }));
    blob(out, HALL.hero[0], 0, HALL.hero[2], 1.05, 1, "hall");
    out.places.push(kid(cam, 1.3, 0, 5.0, { kind: "muscle", expr: "smile", mode: "stand", blink: lidAt(t, 23), gaze: 0.4 }));
    out.places.push(kid(cam, 2.3, 0, 5.4, { kind: "hoodie", expr: "grin", mode: "stand", blink: lidAt(t, 31), gaze: 0.4 }));
    return;
  }
  if (f < STAIRS_AT) {
    // dive toward the hologram: the wireframe school and the crush's portrait
    const u = smooth((f - HOLO_AT) / (STAIRS_AT - HOLO_AT));
    const hx = lerp(0.6, -0.6, u), hz = lerp(15.2, 17.1, u);
    out.places.push(kid(cam, hx, 0, hz, {
      kind: "hero", expr: "amazed", mode: u > 0.82 ? "point" : "run", phase: q((f / FPS) * 2.0 % 1, 40),
      blink: 0, gaze: -0.7, aura: true, eyeFire: true,
    }));
    blob(out, hx, 0, hz, 1.05, 1, "hall");
    out.places.push(kid(cam, HALL.holo[0] + 0.1, 0.72, HALL.holo[2], {
      kind: "crush", expr: "smile", mode: "stand", blink: 0, gaze: 0.2, starEyes: true, blush: true, scale: 0.62,
    }));
    const hu = q((f / 34) % 1, 24);
    out.fx.push({ key: `hearts${hu}`, cw: 560, ch: 560, draw: fxHearts(hu, 6), x: HALL.holo[0], y: 1.5, z: HALL.holo[2] - 0.2, w: 1.4, h: 1.4, soft: true });
    return;
  }
  // stairs sprint, >100 %
  const u = smooth((f - STAIRS_AT) / 135);
  const hz = lerp(30.0, 34.0, u), hy = u < 0.16 ? 0 : (u - 0.16) * 0.66 * 3 * 0.2;
  out.places.push(kid(cam, 0.2, hy, hz, {
    kind: "hero", expr: "stern", mode: "run", phase: q((((f - STAIRS_AT) / FPS) * 2.6) % 1, 40),
    blink: 0, gaze: 0.1, aura: true, eyeFire: true,
  }));
  blob(out, 0.2, hy, hz, 1.0, 1, "hall");
  if (f > STAIRS_AT + 30) {
    const su = q(clamp01((f - STAIRS_AT - 30) / 50), 20);
    out.fx.push({ key: `speed5${su}`, cw: 600, ch: 600, draw: fxSpeed(su), x: 0.6, y: 1.4, z: hz + 0.8, w: 1.4, h: 1.4, soft: true, opacity: 0.55 });
  }
};

// ---------------- shot 6: vent drop, -78 C, friends punch (1725-2055) ----------------
const s6 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const drop = f < FROST_AT;
  const fall = clamp01((f - VENT_AT) / 100);
  const hy = drop ? 2.95 * (1 - smooth(fall)) : 0;
  const mode: Mode = drop ? (fall > 0.9 ? "kneel" : "crouch") : f < CREW_AT ? "hold" : "stand";
  out.places.push(kid(cam, 0.1, hy, 8.0, {
    kind: "hero", expr: drop ? "stern" : f < CREW_AT ? "stern" : "grin", mode,
    prop: !drop && f < CREW_AT + 40 ? "extinguisher" : "none", blink: lidAt(t, 11, [FROST_AT / FPS]),
    gaze: 0.7, aura: true, eyeFire: true,
  }));
  blob(out, 0.1, hy, 8.0, 1.05, 1, "lab");

  const frozen = f >= FROST_AT + 30;
  for (const [i, x, z] of [[0, LAB.goonA[0], LAB.goonA[2]], [1, LAB.goonB[0], LAB.goonB[2]]] as const) {
    const knocked = f >= CREW_AT + 40 + i * 10;
    out.places.push(kid(cam, x, 0, z, {
      kind: "terror", expr: knocked ? "pained" : frozen ? "shock" : "stern", mode: knocked ? "slump" : frozen ? "stand" : "aim",
      blink: 0, gaze: -0.8, prop: "rifle", frost: frozen ? 1 : 0, hurt: knocked,
    }));
    blob(out, x, 0, z, 1.05, 1, "lab");
  }
  if (f >= FROST_AT && f < FROST_AT + 80) {
    const u = q(clamp01((f - FROST_AT) / 80), 24);
    out.fx.push({ key: `co2${u}`, cw: 700, ch: 600, draw: fxCO2(u), x: 1.3, y: 1.05, z: 8.7, w: 2.6, h: 2.2, soft: true });
    out.fx.push({ key: `frost${u}`, cw: 600, ch: 620, draw: fxFrost(u), x: LAB.goonA[0], y: 1.0, z: LAB.goonA[2] - 0.2, w: 1.6, h: 1.7, soft: true, opacity: 0.9 });
  }
  if (f >= CREW_AT) {
    const cu = smooth((f - CREW_AT) / 40);
    const mx = lerp(-1.2, -0.2, cu), mz = lerp(8.0, 9.4, cu);
    out.places.push(kid(cam, mx, 0, mz, {
      kind: "muscle", expr: "grin", mode: f >= CREW_AT + 30 ? "punch" : "run", phase: q((f / FPS) * 2 % 1, 40), blink: 0, gaze: 0.9,
    }));
    blob(out, mx, 0, mz, 1.1, 1, "lab");
    out.places.push(kid(cam, lerp(-1.7, -0.9, cu), 0, lerp(8.4, 9.9, cu), {
      kind: "hoodie", expr: "grin", mode: f >= CREW_AT + 40 ? "punch" : "run", phase: q((f / FPS) * 2 % 1 + 0.5, 40), blink: 0, gaze: 0.9,
    }));
  }
};

// ---------------- shot 7: lab slide, orbit kick, wall slam (2055-2355) ----------------
const s7 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const orbit = f >= ORBIT2_AT;
  const slam = f >= SLAM2_AT;
  if (!orbit) {
    const u = smooth((f - VAULT_AT) / (ORBIT2_AT - VAULT_AT));
    const hx = lerp(-1.8, 0.9, u), hz = lerp(9.4, 10.1, u);
    out.places.push(kid(cam, hx, 0, hz, {
      kind: "hero", expr: "stern", mode: "slide", blink: 0, gaze: 0.9, aura: true, eyeFire: true,
    }));
    blob(out, hx, 0, hz, 1.05, 1, "lab");
    const su = q(u, 24);
    out.fx.push({ key: `speed7${su}`, cw: 600, ch: 600, draw: fxSpeed(su), x: hx - 0.4, y: 1.1, z: hz + 0.5, w: 1.6, h: 1.6, soft: true });
    if (f < 2130) {
      const bu = q(clamp01((f - VAULT_AT) / 60), 20);
      out.fx.push({ key: `glass${bu}`, cw: 400, ch: 400, draw: fxStarBurst, x: 0.8, y: 1.25, z: 10.2, w: 0.8, h: 0.8, soft: true, opacity: 1 - bu });
    }
  } else if (!slam) {
    // bullet-time flying kick
    out.places.push(kid(cam, 1.6, 1.0, 10.4, {
      kind: "hero", expr: "stern", mode: "kick", blink: 0, gaze: 0.7, aura: true, eyeFire: true,
    }));
    blob(out, 1.6, 1.0, 10.4, 1.0, 1, "lab");
    out.places.push(kid(cam, 2.5, 0, 10.9, { kind: "terror", expr: "shock", mode: "stand", blink: 0, gaze: -0.7, prop: "rifle", hurt: false }));
    blob(out, 2.5, 0, 10.9, 1.05, 1, "lab");
    const su = q(clamp01((f - ORBIT2_AT) / 100), 24);
    out.fx.push({ key: `speed8${su}`, cw: 600, ch: 600, draw: fxSpeed(su), x: 2.4, y: 1.4, z: 10.4, w: 2.0, h: 2.0, soft: true, opacity: 0.5 });
  } else {
    // wall slam + K.O.
    const su = clamp01((f - SLAM2_AT) / 30);
    out.places.push(kid(cam, 4.4, 0, 10.6, { kind: "hero", expr: "grin", mode: "punch", blink: 0, gaze: 0.85, aura: true, eyeFire: true }));
    blob(out, 4.4, 0, 10.6, 1.05, 1, "lab");
    out.places.push(kid(cam, 6.0, 0, 10.9, { kind: "terror", expr: "pained", mode: "slump", blink: 0, gaze: -0.8, prop: "none", hurt: true }));
    blob(out, 6.0, 0, 10.9, 1.0, 1, "lab");
    out.fx.push({ key: `impact2${q(su, 20)}`, cw: 700, ch: 700, draw: fxImpact("K.O.", "#ffb03a", q(su, 20)), x: 5.6, y: 1.6, z: 10.9, w: 2.0, h: 2.0, soft: true, opacity: su < 1 ? 1 : 0 });
    if (f > SLAM2_AT + 20) {
      const ku = q(clamp01((f - SLAM2_AT - 20) / 55), 24);
      out.fx.push({ key: `ko7${ku}`, cw: 420, ch: 420, draw: fxKO(ku), x: 5.9, y: 2.0, z: 11.0, w: 0.9, h: 0.9, soft: true });
    }
  }
};

// ---------------- shot 8: hero line, crush, tears (2355-2760) ----------------
const s8 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const tears = f >= TEARS_AT;
  out.places.push(kid(cam, HALL.line[0], 0, HALL.line[2], {
    kind: "hero", expr: f < CRUSH_AT ? "smug" : "grin", mode: f < CRUSH_AT ? "pointSelf" : "stand",
    blink: lidAt(t, 11), gaze: f < CRUSH_AT ? -0.15 : 0.15, talk: f < CRUSH_AT ? talkAt(f) : 0, aura: false,
  }));
  blob(out, HALL.line[0], 0, HALL.line[2], 1.05, 1, "hall");
  out.places.push(kid(cam, HALL.crush[0], 0, HALL.crush[2], {
    kind: "crush", expr: tears ? "laugh" : "smile", mode: tears ? "clap" : "stand", blink: lidAt(t, 41),
    gaze: -0.85, starEyes: true, blush: true,
  }));
  blob(out, HALL.crush[0], 0, HALL.crush[2], 1.0, 1, "hall");
  out.places.push(kid(cam, -1.2, 0, 12.2, {
    kind: "hoodie", expr: tears ? "cry" : "relief", mode: tears ? "cheer" : "stand", blink: 0,
    gaze: 0.35, tears: tears ? 1 : 0, prop: tears ? "thumbs" : "none",
  }));
  blob(out, -1.2, 0, 12.2, 1.05, 1, "hall");
  out.places.push(kid(cam, -2.2, 0, 12.8, {
    kind: "muscle", expr: tears ? "laugh" : "grin", mode: tears ? "clap" : "stand", blink: lidAt(t, 23), gaze: 0.55,
  }));
  blob(out, -2.2, 0, 12.8, 1.1, 1, "hall");
  out.places.push(kid(cam, 2.6, 0, 13.6, { kind: "terror", expr: "pained", mode: "kneel", blink: 0, gaze: -0.6, tied: true, prop: "none" }));
  blob(out, 2.6, 0, 13.6, 0.95, 1, "hall");
  if (f >= CRUSH_AT) {
    const hu = q((f / 40) % 1, 24);
    out.fx.push({ key: `hearts8${hu}`, cw: 520, ch: 520, draw: fxHearts(hu, 4), x: HALL.crush[0], y: 1.72, z: HALL.crush[2] - 0.2, w: 1.05, h: 1.05, soft: true });
  }
};

// ---------------- shot 9: courtyard, salute, pose (2760-3135) ----------------
const s9 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const u = smooth((f - EXIT_AT) / (SALUTE_AT - EXIT_AT));
  const pose = f >= POSE_AT;
  const hz = lerp(20.0, 15.0, u);
  const walk = f < SALUTE_AT;
  out.places.push(kid(cam, 0.4, 0, hz, {
    kind: "hero", expr: pose ? "laugh" : "smug", mode: pose ? "cheer" : walk ? "walk" : "stand",
    phase: walk ? q((f / FPS) * 1.5 % 1, 30) : 0, blink: lidAt(t, 11), gaze: pose ? 0 : -0.2, shades: f < SALUTE_AT,
  }));
  blob(out, 0.4, 0, hz, 1.05, 1, "plaza");
  const mz = lerp(21.0, 16.6, u), wz = lerp(21.2, 17.0, u);
  out.places.push(kid(cam, -0.8, 0, mz, {
    kind: "muscle", expr: pose ? "laugh" : "grin", mode: pose ? "cheer" : walk ? "walk" : "stand",
    phase: walk ? q((f / FPS) * 1.5 % 1 + 0.4, 30) : 0, blink: lidAt(t, 23), gaze: 0.1,
  }));
  blob(out, -0.8, 0, mz, 1.1, 1, "plaza");
  out.places.push(kid(cam, 2.0, 0, wz, {
    kind: "hoodie", expr: pose ? "grin" : "smile", mode: pose ? "cheer" : walk ? "walk" : "stand",
    phase: walk ? q((f / FPS) * 1.5 % 1 + 0.7, 30) : 0, blink: lidAt(t, 31), gaze: 0.1, prop: pose ? "thumbs" : "none",
  }));
  blob(out, 2.0, 0, wz, 1.05, 1, "plaza");
  // two captured gunmen dragged out of the doors
  for (const [i, x, z] of [[0, -2.6, 21.2], [1, 3.2, 21.5]] as const) {
    out.places.push(kid(cam, x, 0, z - 1.4 * u, {
      kind: "terror", expr: "pained", mode: "kneel", blink: 0, gaze: -0.4, tied: true, prop: "none", hurt: i === 0,
    }));
    blob(out, x, 0, z - 1.4 * u, 0.9, 1, "plaza");
  }
  // police + SWAT + press + principal lining the barrier
  out.places.push(kid(cam, COURT.police[0], 0, COURT.police[2], { kind: "cop", expr: "stern", mode: f >= SALUTE_AT ? "salute" : "stand", blink: lidAt(t, 71), gaze: 0.9 }));
  out.places.push(kid(cam, COURT.swat[0], 0, COURT.swat[2], { kind: "swat", expr: "stern", mode: "stand", blink: 0, gaze: 0.8 }));
  out.places.push(kid(cam, COURT.news[0], 0, COURT.news[2], { kind: "reporter", expr: "smile", mode: "hold", prop: "mic", blink: lidAt(t, 81), gaze: 0.6, talk: f > SALUTE_AT ? talkAt(f) : 0 }));
  out.places.push(kid(cam, COURT.news[0] + 1.1, 0, COURT.news[2] + 0.4, { kind: "reporter", expr: "smile", mode: "hold", prop: "mic", blink: lidAt(t, 91), gaze: 0.4 }));
  out.places.push(kid(cam, COURT.principal[0], 0, COURT.principal[2], { kind: "principal", expr: "smile", mode: f >= SALUTE_AT ? "salute" : "stand", blink: lidAt(t, 101), gaze: 0.4 }));
  if (f >= SALUTE_AT) {
    // press flashbulbs
    for (let i = 0; i < 3; i++) {
      const t0 = SALUTE_AT + i * 42;
      const fu = q(clamp01((f - t0) / 18), 20);
      if (f >= t0 && fu < 1) out.fx.push({
        key: `flash${i}${fu}`, cw: 420, ch: 420, draw: fxFlash(fu), x: COURT.news[0] - 0.4 + i * 0.8, y: 2.0, z: COURT.news[2] + 0.3, w: 1.1, h: 1.1, soft: true,
      });
    }
  }
};

// ---------------- shot 10: hug + chalk (3135-3360) ----------------
const s10 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  out.places.push(kid(cam, 0.1, 0, 12.2, {
    kind: "hero", expr: "relief", mode: "hug", blink: lidAt(t, 11), gaze: 0.25, blush: true,
  }));
  blob(out, 0.1, 0, 12.2, 1.05, 1, "plaza");
  out.places.push(kid(cam, 0.8, 0, 11.7, {
    kind: "crush", expr: "smile", mode: "hug", blink: lidAt(t, 41), gaze: -0.6, starEyes: true, blush: true,
  }));
  blob(out, 0.8, 0, 11.7, 1.0, 1, "plaza");
  const hu = q((f / 40) % 1, 24);
  out.fx.push({ key: `hearts10${hu}`, cw: 520, ch: 520, draw: fxHearts(hu, 5), x: 0.4, y: 1.5, z: 11.9, w: 1.4, h: 1.4, soft: true });
  if (f >= CHALK_AT) {
    // FPV chalk: it rides just ahead of the diving lens
    const u = smooth((f - CHALK_AT) / (THWACK_AT - CHALK_AT));
    const cx = lerp(1.35, 0.35, u), cy = 1.56, cz = lerp(8.9, 11.55, u);
    out.fx.push({ key: `chalk${q(u, 24)}`, cw: 440, ch: 220, draw: fxChalk(0), x: cx, y: cy, z: cz, w: 0.3 + 0.25 * u, h: 0.15 + 0.12 * u, rot: q(u, 12) });
  }
};

// ---------------- shot 11: classroom snap, bump, fan (3360-3660) ----------------
const s11 = (f: number, t: number, cam: CamInfo, out: Stage) => {
  const bump = f >= BUMP_AT;
  out.places.push(kid(cam, CLASS.hero[0], 0, 6.6, {
    kind: "hero", expr: bump ? "grin" : "pained", mode: "stand", blink: lidAt(t, 11, [THWACK_AT / FPS]),
    gaze: -0.6, hurt: f >= THWACK_AT + 6, sweat: bump ? 0.6 : f >= THWACK_AT + 10 ? 0.3 : 0,
  }));
  blob(out, CLASS.hero[0], 0, 6.6, 1.05, 1, "classroom");
  out.places.push(kid(cam, -2.0, 0, 8.4, {
    kind: "teacher", expr: "angry", mode: "point", blink: lidAt(t, 61), gaze: 0.85, talk: f > THWACK_AT + 20 ? talkAt(f) : 0,
  }));
  blob(out, -2.0, 0, 8.4, 1.0, 1, "classroom");
  out.places.push(kid(cam, 1.4, 0, 8.32, { kind: "muscle", expr: "laugh", mode: "sit", blink: lidAt(t, 23), gaze: -0.4 }));
  out.places.push(kid(cam, 4.3, 0, 8.32, { kind: "hoodie", expr: "laugh", mode: "sit", blink: lidAt(t, 31), gaze: -0.4 }));
  out.places.push(kid(cam, -4.4, 0, 8.32, { kind: "crush", expr: "smile", mode: "sit", blink: lidAt(t, 41), gaze: -0.2, blush: true }));
  // the chalk that hit him drops to the floor
  out.fx.push({ key: "chalkFloor", cw: 440, ch: 220, draw: fxChalk(0), x: -1.4, y: 0.05, z: 7.2, w: 0.16, h: 0.08, flat: true, rot: 0.5 });
};

// ---------------- stage ----------------
export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  void SHOTS[id - 1];
  findSun(cam, SUN);
  const f = Math.round(t * FPS);
  switch (id) {
    case 1: s1(f, t, cam, out); break;
    case 2: s2(f, t, cam, out); break;
    case 3: s3(f, t, cam, out); break;
    case 4: s4(f, t, cam, out); break;
    case 5: s5(f, t, cam, out); break;
    case 6: s6(f, t, cam, out); break;
    case 7: s7(f, t, cam, out); break;
    case 8: s8(f, t, cam, out); break;
    case 9: s9(f, t, cam, out); break;
    case 10: s10(f, t, cam, out); break;
    case 11: s11(f, t, cam, out); break;
  }
  return out;
};

export { FPS };
