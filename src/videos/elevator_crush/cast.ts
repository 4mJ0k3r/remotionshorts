// 2D character & FX card staging for ElevatorCrushShort (adapted from hotel_lift/cast.ts).
// Actors are yaw-billboards rendered to canvas textures via Pool. The only hand-to-3D contact is shot 5's
// FAN knob, pinned with handWorldPos (SKILL.md Section 3 Rule B, dx = 145, dy = 565, depthOffset = -0.08).
import * as THREE from "three";
import { Pen, drawCharacter, drawFx, drawFxBlob, CharOpts, FxType } from "./toon";
import {
  FPS, glide, clamp01, lerp, BHDAM_AT, RAIN_IN_AT, RAIN_BURST_AT, PHONE_AT, COUGH_AT, GROWL_AT, CABLE_AT, DROP_AT,
  HUG_AT, HEART_AT, SPARKLE_AT, WRITE_AT, PALM_AT,
} from "./story";
import { NOINK } from "./ink";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";

export const SU = 0.00216; // 1000 units = 2.16 m
export const PIV = 975;    // feet pivot in design units

// ---------------- CANVAS POOL ----------------
type Entry = { cv: HTMLCanvasElement; tex: THREE.CanvasTexture; w: number; h: number };
export type Req = { key: string; w: number; h: number; k: number; draw: (p: Pen) => void; tex?: THREE.CanvasTexture };

const makeEntry = (w: number, h: number): Entry => {
  const cv = document.createElement("canvas");
  cv.width = w; cv.height = h;
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
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
    for (const r of this.reqs) {
      const l = want.get(r.key);
      if (l) l.push(r); else want.set(r.key, [r]);
    }
    for (const [key, e] of this.live) {
      if (!want.has(key)) { this.live.delete(key); this.free.push(e); }
    }
    while (this.free.length > 8) {
      const e = this.free.shift()!;
      e.tex.dispose();
      e.cv.width = e.cv.height = 1;
    }
    for (const [key, rs] of want) {
      let e = this.live.get(key);
      if (!e) {
        const r = rs[0];
        const i = this.free.findIndex((x) => x.w === r.w && x.h === r.h);
        e = i >= 0 ? this.free.splice(i, 1)[0] : makeEntry(r.w, r.h);
        const g = e.cv.getContext("2d")!;
        g.setTransform(1, 0, 0, 1, 0, 0);
        g.clearRect(0, 0, e.w, e.h);
        g.setTransform(r.k, 0, 0, r.k, 0, 0);
        r.draw(new Pen(g));
        e.tex.needsUpdate = true;
        this.live.set(key, e);
      }
      for (const r of rs) r.tex = e.tex;
    }
    this.reqs = [];
  }
}

// ---------------- SPRITE ACTORS ----------------
const blank = (() => {
  const c = document.createElement("canvas");
  c.width = c.height = 2;
  return new THREE.CanvasTexture(c);
})();

const BODY_GEO = (() => {
  const g = new THREE.PlaneGeometry(600 * SU, 1000 * SU);
  g.translate(0, (PIV - 500) * SU, 0);
  return g;
})();

const CARD_GEO = new THREE.PlaneGeometry(1, 1);

export class Actor {
  mesh: THREE.Mesh;
  mat: THREE.MeshLambertMaterial;
  dmat: THREE.MeshDepthMaterial;
  r: Req | null = null;

  constructor(parent: THREE.Object3D) {
    this.mat = cardShade(new THREE.MeshLambertMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide }));
    this.mat.alphaToCoverage = false;
    this.dmat = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking, map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.mesh = new THREE.Mesh(BODY_GEO, this.mat);
    this.mesh.customDepthMaterial = this.dmat;
    this.mesh.onBeforeRender = (r) => {
      const rt = r.getRenderTarget();
      CARD_K.uPx.value = (rt ? rt.height : r.domElement.height) / 1920;
    };
    this.mesh.castShadow = false;
    this.mesh.receiveShadow = true;
    this.mesh.visible = false;
    this.mesh.rotation.order = "YXZ";
    this.mesh.renderOrder = 1;
    this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
  }

  bind() {
    const t = this.r?.tex;
    if (t) { this.mat.map = t; this.dmat.map = t; }
  }
}

export class Fx {
  mesh: THREE.Mesh;
  mat: THREE.MeshBasicMaterial;
  soft: THREE.MeshBasicMaterial;
  blob: THREE.MeshBasicMaterial;
  r: Req | null = null;

