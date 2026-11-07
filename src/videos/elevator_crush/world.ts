// Three.js world manager for ElevatorCrushShort: lighting, sky, camera, the two isolated sets (Hard Rule 8),
// reactive set motion (doors, LED, ceiling lights, cable grate, shaft drop, rain window), the shot-5 Rule B knob pin,
// and cast actors / FX cards.
import * as THREE from "three";
import { buildSets, WorldSets, CabinRefs, CAB, PANEL, KNOB_ROW } from "./build";
import { LIGHTS, LOOK, LightPreset, LightName } from "./lights";
import { TONE, CHAR, untone } from "./shade";
import { NOINK } from "./ink";
import { redrawRainWindow } from "./paint";
import { Pool, Actor, Fx, stage, handWorldPos, HERO_S5, HERO_SCALE, FIST_DX, FIST_DY } from "./cast";
import {
  FPS, SHOTS, camAt, glide, lightAt, BHDAM_AT, CABLE_AT, DROP_AT, LIGHTS_BACK_AT,
} from "./story";

const UP = new THREE.Vector3(0, 1, 0);

/** Orients and stretches a unit-height cylinder between points a and b */
const setCable = (m: THREE.Mesh, a: THREE.Vector3, b: THREE.Vector3) => {
  const d = b.clone().sub(a);
  const L = d.length();
  m.position.copy(a).addScaledVector(d, 0.5);
  m.scale.set(1, Math.max(0.01, L), 1);
  m.quaternion.setFromUnitVectors(UP, d.normalize());
};

/** Ceiling-panel colour (linear, >1 blooms) per light */
const CEIL: Record<LightName, [string, number]> = {
  amberCyan: ["#fff1d6", 1.25],
  rainy: ["#e8f0ff", 1.15],
  emergency: ["#ff6a3a", 0.35],
  violetRim: ["#b070ff", 0.3],
  heartbeat: ["#ff7aa0", 0.45],
  goldWarm: ["#ffd9a0", 0.6],
  roseGold: ["#ffd8c0", 1.1],
  neon: ["#7ae8ff", 0.8],
};

/** Door opening 0 (shut) .. 1 (open) per shot / frame */
const doorOpen = (id: number, f: number) => {
  if (id === 1) return 1 - glide(f, 0, 90);
  if (id === 2) {
    if (f < 230) return 1;
    if (f < 283) return 1 - 0.92 * glide(f, 230, 283);
    if (f < 295) return 0.08 + 0.92 * glide(f, 283, 295); // bounce open: she's coming!
    if (f < 340) return 1;
    return 1 - glide(f, 340, 395);
  }
  return 0;
};

