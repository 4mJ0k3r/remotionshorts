// Frame driver for InstantSkillShort. Owns the camera, the per-shot light preset, the exclusive set visibility,
// every reactive 3D prop, and the single 2D-hand-to-3D-prop contact the film is built around (SKILL.md Section 3
// Rule B). Everything here is a pure function of frame number: nothing is integrated, so a still at f710 and frame
// 710 of the video are the same picture.
import * as THREE from "three";
import { buildSets, WorldSets } from "./build";
import { LIGHTS, LOOK, LightName, LightPreset } from "./lights";
import { CHAR, TONE, untone } from "./shade";
import { NOINK } from "./ink";
import { ACTOR_SCALE, Actor, CamInfo, Fx, Pool, handWorldPos, stage } from "./cast";
import {
  AVAL_AT, AVAL_HIT_AT, BREAK_AT, BRAIN, BURIED_AT, CAR_STOP_AT, CASH_END_AT, CASH_START_AT, CHESS, CODE_AT,
  CUBE_SLAM_AT, CUBE_START_AT, DATA_AT, DIG_AT, DIG_END_AT, FLIP_START_AT, FPS, GLOW_AT, GLOW_END, GRIP_FAIL_AT,
  HIGHWAY, KING_FALL_AT, LAND_AT, LOOP_AT, LOOP_AT2, LOOP_AT3, OVERHEAT_AT, OVERHEAT_END_AT, POKER, REACH_START_AT,
  ROAD, SHOTS, SNOW_LAND_AT, SPEED_AT, SPEED_END_AT, TOTAL, UFO_AT, avalPos, camAt, carRoll, clamp01, dofAt, glide,
  lerp, seg,
} from "./story";
import { HERO_FIST } from "./toon";

const UP = new THREE.Vector3(0, 1, 0);

/** the black king is welded to this design-space fist, minus its own base offset */
const KING_BASE_DROP = 0.07;

/**
 * The snow sheets' peak opacities, in build.ts's plume() order [wall-left, wall-right, wall-centre, landing]: the
 * first three are the authored alphas of the sheets build.ts lays down at SNOW.avalEndZ, the fourth is world.ts's
 * own because build.ts ships the landing puff at 0 — the takeoff pad has to stay clean until SNOW_LAND_AT.
 */
const SPRAY_OPA = [0.24, 0.24, 0.2, 0.78];

/** the memory screens' lit glass. build.ts leaves all three emissive-black (a windowless room that starts dark),
 *  so the on-colour is world.ts's to own — cyan, because every other "skill" light in the film is cyan. */
const SCREEN_ON = new THREE.Color("#8fe6f4");

/** screen i lights at these frames and stays on: they are PROP_QUADS[16]'s authored windows, because story.ts
 *  measures screen i from LOOP_AT + i * 62 and LOOP_AT2 / LOOP_AT3 sit exactly 62 and 124 past LOOP_AT. The
 *  fallback keeps that spacing if a fourth memory is ever authored. */
const LOOP_ATS = [LOOP_AT, LOOP_AT2, LOOP_AT3];

/** what the soma turns at OVERHEAT_AT. Cool cyan to a cooked red, and nothing hotter: the grade in lights.ts
 *  spends its whole saturation budget on this one emissive, so a saturated red here would clip the frame. */
const CORE_HOT = new THREE.Color("#a3283a");

export class World {
  root = new THREE.Group();
  /** the live DOF focus point, read by the composition every frame */
  focus = new THREE.Vector3(0, 1.2, 0);
  /** focus falloff for the current shot, in metres */
  cInf = 7;
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight;
  private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh;
  private skyMat: THREE.ShaderMaterial;
  private sets: WorldSets;
  /** the neuron core's resting emissive, captured from build.ts at construction */
  private coreCool = new THREE.Color();
  private sunCache = new Map<number, THREE.Vector3>();
  private v1 = new THREE.Vector3();
  private v2 = new THREE.Vector3();
  private v3 = new THREE.Vector3();

