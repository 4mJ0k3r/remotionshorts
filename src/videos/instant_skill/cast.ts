// 2D cards for InstantSkillShort: every character is a yaw-billboard canvas card lit by cardShade, every effect is
// an unlit 2D card, and both live on layer NOINK so the world ink pass never outlines them (SKILL.md Section 1).
//
// One rule shapes the whole file: nothing here may be a discrete pose swap. `stage()` is a pure function of frame
// number that emits continuous 0..1 parameters (phoneP, boardP, reachP, slumpP, ...), each quantised to a 0.02 step
// so the Pool can cache the drawing. The one place a 2D card has to touch real 3D geometry is shot 5, where the
// hero's fist pins the Grandmaster's black king; that contact is solved by handWorldPos() below, which is the exact
// inverse of the billboard transform world.ts uses to place the card, so the fist stays welded to the piece at
// every camera angle (SKILL.md Section 3 Rule B).
import * as THREE from "three";
import { drawBubble, drawCharacter, drawFx, drawGlove, fxBlob, HERO_CODE, HERO_FIST, Pen } from "./toon";
// KidOpts is type-only, so scripts/is_cast.mjs can load this module under Node's type stripping: as a value import
// it would throw "does not provide an export named 'KidOpts'" long before any pixel renders.
import type { KidOpts } from "./toon";
import {
  APEX_AT, AVAL_AT, AVAL_HIT_AT, BLIND_AT, BENCH_AT, BRAIN, BREAK_AT, BURIED_AT, CABIN, CAR_IN_AT, CAR_STOP_AT,
  CASH_END_AT, CASH_SPARK_AT, CASH_START_AT, CHESS, CHOICE_AT, CLAP_AT, CODE_AT, CODE_END_AT, COVER_AT,
  CUBE_SLAM_AT, CUBE_START_AT, DATA_AT, DEFLATE_AT, DESPAIR_AT, DIG_AT, DIG_END_AT, DISBELIEF_AT, DOOR_AT, DROP_AT,
  FINAL_THUMBS_AT, FLIP_START_AT, FPS, GESTURE_AT, GLOW_AT, GLOW_END, GM_SHOCK_AT, GRIP_FAIL_AT, GUITAR_AT,
  HIGHWAY, JAW_AT, KING_FALL_AT,
  LAND_AT, LEAVE_AT, LEAVE_END_AT, LOOP_AT, LOOP_AT2, LOOP_AT3, NOFORGET_AT, OVERHEAT_AT, OVERHEAT_END_AT,
  PAIN_AT, PAIN_END, POINT_AT, POKER, PROTEST_AT, REACH_END_AT, REACH_START_AT, RELIEF_AT, RIFF_AT, ROAD,
  SEAT_PAN, SHADES_AT, SKATE, SLUMP_AT, SMUG_AT, SNOW, SNOW_LAND_AT, SOLVE_AT, SPEED_AT, SPEED_END_AT,
  SPLIT_AT, SPLIT_END_AT, STARS_AT, THUMBS_AT, UFO_AT, UNBLIND_AT, avalPos, buriedFriend, carRoll, clamp01, glide,
  lerp, seatDrop, seg, snowAir, walkOff,
} from "./story";
import { NOINK } from "./ink";
import { CARD_K, blobMaterial, cardShade } from "./cardshade";

export const SU = 0.00216;   // metres per design unit: the 1000-unit card is 2.16 m tall
export const PIV = 975;      // the feet pivot inside the 600 x 1000 design box
export const ACTOR_SCALE = 0.92;

// ---------------- canvas pool ----------------
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

/** One canvas per distinct DRAWING, not per character: two actors who share a pose share a texture. */
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
    // unbounded free lists are how a 1200-frame render runs out of memory: cap the cache
    while (this.free.length > 10) {
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

const blank = (() => {
  const c = document.createElement("canvas");
  c.width = c.height = 2;
  return new THREE.CanvasTexture(c);
})();

// the card quad is authored in design units and lifted so its origin is the FEET (PIV 975 of 1000)
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
    // cardshade mixes its light in screen pixels, so it needs the live render height every draw
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
    if (this.mesh.material === this.blob) this.mesh.visible = o > 0.4;
  }
}

// ---------------- placements ----------------
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3 };
export type Place = { key: string; draw: (p: Pen) => void; x: number; y: number; z: number; scale: number; size: [number, number, number] };
export type FxPlace = {
  key: string; cw: number; ch: number; draw: (p: Pen) => void;
  x: number; y: number; z: number; w: number; h: number;
  flat?: boolean; soft?: boolean; opacity?: number;
};
export type Stage = { places: Place[]; fx: FxPlace[] };

/** SKILL.md Section 2: continuous floats quantise to 0.02 so Pool cache keys stay finite. */
const q2 = (v: number) => Math.round(v * 50) / 50;
// the idle breath only needs 10 steps - 50 would be 50 full-size canvases per actor for nothing
const q10 = (v: number) => Math.round(v * 10) / 10;

/** drawing resolution by camera distance, sized for the 1080 x 1920 frame */
const tier = (d: number): [number, number, number] =>
  d < 3.4 ? [1200, 2000, 2.0] : d < 6.4 ? [900, 1500, 1.5] : [600, 1000, 1.0];

const tmp = new THREE.Vector3();
const tmp2 = new THREE.Vector3();

