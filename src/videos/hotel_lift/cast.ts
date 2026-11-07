// 2D Character & FX Card staging for HotelLiftShort.
// Actors are yaw-billboards rendered to canvas textures via Pool.
// Pinned 3D-contact points follow SKILL.md Section 3 Rule B.
import * as THREE from "three";
import { Pen, drawCharacter, drawFx, drawFxBlob, CharOpts, FxType } from "./toon";
import { FPS, glide, clamp01 } from "./story";
import { NOINK } from "./ink";
import { cardShade, blobMaterial, CARD_K } from "./cardshade";
import { LIGHTS, LightName } from "./lights";
import { makeBlobTexture } from "./paint";

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
  // Quantize all continuous numeric parameters in key
  const qOpts = {
    ...opts,
    crankP: opts.crankP !== undefined ? q2(opts.crankP) : undefined,
    whistleP: opts.whistleP !== undefined ? q2(opts.whistleP) : undefined,
    teaP: opts.teaP !== undefined ? q2(opts.teaP) : undefined,
    billP: opts.billP !== undefined ? q2(opts.billP) : undefined,
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
    // Shot 1: Guest drinking tea on wooden sidewalk platform at x = 1.4, y = 0, z = 3.8
    const guestPos: [number, number, number] = [1.4, 0.0, 3.8];
    const isShocked = f >= 24; // Switches to shock when hotel begins lift
    out.places.push(makeChar(cam, guestPos[0], guestPos[1], guestPos[2], {
      role: "guest",
      expr: isShocked ? "panicShock" : "confidentSmile",
      gaze: isShocked ? -0.7 : -0.2,
      gazeY: isShocked ? 0.3 : 0.0,
      teaP: 1.0,
    }));
    blob(out, guestPos[0], guestPos[1], guestPos[2], 1.2);

    // Dust puffs along trench foundation when building rises (f = 20..50)
    if (f >= 20 && f <= 50) {
      const u = (f - 20) / 30;
      out.fx.push({
        key: `dust_s1_${q2(u)}`,
        cw: 500, ch: 400,
        draw: (p) => drawFx(p.g, "dust", u),
        x: -0.6, y: 0.1, z: 0.8,
        w: 3.2, h: 2.2,
        soft: true, opacity: 0.85,
      });
      out.fx.push({
        key: `dust_s1_b_${q2(u)}`,
        cw: 500, ch: 400,
        draw: (p) => drawFx(p.g, "dust", u),
        x: 0.8, y: 0.1, z: 0.8,
        w: 2.8, h: 2.0,
        soft: true, opacity: 0.85,
      });
    }
  } else if (id === 2) {
    // Shot 2: Engineer George Pullman in timber trench at x = 0.28, y = 0, z = 0.8
    const engPos: [number, number, number] = [0.28, 0.0, 0.8];

    let crankP = 0.0;
    let expr: CharOpts["expr"] = "confidentSmile";
    if (f < 131) {
      crankP = 0.0;
      expr = "confidentSmile";
    } else if (f <= 155) {
      crankP = clamp01((f - 131) / 21); // Cranks 0 -> 1 over 131..152
      expr = "strainGrin"; // Squinting > < eyes, V-brows, clenched teeth
    } else {
      crankP = 1.0;
      expr = "confidentSmile";
    }

    out.places.push(makeChar(cam, engPos[0], engPos[1], engPos[2], {
      role: "engineer",
      expr,
      crankP,
      gaze: -0.4,
      gazeY: -0.2,
    }));
    blob(out, engPos[0], engPos[1], engPos[2], 1.25);

    // Spark burst when screw bites and beam lifts (f = 142..156)
    if (f >= 142 && f <= 156) {
      const u = (f - 142) / 14;
      out.fx.push({
        key: `sparks_s2_${q2(u)}`,
        cw: 400, ch: 400,
        draw: (p) => drawFx(p.g, "sparks", u),
        x: 0.05, y: 0.85, z: 0.8,
        w: 1.4, h: 1.4,
        soft: true,
      });
    }
  } else {
    // Shot 3: Guest on boardwalk plaza at x = 0.55, y = 0, z = 2.0
    const guestPos: [number, number, number] = [0.55, 0.0, 2.0];

    const billP = f < 236 ? 0.0 : clamp01((f - 236) / 12);
    out.places.push(makeChar(cam, guestPos[0], guestPos[1], guestPos[2], {
      role: "guest",
      expr: "confidentSmile",
      gaze: -0.3,
      gazeY: 0.0,
      billP,
    }));
    blob(out, guestPos[0], guestPos[1], guestPos[2], 1.2);

    // Dust & celebration burst when hotel locks onto piers at f = 235
    if (f >= 235 && f <= 255) {
      const u = (f - 235) / 20;
      out.fx.push({
        key: `dust_s3_${q2(u)}`,
        cw: 500, ch: 400,
        draw: (p) => drawFx(p.g, "dust", u),
        x: -0.8, y: 0.4, z: -10.0,
        w: 8.0, h: 4.5,
        soft: true, opacity: 0.9,
      });
      out.fx.push({
        key: `sparks_s3_${q2(u)}`,
        cw: 400, ch: 400,
        draw: (p) => drawFx(p.g, "sparks", u),
        x: 0.8, y: 0.8, z: -9.5,
        w: 4.0, h: 4.0,
        soft: true,
      });
    }
  }

  return out;
};
