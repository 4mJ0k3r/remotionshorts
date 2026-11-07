// The three "Tower Qwen" sets as one three.js scene. update(id, f, camera, scene) poses shot `id` at frame `f` as a
// PURE function of id + f (no mutable state, so any frame can be rendered out of order): which set is visible, the
// bascule angles, the bus on the rising leaf / in its jump arc, the tug, the gauge needle, the throttle lever pinned
// under the driver's 2D fist, the scrolling river, the camera-relative sun frozen per shot, sky, fog, TONE/CHAR
// uniforms, and the lit cast cards + effect cards (frustum-culled, cached through the canvas Pool).
import * as THREE from "three";
import { buildSets, Sets } from "./build";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage, knobWorld } from "./cast";
import {
  FPS, SHOTS, camAt, tiltDegAt, bus1At, jumpAt, leverAt, lerp, smooth, D2R, TILT1, CAB,
} from "./story";

const UP = new THREE.Vector3(0, 1, 0);
/** stretch a unit cylinder to span a -> b */
const setCable = (m: THREE.Mesh, a: THREE.Vector3, b: THREE.Vector3) => {
  const d = b.clone().sub(a), L = d.length();
  m.position.copy(a).addScaledVector(d, 0.5); m.scale.set(1, Math.max(0.01, L), 1);
  m.quaternion.setFromUnitVectors(UP, d.normalize());
};
const scroll = (o: THREE.Object3D, dx: number, dy: number) => {
  const m = (o as THREE.Mesh).material as THREE.MeshLambertMaterial;
  if (m?.map) m.map.offset.set(dx, dy);
};

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight; private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#cfe4f4", 60, 460);
  private sunCache = new Map<number, THREE.Vector3>();
  private sets: Sets;
  private frustum = new THREE.Frustum();
  private m4 = new THREE.Matrix4(); private v = new THREE.Vector3(); private sph = new THREE.Sphere();
  private box = new THREE.Vector3(...CAB.boxTop);

  constructor() {
    const R = this.root;
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() },
        c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() },
        uSun: { value: new THREE.Vector3(0, 1, 0) }, uGlow: { value: new THREE.Color() }, uGlowK: { value: 0 } },
      vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      fragmentShader: `uniform vec3 c0, c1, c2, c3, c4, uGlow; uniform vec4 e; uniform vec3 uSun; uniform float uGlowK; varying vec3 vP;
        void main(){ vec3 d = normalize(vP); float el = asin(clamp(d.y, -1.0, 1.0));
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el));
          c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el));
          c = mix(c, c4, smoothstep(e.z, e.w, el));
          float g = pow(max(dot(d, uSun), 0.0), 6.0);
          c = mix(c, uGlow, g * uGlowK);
          gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(900, 40, 20), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK);
    R.add(this.sky);
    this.hemi = new THREE.HemisphereLight("#dcecff", "#54788c", 0.62);
    this.sun = new THREE.DirectionalLight("#fff2dc", 3.0);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(4096, 4096);
    R.add(this.hemi, this.sun, this.sun.target);
    this.sets = buildSets();
    R.add(this.sets.root);
  }

  private pr<T>(name: string) { return this.sets.props[name] as T | undefined; }

  /** camera-relative sun, frozen per shot: the shot's mean view direction turned by az toward screen right, lifted by el */
  private shotSun(id: number, L: LightPreset) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1];
    let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 3) {
      const c = camAt(id, f), x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1;
      fx += x / n; fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1; fx /= n; fz /= n;
    const az = THREE.MathUtils.degToRad(L.az), el = THREE.MathUtils.degToRad(L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  private animateProps(f: number, cam: THREE.PerspectiveCamera) {
    const t = f / FPS;
    // ---- shot 1: the road splits, the bus climbs the raised left leaf, a tug crosses the reach ----
    const tilt = tiltDegAt(f) * D2R;
    const left = this.pr<THREE.Group>("leftLeaf"), right = this.pr<THREE.Group>("rightLeaf");
    if (left) left.rotation.z = tilt;
    if (right) right.rotation.z = -tilt;
    const b1 = this.pr<THREE.Group>("bus1");
    if (b1) {
      const b = bus1At(f);
      b1.position.set(...b.p);
      b1.rotation.set(0, 0, b.pitch);                     // the leaf's own angle: the wheels stay on the asphalt
    }
    const tug = this.pr<THREE.Group>("tug");
    if (tug) {
      tug.position.set(-15.5 + f * 0.075, 0.05 * Math.sin(f * 0.19), 18.5 - f * 0.06);
      tug.rotation.set(0.012 * Math.sin(f * 0.19), 0.32, 0.02 * Math.sin(f * 0.11));
    }
    const river1 = this.pr<THREE.Mesh>("river1");
    if (river1) scroll(river1, t * 0.04, t * 0.11);

    // ---- shot 2: the gauge sweeps with the throttle, and the brass lever is pinned to the 2D fist ----
    const needle = this.pr<THREE.Group>("needle");
    if (needle) needle.rotation.z = lerp(-2.15, -0.7, leverAt(f));
    const lv = this.pr<{ pivot: THREE.Group; shaft: THREE.Mesh; knob: THREE.Mesh }>("lever");
    if (lv) {
      const k = knobWorld(cam.position, f);
      lv.knob.position.copy(k);
      setCable(lv.shaft, this.box, k);
    }
    const cabBg = this.pr<{ group: THREE.Group; water: THREE.Mesh }>("cabBg");
    if (cabBg) scroll(cabBg.water, t * 0.05, t * 0.13);

    // ---- shot 3: the bus arcs across the miniature bridge and settles on the far leaf ----
    const b3 = this.pr<THREE.Group>("bus3");
    if (b3) {
      const j = jumpAt(f);
      b3.position.set(...j.p);
      b3.rotation.set(0, 0, j.pitch);
    }
    const river3 = this.pr<THREE.Mesh>("river3");
    if (river3) scroll(river3, t * 0.03, t * 0.09);
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], L = LIGHTS[s.light];
    // ---- camera ----
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.05; cam.far = 1200; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = new THREE.Vector3(...c.look), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    // ---- set visibility + pure-function poses ----
    for (const [name, g] of Object.entries(this.sets.sets)) g.visible = name === s.set;
    this.animateProps(f, cam);
    // ---- light rig ----
    const K = LOOK[s.light], sunDir = this.shotSun(id, L);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.15 + 4, 6, 34);
    this.sun.position.copy(focus).addScaledVector(sunDir, 160); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 10; sc.far = 360; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    this.sun.shadow.radius = 3;
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term;
    TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = K.sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    // ---- sky, fog ----
    const su = this.skyMat.uniforms;
    K.sky.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = K.sky.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    (su.uSun.value as THREE.Vector3).copy(sunDir);
    untone("#fff6e0", su.uGlow.value as THREE.Color);
    su.uGlowK.value = 0.25;
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear; this.fog.far = L.fogFar;
    scene.fog = this.fog; scene.background = null;
    // ---- cast + effects ----
    const right = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 0);
    const st = stage(id, t, { pos: cam.position, right, sun: sunDir });
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    let ai = 0;
    const used: Actor[] = [];
    for (const p of st.places) {
      const sc2 = p.scale ?? 1;
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y + 1.1 * sc2, p.z), 3.5))) continue;
      const a = this.actor(ai++);
      const [w, h, k] = p.size ?? [300, 500, 0.5];
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true;
      a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z), p.roll ?? 0);
      a.mesh.scale.set(p.mirror ? -sc2 : sc2, sc2, sc2);
      a.mesh.castShadow = L.actorShadow;
      a.opacity(p.opacity ?? 1);
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0;
    const fused: Fx[] = [];
    for (const p of st.fx) {
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y, p.z), Math.max(p.w, p.h)))) continue;
      const fx = this.fx(fi++);
      fx.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      fx.use(!!p.soft);
      fx.mesh.visible = true;
      fx.mesh.position.set(p.x, p.y, p.z);
      if (p.flat) fx.mesh.rotation.set(-Math.PI / 2, 0, p.rot ?? 0);
      else { fx.mesh.quaternion.copy(cam.quaternion); fx.mesh.rotateZ(p.rot ?? 0); }
      fx.mesh.scale.set(p.w, p.h, 1);
      fx.opacity(p.opacity ?? 1);
      fused.push(fx);
    }
    for (let fi2 = fi; fi2 < this.fxs.length; fi2++) this.fxs[fi2].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const fx of fused) fx.bind();
    return focus;
  }
}