  constructor() {
    const R = this.root;

    this.skyMat = new THREE.ShaderMaterial({
      uniforms: {
        c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() },
        c2: { value: new THREE.Color() }, c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() },
        e: { value: new THREE.Vector4() },
      },
      vertexShader: `
        varying vec3 vP;
        void main() {
          vP = normalize(position);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 c0, c1, c2, c3, c4;
        uniform vec4 e;
        varying vec3 vP;
        void main() {
          float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el));
          c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el));
          c = mix(c, c4, smoothstep(e.z, e.w, el));
          gl_FragColor = vec4(c, 1.0);
        }
      `,
      side: THREE.BackSide,
      depthWrite: false,
      fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(900, 32, 16), this.skyMat);
    this.sky.renderOrder = -1;
    this.sky.frustumCulled = false;
    this.sky.layers.set(NOINK);
    R.add(this.sky);

    this.hemi = new THREE.HemisphereLight("#f6e6cc", "#9c8265", 0.9);
    this.sun = new THREE.DirectionalLight("#fff0cf", 3.0);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.sun.shadow.camera.near = 0.5;
    this.sun.shadow.camera.far = 60;
    this.sun.shadow.camera.left = -12;
    this.sun.shadow.camera.right = 12;
    this.sun.shadow.camera.top = 12;
    this.sun.shadow.camera.bottom = -12;
    R.add(this.hemi, this.sun, this.sun.target);