const ledText = (id: number, f: number): [string, boolean] => {
  if (id <= 2) return ["FLOOR 4", false];
  if (id === 3 && f < BHDAM_AT) return ["FLOOR 4", false];
  if (id === 3) return ["4 • STUCK", Math.floor((f - BHDAM_AT) / 6) % 2 === 1];
  if (id <= 6) return ["4 • STUCK", Math.floor(f / 30) % 2 === 1];
  if (id === 7) return f >= DROP_AT ? ["3.5 ?!", Math.floor(f / 5) % 2 === 1] : ["4 • STUCK", f >= CABLE_AT && Math.floor(f / 5) % 2 === 1];
  if (id <= 9) return ["STUCK", Math.floor(f / 30) % 2 === 1];
  return ["FLOOR 4", false];
};

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight;
  private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh;
  private skyMat: THREE.ShaderMaterial;
  private sets: WorldSets;
  private sunCache = new Map<number, THREE.Vector3>();
  private knobRest = new THREE.Vector3();
  private rainSeed = -1;

  constructor() {
    const R = this.root;
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: {
        c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() },
        c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() },
      },
      vertexShader: `
        varying vec3 vP;
        void main() { vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }
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
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(900, 32, 16), this.skyMat);
    this.sky.renderOrder = -1;
    this.sky.frustumCulled = false;
    this.sky.layers.set(NOINK);
    R.add(this.sky);

    this.hemi = new THREE.HemisphereLight("#d6ecfa", "#8a7b68", 0.6);
    this.sun = new THREE.DirectionalLight("#fff5e4", 3.0);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.sun.shadow.camera.near = 0.5;
    this.sun.shadow.camera.far = 80;
    this.sun.shadow.camera.left = -8;
    this.sun.shadow.camera.right = 8;
    this.sun.shadow.camera.top = 8;
    this.sun.shadow.camera.bottom = -8;
    R.add(this.hemi, this.sun, this.sun.target);

    this.sets = buildSets();
    R.add(this.sets.cabin.root, this.sets.corridor.root);

    // Brass panel placement: the FAN row sits exactly where the hero's fist lands in shot 5 (mid-shot camera).
    const s5 = SHOTS[4];
    const cm = camAt(5, Math.round((s5.a + s5.b) / 2));
    handWorldPos(new THREE.Vector3(...cm.pos), HERO_S5, HERO_SCALE, FIST_DX, FIST_DY, -0.08, this.knobRest);
    for (const set of [this.sets.cabin, this.sets.corridor]) {
      set.panel.position.set(this.knobRest.x - PANEL.btnX, this.knobRest.y - PANEL.rowY(KNOB_ROW), CAB.WALL_FACE_Z + 0.0125);
      this.placeKnob(set, this.knobRest);
    }
  }

  private placeKnob(set: CabinRefs, p: THREE.Vector3) {
    set.knob.position.copy(p);
    setCable(set.stem, new THREE.Vector3(p.x, p.y, CAB.WALL_FACE_Z + 0.02), p);
  }

  private actor(i: number) {
    while (this.actors.length <= i) this.actors.push(new Actor(this.root));
    return this.actors[i];
  }

  private fx(i: number) {
    while (this.fxs.length <= i) this.fxs.push(new Fx(this.root));
    return this.fxs[i];
  }

  /** Camera-relative frozen sun per shot + light */
  private shotSun(id: number, name: LightName, L: LightPreset) {
    const key = id * 16 + Object.keys(LIGHTS).indexOf(name);
    let v = this.sunCache.get(key);
    if (v) return v;
    const s = SHOTS[id - 1];
    let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 4) {
      const c = camAt(id, f);
      const x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2];
      const n = Math.hypot(x, z) || 1;
      fx += x / n; fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1;
    fx /= n; fz /= n;
    const az = THREE.MathUtils.degToRad(L.az), el = THREE.MathUtils.degToRad(L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az);
    const hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(key, v);
    return v;
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene): THREE.Vector3 {
    const lightName = lightAt(id, f);
    const L = LIGHTS[lightName];
    const look = LOOK[lightName];

    // ---- 1. Camera ----
    const c = camAt(id, f);
    cam.position.set(...c.pos);
    cam.up.set(0, 1, 0);
    cam.lookAt(...c.look);
    cam.fov = c.fov;
    cam.near = 0.1;
    cam.far = 1000;
    cam.updateProjectionMatrix();
    cam.updateMatrixWorld();
    cam.layers.enable(NOINK);

    // ---- 2. Lighting ----
    const sunDir = this.shotSun(id, lightName, L);
    this.sun.position.copy(cam.position).addScaledVector(sunDir, 30);
    this.sun.target.position.copy(cam.position);
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

    const sc = look.sky.c, se = look.sky.e;
    const u = this.skyMat.uniforms;
    u.c0.value.copy(untone(sc[0])); u.c1.value.copy(untone(sc[1])); u.c2.value.copy(untone(sc[2]));
    u.c3.value.copy(untone(sc[3])); u.c4.value.copy(untone(sc[4]));
    u.e.value.set(...(se.slice(1, 5).map((d) => THREE.MathUtils.degToRad(d)) as [number, number, number, number]));

    if (!scene.fog) scene.fog = new THREE.Fog(L.fog, L.fogNear, L.fogFar);
    else { const fg = scene.fog as THREE.Fog; fg.color.set(L.fog); fg.near = L.fogNear; fg.far = L.fogFar; }

    // ---- 3. STRICT SET ISOLATION (Hard Rule 8) ----
    this.sets.corridor.root.visible = id === 2;
    this.sets.cabin.root.visible = id !== 2;
    const set = id === 2 ? this.sets.corridor : this.sets.cabin;

    // ---- 4. Reactive set motion ----
    const open = doorOpen(id, f);
    set.doorL.position.x = -0.43 - 0.86 * open;
    set.doorR.position.x = 0.43 + 0.86 * open;

    const [txt, dim] = ledText(id, f);
    const ledKey = `${txt}|${dim}`;
    if (set.led.last !== ledKey) { set.led.redraw(txt, dim); set.led.last = ledKey; }

    // ceiling panels: power-cut flicker at BHADAAM, dim-light return in shot 10
    const [cc, ci] = CEIL[lightName];
    let k = ci;
    if (id === 3 && f >= BHDAM_AT && f < BHDAM_AT + 10) k = (f - BHDAM_AT) % 4 < 2 ? 0.9 : 0.15;
    if (id === 10) k = ci * (0.35 + 0.65 * glide(f, LIGHTS_BACK_AT - 14, LIGHTS_BACK_AT + 6));
    if (id === 7 && f >= DROP_AT) k = ci * 0.5;
    for (const m of set.ceilLights) m.color.set(cc).multiplyScalar(k);
    const emOn = lightName === "emergency" || (id === 7 && f < DROP_AT);
    set.emLamp.color.set(emOn ? "#ff3020" : "#5a1010").multiplyScalar(emOn ? 2.2 : 1);
    const btnCol = lightName === "emergency" || lightName === "violetRim" ? "#ff7a4a" : "#ffd98a";
    for (const m of set.buttons) m.color.set(btnCol).multiplyScalar(1.3);
    (set.knob.material as THREE.MeshBasicMaterial).color.set("#ffcf56").multiplyScalar(id === 5 ? 1.5 : 1.1);

    // cable grate: rattles in shot 7, swings open at CABLE_AT and stays open afterwards
    let hatchRot = 0;
    if (id === 7) {
      if (f < CABLE_AT) hatchRot = Math.sin(f * 1.3) * 0.025 * glide(f, 1524, 1560);
      else {
        const t = (f - CABLE_AT) / 14;
        hatchRot = -1.25 * Math.min(1, t) - (t > 1 ? Math.sin((f - CABLE_AT - 14) * 0.5) * 0.12 * Math.exp(-(f - CABLE_AT - 14) / 18) : 0);
      }
    } else if (id > 7) hatchRot = -1.25;
    set.hatch.rotation.z = hatchRot;
    for (let i = 0; i < set.cables.length; i++) {
      const vib = id === 7 && f >= 1600 ? Math.sin(f * 2.1 + i * 1.9) * 0.012 * (f >= CABLE_AT ? 2 : 1) : 0;
      set.cables[i].position.x = (i - 1) * 0.18 + vib;
    }
    // cabin dropped 2 ft: the shaft slides up relative to the cabin
    set.shaft.position.y = CAB.H + (id === 7 ? 0.6 * glide(f, DROP_AT, DROP_AT + 8) : id > 7 ? 0.6 : 0);

    // rain window streaks (shot 2): fresh deterministic streaks every 2 frames
    if (id === 2 && set.rainTex) {
      const seed = Math.floor(f / 2);
      if (seed !== this.rainSeed) { redrawRainWindow(set.rainTex, seed); this.rainSeed = seed; }
    }

    // ---- 5. Rule B: FAN knob pinned to the hero's 2D fist (shot 5) ----
    if (id === 5) {
      const p = handWorldPos(cam.position, HERO_S5, HERO_SCALE, FIST_DX, FIST_DY, -0.08);
      this.placeKnob(set, p);
    } else this.placeKnob(set, this.knobRest);

    // ---- 6. Cast ----
    const camRight = new THREE.Vector3();
    cam.matrixWorld.extractBasis(camRight, new THREE.Vector3(), new THREE.Vector3());
    const staged = stage(id, f / FPS, { pos: cam.position, right: camRight });

    let aIdx = 0;
    for (const p of staged.places) {
      const act = this.actor(aIdx++);
      act.mesh.position.set(p.x, p.y, p.z);
      const s = p.scale ?? 1.0;
      act.mesh.scale.set(s, s, s);
      act.mesh.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z);
      act.r = this.pool.req(p.key, p.size![0], p.size![1], p.size![2], p.draw);
      act.mesh.visible = true;
    }
    while (aIdx < this.actors.length) this.actors[aIdx++].mesh.visible = false;

    let fxIdx = 0;
    for (const p of staged.fx) {
      const fxx = this.fx(fxIdx++);
      fxx.mesh.position.set(p.x, p.y, p.z);
      fxx.mesh.scale.set(p.w, p.h, 1);
      if (p.flat) { fxx.mesh.rotation.set(-Math.PI / 2, 0, 0); }
      else { fxx.mesh.rotation.set(0, Math.atan2(cam.position.x - p.x, cam.position.z - p.z), 0); }
      fxx.use(!!p.soft);
      fxx.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      fxx.opacity(p.opacity ?? 1.0);
    }
    while (fxIdx < this.fxs.length) this.fxs[fxIdx++].mesh.visible = false;

    this.pool.flush();
    for (const a of this.actors) if (a.mesh.visible) a.bind();
    for (const x of this.fxs) if (x.mesh.visible) x.bind();

    return new THREE.Vector3(...c.look);
  }
}
