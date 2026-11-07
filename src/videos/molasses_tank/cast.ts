// 2D Character & FX Card staging for MolassesTankShort.
// Actors are yaw-billboards rendered to canvas textures via Pool.
// Pinned 3D-contact points follow SKILL.md Section 3 Rule B.
import * as THREE from "three";
import { Pen, drawCharacter, drawFx, drawFxBlob, CharOpts, FxType } from "./toon";
import { FPS, glide, clamp01 } from "./story";
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
      if (!want.has(key)) {
        this.live.delete(key);
        this.free.push(e);
      }
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
    if (t) {
      this.mat.map = t;
      this.dmat.map = t;
    }
  }

  opacity(o: number) {
    this.mat.transparent = o < 0.999;
    this.mat.opacity = o;
    this.mat.needsUpdate = true;
    this.mesh.visible = o > 0.001;
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

  use(soft: boolean) {
    this.mesh.material = soft ? this.soft : this.mat;
  }

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
  yaw?: number;
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

const q2 = (v: number) => Math.round(v * 50) / 50; // Quantize to 0.02 (SKILL.md Section 2)

/** Resolution tier by camera distance */
const tier = (d: number): [number, number, number] =>
  d < 3.5 ? [1200, 2000, 2.0] : d < 7.0 ? [900, 1500, 1.5] : [600, 1000, 1.0];

const ACTOR_SCALE = 0.92;
const tmp = new THREE.Vector3();

const makeChar = (cam: CamInfo, x: number, y: number, z: number, opts: CharOpts, scale = ACTOR_SCALE): Place => {
  const d = cam.pos.distanceTo(tmp.set(x, y + 1.0 * scale, z)) / scale;
  const [w, h, k] = tier(d);
  const qOpts = {
    ...opts,
    brakeP: opts.brakeP !== undefined ? q2(opts.brakeP) : undefined,
    boardP: opts.boardP !== undefined ? q2(opts.boardP) : undefined,
    cardP: opts.cardP !== undefined ? q2(opts.cardP) : undefined,
    gaze: opts.gaze !== undefined ? q2(opts.gaze) : undefined,
    gazeY: opts.gazeY !== undefined ? q2(opts.gazeY) : undefined,
  };
  return {
    key: `CH|${JSON.stringify(qOpts)}`,
    x, y, z, scale,
    size: [w, h, k],
    draw: (p) => drawCharacter(p.g, qOpts),
  };
};

const blob = (out: Stage, x: number, y: number, z: number, sc = 1.0) => {
  out.fx.push({
    key: "blob|mul",
    cw: 128, ch: 128,
    draw: (p) => drawFxBlob(p.g),
    x, y: y + 0.012, z,
    w: 0.65 * sc, h: 0.46 * sc,
    flat: true,
  });
};

// ---------------- 2D-TO-3D HAND PINNING FORMULA (SKILL.md Section 3 Rule B) ----------------
/**
 * Computes exact 3D world position of a 2D design-space point (dx, dy) on a yaw billboard card.
 * Uses depthOffset = -0.08 (8 cm behind card plane) so 2D fist cleanly covers 3D handle at all angles!
 */
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

// ---------------- SHOT STAGING ----------------
export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const f = Math.round(t * FPS);

  if (id === 1) {
    // Shot 1: Inspector on right wooden boardwalk at x = 1.4, y = 0, z = 3.8
    const inspPos: [number, number, number] = [1.4, 0.0, 3.8];
    const isShocked = f >= 24; // Switches to shock when tank belly bulges & rivets pop
    out.places.push(makeChar(cam, inspPos[0], inspPos[1], inspPos[2], {
      role: "inspector",
      expr: isShocked ? "panicShock" : "calmSmile",
      boardP: 1.0,
      gaze: isShocked ? -0.8 : -0.3,
      gazeY: 0.2,
    }));
    blob(out, inspPos[0], inspPos[1], inspPos[2], 1.0);

    // Amber-brown syrup burst jet nozzle popping at f = 20..50
    if (f >= 20 && f <= 50) {
      const pr = (f - 20) / 30;
      out.fx.push({
        key: `syrup|${q2(pr)}`,
        cw: 600, ch: 600,
        draw: (p) => drawFx(p.g, "syrup", pr),
        x: -0.6, y: 3.2, z: 2.2,
        w: 2.4, h: 2.4,
        soft: true,
      });
    }

    // Ground dust / steam puff at tank base
    if (f >= 22 && f <= 54) {
      const pr = (f - 22) / 32;
      out.fx.push({
        key: `dust|${q2(pr)}`,
        cw: 600, ch: 600,
        draw: (p) => drawFx(p.g, "dust", pr),
        x: 0.0, y: 0.8, z: 2.6,
        w: 3.2, h: 2.2,
        soft: true,
      });
    }

    return out;
  }

  if (id === 2) {
    // Shot 2: Conductor in streetcar cab platform at x = 0.28, y = 0, z = 0.8
    const condPos: [number, number, number] = [0.28, 0.0, 0.8];
    // Brake pull progress: cranks 0 -> 1 over f = 131..155
    const brakeP = f < 131 ? 0 : f > 155 ? 1 : glide(f, 131, 155);
    const expr = f < 131 ? "panicShock" : "strainGrin";

    out.places.push(makeChar(cam, condPos[0], condPos[1], condPos[2], {
      role: "conductor",
      expr,
      brakeP,
      gaze: -0.7,
      gazeY: -0.2,
    }));
    blob(out, condPos[0], condPos[1], condPos[2], 0.95);

    // Sparks when brake hits emergency collar at f = 142..162
    if (f >= 142 && f <= 162) {
      const pr = (f - 142) / 20;
      out.fx.push({
        key: `sparks|${q2(pr)}`,
        cw: 600, ch: 600,
        draw: (p) => drawFx(p.g, "sparks", pr),
        x: -0.15, y: 0.72, z: 0.8,
        w: 1.5, h: 1.5,
        soft: true,
      });
    }

    return out;
  }

  // Shot 3: Conductor in plaza at x = 0.55, y = 0, z = 2.0
  const condPos: [number, number, number] = [0.55, 0.0, 2.0];
  const cardP = f < 236 ? 0 : f > 250 ? 1 : glide(f, 236, 250);
  const expr = f < 235 ? "panicShock" : "calmSmile";

  out.places.push(makeChar(cam, condPos[0], condPos[1], condPos[2], {
    role: "conductor",
    expr,
    cardP,
    gaze: -0.4,
    gazeY: 0.1,
  }));
  blob(out, condPos[0], condPos[1], condPos[2], 1.0);

  // Syrup wave crash dust and syrup splashes on background trestle at f = 235..265
  if (f >= 235 && f <= 265) {
    const pr = (f - 235) / 30;
    out.fx.push({
      key: `dust_crash|${q2(pr)}`,
      cw: 600, ch: 600,
      draw: (p) => drawFx(p.g, "dust", pr),
      x: 0.0, y: 3.5, z: -10.0,
      w: 4.8, h: 3.2,
      soft: true,
    });
    out.fx.push({
      key: `syrup_splash|${q2(pr)}`,
      cw: 600, ch: 600,
      draw: (p) => drawFx(p.g, "syrup", pr),
      x: -0.6, y: 4.2, z: -11.0,
      w: 3.6, h: 3.6,
      soft: true,
    });
  }

  return out;
};