  constructor(parent: THREE.Object3D) {
    this.mat = new THREE.MeshBasicMaterial({ map: blank, alphaTest: 0.5, side: THREE.DoubleSide });
    this.mat.alphaToCoverage = false;
    this.soft = new THREE.MeshBasicMaterial({ map: blank, transparent: true, depthWrite: false, side: THREE.DoubleSide });
    this.blob = blobMaterial(blank);
    this.mesh = new THREE.Mesh(CARD_GEO, this.mat);
    this.mesh.visible = false;
    this.mesh.layers.set(NOINK);
    parent.add(this.mesh);
  }

  use(soft: boolean) { this.mesh.material = soft ? this.soft : this.mat; }

  bind() {
    const t = this.r?.tex;
    if (!t) return;
    if (this.r!.key.includes("|blob|")) {
      if (t.generateMipmaps) { t.generateMipmaps = false; t.minFilter = THREE.LinearFilter; t.needsUpdate = true; }
      this.blob.map = t;
      this.mesh.material = this.blob;
      this.mesh.renderOrder = 0.5;
    } else {
      this.mat.map = t;
      this.soft.map = t;
      this.mesh.renderOrder = 2;
    }
  }

  opacity(o: number) {
    this.mat.transparent = o < 0.999;
    this.mat.opacity = o;
    this.soft.opacity = o;
    this.soft.transparent = true;
    this.mesh.visible = o > 0.001;
  }
}

// ---------------- PLACEMENTS ----------------
export type Place = {
  key: string;
  draw: (p: Pen) => void;
  x: number; y: number; z: number;
  scale?: number;
  size?: [number, number, number];
};

export type FxPlace = {
  key: string;
  cw: number; ch: number;
  draw: (p: Pen) => void;
  x: number; y: number; z: number;
  w: number; h: number;
  flat?: boolean;
  soft?: boolean;
  opacity?: number;
};

export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3 };
export type Stage = { places: Place[]; fx: FxPlace[] };

export const q2 = (v: number) => Math.round(v * 50) / 50; // 0.02 steps (SKILL.md Section 2)

/** Resolution tier by camera distance */
const tier = (d: number): [number, number, number] =>
  d < 3.5 ? [1200, 2000, 2.0] : d < 7.0 ? [900, 1500, 1.5] : [600, 1000, 1.0];

export const HERO_SCALE = 0.92;
export const CRUSH_SCALE = 0.86;
const tmp = new THREE.Vector3();

const Q_KEYS: (keyof CharOpts)[] = [
  "gaze", "gazeY", "blush", "toward", "waveP", "phoneP", "btnPressP", "heartBeatP", "beat", "growlP", "comfortP",
  "palmP", "numP", "fixHairP", "hugP", "writePalmP",
];

const makeChar = (cam: CamInfo, x: number, y: number, z: number, opts: CharOpts, scale: number): Place => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.0 * scale, z)) / scale;
  const [w, h, k] = tier(d);
  const qOpts: CharOpts = { ...opts };
  const rec = qOpts as Record<string, unknown>;
  for (const key of Q_KEYS) {
    const v = rec[key];
    if (typeof v === "number") rec[key] = q2(v);
  }
  return {
    key: `CH|${JSON.stringify(qOpts)}`,
    x, y, z, scale,
    size: [w, h, k],
    draw: (p) => drawCharacter(p.g, qOpts),
  };
};

const blob = (out: Stage, x: number, z: number, sc = 1.0) => {
  out.fx.push({
    key: "blob|mul",
    cw: 128, ch: 128,
    draw: (p) => drawFxBlob(p.g),
    x, y: 0.012, z,
    w: 0.65 * sc, h: 0.46 * sc,
    flat: true,
  });
};

const fx = (out: Stage, type: FxType, u: number, x: number, y: number, z: number, size: number, soft = true, opacity = 1) => {
  const qu = q2(u);
  out.fx.push({
    key: `fx_${type}_${qu}`,
    cw: 400, ch: 400,
    draw: (p) => drawFx(p.g, type, qu),
    x, y, z, w: size, h: size, soft, opacity,
  });
};

/** Burst progress for an FX that fires at `at` and lasts `dur` frames, or null when inactive */
const burst = (f: number, at: number, dur: number) => (f >= at && f < at + dur ? (f - at) / dur : null);

/** Parabolic hop (m) after an impact */
const jolt = (f: number, at: number, h: number, dur = 16) => {
  if (f < at || f >= at + dur) return 0;
  const u = (f - at) / dur;
  return 4 * u * (1 - u) * h;
};