const hero = (cam: CamInfo, c: readonly number[], o: KidOpts, scale = ACTOR_SCALE): Place => {
  // the head is what the lens is actually looking at, so distance is measured to chest height
  const d = cam.pos.distanceTo(tmp.set(c[0], c[1] + 1.15 * scale, c[2])) / scale;
  const [w, h, k] = tier(d);
  const q: KidOpts = {
    ...o,
    gaze: o.gaze !== undefined ? q2(o.gaze) : undefined,
    gazeY: o.gazeY !== undefined ? q2(o.gazeY) : undefined,
    phase: o.phase !== undefined ? q10(o.phase) : undefined,
    phoneP: o.phoneP !== undefined ? q2(o.phoneP) : undefined,
    boardP: o.boardP !== undefined ? q2(o.boardP) : undefined,
    kneePainP: o.kneePainP !== undefined ? q2(o.kneePainP) : undefined,
    blindUpP: o.blindUpP !== undefined ? q2(o.blindUpP) : undefined,
    reachP: o.reachP !== undefined ? q2(o.reachP) : undefined,
    cubeP: o.cubeP !== undefined ? q2(o.cubeP) : undefined,
    dictP: o.dictP !== undefined ? q2(o.dictP) : undefined,
    jawP: o.jawP !== undefined ? q2(o.jawP) : undefined,
    startleP: o.startleP !== undefined ? q2(o.startleP) : undefined,
    gestP: o.gestP !== undefined ? q2(o.gestP) : undefined,
    clapP: o.clapP !== undefined ? q2(o.clapP) : undefined,
    slumpP: o.slumpP !== undefined ? q2(o.slumpP) : undefined,
    thumbsP: o.thumbsP !== undefined ? q2(o.thumbsP) : undefined,
    armsUpP: o.armsUpP !== undefined ? q2(o.armsUpP) : undefined,
    starP: o.starP !== undefined ? q2(o.starP) : undefined,
    sweat: o.sweat !== undefined ? q2(o.sweat) : undefined,
    // Act 2/3. Every one of these is a cache key: a float that skips q2 makes Pool draw a fresh canvas per frame.
    boardKind: o.boardKind, sitP: o.sitP !== undefined ? q2(o.sitP) : undefined,
    wheelP: o.wheelP !== undefined ? q2(o.wheelP) : undefined,
    leanP: o.leanP !== undefined ? q2(o.leanP) : undefined,
    handsUpP: o.handsUpP !== undefined ? q2(o.handsUpP) : undefined,
    pointUpP: o.pointUpP !== undefined ? q2(o.pointUpP) : undefined,
    splitP: o.splitP !== undefined ? q2(o.splitP) : undefined,
    headPainP: o.headPainP !== undefined ? q2(o.headPainP) : undefined,
    earsP: o.earsP !== undefined ? q2(o.earsP) : undefined,
    guitarP: o.guitarP !== undefined ? q2(o.guitarP) : undefined,
    strumP: o.strumP !== undefined ? q2(o.strumP) : undefined,
    guitarSetP: o.guitarSetP !== undefined ? q2(o.guitarSetP) : undefined,
    digP: o.digP !== undefined ? q2(o.digP) : undefined,
    codeP: o.codeP !== undefined ? q2(o.codeP) : undefined,
    walkP: o.walkP !== undefined ? q2(o.walkP) : undefined,
    laughP: o.laughP !== undefined ? q2(o.laughP) : undefined,
    // seatDrop is a per-slot CONSTANT (design units), not an animated float, so it passes through untouched
    sitDrop: o.sitDrop,
  };
  return {
    key: `CH|${JSON.stringify(q)}`,
    x: c[0], y: c[1], z: c[2], scale, size: [w, h, k],
    draw: (p) => drawCharacter(p, q),
  };
};

/** the soft multiply contact shadow every card needs or it reads as floating */
const shadow = (out: Stage, c: readonly number[], sc = 1) => {
  out.fx.push({
    key: "blob|mul", cw: 600, ch: 600, draw: (p) => fxBlob(p),
    x: c[0], y: c[1] + 0.014, z: c[2], w: 0.72 * sc, h: 0.52 * sc, flat: true,
  });
};

/** one 2D effect card, driven by a normalised 0..1 life `u` inside the window */
const fx = (out: Stage, kind: Parameters<typeof drawFx>[1], f0: number, f1: number, f: number, at: readonly number[], w: number, h: number, col?: string, opacity = 1) => {
  if (f < f0 || f > f1) return;
  const u = q2((f - f0) / Math.max(1, f1 - f0));
  out.fx.push({
    key: `FX|${kind}|${u}|${col ?? ""}`, cw: 600, ch: 600,
    draw: (p) => drawFx(p, kind, u, col),
    x: at[0], y: at[1], z: at[2], w, h, soft: true, opacity,
  });
};

/**
 * Shots 21 and 22 are ONE action seen from two cameras, so both call this: the same 26-frame stroke cycle (which
 * divides DIG_END_AT - DIG_AT exactly, so the shovel is home on the frame it stops) and the same buried glove.
 * `extra` lets shot 22 re-light the eyes for the angle read without re-authoring the body.
 */
const digScene = (out: Stage, cam: CamInfo, f: number, solved: boolean, gazeY: number) => {
  const stroke = f >= DIG_AT && f < DIG_END_AT ? ((f - DIG_AT) % 26) / 26 : 0;
  out.places.push(hero(cam, SNOW.hero, {
    role: "hero",
    // three beats keyed off the story, not off the sawtooth: alarm while the mound still hides him, effort for every
    // stroke, relief the moment the digging stops. Keying the face off `stroke` made the reset frame at the top of
    // each 26-frame cycle flip him from strain to a grin in the middle of a rescue.
    expr: f < DIG_AT ? "panicShock" : f < DIG_END_AT ? "strainGrin" : "happyOpen",
    digP: stroke,
    cyanEyes: solved,
    gaze: 0.32, gazeY,
    phase: ((f + 5) % 96) / 96,
  }));
  shadow(out, SNOW.hero, 1.1);
  // The buried friend is deliberately NOT a card here. Sunk to SNOW.friendSunk his own crown is under the mound, so
  // the one thing the audience has to read - a glove, still waving - is its own small FX card on the crest. It stops
  // the frame the real card takes over at BREAK_AT.
  if (f < BREAK_AT) {
    const wave = ((f - BURIED_AT) % 44) / 44;
    out.fx.push({
      key: `GLOVE|${q2(wave)}`, cw: 600, ch: 600, draw: (p) => drawGlove(p, wave),
      x: SNOW.mound[0], y: 0.62, z: SNOW.mound[2], w: 0.85, h: 0.85, soft: true,
    });
  }
  const kick = (f - DIG_AT) % 26;
  if (f >= DIG_AT && f < DIG_END_AT && kick > 10) {
    const u = q2((kick - 10) / 12);
    out.fx.push({
      key: `FX|dust|${u}|dig`, cw: 600, ch: 600,
      draw: (p) => drawFx(p, "dust", u, "#ffffff"),
      x: SNOW.mound[0] + 0.12, y: 0.3, z: SNOW.mound[2] + 0.3, w: 1.1, h: 0.8, soft: true, opacity: 0.55,
    });
  }
};

// ---------------- 2D-hand to 3D-prop contact (SKILL.md Section 3 Rule B) ----------------
/**
 * World position of design point (dx, dy) on a yaw-billboard card, pushed `depthOffset` metres along the card->camera
 * axis. Negative puts the 3D object just BEHIND the card plane so the drawn fist paints over its base at any angle.
 */