    this.sets = buildSets();
    // eight isolated roots, one per SetName. A set that is not added here cannot be made visible below, and a set
    // added twice would put two snow ridges in the same frame.
    R.add(
      this.sets.skate.root, this.sets.chess.root, this.sets.cabin.root, this.sets.poker.root,
      this.sets.snow.root, this.sets.highway.root, this.sets.brain.root, this.sets.road.root,
    );
    // the soma's resting emissive is build.ts's authored "#1f6f86", so it is read off the mesh once here instead
    // of being copied into this file: animBrain only ever lerps FROM it.
    this.coreCool.copy((this.sets.brain.core.material as THREE.MeshLambertMaterial).emissive);
  }

  private actor(i: number) {
    while (this.actors.length <= i) this.actors.push(new Actor(this.root));
    return this.actors[i];
  }

  private fx(i: number) {
    while (this.fxs.length <= i) this.fxs.push(new Fx(this.root));
    return this.fxs[i];
  }

  /** camera-relative key light, frozen per shot so a held face never changes its shading mid-shot */
  private shotSun(id: number, L: LightPreset) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1];
    let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 4) {
      const c = camAt(id, Math.min(f, TOTAL - 1));
      const x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2];
      const n = Math.hypot(x, z) || 1;
      fx += x / n; fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1;
    fx /= n; fz /= n;
    const az = THREE.MathUtils.degToRad(L.az);
    const el = THREE.MathUtils.degToRad(L.el);
    v = new THREE.Vector3(
      (fx * Math.cos(az) - fz * Math.sin(az)) * Math.cos(el),
      Math.sin(el),
      (fz * Math.cos(az) + fx * Math.sin(az)) * Math.cos(el),
    ).normalize();
    this.sunCache.set(id, v);
    return v;
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene): THREE.Vector3 {
    const s = SHOTS[id - 1];
    const L = LIGHTS[s.light as LightName];
    const look = LOOK[s.light as LightName];

    // ---- camera ----
    const c = camAt(id, f);
    cam.position.set(...c.pos);
    cam.up.copy(UP);
    cam.lookAt(c.look[0], c.look[1], c.look[2]);
    cam.fov = c.fov;
    cam.near = 0.1;
    cam.far = 1000;
    cam.updateProjectionMatrix();
    cam.updateMatrixWorld();
    cam.layers.enable(NOINK);

    // ---- DOF: focus always sits on the live subject, never on the set average ----
    const dof = dofAt(f);
    const fp = dof.focus(f);
    this.focus.set(fp[0], fp[1], fp[2]);
    this.cInf = dof.cInf;

    // ---- lights, tone and sky ----
    const sunDir = this.shotSun(id, L);
    this.sun.position.copy(cam.position).addScaledVector(sunDir, 30);
    this.sun.target.position.set(c.look[0], c.look[1], c.look[2]);
    this.sun.color.set(L.sunCol);
    this.sun.intensity = L.sunI;
    this.sun.shadow.bias = L.bias;
    this.sun.shadow.normalBias = L.normalBias;
    this.hemi.color.set(L.sky);
    this.hemi.groundColor.set(L.ground);
    this.hemi.intensity = L.hemiI;

    TONE.uLitCol.value.set(...L.lit);
    TONE.uShadeCol.value.set(...L.shade);
    TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert;
    TONE.uSideK.value = L.sideK;
    TONE.uTerm.value = L.term;
    TONE.uBounce.value.set(...look.bounce);
    TONE.uSat.value = look.sat;

    CHAR.uCharTint.value.set(...L.charTint);
    CHAR.uCharShade.value = L.charShade;
    CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad;
    CHAR.uSideTint.value.set(...L.sideTint);

    const sc = look.sky.c;
    this.skyMat.uniforms.c0.value.copy(untone(sc[0]));
    this.skyMat.uniforms.c1.value.copy(untone(sc[1]));
    this.skyMat.uniforms.c2.value.copy(untone(sc[2]));
    this.skyMat.uniforms.c3.value.copy(untone(sc[3]));
    this.skyMat.uniforms.c4.value.copy(untone(sc[4]));
    const se = look.sky.e;
    this.skyMat.uniforms.e.value.set(
      THREE.MathUtils.degToRad(se[1]), THREE.MathUtils.degToRad(se[2]),
      THREE.MathUtils.degToRad(se[3]), THREE.MathUtils.degToRad(se[4]),
    );

    if (!scene.fog) scene.fog = new THREE.Fog(L.fog, L.fogNear, L.fogFar);
    else {
      (scene.fog as THREE.Fog).color.set(L.fog);
      (scene.fog as THREE.Fog).near = L.fogNear;
      (scene.fog as THREE.Fog).far = L.fogFar;
    }

    // ---- one set visible per shot (Hard Rule 8) ----
    // Eight comparisons over eight different strings, so exactly one of them can ever be true: a second visible
    // root would put a snow ridge inside the chess lounge. The dispatch below is the compile-time guard that a
    // ninth SetName cannot arrive unregistered.
    const st = s.set;
    this.sets.skate.root.visible = st === "skate";
    this.sets.chess.root.visible = st === "chess";
    this.sets.cabin.root.visible = st === "cabin";
    this.sets.poker.root.visible = st === "poker";
    this.sets.snow.root.visible = st === "snow";
    this.sets.highway.root.visible = st === "hwy";
    this.sets.brain.root.visible = st === "brain";
    this.sets.road.root.visible = st === "road";

    // ---- reactive 3D ----
    switch (st) {
      case "skate": this.animSkate(id, f); break;
      case "chess": this.animChess(id, f, cam); break;
      case "cabin": this.animCabin(f); break;
      case "poker": this.animPoker(f); break;
      case "snow": this.animSnow(id, f); break;
      case "hwy": this.animHighway(f); break;
      case "brain": this.animBrain(f); break;
      case "road": this.animRoad(f); break;
      default: {
        // deliberately no fallback: an unknown set gets an error, not the poker lamp swinging in a void. Every
        // SetName is a case above, so `s.set` is `never` here and a new set in story.ts fails `tsc --noEmit`
        // instead of quietly rendering 3714 frames of nothing.
        const unregistered: never = st;
        throw new Error(`world.update: SetName "${String(unregistered)}" has no animation`);
      }
    }

    // ---- cast cards ----
    const camRight = new THREE.Vector3();
    cam.matrixWorld.extractBasis(camRight, this.v2, this.v3);
    const info: CamInfo = { pos: cam.position, right: camRight };

    const staged = stage(id, f / FPS, info);
    let aIdx = 0;
    for (const p of staged.places) {
      const act = this.actor(aIdx++);
      act.mesh.position.set(p.x, p.y, p.z);
      act.mesh.scale.setScalar(p.scale);
      act.mesh.rotation.set(0, Math.atan2(cam.position.x - p.x, cam.position.z - p.z), 0);
      act.r = this.pool.req(p.key, p.size[0], p.size[1], p.size[2], p.draw);
      act.mesh.visible = true;
    }
    while (aIdx < this.actors.length) this.actors[aIdx++].mesh.visible = false;

    let fxIdx = 0;
    for (const p of staged.fx) {
      const card = this.fx(fxIdx++);
      card.mesh.position.set(p.x, p.y, p.z);
      card.mesh.scale.set(p.w, p.h, 1);
      if (p.flat) {
        card.mesh.rotation.set(-Math.PI / 2, 0, 0);
      } else {
        card.mesh.rotation.set(0, Math.atan2(cam.position.x - p.x, cam.position.z - p.z), 0);
      }
      card.use(!!p.soft);
      card.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      card.opacity(p.opacity ?? 1);
    }
    while (fxIdx < this.fxs.length) this.fxs[fxIdx++].mesh.visible = false;

    this.pool.flush();
    for (const a of this.actors) if (a.mesh.visible) a.bind();
    for (const x of this.fxs) if (x.mesh.visible) x.bind();

    return new THREE.Vector3(c.look[0], c.look[1], c.look[2]);
  }

  // ---------------- skatepark ----------------
  // Shots 9, 10 and 17-19 are the same pad with no download and no trick in them, and they degrade out of this
  // method on their own: `on` is 0 for any id but 1 and 2, and the deck flex is a 12-frame sin half-cycle that is
  // back to exactly its authored 0 by FLIP_START_AT + 12 = 192, long before frame 1194. Nothing to add.
  private animSkate(id: number, f: number) {
    const S = this.sets.skate;
    // the cyan pool under the hero: lit on the download, then again through the flight
    const on = id === 1
      ? seg(GLOW_AT, GLOW_AT + 10, f) * (1 - seg(GLOW_END, GLOW_END + 8, f))
      : id === 2
        ? 0.45 + 0.55 * Math.abs(Math.sin(f * 0.32)) * seg(FLIP_START_AT, FLIP_START_AT + 10, f) * (1 - seg(LAND_AT + 24, LAND_AT + 46, f))
        : 0;
    (S.glow.material as THREE.MeshBasicMaterial).opacity = clamp01(on) * 0.55;
    // the ramp deck flexes a hair when he pops off it
    S.ramp.rotation.x = -0.02 * Math.sin(clamp01((f - FLIP_START_AT) / 12) * Math.PI);
  }

  // ---------------- chess hall ----------------
  private animChess(id: number, f: number, cam: THREE.PerspectiveCamera) {
    const C = this.sets.chess;

    // the hand-off cube: the 3D scrambled cube owns the table until the 2D hands take it, and the solved one
    // lands the instant the 2D slam hits, so the two never draw over each other
    C.cubeScrambled.visible = f < CUBE_START_AT;
    C.cubeScrambled.rotation.y = 0.5 + f * 0.004;
    C.cubeSolved.visible = f >= CUBE_SLAM_AT;
    if (C.cubeSolved.visible) {
      const drop = glide(f, CUBE_SLAM_AT, CUBE_SLAM_AT + 10);
      const bounce = Math.abs(Math.sin(drop * Math.PI * 2)) * 0.05 * (1 - drop);
      C.cubeSolved.position.set(CHESS.cubeRest[0], CHESS.cubeRest[1] + bounce + (1 - drop) * 0.10, CHESS.cubeRest[2]);
      C.cubeSolved.rotation.set((1 - drop) * 0.6, -0.32 + (1 - drop) * 1.9, (1 - drop) * 0.4);
    }

    // the match clock ticks one quarter-turn per move
    C.clockHand.rotation.z = -Math.floor(clamp01((f - 456) / 60) * 60) * (Math.PI / 6);

    // the lamp over the felt drifts on its 2.38 m cord: with every banner and board gone, this is the only thing
    // in the hall that moves on its own, so it never stops
    C.pendant.rotation.x = 0.011 * Math.sin(f * 0.042) + 0.004 * Math.sin(f * 0.11);
    C.pendant.rotation.z = 0.009 * Math.cos(f * 0.037);

    // ---- Rule B: the black king is pinned to the hero's fist ----
    // Before the reach it holds its authored rest pose; from REACH_START_AT every frame re-derives the base from
    // toon.ts HERO_FIST through the live billboard basis, so the 2D fist paints over the 3D collar with no gap at
    // any camera angle. Measured drift across shot 5's track is < 3 cm, well inside a 60 cm board.
    if (f >= REACH_START_AT) {
      const p = handWorldPos(cam.position, CHESS.hero, ACTOR_SCALE, HERO_FIST[0], HERO_FIST[1], -0.08, this.v1);
      C.king.position.set(p.x, p.y - KING_BASE_DROP, p.z);
    } else {
      C.king.position.set(...CHESS.king);
    }
    // the tip-over hinges about the piece's own base, falling away from the hero toward the grandmaster
    const fall = glide(f, KING_FALL_AT, KING_FALL_AT + 16);
    const settle = 1 + 0.07 * Math.sin(clamp01((f - KING_FALL_AT) / 30) * Math.PI * 3) * (1 - glide(f, KING_FALL_AT + 16, KING_FALL_AT + 34));
    C.king.rotation.z = -1.42 * fall * settle;
    if (id < 5) {
      // before the blindfold match starts he has not touched the board: the piece stands on its square, upright
      C.king.position.set(...CHESS.king);
      C.king.rotation.z = 0;
    }
  }

  // ---------------- cabin ----------------
  private animCabin(f: number) {
    const P = this.sets.cabin;
    // the aisle strip breathes so the ceiling light is never dead flat
    P.aisleLight.scale.y = 1 + 0.5 * Math.sin(f * 0.12);
  }

  // ---------------- poker lounge ----------------
  private animPoker(f: number) {
    const K = this.sets.poker;
    for (const b of K.cash) {
      const slot = b.userData.slot as number;
      const x = b.userData.x as number;
      const a = CASH_START_AT + slot * 7;
      const k = glide(f, a, a + 22);
      // each bundle clears the felt, rises to chest height and then rings steady with a slight sway
      const settle = 1 - glide(f, CASH_END_AT, CASH_END_AT + 20);
      const rise = k * 0.42;
      b.position.set(x, POKER.cashRow[1] - 0.075 + rise, POKER.cashRow[2]);
      b.rotation.y = (b.userData.rot as number) + Math.sin((f - a) * 0.16) * 0.05 * k * settle;
      b.rotation.z = Math.sin((f - a) * 0.11 + slot) * 0.06 * k * settle;
    }
    // the shade over the felt swings once the money lands
    K.lamp.rotation.z = Math.sin(f * 0.05) * 0.035;
    K.lamp.rotation.x = Math.cos(f * 0.041) * 0.02;
  }

  // ---------------- alpine basin ----------------
  private animSnow(id: number, f: number) {
    const S = this.sets.snow;

    // ---- the wall ----
    // One write of the position story.ts authors, and the eleven teeth, the seven crown lumps and the glow sheet
    // under the lip ride it because they are children of this mesh, not siblings that would be left at the top of
    // the face. It has to leave the picture with the shot that measures it: avalPos parks the 5.0 m-deep slab on
    // SNOW.avalEndZ 8.8, i.e. z 6.0..11.3 once its lean is counted, and shot 22's lens stands at (2.60, 3.03, 7.26) —
    // INSIDE that box, so a wall still standing there renders a camera buried in snow.
    // The handoff is SHOTS[19].b = 2998, which is a hard cut, so retiring it cannot pop on screen.
    // `=== 20`, not `<= 20`: shot 11 also runs on this set, and parked at SNOW.avalStartZ 26 the slab is the whole
    // sky behind his backflip, so an inclusive lower bound renders a 5 m wall of snow over the jump.
    S.aval.visible = id === 20;
    const w = avalPos(f);
    S.aval.position.set(w[0], w[1], w[2]);

    // ---- spray ----
    // The wall's front throws 2-3 m of powder and build.ts parks the three sheets just downstage of SNOW.avalEndZ
    // so they read as the storm's leading edge through shot 20. They come up on AVAL_AT and settle away across the
    // burial — the centre sheet is still billowing at BURIED_AT 3006 and all three are gone at 3056, so the dig
    // starts in clear air and shot 22's rescue never renders through a plume.
    const storm = glide(f, AVAL_AT, AVAL_AT + 14) * (1 - glide(f, AVAL_HIT_AT + 24, BURIED_AT + 50));
    for (let i = 0; i < 3; i++) {
      const sheet = S.spray[i];
      if (!sheet) continue;
      (sheet.material as THREE.MeshBasicMaterial).opacity =
        SPRAY_OPA[i] * storm * (0.8 + 0.2 * Math.sin(f * (0.058 + i * 0.011) + i * 2.3));
    }
    // the landing puff lives entirely inside shot 11: up in 5 frames on SNOW_LAND_AT 1574 and out by +13 = 1587,
    // which is that shot's last frame, so the cut to the highway lands on a clean pad
    const puff = S.spray[3];
    if (puff) {
      const gone = 1 - glide(f, SNOW_LAND_AT + 11, SNOW_LAND_AT + 13);
      (puff.material as THREE.MeshBasicMaterial).opacity =
        SPRAY_OPA[3] * glide(f, SNOW_LAND_AT, SNOW_LAND_AT + 5) * gone;
    }

    // ---- the mound ----
    // Scaled about its own origin, which build.ts parks exactly on SNOW.mound — the same x/z axis the friend's card
    // stands on — so the cut opens where he is rather than wherever the five lumps happen to sit. It holds its
    // authored size, because the plate scripts/is_frame.mjs measures shot 21 against (1.7 m across, 0.34 m tall)
    // IS scale 1, and it only sags 6% = 2 cm of a 0.51 m crest as the dig compacts it. Then BREAK_AT opens the
    // cut: crest to a fifth, rim spread 40%, which leaves a scar in the piste the rising card can stand in.
    // It is an Act 3 prop: SNOW.mound sits 1.05 m up the slope from SNOW.landPad, so leaving it visible for shot 11
    // buries his landing. BURIED_AT 3006 is the frame it forms, which is inside shot 21.
    S.mound.visible = id >= 21;
    const open = glide(f, BREAK_AT, BREAK_AT + 18);
    const sag = 1 - 0.06 * seg(DIG_AT, DIG_END_AT, f);
    S.mound.scale.set(
      lerp(1, 1.4, open),
      lerp(1, 0.2, open) * sag * (1 + 0.02 * open * Math.sin(f * 0.09)),
      lerp(1, 1.4, open),
    );
    // ridgeMats is exposed but build.ts gives it no write, and the only motion a flank plate could take is a
    // texture drift — which would slide the mountains themselves — so the eight ridgelines stay exactly as built.
  }

  // ---------------- desert highway ----------------
  private animHighway(f: number) {
    const H = this.sets.highway;

    // ---- the scroll ----
    // 300 km/h is 83.33 m/s = 2.778 m per frame. makeDashTexture is exactly one HIGHWAY.stripeZ (4.0 m) period and
    // the plate repeats 22x down its 88 m, so the true rate is 0.694 of a period per frame: past the half-period
    // Nyquist limit, where a strobe-less dash pattern stops going forward and starts going backwards. The road
    // therefore travels 1.24 m per frame (0.31 period) and the streak sheets carry the rest of the read — the same
    // bargain a real chase lens makes with motion blur.
    const V = 1.24;
    const RAMP = 16;   // SPEED_AT 1604 -> full rate at 1620, well inside SPEED_AT..SPEED_END_AT 1660
    const u = f - SPEED_AT;
    // the closed-form integral of a linear rate ramp: monotone in f, so the pattern never rewinds and nothing is
    // accumulated between frames — frame 1750 renders the same offset in a still as in the video.
    const travel = u <= 0 ? 0 : u < RAMP ? (u * u * V) / (2 * RAMP) : V * (RAMP / 2 + (u - RAMP));
    const rate = u <= 0 ? 0 : Math.min(1, u / RAMP);
    const dm = H.dash.material as THREE.MeshLambertMaterial;
    if (dm.map) dm.map.offset.y = -(travel / HIGHWAY.stripeZ) % 1;   // v runs toward world -z, so negative is forward
    for (const tyre of H.wheels) {
      // the radius comes off the geometry rather than a number copied from build.ts: rear 0.35, front 0.32, so the
      // fronts do turn 9% faster over the same ground. rotation.x is a real spin only because the axle is baked.
      const r = (tyre.geometry as THREE.CylinderGeometry).parameters.radiusTop;
      tyre.rotation.x = travel / r;
    }

    // ---- the chassis ----
    // HIGHWAY.car is authored at its rear axle and never translates — the road moves past it — so the only writes
    // are pitch and roll on the authored ZXY order. The tub and the four tyres are children of this group, which is
    // what carries the driver with the chassis; the 2D card stays pinned to HIGHWAY.hero and the tub floor under it
    // moves under 2 cm at these amplitudes, because its lever from the axle is only (0, 0.30, 0.12).
    const buzz = Math.sin(f * 0.62) * 0.0018 + Math.sin(f * 1.31) * 0.0009;
    const snap = glide(f, GRIP_FAIL_AT, GRIP_FAIL_AT + 7);
    const ring = 1 + 0.3 * Math.sin((f - GRIP_FAIL_AT) * 0.55) * snap
      * (1 - glide(f, GRIP_FAIL_AT + 7, GRIP_FAIL_AT + 47));
    // the deck vibration runs from the first frame of shot 12 — the car is already at 300 km/h while his hands are
    // not yet on the wheel — but the scroll above is authored to start at SPEED_AT, so the two do not share a ramp
    H.car.rotation.z = 0.018 * Math.sin(f * 0.118 + 1.9) * (1 - snap) + 0.032 * snap * ring + buzz * 1.4;
    // positive x drops the +z nose: the car dives into the G-force, rings twice and holds the lean for shot 13.
    // 0.032 rad roll is 2.6 cm at the 0.81 m half-track and 0.018 rad pitch is 4.4 cm at the 2.42 m front wing, so
    // the car stays inside the 0.95 x 0.52 half-size plate shots 12-13 measure.
    H.car.rotation.x = 0.018 * snap * ring + buzz * 0.8;

    // ---- the 300 km/h read ----
    // The four sheets share this ONE material, so one opacity brings the whole set up together. 0.42 is build.ts's
    // authored peak; SPEED_END_AT hands the shot to the lens 2.25 m above the tub, where the near sheet at y 0.16
    // has fallen out of frame, so 22% of it comes off without taking the speed down with it.
    const STREAK = 0.42;
    const deck = 1 - 0.22 * glide(f, SPEED_END_AT, SPEED_END_AT + 24);
    const flare = glide(f, GRIP_FAIL_AT, GRIP_FAIL_AT + 6) * (1 - glide(f, GRIP_FAIL_AT + 6, GRIP_FAIL_AT + 26));
    (H.speed.material as THREE.MeshBasicMaterial).opacity = clamp01(
      STREAK * rate * deck * (0.9 + 0.1 * Math.sin(f * 0.33)) + STREAK * 0.5 * flare,
    );
  }

  // ---------------- neural chamber ----------------
  private animBrain(f: number) {
    const B = this.sets.brain;
    const cm = B.core.material as THREE.MeshLambertMaterial;

    // ---- the soma ----
    // DATA_AT lights it, OVERHEAT_AT runs it red, OVERHEAT_END_AT stops the shaking — but `heat` has no return
    // term, because shots 15-16 are exactly the joke that nothing cools down again. Both channels go through the
    // emissive build.ts left on the mesh: shade.ts's twoTone rewrites directDiffuse only, so emissive still reaches
    // the output and there is no new uniform to invent here.
    const data = glide(f, DATA_AT, DATA_AT + 20);
    const heat = glide(f, OVERHEAT_AT, OVERHEAT_AT + 18);
    const beat = 0.5 + 0.5 * Math.sin(f * 0.19);       // 0.9 Hz download pulse; 0.19 rad/frame is far under Nyquist
    const hammer = heat * Math.abs(Math.sin(f * 0.42)); // 2 Hz while it cooks, and it never fully stops
    const shake = glide(f, OVERHEAT_AT, OVERHEAT_AT + 10)
      * (1 - glide(f, OVERHEAT_END_AT - 20, OVERHEAT_END_AT + 16)); // clean by 2066, one frame before the cut to 15
    cm.emissive.copy(this.coreCool).lerp(CORE_HOT, heat);
    // 0.42 is build.ts's authored resting intensity; the lit core tops out near 1.6, which is the brightest thing
    // in a room whose only other sources are two cyan strips
    cm.emissiveIntensity = 0.42 + data * (0.3 + 0.34 * beat) + heat * (0.45 + 0.45 * hammer);
    // 5% of a 1.10 m radius is 5.5 cm and the shake is 4.5 cm at its worst: both inside the coreR 1.10 half-size
    // plate shots 14-16 measure, so the lit mesh and the measured core never disagree about where the subject is
    B.core.scale.setScalar(1 + data * 0.05 * beat + shake * 0.03 * Math.sin((f - OVERHEAT_AT) * 0.71));
    B.core.position.set(
      BRAIN.core[0] + shake * 0.045 * Math.sin(f * 0.83),
      BRAIN.core[1] + shake * 0.034 * Math.sin(f * 1.07),
      BRAIN.core[2] + shake * 0.028 * Math.sin(f * 0.61),
    );

    // ---- the memory screens ----
    // Three dark panels until story's LOOP beats, then one every 62 frames, each staying on for the rest of the
    // film — the authored window is PROP_QUADS[16]'s (2290 / 2352 / 2414, all inside shot 16's 2248..2487), so the
    // mesh lights on the same frame the drawn quad becomes answerable and the two can never disagree.
    for (let i = 0; i < B.screens.length; i++) {
      const scr = B.screens[i];
      if (!scr) continue;
      const sm = scr.material as THREE.MeshLambertMaterial;
      const at = LOOP_ATS[i] ?? LOOP_AT + i * 62;
      const on = glide(f, at, at + 10);
      sm.emissive.copy(SCREEN_ON);
      // a panel that is on still has to breathe: 0.05 rad/frame is a 5 Hz flicker off the refresh, not a strobe
      sm.emissiveIntensity = on * (0.82 + 0.1 * Math.sin(f * (0.37 + i * 0.05) + i * 2.4));
    }
    // `dendrites` is exposed but build.ts says nothing in it animates on its own, and it is authored around the
    // soma at BRAIN.core while its own group sits at the world origin — rotating it would shear ten arms off the
    // cell body. Left exactly as built.
  }

  // ---------------- suburban street, then the beam ----------------
  private animRoad(f: number) {
    const K = this.sets.road;

    // ---- the arrival ----
    // carRoll solves ROAD.carIn -> ROAD.carRest on CAR_IN_AT..CAR_STOP_AT, and the arrival is a straight line, so
    // the authored yaw (atan2(11.15, -2.85) = bearing 104.4 deg) can only ever agree with it. Re-asserted because
    // the contract says world.ts drives position AND yaw through the arrival: parked, it sits 2.35 m left of and
    // 1.15 m behind ROAD.hero, which is what frames his back in shot 24 without sharing his silhouette column.
    const p = carRoll(f);
    K.car.position.set(p[0], p[1], p[2]);
    K.car.rotation.y = Math.atan2(ROAD.carRest[0] - ROAD.carIn[0], ROAD.carRest[2] - ROAD.carIn[2]);
    // 2 degrees over the 30 frames straddling the stop = a 6 cm nosedive at the 1.78 m overhang: a brake stop, not
    // a crash, and it is back inside the authored plate by CAR_STOP_AT + 10. The 1 mm idle shudder after it is the
    // "engine still warm" read, and it is the only thing in shot 23's last second that is not a still.
    const dive = Math.sin(clamp01(seg(CAR_STOP_AT - 20, CAR_STOP_AT + 10, f)) * Math.PI) * 0.035;
    K.car.rotation.x = dive + Math.sin(f * 1.42) * 0.0016;

    // ---- the disc ----
    // ROAD.ufo's y 7.4 is not a taste number: build.ts cuts the beam column to reach 7.1 and the hull floor stands
    // 0.38 m under the origin, so the authored pair closes that gap to 8 cm. The hover therefore gets 5 cm of bob
    // and no more, and the descent lands ON 7.4 rather than anywhere near it.
    const down = glide(f, UFO_AT - 34, UFO_AT);
    K.ufo.position.y = ROAD.ufo[1] + (1 - down) * 5.2 + 0.05 * Math.sin(f * 0.085) * down;

    // ---- the column ----
    // ONE opacity, written to the beam and to its ground ellipse, because build.ts says so and because the two
    // must never disagree about how lit the abduction is. UFO_AT is the frame the column reaches the street and
    // CODE_AT the glyph: a 6-frame flare over a 24-frame fall on the same number.
    const lit = glide(f, UFO_AT, UFO_AT + 20);
    const glyph = glide(f, CODE_AT, CODE_AT + 6) * (1 - glide(f, CODE_AT + 6, CODE_AT + 30));
    const op = clamp01(lit * (0.36 + 0.03 * Math.sin(f * 0.072) + 0.2 * glyph));
    (K.beam.material as THREE.MeshBasicMaterial).opacity = op;
    (K.pool.material as THREE.MeshBasicMaterial).opacity = op;
    // the sodium lamp's own bloom is ON from frame 0 — it is the streetlight, not the beam — and it carries shot
    // 23's whole luma while the column is still dark. There is no beat gate in this line on purpose.
    (K.lampGlow.material as THREE.MeshBasicMaterial).opacity =
      0.58 + 0.035 * Math.sin(f * 0.113) + 0.018 * Math.sin(f * 0.41 + 2.1);
    // DOOR_AT has nothing to swing: build.ts hinges the door inside the house group but RoadRefs does not expose
    // it, so the 3400 door beat is currently a subtitle only.
  }
}