/** 160 BPM heartbeat pulse (0..1), ~11 frames per beat */
const beatAt = (f: number) => {
  const ph = (f % 11) / 11;
  return ph < 0.35 ? 1 - ph / 0.35 : 0;
};

// ---------------- 2D-TO-3D HAND PINNING (SKILL.md Section 3 Rule B) ----------------
export const handWorldPos = (
  camPos: THREE.Vector3,
  charPos: [number, number, number],
  scale: number,
  dx: number,
  dy: number,
  depthOffset = -0.08,
  out = new THREE.Vector3()
): THREE.Vector3 => {
  const [cx, cy, cz] = charPos;
  const yaw = Math.atan2(camPos.x - cx, camPos.z - cz);
  const rightX = Math.cos(yaw), rightZ = -Math.sin(yaw);
  const fwdX = Math.sin(yaw),   fwdZ = Math.cos(yaw);
  const localX = (dx - 300) * SU * scale;
  const localY = (PIV - dy) * SU * scale;
  return out.set(
    cx + rightX * localX + fwdX * depthOffset,
    cy + localY,
    cz + rightZ * localX + fwdZ * depthOffset
  );
};

// Shot 5 staging constants shared with world.ts (Rule B pin)
export const HERO_S5: [number, number, number] = [1.55, 0.0, -1.4];
export const FIST_DX = 145, FIST_DY = 565;

// ---------------- SHOT STAGING ----------------
type V3 = [number, number, number];
const vlerp = (a: V3, b: V3, t: number): V3 => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];