export const handWorldPos = (
  camPos: THREE.Vector3,
  charPos: readonly number[],
  scale: number,
  dx: number,
  dy: number,
  depthOffset = -0.08,
  out = new THREE.Vector3(),
): THREE.Vector3 => {
  const [cx, cy, cz] = charPos;
  const yaw = Math.atan2(camPos.x - cx, camPos.z - cz);
  const rightX = Math.cos(yaw), rightZ = -Math.sin(yaw);
  const fwdX = Math.sin(yaw), fwdZ = Math.cos(yaw);
  const localX = (dx - 300) * SU * scale;
  const localY = (PIV - dy) * SU * scale;
  return out.set(
    cx + rightX * localX + fwdX * depthOffset,
    cy + localY,
    cz + rightZ * localX + fwdZ * depthOffset,
  );
};

/** where the hero's pinned fist actually is in the world at frame f — world.ts and cast.ts must agree exactly */
export const kingContact = (camPos: THREE.Vector3, reachP: number, out = new THREE.Vector3()) => {
  // the fist lifts from the table edge (its rest hand) onto HERO_FIST as reachP goes 0 -> 1
  const dx = lerp(392, HERO_FIST[0], clamp01(reachP));
  const dy = lerp(560, HERO_FIST[1], clamp01(reachP));
  return handWorldPos(camPos, CHESS.hero, ACTOR_SCALE, dx, dy, -0.08, out);
};

// ---------------- staging ----------------
export const stage = (id: number, t: number, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const f = Math.round(t * FPS);
  const breath = (offset: number) => ((f + offset) % 96) / 96;
  // The skater's laugh is the SAME expression in shots 9 and 10: a hard cut between two cameras must not be the
  // frame a body resets in.
  const laugh = 1 - glide(f, POINT_AT + 26, POINT_AT + 62);
  /**
   * Where a billboard's pupils point to look at a world object. The card always turns to face the lens, so this is
   * the object's angle on THIS camera's screen, not the character's own heading - and it is the reason shots 16 and
   * 23 can follow a 3D mesh without a hand-tuned number per camera. Signs match toon.ts: +gaze is the viewer's
   * right, +gazeY is down.
   */
  const aim = (from: readonly number[], to: readonly number[]) => {
    const dx = to[0] - from[0], dy = to[1] - (from[1] + 1.47), dz = to[2] - from[2];
    const hd = Math.hypot(dx, dz) || 1;
    const band = (v: number) => Math.max(-1, Math.min(1, v));
    return {
      gaze: band((dx * cam.right.x + dz * cam.right.z) / hd * 1.8),
      gazeY: band(-(dy / hd) * 1.4),
    };
  };

  // ============ BLOCK 1 — CITY SKATEPARK ============
  if (id === 1) {
    // the tutorial plays on the phone, the download lands at GLOW_AT and his eyes go neon
    const phoneP = glide(f, 14, 74);
    const lit = f >= GLOW_AT;
    out.places.push(hero(cam, SKATE.hero, {
      role: "hero",
      expr: lit ? "smirk" : "confidentSmile",
      phoneP,
      cyanEyes: lit && f <= GLOW_END,
      gaze: -0.18, gazeY: lit ? -0.1 : 0.32,
      phase: breath(0),
    }));
    out.places.push(hero(cam, SKATE.skater, {
      role: "skater", expr: "confidentSmile", gaze: 0.34, phase: breath(41),
    }));
    shadow(out, SKATE.hero, 1.1);
    shadow(out, SKATE.skater, 1.0);
    fx(out, "glow", GLOW_AT, GLOW_AT + 26, f, [SKATE.hero[0], 1.52, SKATE.hero[2] + 0.06], 1.1, 1.1, "#00f5d4", 0.9);
    if (f >= GLOW_AT) fx(out, "rays", GLOW_AT, GLOW_AT + 18, f, [SKATE.hero[0], 1.46, SKATE.hero[2] + 0.04], 1.5, 1.5, "#00f5d4", 0.75);
  } else if (id === 2) {
    // pop (FLIP_START) - apex spin (FLIP_APEX) - land (LAND), one continuous 0..1 board curve
    const boardP = glide(f, FLIP_START_AT, LAND_AT + 12);
    // a parabola, not a triangle: the whole card leaves the concrete and falls back on gravity-shaped time
    const airT = seg(FLIP_START_AT + 6, LAND_AT, f);
    const air = 1 - (2 * airT - 1) ** 2;
    out.places.push(hero(cam, [SKATE.hero[0], SKATE.hero[1] + air * 0.34, SKATE.hero[2]], {
      role: "hero",
      expr: f >= LAND_AT ? "happyOpen" : "strainGrin",
      boardP,
      gaze: 0, gazeY: f >= LAND_AT ? 0 : -0.25,
      phase: breath(0),
    }));
    out.places.push(hero(cam, SKATE.skater, {
      role: "skater",
      expr: f >= JAW_AT ? "panicShock" : "confidentSmile",
      jawP: glide(f, JAW_AT, JAW_AT + 16),
      startleP: glide(f, JAW_AT + 4, JAW_AT + 18) * 0.35,
      gaze: -0.3, phase: breath(37),
    }));
    shadow(out, SKATE.hero, 1.1 - air * 0.55);
    shadow(out, SKATE.skater, 1.0);
    fx(out, "dust", FLIP_START_AT, FLIP_START_AT + 18, f, [SKATE.hero[0] - 0.1, 0.12, SKATE.hero[2] + 0.16], 1.5, 0.9, "#e8d8b8");
    fx(out, "burst", LAND_AT, LAND_AT + 22, f, [SKATE.hero[0], 0.28, SKATE.hero[2] + 0.1], 2.0, 1.6, "#ffffff");
    fx(out, "spark", LAND_AT + 2, LAND_AT + 20, f, [SKATE.hero[0] + 0.1, 0.34, SKATE.hero[2] + 0.06], 1.4, 1.4, "#ffd23f");
  } else if (id === 3) {
    // the backfire: hands clamp the knees, bolts of pain, and the bystander stops panicking and starts smirking
    const pain = glide(f, PAIN_AT, PAIN_AT + 26);
    const wince = f > PAIN_END ? 0.55 + 0.45 * Math.abs(Math.sin(((f - PAIN_END) / 34) * Math.PI)) : 1;
    out.places.push(hero(cam, SKATE.hero, {
      role: "hero",
      expr: f >= PAIN_END ? "brokeSad" : "strainGrin",
      kneePainP: pain * wince,
      sweat: pain,
      gaze: 0.1, gazeY: 0.5,
      phase: breath(0),
    }));
    out.places.push(hero(cam, SKATE.skater, {
      role: "skater", expr: f >= PAIN_END ? "smirk" : "panicShock", gaze: -0.32, phase: breath(53),
    }));
    shadow(out, SKATE.hero, 1.1);
    shadow(out, SKATE.skater, 1.0);
    // a spark every ~18 frames across the whole shot, so the knees are never quietly sore
    const cyc = (f - PAIN_AT) % 18;
    if (f >= PAIN_AT && cyc < 12) {
      const u = q2(cyc / 12);
      for (const s of [-1, 1]) {
        out.fx.push({
          key: `FX|spark|${u}|bolts${s}`, cw: 600, ch: 600,
          draw: (p) => drawFx(p, "spark", u, "#ffe14a"),
          x: SKATE.hero[0] + s * 0.19, y: 0.94, z: SKATE.hero[2] + 0.06,
          w: 0.72, h: 0.72, soft: true, opacity: 0.9,
        });
      }
    }
  }

  // ============ BLOCK 2 — CHESS HALL ============
  else if (id === 4) {
    // 15-second cube solve, slam, then the smug arms-up
    const cubeP = glide(f, CUBE_START_AT, CUBE_SLAM_AT);
    const up = glide(f, SMUG_AT, SMUG_AT + 22);
    out.places.push(hero(cam, CHESS.hero, {
      role: "hero",
      expr: f >= SMUG_AT ? "smirk" : "strainGrin",
      cubeP: f >= CUBE_SLAM_AT + 6 ? undefined : cubeP,
      armsUpP: up,
      gaze: 0.12, gazeY: f >= SMUG_AT ? -0.2 : 0.4,
      phase: breath(0),
    }));
    out.places.push(hero(cam, CHESS.friend, {
      role: "friend",
      expr: f >= DISBELIEF_AT ? "panicShock" : "confidentSmile",
      startleP: glide(f, DISBELIEF_AT, DISBELIEF_AT + 20) * 0.5,
      jawP: glide(f, DISBELIEF_AT, DISBELIEF_AT + 20),
      gaze: -0.35, phase: breath(29),
    }));
    out.places.push(hero(cam, CHESS.gm, {
      role: "grandmaster", expr: f >= SMUG_AT ? "strainGrin" : "confidentSmile",
      gaze: 0.3, phase: breath(61),
    }));
    shadow(out, CHESS.hero, 1.15);
    shadow(out, CHESS.friend, 1.0);
    shadow(out, CHESS.gm, 1.0);
    fx(out, "burst", CUBE_SLAM_AT, CUBE_SLAM_AT + 18, f, [CHESS.cubeRest[0], CHESS.cubeRest[1] + 0.1, CHESS.cubeRest[2] + 0.05], 1.6, 1.3, "#ffffff");
    fx(out, "dust", CUBE_SLAM_AT, CUBE_SLAM_AT + 22, f, [CHESS.cubeRest[0], CHESS.cubeRest[1], CHESS.cubeRest[2] + 0.1], 1.3, 0.7, "#efe0c0");
  } else if (id === 5) {
    // blindfold checkmate. The fist pins the 3D king: reachP drives BOTH the 2D arm and world.ts's piece position.
    const reach = glide(f, REACH_START_AT, KING_FALL_AT);
    const hold = 1 - glide(f, REACH_END_AT, REACH_END_AT + 30) * 0.35;
    out.places.push(hero(cam, CHESS.hero, {
      role: "hero", expr: "smirk", blindfold: f >= BLIND_AT,
      reachP: reach * hold,
      gaze: 0.3, phase: breath(0),
    }));
    out.places.push(hero(cam, CHESS.friend, {
      role: "friend",
      expr: f >= GESTURE_AT ? "happyOpen" : "panicShock",
      gestP: glide(f, GESTURE_AT, GESTURE_AT + 20),
      gaze: -0.3, phase: breath(33),
    }));
    out.places.push(hero(cam, CHESS.gm, {
      role: "grandmaster",
      expr: f >= GM_SHOCK_AT ? "panicShock" : "confidentSmile",
      startleP: glide(f, GM_SHOCK_AT, GM_SHOCK_AT + 16),
      gaze: 0.2, phase: breath(57),
    }));
    shadow(out, CHESS.hero, 1.15);
    shadow(out, CHESS.friend, 1.0);
    shadow(out, CHESS.gm, 1.0);
    fx(out, "burst", KING_FALL_AT, KING_FALL_AT + 20, f, [CHESS.king[0], CHESS.king[1] + 0.22, CHESS.king[2] + 0.1], 1.5, 1.5, "#ffffff");
    fx(out, "stars", KING_FALL_AT + 4, KING_FALL_AT + 34, f, [CHESS.gm[0], 1.62, CHESS.gm[2] + 0.1], 1.2, 1.2, "#ffd23f");
    fx(out, "glow", GESTURE_AT, GESTURE_AT + 22, f, [CHESS.board[0], CHESS.board[1] + 0.3, CHESS.board[2] + 0.1], 1.2, 1.2, "#ffd23f", 0.8);
  } else if (id === 6) {
    // the reveal: blindfold up, double thumbs, stars on his own shoulders
    const up = glide(f, UNBLIND_AT, UNBLIND_AT + 18);
    const thumbs = glide(f, THUMBS_AT, THUMBS_AT + 16);
    out.places.push(hero(cam, CHESS.hero, {
      role: "hero", expr: "smirk", blindfold: true, blindUpP: up,
      thumbsP: thumbs,
      starP: f >= STARS_AT ? q2(0.35 + 0.65 * Math.abs(Math.sin(((f - STARS_AT) / 30) * Math.PI))) : 0,
      gaze: -0.1, phase: breath(0),
    }));
    out.places.push(hero(cam, CHESS.friend, {
      role: "friend", expr: "happyOpen", clapP: glide(f, THUMBS_AT + 10, THUMBS_AT + 40), gaze: 0.3, phase: breath(23),
    }));
    out.places.push(hero(cam, CHESS.gm, {
      role: "grandmaster", expr: "brokeSad", slumpP: glide(f, STARS_AT, STARS_AT + 26), gaze: 0.2, phase: breath(49),
    }));
    shadow(out, CHESS.hero, 1.15);
    shadow(out, CHESS.friend, 1.0);
    shadow(out, CHESS.gm, 1.0);
    fx(out, "spark", STARS_AT, STARS_AT + 26, f, [CHESS.hero[0] - 0.34, 1.42, CHESS.hero[2] + 0.05], 0.9, 0.9, "#ffd23f");
    fx(out, "spark", STARS_AT + 8, STARS_AT + 34, f, [CHESS.hero[0] + 0.34, 1.42, CHESS.hero[2] + 0.05], 0.9, 0.9, "#ffd23f");
  }

  // ============ BLOCK 3 — CABIN, then POKER ============
  else if (id === 7) {
    const dictP = glide(f, 990, 1044);
    out.places.push(hero(cam, CABIN.hero, {
      role: "hero", expr: "confidentSmile", dictP,
      gaze: -0.2, gazeY: 0.2, phase: breath(0),
    }));
    // the seat mate is authored seated, so his card sits on the cushion, not the floor
    out.places.push(hero(cam, CABIN.passenger, {
      role: "friend",
      expr: f >= CLAP_AT ? "happyOpen" : "panicShock",
      startleP: f < CLAP_AT ? 0.3 : 0,
      clapP: glide(f, CLAP_AT, CLAP_AT + 34),
      jawP: f < CLAP_AT ? 1 : 0,
      gaze: 0.34, phase: breath(19),
    }, 0.88));
    shadow(out, CABIN.hero, 1.0);
    // three language bubbles pop one after another up the aisle and STAY, so the reading stack grows as a cascade
    // instead of flipping. Overshoot on the scale only: the world position is fixed, so they never drift apart.
    for (const b of CABIN.bubbles) {
      const k = glide(f, b.a, b.a + 9);
      if (k <= 0.001) continue;
      const s = k * (1 + 0.2 * Math.sin(k * Math.PI));
      out.fx.push({
        key: `BUB|${b.text}`, cw: 660, ch: 240,
        draw: (p) => drawBubble(p, b.text),
        x: b.c[0], y: b.c[1], z: b.c[2],
        w: b.w * s, h: b.h * s, soft: true, opacity: clamp01(k * 1.4),
      });
      fx(out, "spark", b.a + 5, b.a + 21, f, [b.c[0], b.c[1] - 0.11, b.c[2] + 0.05], 0.7, 0.7, "#ffffff", 0.85);
    }
  } else if (id === 8) {
    const shades = f >= SHADES_AT;
    out.places.push(hero(cam, POKER.hero, {
      role: "hero", expr: "smirk", shades,
      gaze: -0.12, gazeY: -0.1, phase: breath(0),
    }));
    for (const [i, c, role] of [[0, POKER.oppL, "grandmaster"], [1, POKER.oppR, "friend"]] as [number, readonly number[], "grandmaster" | "friend"][]) {
      out.places.push(hero(cam, c, {
        role,
        expr: "brokeSad",
        slumpP: glide(f, SLUMP_AT + i * 6, SLUMP_AT + 26 + i * 6),
        sweat: 1 - glide(f, SLUMP_AT + 20, SLUMP_AT + 40),
        gaze: i ? 0.3 : -0.3,
        phase: breath(31 + i * 17),
      }));
      shadow(out, c, 1.0);
    }
    shadow(out, POKER.hero, 1.2);
    // the cash rises as one continuous sheet, then the first bundle locks in with a burst on CASH_SPARK
    const rise = glide(f, CASH_START_AT, CASH_END_AT);
    if (rise > 0.01 && rise < 0.995) {
      const u = q2(rise);
      out.fx.push({
        key: `FX|cash|${u}`, cw: 600, ch: 600,
        draw: (p) => drawFx(p, "cash", u, "#8fd6ab"),
        x: POKER.cashRow[0], y: POKER.cashRow[1] + 0.45 * u, z: POKER.cashRow[2] + 0.1,
        w: 2.6, h: 1.5, soft: true, opacity: 0.9,
      });
    }
    fx(out, "burst", CASH_SPARK_AT, CASH_SPARK_AT + 24, f, [POKER.cashRow[0], POKER.cashRow[1] + 0.42, POKER.cashRow[2] + 0.14], 2.2, 2.2, "#ffd23f");
    fx(out, "glow", SHADES_AT, SHADES_AT + 18, f, [POKER.hero[0], 1.5, POKER.hero[2] + 0.06], 1.1, 1.1, "#ffffff", 0.85);
  }

  // ============ ACT 2 — THE BACKFIRE ============
  else if (id === 9) {
    // The physics lecture lands: first he looks at his own hands, then he accuses the sky. The open palms hand their
    // screen time to the raised finger, so the two gestures never draw at once.
    const protest = glide(f, PROTEST_AT, PROTEST_AT + 22);
    const point = glide(f, POINT_AT, POINT_AT + 18);
    out.places.push(hero(cam, SKATE.hero, {
      role: "hero",
      expr: f >= POINT_AT ? "strainGrin" : "panicShock",
      handsUpP: protest * (1 - point),
      pointUpP: point,
      gaze: 0, gazeY: lerp(0.45, -0.6, point),
      phase: breath(0),
    }));
    out.places.push(hero(cam, SKATE.skater, {
      role: "skater", expr: "smirk", laughP: laugh, gaze: -0.3, phase: breath(47),
    }));
    shadow(out, SKATE.hero, 1.1);
    shadow(out, SKATE.skater, 1.0);
    fx(out, "glow", POINT_AT, POINT_AT + 20, f, [SKATE.hero[0], 2.15, SKATE.hero[2] + 0.05], 1.4, 1.4, "#ffffff", 0.45);
  } else if (id === 10) {
    // BRAIN vs BODY: one palm crushes the skull, the other clamps the thigh, and he holds it for the whole crane.
    // The sway is a slow sine, not a second pose, so 200 frames of held gesture still breathes.
    const split = glide(f, SPLIT_AT, SPLIT_AT + 26) * (1 - glide(f, SPLIT_END_AT, SPLIT_END_AT + 24));
    out.places.push(hero(cam, SKATE.hero, {
      role: "hero", expr: "brokeSad", splitP: split,
      sweat: split * (1 - glide(f, SPLIT_END_AT, SPLIT_END_AT + 40)),
      gaze: 0.18 * Math.sin((f - SPLIT_AT) / 21), gazeY: 0.3,
      phase: breath(0),
    }));
    out.places.push(hero(cam, SKATE.skater, {
      role: "skater", expr: "smirk", laughP: laugh, gaze: -0.3, phase: breath(59),
    }));
    shadow(out, SKATE.hero, 1.1);
    shadow(out, SKATE.skater, 1.0);
  } else if (id === 11) {
    // The double backflip. The card rides the exact parabola story.ts authors, so the 2D flight, the drawn board's
    // 720 degrees and the ground shadow all read the same `lift` number.
    const pos = snowAir(f);
    const t = seg(DROP_AT, SNOW_LAND_AT, f);
    const lift = Math.max(0, pos[1] - lerp(SNOW.launch[1], SNOW.landPad[1], t));
    out.places.push(hero(cam, pos, {
      role: "hero",
      expr: f >= SNOW_LAND_AT ? "happyOpen" : "strainGrin",
      boardP: glide(f, DROP_AT, SNOW_LAND_AT + 14), boardKind: "snow",
      gaze: 0, gazeY: f >= SNOW_LAND_AT ? 0 : -0.2,
      phase: breath(0),
    }));
    shadow(out, [pos[0], 0, pos[2]], 1.2 - Math.min(0.6, lift * 0.9));
    fx(out, "dust", DROP_AT, DROP_AT + 18, f, [SNOW.launch[0], SNOW.launch[1] + 0.12, SNOW.launch[2] + 0.2], 2.2, 1.2, "#ffffff");
    fx(out, "rays", APEX_AT - 8, APEX_AT + 14, f, [pos[0], pos[1] + 1.05, pos[2] + 0.1], 1.7, 1.7, "#8fe6f4", 0.5);
    fx(out, "burst", SNOW_LAND_AT, SNOW_LAND_AT + 22, f, [SNOW.landPad[0], 0.3, SNOW.landPad[2] + 0.1], 3.0, 2.2, "#ffffff");
    fx(out, "dust", SNOW_LAND_AT, SNOW_LAND_AT + 26, f, [SNOW.landPad[0], 0.14, SNOW.landPad[2] + 0.3], 2.4, 1.0, "#f4f7fb");
  } else if (id === 12) {
    // SEATED in the tub. The card's pivot stays on the cockpit FLOOR and sitDrop pulls the drawn hip down onto the
    // cushion, which is what puts the 3D rim at his hands instead of across his chest.
    out.places.push(hero(cam, HIGHWAY.hero, {
      role: "hero", expr: f >= SPEED_END_AT ? "smirk" : "confidentSmile",
      sitP: 1, sitDrop: seatDrop(SEAT_PAN.cockpit, HIGHWAY.heroScale),
      wheelP: glide(f, SPEED_AT, SPEED_AT + 18),
      gaze: 0.08, gazeY: -0.3, phase: breath(0),
    }, HIGHWAY.heroScale));
  } else if (id === 13) {
    // The G-force snaps him sideways and then he gives up and holds his own head. Both gestures are authored, so
    // toon.ts ranks them: headPain wins the arms and the drawn rim keeps its place under the fists.
    const jolt = Math.sin(clamp01((f - GRIP_FAIL_AT) / 34) * Math.PI);
    const pain = glide(f, DESPAIR_AT, DESPAIR_AT + 26);
    out.places.push(hero(cam, HIGHWAY.hero, {
      role: "hero", expr: f >= DESPAIR_AT ? "brokeSad" : "panicShock",
      sitP: 1, sitDrop: seatDrop(SEAT_PAN.cockpit, HIGHWAY.heroScale),
      wheelP: 1,
      leanP: jolt * (1 - pain), headPainP: pain,
      sweat: pain, gaze: 0.15, gazeY: lerp(-0.3, 0.45, pain),
      phase: breath(0),
    }, HIGHWAY.heroScale));
    fx(out, "dust", GRIP_FAIL_AT, GRIP_FAIL_AT + 20, f, [HIGHWAY.car[0], 0.16, HIGHWAY.car[2] + 0.7], 2.6, 1.1, "#efe0c0", 0.8);
    // stars over a seated head: 1.42 m is this card's own crown (seatM puts it under the tub rim), not a standing 1.6
    const cyc = (f - DESPAIR_AT) % 22;
    if (f >= DESPAIR_AT && cyc < 12) {
      const u = q2(cyc / 12);
      out.fx.push({
        key: `FX|stars|${u}|cockpit`, cw: 600, ch: 600,
        draw: (p) => drawFx(p, "stars", u, "#ffd23f"),
        x: HIGHWAY.hero[0], y: 1.42, z: HIGHWAY.hero[2] + 0.1, w: 1.2, h: 1.2, soft: true, opacity: 0.85,
      });
    }
  } else if (id === 14) {
    // Thousands of songs download and the soma cooks. The core itself runs red in world.ts; this is the human half.
    const heat = glide(f, OVERHEAT_AT, OVERHEAT_AT + 20);
    out.places.push(hero(cam, BRAIN.hero, {
      role: "hero", expr: f >= OVERHEAT_AT ? "strainGrin" : "smirk",
      cyanEyes: f >= DATA_AT && f <= OVERHEAT_END_AT,
      starP: f >= OVERHEAT_AT
        ? q2(0.35 + 0.65 * Math.abs(Math.sin(((f - OVERHEAT_AT) / 24) * Math.PI))) : 0,
      sweat: heat,
      gaze: 0, gazeY: -0.28, phase: breath(0),
    }));
    shadow(out, BRAIN.hero, 1.1);
    fx(out, "rays", DATA_AT, DATA_AT + 20, f, [BRAIN.hero[0], 1.5, BRAIN.hero[2] + 0.05], 1.6, 1.6, "#00f5d4", 0.7);
    fx(out, "burst", OVERHEAT_AT, OVERHEAT_AT + 18, f, [BRAIN.hero[0], 1.3, BRAIN.hero[2] + 0.12], 1.9, 1.9, "#ff8080");
  } else if (id === 15) {
    // The joke of the shot is that nothing leaves: he realises it in one twelve-frame jolt and then just sweats.
    const s = glide(f, NOFORGET_AT, NOFORGET_AT + 12);
    out.places.push(hero(cam, BRAIN.hero, {
      role: "hero", expr: "panicShock", startleP: s * 0.35,
      sweat: 0.55 + 0.45 * s, gaze: -0.08, gazeY: 0.05, phase: breath(0),
    }));
    shadow(out, BRAIN.hero, 1.1);
  } else if (id === 16) {
    // Three memories light in sequence and he watches each one arrive, then shuts the sound out with both palms.
    const ears = glide(f, COVER_AT, COVER_AT + 22);
    const at = [LOOP_AT, LOOP_AT2, LOOP_AT3];
    let gz = 0, gy = -0.12;
    for (let i = 0; i < BRAIN.screens.length; i++) {
      const a = aim(BRAIN.hero, BRAIN.screens[i].c);
      const k = glide(f, at[i], at[i] + 18);
      gz = lerp(gz, a.gaze, k);
      gy = lerp(gy, a.gazeY, k);
    }
    out.places.push(hero(cam, BRAIN.hero, {
      role: "hero", expr: f >= COVER_AT ? "panicShock" : "strainGrin",
      earsP: ears,
      gaze: lerp(gz, 0, ears), gazeY: lerp(gy, 0.2, ears),
      sweat: ears, phase: breath(0),
    }));
    shadow(out, BRAIN.hero, 1.1);
    for (let i = 0; i < BRAIN.screens.length; i++) {
      const sc = BRAIN.screens[i].c;
      fx(out, "glow", at[i], at[i] + 18, f, [sc[0], sc[1], sc[2] + 0.35], 1.2, 1.2, "#8fe6f4", 0.8);
    }
    fx(out, "burst", COVER_AT, COVER_AT + 16, f, [BRAIN.hero[0], 1.55, BRAIN.hero[2] + 0.1], 1.7, 1.7, "#ffffff", 0.55);
  }

  // ============ ACT 3 — THE PRICE, THEN THE CHOICE ============
  else if (id === 17) {
    // The two friends walk out of the frame on story.ts's shared path, mid-stride the whole way.
    const walk = glide(f, LEAVE_AT, LEAVE_END_AT);
    out.places.push(hero(cam, SKATE.hero, {
      role: "hero", expr: "brokeSad", slumpP: glide(f, LEAVE_AT + 10, LEAVE_AT + 44) * 0.8,
      gaze: 0.3, gazeY: 0.42, phase: breath(0),
    }));
    for (const [c, to, role, ph] of [
      [SKATE.friend, SKATE.friendLeave, "friend", 11] as const,
      [SKATE.friend2, SKATE.friend2Leave, "skater", 37] as const,
    ]) {
      const p = walkOff(f, c, to);
      out.places.push(hero(cam, p, {
        role, expr: "brokeSad", walkP: walk, gaze: role === "friend" ? 0.25 : -0.25, phase: breath(ph),
      }));
      shadow(out, p, 1.0);
    }
    shadow(out, SKATE.hero, 1.1);
  } else if (id === 18) {
    // A year of guitar in three minutes, and no joy in it: the riff keeps cycling while the face goes flat.
    const g = glide(f, GUITAR_AT, GUITAR_AT + 22);
    const strum = f >= RIFF_AT ? ((f - RIFF_AT) % 20) / 20 : 0;
    out.places.push(hero(cam, SKATE.hero, {
      role: "hero", expr: f >= RIFF_AT + 24 ? "brokeSad" : "happyOpen",
      guitarP: g, strumP: strum,
      gaze: -0.12, gazeY: lerp(0.36, 0.12, g), phase: breath(0),
    }));
    shadow(out, SKATE.hero, 1.1);
    // Both cards are centred on the GUITAR, not the man: at y 1.02 a 1.5 m burst spans 0.27..1.77 and the head owns
    // 1.18..1.76, so the chord flash painted itself over his mouth. 0.60 keeps the burst's own shard radius (about
    // 0.4 of the card) under his chin, which is also where the instrument is.
    fx(out, "burst", RIFF_AT, RIFF_AT + 16, f, [SKATE.hero[0] + 0.14, 0.6, SKATE.hero[2] + 0.14], 1.25, 1.25, "#ffd23f");
    const cyc = f >= RIFF_AT ? (f - RIFF_AT) % 20 : 20;
    if (cyc < 12) {
      const u = q2(cyc / 12);
      out.fx.push({
        key: `FX|spark|${u}|riff`, cw: 600, ch: 600,
        draw: (p) => drawFx(p, "spark", u, "#ffe14a"),
        x: SKATE.hero[0] + 0.16, y: 0.78, z: SKATE.hero[2] + 0.18, w: 0.55, h: 0.55, soft: true, opacity: 0.85,
      });
    }
  } else if (id === 19) {
    // He sits on the plaza bench and the guitar leaves the grip. The strum formula is the same expression as shot
    // 18's, multiplied by (1 - sit), so the hand returns to rest across the cut instead of snapping there.
    const deflate = glide(f, DEFLATE_AT, DEFLATE_AT + 26);
    const sit = glide(f, BENCH_AT, BENCH_AT + 26);
    out.places.push(hero(cam, SKATE.heroBench, {
      role: "hero", expr: "brokeSad",
      sitP: sit, sitDrop: seatDrop(SEAT_PAN.bench, ACTOR_SCALE),
      guitarP: 1, strumP: (((f - RIFF_AT) % 20) / 20) * (1 - sit),
      guitarSetP: glide(f, BENCH_AT + 16, BENCH_AT + 52),
      sweat: deflate * 0.5,
      gaze: 0.1, gazeY: lerp(0.3, 0.12, sit), phase: breath(0),
    }));
    shadow(out, SKATE.heroBench, 1.0);
    fx(out, "dust", BENCH_AT + 30, BENCH_AT + 54, f, [SKATE.heroBench[0] + 0.28, 0.1, SKATE.heroBench[2] + 0.2], 1.2, 0.7, "#e8d8b8", 0.7);
  } else if (id === 20) {
    // He points up the face at what he has just done, and the wall answers.
    const flinch = Math.sin(clamp01((f - AVAL_HIT_AT) / 20) * Math.PI);
    out.places.push(hero(cam, SNOW.hero, {
      role: "hero", expr: f >= AVAL_HIT_AT ? "panicShock" : "confidentSmile",
      pointUpP: glide(f, AVAL_AT - 28, AVAL_AT - 8) * (1 - flinch),
      leanP: flinch, startleP: flinch * 0.4,
      gaze: 0.2, gazeY: lerp(-0.55, 0.3, flinch), phase: breath(0),
    }));
    out.places.push(hero(cam, SNOW.friend, {
      role: "friend", expr: f >= AVAL_HIT_AT ? "panicShock" : "happyOpen",
      startleP: glide(f, AVAL_HIT_AT - 12, AVAL_HIT_AT + 10) * 0.5,
      gaze: -0.3, gazeY: -0.35, phase: breath(27),
    }));
    shadow(out, SNOW.hero, 1.1);
    shadow(out, SNOW.friend, 1.0);
    // the storm's leading edge rides the SAME avalPos world.ts moves the 3D wall by, or the two snows separate
    const w = avalPos(f);
    fx(out, "dust", AVAL_AT, AVAL_HIT_AT + 24, f, [w[0], w[1] - 0.95, w[2] - 2.8], 6.5, 3.6, "#ffffff", 0.7);
    // Ground burst, and it has to stay a GROUND burst: at y 0.7 with a 2.0 m card the fully grown shards spanned
    // -0.3..1.7 and the additive white washed straight over the friend's hoodie and legs, so the impact read as a
    // translucent ghost of him rather than as snow hitting his feet. y 0.32 / 1.3 tall caps it at his chest.
    fx(out, "burst", AVAL_HIT_AT, AVAL_HIT_AT + 20, f, [SNOW.friend[0], 0.32, SNOW.friend[2] - 0.4], 2.4, 1.3, "#ffffff");
  } else if (id === 21) {
    digScene(out, cam, f, false, 0.55);
  } else if (id === 22) {
    digScene(out, cam, f, f >= SOLVE_AT && f <= SOLVE_AT + 60,
      lerp(0.55, -0.05, glide(f, BREAK_AT - 10, BREAK_AT + 14)));
    // The friend is the buried card, and he is only in the picture from the frame the mound is cut away: story.ts
    // hides him before BREAK_AT, and he rises through the sunkDepth story.ts owns rather than standing at SNOW.friend.
    const bp = buriedFriend(f);
    if (f >= BREAK_AT) {
      const up = glide(f, BREAK_AT, BREAK_AT + 20);
      out.places.push(hero(cam, bp, {
        role: "friend",
        expr: f >= RELIEF_AT ? "happyOpen" : "panicShock",
        startleP: 0.5 * (1 - glide(f, RELIEF_AT, RELIEF_AT + 24)),
        armsUpP: glide(f, RELIEF_AT, RELIEF_AT + 20),
        gaze: -0.3, gazeY: lerp(0.4, -0.2, up), phase: breath(19),
      }));
      shadow(out, bp, 1.0);
    }
    fx(out, "rays", SOLVE_AT, SOLVE_AT + 20, f, [SNOW.hero[0], 1.5, SNOW.hero[2] + 0.05], 1.5, 1.5, "#00f5d4", 0.65);
    fx(out, "burst", BREAK_AT, BREAK_AT + 20, f, [SNOW.mound[0], 0.6, SNOW.mound[2] + 0.1], 2.6, 2.2, "#ffffff");
    fx(out, "dust", BREAK_AT, BREAK_AT + 26, f, [SNOW.mound[0], 0.24, SNOW.mound[2] + 0.3], 2.2, 1.0, "#f4f7fb");
    fx(out, "glow", RELIEF_AT, RELIEF_AT + 22, f, [bp[0], bp[1] + 1.5, bp[2] + 0.06], 1.2, 1.2, "#ffffff", 0.6);
  } else if (id === 23) {
    // An empty car rolls in and parks. His eyes follow it the whole way, on this camera's own screen axis.
    const p = carRoll(f);
    const look = aim(ROAD.hero, [p[0], p[1] + 0.45, p[2]]);
    out.places.push(hero(cam, ROAD.hero, {
      role: "hero", expr: f >= CAR_STOP_AT ? "confidentSmile" : "smirk",
      gaze: look.gaze, gazeY: look.gazeY, phase: breath(0),
    }));
    shadow(out, ROAD.hero, 1.1);
    // the puff trails where the car WAS ten frames ago, which is what makes it a wake and not a sticker
    const q = carRoll(f - 10);
    const cyc = (f - CAR_IN_AT) % 14;
    if (f >= CAR_IN_AT && f < CAR_STOP_AT + 8 && cyc < 10) {
      const u = q2(cyc / 10);
      out.fx.push({
        key: `FX|dust|${u}|wake`, cw: 600, ch: 600,
        draw: (p2) => drawFx(p2, "dust", u, "#cfd6e2"),
        x: q[0], y: 0.16, z: q[2] + 0.55, w: 1.3, h: 0.8, soft: true, opacity: 0.5,
      });
    }
    fx(out, "burst", CAR_STOP_AT, CAR_STOP_AT + 16, f, [ROAD.carRest[0], 0.34, ROAD.carRest[2] + 0.4], 1.8, 1.4, "#efe0c0");
  } else if (id === 24) {
    const code = glide(f, CODE_AT, CODE_AT + 26);
    const g = handWorldPos(cam.pos, ROAD.hero, ACTOR_SCALE, HERO_CODE[0], HERO_CODE[1], -0.02, tmp2);
    out.places.push(hero(cam, ROAD.hero, {
      role: "hero",
      expr: f >= CODE_AT ? "smirk" : "confidentSmile",
      codeP: code, cyanEyes: f >= CODE_AT && f <= CHOICE_AT,
      startleP: glide(f, DOOR_AT, DOOR_AT + 14) * 0.3,
      gaze: -0.1, gazeY: lerp(0.4, 0.05, code), phase: breath(0),
    }));
    shadow(out, ROAD.hero, 1.1);
    fx(out, "rays", UFO_AT, UFO_AT + 18, f, [ROAD.hero[0], 1.55, ROAD.hero[2] + 0.05], 1.8, 1.8, "#bfe9ff", 0.6);
    fx(out, "burst", CODE_AT, CODE_AT + 16, f, [g.x, g.y, g.z], 1.2, 1.2, "#00f5d4");
    if (f >= CODE_AT && f <= CODE_END_AT) {
      fx(out, "glow", CODE_AT, CODE_END_AT, f, [g.x, g.y, g.z], 0.7, 0.7, "#00f5d4", 0.85);
    }
  } else if (id === 25) {
    // The last look is into the lens, not at anything in the world: gaze 0, and the cyan only just gone.
    const thumbs = glide(f, FINAL_THUMBS_AT, FINAL_THUMBS_AT + 18);
    out.places.push(hero(cam, ROAD.hero, {
      role: "hero", expr: "smirk", thumbsP: thumbs,
      cyanEyes: f <= CHOICE_AT,
      gaze: 0, gazeY: 0, phase: breath(0),
    }));
    shadow(out, ROAD.hero, 1.1);
    fx(out, "glow", CHOICE_AT - 14, CHOICE_AT + 10, f, [ROAD.hero[0], 1.5, ROAD.hero[2] + 0.05], 1.3, 1.3, "#00f5d4", 0.7);
    fx(out, "rays", FINAL_THUMBS_AT, FINAL_THUMBS_AT + 16, f, [ROAD.hero[0], 1.5, ROAD.hero[2] + 0.04], 1.5, 1.5, "#ffd23f", 0.6);
  }

  return out;
};