export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const f = Math.round(t * FPS);
  const hero = (p: V3, o: Omit<CharOpts, "role">) => {
    out.places.push(makeChar(cam, p[0], p[1], p[2], { role: "hero", ...o }, HERO_SCALE));
    blob(out, p[0], p[2], 1.1);
  };
  const crush = (p: V3, o: Omit<CharOpts, "role">) => {
    out.places.push(makeChar(cam, p[0], p[1], p[2], { role: "crush", ...o }, CRUSH_SCALE));
    blob(out, p[0], p[2], 1.0);
  };

  if (id === 1) {
    // Hook: both trapped, doors sliding shut (world.ts). Soft pink aura around the crush.
    const shock = f >= 105;
    hero([-0.4, 0, 1.5], { expr: shock ? "panicShock" : "nervous", gaze: shock ? 0.2 : 0.7, gazeY: shock ? -0.1 : 0.1, toward: 1, blush: 0.4 });
    const cp: V3 = [0.42, 0, 1.15];
    fx(out, "aura", (f % 120) / 120, cp[0], 1.25, cp[2] - 0.08, 1.4, true, 0.75);
    crush(cp, { expr: "shy", gaze: -0.6, gazeY: 0.2, blush: 0.7, toward: -1 });
  } else if (id === 2) {
    // Alone in the lift; at RAIN_IN_AT the doors bounce open and the rain-soaked crush rushes in.
    const arrived = f >= 290;
    hero([-0.45, 0, 0.9], { expr: arrived ? "panicShock" : "neutral", gaze: 0.7, gazeY: arrived ? 0 : 0.3, toward: 1, blush: arrived ? 0.6 : 0 });
    if (f >= 262) {
      const a: V3 = [1.6, 0, -3.7], m: V3 = [0.15, 0, -2.5], e: V3 = [0.42, 0, 1.25];
      let p = f < RAIN_IN_AT + 5 ? vlerp(a, m, glide(f, 262, RAIN_IN_AT + 5)) : vlerp(m, e, glide(f, RAIN_IN_AT + 5, 335));
      const moving = f < 335;
      if (moving) p = [p[0], Math.abs(Math.sin(f * 0.55)) * 0.05, p[2]];
      crush(p, { expr: f < 335 ? "nervous" : "shy", gaze: -0.5, blush: f < 335 ? 0.2 : 0.6, toward: -1, rainDrops: true });
      const u = burst(f, RAIN_BURST_AT, 30);
      if (u !== null) fx(out, "drops", u, p[0], 1.3, p[2] + 0.1, 1.3);
      const s = burst(f, RAIN_BURST_AT, 40);
      if (s !== null) fx(out, "sparkle", s, p[0], 1.45, p[2] - 0.12, 1.5);
    }
  } else if (id === 3) {
    // Heart racing, then BHADAAM! power cut: both jolt +0.18 m, sparks burst from the ceiling lights.
    const cut = f >= BHDAM_AT;
    const jy = jolt(f, BHDAM_AT, 0.18);
    hero([-0.4, jy, 1.3], {
      expr: cut ? (f < BHDAM_AT + 60 ? "panicShock" : "nervous") : "nervous",
      gaze: cut ? 0 : 0.6, gazeY: cut ? -0.7 : 0.1, toward: 1, blush: cut ? 0.1 : 0.6,
      heartBeatP: cut ? 0 : glide(f, 405, 425), beat: cut ? 0 : beatAt(f),
    });
    crush([0.42, jolt(f, BHDAM_AT + 2, 0.16), 0.95], {
      expr: cut ? (f < BHDAM_AT + 60 ? "panicShock" : "nervous") : "neutral",
      gaze: cut ? 0 : -0.3, gazeY: cut ? -0.7 : 0.4, toward: -1,
    });
    const u = burst(f, BHDAM_AT, 24);
    if (u !== null) {
      fx(out, "sparks", u, -0.55, 2.9, -1.55, 1.6);
      fx(out, "sparks", Math.min(1, u * 1.1), 0.55, 2.9, -1.55, 1.6);
    }
  } else if (id === 4) {
    // Hour 1: opposite walls, awkward silence; both raise phones — NO SIGNAL.
    const ph = glide(f, PHONE_AT, PHONE_AT + 30);
    hero([-0.6, 0, 0.7], { expr: "nervous", sweat: true, gaze: lerp(-0.6, 0.6, ph), gazeY: lerp(0, 0.6, ph), toward: 1, phoneP: ph });
    crush([0.6, 0, 0.95], { expr: ph > 0.5 ? "neutral" : "shy", gaze: lerp(0.6, -0.6, ph), gazeY: lerp(0.2, 0.6, ph), toward: -1, phoneP: ph, blush: 0.3 });
  } else if (id === 5) {
    // Crush fixes her hair in the front-left corner; hero stares at the brass floor buttons (Rule B fist).
    const fix = glide(f, 915, 960) * (0.85 + 0.15 * Math.sin(f * 0.12));
    crush([-1.15, 0, -0.8], { expr: "shy", gaze: 0.7, gazeY: 0.1, toward: 1, fixHairP: fix, blush: 0.5 });
    hero(HERO_S5, { expr: "nervous", gaze: -0.8, gazeY: 0.3, toward: -1, btnPressP: glide(f, 1040, 1075), sweat: true });
  } else if (id === 6) {
    // Dry throat cough, then the loud stomach growl.
    const cough = f >= COUGH_AT && f < COUGH_AT + 42;
    const growl = glide(f, GROWL_AT - 5, GROWL_AT + 17);
    hero([0.15, 0, 1.35], {
      expr: growl > 0.3 ? "strain" : cough ? "strain" : "nervous",
      gaze: -0.4, gazeY: 0.2, toward: -1, growlP: growl, blush: growl, sweat: true,
    });
    const c = burst(f, COUGH_AT, 30);
    if (c !== null) fx(out, "dust", c, 0.02, 1.42, 1.5, 0.5);
    crush([-0.55, 0, 0.25], {
      expr: f >= GROWL_AT + 5 && f < GROWL_AT + 60 ? "panicShock" : f >= GROWL_AT + 60 ? "confidentSmile" : "neutral",
      gaze: f >= GROWL_AT ? 0.7 : 0.2, gazeY: 0.1, toward: 1, blush: 0.3,
    });
  } else if (id === 7) {
    // Hour 2: cables grind (sparks at the hatch), then the 2-foot drop: both bounce +0.25 m.
    const scared = f >= CABLE_AT;
    const jh = jolt(f, DROP_AT, 0.25, 18);
    hero([-0.42, jh, 1.2], { expr: scared ? "panicShock" : "nervous", gaze: 0.1, gazeY: -0.8, toward: 1, sweat: true });
    crush([0.45, jolt(f, DROP_AT + 2, 0.22, 18), 0.9], { expr: scared ? "panicShock" : "nervous", gaze: -0.1, gazeY: -0.8, toward: -1 });
    const u = burst(f, CABLE_AT, 26);
    if (u !== null) fx(out, "sparks", u, 0, 3.7, 0.5, 1.6);
    const d = burst(f, DROP_AT, 24);
    if (d !== null) fx(out, "sparks", d, 0.15, 3.7, 0.5, 1.9);
  } else if (id === 8) {
    // She runs straight into his chest (hug), heart burst; then his 160 BPM heartbeat.
    const run = glide(f, 1818, 1880);
    const cp = vlerp([0.75, 0, 1.1], [0.28, 0, 1.58], run);
    if (run < 1) cp[1] = Math.abs(Math.sin(f * 0.5)) * 0.04;
    const hug = glide(f, 1860, 1890);
    const hugged = f >= HUG_AT;
    hero([-0.15, 0, 1.4], {
      expr: "panicShock", gaze: 0.5, gazeY: 0.3, toward: 1, blush: hugged ? 1 : 0.2,
      heartBeatP: glide(f, HEART_AT - 5, HEART_AT + 10), beat: f >= HEART_AT ? beatAt(f) : 0,
    });
    crush(cp, { expr: hugged ? "shy" : "panicShock", gaze: -0.6, gazeY: 0.2, toward: -1, hugP: hug, blush: hugged ? 0.8 : 0 });
    const h = burst(f, HUG_AT, 36);
    if (h !== null) fx(out, "hearts", h, 0.0, 1.55, 1.7, 1.3);
  } else if (id === 9) {
    // Trembling hands on her shoulders -> "safety brakes are locked, nothing will happen to you."
    const calm = f >= 2331;
    const tremble = calm ? 0 : Math.sin(f * 1.7) * 0.004;
    hero([-0.3 + tremble, 0, 1.35], { expr: calm ? "confidentSmile" : "nervous", gaze: 0.5, gazeY: 0.3, toward: 1, comfortP: glide(f, 2200, 2250), blush: 0.6 });
    crush([0.26, 0, 1.58], { expr: calm ? "shy" : "nervous", gaze: -0.6, gazeY: 0, toward: -1, hugP: 1, blush: 0.7 });
    const s = burst(f, 2331, 70);
    if (s !== null) fx(out, "stars", s, 0.0, 1.95, 1.2, 1.9);
  } else if (id === 10) {
    // Dim light returns; she doesn't let go — then lifts her head: eye contact, awkwardness gone.
    const look = f >= 2631;
    hero([-0.3, 0, 1.35], { expr: look ? "confidentSmile" : "shy", gaze: 0.5, gazeY: 0.3, toward: 1, comfortP: 1, blush: 0.8 });
    crush([0.26, 0, 1.58], { expr: look ? "confidentSmile" : "shy", gaze: look ? -0.7 : -0.4, gazeY: look ? -0.6 : 0.4, toward: -1, hugP: 1, blush: 0.8 });
    const s = burst(f, SPARKLE_AT, 60);
    if (s !== null) fx(out, "stars", s, 0.0, 1.95, 1.2, 1.9);
  } else {
    // Cliffhanger: she writes a secret on his palm -> "98XXXXXX??" -> COMMENT PART 2.
    const write = f < 3025 ? glide(f, 2850, 2900) : 1 - glide(f, 3025, 3060);
    const wiggle = f >= 2900 && f < WRITE_AT ? Math.sin(f * 0.9) * 0.08 : 0;
    const palm = glide(f, 2850, 2890);
    const num = clamp01((f - 2905) / (WRITE_AT - 2905));
    const reveal = f >= PALM_AT;
    const wave = glide(f, 3206, 3236);
    hero([-0.3, 0, 1.3], {
      expr: f < WRITE_AT ? "nervous" : reveal ? "confidentSmile" : "panicShock",
      gaze: f < 3206 ? 0.8 : 0, gazeY: f < 3206 ? 0.6 : 0, toward: 1, blush: 0.6,
      palmP: palm, numP: num, cyanEyes: reveal, waveP: wave,
    });
    crush([0.3, 0, 1.5], {
      expr: f < 3206 ? "shy" : "confidentSmile", gaze: f < 3206 ? -0.7 : 0, gazeY: f < 3206 ? 0.6 : 0, toward: -1,
      writePalmP: clamp01(write + wiggle), blush: 0.6, waveP: wave,
    });
    if (f >= 2860 && f < WRITE_AT) fx(out, "cyan", ((f - 2860) % 80) / 80, 0.0, 1.08, 1.62, 0.45, true, 0.85);
    const r = burst(f, PALM_AT, 40);
    if (r !== null) fx(out, "cyan", r, 0.0, 1.08, 1.62, 0.7);
    if (f >= 3206) fx(out, "stars", ((f - 3206) % 70) / 70, 0.0, 2.05, 1.1, 2.0, true, 0.9);
  }

  return out;
};
